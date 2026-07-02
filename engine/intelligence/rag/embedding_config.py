"""
engine/intelligence/rag/embedding_config.py -- Embedding Gateway (single SOT)
=================================================================================
THE single source of truth AND the single entry point for every embedding the
RAG layer produces. Provider, model, and dimension are resolved here once; every
call-site (documents AND queries) routes through ``embed_texts`` / ``embed_query``
so a query can NEVER be embedded in a different vector space than its documents.

Why a gateway (STORY-GBA-F0.2 / GAP-012):
  Before this story the mega-brain had 3 divergent embedding paths:
    1. hybrid_index._openai_embed   -> OpenAI/1536   (correct)
    2. rrf_retrieval._embed_query   -> voyage-4      (DIVERGENT — wrong space)
    3. embedding_service            -> voyage/local(384)/dummy(64)  (silent degrade)
  A query embedded by path 2/3 lands in a different vector space than the docs
  embedded by path 1. pgvector's cosine then silently compares incompatible
  spaces and corrupts ranking with no error. The fix (ported from gbrain's AI
  gateway, SHA 4ee530f: src/core/ai/gateway.ts + src/core/ai/defaults.ts) is a
  single ``embed`` seam: every call resolves model+dim from this module, and the
  provider response dim is asserted against the resolved dim (fail-loud, never
  silent-degrade — mirrors gbrain's embedding-dim-check.ts).

Architectural decision (NOT reopened by this story): Roundtable
RT-2026-04-16-001 fixed the canonical provider as OpenAI text-embedding-3-large
with 1536 dimensions. This matches the ADR post-compare and the active
OPENAI_API_KEY, and resolves the latent 1024(voyage)<->1536(openai) runtime
mismatch surfaced by the F0.1 runtime probe.

Defaults are override-able via environment variables (resolved through
engine.config.get_config):
  - EMBEDDING_PROVIDER   (default: "openai")
  - EMBEDDING_MODEL      (default: "text-embedding-3-large")
  - EMBEDDING_DIMENSIONS (default: "1536")

Story: W1-001.9 (config) / STORY-GBA-F0.2 (gateway consolidation)
DELTA: #45
"""

from __future__ import annotations

from engine.config import get_config

# ---------------------------------------------------------------------------
# Canonical defaults (Roundtable RT-2026-04-16-001)
# ---------------------------------------------------------------------------
PROVIDER: str = "openai"
MODEL: str = "text-embedding-3-large"
DIMENSIONS: int = 1536

# Max chars sent per text (matches hybrid_index query/doc truncation).
MAX_CHARS: int = 8000
# Max items per OpenAI Embeddings API call.
OPENAI_BATCH_SIZE: int = 100


# ---------------------------------------------------------------------------
# Config accessors (gbrain pattern: getEmbeddingModel/getEmbeddingDimensions)
# ---------------------------------------------------------------------------


def get_embedding_config() -> dict:
    """Return the active embedding configuration as a dict.

    Values are resolved through get_config(), meaning environment
    variables and .env entries take precedence over the module-level
    constants. This allows tests and alternative deployments to
    override without touching code.

    Returns:
        dict with keys ``provider``, ``model``, ``dimensions``.
    """
    return {
        "provider": get_config("EMBEDDING_PROVIDER", default=PROVIDER),
        "model": get_config("EMBEDDING_MODEL", default=MODEL),
        "dimensions": int(get_config("EMBEDDING_DIMENSIONS", default=str(DIMENSIONS))),
    }


def get_embedding_provider() -> str:
    """Resolved embedding provider (gbrain: gateway accessor)."""
    return get_config("EMBEDDING_PROVIDER", default=PROVIDER)


def get_embedding_model() -> str:
    """Resolved embedding model id (gbrain: getEmbeddingModel)."""
    return get_config("EMBEDDING_MODEL", default=MODEL)


def get_embedding_dimensions() -> int:
    """Resolved embedding dimension (gbrain: getEmbeddingDimensions)."""
    return int(get_config("EMBEDDING_DIMENSIONS", default=str(DIMENSIONS)))


def get_embedding_signature() -> str:
    """The canonical ``provider:model:dim`` stamp for the active space.

    Ported from gbrain's model:dim signature (embedding-dim-check.ts). Any two
    embeddings sharing this signature live in the same vector space and are
    cosine-comparable; differing signatures are NOT comparable. Used by the
    characterization test to prove every call-site resolves to one space.
    """
    return f"{get_embedding_provider()}:{get_embedding_model()}:{get_embedding_dimensions()}"


