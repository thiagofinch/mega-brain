# Mega Brain - AI Knowledge Management System

## What is Mega Brain?

AI-powered system that transforms expert materials (videos, PDFs, transcriptions) into structured playbooks, DNA schemas, and mind-clone agents. Powered by JARVIS orchestrator. Built on [AIOS Core](https://github.com/SynkraAI/aios-core) framework principles.

## Quick Start

1. Run `npx mega-brain-ai setup` (auto-triggers on first use if `.env` missing)
2. Fill in API keys when prompted (only `OPENAI_API_KEY` is required)
3. Use `/jarvis-briefing` to see system status

## Architecture

```
mega-brain/
├── .claude/               -> Claude Code integration (primary config)
│   ├── commands/              -> 193 commands
│   │   └── AIOS/agents/       -> 80 AIOS agent definitions (.md)
│   ├── hooks/                 -> 40 hooks (Python 3, unified)
│   ├── skills/                -> 52 skill directories
│   ├── rules/                 -> 21 rules (lazy-loaded by keyword)
│   ├── agent-memory/          -> Runtime memory per agent (gitignored)
│   └── aios/                  -> AIOS runtime state (gitignored)
├── core/                  -> Engine
│   ├── tasks/                 -> Atomic tasks
│   ├── workflows/             -> YAML orchestration
│   ├── intelligence/          -> Python scripts + RAG system (13 files)
│   ├── protocols/             -> Pipeline, conclave, DNA protocols
│   ├── schemas/               -> JSON schemas
│   ├── jarvis/                -> JARVIS Soul + DNA
│   └── templates/             -> Agent + log templates
├── agents/                -> Knowledge agents (conclave, cargo, minds)
├── docs/                  -> Documentation, PRDs, plans
├── bin/                   -> CLI tools (npm)
├── inbox/                 -> Raw materials (L3, gitignored)
├── knowledge/             -> Knowledge base (L3, gitignored)
└── logs/                  -> Session logs (L3, gitignored)
```

## Plan Mode

Plans MUST be saved to `docs/plans/` (not ~/.claude/plans/).
When in plan mode, save the plan file to: `docs/plans/YYYY-MM-DD-description.md`

### Layer System

| Layer | Content | Git Status |
|-------|---------|------------|
| L1 (Community) | core/, agents/conclave, .claude/, bin/, docs/ | Tracked (npm package) |
| L2 (Pro) | agents/cargo, agents/sub-agents | Tracked (premium) |
| L3 (Personal) | inbox/, knowledge/, .env, agents/minds | Gitignored |

## DNA Schema (5 Knowledge Layers)

| Layer | Name | Description |
|-------|------|-------------|
| L1 | PHILOSOPHIES | Core beliefs and worldview |
| L2 | MENTAL-MODELS | Thinking and decision frameworks |
| L3 | HEURISTICS | Practical rules and decision shortcuts |
| L4 | FRAMEWORKS | Structured methodologies and processes |
| L5 | METHODOLOGIES | Step-by-step implementations |

## Commands

### Mega Brain Native

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

### AIOS Agent Commands

Activate any of the 80 AIOS agents via slash command:

```
/AIOS:agents:{agent-name}    e.g. /AIOS:agents:architect
```

Additional AIOS commands: `/doc-master`, `/mmos-squad`, `/map`, `/synapse`, `/extract-knowledge`, `/bilhon-docs`

## Agent System

### Agent Definitions — Single Location

All 80 AIOS agent definitions live in one place:

```
.claude/commands/AIOS/agents/     <- 80 .md files, git tracked
```

> **IMPORTANT:** The `.aiox/` directory does NOT exist in this project. All AIOS content has been migrated into `.claude/`. References to `.aiox/` in rules files are legacy and should be ignored in favor of the actual paths documented here.

### Agent Categories

| Type | Count | Purpose | Activation |
|------|-------|---------|------------|
| AIOS Core | 11 | Dev squad | `@dev`, `@qa`, `@architect`, `@pm`, `@po`, `@sm`, `@analyst`, `@devops`, `@data-engineer`, `@ux-design-expert`, `@aios-master` |
| CARGO (Sales) | 4 | Sales roles | `@closer`, `@bdr`, `@sds`, `@lns` |
| CARGO (C-Level) | 4 | Executive roles | `@cro`, `@cfo`, `@cmo`, `@coo` |
| MINDS (DNA) | 7+ | Expert mind clones | `@cole-gordon`, `@alex-hormozi`, `@jeremy-miner`, `@jeremy-haynes` |
| CONCLAVE | 3 | Multi-perspective deliberation | `/conclave` |
| Doc Pipeline | 9 | Document generation | `@doc-master` thru `@doc-orchestrator` |
| Media Buyer | 5 | Paid traffic | `@ad-midas`, `@performance-analyst`, `@creative-analyst` |
| MMOS | 9 | Mind cloning pipeline | `@mind-mapper`, `@cognitive-analyst`, `@identity-analyst` |
| Design | 3 | Design system | `@bilhon-docs`, `@obsidian-ui`, `@design-system` |
| Hormozi Squad | 12 | Hormozi-method specialists | `@hormozi-offers`, `@hormozi-closer`, etc. |
| NERO Squad | 8 | Advanced analysis | `@nero-lead`, `@nero-architect`, etc. |
| Copy | 1 | Copywriting orchestrator | `@copy-chief` |

### Agent Activation Syntax

| Method | Syntax | Example |
|--------|--------|---------|
| @mention | `@agent-name` | `@architect` |
| Slash command | `/AIOS:agents:{name}` | `/AIOS:agents:dev` |
| Star command | `*task-name` | `*analyze-impact` |
| Semantic routing | Automatic via keywords | "analisa arquitetura" → `@architect` |

### Agent Memory (NON-NEGOTIABLE)

Agent memory lives EXCLUSIVELY in `.claude/agent-memory/{slug}/MEMORY.md`.

- Agent definition (`.claude/commands/AIOS/agents/`) != Runtime memory (`.claude/agent-memory/`)
- NEVER store memory inside agent definition files
- NEVER create CLAUDE.md for memory (guard hook blocks automatically)

### Agent Authority Rules

| Agent | Exclusive Authority | Blocked for Others |
|-------|--------------------|--------------------|
| @devops (Gage) | Git Push, PR, CI/CD | `git push`, `gh pr create` |
| @qa (Rex) | Quality Approval | Mark story Ready without QA |
| @pm (Max) | PRD Approval | Approve requirements without PM |
| @architect (Aria) | Architecture Decisions | Stack/infra without Architect |

### Semantic Routing

User requests are automatically routed to the correct agent via intent matching.
Rules: `.claude/rules/semantic-routing.md`

Priority chain: `@agent` explicit > Intent semantic > Keyword matching > Skill matching > `@aios-master` (fallback)

## Hooks System

40 hooks in `.claude/hooks/` (Python 3, stdlib + PyYAML only).
Configured in `settings.json` (gitignored).

| Event | Key Hooks |
|-------|-----------|
| SessionStart | `session_start.py`, `skill_indexer.py`, `inbox_age_alert.py`, `memory_bank_loader.py`, `elicitation_reset.py`, `token_monitor.py` |
| UserPromptSubmit | `skill_router.py`, `quality_watchdog.py`, `memory_updater.py`, `memory_hints_injector.py`, `elicitation_gate.py`, `document_trigger.py`, `council_logger.py` |
| PreToolUse | `creation_validator.py`, `claude_md_guard.py`, `enforce_plan_mode.py` |
| PostToolUse | `post_tool_use.py`, `enforce_dual_location.py`, `post_batch_cascading.py`, `subagent_tracker.py`, `post_output_validator.py` |
| Stop | `stop_hook_completeness.py`, `ralph_wiggum.py` |
| SessionEnd | `session_end.py`, `agent_memory_persister.py`, `session_log.py`, `token_monitor.py` |

## Rules (Lazy Loading)

21 rules loaded on-demand via keyword matching from `.claude/rules/`:

| Group | Topics | File |
|-------|--------|------|
| PHASE-MANAGEMENT | phases, pipeline, batch | RULE-GROUP-1.md |
| PERSISTENCE | sessions, save, resume | RULE-GROUP-2.md |
| OPERATIONS | parallel, templates, KPIs | RULE-GROUP-3.md |
| PHASE-5 | agents, dossiers, cascading | RULE-GROUP-4.md |
| VALIDATION | source-sync, integrity | RULE-GROUP-5.md |
| AUTO-ROUTING | skills, sub-agents, GitHub | RULE-GROUP-6.md |
| GSD | planning, implementation | RULE-GSD-MANDATORY.md |
| ANTHROPIC | hooks, skills, MCP standards | ANTHROPIC-STANDARDS.md |
| AGENT-COGNITION | reasoning, depth-seeking, DNA cascade | agent-cognition.md |
| AGENT-INTEGRITY | traceability, zero invention | agent-integrity.md |
| EPISTEMIC | anti-hallucination, confidence levels | epistemic-standards.md |
| SEMANTIC-ROUTING | intent matching, agent activation | semantic-routing.md |
| ARCHITECTURE | file placement, memory separation | architecture-rules.md |
| AGENT-COMMANDS | @syntax, *commands, /skills | agent-commands-rules.md |
| AIOS-KNOWLEDGE | constitution, agent registry | aios-native-knowledge.md |
| MCP-USAGE | tool priority, Docker MCP | mcp-usage.md |
| MCP-GOVERNANCE | server admin, credentials | mcp-governance.md |
| STATE-MGMT | MISSION-STATE, session lifecycle | state-management.md |
| PIPELINE | processing phases | pipeline.md |
| LOGGING | dual-location, batch templates | logging.md |
| CLAUDE-LITE | quick-start core rules | CLAUDE-LITE.md |

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

## Tool Preferences (aios-core standard)

ALWAYS prefer native Claude Code tools over MCP or shell equivalents:

| Task | Use This | Not This |
|------|----------|----------|
| Read files | `Read` tool | `cat`, `head`, MCP |
| Write files | `Write` / `Edit` tools | `echo >`, `sed`, MCP |
| Search files | `Glob` tool | `find`, `ls` |
| Search content | `Grep` tool | `grep`, `rg` |
| Run commands | `Bash` tool | MCP docker-gateway |

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

Referencia completa: `.claude/skills/teaching/SKILL.md`

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

## CLAUDE.md Policy

- Only 2 CLAUDE.md files are valid: root `CLAUDE.md` and `.claude/CLAUDE.md` (this file)
- NEVER create CLAUDE.md in data or code subdirectories
- Agent memory lives EXCLUSIVELY in `.claude/agent-memory/{slug}/MEMORY.md`
- Guard hook (`claude_md_guard.py`) blocks unsanctioned CLAUDE.md creation
