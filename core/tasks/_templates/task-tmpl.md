# TASK TEMPLATE (HO-TP-001)

> **Versão:** 1.0.0
> **Padrão:** Pedro (aios-core/squad-creator)
> **Uso:** Template para criar novos tasks atômicos

---

## TASK ANATOMY (8 Campos Obrigatórios)

```yaml
---
task: [TASK-ID]
execution_type: Agent | Human | Hybrid | Worker
responsible: "@jarvis" | "@human" | "script"
---
```

---

# [Task Name]

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | [Verbo + Objeto] |
| status | pending |
| responsible_executor | [@jarvis/@human/script] |
| execution_type | [Agent/Human/Hybrid/Worker] |
| input | [Lista de inputs] |
| output | [Lista de outputs] |
| action_items | [N steps] |
| acceptance_criteria | [Critérios de conclusão] |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| input_1 | string/file/json | yes/no | [Descrição] |
| input_2 | ... | ... | ... |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| output_1 | file/json/update | [path] | [Descrição] |
| output_2 | ... | ... | ... |

---

## Execution

### Phase 1: [Nome]

**Quality Gate:** [QG-ID]

1. [Step 1]
2. [Step 2]
3. [Step 3]

### Phase 2: [Nome] (se necessário)

**Quality Gate:** [QG-ID]

1. [Step 1]
2. [Step 2]

---

## Acceptance Criteria

- [ ] [Critério 1 - mensurável]
- [ ] [Critério 2 - mensurável]
- [ ] [Critério 3 - mensurável]

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| [task-id] | [condition] | [what data] |

---

## Scripts de Suporte (opcional)

| Script | Location | Invoked When |
|--------|----------|--------------|
| [script.py] | core/intelligence/ | [condition] |

---

## Notes

[Notas adicionais, edge cases, considerações]

---

**Template Version:** 1.0.0 (HO-TP-001)
