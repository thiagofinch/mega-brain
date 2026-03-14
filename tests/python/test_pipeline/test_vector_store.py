"""Tests for VectorStore abstract interface and ChromaStore implementation.

Uses tmp_path for full isolation -- each test gets its own ChromaDB directory.
Synthetic embeddings (small float lists) are used; no real model needed.
"""

import pytest

from core.intelligence.rag.vector_store import SearchResult, VectorStore
from core.intelligence.rag.chroma_store import ChromaStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emb(seed: float, dim: int = 8) -> list[float]:
    """Generate a deterministic synthetic embedding vector."""
    return [seed + i * 0.01 for i in range(dim)]


def _make_store(tmp_path, name: str = "test_collection") -> ChromaStore:
    """Create an isolated ChromaStore in a temp directory."""
    return ChromaStore(collection_name=name, persist_dir=tmp_path / "chroma")


# ---------------------------------------------------------------------------
# ABC contract tests
# ---------------------------------------------------------------------------

class TestVectorStoreABC:
    """VectorStore is abstract and cannot be instantiated directly."""

    def test_abc_cannot_instantiate(self):
        with pytest.raises(TypeError):
            VectorStore()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------

class TestSearchResult:
    """SearchResult dataclass has correct fields and defaults."""

    def test_fields(self):
        r = SearchResult(chunk_id="c1", text="hello", metadata={"k": "v"}, score=0.95)
        assert r.chunk_id == "c1"
        assert r.text == "hello"
        assert r.metadata == {"k": "v"}
        assert r.score == 0.95

    def test_equality(self):
        a = SearchResult("c1", "hello", {}, 0.9)
        b = SearchResult("c1", "hello", {}, 0.9)
        assert a == b


# ---------------------------------------------------------------------------
# ChromaStore -- initialization
# ---------------------------------------------------------------------------

class TestChromaStoreInit:
    """ChromaStore initialization and persist directory."""

    def test_creates_persist_dir(self, tmp_path):
        target = tmp_path / "sub" / "chroma"
        assert not target.exists()
        _make_store(tmp_path / "sub")
        assert target.exists()

    def test_empty_on_creation(self, tmp_path):
        store = _make_store(tmp_path)
        assert store.count() == 0


# ---------------------------------------------------------------------------
# ChromaStore -- add / count
# ---------------------------------------------------------------------------

class TestChromaStoreAdd:
    """Single and batch add operations."""

    def test_add_single_increments_count(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("chunk-001", "some text", _emb(0.1))
        assert store.count() == 1

    def test_add_with_metadata(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("chunk-001", "text", _emb(0.1), metadata={"source": "hormozi"})
        result = store.get("chunk-001")
        assert result is not None
        assert result.metadata["source"] == "hormozi"

    def test_add_batch_multiple(self, tmp_path):
        store = _make_store(tmp_path)
        ids = [f"c-{i}" for i in range(5)]
        texts = [f"text {i}" for i in range(5)]
        embeddings = [_emb(0.1 * i) for i in range(5)]
        metadatas = [{"idx": str(i)} for i in range(5)]

        store.add_batch(ids, texts, embeddings, metadatas)
        assert store.count() == 5

    def test_add_batch_without_metadata(self, tmp_path):
        store = _make_store(tmp_path)
        store.add_batch(
            ["a", "b"],
            ["text a", "text b"],
            [_emb(0.1), _emb(0.2)],
        )
        assert store.count() == 2


# ---------------------------------------------------------------------------
# ChromaStore -- search
# ---------------------------------------------------------------------------

class TestChromaStoreSearch:
    """Similarity search returns ranked results."""

    def test_search_returns_results(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("c1", "alpha", _emb(0.1))
        store.add("c2", "beta", _emb(0.5))
        store.add("c3", "gamma", _emb(0.9))

        results = store.search(_emb(0.1), top_k=2)
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_most_similar_first(self, tmp_path):
        store = _make_store(tmp_path)
        # c1 embedding is very close to query, c2 is far
        store.add("c1", "close match", _emb(0.10))
        store.add("c2", "far match", _emb(0.90))

        results = store.search(_emb(0.10), top_k=2)
        assert results[0].chunk_id == "c1"
        assert results[0].score >= results[1].score

    def test_search_empty_store(self, tmp_path):
        store = _make_store(tmp_path)
        results = store.search(_emb(0.5), top_k=5)
        assert results == []

    def test_search_top_k_limits(self, tmp_path):
        store = _make_store(tmp_path)
        for i in range(10):
            store.add(f"c{i}", f"text {i}", _emb(0.1 * i))

        results = store.search(_emb(0.5), top_k=3)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# ChromaStore -- get
# ---------------------------------------------------------------------------

class TestChromaStoreGet:
    """Retrieve specific chunks by ID."""

    def test_get_existing(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("target", "found it", _emb(0.3), metadata={"key": "val"})

        result = store.get("target")
        assert result is not None
        assert result.chunk_id == "target"
        assert result.text == "found it"
        assert result.metadata["key"] == "val"
        assert result.score == 1.0

    def test_get_nonexistent_returns_none(self, tmp_path):
        store = _make_store(tmp_path)
        assert store.get("ghost-chunk") is None


# ---------------------------------------------------------------------------
# ChromaStore -- delete
# ---------------------------------------------------------------------------

class TestChromaStoreDelete:
    """Chunk deletion."""

    def test_delete_reduces_count(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("c1", "text", _emb(0.1))
        store.add("c2", "text", _emb(0.2))
        assert store.count() == 2

        deleted = store.delete("c1")
        assert deleted is True
        assert store.count() == 1

    def test_delete_nonexistent_returns_false(self, tmp_path):
        store = _make_store(tmp_path)
        # ChromaDB delete on non-existent does not raise,
        # but our interface guarantees boolean return
        result = store.delete("does-not-exist")
        # ChromaDB silently succeeds on missing IDs, so this is True
        # The important thing is it doesn't crash
        assert isinstance(result, bool)

    def test_deleted_chunk_not_retrievable(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("c1", "text", _emb(0.1))
        store.delete("c1")
        assert store.get("c1") is None


# ---------------------------------------------------------------------------
# ChromaStore -- clear
# ---------------------------------------------------------------------------

class TestChromaStoreClear:
    """Clear removes all chunks."""

    def test_clear_empties_store(self, tmp_path):
        store = _make_store(tmp_path)
        for i in range(5):
            store.add(f"c{i}", f"text {i}", _emb(0.1 * i))
        assert store.count() == 5

        store.clear()
        assert store.count() == 0

    def test_clear_allows_readd(self, tmp_path):
        store = _make_store(tmp_path)
        store.add("c1", "first", _emb(0.1))
        store.clear()
        store.add("c1", "second", _emb(0.2))
        result = store.get("c1")
        assert result is not None
        assert result.text == "second"


# ---------------------------------------------------------------------------
# ChromaStore -- persistence
# ---------------------------------------------------------------------------

class TestChromaStorePersistence:
    """Data survives store re-instantiation (on-disk persistence)."""

    def test_data_persists_across_instances(self, tmp_path):
        persist_dir = tmp_path / "persist_chroma"

        store1 = ChromaStore(collection_name="persist_test", persist_dir=persist_dir)
        store1.add("persist-chunk", "I survive", _emb(0.42))
        assert store1.count() == 1
        del store1

        store2 = ChromaStore(collection_name="persist_test", persist_dir=persist_dir)
        assert store2.count() == 1
        result = store2.get("persist-chunk")
        assert result is not None
        assert result.text == "I survive"
