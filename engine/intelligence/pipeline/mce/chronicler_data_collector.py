"""
chronicler_data_collector.py -- Chronicler Data Collector (centralized)
======================================================================
Centralizes ALL data collection for MCE pipeline rendering, eliminating
the three divergent implementations that cause bugs RC1 (slug detection)
and RC3 (person name lookup).

Public API
----------
- ``resolve_person_name(slug)``       -- Canonical name with accents
- ``resolve_slug_from_path(path)``    -- Slug from any pipeline path
- ``collect_checkpoint_data(slug, template_id, bucket)`` -- Template data
- ``collect_session_data(session_hours)``  -- Session consolidation
- ``collect_final_log_data(slug, ...)``    -- Final log data for Chronicler

Data Sources
~~~~~~~~~~~~
- ``artifacts/canonical/CANONICAL-MAP.json``
- ``artifacts/insights/INSIGHTS-STATE.json``
- ``artifacts/chunks/CHUNKS-STATE.json``
- ``knowledge/external/dna/persons/{slug}/DNA-CONFIG.yaml``
- ``.claude/mission-control/mce/{slug}/metadata.yaml``
- ``.claude/mission-control/mce/{slug}/metrics.yaml``
- ``logs/mce-step-logger.jsonl``
- ``logs/mce-orchestrate.jsonl``

Constraints
~~~~~~~~~~~
- Python 3, stdlib + PyYAML only.
- Never raises exceptions -- returns safe defaults.
- All functions importable independently.

Version: 1.0.0
Date: 2026-03-20
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from engine.intelligence.utils.agent_files import find_agent_file  # MCE-13.6
from engine.paths import ARTIFACTS, LOGS, MISSION_CONTROL, ROOT

logger = logging.getLogger("mce.chronicler_data_collector")

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Segments that should never be returned as a person slug.
# SYNC: This constant is intentionally duplicated in .claude/hooks/mce_step_logger.py
#        (_slug_from_path). Both implementations MUST use the same set. Changes here
#        MUST be mirrored there (and vice-versa). Validated by test_slug_sync.py.
SKIP_SEGMENTS: frozenset[str] = frozenset(
    {
        "dna",
        "dossiers",
        "sources",
        "inbox",
        "chunks",
        "canonical",
        "insights",
        "by-person",
        "persons",
        "themes",
        "calls",
        "meetings",
        "blueprints",
        "podcasts",
        "youtube",
        "misc",
        "collaborators",
        "cargo",
        "system",
    }
)

# Knowledge bucket markers in path segments.
_BUCKET_MARKERS: frozenset[str] = frozenset({"external", "business", "personal"})


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE FILE LOADERS
# ═══════════════════════════════════════════════════════════════════════════════


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file, returning empty dict on any failure."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception:
        logger.debug("Failed to load JSON: %s", path, exc_info=True)
    return {}


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict on any failure."""
    try:
        if path.exists():
            import yaml

            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception:
        logger.debug("Failed to load YAML: %s", path, exc_info=True)
    return {}


def _read_jsonl_recent(path: Path, hours: float) -> list[dict[str, Any]]:
    """Read JSONL entries from the last N hours. Returns empty list on failure."""
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("timestamp", "")
                    if ts_str:
                        # Parse ISO timestamp (handles +00:00 and Z suffixes)
                        ts_clean = ts_str.replace("Z", "+00:00")
                        ts = datetime.fromisoformat(ts_clean)
                        if ts >= cutoff:
                            entries.append(entry)
                    else:
                        # No timestamp -- include by default
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception:
        logger.debug("Failed to read JSONL: %s", path, exc_info=True)
    return entries


# ═══════════════════════════════════════════════════════════════════════════════
# resolve_person_name
# ═══════════════════════════════════════════════════════════════════════════════


