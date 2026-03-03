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
├── .aiox/         -> AIOS Core (gitignored, local-only)
│   ├── development/
│   │   ├── agents/         -> 40+ agent definitions + mega-brain/
│   │   └── skills/         -> 19 development skills (media-buyer, etc.)
│   ├── core/protocols/     -> constitution.yaml, agent-index.yaml
│   └── hooks/              -> 34 AIOS-exclusive hooks + _utils/
├── core/               -> Engine (Pedro pattern)
│   ├── tasks/              -> Atomic tasks (HO-TP-001 anatomy)
│   ├── workflows/          -> YAML orchestration
│   ├── intelligence/       -> Python scripts
│   ├── patterns/           -> YAML configs
│   ├── protocols/          -> Pipeline, conclave, DNA protocols
│   ├── schemas/            -> JSON schemas
│   ├── jarvis/             -> JARVIS Soul + DNA
│   ├── templates/          -> Log templates
│   └── glossary/           -> Domain glossaries
├── agents/             -> AI agents (conclave, cargo, persons)
├── .claude/            -> Claude Code integration
│   ├── agents/             -> 24 Claude Code agent types (gitignored)
│   ├── hooks/              -> 30 hooks (tracked) + merged AIOS features
│   ├── skills/             -> 59 skills (45 native + 14 AIOS, mixed gitignore)
│   ├── commands/           -> 56 commands (39 native + 17 AIOS, mixed gitignore)
│   └── rules/              -> 21 rules (16 native + 5 AIOS, mixed gitignore)
├── docs/               -> Documentation, PRDs, plans
├── bin/                -> CLI tools (npm)
├── inbox/              -> Raw materials (L3)
├── artifacts/          -> Pipeline stages (L3)
├── knowledge/          -> Knowledge base (L3)
└── logs/               -> Session logs (L3)
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

### AIOS Core Commands (migrated, gitignored)

| Command | Description |
|---------|-------------|
| `/AIOS/*` | AIOS agent activation sub-commands |
| `/doc-master` | Document pipeline orchestration |
| `/mmos-squad` | MMOS mind cloning squad |
| `/map` | MMOS mind mapping |
| `/Ralph` | Ralph Wiggum completeness checker |
| `/synapse` | SYNAPSE context engine management |
| `/extract-knowledge` | Knowledge extraction from materials |
| `/bilhon-docs` | BILHON document generation |
| `/merge-aios` | Merge AIOS Core staging content to final locations |

## Agents

Defined in `agents/AGENT-INDEX.yaml`, activated via slash commands.

| Type | Count | Purpose |
|------|-------|---------|
| CARGO | 29+ | Functional roles (Sales, Marketing, Ops) |
| MINDS | 5+ | Expert mind clones |
| CONCLAVE | 3 | Multi-perspective deliberation |
| SYSTEM | 2 | JARVIS, Agent-Creator |
| AIOS Core | 11 | Dev squad (dev, qa, architect, pm, po, sm, analyst, devops, data-engineer, ux-design-expert, aios-master) |
| Doc Pipeline | 9 | Document generation (doc-master thru doc-orchestrator) |
| Media Buyer | 5 | Paid traffic (ad-midas, performance-analyst, creative-analyst, pixel-specialist) |
| MMOS | 9 | Mind cloning (mind-mapper, cognitive-analyst, identity-analyst, etc.) |
| Design | 3 | Design system (design-system, bilhon-design-agent, design-review) |
| Fusion | 11 | Repo merging (fusion-commander, merge-arbiter, etc.) |

### Agent Definitions Location

| Source | Path | Protected |
|--------|------|-----------|
| AIOS Core agents | `.aiox/development/agents/*.md` | Gitignored (.aiox/) |
| Mega-brain agents | `.aiox/development/agents/mega-brain/` | Gitignored (.aiox/) |
| Claude Code agent types | `.claude/agents/*.md` (24 files) | Gitignored (.claude/agents/) |

### Agent Activation

Agents activated with `@agent-name`: `@dev`, `@qa`, `@architect`, `@pm`, `@po`, `@sm`, `@analyst`, `@devops`.

### Agent Memory (NON-NEGOTIABLE)

Agent memory lives EXCLUSIVELY in `.claude/agent-memory/{slug}/MEMORY.md`.

- Agent definition (`.aiox/`) \!= Runtime memory (`.claude/agent-memory/`)
- NEVER store memory inside agent definition files
- NEVER create CLAUDE.md for memory (guard hook blocks automatically)

### Agent Authority Rules

| Agent | Exclusive Authority | Blocked for Others |
|-------|--------------------|--------------------|
| @devops (Gage) | Git Push, PR, CI/CD | `git push`, `gh pr create` |
| @qa (Rex) | Quality Approval | Mark story Ready without QA |
| @pm (Max) | PRD Approval | Approve requirements without PM |
| @architect (Aria) | Architecture Decisions | Stack/infra without Architect |
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

30+ active hooks across two locations (Python 3, stdlib + PyYAML only).
Configured in `settings.json` (gitignored).

| Location | Count | Protected |
|----------|-------|-----------|
| `.claude/hooks/` | 30 | Tracked (mega-brain native) |
| `.aiox/hooks/` | 34 | Gitignored (AIOS-exclusive) |

