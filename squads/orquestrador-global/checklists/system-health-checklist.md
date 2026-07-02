# Checklist: Saude do Sistema

## Metadata
```yaml
id: system-health-checklist
name: Checklist de Saude do Sistema
version: 1.0.0
executor: supervisor-sistema
related_task: audit-system
related_workflow: auditoria-sistema
```

## Purpose

Validar a saude geral do ecossistema Mega Brain-Core, garantindo que todos os componentes estao funcionando adequadamente e que nao ha gaps criticos de cobertura.

---

## Fase 1: Status dos Squads

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 1 | Todos os squads registrados estao ativos? | [ ] | Total: ___ |
| 2 | Nenhum squad com status "error" ou "degraded"? | [ ] | Problematicos: ___ |
| 3 | Todos os squads respondem ao health check? | [ ] | Sem resposta: ___ |
| 4 | Agentes principais disponiveis em cada squad? | [ ] | |
| 5 | Workflows principais funcionais? | [ ] | |

**Score Status Squads:** ___/5

---

## Fase 2: Metricas de Roteamento

| # | Check | Status | Valor |
|---|-------|--------|-------|
| 6 | Routing accuracy >= 90%? | [ ] | ___% |
| 7 | Escalation rate <= 10%? | [ ] | ___% |
| 8 | Unmatched rate <= 5%? | [ ] | ___% |
| 9 | Avg latency <= 2 segundos? | [ ] | ___ms |
| 10 | Taxa de sucesso geral >= 85%? | [ ] | ___% |

**Score Metricas:** ___/5

### Detalhamento de Metricas

| Metrica | Valor Atual | Threshold | Status |
|---------|-------------|-----------|--------|
| Routing Accuracy | ___% | >= 90% | [ ] OK [ ] WARNING [ ] CRITICAL |
| Escalation Rate | ___% | <= 10% | [ ] OK [ ] WARNING [ ] CRITICAL |
| Unmatched Rate | ___% | <= 5% | [ ] OK [ ] WARNING [ ] CRITICAL |
| Avg Latency | ___ms | <= 2000ms | [ ] OK [ ] WARNING [ ] CRITICAL |

---

## Fase 3: Cobertura de Dominios

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 11 | Todos os dominios principais tem squad? | [ ] | |
| 12 | Nenhum dominio com > 10 requests nao atendidos/mes? | [ ] | Dominios: ___ |
| 13 | Capacidades declaradas estao atualizadas? | [ ] | |
| 14 | Keywords de roteamento abrangentes? | [ ] | |
| 15 | Gaps identificados estao documentados? | [ ] | Total gaps: ___ |

**Score Cobertura:** ___/5

### Gaps Identificados

| Dominio | Requests Nao Atendidos | Prioridade | Acao Recomendada |
|---------|------------------------|------------|------------------|
| ___ | ___ | P__ | ___ |
| ___ | ___ | P__ | ___ |
| ___ | ___ | P__ | ___ |

---

## Fase 4: Performance Individual dos Squads

| # | Check | Status |
|---|-------|--------|
| 16 | Nenhum squad com accuracy < 70%? | [ ] |
| 17 | Nenhum squad com latencia > 5s? | [ ] |
| 18 | Nenhum squad com taxa de erro > 10%? | [ ] |
| 19 | Todos os squads com atividade nos ultimos 7 dias? | [ ] |
| 20 | Feedback positivo >= 80% em todos os squads? | [ ] |

**Score Performance:** ___/5

### Squads com Atencao Necessaria

| Squad | Metrica Problema | Valor | Acao |
|-------|------------------|-------|------|
| ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ |

---

## Fase 5: Integridade do Sistema

| # | Check | Status |
|---|-------|--------|
| 21 | SQUAD-REGISTRY.md atualizado? | [ ] |
| 22 | Nenhum conflito de roteamento? | [ ] |
| 23 | Logs de auditoria funcionando? | [ ] |
| 24 | Backups de configuracao em dia? | [ ] |
| 25 | Documentacao de squads atualizada? | [ ] |

**Score Integridade:** ___/5

---

## Fase 6: Alertas e Notificacoes

| # | Check | Status |
|---|-------|--------|
| 26 | Sistema de alertas operacional? | [ ] |
| 27 | Alertas criticos sendo enviados? | [ ] |
| 28 | Notificacoes de gap configuradas? | [ ] |
| 29 | Escalacao automatica funcionando? | [ ] |
| 30 | Relatorios programados em dia? | [ ] |

**Score Alertas:** ___/5

---

## Scoring Final

```
Categoria                Score
─────────────────────────────
Status Squads            ___/5
Metricas Roteamento      ___/5
Cobertura Dominios       ___/5
Performance Squads       ___/5
Integridade Sistema      ___/5
Alertas e Notificacoes   ___/5
─────────────────────────────
TOTAL                    ___/30

Porcentagem: ___%

Classificacao de Saude:
[ ] HEALTHY (>= 90%) - Sistema operando normalmente
[ ] WARNING (75-89%) - Atencao necessaria em alguns pontos
[ ] DEGRADED (60-74%) - Problemas que precisam resolucao
[ ] CRITICAL (< 60%) - Acao imediata necessaria
```

---

## Acoes por Classificacao

### Se HEALTHY
- [ ] Documentar status no relatorio semanal
- [ ] Continuar monitoramento normal

### Se WARNING
- [ ] Identificar itens em warning
- [ ] Criar plano de acao para proxima semana
- [ ] Monitorar evolucao diariamente

### Se DEGRADED
- [ ] Notificar stakeholders
- [ ] Priorizar resolucao dos problemas
- [ ] Agendar revisao em 48h

### Se CRITICAL
- [ ] Notificacao imediata
- [ ] Escalar para responsavel do sistema
- [ ] Criar war room se necessario
- [ ] Resolucao em ate 24h

---

## Quick Reference

### Thresholds de Metricas

| Metrica | OK | Warning | Critical |
|---------|-----|---------|----------|
| Routing Accuracy | >= 90% | 80-89% | < 80% |
| Escalation Rate | <= 10% | 11-20% | > 20% |
| Unmatched Rate | <= 5% | 6-15% | > 15% |
| Avg Latency | <= 2s | 2-5s | > 5s |
| Squad Accuracy | >= 80% | 70-79% | < 70% |

### Prioridade de Gaps

| Prioridade | Criterio | Acao |
|------------|----------|------|
| P0 | > 20 requests/mes nao atendidos | Criar squad imediato |
| P1 | 10-20 requests/mes nao atendidos | Avaliar criacao em 2 semanas |
| P2 | 5-10 requests/mes nao atendidos | Monitorar por 1 mes |
| P3 | < 5 requests/mes nao atendidos | Documentar para revisao trimestral |

### Frequencia de Execucao

| Tipo | Frequencia | Responsavel |
|------|------------|-------------|
| Health Check Rapido | Diario (automatico) | supervisor-sistema |
| Auditoria Completa | Semanal | supervisor-sistema + humano |
| Revisao Estrategica | Mensal | Equipe completa |

---

## Historico de Execucoes

| Data | Score | Status | Principais Issues | Responsavel |
|------|-------|--------|-------------------|-------------|
| ___ | ___/30 | ___ | ___ | ___ |
| ___ | ___/30 | ___ | ___ | ___ |
| ___ | ___/30 | ___ | ___ | ___ |
