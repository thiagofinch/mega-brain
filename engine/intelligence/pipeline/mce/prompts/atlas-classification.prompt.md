# Atlas Classification Prompt — MCE-13.23
#
# This prompt is used by atlas_classifier.py when LLM-assisted classification
# is enabled (MCE_ATLAS_LLM=1). The heuristic path is the default; this prompt
# is the optional high-confidence path.
#
# Template variables injected at runtime (Python .format()):
#   {slug}          — pipeline slug (e.g., "alex-hormozi")
#   {insights_text} — first 1500 chars of aggregated insights from INSIGHTS-STATE.json
#   {valid_domains} — comma-separated list of valid domain names

## Task

You are classifying a knowledge-base entry for the MCE Atlas — a structured map of
expert domain knowledge. Your job is to assign the top 3 most relevant domains from
the provided list.

## Subject

Slug: {slug}

## Sample Insights (first 1500 chars)

{insights_sample}

## Valid Domains

{domains}

## Instructions

1. Read the insights sample carefully.
2. Identify the 3 domains that best describe the PRIMARY topics covered.
3. Rank them: primary (most relevant), secondary, tertiary.
4. Return ONLY a JSON block — no prose, no explanation.

## Output Format (strict JSON, no markdown fences)

{{
  "domains": ["<primary_domain>", "<secondary_domain>", "<tertiary_domain>"],
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reasoning": "<one sentence>"
}}

Rules:
- All values in "domains" MUST be from the valid domains list (exact spelling).
- List 1-3 domains maximum, ordered from most relevant to least relevant.
- confidence = "HIGH" if insights clearly map to domains, "MEDIUM" if partial,
  "LOW" if guessing.
- reasoning is 1 sentence max (used for audit trail only).
- Return valid JSON only — no trailing commas, no comments.
