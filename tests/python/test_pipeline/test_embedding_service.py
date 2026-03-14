"""Tests for the embedding service with caching.

All tests are OFFLINE -- no real API calls, no real filesystem outside tmp_path.
The EmbeddingService under test always falls through to the ``dummy`` provider
because neither ``voyageai`` nor ``sentence_transformers`` are imported.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.intelligence.rag.embedding_service import EmbeddingCache, EmbeddingService


# ============================================================================
# EmbeddingCache
# ============================================================================


class TestEmbeddingCache:
    """Unit tests for the file-based EmbeddingCache."""

    def test_store_and_retrieve(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        embedding = [0.1, 0.2, 0.3]
        cache.put("hello world", embedding, model="test-model")

        result = cache.get("hello world", model="test-model")
        assert result == embedding

    def test_miss_returns_none(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        result = cache.get("nonexistent text", model="test-model")
        assert result is None

    def test_stats_tracks_hits_and_misses(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        cache.put("cached", [1.0, 2.0], model="m")

        cache.get("cached", model="m")  # hit
        cache.get("cached", model="m")  # hit
        cache.get("not-cached", model="m")  # miss

        stats = cache.stats()
        assert stats["session_hits"] == 2
        assert stats["session_misses"] == 1
        assert stats["cached_embeddings"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_clear_removes_all_cached_files(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        cache.put("a", [1.0], model="m")
        cache.put("b", [2.0], model="m")
        cache.put("c", [3.0], model="m")

        deleted = cache.clear()
        assert deleted == 3
        assert cache.get("a", model="m") is None

    def test_different_models_get_different_keys(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        cache.put("same text", [1.0], model="model-a")
        cache.put("same text", [2.0], model="model-b")

        result_a = cache.get("same text", model="model-a")
        result_b = cache.get("same text", model="model-b")

        assert result_a == [1.0]
        assert result_b == [2.0]

    def test_stats_cached_embeddings_counts_files(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        assert cache.stats()["cached_embeddings"] == 0

        cache.put("x", [0.5], model="m")
        assert cache.stats()["cached_embeddings"] == 1

        cache.put("y", [0.6], model="m")
        assert cache.stats()["cached_embeddings"] == 2

    def test_cache_dir_created_if_missing(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "deep" / "nested" / "cache"
        cache = EmbeddingCache(cache_dir=cache_dir)
        assert cache_dir.exists()
        cache.put("test", [1.0], model="m")
        assert cache.get("test", model="m") == [1.0]


# ============================================================================
# EmbeddingService (dummy provider -- no real API)
# ============================================================================


class TestEmbeddingServiceDummy:
    """Tests with the dummy provider (no voyageai, no sentence-transformers)."""

    def _make_service(self, tmp_path: Path) -> EmbeddingService:
        """Create a service that will always use the dummy provider."""
        # provider="auto" but without voyageai/sentence_transformers installed
        # in CI, falls through to dummy.  We force it for safety:
        svc = EmbeddingService(cache_dir=tmp_path, provider="auto")
        # Force dummy by marking as not-initialised and clearing env
        svc._initialised = False
        svc._client = None
        svc._local_model = None
        svc._model_name = "dummy"
        svc._dimension = 64
        svc._initialised = True
        return svc

    def test_embed_generates_consistent_embeddings(
        self, tmp_path: Path
    ) -> None:
        svc = self._make_service(tmp_path)
        emb1 = svc.embed("hello")
        emb2 = svc.embed("hello")  # cached
        assert emb1 == emb2

    def test_embed_different_texts_produce_different_embeddings(
        self, tmp_path: Path
    ) -> None:
        svc = self._make_service(tmp_path)
        emb1 = svc.embed("text one")
        emb2 = svc.embed("text two")
        assert emb1 != emb2

    def test_embed_caches_on_first_call(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        svc.embed("cache me")

        stats = svc.cache.stats()
        assert stats["session_misses"] == 1  # first call was a miss
        assert stats["cached_embeddings"] == 1

    def test_embed_returns_cache_on_second_call(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        svc.embed("cache me")
        svc.embed("cache me")

        stats = svc.cache.stats()
        assert stats["session_hits"] == 1
        assert stats["session_misses"] == 1

    def test_embed_batch_caches_all_items(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        texts = ["alpha", "beta", "gamma"]
        results = svc.embed_batch(texts)

        assert len(results) == 3
        assert all(len(e) == 64 for e in results)
        assert svc.cache.stats()["cached_embeddings"] == 3

    def test_embed_batch_uses_cache_for_known_items(
        self, tmp_path: Path
    ) -> None:
        svc = self._make_service(tmp_path)
        # Pre-cache one item
        svc.embed("alpha")

        # Now batch -- alpha should be cached, beta/gamma should be new
        results = svc.embed_batch(["alpha", "beta", "gamma"])

        assert len(results) == 3
        stats = svc.cache.stats()
        # alpha: 1 miss (first embed) + 1 hit (batch) = 1 hit
        # beta, gamma: 1 miss each in batch
        assert stats["session_hits"] == 1
        assert stats["session_misses"] == 3  # first alpha + beta + gamma

    def test_info_returns_expected_structure(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        info = svc.info()

        assert "provider" in info
        assert "model" in info
        assert "dimension" in info
        assert "cache" in info
        assert isinstance(info["cache"], dict)
        assert "cached_embeddings" in info["cache"]

    def test_dimension_returns_positive(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        assert svc.dimension > 0

    def test_model_name_returns_string(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        assert isinstance(svc.model_name, str)
        assert len(svc.model_name) > 0

    def test_embed_returns_correct_dimension(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        embedding = svc.embed("dimensional check")
        assert len(embedding) == svc.dimension
        assert all(isinstance(v, float) for v in embedding)

    def test_embed_batch_empty_list(self, tmp_path: Path) -> None:
        svc = self._make_service(tmp_path)
        results = svc.embed_batch([])
        assert results == []
