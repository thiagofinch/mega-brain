# Plugin Development Skill

> **Auto-Trigger:** Quando usuário quiser criar plugin, desenvolver extensão, criar skill customizada
> **Keywords:** "plugin", "desenvolver plugin", "criar plugin", "extensão", "criar skill", "plugin-dev", "create-plugin"
> **Prioridade:** ALTA
> **Namespace:** [OFFICIAL]
> **Tools:** Read, Write, Edit, Glob, Grep, Bash, Task

## Quando NÃO Ativar

- Uso de plugins existentes sem modificação
- Debugging de plugins já implementados
- Perguntas gerais sobre plugins
- Quando usuário explicitamente pedir skill diferente

---

## Core Purpose

Comprehensive toolkit for developing Claude Code plugins. Provides structured 8-phase
workflow from concept to deployment with 7 core skills for plugin creation.

---

## The 7 Core Skills

| Skill | Purpose |
|-------|---------|
| **Architecture** | Design plugin structure and interfaces |
| **Implementation** | Write plugin code following best practices |
| **Testing** | Create comprehensive test suites |
| **Documentation** | Write clear plugin documentation |
| **Integration** | Connect with Claude Code systems |
| **Optimization** | Improve performance and reliability |
| **Deployment** | Package and distribute plugins |

---

## The 8 Phases of Plugin Creation

### Phase 1: Concept

- Define plugin purpose
- Identify target users
- List core features
- Set success criteria

### Phase 2: Research

- Study similar plugins
- Review Claude Code plugin API
- Identify dependencies
- Note limitations

### Phase 3: Design

- Create plugin architecture
- Define file structure
- Design interfaces
- Plan extension points

### Phase 4: Scaffold

- Create directory structure
- Initialize configuration files
- Set up development environment
- Create boilerplate code

### Phase 5: Implementation

- Write core functionality
- Implement features incrementally
- Handle errors gracefully
- Follow coding standards

### Phase 6: Testing

- Write unit tests
- Create integration tests
- Test edge cases
- Verify error handling

### Phase 7: Documentation

- Write README
- Document API/interfaces
- Create usage examples
- Add troubleshooting guide

### Phase 8: Deployment

- Package plugin
- Version appropriately
- Publish/distribute
- Monitor feedback

---

## Plugin Structure Template

```
plugin-name/
├── SKILL.md           # Main skill definition
├── README.md          # Documentation
├── package.json       # If npm-based
├── src/
│   ├── index.ts       # Entry point
│   ├── handlers/      # Event handlers
│   └── utils/         # Helper functions
├── tests/
│   └── *.test.ts      # Test files
└── examples/
    └── *.md           # Usage examples
```

---

## SKILL.md Template

```markdown
# [Plugin Name] Skill

> **Auto-Trigger:** [When to activate]
> **Keywords:** "keyword1", "keyword2", "keyword3"
> **Prioridade:** [ALTA | MÉDIA | BAIXA]
> **Tools:** [List of tools used]

## Quando NÃO Ativar

- [Situation 1]
- [Situation 2]

---

## Core Purpose

[Brief description of what the plugin does]

---

## [Main Content Sections]

[Plugin-specific documentation]

---

## Example Prompts This Skill Handles

- "[Example 1]"
- "[Example 2]"
```

---

## Command

Use `/plugin-dev:create-plugin` to start the guided plugin creation workflow.

---

## Example Prompts This Skill Handles

- "Crie um plugin para processar PDFs"
- "Develop a plugin for database migrations"
- "Quero criar uma skill para análise de logs"
- "Build an extension for API testing"
- "Desenvolva um plugin de formatação de código"

---

## Integration Notes

This skill is part of the **Claude Code Official Skills** collection.
Namespace: `[OFFICIAL]` - Distinguishes from Mega Brain custom skills.

For custom Mega Brain skills, see: `/.claude/skills/`
