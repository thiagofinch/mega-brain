# BROWNFIELD DISCOVERY -- MEGA BRAIN

> **Version:** 1.0.0
> **Date:** 2026-03-08
> **Purpose:** Complete system architecture map for aiox-brain integration readiness
> **Scope:** All scripts, hooks, rules, agents, RAG, pipeline, state, dependencies

---

## 1. DIRECTORY TREE (Annotated)

```
mega-brain/                             # Root — npm package "@thiagofinch/mega-brain" v1.3.0
|
|-- core/                               # ENGINE (L1 Community — tracked)
|   |-- tasks/                          # 15 atomic task definitions (.md)
|   |   |-- process-batch.md
|   |   |-- extract-dna.md
|   |   |-- validate-cascade.md
|   |   |-- create-person-agent.md
|   |   |-- create-cargo-agent.md
|   |   |-- update-dossier.md
|   |   |-- enrich-memory.md
|   |   |-- phase5-foundation.md
|   |   |-- phase5-person.md
|   |   |-- phase5-cargo.md
|   |   |-- phase5-themes.md
|   |   |-- phase5-org.md
|   |   |-- phase5-validation.md
|   |   |-- conclave-debate.md
|   |   +-- ingest-material.md
|   |
|   |-- workflows/                      # 4 YAML orchestration definitions
|   |   |-- wf-conclave.yaml            # Multi-agent debate workflow
|   |   |-- wf-extract-dna.yaml         # DNA extraction pipeline
|   |   |-- wf-pipeline-full.yaml       # Full 5-phase pipeline
|   |   +-- wf-ingest.yaml              # Material ingestion workflow
|   |
|   |-- intelligence/                   # Python scripts — the brain
|   |   |-- pipeline/                   # 14 pipeline scripts
|   |   |-- rag/                        # 13 RAG scripts
|   |   |-- retrieval/                  # 4 context assembly scripts
|   |   |-- speakers/                   # 5 speaker diarization scripts
|   |   |-- entities/                   # 5 entity detection scripts
|   |   |-- dossier/                    # 4 dossier management scripts
|   |   |-- roles/                      # 4 role/skill generation scripts
|   |   |-- utils/                      # 2 utility scripts
|   |   |-- validation/                 # Audit + validation scripts
|   |   |-- context_scorer.py           # Adaptive context scoring
|   |   +-- memory_manager.py           # Agent + shared memory store
|   |
|   |-- patterns/                       # YAML config patterns
|   |-- protocols/                      # Pipeline, conclave, DNA protocols
|   |-- schemas/                        # JSON schemas for validation
|   |-- jarvis/                         # JARVIS Soul + DNA
|   |-- templates/                      # Log + agent templates
|   +-- glossary/                       # Domain glossaries
|
|-- agents/                             # AI AGENTS (L1/L2 — tracked)
|   |-- AGENT-INDEX.yaml                # Agent registry (v4.1.0, 27 agents)
|   |-- conclave/                       # 3 deliberation agents (L1)
|   |   |-- critico-metodologico/
|   |   |-- sintetizador/
|   |   +-- advogado-do-diabo/
|   |-- cargo/                          # 14 functional role agents (L2)
|   |   |-- sales/                      # 9 agents (sds, lns, bdr, nepq, coordinator, manager, lead, cs, closer)
|   |   |-- marketing/                  # 1 agent (paid-media-specialist)
|   |   +-- c-level/                    # 4 agents (cfo, coo, cmo, cro)
|   +-- minds/                          # 10 expert mind clones (L3 — gitignored)
|       |-- alex-hormozi/
|       |-- cole-gordon/
|       |-- jeremy-miner/
|       |-- jeremy-haynes/
|       |-- sam-oven/
|       |-- jordan-lee/
|       |-- richard-linder/
|       |-- the-scalable-company/
|       |-- g4-educacao/
|       +-- full-sales-system/
|
|-- .claude/                            # CLAUDE CODE INTEGRATION (L1)
|   |-- hooks/                          # 31 Python hook scripts
|   |-- skills/                         # 95+ skill directories with SKILL.md
|   |-- commands/                       # Slash command definitions
|   |-- rules/                          # 10 rule files (lazy-loaded)
|   |-- sessions/                       # Session persistence
|   |-- mission-control/                # State files (MISSION-STATE, SKILL-INDEX)
|   |-- jarvis/                         # JARVIS state, memory, DNA personality
|   |-- agent-memory/                   # Per-agent memory persistence
|   |-- settings.json                   # Hook registration + deny list
|   +-- CLAUDE.md                       # Project instructions for Claude
|
|-- knowledge/                          # KNOWLEDGE BASE (L2/L3)
|   |-- external/                       # Bucket 1: Expert Knowledge (L2)
|   |   |-- dna/                        # DNA schemas per person
|   |   |-- dossiers/                   # Person + theme dossiers
|   |   |-- playbooks/                  # Actionable playbooks
|   |   |-- sources/                    # Source compilations
|   |   +-- inbox/                      # Raw expert materials
|   |-- workspace/                      # Bucket 2: Business Data (L2/L3)
|   |   |-- _org/                       # Organization structure
|   |   |-- _team/                      # Team data
|   |   |-- _finance/                   # Financial data (L3)
|   |   |-- _meetings/                  # Meeting notes
|   |   |-- _automations/               # Tool configs
|   |   +-- _tools/                     # Detected tools log
|   +-- personal/                       # Bucket 3: Cognitive/Private (L3 ONLY)
|       |-- _email/                     # Email digests
|       |-- _messages/                  # WhatsApp/Slack
|       |-- _calls/                     # Call transcripts
|       +-- _cognitive/                 # Mental models, reflections
|
|-- bin/                                # CLI TOOLS (L1 — npm package)
|   |-- cli.js                          # CLI wrapper
|   |-- mega-brain.js                   # Main CLI entry point
|   |-- push.js                         # Git push helper
|   |-- validate-package.js             # Package validation
|   |-- install-hooks.js                # Hook installer
|   +-- pre-publish-gate.js             # Publish safety gate
|
|-- docs/                               # DOCUMENTATION (L1)
|   |-- prd/                            # Product requirements
|   |-- plans/                          # Plan mode outputs
|   |-- architecture/                   # Architecture documents (this file)
|   +-- reviews/                        # Technical reviews
|
|-- .data/                              # INDEXES (L3 — gitignored)
|   |-- rag_index/                      # BM25 + vector index files
|   +-- knowledge_graph/                # Entity graph JSON
|
|-- inbox/                              # RAW MATERIALS (L3)
|-- artifacts/                          # PIPELINE OUTPUTS (L3)
|-- logs/                               # SESSION LOGS (L3)
|-- system/                             # SYSTEM CONFIG (tracked)
|-- reference/                          # DOCUMENTATION + GUIDES (tracked)
|-- .planning/                          # GSD PLANS (tracked)
|-- research/                           # AD-HOC ANALYSIS (L3)
+-- processing/                         # PIPELINE ARTIFACTS (L3)
```

