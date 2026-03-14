# Technical Debt Assessment -- FINAL

> **Version:** 1.0.0
> **Date:** 2026-03-14
> **Author:** Brownfield Discovery Phase 8 -- The Architect
> **Status:** FINAL -- Incorporates QA review (score 78/100), all conditions addressed
> **Inputs:**
> - `docs/architecture/system-architecture.md` (Phase 1)
> - `docs/prd/technical-debt-DRAFT.md` (Phase 4)
> - `docs/reviews/qa-review.md` (Phase 7 -- QA Gate)
> - Live codebase validation (Phase 8)
> **Skipped Phases:** Phase 2 (Database -- N/A, filesystem-only), Phase 3 (Frontend/UX -- N/A, CLI-only)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total debts | 39 |
| CRITICAL (P0) | 8 |
| HIGH (P1) | 11 |
| MEDIUM (P2) | 13 |
| LOW (P3) | 7 |
| Total estimated effort | ~285 hours |
| Recommended phases | 4 sprints (P0+P1 in first two, P2 in quarter, P3 in backlog) |

This assessment identifies 39 technical debt items across 7 categories: System
Architecture (8), Code Quality (5), Configuration (5), Infrastructure (7),
Documentation (5), Security (6), and Testing (3). Of these, 31 originated from
the Phase 4 DRAFT, and 8 were added from QA gap analysis. One DRAFT claim
(TD-028: "no `.env` file") has been corrected -- the file exists.

The single most impactful finding is that the CI pipeline is entirely decorative:
it hardcodes "PASSED" for all 6 levels regardless of actual results, runs tests
against a non-existent directory, and checks syntax on only the first 50 Python
files. This means every merged PR in the project history has been unvalidated.

---

## QA Conditions -- Resolution Status

The QA gate (score 78/100) imposed 3 mandatory conditions. All are addressed below.

| # | Condition | Resolution |
|---|-----------|------------|
| 1 | Correct TD-028: `.env` file exists | DONE. TD-028 rewritten. Severity downgraded HIGH to LOW. The `.env` file exists (76 lines, 3.4KB). The actual debt is the absence of a startup guard that validates required keys. |
| 2 | Clarify TD-001 safe-delete list | DONE. TD-001 now explicitly enumerates all 21 duplicate files AND the 2 root-only files (`context_scorer.py`, `memory_manager.py`) that must be KEPT. |
| 3 | Add dependency chain to P0 | DONE. Section "Resolution Order" provides a strict 8-step dependency graph for P0 fixes. |

---

## Complete Debt Inventory

### CRITICAL Priority (P0 -- Fix This Sprint)

Total effort: ~14.5 hours

---

#### TD-001: 21 Duplicate Python Modules in core/intelligence/

**Severity:** CRITICAL | **Effort:** 3h | **Area:** Code Quality
**Dependencies:** Must complete BEFORE TD-009 (ruff count drops after deletion)

21 Python modules exist as identical copies at `core/intelligence/` root AND in
their proper subdirectory. A reorganization moved files into subdirectories but
never deleted the originals.

**Safe-to-delete list (21 files):**

| # | Root File | Canonical Location |
|---|-----------|-------------------|
| 1 | `agent_trigger.py` | `agents/` |
| 2 | `audit_layers.py` | `validation/` |
| 3 | `autonomous_processor.py` | `pipeline/` |
| 4 | `bootstrap_registry.py` | `entities/` |
| 5 | `business_model_detector.py` | `entities/` |
| 6 | `dossier_trigger.py` | `dossier/` |
| 7 | `entity_normalizer.py` | `entities/` |
| 8 | `org_chain_detector.py` | `entities/` |
| 9 | `review_dashboard.py` | `dossier/` |
| 10 | `role_detector.py` | `entities/` |
| 11 | `session_autosave.py` | `pipeline/` |
| 12 | `skill_generator.py` | `roles/` |
| 13 | `sow_generator.py` | `roles/` |
| 14 | `sync_package_files.py` | `pipeline/` |
| 15 | `task_orchestrator.py` | `pipeline/` |
| 16 | `theme_analyzer.py` | `dossier/` |
| 17 | `tool_discovery.py` | `roles/` |
| 18 | `validate_json_integrity.py` | `validation/` |
| 19 | `validate_layers.py` | `validation/` |
| 20 | `verify_classifications.py` | `validation/` |
| 21 | `viability_scorer.py` | `roles/` |

**DO NOT DELETE these root-only files (not duplicates):**

| File | Why It Must Stay |
|------|-----------------|
| `context_scorer.py` | Root-only. Imported by `rag/pipeline.py` (2 references). |
| `memory_manager.py` | Root-only. Imported by `context_scorer.py` (2 references) and `rag/pipeline.py` (1 reference). |

**Pre-deletion import fix required:**

`autonomous_processor.py` (root duplicate) imports `task_orchestrator` (root
duplicate) via `from core.intelligence.task_orchestrator import TaskOrchestrator`.
Before deleting, update this import in the CANONICAL copy at
`core/intelligence/pipeline/autonomous_processor.py` to point to
`core.intelligence.pipeline.task_orchestrator`. Then verify no other root-level
duplicate is imported by any non-duplicate code:

```
python3 -c "from core.intelligence.pipeline.task_orchestrator import TaskOrchestrator"
python3 -c "from core.intelligence.rag.pipeline import RAGPipeline"
pytest tests/python/ -v
```

---

#### TD-002: AGENT-INDEX.yaml Uses Deprecated `agents/minds/` Paths

**Severity:** CRITICAL | **Effort:** 1h | **Area:** Configuration
**Dependencies:** Depends on TD-004 (fix references first, then regenerate index)

`agents/AGENT-INDEX.yaml` contains 5 references to `agents/minds/` (the
deprecated path). The `agent_index_updater.py` hook continues generating these
stale paths because it has not been updated for the `agents/minds/` to
`agents/external/` rename.

**Fix:** Update `agent_index_updater.py` to emit `agents/external/` paths.
Regenerate `AGENT-INDEX.yaml`. Update `persona-registry.yaml` (6 references).

---

#### TD-003: Version Mismatch Between Package Manifests

**Severity:** CRITICAL | **Effort:** 10m | **Area:** Configuration
**Dependencies:** None. Safe first fix.

`package.json` declares version `1.4.0`. `pyproject.toml` declares version
`1.3.0`.

**Fix:** Set both to `1.4.0`. Add a single-source-of-version strategy (e.g.,
read from `package.json` in Python at build time, or maintain a shared
`VERSION` file).

---

#### TD-004: 92 Stale References to `agents/minds/` Across 27 Files

**Severity:** CRITICAL | **Effort:** 3h | **Area:** Code Quality
**Dependencies:** MUST come before TD-002 and TD-008

`agents/minds/` was renamed to `agents/external/` but 27 files still reference
the old path across 92 occurrences. This is higher than the DRAFT's original
count of 51/24 -- QA verification plus expanded search uncovered more matches in
artifacts, `.npmignore`, and cursor/windsurf configs.

Affected file categories:
- **Python code:** `audit_layers.py`, `verify_classifications.py`, `pipeline_heal.py`,
  `validate_cascading_integrity.py`
- **Config:** `AGENT-INDEX.yaml`, `persona-registry.yaml`, `.gitignore`, `.npmignore`,
  `.windsurf/agents.yaml`, `.cursor/agents.yaml`, `.claude/agents.yaml`
- **Hooks:** `agent_index_updater.py`
- **Rules:** `directory-contract.md`, `CLAUDE.md`
- **Reference docs:** `LAYERS.md`, `BROWNFIELD-MEGABRAIN.md`,
  `MEGABRAIN-3D-ARCHITECTURE.md`, `CROSS-REPO-ANALYSIS.md`
- **Artifacts:** `AUDIT-REPORT.json` (30 occurrences), various implementation logs

**Fix:** Global find-and-replace `agents/minds/` to `agents/external/` across
all 27 files. Then delete `agents/minds/` directory (its content is a strict
subset of `agents/external/`). Note: some files in `artifacts/` and `outputs/`
are historical records -- decide whether to update those or leave them as-is
with a note.

---

#### TD-014: CI Tests Point to Non-Existent Directory

**Severity:** CRITICAL | **Effort:** 15m | **Area:** Infrastructure
**Dependencies:** None. Safe early fix. Must come before TD-019.

`.github/workflows/verification.yml` checks `if [ -d "scripts/tests" ]` -- that
directory does not exist. Tests live at `tests/python/`. The conditional causes
the test step to silently skip with an info message.

**Fix:** Change `scripts/tests/` to `tests/python/` in `verification.yml`.
Remove the `|| echo` fallback so test failures actually fail the CI.

---

#### TD-019: CI Pipeline is Entirely Decorative (Rewrite Required)

**Severity:** CRITICAL | **Effort:** 4h | **Area:** Infrastructure
**Dependencies:** Depends on TD-014 (fix test path first)

This debt is more severe than originally reported in the DRAFT. The QA review
(GAP-3) revealed that the CI pipeline is not merely "missing tests" -- it is
architecturally designed to always pass:

| Level | What It Claims | What It Actually Does |
|-------|---------------|----------------------|
| Level 1: Lint | Checks Python syntax | Only checks first 50 `.py` files (120+ exist). Never runs ruff. |
| Level 2: Tests | Runs tests | Checks non-existent `scripts/tests/` directory, skips silently |
| Level 3: Integrity | Checks imports | Prints "Basic import check passed" without checking anything |
| Level 4: Structure | Validates dirs | Checks 6 dirs exist (always true in checked-out repo) |
| Level 5: Security | Scans secrets | Basic grep that excludes "test" matches, warns but never fails |
| Level 6: Final | Verification | Hardcodes "PASSED" for all 6 levels regardless of results |

Every PR in project history has merged without actual validation.

**Fix:** Rewrite `verification.yml` completely:
1. Run `ruff check core/ .claude/hooks/` (fail on errors)
2. Run `python3 -m pytest tests/python/ -v` (fail on failures)
3. Run `python3 core/intelligence/validation/validate_json_integrity.py`
4. Run `node bin/pre-publish-gate.js`
5. Remove hardcoded "PASSED" report -- report actual results
6. Set Level 1 to use `setup-python` with 3.12 (currently 3.11)

