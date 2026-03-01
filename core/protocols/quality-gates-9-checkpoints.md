# Quality Gates Protocol: 9 Mandatory Checkpoints

> **Version:** 1.0.0
> **Created:** 2026-02-28
> **Status:** ACTIVE
> **Purpose:** Enforce 9 mandatory human validation gates throughout the mind cloning pipeline
> **Depends On:** apex-viability-scoring.md, dna-mental-8-layer.schema.json, wf-pipeline-full.yaml

---

## Overview

The Quality Gates Protocol defines 9 mandatory human checkpoints that govern the entire mind cloning lifecycle -- from initial viability assessment through production deployment. No clone may advance past a gate without explicit human approval. Gates are sequential and cumulative: a downstream gate cannot pass unless all upstream gates have already passed.

```
    QUALITY GATES: 9-CHECKPOINT PIPELINE
    =====================================

    QG-1  GO/NO-GO Decision          (Post-APEX Scoring)
      |
    QG-2  Source Sufficiency          (Post-Research)
      |
    QG-3  Layer 6 Validation          (Values Hierarchy)
      |
    QG-4  Layer 7 Validation          (Core Obsessions)
      |
    QG-5  Layer 8 Validation          (Productive Paradoxes) *** GOLD GATE ***
      |
    QG-6  System Prompt Review        (Pre-Deployment)
      |
    QG-7  Fidelity Testing            (Post-Blind Test)
      |
    QG-8  Brownfield Safety           (Updates Only)
      |
    QG-9  Production Approval         (Final Sign-Off)

    DEPENDENCY CHAIN:
    QG-1 --> QG-2 --> QG-3 --> QG-4 --> QG-5 --> QG-6 --> QG-7 --> QG-9
                                                          |
                                                   QG-8 --+ (updates only)
```

---

## Gate Dependency Chain

Each gate has strict prerequisites. The system MUST enforce these sequentially.

| Gate | Depends On | Skip Condition |
|------|-----------|----------------|
| QG-1 | None (entry point) | Never |
| QG-2 | QG-1 PASSED | Never |
| QG-3 | QG-2 PASSED | Never |
| QG-4 | QG-3 PASSED | Never |
| QG-5 | QG-4 PASSED | Never |
| QG-6 | QG-5 PASSED | Never |
| QG-7 | QG-6 PASSED | Never |
| QG-8 | QG-7 PASSED (prior version exists) | Skip if greenfield (first clone) |
| QG-9 | QG-7 PASSED + QG-8 PASSED (if applicable) | Never |

---

## Gate Definitions

### QG-1: GO/NO-GO Decision

```
TRIGGER:     After APEX Viability Scoring completes
PHASE:       Pre-Pipeline (Research)
GATE TYPE:   Binary (PASS/REJECT)
BLOCKING:    Yes -- pipeline cannot start without approval
```

**Input:**
- APEX viability score (0-100) from `core/protocols/apex-viability-scoring.md`
- Score breakdown by dimension (A, P, E, X, I, C)
- Source landscape summary

**Pass Criteria:**
- APEX score >= 50 (VIABLE or higher)
- No single dimension scores 0
- At least 2 dimensions score >= 15

**Actions:**

| Result | Action |
|--------|--------|
| PASS (score >= 50) | Approve candidate for cloning pipeline. Record approval with timestamp and approver. |
| CONDITIONAL (score 50-60) | Approve with documented limitations. Flag dimensions below 10 for monitoring. |
| REJECT (score < 50) | Reject candidate. Document rejection reason. Candidate may re-enter if new sources surface. |

**Reviewer:** Human operator (project owner)

**Record Format:**
```yaml
gate: QG-1
person_id: "XX"
apex_score: 72
decision: "PASS"
conditions: []
reviewer: "human"
timestamp: "2026-02-28T14:00:00Z"
notes: "Strong candidate. Weak on Consistency (12/20), monitor during extraction."
```

---

### QG-2: Source Sufficiency

```
TRIGGER:     After research phase completes source inventory
PHASE:       Research / Ingest
GATE TYPE:   Threshold (PASS/INSUFFICIENT)
BLOCKING:    Yes -- extraction cannot begin without sufficient sources
```

**Input:**
- Complete source inventory with metadata
- Source type classification (video, podcast, book, article, interview, course)
- Quality rating per source (HIGH / MEDIUM / LOW)
- Total hours/words of content

