# BLIND TESTING PROTOCOL
# Clone Fidelity Validation via Blind Assessment

> **Version:** 1.0.0
> **Status:** ACTIVE
> **Created:** 2026-02-28
> **Purpose:** Systematic measurement of mind-clone fidelity through blind testing
> **Target:** <10% distinguishability rate = 94% fidelity
> **Minimum:** <20% distinguishability rate = 80% fidelity
> **References:** `agent-integrity.md`, `epistemic-standards.md`, `agent-cognition.md`

---

## 1. OVERVIEW

```
+==============================================================================+
|                                                                              |
|   BLIND TESTING measures how faithfully a mind-clone replicates the          |
|   original person's thinking, voice, reasoning, and contradictions.          |
|                                                                              |
|   If an evaluator cannot distinguish clone output from real output           |
|   more than 10% of the time, the clone achieves 94% FIDELITY.               |
|                                                                              |
+==============================================================================+
```

### Why Blind Testing

| Problem | Without Blind Testing | With Blind Testing |
|---------|----------------------|-------------------|
| Fidelity unknown | "Sounds about right" (subjective) | 94% measured fidelity |
| Drift detection | Undetected until failure | Caught at <5% deviation |
| Quality baseline | No benchmark | Quantified per dimension |
| Regression tracking | Manual review | Automated scoring per version |

### Integration with Existing Protocols

This protocol builds on three existing Mega Brain protocols:

- **AGENT-INTEGRITY-PROTOCOL** (`agent-integrity.md`): Ensures 100% traceability to sources. Blind Testing validates that this traceability produces faithful output.
- **EPISTEMIC-PROTOCOL** (`epistemic-standards.md`): Defines fact vs. recommendation separation. Blind Testing verifies the clone maintains the same epistemic boundaries as the original.
- **AGENT-COGNITION-PROTOCOL** (`agent-cognition.md`): Defines the 5-phase cognitive flow. Blind Testing validates that cascading DNA reasoning produces authentic output.

---

## 2. TEST CASE GENERATION

### 2.1 Volume Requirements

```
+------------------------------------------------------------------------------+
|  MINIMUM TEST CASES PER CLONE: 85                                            |
|  RECOMMENDED TEST CASES PER CLONE: 100-120                                   |
|  MAXIMUM USEFUL TEST CASES: 150 (diminishing returns beyond this)            |
+------------------------------------------------------------------------------+
```

### 2.2 Test Category Distribution

| Category | Percentage | Count (at 100) | Purpose |
|----------|-----------|-----------------|---------|
| Direct Quote Tests | 30% | 30 | Can the evaluator tell real quotes from generated? |
| Decision Scenario Tests | 25% | 25 | Does the clone decide like the real person? |
| Style Tests | 25% | 25 | Does tone, vocabulary, and rhetoric match? |
| Edge Case Tests | 20% | 20 | Does the clone hold the same paradoxes and nuances? |

### 2.3 Source Material Requirements

Test cases MUST be derived from documented source material:

```
+------------------------------------------------------------------------------+
|  SOURCES FOR TEST GENERATION:                                                |
|                                                                              |
|  PRIMARY (required):                                                         |
|  - inbox/{PERSON}/ transcriptions (raw material)                             |
|  - knowledge/dna/persons/{PERSON}/ (structured DNA)                          |
|  - agents/persons/{PERSON}/SOUL.md (identity/voice)                          |
|  - agents/persons/{PERSON}/MEMORY.md (accumulated experience)                |
|                                                                              |
|  SECONDARY (recommended):                                                    |
|  - Published books, interviews, social media posts                           |
|  - Video/audio recordings with timestamps                                    |
|  - Known public decisions with documented reasoning                          |
|                                                                              |
|  NEVER:                                                                      |
|  - Fabricated quotes attributed to the person                                |
|  - Scenarios with no documented precedent for comparison                     |
|  - Tests based on private information not in the knowledge base              |
+------------------------------------------------------------------------------+
```

---

## 3. TEST TYPE SPECIFICATIONS

### 3.1 DIRECT QUOTE TESTS (30%)

