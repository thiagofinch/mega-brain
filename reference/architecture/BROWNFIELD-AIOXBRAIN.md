# Brownfield Discovery: aiox-brain

> **Date:** 2026-03-08
> **Analyst:** Tiny Rick (Architect Agent)
> **Source:** `/Users/thiagofinch/Documents/Projects/aiox-brain/`
> **Scope:** Complete technical analysis of aiox-brain, with focus on MMOS pipeline
> **Status:** COMPLETE

---

## Executive Summary

aiox-brain is a fork of mega-brain-ai v1.3.0 that merges the original Mega Brain knowledge system with MMOS (Mental Model Operating System) -- a cognitive cloning pipeline created by Alan Nicolas. The MMOS subsystem is the only significant new component; the rest is a near-identical copy of mega-brain with minor additions.

Key findings:
- MMOS is a **12,114-line Python library** (18 modules) implementing a full cognitive clone pipeline
- It is **100% self-contained** -- zero imports from `.aiox-core` or external AIOS frameworks
- Core intelligence scripts (RAG, speakers, entities) are **identical** to mega-brain
- The `.aiox-core/` directory is an external SDK (not authored in this repo)
- 33 hooks in `.aiox/hooks/` are unique to aiox-brain; only 2 are shared with mega-brain
- MMOS adds Supabase DB persistence, Gemini Flash integration, and a pytransitions state machine

---

## FASE 1: MMOS Pipeline (Deep Analysis)

### 1.1 Architecture Overview

```
squads/mmos/                          # 320+ files
  config.yaml                         # Squad config v4.0.0
  requirements.txt                    # Python deps (pyyaml, requests, google-generativeai, structlog, transitions, rich, supabase, fastapi, pytest)
  lib/                                # 18 Python modules, 12,114 LOC
    map_mind.py              (978 LOC) # CLI entry point, argparse, resume mode
    workflow_orchestrator.py (1135 LOC) # Phase sequencer, safe_eval, async parallel layers
    gemini_analyzer.py       (1086 LOC) # Gemini Flash 2.0, 2-level cache, async groups
    db_persister.py          (~900 LOC) # Supabase persistence (minds, fragments, scores, drivers)
    debate_engine.py         (~500 LOC) # Clone debate orchestration, fidelity scoring
    state_machine.py         (531 LOC) # pytransitions FSM, 11 states, YAML persistence
    workflow_detector.py     (454 LOC) # Auto-detection: greenfield/brownfield, public/private
    metadata_manager.py      (388 LOC) # Pipeline state in metadata.yaml
    sources_importer.py      (~770 LOC) # Supabase content import (sources + artifacts)
    checkpoints.py           (560 LOC) # Human checkpoint with rich UI, keyboard shortcuts
    progress.py              (624 LOC) # Rich progress bars, ETA estimation
    cache.py                 (390 LOC) # L1 memory cache (LRU, TTL, size-based eviction)
    metrics.py               (545 LOC) # Token/time/cost tracking per phase
    notifications.py         (451 LOC) # Async webhook notifications (httpx)
    summary.py               (406 LOC) # Pipeline summary generator (rich + markdown)
    logging_config.py        (291 LOC) # structlog configuration
    utils.py                 (137 LOC) # Path traversal security
    workflow_preprocessor.py (154 LOC) # YAML import expander
  workflows/                          # 2 master workflows + 9 shared modules
    greenfield-mind.yaml     (264 LOC) # Full pipeline (mode-detect -> finalize)
    brownfield-mind.yaml     (333 LOC) # Incremental update (delta analysis, regression, rollback)
    modules/                          # 7+ shared modules (~620 LOC total)
      analysis-foundation.yaml        # DNA Mental Layers 1-5
      analysis-critical.yaml          # Layers 6-8 + checkpoints
      synthesis-knowledge.yaml        # Frameworks, communication, signatures
      synthesis-cross-layer.yaml      # Cross-layer pattern synthesis (v4.1)
      synthesis-kb.yaml               # KB chunking + specialists
      implementation-identity.yaml    # Identity core extraction
      implementation-prompt.yaml      # System prompt + manual
      validation-complete.yaml        # Testing, fidelity, approval
      self-model.yaml                 # Self-model generation
  tasks/                              # 38 subdirectories with 65+ task markdown files
  templates/                          # 66 template files
  agents/                             # 11 agent definitions (8 legendary + extras)
  tests/                              # 28 test files (pytest)
  schemas/                            # JSON schemas for validation
  scripts/                            # Emulator, utilities
  docs/                               # Epics, stories, technical docs
```