**Pass Criteria:**
- Minimum 5 quality sources (rated MEDIUM or higher)
- Minimum 3 distinct source types (e.g., video + book + podcast)
- At least 1 long-form source (>60 min or >10,000 words)
- Sources span at least 2 distinct time periods (to detect evolution)

**Actions:**

| Result | Action |
|--------|--------|
| PASS | Approve source corpus. Lock source list for extraction phase. |
| INSUFFICIENT | Document gaps. Specify what source types are missing. Return to research phase. |
| MARGINAL (4 sources, 2 types) | May proceed with explicit acknowledgment of limitations in clone fidelity ceiling. |

**Reviewer:** Human operator

**Record Format:**
```yaml
gate: QG-2
person_id: "XX"
total_sources: 8
source_types: ["video", "podcast", "book", "interview"]
quality_breakdown:
  high: 3
  medium: 4
  low: 1
decision: "PASS"
reviewer: "human"
timestamp: "2026-02-28T15:30:00Z"
notes: "Strong corpus. 4 source types, 12+ hours of content."
```

---

### QG-3: Layer 6 Validation (Values Hierarchy)

```
TRIGGER:     After L6 (Values Hierarchy) extraction completes
PHASE:       DNA Extraction
GATE TYPE:   Human Confirmation (CONFIRM/FLAG)
BLOCKING:    Yes -- L7 extraction should not begin until L6 is validated
```

**Input:**
- Extracted values hierarchy (ranked list)
- Trade-off evidence for each value (chose X over Y in context Z)
- Evidence type classification (sacrifice, trade_off, resource_allocation, repeated_choice, crisis_behavior)
- Declared vs. revealed alignment status per value
- Source references per value (minimum 3 for triangulation, per schema)

**Pass Criteria:**
- Human confirms extracted values match known behavior of the subject
- Each value has at least 1 concrete trade-off example
- No value relies solely on self-declaration (must have behavioral evidence)
- Hierarchy ordering passes "smell test" -- would a person who knows the subject agree?

**Actions:**

| Result | Action |
|--------|--------|
| CONFIRM | Values hierarchy locked for downstream use. Proceed to L7. |
| FLAG | Specific values flagged for re-analysis. Return to extraction with guidance on what to look for. |
| PARTIAL | Some values confirmed, others need more evidence. Proceed to L7 for confirmed values only. |

**Reviewer:** Human operator (ideally someone familiar with the subject)

**Record Format:**
```yaml
gate: QG-3
person_id: "XX"
values_count: 5
values_confirmed: ["VAL-XX-001", "VAL-XX-002", "VAL-XX-003", "VAL-XX-004"]
values_flagged: ["VAL-XX-005"]
flag_reasons:
  VAL-XX-005: "Insufficient trade-off evidence. Only one source supports this ranking."
decision: "PARTIAL"
reviewer: "human"
timestamp: "2026-02-28T18:00:00Z"
```

---

### QG-4: Layer 7 Validation (Core Obsessions)

```
TRIGGER:     After L7 (Core Obsessions) extraction completes
PHASE:       DNA Extraction
GATE TYPE:   Human Confirmation (CONFIRM/FLAG)
BLOCKING:    Yes -- L8 extraction should not begin until L7 is validated
```

**Input:**
- Extracted core obsessions (2-5 items, per schema constraint)
- Frequency metric per obsession (must be >= 0.50 of source material)
- Cross-layer manifestation map (must appear in >= 3 layers)
- Origin hypothesis per obsession
- Source references (minimum 3 for triangulation)

**Pass Criteria:**
- Human confirms the 2-3 core obsessions are accurate and genuinely central to the subject's thinking
- Each obsession appears in >= 50% of source material (frequency check)
- Each obsession manifests across >= 3 DNA layers (depth check)
- Obsessions are distinct from each other (no overlapping definitions)
- Human agrees with origin hypotheses or flags them as speculative

**Actions:**

| Result | Action |
|--------|--------|
| CONFIRM | Obsessions locked. Proceed to L8 extraction. |
| FLAG | Specific obsessions flagged as inaccurate or superficial. Return to extraction with correction notes. |
| REJECT | Obsession list fundamentally wrong. Full re-extraction of L7 required. |

**Reviewer:** Human operator

