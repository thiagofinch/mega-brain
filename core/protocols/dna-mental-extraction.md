# DNA Mental Extraction Protocol

> **Version:** 1.0.0
> **Schema:** `core/schemas/dna-mental-8-layer.schema.json`
> **Glossary:** `core/glossary/dna-mental-layers.md`
> **Scope:** Extraction of all 8 DNA layers from source materials

---

## Purpose

This protocol governs how the 8 layers of DNA Mental are extracted from raw source materials (transcriptions, books, courses, podcasts). It defines the order of extraction, quality gates, and validation checkpoints for each layer.

---

## Extraction Phases

```
  PHASE 1: EXPLICIT EXTRACTION (Layers 1-5)
  ==========================================
  Single-pass extraction from source material.
  Each batch of source material yields L1-L5 items directly.

      Source Material
           │
           ▼
  ┌────────────────────┐
  │  L5 Methodologies  │◄── "Step 1... Step 2..." patterns
  ├────────────────────┤
  │  L4 Frameworks     │◄── Named systems, multi-component models
  ├────────────────────┤
  │  L3 Heuristics     │◄── Rules, thresholds, "always/never"
  ├────────────────────┤
  │  L2 Mental Models  │◄── "Think of it like...", analogies
  ├────────────────────┤
  │  L1 Philosophies   │◄── "I believe...", "The truth is..."
  └────────────────────┘

  PHASE 2: DEEP INFERENCE (Layers 6-8)
  ==========================================
  Cross-source analysis AFTER all sources for a person are processed.
  Requires the complete L1-L5 corpus as input.

      Complete L1-L5 Corpus
           │
           ▼
  ┌────────────────────┐
  │  L6 Values         │◄── Trade-off analysis across all sources
  ├────────────────────┤
  │  L7 Obsessions     │◄── Frequency analysis across all sources
  ├────────────────────┤
  │  L8 Paradoxes      │◄── Contradiction detection + resolution
  └────────────────────┘
           │
           ▼
      HUMAN VALIDATION (L8 only)
```

---

## Phase 1: Explicit Extraction (L1-L5)

### When to Execute

- During Pipeline Phase 4 (batch processing)
- For each batch of source material

### Extraction Order

Process each batch in this order (most concrete first):

1. **L5 Methodologies** -- Scan for step-by-step instructions
2. **L4 Frameworks** -- Scan for named models and structured systems
3. **L3 Heuristics** -- Scan for rules, thresholds, decision shortcuts
4. **L2 Mental Models** -- Scan for analogies, lenses, thinking tools
5. **L1 Philosophies** -- Scan for beliefs, convictions, worldview statements

### Signal Words by Layer

| Layer | Signal Words / Patterns |
|-------|------------------------|
| L5 | "Step 1", "First you", "The process is", "How to", "Do X then Y" |
| L4 | Named acronyms (CLOSER, SPIN), "The X framework", "My system for", components listed |
| L3 | Numbers + context ("8-12%", "3x minimum"), "Always", "Never", "Rule of thumb", "If X then Y" |
| L2 | "Think of it like", "It's similar to", "The way I see it", "Imagine", analogies |
| L1 | "I believe", "The truth is", "What people don't understand", "At the end of the day", "The fundamental thing" |

### Quality Gates (L1-L5)

For each extracted item, verify:

```
[ ] Item has a valid ID in the correct pattern
[ ] Item has at least 1 source_reference with chunk_id
[ ] Item's source quote is a direct extraction (not paraphrased)
[ ] Item is classified in the correct layer (not misplaced)
[ ] Item does not duplicate an existing item (check by semantic similarity)
[ ] Confidence score reflects extraction certainty
```

### Deduplication Rules

When a new item seems to duplicate an existing one:

| Scenario | Action |
|----------|--------|
| Exact same concept, same person | Increment `reinforcement_count`, add new source |
| Same concept, different person | Create separate items (different ID prefix), note cross-reference |
| Similar concept, nuanced difference | Create separate items with clear distinction in description |
| Contradictory concept, same person | Flag for L8 Paradox analysis in Phase 2 |

---

## Phase 2: Deep Inference (L6-L8)

### When to Execute

- ONLY after ALL source material for a person has been processed through Phase 1
- During Pipeline Phase 5 (agent generation), sub-phase 5.1 (Foundation)
- Requires the complete L1-L5 corpus for that person as input

### Prerequisites

```
[ ] All batches for person XX processed through Phase 1
[ ] Complete L1-L5 corpus available (DNA.yaml populated)
[ ] Source count >= 3 (minimum for triangulation)
[ ] No pending batch processing for this person
```

---

### L6 Extraction: Values Hierarchy

**Method:** Trade-off analysis across all documented decisions and behaviors.

