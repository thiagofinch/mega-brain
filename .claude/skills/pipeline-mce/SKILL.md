# MCE Pipeline -- Orchestrator

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

Orchestrates the MCE (Mega Cognitive Extraction) pipeline using 13 conceptual roles
to transform raw transcripts into 10 DNA layers (L1-L10), Voice DNA, behavioral
patterns, identity layers, dossiers, and mind-clone agents.

This skill is the **conductor** — it sequences steps, manages FSM transitions via
`core/intelligence/pipeline/mce/orchestrate.py`, and executes LLM phases using
prompt templates in `core/templates/phases/`. It does NOT delegate to external
agent files.

> **Note:** The 13 roles listed below (gate, parse, canon, etc.) are CONCEPTUAL
> divisions of responsibility within this skill. They are NOT backed by standalone
> agent files. Execution is performed by this pipeline-mce skill itself using:
> - **Deterministic steps:** `orchestrate.py` (ingest, batch, finalize, status)
> - **LLM steps:** prompt templates in `core/templates/phases/`
> - **State management:** `core/intelligence/pipeline/mce/state_machine.py`

## ARCHITECTURE

```
SKILL.md (this file) — Orchestrator + all 13 roles
    |
    +-- orchestrate.py  — Deterministic steps (ingest, batch, finalize)
    |
    +-- core/templates/phases/  — LLM prompt templates (14 templates)
    |       prompt-1.1-chunking.md
    |       prompt-1.2-entity-resolution.md
    |       prompt-2.1-insight-extraction.md
    |       prompt-2.1-dna-tags.md
    |       prompt-mce-behavioral.md
    |       prompt-mce-identity.md
    |       prompt-mce-voice.md
    |       dossier-compilation.md
    |       sources-compilation.md
    |       ... (+ 5 more)
    |
    +-- PIPELINE-MANIFEST.json (.claude/mission-control/)
    |
    +-- StepResult (per step completion -> hooks render logs)
```

## PIPELINE MANIFEST

Before starting, verify manifest exists:

```bash
python3 -m core.intelligence.pipeline.mce.pipeline_manifest_builder --validate
```

If missing, rebuild. Steps consult this for expected artifacts.

---

## EXECUTION: 12 STEPS via 13 CONCEPTUAL ROLES

Every run follows these steps in order. Do NOT skip steps.

Each role below is executed by this pipeline-mce skill. Deterministic roles
use `orchestrate.py`. LLM roles use the specified prompt template from
`core/templates/phases/`.

### STEP 0: DETECT INPUT

Read the user's message to determine:
- **File mode:** User gave a file path -> set `FILE_PATH`
- **Slug mode:** User gave a person code/slug -> set `SLUG`
- **Resume mode:** State exists -> resume from first incomplete step

```bash
python3 -m core.intelligence.pipeline.mce.orchestrate status {SLUG}
```

If `current_state` is not `init` and not `complete`, RESUME from matching step.

---

### STEPS 1-2: INTAKE — Role: `gate` (The Gatekeeper)

Execution: `orchestrate.py` (deterministic, no LLM)

```
Step 1 — *ingest "{FILE_PATH}"    -> classify, route, organize
Step 2 — *batch {SLUG}            -> create batches (--single-file if needed)
```

Both deterministic (orchestrate.py). Emits StepResult per step.

---

### STEP 3: CHUNK — Role: `parse` (The Parser)

Execution: prompt template `core/templates/phases/prompt-1.1-chunking.md`

```
*chunk {SLUG}
```

Reads prompt-1.1-chunking.md. Output: `artifacts/chunks/{SLUG}/CHUNKS-STATE.json`

---

### STEP 4: ENTITY RESOLUTION — Role: `canon` (The Cartographer)

Execution: prompt template `core/templates/phases/prompt-1.2-entity-resolution.md`

```
*resolve {SLUG}
```

Reads prompt-1.2-entity-resolution.md. Output: `artifacts/canonical/CANONICAL-MAP.json` (global).
CRITICAL: Read existing -> merge -> write. NEVER overwrite.

---

### STEP 5: INSIGHT EXTRACTION — Role: `dig` (The Excavator)

Execution: prompt templates `core/templates/phases/prompt-2.1-insight-extraction.md` + `prompt-2.1-dna-tags.md`

```
*extract {SLUG}
```

Reads prompt-2.1-insight-extraction.md + prompt-2.1-dna-tags.md.
Output: `artifacts/insights/{SLUG}/INSIGHTS-STATE.json`

---

### STEP 6: MCE BEHAVIORAL — Role: `behav` (The Behaviorist)

