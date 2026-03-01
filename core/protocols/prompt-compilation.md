# Protocol: DNA to System Prompt Compilation

> **Version:** 1.0.0
> **Date:** 2026-02-28
> **Purpose:** Step-by-step protocol for compiling 8-layer DNA into production-ready LLM system prompts
> **Input:** Extracted DNA (dna-mental-8-layer.schema.json) + communication-patterns.yaml
> **Output:** 1 Generalista prompt + 3-5 Specialist prompts per person
> **Templates Used:** system-prompt-generalista.md, system-prompt-specialist.md, communication-patterns.yaml

---

## Overview

This protocol governs the compilation process that transforms raw extracted DNA into
deployable system prompts. It is the final step in the pipeline: after DNA extraction
and enrichment are complete, this protocol produces the artifacts that make the mind
clone operational in any LLM.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPILATION PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCE MATERIALS                                                           │
│       │                                                                     │
│       ▼                                                                     │
│  [Pipeline Phases 1-4] ── Extraction, chunking, insight generation         │
│       │                                                                     │
│       ▼                                                                     │
│  8-LAYER DNA (dna-mental-8-layer.schema.json)                              │
│  + COMMUNICATION PATTERNS (communication-patterns.yaml)                    │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              THIS PROTOCOL (prompt-compilation.md)                   │   │
│  │                                                                     │   │
│  │  Phase 1: Readiness Check                                           │   │
│  │  Phase 2: Generalista Compilation                                   │   │
│  │  Phase 3: Specialist Planning                                       │   │
│  │  Phase 4: Specialist Compilation (x3-5)                             │   │
│  │  Phase 5: Validation                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  OUTPUTS:                                                                   │
│  ├── 1x Generalista system prompt (all 8 layers, all domains)              │
│  ├── 3-5x Specialist system prompts (L1-5, domain-filtered)               │
│  └── 1x Communication patterns profile                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Readiness Check

Before compiling, verify the DNA is ready.

### 1.1 Layer Completeness Thresholds

| Layer | Minimum for Generalista | Minimum for Specialist |
|-------|------------------------|----------------------|
| L1 Philosophies | 60% | 40% (domain-filtered) |
| L2 Mental Models | 50% | 30% (domain-filtered) |
| L3 Heuristics | 60% | 50% (domain-filtered) |
| L4 Frameworks | 50% | 40% (domain-filtered) |
| L5 Methodologies | 40% | 30% (domain-filtered) |
| L6 Values Hierarchy | 30% | Not required |
| L7 Core Obsessions | 50% | Not required |
| L8 Productive Paradoxes | 20% | Not required |

### 1.2 Communication Patterns Minimum

- At least 5 signature phrases captured
- Tone profile complete (all fields populated)
- At least 1 metaphor family identified
- At least 1 rhetoric pattern documented

### 1.3 Readiness Checklist

```
[ ] DNA file exists and validates against schema
[ ] Layer completeness meets thresholds above
[ ] communication-patterns.yaml exists and is populated
[ ] At least 3 sources processed (minimum for triangulation)
[ ] L8 human_validated flag checked (note status for compilation)
```

**If readiness fails:** Document which layers are below threshold and what additional
source material would be needed to reach minimum completeness.

---

## Phase 2: Generalista Compilation

### 2.1 Open Template

Use `core/templates/agents/system-prompt-generalista.md` as the template.

### 2.2 Compile Each Block

Execute in order:

**BLOCK 1 - IDENTITY:**
1. Read all L7_core_obsessions items. Write identity narrative weaving obsessions into first-person voice.
2. Read all L1_philosophies items. Group by domain, write in first person. Cap at 15 items, sorted by confidence descending.
3. Read all L8_productive_paradoxes items. Include ONLY items where `validation_status == "human_confirmed"` OR `confidence >= 0.85`. If `human_validated == false` on the layer, add disclaimer.

**BLOCK 2 - REASONING:**
1. Read all L2_mental_models items. Include trigger_questions. Group by domain. Cap at 12 items.
2. Read all L4_frameworks items. Include components and output. Group by domain. Cap at 10 items.

**BLOCK 3 - DECISIONS:**
1. Read all L3_heuristics items. Mark each as QUANTITATIVE or QUALITATIVE. Prioritize quantitative. Include thresholds, when_to_apply, when_not_to_apply. Cap at 20 items.
2. Read all L6_values_hierarchy items. Present in rank order. Include one trade_off_evidence example per value.

**BLOCK 4 - COMMUNICATION:**
1. Pull from communication-patterns.yaml. Include signature phrases, tone rules, rhetoric patterns, metaphor families, forbidden patterns.

