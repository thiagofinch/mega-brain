# Story 1.5: Repo Consolidation

> **Story ID:** STORY-TD-1.5
> **Epic:** EPIC-TD-001
> **Sprint:** 1
> **Priority:** P0 (organizational debt, not code debt)
> **Source:** `docs/plans/surgical-merge-plan-2026-03-14.md`

---

## Context

Two directories named "mega-brain" exist on this machine, sharing the same 3 git remotes and the same origin:

- **Canonical:** `/Users/thiagofinch/Documents/Projects/mega-brain/` (v1.4.0, 120+ Python modules, 3-bucket architecture, 37 hooks, 101 skills)
- **Other:** `/Users/thiagofinch/Projects/mega-brain/` (v1.3.0, pre-S13 architecture, flat inbox)

The other repo's only unique value is 372 raw transcription files across 3 sources that were never copied over. Everything else in the other repo is a strict subset of ours. The dual-repo situation creates confusion about which repo is authoritative.

---

## Tasks

### Step 1: Verify .env Parity

- [ ] Compare key names (not values) between both repos' `.env` files
- [ ] If any key exists in the other repo's `.env` but not ours, add the key name + value to ours

```bash
diff <(grep -oP '^\w+=' /Users/thiagofinch/Projects/mega-brain/.env | sort) \
     <(grep -oP '^\w+=' /Users/thiagofinch/Documents/Projects/mega-brain/.env | sort)
```

### Step 2: Verify Git Remote Parity

- [ ] Confirm both repos point to the same 3 GitHub repositories (already verified in merge plan -- this is a sanity check)

### Step 3: Audit Inbox Delta

- [ ] Identify the 3 unique source collections that exist only in the other repo:
  - `full-sales-system` (~264 files, ~29MB)
  - `g4-educacao` (~105 files, ~148MB)
  - `grupo-silva` (~3 files, ~112KB)
- [ ] Confirm these do NOT exist in our `knowledge/external/sources/` or `knowledge/external/inbox/`

### Step 4: Copy Unique Inbox Files

- [ ] Copy `full-sales-system` to `knowledge/external/inbox/full-sales-system/`
- [ ] Copy `g4-educacao` to `knowledge/external/inbox/g4-educacao/`
- [ ] Copy `grupo-silva` to `knowledge/external/inbox/grupo-silva/`
- [ ] Normalize directory names to kebab-case
- [ ] Remove any `.DS_Store` files from copied directories

```bash
OUR_INBOX="/Users/thiagofinch/Documents/Projects/mega-brain/knowledge/external/inbox"
THEIR_INBOX="/Users/thiagofinch/Projects/mega-brain/inbox"

cp -R "$THEIR_INBOX/full sales system" "$OUR_INBOX/full-sales-system"
cp -R "$THEIR_INBOX/g4 educacao (gestao 4.0)" "$OUR_INBOX/g4-educacao"
cp -R "$THEIR_INBOX/grupo silva" "$OUR_INBOX/grupo-silva"

# Cleanup
find "$OUR_INBOX" -name '.DS_Store' -delete
```

### Step 5: Archive Other Repo

- [ ] Rename other repo to clearly mark as archived
- [ ] Remove git remotes from archived repo (prevents accidental pushes)

```bash
mv /Users/thiagofinch/Projects/mega-brain \
   /Users/thiagofinch/Projects/mega-brain-ARCHIVED-2026-03-14

cd /Users/thiagofinch/Projects/mega-brain-ARCHIVED-2026-03-14
git remote remove origin
git remote remove backup
git remote remove premium
```

### Step 6: Post-Merge Validation

- [ ] Our git remotes still work: `git fetch --all --dry-run`
- [ ] New inbox files exist: `ls knowledge/external/inbox/{full-sales-system,g4-educacao,grupo-silva}/`
- [ ] No `.DS_Store` in new dirs: `find knowledge/external/inbox/ -name '.DS_Store' | wc -l` returns 0
- [ ] Other repo is renamed and has no remotes
- [ ] Tests still pass: `python3 -m pytest tests/python/ -v`

---

## Acceptance Criteria

- [ ] 3 unique inbox source directories exist in `knowledge/external/inbox/`
- [ ] File counts match: full-sales-system (~264), g4-educacao (~105), grupo-silva (~3)
- [ ] Other repo is renamed to `mega-brain-ARCHIVED-2026-03-14`
- [ ] Archived repo has zero git remotes
- [ ] Our repo is fully functional (tests pass, hooks work)

---

## Technical Notes

**What we are NOT merging:** Everything else from the other repo is excluded:
- `_IMPORT/AIOS/` (43MB reference copy, patterns already extracted)
- `archive/` (363MB migration history logs)
- `.venv-rag/` (65MB, recreatable)
- ClickUp MCP config (deliberately removed, see `mcp-governance.md`)
- Session logs (56 logs referencing stale paths)

**ClickUp MCP:** Per the merge plan, the recommendation is DO NOT READOPT NOW. The removal was deliberate. If needed later, it can be re-added in 5 minutes.

**The new inbox files go into the pipeline queue for future processing via `/ingest`.** They do NOT need immediate processing as part of this story.

**Retention of archived repo:** Safe to delete after 90 days if no lookbacks were needed.

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Verify .env + git remotes | 0.1h |
| Audit inbox delta | 0.25h |
| Copy unique files | 0.15h |
| Archive other repo | 0.05h |
| Post-merge validation | 0.15h |
| **Total** | **~1h** |

---

## Dependencies

None. This story is completely independent and can run in parallel with any other Sprint 1 story.

---

## Definition of Done

- [ ] Single canonical repo exists at `/Users/thiagofinch/Documents/Projects/mega-brain/`
- [ ] Other repo archived with clear naming and no git remotes
- [ ] All unique raw content from other repo is in our `knowledge/external/inbox/`
- [ ] Our repo fully functional (tests, hooks, remotes all work)
- [ ] No confusion about which repo to use going forward
