<!-- cmd_narrative — Narrative Metabolism (MCE-4.1)

NOTE: cmd_narrative itself performs no direct LLM calls. It uses narrative_merger
(stdlib + PyYAML only, zero LLM) to merge incoming narrative entries into
NARRATIVES-STATE.json. This file documents the merge logic for jarvis-chief
and serves as the canonical prompt stub for future LLM-assisted synthesis.

When LLM synthesis is added in a future story, the prompt below is the
recommended starting template. -->

# Narrative Merger — Merge Rules

The narrative merger applies deterministic rules to combine person narrative entries:

- Existing fields are preserved unless the incoming entry explicitly provides newer values.
- `last_updated` is always refreshed to current timestamp.
- `domain` defaults to "vendas" if not present in existing entry.
- Bucket validation enforces knowledge isolation (Art. XIII — cross-contamination blocked).
- Merge is idempotent: running twice produces identical output.

## Future LLM Synthesis Template (stub)

When LLM narrative synthesis is enabled, the following context will be injected:

```
Person: {person_name} (slug: {slug})
Existing narrative entry: {existing_entry_json}
New signals from latest ingestion: {incoming_signals}

Task: Synthesize the updated narrative entry incorporating the new signals.
Preserve existing validated claims. Mark new claims with confidence score.
Return ONLY valid JSON matching the NARRATIVES-STATE person_narrative schema.
```

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