---

## 2. LAYER SYSTEM

| Layer | Content | Git Status | Access |
|-------|---------|------------|--------|
| L1 (Community) | core/, agents/conclave, .claude/, bin/, docs/ | Tracked (npm package) | Public |
| L2 (Pro) | agents/cargo, knowledge/external/ (populated) | Tracked (premium) | Licensed |
| L3 (Personal) | .data/, .env, agents/external/, knowledge/personal/, inbox/ | Gitignored | Private |

The `.gitignore` uses a WHITELIST pattern: line 24 is `*` (ignore everything), then `!*/` re-allows directory traversal, followed by explicit `!filename` entries to allow specific files. This is unusual and requires manual `!` entries for any new tracked file.

---

## 3. PIPELINE SCRIPTS (core/intelligence/pipeline/)

| Script | Lines | Purpose |
|--------|-------|---------|
| `autonomous_processor.py` | ~300 | Queue-based autonomous file processor. FIFO priority queue, SIGALRM timeout, checkpoint/recovery to JSON, exponential backoff retry (max 3 attempts), CLI interface. |
| `task_orchestrator.py` | ~280 | Workflow execution engine. Reads YAML from core/workflows/, executes phases sequentially, resolves tasks from core/tasks/ markdown files, persists state to ORCHESTRATOR-STATE.json. |
| `pipeline_heal.py` | ~350 | Auto-heal system. 14 integrity checks per source (chunks, canonical, insights, narratives, dossiers, nav-map, agent-memory, RAG index, file-registry, session-state, DNA, SOUL, inbox-registry). Produces ASCII report. |
| `batch_governor.py` | ~150 | Partitions files into max-5 batches grouped by source person. |
| `pipeline_router.py` | ~200 | Routes files to external/workspace/personal buckets based on path analysis. Supports dual-routing for owner insights. |
| `bucket_processor.py` | ~250 | Unified 3-layer knowledge ingest processor. Handles all three knowledge buckets. |
| `bucket_router.py` | ~180 | Cross-bucket access control. 5 modes: expert-only, business, full-3d, personal, company-only. |
| `read_ai_config.py` | ~60 | Config loader for Read.ai harvester. Reads from .env. |
| `read_ai_harvester.py` | ~280 | Bulk Read.ai transcript downloader with checkpointing. |
| `read_ai_router.py` | ~150 | Meeting classification (empresa vs pessoal) via keyword scoring. |
| `read_ai_gardener.py` | ~180 | Organizes personal meeting transcripts into themed subfolders. |
| `session_autosave.py` | ~120 | PostToolUse hook tracking tool usage to JSONL. |
| `sync_package_files.py` | ~130 | Syncs package.json `files` field with L1 audit classifications. |
| `validate_layers.py` | ~200 | Layer validation against classification rules. |

