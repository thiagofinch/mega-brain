# Tech Stack — Mega Brain

> **Version:** 1.0.0 | **Date:** 2026-03-05

---

## Languages

| Language | Version | Scope | Rationale |
|----------|---------|-------|-----------|
| Python | 3.12 (.python-version) | Intelligence layer, hooks, processing | Owns AI/ML ecosystem |
| Node.js | 18+ ESM (.nvmrc) | CLI distribution, npm package, setup wizard | Owns npm distribution |

---

## Node.js Dependencies (bin/)

| Package | Purpose | Category |
|---------|---------|----------|
| `chalk` | Terminal color output | UI |
| `boxen` | Terminal box drawing | UI |
| `gradient-string` | Gradient text effects | UI |
| `ora` | Terminal spinners | UI |
| `inquirer` | Interactive CLI prompts | UI |

**Decision:** UI-only dependencies. Zero logic dependencies. CLI is a thin wrapper.

---

## Python Dependencies (scoped)

### Hooks (.claude/hooks/) — `requirements-hooks.txt`
- `PyYAML>=6.0` — config parsing
- **Constraint:** stdlib + PyYAML ONLY (distributed with npm package)

### Pipeline (core/intelligence/pipeline/) — `pyproject.toml [pipeline]`
- `PyYAML>=6.0` — config parsing
- Standard library — dataclasses, pathlib, json

### RAG (core/intelligence/rag/) — `pyproject.toml [rag]`
- `voyageai` — voyage-context-3 embeddings (semantic search)
- `rank-bm25` — local BM25 fallback (keyword search)

### Speakers (core/intelligence/speakers/) — `pyproject.toml [speakers]`
- `pyannote.audio` — local GPU speaker diarization
- `torch` + `torchaudio` — PyTorch runtime
- `numpy` + `scipy` — numerical computing
- `assemblyai` — cloud fallback (no GPU)
- **Constraint:** NEVER distributed with npm (dev-only, L3)

### Dev — `pyproject.toml [dev]`
- `pytest` + `pytest-cov` — testing + coverage
- `ruff` — linting + formatting
- `pyright` — type checking

---

## Tooling

| Tool | Purpose | Config File |
|------|---------|-------------|
| Ruff | Python lint + format | `pyproject.toml [tool.ruff]` |
| Biome | JS lint + format | `biome.json` |
| pyright | Python type checking | `pyproject.toml [tool.pyright]` |
| pytest | Python testing | `pyproject.toml [tool.pytest]` |
| gitleaks | Secret scanning | `.gitleaks.toml` |
| trufflehog | Deep secret scanning (CI) | `.github/workflows/publish.yml` |

---

## MCP Servers (4)

| Server | Package | Purpose |
|--------|---------|---------|
| mega-brain-knowledge | Python (`core/intelligence/rag/mcp_server.py`) | RAG search |
| mega-brain | `@anthropic/filesystem-mcp` | Filesystem access |
| n8n-mcp | `n8n-mcp` | Workflow automation |
| read-ai | `mcp-remote` (OAuth) | Meeting transcriptions |

---

## Storage

| Type | Technology | Layer |
|------|-----------|-------|
| Primary | Local filesystem (L1/L2/L3) | All |
| RAG Index | BM25 local + Voyage embeddings | L3 |
| Knowledge Graph | JSON-based local graph | L3 |
| Database | Supabase pgvector (optional) | Production RAG |

---

## CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `verification.yml` | PR + push to main | 6-level quality pipeline |
| `publish.yml` | Release published | npm publish + security scan |
| `publish-pro.yml` | Tag `pro-v*` | Premium tier publish |
| `claude.yml` | PR opened/sync | Claude Code auto-review |

---

## Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dual language | Python + Node.js | Python for AI/ML, Node for npm distribution |
| No TypeScript | JSDoc + checkJs | 13 CLI files don't justify build step |
| Whitelist .gitignore | Default-deny | Security-first, prevents accidental exposure |
| Layer system | L1/L2/L3 | Community/Pro/Personal content separation |
| Path centralization | `core/paths.py` | Single source of truth for all output routing |