**Objective:** Evaluator is presented with two quotes on the same topic -- one real, one generated by the clone -- and must identify which is real.

**Structure:**

```yaml
test_type: direct_quote
topic: "[TOPIC]"
pair:
  quote_a: "[TEXT]"
  quote_b: "[TEXT]"
  real: "a"  # or "b" -- randomized
source_reference: "[chunk_id or file path]"
difficulty: "[easy|medium|hard]"
```

**Concrete Example:**

```
+------------------------------------------------------------------------------+
|  DIRECT QUOTE TEST #DQ-017                                                   |
|  Subject: Alex Hormozi | Topic: Pricing Strategy                             |
+------------------------------------------------------------------------------+
|                                                                              |
|  QUOTE A:                                                                    |
|  "The goal is to make your offer so good that people feel stupid             |
|   saying no. Price is what you pay, value is what you get. And               |
|   if you can make the value so overwhelming, the price becomes               |
|   irrelevant."                                                               |
|                                                                              |
|  QUOTE B:                                                                    |
|  "Make the offer so good people feel stupid saying no. That is               |
|   the whole game. You are not selling a price, you are selling               |
|   the delta between what they pay and what they get."                        |
|                                                                              |
|  EVALUATOR PICKS: ___                                                        |
|  REAL QUOTE: A                                                               |
|  SOURCE: ^[RAIZ:/inbox/ALEX HORMOZI/YOUTUBE/$100M Offers.txt:L340-345]       |
|                                                                              |
+------------------------------------------------------------------------------+
```

**Difficulty Calibration:**

| Difficulty | Criteria | Expected Accuracy |
|-----------|----------|-------------------|
| Easy | Different vocabulary, wrong cadence | 70-90% correctly identified |
| Medium | Similar vocabulary, slight phrasing difference | 40-60% correctly identified |
| Hard | Near-identical style, subtle difference only | 20-40% correctly identified |

**Distribution:** 10 easy, 12 medium, 8 hard (at 30 tests)

**Generation Rules:**
1. Real quote MUST come from documented source with `^[RAIZ:]` reference
2. Generated quote must address the SAME topic as the real quote
3. Generated quote is produced by the clone agent being tested
4. Position (A/B) MUST be randomized -- never always put real first
5. Both quotes must be similar length (within 20% word count)

---

### 3.2 DECISION SCENARIO TESTS (25%)

**Objective:** Present a business scenario, collect the clone's decision, then compare against the person's documented real decision in the same or highly similar situation.

**Structure:**

```yaml
test_type: decision_scenario
scenario: "[SITUATION DESCRIPTION]"
constraints: "[KEY CONSTRAINTS]"
clone_decision: "[COLLECTED FROM CLONE]"
real_decision: "[DOCUMENTED DECISION]"
real_decision_source: "[chunk_id or file path]"
alignment_score: 0-100
reasoning_match: true|false
```

**Concrete Example:**

```
+------------------------------------------------------------------------------+
|  DECISION SCENARIO TEST #DS-008                                              |
|  Subject: Cole Gordon | Domain: Sales Team Compensation                      |
+------------------------------------------------------------------------------+
|                                                                              |
|  SCENARIO:                                                                   |
|  Your top closer has been consistently hitting 150% of quota for             |
|  3 months. They come to you asking for a raise from 10% commission           |
|  to 15%. Your current margins are 42%. Losing them would cost you            |
|  2-3 months of pipeline while you hire and train a replacement.              |
|                                                                              |
|  CONSTRAINTS:                                                                |
|  - Team of 5 closers, this person does 30% of total revenue                 |
|  - Other closers are aware of the negotiation                                |
|  - Current churn rate among closers: 20% annually                            |
|                                                                              |
|  CLONE'S DECISION: [collected at test time]                                  |
|                                                                              |
|  REAL DECISION (documented):                                                 |
|  "Never raise base commission for one person -- you create                   |
|   precedent. Instead, create a tiered bonus: 10% base stays,                 |
|   12% at 120% quota, 15% at 150% quota. Now every closer has                 |
|   the same opportunity. You keep your margins and you keep                    |
|   your culture."                                                             |
|                                                                              |
|  SOURCE: ^[RAIZ:/inbox/COLE GORDON/MASTERCLASS/compensation.txt:L89-97]      |
|                                                                              |
|  SCORING CRITERIA:                                                           |
|  - Did clone recommend against individual raise? [Y/N]                       |
|  - Did clone suggest tiered/performance-based structure? [Y/N]               |
|  - Did clone consider team dynamics/precedent? [Y/N]                         |
|  - Did clone protect margins? [Y/N]                                          |
|  - Did reasoning path match? [Y/N]                                           |
|                                                                              |
+------------------------------------------------------------------------------+
```

