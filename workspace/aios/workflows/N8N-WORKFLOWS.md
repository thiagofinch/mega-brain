# N8N Workflows - BILHON Automation System

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███╗   ██╗ █████╗ ███╗   ██╗                                             ║
║    ████╗  ██║██╔══██╗████╗  ██║                                             ║
║    ██╔██╗ ██║╚█████╔╝██╔██╗ ██║                                             ║
║    ██║╚██╗██║██╔══██╗██║╚██╗██║                                             ║
║    ██║ ╚████║╚█████╔╝██║ ╚████║                                             ║
║    ╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═══╝                                             ║
║                                                                              ║
║              BILHON N8N AUTOMATION SYSTEM                                    ║
║              Documentacao Completa de Workflows                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Resumo do Sistema

| Metrica | Valor |
|---------|-------|
| **Total Workflows** | 8 |
| **Workflows Ativos** | 3 |
| **Workflows Inativos (Prontos)** | 3 |
| **Workflows Legados** | 2 |
| **Ambiente** | https://thiagofinch.app.n8n.cloud |
| **Versao N8N** | 2.33.0 |
| **Ultima Atualizacao** | 2026-01-11 |
| **User Stories** | US-018 a US-022 |

---

## Workflows Ativos

### 1. BILHON-002-NotificationHub

**ID:** `GqPb5X6K7XWSqlO0`
**Status:** ✅ Ativo
**Nodes:** 3
**Webhook:** `/webhook/notification-hub`

**Proposito:** Hub central de notificacoes. Recebe eventos de outros workflows e distribui para canais apropriados.

**Arquitetura:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Webhook Trigger │────▶│  Process Event  │────▶│ Respond Webhook │
│    (entrada)    │     │   (processar)   │     │    (resposta)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Payload de Entrada:**
```json
{
  "event_type": "task_status_changed",
  "source": "clickup",
  "data": {
    "task_id": "abc123",
    "task_name": "Nome da task",
    "old_status": "backlog",
    "new_status": "em progresso"
  },
  "timestamp": "2026-01-11T20:00:00Z"
}
```

**Endpoints de Saida (Futuros):**
- Slack
- Email
- Telegram
- Webhook customizado

---

### 2. BILHON - ClickUp Status Sync

**ID:** `LUG8Oe2uvul9lAbf`
**Status:** ✅ Ativo
**Nodes:** 4
**Webhook:** `/webhook/clickup-sync`

**Proposito:** Recebe webhooks do ClickUp quando status de tasks mudam e notifica o NotificationHub.

**Arquitetura:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ ClickUp Webhook │────▶│ Filter Status   │────▶│ Format Notif.   │────▶│ Send to Hub     │
│    (entrada)    │     │   (filtrar)     │     │   (formatar)    │     │   (enviar)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Eventos Capturados:**
- `taskStatusUpdated` - Mudanca de status
- `taskCreated` - Nova task criada
- `taskDeleted` - Task deletada

**Configuracao ClickUp:**
1. Acessar Space Settings → Webhooks
2. Adicionar webhook: `https://thiagofinch.app.n8n.cloud/webhook/clickup-sync`
3. Selecionar eventos: Task Status Updated

---

### 3. BILHON - Mega Brain to ClickUp

**ID:** `u3phyaUefq4OxmYl`
**Status:** ✅ Ativo
**Nodes:** 4
**Webhook:** `/webhook/megabrain-clickup`

**Proposito:** Permite que o Mega Brain (JARVIS) crie e atualize tasks no ClickUp programaticamente.

**Arquitetura:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Mega Brain Cmd  │────▶│ Process Command │────▶│ Execute ClickUp │────▶│ Format Response │
│    (webhook)    │     │     (code)      │     │     (API)       │     │   (resposta)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Acoes Suportadas:**

| Acao | Descricao | Payload |
|------|-----------|---------|
| `create_task` | Cria nova task | `{list_id, name, description, status}` |
| `update_status` | Atualiza status | `{task_id, status}` |
| `add_comment` | Adiciona comentario | `{task_id, comment}` |
| `assign_user` | Atribui usuario | `{task_id, user_id}` |

**Exemplo de Uso (JARVIS):**
```bash
curl -X POST https://thiagofinch.app.n8n.cloud/webhook/megabrain-clickup \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_task",
    "data": {
      "list_id": "901310028360",
      "name": "Revisar proposta comercial",
      "description": "Criada automaticamente pelo JARVIS",
      "status": "backlog"
    }
  }'
```

---

## Workflows Inativos

### 4. BILHON-001-HelloWorld

**ID:** `i9ImaKcItU1iQ5St`
**Status:** ⏸️ Inativo
**Nodes:** 2

**Proposito:** Workflow de teste para validar conectividade.

---

### 5. My workflow 2

**ID:** `JrxpSM0HZ9I9ONXZ`
**Status:** ⏸️ Inativo
**Nodes:** 19
**Tags:** Social Media Data Scrape

**Proposito:** Workflow legado de scraping de redes sociais.

