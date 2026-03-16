# Mega Brain -- System Architecture Document

> **Version:** 1.0.0
> **Date:** 2026-03-14
> **Package:** mega-brain-ai v1.4.0
> **Author:** Brownfield Discovery Phase 1 -- The Architect
> **Status:** ACTIVE -- drives all downstream decisions

---

## 1. Executive Summary

Mega Brain is an AI-powered Knowledge Management System that transforms expert materials
(video transcripts, PDFs, course content, meeting recordings) into structured knowledge
artifacts: DNA schemas, mind-clone agents, playbooks, and dossiers. The system is orchestrated
by a JARVIS personality layer running inside Claude Code, with 37 Python hooks, 90+ skills,
and a 5-phase pipeline for knowledge extraction.

**Key Numbers:**

| Metric | Value |
|--------|-------|
| Python intelligence code | ~29,640 lines across 120+ modules |
| Claude Code hooks | 37 active Python scripts |
| Skills | 90+ directories (many externally injected, ~55 native) |
| Agents | 22 registered (5 mind clones, 14 cargo, 3 conclave) |
| Tests | 50 collected (pytest) |
| Node.js dependencies | 6 production, 2 dev |
| Python dependencies | 1 required (PyYAML), 11 optional |
| MCP servers | 4 configured |
| ROUTING keys in paths.py | 100+ output routing constants |
| Rules files | 17 markdown rule documents |

**Architecture Style:**
- Monorepo with layer-based access control (L1 Community / L2 Pro / L3 Personal)
- Distributed as an npm package with Python intelligence engine
- No database -- filesystem-only with JSON/YAML/Markdown as data formats
- RAG indexes (BM25 + optional vector) stored in `.data/`
- Claude Code hooks provide lifecycle enforcement (session, prompt, tool use, stop)

---

## 2. Tech Stack

### 2.1 Languages and Runtimes

| Component | Language | Version | Purpose |
|-----------|----------|---------|---------|
| CLI & Distribution | Node.js (ESM) | >= 18.0.0 | npm package, setup wizard, CLI entry point |
| Intelligence Engine | Python 3 | >= 3.11 (target 3.12) | All pipeline, RAG, agent, and hook logic |
| Configuration | YAML, JSON | N/A | Agent configs, schemas, state files |
| Knowledge Artifacts | Markdown | N/A | Agents, playbooks, dossiers, DNA docs |

### 2.2 Node.js Dependencies (package.json)

**Production (6):**

| Package | Version | Purpose |
|---------|---------|---------|
| `boxen` | ^7.1.0 | CLI box drawing |
| `chalk` | ^5.3.0 | Terminal colors |
| `fs-extra` | ^11.3.4 | Filesystem utilities |
| `gradient-string` | ^2.0.2 | CLI gradient text |
| `inquirer` | ^9.2.0 | Interactive prompts (setup wizard) |
| `ora` | ^7.0.0 | CLI spinners |

All 6 are CLI cosmetic / UX libraries. No business logic in Node.js.

**Dev Dependencies (2):**

| Package | Version | Purpose |
|---------|---------|---------|
| `execa` | ^9.6.1 | Process execution |
| `js-yaml` | ^4.1.1 | YAML parsing |

### 2.3 Python Dependencies (pyproject.toml)

**Required (1):**

| Package | Version | Purpose |
|---------|---------|---------|
| `PyYAML` | >= 6.0, < 7.0 | YAML config parsing (hooks + pipeline) |

**Optional Groups:**

| Group | Packages | Purpose |
|-------|----------|---------|
| `pipeline` | PyYAML | Pipeline processing |
| `speakers` | pyannote.audio, torch, torchaudio, numpy, scipy, assemblyai | Voice diarization, speaker ID |
| `rag` | voyageai, rank-bm25 | Vector embeddings, BM25 search |
| `dev` | pytest, pytest-cov, ruff, pyright | Testing, linting, type checking |

### 2.4 Tooling

| Tool | Config File | Purpose |
|------|-------------|---------|
| Ruff | pyproject.toml `[tool.ruff]` | Python linter + formatter (target py312) |
| Pyright | pyproject.toml `[tool.pyright]` | Python type checker (basic mode) |
| Pytest | pyproject.toml `[tool.pytest]` | Test runner (testpaths: `tests/python/`) |
| Biome | biome.json | JS/JSON linting (if present) |
| EditorConfig | .editorconfig | Cross-editor formatting |
| Gitleaks | .gitleaks.toml | Secret scanning |

---

## 3. Project Structure

### 3.1 Root Directory Tree

```
mega-brain/                         [ROOT]
|
|-- package.json                    Node.js package manifest (v1.4.0)
|-- pyproject.toml                  Python project config (v1.3.0 -- VERSION MISMATCH)
|-- requirements.txt                Python deps (pip install)
|-- requirements-hooks.txt          Hook-specific deps
|-- .gitignore                      Whitelist-based (685 lines, 7 blocks)
|-- .mcp.json                       MCP server configuration (gitignored)
|-- .env                            API keys (gitignored, never exists in repo)
|
|-- core/                           [L1] Intelligence engine (Python)
|-- agents/                         [L1/L2] AI agent definitions
|-- knowledge/                      [L1 scaffold / L2-L3 data] 3-bucket knowledge base
|-- workspace/                      [L1 template / L2 populated] Prescriptive ops layer
|-- bin/                            [L1] CLI executables (Node.js)
|-- reference/                      [L1] Documentation (replaces deprecated docs/)
|-- docs/                           [PROHIBITED per paths.py] Legacy, still has content
|-- system/                         [L1] JARVIS identity files
|-- artifacts/                      [L1 scaffold / L3 data] Pipeline outputs
|-- logs/                           [L1 scaffold / L3 data] Session and processing logs
|-- tests/                          [was L1, now gitignored in BLOCO 7]
|
|-- .claude/                        [L1] Claude Code integration layer
|   |-- CLAUDE.md                   Primary project instructions
|   |-- settings.json               Hook configuration (distributed)
|   |-- settings.local.json         Local hook overrides (gitignored)
|   |-- hooks/                      37 Python lifecycle hooks
|   |-- skills/                     90+ skill directories
|   |-- rules/                      17 rule documents (lazy-loaded)
|   |-- commands/                   50+ slash commands
|   |-- scripts/                    Utility scripts
|   |-- mission-control/            Pipeline state (gitignored)
|   |-- sessions/                   Session logs (gitignored)
|   |-- jarvis/                     JARVIS runtime state (gitignored)
|   `-- trash/                      Soft-delete destination
|
|-- .data/                          [L3] RAG indexes, knowledge graph, embeddings
|-- .planning/                      [gitignored BLOCO 7] GSD planning files
|-- processing/                     [L3] Pipeline intermediate artifacts
|-- research/                       [L3] Ad-hoc analysis outputs
`-- .aiox-core/                     [external] AIOX framework injection
```

