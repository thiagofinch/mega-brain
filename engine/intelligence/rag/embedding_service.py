"""Embedding service with caching for Mega Brain RAG.

Provides a cached interface for generating text embeddings. ALL generation is
delegated to the canonical embedding gateway (``embedding_config``) — there is
ONE provider, model, and dimension across the whole RAG layer. The cache only
prevents re-embedding identical texts; it never changes the vector space.

STORY-GBA-F0.2: this service previously owned its own provider ladder
(voyage -> local sentence-transformers(384d) -> dummy(64d)). That silent
degrade put embeddings in a different space than the OpenAI/1536 documents
in pgvector, corrupting cosine. The ladder is removed; the service now routes
every embedding through ``embedding_config.embed_*`` (fail-loud, single space).

Version: 2.0.0 (gateway-consolidated)
Date: 2026-06-20
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .embedding_config import embed_query, embed_texts, get_embedding_config

DEFAULT_CACHE_DIR = Path(".data/embedding_cache")


class EmbeddingCache:
    """File-based embedding cache using content hash as key.

    Each embedding is stored as a JSON file named by the SHA-256 hash
    of (model + text).  This ensures identical texts embedded with
    different models get separate cache entries.
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self._dir = Path(cache_dir or DEFAULT_CACHE_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0

    def _key(self, text: str, model: str) -> str:
        """Generate cache key from text + model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, text: str, model: str = "default") -> list[float] | None:
        """Get cached embedding, or None if not cached."""
        key = self._key(text, model)
        cache_file = self._dir / f"{key}.json"
        if cache_file.exists():
            self._hits += 1
            return json.loads(cache_file.read_text(encoding="utf-8"))
        self._misses += 1
        return None

    def put(self, text: str, embedding: list[float], model: str = "default") -> None:
        """Store embedding in cache."""
        key = self._key(text, model)
        cache_file = self._dir / f"{key}.json"
        cache_file.write_text(json.dumps(embedding), encoding="utf-8")

    def stats(self) -> dict:
        """Return cache statistics."""
        cached_files = len(list(self._dir.glob("*.json")))
        total = self._hits + self._misses
        return {
            "cached_embeddings": cached_files,
            "session_hits": self._hits,
            "session_misses": self._misses,
            "hit_rate": self._hits / max(1, total),
            "cache_dir": str(self._dir),
        }

    def clear(self) -> int:
        """Clear all cached embeddings. Returns count deleted."""
        count = 0
        for f in self._dir.glob("*.json"):
            f.unlink()
            count += 1
        return count


class EmbeddingService:
    """Unified embedding service with cache and provider fallback.

    Usage::

        service = EmbeddingService()
        embedding = service.embed("some text")
        embeddings = service.embed_batch(["text1", "text2", "text3"])
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        provider: str = "auto",
    ) -> None:
        """Initialise embedding service.

        Args:
            cache_dir: Directory for embedding cache.
            provider: Retained for backward-compatible call signatures only.
                      The active provider is ALWAYS resolved by the canonical
                      gateway (``embedding_config``); this argument no longer
                      selects a divergent provider ladder (STORY-GBA-F0.2).
        """
        self.cache = EmbeddingCache(cache_dir)
        self._provider = provider
        self._model_name = "unknown"
        self._dimension = 0
        self._initialised = False

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------
    def _init_provider(self) -> None:
        """Resolve model/dim from the canonical gateway (single SOT)."""
        if self._initialised:
            return
        self._initialised = True

        emb_cfg = get_embedding_config()
        self._model_name = emb_cfg["model"]
        self._dimension = emb_cfg["dimensions"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Returns cached embedding if available.
        """
        self._init_provider()

        cached = self.cache.get(text, self._model_name)
        if cached is not None:
            return cached

        embedding = self._generate(text)
        self.cache.put(text, embedding, self._model_name)
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Uses cache for already-embedded texts, generates only new ones.
        """
        self._init_provider()

        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            cached = self.cache.get(text, self._model_name)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            new_embeddings = self._generate_batch(uncached_texts)
            for idx, embedding in zip(uncached_indices, new_embeddings):
                results[idx] = embedding
                self.cache.put(texts[idx], embedding, self._model_name)

        return results  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal generation (delegated to the canonical gateway)
    # ------------------------------------------------------------------
    def _generate(self, text: str) -> list[float]:
        """Generate a single embedding via the canonical gateway."""
        return embed_query(text)

    def _generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate a batch of embeddings via the canonical gateway."""
        return embed_texts(texts, input_type="document")

    # ------------------------------------------------------------------
    # Properties & info
    # ------------------------------------------------------------------
    @property
    def model_name(self) -> str:
        self._init_provider()
        return self._model_name

    @property
    def dimension(self) -> int:
        self._init_provider()
        return self._dimension

    def info(self) -> dict:
        """Return service info including provider and cache stats."""
        self._init_provider()
        return {
            "provider": self._provider,
            "model": self._model_name,
            "dimension": self._dimension,
            "cache": self.cache.stats(),
        }