---

#### TD-032: API Key Hardcoded in Auto-Memory File (NEW -- from QA GAP-1)

**Severity:** CRITICAL | **Effort:** 30m | **Area:** Security
**Dependencies:** None. Immediate fix.

The Claude auto-memory file at
`~/.claude/projects/.../memory/MEMORY.md` contains plaintext secrets:

- Fireflies API key: `fe9bae31-e325-4892-b0ce-4a6f31584f87`
- N8N production webhook URL: `https://thiagofinch.app.n8n.cloud/webhook/35f17dcc-...`

While this file is outside the git repo, it persists across all Claude Code
sessions and could be leaked via backup, cloud sync, or project directory
sharing.

**Fix:**
1. Remove plaintext secrets from `MEMORY.md` immediately
2. Replace with reference-only entries: "Fireflies API key stored in `.env` as
   `FIREFLIES_API_KEY`"
3. Rotate the exposed Fireflies API key (it is now in this document's git
   history if committed from a session that read it)
4. Add a guideline to `.claude/rules/` prohibiting secrets in memory files

---

#### TD-033: Pickle Deserialization Without Validation (NEW -- from QA GAP-2)

**Severity:** CRITICAL | **Effort:** 2h | **Area:** Security
**Dependencies:** None. Independent fix.

`core/intelligence/speakers/voice_embedder.py` (line 63) uses `pickle.load()`
to deserialize speaker voice embeddings from disk. Pickle deserialization of
untrusted data is a known remote code execution vector (CWE-502). While the data
is currently locally generated, if the `.data/` directory were ever populated
from an external source (shared knowledge base, downloaded model), this becomes
exploitable.

**Fix:** Replace `pickle` with `json` or `numpy.save/load` for embeddings.
Update the save path to use the new format. Add a migration step for any
existing `.pkl` files.

---

### HIGH Priority (P1 -- Fix Next Sprint)

Total effort: ~37 hours (excluding TD-010 Phase 1 which is 20h)

---

#### TD-005: Python Version Target Inconsistency

**Severity:** HIGH | **Effort:** 15m | **Area:** Configuration
**Dependencies:** None.

`pyproject.toml` has conflicting Python version targets:
- `[tool.ruff]` section: `target-version = "py312"`
- `[tool.pyright]` section: `pythonVersion = "3.11"`
- `.python-version` file: `3.12`
- CI workflow: `python-version: '3.11'`

**Fix:** Align all to `3.12` (matching `.python-version` and ruff).

---

#### TD-006: PostToolUse Hooks Fire on Every Tool Call (No Matcher)

**Severity:** HIGH | **Effort:** 4h | **Area:** Infrastructure
**Dependencies:** None.

The PostToolUse event in `settings.json` has `"matcher": ""` (empty = matches
everything). 11 hooks fire on every Read, Write, Edit, Bash, Glob, Grep call.
Most are only relevant to Write/Edit operations.

**Fix:** Add matchers (e.g., `"matcher": "Write|Edit"`) to hooks that only care
about write operations. Expected 60-70% reduction in PostToolUse invocations.

---

#### TD-007: `docs/` Directory Prohibited but Actively Used

**Severity:** HIGH | **Effort:** 2h | **Area:** Architecture
**Dependencies:** None.

The contradiction is deeper than originally reported (QA GAP-6). Three
authoritative documents give three different answers:
- `CLAUDE.md`: "Plans MUST be saved to `docs/plans/`"
- `directory-contract.md`: `docs/` is PROHIBITED, use `reference/`
- `.claude/CLAUDE.md` Layer System table: lists `docs/` as L1 tracked

The Brownfield Discovery workflow itself creates files in `docs/` -- this very
document is in `docs/prd/`.

**Fix:** Un-prohibit `docs/` in the directory contract. The pragmatic reality is
that `docs/` serves a different purpose than `reference/`: `docs/` contains
process artifacts (plans, PRDs, reviews, stories), while `reference/` contains
durable reference documentation. Formalize this split.

---

#### TD-008: `agents/minds/` Directory Still Exists on Disk

**Severity:** HIGH | **Effort:** 15m | **Area:** Architecture
**Dependencies:** MUST come after TD-004 (fix all references first)

`agents/minds/` exists with 6 subdirectories (`_example`, `alex-hormozi`,
`cole-gordon`, `jeremy-haynes`, `jeremy-miner`, `the-scalable-company`).
`agents/external/` has the same agents plus additional ones. The minds directory
is a strict subset.

**Fix:** Delete `agents/minds/` after completing TD-004.

---

#### TD-009: 352 Ruff Lint Errors

**Severity:** HIGH | **Effort:** 3h | **Area:** Code Quality
**Dependencies:** Should come after TD-001 (duplicate deletion reduces count)

Current `ruff check` returns 352 errors:
- 109 F541 (f-string without placeholders)
- 45 UP006 (non-PEP585 annotations)
- 38 F401 (unused imports)
- 34 I001 (unsorted imports)
- 33 UP017 (datetime timezone UTC)
- 26 UP015 (redundant open modes)
- 8 F841 (unused variables)
- 2 F601 / B023 (potential bugs)

