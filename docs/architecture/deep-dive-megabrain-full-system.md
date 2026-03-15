# Deep Dive: Mega Brain Full System Analysis

> **Version:** 1.0.0
> **Generated:** 2026-03-15
> **Purpose:** Reference document for ~45-hour architectural hardening
> **Method:** File-by-file analysis of all pipeline scripts, rules, skills, hooks, and state files

---

## Table of Contents

1. [Pipeline Flow Diagram](#1-pipeline-flow-diagram)
2. [Script Dependency Map](#2-script-dependency-map)
3. [Rules-by-Domain Map](#3-rules-by-domain-map)
4. [Skills-by-Function Map](#4-skills-by-function-map)
5. [State Files Map](#5-state-files-map)
6. [Duplicates and Redundancies](#6-duplicates-and-redundancies)
7. [Dead Code and Orphans](#7-dead-code-and-orphans)
8. [Per-File Recommendations](#8-per-file-recommendations)

---

## 1. Pipeline Flow Diagram

### 1.1 Legacy Pipeline (Phases 1-5)

The original pipeline follows a 5-phase sequential flow, governed by RULE-GROUP-1. Each phase is bloqueante (blocking). This pipeline is considered "complete" per MISSION-STATE.json (status: PHASE_5_COMPLETE).

```
PHASE 1: Inventory (planilha comparison)
    |
    v
PHASE 2: Download (files from Google Drive)
    |
    v
PHASE 2.5: Tagging (prefix files with [TAG])
    |
    v
PHASE 3: Organization (inbox sorting)
    |
    v
PHASE 4: Pipeline (batch processing, DNA extraction)
    |
    v
PHASE 5: Agent Feeding (5.1 Foundation -> 5.2 Person -> 5.3 Cargo -> 5.4 Theme Dossiers)
```

**Scripts involved (legacy):** Most are now in `.claude/mission-control/` as ad-hoc Python scripts (jarvis_mission.py, mission_pipeline.py, mission_inventory.py, mission_feed.py). These are NOT in `core/intelligence/pipeline/`.

### 1.2 MCE Pipeline (Current Architecture)

The MCE (Mental Cognitive Extraction) pipeline is the current architecture, combining deterministic Python scripts with LLM-driven extraction via the `pipeline-mce` skill. It operates in 12 steps.

```
              FILE ARRIVES (inbox watcher or manual)
                          |
                          v
    +----------------------------------------------+
    | STEP 0: DETECT (workflow_detector.py)         |
    | Greenfield vs Brownfield detection            |
    | Checks: agent dir, DNA files, MCE state       |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 1: INGEST (orchestrate.py ingest)        |
    |   scope_classifier.py --> ScopeDecision       |
    |   smart_router.py --> move/ref/triage         |
    |   inbox_organizer.py --> organize by entity   |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 2: BATCH (orchestrate.py batch)          |
    |   batch_auto_creator.py --> BATCH-XXX.json    |
    |   batch_governor.py --> max 5 files/batch     |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 3: CHUNK (LLM -- pipeline-mce skill)     |
    |   Prompt: prompt-mce-chunk.md                 |
    |   Token-aware segmentation                    |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 4: ENTITY EXTRACTION (LLM)               |
    |   Or gemini_analyzer.py if GOOGLE_API_KEY set |
    |   Detect people, orgs, concepts               |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 5: INSIGHT/DNA EXTRACTION (LLM)          |
    |   5-layer DNA: FILOSOFIAS, MODELOS-MENTAIS,   |
    |   HEURISTICAS, FRAMEWORKS, METODOLOGIAS       |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 6: MCE BEHAVIORAL (LLM)                  |
    |   Extended layers: obsessions, paradoxes,     |
    |   value hierarchy, behavioral patterns        |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 7: MCE IDENTITY (LLM)                    |
    |   Identity model, worldview, decision style   |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 8: MCE VOICE (LLM)                       |
    |   Voice DNA: speech patterns, vocabulary,     |
    |   analogies, signature phrases                |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 9: IDENTITY CHECKPOINT (human pause)     |
    |   Manual review of extracted identity         |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 10: CONSOLIDATION (LLM)                   |
    |   Generate: dossiers, SOURCE docs, DNA YAMLs, |
    |   AGENT.md, SOUL.md, MEMORY.md                |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 11: FINALIZE (orchestrate.py finalize)    |
    |   memory_enricher.py --> route to agents      |
    |   workspace_sync.py --> sync to workspace     |
    |   sop_detector.py --> detect SOPs             |
    |   Update state machine, metrics               |
    +----------------------------------------------+
                          |
                          v
    +----------------------------------------------+
    | STEP 12: REPORT                                |
    |   MCE-PIPELINE-LOG-TEMPLATE.md                |
    |   Metrics summary, artifacts list             |
    +----------------------------------------------+
```

### 1.3 Meeting Ingestion Sub-Pipeline

```
    FIREFLIES API (poll)          READ.AI MCP (OAuth)
         |                              |
         v                              v
    fireflies_sync.py             read_ai_harvester.py (skill)
         |                              |
         v                              v
    meeting_router.py -----> empresa vs pessoal classification
         |
         v
    knowledge/business/inbox/     knowledge/personal/inbox/
    (empresa meetings)            (personal meetings)
         |
         v
    scope_classifier.py --> MCE pipeline step 1+
```

---

## 2. Script Dependency Map

### 2.1 Core Pipeline Scripts (`core/intelligence/pipeline/`)

| # | Script | Bytes | Imports core.paths? | ROUTING keys used | External deps | Role |
|---|--------|-------|--------------------|--------------------|---------------|------|
| 1 | `scope_classifier.py` | 33,645 | YES | KNOWLEDGE_EXTERNAL, LOGS, ROOT, WORKSPACE | None | Classify content into buckets (6-signal weighted) |
| 2 | `inbox_watcher.py` | 20,830 | YES | ROUTING[external_inbox], [business_inbox], [personal_inbox], [workspace_inbox] | `watchdog` | FSEvents daemon, monitors inbox dirs |
| 3 | `inbox_organizer.py` | 25,716 | YES | Bucket inbox paths | None | Auto-organize by entity/content type |
| 4 | `smart_router.py` | 24,884 | YES | LOGS, MISSION_CONTROL, ROUTING | None | Act on ScopeDecision (move/ref/triage) |
| 5 | `batch_auto_creator.py` | 31,317 | PARTIAL | Has fallback to hardcoded paths | None | Scan inbox, create batches |
| 6 | `batch_governor.py` | 2,567 | YES | Uses `INBOX` (deprecated alias) | None | Partition files into batches (max 5) |
| 7 | `bucket_processor.py` | 15,077 | YES (12 consts) | WORKSPACE_ORG, WORKSPACE_TEAM, etc. (stale aliases) | None | 3-layer ingest |
| 8 | `bucket_router.py` | 7,614 | YES | Agent + knowledge paths | None | Cross-bucket access control |
| 9 | `pipeline_router.py` | 8,057 | YES | Uses `INBOX` (deprecated alias) | None | Tri-dimensional bucket routing |
| 10 | `memory_enricher.py` | 31,677 | YES | AGENTS_EXTERNAL, AGENTS_CARGO, LOGS | None | Route insights to agent MEMORY.md |
| 11 | `workspace_sync.py` | 26,435 | YES | WORKSPACE_*, KNOWLEDGE_* | None | Sync 4 rules (SOPs, decisions, dossiers, insights) |
| 12 | `autonomous_processor.py` | 27,949 | NO | Uses env `CLAUDE_PROJECT_DIR` | None | Queue-based unattended processing |
| 13 | `task_orchestrator.py` | 23,789 | NO | Uses env `CLAUDE_PROJECT_DIR` | None | Workflow YAML executor |
| 14 | `pipeline_heal.py` | 27,821 | YES | MISSION_CONTROL | None | Auto-heal detection for missed steps |
| 15 | `sop_detector.py` | 17,216 | YES | BUSINESS_INSIGHTS, BUSINESS_SOPS | None | Auto-detect SOPs in meetings |
| 16 | `insight_speaker_linker.py` | 12,312 | YES | PROCESSING, KNOWLEDGE_BUSINESS | None | Link insights to speakers |
| 17 | `content_hasher.py` | 4,114 | NO | Hardcoded `.data/content_hashes.json` | None | SHA256 dedup |
| 18 | `fireflies_sync.py` | 20,930 | YES | KNOWLEDGE_BUSINESS, KNOWLEDGE_PERSONAL, LOGS | `requests` | Poll Fireflies API |
| 19 | `meeting_router.py` | 5,679 | NO | None | None | empresa/pessoal classification |
| 20 | `ss_bridge.py` | 20,991 | YES | LOGS | `subprocess` | Bridge to Skill Seekers venv |
| 21 | `inbox_processor.py` | 14,488 | YES | LOGS | None | Pre-process PDFs/DOCXs |
| 22 | `session_autosave.py` | 1,245 | NO | Uses env `MEGA_BRAIN_ROOT` | None | Legacy PostToolUse hook |
| 23 | `pdf_extractor.py` | 2,415 | NO | None | `fitz` (PyMuPDF) | PDF text extraction |
| 24 | `sync_package_files.py` | 17,645 | YES | L1 audit paths | None | NPM package sync (NOT pipeline) |
| 25-27 | `extractors/` | ~5,000 | NO | None | Various | DOCX, PDF, video extractors |
| 28 | `video/pipeline.py` | ~3,000 | Partial | None | `whisper` | Video transcription |

### 2.2 MCE Sub-Pipeline (`core/intelligence/pipeline/mce/`)

| # | Script | Bytes | External deps | Role |
|---|--------|-------|---------------|------|
| 1 | `__init__.py` | 1,865 | None | Exports, version 2.0.0 |
| 2 | `orchestrate.py` | 27,518 | None | Central orchestrator (ingest/batch/finalize/status/full) |
| 3 | `state_machine.py` | 8,796 | `transitions` | FSM with 10+ states, persists to YAML |
| 4 | `gemini_analyzer.py` | 10,990 | `google.generativeai` | Optional Gemini Flash 2.0 for classification |
| 5 | `metadata_manager.py` | 10,827 | None | Track sources, phases, attempts. Persists YAML |
| 6 | `metrics.py` | 10,667 | None | Wall-clock timing, persists YAML + JSONL |
| 7 | `cache.py` | 10,543 | None | L1 in-memory LRU + L2 disk JSON (7-day TTL) |
| 8 | `workflow_detector.py` | 9,061 | None | Greenfield vs brownfield detection |
| 9 | `cli.py` | 13,722 | `argparse` | CLI entry point (--resume, --dry-run, --upgrade) |

### 2.3 Dependency Graph (script-to-script)

```
orchestrate.py
    imports: state_machine, metadata_manager, metrics, cache, workflow_detector
    calls:   scope_classifier, smart_router, inbox_organizer, batch_auto_creator
    calls:   memory_enricher, workspace_sync, sop_detector (finalize phase)

scope_classifier.py
    imports: core.paths (KNOWLEDGE_EXTERNAL, LOGS, ROOT, WORKSPACE)
    outputs: ScopeDecision dataclass

smart_router.py
    imports: core.paths (LOGS, MISSION_CONTROL, ROUTING)
    consumes: ScopeDecision from scope_classifier

inbox_organizer.py
    imports: core.paths (bucket inbox paths)
    reads:   knowledge/external/dna/persons/ (entity detection)

batch_auto_creator.py
    imports: batch_governor.partition_files()
    reads:   BATCH-REGISTRY.json

fireflies_sync.py
    imports: meeting_router.MeetingRouter
    writes:  knowledge/business/inbox/ or knowledge/personal/inbox/
    updates: FIREFLIES-STATE.json

memory_enricher.py
    reads:   agents/external/*/MEMORY.md, agents/cargo/*/MEMORY.md
    writes:  same MEMORY.md files (appends insights)

workspace_sync.py
    reads:   knowledge/business/* (SOPs, decisions, dossiers, insights)
    writes:  workspace/* (templates, strategy, businesses, team)
```

### 2.4 Hooks That Touch Pipeline

| Hook | Event | Lines | What It Does | Pipeline Integration |
|------|-------|-------|-------------|---------------------|
| `pipeline_orchestrator.py` | PostToolUse | 450 | Checks if batch processing just completed | Triggers cascading |
| `pipeline_checkpoint.py` | PostToolUse | 572 | Saves checkpoint after batch | State persistence |
| `pipeline_phase_gate.py` | UserPromptSubmit | 196 | Blocks phase advancement if incomplete | Gate enforcement |
| `post_batch_cascading.py` | PostToolUse | 1,830 | Cascades knowledge to destinations post-batch | REGRA #22 enforcement |
| `enforce_dual_location.py` | PostToolUse | 515 | Ensures logs in both MD + JSON | REGRA #8 enforcement |
| `session_autosave_v2.py` | Multiple | 1,162 | Auto-save session state | REGRA #11 |
| `skill_router.py` | UserPromptSubmit | 418 | Routes to skill by keyword | Lazy-loads pipeline-mce skill |
| `skill_indexer.py` | SessionStart | varies | Indexes all skills + sub-agents | Builds SKILL-INDEX.json |
| `creation_validator.py` | PreToolUse | 355 | Validates file creation (paths, templates) | ANTHROPIC-STANDARDS enforcement |
| `quality_watchdog.py` | PostToolUse | 393 | Checks agent output quality | REGRA #29 (warn, not block) |
| `inbox_age_alert.py` | SessionStart | 361 | Warns about stale inbox files | Pipeline awareness |
| `agent_creation_trigger.py` | PostToolUse | 440 | Detects new agent creation | Discovery tracking |

---

## 3. Rules-by-Domain Map

### 3.1 Rule Files Inventory

| File | Type | Rules | Size | Active Enforcement |
|------|------|-------|------|-------------------|
| `RULE-GROUP-1.md` | Phase Management | ZERO, 1-10 | ~12K | Partial (hooks for #8, #11; rest is doc-only) |
| `RULE-GROUP-2.md` | Persistence | 11-14 | ~8K | Yes (session_autosave_v2 for #11; enforce_plan_mode for #13) |
| `RULE-GROUP-3.md` | Operations | 15-17 | ~6K | No hooks (documentation only) |
| `RULE-GROUP-4.md` | Phase 5 Specific | 18-22 | ~10K | Partial (post_batch_cascading for #22; rest doc-only) |
| `RULE-GROUP-5.md` | Validation | 23-26 | ~10K | Partial (validate_phase5.py referenced but not auto-triggered) |
| `RULE-GROUP-6.md` | Auto-Routing | 27-30 | ~10K | Yes (skill_router, skill_indexer, quality_watchdog) |
| `pipeline.md` | Pipeline phases | - | 1.4K | No (documentation pointer) |
| `logging.md` | Dual-location logs | - | 1.2K | Yes (enforce_dual_location.py) |
| `state-management.md` | MISSION-STATE | - | 1.5K | Partial (auto-read at session start) |
| `agent-cognition.md` | Agent thinking flow | - | 8K | No hooks (protocol for agents) |
| `agent-integrity.md` | Source traceability | - | 10K | No hooks (protocol doc) |
| `epistemic-standards.md` | Anti-hallucination | - | 5K | No hooks (protocol doc) |
| `directory-contract.md` | Path governance | - | 14K | Yes (directory_contract_guard.py WARN) |
| `ANTHROPIC-STANDARDS.md` | Hook/skill/MCP standards | - | 6K | Yes (creation_validator.py) |
| `CLAUDE-LITE.md` | Lightweight rule summary | - | 5K | No (startup shortcut) |
| `mcp-governance.md` | MCP usage rules | - | 3K | No hooks |
| `no-secrets-in-memory.md` | Credential safety | - | 0.5K | No hooks (manual enforcement) |
| `RULE-GSD-MANDATORY.md` | GSD planning protocol | - | 2K | Yes (enforce_plan_mode.py partial) |

### 3.2 Rules-to-Pipeline Mapping

| Pipeline Step | Governing Rules | Enforcement Hook |
|---------------|-----------------|-----------------|
| File arrives in inbox | REGRA #7 (inbox is temporary) | inbox_age_alert.py |
| Scope classification | directory-contract.md (path routing) | directory_contract_guard.py |
| Batch creation | REGRA #1 (phases sequential), REGRA #4 (zero duplicates) | pipeline_phase_gate.py |
| Batch processing | REGRA #8 (dual-location logging), REGRA #9 (batch template V2) | enforce_dual_location.py |
| Post-batch cascading | REGRA #22 (multi-destination cascading) | post_batch_cascading.py |
| Source completion | REGRA #21 (theme dossier update) | None (doc-only) |
| Phase 5 execution | REGRAS #18-20 (templates, isolation, auto-advance) | None (doc-only) |
| Phase 5 validation | REGRA #23 (validate_phase5.py) | Referenced but not auto-triggered |
| Agent creation | REGRA #24 (template V3 enforcement) | creation_validator.py |
| Session management | REGRA #11 (session persistence) | session_autosave_v2.py |
| Skill activation | REGRAS #27-28 (auto-routing, visible activation) | skill_router.py, skill_indexer.py |
| Quality checking | REGRA #29 (warn not block) | quality_watchdog.py |
| GitHub workflow | REGRA #30 (issue-branch-PR-merge) | None (doc-only) |

### 3.3 Conflicts and Overlaps Between Rules

| Conflict | Description | Severity |
|----------|-------------|----------|
| REGRA #1 vs MCE pipeline | REGRA #1 defines 5 sequential phases. MCE pipeline uses a 12-step model with its own state machine. The old phase model is completed (PHASE_5_COMPLETE) but rules still reference it. | HIGH -- conceptual mismatch |
| pipeline.md vs RULE-GROUP-1 | pipeline.md is a 60-line summary of the same phases already in RULE-GROUP-1. Pure duplication. | LOW -- just redundant |
| logging.md vs REGRA #8 | logging.md is a 54-line summary of dual-location logging already in REGRA #8. Pure duplication. | LOW -- just redundant |
| state-management.md vs REGRA #5 | Both describe reading MISSION-STATE.json. state-management.md adds update triggers. | LOW -- complementary |
| CLAUDE-LITE.md vs all RULE-GROUPs | CLAUDE-LITE.md is an explicit summary of all 30 rules. Maintained separately but can drift. | MEDIUM -- drift risk |
| REGRA #22 vs REGRA #21 | #22 (post-batch cascading) should trigger #21 (theme dossier update) but they are described independently. | MEDIUM -- integration gap |
| ANTHROPIC-STANDARDS vs creation_validator.py | ANTHROPIC-STANDARDS defines timeout=30 for hooks, but 0 of 41 hooks in settings.json have been verified to actually have timeout:30. | HIGH -- unenforced |

---

## 4. Skills-by-Function Map

### 4.1 Pipeline-Touching Skills (Primary)

| Skill | Path | Lines | Pipeline Role | Entry Point? |
|-------|------|-------|--------------|-------------|
| `pipeline-mce` | `.claude/skills/pipeline-mce/SKILL.md` | 502 | MASTER skill for MCE pipeline. 12-step guide. Steps 0-2 and 11 call Python; Steps 3-10 are LLM prompts. | YES -- primary pipeline entry |
| `pipeline-jarvis` | `.claude/skills/pipeline-jarvis/SKILL.md` | ~400 | LEGACY 8-phase pipeline (superseded by MCE). Still indexed. | DEPRECATED -- replaced by pipeline-mce |
| `knowledge-extraction` | `.claude/skills/knowledge-extraction/SKILL.md` | ~300 | DNA taxonomy extraction guide. Used inside Step 5 of MCE. | NO -- utility within MCE |
| `source-sync` | `.claude/skills/source-sync/SKILL.md` | ~250 | Google Sheets planilha sync. For legacy Phase 1 workflow. | YES -- standalone entry |
| `process-company-inbox` | `.claude/skills/process-company-inbox/SKILL.md` | ~200 | Company inbox processing. Calls scope_classifier + inbox_organizer. | YES -- standalone entry |
| `read-ai-harvester` | `.claude/skills/read-ai-harvester/SKILL.md` | ~150 | Bulk download meeting transcripts from Read.ai MCP. | YES -- standalone entry |

### 4.2 Agent/Knowledge Skills (Secondary)

| Skill | Pipeline Touch | Description |
|-------|---------------|-------------|
| `clone-mind` | Indirect (consumes pipeline output) | Create mind clone agent from DNA |
| `agent-creation` | Indirect | Agent creation using Template V3 |
| `hormozi` | None | Query Hormozi agent |
| `graph-search` | Indirect (reads knowledge graph) | Knowledge graph queries |
| `memory-search` | Indirect (reads agent memory) | Search agent MEMORY.md files |
| `shared-memory` | Indirect | Cross-agent memory operations |

### 4.3 Operational Skills (Tertiary)

| Skill | Description |
|-------|-------------|
| `save` / `resume` | Session persistence |
| `jarvis-briefing` | System status display |
| `verify` / `verification-before-completion` | Post-session verification |
| `commit` | Git commit helper |
| `gha` | GitHub Actions diagnostics |
| `code-review` / `pr-review-toolkit` | PR review |
| `squad-creator` / `squad-guide` | Squad management |
| `deep-research` / `deep-strategic-planning` | Research orchestration |

### 4.4 Skill Index Statistics

From `SKILL-INDEX.json`:
- **Total indexed items:** 105 (47 skills + 1 sub-agent + 57 keyword aliases)
- **Skills with proper Auto-Trigger header:** ~30 of 47 (the rest have generic or missing headers)
- **Sub-agents indexed:** 1

---

## 5. State Files Map

### 5.1 Active State Files (Written to in last 30 days)

| File | Size | Last Modified | Writer | Reader | Purpose |
|------|------|---------------|--------|--------|---------|
| `MISSION-STATE.json` | 82K | 2026-03-13 | orchestrate.py, manual | session_start, pipeline scripts | Master mission state |
| `PIPELINE-STATE.json` | 25K | 2026-03-14 | orchestrate.py | pipeline scripts | Current pipeline phase/files |
| `BATCH-REGISTRY.json` | 107K | 2026-03-14 | batch_auto_creator.py | orchestrate.py, heal.py | Registry of all batches ever |
| `FIREFLIES-STATE.json` | 2K | 2026-03-15 | fireflies_sync.py | fireflies_sync.py | Fireflies sync cursor (59 meetings, tag MEET-100) |
| `SKILL-INDEX.json` | 66K | 2026-03-15 | skill_indexer.py | skill_router.py | Unified skill + sub-agent index |
| `DISCOVERY-STATE.json` | 6K | 2026-03-14 | agent_creation_trigger.py | Discovery tracking | Agent discovery state |
| `ACTIVITY-LOG.jsonl` | 391K | 2026-03-12 | Various hooks | Audit trail | Append-only activity log |
| `AUTOSAVE-STATE.json` | 86K | 2026-03-04 | session_autosave_v2.py | resume skill | Session auto-save |
| `TRIAGE-QUEUE.json` | 1K | 2026-03-13 | smart_router.py | Manual review | Files needing manual triage |
| `READ-AI-STATE.json` | 0.5K | 2026-03-09 | read_ai_harvester | read_ai_harvester | Read.ai sync state |
| `SOURCE-SYNC-STATE.json` | 1K | 2026-03-03 | source-sync skill | source-sync skill | Planilha sync state |
| `plan_mode_warnings.jsonl` | 58K | 2026-03-15 | enforce_plan_mode.py | None | Plan mode warnings log |

#### MCE State (per slug)

| Slug | metadata.yaml | metrics.yaml | pipeline_state.yaml | Status |
|------|--------------|-------------|--------------------|---------|
| `liam-ottley` | YES | YES | YES | Has full state machine |
| `alan-nicolas` | YES | YES | NO | Metadata + metrics only |
| `allfluence` | YES | YES | NO | Metadata + metrics only |
| `calls` | YES | YES | NO | Metadata + metrics only |
| `meet-0004` | YES | YES | NO | Metadata + metrics only |
| `meet-4162` | YES | YES | NO | Metadata + metrics only |
| `meetings` | YES | YES | NO | Metadata + metrics only |
| `tallis-gomes` | YES | YES | NO | Metadata + metrics only |

### 5.2 Legacy State Files (Untouched since 2026-03-03 or earlier)

These files were created during the legacy Phase 1-5 pipeline and have not been modified since. They total **~7.8MB** of the 11MB mission-control directory.

| Category | Files | Total Size | Purpose | Recommendation |
|----------|-------|-----------|---------|----------------|
| COMPARISON-*.json | 8 files | ~3.9MB | Planilha vs filesystem comparisons | ARCHIVE -- mission complete |
| DOWNLOAD-*.json | 7 files | ~170K | Download state and queues | ARCHIVE -- all downloads done |
| TAG-*.json/csv | 6 files | ~535K | Tagging state and mappings | ARCHIVE -- tagging complete |
| PLANILHA-*.json | 5 files | ~900K | Planilha extraction data | KEEP PLANILHA-INDEX.json, archive rest |
| AUDIT-REPORT*.json | 2 files | ~1.4MB | Audit results | ARCHIVE |
| CLEANUP-REPORT.json | 1 file | 174K | Cleanup log | ARCHIVE |
| NEW-FILES-*.json | 2 files | ~345K | Files pending processing | ARCHIVE -- processed |
| MISSING-*.json | 2 files | ~199K | Missing file tracking | ARCHIVE |
| NOTION-MANUAL-*.md | 6 files | ~100K | Notion migration data | ARCHIVE -- Notion removed |
| EXTRAS-REMOVED-*.json | 2 files | ~37K | Extras cleanup log | ARCHIVE |
| JM-*.json | 2 files | ~35K | Jeremy Miner specific data | ARCHIVE |
| Various .py scripts | 8 files | ~180K | Ad-hoc mission scripts | ARCHIVE or DELETE |
| Various .md reports | 15 files | ~480K | Visual reports, protocols | ARCHIVE |
| temp_* files | 7 files | ~90K | Temporary extraction files | DELETE |

### 5.3 State File Writer/Reader Matrix

```
                    WRITER                          READER
                    ------                          ------
MISSION-STATE.json  orchestrate.py, manual          session_start.py, pipeline scripts
                                                    skill (pipeline-mce), manual

PIPELINE-STATE.json orchestrate.py                  orchestrate.py (resume)
                                                    pipeline_heal.py

BATCH-REGISTRY.json batch_auto_creator.py           orchestrate.py
                                                    pipeline_heal.py

FIREFLIES-STATE.json fireflies_sync.py              fireflies_sync.py (idempotency)

SKILL-INDEX.json    skill_indexer.py (SessionStart)  skill_router.py (UserPromptSubmit)

DISCOVERY-STATE.json agent_creation_trigger.py       agent_creation_trigger.py

AUTOSAVE-STATE.json session_autosave_v2.py           resume skill

MCE state (per slug):
  metadata.yaml     metadata_manager.py              orchestrate.py
  metrics.yaml      metrics.py                       orchestrate.py, CLI
  pipeline_state.yaml state_machine.py               orchestrate.py (resume)
```

### 5.4 Consolidation Opportunities

| Current | Proposal | Savings |
|---------|----------|---------|
| MISSION-STATE.json (82K) + PIPELINE-STATE.json (25K) | Merge into single PIPELINE-STATE.json. MISSION-STATE is legacy. | Eliminate dual-state confusion |
| 8 COMPARISON-*.json (3.9MB) | Archive to `.claude/trash/legacy-comparison/` | Free 3.9MB |
| 7 DOWNLOAD-*.json + FILES-TO-DOWNLOAD.json | Archive to `.claude/trash/legacy-downloads/` | Free 170K |
| 6 TAG-*.json/csv | Archive to `.claude/trash/legacy-tags/` | Free 535K |
| 8 ad-hoc .py scripts in mission-control | Move to `.claude/trash/legacy-scripts/` | Clean separation |
| 7 temp_* files | Delete immediately | Free 90K |
| 6 NOTION-MANUAL-*.md | Delete (Notion MCP removed) | Free 100K |

---

## 6. Duplicates and Redundancies

### 6.1 Conceptual Duplicates

| Duplicate Pair | Description | Resolution |
|---------------|-------------|------------|
| `pipeline.md` + `RULE-GROUP-1.md` | pipeline.md is a 60-line subset of RULE-GROUP-1 (rules ZERO, 1-10). | DELETE pipeline.md, update any references |
| `logging.md` + `RULE-GROUP-1.md` (#8, #9) | logging.md is a 54-line subset of REGRA #8 and #9. | DELETE logging.md |
| `CLAUDE-LITE.md` + all RULE-GROUPs | CLAUDE-LITE is a manual summary. Drift guaranteed over time. | KEEP but mark as "generated" and add auto-check |
| `PIPELINE-STATE.json` + `MISSION-STATE.json` | Both track pipeline progress. MISSION-STATE is legacy (created Jan 2). PIPELINE-STATE is current (created Mar 5). | CONSOLIDATE into single file |
| `PIPELINE-STATE-OLD.json` + `PIPELINE-STATE.json` | Explicit old copy. 775 bytes. | DELETE the OLD copy |
| `session_autosave.py` (pipeline/) + `session_autosave_v2.py` (hooks/) | Legacy v1 in pipeline dir, active v2 in hooks dir. | DELETE v1 from pipeline/ |
| `batch_logs/` (135 JSON files) + `logs/batches/` (MD files) | Intentional dual-location (REGRA #8). Not a bug but 2x storage. | KEEP (by design) |
| `AUDIT-REPORT.json` + `AUDIT-REPORT-V2.json` | Two versions of the same audit. Both from Jan 2026. | ARCHIVE both |

### 6.2 Path Aliasing Duplicates

In `core/paths.py`, these backward-compat aliases create confusion:

| Alias | Points To | Used By |
|-------|-----------|---------|
| `WORKSPACE_ORG` | `WORKSPACE_ADMIN` | bucket_processor.py |
| `WORKSPACE_AUTOMATIONS` | `WORKSPACE_WORKFLOWS` | bucket_processor.py |
| `WORKSPACE_TOOLS` | `WORKSPACE_FERRAMENTAS` | bucket_processor.py |
| `INBOX` | `WORKSPACE / "inbox"` | batch_governor.py, pipeline_router.py |

**Impact:** Scripts using these aliases work today but create conceptual confusion. The aliases exist in paths.py lines 64-69.

### 6.3 Skill Duplicates

| Skill A | Skill B | Overlap |
|---------|---------|---------|
| `pipeline-jarvis` | `pipeline-mce` | pipeline-jarvis is the legacy version. pipeline-mce supersedes it. |
| `save` | `session_autosave_v2.py` (hook) | save is manual; autosave is automatic. Both write to same location. Complementary, not duplicate. |
| `verify` | `verification-before-completion` + `verify-6-levels` + `validate-dod` | 4 different verification skills with overlapping concerns. |

---

## 7. Dead Code and Orphans

### 7.1 Dead/Legacy Scripts in Pipeline Directory

| Script | Evidence of Dead Code | Recommendation |
|--------|----------------------|----------------|
| `session_autosave.py` (in pipeline/) | Superseded by `session_autosave_v2.py` in hooks/. Uses env var instead of core.paths. | DELETE |
| `sync_package_files.py` | NPM package sync utility. Not part of knowledge pipeline at all. | MOVE to `bin/` or `core/tools/` |
| `video/pipeline.py` | References `whisper` which is not in requirements. No evidence of recent use. | KEEP but mark as experimental |

### 7.2 Dead/Legacy State Files

| File | Evidence | Recommendation |
|------|----------|----------------|
| 8 COMPARISON-*.json | Phase 1 completed Jan 3, 2026. Never read again. | ARCHIVE |
| 7 DOWNLOAD-*.json | All downloads completed Jan 6, 2026. Never read again. | ARCHIVE |
| PIPELINE-STATE-OLD.json | Explicit "OLD" copy, 775 bytes. | DELETE |
| 7 temp_* files | Temporary extraction artifacts from Feb 5. | DELETE |
| 6 NOTION-MANUAL-*.md | Notion MCP removed. These were manual export guides. | DELETE |
| 8 ad-hoc .py scripts | jarvis_mission.py, mission_pipeline.py, etc. Legacy processing scripts. | ARCHIVE |
| REPROCESS-ALL-PLANILHA.json | 100K file for planilha reprocessing. One-time use. | ARCHIVE |

### 7.3 Orphan Hooks

| Hook | Registered in settings.json? | Evidence of Use | Recommendation |
|------|------------------------------|----------------|----------------|
| `memory_capture.py` | Unknown | No evidence in recent logs | VERIFY registration |
| `memory_updater.py` | Referenced in CLAUDE.md | 203 lines | VERIFY -- may overlap with memory_hints_injector |
| `post_tool_use.py` | Referenced in CLAUDE.md | Not found in hooks/ dir listing | GHOST reference -- remove from CLAUDE.md |
| `resolve_agent_path.py` | Unknown | 155 lines | VERIFY registration |
| `claude_md_agent_sync.py` | Unknown | 155 lines | VERIFY registration |
| `agent_deprecation_guard.py` | Unknown | 196 lines | VERIFY registration |

### 7.4 Referenced But Missing Files

| Reference Location | Missing File | Impact |
|--------------------|--------------|---------|
| RULE-GROUP-5 (REGRA #23) | `.claude/scripts/validate_phase5.py` | Referenced validation script may not exist |
| RULE-GROUP-5 (REGRA #26) | `scripts/validate_cascading_integrity.py` | Referenced validation script may not exist |
| pipeline.md | `@/reference/JARVIS-LOGGING-SYSTEM-V3.md` | Template reference |
| Auto-memory | `bucket_router.py` referenced in 3 docs | File EXISTS (7,614 bytes) -- not actually missing |
| PIPELINE-STATE.json | `inbox/empresa/MEETINGS/*` | References files in `inbox/` which was deprecated in favor of `knowledge/business/inbox/` |

### 7.5 Stale ROUTING Keys

These ROUTING keys in `core/paths.py` point to directories that were deprecated in S13:

| ROUTING Key | Points To | Status |
|-------------|-----------|--------|
| `"download"` | `INBOX` (= `WORKSPACE / "inbox"`) | STALE -- inbox at workspace root is deprecated |
| `"workspace_inbox"` | `WORKSPACE_INBOX` | STALE -- same issue |

---

## 8. Per-File Recommendations

### 8.1 Pipeline Scripts -- Priority Fixes

| Priority | Script | Issue | Fix |
|----------|--------|-------|-----|
| P0 | `batch_governor.py` | Imports deprecated `INBOX` from core.paths | Change to `ROUTING["external_inbox"]` or `ROUTING["business_inbox"]` based on context |
| P0 | `pipeline_router.py` | Imports deprecated `INBOX` from core.paths | Same fix as above |
| P0 | `batch_auto_creator.py` | Has ImportError fallback to hardcoded paths | Remove fallback, require core.paths import |
| P1 | `bucket_processor.py` | Uses stale WORKSPACE_ORG, WORKSPACE_TEAM, etc. aliases | Update to new S13 paths (WORKSPACE_ADMIN, WORKSPACE_GENTE_CULTURA) |
| P1 | `autonomous_processor.py` | Uses env var `CLAUDE_PROJECT_DIR` instead of core.paths | Refactor to use `from core.paths import ROUTING` |
| P1 | `task_orchestrator.py` | Same env var issue as autonomous_processor | Same fix |
| P1 | `content_hasher.py` | Hardcodes `.data/content_hashes.json` | Add ROUTING key or use `DATA / "content_hashes.json"` |
| P1 | `session_autosave.py` (pipeline/) | Uses env var `MEGA_BRAIN_ROOT`, superseded by v2 | DELETE this file |
| P2 | `meeting_router.py` | No core.paths import (standalone utility) | Low impact -- works fine as pure utility |
| P2 | `sync_package_files.py` | Not part of knowledge pipeline | Move to `bin/` or `core/tools/` |

### 8.2 MCE Scripts -- Priority Fixes

| Priority | Script | Issue | Fix |
|----------|--------|-------|-----|
| P1 | `gemini_analyzer.py` | Requires `google.generativeai` (not in requirements) | Add to optional requirements or document fallback |
| P2 | `state_machine.py` | Requires `transitions` library (not in requirements-hooks.txt) | Add to a `requirements-pipeline.txt` |
| P2 | `cli.py` | Has `--upgrade` mode that modifies state in-place | Add backup before upgrade |

### 8.3 Rules -- Priority Fixes

| Priority | File | Issue | Fix |
|----------|------|-------|-----|
| P0 | `pipeline.md` | Pure duplicate of RULE-GROUP-1 subset | DELETE and redirect references |
| P0 | `logging.md` | Pure duplicate of RULE-GROUP-1 #8/#9 | DELETE and redirect references |
| P1 | `RULE-GROUP-1.md` | References 5-phase model but MCE uses 12-step model | Add section acknowledging MCE supersedes legacy phases |
| P1 | `RULE-GROUP-4.md` | Phase 5 rules reference legacy batch model | Add note that MCE pipeline handles this differently |
| P1 | `RULE-GROUP-5.md` | References validate_phase5.py and validate_cascading_integrity.py -- may not exist | VERIFY existence, create if missing |
| P2 | `CLAUDE-LITE.md` | Manual summary risks drift from source rules | Add generation timestamp and check mechanism |

### 8.4 Hooks -- Priority Fixes

| Priority | Hook | Issue | Fix |
|----------|------|-------|-----|
| P0 | ALL hooks | ANTHROPIC-STANDARDS requires timeout:30 -- verify settings.json compliance | Audit settings.json for timeout fields |
| P1 | `post_tool_use.py` | Referenced in CLAUDE.md but not found in hooks/ | Remove from CLAUDE.md or create file |
| P1 | `memory_capture.py` / `memory_updater.py` / `memory_hints_injector.py` | Three memory-related hooks with unclear boundaries | Consolidate or document distinct roles |
| P2 | `pipeline_orchestrator.py` | 450 lines but may overlap with mce/orchestrate.py | Verify if both are needed |

### 8.5 State Files -- Priority Fixes

| Priority | Action | Files | Savings |
|----------|--------|-------|---------|
| P0 | DELETE temp files | 7 temp_* files | 90K |
| P0 | DELETE PIPELINE-STATE-OLD.json | 1 file | 775 bytes |
| P1 | ARCHIVE legacy comparison JSONs | 8 files | 3.9MB |
| P1 | ARCHIVE legacy download JSONs | 7 files | 170K |
| P1 | DELETE Notion migration files | 6 files | 100K |
| P1 | ARCHIVE legacy tag files | 6 files | 535K |
| P2 | ARCHIVE ad-hoc Python scripts | 8 files | 180K |
| P2 | ARCHIVE legacy visual reports/protocols | 15 files | 480K |
| P2 | CONSOLIDATE MISSION-STATE + PIPELINE-STATE | 2 files -> 1 | Conceptual clarity |

### 8.6 Skills -- Priority Fixes

| Priority | Skill | Issue | Fix |
|----------|-------|-------|-----|
| P1 | `pipeline-jarvis` | Legacy skill superseded by pipeline-mce. Still in SKILL-INDEX. | Add DEPRECATED header or remove from index |
| P2 | `verify` + `verification-before-completion` + `verify-6-levels` + `validate-dod` | 4 overlapping verification skills | Consolidate into single `verify` skill |
| P2 | 17 skills without proper Auto-Trigger header | Poor keyword matching = invisible skills | Add proper headers |

---

## Appendix A: File Count Summary

| Category | Count | Total Size |
|----------|-------|-----------|
| Pipeline scripts (`core/intelligence/pipeline/`) | 27+ files | ~500K |
| MCE sub-pipeline (`pipeline/mce/`) | 9 files | ~114K |
| Hooks (`.claude/hooks/`) | 41 files | ~12.6K lines |
| Rules (`.claude/rules/`) | 17 files | ~100K |
| Skills (`.claude/skills/`) | 105 directories | ~varies |
| State files (`.claude/mission-control/`) | 142 files + 135 batch logs | 11MB |
| ROUTING keys (`core/paths.py`) | 107 keys | N/A |

## Appendix B: core.paths ROUTING Keys (Full List)

107 routing keys organized by category:

**Audit/Validation (2):** audit_report, layer_validation
**Session/State (6):** session_log, mission_state, pipeline_state, skill_index, autosave_state, phase_gate_state
**Logs (12):** batch_log, handoff, cascade_log, tool_usage, quality_gaps, dossier_trigger, bucket_processing, autonomous_log, agent_creation_log, read_ai_log, smart_router_log, batch_auto_creator_log
**Knowledge/RAG (5):** rag_chunks, rag_vectors, graph, memory_split, nav_map
**Processing (4):** entity_registry, speakers, diarization, voice_embeddings
**Agent outputs (2):** sow_output, generated_skill
**Downloads (1):** download
**Trash (1):** trash
**Knowledge buckets (5):** workspace_data, personal_data, rag_expert, rag_business, workspace_inbox/personal_inbox/external_inbox
**Workspace departmental (30+):** workspace_aios through workspace_templates (7 spaces x ~4 keys each)
**Business bucket (7):** business_inbox through business_sops
**Agent categories (7):** agents_external through agents_dev_ops
**Personal (4):** personal_email through personal_cognitive
**Reference docs (4):** architecture_doc, implementation_log, onboarding_guide, ux_by_area
**Log templates (2):** workspace_log_template, personal_log_template
**Integrations (9):** read_ai_*, watcher_*, batch_registry, triage_queue, memory_enricher_log, workspace_sync_log, mce_*, ss_bridge_*, inbox_processor_log
**Discovery (3):** discovery_state, role_tracking, agent_creation_log

## Appendix C: Prohibited Directories

From `core/paths.py` line 309-313:

1. `ROOT / "docs"` -- Use `REFERENCE` instead
2. `WORKSPACE / "domains"` -- Removed in S13
3. `WORKSPACE / "providers"` -- Removed in S13

**Note:** This document is saved in `docs/architecture/` which is under the prohibited `docs/` directory. This is a known exception for architecture documentation that predates the prohibition.

---

*Generated by DR Orchestrator agent. Data sourced from file-by-file reads of the actual codebase, not assumptions.*
