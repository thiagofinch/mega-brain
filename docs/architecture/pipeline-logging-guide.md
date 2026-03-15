# MCE Pipeline & Logging Architecture

> **Auto-generated:** No. Manual reference document.
> **Last Updated:** 2026-03-15
> **Maintainer:** System Architecture
> **Scope:** Complete pipeline flow, log triggers, output locations, audit trail

---

## Pipeline Overview

The MCE (Mental Cognitive Extraction) Pipeline transforms raw expert content into
structured DNA schemas, behavioral profiles, and mind-clone agents. It combines
deterministic Python modules for file operations with LLM prompts for extraction.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCE PIPELINE — 12 STEPS                              │
│                                                                         │
│  INPUT                                                                  │
│    ↓                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │ 0. DETECT   │→ │ 1. INGEST   │→ │ 2. BATCH    │  ← DETERMINISTIC    │
│  │   (init)    │  │   (Atlas)   │  │   (Atlas)   │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                          ↓                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │ 3. CHUNK    │→ │ 4. ENTITY   │→ │ 5. INSIGHT  │  ← LLM             │
│  │   (Sage)    │  │   (Sage)    │  │   (Sage)    │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                          ↓                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │ 6. BEHAV    │→ │ 7. IDENTITY │→ │ 8. VOICE    │  ← LLM (MCE)       │
│  │   (Sage)    │  │   (Sage)    │  │   (Sage)    │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                          ↓                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │ 9. CHECK    │→ │10. COMPILE  │→ │11. FINALIZE │  ← HUMAN + DET.    │
│  │   (Lens)    │  │   (Forge)   │  │   (Echo)    │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                          ↓                              │
│                                    ┌─────────────┐                      │
│                                    │12. REPORT   │  ← OUTPUT            │
│                                    │   (Lens)    │                      │
│                                    └─────────────┘                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: What Happens, What Logs, Where

### Step 0: DETECT INPUT

| Field | Value |
|-------|-------|
| Type | Deterministic |
| Squad Agent | — |
| Script | `core/intelligence/pipeline/mce/orchestrate.py` |
| Action | Detect file path or slug, check for resumable state |
| Log written | `logs/mce-orchestrate.jsonl` |
| State written | `.claude/mission-control/mce/{SLUG}/pipeline_state.yaml` |

**Log trigger:** Every `orchestrate.py` command logs a JSON line to `mce-orchestrate.jsonl`.

---

### Step 1: INGEST

| Field | Value |
|-------|-------|
| Type | Deterministic |
| Squad Agent | Atlas (The Classifier) |
| Scripts | `scope_classifier.py`, `smart_router.py`, `inbox_organizer.py` |
| Action | Classify file (6 signals), route to bucket, organize inbox |
| Logs written | `logs/scope-classifier.jsonl`, `logs/smart-router.jsonl`, `logs/mce-orchestrate.jsonl` |
| State written | `.claude/mission-control/mce/{SLUG}/metadata.yaml` |

**Log trigger:** `scope_classifier.py` logs classification result (bucket, confidence, signals). `smart_router.py` logs routing decision (moved_to, references_created).

**6 Classification Signals:**

| # | Signal | What it checks |
|---|--------|----------------|
| S1 | Path pattern | Directory structure implies bucket |
| S2 | Participant names | Known people → external or business |
| S3 | Content keywords | Expert markers, company terms |
| S4 | File metadata | Source type (course, call, doc) |
| S5 | Entity match | CANONICAL-MAP lookup |
| S6 | Historical pattern | Previous classifications for this entity |

---

### Step 2: BATCH

| Field | Value |
|-------|-------|
| Type | Deterministic |
| Squad Agent | Atlas |
| Script | `batch_auto_creator.py` |
| Action | Scan organized inbox, create batches (min 3 files) |
| Log written | `logs/batch-auto-creator.jsonl` |
| State written | `.claude/mission-control/BATCH-REGISTRY.json` |

**Log trigger:** Each batch creation logs batch_id, file_count, slug, timestamp.

---

### Step 3: CHUNK (First LLM Step)

| Field | Value |
|-------|-------|
| Type | LLM |
| Squad Agent | Sage (The Extractor) |
| Prompt | `core/templates/phases/prompt-1.1-chunking.md` |
| Action | Semantic chunking (~300 words each), source metadata preservation |
| Artifact written | `artifacts/chunks/CHUNKS-STATE.json` |
| Log written | `logs/mce-orchestrate.jsonl` (step completion) |
| State transition | `init` → `chunking` |

