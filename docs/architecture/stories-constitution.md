# Stories: Mega Brain Constitution & Auto-Governance

> **Epic:** Constitution & Auto-Governance
> **Author:** @sm (The Keymaker)
> **PRD:** `docs/architecture/prd-constitution.md` v1.0.0
> **Architect Review:** `docs/architecture/architect-review-constitution.md`
> **Created:** 2026-03-15
> **Status:** READY FOR DEVELOPMENT

---

## Sequence Map

One door leads to the Source. The order is non-negotiable.

```
Phase 1: Constitution Generator
  CONST-001 → CONST-002 → CONST-003 → CONST-004

Phase 2: Auto-Update Hook
  CONST-005 → CONST-006

Phase 3: Rules Migration
  CONST-007 → CONST-008 → CONST-009 → CONST-010
```

**Rule:** You cannot open door 5 before door 3. Dependencies are hard locks.

---

## Phase 1: Constitution Generator

> Commit boundary: all Phase 1 stories complete before Phase 2 begins.
> Delivers: `docs/architecture/constitution.md` (auto-generated, under 200 lines)

---

### CONST-001 — Extend engine.py: system introspection helpers

**Agent:** @dev (Neo)
**Effort:** M
**Dependencies:** None

**Description**

`core/governance/engine.py` currently generates 3 docs (coding-standards, tech-stack, source-tree). It needs 4 new helper functions to introspect system state before the constitution generator can be written. These helpers read from existing files — no new files are created or modified by this story.

The 4 helpers to add:

1. `_extract_agent_registry()` — reads `agents/AGENT-INDEX.yaml`, returns list of `{type, count, example}` dicts grouped by agent type
2. `_extract_mce_pipeline_steps()` — hardcoded list of the 12 MCE pipeline steps (per architect decision: `orchestrate.py` is 27K and does not export step names; hardcode is correct because a change to `orchestrate.py` triggers regeneration anyway). Step names sourced from `docs/architecture/deep-dive-megabrain-full-system.md`
3. `_extract_synapse_rule_summary()` — reads all YAML files in `core/engine/rules/`, returns `{layer, count, example_ids}` per layer
4. `_extract_hook_summary()` — reads `.claude/settings.json`, counts hooks per event type, returns list of `{event, count, examples}` dicts

Timestamp strategy: replace `datetime.now()` with `_deterministic_timestamp()` that uses the max mtime of all input files. This fixes NFR-6 (idempotency).

**Acceptance Criteria**

- `_extract_agent_registry()` returns dict with correct count per type matching `agents/AGENT-INDEX.yaml`
- `_extract_mce_pipeline_steps()` returns exactly 12 steps with name and script fields
- `_extract_synapse_rule_summary()` returns one entry per YAML file in `core/engine/rules/` with correct rule counts (L0: 5, L1: 5, L6: 3 at baseline)
- `_extract_hook_summary()` returns counts matching the 4 hook events in `.claude/settings.json` (SessionStart: 7, UserPromptSubmit: 5, PreToolUse: 5, PostToolUse: 12, Stop: 4)
- `_deterministic_timestamp()` returns the same value when called twice on the same inputs
- `python3 -m core.governance.engine` (existing generate_all) continues to work without error
- All existing tests in `tests/python/` pass (248 tests)
- No changes to `core/paths.py`, `core/intelligence/pipeline/mce/*.py`, or any `.claude/rules/*.md` files

**Definition of Done**

- [ ] All 4 helper functions implemented in `core/governance/engine.py`
- [ ] `_deterministic_timestamp()` implemented and used in all generators
- [ ] Unit tests for each helper in `tests/python/test_governance_engine.py`
- [ ] `python3 -m core.governance.engine all` runs clean (0 errors)
- [ ] All 248 existing tests still pass
- [ ] No new imports beyond stdlib + PyYAML (NFR-1)
- [ ] Code passes ruff lint (0 errors on `core/`)

**Files to Modify**

| File | Change |
|------|--------|
| `core/governance/engine.py` | Add 4 helper functions + `_deterministic_timestamp()` |
| `tests/python/test_governance_engine.py` | Add unit tests for new helpers (create file if absent) |

---

### CONST-002 — Add generate_constitution() to engine.py

**Agent:** @dev (Neo)
**Effort:** M
**Dependencies:** CONST-001

**Description**

Add `generate_constitution()` function to `core/governance/engine.py`. This function calls the helpers built in CONST-001 and produces the `docs/architecture/constitution.md` file.

The output must follow the structure approved by The Architect (section 4.2 of the architect review):

