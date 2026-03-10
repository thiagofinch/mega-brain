# PRODUCTION DEPLOYMENT CHECKLIST

> **Date:** 2026-03-06
> **Status:** READY TO EXECUTE
> **Duration:** 45-90 minutes
> **Architecture:** Vercel + Render + Supabase + DataDog

---

## ✅ PRE-DEPLOYMENT (15 minutes)

### Code Quality & Security

- [ ] **Remove hardcoded secrets**
  ```bash
  cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"
  git grep -i "sk-proj-\|postgresql://\|app_usr-" -- "*.js" "*.ts" "*.json" | grep -v ".env\|package-lock"
  # Expected: 0 results (only in .env file)
  ```

- [ ] **Run npm audit**
  ```bash
  npm audit --production
  # Fix critical vulnerabilities if any
  ```

- [ ] **Verify TypeScript compilation**
  ```bash
  cd frontend && npx tsc --noEmit
  # Expected: No errors
  ```

- [ ] **Check ESLint**
  ```bash
  npm run lint
  # Expected: 0 errors
  ```

- [ ] **Ensure clean git state**
  ```bash
  git status
  git log --oneline -1
  # Expected: "working tree clean"
  ```

### Network & DNS Planning

- [ ] **Document target URLs**
  ```
  Frontend:  [to be assigned by Vercel]
  Backend:   [to be assigned by Render]
  Database:  [Supabase connection string to be saved]
  Monitoring: [DataDog dashboard URL]
  ```

- [ ] **Verify GitHub access**
  ```bash
  git remote -v
  # Expected: Shows GitHub repo URL
  ```

---

## 🌐 PHASE 1: FRONTEND DEPLOYMENT (15 minutes)

### 1.1: Local Build Verification

- [ ] **Install dependencies**
  ```bash
  cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain/frontend"
  npm ci
  ```

- [ ] **Build frontend**
  ```bash
  npm run build
  ls -la .next
  du -sh .next
  ```
  **Expected:** `.next` folder exists, ~50-150MB

- [ ] **Verify build artifacts**
  ```bash
  ls .next/static/chunks/ | wc -l
  # Expected: Multiple chunk files created
  ```

### 1.2: Git Preparation

- [ ] **Push to GitHub**
  ```bash
  cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"
  git push origin main -u
  ```

- [ ] **Create release tag**
  ```bash
  git tag v1.0.0-prod
  git push origin v1.0.0-prod
  ```

- [ ] **Verify push**
  ```bash
  git remote show origin | grep "HEAD branch"
  # Expected: HEAD branch is main
  ```

### 1.3: Vercel Deployment

