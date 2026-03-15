#!/usr/bin/env python3
"""
BUCKET QUERY ROUTER - Story S15
=================================
Routes RAG queries to the appropriate knowledge bucket index:
  external  -> .data/rag_index  (expert knowledge, BM25 + vector)
  business  -> .data/rag_business (meetings, calls, org data)
  personal  -> knowledge/personal/index  (future)
  all       -> merge results from all available buckets
  auto      -> keyword detection to pick the best bucket

Graceful degradation: missing indexes return empty results, never crash.

Version: 1.0.0
Date: 2026-03-09
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Literal

from core.paths import KNOWLEDGE_PERSONAL, RAG_BUSINESS, RAG_INDEX

# ---------------------------------------------------------------------------
# TYPES
# ---------------------------------------------------------------------------
Bucket = Literal["external", "business", "personal", "all", "auto"]

VALID_BUCKETS: set[str] = {"external", "business", "personal", "all", "auto"}

# ---------------------------------------------------------------------------
# BUCKET -> INDEX DIRECTORY MAP
# ---------------------------------------------------------------------------
BUCKET_INDEX_DIRS: dict[str, Path] = {
    "external": RAG_INDEX,
    "business": RAG_BUSINESS,
    "personal": KNOWLEDGE_PERSONAL / "index",
}


# ---------------------------------------------------------------------------
# AUTO-ROUTING KEYWORD DETECTION
# ---------------------------------------------------------------------------
_EXTERNAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(?:hormozi|alex\s*hormozi)\b",
        r"\b(?:cole\s*gordon)\b",
        r"\b(?:jeremy\s*(?:miner|haynes))\b",
        r"\b(?:sam\s*oven[s]?)\b",
        r"\b(?:pedro\s*val[eé]rio)\b",
        r"\b(?:alan\s*nicolas)\b",
        r"\b(?:richard\s*linder)\b",
        r"\b(?:framework|methodology|metodologia|heuristic|heur[ií]stica)\b",
        r"\b(?:playbook|dna\s*cognitivo|mental\s*model)\b",
        r"\b(?:closer|closing|objection|obje[cç][aã]o)\b",
        r"\b(?:high[\s-]?ticket|sales\s*training|offer\s*creation)\b",
    ]
]

_BUSINESS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(?:meeting|reuni[aã]o|call|chamada)\b",
        r"\b(?:your-company)\b",  # Replace with your company name
        r"\b(?:team|equipe|time|colaborador)\b",
        r"\b(?:kpi|okr|mrr|arr|cac|ltv|churn)\b",
        r"\b(?:org|organiza[cç][aã]o|departamento|department)\b",
        r"\b(?:sprint|backlog|standup|retro)\b",
        r"\b(?:finance|financeiro|dre|p&l|receita|revenue)\b",
        r"\b(?:contrata[cç][aã]o|hiring|onboarding)\b",
        r"\b(?:sop|processo\s*interno|internal\s*process)\b",
    ]
]

_PERSONAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(?:I\s*think|eu\s*acho|minha\s*opini[aã]o)\b",
        r"\b(?:my\s*notes?|minhas?\s*notas?)\b",
        r"\b(?:personally|pessoalmente)\b",
        r"\b(?:my\s*reflection|reflex[aã]o\s*pessoal)\b",
        r"\b(?:diario|diary|journal)\b",
    ]
]


def detect_bucket(question: str) -> Bucket:
    """Detect the best bucket from question keywords.

    Returns:
        The most likely bucket, or "all" if ambiguous.
    """
    scores: dict[str, int] = {"external": 0, "business": 0, "personal": 0}

    for pattern in _EXTERNAL_PATTERNS:
        if pattern.search(question):
            scores["external"] += 1

    for pattern in _BUSINESS_PATTERNS:
        if pattern.search(question):
            scores["business"] += 1

    for pattern in _PERSONAL_PATTERNS:
        if pattern.search(question):
            scores["personal"] += 1

    max_score = max(scores.values())
    if max_score == 0:
        return "all"

    # Check for ties
    winners = [b for b, s in scores.items() if s == max_score]
    if len(winners) > 1:
        return "all"

    return winners[0]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# INDEX LOADING HELPERS
# ---------------------------------------------------------------------------
def _index_exists(index_dir: Path) -> bool:
    """Check whether a usable index exists at the given directory."""
    chunks_file = index_dir / "chunks.json"
    bm25_file = index_dir / "bm25.json"
    return chunks_file.exists() and bm25_file.exists()


def _search_bucket(
    question: str,
    bucket_name: str,
    index_dir: Path,
    top_k: int = 10,
) -> list[dict]:
    """Search a single bucket index.

    Returns list of result dicts, each tagged with ``bucket``.
    Gracefully returns empty list if index missing or load fails.
    """
    if not _index_exists(index_dir):
        return []

    # Lazy import to avoid circular imports
    from .hybrid_index import HybridIndex
    from .hybrid_query import hybrid_search

    idx = HybridIndex()
    if not idx.load(index_dir):
        return []

    search_result = hybrid_search(question, top_k=top_k, index=idx)

    if "error" in search_result:
        return []

    results: list[dict] = []
    for item in search_result.get("results", []):
        tagged = dict(item)
        tagged["bucket"] = bucket_name
        results.append(tagged)

    return results


# ---------------------------------------------------------------------------
# MAIN QUERY FUNCTION
# ---------------------------------------------------------------------------
def query(
    question: str,
    bucket: Bucket = "all",
    top_k: int = 10,
) -> list[dict]:
    """Route query to appropriate RAG bucket.

    Args:
        question: Natural language query.
        bucket: Which bucket to search.
            - ``"external"`` -- expert knowledge only
            - ``"business"`` -- business/org data only
            - ``"personal"`` -- personal/cognitive data only
            - ``"all"``      -- search all available, merge by score
            - ``"auto"``     -- detect from question keywords
        top_k: Number of results to return.

    Returns:
        List of ``{chunk_id, text_preview, score, source_file, bucket, ...}`` dicts
        sorted by score descending. Empty list if nothing found or indexes missing.
    """
    if bucket not in VALID_BUCKETS:
        bucket = "all"

    # Resolve auto bucket
    resolved_bucket: str = bucket
    if bucket == "auto":
        resolved_bucket = detect_bucket(question)

    # Determine which buckets to search
    if resolved_bucket in ("external", "business", "personal"):
        buckets_to_search = [resolved_bucket]
    else:
        # "all" -- search every bucket that has an index
        buckets_to_search = list(BUCKET_INDEX_DIRS.keys())

    # Search each bucket
    all_results: list[dict] = []
    for bname in buckets_to_search:
        index_dir = BUCKET_INDEX_DIRS.get(bname)
        if index_dir is None:
            continue
        bucket_results = _search_bucket(question, bname, index_dir, top_k=top_k)
        all_results.extend(bucket_results)

    # Sort merged results by score descending
    all_results.sort(key=lambda r: r.get("score", 0), reverse=True)

    # Deduplicate by chunk_id (keep highest score)
    seen_chunk_ids: set[str] = set()
    deduplicated: list[dict] = []
    for item in all_results:
        cid = item.get("chunk_id", "")
        if cid and cid in seen_chunk_ids:
            continue
        if cid:
            seen_chunk_ids.add(cid)
        deduplicated.append(item)

    return deduplicated[:top_k]


# ---------------------------------------------------------------------------
# METADATA / INTROSPECTION
# ---------------------------------------------------------------------------
def available_buckets() -> dict[str, dict]:
    """Return metadata about each bucket's index status.

    Returns:
        ``{bucket_name: {"index_dir": str, "exists": bool}}``
    """
    status: dict[str, dict] = {}
    for bname, index_dir in BUCKET_INDEX_DIRS.items():
        status[bname] = {
            "index_dir": str(index_dir),
            "exists": _index_exists(index_dir),
        }
    return status


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for bucket query router."""
    if len(sys.argv) < 2:
        print('Usage: python3 -m core.intelligence.rag.bucket_query_router "<query>" [bucket]')
        print("  bucket: external | business | personal | all | auto  (default: all)")
        print()
        print("Examples:")
        print('  python3 -m core.intelligence.rag.bucket_query_router "Hormozi offer"')
        print(
            '  python3 -m core.intelligence.rag.bucket_query_router "team meeting notes" business'
        )
        print('  python3 -m core.intelligence.rag.bucket_query_router "closing framework" auto')
        sys.exit(1)

    question = sys.argv[1]
    bucket_arg: Bucket = "all"
    if len(sys.argv) >= 3 and sys.argv[2] in VALID_BUCKETS:
        bucket_arg = sys.argv[2]  # type: ignore[assignment]

    print(f"\n{'=' * 60}")
    print("BUCKET QUERY ROUTER")
    print(f"{'=' * 60}")
    print(f"Query:  {question}")
    print(f"Bucket: {bucket_arg}")

    if bucket_arg == "auto":
        detected = detect_bucket(question)
        print(f"  -> auto-detected: {detected}")

    print()

    # Show bucket status
    buckets = available_buckets()
    print("Bucket Status:")
    for bname, info in buckets.items():
        marker = "[OK]" if info["exists"] else "[--]"
        print(f"  {marker} {bname:10s}  {info['index_dir']}")
    print()

    t0 = time.time()
    results = query(question, bucket=bucket_arg, top_k=10)
    latency_ms = (time.time() - t0) * 1000

    print(f"Results: {len(results)}  ({latency_ms:.1f}ms)")
    print()

    for r in results:
        rank = r.get("rank", "?")
        score = r.get("score", 0)
        cid = r.get("chunk_id", "?")
        bkt = r.get("bucket", "?")
        preview = r.get("text_preview", "")[:80]
        print(f"  #{rank} [{score:.4f}] ({bkt}) {cid}")
        print(f"     {preview}...")
        print()

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