**Record Format:**
```yaml
gate: QG-4
person_id: "XX"
obsessions_count: 3
obsessions_confirmed: ["OBS-XX-001", "OBS-XX-002"]
obsessions_flagged: ["OBS-XX-003"]
flag_reasons:
  OBS-XX-003: "This looks like a topic, not an obsession. Frequency is 0.52 but feels forced."
decision: "FLAG"
reviewer: "human"
timestamp: "2026-02-28T20:00:00Z"
```

---

### QG-5: Layer 8 Validation (Productive Paradoxes) -- THE GOLD GATE

```
TRIGGER:     After L8 (Productive Paradoxes) extraction completes
PHASE:       DNA Extraction
GATE TYPE:   Human Confirmation (CONFIRM/REJECT)
BLOCKING:    Yes -- this is the GOLD GATE. No agent generation without L8 validation.
IMPORTANCE:  CRITICAL -- paradoxes are what make a clone feel human vs. robotic
```

**Why This Is the Gold Gate:**

Productive paradoxes are the most nuanced and error-prone layer to extract. A naive system sees contradictions and picks one side. A sophisticated clone holds both sides and knows when each applies. Getting this wrong produces a flat, one-dimensional agent. Getting it right produces a clone that genuinely surprises people with its human-like reasoning.

**Input:**
- Extracted paradox pairs (thesis + antithesis + synthesis)
- Context conditions for each side (when thesis applies vs. when antithesis applies)
- Source references for both sides (minimum 2 per side, per schema)
- Confidence score per paradox
- Cross-layer relationships (which items in L1-L7 relate to each side)

**Pass Criteria:**
- Human confirms each paradox is GENUINE, not an extraction artifact
- Both sides of each paradox have independent source evidence (not cherry-picked)
- Synthesis (contextual resolution) is coherent and non-trivial
- Paradoxes are distinct from each other
- No paradox is simply an error or misunderstanding of the source material
- Confidence threshold: all paradoxes must have confidence >= 0.7 or human override

**Actions:**

| Result | Action |
|--------|--------|
| CONFIRM | Set `human_validated: true` on L8 layer. Paradoxes are locked for agent generation. Proceed to QG-6. |
| REJECT (partial) | Specific paradoxes marked `human_rejected`. Remaining confirmed paradoxes proceed. Rejected items removed from agent generation. |
| REJECT (full) | All paradoxes rejected. L8 re-extraction required. Pipeline blocks until re-extraction and re-validation. |

**Reviewer:** Human operator (MUST be someone who understands the subject deeply)

**Record Format:**
```yaml
gate: QG-5
person_id: "XX"
paradoxes_count: 4
paradoxes_confirmed: ["PAR-XX-001", "PAR-XX-002", "PAR-XX-003"]
paradoxes_rejected: ["PAR-XX-004"]
rejection_reasons:
  PAR-XX-004: "This is not a paradox. The subject changed their mind between 2019 and 2023. It is evolution, not coexistence."
decision: "CONFIRM"
human_validated: true
reviewer: "human"
timestamp: "2026-03-01T10:00:00Z"
notes: "PAR-XX-002 is particularly strong. Gold-standard example of productive paradox."
```

---

### QG-6: System Prompt Review

```
TRIGGER:     After system prompts are compiled from validated DNA (L1-L8)
PHASE:       Agent Generation
GATE TYPE:   Human Review (APPROVE/REVISE)
BLOCKING:    Yes -- no deployment without prompt approval
```

**Input:**
- Compiled generalista system prompt
- Compiled specialist system prompt(s), if applicable
- Prompt metadata (token count, layer coverage, source count)
- Traceability map (which prompt sections map to which DNA items)

**Pass Criteria:**
- Prompt accurately represents the validated DNA layers
- No hallucinated content (every claim traceable to DNA items)
- Voice and tone match the subject (per SOUL.md patterns)
- Prompt is not excessively long (practical token budget check)
- No contradictions within the prompt (unless they are validated L8 paradoxes)
- Specialist prompts correctly scope to their domain

**Actions:**

| Result | Action |
|--------|--------|
| APPROVE | Prompts locked for deployment. Proceed to QG-7 (fidelity testing). |
| REVISE | Specific sections flagged for revision. Return to prompt compilation with notes. |
| REJECT | Prompts fundamentally flawed. Full recompilation required. |

**Reviewer:** Human operator

**Record Format:**
```yaml
gate: QG-6
person_id: "XX"
prompt_type: "generalista"
token_count: 4200
layer_coverage:
  L1: true
  L2: true
  L3: true
  L4: true
  L5: true
  L6: true
  L7: true
  L8: true
decision: "APPROVE"
revisions_requested: []
reviewer: "human"
timestamp: "2026-03-01T14:00:00Z"
```