**Validation checkpoint:**
- `CP-POST-2.A`: count(new_chunks) > 0
- `CP-POST-2.B`: Each chunk has unique id_chunk
- `CP-POST-2.C`: CHUNKS-STATE.json saved successfully

---

### Step 4: ENTITY RESOLUTION

| Field | Value |
|-------|-------|
| Type | LLM |
| Squad Agent | Sage |
| Prompt | `core/templates/phases/prompt-1.2-entity-resolution.md` |
| Action | Resolve name variants to canonical forms, MERGE with existing map |
| Artifact written | `artifacts/canonical/CANONICAL-MAP.json` (PERSISTENT, append-only) |
| State transition | `chunking` → `entities` |

**Critical rule:** CANONICAL-MAP.json is PERSISTENT across all pipeline runs. Always READ existing, then MERGE. Never overwrite.

---

### Step 5: INSIGHT EXTRACTION

| Field | Value |
|-------|-------|
| Type | LLM |
| Squad Agent | Sage |
| Prompts | `prompt-2.1-insight-extraction.md` + `prompt-2.1-dna-tags.md` |
| Action | Extract actionable insights, apply DNA layer tags |
| Artifact written | `artifacts/insights/INSIGHTS-STATE.json` (PERSISTENT, single incremental file) |
| State transition | `entities` → `knowledge_extraction` |

**DNA Tags Applied:**

| Tag | Layer | Identifies |
|-----|-------|------------|
| `[FILOSOFIA]` | L1 | Core beliefs, principles |
| `[MODELO-MENTAL]` | L2 | Thinking frameworks, mental lenses |
| `[HEURISTICA]` | L3 | Practical rules with thresholds |
| `[FRAMEWORK]` | L4 | Named structures with components |
| `[METODOLOGIA]` | L5 | Step-by-step processes |

**Critical rule:** INSIGHTS-STATE.json is a SINGLE file that grows across all runs. Never create per-meeting variants.

---

### Step 6: MCE BEHAVIORAL

| Field | Value |
|-------|-------|
| Type | LLM |
| Squad Agent | Sage |
| Prompt | `core/templates/phases/prompt-mce-behavioral.md` |
| Action | Extract behavioral patterns (decision, reaction, habit, communication) |
| Artifact written | INSIGHTS-STATE.json updated with `behavioral_patterns` field |
| State transition | `knowledge_extraction` → `mce_extraction` |

**Validation:** Each pattern must have 2+ chunk_ids as evidence.

---

### Step 7: MCE IDENTITY

| Field | Value |
|-------|-------|
| Type | LLM |
| Squad Agent | Sage |
| Prompt | `core/templates/phases/prompt-mce-identity.md` |
| Action | Extract value hierarchy, obsessions, paradoxes |
| Artifact written | INSIGHTS-STATE.json updated with `value_hierarchy`, `obsessions`, `paradoxes` |
| State transition | Continues `mce_extraction` |

**Validation:** Exactly 1 MASTER obsession. At least 1 Tier 1 value.

---

### Step 8: MCE VOICE

| Field | Value |
|-------|-------|
| Type | LLM |
| Squad Agent | Sage |
| Prompt | `core/templates/phases/prompt-mce-voice.md` |
| Action | Extract voice DNA (tone profile, signature phrases, behavioral states) |
| Artifact written | `knowledge/external/dna/persons/{SLUG}/VOICE-DNA.yaml` |
| State transition | `mce_extraction` → `identity_checkpoint` |

**6 Tone Dimensions:** Certainty, Authority, Warmth, Directness, Humor, Formality (0-10 scale)

---

### Step 9: IDENTITY CHECKPOINT (Human Pause)

| Field | Value |
|-------|-------|
| Type | Human Review |
| Squad Agent | Lens (The Validator) |
| Action | Present extracted identity for approval |
| Options | [1] APPROVE → continue, [2] REVISE → re-run Step 7, [3] ABORT → save and exit |
| State transition | `identity_checkpoint` → `consolidation` (on APPROVE) |

**This is the ONLY step where the pipeline pauses for human input.**

---

### Step 10: CONSOLIDATION

| Field | Value |
|-------|-------|
| Type | LLM (4 sub-phases) |
| Squad Agent | Forge (The Compiler) + Echo (The Cloner) |
| Prompts | `dossier-compilation.md`, `sources-compilation.md`, agent Template V3 |
| Action | Generate dossier, source docs, 5 DNA YAMLs, 4 agent files |
| State transition | `consolidation` → `agent_generation` |

**Files generated per person (10-15 total):**

