> **Auto-Trigger:** When user mentions Read.ai, meeting transcripts, harvest meetings, or bulk download meetings
> **Keywords:** "read.ai", "read ai", "harvest meetings", "meeting transcripts", "transcript harvester", "download meetings"
> **Prioridade:** MEDIA
> **Tools:** Bash, Read, Write

# Read.ai Transcript Harvester

Bulk-downloads all meeting transcripts from the Read.ai API, classifies them into company vs. personal buckets, and stages them for Pipeline Jarvis ingestion.

## When NOT to Activate

- User is asking about reading files (not Read.ai the product)
- User is discussing calendar events without mentioning transcripts
- User is processing already-downloaded transcripts (use `/process-inbox` instead)

## Prerequisites

Set these environment variables in `.env` before running:

```
READ_AI_EMAIL=your-email@example.com
READ_AI_PASSWORD=your-password
READ_AI_API_URL=https://api.read.ai/mcp
READ_AI_COMPANY_NAME=Your Company
READ_AI_COMPANY_DOMAINS=company.com,company.com.br
READ_AI_COMPANY_KEYWORDS=company,company name
READ_AI_TAG_PREFIX=MEET
READ_AI_INGESTION_BATCH=10
READ_AI_GARDENER_TRIGGER=5
READ_AI_PAGE_SIZE=50
```

## Commands

### Start Harvest (YOLO Mode)

```bash
python3 -m core.intelligence.pipeline.read_ai_harvester run
```

Autonomous loop: paginate API → download → classify → route → checkpoint. Runs until all meetings are processed or stop signal is received.

### Resume After Interruption

```bash
python3 -m core.intelligence.pipeline.read_ai_harvester resume
```

Loads last checkpoint and skips already-downloaded meetings.

### Graceful Stop

```bash
python3 -m core.intelligence.pipeline.read_ai_harvester stop
```

Creates stop signal file. Harvest finishes current download then stops.

### Check Status

```bash
python3 -m core.intelligence.pipeline.read_ai_harvester status
```

Shows progress: downloaded, empresa/pessoal counts, failures, gardener runs.

## Architecture

```
Read.ai API ─→ [HARVESTER] ─→ artifacts/read-ai-staging/
                                        │
                                   [ROUTER] scores meeting metadata
                                        │
                          ┌──────────────┴──────────────┐
                          ▼                              ▼
                inbox/empresa/MEETINGS/      inbox/PESSOAL/MEETINGS/
                                                        │
                                              [GARDENER] (every N)
                                              organizes into subfolders:
                                              COACHING/ NETWORKING/
                                              LEARNING/ SALES/ etc.
```

## Routing Logic

Meetings are scored based on metadata:

| Signal | Points |
|--------|--------|
| Organizer email matches company domain | +3 |
| Participant email matches company domain | +2 each |
| Title contains company keyword | +2 |
| Title/description has business keywords | +1 |

Score >= 3 → **empresa**, otherwise → **pessoal**.

## Transcript Output Format

```
═══════════════════════════════════════════════════
MEETING TRANSCRIPT
═══════════════════════════════════════════════════
Title: {title}
Date: {date}
Duration: {duration} minutes
Participants: {list}
Source: Read.ai | Meeting ID: {id}
═══════════════════════════════════════════════════

[00:00:00] Speaker Name:
Good morning everyone!

[00:00:15] Speaker 2:
Let's get started...
```

## File Tagging

Files are tagged sequentially: `[MEET-0001] Meeting Title.txt`

The tag counter persists across runs via the state file.

## State & Logs

| File | Location | Purpose |
|------|----------|---------|
| State | `.claude/mission-control/READ-AI-HARVEST-STATE.json` | Resume support, tag counter, processed IDs |
| Harvest log | `logs/read-ai-harvest/harvest.jsonl` | Download events, errors, triggers |
| Routing log | `logs/read-ai-harvest/routing.jsonl` | Classification decisions with scores |
| Gardener log | `logs/read-ai-harvest/gardener.jsonl` | File reorganization events |
| Stop signal | `.claude/mission-control/STOP-READ-AI-HARVEST` | Graceful shutdown trigger |

## Triggers

- **Gardener:** Runs automatically every N personal downloads (default: 5)
- **Ingestion:** Logs batch-ready event every N total downloads (default: 10). Run `/process-inbox` to trigger Pipeline Jarvis.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Auth fails (401) | Check READ_AI_EMAIL and READ_AI_PASSWORD in .env |
| Rate limited (429) | Harvester auto-retries with exponential backoff |
| Interrupted mid-run | Run `resume` to continue from checkpoint |
| Wrong classification | Check READ_AI_COMPANY_DOMAINS covers all your email domains |
| Need to re-run | Delete the state file and run again |

## Examples

```bash
# First run — full harvest
python3 -m core.intelligence.pipeline.read_ai_harvester run

# Check progress from another terminal
python3 -m core.intelligence.pipeline.read_ai_harvester status

# Stop gracefully
python3 -m core.intelligence.pipeline.read_ai_harvester stop

# Resume later
python3 -m core.intelligence.pipeline.read_ai_harvester resume
```
