# SPEC: MCE Pipeline Real-Time Logging for Steps 3-10

> **Version:** 1.0.0
> **Date:** 2026-03-15
> **Author:** System Architecture
> **Status:** READY FOR IMPLEMENTATION
> **Audience:** External Python developer with zero prior knowledge of this project

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [System Context](#2-system-context)
3. [Existing Logging Infrastructure](#3-existing-logging-infrastructure)
4. [Architecture Decision](#4-architecture-decision)
5. [Detailed Requirements](#5-detailed-requirements)
6. [Implementation Guide](#6-implementation-guide)
7. [Human-Readable Log Generation](#7-human-readable-log-generation)
8. [Testing Protocol](#8-testing-protocol)
9. [File Manifest](#9-file-manifest)

---

## 1. Problem Statement

### What the MCE Pipeline Does

The MCE (Mental Cognitive Extraction) Pipeline transforms raw expert content (transcripts,
PDFs, videos) into structured knowledge: DNA schemas, behavioral profiles, voice fingerprints,
and mind-clone agents. It has 12 steps executed in order.

### What Works Today

Steps 0, 1, 2, and 11 are **deterministic** -- they run Python scripts that produce
structured JSON output and append JSONL log entries automatically.

The orchestrator (`core/intelligence/pipeline/mce/orchestrate.py`) uses a function
called `_append_jsonl()` that writes one JSON line per command to
`logs/mce-orchestrate.jsonl`. This happens automatically for every `ingest`, `batch`,
`finalize`, and `status` command.

Additionally:

- `scope_classifier.py` writes to `logs/scope-classifier.jsonl`
- `smart_router.py` writes to `logs/smart-router.jsonl`
- `batch_auto_creator.py` writes to `logs/batch-auto-creator.jsonl`
- `metrics.py` writes to `logs/mce-metrics.jsonl`
- `memory_enricher.py` writes to `logs/memory-enricher.jsonl`
- `workspace_sync.py` writes to `logs/workspace-sync.jsonl`

These scripts all use the same pattern: append a JSON object as a single line to a
`.jsonl` file under `logs/`.

### What is Broken

Steps 3 through 10 are **LLM steps** -- they are executed by a Claude Code skill
(`.claude/skills/pipeline-mce/SKILL.md`). The skill reads prompt templates, sends
content to the LLM, and writes the results to artifact files (JSON and YAML). These
steps produce ZERO operational JSONL log entries.

The artifact files themselves ARE updated:

| Step | Artifact Written |
|------|-----------------|
| 3. Chunking | `artifacts/chunks/CHUNKS-STATE.json` |
| 4. Entity Resolution | `artifacts/canonical/CANONICAL-MAP.json` |
| 5. Insight Extraction | `artifacts/insights/INSIGHTS-STATE.json` |
| 6. MCE Behavioral | `artifacts/insights/INSIGHTS-STATE.json` (updated) |
| 7. MCE Identity | `artifacts/insights/INSIGHTS-STATE.json` (updated) |
| 8. MCE Voice | `knowledge/external/dna/persons/{SLUG}/VOICE-DNA.yaml` |
| 9. Identity Checkpoint | (human interaction, no file write) |
| 10. Consolidation | Multiple files: dossiers, DNA YAMLs, agent files |

But the JSONL audit trail has a complete gap from Step 2 (batch) to Step 11 (finalize).
An operator looking at `logs/mce-orchestrate.jsonl` sees the pipeline start, then
nothing, then the finalize entry -- with no visibility into what happened during the
6-8 most critical extraction steps.

### Why This Matters

1. **No observability.** If Step 5 (insight extraction) takes 45 minutes, the operator
   has no idea whether it is working, stuck, or produced garbage.
2. **No metrics.** Wall-clock timing for LLM steps is not tracked. The `metrics.yaml`
   file only records phases that deterministic scripts explicitly start/stop.
3. **No audit trail.** The system's own rule says "If it was not logged, it was not
   processed." Steps 3-10 violate this rule.
4. **No progressive status.** The human-readable MCE log template
   (`core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md`) has 12 sections that are
   supposed to fill progressively. Without JSONL data for Steps 3-10, sections 3-10
   stay as `[*] PENDENTE` forever.

---

## 2. System Context

This section explains the project structure and conventions an external developer
needs to understand before writing code.

### 2.1 Project Root

The project root is the directory containing `core/`, `agents/`, `knowledge/`,
`artifacts/`, `logs/`, and `.claude/`. All paths in this document are relative to this
root unless stated otherwise.

The Python constant for the project root is defined in `core/paths.py`:

```python
ROOT = Path(__file__).resolve().parent.parent
```

### 2.2 Directory Structure Relevant to Logging

```
mega-brain/                          # Project root
├── core/
│   ├── paths.py                     # Single source of truth for ALL paths
│   ├── intelligence/pipeline/mce/
│   │   ├── orchestrate.py           # Deterministic orchestrator (Steps 0-2, 11)
│   │   ├── state_machine.py         # FSM: init -> chunking -> ... -> complete
│   │   ├── metadata_manager.py      # Phase progress tracking
│   │   ├── metrics.py               # Wall-clock timing per phase
│   │   └── workflow_detector.py     # Greenfield/brownfield detection
│   └── templates/logs/
│       └── MCE-PIPELINE-LOG-TEMPLATE.md  # Human-readable log template (423 lines)
├── artifacts/                       # Pipeline output artifacts (gitignored)
│   ├── chunks/
│   │   └── CHUNKS-STATE.json        # Step 3 output
│   ├── canonical/
│   │   └── CANONICAL-MAP.json       # Step 4 output (persistent, append-only)
│   └── insights/
│       └── INSIGHTS-STATE.json      # Steps 5-7 output (single incremental file)
├── knowledge/external/dna/persons/
│   └── {SLUG}/
│       └── VOICE-DNA.yaml           # Step 8 output
├── logs/                            # All JSONL audit logs (gitignored)
│   ├── mce-orchestrate.jsonl        # Main pipeline audit log
│   ├── mce-metrics.jsonl            # Timing metrics
│   ├── mce-step-logger.jsonl        # NEW: what this spec creates
│   ├── scope-classifier.jsonl
│   ├── smart-router.jsonl
│   ├── batch-auto-creator.jsonl
│   ├── memory-enricher.jsonl
│   ├── workspace-sync.jsonl
│   └── mce/{SLUG}/
│       └── MCE-{TAG}.md             # Human-readable pipeline log
├── .claude/
│   ├── hooks/                       # PostToolUse hooks (Python 3, stdlib + PyYAML)
│   │   ├── pipeline_checkpoint.py   # Existing: pipeline state snapshots
│   │   ├── governance_auto_update.py # Existing: watch-and-trigger pattern
│   │   └── mce_step_logger.py       # NEW: what this spec creates
│   ├── settings.json                # Hook registration
│   ├── mission-control/mce/{SLUG}/  # Per-slug state files
│   │   ├── pipeline_state.yaml      # FSM state + transition history
│   │   ├── metadata.yaml            # Phase progress + sources
│   │   └── metrics.yaml             # Wall-clock timing
│   └── skills/pipeline-mce/
│       └── SKILL.md                 # The skill that executes Steps 3-10
└── .data/                           # Indexes and caches (gitignored)
```

### 2.3 How core/paths.py ROUTING Works

`core/paths.py` defines a single dictionary called `ROUTING` that maps logical names
to filesystem paths. Every script that writes output MUST use these paths instead of
hardcoding them.

Key entries relevant to this spec:

```python
# From core/paths.py (actual code)
LOGS = ROOT / "logs"
ARTIFACTS = ROOT / "artifacts"
MISSION_CONTROL = CLAUDE / "mission-control"

ROUTING = {
    # ...
    "mce_state":       MISSION_CONTROL / "mce",          # Per-slug state dir
    "mce_metrics_log": LOGS / "mce-metrics.jsonl",        # Timing audit
    "mce_cache":       DATA / "mce_cache",                # Analysis cache
    # ...
}
```

The new hook MUST import from `core.paths` where possible. If importing fails (hook
runs outside the Python path), it falls back to environment-variable-based path
construction (see `CLAUDE_PROJECT_DIR` pattern in existing hooks).

### 2.4 Where JSONL Logs Live

All `.jsonl` files live under `logs/` at the project root. The `logs/` directory is
gitignored (L3 runtime data). Each line in a `.jsonl` file is a self-contained JSON
object terminated by `\n`.

### 2.5 Where State Files Live

Per-slug state files live at `.claude/mission-control/mce/{SLUG}/`. Three files per slug:

| File | Content | Format |
|------|---------|--------|
| `pipeline_state.yaml` | FSM state (e.g., `chunking`, `entities`) + transition history | YAML |
| `metadata.yaml` | Phase completion flags, sources processed, attempt counts | YAML |
| `metrics.yaml` | Wall-clock start/end times per phase | YAML |

### 2.6 Where Artifact Files Live

Artifacts are the output of LLM steps. They live under `artifacts/` and
`knowledge/external/dna/persons/`:

| Artifact | Path | Written by Step |
|----------|------|-----------------|
| Chunks | `artifacts/chunks/CHUNKS-STATE.json` | 3 |
| Canonical Map | `artifacts/canonical/CANONICAL-MAP.json` | 4 |
| Insights | `artifacts/insights/INSIGHTS-STATE.json` | 5, 6, 7 |
| Voice DNA | `knowledge/external/dna/persons/{SLUG}/VOICE-DNA.yaml` | 8 |
| Dossier | `knowledge/external/dossiers/persons/DOSSIER-{PERSON}.md` | 10 |
| DNA YAMLs | `knowledge/external/dna/persons/{SLUG}/*.yaml` | 10 |
| Agent files | `agents/external/{SLUG}/*.md` | 10 |

### 2.7 The Existing _append_jsonl() Pattern

The orchestrator uses this exact function to write log entries. This is the canonical
pattern that the new hook MUST replicate:

```python
# From core/intelligence/pipeline/mce/orchestrate.py (lines 181-192)

_ORCHESTRATE_LOG = LOGS / "mce-orchestrate.jsonl"

def _append_jsonl(entry: dict[str, Any]) -> None:
    """Append a JSON line to the orchestrate audit log.

    Non-fatal: swallows all exceptions so it never blocks pipeline work.
    """
    try:
        _ORCHESTRATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_ORCHESTRATE_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write orchestrate JSONL", exc_info=True)
```

Key properties of this pattern:

1. **Non-fatal.** Logging failures are swallowed silently. Logging must NEVER block
   pipeline execution.
2. **mkdir parents.** The parent directory is created if it does not exist.
3. **Append mode.** File is opened with `"a"` (append), never `"w"` (write/truncate).
4. **ensure_ascii=False.** Supports non-ASCII content (Portuguese text is common).
5. **default=str.** Handles `Path`, `datetime`, and other non-serializable types.
6. **Newline terminated.** Each entry ends with `\n`.

---

## 3. Existing Logging Infrastructure

### 3.1 All 13 JSONL Log Files

| # | Log File | Writer Script | What It Records |
|---|----------|---------------|-----------------|
| 1 | `logs/mce-orchestrate.jsonl` | `orchestrate.py` | Every MCE command (ingest, batch, finalize, status) |
| 2 | `logs/mce-metrics.jsonl` | `metrics.py` | Wall-clock timing summary per pipeline run |
| 3 | `logs/scope-classifier.jsonl` | `scope_classifier.py` | 6-signal classification results |
| 4 | `logs/smart-router.jsonl` | `smart_router.py` | File routing decisions (moved_to, references_created) |
| 5 | `logs/batch-auto-creator.jsonl` | `batch_auto_creator.py` | Batch creation events (batch_id, file_count) |
| 6 | `logs/memory-enricher.jsonl` | `memory_enricher.py` | Insight-to-MEMORY.md routing |
| 7 | `logs/workspace-sync.jsonl` | `workspace_sync.py` | Business knowledge synced to workspace |
| 8 | `logs/agent-creation.jsonl` | `agent_creation_trigger.py` | MCE threshold check (3+ insights triggers agent) |
| 9 | `logs/agent-index-updates.jsonl` | `agent_index_updater.py` | AGENT-INDEX.yaml modifications |
| 10 | `logs/pipeline-checkpoints.jsonl` | `pipeline_checkpoint.py` | Pipeline state snapshots |
| 11 | `logs/pipeline-guard.jsonl` | `pipeline_guard.py` | Output path validation against ROUTING |
| 12 | `logs/claude-md-sync.jsonl` | `claude_md_agent_sync.py` | CLAUDE.md auto-updates |
| 13 | `logs/prompts.jsonl` | PostToolUse hooks | Prompt execution tracking |

The new logger will create entry **#14**: `logs/mce-step-logger.jsonl`.

### 3.2 JSON Schema of a Log Entry

Here is the actual schema used by `mce-orchestrate.jsonl` (from `_build_result()`
in `orchestrate.py`, lines 237-256):

```json
{
  "command": "ingest",
  "success": true,
  "timestamp": "2026-03-15T14:23:01.123456+00:00",
  "duration_ms": 342.7,
  "slug": "alex-hormozi",
  "file_path": "/absolute/path/to/file.txt",
  "classification": {
    "primary_bucket": "external",
    "cascade_buckets": ["business"],
    "confidence": 0.792,
    "source_type": "transcript",
    "reasons": ["S1: path pattern match", "S3: expert keywords"]
  },
  "routing": {
    "action": "move",
    "moved_to": "/path/to/knowledge/external/inbox/alex-hormozi/file.txt",
    "references_created": []
  },
  "state": {
    "current": "init",
    "metadata_status": "in_progress"
  }
}
```

The new logger will follow a compatible schema with `step`, `step_name`, `slug`,
`timestamp`, `artifact_path`, `metrics`, and step-specific fields.

### 3.3 The Hook System

Claude Code hooks are Python scripts registered in `.claude/settings.json`. They
fire at specific lifecycle events.

**Event types relevant to this spec:**

| Event | When It Fires | Receives |
|-------|---------------|----------|
| `PreToolUse` | Before a tool call executes | `tool_name`, `tool_input` |
| `PostToolUse` | After a tool call completes | `tool_name`, `tool_input`, `tool_output` |

**How hooks receive data:**

Hooks read a JSON payload from stdin. The payload structure for PostToolUse:

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/absolute/path/to/artifacts/chunks/CHUNKS-STATE.json",
    "content": "... the file content ..."
  }
}
```

For the `Edit` tool:

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/absolute/path/to/artifacts/insights/INSIGHTS-STATE.json",
    "old_string": "...",
    "new_string": "..."
  }
}
```

**How hooks respond:**

Hooks print a JSON response to stdout:

```json
{
  "continue": true,
  "feedback": "Optional message shown to the LLM"
}
```

If `feedback` is `null` or missing, no message is shown. If present, the LLM sees it
as a system message.

**Hook registration in settings.json:**

The `PostToolUse` section in `.claude/settings.json` has two matcher groups:

1. Matcher `""` (empty string) -- fires on ALL tool calls (12 hooks registered here)
2. Matcher `"Write|Edit"` -- fires only on Write or Edit tool calls (1 hook registered here)

The new hook MUST be registered in the `"Write|Edit"` matcher group, because it only
needs to fire when artifact files are written or edited.

### 3.4 Existing PostToolUse Hooks

Currently registered in `.claude/settings.json` PostToolUse section:

**Matcher "" (all tools):**

| # | Hook | Purpose |
|---|------|---------|
| 1 | `post_tool_use.py` | General post-tool-use processing |
| 2 | `enforce_dual_location.py` | Verify dual-location logging |
| 3 | `pipeline_checkpoint.py` | Snapshot pipeline state |
| 4 | `agent_creation_trigger.py` | Check MCE threshold (3+ insights) |
| 5 | `agent_index_updater.py` | Update AGENT-INDEX.yaml |
| 6 | `claude_md_agent_sync.py` | Sync CLAUDE.md when agents change |
| 7 | `agent_memory_persister.py` | Persist agent memory |
| 8 | `memory_capture.py` | Capture conversation memory |
| 9 | `post_batch_cascading.py` | Cascade knowledge to dossiers |
| 10 | `pipeline_phase_gate.py` | Verify phase complete before advance |
| 11 | `pipeline_orchestrator.py` | Auto-advance pipeline |
| 12 | `pipeline_guard.py` | Validate output path |

**Matcher "Write|Edit":**

| # | Hook | Purpose |
|---|------|---------|
| 1 | `governance_auto_update.py` | Regenerate governance docs when rules change |

### 3.5 The governance_auto_update.py Pattern

This hook demonstrates the exact pattern the new logger should follow. It watches
for writes to specific file paths and triggers an action when a match is found.

From `.claude/hooks/governance_auto_update.py`:

```python
_ROOT = Path(__file__).resolve().parent.parent.parent
WATCH_PREFIXES = ("core/engine/rules/", "core/intelligence/pipeline/mce/")
WATCH_EXACT = {
    "core/paths.py", "pyproject.toml", "biome.json",
    "package.json", ".claude/settings.json",
}

def _to_relative(file_path: str) -> str:
    try:
        return str(Path(file_path).resolve().relative_to(_ROOT))
    except (ValueError, OSError):
        return file_path

def _matches(rel: str) -> bool:
    if rel in WATCH_EXACT:
        return True
    return any(rel.startswith(p) for p in WATCH_PREFIXES)
```

The new hook will use this same `_to_relative()` + prefix matching pattern to detect
artifact file writes.

---

## 4. Architecture Decision

### 4.1 Recommended Approach: Hook-Based Detection

The new logging system uses a **PostToolUse hook** that watches for Write/Edit
operations on artifact files. When a matching file is written, the hook reads the
artifact, extracts relevant metrics, and appends a JSONL log entry.

### 4.2 Why Hook-Based, Not Skill-Based

Three approaches were considered:

| Approach | Description | Verdict |
|----------|-------------|---------|
| **A: Skill-based** | Modify the skill (SKILL.md) to add logging instructions | REJECTED |
| **B: Orchestrator-based** | Extend orchestrate.py to call LLM steps | REJECTED |
| **C: Hook-based** | PostToolUse hook detects artifact writes | SELECTED |

**Why A (skill-based) was rejected:**

- Skills are natural-language instructions to an LLM. The LLM might forget, skip, or
  incorrectly format log entries.
- Skill modifications require LLM cooperation. Hooks do not.
- Testing is non-deterministic. You cannot assert that an LLM will always log correctly.

**Why B (orchestrator-based) was rejected:**

- The orchestrator (`orchestrate.py`) runs as a separate Python process. It has no
  visibility into LLM tool calls. Steps 3-10 are executed by the LLM using Claude Code
  native tools (Write, Edit, Read), not by calling orchestrate.py.

**Why C (hook-based) was selected:**

- Hooks fire automatically on every Write/Edit tool call. No LLM cooperation required.
- The hook can read the artifact file that was just written and extract metrics.
- Hooks are Python scripts with a well-defined contract (stdin JSON, stdout JSON).
- Existing hooks (`pipeline_checkpoint.py`, `governance_auto_update.py`) prove this
  pattern works reliably.
- The hook is invisible to the LLM -- it cannot be forgotten or skipped.

### 4.3 Trigger Definition

The hook fires on PostToolUse when:

1. `tool_name` is `Write` or `Edit`
2. `file_path` matches one of the artifact patterns (see Section 5)

### 4.4 Slug Detection Strategy

The hook must determine which pipeline slug the artifact belongs to. Two strategies:

1. **Path-based:** Extract slug from the file path (e.g.,
   `knowledge/external/dna/persons/alex-hormozi/VOICE-DNA.yaml` -> `alex-hormozi`).
2. **State-file scan:** Scan `.claude/mission-control/mce/` for active (non-complete)
   pipelines and use the slug of the currently running one.

The implementation should try path-based first. If ambiguous, fall back to state-file
scan. See Section 6 for implementation details.

---

## 5. Detailed Requirements

### 5.1 Step 3: CHUNK

**Artifact written:** `artifacts/chunks/CHUNKS-STATE.json`

**Pattern match:** File path contains `artifacts/chunks/CHUNKS-STATE.json`

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T14:25:00.000000+00:00",
  "step": 3,
  "step_name": "chunking",
  "slug": "alex-hormozi",
  "artifact_path": "artifacts/chunks/CHUNKS-STATE.json",
  "metrics": {
    "chunks_created": 45,
    "avg_chunk_words": 312,
    "total_tokens_estimate": 18400,
    "persons_detected": ["Alex Hormozi", "Leila Hormozi"],
    "source_files_processed": 5
  },
  "validation": {
    "has_chunks": true,
    "all_chunks_have_ids": true,
    "chunk_count": 45
  }
}
```

**Fields to extract from artifact:**

- Parse `CHUNKS-STATE.json` as JSON.
- Count entries in the `chunks` array -> `chunks_created`.
- For each chunk, count words in `text` field -> compute average -> `avg_chunk_words`.
- Estimate tokens as `total_words * 1.3` -> `total_tokens_estimate`.
- Extract unique values from `speaker` or `person` fields -> `persons_detected`.
- Count unique `source_file` values -> `source_files_processed`.
- Validate: every chunk has an `id_chunk` field -> `all_chunks_have_ids`.

---

### 5.2 Step 4: ENTITY RESOLUTION

**Artifact written:** `artifacts/canonical/CANONICAL-MAP.json`

**Pattern match:** File path contains `artifacts/canonical/CANONICAL-MAP.json`

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T14:30:00.000000+00:00",
  "step": 4,
  "step_name": "entity_resolution",
  "slug": "alex-hormozi",
  "artifact_path": "artifacts/canonical/CANONICAL-MAP.json",
  "metrics": {
    "total_entities": 12,
    "total_variants": 34,
    "new_entities_added": 3,
    "new_variants_added": 8
  },
  "validation": {
    "has_entities": true,
    "entity_count": 12
  }
}
```

**Fields to extract from artifact:**

- Parse `CANONICAL-MAP.json` as JSON.
- Count top-level canonical entries -> `total_entities`.
- Sum all variant arrays -> `total_variants`.
- To determine `new_entities_added` and `new_variants_added`: the hook should read
  the previous log entry for this step (from `logs/mce-step-logger.jsonl`) and
  compute the delta. If no previous entry exists, set both to the total values.

---

### 5.3 Step 5: INSIGHT EXTRACTION

**Artifact written:** `artifacts/insights/INSIGHTS-STATE.json`

**Pattern match:** File path contains `artifacts/insights/INSIGHTS-STATE.json`

**Differentiation:** Steps 5, 6, and 7 all write to the same file. The hook must
detect WHICH step just executed by examining the file content:

| Condition | Step Detected |
|-----------|---------------|
| File has `persons` with `insights` arrays but NO `behavioral_patterns` | Step 5 |
| File has `behavioral_patterns` field but NO `value_hierarchy` | Step 6 |
| File has `value_hierarchy` field | Step 7 |

**JSONL entry schema (Step 5):**

```json
{
  "timestamp": "2026-03-15T14:35:00.000000+00:00",
  "step": 5,
  "step_name": "insight_extraction",
  "slug": "alex-hormozi",
  "artifact_path": "artifacts/insights/INSIGHTS-STATE.json",
  "metrics": {
    "total_insights": 42,
    "by_priority": {"HIGH": 8, "MEDIUM": 22, "LOW": 12},
    "by_dna_tag": {
      "FILOSOFIA": 5,
      "MODELO-MENTAL": 8,
      "HEURISTICA": 12,
      "FRAMEWORK": 10,
      "METODOLOGIA": 7
    },
    "persons_with_insights": 2
  },
  "validation": {
    "has_persons": true,
    "has_insights": true,
    "insights_have_chunk_refs": true,
    "insight_count": 42
  }
}
```

**Fields to extract from artifact:**

- Parse `INSIGHTS-STATE.json` as JSON.
- Navigate to each person's `insights` array -> count total -> `total_insights`.
- Count by `priority` field -> `by_priority`.
- Count by `tag` field -> `by_dna_tag`.
- Count entries in `persons` -> `persons_with_insights`.
- Validate: each insight has at least one `chunk_id` reference -> `insights_have_chunk_refs`.

---

### 5.4 Step 6: MCE BEHAVIORAL

**Artifact written:** `artifacts/insights/INSIGHTS-STATE.json` (same file as Step 5)

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T14:40:00.000000+00:00",
  "step": 6,
  "step_name": "mce_behavioral",
  "slug": "alex-hormozi",
  "artifact_path": "artifacts/insights/INSIGHTS-STATE.json",
  "metrics": {
    "total_patterns": 15,
    "by_type": {
      "decision": 4,
      "reaction": 3,
      "habit": 5,
      "communication": 3
    },
    "patterns_with_evidence": 15,
    "avg_evidence_chunks": 3.2
  },
  "validation": {
    "has_behavioral_patterns": true,
    "all_patterns_have_2plus_chunks": true,
    "pattern_count": 15
  }
}
```

**Fields to extract from artifact:**

- Read `behavioral_patterns` field from INSIGHTS-STATE.json.
- Count entries -> `total_patterns`.
- Group by `type` field -> `by_type`.
- Count patterns with >= 2 `chunk_ids` -> `patterns_with_evidence`.
- Average `len(chunk_ids)` across all patterns -> `avg_evidence_chunks`.
- Validate: every pattern has >= 2 chunk_ids -> `all_patterns_have_2plus_chunks`.

---

### 5.5 Step 7: MCE IDENTITY

**Artifact written:** `artifacts/insights/INSIGHTS-STATE.json` (same file as Steps 5-6)

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T14:45:00.000000+00:00",
  "step": 7,
  "step_name": "mce_identity",
  "slug": "alex-hormozi",
  "artifact_path": "artifacts/insights/INSIGHTS-STATE.json",
  "metrics": {
    "values_count": 7,
    "tier1_count": 2,
    "tier2_count": 5,
    "obsessions_count": 3,
    "master_obsessions": 1,
    "paradoxes_count": 2,
    "productive_paradoxes": 1
  },
  "validation": {
    "has_value_hierarchy": true,
    "has_tier1_value": true,
    "has_obsessions": true,
    "exactly_one_master": true,
    "has_paradoxes": true
  }
}
```

**Fields to extract from artifact:**

- Read `value_hierarchy` -> count entries, filter by tier -> `values_count`, `tier1_count`, `tier2_count`.
- Read `obsessions` -> count total, count entries where status is "MASTER" -> `obsessions_count`, `master_obsessions`.
- Read `paradoxes` -> count total, count where `productive` is true -> `paradoxes_count`, `productive_paradoxes`.
- Validate: exactly 1 MASTER obsession, at least 1 Tier 1 value.

---

### 5.6 Step 8: MCE VOICE

**Artifact written:** `knowledge/external/dna/persons/{SLUG}/VOICE-DNA.yaml`

**Pattern match:** File path matches `knowledge/external/dna/persons/*/VOICE-DNA.yaml`

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T14:50:00.000000+00:00",
  "step": 8,
  "step_name": "mce_voice",
  "slug": "alex-hormozi",
  "artifact_path": "knowledge/external/dna/persons/alex-hormozi/VOICE-DNA.yaml",
  "metrics": {
    "tone_dimensions_defined": 6,
    "signature_phrases": 8,
    "behavioral_states": 4,
    "forbidden_patterns": 2,
    "tone_profile": {
      "certainty": 9,
      "authority": 8,
      "warmth": 5,
      "directness": 9,
      "humor": 4,
      "formality": 3
    }
  },
  "validation": {
    "has_tone_profile": true,
    "has_signature_phrases": true,
    "signature_phrases_gte_5": true,
    "has_behavioral_states": true,
    "tone_dimensions_complete": true
  }
}
```

**Fields to extract from artifact:**

- Parse YAML file.
- Count defined tone dimensions (out of 6: certainty, authority, warmth, directness, humor, formality).
- Count entries in `signature_phrases` array.
- Count entries in `behavioral_states` array.
- Count entries in `forbidden_patterns` or `forbidden_words` array.
- Extract all 6 tone scores into `tone_profile`.
- Validate: >= 5 signature phrases, all 6 tone dimensions defined.

---

### 5.7 Step 9: IDENTITY CHECKPOINT

**No artifact written.** This step is a human interaction pause. The hook cannot
detect this step via file writes.

**Alternative detection:** When Step 9 completes (user approves), the skill
transitions the state machine from `identity_checkpoint` to `consolidation`. This
state change is written to `pipeline_state.yaml`. The hook CAN watch for writes to
`.claude/mission-control/mce/*/pipeline_state.yaml` and detect the transition.

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T15:00:00.000000+00:00",
  "step": 9,
  "step_name": "identity_checkpoint",
  "slug": "alex-hormozi",
  "artifact_path": ".claude/mission-control/mce/alex-hormozi/pipeline_state.yaml",
  "metrics": {
    "decision": "APPROVE",
    "previous_state": "identity_checkpoint",
    "new_state": "consolidation"
  },
  "validation": {
    "checkpoint_resolved": true
  }
}
```

**Detection logic:**

- Watch for writes to `.claude/mission-control/mce/*/pipeline_state.yaml`.
- Parse YAML. If `state` is `consolidation` and the last history entry shows
  `from: identity_checkpoint`, `to: consolidation`, log the checkpoint step.

---

### 5.8 Step 10: CONSOLIDATION

**Artifacts written:** Multiple files across several directories.

**Pattern matches:**

| Sub-step | Pattern | What |
|----------|---------|------|
| 10.1 Dossier | `knowledge/external/dossiers/persons/DOSSIER-*.md` | Person dossier |
| 10.2 Sources | `knowledge/external/sources/*/` | Theme compilation docs |
| 10.3 DNA YAMLs | `knowledge/external/dna/persons/*/FILOSOFIAS.yaml` | (and 4 more YAML files) |
| 10.4 Agent | `agents/external/*/AGENT.md` | Agent main file |

Because Step 10 writes many files, the hook should log ONE consolidated entry when
the LAST expected artifact is written (the agent files, sub-step 10.4). Individual
file writes during Step 10 should be accumulated in memory within the hook.

**JSONL entry schema:**

```json
{
  "timestamp": "2026-03-15T15:10:00.000000+00:00",
  "step": 10,
  "step_name": "consolidation",
  "slug": "alex-hormozi",
  "artifact_path": "agents/external/alex-hormozi/AGENT.md",
  "metrics": {
    "dossier_created": true,
    "dossier_path": "knowledge/external/dossiers/persons/DOSSIER-ALEX-HORMOZI.md",
    "source_docs_created": 5,
    "dna_yamls_created": 5,
    "dna_yamls": [
      "FILOSOFIAS.yaml",
      "MODELOS-MENTAIS.yaml",
      "HEURISTICAS.yaml",
      "FRAMEWORKS.yaml",
      "METODOLOGIAS.yaml"
    ],
    "agent_files_created": 4,
    "agent_files": [
      "AGENT.md",
      "SOUL.md",
      "MEMORY.md",
      "DNA-CONFIG.yaml"
    ]
  },
  "validation": {
    "has_dossier": true,
    "has_dna_yamls": true,
    "has_agent_files": true,
    "all_artifacts_present": true
  }
}
```

**Detection logic:**

Since Step 10 writes multiple files across multiple Write/Edit calls, the hook should:

1. Track Step 10 artifact writes in a small state file:
   `.claude/mission-control/mce/{SLUG}/step10_tracker.json`.
2. Each matching Write/Edit updates the tracker with the file written.
3. When the tracker detects that agent files are written (`AGENT.md` or
   `DNA-CONFIG.yaml`), emit the consolidated JSONL entry and delete the tracker.

**Alternative (simpler):** Log each sub-step as a separate JSONL entry with a
`substep` field (e.g., `10.1`, `10.2`, `10.3`, `10.4`). This avoids stateful
tracking at the cost of more log entries. RECOMMENDED for initial implementation.

---

### 5.9 All Log Entries Go To

All entries from this hook are appended to a single file:

```
logs/mce-step-logger.jsonl
```

This is ONE file for all slugs, all steps. Each entry has a `slug` field for filtering.

---

## 6. Implementation Guide

### 6.1 New File: .claude/hooks/mce_step_logger.py

Create this file at `.claude/hooks/mce_step_logger.py`.

**Constraints (per project hook rules):**

- Python 3 standard library ONLY, plus `PyYAML` (the only allowed external dependency for hooks).
- No `pip install` of anything else.
- Must exit 0 on success, 1 on warning (shown to LLM but does not block), 2 on
  block (never use -- logging must never block).
- Timeout: 5000ms (5 seconds).

### 6.2 Code Skeleton

```python
#!/usr/bin/env python3
"""MCE Step Logger -- PostToolUse (Write|Edit).

Detects writes to MCE artifact files during Steps 3-10 and appends
structured JSONL log entries. Never blocks pipeline execution (exit 0).

Version: 1.0.0
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Optional: PyYAML for VOICE-DNA.yaml parsing and state file parsing
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
LOG_PATH = PROJECT_DIR / "logs" / "mce-step-logger.jsonl"
MCE_STATE_DIR = PROJECT_DIR / ".claude" / "mission-control" / "mce"

# Artifact patterns: prefix -> (step_number, step_name)
# Order matters: more specific patterns first
ARTIFACT_PATTERNS: list[tuple[str, int, str]] = [
    ("artifacts/chunks/CHUNKS-STATE.json", 3, "chunking"),
    ("artifacts/canonical/CANONICAL-MAP.json", 4, "entity_resolution"),
    ("artifacts/insights/INSIGHTS-STATE.json", -1, "_insights_detect"),  # special: steps 5/6/7
    ("knowledge/external/dna/persons/", 8, "mce_voice"),                 # VOICE-DNA.yaml only
    ("knowledge/external/dossiers/persons/DOSSIER-", 10, "consolidation"),
    ("knowledge/external/dna/persons/", 10, "consolidation"),            # DNA YAMLs (non-VOICE)
    ("knowledge/external/sources/", 10, "consolidation"),
    ("agents/external/", 10, "consolidation"),
    (".claude/mission-control/mce/", 9, "identity_checkpoint"),          # state file writes
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _to_relative(file_path: str) -> str:
    """Convert absolute path to project-relative path."""
    try:
        return str(Path(file_path).resolve().relative_to(PROJECT_DIR))
    except (ValueError, OSError):
        return file_path


def _append_jsonl(entry: dict[str, Any]) -> None:
    """Append a JSON line to the step logger audit log.

    Non-fatal: swallows all exceptions so it never blocks pipeline work.
    """
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # Never block


def _read_json(path: Path) -> dict | list | None:
    """Read a JSON file, returning None on any error."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _read_yaml(path: Path) -> dict | None:
    """Read a YAML file, returning None on any error or if PyYAML is missing."""
    if not HAS_YAML:
        return None
    try:
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        pass
    return None


def _detect_slug_from_path(rel: str) -> str:
    """Extract slug from a relative artifact path.

    Examples:
        'knowledge/external/dna/persons/alex-hormozi/VOICE-DNA.yaml' -> 'alex-hormozi'
        'agents/external/alex-hormozi/AGENT.md' -> 'alex-hormozi'
        'artifacts/chunks/CHUNKS-STATE.json' -> (needs state scan)
    """
    parts = Path(rel).parts
    # Pattern: .../persons/{slug}/... or .../external/{slug}/...
    for i, part in enumerate(parts):
        if part in ("persons", "external") and i + 1 < len(parts):
            candidate = parts[i + 1]
            # Skip if it looks like a filename (has extension)
            if "." not in candidate:
                return candidate
    return ""


def _detect_slug_from_state() -> str:
    """Scan MCE state dirs for the active (non-complete) pipeline slug."""
    if not MCE_STATE_DIR.exists():
        return ""
    for d in sorted(MCE_STATE_DIR.iterdir()):
        if not d.is_dir():
            continue
        state_file = d / "pipeline_state.yaml"
        data = _read_yaml(state_file)
        if data and data.get("state") not in ("complete", "failed", None):
            return d.name
    return ""


def _detect_slug(rel: str) -> str:
    """Detect slug from path, with fallback to state scan."""
    slug = _detect_slug_from_path(rel)
    if not slug:
        slug = _detect_slug_from_state()
    return slug


# ---------------------------------------------------------------------------
# Step Detection and Matching
# ---------------------------------------------------------------------------


def _match_artifact(rel: str) -> tuple[int, str] | None:
    """Match a relative path against artifact patterns.

    Returns (step_number, step_name) or None if no match.
    """
    # Special case: VOICE-DNA.yaml specifically
    if "VOICE-DNA.yaml" in rel and "knowledge/external/dna/persons/" in rel:
        return (8, "mce_voice")

    # Special case: pipeline_state.yaml for Step 9
    if "pipeline_state.yaml" in rel and ".claude/mission-control/mce/" in rel:
        return (9, "identity_checkpoint")

    # Special case: Step 10 DNA YAMLs (not VOICE-DNA)
    dna_yaml_names = {
        "FILOSOFIAS.yaml", "MODELOS-MENTAIS.yaml", "HEURISTICAS.yaml",
        "FRAMEWORKS.yaml", "METODOLOGIAS.yaml",
    }
    filename = Path(rel).name
    if filename in dna_yaml_names and "knowledge/external/dna/persons/" in rel:
        return (10, "consolidation")

    for pattern, step, name in ARTIFACT_PATTERNS:
        if pattern in rel:
            return (step, name)

    return None


def _detect_insights_step(data: dict) -> tuple[int, str]:
    """Differentiate Steps 5/6/7 by examining INSIGHTS-STATE.json content.

    Returns (step_number, step_name).
    """
    # Check for Step 7 markers first (most specific)
    persons = data.get("persons", {})
    any_person = next(iter(persons.values()), {}) if isinstance(persons, dict) else {}
    if not isinstance(any_person, dict):
        any_person = {}

    if data.get("value_hierarchy") or any_person.get("value_hierarchy"):
        return (7, "mce_identity")

    if data.get("behavioral_patterns") or any_person.get("behavioral_patterns"):
        return (6, "mce_behavioral")

    return (5, "insight_extraction")


# ---------------------------------------------------------------------------
# Metric Extractors (one per step)
# ---------------------------------------------------------------------------


def _extract_step3(data: Any) -> tuple[dict, dict]:
    """Extract metrics from CHUNKS-STATE.json."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    chunks = []
    if isinstance(data, dict):
        chunks = data.get("chunks", [])
    elif isinstance(data, list):
        chunks = data

    metrics["chunks_created"] = len(chunks)

    # Compute avg words
    word_counts = []
    persons_set: set[str] = set()
    sources_set: set[str] = set()
    all_have_ids = True

    for c in chunks:
        if not isinstance(c, dict):
            continue
        text = c.get("text", "")
        word_counts.append(len(text.split()))
        for field in ("speaker", "person", "persona"):
            val = c.get(field, "")
            if val:
                persons_set.add(str(val))
        src = c.get("source_file", c.get("source", ""))
        if src:
            sources_set.add(str(src))
        if not c.get("id_chunk") and not c.get("id"):
            all_have_ids = False

    metrics["avg_chunk_words"] = round(sum(word_counts) / max(len(word_counts), 1))
    metrics["total_tokens_estimate"] = round(sum(word_counts) * 1.3)
    metrics["persons_detected"] = sorted(persons_set)
    metrics["source_files_processed"] = len(sources_set)

    validation["has_chunks"] = len(chunks) > 0
    validation["all_chunks_have_ids"] = all_have_ids
    validation["chunk_count"] = len(chunks)

    return metrics, validation


def _extract_step4(data: Any) -> tuple[dict, dict]:
    """Extract metrics from CANONICAL-MAP.json."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    entities = {}
    if isinstance(data, dict):
        # Support both flat {canonical: [variants]} and nested structures
        entities = data.get("entities", data)

    total_entities = 0
    total_variants = 0
    for _key, val in entities.items():
        if isinstance(val, list):
            total_entities += 1
            total_variants += len(val)
        elif isinstance(val, dict) and "variants" in val:
            total_entities += 1
            total_variants += len(val.get("variants", []))

    metrics["total_entities"] = total_entities
    metrics["total_variants"] = total_variants

    validation["has_entities"] = total_entities > 0
    validation["entity_count"] = total_entities

    return metrics, validation


def _extract_step5(data: dict) -> tuple[dict, dict]:
    """Extract metrics from INSIGHTS-STATE.json (insight extraction)."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    persons = data.get("persons", {})
    total_insights = 0
    by_priority: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    has_chunk_refs = True

    if isinstance(persons, dict):
        for _name, pdata in persons.items():
            insights = []
            if isinstance(pdata, dict):
                insights = pdata.get("insights", [])
            elif isinstance(pdata, list):
                insights = pdata
            total_insights += len(insights)
            for ins in insights:
                if not isinstance(ins, dict):
                    continue
                prio = ins.get("priority", "UNKNOWN")
                by_priority[prio] = by_priority.get(prio, 0) + 1
                tag = ins.get("tag", "UNKNOWN")
                by_tag[tag] = by_tag.get(tag, 0) + 1
                if not ins.get("chunk_id") and not ins.get("chunk_ids"):
                    has_chunk_refs = False

    metrics["total_insights"] = total_insights
    metrics["by_priority"] = by_priority
    metrics["by_dna_tag"] = by_tag
    metrics["persons_with_insights"] = len(persons) if isinstance(persons, dict) else 0

    validation["has_persons"] = len(persons) > 0 if isinstance(persons, dict) else False
    validation["has_insights"] = total_insights > 0
    validation["insights_have_chunk_refs"] = has_chunk_refs
    validation["insight_count"] = total_insights

    return metrics, validation


def _extract_step6(data: dict) -> tuple[dict, dict]:
    """Extract metrics from INSIGHTS-STATE.json (behavioral patterns)."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    patterns = data.get("behavioral_patterns", [])
    # Also check inside persons
    if not patterns:
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            for _name, pdata in persons.items():
                if isinstance(pdata, dict):
                    patterns.extend(pdata.get("behavioral_patterns", []))

    by_type: dict[str, int] = {}
    with_evidence = 0
    total_chunks = 0

    for p in patterns:
        if not isinstance(p, dict):
            continue
        ptype = p.get("type", "unknown")
        by_type[ptype] = by_type.get(ptype, 0) + 1
        chunk_ids = p.get("chunk_ids", p.get("chunks", []))
        if len(chunk_ids) >= 2:
            with_evidence += 1
        total_chunks += len(chunk_ids)

    metrics["total_patterns"] = len(patterns)
    metrics["by_type"] = by_type
    metrics["patterns_with_evidence"] = with_evidence
    metrics["avg_evidence_chunks"] = round(total_chunks / max(len(patterns), 1), 1)

    validation["has_behavioral_patterns"] = len(patterns) > 0
    validation["all_patterns_have_2plus_chunks"] = with_evidence == len(patterns) and len(patterns) > 0
    validation["pattern_count"] = len(patterns)

    return metrics, validation


def _extract_step7(data: dict) -> tuple[dict, dict]:
    """Extract metrics from INSIGHTS-STATE.json (identity layers)."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    values = data.get("value_hierarchy", [])
    obsessions = data.get("obsessions", [])
    paradoxes = data.get("paradoxes", [])

    # Also check inside persons
    if not values:
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            for _name, pdata in persons.items():
                if isinstance(pdata, dict):
                    if not values:
                        values = pdata.get("value_hierarchy", [])
                    if not obsessions:
                        obsessions = pdata.get("obsessions", [])
                    if not paradoxes:
                        paradoxes = pdata.get("paradoxes", [])

    tier1 = sum(1 for v in values if isinstance(v, dict) and v.get("tier") == 1)
    tier2 = sum(1 for v in values if isinstance(v, dict) and v.get("tier") == 2)
    masters = sum(1 for o in obsessions if isinstance(o, dict) and
                  str(o.get("status", "")).upper() == "MASTER")
    productive = sum(1 for p in paradoxes if isinstance(p, dict) and p.get("productive"))

    metrics["values_count"] = len(values)
    metrics["tier1_count"] = tier1
    metrics["tier2_count"] = tier2
    metrics["obsessions_count"] = len(obsessions)
    metrics["master_obsessions"] = masters
    metrics["paradoxes_count"] = len(paradoxes)
    metrics["productive_paradoxes"] = productive

    validation["has_value_hierarchy"] = len(values) > 0
    validation["has_tier1_value"] = tier1 > 0
    validation["has_obsessions"] = len(obsessions) > 0
    validation["exactly_one_master"] = masters == 1
    validation["has_paradoxes"] = len(paradoxes) > 0

    return metrics, validation


def _extract_step8(data: dict) -> tuple[dict, dict]:
    """Extract metrics from VOICE-DNA.yaml."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    tone_keys = ["certainty", "authority", "warmth", "directness", "humor", "formality"]
    tone_profile = {}
    tone_data = data.get("tone_profile", data.get("tone", {}))
    if isinstance(tone_data, dict):
        for k in tone_keys:
            val = tone_data.get(k)
            if val is not None:
                tone_profile[k] = val

    phrases = data.get("signature_phrases", [])
    states = data.get("behavioral_states", [])
    forbidden = data.get("forbidden_patterns", data.get("forbidden_words", []))

    metrics["tone_dimensions_defined"] = len(tone_profile)
    metrics["signature_phrases"] = len(phrases)
    metrics["behavioral_states"] = len(states)
    metrics["forbidden_patterns"] = len(forbidden) if isinstance(forbidden, list) else 0
    metrics["tone_profile"] = tone_profile

    validation["has_tone_profile"] = len(tone_profile) > 0
    validation["has_signature_phrases"] = len(phrases) > 0
    validation["signature_phrases_gte_5"] = len(phrases) >= 5
    validation["has_behavioral_states"] = len(states) > 0
    validation["tone_dimensions_complete"] = len(tone_profile) == 6

    return metrics, validation


def _extract_step9(data: dict) -> tuple[dict, dict]:
    """Extract metrics from pipeline_state.yaml (identity checkpoint)."""
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    history = data.get("history", [])
    current_state = data.get("state", "")

    # Find the checkpoint resolution in history
    decision = "UNKNOWN"
    prev_state = ""
    for entry in reversed(history):
        if isinstance(entry, dict):
            if entry.get("to") == "consolidation" and entry.get("from") == "identity_checkpoint":
                decision = "APPROVE"
                prev_state = "identity_checkpoint"
                break
            elif entry.get("to") == "mce_extraction" and entry.get("from") == "identity_checkpoint":
                decision = "REVISE"
                prev_state = "identity_checkpoint"
                break

    metrics["decision"] = decision
    metrics["previous_state"] = prev_state
    metrics["new_state"] = current_state

    validation["checkpoint_resolved"] = decision != "UNKNOWN"

    return metrics, validation


def _extract_step10(rel: str, abs_path: Path) -> tuple[dict, dict]:
    """Extract metrics for consolidation sub-steps.

    Since Step 10 writes many files, we log each sub-step individually.
    """
    metrics: dict[str, Any] = {}
    validation: dict[str, Any] = {}

    filename = Path(rel).name

    if filename.startswith("DOSSIER-"):
        metrics["substep"] = "10.1_dossier"
        metrics["dossier_path"] = rel
        metrics["file_size_bytes"] = abs_path.stat().st_size if abs_path.exists() else 0
        validation["has_dossier"] = abs_path.exists()

    elif filename in {"FILOSOFIAS.yaml", "MODELOS-MENTAIS.yaml", "HEURISTICAS.yaml",
                       "FRAMEWORKS.yaml", "METODOLOGIAS.yaml"}:
        metrics["substep"] = "10.3_dna_yaml"
        metrics["yaml_name"] = filename
        metrics["file_size_bytes"] = abs_path.stat().st_size if abs_path.exists() else 0
        validation["has_dna_yaml"] = abs_path.exists()

    elif filename in {"AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml"}:
        metrics["substep"] = "10.4_agent"
        metrics["agent_file"] = filename
        metrics["file_size_bytes"] = abs_path.stat().st_size if abs_path.exists() else 0
        validation["has_agent_file"] = abs_path.exists()

    elif "knowledge/external/sources/" in rel:
        metrics["substep"] = "10.2_sources"
        metrics["source_doc"] = filename
        validation["has_source_doc"] = abs_path.exists()

    return metrics, validation


# ---------------------------------------------------------------------------
# Main Hook Entry
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point. Reads hook input from stdin, processes, exits 0."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        event = json.loads(raw)
        tool_name = event.get("tool_name", "")
        tool_input = event.get("tool_input", {})

        # Only process Write and Edit
        if tool_name not in ("Write", "Edit"):
            sys.exit(0)

        file_path = tool_input.get("file_path", "")
        if not file_path:
            sys.exit(0)

        rel = _to_relative(file_path)
        abs_path = Path(file_path).resolve()

        # Match against artifact patterns
        match = _match_artifact(rel)
        if match is None:
            sys.exit(0)

        step, step_name = match

        # Detect slug
        slug = _detect_slug(rel)
        if not slug:
            slug = "unknown"

        # Special case: INSIGHTS-STATE.json can be Steps 5, 6, or 7
        if step == -1 and step_name == "_insights_detect":
            data = _read_json(abs_path)
            if data is None or not isinstance(data, dict):
                sys.exit(0)
            step, step_name = _detect_insights_step(data)

        # Special case: Step 9 -- only log if checkpoint was actually resolved
        if step == 9:
            data = _read_yaml(abs_path)
            if data is None or not isinstance(data, dict):
                sys.exit(0)
            # Only log if this is actually a checkpoint transition
            history = data.get("history", [])
            if not history:
                sys.exit(0)
            last = history[-1] if history else {}
            if last.get("from") != "identity_checkpoint":
                sys.exit(0)

        # Special case: Step 8 -- only VOICE-DNA.yaml, not other YAML files
        if step == 8 and "VOICE-DNA.yaml" not in rel:
            sys.exit(0)

        # Extract metrics based on step
        metrics: dict[str, Any] = {}
        validation: dict[str, Any] = {}

        if step == 3:
            data = _read_json(abs_path)
            if data is not None:
                metrics, validation = _extract_step3(data)

        elif step == 4:
            data = _read_json(abs_path)
            if data is not None:
                metrics, validation = _extract_step4(data)

        elif step == 5:
            data = _read_json(abs_path)
            if data is not None and isinstance(data, dict):
                metrics, validation = _extract_step5(data)

        elif step == 6:
            data = _read_json(abs_path)
            if data is not None and isinstance(data, dict):
                metrics, validation = _extract_step6(data)

        elif step == 7:
            data = _read_json(abs_path)
            if data is not None and isinstance(data, dict):
                metrics, validation = _extract_step7(data)

        elif step == 8:
            data = _read_yaml(abs_path)
            if data is not None and isinstance(data, dict):
                metrics, validation = _extract_step8(data)

        elif step == 9:
            data = _read_yaml(abs_path)
            if data is not None and isinstance(data, dict):
                metrics, validation = _extract_step9(data)

        elif step == 10:
            metrics, validation = _extract_step10(rel, abs_path)

        # Build and write log entry
        entry: dict[str, Any] = {
            "timestamp": _now_iso(),
            "step": step,
            "step_name": step_name,
            "slug": slug,
            "artifact_path": rel,
            "metrics": metrics,
            "validation": validation,
        }

        _append_jsonl(entry)

        # Emit feedback to LLM for visibility (optional)
        step_label = f"Step {step} ({step_name})"
        print(json.dumps({
            "continue": True,
            "feedback": f"[MCE Logger] {step_label} logged for {slug}"
        }))
        sys.exit(0)

    except Exception:
        # Never block pipeline execution
        print(json.dumps({"continue": True, "feedback": None}))
        sys.exit(0)


if __name__ == "__main__":
    main()
```

### 6.3 Register in settings.json

Add the new hook to the `PostToolUse` section, in the `"Write|Edit"` matcher group.
This group already contains `governance_auto_update.py`.

**Current state of the Write|Edit PostToolUse block in `.claude/settings.json`:**

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "python3 .claude/hooks/governance_auto_update.py",
      "timeout": 15000
    }
  ]
}
```

**After adding the new hook:**

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    {
      "type": "command",
      "command": "python3 .claude/hooks/governance_auto_update.py",
      "timeout": 15000
    },
    {
      "type": "command",
      "command": "python3 .claude/hooks/mce_step_logger.py",
      "timeout": 5000
    }
  ]
}
```

### 6.4 ROUTING Update

Add a new entry to `core/paths.py` ROUTING dictionary:

```python
# In ROUTING dict, add:
"mce_step_log": LOGS / "mce-step-logger.jsonl",
```

This registers the new log file in the project's path registry.

---

## 7. Human-Readable Log Generation

### 7.1 Progressive Fill Pattern

The MCE Pipeline Log Template (`core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md`)
has 12 sections. Each section starts as `[*] PENDENTE` and transitions to
`[@] COMPLETO` with real data when its step finishes.

The JSONL entries created by the new hook provide the data needed to fill sections
3 through 10 of this template.

### 7.2 Optional Log Regeneration

After appending a JSONL entry, the hook MAY regenerate the human-readable log. This
is OPTIONAL for the initial implementation but RECOMMENDED for future iterations.

**How regeneration would work:**

1. Read `logs/mce-step-logger.jsonl` and filter entries for the current slug.
2. Read the template from `core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md`.
3. For each step with a JSONL entry, fill the corresponding template section with
   real data from the `metrics` and `validation` fields.
4. Write the filled template to `logs/mce/{SLUG}/MCE-{TAG}.md`.

**Where the output goes:**

```
logs/mce/{SLUG}/MCE-{TAG}.md
```

Where `{TAG}` is derived from the meeting or source tag (e.g., `MEET-0097` or
`AH-BATCH-001`). The tag can be read from `metadata.yaml` or derived from the
slug and a sequence number.

### 7.3 Rendering Rules

1. Start from the top. Sections 1-2 are filled from `mce-orchestrate.jsonl` data.
2. Each step fills its section. When Step 3 JSONL entry appears, section 3 changes
   from `[*] PENDENTE` to `[@] COMPLETO`.
3. Never remove empty sections. Show them as `PENDENTE`.
4. The PIPELINE PROGRESS bar at the bottom updates to reflect completed steps.
5. Duration accumulates from `metrics.yaml` wall-clock data.

---

## 8. Testing Protocol

### 8.1 How to Verify

1. Choose a test slug with existing source files (or create a test slug with 3+
   small `.txt` files in `knowledge/external/inbox/{test-slug}/`).

2. Run the full pipeline:
   ```
   /pipeline-mce {test-slug}
   ```

3. After each step completes, verify JSONL entries appear in
   `logs/mce-step-logger.jsonl`:

   ```bash
   # Count entries for the test slug
   grep -c '"slug": "{test-slug}"' logs/mce-step-logger.jsonl

   # View the latest entry
   tail -1 logs/mce-step-logger.jsonl | python3 -m json.tool
   ```

### 8.2 Expected Entries Per Full Pipeline Run

A complete pipeline run (Steps 0-12) should produce the following entries in
`logs/mce-step-logger.jsonl`:

| Step | step_name | Expected Entries | Notes |
|------|-----------|-----------------|-------|
| 3 | `chunking` | 1 | One entry when CHUNKS-STATE.json is written |
| 4 | `entity_resolution` | 1 | One entry when CANONICAL-MAP.json is written |
| 5 | `insight_extraction` | 1 | One entry when INSIGHTS-STATE.json first gets insights |
| 6 | `mce_behavioral` | 1 | One entry when behavioral_patterns appears |
| 7 | `mce_identity` | 1 | One entry when value_hierarchy appears |
| 8 | `mce_voice` | 1 | One entry when VOICE-DNA.yaml is written |
| 9 | `identity_checkpoint` | 1 | One entry when pipeline_state.yaml transitions from checkpoint |
| 10 | `consolidation` | 5-12 | One entry per artifact file written (dossier, DNA YAMLs, agent files) |
| **TOTAL** | | **12-19** | Varies based on how many Step 10 artifacts are created |

Steps 0, 1, 2, 11, and 12 are NOT logged by this hook (they are already logged by
`orchestrate.py` and other deterministic scripts).

### 8.3 Validation Script

Create a validation script at `core/intelligence/validation/validate_mce_logs.py`:

```python
#!/usr/bin/env python3
"""Validate MCE step logger completeness for a given slug.

Usage:
    python3 -m core.intelligence.validation.validate_mce_logs alex-hormozi
"""

import json
import sys
from pathlib import Path

EXPECTED_STEPS = {3, 4, 5, 6, 7, 8, 9, 10}
LOG_PATH = Path("logs/mce-step-logger.jsonl")


def validate(slug: str) -> bool:
    """Check that all expected steps have at least one log entry."""
    if not LOG_PATH.exists():
        print(f"FAIL: {LOG_PATH} does not exist")
        return False

    found_steps: set[int] = set()
    entries = 0

    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("slug") != slug:
                continue
            entries += 1
            step = entry.get("step")
            if isinstance(step, int):
                found_steps.add(step)

    missing = EXPECTED_STEPS - found_steps
    print(f"\nMCE Step Logger Validation for '{slug}'")
    print(f"{'=' * 50}")
    print(f"Total entries found: {entries}")
    print(f"Steps covered: {sorted(found_steps)}")

    if missing:
        print(f"MISSING steps: {sorted(missing)}")
        for s in sorted(missing):
            step_names = {
                3: "chunking", 4: "entity_resolution",
                5: "insight_extraction", 6: "mce_behavioral",
                7: "mce_identity", 8: "mce_voice",
                9: "identity_checkpoint", 10: "consolidation",
            }
            print(f"  Step {s} ({step_names.get(s, '?')}): NO LOG ENTRY")
        print(f"\nRESULT: FAIL ({len(missing)} steps missing)")
        return False
    else:
        print(f"\nRESULT: PASS (all {len(EXPECTED_STEPS)} steps logged)")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m core.intelligence.validation.validate_mce_logs <slug>")
        sys.exit(1)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
```

---

## 9. File Manifest

### 9.1 Files the Developer MUST Create

| # | File | Purpose |
|---|------|---------|
| 1 | `.claude/hooks/mce_step_logger.py` | The main hook (PostToolUse, Write/Edit) |
| 2 | `core/intelligence/validation/validate_mce_logs.py` | Validation script for log completeness |

### 9.2 Files the Developer MUST Modify

| # | File | Change |
|---|------|--------|
| 1 | `.claude/settings.json` | Add `mce_step_logger.py` to PostToolUse Write/Edit matcher |
| 2 | `core/paths.py` | Add `"mce_step_log"` entry to ROUTING dict |

### 9.3 Files the Developer MUST Read (But NOT Modify)

| # | File | Why |
|---|------|-----|
| 1 | `core/intelligence/pipeline/mce/orchestrate.py` | Understand `_append_jsonl()` pattern and slug detection |
| 2 | `core/intelligence/pipeline/mce/metrics.py` | Understand timing data schema |
| 3 | `core/intelligence/pipeline/mce/state_machine.py` | Understand FSM states and transitions |
| 4 | `core/intelligence/pipeline/mce/metadata_manager.py` | Understand phase tracking |
| 5 | `.claude/hooks/pipeline_checkpoint.py` | Reference for PostToolUse hook structure |
| 6 | `.claude/hooks/governance_auto_update.py` | Reference for Write/Edit watch-and-trigger pattern |
| 7 | `.claude/skills/pipeline-mce/SKILL.md` | Understand Steps 3-10 execution flow |
| 8 | `core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md` | Understand human-readable log format |
| 9 | `docs/architecture/pipeline-logging-guide.md` | System overview and existing log inventory |

### 9.4 Dependencies and Constraints

| Constraint | Detail |
|-----------|--------|
| Python version | 3.10+ (project uses `from __future__ import annotations`) |
| Allowed imports | `json`, `os`, `sys`, `datetime`, `pathlib`, `typing` (all stdlib) |
| Allowed external | `yaml` (PyYAML) -- already installed, required for VOICE-DNA.yaml parsing |
| Forbidden | `requests`, `httpx`, `aiohttp`, `openai`, `anthropic`, or any other package |
| Exit codes | 0 = success, 1 = warning (feedback shown to LLM), 2 = block (NEVER use) |
| Timeout | 5000ms (5 seconds) -- hook must complete within this window |
| Side effects | Append to `logs/mce-step-logger.jsonl` only. NEVER modify artifact files. |
| Error handling | Swallow all exceptions. Logging must NEVER block pipeline execution. |

### 9.5 Runtime Files Created by the Hook

| File | Created When | Retention |
|------|-------------|-----------|
| `logs/mce-step-logger.jsonl` | First artifact write detected | Permanent (append-only) |

---

## Appendix A: Complete Step-to-Artifact Mapping

```
Step 0  (DETECT)     -> (no artifact)
Step 1  (INGEST)     -> logs/scope-classifier.jsonl, logs/smart-router.jsonl
Step 2  (BATCH)      -> logs/batch-auto-creator.jsonl
Step 3  (CHUNK)      -> artifacts/chunks/CHUNKS-STATE.json               <-- NEW LOGGING
Step 4  (ENTITY)     -> artifacts/canonical/CANONICAL-MAP.json           <-- NEW LOGGING
Step 5  (INSIGHT)    -> artifacts/insights/INSIGHTS-STATE.json           <-- NEW LOGGING
Step 6  (BEHAVIORAL) -> artifacts/insights/INSIGHTS-STATE.json           <-- NEW LOGGING
Step 7  (IDENTITY)   -> artifacts/insights/INSIGHTS-STATE.json           <-- NEW LOGGING
Step 8  (VOICE)      -> knowledge/external/dna/persons/*/VOICE-DNA.yaml  <-- NEW LOGGING
Step 9  (CHECKPOINT) -> .claude/mission-control/mce/*/pipeline_state.yaml<-- NEW LOGGING
Step 10 (COMPILE)    -> dossiers, DNA YAMLs, sources, agent files        <-- NEW LOGGING
Step 11 (FINALIZE)   -> logs/memory-enricher.jsonl, logs/mce-metrics.jsonl
Step 12 (REPORT)     -> logs/mce/{SLUG}/MCE-{TAG}.md
```

---

## Appendix B: INSIGHTS-STATE.json Step Detection Decision Tree

Since Steps 5, 6, and 7 all write to the same file (`INSIGHTS-STATE.json`), the hook
must differentiate which step just executed. This decision tree is authoritative:

```
INSIGHTS-STATE.json written
├── Has `value_hierarchy` field?
│   └── YES -> Step 7 (mce_identity)
├── Has `behavioral_patterns` field?
│   └── YES -> Step 6 (mce_behavioral)
└── Has `persons` with `insights` arrays?
    └── YES -> Step 5 (insight_extraction)
```

Check in order: Step 7 first (most fields present), then Step 6, then Step 5.
This works because each successive step ADDS fields to the same file -- the file
only gains the `value_hierarchy` field after Step 7 runs, so its presence is an
unambiguous signal.

**Edge case:** If the hook fires multiple times for the same step (e.g., the LLM
writes to INSIGHTS-STATE.json twice during Step 5), duplicate entries will appear
in the JSONL log. This is acceptable -- downstream consumers can dedup by
`(slug, step, timestamp)`.

---

## Appendix C: FSM State-to-Step Mapping

For cross-referencing with `pipeline_state.yaml`:

| FSM State | Corresponding Steps |
|-----------|-------------------|
| `init` | Step 0 (detect) |
| `chunking` | Steps 1-3 |
| `entities` | Step 4 |
| `knowledge_extraction` | Step 5 |
| `mce_extraction` | Steps 6-7 |
| `identity_checkpoint` | Step 9 |
| `consolidation` | Step 10 |
| `agent_generation` | Step 10.4 |
| `validation` | Step 12 |
| `complete` | Pipeline done |
| `failed` | Pipeline error |
| `paused` | Pipeline suspended |

---

*End of SPEC-MCE-REALTIME-LOGGING.md*
*Template: core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md*
*Related: docs/architecture/pipeline-logging-guide.md*
