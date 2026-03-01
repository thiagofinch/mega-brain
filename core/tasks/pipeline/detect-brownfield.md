# detect-brownfield

```yaml
---
task: TSK-050
execution_type: Hybrid
responsible: "@jarvis"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Detect Brownfield Scenario |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Hybrid |
| input | source_code, existing_dna_path |
| output | brownfield_status, existing_dna, snapshot_path |
| action_items | 4 steps |
| acceptance_criteria | Brownfield or greenfield determination made with evidence |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| source_code | string | yes | Source identifier (e.g., "CG", "JM", "JH") |
| existing_dna_path | string | yes | Expected path to existing DNA-CONFIG.yaml |
| rollback_enabled | boolean | no | Whether to create pre-update snapshot (default: true) |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| brownfield_confirmed | boolean | return value | true if brownfield criteria met |
| existing_dna | yaml | return value | Parsed existing DNA-CONFIG.yaml contents |
| snapshot_path | string | return value | Path to rollback snapshot directory |
| detection_report | json | artifacts/brownfield/diffs/{source}/ | Detection analysis |
| layer_counts | json | return value | Item count per layer in existing DNA |

---

## Execution

### Phase 1: Existence Verification

**Quality Gate:** QG-BF-001

1. Check if `agents/persons/{source_code}/` directory exists
2. Check if `agents/persons/{source_code}/DNA-CONFIG.yaml` exists
3. Check if `agents/persons/{source_code}/metadata.yaml` exists
4. If ANY check fails, set `brownfield_confirmed = false` and HALT (greenfield path)

### Phase 2: Completeness Validation

**Quality Gate:** QG-BF-002

1. Parse DNA-CONFIG.yaml and validate YAML structure
2. Verify all 5 layers present and non-empty:
   - L1_PHILOSOPHIES: minimum 1 item
   - L2_MENTAL_MODELS: minimum 1 item
   - L3_HEURISTICS: minimum 1 item
   - L4_FRAMEWORKS: minimum 1 item
   - L5_METHODOLOGIES: minimum 1 item
3. Read metadata.yaml and verify `pipeline_status == "completed"`
4. Record `layer_counts` for each layer (used by diff-analysis)

### Phase 3: Snapshot Creation

**Quality Gate:** QG-BF-003

1. If `rollback_enabled == true`:
   a. Create directory `artifacts/brownfield/snapshots/{source_code}/`
   b. Copy DNA-CONFIG.yaml, SOUL.md, MEMORY.md, AGENT.md, metadata.yaml
   c. Generate SNAPSHOT-MANIFEST.json with:
      - Timestamp
      - SHA256 hashes of each file
      - Layer counts
      - Snapshot ID format: `SNAP-{SOURCE_CODE}-{YYYYMMDD-HHmm}`
2. Record `snapshot_path` in output

### Phase 4: Detection Report

**Quality Gate:** QG-BF-004

1. Generate detection report JSON:
   ```json
   {
     "source_code": "CG",
     "brownfield_confirmed": true,
     "detection_timestamp": "2026-02-28T14:00:00Z",
     "existing_clone": {
       "dna_path": "agents/persons/cole-gordon/DNA-CONFIG.yaml",
       "layer_counts": {"L1": 12, "L2": 8, "L3": 22, "L4": 15, "L5": 9},
       "total_items": 66,
       "pipeline_status": "completed",
       "last_updated": "2026-01-15T10:00:00Z"
     },
     "snapshot": {
       "created": true,
       "path": "artifacts/brownfield/snapshots/CG/",
       "manifest": "SNAP-CG-20260228-1400"
     }
   }
   ```
2. Save to `artifacts/brownfield/diffs/{source_code}/detection-report.json`
3. Set `brownfield_confirmed = true`

---

## Acceptance Criteria

- [ ] Directory existence checked for agent source
- [ ] DNA-CONFIG.yaml parsed and validated (all 5 layers non-empty)
- [ ] metadata.yaml pipeline_status verified as "completed"
- [ ] Snapshot created with manifest (if rollback_enabled)
- [ ] Detection report generated with layer counts
- [ ] Clear boolean output: brownfield_confirmed = true/false

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| diff-analysis | brownfield_confirmed == true | existing_dna, layer_counts, snapshot_path |
| wf-pipeline-full | brownfield_confirmed == false | source_code, new_files (redirect to greenfield) |

---

## Decision Tree Summary

```
detect-brownfield
       │
       ├── Directory exists? ─── NO ──→ GREENFIELD (halt)
       │         │
       │        YES
       │         │
       ├── DNA valid + 5 layers? ── NO ──→ GREENFIELD (halt)
       │         │
       │        YES
       │         │
       ├── pipeline_status == completed? ── NO ──→ GREENFIELD (halt)
       │         │
       │        YES
       │         │
       ├── Create snapshot (if enabled)
       │         │
       └── Output: brownfield_confirmed = true ──→ diff-analysis
```

---

## Notes

- This task is the GATEWAY for brownfield mode. If it outputs `false`, the entire
  brownfield workflow is skipped and wf-pipeline-full takes over.
- Snapshot creation adds ~2% overhead but enables safe rollback.
- Layer counts from this phase are critical input for diff-analysis to calculate
  the delta accurately.

---

**Task Version:** 1.0.0
