# Story 1.4: Paths -- Fix Stale References to agents/minds/

> **Story ID:** STORY-TD-1.4
> **Epic:** EPIC-TD-001
> **Sprint:** 1
> **Priority:** P0 CRITICAL
> **Debitos:** TD-004 (92 stale references across 27 files), TD-002 (AGENT-INDEX.yaml), TD-008 (agents/minds/ directory still exists)

---

## Context

`agents/minds/` was renamed to `agents/external/` during a structural migration, but 27 files across the codebase still reference the old path -- 92 occurrences total. The `AGENT-INDEX.yaml` file has 5 references to the deprecated path because the `agent_index_updater.py` hook was never updated. The `agents/minds/` directory itself still exists on disk as a strict subset of `agents/external/`.

This is the foundational cleanup that must happen BEFORE deleting the directory and BEFORE regenerating the agent index.

---

## Tasks

### TD-004: Fix 92 Stale References

**Python code files:**
- [ ] Fix `core/intelligence/audit_layers.py` (or its canonical copy in `validation/`)
- [ ] Fix `core/intelligence/verify_classifications.py` (or canonical in `validation/`)
- [ ] Fix `core/intelligence/pipeline/pipeline_heal.py`
- [ ] Fix `scripts/validate_cascading_integrity.py`

**Config files:**
- [ ] Fix `agents/AGENT-INDEX.yaml` (5 references)
- [ ] Fix `agents/persona-registry.yaml` (6 references)
- [ ] Fix `.gitignore`
- [ ] Fix `.npmignore`
- [ ] Fix `.windsurf/agents.yaml` (if exists)
- [ ] Fix `.cursor/agents.yaml` (if exists)
- [ ] Fix `.claude/agents.yaml` (if exists)

**Hooks:**
- [ ] Fix `.claude/hooks/agent_index_updater.py` -- update to emit `agents/external/` paths

**Rules and documentation:**
- [ ] Fix `.claude/rules/directory-contract.md`
- [ ] Fix `.claude/CLAUDE.md` (Layer System table and architecture diagram)
- [ ] Fix `reference/LAYERS.md`
- [ ] Fix `reference/architecture/BROWNFIELD-MEGABRAIN.md`
- [ ] Fix `reference/MEGABRAIN-3D-ARCHITECTURE.md`
- [ ] Fix `docs/reports/CROSS-REPO-ANALYSIS.md` (if it exists as a live doc, not historical)

**Artifacts (historical records -- decision needed):**
- [ ] `artifacts/AUDIT-REPORT.json` has 30 occurrences. Decision: update the path references but add a note "Updated from agents/minds/ to agents/external/ on 2026-03-XX" so the historical context is preserved.
- [ ] Other artifact files: same approach (update + note)

**Method:** Global find-and-replace `agents/minds/` to `agents/external/` with manual review of each match.

```bash
# Find all occurrences
grep -r "agents/minds/" . --include="*.{py,md,yaml,json,yml,txt}" -l

# For each file, review and replace
# Do NOT blind sed -- some contexts may need different handling
```

### TD-002: Regenerate AGENT-INDEX.yaml

After fixing all references:
- [ ] Update `agent_index_updater.py` to emit `agents/external/` paths
- [ ] Run the index updater to regenerate `AGENT-INDEX.yaml`
- [ ] Verify all paths in the generated file point to `agents/external/`
- [ ] Update `persona-registry.yaml` if not already covered in TD-004

### TD-008: Delete agents/minds/ Directory

After ALL references are fixed:
- [ ] Verify `agents/minds/` is a strict subset of `agents/external/`: compare directory trees
- [ ] Delete `agents/minds/` directory
- [ ] Verify: `ls agents/minds/ 2>/dev/null` returns error

### Post-Fix Validation

- [ ] `grep -r "agents/minds/" . --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" --include="*.yml"` returns 0 results
- [ ] `python3 -m pytest tests/python/ -v` passes
- [ ] Agent discovery still works (test loading an agent from `agents/external/`)

---

## Acceptance Criteria

- [ ] `grep -r "agents/minds/" . --include="*.{py,md,yaml,json,yml}"` returns 0 results
- [ ] `agents/minds/` directory does not exist
- [ ] `AGENT-INDEX.yaml` references only `agents/external/` paths
- [ ] `persona-registry.yaml` references only `agents/external/` paths
- [ ] `agent_index_updater.py` generates `agents/external/` paths
- [ ] All tests pass after the changes

---

## Technical Notes

**Why 92, not 51:** The original DRAFT counted 51 references across 24 files. The QA verification plus expanded search (including `.npmignore`, cursor/windsurf configs, and artifact files) uncovered 92 across 27 files.

**Historical artifacts:** Files in `artifacts/` and `outputs/` are historical records. The assessment recommends updating the paths but adding a note about the change. This preserves the historical record while eliminating stale references that confuse tooling.

**Dynamic path construction:** Some Python scripts construct paths dynamically (e.g., `Path("agents") / agent_type / agent_name`). These use variables, not hardcoded "minds", so they should work after the directory rename. However, verify with a runtime test.

**Dependency chain:**
```
TD-004 (fix refs) -> TD-002 (regenerate index) -> TD-008 (delete directory)
```
Execute in this exact order. Deleting the directory before fixing references will break imports and agent discovery.

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Fix 92 references across 27 files (TD-004) | 2.5h |
| Update agent_index_updater.py + regenerate (TD-002) | 0.75h |
| Delete agents/minds/ + verify (TD-008) | 0.25h |
| Post-fix validation (grep + tests) | 0.5h |
| **Total** | **~4h** |

---

## Dependencies

| Dependency | Reason |
|------------|--------|
| None | This story has no blockers. It SHOULD be done before Story 1.3 (duplicates) for accurate ruff counts, and MUST be done before Story 1.2 (CI) for a clean lint baseline. |

**This story BLOCKS:**
- Story 1.3 (duplicate deletion -- ruff count depends on clean references)
- Story 1.2 (CI rewrite -- CI should lint a clean codebase)

---

## Definition of Done

- [ ] Zero references to `agents/minds/` anywhere in the codebase
- [ ] `agents/minds/` directory physically deleted
- [ ] `AGENT-INDEX.yaml` regenerated with correct paths
- [ ] `agent_index_updater.py` updated to emit correct paths
- [ ] All tests pass
- [ ] Agent loading from `agents/external/` works correctly
