# DNA Mental - 8-Layer Cognitive Architecture

> **Version:** 1.0.0
> **Schema:** `core/schemas/dna-mental-8-layer.schema.json`
> **Origin:** MMOS DNA Mental methodology, adapted for Mega Brain

---

## Overview

The DNA Mental 8-Layer architecture maps the complete cognitive structure of an expert mind. Layers 1-5 capture what someone knows and how they operate. Layers 6-8 capture who they are at a deeper level -- what they sacrifice for, what they cannot stop thinking about, and where they productively contradict themselves.

```
                EXPLICIT KNOWLEDGE (Layers 1-5)
                ================================
                Extracted from direct statements

  L5  METHODOLOGIES       Step-by-step implementations
  L4  FRAMEWORKS          Structured processes and models
  L3  HEURISTICS          Rules of thumb and decision shortcuts
  L2  MENTAL MODELS       Thinking lenses and decision frameworks
  L1  PHILOSOPHIES        Core beliefs and worldview

                ================================

                DEEP COGNITION (Layers 6-8)
                ================================
                Inferred from patterns across sources
                Require triangulation (3+ sources min)

  L6  VALUES HIERARCHY    Revealed through sacrifice, not declaration
  L7  CORE OBSESSIONS     Deep drivers in 50%+ of all material
  L8  PRODUCTIVE PARADOXES  Contradictions that coexist contextually

                ================================
                L8 requires HUMAN VALIDATION
```

---

## Layer Definitions

### L1: Philosophies

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `FIL-XX-NNN` (e.g., FIL-AH-001) |
| **What it captures** | Core beliefs, worldview, foundational convictions |
| **How to identify** | Statements like "I believe...", "The truth is...", "What people don't understand is..." |
| **Extraction method** | Direct extraction from statements |
| **Minimum sources** | 1 (but reinforcement from 2+ increases confidence) |
| **Cascading role** | Philosophical foundation that all other layers must align with |

**Examples:**
- "Volume negates luck" (FIL-AH-001) -- Hormozi
- "Price is a function of the transformation, not the time" (FIL-SO-003) -- Sam Oven
- "Sales is a transference of certainty" (FIL-CG-001) -- Cole Gordon

**What it is NOT:**
- Not a preference ("I like working mornings") -- that is personal style
- Not a fact ("The market grew 20%") -- that is data
- Not a strategy ("We should expand to Europe") -- that is a decision

---

### L2: Mental Models

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `MM-XX-NNN` (e.g., MM-AH-005) |
| **What it captures** | Thinking lenses, decision frameworks, cognitive tools |
| **How to identify** | "Think of it like...", "The way I see it...", analogies, metaphors used for decision-making |
| **Extraction method** | Direct extraction + pattern recognition |
| **Minimum sources** | 1 |
| **Cascading role** | Shapes how the expert interprets situations before applying specific tools |

**Examples:**
- "Christmas Tree Org Structure" (MM-AH-005) -- Sales hierarchy as visual model
- "Barbell Strategy" (MM-SO-002) -- All-in on extremes, nothing in the middle
- "The 5 Weapons of Closing" (MM-CG-010) -- Mental model for closing toolkit

**Key property:** Each mental model must include `trigger_questions` -- the questions it prompts the thinker to ask when activated.

---

### L3: Heuristics

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `HEUR-XX-NNN` (e.g., HEUR-AH-025) |
| **What it captures** | Practical rules, decision shortcuts, rules of thumb |
| **How to identify** | Numeric thresholds, "always/never" rules, conditional triggers |
| **Extraction method** | Direct extraction |
| **Minimum sources** | 1 |
| **Cascading role** | Concrete decision points that agents use for immediate guidance |
| **Sub-types** | `quantitative` (has numbers) and `qualitative` (pattern-based) |

**Examples (quantitative):**
- "Commission should be 8-12% of cash collected" (HEUR-AH-025)
- "If show rate < 66%, implement double booking" (HEUR-CG-018)
- "LTV/CAC must be >= 3x" (HEUR-AH-030)