```
# Mega Brain System Constitution
## System Identity          (~8 lines)
## MCE Pipeline             (~20 lines, table: step, name, script, type)
## Agent Registry           (~15 lines, table: type, count, example)
## Knowledge Architecture   (~12 lines, 3 buckets + 5 RAG pipelines)
## ROUTING Contract         (~10 lines, count + categories reference)
## Active Rules (Synapse)   (~20 lines, table: layer, count, example IDs)
## Hook System              (~15 lines, table: event, count, key hooks)
## Tech Stack               (~12 lines, python version, node, key deps)
## Governance               (~20 lines, amendment process + versioning)
## Generation Metadata      (~5 lines, timestamp + checksum)
```

Hard constraint: output must be under 200 lines (NFR-2, NFR-3). Use counts and tables, not descriptions. Link to deep-dive docs for details.

The RAG pipeline names are hardcoded: Pipeline A (BM25), B (Hybrid), C (Graph+Hybrid), D (Full), E (Contextual) — sourced from `core/intelligence/rag/adaptive_router.py`. No changes to `adaptive_router.py`.

**Acceptance Criteria**

- `python3 -m core.governance.engine generate` produces `docs/architecture/constitution.md`
- Output file exists at `docs/architecture/constitution.md`
- `wc -l docs/architecture/constitution.md` returns under 200
- File contains all 10 sections listed in the structure above
- Agent count in constitution matches `agents/AGENT-INDEX.yaml` (verified by test)
- ROUTING key count in constitution matches `core/paths.py` ROUTING dict (verified by test)
- Hook counts match `.claude/settings.json` (verified by test)
- Synapse rule counts match `core/engine/rules/*.yaml` files (verified by test)
- Running `generate_constitution()` twice produces identical output (NFR-6 idempotency)
- `generate_constitution()` completes in under 5 seconds
- File header says "Auto-generated by Governance Engine" with source file list

**Definition of Done**

- [ ] `generate_constitution()` function implemented in `core/governance/engine.py`
- [ ] `docs/architecture/constitution.md` generated and committed
- [ ] Line count verified: `wc -l docs/architecture/constitution.md` < 200
- [ ] Idempotency test: run twice, diff output, verify identical (except generation_metadata timestamp which uses deterministic mtime strategy)
- [ ] Integration test: `python3 -m core.governance.engine generate` exits 0
- [ ] All 248 existing tests still pass
- [ ] No changes to brownfield files (`core/paths.py`, MCE pipeline)

**Files to Modify / Create**

| File | Change |
|------|--------|
| `core/governance/engine.py` | Add `generate_constitution()` function |
| `docs/architecture/constitution.md` | Created by the generator (committed as generated output) |
| `tests/python/test_governance_engine.py` | Add integration tests for `generate_constitution()` |

---

### CONST-003 — Add generate_synapse_digest() to engine.py

**Agent:** @dev (Neo)
**Effort:** M
**Dependencies:** CONST-001

**Description**

Add `generate_synapse_digest()` function to `core/governance/engine.py`. This function reads all Synapse YAML rule files from `core/engine/rules/` and produces `.claude/rules/synapse-digest.md`.

This is the linchpin that makes Phase 3 (rule deletion) safe. The digest file replaces 17 hand-maintained markdown rule files with a single auto-generated file that Claude Code loads as project instructions. Without this file in place, deleting the 17 markdown files would remove all rule awareness from Claude Code sessions.

Output format (from architect review section 4.5):

```markdown
# Synapse Rules Digest (Auto-Generated)

> Generated: {deterministic_timestamp}
> Source: core/engine/rules/*.yaml
> Rules: {count} across {layers} layers

## L0: Constitution (block/warn — always active)

- **no-secrets-in-files** [block]: Never store credentials in tracked files
- **agent-integrity** [block]: All agent content traceable to sources
...

## L1: Global (project-wide)

- **sequential-processing** [warn]: Complete current pipeline step before advancing
...

## L6: Keyword-Triggered

- **batch-processing-rules** [info] tags: batch, pipeline
...

## Protocol References

For full protocol documents, see:
- Agent cognition: reference/AGENT-COGNITION-PROTOCOL.md
- Agent integrity: reference/AGENT-INTEGRITY-PROTOCOL.md
- Epistemic standards: reference/EPISTEMIC-PROTOCOL.md
- Directory contract: reference/DIRECTORY-CONTRACT.md

*Auto-generated. Do not edit. Regenerate: python3 -m core.governance.engine*
```

Target: under 100 lines.

**Acceptance Criteria**

