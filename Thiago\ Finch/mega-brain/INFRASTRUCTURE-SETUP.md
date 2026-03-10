# Infrastructure Setup: Vercel + GitHub Actions + Monitoring

> **Status:** ✅ Complete
> **Last Updated:** 2026-03-06
> **Maintainer:** @devops

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Vercel Configuration](#vercel-configuration)
3. [GitHub Actions](#github-actions)
4. [Environment Variables](#environment-variables)
5. [Monitoring & Logging](#monitoring--logging)
6. [Performance Targets](#performance-targets)
7. [Security](#security)
8. [Deployment Process](#deployment-process)
9. [Troubleshooting](#troubleshooting)
10. [Monitoring Dashboard](#monitoring-dashboard)

---

## Overview

This document covers the complete infrastructure setup for the Mega Brain frontend, including:

- **Vercel** for edge deployment and serverless functions
- **GitHub Actions** for CI/CD automation
- **Performance monitoring** via Lighthouse, Web Vitals, and custom metrics
- **Security** with CSP headers, HTTPS enforcement, and dependency scanning
- **Error tracking** for frontend errors and exceptions

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                          GitHub Repository                                  │
│                          (main/develop)                                      │
│                                  │                                           │
│                    ┌─────────────┼─────────────┐                            │
│                    │             │             │                            │
│                    ▼             ▼             ▼                            │
│            Lint/Type Check  Build Test   Security Check                    │
│            (GitHub Actions)  (GitHub A)   (GitHub Actions)                 │
│                    │             │             │                            │
│                    └─────────────┼─────────────┘                            │
│                                  │                                           │
│                    ┌─────────────┴─────────────┐                            │
│                    │                           │                            │
│                    ▼                           ▼                            │
│            Pull Request Preview        Production Deploy                   │
│            (Vercel Preview)            (Vercel Production)                 │
│                                                                             │
│                    ┌───────────────────────────────────────┐                │
│                    │                                       │                │
│                    ▼                                       ▼                │
│            Web Vitals Collection              Health Checks                │
│            (Client-side Monitoring)           (API Verification)            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Vercel Configuration

### Setup Steps

1. **Connect GitHub Repository**
   - Visit [vercel.com/new](https://vercel.com/new)
   - Select GitHub account and repository
   - Select framework: **Next.js**
   - Project name: `mega-brain`

2. **Configure Build Settings**
   ```
   Framework: Next.js
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm ci
   ```

3. **Add Environment Variables**

   In Vercel Dashboard → Settings → Environment Variables, add:

   ```
   NEXT_PUBLIC_API_URL=https://api.example.com
   NEXT_PUBLIC_WS_URL=wss://api.example.com
   NEXT_PUBLIC_BUILD_ID={automatic}
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   MERCADOLIVRE_API_KEY=...
   MERCADOLIVRE_API_SECRET=...
   ```

4. **Deployment Settings**
   - **Preview Deployments:** Enabled for all branches
   - **Production Branch:** `main`
   - **Automatic deployments:** On push
   - **Rollback:** Enabled

### vercel.json Configuration

Location: `/vercel.json`

```json
{
  "name": "mega-brain",
  "version": 2,
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": { "description": "API Base URL" },
    "DATABASE_URL": { "description": "PostgreSQL connection" }
  },
  "regions": ["sfo1"],
  "ignoreCommand": "git diff --quiet HEAD^ HEAD -- frontend || exit 0"
}
```

---

## GitHub Actions

### Workflows Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **lint-and-test.yml** | Push/PR | ESLint, type-check, build, tests |
| **deploy-preview.yml** | PR on main/develop | Auto-deploy preview to Vercel |
| **deploy-production.yml** | Push to main | Auto-deploy to production |
| **security-checks.yml** | Push/PR/Schedule | Dependency audit, CodeQL, secrets scan |

### 1. Lint & Test Workflow

**File:** `.github/workflows/lint-and-test.yml`

**Stages:**
1. **ESLint** - Code style and quality
2. **TypeScript** - Type checking
3. **Build** - Build verification
4. **Tests** - Unit tests (jest/vitest)
5. **Lighthouse** - Performance audit (PRs only)

**Status Checks Required:** ✅ All must pass before merge

### 2. Deploy Preview Workflow

**File:** `.github/workflows/deploy-preview.yml`

**Trigger:** PR creation/update

**Process:**
1. Check out code
2. Deploy to Vercel preview
3. Comment PR with preview URL
4. Update commit status

**Preview URL Format:** `https://mega-brain-pr-123.vercel.app`

### 3. Deploy Production Workflow

**File:** `.github/workflows/deploy-production.yml`

**Trigger:** Push to main branch

**Process:**
1. Pre-deployment checks (lint, type-check, build)
2. Deploy to Vercel production
3. Run smoke tests (health check)
4. Notify Slack

**Rollback:** Via Vercel dashboard (1-click)

### 4. Security Checks Workflow

**File:** `.github/workflows/security-checks.yml`

**Runs:**
- On every push/PR
- Weekly schedule (Mondays at midnight)

**Checks:**
- `npm audit` - Dependency vulnerabilities
- **CodeQL** - Static code analysis
- **TruffleHog** - Secret detection
- **Dependabot** - Dependency updates (auto-PR)

---

## Environment Variables

### Local Development

**File:** `frontend/.env.local` (gitignored)

```bash
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:8080
DATABASE_URL=postgresql://user:pass@localhost:5432/mega_brain
REDIS_URL=redis://localhost:6379
MERCADOLIVRE_API_KEY=your_key
MERCADOLIVRE_API_SECRET=your_secret
NEXT_PUBLIC_ML_CLIENT_ID=your_client_id
NEXT_PUBLIC_LOG_LEVEL=debug
```

### Production (Vercel)

Set in Vercel Dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_WS_URL=wss://api.example.com
DATABASE_URL=postgresql://user:pass@prod.database.host/mega_brain
REDIS_URL=redis://prod.redis.host:6379
MERCADOLIVRE_API_KEY=prod_key
MERCADOLIVRE_API_SECRET=prod_secret
NEXT_PUBLIC_ML_CLIENT_ID=prod_client_id
```

### Required Variables Reference

| Variable | Development | Production | Required |
|----------|-------------|-----------|----------|
| `NODE_ENV` | development | production | ✅ |
| `NEXT_PUBLIC_API_URL` | http://localhost:3001 | https://api.example.com | ✅ |
| `NEXT_PUBLIC_WS_URL` | ws://localhost:8080 | wss://api.example.com | ✅ |
| `DATABASE_URL` | local postgres | managed postgres | ✅ |
| `REDIS_URL` | local redis | managed redis | ⚠️ Optional |
| `MERCADOLIVRE_API_KEY` | dev key | prod key | ✅ |
| `MERCADOLIVRE_API_SECRET` | dev secret | prod secret | ✅ |

---

## Monitoring & Logging

### 1. Frontend Monitoring (Web Vitals)

**File:** `frontend/lib/monitoring.ts`

Tracks:
- **Largest Contentful Paint (LCP)** - Paint timing
- **Cumulative Layout Shift (CLS)** - Visual stability
- **First Input Delay (FID)** - Interactivity
- **Page Load Time** - Overall performance
- **Time to First Byte (TTFB)** - Server response
- **Resource Metrics** - Asset loading times

**Integration:**

```typescript
import { monitoring } from '@/lib/monitoring';

// Metrics automatically collected on page load
// Errors automatically captured
// Sent to `/api/metrics` endpoint
```

### 2. Health Check Endpoint

**File:** `frontend/pages/api/health.ts`

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T10:00:00Z",
  "uptime": 3600,
  "environment": "production",
  "version": "abc123de",
  "checks": {
    "api": { "status": "ok", "responseTime": 45 },
    "database": { "status": "ok" },
    "cache": { "status": "ok" }
  }
}
```

**Used by:**
- Vercel health checks
- Uptime monitoring services
- Kubernetes liveness probes

### 3. Metrics Collection Endpoint

**File:** `frontend/pages/api/metrics.ts`

**Endpoint:** `POST /api/metrics`

**Payload:**
```json
{
  "metrics": [
    {
      "name": "Page Load Time",
      "value": 1250,
      "type": "navigation",
      "timestamp": 1741350000000
    }
  ],
  "sessionId": "unique-session-id",
  "url": "https://app.example.com/dashboard",
  "userAgent": "Mozilla/5.0..."
}
```

**Features:**
- Automatic batching (sends when 10+ metrics collected or 30s timeout)
- Uses `sendBeacon()` for reliability
- Survives page navigation/unload
- Categorizes metrics by type
- Generates alerts for performance issues

---

## Performance Targets

### Web Vitals Thresholds

| Metric | Target | Alert Level |
|--------|--------|------------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Warning @ >3s, Critical @ >4s |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Warning @ >0.15 |
| **FID** (First Input Delay) | < 100ms | Warning @ >200ms |
| **TTFB** (Time to First Byte) | < 600ms | Warning @ >1000ms |
| **Page Load Time** | < 2.5s | Warning @ >3s |

### Lighthouse Scores

| Category | Target |
|----------|--------|
| Performance | 90+ |
| Accessibility | 90+ |
| Best Practices | 90+ |
| SEO | 90+ |

### Resource Metrics

| Metric | Target |
|--------|--------|
| Total Bundle Size | < 500KB (gzipped) |
| First Byte Time | < 600ms |
| Largest Image | < 500KB |
| Number of Requests | < 100 |

---

## Security

### Security Headers (next.config.js)

```javascript
{
  key: 'X-Content-Type-Options',
  value: 'nosniff'
},
{
  key: 'X-Frame-Options',
  value: 'DENY'
},
{
  key: 'X-XSS-Protection',
  value: '1; mode=block'
},
{
  key: 'Strict-Transport-Security',
  value: 'max-age=31536000; includeSubDomains; preload'
},
{
  key: 'Content-Security-Policy',
  value: "default-src 'self'; script-src 'self' 'unsafe-inline'"
}
```

### Vercel Security Features

- ✅ HTTPS only (automatic)
- ✅ DDoS protection
- ✅ WAF (Web Application Firewall)
- ✅ Automatic backups
- ✅ Encryption at rest & in transit

### GitHub Branch Protection

**Settings → Branches → Add Rule (main)**

```
✅ Require pull request reviews (1 approver minimum)
✅ Require status checks to pass:
   - Lint & Tests
   - Build Verification
   - Type Check
   - Lighthouse (if applicable)
✅ Require branches to be up to date
✅ Dismiss stale PR approvals
✅ Require code owner reviews
✅ Allow auto-merge (Squash required)
✅ Include administrators
```

### Secrets Management

**Do NOT commit:**
- API keys
- Database passwords
- Tokens
- SSL certificates

**Store in:**
- Vercel Dashboard (Environment Variables)
- GitHub Secrets (for workflows)
- 1Password/LastPass (team credentials)

---

## Deployment Process

### Manual Deployment

1. **Deploy to Preview**
   ```bash
   # Create PR from your branch
   git push origin feature/my-feature
   # GitHub Actions automatically deploys preview
   ```

2. **Deploy to Production**
   ```bash
   # Merge PR to main
   git checkout main
   git merge feature/my-feature
   git push origin main
   # GitHub Actions automatically deploys to production
   ```

3. **Rollback**
   - Visit Vercel Dashboard → Deployments
   - Find previous deployment
   - Click "Promote to Production"
   - Takes ~30 seconds

### Automated Deployment Flow

```
Commit → GitHub Actions Checks → Status Checks Pass →
  → Merge to main → Production Deploy → Health Check →
    → Smoke Test → Slack Notification → Live
```

**Expected Deployment Time:** 3-5 minutes

### Pre-deployment Checklist

```
[ ] All feature branches merged to develop first
[ ] Code review approved (1+ reviewers)
[ ] All status checks passing
[ ] Lighthouse score acceptable (90+)
[ ] No security warnings
[ ] Environment variables configured
[ ] Database migrations ran (if applicable)
```

---

## Performance Optimization

### Code Splitting

Configured in `next.config.js`:

```javascript
splitChunks: {
  chunks: 'all',
  cacheGroups: {
    vendor: {
      test: /node_modules/,
      filename: 'chunks/vendor-[hash].js',
    },
    react: {
      test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
      filename: 'chunks/react-[hash].js',
    }
  }
}
```

### Image Optimization

```javascript
images: {
  formats: ['image/avif', 'image/webp'],
  remotePatterns: [
    { protocol: 'https', hostname: '*.mercadolibre.com' }
  ]
}
```

### Bundle Analysis

```bash
# Analyze bundle size
npm install --save-dev @next/bundle-analyzer

# In next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

# Run
ANALYZE=true npm run build
```

---

## Monitoring Dashboard

### Vercel Dashboard

- **URL:** [vercel.com/dashboard](https://vercel.com/dashboard)
- **Metrics:** Deployment history, performance, logs
- **Alerts:** Can configure via integrations

### GitHub Actions

- **URL:** GitHub Repo → Actions tab
- **View:** Workflow runs, logs, test results

### Custom Monitoring (To Implement)

Recommended integrations:

1. **Datadog** (Enterprise)
   - Real-time performance monitoring
   - Alert management
   - Log aggregation

2. **New Relic** (Mid-market)
   - Application performance monitoring
   - Error tracking
   - Infrastructure visibility

3. **Sentry** (Free/Paid)
   - Error tracking (frontend + backend)
   - Performance monitoring
   - Release tracking

4. **CloudWatch** (AWS)
   - Logs aggregation
   - Metrics dashboard
   - Alert rules

### Slack Integration

**Configured in deploy-production.yml:**

```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1.24.0
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

**Setup:**
1. Go to Slack Workspace → Apps & Integrations
2. Search "Incoming Webhooks"
3. Create webhook for #deployments channel
4. Add to GitHub Secrets as `SLACK_WEBHOOK_URL`

**Notifications:**
- ✅ Deployment successful
- ❌ Deployment failed
- ⚠️ Build warnings
- 🚨 Health check failures

---

## Troubleshooting

### Build Fails: "npm ERR! code ENOENT"

**Cause:** `package-lock.json` out of sync

**Fix:**
```bash
cd frontend
rm package-lock.json
npm install
git add package-lock.json
git commit -m "chore: update package-lock.json"
```

### Deployment Timeout

**Cause:** Build takes >15 minutes

**Solutions:**
1. Check for large unoptimized images
2. Review webpack config
3. Split code further
4. Increase Vercel timeout in vercel.json

### Preview URL Not Accessible

**Cause:** Vercel deployment failed

**Check:**
1. GitHub Actions status (lint, type-check)
2. Vercel deployment logs
3. Environment variables configured

### Performance Score Low (< 80)

**Debug:**
1. Run Lighthouse locally: `npm run build && npm start`
2. Check Chrome DevTools Performance tab
3. Identify slow resources
4. Optimize images, minify bundles, defer scripts

### Health Check Failing

**Debug:**
```bash
# Local test
curl http://localhost:3000/api/health

# Production test
curl https://mega-brain.vercel.app/api/health

# Check API connectivity
curl $NEXT_PUBLIC_API_URL/health
```

---

## Runbooks

### Incident: Frontend Down

```
1. Check Vercel Status Page (status.vercel.com)
2. Check GitHub Actions last deployment
3. Visit /api/health endpoint
4. Check Slack #deployments for errors
5. If recent deploy: rollback via Vercel dashboard
6. If not recent: check infrastructure (API, database)
7. Post incident to #incidents channel
```

### Incident: Performance Degraded

```
1. Check Vercel Analytics for changes
2. Review recent deployments
3. Check Core Web Vitals metrics
4. Identify bottleneck (API, assets, code)
5. If API: check backend status
6. If assets: check CDN status
7. If code: identify commit causing regression
8. Rollback or hotfix
```

### Incident: Errors Spiking

```
1. Check frontend error logs
2. Identify error type and affected pages
3. Check error patterns (browser, OS, geography)
4. Review recent changes
5. Check API connectivity
6. If widespread: consider rollback
7. If isolated: apply hotfix
8. Monitor error rate after fix
```

---

## Maintenance

### Weekly

- [ ] Check dependency updates in GitHub
- [ ] Review Vercel analytics for performance
- [ ] Check security alerts

### Monthly

- [ ] Run full security audit (`npm audit`)
- [ ] Update Lighthouse report
- [ ] Review and optimize slow pages
- [ ] Check coverage reports

### Quarterly

- [ ] Full infrastructure review
- [ ] Update Node.js/Next.js versions
- [ ] Audit CDN configuration
- [ ] Review and update security headers

---

## Contacts & Escalation

| Issue | Contact | Escalation |
|-------|---------|-----------|
| Frontend Build Failure | @devops | @tech-lead |
| Deployment Issues | @devops | @devops-team |
| Performance Regression | @devops | @backend-team (if API issue) |
| Security Alert | @devops | @security-team |
| Infrastructure Down | @devops | @infrastructure-team |

---

## Quick Reference

### Useful Commands

```bash
# Local development
npm run dev                    # Start dev server
npm run build                  # Production build
npm run start                  # Run production build
npm run lint                   # Run ESLint
npm test                       # Run tests
npm run lighthouse             # Run Lighthouse audit

# Vercel CLI
vercel                         # Deploy (interactive)
vercel --prod                  # Deploy to production
vercel rollback                # Rollback last deployment
vercel env pull                # Pull env vars from Vercel

# GitHub
gh workflow view               # View workflows
gh run list                    # List recent runs
gh pr create                   # Create pull request
```

### Important URLs

| Service | URL |
|---------|-----|
| Vercel Dashboard | https://vercel.com/dashboard |
| GitHub Repo | https://github.com/thiago-finch/mega-brain |
| GitHub Actions | https://github.com/thiago-finch/mega-brain/actions |
| Production App | https://mega-brain.vercel.app |
| Health Check | https://mega-brain.vercel.app/api/health |
| Slack Channel | #deployments |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-06 | @devops | Initial setup: Vercel + GitHub Actions + Monitoring |

---

*Last updated: 2026-03-06 by @devops*
*For updates or questions, contact the DevOps team.*
