# research-specialist

> **Pipeline Position:** Phase 0 - Discovery & Source Collection
> **Handoff to:** @analyst (Phase 2 via /ingest)

Load and activate the Research Specialist agent from `.aiox/development/agents/research-specialist.md`

## Commands

| Command | Description |
|---------|-------------|
| `*help` | Show available commands |
| `*discover --persona {name}` | Discover sources for a personality |
| `*collect --sources {list}` | Collect and organize materials |
| `*build-kb --persona {name}` | Build knowledge base from sources |
| `*validate --source {url}` | Validate source quality |
| `*exit` | Deactivate |

## Pipeline Flow

```
@research-specialist *discover --persona alex-hormozi
        ↓
   Sources collected (min 10)
        ↓
@mind-pm *viability-check (Phase 1)
```
