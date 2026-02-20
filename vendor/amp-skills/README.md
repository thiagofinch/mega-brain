# Amp Skills

A collection of specialized skills for [Amp](https://ampcode.com), the AI coding agent.

## What are Skills?

Skills are domain-specific instruction sets that extend Amp's capabilities. When you invoke a skill, it loads detailed workflows, patterns, and techniques into the conversation context.

## Available Skills

### Marketing & Content
- **brand-voice** - Define or extract a consistent brand voice
- **positioning-angles** - Find the angle that makes something sell
- **direct-response-copy** - Write copy that converts
- **lead-magnet** - Generate lead magnet concepts
- **content-atomizer** - Transform content into platform-optimized assets
- **email-sequences** - Build email sequences that convert
- **newsletter** - Create best-in-class newsletters
- **keyword-research** - Strategic keyword research without expensive tools
- **seo-content** - Create SEO-optimized content that ranks
- **orchestrator** - Marketing strategist that routes to the right skill(s)

### Development
- **ralph** - Set up Ralph for autonomous feature development
- **build-feature** - Autonomous task loop for implementing features
- **compound-engineering** - Plan → Work → Review → Compound workflow
- **prd** - Generate Product Requirements Documents
- **frontend-design** - Create distinctive, production-grade interfaces
- **dev-browser** - Browser automation with persistent page state

### Document Handling
- **pdf** - PDF manipulation (extract, create, merge, split, forms)
- **docx** - Word document creation, editing, and analysis
- **xlsx** - Spreadsheet creation, editing, and analysis

### Utilities
- **web-artifacts-builder** - Create multi-component HTML artifacts for claude.ai

## Usage

Skills are automatically available in Amp. To use one:

```
Use the direct-response-copy skill to write a landing page for my SaaS product.
```

Or trigger naturally:
```
Help me write copy for my landing page.
```

Amp will load the appropriate skill based on your request.

## Adding Skills

Each skill is a folder containing a `SKILL.md` file with frontmatter:

```markdown
---
name: my-skill
description: "Brief description. Use when... Triggers on: keyword1, keyword2."
---

# Skill Title

Instructions, workflows, and patterns go here.
```

## License

MIT