def resolve_person_name(slug: str) -> str:
    """Resolve a slug to the canonical person name (with accents).

    Priority chain:
        1. CANONICAL-MAP.json -- canonical_state.canonical_map keys
        2. metadata.yaml -- persona field or person field
        3. INSIGHTS-STATE.json -- persons dict keys
        4. DNA-CONFIG.yaml -- person field
        5. Fallback: capitalize each word from slug

    Args:
        slug: Person slug, e.g. ``"jane-doe"``.

    Returns:
        Canonical person name (e.g. ``"Jane Doe"``), or a
        capitalize-from-slug fallback if no source has the name.
        Never raises.
    """
    if not slug:
        return ""

    fallback = " ".join(w.capitalize() for w in slug.split("-"))

    # --- Priority 1: CANONICAL-MAP.json ---
    canonical_path = ARTIFACTS / "canonical" / "CANONICAL-MAP.json"
    canonical = _load_json(canonical_path)

    # The canonical map has two levels where names live:
    #   - canonical_state.canonical_map: {Name: [aliases]}
    #   - Top-level persons/entities dicts
    canonical_map = canonical.get("canonical_state", {}).get("canonical_map", {})

    # Build a slug->name lookup from canonical map keys
    for name in canonical_map:
        name_slug = name.lower().replace(" ", "-").replace("_", "-")
        # Also strip accents for fuzzy matching
        name_slug_ascii = _strip_accents(name_slug)
        slug_ascii = _strip_accents(slug)
        if name_slug == slug or name_slug_ascii == slug_ascii:
            return name

    # Also check top-level "persons" dict in canonical map
    persons_dict = canonical.get("persons", {})
    if isinstance(persons_dict, dict):
        for name in persons_dict:
            name_slug = name.lower().replace(" ", "-").replace("_", "-")
            name_slug_ascii = _strip_accents(name_slug)
            slug_ascii = _strip_accents(slug)
            if name_slug == slug or name_slug_ascii == slug_ascii:
                return name

    # --- Priority 2: metadata.yaml ---
    meta = _load_yaml(MISSION_CONTROL / "mce" / slug / "metadata.yaml")
    meta_name = meta.get("person", meta.get("persona", ""))
    if meta_name and isinstance(meta_name, str) and meta_name != slug:
        return meta_name

    # --- Priority 3: INSIGHTS-STATE.json ---
    insights = _load_json(ARTIFACTS / "insights" / "INSIGHTS-STATE.json")
    persons_insights = insights.get("persons", {})
    if isinstance(persons_insights, dict):
        for name in persons_insights:
            name_slug = name.lower().replace(" ", "-").replace("_", "-")
            name_slug_ascii = _strip_accents(name_slug)
            slug_ascii = _strip_accents(slug)
            if name_slug == slug or name_slug_ascii == slug_ascii:
                return name

    # --- Priority 4: DNA-CONFIG.yaml ---
    dna_config = _load_yaml(
        ROOT / "knowledge" / "external" / "dna" / "persons" / slug / "DNA-CONFIG.yaml"
    )
    dna_name = dna_config.get("person", "")
    if dna_name and isinstance(dna_name, str):
        return dna_name

    # --- Priority 5: fallback capitalize ---
    return fallback


def _strip_accents(text: str) -> str:
    """Remove common accents for fuzzy slug matching.

    Uses unicodedata normalization (stdlib) to decompose accented characters,
    then strips the combining marks.
    """
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ═══════════════════════════════════════════════════════════════════════════════
# resolve_slug_from_path
# ═══════════════════════════════════════════════════════════════════════════════


