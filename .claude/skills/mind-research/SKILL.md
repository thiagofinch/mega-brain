---
name: mind-research
description: "Mind Research - Pesquisa iterativa de elite minds para qualquer domínio."---

# Mind Research

Pipeline multi-agente para pesquisa de elite minds usando Teams com agentes Mega Brain.

## Overview

```
/mind-research {domain} [--context "context"] [--must-include-local]

Phase 1: Broad Research       → @analyst (Merovingian)           → 01-broad-research.md
Phase 2: Devil's Advocate     → @analyst (Merovingian)           → 02-devils-advocate.md
Phase 3: Framework Validation → 3-4 @analyst (PARALLEL)    → 03-framework-validation.md
Phase 4: Cross-Reference      → @analyst (Merovingian) [optional] → 04-cross-reference.md
Phase 5: Final Synthesis      → @analyst (Merovingian)           → 05-final-report.md

Specialists:
- @knowledge-architect: Source quality assessment (Phase 1-2)
- @process-architect: Process checkpoint validation (Phase 3)

All Mega Brain agents use subagent_type: "mega-brain-analyst" (Context Parity v2.1).
```

## Input Collection

Collect from user (use AskUserQuestion if needed):

1. **Domain**: Qual área de expertise? (ex: copywriting, legal, HR)
2. **Context**: Contexto adicional? (ex: "for Brazilian startups")
3. **Must Include Local**: Incluir experts locais/regionais? (yes/no)
4. **Specific Needs**: Necessidades específicas? (ex: ["contracts", "tax"])

If the user already provided sufficient context in arguments, skip collection and start directly.

## Setup

### Artifact Directory

Create artifact output directory:

```
outputs/mind_research/{domain}/
```

Where `{domain}` is the domain name in snake_case (e.g., `copywriting`, `tax_law`).

### Team Creation

```
TeamCreate(team_name: "mind-research-{domain}")
```

### Task Creation (with dependencies)

Create 5 sequential tasks:

| ID | Task | Agent | subagent_type | Blocked By |
|----|------|-------|---------------|------------|
| 1 | Broad Research - Map universe of experts | analyst | mega-brain-analyst | - |
| 2 | Devil's Advocate - Question and refine | analyst | mega-brain-analyst | 1 |
| 3 | Framework Validation - Score and validate | analyst (parallel) | mega-brain-analyst | 2 |
| 4 | Cross-Reference - Verify and complete | analyst | mega-brain-analyst | 3 |
| 5 | Final Synthesis - Create elite list | analyst | mega-brain-analyst | 4 |

Note: Task 4 is optional and may be skipped if Phase 3 produces clean results.

## AGENT_MAP

```yaml
# Mapeamento: role -> subagent_type
AGENT_MAP:
  analyst: "mega-brain-analyst"              # Mega Brain: research, analysis, validation
  squad-architect: "mega-brain-analyst"      # Mega Brain: synthesis and final report (analyst role)
  knowledge-architect: "knowledge-architect"           # Custom: source quality (Phase 1-2 handoff)
  process-architect: "process-architect"       # Custom: process validation (Phase 3 handoff)
```

## Context Loading (Automatic)

Each Mega Brain agent wrapper (`.claude/agents/*.md`) automatically loads:
- Git status, branch, permissions
- Gotchas filtered by domain
- Technical preferences
- Project status

**No need to include context loading instructions in prompts** - the wrappers handle it.
Custom agents (knowledge-architect, process-architect, squad-architect) handle their own context.

## Execution Pattern (CRITICAL)

### How Agent Waiting Works

The `Task` tool has **native blocking behavior** - it automatically waits for the agent to complete before returning. You do NOT need any manual waiting mechanism.

### Sequential Phases (1, 2, 4, 5)

```
# Task tool WITHOUT run_in_background = BLOCKS until agent completes
Task(prompt: "...", subagent_type: "mega-brain-analyst", ...)
# ↑ This line does NOT return until the agent finishes
# ↓ When execution reaches here, the agent is DONE
TaskUpdate(taskId: "X", status: "completed")
```

### Parallel Phase (3 - Framework Validation)

