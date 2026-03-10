# Getting Started: DevOps Setup (Step-by-Step)

> **Estimated Time:** 15-20 minutes
> **Difficulty:** Intermediate
> **Last Updated:** 2026-03-06

---

## 📋 Pre-requisites

- [ ] Vercel account (free tier is fine)
- [ ] GitHub account with admin access to repo
- [ ] Node.js 20+ installed locally

---

## Step 1: Create Vercel Project (5 minutes)

### 1.1 Connect Repository

```bash
# Visit this link:
https://vercel.com/new

# Select:
- GitHub account (select "thiago-finch")
- Repository: "mega-brain"
```

### 1.2 Configure Project

```
Framework: Next.js
Project name: mega-brain
Root directory: frontend/ (or let it auto-detect)
Build Command: npm run build
Output Directory: .next
Install Command: npm ci
```

### 1.3 Add Environment Variables

In Vercel Dashboard → Project Settings → Environment Variables, add:

**Development:**
```
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:8080
```

**Preview & Production:**
```
NEXT_PUBLIC_API_URL=https://api.example.com  (update with real URL)
NEXT_PUBLIC_WS_URL=wss://api.example.com      (update with real URL)
MERCADOLIVRE_API_KEY=your_key_here
MERCADOLIVRE_API_SECRET=your_secret_here
DATABASE_URL=postgresql://user:pass@host:5432/mega_brain
```

### 1.4 Complete Setup

- Click "Deploy"
- Wait for initial deployment (2-3 minutes)
- Note the deployment URL
- ✅ You now have a production URL!

---

## Step 2: Get GitHub Secrets (5 minutes)

### 2.1 Get Vercel Credentials

**In Vercel Dashboard:**

1. Go to Settings → Tokens
2. Create new token (name: `GITHUB_DEPLOY`)
3. Copy token → Save to password manager
4. Go to Project Settings → General
5. Copy Project ID
6. Go to Account Settings → General
7. Copy Team ID (Organization ID)

### 2.2 Add GitHub Secrets

**In GitHub:**

1. Go to Repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"

Add these secrets:

| Name | Value | Source |
|------|-------|--------|
| `VERCEL_TOKEN` | Your token | Vercel Settings → Tokens |
| `VERCEL_ORG_ID` | Team ID | Vercel Account Settings |
| `VERCEL_PROJECT_ID` | Project ID | Vercel Project Settings |

**Optional (for Slack notifications):**

| Name | Value | Source |
|------|-------|--------|
| `SLACK_WEBHOOK_URL` | Your webhook | Slack Incoming Webhook |
| `PRODUCTION_URL` | https://mega-brain.vercel.app | Vercel project URL |

### 2.3 Verify Secrets

```bash
# All secrets should appear with a checkmark
GitHub Repo → Settings → Secrets and variables → Actions

Should see:
✅ VERCEL_TOKEN
✅ VERCEL_ORG_ID
✅ VERCEL_PROJECT_ID
✅ SLACK_WEBHOOK_URL (if added)
```

---

## Step 3: Configure Branch Protection (3 minutes)

### 3.1 Add Branch Protection Rule

**In GitHub:**

1. Go to Repo → Settings → Branches
2. Click "Add rule" under "Branch protection rules"
3. Enter branch name: `main`

### 3.2 Configure Rule

Enable these checkboxes:

```
✅ Require a pull request before merging
   └─ Require approvals: 1

✅ Require status checks to pass before merging
   └─ Require branches to be up to date before merging
   └─ Add status checks:
      ├─ ESLint
      ├─ TypeScript Type Check
      ├─ Build Verification
      └─ Unit Tests (if exists)

✅ Require code owner reviews (optional)

✅ Allow auto-merge
   └─ Squash (recommended)

✅ Require administrators to follow these rules
```

### 3.3 Save Rule

Click "Create" button

✅ Now main branch is protected!

---

## Step 4: Test the Pipeline (5 minutes)