def resolve_slug_from_path(path: str) -> str:
    """Extract the person/source slug from a pipeline file path.

    Priority chain:
        1. Segment after ``persons/`` (highest priority)
        2. Segment after bucket markers (``external/``, ``business/``, ``personal/``)
           with SKIP_SEGMENTS filtering
        3. Segment after ``agents/`` with SKIP_SEGMENTS filtering
        4. Active pipeline scan from ``.claude/mission-control/mce/``
        5. Empty string fallback

    SYNC: This logic is intentionally duplicated (inline) in
          ``.claude/hooks/mce_step_logger.py`` ``_slug_from_path()``.
          Both implementations MUST produce identical results.
          Validated by ``tests/python/test_pipeline/test_slug_sync.py``.

    Args:
        path: Absolute or relative file path from the pipeline.

    Returns:
        Slug string (e.g. ``"process-architect"``), or ``""`` if no slug
        can be determined. Never raises.
    """
    if not path:
        return ""

    try:
        parts = Path(path).parts
    except Exception:
        return ""

    # --- Priority 1: segment after "persons" ---
    for i, part in enumerate(parts):
        if part == "persons" and i + 1 < len(parts):
            candidate = parts[i + 1]
            # Skip files (contain dots like DOSSIER-PEDRO.md)
            if "." not in candidate:
                return candidate

    # --- Priority 2: segment after bucket markers, walking past structural dirs ---
    for i, part in enumerate(parts):
        if part in _BUCKET_MARKERS:
            # Walk forward past SKIP_SEGMENTS to find the real slug
            for j in range(i + 1, len(parts)):
                candidate = parts[j]
                if "." in candidate:
                    break  # Hit a filename, stop walking
                if candidate not in SKIP_SEGMENTS:
                    return candidate

    # --- Priority 3: segment after "agents", walking past structural dirs ---
    for i, part in enumerate(parts):
        if part == "agents":
            for j in range(i + 1, len(parts)):
                candidate = parts[j]
                if "." in candidate:
                    break
                if candidate not in SKIP_SEGMENTS:
                    return candidate

    # --- Priority 4: active pipeline scan ---
    # For artifact paths (chunks, insights, etc.), try to find the active slug
    # from mission-control MCE state directories.
    path_lower = path.lower()
    if any(marker in path_lower for marker in ("artifacts/", "chunks", "insights")):
        slug = _scan_active_pipeline()
        if slug:
            return slug

    return ""


def _scan_active_pipeline() -> str:
    """Scan .claude/mission-control/mce/ for the most recently active pipeline.

    Returns the slug of the pipeline with the most recent metadata update,
    or empty string if nothing found.
    """
    mce_dir = MISSION_CONTROL / "mce"
    if not mce_dir.exists():
        return ""

    best_slug = ""
    best_time = ""

    try:
        for entry in mce_dir.iterdir():
            if not entry.is_dir():
                continue
            meta_path = entry / "metadata.yaml"
            if meta_path.exists():
                meta = _load_yaml(meta_path)
                updated = meta.get("updated_at", meta.get("started_at", ""))
                if isinstance(updated, str) and updated > best_time:
                    best_time = updated
                    best_slug = entry.name
    except Exception:
        logger.debug("Failed to scan MCE state dir", exc_info=True)

    return best_slug


# ═══════════════════════════════════════════════════════════════════════════════
# collect_checkpoint_data
# ═══════════════════════════════════════════════════════════════════════════════


