"""navigation.py — Reverse lookup helpers for NAVIGATION-MAP (Story MCE-3.6).

Wraps `.data/navigation-map.json` (built by `scripts/build-navigation-map.py`)
with three query helpers used by the rest of the engine.

Resolution order for chunk lookups:
    1. `[chunk_X-N]` inline cited in a dossier section
    2. (future) sources/ index — V2

Usage:
    from engine.intelligence.navigation import (
        resolve_chunk,
        list_chunks_in_section,
        find_orphan_chunks,
    )

    appearances = resolve_chunk("chunk_JD-0001-23")
    # [{"file": "dossier-jane-doe.md", "section": "Filosofia",
    #   "type": "dossier_person", "bucket": "external"}]
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
NAV_MAP_PATH = ROOT / ".data" / "navigation-map.json"


def _normalize_chunk_key(chunk_id: str) -> str:
    """Accept `chunk_X-N` or `X-N` — return the canonical `chunk_X-N` form."""
    if not chunk_id:
        return ""
    s = chunk_id.strip()
    return s if s.startswith("chunk_") else f"chunk_{s}"


@lru_cache(maxsize=1)
def _load_nav_map(path_str: str | None = None) -> dict:
    """Load the navigation-map JSON. Cached: clear via `_load_nav_map.cache_clear()`."""
    p = Path(path_str) if path_str else NAV_MAP_PATH
    if not p.is_file():
        return {
            "version": "0.0.0",
            "dossiers": {},
            "chunk_reverse_index": {},
            "statistics": {"total_dossiers_mapped": 0, "total_chunks_indexed": 0},
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load navigation-map %s: %s", p, exc)
        return {
            "version": "0.0.0",
            "dossiers": {},
            "chunk_reverse_index": {},
            "statistics": {"total_dossiers_mapped": 0, "total_chunks_indexed": 0},
        }


def resolve_chunk(chunk_id: str, nav_map_path: Path | None = None) -> list[dict]:
    """Return the list of appearances for a chunk_id.

    Args:
        chunk_id: Either `chunk_RT-0001-23` or `RT-0001-23` (prefix added if missing).
        nav_map_path: Override for testing.

    Returns:
        List of `{file, section, type, bucket}` dicts, empty if not indexed.
    """
    nav = _load_nav_map(str(nav_map_path) if nav_map_path else None)
    key = _normalize_chunk_key(chunk_id)
    entry = nav.get("chunk_reverse_index", {}).get(key)
    if not entry:
        return []
    return list(entry.get("appears_in", []))


def list_chunks_in_section(
    dossier_path: str,
    section: str,
    nav_map_path: Path | None = None,
) -> list[str]:
    """Return chunk_ids cited inside `section` of `dossier_path`.

    Args:
        dossier_path: Filename only (e.g. `dossier-jane-doe.md`) OR repo-relative path.
        section: Section title without the `## ` prefix and without leading numbering.

    Returns:
        Ordered list of raw chunk_ids (without `chunk_` prefix), possibly with duplicates.
    """
    nav = _load_nav_map(str(nav_map_path) if nav_map_path else None)
    dossier_name = Path(dossier_path).name
    for dtype_entries in nav.get("dossiers", {}).values():
        if dossier_name in dtype_entries:
            return list(dtype_entries[dossier_name].get("sections", {}).get(section, []))
    return []


def find_orphan_chunks(
    chunks_state_path: Path,
    nav_map_path: Path | None = None,
) -> list[str]:
    """Return chunk_ids present in a CHUNKS-STATE.json but never cited in any dossier.

    Args:
        chunks_state_path: Path to a slug's `.data/artifacts/mce/<slug>/CHUNKS-STATE.json`.
        nav_map_path: Override for testing.

    Returns:
        Sorted list of orphan chunk_ids (without `chunk_` prefix).
    """
    if not chunks_state_path.is_file():
        return []
    try:
        data = json.loads(chunks_state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Cannot read CHUNKS-STATE %s: %s", chunks_state_path, exc)
        return []
    declared: set[str] = set()
    for chunk in data.get("chunks", []) or []:
        if isinstance(chunk, dict):
            for key in ("id_chunk", "chunk_id", "id"):
                if chunk.get(key):
                    declared.add(str(chunk[key]))
                    break
        elif isinstance(chunk, str):
            declared.add(chunk)

    if not declared:
        return []

    nav = _load_nav_map(str(nav_map_path) if nav_map_path else None)
    cited = {
        key[len("chunk_") :]
        for key in nav.get("chunk_reverse_index", {})
        if key.startswith("chunk_")
    }
    return sorted(declared - cited)


def reload() -> None:
    """Force a fresh read of navigation-map.json on next call."""
    _load_nav_map.cache_clear()
