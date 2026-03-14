# Technical Debt Assessment -- DRAFT

> **Version:** 0.1.0-DRAFT
> **Date:** 2026-03-14
> **Author:** Brownfield Discovery Phase 4 -- The Architect
> **Status:** DRAFT -- Pending specialist review
> **Input:** `docs/architecture/system-architecture.md` (Phase 1) + live codebase validation
> **Skipped Phases:** Phase 2 (Database -- N/A, filesystem-only), Phase 3 (Frontend/UX -- N/A, CLI-only)

---

## 1. System Architecture Debts

These debts were identified in the Phase 1 system architecture document and validated
against the live codebase.

### TD-001: 21 Duplicate Python Modules in core/intelligence/

**Severity:** CRITICAL
**Impact:** Developer confusion, bug divergence risk, maintenance double-work
**Effort:** 3h
**Area:** Code Quality

21 Python modules exist as identical copies at `core/intelligence/` root AND in their
proper subdirectory (e.g., `core/intelligence/agent_trigger.py` duplicates
`core/intelligence/agents/agent_trigger.py`). Only 1 of the 21 root copies
(`task_orchestrator.py`) has any import reference. The other 20 are confirmed dead code.

Origin: A reorganization moved files into subdirectories but never deleted the originals.

**Files:** 42 files (21 pairs). Full list in `docs/architecture/system-architecture.md` section 4.3.

**Fix:** Delete 20 dead root copies. For `task_orchestrator.py`, update its one importer
to point to `core/intelligence/pipeline/task_orchestrator.py`, then delete the root copy.

---

### TD-002: AGENT-INDEX.yaml Uses Deprecated `agents/minds/` Paths

**Severity:** CRITICAL
**Impact:** Agent discovery returns stale paths, breaks any tooling that follows the index
**Effort:** 1h
**Area:** Configuration

`agents/AGENT-INDEX.yaml` contains 5 references to `agents/minds/` (the deprecated path).
The `agent_index_updater.py` hook continues generating these stale paths because it
has not been updated for the `agents/minds/` to `agents/external/` rename.

**Fix:** Update `agent_index_updater.py` to emit `agents/external/` paths. Regenerate
`AGENT-INDEX.yaml`. Update `persona-registry.yaml` (6 references).

---

### TD-003: Version Mismatch Between Package Manifests

**Severity:** CRITICAL
**Impact:** npm publishes 1.4.0, pip installs 1.3.0, causes user confusion on version reporting
**Effort:** 10m
**Area:** Configuration

`package.json` declares version `1.4.0`. `pyproject.toml` declares version `1.3.0`.

**Fix:** Set both to `1.4.0`. Add a single-source-of-version strategy (e.g., read from
`package.json` in Python at build time, or maintain a shared `VERSION` file).

---

### TD-004: 51 Stale References to `agents/minds/` Across 24 Files

**Severity:** CRITICAL
**Impact:** Any code path following these references hits wrong or missing directories
**Effort:** 2h
**Area:** Code Quality

`agents/minds/` was renamed to `agents/external/` but 24 files still reference the old
path across 51 occurrences. This includes:
- Python code: `audit_layers.py`, `verify_classifications.py`, `pipeline_heal.py`
- Config: `AGENT-INDEX.yaml`, `persona-registry.yaml`, `.gitignore`
- Hooks: `agent_index_updater.py`
- Rules: `directory-contract.md`
- Claude config: `.claude/CLAUDE.md`
- Reference docs: `LAYERS.md`, `BROWNFIELD-MEGABRAIN.md`

**Fix:** Global find-and-replace `agents/minds/` to `agents/external/` across all 24 files.
Then delete `agents/minds/` directory (its content is a subset of `agents/external/`).

---

### TD-005: Python Version Target Inconsistency

**Severity:** HIGH
**Impact:** Pyright type checking runs against 3.11 while ruff targets 3.12, leading to
silent mismatches in type behavior
**Effort:** 15m
**Area:** Configuration

`pyproject.toml` has two conflicting Python version targets:
- `[tool.ruff]` section: `target-version = "py312"`
- `[tool.pyright]` section: `pythonVersion = "3.11"`
- `.python-version` file: `3.12`

**Fix:** Align all to `3.12` (matching `.python-version` and ruff).

---

### TD-006: PostToolUse Hooks Fire on Every Tool Call (No Matcher)

