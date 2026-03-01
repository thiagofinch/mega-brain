# BROWNFIELD DETECTION PROTOCOL

> **Versão:** 1.0.0
> **Padrão:** Pedro (aios-core/squad-creator)
> **Workflow:** wf-brownfield-update.yaml
> **Propósito:** Define how the system detects, classifies, and manages brownfield update scenarios

---

## Overview

The Brownfield Detection Protocol determines whether new source materials should trigger
a full greenfield pipeline (wf-pipeline-full) or an incremental brownfield update
(wf-brownfield-update). This saves 60-75% of processing time and tokens by avoiding
redundant extraction of already-captured knowledge.

---

## 1. Detection Criteria

### 1.1 Brownfield Trigger Conditions

A brownfield scenario is confirmed when ALL of the following are true:

| # | Condition | Check |
|---|-----------|-------|
| 1 | Clone exists | `agents/persons/{source}/` directory exists |
| 2 | DNA is complete | `agents/persons/{source}/DNA-CONFIG.yaml` exists and is valid YAML |
| 3 | Pipeline completed | `metadata.yaml` contains `pipeline_status: completed` |
| 4 | All 5 layers present | DNA-CONFIG.yaml has non-empty L1 through L5 |

If ANY condition fails, the system falls back to `wf-pipeline-full` (greenfield).

### 1.2 Detection Decision Tree

```
NEW SOURCE MATERIAL ARRIVES
         │
         ▼
    ┌────────────────────────────┐
    │ Does agents/persons/{src}/ │
    │ directory exist?           │
    └────────────┬───────────────┘
                 │
         ┌───────┴───────┐
         │ NO            │ YES
         ▼               ▼
    GREENFIELD      ┌────────────────────────────┐
    (wf-pipeline-   │ Does DNA-CONFIG.yaml exist │
     full)          │ and contain all 5 layers?  │
                    └────────────┬───────────────┘
                                 │
                         ┌───────┴───────┐
                         │ NO            │ YES
                         ▼               ▼
                    GREENFIELD      ┌────────────────────────────┐
                                    │ metadata.yaml has          │
                                    │ pipeline_status: completed?│
                                    └────────────┬───────────────┘
                                                 │
                                         ┌───────┴───────┐
                                         │ NO            │ YES
                                         ▼               ▼
                                    GREENFIELD      BROWNFIELD
                                                    (wf-brownfield-
                                                     update)
```

---

## 2. Pre-Update Snapshot

Before ANY modification occurs in brownfield mode, the system MUST create a
complete snapshot for rollback capability.

### 2.1 Snapshot Contents

| Artifact | Source Location | Snapshot Location |
|----------|----------------|-------------------|
| DNA-CONFIG.yaml | `agents/persons/{src}/DNA-CONFIG.yaml` | `artifacts/brownfield/snapshots/{src}/DNA-CONFIG.yaml` |
| SOUL.md | `agents/persons/{src}/SOUL.md` | `artifacts/brownfield/snapshots/{src}/SOUL.md` |
| MEMORY.md | `agents/persons/{src}/MEMORY.md` | `artifacts/brownfield/snapshots/{src}/MEMORY.md` |
| AGENT.md | `agents/persons/{src}/AGENT.md` | `artifacts/brownfield/snapshots/{src}/AGENT.md` |
| metadata.yaml | `agents/persons/{src}/metadata.yaml` | `artifacts/brownfield/snapshots/{src}/metadata.yaml` |

### 2.2 Snapshot Naming

```
artifacts/brownfield/snapshots/{source_code}/
├── SNAPSHOT-MANIFEST.json      # Timestamp, file hashes, previous version
├── DNA-CONFIG.yaml
├── SOUL.md
├── MEMORY.md
├── AGENT.md
└── metadata.yaml
```

### 2.3 SNAPSHOT-MANIFEST.json Format

```json
{
  "snapshot_id": "SNAP-{SOURCE_CODE}-{YYYYMMDD-HHmm}",
  "source_code": "CG",
  "created_at": "2026-02-28T14:00:00Z",
  "trigger": "brownfield_update",
  "new_files_count": 3,
  "previous_pipeline_status": "completed",
  "previous_layer_counts": {
    "L1_philosophies": 12,
    "L2_mental_models": 8,
    "L3_heuristics": 22,
    "L4_frameworks": 15,
    "L5_methodologies": 9
  },
  "file_hashes": {
    "DNA-CONFIG.yaml": "sha256:abc123...",
    "SOUL.md": "sha256:def456...",
    "MEMORY.md": "sha256:ghi789...",
    "AGENT.md": "sha256:jkl012...",
    "metadata.yaml": "sha256:mno345..."
  }
}
```

---

## 3. Diff Classification

The diff analysis classifies each piece of new information into one of four categories:

### 3.1 Classification Types

| Type | Symbol | Description | Action |
|------|--------|-------------|--------|
| **ADDITION** | `+` | New information not present in existing DNA | Append to appropriate layer |
| **REINFORCEMENT** | `=` | Information that confirms/strengthens existing items | Increment confidence weight |
| **CONTRADICTION** | `!` | Information that conflicts with existing DNA | Flag for human review |
| **REDUNDANT** | `~` | Information already captured (duplicate) | Skip, log as redundant |

### 3.2 Layer Impact Matrix

