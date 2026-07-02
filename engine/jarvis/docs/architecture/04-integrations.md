# Mega Brain - Integration Architecture

## Integration Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEGA BRAIN INTEGRATIONS                          │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌───────────────┐
                              │  MEGA BRAIN   │
                              └───────┬───────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
    │   YouTube     │        │  AssemblyAI   │        │  Filesystem   │
    │ Transcript API│        │     API       │        │     MCP       │
    └───────────────┘        └───────────────┘        └───────────────┘
```

---

## API Integrations

### 1. YouTube Transcript API

**Purpose:** Fetch transcripts from YouTube videos without downloading the video

**Package:** `youtube-transcript-api`

**Version:** 1.2.3+

| Property | Value |
|----------|-------|
| **Protocol** | HTTPS |
| **Auth** | None required |
| **Rate Limit** | Fair use (no official limit) |
| **Data Format** | JSON array |

**Usage:**
```python
from youtube_transcript_api import YouTubeTranscriptApi

# Initialize (new API in v1.2.3+)
api = YouTubeTranscriptApi()

# Fetch transcript
transcript = api.fetch("VIDEO_ID")

# Response format
[
    {"text": "Hello everyone", "start": 0.0, "duration": 2.5},
    {"text": "Today we're going to talk about", "start": 2.5, "duration": 3.0},
    ...
]
```

**Error Handling:**
| Error | Cause | Action |
|-------|-------|--------|
| `TranscriptsDisabled` | Video has no captions | Use AssemblyAI |
| `NoTranscriptFound` | Captions not in target language | Try auto-generated |
| `VideoUnavailable` | Private or deleted video | Inform user |

---

### 2. AssemblyAI API

**Purpose:** Transcribe local audio/video files with advanced features

**Package:** `assemblyai`

| Property | Value |
|----------|-------|
| **Protocol** | HTTPS REST |
| **Auth** | API Key (header) |
| **Rate Limit** | Based on plan |
| **Data Format** | JSON |

**Configuration:**
```python
import assemblyai as aai

# Set API key
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Configure transcription
config = aai.TranscriptionConfig(
    language_code="en",
    punctuate=True,
    format_text=True,
    auto_chapters=True,
    speaker_labels=True,
    entity_detection=True,
)

# Transcribe
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(file_path, config=config)
```

**Features Used:**
| Feature | Description | Use Case |
|---------|-------------|----------|
| `punctuate` | Add punctuation | Readability |
| `format_text` | Format output | Clean text |
| `auto_chapters` | Detect topics | Navigation |
| `speaker_labels` | Identify speakers | Multi-speaker content |
| `entity_detection` | Extract entities | Names, companies |

**Environment Variable:**
```bash
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here
```

---

## MCP Integrations

### Filesystem MCP

**Purpose:** Provide Claude Code access to local filesystem

**Package:** `@anthropic-ai/mcp-server-filesystem`

**Configuration (settings.local.json):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic-ai/mcp-server-filesystem",
        "/path/to/your/mega-brain"
      ],
      "env": {}
    }
  }
}
```

**Capabilities:**
- Read files within project directory
- Write files within project directory
- List directory contents
- File metadata access

**Security:**
- Scoped to project directory only
- No access outside defined path

---

## Hook Integrations

### PreToolUse Hooks

**WebSearch Enhancement:**
```json
{
  "matcher": "WebSearch",
  "hooks": [{
    "type": "command",
    "command": "echo 'Adding current year to search query if not present'"
  }]
}
```

### PostToolUse Hooks

**INBOX Monitoring:**
```json
{
  "matcher": "Write",
  "hooks": [{
    "type": "command",
    "command": "if [[ \"$TOOL_INPUT\" == *\"inbox\"* ]] && [[ \"$TOOL_INPUT\" == *\".txt\"* ]]; then echo '[INBOX] New transcript detected'; fi"
  }]
}
```

---

## Permission Configuration

### Allowed Operations

**Bash Commands:**
```json
[
  "Bash(mkdir:*)",
  "Bash(cp:*)",
  "Bash(mv:*)",
  "Bash(ls:*)",
  "Bash(python:*)",
  "Bash(python3:*)",
  "Bash(pip:*)",
  "Bash(npm:*)",
  "Bash(node:*)",
  "Bash(git:*)",
  "Bash(yt-dlp:*)"
]
```

**File Operations:**
```json
[
  "Read(*)",
  "Write(*)",
  "Edit(*)"
]
```

**Web Access:**
```json
[
  "WebFetch(domain:youtube.com)",
  "WebFetch(domain:www.youtube.com)",
  "WebFetch(domain:youtu.be)",
  "WebFetch(domain:api.assemblyai.com)",
  "WebSearch"
]
```

---

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `ASSEMBLYAI_API_KEY` | AssemblyAI authentication | For local transcription |
| `MEGA_BRAIN_ROOT` | Project root path | Optional (default) |
| `KNOWLEDGE_PATH` | Knowledge folder path | Optional (default) |
| `INBOX_PATH` | INBOX folder path | Optional (default) |

**Default Paths (settings.local.json):**
```json
{
  "env": {
    "MEGA_BRAIN_ROOT": "/path/to/your/mega-brain",
    "KNOWLEDGE_PATH": "/path/to/your/mega-brain/knowledge",
    "INBOX_PATH": "/path/to/your/mega-brain/inbox"
  }
}
```

---

## Integration Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY GRAPH                                 │
└─────────────────────────────────────────────────────────────────────────┘

  Python Packages              Node Packages              System
  ═══════════════              ═════════════              ══════

  youtube-transcript-api       @anthropic-ai/             Claude Code
        │                      mcp-server-filesystem           │
        │                            │                         │
        ▼                            ▼                         ▼
  assemblyai                    npx (npm)               Bash shell
        │                            │                         │
        └────────────────────────────┴─────────────────────────┘
                                     │
                               MEGA BRAIN
```

---

## Future Integration Opportunities

| Integration | Purpose | Priority |
|-------------|---------|----------|
| **Notion API** | Export knowledge to Notion | Medium |
| **Obsidian** | Sync with Obsidian vault | Medium |
| **Whisper API** | Alternative transcription | Low |
| **Deepgram** | Alternative transcription | Low |
| **PostgreSQL MCP** | Structured knowledge storage | Low |
