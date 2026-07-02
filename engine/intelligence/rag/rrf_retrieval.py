"""RRF Hybrid Retrieval — pgvector + BM25 with result cache.

Pure Python implementation of Reciprocal Rank Fusion (k=60) combining:
  - Dense: pgvector via the canonical embedding gateway (OpenAI/1536)
  - Sparse: BM25 local index

Story: STORY-RAG-5 (S5) — Phase 1 Wave 3
Date: 2026-04-12

Constitution Art. XIII: bucket isolation enforced at every call.
RRF operates WITHIN a single bucket — never fuses across buckets.

Reference: FlashRAG Python RRF pattern (Compare S14-C2).
k=60: FlashRAG-recommended default for balanced precision/recall.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vector_store import SearchResult

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
RRF_K = 60  # RRF constant — FlashRAG default
DENSE_TOP = 30  # Dense candidates from pgvector
SPARSE_TOP = 30  # Sparse candidates from BM25
CACHE_SIZE = 512  # Max cached query results (LRU eviction)


# ---------------------------------------------------------------------------
# RESULT TYPE
# ---------------------------------------------------------------------------
@dataclass
class RRFResult:
    """A single result from RRF fusion."""

    chunk_id: str
    text: str
    score: float  # RRF score (not similarity — higher is better)
    bucket: str
    source_path: str
    person: str
    layer: str
    section: str
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "score": round(self.score, 6),
            "bucket": self.bucket,
            "source_path": self.source_path,
            "person": self.person,
            "layer": self.layer,
            "section": self.section,
            "text_preview": self.text[:200],
        }


# ---------------------------------------------------------------------------
# RRF CORE
# ---------------------------------------------------------------------------
def _rrf_fuse(
    rankings: list[list[tuple[str, float]]],
    k: int = RRF_K,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion over chunk_id-keyed rankings.

    Args:
        rankings: List of [(chunk_id, score), ...] from multiple retrievers.
        k: RRF constant. Higher k = more weight to lower ranks.

    Returns: [(chunk_id, rrf_score), ...] sorted descending, scores in [0, 1].

    STORY-GBA-F2.1: scores are normalized to [0, 1] after summation, ported
    literally from gbrain's ``rrfFusionWeighted`` (hybrid.ts, SHA 4ee530f).
    The gbrain divides every accumulated score by ``maxScore`` so the top
    result lands at 1.0 and the rest scale proportionally. This is a strictly
    monotonic transform (all raw scores are positive, divided by the same
    positive ``maxScore``) — it ONLY rescales, it NEVER reorders. The
    normalized range is the pre-requisite for the cosine re-score blend
    (F2.3: ``0.7·rrf + 0.3·cosine``) which needs both terms in [0, 1].

    Note: gbrain's ``compiled_truth`` boost is intentionally NOT ported — that
    is gbrain-specific page-type logic with no equivalent in mega-brain, and
    inventing it would violate Constitution Art. IV (No Invention).
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, (chunk_id, _score) in enumerate(ranking):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)

    if not scores:
        return []

    # Normalize to [0, 1] by dividing by the max score (gbrain hybrid.ts:1847).
    # Monotonic: preserves order, only rescales. Guard maxScore > 0 like gbrain.
    max_score = max(scores.values())
    if max_score > 0:
        scores = {cid: s / max_score for cid, s in scores.items()}

    return sorted(scores.items(), key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# COSINE RE-SCORE (STORY-GBA-F2.3) — blend 0.7·rrf + 0.3·cosine, same space
# ---------------------------------------------------------------------------
COSINE_RRF_WEIGHT = 0.7  # gbrain hybrid.ts:1949 — weight on normalized RRF
COSINE_SIM_WEIGHT = 0.3  # gbrain hybrid.ts:1949 — weight on cosine similarity


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors.

    Ported VERBATIM from gbrain ``cosineSimilarity`` (hybrid.ts, SHA 4ee530f):
    single pass accumulating dot product and both magnitudes, with a
    zero-magnitude guard returning 0.0 (never NaN). Vectors MUST share the same
    embedding space (same dimension) — guaranteed here because both the query
    and the hydrated chunk vector resolve through the F0.2 gateway / active
    column. Mismatched lengths zip to the shorter, but in the active-space
    invariant the lengths are always equal.
    """
    dot = 0.0
    mag_a = 0.0
    mag_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        mag_a += x * x
        mag_b += y * y
    denom = (mag_a**0.5) * (mag_b**0.5)
    return 0.0 if denom == 0 else dot / denom


