# Visual Extraction Command

Process a video transcript that contains VISUAL descriptions (screen content, UI elements, clicks, navigation) alongside verbal content (speech, explanations). This command extracts structured information from what is SHOWN on screen, not just what is SAID.

> **Version:** 1.0.0
> **Extension of:** Phase 4 (Insight Extraction)
> **Output:** `processing/visual/{SOURCE_ID}-visual.json`
> **Prompt:** `core/templates/phases/prompt-visual-extraction.md`

---

## Input

$ARGUMENTS = path to video file, transcript file, or pre-structured JSON

```
/visual-extract [path-to-video-or-transcript] [--person "Name"] [--type TYPE]
```

**Parameters:**
- `path` (required): Path to the source file
- `--person "Name"` (optional): Name of the presenter/person in the video
- `--type TYPE` (optional): Content type hint — `screencast`, `demo`, `tutorial`, `walkthrough`, `presentation`

---

## PRIMEIRA ACAO OBRIGATORIA

> **ANTES de processar, LEIA `/system/SESSION-STATE.md`**
> Verificar se este video ja foi processado visualmente.

---

## Workflow

### Step 1: Detect Input Type

```
PARSE file extension from $ARGUMENTS:

IF extension in [.mp4, .mov, .webm, .avi, .mkv]:
  -> INPUT_TYPE = "video_raw"
  -> Transcribe with visual frame extraction (Step 1b)

IF extension in [.txt, .md]:
  -> INPUT_TYPE = "visual_transcript"
  -> Process as visual transcript directly (Step 2)

IF extension in [.json]:
  -> INPUT_TYPE = "pre_structured"
  -> Validate JSON schema, skip to Step 4

ELSE:
  -> LOG ERROR: "Unsupported file type: {extension}"
  -> EXIT with status: UNSUPPORTED_FORMAT
```

### Step 1b: Transcribe Video with Visual Context (only for raw video)

```
IF INPUT_TYPE == "video_raw":

  # Audio transcription
  whisper "$ARGUMENTS" --language auto --output_format txt --output_dir "processing/visual/"

  # Visual frame extraction (if ffmpeg available)
  # Extract 1 frame every 30 seconds for visual reference
  ffmpeg -i "$ARGUMENTS" -vf "fps=1/30" -q:v 2 "processing/visual/frames/frame_%04d.jpg"

  -> TRANSCRIPT_PATH = generated .txt file
  -> FRAMES_DIR = processing/visual/frames/
  -> LOG: "Transcribed {duration} of audio, extracted {N} visual frames"
```

### Step 2: Extract Path Metadata

```
PARSE $ARGUMENTS to extract:

SOURCE_PERSON = from --person flag, or extract from path
  -> Ex: --person "Cole Gordon" or path contains "COLE GORDON/"

SOURCE_TYPE = from --type flag, or infer:
  -> If "screencast" in filename or path -> "screencast"
  -> If "demo" in filename or path -> "demo"
  -> If "tutorial" in filename or path -> "tutorial"
  -> Default -> "video_visual"

SOURCE_ID = Generate unique ID
  -> Format: "{INITIALS}-VIS{NNN}"
  -> Ex: "CG-VIS001" for Cole Gordon visual extraction #1

SOURCE_DATETIME = Extract from filename if present, else NOW()
```

### Step 3: Load State Files

```
Required state files (create if missing):

INSIGHTS_STATE = READ /processing/insights/INSIGHTS-STATE.json
  -> IF missing: CREATE with {"insights_state": {"persons": {}, "themes": {}, "version": "v1", "change_log": []}}

CHUNKS_STATE = READ /processing/chunks/CHUNKS-STATE.json
  -> IF missing: CREATE with {"chunks": [], "meta": {"version": "v1"}}
```

### Step 4: Execute Visual Extraction Protocol

