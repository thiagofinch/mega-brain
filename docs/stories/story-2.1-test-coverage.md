# Story 2.1: Testing -- Restore Test Coverage

> **Story ID:** STORY-TD-2.1
> **Epic:** EPIC-TD-001
> **Sprint:** 2
> **Priority:** P1 HIGH
> **Debitos:** TD-017 (.gitignore contradicts test tracking), TD-038 (test regression 248 -> 50), TD-010 Phase 1 (pipeline unit tests)

---

## Context

Three testing problems compound into a single story:

1. The `.gitignore` has a contradiction: line 278-279 whitelist `tests/`, but line 652 denies `tests/` again. Since last-match-wins in gitignore, tests are effectively invisible to git. No test file has ever been tracked.

2. A previous session recorded 248 tests passing. The current count is 50. The regression of 198 tests is unexplained and undocumented. Some tests may have been removed, relocated, or the test infrastructure changed.

3. Test coverage for `core/intelligence/pipeline/` is 0%. This is the most critical module in the system -- it processes all knowledge ingestion. TD-010 Phase 1 calls for 20h of pipeline tests to reach ~40% coverage.

This story addresses all three: fix the gitignore, investigate the regression, and build the first round of pipeline tests.

---

## Tasks

### TD-017: Fix .gitignore Contradiction

- [ ] Open `.gitignore`
- [ ] Find line 652 (in BLOCO 7 "HYGIENE DENY"): `tests/`
- [ ] Delete that line
- [ ] Save and run `git status` -- expect a large diff as test files appear as "new" to git
- [ ] Stage all test files: `git add tests/`
- [ ] Commit with message explaining this is a gitignore fix, not new tests

### TD-038: Investigate Test Regression

- [ ] Run `python3 -m pytest tests/python/ -v --co` (collect only, no execution) to see current test inventory
- [ ] Check git log for test-related changes: `git log --oneline --all -- tests/`
- [ ] Check if test files exist outside `tests/python/` (some may have been moved): `find . -name "test_*.py" -not -path "./tests/*" -not -path "./.venv*"`
- [ ] Check if test files are in `.data/` or other gitignored directories
- [ ] Document findings in a short section at the end of this story file or in a separate `docs/reports/test-regression-investigation.md`
- [ ] If missing tests can be recovered, restore them. If they were intentionally removed, document why.

### TD-010 Phase 1: Pipeline Unit Tests

Write unit tests for the most critical pipeline modules. Target: >= 40% coverage of `core/intelligence/pipeline/`.

**Priority modules to test (by risk):**

- [ ] `scope_classifier.py` -- Tests for business/external/personal classification
- [ ] `smart_router.py` -- Tests for routing decisions based on scope
- [ ] `batch_auto_creator.py` -- Tests for automatic batch creation from inbox
- [ ] `inbox_organizer.py` -- Tests for file organization and naming
- [ ] `autonomous_processor.py` -- Tests for end-to-end pipeline processing

**Test approach:**

- [ ] Create `tests/python/test_pipeline/` directory structure
- [ ] Each test file mirrors the module: `test_scope_classifier.py`, etc.
- [ ] Use pytest fixtures for common test data (sample transcripts, mock files)
- [ ] Mock external API calls (Fireflies, OpenAI) -- tests must run offline
- [ ] Focus on happy paths first, then edge cases

**Coverage target:**

- [ ] Run `pytest --cov=core.intelligence.pipeline tests/python/test_pipeline/ --cov-report=term-missing`
- [ ] Target: >= 40% line coverage for `core/intelligence/pipeline/`

---

## Acceptance Criteria

- [ ] `git ls-files tests/python/ | wc -l` returns > 0 (tests are tracked by git)
- [ ] `.gitignore` line 652 no longer denies `tests/`
- [ ] Test regression investigation documented (what happened to 198 tests)
- [ ] `python3 -m pytest tests/python/ -v` passes with more than 50 tests
- [ ] `core/intelligence/pipeline/` has unit tests covering >= 40% of lines
- [ ] All tests run without network access (external APIs are mocked)

---

## Technical Notes

**The gitignore file is 694 lines long.** It uses a whitelist strategy (line 24 has `*` to deny everything, then `!` patterns whitelist specific paths). The contradiction happens because BLOCO 7 (line ~650) re-denies `tests/` after BLOCO 2 (line ~278) whitelisted it. Last match wins.

**Expected git diff after fix:** All files in `tests/python/` will appear as "new" to git. This is expected and correct. The PR description should explain this clearly.

**Test regression hypotheses:**
- Tests may have been moved to a directory not under `tests/python/`
- Tests may reference modules that were reorganized (the 21 duplicates)
- The test infrastructure (conftest, fixtures) may have changed
- Tests may have been accidentally deleted during a reorganization

**Pipeline test challenges:**
- `scope_classifier.py` likely uses LLM calls -- these MUST be mocked
- File I/O is heavy -- use `tmp_path` fixture for isolation
- Some modules depend on state files in `.claude/mission-control/` -- create test fixtures

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Fix .gitignore + stage tests (TD-017) | 0.25h |
| Investigate test regression (TD-038) | 1h |
| Write pipeline unit tests (TD-010 Phase 1) | 5.5h |
| Coverage analysis + gap filling | 1.25h |
| **Total** | **~8h** |

---

## Dependencies

| Dependency | Reason |
|------------|--------|
| Story 1.2 (CI rewrite) | CI must be functional for new tests to be validated automatically |
| Story 1.3 (duplicate modules) | Duplicate modules should be removed first so tests import from canonical locations |

---

## Definition of Done

- [ ] Tests are tracked by git (gitignore fix committed)
- [ ] Test regression investigation complete and documented
- [ ] Pipeline test suite exists at `tests/python/test_pipeline/`
- [ ] >= 40% line coverage of `core/intelligence/pipeline/`
- [ ] All tests pass: `python3 -m pytest tests/python/ -v`
- [ ] CI runs the new tests automatically (verified via PR)
- [ ] No test depends on network access or external API availability
