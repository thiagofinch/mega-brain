# Pre-Handoff Checklist (PA-6.1)

> Run after audit-plan.js persists, before handing off to user/executor.

- [ ] Plan persisted at outputs/plans/{date}_{slug}/ (4 files: yaml, md, json, audit.jsonl)
- [ ] plan-registry.yaml updated with new entry (status: active)
- [ ] .data/audit-trail.jsonl appended with plan_emitted event
- [ ] handoff.next_action_suggested non-empty
- [ ] handoff.next_action_executor identified
- [ ] handoff.approvals_required documented (or explicitly empty)
- [ ] handoff.do_not_execute_until lists at least "user approval" if complexity ≥ high
- [ ] All risks RPN > 200 have mitigation documented
- [ ] All falsifiable_assumptions have testable criteria