**Scoring Matrix:**

| Criteria Match | Points | Classification |
|---------------|--------|----------------|
| 5/5 criteria | 100 | Perfect alignment |
| 4/5 criteria | 80 | Strong alignment |
| 3/5 criteria | 60 | Moderate alignment |
| 2/5 criteria | 40 | Weak alignment |
| 1/5 criteria | 20 | Poor alignment |
| 0/5 criteria | 0 | No alignment |

**Generation Rules:**
1. Scenario MUST be based on a real documented decision
2. Scenario is presented WITHOUT revealing the real decision
3. Clone responds independently, then comparison is made
4. Minimum 5 scoring criteria per scenario
5. At least 5 scenarios must involve cross-domain decisions (e.g., sales + finance)

---

### 3.3 STYLE TESTS (25%)

**Objective:** Evaluate whether the clone's linguistic patterns, rhetorical devices, and tonal qualities match the original person.

**Structure:**

```yaml
test_type: style
dimension: "[vocabulary|rhetoric|tone|cadence|analogy]"
sample_text: "[CLONE-GENERATED TEXT, 200-500 words]"
reference_texts:
  - source: "[file path]"
    excerpt: "[REFERENCE TEXT]"
scoring:
  vocabulary_match: 0-100
  rhetorical_match: 0-100
  tonal_match: 0-100
  cadence_match: 0-100
  overall: 0-100
```

**Concrete Example:**

```
+------------------------------------------------------------------------------+
|  STYLE TEST #ST-012                                                          |
|  Subject: Alex Hormozi | Dimension: Rhetorical Pattern                       |
+------------------------------------------------------------------------------+
|                                                                              |
|  PROMPT TO CLONE:                                                            |
|  "Explain why most businesses fail in their first year."                     |
|                                                                              |
|  CLONE OUTPUT: [collected at test time]                                      |
|                                                                              |
|  STYLE CHECKLIST:                                                            |
|                                                                              |
|  VOCABULARY:                                                                 |
|  [ ] Uses characteristic terms: "leverage", "unit economics",                |
|      "LTV", "CAC", "the game", "compounding"                                |
|  [ ] Avoids terms the person never uses                                      |
|  [ ] Technical precision matches (not over/under-simplified)                 |
|                                                                              |
|  RHETORIC:                                                                   |
|  [ ] Uses contrast/juxtaposition ("most people do X, but Y")                |
|  [ ] Employs reframing ("it is not about X, it is about Y")                 |
|  [ ] Mathematical/logical argumentation style                                |
|  [ ] Direct, confrontational tone with the audience                          |
|                                                                              |
|  TONE:                                                                       |
|  [ ] Confident/assertive (not hedging)                                       |
|  [ ] Teacher-mode (explaining from experience)                               |
|  [ ] Occasional self-deprecating humor about past failures                   |
|  [ ] No false modesty                                                        |
|                                                                              |
|  CADENCE:                                                                    |
|  [ ] Short punchy sentences mixed with longer explanations                   |
|  [ ] Builds to a single clear conclusion                                     |
|  [ ] Uses repetition for emphasis                                            |
|  [ ] Paragraph length: 2-4 sentences (not walls of text)                     |
|                                                                              |
|  ANALOGY PATTERNS:                                                           |
|  [ ] Uses business/math analogies (not literary/poetic)                      |
|  [ ] References personal experience ("when I had Gym Launch...")             |
|  [ ] Quantifies wherever possible ("8 out of 10", "3x", etc.)               |
|                                                                              |
|  SCORING: ___/20 checklist items = ___%                                      |
|                                                                              |
+------------------------------------------------------------------------------+
```

