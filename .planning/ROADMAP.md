# Roadmap: Mega Brain Pipeline Hardening

**Created:** 2026-02-27
**Last Updated:** 2026-02-27

## Milestones

- ✅ **v1.0 Pipeline Foundation** — Phases 1-3 (shipped 2026-02-27)
- ⏸️ **v1.1 Autonomous Mode** — Phases 4-6 (paused at phase 6)
- ✅ **v1.2 Layer Audit** — Phases 7-9 (shipped 2026-02-27)
- 🚧 **v1.3 NPM Packaging** — Phases 10-12 (in progress)

## Phases

<details>
<summary>✅ v1.0 Pipeline Foundation (Phases 1-3) — SHIPPED 2026-02-27</summary>

- [x] Phase 1: Data Repair (2/2 plans) — completed 2026-02-27
- [x] Phase 2: Cascading Validation (1/1 plans) — completed 2026-02-27
- [x] Phase 3: Checkpoint Hooks (1/1 plans) — completed 2026-02-27

**Archive:** [v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>⏸️ v1.1 Autonomous Mode (Phases 4-6) — PAUSED</summary>

- [x] Phase 4: Task Orchestrator (1/1 plans) — completed 2026-02-27
- [x] Phase 5: Autonomous Mode (2/2 plans) — completed 2026-02-27
- [ ] Phase 6: Integration Test — paused (not started)

</details>

<details>
<summary>✅ v1.2 Layer Audit (Phases 7-9) — SHIPPED 2026-02-27</summary>

- [x] Phase 7: Full Audit (1/1 plans) — completed 2026-02-27
- [x] Phase 8: Layer Documentation (1/1 plans) — completed 2026-02-27
- [x] Phase 9: Layer Validation (1/1 plans) — completed 2026-02-27

**Archive:** [v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)

</details>

<details open>
<summary>🚧 v1.3 NPM Packaging (Phases 10-12) — IN PROGRESS</summary>

- [x] **Phase 10: Audit Resolution** - Resolve all REVIEW items and clean DELETE candidates (completed 2026-02-27)
- [x] **Phase 11: Package Sync** - Auto-generate files field and sync package.json/.npmignore (completed 2026-02-27)
- [x] **Phase 12: Validation and Docs** - Validation script, dry-run test, pre-publish gate, README (completed 2026-02-27)

</details>

## Phase Details

### Phase 10: Audit Resolution
**Goal**: The layer audit achieves 100% coverage — every file in the repository is definitively classified, nothing left in REVIEW, and DELETE candidates removed.
**Depends on**: Phase 9 (v1.2 Layer Validation — shipped)
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04
**Success Criteria** (what must be TRUE):
  1. Running `audit_layers.py` produces a report showing 0 REVIEW items
  2. Every file that was REVIEW is now classified as L1, L2, L3, NEVER, or DELETE
  3. All DELETE candidates are removed from the repository (no stale files remain)
  4. The audit report can be regenerated cleanly, reflecting the updated classifier rules
**Plans**: TBD

### Phase 11: Package Sync
**Goal**: The package.json `files` field and `.npmignore` are automatically derived from the L1 audit — no manual curation, always in sync.
**Depends on**: Phase 10 (Audit Resolution — 0 REVIEW items required)
**Requirements**: SYNC-01, SYNC-02, SYNC-03
**Success Criteria** (what must be TRUE):
  1. A script runs and outputs the exact `files` array that should go into package.json, derived from L1 audit results
  2. package.json `files` field matches what the L1 audit identifies as publishable content
  3. `.npmignore` aligns with audit classifications — L2/L3/NEVER/DELETE patterns are excluded
**Plans**: TBD

### Phase 12: Validation and Docs
**Goal**: The package is verifiably publish-ready — an automated gate confirms npm pack contents are correct, a dry-run produces the expected file list, and consumers have a clear README.
**Depends on**: Phase 11 (Package Sync — files field synced)
**Requirements**: VAL-01, VAL-02, VAL-03, DOC-01
**Success Criteria** (what must be TRUE):
  1. A validation script compares `npm pack --dry-run` output against the L1 classification and reports PASSED or FAILED
  2. `npm pack --dry-run` produces a file list containing only L1 content (no L2/L3/NEVER files present)
  3. The pre-publish gate script exits 0 on a clean package and exits 1 if violations are found
  4. The README contains install instructions, quick start, and feature overview sufficient for a new consumer to get started
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Repair | v1.0 | 2/2 | ✅ Complete | 2026-02-27 |
| 2. Cascading Validation | v1.0 | 1/1 | ✅ Complete | 2026-02-27 |
| 3. Checkpoint Hooks | v1.0 | 1/1 | ✅ Complete | 2026-02-27 |
| 4. Task Orchestrator | v1.1 | 1/1 | ✅ Complete | 2026-02-27 |
| 5. Autonomous Mode | v1.1 | 2/2 | ✅ Complete | 2026-02-27 |
| 6. Integration Test | v1.1 | 0/? | ⏸️ Paused | - |
| 7. Full Audit | v1.2 | 1/1 | ✅ Complete | 2026-02-27 |
| 8. Layer Documentation | v1.2 | 1/1 | ✅ Complete | 2026-02-27 |
| 9. Layer Validation | v1.2 | 1/1 | ✅ Complete | 2026-02-27 |
| 10. Audit Resolution | 2/2 | Complete    | 2026-02-27 | - |
| 11. Package Sync | 2/2 | Complete    | 2026-02-27 | - |
| 12. Validation and Docs | 2/2 | Complete    | 2026-02-27 | - |

## Dependencies

```
v1.0 (SHIPPED)
├── Phase 1 ──► Phase 2 ──► Phase 3

v1.1 (PAUSED)
├── Phase 4 ──► Phase 5 ──► Phase 6 (paused)

v1.2 (SHIPPED)
└── Phase 7 ──► Phase 8 ──► Phase 9

v1.3 (IN PROGRESS)
└── Phase 10 ──► Phase 11 ──► Phase 12
```

---
*Roadmap updated: 2026-02-27 after v1.3 milestone roadmap*
