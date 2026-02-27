# Agents Directory

Central hub for all AI agents in Mega Brain.

## Layer Architecture

| Layer | Path | Description | Trigger |
|-------|------|-------------|---------|
| L0 | `core/jarvis/` | System orchestrators | Manual |
| L1 | `conclave/` | Constitutional deliberation | `/conclave` |
| L2 | `boardroom/` | C-Level executives | Threshold >=10 |
| L3 | `minds/` | Expert mind clones | Pipeline Phase 5.2 |
| L4 | `cargo/` | Operational roles | Threshold >=5 |
| SUB | `.claude/jarvis/sub-agents/` | JARVIS operatives | Keywords |

## Directory Structure

```
agents/
├── minds/           # L3 - Expert mind clones (Hormozi, Cole Gordon, etc.)
├── cargo/           # L4 - Functional roles (Sales, Marketing, Ops)
├── conclave/        # L1 - Deliberative agents (Critic, Advocate, Synthesizer)
├── boardroom/       # L2 - C-Level strategic debates
├── autonomous/      # Meta-agents (Evolver, Benchmark, Critic)
├── sub-agents/      # Specialized sub-agents
├── protocols/       # Agent interaction protocols
├── constitution/    # Constitutional base for deliberations
├── sua-empresa/     # Organizational structure
├── discovery/       # Role detection and tracking
├── _templates/      # Official agent templates (V3)
├── AGENT-INDEX.yaml # Master catalog (auto-updated)
└── persona-registry.yaml # Layer definitions
```

## Commands

| Command | Action |
|---------|--------|
| `/create-agent` | Create new agent |
| `/ask [id]` | Query specific agent |
| `/conclave` | Start council deliberation |
| `/agents` | Show agent status |

## Creating Agents

Use `/create-agent --layer [L0-L4|SUB] --id [id] --name "[name]" --role "[role]"`

All agents follow `_templates/TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md` (11 mandatory parts).