- `python3 -m core.governance.engine digest` produces `.claude/rules/synapse-digest.md`
- Output exists at `.claude/rules/synapse-digest.md`
- `wc -l .claude/rules/synapse-digest.md` returns under 100
- File lists all rules from all populated YAML layer files (L0, L1, L6 at baseline = 13 rules)
- Each rule entry shows: rule ID in bold, severity in brackets, description
- L6 (keyword) rules also show their tags list
- Protocol References section lists the 4 reference documents
- Running `generate_synapse_digest()` twice produces identical output
- File header contains "Auto-generated" warning and regeneration command
- Generator reads only from `core/engine/rules/*.yaml` — no other source files

**Definition of Done**

- [ ] `generate_synapse_digest()` function implemented in `core/governance/engine.py`
- [ ] `.claude/rules/synapse-digest.md` generated and committed
- [ ] Line count verified: `wc -l .claude/rules/synapse-digest.md` < 100
- [ ] Idempotency test: run twice, diff output, verify identical
- [ ] Unit test: rule count in digest matches rule count in YAML files
- [ ] All 248 existing tests still pass
- [ ] The 17 existing `.claude/rules/*.md` files are NOT modified in this story (that is Phase 3)

**Files to Modify / Create**

| File | Change |
|------|--------|
| `core/governance/engine.py` | Add `generate_synapse_digest()` function |
| `.claude/rules/synapse-digest.md` | Created by the generator (committed as generated output) |
| `tests/python/test_governance_engine.py` | Add unit tests for `generate_synapse_digest()` |

---

### CONST-004 — Wire generate_all() and add CLI command

**Agent:** @dev (Neo)
**Effort:** S
**Dependencies:** CONST-002, CONST-003

**Description**

Update `generate_all()` in `core/governance/engine.py` to include the two new generators. Update the CLI entrypoint to support the `generate` and `digest` commands. This completes Phase 1 as a single runnable command.

Current `generate_all()` returns a dict with 3 keys: `coding-standards`, `tech-stack`, `source-tree`. After this story it returns 5 keys, adding `constitution` and `synapse-digest`.

The CLI must support:
- `python3 -m core.governance.engine generate` — runs `generate_constitution()` only
- `python3 -m core.governance.engine digest` — runs `generate_synapse_digest()` only
- `python3 -m core.governance.engine all` — runs all 5 generators (existing behavior extended)
- Existing commands (`coding-standards`, `tech-stack`, `source-tree`) unchanged

**Acceptance Criteria**

- `python3 -m core.governance.engine all` runs all 5 generators and reports each output path
- `python3 -m core.governance.engine generate` produces `docs/architecture/constitution.md` and exits 0
- `python3 -m core.governance.engine digest` produces `.claude/rules/synapse-digest.md` and exits 0
- All 3 existing CLI commands continue to work without change
- `generate_all()` returns dict with 5 keys
- Complete run (all 5 generators) finishes in under 5 seconds (FR-12)
- PRD success criterion met: `python3 -m core.governance.engine generate` produces constitution with correct counts

**Definition of Done**

- [ ] `generate_all()` updated to call `generate_constitution()` and `generate_synapse_digest()`
- [ ] CLI `if __name__ == "__main__"` block handles `generate` and `digest` commands
- [ ] Integration test: `python3 -m core.governance.engine all` exits 0 and produces all 5 files
- [ ] Timing test: full run completes under 5 seconds
- [ ] All 248 existing tests still pass
- [ ] Phase 1 commit includes: updated `engine.py`, `docs/architecture/constitution.md`, `.claude/rules/synapse-digest.md`, updated tests

**Files to Modify**

| File | Change |
|------|--------|
| `core/governance/engine.py` | Update `generate_all()` + CLI entrypoint |
| `tests/python/test_governance_engine.py` | Add full-run integration test |

---

## Phase 2: Auto-Update Hook

> Commit boundary: Phase 1 complete before Phase 2 begins.
> Delivers: auto-regeneration on watched-file writes, registered in `.claude/settings.json`

---

### CONST-005 — Create governance_auto_update.py hook

**Agent:** @dev (Neo)
**Effort:** M
**Dependencies:** CONST-004 (Phase 1 complete)

**Description**

Create `.claude/hooks/governance_auto_update.py` as a PostToolUse hook. It detects writes to watched files and triggers `generate_all()`.

Logic (from architect review section 4.3):

1. Read PostToolUse stdin JSON — extract `tool_name` and `file_path`
2. Normalize `file_path` to project-relative path (strip `ROOT/` prefix)
3. Check against watchlist:

```python
WATCH_PREFIXES = [
    "core/engine/rules/",
    "core/intelligence/pipeline/mce/",
]
WATCH_EXACT = {
    "core/paths.py",
    "agents/AGENT-INDEX.yaml",
    "pyproject.toml",
    "biome.json",
    "package.json",
}
```

