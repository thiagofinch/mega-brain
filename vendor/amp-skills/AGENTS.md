# Skills Repository Guidelines

## Structure

Each skill is a folder containing:
- `SKILL.md` - The skill definition (required)
- Additional resources (scripts, templates, references) as needed

## Skill Naming

- Folder name = skill name (kebab-case)
- Keep names short and descriptive
- Use verbs or nouns that describe the capability

## SKILL.md Format

```markdown
---
name: skill-name
description: "One-line description. Use when [context]. Triggers on: trigger1, trigger2, trigger3."
---

# Skill Title

[Main content with workflows, patterns, examples]
```

### Description Best Practices

The description field is critical - it determines when the skill gets loaded:
- Start with what the skill does
- Include "Use when..." to specify context
- End with "Triggers on:" followed by keyword phrases
- Keep under 300 characters

## Writing Good Skills

1. **Be specific** - Detailed instructions beat vague guidance
2. **Include examples** - Show, don't just tell
3. **Define workflows** - Step-by-step processes work best
4. **Add checklists** - Help ensure nothing is missed
5. **Reference patterns** - Point to existing code/files when relevant

## Testing Skills

Load your skill and verify:
- Triggers fire on expected phrases
- Instructions are clear and actionable
- Examples cover common use cases
- Workflows produce expected outputs

## Commits

Use conventional commits:
- `feat: add new-skill skill` - New skill
- `fix: correct workflow in skill-name` - Bug fix
- `docs: update skill-name examples` - Documentation
- `refactor: restructure skill-name` - Refactoring
