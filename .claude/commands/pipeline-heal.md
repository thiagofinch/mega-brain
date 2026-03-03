---
description: "Detect and heal missed pipeline steps for a SOURCE_ID"
---

# /pipeline-heal

Detect and heal missed pipeline steps after source processing.

## Arguments

$ARGUMENTS — SOURCE_ID (e.g., TF001) or flags:
- `{SOURCE_ID}` — Check and heal a specific source
- `--all` — Check all known sources
- `--check-only` — Detection only, no healing

## Execution

1. **Run detection engine:**
   ```bash
   python3 core/intelligence/pipeline_heal.py --check {SOURCE_ID}
   ```

2. **Read the SKILL for heal instructions:**
   Read `.claude/skills/pipeline-heal/SKILL.md` for the full heal protocol.

3. **For each failed check:** Execute the corresponding heal action from the SKILL.

4. **Re-run detection** to confirm all healed.

5. **Show before/after comparison** with score change.

## Quick Reference

| Check    | What It Verifies                          |
|----------|-------------------------------------------|
| P2       | CHUNKS-STATE has source chunks            |
| P3       | CANONICAL-MAP has source entities         |
| P4       | INSIGHTS-STATE has source insights        |
| P5       | NARRATIVES-STATE has person narrative     |
| P6.2     | Person dossier exists                     |
| P6.3     | Theme dossiers reference source           |
| P6.6     | NAVIGATION-MAP.json updated               |
| P7.4     | Agent MEMORY.md has source_id             |
| P8.1.1   | RAG BM25 index is current                 |
| P8.1.2   | file-registry.json has entry              |
| P8.1.3   | Session state updated                     |
| P8.1.8   | DNA exists if density >= 3/5              |
| P8.1.9   | SOUL.md updated with source_id            |
| P8.3.5   | INBOX-REGISTRY entry exists               |