### 1.2 Pipeline Flow

The MMOS pipeline implements a 2x2 matrix:

| | Greenfield (new clone) | Brownfield (update clone) |
|---|---|---|
| **Public figure** | Web scraping + APEX viability | Incremental web search |
| **Private individual** | Interviews OR provided materials | Add new materials, delta analysis |

**Greenfield sequence (8 phases):**
1. Phase 0: Mode Detection (Victoria)
2. Phase 1: Viability + Research (Victoria + Tim)
3. Phases 2-7: Shared modules (Daniel, Barbara, Brene, Charlie, Constantin, Quinn)
4. Phase 8: Finalization (Victoria)

**Brownfield sequence (9 phases):**
1. Phase 0: Assessment + Mandatory Backup
2. Phase 1: Incremental Research
3. Phase 2: Delta Analysis (smart re-analysis)
4. Phases 3-7: Shared modules (selective execution)
5. Phase 8: Regression Testing
6. Phase 9: COMMIT/ROLLBACK Decision

### 1.3 Eight Legendary Agents

| Agent | Slug | Phase Ownership |
|-------|------|-----------------|
| Victoria | viability-specialist | Init, viability, finalization |
| Tim | research-specialist | Research, source collection |
| Daniel | behavioral-analyst | Layers 1-3 (behavioral patterns) |
| Barbara | cognitive-architect | Layers 4-5 (mental models) |
| Brene | identity-analyst | Layers 6-8 (values, obsessions, paradoxes) |
| Charlie | synthesis-expert | Synthesis, KB chunking |
| Constantin | implementation-architect | Identity core, system prompts |
| Quinn | quality-specialist | QA, validation, fidelity testing |

### 1.4 State Machine (pytransitions)

11 states with YAML persistence for resume capability:

```
init -> research -> L1_L3 -> L4_L5 -> L6_L8 -> checkpoint_L6_8 ->
  synthesis -> implementation -> validation -> complete
  (any) -> failed (with recover transition)
  checkpoint_L6_8 -> L6_L8 (revision loop)
```

State is persisted at `outputs/minds/{slug}/metadata/pipeline_state.yaml`.

### 1.5 Gemini Flash Integration

- Two-level caching: L1 (memory LRU, 1h TTL, 100MB max) + L2 (filesystem, 7d TTL)
- Cache key: SHA256(layer_id + content_hash + model + params)
- Async execution with semaphore rate limiting
- Layer groups: GROUP_1 (L1-L3), GROUP_2 (L4-L5), GROUP_3 (L6-L8)
- Human checkpoint between GROUP_2 and GROUP_3
- Cost comparison: Gemini Flash vs Claude pricing estimation

### 1.6 Supabase Persistence

Tables used by `db_persister.py`:
- `minds` - Central registry (metadata JSONB)
- `mind_system_mappings` - Assessment results (MBTI, Big5)
- `mind_component_scores` - Per-component scores
- `mind_drivers` - Cognitive drivers + values + obsessions
- `drivers` - Driver definitions (FK target)
- `fragments` - Knowledge base chunks
- `mind_tools` - Frameworks/tools used by mind
- `component_driver_map` - Component-to-driver inference
- `job_executions` - Pipeline execution tracking
- `contents` - Source materials and artifacts

SQL function: `infer_drivers_from_scores(mind_id)` for automatic driver inference.

### 1.7 Security

- `utils.py`: Path traversal protection with symlink attack detection (MMOS-002)
- `workflow_orchestrator.py`: `safe_eval_condition()` uses AST parsing to block code injection in workflow `skip_if` conditions
- `map_mind.py`: Input sanitization for person slugs

### 1.8 Import Dependencies

**Critical finding: MMOS has ZERO imports from `.aiox-core` or any AIOS framework.**