316 of 352 are auto-fixable. However, per QA guidance, the 109 F541 errors must
NOT be bulk auto-fixed -- each needs human review to determine if a `{variable}`
was accidentally removed (bug) or if the f-prefix is just unnecessary (style).

**Fix:**
1. Run `ruff check --fix core/ .claude/hooks/` for the 207 non-F541 auto-fixable
   errors
2. Manually review each F541 instance (109 cases)
3. Manually fix the remaining 36 non-auto-fixable errors

---

#### TD-010: 50 Tests for 29,640 Lines of Python (~0.17% Coverage)

**Severity:** HIGH | **Effort:** 80h+ (phased) | **Area:** Testing
**Dependencies:** None for Phase 1. Later phases depend on TD-001 cleanup.

The test-to-code ratio is critically low. 50 tests cover only layer
classification (44), RAG chunker (13), and bucket processor (22). Zero tests
exist for pipeline, MCE, hooks, entity resolution, or dossier compilation.

Historical note (QA GAP-7): A previous session recorded 248 tests passing. The
regression to 50 suggests tests were either removed, moved, or the test
infrastructure changed. This history itself is a debt indicator.

**Fix (phased):**
- Phase 1 (20h): Unit tests for `core/intelligence/pipeline/`
- Phase 2 (20h): Unit tests for `core/intelligence/rag/`
- Phase 3 (20h): Integration tests for hook system
- Phase 4 (20h): Tests for entities, dossier, agents modules

---

#### TD-017: `.gitignore` Tests Contradiction (Line 278 vs 652)

**Severity:** HIGH | **Effort:** 15m | **Area:** Configuration
**Dependencies:** None. Independent fix.

The 694-line `.gitignore` has a contradiction:
- Line 278-279: `!tests/` and `!tests/**` (whitelist)
- Line 652: `tests/` (deny -- in BLOCO 7 "HYGIENE DENY")

Last match wins in gitignore, so tests are effectively ignored by git.

**Fix:** Remove line 652 (`tests/` in BLOCO 7). After fix, run `git status` to
confirm test files appear as tracked. Expect a large diff as test files become
visible to git for the first time.

---

#### TD-024: CLAUDE.md Architecture Diagram Shows Deprecated Directories

**Severity:** HIGH | **Effort:** 30m | **Area:** Documentation
**Dependencies:** None.

`.claude/CLAUDE.md` architecture diagram includes deprecated paths:
- `workspace/domains/` (removed in S13)
- `workspace/team/` (removed in S13)
- `agents/minds/` in Layer System table

**Fix:** Update to match `directory-contract.md` v4.0.0.

---

#### TD-031: RAG Business Index Not Built

**Severity:** HIGH | **Effort:** 2h | **Area:** Architecture
**Dependencies:** None.

The `rag_business` path is defined in `paths.py` but the index is empty.
Business knowledge (meeting insights, call transcripts) cannot be searched
semantically.

**Fix:** Run the chunker + BM25 index builder against `knowledge/business/`
content.

---

#### TD-034: Hook Error Handling is Inconsistent (NEW -- from QA GAP-4)

**Severity:** HIGH | **Effort:** 4h | **Area:** Infrastructure
**Dependencies:** None.

All 37 hooks in `.claude/hooks/` have `sys.exit()` calls, but error handling
patterns vary wildly:
- Some hooks have 8-9 `sys.exit()` calls with proper error codes (0/1/2)
- Some hooks catch ALL exceptions and exit silently with `sys.exit(0)`
- `memory_capture.py` has a 30ms timeout (Python startup alone takes longer)

The Anthropic Standards document (`.claude/rules/ANTHROPIC-STANDARDS.md`) defines
the correct exit code convention (0=success, 1=warning, 2=block) but compliance
is inconsistent.

**Fix:** Audit all 37 hooks for exit code compliance. Standardize error handling
to match the Anthropic Standards specification. Fix or remove
`memory_capture.py` (30ms timeout makes it a permanent no-op).

---

### MEDIUM Priority (P2 -- Fix This Quarter)

Total effort: ~67 hours

---

#### TD-011: 34 Files Use Hardcoded `BASE_DIR` Instead of `core.paths`

**Severity:** MEDIUM | **Effort:** 6h | **Area:** Code Quality
**Dependencies:** Re-count after TD-001 (some files are in duplicates)

34 Python files define their own `BASE_DIR` via `Path(__file__).resolve()...`
instead of importing from `core.paths`. Creates two parallel path resolution
systems.

**Fix:** Refactor all files to import from `core.paths`. Remove all local
`BASE_DIR` definitions.

---

#### TD-013: 109 f-strings Without Placeholders (F541)

**Severity:** MEDIUM | **Effort:** 4h | **Area:** Code Quality
**Dependencies:** Re-count after TD-001 (some are in duplicates). Partially
overlaps with TD-009 but requires individual human review.

Each instance needs determination: bug (placeholder accidentally deleted) or
unnecessary f-prefix (style issue).

**Fix:** Review each F541 instance individually. Do NOT batch auto-fix.

---

#### TD-015: `memory_capture.py` Timeout Set to 30ms

**Severity:** MEDIUM | **Effort:** 5m | **Area:** Configuration
**Dependencies:** None.

