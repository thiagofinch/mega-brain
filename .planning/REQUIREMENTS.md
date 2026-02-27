# Requirements: Mega Brain Pipeline Hardening

**Defined:** 2026-02-27
**Core Value:** Publish all 3 layers — L1 public npm, L2 premium npm, L3 personal backup

## v1.3 Requirements

### Package Sync

- [x] **SYNC-01**: Sync package.json `files` with L1 audit results
- [x] **SYNC-02**: Update .npmignore to align with audit classifications
- [x] **SYNC-03**: Clean DELETE candidates from repo

### Publish L1 (Public npm)

- [ ] **PUB-01**: `npm pack --dry-run` produces correct L1-only file list
- [ ] **PUB-02**: Pre-publish gate passes (no secrets, no L2/L3)
- [ ] **PUB-03**: `npm publish` L1 package live on registry

### Publish L2 (Premium npm)

- [ ] **L2-01**: L2 build script includes L1 + populated content (minds, cargo, dossiers, playbooks, dna)
- [ ] **L2-02**: L2 package published (private npm or repo)

### Layer 3 (Personal backup)

- [ ] **L3-01**: L3 .gitignore configured (excludes secrets, includes inbox/logs/sessions)
- [ ] **L3-02**: L3 backup verified locally

## Out of Scope

| Feature | Reason |
|---------|--------|
| CI/CD pipeline | Future milestone |
| REVIEW item resolution | Not blocking publish |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SYNC-01 | Phase 11 | Done |
| SYNC-02 | Phase 11 | Done |
| SYNC-03 | Phase 11 | Done |
| PUB-01 | Phase 10 | Pending |
| PUB-02 | Phase 10 | Pending |
| PUB-03 | Phase 10 | Pending |
| L2-01 | Phase 11 | Pending |
| L2-02 | Phase 11 | Pending |
| L3-01 | Phase 12 | Pending |
| L3-02 | Phase 12 | Pending |

**Coverage:**
- v1.3 requirements: 10 total
- Mapped to phases: 10 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-02-27*
*Last updated: 2026-02-27 after scope revision — publish all 3 layers*
