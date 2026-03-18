# CROSS-REPO ANALYSIS: mega-brain x aiox-brain

> **Version:** 1.0.0
> **Date:** 2026-03-08
> **Analyst:** Tiny Rick (Architect Agent)
> **Inputs:** BROWNFIELD-MEGABRAIN.md, BROWNFIELD-AIOXBRAIN.md, TECHNICAL-GAPS.md, AIOXBRAIN-INTEGRATION-NOTES.md
> **Scope:** Script-by-script diff, MMOS feasibility, dependency delta, blocker analysis

---

## Section 1: Script-by-Script Diff

### 1.1 RAG Scripts (core/intelligence/rag/)

| Script | mega-brain | aiox-brain | Status | Notes |
|--------|-----------|------------|--------|-------|
| `adaptive_router.py` | Yes | Yes | IDENTICAL | 5-pipeline intent router |
| `associative_memory.py` | Yes | Yes | IDENTICAL | HippoRAG PPR implementation |
| `chunker.py` | Yes | Yes | IDENTICAL | 512-token recursive splitter |
| `evaluator.py` | Yes | Yes | IDENTICAL | RAGAS-inspired evaluation |
| `graph_builder.py` | Yes | Yes | IDENTICAL | Knowledge graph from DNA YAML |
| `graph_query.py` | Yes | Yes | IDENTICAL | 5 query types |
| `hybrid_index.py` | Yes | Yes | IDENTICAL | BM25 + Voyage AI vector |
| `hybrid_query.py` | Yes | Yes | IDENTICAL | 3-stage RRF fusion |
| `mcp_server.py` | Yes | Yes | IDENTICAL | MCP stdio JSON-RPC, 5 tools |
| `ontology_layer.py` | Yes | Yes | IDENTICAL | OG-RAG 5-layer DNA ontology |
| `self_rag.py` | Yes | Yes | IDENTICAL | Post-generation verification |
| `pipeline.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Both repos have this file. The brownfield incorrectly listed it as UNIQUE to aiox-brain. Actual content may have diverged -- diff required against the aiox-brain source. |
| `__init__.py` | Yes | Yes | IDENTICAL | Package init |

**Summary:** 11 confirmed identical. 1 needs manual diff (`pipeline.py`). 0 unique to either repo.

### 1.2 Pipeline Scripts (core/intelligence/pipeline/)

| Script | mega-brain | aiox-brain | Status | Notes |
|--------|-----------|------------|--------|-------|
| `autonomous_processor.py` | Yes | Yes | IDENTICAL | Queue-based file processor |
| `batch_governor.py` | Yes | Yes | IDENTICAL | Max-5 batch partitioner |
| `bucket_processor.py` | Yes | Yes | IDENTICAL | 3-layer knowledge ingest |
| `bucket_router.py` | Yes | Yes | IDENTICAL | Cross-bucket access control |
| `pipeline_heal.py` | Yes | Yes | IDENTICAL | Auto-heal (14 checks) |
| `pipeline_router.py` | Yes | Yes | IDENTICAL | External/workspace/personal routing |
| `read_ai_config.py` | Yes | Yes | IDENTICAL | Read.ai config loader |
| `read_ai_gardener.py` | Yes | Yes | IDENTICAL | Meeting transcript organizer |
| `read_ai_harvester.py` | Yes | Yes | IDENTICAL | Bulk Read.ai downloader |
| `read_ai_router.py` | Yes | Yes | IDENTICAL | Meeting classification |
| `session_autosave.py` | Yes | Yes | IDENTICAL | PostToolUse JSONL tracking |
| `sync_package_files.py` | Yes | Yes | IDENTICAL | package.json files sync |
| `task_orchestrator.py` | Yes | Yes | IDENTICAL | YAML workflow executor |
| `validate_layers.py` | Yes | Yes | IDENTICAL | Layer validation |

**Summary:** All 14 scripts identical. 0 diverged. 0 unique.

### 1.3 Speakers (core/intelligence/speakers/)

| Script | mega-brain | aiox-brain | Status |
|--------|-----------|------------|--------|
| `voice_diarizer.py` | Yes | Yes | IDENTICAL |
| `voice_embedder.py` | Yes | Yes | IDENTICAL |
| `voice_registry.py` | Yes | Yes | IDENTICAL |
| `speaker_labeler.py` | Yes | Yes | IDENTICAL |
| `speaker_gate.py` | Yes | Yes | IDENTICAL |

**Summary:** All 5 identical.

### 1.4 Entities (core/intelligence/entities/)

| Script | mega-brain | aiox-brain | Status |
|--------|-----------|------------|--------|
| `bootstrap_registry.py` | Yes | Yes | IDENTICAL |
| `entity_normalizer.py` | Yes | Yes | IDENTICAL |
| `role_detector.py` | Yes | Yes | IDENTICAL |
| `org_chain_detector.py` | Yes | Yes | IDENTICAL |
| `business_model_detector.py` | Yes | Yes | IDENTICAL |

**Summary:** All 5 identical.

### 1.5 Retrieval (core/intelligence/retrieval/)

| Script | mega-brain | aiox-brain | Status |
|--------|-----------|------------|--------|
| `context_assembler.py` | Yes | Yes | IDENTICAL |
| `memory_splitter.py` | Yes | Yes | IDENTICAL |
| `nav_map_builder.py` | Yes | Yes | IDENTICAL |
| `query_analyzer.py` | Yes | Yes | IDENTICAL |

**Summary:** All 4 identical.

### 1.6 Dossier (core/intelligence/dossier/)

**CORRECTION:** The aiox-brain brownfield doc (section 2.6) listed these as "UNIQUE to aiox-brain." This is INCORRECT. All 4 files exist in mega-brain as confirmed by filesystem inspection.

| Script | mega-brain | aiox-brain | Status | Notes |
|--------|-----------|------------|--------|-------|
| `dossier_tracer.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error -- both repos have this |
| `dossier_trigger.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error -- both repos have this |
| `review_dashboard.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error -- both repos have this |
| `theme_analyzer.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error -- both repos have this |

**Summary:** All 4 exist in both repos. Content may be identical or diverged -- requires manual diff against aiox-brain source files.

### 1.7 Roles (core/intelligence/roles/)

**CORRECTION:** Same issue as dossier -- the brownfield doc listed these as unique to aiox-brain but they exist in mega-brain.

| Script | mega-brain | aiox-brain | Status | Notes |
|--------|-----------|------------|--------|-------|
| `skill_generator.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error |
| `sow_generator.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error |
| `tool_discovery.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error |
| `viability_scorer.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error |

**Summary:** All 4 exist in both repos. Diff required.

### 1.8 Agents (core/intelligence/agents/)

**CORRECTION:** Same issue -- `agent_trigger.py` exists in both repos.

| Script | mega-brain | aiox-brain | Status | Notes |
|--------|-----------|------------|--------|-------|
| `agent_trigger.py` | Yes | Yes | **NEEDS MANUAL REVIEW** | Brownfield doc error |

### 1.9 Top-Level Intelligence (core/intelligence/)

| Script | mega-brain | aiox-brain | Status |
|--------|-----------|------------|--------|
| `context_scorer.py` | Yes | Yes | IDENTICAL |
| `memory_manager.py` | Yes | Yes | IDENTICAL |

### 1.10 Validation (core/intelligence/validation/)

| Script | mega-brain | aiox-brain | Status |
|--------|-----------|------------|--------|
| Audit + validation scripts | Yes | Yes | IDENTICAL |

### 1.11 Utils (core/intelligence/utils/)

| Script | mega-brain | aiox-brain | Status |
|--------|-----------|------------|--------|
| `auto_organize_inbox.py` | Yes | Yes | IDENTICAL |
| `classify_unknown.py` | Yes | Yes | IDENTICAL |

### 1.12 UNIQUE to aiox-brain (MMOS Pipeline)

These files exist ONLY in aiox-brain's `squads/mmos/lib/` directory. They have NO equivalent in mega-brain.

| Script | LOC | Purpose |
|--------|-----|---------|
| `map_mind.py` | 978 | CLI entry point with argparse, resume mode |
| `workflow_orchestrator.py` | 1,135 | Phase sequencer, safe_eval, async parallel |
| `gemini_analyzer.py` | 1,086 | Gemini Flash 2.0 with 2-level cache |
| `db_persister.py` | ~900 | Supabase persistence (10 tables) |
| `debate_engine.py` | ~500 | Clone debate orchestration |
| `state_machine.py` | 531 | pytransitions FSM (11 states, YAML persist) |
| `workflow_detector.py` | 454 | Auto-detect greenfield/brownfield |
| `metadata_manager.py` | 388 | Pipeline state tracking in metadata.yaml |
| `sources_importer.py` | ~770 | Supabase content import |
| `checkpoints.py` | 560 | Human checkpoint with rich UI |
| `progress.py` | 624 | Rich progress bars + ETA |
| `cache.py` | 390 | L1 LRU cache (TTL, size eviction) |
| `metrics.py` | 545 | Token/time/cost tracking per phase |
| `notifications.py` | 451 | Async webhook notifications |
| `summary.py` | 406 | Pipeline summary generator |
| `logging_config.py` | 291 | structlog configuration |
| `utils.py` | 137 | Path traversal security |
| `workflow_preprocessor.py` | 154 | YAML import expander |

**Total unique MMOS code:** 18 files, 12,114 lines.

### 1.13 UNIQUE to mega-brain

No unique scripts in `core/intelligence/` that are absent from aiox-brain. mega-brain's unique value is in its hooks, rules, skills, and agent ecosystem -- not in the intelligence scripts.

### 1.14 Script Diff Summary

| Category | Total | IDENTICAL | NEEDS MANUAL REVIEW | UNIQUE to aiox (MMOS) | UNIQUE to mega-brain |
|----------|-------|-----------|---------------------|----------------------|---------------------|
| RAG | 13 | 12 | 1 | 0 | 0 |
| Pipeline | 14 | 14 | 0 | 0 | 0 |
| Speakers | 5 | 5 | 0 | 0 | 0 |
| Entities | 5 | 5 | 0 | 0 | 0 |
| Retrieval | 4 | 4 | 0 | 0 | 0 |
| Dossier | 4 | 0 | 4 | 0 | 0 |
| Roles | 4 | 0 | 4 | 0 | 0 |
| Agents | 1 | 0 | 1 | 0 | 0 |
| Top-level | 2 | 2 | 0 | 0 | 0 |
| Validation | ~2 | ~2 | 0 | 0 | 0 |
| Utils | 2 | 2 | 0 | 0 | 0 |
| MMOS lib | 18 | -- | -- | 18 | -- |
| **TOTAL** | **~74** | **~46** | **10** | **18** | **0** |

**Brownfield Doc Errata:** The aiox-brain brownfield document (section 2.6) incorrectly listed dossier/ (4 files), roles/ (4 files), and agents/ (1 file) as "UNIQUE to aiox-brain." These 9 scripts exist in both repositories. A manual diff against the aiox-brain source is required to determine whether they are identical or diverged.

---

## Section 2: MMOS Integration Feasibility

### 2.1 MMOS Module Standalone Status

Each module's standalone status was confirmed from the aiox-brain brownfield analysis. The critical finding is that MMOS has **zero imports from `.aiox-core` or any AIOS framework** -- it is 100% self-contained.

| Module | Standalone | External Dependencies | Integration Risk |
|--------|-----------|----------------------|-----------------|
| `state_machine.py` | YES | `transitions`, `pyyaml` | LOW |
| `workflow_orchestrator.py` | YES | `asyncio` (stdlib), requires state_machine + metadata_manager | LOW |
| `gemini_analyzer.py` | YES | `google-generativeai`, requires cache.py | LOW |
| `cache.py` | YES | None (stdlib only) | VERY LOW |
| `metrics.py` | YES | None (stdlib + pyyaml) | VERY LOW |
| `metadata_manager.py` | YES | `pyyaml` | VERY LOW |
| `workflow_detector.py` | YES | `pyyaml` | VERY LOW |
| `checkpoints.py` | YES | `rich` | LOW |
| `map_mind.py` | YES | Requires all above | MEDIUM (many internal deps) |
| `workflow_preprocessor.py` | YES | `pyyaml` | VERY LOW |
| `progress.py` | YES | `rich` | LOW |
| `summary.py` | YES | `rich` | LOW |
| `logging_config.py` | YES | `structlog` | LOW |
| `notifications.py` | YES | `httpx` | LOW |
| `utils.py` | YES | None (stdlib) | VERY LOW |
| `db_persister.py` | PARTIAL | `supabase`, `psycopg2` -- requires Supabase infrastructure | HIGH |
| `sources_importer.py` | PARTIAL | `supabase` -- requires Supabase infrastructure | HIGH |
| `debate_engine.py` | PARTIAL | Requires emulator module (not fully standalone) | MEDIUM |

### 2.2 MMOS Output Mapping to mega-brain Knowledge Structure

MMOS outputs to `outputs/minds/{slug}/`. This path does not exist in mega-brain and conflicts with the directory contract. Here is the mapping:

| MMOS Output Path | mega-brain Destination | paths.py Constant | Conflict? |
|------------------|----------------------|-------------------|-----------|
| `outputs/minds/{slug}/metadata/` | `.claude/mission-control/mmos/` | `ROUTING["pipeline_state"]` | NO -- new subdir, no conflict |
| `outputs/minds/{slug}/sources/` | `knowledge/external/inbox/` | `ROUTING["external_inbox"]` | NO -- aligns with existing pattern |
| `outputs/minds/{slug}/artifacts/*.yaml` | `knowledge/external/dna/persons/{slug}/` | `ROUTING["memory_split"]` | NO -- DNA schemas already go here |
| `outputs/minds/{slug}/system_prompts/` | `agents/external/{slug}/` | `AGENTS` constant | NO -- mega-brain already stores mind agents here |
| `outputs/minds/{slug}/kb/` | `.data/rag_expert/` | `ROUTING["rag_chunks"]` | NO -- chunks index already here |
| `outputs/minds/{slug}/docs/logs/` | `logs/mmos/` | `LOGS` constant | NO -- new subdir |
| `outputs/minds/{slug}/metrics.yaml` | `logs/mmos/{slug}-metrics.yaml` | `LOGS` constant | NO -- new subdir |
| `outputs/minds/{slug}/.backup-*/` | `.claude/trash/mmos-backups/` | `ROUTING["trash"]` | NO -- trash dir exists for this |

**Verdict:** No path conflicts with `core/paths.py`. All MMOS outputs can be routed to existing mega-brain directories. The adaptation requires:
1. Adding a `ROUTING["mmos_state"]` entry pointing to `MISSION_CONTROL / "mmos"`
2. Adding a `ROUTING["mmos_logs"]` entry pointing to `LOGS / "mmos"`
3. Modifying MMOS output paths in `metadata_manager.py` and `map_mind.py` to use `core.paths` constants

### 2.3 Hook Conflicts

| MMOS Concept | Existing mega-brain Hook | Conflict? | Resolution |
|--------------|-------------------------|-----------|------------|
| Token monitoring (`token_monitor.py`) | None | NO | New hook, clean addition |
| Token checkpoint (`token_checkpoint.py`) | None | NO | New hook, clean addition |
| Auto-embed after ingestion (`post_ingestion_embeddings.py`) | None (manual RAG rebuild) | NO | New hook, adds automation |
| Knowledge graph rebuild (`post_ingestion_kg_rebuild.py`) | None (manual graph rebuild) | NO | New hook, adds automation |
| Agent quality scoring (`agent_doctor.py` + `post_output_validator.py`) | `quality_watchdog.py` | PARTIAL | Overlapping concern. mega-brain's watchdog does detection/warning; aiox's agent_doctor adds fix proposals. Could complement, not replace. |
| DNA skill generation (`dna_skill_generator.py` + `framework_to_skill.py`) | `skill_generator.py` (core/intelligence/roles/) | PARTIAL | mega-brain has the core script; aiox-brain wraps it as a hook trigger. |
| Clone governance (`mind-clone-governance.py`) | None | NO | New hook, MMOS-specific |
| SQL governance (`sql-governance.py`) | None | NO | Only needed if Supabase is adopted |

**Verdict:** No blocking hook conflicts. 2 areas of partial overlap (quality scoring, skill generation) where the aiox-brain hooks could complement the existing mega-brain system rather than replace it.

### 2.4 paths.py Changes Required

New constants to add to `core/paths.py`:

```python
# ── MMOS PIPELINE ───────────────────────────────────────────────
MMOS = CORE / "intelligence" / "pipeline" / "mmos"
MMOS_WORKFLOWS = CORE / "workflows" / "mmos"