def collect_checkpoint_data(
    slug: str,
    template_id: int,
    bucket: str = "external",
) -> dict[str, Any]:
    """Collect all data needed to render a specific MCE output template.

    Returns a self-contained dict with everything the renderer needs.
    Template-specific data is collected based on ``template_id``.

    Args:
        slug: Person slug (e.g. ``"process-architect"``).
        template_id: MCE template number (1-7).
        bucket: Knowledge bucket (``"external"``, ``"business"``, ``"personal"``).

    Returns:
        Dict with keys: ``template_id``, ``slug``, ``person_name``, ``bucket``,
        ``timestamp``, ``metrics``, ``deltas``, ``validation``, ``progress``,
        ``files``, ``insights``, ``dna``. Never raises.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    person_name = resolve_person_name(slug)

    # Base context present in all templates
    ctx: dict[str, Any] = {
        "template_id": template_id,
        "slug": slug,
        "person_name": person_name,
        "bucket": bucket,
        "timestamp": now,
        "metrics": {},
        "deltas": {},
        "validation": {},
        "progress": {},
        "files": {},
        "insights": {},
        "dna": {},
    }

    # Load common data sources
    metadata = _load_yaml(MISSION_CONTROL / "mce" / slug / "metadata.yaml")
    metrics_data = _load_yaml(MISSION_CONTROL / "mce" / slug / "metrics.yaml")
    chunks_state = _load_json(ARTIFACTS / "chunks" / "CHUNKS-STATE.json")
    insights_state = _load_json(ARTIFACTS / "insights" / "INSIGHTS-STATE.json")
    dna_config = _load_yaml(
        ROOT / "knowledge" / "external" / "dna" / "persons" / slug / "DNA-CONFIG.yaml"
    )

    # --- METRICS ---
    chunks_list = chunks_state.get("chunks", [])
    chunks_count = len(chunks_list) if isinstance(chunks_list, list) else 0

    total_insights = insights_state.get("total_insights", 0)
    person_insights = _count_person_insights(insights_state, person_name)

    composition = dna_config.get("composition", {})
    dna_total = composition.get("total", 0)
    fil = composition.get("FILOSOFIAS", 0)
    mm = composition.get("MODELOS_MENTAIS", 0)
    heu = composition.get("HEURISTICAS", 0)
    fw = composition.get("FRAMEWORKS", 0)
    met = composition.get("METODOLOGIAS", 0)

    phases_completed = len(metadata.get("phases_completed", {}))
    duration = metrics_data.get("total", {}).get("duration_seconds", 0)
    mode = metadata.get("mode", "unknown")
    source_code = metadata.get("source_code", "")
    pipeline_status = metadata.get("pipeline_status", "unknown")

    ctx["metrics"] = {
        "chunks_count": chunks_count,
        "total_insights": total_insights,
        "person_insights": person_insights,
        "dna_total": dna_total,
        "phases_completed": phases_completed,
        "duration_seconds": duration,
        "mode": mode,
        "source_code": source_code,
        "pipeline_status": pipeline_status,
    }

    # MCE identity layers (L9, L10) -- standalone YAML files
    obsessions_count = _count_mce_layer_items(slug, "OBSESSIONS.yaml", "obsessions")
    paradoxes_count = _count_mce_layer_items(slug, "PARADOXES.yaml", "paradoxes")

    ctx["dna"] = {
        "FILOSOFIAS": fil,
        "MODELOS_MENTAIS": mm,
        "HEURISTICAS": heu,
        "FRAMEWORKS": fw,
        "METODOLOGIAS": met,
        "total": dna_total,
        "OBSESSIONS": obsessions_count,
        "PARADOXES": paradoxes_count,
    }

    ctx["insights"] = {
        "total": total_insights,
        "person": person_insights,
        "categories": list(insights_state.get("categories", {}).keys()),
    }

    # --- VALIDATION ---
    ctx["validation"] = {
        "chunks_ok": chunks_count > 0,
        "insights_ok": person_insights > 0,
        "dna_ok": dna_total > 0,
        "metadata_ok": bool(metadata),
        "metrics_ok": bool(metrics_data),
    }

    # --- PROGRESS ---
    total_phases = 5  # typical pipeline phases
    ctx["progress"] = {
        "phases_completed": phases_completed,
        "total_phases": total_phases,
        "percentage": round(phases_completed / total_phases * 100) if total_phases else 0,
    }

    # --- FILES ---
    sources = metadata.get("sources_processed", [])
    ctx["files"] = {
        "sources_processed": sources if isinstance(sources, list) else [],
        "dna_config_exists": (
            ROOT / "knowledge" / "external" / "dna" / "persons" / slug / "DNA-CONFIG.yaml"
        ).exists(),
        # MCE-13.6: case-insensitive check for agent file
        "agent_exists": find_agent_file(ROOT / "agents" / "external" / slug, "agent.md") is not None,
    }

    # --- TEMPLATE-SPECIFIC DELTAS ---
    ctx["deltas"] = _collect_template_deltas(template_id, slug, metadata, insights_state)

    return ctx


def _count_person_insights(insights_state: dict, person_name: str) -> int:
    """Count insights for a specific person in INSIGHTS-STATE."""
    persons = insights_state.get("persons", {})
    if not isinstance(persons, dict):
        return 0

    pdata = persons.get(person_name, {})
    if isinstance(pdata, dict):
        pinsights = pdata.get("insights", [])
        return len(pinsights) if isinstance(pinsights, list) else 0
    elif isinstance(pdata, list):
        return len(pdata)
    return 0


def _count_mce_layer_items(slug: str, filename: str, fallback_key: str) -> int:
    """Count items in a standalone MCE layer YAML file (L9/L10).

    Checks the standalone file first, then falls back to INSIGHTS-STATE.json
    for backward compatibility with pre-L9/L10 pipeline runs.

    Args:
        slug: Person slug.
        filename: YAML filename (e.g. ``"OBSESSIONS.yaml"``).
        fallback_key: Key to look for in INSIGHTS-STATE.json (e.g. ``"obsessions"``).

    Returns:
        Count of items found, or 0 if neither source exists.
    """
    # Priority 1: standalone YAML file (new L9/L10 location)
    standalone_path = ROOT / "knowledge" / "external" / "dna" / "persons" / slug / filename
    standalone = _load_yaml(standalone_path)
    if standalone:
        items = standalone.get(fallback_key, [])
        if isinstance(items, list | dict):
            return len(items)
        return 1 if items else 0

    # Priority 2: fallback to INSIGHTS-STATE.json
    insights_state = _load_json(ARTIFACTS / "insights" / "INSIGHTS-STATE.json")
    fallback_data = insights_state.get(fallback_key, [])
    if isinstance(fallback_data, list | dict):
        return len(fallback_data)
    return 0


def _collect_template_deltas(
    template_id: int,
    slug: str,
    metadata: dict,
    insights_state: dict,
) -> dict[str, Any]:
    """Collect template-specific delta information."""
    deltas: dict[str, Any] = {}

    if template_id == 1:
        # EXTRACTION SUMMARY -- needs before/after counts
        deltas["type"] = "extraction"
        deltas["sources_count"] = len(metadata.get("sources_processed", []))

    elif template_id == 2:
        # AGENT UPDATE -- needs agent file info
        agent_dir = ROOT / "agents" / "external" / slug
        deltas["type"] = "agent_update"
        deltas["agent_exists"] = agent_dir.exists()
        deltas["agent_files"] = []
        if agent_dir.exists():
            try:
                deltas["agent_files"] = [f.name for f in agent_dir.iterdir() if f.is_file()]
            except Exception:
                pass

    elif template_id == 3:
        # CARGO ENRICHMENT -- needs cargo agent info
        deltas["type"] = "cargo_enrichment"
        cargo_dir = ROOT / "agents" / "cargo"
        deltas["cargo_count"] = 0
        if cargo_dir.exists():
            try:
                deltas["cargo_count"] = sum(1 for d in cargo_dir.iterdir() if d.is_dir())
            except Exception:
                pass

    elif template_id == 4:
        # DNA ANALYSIS -- needs DNA layer breakdown
        deltas["type"] = "dna_analysis"

    elif template_id == 5:
        # DOSSIER UPDATE -- needs dossier file info
        deltas["type"] = "dossier_update"
        dossier_dir = ROOT / "knowledge" / "external" / "dossiers" / "persons"
        deltas["dossier_exists"] = False
        if dossier_dir.exists():
            try:
                for f in dossier_dir.iterdir():
                    if slug.lower() in f.name.lower():
                        deltas["dossier_exists"] = True
                        deltas["dossier_file"] = f.name
                        break
            except Exception:
                pass

    elif template_id == 6:
        # INDEX REBUILD -- needs RAG index info
        deltas["type"] = "index_rebuild"

    elif template_id == 7:
        # SESSION CONSOLIDATION -- handled by collect_session_data
        deltas["type"] = "session"

    return deltas


# ═══════════════════════════════════════════════════════════════════════════════
# collect_session_data
# ═══════════════════════════════════════════════════════════════════════════════


def collect_session_data(session_hours: float = 8.0) -> dict[str, Any]:
    """Collect aggregated session data across all slugs processed.

    Reads JSONL logs from the last ``session_hours`` hours and aggregates
    by slug for Template 7 (SESSION CONSOLIDATION).

    Args:
        session_hours: How many hours back to scan logs.

    Returns:
        Dict with keys: ``slugs_processed``, ``total_steps``, ``agents_count``,
        ``dossiers_count``, ``session_hours``, ``timestamp``, ``per_slug``.
        Never raises.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    result: dict[str, Any] = {
        "slugs_processed": [],
        "total_steps": 0,
        "agents_count": 0,
        "dossiers_count": 0,
        "session_hours": session_hours,
        "timestamp": now,
        "per_slug": {},
    }

    # Read orchestrate JSONL for commands executed
    orchestrate_entries = _read_jsonl_recent(LOGS / "mce-orchestrate.jsonl", session_hours)

    # Read step logger JSONL for pipeline steps
    step_entries = _read_jsonl_recent(LOGS / "mce-step-logger.jsonl", session_hours)

    # Aggregate slugs from orchestrate log
    slugs_seen: set[str] = set()
    per_slug: dict[str, dict[str, Any]] = {}

    for entry in orchestrate_entries:
        slug = entry.get("slug", "")
        if slug and slug != "unknown":
            slugs_seen.add(slug)
            if slug not in per_slug:
                per_slug[slug] = {
                    "commands": [],
                    "steps": 0,
                    "success": True,
                }
            per_slug[slug]["commands"].append(entry.get("command", ""))

    # Aggregate steps from step logger
    for entry in step_entries:
        slug = entry.get("slug", "")
        if slug and slug != "unknown":
            slugs_seen.add(slug)
            if slug not in per_slug:
                per_slug[slug] = {"commands": [], "steps": 0, "success": True}
            per_slug[slug]["steps"] += 1

    result["slugs_processed"] = sorted(slugs_seen)
    result["total_steps"] = sum(ps.get("steps", 0) for ps in per_slug.values())
    result["per_slug"] = per_slug

    # Count agents and dossiers created/updated in session
    agents_dir = ROOT / "agents" / "external"
    dossiers_dir = ROOT / "knowledge" / "external" / "dossiers" / "persons"

    if agents_dir.exists():
        try:
            result["agents_count"] = sum(1 for d in agents_dir.iterdir() if d.is_dir())
        except Exception:
            pass

    if dossiers_dir.exists():
        try:
            result["dossiers_count"] = sum(1 for f in dossiers_dir.iterdir() if f.is_file())
        except Exception:
            pass

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# collect_final_log_data
# ═══════════════════════════════════════════════════════════════════════════════


