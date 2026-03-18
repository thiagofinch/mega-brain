# Story 3.4: SS Bridge

> **Epic:** Evolucao Mega Brain (v1.4.0 -> v2.0.0)
> **Sprint:** 3 -- Quick Wins
> **Effort:** ~2h
> **Risk:** LOW
> **Priority:** P1 (enables Skill Seekers integration path)
> **Dependencies:** Story 3.1 + 3.2 (fallback extractors)

---

## Objective

Create a subprocess bridge module that calls Skill Seekers CLI tools from
Mega Brain scripts without sharing a Python venv. If Skill Seekers is not
installed, the bridge falls back to native extractors (pymupdf, mammoth).

This is the B approach from the surgical merge plan: CLI Subprocess Bridge.
Zero dependency contamination. Zero shared memory.

---

## Tasks

| # | Task                                                | Effort |
|---|------------------------------------------------------|--------|
| 1 | Create `ss_bridge_config.yaml`                       | 10 min |
|   | Location: `core/intelligence/pipeline/`               |        |
|   | Fields: venv_path, timeout_seconds, fallback_enabled  |        |
| 2 | Create `ss_bridge.py`                                 | 45 min |
|   | Location: `core/intelligence/pipeline/`               |        |
|   | Functions:                                            |        |
|   |   is_ss_available() -> bool                           |        |
|   |   call_ss(command, timeout) -> CompletedProcess       |        |
|   |   ingest_pdf(path, source_tag) -> Path                |        |
|   |   ingest_docx(path, source_tag) -> Path               |        |
|   |   ingest_video(url, source_tag) -> Path (SS required) |        |
|   |   ingest_website(url, source_tag) -> Path (SS req.)   |        |
| 3 | Register path in `core/paths.py` ROUTING              | 5 min  |
|   | Key: `"ss_bridge_config"` -> pipeline/ss_bridge_...   |        |
| 4 | Write test: `tests/python/test_ss_bridge.py`          | 30 min |
|   | test_is_ss_available_when_missing (returns False)      |        |
|   | test_pdf_fallback_to_pymupdf (SS absent -> pymupdf)   |        |
|   | test_docx_fallback_to_mammoth (SS absent -> mammoth)   |        |
|   | test_video_requires_ss (SS absent -> RuntimeError)     |        |
|   | test_website_requires_ss (SS absent -> RuntimeError)   |        |
| 5 | Create install script: `bin/install-skill-seekers.sh`  | 15 min |
|   | Creates isolated venv at ~/.venvs/skill-seekers/       |        |
|   | pip installs skill-seekers in that venv                |        |
|   | Verifies installation with --version check             |        |

---

## Bridge Architecture

```
MB code (core/intelligence/pipeline/)
  |
  +-- ss_bridge.py
  |     |
  |     +-- is_ss_available()
  |     |     Checks: ~/.venvs/skill-seekers/bin/skill-seekers-pdf exists?
  |     |
  |     +-- ingest_pdf(path, tag)
  |     |     IF SS available: subprocess.run(["~/.venvs/.../skill-seekers-pdf", ...])
  |     |     IF NOT: from .extractors.pdf_extractor import extract_pdf (fallback)
  |     |
  |     +-- ingest_video(url, tag)
  |           IF SS available: subprocess.run(["~/.venvs/.../skill-seekers-video", ...])
  |           IF NOT: raise RuntimeError("Install Skill Seekers for video processing")
  |
  +-- ss_bridge_config.yaml
        venv_path: "~/.venvs/skill-seekers"
        timeout_seconds: 300
        fallback_enabled: true
```

---

## Acceptance Criteria

- [ ] `from core.intelligence.pipeline.ss_bridge import is_ss_available` works
- [ ] is_ss_available() returns False when SS not installed (expected default)
- [ ] ingest_pdf falls back to pymupdf when SS not installed
- [ ] ingest_docx falls back to mammoth when SS not installed
- [ ] ingest_video raises RuntimeError when SS not installed
- [ ] install-skill-seekers.sh creates isolated venv (does NOT touch MB venv)
- [ ] 5 tests pass in test_ss_bridge.py
- [ ] No SS imports anywhere in MB codebase (subprocess only)

---

## Definition of Done

- Code passes ruff lint
- Tests pass in CI (all tests run WITHOUT SS installed)
- ss_bridge.py has zero imports from skill-seekers package
- Bridge config uses expanduser for ~ path resolution
- No changes to existing pipeline behavior (bridge is opt-in)

---

## File Map

```
CREATES:
  core/intelligence/pipeline/ss_bridge.py
  core/intelligence/pipeline/ss_bridge_config.yaml
  bin/install-skill-seekers.sh
  tests/python/test_ss_bridge.py

MODIFIES:
  core/paths.py (add ROUTING key)
```
