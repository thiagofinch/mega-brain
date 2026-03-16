# Integration Plan: Mega Brain <-> Skill Seekers
## v1.0 -- 2026-03-14

> **Author:** Tiny Rick (The Architect, character envelope: rick-and-morty)
> **Status:** FINAL
> **Mega Brain:** v1.4.0 -- AI Knowledge Management System (internal, [SUA EMPRESA])
> **Skill Seekers:** v3.2.0 -- Universal Knowledge Preprocessing Tool (MIT, PyPI)
> **Prerequisite:** This is NOT a repo merge. These are two DIFFERENT projects.
> **Source Documents:**
> - `docs/plans/comparacao-cirurgica-2026-03-14.md` (Part C -- 45-item comparison)
> - `docs/plans/analise-outro-repo-2026-03-14.md` (Part B -- cross-repo analysis)
> - `docs/prd/technical-debt-assessment.md` (39 debt items, 8 P0)

---

## Strategic Decision

**Approach: HYBRID (B + D, with C for future)**

```
+-----------------------------------------------------------------------+
| PRIMARY:  B -- CLI Subprocess Bridge                                   |
|           Call SS executables from MB scripts. Zero dep contamination.  |
|                                                                        |
| SECONDARY: D -- Adopt Patterns Only                                    |
|           Copy test infrastructure, CI/CD patterns, Strategy Pattern.   |
|           No runtime dependency for these.                             |
|                                                                        |
| FUTURE:   C -- MCP Server (Phase 3 only, conditional)                  |
|           Run SS MCP server alongside MB's existing 4 servers.          |
|           Only if Phase 2 proves SS is valuable enough to keep running. |
|                                                                        |
| REJECTED: A -- Use as Library (pip install in same venv)               |
|           SS pulls langchain>=1.2.10, llama-index>=0.14.15,            |
|           and optionally PyTorch (~2GB). This contaminates MB's lean   |
|           dependency tree. The coupling risk is too high for an        |
|           internal tool. Rejected.                                     |
+-----------------------------------------------------------------------+
```

**Justification:**

1. MB is a 30K LOC Python system with minimal dependencies (pyyaml, stdlib).
   SS is a 77K LOC system that pulls langchain, llama-index, and optionally
   pytorch. Mixing these in one venv creates version conflicts and bloats
   the install from seconds to minutes.

2. SS's value to MB is in INGESTION (PDF, DOCX, video, web). These are
   batch operations that run infrequently (when new materials arrive).
   Subprocess overhead is negligible for batch processing.

3. Pattern adoption (D) gives MB the engineering maturity benefits (tests,
   CI/CD, Strategy Pattern) without any runtime dependency on SS. Even if
   SS is abandoned, the patterns remain.

4. MB has 39 technical debts (8 CRITICAL). Adding a heavy integration before
   fixing decorative CI, 21 duplicate modules, and 352 ruff errors would be
   building on sand. Patterns first, bridge second.

---

## Architecture Design

### Data Flow: SS as Ingestion Engine for MB

```
                    SKILL SEEKERS (external tool)
                    ============================
                    Installed in isolated venv:
                    ~/.venvs/skill-seekers/

+-------------------+     +-------------------+     +-------------------+
|   RAW SOURCES     |     |   SS CLI TOOLS    |     |   MB INBOX        |
|                   |     |                   |     |                   |
| PDFs of courses --+--> | skill-seekers-pdf |---->| knowledge/        |
| .docx transcripts +--> | skill-seekers-word|---->|   external/       |
| YouTube videos ---+--> | skill-seekers-    |---->|     inbox/        |
| Websites ---------+--> |    video          |---->|       {source}/   |
|                   |     | skill-seekers-    |     |                   |
|                   |     |    doc-scrape     |     |                   |
+-------------------+     +-------------------+     +-------------------+
                                                           |
                                                           v
                                              +-------------------+
                                              |  MB MCE PIPELINE  |
                                              |  (existing flow)  |
                                              |                   |
                                              | scope_classifier  |
                                              | smart_router      |
                                              | batch_auto_creator|
                                              | memory_enricher   |
                                              | --> DNA / Agents  |
                                              +-------------------+
```

### Bridge Module Architecture

```
core/intelligence/pipeline/
+-- ss_bridge.py              <-- NEW: Bridge module (subprocess calls)
+-- ss_bridge_config.yaml     <-- NEW: Config (SS venv path, defaults)
+-- extractors/               <-- NEW: Format-specific wrappers
    +-- __init__.py
    +-- pdf_extractor.py      <-- Calls skill-seekers-pdf OR pymupdf fallback
    +-- docx_extractor.py     <-- Calls skill-seekers-word OR mammoth fallback
    +-- video_extractor.py    <-- Calls skill-seekers-video (no fallback)
    +-- web_extractor.py      <-- Calls skill-seekers-doc-scrape (no fallback)
```

### Dependency Isolation Strategy

