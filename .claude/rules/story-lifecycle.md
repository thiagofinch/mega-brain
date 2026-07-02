---
paths:
  - "docs/stories/**"
  - "docs/qa/gates/**"
  - "docs/epics/**"
---
# Story Lifecycle

Applies when working on stories in `docs/stories/`.

## Story Phases

```
Draft → Ready → InProgress → InReview → Done
```

### Phase Transitions

| Status | Trigger | Agent | Action |
|--------|---------|-------|--------|
| Draft | @sm creates story | @sm | Story file created |
| Ready | @po validates (GO) | @po | **MUST update status field from Draft → Ready** |
| InProgress | @dev starts implementation | @dev | Update status field |
| InReview | @dev completes, @qa reviews | @qa | Update status field |
| Done | @qa PASS, @devops pushes | @devops | Update status field |

**CRITICAL:** The `Draft → Ready` transition is the responsibility of @po during `*validate-story-draft`. When verdict is GO (including conditional GO after fixes), @po MUST update the story's Status field to `Ready` and log the transition in the Change Log.

## Phase 1: Create (@sm)

**Task:** `create-next-story.md`
**Inputs:** PRD sharded, epic context
**Output:** `{epicNum}.{storyNum}.story.md`

## Phase 2: Validate (@po)

**Task:** `validate-next-story.md`

### 10-Point Validation Checklist

1. Clear and objective title
2. Complete description (problem/need explained)
3. Testable acceptance criteria (Given/When/Then preferred)
4. Well-defined scope (IN and OUT clearly listed)
5. Dependencies mapped (prerequisite stories/resources)
6. Complexity estimate (points or T-shirt sizing)
7. Business value (benefit to user/business clear)
8. Risks documented (potential problems identified)
9. Criteria of Done (clear definition of complete)
10. Alignment with PRD/Epic (consistency with source docs)

**Decision:** GO (>=7/10) or NO-GO (<7/10 with required fixes)

## Phase 3: Implement (@dev)

**Task:** `dev-develop-story.md`

### Execution Modes

**YOLO (autonomous):**
- 0-1 prompts
- Decisions logged in `decision-log-{story-id}.md`
- Best for: simple, deterministic tasks

**Interactive (default):**
- 5-10 prompts with educational checkpoints
- Confirmations at key decision points
- Best for: learning, complex decisions

**Pre-Flight (plan-first):**
- All questions upfront (10-15 prompts)
- Generates execution plan
- Then zero-ambiguity execution
- Best for: ambiguous requirements, critical work

## Phase 4: QA Gate (@qa)

**Task:** `qa-gate.md`

### 8 Quality Checks

1. **Code review** — patterns, readability, maintainability
2. **Unit tests** — adequate coverage, all passing
3. **Acceptance criteria** — all met per story AC
4. **No regressions** — existing functionality preserved
5. **Performance** — within acceptable limits
6. **Security** — OWASP basics verified
7. **Documentation** — updated if necessary
8. **Runtime Probe** *(MANDATORY — added 2026-05-14, Story TIL-RUNTIME-GATE)* — Feature must be verified in a prod-like environment without mocks. Mock-only tests do not capture real runtime shape (root cause of 5 latent bugs in Wave 3). **A story CANNOT transition to Done without a Runtime Probe section present in the QA report with a PASS verdict.** INCONCLUSIVE is accepted when credentials or environment constraints prevent full probe, but justification must be documented inline. Template: `.claude/templates/qa-runtime-probe.md`. Implicit tracking metric: `runtime_probe_pass_rate` target = 100% (one entry per story Done).

### Gate Decisions

| Decision | Score | Action |
|----------|-------|--------|
| PASS | All checks OK | Approve, proceed to @devops push |
| CONCERNS | Minor issues | Approve with observations documented |
| FAIL | HIGH/CRITICAL issues | Return to @dev with feedback |
| WAIVED | Issues accepted | Approve with waiver documented (rare) |

## QA Loop (Iterative Review-Fix)

```
@qa review → verdict → @dev fixes → re-review (max 5 iterations)
```

**Escalation triggers:**
- max_iterations_reached (default: 5)
- verdict_blocked
- fix_failure (after retries)
- manual_escalate (user command)

## Story File Update Rules

| Section | Who Can Edit |
|---------|-------------|
| Title, Description, AC, Scope | @po only |
| File List, Dev Notes, checkboxes | @dev |
| QA Results | @qa only |
| Change Log | Any agent (append only) |

## Branch Naming

```
feat/{story-id}-short-description
fix/{story-id}-short-description
```

Example: `feat/X.Y-feature-name`

## Commit Convention

```
feat: implement user feature [Story X.Y]
fix: correct RLS policy for module [Story X.Y]
```

## Quality Gates

All stories must pass before merge:
- [ ] Lint passes
- [ ] Typecheck passes
- [ ] CODEOWNERS review
- [ ] PR description references story
- [ ] Acceptance criteria checked off

## Story File Location

```
docs/stories/
  epic-{N}/
    EPIC-{N}-TITLE.md           — Epic overview
    STORY-{N}.{M}-TITLE.md     — Individual stories
```
