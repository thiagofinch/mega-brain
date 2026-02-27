# process-batch

```yaml
---
task: TSK-030
execution_type: Agent
responsible: "@jarvis"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Process Content Batch |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | batch files, source config |
| output | BATCH-XXX.md, insights, cascading |
| action_items | 6 steps |
| acceptance_criteria | Batch log complete with cascading |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| batch_id | string | yes | Batch identifier (e.g., "BATCH-050") |
| source_code | string | yes | Source code (e.g., "CG", "JM") |
| files | array | yes | Files to process in batch |
| template | string | no | Batch template version |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| batch_log | md | logs/batches/BATCH-XXX.md | Full batch log |
| insights | json | artifacts/insights/ | Extracted insights |
| cascading | json | logs/cascading.jsonl | Cascading record |

---

## Execution

### Phase 1: Batch Setup

**Quality Gate:** QG-BATCH-001

1. Verify all input files exist
2. Load batch template from `core/templates/`
3. Initialize batch log with header

### Phase 2: Content Processing

**Quality Gate:** QG-BATCH-002

1. Execute chunking (PROMPT-1.1)
2. Execute entity resolution (PROMPT-1.2)
3. Execute insight extraction (PROMPT-2.1)
4. Execute narrative synthesis (PROMPT-3.1)

### Phase 3: Log Generation

**Quality Gate:** QG-BATCH-003

1. Generate full batch log (14 sections)
2. Display log in chat (RULE #9)
3. Save to dual locations (RULE #8)

### Phase 4: Cascading

**Quality Gate:** QG-BATCH-004

1. Read "DESTINO DO CONHECIMENTO" section
2. Execute cascading to all destinations
3. Add "Cascateamento Executado" section
4. Validate cascading integrity

---

## Acceptance Criteria

- [ ] All 14 batch sections present
- [ ] Log displayed in chat (not just saved)
- [ ] Dual-location logging complete
- [ ] Cascading validated (all destinations exist)
- [ ] "Cascateamento Executado" section added

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| validate-cascade | batch_complete | batch_id, destinations |
| trigger-agent | new_insights | insights array |
| trigger-dossier | theme_updated | theme details |

---

## Protocol Reference

See `core/templates/pipeline/PIPELINE-JARVIS-v2.1.md` for detailed workflow.

---

**Task Version:** 1.0.0
