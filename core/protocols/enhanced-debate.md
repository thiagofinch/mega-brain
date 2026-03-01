# ENHANCED DEBATE ENGINE
# Structured Multi-Agent Argumentation Protocol

> **Version:** 1.0.0
> **Status:** ACTIVE
> **Created:** 2026-02-28
> **Purpose:** Structured debate with scoring, evidence tracking, and conflict resolution
> **References:** `wf-conclave.yaml`, `agent-cognition.md`, `epistemic-standards.md`

---

## 1. OVERVIEW

```
+==============================================================================+
|                                                                              |
|   ENHANCED DEBATE ENGINE extends the Conclave with structured argumentation, |
|   evidence-based scoring, and formal conflict resolution. Every claim must   |
|   cite DNA sources, every rebuttal must address the specific evidence, and   |
|   every resolution must document what was decided and why.                   |
|                                                                              |
+==============================================================================+
```

### Enhancements Over Current Conclave

| Aspect | Current Conclave | Enhanced Debate |
|--------|-----------------|-----------------|
| Arguments | Free-form positions | Structured claims with evidence |
| Scoring | Quality score (single number) | Multi-dimensional scorecard |
| Conflicts | Identified by CRITIC | Formally tracked with resolution status |
| Evidence | Optional ^[FONTE] | MANDATORY per claim (auto-validated) |
| Rounds | 2 rounds (position + confrontation) | N rounds until convergence or deadlock |
| Output | Recommendation | Decision record with dissent log |

---

## 2. DEBATE STRUCTURE

### 2.1 Argument Format

Every argument in the debate MUST follow this structure:

```
CLAIM: [Clear, falsifiable statement]
EVIDENCE:
  - [DNA-ID]: "[quote or paraphrase]" (confidence: X%)
  - [DNA-ID]: "[quote or paraphrase]" (confidence: X%)
REASONING: [How evidence supports claim - 2-3 sentences]
CONFIDENCE: [0-100]%
LIMITATIONS: [What this claim does NOT cover]
```

### 2.2 Rebuttal Format

```
TARGETS: [Claim being rebutted]
CHALLENGE: [Specific weakness in claim or evidence]
COUNTER-EVIDENCE:
  - [DNA-ID]: "[contradicting evidence]"
ALTERNATIVE: [What should be concluded instead]
```

### 2.3 Concession Format

```
CONCEDES: [Which opposing claim]
REASON: [Why the evidence is stronger]
MODIFIES: [How this changes my position]
```

---

## 3. SCORING SYSTEM

### 3.1 Scorecard Dimensions

| Dimension | Weight | Measures |
|-----------|--------|----------|
| Evidence Strength | 30% | Quality and quantity of DNA citations |
| Logical Coherence | 25% | Internal consistency of reasoning chain |
| Practical Applicability | 20% | Can this be implemented in context? |
| Risk Awareness | 15% | Limitations and edge cases acknowledged |
| Epistemic Honesty | 10% | Appropriate confidence levels, concessions made |

### 3.2 Scoring Rules

```
+------------------------------------------------------------------------------+
|  EVIDENCE STRENGTH (0-100):                                                  |
|  - Per cited DNA element: +10 points (max 50)                                |
|  - High confidence citation (>0.8): +5 bonus                                |
|  - Cross-person corroboration: +10 bonus                                     |
|  - Uncited claim: -20 penalty                                                |
|  - Fabricated citation: -50 penalty (CRITICAL)                               |
|                                                                              |
|  LOGICAL COHERENCE (0-100):                                                  |
|  - Reasoning chain follows DNA cascade: +30                                  |
|  - No internal contradictions: +30                                           |
|  - Addresses counterarguments: +20                                           |
|  - Makes concessions where appropriate: +20                                  |
|                                                                              |
|  PRACTICAL APPLICABILITY (0-100):                                            |
|  - Specific to user's context: +40                                           |
|  - Actionable next steps: +30                                                |
|  - Resource-aware: +30                                                       |
|                                                                              |
|  RISK AWARENESS (0-100):                                                     |
|  - Limitations stated: +40                                                   |
|  - Edge cases identified: +30                                                |
|  - Failure modes acknowledged: +30                                           |
|                                                                              |
|  EPISTEMIC HONESTY (0-100):                                                  |
|  - Confidence calibrated to evidence: +40                                    |
|  - Concessions made when warranted: +30                                      |
|  - "I don't know" when appropriate: +30                                      |
+------------------------------------------------------------------------------+
```