| Event | Key Hooks (.claude/) | AIOS Hooks (.aiox/) |
|-------|---------------------|--------------------------|
| SessionStart | `session_start.py`, `inbox_age_alert.py`, `skill_indexer.py` | `memory_bank_loader.py`, `elicitation_reset.py`, `token_monitor.py` |
| UserPromptSubmit | `skill_router.py`, `quality_watchdog.py`, `memory_updater.py` | `elicitation_gate.py`, `document_trigger.py`, `council_logger.py` |
| PreToolUse | `creation_validator.py`, `claude_md_guard.py` | - |
| PostToolUse | `post_tool_use.py`, `enforce_dual_location.py` | `subagent_tracker.py`, `post_output_validator.py` |
| Stop | `stop_hook_completeness.py`, `ralph_wiggum.py` | - |
| SessionEnd | `session_end.py`, `agent_memory_persister.py` | `session_log.py`, `token_monitor.py` |

## Rules (Lazy Loading)

Detailed rules loaded on-demand via keyword matching from `.claude/rules/`:

| Group | Topics | File |
|-------|--------|------|
| PHASE-MANAGEMENT | phases, pipeline, batch | RULE-GROUP-1.md |
| PERSISTENCE | sessions, save, resume | RULE-GROUP-2.md |
| OPERATIONS | parallel, templates, KPIs | RULE-GROUP-3.md |
| PHASE-5 | agents, dossiers, cascading | RULE-GROUP-4.md |
| VALIDATION | source-sync, integrity | RULE-GROUP-5.md |
| AUTO-ROUTING | skills, sub-agents, GitHub | RULE-GROUP-6.md |

### AIOS Core Rules (migrated, gitignored)

| Rule | Purpose |
|------|---------|
| `semantic-routing.md` | Auto-routes user requests to correct agent via intent |
| `architecture-rules.md` | Agent memory architecture, definition vs runtime |
| `agent-commands-rules.md` | Agent command syntax and activation |
| `aios-native-knowledge.md` | AIOS native knowledge base |
| `mcp-usage.md` | MCP server governance and tool selection priority |

## AIOS Core Integration

Content migrated from `aios-core` repo. All AIOS content is local-only (gitignored + npm-excluded).

### Protection Layers

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Git | `.gitignore` entries per file | Each migrated file individually listed |
| npm | `.npmignore` + `package.json` negations | `!` patterns exclude each file |
| CI/CD | `.aiox/` never in git = never in checkout | No workflow references |
| Pre-publish | `bin/pre-publish-gate.js` blocks `.aiox/` content | Physical block before npm publish |

### Protocols

| Protocol | Path | Purpose |
|----------|------|---------|
| Constitution | `.aiox/core/protocols/constitution.yaml` | Non-negotiable principles |
| Agent Index | `.aiox/core/protocols/agent-index.yaml` | Agent catalog |
| Orchestration | `.aiox/core/protocols/orchestration-rules.yaml` | Agent handoff rules |

### Semantic Routing

User requests are automatically routed to the correct agent via intent matching.
Rules: `.claude/rules/semantic-routing.md`

Priority chain: `@agent` explicit > Intent semantic > Keyword matching > Skill matching > `@aios-master` (fallback)

### Development Skills (AIOS)

Located in `.aiox/development/skills/`:

| Skill | Purpose |
|-------|---------|
| `writing-plans` | Exact implementation plans (2-5 min tasks) |
| `subagent-driven-development` | Execute plans with @dev/@qa dispatch |
| `test-driven-development` | RED-GREEN-REFACTOR enforced |
| `systematic-debugging` | Root cause investigation (4-phase) |
| `media-buyer/` | 18 skills from 47 frameworks (5 experts) |
| `doc-generation/` | Document pipeline skills |
| `mmos-cognitive-analysis/` | Mind cloning analysis |

## Teaching Mode (SEMPRE ATIVO)

Ao criar, modificar ou explicar qualquer elemento tecnico, OBRIGATORIAMENTE inclua:

1. TREE ARQUITETURAL COMPLETO mostrando ONDE o elemento mora (desde a raiz do projeto)
2. RAIO-X COMPLETO com tabela: o que e, onde fica, dentro de que, ligado a que, quem aciona, o que tem dentro, formato e porque, o que quebra se apagar, alternativa possivel
3. MAPA DE CONEXOES VISUAL com setas e verbos claros (chama, dispara, usa, le, escreve)
4. ANALOGIA COM MUNDO REAL usando operacao de empresa (vendas, marketing, gestao, CRM)
5. DECISOES TECNICAS EXPLICADAS: o que decidiu, por que, alternativa existente, consequencia da escolha

### Regras de linguagem:
- Nunca encurtar caminhos sem mostrar o contexto completo desde a raiz
- Nunca usar termo tecnico sem traducao imediata entre parenteses
- Nunca mencionar pasta sem mostrar o que tem dentro dela
- Ir ate 2 niveis de profundidade no "porque". No 3o nivel, perguntar se quer aprofundar
- Usar linguagem de negocios como analogia primaria
- Sempre responder a pergunta antes que ela seja feita

### Referencia completa da skill:
Consultar `.claude/skills/teaching/SKILL.md` para exemplos e formato detalhado.

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
- Agent memory lives EXCLUSIVELY in `.claude/agent-memory/{slug}/MEMORY.md`
- Guard hook (`claude_md_guard.py`) blocks unsanctioned CLAUDE.md creation
