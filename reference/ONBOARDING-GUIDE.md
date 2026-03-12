# Mega Brain 3D — Onboarding Guide

> **Version:** 1.0.0 | **Date:** 2026-03-07
> **paths.py:** `ROUTING["onboarding_guide"]`
> **Audience:** Founder setting up the 3 knowledge dimensions from scratch

---

## What Is Mega Brain 3D?

Three separate knowledge layers that feed your AI council:

| Bucket | What Goes In | Where It Lives | Who Sees It |
|--------|-------------|---------------|-------------|
| **External** (experts) | Courses, frameworks, expert content | `knowledge/external/` | Everyone (L1/L2) |
| **Workspace** (company) | Org data, finance, meetings, tools | `workspace/` | Business mode (L2) |
| **Personal** (you) | Emails, calls, journal, reflections | `knowledge/personal/` | Only you (L3) |

---

## Step 1: External Bucket (already populated)

This bucket contains expert knowledge from mind clones (Hormozi, Cole Gordon, etc.). It's already set up if you've been using Mega Brain.

**Check status:**
```
python3 -c "from core.intelligence.pipeline.bucket_processor import bucket_status; s=bucket_status(); print(f'External: {s[\"external\"][\"processed_files\"]} files')"
```

**Add new expert material:**
```
/ingest [path-to-file-or-URL]
```

---

## Step 2: Workspace Bucket (start here)

This is your company's brain. Start with the highest-impact data first.

### Priority 1: Financial Data
Drop your DRE, P&L, or KPI spreadsheet into `workspace/inbox/financial/`:
```
/ingest-empresa ./your-dre-2026.csv --type METRICS
```
Now the council can cite real numbers when advising.

### Priority 2: Team Structure
Drop job descriptions, org charts, or role documents:
```
/ingest-empresa ./organograma.pdf --type ORG
/ingest-empresa ./jd-closer.md --type JD
```

### Priority 3: Meeting Recordings
If using Read.ai or another recording tool:
```
/ingest-empresa ./meeting-transcript.txt
```
The system auto-classifies by content.

### Priority 4: Tools & Processes
Document which tools your company uses. The system detects mentions automatically and logs them in `workspace/DETECTED-TOOLS-LOG.md`.

---

## Step 3: Personal Bucket (optional, L3 only)

This data NEVER leaves your machine. Not tracked by git, not indexed in shared RAG.

### Emails
```
/ingest-pessoal ./email-export.mbox
```

### Voice Memos / Calls
```
/ingest-pessoal ./call-recording.mp3
```

### Journal / Reflections
Create markdown files directly:
```
Write to knowledge/personal/cognitive/2026-03-reflection.md
```

---

## Step 4: Use the Council with 3D Context

Once you have data in the buckets, the council debates using all three perspectives:

```
/conclave --mode full-3d "Should we hire a new closer?"
```

Modes:
- `expert-only` — only expert knowledge (default)
- `business` — experts + your company data
- `full-3d` — everything including personal context
- `company-only` — just your company data
- `personal` — just your personal data

---

## What Happens Automatically

1. Files dropped in any `inbox/` are auto-classified by `bucket_processor.py`
2. The council signals which buckets it consulted (and which are missing)
3. `MISSING-CONTEXT-LOG.md` tracks what data would improve responses
4. `DETECTED-TOOLS-LOG.md` auto-updates when you mention tools

---

## Directory Quick Reference

```
workspace/           Your company
  inbox/               Drop files here
  org/                 Organization structure
  team/                People, JDs, roles
  finance/             Numbers, KPIs, DRE
  meetings/            Meeting transcripts
  tools/               Tool configs, connector specs
  automations/         N8N, webhooks

knowledge/external/  Expert minds
  sources/             Raw expert content
  dossiers/            Consolidated dossiers
  playbooks/           Actionable playbooks
  dna/                 DNA schemas (5 layers)

knowledge/personal/  Your private data (L3)
  email/               Email digests
  messages/            WhatsApp, Telegram
  calls/               Call transcripts
  cognitive/           Journal, reflections
```
