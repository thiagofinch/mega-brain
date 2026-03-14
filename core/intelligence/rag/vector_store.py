"""Abstract vector store interface for Mega Brain RAG.

Provides a pluggable backend for vector storage and similarity search.
Concrete implementations: ChromaStore (default), with interface for
future FAISS, Qdrant, Weaviate backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """A single search result from vector store."""

    chunk_id: str
    text: str
    metadata: dict
    score: float  # similarity score (higher = more similar)


class VectorStore(ABC):
    """Abstract base class for vector storage backends."""

    @abstractmethod
    def add(
        self,
        chunk_id: str,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Add a single chunk with its embedding."""
        ...

    @abstractmethod
    def add_batch(
        self,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add multiple chunks in one operation."""
        ...

    @abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int = 10
    ) -> list[SearchResult]:
        """Search by embedding vector similarity."""
        ...

    @abstractmethod
    def get(self, chunk_id: str) -> SearchResult | None:
        """Get a specific chunk by ID."""
        ...

    @abstractmethod
    def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored chunks."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all chunks."""
        ...