---

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       BILHON AUTOMATION ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                              ┌──────────────────┐                               │
│                              │  NOTIFICATION    │                               │
│                              │      HUB         │                               │
│                              │  (GqPb5X6K...)   │                               │
│                              └────────┬─────────┘                               │
│                                       │                                          │
│                     ┌─────────────────┼─────────────────┐                       │
│                     │                 │                 │                       │
│                     ▼                 ▼                 ▼                       │
│              ┌──────────┐      ┌──────────┐      ┌──────────┐                   │
│              │  Slack   │      │  Email   │      │ Telegram │                   │
│              │ (futuro) │      │ (futuro) │      │ (futuro) │                   │
│              └──────────┘      └──────────┘      └──────────┘                   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                          FONTES DE EVENTOS                               │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  ┌────────────────────┐          ┌────────────────────┐                 │    │
│  │  │   CLICKUP SYNC     │          │   MEGA BRAIN       │                 │    │
│  │  │  (LUG8Oe2uvul...)  │          │  (u3phyaUefq...)   │                 │    │
│  │  │                    │          │                    │                 │    │
│  │  │  ClickUp → N8N     │          │  JARVIS → ClickUp  │                 │    │
│  │  └────────────────────┘          └────────────────────┘                 │    │
│  │           │                               ▲                              │    │
│  │           │                               │                              │    │
│  │           ▼                               │                              │    │
│  │  ┌────────────────────┐          ┌────────────────────┐                 │    │
│  │  │      CLICKUP       │◀────────▶│    MEGA BRAIN      │                 │    │
│  │  │   (Workspace)      │          │    (JARVIS)        │                 │    │
│  │  └────────────────────┘          └────────────────────┘                 │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## URLs de Webhook

| Workflow | Endpoint | Metodo |
|----------|----------|--------|
| NotificationHub | `https://thiagofinch.app.n8n.cloud/webhook/notification-hub` | POST |
| ClickUp Sync | `https://thiagofinch.app.n8n.cloud/webhook/clickup-sync` | POST |
| Mega Brain → ClickUp | `https://thiagofinch.app.n8n.cloud/webhook/megabrain-clickup` | POST |

---

## Workflows Prontos (Aguardando Ativacao)

### BILHON-005-FinancialAlerts (US-020)

**ID:** `lXeTEJmDi0EOdOvU`
**Status:** ⏸️ Criado - Aguarda Ativacao
**Nodes:** 5
**Trigger:** Schedule (24h)

**Proposito:** Monitorar metricas financeiras e disparar alertas automaticos.

**Arquitetura:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Daily Check │────▶│ Fetch Metrics│────▶│ Check Thres │────▶│ Has Alerts? │────▶│ Send to Hub │
│  (schedule) │     │   (HTTP)    │     │   (code)    │     │  (filter)   │     │   (HTTP)    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Thresholds Configurados:**
- MRR queda > 10% → Alerta HIGH
- Churn > 10% → Alerta HIGH
- Custos > 20% do budget → Alerta MEDIUM

---

### BILHON-006-CallsPipeline (US-021)

**ID:** `ggo7iPoqaRhzGOzx`
**Status:** ⏸️ Criado - Aguarda Ativacao
**Nodes:** 5
**Webhook:** `/webhook/fathom-calls`

**Proposito:** Processar transcricoes de calls (Fathom) automaticamente.

**Arquitetura:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│Fathom Webhk │────▶│Extract Meta │────▶│Format Brain │────▶│ Notify Hub  │────▶│  Respond    │
│  (entrada)  │     │   (code)    │     │   (code)    │     │   (HTTP)    │     │  (success)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Classificacao Automatica:**
- CLIENT → `/bilhon/calls/CLIENTS/`
- MENTOR → `/bilhon/calls/MENTORS/`
- TEAM → `/bilhon/calls/TEAM/`

---

### BILHON-007-ExecutionDashboard (US-022)

**ID:** `BgzTdfWdt1SfGf2T`
**Status:** ⏸️ Criado - Aguarda Ativacao
**Nodes:** 4
**Webhook:** `/webhook/dashboard-data` (GET)

**Proposito:** Agregar dados de execucao e fornecer metricas para dashboard.

**Arquitetura:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│Dashboard Req│────▶│Aggregate Data│────▶│Format Resp  │────▶│Return Data  │
│   (GET)     │     │   (code)    │     │   (set)     │     │  (respond)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**Dados Agregados:**
- Execucoes de workflows (total, sucesso, falha)
- Status de integracoes
- Resumo de alertas
- Resumo de tasks

---

## Configuracao ClickUp

### Workspace ID
`9013070037`

### Space: Bilhon Cortex
`90131690598`

### Listas Principais

| Lista | ID | Uso |
|-------|-------|-----|
| Backlog | `901310028360` | Tasks nao iniciadas |
| Campanha Evergreen Macro | `901310040851` | Campanhas marketing |

---

## Troubleshooting

### Webhook nao responde

1. Verificar se workflow esta ativo no N8N
2. Verificar URL do webhook (case-sensitive)
3. Testar com curl simples
4. Verificar logs de execucao no N8N

### ClickUp nao envia eventos

1. Verificar configuracao do webhook no ClickUp
2. Confirmar que eventos corretos estao selecionados
3. Testar manualmente mudando status de task

---

## Changelog

| Versao | Data | Mudancas |
|--------|------|----------|
| 2.0.0 | 2026-01-11 | US-020/021/022: +3 workflows criados (Financial, Calls, Dashboard) |
| 1.0.0 | 2026-01-11 | US-018/019: Documentacao inicial - 3 workflows ativos |

---

**Ultima Atualizacao:** 2026-01-11
**Versao:** 2.0.0
**Autor:** JARVIS
**User Stories:** US-018, US-019, US-020, US-021, US-022
