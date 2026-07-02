"""RAGAS Evaluator — IDBasedContextPrecision baseline.

Zero-LLM evaluation metric: compares retrieved chunk_ids against
ground-truth expected_chunk_ids. No API calls required.

Story: STORY-RAG-9 (S9) — Phase 2 Wave 5
Date: 2026-04-12

Output:
  baseline: .data/ragas/baseline_YYYY-MM-DD.json
  Format: {"metric": "IDBasedContextPrecision", "score": float,
           "pairs_evaluated": int, "timestamp": str, "by_person": dict}

Usage:
    python3 -m engine.intelligence.rag.ragas_evaluator
    python3 -m engine.intelligence.rag.ragas_evaluator --generate-pairs
    python3 -m engine.intelligence.rag.ragas_evaluator --pairs-path custom.jsonl
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# IDBasedContextPrecision (zero-LLM)
# ---------------------------------------------------------------------------
def id_based_context_precision(
    retrieved_ids: list[str],
    expected_ids: list[str],
) -> float:
    """Compute IDBasedContextPrecision for a single query.

    Precision = |retrieved ∩ expected| / |retrieved|

    Zero-LLM: uses chunk ID set intersection.
    Returns 0.0 if no chunks retrieved.

    Args:
        retrieved_ids: Chunk IDs returned by RAG pipeline.
        expected_ids: Ground-truth chunk IDs from HEURISTICAS.yaml.

    Returns: float in [0.0, 1.0]
    """
    if not retrieved_ids:
        return 0.0
    retrieved_set = set(retrieved_ids)
    expected_set = set(expected_ids)
    hits = retrieved_set & expected_set
    return len(hits) / len(retrieved_set)


# ---------------------------------------------------------------------------
# SHARED RETRIEVAL (reused by eval_gate.py — single retrieval source of truth)
# ---------------------------------------------------------------------------
def retrieve_chunk_ids(
    query: str,
    bucket: str = "external",
    top_k: int = 10,
) -> list[str]:
    """Retrieve ordered chunk_ids for a query (best first).

    Mirrors the retrieval path used by `evaluate()`: RRF hybrid retrieval with
    a BM25-only fallback when the RRF pipeline is unavailable. Extracted so the
    recall@K eval gate (`eval_gate.py`) reuses ONE retrieval entrypoint instead
    of duplicating the fusion/fallback logic.

    Returns [] on any retrieval failure (the caller decides how to score an
    empty result; the eval gate treats empty retrieval as recall 0, NOT as an
    error — only an exception is fail-closed).

    Story: STORY-GBA-F0.1 (EPIC-GBRAIN-ABSORPTION).
    """
    # Primary: RRF hybrid retrieval (pgvector dense + BM25 sparse).
    try:
        from .rrf_retrieval import rrf_retrieve

        results = rrf_retrieve(query, bucket=bucket, top_k=top_k)
        return [r.chunk_id for r in results]
    except Exception:
        pass

    # Fallback: BM25-only via local hybrid_index.
    try:
        from .hybrid_index import get_index

        idx = get_index()
        if idx.built:
            bm25_results = idx.bm25.query(query, top_k=top_k)
            return [
                idx.chunks[i].get("chunk_id", str(i))
                for i, _ in bm25_results
                if i < len(idx.chunks)
            ]
    except Exception:
        pass

    return []


# ---------------------------------------------------------------------------
# EVALUATE PIPELINE
# ---------------------------------------------------------------------------
def evaluate(
    pairs: list[dict] | None = None,
    pairs_path: Path | None = None,
    top_k: int = 10,
    verbose: bool = False,
) -> dict:
    """Run IDBasedContextPrecision evaluation over ground truth pairs.

    Args:
        pairs: Pre-loaded list of ground truth dicts.
        pairs_path: Path to JSONL file (used if pairs is None).
        top_k: Number of chunks to retrieve per query.
        verbose: Print per-query scores.

    Returns:
        {
            "metric": "IDBasedContextPrecision",
            "score": float,
            "pairs_evaluated": int,
            "pairs_skipped": int,
            "timestamp": str,
            "by_person": {person: {"score": float, "count": int}},
        }
    """
    # Load ground truth
    if pairs is None:
        from .ground_truth_generator import load_pairs

        pairs = load_pairs(pairs_path)

    if not pairs:
        return {
            "metric": "IDBasedContextPrecision",
            "score": 0.0,
            "pairs_evaluated": 0,
            "pairs_skipped": 0,
            "error": "No ground truth pairs. Run --generate-pairs first.",
        }

    # Import retrieval pipeline (lazy, non-blocking)
    try:
        from .rrf_retrieval import rrf_retrieve

        retrieval_available = True
    except Exception:
        retrieval_available = False

    scores: list[float] = []
    by_person: dict[str, list[float]] = {}
    skipped = 0

    for pair in pairs:
        query = pair.get("query", "")
        expected_ids = pair.get("expected_chunk_ids", [])
        person = pair.get("person", "unknown")

        if not query or not expected_ids:
            skipped += 1
            continue

        # Retrieve chunks
        retrieved_ids: list[str] = []
        if retrieval_available:
            try:
                bucket = "external"  # HEURISTICAS are always external bucket
                results = rrf_retrieve(query, bucket=bucket, top_k=top_k)
                retrieved_ids = [r.chunk_id for r in results]
            except Exception:
                skipped += 1
                continue
        else:
            # Fallback: try BM25-only via hybrid_index
            try:
                from .hybrid_index import get_index

                idx = get_index()
                if idx.built:
                    bm25_results = idx.bm25.query(query, top_k=top_k)
                    retrieved_ids = [
                        idx.chunks[i].get("chunk_id", str(i))
                        for i, _ in bm25_results
                        if i < len(idx.chunks)
                    ]
            except Exception:
                skipped += 1
                continue

        precision = id_based_context_precision(retrieved_ids, expected_ids)
        scores.append(precision)
        by_person.setdefault(person, []).append(precision)

        if verbose:
            print(f"  [{person}] {query[:60]}... → {precision:.3f}")

    overall = sum(scores) / len(scores) if scores else 0.0

    return {
        "metric": "IDBasedContextPrecision",
        "score": round(overall, 4),
        "pairs_evaluated": len(scores),
        "pairs_skipped": skipped,
        "timestamp": datetime.now(UTC).isoformat(),
        "by_person": {
            p: {
                "score": round(sum(s) / len(s), 4),
                "count": len(s),
            }
            for p, s in by_person.items()
        },
    }


def save_baseline(result: dict, output_path: Path | None = None) -> Path:
    """Save evaluation result as baseline JSON."""
    if output_path is None:
        root = Path(__file__).resolve().parents[3]
        ragas_dir = root / ".data" / "ragas"
        ragas_dir.mkdir(parents=True, exist_ok=True)
        date = datetime.now(UTC).strftime("%Y-%m-%d")
        output_path = ragas_dir / f"baseline_{date}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="RAGAS IDBasedContextPrecision evaluation")
    parser.add_argument(
        "--generate-pairs",
        action="store_true",
        help="Generate ground truth pairs before evaluating",
    )
    parser.add_argument(
        "--pairs-path", type=Path, default=None, help="Path to custom ground truth JSONL"
    )
    parser.add_argument(
        "--top-k", type=int, default=10, help="Chunks to retrieve per query (default 10)"
    )
    parser.add_argument("--verbose", action="store_true", help="Print per-query scores")
    args = parser.parse_args()

    # Generate pairs if requested
    if args.generate_pairs:
        from .ground_truth_generator import generate_pairs, save_pairs

        print("Generating ground truth pairs...")
        pairs = generate_pairs()
        out = save_pairs(pairs)
        print(f"Generated {len(pairs)} pairs → {out}\n")

    # Evaluate
    print(f"Running IDBasedContextPrecision (top_k={args.top_k}, zero-LLM)...")
    result = evaluate(pairs_path=args.pairs_path, top_k=args.top_k, verbose=args.verbose)

    print(f"\n{'=' * 50}")
    print(f"IDBasedContextPrecision: {result['score']:.4f}")
    print(f"Pairs evaluated: {result['pairs_evaluated']}")
    print(f"Pairs skipped:   {result['pairs_skipped']}")

    if result.get("by_person"):
        print("\nBy person:")
        for person, stats in sorted(result["by_person"].items(), key=lambda x: -x[1]["score"]):
            print(f"  {person}: {stats['score']:.4f} ({stats['count']} pairs)")
    print(f"{'=' * 50}\n")

    # Save baseline
    out = save_baseline(result)
    print(f"Baseline saved → {out}")


if __name__ == "__main__":
    main()
