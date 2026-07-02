# validate-cascade

```yaml
---
task: TSK-040
execution_type: Worker
responsible: "script"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Validate Cascading Integrity |
| status | active |
| responsible_executor | validate_cascading_integrity.py |
| execution_type | Worker |
| input | batch_id, destinations list |
| output | validation result, gap report |
| action_items | 4 steps |
| acceptance_criteria | All destinations exist and reference batch |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| batch_id | string | yes | Batch to validate |
| destinations | array | no | Override destinations list |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| status | enum | return value | PASSED/WARNING/FAILED |
| gaps | array | return value | Missing destinations |
| report | json | logs/cascading-verified.jsonl | Validation record |

---

## Execution

### Phase 1: Destination Extraction

**Quality Gate:** QG-VAL-001

1. Read batch file
2. Extract "DESTINO DO CONHECIMENTO" section
3. Parse destination list

### Phase 2: Existence Check

**Quality Gate:** QG-VAL-002

1. For each destination, verify file exists
2. Log missing files as gaps

### Phase 3: Reference Check

**Quality Gate:** QG-VAL-003

1. For each existing destination, check for batch_id reference
2. Log missing references as warnings

### Phase 4: Status Determination

**Quality Gate:** QG-VAL-004

1. If gaps exist → FAILED
2. If warnings exist → WARNING
3. Otherwise → PASSED

---

## Acceptance Criteria

- [ ] All destinations checked
- [ ] Status determined (PASSED/WARNING/FAILED)
- [ ] Report logged to cascading-verified.jsonl
- [ ] If FAILED, gap list provided

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| verify-completeness | validation_passed | batch_id |
| process-batch | validation_failed | gaps to fix |

---

## Scripts de Suporte

| Script | Location | Invoked When |
|--------|----------|--------------|
| validate_cascading_integrity.py | scripts/ | Always |

---

**Task Version:** 1.0.0