This matrix determines which layers to re-process based on the type of new content detected:

| New Content Type | L1 | L2 | L3 | L4 | L5 | Examples |
|-----------------|----|----|----|----|-----|----------|
| New beliefs/values | RE-EXTRACT | check | - | - | - | "I believe X", "My philosophy is..." |
| New thinking patterns | - | RE-EXTRACT | check | - | - | "The way I think about...", "My mental model..." |
| New rules of thumb | - | - | RE-EXTRACT | check | - | "Always do X before Y", "Never spend more than Z%" |
| New structured methods | - | - | check | RE-EXTRACT | check | "My 5-step process...", "The framework I use..." |
| New implementations | - | - | - | check | RE-EXTRACT | "Step 1: Do X, Step 2: Do Y..." |
| Contradictory statement | FLAG | FLAG | FLAG | FLAG | FLAG | Conflicts with existing item |

Legend:
- `RE-EXTRACT`: Full re-extraction of this layer with new + existing content
- `check`: Verify existing items still valid, update if needed
- `-`: No action needed
- `FLAG`: Flag for human review regardless of layer

### 3.3 Contradiction Handling

```
CONTRADICTION DETECTED
         │
         ▼
    ┌────────────────────────────┐
    │ Is contradiction in L1     │
    │ (core philosophies)?       │
    └────────────┬───────────────┘
                 │
         ┌───────┴───────┐
         │ YES           │ NO
         ▼               ▼
    HALT & ESCALATE    ┌────────────────────────────┐
    (L1 contradictions │ Is it a contextual nuance  │
     require human     │ vs true contradiction?     │
     decision)         └────────────┬───────────────┘
                                    │
                            ┌───────┴───────┐
                            │ NUANCE        │ CONTRADICTION
                            ▼               ▼
                       ADD AS VARIANT   FLAG FOR REVIEW
                       (both versions   (human decides
                        kept with       which to keep)
                        context tags)
```

---

## 4. Rollback Protocol

### 4.1 Rollback Triggers

Automatic rollback is triggered when ANY of these conditions occur during regression testing:

| # | Trigger | Threshold |
|---|---------|-----------|
| 1 | Fidelity score drops | Updated score < previous score - 5% |
| 2 | Items removed | Any pre-existing DNA item missing from merged result |
| 3 | L1 instability | Core philosophy items changed semantically |
| 4 | YAML corruption | Merged DNA-CONFIG.yaml fails validation |
| 5 | Layer missing | Any of 5 layers empty after merge |

### 4.2 Rollback Procedure

```
REGRESSION FAILED
         │
         ▼
    1. HALT all propagation
         │
         ▼
    2. RESTORE files from snapshot
       ├── DNA-CONFIG.yaml ← snapshot
       ├── SOUL.md ← snapshot
       ├── MEMORY.md ← snapshot
       └── AGENT.md ← snapshot
         │
         ▼
    3. LOG rollback event
       └── logs/brownfield/ROLLBACK-{SOURCE}-{DATE}.md
         │
         ▼
    4. PRESERVE diff report
       └── artifacts/brownfield/diffs/{source}/ (kept for debugging)
         │
         ▼
    5. NOTIFY user with:
       ├── Reason for rollback
       ├── Specific failing checks
       ├── Diff report location
       └── Suggested remediation
```

### 4.3 Post-Rollback Options

After a rollback, the user may choose:

| Option | Description |
|--------|-------------|
| **Retry with filters** | Re-run brownfield excluding contradictory sources |
| **Manual merge** | Review diff report and manually decide what to keep |
| **Full reprocess** | Fall back to wf-pipeline-full (greenfield) |
| **Abort** | Keep existing clone unchanged, discard new sources |

---

## 5. Metadata Tracking

### 5.1 metadata.yaml Update

After successful brownfield update, metadata.yaml is updated:

```yaml
pipeline_status: completed
last_greenfield: "2026-01-15T10:00:00Z"
last_brownfield: "2026-02-28T14:00:00Z"
brownfield_updates:
  - date: "2026-02-28T14:00:00Z"
    new_files: 3
    layers_affected: ["L3", "L4"]
    items_added: 7
    items_reinforced: 4
    contradictions_flagged: 1
    snapshot_id: "SNAP-CG-20260228-1400"
total_sources_processed: 15
total_brownfield_updates: 1
```

---

## 6. Integration Points

| System | Integration |
|--------|-------------|
| **wf-pipeline-full** | Brownfield detection runs BEFORE full pipeline; redirects if brownfield confirmed |
| **wf-extract-dna** | Selective extraction reuses extract-dna task with `mode: incremental` |
| **validate-cascade** | Same validation task used for brownfield merge validation |
| **MISSION-STATE.json** | Updated with brownfield session info |
| **Dual-location logging** | Brownfield logs written to both `logs/brownfield/` and `.claude/mission-control/` |

---

## 7. Performance Expectations

| Metric | Greenfield | Brownfield | Savings |
|--------|-----------|------------|---------|
| Layers processed | 5 (all) | 1-3 (affected only) | 40-80% |
| Token usage | 100% baseline | 25-40% of baseline | 60-75% |
| Time | 100% baseline | 30-50% of baseline | 50-70% |
| Snapshot overhead | N/A | ~2% additional | Negligible |

---

**Protocol Version:** 1.0.0
