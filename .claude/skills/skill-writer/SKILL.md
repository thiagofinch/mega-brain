---
name: skill-writer
description: Guide users through creating Agent Skills for Claude Code. Use when the user wants to create, write, author, or design a new Skill, or needs help with SKILL.md files, frontmatter, or skill structure.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(mkdir:*), Bash(ls:*)
---

# Skill Writer

Create well-structured Agent Skills for Claude Code following best practices.

## Quick start

```yaml
---
name: my-skill-name
description: What this does. Use when user mentions X, Y, or Z.
---

# My Skill Name

Instructions for Claude here...
```

## When to use this Skill

- Creating a new Agent Skill
- Writing or updating SKILL.md files
- Designing skill structure and frontmatter
- Converting existing prompts into Skills

## Instructions

### Step 1: Determine scope

Ask clarifying questions:
- What specific capability should this Skill provide?
- When should Claude use this Skill?
- What tools or resources does it need?

**Rule**: One Skill = one capability

### Step 2: Choose location

| Location | Use Case |
|----------|----------|
| `~/.claude/skills/` | Personal, experimental |
| `.claude/skills/` | Team/project, git-tracked |

### Step 3: Create structure

```bash
mkdir -p .claude/skills/skill-name
```

Multi-file structure:
```
skill-name/
├── SKILL.md (required)
├── reference.md (optional)
├── examples.md (optional)
└── scripts/ (optional)
```

### Step 4: Write frontmatter

```yaml
---
name: skill-name
description: Brief description of what this does and when to use it
---
```

| Field | Rules |
|-------|-------|
| `name` | Lowercase, hyphens, max 64 chars, **must match folder name** |
| `description` | Max 1024 chars, include WHAT + WHEN to use |
| `allowed-tools` | (Optional) Restrict tool access |

### Step 5: Write effective descriptions

**Formula**: `[What it does] + [When to use it] + [Key triggers]`

```yaml
# Good
description: Extract text from PDFs, fill forms. Use when working with PDF files or document extraction.

# Bad
description: Helps with documents
```

Tips:
- Include file extensions (.pdf, .xlsx)
- Use trigger words ("analyze", "extract", "generate")
- Add "Use when..." clause

### Step 6: Structure content

```markdown
# Skill Name

Brief overview.

## Quick start

Simple example.

## Instructions

Step-by-step guidance.

## Requirements

Dependencies if any.
```

### Step 7: Validate

- [ ] SKILL.md exists in correct location
- [ ] Directory name matches frontmatter `name`
- [ ] YAML valid (no tabs, spaces only)
- [ ] Description < 1024 chars, includes what + when
- [ ] Instructions are actionable

### Step 8: Test

1. Restart Claude Code to load Skill
2. Ask questions matching the description
3. Verify activation and behavior

## Additional resources

- **Patterns and examples**: See [examples.md](examples.md)
- **Debugging issues**: See [troubleshooting.md](troubleshooting.md)

## Output format

When creating a Skill, I will:

1. Ask clarifying questions about scope
2. Suggest name and location
3. Create SKILL.md with proper frontmatter
4. Include instructions and examples
5. Add supporting files if needed
6. Validate against requirements

## Best practices summary

1. **One Skill, one purpose**
2. **Specific descriptions** with trigger words
3. **Clear instructions** written for Claude
4. **Concrete examples** with real code
5. **Progressive disclosure** for complex Skills
6. **Under 500 lines** in SKILL.md
