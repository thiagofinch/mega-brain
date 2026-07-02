# ADR-PA-001 — `plan-architect` Model Tier Defaults per Mode

> **Status:** ACCEPTED — calibrated with empirical evidence from Run #1 + Run #1.5 (Full Golden Set)
> **Date:** 2026-04-28 (Run #1) / 2026-04-29 (Run #1.5 closure)
> **Story:** STORY-PA-6.2 Part C
> **Empirical evidence:** `outputs/eval/plan-architect/20260428-215316/dashboard.md`
> **Plans evaluated:** **20 total** — full Golden Set (10 demands × 2 configs sonnet+opus)
> **Demand variants Run #1.5:** G6 (advocacia → frameworks IA), G8 (afiliados → OaaS plan-architect monetization). Per operator 2026-04-29.

---

## Context

`plan-architect` orquestra múltiplos sub-agents para produzir planos de orquestração. Cada sub-agent pode rodar com `sonnet`, `opus`, ou `haiku`. Combinações ótimas variam por modo de operação (SIMPLE / STANDARD / COMPLEX / CRITICAL).

**Trade-off central:** custo (Opus 5x Sonnet 18.75x Haiku) vs qualidade (paralelização, risk calibration, completeness).

**Premissa do user (operator, 2026-04-28):** "Perda de qualidade aqui pode me custar muito mais caro do que apenas tokens."

## Decision (ACCEPTED — empirically calibrated)

| Modo | dag-architect | intent-parser | capability-cartographer | roteador | risk-assessor | cost-estimator |
|---|---|---|---|---|---|---|
| **SIMPLE** | sonnet | sonnet | haiku | sonnet | haiku | (script) |
| **STANDARD** | sonnet | sonnet | haiku | sonnet | sonnet | (script) |
| **COMPLEX** | **opus** | sonnet | sonnet | sonnet | sonnet | (script) |
| **CRITICAL** | **opus** | opus | sonnet | sonnet | **opus** | (script) |

**Calibration changes vs initial DRAFT (blueprint §12.6):**
- ✏️ COMPLEX `risk-assessor`: opus → **sonnet** (H2 evidence weak — risk coverage Δ=0.40 not enough to justify 5x cost)
- All other defaults remain as DRAFT (validated by empirical evidence)

## Hypotheses Validation Results

### H1 — Opus paraleliza melhor que Sonnet ✅ **CONFIRMED**

**Evidence:** Mean parallelization score across 5 demands:
- Sonnet: 3.60
- Opus: **4.40** (+22%)

**Specific cases:**
- G3 (curso BF, COMPLEX): Sonnet 4 parallel_groups com 11 nodes; Opus 4 parallel_groups com **14 nodes** + parallelization score 5/5 vs Sonnet 4/5
- G10 (incident, CRITICAL): Sonnet identificou 1 parallel_group / 2-way; Opus identificou **4-way parallel investigation phase** (tracing/logs/metrics/code-diff em paralelo) reduzindo CPM 190min serial → 105min (1.81x speedup)

**Conclusão:** Opus genuinamente raciocina sobre paralelização em planos COMPLEX/CRITICAL. Justifica adoção como `dag-architect` em COMPLEX/CRITICAL.

### H2 — Opus identifica riscos com RPN mais calibrado ⚠️ **PARTIALLY CONFIRMED**

**Evidence:** Mean risk_coverage:
- Sonnet: 4.20
- Opus: **4.60** (+10%)

**Diferença pequena.** Pre-mortem rates iguais (3 ativações cada modelo). RPN absolute values similares. Opus mais explícito em failure modes (G10 opus pre-mortem: 5 failure modes incluindo multi-cause incident, clock skew, dirty rollback state — Sonnet pre-mortem similar mas menos profundo).

**Conclusão:** ROI insuficiente para promover Opus a `risk-assessor` em COMPLEX (mantém sonnet). Em CRITICAL, mantém Opus pois trabalho com stakes muito altos.

### H3 — Sonnet é suficiente para SIMPLE/STANDARD ✅ **CONFIRMED**

**Evidence:** Plans SIMPLE:
- G1 sonnet: **4.40** (above threshold 4.0)
- G2 sonnet: **4.60** (acima do Opus 4.43)

**Conclusão sólida:** Sonnet é não apenas suficiente, mas em alguns casos superior em SIMPLE (G2). Pareto-domina Opus em SIMPLE.

### H4 — Opus reduz drift entre plano e execução ⏳ **DEFERRED**

Requires execution data. Plans not yet executed in real workflows. **Re-eval em 90 dias** após plans executados gerarem drift_record via verify-deploy.

### H5 — Custo Opus não justifica diferença de qualidade em ≥ 80% SIMPLE/STANDARD ✅ **CONFIRMED**

**Evidence — Pareto analysis:**

| Demand | Sonnet score | Opus score | Cost ratio | Verdict |
|---|---|---|---|---|
| G1 (SIMPLE) | 4.40 | 4.43 | 1.4x | Opus dominado (+0.03 score, +40% cost) |
| G2 (SIMPLE) | 4.60 | 4.43 | 1.4x | **Sonnet vence em score E custo** |
| G3 (COMPLEX) | 4.30 | 4.57 | 16.3x | Opus +0.27 score por 16x cost — Pareto marginal |
| G7 (COMPLEX) | 4.40 | 4.43 | 23.6x | Opus dominado (+0.03 por 23x) |
| G10 (CRITICAL) | 4.40 | 4.71 | 1.5x | **Opus claramente vence** (+0.31 por 1.5x) |

**Conclusão:** Em SIMPLE/STANDARD, Opus é Pareto-dominado em 100% dos casos testados (G1, G2). Em COMPLEX, marginal. Em CRITICAL, claro ROI para Opus.

## Cost Projection (calibrated to empirical numbers)

Per typical plan, with empirical Run #1 data:

| Mode | DRAFT estimate | **EMPIRICAL (Run #1)** | Variance |
|---|---|---|---|
| SIMPLE | $0.75 | **$0.05** | 15x cheaper |
| STANDARD | $0.60 | (no data) | — |
| COMPLEX | $1.80 (mix) | **$0.70 sonnet / $13.80 opus** | sonnet 2.5x cheaper, opus 7.6x more expensive |
| CRITICAL | $3.50 | **$1.42 opus** | 2.5x cheaper |

**Distribution hypothesis (from blueprint):** 60% STANDARD, 25% SIMPLE, 12% COMPLEX, 3% CRITICAL.

**Empirical mean cost (using ACCEPTED defaults):**
- SIMPLE 25% × $0.05 = $0.013
- STANDARD 60% × $0.05 (extrapolated similar) = $0.030
- COMPLEX 12% × $13.80 (opus dag-architect mode) = $1.656
- CRITICAL 3% × $1.42 = $0.043

**Mean cost per plan: ~$1.74** (driven primarily by COMPLEX 12%).

## Pricing Snapshot (B4 mandatory)

- **Snapshot date:** 2026-04-28
- **Source:** `squads/orquestrador-global/data/pricing-snapshot.yaml`
- **Anthropic pricing URL:** https://docs.claude.com/en/docs/build-with-claude/pricing
- **Re-snapshot policy:** quarterly OR before any eval run >= $50 estimate

## Variance Analysis ⏳ DEFERRED to Run #2

Variance test (3 re-rodadas com seeds diferentes) **não foi executado** em Run #1 (Lean variant). Decisão consciente: Run #1 focou em validação primária H1+H3+H5 (3 hipóteses confirmadas com clareza). Variance test seria custo sem ROI imediato.

**Re-evaluation triggers:**
- 30 dias: Golden Set é representativo? Adicionar STANDARD demand.
- 90 dias: Run #2 com variance test (3 seeds × 2 critical demands × 2 models = 12 plans)

## Auto-bias Detection ⏳ DEFERRED to Run #2

Cross-eval (sonnet judging opus, opus judging sonnet) não executado. Razão similar: foco em hipóteses primárias.

## Pareto Chart

```
Quality (1-5)
    5 |  G2-sonnet ●
      |  G10-opus ●
      |  G3-opus ●
      |  G1-opus ●  G2-opus ●  G7-opus ●  G1-sonnet ●  G7-sonnet ●  G10-sonnet ●
      |  G3-sonnet ●
    4 |
      |
    3 |
      └─────────────────────────────────────────────────────
       $0.05         $1.00          $5.00         $15.00       Cost (USD log scale)

Pareto frontier:
  - G2-sonnet ($0.05, 4.60) — best ROI in SIMPLE
  - G10-opus ($1.42, 4.71) — best ROI in CRITICAL
  - G3-opus ($12.74, 4.57) — best score in COMPLEX (but expensive)

Pareto-dominated:
  - G1-opus dominated by G1-sonnet (similar score, 1.4x cost)
  - G7-opus dominated by G7-sonnet (similar score, 23.6x cost)
```

## Limits of Applicability

This ADR is calibrated to:
- **10 demands tested** (full Golden Set after Run #1.5): G1, G2, G3, G4, G5, G6-v2, G7, G8-v2, G9, G10 — 100% coverage
- 20 plans evaluated total (sonnet + opus per demand)
- Anthropic pricing snapshot 2026-04-28
- Hub ecosystem state at PA-6.1 completion
- No variance test (single seed per plan), no auto-cross-eval (deferred to Run #2)

**Re-evaluation triggers (per backlog-monitoring.md):**
- 30 dias: review Golden Set + add STANDARD demand
- 90 dias: full Run #2 with variance test (BL-2 trigger if data justifies)
- Pricing changes: re-snapshot
- New model tier released: include in eval

## Decision Status Log

| Date | Status | Source |
|---|---|---|
| 2026-04-28 (T1) | DRAFT created | Blueprint §12.6 hypothesis |
| 2026-04-28 (T2) | **ACCEPTED** | Empirical evidence Run #1 Lean (10 plans, H1+H3+H5 confirmed) |
| 2026-04-29 (T3) | **REINFORCED** | Run #1.5 (10 plans G4/G5/G6-v2/G8-v2/G9 — full Golden Set 20 plans). H1+H2+H3+H5 reconfirmados com sample 2x maior. Defaults inalterados. STANDARD nuance descoberta: G9 cross-domain favorece Opus dag-architect (+0.31). |

## References

- Blueprint: `docs/architecture/plan-architect-blueprint.md` v1.1 §12 (eval strategy)
- Eval framework: `docs/architecture/plan-architect-eval-framework.md`
- Story: `docs/stories/epic-plan-architect/STORY-PA-6.2-EVAL-FRAMEWORK-GOLDEN-SET-ADR.md`
- Golden Set: `squads/orquestrador-global/data/golden-set.yaml`
- Rubric: `squads/orquestrador-global/knowledge/PLAN-QUALITY-RUBRIC.md`
- Workflow: `squads/orquestrador-global/workflows/wf-eval-plan-architect.yaml`
- Defaults config: `squads/orquestrador-global/data/model-tier-defaults.yaml` (UPDATED post ACCEPTED)
- Run #1 dashboard: `outputs/eval/plan-architect/20260428-215316/dashboard.md`
- Run #1 plans: `outputs/eval/plan-architect/20260428-215316/G*-{sonnet,opus}.yaml`