**Style Dimensions Evaluated:**

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Vocabulary | 25% | Word choice, jargon, technical terms |
| Rhetoric | 25% | Argumentation patterns, persuasion style |
| Tone | 20% | Emotional register, confidence level, formality |
| Cadence | 15% | Sentence length, paragraph structure, pacing |
| Analogy | 15% | Types of comparisons, reference domains |

**Generation Rules:**
1. Prompts must be open-ended enough to reveal style (not yes/no questions)
2. Minimum 200 words of clone output per test
3. Reference texts must span at least 3 different source materials
4. Each style dimension must be tested at least 4 times across all tests

---

### 3.4 EDGE CASE TESTS (20%)

**Objective:** Test whether the clone faithfully reproduces the person's nuanced, paradoxical, or counterintuitive positions -- the positions most likely to be smoothed over by an AI.

**Structure:**

```yaml
test_type: edge_case
subtype: "[paradox|nuance|contradiction|evolution|boundary]"
setup: "[CONTEXT THAT MAKES THE POSITION NON-OBVIOUS]"
expected_position: "[DOCUMENTED NUANCED POSITION]"
trap_position: "[WHAT A GENERIC AI WOULD SAY]"
source_reference: "[chunk_id or file path]"
fidelity_score: 0-100
```

**Concrete Example:**

```
+------------------------------------------------------------------------------+
|  EDGE CASE TEST #EC-005                                                      |
|  Subject: Alex Hormozi | Subtype: Paradox                                   |
+------------------------------------------------------------------------------+
|                                                                              |
|  SETUP:                                                                      |
|  "You say you should give away everything for free to build                  |
|   goodwill. But you also sell high-ticket programs at $35k+.                 |
|   How do you reconcile giving everything away for free while                 |
|   charging premium prices?"                                                  |
|                                                                              |
|  EXPECTED POSITION (documented):                                             |
|  The person holds BOTH positions simultaneously without seeing               |
|  them as contradictory. Free content builds trust and                        |
|  demonstrates competence. Paid programs provide accountability,              |
|  access, and implementation support. The INFORMATION is free;                |
|  the IMPLEMENTATION is paid. "I have given away everything I                 |
|  know for free. People still pay because they are paying for                 |
|  proximity, accountability, and speed."                                      |
|                                                                              |
|  SOURCE: ^[RAIZ:/inbox/ALEX HORMOZI/YOUTUBE/100M Leads.txt:L1204-1220]      |
|                                                                              |
|  TRAP POSITION (generic AI would say):                                       |
|  "You should find a balance between free and paid content.                   |
|   Give away some things for free as a lead magnet, but keep                  |
|   your best material behind a paywall."                                      |
|                                                                              |
|  FIDELITY CRITERIA:                                                          |
|  [ ] Clone holds both positions WITHOUT trying to resolve tension            |
|  [ ] Clone frames information vs. implementation distinction                 |
|  [ ] Clone does NOT suggest "finding a balance" (the trap)                   |
|  [ ] Clone references specific reasoning (accountability, speed, proximity)  |
|  [ ] Confidence is HIGH (not hedging or presenting "both sides")             |
|                                                                              |
|  PASS: 4/5+ criteria met                                                     |
|  FAIL: <4/5 criteria met                                                     |
|                                                                              |
+------------------------------------------------------------------------------+
```

**Edge Case Subtypes:**

| Subtype | Count | What It Tests |
|---------|-------|---------------|
| Paradox | 5 | Positions that seem contradictory but the person holds both |
| Nuance | 5 | Positions with important qualifiers that generic AI drops |
| Contradiction | 3 | Actual evolution in thinking (person changed their mind) |
| Evolution | 4 | Views that shifted over time -- clone must reflect LATEST |
| Boundary | 3 | Topics the person explicitly refuses to opine on |