**Severity:** HIGH
**Impact:** 11 Python processes spawn on EVERY tool call. Total PostToolUse timeout
budget: 75s. Real-world latency per tool use is significant.
**Effort:** 4h
**Area:** Infrastructure

The PostToolUse event in `settings.json` has `"matcher": ""` (empty = matches everything).
11 hooks fire on every Read, Write, Edit, Bash, Glob, Grep call. Most of these hooks
are only relevant to specific tool types:
- `post_batch_cascading.py` -- only relevant to Write/Edit
- `agent_creation_trigger.py` -- only relevant to Write
- `agent_index_updater.py` -- only relevant to Write/Edit on agent files
- `pipeline_checkpoint.py` -- only relevant to Write
- `pipeline_phase_gate.py` -- only relevant to Write
- `pipeline_orchestrator.py` -- only relevant to Write

**Fix:** Add matchers (e.g., `"matcher": "Write|Edit"`) to hooks that only care about
write operations. This could reduce PostToolUse hook invocations by 60-70%.

---

### TD-007: `docs/` Directory Still Has Content Despite Being PROHIBITED

**Severity:** HIGH
**Impact:** New files keep being written to `docs/` (including this document) despite
`paths.py` declaring it PROHIBITED. The directory contract says use `reference/`.
**Effort:** 2h
**Area:** Architecture

The `docs/` directory contains active subdirectories: `architecture/`, `frontend/`,
`plans/`, `prd/`, `prompts/`, `reports/`, `reviews/`, `stories/`. However, `paths.py`
has `docs/` in its PROHIBITED list and `directory-contract.md` says to use `reference/`.

The CLAUDE.md itself says plans go to `docs/plans/` -- contradicting the directory contract.

**Fix:** Decide: either un-prohibit `docs/` in the directory contract (pragmatic) or
migrate all `docs/` content to `reference/` and update all references. The current
state of having a PROHIBITED directory that is actively used is self-contradictory.

---

### TD-008: `agents/minds/` Directory Still Exists on Disk

**Severity:** HIGH
**Impact:** Two competing directories for the same agents creates confusion about which
is canonical
**Effort:** 15m
**Area:** Architecture

`agents/minds/` still exists with 6 subdirectories. `agents/external/` has the same
agents plus 7 additional ones. The minds directory is a strict subset of external.

**Fix:** Delete `agents/minds/` after fixing TD-004.

---

## 2. Code Quality Debts

### TD-009: 352 Ruff Lint Errors

**Severity:** HIGH
**Impact:** Code quality degradation, unused imports bloating memory, potential bugs from
unused variables and f-string placeholders
**Effort:** 2h (316 auto-fixable)
**Area:** Code Quality

Current `ruff check` returns 352 errors across `core/` and `.claude/hooks/`. Breakdown:
- 109 F541 (f-string without placeholders -- likely bugs or dead format strings)
- 45 UP006 (non-PEP585 annotations)
- 38 F401 (unused imports)
- 34 I001 (unsorted imports)
- 33 UP017 (datetime timezone UTC)
- 26 UP015 (redundant open modes)
- 8 F841 (unused variables)
- 2 F601 / B023 (potential bugs)

316 of 352 are auto-fixable with `ruff check --fix`.

**Fix:** Run `ruff check --fix core/ .claude/hooks/` for the 316 auto-fixable errors.
Manually fix the remaining 36.

---

### TD-010: 50 Tests for 29,640 Lines of Python (~0.17% Coverage)

**Severity:** HIGH
**Impact:** Zero safety net for refactoring. Any change to pipeline, RAG, or agent code
is a leap of faith.
**Effort:** 80h+ (phased over multiple sprints)
**Area:** Code Quality

The test-to-code ratio is critically low. 50 tests cover:
- 44 layer classification tests
- 13 RAG chunker tests
- 22 bucket processor tests
- 0 tests for pipeline (biggest code area)
- 0 tests for MCE
- 0 tests for hooks
- 0 tests for entity resolution
- 0 tests for dossier compilation

**Fix:** Phased approach:
- Phase 1 (20h): Unit tests for `core/intelligence/pipeline/` (highest business value)
- Phase 2 (20h): Unit tests for `core/intelligence/rag/` (second highest)
- Phase 3 (20h): Integration tests for hook system
- Phase 4 (20h): Tests for entities, dossier, agents modules

---