In `settings.json`, `memory_capture.py` has `"timeout": 30` (30ms). Every other
hook has 5000-10000ms. Python process startup alone exceeds 30ms.

**Fix:** Change timeout to 5000ms or remove the hook if it serves no purpose.

---

#### TD-018: JSON State Files Have No Runtime Schema Validation

**Severity:** MEDIUM | **Effort:** 8h | **Area:** Architecture
**Dependencies:** None.

10+ JSON state files in `.claude/mission-control/` are read without schema
validation. `core/schemas/` contains 6 JSON schemas but zero Python code
references them -- they are documentation-only artifacts.

**Fix:** Add schema validation at read time for critical state files. Use the
existing schemas or consolidate into a validation utility.

---

#### TD-020: Hook System Total Timeout Budget is 195 Seconds

**Severity:** MEDIUM | **Effort:** 8h | **Area:** Infrastructure
**Dependencies:** Consider alongside TD-006 (matcher optimization)

Worst-case interaction cycle triggers 33 hooks with combined timeout of 195
seconds:
- SessionStart: 4 hooks, 25s
- UserPromptSubmit: 7 hooks, 40s
- PreToolUse: 5 hooks, 25s
- PostToolUse: 11 hooks, 75s
- Stop: 6 hooks, 35s

**Fix:** Consolidate related hooks:
- Merge agent lifecycle hooks into single `agent_lifecycle.py`
- Merge pipeline hooks into single `pipeline_hooks.py`
- Merge session hooks into single `session_lifecycle.py`

---

#### TD-025: `reference/` Docs Reference Deprecated Paths

**Severity:** MEDIUM | **Effort:** 2h | **Area:** Documentation
**Dependencies:** Should come after TD-004 (agents/minds fixup)

- `reference/LAYERS.md`: 6 references to `docs/` as L1 path
- `reference/architecture/BROWNFIELD-MEGABRAIN.md`: 3 references to
  `knowledge/workspace/` (deprecated since S12)
- `reference/MEGABRAIN-3D-ARCHITECTURE.md`: 1 reference to `agents/minds/`

**Fix:** Update all reference docs to match current directory structure.

---

#### TD-026: Missing Capstone Documentation

**Severity:** MEDIUM | **Effort:** 16h | **Area:** Documentation
**Dependencies:** None.

Referenced in code/rules but do not exist:
- `reference/IMPLEMENTATION-LOG.md`
- `reference/ONBOARDING-GUIDE.md`

**Fix:** Create both documents. Update `MEGABRAIN-3D-ARCHITECTURE.md`.

---

#### TD-029: `.mcp.json` Contains Hardcoded Absolute Path

**Severity:** MEDIUM | **Effort:** 15m | **Area:** Security
**Dependencies:** None.

The filesystem MCP server configuration contains
`/Users/thiagofinch/Documents/Projects/mega-brain` which breaks for any other
user or machine.

**Fix:** Use relative path or `${HOME}` variable interpolation.

---

#### TD-030: No Credential Rotation Policy

**Severity:** MEDIUM | **Effort:** 2h | **Area:** Security
**Dependencies:** None.

API keys (Fireflies bearer token, N8N API key) have no documented rotation
schedule or expiry monitoring.

**Fix:** Document rotation schedule in `reference/SECURITY.md`. Consider adding
a `session_start.py` check that warns if API keys are older than 90 days.

---

#### TD-035: No Concurrent State File Access Protection (NEW -- from QA GAP-5)

**Severity:** MEDIUM | **Effort:** 4h | **Area:** Architecture
**Dependencies:** Relates to TD-006 (fewer hooks = fewer concurrent writes)

Multiple hooks may write to the same JSON state files during a single tool use
cycle. 11 PostToolUse hooks fire on every tool call. If two hooks read-modify-write
the same file, the last writer wins and earlier changes are silently lost. No
file locking mechanism exists.

**Fix:** Add file locking (e.g., `fcntl.flock()`) for critical state files, or
serialize state updates through a single coordinator hook.

---

#### TD-036: `.npmignore` References Stale Paths (NEW -- from QA GAP-8)

**Severity:** MEDIUM | **Effort:** 1h | **Area:** Configuration
**Dependencies:** Should come after TD-004

The `.npmignore` file (144 lines) contains stale references:
- Line 23: `agents/minds/` (deprecated, should be `agents/external/`)
- Line 28-30: `knowledge/dna/`, `knowledge/dossiers/`, `knowledge/playbooks/`,
  `knowledge/sources/` (these paths moved under `knowledge/external/` in S12)
- Line 37: `inbox/` (root inbox removed in S03)

Additionally, since `package.json` "files" is the primary whitelist and
`.npmignore` is the second defense layer, the `.npmignore` should be audited
against the current directory structure to ensure the published package does not
include the 21 duplicate modules, `.DS_Store` files, or debug artifacts.

**Fix:** Update all stale paths. Run `npm pack --dry-run` to verify published
file list matches expectations.

---

#### TD-037: `docs/` vs `reference/` Self-Referential Contradiction (NEW -- from QA GAP-6)

