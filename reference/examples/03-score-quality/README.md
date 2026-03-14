# Example 03: Score Content Quality

Demonstrates how to evaluate content quality using the numeric scorer.
Scores pipeline batches and agents on a 0-100 scale across 4 dimensions.

## Prerequisites

No extra dependencies. Pure Python using only stdlib.

## Usage

### Score a pipeline batch

```python
from core.intelligence.validation.quality_scorer import score_batch, persist_score

score = score_batch("logs/batches/BATCH-050.md", batch_id="BATCH-050")

print(f"Score: {score.total}/100 (Grade: {score.grade})")
print(f"  Coverage:      {score.coverage}/25")
print(f"  Clarity:       {score.clarity}/25")
print(f"  Completeness:  {score.completeness}/25")
print(f"  Traceability:  {score.traceability}/25")
print(f"  Details:       {score.details}")

# Save for trend tracking (appends to .data/quality_scores.jsonl)
persist_score(score)
```

### Score an agent

```python
from core.intelligence.validation.quality_scorer import score_agent

score = score_agent("agents/external/alex-hormozi")

print(f"Agent Score: {score.total}/100 (Grade: {score.grade})")
print(f"  Files present:    {score.details['coverage']}")
print(f"  Structure:        {score.details['clarity']}")
print(f"  Template parts:   {score.details['completeness']}")
print(f"  Citations:        {score.details['traceability']}")
```

### Track score trends over time

```python
from core.intelligence.validation.quality_scorer import get_trend, load_scores

# Get score history for a specific item
trend = get_trend("BATCH-050")
print(f"Score history: {trend}")
# Output: [65, 72, 78]  -- improving over iterations

# Load ALL historical scores
all_scores = load_scores()
print(f"Total scores tracked: {len(all_scores)}")

# Filter by type
batch_scores = [s for s in all_scores if s.item_type == "batch"]
agent_scores = [s for s in all_scores if s.item_type == "agent"]
print(f"Batches scored: {len(batch_scores)}")
print(f"Agents scored:  {len(agent_scores)}")
```

## Scoring Dimensions

| Dimension | What It Measures | Max | Batch Checks | Agent Checks |
|-----------|-----------------|-----|--------------|--------------|
| Coverage | Content breadth | 25 | DNA layers referenced (5 layers) | Required files present (4 files) |
| Clarity | Structure quality | 25 | Headers, sections, lists, length | ASCII art, headers, template parts |
| Completeness | Expected sections | 25 | CONTEXTO, DESTINO, ARQUIVO, BATCH, FONTE | Template V3 parts (10 parts) |
| Traceability | Source citations | 25 | ^[FONTE] and [FONTE markers | Citations in SOUL.md + MEMORY.md |

## Grades

| Grade | Score Range | Meaning |
|-------|-----------|---------|
| A | 90-100 | Excellent -- all dimensions strong |
| B | 70-89 | Good -- minor gaps |
| C | 50-69 | Acceptable -- needs improvement |
| D | 30-49 | Weak -- significant gaps |
| F | 0-29 | Critical -- major rework needed |

## Storage

Scores are persisted as JSONL (one JSON object per line):

```
.data/quality_scores.jsonl
```

Each entry contains:
```json
{
  "item_id": "BATCH-050",
  "item_type": "batch",
  "coverage": 20,
  "clarity": 25,
  "completeness": 15,
  "traceability": 20,
  "total": 80,
  "grade": "B",
  "timestamp": "2026-03-14T10:30:00+00:00",
  "details": { ... }
}
```

## Source

Module: `core/intelligence/validation/quality_scorer.py`

Key functions:
- `score_batch(batch_path, batch_id=None) -> QualityScore`
- `score_agent(agent_dir) -> QualityScore`
- `persist_score(score, scores_file=None) -> None`
- `load_scores(scores_file=None) -> list[QualityScore]`
- `get_trend(item_id, scores_file=None) -> list[int]`
