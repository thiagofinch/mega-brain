#!/usr/bin/env python3
"""
RAG HEALTH CHECK - Aggregated Health Metrics for All RAG Buckets
====================================================================
Operator dashboard for the data layer. Aggregates staleness status,
chunk counts, and knowledge graph metrics across all 3 RAG buckets
(external, business, personal) plus the knowledge graph.

Skill activation:  /rag-health
CLI:               python3 -m core.intelligence.rag.health_check
Exit code:         0 = all healthy, 1 = at least one index stale

Imports:
    from core.intelligence.rag.health_check import run_health_check

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core.paths import (
    DATA,
    KNOWLEDGE_GRAPH,
    KNOWLEDGE_PERSONAL,
    RAG_BUSINESS,
    RAG_INDEX,
)

from core.intelligence.rag.staleness_checker import check_staleness

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Map bucket names to their index directories for chunk counting.
# Must stay aligned with staleness_checker._BUCKET_CONFIG so both modules
# inspect the same directories.
_BUCKET_INDEX_DIRS: dict[str, Path] = {
    "external": RAG_INDEX,
    "business": RAG_BUSINESS,
    "personal": KNOWLEDGE_PERSONAL / "index",
}

# Knowledge graph path
_GRAPH_FILE = KNOWLEDGE_GRAPH / "graph.json"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _count_chunks(index_dir: Path) -> int:
    """Count chunks in a bucket's chunks.json file.

    Returns 0 if the file does not exist or cannot be parsed.
    """
    chunks_file = index_dir / "chunks.json"
    if not chunks_file.exists():
        return 0

    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # chunks.json may be a list or a dict with a 'chunks'/'documents' key.
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            for key in ("chunks", "documents"):
                if key in data:
                    return len(data[key])
            return 0
        return 0
    except (json.JSONDecodeError, OSError):
        return 0


def _index_size_mb(index_dir: Path) -> float:
    """Total size of all files in an index directory, in megabytes.

    Returns 0.0 if directory does not exist.
    """
    if not index_dir.exists():
        return 0.0
    total = sum(
        f.stat().st_size for f in index_dir.iterdir() if f.is_file()
    )
    return round(total / (1024 * 1024), 1)


def _load_graph_stats() -> dict[str, Any]:
    """Load knowledge graph stats from graph.json.

    Returns a dict with entity_count, edge_count, and last_build_time.
    Handles missing or corrupt files gracefully.
    """
    result: dict[str, Any] = {
        "exists": False,
        "entity_count": 0,
        "edge_count": 0,
        "last_build_time": "",
        "file_size_mb": 0.0,
    }

    if not _GRAPH_FILE.exists():
        return result

    result["exists"] = True
    result["file_size_mb"] = round(
        _GRAPH_FILE.stat().st_size / (1024 * 1024), 2
    )

    # Last build time from file mtime
    mtime = _GRAPH_FILE.stat().st_mtime
    result["last_build_time"] = time.strftime(
        "%Y-%m-%d %H:%M", time.localtime(mtime)
    )

    try:
        with open(_GRAPH_FILE, "r", encoding="utf-8") as f:
            graph = json.load(f)

        # Extract counts from stats block if available, otherwise count directly
        stats = graph.get("stats", {})
        if stats:
            result["entity_count"] = stats.get("total_entities", 0)
            result["edge_count"] = stats.get("total_edges", 0)
        else:
            result["entity_count"] = len(graph.get("entities", []))
            result["edge_count"] = len(graph.get("edges", []))

    except (json.JSONDecodeError, OSError):
        pass

    return result


def _format_age(hours: float) -> str:
    """Format age in hours into a human-readable string."""
    if hours < 0:
        return "N/A"
    if hours < 1:
        return f"{hours * 60:.0f}m"
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


def run_health_check() -> dict[str, Any]:
    """Run a full health check across all RAG buckets and knowledge graph.

    Returns a structured dict with all metrics, suitable for both
    programmatic consumption and rendering into ASCII tables.
    """
    staleness = check_staleness(bucket="all")

    buckets: dict[str, Any] = {}
    for name, index_dir in _BUCKET_INDEX_DIRS.items():
        stale_info = staleness["buckets"].get(name, {})
        chunk_count = _count_chunks(index_dir)
        size_mb = _index_size_mb(index_dir)

        buckets[name] = {
            "exists": index_dir.exists() and (index_dir / "chunks.json").exists(),
            "chunk_count": chunk_count,
            "size_mb": size_mb,
            "is_stale": stale_info.get("is_stale", True),
            "index_age_hours": stale_info.get("index_age_hours", -1.0),
            "newest_source_age_hours": stale_info.get(
                "newest_source_age_hours", -1.0
            ),
            "newest_source": stale_info.get("newest_source", ""),
        }

    graph = _load_graph_stats()

    return {
        "checked_at": staleness["checked_at"],
        "is_stale": staleness["is_stale"],
        "buckets": buckets,
        "knowledge_graph": graph,
    }


def render_ascii_table(report: dict[str, Any]) -> str:
    """Render the health check report as an ASCII table for terminal output."""
    lines: list[str] = []

    # Header
    lines.append("")
    lines.append("=" * 72)
    lines.append("  RAG HEALTH CHECK")
    lines.append("=" * 72)
    lines.append(f"  Checked at: {report['checked_at']}")
    overall = "STALE" if report["is_stale"] else "HEALTHY"
    lines.append(f"  Overall:    {overall}")
    lines.append("-" * 72)

    # Bucket table header
    lines.append("")
    lines.append(
        f"  {'Bucket':<12} {'Status':<10} {'Chunks':>8} "
        f"{'Size':>8} {'Index Age':>10} {'Source Age':>11}"
    )
    lines.append(f"  {'─' * 12} {'─' * 10} {'─' * 8} {'─' * 8} {'─' * 10} {'─' * 11}")

    # Bucket rows
    for name, info in report["buckets"].items():
        if not info["exists"]:
            status = "NOT BUILT"
            chunks = "-"
            size = "-"
            idx_age = "-"
            src_age = "-"
        else:
            status = "STALE" if info["is_stale"] else "FRESH"
            chunks = str(info["chunk_count"])
            size = f"{info['size_mb']}MB"
            idx_age = _format_age(info["index_age_hours"])
            src_age = _format_age(info["newest_source_age_hours"])

        lines.append(
            f"  {name:<12} {status:<10} {chunks:>8} "
            f"{size:>8} {idx_age:>10} {src_age:>11}"
        )

    # Knowledge graph section
    lines.append("")
    lines.append("-" * 72)
    lines.append("  Knowledge Graph")
    lines.append("-" * 72)

    graph = report["knowledge_graph"]
    if not graph["exists"]:
        lines.append("  Status: NOT BUILT")
    else:
        lines.append(f"  Entities:   {graph['entity_count']}")
        lines.append(f"  Edges:      {graph['edge_count']}")
        lines.append(f"  Last build: {graph['last_build_time']}")
        lines.append(f"  File size:  {graph['file_size_mb']}MB")

    # Footer
    lines.append("")
    lines.append("=" * 72)

    if report["is_stale"]:
        lines.append("  Run /rag-rebuild to update stale indexes.")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entrypoint for RAG health check."""
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG Health Check -- aggregated metrics for all buckets"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output machine-readable JSON instead of ASCII table",
    )
    args = parser.parse_args()

    report = run_health_check()

    if args.json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_ascii_table(report))

    # Exit code 1 when any index is stale -- enables CI integration.
    if report["is_stale"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
