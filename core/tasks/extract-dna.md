# extract-dna

```yaml
---
task: TSK-020
execution_type: Agent
responsible: "@jarvis"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Extract Cognitive DNA |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | insights, themes, source content |
| output | DNA-CONFIG.yaml (5 layers) |
| action_items | 5 steps |
| acceptance_criteria | All 5 DNA layers populated |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| insights | json | yes | Extracted insights from content |
| themes | array | yes | Theme classifications |
| source_id | string | yes | Source identifier (e.g., "CG", "JM") |
| chunks | array | yes | Content chunks for reference |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| dna_config | yaml | agents/persons/{name}/DNA-CONFIG.yaml | 5-layer DNA structure |
| layer_counts | json | return value | Count per layer |

---

## Execution

### Phase 1: Philosophy Extraction (L1)

**Quality Gate:** QG-DNA-001

1. Identify core beliefs and worldview statements
2. Extract value system indicators
3. Map to PHILOSOPHIES layer

### Phase 2: Mental Models (L2)

**Quality Gate:** QG-DNA-002

1. Identify thinking frameworks
2. Extract decision-making patterns
3. Map to MENTAL-MODELS layer

### Phase 3: Heuristics (L3)

**Quality Gate:** QG-DNA-003

1. Extract practical rules
2. Identify decision shortcuts
3. Map to HEURISTICS layer

### Phase 4: Frameworks (L4)

**Quality Gate:** QG-DNA-004

1. Identify structured methodologies
2. Extract process definitions
3. Map to FRAMEWORKS layer

### Phase 5: Methodologies (L5)

**Quality Gate:** QG-DNA-005

1. Extract step-by-step implementations
2. Identify tactical procedures
3. Map to METHODOLOGIES layer

---

## Acceptance Criteria

- [ ] All 5 DNA layers populated
- [ ] Minimum 3 items per layer
- [ ] Source citations for each item (^[chunk_id])
- [ ] Valid YAML structure

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| trigger-agent | dna_complete | DNA-CONFIG path |
| validate-cascade | extraction_done | layer_counts |

---

## Protocol Reference

See `core/templates/agents/dna-extraction.md` for detailed instructions.

---

**Task Version:** 1.0.0