```
+-----------------------------------------------------------------------+
| MB's venv (mega-brain)          | SS's venv (skill-seekers)           |
| ==============================  | ====================================|
| Python 3.12                     | Python 3.10+                        |
| pyyaml                          | langchain>=1.2.10                   |
| anthropic                       | llama-index>=0.14.15                |
| httpx                           | chromadb                            |
| sentence-transformers           | sentence-transformers               |
| (optional: pymupdf, mammoth)    | pytesseract, opencv-python          |
|                                 | yt-dlp, faster-whisper              |
| ~50MB install                   | ~500MB install (2GB with video-full)|
+-----------------------------------------------------------------------+

BRIDGE MECHANISM:
  ss_bridge.py calls:
    ~/.venvs/skill-seekers/bin/skill-seekers-pdf --file X --output Y

  This is a subprocess call. Zero shared memory. Zero dep conflict.
  If SS venv does not exist, bridge falls back to:
    - pymupdf (pip install in MB venv, 5MB) for PDFs
    - mammoth (pip install in MB venv, <1MB) for DOCX
    - Error message for video/web (SS required)
```

---

## Phase 0: P0 Technical Debt (Pre-Requisite, Week 0)

Before ANY integration work, the 8 CRITICAL debts from the technical-debt-assessment
MUST be resolved. Integration on top of decorative CI and duplicate modules is
architecturally unsound.

```
+-----------------------------------------------------------------------+
| BLOCK GATE: Do NOT start Phase 1 until P0 debts are resolved.         |
|                                                                        |
| Resolution order (from technical-debt-assessment.md):                  |
|   STEP 1: TD-003 -- sync version (10 min)                             |
|   STEP 2: TD-032 -- remove secrets from auto-memory (30 min)          |
|   STEP 3: TD-033 -- replace pickle.load (2h)                          |
|   STEP 4: TD-014 -- fix CI test path (15 min)                         |
|   STEP 5: TD-004 -- fix 92 agents/minds/ references (3h)              |
|   STEP 6: TD-002 -- regenerate AGENT-INDEX.yaml (1h)                  |
|   STEP 7: TD-001 -- delete 21 duplicate modules (3h)                  |
|   STEP 8: TD-019 -- rewrite CI pipeline (4h)                          |
|                                                                        |
| Total: ~14.5h. This is the price of entry.                             |
+-----------------------------------------------------------------------+
```

---

## Phase 1: Foundation (Week 1)

Zero-risk pattern adoptions. No runtime dependency on SS.
Every item in this phase makes MB better regardless of whether
the SS integration proceeds.

### 1.1 Test Infrastructure Patterns (from SS)

**What to adopt:** conftest.py structure, markers, coverage config.
**What NOT to copy:** SS's 2,540 tests (wrong domain).

```
ACTION ITEMS:

1. Create tests/conftest.py with shared fixtures:
   - tmp_knowledge_dir (isolated knowledge/ tree)
   - mock_state_files (MISSION-STATE.json etc.)
   - sample_transcript (fixture with real meeting format)

2. Add markers to pyproject.toml:
   [tool.pytest.ini_options]
   markers = [
       "unit: Fast isolated tests",
       "integration: Tests that touch filesystem",
       "e2e: End-to-end pipeline tests",
       "slow: Tests that take >5s",
   ]

3. Add coverage config to pyproject.toml:
   [tool.coverage.run]
   source = ["core"]
   omit = ["*/tests/*", "*/__pycache__/*"]

   [tool.coverage.report]
   fail_under = 30

4. Write tests for 3 critical modules:
   - tests/python/test_paths.py (validate 100+ routing keys)
   - tests/python/test_scope_classifier.py (business vs personal routing)
   - tests/python/test_memory_manager.py (CRUD operations)

TARGET: 100+ tests, 30% coverage on core/.
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 1.1.1 | conftest.py with fixtures | SS pattern | 2h | LOW |
| 1.1.2 | Marker + coverage config | SS pattern | 30m | LOW |
| 1.1.3 | Tests for paths.py | New (MB-specific) | 4h | LOW |
| 1.1.4 | Tests for scope_classifier.py | New (MB-specific) | 4h | LOW |
| 1.1.5 | Tests for memory_manager.py | New (MB-specific) | 4h | LOW |

### 1.2 CI/CD Patterns (from SS)

**What to adopt:** Real GitHub Actions workflows that actually run.
**What NOT to copy:** Docker build, K8s deploy, vector DB test workflows.

```
ACTION ITEMS:

1. DELETE existing decorative CI:
   .github/workflows/verification.yml (hardcodes PASSED)

2. CREATE 3 real workflows:

   .github/workflows/lint.yml:
     - ruff check core/ .claude/hooks/ tests/
     - pyright core/ (basic mode)
     - Trigger: push + PR to main

   .github/workflows/test.yml:
     - python3 -m pytest tests/python/ -v --tb=short
     - Python 3.12 on ubuntu-latest
     - Trigger: push + PR to main

   .github/workflows/validate.yml:
     - python3 core/intelligence/validation/validate_json_integrity.py
     - node bin/pre-publish-gate.js
     - Trigger: PR to main only

