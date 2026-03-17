# MCE Pipeline -- Imperative Execution Guide

> **Auto-Trigger:** Processamento MCE, pipeline cognitivo, extraction pipeline
> **Keywords:** "pipeline-mce", "mce", "pipeline cognitivo", "process-jarvis", "processar fonte", "extrair DNA", "cognitive extraction", "voice dna", "behavioral patterns"
> **Prioridade:** ALTA
> **Tools:** Read, Write, Edit, Bash, Glob, Grep

## Quando NAO Ativar

- RAG queries (use `/graph-search` or `/memory-search`)
- Manual document creation
- Conclave sessions (use `/conclave`)
- Source sync (use `/source-sync`)

---

## WHAT THIS SKILL DOES

Transforms raw transcripts into 9+ DNA layers, Voice DNA, behavioral patterns, identity
layers, dossiers, and fully-generated mind-clone agents. Combines a deterministic Python
orchestrator (`orchestrate.py`) for file ops with LLM prompt execution for extraction.

## EXECUTION: 12 STEPS

Every run follows these 12 steps in order. Do NOT skip steps. Do NOT ask permission
between steps unless the step says PAUSE.

### MANDATORY RULES (apply to ALL steps)

**RULE 1 — ALWAYS use Write tool for artifact saves.**
Steps 3-10 MUST save all artifact files (JSON, YAML, MD) using the **Write** tool,
NEVER via Bash with `python3 -c` or shell redirection. This ensures the PostToolUse
hook (`mce_step_logger.py`) fires and records JSONL audit entries + metrics.
Exception: Read-only Bash commands (status checks, validations) are fine.

**RULE 2 — Display Raio-X panel after each step.**
After completing each step (3-10), display an inline status panel to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP {N} — {STEP_NAME}                    `●` DONE
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────
  {2-4 lines of key metrics for this step}
  ──────────────────────────────────────────────────
  Progress: [{bar}] {N}/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Do NOT rely on hook feedback for display — hooks are invisible to the user.
The skill itself must print status after each step completes.

**RULE 3 — QA GATE after every step (MANDATORY).**
After completing each step (1-11), run the automated QA gate BEFORE proceeding.
This is NON-NEGOTIABLE. The QA gate verifies that the step actually produced
what it claims. Without QA, code gets written but never wired (see: gotchas-memory.js
incident — Epic 9 was coded but never activated because no QA validated the hook).

**Primary method (automated):**
Run this command after each step N completes:
```bash
python3 -c "
import json
from core.intelligence.pipeline.mce.qa_gates import validate_step
result = validate_step({N}, '{SLUG}')
print(json.dumps(result, indent=2, default=str))
"
```

Replace `{N}` with the step number (1-11) and `{SLUG}` with the person slug
(e.g., `alex-hormozi`). These are the same variables used throughout SKILL.md steps.

Parse the JSON output:
- If `"passed": true` — proceed to next step
- If `"passed": false` — check `"blocking_failures"` list
  - Fix each blocking failure before proceeding
  - If fix fails 3 times — SURFACE to user with error details
  - Do NOT proceed to step N+1 until gate passes

**Fallback method (if qa_gates.py not installed):**
If the automated gate fails with ImportError or ModuleNotFoundError, use this manual
checklist instead:

| Step | QA Validates |
|------|-------------|
| 1 INGEST | File moved to correct bucket? Output JSON has `success: true`? |
| 2 BATCH | Batches created > 0? Files above threshold? |
| 3 CHUNK | CHUNKS-STATE.json exists? chunks[] non-empty? All chunk_ids unique? |
| 4 ENTITY | CANONICAL-MAP.json updated? Source person has entry? |
| 5 INSIGHT | INSIGHTS-STATE.json has person entry? insights[] non-empty? Each has chunks[]? |
| 6 BEHAVIORAL | behavioral_patterns field exists? Each pattern has 2+ chunk_ids? |
| 7 IDENTITY | value_hierarchy has Tier 1? Exactly 1 MASTER obsession? |
| 8 VOICE | VOICE-DNA.yaml exists? Has signature_phrases + behavioral_states + dimensions? |
| 9 CHECKPOINT | User explicitly typed APPROVE/1? |
| 10 CONSOLIDATE | ALL 6 sub-steps ran? Dossier exists? 5/5 DNA YAMLs? Agent files? Cross-ref PASS? |
| 11 FINALIZE | enrichment.appended > 0? State is complete? Log file written? |

