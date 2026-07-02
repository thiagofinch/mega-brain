---
paths:
  - "squads/orquestrador-global/**"
  - ".claude/skills/orquestrador-global/**"
  - "outputs/plans/**"
---

# Plan-Architect Execution Handoff — MegaBrain Hub

Applies whenever someone invokes `/orquestrador-global` or interacts with a plan produced by it.

## NON-NEGOTIABLE Invariant (P1)

`/orquestrador-global` and the `plan-architect` agent are **plan-only**. They produce a plan and **NEVER execute it**.

This is enforced architecturally:
- Agent frontmatter declares `plan_only: true`
- Hook `.claude/hooks/pre-execution-block.sh` blocks any execution tool from the agent (Bash, Edit, Write outside `outputs/plans/`, TeamCreate, TaskCreate, etc.)
- Allowed tools restricted to 5 read-only / persistence pipeline scripts:
  `scan-capabilities.js`, `validate-plan.js`, `estimate-cost.js`, `render-plan.js`, `audit-plan.js`

## The Anti-Pattern (root cause of post-mortem 2026-05-03)

**Wrong mental model:** "I called `/orquestrador-global launch course X` so the agents are running now."

**Reality:** the skill produced a `plan.json` describing **which** agents to call and in **what order**. Nothing has executed. The plan sits in `outputs/plans/{date}_{slug}/` waiting for a human or a downstream skill to consume it.

If you closed the session after `/orquestrador-global` returned, **zero work happened**. The plan is metadata, not execution.

## Canonical Execution Route

```
USER demand
    ↓
/orquestrador-global <demand>          [PLAN ONLY — produces outputs/plans/{slug}/plan.json]
    ↓
Human review of plan.md + risks         [GATE — approval if handoff.do_not_execute_until exists]
    ↓
plan-to-swarm.js (adapter)              [Maps DAG nodes → swarm-execute task batches]
    ↓
/swarm-execute <batch.json>             [EXECUTES — one batch per topological layer]
    ↓
Repeat per batch (deps respected)
```

## How to invoke the adapter

```bash
# 1. See the plan summary first (no side effects)
node squads/orquestrador-global/scripts/plan-to-swarm.js \
  --in outputs/plans/2026-05-03_launch-curso/plan.json \
  --dry-run

# 2. Convert and review all batches
node squads/orquestrador-global/scripts/plan-to-swarm.js \
  --in outputs/plans/2026-05-03_launch-curso/plan.json \
  --format yaml --out /tmp/batches.yaml

# 3. Pipe a single batch directly to /swarm-execute
node squads/orquestrador-global/scripts/plan-to-swarm.js \
  --in outputs/plans/2026-05-03_launch-curso/plan.json \
  --batch 1 --swarm-input-only > /tmp/swarm-batch-1.json
# Then in Claude:
# /swarm-execute (paste content of /tmp/swarm-batch-1.json)
```

## Mapping reference (DAG node → swarm-execute task)

| Plan field | Swarm-execute field | Rule |
|---|---|---|
| `dag.nodes[].capability` | `task.agent` | Colon → double-dash separator (`a:b` → `a--b`) |
| `dag.nodes[].label` + demand context + I/O + risk | `task.prompt` | Composed from multiple fields for context |
| `dag.nodes[].outputs_produced` non-empty | `task.mode` | `"write"` if any outputs, else `"read"` |
| `dag.nodes[].estimated_duration_minutes` | `task.effort` | <1=1, <2=2, <10=3, <30=4, <60=5, ≥60=6 |
| `dag.nodes[].outputs_produced` | `task.file_set` | Direct copy when present |
| `dag.nodes[].quality_gate` | `task.checklist` | Direct (path or name; swarm resolves) |
| `dag.edges` + `dag.parallel_groups` | batch grouping | Kahn's topological sort, validated against parallel_groups |

## When NOT to use the adapter