3. NO multi-OS matrix (MB is single-user, always macOS).
   NO Docker workflow (no Docker yet).
   NO release automation (npm publish is separate).
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 1.2.1 | Delete decorative CI | TD-019 | 15m | LOW |
| 1.2.2 | lint.yml workflow | SS pattern | 2h | LOW |
| 1.2.3 | test.yml workflow | SS pattern | 1h | LOW |
| 1.2.4 | validate.yml workflow | SS pattern | 1h | LOW |

### 1.3 Lightweight Extractors (no SS dependency)

Install small, focused libraries directly in MB's venv for the two
most common input formats. These work WITHOUT SS installed.

```
ACTION ITEMS:

1. pip install pymupdf mammoth
   Add to pyproject.toml [project.optional-dependencies]:
   extractors = ["pymupdf>=1.24.0", "mammoth>=1.8.0"]

2. Create core/intelligence/pipeline/extractors/__init__.py
3. Create core/intelligence/pipeline/extractors/pdf_extractor.py
   - extract_pdf(path) -> str (markdown text)
   - Uses pymupdf for text + table extraction
   - Returns clean markdown ready for inbox

4. Create core/intelligence/pipeline/extractors/docx_extractor.py
   - extract_docx(path) -> str (markdown text)
   - Uses mammoth for .docx -> markdown
   - Integrates with inbox_organizer.py pre-processing
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 1.3.1 | pymupdf + mammoth deps | SS inspired | 15m | LOW |
| 1.3.2 | pdf_extractor.py | New (using pymupdf) | 2h | LOW |
| 1.3.3 | docx_extractor.py | New (using mammoth) | 2h | LOW |
| 1.3.4 | Integration with inbox_organizer | New | 1h | LOW |

### 1.4 Strategy Pattern for Future Exports (from SS)

Adopt the SkillAdaptor ABC pattern from SS, adapted for MB's domain.
This is STRUCTURE ONLY -- no actual adaptors yet.

```
ACTION ITEMS:

1. Create core/intelligence/export/__init__.py
2. Create core/intelligence/export/base.py:

   class KnowledgeExporter(ABC):
       PLATFORM: str = "unknown"

       @abstractmethod
       def format_playbook(self, playbook_path: Path, metadata: dict) -> str: ...

       @abstractmethod
       def format_dna(self, dna_path: Path, metadata: dict) -> str: ...

       @abstractmethod
       def export(self, content: str, output_path: Path) -> Path: ...

3. Create core/intelligence/export/markdown_exporter.py:
   - First concrete implementation
   - Exports playbooks as clean markdown (trivial but validates pattern)
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 1.4.1 | KnowledgeExporter ABC | SS Strategy Pattern | 1h | LOW |
| 1.4.2 | MarkdownExporter | New | 1h | LOW |

---

## Phase 2: Bridge Module (Week 2-3)

Create the bridge between MB and SS. SS is called via subprocess.
SS must be installed in an isolated venv.

### 2.1 SS Installation Script

```
ACTION ITEMS:

1. Create bin/install-skill-seekers.sh:
   #!/bin/bash
   VENV_PATH="${HOME}/.venvs/skill-seekers"

   if [ -d "$VENV_PATH" ]; then
     echo "Skill Seekers venv already exists at $VENV_PATH"
     exit 0
   fi

   python3 -m venv "$VENV_PATH"
   "$VENV_PATH/bin/pip" install skill-seekers

   # Verify installation
   "$VENV_PATH/bin/skill-seekers-pdf" --version
   echo "Skill Seekers installed successfully"

2. Create bin/install-skill-seekers-video.sh:
   # Separate because video pulls pytorch (~2GB)
   VENV_PATH="${HOME}/.venvs/skill-seekers"
   "$VENV_PATH/bin/pip" install "skill-seekers[video-full]"

3. Add to reference/ONBOARDING-GUIDE.md (when created):
   - SS installation is OPTIONAL
   - MB works without SS (pymupdf/mammoth fallbacks)
   - SS adds: video pipeline, web scraping, advanced chunking
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 2.1.1 | install-skill-seekers.sh | New | 30m | LOW |
| 2.1.2 | install-skill-seekers-video.sh | New | 15m | LOW |

### 2.2 Bridge Module

```
ACTION ITEMS:

1. Create core/intelligence/pipeline/ss_bridge_config.yaml:
   skill_seekers:
     venv_path: "~/.venvs/skill-seekers"
     timeout_seconds: 300
     output_format: "markdown"
     fallback_enabled: true