---

## 4. CONFLICT RESOLUTION

### 4.1 Conflict Types

| Type | Description | Resolution Method |
|------|-------------|-------------------|
| FACTUAL | Different data/numbers cited | Verify against source material |
| PHILOSOPHICAL | Different core beliefs | Document both, let user decide |
| METHODOLOGICAL | Different approaches to same goal | Compare evidence, recommend with caveats |
| CONTEXTUAL | Same advice, different contexts | Clarify which context applies |
| PRIORITY | Agree on what but disagree on when | Evaluate urgency and dependencies |

### 4.2 Resolution Protocol

```
STEP 1: CLASSIFY conflict type
STEP 2: IDENTIFY common ground (what both sides agree on)
STEP 3: ISOLATE specific disagreement (narrowest possible framing)
STEP 4: EVALUATE evidence quality on both sides
STEP 5: RESOLVE or ESCALATE

  IF evidence clearly favors one side:
    → RESOLVE with winning position + dissent noted

  IF evidence is balanced:
    → PRESENT both with recommendation + reasoning

  IF evidence is insufficient:
    → DECLARE deadlock + specify what data would resolve it
```

### 4.3 Decision Record

Every resolved debate produces a decision record:

```yaml
decision:
  id: "DEC-2026-001"
  question: "What commission structure for closers?"
  date: "2026-03-01"
  participants: ["CLOSER", "CFO", "CRO"]
  rounds: 3
  outcome: "RESOLVED"

  winning_position:
    agent: "CFO"
    claim: "10% base + 5% performance bonus"
    score: 82
    evidence: ["HEUR-AH-025", "HEUR-CG-018", "FW-SO-003"]

  dissenting_positions:
    - agent: "CLOSER"
      claim: "15% flat commission"
      score: 71
      reason_for_dissent: "Higher motivation for top performers"

  resolution_basis: "METHODOLOGICAL - CFO's evidence included margin analysis"

  confidence: 75
  review_trigger: "Revisit if close rate drops below 25%"
```

---

## 5. CONVERGENCE DETECTION

### 5.1 When to Stop Debating

```
CONVERGED: All agents' positions within 15% score of each other
  → Synthesize into unified recommendation

DOMINANT: One position scores >20 points above all others
  → Declare winner, log dissent

DEADLOCKED: After 5 rounds, no convergence or dominance
  → Escalate to user with both positions and evidence summary

CONSENSUS: All agents agree (rare)
  → High-confidence recommendation
```

---

## 6. INTEGRATION

### With Conclave Workflow

Enhanced Debate replaces phases 1-2 of wf-conclave.yaml:
- Phase 0 (Constitution): Unchanged
- Phase 1 (Debate): NOW uses structured argument format + scoring
- Phase 2 (CRITIC): NOW validates evidence citations + scores
- Phase 3 (ADVOCATE): NOW must use rebuttal format
- Phase 4 (SYNTHESIS): NOW produces decision record

### With Agent Cognition

Agents in debate MUST follow AGENT-COGNITION-PROTOCOL:
- Phase 0 (Activation): Load identity before debating
- Phase 1 (Reasoning): Use DNA cascade for evidence
- Phase 1.5 (Depth-Seeking): Navigate to RAIZ for disputed claims
- Phase 2 (Epistemic): Declare confidence per claim

---

*Enhanced Debate Engine v1.0.0 -- Mega Brain*
