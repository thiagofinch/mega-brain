You are a Sage-class extractor analyzing transcript chunks to produce STRUCTURED, ACTIONABLE insights about {person_name}.

For EACH chunk below, extract 0 to 3 insights. Each insight must include:
  - id: short id (e.g. "INS-{tag_code}-001", "INS-{tag_code}-002" ...)
  - insight: a clear, actionable sentence in the same language as the chunk (NOT a summary)
  - quote: a verbatim quote from the chunk that supports the insight
  - chunks: array of chunk ids (the source chunk's id_chunk goes here)
  - tag: ONE of [FILOSOFIA], [MODELO-MENTAL], [HEURISTICA], [FRAMEWORK], [METODOLOGIA]
  - category: ONE of [vendas, pricing, hiring, nepq, outbound, metricas, cultura, gestao, fechamento, scaling, paid-media, customer-retention, ai-systems, none]
  - priority: HIGH | MEDIUM | LOW
  - confidence: HIGH | MEDIUM | LOW

DNA tag guide:
  [FILOSOFIA]    -- a belief, worldview, axiom ("X is the foundation of Y")
  [MODELO-MENTAL] -- a way of thinking, conceptual lens ("the N types of X")
  [HEURISTICA]   -- a practical rule, decision shortcut, or threshold.
                    MCE-13.14: Tag with ":quantitative" when the heuristic contains
                    a number, metric, ratio, timeframe, or measurable threshold.
                    Examples: "if show-rate < 50%, fix the confirmation sequence" → :quantitative
                              "close deals in 7 days" → :quantitative
                              "hire slowly, fire fast" → (no number, standard tag)
                    Full tag format: [HEURISTICA:quantitative] when numeric signal present.
  [FRAMEWORK]    -- MCE-13.15: Accept ANY reusable approach with a recognisable name,
                    not only formal named systems. Criteria (one is sufficient):
                      a) Has a proper name used by the person ("The 3-Step Qualification", "my method")
                      b) Has identifiable phases/components that work together
                      c) Is presented as something others can apply ("you do X, then Y")
                    Do NOT require academic/published frameworks. Informal working frameworks
                    ("my approach to objection handling: acknowledge → reframe → proof") qualify.
                    Target: extract ≥3 frameworks per dense content source.
  [METODOLOGIA]  -- a step-by-step sequence ("Step 1: ..., Step 2: ...")

Category guide (choose the BEST match; use "none" when genuinely cross-cutting):
  vendas          -- sales process, scripts, conversion, qualification, follow-up
  pricing         -- price strategy, anchoring, value-based pricing, discounts
  hiring          -- recruitment, selection criteria, onboarding, talent acquisition
  nepq            -- neuro-emotional persuasion questions, NEPQ methodology
  outbound        -- SDR, cold outreach, prospecting, pipeline generation
  metricas        -- KPIs, metrics, tracking, dashboards, show-rates
  cultura         -- team culture, gamification, rituals, values, identity
  gestao          -- management, operations, leadership, decision-making, accountability
  fechamento      -- closing techniques, objection handling, final commitment
  scaling         -- business systems, growth operations, capacity, leverage
  paid-media      -- paid advertising, traffic, funnels, ROAS, creative production
  customer-retention -- churn, LTV, upsell, retention, customer success
  ai-systems      -- AI tools, automation, agentic systems, AI-augmented ops
  none            -- genuinely cross-cutting; use as last resort

Output ONLY valid JSON in this exact shape (no prose, no markdown fences):
{{
  "insights": [
    {{
      "id": "INS-{tag_code}-001",
      "insight": "...",
      "quote": "...",
      "chunks": ["chunk_N"],
      "tag": "[HEURISTICA]",
      "category": "vendas",
      "priority": "HIGH",
      "confidence": "HIGH"
    }}
  ]
}}

If no high-quality insights are extractable, return `{{"insights": []}}`.

Chunks ({chunk_count}):
{chunks_block}

## Classification Pressure (added 2026-05-22)

When extracting observations, attempt L1-L10 DNA layer classification for every observation. Use the schema's `unmapped_observations[]` field ONLY after explicitly exhausting all 10 layers and concluding the observation is genuinely cross-cutting or layer-novel. The escape hatch is for honest signal capture, not for lazy routing.