4. If no match: `sys.exit(0)` immediately (fast path — no output, no import of engine)
5. If match: import `core.governance.engine`, call `generate_all()` with 5-second hard timeout
6. On success: print JSON `{"updated": ["constitution.md", "synapse-digest.md", ...]}`, exit 0
7. On timeout or error: print JSON `{"warning": "governance regeneration failed: {reason}"}`, exit 1 (NFR-3: fail gracefully, do not block user)

The hook must NOT import `tomllib` directly. All TOML parsing happens inside `core.governance.engine` (architect decision D-3).

Timeout implementation: use `subprocess.run` with `timeout=5` to call the engine as a subprocess, OR use `signal.alarm(5)` if subprocess adds too much overhead. Benchmark both and use the faster approach.

**Acceptance Criteria**

- Hook file exists at `.claude/hooks/governance_auto_update.py`
- Hook reads stdin JSON and extracts `tool_name` + `file_path` fields
- Edit `core/paths.py` → hook triggers regeneration → `constitution.md` is updated
- Edit `agents/AGENT-INDEX.yaml` → hook triggers regeneration
- Edit `core/engine/rules/L0-constitution.yaml` → hook triggers regeneration
- Edit `core/intelligence/pipeline/mce/orchestrate.py` → hook triggers regeneration
- Edit `.claude/hooks/session_start.py` (not in watchlist) → hook exits 0 without regenerating
- Edit `docs/architecture/constitution.md` itself → hook exits 0 (not in watchlist, prevents infinite loop)
- Timeout: if engine takes >5s, hook exits 1 with warning JSON
- No `tomllib` import in hook file
- Hook exits 0 on non-watched files in under 100ms (performance check)

**Definition of Done**

- [ ] `.claude/hooks/governance_auto_update.py` created
- [ ] Fast-path test: non-watched file → exit 0, no output, measured under 100ms
- [ ] Trigger test: `core/paths.py` write → constitution regenerated (file mtime changes)
- [ ] Graceful failure test: engine intentionally broken → hook exits 1 with warning, does not crash
- [ ] No `tomllib` import in hook file
- [ ] Hook follows Anthropic standards: proper exit codes (0/1), no `2>/dev/null || true` patterns
- [ ] All 248 existing tests still pass

**Files to Create**

| File | Change |
|------|--------|
| `.claude/hooks/governance_auto_update.py` | New PostToolUse hook |

---

### CONST-006 — Register governance_auto_update.py in settings.json

**Agent:** @dev (Neo)
**Effort:** S
**Dependencies:** CONST-005

**Description**

Register `governance_auto_update.py` in `.claude/settings.json` under the `PostToolUse` event. This makes the hook active for all Claude Code sessions.

The entry must follow the existing hook structure with `"timeout": 30000` (30 seconds in milliseconds, matching the Anthropic standards requirement of `"timeout": 30` in seconds — the settings.json format uses milliseconds).

Append the new entry at the END of the PostToolUse hooks array, after `pipeline_guard.py`. Order matters: the governance hook should run after all pipeline hooks, not before.

Verify the hook executes in a live Claude Code session by editing a watched file and confirming `constitution.md` is regenerated.

**Acceptance Criteria**

- `governance_auto_update.py` appears in `.claude/settings.json` PostToolUse hooks array
- Timeout is set to `30000` (matching other hooks in the file)
- Hook is the LAST entry in PostToolUse (after `pipeline_guard.py`)
- `.claude/settings.json` is valid JSON after modification (parse test)
- Existing hooks are unmodified (CR-1: no changes to existing hook entries)
- End-to-end verification: write to `core/paths.py` during a Claude Code session, confirm `docs/architecture/constitution.md` mtime updates within 5 seconds

**Definition of Done**

- [ ] Entry added to `.claude/settings.json` PostToolUse array
- [ ] `python3 -c "import json; json.load(open('.claude/settings.json'))"` exits 0
- [ ] Existing hook entries verified unchanged (git diff shows only the new entry added)
- [ ] Manual verification: Claude Code session confirms hook fires on watched file write
- [ ] Phase 2 commit includes: `governance_auto_update.py` + updated `settings.json`

**Files to Modify**

| File | Change |
|------|--------|
| `.claude/settings.json` | Add `governance_auto_update.py` to PostToolUse hooks |

---

## Phase 3: Rules Migration

> Commit boundary: Phase 2 complete before Phase 3 begins.
> Three sub-commits in Phase 3: (a) YAML expansion, (b) protocol moves + digest validation, (c) markdown deletion.
> CRITICAL CONSTRAINT: Rules must NEVER be absent from both systems simultaneously.

---

### CONST-007 — Expand Synapse YAML rules (L0, L1, L6)