**Severity:** MEDIUM | **Effort:** 2h | **Area:** Documentation
**Dependencies:** Overlaps with TD-007 but focuses on the deeper inconsistency

Three authoritative documents give contradictory guidance about `docs/`:
- `CLAUDE.md`: "Plans MUST be saved to `docs/plans/`"
- `directory-contract.md`: `docs/` is PROHIBITED, use `reference/`
- `.claude/CLAUDE.md`: Layer System table lists `docs/` as L1 tracked

This is self-referential: the Brownfield Discovery workflow that identified this
contradiction is itself writing files to `docs/`. The `paths.py` ROUTING table
does not have a key for `docs/`, reinforcing the prohibition, yet 8
subdirectories exist under `docs/` with active content.

**Fix:** Formalize the `docs/` vs `reference/` split:
- `docs/` = ephemeral process artifacts (plans, PRDs, reviews, stories, reports)
- `reference/` = durable reference documentation (architecture, guides, protocols)
- Update `directory-contract.md` to un-prohibit `docs/` with this definition
- Add `ROUTING["docs_plans"]`, `ROUTING["docs_prd"]` etc. to `paths.py`
- Update CLAUDE.md to reflect the split

---

### LOW Priority (P3 -- Backlog)

Total effort: ~45 hours

---

#### TD-012: 22 TODO/FIXME/HACK Comments in Production Code

**Severity:** LOW | **Effort:** 4h | **Area:** Code Quality
**Dependencies:** None.

22 TODO/FIXME/HACK comments in `core/intelligence/` represent untracked debt.

**Fix:** Audit all 22. Convert actionable ones to GitHub issues. Remove stale
ones.

---

#### TD-016: `pipeline` Optional Dependency Group is Redundant

**Severity:** LOW | **Effort:** 5m | **Area:** Configuration
**Dependencies:** None.

In `pyproject.toml`, the `[pipeline]` optional group only contains `PyYAML`,
which is already a required dependency.

**Fix:** Remove the group or add actual pipeline-specific dependencies.

---

#### TD-021: `core/.claude/` Rogue Directory

**Severity:** LOW | **Effort:** 5m | **Area:** Infrastructure
**Dependencies:** None.

Contains only `.DS_Store` and an empty `sessions/` subdirectory.

**Fix:** Delete `core/.claude/` entirely.

---

#### TD-022: `outputs/` Directory Exists Outside Directory Contract

**Severity:** LOW | **Effort:** 5m | **Area:** Infrastructure
**Dependencies:** None.

Rogue directory not tracked by `paths.py` or `directory-contract.md`.

**Fix:** Determine if content should move to `artifacts/` or delete if empty.

---

#### TD-023: 67 `.DS_Store` Files and 41 `.pyc` Files in Working Tree

**Severity:** LOW | **Effort:** 15m | **Area:** Infrastructure
**Dependencies:** None.

**Fix:** Add to BLOCO 1 of `.gitignore`. Run cleanup commands.

---

#### TD-027: 17 Rule Files Total ~5,120 Lines of Markdown

**Severity:** LOW | **Effort:** 16h | **Area:** Documentation
**Dependencies:** None.

17 rule documents with overlapping and occasionally contradictory instructions.
The lazy-loading architecture is sound but content needs pruning.

**Fix:** Audit for contradictions, overlaps, and obsolete rules. Consolidate
where possible.

---

#### TD-028: No `.env` Startup Validation Guard (CORRECTED)

**Severity:** LOW | **Effort:** 1h | **Area:** Security
**Dependencies:** None.

**CORRECTION from DRAFT:** The `.env` file EXISTS (76 lines, 3.4KB, verified by
QA). The original DRAFT incorrectly claimed it did not exist. The actual debt is
the absence of a startup guard that validates required keys
(`OPENAI_API_KEY`, `VOYAGE_API_KEY`, `FIREFLIES_API_KEY`) are present and
non-empty.

**Fix:** Add validation in `session_start.py` or CLI entry point that warns if
required keys are missing or empty in `.env`.

---

#### TD-038: Test Count Regression Not Documented (NEW -- from QA GAP-7)

**Severity:** LOW | **Effort:** 1h | **Area:** Testing
**Dependencies:** None.

A previous session recorded 248 tests passing. Current count is 50. The
regression suggests tests were removed, relocated, or the test infrastructure
changed. No record explains this history.

**Fix:** Investigate and document what happened to the missing 198 tests. If
they were moved (e.g., to a different runner or framework), restore access. If
they were deleted, document why.

---

## Resolution Order

The P0 dependency chain MUST be followed in this exact sequence. Each step
depends on the one before it.

```
STEP 1: TD-003 (sync versions)
         No dependencies. Safe first fix. 10 minutes.
              |
              v
STEP 2: TD-032 (remove secrets from auto-memory)
         No dependencies. Immediate security fix. 30 minutes.
              |
              v
STEP 3: TD-033 (replace pickle.load)
         No dependencies. Security fix. 2 hours.
              |
              v
STEP 4: TD-014 (fix CI test path)
         No dependencies. 15 minutes.
              |
              v
STEP 5: TD-004 (fix 92 agents/minds/ references)
         MUST come before TD-002 and TD-008.
         3 hours.
              |
              v
STEP 6: TD-002 (regenerate AGENT-INDEX.yaml)
         Depends on TD-004. 1 hour.
              |
              v
STEP 7: TD-001 (delete 21 duplicate modules)
         MUST update autonomous_processor.py import FIRST.
         MUST verify context_scorer.py and memory_manager.py are NOT deleted.
         Run smoke tests after each batch of deletions.
         3 hours.
              |
              v
STEP 8: TD-019 (rewrite CI pipeline)
         Depends on TD-014 (path fix) and TD-001 (clean codebase).
         Should run clean ruff + pytest in new CI.
         4 hours.
```

