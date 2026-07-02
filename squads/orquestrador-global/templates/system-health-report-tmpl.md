# System Health Report Template

> Relatório de saúde do ecossistema Mega Brain gerado pelo Supervisor de Sistema

## Metadata

```yaml
template:
  id: system-health-report
  name: System Health Report
  agent: supervisor-sistema
  output_format: markdown
```

---

# System Health Report | {{report_date}}

**Período:** {{start_date}} - {{end_date}}
**Tipo:** {{report_type}} (Diário | Semanal | Mensal | Ad-hoc)
**Gerado em:** {{generated_at}}
**Gerado por:** Supervisor de Sistema v{{version}}

---

## Executive Summary

### Overall Health Score

```
┌────────────────────────────────────────────────────────┐
│                 SYSTEM HEALTH: {{health_score}}%                  │
│  [{{health_bar}}]  │
│                    {{health_status}}                    │
└────────────────────────────────────────────────────────┘
```

**Status:** {{health_status}} (🟢 Healthy | 🟡 Degraded | 🔴 Critical)

### Key Highlights
- ✅ {{highlight_1}}
- ✅ {{highlight_2}}
- ⚠️ {{warning_1}}
- 🔴 {{critical_1}}

---

## Ecosystem Overview

### Squad Census

| Categoria | Count | Status |
|-----------|-------|--------|
| **Total de Squads** | {{total_squads}} | - |
| **Squads Ativos** | {{active_squads}} | {{active_status}} |
| **Squads Inativos** | {{inactive_squads}} | {{inactive_status}} |
| **Total de Agentes** | {{total_agents}} | - |

### Squad Distribution by Domain

```
┌─────────────────────────────────────────────────────────┐
│ Domain Distribution                                      │
├─────────────────────────────────────────────────────────┤
│ {{domain_1}}: [{{bar_1}}] {{pct_1}}% ({{count_1}} squads)│
│ {{domain_2}}: [{{bar_2}}] {{pct_2}}% ({{count_2}} squads)│
│ {{domain_3}}: [{{bar_3}}] {{pct_3}}% ({{count_3}} squads)│
│ {{domain_4}}: [{{bar_4}}] {{pct_4}}% ({{count_4}} squads)│
│ {{domain_5}}: [{{bar_5}}] {{pct_5}}% ({{count_5}} squads)│
└─────────────────────────────────────────────────────────┘
```

---

## Routing Metrics

### Volume

| Métrica | Período Anterior | Período Atual | Variação |
|---------|------------------|---------------|----------|
| **Total de Requests** | {{prev_requests}} | {{curr_requests}} | {{var_requests}} |
| **Requests/dia** | {{prev_daily}} | {{curr_daily}} | {{var_daily}} |
| **Pico de requests** | {{prev_peak}} | {{curr_peak}} | {{var_peak}} |

### Routing Accuracy

| Tipo de Decisão | Count | % | Meta | Status |
|-----------------|-------|---|------|--------|
| **Direct Route** (≥0.8) | {{direct_count}} | {{direct_pct}}% | >80% | {{direct_status}} |
| **Confirm** (0.6-0.79) | {{confirm_count}} | {{confirm_pct}}% | <15% | {{confirm_status}} |
| **Escalate** (<0.6) | {{escalate_count}} | {{escalate_pct}}% | <5% | {{escalate_status}} |

### Accuracy Validation

| Métrica | Valor | Meta | Status |
|---------|-------|------|--------|
| **Precisão de roteamento** | {{routing_accuracy}}% | >90% | {{accuracy_status}} |
| **Taxa de re-roteamento** | {{reroute_rate}}% | <5% | {{reroute_status}} |
| **Taxa de sucesso** | {{success_rate}}% | >95% | {{success_status}} |

---

## Squad Performance

### Top Performing Squads

| # | Squad | Requests | Success Rate | Avg Latency |
|---|-------|----------|--------------|-------------|
| 1 | {{top_1_squad}} | {{top_1_requests}} | {{top_1_success}}% | {{top_1_latency}}ms |
| 2 | {{top_2_squad}} | {{top_2_requests}} | {{top_2_success}}% | {{top_2_latency}}ms |
| 3 | {{top_3_squad}} | {{top_3_requests}} | {{top_3_success}}% | {{top_3_latency}}ms |
| 4 | {{top_4_squad}} | {{top_4_requests}} | {{top_4_success}}% | {{top_4_latency}}ms |
| 5 | {{top_5_squad}} | {{top_5_requests}} | {{top_5_success}}% | {{top_5_latency}}ms |

### Underperforming Squads

| Squad | Issue | Requests | Metric | Recommendation |
|-------|-------|----------|--------|----------------|
| {{under_1_squad}} | {{under_1_issue}} | {{under_1_requests}} | {{under_1_metric}} | {{under_1_rec}} |
| {{under_2_squad}} | {{under_2_issue}} | {{under_2_requests}} | {{under_2_metric}} | {{under_2_rec}} |

### Unused Squads

| Squad | Último uso | Dias inativo | Ação sugerida |
|-------|------------|--------------|---------------|
| {{unused_1}} | {{unused_1_last}} | {{unused_1_days}} | {{unused_1_action}} |
| {{unused_2}} | {{unused_2_last}} | {{unused_2_days}} | {{unused_2_action}} |

---

## Gap Analysis

### Unmatched Requests