**Generation Rules:**
1. Every paradox test must document BOTH sides with source references
2. Every trap position must represent what a generic AI (without DNA) would produce
3. Evolution tests must include timestamps showing when views changed
4. Boundary tests must verify the clone says "I do not have a position on that" when appropriate
5. At minimum, 3 edge cases must cross DNA layers (e.g., a PHILOSOPHY that contradicts a HEURISTIC)

---

## 4. EVALUATION METHODOLOGY

### 4.1 Evaluator Requirements

```
+------------------------------------------------------------------------------+
|  EVALUATOR QUALIFICATIONS:                                                   |
|                                                                              |
|  REQUIRED:                                                                   |
|  - Familiar with the original person's public content                        |
|  - Has consumed at least 10 hours of the person's material                   |
|  - Can articulate what makes the person's style distinctive                  |
|                                                                              |
|  IDEAL:                                                                      |
|  - Has worked with or studied under the person                               |
|  - Can identify the person's voice in a blind reading                        |
|  - Understands the person's domain at an intermediate level                  |
|                                                                              |
|  EVALUATOR COUNT:                                                            |
|  - Minimum: 3 evaluators per test round                                      |
|  - Recommended: 5 evaluators                                                 |
|  - Inter-rater reliability target: Cohen's kappa >= 0.70                     |
|                                                                              |
|  EVALUATOR MUST NOT:                                                         |
|  - Know which response is from the clone                                     |
|  - Have access to source material during evaluation                          |
|  - Discuss their evaluations with other evaluators before scoring            |
+------------------------------------------------------------------------------+
```

### 4.2 Blind Protocol

```
+------------------------------------------------------------------------------+
|  BLINDING PROCEDURE:                                                         |
|                                                                              |
|  1. TEST ADMINISTRATOR generates test cases                                  |
|  2. TEST ADMINISTRATOR collects clone responses                              |
|  3. TEST ADMINISTRATOR randomizes presentation order                         |
|  4. EVALUATOR receives paired/single items with no labels                    |
|  5. EVALUATOR scores independently                                           |
|  6. SCORES are collected before revealing answers                            |
|  7. ANALYSIS is performed on aggregate data                                  |
|                                                                              |
|  ANTI-BIAS MEASURES:                                                         |
|  - No evaluator scores more than 40 tests in one session                     |
|  - Tests are presented in randomized order per evaluator                     |
|  - Fatigue check: discard last 10% if accuracy drops >15%                    |
|  - Each test type is intermixed (not grouped by category)                    |
+------------------------------------------------------------------------------+
```

### 4.3 Scoring System

**Per-Test Scoring:**

| Test Type | Scoring Method | Pass Threshold |
|-----------|---------------|----------------|
| Direct Quote | Binary: evaluator picks correctly or not | <50% correct = pass (indistinguishable) |
| Decision Scenario | 0-100 alignment score | >= 70 alignment |
| Style | 0-100 composite across dimensions | >= 75 composite |
| Edge Case | Binary: criteria met or not | >= 4/5 criteria |

**Aggregate Scoring:**

```
DISTINGUISHABILITY RATE = (correctly_identified_tests / total_tests) * 100

FIDELITY SCORE = 100 - DISTINGUISHABILITY_RATE

+------------------------------------------------------------------------------+
|  FIDELITY CLASSIFICATION:                                                    |
|                                                                              |
|  >= 94% fidelity (<= 6% distinguishable)   -->  EXCEPTIONAL                 |
|  90-93% fidelity (7-10% distinguishable)   -->  TARGET MET                  |
|  80-89% fidelity (11-20% distinguishable)  -->  ACCEPTABLE                  |
|  70-79% fidelity (21-30% distinguishable)  -->  NEEDS IMPROVEMENT           |
|  < 70% fidelity (> 30% distinguishable)    -->  FAILING                     |
+------------------------------------------------------------------------------+
```

---

## 5. FIDELITY DIMENSIONS

### 5.1 The Five Dimensions

Each clone is evaluated across five independent fidelity dimensions:

```
+------------------------------------------------------------------------------+
|                                                                              |
|  DIMENSION 1: CONTENT FIDELITY                                              |
|  "Does it say what the person would say?"                                    |
|  --------------------------------------------------------------------------  |
|  Measures: Factual accuracy of positions, recommendations, and beliefs       |
|  Source: DNA Layers (Philosophies, Mental Models, Heuristics, Frameworks)     |
|  Tests: Decision Scenarios (primary), Edge Cases (secondary)                 |
|  Weight: 30%                                                                 |
|                                                                              |
+------------------------------------------------------------------------------+
|                                                                              |
|  DIMENSION 2: LINGUISTIC FIDELITY                                            |
|  "Does it sound like the person?"                                            |
|  --------------------------------------------------------------------------  |
|  Measures: Vocabulary, sentence structure, jargon, formality level           |
|  Source: SOUL.md (voice system), raw transcriptions                          |
|  Tests: Style Tests (primary), Direct Quote Tests (secondary)                |
|  Weight: 25%                                                                 |
|                                                                              |
+------------------------------------------------------------------------------+
|                                                                              |
|  DIMENSION 3: REASONING FIDELITY                                             |
|  "Does it think like the person?"                                            |
|  --------------------------------------------------------------------------  |
|  Measures: Argumentation patterns, logical structure, prioritization         |
|  Source: Mental Models, Frameworks, MEMORY.md (decision patterns)            |
|  Tests: Decision Scenarios (primary), Style Tests (secondary)                |
|  Weight: 25%                                                                 |
|                                                                              |
+------------------------------------------------------------------------------+
|                                                                              |
|  DIMENSION 4: EMOTIONAL FIDELITY                                             |
|  "Does it react like the person?"                                            |
|  --------------------------------------------------------------------------  |
|  Measures: Emotional register, intensity, empathy vs. directness             |
|  Source: SOUL.md (tone), MEMORY.md (reaction patterns)                       |
|  Tests: Style Tests (primary), Edge Cases (secondary)                        |
|  Weight: 10%                                                                 |
|                                                                              |
+------------------------------------------------------------------------------+
|                                                                              |
|  DIMENSION 5: PARADOX FIDELITY                                               |
|  "Does it hold the same contradictions?"                                     |
|  --------------------------------------------------------------------------  |
|  Measures: Ability to hold simultaneous opposing views authentically          |
|  Source: Cross-layer DNA analysis, documented contradictions                  |
|  Tests: Edge Cases (primary)                                                 |
|  Weight: 10%                                                                 |
|                                                                              |
+------------------------------------------------------------------------------+
```

### 5.2 Composite Fidelity Score

```
COMPOSITE = (Content * 0.30) + (Linguistic * 0.25) + (Reasoning * 0.25)
          + (Emotional * 0.10) + (Paradox * 0.10)
```

### 5.3 Dimension Interaction Matrix

| Dimension | Reinforces | Conflicts With |
|-----------|-----------|----------------|
| Content | Reasoning (same conclusions via same logic) | Paradox (content can seem contradictory) |
| Linguistic | Emotional (tone is part of language) | Content (style without substance is hollow) |
| Reasoning | Content (logic leads to same answers) | Emotional (logic vs. gut reactions) |
| Emotional | Linguistic (feelings expressed through words) | Reasoning (emotions can override logic) |
| Paradox | Content (full picture includes contradictions) | Reasoning (paradoxes resist neat logic) |

---

## 6. TEST EXECUTION WORKFLOW

### 6.1 Full Workflow

