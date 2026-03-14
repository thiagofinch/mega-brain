# Story 2.2: Hooks -- Standardize Error Handling

> **Story ID:** STORY-TD-2.2
> **Epic:** EPIC-TD-001
> **Sprint:** 2
> **Priority:** P1 HIGH
> **Debitos:** TD-034 (inconsistent hook error patterns), TD-015 (memory_capture.py 30ms timeout)

---

## Context

All 37 hooks in `.claude/hooks/` have `sys.exit()` calls, but error handling patterns vary wildly. Some hooks have 8-9 `sys.exit()` calls with proper error codes (0=success, 1=warning, 2=block). Some hooks catch ALL exceptions and exit silently with `sys.exit(0)`, effectively swallowing errors. `memory_capture.py` has a 30ms timeout -- Python process startup alone takes longer than that, making the hook a permanent no-op.

The Anthropic Standards document (`.claude/rules/ANTHROPIC-STANDARDS.md`) defines the correct exit code convention, but compliance is inconsistent.

This story standardizes error handling across all hooks WITHOUT consolidating them (consolidation is a separate P2 item, TD-020).

---

## Tasks

### TD-015: Fix memory_capture.py Timeout

- [ ] Open `.claude/settings.json`
- [ ] Find `memory_capture.py` entry
- [ ] Change `"timeout": 30` to `"timeout": 5000` (or remove the hook entirely if it serves no purpose)
- [ ] If changing timeout: test that the hook actually runs by adding a debug log
- [ ] If removing: document why in a commit message

### TD-034: Audit All 37 Hooks

Create an audit spreadsheet (or markdown table) tracking each hook:

- [ ] For each hook in `.claude/hooks/`:

| Hook | Exit Codes Used | Catch-All Pattern | Compliant | Fix Needed |
|------|----------------|-------------------|-----------|------------|
| `hook_name.py` | 0, 1, 2 | No | Yes | - |
| `hook_name.py` | 0 only | Yes (swallows errors) | No | Add proper exit codes |
| ... | ... | ... | ... | ... |

### TD-034: Standardize Error Handling

For each non-compliant hook:

- [ ] Replace catch-all `except Exception: sys.exit(0)` with proper error handling:

```python
try:
    # main logic
    sys.exit(0)  # success
except NonCriticalError as e:
    print(json.dumps({"warning": str(e)}))
    sys.exit(1)  # warning -- continue but notify
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(2)  # block -- stop execution
```

- [ ] Ensure every hook has exactly 3 exit paths: success (0), warning (1), error (2)
- [ ] Remove any `2>/dev/null || true` patterns
- [ ] Add structured JSON output for warnings and errors (not bare print statements)

**Hooks with known issues (from assessment):**

- [ ] Fix hooks that catch all exceptions and exit 0 (identify by searching for `except.*:\s*sys.exit\(0\)`)
- [ ] Fix hooks that use bare `except:` without specifying exception type
- [ ] Fix hooks that print unstructured error messages
- [ ] Verify `memory_capture.py` is either functional (with 5000ms timeout) or removed

### Validation

- [ ] Run each modified hook manually to verify it starts without errors
- [ ] Test warning path: trigger a non-critical condition and verify exit code 1
- [ ] Test error path: trigger an error condition and verify exit code 2
- [ ] Start a new Claude Code session to verify hooks fire without issues

---

## Acceptance Criteria

- [ ] All 37 hooks follow the 0/1/2 exit code convention from ANTHROPIC-STANDARDS.md
- [ ] No hook uses catch-all `except: sys.exit(0)` to swallow errors
- [ ] No hook uses `2>/dev/null || true` pattern
- [ ] `memory_capture.py` has a functional timeout (5000ms) or is removed
- [ ] All hooks produce structured JSON output for warnings and errors
- [ ] A new Claude Code session starts without hook errors

---

## Technical Notes

**Scope boundary:** This story standardizes error handling patterns ONLY. It does NOT consolidate hooks (TD-020, P2, ~8h). The 37 hooks remain as 37 separate files. The goal is consistent behavior, not architectural change.

**Testing hooks:** Hooks are Python scripts that read from stdin and write to stdout. They can be tested manually:

```bash
echo '{"tool_name": "Write", "tool_input": {"file_path": "/test"}}' | python3 .claude/hooks/some_hook.py
echo $?  # should be 0, 1, or 2
```

**Anthropic Standards reference (`.claude/rules/ANTHROPIC-STANDARDS.md` section 1.2):**
- Exit 0 = Success (hook passed)
- Exit 1 = Warning (continue but notify)
- Exit 2 = Error/Block (stop execution)

**The 30ms timeout on memory_capture.py:** Python 3.12 startup time on macOS is ~40-80ms. A 30ms timeout means the hook is killed before it even finishes importing modules. It has never successfully executed.

**JSON output format for hooks:**
```json
{"warning": "File X was not found, using fallback"}
{"error": "Required state file is corrupted"}
```

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Fix memory_capture.py timeout (TD-015) | 0.25h |
| Audit 37 hooks -- create compliance table | 1.5h |
| Fix non-compliant hooks (~15-20 estimated) | 3h |
| Test each modified hook | 1h |
| Session integration test | 0.25h |
| **Total** | **~6h** |

---

## Dependencies

None. This story is independent of all other stories in the epic. It can run in parallel with Story 2.1.

---

## Definition of Done

- [ ] Audit table complete: all 37 hooks documented with compliance status
- [ ] All hooks use 0/1/2 exit codes per ANTHROPIC-STANDARDS.md
- [ ] No error-swallowing patterns remain
- [ ] `memory_capture.py` resolved (functional or removed)
- [ ] All modified hooks tested manually
- [ ] New Claude Code session starts cleanly with all hooks active
- [ ] Audit table committed as `docs/reports/hook-compliance-audit.md`