# Add to ROUTING dict:
ROUTING["mmos_state"] = MISSION_CONTROL / "mmos"
ROUTING["mmos_logs"] = LOGS / "mmos"
ROUTING["mmos_metrics"] = LOGS / "mmos"
ROUTING["mmos_backups"] = TRASH / "mmos-backups"
```

No existing constants need modification. These are purely additive.

---

## Section 3: Dependency Delta

### 3.1 Python Packages (aiox-brain but NOT mega-brain)

| Package | Required by MMOS? | Available on PyPI? | Required for Integration? | Notes |
|---------|-------------------|-------------------|--------------------------|-------|
| `google-generativeai>=0.3.0` | YES (gemini_analyzer.py) | YES | **YES for Wave 1** | Gemini Flash API client |
| `transitions>=0.9.0` | YES (state_machine.py) | YES | **YES for Wave 1** | pytransitions state machine |
| `structlog>=24.0.0` | YES (logging_config.py) | YES | **NO -- optional** | Can be replaced with stdlib logging |
| `rich>=13.0.0` | YES (checkpoints.py, progress.py, summary.py) | YES | **YES for Wave 2** | Terminal UI for checkpoints |
| `httpx>=0.25.0` | YES (notifications.py) | YES | **NO -- optional** | Only for webhook notifications |
| `supabase>=2.0.0` | YES (db_persister.py, sources_importer.py) | YES | **NO -- Wave 3 only** | Database persistence (optional) |
| `psycopg2>=2.9.0` | YES (sources_importer.py) | YES | **NO -- Wave 3 only** | PostgreSQL driver (optional) |
| `fastapi>=0.104.0` | YES (API endpoints) | YES | **NO -- optional** | Only for REST API exposure |
| `uvicorn>=0.24.0` | YES (API server) | YES | **NO -- optional** | Only for REST API server |
| `pydantic>=2.0.0` | YES (data models) | YES | **NO -- optional** | Data validation (FastAPI dep) |
| `requests>=2.31.0` | YES (web search in MMOS) | YES | **NO -- optional** | HTTP client for web research |

### 3.2 Minimum New Dependencies (Wave 1 + Wave 2)

```
transitions>=0.9.0          # State machine -- required
google-generativeai>=0.3.0  # Gemini Flash -- required
rich>=13.0.0                # Terminal UI -- required for checkpoints
```

These 3 packages are the minimum for a functional MMOS integration.

### 3.3 Node Packages

| Package | aiox-brain | mega-brain | Required? |
|---------|-----------|------------|-----------|
| `fs-extra` | MISSING | YES (^11.2.0) | N/A -- aiox-brain is missing this, not the other way |

No new Node packages are required for MMOS integration. MMOS is 100% Python.

### 3.4 Where to Declare Dependencies

Add to `pyproject.toml` as a new optional group:

```toml
[project.optional-dependencies]
mmos = [
    "transitions>=0.9.0",
    "google-generativeai>=0.3.0",
    "rich>=13.0.0",
    "structlog>=24.0.0",  # optional but recommended
]
mmos-db = [
    "supabase>=2.0.0",
    "psycopg2-binary>=2.9.0",
]
mmos-api = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
]
```

Install with: `pip install -e ".[mmos]"`

---

## Section 4: Critical Blocker Analysis

### 4.1 The Hardcoded Paths Problem

The TECHNICAL-GAPS document identified that 45+ scripts use hardcoded `Path(__file__).resolve().parent...` chains instead of importing from `core/paths.py`. Only 5 scripts currently import from `core.paths`.

### 4.2 Would MMOS Integration Be BLOCKED by Hardcoded Paths?

**NO -- MMOS integration is NOT blocked by existing hardcoded paths.**

Reasoning:

1. **MMOS is additive, not modifying.** The 18 MMOS files are NEW code placed in a NEW subdirectory (`core/intelligence/pipeline/mmos/`). They do not modify any existing scripts. The hardcoded paths in existing scripts are a maintenance problem, but they do not prevent new code from being added.

2. **MMOS scripts will use `core.paths` from day one.** Since we are writing the integration adapter, we can ensure all MMOS scripts import from `core.paths` rather than using hardcoded paths. This actually sets a precedent for fixing the existing scripts later.

3. **The directory contract is not violated.** MMOS outputs map cleanly to existing knowledge structure directories (Section 2.2). No existing output routing is disrupted.

4. **MMOS does not import from existing mega-brain scripts.** The MMOS pipeline is self-contained. It does not call `chunker.py`, `hybrid_index.py`, or any other existing intelligence script. It has its own analysis logic via Gemini Flash. Therefore, it does not inherit the hardcoded path problem.

### 4.3 Can MMOS Be Integrated BEFORE Fixing Hardcoded Paths?

**YES -- MMOS can be integrated before fixing hardcoded paths.**

The two efforts are independent:

| Effort | Scope | Dependencies |
|--------|-------|-------------|
| Fix hardcoded paths | 45+ existing scripts | None -- pure refactoring |
| Integrate MMOS | 18 new scripts + deps | None -- pure addition |

They can run in parallel. In fact, the MMOS integration serves as a good test case for the `core.paths` pattern, since all MMOS scripts will be written to use it.

### 4.4 Must Paths Be Fixed First?

**NO -- but fixing them first would be IDEAL for one reason:**

If hardcoded paths are fixed first, then a future refactoring of the directory structure (e.g., renaming `core/intelligence/pipeline/` to `core/pipeline/`) would not break MMOS scripts. But since no directory restructuring is currently planned, this is a theoretical concern, not a practical blocker.

### 4.5 Recommended Sequencing

```
PARALLEL TRACK A (no dependency on B):
  Wave 0 Pre-req fixes (deny list, AGENT-INDEX dupes, docs sync)
  |
  Wave 1 MMOS Foundation (state machine, orchestrator, Gemini)
  |
  Wave 2 MMOS Workflows + CLI

