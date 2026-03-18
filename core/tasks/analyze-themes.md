# analyze-themes

```yaml
---
task: TSK-010
execution_type: Worker
responsible: "script"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Analyze Thematic Content |
| status | active |
| responsible_executor | theme_analyzer.py |
| execution_type | Worker |
| input | normalized content, entities |
| output | theme classifications, topic clusters |
| action_items | 4 steps |
| acceptance_criteria | Themes identified with hierarchy |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | yes | Normalized text |
| entities | json | yes | Entity map from normalize-entities |
| role | string | no | Primary role from detect-role |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| themes | array | return value | Identified themes |
| hierarchy | json | return value | Theme parent-child relationships |
| topic_clusters | array | return value | Related topic groupings |

---

## Execution

### Phase 1: Theme Identification

**Quality Gate:** QG-THEME-001

1. Load domain glossaries from `core/glossary/`
2. Extract key topics from content
3. Map topics to theme taxonomy
4. Build theme hierarchy

---

## Acceptance Criteria

- [ ] At least one theme identified
- [ ] Themes mapped to known taxonomy
- [ ] Hierarchy depth >= 1

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| extract-dna | themes_identified | themes, hierarchy |
| trigger-dossier | new_theme | theme details |

---

## Scripts de Suporte

| Script | Location | Invoked When |
|--------|----------|--------------|
| theme_analyzer.py | core/intelligence/ | Always |

---

**Task Version:** 1.0.0
