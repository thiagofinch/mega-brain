# Mega Brain Examples

Working examples demonstrating core Mega Brain capabilities.
Each example uses real module imports and function signatures from the codebase.

| # | Example | What It Shows | Key Module |
|---|---------|---------------|------------|
| 01 | [Ingest PDF](01-ingest-pdf/) | Extract PDF text and route to inbox | `pipeline/pdf_extractor.py` |
| 02 | [Query RAG](02-query-rag/) | Hybrid search (BM25 + vector + RRF) | `rag/hybrid_query.py` |
| 03 | [Score Quality](03-score-quality/) | Numeric quality scoring (0-100) | `validation/quality_scorer.py` |
| 04 | [Vector Search](04-vector-search/) | ChromaDB persistent vector store | `rag/chroma_store.py` |
| 05 | [Agent API](05-agent-api/) | REST API for agent queries + conclave | `api/agent_server.py` |

## Prerequisites

- Python 3.12+
- Mega Brain repo cloned and knowledge base populated

### Per-example dependencies

```bash
# Example 01: PDF extraction
pip install pymupdf

# Example 02: RAG search (BM25 always available, vector needs VOYAGE_API_KEY)
# No extra install -- uses stdlib + built-in BM25

# Example 03: Quality scoring
# No extra install -- pure Python

# Example 04: Vector store
pip install chromadb

# Example 05: Agent API
pip install fastapi uvicorn pyyaml
```

## Running

All examples assume you are in the project root (`mega-brain/`).

```bash
cd /path/to/mega-brain
python -c "from core.intelligence.pipeline.pdf_extractor import extract_pdf; print('OK')"
```

## Architecture Context

```
core/intelligence/
  pipeline/    -- Ingestion, routing, extraction
  rag/         -- Retrieval: BM25, vector, hybrid, graph
  validation/  -- Quality scoring, layer audits
core/api/      -- FastAPI agent server + conclave service
```