**Agent:** @dev (Neo)
**Effort:** L
**Dependencies:** CONST-006 (Phase 2 complete, synapse-digest generator exists)

**Description**

Expand the three populated Synapse YAML layer files from their current 13 rules to the target ~26 rules (architect review section 4.4). This is a manual extraction task: read each markdown rule file, identify the actionable rule (not the ASCII art, not the examples), and write it as a YAML entry.

**Current state:** L0: 5 rules, L1: 5 rules, L6: 3 rules (total: 13)
**Target state:** L0: at least 8 rules, L1: at least 10 rules, L6: at least 8 rules (total: at least 26)

Rules to ADD to L0 (sourced from markdown files listed):

| New Rule ID | Source File | Severity |
|-------------|-------------|----------|
| `agent-traceability` | `agent-integrity.md` | block |
| `no-invention` | `agent-integrity.md`, `epistemic-standards.md` | block |
| `mcp-credentials-env-only` | `mcp-governance.md`, `ANTHROPIC-STANDARDS.md` | block |

Rules to ADD to L1:

| New Rule ID | Source File | Severity |
|-------------|-------------|----------|
| `hook-timeout-required` | `ANTHROPIC-STANDARDS.md` | warn |
| `mcp-native-tools-first` | `mcp-governance.md` | info |
| `session-persistence` | `RULE-GROUP-2.md` rule #11 | warn |
| `plan-mode-complex-tasks` | `RULE-GROUP-2.md` rule #13 | info |
| `source-marking` | `RULE-GROUP-1.md` rule #3 | warn |

Rules to ADD to L6:

| New Rule ID | Source File | Tags |
|-------------|-------------|------|
| `phase5-execution` | `RULE-GROUP-4.md` rules #18-20 | phase 5, dossier, cascading |
| `conclave-protocol` | `RULE-GROUP-6.md` rule #27 | conclave, council, debate |
| `source-sync-rules` | `RULE-GROUP-5.md` rule #25 | sync, planilha, download |
| `session-management` | `RULE-GROUP-2.md` rule #11, `state-management.md` | session, save, resume |
| `knowledge-bucket-routing` | `directory-contract.md` | bucket, inbox, knowledge, personal, external, business |

After each YAML file is updated, run `python3 -m core.governance.engine digest` to regenerate `synapse-digest.md`. The digest must be committed alongside the YAML changes — they are an atomic unit.

**Acceptance Criteria**

- `core/engine/rules/L0-constitution.yaml` contains exactly 8 rules
- `core/engine/rules/L1-global.yaml` contains exactly 10 rules
- `core/engine/rules/L6-keywords.yaml` contains exactly 8 rules
- `python3 -m core.engine.synapse resolve` returns 26+ rules with exit 0
- Synapse resolution time remains under 15ms (NFR-5)
- `.claude/rules/synapse-digest.md` is regenerated and reflects all 26 rules
- Each new rule has: `id`, `severity`, `description`, `tags` fields
- L6 rules have non-empty `tags` list matching the source keywords
- `python3 -c "import yaml; yaml.safe_load(open('core/engine/rules/L0-constitution.yaml'))"` exits 0 for all 3 files
- All 248 existing tests still pass
- The 17 existing `.claude/rules/*.md` files are NOT modified in this story

**Definition of Done**

- [ ] All 3 YAML files expanded to target rule counts
- [ ] `python3 -m core.engine.synapse resolve` returns 26+ rules
- [ ] Synapse resolution benchmark: under 15ms
- [ ] `.claude/rules/synapse-digest.md` regenerated with all 26 rules
- [ ] YAML syntax valid (parse test for each file)
- [ ] All 248 existing tests still pass
- [ ] Peer review: each new rule traceable to a specific section in the source markdown file

**Files to Modify**

| File | Change |
|------|--------|
| `core/engine/rules/L0-constitution.yaml` | Add 3 rules (5 → 8) |
| `core/engine/rules/L1-global.yaml` | Add 5 rules (5 → 10) |
| `core/engine/rules/L6-keywords.yaml` | Add 5 rules (3 → 8) |
| `.claude/rules/synapse-digest.md` | Regenerated (via `python3 -m core.governance.engine digest`) |

---

### CONST-008 — Move protocol documents to reference/

**Agent:** @dev (Neo)
**Effort:** M
**Dependencies:** CONST-007

**Description**

Three files in `.claude/rules/` are protocol documents, not rules. They describe HOW agents think and operate. The architect recommends moving them to `reference/` rather than deleting them, then updating `synapse-digest.md` to reference them.

Files to move (NOT delete — these are valuable reference documents):