| Categoria | Count | % | Exemplos |
|-----------|-------|---|----------|
| **Sem match** | {{unmatched_count}} | {{unmatched_pct}}% | {{unmatched_examples}} |
| **Baixa confiança** | {{low_conf_count}} | {{low_conf_pct}}% | {{low_conf_examples}} |
| **Escalados** | {{escalated_count}} | {{escalated_pct}}% | {{escalated_examples}} |

### Patterns in Unmatched Requests

| Pattern | Frequência | Sugestão |
|---------|------------|----------|
| {{pattern_1}} | {{freq_1}} | {{suggestion_1}} |
| {{pattern_2}} | {{freq_2}} | {{suggestion_2}} |
| {{pattern_3}} | {{freq_3}} | {{suggestion_3}} |

### Recommended New Squads

| Prioridade | Squad Sugerido | Justificativa | Requests Potenciais |
|------------|----------------|---------------|---------------------|
| {{prio_1}} | {{new_squad_1}} | {{just_1}} | {{potential_1}} |
| {{prio_2}} | {{new_squad_2}} | {{just_2}} | {{potential_2}} |

---

## Latency Analysis

### Orchestration Pipeline

| Stage | P50 | P95 | P99 | Meta | Status |
|-------|-----|-----|-----|------|--------|
| **Classificação** | {{class_p50}}ms | {{class_p95}}ms | {{class_p99}}ms | <500ms | {{class_status}} |
| **Indexação** | {{index_p50}}ms | {{index_p95}}ms | {{index_p99}}ms | <200ms | {{index_status}} |
| **Roteamento** | {{route_p50}}ms | {{route_p95}}ms | {{route_p99}}ms | <100ms | {{route_status}} |
| **Total Pipeline** | {{total_p50}}ms | {{total_p95}}ms | {{total_p99}}ms | <1000ms | {{total_status}} |

### Latency Trend

```
Latência P95 (últimos 7 dias)
│
│     {{trend_visual}}
│
└───────────────────────────────────────────→
    {{day_1}} {{day_2}} {{day_3}} {{day_4}} {{day_5}} {{day_6}} {{day_7}}
```

---

## Registry Health

### Index Status

| Métrica | Valor | Status |
|---------|-------|--------|
| **Cobertura** | {{index_coverage}}% | {{coverage_status}} |
| **Última sincronização** | {{last_sync}} | {{sync_status}} |
| **Squads no índice** | {{indexed_squads}} | - |
| **Squads em disco** | {{disk_squads}} | - |
| **Discrepâncias** | {{discrepancies}} | {{disc_status}} |

### Index Issues

| Issue | Squad | Ação |
|-------|-------|------|
| {{issue_1}} | {{issue_1_squad}} | {{issue_1_action}} |
| {{issue_2}} | {{issue_2_squad}} | {{issue_2_action}} |

---

## Alerts & Incidents

### Active Alerts

| Severidade | Alerta | Desde | Impacto | Ação |
|------------|--------|-------|---------|------|
| {{alert_1_sev}} | {{alert_1_msg}} | {{alert_1_since}} | {{alert_1_impact}} | {{alert_1_action}} |
| {{alert_2_sev}} | {{alert_2_msg}} | {{alert_2_since}} | {{alert_2_impact}} | {{alert_2_action}} |

### Incidents This Period

| Data | Incident | Duração | Impacto | RCA |
|------|----------|---------|---------|-----|
| {{incident_1_date}} | {{incident_1_desc}} | {{incident_1_duration}} | {{incident_1_impact}} | {{incident_1_rca}} |

---

## Recommendations

### Immediate Actions (P0)

| # | Ação | Impacto | Owner |
|---|------|---------|-------|
| 1 | {{action_p0_1}} | {{impact_p0_1}} | {{owner_p0_1}} |
| 2 | {{action_p0_2}} | {{impact_p0_2}} | {{owner_p0_2}} |

### Short-term (P1)

| # | Ação | Impacto | Owner |
|---|------|---------|-------|
| 1 | {{action_p1_1}} | {{impact_p1_1}} | {{owner_p1_1}} |
| 2 | {{action_p1_2}} | {{impact_p1_2}} | {{owner_p1_2}} |

### Long-term (P2)

| # | Ação | Impacto | Owner |
|---|------|---------|-------|
| 1 | {{action_p2_1}} | {{impact_p2_1}} | {{owner_p2_1}} |

---

## Appendix

### Squad Inventory

| Squad | Version | Agents | Status | Last Update |
|-------|---------|--------|--------|-------------|
| {{inv_1_squad}} | {{inv_1_version}} | {{inv_1_agents}} | {{inv_1_status}} | {{inv_1_update}} |
| {{inv_2_squad}} | {{inv_2_version}} | {{inv_2_agents}} | {{inv_2_status}} | {{inv_2_update}} |
| {{inv_3_squad}} | {{inv_3_version}} | {{inv_3_agents}} | {{inv_3_status}} | {{inv_3_update}} |

### Glossary

| Termo | Definição |
|-------|-----------|
| **Direct Route** | Roteamento automático com confiança ≥0.8 |
| **Confirm** | Roteamento com confirmação do usuário (0.6-0.79) |
| **Escalate** | Decisão delegada para humano (<0.6) |
| **Health Score** | Média ponderada de todas as métricas de saúde |

---

**Relatório gerado por:** Supervisor de Sistema
**Próximo relatório:** {{next_report}}
**Contato:** {{contact}}
