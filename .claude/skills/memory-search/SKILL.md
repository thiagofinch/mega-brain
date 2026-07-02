> **Auto-Trigger:** When user asks about agent memories, past decisions, or memory operations
> **Keywords:** "memory search", "memory-search", "agent memory", "what does the agent remember", "memory stats", "prune memory", "consolidate memory"
> **Prioridade:** ALTA
> **Tools:** Bash, Read

## Quando NAO Ativar
- File-based MEMORY.md reads (use Read tool directly)
- Knowledge graph queries (use /graph-search)
- RAG semantic search (use /rag-search)

## O Que Faz

Interfaces with the programmatic Memory Manager API (`core/intelligence/memory_manager.py`).
Each agent has a JSONL-backed memory store in `.data/agent_memory/{agent_id}/memories.jsonl`.

Scoring: `0.5 * semantic_sim + 0.3 * recency_decay + 0.2 * importance`

## Operations

### Write a memory
```bash
python3 -m core.intelligence.memory_manager write {agent_id} "content here" --importance 0.8 --tags tag1,tag2
```

### Search memories
```bash
python3 -m core.intelligence.memory_manager search {agent_id} "query terms" --top-k 10
```

### Get stats
```bash
python3 -m core.intelligence.memory_manager stats {agent_id}
```

### Prune low-value entries
```bash
python3 -m core.intelligence.memory_manager prune {agent_id} --max-entries 200
```

### Consolidate near-duplicates
```bash
python3 -m core.intelligence.memory_manager consolidate {agent_id}
```

## Memory Scopes
- **core** — Protected from pruning, fundamental knowledge
- **long_term** — Standard persistent memory (default)
- **session** — Ephemeral, pruned aggressively

## Pinned Entries
Entries marked `pinned=True` are never pruned regardless of score.

## Architecture
```
.data/agent_memory/
  {agent_id}/
    memories.jsonl     <- JSONL, sorted by composite_score
  _shared/
    memories.jsonl     <- Cross-agent shared store
```

## API (Python)
```python
from core.intelligence.memory_manager import memory_write, memory_search, get_store

# Write
entry = memory_write("closer", "Always isolate objection before responding", importance=0.9)

# Search
results = memory_search("closer", "objection handling", top_k=5)

# Stats
stats = get_store("closer").stats()
```
