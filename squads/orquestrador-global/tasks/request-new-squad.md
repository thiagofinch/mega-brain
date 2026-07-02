---
task: request-new-squad
name: request-new-squad
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@roteador'
responsavel_type: Agent
atomic_layer: Molecule
elicit: false
estimated_time: 30-60min
model: sonnet
Entrada:
- campo: brief
  tipo: markdown
  obrigatorio: true
  default: null
Saida:
- campo: deliverable
  tipo: markdown
pre_condition: Capability gap confirmed (no existing squad in registry matches required capability)
post_condition: Squad creation request handed off to squad-creator with full context and rationale
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: request-new-squad
squad: orquestrador-global
status: ready
execution_type: hybrid
orchestration_boundary:
  live_routing_performed: false
  external_dispatch_performed: false
  workspace_write_performed: false
megabrain_validation:
  last_run: "20260514-validate-deep"
  validated_at: "2026-05-15T00:00:00Z"
  validator: mega-brain/megabrain-chief
  mode: deep
  squad: orquestrador-global
  status: pass
  evidence:
    - schema_contract_normalized
    - task_boundary_declared
    - plan_only_orchestration_preserved
---

# request-new-squad

**Task ID:** request-new-squad
**Squad:** orquestrador-global
**Type:** request
**Complexity:** medium
**Estimated Tokens:** 1000-1500

---

## Objetivo

Processar solicitação de criação de novo squad quando uma capacidade não é atendida pelo ecossistema atual, encaminhando para o squad-creator com contexto completo.

---

## Trigger Phrases

- "criar novo squad"
- "preciso de um squad para"
- "não tem squad para"
- "solicitar squad"
- "nova capacidade"

---

## Agents Envolvidos

| Agent | Role | Contribuição |
|-------|------|--------------|
| roteador | Triage | Valida necessidade |
| supervisor-sistema | Análise | Verifica gaps |
| → squad-creator | Destino | Recebe solicitação |

---

## Input Obrigatório

```yaml
squad_request:
  necessidade:
    descricao: "o que precisa ser feito"
    frequencia: "com que frequência"
    urgencia: "alta | média | baixa"

  contexto:
    tentativas_anteriores: "squads já consultados"
    por_que_nao_atendeu: "razão da não adequação"
```

---

## Framework de Solicitação

### FASE 1: Validação (@roteador)

```markdown
## 1. Validação da Necessidade

### Checklist de Validação
- [ ] Busca por squads existentes realizada?
- [ ] Nenhum squad atende parcialmente?
- [ ] Necessidade é recorrente (não pontual)?
- [ ] Escopo é suficientemente definido?

### Squads Consultados
| Squad | Capacidade Testada | Por que não atende |
|-------|-------------------|-------------------|
| @[squad-1] | [cap] | [razão] |
| @[squad-2] | [cap] | [razão] |

### Decisão
- [ ] ✅ Prosseguir com solicitação
- [ ] ❌ Redirecionar para squad existente
- [ ] ❌ Necessidade muito específica (task, não squad)
```

### FASE 2: Análise de Gap (@supervisor-sistema)

```markdown
## 2. Análise do Gap

### Gap Identificado
```yaml
gap:
  dominio: "[domínio do gap]"
  capacidades_faltantes:
    - "[capacidade 1]"
    - "[capacidade 2]"
  frequencia_demanda: "[estimativa]"
  impacto_negocio: "alto | médio | baixo"
```

### Relação com Squads Existentes
| Squad Existente | Sobreposição | Pode Expandir? |
|-----------------|--------------|----------------|
| @[squad-1] | X% | Sim/Não |
| @[squad-2] | X% | Sim/Não |

### Recomendação
- [ ] Criar novo squad independente
- [ ] Expandir squad existente
- [ ] Criar sub-squad de squad existente
```

### FASE 3: Preparação do Brief (@roteador)

```markdown
## 3. Brief para Squad Creator

### Contexto do Pedido
```yaml
request:
  id: "req-YYYYMMDD-XXX"
  data: "[data]"
  solicitante: "[quem pediu]"
  urgencia: "[nível]"
```

### Especificação da Necessidade
```yaml
squad_spec:
  nome_sugerido: "[nome]"
  dominio: "[domínio]"
  tipo: "specialist | pipeline | domain | hybrid"

  capacidades_requeridas:
    - "[capacidade 1]"
    - "[capacidade 2]"
    - "[capacidade 3]"

  casos_de_uso:
    - "[caso 1]"
    - "[caso 2]"

  integrações:
    - squad: "@[squad]"
      tipo: "[consume | produce | both]"

  prioridade: "P0 | P1 | P2"
  justificativa: "[por que é necessário]"
```

### Evidências
- [X] solicitações não atendidas nos últimos 30 dias
- Gap confirmado pelo supervisor-sistema
- Impacto estimado: [descrição]
```

### FASE 4: Encaminhamento (@roteador)

```markdown
## 4. Encaminhamento para Squad Creator

### Ação
Encaminhar para `@squad-creator` com:
1. Brief completo
2. Contexto de validação
3. Prioridade definida

### Comando de Criação
```
@squad-creator *create-squad

Brief:
- Nome: [nome sugerido]
- Domínio: [domínio]
- Capacidades: [lista]
- Casos de uso: [lista]
- Prioridade: [P0/P1/P2]
```

### Follow-up
- Notificar solicitante do encaminhamento
- Agendar check-in em 7 dias
- Registrar no log de solicitações
```

---

## Output Esperado

```markdown
# SOLICITAÇÃO DE NOVO SQUAD

**ID:** req-[YYYYMMDD]-[XXX]
**Data:** [data]
**Status:** Encaminhado para @squad-creator

---

## Resumo

**Necessidade:** [descrição curta]
**Domínio:** [domínio]
**Prioridade:** [P0/P1/P2]

---

## Validação

✅ Necessidade validada
✅ Gap confirmado
✅ Não há squad existente adequado

---

## Próximos Passos

1. @squad-creator irá analisar e iniciar criação
2. Estimativa de conclusão: [X dias]
3. Você será notificado quando o squad estiver pronto

---

## Acompanhamento

Para verificar status:
```
@orquestrador *status-request req-[ID]
```
```

---

## Completion Criteria

- [ ] Necessidade validada
- [ ] Squads existentes verificados
- [ ] Gap confirmado
- [ ] Brief preparado
- [ ] Encaminhado para squad-creator
- [ ] Solicitante notificado
- [ ] Registrado para follow-up

---

## Related Files

- tasks/audit-system.md
- tasks/find-capability.md

---

## Version

```yaml
version: 1.0.0
created: 2026-02-04
author: Squad Creator
last_update: 2026-02-04
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*

## Quality Gate
- [ ] Processo documentado com inputs, outputs e owner definidos
- [ ] Checklist de validação aplicado antes da entrega
- [ ] Métricas de qualidade verificadas contra threshold
- [ ] Handoff preparado com contexto para próximo agente
- [ ] Bloqueios escalados em até 24h se não resolvidos