### TD-011: 34 Files Use Hardcoded `BASE_DIR` Instead of `core.paths`

**Severity:** MEDIUM
**Impact:** If directory structure changes, these 34 files break while the 25 files using
`core.paths` survive. Inconsistent path resolution across the codebase.
**Effort:** 6h
**Area:** Code Quality

34 Python files in `core/intelligence/` define their own `BASE_DIR` via
`Path(__file__).resolve().parent.parent...` instead of importing from `core.paths`.
25 files correctly use `core.paths`. This creates two parallel path resolution systems.

**Fix:** Refactor all 34 files to import constants from `core.paths`. Remove all
`BASE_DIR` definitions.

---

### TD-012: 22 TODO/FIXME/HACK Comments in Production Code

**Severity:** LOW
**Impact:** Untracked technical debt hiding in comments
**Effort:** 4h (triage and convert to issues)
**Area:** Code Quality

22 TODO/FIXME/HACK comments exist in `core/intelligence/`. These represent untracked
debt items that should be converted to GitHub issues or resolved.

**Fix:** Audit all 22 comments. Convert actionable ones to GitHub issues. Remove stale
ones. Fix trivial ones inline.

---

### TD-013: 109 f-strings Without Placeholders (F541)

**Severity:** MEDIUM
**Impact:** 109 instances where `f"string"` is used but no `{variable}` appears inside.
These are either bugs (placeholder was deleted) or unnecessary f-prefixes.
**Effort:** 2h
**Area:** Code Quality

This is the single largest lint error category. Each instance needs manual review to
determine if it is:
a) A bug (someone removed the variable but kept the f-prefix)
b) An unnecessary f-prefix (should be a plain string)

**Fix:** Review each F541 instance. This is partially auto-fixable by ruff but each case
needs confirmation that no placeholder was accidentally removed.

---

## 3. Configuration Debts

### TD-014: CI/CD Test Path Points to Non-Existent Directory

**Severity:** CRITICAL
**Impact:** CI pipeline runs zero tests silently. The `|| echo` fallback masks the failure.
**Effort:** 15m
**Area:** Infrastructure

`.github/workflows/verification.yml` runs:
```
python -m pytest scripts/tests/ -v --tb=short || echo "Some tests failed or no tests found"
```

The directory `scripts/tests/` does not exist. Tests are at `tests/python/`. The
`|| echo` causes this to silently succeed, meaning CI never runs any tests.

**Fix:** Change `scripts/tests/` to `tests/python/` in `verification.yml`. Remove the
`|| echo` fallback so test failures actually fail the CI.

---

### TD-015: `memory_capture.py` Timeout Set to 30ms

**Severity:** MEDIUM
**Impact:** Hook likely times out on every invocation, silently failing. Standard timeout
is 5000ms.
**Effort:** 5m
**Area:** Configuration

In `settings.json`, `memory_capture.py` has `"timeout": 30` (30ms). Every other hook
has 5000-10000ms. Python process startup alone exceeds 30ms, meaning this hook
effectively never completes.

**Fix:** Change timeout to 5000ms or determine if the hook should be removed entirely.

---

### TD-016: `pipeline` Optional Dependency Group is Redundant

**Severity:** LOW
**Impact:** Confusing for users -- installing `[pipeline]` gives nothing beyond base deps
**Effort:** 5m
**Area:** Configuration

In `pyproject.toml`, the `[pipeline]` optional group only contains `PyYAML`, which is
already a required dependency. This group serves no purpose.

**Fix:** Either remove the group or add actual pipeline-specific dependencies to it.

---

### TD-017: `.gitignore` Tests Contradiction (Line 278 vs 652)

**Severity:** HIGH
**Impact:** Tests are whitelisted on line 278 (`!tests/`) then denied on line 652
(`tests/`). The LAST rule wins in gitignore, so tests are effectively ignored.
**Effort:** 15m
**Area:** Configuration

The 694-line whitelist-based `.gitignore` has a contradiction:
- Line 278-279: `!tests/` and `!tests/**` (whitelist)
- Line 652: `tests/` (deny -- in BLOCO 7 "HYGIENE DENY")

Since gitignore processes rules top-to-bottom and last match wins, line 652 overrides
lines 278-279, making tests gitignored.

**Fix:** Remove line 652 (`tests/` in BLOCO 7). Tests should be L1 (tracked in git).

---