```
# Spawn validation agents in a SINGLE message with run_in_background: true
# Start conservative with max 4 parallel agents
Task(prompt: "Validate Mind 1...", run_in_background: true, model: "haiku")  → returns id_1
Task(prompt: "Validate Mind 2...", run_in_background: true, model: "haiku")  → returns id_2
Task(prompt: "Validate Mind 3...", run_in_background: true, model: "haiku")  → returns id_3
Task(prompt: "Validate Mind 4...", run_in_background: true, model: "haiku")  → returns id_4

# Then wait for each using TaskOutput (blocks until agent completes)
TaskOutput(task_id: "id_1", block: true)
TaskOutput(task_id: "id_2", block: true)
TaskOutput(task_id: "id_3", block: true)
TaskOutput(task_id: "id_4", block: true

# If more than 4 minds, repeat for next batch
```

### NEVER DO THIS (Anti-Patterns)

```
# ❌ WRONG: Sleep loops
Bash("sleep 30")
Bash("sleep 60")

# ❌ WRONG: Polling loops
while not done:
    Bash("sleep 10")
    check_if_file_exists()

# ❌ WRONG: Periodic file checking
Read("output_file")  # hoping it appeared
Bash("sleep 30")
Read("output_file")  # checking again

# ❌ WRONG: Asking teammate for status via SendMessage polling
SendMessage("hey, are you done yet?")

# ❌ WRONG: Accepting mind without framework validation
# ❌ WRONG: Skipping Phase 2 (Devil's Advocate)
# ❌ WRONG: Auto-restarting phases on failure (escalate instead)
# ❌ WRONG: Trusting fame alone without documented frameworks
```

The Task tool handles ALL waiting automatically. Trust the blocking mechanism.

---

## Veto Conditions (MANDATORY)

These veto conditions MUST be enforced. They are not documentation - they are HARD BLOCKS.

### Phase 1 Vetos
```yaml
P1_V01:
  condition: "minds_count < 15"
  action: "VETO - Cannot proceed to Phase 2"
  message: "Need at least 15 names. Found: {count}"

P1_V02:
  condition: "any_mind has sources < 3"
  action: "FLAG - Needs more validation"
  message: "{mind_name} has only {count} sources"
```

### Phase 2 Vetos
```yaml
P2_V01:
  condition: "devils_advocate_questions_answered < 5"
  action: "VETO - Self-questioning incomplete"
  message: "Must answer at least 5 self-questioning prompts"

P2_V02:
  condition: "no_new_minds_added"
  action: "WARN - Review thoroughness"
  message: "Devil's advocate should surface at least 1-2 new names"

P2_V03:
  condition: "refined_count outside 8-12 range"
  action: "VETO - Invalid refinement"
  message: "Must refine to 8-12 names, found: {count}"
```

### Phase 3 Vetos (CRITICAL)
```yaml
P3_V01:
  condition: "any_mind.total_score < 10"
  action: "CUT from list"
  message: "{mind_name} failed validation ({score}/15)"

P3_V02:
  condition: "any_mind.framework_documented < 2"
  action: "CUT (absolute - no exceptions)"
  message: "{mind_name} has no documented framework"

P3_V03:
  condition: "passing_minds < 3"
  action: "ESCALATE to team lead"
  message: "Only {count} minds passed. Need human decision."

P3_V04:
  condition: "tier_0_count == 0"
  action: "WARN"
  message: "No Tier 0 (diagnostic) mind identified"
```

### Phase 5 Vetos
```yaml
P5_V01:
  condition: "final_count < 3 OR final_count > 5"
  action: "WARN"
  message: "Final list should be 3-5 minds, found: {count}"

P5_V02:
  condition: "tier_0_count == 0 in final"
  action: "ESCALATE"
  message: "No Tier 0 mind in final list. Squad needs diagnostic capability."
```

---

## Phase Execution

### Phase 1: Broad Research (@analyst / Merovingian)

Spawn 1 agent via Task tool:
- `subagent_type`: "mega-brain-analyst"
- `team_name`: "mind-research-{domain}"
- `name`: "analyst-phase1"
- `mode`: "bypassPermissions"

**Agent prompt:**

