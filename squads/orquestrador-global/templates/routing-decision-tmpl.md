# Routing Decision Template

> Template para documentar decisões de roteamento do Orquestrador Global

## Metadata

```yaml
template:
  id: routing-decision
  name: Routing Decision
  agent: roteador
  output_format: markdown
```

---

# Routing Decision | {{decision_id}}

**Timestamp:** {{timestamp}}
**Request ID:** {{request_id}}
**Tipo:** {{decision_type}} (Direct Route | Confirm | Escalate | Create Squad)

---

## Solicitação Original

### Input do Usuário
```
{{user_input}}
```

### Contexto
| Campo | Valor |
|-------|-------|
| **Origem** | {{origin}} |
| **Usuário/Sistema** | {{requester}} |
| **Sessão** | {{session_id}} |
| **Histórico** | {{has_history}} |

---

## Classificação de Intenção

### Intenção Estruturada

```yaml
intent:
  primary: {{primary_intent}}
  secondary: {{secondary_intent}}
  action: {{action_type}}
  domain: {{domain}}
  entities:
    - type: {{entity_1_type}}
      value: {{entity_1_value}}
    - type: {{entity_2_type}}
      value: {{entity_2_value}}
  context:
    urgency: {{urgency}}
    complexity: {{complexity}}
```

### Confiança da Classificação
| Aspecto | Score |
|---------|-------|
| **Intenção primária** | {{confidence_primary}}% |
| **Domínio** | {{confidence_domain}}% |
| **Entidades** | {{confidence_entities}}% |
| **Overall** | {{confidence_overall}}% |

---

## Squad Matching

### Candidatos Encontrados

| # | Squad | Score | Match Reason |
|---|-------|-------|--------------|
| 1 | {{squad_1}} | {{score_1}} | {{reason_1}} |
| 2 | {{squad_2}} | {{score_2}} | {{reason_2}} |
| 3 | {{squad_3}} | {{score_3}} | {{reason_3}} |

### Scoring Breakdown (Squad Selecionado)

| Componente | Peso | Score | Contribuição |
|------------|------|-------|--------------|
| Match de Domínio | 40% | {{domain_score}} | {{domain_contrib}} |
| Match de Problemas | 35% | {{problems_score}} | {{problems_contrib}} |
| Match de Tipo de Tarefa | 15% | {{task_score}} | {{task_contrib}} |
| Match de Keywords | 10% | {{keywords_score}} | {{keywords_contrib}} |
| **TOTAL** | 100% | **{{total_score}}** | - |

---

## Decisão de Roteamento

### Threshold Analysis

```
Score: {{total_score}}

┌────────────────────────────────────────────────────────┐
│ 0.0   0.4   0.6   0.8   1.0                            │
│  │─────┼─────┼─────┼─────│                             │
│  │ ESC │CONF │ DIR │                                   │
│  │     │     │     │                                   │
│  │     │     │  ▲  │  ← Score atual                    │
│  │     │     │  │  │                                   │
└────────────────────────────────────────────────────────┘

ESC = Escalar para humano (<0.6)
CONF = Confirmar com usuário (0.6-0.79)
DIR = Roteamento direto (≥0.8)
```

### Decisão

| Campo | Valor |
|-------|-------|
| **Ação** | {{action}} |
| **Squad Destino** | {{target_squad}} |
| **Agente Destino** | {{target_agent}} |
| **Workflow** | {{target_workflow}} |
| **Confiança** | {{confidence_level}} |

### Justificativa
```
{{justification}}
```

---

## Execução

### Handoff Payload

```yaml
handoff:
  to_squad: {{target_squad}}
  to_agent: {{target_agent}}
  request:
    original: "{{user_input}}"
    structured_intent: {{structured_intent}}
    context:
      session_id: {{session_id}}
      routing_decision_id: {{decision_id}}
      confidence: {{total_score}}
```

### Status

| Etapa | Status | Timestamp |
|-------|--------|-----------|
| Classificação | {{status_classification}} | {{ts_classification}} |
| Indexação | {{status_indexing}} | {{ts_indexing}} |
| Roteamento | {{status_routing}} | {{ts_routing}} |
| Handoff | {{status_handoff}} | {{ts_handoff}} |
| Resposta | {{status_response}} | {{ts_response}} |

---

## Alternativas Consideradas

### Por que não {{alt_squad_1}}?
{{alt_1_reason}}

### Por que não {{alt_squad_2}}?
{{alt_2_reason}}

---

## Fallbacks Aplicados

| Situação | Fallback | Aplicado? |
|----------|----------|-----------|
| Sem match | Solicitar mais contexto | {{fallback_no_match}} |
| Baixa confiança | Apresentar opções | {{fallback_low_conf}} |
| Nova capacidade | Rotear para squad-creator | {{fallback_new_cap}} |

---

## Feedback Loop

### Para Melhorar o Roteamento

| Pergunta | Resposta |
|----------|----------|
| Roteamento foi correto? | {{feedback_correct}} |
| Squad conseguiu atender? | {{feedback_served}} |
| Houve re-roteamento? | {{feedback_rerouted}} |
| Sugestão de melhoria | {{feedback_suggestion}} |

---

## Métricas

| Métrica | Valor |
|---------|-------|
| **Latência total** | {{latency_total}}ms |
| **Latência classificação** | {{latency_classification}}ms |
| **Latência indexação** | {{latency_indexing}}ms |
| **Latência decisão** | {{latency_decision}}ms |

---

## Audit Trail

```
{{audit_log}}
```

---

**Processado por:** Orquestrador Global v{{version}}
**Timestamp:** {{timestamp}}