### TD-018: JSON State Files Have No Runtime Schema Validation

**Severity:** MEDIUM
**Impact:** Corrupted or malformed state JSON files cause silent pipeline failures.
No validation on read means garbage-in-garbage-out.
**Effort:** 8h
**Area:** Architecture

10+ JSON state files in `.claude/mission-control/` are read by hooks and pipeline code
without any schema validation. `core/schemas/` contains 7 JSON schemas but zero Python
code references them -- they are documentation-only artifacts.

**Fix:** Add schema validation at read time for critical state files
(`MISSION-STATE.json`, `FIREFLIES-STATE.json`, `BATCH-REGISTRY.json`). Use the existing
schemas in `core/schemas/` or consolidate into a validation utility.

---

## 4. Infrastructure Debts

### TD-019: No CI Test Execution (Zero Effective Test Coverage in CI)

**Severity:** CRITICAL
**Impact:** Pull requests merge without any test validation. Combined with TD-014 (wrong
test path), CI provides false confidence.
**Effort:** 4h
**Area:** Infrastructure

The verification workflow exists but:
1. Points to wrong test directory (TD-014)
2. Suppresses failures with `|| echo`
3. Does not run ruff lint check
4. Does not run pyright type check
5. Does not validate JSON integrity

**Fix:** Rewrite `verification.yml` to:
1. Run `ruff check core/ .claude/hooks/` (fail on errors)
2. Run `python3 -m pytest tests/python/ -v` (fail on failures)
3. Run `python3 core/intelligence/validation/validate_json_integrity.py`
4. Run `node bin/pre-publish-gate.js`

---

### TD-020: Hook System Total Timeout Budget is 195 Seconds

**Severity:** MEDIUM
**Impact:** Worst-case scenario: a single interaction cycle (prompt + tool use + stop)
triggers 33 hooks with combined timeout of 195 seconds. In practice, hooks exit early,
but the architectural budget is concerning.
**Effort:** 8h (consolidation project)
**Area:** Infrastructure

Breakdown:
- SessionStart: 4 hooks, 25s budget
- UserPromptSubmit: 7 hooks, 40s budget
- PreToolUse: 5 hooks, 25s budget (only fires on Write|Edit)
- PostToolUse: 11 hooks, 75s budget (fires on EVERY tool call)
- Stop: 6 hooks, 35s budget

Each hook spawns a separate Python process.

**Fix:** Consolidate related hooks into fewer scripts with internal routing:
- Merge `agent_creation_trigger`, `agent_index_updater`, `agent_memory_persister`,
  `claude_md_agent_sync` into a single `agent_lifecycle.py`
- Merge `pipeline_checkpoint`, `pipeline_phase_gate`, `pipeline_orchestrator` into
  a single `pipeline_hooks.py`
- Merge `session_end`, `continuous_save`, `session_index` into `session_lifecycle.py`

---

### TD-021: `core/.claude/` Rogue Directory

**Severity:** LOW
**Impact:** Confusing directory that should not exist inside the core engine.
Contains only `.DS_Store` and an empty `sessions/` subdirectory.
**Effort:** 5m
**Area:** Infrastructure

**Fix:** Delete `core/.claude/` entirely.

---

### TD-022: `outputs/` Directory Exists Outside Directory Contract

**Severity:** LOW
**Impact:** Rogue directory not tracked by `paths.py` or `directory-contract.md`.
Contains only `.DS_Store` and an `execute/` subdirectory.
**Effort:** 5m
**Area:** Infrastructure

**Fix:** Determine if content should move to `artifacts/` (per directory contract) or
delete if empty.

---

### TD-023: 67 `.DS_Store` Files and 41 `.pyc` Files in Working Tree

**Severity:** LOW
**Impact:** Noise in file listings, potential git tracking of OS artifacts
**Effort:** 15m
**Area:** Infrastructure

**Fix:** Add `.DS_Store` and `__pycache__/` to the NEVER block (BLOCO 1) of `.gitignore`.
Run `find . -name ".DS_Store" -delete` and `find . -name "*.pyc" -delete`.

---

## 5. Documentation Debts

### TD-024: CLAUDE.md Architecture Diagram Shows Deprecated Directories

**Severity:** HIGH
**Impact:** The primary project instructions file (read by every Claude Code session)
contains stale directory names, leading AI sessions astray
**Effort:** 30m
**Area:** Documentation

