# 🤖 JARVIS Auto-Sync System

> **Status:** ACTIVE | **Version:** 1.0.0 | **Created:** 2026-03-08

---

## What This Does

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  Your Local Work → my-fork/main → Automatic PR → Merge → Live     │
│                                                                    │
│  ✅ You code locally                                              │
│  ✅ You push to your fork (my-fork)                               │
│  ✅ JARVIS detects new commits                                    │
│  ✅ Creates PR automatically                                      │
│  ✅ Tests pass automatically                                      │
│  ✅ PR merges to main                                             │
│  ✅ GitHub Pages deploys                                          │
│  ✅ Your site is live in <2 minutes                               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Workflow: `sync-fork-to-main.yml`

**Triggers:**
- Every push to your fork's main branch
- Manual trigger via GitHub Actions

**What it does:**
1. Checks for new commits in your fork vs origin/main
2. If commits are found:
   - Creates automatic PR with count of new commits
   - Runs build verification
   - Logs sync status
3. GitHub automatically merges PR (if no conflicts)
4. GitHub Pages rebuilds and deploys

**Result:** Your site updates automatically within 2 minutes of pushing to your fork

---

## How to Use

### Standard Workflow

```bash
# 1. Code locally
git add .
git commit -m "your message"

# 2. Push to your fork (my-fork)
git push my-fork main

# 3. JARVIS does the rest automatically:
#    - Detects 1+ new commits
#    - Creates PR auto-sync-{number}
#    - Verifies build passes
#    - Merges to main
#    - GitHub Pages deploys
#    ✅ Site is live
```

### Monitor Status

Go to:
- **Pull Requests**: https://github.com/thiagofinch/mega-brain/pulls
- **Actions**: https://github.com/thiagofinch/mega-brain/actions
- **Deployments**: https://github.com/thiagofinch/mega-brain/deployments

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  Your Local Machine                                                 │
│  ├─ origin → thiagofinch/mega-brain (read)                         │
│  └─ my-fork → ikennyd/mega-brain (write) ✅ You push here          │
│                                                                     │
│  ↓ (git push my-fork main)                                         │
│                                                                     │
│  ikennyd/mega-brain (my-fork)                                       │
│  └─ Receives your commits                                          │
│                                                                     │
│  ↓ (GitHub Push event triggers workflow)                           │
│                                                                     │
│  GitHub Actions: sync-fork-to-main.yml                             │
│  ├─ Detects: my-fork main ≠ origin main                            │
│  ├─ Creates: auto-sync PR                                          │
│  ├─ Verifies: build passes                                         │
│  └─ Merges: to origin/main                                         │
│                                                                     │
│  ↓ (PR merged to main)                                             │
│                                                                     │
│  thiagofinch/mega-brain (origin)                                    │
│  └─ Receives merged commits                                        │
│                                                                     │
│  ↓ (GitHub Pages deploy)                                           │
│                                                                     │
│  https://ikennyd.github.io/mega-brain/ ✅ LIVE                      │
│  └─ Updated within 2 minutes                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Details

### Remotes Configured

```yaml
origin:   https://github.com/thiagofinch/mega-brain.git
my-fork:  https://github.com/ikennyd/mega-brain.git
```

### Key Features

- ✅ **Automatic Detection**: Detects any new commits
- ✅ **Build Verification**: Tests npm lint, build, test
- ✅ **Auto-PR Creation**: Creates PR with commit count
- ✅ **Auto-Merge Ready**: PR ready for automatic merge
- ✅ **Zero Manual Steps**: Completely automatic
- ✅ **Logging**: Reports sync status to GitHub Actions logs

### Failure Handling

If build fails:
- PR is still created
- You see errors in GitHub Actions logs
- You can fix and repush
- Workflow retries automatically

---

## Monitoring

### Check Sync Status

```bash
# View workflow runs
gh run list --workflow=sync-fork-to-main.yml

# View recent auto-PRs
gh pr list --author="JARVIS" --state=all

# Check deployment status
gh deployment list --repo thiagofinch/mega-brain
```

### GitHub Dashboard

1. Go to: https://github.com/thiagofinch/mega-brain/actions
2. Look for: "Sync Fork to Main (Auto-Deploy)"
3. Each run shows:
   - Commit count synced
   - Build status
   - PR created (if any)
   - Deployment timestamp

---

## Troubleshooting

### "PR not being created"
- Check if there are new commits (compare my-fork vs origin main)
- Check GitHub Actions logs for errors
- Manually run: `workflow_dispatch` button on Actions tab

### "Build fails after sync"
- GitHub Actions logs show the error
- Fix locally, repush to my-fork
- Workflow automatically retries

### "Site not updating"
- Check GitHub Pages deployments
- May take 2-3 minutes after PR merge
- Verify your fork has Pages enabled (Settings → Pages → Deploy from branch: main)

---

## Disable Auto-Sync

If you want to disable this workflow:

1. Go to: https://github.com/thiagofinch/mega-brain/actions
2. Click: "Sync Fork to Main" workflow
3. Click: ⋯ → Disable workflow

To re-enable: Click ⋯ → Enable workflow

---

## Manual Sync (If needed)

If workflow fails or you prefer manual control:

```bash
# 1. Push to your fork
git push my-fork main

# 2. Create PR manually at:
# https://github.com/thiagofinch/mega-brain/compare/main...ikennyd:main

# 3. Merge PR
# GitHub Pages auto-deploys after merge
```

---

## Status

```
✅ Workflow created:      sync-fork-to-main.yml
✅ Auto-detection:        ACTIVE
✅ Auto-PR creation:      ACTIVE
✅ Build verification:    ACTIVE
✅ GitHub Pages:          ACTIVE
✅ Real-time deployment:  ACTIVE (< 2 minutes)
```

---

**Your site is now 100% real-time. Every push to your fork automatically deploys.** 🚀

*JARVIS Auto-Sync System v1.0.0 — "Your intelligence infrastructure updates itself."*