---

## 4. RAG SCRIPTS (core/intelligence/rag/)

| Script | Lines | Purpose |
|--------|-------|---------|
| `chunker.py` | ~300 | Recursive 512-token splitting with 15% overlap. Indexes DNA, dossiers, playbooks from knowledge/external/. Produces Chunk dataclass with metadata (person, source, domain, layer). |
| `hybrid_index.py` | ~363 | Dual-strategy indexing. BM25 (term frequency) + Voyage AI vector (voyage-3, 1024 dims). Local JSON storage. Singleton pattern. Auto-loads .env for VOYAGE_API_KEY. |
| `hybrid_query.py` | ~250 | 3-stage retrieval: vector top-30 + BM25 top-30 + RRF fusion (k=60). Strategic source ordering. Person filter support. |
| `graph_builder.py` | ~350 | Knowledge graph from DNA YAML files. Entities: conceito, filosofia, modelo-mental, heuristica, framework, metodologia. Edges: pertence-a, implementa, contrasta-com, complementa. LazyGraphRAG community summaries. |
| `graph_query.py` | ~280 | 5 query types: GLOBAL (community summaries), ONTOLOGICAL (DNA hierarchy), ASSOCIATIVE (PPR), HIERARCHICAL (layer traversal), FACTUAL (entity lookup). |
| `ontology_layer.py` | ~200 | OG-RAG anchored to the 5-layer DNA ontology. Hierarchy traversal: filosofia -> modelo-mental -> heuristica -> framework -> metodologia. |
| `associative_memory.py` | ~418 | HippoRAG 2 implementation. Personalized PageRank (alpha=0.15, 20 iterations, tolerance=1e-6). Seed activation via keyword matching. Cross-expert connection finder. |
| `adaptive_router.py` | ~300 | Routes queries to 5 pipelines by intent classification. Pipeline A: BM25-only (factual). B: Hybrid (analytical). C: Hybrid+Graph (strategic). D: Full RAG+Graph+Memory (complex). E: LLM-only (greeting/meta). |
| `self_rag.py` | ~200 | Post-generation verification. Claim extraction from response text, verification against retrieved chunks, faithfulness scoring (0.0--1.0). |
| `mcp_server.py` | ~250 | MCP stdio JSON-RPC server. 5 tools: search_knowledge, get_agent_context, list_experts, get_graph_connections, verify_response. |
| `evaluator.py` | ~200 | RAGAS-inspired evaluation. Metrics: faithfulness, context precision, context recall, answer relevancy. Ground truth comparison. |
| `pipeline.py` | ~243 | Unified entry point. Connects adaptive_router -> retrieval -> memory -> fusion -> output. PipelineResult dataclass. 70/30 RAG/memory budget split. |
| `__init__.py` | ~5 | Package init. |

### RAG Pipeline Architecture

