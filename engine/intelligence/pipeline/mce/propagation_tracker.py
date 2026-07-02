"""Propagation Gaps Tracker — Story MCE-11.4.

Tracks whether each processed source reached all 5 downstream destinations
(chunks → insights → dossier → agent MEMORY → DNA files).  Writes a single
cumulative ``PROPAGATION-GAPS.json`` under ``.data/artifacts/`` so the founder
can answer: "Did Liam Ottley's video reach the Closer agent's MEMORY?"

Gap types:
    GAP-TYPE-1  chunks generated
    GAP-TYPE-2  insights extracted
    GAP-TYPE-3  dossier file written/updated
    GAP-TYPE-4  at least one agent MEMORY.md updated
    GAP-TYPE-5  DNA YAML files present (only checked if sufficient material)

Entry point:
    track_propagation_gaps(slug, bucket="external") -> dict

Art. XII (Pipeline MCE Integrity): fail-open — exceptions write
``{overall: "UNKNOWN"}`` rather than aborting cmd_finalize.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical root — mirrors the pattern used across orchestrate.py
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# Canonical .data paths (same constants as orchestrate.py)
_ARTIFACTS = _PROJECT_ROOT / ".data" / "artifacts"
_GAPS_FILE = _ARTIFACTS / "PROPAGATION-GAPS.json"

# DNA layer file names that must exist for GAP-TYPE-5 to pass
_DNA_LAYER_FILES = [
    "filosofias.yaml",
    "modelos-mentais.yaml",
    "heuristicas.yaml",
    "frameworks.yaml",
    "metodologias.yaml",
    "behavioral-patterns.yaml",
    "values-hierarchy.yaml",
    "voice-dna.yaml",
    "obsessions.yaml",
    "paradoxes.yaml",
    # Alternate English-named variants used in some personas
    "PHILOSOPHIES.yaml",
    "MENTAL-MODELS.yaml",
    "HEURISTICS.yaml",
    "FRAMEWORKS.yaml",
    "METHODOLOGIES.yaml",
    "BEHAVIORAL-PATTERNS.yaml",
    "VALUES-HIERARCHY.yaml",
    "VOICE-DNA.yaml",
    "OBSESSIONS.yaml",
    "PARADOXES.yaml",
]
# Minimum distinct layer files required for GAP-TYPE-5 PASS
_DNA_MIN_FILES = 3

# Minimum chunks to trigger GAP-TYPE-5 check
_DNA_CHUNK_THRESHOLD = 10

# Maximum source entries to keep in the JSON (prune oldest if exceeded)
_MAX_SOURCES = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _atomic_write_json(data: dict[str, Any], target: Path) -> None:
    """Atomic JSON write via tempfile.mkstemp + os.replace (Art. X pattern)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            f.write("\n")
        os.replace(tmp_path_str, target)
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise


def _load_gaps_file() -> dict[str, Any]:
    """Load existing PROPAGATION-GAPS.json or return a fresh skeleton."""
    if _GAPS_FILE.exists():
        try:
            data = json.loads(_GAPS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("propagation_tracker: cannot read existing gaps file: %s", exc)
    return {"last_updated": _now_iso(), "sources": {}}


def _prune_oldest(sources: dict[str, Any], max_entries: int = _MAX_SOURCES) -> dict[str, Any]:
    """Remove oldest entries when sources dict exceeds max_entries (AC-risk mitigation)."""
    if len(sources) <= max_entries:
        return sources
    # Sort by processed_at ascending; drop the tail
    sorted_keys = sorted(
        sources.keys(),
        key=lambda k: sources[k].get("processed_at", ""),
    )
    keys_to_drop = sorted_keys[: len(sources) - max_entries]
    for k in keys_to_drop:
        del sources[k]
    return sources


# ---------------------------------------------------------------------------
# Gap detection: individual checks
# ---------------------------------------------------------------------------


def _check_gap1_chunks(slug: str) -> dict[str, Any]:
    """GAP-TYPE-1: Were chunks generated for this slug?"""
    slug_dir = _ARTIFACTS / "chunks" / slug
    count = 0

    # Priority 1: slug-isolated CHUNKS-STATE.json
    chunks_state = slug_dir / "CHUNKS-STATE.json"
    if chunks_state.exists():
        try:
            data = json.loads(chunks_state.read_text(encoding="utf-8"))
            chunks = data.get("chunks", [])
            count = len(chunks)
        except (json.JSONDecodeError, OSError):
            pass

    # Priority 2: per-batch BATCH-*-chunks.json files in slug dir
    if count == 0 and slug_dir.is_dir():
        for batch_file in slug_dir.glob("BATCH-*-chunks.json"):
            try:
                data = json.loads(batch_file.read_text(encoding="utf-8"))
                count += len(data.get("chunks", []))
            except (json.JSONDecodeError, OSError):
                pass

    # Priority 3: legacy flat files (source-code prefix, e.g., AH-YT001-chunks.json)
    if count == 0:
        try:
            from engine.intelligence.pipeline.batch_auto_creator import derive_source_code

            source_code = derive_source_code(slug)
        except Exception:
            source_code = ""
        if source_code:
            for f in (_ARTIFACTS / "chunks").glob(f"{source_code}*chunks.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    count += len(data.get("chunks", []))
                except (json.JSONDecodeError, OSError):
                    pass

    return {
        "description": "No chunks generated",
        "status": "PASS" if count > 0 else "FAIL",
        "count": count,
    }


def _check_gap2_insights(slug: str) -> dict[str, Any]:
    """GAP-TYPE-2: Were insights extracted for this slug?"""
    # Per-slug INSIGHTS-STATE.json (canonical per MCE-11.14)
    slug_insights = _ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    legacy_insights = _ARTIFACTS / "insights" / "INSIGHTS-STATE.json"

    insights_path = (
        slug_insights
        if slug_insights.exists()
        else (legacy_insights if legacy_insights.exists() else None)
    )

    total_insights = 0
    if insights_path is not None:
        try:
            data = json.loads(insights_path.read_text(encoding="utf-8"))
            # total_insights field (MCE-11.14 schema)
            total_insights = int(data.get("total_insights", 0))
            if total_insights == 0:
                # Fallback: count across persons map
                persons = data.get("persons", {})
                for pdata in persons.values():
                    if isinstance(pdata, dict):
                        total_insights += len(pdata.get("insights", []))
            if total_insights == 0:
                # Fallback: count across categories map
                categories = data.get("categories", {})
                for cdata in categories.values():
                    if isinstance(cdata, dict):
                        total_insights += len(cdata.get("insights", []))
                    elif isinstance(cdata, list):
                        total_insights += len(cdata)
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("propagation_tracker GAP-2: cannot read insights: %s", exc)

    return {
        "description": "No insights extracted",
        "status": "PASS" if total_insights > 0 else "FAIL",
        "count": total_insights,
    }


def _check_gap3_dossier(slug: str, bucket: str) -> dict[str, Any]:
    """GAP-TYPE-3: Does a dossier file exist for this slug?"""
    # Canonical path from dossier_generator.py
    dossier_dir = _PROJECT_ROOT / "knowledge" / bucket / "dossiers" / "persons"
    dossier_path = dossier_dir / f"dossier-{slug}.md"

    updated = dossier_path.exists()
    return {
        "description": "Dossier not updated",
        "status": "PASS" if updated else "FAIL",
        "updated": updated,
        "path": str(dossier_path) if updated else None,
    }


def _check_gap4_agent_memory(slug: str, bucket: str) -> dict[str, Any]:
    """GAP-TYPE-4: Was at least one agent MEMORY.md updated for this slug?

    Checks agent directories for any MEMORY.md / memory.md file.
    Reports which agents have a memory file (presence, not mtime — mtime
    is fragile per the Risk section in the story; presence is a weaker but
    more reliable signal).
    """
    agents_updated: list[str] = []

    # Primary: direct agent dir for this slug
    primary_dir = _PROJECT_ROOT / "agents" / bucket / slug
    for mem_name in ("MEMORY.md", "memory.md"):
        if (primary_dir / mem_name).exists():
            agents_updated.append(f"agents/{bucket}/{slug}/{mem_name}")
            break

    # Secondary: cargo agents that might hold a memory for this slug
    # (e.g., agents/external/cargo/*/memory.md)
    cargo_base = _PROJECT_ROOT / "agents" / bucket / "cargo"
    if cargo_base.is_dir():
        for cargo_dir in cargo_base.iterdir():
            if not cargo_dir.is_dir():
                continue
            for mem_name in ("MEMORY.md", "memory.md"):
                mem_path = cargo_dir / mem_name
                if mem_path.exists():
                    # Only include if the memory file references this slug
                    try:
                        content = mem_path.read_text(encoding="utf-8", errors="ignore")
                        if slug.lower() in content.lower():
                            agents_updated.append(str(mem_path.relative_to(_PROJECT_ROOT)))
                    except OSError:
                        pass
                    break

    return {
        "description": "Agent MEMORY not updated",
        "status": "PASS" if agents_updated else "FAIL",
        "agents_updated": agents_updated,
    }


def _check_gap5_dna(slug: str, bucket: str, chunk_count: int) -> dict[str, Any]:
    """GAP-TYPE-5: Do DNA YAML files exist for a person with sufficient material?

    Only triggered when chunk_count > _DNA_CHUNK_THRESHOLD (10).  If the
    slug hasn't been processed enough, this check always PASses (not enough
    material to expect DNA yet).
    """
    if chunk_count <= _DNA_CHUNK_THRESHOLD:
        return {
            "description": "DNA files missing for person with sufficient material",
            "status": "PASS",
            "reason": f"chunk_count={chunk_count} below threshold={_DNA_CHUNK_THRESHOLD}; DNA not expected yet",
        }

    # Resolve DNA directory for bucket
    if bucket == "personal":
        dna_dir = _PROJECT_ROOT / "knowledge" / "personal" / "dna"
    elif bucket == "business":
        dna_dir = _PROJECT_ROOT / "knowledge" / "business" / "people" / slug
    else:
        dna_dir = _PROJECT_ROOT / "knowledge" / "external" / "dna" / "persons" / slug

    if not dna_dir.exists():
        return {
            "description": "DNA files missing for person with sufficient material",
            "status": "FAIL",
            "reason": f"DNA directory does not exist: {dna_dir}",
        }

    # Count distinct layer files present
    found = [f for f in _DNA_LAYER_FILES if (dna_dir / f).exists()]
    # Deduplicate in case both English and Portuguese variants exist
    found_unique = list({f.lower() for f in found})

    passed = len(found_unique) >= _DNA_MIN_FILES
    return {
        "description": "DNA files missing for person with sufficient material",
        "status": "PASS" if passed else "FAIL",
        "files_found": len(found_unique),
        "files_required": _DNA_MIN_FILES,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def detect_propagation_gaps(
    slug: str, source_id: str = "", bucket: str = "external"
) -> dict[str, Any]:
    """Detect all 5 propagation gap types for a slug.

    Args:
        slug:      Person/source slug (e.g., "liam-ottley").
        source_id: Canonical source ID (e.g., "LO-0003"). Defaults to slug
                   code derivation when empty.
        bucket:    Knowledge bucket ("external", "business", "personal").

    Returns:
        Entry dict matching the PROPAGATION-GAPS.json schema per AC1.
    """
    if not source_id:
        try:
            from engine.intelligence.pipeline.batch_auto_creator import derive_source_code

            source_id = derive_source_code(slug)
        except Exception:
            source_id = slug.upper()[:8]

    gap1 = _check_gap1_chunks(slug)
    gap2 = _check_gap2_insights(slug)
    gap3 = _check_gap3_dossier(slug, bucket)
    gap4 = _check_gap4_agent_memory(slug, bucket)
    gap5 = _check_gap5_dna(slug, bucket, chunk_count=gap1.get("count", 0))

    gaps = {
        "GAP-TYPE-1": gap1,
        "GAP-TYPE-2": gap2,
        "GAP-TYPE-3": gap3,
        "GAP-TYPE-4": gap4,
        "GAP-TYPE-5": gap5,
    }

    gap_count = sum(1 for g in gaps.values() if g.get("status") == "FAIL")
    overall = "COMPLETE" if gap_count == 0 else "INCOMPLETE"

    return {
        "slug": slug,
        "source_id": source_id,
        "bucket": bucket,
        "processed_at": _now_iso(),
        "gaps": gaps,
        "overall": overall,
        "gap_count": gap_count,
    }


def track_propagation_gaps(slug: str, bucket: str = "external") -> dict[str, Any]:
    """Detect gaps and persist result to PROPAGATION-GAPS.json (Art. X: atomic write).

    This is the function called from cmd_finalize.  Fail-open per Art. XII:
    on any exception, returns ``{overall: "UNKNOWN", error: str(exc)}``.

    Args:
        slug:   Person/source slug.
        bucket: Knowledge bucket.

    Returns:
        The entry dict that was written (or an UNKNOWN stub on error).
    """
    try:
        # Derive source_id from metadata for a richer key
        source_id = ""
        try:
            from engine.intelligence.pipeline.mce.metadata_manager import MetadataManager

            mgr = MetadataManager.load(slug)
            if mgr is not None:
                ctx = mgr.to_dict() if hasattr(mgr, "to_dict") else {}
                source_id = ctx.get("source_id", ctx.get("batch_id", "")) or ""
        except Exception:
            pass

        entry = detect_propagation_gaps(slug, source_id=source_id, bucket=bucket)

        # Merge into cumulative file
        existing = _load_gaps_file()
        sources = existing.get("sources", {})
        if not isinstance(sources, dict):
            sources = {}

        # Key strategy: use source_id when it is distinct from the slug (i.e.,
        # a real pipeline-assigned code like "AH-YT005").  When source_id is
        # empty or equal to the derived slug code (both point to the same slug),
        # use slug directly so multiple runs for the same slug update the same
        # entry rather than creating spurious duplicates.
        derived_source_id = entry.get("source_id", "")
        key = (
            derived_source_id
            if (derived_source_id and derived_source_id != slug.upper()[:8])
            else slug
        )
        sources[key] = entry

        _prune_oldest(sources, _MAX_SOURCES)
        existing["sources"] = sources
        existing["last_updated"] = _now_iso()

        _atomic_write_json(existing, _GAPS_FILE)
        logger.info(
            "propagation_tracker: wrote gaps for %s (key=%s, overall=%s, gap_count=%d)",
            slug,
            key,
            entry.get("overall", "?"),
            entry.get("gap_count", -1),
        )
        return entry

    except Exception as exc:
        logger.warning("propagation_tracker: unexpected failure for %s: %s", slug, exc)
        return {
            "slug": slug,
            "source_id": "",
            "bucket": bucket,
            "processed_at": _now_iso(),
            "gaps": {},
            "overall": "UNKNOWN",
            "gap_count": -1,
            "error": str(exc),
        }