---

### QG-7: Fidelity Testing

```
TRIGGER:     After blind fidelity testing completes
PHASE:       Validation / Testing
GATE TYPE:   Metric-Based (PASS/IMPROVE)
BLOCKING:    Yes -- production deployment requires fidelity threshold
```

**Input:**
- Fidelity test report
- Distinguishability rate (% of evaluators who correctly identified the clone vs. real)
- Sample size and evaluator qualifications
- Per-dimension fidelity scores (voice, reasoning, values, domain expertise)
- Failure analysis (which questions/scenarios exposed the clone)

**Pass Criteria:**

| Tier | Distinguishability | Fidelity | Decision |
|------|-------------------|----------|----------|
| GOLD | < 10% | >= 94% | Production-ready. Exceptional quality. |
| SILVER | 10-20% | 80-93% | Production-ready with documented limitations. |
| BRONZE | 20-30% | 70-79% | Conditional approval. Improvement plan required. |
| FAIL | > 30% | < 70% | Not production-ready. Return to prompt revision (QG-6). |

**Actions:**

| Result | Action |
|--------|--------|
| GOLD/SILVER | Approve for production. Proceed to QG-9 (or QG-8 if update). |
| BRONZE | Approve with mandatory improvement plan and timeline. Proceed to QG-9 with conditions. |
| FAIL | Return to QG-6 for prompt revision. Document failure patterns for targeted improvement. |

**Reviewer:** Human operator + fidelity test data

**Record Format:**
```yaml
gate: QG-7
person_id: "XX"
test_sample_size: 20
distinguishability_rate: 0.08
fidelity_score: 0.95
tier: "GOLD"
per_dimension:
  voice: 0.96
  reasoning: 0.93
  values: 0.97
  domain_expertise: 0.94
failure_patterns: []
decision: "PASS"
reviewer: "human"
timestamp: "2026-03-02T16:00:00Z"
```

---

### QG-8: Brownfield Safety (Updates Only)

```
TRIGGER:     After updating an existing production clone with new sources/DNA
PHASE:       Update Validation
GATE TYPE:   Regression Check (PASS/ROLLBACK)
BLOCKING:    Yes -- updates cannot deploy if fidelity regresses
SKIP:        Skip this gate entirely for greenfield (first-time) clones
```

**Input:**
- Previous fidelity score (from last QG-7)
- New fidelity score (after update)
- Delta analysis (what changed and why)
- Regression test results (same test suite, before and after)
- List of DNA items added/modified/removed

**Pass Criteria:**
- No fidelity drop > 5% overall
- No single dimension drops > 10%
- New sources do not contradict validated L8 paradoxes without re-validation
- Updated prompts pass diff review (changes are intentional, not side effects)

**Actions:**

| Result | Action |
|--------|--------|
| PASS | Update approved. Proceed to QG-9 for production deployment. |
| WARN (drop 3-5%) | Approve with monitoring. Schedule follow-up fidelity test in 7 days. |
| ROLLBACK (drop > 5%) | Rollback to previous version. Investigate regression cause. Fix and re-test. |

**Reviewer:** Human operator

**Record Format:**
```yaml
gate: QG-8
person_id: "XX"
previous_fidelity: 0.95
new_fidelity: 0.93
delta: -0.02
per_dimension_delta:
  voice: -0.01
  reasoning: -0.03
  values: 0.00
  domain_expertise: -0.02
dna_changes:
  added: 3
  modified: 1
  removed: 0
decision: "PASS"
reviewer: "human"
timestamp: "2026-03-05T10:00:00Z"
```

---

### QG-9: Production Approval (Final Sign-Off)

```
TRIGGER:     All prerequisite gates passed (QG-7 + QG-8 if applicable)
PHASE:       Deployment
GATE TYPE:   Final Authorization (DEPLOY/HOLD)
BLOCKING:    Yes -- the final gate before production
```

**Input:**
- Complete gate history (QG-1 through QG-7/QG-8)
- Final clone package manifest (prompts, DNA, configuration)
- Any outstanding conditions from previous gates
- Deployment target and access configuration

**Pass Criteria:**
- ALL prerequisite gates show PASSED status
- No unresolved conditions from any gate
- Complete gate audit trail exists
- Clone package is versioned and checksummed
- Deployment target is configured and accessible

**Actions:**