```
## Mission: broad-research

## Context
Domain: {domain}
Additional context: {context}
Include local experts: {must_include_local}
Specific needs: {specific_needs}

## Mission
Map the universe of experts in {domain}. Generate initial list of 15-20 names.

### Research Queries (use EXA web search)
- "best {domain} experts thought leaders"
- "top {domain} consultants frameworks"
- "most influential {domain} professionals"
- "{domain} methodology creators founders"
- "best {domain} books authors"
# If must_include_local:
- "best {domain} Brazil specialists"
- "{domain} Brazilian reference experts"

### Extract Per Result
For each expert found:
- name: Expert name
- title: Known title/position
- known_for: What they're known for
- has_framework: Has own framework/methodology? (yes/no/unknown)
- sources_found: Which sources mention this person (count)

### Specialist Handoff
After initial research, invoke @knowledge-architect for source quality assessment:
- Spawn @knowledge-architect with run_in_background: true
- Prompt: "Assess source quality for these {N} minds. Classify sources as ouro (gold) or bronze."
- Wait for response via TaskOutput

### Veto Conditions (ENFORCE)
- P1_V01: If minds_count < 15 → CANNOT proceed, return to research
- P1_V02: Flag any mind with sources < 3

## Output
Save complete result to: outputs/mind_research/{domain}/01-broad-research.md

Format:
# Broad Research - {domain}
## Executive Summary (5-7 lines)
## Initial Mapping (15-20 names)
| # | Name | Known for | Framework? | Sources | Source Quality |
## Source Quality Assessment (from @knowledge-architect)
## Observations
## Veto Check
- minds_count: {N} ✓/✗
- minds with sources < 3: {list}

After saving, send a message to the team lead with:
- Number of minds identified
- Source quality distribution (gold vs bronze)
- Any veto conditions triggered
```

The Task tool call above **blocks automatically** until the analyst agent completes.
When control returns to you, the agent is done. Then:
1. `TaskUpdate(taskId: "1", status: "completed")`
2. `TaskUpdate(taskId: "2", status: "in_progress")` (unblock next phase)
3. Proceed immediately to Phase 2.

---

### Phase 2: Devil's Advocate (@analyst / Merovingian)

Spawn 1 agent via Task tool:
- `subagent_type`: "mega-brain-analyst"
- `team_name`: "mind-research-{domain}"
- `name`: "analyst-phase2"
- `mode`: "bypassPermissions"

**Agent prompt:**

```
## Mission: devils-advocate

## Context
Domain: {domain}

## Input from Previous Phase
Read: outputs/mind_research/{domain}/01-broad-research.md

## Mission
Question your own research, find who's missing. Refine to 10-12 names.

### Self-Questioning (MUST answer at least 5)
1. "Why {Expert A} and not {Expert B}?"
2. "Who would criticize this list? Why?"
3. "Who are the contrarians in {domain}?"
4. "Who is doing innovative work but isn't famous yet?"
5. "Is the list too American/Eurocentric?"
6. "Is any niche underrepresented?"

### Additional Research Queries
- "critics of {expert_names} methodology"
- "alternatives to {popular_framework}"
- "{domain} contrarian experts different approach"
- "underrated {domain} experts hidden gems"
- "who disagrees with {top_expert} {domain}"

### Heuristic: SC_DA_001 - Devil's Advocate Cut/Keep
Apply this decision heuristic:

Weights:
- source_mentions: 0.8
- original_work: 0.9
- practical_results: 0.9
- framework_documented: 1.0 (VETO power)

Thresholds:
- source_mentions: >= 3
- original_work: true
- practical_results: true

Decision Tree:
- IF sources < 2 → CUT (insufficient validation)
- ELSE IF is_popularizer_only → CUT (no original work)
- ELSE IF no_practical_evidence → REVIEW (needs more research)
- ELSE → KEEP (proceed to Phase 3)

### Veto Conditions (ENFORCE)
- P2_V01: devils_advocate_questions_answered < 5 → VETO
- P2_V02: no_new_minds_added → WARN
- P2_V03: refined_count outside 8-12 → VETO

## Output
Save complete result to: outputs/mind_research/{domain}/02-devils-advocate.md

Format:
# Devil's Advocate - {domain}
## Executive Summary
## Self-Questioning Responses (5+ questions answered)
## Names Added (weren't in initial list)
| Name | Why they were missing | Relevance |
## Names Questioned and Cut
| Name | Questioning | Decision | Heuristic Applied |
## Refined List (10-12 names)
| # | Name | Score | Status |
## Veto Check
- questions_answered: {N} ✓/✗
- new_minds_added: {N}
- refined_count: {N} ✓/✗

After saving, send a message to the team lead with:
- Names added through devil's advocate
- Names cut and why
- Final count for Phase 3
```

