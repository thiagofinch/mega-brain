"""ChromaDB implementation of VectorStore.

Provides persistent local vector storage using ChromaDB. Data is persisted
to disk in .data/chroma/ by default, enabling zero-infrastructure semantic
search that scales to 50K+ chunks.
"""

from __future__ import annotations

from pathlib import Path

from core.intelligence.rag.vector_store import SearchResult, VectorStore
from core.paths import DATA


class ChromaStore(VectorStore):
    """ChromaDB-backed vector store.

    Data persisted locally in .data/chroma/ directory.
    Uses cosine similarity for distance metric.
    """

    def __init__(
        self,
        collection_name: str = "mega_brain",
        persist_dir: str | Path | None = None,
    ):
        try:
            import chromadb
        except ImportError as exc:
            raise ImportError(
                "chromadb required. Install: pip install 'mega-brain[vectordb]'"
            ) from exc

        if persist_dir is None:
            persist_dir = DATA / "chroma"
        persist_dir = Path(persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        chunk_id: str,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Add a single chunk with its embedding."""
        kwargs: dict = {
            "ids": [chunk_id],
            "documents": [text],
            "embeddings": [embedding],
        }
        if metadata:
            kwargs["metadatas"] = [metadata]
        self._collection.add(**kwargs)

    def add_batch(
        self,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add multiple chunks in one operation."""
        kwargs: dict = {
            "ids": chunk_ids,
            "documents": texts,
            "embeddings": embeddings,
        }
        if metadatas:
            kwargs["metadatas"] = metadatas
        self._collection.add(**kwargs)

    def search(self, query_embedding: list[float], top_k: int = 10) -> list[SearchResult]:
        """Search by embedding vector similarity.

        Returns results sorted by descending similarity (highest first).
        Cosine distance is converted to similarity via: score = 1.0 - distance.
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                search_results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        text=results["documents"][0][i] if results["documents"] else "",
                        metadata=(results["metadatas"][0][i] if results["metadatas"] else {}),
                        score=1.0 - results["distances"][0][i],
                    )
                )
        return search_results

    def get(self, chunk_id: str) -> SearchResult | None:
        """Get a specific chunk by ID. Returns None if not found."""
        try:
            result = self._collection.get(ids=[chunk_id], include=["documents", "metadatas"])
            if result["ids"]:
                return SearchResult(
                    chunk_id=chunk_id,
                    text=result["documents"][0] if result["documents"] else "",
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                    score=1.0,
                )
        except Exception:
            pass
        return None

    def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID. Returns True if successful."""
        try:
            self._collection.delete(ids=[chunk_id])
            return True
        except Exception:
            return False

    def count(self) -> int:
        """Return total number of stored chunks."""
        return self._collection.count()

    def clear(self) -> None:
        """Remove all chunks by recreating the collection."""
        collection_name = self._collection.name
        collection_metadata = self._collection.metadata
        self._client.delete_collection(collection_name)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata=collection_metadata,
        )
