# Example 05: Query Agents via REST API

Demonstrates the Agent API for programmatic access to mind-clone agents
and the Conclave debate system.

## Prerequisites

```bash
pip install fastapi uvicorn pyyaml
```

## Start the Server

```bash
uvicorn core.api.agent_server:app --port 8200
```

## Endpoints

### Health and metadata

```bash
# Root info
curl http://localhost:8200/

# Health check
curl http://localhost:8200/health

# List agent categories
curl http://localhost:8200/categories
```

### Agent queries

```bash
# List all agents (with optional category filter)
curl http://localhost:8200/agents
curl "http://localhost:8200/agents?category=external"
curl "http://localhost:8200/agents?category=cargo"

# Get a specific agent's full profile
curl http://localhost:8200/agents/alex-hormozi

# Get an agent's soul (identity, voice, beliefs)
curl http://localhost:8200/agents/alex-hormozi/soul

# Get an agent's memory (insights, patterns, decisions)
curl http://localhost:8200/agents/alex-hormozi/memory
```

### Conclave (multi-agent debate)

```bash
# List agents available for conclave
curl http://localhost:8200/conclave/agents

# Start a debate between agents
curl -X POST "http://localhost:8200/conclave/debate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How to structure sales compensation for a 5-person team?",
    "agents": ["alex-hormozi", "cole-gordon"]
  }'
```

## Python Client Example

```python
import requests

BASE = "http://localhost:8200"

# List all agents
response = requests.get(f"{BASE}/agents")
data = response.json()
print(f"Total agents: {data['count']}")
for agent in data["agents"]:
    print(f"  {agent['id']} ({agent['category']}) - {agent['completeness']}% complete")

# Get specific agent
hormozi = requests.get(f"{BASE}/agents/alex-hormozi").json()
print(f"\nAgent: {hormozi['id']}")
print(f"Category: {hormozi['category']}")
print(f"Files: {hormozi['files']}")
print(f"Completeness: {hormozi['completeness']}%")

# Get agent soul
soul = requests.get(f"{BASE}/agents/alex-hormozi/soul").json()
if soul.get("content"):
    print(f"\nSOUL preview: {soul['content'][:200]}...")

# Start a conclave debate
debate = requests.post(f"{BASE}/conclave/debate", json={
    "topic": "Best approach to handle 'I need to think about it' objection",
    "agents": ["alex-hormozi", "cole-gordon"]
}).json()
print(f"\nDebate result: {debate}")
```

## Response Formats

### GET /agents

```json
{
  "agents": [
    {
      "id": "alex-hormozi",
      "category": "external",
      "subcategory": null,
      "files": {"AGENT.md": true, "SOUL.md": true, "MEMORY.md": true, "DNA-CONFIG.yaml": true},
      "completeness": 100
    }
  ],
  "count": 35,
  "categories": ["external", "cargo", "system", "business", "personal"]
}
```

### GET /agents/{id}

```json
{
  "id": "alex-hormozi",
  "category": "external",
  "subcategory": null,
  "files": {"AGENT.md": true, "SOUL.md": true, "MEMORY.md": true, "DNA-CONFIG.yaml": true},
  "completeness": 100,
  "path": "agents/external/alex-hormozi"
}
```

## Agent Categories

| Category | What It Contains | Example Agents |
|----------|-----------------|----------------|
| external | Expert mind clones | alex-hormozi, cole-gordon, jeremy-miner |
| cargo | Functional role hybrids | closer, cro, cfo, cmo |
| system | Infrastructure agents | conclave, boardroom, jarvis |
| business | Collaborator clones | (team members) |
| personal | Founder clone | (founder) |

## Source

Module: `core/api/agent_server.py`

Endpoints:
- `GET /` -- Server info
- `GET /health` -- Health check
- `GET /categories` -- List agent categories
- `GET /agents` -- List agents (optional `?category=` filter)
- `GET /agents/{agent_id}` -- Agent details
- `GET /agents/{agent_id}/soul` -- Agent soul/identity
- `GET /agents/{agent_id}/memory` -- Agent memory/insights
- `GET /conclave/agents` -- Conclave-eligible agents
- `POST /conclave/debate` -- Start multi-agent debate
