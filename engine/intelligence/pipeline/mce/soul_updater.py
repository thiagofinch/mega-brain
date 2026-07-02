"""SOUL.md Incremental Update — Story MCE-11.3.

Appends an evolution section to an existing agent's SOUL.md file using
HIGH-priority insights discovered during re-ingest.  This module is the
port of §8.1.9 ("SOUL.md Auto-Update") from the OLD MegaBrain pipeline.

Design constraints:
- Append-only: never modifies existing sections above the new entry.
- Idempotent: will not append a second entry for the same date.
- Non-blocking: callers wrap invocations in try/except — failures never
  abort cmd_finalize (Constitution Art. XII).
- No LLM calls: synthesis uses lightweight template-fill for speed and
  determinism (Wave B enhancement slot reserved for LLM synthesis).
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root resolution (portable — never hardcoded machine path)
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[4]  # mega-brain/


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _soul_path_for_slug(slug: str, bucket: str = "external") -> Path | None:
    """Return the path to the agent's SOUL.md (or soul.md) file.

    Checks:
    1. agents/{bucket}/{slug}/SOUL.md
    2. agents/{bucket}/{slug}/soul.md
    3. agents/{bucket}/cargo/**/{slug}/SOUL.md  (cargo agents)
    4. agents/{bucket}/cargo/**/{slug}/soul.md  (cargo agents, lowercase)

    Returns None when no file is found — caller handles as no-op.
    """
    base = _PROJECT_ROOT / "agents" / bucket

    # Direct agent path
    for name in ("SOUL.md", "soul.md"):
        candidate = base / slug / name
        if candidate.exists():
            return candidate

    # Cargo agents: agents/external/cargo/{category}/{slug}/SOUL.md
    cargo_root = base / "cargo"
    if cargo_root.exists():
        for name in ("SOUL.md", "soul.md"):
            matches = list(cargo_root.rglob(f"{slug}/{name}"))
            if matches:
                return matches[0]

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def update_soul(slug: str, insights: list[dict[str, Any]]) -> dict[str, Any]:
    """Append an evolution section to an existing SOUL.md with HIGH insights.

    Args:
        slug:     Agent slug (e.g. "alex-hormozi").
        insights: List of insight dicts from INSIGHTS-STATE.json (persons layer).
                  Each dict is expected to have at least: insight (str), tag (str),
                  priority (str), source (dict with source_id key).

    Returns:
        dict with keys:
            updated (bool)       — True when SOUL.md was modified
            sections_added (int) — Number of sections appended (0 or 1)
            reason (str)         — Human-readable outcome description
    """
    # AC3 — filter to HIGH priority only
    high_insights = [
        ins
        for ins in insights
        if isinstance(ins, dict) and ins.get("priority", "").upper() == "HIGH"
    ]

    if not high_insights:
        logger.debug("soul_updater: no HIGH insights for slug=%s — skipping", slug)
        return {"updated": False, "sections_added": 0, "reason": "no_high_insights"}

    # AC5 — resolve SOUL.md path; no-op if not found
    soul_path = _soul_path_for_slug(slug)
    if soul_path is None:
        logger.debug("soul_updater: no SOUL.md found for slug=%s — skipping", slug)
        return {"updated": False, "sections_added": 0, "reason": "no_soul_file"}

    today_str = date.today().isoformat()  # e.g. "2026-05-27"

    # Idempotency guard (Risk: append runs multiple times in same session)
    existing_content = soul_path.read_text(encoding="utf-8")
    idempotency_marker = f"## Evolucao {today_str}"
    if idempotency_marker in existing_content:
        logger.debug(
            "soul_updater: evolution section for %s already present in %s — skipping",
            today_str,
            soul_path,
        )
        return {"updated": False, "sections_added": 0, "reason": "already_updated_today"}

    # Derive source_id from first insight that has one
    source_id = "unknown"
    for ins in high_insights:
        src = ins.get("source")
        if isinstance(src, dict):
            candidate = src.get("source_id") or src.get("batch_id")
            if candidate:
                source_id = candidate
                break
        elif isinstance(src, str) and src:
            source_id = src
            break

    # AC4 — build evolution section (template-fill, no LLM)
    n = len(high_insights)
    bullet_lines = []
    # Include up to 5 insight bullets for readability
    for ins in high_insights[:5]:
        text = ins.get("insight", "").strip()
        tag = ins.get("tag", "").strip()
        if text:
            suffix = f" {tag}" if tag else ""
            bullet_lines.append(f"- {text}{suffix}")

    # Collect signature phrases (quote field, up to 3)
    sig_phrases = []
    for ins in high_insights:
        quote = ins.get("quote", "").strip()
        if quote and len(sig_phrases) < 3:
            sig_phrases.append(quote)

    # Build section text
    lines: list[str] = [
        "",
        f"## Evolucao {today_str}",
        "",
        f"*Atualizado apos ingestao de `{source_id}` ({n} insights HIGH)*",
        "",
    ]

    lines.extend(bullet_lines)

    if sig_phrases:
        lines.append("")
        lines.append("**Novas frases-assinatura identificadas:**")
        for phrase in sig_phrases:
            lines.append(f"- {phrase}")

    lines.append("")

    section_text = "\n".join(lines)

    # AC4 — append-only write
    with soul_path.open("a", encoding="utf-8") as fh:
        fh.write(section_text)

    logger.info(
        "soul_updater: appended evolution section to %s (%d HIGH insights, source=%s)",
        soul_path,
        n,
        source_id,
    )

    return {
        "updated": True,
        "sections_added": 1,
        "reason": f"appended evolution section ({n} HIGH insights from {source_id})",
        "soul_path": str(soul_path),
    }


def update_soul_incremental(slug: str, bucket: str = "external") -> dict[str, Any]:
    """Convenience wrapper: reads INSIGHTS-STATE, extracts HIGH insights, calls update_soul.

    This is the entry point invoked from cmd_finalize.  It handles INSIGHTS-STATE
    discovery (slug-isolated path with legacy fallback) so the caller does not need
    to pass the insights list explicitly.

    Args:
        slug:   Agent slug.
        bucket: Knowledge bucket ("external", "business", "personal").

    Returns:
        Same dict as update_soul(), plus optional "insights_source" key.
    """
    artifacts_root = _PROJECT_ROOT / ".data" / "artifacts"
    slug_insights = artifacts_root / "insights" / slug / "INSIGHTS-STATE.json"
    legacy_insights = artifacts_root / "insights" / "INSIGHTS-STATE.json"

    insights_path = (
        slug_insights
        if slug_insights.exists()
        else (legacy_insights if legacy_insights.exists() else None)
    )

    if insights_path is None:
        logger.debug("soul_updater: INSIGHTS-STATE.json not found for slug=%s", slug)
        return {
            "updated": False,
            "sections_added": 0,
            "reason": "no_insights_state",
            "insights_source": None,
        }

    try:
        data = json.loads(insights_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("soul_updater: cannot read %s: %s", insights_path, exc)
        return {
            "updated": False,
            "sections_added": 0,
            "reason": f"insights_read_error: {exc}",
        }

    # Collect all insights across persons layer
    all_insights: list[dict[str, Any]] = []
    persons = data.get("persons", {})
    if isinstance(persons, dict):
        for pdata in persons.values():
            if isinstance(pdata, dict):
                all_insights.extend(
                    ins for ins in pdata.get("insights", []) if isinstance(ins, dict)
                )

    result = update_soul(slug, all_insights)
    result["insights_source"] = str(insights_path)
    return result
