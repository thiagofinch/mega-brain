# Slack Connector — Specification

> **Path:** `workspace/tools/SLACK-CONNECTOR.md`
> **PRD Reference:** Section 4.2
> **Status:** PLANNED

---

## Purpose

Absorb Slack messages into `workspace/meetings/` or relevant area directory, classified by channel and area.

## Options

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A (preferred)** | Slack MCP server | Native agent integration, real-time | Requires Slack API token |
| **B (fallback)** | N8N webhook export | Periodic batch, simpler setup | Delay, no real-time |

## Implementation Plan

1. Register Slack app with `channels:history` + `channels:read` scopes
2. Add `SLACK_BOT_TOKEN` to `.env`
3. Configure MCP server in `.mcp.json` or use n8n webhook
4. Messages classified: channel → company area → date
5. Output: `workspace/meetings/{area}/{date}/slack-{channel}.md`

## Data Flow

```
Slack API → MCP/N8N → workspace/inbox/slack/ → bucket_processor → workspace/meetings/
```

## Dependencies

- Slack Bot Token (OAuth)
- Channel mapping: which Slack channel maps to which company area
