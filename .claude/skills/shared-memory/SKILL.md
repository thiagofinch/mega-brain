> **Auto-Trigger:** When user asks about cross-agent decisions, shared knowledge, or conclave outcomes
> **Keywords:** "shared memory", "shared-memory", "cross-agent", "conclave decision", "agent agreement", "shared store"
> **Prioridade:** MEDIA
> **Tools:** Bash, Read

## Quando NAO Ativar
- Single-agent memory operations (use /memory-search)
- File reads of any kind (use Read)
- Knowledge graph queries (use /graph-search)

## O Que Faz

Manages the cross-agent Shared Memory Store — a centralized JSONL store where
inter-agent agreements, conclave decisions, and cross-cutting knowledge live.

Located at: `.data/agent_memory/_shared/memories.jsonl`

## Operations

### Write a shared decision
```bash
python3 -m core.intelligence.memory_manager shared-write "Commission structure: 10% base + 5% bonus for top performers" --agents CLOSER,CFO
```

### Search shared memories
```bash
python3 -m core.intelligence.memory_manager shared-search "compensation"
```

## Python API
```python
from core.intelligence.memory_manager import shared_write, shared_search, get_shared_store

# Record a conclave decision
entry = shared_write(
    "Decided: High-ticket threshold is R$5,000+",
    agents_involved=["CLOSER", "CRO", "CFO"],
    importance=0.95,
    scope="core",
    pinned=True,
)

# Search decisions involving an agent
results = get_shared_store().search_by_agent("CFO")

# Search by topic
results = shared_search("pricing threshold")
```

## Integration Points

### With /conclave
After a conclave session concludes with a decision, the synthesizer should write
the decision to shared memory:
```python
shared_write(
    f"CONCLAVE DECISION: {decision_summary}",
    agents_involved=participating_agents,
    importance=0.9,
    scope="core",
    pinned=True,
    tags=["conclave", f"session:{session_id}"],
)
```

### With Agent Memory
Individual agents can search shared memory to check for existing cross-agent
agreements before making solo recommendations.

## Store Location
```
.data/agent_memory/_shared/memories.jsonl
```
