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

5. Save MERGED output to:
   ```
   artifacts/canonical/CANONICAL-MAP.json
   ```

6. Validate: CANONICAL-MAP.json exists and has entities mapped.

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
   - For new persons, add a new entry to `persons`.
   - Dedup by `chunk_id`: skip insights whose `chunk_id` already exists.

6. Save MERGED output to:
   ```
   artifacts/insights/INSIGHTS-STATE.json
   ```

7. Validate: INSIGHTS-STATE.json has `persons` object with at least 1 person
   entry and `insights` array with >= 1 entry.

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

4. Save updated INSIGHTS-STATE.json (merged, not overwritten).

5. Validate: INSIGHTS-STATE.json now has `behavioral_patterns` field with
   at least 1 pattern per person.

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

4. Save updated INSIGHTS-STATE.json.

5. Validate: `value_hierarchy` has at least 1 Tier 1 value.
   `obsessions` has exactly 1 MASTER obsession.

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

---

### STEP 10: CONSOLIDATION (LLM)

**What:** Compile extracted knowledge into dossiers, sources, DNA YAMLs.
**Depends on:** All artifacts from Steps 3-8.

1. **Dossier compilation.** Read and execute:
   ```
   Read: core/templates/phases/dossier-compilation.md
   ```
   Save to: `knowledge/external/dossiers/persons/DOSSIER-{PERSON}.md`

2. **Source compilation.** Read and execute:
   ```
   Read: core/templates/phases/sources-compilation.md
   ```
   Group insights by theme per person.
   Save to: `knowledge/external/sources/{slug}/{theme}.md`

3. **DNA YAML generation.** From INSIGHTS-STATE.json, generate/update:
   ```
   knowledge/external/dna/persons/{SLUG}/FILOSOFIAS.yaml
   knowledge/external/dna/persons/{SLUG}/MODELOS-MENTAIS.yaml
   knowledge/external/dna/persons/{SLUG}/HEURISTICAS.yaml
   knowledge/external/dna/persons/{SLUG}/FRAMEWORKS.yaml
   knowledge/external/dna/persons/{SLUG}/METODOLOGIAS.yaml
   ```
   Filter insights by `tag` field. If files exist, MERGE: increment version,
   append new entries, preserve existing.

4. **Agent generation.** Read the agent template:
   ```
   Read: agents/_templates/TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md
   ```
   Generate or update:
   ```
   agents/external/{SLUG}/AGENT.md
   agents/external/{SLUG}/SOUL.md
   agents/external/{SLUG}/MEMORY.md
   agents/external/{SLUG}/DNA-CONFIG.yaml
   ```
   Integrate all MCE data (behavioral_patterns, value_hierarchy, obsessions,
   paradoxes, VOICE-DNA) into the agent files following Template V3 structure.

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
