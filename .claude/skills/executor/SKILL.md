---
name: executor
version: 1.0.0
description: Orquestrador de operacoes autonomas. Executa acoes no ClickUp, N8N e Google Drive baseado em decisoes dos agentes.
triggers:
  - executar
  - criar task
  - notificar
  - agendar
  - processar
user_invocable: false
auto_trigger: true
---

# SKILL: Executor - Operacoes Autonomas

## Proposito

Orquestrar e executar acoes autonomas baseadas em decisoes dos agentes TALENT, FINANCE e COUNCIL. Este skill e ativado AUTOMATICAMENTE quando outros agentes produzem outputs acionaveis.

## Quando Ativar Automaticamente

```yaml
triggers:
  - AGENT-TALENT emite HELL YES
  - AGENT-FINANCE emite alerta
  - COUNCIL emite decisao com confianca >= 70%
  - Usuario solicita execucao explicita
```

## Contexto Obrigatorio

```
OBRIGATORIO:
1. /[sua-empresa]/agents/AGENT-EXECUTOR.md (persona e capacidades)
2. /[sua-empresa]/[SUA EMPRESA]-CONTEXT.md (contexto operacional)

INTEGRACAO:
- ClickUp MCP (criar/atualizar tasks)
- N8N Webhooks (notificacoes, workflows)
- Google Drive MCP (arquivos, planilhas)
```

## Classificacao de Risco

Antes de executar, classificar:

```
LOW RISK (Executar automaticamente):
- Criar task no ClickUp
- Atualizar status
- Enviar notificacao
- Gerar relatorio

MEDIUM RISK (Confirmar com usuario):
- Criar campanha
- Aprovar gasto operacional
- Modificar processo

HIGH RISK (Escalar para COUNCIL):
- Contratacao/demissao
- Investimento > R$ 100K
- Mudanca estrategica
```

## Acoes Disponiveis

### 1. Task Management (ClickUp)

```bash
# Criar task
mcp__clickup__clickup_create_task(
  list_id: "${CLICKUP_LIST_ID}",
  name: "Nome da task",
  description: "Descricao",
  status: "backlog"
)

# Atualizar status
mcp__clickup__clickup_update_task(
  task_id: "id",
  status: "em progresso"
)
```

### 2. Notificacoes (N8N)

```bash
# Enviar para NotificationHub
curl -X POST https://<your-n8n-instance>.app.n8n.cloud/webhook/notification-hub \
  -d '{
    "event_type": "alert",
    "source": "AGENT-FINANCE",
    "data": {...}
  }'
```

### 3. Google Drive

```bash
# Ler planilha
mcp__gdrive__gsheets_read(spreadsheetId: "id")

# Atualizar celula
mcp__gdrive__gsheets_update_cell(fileId: "id", range: "A1", value: "valor")
```

## Fluxo de Execucao

```
1. RECEBER trigger de outro agente
2. CLASSIFICAR nivel de risco
3. SE LOW → EXECUTAR automaticamente
   SE MEDIUM → CONFIRMAR com usuario
   SE HIGH → ESCALAR para COUNCIL
4. LOGAR acao em /logs/EXECUTOR/
5. RETORNAR confirmacao
```

## Logging Obrigatorio

Toda acao deve ser logada:

```json
{
  "timestamp": "ISO8601",
  "action": "nome_acao",
  "trigger": "agente:evento",
  "risk_level": "LOW|MEDIUM|HIGH",
  "status": "SUCCESS|FAILED|PENDING"
}
```

## Exemplo de Uso Automatico

**AGENT-TALENT emite HELL YES para candidato:**

```
EXECUTOR detecta trigger: AGENT-TALENT:HELL_YES
EXECUTOR classifica: LOW RISK (criar task)
EXECUTOR executa:
  → mcp__clickup__clickup_create_task(
      list_id: "${CLICKUP_LIST_ID}",
      name: "Onboarding: Maria Silva - SDR",
      description: "Candidata aprovada via AGENT-TALENT\nScore: 8.5/10"
    )
EXECUTOR loga: /logs/EXECUTOR/2026-01-11.jsonl
EXECUTOR notifica: Usuario informado via chat
```

## Principios Inviolaveis

1. **Sempre logar** - Nenhuma acao sem registro
2. **Classificar risco** - Nunca executar HIGH sem aprovacao
3. **Transparencia** - Usuario sempre sabe o que foi feito
4. **Rastreabilidade** - Toda acao tem origem identificada

---

**Ultima Atualizacao:** 2026-01-11
**User Story:** US-026
