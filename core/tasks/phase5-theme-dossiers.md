# phase5-theme-dossiers

```yaml
---
task: TSK-053
execution_type: Agent
responsible: "@jarvis"
template: "reference/templates/phase5/MOGA-BRAIN-PHASE5-TEMPLATES.md#5.4"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Phase 5.4 — Theme Dossiers |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | source_code, themes, batch_ids |
| output | DOSSIER-{TEMA}.md criados/atualizados, template log 5.4 |
| action_items | 4 steps |
| acceptance_criteria | Todos dossiers temáticos atualizados (REGRA #21), template exibido |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| source_code | string | yes | Código da fonte |
| themes | array | yes | Temas identificados na fase 5.1 |
| batch_ids | array | yes | IDs dos batches para comparação de versão |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| dossiers_updated | array | knowledge/dossiers/themes/ | Dossiers criados ou atualizados |
| template_5_4 | display | chat | Template visual obrigatório |

---

## Execution

### Step 1: Map Themes to Dossiers

**Quality Gate:** QG-P5-030

1. Para cada tema dos batches, verificar se DOSSIER-{TEMA}.md existe
2. Registrar: existentes (precisam atualização) vs novos (precisam criação)

### Step 2: Version Check (REGRA #21)

**Quality Gate:** QG-P5-031

1. Para cada dossier existente: comparar data_modificação vs data dos batches
2. Se batches > dossier → marcar para ATUALIZAÇÃO obrigatória
3. Se dossier >= batches → SKIP (já atualizado)
4. NUNCA assumir "existe = atualizado"

### Step 3: Create/Update Dossiers

**Quality Gate:** QG-P5-032

1. Para dossiers novos: criar com frameworks/heurísticas/metodologias dos batches
2. Para dossiers desatualizados: adicionar novos elementos, incrementar versão (v2.0 → v3.0)
3. Cross-referenciar com person agent e cargo agents relevantes

### Step 4: Display Template 5.4

**Quality Gate:** QG-P5-033

1. Exibir template visual 5.4 THEME DOSSIERS no chat (REGRA #18)
2. Listar dossiers criados/atualizados com delta

---

## Acceptance Criteria

- [ ] Todos temas mapeados para dossiers
- [ ] Verificação de versão realizada (data_dossier vs data_batches)
- [ ] Dossiers desatualizados atualizados com versão incrementada
- [ ] Cross-referências com person/cargo agents adicionadas
- [ ] Template 5.4 exibido no chat

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| (próxima fonte) | theme_dossiers_complete | source complete, log final da fonte |
| phase5-org-live | all_sources_complete | lista de todas fontes processadas |

---

**Task Version:** 1.0.0
