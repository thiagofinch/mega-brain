# Self-Evolution Report -- {{quarter}} {{year}}

> **Ciclo:** {{quarter}} {{year}}
> **Período:** {{quarter_start}} a {{quarter_end}}
> **Owner:** @pm + @architect
> **Gerado em:** {{generated_at}}

---

## Resumo Executivo

{{executive_summary}}

### KPIs do Ciclo

| Métrica | Baseline (Fase 1) | Pos-Ciclo (Fase 6) | Delta |
|---------|-------------------|---------------------|-------|
| QA Pass Rate | {{qa_pass_rate_baseline}} | {{qa_pass_rate_post}} | {{qa_pass_rate_delta}} |
| Rework Rate | {{rework_rate_baseline}} | {{rework_rate_post}} | {{rework_rate_delta}} |
| Issues CRITICAL abertos | {{critical_issues_baseline}} | {{critical_issues_post}} | {{critical_issues_delta}} |
| Governance Health Score | {{governance_score_baseline}} | {{governance_score_post}} | {{governance_score_delta}} |
| Remediacoes Stale (>30d) | {{stale_baseline}} | {{stale_post}} | {{stale_delta}} |

---

## Métricas SDC

{{sdc_metrics}}

### Detalhamento por Squad

| Squad | Stories | QA Pass Rate | Avg Rework | Bottleneck Phase |
|-------|---------|-------------|------------|------------------|
{{sdc_squad_rows}}

---

## Auditorias Realizadas

{{audits}}

### Framework Audit (7 targets)

| Target | Findings | CRITICAL | HIGH | MEDIUM |
|--------|----------|----------|------|--------|
{{framework_audit_rows}}

### Blind Spot Self-Audits

| Squad | Blind Spots | Camada Mais Rica | Checkpoints Propostos |
|-------|-------------|------------------|----------------------|
{{blind_spot_audit_rows}}

---

## Top Blind Spots

{{top_blind_spots}}

### Top 10 por RPN (Risk Priority Number)

| # | Título | Squad | RPN | Severity | Status |
|---|--------|-------|-----|----------|--------|
{{top_blind_spots_rows}}

---

## Proposals Geradas

{{proposals}}

### Resumo

| Status | Quantidade |
|--------|-----------|
| Aprovadas | {{proposals_approved}} |
| Rejeitadas | {{proposals_rejected}} |
| Deferidas | {{proposals_deferred}} |
| **Total** | **{{proposals_total}}** |

### Proposals Aprovadas e Implementadas

| # | Título | Squad Afetado | Effort | Status |
|---|--------|--------------|--------|--------|
{{approved_proposals_rows}}

### Proposals Rejeitadas

| # | Título | Motivo da Rejeicao |
|---|--------|-------------------|
{{rejected_proposals_rows}}

---

## Comparação com Ciclo Anterior

{{comparison}}

### Tendência

| Métrica | {{prev_quarter}} | {{current_quarter}} | Tendência |
|---------|-------------------|----------------------|-----------|
{{comparison_rows}}

---

## Recomendações para Próximo Ciclo

{{recommendations}}

### Ações Sugeridas

1. {{recommendation_1}}
2. {{recommendation_2}}
3. {{recommendation_3}}

### Proposals Deferidas (herdadas)

{{deferred_proposals}}

---

## Apendice

### Comandos Executados

```
Fase 1 (Collect):  {{phase_1_date}}
Fase 2 (Audit):    {{phase_2_date}}
Fase 3 (Prioritize): {{phase_3_date}}
Fase 4 (Propose):  {{phase_4_date}}
Fase 5 (Review):   {{phase_5_date}}
Fase 6 (Apply):    {{phase_6_date}}
```

### Arquivos Gerados

- Baseline metrics: {{baseline_path}}
- Framework audit report: {{framework_audit_path}}
- Proposals: {{proposals_path}}
- Este relatório: `core/reports/self-evolution-{{quarter_code}}.md`

---

*Gerado pelo Self-Evolution Cycle (Story 78.6) -- Template v1.0.0*