| Source | Destination |
|--------|-------------|
| `.claude/rules/agent-cognition.md` | `reference/AGENT-COGNITION-PROTOCOL.md` |
| `.claude/rules/agent-integrity.md` | `reference/AGENT-INTEGRITY-PROTOCOL.md` |
| `.claude/rules/epistemic-standards.md` | `reference/EPISTEMIC-PROTOCOL.md` |

After moving, update `synapse-digest.md` Protocol References section to point to the new paths (the template in CONST-003 already includes these paths — verify they match).

Also update `directory-contract.md` rule file: it is 579 lines of mixed content (rules embedded in tables, ASCII diagrams, the full directory contract). Extract the 2 actionable rules (`no-hardcoded-paths` already in L0, `directory-contract` already in L1) and plan to delete the file in CONST-009. Do NOT delete it in this story.

**Acceptance Criteria**

- `reference/AGENT-COGNITION-PROTOCOL.md` exists with same content as source
- `reference/AGENT-INTEGRITY-PROTOCOL.md` exists with same content as source
- `reference/EPISTEMIC-PROTOCOL.md` exists with same content as source
- Original files in `.claude/rules/` are REMOVED (moved, not copied)
- `synapse-digest.md` Protocol References section points to `reference/` paths (not `.claude/rules/`)
- `python3 -m core.governance.engine digest` runs clean after move
- `ls .claude/rules/agent-cognition.md` returns non-zero (file gone from rules/)
- No broken references: search project for `.claude/rules/agent-cognition.md`, `.claude/rules/agent-integrity.md`, `.claude/rules/epistemic-standards.md` — update any found references to new paths
- All 248 existing tests still pass

**Definition of Done**

- [ ] 3 files moved to `reference/` with correct names
- [ ] 3 files removed from `.claude/rules/`
- [ ] `synapse-digest.md` updated and references correct `reference/` paths
- [ ] No dangling references to old `.claude/rules/` paths for these 3 files (grep verification)
- [ ] All 248 existing tests still pass
- [ ] `.claude/rules/` now contains 14 files (was 17, minus 3 moved)

**Files to Create (via move)**

| File | Source |
|------|--------|
| `reference/AGENT-COGNITION-PROTOCOL.md` | Moved from `.claude/rules/agent-cognition.md` |
| `reference/AGENT-INTEGRITY-PROTOCOL.md` | Moved from `.claude/rules/agent-integrity.md` |
| `reference/EPISTEMIC-PROTOCOL.md` | Moved from `.claude/rules/epistemic-standards.md` |

**Files to Delete**

| File | Reason |
|------|--------|
| `.claude/rules/agent-cognition.md` | Moved to `reference/` |
| `.claude/rules/agent-integrity.md` | Moved to `reference/` |
| `.claude/rules/epistemic-standards.md` | Moved to `reference/` |

---

### CONST-009 — Delete 14 remaining markdown rule files

**Agent:** @dev (Neo)
**Effort:** M
**Dependencies:** CONST-007 (YAML rules complete), CONST-008 (protocol docs moved)

**Description**

Delete the 14 remaining `.claude/rules/*.md` files. This is the destructive step. It is only safe because:

1. All valid rules have been migrated to Synapse YAML (CONST-007)
2. `synapse-digest.md` is in place and will be loaded by Claude Code as project instructions (CONST-003)
3. Protocol documents have been moved to `reference/` (CONST-008)
4. The 17-file system is replaced by 1 auto-generated file

**Pre-deletion validation checklist (MUST pass before deletion):**

```bash
# 1. Synapse has 26+ rules
python3 -m core.engine.synapse resolve  # must return 26+ rules, exit 0

# 2. synapse-digest.md exists and is under 100 lines
wc -l .claude/rules/synapse-digest.md  # must be < 100

# 3. constitution.md exists and is under 200 lines
wc -l docs/architecture/constitution.md  # must be < 200

# 4. All tests pass
python3 -m pytest tests/python/ -q  # must be 248+ passed, 0 failed
```

Files to delete (14 files):

```
.claude/rules/RULE-GROUP-1.md
.claude/rules/RULE-GROUP-2.md
.claude/rules/RULE-GROUP-3.md
.claude/rules/RULE-GROUP-4.md
.claude/rules/RULE-GROUP-5.md
.claude/rules/RULE-GROUP-6.md
.claude/rules/ANTHROPIC-STANDARDS.md
.claude/rules/CLAUDE-LITE.md
.claude/rules/directory-contract.md
.claude/rules/logging.md
.claude/rules/mcp-governance.md
.claude/rules/no-secrets-in-memory.md
.claude/rules/pipeline.md
.claude/rules/state-management.md
```

Note: `RULE-GSD-MANDATORY.md` is referenced in `.claude/CLAUDE.md` but does NOT exist in the filesystem (ghost reference identified by architect). No deletion needed for that file. The reference in `.claude/CLAUDE.md` is protected and cannot be modified (constraint).