**Examples (qualitative):**
- "Always isolate the objection before responding" (HEUR-CG-042)
- "Never hire for a role you haven't done yourself" (HEUR-AH-055)

**Priority in cascading:** Quantitative heuristics are prioritized over qualitative when both exist for the same decision.

---

### L4: Frameworks

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `FW-XX-NNN` (e.g., FW-AH-003) |
| **What it captures** | Structured multi-step processes, named models, repeatable structures |
| **How to identify** | Named systems (often acronyms), multi-component models, structured approaches |
| **Extraction method** | Direct extraction of components and their relationships |
| **Minimum sources** | 1 |
| **Cascading role** | Structured approach to apply when a specific domain is triggered |

**Examples:**
- "CLOSER Framework" (FW-AH-003) -- C-L-O-S-E-R for sales calls
- "Value Equation" (FW-AH-001) -- Dream Outcome x Probability / Time x Effort
- "Purple Ocean Method" (FW-SO-003) -- Category design strategy

**Difference from Methodologies:** Frameworks define WHAT the structure is. Methodologies define HOW to execute step by step.

---

### L5: Methodologies

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `MET-XX-NNN` (e.g., MET-CG-005) |
| **What it captures** | Step-by-step implementation guides, actionable procedures |
| **How to identify** | "Step 1... Step 2...", "First do X, then Y", sequential instructions |
| **Extraction method** | Direct extraction of ordered steps |
| **Minimum sources** | 1 |
| **Cascading role** | Most concrete layer -- used first in the reasoning cascade when available |

**Examples:**
- "Objection Handling 4-Step" (MET-CG-005) -- Isolate, Validate, Reframe, Close
- "Hiring Process for Sales Reps" (MET-AH-008) -- 6-step hiring methodology
- "Payment Plan Negotiation" (MET-CG-012) -- How to structure deal-making

**Key property:** Each methodology must have `steps` with `step_number`, `action`, `description`, and optionally `success_criteria`.

---

### L6: Values Hierarchy (NEW)

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `VAL-XX-NNN` (e.g., VAL-AH-001) |
| **What it captures** | True values as revealed through sacrifice and trade-offs, not self-declarations |
| **How to identify** | Moments of sacrifice, resource allocation patterns, consistent choices under pressure |
| **Extraction method** | **Inference from behavioral evidence** -- NOT from "I value X" statements |
| **Minimum sources** | **3 (triangulation required)** |
| **Cascading role** | Provides the motivational compass that explains WHY the expert makes certain trade-offs |

**The core principle:** A person's values are not what they say they value. Values are what they sacrifice for. If someone says "I value family" but works 100-hour weeks, their revealed value hierarchy puts growth/impact above family time.

**Evidence types:**
- `sacrifice` -- What they gave up to get something else
- `trade_off` -- Explicit either/or decisions documented in source material
- `resource_allocation` -- Where they put time, money, attention
- `repeated_choice` -- Consistent pattern of choosing A over B
- `crisis_behavior` -- What they prioritize when everything is on fire

**Examples:**
- VAL-AH-001: "Speed over Perfection" -- Revealed through repeated patterns of launching fast, iterating later, choosing velocity over polish in every documented business decision
- VAL-CG-001: "Mastery over Scale" -- Chose to stay in sales training niche rather than diversifying, invested in depth over breadth

**Structure of evidence:**

```yaml
trade_off_evidence:
  - chose: "Launched with known bugs"
    over: "Waiting for perfect product"
    context: "Gym Launch initial rollout"
    source: {chunk_id: "AH003-045"}
  - chose: "Hired B-players fast"
    over: "Waiting months for A-players"
    context: "Scaling from $3M to $10M"
    source: {chunk_id: "AH015-022"}
```

**What it is NOT:**
- Not self-reported values ("I believe in integrity") -- those go in L1 Philosophies
- Not preferences ("I prefer morning meetings") -- those are stylistic choices
- Not one-time decisions -- must show pattern across 3+ sources

---

