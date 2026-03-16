> **Auto-Trigger:** When user asks about RAG status, index health, or data layer diagnostics
> **Keywords:** "rag health", "rag-health", "index health", "index status", "stale index", "rag status", "data health", "bucket health", "chunk count"
> **Prioridade:** ALTA
> **Tools:** Bash, Read

## Quando NAO Ativar
- Semantic search queries (use /rag-search or /memory-search)
- Knowledge graph traversal (use /graph-search)
- Index rebuild (use /rag-rebuild)

## O Que Faz

Runs a full health diagnostic across all 3 RAG buckets (external, business, personal) plus the knowledge graph. Displays an ASCII table with:

- Chunk counts per bucket
- Index ages (how old each index is)
- Staleness status (FRESH / STALE / NOT BUILT)
- Knowledge graph entity count, edge count, and last build time

Returns exit code 1 if any index is stale, enabling CI integration.

## Como Usar

### Quick check (ASCII table)
```bash
cd /Users/thiagofinch/Documents/Projects/mega-brain
python3 -m core.intelligence.rag.health_check
```

### Machine-readable JSON
```bash
cd /Users/thiagofinch/Documents/Projects/mega-brain
python3 -m core.intelligence.rag.health_check --json
```

### Programmatic import
```python
from core.intelligence.rag.health_check import run_health_check, render_ascii_table

report = run_health_check()
if report["is_stale"]:
    print(render_ascii_table(report))
```

## What Each Column Means

| Column | Description |
|--------|-------------|
| Bucket | RAG index name (external, business, personal) |
| Status | FRESH (index newer than sources), STALE (sources changed since last build), NOT BUILT (no index exists) |
| Chunks | Number of text chunks in the index |
| Size | Total disk size of the index files |
| Index Age | How long ago the index was last built |
| Source Age | How recently the newest source file was modified |

## Dependencies

- `core/intelligence/rag/staleness_checker.py` -- provides `check_staleness()` per-bucket freshness data
- `core/paths.py` -- canonical paths for `.data/rag_index/`, `.data/rag_business/`, `.data/knowledge_graph/`
- `.data/knowledge_graph/graph.json` -- knowledge graph with stats block

## File Locations

- **Health check script:** `core/intelligence/rag/health_check.py`
- **Staleness checker:** `core/intelligence/rag/staleness_checker.py`
- **RAG indexes:** `.data/rag_index/` (external), `.data/rag_business/` (business), `.data/rag_personal/` (personal)
- **Knowledge graph:** `.data/knowledge_graph/graph.json`