`.claude/CLAUDE.md` architecture diagram includes:
- `workspace/domains/` (removed in S13)
- `workspace/team/` (removed in S13, migrated to `gente-cultura/equipe/`)
- `agents/minds/` in Layer System table (deprecated, now `agents/external/`)

**Fix:** Update CLAUDE.md architecture diagram and Layer System table to match the
current directory-contract.md (v4.0.0).

---

### TD-025: `reference/` Docs Reference Deprecated Paths

**Severity:** MEDIUM
**Impact:** Reference documentation misleads developers and AI sessions
**Effort:** 2h
**Area:** Documentation

- `reference/LAYERS.md` references `docs/` as L1 path (6 occurrences)
- `reference/architecture/BROWNFIELD-MEGABRAIN.md` references `knowledge/workspace/`
  (3 occurrences, deprecated since S12)
- `reference/MEGABRAIN-3D-ARCHITECTURE.md` references `agents/minds/` (1 occurrence)

**Fix:** Update all reference docs to match current directory structure.

---

### TD-026: Missing Capstone Documentation

**Severity:** MEDIUM
**Impact:** No single document explains the full 3D architecture to a new developer
**Effort:** 16h
**Area:** Documentation

The following documents are referenced in code/rules but do not exist in their
documented locations:
- `reference/IMPLEMENTATION-LOG.md` (referenced in directory-contract.md routing table)
- `reference/ONBOARDING-GUIDE.md` (referenced in directory-contract.md routing table)

`reference/MEGABRAIN-3D-ARCHITECTURE.md` exists but may be outdated (references
`agents/minds/`).

**Fix:** Create IMPLEMENTATION-LOG.md and ONBOARDING-GUIDE.md. Update
MEGABRAIN-3D-ARCHITECTURE.md.

---

### TD-027: Rule Files Total ~8,000 Lines of Markdown

**Severity:** LOW
**Impact:** 17 rule documents totaling ~8,000 lines create a massive instruction set.
Many rules overlap or contradict (e.g., CLAUDE.md says `docs/plans/` but directory
contract prohibits `docs/`).
**Effort:** 16h
**Area:** Documentation

**Fix:** Audit all 17 rule files for contradictions, overlaps, and obsolete rules.
Consolidate where possible. The lazy-loading architecture is sound but the content
needs pruning.

---

## 6. Security Debts

### TD-028: No `.env` File Exists -- System Runs Without API Keys

**Severity:** HIGH
**Impact:** Pipeline features (Whisper transcription, vector RAG, Fireflies sync) are
non-functional without the `.env` file. No setup validation confirms keys exist.
**Effort:** 1h
**Area:** Security

The system expects `OPENAI_API_KEY`, `VOYAGE_API_KEY`, `FIREFLIES_API_KEY` in `.env`
but the file does not exist in the working tree. The `/setup` command should create it
but there is no startup guard that verifies it.

**Fix:** Add a startup check (in `session_start.py` or CLI entry point) that warns if
`.env` is missing or if required keys are absent.

---

### TD-029: `.mcp.json` Contains Hardcoded Absolute Path

**Severity:** MEDIUM
**Impact:** The filesystem MCP server configuration contains `/Users/thiagofinch/...`
which breaks for any other user or machine
**Effort:** 15m
**Area:** Security

**Fix:** Use relative path or `${HOME}` variable interpolation for the filesystem MCP
server path.

---

### TD-030: No Credential Rotation Policy

**Severity:** MEDIUM
**Impact:** API keys (Fireflies bearer token, N8N API key) have no documented rotation
schedule or expiry monitoring
**Effort:** 2h (documentation + optional automation)
**Area:** Security

**Fix:** Document rotation schedule in `reference/SECURITY.md`. Consider adding a
`session_start.py` check that warns if API keys are older than 90 days (track creation
date in `.env` comment).

---

### TD-031: RAG Business Index Not Built

**Severity:** HIGH
**Impact:** Business knowledge (meeting insights, call transcripts) cannot be searched
semantically. The `rag_business` path is defined in `paths.py` but the index is empty.
**Effort:** 2h
**Area:** Architecture

**Fix:** Run the chunker + BM25 index builder against `knowledge/business/` content.

---

## 7. Matriz Preliminar

