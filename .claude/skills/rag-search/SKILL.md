---
name: rag-search
description: Search Mega Brain RAG knowledge across external, business, and personal buckets using the query orchestrator module. Use when the user asks to search Oracle knowledge, consult RAG, or find what the knowledge base says about a topic.
auto-trigger:
  - rag search
  - buscar no rag
  - procurar no knowledge
  - serviços produtizados
  - high-ticket
  - oracle query
  - consultar rag
  - search rag
  - what does oracle know about
  - oracle query about my company
allowed-tools: Read, Bash(grep:*), Bash(python3:*), Bash(test:*)
---

# RAG Search

> **Auto-Trigger:** When the user wants Oracle or Claude Code to search indexed knowledge across RAG buckets instead of guessing from context alone
> **Keywords:** "rag search", "buscar no rag", "procurar no knowledge", "serviços produtizados", "high-ticket", "oracle query", "consultar rag", "search rag", "what does oracle know about", "oracle query about my company"
> **Prioridade:** ALTA
> **Tools:** Bash, Read

## Quando NAO Ativar
- Knowledge graph traversal or entity relationships (use `/graph-search`)
- RAG health, freshness, or stale-index diagnostics (use `/rag-health`)
- Raw file lookup when exact path is already known (use Read or Grep directly)

## O Que Faz

Runs cross-bucket BM25 search through the Query Orchestrator module at `engine/intelligence/rag/query_orchestrator.py`.

This is the correct invocation form:

```bash
python3 -m engine.intelligence.rag.query_orchestrator '<query>'
```

Do not run the file directly with `python3 engine/intelligence/rag/query_orchestrator.py ...`.
Script-form breaks imports and can raise `ModuleNotFoundError`. Use module form only.

## Buckets Consultados

- `external` - expert knowledge and source materials
- `business` - meetings, calls, operations, SOPs
- `personal` - personal notes and founder knowledge

Optional second argument limits the search to one or more buckets:

```bash
python3 -m engine.intelligence.rag.query_orchestrator '<query>' business
python3 -m engine.intelligence.rag.query_orchestrator '<query>' external,business
```

If no bucket is passed, the orchestrator searches all three buckets in parallel.

## Output Esperado

The CLI returns a ranked list of chunks. Each result should be interpreted with these fields:

- `bucket` - which knowledge bucket matched (`external`, `business`, `personal`)
- `source_file` - original file path or source artifact that produced the chunk
- `score` - relevance score used for ranking
- `chunk_id` - stable chunk identifier
- `text` - chunk content preview or full chunk body

Expected output shape:

```text
#1 [0.8421] (business) chunk_00123
   File: workspace/ops/processos-sops/ofertas.md
   ...
```

When summarizing results back to the user, prefer this compact structure:

```text
- bucket: business
  source_file: workspace/ops/processos-sops/ofertas.md
  score: 0.8421
  chunk_id: chunk_00123
```

## Como Usar

### Example 1: broad Oracle query

```bash
python3 -m engine.intelligence.rag.query_orchestrator 'what does oracle know about serviços produtizados'
```

Expected shape:

```text
Searched: external, business, personal
Results: 10

#1 [0.84] (business) ...
   File: ...
```

### Example 2: pricing / offer research

```bash
python3 -m engine.intelligence.rag.query_orchestrator 'high-ticket offer structure for serviços produtizados' external,business
```

Expected shape:

```text
#1 [0.79] (external) ...
   File: ...
#2 [0.74] (business) ...
   File: ...
```

### Example 3: direct consult request

```bash
python3 -m engine.intelligence.rag.query_orchestrator 'consultar rag sobre a sua organização para ofertas'
```

Expected shape:

```text
Searched: external, business, personal
Results: N
- bucket: external
  source_file: ...
  score: ...
```

## File Locations

- **Query orchestrator module:** `engine/intelligence/rag/query_orchestrator.py`
- **Canonical routing map:** `engine/paths.py`
- **Bucket indexes:** `.data/rag_expert/`, `.data/rag_business/`, `knowledge/personal/index/`
