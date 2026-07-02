# Mega Brain — AI Knowledge Management System

## What is Mega Brain?

AI-powered system that transforms expert materials (videos, PDFs, transcriptions) into structured playbooks, DNA schemas, and mind-clone agents. Powered by JARVIS orchestrator.

## Quick Start

1. Run `npx @thiagofinch/mega-brain@latest install`
2. Fill in API keys when prompted (all optional — `OPENAI_API_KEY` recommended for video/audio transcription)
3. Use `/jarvis-briefing` to see system status
4. To update without losing data: `npx @thiagofinch/mega-brain@latest update`

## Constitution (Supreme Law)

The Mega Brain Constitution applies. 14 non-negotiable principles:

| Article | Principle | Type |
|---------|-----------|------|
| I | CLI First | NON-NEGOTIABLE |
| II | Agent Authority | NON-NEGOTIABLE |
| III | Story-Driven Development | MUST |
| IV | No Invention | MUST |
| V | Quality First | MUST |
| VI | Absolute Imports | SHOULD |
| VII | Autonomous Scheduling Governance | MUST |
| VIII | BU Accountability | MUST |
| IX | Journey Log Mandatory | MUST |
| X | Artifact Contracts | MUST |
| XI | Squad-First Portability | NON-NEGOTIABLE |
| XII | Pipeline MCE Integrity | MUST |
| XIII | Knowledge Bucket Isolation | MUST |
| XIV | Workspace Layer Hierarchy | MUST |

Reference: `mega-brain-core/constitution.md`

## Governance Hierarchy

```
Constitution (immutable law — Articles I-XIV)
  → CLAUDE.md (nervous system index — this file)
    → Atom Rules (lazy-loaded by keyword — 14 files)
      → Synapse Engine (YAML rule digest)
        → Hooks (automated enforcement — 92 wired)
          → Skills (operational capabilities)
            → Squads (execution units)
              → Workspace + Knowledge (business data)
```

## Architecture

```
mega-brain/
├── mega-brain-core/         → Mega Brain framework (constitution, agents, tasks, workflows)
├── engine/             → Mega Brain engine (pipeline, RAG, speakers, dossier, jarvis)
├── infrastructure/     → CI/CD, deploy configs, integrations
├── .claude/            → Claude Code integration (hooks, skills, rules, settings)
├── squads/             → Execution units (MEGABRAIN-governed)
├── workspace/          → Business data (L0-L4 per business unit)
├── knowledge/          → Knowledge base (3 isolated buckets)
├── agents/             → AI agents (5 categories)
├── scripts/            → Operational scripts
├── tests/              → Test suites
├── docs/               → Plans, stories, architecture
├── logs/               → Session logs (gitignored)
├── artifacts/          → Pipeline outputs (gitignored)
├── .data/              → RAG indexes (gitignored)
└── processing/         → Pipeline artifacts (gitignored)
```

## Kernel Session Layer

How agents boot (5-step activation sequence):

1. Load `agent.md` — operational definition, commands, scope
2. Load `soul.md` — identity, voice, personality
3. Load `dna-config.yaml` — knowledge sources with weights
4. Load `memory.md` — accumulated experience, decisions
5. Checkpoint: "Am I responding as this agent would?"

Navigation chain: AGENT → SOUL → MEMORY → DNA → INSIGHTS → CHUNKS → SOURCE

> **Naming:** arquivos de agente external/business/personal sao lowercase (`agent.md`, `soul.md`, `memory.md`, `dna-config.yaml`). Cargo agents (`agents/external/cargo/`) mantêm convencao legada UPPERCASE (`MEMORY.md`). Spec completa: `docs/architecture/knowledge-agent-architecture.md`.

### Dossiers de tema — retrieve-on-demand (NAO entram no boot)

Dossiers de tema (`knowledge/external/dossiers/themes/*.md`) NAO sao carregados no boot do agente individual. Sao consultados sob demanda via RAG retrieve quando a query toca o tema, ou explicitamente invocados no Conclave/Roundtable como evidencia cruzada.

**Razao arquitetural:** isolamento de identidade. Carregar `dossier-filosofia-operacional.md` (que agrega Alex Hormozi, Jordan Lee, Cole Gordon, etc.) no boot do `@jordan-lee` contaminaria a identidade isolada com perspectivas de outros especialistas antes de qualquer query.

**Padrao de uso correto:**

```python
# Agente individual responde da sua filosofia DELE:
@jordan-lee → le filosofias.yaml dele → responde isolado

# Conclave invoca dossier de tema como evidencia cruzada:
@conclave roundtable "filosofia operacional" → modera retrieve cross-pessoa
```