```
Query
  |
  v
adaptive_router.py          # Classify intent, select pipeline A/B/C/D/E
  |
  +---> Pipeline A (BM25-only)
  |       +-- hybrid_query.py (BM25 path only)
  |
  +---> Pipeline B (Hybrid)
  |       +-- hybrid_query.py (vector + BM25 + RRF)
  |
  +---> Pipeline C (Hybrid + Graph)
  |       +-- hybrid_query.py + graph_query.py
  |       +-- ontology_layer.py (DNA hierarchy)
  |       +-- associative_memory.py (PPR)
  |
  +---> Pipeline D (Full)
  |       +-- All of C + memory_manager.py + context_scorer.py
  |
  +---> Pipeline E (LLM-only)
          +-- No retrieval (greetings, meta queries)
  |
  v
pipeline.py                 # Fuse RAG context + memory context
  |
  v
self_rag.py                 # Post-generation verification (optional)
  |
  v
PipelineResult              # query, intent, pipeline, context, sources, latency
```

---

## 5. INTELLIGENCE SCRIPTS (core/intelligence/)

### 5.1 Retrieval (core/intelligence/retrieval/)

| Script | Purpose |
|--------|---------|
| `context_assembler.py` | Smart trimmed context assembly per agent. Reduces 542KB full context to ~30KB relevant context. |
| `memory_splitter.py` | Splits monolithic MEMORY.md into per-domain files for faster retrieval. |
| `nav_map_builder.py` | Populates NAVIGATION-MAP.json with section-to-chunk mappings. |
| `query_analyzer.py` | Maps query -> domains -> agents using DOMAINS-TAXONOMY. |

### 5.2 Speakers (core/intelligence/speakers/)

| Script | Purpose |
|--------|---------|
| `voice_diarizer.py` | Audio segmentation. Supports pyannote (local) or AssemblyAI (cloud). |
| `voice_embedder.py` | Speaker embedding extraction for voice fingerprinting. |
| `voice_registry.py` | Persistent voice fingerprint store. |
| `speaker_labeler.py` | Interactive speaker identification from diarized segments. |
| `speaker_gate.py` | Validates speaker labels in transcripts. |

### 5.3 Entities (core/intelligence/entities/)

| Script | Purpose |
|--------|---------|
| `bootstrap_registry.py` | Populates initial ENTITY-REGISTRY.json from known agents. |
| `entity_normalizer.py` | Continuous entity canonicalization (merge duplicates, standardize names). |
| `role_detector.py` | 3-level role detection: direct (explicit mention), inferred (context), emergent (behavioral pattern). |
| `org_chain_detector.py` | Detects hierarchical org patterns in transcripts. |
| `business_model_detector.py` | Detects organizational structure from absorbed entities. |

### 5.4 Dossier (core/intelligence/dossier/)

| Script | Purpose |
|--------|---------|
| `dossier_tracer.py` | Adds inline DNA references (^[FONTE]) to dossier content. |
| `dossier_trigger.py` | Evaluates when to create/update thematic dossiers based on thresholds. |
| `theme_analyzer.py` | Extracts and normalizes themes from chunks and insights. |
| `review_dashboard.py` | CLI dashboard for human checkpoint management. |

### 5.5 Roles (core/intelligence/roles/)

| Script | Purpose |
|--------|---------|
| `skill_generator.py` | Converts DNA frameworks into executable SKILL.md files. |
| `sow_generator.py` | Generates dual-purpose SOW (Statement of Work) for detected roles. |
| `tool_discovery.py` | Discovers available tools per role from system config. |
| `viability_scorer.py` | APEX multidimensional scoring for agent creation viability. |

### 5.6 Agents (core/intelligence/agents/)

| Script | Purpose |
|--------|---------|
| `agent_trigger.py` | Evaluates when to create new agents based on material density thresholds. |

### 5.7 Utils (core/intelligence/utils/)

| Script | Purpose |
|--------|---------|
| `auto_organize_inbox.py` | Auto-organize inbox files by content type and source. |
| `classify_unknown.py` | Classify and move unknown files to appropriate directories. |

### 5.8 Top-Level Intelligence

| Script | Purpose |
|--------|---------|
| `context_scorer.py` | Adaptive context scoring for memory retrieval budget allocation. |
| `memory_manager.py` | Agent-specific + shared memory store with JSON persistence. |

---

## 6. HOOKS (.claude/hooks/)