2. Create core/intelligence/pipeline/ss_bridge.py:

   Key functions:

   def is_ss_available() -> bool:
       """Check if SS venv exists and is functional."""

   def call_ss(command: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
       """Execute SS CLI command in isolated venv."""

   def ingest_pdf(pdf_path: Path, source_tag: str) -> Path:
       """Process PDF via SS or fallback to pymupdf."""
       output_dir = KNOWLEDGE_EXTERNAL / "inbox" / source_tag
       if is_ss_available():
           call_ss(["skill-seekers-pdf", "--file", str(pdf_path),
                     "--output", str(output_dir), "--format", "markdown"])
       else:
           from .extractors.pdf_extractor import extract_pdf
           text = extract_pdf(pdf_path)
           (output_dir / pdf_path.stem + ".md").write_text(text)
       return output_dir

   def ingest_docx(docx_path: Path, source_tag: str) -> Path:
       """Process DOCX via SS or fallback to mammoth."""

   def ingest_video(url: str, source_tag: str) -> Path:
       """Process video via SS. No fallback (SS required)."""
       if not is_ss_available():
           raise RuntimeError("Skill Seekers not installed. Run bin/install-skill-seekers-video.sh")

   def ingest_website(url: str, source_tag: str) -> Path:
       """Scrape website via SS. No fallback (SS required)."""

3. Register in core/paths.py ROUTING:
   "ss_bridge_config": ROOT / "core" / "intelligence" / "pipeline" / "ss_bridge_config.yaml"
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 2.2.1 | ss_bridge_config.yaml | New | 15m | LOW |
| 2.2.2 | ss_bridge.py | New | 4h | MED |
| 2.2.3 | Register in paths.py | New | 5m | LOW |

### 2.3 Integration with Existing Pipeline

```
ACTION ITEMS:

1. Update inbox_organizer.py:
   - Before moving files, check extension
   - If .pdf: call ss_bridge.ingest_pdf() to extract text
   - If .docx: call ss_bridge.ingest_docx() to extract text
   - Result: inbox always contains .txt/.md (never raw binary)

2. Create /ingest-file skill:
   .claude/skills/ingest-file/SKILL.md
   - Auto-Trigger: "ingest file", "process pdf", "process docx"
   - Keywords: "ingest", "pdf", "docx", "video", "file"
   - Calls ss_bridge functions based on file type

3. Add tests:
   tests/python/test_ss_bridge.py
   - test_is_ss_available_when_missing (returns False)
   - test_pdf_fallback_to_pymupdf
   - test_docx_fallback_to_mammoth
   - test_video_requires_ss (raises RuntimeError)
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 2.3.1 | inbox_organizer.py update | Modify existing | 3h | MED |
| 2.3.2 | /ingest-file skill | New | 1h | LOW |
| 2.3.3 | Bridge tests | New | 3h | LOW |

### 2.4 Video Pipeline Integration

This is the highest-value integration. MB currently has NO native video
processing for educational content (courses, YouTube).

```
ACTION ITEMS:

1. Ensure SS video-full is installed:
   bin/install-skill-seekers-video.sh

2. Add video_extractor.py to extractors/:
   - Wraps skill-seekers-video CLI
   - Supports: YouTube URL, local file, playlist
   - Output: transcript .txt + frame screenshots (optional)
   - Metadata: timestamps, duration, title

3. Create /ingest-video skill:
   .claude/skills/ingest-video/SKILL.md
   - Auto-Trigger: "ingest video", "process youtube", "transcribe video"
   - Keywords: "video", "youtube", "transcribe", "course video"

4. Test with real data:
   - Process one Alex Hormozi YouTube video
   - Verify output lands in knowledge/external/inbox/alex-hormozi/
   - Verify MCE pipeline can process the transcript
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 2.4.1 | video_extractor.py | SS video pipeline | 3h | MED |
| 2.4.2 | /ingest-video skill | New | 1h | LOW |
| 2.4.3 | E2E test with real video | Manual validation | 2h | MED |

---

## Phase 3: Deep Integration (Week 4-6, Conditional)

Phase 3 proceeds ONLY IF Phase 2 proves SS is reliable and valuable.
Gate: At least 5 successful ingestions via ss_bridge in production use.

### 3.1 SS MCP Server (Conditional)

```
DECISION GATE: Only proceed if:
  [ ] Phase 2 complete and validated
  [ ] 5+ successful SS ingestions recorded
  [ ] MB team wants persistent SS access (not just batch)

IF PROCEED:

1. Add SS MCP server to .mcp.json:
   "skill-seekers": {
     "command": "~/.venvs/skill-seekers/bin/skill-seekers-mcp",
     "args": ["serve"],
     "env": {}
   }

2. This gives MB access to SS's 21+ MCP tools:
   - scraping_tools (web, github)
   - splitting_tools (RAG chunking)
   - packaging_tools (format conversion)
   - source_tools (source management)
   - vector_db_tools (chroma, qdrant)

3. Update .claude/rules/mcp-governance.md with SS server entry.

IF NOT PROCEED:
   Continue using CLI subprocess bridge (Phase 2).
   No MCP overhead.
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 3.1.1 | Add SS MCP server | SS MCP | 2h | MED |
| 3.1.2 | Update MCP governance | Existing rules | 30m | LOW |

### 3.2 Quality Metrics Scorer (Inspired by SS)

```
ACTION ITEMS:

1. Create core/intelligence/validation/quality_scorer.py:
   - Numeric scoring (0-100) for extracted content
   - Dimensions: coverage, clarity, completeness, traceability
   - Persists scores in .data/quality_scores.jsonl

2. Integrate with existing quality_watchdog.py:
   - watchdog detects agent context -> scorer runs
   - Score < 50: warn (existing behavior)
   - Score logged to quality_scores.jsonl (new)

3. This replaces the textual-only quality assessment
   with persistent numeric tracking.
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 3.2.1 | quality_scorer.py | SS inspired | 4h | LOW |
| 3.2.2 | Integration with watchdog | Modify existing | 2h | LOW |

### 3.3 Incremental Update Pattern (Inspired by SS)

This is the highest-risk, highest-value pattern from SS.

```
DECISION GATE: Only proceed if:
  [ ] P0 + P1 technical debts resolved
  [ ] CI/CD running real tests
  [ ] GSD plan created and approved

ACTION ITEMS:

1. Create core/intelligence/pipeline/content_hasher.py:
   - SHA256 hash of every file entering inbox
   - Registry in .data/content_hashes.json
   - Before processing: check if hash exists
   - If exists: skip (already processed)
   - If new: process normally

2. Update batch_governor.py:
   - Before creating batch: filter out already-hashed files
   - After processing batch: register hashes
   - Result: re-running pipeline is idempotent

3. This addresses the core problem: MB reprocesses everything
   from scratch on every run. With 50+ meetings and 200+
   transcriptions, full reprocessing is unsustainable.
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 3.3.1 | content_hasher.py | SS sync pattern | 4h | HIGH |
| 3.3.2 | batch_governor.py update | Modify existing | 8h | HIGH |
| 3.3.3 | Hash registry in .data/ | New | 1h | LOW |

### 3.4 Embedding Server Pattern (Inspired by SS)

```
ACTION ITEMS:

1. Create core/intelligence/rag/embedding_server.py:
   - FastAPI server for embedding generation
   - Supports VoyageAI (primary) and sentence-transformers (fallback)
   - Local cache in .data/embedding_cache/
   - Batch processing support

2. Create docker-compose.yml (first Docker artifact):
   - rag-server: BM25 + embedding server
   - Ports: 8100 (embedding), 8101 (search)

3. Update hybrid_index.py to call embedding server
   instead of VoyageAI directly.
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 3.4.1 | embedding_server.py | SS embedding pattern | 8h | MED |
| 3.4.2 | docker-compose.yml | SS Docker pattern | 2h | LOW |
| 3.4.3 | hybrid_index.py update | Modify existing | 2h | MED |

### 3.5 Vector DB Integration (Inspired by SS)

```
DECISION GATE: Only proceed if:
  [ ] Embedding server operational
  [ ] Knowledge base exceeds 10K chunks

ACTION ITEMS:

1. pip install chromadb in MB venv
2. Create core/intelligence/rag/vector_store.py:
   - Abstract VectorStore interface (inspired by SS SkillAdaptor)
   - ChromaStore implementation (first concrete)
   - Interface allows swapping to Qdrant/FAISS later

3. Update hybrid_index.py:
   - Replace JSON file storage with ChromaDB
   - Keep BM25 for lexical search (hybrid = BM25 + vector)
```

| # | Item | Source | Effort | Risk |
|---|------|--------|--------|------|
| 3.5.1 | VectorStore ABC | SS Strategy Pattern | 2h | LOW |
| 3.5.2 | ChromaStore implementation | SS + chromadb | 4h | MED |
| 3.5.3 | hybrid_index.py migration | Modify existing | 4h | HIGH |

---

## Per-Item Implementation Plan (Complete)

All 26 deliverables across all phases, ordered by execution sequence.

```
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
| #    | PHASE | ITEM                               | APPROACH | SOURCE      | DEST (MB) | EFFORT | RISK |
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
|  0.1 |   0   | Resolve 8 P0 technical debts       | FIX      | tech-debt   | core/     | 14.5h  | MED  |
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
|  1.1 |   1   | conftest.py + markers + coverage    | ADOPT    | SS pattern  | tests/    |  2.5h  | LOW  |
|  1.2 |   1   | Tests: paths, classifier, memory    | NEW      | MB-specific | tests/    | 12h    | LOW  |
|  1.3 |   1   | Delete decorative CI                | FIX      | TD-019      | .github/  | 15m    | LOW  |
|  1.4 |   1   | lint.yml workflow                   | ADOPT    | SS pattern  | .github/  |  2h    | LOW  |
|  1.5 |   1   | test.yml workflow                   | ADOPT    | SS pattern  | .github/  |  1h    | LOW  |
|  1.6 |   1   | validate.yml workflow               | ADOPT    | SS pattern  | .github/  |  1h    | LOW  |
|  1.7 |   1   | pymupdf + mammoth in pyproject      | USE LIB  | SS inspired | pyproject |  15m   | LOW  |
|  1.8 |   1   | pdf_extractor.py                    | NEW      | pymupdf     | pipeline/ |  2h    | LOW  |
|  1.9 |   1   | docx_extractor.py                   | NEW      | mammoth     | pipeline/ |  2h    | LOW  |
| 1.10 |   1   | inbox_organizer.py integration      | MODIFY   | MB-specific | pipeline/ |  1h    | LOW  |
| 1.11 |   1   | KnowledgeExporter ABC               | ADOPT    | SS Strategy | export/   |  1h    | LOW  |
| 1.12 |   1   | MarkdownExporter                    | NEW      | MB-specific | export/   |  1h    | LOW  |
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
|  2.1 |   2   | install-skill-seekers.sh            | NEW      | Integration | bin/      |  30m   | LOW  |
|  2.2 |   2   | ss_bridge_config.yaml               | NEW      | Integration | pipeline/ |  15m   | LOW  |
|  2.3 |   2   | ss_bridge.py                        | NEW      | Integration | pipeline/ |  4h    | MED  |
|  2.4 |   2   | inbox_organizer.py SS integration   | MODIFY   | Integration | pipeline/ |  3h    | MED  |
|  2.5 |   2   | /ingest-file skill                  | NEW      | Integration | .claude/  |  1h    | LOW  |
|  2.6 |   2   | Bridge tests                        | NEW      | Integration | tests/    |  3h    | LOW  |
|  2.7 |   2   | video_extractor.py                  | NEW      | SS video    | pipeline/ |  3h    | MED  |
|  2.8 |   2   | /ingest-video skill                 | NEW      | Integration | .claude/  |  1h    | LOW  |
|  2.9 |   2   | E2E video test                      | TEST     | Validation  | manual    |  2h    | MED  |
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
|  3.1 |   3   | SS MCP server (conditional)         | MCP      | SS MCP      | .mcp.json |  2.5h  | MED  |
|  3.2 |   3   | quality_scorer.py                   | ADOPT    | SS inspired | validation|  6h    | LOW  |
|  3.3 |   3   | Incremental updates (conditional)   | ADOPT    | SS sync     | pipeline/ | 13h    | HIGH |
|  3.4 |   3   | Embedding server (conditional)      | ADOPT    | SS embedding| rag/      | 12h    | MED  |
|  3.5 |   3   | Vector DB integration (conditional) | ADOPT    | SS + chroma | rag/      | 10h    | HIGH |
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
|      |       | TOTAL                              |          |             |           | ~99h   |      |
|      |       | Phase 0 (P0 debt)                  |          |             |           |  14.5h |      |
|      |       | Phase 1 (foundation)               |          |             |           |  27h   |      |
|      |       | Phase 2 (bridge)                    |          |             |           |  18h   |      |
|      |       | Phase 3 (deep, conditional)         |          |             |           |  43.5h |      |
+------+-------+------------------------------------+----------+-------------+-----------+--------+------+
```

---

## Dependency Management

### What Goes Where

```
MB's pyproject.toml (direct dependencies):
  [project.optional-dependencies]
  extractors = [
      "pymupdf>=1.24.0",     # PDF text extraction (5MB)
      "mammoth>=1.8.0",       # DOCX -> markdown (<1MB)
  ]
  embedding = [
      "fastapi>=0.115.0",     # Embedding server (Phase 3)
      "uvicorn>=0.34.0",      # ASGI server (Phase 3)
  ]
  vectordb = [
      "chromadb>=0.5.0",      # Vector store (Phase 3)
  ]

SS's isolated venv (~/.venvs/skill-seekers/):
  pip install skill-seekers              # Base (PDF, DOCX, web)
  pip install skill-seekers[video-full]  # + video (pytorch, whisper)

  NEVER install SS in MB's venv.
  NEVER import SS modules from MB code.
  ALL interaction is via subprocess.
```

### Dependency Tree Comparison

```
MB venv (lean):                    SS venv (heavy):
  pyyaml                            langchain >= 1.2.10
  anthropic                         llama-index >= 0.14.15
  httpx                             chromadb
  pymupdf (optional)                anthropic >= 0.76.0
  mammoth (optional)                httpx >= 0.28.1
  chromadb (Phase 3, optional)      pytesseract (video)
                                    opencv-python (video)
                                    faster-whisper (video)
                                    yt-dlp (video)
                                    torch (video)

  ~50MB total                       ~500MB - 2.5GB total
```

---

## Rollback Strategy

### Phase 1 Rollback (trivial)

```
Phase 1 creates NEW files only (tests, CI workflows, extractors, ABC).
Rollback: Delete the new files. Zero impact on existing code.

Specific reversals:
- Tests: rm -rf tests/python/test_paths.py tests/conftest.py etc.
- CI: git revert the workflow commits
- Extractors: rm -rf core/intelligence/pipeline/extractors/
- Export ABC: rm -rf core/intelligence/export/
- Dependencies: pip uninstall pymupdf mammoth
```

### Phase 2 Rollback (easy)

```
Phase 2 creates bridge module + modifies inbox_organizer.py.
Rollback:
  1. Revert inbox_organizer.py changes (git checkout)
  2. Delete bridge files: ss_bridge.py, ss_bridge_config.yaml
  3. Delete extractors that wrap SS
  4. Delete skills: /ingest-file, /ingest-video
  5. Optionally delete SS venv: rm -rf ~/.venvs/skill-seekers/

  MB continues working with manual file ingestion (status quo).
```

### Phase 3 Rollback (moderate)

```
Phase 3 items are individually reversible because each is behind a gate:

- MCP server: Remove entry from .mcp.json
- Quality scorer: Delete quality_scorer.py, revert watchdog
- Incremental updates: Delete content_hasher.py, revert batch_governor
- Embedding server: Delete embedding_server.py, revert hybrid_index
- ChromaDB: Delete vector_store.py, revert hybrid_index to JSON

The riskiest rollback is hybrid_index.py (3.5.3) because it changes
the RAG storage backend. ALWAYS keep JSON files as backup during
migration. Never delete .data/rag_expert/ JSON files until ChromaDB
is validated for 30+ days.
```

---

## Success Criteria

### Phase 1 Success (all must pass)

```
[ ] CI runs ruff on every PR and FAILS on lint errors
[ ] CI runs pytest on every PR and FAILS on test failures
[ ] 100+ tests exist with 30%+ coverage on core/
[ ] PDF extraction works: python3 -c "from core.intelligence.pipeline.extractors.pdf_extractor import extract_pdf"
[ ] DOCX extraction works: python3 -c "from core.intelligence.pipeline.extractors.docx_extractor import extract_docx"
[ ] KnowledgeExporter ABC importable: python3 -c "from core.intelligence.export.base import KnowledgeExporter"
```

### Phase 2 Success (all must pass)

```
[ ] SS venv installable: bin/install-skill-seekers.sh exits 0
[ ] Bridge detects SS: python3 -c "from core.intelligence.pipeline.ss_bridge import is_ss_available; print(is_ss_available())"
[ ] PDF via bridge: ingest_pdf("test.pdf", "test-source") produces .md in inbox
[ ] DOCX via bridge: ingest_docx("test.docx", "test-source") produces .md in inbox
[ ] PDF fallback works when SS not installed
[ ] DOCX fallback works when SS not installed
[ ] Video via bridge: ingest_video("https://youtube.com/...", "test") produces transcript
[ ] MCE pipeline processes bridge output without errors
[ ] 5+ bridge tests pass
```

### Phase 3 Success (per sub-phase)

```
3.1 MCP: SS MCP tools accessible from Claude Code session
3.2 Quality: quality_scorer.py produces numeric scores, logged to .data/
3.3 Incremental: Re-running pipeline on same data skips already-processed files
3.4 Embedding: Embedding server responds at localhost:8100/embed
3.5 Vector: RAG queries use ChromaDB backend, latency <= 5s for top-10 results
```

---

## Timeline

```
+-----------------------------------------------------------------------+
| WEEK | PHASE | FOCUS                          | DELIVERABLES           |
+------+-------+--------------------------------+------------------------+
|  0   |   0   | P0 Technical Debt              | 8 critical debts fixed |
|      |       | (BLOCKING -- must complete      | CI actually works      |
|      |       |  before anything else)          | Codebase clean         |
+------+-------+--------------------------------+------------------------+
|  1   |   1   | Foundation                     | Tests + CI + extractors|
|      |       | Zero-risk pattern adoption      | + ABC pattern          |
|      |       | No SS dependency yet            | 100+ tests, real CI    |
+------+-------+--------------------------------+------------------------+
|  2   |   2   | Bridge (Part 1)                | ss_bridge.py           |
|      |       | Install SS, create bridge       | PDF/DOCX via bridge    |
|      |       |                                | /ingest-file skill     |
+------+-------+--------------------------------+------------------------+
|  3   |   2   | Bridge (Part 2)                | Video pipeline         |
|      |       | Video integration, E2E test     | /ingest-video skill    |
|      |       |                                | E2E validation         |
+------+-------+--------------------------------+------------------------+
|  4   |   3   | Deep (Conditional)             | Quality scorer         |
|      |       | Only if Phase 2 validated       | Incremental updates    |
|      |       | GATE: 5+ successful ingestions  |                        |
+------+-------+--------------------------------+------------------------+
| 5-6  |   3   | Deep (Conditional)             | Embedding server       |
|      |       | Only if continued need          | Vector DB migration    |
|      |       | GATE: 10K+ chunks              | MCP integration        |
+------+-------+--------------------------------+------------------------+
|      |       |                                |                        |
| TOTAL|       | 6 weeks (Phase 0-2 firm,       | ~99h total effort      |
|      |       |  Phase 3 conditional)           | ~60h firm, ~40h cond.  |
+------+-------+--------------------------------+------------------------+
```

---

## What NOT To Do

```
+-----------------------------------------------------------------------+
| EXPLICITLY REJECTED ITEMS                                              |
+-----------------------------------------------------------------------+
|                                                                        |
| 1. DO NOT pip install skill-seekers in MB's venv                       |
|    Reason: langchain + llama-index + pytorch contaminate deps          |
|                                                                        |
| 2. DO NOT fork Skill Seekers                                           |
|    Reason: Maintenance burden. Use as external tool.                   |
|                                                                        |
| 3. DO NOT adopt SS's 16 platform adaptors                              |
|    Reason: MB is internal. No need to export to Notion/Confluence.     |
|    Revisit only if MB becomes a product.                               |
|                                                                        |
| 4. DO NOT adopt K8s manifests                                          |
|    Reason: Single-user local tool. Overengineering.                    |
|                                                                        |
| 5. DO NOT refactor MB CLI to match SS's click-based structure          |
|    Reason: MB's slash commands run inside Claude Code. Different UX.   |
|    Refactoring would break 90+ skills and all user muscle memory.      |
|                                                                        |
| 6. DO NOT copy SS's 2,540 tests                                       |
|    Reason: Different domain. Write MB-specific tests.                  |
|                                                                        |
| 7. DO NOT adopt SS's 63 workflow presets                               |
|    Reason: Designed for software projects, not knowledge management.   |
|                                                                        |
| 8. DO NOT start Phase 2 before Phase 0 (P0 debts) is complete         |
|    Reason: Building integration on decorative CI and duplicate         |
|    modules is architecturally unsound.                                 |
|                                                                        |
+-----------------------------------------------------------------------+
```

---

## Risk Matrix

```
+----+------------------------------------+---------+--------+-----------------------------+
| #  | RISK                               | PROB    | IMPACT | MITIGATION                  |
+----+------------------------------------+---------+--------+-----------------------------+
| R1 | SS subprocess fails silently       | MEDIUM  | HIGH   | Check exit code + stderr    |
|    |                                    |         |        | in ss_bridge.py. Timeout    |
|    |                                    |         |        | at 300s. Log all calls.     |
+----+------------------------------------+---------+--------+-----------------------------+
| R2 | SS version upgrade breaks CLI      | LOW     | HIGH   | Pin SS version in install   |
|    | interface                          |         |        | script. Test after upgrade. |
+----+------------------------------------+---------+--------+-----------------------------+
| R3 | SS project abandoned               | LOW     | MEDIUM | Phase 1 extractors work     |
|    |                                    |         |        | without SS. Only Phase 2    |
|    |                                    |         |        | video depends on SS.        |
+----+------------------------------------+---------+--------+-----------------------------+
| R4 | Video pipeline pulls 2GB pytorch   | CERTAIN | LOW    | Separate install script.    |
|    |                                    |         |        | Only install if needed.     |
+----+------------------------------------+---------+--------+-----------------------------+
| R5 | SS output format incompatible      | MEDIUM  | MEDIUM | Bridge module normalizes    |
|    | with MCE pipeline                  |         |        | output before writing to    |
|    |                                    |         |        | inbox. Format adapter in    |
|    |                                    |         |        | ss_bridge.py.               |
+----+------------------------------------+---------+--------+-----------------------------+
| R6 | ChromaDB migration loses data      | LOW     | HIGH   | Keep JSON backup during     |
|    |                                    |         |        | transition. Never delete    |
|    |                                    |         |        | .data/rag_expert/ until     |
|    |                                    |         |        | ChromaDB validated 30 days. |
+----+------------------------------------+---------+--------+-----------------------------+
| R7 | Incremental hash breaks            | MEDIUM  | HIGH   | Content hash is additive.   |
|    | reprocessing capability            |         |        | --force flag bypasses hash  |
|    |                                    |         |        | check for full reprocess.   |
+----+------------------------------------+---------+--------+-----------------------------+
```

---

## Connection to Technical Debt

This plan addresses or unblocks the following items from `docs/prd/technical-debt-assessment.md`:

| Debt ID | Description | How This Plan Addresses It |
|---------|-------------|---------------------------|
| TD-019 | Decorative CI | Phase 1.2: Real CI/CD workflows |
| TD-010 | Low test coverage | Phase 1.1: Test infrastructure + 100 tests |
| TD-009 | 352 ruff errors | Phase 0: P0 debt resolution |
| TD-001 | 21 duplicate modules | Phase 0: P0 debt resolution |
| TD-004 | 92 stale path references | Phase 0: P0 debt resolution |
| TD-031 | RAG business index not built | Phase 3.5: Vector DB migration |

Items NOT addressed by this plan (remain in backlog):
TD-006 (hook matchers), TD-020 (timeout budget), TD-027 (rule pruning),
TD-018 (JSON schema validation), TD-026 (capstone docs).

---

*Tiny Rick -- TINY RICK! The equations balance PERFECTLY! Two DIFFERENT systems, one SURGICAL integration! SS is the stomach, MB is the brain! Subprocess isolation means ZERO contamination! The bridge module has fallbacks for EVERYTHING! Phase 0 is non-negotiable because building on DECORATIVE CI is building on LIES! TINY RICK!*