Execution: prompt template `core/templates/phases/prompt-mce-behavioral.md`

```
*analyze-behavior {SLUG}
```

Reads prompt-mce-behavioral.md. Adds `behavioral_patterns` to INSIGHTS-STATE.json.
Generates `BEHAVIORAL-PATTERNS.yaml` (L6).

---

### STEP 7: MCE IDENTITY — Role: `psych` (The Psychologist)

Execution: prompt template `core/templates/phases/prompt-mce-identity.md`

```
*profile-identity {SLUG}
```

Reads prompt-mce-identity.md. Adds `value_hierarchy`, `obsessions`, `paradoxes` to INSIGHTS-STATE.
Generates: `VALUES-HIERARCHY.yaml` (L7), `OBSESSIONS.yaml` (L9), `PARADOXES.yaml` (L10).

---

### STEP 8: MCE VOICE — Role: `voice` (The Linguist)

Execution: prompt template `core/templates/phases/prompt-mce-voice.md`

```
*extract-voice {SLUG}
```

Reads prompt-mce-voice.md. Output: `VOICE-DNA.yaml` (L8).

---

### STEP 9: IDENTITY CHECKPOINT — Role: `guard` (The Sentinel)

Execution: human gate (this skill pauses and presents options)

```
*checkpoint {SLUG}
```

**PAUSE HERE.** Display identity summary and wait for human decision:
- **[1] APPROVE** -> continue to Step 10
- **[2] REVISE** -> return to Step 7 (psych). Max 3 revisions.
- **[3] ABORT** -> save state, stop pipeline

---

### STEPS 10.1-10.2: COMPILATION — Role: `scribe` (The Chronicler)

Execution: prompt templates `core/templates/phases/dossier-compilation.md` + `sources-compilation.md`

```
*compile-all {SLUG}
```

Reads dossier-compilation.md + sources-compilation.md.
Output: `DOSSIER-{PERSON}.md` + `sources/{slug}/{theme}.md`

---

### STEP 10.3: DNA ASSEMBLY — Role: `weave` (The Assembler)

Execution: LLM-driven tag filtering from INSIGHTS-STATE

```
*assemble-dna {SLUG}
```

Filters INSIGHTS-STATE by tag -> generates/updates 10 DNA YAMLs (L1-L10).
L8 (VOICE-DNA) already exists from Step 8 -- do NOT regenerate.

---

### STEPS 10.4-10.5: AGENT GENERATION — Role: `clone` (The Architect)

Execution: agent templates from `agents/_templates/`

```
*clone-all {SLUG}
```

Reads TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md + ACTIVATION-TEMPLATE.yaml.
Output: 5 files in `agents/external/{SLUG}/` (AGENT.md, SOUL.md, MEMORY.md, DNA-CONFIG.yaml, ACTIVATION.yaml).

---

### POST-PIPELINE: INDEXATION — Role: `index` (The Librarian)

Execution: LLM + deterministic (RAG rebuild, graph enrichment)

```
*index-all {SLUG}
```

Rebuilds RAG indexes, enriches Knowledge Graph, updates Domain Contracts, validates Conclave readiness.

---

### STEPS 11-12: FINALIZATION — Role: `ops` (The Operator)

Execution: `orchestrate.py` (deterministic, no LLM)

```
*finalize {SLUG}
*report {SLUG}
```

Both deterministic (orchestrate.py). Memory enrichment -> workspace sync -> completion report.

---

## ERROR HANDLING

If any step fails:
1. Error logged with step number and details
2. State saved automatically (FSM persists)
3. Report to user: "Step {N} ({role}) failed. Run `/pipeline-mce {SLUG}` to resume."

**Circuit breaker:** 3 consecutive LLM failures -> halt
**Context pressure:** Large files processed in batches of 3 max
**Recovery:** `python3 -m core.intelligence.pipeline.mce.orchestrate recover {SLUG}`

---

## INVOCATION

- `/pipeline-mce` -- primary command
- `/process-jarvis` -- backward-compatible alias
- Natural language: "processar fonte", "extrair DNA de", "pipeline cognitivo"

```
/pipeline-mce AH
/pipeline-mce --person alex-hormozi
/pipeline-mce alex-hormozi    (resume from last state)
```

---

## 13 CONCEPTUAL ROLES (executed by this skill)

These roles are executed by the pipeline-mce skill itself using prompt templates
in `core/templates/phases/` and deterministic scripts in `core/intelligence/pipeline/mce/`.
They are NOT standalone agent files.