All `.aiox-core` references found are documentation-only (in `docs/stories/`, `workflows/README.md`). The MMOS library is 100% self-contained with these external dependencies:
- `pyyaml` (YAML parsing)
- `requests` (HTTP calls for web search)
- `google-generativeai` (Gemini API)
- `structlog` (structured logging)
- `transitions` (state machine)
- `rich` (terminal UI)
- `supabase` / `psycopg2` (database, optional)
- `fastapi` / `uvicorn` (API, optional)
- `httpx` (async HTTP for webhooks, optional)

### 1.9 Workflow Module System

The `workflow_preprocessor.py` expands `import:` directives in YAML workflows before execution. Modules follow a standard format:

```yaml
module:
  id: module-id
  version: 1.0.0
phases:
  - agent: behavioral-analyst
    phase: analysis
    creates: artifact-name
```

Only the `phases:` section is expanded into the parent workflow. This achieves 66% reduction in workflow LOC (3,023 -> ~1,020 lines).

---

## FASE 2: Core Intelligence Comparison

### 2.1 RAG Scripts (11 files)

| File | mega-brain | aiox-brain | Status |
|------|-----------|------------|--------|
| adaptive_router.py | Yes | Yes | IDENTICAL |
| associative_memory.py | Yes | Yes | IDENTICAL |
| chunker.py | Yes | Yes | IDENTICAL |
| evaluator.py | Yes | Yes | IDENTICAL |
| graph_builder.py | Yes | Yes | IDENTICAL |
| graph_query.py | Yes | Yes | IDENTICAL |
| hybrid_index.py | Yes | Yes | IDENTICAL |
| hybrid_query.py | Yes | Yes | IDENTICAL |
| mcp_server.py | Yes | Yes | IDENTICAL |
| ontology_layer.py | Yes | Yes | IDENTICAL |
| self_rag.py | Yes | Yes | IDENTICAL |
| pipeline.py | No | Yes | **UNIQUE to aiox-brain** |

`pipeline.py` in aiox-brain's RAG directory is the only RAG difference.

### 2.2 Speakers (5 files) -- IDENTICAL

Both projects have identical speaker diarization scripts:
- `speaker_gate.py`, `speaker_labeler.py`, `voice_diarizer.py`, `voice_embedder.py`, `voice_registry.py`

### 2.3 Entities (5 files) -- IDENTICAL

Both projects have identical entity detection scripts:
- `bootstrap_registry.py`, `business_model_detector.py`, `entity_normalizer.py`, `org_chain_detector.py`, `role_detector.py`

### 2.4 Retrieval (4 files) -- IDENTICAL

Both projects: `context_assembler.py`, `memory_splitter.py`, `nav_map_builder.py`, `query_analyzer.py`

### 2.5 Pipeline Intelligence (5 files) -- IDENTICAL to mega-brain

`autonomous_processor.py`, `pipeline_heal.py`, `session_autosave.py`, `sync_package_files.py`, `task_orchestrator.py`

### 2.6 UNIQUE to aiox-brain (core/intelligence/)

| Directory | Files | Purpose |
|-----------|-------|---------|
| `dossier/` | dossier_tracer.py, dossier_trigger.py, review_dashboard.py, theme_analyzer.py | Dossier lifecycle management |
| `roles/` | skill_generator.py, sow_generator.py, tool_discovery.py, viability_scorer.py | Role-based generation |
| `agents/` | agent_trigger.py | Agent auto-creation triggers |

These 9 unique files extend mega-brain's intelligence layer with dossier management and agent lifecycle automation.

---

## FASE 3: Hooks and Rules Comparison

### 3.1 Hooks Overlap

| Category | Count |
|----------|-------|
| Shared between both projects | 2 (`skill_indexer.py`, `user_prompt_submit.py`) |
| Unique to mega-brain (`.claude/hooks/`) | 33 |
| Unique to aiox-brain (`.aiox/hooks/`) | 33 |

### 3.2 Hooks Unique to aiox-brain (`.aiox/hooks/`)

