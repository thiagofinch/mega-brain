#!/usr/bin/env python3
"""
RAG HEALTH CHECK - BrainHealth 6-Metric Contract
====================================================================
Unified health metrics for all RAG buckets. Absorbs staleness detection
(formerly in staleness_checker.py) and exports a BrainHealth dataclass
with 6 canonical metrics consumed by engine/doctor.py and /rag-health.

Skill activation:  /rag-health
CLI:               python3 -m engine.intelligence.rag.health_check
Exit code:         0 = all healthy, 1 = at least one issue

Imports:
    from engine.intelligence.rag.health_check import BrainHealth, run_health_check

Story: W2-001.10
DELTA: #23, #22
Version: 2.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.intelligence.rag.embedding_config import get_embedding_config
from engine.paths import (
    DATA,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_GRAPH,
    KNOWLEDGE_PERSONAL,
    RAG_BUSINESS,
    RAG_INDEX,
)

# ---------------------------------------------------------------------------
# TYPE CONTRACT
# ---------------------------------------------------------------------------


@dataclass
class BrainHealth:
    """Canonical 6-metric health contract for the RAG subsystem.

    Consumed by engine/doctor.py (Wave 1) and /rag-health skill.

    Attributes:
        index_count: Total number of indexed documents (chunks) across all buckets.
        stale_count: Number of buckets whose index is older than newest source.
        orphan_count: Chunks in index directories that have no parent document
                      (approximated via chunks without matching source files).
        avg_freshness: Average age in days of the newest source file per bucket.
                       Lower = fresher. -1.0 if no sources exist.
        dead_links: Links in knowledge graph pointing to non-existent nodes.
        embedding_dimension_consistency: True if all sampled embeddings match
                                         the canonical dimension from embedding_config.
    """

    index_count: int
    stale_count: int
    orphan_count: int
    avg_freshness: float
    dead_links: int
    embedding_dimension_consistency: bool


# ---------------------------------------------------------------------------
# CONSTANTS (absorbed from staleness_checker.py)
# ---------------------------------------------------------------------------

# Map bucket names to their index directories for chunk counting.
_BUCKET_INDEX_DIRS: dict[str, Path] = {
    "external": RAG_INDEX,
    "business": RAG_BUSINESS,
    "personal": KNOWLEDGE_PERSONAL / "index",
}

# Map each bucket to its index directory and source directories.
# Absorbed from staleness_checker._BUCKET_CONFIG.
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

# Knowledge graph path
_GRAPH_FILE = KNOWLEDGE_GRAPH / "graph.json"


# ---------------------------------------------------------------------------
# STALENESS HELPERS (absorbed from staleness_checker.py)
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

    return min(mtimes) if mtimes else 0.0


# ---------------------------------------------------------------------------
# STALENESS PUBLIC API (backward-compatible, absorbed from staleness_checker)
# ---------------------------------------------------------------------------


def check_staleness(bucket: str = "all") -> dict[str, Any]:
    """Check whether RAG indexes are stale relative to source files.

    Backward-compatible with the former staleness_checker.check_staleness().

    Args:
        bucket: ``"external"``, ``"business"``, ``"personal"``, or
            ``"all"`` (default) to check every bucket.

    Returns:
        Dict with per-bucket results and a top-level ``is_stale`` flag.
    """
    now = time.time()
    buckets_to_check = list(_BUCKET_CONFIG.keys()) if bucket == "all" else [bucket]

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
# CHUNK / INDEX HELPERS
# ---------------------------------------------------------------------------


def _count_chunks(index_dir: Path) -> int:
    """Count chunks in a bucket's chunks.json file.

    Returns 0 if the file does not exist or cannot be parsed.
    """
    chunks_file = index_dir / "chunks.json"
    if not chunks_file.exists():
        return 0

    try:
        with open(chunks_file, encoding="utf-8") as f:
            data = json.load(f)

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
    """Total size of all files in an index directory, in megabytes."""
    if not index_dir.exists():
        return 0.0
    total = sum(f.stat().st_size for f in index_dir.iterdir() if f.is_file())
    return round(total / (1024 * 1024), 1)


def _load_graph_stats() -> dict[str, Any]:
    """Load knowledge graph stats from graph.json."""
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
    result["file_size_mb"] = round(_GRAPH_FILE.stat().st_size / (1024 * 1024), 2)

    mtime = _GRAPH_FILE.stat().st_mtime
    result["last_build_time"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))

    try:
        with open(_GRAPH_FILE, encoding="utf-8") as f:
            graph = json.load(f)

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


def _count_dead_links_in_graph() -> int:
    """Count links in the knowledge graph that point to non-existent nodes.

    Returns 0 if graph file does not exist or has no edges.
    """
    if not _GRAPH_FILE.exists():
        return 0

    try:
        with open(_GRAPH_FILE, encoding="utf-8") as f:
            graph = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0

    entities = graph.get("entities", [])
    edges = graph.get("edges", [])

    if not edges:
        return 0

    # Build set of known entity IDs/slugs
    entity_ids: set[str] = set()
    for entity in entities:
        if isinstance(entity, dict):
            for key in ("id", "slug", "name"):
                if key in entity:
                    entity_ids.add(str(entity[key]))
        elif isinstance(entity, str):
            entity_ids.add(entity)

    dead = 0
    for edge in edges:
        if isinstance(edge, dict):
            target = str(edge.get("to", edge.get("target", "")))
            source = str(edge.get("from", edge.get("source", "")))
            if target and target not in entity_ids:
                dead += 1
            if source and source not in entity_ids:
                dead += 1

    return dead


def _check_embedding_dimension_consistency() -> bool:
    """Verify that sampled embeddings match the canonical dimension.

    Samples up to 5 embeddings from each bucket's chunks.json and checks
    that their dimension matches embedding_config.DIMENSIONS.

    Returns True if all sampled embeddings are consistent (or none exist).
    """
    expected_dim = get_embedding_config()["dimensions"]

    for index_dir in _BUCKET_INDEX_DIRS.values():
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            continue

        try:
            with open(chunks_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Extract chunks list
        chunks: list[Any] = []
        if isinstance(data, list):
            chunks = data
        elif isinstance(data, dict):
            for key in ("chunks", "documents"):
                if key in data and isinstance(data[key], list):
                    chunks = data[key]
                    break

        # Sample up to 5 chunks with embeddings
        sampled = 0
        for chunk in chunks:
            if sampled >= 5:
                break
            if not isinstance(chunk, dict):
                continue
            embedding = chunk.get("embedding") or chunk.get("vector")
            if embedding and isinstance(embedding, list):
                if len(embedding) != expected_dim:
                    return False
                sampled += 1

    return True


def _count_orphan_chunks() -> int:
    """Count chunks that appear to have no matching source file.

    Approximation: checks if chunks reference a source path that no longer
    exists on the filesystem. Returns 0 if no source references are found
    in chunks (conservative -- assumes no orphans when we cannot tell).
    """
    orphan_count = 0

    for index_dir in _BUCKET_INDEX_DIRS.values():
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            continue

        try:
            with open(chunks_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        chunks: list[Any] = []
        if isinstance(data, list):
            chunks = data
        elif isinstance(data, dict):
            for key in ("chunks", "documents"):
                if key in data and isinstance(data[key], list):
                    chunks = data[key]
                    break

        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            source = chunk.get("source") or chunk.get("source_file") or ""
            if source and not Path(source).exists():
                orphan_count += 1

    return orphan_count


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

    Returns a structured dict with all metrics plus the BrainHealth contract,
    suitable for both programmatic consumption and rendering.
    """
    staleness = check_staleness(bucket="all")

    total_chunks = 0
    stale_count = 0
    freshness_values: list[float] = []

    buckets: dict[str, Any] = {}
    for name, index_dir in _BUCKET_INDEX_DIRS.items():
        stale_info = staleness["buckets"].get(name, {})
        chunk_count = _count_chunks(index_dir)
        size_mb = _index_size_mb(index_dir)

        total_chunks += chunk_count

        if stale_info.get("is_stale", True):
            stale_count += 1

        src_age_hours = stale_info.get("newest_source_age_hours", -1.0)
        if src_age_hours >= 0:
            freshness_values.append(src_age_hours / 24.0)  # convert to days

        buckets[name] = {
            "exists": index_dir.exists() and (index_dir / "chunks.json").exists(),
            "chunk_count": chunk_count,
            "size_mb": size_mb,
            "is_stale": stale_info.get("is_stale", True),
            "index_age_hours": stale_info.get("index_age_hours", -1.0),
            "newest_source_age_hours": src_age_hours,
            "newest_source": stale_info.get("newest_source", ""),
        }

    graph = _load_graph_stats()
    dead_links = _count_dead_links_in_graph()
    orphan_count = _count_orphan_chunks()
    embedding_consistent = _check_embedding_dimension_consistency()
    avg_freshness = (
        round(sum(freshness_values) / len(freshness_values), 2) if freshness_values else -1.0
    )

    brain_health = BrainHealth(
        index_count=total_chunks,
        stale_count=stale_count,
        orphan_count=orphan_count,
        avg_freshness=avg_freshness,
        dead_links=dead_links,
        embedding_dimension_consistency=embedding_consistent,
    )

    return {
        "checked_at": staleness["checked_at"],
        "is_stale": staleness["is_stale"],
        "brain_health": brain_health,
        "buckets": buckets,
        "knowledge_graph": graph,
    }


