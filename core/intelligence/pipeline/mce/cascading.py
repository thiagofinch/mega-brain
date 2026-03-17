"""
cascading.py -- Post-extraction cascade for MCE pipeline
=========================================================
Routes extracted insights from INSIGHTS-STATE.json to:
  1. Cargo agent MEMORY.md files (via DNA-CONFIG.yaml reverse lookup)
  2. Theme dossiers in knowledge/external/dossiers/themes/

Ported from .claude/hooks/post_batch_cascading.py but adapted to work
with the INSIGHTS-STATE.json format (person-keyed, not batch-keyed).

Called directly by orchestrate.cmd_finalize() as a Python import,
not as a PostToolUse hook -- so it fires reliably every time.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - Append-only to MEMORY.md / dossier files.
    - JSONL logging to logs/cascading.jsonl.

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from core.paths import (
    AGENTS_CARGO,
    KNOWLEDGE_EXTERNAL,
    LOGS,
    ROOT,
)

logger = logging.getLogger("mce.cascading")

_CASCADING_LOG: Path = LOGS / "cascading.jsonl"
_DOSSIERS_DIR: Path = KNOWLEDGE_EXTERNAL / "dossiers" / "themes"


# ---------------------------------------------------------------------------
# JSONL logging
# ---------------------------------------------------------------------------


def _log_action(entry: dict[str, Any]) -> None:
    """Append a JSON line to the cascading audit log (non-fatal)."""
    try:
        _CASCADING_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["timestamp"] = datetime.now(UTC).isoformat()
        with open(_CASCADING_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write cascading log", exc_info=True)


# ---------------------------------------------------------------------------
# Agent discovery
# ---------------------------------------------------------------------------


def _find_cargo_agents_for_person(person_slug: str) -> list[Path]:
    """Find all cargo agents that consume DNA from a given person.

    Scans agents/cargo/**/DNA-CONFIG.yaml for entries in
    dna_sources.primario[].pessoa matching the slug.

    Args:
        person_slug: Kebab-case person identifier.

    Returns:
        List of cargo agent directory Paths.
    """
    targets: list[Path] = []
    slug_lower = person_slug.lower().strip()

    if not AGENTS_CARGO.is_dir():
        return targets

    for config_path in AGENTS_CARGO.rglob("DNA-CONFIG.yaml"):
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        dna_sources = data.get("dna_sources", {})
        if not isinstance(dna_sources, dict):
            continue

        primario = dna_sources.get("primario", [])
        if not isinstance(primario, list):
            continue

        for entry in primario:
            if not isinstance(entry, dict):
                continue
            pessoa = entry.get("pessoa", "").lower().strip()
            if pessoa == slug_lower:
                targets.append(config_path.parent)
                break

    return targets


# ---------------------------------------------------------------------------
# Cargo agent MEMORY.md update
# ---------------------------------------------------------------------------


def _update_cargo_memory(
    agent_dir: Path,
    insights: list[dict[str, Any]],
    person_slug: str,
) -> dict[str, Any]:
    """Append insights to a cargo agent's MEMORY.md.

    Args:
        agent_dir: Path to the cargo agent directory.
        insights: List of insight dicts to append.
        person_slug: Source person slug for attribution.

    Returns:
        Dict with update results.
    """
    memory_path = agent_dir / "MEMORY.md"
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    appended = 0

    # Create stub if MEMORY.md doesn't exist
    if not memory_path.exists():
        agent_name = " ".join(w.capitalize() for w in agent_dir.name.split("-"))
        memory_path.write_text(
            f"# MEMORY: {agent_name}\n\n"
            f"> **Atualizado:** {now}\n\n---\n\n"
            "## INSIGHTS EXTRAIDOS\n\n"
            "*Insights serao adicionados aqui automaticamente.*\n\n---\n\n"
            "## HISTORICO DE ATUALIZACOES\n\n"
            "| Data | Mudanca | Material Processado |\n"
            "|------|---------|---------------------|\n"
            f"| {now} | Criacao inicial (auto-gerado) | cascading.py v1.0 |\n",
            encoding="utf-8",
        )

    try:
        text = memory_path.read_text(encoding="utf-8")
    except Exception as exc:
        return {"error": str(exc), "appended": 0}

    for insight in insights:
        # Dedup: check if insight ID or chunk_id already present
        insight_id = insight.get("id", "") or insight.get("chunk_id", "")
        if insight_id and insight_id in text:
            continue

        title = insight.get("title", "") or insight.get("insight", "Insight")
        content = (
            insight.get("content")
            or insight.get("insight")
            or insight.get("summary")
            or title
        )
        tag = insight.get("tag", "")
        priority = insight.get("priority", "MEDIUM")

        entry = (
            f"\n### {now} - {title}\n\n"
            f"**Source:** {person_slug} | **Tag:** {tag} | **Priority:** {priority}\n\n"
        )
        if insight_id:
            entry += f"**ID:** {insight_id}\n\n"
        entry += f"{content}\n"

        # Insert before the HISTORICO section or at EOF
        hist_marker = "## HISTORICO DE ATUALIZACOES"
        hist_alt = "## HIST\u00d3RICO DE ATUALIZA\u00c7\u00d5ES"
        hist_pos = text.find(hist_marker)
        if hist_pos == -1:
            hist_pos = text.find(hist_alt)

        if hist_pos != -1:
            # Find the --- separator before HISTORICO
            sep_pos = text.rfind("---", 0, hist_pos)
            if sep_pos != -1:
                text = text[:sep_pos].rstrip() + "\n" + entry + "\n---\n\n" + text[hist_pos:]
            else:
                text = text[:hist_pos].rstrip() + "\n" + entry + "\n" + text[hist_pos:]
        else:
            text = text.rstrip() + "\n" + entry + "\n"

        appended += 1

    # Update the date header
    text = re.sub(
        r"(\*\*Atualizado:\*\*)\s*\d{4}-\d{2}-\d{2}",
        f"\\1 {now}",
        text,
        count=1,
    )

    try:
        memory_path.write_text(text, encoding="utf-8")
    except Exception as exc:
        return {"error": str(exc), "appended": appended}

    return {"appended": appended, "path": str(memory_path)}


# ---------------------------------------------------------------------------
# Theme dossier update
# ---------------------------------------------------------------------------


def _update_theme_dossiers(
    insights: list[dict[str, Any]],
    person_slug: str,
) -> dict[str, Any]:
    """Update theme dossiers with new insights grouped by category.

    Args:
        insights: List of insight dicts.
        person_slug: Source person for attribution.

    Returns:
        Dict with update results.
    """
    _DOSSIERS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    # Include HH:MM:SS in the section header so multiple same-day pipeline
    # runs produce unique markers and the dedup check does not falsely skip
    # the second run.  The date-only value (``now``) is kept for display
    # in dossier metadata fields where day-level granularity is sufficient.
    now_precise = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    # Group insights by category/theme
    by_theme: dict[str, list[dict]] = {}
    for ins in insights:
        cat = ins.get("category", "") or ins.get("dna_layer", "") or "general"
        # Normalize: lowercase, replace spaces with hyphens
        theme_key = cat.upper().replace(" ", "-").replace("_", "-")
        if theme_key not in by_theme:
            by_theme[theme_key] = []
        by_theme[theme_key].append(ins)

    themes_updated = 0
    themes_created = 0

    for theme_key, theme_insights in by_theme.items():
        # Update threshold: 2+ insights required. Lower than the create
        # threshold (3) because an existing dossier already has foundational
        # content -- even 2 new insights add meaningful enrichment.
        if len(theme_insights) < 2:
            continue

        dossier_name = f"DOSSIER-{theme_key}.md"
        dossier_path = _DOSSIERS_DIR / dossier_name

        if dossier_path.exists():
            try:
                text = dossier_path.read_text(encoding="utf-8")
                # Append a new section for this person's insights.
                # Uses ``now_precise`` (date + time) so multiple same-day
                # runs produce distinct sections and the dedup marker below
                # does not falsely suppress the second run.
                section = (
                    f"\n\n---\n\n"
                    f"## {person_slug.upper()} — Atualizacao {now_precise}\n\n"
                    f"**Fonte:** MCE Pipeline cascading\n"
                    f"**Insights:** {len(theme_insights)}\n\n"
                )
                for ins in theme_insights[:10]:  # cap at 10 per update
                    title = ins.get("title", "") or ins.get("insight", "")
                    priority = ins.get("priority", "MEDIUM")
                    section += f"- **[{priority}]** {title}\n"

                # Dedup: skip only if a section with this exact person +
                # timestamp already exists (second-level precision avoids
                # same-day collisions while still preventing true duplicates
                # within the same pipeline run).
                marker = f"{person_slug.upper()} — Atualizacao {now_precise}"
                if marker not in text:
                    text += section
                    dossier_path.write_text(text, encoding="utf-8")
                    themes_updated += 1
            except Exception as exc:
                logger.warning("Failed to update dossier %s: %s", dossier_path.name, exc)
        else:
            # Create threshold: 3+ insights required. Higher bar than
            # updates (2) because a brand-new dossier must carry enough
            # substance to justify its existence as a standalone file.
            if len(theme_insights) < 3:
                continue
            try:
                content = (
                    f"# DOSSIER: {theme_key}\n\n"
                    f"> **Versao:** 1.0.0\n"
                    f"> **Atualizado:** {now}\n"
                    f"> **Auto-gerado por:** cascading.py v1.0\n\n---\n\n"
                    f"## VISAO GERAL\n\n"
                    f"Theme dossier consolidando insights de multiplas fontes.\n\n"
                    f"---\n\n"
                    f"## {person_slug.upper()} — Atualizacao {now_precise}\n\n"
                    f"**Insights:** {len(theme_insights)}\n\n"
                )
                for ins in theme_insights[:10]:
                    title = ins.get("title", "") or ins.get("insight", "")
                    priority = ins.get("priority", "MEDIUM")
                    content += f"- **[{priority}]** {title}\n"

                dossier_path.write_text(content, encoding="utf-8")
                themes_created += 1
            except Exception as exc:
                logger.warning("Failed to create dossier %s: %s", dossier_path.name, exc)

    return {
        "themes_updated": themes_updated,
        "themes_created": themes_created,
        "themes_scanned": len(by_theme),
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def run_post_extraction_cascade(
    slug: str,
    insights_path: Path,
) -> dict[str, Any]:
    """Run the full post-extraction cascade for a person.

    Reads INSIGHTS-STATE.json, finds insights for the given slug,
    and cascades to cargo agents and theme dossiers.

    Args:
        slug: Person slug (e.g. "alex-hormozi").
        insights_path: Path to INSIGHTS-STATE.json.

    Returns:
        Dict with cascade results.
    """
    result: dict[str, Any] = {
        "slug": slug,
        "cargo_agents_updated": 0,
        "cargo_agents_found": 0,
        "themes_updated": 0,
        "themes_created": 0,
        "insights_processed": 0,
    }

    if not insights_path.exists():
        result["skipped"] = "INSIGHTS-STATE.json not found"
        return result

    try:
        data = json.loads(insights_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["error"] = f"Failed to read INSIGHTS-STATE: {exc}"
        return result

    # Collect insights for this slug from all sources in the file
    person_insights: list[dict] = []

    # Source 1: "persons" dict
    persons = data.get("persons", {})
    if isinstance(persons, dict):
        for person_name, pdata in persons.items():
            if not isinstance(pdata, dict):
                continue
            raw_slug = pdata.get("slug", "") or person_name
            p_slug = raw_slug.lower().strip().replace(" ", "-")
            if p_slug == slug:
                person_insights.extend(pdata.get("insights", []))

    # Source 2: flat "insights" list
    flat_insights = data.get("insights", [])
    if isinstance(flat_insights, list):
        for ins in flat_insights:
            if not isinstance(ins, dict):
                continue
            p_name = ins.get("person", "")
            p_slug = p_name.lower().strip().replace(" ", "-")
            if p_slug == slug:
                person_insights.append(ins)

    if not person_insights:
        result["skipped"] = f"No insights found for slug={slug}"
        _log_action({"action": "cascade_skipped", **result})
        return result

    result["insights_processed"] = len(person_insights)

    # --- Cascade to cargo agents ---
    cargo_dirs = _find_cargo_agents_for_person(slug)
    result["cargo_agents_found"] = len(cargo_dirs)

    for agent_dir in cargo_dirs:
        update_result = _update_cargo_memory(agent_dir, person_insights, slug)
        if update_result.get("appended", 0) > 0:
            result["cargo_agents_updated"] += 1
            _log_action({
                "action": "cargo_memory_updated",
                "agent": str(agent_dir.relative_to(ROOT)),
                "appended": update_result["appended"],
                "slug": slug,
            })

    # --- Cascade to theme dossiers ---
    dossier_result = _update_theme_dossiers(person_insights, slug)
    result["themes_updated"] = dossier_result.get("themes_updated", 0)
    result["themes_created"] = dossier_result.get("themes_created", 0)

    _log_action({"action": "cascade_complete", **result})
    logger.info(
        "Cascade complete for %s: %d cargo agents updated, %d themes updated, %d themes created",
        slug,
        result["cargo_agents_updated"],
        result["themes_updated"],
        result["themes_created"],
    )

    return result
