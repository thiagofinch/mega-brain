# Hookify Skill

> **Auto-Trigger:** Quando usuário quiser criar hook, regra de segurança, validação customizada, lifecycle hook
> **Keywords:** "hook", "criar hook", "lifecycle", "safety rule", "validação", "regra de segurança", "pre-tool", "post-tool"
> **Prioridade:** ALTA
> **Namespace:** [OFFICIAL]
> **Tools:** Read, Write, Edit, Glob, Grep

## Quando NÃO Ativar

- Discussões sobre hooks existentes sem intenção de criar novos
- Debugging de hooks já implementados
- Perguntas gerais sobre o sistema de hooks
- Quando usuário explicitamente pedir skill diferente

---

## Core Purpose

Creating custom safety rules and hooks for Claude Code via markdown files with YAML frontmatter.
Enables pattern detection, regex matching, and warn/block modes for tool usage control.

---

## Hook Structure

### File Format

```markdown
---
name: hook-name
description: What this hook does
trigger: PreToolUse | PostToolUse | UserPromptSubmit | SessionStart | Stop
tools: ["Bash", "Write", "Edit"]  # Optional: specific tools to match
pattern: "regex pattern"  # Optional: content pattern matching
mode: warn | block  # Default: warn
---

# Instructions for what to do when triggered

Your custom logic here...
```

### Trigger Types

| Trigger | When It Fires |
|---------|---------------|
| `PreToolUse` | Before any tool execution |
| `PostToolUse` | After tool execution |
| `UserPromptSubmit` | When user sends a message |
| `SessionStart` | At session initialization |
| `Stop` | At session end |

### Mode Options

| Mode | Behavior |
|------|----------|
| `warn` | Alerts but continues execution |
| `block` | Prevents the action entirely |

---

## Implementation Guidelines

### 1. Identify the Need

- What action should be controlled?
- When should the hook trigger?
- Should it warn or block?

### 2. Define Patterns

- Use regex for content matching
- Specify tools if action-specific
- Consider edge cases

### 3. Write Instructions

- Clear, concise logic
- Explain the "why" for debugging
- Include examples if complex

---

## Example Hooks

### Prevent Dangerous Commands

```markdown
---
name: prevent-rm-rf
description: Blocks recursive force delete commands
trigger: PreToolUse
tools: ["Bash"]
pattern: "rm\\s+-rf"
mode: block
---

This command is blocked for safety. Use explicit file deletion instead.
```

### Warn on Sensitive Files

```markdown
---
name: warn-env-access
description: Warns when accessing environment files
trigger: PreToolUse
tools: ["Read", "Edit"]
pattern: "\\.env"
mode: warn
---

You're accessing an environment file. Ensure no secrets are exposed.
```

---

## Example Prompts This Skill Handles

- "Crie um hook para bloquear comandos perigosos"
- "Create a safety rule for database operations"
- "Preciso de uma validação antes de editar arquivos .env"
- "Make a pre-tool hook that warns about large file writes"
- "Quero criar regras de segurança customizadas"

---

## Integration Notes

This skill is part of the **Claude Code Official Skills** collection.
Namespace: `[OFFICIAL]` - Distinguishes from Mega Brain custom skills.

For custom Mega Brain skills, see: `/.claude/skills/`
