"""
memory_enricher.py -- Auto-append insights to agent MEMORY.md files
====================================================================
Closes the insight-to-agent gap: when the pipeline extracts insights from
batches, this module routes each insight to the correct agent(s) and appends
it to their MEMORY.md in the existing table/section format.

Design decisions (preserved as comments per spec):

  1. Person slug -> agents/external/{slug}/MEMORY.md  (direct match)
  2. Person slug -> cargo agents that list that person in DNA-CONFIG.yaml
     dna_sources.primario[].pessoa  (reverse lookup, cached per session)
  3. Dedup: scan existing MEMORY.md text for chunk_id string presence
  4. Append-only to "## INSIGHTS EXTRAIDOS" section (or create it)
  5. Never overwrite -- reads existing content, appends, writes back
  6. If agent dir doesn't exist -> skip (agent_generator hasn't run yet)
  7. If MEMORY.md doesn't exist -> create minimal stub from template header

Integration:
    Called by batch_auto_creator.py after batch creation (ImportError safe).
    Also callable standalone for backfill.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - JSONL logging.

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------

from core.paths import (  # noqa: E402
    AGENTS_BUSINESS,
    AGENTS_CARGO,
    AGENTS_EXTERNAL,
    LOGS,
    ROOT,
    ROUTING,
)

_ROOT = ROOT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Log file for enrichment events.
ENRICHER_LOG: Path = ROUTING.get("memory_enricher_log", LOGS / "memory-enricher.jsonl")

# MCE extraction threshold: 3+ cumulative insights per person triggers MCE.
MCE_INSIGHT_THRESHOLD: int = 3

# Section header we append insights to in MEMORY.md.
INSIGHTS_SECTION_HEADER = "## INSIGHTS EXTRAIDOS"
INSIGHTS_SECTION_HEADER_ALT = "## INSIGHTS EXTRA\u00cdDOS"  # accented I

# History section we append update records to.
HISTORY_SECTION_HEADER = "## HIST\u00d3RICO DE ATUALIZA\u00c7\u00d5ES"
HISTORY_SECTION_HEADER_ALT = "## HISTORICO DE ATUALIZACOES"

# Marker that separates the end of the insights section from the next section.
SECTION_MARKER_RE = re.compile(r"^## ", re.MULTILINE)

# ---------------------------------------------------------------------------
# INSIGHT DATA STRUCTURE
# ---------------------------------------------------------------------------


class Insight:
    """Represents a single insight to be enriched into agent MEMORY.md.

    Attributes:
        person_slug: Kebab-case person identifier (e.g., 'alex-hormozi').
        chunk_id: Unique chunk identifier for dedup (e.g., 'chunk_199').
        insight_id: Optional insight identifier (e.g., 'CF001').
        tag: Source tag (e.g., 'AH-SS001').
        title: Short description of the insight.
        content: Full insight text.
        priority: Priority level ('HIGH', 'MEDIUM', 'LOW').
        path_raiz: Path to the original source file in inbox.
        batch_id: ID of the batch that produced this insight.
    """

    __slots__ = (
        "batch_id",
        "chunk_id",
        "content",
        "insight_id",
        "path_raiz",
        "person_slug",
        "priority",
        "tag",
        "title",
    )

    def __init__(
        self,
        person_slug: str,
        chunk_id: str,
        insight_id: str = "",
        tag: str = "",
        title: str = "",
        content: str = "",
        priority: str = "MEDIUM",
        path_raiz: str = "",
        batch_id: str = "",
    ) -> None:
        self.person_slug = person_slug.lower().strip()
        self.chunk_id = chunk_id.strip()
        self.insight_id = insight_id.strip()
        self.tag = tag.strip()
        self.title = title.strip()
        self.content = content.strip()
        self.priority = priority.upper().strip()
        self.path_raiz = path_raiz.strip()
        self.batch_id = batch_id.strip()

    def to_dict(self) -> dict[str, str]:
        """Serialize to dict for logging."""
        return {
            "person_slug": self.person_slug,
            "chunk_id": self.chunk_id,
            "insight_id": self.insight_id,
            "tag": self.tag,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
            "path_raiz": self.path_raiz,
            "batch_id": self.batch_id,
        }


# ---------------------------------------------------------------------------
# CARGO AGENT REVERSE LOOKUP (cached)
# ---------------------------------------------------------------------------

_cargo_reverse_map: dict[str, list[Path]] | None = None


def _build_cargo_reverse_map() -> dict[str, list[Path]]:
    """Scan all cargo agent DNA-CONFIG.yaml files and build a reverse map.

    Maps person_slug -> list of cargo agent directories that consume that
    person's DNA (via dna_sources.primario[].pessoa).

    This is cached at module level because it only changes when cargo agents
    are created or modified (rare during a pipeline run).

    Returns:
        Dict mapping lowercase person slug to list of cargo agent Paths.
    """
    global _cargo_reverse_map
    if _cargo_reverse_map is not None:
        return _cargo_reverse_map

    reverse: dict[str, list[Path]] = {}

    if not AGENTS_CARGO.exists():
        _cargo_reverse_map = reverse
        return reverse

    # Cargo agents are nested: agents/cargo/{area}/{role}/DNA-CONFIG.yaml
    for config_path in AGENTS_CARGO.rglob("DNA-CONFIG.yaml"):
        agent_dir = config_path.parent

        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            logger.debug("Failed to parse %s", config_path)
            continue

        if not isinstance(data, dict):
            continue

        # Extract person slugs from dna_sources.primario
        dna_sources = data.get("dna_sources", {})
        if not isinstance(dna_sources, dict):
            continue

        primario = dna_sources.get("primario", [])
        if not isinstance(primario, list):
            continue

        for entry in primario:
            if not isinstance(entry, dict):
                continue
            pessoa = entry.get("pessoa", "")
            if not pessoa:
                continue
            # Normalize: some configs use uppercase (e.g., "SAM-OVEN")
            slug = pessoa.lower().strip()
            if slug not in reverse:
                reverse[slug] = []
            if agent_dir not in reverse[slug]:
                reverse[slug].append(agent_dir)

    _cargo_reverse_map = reverse
    logger.debug(
        "Built cargo reverse map: %d person slugs -> %d cargo agents",
        len(reverse),
        sum(len(v) for v in reverse.values()),
    )
    return reverse


def invalidate_cargo_cache() -> None:
    """Force rebuild of the cargo reverse map on next call.

    Useful after creating new cargo agents mid-session.
    """
    global _cargo_reverse_map
    _cargo_reverse_map = None


# ---------------------------------------------------------------------------
# TARGET AGENT DISCOVERY
# ---------------------------------------------------------------------------


def _find_target_agents(person_slug: str) -> list[Path]:
    """Find all agent directories that should receive insights for a person.

    Strategy:
        1. Direct match: agents/external/{person_slug}/ (if exists)
        2. Direct match: agents/business/{subcat}/{person_slug}/ (collaborators,
           partners, alumni -- any subdirectory under agents/business/)
        3. Cargo consumers: any cargo agent whose DNA-CONFIG.yaml lists
           this person in dna_sources.primario

    Args:
        person_slug: Kebab-case person identifier.

    Returns:
        List of absolute Paths to agent directories (may be empty).
    """
    targets: list[Path] = []
    slug = person_slug.lower().strip()

    # 1. Direct external agent match
    external_dir = AGENTS_EXTERNAL / slug
    if external_dir.is_dir():
        targets.append(external_dir)

    # 2. Direct business agent match (scan subcategories)
    if AGENTS_BUSINESS.is_dir():
        for subcat in AGENTS_BUSINESS.iterdir():
            if not subcat.is_dir() or subcat.name.startswith("."):
                continue
            candidate = subcat / slug
            if candidate.is_dir() and candidate not in targets:
                targets.append(candidate)

    # 3. Cargo agent consumers
    cargo_map = _build_cargo_reverse_map()
    cargo_targets = cargo_map.get(slug, [])
    for cargo_dir in cargo_targets:
        if cargo_dir.is_dir() and cargo_dir not in targets:
            targets.append(cargo_dir)

    return targets


# ---------------------------------------------------------------------------
# DEDUP CHECK
# ---------------------------------------------------------------------------


def _is_duplicate(memory_text: str, chunk_id: str) -> bool:
    """Check if a chunk_id already appears in the MEMORY.md text.

    Simple string search -- if the chunk_id string is present anywhere
    in the file, we consider it a duplicate. This handles both table rows
    and inline references.

    Args:
        memory_text: Full text content of MEMORY.md.
        chunk_id: The chunk identifier to search for.

    Returns:
        True if chunk_id is already present in the text.
    """
    if not chunk_id:
        return False
    return chunk_id in memory_text


# ---------------------------------------------------------------------------
# MEMORY.MD CREATION (from template stub)
# ---------------------------------------------------------------------------

_MEMORY_STUB_TEMPLATE = """\
# MEMORY: {person_name}

