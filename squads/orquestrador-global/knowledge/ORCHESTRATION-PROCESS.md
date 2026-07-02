# ORCHESTRATION PROCESS

## Overview

This document defines the end-to-end orchestration process for the orquestrador-global squad. It covers the complete lifecycle from receiving a demand through multi-squad execution to consolidated delivery, with specific patterns for different orchestration scenarios.

---

## The Orchestration Pipeline

```
RECEIVE         CLASSIFY          PLAN             EXECUTE          REVIEW           DELIVER
  |                |                |                 |                |                |
  v                v                v                 v                v                v
Parse            Intent +         Build             Sequential/      Stage Gate       Consolidate
Request          Scale            Execution         Parallel         Quality          + Archive
                 Assess           Plan              Routing          Checkpoint
```

### Phase 1: Receive Demand

Every orchestration begins with a demand. Sources:

| Source | Format | Routing |
|--------|--------|---------|
| User prompt | Natural language | Parse intent from conversation |
| Star command | *plan, *execute, *execute-team | Direct pipeline trigger |
| Webhook | JSON payload | Pre-classified by sender |
| Squad referral | "I need help from another squad" | Cross-squad routing |
| Scheduled trigger | Cron-based | Pre-configured pipeline |

**Parsing protocol:**
1. Extract the core request (what the user wants)
2. Identify explicit constraints (budget, deadline, platform)
3. Detect implicit requirements (brand alignment, audience targeting)
4. Check for context from previous sessions (SuperMemory recall)

### Phase 2: Classify

Classification produces three outputs:

1. **Intent**: What type of work is this?
2. **Scale**: How complex is the execution?
3. **Squad map**: Which squads are needed?

**Intent Classification:**

| Intent Category | Example Requests | Typical Squads |
|-----------------|-----------------|----------------|
| Content creation | "Create a landing page" | funnel-creator, copywriting, design-system |
| Campaign launch | "Launch a new ad campaign" | creative-studio, media-buy, data-analytics |
| Analysis/research | "Analyze our competitors" | deep-scraper, data-analytics, conselho |
| Technical work | "Set up a webhook" | full-stack-dev, core-dev |
| Process setup | "Configure our ClickUp" | project-management-clickup |
| Full pipeline | "I want to sell a new product" | Multiple (5-8 squads) |

**Scale Assessment (IDS-8):**

```bash
node core/scripts/ops/ids-ops.mjs assess "description of the demand"
```

| Scale | Squads | Agents | Duration | Gate Level |
|-------|--------|--------|----------|------------|
| QUICK | 1 | 1-2 | Minutes | None |
| SMALL | 1 | 2-3 | Hours | Advisory |
| MEDIUM | 2-3 | 5-8 | Days | Soft block |
| LARGE | 3-5 | 8-14 | Week | Hard block |
| EPIC | 5-10 | 20-40 | Weeks | Multi-stage |
| MEGA | 10+ | 40-100 | Months | Full PMO |

### Phase 3: Plan Execution

For MEDIUM+ tasks, create an execution plan before starting:

**Plan Template:**
```markdown
# Execution Plan: {Title}

## Demand
{Original user request}

## Squads
| # | Squad | Role | Dependencies |
|---|-------|------|-------------|
| 1 | {squad} | {what it does} | None |
| 2 | {squad} | {what it does} | Squad 1 output |

## Execution Flow
{Sequential, parallel, fan-out, fan-in pattern}

## Gates
- After Stage 1: {criteria}
- After Stage 2: {criteria}

## Estimated Duration
{Total time estimate}
```

**Approval protocol:**
- QUICK/SMALL: No approval needed, execute immediately
- MEDIUM: Show plan, auto-approve unless user objects within 30s
- LARGE/EPIC/MEGA: Show plan, wait for explicit user approval

### Phase 4: Execute

Execute the plan by activating squads in the planned sequence.

**Execution Protocol:**
1. Create execution directory: `.data/executions/YYYY-MM-DD_slug/`
2. Write `00-master-plan.md`
3. Set session scale: `node core/scripts/ops/ids-ops.mjs set-scale {SCALE}`
4. For each stage:
   a. Write `{NN}-{squad}-input.md` with briefing
   b. Activate squad agent
   c. Capture output in `{NN}-{squad}-output.md`
   d. Run gate check if applicable
   e. Append to audit trail
5. On completion: write `99-execution-summary.md`

**Handoff Packaging:**

Each squad receives a structured briefing:

