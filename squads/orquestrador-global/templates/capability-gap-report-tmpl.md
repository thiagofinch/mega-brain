<!-- Consumer: PA-7 wf-capability-gap-resolution → request-new-squad / ADR; operator review -->
<!-- Schema: produzido quando dag-architect não consegue cobrir 100% dos sub-objetivos com capabilities existentes -->

# Capability Gap Report — `{plan_id}`

> **Demanda:** {demand_summary}
> **Data:** {created_at}
> **Severidade:** {LOW / MEDIUM / HIGH / CRITICAL}

## Sub-objetivos Cobertos vs Não-Cobertos

| Sub-objetivo | Capability Match | Score | Status |
|---|---|---|---|
| {obj 1} | {capability} | {score} | COVERED |
| {obj 2} | (none) | — | **GAP** |

## Gaps Detectados

### Gap 1 — `{nome do gap}`

**Sub-objetivo:** {description}

**Por que falta:** {rationale após Prior-Art Search}

**Prior-Art Search executada:**
- Tool: {grep/glob}
- Pattern: `{pattern}`
- Scope: `{paths}`
- Matches: {N}
- Verdict: CONFIRMED_ABSENT

**Workaround possível:** {alternativa via combinação de capabilities existentes, se houver}

**Blocker Resolution executado:**
- L0 Evidence: {command_or_url} → {status_or_error}
- L1 Local workaround: {attempted_tool_or_reason_not_applicable}
- L2 Capability search: {paths_and_matches}
- L3 External services ranked: {service_1, service_2, service_3}
- L4 Approval required: {yes/no + exact ask}

**Cost de workaround vs CREATE:** {comparação}

**Recomendação:** ADAPT existente / CREATE new / Defer to backlog

---

## Padrão Recorrente?

- [ ] Mesmo gap apareceu em planos passados? {yes/no} — referências: {plan_ids}
- [ ] Trigger pattern: {N gaps similares em últimos 30 dias}
- [ ] Threshold para `request-new-squad`: 3+ ocorrências em 60 dias

## Escalation Required

- [ ] Sim — abrir story em `request-new-squad` workflow
- [ ] Não — workaround inline aceitável

## Próximos Passos

1. {ação 1}
2. {ação 2}

---

## Example

> **Demanda:** "Análise de sentimento em comentários do YouTube de concorrentes"
> **Data:** 2026-04-28
> **Severidade:** MEDIUM

### Sub-objetivos

| Sub-objetivo | Capability | Score | Status |
|---|---|---|---|
| Coletar comentários de YouTube | spy/youtube-fetcher | 0.88 | COVERED |
| Classificar sentimento PT-BR | (none) | — | **GAP** |
| Aggregar + dashboard | data/data-chief | 0.91 | COVERED |

### Gap 1 — Classificador de sentimento PT-BR

**Sub-objetivo:** Classificar comentários PT-BR (positivo/neutro/negativo) com 80%+ accuracy

**Por que falta:** Hub não tem agent ou skill especializado em sentiment analysis. `mega-brain` faz análise mas não classificação estruturada.

**Prior-Art Search:**
- Tool: Grep
- Pattern: "sentiment|sentimento"
- Scope: `squads/**, .claude/skills/**`
- Matches: 3 (todos em prose, nenhum funcional)
- Verdict: CONFIRMED_ABSENT

**Workaround possível:** Invocar Claude direto via prompt em `mega-brain` agent — não otimizado mas funciona.

**Cost workaround:** ~$0.15/100 comments (Claude direct) vs CREATE: 2 dias dev + ongoing maintenance.

**Recomendação:** Workaround inline pra esta demanda; defer CREATE ao backlog se padrão recorrer.

### Padrão Recorrente?

- [ ] Sim — 1 demanda similar há 3 semanas (plan_id: competitor-watch-20260407)
- [ ] Não há trigger ainda (precisa 3+ em 60d)

### Escalation

- [x] Não — workaround inline aceitável; criar BL-N candidate em `BACKLOG-CANDIDATES.md`

### Próximos Passos

1. Adicionar BL-7 em backlog: "PT-BR sentiment classifier" com trigger "3 demandas em 60d"
2. Plano original prossegue com workaround via mega-brain