### L7: Core Obsessions (NEW)

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `OBS-XX-NNN` (e.g., OBS-AH-001) |
| **What it captures** | The 2-3 deep cognitive drivers that appear in 50%+ of all source material |
| **How to identify** | Themes that recur across domains, topics the person cannot stop returning to, gravitational forces that pull everything into orbit |
| **Extraction method** | **Cross-source frequency analysis** -- requires scanning ALL processed material |
| **Minimum sources** | **3 (triangulation required)** |
| **Maximum items** | **5** -- if more are found, the analysis is too shallow |
| **Cascading role** | Meta-layer that EXPLAINS why certain philosophies, frameworks, and heuristics exist |

**The core principle:** Obsessions are not topics. A person who talks about sales is not "obsessed with sales." But if every sales framework they create optimizes for LEVERAGE (fewer inputs, more outputs), then leverage is the obsession. The obsession is the WHY behind the WHAT.

**Frequency requirement:** Must appear in at least 50% of all processed source material. This is what separates a core obsession from a recurring theme.

**Manifestation requirement:** Must manifest across at least 3 different layers (L1-L6). An obsession that only appears in frameworks but not in philosophies or heuristics is not deep enough to be a core obsession.

**Examples:**
- OBS-AH-001: "Leverage" (frequency: 0.85)
  - L1 manifestation: "Volume negates luck" (FIL-AH-001)
  - L3 manifestation: "1 input should create 10 outputs" (HEUR-AH-060)
  - L4 manifestation: "Value Equation" (FW-AH-001) -- time/effort in denominator
  - L6 manifestation: Consistently chose scalable over high-touch

- OBS-CG-001: "Precision" (frequency: 0.72)
  - L1 manifestation: "Sales is a science, not an art" (FIL-CG-005)
  - L3 manifestation: "Word-for-word scripts outperform improvisation" (HEUR-CG-030)
  - L5 manifestation: Every methodology has exact language to use

**What it is NOT:**
- Not a topic area ("sales", "marketing") -- those are domains
- Not a philosophy ("hard work pays off") -- that goes in L1
- Not a value ("I value speed") -- that goes in L6

---

### L8: Productive Paradoxes (NEW - GOLD LAYER)

| Attribute | Detail |
|-----------|--------|
| **ID Pattern** | `PAR-XX-NNN` (e.g., PAR-AH-001) |
| **What it captures** | Contradictions that coexist contextually -- both sides are true depending on context |
| **How to identify** | Person advocates X in one context and NOT-X in another; seemingly contradictory advice across sources |
| **Extraction method** | **Cross-source contradiction detection + contextual resolution** |
| **Minimum sources** | **2 per side** (2 for thesis + 2 for antithesis = 4 total minimum) |
| **Cascading role** | The most human layer -- makes mind clones feel real instead of one-dimensional |
| **Human validation** | **REQUIRED before publishing** -- this is the GOLD LAYER |

**The core principle:** A naive system sees contradiction as error. A sophisticated system recognizes that intelligent people hold contradictory positions because context changes. The paradox is not a bug -- it is the feature that separates a caricature from a clone.

**Why this is the Gold Layer:**
1. It is the hardest to extract correctly
2. False positives (extraction errors misidentified as paradoxes) destroy agent credibility
3. True positives make the clone feel genuinely human
4. Only a human who understands the expert can confirm the paradox is real

**Structure:**

```yaml
- id: PAR-AH-001
  thesis: "Give everything away for free"
  antithesis: "Charge premium prices"
  synthesis: "Free content builds audience and trust at scale. Premium pricing extracts value from those who want speed, implementation, and accountability. Both are true simultaneously for different segments."
  thesis_context: "Content marketing, audience building, top of funnel"
  antithesis_context: "High-ticket offers, coaching, implementation"
  validation_status: "human_confirmed"
```

**Validation states:**
- `pending_human_review` -- Extracted but NOT yet confirmed. Must not be used in agent generation.
- `human_confirmed` -- A human has reviewed and confirmed this is a genuine paradox. Safe to use.
- `human_rejected` -- Flagged as extraction error or false positive. Must be removed or re-analyzed.
- `auto_high_confidence` -- System confidence > 0.95 AND both sides have 3+ sources. May be used with disclaimer.