```
READ core/templates/phases/prompt-visual-extraction.md

APPLY visual extraction protocol to TRANSCRIPT content.

INPUT:
  - transcript: Full content of the transcript file
  - person: SOURCE_PERSON (if known)
  - source_type: SOURCE_TYPE
  - frames: FRAMES_DIR (if available from Step 1b)

EXTRACTION RULES:
  - Dual-channel evidence: tag every observation as VISUAL, VERBAL, or BOTH
  - 9 categories (A through I) — see prompt template for details
  - Capture ALL identifiers: IDs, names, URLs, field names, values
  - Preserve hierarchy: parent > child relationships
  - Capture sequences: navigation flows, click paths, state transitions
  - No interpretation: describe what IS, not what it MEANS
  - Timestamps mandatory for every segment
  - Minimum 1 segment per 30 seconds of content
  - Divergences (screen shows X, speech says Y) are STOPS — record as type "divergencia"

OUTPUT:
  VISUAL_SEGMENTS = array of structured segments
  RELATIONSHIPS = connections between entities discovered
  HEURISTICS = principles, anti-patterns, methodology demonstrated
```

### Step 5: Generate Structured Output

```
BUILD visual extraction JSON:

{
  "source": {
    "type": "video_visual",
    "title": "{extracted or provided title}",
    "person": "{SOURCE_PERSON}",
    "source_id": "{SOURCE_ID}",
    "source_path": "{$ARGUMENTS}",
    "source_datetime": "{SOURCE_DATETIME}",
    "duration": "{estimated or extracted duration}",
    "extraction_type": "visual",
    "content_type": "{SOURCE_TYPE}"
  },
  "segments": [
    {
      "timestamp": "MM:SS",
      "type": "tela|fala|acao|divergencia",
      "category": "A|B|C|D|E|F|G|H|I",
      "content": "exact description of what is visible or spoken",
      "confidence": "high|medium|low",
      "identifiers": {
        "ids": [],
        "names": [],
        "fields": [],
        "values": [],
        "urls": []
      },
      "evidence_type": "visual|verbal|both",
      "truth_candidate": true|false
    }
  ],
  "relationships_discovered": [
    {
      "from": "entity A",
      "to": "entity B",
      "type": "feeds_into|triggers|contains|links_to|depends_on",
      "evidence": "visual|verbal|both",
      "timestamp": "MM:SS"
    }
  ],
  "heuristics_captured": [
    {
      "id": "HEUR-{NNN}",
      "type": "principle|anti_pattern|sequence|methodology|comparison",
      "content": "verbatim statement or observed pattern",
      "evidence_type": "visual|verbal|both",
      "timestamp": "MM:SS"
    }
  ],
  "summary": {
    "total_segments": 0,
    "by_category": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0},
    "by_evidence_type": {"visual": 0, "verbal": 0, "both": 0},
    "truth_candidates": 0,
    "divergences": 0,
    "unique_identifiers": 0,
    "relationships_count": 0,
    "heuristics_count": 0
  }
}

WRITE to: /processing/visual/{SOURCE_ID}-visual.json

LOG: "Visual extraction complete: {total_segments} segments, {truth_candidates} TRUTH candidates, {divergences} divergences"
```

### Step 6: Feed into JARVIS Phase 4

```
The visual extraction output is ADDITIONAL input for Phase 4 insight extraction.

CONVERT visual segments to Phase 4 compatible chunks:

FOR each segment in VISUAL_SEGMENTS:
  CREATE chunk:
    {
      "id_chunk": "vchunk_{SOURCE_ID}_{INDEX}",
      "texto": segment.content,
      "pessoas": [SOURCE_PERSON] if SOURCE_PERSON else [],
      "temas": [map_category_to_theme(segment.category)],
      "meta": {
        "scope": "company",
        "corpus": SOURCE_PERSON or "unknown",
        "source_type": "video_visual",
        "source_id": SOURCE_ID,
        "evidence_type": segment.evidence_type,
        "visual_category": segment.category,
        "timestamp": segment.timestamp
      }
    }

CATEGORY TO THEME MAPPING:
  A -> "Application Structure"
  B -> "Form Fields & Data Entry"
  C -> "Workflow States"
  D -> "Automations & Integrations"
  E -> "Views & Visualization"
  F -> "Relationships & Navigation"
  G -> "Usage Patterns"
  H -> "Identifiers & Data"
  I -> "Templates & Content"

APPEND visual chunks to CHUNKS_STATE
WRITE /processing/chunks/CHUNKS-STATE.json

LOG: "Visual chunks merged into CHUNKS-STATE: +{N} chunks with evidence_type markers"
```