- **Task is trivial** (single node, single agent) — invoke the agent directly. The orchestrator + adapter overhead is not worth it.
- **You already know which agent to call** — skip planning, invoke directly.
- **Plan failed validation** (`validate-plan.js` reported errors) — fix the plan before executing.
- **Critical risks not mitigated** (`risks.top_risks[].rpn > 300` without mitigation) — escalate to roundtable, do not auto-execute.

## Approval Gate (do_not_execute_until)

Plans may declare `handoff.do_not_execute_until: ["user approval"]` or similar. The adapter preserves these fields in its output but does NOT enforce them — `/swarm-execute` and the human are responsible for honoring approval gates.

For plans flagged `mode=CRITICAL`, the canonical chain is:

```
/orquestrador-global → /roundtable (consensus review) → human approval → adapter → /swarm-execute
```

## Failure Modes & Recovery

| Symptom | Cause | Recovery |
|---|---|---|
| Adapter says "schema_version expected 2.0" | Old plan from spoke (informal v1.x) | Re-run `/orquestrador-global` to regenerate |
| Adapter says "Cycle detected in DAG" | plan-architect produced invalid DAG | Bug in plan-architect; report to @architect; do not patch downstream |
| Adapter says "Edge references unknown node" | Same | Same |
| Adapter agent IDs don't match swarm-execute registry | Capability cache stale | Re-run `node squads/orquestrador-global/scripts/scan-capabilities.js --force` then re-plan |
| swarm-execute fails on agent ID | Agent missing on this branch (e.g. `cole-gordon` on a feature branch before materialization) | Materialize the missing agent or remove from plan; re-run plan |

## Why an Adapter Instead of a Combined Skill

The orquestrador-global is plan-only by design (P1) — and by hook enforcement. Building a skill that "plans + executes" would violate P1 and complicate auditability. The adapter is the **only** glue that's allowed to span the boundary, and it does it as a deterministic, testable script with no agent reasoning involved.

This separation keeps:
- **Plan reviewability** (human sees plan before execution)
- **Plan auditability** (`outputs/plans/{slug}/audit.jsonl` records every plan)
- **Execution pluggability** (swap `/swarm-execute` for `/wave-execute` etc. without touching planner)

## Reference

- Adapter source: `squads/orquestrador-global/scripts/plan-to-swarm.js`
- Adapter tests: `squads/orquestrador-global/scripts/__tests__/plan-to-swarm.test.js` (54 tests)
- Plan schema: `squads/orquestrador-global/templates/orchestration-plan-tmpl.yaml` (schema_version 2.0)
- Swarm-execute SKILL: `.claude/skills/swarm-execute/SKILL.md`
- Plan-architect agent: `squads/orquestrador-global/agents/plan-architect.md`
- ADR: `docs/adrs/ADR-PA-001-plan-architect-model-defaults.md`

## Anti-Pattern (DO NOT do)

```text
# WRONG — assumes /orquestrador-global executes
User: /orquestrador-global launch new course
Claude: <produces plan.json>
User: <closes session>
Result: zero work done; user later complains "agents weren't activated"
```

```text
# WRONG — manually rebuilding what the adapter does
User: /orquestrador-global launch new course
User: <reads plan, hand-codes a swarm-execute JSON, types it in chat>
Result: error-prone, loses traceability fields, drifts from plan
```

```text
# RIGHT — full chain
User: /orquestrador-global launch new course
Claude: <produces plan.json>
User: <reviews plan.md, especially risks and handoff.approvals_required>
User: node .../plan-to-swarm.js --in <plan> --batch 1 --swarm-input-only > batch.json
User: /swarm-execute (with contents of batch.json)
Claude: <executes batch 1 in parallel>
User: <waits for batch 1 to finish>
User: node .../plan-to-swarm.js --in <plan> --batch 2 --swarm-input-only > batch2.json
User: /swarm-execute (with contents of batch2.json)
... repeat per batch
```
