#!/usr/bin/env python3
"""
STALENESS CHECKER - RAG Index Freshness Detection
====================================================
Compares the mtime of each RAG index (BM25 per bucket) against
the newest source file in the corresponding knowledge bucket.

Importable:
    from core.intelligence.rag.staleness_checker import check_staleness

CLI:
    python3 -m core.intelligence.rag.staleness_checker

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from core.paths import (
    DATA,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
    RAG_BUSINESS,
    RAG_INDEX,
)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Map each bucket to its index directory and source directories.
# Source dirs mirror chunker.py INDEX_SOURCES so staleness detection
# covers the same files the chunker would process.
_BUCKET_CONFIG: dict[str, dict[str, Any]] = {
    "external": {
        "index_dir": RAG_INDEX,
        "source_dirs": [
            KNOWLEDGE_EXTERNAL / "dna" / "persons",
            KNOWLEDGE_EXTERNAL / "dossiers" / "persons",
            KNOWLEDGE_EXTERNAL / "dossiers" / "themes",
            KNOWLEDGE_EXTERNAL / "playbooks",
        ],
    },
    "business": {
        "index_dir": RAG_BUSINESS,
        "source_dirs": [
            DATA.parent / "knowledge" / "business" / "dossiers" / "persons",
            DATA.parent / "knowledge" / "business" / "insights",
            DATA.parent / "knowledge" / "business" / "inbox",
            DATA.parent / "knowledge" / "business" / "decisions",
        ],
    },
    "personal": {
        "index_dir": KNOWLEDGE_PERSONAL / "index",
        "source_dirs": [
            KNOWLEDGE_PERSONAL / "cognitive",
            KNOWLEDGE_PERSONAL / "inbox",
        ],
    },
}

# File extensions that are considered indexable source content.
_SOURCE_EXTENSIONS = {".md", ".yaml", ".yml", ".txt", ".json"}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _newest_file_in_dirs(dirs: list[Path]) -> tuple[float, str]:
    """Walk *dirs* recursively, return (mtime, path_str) of the newest file.

    Only considers files with extensions in ``_SOURCE_EXTENSIONS``.
    Returns ``(0.0, "")`` when no qualifying file is found.
    """
    newest_mtime = 0.0
    newest_path = ""

    for d in dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in _SOURCE_EXTENSIONS:
                continue
            mt = f.stat().st_mtime
            if mt > newest_mtime:
                newest_mtime = mt
                newest_path = str(f)

    return newest_mtime, newest_path


def _index_mtime(index_dir: Path) -> float:
    """Return the oldest mtime among the core index files.

    The index is only as fresh as its oldest constituent file
    (``bm25.json``, ``chunks.json``).  If any core file is missing
    the index is considered non-existent (returns ``0.0``).
    """
    core_files = ["bm25.json", "chunks.json"]
    mtimes: list[float] = []

    for name in core_files:
        p = index_dir / name
        if not p.exists():
            return 0.0
        mtimes.append(p.stat().st_mtime)

    # The oldest file determines effective freshness.
    return min(mtimes) if mtimes else 0.0


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


def check_staleness(bucket: str = "all") -> dict[str, Any]:
    """Check whether RAG indexes are stale relative to source files.

    Args:
        bucket: ``"external"``, ``"business"``, ``"personal"``, or
            ``"all"`` (default) to check every bucket.

    Returns:
        Dict with per-bucket results and a top-level ``is_stale`` flag::

            {
                "is_stale": True,
                "checked_at": "2026-03-16T12:00:00",
                "buckets": {
                    "external": {
                        "is_stale": True,
                        "index_age_hours": 216.5,
                        "newest_source": "/abs/path/to/file.yaml",
                        "newest_source_age_hours": 2.1,
                        "index_exists": True,
                    },
                    ...
                },
            }

        When *bucket* is a single name, only that entry appears in
        ``buckets`` but the top-level ``is_stale`` still reflects it.
    """
    now = time.time()
    buckets_to_check = (
        list(_BUCKET_CONFIG.keys()) if bucket == "all" else [bucket]
    )

    results: dict[str, Any] = {
        "is_stale": False,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "buckets": {},
    }

    for b in buckets_to_check:
        cfg = _BUCKET_CONFIG.get(b)
        if cfg is None:
            results["buckets"][b] = {"error": f"Unknown bucket: {b}"}
            continue

        idx_mt = _index_mtime(cfg["index_dir"])
        src_mt, src_path = _newest_file_in_dirs(cfg["source_dirs"])

        index_exists = idx_mt > 0.0
        idx_age_hours = (now - idx_mt) / 3600.0 if index_exists else -1.0
        src_age_hours = (now - src_mt) / 3600.0 if src_mt > 0.0 else -1.0

        # Stale when: index missing, or newest source is newer than index.
        bucket_stale = (not index_exists) or (src_mt > idx_mt)

        entry = {
            "is_stale": bucket_stale,
            "index_age_hours": round(idx_age_hours, 2),
            "newest_source": src_path,
            "newest_source_age_hours": round(src_age_hours, 2),
            "index_exists": index_exists,
        }
        results["buckets"][b] = entry

        if bucket_stale:
            results["is_stale"] = True

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Human-readable staleness report, suitable for terminal output."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check RAG index staleness against knowledge source files"
    )
    parser.add_argument(
        "--bucket",
        default="all",
        choices=["external", "business", "personal", "all"],
        help="Which bucket to check (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output machine-readable JSON instead of human report",
    )
    args = parser.parse_args()

    result = check_staleness(bucket=args.bucket)

    if args.json_output:
        import json

        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # -- Human-readable report --
    print(f"\n{'=' * 60}")
    print("RAG STALENESS REPORT")
    print(f"{'=' * 60}")
    print(f"  Checked at: {result['checked_at']}")
    overall = "STALE" if result["is_stale"] else "FRESH"
    print(f"  Overall:    {overall}")
    print(f"{'─' * 60}")

    for bname, info in result["buckets"].items():
        if "error" in info:
            print(f"\n  [{bname}] ERROR: {info['error']}")
            continue

        status = "STALE" if info["is_stale"] else "FRESH"
        print(f"\n  [{bname}] {status}")

        if info["index_exists"]:
            print(f"    Index age:          {info['index_age_hours']:.1f} hours")
        else:
            print("    Index age:          NOT BUILT")

        if info["newest_source"]:
            print(f"    Newest source age:  {info['newest_source_age_hours']:.1f} hours")
            print(f"    Newest source:      {info['newest_source']}")
        else:
            print("    Newest source:      (no source files found)")

    print(f"\n{'=' * 60}\n")

    # Exit code 1 when stale -- enables CI integration.
    if result["is_stale"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
