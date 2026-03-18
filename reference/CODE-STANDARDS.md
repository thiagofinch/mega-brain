# Code Standards — Mega Brain

> **Version:** 1.0.0 | **Date:** 2026-03-05

---

## 1. Overview

This document defines code conventions for the Mega Brain project. It covers two languages (JavaScript, Python) across three codebases (`bin/`, `core/intelligence/`, `.claude/hooks/`).

**Enforcement:** `ruff` (Python), `biome` (JS). Config in `pyproject.toml` and `biome.json`.

---

## 2. JavaScript Standards (bin/)

### Runtime & Module System
- Node.js >= 18.0.0, ESM only (`"type": "module"`)
- All files use `import`/`export`. No `require()`.

### Style (enforced by Biome)
- Semicolons: yes
- Quotes: single
- Indentation: 2 spaces
- Trailing commas: yes (multi-line)
- Max line length: 100

### Naming
- Files: `kebab-case.js`
- Functions/variables: `camelCase`
- Constants: `SCREAMING_SNAKE`

### Imports
```js
// 1. Node.js builtins
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';

// 2. Third-party (npm)
import chalk from 'chalk';

// 3. Local modules
import { readLicense } from './lib/license.js';
```

### Error Handling
- Top-level: `main().catch(err => { console.error(err.message); process.exit(1); })`
- Expected failures: bare `catch {}` when error is not needed
- Logged failures: `catch (err)` with meaningful message

### Documentation
- JSDoc `/** */` on all exported functions
- At minimum: description, `@param`, `@returns`

### Type Safety
- No TypeScript (project decision)
- Use JSDoc type annotations + `jsconfig.json` with `checkJs: true`

---

## 3. Python Standards — Core (core/intelligence/)

### Runtime
- Python >= 3.11 (pinned in `.python-version`)
- Config centralized in `pyproject.toml`

### Style (enforced by Ruff)
- PEP 8 compliant
- Quotes: double
- Indentation: 4 spaces
- Max line length: 100

### Naming
- Files: `snake_case.py`
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Private: leading underscore `_`
- Constants: `SCREAMING_SNAKE`

### Imports (enforced by Ruff isort)
```python
# 1. Stdlib (alphabetical)
import json
import re
import sys

# 2. Third-party
import yaml

# 3. Local
from core.paths import ROOT, KNOWLEDGE_EXTERNAL, ROUTING
```

### Paths — CRITICAL RULE
**All files MUST import from `core.paths`.** Never compute `BASE_DIR` locally.

```python
# CORRECT
from core.paths import ROOT, KNOWLEDGE_EXTERNAL

# WRONG — never do this
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
```

### Type Hints
- Required on all public function signatures
- Use `typing` module for 3.11 compatibility (`Optional`, `Dict`, `List`)
- Enforced by `pyright` in basic mode on `core/`

### Docstrings
- Google style (Args, Returns, Raises)
- Required on modules and public functions
- Optional on private helpers

### Error Handling
- Use specific exception tuples: `except (YAMLError, OSError):`
- Never use bare `except:`
- Add `logging.warning()` in catch blocks for traceability

### Logging
- All intelligence scripts: `import logging; logger = logging.getLogger(__name__)`
- Use `logger.warning()` in error paths
- Use `print()` only in `if __name__ == "__main__"` CLI entry points

---

## 4. Python Standards — Hooks (.claude/hooks/)

### Dependency Constraint
**stdlib + PyYAML ONLY.** This is a distribution constraint — hooks ship with the npm package. No third-party imports beyond PyYAML.

### Exit Codes
- `0` = success (hook passed)
- `1` = warning (continue with notification)
- `2` = error/block (stop execution)

### Communication
- Output: JSON to stdout
- Input: JSON from stdin (hook event payload)
- Timeout: 30 seconds max

### Prohibited Patterns
- `2>/dev/null || true` — never suppress errors
- `subprocess.run(shell=True)` — security risk

---

## 5. File & Directory Conventions

- Directories: lowercase (`inbox`, `system`)
- Config files: SCREAMING-CASE (`STATE.json`, `MEMORY.md`)
- Skills: kebab-case directories (`knowledge-extraction/`)
- New output paths: MUST be added to `core/paths.py` ROUTING dict

---

## 6. Testing Standards

### Frameworks
- Python: `pytest` with `pytest-cov`
- JS: Node built-in test runner (`node:test`)

### Test Location
```
tests/
  python/
    test_validation/    # Layer classification tests
    test_rag/           # RAG chunker, indexer, query tests
    test_hooks/         # Hook behavior tests
  js/                   # CLI tests
  integration/          # Cross-language tests
```

### Naming
- Python: `test_*.py`, functions `test_*`
- JS: `test_*.js`

### Coverage Targets
- Phase 1: 40% on `core/intelligence/rag/` and `core/intelligence/validation/`
- Phase 2: 50% on `core/intelligence/` overall
- Steady state: 70% on new code

---

## 7. Git Workflow

- Branch naming: `type/issue-XX-description`
- Commit messages: Conventional Commits (`feat`, `fix`, `chore`, `docs`, `refactor`)
- No direct commits to `main`
- `git push` blocked for non-devops agents (settings.json deny list)

---

## 8. Security Standards

- NEVER hardcode secrets (enforced by `.gitleaks.toml` + `trufflehog`)
- `.env` is the ONLY credential source
- `.mcp.json` uses `${ENV_VAR}` syntax, never plaintext tokens
- All hooks: `"timeout": 30` (ANTHROPIC-STANDARDS)
- `curl`/`wget` denied in bash hooks

---

## 9. Dependency Management

- Python: `pyproject.toml` (primary), scoped optional dependencies
- JS: `package.json` + `package-lock.json` (committed)
- Hooks: `requirements-hooks.txt` (PyYAML only)
- New dependencies require justification in PR description
