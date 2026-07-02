---
task: route-request
name: route-request
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@intent-parser'
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
pre_condition: User request payload received with text and optional context/urgency
post_condition: Routing decision (route_direct|route_confirm|present_options|escalate) emitted with squad/agent destination and confidence score
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: route-request
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

# route-request

**Task ID:** route-request
**Squad:** orquestrador-global
**Type:** routing
**Complexity:** low
**Estimated Tokens:** 500-1000

---

## Objetivo

Rotear uma solicitação do usuário para o squad ou agente mais adequado, usando análise semântica e scoring de capacidades.

---

## Trigger Phrases

- "rotear solicitação"
- "qual squad usar"
- "quem pode ajudar com"
- "direcionar para"
- "encaminhar pedido"

---

## Agents Envolvidos

| Agent | Role | Contribuição |
|-------|------|--------------|
| classificador-intenção | Análise | Extrai intenção estruturada |
| indexador-squads | Busca | Encontra squads compatíveis |
| roteador | Decisão | Decide destino final |

---

## Input Obrigatório

```yaml
routing_input:
  solicitacao:
    texto: "texto da solicitação do usuário"
    contexto: "contexto adicional (opcional)"
    urgencia: "normal | urgente"
```

---

## Framework de Roteamento

### FASE 1: Classificação de Intenção (@classificador-intenção)

```markdown
## 1. Análise da Solicitação

### Extração de Intenção
```yaml
intent:
  ação: "[criar | analisar | resolver | configurar | etc]"
  objeto: "[conteúdo | código | campanha | processo | etc]"
  domínio: "[marketing | desenvolvimento | vendas | etc]"
  especificidade: "[genérico | específico]"
```

### Entidades Identificadas
| Entidade | Valor | Confiança |
|----------|-------|-----------|
| Domínio | [valor] | X% |
| Ação | [valor] | X% |
| Objeto | [valor] | X% |

### Keywords Detectadas
- [keyword 1]
- [keyword 2]
- [keyword 3]
```

### FASE 2: Busca de Squads (@indexador-squads)

```markdown
## 2. Squads Compatíveis

### Matching por Capacidade
| Squad | Capacidades Match | Score |
|-------|-------------------|-------|
| [squad 1] | [caps] | X% |
| [squad 2] | [caps] | X% |
| [squad 3] | [caps] | X% |

### Scoring Algorithm
```
score = (semantic_match × 0.4) +
        (capability_coverage × 0.3) +
        (historical_success × 0.2) +
        (availability × 0.1)
```

### Resultado da Busca
```yaml
top_matches:
  - squad: "[squad 1]"
    score: 0.XX
    capabilities_matched: ["cap1", "cap2"]
    agent_sugerido: "[agent]"

  - squad: "[squad 2]"
    score: 0.XX
    capabilities_matched: ["cap1"]
    agent_sugerido: "[agent]"
```
```

### FASE 3: Decisão de Roteamento (@roteador)

```markdown
## 3. Decisão Final

### Thresholds de Decisão
| Score | Ação |
|-------|------|
| >= 0.8 | Rotear direto |
| 0.6 - 0.8 | Rotear com confirmação |
| 0.4 - 0.6 | Apresentar opções |
| < 0.4 | Escalar para humano ou criar squad |

### Decisão
```yaml
decisão:
  tipo: "[route_direct | route_confirm | present_options | escalate]"
  destino:
    squad: "[squad selecionado]"
    agent: "[agent selecionado]"
  confiança: X%
  justificativa: "[por que este squad]"
```

### Caso: Múltiplas Opções
```markdown
Encontrei X squads que podem ajudar:

1. **@[squad-1]** - [descrição curta]
   - Melhor para: [casos de uso]

2. **@[squad-2]** - [descrição curta]
   - Melhor para: [casos de uso]

Qual você prefere?
```

### Caso: Nenhum Match
```markdown
Não encontrei um squad específico para esta solicitação.

Opções:
1. Reformular a solicitação com mais contexto
2. Criar novo squad para esta capacidade
3. Escalar para suporte humano

O que você prefere?
```
```

---

## Output Esperado

```markdown
# RESULTADO DO ROTEAMENTO

**Solicitação:** [resumo]
**Timestamp:** [data/hora]

---

## Análise

**Intenção:** [ação] + [objeto]
**Domínio:** [domínio]
**Confiança:** X%

---

## Roteamento

**Squad:** @[squad-selecionado]
**Agent:** @[agent-selecionado]
**Comando:** *[comando sugerido]

---

## Justificativa

[Por que este squad/agent foi escolhido]

---

## Próximo Passo

[Instrução para o usuário ou auto-execução]
```

---

## Completion Criteria

- [ ] Intenção extraída
- [ ] Squads compatíveis identificados
- [ ] Scoring calculado
- [ ] Decisão tomada
- [ ] Resposta formatada
- [ ] Roteamento executado ou opções apresentadas

---

## Related Files

- tasks/indexar-squad.md
- knowledge/SQUAD-REGISTRY.md

---

## Version

```yaml
version: 1.0.0
created: 2026-02-04
author: Squad Creator
last_update: 2026-02-04
```

## Quality Gate

| Check | Critério | Severidade |
|-------|---------|------------|
| Output completo | Todos os campos do template preenchidos | CRITICAL |
| Qualidade verificada | Revisado contra checklist do squad | HIGH |
| Sem dados inventados | Todas as métricas baseadas em dados reais | CRITICAL |

## Validation

```yaml
validation:
  schema_version: 1
  when: "post"
  checks:
    - id: "has-demand-classification"
      type: "assertion"
      expression: "output.content && (output.content.includes('intent') || output.content.includes('Intenção') || output.content.includes('dominio') || output.content.includes('Domínio'))"
      message: "O roteamento deve conter classificação da demanda com intenção e domínio identificados"
      severity: "CRITICAL"

    - id: "has-routing-decision"
      type: "assertion"
      expression: "output.content && (output.content.includes('decisao') || output.content.includes('Decisão') || output.content.includes('destino') || output.content.includes('Roteamento'))"
      message: "O roteamento deve conter decisão final com tipo (route_direct, route_confirm, present_options, escalate)"
      severity: "CRITICAL"

    - id: "has-squad-assignment"
      type: "assertion"
      expression: "output.content && (output.content.includes('Squad:') || output.content.includes('squad:') || output.content.includes('Agent:') || output.content.includes('agent_sugerido'))"
      message: "O roteamento deve conter atribuição de squad e agente selecionados"
      severity: "HIGH"
  on_fail: "retry"
  max_retries: 2
  escalate_to: "@megabrain-master"
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
