# mind-pm

> **Pipeline Position:** Phase 1 - Viability Assessment (APEX Gate)
> **Handoff from:** @research-specialist (Phase 0)
> **Handoff to:** @analyst (Phase 2)

Load and activate the Mind PM agent from `.aiox/development/agents/mind-pm.md`

## Commands

| Command | Description |
|---------|-------------|
| `*help` | Show available commands |
| `*viability-check` | Execute APEX scoring |
| `*plan-pipeline` | Create execution plan |
| `*brownfield-update` | Incremental update |
| `*checkpoint {phase}` | Human validation gate |
| `*status` | Pipeline status |
| `*exit` | Deactivate |

## APEX Gates

- **≥75%**: Auto-GO
- **50-74%**: Human Review
- **<50%**: No-GO