| Hook | Purpose | Integration Value |
|------|---------|-------------------|
| `mind-clone-governance.py` | Governance rules for clone operations | HIGH -- MMOS-specific |
| `sql-governance.py` | Supabase query governance | MEDIUM -- if adopting DB |
| `token_monitor.py` | Token usage monitoring | HIGH -- cost control |
| `token_checkpoint.py` | Token budget checkpoints | HIGH -- cost control |
| `elicitation_gate.py` | Interview protocol gating | MEDIUM -- MMOS-specific |
| `elicitation_reset.py` | Reset interview state | LOW -- MMOS-specific |
| `multi_agent_hook.py` | Multi-agent coordination | MEDIUM |
| `subagent_tracker.py` | Sub-agent lifecycle tracking | MEDIUM |
| `memory_bank_loader.py` | Memory bank auto-loading | MEDIUM |
| `dna_skill_generator.py` | Generate skills from DNA | HIGH -- knowledge automation |
| `framework_to_skill.py` | Convert frameworks to skills | HIGH -- knowledge automation |
| `agent_doctor.py` | Agent quality diagnostics | HIGH -- quality system |
| `post_output_validator.py` | Output quality scoring | HIGH -- quality system |
| `pattern_analyzer.py` | Request pattern detection | MEDIUM |
| `pattern_persistence.py` | Pattern learning persistence | MEDIUM |
| `post_ingestion_embeddings.py` | Auto-embed after ingestion | HIGH -- RAG pipeline |
| `post_ingestion_kg_rebuild.py` | Auto-rebuild knowledge graph | HIGH -- RAG pipeline |
| `document_trigger.py` | Document creation triggers | MEDIUM |
| `post_write_validator.py` | Post-write validation | MEDIUM |
| `write-path-validation.py` | Path validation on write | MEDIUM |
| `read-protection.py` | Read access protection | MEDIUM |
| `slug-validation.py` | Slug format validation | LOW |
| `auto_formatter.py` | Auto-format outputs | LOW |
| `checkpoint_writer.py` | Checkpoint state writer | MEDIUM |
| `claude_md_updater.py` | Auto-update CLAUDE.md | MEDIUM |
| `council_logger.py` | Council session logging | MEDIUM |
| `ledger_updater.py` | Financial ledger updates | LOW -- domain-specific |
| `migrate_frameworks.py` | Framework migration utility | LOW -- one-time |
| `notification_system.py` | Notification dispatch | MEDIUM |
| `session_log.py` | Session logging | LOW -- have similar |
| `status_line.py` | Status line display | LOW |
| `jarvis_briefing.py` | Briefing generation | LOW -- have similar |

### 3.3 Hooks Unique to mega-brain (`.claude/hooks/`)

33 hooks unique to mega-brain including: `creation_validator.py`, `directory_contract_guard.py`, `gsd-*.js` (3 GSD hooks), `ralph_wiggum.py`, `stop_hook_completeness.py`, and others. These are mega-brain's mature governance system and should NOT be replaced.

### 3.4 Rules

aiox-brain appears to have a different rules directory structure in `.aiox-core/` (external SDK) rather than `.claude/rules/`. mega-brain's rules system is more mature and comprehensive (30 rules across 6 groups).

---

## FASE 4: Dependencies and Infrastructure

### 4.1 package.json Comparison

| Field | mega-brain | aiox-brain |
|-------|-----------|------------|
| name | mega-brain-ai | mega-brain-ai |
| version | 1.3.0 | 1.3.0 |
| deps | boxen, chalk, fs-extra, gradient-string, inquirer, ora | boxen, chalk, gradient-string, inquirer, ora |
| devDeps | execa, js-yaml | execa, js-yaml |

aiox-brain is **missing `fs-extra`** from dependencies. Otherwise identical.

### 4.2 Python Dependencies

| Dependency | mega-brain | aiox-brain (root) | MMOS-specific |
|------------|-----------|-------------------|---------------|
| PyYAML | Yes | Yes | Yes |
| pyannote.audio | Yes | Yes | -- |
| torch/torchaudio | Yes | Yes | -- |
| google-generativeai | -- | -- | Yes |
| structlog | -- | -- | Yes |
| transitions | -- | -- | Yes |
| rich | -- | -- | Yes |
| supabase | -- | -- | Yes |
| fastapi | -- | -- | Yes |
| uvicorn | -- | -- | Yes |
| pydantic | -- | -- | Yes |
| httpx | -- | -- | Yes (notifications) |
| psycopg2 | -- | -- | Yes (sources_importer) |

