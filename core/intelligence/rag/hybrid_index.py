#!/usr/bin/env python3
"""
HYBRID INDEX - Phase 3.2
=========================
Dual-strategy indexing: vector (voyage-context-3) + BM25.
Local JSON storage with pgvector adapter interface for production.

Versao: 1.0.0
Data: 2026-03-01
"""

import json
import math
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .chunker import Chunk, chunk_all

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
INDEX_DIR = BASE_DIR / ".data" / "rag_index"
VECTOR_INDEX_FILE = INDEX_DIR / "vectors.json"
BM25_INDEX_FILE = INDEX_DIR / "bm25.json"
CHUNKS_FILE = INDEX_DIR / "chunks.json"

VOYAGE_MODEL = "voyage-3"  # voyage-context-3 when available
VOYAGE_BATCH_SIZE = 64     # Max items per API call
EMBEDDING_DIM = 1024       # voyage-3 dimension


# ---------------------------------------------------------------------------
# BM25 LOCAL INDEX
# ---------------------------------------------------------------------------
class BM25Index:
    """Simple BM25 index using term frequencies."""

    def __init__(self):
        self.doc_freqs: Dict[str, int] = {}  # term -> num docs containing it
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.term_freqs: List[Dict[str, int]] = []  # per-doc term frequencies
        self.n_docs: int = 0
        self.k1: float = 1.5
        self.b: float = 0.75

    def build(self, documents: List[str]) -> None:
        """Build BM25 index from document texts."""
        self.n_docs = len(documents)
        self.doc_freqs = {}
        self.doc_lengths = []
        self.term_freqs = []

        for doc in documents:
            tokens = _tokenize(doc)
            tf = Counter(tokens)
            self.term_freqs.append(dict(tf))
            self.doc_lengths.append(len(tokens))

            for term in set(tokens):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avg_doc_length = (
            sum(self.doc_lengths) / max(self.n_docs, 1)
        )

    def query(self, query_text: str, top_k: int = 30) -> List[Tuple[int, float]]:
        """Search BM25 index. Returns [(doc_index, score), ...]."""
        query_tokens = _tokenize(query_text)
        scores: List[float] = [0.0] * self.n_docs

        for term in query_tokens:
            if term not in self.doc_freqs:
                continue
            df = self.doc_freqs[term]
            idf = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)

            for i in range(self.n_docs):
                tf = self.term_freqs[i].get(term, 0)
                if tf == 0:
                    continue
                dl = self.doc_lengths[i]
                norm_tf = (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_doc_length, 1))
                )
                scores[i] += idf * norm_tf

        # Top-k
        indexed_scores = [(i, s) for i, s in enumerate(scores) if s > 0]
        indexed_scores.sort(key=lambda x: -x[1])
        return indexed_scores[:top_k]

    def to_dict(self) -> dict:
        return {
            "doc_freqs": self.doc_freqs,
            "doc_lengths": self.doc_lengths,
            "avg_doc_length": self.avg_doc_length,
            "term_freqs": self.term_freqs,
            "n_docs": self.n_docs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BM25Index":
        idx = cls()
        idx.doc_freqs = data["doc_freqs"]
        idx.doc_lengths = data["doc_lengths"]
        idx.avg_doc_length = data["avg_doc_length"]
        idx.term_freqs = data["term_freqs"]
        idx.n_docs = data["n_docs"]
        return idx


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase, split on non-alphanum, filter short."""
    import re
    tokens = re.findall(r'[a-z\u00e0-\u024f]{2,}', text.lower())
    return tokens


# ---------------------------------------------------------------------------
# VECTOR INDEX (voyage-context-3)
# ---------------------------------------------------------------------------
class VectorIndex:
    """Vector similarity index using Voyage AI embeddings."""

    def __init__(self):
        self.vectors: List[List[float]] = []
        self.dim: int = EMBEDDING_DIM

    def build(self, texts: List[str], batch_size: int = VOYAGE_BATCH_SIZE) -> None:
        """Build vector index by embedding all texts."""
        self.vectors = []

        try:
            import voyageai
            client = voyageai.Client()
        except (ImportError, Exception) as e:
            print(f"[VectorIndex] voyageai not available: {e}")
            print("[VectorIndex] Using zero vectors as fallback.")
            self.vectors = [[0.0] * self.dim for _ in texts]
            return

        # Batch embed
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Truncate very long texts
            batch = [t[:8000] for t in batch]
            try:
                result = client.embed(batch, model=VOYAGE_MODEL,
                                      input_type="document")
                self.vectors.extend(result.embeddings)
            except Exception as e:
                print(f"[VectorIndex] Embedding batch {i//batch_size} failed: {e}")
                self.vectors.extend([[0.0] * self.dim for _ in batch])

            # Rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.5)

    def query(self, query_text: str, top_k: int = 30) -> List[Tuple[int, float]]:
        """Search by vector similarity. Returns [(doc_index, score), ...]."""
        if not self.vectors:
            return []

        try:
            import voyageai
            client = voyageai.Client()
            result = client.embed([query_text[:8000]], model=VOYAGE_MODEL,
                                  input_type="query")
            query_vec = result.embeddings[0]
        except Exception:
            return []

        # Cosine similarity
        scores = []
        for i, doc_vec in enumerate(self.vectors):
            sim = _cosine_sim(query_vec, doc_vec)
            if sim > 0:
                scores.append((i, sim))

        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]

    def to_dict(self) -> dict:
        return {"vectors": self.vectors, "dim": self.dim}

    @classmethod
    def from_dict(cls, data: dict) -> "VectorIndex":
        idx = cls()
        idx.vectors = data.get("vectors", [])
        idx.dim = data.get("dim", EMBEDDING_DIM)
        return idx


def _cosine_sim(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# HYBRID INDEX
# ---------------------------------------------------------------------------
class HybridIndex:
    """Combined vector + BM25 index with local JSON storage."""

    def __init__(self):
        self.chunks: List[dict] = []
        self.bm25 = BM25Index()
        self.vector = VectorIndex()
        self.built: bool = False

    def build(self, chunks: Optional[List[Chunk]] = None,
              skip_vectors: bool = False) -> dict:
        """Build both indexes from chunks.

        Args:
            chunks: List of Chunk objects. If None, chunks entire KB.
            skip_vectors: If True, only build BM25 (faster, no API calls).

        Returns stats dict.
        """
        if chunks is None:
            chunks = chunk_all()

        texts = [c.text for c in chunks]
        self.chunks = [c.to_dict() for c in chunks]

        # BM25
        t0 = time.time()
        self.bm25.build(texts)
        bm25_time = time.time() - t0

        # Vector
        vector_time = 0.0
        if not skip_vectors:
            t0 = time.time()
            self.vector.build(texts)
            vector_time = time.time() - t0

        self.built = True
        return {
            "total_chunks": len(chunks),
            "bm25_time_s": round(bm25_time, 2),
            "vector_time_s": round(vector_time, 2),
            "vectors_built": not skip_vectors,
        }

    def save(self, index_dir: Optional[Path] = None) -> None:
        """Save index to disk."""
        d = index_dir or INDEX_DIR
        d.mkdir(parents=True, exist_ok=True)

        with open(d / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False)

        with open(d / "bm25.json", "w", encoding="utf-8") as f:
            json.dump(self.bm25.to_dict(), f)

        with open(d / "vectors.json", "w", encoding="utf-8") as f:
            json.dump(self.vector.to_dict(), f)

    def load(self, index_dir: Optional[Path] = None) -> bool:
        """Load index from disk. Returns True if loaded."""
        d = index_dir or INDEX_DIR
        chunks_path = d / "chunks.json"
        bm25_path = d / "bm25.json"

        if not chunks_path.exists():
            return False

        with open(chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        if bm25_path.exists():
            with open(bm25_path, "r", encoding="utf-8") as f:
                self.bm25 = BM25Index.from_dict(json.load(f))

        vectors_path = d / "vectors.json"
        if vectors_path.exists():
            with open(vectors_path, "r", encoding="utf-8") as f:
                self.vector = VectorIndex.from_dict(json.load(f))

        self.built = True
        return True

    def get_chunk(self, index: int) -> dict:
        """Get chunk dict by index."""
        if 0 <= index < len(self.chunks):
            return self.chunks[index]
        return {}


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------
_index: Optional[HybridIndex] = None


def get_index() -> HybridIndex:
    """Get or create the hybrid index singleton."""
    global _index
    if _index is None:
        _index = HybridIndex()
        if not _index.load():
            _index = HybridIndex()
    return _index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build hybrid RAG index")
    parser.add_argument("--full", action="store_true",
                        help="Full build with vector embeddings")
    parser.add_argument("--bm25-only", action="store_true",
                        help="Build only BM25 index (no API calls)")
    args = parser.parse_args()

    skip_vectors = args.bm25_only or not args.full

    print(f"\n{'='*60}")
    print("HYBRID INDEX BUILDER")
    print(f"{'='*60}")
    if skip_vectors:
        print("[BM25-only mode — no vector embeddings]\n")
    else:
        print(f"[Full mode — voyage model: {VOYAGE_MODEL}]\n")

    idx = HybridIndex()
    stats = idx.build(skip_vectors=skip_vectors)

    print(f"Chunks indexed: {stats['total_chunks']}")
    print(f"BM25 build time: {stats['bm25_time_s']}s")
    if stats["vectors_built"]:
        print(f"Vector build time: {stats['vector_time_s']}s")

    idx.save()
    print(f"\nIndex saved to: {INDEX_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