| ID | Debt | Area | Severity | Impact | Effort | Priority |
|----|------|------|----------|--------|--------|----------|
| TD-001 | 21 duplicate Python modules | Code Quality | CRITICAL | Bug divergence, dead code | 3h | P0 |
| TD-002 | AGENT-INDEX.yaml stale paths | Configuration | CRITICAL | Broken agent discovery | 1h | P0 |
| TD-003 | Version mismatch (1.4.0 vs 1.3.0) | Configuration | CRITICAL | User confusion | 10m | P0 |
| TD-004 | 51 stale `agents/minds/` references | Code Quality | CRITICAL | Broken path resolution | 2h | P0 |
| TD-014 | CI tests point to non-existent dir | Infrastructure | CRITICAL | Zero CI test execution | 15m | P0 |
| TD-005 | Python version target inconsistency | Configuration | HIGH | Silent type check mismatches | 15m | P1 |
| TD-006 | PostToolUse hooks fire on ALL tools | Infrastructure | HIGH | Performance degradation | 4h | P1 |
| TD-007 | `docs/` PROHIBITED but actively used | Architecture | HIGH | Self-contradictory contract | 2h | P1 |
| TD-008 | `agents/minds/` dir still exists | Architecture | HIGH | Competing directories | 15m | P1 |
| TD-009 | 352 ruff lint errors | Code Quality | HIGH | Code quality, potential bugs | 2h | P1 |
| TD-010 | 50 tests for 29,640 lines (~0.17%) | Code Quality | HIGH | No refactoring safety net | 80h+ | P1 |
| TD-017 | `.gitignore` tests contradiction | Configuration | HIGH | Tests not tracked in git | 15m | P1 |
| TD-019 | No effective CI test execution | Infrastructure | CRITICAL | PRs merge untested | 4h | P0 |
| TD-024 | CLAUDE.md stale architecture diagram | Documentation | HIGH | AI sessions misled | 30m | P1 |
| TD-028 | No `.env` file, no startup guard | Security | HIGH | Pipeline features broken | 1h | P1 |
| TD-031 | RAG business index not built | Architecture | HIGH | Business search disabled | 2h | P1 |
| TD-011 | 34 files use hardcoded BASE_DIR | Code Quality | MEDIUM | Inconsistent path resolution | 6h | P2 |
| TD-013 | 109 f-strings without placeholders | Code Quality | MEDIUM | Potential bugs | 2h | P2 |
| TD-015 | memory_capture.py 30ms timeout | Configuration | MEDIUM | Hook always times out | 5m | P2 |
| TD-018 | No runtime schema validation | Architecture | MEDIUM | Silent state corruption | 8h | P2 |
| TD-020 | 195s total hook timeout budget | Infrastructure | MEDIUM | Process spawn overhead | 8h | P2 |
| TD-025 | Reference docs stale paths | Documentation | MEDIUM | Dev/AI misdirection | 2h | P2 |
| TD-026 | Missing capstone docs | Documentation | MEDIUM | Onboarding gap | 16h | P2 |
| TD-029 | Hardcoded absolute path in .mcp.json | Security | MEDIUM | Breaks on other machines | 15m | P2 |
| TD-030 | No credential rotation policy | Security | MEDIUM | Stale API keys risk | 2h | P2 |
| TD-012 | 22 TODO/FIXME comments | Code Quality | LOW | Untracked debt | 4h | P3 |
| TD-016 | Redundant `[pipeline]` dep group | Configuration | LOW | User confusion | 5m | P3 |
| TD-021 | `core/.claude/` rogue directory | Infrastructure | LOW | Confusing layout | 5m | P3 |
| TD-022 | `outputs/` dir outside contract | Infrastructure | LOW | Rogue directory | 5m | P3 |
| TD-023 | 67 .DS_Store + 41 .pyc files | Infrastructure | LOW | Noise | 15m | P3 |
| TD-027 | 8,000 lines of rule files | Documentation | LOW | Instruction bloat | 16h | P3 |

---

## 8. Priority Summary

### P0 -- Fix This Sprint (estimated 6.5h)

| ID | Debt | Effort |
|----|------|--------|
| TD-003 | Sync version numbers | 10m |
| TD-014 | Fix CI test path | 15m |
| TD-001 | Delete 21 duplicate modules | 3h |
| TD-004 | Fix 51 `agents/minds/` references | 2h |
| TD-002 | Fix AGENT-INDEX.yaml paths | 1h |
| TD-019 | Fix CI pipeline to actually run tests | (overlaps TD-014) |

