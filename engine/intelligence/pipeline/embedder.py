"""C-18 shim (2026-05-12): adapter for orchestrate.py process-batch.

orchestrate.py imports ``embed_chunks`` from
``engine.intelligence.pipeline.embedder`` — actual embedder lives in
``services/local-rag/embedder.py`` (Ollama-based) with a different signature.

This shim provides ``embed_chunks(chunks)`` using the canonical OpenAI
text-embedding-3-large @ 1536d path (per the post-compare architecture
decisions in CLAUDE.md). Falls back to Ollama via services/local-rag if
OPENAI_API_KEY is missing.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from engine.intelligence.pipeline.embed_retry import (
    MAX_EMBED_RETRIES,
    compute_retry_delay,
    extract_retry_after,
    is_rate_limit_error,
)

logger = logging.getLogger("pipeline.embedder")


class EmbeddingFailedError(RuntimeError):
    """Raised when embedding generation fails TOTALLY (no chunk got a vector).

    STORY-GBA-W2.1 — fixes the silent-degrade idempotency hole. Previously a
    total embedding failure returned the chunks unmodified (``return chunks``),
    which let ``cmd_process_batch``'s ``pipeline_transaction`` commit a batch
    with zero embeddings. The ingestion guard had already registered the
    ``content_hash`` (at orchestrate.py:812, BEFORE the transaction), so every
    re-run saw DUPLICATE and skipped — the document was registered but stayed
    permanently un-embedded.

    By raising on total failure, the exception escapes the ``with
    pipeline_transaction(...)`` block (orchestrate.py:1824), triggering a real
    rollback instead of a silent commit. The caller surfaces ``rolled_back=True``.

    Note (scope boundary): un-registering the already-written content_hash is
    NOT in this story's scope — that registry write happens at Phase 0, outside
    the transaction. W2.1 closes the embedder→transaction half of the hole.
    """


def _load_openai_key() -> str | None:
    """Load OPENAI_API_KEY from env or .env file."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    os.environ["OPENAI_API_KEY"] = val
                    return val
    return None


def _embed_via_openai_with_retries(
    client: Any,
    texts: list[str],
    *,
    batch_size: int = 100,
    sleep: Any = None,
) -> list[list[float]]:
    """Embed ``texts`` via the OpenAI SDK with a 5-attempt 429 backoff loop.

    STORY-GBA-W2.2 — ports the resilience the rebuild path already has
    (``rag/hybrid_index.py::_embed_texts``, 5 retries) to the INGESTION path,
    augmented with ±30% jitter and ``Retry-After`` floor (gbrain
    ``embedBatchWithBackoff`` @ 4ee530f). The delay math is shared via
    ``embed_retry.compute_retry_delay`` (DRY); only the loop form lives here,
    because ingestion must fail LOUD on exhaust (the caller re-raises as
    ``EmbeddingFailedError``) whereas the rebuild loop fails open (zero vectors).

    Each batch of up to ``batch_size`` texts gets up to ``MAX_EMBED_RETRIES``
    attempts. A non-429 error aborts immediately (no point retrying a bad key /
    dim mismatch). A 429 that survives all attempts re-raises, which bubbles up
    to ``embed_chunks``'s OpenAI ``except`` → Ollama fallback → total-failure
    raise (W2.1).

    ``sleep`` is injectable so tests assert the computed delays without sleeping.

    Returns the embeddings aligned 1:1 with ``texts``. Raises on unrecoverable
    error (caller catches and degrades / raises per W2.1).
    """
    # Resolve sleep at call time (not as a bound default) so a test patching
    # ``embedder.time.sleep`` is honored even via the production call site.
    if sleep is None:
        sleep = time.sleep
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        last_exc: Exception | None = None
        for attempt in range(MAX_EMBED_RETRIES):
            try:
                resp = client.embeddings.create(
                    model="text-embedding-3-large",
                    input=batch,
                    dimensions=1536,
                )
                all_embeddings.extend([d.embedding for d in resp.data])
                last_exc = None
                break
            except Exception as e:
                last_exc = e
                # Non-429 → permanent; don't waste the remaining attempts.
                if not is_rate_limit_error(e):
                    raise
                # 429 on the final attempt → exhausted; re-raise to the caller.
                if attempt >= MAX_EMBED_RETRIES - 1:
                    raise
                retry_after = extract_retry_after(e)
                delay = compute_retry_delay(attempt, retry_after=retry_after)
                logger.warning(
                    "OpenAI embed rate-limited (429), retrying in %.2fs "
                    "(attempt %d/%d, retry_after=%s)",
                    delay,
                    attempt + 1,
                    MAX_EMBED_RETRIES,
                    retry_after,
                )
                sleep(delay)
        if last_exc is not None:  # pragma: no cover — loop re-raises before here
            raise last_exc
    return all_embeddings