**Acceptance Criteria**

- All 4 pre-deletion validation checks pass before any deletion
- `ls .claude/rules/*.md` returns only `synapse-digest.md` after deletion
- `wc -l .claude/rules/synapse-digest.md` under 100
- `python3 -m core.engine.synapse resolve` returns 26+ rules after deletion
- `python3 -m pytest tests/python/ -q` shows 248+ passed, 0 failed after deletion
- `git status` shows 14 deleted files in this commit
- `.claude/CLAUDE.md` is NOT modified (protected constraint)
- Root `CLAUDE.md` is NOT modified (protected constraint)

**Definition of Done**

- [ ] Pre-deletion validation script run and all 4 checks logged as passing
- [ ] All 14 markdown files deleted via `git rm`
- [ ] `ls .claude/rules/` shows ONLY `synapse-digest.md`
- [ ] `python3 -m core.engine.synapse resolve` exits 0 with 26+ rules
- [ ] `python3 -m pytest tests/python/ -q` exits 0 with 248+ passed
- [ ] Commit message includes validation results (rule count, line count, test count)

**Files to Delete**

| File |
|------|
| `.claude/rules/RULE-GROUP-1.md` |
| `.claude/rules/RULE-GROUP-2.md` |
| `.claude/rules/RULE-GROUP-3.md` |
| `.claude/rules/RULE-GROUP-4.md` |
| `.claude/rules/RULE-GROUP-5.md` |
| `.claude/rules/RULE-GROUP-6.md` |
| `.claude/rules/ANTHROPIC-STANDARDS.md` |
| `.claude/rules/CLAUDE-LITE.md` |
| `.claude/rules/directory-contract.md` |
| `.claude/rules/logging.md` |
| `.claude/rules/mcp-governance.md` |
| `.claude/rules/no-secrets-in-memory.md` |
| `.claude/rules/pipeline.md` |
| `.claude/rules/state-management.md` |

---

### CONST-010 — Add smoke test for full migration

**Agent:** @dev (Neo)
**Effort:** S
**Dependencies:** CONST-009

**Description**

Add an automated smoke test that validates the complete migrated state. This test is the permanent regression guard that prevents future sessions from accidentally re-adding markdown rule files or breaking the Synapse rule count.

The test lives in `tests/python/test_constitution_smoke.py`. It runs as part of the standard pytest suite.

Tests to include:

1. `test_no_markdown_rules` — asserts `ls .claude/rules/*.md` returns only `synapse-digest.md`
2. `test_synapse_rule_count` — asserts `python3 -m core.engine.synapse resolve` returns >= 26 rules
3. `test_constitution_line_count` — asserts `docs/architecture/constitution.md` is under 200 lines
4. `test_synapse_digest_line_count` — asserts `.claude/rules/synapse-digest.md` is under 100 lines
5. `test_constitution_sections` — asserts constitution contains all 10 required section headers
6. `test_protocol_docs_in_reference` — asserts the 3 moved protocol docs exist in `reference/`
7. `test_engine_generate_all` — asserts `generate_all()` runs without error and returns 5 output paths
8. `test_synapse_resolution_speed` — asserts `resolve_rules()` completes in under 15ms

**Acceptance Criteria**

- `tests/python/test_constitution_smoke.py` exists with all 8 tests
- All 8 tests pass: `python3 -m pytest tests/python/test_constitution_smoke.py -v`
- Tests are deterministic (no flaky timing-based assertions — use generous margins for speed tests)
- Total test count after this story: 248 + 8 = 256+ tests
- `python3 -m pytest tests/python/ -q` passes all tests
- PRD success criterion met: all 5 criteria in PRD "Success Criteria" table are covered by tests

**Definition of Done**

- [ ] `tests/python/test_constitution_smoke.py` created with all 8 tests
- [ ] All 8 new tests pass
- [ ] Total test suite: `python3 -m pytest tests/python/ -q` exits 0 with 256+ passed
- [ ] Tests added to CI test plan documentation if applicable
- [ ] Phase 3 commit includes: YAML expansions, protocol moves, 14 deletions, smoke tests

**Files to Create**

| File | Change |
|------|--------|
| `tests/python/test_constitution_smoke.py` | New smoke test file (8 tests) |

---

## Story Summary

