# Extracted from: .claude/skills/roundtable/SKILL.md (ATM-RT-008 + decision mode sections)
# Part of: SP-ROUNDTABLE process
# Version: 1.1.0

# Roundtable Decision — {subject}

> **Date:** {date}
> **Mode:** decision
> **Participants:** {agent_list}
> **Verdict:** {verdict}
> **Debate Rounds:** {round_count}

**Verdict Model:** DECIDED | SPLIT | ESCALATED

---

## Options Evaluated

| # | Option | Description |
|---|--------|-------------|
| {n} | {option_name} | {option_description} |

## Agent Evaluations

### {agent_name} ({persona})

| Option | Pros | Cons | Risk | Vote |
|--------|------|------|------|------|
| {option_name} | {pros} | {cons} | {risk} | {vote} |

**Recommended Option:** {option}
**Justification:** {why}

---

## Verdicts Summary

| Agent | Recommended Option | Confidence | Key Justification |
|-------|-------------------|------------|-------------------|
| {agent_name} | {option} | {confidence} | {justification} |

## Decisions Table

| # | Decision | Options Considered | Votes | Result | Confidence |
|---|----------|--------------------|-------|--------|------------|
| {n} | {decision} | {options} | {votes_breakdown} | {result} | {confidence} |

## Consensus Points (agreed by 2+ agents)

| # | Point | Agents | Severity |
|---|-------|--------|----------|
| {n} | {point} | {agents} | {severity} |

## Resolved Conflicts

| Conflict | Agent A | Agent B | Resolution | Basis |
|----------|---------|---------|------------|-------|
| {conflict} | {agent_a_position} | {agent_b_position} | {resolution} | {basis} |

## Unresolved (Escalated to User)

| # | Conflict | Agent A | Agent B | Recommendation |
|---|----------|---------|---------|----------------|
| {n} | {conflict} | {agent_a_position} | {agent_b_position} | {recommendation} |

## Extracted Stories (if decisions generate new work)

| # | Story Title | Source Decision | Suggested Epic | Severity |
|---|-------------|----------------|----------------|----------|
| {n} | {story_title} | {source_decision} | {suggested_epic} | {severity} |

## Action Plan

| # | Action | Severity | Applies To | Owner |
|---|--------|----------|------------|-------|
| {n} | {action} | {severity} | {applies_to} | {owner} |

## Final Verdict

**Result:** {verdict} | **Winning Option:** {winning_option} | **Rounds:** {round_count}

---

*Artifact lifecycle: draft > validated > approved > stale (after 90 days) > archived*
