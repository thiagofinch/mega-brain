# Skill Examples

Common patterns and templates for creating Skills.

## Read-only Skill

For Skills that only analyze without modifying:

```yaml
---
name: code-reader
description: Read and analyze code without making changes. Use for code review, understanding codebases, or documentation.
allowed-tools: Read, Grep, Glob
---

# Code Reader

Analyze code structure and patterns without making modifications.

## Instructions

1. Use Glob to find relevant files
2. Use Read to examine content
3. Use Grep to search patterns
4. Report findings without editing
```

## Script-based Skill

For Skills that use helper scripts:

```yaml
---
name: data-processor
description: Process CSV and JSON data files with Python scripts. Use when analyzing data files or transforming datasets.
---

# Data Processor

## Instructions

1. Use the processing script:
```bash
python scripts/process.py input.csv --output results.json
```

2. Validate output:
```bash
python scripts/validate.py results.json
```

## Requirements

```bash
pip install pandas
```
```

## Multi-file Skill (Progressive Disclosure)

For complex Skills with extensive documentation:

```yaml
---
name: api-designer
description: Design REST APIs following best practices. Use when creating API endpoints, designing routes, or planning API architecture.
---

# API Designer

Quick start: See [examples.md](examples.md)

Detailed reference: See [reference.md](reference.md)

## Instructions

1. Gather requirements
2. Design endpoints (see examples.md)
3. Document with OpenAPI spec
4. Review against best practices (see reference.md)
```

## Description Examples

### Good Descriptions

```yaml
# Specific actions + file types + trigger words
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Clear scope + when to use
description: Analyze Excel spreadsheets, create pivot tables, and generate charts. Use when working with Excel files, spreadsheets, or analyzing tabular data in .xlsx format.

# Action-oriented + context
description: Generate git commit messages following conventional commits format. Use when the user wants to commit changes or needs help writing commit messages.
```

### Bad Descriptions

```yaml
# Too vague
description: Helps with documents

# No trigger context
description: For data analysis

# Too broad
description: General purpose tool for files
```

## Validation Checklist Template

Include this in your Skill for self-validation:

```markdown
## Validation checklist

Before finalizing, verify:

- [ ] Name is lowercase, hyphens only, max 64 chars
- [ ] Name matches directory name exactly
- [ ] Description < 1024 chars
- [ ] Description includes "what" and "when"
- [ ] YAML frontmatter has no tabs
- [ ] Instructions are step-by-step
- [ ] Examples use real code
- [ ] Dependencies documented
- [ ] File paths use forward slashes
```

## File Structure Examples

### Minimal Skill (single file)

```
commit-helper/
└── SKILL.md
```

### Standard Skill (with examples)

```
pdf-processor/
├── SKILL.md
└── examples.md
```

### Complex Skill (full structure)

```
api-designer/
├── SKILL.md
├── reference.md
├── examples.md
├── templates/
│   └── openapi.yaml
└── scripts/
    └── validate.py
```

## Frontmatter Options

### Basic (required fields only)

```yaml
---
name: my-skill
description: What it does. Use when X happens.
---
```

### With tool restrictions

```yaml
---
name: my-skill
description: What it does. Use when X happens.
allowed-tools: Read, Grep, Glob, Write, Edit
---
```

### Full options

```yaml
---
name: my-skill
description: What it does. Use when X happens.
allowed-tools: Read, Grep, Glob
model: claude-sonnet-4-20250514
---
```
