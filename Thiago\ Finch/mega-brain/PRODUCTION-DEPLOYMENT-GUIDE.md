# PRODUCTION DEPLOYMENT GUIDE

> **Date:** March 6, 2026
> **Status:** READY FOR EXECUTION
> **Duration:** 45-90 minutes
> **Architecture:** Vercel (Frontend) + Render (Backend) + Supabase (Database) + DataDog (Monitoring)

---

## 🚀 QUICK START

This guide walks you through deploying **Mega Brain** to production with zero downtime.

### What You'll Deploy
- **Frontend:** Next.js app on Vercel (automatic deployments, CDN, HTTPS)
- **Backend:** Express server on Render (stateless, auto-scaling, monitoring)
- **Database:** PostgreSQL on Supabase (managed, backups, replication)
- **Monitoring:** DataDog APM + RUM (real-time insights, alerts)

### Prerequisites
- [ ] GitHub account (repository already set up)
- [ ] Vercel account (free, https://vercel.com)
- [ ] Render account (free tier available, https://render.com)
- [ ] Supabase account (free tier, https://supabase.com)
- [ ] DataDog account (free trial, https://datadoghq.com)
- [ ] 45-90 minutes of time
- [ ] Knowledge of your API endpoints and database schema

---

## 📚 DOCUMENTATION FILES

Read in this order:

1. **This file** (PRODUCTION-DEPLOYMENT-GUIDE.md) - Overview and strategy
2. **PRODUCTION-DEPLOYMENT-STRATEGY.md** - Detailed technical guide (8,000+ words)
3. **PRODUCTION-DEPLOYMENT-CHECKLIST.md** - Step-by-step checklist with exact commands

---

## 🎯 DEPLOYMENT ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USERS (Browser)                              │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼────────┐   ┌───▼────────┐  ┌──▼──────────┐
        │  Vercel CDN    │   │  WebSocket │  │ DataDog RUM │
        │  (Frontend)    │   │  (Real-time)   │ (Analytics) │
        └────────────────┘   └───┬────────┘  └─────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Render.com (Backend)   │
                    │  - Express API          │
                    │  - WebSocket handler    │
                    │  - Auto-scaling         │
                    │  - DataDog APM          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Supabase PostgreSQL    │
                    │  - Production database  │
                    │  - Automatic backups    │
                    │  - Real-time features   │
                    └────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  DataDog (Monitoring)   │
                    │  - APM traces           │
                    │  - Error tracking       │
                    │  - Performance metrics  │
                    └────────────────────────┘
```

---

## 🔧 PHASE OVERVIEW

### Phase 1: Pre-Deployment (15 min)
- Git repository audit
- Security review
- Code quality checks

### Phase 2: Frontend Deployment (15 min)
- Build verification
- Push to GitHub
- Deploy to Vercel
- Configure environment variables

### Phase 3: Database Setup (20 min)
- Create Supabase project
- Initialize PostgreSQL schema
- Verify connectivity

### Phase 4: Backend Deployment (15 min)
- Create Render service
- Add environment variables
- Deploy and verify

### Phase 5: Monitoring (15 min)
- Configure DataDog APM
- Set up real-time monitoring
- Create alerting rules

### Phase 6: Final Validation (10 min)
- Full stack integration tests
- Security verification
- Performance baseline

---

## ✅ PRODUCTION READINESS CHECKLIST

Before starting, verify:

### Code Quality
- [ ] No hardcoded secrets in code
- [ ] All tests passing
- [ ] ESLint clean
- [ ] TypeScript compiles
- [ ] No npm vulnerabilities

### Git Repository
- [ ] Working tree clean
- [ ] All changes committed
- [ ] GitHub remote configured
- [ ] Main branch is primary
- [ ] No untracked files

### Configuration
- [ ] .env file exists locally
- [ ] .env is gitignored
- [ ] Environment variables documented
- [ ] Database schema ready
- [ ] API endpoints tested locally

### Infrastructure
- [ ] Node.js 18+ installed
- [ ] npm latest version
- [ ] All dependencies installed
- [ ] Frontend builds locally
- [ ] Backend starts locally

---

## 🌐 FRONTEND DEPLOYMENT (Vercel)

### Step 1: Prepare Frontend
```bash
cd frontend
npm ci                    # Install dependencies
npm run build             # Verify build succeeds
npm run lint              # Check code quality
```

### Step 2: Push to GitHub
```bash
git push origin main
git tag v1.0.0-prod
git push origin v1.0.0-prod
```

### Step 3: Deploy to Vercel
1. Go to https://vercel.com/new
2. Click "Clone from GitHub"
3. Select `mega-brain` repository
4. Configure:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `.next`
5. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://mega-brain-api.onrender.com`
   - `NEXT_PUBLIC_API_WS_URL`: `wss://mega-brain-api.onrender.com`
6. Click Deploy

**Expected time:** 5 minutes

### Step 4: Verify Deployment
```bash
curl -I https://mega-brain-prod-[random].vercel.app
# Expected: HTTP 200 OK
```

---

## 🔗 DATABASE SETUP (Supabase)

### Step 1: Create Project
1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Configure:
   - **Name:** `mega-brain-prod`
   - **Region:** `us-east-1`
   - **Password:** Generate strong password
4. Wait for provisioning (2-3 minutes)

### Step 2: Initialize Schema
```bash
# Get connection string from Supabase Dashboard
SUPABASE_URL="postgresql://..."

# Initialize database
psql "$SUPABASE_URL" < scripts/schema-init.sql

# Verify tables created
psql "$SUPABASE_URL" -c "\dt public.*"
```

### Step 3: Enable Backups
1. Go to Supabase Dashboard → Settings → Backups
2. Verify daily backups enabled
3. Note retention period

**Expected time:** 8 minutes

---

## 🖥️ BACKEND DEPLOYMENT (Render)

### Step 1: Create Service
1. Go to https://render.com/dashboard
2. Click "New+" → "Web Service"
3. Select `mega-brain` repository
4. Configure:
   - **Name:** `mega-brain-api`
   - **Region:** `Frankfurt`
   - **Build Command:** `npm ci`
   - **Start Command:** `node server.js`

### Step 2: Add Environment Variables
```
NODE_ENV = production
DATABASE_URL = postgresql://postgres.XXX:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
CORS_ORIGINS = https://mega-brain-prod-[random].vercel.app
OPENAI_API_KEY = sk-proj-...
VOYAGE_API_KEY = pa--...
MERCADOLIVRE_CLIENT_ID = ...
MERCADOLIVRE_CLIENT_SECRET = ...
MERCADOLIVRE_REDIRECT_URL = ...
MERCADOLIVRE_ACCESS_TOKEN = ...
```

### Step 3: Deploy
Click "Create Web Service" and wait for build (3-5 minutes)

### Step 4: Verify Deployment
```bash
curl https://mega-brain-api-[random].onrender.com/health
# Expected: {"status":"online","database":"connected",...}
```

---

## 📊 MONITORING SETUP (DataDog)

### Step 1: Create Account
1. Go to https://www.datadoghq.com
2. Sign up for free trial
3. Create organization and API key

### Step 2: Add APM to Backend
```bash
npm install dd-trace --save

# Add to top of server.js
import tracer from 'dd-trace';
tracer.init({
  service: 'mega-brain-api',
  env: 'production'
});
```

### Step 3: Add RUM to Frontend
```bash
npm install @datadog/browser-rum --save

# Initialize in app/layout.tsx
import { datadogRum } from '@datadog/browser-rum';
datadogRum.init({...});
```

### Step 4: Configure Alerts
1. DataDog → Monitors → New Monitor
2. Create alerts for:
   - Error rate > 1%
   - Latency P99 > 500ms
   - Database connection failures
   - Service unavailability

---

## 🧪 VALIDATION TESTS

### Full Stack Connectivity
```bash
# Frontend loads
curl -I https://mega-brain-prod-[random].vercel.app

# Backend responds
curl https://mega-brain-api-[random].onrender.com/health

# Database accessible
curl https://mega-brain-api-[random].onrender.com/api/sales

# CORS configured
curl -H "Origin: https://mega-brain-prod-[random].vercel.app" \
  https://mega-brain-api-[random].onrender.com/health
```

### Browser Testing
1. Open frontend URL in browser
2. Check DevTools Console (no errors)
3. Check Network tab (all requests successful)
4. Test dashboard interaction
5. Verify responsive design

### Monitoring Data
1. Generate traffic to backend
2. Wait 2-3 minutes
3. Check DataDog dashboard for:
   - APM traces
   - RUM sessions
   - Custom metrics

---

## 🔐 SECURITY CHECKLIST

- [ ] No hardcoded secrets in code
- [ ] .env is gitignored
- [ ] HTTPS/TLS on all services
- [ ] CORS properly configured
- [ ] Database backups enabled
- [ ] API rate limiting enabled
- [ ] Security headers present
- [ ] No sensitive data in logs

---

## 📈 POST-DEPLOYMENT ACTIONS

### First Hour
- Monitor error rates (should be 0-1%)
- Check response times (P99 < 500ms)
- Verify database persistence
- Confirm all services responding

### First Day
- Review error logs in DataDog
- Check database query performance
- Verify automatic backups
- Test disaster recovery procedure

### First Week
- Monitor trends in metrics
- Optimize any slow queries
- Review security logs
- Update documentation

---

## 🆘 TROUBLESHOOTING

### Frontend Issues
```bash
# Blank page on Vercel
# → Check Vercel build logs
# → Verify NEXT_PUBLIC_API_URL is set
# → Clear cache and redeploy

# API 404 errors
# → Verify backend URL in env vars
# → Check backend is responding
# → Check CORS configuration
```

### Backend Issues
```bash
# Service keeps crashing
# → Check Render logs
# → Verify DATABASE_URL
# → Increase memory if needed

# Database connection fails
# → Check connection string
# → Verify Supabase is up
# → Check IP whitelisting
```

### Monitoring Issues
```bash
# DataDog not receiving data
# → Verify API key
# → Check agent is initialized
# → Review network connectivity
```

---

## 📚 DETAILED DOCUMENTATION

For comprehensive information, see:
- **PRODUCTION-DEPLOYMENT-STRATEGY.md** - Full technical guide
- **PRODUCTION-DEPLOYMENT-CHECKLIST.md** - Step-by-step with exact commands

---

## 📞 SUPPORT RESOURCES

**Platform Documentation:**
- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs
- DataDog Docs: https://docs.datadoghq.com

**Support Contacts:**
- Vercel Support: https://vercel.com/support
- Render Support: https://render.com/support
- Supabase Support: https://supabase.com/support
- DataDog Support: https://datadoghq.com/support

---

## ✨ SUCCESS CRITERIA

Your deployment is successful when:

✅ Frontend loads without JavaScript errors
✅ Backend `/health` returns `status: "online"`
✅ Database tables created and accessible
✅ DataDog receiving APM traces
✅ DataDog receiving RUM sessions
✅ HTTPS working on both services
✅ CORS properly configured
✅ No critical errors in first hour
✅ Error rate < 1%
✅ Response time P99 < 500ms

---

## 🎉 SUMMARY

You now have a complete production deployment package with:

1. **PRODUCTION-DEPLOYMENT-STRATEGY.md** (8,000+ words)
   - Detailed technical guide
   - Architecture diagrams
   - Complete code examples
   - Troubleshooting guide

2. **PRODUCTION-DEPLOYMENT-CHECKLIST.md** (step-by-step)
   - Exact commands to run
   - Things to verify at each step
   - Success criteria for each phase

3. **This guide** (overview & quick reference)
   - High-level strategy
   - Key milestones
   - Resource links

### Next Steps
1. Read PRODUCTION-DEPLOYMENT-STRATEGY.md
2. Follow PRODUCTION-DEPLOYMENT-CHECKLIST.md exactly
3. Deploy to production
4. Monitor for 24 hours
5. Celebrate! 🎉

---

**Ready to deploy? Start with PRODUCTION-DEPLOYMENT-CHECKLIST.md**

*For questions or issues, refer to the troubleshooting section or contact platform support.*
