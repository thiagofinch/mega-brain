# Team Status Report Template

> Template para output do comando `*team-status`, exibindo estado atual de uma equipe em execução

## Metadata

```yaml
template:
  id: team-status-report
  name: Team Status Report
  agent: team-coordinator
  output_format: markdown
  trigger: "*team-status"
```

---

# Team Status | {{team_name}}

**Report Time:** {{report_timestamp}}
**Team Created:** {{created_at}}
**Elapsed:** {{elapsed_time}}

---

## Squad em Execução

| Campo | Valor |
|-------|-------|
| **Squad** | {{squad_name}} |
| **Padrão** | {{pattern_name}} |
| **Plan ID** | {{plan_id}} |
| **Status** | {{team_status}} (planning / spawning / executing / synthesizing / shutting_down / completed) |

---

## Agentes

| # | Agente | Papel | Modelo | Status | Tarefa Atual | Completas | Total |
|---|--------|-------|--------|--------|--------------|-----------|-------|
| 1 | {{agent_1_name}} | {{agent_1_role}} | {{agent_1_model}} | {{agent_1_status}} | {{agent_1_current_task}} | {{agent_1_completed}} | {{agent_1_total}} |
| 2 | {{agent_2_name}} | {{agent_2_role}} | {{agent_2_model}} | {{agent_2_status}} | {{agent_2_current_task}} | {{agent_2_completed}} | {{agent_2_total}} |
| 3 | {{agent_3_name}} | {{agent_3_role}} | {{agent_3_model}} | {{agent_3_status}} | {{agent_3_current_task}} | {{agent_3_completed}} | {{agent_3_total}} |
| 4 | {{agent_4_name}} | {{agent_4_role}} | {{agent_4_model}} | {{agent_4_status}} | {{agent_4_current_task}} | {{agent_4_completed}} | {{agent_4_total}} |

### Status Legend
- `active` - Agente processando tarefa
- `idle` - Agente aguardando próxima tarefa
- `completed` - Agente completou todas as tarefas
- `stuck` - Agente sem progresso por mais de 5 minutos
- `error` - Agente encontrou erro

---

## Progresso de Tarefas

### Overview

```
Completas: {{tasks_completed}}/{{tasks_total}} ({{tasks_percentage}}%)

[{{progress_bar}}] {{tasks_percentage}}%

Exemplo:
[████████████░░░░░░░░] 60%
```

### Tarefas Detalhadas

| Task ID | Tarefa | Agente | Status | Início | Duração |
|---------|--------|--------|--------|--------|---------|
| T1 | {{task_1_desc}} | {{task_1_agent}} | {{task_1_status}} | {{task_1_start}} | {{task_1_duration}} |
| T2 | {{task_2_desc}} | {{task_2_agent}} | {{task_2_status}} | {{task_2_start}} | {{task_2_duration}} |
| T3 | {{task_3_desc}} | {{task_3_agent}} | {{task_3_status}} | {{task_3_start}} | {{task_3_duration}} |
| T4 | {{task_4_desc}} | {{task_4_agent}} | {{task_4_status}} | {{task_4_start}} | {{task_4_duration}} |

### Task Status Legend
- `completed` - Tarefa finalizada com sucesso
- `in_progress` - Tarefa sendo executada
- `pending` - Tarefa aguardando dependências
- `blocked` - Tarefa bloqueada por dependência não resolvida
- `failed` - Tarefa falhou e precisa intervenção

---

## Blockers

> Seção presente apenas quando há bloqueios ativos

| # | Blocker | Agente Afetado | Tarefa Bloqueada | Desde | Ação Sugerida |
|---|---------|----------------|------------------|-------|---------------|
| 1 | {{blocker_1_desc}} | {{blocker_1_agent}} | {{blocker_1_task}} | {{blocker_1_since}} | {{blocker_1_action}} |
| 2 | {{blocker_2_desc}} | {{blocker_2_agent}} | {{blocker_2_task}} | {{blocker_2_since}} | {{blocker_2_action}} |

### Severidade dos Blockers
```
{{#if critical_blockers}}
CRITICAL: {{critical_count}} blocker(s) impedindo progresso geral
{{/if}}
{{#if warning_blockers}}
WARNING: {{warning_count}} blocker(s) causando lentidão
{{/if}}
{{#if no_blockers}}
OK: Nenhum blocker ativo
{{/if}}
```

---

## Atividade Recente

| Timestamp | Agente | Evento | Detalhes |
|-----------|--------|--------|----------|
| {{event_1_time}} | {{event_1_agent}} | {{event_1_type}} | {{event_1_details}} |
| {{event_2_time}} | {{event_2_agent}} | {{event_2_type}} | {{event_2_details}} |
| {{event_3_time}} | {{event_3_agent}} | {{event_3_type}} | {{event_3_details}} |
| {{event_4_time}} | {{event_4_agent}} | {{event_4_type}} | {{event_4_details}} |
| {{event_5_time}} | {{event_5_agent}} | {{event_5_type}} | {{event_5_details}} |

### Tipos de Evento
- `task_started` - Agente iniciou tarefa
- `task_completed` - Agente completou tarefa
- `task_failed` - Tarefa falhou
- `message_sent` - Mensagem entre agentes
- `blocker_detected` - Bloqueio detectado
- `blocker_resolved` - Bloqueio resolvido
- `agent_idle` - Agente ficou idle
- `agent_reassigned` - Tarefa reatribuída

---

## Estimativa de Conclusão

| Métrica | Valor |
|---------|-------|
| **Tarefas restantes** | {{remaining_tasks}} |
| **Agentes ativos** | {{active_agents}} |
| **Velocidade média** | {{avg_task_duration}} por tarefa |
| **ETA estimado** | {{estimated_completion}} |

### Projeção

```
Início:     {{created_at}}
Agora:      {{report_timestamp}}
Decorrido:  {{elapsed_time}}
Restante:   ~{{estimated_remaining}}
ETA:        {{estimated_completion}}
```

---

## Multi-Squad Progress

> Seção presente apenas em execuções multi-squad

### Fila de Squads

| # | Squad | Status | Progresso | Duração |
|---|-------|--------|-----------|---------|
| 1 | {{ms_squad_1}} | {{ms_status_1}} | {{ms_progress_1}} | {{ms_duration_1}} |
| 2 | {{ms_squad_2}} | {{ms_status_2}} | {{ms_progress_2}} | {{ms_duration_2}} |
| 3 | {{ms_squad_3}} | {{ms_status_3}} | {{ms_progress_3}} | {{ms_duration_3}} |

### Squad Status Legend
- `completed` - Squad executado com sucesso
- `executing` - Squad em execução atual
- `queued` - Squad aguardando na fila
- `failed` - Squad falhou

---

**Gerado por:** Team Coordinator v{{version}}
**Próximo refresh:** `*team-status` para atualizar