**Implementacao:** ver `engine/intelligence/rag/searcher.py` para retrieve via bucket external; ver `engine/intelligence/pipeline/mce/theme_router.py` para resolucao de tema.

## Pipeline MCE

Mental Cognitive Extraction — 6 sequential, blocking phases:

| Phase | Name | Output |
|-------|------|--------|
| 0 | Ingestion Guard | Dedup verdict (NEW/SKIP/INCREMENTAL) |
| 1 | Download | Raw materials in inbox |
| 2 | Organization | Classified by source/type |
| 3 | De-Para | Planilha ↔ Computer sync |
| 4 | Pipeline | Batches → DNA extraction (L1-L10) |
| 4.5 | RAG Indexation | BM25 rebuild + RAG Indexation Mandatory (Art. XV) |
| 5b (opt-in) | GraphRAG Index | Build KnowledgeGraph + detect cross-person communities. Requires `MCE_GRAPHRAG_ENABLED=1`. Default: skipped. |
| 5 | Agents | Person/Cargo agents + dossiers |

Phase 0 runs automatically before classification. Prevents duplicate processing via identity (source ID) + integrity (body hash + word count). Registry: `.data/ingestion-registry.json`. Code: `engine/intelligence/pipeline/ingestion_guard.py`.

### Auto-orchestration model (STORY-MCE-ROUND-TRIP, 2026-05-13)

The pipeline is now end-to-end auto-orchestrated. Drop a file via `/ingest` and the system advances itself through CLASSIFIED → EXTRACTING → ... → S12 without manual `python3` invocations.

| Edge | What happens | Code |
|------|--------------|------|
| `/ingest <path>` | Executable slash invokes `python3 -u scripts/ingest-with-entity-discovery.py` with streaming stdout | `.claude/commands/ingest.md` + `scripts/ingest-with-entity-discovery.py` |
| **Speaker Visual Gate** (pre_07) | Gemini extracts speaker + subject from videos. Bypassed explicitly when `GEMINI_API_KEY` absent or `--skip-gemini` set — emits `[pre_07] BYPASSED (reason: ...)` line | `engine/intelligence/pipeline/video/pipeline.py::extract_local_video_via_gemini` |
| **Entity Discovery dual** (pre_08) | Reconciles filename evidence with Speaker Gate output via `infer_entities()` → routes to `external/{author}/` or `business/{subject}/` | `engine/intelligence/pipeline/batch_auto_creator.py::infer_entities` |
| **Filename sidecar** | Merged `{file}.entity-discovery.json` (schema v1.1.0). N1 portion = `filename_original`, `tokens_dropped`, `normalizer_rule`. N5 portion = `decision`, `gemini_used`, `gemini_bypassed_reason`. Disjoint field groups, last-writer-wins safe | `engine/intelligence/pipeline/filename_sidecar_schema.json` |
| **CLASSIFIED → S3 auto-advance** | `batch_auto_creator` emits `.advance-trigger.json`. PostToolUse hook listener (`<500ms`) detaches `cmd_auto_advance(slug)` subprocess | `.claude/hooks/pipeline_orchestrator.py::_route_advance_trigger` + `engine/intelligence/pipeline/mce/orchestrate.py::cmd_auto_advance` |
| **Cron backstop** | `python3 -m engine.intelligence.pipeline.mce.orchestrate auto-advance <slug>` recovers within 5min if hook missed | same |
| **MCE log emission** | `cmd_finalize` calls `log_generator.generate_mce_log()`; stdout prints path; exception in log_generator is non-fatal (Art. XII) | `engine/intelligence/pipeline/mce/orchestrate.py::cmd_finalize` |

`/ingest --process` chains the full pipeline (orchestrate.cmd_full) as a streaming subprocess so chat sees live state. Cascade categories are now loaded from `agents/_registry/ecosystem-registry.yaml` (no hardcoded `REAL_CATEGORIES`).

DNA Schema (10 Layers):

| Layer | Name | Description |
|-------|------|-------------|
| L1 | PHILOSOPHIES | Core beliefs and worldview |
| L2 | MENTAL-MODELS | Thinking and decision frameworks |
| L3 | HEURISTICS | Practical rules and decision shortcuts |
| L4 | FRAMEWORKS | Structured methodologies and processes |
| L5 | METHODOLOGIES | Step-by-step implementations |
| L6 | BEHAVIORAL-PATTERNS | Behavioral patterns and triggers |
| L7 | VALUES-HIERARCHY | Values hierarchy and priorities |
| L8 | VOICE-DNA | Voice DNA, signature phrases, states |
| L9 | OBSESSIONS | Recurring obsessions and cognitive priorities |
| L10 | PARADOXES | Internal paradoxes and productive contradictions |

