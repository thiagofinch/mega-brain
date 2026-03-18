# phase5-final

```yaml
---
task: TSK-055
execution_type: Agent
responsible: "@jarvis"
template: "reference/templates/phase5/MOGA-BRAIN-PHASE5-TEMPLATES.md#5.FINAL"
trigger: "cross_source"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Phase 5.FINAL — Consolidated Report (Cross-Source) |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | all_sources_complete, all_dossiers, all_agents |
| output | Relatório consolidado cross-source, SESSION-LOG, template 5.FINAL |
| trigger | Manual — após phase5-org-live completar |
| action_items | 4 steps |
| acceptance_criteria | Relatório cross-source completo, MISSION-STATE atualizado, template exibido |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| sources_processed | array | yes | Lista de todas fontes processadas |
| mission_state_path | string | yes | Path para MISSION-STATE.json |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| final_report | markdown | logs/phase5-final-{date}.md | Relatório cross-source |
| session_log | markdown | .claude/sessions/SESSION-{ts}.md | Log da sessão |
| mission_state | json | .claude/mission-control/MISSION-STATE.json | Estado atualizado |
| template_final | display | chat | Template visual 5.FINAL obrigatório |

---

## Execution

### Step 1: Cross-Source Metrics

**Quality Gate:** QG-P5-050

1. Consolidar totais de todas fontes: chunks, insights, DNA elements
2. Calcular delta total (antes vs depois de todas fontes)
3. Listar todos artefatos criados/atualizados

### Step 2: Knowledge Graph Summary

**Quality Gate:** QG-P5-051

1. Listar todos PERSON agents atualizados
2. Listar todos CARGO agents enriquecidos
3. Listar todos THEME dossiers criados/atualizados
4. Listar conexões cross-source identificadas

### Step 3: Update MISSION-STATE

**Quality Gate:** QG-P5-052

1. Atualizar phase_status → COMPLETE para todas fontes processadas
2. Atualizar percent_complete
3. Definir next_action para próxima missão

### Step 4: Display Template 5.FINAL + Save Session

**Quality Gate:** QG-P5-053

1. Exibir template visual 5.FINAL CONSOLIDADO no chat (REGRA #18)
2. Salvar SESSION-LOG via skill /save
3. Marcar Fase 5 como COMPLETE

---

## Acceptance Criteria

- [ ] Relatório cross-source completo com métricas reais
- [ ] MISSION-STATE.json atualizado
- [ ] SESSION-LOG salvo
- [ ] Template 5.FINAL exibido no chat
- [ ] validate_phase5.py executado (REGRA #23) — exit code 0

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| (nova missão) | phase5_complete | - |

---

**Task Version:** 1.0.0