### 6.1 Hook Registry (settings.json)

| Event | Hook | Timeout | Purpose |
|-------|------|---------|---------|
| **SessionStart** | `session_start.py` | 30 | Initialize session state |
| | `skill_indexer.py` | 30 | Scan skills, generate SKILL-INDEX.json |
| | `inbox_age_alert.py` | 30 | Alert on stale inbox items |
| | `session_index.py` | 10 | Index session for resume |
| **UserPromptSubmit** | `skill_router.py` | 30 | Auto-route to matching skills by keyword |
| | `quality_watchdog.py` | 30 | Detect agent quality gaps |
| | `user_prompt_submit.py` | 30 | General prompt processing |
| | `memory_hints_injector.py` | 10 | Inject relevant memory hints |
| | `enforce_plan_mode.py` | 10 | Force plan mode for complex tasks |
| | `memory_updater.py` | 10 | Update memory from prompt context |
| | `pending_tracker.py` | 10 | Track pending tasks |
| **PreToolUse** (Write/Edit) | `claude_md_guard.py` | 30 | Protect CLAUDE.md from bad edits |
| | `creation_validator.py` | 30 | Validate file creation location |
| | `directory_contract_guard.py` | 30 | Enforce directory contract |
| **PostToolUse** | `post_tool_use.py` | 30 | General post-tool processing |
| | `enforce_dual_location.py` | 30 | Enforce dual-location logging |
| | `pipeline_checkpoint.py` | 10 | Checkpoint pipeline state |
| | `agent_creation_trigger.py` | 10 | Trigger agent creation evaluator |
| | `agent_index_updater.py` | 10 | Update AGENT-INDEX.yaml |
| | `claude_md_agent_sync.py` | 10 | Sync agent count to CLAUDE.md |
| | `agent_memory_persister.py` | 10 | Persist agent memory changes |
| | `post_batch_cascading.py` | 10 | Cascade knowledge to downstream targets |
| | `pipeline_phase_gate.py` | 10 | Gate pipeline phase transitions |
| **Stop** | `stop_hook_completeness.py` | 30 | Verify session completeness |
| | `session_end.py` | 30 | Finalize session state |
| | `ralph_wiggum.py` | 30 | End-of-session humor hook |
| | `continuous_save.py` | 10 | Save session state |
| | `memory_manager_stop.py` | 10 | Flush memory to disk |
| | `session_index.py` | 10 | Update session index |

### 6.2 Unregistered Hooks (exist in hooks/ but NOT in settings.json)

| Hook | Purpose | Status |
|------|---------|--------|
| `resolve_agent_path.py` | Resolve agent paths from IDs | ORPHANED |
| `session_autosave_v2.py` | Alternative session autosave | ORPHANED |
| `pre_commit_audit.py` | Pre-commit validation | ORPHANED |

---

## 7. RULES (.claude/rules/)

Rules are lazy-loaded via keyword matching from the UserPromptSubmit hook (skill_router.py).

| File | Group | Keywords | Scope |
|------|-------|----------|-------|
| `RULE-GROUP-1.md` | PHASE-MANAGEMENT | fase, pipeline, batch, missao, inbox, de-para | Rules 0-10 |
| `RULE-GROUP-2.md` | PERSISTENCE | sessao, save, resume, plan mode, verificacao | Rules 11-14 |
| `RULE-GROUP-3.md` | OPERATIONS | terminal, paralelo, template, KPI | Rules 15-17 |
| `RULE-GROUP-4.md` | PHASE-5-SPECIFIC | agente, dossier, cascateamento, source | Rules 18-22 |
| `RULE-GROUP-5.md` | VALIDATION | validar, source-sync, integridade, enforcement | Rules 23-26 |
| `RULE-GROUP-6.md` | AUTO-ROUTING | skill, sub-agent, quality, GitHub | Rules 27-30 |
| `RULE-GSD-MANDATORY.md` | GSD WORKFLOW | plano, implementar, criar feature | GSD enforcement |
| `ANTHROPIC-STANDARDS.md` | STANDARDS | hooks, skills, mcp, sub-agents | Compliance |
| `agent-cognition.md` | COGNITION | agent phases, depth-seeking, epistemic | Agent reasoning protocol |
| `agent-integrity.md` | INTEGRITY | rastreabilidade, fonte, citacao | Zero-invention enforcement |
| `directory-contract.md` | PATHS | directory, output, path, bucket | Where to save outputs |
| `epistemic-standards.md` | EPISTEMIC | confidence, fato, recomendacao | Anti-hallucination |
| `mcp-governance.md` | MCP | mcp, server, credentials | MCP server governance |
| `state-management.md` | STATE | MISSION-STATE, sessao, posicao | State file management |
| `CLAUDE-LITE.md` | LITE | (session startup) | Compact rule summary |

