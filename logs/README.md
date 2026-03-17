# Logs

Logs de sessoes e processamento. Gerados automaticamente.

## Subpastas

- `sessions/start/` -- Session start hooks (JSON, auto-generated)
- `sessions/autosave/` -- Session snapshots from autosave V2 (MD)
- `sessions/reports/` -- MCE Session Reports (MD, concatenated)
- `mce/` -- Progressive MCE pipeline logs by person
- `batches/` -- Batch processing logs (legacy)
- `handoffs/` -- Session handoff files for context transfer
- `wave-mce/` -- Wave execution logs
- `archive/` -- Historical logs (batch-logs, audits, tags)

## JSONL Logs (root level)

| Log File | Source Hook | Content |
|----------|-----------|---------|
| `mce-step-logger.jsonl` | PostToolUse | Per-artifact MCE step metrics |
| `mce-orchestrate.jsonl` | Pipeline | Orchestration commands and state |
| `mce-metrics.jsonl` | Pipeline | Aggregated MCE metrics |
| `scope-classifier.jsonl` | Pipeline | Source classification decisions |
| `smart-router.jsonl` | Pipeline | Routing decisions |
| `pipeline-checkpoints.jsonl` | PostToolUse | Phase checkpoint saves |
| `memory-enricher.jsonl` | Pipeline | Memory enrichment operations |
| `agent-creation.jsonl` | PostToolUse | Agent file creation events |
| `cascading.jsonl` | Pipeline | Knowledge cascading events |
| `batch-auto-creator.jsonl` | Pipeline | Auto batch creation |
| `workspace-sync.jsonl` | Pipeline | Workspace sync operations |
| `actions.json` | UserPromptSubmit | Action tracking |
| `prompts.jsonl` | UserPromptSubmit | Prompt logging |
| `pipeline-guard.jsonl` | PreToolUse | Pipeline guard decisions |

Estes logs sao locais e nao sao rastreados pelo git.