The Task tool call above **blocks automatically** until the analyst agent completes.
When control returns to you, the agent is done. Then:
1. `TaskUpdate(taskId: "2", status: "completed")`
2. `TaskUpdate(taskId: "3", status: "in_progress")` (unblock next phase)
3. Proceed immediately to Phase 3.

---

### Phase 3: Framework Validation (PARALLEL @analyst)

This phase is **parallel** - spawn multiple agents simultaneously (max 4 at a time).

Read 02-devils-advocate.md to get the list of 10-12 minds to validate.
Spawn 1 validation agent per mind, up to 4 in parallel.

Spawn agents in parallel via Task tool, all with:
- `subagent_type`: "mega-brain-analyst"
- `team_name`: "mind-research-{domain}"
- `mode`: "bypassPermissions"
- `model`: "haiku" (lighter model for structured validation)

**Validation Agent prompt template:**

```
## Mission
Validate {mind_name} against framework validation criteria.

### Research Queries
- "{mind_name} methodology framework"
- "{mind_name} process step by step"
- "{mind_name} book template checklist"
- "{mind_name} case study results"

### Scoring Criteria (0-3 scale each)
1. framework_documented: Has methodology/framework with own name?
   - 0: No framework
   - 1: Vague methodology
   - 2: Named framework
   - 3: Complete, documented framework

2. process_extractable: Is there a documented step-by-step process?
   - 0: No process
   - 1: High-level steps
   - 2: Detailed process
   - 3: Replicable playbook

3. artifacts_available: Has extractable templates, checklists, frameworks?
   - 0: None
   - 1: Few examples
   - 2: Multiple artifacts
   - 3: Comprehensive toolkit

4. examples_exist: Are there application examples?
   - 0: No examples
   - 1: Anecdotal
   - 2: Case studies
   - 3: Verified results with metrics

5. material_accessible: Is the material accessible (books, courses, articles)?
   - 0: Not accessible
   - 1: Hard to find
   - 2: Available
   - 3: Widely accessible

### Tier Classification
Based on validation, assign tier:
- Tier 0 (Diagnosis): Creates diagnostic/audit frameworks, analytical focus
- Tier 1 (Masters): Proven track record ($XXM+ results), original methodology
- Tier 2 (Systematizers): Creates teachable frameworks, process-oriented
- Tier 3 (Specialists): Format/channel specific expertise

### Heuristic: SC_FV_001 - Framework Validation Gate
Weights:
- framework_documented: 1.0 (VETO power)
- process_extractable: 0.9
- artifacts_available: 0.8
- examples_exist: 0.8
- material_accessible: 0.7

Veto Conditions:
- IF framework_documented < 2 → VETO (no replicable methodology)
- IF total_score < 10 → VETO (insufficient documentation)

## Output
Save to: outputs/mind_research/{domain}/03-validations/{mind_slug}.md

Format:
# Validation: {mind_name}
## Summary
- Total Score: {X}/15
- Status: PASS/FAIL
- Tier: {0/1/2/3}

## Scoring Breakdown
| Criterion | Score | Evidence |
|-----------|-------|----------|
| framework_documented | X/3 | {evidence} |
| process_extractable | X/3 | {evidence} |
| artifacts_available | X/3 | {evidence} |
| examples_exist | X/3 | {evidence} |
| material_accessible | X/3 | {evidence} |

## Known For
## Main Framework
## Available Material
## Recommendation
```

**Parallel Execution (CRITICAL):**

