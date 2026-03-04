# Pipeline Auto-Heal

> **Auto-Trigger:** After pipeline processing, when gaps are suspected, or on explicit request
> **Keywords:** "pipeline-heal", "heal", "pipeline gap", "missed step", "auto-heal", "pipeline health", "check pipeline"
> **Prioridade:** ALTA
> **Tools:** Read, Bash, Write, Edit

## Quando NÃO Ativar

- During active pipeline processing (wait until complete)
- For non-pipeline tasks (code changes, agent creation, etc.)
- When user is just asking about pipeline architecture (use docs instead)

---

## What This Skill Does

Detects and heals missed pipeline steps after any source processing. Uses `core/intelligence/pipeline/pipeline_heal.py` as the detection engine.

---

## Step 1: Run Detection

```bash
python3 core/intelligence/pipeline/pipeline_heal.py --check {SOURCE_ID}
```

If SOURCE_ID is unknown, list available sources first:

```bash
python3 core/intelligence/pipeline/pipeline_heal.py --list-sources
```

To check ALL sources at once:

```bash
python3 core/intelligence/pipeline/pipeline_heal.py --check-all
```

Parse the output to identify failed checks (lines with cross mark).

---

## Step 2: Heal Each Failed Check

For each failed check, execute the appropriate heal action:

### P2 — Chunking Missing

Re-run chunking phase. Use `/process-jarvis` Phase 2 for the source.

### P3 — Entity Resolution Missing

Re-run entity extraction. Use `/process-jarvis` Phase 3 for the source.

### P4 — Insights Missing

Re-run insight extraction. Use `/process-jarvis` Phase 4 for the source.

### P5 — Narratives Missing

Re-run narrative synthesis. Use `/process-jarvis` Phase 5 for the source.

### P6.2 — Person Dossier Missing

Compile person dossier from INSIGHTS-STATE and NARRATIVES-STATE.

### P6.3 — Theme Dossiers Missing

Create/update theme dossiers that reference this source's insights.

### P6.6 — Navigation Map Outdated

```bash
python3 core/intelligence/nav_map_builder.py
```

### P7.4 — Agent MEMORY Missing

Read the person's DOSSIER and HIGH insights, then update `agents/minds/{slug}/MEMORY.md`:
1. Read `processing/insights/INSIGHTS-STATE.json` — filter for source_id chunks
2. Extract HIGH confidence insights
3. Append a new section to MEMORY.md with source_id header and insights table

### P8.1.1 — RAG Index Outdated

```bash
python3 core/intelligence/rag/hybrid_index.py --build
```

### P8.1.2 — File Registry Missing Entry

```bash
python3 scripts/file_registry.py --scan
```

If script doesn't exist, manually add entry to `system/REGISTRY/file-registry.json`.

### P8.1.3 — Session State Not Updated

Update `.claude/mission-control/MISSION-STATE.json` with source completion data.

### P8.1.8 — DNA Missing (Density >= 3)

Run DNA extraction:
1. Read the person's DOSSIER (all sections)
2. Read INSIGHTS-STATE filtered for this source
3. Execute `/extract-dna {person-slug}` to create the 5-layer DNA

### P8.1.9 — SOUL Not Updated

1. Read `agents/minds/{slug}/SOUL.md`
2. Read HIGH insights from INSIGHTS-STATE for this source
3. Append an evolution entry:

```markdown
## Evolution: {SOURCE_ID}

**Source:** {source_title}
**Date:** {today}
**Key insights integrated:**
- {insight_1}
- {insight_2}
- ...
```

### P8.3.5 — INBOX Registry Missing

1. Read `system/registry/INBOX-REGISTRY.md`
2. Add entry with source metadata:

```markdown
| {SOURCE_ID} | {source_title} | {speaker} | {chunk_count} chunks | {date} | PROCESSED |
```

---

## Step 3: Re-Run Detection

After healing, re-run detection to confirm all checks pass:

```bash
python3 core/intelligence/pipeline/pipeline_heal.py --check {SOURCE_ID}
```

---

## Step 4: Show Before/After

Display comparison:

```
BEFORE: 11/14 (78%)
AFTER:  14/14 (100%)

HEALED:
  - [P8.1.2] File Registry — entry added
  - [P8.1.9] SOUL Update — evolution entry appended
  - [P8.3.5] INBOX Registry — entry added
```

---

## Examples

**Check specific source:**
```
/pipeline-heal TF001
```

**Check all sources:**
```
/pipeline-heal --all
```

**Check only (no healing):**
```
/pipeline-heal TF001 --check-only
```
