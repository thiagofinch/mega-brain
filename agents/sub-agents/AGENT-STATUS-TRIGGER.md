# AGENT-STATUS-TRIGGER

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ████████╗██████╗ ██╗ ██████╗  ██████╗ ███████╗██████╗                     ║
║    ╚══██╔══╝██╔══██╗██║██╔════╝ ██╔════╝ ██╔════╝██╔══██╗                    ║
║       ██║   ██████╔╝██║██║  ███╗██║  ███╗█████╗  ██████╔╝                    ║
║       ██║   ██╔══██╗██║██║   ██║██║   ██║██╔══╝  ██╔══██╗                    ║
║       ██║   ██║  ██║██║╚██████╔╝╚██████╔╝███████╗██║  ██║                    ║
║       ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝                    ║
║                                                                              ║
║              STATUS TRIGGER AGENT                                            ║
║              Automacao baseada em mudancas de status                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## IDENTIDADE

| Campo | Valor |
|-------|-------|
| **Nome** | STATUS-TRIGGER |
| **Tipo** | SUB-AGENT (Automation) |
| **Owner** | JARVIS |
| **Criado** | 2026-01-11 |
| **User Story** | US-010 |

---

## PROPOSITO

O STATUS-TRIGGER e um agente de automacao que reage a mudancas de status em sistemas externos (ClickUp, N8N) e executa acoes apropriadas dentro do Mega Brain.

### Responsabilidades

1. **Monitorar** eventos de mudanca de status vindos do NotificationHub
2. **Classificar** o tipo de evento e sua prioridade
3. **Disparar** acoes automaticas baseadas em regras configuradas
4. **Notificar** stakeholders quando necessario
5. **Logar** todas as acoes para auditoria

---

## CONFIGURACAO

```yaml
agent:
  id: "status-trigger"
  type: "automation"
  enabled: true

sources:
  - name: "clickup"
    webhook: "/webhook/clickup-sync"
    events:
      - "taskStatusUpdated"
      - "taskCreated"
      - "taskDeleted"
      - "taskAssigneeUpdated"

  - name: "n8n"
    webhook: "/webhook/notification-hub"
    events:
      - "workflow_completed"
      - "workflow_failed"
      - "execution_started"

priority_mapping:
  P1_CRITICAL:
    statuses: ["atrasado", "bloqueado"]
    notify: ["owner", "head_ops"]
    slack_channel: "#alerts-critical"

  P2_HIGH:
    statuses: ["aguardando revisão", "reprovado"]
    notify: ["owner"]
    slack_channel: "#alerts-high"

  P3_NORMAL:
    statuses: ["em progresso", "concluído"]
    notify: []
    log_only: true

  P4_LOW:
    statuses: ["backlog", "onhold", "cancelado"]
    notify: []
    log_only: true
```

---

## REGRAS DE ACAO

### Regra 1: Task Atrasada

```
TRIGGER: status = "atrasado"
CONDITIONS:
  - task.due_date < now()
  - task.priority in [1, 2]
ACTIONS:
  1. Notificar owner via Slack
  2. Notificar gestor direto
  3. Criar alerta no dashboard
  4. Logar evento
```

### Regra 2: Task Bloqueada

```
TRIGGER: status = "bloqueado"
CONDITIONS:
  - any
ACTIONS:
  1. Notificar owner: "O que esta bloqueando?"
  2. Criar subtask: "Resolver bloqueio"
  3. Escalar se > 24h sem resolucao
  4. Logar evento
```

### Regra 3: Task Concluida (Quality Gate)

```
TRIGGER: status = "concluído"
CONDITIONS:
  - task.custom_fields.quality_gate = true
ACTIONS:
  1. Verificar se aprovacao existe
  2. Se nao: Reverter para "aguardando revisão"
  3. Notificar: "Quality Gate nao cumprido"
  4. Logar evento
```

### Regra 4: Candidato em Oferta

```
TRIGGER: status = "OFERTA"
CONDITIONS:
  - space = "RH"
  - folder = "HIRING"
ACTIONS:
  1. Notificar [OWNER] e CEO
  2. Criar task: "Aprovacao executiva"
  3. Definir SLA: 48h
  4. Logar evento
```

### Regra 5: Workflow N8N Falhou

