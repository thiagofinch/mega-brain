# FIDELITY REPORT

> **Report ID:** {REPORT_ID}
> **Clone:** {CLONE_NAME} ({CLONE_ID})
> **Clone Version:** {CLONE_VERSION}
> **Date:** {DATE}
> **Protocol:** Blind Testing Protocol v1.0.0
> **Evaluators:** {EVALUATOR_COUNT}
> **Inter-Rater Reliability:** {KAPPA} (Cohen's kappa)

---

## EXECUTIVE SUMMARY

```
+==============================================================================+
|                                                                              |
|   CLONE: {CLONE_NAME}                                                        |
|   COMPOSITE FIDELITY: {COMPOSITE}%                                           |
|   CLASSIFICATION: {CLASSIFICATION}                                           |
|   OVERALL RESULT: {OVERALL_RESULT}                                           |
|   DISTINGUISHABILITY RATE: {DIST_RATE}%                                      |
|                                                                              |
+==============================================================================+
```

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Composite Fidelity | {COMPOSITE}% | >= 90% | {STATUS} |
| Distinguishability Rate | {DIST_RATE}% | <= 10% | {STATUS} |
| Test Cases Administered | {TOTAL_TESTS} | >= 85 | {STATUS} |
| Evaluator Count | {EVALUATOR_COUNT} | >= 3 | {STATUS} |
| Inter-Rater Reliability | {KAPPA} | >= 0.70 | {STATUS} |

---

## CATEGORY RESULTS

### Direct Quote Tests ({DQ_COUNT} tests)

```
+------------------------------------------------------------------------------+
|  Correctly Identified: {DQ_CORRECT}/{DQ_COUNT} ({DQ_RATE}%)                  |
|  Status: {DQ_STATUS}                                                         |
|  (Lower identification rate = higher fidelity)                               |
+------------------------------------------------------------------------------+
```

| Difficulty | Total | Identified | Rate |
|-----------|-------|------------|------|
| Easy | {EASY_TOTAL} | {EASY_ID} | {EASY_RATE}% |
| Medium | {MED_TOTAL} | {MED_ID} | {MED_RATE}% |
| Hard | {HARD_TOTAL} | {HARD_ID} | {HARD_RATE}% |

### Decision Scenario Tests ({DS_COUNT} tests)

```
+------------------------------------------------------------------------------+
|  Average Alignment: {DS_AVG}/100                                             |
|  Status: {DS_STATUS}                                                         |
+------------------------------------------------------------------------------+
```

| Alignment Level | Count | Percentage |
|----------------|-------|------------|
| Perfect (100) | {PERFECT} | {PERFECT_PCT}% |
| Strong (80) | {STRONG} | {STRONG_PCT}% |
| Moderate (60) | {MODERATE} | {MODERATE_PCT}% |
| Weak (40) | {WEAK} | {WEAK_PCT}% |
| Poor (20) | {POOR} | {POOR_PCT}% |
| None (0) | {NONE} | {NONE_PCT}% |

### Style Tests ({ST_COUNT} tests)

```
+------------------------------------------------------------------------------+
|  Composite Style Score: {ST_COMPOSITE}/100                                   |
|  Status: {ST_STATUS}                                                         |
+------------------------------------------------------------------------------+
```

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Vocabulary | {VOC}/100 | 25% | {VOC_W} |
| Rhetoric | {RHE}/100 | 25% | {RHE_W} |
| Tone | {TON}/100 | 20% | {TON_W} |
| Cadence | {CAD}/100 | 15% | {CAD_W} |
| Analogy | {ANA}/100 | 15% | {ANA_W} |

### Edge Case Tests ({EC_COUNT} tests)

```
+------------------------------------------------------------------------------+
|  Tests Passed: {EC_PASSED}/{EC_COUNT} ({EC_RATE}%)                           |
|  Status: {EC_STATUS}                                                         |
+------------------------------------------------------------------------------+
```

| Subtype | Total | Passed | Rate |
|---------|-------|--------|------|
| Paradox | {PAR_T} | {PAR_P} | {PAR_R}% |
| Nuance | {NUA_T} | {NUA_P} | {NUA_R}% |
| Contradiction | {CON_T} | {CON_P} | {CON_R}% |
| Evolution | {EVO_T} | {EVO_P} | {EVO_R}% |
| Boundary | {BND_T} | {BND_P} | {BND_R}% |

---

## FIDELITY DIMENSIONS

```
+------------------------------------------------------------------------------+
|                        FIDELITY DIMENSION SCORES                             |
+------------------------------------------------------------------------------+
|                                                                              |
|  Content    [{CONTENT_BAR}] {CONTENT}%  (weight: 30%)                        |
|  Linguistic [{LINGUISTIC_BAR}] {LINGUISTIC}%  (weight: 25%)                  |
|  Reasoning  [{REASONING_BAR}] {REASONING}%  (weight: 25%)                   |
|  Emotional  [{EMOTIONAL_BAR}] {EMOTIONAL}%  (weight: 10%)                    |
|  Paradox    [{PARADOX_BAR}] {PARADOX}%  (weight: 10%)                        |
|                                                                              |
|  COMPOSITE  [{COMPOSITE_BAR}] {COMPOSITE}%                                   |
|                                                                              |
+------------------------------------------------------------------------------+
```

| Dimension | Score | Weight | Weighted | Below 75%? |
|-----------|-------|--------|----------|------------|
| Content | {CONTENT}% | 0.30 | {CONTENT_W} | {CONTENT_FLAG} |
| Linguistic | {LINGUISTIC}% | 0.25 | {LINGUISTIC_W} | {LINGUISTIC_FLAG} |
| Reasoning | {REASONING}% | 0.25 | {REASONING_W} | {REASONING_FLAG} |
| Emotional | {EMOTIONAL}% | 0.10 | {EMOTIONAL_W} | {EMOTIONAL_FLAG} |
| Paradox | {PARADOX}% | 0.10 | {PARADOX_W} | {PARADOX_FLAG} |
| **COMPOSITE** | **{COMPOSITE}%** | **1.00** | **{COMPOSITE}** | -- |

---

## REGRESSION ANALYSIS

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Composite | {PREV_COMPOSITE}% | {COMPOSITE}% | {DELTA}% |
| Content | {PREV_CONTENT}% | {CONTENT}% | {DELTA_CONTENT}% |
| Linguistic | {PREV_LINGUISTIC}% | {LINGUISTIC}% | {DELTA_LINGUISTIC}% |
| Reasoning | {PREV_REASONING}% | {REASONING}% | {DELTA_REASONING}% |
| Emotional | {PREV_EMOTIONAL}% | {EMOTIONAL}% | {DELTA_EMOTIONAL}% |
| Paradox | {PREV_PARADOX}% | {PARADOX}% | {DELTA_PARADOX}% |

**Regression Detected:** {REGRESSION_DETECTED}
**Severity:** {REGRESSION_SEVERITY}

---

## WEAKEST DIMENSIONS

{WEAKNESS_ANALYSIS}

<!-- For each dimension below 75%, provide: -->
<!-- 1. Which test cases revealed the weakness -->
<!-- 2. Root cause analysis (what DNA gap causes this) -->
<!-- 3. Specific source material that could address the gap -->

---

## REMEDIATION PLAN

<!-- Only present if overall_result is CONDITIONAL_PASS or FAIL -->

| Priority | Dimension | Action | Deadline |
|----------|-----------|--------|----------|
| {PRIORITY} | {DIMENSION} | {ACTION} | {DEADLINE} |

---

## NOTABLE TEST RESULTS

### Strongest Performance

<!-- List 3-5 tests where the clone performed exceptionally well -->

| Test ID | Category | Score | Why Notable |
|---------|----------|-------|-------------|
| {TEST_ID} | {CATEGORY} | {SCORE} | {REASON} |

### Weakest Performance

<!-- List 3-5 tests where the clone performed poorly -->

| Test ID | Category | Score | Root Cause |
|---------|----------|-------|------------|
| {TEST_ID} | {CATEGORY} | {SCORE} | {CAUSE} |

### Trap Failures

<!-- List edge case tests where the clone fell into the "generic AI" trap -->

| Test ID | Subtype | Expected Position | Clone Gave |
|---------|---------|-------------------|------------|
| {TEST_ID} | {SUBTYPE} | {EXPECTED} | {CLONE_GAVE} |

---

## SOURCE MATERIALS USED

| Path | Type | Tests Generated |
|------|------|-----------------|
| {PATH} | {TYPE} | {COUNT} |

---

## APPENDIX: METHODOLOGY

- **Protocol:** Blind Testing Protocol v1.0.0 (`core/protocols/blind-testing-protocol.md`)
- **Schema:** `core/schemas/fidelity-report.schema.json`
- **Test Template:** `core/templates/validation/blind-test-template.yaml`
- **Composite Formula:** `(Content * 0.30) + (Linguistic * 0.25) + (Reasoning * 0.25) + (Emotional * 0.10) + (Paradox * 0.10)`
- **Classification:** EXCEPTIONAL (>=94%) | TARGET_MET (90-93%) | ACCEPTABLE (80-89%) | NEEDS_IMPROVEMENT (70-79%) | FAILING (<70%)

---

## SIGN-OFF

- **Test Administrator:** {ADMIN}
- **Date:** {DATE}
- **Next Scheduled Test:** {NEXT_TEST_DATE}

---

*Generated by Blind Testing Protocol v1.0.0*
*Schema: fidelity-report.schema.json*