- [ ] **Create Vercel account** (https://vercel.com)
  - [ ] Sign up / Login
  - [ ] Authorize GitHub access
  - [ ] Accept permissions

- [ ] **Create new project**
  - [ ] Go to https://vercel.com/new
  - [ ] Select "Clone from GitHub"
  - [ ] Choose `mega-brain` repository
  - [ ] Set Root Directory: `frontend`
  - [ ] Build Command: `npm run build`
  - [ ] Output Directory: `.next`
  - [ ] Click "Deploy"

- [ ] **Record deployment information**
  ```
  Vercel Project URL: https://mega-brain-prod-[random].vercel.app
  Project Name: mega-brain-prod
  Status: _________________ (wait for completion)
  ```

- [ ] **Wait for build completion** (3-5 minutes)

- [ ] **Verify deployment succeeded**
  ```bash
  curl -I https://mega-brain-prod-[random].vercel.app
  # Expected: HTTP/1.1 200 OK or 301
  ```

---

## 🔗 PHASE 2: DATABASE SETUP (20 minutes)

### 2.1: Supabase Project Creation

- [ ] **Create Supabase account** (https://supabase.com)
  - [ ] Sign up
  - [ ] Create organization
  - [ ] Go to dashboard

- [ ] **Create new project**
  - [ ] Click "New Project"
  - [ ] Project Name: `mega-brain-prod`
  - [ ] Region: `us-east-1` (or your region)
  - [ ] Generate database password: `[SAVE SECURELY]`
  - [ ] Wait for provisioning (2-3 minutes)

- [ ] **Record connection details**
  ```
  Project ID: _______________________
  DB Password: ______________________ [SAVED IN PASSWORD MANAGER]
  Connection String: postgresql://postgres.[ID]:PASS@aws-0-us-east-1.pooler.supabase.com:6543/postgres
  ```

### 2.2: Database Schema Initialization

- [ ] **Create schema file** (`scripts/schema-init.sql`)
  - [ ] Copy full schema from PRODUCTION-DEPLOYMENT-STRATEGY.md
  - [ ] Save to `scripts/schema-init.sql`
  - [ ] Verify 3 tables (sales_live, sales_daily, sales_hourly)

- [ ] **Execute schema**
  ```bash
  SUPABASE_URL="postgresql://postgres.[ID]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
  psql "$SUPABASE_URL" < scripts/schema-init.sql

  # Verify
  psql "$SUPABASE_URL" -c "\dt public.*"
  # Expected: 3 tables listed
  ```

- [ ] **Verify indexes created**
  ```bash
  psql "$SUPABASE_URL" -c "SELECT indexname FROM pg_indexes WHERE schemaname='public';"
  # Expected: At least 5 indexes
  ```

- [ ] **Verify views created**
  ```bash
  psql "$SUPABASE_URL" -c "SELECT viewname FROM pg_views WHERE schemaname='public';"
  # Expected: At least 1 view (v_sales_today)
  ```

### 2.3: Connection Verification

- [ ] **Test connection**
  ```bash
  psql "$SUPABASE_URL" -c "SELECT NOW(), VERSION();"
  # Expected: Current timestamp and PostgreSQL version
  ```

- [ ] **Check table structure**
  ```bash
  psql "$SUPABASE_URL" -c "\d+ public.sales_live"
  # Expected: All columns visible
  ```

---

## 🖥️ PHASE 3: BACKEND DEPLOYMENT (15 minutes)

### 3.1: Render Account & Configuration

- [ ] **Create Render account** (https://render.com)
  - [ ] Sign up with GitHub
  - [ ] Authorize permissions
  - [ ] Go to dashboard

- [ ] **Create Web Service**
  - [ ] Click "New+" → "Web Service"
  - [ ] Select `mega-brain` repository
  - [ ] Branch: `main`
  - [ ] Service Name: `mega-brain-api`
  - [ ] Region: `Frankfurt` (best for Brazil)
  - [ ] Runtime: `Node`
  - [ ] Build Command: `npm ci`
  - [ ] Start Command: `node server.js`

- [ ] **Add Environment Variables**
  ```
  NODE_ENV = production
  DATABASE_URL = postgresql://postgres.[ID]:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
  CORS_ORIGINS = https://mega-brain-prod-[random].vercel.app
  OPENAI_API_KEY = sk-proj-[from .env]
  VOYAGE_API_KEY = pa--[from .env]
  MERCADOLIVRE_CLIENT_ID = [from .env]
  MERCADOLIVRE_CLIENT_SECRET = [from .env]
  MERCADOLIVRE_REDIRECT_URL = [from .env]
  MERCADOLIVRE_ACCESS_TOKEN = [from .env]
  ```

- [ ] **Click "Create Web Service"**

- [ ] **Record service information**
  ```
  Service URL: https://mega-brain-api-[random].onrender.com
  Service Name: mega-brain-api
  Status: _________________ (wait for build)
  ```

- [ ] **Wait for build completion** (3-5 minutes)

### 3.2: Backend Verification

- [ ] **Check health endpoint**
  ```bash
  BACKEND_URL="https://mega-brain-api-[random].onrender.com"

  curl -s "$BACKEND_URL/health" | jq .
  # Expected: {"status":"online","database":"connected",...}
  ```

- [ ] **Check API endpoints**
  ```bash
  curl -s "$BACKEND_URL/api/sales" | jq . | head -10
  # Expected: Sales data (may be empty initially)
  ```

- [ ] **Verify database connection**
  ```bash
  curl -s "$BACKEND_URL/health" | jq .database
  # Expected: "connected"
  ```

---

## 📊 PHASE 4: MONITORING SETUP (15 minutes)

### 4.1: DataDog Account & Setup

- [ ] **Create DataDog account** (https://www.datadoghq.com)
  - [ ] Sign up for free trial
  - [ ] Create organization
  - [ ] Create API key

- [ ] **Record DataDog credentials**
  ```
  Organization: _______________________
  API Key: _______________________
  Application ID: _______________________
  Client Token: _______________________
  Site: datadoghq.com
  ```

- [ ] **Save credentials to environment**
  ```bash
  # In ~/.zshrc or ~/.bash_profile
  export DD_API_KEY="your-api-key"
  export NEXT_PUBLIC_DD_APP_ID="your-app-id"
  export NEXT_PUBLIC_DD_CLIENT_TOKEN="your-client-token"
  ```

### 4.2: APM Agent Installation (Backend)

- [ ] **Install dd-trace**
  ```bash
  cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"
  npm install dd-trace --save
  ```

- [ ] **Update server.js** (add at top)
  ```javascript
  import tracer from 'dd-trace';

  if (process.env.NODE_ENV === 'production') {
    tracer.init({
      service: 'mega-brain-api',
      version: '1.0.0',
      env: 'production',
      logInjection: true
    });
  }

  import express from 'express';
  // ... rest of file
  ```

- [ ] **Commit changes**
  ```bash
  git add -A
  git commit -m "chore: add DataDog APM tracing"
  git push origin main
  ```

- [ ] **Redeploy to Render**
  - [ ] Go to Render Dashboard
  - [ ] Select `mega-brain-api`
  - [ ] Click "Redeploy latest commit"
  - [ ] Wait for completion

### 4.3: RUM Setup (Frontend)

- [ ] **Install @datadog/browser-rum**
  ```bash
  cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain/frontend"
  npm install @datadog/browser-rum --save
  ```

- [ ] **Create app/datadog.ts** (use code from PRODUCTION-DEPLOYMENT-STRATEGY.md)

- [ ] **Update app/layout.tsx** to initialize DataDog

- [ ] **Commit changes**
  ```bash
  git add -A
  git commit -m "chore: add DataDog RUM monitoring"
  git push origin main
  ```

- [ ] **Redeploy to Vercel**
  - [ ] Vercel auto-deploys on push
  - [ ] Wait for build completion

### 4.4: Configure Alerts

- [ ] **Create Monitor: High Error Rate**
  - [ ] DataDog → Monitors → New Monitor
  - [ ] Type: Metric Alert
  - [ ] Metric: `trace.web.request.errors`
  - [ ] Condition: `> 1%` over 5 minutes
  - [ ] Severity: Warning
  - [ ] Notification: Email or Slack

- [ ] **Create Monitor: High Latency**
  - [ ] Metric: `trace.web.request.duration.99p`
  - [ ] Condition: `> 500ms` over 5 minutes
  - [ ] Severity: Warning

- [ ] **Create Monitor: Database Connection Failed**
  - [ ] Type: Custom Monitor
  - [ ] Condition: Render service logs contain "connection failed"
  - [ ] Severity: Critical

- [ ] **Create Dashboard**
  - [ ] Name: "Mega Brain Production"
  - [ ] Add widgets for key metrics
  - [ ] Save and share

---

## ✅ PHASE 5: INTEGRATION TESTING (10 minutes)

### 5.1: Full Stack Connectivity

- [ ] **Frontend loads**
  ```bash
  FRONTEND_URL="https://mega-brain-prod-[random].vercel.app"
  curl -I $FRONTEND_URL | grep "200\|301"
  # Expected: HTTP 200 or 301
  ```

- [ ] **Backend responds**
  ```bash
  BACKEND_URL="https://mega-brain-api-[random].onrender.com"
  curl -s "$BACKEND_URL/health" | jq .status | grep -q "online"
  # Expected: "online"
  ```

- [ ] **Database accessible**
  ```bash
  curl -s "$BACKEND_URL/api/sales" | jq . > /dev/null
  # Expected: Returns valid JSON
  ```

- [ ] **CORS configured**
  ```bash
  curl -s -H "Origin: $FRONTEND_URL" "$BACKEND_URL/health" | jq . > /dev/null
  # Expected: Valid response (no CORS error)
  ```

### 5.2: API Functionality

- [ ] **Sales data endpoint**
  ```bash
  curl -s "$BACKEND_URL/api/sales" | jq '.length'
  # Expected: Number (may be 0 initially)
  ```

- [ ] **Daily aggregation**
  ```bash
  curl -s "$BACKEND_URL/api/daily" | jq '.length'
  # Expected: Number
  ```

- [ ] **Marketplace data**
  ```bash
  curl -s "$BACKEND_URL/api/marketplace" | jq '.'
  # Expected: Marketplace statistics
  ```

### 5.3: Frontend Functionality

- [ ] **Homepage loads**
  - [ ] Open $FRONTEND_URL in browser
  - [ ] Check for JavaScript errors (DevTools → Console)
  - [ ] Verify CSS styling applied

- [ ] **Dashboard displays**
  - [ ] Navigate to dashboard
  - [ ] Check for data visualization (charts load)
  - [ ] Verify real-time updates (if data available)

- [ ] **Responsive design**
  - [ ] Test on mobile (DevTools → Mobile)
  - [ ] Test on tablet
  - [ ] Test on desktop
  - [ ] Verify all elements visible

### 5.4: DataDog Integration

- [ ] **Verify APM data arriving**
  - [ ] DataDog Dashboard → APM → Services
  - [ ] Look for `mega-brain-api` service
  - [ ] Check request metrics

- [ ] **Verify RUM data arriving**
  - [ ] DataDog Dashboard → RUM → Sessions
  - [ ] Look for frontend events
  - [ ] Check user activity

- [ ] **Check custom metrics**
  - [ ] Generate some traffic to backend
  - [ ] Wait 2-3 minutes for data to arrive
  - [ ] Verify in DataDog dashboard

---

## 🔐 PHASE 6: SECURITY HARDENING (10 minutes)

### 6.1: HTTPS Verification

- [ ] **Check SSL certificate (Frontend)**
  ```bash
  openssl s_client -connect mega-brain-prod-[random].vercel.app:443 -showcerts | grep "Verify return code"
  # Expected: "Verify return code: 0 (ok)"
  ```

- [ ] **Check SSL certificate (Backend)**
  ```bash
  openssl s_client -connect mega-brain-api-[random].onrender.com:443 -showcerts | grep "Verify return code"
  # Expected: "Verify return code: 0 (ok)"
  ```

### 6.2: Security Headers

- [ ] **Check Vercel headers**
  ```bash
  curl -I https://mega-brain-prod-[random].vercel.app | grep -i "strict-transport-security\|x-frame\|x-content-type"
  # Expected: At least one security header present
  ```

- [ ] **Check Render headers**
  ```bash
  curl -I https://mega-brain-api-[random].onrender.com | grep -i "strict-transport-security"
  # Expected: HSTS header present
  ```

### 6.3: Environment Variable Verification

- [ ] **Verify secrets NOT in codebase**
  ```bash
  git log -p --all | grep -i "sk-proj-\|postgresql://\|Bearer " | wc -l
  # Expected: 0 (or only in commits before this one)
  ```

- [ ] **Verify .env gitignored**
  ```bash
  git check-ignore .env && echo "✓ .env is gitignored" || echo "✗ .env is NOT gitignored"
  # Expected: .env is gitignored
  ```

### 6.4: Database Backup

- [ ] **Enable Supabase backups**
  - [ ] Supabase Dashboard → Settings → Backups
  - [ ] Verify daily backups enabled
  - [ ] Note backup retention period

- [ ] **Test manual backup**
  ```bash
  pg_dump "$DATABASE_URL" > "backup-$(date +%Y-%m-%d-%H%M%S).sql"
  ls -lah backup-*.sql
  # Expected: Backup file created (size > 1MB if data exists)
  ```

---

## 📋 FINAL VALIDATION (5 minutes)

### Checklist Completion

- [ ] All 6 phases completed
- [ ] All API endpoints responding
- [ ] DataDog receiving metrics
- [ ] Alerts configured
- [ ] Backups enabled
- [ ] HTTPS working
- [ ] No critical errors in logs

### Documentation

- [ ] **Record all URLs**
  ```
  Frontend:     https://mega-brain-prod-[random].vercel.app
  Backend:      https://mega-brain-api-[random].onrender.com
  Database:     Supabase PostgreSQL (saved in password manager)
  Monitoring:   https://app.datadoghq.com
  ```

- [ ] **Save credentials securely**
  - [ ] Supabase connection string
  - [ ] DataDog API keys
  - [ ] Render API key
  - [ ] Vercel token (for CLI)

- [ ] **Create DEPLOYMENT-RECORD.md**
  ```markdown
  # Deployment Record

  **Date:** 2026-03-06
  **Status:** LIVE
  **Duration:** XX minutes

  ## Services
  - Frontend: [URL]
  - Backend: [URL]
  - Database: [Provider/Region]
  - Monitoring: [DataDog]

  ## Key Metrics
  - Build time: XX min
  - Deploy time: XX min
  - First errors: NONE ✓
  - Uptime: 100% ✓
  ```

### Handoff

- [ ] **Notify team**
  - [ ] Slack message with production URLs
  - [ ] Email with access instructions
  - [ ] Documentation link

- [ ] **Set up monitoring alerts**
  - [ ] Configure Slack integration in DataDog
  - [ ] Add email notifications
  - [ ] Set escalation policy

---

## 🚨 IMMEDIATE ACTIONS (First Hour)

### Monitor Closely

- [ ] Check DataDog dashboard every 10 minutes
- [ ] Monitor error rate (should be 0-1%)
- [ ] Monitor response time (P99 < 500ms)
- [ ] Check Vercel/Render logs for warnings
- [ ] Monitor database connections

### Be Ready to Rollback

```bash
# If critical issue found:

# 1. Pause traffic to new deployment
# (Usually automatic via DNS or load balancer)

# 2. Redeploy previous stable version
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"
git tag v1.0.0-prod-rollback
git push origin v1.0.0-prod-rollback

# 3. Notify team of incident
# 4. Analyze root cause
# 5. Fix and redeploy
```

---

## ✨ SUCCESS CRITERIA

✅ **Deployment is successful when:**

- Frontend loads without JavaScript errors
- Backend `/health` returns `status: "online"`
- Database shows all tables created
- DataDog receives APM traces
- DataDog receives RUM sessions
- No alerts triggered in first hour
- All security headers present
- HTTPS working on both services
- CORS properly configured
- Backups enabled and tested

---

## 📚 QUICK REFERENCE

**Production URLs** (update after deployment)
```
Frontend:  https://mega-brain-prod-[random].vercel.app
Backend:   https://mega-brain-api-[random].onrender.com
Database:  postgresql://...
Monitor:   https://app.datadoghq.com
```

**Important Files**
```
PRODUCTION-DEPLOYMENT-STRATEGY.md    → Full guide
PRODUCTION-DEPLOYMENT-CHECKLIST.md   → This file
scripts/schema-init.sql              → Database schema
server.js                            → Backend server
frontend/                            → Frontend application
```

**Support Contacts**
```
Vercel Support:    https://vercel.com/support
Render Support:    https://render.com/support
Supabase Support:  https://supabase.com/support
DataDog Support:   https://www.datadoghq.com/support/
```

---

**END OF PRODUCTION DEPLOYMENT CHECKLIST**

*When deployment is complete, celebrate! You've successfully deployed a production application.*
