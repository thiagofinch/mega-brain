# Extracted from: .claude/skills/roundtable/SKILL.md (ATM-RT-008: Generate Report)
# Part of: SP-ROUNDTABLE process
# Version: 1.1.0

# Roundtable Review — {subject}

> **Date:** {date}
> **Mode:** {mode}
> **Participants:** {agent_list}
> **Verdict:** {verdict} ({score}/10)
> **Debate Rounds:** {round_count}

---

## Verdicts Summary

| Agent | Verdict | Score | Key Finding |
|-------|---------|-------|-------------|
| {agent_name} | {agent_verdict} | {agent_score} | {key_finding} |

## Consolidated Findings (Deduplicated)

### BLOCKER

| # | Finding | Agents | Recommendation |
|---|---------|--------|----------------|
| {n} | {finding} | {agents} | {recommendation} |

### CRITICAL

| # | Finding | Agents | Recommendation |
|---|---------|--------|----------------|
| {n} | {finding} | {agents} | {recommendation} |

### HIGH

| # | Finding | Agents | Recommendation |
|---|---------|--------|----------------|
| {n} | {finding} | {agents} | {recommendation} |

### MEDIUM

| # | Finding | Agents | Recommendation |
|---|---------|--------|----------------|
| {n} | {finding} | {agents} | {recommendation} |

### LOW

| # | Finding | Agents | Recommendation |
|---|---------|--------|----------------|
| {n} | {finding} | {agents} | {recommendation} |

## Consensus Points (agreed by 2+ agents)

| # | Point | Agents | Severity |
|---|-------|--------|----------|
| {n} | {point} | {agents} | {severity} |

## Metrics Dashboard (for epic subjects)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| {metric} | {value} | {target} | {status} |

## Resolved Conflicts

| Conflict | Agent A | Agent B | Resolution | Basis |
|----------|---------|---------|------------|-------|
| {conflict} | {agent_a_position} | {agent_b_position} | {resolution} | {basis} |

## Unresolved (Escalated to User)

| # | Conflict | Agent A | Agent B | Recommendation |
|---|----------|---------|---------|----------------|
| {n} | {conflict} | {agent_a_position} | {agent_b_position} | {recommendation} |

## Extracted Stories (if BLOCKER/CRITICAL represent new work)

| # | Story Title | Source Finding | Suggested Epic | Severity |
|---|-------------|----------------|----------------|----------|
| {n} | {story_title} | {source_finding} | {suggested_epic} | {severity} |

## Action Plan

| # | Action | Severity | Applies To | Owner |
|---|--------|----------|------------|-------|
| {n} | {action} | {severity} | {applies_to} | {owner} |

## Final Verdict

**Score:** {score}/10 | **Status:** {verdict} | **Rounds:** {round_count}

---

*Artifact lifecycle: draft > validated > approved > stale (after 90 days) > archived*
