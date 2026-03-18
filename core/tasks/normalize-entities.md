# normalize-entities

```yaml
---
task: TSK-002
execution_type: Worker
responsible: "script"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Normalize Named Entities |
| status | active |
| responsible_executor | entity_normalizer.py |
| execution_type | Worker |
| input | raw text, entity types |
| output | normalized entities map |
| action_items | 4 steps |
| acceptance_criteria | Entities normalized with canonical forms |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | yes | Text containing entities |
| entity_types | array | no | Types to extract (PERSON, ORG, etc) |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| entities | json | return value | Normalized entity map |
| canonical_forms | json | return value | Canonical name mappings |

---

## Execution

### Phase 1: Entity Extraction

**Quality Gate:** QG-ENT-001

1. Identify named entities in text
2. Group variations (e.g., "Cole Gordon", "Cole", "Gordon")
3. Select canonical form for each entity
4. Build normalization map

---

## Acceptance Criteria

- [ ] All entity variations grouped
- [ ] Canonical form selected per entity
- [ ] No duplicate entries in output

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| analyze-themes | entities_normalized | canonical_forms |
| extract-knowledge | complete | entities map |

---

## Scripts de Suporte

| Script | Location | Invoked When |
|--------|----------|--------------|
| entity_normalizer.py | core/intelligence/ | Always |

---

**Task Version:** 1.0.0
