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

Dual-Zone Mode (Story W3-001.1):
  When MEMORY_ENRICHER_DUAL_ZONE=true (env var, default: false):
  - ## State section: rewrite (replaced entirely each enrichment pass)
  - ## Timeline section: append-only (entries never deleted)
  When MEMORY_ENRICHER_DUAL_ZONE=false or unset:
  - Behavior is 100% identical to v1.0.0 (zero regression)

Integration:
    Called by batch_auto_creator.py after batch creation (ImportError safe).
    Also callable standalone for backfill.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from engine.paths.
    - JSONL logging.

Version: 2.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

from engine.paths import (  # noqa: E402
    AGENTS_BUSINESS,
    AGENTS_CARGO,
    AGENTS_EXTERNAL,
    LOGS,
    ROUTING,
)

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
# DUAL-ZONE FEATURE FLAG (Story W3-001.1)
# ---------------------------------------------------------------------------
# When true: MEMORY.md gets two zones:
#   ## State   -- rewrite (replaced each enrichment pass with current state)
#   ## Timeline -- append-only (entries never deleted)
# When false: behavior is 100% identical to v1.0.0.

DUAL_ZONE_ENABLED: bool = os.environ.get("MEMORY_ENRICHER_DUAL_ZONE", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# Section headers for dual-zone mode.
STATE_SECTION_HEADER = "## State"
TIMELINE_SECTION_HEADER = "## Timeline"


def is_dual_zone_enabled() -> bool:
    """Return whether dual-zone mode is currently active.

    Re-reads the environment variable each time so tests can toggle it
    without reloading the module.
    """
    return os.environ.get("MEMORY_ENRICHER_DUAL_ZONE", "false").strip().lower() in (
        "true",
        "1",
        "yes",
    )


# ---------------------------------------------------------------------------
# INSIGHT DATA STRUCTURE
# ---------------------------------------------------------------------------


class Insight:
    """Represents a single insight to be enriched into agent MEMORY.md.

    Attributes:
        person_slug: Kebab-case person identifier (e.g., 'alex-hormozi').
        chunk_id: Unique chunk identifier for dedup (e.g., 'chunk_199').
        insight_id: Optional insight identifier (e.g., 'CF001').
        tag: Source tag (e.g., 'AH-SRC001').
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
    # Canonical lowercase first; fall back to UPPERCASE for cargo agents (legacy convention)
    memory_path = agent_dir / "memory.md"
    if not memory_path.exists():
        legacy_path = agent_dir / "MEMORY.md"
        if legacy_path.exists():
            return legacy_path

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
# DUAL-ZONE MODE (Story W3-001.1)
# ---------------------------------------------------------------------------
# When MEMORY_ENRICHER_DUAL_ZONE=true, MEMORY.md gets two zones:
#   ## State    -- rewrite (replaced entirely each enrichment pass)
#   ## Timeline -- append-only (entries never deleted, only appended)
#
# The original _append_insight is NEVER modified -- dual-zone routes to
# _append_insight_dual_zone instead.
# ---------------------------------------------------------------------------


def _find_section_bounds(text: str, header: str) -> tuple[int, int] | None:
    """Find the start (inclusive of header) and end of a ## section.

    End is defined as the character position just before the next ``## ``
    marker, or EOF if no subsequent section exists.

    Args:
        text: Full markdown text.
        header: The exact section header string (e.g. ``"## State"``).

    Returns:
        Tuple of (start, end) character positions, or None if not found.
    """
    pos = text.find(header)
    if pos == -1:
        return None

    # Search for next section after this header
    search_start = pos + len(header)
    remaining = text[search_start:]

    next_match = SECTION_MARKER_RE.search(remaining)
    if next_match is not None:
        end = search_start + next_match.start()
    else:
        end = len(text)

    return (pos, end)


def _build_state_section(insights: list[Insight], date: str) -> str:
    """Build the full ``## State`` section content (rewrite mode).

    This section is replaced entirely on each enrichment pass. It represents
    the current snapshot of recently enriched insights for this agent.

    Args:
        insights: All insights being enriched in this pass for this agent.
        date: ISO date string.

    Returns:
        Full section text including the ``## State`` header.
    """
    lines: list[str] = []
    lines.append(STATE_SECTION_HEADER)
    lines.append("")
    lines.append(f"> Last updated: {date}")
    lines.append(f"> Insights in current state: {len(insights)}")
    lines.append("")

    for insight in insights:
        lines.append(f"### {insight.title or 'Insight from Pipeline'}")
        lines.append("")
        if insight.content:
            lines.append(insight.content)
            lines.append("")
        # Traceability table
        lines.append("| Campo | Valor |")
        lines.append("|-------|-------|")
        if insight.insight_id:
            lines.append(f"| insight_id | {insight.insight_id} |")
        if insight.chunk_id:
            lines.append(f"| chunk_id | {insight.chunk_id} |")
        if insight.batch_id:
            lines.append(f"| batch_id | {insight.batch_id} |")
        if insight.tag:
            lines.append(f"| tag | {insight.tag} |")
        if insight.priority:
            lines.append(f"| priority | {insight.priority} |")
        lines.append("")

    return "\n".join(lines)


def _build_timeline_entry(insight: Insight, date: str) -> str:
    """Build a single timeline entry for the ``## Timeline`` section.

    Timeline entries are append-only -- they are never deleted or modified.

    Args:
        insight: The insight to record.
        date: ISO date string.

    Returns:
        Formatted markdown string for one timeline entry.
    """
    title = insight.title or insight.chunk_id or "Pipeline insight"
    source = insight.batch_id or insight.tag or "memory_enricher"
    chunk = insight.chunk_id or "n/a"
    return f"- **[{date}]** {title} | chunk: `{chunk}` | source: {source}"


def _append_insight_dual_zone(
    memory_path: Path,
    insights_for_agent: list[Insight],
) -> int:
    """Enrich a MEMORY.md using dual-zone mode.

    - ``## State`` is rewritten entirely with the current batch of insights.
    - ``## Timeline`` receives one append-only entry per new insight (deduped).

    Args:
        memory_path: Absolute path to the MEMORY.md file.
        insights_for_agent: All insights destined for this agent in this pass.

    Returns:
        Number of insights successfully appended to Timeline (new, non-dedup).
    """
    try:
        text = memory_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Cannot read %s: %s", memory_path, exc)
        return 0

    now = datetime.now(UTC).strftime("%Y-%m-%d")
    appended_count = 0

    # --- REWRITE: ## State section ---
    new_state = _build_state_section(insights_for_agent, now)

    state_bounds = _find_section_bounds(text, STATE_SECTION_HEADER)
    if state_bounds is not None:
        start, end = state_bounds
        text = text[:start] + new_state + "\n\n" + text[end:].lstrip("\n")
    else:
        # Insert ## State before ## Timeline, or before first ## section, or at EOF
        timeline_bounds = _find_section_bounds(text, TIMELINE_SECTION_HEADER)
        if timeline_bounds is not None:
            insert_at = timeline_bounds[0]
            text = text[:insert_at] + new_state + "\n\n---\n\n" + text[insert_at:]
        else:
            # Find insertion point: after the header block (first ---)
            first_hr = text.find("\n---\n")
            if first_hr != -1:
                insert_at = first_hr + len("\n---\n")
                text = text[:insert_at] + "\n" + new_state + "\n\n---\n\n" + text[insert_at:]
            else:
                text = text.rstrip() + "\n\n" + new_state + "\n"

    # --- APPEND-ONLY: ## Timeline section ---
    # Ensure ## Timeline section exists
    if TIMELINE_SECTION_HEADER not in text:
        # Append at the very end
        text = text.rstrip() + "\n\n---\n\n" + TIMELINE_SECTION_HEADER + "\n\n"

    for insight in insights_for_agent:
        # Dedup: check if chunk_id already exists in the TIMELINE section only.
        # We must NOT check the full file because State also contains chunk_ids
        # and would cause false-positive dedup on every pass.
        timeline_bounds = _find_section_bounds(text, TIMELINE_SECTION_HEADER)
        timeline_text = ""
        if timeline_bounds is not None:
            timeline_text = text[timeline_bounds[0] : timeline_bounds[1]]
        if _is_duplicate(timeline_text, insight.chunk_id):
            logger.debug(
                "Duplicate chunk_id '%s' in %s timeline, skipping",
                insight.chunk_id,
                memory_path,
            )
            continue

        entry = _build_timeline_entry(insight, now)

        # Append entry at the end of the ## Timeline section
        timeline_bounds = _find_section_bounds(text, TIMELINE_SECTION_HEADER)
        if timeline_bounds is not None:
            _, end = timeline_bounds
            # Insert just before end (which is next section or EOF)
            insert_text = entry + "\n"
            text = text[:end].rstrip() + "\n" + insert_text + "\n" + text[end:].lstrip("\n")
        else:
            # Should not happen since we ensured it exists above
            text = text.rstrip() + "\n" + entry + "\n"

        appended_count += 1

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
        logger.info(
            "Dual-zone enriched %s: state rewritten, %d timeline entries added",
            memory_path,
            appended_count,
        )
        return appended_count
    except Exception as exc:
        logger.warning("Failed to write %s: %s", memory_path, exc)
        return 0


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

        from engine.intelligence.pipeline.memory_enricher import enrich

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

    # Validate all insights first (shared by both modes)
    valid_insights: list[Insight] = []
    for insight in normalized:
        if not insight.person_slug:
            results["errors"].append(f"Missing person_slug for chunk_id={insight.chunk_id}")
            continue
        if not insight.chunk_id:
            results["errors"].append(f"Missing chunk_id for person_slug={insight.person_slug}")
            continue
        valid_insights.append(insight)

    if is_dual_zone_enabled():
        # --- DUAL-ZONE MODE ---
        # Batch insights per agent directory, then call _append_insight_dual_zone
        # once per agent with all insights for that agent.
        agent_batches: dict[Path, list[Insight]] = {}

        for insight in valid_insights:
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
                if agent_dir not in agent_batches:
                    agent_batches[agent_dir] = []
                agent_batches[agent_dir].append(insight)

        for agent_dir, agent_insights in agent_batches.items():
            memory_path = _create_memory_if_missing(agent_dir)
            appended = _append_insight_dual_zone(memory_path, agent_insights)
            results["appended"] += appended
            results["skipped_dedup"] += len(agent_insights) - appended
            if appended > 0:
                try:
                    rel = str(agent_dir.relative_to(_ROOT))
                except ValueError:
                    rel = str(agent_dir)
                enriched_agents.add(rel)
    else:
        # --- LEGACY MODE (v1.0.0 behavior, zero changes) ---
        for insight in valid_insights:
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
    from engine.paths import ARTIFACTS, KNOWLEDGE_EXTERNAL

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
                # Format A (current): {"persons": {"Display Name": {"slug": "x", "insights": [...]}}}
                # Also handles legacy: {"persons": {"slug": {"insights": [...]}}}
                persons_data = data.get("persons", {})
                if isinstance(persons_data, dict):
                    for key, pdata in persons_data.items():
                        if isinstance(pdata, dict):
                            # Use the nested slug field if present, otherwise use the key itself
                            slug = pdata.get("slug", key).lower().strip()
                            # Normalize display-name keys to kebab-case slugs
                            if " " in slug:
                                slug = slug.lower().replace(" ", "-")
                            ins = pdata.get("insights", [])
                            count = len(ins) if isinstance(ins, list) else 0
                            person_counts[slug] = person_counts.get(slug, 0) + count

                # Format B (current): {"categories": {"cat_name": {"insights": [...]}}}
                # Count insights per person from the flat insights lists inside categories.
                categories_data = data.get("categories", {})
                if isinstance(categories_data, dict):
                    for _cat_name, cat_data in categories_data.items():
                        if not isinstance(cat_data, dict):
                            continue
                        cat_insights = cat_data.get("insights", [])
                        if not isinstance(cat_insights, list):
                            continue
                        for item in cat_insights:
                            if not isinstance(item, dict):
                                continue
                            slug = item.get("person_slug", "").lower().strip()
                            if slug:
                                person_counts[slug] = person_counts.get(slug, 0) + 1

                # Format C: {"insights": [{person_slug: ...}, ...]}
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
        from engine.paths import ARTIFACTS

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
        # Format A (current): {"categories": {"cat_name": {"insights": [...]}}}
        categories_data = data.get("categories", {})
        if isinstance(categories_data, dict) and categories_data:
            for cat_name, cat_data in categories_data.items():
                if not isinstance(cat_data, dict):
                    continue
                cat_insights = cat_data.get("insights", [])
                if isinstance(cat_insights, list):
                    for item in cat_insights:
                        if isinstance(item, dict):
                            # Normalize: map category-format fields to enricher fields
                            normalized: dict[str, str] = {}
                            normalized["chunk_id"] = item.get("id", "")
                            normalized["title"] = item.get("insight", item.get("title", ""))
                            normalized["content"] = item.get("insight", item.get("content", ""))
                            normalized["priority"] = item.get("priority", "MEDIUM")
                            normalized["tag"] = item.get("tag", "")
                            # person_slug may not be in category insights; try to infer
                            normalized["person_slug"] = item.get("person_slug", "")
                            # Carry over any fields that match Insight slots directly
                            for key in ("insight_id", "path_raiz", "batch_id"):
                                if key in item:
                                    normalized[key] = item[key]
                            insight_list.append(normalized)

        # Format B (current): {"persons": {"Name": {"slug": "x", "insights": [...]}}}
        persons_data = data.get("persons", {})
        if isinstance(persons_data, dict):
            for _display_name, pdata in persons_data.items():
                if not isinstance(pdata, dict):
                    continue
                slug = pdata.get("slug", _display_name).lower().strip()
                if " " in slug:
                    slug = slug.lower().replace(" ", "-")
                person_insights = pdata.get("insights", [])
                if isinstance(person_insights, list):
                    for item in person_insights:
                        if isinstance(item, dict):
                            normalized = dict(item)
                            # Ensure person_slug is set
                            if "person_slug" not in normalized or not normalized["person_slug"]:
                                normalized["person_slug"] = slug
                            # Map 'id' to 'chunk_id' if chunk_id missing
                            if "chunk_id" not in normalized and "id" in normalized:
                                normalized["chunk_id"] = normalized["id"]
                            # Map 'insight' text to 'title'/'content' if missing
                            if "title" not in normalized and "insight" in normalized:
                                normalized["title"] = normalized["insight"]
                            if "content" not in normalized and "insight" in normalized:
                                normalized["content"] = normalized["insight"]
                            insight_list.append(normalized)

        # Format C: {"insights": [{...}, ...]} (flat list with person_slug)
        flat_insights = data.get("insights", [])
        if isinstance(flat_insights, list):
            for item in flat_insights:
                if isinstance(item, dict):
                    insight_list.append(item)

        # Fallback: try "items" or "data" keys
        if not insight_list:
            for key in ("items", "data"):
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
