# Source Tree — Mega Brain

> **Version:** 1.0.0 | **Date:** 2026-03-05
> **Machine-readable contract:** `core/paths.py`
> **Human-readable contract:** `.claude/rules/directory-contract.md`

---

## Top-Level Structure

```
mega-brain/
├── bin/                  JS CLI tools (npm entry points)
├── core/                 Python engine (intelligence, workflows, schemas)
├── agents/               Knowledge agents (conclave, cargo, minds)
├── reference/            Documentation (guides, standards, ADRs)
├── docs/                 Legacy docs (migrating to reference/)
├── workspace/            Business data — L1 template, L2 populated (org, finance, meetings)
├── knowledge/            Knowledge base (2 buckets)
│   ├── external/         Expert content (dna, dossiers, playbooks)
│   └── personal/         Private content — L3 only (email, calls, cognitive)
├── artifacts/            Pipeline output (chunks, insights, canonical)
├── inbox/                Raw materials awaiting processing
├── logs/                 Session and batch logs
├── tests/                Test suites (Python + JS)
├── .claude/              Claude Code integration
│   ├── hooks/            Lifecycle hooks (Python, stdlib+PyYAML)
│   ├── skills/           Slash-command skills
│   ├── commands/         Custom commands
│   ├── rules/            Governance rules (lazy-loaded)
│   ├── aios/             AIOS agent system
│   └── agent-memory/     Persistent agent memory
├── .github/              CI/CD workflows + templates
├── .planning/            GSD planning phases
└── system/               JARVIS state + DNA + soul
```

---

## Layer Architecture

| Layer | Content | Git | npm |
|-------|---------|-----|-----|
| L1 (Community) | core/, bin/, agents/templates, .claude/, workspace/ (template) | Tracked | Published |
| L2 (Pro) | agents/cargo/*, knowledge/external/*, workspace/ (populated) | Tracked | Premium |
| L3 (Personal) | inbox/*, logs/*, knowledge/personal/*, .env, sessions | Gitignored | Never |
| NEVER | .env, credentials, .DS_Store, __pycache__ | Blocked | Blocked |

---

## Config Files

| File | Purpose |
|------|---------|
| `package.json` | npm package config, scripts, dependencies |
| `pyproject.toml` | Python tooling (ruff, pyright, pytest, deps) |
| `biome.json` | JavaScript lint + format |
| `jsconfig.json` | JS type checking (checkJs) |
| `.editorconfig` | Cross-editor whitespace rules |
| `.python-version` | Python version pin (3.12) |
| `.nvmrc` | Node version pin (18) |
| `.gitignore` | Whitelist-based layer protection |
| `.gitleaks.toml` | Secret scanning patterns |
| `requirements-hooks.txt` | Hook-only Python deps (PyYAML) |
| `core/paths.py` | Output routing contract (machine-readable) |

---

## Test Structure

```
tests/
├── python/
│   ├── conftest.py              Shared fixtures
│   ├── test_validation/         Layer classification tests (44 cases)
│   ├── test_rag/                RAG chunker, indexer, query tests
│   └── test_hooks/              Hook behavior tests
├── js/                          Node test runner tests
└── integration/                 Cross-language tests
```

---

## Key Scripts

| Command | Action |
|---------|--------|
| `npm run lint` | Ruff check on Python |
| `npm run lint:fix` | Ruff auto-fix |
| `npm run format` | Ruff format |
| `npm run test` | pytest on tests/python/ |
| `npm run test:coverage` | pytest with coverage report |
| `npm run validate:layers` | Layer validation (L1-only in npm) |
| `npm run validate:json` | JSON integrity check |
