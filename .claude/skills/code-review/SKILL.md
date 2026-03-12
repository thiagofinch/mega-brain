# Code Review Skill

> **Auto-Trigger:** Quando usuário pedir review de código, análise de qualidade, revisão de PR, auditoria de código
> **Keywords:** "review", "revisar código", "code review", "análise de código", "qualidade de código", "revisar mudanças"
> **Prioridade:** ALTA
> **Namespace:** [OFFICIAL]
> **Tools:** Read, Glob, Grep, Task

## Quando NÃO Ativar

- Escrita de código novo sem review
- Debugging sem análise de qualidade
- Perguntas sobre padrões sem código para revisar
- Quando usuário explicitamente pedir skill diferente

---

## Core Purpose

Multi-agent PR/code review system with confidence-based scoring. Uses 4 parallel agents
to provide comprehensive analysis with 80-point confidence threshold for recommendations.

---

## The 4 Review Agents

### 1. Architecture Agent

**Focus:** Structural analysis

- Code organization
- Design patterns
- Dependency management
- Scalability concerns
- SOLID principles adherence

### 2. Security Agent

**Focus:** Vulnerability detection

- Input validation
- Authentication/authorization
- Data exposure risks
- Injection vulnerabilities
- Secure coding practices

### 3. Performance Agent

**Focus:** Efficiency analysis

- Algorithm complexity
- Memory usage
- Database query efficiency
- Caching opportunities
- Resource management

### 4. Maintainability Agent

**Focus:** Code quality

- Readability
- Documentation
- Test coverage
- Technical debt
- Naming conventions

---

## Confidence Scoring System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONFIDENCE SCALE                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  90-100: Critical issue - Must fix before merge                             │
│  80-89:  Strong recommendation - Should address                             │
│  70-79:  Suggestion - Consider addressing                                   │
│  60-69:  Minor - Nice to have                                               │
│  <60:    Informational only                                                 │
│                                                                             │
│  THRESHOLD: 80+ = Actionable recommendation                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Review Output Format

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CODE REVIEW REPORT                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Files Reviewed: [N]                                                         ║
║  Lines Changed: +[added] / -[removed]                                        ║
║  Overall Score: [X]/100                                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─ CRITICAL (90+) ────────────────────────────────────────────────────────────┐
│  [Issues that must be fixed]                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ RECOMMENDATIONS (80-89) ───────────────────────────────────────────────────┐
│  [Strong suggestions]                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ SUGGESTIONS (70-79) ───────────────────────────────────────────────────────┐
│  [Nice to have improvements]                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ POSITIVES ─────────────────────────────────────────────────────────────────┐
│  [What's done well]                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Review Checklist

### Architecture
- [ ] Follows project patterns
- [ ] Appropriate abstractions
- [ ] Clear separation of concerns
- [ ] No circular dependencies

### Security
- [ ] Input validated
- [ ] No hardcoded secrets
- [ ] Proper error handling
- [ ] Secure defaults

### Performance
- [ ] No obvious N+1 queries
- [ ] Appropriate caching
- [ ] Efficient algorithms
- [ ] Resource cleanup

### Maintainability
- [ ] Clear naming
- [ ] Adequate comments
- [ ] Tests included
- [ ] Documentation updated

---

## Example Prompts This Skill Handles

- "Revise o código que acabei de escrever"
- "Do a code review on my PR changes"
- "Analise a qualidade deste módulo"
- "Review the authentication implementation"
- "Faça uma auditoria de segurança neste código"

---

## Integration Notes

This skill is part of the **Claude Code Official Skills** collection.
Namespace: `[OFFICIAL]` - Distinguishes from Mega Brain custom skills.

For custom Mega Brain skills, see: `/.claude/skills/`
