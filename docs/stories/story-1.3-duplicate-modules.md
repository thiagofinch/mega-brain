# Story 1.3: Codebase -- Eliminate Duplicate Modules

> **Story ID:** STORY-TD-1.3
> **Epic:** EPIC-TD-001
> **Sprint:** 1
> **Priority:** P0 CRITICAL
> **Debitos:** TD-001 (21 duplicate Python modules), TD-003 (version mismatch)

---

## Context

21 Python modules exist as identical copies at `core/intelligence/` root AND in their proper subdirectory (`pipeline/`, `entities/`, `validation/`, `dossier/`, `roles/`). A reorganization moved files into subdirectories but never deleted the originals. This means editing the wrong copy silently discards work -- the canonical copy in the subdirectory is what gets imported. Additionally, `package.json` says version 1.4.0 while `pyproject.toml` says 1.3.0.

---

## Tasks

### TD-003: Sync Package Versions

- [ ] Open `pyproject.toml`, update `version = "1.3.0"` to `version = "1.4.0"`
- [ ] Verify with: `python3 -c "import json,tomllib; p=json.load(open('package.json')); t=tomllib.load(open('pyproject.toml','rb')); assert p['version']==t['project']['version'], f'{p[\"version\"]} != {t[\"project\"][\"version\"]}'"`
- [ ] Consider adding a VERSION file or cross-check script for future sync

### TD-001: Pre-Deletion Import Fix

Before deleting any duplicate, fix the one known cross-import:

- [ ] Open `core/intelligence/pipeline/autonomous_processor.py` (the CANONICAL copy)
- [ ] Find import: `from core.intelligence.task_orchestrator import TaskOrchestrator`
- [ ] Change to: `from core.intelligence.pipeline.task_orchestrator import TaskOrchestrator`
- [ ] Verify: `python3 -c "from core.intelligence.pipeline.autonomous_processor import AutonomousProcessor"`

### TD-001: Systematic Deletion (21 files)

Delete in batches, smoke-test after each batch:

**Batch A: pipeline/ duplicates (4 files)**
- [ ] Delete `core/intelligence/autonomous_processor.py`
- [ ] Delete `core/intelligence/session_autosave.py`
- [ ] Delete `core/intelligence/sync_package_files.py`
- [ ] Delete `core/intelligence/task_orchestrator.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.pipeline.task_orchestrator import TaskOrchestrator"`

**Batch B: entities/ duplicates (5 files)**
- [ ] Delete `core/intelligence/bootstrap_registry.py`
- [ ] Delete `core/intelligence/business_model_detector.py`
- [ ] Delete `core/intelligence/entity_normalizer.py`
- [ ] Delete `core/intelligence/org_chain_detector.py`
- [ ] Delete `core/intelligence/role_detector.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.entities.entity_normalizer import EntityNormalizer"`

**Batch C: validation/ duplicates (4 files)**
- [ ] Delete `core/intelligence/audit_layers.py`
- [ ] Delete `core/intelligence/validate_json_integrity.py`
- [ ] Delete `core/intelligence/validate_layers.py`
- [ ] Delete `core/intelligence/verify_classifications.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.validation.validate_layers import validate_layers"`

**Batch D: dossier/ duplicates (3 files)**
- [ ] Delete `core/intelligence/dossier_trigger.py`
- [ ] Delete `core/intelligence/review_dashboard.py`
- [ ] Delete `core/intelligence/theme_analyzer.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.dossier.theme_analyzer import ThemeAnalyzer"`

**Batch E: roles/ duplicates (3 files)**
- [ ] Delete `core/intelligence/skill_generator.py`
- [ ] Delete `core/intelligence/sow_generator.py`
- [ ] Delete `core/intelligence/viability_scorer.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.roles.sow_generator import SOWGenerator"`

**Batch F: agents/ duplicate (1 file)**
- [ ] Delete `core/intelligence/agent_trigger.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.agents.agent_trigger import AgentTrigger"`

**Batch G: roles/ remaining (1 file)**
- [ ] Delete `core/intelligence/tool_discovery.py`
- [ ] Smoke test: `python3 -c "from core.intelligence.roles.tool_discovery import ToolDiscovery"`

### Post-Deletion Validation

- [ ] Confirm root-only files were NOT deleted: `ls core/intelligence/context_scorer.py core/intelligence/memory_manager.py`
- [ ] Run full test suite: `python3 -m pytest tests/python/ -v`
- [ ] Verify RAG pipeline: `python3 -c "from core.intelligence.rag.pipeline import RAGPipeline"`

---

## Acceptance Criteria

- [ ] `ls core/intelligence/*.py | grep -v __init__ | wc -l` returns exactly 2 (context_scorer.py + memory_manager.py)
- [ ] `package.json` version = `pyproject.toml` version = 1.4.0
- [ ] `python3 -m pytest tests/python/ -v` passes with 0 failures
- [ ] `python3 -c "from core.intelligence.rag.pipeline import RAGPipeline"` succeeds
- [ ] No import errors from any canonical module

---

## Technical Notes

**DO NOT DELETE these root-only files (they are NOT duplicates):**

| File | Why It Must Stay |
|------|-----------------|
| `context_scorer.py` | Root-only. Imported by `rag/pipeline.py` (2 references) |
| `memory_manager.py` | Root-only. Imported by `context_scorer.py` (2 references) and `rag/pipeline.py` (1 reference) |

**Import fix is CRITICAL:** The root `autonomous_processor.py` imports `task_orchestrator` via `from core.intelligence.task_orchestrator`. The CANONICAL copy at `pipeline/autonomous_processor.py` must have this import updated to `from core.intelligence.pipeline.task_orchestrator` BEFORE the root duplicate is deleted. Otherwise the canonical copy breaks.

**Batch approach rationale:** Deleting all 21 at once is risky. Batching by subdirectory with smoke tests after each batch catches any unexpected cross-imports early.

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Version sync (TD-003) | 0.15h |
| Pre-deletion import fix | 0.25h |
| Delete 21 files in 7 batches + smoke tests | 2.5h |
| Post-deletion full test suite + validation | 1h |
| **Total** | **~4h** |

---

## Dependencies

| Dependency | Reason |
|------------|--------|
| Story 1.4 (paths) | Ideally stale `agents/minds/` refs are fixed first so ruff error count is accurate post-deletion. Soft dependency. |

---

## Definition of Done

- [ ] Exactly 2 `.py` files remain in `core/intelligence/` root (excluding `__init__.py`)
- [ ] Both manifest versions are synced at 1.4.0
- [ ] All tests pass
- [ ] RAG pipeline imports succeed
- [ ] No runtime import errors from any module that previously imported from root
