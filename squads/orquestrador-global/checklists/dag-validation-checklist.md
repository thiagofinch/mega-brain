# DAG Validation Checklist (PA-6.1)

> Run after dag-architect synthesis, before plan emission.

- [ ] DAG cycle-free (Kahn topological sort succeeds → validate-plan.js cycle check passes)
- [ ] All node IDs unique (no duplicates in dag.nodes)
- [ ] All edges reference existing node IDs (no dangling)
- [ ] Critical path identified (longest duration path); critical_path nodes annotated
- [ ] Parallel groups documented (parallelizable_with on each node, or explicit empty)
- [ ] Each node has model_tier (opus|sonnet|haiku)
- [ ] Each node has risk (severity, occurrence, detectability, rpn)
- [ ] No node implies action requiring @devops without authorship attribution
- [ ] Quality gates between phases identified
- [ ] critical_path_duration_minutes computed
