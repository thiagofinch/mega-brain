#!/usr/bin/env python3
"""
HYBRID QUERY ENGINE - Phase 3.3
=================================
3-stage retrieval pipeline:
1. Vector search (canonical embedding gateway — OpenAI/1536) → top 30
2. BM25 keyword search → top 30
3. Reciprocal Rank Fusion (RRF, k=60) → merged
4. 4-layer deduplication (chunk_id, source+offset, content hash, text similarity)
5. Score-based ranking → top 10
6. Strategic ordering (most relevant at START and END of context)

Versao: 1.1.0
Data: 2026-04-16
"""

import hashlib
import os
import sys
import time
from collections.abc import Callable
from difflib import SequenceMatcher

from .hybrid_index import HybridIndex, get_index, get_index_for_bucket


# S5: pgvector-backed RRF retrieval (primary path when Supabase is configured)
def _try_rrf_retrieve(query: str, bucket: str, top_k: int) -> list | None:
    """Attempt RRF retrieval via pgvector. Returns None if unavailable."""
    try:
        from engine.providers.supabase_client import is_enabled

        if not is_enabled():
            return None
        from .rrf_retrieval import rrf_retrieve

        results = rrf_retrieve(query, bucket=bucket, top_k=top_k)
        return results if results else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_TOP_K = 10
RRF_K = 60  # RRF constant (higher = more weight to lower ranks)
VECTOR_TOP = 30  # Candidates from vector search
BM25_TOP = 30  # Candidates from BM25 search
RERANK_CANDIDATES = 50  # Max candidates for reranking

# ---------------------------------------------------------------------------
# RERANKER (zerank-2 cross-encoder) — STORY-GBA-F2.2
# Ported from gbrain src/core/search/rerank.ts (SHA 4ee530f).
# ---------------------------------------------------------------------------
# Default cross-encoder model. Matches gbrain DEFAULT_RERANKER_MODEL
# (gateway.ts:114, SHA 4ee530f). The provider:model string is passed through
# to the reranker client; the API key is read from the env at call time.
DEFAULT_RERANKER_MODEL = "zeroentropyai:zerank-2"
# How many of the top RRF candidates to send to the cross-encoder. The
# un-reranked tail past this index keeps its original RRF order — this is the
# recall-preserving tail (gbrain rerank.ts:130 ``opts.topNIn``, default 30).
RERANKER_TOP_N_IN = 30
# Per-call timeout (seconds). gbrain default is 5000ms (gateway.ts
# DEFAULT_RERANK_TIMEOUT_MS). Search hot path — long stalls degrade UX.
RERANKER_TIMEOUT_S = 5.0
# Env var holding the zerank-2 API key. Absent/empty ⇒ reranker is
# unavailable ⇒ fail-open to RRF order (production behavior when the provider
# is not configured). No key is in .env today, so the default client below
# always fail-opens until a key is added (see Dev Agent Record STUB note).
RERANKER_API_KEY_ENV = "ZEROENTROPY_API_KEY"

# ---------------------------------------------------------------------------
# DELIBERATE ACTIVATION FLAG — STORY-GBA-F2.5
# ---------------------------------------------------------------------------
# Env var that turns the reranker ON/OFF *deliberately* (no code edit). Before
# F2.5, the reranker was "on" purely as a side effect of the API key existing
# in the env (the only OFF condition was the key being absent, which makes
# ``_default_reranker_fn`` fail-open). That made activation ACCIDENTAL. This
# flag makes it a registered DECISION and provides a kill-switch.
#
# Precedence (resolved by ``reranker_enabled()``):
#
#   | ZEROENTROPY_API_KEY | MCE_RERANKER_ENABLED | Reranker | Rationale            |
#   |---------------------|----------------------|----------|----------------------|
#   | absent/empty        | (any)                | OFF      | no key ⇒ nothing to  |
#   |                     |                      |          | turn on (fail-open)  |
#   | present             | not set              | ON       | safe default: key    |
#   |                     |                      |          | provisioned = intent |
#   | present             | 1/true/on/yes        | ON       | explicit activation  |
#   | present             | 0/false/off/no/""    | OFF      | KILL-SWITCH (key     |
#   |                     |                      |          | alone is NOT enough) |
#
# The kill-switch row is the heart of "deliberate": key presence alone no
# longer determines behavior uncontrollably.
RERANKER_FLAG_ENV = "MCE_RERANKER_ENABLED"
_TRUTHY = frozenset({"1", "true", "on", "yes"})
_FALSY = frozenset({"0", "false", "off", "no", ""})