**Step-by-step:**

1. **Collect decision points** -- Scan all L1-L5 items and source material for moments where the person made explicit choices between competing priorities.

2. **Build trade-off pairs** -- For each decision, document:
   - What they CHOSE (reveals the higher value)
   - What they SACRIFICED (reveals the lower value)
   - The context of the decision

3. **Cluster into values** -- Group trade-off pairs by the underlying value being served:
   - Speed, Control, Freedom, Impact, Mastery, Wealth, Security, etc.

4. **Rank by consistency** -- The value that wins most consistently in trade-offs ranks highest.

5. **Cross-validate with L1** -- Compare revealed values against declared philosophies (L1). Note alignments and contradictions.

6. **Require triangulation** -- Each value must have evidence from 3+ independent sources.

**Evidence collection template:**

```yaml
value: "Speed"
trade_off_evidence:
  - chose: "[specific thing chosen]"
    over: "[specific thing sacrificed]"
    context: "[when/where this happened]"
    source:
      source_id: "AH003"
      chunk_id: "AH003-045"
      quote: "[exact words]"
```

**Quality gate:**

```
[ ] Each value has >= 3 independent trade-off examples
[ ] Trade-offs come from >= 3 different sources
[ ] Ranking is consistent (no value wins AND loses equally)
[ ] declared_vs_revealed field is set accurately
[ ] No values based solely on self-declarations
```

---

### L7 Extraction: Core Obsessions

**Method:** Frequency analysis + cross-layer manifestation mapping.

**Step-by-step:**

1. **Frequency scan** -- Analyze ALL processed source material. Identify themes/drivers that appear in >= 50% of sources.

2. **Distinguish topics from obsessions:**
   - TOPIC: "Sales" -- this is a domain, not an obsession
   - OBSESSION: "Leverage" -- this is the WHY behind sales frameworks that minimize input and maximize output

3. **Map manifestations** -- For each candidate obsession, find where it appears across layers:
   - Does it appear in L1 Philosophies?
   - Does it shape L2 Mental Models?
   - Does it create L3 Heuristics?
   - Does it structure L4 Frameworks?
   - Does it drive L5 Methodology design?
   - Does it explain L6 Value trade-offs?

4. **Require cross-layer presence** -- Must manifest in >= 3 different layers.

5. **Limit to 2-5 items** -- If analysis yields more than 5 candidates, go deeper. More than 5 means the analysis is too surface-level.

6. **Document origin hypothesis** -- Optionally note biographical/experiential roots.

**Quality gate:**

```
[ ] Each obsession appears in >= 50% of source material
[ ] Each obsession manifests in >= 3 different layers (L1-L6)
[ ] Total obsessions: 2-5 (not more)
[ ] Obsessions are DRIVERS, not topics or domains
[ ] Each has >= 3 independent source references
[ ] Frequency is calculated, not estimated
```

---

### L8 Extraction: Productive Paradoxes

**Method:** Contradiction detection + contextual resolution.

**Step-by-step:**

1. **Scan for contradictions** -- Review all L1-L5 items for the same person. Flag pairs where:
   - Item A says "do X" and Item B says "do NOT-X"
   - Heuristic A has threshold > N and Heuristic B implies threshold < N
   - Philosophy A and Philosophy B seem incompatible

2. **Filter out non-paradoxes:**
   - Evolution over time: "Used to think X, now thinks Y" -- NOT a paradox
   - Audience difference: "Says X to beginners, Y to experts" -- may be pedagogical
   - Imprecision: "Said 8% once and 12% another time" -- NOT a paradox
   - Context already encoded: "Do X in situation A, do Y in situation B" -- already resolved

3. **Confirm genuine paradoxes** -- For remaining candidates:
   - Verify BOTH sides have >= 2 independent sources
   - Verify the person genuinely holds BOTH positions simultaneously (not sequentially)
   - Verify the context difference is real (not just different wording)

4. **Write the synthesis** -- For each confirmed paradox, articulate:
   - WHEN the thesis applies (thesis_context)
   - WHEN the antithesis applies (antithesis_context)
   - HOW both coexist (synthesis)

5. **Set validation_status to `pending_human_review`** -- NEVER set to `human_confirmed` automatically.

6. **Optional: auto_high_confidence** -- If BOTH sides have 3+ sources AND confidence > 0.95, may flag as `auto_high_confidence`. This allows provisional use with a disclaimer but does NOT replace human validation.

**Quality gate:**

```
[ ] Each paradox has >= 2 sources per side (4 total minimum)
[ ] Non-paradoxes filtered out (evolution, imprecision, audience)
[ ] Synthesis explains contextual coexistence clearly
[ ] thesis_context and antithesis_context are distinct and specific
[ ] validation_status is "pending_human_review" (NOT "human_confirmed")
[ ] Related items in other layers are cross-referenced
```

