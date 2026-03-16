# Meeting Recorder — Tool Decision

> **Path:** `workspace/tools/MEETING-RECORDER-DECISION.md`
> **PRD Reference:** Section 4.3
> **Status:** PENDING DECISION

---

## Candidates

| Tool | Transcription | Auto-categorize | API/Export | Cost | Integration |
|------|--------------|-----------------|------------|------|-------------|
| Read.ai | Yes (high quality) | By meeting type | API + CSV export | Free tier available | Already in pipeline |
| Fireflies.ai | Yes | By topic | REST API | $10/mo | Good API |
| Otter.ai | Yes | Basic | Limited API | $8.33/mo | Weak API |
| Zoom native | Yes | No | Webhook | Included | Direct |
| Google Meet | Yes | No | Drive export | Included | Via Drive MCP |

## Evaluation Criteria

1. **Transcription quality** — accuracy for PT-BR + EN mixed calls
2. **Auto-categorization** — tag by company area automatically
3. **API access** — programmatic export to `knowledge/business/inbox/meetings/`
4. **Cost** — monthly cost at scale
5. **Integration path** — how quickly can we connect to Mega Brain

## Current Recommendation

**Read.ai** — already integrated via `read-ai-harvester` skill. Transcriptions can be harvested directly into `knowledge/business/inbox/meetings/` using the existing pipeline.

## Data Flow

```
Meeting Tool → Export/API → knowledge/business/inbox/meetings/ → bucket_processor → workspace/meetings/{area}/
```

## Decision

- [ ] Tool selected: ___________
- [ ] API key configured in `.env`
- [ ] Integration tested
- [ ] First batch of meetings processed