```
+------------------------------------------------------------------------------+
|                                                                              |
|  PHASE 1: PREPARATION (1-2 days)                                             |
|  ---------------------------------                                           |
|  1. Select clone to evaluate                                                 |
|  2. Gather source materials (inbox, DNA, SOUL, MEMORY)                       |
|  3. Generate test cases using blind-test-template.yaml                       |
|  4. Review test cases for source traceability                                |
|  5. Randomize presentation order                                             |
|  6. Recruit and brief evaluators                                             |
|                                                                              |
|  PHASE 2: CLONE RESPONSE COLLECTION (1 day)                                  |
|  ------------------------------------------                                  |
|  1. Present scenarios/prompts to clone                                       |
|  2. Collect clone responses without human editing                            |
|  3. Pair with real quotes/decisions                                          |
|  4. Randomize A/B positioning                                                |
|                                                                              |
|  PHASE 3: BLIND EVALUATION (2-3 days)                                        |
|  -------------------------------------                                       |
|  1. Distribute test packets to evaluators                                    |
|  2. Evaluators score independently                                           |
|  3. Collect all scores before unblinding                                     |
|  4. Check inter-rater reliability                                            |
|                                                                              |
|  PHASE 4: ANALYSIS (1 day)                                                   |
|  --------------------------                                                  |
|  1. Calculate distinguishability rate per category                           |
|  2. Calculate fidelity score per dimension                                   |
|  3. Calculate composite fidelity score                                       |
|  4. Identify weakest dimensions                                              |
|  5. Generate fidelity report                                                 |
|                                                                              |
|  PHASE 5: REMEDIATION (as needed)                                            |
|  ---------------------------------                                           |
|  1. If fidelity < 80%: mandatory remediation                                |
|  2. Identify specific DNA gaps                                               |
|  3. Process additional source material                                       |
|  4. Re-run failed test categories                                            |
|  5. Document improvements in MEMORY.md                                       |
|                                                                              |
+------------------------------------------------------------------------------+
```

### 6.2 Automated vs. Manual Steps

| Step | Automated | Manual | Notes |
|------|-----------|--------|-------|
| Test case generation | Template-assisted | Review required | YAML template + human validation |
| Clone response collection | Fully automated | -- | Run clone agent with prompts |
| Randomization | Fully automated | -- | Script-based shuffle |
| Evaluation | -- | Fully manual | Human evaluators required |
| Score calculation | Fully automated | -- | Schema-validated JSON output |
| Report generation | Template-assisted | Interpretation | Fidelity report template |
| Remediation planning | -- | Fully manual | Requires domain expertise |

---

## 7. PASS/FAIL CRITERIA

### 7.1 Per-Category Thresholds

| Category | Pass | Conditional Pass | Fail |
|----------|------|-------------------|------|
| Direct Quote | <40% correctly identified | 40-55% correctly identified | >55% correctly identified |
| Decision Scenario | Average alignment >= 75 | Average alignment 60-74 | Average alignment < 60 |
| Style | Composite >= 80 | Composite 65-79 | Composite < 65 |
| Edge Case | >= 75% of tests pass | 60-74% of tests pass | < 60% of tests pass |

### 7.2 Overall Pass/Fail

```
+------------------------------------------------------------------------------+
|  OVERALL RESULT DETERMINATION:                                               |
|                                                                              |
|  PASS:                                                                       |
|  - Composite fidelity >= 90%                                                 |
|  - No single dimension below 75%                                             |
|  - No single category in FAIL status                                         |
|                                                                              |
|  CONDITIONAL PASS:                                                           |
|  - Composite fidelity >= 80%                                                 |
|  - Maximum 1 dimension below 75% (but above 60%)                             |
|  - Maximum 1 category in CONDITIONAL PASS status                             |
|  - Remediation plan required within 14 days                                  |
|                                                                              |
|  FAIL:                                                                       |
|  - Composite fidelity < 80%                                                  |
|  - OR 2+ dimensions below 75%                                                |
|  - OR any dimension below 60%                                                |
|  - OR any category in FAIL status                                            |
|  - Mandatory remediation before clone is considered operational              |
|                                                                              |
+------------------------------------------------------------------------------+
```

### 7.3 Regression Testing

