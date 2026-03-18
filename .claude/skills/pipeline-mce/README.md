# MCE Pipeline Skill

## What It Does

Orchestrates the full Mega Brain cognitive extraction pipeline. Takes raw transcripts
and produces: chunked content, resolved entities, 5-layer DNA YAMLs, Voice DNA,
behavioral patterns, identity layers (values/obsessions/paradoxes), dossiers, source
compilations, and fully-generated mind-clone agents.

## Quick Start

```
/pipeline-mce AH                    # Process Alex Hormozi sources
/pipeline-mce --person cole-gordon   # Process by person slug
/process-jarvis CG                   # Backward-compatible alias
```

## Pipeline Flow

```
PHASE 1: FOUNDATION
  1.1 Chunking (prompt-1.1) -> CHUNKS-STATE.json
  1.2 Entity Resolution (prompt-1.2) -> CANONICAL-MAP.json

PHASE 2: EXTRACTION (parallel tracks)
  Track A (Knowledge):
    2A.1 Insight Extraction (prompt-2.1 + dna-tags) -> INSIGHTS-STATE.json
    2A.2 Narrative Synthesis (prompt-3.1) -> SOURCE-{ID}.md
  Track B (Cognitive):
    2B.1 Behavioral Patterns (prompt-mce-behavioral) -> behavioral_patterns
    2B.2 Identity Layer (prompt-mce-identity) -> values/obsessions/paradoxes
    2B.3 Voice DNA (prompt-mce-voice) -> VOICE-DNA.yaml

PHASE 3: IDENTITY CHECKPOINT (human approval)
PHASE 4: CONSOLIDATION (dossiers + sources + DNA YAMLs)
PHASE 5: AGENT GENERATION (agent files + memory + workspace sync)
PHASE 6: VALIDATION (integrity check)
```

## Resume Support

The pipeline saves state to `.claude/mission-control/mce/{slug}/pipeline_state.yaml`.
If interrupted, re-run the same command to resume from the last incomplete phase.

## Key Outputs

| Output | Location |
|--------|----------|
| Chunks | `artifacts/chunks/CHUNKS-STATE.json` |
| Canonical Map | `artifacts/canonical/CANONICAL-MAP.json` |
| Insights + MCE | `artifacts/insights/INSIGHTS-STATE.json` |
| Voice DNA | `knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml` |
| DNA YAMLs (5 layers) | `knowledge/external/dna/persons/{slug}/` |
| Dossier | `knowledge/external/dossiers/persons/DOSSIER-{PERSON}.md` |
| Sources | `knowledge/external/sources/{person}/{theme}.md` |
| Agent | `agents/external/{slug}/AGENT.md` + SOUL.md + MEMORY.md |