---

## 8. AGENT INVENTORY

### 8.1 MINDS (Expert Clones) -- L3

| ID | Path | Status |
|----|------|--------|
| alex-hormozi | agents/external/alex-hormozi/ | active |
| cole-gordon | agents/external/cole-gordon/ | active |
| jeremy-miner | agents/external/jeremy-miner/ | active |
| jeremy-haynes | agents/external/jeremy-haynes/ | active |
| sam-oven | agents/external/sam-oven/ | active |
| jordan-lee | agents/external/jordan-lee/ | active |
| richard-linder | agents/external/richard-linder/ | active |
| the-scalable-company | agents/external/the-scalable-company/ | active |
| g4-educacao | agents/external/g4-educacao/ | active |
| full-sales-system | agents/external/full-sales-system/ | active |

### 8.2 CARGO (Functional Roles) -- L2

| ID | Area | Path |
|----|------|------|
| sds | sales | agents/cargo/sales/sds/ |
| lns | sales | agents/cargo/sales/lns/ |
| bdr | sales | agents/cargo/sales/bdr/ |
| nepq-specialist | sales | agents/cargo/sales/nepq-specialist/ |
| sales-coordinator | sales | agents/cargo/sales/sales-coordinator/ |
| sales-manager | sales | agents/cargo/sales/sales-manager/ |
| sales-lead | sales | agents/cargo/sales/sales-lead/ |
| customer-success | sales | agents/cargo/sales/customer-success/ |
| closer | sales | agents/cargo/sales/closer/ |
| paid-media-specialist | marketing | agents/cargo/marketing/paid-media-specialist/ |
| cfo | c-level | agents/cargo/c-level/cfo/ |
| coo | c-level | agents/cargo/c-level/coo/ |
| cmo | c-level | agents/cargo/c-level/cmo/ |
| cro | c-level | agents/cargo/c-level/cro/ |

### 8.3 CONCLAVE (Deliberation) -- L1

| ID | Path |
|----|------|
| critico-metodologico | agents/conclave/critico-metodologico/ |
| sintetizador | agents/conclave/sintetizador/ |
| advogado-do-diabo | agents/conclave/advogado-do-diabo/ |

### 8.4 Agent File Structure (per agent)

```
agents/{type}/{id}/
|-- AGENT.md              # Operational definition (11-part Template V3)
|-- SOUL.md               # Identity, voice, personality
|-- MEMORY.md             # Experiential memory, learned patterns
+-- DNA-CONFIG.yaml       # Source configuration, weights, paths
```

---

## 9. STATE MANAGEMENT

### 9.1 State Files

| File | Location | Purpose |
|------|----------|---------|
| MISSION-STATE.json | .claude/mission-control/ | Current mission phase, progress, session |
| JARVIS-STATE.json | .claude/jarvis/ | JARVIS operational state |
| JARVIS-MEMORY.md | .claude/jarvis/ | JARVIS relational memory |
| SKILL-INDEX.json | .claude/mission-control/ | Auto-generated skill/keyword index |
| ORCHESTRATOR-STATE.json | .claude/mission-control/ | Task orchestrator state |
| PLANILHA-INDEX.json | .claude/mission-control/ | Source sync snapshot |
| SOURCE-SYNC-STATE.json | .claude/mission-control/ | Source sync state |
| SESSION-*.md | .claude/sessions/ | Session logs |
| LATEST-SESSION.md | .claude/sessions/ | Most recent session pointer |

### 9.2 State Flow

```
Session Start
  |
  v
session_start.py --> Read JARVIS-STATE.json, MISSION-STATE.json
  |
  v
skill_indexer.py --> Scan skills/ + sub-agents/ --> Write SKILL-INDEX.json
  |
  v
[User Interaction]
  |
  v
PostToolUse hooks --> Update MISSION-STATE, session logs
  |
  v
Stop hooks --> Write HANDOFF, update session index, flush memory
```