### 4.3 .aiox-core SDK

The `.aiox-core/` directory is an **external SDK** (CreatorOS/AIOS framework), not authored within this project. Contains:
- `core-config.yaml` - AIOS configuration
- `constitution.md` - Framework rules
- `cli/` - CLI tools
- `infrastructure/` - Agent infrastructure
- `development/` - Development tools (architect agent definition)
- `install-manifest.yaml` - 36KB installation manifest

This SDK provides the "squad" architecture pattern (config.yaml, agents, tasks, workflows, templates, checklists) but MMOS does NOT depend on it at runtime.

---

## FASE 5: Knowledge Structure

### 5.1 Knowledge Directory

```
aiox-brain/knowledge/
  NAVIGATION-MAP.json              # Auto-generated nav map
  README.md
  external/
    dna/
      DOMAINS-TAXONOMY.yaml        # Domain taxonomy
      _dna-skills-registry.yaml    # Skills extracted from DNA
      maps/
        MAP-CONFLITOS.yaml         # Cross-source conflict resolution
      persons/
        jordan-lee/
          CONFIG.yaml, FILOSOFIAS.yaml, FRAMEWORKS.yaml,
          HEURISTICAS.yaml, METODOLOGIAS.yaml, MODELOS-MENTAIS.yaml
        richard-linder/
          (same 6 files)
        the-scalable-company/
          (same 6 files)
```

### 5.2 DNA Schema Format

Each person's DNA uses 5 knowledge layers in YAML:
1. `FILOSOFIAS.yaml` -- Core beliefs and worldview
2. `MODELOS-MENTAIS.yaml` -- Thinking and decision frameworks
3. `HEURISTICAS.yaml` -- Practical rules and shortcuts
4. `FRAMEWORKS.yaml` -- Structured methodologies
5. `METODOLOGIAS.yaml` -- Step-by-step implementations

Plus `CONFIG.yaml` for metadata (sources, weights, paths).

This is the **same structure** as mega-brain's DNA schema.

### 5.3 MMOS Output Format

MMOS clones output to `outputs/minds/{slug}/`:
```
outputs/minds/{slug}/
  metadata/
    mode.yaml                # Workflow mode
    config.yaml              # Clone config
    metadata.yaml            # Pipeline state (v1 of state machine)
    pipeline_state.yaml      # pytransitions state (v2)
    temporal_context.yaml    # Time-based source context
    version_history.yaml     # Brownfield version tracking
  sources/
    sources_master.yaml      # Source inventory
    {type}/                  # Categorized source files
  artifacts/
    *.yaml                   # Layer analysis artifacts
    cognitive_architecture.yaml
  system_prompts/            # Generated system prompts (versioned)
  kb/                        # Knowledge base chunks
  docs/
    PRD.md                   # Product Requirements Doc
    TODO.md                  # Task tracking
    LIMITATIONS.md           # Known limitations
    logs/                    # Execution logs (per-phase)
  metrics.yaml               # Token/time/cost metrics
  .backup-{timestamp}/       # Brownfield safety backups
```

### 5.4 TAG-RESOLVER.json

Found at `knowledge/external/dna/` -- aiox-brain uses the same tagging system as mega-brain. No separate TAG-RESOLVER.json was found in the MMOS directory structure; tagging is handled within the knowledge layer.

---

## File Inventory Summary

| Category | Count |
|----------|-------|
| MMOS Python files (total) | 50 |
| MMOS Python files (lib/) | 18 |
| MMOS lib lines of code | 12,114 |
| MMOS YAML files | 93 |
| MMOS task files | 65+ |
| MMOS template files | 66 |
| MMOS agent definitions | 11 |
| MMOS test files | 28 |
| aiox-brain unique hooks | 33 |
| Core intelligence unique files | 9 |
| Shared hooks (both projects) | 2 |

---

*Analysis by Tiny Rick (Architect Agent) -- 2026-03-08*
