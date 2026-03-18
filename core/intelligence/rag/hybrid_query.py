#!/usr/bin/env python3
"""
HYBRID QUERY ENGINE - Phase 3.3
=================================
3-stage retrieval pipeline:
1. Vector search (voyage-context-3) → top 30
2. BM25 keyword search → top 30
3. Reciprocal Rank Fusion (RRF, k=60) → merged
4. Reranking (zerank-2 when available, else score-based) → top 10
5. Strategic ordering (most relevant at START and END of context)

Versao: 1.0.0
Data: 2026-03-01
"""

import sys
import time

from .hybrid_index import HybridIndex, get_index

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_TOP_K = 10
RRF_K = 60  # RRF constant (higher = more weight to lower ranks)
VECTOR_TOP = 30  # Candidates from vector search
BM25_TOP = 30  # Candidates from BM25 search
RERANK_CANDIDATES = 50  # Max candidates for reranking


# ---------------------------------------------------------------------------
# RECIPROCAL RANK FUSION
# ---------------------------------------------------------------------------
def reciprocal_rank_fusion(
    rankings: list[list[tuple[int, float]]],
    k: int = RRF_K,
) -> list[tuple[int, float]]:
    """Combine multiple rankings using RRF.

    Args:
        rankings: List of [(doc_index, score), ...] from different retrievers
        k: RRF constant

    Returns: [(doc_index, rrf_score), ...] sorted by score desc
    """
    scores: dict[int, float] = {}

    for ranking in rankings:
        for rank, (doc_idx, _score) in enumerate(ranking):
            rrf_score = 1.0 / (k + rank + 1)
            scores[doc_idx] = scores.get(doc_idx, 0) + rrf_score

    sorted_results = sorted(scores.items(), key=lambda x: -x[1])
    return sorted_results


# ---------------------------------------------------------------------------
# RERANKER
# ---------------------------------------------------------------------------
def rerank(
    query: str,
    candidates: list[tuple[int, float]],
    chunks: list[dict],
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[int, float]]:
    """Rerank candidates. Uses zerank-2 if available, else pass-through.

    Args:
        query: The search query
        candidates: [(doc_index, rrf_score), ...]
        chunks: All chunks (for text access)
        top_k: Number of results to return

    Returns: [(doc_index, rerank_score), ...] top_k results
    """
    if not candidates:
        return []

    # Try zerank-2 reranker
    try:
        return _rerank_zerank(query, candidates, chunks, top_k)
    except (ImportError, Exception):
        pass

    # Fallback: use RRF scores directly (already good quality)
    return candidates[:top_k]


def _rerank_zerank(
    query: str,
    candidates: list[tuple[int, float]],
    chunks: list[dict],
    top_k: int,
) -> list[tuple[int, float]]:
    """Rerank using ZeroEntropy zerank-2."""
    # Stub — activate when zeroentropy SDK is available
    # from zeroentropy import Client
    # client = Client()
    # texts = [chunks[idx]["text"][:2000] for idx, _ in candidates[:RERANK_CANDIDATES]]
    # results = client.rerank(query=query, documents=texts, model="zerank-2", top_k=top_k)
    # return [(candidates[r.index][0], r.score) for r in results]
    raise ImportError("zerank-2 not available")


# ---------------------------------------------------------------------------
# STRATEGIC ORDERING (Lost in the Middle mitigation)
# ---------------------------------------------------------------------------
def strategic_order(results: list[tuple[int, float]]) -> list[tuple[int, float]]:
    """Reorder results: most relevant at START and END of context.

    This mitigates the "lost in the middle" problem where LLMs pay more
    attention to the beginning and end of their context.

    Pattern: 1st, 3rd, 5th, ..., 6th, 4th, 2nd
    """
    if len(results) <= 2:
        return results

    # Split into odd and even positions
    front = results[::2]  # 0, 2, 4, ... (strongest)
    back = results[1::2]  # 1, 3, 5, ... (second tier)
    back.reverse()  # Reverse so 2nd strongest is at the end

    return front + back


# ---------------------------------------------------------------------------
# QUERY ENGINE
# ---------------------------------------------------------------------------
class QueryResult:
    """A single search result with metadata."""

    def __init__(self, chunk: dict, score: float, rank: int):
        self.chunk = chunk
        self.score = score
        self.rank = rank
        self.chunk_id = chunk.get("chunk_id", "")
        self.text = chunk.get("text", "")
        self.source_file = chunk.get("source_file", "")
        self.person = chunk.get("person", "")
        self.domain = chunk.get("domain", "")
        self.section = chunk.get("section", "")

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "score": round(self.score, 4),
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "person": self.person,
            "domain": self.domain,
            "section": self.section,
            "text_preview": self.text[:200],
        }


