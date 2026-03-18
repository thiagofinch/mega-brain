# Story 3.1: PDF Extraction

> **Epic:** Evolucao Mega Brain (v1.4.0 -> v2.0.0)
> **Sprint:** 3 -- Quick Wins
> **Effort:** ~1h
> **Risk:** LOW
> **Priority:** P2 (from surgical comparison CAT1 item 9)
> **Dependencies:** None

---

## Objective

Add native PDF text extraction to the pipeline so PDF files landing in inbox
are automatically converted to markdown text before processing.

Currently, PDFs require manual conversion or LLM-based reading. This story
adds a deterministic, fast extractor using PyMuPDF.

---

## Tasks

| # | Task                                               | Effort |
|---|-----------------------------------------------------|--------|
| 1 | Add `pymupdf>=1.24.0` to pyproject.toml             | 5 min  |
|   | Section: `[project.optional-dependencies]`           |        |
|   | Key: `extractors = ["pymupdf>=1.24.0"]`              |        |
| 2 | Create `core/intelligence/pipeline/extractors/`      | 5 min  |
|   | Add `__init__.py` with module docstring              |        |
| 3 | Create `pdf_extractor.py`                            | 30 min |
|   | Function: `extract_pdf(path: Path) -> str`           |        |
|   | Returns clean markdown text (headings, paragraphs)   |        |
|   | Handles multi-page, tables, embedded text            |        |
|   | Strips headers/footers if repetitive                |        |
| 4 | Write test: `tests/python/test_pdf_extractor.py`     | 15 min |
|   | test_extract_simple_pdf (create test PDF in fixture)  |        |
|   | test_extract_empty_pdf (returns empty string)         |        |
|   | test_extract_nonexistent_file (raises FileNotFound)   |        |
| 5 | Register path in `core/paths.py` ROUTING             | 5 min  |
|   | Key: `"extractors"` -> pipeline/extractors/           |        |

---

## Acceptance Criteria

- [ ] `pip install pymupdf` succeeds from pyproject.toml extras
- [ ] `from core.intelligence.pipeline.extractors.pdf_extractor import extract_pdf` works
- [ ] extract_pdf produces readable markdown from a real PDF
- [ ] 3 tests pass in test_pdf_extractor.py
- [ ] No changes to existing files except pyproject.toml and paths.py

---

## Definition of Done

- Code passes ruff lint
- Tests pass in CI
- Function documented with docstring and type hints
- No impact on existing pipeline (this is additive only)

---

## File Map

```
CREATES:
  core/intelligence/pipeline/extractors/__init__.py
  core/intelligence/pipeline/extractors/pdf_extractor.py
  tests/python/test_pdf_extractor.py

MODIFIES:
  pyproject.toml (add pymupdf to optional-dependencies)
  core/paths.py (add ROUTING key)
```
