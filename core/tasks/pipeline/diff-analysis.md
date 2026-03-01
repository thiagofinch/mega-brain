# diff-analysis

```yaml
---
task: TSK-051
execution_type: Agent
responsible: "@jarvis"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Diff Analysis: New vs Existing DNA |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | new_themes, existing_dna, new_files, source_code |
| output | diff_report, affected_layers, contradictions |
| action_items | 5 steps |
| acceptance_criteria | Every new item classified as ADDITION, REINFORCEMENT, CONTRADICTION, or REDUNDANT |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| new_themes | json | yes | Theme analysis output from analyze-themes on new files |
| existing_dna | yaml | yes | Parsed existing DNA-CONFIG.yaml (all 5 layers) |
| new_files | array | yes | List of new source files to integrate |
| source_code | string | yes | Source identifier (e.g., "CG") |
| layer_counts | json | yes | Item count per layer from detect-brownfield |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| diff_report | json | artifacts/brownfield/diffs/{source}/ | Full diff with classifications |
| affected_layers | array | return value | List of layers needing re-extraction (e.g., ["L3", "L4"]) |
| contradictions | array | return value | Items flagging conflicts with existing DNA |
| additions_count | integer | return value | Number of new items to add |
| reinforcements_count | integer | return value | Number of existing items reinforced |

---

## Execution

### Phase 1: Content Extraction from New Sources

**Quality Gate:** QG-DIFF-001

1. For each file in `new_files`, extract candidate DNA items:
   - L1 candidates: Belief statements, worldview declarations, value assertions
   - L2 candidates: Thinking patterns, decision frameworks, mental models
   - L3 candidates: Rules of thumb, numerical thresholds, heuristic shortcuts
   - L4 candidates: Structured processes, named frameworks, multi-step methods
   - L5 candidates: Step-by-step implementations, tactical procedures
2. Tag each candidate with source file and location (^[FONTE:file:line])
3. Produce `candidate_items[]` with layer assignment and source citation

### Phase 2: Semantic Comparison

**Quality Gate:** QG-DIFF-002

1. For each `candidate_item`, compare against every item in `existing_dna` within the same layer
2. Compute semantic similarity (threshold: 0.85 for duplicate detection)
3. Classify each candidate:

| Similarity Score | Classification | Action |
|-----------------|----------------|--------|
| >= 0.85 | REDUNDANT (~) | Skip, log as already captured |
| 0.60 - 0.84 | REINFORCEMENT (=) | Existing item gets confidence boost |
| < 0.60 | ADDITION (+) | New item for the layer |
| Any + logical conflict | CONTRADICTION (!) | Flag for human review |

4. For CONTRADICTION detection specifically:
   - Check if candidate negates an existing item (opposite assertion)
   - Check if candidate provides a conflicting number/threshold
   - Check if candidate contradicts a core philosophy (L1 critical)

### Phase 3: Layer Impact Assessment

**Quality Gate:** QG-DIFF-003

1. Aggregate classifications by layer:
   ```
   L1: 0 additions, 2 reinforcements, 0 contradictions, 1 redundant
   L2: 0 additions, 0 reinforcements, 0 contradictions, 0 redundant
   L3: 5 additions, 3 reinforcements, 1 contradiction, 2 redundant
   L4: 2 additions, 1 reinforcement, 0 contradictions, 0 redundant
   L5: 0 additions, 0 reinforcements, 0 contradictions, 0 redundant
   ```
2. Determine `affected_layers`: any layer with ADDITIONS or CONTRADICTIONS
3. Apply Layer Impact Matrix from brownfield-detection protocol:
   - If L1 affected: flag as HIGH IMPACT (core identity may shift)
   - If only L3-L5 affected: flag as LOW IMPACT (additive knowledge)

### Phase 4: Contradiction Deep Analysis

**Quality Gate:** QG-DIFF-004

1. For each CONTRADICTION found:
   a. Extract existing item text and source citation
   b. Extract conflicting new item text and source citation
   c. Determine contradiction type:
      - **TEMPORAL**: Speaker changed their mind over time (newer may supersede)
      - **CONTEXTUAL**: Different advice for different contexts (both valid)
      - **FUNDAMENTAL**: Core disagreement (requires human decision)
   d. Generate recommendation but do NOT auto-resolve
2. If ANY L1 contradiction exists: set `l1_contradiction_flag = true`

### Phase 5: Diff Report Generation

**Quality Gate:** QG-DIFF-005

1. Generate comprehensive diff report:
   ```json
   {
     "source_code": "CG",
     "analysis_timestamp": "2026-02-28T14:30:00Z",
     "new_files_analyzed": 3,
     "summary": {
       "total_candidates": 18,
       "additions": 7,
       "reinforcements": 6,
       "contradictions": 1,
       "redundant": 4
     },
     "affected_layers": ["L3", "L4"],
     "impact_level": "LOW",
     "l1_contradiction_flag": false,
     "layer_detail": {
       "L1": { "additions": 0, "reinforcements": 2, "contradictions": 0, "redundant": 1 },
       "L2": { "additions": 0, "reinforcements": 0, "contradictions": 0, "redundant": 0 },
       "L3": { "additions": 5, "reinforcements": 3, "contradictions": 1, "redundant": 2 },
       "L4": { "additions": 2, "reinforcements": 1, "contradictions": 0, "redundant": 0 },
       "L5": { "additions": 0, "reinforcements": 0, "contradictions": 0, "redundant": 1 }
     },
     "items": [
       {
         "id": "DIFF-001",
         "layer": "L3",
         "classification": "ADDITION",
         "content": "Follow up within 5 minutes of lead submission",
         "source": "^[new-training-video.txt:line-245]",
         "similar_existing": null,
         "similarity_score": 0.12
       },
       {
         "id": "DIFF-002",
         "layer": "L3",
         "classification": "CONTRADICTION",
         "content": "Commission should be 15% flat rate",
         "source": "^[new-training-video.txt:line-890]",
         "similar_existing": {
           "id": "HEUR-CG-025",
           "content": "Commission between 8-12% of value",
           "source": "^[original-training.txt:line-340]"
         },
         "similarity_score": 0.72,
         "contradiction_type": "TEMPORAL",
         "recommendation": "Newer source may supersede; flag for human review"
       }
     ],
     "estimated_savings": {
       "layers_skipped": 3,
       "token_savings_pct": 65,
       "time_savings_pct": 60
     }
   }
   ```
2. Save to `artifacts/brownfield/diffs/{source_code}/diff-report-{YYYYMMDD}.json`

---

## Acceptance Criteria

- [ ] All new source files analyzed for candidate DNA items
- [ ] Every candidate classified as ADDITION, REINFORCEMENT, CONTRADICTION, or REDUNDANT
- [ ] Affected layers list determined (only layers with additions/contradictions)
- [ ] Contradictions analyzed with type (TEMPORAL/CONTEXTUAL/FUNDAMENTAL)
- [ ] No contradictions auto-resolved (all flagged for human review)
- [ ] Diff report generated with per-layer breakdown
- [ ] Estimated savings calculated

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| extract-dna (selective) | diff_complete | affected_layers, candidate items per layer |
| notify-user | contradictions_found | contradiction details for review |

---

## Notes

- Semantic similarity uses cosine similarity on embeddings when available (VOYAGE_API_KEY),
  falls back to keyword overlap ratio when embeddings unavailable.
- The 0.85 threshold for REDUNDANT classification is deliberately high to avoid
  false deduplication. It is better to add a near-duplicate than to miss genuinely
  new knowledge.
- CONTRADICTION classification is the most critical output. False negatives here
  (missing a real contradiction) can corrupt clone fidelity. When in doubt, classify
  as CONTRADICTION rather than REINFORCEMENT.
- This task does NOT modify any files. It is purely analytical. Modifications happen
  in the MERGE phase of wf-brownfield-update.

---

**Task Version:** 1.0.0
