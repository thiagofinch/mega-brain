# mind-mapper

> **Pipeline Position:** META-LAYER - Master Orchestrator
> **Coordinates:** All 9 phases (0-8)

Load and activate the Mind Mapper agent from `.aiox/development/agents/mind-mapper.md`

## The Magic Command

```
@mind-mapper *map alex-hormozi
```

**Automatically:**
1. Detects greenfield vs brownfield
2. Calls @research-specialist if needs sources
3. Validates viability with @mind-pm
4. Processes with @analyst
5. Extracts layers 1-4 with @cognitive-analyst
6. Extracts layers 5-8 with @identity-analyst (human checkpoints)
7. Synthesizes with @charlie
8. Compiles prompts with @system-prompt-architect
9. Validates with @debate
10. Activates with @emulator

## Commands

| Command | Description |
|---------|-------------|
| `*help` | Show available commands |
| `*map {slug}` | Execute complete pipeline |
| `*map {slug} --mode greenfield` | Force new clone |
| `*map {slug} --mode brownfield` | Force update |
| `*status {slug}` | Clone status |
| `*estimate {slug}` | Effort estimation |
| `*resume {slug}` | Resume interrupted |
| `*exit` | Deactivate |

## Fidelity Target: ≥85% across all 8 layers