---

## Human Validation Protocol (L8)

### Who Validates

The human stakeholder who deeply understands the expert being modeled. This is NOT a casual review -- it requires someone who can distinguish genuine paradoxes from extraction errors.

### Validation Checklist

For each L8 item in `pending_human_review`:

```
[ ] Is this a GENUINE contradiction the expert holds?
    → YES: Set to "human_confirmed"
    → NO: Set to "human_rejected" with reason

[ ] Is the synthesis accurate?
    → If not, revise synthesis before confirming

[ ] Are the contexts correct?
    → Thesis context: Is this really when side A applies?
    → Antithesis context: Is this really when side B applies?

[ ] Would you be comfortable if the mind clone used this paradox?
    → If hesitant, keep in "pending_human_review"
```

### After Validation

- `human_confirmed` items are published to agents and used in reasoning
- `human_rejected` items are logged with rejection reason and archived
- `pending_human_review` items are NOT used in agent generation

---

## Integration with Existing Pipeline

### Phase 4 (Batch Processing) Changes

Each batch now extracts L1-L5 items. The batch log template adds:

```
┌─ DNA EXTRACTION ────────────────────────────────────────────────────────────┐
│  L1 Philosophies:   +N new, M reinforced                                    │
│  L2 Mental Models:  +N new, M reinforced                                    │
│  L3 Heuristics:     +N new (Q quantitative, R qualitative), M reinforced    │
│  L4 Frameworks:     +N new, M reinforced                                    │
│  L5 Methodologies:  +N new, M reinforced                                    │
│                                                                             │
│  L6-L8: Deferred to Phase 5 (requires complete corpus)                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 5 (Agent Generation) Changes

Sub-phase 5.1 (Foundation) now includes L6-L8 extraction:

```
5.1 FOUNDATION (per source):
    5.1.1  Load all batches for source
    5.1.2  Consolidate L1-L5 DNA
    5.1.3  Extract L6 Values Hierarchy    ← NEW
    5.1.4  Extract L7 Core Obsessions     ← NEW
    5.1.5  Extract L8 Productive Paradoxes ← NEW
    5.1.6  Queue L8 for human validation   ← NEW
    5.1.7  Create SOURCE-XX.md
```

### DNA-CONFIG.yaml Changes

The `dna_sources` section in DNA-CONFIG.yaml should reference which layers have been extracted:

```yaml
dna_sources:
  primario:
    - pessoa: "alex-hormozi"
      layers_extracted: ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"]
      l8_validation_status: "pending_human_review"  # or "human_confirmed"
```

---

## Reasoning Cascade Update

The agent reasoning cascade (AGENT-COGNITION-PROTOCOL) is extended for L6-L8:

```
EXISTING CASCADE (L1-L5):
  METHODOLOGY → FRAMEWORK → HEURISTICS → MENTAL MODEL → PHILOSOPHY

EXTENDED CASCADE (L1-L8):
  METHODOLOGY (L5)
      → FRAMEWORK (L4)
      → HEURISTICS (L3)
      → MENTAL MODEL (L2)
      → PHILOSOPHY (L1)
      → VALUES CHECK (L6): "Does this align with revealed values?"
      → OBSESSION CHECK (L7): "Is a core obsession influencing this?"
      → PARADOX CHECK (L8): "Is there a productive paradox here?"

L6 CHECK: After forming a recommendation, verify it aligns with the
          expert's revealed values hierarchy. If it conflicts with a
          top-ranked value, flag and explain.

L7 CHECK: After forming a recommendation, check if a core obsession
          is pulling the reasoning in a specific direction. If so,
          make it transparent: "Note: This recommendation reflects
          [PERSON]'s core obsession with [X]."

L8 CHECK: If the situation maps to a known productive paradox,
          present BOTH sides with their contexts instead of picking
          one side. This is what makes the clone feel human.
```

---

## Error Handling

| Error | Resolution |
|-------|------------|
| L6 value has < 3 sources | Do NOT publish. Mark as `draft` and collect more evidence |
| L7 obsession frequency < 50% | Demote to "recurring theme" (not obsession). Do not include in L7 |
| L7 yields > 5 obsessions | Re-analyze at deeper level. Merge overlapping obsessions |
| L8 paradox is actually evolution | Reclassify as temporal change. Remove from L8 |
| L8 paradox is imprecision | Reclassify as data quality issue. Remove from L8 |
| L8 human rejects paradox | Archive with rejection reason. Do not re-submit same paradox |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-02-28 | Initial extraction protocol for 8-layer DNA Mental |
