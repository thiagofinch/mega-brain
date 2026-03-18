# Story 3.2: DOCX Extraction

> **Epic:** Evolucao Mega Brain (v1.4.0 -> v2.0.0)
> **Sprint:** 3 -- Quick Wins
> **Effort:** ~1h
> **Risk:** LOW
> **Priority:** P2 (from surgical comparison CAT1 item 10)
> **Dependencies:** Story 3.1 (shares extractors/ directory)

---

## Objective

Add native DOCX-to-markdown extraction so .docx transcriptions from Google Drive
are automatically converted to text before entering the pipeline.

Currently, .docx files from the Drive-linked planilha must be manually converted
to .txt. This story automates that using mammoth (lightweight, no binary deps).

---

## Tasks

| # | Task                                               | Effort |
|---|-----------------------------------------------------|--------|
| 1 | Add `mammoth>=1.8.0` to pyproject.toml              | 5 min  |
|   | Append to existing `extractors` optional-deps       |        |
|   | `extractors = ["pymupdf>=1.24.0", "mammoth>=1.8.0"]`|        |
| 2 | Create `docx_extractor.py` in extractors/            | 30 min |
|   | Function: `extract_docx(path: Path) -> str`          |        |
|   | Returns clean markdown (headings, lists, paragraphs) |        |
|   | Preserves heading hierarchy from Word styles         |        |
|   | Strips images (text-only extraction)                 |        |
| 3 | Write test: `tests/python/test_docx_extractor.py`    | 15 min |
|   | test_extract_simple_docx (create test .docx fixture)  |        |
|   | test_extract_empty_docx (returns empty string)        |        |
|   | test_extract_nonexistent_file (raises FileNotFound)   |        |
| 4 | Integration hook in inbox_organizer.py               | 10 min |
|   | Before moving .docx files: detect extension           |        |
|   | If .docx: call extract_docx, save as .md alongside    |        |
|   | Pipeline processes .md, ignores original .docx        |        |

---

## Acceptance Criteria

- [ ] `pip install mammoth` succeeds from pyproject.toml extras
- [ ] `from core.intelligence.pipeline.extractors.docx_extractor import extract_docx` works
- [ ] extract_docx produces readable markdown from a real .docx
- [ ] Heading hierarchy preserved (H1, H2, H3 from Word styles)
- [ ] 3 tests pass in test_docx_extractor.py
- [ ] inbox_organizer.py auto-converts .docx files on ingest

---

## Definition of Done

- Code passes ruff lint
- Tests pass in CI
- Function documented with docstring and type hints
- inbox_organizer.py change is backward-compatible (non-.docx files unaffected)

---

## File Map

```
CREATES:
  core/intelligence/pipeline/extractors/docx_extractor.py
  tests/python/test_docx_extractor.py

MODIFIES:
  pyproject.toml (append mammoth to extractors optional-deps)
  core/intelligence/pipeline/inbox_organizer.py (add .docx detection)
```
