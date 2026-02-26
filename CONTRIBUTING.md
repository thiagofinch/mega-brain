# Contributing to Mega Brain

## Maintainer

This project is maintained exclusively by **@thiagofinch**. All official updates and releases are published by the maintainer only.

## Branch Workflow

**Push direto em `main` = PROIBIDO.** Always create a branch and open a Pull Request.

### Branch Naming

| Prefix | Use Case |
|--------|----------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `refactor/` | Code refactoring |
| `test/` | Adding or updating tests |

Format: `{prefix}{short-description}` (e.g., `feat/add-pipeline-v2`, `fix/batch-log-format`)

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new pipeline processor
fix: correct batch numbering in logs
docs: update CLAUDE.md with new rules
refactor: simplify session autosave logic
test: add unit tests for source-sync
chore: update dependencies
```

Reference related issues when applicable: `feat: add login form refs #42`

## Pull Requests

1. Create a branch from `main` following the naming convention above
2. Make your changes with conventional commits
3. Open a PR using the provided template
4. All PRs require approval from **@thiagofinch** before merge
5. Ensure all checklist items in the PR template are addressed
6. Use `Fixes #XX` in the PR body to auto-close related issues

## What NOT to Do

- Do NOT push directly to `main`
- Do NOT merge without PR approval
- Do NOT commit secrets, API keys, or `.env` files
- Do NOT skip the PR template checklist

## Security

- Never hardcode credentials in code
- Use `.env` for all secrets (already in `.gitignore`)
- If a key is accidentally exposed, rotate it immediately

## Questions?

Open an issue or reach out to **@thiagofinch**.