```
+------------------------------------------------------------------------------+
|  WHEN TO RE-TEST:                                                            |
|                                                                              |
|  MANDATORY:                                                                  |
|  - After processing new source material (>10 files)                          |
|  - After modifying SOUL.md or DNA-CONFIG.yaml                                |
|  - After remediation of a FAIL result                                        |
|  - Quarterly (every 90 days) for active clones                               |
|                                                                              |
|  RECOMMENDED:                                                                |
|  - After processing any new source material                                  |
|  - After modifying MEMORY.md significantly                                   |
|  - When users report "that does not sound like [person]"                     |
|                                                                              |
|  REGRESSION THRESHOLD:                                                       |
|  - If fidelity drops >5% from previous test: INVESTIGATE                     |
|  - If fidelity drops >10% from previous test: REMEDIATE                      |
|  - Fidelity MUST NOT drop below 80% at any point                             |
+------------------------------------------------------------------------------+
```

---

## 8. REMEDIATION PROTOCOL

### 8.1 Diagnosis

When a clone fails or conditionally passes, diagnose the root cause:

| Symptom | Likely Cause | Remediation |
|---------|-------------|-------------|
| Low Content Fidelity | Insufficient DNA extraction | Process more source material, enrich DNA layers |
| Low Linguistic Fidelity | SOUL.md voice system weak | Add more characteristic phrases, study cadence |
| Low Reasoning Fidelity | Mental Models / Frameworks gaps | Extract more decision patterns from sources |
| Low Emotional Fidelity | Tone not captured in SOUL.md | Add emotional register examples, reaction patterns |
| Low Paradox Fidelity | Contradictions not documented | Explicitly document paradoxes in MEMORY.md |

### 8.2 Remediation Workflow

```
1. Identify failing dimension(s) and test(s)
2. Trace failure to specific DNA gap
3. Locate additional source material that covers the gap
4. Process through Pipeline (ingest -> chunks -> insights -> DNA)
5. Update SOUL.md / MEMORY.md / DNA-CONFIG.yaml as needed
6. Re-run ONLY the failed test category (not full suite)
7. If pass: run full suite to check for regressions
8. Document remediation in clone's MEMORY.md
```

---

## 9. REPORTING

### 9.1 Fidelity Report Structure

See `core/templates/validation/fidelity-report.md` for the full report template.

### 9.2 Report Distribution

| Audience | Receives | Format |
|----------|----------|--------|
| System (automated) | Full JSON report | `fidelity-report.schema.json` |
| Clone maintainer | Full markdown report | `fidelity-report.md` template |
| Clone MEMORY.md | Summary + action items | Appended to MEMORY.md |
| AGENT-INDEX.yaml | Fidelity score badge | `fidelity: 94%` field |

---

## 10. RELATION TO DNA SCHEMA

The blind testing protocol validates each DNA layer independently:

| DNA Layer | Validated By | How |
|-----------|-------------|-----|
| L1 PHILOSOPHIES | Edge Case Tests (Paradox) | Do paradoxes and core beliefs hold? |
| L2 MENTAL-MODELS | Decision Scenario Tests | Does clone apply the same thinking frameworks? |
| L3 HEURISTICS | Decision Scenario Tests | Does clone use the same rules of thumb? |
| L4 FRAMEWORKS | Style Tests (Rhetoric) | Does clone structure arguments the same way? |
| L5 METHODOLOGIES | Decision Scenario Tests | Does clone follow the same step-by-step processes? |

---

## CHECKLIST: BEFORE DECLARING A CLONE VALIDATED

```
[ ] Minimum 85 test cases generated
[ ] All 4 test categories represented at correct percentages
[ ] All test cases have source references (^[RAIZ:] format)
[ ] Minimum 3 evaluators recruited and briefed
[ ] Evaluators are properly blinded
[ ] Clone responses collected without editing
[ ] All scores collected before unblinding
[ ] Inter-rater reliability >= 0.70 (Cohen's kappa)
[ ] Composite fidelity calculated across all 5 dimensions
[ ] No single dimension below minimum threshold
[ ] Fidelity report generated and stored
[ ] Results documented in clone's MEMORY.md
[ ] AGENT-INDEX.yaml updated with fidelity score
```

---

## CHANGELOG

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-02-28 | Initial protocol: 4 test types, 5 fidelity dimensions, scoring system |

---

*End of BLIND-TESTING-PROTOCOL*
