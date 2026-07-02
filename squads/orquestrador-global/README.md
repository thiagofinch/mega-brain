# Orquestrador Global

Central nervous system of Mega Brain. Entry-point único `plan-architect` (THE ONE CREATE per EPIC-PLAN-ARCHITECT) que recebe demandas em linguagem natural e produz **planos completos de orquestração** (DAG + paralelização + riscos + custos + handoff) **SEM EXECUTAR**.

**Status:** production-ready · ADR-PA-001 ACCEPTED + REINFORCED · empirically validated (Run #1 + Run #1.5, 20 plans, Golden Set 100%)

## Agents (7)

| Agent | Tier | Role |
|-------|------|------|
| `plan-architect` | orchestrator | **Entry-point único** — `plan_only=true`. Coordena 6 fases (intent → cartography → routing → DAG → validation → handoff). |
| `intent-parser` | tier_0 | Classifica intent + elicitação inline (max 3 perguntas se confidence < 0.7) |
| `capability-cartographer` | tier_0 | Descoberta de capacidades via `scan-capabilities.js` (3905 caps em ~329ms) |
| `roteador` | tier_1 | Scoring + decisões IDS (REUSE/ADAPT/CREATE) |
| `supervisor-sistema` | tier_1 | Health monitoring + gap detection no ecossistema |
| `dag-architect` | tier_2 | Constrói DAG + CPM + grupos paralelos (`plan_only=true`) |
| `_executor-coverage` | tier_2 | Cobertura de executor types (Human/Agent/Worker/Clone) |

## Invocation Surfaces (3)

```bash
# 1. Slash skill (Claude Code)
/orquestrador-global <demanda>

# 2. Subagent direto (Claude Code)
@orquestrador-global--plan-architect <demanda>

# 3. Gemini CLI command
/megabrain-orquestrador-global--plan-architect <demanda>
```

## Flags

```bash
/orquestrador-global mode=COMPLEX <demanda>             # forçar tier de modelo
/orquestrador-global budget=10 <demanda>                # budget cap em USD
/orquestrador-global --dry-run <demanda>                # não persiste plan
/orquestrador-global --cross-domain <demanda>           # opt-in opus dag-architect
```

## Pipeline (6 fases)

```
DEMAND
  ↓
[L1] intent-parser → confidence + parsed{domain,complexity,BUs}
  ↓
[L2] capability-cartographer → ranked capabilities
  ↓
[L3] roteador → scoring + IDS decisions (REUSE/ADAPT/CREATE)
  ↓
[L4] dag-architect (plan_only=true) + risk-assessor (FMEA RPN per node)
     [pre-mortem if RPN_max>300 OR mode=CRITICAL]
  ↓
[L5] validate-plan.js → estimate-cost.js → render-plan.js → audit-plan.js
  ↓
[L6] HANDOFF: 3-line summary + Mermaid + top risks + next_action_suggested (NÃO executado)
```

## Output

```
outputs/plans/{YYYYMMDD}_{slug}/
  plan.yaml         # canonical structured plan
  plan.md           # human-readable + Mermaid DAG
  plan.json         # machine-readable
  audit.jsonl       # provenance
```
Plus: `data/plan-registry.yaml` (registry update) + `.data/audit-trail.jsonl` (Hub append).

## Defesas em Profundidade (P1 plan-only enforcement)

1. **Agent-level:** `plan-architect.md` "What plan-architect NEVER Does" section
2. **Workflow-level:** `wf-plan-demand.yaml` `plan_only: true` mandatory
3. **Sub-agent level:** `dag-architect.md` `plan_only` flag em frontmatter
4. **Hook-level:** `.claude/hooks/pre-execution-block.sh` em PreToolUse (WARN mode → BLOCK em 2 semanas)
5. **Validator-level:** `scripts/validate-plan.js` constitutional checks (CODEOWNERS, business isolation, agent authority, no-invention)

## Defaults Calibrados (ADR-PA-001 REINFORCED)

| Tier | Modelo | Justificativa |
|------|--------|---------------|
| SIMPLE | sonnet | Run #1+#1.5: sufficient (4.50 mean) |
| STANDARD | sonnet | Run #1+#1.5: sufficient (4.567 mean) |
| COMPLEX | opus (dag-architect) | H1 confirmed (+0.40 mean) |
| CRITICAL | opus (intent + dag + risk) | Full team escalation |

`cross_domain_override`: opt-in flag `--cross-domain` para STANDARD com forte evidence (G9 +0.31).

## Stack

- 7 agents · 25 tasks (12 .md + 13 .yaml) · 28 workflows (20 .yaml + 8 .md)
- 22 templates · 9 checklists · 8 deterministic scripts
- 12 MEGABRAIN tokens (refined v1.1.0, 100% consumed_by[]) · quality gates 3-state APPROVE/REVIEW/VETO
- Infrastructure-map (470 lines, 6 sections) · deviation-registry (squad-scoped)

## Quick Start

```bash
# Validar capabilities scan
node squads/orquestrador-global/scripts/scan-capabilities.js --dry-run --subset squads-config

# Conferir empirical evidence
cat outputs/eval/plan-architect/20260428-215316/dashboard.md

# Primeiro teste real (G2 baseline: sonnet 4.60/5, $0.05)
/orquestrador-global Criar SOP de onboarding cliente novo
```

## References

- **Blueprint:** `docs/architecture/plan-architect-blueprint.md`
- **ADR:** `docs/adrs/ADR-PA-001-plan-architect-model-defaults.md`
- **Empirical evidence:** `outputs/eval/plan-architect/20260428-215316/`
- **Backlog:** `docs/architecture/plan-architect-backlog-candidates.md` (6 BL-N items)
- **SOP de monitoring:** `docs/architecture/plan-architect-backlog-monitoring.md`
- **Eval framework:** `docs/architecture/plan-architect-eval-framework.md`
- **Latest validation:** `outputs/squad-validations/orquestrador-global/latest/`
## MEGABRAIN Deep Validation

- Last run: `20260514-validate-deep`
- Validator: `mega-brain/megabrain-chief`
- Command: `*validate-squad orquestrador-global --deep`
- Score: `98.2/100`
- Status: `PASS`
- Scope: agents, tasks, workflows, scripts, contracts, data registries, invocation surfaces and plan-only boundaries.
- Live execution: not performed; validation preserved the plan-only contract and did not call external webhooks, n8n, WhatsApp or workspace writes.
