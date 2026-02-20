# Hook Security Threat Model

> **Version:** 1.0.0
> **Created:** 2026-02-18
> **Source:** Quality Uplift SEC-001
> **Scope:** All 33 hooks in `.claude/hooks/`

---

## 1. Current State

### Hook Inventory (33 hooks)

| Category | Count | Hooks |
|----------|-------|-------|
| Session lifecycle | 4 | session_start, session_end, session_autosave_v2, session-source-sync |
| Agent memory | 4 | skill_router, memory_hints_injector, agent_memory_persister, memory_updater |
| Pipeline enforcement | 5 | post_batch_cascading, enforce_dual_location, enforce_plan_mode, quality_watchdog, post_write_validator |
| Validation | 4 | creation_validator, post_output_validator, stop_hook_completeness, claude_md_guard |
| Tracking | 5 | post_tool_use, pending_tracker, subagent_tracker, pattern_analyzer, token_checkpoint |
| Utility | 5 | jarvis_briefing, checkpoint_writer, inbox_age_alert, notification_system, ledger_updater |
| Indexing | 2 | skill_indexer, auto_formatter |
| Agent system | 3 | multi_agent_hook, agent_doctor, ralph_wiggum |

### Execution Context

All hooks run as **Python scripts** invoked by Claude Code's hook system with:
- **Full filesystem access** (read/write to any path the user can access)
- **Full network access** (no restrictions on outbound connections)
- **User-level privileges** (same as the Claude Code process)
- **No process isolation** (no containers, chroot, or namespaces)
- **30-second timeout** (configurable per hook)

---

## 2. Threat Analysis

### T1: Path Traversal (MEDIUM)

**Risk:** A hook could read/write files outside the mega-brain directory.

**Current mitigations:**
- All hooks use env-based paths (`CLAUDE_PROJECT_DIR` with `.` fallback)
- `claude_md_guard.py` validates CLAUDE.md paths specifically
- No hooks accept arbitrary user-controlled paths

**Assessment:** LOW actual risk. Hooks are written by the system owner and are not user-facing. Path traversal is only a concern if hooks process untrusted input.

### T2: Credential Exposure (HIGH)

**Risk:** Hooks could accidentally log or expose credentials.

**Current mitigations:**
- `.env` is in `.gitignore`
- Token files (`token.json`, `token_write.json`) now untracked (Quality Uplift SEC-002)
- Hooks read state files, not credential files directly

**Assessment:** MEDIUM residual. OAuth tokens were in git history (now untracked but not purged). Recommend `git filter-branch` or BFG to clean history.

### T3: Unintended State Corruption (MEDIUM)

**Risk:** Multiple hooks writing to the same state files concurrently.

**Current mitigations:**
- Hooks run sequentially within each lifecycle event
- State files use JSON (atomic write via temp file + rename)
- `post_batch_cascading.py` has explicit state locking

**Assessment:** LOW actual risk. Claude Code runs hooks sequentially per event.

### T4: Hook Chain Amplification (LOW)

**Risk:** A hook could trigger actions that trigger other hooks (cascade).

**Current mitigations:**
- Claude Code hook system does not re-trigger hooks from hook actions
- Hooks output to stdout/stderr, not tool calls

**Assessment:** NOT APPLICABLE. Hook system is non-recursive by design.

### T5: Denial of Service (LOW)

**Risk:** A hook could hang or consume excessive resources.

**Current mitigations:**
- 30-second timeout per hook
- Hooks are lightweight Python scripts
- No hooks perform heavy computation or long network calls

**Assessment:** ACCEPTABLE. Timeout is sufficient protection.

---

## 3. Sandboxing Decision

### Recommendation: NO ADDITIONAL SANDBOXING REQUIRED

**Rationale:**

1. **Single-user system.** Mega Brain is operated by one user. Hooks are authored by the system owner, not untrusted third parties.

2. **Claude Code enforces sequential execution.** No parallel hook execution means no race conditions.

3. **Cost vs benefit.** Containerizing or sandboxing 33 hooks would add complexity and latency with minimal security benefit for a single-user development environment.

4. **Existing mitigations are sufficient:**
   - `claude_md_guard.py` for write protection
   - `.gitignore` for credential protection
   - 30s timeouts for DoS protection
   - Sequential execution for consistency

### Recommended Actions (Non-Sandboxing)

| Action | Priority | Status |
|--------|----------|--------|
| Untrack credential files from git | HIGH | DONE (SEC-002) |
| Purge credentials from git history | HIGH | PENDING (requires user approval) |
| Keep `.env.example` updated | MEDIUM | DONE (STATE-002) |
| Document hook write paths | LOW | DONE (GOVERNANCE-MAP.md) |
| Review hooks annually | LOW | Schedule for 2027-02-18 |

---

## 4. Audit Trail

### Current Logging

| Hook | Logs to | Format |
|------|---------|--------|
| post_batch_cascading | `.claude/mission-control/batch-logs/` | JSON |
| session_autosave_v2 | `.claude/mission-control/AUTOSAVE-STATE.json` | JSON |
| skill_router | stdout (visible in session) | Text |
| quality_watchdog | stdout | Text |
| token_checkpoint | `.claude/jarvis/TOKEN-CHECKPOINT.json` | JSON |
| pattern_analyzer | `.claude/learning-system/` | YAML |

### Gaps

- No centralized audit log for hook executions
- No logging of hook failures (only stdout/stderr)
- Recommendation: Add `logs/hooks/` directory for structured hook execution logs in future iteration

---

## 5. References

| Document | Path |
|----------|------|
| CONSTITUTION.md | `system/protocols/CONSTITUTION.md` |
| GOVERNANCE-MAP.md | `system/protocols/GOVERNANCE-MAP.md` |
| ENFORCEMENT.md | `system/protocols/system/ENFORCEMENT.md` |
| settings.json | `.claude/settings.json` (hook registrations) |
