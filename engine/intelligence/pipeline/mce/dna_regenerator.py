"""
dna_regenerator.py -- L1-L5 YAML regeneration from INSIGHTS-STATE.json
=======================================================================

Reads per-slug INSIGHTS-STATE.json and regenerates the five DNA layer YAMLs
(L1-L5) under knowledge/external/dna/persons/{slug}/ from tagged insights.

Tag-to-file mapping:
    [FILOSOFIA]     -> filosofias.yaml      (L1)
    [MODELO-MENTAL] -> modelos-mentais.yaml (L2)
    [HEURISTICA]    -> heuristicas.yaml     (L3)
    [FRAMEWORK]     -> frameworks.yaml      (L4)
    [METODOLOGIA]   -> metodologias.yaml    (L5)

Schema per entry (APPEND-ONLY, idempotent):
    id: <str>
    name: <str>
    description: <str>
    source_insight_ids: [<str>, ...]
    chunk_refs: [<str>, ...]
    confidence: <float>
    last_updated: <ISO date str>

Dedup strategy: lowercase + strip first 50 chars of 'name' field.
Existing entries that match get their source_insight_ids and chunk_refs
extended with new values (union, no duplicates). No deletions.

Constraints:
    - stdlib + PyYAML only (no LLM calls).
    - Never deletes existing entries.
    - Idempotent: running twice on same data produces identical output.
    - Non-fatal: exceptions are logged and returned in result dict.

Called by:
    orchestrate.cmd_finalize() after cmd_consolidate().

Version: 1.0.0
Date: 2026-05-27
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.paths import ARTIFACTS

logger = logging.getLogger("mce.dna_regenerator")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tag value -> (yaml filename, layer label, id prefix)
_TAG_MAP: dict[str, tuple[str, str, str]] = {
    "[FILOSOFIA]": ("filosofias.yaml", "L1_FILOSOFIAS", "fil"),
    "[MODELO-MENTAL]": ("modelos-mentais.yaml", "L2_MODELOS_MENTAIS", "mm"),
    "[HEURISTICA]": ("heuristicas.yaml", "L3_HEURISTICAS", "heu"),
    "[FRAMEWORK]": ("frameworks.yaml", "L4_FRAMEWORKS", "fra"),
    "[METODOLOGIA]": ("metodologias.yaml", "L5_METODOLOGIAS", "met"),
}

_TODAY = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dedup_key(name: str) -> str:
    """Normalise a name string into a dedup key."""
    return name.lower().strip()[:50]


def _load_insights_for_slug(slug: str) -> list[dict]:
    """Load insights list from per-slug INSIGHTS-STATE.json."""
    per_slug_path: Path = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    if not per_slug_path.exists():
        logger.debug("dna_regenerator: no INSIGHTS-STATE.json for slug=%s", slug)
        return []
    try:
        data = json.loads(per_slug_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("dna_regenerator: failed to parse insights for %s: %s", slug, exc)
        return []

    collected: list[dict] = []

    # Primary shape: {"persons": {"<Name>": {"insights": [...]}}}
    persons = data.get("persons", {})
    if isinstance(persons, dict):
        for pdata in persons.values():
            if isinstance(pdata, dict):
                for ins in pdata.get("insights", []):
                    if isinstance(ins, dict):
                        collected.append(ins)

    # Secondary shape: flat "insights" list
    flat = data.get("insights", [])
    if isinstance(flat, list):
        collected.extend(i for i in flat if isinstance(i, dict))

    return collected


def _group_by_tag(insights: list[dict]) -> dict[str, list[dict]]:
    """Group insights by their 'tag' field, keeping only L1-L5 tags."""
    groups: dict[str, list[dict]] = {tag: [] for tag in _TAG_MAP}
    for ins in insights:
        tag = (ins.get("tag") or "").strip().upper()
        # Normalise to match keys (e.g. "[FILOSOFIA]")
        normalised = f"[{tag.strip('[]')}]"
        if normalised in groups:
            groups[normalised].append(ins)
    return groups


def _load_yaml_safe(path: Path) -> dict:
    """Load a YAML file or return a minimal scaffold if missing/invalid."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("dna_regenerator: failed to load YAML %s: %s", path, exc)
        return {}


def _build_entry_from_insight(ins: dict, existing_ids: set[str], id_prefix: str, seq: int) -> dict:
    """Build a new YAML entry dict from a raw insight dict."""
    insight_id = ins.get("id", "")
    name = ins.get("insight", "") or ins.get("name", "") or ins.get("title", insight_id)
    description = ins.get("insight", "") or ins.get("description", "") or name
    chunks = list(ins.get("chunks", []) or [])
    confidence = ins.get("confidence", 0.8)
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except ValueError:
            confidence = 0.8

    new_id = f"{id_prefix}_{seq:03d}"
    # Avoid clashing with existing IDs
    while new_id in existing_ids:
        seq += 1
        new_id = f"{id_prefix}_{seq:03d}"

    return {
        "id": new_id,
        "name": name[:200],
        "description": description[:500],
        "source_insight_ids": [insight_id] if insight_id else [],
        "chunk_refs": chunks,
        "confidence": round(float(confidence), 2),
        "last_updated": _TODAY,
    }


