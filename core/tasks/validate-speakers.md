# QG-SPEAKER-001 — Validate Speaker Labels

**ID:** QG-SPEAKER-001
**Type:** Pre-validation gate
**Phase:** phase_0 (PRE_VALIDATION)
**Blocking:** true

## Purpose

Detect speaker labels in transcript before ingestion.
Blocks pipeline and presents options if labels are absent in multi-voice content.

## Detection Patterns

- `Nome Sobrenome: texto` (e.g., "Pedro Valerio Lopez: Então...")
- `[00:00] Nome:` (timestamp + name)
- `Speaker 1:` / `SPEAKER_00:` (auto-diarized)

## Execution

```bash
python3 core/intelligence/speakers/speaker_gate.py <file_path>
```

Exit codes:
- `0` — Labels detected OR user chose monologue/manual → continue
- `1` — User cancelled OR error → abort ingestion

## Options when no labels found

1. **Monologue** — Attribute entire transcript to declared source. Continue.
2. **Manual identification** — User provides participant names. System applies heuristic split.
3. **Cancel** — Abort ingestion. File stays in inbox.

## Integration

Called by `wf-ingest.yaml` phase_0 before DOWNLOAD.
Implemented in `core/intelligence/speakers/speaker_gate.py`.