**BLOCK 5 - KNOWLEDGE:**
1. Read all L5_methodologies items. Include full steps with success_criteria. Include ALL matching items.
2. Compile cross_layer_links into reference table. Cap at 15 most important links.

### 2.3 Token Budget Check

Target: 4,000-8,000 tokens. If exceeding 8,000, prune lowest-confidence items first, starting from the largest block.

### 2.4 Run Compilation Checklist

Use the 22-point checklist from system-prompt-generalista.md. All items must pass.

---

## Phase 3: Specialist Planning

### 3.1 Domain Inventory

List all unique domains present across L1-L5 items in the DNA.

### 3.2 Viability Assessment

For each domain, count:
- L3 heuristics in domain: need >= 3
- L5 methodologies in domain: need >= 1

A specialist is **viable** if it meets both thresholds.

### 3.3 Role Assignment

For each viable domain, select the most appropriate specialist role from the standard list (Copywriter, Strategist, Sales Coach, Mentor, Operator) or define a custom role.

### 3.4 Output: Specialist Plan

```
Person: {{PERSON_NAME}}
Viable Specialists:
1. [Role] - [Domain] - L3: N heuristics, L5: N methodologies
2. [Role] - [Domain] - L3: N heuristics, L5: N methodologies
3. [Role] - [Domain] - L3: N heuristics, L5: N methodologies

Non-viable domains (kept in Generalista only):
- [Domain] - L3: N (below threshold), L5: N
```

---

## Phase 4: Specialist Compilation

Repeat for each viable specialist:

### 4.1 Open Template

Use `core/templates/agents/system-prompt-specialist.md`.

### 4.2 Domain Filter

For each of L1-L5, filter items where `domain` matches the specialist's domain. Include items with confidence >= 0.70 only.

### 4.3 Compile Sections

1. Write role definition (description, boundaries, output format).
2. Compile domain-filtered L1 philosophies.
3. Compile domain-filtered L2 mental models with trigger questions.
4. Compile domain-filtered L3 heuristics with thresholds.
5. Compile domain-filtered L4 frameworks with components.
6. Compile domain-filtered L5 methodologies with full steps.
7. Pull domain-specific communication from communication-patterns.yaml `domain_overrides`.

### 4.4 Token Budget Check

Target: 2,000-4,000 tokens per specialist.

### 4.5 Run Compilation Checklist

Use the 17-point checklist from system-prompt-specialist.md.

---

## Phase 5: Validation

### 5.1 Cross-Prompt Consistency

Verify that no specialist contradicts the generalista. The specialist is a strict subset.

### 5.2 Voice Consistency

Read each compiled prompt aloud (or simulate). Does it sound like the person? Check against communication-patterns.yaml.

### 5.3 Coverage Check

Verify that every L3 heuristic and L5 methodology appears in at least one output (generalista or a specialist).

### 5.4 Final Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FINAL VALIDATION CHECKLIST                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [ ] Generalista compiled and passes 22-point checklist                    │
│  [ ] 3-5 specialists compiled, each passing 17-point checklist             │
│  [ ] No specialist contradicts generalista content                         │
│  [ ] Voice sounds authentic across all prompts                             │
│  [ ] Every heuristic and methodology appears in at least one prompt        │
│  [ ] Token budgets respected (generalista 4-8K, specialists 2-4K each)    │
│  [ ] L8 disclaimer present if human_validated == false                     │
│  [ ] Metadata sections complete with accurate counts                       │
│  [ ] All compilation artifacts saved to person's agent directory            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Output File Locations

Compiled prompts are saved alongside the agent's existing files:

```
agents/persons/{{person-name}}/
├── AGENT.md                              # Existing
├── SOUL.md                               # Existing
├── MEMORY.md                             # Existing
├── DNA-CONFIG.yaml                       # Existing
└── prompts/                              # NEW - compiled prompts
    ├── generalista.md                    # Full mind clone prompt
    ├── specialist-{{role-1}}.md          # Domain specialist 1
    ├── specialist-{{role-2}}.md          # Domain specialist 2
    ├── specialist-{{role-3}}.md          # Domain specialist 3
    └── COMPILATION-LOG.md                # Audit trail of compilation
```

---

## Compatibility

| Artifact | Version | Status |
|----------|---------|--------|
| dna-mental-8-layer.schema.json | 1.0.0 | Required |
| SOUL-TEMPLATE.md | 2.0 | Compatible (SOUL feeds communication block) |
| DNA-CONFIG-TEMPLATE.yaml | 2.0.0 | Compatible (sources feed metadata) |
| AGENT-INTEGRITY-PROTOCOL | 1.2.1 | Enforced (traceability rules apply) |

---

*Protocol: prompt-compilation.md v1.0.0*
*See also: system-prompt-generalista.md, system-prompt-specialist.md, communication-patterns.yaml*