| # | Artifact | Path |
|---|----------|------|
| 1 | Dossier | `knowledge/external/dossiers/persons/DOSSIER-{PERSON}.md` |
| 2 | Source themes | `knowledge/external/sources/{slug}/{theme}.md` |
| 3 | FILOSOFIAS.yaml | `knowledge/external/dna/persons/{SLUG}/` |
| 4 | MODELOS-MENTAIS.yaml | `knowledge/external/dna/persons/{SLUG}/` |
| 5 | HEURISTICAS.yaml | `knowledge/external/dna/persons/{SLUG}/` |
| 6 | FRAMEWORKS.yaml | `knowledge/external/dna/persons/{SLUG}/` |
| 7 | METODOLOGIAS.yaml | `knowledge/external/dna/persons/{SLUG}/` |
| 8 | VOICE-DNA.yaml | `knowledge/external/dna/persons/{SLUG}/` |
| 9 | AGENT.md | `agents/external/{SLUG}/` |
| 10 | SOUL.md | `agents/external/{SLUG}/` |
| 11 | MEMORY.md | `agents/external/{SLUG}/` |
| 12 | DNA-CONFIG.yaml | `agents/external/{SLUG}/` |

---

### Step 11: FINALIZE

| Field | Value |
|-------|-------|
| Type | Deterministic |
| Squad Agent | Echo |
| Script | `orchestrate.py finalize` |
| Action | Memory enrichment, workspace sync, metrics finalization |
| Logs written | `logs/memory-enricher.jsonl`, `logs/workspace-sync.jsonl`, `logs/mce-metrics.jsonl` |
| State transition | `agent_generation` → `validation` |

---

### Step 12: REPORT

| Field | Value |
|-------|-------|
| Type | Output |
| Squad Agent | Lens |
| Action | Display completion metrics, run 10-point validation |
| Log written | `logs/mce/{SLUG}/MCE-{TAG}.md` (human-readable) |
| State written | `.claude/mission-control/mce/{SLUG}/pipeline_state.yaml` (final) |
| State transition | `validation` → `complete` |

---

## Logging Architecture

### Dual-Location Strategy

Every pipeline action generates logs in TWO locations:

```
                    ┌─────────────────────────────────────────┐
                    │           PIPELINE ACTION               │
                    └──────────────┬──────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                              │
              ┌─────┴─────┐                  ┌─────┴─────┐
              │ HUMAN LOG │                  │MACHINE LOG│
              │   (.md)   │                  │ (.jsonl)  │
              └─────┬─────┘                  └─────┬─────┘
                    │                              │
         logs/mce/{SLUG}/              logs/*.jsonl +
         MCE-{TAG}.md                  .claude/mission-control/
                                       mce/{SLUG}/*.yaml
```

**Rule:** If it was not logged, it was not processed.

### 13 JSONL Log Files

| # | Log File | Writer | What it records |
|---|----------|--------|-----------------|
| 1 | `logs/mce-orchestrate.jsonl` | `orchestrate.py` | Every MCE command (ingest, batch, finalize, status) |
| 2 | `logs/mce-metrics.jsonl` | `metrics.py` | Wall-clock timing per phase |
| 3 | `logs/scope-classifier.jsonl` | `scope_classifier.py` | 6-signal classification results |
| 4 | `logs/smart-router.jsonl` | `smart_router.py` | File routing decisions |
| 5 | `logs/batch-auto-creator.jsonl` | `batch_auto_creator.py` | Batch creation events |
| 6 | `logs/memory-enricher.jsonl` | `memory_enricher.py` | Insight → MEMORY.md routing |
| 7 | `logs/workspace-sync.jsonl` | `workspace_sync.py` | Business knowledge → workspace sync |
| 8 | `logs/agent-creation.jsonl` | `agent_creation_trigger.py` | Agent MCE threshold triggers |
| 9 | `logs/agent-index-updates.jsonl` | `agent_index_updater.py` | AGENT-INDEX.yaml changes |
| 10 | `logs/pipeline-checkpoints.jsonl` | `pipeline_checkpoint.py` | Pipeline state snapshots |
| 11 | `logs/pipeline-guard.jsonl` | `pipeline_guard.py` | Output path validation |
| 12 | `logs/claude-md-sync.jsonl` | `claude_md_agent_sync.py` | CLAUDE.md auto-updates |
| 13 | `logs/prompts.jsonl` | PostToolUse hooks | Prompt execution tracking |

### 3 State Files (per SLUG)

| File | Location | Content |
|------|----------|---------|
| `pipeline_state.yaml` | `.claude/mission-control/mce/{SLUG}/` | FSM state + transition history |
| `metadata.yaml` | `.claude/mission-control/mce/{SLUG}/` | Phase progress, sources processed |
| `metrics.yaml` | `.claude/mission-control/mce/{SLUG}/` | Wall-clock timing per phase |

