> **Auto-Trigger:** When user asks about relationships between concepts, experts, or knowledge graph queries
> **Keywords:** "graph search", "knowledge graph", "graph-search", "entities", "relationships", "connected to", "related concepts", "graph query"
> **Prioridade:** ALTA
> **Tools:** Bash, Read

## Quando NAO Ativar
- General text search (use Grep instead)
- RAG semantic search (use /rag-search)
- File search (use Glob)

## O Que Faz

Queries the Mega Brain Knowledge Graph (1,302 entities, 2,508 edges, 10 communities).
The graph is built from DNA YAMLs (5 layers x 10 persons) via `graph_builder.py`.

## Entity Types
- **pessoa** — Expert persons (Alex Hormozi, Cole Gordon, etc.)
- **dominio** — Knowledge domains (vendas, hiring, compensation, etc.)
- **filosofia** — Core beliefs (L1)
- **modelo_mental** — Thinking frameworks (L2)
- **heuristica** — Decision rules with thresholds (L3)
- **framework** — Structured methodologies (L4)
- **metodologia** — Step-by-step processes (L5)

## Relationship Types
- TEM (Pessoa -> Entry), PERTENCE_A (Entry -> Dominio)
- GERA, PRODUZ, MATERIALIZA, IMPLEMENTA (cascading layers)
- RELACIONADA_COM (cross-references between entries)

## Como Usar

### Search by entity name
```bash
python3 -c "
import json
from pathlib import Path
graph = json.loads(Path('.data/knowledge_graph/graph.json').read_text())
query = 'QUERY_HERE'.lower()
matches = [e for e in graph['entities'] if query in e.get('label','').lower() or query in e['id'].lower()]
for m in matches[:10]:
    print(f\"  {m['id']} | {m['type']} | {m.get('label','')} | pessoa={m.get('pessoa','')}\")
"
```

### Find connections from an entity
```bash
python3 -c "
import json
from pathlib import Path
graph = json.loads(Path('.data/knowledge_graph/graph.json').read_text())
entity_id = 'ENTITY_ID_HERE'
edges = [e for e in graph['edges'] if e['source'] == entity_id or e['target'] == entity_id]
for e in edges[:20]:
    print(f\"  {e['source']} --[{e['rel_type']}]--> {e['target']}\")
"
```

### Full rebuild
```bash
cd "$MEGA_BRAIN_ROOT"  # or your mega-brain project root
python3 -m core.intelligence.rag.graph_builder --build
```

## Graph Location
- **Graph file:** `.data/knowledge_graph/graph.json` (668KB)
- **Builder:** `core/intelligence/rag/graph_builder.py`
- **DNA source:** `knowledge/external/dna/persons/`
