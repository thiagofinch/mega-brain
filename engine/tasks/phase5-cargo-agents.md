# phase5-cargo-agents

```yaml
---
task: TSK-052
execution_type: Agent
responsible: "@jarvis"
template: "reference/templates/phase5/MOGA-BRAIN-PHASE5-TEMPLATES.md#5.3"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Phase 5.3 — Cargo Agents |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | source_code, dna_config_path, agent_path |
| output | CARGO DNA-CONFIG.yaml enriquecidos, template log 5.3 |
| action_items | 3 steps |
| acceptance_criteria | Cargo agents relevantes enriquecidos com contribuições da fonte |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| source_code | string | yes | Código da fonte |
| dna_config_path | string | yes | Path para DNA-CONFIG.yaml da fonte |
| agent_path | string | yes | Path do person agent (output da 5.2) |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| cargo_updates | array | agents/cargo/{area}/{cargo}/ | Lista de cargos enriquecidos |
| template_5_3 | display | chat | Template visual obrigatório |

---

## Execution

### Step 1: Identify Cargo Contributions

**Quality Gate:** QG-P5-020

1. Analisar DNA da fonte (heurísticas, frameworks, metodologias)
2. Mapear domínios: vendas → @closer/@bdr, finanças → @cfo, marketing → @cmo, etc.
3. Identificar quais cargo agents se beneficiam desta fonte

### Step 2: Enrich Cargo DNA-CONFIG

**Quality Gate:** QG-P5-021

1. Para cada cargo relevante, abrir DNA-CONFIG.yaml
2. Adicionar fonte com peso apropriado (0.0-1.0)
3. Registrar novos insight_ids e chunk_ids
4. Incrementar contadores por camada

### Step 3: Display Template 5.3

**Quality Gate:** QG-P5-022

1. Exibir template visual 5.3 CARGO AGENTS no chat (REGRA #18)
2. Listar cargos enriquecidos com delta de elementos

---

## Acceptance Criteria

- [ ] Domínios mapeados para cargos corretos
- [ ] DNA-CONFIG de cada cargo relevante atualizado
- [ ] Rastreabilidade mantida (insight_ids, chunk_ids)
- [ ] Template 5.3 exibido no chat

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| phase5-theme-dossiers | cargo_agents_complete | source_code, themes |

---

**Task Version:** 1.0.0
