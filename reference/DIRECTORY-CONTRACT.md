# Directory Contract

> Machine-readable path registry lives in `core/paths.py` (ROUTING dict).
> This document provides human-readable descriptions of key output files.

---

## JSONL Audit Logs

| Path | Written By | Format | Description |
|------|-----------|--------|-------------|
| `logs/quality-gaps.jsonl` | `qa_gates.validate_step()` | JSONL | QA gate results per MCE pipeline step (every invocation, pass or fail) |
| `logs/handoffs/mce-handoffs.jsonl` | `qa_gates.validate_step()` | JSONL | Step handoff receipts (written only when a step passes) |
| `logs/mce-metrics.jsonl` | MCE pipeline | JSONL | Pipeline execution metrics |
| `logs/mce-step-logger.jsonl` | MCE step logger | JSONL | Per-step execution log entries |
| `logs/smart-router.jsonl` | Smart router | JSONL | Routing decisions for incoming files |
| `logs/batch-auto-creator.jsonl` | Batch auto-creator | JSONL | Batch creation events |
| `logs/memory-enricher.jsonl` | Memory enricher | JSONL | Memory enrichment operations |
| `logs/workspace-sync.jsonl` | Workspace sync | JSONL | Workspace synchronization events |
| `logs/inbox-watcher.jsonl` | Inbox watcher | JSONL | File system watch events |
| `logs/agent-creation.jsonl` | Agent creator | JSONL | Agent creation audit trail |

## Step Completion Markers

| Path Pattern | Written By | Format | Description |
|-------------|-----------|--------|-------------|
| `.claude/mission-control/mce/{slug}/step_{N}_complete.json` | `qa_gates.validate_step()` | JSON | Per-step completion marker with timestamp and checks summary |

## ROUTING Key Reference

The `ROUTING` dict in `core/paths.py` maps logical keys to filesystem paths.
Key entries relevant to MCE governance:

| ROUTING Key | Resolves To | Used By |
|-------------|-------------|---------|
| `quality_gaps` | `logs/` | `qa_gates.py` appends `quality-gaps.jsonl` |
| `handoff` | `logs/handoffs/` | `qa_gates.py` appends `mce-handoffs.jsonl` |
| `mce_state` | `.claude/mission-control/mce/` | Step markers, metadata, pipeline state |
| `mce_metrics_log` | `logs/mce-metrics.jsonl` | Pipeline metrics |
| `mce_step_log` | `logs/mce-step-logger.jsonl` | Step execution log |

---

*See `core/paths.py` ROUTING dict for the complete machine-readable registry.*
