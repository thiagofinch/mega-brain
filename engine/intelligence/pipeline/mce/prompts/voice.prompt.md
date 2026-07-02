You are an expert Voice DNA extractor for the MCE pipeline.

Person: {person_name} (slug: {slug}, code: {code})

Sample quotes from their content:
{quotes_text}

Derived signature phrase seeds:
{phrases_json}

Your task — return a JSON object for this person's Voice DNA with:
{{
  "tone_profile": {{
    "certainty": {{"score": 7.5, "justificativa": "string", "chunk_ids": ["chunk_2"]}},
    "authority": {{"score": 8.0, "justificativa": "string", "chunk_ids": ["chunk_4"]}},
    "warmth": {{"score": 6.5, "justificativa": "string", "chunk_ids": ["chunk_2"]}},
    "directness": {{"score": 7.0, "justificativa": "string", "chunk_ids": ["chunk_4"]}},
    "teaching_focus": {{"score": 8.5, "justificativa": "string", "chunk_ids": ["chunk_2"]}},
    "confidence": {{"score": 7.5, "justificativa": "string", "chunk_ids": ["chunk_4"]}}
  }},
  "signature_phrases": [
    {{"id": "VP-{code}-001", "phrase": "string", "context": "string", "chunk_ids": ["chunk_X"], "poder": 8}}
    // ... 3-5 phrases
  ],
  "behavioral_states": [
    {{"nome": "Teaching Mode", "trigger": "string", "tom": "string", "sinais": ["string1", "string2"], "chunk_ids": ["chunk_X"]}}
    // ... MCE-13.19: extract 6-8 states minimum (not just 3-4).
    // Suggested state vocabulary (use what is actually evidenced in the content):
    //   Teaching     — explaining, breaking down, educating; tone: methodical, patient
    //   Analytical   — dissecting data, metrics, patterns; tone: precise, measured
    //   Engagement   — rallying, energising audience; tone: high-energy, motivational
    //   Visionary    — painting future possibilities; tone: expansive, confident
    //   Skeptical    — challenging assumptions, debunking; tone: sharp, provocative
    //   Empathic     — acknowledging pain, validating; tone: warm, understanding
    //   Authoritative — declaring non-negotiables, setting standards; tone: direct, commanding
    //   Coaching     — guiding through a process, asking questions; tone: Socratic, encouraging
    // Only include states that have concrete evidence in the chunks provided.
    // Do NOT invent states without chunk support.
  ],
  "communication_patterns": {{
    "opening_hooks": {{"padrao": "string", "exemplos": ["quote1"], "chunk_ids": ["chunk_X"]}},
    "story_structure": {{"padrao": "string", "descricao": "string", "chunk_ids": ["chunk_X"]}},
    "closing_signatures": {{"padrao": "string", "exemplos": ["quote1"], "chunk_ids": ["chunk_X"]}}
  }}
}}

Rules:
- Base ALL claims on the actual quotes provided above.
- chunk_ids should reference the chunk IDs from the quotes (e.g. chunk_2, chunk_4, chunk_6).
- Signature phrases MUST be actual phrases from the quotes, not invented.
- Return ONLY valid JSON. No markdown. No explanation.

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