# ---------------------------------------------------------------------------
# RERANKER PROVIDER SELECTION — STORY-CIH-RERANKER-PROVIDER
# ---------------------------------------------------------------------------
# Two live cross-encoders are wired: ``zeroentropy`` (zerank-2) and ``cohere``
# (rerank-v3.5). The provider is chosen DELIBERATELY via env (no code edit, no
# accidental default on key rotation). Each provider reads its OWN API key.
RERANKER_PROVIDER_ENV = "MCE_RERANKER_PROVIDER"
_VALID_PROVIDERS = frozenset({"zeroentropy", "cohere"})
_DEFAULT_PROVIDER = "zeroentropy"

# Cohere v2 rerank seam (ported from tests/rag/reranker_clients.py — the real
# client validated in epic-RETRIEVAL-BENCHMARK RBM-2). PT-BR SOTA per research.
COHERE_API_KEY_ENV = "COHERE_API_KEY"
COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"
COHERE_DEFAULT_MODEL = "rerank-v3.5"
COHERE_MAX_RETRIES = 6  # trial keys cap at ~10 calls/min
COHERE_RETRY_BACKOFF_S = 7.0


def reranker_provider() -> str:
    """Resolve the active reranker provider (``zeroentropy`` | ``cohere``).

    Unknown/unset ⇒ ``zeroentropy`` (the F2.2 default). Read at call time so a
    flip takes effect on the next query.
    """
    raw = os.environ.get(RERANKER_PROVIDER_ENV, "").strip().lower()
    return raw if raw in _VALID_PROVIDERS else _DEFAULT_PROVIDER


def _provider_key_env(provider: str) -> str:
    """Env var holding the API key for the given provider."""
    return COHERE_API_KEY_ENV if provider == "cohere" else RERANKER_API_KEY_ENV


def _parse_flag(raw: str | None) -> bool | None:
    """Parse ``MCE_RERANKER_ENABLED`` into True/False/None (unset/unknown).

    Returns:
        True  — explicit truthy (``1/true/on/yes``, case-insensitive).
        False — explicit falsy (``0/false/off/no`` or empty string).
        None  — env var not set (so the safe default applies).

    Unknown non-empty values fall back to None (treated as "not set" ⇒ safe
    default) — we never guess truthy from garbage; that would defeat the
    kill-switch's predictability.
    """
    if raw is None:
        return None
    val = raw.strip().lower()
    if val in _TRUTHY:
        return True
    if val in _FALSY:
        return False
    return None


def reranker_enabled() -> bool:
    """Resolve whether the zerank-2 reranker should run for this query.

    Pure function of two env vars (read at call time, so a kill-switch flip
    takes effect on the NEXT query — no restart, no code edit). Implements the
    precedence table above (STORY-GBA-F2.5 AC1/AC2):

      1. No API key ⇒ OFF (the default client would fail-open to RRF anyway;
         we short-circuit so the upstream call cost never materializes).
      2. Key present + flag unset/unknown ⇒ ON (safe default: a provisioned key
         expresses intent to use the reranker).
      3. Key present + flag explicitly falsy ⇒ OFF (the kill-switch — proves
         activation is DELIBERATE, not a side effect of the key existing).
      4. Key present + flag explicitly truthy ⇒ ON (explicit activation).
    """
    key = os.environ.get(_provider_key_env(reranker_provider()), "").strip()
    if not key:
        return False  # no key for the active provider ⇒ nothing to turn on
    flag = _parse_flag(os.environ.get(RERANKER_FLAG_ENV))
    if flag is None:
        return True  # safe default: key provisioned = intent to use
    return flag  # explicit truthy/falsy (kill-switch lives here)


class RerankError(Exception):
    """Reranker failure with a classified reason (ported from gbrain
    gateway.ts ``RerankError``). ``reason`` is one of: auth, rate_limit,
    network, timeout, payload_too_large, unknown.

    applyReranker catches this and fail-opens to the RRF order; the reason is
    recorded for audit/observability without ever breaking search.
    """

    def __init__(self, message: str, reason: str = "unknown"):
        super().__init__(message)
        self.reason = reason