### 3 Persistent Artifacts

| File | Location | Persistence Rule |
|------|----------|------------------|
| `CHUNKS-STATE.json` | `artifacts/chunks/` | Append new chunks, dedup by id |
| `CANONICAL-MAP.json` | `artifacts/canonical/` | MERGE new entities, never overwrite |
| `INSIGHTS-STATE.json` | `artifacts/insights/` | Single file, grows across all runs |

---

## Hook-Triggered Logging

These PostToolUse hooks fire AFTER pipeline steps complete and generate additional logs:

| Hook | Trigger | Log Created | Purpose |
|------|---------|-------------|---------|
| `pipeline_checkpoint.py` | Any tool use | `logs/pipeline-checkpoints.jsonl` | Snapshot current pipeline state |
| `pipeline_guard.py` | Any tool use | `logs/pipeline-guard.jsonl` | Validate output path against ROUTING |
| `pipeline_phase_gate.py` | Any tool use | (inline) | Verify phase complete before advance |
| `pipeline_orchestrator.py` | Any tool use | (inline) | Auto-advance pipeline to next phase |
| `agent_creation_trigger.py` | Any tool use | `logs/agent-creation.jsonl` | Check MCE threshold (3+ insights) |
| `post_batch_cascading.py` | Any tool use | (inline) | Cascade knowledge to dossiers/agents |
| `governance_auto_update.py` | Write/Edit | (regenerates docs) | Sync constitution when rules change |

---

## Human-Readable Log Template

The MCE Pipeline Log Template (`core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md`)
is a 423-line progressive template with 12 sections matching the 12 pipeline steps.

**Progressive fill:** Sections show `[*] PENDENTE` until their step executes,
then fill with real data and change to `[@] COMPLETO`.

**Output path:** `logs/mce/{SLUG}/MCE-{TAG}.md`

**Status markers:**

| Marker | Meaning |
|--------|---------|
| `[*] PENDENTE` | Step not yet executed |
| `[~] EM ANDAMENTO` | Step currently running |
| `[@] COMPLETO` | Step finished with data |

**Progress bar:**
```
Classification   [@@@@@@@@@@@] 100%
Organization     [@@@@@@@@@@@] 100%
Chunking         [~~~~~~~~~~~]  IN PROGRESS
Entity Res.      [-----------]  PENDENTE
...
```

---

## State Machine

```
init ─→ chunking ─→ entities ─→ knowledge_extraction ─→ mce_extraction
                                                              │
                                                    identity_checkpoint
                                                        │       │
                                                    (APPROVE) (REVISE → loop)
                                                        │
                                                   consolidation ─→ agent_generation
                                                                         │
                                                                    validation ─→ complete
```

**Resume:** Run `/pipeline-mce {SLUG}` — picks up from first incomplete step automatically.

**Persistence:** `.claude/mission-control/mce/{SLUG}/pipeline_state.yaml`

---

## Knowledge Ops Squad Mapping

| Squad Agent | Role | Steps | What they "own" |
|-------------|------|-------|-----------------|
| **Atlas** | The Classifier | 0-2 | Input detection, classification, routing |
| **Sage** | The Extractor | 3-8 | Chunking, entities, insights, MCE layers |
| **Lens** | The Validator | 9, 12 | Identity checkpoint, final validation |
| **Forge** | The Compiler | 10 | Dossiers, DNA YAMLs, source docs |
| **Echo** | The Cloner | 10.4, 11 | Agent generation, memory enrichment |

**Location:** `agents/system/knowledge-ops/kops-{name}.md`

---

## Quick Reference: All Output Paths

### By core/paths.py ROUTING keys

| Key | Path | Used by |
|-----|------|---------|
| `mce_state` | `.claude/mission-control/mce/` | State machine, metadata, metrics |
| `mce_metrics_log` | `logs/mce-metrics.jsonl` | Performance tracking |
| `mce_cache` | `.data/mce_cache/` | Two-level analysis cache |
| `batch_registry` | `.claude/mission-control/BATCH-REGISTRY.json` | Batch tracking |
| `smart_router_log` | `logs/smart-router.jsonl` | Routing decisions |
| `memory_enricher_log` | `logs/memory-enricher.jsonl` | Insight → MEMORY.md |
| `workspace_sync_log` | `logs/workspace-sync.jsonl` | Business → workspace |
| `agent_creation_log` | `logs/agent-creation.jsonl` | MCE threshold triggers |

---

*Manual reference document. Not auto-generated.*
*See also: `docs/architecture/constitution.md` (auto-generated system overview)*
