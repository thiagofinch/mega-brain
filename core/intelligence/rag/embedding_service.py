"""Embedding service with caching for Mega Brain RAG.

Provides a cached interface for generating text embeddings.
Supports VoyageAI (primary) and local sentence-transformers (fallback).
Cache prevents re-embedding identical texts.

Version: 1.0.0
Date: 2026-03-14
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

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
            provider: ``"voyage"`` | ``"local"`` | ``"auto"``
                      (try voyage first, fall back to local, then dummy).
        """
        self.cache = EmbeddingCache(cache_dir)
        self._provider = provider
        self._model_name = "unknown"
        self._dimension = 0
        self._client: object | None = None
        self._local_model: object | None = None
        self._initialised = False

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------
    def _init_provider(self) -> None:
        """Lazy-initialise the embedding provider."""
        if self._initialised:
            return
        self._initialised = True

        if self._provider in ("voyage", "auto"):
            if self._try_voyage():
                return

        if self._provider in ("local", "auto"):
            if self._try_local():
                return

        # No provider available -- use deterministic dummy embeddings
        self._model_name = "dummy"
        self._dimension = 64

    def _try_voyage(self) -> bool:
        """Attempt to initialise VoyageAI provider."""
        api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            # Try loading from .env
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("VOYAGE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not api_key:
            return False
        try:
            import voyageai  # type: ignore[import-untyped]

            self._client = voyageai.Client(api_key=api_key)
            self._model_name = "voyage-3-lite"
            self._dimension = 512
            return True
        except ImportError:
            return False

    def _try_local(self) -> bool:
        """Attempt to initialise sentence-transformers provider."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._model_name = "all-MiniLM-L6-v2"
            self._dimension = 384
            return True
        except ImportError:
            return False

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
    # Internal generation
    # ------------------------------------------------------------------
    def _generate(self, text: str) -> list[float]:
        """Generate a single embedding via the active provider."""
        if self._client is not None:
            result = self._client.embed([text], model=self._model_name)  # type: ignore[union-attr]
            return result.embeddings[0]  # type: ignore[union-attr]
        if self._local_model is not None:
            return self._local_model.encode(text).tolist()  # type: ignore[union-attr]
        return self._dummy_embed(text)

    def _generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch via the active provider."""
        if self._client is not None:
            result = self._client.embed(texts, model=self._model_name)  # type: ignore[union-attr]
            return result.embeddings  # type: ignore[union-attr]
        if self._local_model is not None:
            return [e.tolist() for e in self._local_model.encode(texts)]  # type: ignore[union-attr]
        return [self._dummy_embed(t) for t in texts]

    def _dummy_embed(self, text: str) -> list[float]:
        """Deterministic dummy embedding for testing without any provider."""
        h = hashlib.md5(text.encode()).hexdigest()
        raw = [int(h[i : i + 2], 16) / 255.0 for i in range(0, min(len(h), self._dimension * 2), 2)]
        # Pad to dimension if hex digest is shorter
        while len(raw) < self._dimension:
            raw.append(0.0)
        return raw[: self._dimension]

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