def get_artifact_signature() -> str:
    """The ``model:dim`` provenance stamp written into the embedding artifact.

    STORY-GBA-W2.4 (Decision D2): the artifact-level signature granularity is
    ``model:dim`` (e.g. ``text-embedding-3-large:1536``) — NOT the full
    ``provider:model:dim`` of :func:`get_embedding_signature`. Rationale:

      * The artifact (``vectors.json``) is what the drift quarantine compares
        against the running config. What makes two stored vectors reuse-eligible
        is whether they came from the same MODEL at the same DIMENSION; the
        provider is implied by the model id (``text-embedding-3-large`` is
        unambiguously OpenAI) and adding it would only widen the stamp without
        adding discriminating power for reuse.
      * Keeping the artifact stamp at ``model:dim`` matches gbrain's port-spec
        D2 exactly and keeps the on-disk shape minimal (zero schema change to
        ``content_hashes``; the stamp is a single extra top-level key in
        ``vectors.json``).

    A swap of either the model OR the dimension changes this string, which the
    loader (``_load_prior_vector_map``) reads to decide stale-vs-reusable.
    """
    return f"{get_embedding_model()}:{get_embedding_dimensions()}"


# ---------------------------------------------------------------------------
# Gateway — the single embedding seam (gbrain: gateway.embed / embedOne)
# ---------------------------------------------------------------------------


class EmbeddingConfigError(RuntimeError):
    """Raised when the gateway cannot produce embeddings in the canonical space.

    Fail-loud by design (gbrain embedding-dim-check.ts): a missing API key or a
    provider returning the wrong dimension MUST surface as an error, never a
    silent degrade to a dummy/low-dim vector that corrupts cosine downstream.
    """


def _resolve_openai_api_key() -> str | None:
    """Resolve the OpenAI API key via the canonical config hierarchy."""
    return get_config("OPENAI_API_KEY")


def _openai_embed(texts: list[str], model: str, dimensions: int, api_key: str) -> list[list[float]]:
    """Call the OpenAI Embeddings API; assert returned dim == requested dim.

    Mirrors hybrid_index._openai_embed (the validated gold path): explicitly
    passes ``dimensions`` so text-embedding-3-large emits reduced-dim vectors
    matching the pgvector schema, and raises on any dim mismatch (the
    silent-corruption class this gateway exists to kill).
    """
    import requests

    payload = {"input": texts, "model": model, "dimensions": dimensions}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    resp = requests.post(
        "https://api.openai.com/v1/embeddings",
        json=payload,
        headers=headers,
        timeout=(10, 120),  # (connect, read) — read timeout enforced on TLS keep-alive
    )
    resp.raise_for_status()
    data = resp.json()
    vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
    if vectors and len(vectors[0]) != dimensions:
        raise EmbeddingConfigError(
            f"Provider returned dim={len(vectors[0])} but gateway requested dim={dimensions} "
            f"(signature {get_embedding_signature()}) — refusing to write a vector into the "
            f"wrong space."
        )
    return vectors


def embed_texts(texts: list[str], *, input_type: str = "document") -> list[list[float]]:
    """Embed a batch of texts through the canonical gateway. THE seam.

    Every document/query embedding in the RAG layer routes here, so the
    resolved (model, dim) is identical for both sides of every cosine compare.

    Args:
        texts: Texts to embed. Each is truncated to ``MAX_CHARS``.
        input_type: ``"document"`` or ``"query"`` (kept for provider parity;
            OpenAI text-embedding-3-* does not distinguish, but the parameter
            keeps the seam provider-agnostic and documents caller intent).

    Returns:
        One embedding (list[float] of length ``get_embedding_dimensions()``)
        per input text, in input order.

    Raises:
        EmbeddingConfigError: provider unavailable, unsupported provider, or a
            returned dimension that does not match the resolved space.
    """
    if not texts:
        return []

    provider = get_embedding_provider()
    model = get_embedding_model()
    dimensions = get_embedding_dimensions()
    truncated = [(t or "")[:MAX_CHARS] for t in texts]

    if provider != "openai":
        raise EmbeddingConfigError(
            f"Embedding gateway is configured for provider '{provider}', but only 'openai' "
            f"is supported as the canonical space (signature {get_embedding_signature()}). "
            f"Set EMBEDDING_PROVIDER=openai or extend the gateway deliberately."
        )

    api_key = _resolve_openai_api_key()
    if not api_key:
        raise EmbeddingConfigError(
            "OPENAI_API_KEY is not configured — the embedding gateway refuses to fall back to "
            "a divergent provider/dimension (no silent degrade). Configure the key in .env."
        )

    out: list[list[float]] = []
    for start in range(0, len(truncated), OPENAI_BATCH_SIZE):
        batch = truncated[start : start + OPENAI_BATCH_SIZE]
        out.extend(_openai_embed(batch, model, dimensions, api_key))
    return out


def embed_query(query: str) -> list[float]:
    """Embed a single query string through the canonical gateway.

    Convenience wrapper over ``embed_texts`` (gbrain: embedOne). Guarantees the
    query lands in the SAME space as the documents — the exact bug F0.2 fixes.
    An empty/blank query short-circuits to ``[]`` (no provider call).
    """
    if not query:
        return []
    vectors = embed_texts([query], input_type="query")
    return vectors[0] if vectors else []