def render_ascii_table(report: dict[str, Any]) -> str:
    """Render the health check report as an ASCII table for terminal output."""
    lines: list[str] = []
    bh: BrainHealth = report["brain_health"]

    # Header
    lines.append("")
    lines.append("=" * 72)
    lines.append("  RAG HEALTH CHECK (BrainHealth 6-Metric)")
    lines.append("=" * 72)
    lines.append(f"  Checked at: {report['checked_at']}")
    overall = "STALE" if report["is_stale"] else "HEALTHY"
    lines.append(f"  Overall:    {overall}")
    lines.append("-" * 72)

    # BrainHealth summary
    lines.append("")
    lines.append("  BrainHealth Contract")
    lines.append(f"  {'.' * 40}")
    lines.append(f"    index_count:          {bh.index_count}")
    lines.append(f"    stale_count:          {bh.stale_count}")
    lines.append(f"    orphan_count:         {bh.orphan_count}")
    freshness_str = f"{bh.avg_freshness:.2f}d" if bh.avg_freshness >= 0 else "N/A"
    lines.append(f"    avg_freshness:        {freshness_str}")
    lines.append(f"    dead_links:           {bh.dead_links}")
    embed_str = "CONSISTENT" if bh.embedding_dimension_consistency else "INCONSISTENT"
    lines.append(f"    embedding_dim:        {embed_str}")
    lines.append("")
    lines.append("-" * 72)

    # Bucket table header
    lines.append("")
    lines.append(
        f"  {'Bucket':<12} {'Status':<10} {'Chunks':>8} "
        f"{'Size':>8} {'Index Age':>10} {'Source Age':>11}"
    )
    lines.append(
        f"  {'---' * 4:<12} {'---' * 3:<10} {'---' * 2:>8} "
        f"{'---' * 2:>8} {'---' * 3:>10} {'---' * 3:>11}"
    )

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
            f"  {name:<12} {status:<10} {chunks:>8} " f"{size:>8} {idx_age:>10} {src_age:>11}"
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
        description="RAG Health Check -- BrainHealth 6-metric contract"
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
        # Serialize BrainHealth dataclass to dict for JSON output
        report_json = {**report}
        bh = report_json.pop("brain_health")
        report_json["brain_health"] = {
            "index_count": bh.index_count,
            "stale_count": bh.stale_count,
            "orphan_count": bh.orphan_count,
            "avg_freshness": bh.avg_freshness,
            "dead_links": bh.dead_links,
            "embedding_dimension_consistency": bh.embedding_dimension_consistency,
        }
        print(json.dumps(report_json, indent=2, ensure_ascii=False))
    else:
        print(render_ascii_table(report))

    # Exit code 1 when any index is stale.
    if report["is_stale"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
