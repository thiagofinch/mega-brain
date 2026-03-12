# Mega Brain - Data Flow Architecture

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW OVERVIEW                             │
└─────────────────────────────────────────────────────────────────────────┘

 EXTERNAL SOURCES                    PROCESSING                    OUTPUT
 ═══════════════                    ══════════                    ══════

 ┌─────────────┐                                              ┌──────────┐
 │   YouTube   │──┐                                           │ 01-time  │
 │    Video    │  │                                           ├──────────┤
 └─────────────┘  │   ┌──────────┐   ┌──────────────────┐    │ 02-sales │
                  ├──▶│ inbox │──▶│ Knowledge        │───▶├──────────┤
 ┌─────────────┐  │   │          │   │ Extraction       │    │ 03-hire  │
 │ Local Video │──┘   └──────────┘   │ Pipeline         │    ├──────────┤
 │   (.mp4)    │                     └──────────────────┘    │   ...    │
 └─────────────┘                                              └──────────┘
```

---

## Processing Pipelines

### Pipeline 1: YouTube Video Processing

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ YouTube URL  │───▶│ Extract      │───▶│ Fetch        │───▶│ Save to      │
│              │    │ Video ID     │    │ Transcript   │    │ inbox     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                    youtube-transcript-api
                                              │
                                    ┌─────────▼─────────┐
                                    │ Returns: list of  │
                                    │ {text, start,     │
                                    │  duration}        │
                                    └───────────────────┘
```

**Data Transformation:**
```python
# Input
url = "https://youtube.com/watch?v=VIDEO_ID"

# Processing
video_id = extract_video_id(url)  # "VIDEO_ID"
transcript = api.fetch(video_id)   # [{text: "...", start: 0.0}, ...]
text = " ".join([t['text'] for t in transcript])

# Output
# inbox/Video Title.txt (plain text, UTF-8)
```

---

### Pipeline 2: Local File Transcription

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Local File   │───▶│ Upload to    │───▶│ AssemblyAI   │───▶│ Save to      │
│ (.mp4/.mp3)  │    │ AssemblyAI   │    │ Transcribe   │    │ inbox     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                    AssemblyAI API
                                              │
                                    ┌─────────▼─────────┐
                                    │ Returns: text,    │
                                    │ chapters,         │
                                    │ speakers,         │
                                    │ entities          │
                                    └───────────────────┘
```

**Configuration:**
```python
config = aai.TranscriptionConfig(
    language_code="en",
    punctuate=True,
    format_text=True,
    auto_chapters=True,
    speaker_labels=True,
    entity_detection=True,
)
```

---

### Pipeline 3: Knowledge Extraction

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Transcript   │───▶│ Theme        │───▶│ AI Agent     │───▶│ Knowledge    │
│ (.txt)       │    │ Detection    │    │ Extraction   │    │ Files        │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
        │                  │                   │                   │
        ▼                  ▼                   ▼                   ▼
   Plain text        Keyword         b2b-sales-expert      Markdown files
   78,000+ chars     matching        agent analysis        in KNOWLEDGE/
```

**Theme Detection Keywords:**
```python
THEMES = {
    "01-estrutura-time": ["team", "bdr", "sds", "bc", "christmas tree"],
    "02-processo-vendas": ["sales", "closer", "closing", "objection"],
    "03-contratacao": ["hiring", "recruit", "farm system"],
    "04-comissionamento": ["compensation", "commission", "ote"],
    "05-metricas": ["kpi", "metric", "cac", "ltv", "conversion"],
    ...
}
```

---

## Data Formats

### Input Formats

| Format | Extension | Source | Handler |
|--------|-----------|--------|---------|
| YouTube URL | - | Web | youtube-transcript-api |
| Video | .mp4 | Local | AssemblyAI |
| Audio | .mp3, .wav, .m4a | Local | AssemblyAI |
| Transcript | .txt | INBOX | Direct read |
| Document | .pdf, .docx | Local | Manual |

### Output Format

**Knowledge File Template:**
```markdown
# [Topic Title]

## Resumo Executivo
[1-2 sentence summary]

---

## Visão [Source Name]

### Contexto
[Industry, ticket size, team stage]

### [Subtopic 1]
- Point 1 with specific numbers
- Point 2 with exact metrics
- Actionable recommendation

### Fonte
- Video: [Title]
- Fonte: [Speaker/Company]
- Confiabilidade: Alta/Média
```

---

## Data Transformation Rules

### 1. Number Preservation
```
Input:  "We had a 25% close rate"
Output: "Close rate: 25%" (exact, never rounded)
```

### 2. Context Annotation
```
Input:  "Our BDRs make 100 calls per day"
Output: "BDR calls: 100/dia (contexto: high-ticket B2B, $20k+ ticket)"
```

### 3. Source Attribution
```
Every extracted insight MUST include:
- Source video/document name
- Speaker/author
- Reliability rating
```

### 4. Language Handling
```
Input:  English transcripts
Output: Portuguese (BR) knowledge files
        (Technical terms may remain in English)
```

---

## Data Volume Estimates

| Stage | Typical Size |
|-------|--------------|
| YouTube transcript | 15,000 - 100,000 chars |
| Local video (1 hour) | 10,000 - 50,000 words |
| Knowledge file | 500 - 2,000 words |
| Themes per source | 2-5 themes |

---

## State Transitions

```
┌────────────────┐
│   UNPROCESSED  │ ◀─── File dropped in inbox
└───────┬────────┘
        │ /scan-inbox or /process-video
        ▼
┌────────────────┐
│  TRANSCRIBED   │ ◀─── Transcript created in inbox
└───────┬────────┘
        │ /extract-knowledge
        ▼
┌────────────────┐
│   EXTRACTED    │ ◀─── Knowledge files in KNOWLEDGE/
└───────┬────────┘
        │ Manual review (optional)
        ▼
┌────────────────┐
│   VALIDATED    │ ◀─── Ready for use in playbook
└────────────────┘
```

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No transcript available | YouTube video without captions | Use local transcription |
| API rate limit | Too many requests | Wait and retry |
| Theme not detected | Content doesn't match keywords | Put in 99-secundario |
| File too large | Video > 1GB | Split or compress |