# ---------------------------------------------------------------------------
# STORY-GBA-W2.3 — content_sha reuse on re-ingest
# ---------------------------------------------------------------------------
# Expected OpenAI text-embedding-3-large dimension. Mirrors VectorIndex.dim's
# 1536 invariant used by build_incremental's reuse-eligibility guard — a cached
# vector that is not a 1536-float list is a MISS, not a reuse (don't poison).
_EMBED_DIM = 1536


def _content_sha(text: str) -> str:
    """Canonical content-identity key — REUSE of ``chunker.content_sha``.

    The same pure ``sha256(text[:8000])[:16]`` the rebuild's incremental path and
    the on-disk chunks.json use, so an ingestion-side hit matches a rebuild-side
    cached vector exactly. Imported lazily to avoid a heavy chunker import on the
    embedder's hot path when there is nothing to reuse.
    """
    from engine.intelligence.rag.chunker import content_sha

    return content_sha(text)


def _load_prior_map_for_chunks(
    chunks: list[dict[str, Any]],
) -> dict[str, list[float]]:
    """Load the prior {content_sha -> vector} map for the chunks' bucket.

    REUSE of the rebuild loader: delegates to
    ``hybrid_index.load_prior_vector_map_for_bucket`` (which itself delegates to
    the unchanged ``HybridIndex._load_prior_vector_map``). No second source of
    truth for vectors lives here.

    The bucket is read from the chunk dicts (Art. XIII isolation field, always set
    by ``Chunk.to_dict``); we default to ``external`` when absent. Any failure to
    load (missing index, import error) degrades to an empty map => embed
    everything (pre-W2.3 behavior), so reuse is a pure optimization that can never
    break ingestion.
    """
    bucket = "external"
    for c in chunks:
        b = c.get("bucket")
        if b:
            bucket = b
            break
    try:
        from engine.intelligence.rag.hybrid_index import (
            load_prior_vector_map_for_bucket,
        )

        return load_prior_vector_map_for_bucket(bucket)
    except Exception as e:  # pragma: no cover — defensive; reuse is best-effort
        logger.warning(
            "W2.3 prior-map load failed (%s); embedding all chunks", type(e).__name__
        )
        return {}


def _reuse_partition(
    texts: list[str], prior_map: dict[str, list[float]]
) -> tuple[list[int], list[int]]:
    """Partition chunk indices into (reuse, to_embed) by content_sha.

    A position is REUSE iff its ``content_sha`` is in ``prior_map`` AND the cached
    vector passes the 1536d guard (mirrors ``build_incremental._reusable``); every
    other position is a MISS that must be embedded via the W2.2 resilient path.
    Order within each list follows the original chunk order.
    """
    reuse_idx: list[int] = []
    to_embed_idx: list[int] = []
    for i, text in enumerate(texts):
        vec = prior_map.get(_content_sha(text))
        if isinstance(vec, list) and len(vec) == _EMBED_DIM:
            reuse_idx.append(i)
        else:
            to_embed_idx.append(i)
    return reuse_idx, to_embed_idx


