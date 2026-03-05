# TASK REGISTRY

> **Versão:** 1.0.0
> **Última Atualização:** 2026-02-26
> **Padrão:** HO-TP-001 (Pedro/aios-core)

---

## Visão Geral

Tasks são unidades ATÔMICAS de execução que o JARVIS orquestra via workflows.
Diferente de Skills (user-facing), Tasks são MACHINE-ONLY.

---

## Categorias de Tasks

| Categoria | Descrição | Tasks |
|-----------|-----------|-------|
| FOUNDATION | Sem dependências, base do sistema | detect-role, normalize-entities, validate-schema |
| INTELLIGENCE | Dependem de Foundation | analyze-themes, detect-business-model, score-viability |
| EXTRACTION | Dependem de Intelligence | extract-dna, extract-knowledge, generate-skill |
| PIPELINE | Dependem de Extraction | process-batch, trigger-agent, trigger-dossier |
| VALIDATION | Dependem de Pipeline | validate-cascade, verify-completeness |

---

## Task Index

### FOUNDATION TASKS

| Task ID | Name | Script | Status |
|---------|------|--------|--------|
| TSK-001 | detect-role | role_detector.py | ✅ ACTIVE |
| TSK-002 | normalize-entities | entity_normalizer.py | ✅ ACTIVE |
| TSK-003 | validate-schema | - | 📋 PLANNED |

### INTELLIGENCE TASKS

| Task ID | Name | Script | Status |
|---------|------|--------|--------|
| TSK-010 | analyze-themes | theme_analyzer.py | ✅ ACTIVE |
| TSK-011 | detect-business-model | business_model_detector.py | ✅ ACTIVE |
| TSK-012 | score-viability | viability_scorer.py | ✅ ACTIVE |

### EXTRACTION TASKS

| Task ID | Name | Script | Status |
|---------|------|--------|--------|
| TSK-020 | extract-dna | - | ✅ ACTIVE |
| TSK-021 | extract-knowledge | - | ✅ ACTIVE |
| TSK-022 | generate-skill | skill_generator.py | ✅ ACTIVE |

### PIPELINE TASKS

| Task ID | Name | Script | Status |
|---------|------|--------|--------|
| TSK-030 | process-batch | - | ✅ ACTIVE |
| TSK-031 | trigger-agent | agent_trigger.py | ✅ ACTIVE |
| TSK-032 | trigger-dossier | dossier_trigger.py | ✅ ACTIVE |

### VALIDATION TASKS

| Task ID | Name | Script | Status |
|---------|------|--------|--------|
| TSK-040 | validate-cascade | - | ✅ ACTIVE |
| TSK-041 | verify-completeness | - | ✅ ACTIVE |

### PHASE 5 TASKS

| Task ID | Name | Template | Trigger | Status |
|---------|------|----------|---------|--------|
| TSK-050 | phase5-foundation | 5.1 FOUNDATION | Per-source | ✅ ACTIVE |
| TSK-051 | phase5-person-agents | 5.2 PERSON AGENTS | Per-source | ✅ ACTIVE |
| TSK-052 | phase5-cargo-agents | 5.3 CARGO AGENTS | Per-source | ✅ ACTIVE |
| TSK-053 | phase5-theme-dossiers | 5.4 THEME DOSSIERS | Per-source | ✅ ACTIVE |
| TSK-054 | phase5-org-live | 5.5 ORG-LIVE | Cross-source (manual) | ✅ ACTIVE |
| TSK-055 | phase5-final | 5.FINAL CONSOLIDADO | Cross-source (manual) | ✅ ACTIVE |

> **Nota:** TSK-040 (validate-cascade) cobre o sub-template 5.6 VALIDATION — não replicado.

---

## Dependency Graph

```
FOUNDATION
    │
    ├── detect-role ─────────┐
    ├── normalize-entities ──┼── INTELLIGENCE
    └── validate-schema ─────┘       │
                                     ├── analyze-themes ─────┐
                                     ├── detect-business ────┼── EXTRACTION
                                     └── score-viability ────┘       │
                                                                     ├── extract-dna ────┐
                                                                     ├── extract-knowledge┼── PIPELINE
                                                                     └── generate-skill ─┘       │
                                                                                                 ├── process-batch ────┐
                                                                                                 ├── trigger-agent ────┼── VALIDATION
                                                                                                 └── trigger-dossier ──┘       │
                                                                                                                               ├── validate-cascade
                                                                                                                               └── verify-completeness
```

---

## Como Usar

1. Tasks são invocadas por Workflows (`.yaml` em `core/workflows/`)
2. Cada task segue anatomia HO-TP-001 (8 campos obrigatórios)
3. Tasks podem invocar scripts de `core/intelligence/`
4. O JARVIS é o único orquestrador que executa tasks

---

## Adicionando Nova Task

1. Copiar template de `_templates/task-tmpl.md`
2. Preencher os 8 campos obrigatórios
3. Definir inputs/outputs/acceptance criteria
4. Registrar neste arquivo (TASK-REGISTRY.md)
5. Atualizar CHANGELOG.md

---

*Registry v1.0.0 - 2026-02-26*
