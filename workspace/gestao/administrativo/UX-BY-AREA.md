# UX by Area — How Each Department Sends Data

> **Path:** `workspace/org/UX-BY-AREA.md`
> **paths.py:** `ROUTING["ux_by_area"]`

---

## How It Works

Each area of the company has a clear path to send context into the Mega Brain workspace bucket. No technical knowledge required — just drop files or use the designated command.

---

## Per-Area Data Flow

| Area | What to Send | Where It Goes | Command |
|------|-------------|---------------|---------|
| **Sales** | Call recordings, CRM exports, pipeline reports | `knowledge/business/inbox/calls/` | `/ingest-empresa --type METRICS` |
| **Finance** | DRE, P&L, cash flow, budget sheets | `knowledge/business/inbox/financial/` | `/ingest-empresa --type METRICS` |
| **Operations** | Process docs, SOPs, ritual descriptions | `knowledge/business/inbox/documents/` | `/ingest-empresa --type OPS` |
| **HR/Team** | Job descriptions, org chart, onboarding docs | `knowledge/business/inbox/documents/` | `/ingest-empresa --type JD` |
| **Marketing** | Campaign reports, creative briefs, KPIs | `knowledge/business/inbox/documents/` | `/ingest-empresa --type METRICS` |
| **Meetings** | Transcriptions, meeting notes, decisions | `knowledge/business/inbox/meetings/` | `/ingest-empresa --type OPS` |
| **Slack** | Channel exports, key discussions | `knowledge/business/inbox/slack/` | (future: Slack MCP connector) |

## After Ingestion

The `bucket_processor.py` auto-classifies and routes each file to the correct destination:

```
knowledge/business/inbox/{type}/file.txt
       |
       v
  bucket_processor.py (classifies by content patterns)
       |
       v
  workspace/{org|team|finance|meetings|automations|tools}/file.txt
```

## Quick Start for New Area

1. Drop files into `knowledge/business/inbox/` (any subfolder)
2. Run `/ingest-empresa` or wait for auto-processing
3. Files are classified and moved to the right `workspace/` subdir
4. Council agents can now access this data in `business` or `full-3d` mode
