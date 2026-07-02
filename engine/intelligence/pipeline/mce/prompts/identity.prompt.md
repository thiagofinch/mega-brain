You are an expert identity layer extractor for the MCE pipeline.

Person: {person_name} (slug: {slug}, code: {code})

Source insights (FILOSOFIA/MODELO-MENTAL tags):
{insights_text}

Derived obsessions so far:
{derived_obsessions_json}

Your task — return a JSON object with exactly 3 keys:
{{
  "values_hierarchy": [
    {{"id": "VAL-{code}-001", "value": "string", "rank": 1, "tier": 1, "evidence": "string", "chunk_ids": ["chunk_X"], "insight_ids": ["INS-X"], "quote": "string"}}
    // ... 3-5 total values
  ],
  "obsessions": [
    {{"id": "OBS-{code}-001", "obsession": "string", "frequency": 5, "examples": ["string"], "chunk_ids": ["chunk_X"], "insight_ids": ["INS-X"], "quote": "string"}}
    // ... 3-5 total obsessions
  ],
  "paradoxes": [
    {{"id": "PAR-{code}-001", "tension_a": "string", "tension_b": "string", "resolution": "string", "chunk_ids": ["chunk_X"], "insight_ids": ["INS-X"], "quote": "string"}}
    // ... 2-4 total paradoxes
  ]
}}

Rules:
- Values must be derived from the FILOSOFIA/MODELO-MENTAL insights above.
- Obsessions = recurring themes that drive ALL decisions. Check the derived obsessions + insights.
- Paradoxes = productive contradictions (things that seem to conflict but both are true for this person).
- Use chunk_ids from the insights list above where possible (e.g. ["chunk_2", "chunk_4"]).
- Return ONLY valid JSON. No markdown. No explanation.

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