---

## 10. OUTPUT ROUTING (core/paths.py)

`core/paths.py` is the single source of truth for all output paths. 146 lines, defines 50+ routing constants.

### Key Constants

| Constant | Path | Purpose |
|----------|------|---------|
| ROOT | Project root | Base for all paths |
| CORE | core/ | Engine directory |
| AGENTS | agents/ | Agent definitions |
| KNOWLEDGE_EXTERNAL | knowledge/external/ | Expert knowledge (Bucket 1) |
| KNOWLEDGE_WORKSPACE | knowledge/workspace/ | Business data (Bucket 2) |
| KNOWLEDGE_PERSONAL | knowledge/personal/ | Cognitive data (Bucket 3) |
| RAG_EXPERT | .data/rag_expert/ | Expert RAG index |
| RAG_BUSINESS | .data/rag_business/ | Business RAG index |
| KNOWLEDGE_GRAPH | .data/knowledge_graph/ | Entity graph |
| MISSION_CONTROL | .claude/mission-control/ | State files |

### ROUTING Dict (selected entries)

| Key | Target |
|-----|--------|
| audit_report | artifacts/audit/ |
| session_log | .claude/sessions/ |
| skill_index | .claude/mission-control/ |
| batch_log | logs/batches/ |
| handoff | logs/handoffs/ |
| rag_chunks | .data/rag_expert/ |
| graph | .data/knowledge_graph/ |
| memory_split | knowledge/external/dna/persons/ |
| nav_map | knowledge/external/ |
| download | inbox/ |
| workspace_data | knowledge/workspace/ |
| personal_data | knowledge/personal/ |

### PROHIBITED Paths

- `docs/` -- blocked for new file creation; use `reference/` instead

---

## 11. DEPENDENCIES

### 11.1 Node.js (package.json)

| Package | Version | Purpose |
|---------|---------|---------|
| boxen | ^8.0.1 | CLI box drawing |
| chalk | ^5.3.0 | CLI color output |
| fs-extra | ^11.2.0 | File system utilities |
| gradient-string | ^3.0.0 | CLI gradient text |
| inquirer | ^12.3.0 | Interactive CLI prompts |
| ora | ^8.1.1 | CLI spinners |

Dev dependencies: execa (^9.5.2), js-yaml (^4.1.0)

### 11.2 Python (pyproject.toml)

Core: PyYAML only. Python >= 3.11.

| Group | Packages |
|-------|----------|
| pipeline | PyYAML |
| speakers | pyannote.audio, torch, scipy, assemblyai |
| rag | voyageai, rank-bm25 |
| dev | pytest, pytest-cov, ruff, pyright |

### 11.3 MCP Servers (.mcp.json)

| Server | Type | Package/Command |
|--------|------|-----------------|
| mega-brain-knowledge | Python | core/intelligence/rag/mcp_server.py |
| n8n-mcp | npx | n8n-mcp |
| read-ai | npx | mcp-remote (SSE URL) |

---

## 12. WORKFLOWS (core/workflows/)

| Workflow | Phases | Tasks |
|----------|--------|-------|
| wf-pipeline-full.yaml | 5 phases | ingest, organize, tag, process, agents |
| wf-extract-dna.yaml | 3 phases | chunk, extract, consolidate |
| wf-conclave.yaml | 4 phases | activate, debate, synthesize, record |
| wf-ingest.yaml | 2 phases | classify, organize |

Workflows are executed by `task_orchestrator.py` which reads YAML definitions and resolves task markdown files from `core/tasks/`.

---

## 13. DNA SCHEMA (5 Knowledge Layers)

| Layer | Name | ID Format | Description |
|-------|------|-----------|-------------|
| L1 | PHILOSOPHIES | FIL-{PERSON}-{NNN} | Core beliefs and worldview |
| L2 | MENTAL-MODELS | MM-{PERSON}-{NNN} | Thinking and decision frameworks |
| L3 | HEURISTICS | HEUR-{PERSON}-{NNN} | Practical rules and decision shortcuts |
| L4 | FRAMEWORKS | FW-{PERSON}-{NNN} | Structured methodologies and processes |
| L5 | METHODOLOGIES | MET-{PERSON}-{NNN} | Step-by-step implementations |