def collect_final_log_data(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    index_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect all data needed for the final Chronicler log.

    Replaces the inline data loading that was scattered across
    ``log_generator.py`` and ``orchestrate.py``'s ``cmd_finalize()``.

    Args:
        slug: Person slug (e.g. ``"process-architect"``).
        enrichment_result: Output from memory enrichment step.
        cascade_result: Output from cascading step.
        sync_result: Output from workspace sync step.
        index_result: Output from index rebuild step.

    Returns:
        Dict with all fields needed by ``generate_mce_log()``.
        Keys include: ``person_name``, ``tag``, ``metadata``, ``metrics``,
        ``chunks_count``, ``person_insights``, ``total_insights``,
        ``dna``, ``enrichment``, ``cascade``, ``sync``, ``index``.
        Never raises.
    """
    enrichment_result = enrichment_result or {}
    cascade_result = cascade_result or {}
    sync_result = sync_result or {}
    index_result = index_result or {}

    person_name = resolve_person_name(slug)
    tag = _make_tag(slug)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Load data sources (same as log_generator's _load_* functions)
    metadata = _load_yaml(MISSION_CONTROL / "mce" / slug / "metadata.yaml")
    metrics_data = _load_yaml(MISSION_CONTROL / "mce" / slug / "metrics.yaml")
    dna_config = _load_yaml(
        ROOT / "knowledge" / "external" / "dna" / "persons" / slug / "DNA-CONFIG.yaml"
    )

    # Chunks count
    # G11 (2026-05-13): read slug-isolated layout first (canonical: cmd_process_batch
    # writes ``ARTIFACTS / "chunks" / {slug} / BATCH-*-chunks.json``).  Fall back
    # to legacy consolidated CHUNKS-STATE.json only when nothing slug-local is
    # available.  Previously this read ONLY the legacy path, which was rarely
    # written, so chunks_count stayed at 0 even with hundreds of real chunks.
    chunks_count = 0
    slug_chunks_dir = ARTIFACTS / "chunks" / slug
    if slug_chunks_dir.is_dir():
        for cjson in slug_chunks_dir.glob("BATCH-*-chunks.json"):
            cd = _load_json(cjson)
            cl = cd.get("chunks", [])
            if isinstance(cl, list):
                chunks_count += len(cl)

    if chunks_count == 0:
        chunks_path_slug = ARTIFACTS / "chunks" / slug / "CHUNKS-STATE.json"
        chunks_path_legacy = ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
        chunks_path = chunks_path_slug if chunks_path_slug.exists() else chunks_path_legacy
        chunks_data = _load_json(chunks_path)
        chunks_list = chunks_data.get("chunks", [])
        if isinstance(chunks_list, list):
            chunks_count = len(chunks_list)

    # Insights count
    # G11 (2026-05-13): same slug-isolated -> legacy fallback pattern that
    # cmd_report uses (orchestrate.py:1570-1572).  Keeps log_generator in sync
    # with the canonical state location.
    insights_slug = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    insights_legacy = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    insights_state_path = insights_slug if insights_slug.exists() else insights_legacy
    insights_state = _load_json(insights_state_path)
    total_insights = insights_state.get("total_insights", 0)
    person_insights = _count_person_insights(insights_state, person_name)

    # DNA composition
    composition = dna_config.get("composition", {})
    fil = composition.get("FILOSOFIAS", 0)
    mm = composition.get("MODELOS_MENTAIS", 0)
    heu = composition.get("HEURISTICAS", 0)
    fw = composition.get("FRAMEWORKS", 0)
    met = composition.get("METODOLOGIAS", 0)
    dna_total = composition.get("total", fil + mm + heu + fw + met)

    # MCE identity layers (L9, L10)
    obsessions_count = _count_mce_layer_items(slug, "OBSESSIONS.yaml", "obsessions")
    paradoxes_count = _count_mce_layer_items(slug, "PARADOXES.yaml", "paradoxes")

    # G17 (2026-05-13): resolve canonical primary_bucket for this slug.
    # Priority order:
    #   1. metadata.yaml "bucket" field (set by orchestrate.cmd_ingest)
    #   2. existing agents/{bucket}/{slug}/ directory
    #   3. existing knowledge/{bucket}/dna/persons/{slug}/ directory (DNA evidence)
    #   4. default "external"
    bucket = _detect_primary_bucket(slug, metadata)

    return {
        # Identity
        "slug": slug,
        "person_name": person_name,
        "tag": tag,
        "timestamp": now,
        "bucket": bucket,
        # State files
        "metadata": metadata,
        "metrics": metrics_data,
        # Counts
        "chunks_count": chunks_count,
        "total_insights": total_insights,
        "person_insights": person_insights,
        # DNA breakdown
        "dna": {
            "FILOSOFIAS": fil,
            "MODELOS_MENTAIS": mm,
            "HEURISTICAS": heu,
            "FRAMEWORKS": fw,
            "METODOLOGIAS": met,
            "total": dna_total,
            "OBSESSIONS": obsessions_count,
            "PARADOXES": paradoxes_count,
        },
        # Pipeline sub-step results (passed through)
        "enrichment": enrichment_result,
        "cascade": cascade_result,
        "sync": sync_result,
        "index": index_result,
    }


def _detect_primary_bucket(slug: str, metadata: dict[str, Any] | None = None) -> str:
    """Resolve canonical primary_bucket for a slug.

    G17 (2026-05-13): The MCE validation checklist needs to know which bucket
    a slug belongs to in order to evaluate RAG indexes correctly.  A slug
    routed to ``external`` should NOT be penalised for having zero chunks in
    the ``business`` RAG index — that's an isolation requirement, not a gap.

    Priority order:
        1. ``metadata['bucket']`` (canonical -- set by orchestrate.cmd_ingest).
        2. Existing ``agents/{bucket}/{slug}/`` directory (cargo agents live
           one level deeper so this catches person-agents only).
        3. Existing ``knowledge/{bucket}/dna/persons/{slug}/`` directory (DNA
           extraction evidence -- the bucket the slug was classified into).
        4. Default ``"external"`` (matches orchestrate._detect_bucket_for_slug).

    Args:
        slug: Person/source slug.
        metadata: Optional pre-loaded ``metadata.yaml`` dict.

    Returns:
        One of ``"external" | "business" | "personal"``.
    """
    # 1. metadata.yaml
    if isinstance(metadata, dict):
        b = metadata.get("bucket")
        if b in ("external", "business", "personal"):
            return b

    # 2. agents/{bucket}/{slug}/ -- top-level person agents only
    for b in ("personal", "business", "external"):
        candidate = ROOT / "agents" / b / slug
        if candidate.is_dir():
            return b

    # 3. knowledge/{bucket}/dna/persons/{slug}/ -- DNA evidence
    for b in ("personal", "business", "external"):
        candidate = ROOT / "knowledge" / b / "dna" / "persons" / slug
        if candidate.is_dir():
            return b

    return "external"


def _make_tag(slug: str) -> str:
    """Generate a short tag from slug (e.g. 'process-architect' -> 'PA')."""
    parts = slug.split("-")
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return slug[:2].upper() if slug else "XX"
