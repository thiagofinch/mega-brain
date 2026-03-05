# phase5-foundation

```yaml
---
task: TSK-050
execution_type: Agent
responsible: "@jarvis"
template: "reference/templates/phase5/MOGA-BRAIN-PHASE5-TEMPLATES.md#5.1"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Phase 5.1 — Foundation |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | source_code, batch_ids, dna_config |
| output | SOURCE-XX.md, DNA layers (5), template log 5.1 |
| action_items | 4 steps |
| acceptance_criteria | DNA consolidado, SOURCE-XX.md criado, template exibido no chat |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| source_code | string | yes | Código da fonte (e.g., CG, JM) |
| batch_ids | array | yes | IDs de todos os batches da fonte |
| dna_config_path | string | yes | Path para DNA-CONFIG.yaml |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| source_log | markdown | logs/SOURCES/SOURCE-{code}.md | Log consolidado da fonte |
| dna_updated | yaml | knowledge/dna/persons/{source}/ | 5 camadas atualizadas |
| template_5_1 | display | chat | Template visual obrigatório |

---

## Execution

### Step 1: Load All Batches (Source Isolation)

**Quality Gate:** QG-P5-001

1. Carregar TODOS os batches da fonte (source_code) em sequência
2. NÃO carregar batches de outras fontes
3. Consolidar insights por camada DNA

### Step 2: Update DNA Layers

**Quality Gate:** QG-P5-002

1. Atualizar FILOSOFIAS.yaml (+N elementos)
2. Atualizar MODELOS-MENTAIS.yaml (+N elementos)
3. Atualizar HEURISTICAS.yaml (+N elementos)
4. Atualizar FRAMEWORKS.yaml (+N elementos)
5. Atualizar METODOLOGIAS.yaml (+N elementos)

### Step 3: Create SOURCE Log

**Quality Gate:** QG-P5-003

1. Criar `logs/SOURCES/SOURCE-{source_code}.md`
2. Incluir métricas por batch, top insights, totais DNA

### Step 4: Display Template 5.1

**Quality Gate:** QG-P5-004

1. Exibir template visual 5.1 FOUNDATION no chat (REGRA #18)
2. Preencher variáveis com dados reais

---

## Acceptance Criteria

- [ ] Todos batches da fonte carregados (sem cross-source)
- [ ] Todas 5 camadas DNA atualizadas
- [ ] SOURCE-{code}.md criado em logs/SOURCES/
- [ ] Template 5.1 exibido no chat

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| phase5-person-agents | foundation_complete | source_code, dna_config_path |

---

**Task Version:** 1.0.0