**QA Gate display format (show after each step's Raio-X panel):**

```
  QA GATE — STEP {N}                    [AUTOMATED]
  [pass] {check_1_name}: {detail}
  [pass] {check_2_name}: {detail}
  [FAIL] {check_3_name}: {detail} <-- BLOCKS PIPELINE
  Result: PASS ({passed}/{total}) | FAIL ({passed}/{total} — fix before proceeding)
```

When using the fallback manual checklist, replace `[AUTOMATED]` with `[MANUAL]`
in the display format above.

**RULE 4 — Chronicler Log accumulates progressively.**
After each step's QA Gate passes, append the step's metrics to the session log file
at `logs/mce/{SLUG}/MCE-{TAG}-SESSION-{DATE}.md` using Chronicler Design System
(120 chars, nested boxes). The log grows incrementally — each step ADDS a section,
never rewrites previous sections. Use **Write tool with append** or **Edit tool**.

This ensures that even if the pipeline crashes mid-run, all completed steps
have their visual log preserved.

### STEP 0: DETECT INPUT

Read the user's message to determine:
- **File mode:** User gave a file path. Set `FILE_PATH` to that path.
- **Slug mode:** User gave a person code or slug (e.g. `AH`, `alex-hormozi`). Set `SLUG`.
- **Resume mode:** State file exists for the slug. Resume from first incomplete step.

If unclear, ask: "Which source file or person slug should I process?"

Then check for existing state:

```bash
python3 -m core.intelligence.pipeline.mce.orchestrate status {SLUG}
```

Parse the JSON output. If `state_machine.current_state` is not `init` and not `complete`,
RESUME from the step matching the current state.

---

### STEP 1: INGEST (Deterministic)

**Trigger:** User provides a file path.
**Skip if:** File already ingested (check status output).

Run:
```bash
python3 -m core.intelligence.pipeline.mce.orchestrate ingest "{FILE_PATH}"
```

Parse the JSON output. Extract:
- `slug` -- the detected person slug
- `classification.primary_bucket` -- which bucket the file landed in
- `workflow.mode` -- greenfield or brownfield
- `routing.moved_to` -- where the file was moved

If `success` is false, STOP and report the error to the user.

Set `SLUG` from the output. Set `SOURCE_CODE` from slug (first 2 chars uppercase).

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 1 -- INGEST                                      [OK]
  Slug: {SLUG} | Bucket: {PRIMARY_BUCKET}
  ──────────────────────────────────────────────────────────
  primary_bucket: {BUCKET}
  confidence: {CONFIDENCE}%
  workflow: {MODE}
  routed_to: {MOVED_TO}
  ──────────────────────────────────────────────────────────
  Progress: [==>                      ] 1/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 2: BATCH (Deterministic)

**Trigger:** After ingest, or when user provides a slug directly.

Run:
```bash
python3 -m core.intelligence.pipeline.mce.orchestrate batch {SLUG}
```

Parse the JSON output. Extract:
- `batches_for_slug` -- list of batch objects created for this slug
- `state.current` -- should now be `chunking`

If no batches were created and `files_below_threshold` > 0, report:
"Not enough files to create a batch. Minimum is 3 files. Add more source
files to `knowledge/external/inbox/{SLUG}/` and retry."

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 2 -- BATCH                                       [OK]
  Slug: {SLUG}
  ──────────────────────────────────────────────────────────
  batches_created: {N}
  files_scanned: {N}
  state: {STATE}
  ──────────────────────────────────────────────────────────
  Progress: [====>                    ] 2/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 3: CHUNK (LLM)

**What:** Semantic chunking of source material.
**State transition:** `chunking` phase active.

1. Read the prompt template:
   ```
   Read: core/templates/phases/prompt-1.1-chunking.md
   ```

2. Read all source files for this slug from the organized inbox:
   ```
   Glob: knowledge/external/inbox/{SLUG}/**/*.txt
   Glob: knowledge/external/inbox/{SLUG}/**/*.md
   Glob: knowledge/external/inbox/{SLUG}/**/*.docx
   ```

3. Execute the chunking prompt against each source file. Follow the prompt
   instructions EXACTLY -- it specifies output format, chunk structure, and
   validation checkpoints.

4. Save output to:
   ```
   artifacts/chunks/CHUNKS-STATE.json
   ```

5. Validate: CHUNKS-STATE.json exists and has `chunks` array with >= 1 entry.

If processing large files (> 30,000 chars), process in batches of 3 files max.
Save CHUNKS-STATE.json incrementally after each batch.

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 3 -- CHUNK                                       [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Chunks created:    {CHUNK_COUNT}
  Persons detected:  {PERSON_LIST}
  Files processed:   {FILE_COUNT}
  ──────────────────────────────────────────────────────────
  Progress: [======>                  ] 3/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 4: ENTITY RESOLUTION (LLM)

**What:** Resolve entity name variants to canonical forms.
**Depends on:** CHUNKS-STATE.json from Step 3.

**CRITICAL: CANONICAL-MAP.json is PERSISTENT across all pipeline runs.**

1. Read the prompt template:
   ```
   Read: core/templates/phases/prompt-1.2-entity-resolution.md
   ```

2. Read CHUNKS-STATE.json.

3. **ALWAYS read existing `artifacts/canonical/CANONICAL-MAP.json` first.**
   If it exists, load the existing entity map. New entities discovered in this
   run MUST be MERGED with existing ones. Never overwrite or reset the file.
   If a new variant maps to an already-known canonical form, add the variant
   to that canonical entry. If a truly new entity is found, add a new entry.

4. Execute entity resolution following the prompt instructions.

5. Save MERGED output using the **Write** tool to:
   ```
   artifacts/canonical/CANONICAL-MAP.json
   ```
   (NEVER use Bash/python3 to write this file — Write tool triggers logging hook.)

6. Validate: CANONICAL-MAP.json exists and has entities mapped.

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 4 -- ENTITY RESOLUTION                           [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Entities resolved:  {ENTITY_COUNT}
  New variants:       {NEW_VARIANT_COUNT}
  Merged with existing: {MERGED_COUNT}
  ──────────────────────────────────────────────────────────
  Progress: [========>                ] 4/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 5: INSIGHT EXTRACTION (LLM)

**What:** Extract actionable insights from chunks.
**Depends on:** CHUNKS-STATE.json + CANONICAL-MAP.json.

**CRITICAL: INSIGHTS-STATE.json is a SINGLE incremental file.**
ALWAYS read the existing `artifacts/insights/INSIGHTS-STATE.json` first.
APPEND new insights to the existing data. NEVER create per-meeting or
per-batch separate files (e.g., INSIGHTS-STATE-MEET0040.json is WRONG).
One file grows over time across all pipeline runs.

1. Read the prompt templates:
   ```
   Read: core/templates/phases/prompt-2.1-insight-extraction.md
   Read: core/templates/phases/prompt-2.1-dna-tags.md
   ```

2. Read CHUNKS-STATE.json and CANONICAL-MAP.json.

3. **Read existing `artifacts/insights/INSIGHTS-STATE.json`** if it exists.
   Load the existing persons and insights arrays.

4. Execute insight extraction following the prompt instructions.
   Apply DNA tags to each insight.

5. **MERGE** new insights with existing ones:
   - For each person already in `persons`, append new insights to their array.
   - For new persons, add a new entry to `persons` with a `slug` field
     (kebab-case, e.g. `"slug": "alex-hormozi"`).
   - Dedup by `chunk_id`: skip insights whose `chunk_id` already exists.
   - **MANDATORY:** Every insight in the flat `insights` array MUST include
     a `person` field with the display name (e.g. `"person": "Alex Hormozi"`).
     Every person entry in `persons` MUST include a `slug` field.
     The memory enricher converts `person` → `person_slug` automatically,
     but the data must be present.

6. Save MERGED output using the **Write** tool to:
   ```
   artifacts/insights/INSIGHTS-STATE.json
   ```
   (NEVER use Bash/python3 to write this file — Write tool triggers logging hook.)

7. Validate: INSIGHTS-STATE.json has `persons` object with at least 1 person
   entry and `insights` array with >= 1 entry.

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 5 -- INSIGHT EXTRACTION                          [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Total insights:    {TOTAL}
  By tag:            FILOSOFIA: {N}, MODELO-MENTAL: {N}, HEURISTICA: {N}, FRAMEWORK: {N}, METODOLOGIA: {N}
  Persons:           {PERSON_COUNT}
  ──────────────────────────────────────────────────────────
  Progress: [==========>              ] 5/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 6: MCE BEHAVIORAL (LLM)

**What:** Extract behavioral patterns from insights.
**Depends on:** INSIGHTS-STATE.json from Step 5.

1. Read the prompt template:
   ```
   Read: core/templates/phases/prompt-mce-behavioral.md
   ```

2. Read INSIGHTS-STATE.json.

3. Execute behavioral pattern extraction. Follow the prompt instructions
   for output format (adds `behavioral_patterns` to INSIGHTS-STATE.json).

4. Save updated INSIGHTS-STATE.json using the **Write** tool (merged, not overwritten).

5. Validate: INSIGHTS-STATE.json now has `behavioral_patterns` field with
   at least 1 pattern per person.

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 6 -- MCE BEHAVIORAL                              [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Patterns found:    {PATTERN_COUNT}
    - {pattern_1_name}
    - {pattern_2_name}
    - {pattern_3_name}
  ──────────────────────────────────────────────────────────
  Progress: [============>            ] 6/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 7: MCE IDENTITY (LLM)

**What:** Extract value hierarchy, obsessions, paradoxes.
**Depends on:** INSIGHTS-STATE.json with behavioral_patterns from Step 6.

1. Read the prompt template:
   ```
   Read: core/templates/phases/prompt-mce-identity.md
   ```

2. Read INSIGHTS-STATE.json (with behavioral_patterns).

3. Execute identity extraction. Adds `value_hierarchy`, `obsessions`,
   `paradoxes` to INSIGHTS-STATE.json.

4. Save updated INSIGHTS-STATE.json using the **Write** tool.

5. Validate: `value_hierarchy` has at least 1 Tier 1 value.
   `obsessions` has exactly 1 MASTER obsession.

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 7 -- MCE IDENTITY                                [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Values:         {VALUE_COUNT} (Tier 1: {N}, Tier 2: {N})
  Obsessions:     {N} (Master: {MASTER_NAME})
  Paradoxes:      {N}
  ──────────────────────────────────────────────────────────
  Progress: [==============>          ] 7/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 8: MCE VOICE (LLM)

**What:** Extract Voice DNA -- speech patterns, signature phrases, emotional states.
**Depends on:** INSIGHTS-STATE.json + CHUNKS-STATE.json.

1. Read the prompt template:
   ```
   Read: core/templates/phases/prompt-mce-voice.md
   ```

2. Read INSIGHTS-STATE.json and CHUNKS-STATE.json.

3. Execute voice DNA extraction. Output is a standalone YAML file.

4. Save output to:
   ```
   knowledge/external/dna/persons/{SLUG}/VOICE-DNA.yaml
   ```

5. Validate: VOICE-DNA.yaml exists and has `signature_phrases`,
   `behavioral_states`, and dimensional scores.

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 8 -- MCE VOICE                                   [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Signature phrases: {PHRASE_COUNT}
  Behavioral states: {STATE_COUNT}
  Dimensions:        Certainty: {N}/10 | Authority: {N}/10 | Warmth: {N}/10 | Directness: {N}/10
  ──────────────────────────────────────────────────────────
  Progress: [================>        ] 8/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 9: IDENTITY CHECKPOINT (Human -- PAUSE HERE)

**What:** Present extracted identity core to user for validation.
**This is the ONLY step where you PAUSE and wait for user input.**

Display this to the user:

```
======================================================================
  IDENTITY CHECKPOINT -- {Person Name} ({SOURCE_CODE})
======================================================================

  VALUE HIERARCHY:
    Tier 1 (Existential):
      {list values with scores}
    Tier 2 (Operational):
      {list values with scores}

  MASTER OBSESSION:
    {obsession name} (intensity: {N}/10)

  PARADOXES DETECTED: {count}
    {list paradoxes with productive flag}

  VOICE DNA SUMMARY:
    Certainty: {N}/10 | Authority: {N}/10
    Warmth: {N}/10 | Directness: {N}/10
    Signature Phrases: {count}
    Behavioral States: {count}

  BEHAVIORAL PATTERNS: {count}
    {top 3 patterns with triggers}

----------------------------------------------------------------------
  Options:
    [1] APPROVE -- proceed to consolidation
    [2] REVISE  -- re-run MCE Identity with feedback
    [3] ABORT   -- save state and exit
----------------------------------------------------------------------
```

- If **APPROVE**: Continue to Step 10.
- If **REVISE**: Ask user what to adjust. Re-run Step 7 with user feedback
  as additional context. Then present checkpoint again.
- If **ABORT**: Save all state. Report what was completed. Stop.

After the user APPROVES, OUTPUT this exact block before proceeding:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 9 -- IDENTITY CHECKPOINT                         [OK]
  Slug: {SLUG}
  ──────────────────────────────────────────────────────────
  User decision: APPROVED
  ──────────────────────────────────────────────────────────
  Progress: [==================>      ] 9/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 10: CONSOLIDATION (LLM) -- 6 Sub-Steps, ALL Mandatory

**What:** Compile extracted knowledge into dossiers, sources, DNA YAMLs, theme dossiers, agents.
**Depends on:** All artifacts from Steps 3-8.
**CRITICAL:** Execute ALL 6 sub-steps. Do NOT skip any. Use **Write** tool for all saves.

#### 10.1 — Person Dossier (MANDATORY)

Read the template, then create or MERGE into the person dossier:
```
Read: core/templates/phases/dossier-compilation.md
```
- If `knowledge/external/dossiers/persons/DOSSIER-{PERSON}.md` EXISTS: read it,
  MERGE new MCE data (behavioral patterns, identity core, voice summary).
  Add sections if missing. Increment version. NEVER overwrite existing data.
- If NOT EXISTS: create from template.
- Save using **Write** tool.

#### 10.2 — DNA YAML Generation (MANDATORY — ALL 5 files)

From INSIGHTS-STATE.json, filter insights by `tag` and append to EACH DNA YAML.
**You MUST update ALL 5 files, not just one.** For each file:

1. **Read** the existing file (if exists)
2. **Append** new entries matching the tag. Dedup by insight ID.
3. **Increment** version and add `updated` timestamp.
4. **Save** using **Write** tool.

| Tag in Insight | Target File | Action |
|----------------|-------------|--------|
| `[FILOSOFIA]` | `knowledge/external/dna/persons/{SLUG}/FILOSOFIAS.yaml` | Append new entries |
| `[MODELO-MENTAL]` | `knowledge/external/dna/persons/{SLUG}/MODELOS-MENTAIS.yaml` | Append new entries |
| `[HEURISTICA]` | `knowledge/external/dna/persons/{SLUG}/HEURISTICAS.yaml` | Append new entries |
| `[FRAMEWORK]` | `knowledge/external/dna/persons/{SLUG}/FRAMEWORKS.yaml` | Append new entries |
| `[METODOLOGIA]` | `knowledge/external/dna/persons/{SLUG}/METODOLOGIAS.yaml` | Append new entries |

If a file has ZERO new insights for its tag, still read it and bump `updated` timestamp
(no new entries, but confirms it was checked). Update `DNA-CONFIG.yaml` counts.

#### 10.3 — Source Docs by Theme (MANDATORY)

Read the template:
```
Read: core/templates/phases/sources-compilation.md
```
Group all insights for this person by theme. For each theme:
- If `knowledge/external/sources/{SLUG-UPPER}/{THEME-UPPER}.md` EXISTS:
  MERGE new insights incrementally (append to existing sections, never overwrite).
- If NOT EXISTS: create from template.
- Create `_INDEX.md` if missing, or update it.
- Save using **Write** tool.

**Anti-duplication:** Before appending an insight, check if its `id` already
exists in the file. Skip if present.

#### 10.4 — Theme Dossiers (MANDATORY)

For each THEME that has 3+ insights from this person:
- Check if `knowledge/external/dossiers/themes/DOSSIER-{THEME-UPPER}.md` EXISTS.
- If EXISTS: MERGE — add/update this person's position in "POSICOES POR PESSOA" section.
  Add new frameworks, metrics, quotes. Never remove existing content from other persons.
- If NOT EXISTS and theme has 5+ insights: CREATE from theme dossier template
  in `dossier-compilation.md`.
- Save using **Write** tool.

**Anti-duplication:** Check person's section in the theme dossier before adding.
If person already has a section, update it with new data. Don't create duplicate sections.

#### 10.5 — Agent Files (MANDATORY)

Read the agent template:
```
Read: agents/_templates/TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md
```
Generate or update (all using **Write** or **Edit** tool):
```
agents/external/{SLUG}/AGENT.md       — version bump, maturidade bar, DNA refs
agents/external/{SLUG}/SOUL.md        — new beliefs from [FILOSOFIA] insights
agents/external/{SLUG}/MEMORY.md      — new insights + decisional patterns
agents/external/{SLUG}/DNA-CONFIG.yaml — update counts, version, timestamp
```
Integrate all MCE data (behavioral_patterns, value_hierarchy, obsessions,
paradoxes, VOICE-DNA) into the agent files following Template V3 structure.

#### 10.6 — Cross-Reference Validation (MANDATORY)

After all sub-steps, validate cross-references:
- Person dossier links to theme dossiers that exist
- Source docs link back to dossier
- Agent DNA-CONFIG.yaml counts match actual YAML file contents
- All version numbers are consistent across the person's files

Report any broken links or count mismatches.

After completing this step (all 6 sub-steps), OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 10 -- CONSOLIDATION                              [OK]
  Slug: {SLUG} | Bucket: {BUCKET}
  ──────────────────────────────────────────────────────────
  Dossier:    {CREATED or UPDATED}
  DNA YAMLs:  {N}/5 updated
  Sources:    {THEME_COUNT} theme docs
  Agents:     {AGENT_FILES_COUNT} files generated
  Validation: {PASS or FAIL}
  ──────────────────────────────────────────────────────────
  Progress: [====================>    ] 10/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 11: FINALIZE (Deterministic)

**What:** Memory enrichment, workspace sync, metrics finalization.

Run:
```bash
python3 -m core.intelligence.pipeline.mce.orchestrate finalize {SLUG}
```

Parse the JSON output. Verify:
- `enrichment.appended` -- insights added to agent MEMORY.md files
- `workspace_sync.synced` -- items synced to workspace
- `state.current` -- should be `complete`

After completing this step, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 11 -- FINALIZE                                   [OK]
  Slug: {SLUG}
  ──────────────────────────────────────────────────────────
  Enrichment appended:  {N}
  Workspace synced:     {N}
  State:                {STATE}
  ──────────────────────────────────────────────────────────
  Progress: [======================> ] 11/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### STEP 12: REPORT

Display the completion report:

```
======================================================================
  MCE PIPELINE COMPLETE -- {Person Name} ({SOURCE_CODE})
======================================================================

  EXTRACTION METRICS:
    Chunks:              {N}
    Insights:            {N} (HIGH: {N}, MEDIUM: {N}, LOW: {N})
    Behavioral Patterns: {N}
    Values:              {N} (Tier 1: {N}, Tier 2: {N})
    Obsessions:          {N} (Master: {name})
    Paradoxes:           {N}
    Signature Phrases:   {N}
    Behavioral States:   {N}

  FILES GENERATED:
    {list all files created/updated with absolute paths}

  VALIDATION:
    [ ] CHUNKS-STATE.json has chunks
    [ ] CANONICAL-MAP.json has entities
    [ ] INSIGHTS-STATE.json has insights + behavioral + identity + voice
    [ ] VOICE-DNA.yaml exists
    [ ] DOSSIER exists
    [ ] Agent files exist (AGENT.md, SOUL.md, MEMORY.md, DNA-CONFIG.yaml)
    [ ] All chunk_ids in insights exist in CHUNKS-STATE
    [ ] behavioral_patterns have min 2 chunk_ids each
    [ ] value_hierarchy has >= 1 Tier 1 value
    [ ] Max 1 MASTER obsession

  RESULT: {PASSED | FAILED with details}
======================================================================
```

After displaying the completion report, OUTPUT this exact block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 12 -- REPORT                                     [OK]
  Slug: {SLUG}
  ──────────────────────────────────────────────────────────
  Pipeline COMPLETE
  Duration: {TOTAL_DURATION}
  ──────────────────────────────────────────────────────────
  Progress: [========================] 12/12 steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## OUTPUT TEMPLATES — DYNAMIC RENDERING RULES

The MCE pipeline has TWO visual layers that work together:

- **Micro-panels** (per-step, automatic): The `mce_step_logger.py` hook fires on every Write
  to MCE artifacts and renders a PW=62 ASCII panel as hook feedback. These are machine-generated
  and invisible to the user (hook feedback goes to internal logs only).

- **Output templates** (checkpoint, manual): Claude reads and renders templates from
  `core/templates/output/MCE-OUTPUT-TEMPLATES.md` at specific checkpoints during the pipeline.
  These ARE visible — they appear directly in the chat as rendered ASCII panels (RW=72).

### Template Source

```
core/templates/output/MCE-OUTPUT-TEMPLATES.md
```

7 templates, 814 lines, RW=72 inner width. Read this file ONCE at pipeline start
and cache the section boundaries. Each template is inside a fenced code block (```).

### Rendering Rules — WHEN to Show Each Template

| Trigger Point | Template # | Template Name | Condition |
|---------------|-----------|---------------|-----------|
| After Step 5 completes | 1 | EXTRACTION SUMMARY | ALWAYS — shows DNA delta, files, top insights |
| After Step 10.5 (agent files) | 2 | PERSON AGENT | ALWAYS — shows agent card, 11 parts, connections |
| After Step 10.5 (if cargo enriched) | 3 | CARGO AGENT ENRICHMENT | IF cargo agents were created or enriched |
| After Step 10.4 (theme dossiers) | 4 | THEME DOSSIER | IF any theme dossier was created or updated |
| After Step 11 (finalize) | 5 | WORKSPACE SYNC | IF workspace items were synced (enrichment.appended > 0) |
| After Step 12 (report) | 6 | VALIDATION GATE | ALWAYS — final checklist + resumo da fonte |
| End of multi-source session | 7 | SESSION CONSOLIDATION | IF 2+ sources processed in same session |

### Rendering Rules — HOW to Fill Templates

**Step 1: Read the template block.**
Extract the code-fenced block for the target template number from MCE-OUTPUT-TEMPLATES.md.

**Step 2: Collect real data.**
Read the relevant artifact files to get actual numbers:

| Template | Data Sources |
|----------|-------------|
| 1 EXTRACTION SUMMARY | INSIGHTS-STATE.json (counts by tag), CHUNKS-STATE.json (chunk count), DNA YAMLs (element counts) |
| 2 PERSON AGENT | Agent files (AGENT.md line count, parts), DNA-CONFIG.yaml (composition), AGENT-INDEX.yaml |
| 3 CARGO ENRICHMENT | AGENT-INDEX.yaml (cargo agents), DNA-CONFIG.yaml (weights before/after) |
| 4 THEME DOSSIER | Dossier files (section counts before/after), _INDEX.md |
| 5 WORKSPACE SYNC | orchestrate.py finalize output (enrichment counts, workspace sync counts) |
| 6 VALIDATION GATE | All artifacts (checklist validation), cumulative metrics |
| 7 SESSION CONSOLIDATION | All person slugs processed, AGENT-INDEX.yaml, all dossiers |

**Step 3: Replace placeholders.**
Every `{PLACEHOLDER}` in the template must be replaced with real data. Rules:

- `{BAR_20}` — Generate using: `"█" * int(pct/100*20) + "░" * (20 - int(pct/100*20))`
- `{BAR_30}` — Same logic with width 30
- `{N_ANTES}` / `{N_DEPOIS}` — Read from previous state vs current state. If greenfield (first run), ANTES = 0
- `{DELTA}` — Always show with sign: `+13`, `-2`, or `0`
- `{%}` — Percentage of that layer relative to total elements
- `{SLUG_UPPER}` — `slug.upper().replace("-", " ")`
- `{BUCKET_ICON}` — `📚 EXTERNAL` or `🏢 BUSINESS` or `🧠 PERSONAL`
- `{HH:MM}` — Current time
- Progress bar at bottom — Update S00-S12 markers: `●` done, `◉` current, `○` pending

**Step 4: Render in chat.**
Print the filled template directly. Do NOT wrap in additional code fences.
The template already uses Unicode box-drawing characters that render correctly in the terminal.

### Rendering Rules — WHAT NEVER TO DO

```
NEVER skip a template that the trigger condition says ALWAYS
NEVER show a template with unfilled {PLACEHOLDER} variables
NEVER abbreviate or summarize a template — show it COMPLETE
NEVER show Template 7 (SESSION CONSOLIDATION) for single-source runs
NEVER show templates for steps that were SKIPPED or FAILED
NEVER wrap the rendered template in markdown code fences (```) — print raw
```

### Rendering Rules — COEXISTENCE WITH MICRO-PANELS

The hook-generated micro-panels (PW=62) and the output templates (RW=72) serve different purposes:

| Aspect | Micro-Panel (Hook) | Output Template (Skill) |
|--------|-------------------|------------------------|
| Width | PW=62 (66 total) | RW=72 (78 total) |
| Trigger | Every Write to MCE artifact | Specific checkpoint moments |
| Visibility | Internal (hook feedback log) | User-facing (chat output) |
| Content | Single-step metrics snapshot | Cross-step summary with deltas |
| Who renders | `mce_step_logger.py` (Python) | Claude (reads template + fills) |

Both fire independently. The micro-panel logs to JSONL for audit. The output template
shows in chat for the user. They do NOT conflict — they complement.

### Rendering Rules — STEP-BY-STEP PANEL + TEMPLATE SEQUENCE

During a full pipeline run, the user sees this sequence:

```
Step 0: DETECT INPUT
  → Inline status panel (RULE 2)

Step 1: INGEST
  → Inline status panel

Step 2: BATCH
  → Inline status panel

Step 3: CHUNK
  → Inline status panel
  (hook: micro-panel fires silently on CHUNKS-STATE.json write)

Step 4: ENTITY RESOLUTION
  → Inline status panel
  (hook: micro-panel fires silently on CANONICAL-MAP.json write)

Step 5: INSIGHT EXTRACTION
  → Inline status panel
  → ★ TEMPLATE 1: EXTRACTION SUMMARY (DNA delta, files, top insights)

Step 6: MCE BEHAVIORAL
  → Inline status panel

Step 7: MCE IDENTITY
  → Inline status panel

Step 8: MCE VOICE
  → Inline status panel

Step 9: IDENTITY CHECKPOINT
  → PAUSE — show checkpoint display, wait for user

Step 10: CONSOLIDATION (6 sub-steps)
  → After 10.1-10.3: inline status
  → After 10.4 (theme dossiers): ★ TEMPLATE 4: THEME DOSSIER (if any created/updated)
  → After 10.5 (agent files): ★ TEMPLATE 2: PERSON AGENT
  → After 10.5 (if cargo): ★ TEMPLATE 3: CARGO AGENT ENRICHMENT
  → After 10.6 (validation): inline status
  → Consolidation complete panel

Step 11: FINALIZE
  → Inline status panel
  → ★ TEMPLATE 5: WORKSPACE SYNC (if enrichment.appended > 0)

Step 12: REPORT
  → ★ TEMPLATE 6: VALIDATION GATE (always — final checklist)
  → Completion report

End of Session (if multi-source):
  → ★ TEMPLATE 7: SESSION CONSOLIDATION
```

### Template Rendering — Practical Example

After Step 5 completes for slug `pedro-valerio` in bucket `business`:

1. Read `core/templates/output/MCE-OUTPUT-TEMPLATES.md`
2. Extract Template 1 (EXTRACTION SUMMARY) code block
3. Read `artifacts/insights/INSIGHTS-STATE.json` — count insights by tag
4. Read `artifacts/chunks/CHUNKS-STATE.json` — count chunks
5. Read DNA YAMLs — count elements per layer (before = 0 if greenfield)
6. Fill all placeholders with real numbers
7. Print the filled template in chat

The result looks like a rich ASCII dashboard with real metrics, not placeholder text.

---

## ERROR HANDLING

If any step fails:
1. Log the error with step number and details.
2. Save all state (orchestrate.py handles this for deterministic steps).
3. Report to user: "Step {N} ({name}) failed: {error}. Run `/pipeline-mce {SLUG}` to resume."

**Circuit breaker:** If any LLM step fails 3 times consecutively, save state and stop.
Report: "Pipeline halted after 3 failures at Step {N}. Manual intervention needed."

**Context pressure:** For large files approaching context limits, process in batches
of 3 files max. Save state incrementally.

---

## INVOCATION

- `/pipeline-mce` -- primary command
- `/process-jarvis` -- backward-compatible (routes to MCE if MCE prompts exist)
- Natural language: "processar fonte", "extrair DNA de", "pipeline cognitivo"

Examples:
```
/pipeline-mce AH
/pipeline-mce --person alex-hormozi --files knowledge/external/inbox/alex-hormozi/*.txt
/pipeline-mce alex-hormozi (resume from last state)
```

---

## FILE REFERENCE

| File | Purpose |
|------|---------|
| `core/intelligence/pipeline/mce/orchestrate.py` | Deterministic orchestrator (ingest/batch/finalize/status) |
| `core/intelligence/pipeline/mce/log_renderer.py` | Progressive ASCII progress panels for 12 pipeline steps |
| `core/intelligence/pipeline/mce/state_machine.py` | FSM for pipeline phase transitions |
| `core/intelligence/pipeline/mce/metadata_manager.py` | Progress tracking per run |
| `core/intelligence/pipeline/mce/metrics.py` | Wall-clock timing per phase |
| `core/intelligence/pipeline/mce/workflow_detector.py` | Greenfield/brownfield detection |
| `core/intelligence/pipeline/scope_classifier.py` | 6-signal file classification |
| `core/intelligence/pipeline/smart_router.py` | File routing to correct bucket |
| `core/intelligence/pipeline/inbox_organizer.py` | Inbox organization by entity |
| `core/intelligence/pipeline/batch_auto_creator.py` | Batch creation with registry |
| `core/intelligence/pipeline/memory_enricher.py` | Insight routing to agent MEMORY.md |
| `core/intelligence/pipeline/workspace_sync.py` | Business knowledge to workspace sync |
| `core/templates/phases/prompt-1.1-chunking.md` | Chunking prompt |
| `core/templates/phases/prompt-1.2-entity-resolution.md` | Entity resolution prompt |
| `core/templates/phases/prompt-2.1-insight-extraction.md` | Insight extraction prompt |
| `core/templates/phases/prompt-2.1-dna-tags.md` | DNA tag classification |
| `core/templates/phases/prompt-mce-behavioral.md` | MCE-1: Behavioral patterns |
| `core/templates/phases/prompt-mce-identity.md` | MCE-2: Identity layers |
| `core/templates/phases/prompt-mce-voice.md` | MCE-3: Voice DNA |
| `core/templates/phases/dossier-compilation.md` | Dossier compilation |
| `core/templates/phases/sources-compilation.md` | Source compilation |
| `agents/_templates/TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md` | Agent template V3 |

---

## STATE PERSISTENCE

All state persists to: `.claude/mission-control/mce/{SLUG}/`

| File | Content |
|------|---------|
| `pipeline_state.yaml` | FSM state + transition history |
| `metadata.yaml` | Phase progress + sources processed |
| `metrics.yaml` | Wall-clock timing per phase |

Audit log: `logs/mce-orchestrate.jsonl` (append-only, one JSON line per command).

Resume is automatic: run `/pipeline-mce {SLUG}` and the skill picks up from the
first incomplete step.

---

## KNOWLEDGE OPS SQUAD INTEGRATION

The MCE pipeline maps to the Knowledge Ops squad agents
(`agents/system/knowledge-ops/`). Each step conceptually delegates to:

| Squad Agent | Role | Pipeline Steps |
|-------------|------|----------------|
| **Atlas** (The Classifier) | Classifies and routes incoming content | Steps 0-1 (DETECT + INGEST) |
| **Sage** (The Extractor) | Extracts insights, behavioral patterns, identity layers | Steps 3-8 (CHUNK through VOICE) |
| **Lens** (The Validator) | Validates extraction quality, identity checkpoint | Step 9 (IDENTITY CHECKPOINT) |
| **Forge** (The Compiler) | Compiles dossiers, DNA YAMLs, agent files | Step 10 (CONSOLIDATION) |
| **Echo** (The Cloner) | Generates mind-clone agents from compiled knowledge | Step 10.4 (Agent Generation) |

The squad agents are NOT invoked programmatically. They serve as the
conceptual architecture for which agent "owns" each pipeline phase.
When debugging or extending the pipeline, reference the squad agent
responsible for that phase.