### Step 7: Update Insight State with Visual Evidence

```
FOR each insight generated from visual segments:
  ADD field: "evidence_type": segment.evidence_type
  ADD field: "visual_category": segment.category

  IF segment.evidence_type == "both":
    SET confidence: "HIGH"
    SET truth_candidate: true

  IF segment.type == "divergencia":
    SET status: "contradiction"
    APPEND to change_log: {
      "entity": "visual_divergence",
      "key": segment.content,
      "chunks": [segment.chunk_id],
      "change": "contradiction",
      "note": "Visual/verbal divergence detected at {timestamp}"
    }

WRITE /processing/insights/INSIGHTS-STATE.json

LOG: "Insights updated with {N} visual-evidence entries"
```

### Step 8: Generate Processing Report

```
DISPLAY summary:

  ================================================================
  VISUAL EXTRACTION COMPLETE
  ================================================================
  Source:           {SOURCE_PERSON} - {title}
  Source ID:        {SOURCE_ID}
  Duration:         {duration}
  ================================================================
  Total Segments:   {total_segments}
  By Evidence:      VISUAL={visual} | VERBAL={verbal} | BOTH={both}
  TRUTH Candidates: {truth_candidates}
  Divergences:      {divergences}
  ================================================================
  Categories:
    A (Structure):      {count_A}
    B (Fields):         {count_B}
    C (Workflows):      {count_C}
    D (Automations):    {count_D}
    E (Views):          {count_E}
    F (Relationships):  {count_F}
    G (Patterns):       {count_G}
    H (Identifiers):    {count_H}
    I (Templates):      {count_I}
  ================================================================
  Relationships:    {relationships_count}
  Heuristics:       {heuristics_count}
  ================================================================
  Output:           processing/visual/{SOURCE_ID}-visual.json
  Chunks Added:     processing/chunks/CHUNKS-STATE.json (+{N})
  Insights Updated: processing/insights/INSIGHTS-STATE.json (+{N})
  ================================================================
```

---

## Integration with JARVIS Pipeline

This command runs INDEPENDENTLY of `/process-jarvis`. It does NOT replace Phase 4 -- it EXTENDS it.

**Two valid workflows:**

1. **Visual-first:** Run `/visual-extract` on video transcript, THEN run `/process-jarvis` on same file. Phase 4 will find the visual chunks already in CHUNKS-STATE and incorporate them.

2. **Parallel:** Run `/process-jarvis` for audio/text processing AND `/visual-extract` for visual processing. Both write to the same state files (CHUNKS-STATE, INSIGHTS-STATE) with different evidence_type markers.

**Key distinction:**
- `/process-jarvis` processes what was SAID (verbal evidence)
- `/visual-extract` processes what was SHOWN (visual evidence) and captures BOTH when screen and speech align

---

## Error Handling

| Error | Action |
|-------|--------|
| File not found | EXIT with FILE_NOT_FOUND |
| Unsupported format | EXIT with UNSUPPORTED_FORMAT |
| No visual markers in transcript | WARN: "No [SCREEN]/[TELA] markers found. Processing as text-only visual analysis." |
| Whisper not installed | `pip install openai-whisper` |
| ffmpeg not available | Skip frame extraction, process audio only |
| Empty transcript | EXIT with EMPTY_CONTENT |

---

## Example Usage

```
# Process a transcript with visual descriptions
/visual-extract inbox/JOHN DOE/DEMOS/crm-pipeline-demo.txt --person "John Doe" --type demo

# Process a raw video file
/visual-extract inbox/recordings/platform-walkthrough.mp4 --person "Jane Smith" --type screencast

# Process pre-structured visual JSON
/visual-extract processing/visual/manual-extraction.json

# Process without specifying person (will attempt to extract from path)
/visual-extract inbox/TUTORIALS/saas-dashboard-setup.txt --type tutorial
```
