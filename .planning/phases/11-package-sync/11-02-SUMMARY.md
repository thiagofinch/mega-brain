---
phase: 11-package-sync
plan: 02
subsystem: packaging
tags: [npm, npmignore, allowlist, audit, defense-in-depth]

requires:
  - phase: 11-package-sync
    provides: "sync_package_files.py with --npmignore and --allowlist modes"
provides:
  - "Auto-generated .npmignore aligned with audit L2/L3/NEVER patterns"
  - "layer1-allowlist.txt mirroring package.json files field (143 entries)"
  - "All three packaging artifacts regenerable from one script"
affects: [12-validation-docs]

tech-stack:
  added: []
  patterns: ["defense-in-depth: files whitelist + npmignore exclusion"]

key-files:
  created: []
  modified:
    - ".npmignore"
    - ".github/layer1-allowlist.txt"
    - ".github/layer2-manifest.txt"

key-decisions:
  - ".npmignore reduced from 232 to 139 lines (auto-generated, not hand-curated)"
  - "layer1-allowlist.txt entries match package.json files exactly (143 entries)"

patterns-established:
  - "Single regeneration command for all packaging artifacts: sync_package_files.py"
  - "Defense-in-depth: npm pack output unchanged after .npmignore update (files field is primary)"

requirements-completed: [SYNC-02]

duration: 5min
completed: 2026-02-27
---

# Phase 11 Plan 02: .npmignore + Allowlist Sync Summary

**Auto-generated .npmignore from audit patterns and synced layer1-allowlist.txt with 143-entry files field**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-27T20:30:00Z
- **Completed:** 2026-02-27T20:35:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Regenerated .npmignore from audit L2/L3/NEVER patterns (232 -> 139 lines)
- Synced layer1-allowlist.txt with package.json files field (143 entries exact match)
- Updated layer2-manifest.txt header with audit review date
- Verified npm pack output unchanged at 619 files (defense-in-depth confirmed)
- All three artifacts regenerable: `--print`, `--npmignore`, `--allowlist`

## Task Commits

1. **Task 1: Regenerate .npmignore** - `be51a47f` (feat)
2. **Task 2: Sync layer1-allowlist.txt** - `03158b52` (feat)

## Files Created/Modified
- `.npmignore` - Auto-generated from audit layer patterns (139 lines)
- `.github/layer1-allowlist.txt` - Mirrors package.json files field (143 entries)
- `.github/layer2-manifest.txt` - Added audit review date to header

## Decisions Made
- Kept .npmignore as defense-in-depth even though files field is primary whitelist
- Included runtime state directories (agent-memory, aios) in npmignore but they're in files field as L1 scaffold

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All SYNC-01/02/03 requirements satisfied
- Phase 12 can now validate the synced packaging artifacts
- Pre-publish gate can reference sync script for automated checks

---
*Phase: 11-package-sync*
*Completed: 2026-02-27*
