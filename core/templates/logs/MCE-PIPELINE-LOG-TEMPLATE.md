# MCE-PIPELINE-LOG-TEMPLATE.md

> **Version:** 1.0.0
> **Date:** 2026-03-11
> **Status:** OFFICIAL -- Source of Truth for MCE Pipeline Logs
> **Replaces:** batch-visual-template.md (for MCE pipeline runs)

---

## USAGE

This is a PROGRESSIVE template. Sections show `[*] PENDENTE` when data is not yet
available and fill in with real data as the pipeline advances. The same template
works at every stage -- from initial classification to full agent generation.

**Status markers:**
- `[*] PENDENTE` -- step not yet executed
- `[~] EM ANDAMENTO` -- step currently running
- `[@] COMPLETO` -- step finished with data below

**When to generate:** After EACH pipeline step completes, regenerate the full log
with updated sections. The log file is overwritten in place (not appended).

**Output paths (dual-location per REGRA #8):**
- `logs/mce/{SLUG}/MCE-{TAG}.md` -- human-readable log
- `.claude/mission-control/mce/{SLUG}/pipeline_state.yaml` -- machine state

---

## TEMPLATE START

````markdown
# MCE PIPELINE LOG -- {TAG}

```
+======================================================================+
|  M C E   P I P E L I N E   L O G                                     |
|                                                                      |
|  Tag:      {TAG}                                                     |
|  Person:   {PERSON_NAME} ({SOURCE_CODE})                             |
|  Status:   {STATUS}                                                  |
|  Started:  {START_TIMESTAMP}                                         |
|  Updated:  {LAST_UPDATE_TIMESTAMP}                                   |
+======================================================================+
```

## META

| Field | Value |
|-------|-------|
| Source file(s) | {source_files} |
| Ingested at | {ingest_timestamp} |
| Primary bucket | {primary_bucket} |
| Classification confidence | {confidence}% |
| Cascade buckets | {cascade_buckets} |
| Workflow mode | {greenfield_or_brownfield} |
| Pipeline status | {CLASSIFIED / CHUNKED / EXTRACTED / MCE_COMPLETE / AGENT_CREATED} |

---

## 1. CLASSIFICATION -- Atlas [@] COMPLETO

```
+----------------------------------------------------------------------+
|  ATLAS -- The Classifier                                             |
+----------------------------------------------------------------------+
```

| # | Signal | Bucket | Score |
|---|--------|--------|-------|
| S1 | Path pattern | {bucket} | +{score} |
| S2 | Participant names | {bucket} | +{score} |
| S3 | Content keywords | {bucket} | +{score} |
| S4 | File metadata | {bucket} | +{score} |
| S5 | Entity match | {bucket} | +{score} |
| S6 | Historical pattern | {bucket} | +{score} |

**Decision:** {primary_bucket} @ {confidence}%
**Cascade:** {cascade_buckets}
**Routing:** {AUTO / TRIAGE / SKIP}

---

## 2. ORGANIZATION -- Atlas [@] COMPLETO

| Field | Value |
|-------|-------|
| Original path | {original_path} |
| Organized to | {destination_path} |
| Entity detected | {entity_slug} |
| Cascade refs | {ref_paths} |
| Batch ID | {batch_id} |
| Files in batch | {file_count} |

---

## 3. CHUNKING -- Sage [*] PENDENTE

```
+----------------------------------------------------------------------+
|  SAGE -- The Extractor                                               |
+----------------------------------------------------------------------+
```

| Metric | Value |
|--------|-------|
| Chunks created | {N} |
| Avg chunk size | {N} words |
| Total tokens | {N} |
| Persons detected | {person_list} |
| Themes detected | {theme_list} |
| Source files processed | {N}/{total} |

---

## 4. ENTITY RESOLUTION -- Sage [*] PENDENTE

| # | Raw Variant | Canonical Form | Confidence |
|---|-------------|----------------|------------|
| 1 | {alias_1} | {canonical_1} | {score}% |
| 2 | {alias_2} | {canonical_2} | {score}% |

**Entities merged with existing CANONICAL-MAP:** {N} new, {N} updated, {N} unchanged

---

## 5. INSIGHT EXTRACTION -- Sage [*] PENDENTE

| # | ID | Insight | DNA Tag | Priority | Chunks |
|---|----|---------|---------|----------|--------|
| 1 | {id} | {text_truncated} | [HEURISTICA] | HIGH | chunk_001, chunk_003 |
| 2 | {id} | {text_truncated} | [FRAMEWORK] | MEDIUM | chunk_007 |

**Totals:** {N} insights ({N} HIGH, {N} MEDIUM, {N} LOW)

### DNA Layer Breakdown

| Layer | Count |
|-------|-------|
| FILOSOFIAS | {N} |
| MODELOS-MENTAIS | {N} |
| HEURISTICAS | {N} |
| FRAMEWORKS | {N} |
| METODOLOGIAS | {N} |
| **Total** | **{N}** |

---

## 6. MCE BEHAVIORAL -- Sage [*] PENDENTE

| # | ID | Pattern | Type | Trigger | Frequency | Chunks |
|---|----|---------|------|---------|-----------|--------|
| 1 | {id} | {pattern} | {decision/reaction/habit/communication} | {trigger} | {freq} | {chunks} |

**Totals:** {N} patterns across {N} categories

---

## 7. MCE IDENTITY -- Sage [*] PENDENTE

### Values Hierarchy

| Rank | Value | Score | Tier |
|------|-------|-------|------|
| 1 | {value} | {N}/10 | Tier 1 (Existential) |
| 2 | {value} | {N}/10 | Tier 1 (Existential) |
| 3 | {value} | {N}/10 | Tier 2 (Operational) |

### Obsessions

| # | Name | Intensity | Status |
|---|------|-----------|--------|
| 1 | {obsession} | {N}/10 | MASTER |
| 2 | {obsession} | {N}/10 | SECONDARY |

### Paradoxes

| # | Tension | Type | Productive? |
|---|---------|------|-------------|
| 1 | {tension_description} | {philosophical/operational} | {YES/NO} |

---

## 8. MCE VOICE -- Sage [*] PENDENTE

### Tone Profile

| Dimension | Score (0-10) |
|-----------|-------------|
| Certainty | {N} |
| Authority | {N} |
| Warmth | {N} |
| Directness | {N} |
| Humor | {N} |
| Formality | {N} |

### Signature Phrases

| # | Phrase | Occurrences | Context |
|---|--------|-------------|---------|
| 1 | "{phrase}" | {N} | {context} |
| 2 | "{phrase}" | {N} | {context} |

### Behavioral States

| # | State | Trigger | Speech Pattern |
|---|-------|---------|----------------|
| 1 | {state} | {trigger} | {pattern} |

### Forbidden Words / Patterns
{list_or_none}

---

## 9. IDENTITY CHECKPOINT -- Lens [*] PENDENTE

```
+----------------------------------------------------------------------+
|  LENS -- The Validator                                               |
+----------------------------------------------------------------------+
```

| Field | Value |
|-------|-------|
| Decision | {APPROVE / REVISE / ABORT} |
| Reviewed by | {human / auto} |
| Timestamp | {ts} |
| Revision notes | {notes_or_none} |

---

## 10. CONSOLIDATION -- Forge [*] PENDENTE

```
+----------------------------------------------------------------------+
|  FORGE -- The Compiler                                               |
+----------------------------------------------------------------------+
```

| # | Artifact | Path | Status |
|---|----------|------|--------|
| 1 | Dossier | {path} | {CREATED / UPDATED / SKIPPED} |
| 2 | Sources | {path} | {CREATED / UPDATED / SKIPPED} |
| 3 | FILOSOFIAS.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 4 | MODELOS-MENTAIS.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 5 | HEURISTICAS.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 6 | FRAMEWORKS.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 7 | METODOLOGIAS.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 8 | BEHAVIORAL-PATTERNS.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 9 | VALUES-HIERARCHY.yaml | {path} | {CREATED / UPDATED / MERGED} |
| 10 | VOICE-DNA.yaml | {path} | {CREATED / UPDATED / MERGED} |

---

## 11. AGENT GENERATION -- Echo [*] PENDENTE

```
+----------------------------------------------------------------------+
|  ECHO -- The Cloner                                                  |
+----------------------------------------------------------------------+
```

| # | File | Path | Status |
|---|------|------|--------|
| 1 | AGENT.md | {path} | {CREATED / UPDATED / THRESHOLD_NOT_MET} |
| 2 | SOUL.md | {path} | {CREATED / UPDATED / THRESHOLD_NOT_MET} |
| 3 | MEMORY.md | {path} | {ENRICHED / THRESHOLD_NOT_MET} |
| 4 | DNA-CONFIG.yaml | {path} | {CREATED / UPDATED / THRESHOLD_NOT_MET} |
| 5 | ACTIVATION.md | {path} | {CREATED / THRESHOLD_NOT_MET} |

**MCE Threshold:** {current}/{required} insights for {person}
**Agent Type:** {external / business / cargo}

---

## 12. VALIDATION -- Lens [*] PENDENTE

```
+----------------------------------------------------------------------+
|  LENS -- Final Validation                                            |
+----------------------------------------------------------------------+
```

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | Chunks have IDs | {PASS / FAIL} | {N}/{N} |
| 2 | Insights have chunk refs | {PASS / FAIL} | {N}/{N} |
| 3 | MCE behavioral has evidence | {PASS / FAIL} | {N}/{N} with 2+ chunks |
| 4 | Values have scores | {PASS / FAIL} | {N}/{N} scored |
| 5 | Voice DNA exists | {PASS / FAIL} | {file_size} |
| 6 | Tone profile defined | {PASS / FAIL} | {N}/6 dimensions |
| 7 | Signature phrases >= 5 | {PASS / FAIL} | {N} phrases |
| 8 | Agent has rastreability | {PASS / FAIL} | {N} ^[FONTE] refs |
| 9 | CANONICAL-MAP consistent | {PASS / FAIL} | {N} entities |
| 10 | Max 1 MASTER obsession | {PASS / FAIL} | {N} masters |

**Score:** {N}/100
**Verdict:** {PASS / FAIL}

---

## PIPELINE DURATION

| # | Phase | Squad | Duration |
|---|-------|-------|----------|
| 1 | Classification | Atlas | {N}s |
| 2 | Organization | Atlas | {N}s |
| 3 | Chunking | Sage | {N}s |
| 4 | Entity Resolution | Sage | {N}s |
| 5 | Insight Extraction | Sage | {N}s |
| 6 | MCE Behavioral | Sage | {N}s |
| 7 | MCE Identity | Sage | {N}s |
| 8 | MCE Voice | Sage | {N}s |
| 9 | Identity Checkpoint | Lens | {N}s |
| 10 | Consolidation | Forge | {N}s |
| 11 | Agent Generation | Echo | {N}s |
| 12 | Validation | Lens | {N}s |
| | **TOTAL** | | **{N}s** |

---

## PIPELINE PROGRESS

```
Classification   [@@@@@@@@@@@] 100%
Organization     [@@@@@@@@@@@] 100%
Chunking         [~~~~~~~~~~~]  IN PROGRESS
Entity Res.      [-----------]  PENDENTE
Insight Ext.     [-----------]  PENDENTE
MCE Behavioral   [-----------]  PENDENTE
MCE Identity     [-----------]  PENDENTE
MCE Voice        [-----------]  PENDENTE
Checkpoint       [-----------]  PENDENTE
Consolidation    [-----------]  PENDENTE
Agent Gen.       [-----------]  PENDENTE
Validation       [-----------]  PENDENTE
```

---

## AUDIT TRAIL

| Log | Path | Entries |
|-----|------|---------|
| scope-classifier | logs/scope-classifier.jsonl | {N} |
| smart-router | logs/smart-router.jsonl | {N} |
| mce-orchestrate | logs/mce-orchestrate.jsonl | {N} |
| batch-auto-creator | logs/batch-auto-creator.jsonl | {N} |

---

*Generated by MCE Pipeline v1.0.0 at {GENERATION_TIMESTAMP}*
*Template: core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md*
````

## TEMPLATE END

---

## RENDERING RULES

### Progressive Fill

When generating this log, follow these rules:

1. **Start from the top.** Sections 1-2 are filled after classification/organization.
2. **Each step fills its section.** After chunking, section 3 changes from PENDENTE to COMPLETO.
3. **Never remove empty sections.** Show them as PENDENTE so the user sees what comes next.
4. **Progress bar updates every step.** The PIPELINE PROGRESS section reflects current state.
5. **Duration accumulates.** Each phase logs wall-clock time. Total is sum of all phases.

### Status Transitions

```
CLASSIFIED     -> Sections 1-2 filled, 3-12 PENDENTE
CHUNKED        -> Sections 1-4 filled, 5-12 PENDENTE
EXTRACTED      -> Sections 1-8 filled, 9-12 PENDENTE
MCE_COMPLETE   -> Sections 1-9 filled, 10-12 PENDENTE
AGENT_CREATED  -> All sections filled
```

### Material Type Adaptations

| Material | Classification Notes | Chunking Notes |
|----------|---------------------|----------------|
| Meeting transcript | S2 (participants) weighted heavily | Speaker-aware chunking |
| Course video | S1 (path) + S3 (keywords) primary | Topic-based chunking |
| PDF / book | S4 (metadata) primary | Chapter/section chunking |
| Podcast | S3 (keywords) primary | Time-segment chunking |

### Backward Compatibility

For legacy pipeline runs (pre-MCE), sections 6-8 (MCE Behavioral, Identity, Voice)
will show PENDENTE permanently. The template still works -- it just shows the
classic 5-layer DNA extraction in section 5 and skips the MCE-specific layers.

---

## INTEGRATION

### Python Usage

```python
# The MCE orchestrator generates this log after each step:
# core/intelligence/pipeline/mce/orchestrate.py

from pathlib import Path

def render_mce_log(slug: str, state: dict) -> str:
    """Render the MCE pipeline log from current state."""
    # Read template, fill variables, write to logs/mce/{slug}/
    ...
```

### Skill Reference

The `/pipeline-mce` skill (`.claude/skills/pipeline-mce/SKILL.md`) generates
this log at Step 12 (REPORT). Earlier steps update the state file which can
be used to regenerate the log at any point.

---

*End of MCE-PIPELINE-LOG-TEMPLATE.md*
