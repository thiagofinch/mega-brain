# TASK CHANGELOG

> **Padrão:** Pedro (aios-core)
> **Propósito:** Auditoria de mudanças em tasks

---

## [1.0.0] - 2026-02-26

### Added
- Criação inicial do sistema de tasks
- Template HO-TP-001 em `_templates/task-tmpl.md`
- TASK-REGISTRY.md com categorias e dependency graph
- Foundation tasks: detect-role, normalize-entities
- Intelligence tasks: analyze-themes, detect-business-model, score-viability
- Extraction tasks: extract-dna, extract-knowledge, generate-skill
- Pipeline tasks: process-batch, trigger-agent, trigger-dossier
- Validation tasks: validate-cascade, verify-completeness

### Structure
```
core/tasks/
├── _templates/
│   └── task-tmpl.md
├── TASK-REGISTRY.md
├── CHANGELOG.md
├── detect-role.md
├── normalize-entities.md
├── analyze-themes.md
├── extract-dna.md
├── process-batch.md
└── validate-cascade.md
```

---

## Convenções

### Formato de Versão
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes na anatomia de tasks
- MINOR: Novas tasks adicionadas
- PATCH: Fixes em tasks existentes

### Tipos de Mudança
- **Added**: Nova task criada
- **Changed**: Task modificada (inputs/outputs/logic)
- **Deprecated**: Task marcada para remoção
- **Removed**: Task removida
- **Fixed**: Bug fix em task
- **Security**: Vulnerabilidade corrigida

---

*Changelog v1.0.0*