## Knowledge Architecture (3 Buckets)

| Bucket | Path | Content | RAG Index |
|--------|------|---------|-----------|
| External | `knowledge/external/` | Expert courses, books, podcasts | `.data/rag_index/` |
| Business | `knowledge/business/` | Meetings, calls, SOPs | `.data/rag_business/` |
| Personal | `knowledge/personal/` | Notes, email, reflections | `knowledge/personal/index/` |

Buckets are **isolated** — no cross-contamination (Constitution Art. XIII).

## Workspace (L0-L4)

```
workspace/businesses/{bu}/
  L0-identity/    (TTL: 365d) — company DNA, legal, founder
  L1-strategy/    (TTL: 90d)  — ICP, BMC, pricing, offerbook
  L2-tactical/    (TTL: 60d)  — brand, campaigns, acceleration
  L3-product/     (TTL: 30d)  — product specs, roadmaps
  L4-operational/ (TTL: 7d)   — day-to-day operations
```

Golden Rule: L0 > L1 > L2 > L3 > L4 (higher layers override lower).

## MEGABRAIN Composition

Token → Atom → Molecule → Organism → Template → Instance

Canonical refs: `squads/mega-brain/data/composition-rules.yaml` | `token-registry.yaml`

> **Nota de aplicabilidade:** MEGABRAIN Composition aplica-se EXCLUSIVAMENTE a squads em `squads/`. Agentes de conhecimento (`agents/external/`, `agents/cargo/`, `agents/business/`, `agents/personal/`) seguem o **Kernel Session Layer (KSL)** — ver `docs/architecture/knowledge-agent-architecture.md` para spec completa.

## Atom Rules (lazy-loaded by keyword)

| Atom | Concern | Keywords |
|------|---------|----------|
| atom-pipeline | MCE phases, batching, logging | fase, pipeline, batch |
| atom-pipeline-phase5 | Phase 5 templates, isolation | agente, dossier, cascateamento |
| atom-session | Persistence, state, plan mode | sessão, save, resume |
| atom-agents | Authority, cognition, integrity | agent, authority, handoff |
| atom-workspace | L0-L4, artifacts, hub governance | workspace, artifact, product |
| atom-directory | Filesystem contract, routing | directory, path, bucket |
| atom-standards | Anthropic, IDS, skills, security | standard, hook, skill, IDS |
| atom-routing | Skill/agent auto-routing | skill, auto-trigger, routing |
| atom-quality | Quality gates, CodeRabbit | validate, quality, gate |
| atom-github | GitHub workflow, story lifecycle | github, git, push, pr |
| atom-workflow | SDC, QA Loop, Spec Pipeline | workflow, story, SDC |
| atom-mcp | MCP governance, tool priority | MCP, docker, gateway |
| atom-squads | Squad structure, MEGABRAIN fields | squad, MEGABRAIN, config.yaml |
| atom-operations | Parallelism, company context | terminal, empresa, template |

## Agents

| Type | Path | Source | Example |
|------|------|--------|---------|
| External | `agents/external/` | `knowledge/external/` | Alex Hormozi |
| Business | `agents/business/` | `knowledge/business/` | Team members |
| Personal | `agents/personal/` | `knowledge/personal/` | Founder |
| Cargo | `agents/cargo/` | Multiple buckets | CFO, CRO, Closer |
| System | `agents/system/` | Config-driven | JARVIS, Conclave |

Registry: `agents/_registry/ecosystem-registry.yaml`

## Hooks System

44+ active hooks in `.claude/hooks/` (Python 3, stdlib + PyYAML only).

> Note: `pipeline_checkpoint.py` archived MCE-5.1 — superseded by Wave 2 hooks (`checkpoint_observer.py` + `enforcement_guard.py`).

| Event | Count | Key Hooks |
|-------|-------|-----------|
| SessionStart | 5 | session_start, skill_indexer, inbox_age_alert, startup_health |
| UserPromptSubmit | 7 | skill_router, quality_watchdog, memory_updater, enforce_plan_mode |
| PreToolUse | 7 | creation_validator, claude_md_guard, directory_contract_guard, pipeline_merge_guard |
| PostToolUse | 14 | pipeline_orchestrator, post_batch_cascading, agent_memory_persister |
| Stop | 9 | delivery_guardian, session_end, stop_workspace_audit |

