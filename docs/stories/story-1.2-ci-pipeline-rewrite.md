# Story 1.2: CI -- Rewrite Quality Pipeline

> **Story ID:** STORY-TD-1.2
> **Epic:** EPIC-TD-001
> **Sprint:** 1
> **Priority:** P0 CRITICAL
> **Debitos:** TD-014 (CI tests point to non-existent directory), TD-019 (CI pipeline is entirely decorative)

---

## Context

The CI pipeline at `.github/workflows/verification.yml` is the most severe structural debt in the project. It is not "missing tests" -- it is architecturally designed to always pass. Level 6 (Final) hardcodes "PASSED" for all 6 levels regardless of actual results. Level 2 checks a directory (`scripts/tests/`) that does not exist, so tests silently skip. Level 1 only lints the first 50 Python files out of 120+. Every PR in project history has merged without actual validation.

This is worse than having no CI at all because it creates a false sense of security.

---

## Tasks

### TD-014: Fix CI Test Path

- [ ] Open `.github/workflows/verification.yml`
- [ ] Find the test step that checks `if [ -d "scripts/tests" ]`
- [ ] Replace `scripts/tests/` with `tests/python/`
- [ ] Remove the `|| echo "info message"` fallback that allows silent skip
- [ ] Ensure test failures cause the step to fail (non-zero exit code propagates)

### TD-019: Rewrite CI Pipeline

- [ ] Delete the existing 6-level structure (it is decorative, not fixable)
- [ ] Create a new `verification.yml` with these steps:

**Step 1: Setup**
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # NOT 3.11 -- matches .python-version
- run: pip install ruff pyyaml pytest
```

**Step 2: Lint**
```yaml
- name: Lint
  run: ruff check core/ .claude/hooks/ --output-format=github
```

**Step 3: Tests**
```yaml
- name: Tests
  run: python3 -m pytest tests/python/ -v --tb=short
```

**Step 4: Integrity**
```yaml
- name: JSON Integrity
  run: python3 core/intelligence/validation/validate_json_integrity.py
```

**Step 5: Pre-publish Gate**
```yaml
- name: Pre-publish Gate
  run: node bin/pre-publish-gate.js
```

- [ ] Remove ALL hardcoded "PASSED" strings
- [ ] Remove the final summary step that reports fake results
- [ ] Ensure each step's exit code determines pass/fail (no `|| true`, no `2>/dev/null`)
- [ ] Set `fail-fast: true` on the job so failures stop early

### Validation

- [ ] Push a branch with a deliberately failing test and verify CI marks it as FAILED
- [ ] Push a branch with a ruff error and verify CI marks it as FAILED
- [ ] Push a clean branch and verify CI marks it as PASSED

---

## Acceptance Criteria

- [ ] CI runs `ruff check` against ALL Python files in `core/` and `.claude/hooks/` (not first 50)
- [ ] CI runs `pytest tests/python/ -v` against the actual test directory
- [ ] CI uses Python 3.12 (not 3.11)
- [ ] CI step failure causes the workflow to fail (no silent skipping)
- [ ] No hardcoded "PASSED" strings exist in `verification.yml`
- [ ] A PR with a failing test is blocked by CI (verified by pushing one)

---

## Technical Notes

**Current verification.yml structure (to be replaced):**

| Level | Claims To Check | Actually Does |
|-------|----------------|---------------|
| Level 1: Lint | Python syntax | Only first 50 .py files, never runs ruff |
| Level 2: Tests | Run tests | Checks non-existent scripts/tests/, skips |
| Level 3: Integrity | Check imports | Prints "passed" without checking |
| Level 4: Structure | Validate dirs | Checks 6 dirs exist (always true) |
| Level 5: Security | Scan secrets | Basic grep, warns but never fails |
| Level 6: Final | Report | Hardcodes PASSED for all 6 levels |

**The new pipeline should be ~40 lines, not 200+.** Simplicity is the feature. Each step either passes or fails. No wrapper scripts, no conditional skipping, no "info" messages that hide failures.

**Python version:** `.python-version` says 3.12. `pyproject.toml` ruff targets 3.12. CI currently uses 3.11 (TD-005). Aligning to 3.12 is part of this rewrite.

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Fix test path (TD-014) | 0.25h |
| Rewrite verification.yml (TD-019) | 2h |
| Test with deliberate failures | 1h |
| Iterate on CI config if issues arise | 0.75h |
| **Total** | **4h** |

---

## Dependencies

| Dependency | Reason |
|------------|--------|
| Story 1.1 (security) | Should be done first but not a hard blocker |
| Story 1.3 (duplicates) | CI should run on a clean codebase. Ideally duplicates are removed first so ruff count is accurate. Soft dependency. |
| TD-005 (Python version) | Folded into this story -- CI will use 3.12 |

---

## Definition of Done

- [ ] New `verification.yml` is committed and replaces the old one
- [ ] CI passes on a clean branch (ruff clean + all tests pass)
- [ ] CI fails on a branch with a failing test (verified)
- [ ] CI fails on a branch with a ruff error (verified)
- [ ] Python version in CI is 3.12
- [ ] Zero hardcoded "PASSED" strings in the workflow file
- [ ] No `|| true` or `2>/dev/null` patterns in the workflow file