DNA is stored in YAML files under `knowledge/external/dna/persons/{person-id}/` and referenced by agents via `DNA-CONFIG.yaml`.

---

## 14. KNOWLEDGE ROUTING

```
Raw Material (inbox/)
  |
  v
pipeline_router.py          # Classify: external / workspace / personal
  |
  +---> knowledge/external/    # Expert content
  |       +-- chunker.py       # 512-token chunks
  |       +-- hybrid_index.py  # BM25 + vector index
  |       +-- graph_builder.py # Knowledge graph
  |
  +---> knowledge/workspace/   # Business data
  |       +-- Separate RAG index (.data/rag_business/)
  |
  +---> knowledge/personal/    # Cognitive/private
          +-- Local index only (never published)
```

### RAG Isolation

Each bucket maintains separate RAG indexes to prevent data leakage:
- Expert knowledge: `.data/rag_expert/`
- Business data: `.data/rag_business/`
- Personal data: `knowledge/personal/index/` (L3 only)

---

## 15. CLI ENTRY POINTS

| Command | Binary | Script | Purpose |
|---------|--------|--------|---------|
| `npx @thiagofinch/mega-brain` | @thiagofinch/mega-brain | bin/cli.js | Main CLI wrapper |
| `npx mega-brain` | mega-brain | bin/mega-brain.js | Alternative entry |
| `npx mega-brain-push` | mega-brain-push | bin/push.js | Git push helper |

### npm Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| start | bin/cli.js | Run CLI |
| validate | bin/validate-package.js | Validate package structure |
| lint | ruff check core/ | Python linting |
| format | ruff format core/ | Python formatting |
| test | pytest tests/python | Run Python tests |
| postinstall | bin/install-hooks.js | Auto-install hooks |
| prepublishOnly | bin/pre-publish-gate.js | Publish safety gate |

---

## 16. TEST INFRASTRUCTURE

| Test File | Covers |
|-----------|--------|
| test_audit_layers.py | core/intelligence/validation/ |
| test_bucket_processor.py | core/intelligence/pipeline/bucket_processor.py |
| test_chunker.py | core/intelligence/rag/chunker.py |
| test_pipeline_router.py | core/intelligence/pipeline/pipeline_router.py |
| test_batch_governor.py | core/intelligence/pipeline/batch_governor.py |
| test_memory_manager.py | core/intelligence/memory_manager.py |
| test_context_scorer.py | core/intelligence/context_scorer.py |
| test_persona_fidelity.py | Agent persona consistency |

Coverage threshold: 40% (pyproject.toml `fail_under = 40`).

---

## 17. SKILLS OVERVIEW

95+ skill directories in `.claude/skills/`, each containing a `SKILL.md` with:
- Auto-Trigger conditions
- Keywords for auto-routing
- Priority (ALTA/MEDIA/BAIXA)
- Tools used
- "When NOT to activate" section

Skills are indexed at session start by `skill_indexer.py` into `SKILL-INDEX.json`, then matched against user prompts by `skill_router.py` in the UserPromptSubmit hook.

Skill categories include: knowledge-extraction, pipeline-jarvis, teaching, source-sync, save/resume, pdf/xlsx processing, conclave, GSD workflow, squad management, brand/copy/storytelling, and many more.

---

## 18. SLASH COMMANDS

| Command | Purpose |
|---------|---------|
| /jarvis-briefing | Operational status + health score |
| /jarvis-full | Full pipeline (ingest + process + enrich) |
| /process-jarvis | Pipeline processor (5 phases) |
| /conclave | Council session (multi-agent debate) |
| /ingest | Ingest new material |
| /save | Save current session |
| /resume | Resume previous session |
| /setup | Environment setup wizard |
| /mission | Mission control |
| /verify | Post-session verification |
| /source-sync | Sync with source spreadsheet |
| /rag-search | Semantic search in knowledge base |
| /extract-dna | Extract DNA from source material |
| /extract-knowledge | Knowledge extraction agent |

---

*END OF BROWNFIELD DISCOVERY -- MEGA BRAIN*
*Document generated: 2026-03-08*
