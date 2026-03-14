# Example 02: Query the Knowledge Base (RAG)

Demonstrates how to search the knowledge base using the hybrid retrieval pipeline.

## Prerequisites

- BM25 index built (`.data/rag_index/` exists with `chunks.json` and `bm25.json`)
- Optional: `VOYAGE_API_KEY` in `.env` for vector similarity search

To build the index for the first time:

```bash
python -m core.intelligence.rag.hybrid_index --bm25-only
```

## Usage

### Quick search with hybrid_search (recommended)

```python
from core.intelligence.rag.hybrid_query import hybrid_search

results = hybrid_search(
    query="How does Hormozi structure sales compensation?",
    top_k=5
)

print(f"Query: {results['query']}")
print(f"Found: {len(results['results'])} results in {results['latency_ms']:.0f}ms")
print(f"Pipeline: {results['pipeline']}")
print()

for r in results["results"]:
    print(f"  Score: {r['score']:.4f} | Source: {r['metadata'].get('source', 'unknown')}")
    print(f"  {r['text'][:150]}...")
    print()
```

### Search with filters

```python
from core.intelligence.rag.hybrid_query import hybrid_search

# Filter by expert
results = hybrid_search(
    query="objection handling techniques",
    top_k=5,
    filters={"person": "cole-gordon"}
)

# Filter by DNA layer
results = hybrid_search(
    query="pricing strategy",
    top_k=5,
    filters={"layer": "HEURISTICS"}
)
```

### Low-level BM25 search

```python
from core.intelligence.rag.hybrid_index import get_index

index = get_index()
if not index.built:
    index.load()  # Load from .data/rag_index/

# Raw BM25 query -- returns (doc_index, score) tuples
bm25_results = index.bm25.query("sales team structure", top_k=10)

for doc_idx, score in bm25_results:
    chunk = index.get_chunk(doc_idx)
    print(f"Score: {score:.4f} | {chunk.get('metadata', {}).get('source', '?')}")
    print(f"  {chunk['text'][:120]}...")
```

## What Happens

The hybrid search pipeline runs 5 stages:

```
Query
  |
  v
Stage 1: Vector search (voyage-3) --> top 30 candidates
  |
  v
Stage 2: BM25 keyword search --> top 30 candidates
  |
  v
Stage 3: Reciprocal Rank Fusion (RRF, k=60) --> merged ranking
  |
  v
Stage 4: Reranking (zerank-2 if available, else score-based) --> top K
  |
  v
Stage 5: Strategic ordering (best results at start AND end of context)
  |
  v
Results
```

- BM25 is always available (no API key needed)
- Vector search activates when `VOYAGE_API_KEY` is set in `.env` or shell
- If only BM25 is available, stages 1 and 3 are simplified to BM25-only

## Search Modes

| Mode | What It Uses | Speed | Quality | Requires |
|------|-------------|-------|---------|----------|
| BM25-only | Keyword matching | Fast (~50ms) | Good for exact terms | Nothing |
| Hybrid | BM25 + vector + RRF | Medium (~3s) | Best for concepts | VOYAGE_API_KEY |
| Graph-enhanced | Hybrid + knowledge graph | Slower (~6s) | Best for cross-expert | VOYAGE_API_KEY + graph |

## Source

Module: `core/intelligence/rag/hybrid_query.py`

Key function:
- `hybrid_search(query, top_k=10, index=None, filters=None, use_strategic_order=True) -> dict`

Supporting modules:
- `core/intelligence/rag/hybrid_index.py` -- BM25Index, VectorIndex, HybridIndex
- `core/intelligence/rag/chunker.py` -- Text chunking