1. Spawn up to 4 agents in a **single message** using 4 `Task` calls with `run_in_background: true`
2. Collect the 4 `task_id` values returned
3. Use `TaskOutput(task_id: "id", block: true)` for each to wait
4. After all 4 TaskOutput calls return, repeat for next batch if needed

**After all validations complete:**

1. Read all validation files from `outputs/mind_research/{domain}/03-validations/`
2. Invoke @process-architect for checkpoint validation:
   - Prompt: "Audit the Framework Validation results. Check veto conditions. Identify any process failures."
3. Consolidate into `outputs/mind_research/{domain}/03-framework-validation.md`:

```markdown
# Framework Validation - {domain}

## Executive Summary
- Minds Validated: {N}
- Passed: {N}
- Failed: {N}
- Tier 0: {N}

## Validation Results
| Expert | Score | Status | Tier | Veto Condition |
|--------|-------|--------|------|----------------|

## Process Validation (from @process-architect)
{checkpoint validation results}

## Cut Due to Lack of Documentation
| Expert | Reason | Veto Condition |

## Veto Check
- P3_V01: minds with score < 10: {list}
- P3_V02: minds with framework_documented < 2: {list}
- P3_V03: passing_minds: {N} ✓/✗
- P3_V04: tier_0_count: {N}
```

Then:
1. `TaskUpdate(taskId: "3", status: "completed")`
2. `TaskUpdate(taskId: "4", status: "in_progress")` (unblock next phase)
3. Proceed to Phase 4 (or skip to Phase 5 if results are clean)

---

### Phase 4: Cross-Reference (Optional, @analyst / Merovingian)

**Condition:** Only execute if:
- More than 6 minds passed Phase 3, OR
- Doubts remain about completeness, OR
- @process-architect flagged issues

If conditions not met, skip to Phase 5.

Spawn 1 agent via Task tool:
- `subagent_type`: "mega-brain-analyst"
- `team_name`: "mind-research-{domain}"
- `name`: "analyst-phase4"
- `mode`: "bypassPermissions"

**Agent prompt:**

```
## Mission: cross-reference

## Input from Previous Phases
Read: outputs/mind_research/{domain}/01-broad-research.md
Read: outputs/mind_research/{domain}/02-devils-advocate.md
Read: outputs/mind_research/{domain}/03-framework-validation.md

## Mission
Validate through multiple perspectives. Verify reputation and check for omissions.

### Cross-Reference Checks
- Appears in "best of" lists from multiple sources?
- Cited by other domain experts?
- Has verifiable track record?
- Results are verifiable?

### Final Questions
- Did we miss anyone obvious that any domain expert would mention?
- Does the list cover different approaches/schools in the domain?
- Is there sufficient diversity (geographic, approach)?

## Output
Save to: outputs/mind_research/{domain}/04-cross-reference.md

Format:
# Cross-Reference - {domain}
## Verification Results
## Obvious Omissions Check
## Diversity Assessment
## Final Recommendations
```

---

### Phase 5: Final Synthesis (@analyst)

Spawn 1 agent via Task tool:
- `subagent_type`: "mega-brain-analyst"
- `team_name`: "mind-research-{domain}"
- `name`: "analyst-phase5"
- `mode`: "bypassPermissions"

**Agent prompt:**