def embed_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate embeddings for a list of chunk dicts.

    Args:
        chunks: List of dicts with at least a ``text`` key (or content/body fallback).

    Returns:
        Same list with each chunk augmented with ``embedding`` (list[float]) and
        ``embedding_model`` keys. Original keys preserved.

    Behavior:
        - Primary: OpenAI text-embedding-3-large @ 1536d (canonical per architecture),
          wrapped in a 5-attempt 429 backoff loop with ±30% jitter and Retry-After
          floor (STORY-GBA-W2.2). Transient rate-limits no longer drop ingestion on
          the first retry the way the old SDK ``max_retries=2`` shim did.
        - Fallback: Ollama via services/local-rag/embedder.py
        - On TOTAL failure (no path produced any vector, incl. 429 surviving all
          5 attempts): raises
          :class:`EmbeddingFailedError` so the caller's pipeline_transaction
          rolls back instead of committing un-embedded chunks (STORY-GBA-W2.1).

    Raises:
        EmbeddingFailedError: when every embedding path fails and no chunk
            received an embedding.
    """
    if not chunks:
        return []

    texts: list[str] = []
    for c in chunks:
        text = c.get("text") or c.get("content") or c.get("body") or ""
        texts.append(text)

    # STORY-GBA-W2.3 — REUSE by content_sha before any API call.
    # Re-ingesting an unchanged document must NOT re-embed: we consult the SAME
    # prior {content_sha -> vector} map the rebuild's incremental path uses
    # (rag/hybrid_index.py:548 -> _load_prior_vector_map) and reuse every hit,
    # embedding ONLY the misses (new/changed chunks) via the W2.2 resilient path.
    #
    # Signature quarantine (STORY-GBA-W2.4): the model:dim hit criterion is
    # enforced UPSTREAM, inside _load_prior_vector_map (artifact granularity, D2).
    # When the artifact's stored signature differs from the running config's
    # (model or dim swap), or the artifact is legacy/signature-less, that loader
    # returns {} — so the prior_map we receive here is ALREADY filtered to the
    # current embedding space. The partition below therefore keeps its W2.3 shape
    # (content_sha + 1536d guard): an empty prior_map forces a full re-embed,
    # which is exactly the "swap → re-embed all" behavior W2.4 requires, with no
    # second signature check duplicated on the ingestion side.
    prior_map = _load_prior_map_for_chunks(chunks)
    reuse_idx, to_embed_idx = _reuse_partition(texts, prior_map)

    if reuse_idx and not to_embed_idx:
        # Full reuse — zero API calls. Stamp every chunk from the prior map.
        for i in reuse_idx:
            chunks[i]["embedding"] = prior_map[_content_sha(texts[i])]
            chunks[i]["embedding_model"] = "text-embedding-3-large@1536d"
        logger.info(
            "Reused %d/%d chunk embeddings by content_sha (0 API calls)",
            len(reuse_idx),
            len(chunks),
        )
        return chunks

    # Apply reuse hits up-front; only the misses go to the embedding paths below.
    for i in reuse_idx:
        chunks[i]["embedding"] = prior_map[_content_sha(texts[i])]
        chunks[i]["embedding_model"] = "text-embedding-3-large@1536d"
    if reuse_idx:
        logger.info(
            "Reused %d/%d chunk embeddings by content_sha; embedding %d new/changed",
            len(reuse_idx),
            len(chunks),
            len(to_embed_idx),
        )

    miss_texts = [texts[i] for i in to_embed_idx]

    # Primary: OpenAI
    api_key = _load_openai_key()
    if api_key:
        try:
            from openai import OpenAI

            # MCE-2.1 AC7: explicit timeout so a hang on the SSL socket (~6min
            # observed in AC7 run 2) fails fast instead of stalling the pipeline.
            #
            # STORY-GBA-W2.2: max_retries=0 — the SDK's built-in 2-retry stack is
            # DISABLED so this wrapper's 5-attempt 429 loop is the single source
            # of truth (gbrain D4a). Without this, the SDK's 2 retries would
            # MULTIPLY against our 5 (10+ effective attempts) and the SDK's short
            # ~4s backoff window would mask the per-batch retry timing we control.
            client = OpenAI(api_key=api_key, timeout=60.0, max_retries=0)

            miss_embeddings = _embed_via_openai_with_retries(client, miss_texts)

            # H3 (CodeRabbit PR34): guard the 1:1 contract before the zip.
            # OpenAI returns resp.data 1:1 with input by contract, but a
            # partial/short response would make zip() truncate silently — some
            # to_embed_idx chunks would keep no "embedding" yet still commit,
            # violating the W2.1 invariant. Raise the typed error so the
            # exception escapes pipeline_transaction and forces a rollback.
            if len(miss_embeddings) != len(miss_texts):
                raise EmbeddingFailedError(
                    f"OpenAI returned {len(miss_embeddings)} embeddings for "
                    f"{len(miss_texts)} input(s) — count mismatch, refusing to "
                    "commit misaligned vectors (W2.1)"
                )

            for i, emb in zip(to_embed_idx, miss_embeddings):
                chunks[i]["embedding"] = emb
                chunks[i]["embedding_model"] = "text-embedding-3-large@1536d"
            logger.info(
                f"Embedded {len(to_embed_idx)} chunks via OpenAI text-embedding-3-large"
            )
            return chunks
        except ImportError:
            logger.warning("openai package not installed; trying Ollama fallback")
        except Exception as e:
            logger.error(f"OpenAI embed failed: {type(e).__name__}: {str(e)[:200]}")

    # Fallback: services/local-rag/embedder
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "services" / "local-rag"))
        from embedder import get_embeddings_batch  # type: ignore

        miss_embeddings = get_embeddings_batch(miss_texts)
        # H3 (CodeRabbit PR34): same 1:1 guard on the Ollama fallback. This is
        # the LAST path before ``return chunks`` — a short batch here would zip-
        # truncate and commit un-embedded chunks (the residual W2.1 hole). The
        # raise is re-caught below as an Exception and surfaces via the typed
        # total-failure raise, so a mismatch never commits misaligned vectors.
        if len(miss_embeddings) != len(miss_texts):
            raise EmbeddingFailedError(
                f"Ollama returned {len(miss_embeddings)} embeddings for "
                f"{len(miss_texts)} input(s) — count mismatch, refusing to "
                "commit misaligned vectors (W2.1)"
            )
        for i, emb in zip(to_embed_idx, miss_embeddings):
            chunks[i]["embedding"] = emb
            chunks[i]["embedding_model"] = "ollama-local"
        logger.info(f"Embedded {len(to_embed_idx)} chunks via Ollama (fallback)")
        return chunks
    except Exception as e:
        logger.error(f"Ollama fallback also failed: {type(e).__name__}: {e}")

    # STORY-GBA-W2.1: TOTAL failure for the chunks that still NEEDED embedding.
    # Previously this did ``return chunks`` (silent degrade) — chunks without
    # embeddings flowed back into cmd_process_batch's pipeline_transaction and
    # committed, leaving a registered-but-un-embedded document. Now we RAISE so
    # the exception escapes the transaction and forces a rollback. Re-run then
    # re-processes instead of seeing a half-committed batch.
    #
    # W2.3 interaction: content_sha reuse hits (``reuse_idx``) were already
    # stamped above, so a fully-reused batch returned earlier and never reaches
    # here. We only get here when there were MISSES (``to_embed_idx``) and every
    # embedding path failed for them — i.e. some chunks would remain un-embedded.
    # That still violates the W2.1 invariant (no un-embedded chunk may commit),
    # so we raise. The count reported is the miss count, not the whole batch.
    #
    # Scope (W2.2): PARTIAL failure — where some misses got embeddings via a
    # successful path above — keeps the current controlled-degrade behavior
    # (those paths already ``return chunks`` with the embeddings they got).
    msg = (
        f"Total embedding failure: all paths exhausted for {len(to_embed_idx)} "
        f"new/changed chunk(s) ({len(reuse_idx)} reused by content_sha) "
        "(OpenAI + Ollama fallback both failed or unavailable)"
    )
    logger.error(msg)
    raise EmbeddingFailedError(msg)
