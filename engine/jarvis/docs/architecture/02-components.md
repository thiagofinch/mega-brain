# Mega Brain - Component Architecture

## Component Overview (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            MEGA BRAIN                                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        .claude/ (Configuration Layer)            │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐  │   │
│  │  │  agents/  │  │ commands/ │  │  skills/  │  │  settings   │  │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────────────┐  │
│  │   inbox   │  │     scripts/     │  │       KNOWLEDGE/        │  │
│  │  (Input)     │──│   (Processing)   │──│       (Output)          │  │
│  └──────────────┘  └──────────────────┘  └─────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Components (.claude/)

### Agents

| Agent | File | Purpose |
|-------|------|---------|
| **b2b-sales-expert** | `agents/b2b-sales-expert.md` | Specialized agent for analyzing B2B sales content with domain expertise |

**Agent Capabilities:**
- Team structure analysis (Christmas Tree, Farm System)
- Sales process evaluation (CLOSER framework)
- Compensation plan validation
- Metric benchmarking
- Context-aware advice (ticket size, industry)

---

### Commands

| Command | File | Trigger | Description |
|---------|------|---------|-------------|
| `/process-video` | `commands/process-video.md` | URL or path | Process YouTube or local video |
| `/extract-knowledge` | `commands/extract-knowledge.md` | File path | Extract knowledge from transcript |
| `/scan-inbox` | `commands/scan-inbox.md` | None | Scan INBOX for pending files |
| `/documentation/create-architecture-documentation` | `commands/documentation/...` | None | Generate architecture docs |

**Command Flow:**
```
/scan-inbox → Lists pending files
       ↓
/process-video [URL] → Creates transcript
       ↓
/extract-knowledge [path] → Creates knowledge files
```

---

### Skills

| Skill | Directory | Capabilities |
|-------|-----------|--------------|
| **video-processing** | `skills/video-processing/` | YouTube transcript fetch, AssemblyAI integration, format handling |
| **knowledge-extraction** | `skills/knowledge-extraction/` | Theme detection, content classification, structured output |

**Skill Structure:**
```
skills/
├── video-processing/
│   └── SKILL.md          # Skill definition and capabilities
└── knowledge-extraction/
    └── SKILL.md          # Extraction rules and patterns
```

---

### Settings

**File:** `settings.local.json`

| Section | Purpose |
|---------|---------|
| `permissions.allow` | Allowed tools and domains |
| `permissions.deny` | Blocked operations |
| `hooks.PreToolUse` | Pre-execution triggers |
| `hooks.PostToolUse` | Post-execution triggers |
| `mcpServers` | MCP server configurations |
| `env` | Environment variables |

**Configured Permissions:**
- Bash operations: mkdir, cp, mv, ls, python, pip, npm, node, git, yt-dlp
- File operations: Read, Write, Edit
- Web access: youtube.com, youtu.be, api.assemblyai.com
- Web search enabled

**Configured Hooks:**
- `PreToolUse:WebSearch` - Adds current year to searches
- `PostToolUse:Write` - Detects new transcripts in INBOX

---

## Processing Components (scripts/)

### transcribe.py

**Purpose:** Transcribe local audio/video files using AssemblyAI API

**Dependencies:**
- `assemblyai` Python package
- `ASSEMBLYAI_API_KEY` environment variable

**Features:**
- Supports MP4, MP3, WAV, M4A formats
- Auto language detection
- Punctuation and formatting
- Auto chapters
- Speaker labels
- Entity detection

---

### auto_organize_inbox.py

**Purpose:** Scan INBOX folder and suggest actions for each file

**Features:**
- File type detection
- Theme keyword matching
- Word count for transcripts
- Action suggestions

**Output:**
```
MEGA BRAIN - INBOX SCANNER
============================================================
File: transcript.txt
  Type: transcript
  Words: 15,234
  Detected themes: 01-estrutura-time, 03-contratacao
  Action: Run /extract-knowledge inbox/transcript.txt
============================================================
```

---

## Data Components

### inbox (Input)

**Purpose:** Drop zone for unprocessed content

**Accepted Formats:**
| Type | Extensions |
|------|------------|
| Video | .mp4 |
| Audio | .mp3, .wav, .m4a |
| Transcript | .txt |
| Document | .pdf, .docx, .xlsx |

---

### KNOWLEDGE (Output)

**Purpose:** Organized knowledge base with themed folders

| Folder | Theme | Content Type |
|--------|-------|--------------|
| `01-estrutura-time/` | Team Structure | Org charts, roles, hierarchy |
| `02-processo-vendas/` | Sales Process | Closing, qualification, scripts |
| `03-contratacao/` | Hiring | Recruiting, interviews, onboarding |
| `04-comissionamento/` | Compensation | OTE, commissions, incentives |
| `05-metricas/` | Metrics | KPIs, benchmarks, conversion rates |
| `06-funil-aplicacao/` | Application Funnel | Lead qualification, pipeline |
| `07-pricing/` | Pricing | High-ticket strategies |
| `08-ferramentas/` | Tools | CRM, tech stack |
| `09-gestao/` | Management | Leadership, coaching |
| `99-secundario/` | Secondary | Other supporting topics |

**Current Knowledge Files (16):**
- 01-estrutura-time: 2 files
- 02-processo-vendas: 3 files
- 03-contratacao: 1 file
- 04-comissionamento: 1 file
- 05-metricas: 2 files
- 06-funil-aplicacao: 1 file
- 07-pricing: 1 file
- 08-ferramentas: 1 file
- 99-secundario: 4 files

---

## Component Dependencies

```
┌────────────────┐     ┌────────────────┐
│    Commands    │────▶│     Skills     │
└───────┬────────┘     └───────┬────────┘
        │                      │
        ▼                      ▼
┌────────────────┐     ┌────────────────┐
│    Agents      │     │    Scripts     │
└───────┬────────┘     └───────┬────────┘
        │                      │
        └──────────┬───────────┘
                   ▼
           ┌────────────────┐
           │   KNOWLEDGE    │
           └────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **AI Runtime** | Claude Code CLI |
| **Configuration** | JSON, Markdown |
| **Scripts** | Python 3.x |
| **APIs** | youtube-transcript-api, AssemblyAI |
| **MCP** | @anthropic-ai/mcp-server-filesystem |
