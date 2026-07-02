---
task: find-capability
name: find-capability
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@capability-cartographer'
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
pre_condition: Squad registry indexed and searchable (capability_query input received)
post_condition: Ranked list of squads with matching capabilities returned with scores and rationale
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: find-capability
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

# find-capability

**Task ID:** find-capability
**Squad:** orquestrador-global
**Type:** search
**Complexity:** low
**Estimated Tokens:** 500-800

---

## Objetivo

Buscar squads por capacidade específica, retornando opções ranqueadas com detalhes de como cada squad pode ajudar.

---

## Trigger Phrases

- "buscar squad"
- "encontrar quem"
- "qual squad faz"
- "quem pode"
- "listar capacidades"

---

## Agents Envolvidos

| Agent | Role | Contribuição |
|-------|------|--------------|
| indexador-squads | Lead | Busca e matching |

---

## Input Obrigatório

```yaml
search_input:
  capacidade:
    busca: "texto descrevendo a capacidade"
    # ou
    keywords: ["keyword1", "keyword2"]

  filtros:
    dominio: "opcional - filtrar por domínio"
    tipo: "opcional - tipo de squad"
```

---

## Framework de Busca

### FASE 1: Processamento da Query (@indexador-squads)

```markdown
## 1. Análise da Busca

### Query Original
"[texto da busca]"

### Keywords Extraídas
- [keyword 1]
- [keyword 2]
- [keyword 3]

### Sinônimos Expandidos
| Keyword | Sinônimos |
|---------|-----------|
| [kw1] | [syn1, syn2] |
| [kw2] | [syn1, syn2] |

### Filtros Aplicados
- Domínio: [domínio ou "todos"]
- Tipo: [tipo ou "todos"]
```

### FASE 2: Matching (@indexador-squads)

```markdown
## 2. Resultados da Busca

### Algoritmo de Matching
```
score = keyword_match × 0.5 +
        capability_description × 0.3 +
        historical_usage × 0.2
```

### Resultados (Top 5)
| # | Squad | Score | Capacidades Matched |
|---|-------|-------|---------------------|
| 1 | @[squad-1] | X% | [caps] |
| 2 | @[squad-2] | X% | [caps] |
| 3 | @[squad-3] | X% | [caps] |
| 4 | @[squad-4] | X% | [caps] |
| 5 | @[squad-5] | X% | [caps] |
```

### FASE 3: Detalhamento (@indexador-squads)

```markdown
## 3. Detalhes dos Resultados

### 1. @[squad-1] - [nome]
**Score:** X%
**Domínio:** [domínio]
**Descrição:** [descrição curta]

**Capacidades Relevantes:**
- [cap 1]
- [cap 2]

**Tasks Disponíveis:**
- *[task-1] - [descrição]
- *[task-2] - [descrição]

**Como Ativar:** `@[squad-1]` ou `/[comando]`

---

### 2. @[squad-2] - [nome]
...
```

---

## Output Esperado

```markdown
# BUSCA DE CAPACIDADE

**Query:** "[busca original]"
**Resultados:** X squads encontrados

---

## Resultados

### 1. @[squad-1] ⭐ Melhor Match (X%)

**O que faz:** [descrição]

**Pode ajudar com:**
- [capacidade 1]
- [capacidade 2]

**Comandos úteis:**
- `*[comando-1]` - [descrição]
- `*[comando-2]` - [descrição]

---

### 2. @[squad-2] (X%)

**O que faz:** [descrição]

**Pode ajudar com:**
- [capacidade 1]

---

## Nenhum resultado?

Se nenhum squad atender sua necessidade:
1. Reformule a busca com mais detalhes
2. Use `*create-squad-request` para solicitar novo squad
3. Consulte o @orquestrador para orientação
```

---

## Completion Criteria

- [ ] Query processada
- [ ] Keywords extraídas
- [ ] Matching executado
- [ ] Resultados ranqueados
- [ ] Detalhes formatados
- [ ] Instruções de uso incluídas

---

## Related Files

- knowledge/SQUAD-REGISTRY.md
- tasks/route-request.md

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

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