PARALLEL TRACK B (no dependency on A):
  Hardcoded path migration (45+ scripts -> core.paths imports)
  |
  pip install -e . (proper package installation)
  |
  sys.path hack removal

MERGE POINT:
  Both tracks complete -> full integration tests
```

### 4.6 Blocker Summary

| Potential Blocker | Status | Severity |
|-------------------|--------|----------|
| Hardcoded paths in existing scripts | **NOT A BLOCKER** for MMOS | N/A for integration |
| Missing Python dependencies | **Easily resolved** -- pip install | LOW |
| MMOS output path conflicts | **NO conflicts** found | CLEAR |
| Hook conflicts | **NO blocking conflicts** | CLEAR |
| .gitignore whitelist pattern | **NOT A BLOCKER** -- MMOS files go in tracked dirs (core/) | CLEAR |
| Missing GOOGLE_API_KEY | **Soft blocker** -- Gemini analyzer needs this in .env | LOW |
| Supabase infrastructure | **NOT required** -- DB persistence is optional (Wave 3) | N/A for Waves 1-2 |

**Verdict: There are ZERO hard blockers for MMOS integration.** The path to integration is clear.

---

## Appendix: Files Requiring Manual Diff

The following 10 files exist in both repositories but were either incorrectly labeled as "unique" in the brownfield docs or need verification of identical content. Before integration, run a diff of these files against their aiox-brain counterparts:

```
core/intelligence/rag/pipeline.py
core/intelligence/dossier/dossier_tracer.py
core/intelligence/dossier/dossier_trigger.py
core/intelligence/dossier/review_dashboard.py
core/intelligence/dossier/theme_analyzer.py
core/intelligence/roles/skill_generator.py
core/intelligence/roles/sow_generator.py
core/intelligence/roles/tool_discovery.py
core/intelligence/roles/viability_scorer.py
core/intelligence/agents/agent_trigger.py
```

If these are identical, no action needed. If diverged, evaluate which version is more mature and document the delta.

---

*CROSS-REPO ANALYSIS COMPLETE -- Tiny Rick (Architect Agent) -- 2026-03-08*