```markdown
## Briefing for {Squad}

### What to Do
{Clear description of the deliverable}

### Context
{Relevant context from previous stages}

### Inputs
{Files, data, or previous squad outputs to use}

### Constraints
{Brand guidelines, budget limits, technical requirements}

### Expected Output
{What the deliverable should look like}

### Deadline
{When this stage needs to be complete}
```

### Phase 5: Gate Review

Quality checkpoints between stages:

| Gate Type | When | Criteria | Failure Action |
|-----------|------|----------|---------------|
| Auto-pass | QUICK/SMALL tasks | Output exists and is non-empty | Retry once |
| Advisory | MEDIUM tasks | Completeness check | Warn and proceed |
| Soft block | LARGE tasks | Quality + completeness | Require revision |
| Hard block | EPIC/MEGA tasks | Full quality review + approval | Halt until approved |

**Gate Review Protocol:**
1. Check output against gate criteria
2. If pass: proceed to next stage
3. If fail: send revision notes to squad with specific deficiencies
4. Squad revises and resubmits
5. Maximum 2 revision cycles before escalation

### Phase 6: Deliver

Consolidate all outputs into the final delivery:

1. Assemble all squad outputs into a coherent package
2. Run consistency check across outputs (naming, tone, data accuracy)
3. Write execution summary with per-squad quality scores
4. Archive execution directory
5. Save summary to SuperMemory for future reference

---

## Orchestration Patterns

### Pattern 1: Sequential Pipeline

```
Squad A -> Squad B -> Squad C -> Delivery
```

**When to use**: Each squad's output is the next squad's input.
**Example**: Research -> Copywriting -> Funnel Builder -> Deploy

### Pattern 2: Parallel Fan-Out

```
         +-> Squad A --+
Brief -->|             |--> Assembly -> Delivery
         +-> Squad B --+
```

**When to use**: Multiple squads can work independently from the same brief.
**Example**: Brief -> Copy + Design + Vídeo -> Final Page

### Pattern 3: Diamond (Fan-Out + Fan-In)

```
         +-> Squad A --+
Brief -->|             |--> Gate -> Squad D -> Delivery
         +-> Squad B --+
         +-> Squad C --+
```

**When to use**: Multiple independent outputs feed into a final assembly squad.

### Pattern 4: Iterative Loop

```
Squad A -> Review -> [Pass] -> Delivery
              |
              +-> [Fail] -> Squad A (revise)
```

**When to use**: Output needs quality validation before proceeding.

---

## Error Handling

| Error Type | Detection | Response |
|------------|-----------|----------|
| Squad timeout | No output after expected duration | Alert user, extend or reassign |
| Quality gate failure | Output does not meet criteria | Send revision notes, max 2 retries |
| Squad not available | Agent activation fails | Fallback to alternative squad or defer |
| Dependency failure | Upstream squad output is incomplete | Block downstream, notify |
| Budget exceeded | IDS-11 cost check | Pause execution, alert user |
| Circuit breaker open | Too many failures in pipeline | Halt pipeline, manual review |
| External access/tool blocker | Login required, rate limit, missing credential, missing tool/service | Apply `BLOCKER-RESOLUTION-PROTOCOL.md` before returning to user |

### Active Blocker Resolution

The orchestrator must not stop at "blocked" when the blocker is solvable through tools, services, credentials or capability routing.

Required sequence:

1. Confirm the blocker with evidence.
2. Try local no-approval workarounds.
3. Search existing capabilities in squads, skills, services, apps and packages.
4. Rank external service candidates when local/repo capability is insufficient.
5. Ask for approval only when credentials, cookies, paid services, login or compliance risk are required.
6. Persist `blocker-resolution-report.md` for MEDIUM+ or recurring blockers.

Canonical reference: `knowledge/BLOCKER-RESOLUTION-PROTOCOL.md`.
Operational task: `tasks/resolve-external-blocker.yaml`.

Final status may be `blocked` only after the resolution ladder has been attempted or an approval-gated option has been presented.

---

## Execution Logging Standard

Every execution produces these files:

```
.data/executions/YYYY-MM-DD_slug/
  |-- 00-master-plan.md        # Approved execution plan
  |-- 01-{squad}-input.md      # Briefing for first squad
  |-- 01-{squad}-output.md     # Output from first squad
  |-- 02-{squad}-input.md      # Briefing for second squad
  |-- 02-{squad}-output.md     # Output from second squad
  |-- ...
  |-- 99-execution-summary.md  # Consolidated summary
  |-- audit.jsonl              # Machine-readable audit trail
```

---

*Process version 1.0.0 -- Created 2026-03-11*