### 3.2 Layer System

| Layer | Git Status | Content | Examples |
|-------|------------|---------|----------|
| **L1** (Community) | Tracked, npm-published | Engine, templates, CLI, hooks, rules | `core/`, `bin/`, `.claude/hooks/`, `agents/_templates/` |
| **L2** (Pro) | Tracked, premium repo | Populated knowledge + expert agents | `knowledge/external/dna/`, `agents/external/`, `agents/cargo/` |
| **L3** (Personal) | Gitignored | Runtime data, private content | `.data/`, `knowledge/personal/`, `logs/`, `.claude/sessions/` |

The `.gitignore` uses a **whitelist architecture** (line 24: `*` ignores everything, then `!` rules selectively allow). This is split into 7 blocks:
1. NEVER (secrets, dev artifacts)
2. L3 ONLY (runtime, personal)
3. External framework injections
4. ALLOW L1 (community/npm)
5. ALLOW L2 (premium)
6. DENY OVERRIDES (externally-injected skills/commands)
7. HYGIENE DENY (previously-tracked L3 content)

---

## 4. Core Engine Architecture

### 4.1 Directory Structure

```
core/
|-- __init__.py
|-- paths.py                        [CRITICAL] Centralized path registry (298 lines, 100+ ROUTING keys)
|
|-- intelligence/                   Main Python intelligence package
|   |-- __init__.py
|   |
|   |-- pipeline/                   Ingestion and processing pipeline
|   |   |-- autonomous_processor.py
|   |   |-- batch_auto_creator.py
|   |   |-- batch_governor.py
|   |   |-- bucket_processor.py
|   |   |-- bucket_router.py
|   |   |-- fireflies_config.py
|   |   |-- fireflies_sync.py
|   |   |-- inbox_organizer.py
|   |   |-- inbox_watcher.py
|   |   |-- insight_speaker_linker.py
|   |   |-- meeting_router.py
|   |   |-- memory_enricher.py
|   |   |-- pipeline_heal.py
|   |   |-- pipeline_router.py
|   |   |-- read_ai_*.py             (5 files: config, gardener, harvester, oauth, router)
|   |   |-- scope_classifier.py
|   |   |-- session_autosave.py
|   |   |-- smart_router.py
|   |   |-- sop_detector.py
|   |   |-- sync_package_files.py
|   |   |-- task_orchestrator.py
|   |   |-- workspace_sync.py
|   |   `-- mce/                    MCE (Mental Cognitive Extraction) sub-pipeline
|   |       |-- cache.py
|   |       |-- cli.py
|   |       |-- gemini_analyzer.py
|   |       |-- metadata_manager.py
|   |       |-- metrics.py
|   |       |-- orchestrate.py
|   |       |-- state_machine.py
|   |       `-- workflow_detector.py
|   |
|   |-- rag/                        RAG (Retrieval-Augmented Generation) system
|   |   |-- adaptive_router.py
|   |   |-- associative_memory.py
|   |   |-- bucket_query_router.py
|   |   |-- chunker.py
|   |   |-- evaluator.py
|   |   |-- graph_builder.py
|   |   |-- graph_query.py
|   |   |-- hybrid_index.py
|   |   |-- hybrid_query.py
|   |   |-- mcp_server.py           Exposes RAG as MCP tool
|   |   |-- ontology_layer.py
|   |   |-- pipeline.py
|   |   `-- self_rag.py
|   |
|   |-- agents/                     Agent generation and activation
|   |-- dossier/                    Dossier compilation and analysis
|   |-- entities/                   Entity detection and normalization
|   |-- retrieval/                  Context assembly and query analysis
|   |-- roles/                      SOW and skill generation
|   |-- speakers/                   Voice diarization and speaker ID
|   |-- utils/                      Inbox organization utilities
|   |-- validation/                 Layer auditing and JSON integrity
|   |
|   |-- memory_manager.py           Agent memory CRUD (603 lines)
|   `-- context_scorer.py           Context relevance scoring
|
|-- glossary/                       Domain glossaries (sales, marketing, finance, ops, digital)
|-- jarvis/                         JARVIS sub-agent definitions
|-- patterns/                       Role patterns, quality gates, trigger configs
|-- schemas/                        JSON schemas for state files
|-- tasks/                          Markdown task definitions (extract-dna, process-batch, etc.)
|-- templates/                      Agent, debate, log, phase prompt templates
`-- workflows/                      YAML workflow definitions (pipeline, conclave, ingest)
```

### 4.2 paths.py -- The Central Nervous System

`core/paths.py` is the single source of truth for all directory paths and output routing. It defines:

- **30+ path constants** (ROOT, CORE, AGENTS, WORKSPACE, KNOWLEDGE_EXTERNAL, etc.)
- **100+ ROUTING dictionary entries** mapping logical outputs to filesystem paths
- **Backward compatibility aliases** for renamed directories
- **PROHIBITED list** preventing writes to deprecated directories

All Python scripts importing from `core.paths` (26 files currently use it) get correct paths regardless of filesystem reorganization. Scripts that hardcode paths are considered technical debt.

### 4.3 Duplicate Module Problem

**21 Python modules** exist as duplicates -- once at `core/intelligence/` root and once inside the appropriate subdirectory. This is the largest code debt in the system:

| Root File | Subdirectory Copy | Module |
|-----------|-------------------|--------|
| `agent_trigger.py` | `agents/agent_trigger.py` | Agent triggering |
| `audit_layers.py` | `validation/audit_layers.py` | Layer auditing |
| `autonomous_processor.py` | `pipeline/autonomous_processor.py` | Autonomous processing |
| `bootstrap_registry.py` | `entities/bootstrap_registry.py` | Entity bootstrap |
| `business_model_detector.py` | `entities/business_model_detector.py` | Business model detection |
| `dossier_trigger.py` | `dossier/dossier_trigger.py` | Dossier triggers |
| `entity_normalizer.py` | `entities/entity_normalizer.py` | Entity normalization |
| `org_chain_detector.py` | `entities/org_chain_detector.py` | Org chain detection |
| `review_dashboard.py` | `dossier/review_dashboard.py` | Review dashboard |
| `role_detector.py` | `entities/role_detector.py` | Role detection |
| `session_autosave.py` | `pipeline/session_autosave.py` | Session autosave |
| `skill_generator.py` | `roles/skill_generator.py` | Skill generation |
| `sow_generator.py` | `roles/sow_generator.py` | SOW generation |
| `sync_package_files.py` | `pipeline/sync_package_files.py` | Package file sync |
| `task_orchestrator.py` | `pipeline/task_orchestrator.py` | Task orchestration |
| `theme_analyzer.py` | `dossier/theme_analyzer.py` | Theme analysis |
| `tool_discovery.py` | `roles/tool_discovery.py` | Tool discovery |
| `validate_json_integrity.py` | `validation/validate_json_integrity.py` | JSON validation |
| `validate_layers.py` | `validation/validate_layers.py` | Layer validation |
| `verify_classifications.py` | `validation/verify_classifications.py` | Classification verification |
| `viability_scorer.py` | `roles/viability_scorer.py` | Viability scoring |

These likely originated from a reorganization where files were copied into subdirectories but the originals were never removed.

---

## 5. Agent System Architecture

### 5.1 Agent Categories

```
agents/
|-- AGENT-INDEX.yaml                Registry (22 agents, auto-updated by hook)
|-- MASTER-AGENT.md                 Master agent definition
|-- persona-registry.yaml           Persona mapping
|-- _master-registry.yaml           Master registry
|
|-- external/                       [L2] Expert mind clones (14 persons)
|   |-- alex-hormozi/
|   |-- cole-gordon/
|   |-- jeremy-haynes/
|   |-- jeremy-miner/
|   |-- liam-ottley/
|   |-- sam-oven/
|   |-- richard-linder/
|   |-- jordan-lee/
|   |-- the-scalable-company/
|   |-- full-sales-system/
|   |-- g4-educacao/
|   |-- {your-collaborators}/        [L3 -- gitignored]
|   `-- _example/
|
|-- cargo/                          [L2] Functional role agents (12 categories)
|   |-- c-level/                    CFO, CMO, COO, CRO (full: AGENT+SOUL+MEMORY+DNA)
|   |-- sales/                      11 roles (closer, sds, bdr, lns, etc.)
|   |-- marketing/                  4 roles (paid-media, funnel-strategist, marketer, cmo)
|   |-- operations/                 3 roles (cfo, coo, sales-coordinator)
|   |-- hr/                         hr-director
|   |-- content/                    content-creator
|   |-- design/                     designer
|   |-- general/                    paid-media-specialist, sdr
|   |-- growth/                     media-buyer
|   `-- tech/                       data-analyst
|
|-- system/                         [L1] Infrastructure agents
|   |-- boardroom/                  Audio debate generation
|   |-- conclave/                   3 deliberative agents (critic, devil's advocate, synthesizer)
|   |-- knowledge-ops/              5 agents (Atlas, Echo, Forge, Lens, Sage)
|   `-- dev-ops/                    5 agents (Anvil, Beacon, Compass, Hawk, Rocket)
|
|-- business/                       [L3] Collaborator clones (empty)
|-- personal/                       [L3] Founder clone (empty)
|-- minds/                          [LEGACY] Old name for external/ (still has data)
|-- discovery/                      [L3] Auto-generated role tracking
|-- sua-empresa/                    [L3] Company operational structure
|-- constitution/                   [L1] Agent governance rules
`-- _templates/                     [L1] Agent creation templates (V3)
```

### 5.2 Agent File Standard

Each fully-formed agent has 4 files:

| File | Purpose | Required |
|------|---------|----------|
| `AGENT.md` | Operational definition (11 parts, Template V3) | Yes |
| `SOUL.md` | Identity, voice, personality | Yes |
| `MEMORY.md` | Accumulated experience and insights | Yes |
| `DNA-CONFIG.yaml` | Knowledge source configuration with weights | Yes |

Some cargo agents only have SOW files (`SOW.md` + `SOW.json`) without the full agent structure.

### 5.3 AGENT-INDEX.yaml Drift

The `AGENT-INDEX.yaml` still references `agents/minds/` paths and uses the label "minds" rather than "external". The auto-updater hook (`agent_index_updater.py`) is generating stale path references. Additionally, 20+ files still reference `agents/minds/` (the deprecated path).

---

## 6. Knowledge Architecture (3 Buckets)

### 6.1 Bucket Structure

```
knowledge/
|-- README.md
|
|-- external/                       Bucket 1: Expert Knowledge [L2]
|   |-- inbox/                      Raw expert materials [L3 -- gitignored content]
|   |-- dna/                        DNA schemas per person (5 layers each)
|   |   `-- persons/                alex-hormozi/, cole-gordon/, etc.
|   |-- dossiers/
|   |   |-- persons/                Per-person consolidations
|   |   |-- themes/                 Cross-person theme consolidations
|   |   `-- system/                 System-level dossiers
|   |-- playbooks/                  40+ actionable playbooks
|   |-- sources/                    Per-expert source compilations with raw/ subdirs
|   |-- TAG-RESOLVER.json           Tag-to-file mapping
|   `-- NAVIGATION-MAP.json         Knowledge navigation index
|
|-- business/                       Bucket 2: Company Operations [L3 except scaffold]
|   |-- inbox/                      Raw business materials
|   |   `-- {person-or-company}/    your-company/, collaborator-name/, etc.
|   |-- people/                     Collaborative DNA clones
|   |-- dossiers/                   Company/theme/person dossiers
|   |-- insights/                   Meeting insights (by-meeting, by-person, by-theme)
|   |-- narratives/                 Connected stories
|   |-- decisions/                  Strategic decisions (DEC-*.md)
|   `-- sops/                       Auto-detected process drafts
|
`-- personal/                       Bucket 3: Founder Cognitive [L3 ONLY]
    |-- inbox/                      Raw personal materials (per-company subdirs)
    |-- calls/
    |-- messages/
    |-- email/
    |-- cognitive/                   FOUNDER-DNA.md
    `-- PERSONAL-LOG.md
```

### 6.2 DNA Schema (5 Knowledge Layers)

Each expert's DNA is stored in `knowledge/external/dna/persons/{person}/` with:

| Layer | File | Description |
|-------|------|-------------|
| L1 | `FILOSOFIAS.yaml` | Crenças fundamentais e visão de mundo |
| L2 | `MODELOS-MENTAIS.yaml` | Frameworks de pensamento e decisão |
| L3 | `HEURISTICAS.yaml` | Regras práticas e atalhos decisórios |
| L4 | `FRAMEWORKS.yaml` | Metodologias estruturadas e processos |
| L5 | `METODOLOGIAS.yaml` | Implementações passo-a-passo |

Plus `DNA-CONFIG.yaml` for metadata and source references.

### 6.3 RAG Isolation

Each bucket has isolated RAG indexes to prevent cross-contamination:

| Bucket | RAG Index Path | Status |
|--------|---------------|--------|
| External (experts) | `.data/rag_expert/` | ACTIVE (BM25 built: 2,812 chunks) |
| Business (company) | `.data/rag_business/` | PATH DEFINED, index not built |
| Personal (founder) | `knowledge/personal/index/` | PATH DEFINED, index not built |

Vector indexes require `VOYAGE_API_KEY` which is not configured.

---

## 7. Workspace Architecture

### 7.1 Prescriptive Operations Layer

```
workspace/                          PRESCRIPTIVE -- how the company SHOULD function
|-- workspace.yaml                  Workspace manifest [gitignored -- populated]
|-- structure.yaml                  Org structure [gitignored -- populated]
|-- relationships.yaml              Business relationships [gitignored -- populated]
|
|-- _system/                        Internal config and references
|-- _templates/                     Validated SOPs (promoted from knowledge/business/sops/)
|-- inbox/                          Triage staging [deprecated per pipeline gaps, gitignored]
|
|-- businesses/                     Strategic DNA per Business Unit (12 folders each)
|   |-- {your-company}/
|   |-- {brand-1}/
|   |-- {brand-2}/
|   `-- {brand-N}/
|
|-- aios/                           AI Management space
|-- ops/                            Operations space (meetings, SOPs, sprints)
|-- delivery/                       Delivery space (prospection, projects, content)
|-- comercial/                      Commercial space (CRM, pipeline)
|-- gestao/                         Management space (legal, finance, admin)
|-- gente-cultura/                  People & Culture (OKRs, recruitment, team)
|-- marketing/                      Marketing (performance, campaigns, creative)
`-- strategy/                       Strategic decisions
```

7 departmental spaces mirror ClickUp workspace structure. Each business unit has 12 standard folders defined by `BU_TEMPLATE_DIRS` in `paths.py`.

---

## 8. Claude Code Integration

### 8.1 Hooks (37 Python Scripts)

All hooks are Python 3, stdlib + PyYAML only. Configured in `.claude/settings.json`.

**SessionStart (4 hooks):**

| Hook | Timeout | Purpose |
|------|---------|---------|
| `session_start.py` | 10s | Initialize session state |
| `skill_indexer.py` | 5s | Scan skills/sub-agents, generate SKILL-INDEX.json |
| `inbox_age_alert.py` | 5s | Warn about stale inbox items |
| `session_index.py` | 5s | Build session index |

**UserPromptSubmit (7 hooks):**

| Hook | Timeout | Purpose |
|------|---------|---------|
| `skill_router.py` | 10s | Auto-activate skills by keyword matching |
| `quality_watchdog.py` | 5s | Detect quality gaps in agent outputs |
| `user_prompt_submit.py` | 5s | General prompt processing |
| `memory_hints_injector.py` | 5s | Inject relevant memory hints |
| `enforce_plan_mode.py` | 5s | Enforce plan mode for complex tasks |
| `memory_updater.py` | 5s | Update agent memory from conversation |
| `pending_tracker.py` | 5s | Track pending tasks |

**PreToolUse (5 hooks, matcher: Write|Edit):**

| Hook | Timeout | Purpose |
|------|---------|---------|
| `claude_md_guard.py` | 5s | Protect CLAUDE.md from unauthorized edits |
| `creation_validator.py` | 5s | Validate new file creation (Anthropic standards) |
| `directory_contract_guard.py` | 5s | Enforce directory contract |
| `pre_commit_audit.py` | 5s | Pre-commit security audit |
| `agent_deprecation_guard.py` | 5s | Block writes to deprecated agent paths |

**PostToolUse (11 hooks, no matcher -- fires on ALL tool uses):**

| Hook | Timeout | Purpose |
|------|---------|---------|
| `post_tool_use.py` | 10s | General post-tool processing |
| `enforce_dual_location.py` | 5s | Ensure logs written to both locations |
| `pipeline_checkpoint.py` | 5s | Save pipeline checkpoint state |
| `agent_creation_trigger.py` | 5s | Trigger agent creation from pipeline |
| `agent_index_updater.py` | 5s | Update AGENT-INDEX.yaml after changes |
| `claude_md_agent_sync.py` | 5s | Sync agent info to CLAUDE.md |
| `agent_memory_persister.py` | 5s | Persist agent memory changes |
| `memory_capture.py` | 30ms | Lightweight memory capture |
| `post_batch_cascading.py` | 10s | Cascade batch outputs to destinations |
| `pipeline_phase_gate.py` | 5s | Enforce pipeline phase gates |
| `pipeline_orchestrator.py` | 10s | Orchestrate pipeline transitions |

**Stop (6 hooks):**

| Hook | Timeout | Purpose |
|------|---------|---------|
| `stop_hook_completeness.py` | 5s | Verify work completeness |
| `session_end.py` | 10s | Save session end state |
| `ralph_wiggum.py` | 5s | Post-session warnings |
| `continuous_save.py` | 5s | Continuous state saving |
| `memory_manager_stop.py` | 10s | Persist memory manager state |
| `session_index.py` | 5s | Update session index |

**Hook Performance Concern:** 33 hooks fire on every interaction cycle. PostToolUse alone has 11 hooks with no matcher (fires on EVERY tool call). Total worst-case hook execution per tool use: ~70 seconds of timeout budget.

### 8.2 Skills (~90 Directories)

Skills are Markdown-based instruction sets loaded on-demand via keyword matching. Native Mega Brain skills include:

| Category | Skills |
|----------|--------|
| Pipeline | `pipeline-jarvis`, `pipeline-mce`, `knowledge-extraction`, `process-company-inbox` |
| RAG/Search | `graph-search`, `memory-search`, `shared-memory`, `rag-search` |
| Session | `save`, `resume`, `session-launcher`, `chronicler` |
| Agent | `agent-creation`, `ask-company`, `brainstorming` |
| Source | `source-sync`, `smart-download-tagger`, `hybrid-source-reading`, `gdrive-transcription-downloader` |
| Dev | `code-review`, `feature-dev`, `github-workflow`, `hookify`, `python-megabrain` |
| Quality | `verify`, `verify-6-levels`, `verification-before-completion`, `validate-dod` |
| Planning | `writing-plans`, `executing-plans`, `dispatching-parallel-agents` |

~40 skill directories are externally injected by AIOX sync and blocked by `.gitignore` BLOCO 6.

### 8.3 Rules (17 Documents, Lazy-Loaded)

| File | Content | Size |
|------|---------|------|
| `RULE-GROUP-1.md` | Phase management (Rules ZERO, 1-10) | Large |
| `RULE-GROUP-2.md` | Persistence (Rules 11-14) | Large |
| `RULE-GROUP-3.md` | Operations (Rules 15-17) | Large |
| `RULE-GROUP-4.md` | Phase 5 specifics (Rules 18-22) | Large |
| `RULE-GROUP-5.md` | Validation (Rules 23-26) | Large |
| `RULE-GROUP-6.md` | Auto-routing (Rules 27-30) | Large |
| `RULE-GSD-MANDATORY.md` | GSD workflow enforcement | Medium |
| `CLAUDE-LITE.md` | Lite startup document (~4KB) | Small |
| `agent-cognition.md` | Agent cognitive protocol | Large |
| `agent-integrity.md` | Agent integrity protocol | Large |
| `epistemic-standards.md` | Anti-hallucination protocol | Large |
| `directory-contract.md` | Directory routing contract (v4.0.0) | Large |
| `state-management.md` | MISSION-STATE.json rules | Small |
| `mcp-governance.md` | MCP server governance | Medium |
| `ANTHROPIC-STANDARDS.md` | Hook/skill/MCP creation standards | Large |
| `logging.md` | Logging requirements | Medium |
| `pipeline.md` | Pipeline operation rules | Medium |

### 8.4 Commands (~50)

Slash commands in `.claude/commands/` for user-facing operations. Key commands:

| Command | Purpose |
|---------|---------|
| `/jarvis-briefing` | System status dashboard |
| `/jarvis-full` | Full pipeline execution |
| `/process-jarvis` | Pipeline processor |
| `/conclave` | Multi-agent debate session |
| `/ingest` | Ingest new material |
| `/save`, `/resume` | Session persistence |
| `/setup` | Environment setup wizard |
| `/gsd` | Get Shit Done planning framework |

---

## 9. Pipeline Architecture

### 9.1 JARVIS Pipeline (5 Phases)

```
Phase 1: Download/Ingest
    Raw materials -> knowledge/{bucket}/inbox/
    Sources: Google Drive, Fireflies, Read.ai, manual upload

Phase 2: Organization
    Inbox -> structured directories
    Tags: [TAG-XXXX] naming convention
    De-Para: planilha vs filesystem reconciliation

Phase 3: Processing
    Chunking (prompt-1.1), Entity Resolution (prompt-1.2)
    DNA Tag Extraction (prompt-2.1), Insight Extraction
    Narrative Synthesis (prompt-3.1)

Phase 4: Pipeline
    Batch processing (BATCH-XXX.md logs)
    DNA extraction across 5 layers
    Cascading to destination artifacts

Phase 5: Agent Generation
    5.1 Foundation (DNA consolidation)
    5.2 Person Agents (AGENT.md, SOUL.md, MEMORY.md)
    5.3 Cargo Contributions (enrich hybrid agents)
    5.4 Theme Dossiers (cross-source consolidation)
    5.5 Sua-Empresa sync
    5.6 Validation
```

### 9.2 MCE Pipeline (Mental Cognitive Extraction)

Located in `core/intelligence/pipeline/mce/`:

| Module | Purpose |
|--------|---------|
| `orchestrate.py` | Main MCE orchestration |
| `state_machine.py` | Pipeline state transitions |
| `gemini_analyzer.py` | Gemini-based analysis (optional) |
| `cache.py` | MCE result caching |
| `metadata_manager.py` | Metadata tracking |
| `metrics.py` | Pipeline metrics collection |
| `workflow_detector.py` | Workflow pattern detection |
| `cli.py` | CLI entry point |

### 9.3 Integration Pipelines

**Fireflies.ai:**
- `fireflies_config.py` -- configuration
- `fireflies_sync.py` -- poll-based sync (5-min launchd cron)
- State: `.claude/mission-control/FIREFLIES-STATE.json`
- API: GraphQL at `api.fireflies.ai/graphql` (Bearer token)

**Read.ai:**
- `read_ai_harvester.py` -- meeting transcript harvester
- `read_ai_router.py` -- meeting routing logic
- `read_ai_config.py` -- configuration
- `read_ai_gardener.py` -- maintenance
- `read_ai_oauth.py` -- OAuth flow
- State: `.claude/mission-control/READ-AI-STATE.json`
- API: MCP-based OAuth integration

**Scope Classification:**
- `scope_classifier.py` -- classifies content as business/personal/external
- `smart_router.py` -- routes classified content to appropriate bucket
- `inbox_organizer.py` -- organizes inbox content by person/company

---

## 10. Data Layer

### 10.1 RAG System

```
.data/
|-- rag_expert/                     Expert knowledge index
|   |-- bm25_index.json             BM25 inverted index
|   |-- chunks.json                 2,812 chunks, 743K tokens
|   `-- metadata.json               Index metadata
|
|-- rag_business/                   Business knowledge index [NOT BUILT]
|-- knowledge_graph/                Entity-relationship graph
|   `-- graph.json                  1,302 entities, 2,508 edges
|
|-- mce_cache/                      MCE pipeline cache
|-- voice_embeddings/               Speaker voice embeddings
`-- agent_memory/                   Per-agent JSONL memory stores
```

### 10.2 RAG Pipelines

| Pipeline | Components | Speed |
|----------|-----------|-------|
| A (BM25) | BM25 search only | ~3.6s |
| B (Hybrid) | BM25 + vector (if VOYAGE_API_KEY) | ~3.0s |
| C (Graph+Hybrid) | Knowledge graph + hybrid search | ~5.8s |
| D (Full) | Hierarchical multi-pipeline | ~2.5s |

### 10.3 State Files (JSON)

Pipeline state is managed through JSON files in `.claude/mission-control/`:

| File | Purpose |
|------|---------|
| `MISSION-STATE.json` | Current pipeline phase and progress |
| `FIREFLIES-STATE.json` | Fireflies sync state (50 meetings tracked) |
| `READ-AI-STATE.json` | Read.ai harvest state |
| `SKILL-INDEX.json` | Auto-generated skill/sub-agent index |
| `BATCH-REGISTRY.json` | Batch processing registry |
| `TRIAGE-QUEUE.json` | Content triage queue |
| `DISCOVERY-STATE.json` | Agent discovery state |
| `PHASE-GATE-STATE.json` | Phase gate tracking |
| `WATCHER-STATE.json` | Inbox watcher state |

---

## 11. Integration Points

### 11.1 MCP Servers (4 Configured)

| Server | Package | Transport | Purpose |
|--------|---------|-----------|---------|
| `mega-brain-knowledge` | `core.intelligence.rag.mcp_server` | stdio (Python) | Local RAG semantic search |
| `mega-brain` | `@modelcontextprotocol/server-filesystem` | stdio (Node) | Filesystem access |
| `n8n-mcp` | `n8n-mcp` | stdio (Node) | N8N workflow automation |
| `read-ai` | `mcp-remote` | HTTP (OAuth) | Read.ai meeting transcripts |

### 11.2 External APIs

| API | Auth Method | Purpose | Status |
|-----|-------------|---------|--------|
| Fireflies.ai | Bearer token (env) | Meeting transcripts | ACTIVE |
| Read.ai | OAuth via MCP | Meeting transcripts | ACTIVE (500 errors on some endpoints) |
| OpenAI Whisper | API key (env) | Audio transcription | CONFIGURED (requires OPENAI_API_KEY) |
| VoyageAI | API key (env) | Semantic embeddings | CONFIGURED (optional) |
| N8N Cloud | API key (env) | Workflow automation | ACTIVE |

### 11.3 N8N Webhook

- Workflow: "Read.ai Mega Brain" (created via N8N UI, NOT API)
- Production URL: N8N Cloud webhook endpoint
- Method: POST
- Known bug: N8N Cloud workflows created via API do NOT register production webhooks

---

## 12. Configuration and Build

### 12.1 Package Distribution

Distributed as npm package `mega-brain-ai`:

| Entry Point | File | Purpose |
|-------------|------|---------|
| `mega-brain-ai` | `bin/cli.js` | Main CLI entry |
| `mega-brain` | `bin/cli.js` | Alias |
| `mega-brain-push` | `bin/push.js` | Push utility |

**npm Scripts:**

| Script | Command | Purpose |
|--------|---------|---------|
| `start` | `node bin/mega-brain.js` | Start application |
| `lint` | `ruff check core/ .claude/hooks/` | Python linting |
| `test` | `python3 -m pytest tests/python/ -v` | Run tests |
| `validate` | `node bin/mega-brain.js validate` | System validation |
| `validate:json` | `python3 core/intelligence/validation/validate_json_integrity.py` | JSON integrity |
| `postinstall` | `node bin/install-hooks.js` | Install hooks on npm install |
| `prepublishOnly` | `node bin/pre-publish-gate.js` | Pre-publish validation |

### 12.2 Configuration Files

| File | Git Status | Purpose |
|------|------------|---------|
| `package.json` | Tracked | Node.js package (v1.4.0) |
| `pyproject.toml` | Tracked | Python project (v1.3.0) |
| `.mcp.json` | Gitignored | MCP server configuration |
| `.env` | Gitignored | API keys and secrets |
| `.claude/settings.json` | Tracked | Hook configuration (distributed) |
| `.claude/settings.local.json` | Gitignored | Local hook overrides |
| `biome.json` | Tracked | JS/JSON formatting |
| `.editorconfig` | Tracked | Editor settings |
| `.gitleaks.toml` | Tracked | Secret scanning rules |

### 12.3 Version Mismatch

`package.json` declares version `1.4.0` while `pyproject.toml` declares version `1.3.0`. These should be synchronized.

---

## 13. Security Architecture

### 13.1 Layer-Based Access Control

| Control | Mechanism |
|---------|-----------|
| L3 content protection | `.gitignore` whitelist architecture (BLOCO 2, 7) |
| Secret scanning | `.gitleaks.toml` configuration |
| Env file protection | `settings.json` deny list blocks Read/Write/Edit of `*.env` |
| SSH protection | `settings.json` deny list blocks `~/.ssh/*` |
| Destructive commands | `settings.json` blocks `rm -rf`, `curl`, `wget` |
| Git push | Blocked by deny rules -- must delegate to @devops |

### 13.2 Hook-Based Enforcement

| Hook | What It Enforces |
|------|-----------------|
| `claude_md_guard.py` | Prevents unauthorized CLAUDE.md edits |
| `directory_contract_guard.py` | Enforces directory routing contract |
| `creation_validator.py` | Validates Anthropic standards compliance |
| `pre_commit_audit.py` | Pre-commit security checks |
| `agent_deprecation_guard.py` | Blocks writes to deprecated paths |

### 13.3 Security Gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| No .env file exists | HIGH | System runs without API keys configured |
| `.mcp.json` hardcoded path | MEDIUM | Contains absolute path `/Users/thiagofinch/...` for filesystem MCP |
| `memory_capture.py` timeout 30ms | LOW | Likely too short, may silently fail |
| Hooks use `2>/dev/null` in some paths | LOW | Contradicts ANTHROPIC-STANDARDS error handling rules |
| No credential rotation policy | MEDIUM | API keys (Fireflies, N8N) have no rotation schedule |

---

## 14. Technical Debt Inventory

### 14.1 CRITICAL (Block shipping / data integrity risk)

| # | Debt | Severity | Effort | Files Affected |
|---|------|----------|--------|----------------|
| D1 | **21 duplicate Python modules** in `core/intelligence/` -- root files are copies of subdirectory files | CRITICAL | MEDIUM (2-4h) | 42 files (21 pairs) |
| D2 | **AGENT-INDEX.yaml uses `agents/minds/` paths** instead of `agents/external/` | CRITICAL | LOW (30m) | 1 file + hook |
| D3 | **Version mismatch:** package.json=1.4.0 vs pyproject.toml=1.3.0 | CRITICAL | TRIVIAL (5m) | 2 files |
| D4 | **20+ files still reference `agents/minds/`** (deprecated path) | CRITICAL | MEDIUM (1-2h) | 20+ files |

### 14.2 HIGH (Blocks quality / scaling)

| # | Debt | Severity | Effort | Files Affected |
|---|------|----------|--------|----------------|
| D5 | **50 tests total** for 29,640 lines of Python -- coverage is ~0.17% | HIGH | HIGH (40h+) | All of `core/intelligence/` |
| D6 | **11 PostToolUse hooks with no matcher** fire on EVERY tool call | HIGH | MEDIUM (2h) | `settings.json` |
| D7 | **`docs/` directory still has content** but is PROHIBITED in `paths.py` | HIGH | LOW (1h) | docs/ tree |
| D8 | **`agents/minds/` directory still exists** alongside `agents/external/` | HIGH | LOW (30m) | filesystem |
| D9 | **RAG business index not built** -- bucket router has dead path | HIGH | MEDIUM (2h) | `.data/rag_business/` |
| D10 | **Vector RAG disabled** -- no VOYAGE_API_KEY configured | HIGH | LOW (config) | `.env` |

### 14.3 MEDIUM (Maintenance burden / code quality)

| # | Debt | Severity | Effort | Files Affected |
|---|------|----------|--------|----------------|
| D11 | **CLAUDE.md references deprecated `workspace/domains/`, `workspace/team/`** | MEDIUM | LOW (30m) | `.claude/CLAUDE.md` |
| D12 | **37 hooks total** -- high maintenance burden, every hook is a Python process spawn | MEDIUM | HIGH (design) | `.claude/hooks/` |
| D13 | **~40 externally-injected skills** blocked by gitignore but present on disk | MEDIUM | LOW (cleanup) | `.claude/skills/` |
| D14 | **`core/.claude/` directory exists** -- rogue Claude config inside core engine | MEDIUM | TRIVIAL (delete) | 1 file |
| D15 | **No `package-lock.json` in repo** -- non-deterministic npm installs | MEDIUM | TRIVIAL (generate) | 1 file |
| D16 | **`requirements.txt` may drift** from `pyproject.toml` deps | MEDIUM | LOW (automate) | 2 files |
| D17 | **read_ai_*.py excluded from ruff** -- 5 files with no linting | MEDIUM | MEDIUM (2h) | 5 files |
| D18 | **Cargo agents have mixed file formats** -- some have AGENT+SOUL+MEMORY+DNA, others only SOW | MEDIUM | HIGH (content) | ~15 agents |

### 14.4 LOW (Nice to fix / cosmetic)

| # | Debt | Severity | Effort | Files Affected |
|---|------|----------|--------|----------------|
| D19 | **`.mcp.json` has absolute path** for filesystem MCP server | LOW | TRIVIAL | 1 file |
| D20 | **`memory_capture.py` timeout is 30ms** vs 5000ms standard | LOW | TRIVIAL | `settings.json` |
| D21 | **`.DS_Store` files tracked in some dirs** | LOW | TRIVIAL (gitignore) | Multiple |
| D22 | **`outputs/` directory exists** at root -- not in directory contract | LOW | LOW (move/delete) | 1 dir |
| D23 | **Rule files reference JARVIS identity** which conflicts with character envelope system | LOW | MEDIUM | 17 rule files |
| D24 | **`tests/` gitignored in BLOCO 7** -- tests should be tracked | LOW | LOW (fix gitignore) | `.gitignore` |

---

## 15. Dependency Analysis

### 15.1 Node.js Dependency Graph

```
mega-brain-ai (npm package)
|-- boxen ^7.1.0          CLI boxes (ESM, 3 transitive)
|-- chalk ^5.3.0          Terminal colors (ESM, 0 transitive)
|-- fs-extra ^11.3.4      FS utilities (CJS compat, 2 transitive)
|-- gradient-string ^2.0.2 Gradient text (2 transitive)
|-- inquirer ^9.2.0       Interactive prompts (15+ transitive)
|-- ora ^7.0.0            Spinners (5+ transitive)
|
|-- [dev] execa ^9.6.1    Process execution
`-- [dev] js-yaml ^4.1.1  YAML parsing
```

All production Node.js dependencies are CLI cosmetic libraries. The actual intelligence is in Python. Risk assessment: LOW -- these are stable, well-maintained packages.

### 15.2 Python Dependency Graph

```
mega-brain (pip package)
|-- PyYAML >=6.0,<7.0     [REQUIRED] Config parsing
|
|-- [pipeline] PyYAML     Same as required (redundant group)
|
|-- [speakers]            GPU-heavy, optional
|   |-- pyannote.audio    Speaker diarization
|   |-- torch + torchaudio ML framework
|   |-- numpy, scipy      Numerical computing
|   `-- assemblyai        Cloud speech-to-text
|
|-- [rag]                 Search, optional
|   |-- voyageai          Vector embeddings
|   `-- rank-bm25         BM25 text search
|
`-- [dev]                 Development
    |-- pytest + pytest-cov Testing
    |-- ruff              Linting
    `-- pyright           Type checking
```

Risk assessment:
- PyYAML: stable, low risk
- torch/pyannote: heavy, version-sensitive, GPU-optional
- voyageai: cloud dependency, requires API key
- rank-bm25: lightweight, stable

### 15.3 Unused Dependencies

The `pipeline` optional group in `pyproject.toml` only contains `PyYAML` which is already in the required deps. This group serves no purpose.

---

## 16. Recommendations

### 16.1 Immediate Actions (This Sprint)

| Priority | Action | Debt ID | Impact |
|----------|--------|---------|--------|
| 1 | Delete 21 duplicate root files in `core/intelligence/` | D1 | Eliminates confusion, reduces maintenance |
| 2 | Sync version numbers (package.json and pyproject.toml to 1.4.0) | D3 | Consistency |
| 3 | Update AGENT-INDEX.yaml to use `agents/external/` paths | D2 | Fixes stale references |
| 4 | Fix `memory_capture.py` timeout from 30ms to 5000ms | D20 | Prevents silent failures |
| 5 | Delete `agents/minds/` directory (data is in `agents/external/`) | D8 | Removes deprecated path |
| 6 | Delete `core/.claude/` rogue directory | D14 | Cleanup |

### 16.2 Short-Term (Next 2 Sprints)

| Priority | Action | Debt ID | Impact |
|----------|--------|---------|--------|
| 7 | Add PostToolUse matchers to reduce hook firing | D6 | Performance improvement |
| 8 | Migrate `docs/` content to `reference/` | D7 | Aligns with directory contract |
| 9 | Fix all 20+ `agents/minds/` references to `agents/external/` | D4 | Eliminates deprecated paths |
| 10 | Update CLAUDE.md to reflect current workspace structure | D11 | Accurate documentation |
| 11 | Un-ignore `tests/` in gitignore (should be L1) | D24 | Tests should be tracked |
| 12 | Generate and commit `package-lock.json` | D15 | Deterministic builds |

### 16.3 Medium-Term (Next Quarter)

| Priority | Action | Debt ID | Impact |
|----------|--------|---------|--------|
| 13 | Increase test coverage to 40% minimum (from 0.17%) | D5 | Quality assurance |
| 14 | Build RAG business index | D9 | Enables business knowledge search |
| 15 | Consolidate cargo agent formats (all should have AGENT+SOUL+MEMORY+DNA) | D18 | Agent consistency |
| 16 | Clean externally-injected skills from disk | D13 | Reduces confusion |
| 17 | Enable ruff on read_ai_*.py files | D17 | Code quality |

### 16.4 Architectural Recommendations

1. **Hook consolidation:** Consider merging related hooks into fewer scripts to reduce process spawning overhead. The 11 PostToolUse hooks could be consolidated into 3-4 with internal routing.

2. **Test infrastructure:** The 50:29,640 test-to-code ratio is critically low. Prioritize testing `core/intelligence/pipeline/` and `core/intelligence/rag/` as these contain the core business logic.

3. **Dual-language concern:** The system uses Node.js only for CLI cosmetics and Python for all logic. Consider whether the Node.js layer adds value beyond `npx` distribution, or if a pure Python distribution (via pip) would reduce complexity.

4. **State file proliferation:** 10+ JSON state files in `.claude/mission-control/` with no schema validation at runtime. Consider consolidating into fewer state files or adding JSON schema validation on read.

5. **Gitignore complexity:** The 685-line whitelist-based `.gitignore` with 7 blocks is fragile. Any new file defaults to ignored. Consider documenting a simpler "add new file" procedure.

---

## Appendix A: File Count by Directory

| Directory | Files | Lines (approx) |
|-----------|-------|-----------------|
| `core/intelligence/` | 120+ Python modules | ~29,640 |
| `.claude/hooks/` | 37 Python scripts | ~5,000 est. |
| `.claude/skills/` | 90+ directories | ~10,000 est. |
| `.claude/rules/` | 17 Markdown files | ~8,000 est. |
| `.claude/commands/` | 50+ Markdown files | ~3,000 est. |
| `agents/` | 100+ files across categories | ~15,000 est. |
| `knowledge/external/` | 200+ files (dna, dossiers, playbooks) | ~50,000 est. |
| `bin/` | 10+ JS files | ~2,000 est. |

## Appendix B: Key File Paths

| Purpose | Path |
|---------|------|
| Path registry | `core/paths.py` |
| Agent index | `agents/AGENT-INDEX.yaml` |
| Hook config | `.claude/settings.json` |
| Package manifest | `package.json` |
| Python config | `pyproject.toml` |
| MCP config | `.mcp.json` |
| Directory contract | `.claude/rules/directory-contract.md` |
| Main CLAUDE.md | `.claude/CLAUDE.md` |
| JARVIS soul | `system/02-JARVIS-SOUL.md` |
| JARVIS DNA | `system/03-JARVIS-DNA.yaml` |

---

*Document generated by Brownfield Discovery Phase 1 -- The Architect*
*Tiny Rick -- TINY RICK! Architecture equations balanced!*
