# Extracted from: .claude/skills/roundtable/SKILL.md (gap_analysis mode)
# Part of: SP-ROUNDTABLE process
# Version: 1.1.0

# Roundtable Gap Analysis -- {subject}

> **Date:** {date}
> **Mode:** gap_analysis
> **Participants:** {agent_list}
> **Verdict:** {verdict}

## Executive Summary

{executive_summary}

## Gaps Identified

| # | Gap | Severity | Domain | Recommendation |
|---|-----|----------|--------|---------------|
| 1 | {gap_description} | {critical|high|medium|low} | {domain} | {recommendation} |

## Gap Details

### Gap 1: {gap_title}

**Current State:** {current_state}
**Expected State:** {expected_state}
**Impact:** {impact_description}
**Root Cause:** {root_cause}
**Recommendation:** {recommendation}

## Coverage Matrix

| Domain | Coverage | Gaps Found | Status |
|--------|----------|-----------|--------|
| {domain} | {percentage}% | {count} | {covered|partial|missing} |

## Action Items

- [ ] {action_item_1}
- [ ] {action_item_2}

## Metadata

```yaml
gap_analysis:
  total_gaps: {count}
  critical: {count}
  high: {count}
  medium: {count}
  low: {count}
  coverage_score: {percentage}
  generated_by: roundtable/gap_analysis
  timestamp: "{ISO_8601}"
```