```
## Mission: final-synthesis

You are acting as a squad architect for this final synthesis phase.
Reference the squad architecture guidelines from: squads/squad-creator/agents/squad-architect.md

## Inputs from ALL Previous Phases
Read ALL files in: outputs/mind_research/{domain}/
- 01-broad-research.md
- 02-devils-advocate.md
- 03-framework-validation.md
- 04-cross-reference.md (if exists)

## Mission
Create the final elite mind research report.

### Tiebreakers (if more than 5 minds)
Apply in order:
1. Who has the most documented material?
2. Who has the most recent success cases?
3. Who has the most complete framework?
4. Who best complements others on the list?

### Tier Distribution Requirements
- At least 1 Tier 0 (diagnostic capability)
- Core should be Tier 1 masters
- Support with Tier 2 systematizers

### Veto Conditions (ENFORCE)
- P5_V01: final_count outside 3-5 → WARN
- P5_V02: tier_0_count == 0 → ESCALATE

## Output
Save complete result to: outputs/mind_research/{domain}/05-final-report.md

Format:
# Mind Research Report: {Domain}

**Generated:** {date}
**Domain:** {domain}
**Context:** {context}
**Iterations executed:** {phases completed}

---

## Executive Summary
{Paragraph summarizing research and conclusions}

---

## Final Elite: {N} Selected Minds

### Tier Distribution
| Tier | Minds | Role |
|------|-------|------|
| Tier 0 | {names} | Diagnosis/Audit - ALWAYS first |
| Tier 1 | {names} | Core Masters - Primary execution |
| Tier 2 | {names} | Systematizers - Frameworks |
| Tier 3 | {names} | Specialists - Format-specific |

---

### 1. {Expert Name}
- **Tier:** {0|1|2|3}
- **Known for:** {description}
- **Main Framework:** {framework name}
- **Why include:** {justification}
- **Quality Score:** {X}/15
- **Available Material:**
  - {book/course/article 1}
  - {book/course/article 2}

[Repeat for each expert]

---

## Minds Considered but Not Selected
| Expert | Reason for Exclusion |

---

## Next Steps
For each selected mind, execute:
1. `/clone-mind {mind_name}` - Clone mind DNA
2. Agent creation via squad-creator

---

## Research Metadata
| Metric | Value |
|--------|-------|
| Initial names mapped | {N} |
| After devil's advocate | {N} |
| After framework validation | {N} |
| Final elite | {N} |
| Phases executed | {N} |
| Specialists invoked | @knowledge-architect, @process-architect |

After saving, send a message to the team lead with:
- Final count and tier distribution
- Top recommendation for squad creation
```

The Task tool call above **blocks automatically** until the analyst agent completes.
When control returns to you, the agent is done. Then:
1. `TaskUpdate(taskId: "5", status: "completed")`
2. Proceed to Finalization.

---

## Finalization

After Phase 5 completes:

1. **Present summary** to user:
   - Links to all generated artifacts
   - Final elite list with tier distribution
   - Recommended next steps

2. **Cleanup**:
   - Send shutdown_request to all remaining agents
   - Execute TeamDelete after all agents shut down

3. **Final summary format**:

```markdown
## Mind Research Complete: {domain}

### Generated Artifacts
- `outputs/mind_research/{domain}/01-broad-research.md` - Initial mapping
- `outputs/mind_research/{domain}/02-devils-advocate.md` - Refined list
- `outputs/mind_research/{domain}/03-framework-validation.md` - Validated minds
- `outputs/mind_research/{domain}/04-cross-reference.md` - Cross-validation (if executed)
- `outputs/mind_research/{domain}/05-final-report.md` - Final elite list

### Final Elite: {N} Minds
| # | Name | Tier | Score |
|---|------|------|-------|

### Tier Distribution
- Tier 0 (Diagnostic): {N} minds
- Tier 1 (Masters): {N} minds
- Tier 2 (Systematizers): {N} minds

### Next Steps
1. Review final report at `05-final-report.md`
2. For each mind: `/clone-mind {name}` to extract DNA
3. Create agents via squad-creator workflow
```

## Implementation Notes

- Each spawned agent runs in its own context (no shared memory)
- Communication between phases is via FILES (not messages)
- The team lead coordinates and ensures quality between phases
- If an agent fails, recreate the task and re-spawn the agent
- Phase 3 validation agents run in PARALLEL (max 4 at a time) for efficiency
- Use `model: "haiku"` for Phase 3 validation agents (lighter, faster)
- Always use `mode: "bypassPermissions"` for agents that need to read/write files
- @knowledge-architect provides source quality assessment in Phase 1-2
- @process-architect validates process checkpoints in Phase 3

## Migration from wf-mind-research-loop.yaml

### Path Changes
```
Old: outputs/research/{domain}-minds-research.md
New: outputs/mind_research/{domain}/05-final-report.md
```

### Invocation Changes
```
Old: @squad-architect interprets wf-mind-research-loop.yaml
New: Direct invocation via /mind-research {domain}
```

### Dependent Workflows
Update these to use new paths:
- `wf-clone-mind.yaml`: Update input path
- Any automation reading from `outputs/research/`