| Result | Action |
|--------|--------|
| DEPLOY | Clone deployed to production. Version recorded. Monitoring begins. |
| HOLD | Deployment deferred. Document hold reason and conditions for release. |
| REJECT | Fundamental issue discovered during final review. Route back to appropriate gate. |

**Reviewer:** Human operator (project owner -- final authority)

**Record Format:**
```yaml
gate: QG-9
person_id: "XX"
clone_version: "1.0.0"
prerequisite_gates:
  QG-1: "PASSED"
  QG-2: "PASSED"
  QG-3: "PASSED"
  QG-4: "PASSED"
  QG-5: "PASSED"
  QG-6: "PASSED"
  QG-7: "PASSED"
  QG-8: "SKIPPED"  # greenfield
outstanding_conditions: []
decision: "DEPLOY"
reviewer: "human"
timestamp: "2026-03-03T09:00:00Z"
notes: "First production clone. All 8 applicable gates passed. Monitoring active."
```

---

## Status Tracking

### Gate Status Values

| Status | Meaning |
|--------|---------|
| `NOT_STARTED` | Gate has not been triggered yet |
| `IN_PROGRESS` | Gate inputs are being prepared |
| `AWAITING_REVIEW` | Gate is ready for human review |
| `PASSED` | Gate passed -- downstream gates unlocked |
| `FAILED` | Gate failed -- must be resolved before retry |
| `CONDITIONAL` | Gate passed with conditions that must be monitored |
| `SKIPPED` | Gate not applicable (e.g., QG-8 on greenfield) |

### Aggregate Pipeline Status

```
PIPELINE STATUS = f(all gate statuses)

ALL gates PASSED/SKIPPED           --> COMPLETE
Any gate FAILED                    --> BLOCKED at {gate_id}
Any gate AWAITING_REVIEW           --> PENDING HUMAN ACTION at {gate_id}
All prior gates PASSED, next gate  --> READY FOR {gate_id}
  NOT_STARTED
```

---

## Integration Points

### With Existing Workflows

| Workflow | Integration |
|----------|-------------|
| `wf-pipeline-full.yaml` | QG-1 maps to pre-pipeline. QG-3/QG-4/QG-5 map to phase_3 (EXTRACTION) checkpoints. |
| `wf-ingest.yaml` | QG-2 validates source sufficiency post-ingest. |
| `wf-extract-dna.yaml` | QG-3/QG-4/QG-5 are embedded within DNA extraction flow. |

### With Existing Schemas

| Schema | Integration |
|--------|-------------|
| `dna-mental-8-layer.schema.json` | QG-3 validates L6, QG-4 validates L7, QG-5 validates L8. The `human_validated` field on L8 is set by QG-5. |
| `quality-gate.schema.json` | All gate records conform to this schema. |

### With Existing Checkpoints

The existing `wf-pipeline-full.yaml` defines 5 checkpoints (CP_FOUNDATION through CP_VALIDATION). Quality Gates are a SUPERSET that adds human validation on top of automated checkpoints:

| Pipeline Checkpoint | Quality Gate Overlay |
|--------------------|---------------------|
| CP_FOUNDATION | QG-2 (source sufficiency) |
| CP_INTELLIGENCE | -- (automated, no human gate needed) |
| CP_EXTRACTION | QG-3, QG-4, QG-5 (layer validations) |
| CP_PIPELINE | QG-6 (prompt review) |
| CP_VALIDATION | QG-7, QG-8, QG-9 (fidelity + deployment) |

---

## Audit Trail

Every gate decision MUST be recorded with:
1. Gate ID
2. Person ID
3. Decision (PASS/FAIL/CONDITIONAL/SKIP)
4. Reviewer identity
5. Timestamp
6. Input summary
7. Notes/rationale

Gate records are stored in: `logs/quality-gates/{person_id}/QG-{N}-{timestamp}.yaml`

The aggregate gate status for a clone is tracked in: `core/checklists/clone-quality-gates.yaml` (per-person instance)

---

## Escalation Protocol

If a gate fails twice consecutively:

1. Escalate to project owner
2. Conduct root cause analysis
3. Document the failure pattern
4. Determine if the issue is in extraction, sources, or the subject's suitability
5. If the subject is fundamentally unsuitable, route back to QG-1 for re-evaluation

---

*Quality Gates Protocol v1.0.0 -- 9 Mandatory Checkpoints*
*No clone ships without human approval at every critical junction.*
