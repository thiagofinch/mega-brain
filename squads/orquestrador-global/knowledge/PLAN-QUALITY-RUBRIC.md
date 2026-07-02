# Plan Quality Rubric — 7 Dimensões

> **Consumer:** `skill-tester/quality-judge` (REUSE) via `wf-eval-plan-architect.yaml`
> **Story:** STORY-PA-6.2 Part A
> **Source:** `docs/architecture/plan-architect-eval-framework.md` §5
>
> Threshold de aprovação: média ≥ 4.0 com nenhuma dimensão < 3 e variance std ≤ 0.5 entre re-rodadas.

---

## D1 — Completeness (1-5)

**Definição:** Todos os sub-objetivos da demanda foram cobertos?

| Score | Anchor |
|---|---|
| 1 | Ignorou ≥ 50% dos sub-objetivos óbvios |
| 2 | Cobriu sub-objetivos óbvios mas perdeu 2-3 dependências |
| 3 | Cobertura completa dos sub-objetivos explícitos |
| 4 | Cobertura completa + 1-2 sub-objetivos implícitos antecipados |
| 5 | 100% cobertura, antecipa sub-objetivos não-óbvios com justificativa |

---

## D2 — Capability Match (1-5)

**Definição:** Capabilities escolhidas são as melhores disponíveis no Hub?

| Score | Anchor |
|---|---|
| 1 | Escolha aleatória ou inventou capability inexistente |
| 2 | Capability existe mas não é a mais adequada (top-3 não considerada) |
| 3 | Top-3 considerado, escolha defensível |
| 4 | Top-3 ranqueado, justificativa explícita por nó |
| 5 | Top-3 ranqueado + Prior-Art Search rows + IDS decisions completas |

---

## D3 — Parallelization (1-5)

**Definição:** DAG explora paralelização real ou força tudo serial?

| Score | Anchor |
|---|---|
| 1 | Tudo sequencial mesmo quando independente |
| 2 | Identifica 1-2 paralelos mas perde maioria |
| 3 | Identifica paralelos óbvios |
| 4 | Identifica todos os parallel groups + critical path |
| 5 | Parallel groups + critical path + slack analysis (CPM completo) |

---

## D4 — Risk Coverage (1-5)

**Definição:** Riscos materiais identificados e mitigados?

| Score | Anchor |
|---|---|
| 1 | Sem section de risk OR genérica demais |
| 2 | Riscos listados mas sem RPN ou mitigação |
| 3 | RPN calibrado mas mitigação genérica |
| 4 | RPN calibrado + mitigação concreta por top-3 risks |
| 5 | RPN + mitigação + pre-mortem se RPN_max > 300 OR critical |

---

## D5 — Cost Efficiency (1-5)

**Definição:** Custo estimado é proporcional ao valor entregue?

| Score | Anchor |
|---|---|
| 1 | Opus pra tudo, ignora haiku/sonnet onde cabe |
| 2 | Mix de tiers mas sem rationale |
| 3 | Tier mix razoável |
| 4 | Tier mix com rationale por nó |
| 5 | Tier mix justificado + cost-per-node breakdown + Pareto consideration |

---

## D6 — Clarity (1-5)

**Definição:** Humano consegue executar sem perguntar?

| Score | Anchor |
|---|---|
| 1 | Plano vago, exige perguntas |
| 2 | Plano legível mas com ambiguidades |
| 3 | Plano claro, executável com ≤ 1 esclarecimento |
| 4 | Auto-suficiente + handoff explícito |
| 5 | Auto-suficiente + handoff + Mermaid + executive summary 3-line |

---

## D7 — Falsifiability (1-5)

**Definição:** Assumptions e success criteria são testáveis?

| Score | Anchor |
|---|---|
| 1 | "Vai funcionar" / sem critério mensurável |
| 2 | Critérios listados mas vagos |
| 3 | Cada AC tem threshold mensurável |
| 4 | Cada assumption tem teste; cada AC tem threshold |
| 5 | Assumption + teste + AC + threshold + rollback path |

---

## Agregação

**Score final do plano:**

```
quality_score = (D1 + D2 + D3 + D4 + D5 + D6 + D7) / 7
```

**Threshold de PASS:**
- quality_score ≥ 4.0
- nenhuma dimensão < 3
- variance std ≤ 0.5 (entre 3 re-rodadas com seeds diferentes)

**FAIL:**
- qualquer dimensão < 3 → FAIL imediato (mesmo se média ≥ 4.0)
- média < 4.0 → FAIL
- variance > 0.5 → FAIL com flag "non-deterministic"

---

## Auto-bias detection

Quando modelo X avalia plano produzido por modelo Y:

```
auto_bias_score = avg(self_eval) - avg(cross_eval)
```

- Se `auto_bias_score > 0.5` → modelo prefere próprio output (flag para human review)
- Mitigação: human eval operator serve como tiebreaker
