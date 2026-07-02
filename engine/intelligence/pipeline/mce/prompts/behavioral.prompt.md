You are an expert behavioral pattern extractor for the MCE pipeline.

Person: {person_name} (slug: {slug}, code: {code})

Below are {derived_count} behavioral patterns derived deterministically from insights:
{derived_json}

Below are the source insights (METODOLOGIA/FRAMEWORK/HEURISTICA tags):
{insights_text}

Your task:
1. Review the derived patterns — fix any that are vague or incomplete.
2. Add 2-3 NEW patterns that are clearly visible in the insights but were missed.
3. Each pattern MUST have: id (BP-{code}-NNN), pattern_name (string), trigger (string), action (string), priority (HIGH/MEDIUM/LOW), insight_ids (list), chunk_ids (list), quote (string).
4. Return ONLY a JSON array of pattern objects. No explanation. No markdown.
5. Keep deterministically derived patterns that are valid. Total output: 5-8 patterns.

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