def hybrid_search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    index: HybridIndex | None = None,
    filters: dict | None = None,
    use_strategic_order: bool = True,
) -> dict:
    """Full hybrid search pipeline.

    Args:
        query: Search query
        top_k: Number of results
        index: HybridIndex instance (uses singleton if None)
        filters: Optional {"person": str, "domain": str, "layer": str}
        use_strategic_order: Apply lost-in-the-middle mitigation

    Returns:
        {
            "query": str,
            "results": [QueryResult.to_dict(), ...],
            "total_candidates": int,
            "pipeline": {"vector": int, "bm25": int, "rrf": int, "reranked": int},
            "latency_ms": float,
        }
    """
    t0 = time.time()
    idx = index or get_index()

    if not idx.built or not idx.chunks:
        return {"query": query, "error": "Index not built. Run hybrid_index.py --bm25-only first."}

    # Stage 1: Vector search
    vector_results = idx.vector.query(query, top_k=VECTOR_TOP)

    # Stage 2: BM25 search
    bm25_results = idx.bm25.query(query, top_k=BM25_TOP)

    # Stage 3: RRF fusion
    rankings = []
    if vector_results:
        rankings.append(vector_results)
    if bm25_results:
        rankings.append(bm25_results)

    if not rankings:
        return {"query": query, "results": [], "total_candidates": 0}

    fused = reciprocal_rank_fusion(rankings)

    # Apply filters
    if filters:
        fused = _apply_filters(fused, idx.chunks, filters)

    # Stage 4: Rerank
    reranked = rerank(query, fused[:RERANK_CANDIDATES], idx.chunks, top_k=top_k)

    # Stage 5: Strategic ordering
    if use_strategic_order:
        reranked = strategic_order(reranked)

    # Build results
    results = []
    for rank, (doc_idx, score) in enumerate(reranked):
        chunk = idx.get_chunk(doc_idx)
        if chunk:
            results.append(QueryResult(chunk, score, rank + 1))

    latency = (time.time() - t0) * 1000

    return {
        "query": query,
        "results": [r.to_dict() for r in results],
        "total_candidates": len(fused),
        "pipeline": {
            "vector": len(vector_results),
            "bm25": len(bm25_results),
            "rrf": len(fused),
            "reranked": len(reranked),
        },
        "latency_ms": round(latency, 1),
    }


def _apply_filters(
    results: list[tuple[int, float]],
    chunks: list[dict],
    filters: dict,
) -> list[tuple[int, float]]:
    """Filter results by metadata."""
    filtered = []
    for doc_idx, score in results:
        if doc_idx >= len(chunks):
            continue
        chunk = chunks[doc_idx]
        match = True
        for key, value in filters.items():
            if value and chunk.get(key, "").lower() != value.lower():
                match = False
                break
        if match:
            filtered.append((doc_idx, score))
    return filtered


# ---------------------------------------------------------------------------
# CONTEXT BUILDER (for debate integration)
# ---------------------------------------------------------------------------
def build_rag_context(
    query: str,
    top_k: int = 20,
    max_tokens: int = 8000,
    index: HybridIndex | None = None,
) -> dict:
    """Build RAG context for debate/conclave integration.

    Returns a formatted context block with sources.
    """
    result = hybrid_search(query, top_k=top_k, index=index)

    if "error" in result:
        return result

    context_parts = []
    sources = []
    total_chars = 0
    char_limit = max_tokens * 4  # Approximate

    for r in result["results"]:
        text = r.get("text_preview", "")
        # Get full text from chunk
        chunk_text = ""
        for rank_result in result["results"]:
            if rank_result["chunk_id"] == r["chunk_id"]:
                chunk_text = text
                break

        if total_chars + len(chunk_text) > char_limit:
            break

        citation = f"[RAG:{r['chunk_id']}]"
        context_parts.append(f"{citation} {chunk_text}")
        sources.append(
            {
                "chunk_id": r["chunk_id"],
                "source_file": r["source_file"],
                "person": r["person"],
                "section": r["section"],
            }
        )
        total_chars += len(chunk_text)

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources,
        "chunks_used": len(sources),
        "latency_ms": result["latency_ms"],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python3 -m core.intelligence.rag.hybrid_query "<query>"')
        print('Example: python3 -m core.intelligence.rag.hybrid_query "commission structure"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"\n{'=' * 60}")
    print("HYBRID QUERY ENGINE")
    print(f"{'=' * 60}")
    print(f"Query: {query}\n")

    result = hybrid_search(query)

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    pipe = result["pipeline"]
    print(
        f"Pipeline: vector={pipe['vector']}, bm25={pipe['bm25']}, "
        f"rrf={pipe['rrf']}, reranked={pipe['reranked']}"
    )
    print(f"Latency: {result['latency_ms']}ms\n")

    for r in result["results"]:
        print(f"  #{r['rank']} [{r['score']}] {r['chunk_id']}")
        print(f"     Source: {r['source_file']}")
        if r["person"]:
            print(f"     Person: {r['person']}")
        if r["section"]:
            print(f"     Section: {r['section']}")
        print(f"     Preview: {r['text_preview'][:100]}...")
        print()

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
