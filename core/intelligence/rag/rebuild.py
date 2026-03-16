#!/usr/bin/env python3
"""
REBUILD - RAG Index + Knowledge Graph Full Rebuild
====================================================
Rebuilds all RAG indexes (BM25 per bucket) and the knowledge graph
in a single deterministic pass.  No LLM calls.

Called automatically by the MCE pipeline ``cmd_finalize`` step, or
manually via CLI for maintenance / recovery.

Usage::

    python3 -m core.intelligence.rag.rebuild [--bucket BUCKET] [--full]

Options:
    --bucket external|business|personal|all   (default: all)
    --full   Include vector embeddings (requires VOYAGE_API_KEY)

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import time
from typing import Any


def rebuild(
    bucket: str = "all",
    skip_vectors: bool = True,
) -> dict[str, Any]:
    """Rebuild RAG indexes for specified bucket(s) and knowledge graph.

    Args:
        bucket: Which bucket to rebuild --
            ``"external"``, ``"business"``, ``"personal"``, or ``"all"``.
        skip_vectors: If ``True`` (default), only build BM25 indexes.
            Set to ``False`` for full vector rebuild (needs VOYAGE_API_KEY).

    Returns:
        Stats dict with per-bucket chunk counts and graph stats::

            {
                "external": {"chunks": 3012, "dir": ".data/rag_index"},
                "business": {"chunks": 48, "dir": ".data/rag_business"},
                "personal": {"chunks": 12, "dir": "knowledge/personal/index"},
                "graph": {"total_entities": 1302, "total_edges": 2508, ...},
                "duration_s": 4.2,
            }
    """
    from core.paths import KNOWLEDGE_PERSONAL, RAG_BUSINESS, RAG_INDEX

    from .graph_builder import build_graph
    from .hybrid_index import HybridIndex

    t0 = time.monotonic()
    results: dict[str, Any] = {}

    # -- Per-bucket BM25 indexes ------------------------------------------

    buckets_to_build = (
        ["external", "business", "personal"]
        if bucket == "all"
        else [bucket]
    )

    bucket_dirs = {
        "external": RAG_INDEX,
        "business": RAG_BUSINESS,
        "personal": KNOWLEDGE_PERSONAL / "index",
    }

    for b in buckets_to_build:
        target_dir = bucket_dirs.get(b)
        if target_dir is None:
            results[b] = {"error": f"Unknown bucket: {b}"}
            continue

        idx = HybridIndex.build_for_bucket(b, skip_vectors=skip_vectors)
        idx.save(target_dir)
        results[b] = {
            "chunks": len(idx.chunks),
            "dir": str(target_dir),
        }

    # -- Knowledge graph (always rebuilt) ---------------------------------

    graph = build_graph()
    graph.save()
    results["graph"] = graph.stats

    results["duration_s"] = round(time.monotonic() - t0, 2)
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Rebuild RAG indexes and knowledge graph"
    )
    parser.add_argument(
        "--bucket",
        default="all",
        choices=["external", "business", "personal", "all"],
        help="Which bucket to rebuild (default: all)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include vector embeddings (requires VOYAGE_API_KEY)",
    )
    args = parser.parse_args()

    skip_vectors = not args.full

    print(f"\n{'=' * 60}")
    print("RAG INDEX REBUILD")
    print(f"{'=' * 60}")
    print(f"  Bucket: {args.bucket}")
    print(f"  Mode:   {'full (BM25 + vectors)' if args.full else 'BM25-only'}")
    print(f"{'─' * 60}\n")

    results = rebuild(bucket=args.bucket, skip_vectors=skip_vectors)

    # Pretty-print results
    for key in ("external", "business", "personal"):
        if key in results:
            info = results[key]
            if "error" in info:
                print(f"  {key}: ERROR - {info['error']}")
            else:
                print(f"  {key}: {info['chunks']} chunks -> {info['dir']}")

    if "graph" in results:
        g = results["graph"]
        print(
            f"\n  graph: {g.get('total_entities', 0)} entities, "
            f"{g.get('total_edges', 0)} edges"
        )

    duration = results.get("duration_s", 0)
    print(f"\n  Total time: {duration}s")
    print(f"\n{'=' * 60}")

    # Also dump machine-readable JSON to stdout
    print("\n--- JSON ---")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
