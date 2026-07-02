# Checklist: Execução de Team de Agentes

## Metadata
```yaml
id: team-execution-checklist
name: Checklist de Execução de Team de Agentes
version: 1.0.0
executor: dag-architect
related_task: execute-team
```

## Purpose

Garantir que cada execução de equipe de agentes segue o processo completo: planejamento, spawning, execução, síntese e cleanup, sem deixar recursos órfãos ou outputs incompletos.

---

## Fase 1: Pre-Spawn (Planejamento)

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 1 | Demanda classificada com intenção estruturada? | [ ] | Domínio: ___ / Tipo: ___ |
| 2 | Squad selecionado com score de match adequado? | [ ] | Squad: ___ / Score: ___ |
| 3 | Padrão de equipe determinado (lead-workers/pipeline/swarm/specialist-pool)? | [ ] | Padrão: ___ |
| 4 | Plano de execução aprovado pelo usuário? | [ ] | Plan ID: ___ |

**Score Pre-Spawn:** ___/4

---

## Fase 2: Spawning

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 5 | TeamCreate executado com sucesso? | [ ] | Team ID: ___ |
| 6 | Todos os agentes planejados foram spawnados? | [ ] | Spawnados: ___/___ |
| 7 | Modelos corretamente atribuídos conforme MODEL-STRATEGY? | [ ] | Opus: ___ / Sonnet: ___ / Haiku: ___ |
| 8 | Tarefas iniciais criadas via TaskCreate? | [ ] | Tasks criadas: ___ |

**Verificação de Agentes:**

| Agente | Modelo Planejado | Modelo Atribuído | Spawn OK? |
|--------|-----------------|------------------|-----------|
| ___ | ___ | ___ | [ ] |
| ___ | ___ | ___ | [ ] |
| ___ | ___ | ___ | [ ] |
| ___ | ___ | ___ | [ ] |

**Score Spawning:** ___/4

---

## Fase 3: Execução

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 9 | Todos os agentes receberam suas tarefas? | [ ] | Agentes com tarefas: ___/___ |
| 10 | Nenhum agente stuck/idle além do threshold (2min)? | [ ] | Idle detectados: ___ |
| 11 | Dependências de tarefas respeitadas (bloqueios corretos)? | [ ] | Violações: ___ |
| 12 | Outputs intermediários coletados de tarefas completadas? | [ ] | Outputs recebidos: ___/___ |

**Monitoramento de Execução:**

| Agente | Tarefas Completadas | Tarefas Pendentes | Tempo Idle | Status |
|--------|--------------------|--------------------|------------|--------|
| ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ | ___ |

**Score Execução:** ___/4

---

## Fase 4: Síntese

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 13 | Todos os outputs de agentes foram recebidos? | [ ] | Recebidos: ___/___ |
| 14 | Resultados consolidados sem conflitos ou inconsistências? | [ ] | Conflitos: ___ |
| 15 | Quality check do resultado final passou? | [ ] | Quality Score: ___/1.0 |

**Validação de Outputs:**

| Agente | Output Esperado | Output Recebido | Qualidade |
|--------|----------------|-----------------|-----------|
| ___ | ___ | [ ] Sim / [ ] Não | ___/1.0 |
| ___ | ___ | [ ] Sim / [ ] Não | ___/1.0 |
| ___ | ___ | [ ] Sim / [ ] Não | ___/1.0 |
| ___ | ___ | [ ] Sim / [ ] Não | ___/1.0 |

**Score Síntese:** ___/3

---

## Fase 5: Cleanup

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 16 | Todos os agentes receberam shutdown e confirmaram? | [ ] | Shutdown: ___/___ |
| 17 | TeamDelete executado com sucesso? | [ ] | Team ID: ___ |
| 18 | Outputs salvos no diretório team-outputs/? | [ ] | Path: ___ |

**Verificação de Shutdown:**

| Agente | Shutdown Enviado | Confirmado | Tempo de Resposta |
|--------|-----------------|------------|-------------------|
| ___ | [ ] | [ ] | ___ |
| ___ | [ ] | [ ] | ___ |
| ___ | [ ] | [ ] | ___ |
| ___ | [ ] | [ ] | ___ |

**Score Cleanup:** ___/3

---

## Scoring Final

```
Fase 1 (Pre-Spawn):  ___/4
Fase 2 (Spawning):   ___/4
Fase 3 (Execução):   ___/4
Fase 4 (Síntese):    ___/3
Fase 5 (Cleanup):    ___/3
─────────────────────────────
TOTAL:               ___/18

Qualidade da Execução:
[ ] EXCELENTE (>90%, 17-18) - Execução perfeita
[ ] BOM (80-90%, 15-16) - Pequenos ajustes necessários
[ ] REGULAR (70-80%, 13-14) - Revisar processo
[ ] FRACO (<70%, <13) - Investigar falha de execução
```

---

## Quick Reference

### Padrões de Equipe

| Padrão | Quando Usar | Comunicação | Max Agentes |
|--------|-------------|-------------|-------------|
| lead-workers | Tarefa divisível em sub-tarefas independentes | Lead distribui, workers executam | 1 lead + N workers |
| pipeline | Trabalho sequencial (output -> input) | Cadeia linear | N stages |
| swarm | Múltiplas perspectivas sobre mesmo problema | Todos para todos | 3-5 agentes |
| specialist-pool | Requer múltiplas especialidades | Via coordinator | 2-6 specialists |

### Alocação de Modelos (MODEL-STRATEGY)

| Papel | Modelo | Justificativa |
|-------|--------|---------------|
| Lead / Coordinator | sonnet | Planejamento e decisão |
| Worker (criativo) | sonnet | Qualidade de output |
| Worker (operacional) | haiku | Custo-benefício |
| Reviewer / QA | sonnet | Análise crítica |
| Tarefas simples | haiku | Eficiência de custo |
| Decisões de arquitetura | opus | Máxima qualidade |

### Thresholds de Monitoramento

| Situação | Threshold | Ação |
|----------|-----------|------|
| Agente idle | > 2 minutos | Verificar e reatribuir |
| Tarefa sem progresso | > 5 minutos | Investigar bloqueio |
| Agente sem resposta | > 3 minutos | Tentar re-ping |
| Shutdown sem confirmação | > 30 segundos | Force terminate |

### Checklist Rápido de Emergência

| Problema | Ação Imediata |
|----------|---------------|
| Agente stuck | Reatribuir tarefa a outro agente |
| Dependência circular | Remover bloqueio manual, escalar |
| Output inconsistente | Re-executar tarefa com agente diferente |
| Todos agentes idle | Verificar se há tarefas pendentes |
| Erro de spawn | Retry com modelo fallback |
| Timeout geral | Sintetizar resultados parciais, informar usuário |

### Log Obrigatório

```yaml
log_execucao:
  timestamp: "YYYY-MM-DD HH:MM:SS"
  team_id: "uuid"
  squad: "nome-do-squad"
  pattern: "lead-workers"
  agents_count: N
  tasks_total: N
  tasks_completed: N
  duration_ms: XXXX
  quality_score: 0.XX
  status: "completed | partial | failed"
```