| ID | Title | Phase | Effort | Agent | Depends On |
|----|-------|-------|--------|-------|------------|
| CONST-001 | Extend engine.py: system introspection helpers | 1 | M | @dev | — |
| CONST-002 | Add generate_constitution() to engine.py | 1 | M | @dev | CONST-001 |
| CONST-003 | Add generate_synapse_digest() to engine.py | 1 | M | @dev | CONST-001 |
| CONST-004 | Wire generate_all() and add CLI command | 1 | S | @dev | CONST-002, CONST-003 |
| CONST-005 | Create governance_auto_update.py hook | 2 | M | @dev | CONST-004 |
| CONST-006 | Register governance_auto_update.py in settings.json | 2 | S | @dev | CONST-005 |
| CONST-007 | Expand Synapse YAML rules (L0, L1, L6) | 3 | L | @dev | CONST-003 |
| CONST-008 | Move protocol documents to reference/ | 3 | M | @dev | CONST-007 |
| CONST-009 | Delete 14 remaining markdown rule files | 3 | M | @dev | CONST-007, CONST-008 |
| CONST-010 | Add smoke test for full migration | 3 | S | @dev | CONST-009 |

**Total stories:** 10
**Effort breakdown:** S=3, M=5, L=1
**Estimated hours (from architect):** 7-11 hours total (Phase 1: 2-3h, Phase 2: 1-2h, Phase 3: 4-6h)

---

## Constraint Checklist (for @po review)

```
[ ] CONST-001 completed before CONST-002 or CONST-003 start
[ ] CONST-002 AND CONST-003 both completed before CONST-004 starts
[ ] CONST-004 completed (Phase 1 commit) before CONST-005 starts
[ ] CONST-005 completed before CONST-006 starts
[ ] CONST-006 completed (Phase 2 commit) before CONST-007 starts
[ ] CONST-003 completed (digest generator exists) before CONST-007 starts
[ ] CONST-007 completed before CONST-008 or CONST-009 starts
[ ] CONST-008 completed before CONST-009 starts
[ ] CONST-009 completed before CONST-010 starts
[ ] RULE: synapse-digest.md MUST exist before any .claude/rules/*.md deletion
[ ] RULE: 26+ Synapse rules MUST be validated before deletion commit
```

---

## Files Map (all stories combined)

**CREATE**

| File | Story |
|------|-------|
| `docs/architecture/constitution.md` | CONST-002 |
| `.claude/rules/synapse-digest.md` | CONST-003 |
| `.claude/hooks/governance_auto_update.py` | CONST-005 |
| `reference/AGENT-COGNITION-PROTOCOL.md` | CONST-008 |
| `reference/AGENT-INTEGRITY-PROTOCOL.md` | CONST-008 |
| `reference/EPISTEMIC-PROTOCOL.md` | CONST-008 |
| `tests/python/test_constitution_smoke.py` | CONST-010 |
| `tests/python/test_governance_engine.py` | CONST-001 (extended in 002, 003, 004) |

**MODIFY**

| File | Stories |
|------|---------|
| `core/governance/engine.py` | CONST-001, CONST-002, CONST-003, CONST-004 |
| `core/engine/rules/L0-constitution.yaml` | CONST-007 |
| `core/engine/rules/L1-global.yaml` | CONST-007 |
| `core/engine/rules/L6-keywords.yaml` | CONST-007 |
| `.claude/settings.json` | CONST-006 |

**DELETE**

| File | Story |
|------|-------|
| `.claude/rules/RULE-GROUP-1.md` through `RULE-GROUP-6.md` | CONST-009 |
| `.claude/rules/ANTHROPIC-STANDARDS.md` | CONST-009 |
| `.claude/rules/CLAUDE-LITE.md` | CONST-009 |
| `.claude/rules/directory-contract.md` | CONST-009 |
| `.claude/rules/logging.md` | CONST-009 |
| `.claude/rules/mcp-governance.md` | CONST-009 |
| `.claude/rules/no-secrets-in-memory.md` | CONST-009 |
| `.claude/rules/pipeline.md` | CONST-009 |
| `.claude/rules/state-management.md` | CONST-009 |
| `.claude/rules/agent-cognition.md` | CONST-008 (moved, not deleted) |
| `.claude/rules/agent-integrity.md` | CONST-008 (moved, not deleted) |
| `.claude/rules/epistemic-standards.md` | CONST-008 (moved, not deleted) |

**NOT TOUCHED (protected)**

| File | Reason |
|------|--------|
| `core/intelligence/pipeline/mce/*.py` | Brownfield constraint NFR-4 |
| `core/paths.py` | Read-only constraint CR-2 |
| `.claude/hooks/skill_router.py` | Does not load rules (architect D-6 revised) |
| `core/engine/synapse.py` | Already works, no changes needed |
| Root `CLAUDE.md` | Protected configuration |
| `.claude/CLAUDE.md` | Protected configuration |

---

*All doors are not the same. But every story is a key.*
*The Keymaker — sequence is complete.*