> **Atualizado:** {date}
> **Versao:** 1.0.0

---

## MATERIAIS PROCESSADOS

*Nenhum material processado ainda.*

---

## PADROES DE PENSAMENTO

*A ser populado com processamento de materiais via Pipeline.*

---

## EXPRESSOES CARACTERISTICAS

*Nenhuma expressao identificada ainda.*

---

## INSIGHTS EXTRAIDOS

*Insights do Pipeline serao adicionados aqui automaticamente.*

---

## HISTORICO DE ATUALIZACOES

| Data | Mudanca | Material Processado |
|------|---------|---------------------|
| {date} | Criacao inicial (auto-gerado) | memory_enricher.py v1.0.0 |

---

*MEMORY.md v1.0.0 - Auto-gerado por `memory_enricher.py`*
"""


def _create_memory_if_missing(agent_dir: Path) -> Path:
    """Create a minimal MEMORY.md from template if the file doesn't exist.

    Args:
        agent_dir: Path to the agent directory.

    Returns:
        Path to the (existing or newly created) MEMORY.md file.
    """
    memory_path = agent_dir / "MEMORY.md"

    if memory_path.exists():
        return memory_path

    # Derive person name from directory name
    slug = agent_dir.name
    person_name = " ".join(w.capitalize() for w in slug.split("-"))
    now = datetime.now(UTC).strftime("%Y-%m-%d")

    content = _MEMORY_STUB_TEMPLATE.format(person_name=person_name, date=now)

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(content, encoding="utf-8")

    logger.info("Created MEMORY.md stub at %s", memory_path)
    return memory_path


# ---------------------------------------------------------------------------
# INSIGHT APPEND LOGIC
# ---------------------------------------------------------------------------


def _format_insight_entry(insight: Insight, date: str) -> str:
    """Format a single insight as a markdown subsection for MEMORY.md.

    Follows the SOLO agent format from the memory template:
        ### {DATE} - {Title}
        **Rastreabilidade:**
        | Campo | Valor |
        ...
        **Insight:** ...

    Args:
        insight: The Insight object to format.
        date: ISO date string for the entry.

    Returns:
        Formatted markdown string (with leading newlines for separation).
    """
    lines: list[str] = []
    lines.append("")
    lines.append(f"### {date} - {insight.title or 'Insight from Pipeline'}")
    lines.append("")
    lines.append("**Rastreabilidade:**")
    lines.append("| Campo | Valor |")
    lines.append("|-------|-------|")

    if insight.insight_id:
        lines.append(f"| insight_id | {insight.insight_id} |")
    if insight.chunk_id:
        lines.append(f"| chunk_id | {insight.chunk_id} |")
    if insight.path_raiz:
        lines.append(f"| PATH_RAIZ | {insight.path_raiz} |")
    if insight.batch_id:
        lines.append(f"| batch_id | {insight.batch_id} |")
    if insight.tag:
        lines.append(f"| tag | {insight.tag} |")

    lines.append("")

    if insight.content:
        lines.append("**Insight:**")
        lines.append(insight.content)
        lines.append("")

    return "\n".join(lines)


def _format_history_row(date: str, insight: Insight) -> str:
    """Format a single row for the HISTORICO DE ATUALIZACOES table.

    Args:
        date: ISO date string.
        insight: The Insight that triggered the update.

    Returns:
        A markdown table row string.
    """
    title = insight.title or insight.chunk_id or "Pipeline insight"
    source = insight.batch_id or insight.tag or "memory_enricher.py"
    return f"| {date} | Insight: {title} | {source} |"


def _append_insight(memory_path: Path, insight: Insight) -> bool:
    """Append a single insight to an existing MEMORY.md file.

    Strategy:
        1. Read the full file content.
        2. Find the "## INSIGHTS EXTRAIDOS" section.
        3. Find the NEXT section header after it (or EOF).
        4. Insert the formatted insight just before that next section.
        5. Also append a row to the HISTORICO table if it exists.
        6. Write back the modified content.

    Args:
        memory_path: Absolute path to the MEMORY.md file.
        insight: The Insight to append.

    Returns:
        True if the insight was appended, False if skipped (dedup or error).
    """
    try:
        text = memory_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Cannot read %s: %s", memory_path, exc)
        return False

    # Dedup check
    if _is_duplicate(text, insight.chunk_id):
        logger.debug(
            "Duplicate chunk_id '%s' in %s, skipping",
            insight.chunk_id,
            memory_path,
        )
        return False

    now = datetime.now(UTC).strftime("%Y-%m-%d")
    entry_text = _format_insight_entry(insight, now)

    # Find the insights section
    insights_pos = text.find(INSIGHTS_SECTION_HEADER)
    if insights_pos == -1:
        insights_pos = text.find(INSIGHTS_SECTION_HEADER_ALT)

    if insights_pos == -1:
        # Section doesn't exist -- append it before the history section or EOF
        history_pos = text.find(HISTORY_SECTION_HEADER)
        if history_pos == -1:
            history_pos = text.find(HISTORY_SECTION_HEADER_ALT)

        if history_pos != -1:
            insert_block = f"\n{INSIGHTS_SECTION_HEADER}\n{entry_text}\n\n---\n\n"
            text = text[:history_pos] + insert_block + text[history_pos:]
        else:
            # No history section either -- append at EOF
            text = text.rstrip() + f"\n\n{INSIGHTS_SECTION_HEADER}\n{entry_text}\n"
    else:
        # Find the next ## section after insights header
        # (skip past the header line itself)
        search_start = insights_pos + len(INSIGHTS_SECTION_HEADER)
        remaining = text[search_start:]

        # Find next section boundary (## or ---)
        next_section = None
        for match in SECTION_MARKER_RE.finditer(remaining):
            next_section = search_start + match.start()
            break

        if next_section is not None:
            # Insert just before the next section (before the --- separator)
            # Walk back to find the --- separator before the next ##
            insert_pos = next_section
            pre_section = text[:insert_pos].rstrip()

            # Check if there's a --- separator to preserve
            if pre_section.endswith("---"):
                insert_pos = len(pre_section) - 3
                text = (
                    text[:insert_pos].rstrip()
                    + "\n"
                    + entry_text
                    + "\n\n---\n\n"
                    + text[next_section:]
                )
            else:
                text = text[:insert_pos].rstrip() + "\n" + entry_text + "\n\n" + text[insert_pos:]
        else:
            # No next section -- append at end of file
            text = text.rstrip() + "\n" + entry_text + "\n"

    # Append history row if history section exists
    history_row = _format_history_row(now, insight)
    history_pos = text.find(HISTORY_SECTION_HEADER)
    if history_pos == -1:
        history_pos = text.find(HISTORY_SECTION_HEADER_ALT)

    if history_pos != -1:
        # Find the last table row in the history section (look for | ... |)
        history_section_start = history_pos
        history_remaining = text[history_section_start:]

        # Find next ## after history
        next_after_history = None
        for match in SECTION_MARKER_RE.finditer(history_remaining[len(HISTORY_SECTION_HEADER) :]):
            next_after_history = history_section_start + len(HISTORY_SECTION_HEADER) + match.start()
            break

        # Find the last occurrence of "\n|" in the history table area
        area_start = history_section_start
        if next_after_history is not None:
            area_end = next_after_history
        else:
            area_end = len(text)

        area_text = text[area_start:area_end]
        last_pipe = area_text.rfind("\n|")
        if last_pipe != -1:
            # Find the end of that line
            line_end = area_text.find("\n", last_pipe + 1)
            if line_end == -1:
                line_end = len(area_text)
            abs_insert = area_start + line_end
            text = text[:abs_insert] + "\n" + history_row + text[abs_insert:]

    # Update the "Atualizado" date in the header
    text = re.sub(
        r"(\*\*Atualizado:\*\*)\s*\d{4}-\d{2}-\d{2}",
        f"\\1 {now}",
        text,
        count=1,
    )

    # Write back
    try:
        memory_path.write_text(text, encoding="utf-8")
        logger.info("Appended insight '%s' to %s", insight.chunk_id, memory_path)
        return True
    except Exception as exc:
        logger.warning("Failed to write %s: %s", memory_path, exc)
        return False


# ---------------------------------------------------------------------------
# JSONL LOGGING
# ---------------------------------------------------------------------------


def _log_enrichment(
    insights: list[Insight],
    results: dict[str, Any],
    duration_ms: int,
) -> None:
    """Append enrichment event to JSONL audit log.

    Args:
        insights: List of insights that were processed.
        results: Summary dict of enrichment results.
        duration_ms: Time taken in milliseconds.
    """
    try:
        ENRICHER_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "insights_received": len(insights),
            "insights_appended": results.get("appended", 0),
            "insights_skipped_dedup": results.get("skipped_dedup", 0),
            "insights_skipped_no_agent": results.get("skipped_no_agent", 0),
            "agents_enriched": results.get("agents_enriched", []),
            "duration_ms": duration_ms,
        }
        with open(ENRICHER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write enricher log", exc_info=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------


def enrich(insights: list[dict[str, str] | Insight]) -> dict[str, Any]:
    """Route insights to the correct agent MEMORY.md files and append them.

    This is the main public API. It accepts a list of insights (either
    Insight objects or dicts with the same keys), finds target agents,
    deduplicates, and appends new insights.

    Args:
        insights: List of Insight objects or dicts with keys:
            person_slug (required), chunk_id (required),
            insight_id, tag, title, content, priority, path_raiz, batch_id.

    Returns:
        Dict with enrichment results::

            {
                "appended": 3,
                "skipped_dedup": 1,
                "skipped_no_agent": 0,
                "agents_enriched": ["agents/external/alex-hormozi", ...],
                "errors": [],
            }

    Example::

        from core.intelligence.pipeline.memory_enricher import enrich

        results = enrich([
            {
                "person_slug": "alex-hormozi",
                "chunk_id": "chunk_300",
                "title": "New insight about scaling",
                "content": "Systems beat talent...",
                "tag": "AH-SS002",
                "batch_id": "BATCH-150-AH",
            },
        ])
    """
    import time

    start = time.monotonic()

    results: dict[str, Any] = {
        "appended": 0,
        "skipped_dedup": 0,
        "skipped_no_agent": 0,
        "agents_enriched": [],
        "errors": [],
    }

    if not insights:
        return results

    # Normalize inputs to Insight objects
    normalized: list[Insight] = []
    for item in insights:
        if isinstance(item, Insight):
            normalized.append(item)
        elif isinstance(item, dict):
            try:
                normalized.append(
                    Insight(**{k: v for k, v in item.items() if k in Insight.__slots__})
                )
            except TypeError as exc:
                results["errors"].append(f"Invalid insight dict: {exc}")
                continue
        else:
            results["errors"].append(f"Unsupported insight type: {type(item).__name__}")
            continue

    enriched_agents: set[str] = set()

    for insight in normalized:
        if not insight.person_slug:
            results["errors"].append(f"Missing person_slug for chunk_id={insight.chunk_id}")
            continue

        if not insight.chunk_id:
            results["errors"].append(f"Missing chunk_id for person_slug={insight.person_slug}")
            continue

        # Find all target agent directories
        targets = _find_target_agents(insight.person_slug)

        if not targets:
            results["skipped_no_agent"] += 1
            logger.debug(
                "No agent found for '%s', skipping chunk_id='%s'",
                insight.person_slug,
                insight.chunk_id,
            )
            continue

        for agent_dir in targets:
            # Ensure MEMORY.md exists (create stub if needed)
            memory_path = _create_memory_if_missing(agent_dir)

            # Attempt to append
            success = _append_insight(memory_path, insight)

            if success:
                results["appended"] += 1
                try:
                    rel = str(agent_dir.relative_to(_ROOT))
                except ValueError:
                    rel = str(agent_dir)
                enriched_agents.add(rel)
            else:
                # _append_insight returns False for dedup or error
                # (errors are already logged inside the function)
                results["skipped_dedup"] += 1

    results["agents_enriched"] = sorted(enriched_agents)

    elapsed = int((time.monotonic() - start) * 1000)
    _log_enrichment(normalized, results, elapsed)

    logger.info(
        "Memory enrichment complete: %d appended, %d dedup, %d no-agent, %d errors",
        results["appended"],
        results["skipped_dedup"],
        results["skipped_no_agent"],
        len(results["errors"]),
    )

    # --- MCE THRESHOLD CHECK (cumulative per person) ---
    # After enriching, check total insights per person across all of
    # INSIGHTS-STATE.json. If >= MCE_INSIGHT_THRESHOLD and no MCE YAMLs
    # exist for that person, log MCE_THRESHOLD_REACHED.
    mce_ready = _check_mce_thresholds(normalized)
    if mce_ready:
        results["mce_threshold_reached"] = mce_ready

    return results


# ---------------------------------------------------------------------------
# MCE THRESHOLD CHECK (cumulative per person)
# ---------------------------------------------------------------------------


def _check_mce_thresholds(insights: list[Insight]) -> list[str]:
    """Check if any person has reached the MCE insight threshold cumulatively.

    Reads the consolidated INSIGHTS-STATE.json to count total insights per
    person across ALL pipeline runs. If a person has >= MCE_INSIGHT_THRESHOLD
    insights and no MCE VOICE-DNA.yaml exists yet, log MCE_THRESHOLD_REACHED.

    Args:
        insights: List of Insight objects from this enrichment run (used to
            identify which persons to check).

    Returns:
        List of person slugs that have reached the MCE threshold.
    """
    from core.paths import ARTIFACTS, KNOWLEDGE_EXTERNAL

    # Collect unique person slugs from this run.
    persons_to_check = {i.person_slug for i in insights if i.person_slug}
    if not persons_to_check:
        return []

    # Load INSIGHTS-STATE.json to count total insights per person.
    insights_state_path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    person_counts: dict[str, int] = {}

    if insights_state_path.exists():
        try:
            data = json.loads(insights_state_path.read_text(encoding="utf-8"))

            # Handle multiple INSIGHTS-STATE.json formats.
            if isinstance(data, dict):
                # Format: {"persons": {"slug": {"insights": [...]}}}
                persons_data = data.get("persons", {})
                if isinstance(persons_data, dict):
                    for slug, pdata in persons_data.items():
                        if isinstance(pdata, dict):
                            ins = pdata.get("insights", [])
                            person_counts[slug.lower()] = len(ins) if isinstance(ins, list) else 0

                # Format: {"insights": [{...}, ...]}
                all_insights = data.get("insights", [])
                if isinstance(all_insights, list):
                    for item in all_insights:
                        if isinstance(item, dict):
                            slug = item.get("person_slug", "").lower()
                            if slug:
                                person_counts[slug] = person_counts.get(slug, 0) + 1
        except (json.JSONDecodeError, OSError):
            logger.debug("Could not read INSIGHTS-STATE.json for MCE threshold check")

    # Check each person from this run.
    mce_ready: list[str] = []

    for slug in persons_to_check:
        count = person_counts.get(slug, 0)
        if count < MCE_INSIGHT_THRESHOLD:
            continue

        # Check if MCE VOICE-DNA.yaml already exists (MCE already ran).
        voice_dna = KNOWLEDGE_EXTERNAL / "dna" / "persons" / slug / "VOICE-DNA.yaml"
        if voice_dna.exists():
            continue

        mce_ready.append(slug)
        logger.info(
            "MCE_THRESHOLD_REACHED: %s has %d insights (threshold=%d), "
            "no VOICE-DNA.yaml found -- MCE extraction eligible",
            slug,
            count,
            MCE_INSIGHT_THRESHOLD,
        )

    return mce_ready


# ---------------------------------------------------------------------------
# CONVENIENCE: enrich from INSIGHTS-STATE.json
# ---------------------------------------------------------------------------


def enrich_from_insights_state(
    insights_state_path: Path | None = None,
) -> dict[str, Any]:
    """Load insights from INSIGHTS-STATE.json and enrich all agents.

    This is a convenience function for backfilling -- reads the consolidated
    insights state file and routes each insight to the correct agents.

    Args:
        insights_state_path: Path to INSIGHTS-STATE.json.
            Defaults to artifacts/insights/INSIGHTS-STATE.json.

    Returns:
        Same dict as enrich().
    """
    if insights_state_path is None:
        from core.paths import ARTIFACTS

        insights_state_path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"

    if not insights_state_path.exists():
        logger.warning("INSIGHTS-STATE.json not found at %s", insights_state_path)
        return {"appended": 0, "skipped_dedup": 0, "skipped_no_agent": 0, "errors": []}

    try:
        data = json.loads(insights_state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"appended": 0, "errors": [f"Failed to read state: {exc}"]}

    # INSIGHTS-STATE.json may have various formats; handle the common ones.
    insight_list: list[dict] = []

    if isinstance(data, list):
        insight_list = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ("insights", "items", "data"):
            if key in data and isinstance(data[key], list):
                insight_list = data[key]
                break

    if not insight_list:
        logger.info("No insights found in %s", insights_state_path)
        return {"appended": 0, "skipped_dedup": 0, "skipped_no_agent": 0, "errors": []}

    return enrich(insight_list)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for standalone or backfill usage."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="memory_enricher",
        description="Enrich agent MEMORY.md files with pipeline insights.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Path to INSIGHTS-STATE.json (default: artifacts/insights/INSIGHTS-STATE.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    results = enrich_from_insights_state(args.state_file)

    print("\nMemory Enrichment Results:")
    print(f"  Insights appended:       {results.get('appended', 0)}")
    print(f"  Skipped (duplicate):     {results.get('skipped_dedup', 0)}")
    print(f"  Skipped (no agent):      {results.get('skipped_no_agent', 0)}")
    print(f"  Errors:                  {len(results.get('errors', []))}")

    if results.get("agents_enriched"):
        print("  Agents enriched:")
        for agent in results["agents_enriched"]:
            print(f"    [+] {agent}")

    if results.get("errors"):
        print("  Errors:")
        for err in results["errors"]:
            print(f"    [!] {err}")

    return 1 if results.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