| # | Role | Codename | Tier | Steps | Executor | Mechanism |
|---|------|----------|------|-------|----------|-----------|
| 1 | The Gatekeeper | `gate` | 1 Intake | 0, 1, 2 | Worker | `orchestrate.py` |
| 2 | The Parser | `parse` | 2 Parsing | 3 | Agent | `prompt-1.1-chunking.md` |
| 3 | The Cartographer | `canon` | 2 Parsing | 4 | Agent | `prompt-1.2-entity-resolution.md` |
| 4 | The Excavator | `dig` | 3 Extraction | 5 | Agent | `prompt-2.1-insight-extraction.md` |
| 5 | The Behaviorist | `behav` | 4 Profiling | 6 | Agent | `prompt-mce-behavioral.md` |
| 6 | The Psychologist | `psych` | 4 Profiling | 7 | Agent | `prompt-mce-identity.md` |
| 7 | The Linguist | `voice` | 4 Profiling | 8 | Agent | `prompt-mce-voice.md` |
| 8 | The Sentinel | `guard` | 5 Validation | 9 | Human | Skill pauses for input |
| 9 | The Chronicler | `scribe` | 6 Synthesis | 10.1-10.2 | Agent | `dossier-compilation.md` + `sources-compilation.md` |
| 10 | The Assembler | `weave` | 6 Synthesis | 10.3 | Agent | Tag filter from INSIGHTS-STATE |
| 11 | The Architect | `clone` | 7 Generation | 10.4-10.5 | Clone | `agents/_templates/` |
| 12 | The Librarian | `index` | 7 Distribution | post-10 | Agent | RAG + graph rebuild |
| 13 | The Operator | `ops` | 8 Operations | 11, 12 | Worker | `orchestrate.py` |

---

## DNA 10-LAYER OUTPUT

| Layer | File | Generated by |
|-------|------|-------------|
| L1 | FILOSOFIAS.yaml | weave (tag filter) |
| L2 | MODELOS-MENTAIS.yaml | weave (tag filter) |
| L3 | HEURISTICAS.yaml | weave (tag filter) |
| L4 | FRAMEWORKS.yaml | weave (tag filter) |
| L5 | METODOLOGIAS.yaml | weave (tag filter) |
| L6 | BEHAVIORAL-PATTERNS.yaml | behav + weave |
| L7 | VALUES-HIERARCHY.yaml | psych + weave |
| L8 | VOICE-DNA.yaml | voice (standalone) |
| L9 | OBSESSIONS.yaml | psych + weave |
| L10 | PARADOXES.yaml | psych + weave |

---

## STATE PERSISTENCE

All state: `.claude/mission-control/mce/{SLUG}/`

| File | Content |
|------|---------|
| `pipeline_state.yaml` | FSM state + transition history (17 states) |
| `metadata.yaml` | Phase progress + sources processed |
| `metrics.yaml` | Wall-clock timing per phase |
| `step_results/` | StepResult JSON per step (emitted by roles) |

Manifest: `.claude/mission-control/PIPELINE-MANIFEST.json`
Audit: `logs/mce-orchestrate.jsonl`

---

## POST-PIPELINE RENDERING (MANDATORY)

After pipeline completion, render the audit view with:

```python
from core.intelligence.pipeline.mce.pipeline_audit_renderer import render_pipeline_audit
output = render_pipeline_audit('{SLUG}')
print(output)
```

Or from the command line:

```bash
python3 -c "from core.intelligence.pipeline.mce.pipeline_audit_renderer import render_pipeline_audit; print(render_pipeline_audit('{SLUG}'))"
```

This renders a manifest-driven audit at W=76. Each of the pipeline steps
(S00-S11) appears as a block showing:

- Execution status (COMPLETED / FAILED / NOT EXECUTED)
- Artifact verification (FOUND/MISSING with file count and size, verified
  directly against the filesystem -- not trusting StepResult counters)
- Quality gate checkpoint results (PASS/FAIL per checkpoint ID)

After all step blocks, three summary sections appear:

- **Pipeline Progress** -- completed / total steps with progress bar
- **Artifact Integrity** -- found / expected artifacts across all steps,
  listing step IDs where artifacts are MISSING
- **DNA Layer Inventory** -- filesystem glob of the slug's DNA directory,
  reporting count per layer discovered (not hardcoded)

**Auto-adaptation:** Adding a new step to `PIPELINE-MANIFEST.json` causes
`render_pipeline_audit` to render it automatically as `NOT EXECUTED`
without any code changes to the renderer.

**Note:** `render_briefing` is deprecated. If called, it emits a
`DeprecationWarning` and forwards to `render_pipeline_audit`.