def _cosine_rescore(
    fused: list[tuple[str, float]],
    query_vec: list[float],
    embedding_map: dict[str, list[float]],
) -> list[tuple[str, float]]:
    """Blend ``0.7·rrf_norm + 0.3·cosine`` and re-sort, in the ACTIVE space.

    Ported from gbrain ``cosineReScore`` (hybrid.ts:1949, SHA 4ee530f). Runs on
    the fused (already RRF-normalized by F2.1) candidates BEFORE the top_k cut,
    so a semantically closer chunk can climb above a lexically-favored one and
    survive truncation — gbrain's "runs before dedup so semantically better
    chunks survive".

    Fail-open contract (gbrain parity):
      - empty ``query_vec`` or empty ``embedding_map`` → return ``fused``
        untouched (no blend, original RRF order preserved).
      - a candidate with no hydrated embedding keeps its pure RRF score.

    Args:
        fused: ``[(chunk_id, rrf_score), ...]`` from ``_rrf_fuse`` (already in
            [0, 1] per F2.1).
        query_vec: The query embedding in the active space (F0.2 gateway).
        embedding_map: ``{chunk_id: chunk_embedding}`` hydrated from the active
            column — the SAME space as ``query_vec``.

    Returns:
        ``[(chunk_id, blended_score), ...]`` sorted by blended score descending.
    """
    if not query_vec or not embedding_map:
        return fused

    # Re-normalize RRF locally against the observed max (gbrain re-divides by
    # maxRrf inside cosineReScore). Idempotent here since F2.1 already put the
    # top at 1.0, but ported literally to preserve the contract.
    max_rrf = max((score for _, score in fused), default=0.0)

    rescored: list[tuple[str, float]] = []
    for chunk_id, rrf_score in fused:
        chunk_emb = embedding_map.get(chunk_id)
        if chunk_emb is None:
            # No hydrated vector → keep pure RRF score (gbrain: return r).
            rescored.append((chunk_id, rrf_score))
            continue
        cosine = cosine_similarity(query_vec, chunk_emb)
        norm_rrf = rrf_score / max_rrf if max_rrf > 0 else 0.0
        blended = COSINE_RRF_WEIGHT * norm_rrf + COSINE_SIM_WEIGHT * cosine
        rescored.append((chunk_id, blended))

    return sorted(rescored, key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# QUERY HASH (for cache key)
# ---------------------------------------------------------------------------
def _query_hash(query: str, bucket: str) -> str:
    return hashlib.sha256(f"{bucket}:{query}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# RESULT CACHE
# ---------------------------------------------------------------------------
# Module-level dict cache: {(query_hash, bucket): (timestamp, results)}
# Invalidated when rebuild signal is detected via staleness_checker.
_result_cache: dict[str, tuple[float, list[RRFResult]]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour default; invalidated on index rebuild


def _cache_get(query: str, bucket: str) -> list[RRFResult] | None:
    key = _query_hash(query, bucket)
    entry = _result_cache.get(key)
    if entry is None:
        return None
    ts, results = entry
    if time.time() - ts > _CACHE_TTL_SECONDS:
        del _result_cache[key]
        return None
    return results


def _cache_set(query: str, bucket: str, results: list[RRFResult]) -> None:
    if len(_result_cache) >= CACHE_SIZE:
        # Evict oldest entry
        oldest_key = min(_result_cache, key=lambda k: _result_cache[k][0])
        del _result_cache[oldest_key]
    _result_cache[_query_hash(query, bucket)] = (time.time(), results)


def invalidate_cache(bucket: str | None = None) -> int:
    """Invalidate result cache. Called by staleness_checker on rebuild.

    Args:
        bucket: Invalidate only this bucket. None = invalidate all.

    Returns: Number of entries removed.
    """
    if bucket is None:
        count = len(_result_cache)
        _result_cache.clear()
        return count
    # Bucket-scoped invalidation requires storing bucket in cache key separately
    # For simplicity, clear all (keys are hashed, can't filter by bucket without a reverse map)
    count = len(_result_cache)
    _result_cache.clear()
    return count


# ---------------------------------------------------------------------------
# EMBEDDING
# ---------------------------------------------------------------------------
def _embed_query(query: str) -> list[float] | None:
    """Embed query text through the canonical embedding gateway.

    STORY-GBA-F0.2: this previously embedded with a hardcoded voyage-4 model,
    placing queries in a different vector space than the OpenAI/1536 documents
    in pgvector — silently corrupting the cosine compare. It now resolves the
    model/dim from ``embedding_config`` (the single SOT), so query and document
    embeddings always share one space. Returns None on failure so dense
    retrieval degrades to sparse-only rather than crashing the query path.
    """
    try:
        from .embedding_config import embed_query

        return embed_query(query)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# MAIN RETRIEVAL FUNCTION
# ---------------------------------------------------------------------------
def rrf_retrieve(
    query: str,
    bucket: str = "external",
    top_k: int = 30,
    k: int = RRF_K,
    use_cache: bool = True,
) -> list[RRFResult]:
    """Hybrid RRF retrieval: pgvector dense + BM25 sparse.

    ALWAYS bucket-scoped (Art. XIII). Never cross-bucket.

    Args:
        query: Natural language query.
        bucket: Knowledge bucket to search (external | business | personal).
        top_k: Number of final results.
        k: RRF constant (default 60).
        use_cache: Return cached results if available.

    Returns: List of RRFResult, sorted by RRF score descending.
    """
    # Cache check
    if use_cache:
        cached = _cache_get(query, bucket)
        if cached is not None:
            return cached[:top_k]

    # ----------------------------------------------------------------
    # Dense retrieval: pgvector
    # ----------------------------------------------------------------
    dense_ranking: list[tuple[str, float]] = []
    query_vec = _embed_query(query)
    pgstore = None  # retained for F2.3 cosine re-score hydration (active column)

    if query_vec is not None:
        try:
            from .store_resolver import get_vector_store

            # STORY-GBA-F1.2: env-resolved backend (DATABASE_URL → PostgresStore,
            # SUPABASE_URL → PgVectorStore). On no-backend the resolver raises and
            # this except falls back to dense_map = {} (BM25-only retrieval).
            pgstore = get_vector_store(bucket=bucket)
            dense_results = pgstore.search(query_vec, top_k=DENSE_TOP)
            dense_ranking = [(r.chunk_id, r.score) for r in dense_results]
            # Build chunk_id → SearchResult map for text retrieval
            dense_map: dict[str, SearchResult] = {r.chunk_id: r for r in dense_results}
        except Exception:
            dense_map = {}
    else:
        dense_map = {}

    # ----------------------------------------------------------------
    # Sparse retrieval: BM25 (local index)
    # ----------------------------------------------------------------
    sparse_ranking: list[tuple[str, float]] = []
    sparse_map: dict[str, dict] = {}  # chunk_id → chunk dict (from local index)

    try:
        from .hybrid_index import get_index

        idx = get_index()
        if idx.built and idx.chunks:
            # Filter to current bucket
            bucket_chunks = [
                (i, ch) for i, ch in enumerate(idx.chunks) if ch.get("bucket", "external") == bucket
            ]
            # Run BM25 over bucket-filtered texts
            if bucket_chunks:
                # Run BM25 and filter results to bucket
                bm25_raw = idx.bm25.query(query, top_k=SPARSE_TOP)
                # Map local indices back to chunk_ids, filtering to bucket
                bucket_idx_set = {i for i, _ in bucket_chunks}
                for local_idx, score in bm25_raw:
                    if local_idx in bucket_idx_set and local_idx < len(idx.chunks):
                        ch = idx.chunks[local_idx]
                        if ch.get("bucket", "external") == bucket:
                            cid = ch.get("chunk_id", str(local_idx))
                            sparse_ranking.append((cid, score))
                            sparse_map[cid] = ch
    except Exception:
        pass

    # ----------------------------------------------------------------
    # RRF Fusion
    # ----------------------------------------------------------------
    rankings = []
    if dense_ranking:
        rankings.append(dense_ranking)
    if sparse_ranking:
        rankings.append(sparse_ranking)

    if not rankings:
        return []

    fused = _rrf_fuse(rankings, k=k)

    # ----------------------------------------------------------------
    # Cosine re-score (STORY-GBA-F2.3): blend 0.7·rrf + 0.3·cosine in the
    # ACTIVE embedding space, BEFORE the top_k cut so a semantically closer
    # chunk can survive truncation. Gated on the single-space invariant:
    #   - F0.2 guarantees one embedding gateway + one physical column, so the
    #     hydrated chunk vectors share the query's space.
    #   - We hydrate (never recompute) from the active column via pgstore.
    #   - Fail-open: no query vec / no pgstore / empty hydration → plain RRF.
    # ----------------------------------------------------------------
    if query_vec and pgstore is not None and fused:
        candidate_ids = [cid for cid, _ in fused]
        embedding_map = pgstore.get_embeddings_by_chunk_ids(candidate_ids)
        fused = _cosine_rescore(fused, query_vec, embedding_map)

    # ----------------------------------------------------------------
    # Build RRFResult list
    # ----------------------------------------------------------------
    results: list[RRFResult] = []
    for chunk_id, rrf_score in fused[:top_k]:
        # Prefer pgvector data (richer metadata), fallback to local
        if chunk_id in dense_map:
            sr = dense_map[chunk_id]
            result = RRFResult(
                chunk_id=chunk_id,
                text=sr.text,
                score=rrf_score,
                bucket=sr.metadata.get("bucket", bucket),
                source_path=sr.metadata.get("source_path", ""),
                person=sr.metadata.get("person", ""),
                layer=sr.metadata.get("layer", ""),
                section=sr.metadata.get("section", ""),
                metadata=sr.metadata,
            )
        elif chunk_id in sparse_map:
            ch = sparse_map[chunk_id]
            result = RRFResult(
                chunk_id=chunk_id,
                text=ch.get("text", ""),
                score=rrf_score,
                bucket=ch.get("bucket", bucket),
                source_path=ch.get("source_file", ""),
                person=ch.get("person", ""),
                layer=ch.get("layer", ""),
                section=ch.get("section", ""),
                metadata=ch.get("metadata", {}),
            )
        else:
            continue

        results.append(result)

    # Cache result
    if use_cache:
        _cache_set(query, bucket, results)

    return results
