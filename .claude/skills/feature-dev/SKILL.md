# Feature Development Skill

> **Auto-Trigger:** Quando usuário pedir nova feature, funcionalidade, implementação estruturada, desenvolvimento guiado
> **Keywords:** "feature", "nova funcionalidade", "7 fases", "implementar feature", "desenvolvimento estruturado", "feature workflow"
> **Prioridade:** ALTA
> **Namespace:** [OFFICIAL]
> **Tools:** Read, Write, Edit, Glob, Grep, Bash, Task

## Quando NÃO Ativar

- Bug fixes simples sem nova funcionalidade
- Refatorações sem adicionar features
- Perguntas sobre features existentes
- Quando usuário explicitamente pedir skill diferente

---

## Core Purpose

Structured 7-phase workflow for implementing new features with comprehensive planning,
exploration, and review cycles. Ensures high-quality implementations through systematic approach.

---

## The 7 Phases

### Phase 1: Discovery

**Goal:** Understand the request deeply

- Clarify requirements with user
- Identify acceptance criteria
- Define scope boundaries
- Document assumptions

### Phase 2: Exploration

**Goal:** Understand the existing codebase

- Search for related code patterns
- Identify integration points
- Map dependencies
- Note existing conventions

### Phase 3: Questions

**Goal:** Resolve ambiguities

- Ask clarifying questions
- Validate assumptions
- Confirm technical approach
- Get user sign-off on direction

### Phase 4: Architecture

**Goal:** Design the solution

- Plan file changes
- Design interfaces/contracts
- Consider edge cases
- Document technical decisions

### Phase 5: Implementation

**Goal:** Write the code

- Follow established patterns
- Write clean, tested code
- Implement incrementally
- Handle errors gracefully

### Phase 6: Review

**Goal:** Validate the implementation

- Self-review all changes
- Run tests
- Check for regressions
- Verify against requirements

### Phase 7: Summary

**Goal:** Document and handoff

- Summarize changes made
- Document any follow-ups needed
- Note technical debt if any
- Provide usage examples

---

## Phase Execution Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE N: [NAME]                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  STATUS: [IN_PROGRESS | COMPLETE | BLOCKED]                                 │
│                                                                             │
│  ACTIONS:                                                                   │
│  ✅ [Completed action]                                                      │
│  ⏳ [In progress action]                                                    │
│  ⬚ [Pending action]                                                        │
│                                                                             │
│  FINDINGS:                                                                  │
│  - [Key finding or decision]                                                │
│                                                                             │
│  NEXT: [What happens next]                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Guidelines

### Before Starting

1. Confirm feature scope with user
2. Estimate complexity (S/M/L/XL)
3. Identify blockers early
4. Set expectations on deliverables

### During Implementation

1. Stay within defined scope
2. Communicate phase transitions
3. Surface blockers immediately
4. Keep code clean and documented

### After Completion

1. Provide clear summary
2. List any follow-up items
3. Document technical decisions
4. Suggest testing approach

---

## Example Prompts This Skill Handles

- "Implemente uma feature de autenticação OAuth"
- "Add a dark mode toggle to the application"
- "Preciso de uma nova funcionalidade de export para CSV"
- "Create a notification system with email and push support"
- "Desenvolva um sistema de cache para a API"

---

## Integration Notes

This skill is part of the **Claude Code Official Skills** collection.
Namespace: `[OFFICIAL]` - Distinguishes from Mega Brain custom skills.

For custom Mega Brain skills, see: `/.claude/skills/`