### 4.1 Create Test Branch

```bash
cd /path/to/mega-brain

# Create test branch
git checkout -b test/ci-setup

# Make a small change
echo "# Test CI" >> README.md

# Commit
git add -A
git commit -m "test: verify CI pipeline"

# Push
git push origin test/ci-setup
```

### 4.2 Create Pull Request

**In GitHub:**

1. Go to Pull requests tab
2. Click "New pull request"
3. Select `test/ci-setup` branch
4. Click "Create pull request"

### 4.3 Watch Status Checks

**In PR page, scroll down to "Checks" section:**

You should see workflows running:

```
🟡 lint-and-test →
   ├─ ESLint: 🟡 (running)
   ├─ TypeScript: 🟡 (running)
   ├─ Build: 🟡 (running)
   └─ Tests: 🟡 (running)

🟡 deploy-preview →
   ├─ Building... → 🟡
```

**Wait 3-5 minutes for all checks:**

```
✅ lint-and-test
✅ deploy-preview
✅ All checks passed!
```

### 4.4 View Preview

Once `deploy-preview` passes:

```
In PR → Look for comment from "vercel" bot:

"✅ Preview Deployed
🔗 [View Preview](https://mega-brain-pr-123.vercel.app)"

Click link to see your preview deployment!
```

### 4.5 Merge Test PR

Once all checks pass:

1. Click "Approve" (if needed)
2. Click "Squash and merge"
3. Watch production deployment trigger!

### 4.6 Verify Production Deployment

**In Vercel Dashboard:**

1. Go to Deployments
2. Should see new "Production" deployment
3. Check production URL
4. Should see your test change!

✅ **CI/CD Pipeline is working!**

---

## Step 5: Verify Health Check (2 minutes)

### 5.1 Test Health Endpoint

**Local:**
```bash
curl http://localhost:3000/api/health
```

**Production:**
```bash
curl https://mega-brain.vercel.app/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T10:00:00Z",
  "uptime": 123.45,
  "environment": "production",
  "version": "abc123de",
  "checks": {
    "api": {
      "status": "ok",
      "responseTime": 45
    }
  }
}
```

✅ Health check working!

---

## Step 6: Optional - Slack Integration (5 minutes)

### 6.1 Create Slack Webhook

**In Slack Workspace:**

1. Go to api.slack.com/apps
2. Click "Create New App"
3. Select "From scratch"
4. App name: `mega-brain-deployments`
5. Workspace: select your workspace
6. Click "Create App"

### 6.2 Enable Incoming Webhooks

1. Left sidebar → "Incoming Webhooks"
2. Toggle "On"
3. Click "Add New Webhook to Workspace"
4. Select channel: `#deployments` (or create it)
5. Click "Allow"

### 6.3 Copy Webhook URL

1. Under "Webhook URLs for Your Workspace"
2. Copy the URL (starts with `https://hooks.slack.com/...`)

### 6.4 Add to GitHub Secrets

```bash
# In GitHub Secrets (as done in Step 2):
Add: SLACK_WEBHOOK_URL = your_webhook_url
```

### 6.5 Test Notification

**Deploy something:**

```bash
git checkout main
echo "# Update" >> README.md
git add -A
git commit -m "test: slack notification"
git push origin main
```

**Wait for deployment, then check Slack:**

```
In #deployments channel you should see:

✅ Production Deployment Successful
   Commit: abc123def
   Branch: main
   Deployed by: your-username
```

✅ Slack integration working!

---

## Step 7: Clean Up (1 minute)

### 7.1 Delete Test Branch

```bash
# Locally
git branch -D test/ci-setup

# On GitHub (usually auto-deleted after merge, but just in case)
git push origin --delete test/ci-setup
```

---

## Verification Checklist