**Examples:**
- PAR-AH-001: "Give free / Charge premium" -- Free builds audience, premium extracts from action-takers
- PAR-AH-002: "Move fast / Be patient" -- Sprint on execution, be patient on compounding results
- PAR-CG-001: "Follow the script exactly / Read the room and adapt" -- Script provides structure, tonality and timing require human judgment

**What it is NOT:**
- Not an inconsistency or error ("He said 8% commission once and 12% another time") -- that is imprecision
- Not evolution over time ("He used to think X, now thinks Y") -- that is growth, not paradox
- Not different audience framing ("Says A to beginners, B to advanced") -- that may be pedagogical, not paradoxical

---

## Layer Relationships

```
L8 PARADOXES ─────────────────── The contradictions that make clones human
    │                              Requires: L1+L3+L6 items on both sides
    │
L7 OBSESSIONS ───────────────── The gravitational forces behind everything
    │                              Manifests in: L1, L2, L3, L4, L5, L6
    │
L6 VALUES ───────────────────── The motivational compass
    │                              Revealed by: L1 contradicting behavior
    │                              Explains: L3 trade-off heuristics
    │
    ╔═══════════════════════════╗
    ║   EXPLICIT KNOWLEDGE      ║
    ╠═══════════════════════════╣
    ║                           ║
L5  ║ METHODOLOGIES             ║── Step-by-step HOW
    ║   │                       ║
L4  ║ FRAMEWORKS                ║── Structured WHAT
    ║   │                       ║
L3  ║ HEURISTICS                ║── Decision shortcuts
    ║   │                       ║
L2  ║ MENTAL MODELS             ║── Thinking lenses
    ║   │                       ║
L1  ║ PHILOSOPHIES              ║── Foundational beliefs
    ║                           ║
    ╚═══════════════════════════╝
```

---

## ID Patterns Summary

| Layer | ID Pattern | Regex | Example |
|-------|-----------|-------|---------|
| L1 Philosophies | `FIL-XX-NNN` | `^FIL-[A-Z]{2,4}-\d{3}$` | FIL-AH-001 |
| L2 Mental Models | `MM-XX-NNN` | `^MM-[A-Z]{2,4}-\d{3}$` | MM-AH-005 |
| L3 Heuristics | `HEUR-XX-NNN` | `^HEUR-[A-Z]{2,4}-\d{3}$` | HEUR-CG-018 |
| L4 Frameworks | `FW-XX-NNN` | `^FW-[A-Z]{2,4}-\d{3}$` | FW-AH-003 |
| L5 Methodologies | `MET-XX-NNN` | `^MET-[A-Z]{2,4}-\d{3}$` | MET-CG-005 |
| L6 Values Hierarchy | `VAL-XX-NNN` | `^VAL-[A-Z]{2,4}-\d{3}$` | VAL-AH-001 |
| L7 Core Obsessions | `OBS-XX-NNN` | `^OBS-[A-Z]{2,4}-\d{3}$` | OBS-AH-001 |
| L8 Productive Paradoxes | `PAR-XX-NNN` | `^PAR-[A-Z]{2,4}-\d{3}$` | PAR-AH-001 |

Where `XX` is the 2-4 letter person prefix (e.g., AH = Alex Hormozi, CG = Cole Gordon) and `NNN` is a zero-padded sequence number.

---

## Triangulation Requirements

| Layer | Minimum Independent Sources | Rationale |
|-------|----------------------------|-----------|
| L1-L5 | 1 (2+ recommended) | Explicit knowledge can be extracted from single statements |
| L6 Values | 3 | Values must be revealed through behavioral patterns, not declarations |
| L7 Obsessions | 3 + 50% frequency | Must be pervasive enough to qualify as a cognitive driver |
| L8 Paradoxes | 4 (2 per side) | Both sides must have independent evidence to avoid false positives |

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-02-28 | Initial 8-layer architecture definition |
