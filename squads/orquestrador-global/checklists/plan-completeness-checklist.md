# Plan Completeness Checklist (PA-6.1)

> Run before emitting plan to user. All boxes must be ticked.

- [ ] schema_version == "2.0"
- [ ] plan_id present (slug-YYYYMMDD-HHmmss format)
- [ ] demand.raw populated (original user text)
- [ ] demand.parsed.confidence ∈ [0.0, 1.0]
- [ ] demand.parsed has all 8 required fields (per blueprint §6 + intent-taxonomy.yaml)
- [ ] discovery.cache_version + cache_age_seconds populated
- [ ] selected_capabilities is non-empty array; each entry has id, type, score, ids_decision
- [ ] dag.nodes is non-empty; each node has id, capability, capability_type, label, model_tier, risk
- [ ] dag.edges links existing node ids only (no dangling references)
- [ ] dag.parallel_groups identified (or explicitly empty with reason)
- [ ] dag.critical_path identified (or empty for single-node plans)
- [ ] risks.top_risks populated (≥ 0; empty acceptable for SIMPLE)
- [ ] resource_estimate.total_cost_usd computed
- [ ] success_criteria has ≥ 1 testable metric
- [ ] falsifiable_assumptions has ≥ 1 testable assumption
- [ ] constitutional_compliance: all 4 checks marked pass/fail (no "unchecked")
- [ ] handoff.next_action_suggested populated
- [ ] handoff.next_action_executor identified (@dev/@qa/@devops/etc.)
- [ ] quality_score computed (1-5)
- [ ] audit fields populated (cache_manifest_hash, scoring_config_version, heuristics_applied)