```
After completing all steps, verify:

Infrastructure:
[ ] Vercel project created and deployed
[ ] Environment variables configured
[ ] Health check endpoint responding (GET /api/health)
[ ] Metrics endpoint working (POST /api/metrics)

CI/CD Pipeline:
[ ] GitHub Actions workflows visible
[ ] Lint workflow passes
[ ] Build verification passes
[ ] Preview deployment auto-triggers on PR
[ ] Production deployment auto-triggers on main merge

Security:
[ ] Branch protection enabled on main
[ ] Status checks required for merge
[ ] GitHub Secrets configured (not visible)
[ ] Vercel env vars configured (hidden)

Monitoring:
[ ] Health check endpoint responds
[ ] Lighthouse audit runs on PRs
[ ] Performance targets configured

Optional:
[ ] Slack notifications arriving
[ ] Error monitoring setup (if using Sentry)
```

---

## Troubleshooting

### Problem: "No build output found" in Vercel

**Solution:**
1. Check build command: `npm run build`
2. Check output directory: `.next`
3. Ensure package.json has `next` dependency
4. Try: `vercel env pull` to sync env vars

### Problem: GitHub Secrets not working

**Solution:**
1. Verify secret names are exact (case-sensitive!)
2. Try: Delete and recreate secret
3. Check: Secret is "Repository Secret" not "Organization Secret"

### Problem: Preview not deploying

**Solution:**
1. Check GitHub Actions tab for errors
2. Look for workflow failures
3. Verify: All status checks passing
4. Try: Push a new commit to trigger redeploy

### Problem: Health check returning 503

**Solution:**
1. Check: `NEXT_PUBLIC_API_URL` is set correctly
2. Try: `curl $NEXT_PUBLIC_API_URL/health`
3. If API down: Check backend service
4. Local test: `curl http://localhost:3000/api/health`

### Problem: Lighthouse failing

**Solution:**
1. Run locally: `npm run build && npm start`
2. Check build size: Look at webpack warnings
3. Optimize images: Reduce size of images
4. Check Core Web Vitals: Use Chrome DevTools

---

## Next Steps

Once verified, you're ready for:

1. **Frontend Development**
   - Developer creates feature branch
   - Creates PR → Preview auto-deploys
   - Requests review → Team reviews preview
   - Merges → Production auto-deploys

2. **Monitoring & Alerting**
   - Set up Datadog or New Relic
   - Configure error tracking (Sentry)
   - Set up performance alerts
   - Configure uptime monitoring

3. **Performance Optimization**
   - Run Lighthouse audit
   - Record baseline metrics
   - Identify bottlenecks
   - Implement optimizations

4. **Scale & Maintain**
   - Monitor deployment frequency
   - Track error rates
   - Review performance metrics
   - Update dependencies regularly

---

## Useful Commands

```bash
# Local development
npm run dev              # Start dev server (localhost:3000)
npm run build            # Build for production
npm run start            # Run production build locally
npm run lint             # Run ESLint
npm test                 # Run tests

# Vercel CLI
npm install -g vercel    # Install globally
vercel                   # Deploy (interactive)
vercel --prod            # Deploy to production
vercel env pull          # Pull env vars
vercel rollback          # Rollback last deployment

# Git/GitHub
git checkout -b feature/my-feature      # Create feature branch
git add .
git commit -m "feat: description"
git push origin feature/my-feature
gh pr create --web                      # Create PR in browser
```

---

## Quick Reference

| Step | Time | Task |
|------|------|------|
| 1 | 5 min | Create Vercel project |
| 2 | 5 min | Get GitHub secrets |
| 3 | 3 min | Configure branch protection |
| 4 | 5 min | Test CI/CD pipeline |
| 5 | 2 min | Verify health check |
| 6 | 5 min | Optional: Slack integration |
| 7 | 1 min | Clean up |
| **Total** | **~26 min** | **Infrastructure Ready** |

---

## Support

- **Questions?** Check INFRASTRUCTURE-SETUP.md
- **Issues?** See Troubleshooting section above
- **Help needed?** Contact @devops on Slack

---

**You're all set! Happy deploying! 🚀**

*Generated: 2026-03-06*