def _hash_query(query: str) -> str:
    """SHA-256 prefix (8 hex chars) of the query — privacy-preserving audit
    key (gbrain rerank.ts ``hashQuery``). Never logs the raw query text."""
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:8]


def _zeroentropy_rerank(
    query: str,
    documents: list[str],
    *,
    model: str,
    timeout_s: float,
) -> list[tuple[int, float]]:
    """ZeroEntropy zerank-2 client. Raises ``RerankError`` so the caller
    fail-opens to RRF order. Mirrors gbrain ``gateway.rerank`` reason table."""
    api_key = os.environ.get(RERANKER_API_KEY_ENV, "").strip()
    if not api_key:
        raise RerankError(
            f"reranker unavailable: {RERANKER_API_KEY_ENV} not set", "auth"
        )
    try:
        import json
        import urllib.error
        import urllib.request

        # provider:model → modelId (gbrain resolveRecipe splits on ":").
        model_id = model.split(":", 1)[1] if ":" in model else model
        body = json.dumps(
            {"model": model_id, "query": query, "documents": documents}
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.zeroentropy.dev/v1/models/rerank",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        status = e.code
        reason = (
            "auth"
            if status in (401, 403)
            else "rate_limit"
            if status == 429
            else "network"
            if status >= 500
            else "unknown"
        )
        raise RerankError(f"rerank HTTP {status}", reason) from e
    except TimeoutError as e:
        raise RerankError("rerank timed out", "timeout") from e
    except urllib.error.URLError as e:
        raise RerankError(f"rerank network error: {e}", "network") from e
    except Exception as e:  # any unexpected shape ⇒ unknown
        raise RerankError(f"rerank failed: {e}", "unknown") from e

    results = payload.get("results")
    if not isinstance(results, list):
        raise RerankError("rerank: malformed response (no results array)", "unknown")
    return [
        (int(r.get("index", 0)), float(r.get("relevance_score", 0.0)))
        for r in results
        if isinstance(r, dict)
    ]


def _cohere_rerank(
    query: str,
    documents: list[str],
    *,
    timeout_s: float,
) -> list[tuple[int, float]]:
    """Cohere rerank-v3.5 client (ported from tests/rag/reranker_clients.py,
    validated in RBM-2). Bounded 429 retry for trial keys. Raises
    ``RerankError`` on failure so the caller fail-opens to RRF order."""
    api_key = os.environ.get(COHERE_API_KEY_ENV, "").strip()
    if not api_key:
        raise RerankError(
            f"reranker unavailable: {COHERE_API_KEY_ENV} not set", "auth"
        )
    import json
    import urllib.error
    import urllib.request

    body = json.dumps(
        {"model": COHERE_DEFAULT_MODEL, "query": query, "documents": documents}
    ).encode("utf-8")
    req = urllib.request.Request(
        COHERE_RERANK_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    payload = None
    last_err: Exception | None = None
    for attempt in range(COHERE_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            status = e.code
            if status == 429 and attempt < COHERE_MAX_RETRIES:
                time.sleep(COHERE_RETRY_BACKOFF_S)
                last_err = e
                continue
            reason = (
                "auth"
                if status in (401, 403)
                else "rate_limit"
                if status == 429
                else "network"
                if status >= 500
                else "unknown"
            )
            raise RerankError(f"cohere rerank HTTP {status}", reason) from e
        except TimeoutError as e:
            raise RerankError("cohere rerank timed out", "timeout") from e
        except urllib.error.URLError as e:
            raise RerankError(f"cohere rerank network error: {e}", "network") from e
        except Exception as e:
            raise RerankError(f"cohere rerank failed: {e}", "unknown") from e
    if payload is None:
        raise RerankError(f"cohere rerank exhausted retries: {last_err}", "rate_limit")

    results = payload.get("results")
    if not isinstance(results, list):
        raise RerankError("cohere rerank: malformed response (no results)", "unknown")
    return [
        (int(r.get("index", 0)), float(r.get("relevance_score", 0.0)))
        for r in results
        if isinstance(r, dict)
    ]


def _default_reranker_fn(
    query: str,
    documents: list[str],
    *,
    model: str,
    timeout_s: float,
) -> list[tuple[int, float]]:
    """Production reranker seam — dispatches to the provider chosen by
    ``MCE_RERANKER_PROVIDER`` (``zeroentropy`` default | ``cohere``). Each
    provider raises ``RerankError`` so ``apply_reranker`` fail-opens to RRF.
    """
    if reranker_provider() == "cohere":
        return _cohere_rerank(query, documents, timeout_s=timeout_s)
    return _zeroentropy_rerank(query, documents, model=model, timeout_s=timeout_s)


# Type of the injectable reranker seam (mirrors gbrain ``opts.rerankerFn``).
RerankerFn = Callable[..., list[tuple[int, float]]]


def apply_reranker(
    query: str,
    candidates: list[tuple[int, float]],
    chunks: list[dict],
    *,
    top_n_in: int = RERANKER_TOP_N_IN,
    model: str = DEFAULT_RERANKER_MODEL,
    timeout_s: float = RERANKER_TIMEOUT_S,
    reranker_fn: RerankerFn | None = None,
) -> list[tuple[int, float]]:
    """Reorder the top ``top_n_in`` candidates by cross-encoder relevance.

    LITERAL PORT of gbrain ``applyReranker`` (rerank.ts:58, SHA 4ee530f):

      * Split candidates into ``head`` (top ``top_n_in``) and ``tail``.
      * Send ``head`` document texts to the reranker; reorder ``head`` by the
        returned relevance scores.
      * **Recall-preserving tail (rerank.ts:130):** the un-reranked ``tail``
        keeps its original RRF position, appended after the reordered head.
        Head items the reranker did NOT return are preserved at the end of the
        head section (no silent recall loss).
      * **Fail-open:** ANY error (auth, network, timeout, malformed, …) returns
        the original ``candidates`` order unchanged. Never raises. Search
        reliability beats reranker quality.

    The ``reranker_fn`` seam is injected in tests (a deterministic stub) and is
    ``_default_reranker_fn`` (zerank-2 client) in production. Truncation to
    ``top_k`` is the caller's job (``rerank``) — this function only reorders.

    Args:
        query: search query.
        candidates: ``[(doc_index, rrf_score), ...]`` already deduped, RRF order.
        chunks: all chunks (for document text access).
        top_n_in: how many top candidates to rerank (recall-preserving tail
            starts after this).
        model: provider:model string for the cross-encoder.
        timeout_s: per-call timeout.
        reranker_fn: test seam; production NEVER sets this.

    Returns: reordered ``[(doc_index, score), ...]`` (same length as input;
        nothing dropped here).
    """
    # Empty / degenerate input passes through (no upstream call).
    if not candidates or top_n_in <= 0:
        return candidates

    head = candidates[:top_n_in]
    tail = candidates[top_n_in:]

    # Document text for the head. Fall back to other text fields then empty
    # (defensive — gbrain falls back to title). Empty docs are still sent; the
    # upstream model decides.
    documents: list[str] = []
    for doc_idx, _score in head:
        text = ""
        if 0 <= doc_idx < len(chunks):
            chunk = chunks[doc_idx]
            text = chunk.get("text", "") or chunk.get("text_preview", "") or chunk.get("section", "")
        documents.append(text)

    fn = reranker_fn or _default_reranker_fn
    _provider = "injected" if reranker_fn is not None else reranker_provider()
    _t0 = time.perf_counter()
    try:
        reranked = fn(
            query,
            documents,
            model=model,
            timeout_s=timeout_s,
        )
    except Exception as err:  # fail-open on EVERY error class
        reason = err.reason if isinstance(err, RerankError) else "unknown"
        # Observability without breaking search; audit logging must never throw.
        try:
            sys.stderr.write(
                f"[reranker] {_provider} fail-open ({reason}) "
                f"query={_hash_query(query)} docs={len(documents)}\n"
            )
        except Exception:
            pass
        return candidates  # original RRF order, unchanged

    # Defensive: malformed shape ⇒ pass through (gbrain same guard).
    if not isinstance(reranked, list) or len(reranked) == 0:
        return candidates

    # Visible success signal: proves the reranker actually ran and reordered,
    # so activation is observable on every query (not just inferable). Never
    # throws — audit logging must not break search.
    try:
        _ms = (time.perf_counter() - _t0) * 1000.0
        sys.stderr.write(
            f"[reranker] {_provider} reordered docs={len(documents)} "
            f"scored={len(reranked)} in {_ms:.0f}ms query={_hash_query(query)}\n"
        )
    except Exception:
        pass

    # Reorder head by reranker output. Keep only indices the reranker returned,
    # in its order; dedup repeats.
    seen: set[int] = set()
    reordered_head: list[tuple[int, float]] = []
    for r in reranked:
        idx, rel = r[0], r[1]
        if 0 <= idx < len(head) and idx not in seen:
            seen.add(idx)
            doc_idx, _rrf = head[idx]
            # Stamp reranker score onto the result tuple (replaces the carried
            # score for downstream ordering; RRF score lives in the tail/dedup).
            reordered_head.append((doc_idx, rel))

    # Head items the reranker dropped (rare) keep their original position at the
    # END of the head section — recall preserved, gbrain rerank.ts:128-130.
    for i in range(len(head)):
        if i not in seen:
            reordered_head.append(head[i])

    # Recall-preserving tail: original RRF order appended after reordered head.
    return reordered_head + tail


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
# 4-LAYER DEDUPLICATION
# ---------------------------------------------------------------------------
SIMILARITY_THRESHOLD = 0.95


def _text_hash(text: str) -> str:
    """SHA-256 hash of normalized text for content-level dedup."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def deduplicate_results(
    candidates: list[tuple[int, float]],
    chunks: list[dict],
) -> list[tuple[int, float]]:
    """4-layer deduplication after RRF fusion.

    Layers (applied in order, first match removes the duplicate):
      1. Exact chunk_id — same chunk indexed twice
      2. source_file + offset — same passage from same file
      3. Content hash (SHA-256) — identical text from different sources
      4. Text similarity > 0.95 — near-duplicate passages

    Args:
        candidates: [(doc_index, rrf_score), ...] sorted by score desc
        chunks: All chunks (for metadata access)

    Returns: deduplicated [(doc_index, rrf_score), ...]
    """
    seen_chunk_ids: set[str] = set()
    seen_source_offsets: set[str] = set()
    seen_hashes: set[str] = set()
    kept_texts: list[str] = []
    deduped: list[tuple[int, float]] = []

    for doc_idx, score in candidates:
        if doc_idx >= len(chunks):
            continue
        chunk = chunks[doc_idx]
        text = chunk.get("text", "")

        # Layer 1: exact chunk_id
        chunk_id = chunk.get("chunk_id", "")
        if chunk_id and chunk_id in seen_chunk_ids:
            continue
        if chunk_id:
            seen_chunk_ids.add(chunk_id)

        # Layer 2: source_file + offset
        source_file = chunk.get("source_file", "")
        offset = chunk.get("offset", "")
        if source_file and offset:
            key = f"{source_file}::{offset}"
            if key in seen_source_offsets:
                continue
            seen_source_offsets.add(key)

        # Layer 3: content hash
        if text:
            h = _text_hash(text)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

        # Layer 4: text similarity > threshold
        if text and any(
            SequenceMatcher(None, text[:500], kept[:500]).ratio() > SIMILARITY_THRESHOLD
            for kept in kept_texts
        ):
            continue

        if text:
            kept_texts.append(text[:500])
        deduped.append((doc_idx, score))

    return deduped


# ---------------------------------------------------------------------------
# RERANKER
# ---------------------------------------------------------------------------
def rerank(
    query: str,
    candidates: list[tuple[int, float]],
    chunks: list[dict],
    top_k: int = DEFAULT_TOP_K,
    *,
    reranker_fn: "RerankerFn | None" = None,
) -> list[tuple[int, float]]:
    """Rank candidates: dedup → zerank-2 cross-encoder rerank → truncate.

    STORY-GBA-F2.2 — the previous body was dedup+truncate only ("RRF scores
    are already high quality", ZERO cross-encoder). A real cross-encoder
    (zerank-2) now reorders the deduped candidates BEFORE truncation, via
    ``apply_reranker`` (ported from gbrain rerank.ts, SHA 4ee530f).

    Pipeline position (CRITICAL — RNF-1): this runs at the chunk-ranking stage,
    strictly BEFORE the HHEM gate. The HHEM gate is a separate, later stage
    (``rag/pipeline.py::verify`` → ``hhem_gate.check_response``) operating on
    the GENERATED response, not on chunk ordering. This function never touches
    it; the gate remains the final grounding check.

    Order of operations:
      1. ``deduplicate_results`` — 4-layer dedup (unchanged) BEFORE truncation
         so we don't lose unique results.
      2. ``apply_reranker`` — zerank-2 reorders the top candidates; the
         recall-preserving tail keeps RRF order; fail-open to RRF on any error.
      3. truncate to ``top_k``.

    Args:
        query: The search query
        candidates: [(doc_index, rrf_score), ...]
        chunks: All chunks (for text access)
        top_k: Number of results to return
        reranker_fn: test seam forwarded to ``apply_reranker``; production
            NEVER sets this (defaults to the zerank-2 client, which fail-opens
            to RRF order when no API key is configured).

    Returns: [(doc_index, score), ...] top_k deduplicated, reranked results
    """
    if not candidates:
        return []

    # 1. Deduplicate before reranking/truncation so we don't lose unique results.
    deduped = deduplicate_results(candidates, chunks)

    # 2. Cross-encoder rerank (zerank-2) — DELIBERATELY GATED (STORY-GBA-F2.5).
    #    The flag gates the CALL to the reranker, not the algorithm. When the
    #    reranker is OFF (kill-switch, or no API key), we skip ``apply_reranker``
    #    entirely and the result is the deduped RRF order — IDENTICAL to the
    #    pre-F2.2 baseline (legacy dedup+truncate). When ON, the zerank-2
    #    cross-encoder reorders with the recall-preserving tail + fail-open.
    #
    #    Seam override: an explicit ``reranker_fn`` (test injection) ALWAYS
    #    exercises the rerank path — the deterministic stub/seam IS the unit
    #    under test and must not be silenced by the env gate. Production NEVER
    #    sets ``reranker_fn``, so production goes through ``reranker_enabled()``.
    if reranker_fn is not None or reranker_enabled():
        reranked = apply_reranker(query, deduped, chunks, reranker_fn=reranker_fn)
    else:
        reranked = deduped  # reranker OFF ⇒ baseline RRF order, no upstream call

    # 3. Truncate to top_k (AFTER reranking so the best chunks survive the cut).
    return reranked[:top_k]


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
    bucket: str = "external",
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

    # -- Primary: pgvector RRF (S5) --
    rrf_results = _try_rrf_retrieve(query, bucket=bucket, top_k=top_k)
    if rrf_results:
        latency = (time.time() - t0) * 1000
        results = [
            QueryResult(
                {
                    "chunk_id": r.chunk_id,
                    "text": r.text,
                    "source_file": r.source_path,
                    "person": r.person,
                    "domain": "",
                    "section": r.section,
                    "bucket": r.bucket,
                },
                r.score,
                rank + 1,
            )
            for rank, r in enumerate(rrf_results)
        ]
        if use_strategic_order:
            ranked = [(i, r.score) for i, r in enumerate(rrf_results)]
            ranked = strategic_order(ranked)
            results = [results[i] for i, _ in ranked if i < len(results)]
        return {
            "query": query,
            "results": [r.to_dict() for r in results],
            "total_candidates": len(rrf_results),
            "pipeline": {"backend": "pgvector_rrf", "bucket": bucket, "rrf_k": 60},
            "latency_ms": round(latency, 1),
        }

    # -- Fallback: local JSON index (bucket-scoped) --
    # STORY-RAG-BUSINESS-BUCKET-ROUTING: load the index for the REQUESTED bucket,
    # not the external-default singleton. Before this fix, get_index() always
    # loaded RAG_INDEX (external), so bucket="business"/"personal" queries on the
    # local path silently returned external content. An explicitly injected
    # ``index`` (tests) still wins.
    idx = index or get_index_for_bucket(bucket)

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

    # Resolve full chunk texts from the index so we get complete content,
    # not just the 200-char text_preview stored in QueryResult.to_dict().
    idx = index or get_index()
    chunk_lookup: dict[str, str] = {}
    if idx and idx.built:
        for chunk in idx.chunks:
            cid = chunk.get("chunk_id", "")
            if cid:
                chunk_lookup[cid] = chunk.get("text", "")

    context_parts = []
    sources = []
    total_chars = 0
    char_limit = max_tokens * 4  # Approximate

    for r in result["results"]:
        chunk_id = r.get("chunk_id", "")
        # Use full text from index; fall back to preview if index unavailable
        chunk_text = chunk_lookup.get(chunk_id, "") or r.get("text_preview", "")

        if total_chars + len(chunk_text) > char_limit:
            break

        citation = f"[RAG:{chunk_id}]"
        context_parts.append(f"{citation} {chunk_text}")
        sources.append(
            {
                "chunk_id": chunk_id,
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
