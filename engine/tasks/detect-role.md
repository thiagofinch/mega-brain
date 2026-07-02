# detect-role

```yaml
---
task: TSK-001
execution_type: Worker
responsible: "script"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Detect Role from Content |
| status | active |
| responsible_executor | role_detector.py |
| execution_type | Worker |
| input | text content, patterns config |
| output | detected roles, confidence scores |
| action_items | 3 steps |
| acceptance_criteria | Role detected with >70% confidence |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | yes | Text to analyze for roles |
| patterns_path | string | no | Path to role patterns YAML |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| roles | json | return value | Detected roles with scores |
| primary_role | string | return value | Highest confidence role |

---

## Execution

### Phase 1: Pattern Matching

**Quality Gate:** QG-ROLE-001

1. Load role patterns from `core/patterns/_ROLE_PATTERNS.yaml`
2. Tokenize and normalize input text
3. Match patterns against content
4. Calculate confidence scores per role

---

## Acceptance Criteria

- [ ] At least one role detected
- [ ] Confidence score >= 0.70 for primary role
- [ ] Valid JSON output format

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| analyze-themes | role_detected | primary_role, content |
| trigger-agent | high_confidence | roles array |

---

## Scripts de Suporte

| Script | Location | Invoked When |
|--------|----------|--------------|
| role_detector.py | core/intelligence/ | Always |

---

**Task Version:** 1.0.0
