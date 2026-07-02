# Constitutional Compliance Checklist (PA-6.1)

> ALWAYS run via validate-plan.js. ANY failure → REJECT plan.

- [ ] CODEOWNERS: no plan node mutates restricted paths without approval_token
- [ ] Business isolation: no plan node accesses cross-business workspace data
- [ ] Agent authority: no plan node implies push/PR without @devops attribution
- [ ] No-invention: every plan node has Prior-Art Search row (REUSE/ADAPT/CREATE with evidence)
- [ ] Hub-canonical paths: no spoke-relative absolute paths in plan
- [ ] Sync-bridge: outputs target Hub paths (Hub → Spoke direction)
- [ ] Quality First: validate:yaml + validate:squad-structure called via post-plan-validate hook
