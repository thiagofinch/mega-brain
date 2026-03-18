# phase5-person-agents

```yaml
---
task: TSK-051
execution_type: Agent
responsible: "@jarvis"
template: "reference/templates/phase5/MOGA-BRAIN-PHASE5-TEMPLATES.md#5.2"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Phase 5.2 — Person Agents |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | source_code, dna_config_path |
| output | AGENT.md, SOUL.md, MEMORY.md atualizados, template log 5.2 |
| action_items | 3 steps |
| acceptance_criteria | Person agent atualizado com DNA da fonte, template exibido no chat |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| source_code | string | yes | Código da fonte (e.g., CG, JM) |
| dna_config_path | string | yes | Path para DNA-CONFIG.yaml atualizado pela 5.1 |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| agent_md | markdown | agents/persons/{name}/AGENT.md | Agent atualizado |
| soul_md | markdown | agents/persons/{name}/SOUL.md | Soul atualizado |
| memory_md | markdown | agents/persons/{name}/MEMORY.md | Memory com novos insights |
| template_5_2 | display | chat | Template visual obrigatório |

---

## Execution

### Step 1: Load/Create Person Agent

**Quality Gate:** QG-P5-010

1. Verificar se AGENT.md existe em `agents/persons/{source}/`
2. Se não existe → criar com template V3 (REGRA #24)
3. Se existe → carregar para atualização

### Step 2: Update Agent Files

**Quality Gate:** QG-P5-011

1. Atualizar AGENT.md — seções MAPA NEURAL com novos elementos DNA
2. Atualizar SOUL.md — novas filosofias e frases características
3. Atualizar MEMORY.md — novos insights com ^[chunk_id]

### Step 3: Display Template 5.2

**Quality Gate:** QG-P5-012

1. Exibir template visual 5.2 PERSON AGENTS no chat (REGRA #18)
2. Preencher variáveis com dados reais (artefatos criados/atualizados)

---

## Acceptance Criteria

- [ ] AGENT.md criado/atualizado com rastreabilidade 100% (AGENT-INTEGRITY-PROTOCOL)
- [ ] SOUL.md atualizado com novos insights
- [ ] MEMORY.md atualizado com ^[chunk_id] para cada insight
- [ ] Template 5.2 exibido no chat

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| phase5-cargo-agents | person_agent_complete | source_code, agent_path |

---

**Task Version:** 1.0.0