```
TRIGGER: event = "workflow_failed"
CONDITIONS:
  - workflow.name contains "[SUA EMPRESA]"
ACTIONS:
  1. Notificar Head Ops
  2. Criar task em "[Sua Empresa] Cortex"
  3. Capturar error log
  4. Logar evento
```

---

## INTERFACE COM N8N

### Webhook Payload Esperado

```json
{
  "type": "clickup_status_change",
  "task_id": "abc123",
  "task_name": "Nome da Task",
  "old_status": "em progresso",
  "new_status": "atrasado",
  "space_id": "${CLICKUP_LIST_ID}",
  "assignee": "user@[sua-empresa].com",
  "timestamp": "2026-01-11T14:30:00Z",
  "metadata": {
    "due_date": "2026-01-10",
    "priority": 1,
    "custom_fields": {}
  }
}
```

### Acoes Disponiveis

| Acao | Endpoint | Descricao |
|------|----------|-----------|
| `notify_slack` | N8N Slack Node | Envia mensagem para canal |
| `create_task` | ClickUp MCP | Cria nova task |
| `update_task` | ClickUp MCP | Atualiza task existente |
| `send_email` | N8N Email Node | Envia email |
| `log_event` | Local JSON | Loga evento |

---

## INTEGRACAO COM MEGA BRAIN

### Atualizacao de Estado

Quando um evento e processado, o agente atualiza:

1. **MISSION-STATE.json** - Se evento relacionado a missao ativa
2. **JARVIS-STATE.json** - Registro de acao do agente
3. **logs/events.jsonl** - Log persistente

### Comunicacao com JARVIS

```
STATUS-TRIGGER → JARVIS
  - Reporta eventos processados
  - Solicita decisoes em casos ambiguos
  - Escala problemas criticos

JARVIS → STATUS-TRIGGER
  - Configura novas regras
  - Ajusta prioridades
  - Desativa/ativa regras
```

---

## METRICAS

| Metrica | Descricao | Target |
|---------|-----------|--------|
| **Events Processed** | Total de eventos processados | - |
| **Avg Response Time** | Tempo medio de resposta | < 5s |
| **Actions Triggered** | Acoes executadas | - |
| **Errors** | Erros de processamento | < 1% |
| **Escalations** | Eventos escalados | < 5% |

---

## LOGS

### Formato de Log

```json
{
  "timestamp": "2026-01-11T14:30:00Z",
  "agent": "status-trigger",
  "event_type": "clickup_status_change",
  "task_id": "abc123",
  "old_status": "em progresso",
  "new_status": "atrasado",
  "priority": "P1_CRITICAL",
  "actions_taken": [
    {"action": "notify_slack", "target": "#alerts-critical", "status": "success"},
    {"action": "notify_owner", "target": "user@[sua-empresa].com", "status": "success"}
  ],
  "processing_time_ms": 234
}
```

### Localizacao

- **Real-time**: `/logs/events.jsonl`
- **Daily**: `/logs/DAILY/events-YYYY-MM-DD.jsonl`
- **Dashboard**: N8N Execution History

---

## ATIVACAO

### Via N8N Workflow

O agente e ativado pelo workflow `[SUA EMPRESA] - ClickUp Status Sync` que:

1. Recebe webhook do ClickUp
2. Filtra eventos de status
3. Formata payload
4. Envia para NotificationHub
5. NotificationHub processa regras do STATUS-TRIGGER

### Diagrama de Fluxo

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   ClickUp    │────▶│  ClickUp     │────▶│ Notification │────▶│   STATUS     │
│   Webhook    │     │  Sync WF     │     │    Hub WF    │     │   TRIGGER    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                      │
                                                                      ▼
                                          ┌──────────────────────────────────┐
                                          │  ACOES:                          │
                                          │  - Slack Notification            │
                                          │  - Email                         │
                                          │  - Create Task                   │
                                          │  - Update State                  │
                                          │  - Log Event                     │
                                          └──────────────────────────────────┘
```

---

## PROXIMAS EVOLUCOES

1. **ML-based Priority**: Usar ML para ajustar prioridades automaticamente
2. **Smart Routing**: Rotear para agente especialista baseado em contexto
3. **Predictive Alerts**: Alertar antes de task ficar atrasada
4. **Auto-Resolution**: Resolver bloqueios simples automaticamente

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              AGENT CRIADO POR JARVIS                                         ║
║              Data: 2026-01-11                                                ║
║              User Story: US-010                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