### P1 -- Fix Next Sprint (estimated 12h excl. test coverage)

| ID | Debt | Effort |
|----|------|--------|
| TD-005 | Align Python version targets | 15m |
| TD-008 | Delete `agents/minds/` directory | 15m |
| TD-017 | Fix gitignore tests contradiction | 15m |
| TD-015 | Fix memory_capture timeout | 5m |
| TD-024 | Update CLAUDE.md diagram | 30m |
| TD-028 | Add .env startup guard | 1h |
| TD-009 | Fix 352 ruff lint errors | 2h |
| TD-006 | Add PostToolUse matchers | 4h |
| TD-007 | Resolve docs/ vs reference/ | 2h |
| TD-031 | Build RAG business index | 2h |
| TD-010 | Test coverage (Phase 1 only) | 20h |

### P2 -- Fix Next Quarter

TD-011, TD-013, TD-018, TD-020, TD-025, TD-026, TD-029, TD-030

### P3 -- Nice To Have

TD-012, TD-016, TD-021, TD-022, TD-023, TD-027

---

## 9. Questions for Reviewers

### For the System Owner

1. **docs/ vs reference/:** The directory contract prohibits `docs/` and mandates
   `reference/`, but `CLAUDE.md` sends plans to `docs/plans/` and active architecture
   docs live in `docs/architecture/`. Which is canonical? Should we un-prohibit `docs/`
   or actually migrate everything?

2. **agents/minds/ data:** The `agents/minds/` directory has 6 agent subdirectories that
   also exist in `agents/external/`. Are the copies in `minds/` older versions that can
   be safely deleted, or do some have unique content?

3. **Hook consolidation appetite:** Reducing from 33 hooks to ~15 would halve process
   spawning overhead. Is the current granularity intentional (each hook is independently
   deployable) or accidental (grew organically)?

4. **Test coverage target:** The current 0.17% is effectively zero. What is the minimum
   acceptable coverage before the next npm publish? Suggestion: 40% on
   `core/intelligence/pipeline/` as first milestone.

5. **Rule file pruning:** 17 rule files with ~8,000 lines of Markdown contain overlapping
   and occasionally contradictory instructions. Is there appetite for an audit pass to
   consolidate to ~10 files with ~4,000 lines?

### For the Pipeline Owner

6. **MCE pipeline stability:** The MCE sub-pipeline in `core/intelligence/pipeline/mce/`
   has 8 modules but zero tests. How stable is it? Should it be marked experimental
   until tests exist?

7. **Fireflies vs Read.ai:** Both integrations harvest meeting transcripts. Is there a
   plan to consolidate to one, or do both serve different meeting types?

8. **RAG business index:** The `rag_business` path is defined but the index is not built.
   Is this blocked by missing content in `knowledge/business/`, or is it a build step
   that was never run?

### For the DevOps Owner

9. **CI pipeline gaps:** The verification workflow exists but runs tests against a
   non-existent directory. Has this been noticed? Are there other CI jobs that actually
   validate code?

10. **npm publish safety:** The `prepublishOnly` script runs `pre-publish-gate.js`. Does
    this gate catch the issues identified here (version mismatch, lint errors, test
    failures)?

---

## Appendix: Methodology

This assessment was produced by:

1. Reading the Phase 1 system architecture document
   (`docs/architecture/system-architecture.md`)

2. Validating every claim against the live codebase:
   - Running `ruff check` to verify lint status
   - Running `pytest --collect-only` to verify test count
   - Using `find` and `grep` to verify file counts and stale references
   - Checking `settings.json` to verify hook configuration
   - Inspecting `.gitignore` for contradictions
   - Checking CI workflows for correct test paths

3. Identifying debts not covered in Phase 1:
   - CI test path pointing to non-existent directory (TD-014)
   - CI zero effective test execution (TD-019)
   - `.gitignore` tests contradiction (TD-017)
   - f-string placeholder bugs (TD-013)
   - Python version target inconsistency (TD-005)
   - JSON schema non-usage (TD-018)
   - .DS_Store / .pyc pollution (TD-023)

4. Phases 2 (Database) and 3 (Frontend/UX) were correctly skipped -- this system has
   no database (filesystem-only) and no frontend UI (CLI-only).

---

**END OF DRAFT**

*Awaiting specialist review before finalization.*