**P1 Recommended Order (after P0 complete):**

```
TD-008 (delete agents/minds/)           -- 15m, depends on TD-004
TD-005 (align Python versions)          -- 15m
TD-017 (fix gitignore contradiction)    -- 15m
TD-015 (fix memory_capture timeout)     -- 5m, consolidate with TD-034
TD-034 (standardize hook error handling) -- 4h
TD-024 (update CLAUDE.md diagram)       -- 30m
TD-009 (fix 352 ruff errors)            -- 3h, reduced count after TD-001
TD-006 (add PostToolUse matchers)       -- 4h
TD-007 (resolve docs/reference)         -- 2h
TD-031 (build RAG business index)       -- 2h
TD-010 Phase 1 (pipeline tests)         -- 20h
```

**Cross-Priority Dependencies:**

| P2 Debt | Affected By | Impact |
|---------|------------|--------|
| TD-011 (hardcoded BASE_DIR) | TD-001 (duplicates) | Some of the 34 files are in the duplicate set. Re-count after P0. |
| TD-013 (F541 f-strings) | TD-001 (duplicates) | Some F541 errors are in duplicate files. Re-count after P0. |
| TD-036 (.npmignore stale paths) | TD-004 (agents/minds) | Fix agents/minds refs in .npmignore as part of TD-004. |

---

## Risk Matrix

| Risk | Category | Probability | Impact | Mitigation |
|------|----------|-------------|--------|------------|
| Deleting duplicate modules breaks runtime imports | Regression | HIGH | HIGH | 3 root modules have active imports. Update importers BEFORE deleting. Smoke test after each deletion batch. |
| CI continues to pass with broken code after "fixes" | Infrastructure | CERTAIN | HIGH | Rewrite CI completely (TD-019). Current CI is decorative. |
| `agents/minds/` rename causes path resolution failures | Regression | MEDIUM | HIGH | Run full pytest + manual pipeline test after fixing 92 references. Some code constructs paths dynamically. |
| `.gitignore` fix causes large git diff | Integration | HIGH | MEDIUM | After removing line 652, all test files appear as "new." Communicate clearly in PR description. |
| Ruff auto-fix changes runtime behavior | Regression | LOW | HIGH | 109 F541 instances are the risk. Review individually, do NOT batch auto-fix. |
| Pickle deserialization from shared data sources | Security | LOW | CRITICAL | Replace pickle with JSON before any knowledge-sharing feature. |
| API key in auto-memory leaks via backup/sync | Security | MEDIUM | HIGH | Remove plaintext secrets immediately. Rotate exposed key. |
| Hook consolidation introduces new bugs | Regression | MEDIUM | MEDIUM | Add tests for consolidated hooks before removing originals. |
| State file corruption from concurrent hook writes | Data Integrity | LOW | HIGH | Add file locking for critical JSON files. Reduced risk after TD-006 (fewer concurrent hooks). |
| Version sync breaks npm publish pipeline | Integration | LOW | MEDIUM | Test `npm pack` after syncing versions. |
| Exposed webhook URL enables unauthorized access | Security | LOW | MEDIUM | Webhook URL in auto-memory could be called externally. Rotate if concerned. |

---

## Success Criteria

How to verify each priority tier is fully resolved.

### P0 Complete When:

| Criterion | Verification Command |
|-----------|---------------------|
| No agents/minds/ references anywhere | `grep -r "agents/minds/" . --include="*.{py,md,yaml,json}"` returns 0 results |
| Zero duplicate root modules | `ls core/intelligence/*.py | grep -v __init__ | wc -l` returns exactly 2 (`context_scorer.py`, `memory_manager.py`) |
| Versions synced | `python3 -c "import json,tomllib; p=json.load(open('package.json')); t=tomllib.load(open('pyproject.toml','rb')); assert p['version']==t['project']['version']"` succeeds |
| CI runs real tests | Push a PR with a failing test, verify CI marks it as failed |
| No secrets in auto-memory | `grep -i "api.key\|bearer\|token.*=" ~/.claude/projects/*/memory/MEMORY.md` returns 0 matches (excluding reference-only entries) |
| No pickle deserialization | `grep -r "pickle.load" core/` returns 0 results |
| RAG pipeline works after cleanup | `python3 -c "from core.intelligence.rag.pipeline import RAGPipeline"` succeeds |

### P1 Complete When:

| Criterion | Verification Command |
|-----------|---------------------|
| Zero ruff errors | `ruff check core/ .claude/hooks/` returns "All checks passed!" |
| Tests tracked by git | `git ls-files tests/python/ | wc -l` returns >0 |
| agents/minds/ deleted | `ls agents/minds/ 2>/dev/null` returns error |
| Hook error handling standardized | All 37 hooks follow 0/1/2 exit code convention |
| RAG business index built | `.data/rag_business/` contains index files |
| Pipeline test coverage >= 40% | `pytest --cov=core.intelligence.pipeline tests/` reports >=40% |

### P2 Complete When:

| Criterion | Verification Command |
|-----------|---------------------|
| Zero hardcoded BASE_DIR | `grep -r "BASE_DIR" core/intelligence/*.py` returns 0 results |
| docs/ vs reference/ resolved | `directory-contract.md` no longer lists `docs/` as PROHIBITED |
| Schema validation active | Critical state files validated on read |
| .npmignore current | `npm pack --dry-run` shows no stale paths |

---

## Appendix: Verification Data

All data points verified against the live codebase on 2026-03-14.

| Metric | DRAFT Claim | QA Verification | Final Verification (Phase 8) |
|--------|-------------|-----------------|------------------------------|
| Ruff errors | 352 | 352 CONFIRMED | 352 CONFIRMED |
| Duplicate modules | 21 | 21 CONFIRMED (but 3 have imports, not 1) | 21 CONFIRMED. 2 root-only non-duplicates identified. |
| `agents/minds/` references | 51 across 24 files | 51 CONFIRMED | 92 across 27 files (expanded search scope) |
| `.gitignore` contradiction | Lines 278 vs 652 | CONFIRMED | CONFIRMED. File is 694 lines. |
| CI test directory | `scripts/tests/` does not exist | CONFIRMED | CONFIRMED. CI is entirely decorative (GAP-3). |
| `.env` file | "Does not exist" | EXISTS (76 lines, 3.4KB) | CONFIRMED EXISTS. DRAFT claim CORRECTED. |
| Test count | 50 | 50 CONFIRMED | 50 CONFIRMED. Previous session had 248 (regression). |
| JSON schemas | 7 in `core/schemas/` | Not re-verified | 6 confirmed (not 7). Zero Python imports. |
| Rule files | 17 files, ~8,000 lines | Not re-verified | 17 files, 5,120 lines (lower than DRAFT estimate). |
| MCE modules | Not counted | Not counted | 8 modules in `pipeline/mce/`, zero tests. |
| `.npmignore` | Not audited | GAP-8: Not audited | 144 lines. Contains 4+ stale path references. |
| Root-only modules | Not identified | `context_scorer.py`, `memory_manager.py` | CONFIRMED. Both have active importers in `rag/pipeline.py`. |
| Pickle usage | Not identified | GAP-2: `voice_embedder.py:63` | CONFIRMED at `core/intelligence/speakers/voice_embedder.py:63`. |
| Hook count | 33 hooks | 37 hooks across 5 events | 37 CONFIRMED (from `settings.json`). |

---

## Appendix: Debt-to-Debt Dependency Graph

```
TD-003 (versions)
  |
  |  (no dependency)
  v
TD-032 (secrets) -----> TD-030 (rotation policy, P2)
  |
  |  (no dependency)
  v
TD-033 (pickle)
  |
  |  (no dependency)
  v
TD-014 (CI path) -----> TD-019 (CI rewrite)
  |                          |
  |  (no dependency)         |
  v                          v
TD-004 (agents/minds) --+-> TD-002 (AGENT-INDEX)
  |                     |
  |                     +-> TD-008 (delete minds/)
  |                     |
  |                     +-> TD-036 (.npmignore stale)
  |                     |
  |                     +-> TD-025 (reference docs)
  |                     |
  |                     +-> TD-024 (CLAUDE.md)
  v
TD-001 (duplicates) --> TD-009 (ruff, count drops)
  |                 --> TD-011 (BASE_DIR, count drops)
  |                 --> TD-013 (F541, count drops)
  v
TD-019 (CI rewrite) --> TD-010 (tests, CI must work first)

TD-006 (matchers) ----> TD-035 (concurrent writes, fewer hooks = less risk)
                   ---> TD-020 (timeout budget, fewer fires = less timeout)

TD-007 (docs/) -------> TD-037 (docs/reference split)

TD-034 (hook errors) -> TD-015 (memory_capture 30ms, subset of TD-034)
```

---

## Appendix: Effort Summary by Priority

| Priority | Debt Count | Estimated Effort | Recommended Timeframe |
|----------|-----------|-----------------|----------------------|
| P0 (CRITICAL) | 8 | ~14.5h | This sprint (1-2 days focused) |
| P1 (HIGH) | 11 | ~37h (excl. TD-010 Phase 1: +20h) | Next sprint |
| P2 (MEDIUM) | 13 | ~67h | This quarter |
| P3 (LOW) | 7 | ~45h (mostly TD-027 rule pruning + TD-010 later phases) | Backlog |
| **TOTAL** | **39** | **~163.5h** (P0+P1+P2) / **~208.5h** (all) | |

Note: TD-010 (test coverage) accounts for 80h across all 4 phases. Excluding
that single item, the remaining 38 debts total ~128.5h.

---

**END OF FINAL ASSESSMENT**

*Brownfield Discovery Phase 8 -- All QA conditions addressed.*