def _merge_into_yaml(
    yaml_path: Path,
    tag_insights: list[dict],
    layer_label: str,
    id_prefix: str,
    slug: str,
) -> dict[str, Any]:
    """Merge new insights into an existing (or new) YAML file.

    APPEND-ONLY:
    - Existing entries that match by dedup_key get source_insight_ids and
      chunk_refs extended (union). No other fields overwritten.
    - New entries are appended at the end.

    Returns a result dict with keys: added, updated, total.
    """
    existing = _load_yaml_safe(yaml_path)
    entries: list[dict] = existing.get("entries", []) or []

    # Build index: dedup_key -> list index
    key_to_idx: dict[str, int] = {}
    existing_ids: set[str] = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        key_to_idx[_dedup_key(entry.get("name", ""))] = idx
        existing_ids.add(entry.get("id", ""))

    added = 0
    updated = 0

    # Determine next seq for new IDs
    seq = len(entries) + 1

    for ins in tag_insights:
        name = ins.get("insight", "") or ins.get("name", "") or ins.get("title", "")
        dk = _dedup_key(name)

        insight_id = ins.get("id", "")
        chunks = list(ins.get("chunks", []) or [])

        if dk in key_to_idx:
            # Update existing entry: extend source_insight_ids + chunk_refs
            idx = key_to_idx[dk]
            entry = entries[idx]
            existing_src_ids: list = entry.get("source_insight_ids", []) or []
            existing_chunks: list = entry.get("chunk_refs", []) or []

            changed = False
            if insight_id and insight_id not in existing_src_ids:
                existing_src_ids.append(insight_id)
                changed = True
            for ch in chunks:
                if ch not in existing_chunks:
                    existing_chunks.append(ch)
                    changed = True

            if changed:
                entry["source_insight_ids"] = existing_src_ids
                entry["chunk_refs"] = existing_chunks
                entry["last_updated"] = _TODAY
                entries[idx] = entry
                updated += 1
        else:
            # New entry
            new_entry = _build_entry_from_insight(ins, existing_ids, id_prefix, seq)
            seq += 1
            entries.append(new_entry)
            key_to_idx[dk] = len(entries) - 1
            existing_ids.add(new_entry["id"])
            added += 1

    # Write back
    now_iso = _TODAY
    output: dict = {
        "version": existing.get("version", "3.0"),
        "person": slug,
        "layer": layer_label,
        "updated": now_iso,
        "pipeline_run": f"MCE-DNA-REGEN-{datetime.now(UTC).strftime('%Y-%m-%d')}",
    }
    # Preserve prior_run if present
    if "pipeline_run" in existing:
        output["prior_run"] = existing["pipeline_run"]
    output["source_count"] = existing.get("source_count", 0)
    output["total_entries"] = len(entries)
    output["entries"] = entries

    try:
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.write_text(
            yaml.dump(output, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("dna_regenerator: failed to write %s: %s", yaml_path, exc)
        return {"added": added, "updated": updated, "total": len(entries), "error": str(exc)}

    return {"added": added, "updated": updated, "total": len(entries)}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def regenerate_l1_l5_yamls(slug: str, bucket: str = "external") -> dict[str, Any]:
    """Regenerate L1-L5 YAML files for a person from their INSIGHTS-STATE.json.

    Reads all tagged insights from .data/artifacts/insights/{slug}/INSIGHTS-STATE.json,
    groups by tag ([FILOSOFIA], [MODELO-MENTAL], etc.), and merges into the
    corresponding YAML files under knowledge/{bucket}/dna/persons/{slug}/.

    APPEND-ONLY: never deletes existing entries. Idempotent.

    Args:
        slug: Person slug (e.g. "alex-hormozi").
        bucket: Knowledge bucket, default "external".

    Returns:
        Dict with per-layer results plus totals. Keys:
            success: bool
            slug: str
            layers: dict[str, {added, updated, total}]
            total_added: int
            total_updated: int
            error: str (only on fatal error)
    """
    result: dict[str, Any] = {
        "success": True,
        "slug": slug,
        "bucket": bucket,
        "layers": {},
        "total_added": 0,
        "total_updated": 0,
    }

    # Resolve person DNA dir via the single SOT (STORY-MCE-BUCKET-AWARE-WRITES, Art. XIII).
    # This used to be structurally hardcoded to the external bucket in both
    # branches, leaking business/personal L1-L5 DNA. Now bucket-aware.
    from engine.intelligence.pipeline.mce.person_paths import PersonArtifactPaths

    person_dir = PersonArtifactPaths(slug, bucket).dna

    # Load insights
    all_insights = _load_insights_for_slug(slug)
    if not all_insights:
        result["skipped"] = f"No insights found for slug={slug}"
        logger.info("dna_regenerator: no insights for %s, skipping L1-L5 regen", slug)
        return result

    logger.info(
        "dna_regenerator: regenerating L1-L5 for slug=%s from %d insights",
        slug,
        len(all_insights),
    )

    # Group by tag
    grouped = _group_by_tag(all_insights)

    for tag, (yaml_filename, layer_label, id_prefix) in _TAG_MAP.items():
        tag_insights = grouped.get(tag, [])
        if not tag_insights:
            result["layers"][layer_label] = {
                "added": 0,
                "updated": 0,
                "total": 0,
                "skipped": "no insights for tag",
            }
            continue

        yaml_path = person_dir / yaml_filename
        try:
            layer_result = _merge_into_yaml(yaml_path, tag_insights, layer_label, id_prefix, slug)
            result["layers"][layer_label] = layer_result
            result["total_added"] += layer_result.get("added", 0)
            result["total_updated"] += layer_result.get("updated", 0)
            logger.info(
                "dna_regenerator: %s/%s: added=%d updated=%d total=%d",
                slug,
                yaml_filename,
                layer_result.get("added", 0),
                layer_result.get("updated", 0),
                layer_result.get("total", 0),
            )
        except Exception as exc:
            logger.warning(
                "dna_regenerator: layer %s for slug=%s failed: %s",
                layer_label,
                slug,
                exc,
            )
            result["layers"][layer_label] = {"error": str(exc)}

    return result
