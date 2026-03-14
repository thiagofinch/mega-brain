# Example 04: Vector Store with ChromaDB

Demonstrates persistent vector storage using ChromaDB for semantic search.

## Prerequisites

```bash
pip install chromadb
```

## Usage

### Initialize and add chunks

```python
from core.intelligence.rag.chroma_store import ChromaStore

# Initialize (data persisted to .data/chroma/ by default)
store = ChromaStore(collection_name="expert_knowledge")

# Add a single chunk with its embedding
store.add(
    chunk_id="hormozi-001",
    text="The only way to grow is to make an offer so good people feel stupid saying no.",
    embedding=[0.1, 0.2, 0.3],  # Real embedding from VoyageAI or sentence-transformers
    metadata={"source": "alex-hormozi", "topic": "offers"}
)

# Add multiple chunks in batch (more efficient)
store.add_batch(
    chunk_ids=["hormozi-002", "hormozi-003"],
    texts=[
        "Volume negates luck. The more you do, the less luck matters.",
        "Charge as much as possible for your services."
    ],
    embeddings=[[0.15, 0.25, 0.35], [0.2, 0.3, 0.4]],
    metadatas=[
        {"source": "alex-hormozi", "topic": "mindset"},
        {"source": "alex-hormozi", "topic": "pricing"}
    ]
)
```

### Search by similarity

```python
from core.intelligence.rag.chroma_store import ChromaStore

store = ChromaStore(collection_name="expert_knowledge")

# Search by embedding vector
results = store.search(
    query_embedding=[0.15, 0.25, 0.35],
    top_k=5
)

for r in results:
    print(f"Score: {r.score:.3f} | {r.chunk_id}")
    print(f"  {r.text[:100]}")
    print(f"  Metadata: {r.metadata}")
    print()
```

### Check collection stats

```python
from core.intelligence.rag.chroma_store import ChromaStore

store = ChromaStore(collection_name="expert_knowledge")
print(f"Total chunks stored: {store.count()}")
```

### Custom persist directory

```python
from core.intelligence.rag.chroma_store import ChromaStore

# Use a custom location for the vector database
store = ChromaStore(
    collection_name="my_collection",
    persist_dir="/path/to/custom/chroma"
)
```

## How It Works

ChromaStore implements the `VectorStore` abstract interface defined in
`core/intelligence/rag/vector_store.py`:

```
VectorStore (abstract)
  |
  +-- ChromaStore (ChromaDB implementation)
       |
       +-- add(chunk_id, text, embedding, metadata)
       +-- add_batch(chunk_ids, texts, embeddings, metadatas)
       +-- search(query_embedding, top_k) -> list[SearchResult]
       +-- count() -> int
```

### SearchResult fields

| Field | Type | Description |
|-------|------|-------------|
| chunk_id | str | Unique identifier for the chunk |
| text | str | The original text content |
| score | float | Cosine similarity score (0.0 to 1.0) |
| metadata | dict | Associated metadata (source, topic, etc.) |

## Storage

- Default location: `.data/chroma/`
- Survives process restarts (persistent storage)
- Uses HNSW index with cosine distance metric
- No external database needed -- runs entirely local

## Source

Module: `core/intelligence/rag/chroma_store.py`

Key class: `ChromaStore(collection_name="mega_brain", persist_dir=None)`

Methods:
- `add(chunk_id, text, embedding, metadata=None) -> None`
- `add_batch(chunk_ids, texts, embeddings, metadatas=None) -> None`
- `search(query_embedding, top_k=10) -> list[SearchResult]`
- `count() -> int`
