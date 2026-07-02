# phase5-org-live

```yaml
---
task: TSK-054
execution_type: Agent
responsible: "@jarvis"
template: "reference/templates/phase5/MOGA-BRAIN-PHASE5-TEMPLATES.md#5.5"
trigger: "cross_source"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Phase 5.5 — Org-Live (Cross-Source) |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | all_sources_complete, org_context_path |
| output | SUA-EMPRESA context atualizado, SOWs atualizados, template log 5.5 |
| trigger | Manual — após TODAS as fontes completarem 5.1-5.4 |
| action_items | 3 steps |
| acceptance_criteria | Estrutura organizacional sincronizada, SOWs atualizados |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| sources_processed | array | yes | Lista de todas fontes que completaram 5.1-5.4 |
| org_context_path | string | no | Path para [SUA-EMPRESA]-CONTEXT.md |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| org_context | markdown | agents/sua-empresa/ | Contexto org atualizado |
| sow_updates | array | agents/cargo/{area}/{cargo}/ | SOWs atualizados |
| template_5_5 | display | chat | Template visual obrigatório |

---

## Execution

### Step 1: Sync Organizational Structure

**Quality Gate:** QG-P5-040

1. Ler [SUA-EMPRESA]-CONTEXT.md atual
2. Cruzar com novos cargo agent updates de todas fontes
3. Identificar gaps na estrutura organizacional

### Step 2: Update SOWs

**Quality Gate:** QG-P5-041

1. Para cada cargo com novos insights: atualizar SOW
2. Adicionar responsabilidades identificadas nas fontes
3. Registrar fonte de cada atualização

### Step 3: Display Template 5.5

**Quality Gate:** QG-P5-042

1. Exibir template visual 5.5 ORG-LIVE no chat (REGRA #18)
2. Mostrar delta org estrutural

---

## Acceptance Criteria

- [ ] Contexto organizacional sincronizado com todas fontes processadas
- [ ] SOWs de cargos relevantes atualizados
- [ ] Rastreabilidade mantida (fonte de cada update)
- [ ] Template 5.5 exibido no chat

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| phase5-final | org_live_complete | summary_all_sources |

---

**Task Version:** 1.0.0
