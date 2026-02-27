# Mega Brain - AI Knowledge Management System

## What is Mega Brain?

AI-powered system that transforms expert materials (videos, PDFs, transcriptions) into structured playbooks, DNA schemas, and mind-clone agents. Powered by JARVIS orchestrator.

## Quick Start

1. Run `npx mega-brain-ai setup` (auto-triggers on first use if `.env` missing)
2. Fill in API keys when prompted (only `OPENAI_API_KEY` is required)
3. Use `/jarvis-briefing` to see system status

## Architecture

```
mega-brain/
├── core/           -> Engine (Pedro pattern)
│   ├── tasks/          -> Atomic tasks (HO-TP-001 anatomy)
│   ├── workflows/      -> YAML orchestration
│   ├── intelligence/   -> Python scripts
│   ├── patterns/       -> YAML configs
│   ├── protocols/      -> Pipeline, conclave, DNA protocols
│   ├── schemas/        -> JSON schemas
│   ├── jarvis/         -> JARVIS Soul + DNA
│   ├── templates/      -> Log templates
│   └── glossary/       -> Domain glossaries
├── agents/         -> AI agents (conclave, cargo, persons)
├── .claude/        -> Claude Code integration
├── docs/           -> Documentation, PRDs, plans
│   ├── prd/            -> Product requirements
│   └── plans/          -> Plan mode outputs
├── bin/            -> CLI tools (npm)
├── inbox/          -> Raw materials (L3)
├── artifacts/      -> Pipeline stages (L3)
├── knowledge/      -> Knowledge base (L3)
└── logs/           -> Session logs (L3)
```

## Plan Mode

Plans MUST be saved to `docs/plans/` (not ~/.claude/plans/).
When in plan mode, save the plan file to: `docs/plans/YYYY-MM-DD-description.md`

### Layer System

| Layer | Content | Git Status |
|-------|---------|------------|
| L1 (Community) | core/, agents/conclave, .claude/, bin/, docs/ | Tracked (npm package) |
| L2 (Pro) | agents/cargo, agents/sub-agents | Tracked (premium) |
| L3 (Personal) | .data/, .env, agents/persons | Gitignored |

## Community vs Pro

| Feature | Community | Pro |
|---------|-----------|-----|
| CLI & Templates | yes | yes |
| Skills & Hooks | yes | yes |
| Agent Templates | yes | yes |
| Knowledge Base (populated) | - | yes |
| Mind Clone Agents | - | yes |
| Pipeline Processing | - | yes |
| Council / Conclave | - | yes |

## DNA Schema (5 Knowledge Layers)

| Layer | Name | Description |
|-------|------|-------------|
| L1 | PHILOSOPHIES | Core beliefs and worldview |
| L2 | MENTAL-MODELS | Thinking and decision frameworks |
| L3 | HEURISTICS | Practical rules and decision shortcuts |
| L4 | FRAMEWORKS | Structured methodologies and processes |
| L5 | METHODOLOGIES | Step-by-step implementations |

## Commands

| Command | Description |
|---------|-------------|
| `/jarvis-briefing` | Operational status + health score |
| `/jarvis-full` | Full pipeline (ingest + process + enrich) |
| `/process-jarvis` | Pipeline processor (5 phases) |
| `/conclave` | Council session (multi-agent debate) |
| `/ingest` | Ingest new material |
| `/save` | Save current session |
| `/resume` | Resume previous session |
| `/setup` | Environment setup wizard |

## Agents

Defined in `AGENT-INDEX.yaml`, activated via slash commands.

| Type | Count | Purpose |
|------|-------|---------|
| CARGO | 29 | Functional roles (Sales, Marketing, Ops) |
| MINDS | 5 | Expert mind clones |
| CONCLAVE | 3 | Multi-perspective deliberation |
| SYSTEM | 2 | JARVIS, Agent-Creator |

**Total Active Agents:** 37
## Configuration

- **`.env`** is the ONLY source of truth for credentials
- Run `/setup` to configure interactively
- Never hardcode API keys anywhere
- `.mcp.json` uses `${ENV_VAR}` syntax for MCP servers

### Required Keys

| Key | Purpose | Required? |
|-----|---------|-----------|
| `OPENAI_API_KEY` | Whisper transcription | Yes (pipeline needs it) |
| `VOYAGE_API_KEY` | Semantic embeddings (RAG) | Recommended |
| `GOOGLE_CLIENT_ID` | Drive import | Optional |
| `ANTHROPIC_API_KEY` | N/A with Claude Code | Not needed |

## Hooks System

20+ active hooks in `.claude/hooks/` (Python 3, stdlib + PyYAML only).
Configured in `settings.json` (distributed) and `settings.local.json` (local overrides).

| Event | Key Hooks |
|-------|-----------|
| SessionStart | `session_start.py`, `inbox_age_alert.py`, `skill_indexer.py` |
| UserPromptSubmit | `skill_router.py`, `quality_watchdog.py`, `memory_updater.py` |
| PreToolUse | `creation_validator.py`, `claude_md_guard.py` |
| PostToolUse | `post_tool_use.py`, `enforce_dual_location.py` |
| Stop | `stop_hook_completeness.py`, `ralph_wiggum.py` |

## Rules (Lazy Loading)

Detailed rules are loaded on-demand via keyword matching from `.claude/rules/`:

| Group | Topics | File |
|-------|--------|------|
| PHASE-MANAGEMENT | phases, pipeline, batch | RULE-GROUP-1.md |
| PERSISTENCE | sessions, save, resume | RULE-GROUP-2.md |
| OPERATIONS | parallel, templates, KPIs | RULE-GROUP-3.md |
| PHASE-5 | agents, dossiers, cascading | RULE-GROUP-4.md |
| VALIDATION | source-sync, integrity | RULE-GROUP-5.md |
| AUTO-ROUTING | skills, sub-agents, GitHub | RULE-GROUP-6.md |

## Security

1. **NEVER** hardcode API keys or tokens in code
2. **ALWAYS** use `.env` for credentials (gitignored)
3. Google OAuth credentials via config file, not code
4. `git push` is blocked by `settings.json` deny rules — delegate to @devops

## Conventions

- Folders: lowercase (`inbox`, `system`)
- Config files: SCREAMING-CASE (`STATE.json`, `MEMORY.md`)
- Python scripts: snake_case, use `pathlib.Path` for cross-platform paths
- Skills: kebab-case directories (`knowledge-extraction/`)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Hook failed" | Check Python 3 is in PATH |
| ".env not found" | Run `npx mega-brain-ai setup` |
| "Permission denied on git push" | By design — use branch + PR workflow |
| Skills not auto-activating | Check `SKILL-INDEX.json` is generated on SessionStart |

## Recent Changes

See `system/docs/CHANGELOG-ARCHITECTURE.md` for architectural evolution history.

## CLAUDE.md Policy

- Only 2 CLAUDE.md files are valid: root `CLAUDE.md` and `.claude/CLAUDE.md` (this file)
- NEVER create CLAUDE.md in data or code subdirectories
- Agent memory lives in `.claude/jarvis/` and `.claude/skills/`