## Post-Compare Architecture State (2026-04-16)

Pipeline `/compare-architecture` completou Fases 0-6. 46 capabilities analisadas, decisoes aprovadas.

### Mudancas ja aplicadas nesta sessao
- 7 hooks corrigidos (paths `core/` -> `engine/`)
- Art. VII atualizado (L3 permitido para pipeline)
- ADR-002 reescrito (workspace != buckets)
- 3 ADRs criados (BrainEngine, Category Schema, Automated Pipeline)

### Decisoes arquiteturais em vigor
- Embedding canonico: OpenAI text-embedding-3-large 1536d
- Memoria = tipo de pagina no backend (consolidar 5 hooks em 1)
- BrainEngine como camada de query (filesystem para edicao humana)
- Scheduler real para pipeline autonomo 24/7
- Operations-as-objects como fonte unica para CLI + MCP

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

## Configuration

- **`.env`** is the ONLY source of truth for credentials
- Run `/setup` to configure interactively
- Never hardcode API keys anywhere
- `.mcp.json` uses `${ENV_VAR}` syntax for MCP servers

| Key | Purpose | Required? |
|-----|---------|-----------|
| `OPENAI_API_KEY` | Whisper transcription | Recommended |
| `VOYAGE_API_KEY` | Semantic embeddings (RAG) | Recommended |
| `GOOGLE_CLIENT_ID` | Drive import | Optional |

## Security

1. **NEVER** hardcode API keys or tokens in code
2. **ALWAYS** use `.env` for credentials (gitignored)
3. `git push` is blocked by pre-push hook — delegate to @devops

## Conventions

- Folders: lowercase (`inbox`, `system`)
- Config files: SCREAMING-CASE (`STATE.json`, `MEMORY.md`)
- Python scripts: snake_case, use `pathlib.Path`
- Skills: kebab-case directories (`knowledge-extraction/`)

## Layer System

This cloned repository IS the complete product — there is no community/pro split. The table below describes only how files are tracked vs. kept local.

| Layer | Content | Git Status |
|-------|---------|------------|
| Tracked | engine/, agents/conclave, agents/cargo, knowledge/external/ (populated), .claude/, bin/, docs/ | Tracked (npm package) |
| Local | .data/, .env, agents/external/, knowledge/personal/ | Gitignored |

## Teaching Mode (ALWAYS ACTIVE)

When creating, modifying, or explaining any technical element, MUST include:

1. Tree showing WHERE the element lives (from project root)
2. X-Ray table: what it is, where it lives, what it connects to, who triggers it, what's inside, format and why, what breaks if deleted
3. Connection map with arrows and clear verbs (calls, triggers, uses, reads, writes)
4. Real-world analogy using business operations (sales, marketing, management)
5. Technical decisions explained: what, why, alternative, consequence

Rules:
- Never shorten paths without full context from root
- Never use technical term without immediate translation
- Never mention a folder without showing what's inside
- Go 2 levels deep on "why". At 3rd level, ask if user wants to go deeper.

Full reference: `.claude/skills/teaching/SKILL.md`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Hook failed" | Check Python 3 is in PATH |
| ".env not found" | Run `npx @thiagofinch/mega-brain@latest setup` |
| "Permission denied on git push" | By design — use branch + PR workflow |
| Skills not auto-activating | Check `SKILL-INDEX.json` is generated on SessionStart |

## Service-Capability Contract (ENFORCED)

Todo novo diretório criado em `services/` DEVE ter uma entry correspondente em `agents/_registry/capability-registry.yaml` antes de ser considerado operacional.

**Regra:** Sem capability declarada → service não existe para o Tool Intelligence Layer.

Verificar gaps: `CLAUDE_PROJECT_DIR=$(pwd) python3 .claude/hooks/discover_capability_gaps.py`
Registrar novo service: adicionar entry em `agents/_registry/capability-registry.yaml` + rodar `python3 .claude/hooks/sync_capability_status.py`

## Supabase Role (2026-05-28)

Supabase = reactive mirror parcial do filesystem (NAO source of truth). Filesystem e SOT absoluto.
Doc canonico: `docs/architecture/supabase-role.md`

## CLAUDE.md Policy

- Only 2 CLAUDE.md files are valid: root `CLAUDE.md` and `.claude/CLAUDE.md` (this file)
- NEVER create CLAUDE.md in data or code subdirectories
- Agent memory lives in `.claude/jarvis/` and `.claude/skills/`
