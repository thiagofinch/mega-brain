---
paths:
  - "docs/stories/**"
  - "docs/plans/**"
  - "docs/epics/**"
  - "docs/architecture/**"
---

# IDS Principles

> Status: Aspirational guidance — IDS epic is in planning phase.

## Decision Hierarchy: REUSE > ADAPT > CREATE

### REUSE (Relevance >= 90%)
- Use existing artifact directly without modification
- Import/reference existing entity
- No justification needed beyond confirming match

### ADAPT (Relevance 60-89%)
- Adaptability score >= 0.6
- Changes MUST NOT exceed 30% of original artifact
- Changes MUST NOT break existing consumers (check usedBy list)
- Document changes in artifact's change log
- Update registry relationships
- Impact analysis required

### CREATE (No suitable match)
Required justification:
- `evaluated_patterns`: Existing entities you considered
- `rejection_reasons`: Why each was rejected (technical reasons)
- `new_capability`: What unique capability this provides
- Register in Entity Registry within 24 hours
- Establish relationships with existing entities
- Define adaptability constraints for future reuse

## Verification Gates G1-G6

| Gate | Phase | Agent | Type | Blocking |
|------|-------|-------|------|----------|
| G1 | Epic Creation | @pm | Advisory | No |
| G2 | Story Creation | @sm | Advisory | No |
| G3 | Story Validation | @po | Soft Block | Can override with reason |
| G4 | Dev Context | @dev | Informational | No (logged only) |
| G5 | QA Review | @qa | Hard Block | Yes if no registry entry |
| G6 | CI/CD | @devops | Hard Block | Yes on CRITICAL |

## Override Policy

**Command:** `--override-ids --override-reason "explanation"`

**Permitted when:**
- Time-critical fix requires immediate creation
- Adaptation would introduce unacceptable risk
- Existing artifact is deprecated/frozen

**Requirements:**
- Logged for audit trail
- Reviewed within 7 days

## Graceful Degradation

All gates implement circuit breaker:
- **Timeout:** 2s default
- **On timeout:** warn-and-proceed
- **On error:** log-and-proceed
- **Key principle:** Development NEVER blocked by IDS failures

## Constitutional Alignment

**Article IV-A: Incremental Development**

Four Core Rules:
1. **Registry Consultation Required** — Query before creating
2. **Decision Hierarchy** — REUSE > ADAPT > CREATE strictly
3. **Adaptation Limits** — Changes < 30%, don't break consumers
4. **Creation Requirements** — Full justification, register within 24h
