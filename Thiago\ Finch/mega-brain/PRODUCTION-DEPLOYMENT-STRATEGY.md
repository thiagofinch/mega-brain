# PRODUCTION DEPLOYMENT STRATEGY

> **Date:** 2026-03-06
> **Status:** READY FOR EXECUTION
> **Estimated Duration:** 45-90 minutes
> **Architecture:** Vercel (Frontend) + Render (Backend) + Supabase (Database) + DataDog (Monitoring)

---

## 📊 CURRENT STATE ANALYSIS

### Project Structure
```
mega-brain/
├── frontend/                    # Next.js 14 application
│   ├── package.json
│   ├── next.config.js
│   ├── app/                    # App Router (next/app)
│   ├── components/
│   ├── public/
│   └── tailwind.config.js
│
├── server.js                   # Express backend (3000)
├── src/
│   ├── db.js                   # SQLite/PostgreSQL adapter
│   ├── mocks/                  # Mock data generators
│   └── api/                    # API endpoints
│
├── .env                        # Configuration
├── package.json                # Root package (CLI)
└── docker-compose.dev.yml      # Development Docker setup
```

### Current Technology Stack
- **Frontend:** Next.js 14, React 18, Tailwind CSS, Recharts, Socket.IO client
- **Backend:** Express.js, Node.js, Socket.IO server
- **Database:** SQLite (dev), will migrate to PostgreSQL
- **UI Components:** Framer Motion, next-themes
- **Real-time:** Socket.IO for WebSocket communication

### What Works Locally
- Next.js frontend development server
- Express backend with WebSocket support
- SQLite database integration
- MercadoLivre API integration
- Real-time sales dashboard

---

## 🎯 DEPLOYMENT ARCHITECTURE

### Production Stack

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      END USERS (Browser)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
        ┌───────▼────────┐   ┌──────▼──────┐   ┌──────▼──────────┐
        │  Vercel CDN    │   │  WebSocket  │   │  DataDog RUM    │
        │  (Frontend)    │   │  (Socket.IO)│   │  (Monitoring)   │
        └────────────────┘   └──────┬──────┘   └─────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │    Render.com API Server      │
                    │      (Express + Node.js)      │
                    │    - /api/* endpoints         │
                    │    - WebSocket handler        │
                    │    - MercadoLivre integration │
                    │    - DataDog APM tracing      │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  Supabase PostgreSQL          │
                    │  - sales_live table           │
                    │  - sales_daily table          │
                    │  - Real-time subscriptions    │
                    │  - Automatic backups          │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │    DataDog Monitoring         │
                    │  - APM (Backend traces)       │
                    │  - RUM (Frontend events)      │
                    │  - Log aggregation            │
                    │  - Alerts & dashboards        │
                    └───────────────────────────────┘
```

### DNS & Domain Routing
```
yourdomain.com/
├── yourdomain.com            → Vercel frontend (mega-brain.vercel.app)
├── api.yourdomain.com        → Render backend (mega-brain-api.onrender.com)
└── monitoring.yourdomain.com → DataDog dashboard (optional)
```

---

## 🚀 PHASE 1: PRE-DEPLOYMENT CHECKLIST

### Security Review
```
✓ Remove hardcoded secrets from .env
✓ Generate production-grade API keys
✓ Review CORS configuration
✓ Verify API rate limiting
✓ Check authentication/authorization
✓ Audit database permissions
```

### Code Quality
```
✓ Run npm audit (dependencies)
✓ Check TypeScript compilation
✓ Lint all code (ESLint)
✓ Performance metrics
✓ Accessibility checks (axe, etc.)
```

### Git Preparation
```
✓ Ensure all changes are committed
✓ Branch from main for deployment
✓ Tag release (v1.0.0-prod)
✓ All tests passing
```

---

## 🌐 PHASE 2: FRONTEND DEPLOYMENT (Vercel)

### Step 2.1: Prepare Frontend

```bash
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain/frontend"

# Install dependencies
npm ci

# Build locally first
npm run build

# Check build output
ls -la .next

# Verify build size
du -sh .next
```

**Expected Output:**
- Build completes without errors
- `.next` folder created (~50-150MB)
- No TypeScript errors
- All assets optimized

### Step 2.2: Create Vercel Configuration

**File:** `vercel.json` (root of frontend)

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "nodeVersion": "20.x",
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url",
    "NEXT_PUBLIC_API_WS_URL": "@api_ws_url"
  }
}
```

### Step 2.3: Push to GitHub

```bash
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"

# Verify nothing uncommitted
git status

# Push to remote
git push origin main -u

# Create release tag
git tag v1.0.0-prod
git push origin v1.0.0-prod
```

### Step 2.4: Deploy to Vercel

**Option A: GitHub Integration (Recommended)**
1. Go to https://vercel.com/new
2. Select "Clone from GitHub"
3. Authorize Vercel to access your GitHub
4. Select `mega-brain` repository
5. Configure:
   - **Project Name:** mega-brain-prod
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `.next`
6. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://mega-brain-api.onrender.com`
   - `NEXT_PUBLIC_API_WS_URL`: `wss://mega-brain-api.onrender.com`
7. Click Deploy
8. Wait for build (~3-5 minutes)

**Option B: Vercel CLI**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod

# Follow prompts and confirm
```

### Step 2.5: Verify Frontend Deployment

```bash
# Test frontend URL
VERCEL_URL="https://mega-brain-[random].vercel.app"

# Check homepage loads
curl -I $VERCEL_URL | grep "200\|301"

# Check API connectivity (will fail until backend is live)
curl $VERCEL_URL/api/status || echo "API not ready yet"
```

**Success Criteria:**
- ✓ Frontend loads without errors
- ✓ No 404s on assets
- ✓ Responsive design works
- ✓ Dashboard loads (may show API errors initially)

---

## 🔗 PHASE 3: DATABASE SETUP (Supabase)

### Step 3.1: Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click **"New Project"**
3. Configure:
   - **Organization:** Create or select
   - **Project Name:** `mega-brain-prod`
   - **Database Password:** Generate strong password (save securely)
   - **Region:** `us-east-1` (or closest to your users)
4. Click **Create New Project**
5. Wait for provisioning (~2-3 minutes)

### Step 3.2: Get Connection Details

1. Go to **Settings → Database**
2. Copy the **Connection String:**
   ```
   postgresql://postgres.[project-id]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
3. Save in secure location (password manager)

### Step 3.3: Initialize Database Schema

Create file `scripts/schema-init.sql`:

```sql
-- ============================================================================
-- MEGA BRAIN PRODUCTION SCHEMA
-- ============================================================================

-- Create tables
CREATE TABLE IF NOT EXISTS public.sales_live (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id INTEGER NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1,
  price DECIMAL(12, 2) NOT NULL,
  commission DECIMAL(12, 2),
  shipping_cost DECIMAL(12, 2),
  margin_pct DECIMAL(5, 2),
  marketplace VARCHAR(50) NOT NULL DEFAULT 'mercadolivre',
  sale_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.sales_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sale_date DATE NOT NULL UNIQUE,
  total_sales INTEGER NOT NULL DEFAULT 0,
  gross_revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
  net_revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
  avg_margin DECIMAL(5, 2),
  total_shipping DECIMAL(12, 2),
  total_commission DECIMAL(12, 2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.sales_hourly (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hour_bucket TIMESTAMP WITH TIME ZONE NOT NULL,
  sales_count INTEGER NOT NULL DEFAULT 0,
  revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(hour_bucket)
);

-- Create indexes
CREATE INDEX idx_sales_live_timestamp ON public.sales_live(sale_timestamp DESC);
CREATE INDEX idx_sales_live_marketplace ON public.sales_live(marketplace);
CREATE INDEX idx_sales_live_product ON public.sales_live(product_id);
CREATE INDEX idx_sales_daily_date ON public.sales_daily(sale_date DESC);
CREATE INDEX idx_sales_hourly_bucket ON public.sales_hourly(hour_bucket DESC);

-- Create views
CREATE OR REPLACE VIEW public.v_sales_today AS
SELECT
  COUNT(*) as total_sales,
  SUM(price) as total_revenue,
  AVG(margin_pct) as avg_margin,
  MAX(sale_timestamp) as last_sale
FROM public.sales_live
WHERE DATE(sale_timestamp AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE AT TIME ZONE 'America/Sao_Paulo';

-- Enable Row Level Security (optional, for multi-tenant)
-- ALTER TABLE public.sales_live ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.sales_daily ENABLE ROW LEVEL SECURITY;

-- Create function for daily aggregation
CREATE OR REPLACE FUNCTION public.aggregate_daily_sales()
RETURNS void AS $$
BEGIN
  INSERT INTO public.sales_daily (sale_date, total_sales, gross_revenue, net_revenue, avg_margin)
  SELECT
    DATE(sale_timestamp AT TIME ZONE 'America/Sao_Paulo'),
    COUNT(*),
    SUM(price),
    SUM(price) - SUM(COALESCE(commission, 0)) - SUM(COALESCE(shipping_cost, 0)),
    AVG(margin_pct)
  FROM public.sales_live
  WHERE DATE(sale_timestamp AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE AT TIME ZONE 'America/Sao_Paulo'
  GROUP BY DATE(sale_timestamp AT TIME ZONE 'America/Sao_Paulo')
  ON CONFLICT (sale_date) DO UPDATE SET
    total_sales = EXCLUDED.total_sales,
    gross_revenue = EXCLUDED.gross_revenue,
    net_revenue = EXCLUDED.net_revenue,
    avg_margin = EXCLUDED.avg_margin,
    updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON public.sales_live TO postgres;
GRANT SELECT, INSERT, UPDATE ON public.sales_daily TO postgres;
GRANT SELECT ON public.v_sales_today TO postgres;
```

### Step 3.4: Execute Schema

```bash
# Copy connection string (no trailing newline)
SUPABASE_URL="postgresql://postgres.XXXX:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# Run schema initialization
psql "$SUPABASE_URL" < scripts/schema-init.sql

# Verify tables created
psql "$SUPABASE_URL" -c "\dt public.*"
```

**Expected Output:**
```
Schema | Name        | Type  | Owner
--------+-------------+-------+----------
public | sales_daily | table | postgres
public | sales_hourly| table | postgres
public | sales_live  | table | postgres
```

---

## 🖥️ PHASE 4: BACKEND DEPLOYMENT (Render)

### Step 4.1: Prepare Backend

```bash
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"

# Verify server.js exists
ls -la server.js

# Check dependencies
cat package.json | grep -E "express|socket.io|cors|dotenv"

# Install dependencies (if not already done)
npm ci
```

### Step 4.2: Create Environment Configuration for Production

Update `server.js` to handle production environment:

```javascript
// At the top of server.js, after dotenv.config()

const isProduction = process.env.NODE_ENV === 'production';
const API_PORT = process.env.PORT || 3000;
const WS_PORT = process.env.WS_PORT || 3001;

// CORS configuration
const corsOrigins = isProduction
  ? [
      'https://mega-brain-[random].vercel.app',
      'https://yourdomain.com'
    ]
  : ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3000'];

// Database configuration
const dbConfig = isProduction
  ? {
      type: 'postgres',
      url: process.env.DATABASE_URL,
      ssl: true,
      logging: false
    }
  : {
      type: 'sqlite',
      filename: './dev.db'
    };
```

### Step 4.3: Create Render.com Account

1. Go to https://render.com
2. Sign up with GitHub (easiest)
3. Authorize Render to access your GitHub repositories
4. Go to Dashboard

### Step 4.4: Deploy to Render

1. Click **New+** → **Web Service**
2. Configure:
   - **Repository:** Select `mega-brain`
   - **Branch:** `main`
   - **Name:** `mega-brain-api`
   - **Region:** `Frankfurt` (best for Brazil latency)
   - **Runtime:** `Node`
   - **Build Command:** `npm ci`
   - **Start Command:** `node server.js`
   - **Plan:** `Starter` ($7/month) or `Standard`

3. Add Environment Variables:
   ```
   NODE_ENV = production
   DATABASE_URL = postgresql://postgres.XXXX:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   CORS_ORIGINS = https://mega-brain-[random].vercel.app
   NEXT_PUBLIC_API_URL = https://mega-brain-api-[random].onrender.com

   # Copy from .env
   OPENAI_API_KEY = sk-proj-...
   VOYAGE_API_KEY = pa--...
   MERCADOLIVRE_CLIENT_ID = ...
   MERCADOLIVRE_CLIENT_SECRET = ...
   MERCADOLIVRE_REDIRECT_URL = ...
   MERCADOLIVRE_ACCESS_TOKEN = ...
   ```

4. Click **Create Web Service**
5. Wait for deployment (~3-5 minutes)

**Build Process:**
- Docker image created
- Dependencies installed
- Server starts on PORT (assigned by Render)
- Service becomes accessible

### Step 4.5: Verify Backend Deployment

```bash
# Get Render URL from dashboard (something like https://mega-brain-api-xxx.onrender.com)
RENDER_URL="https://mega-brain-api-[random].onrender.com"

# Test health endpoint
curl -s "$RENDER_URL/health" | jq .

# Expected response:
# {
#   "status": "online",
#   "uptime": 12345,
#   "connectedClients": 0,
#   "database": "connected",
#   "timestamp": "2026-03-06T..."
# }

# Test API endpoint
curl -s "$RENDER_URL/api/sales" | jq . | head -20
```

**Success Criteria:**
- ✓ `/health` returns `status: "online"`
- ✓ Database shows `"connected"`
- ✓ API endpoints respond
- ✓ No 500 errors in response

---

## 📊 PHASE 5: MONITORING SETUP (DataDog)

### Step 5.1: Create DataDog Account

1. Go to https://www.datadoghq.com
2. Sign up for free trial
3. Create organization
4. Create first API key

### Step 5.2: Install APM Agent (Backend)

Update backend to include DataDog tracing:

```bash
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"

# Install dd-trace
npm install dd-trace --save
```

**Update `server.js` (add at very top, before other imports):**

```javascript
import tracer from 'dd-trace';

if (process.env.NODE_ENV === 'production') {
  tracer.init({
    service: 'mega-brain-api',
    version: '1.0.0',
    env: 'production',
    logInjection: true,
    analytics: true
  });
}

// Rest of imports...
import express from 'express';
// ...
```

### Step 5.3: Install RUM Agent (Frontend)

Update Next.js frontend:

```bash
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain/frontend"

npm install @datadog/browser-rum --save
```

**Create file `app/datadog.ts`:**

```typescript
import { datadogRum } from '@datadog/browser-rum';

export function initializeDataDog() {
  if (typeof window === 'undefined') return;

  if (process.env.NEXT_PUBLIC_ENV === 'production') {
    datadogRum.init({
      applicationId: process.env.NEXT_PUBLIC_DD_APP_ID || '',
      clientToken: process.env.NEXT_PUBLIC_DD_CLIENT_TOKEN || '',
      service: 'mega-brain-frontend',
      version: '1.0.0',
      site: 'datadoghq.com',
      sessionSampleRate: 100,
      sessionReplaySampleRate: 20,
      trackUserInteractions: true,
      trackResources: true,
      trackLongTasks: true,
      defaultPrivacyLevel: 'mask-user-input'
    });

    datadogRum.startSessionReplayRecording();
  }
}
```

**Update `app/layout.tsx`:**

```typescript
import { initializeDataDog } from './datadog';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Initialize DataDog client-side
  if (typeof window !== 'undefined') {
    initializeDataDog();
  }

  return (
    <html lang="en">
      <head>
        {/* ... existing head content ... */}
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
```

### Step 5.4: Configure DataDog Dashboard

1. Login to https://app.datadoghq.com
2. Navigate to **Monitors** → **New Monitor**
3. Create alerts:

**Alert 1: High Error Rate**
```
Metric: trace.web.request.errors
Threshold: > 1% over 5 minutes
Severity: Warning
```

**Alert 2: High Latency**
```
Metric: trace.web.request.duration.99p
Threshold: > 500ms over 5 minutes
Severity: Warning
```

**Alert 3: Database Connection Failures**
```
Metric: custom.db.connection.errors
Threshold: > 0 over 1 minute
Severity: Critical
```

**Alert 4: Service Down**
```
Type: Host Alert
Metric: system.up
Threshold: down for 5 minutes
Severity: Critical
```

### Step 5.5: Create Custom Dashboard

1. Click **Dashboard** → **New Dashboard**
2. Name: "Mega Brain Production"
3. Add widgets:
   - Request volume (last 24h)
   - Error rate (%)
   - P99 latency (ms)
   - Active users (RUM)
   - Database query duration
   - Revenue trend (custom metric)

---

## ✅ PHASE 6: PRODUCTION VALIDATION

### Step 6.1: Full Stack Integration Test

```bash
# Set variables
FRONTEND_URL="https://mega-brain-[random].vercel.app"
BACKEND_URL="https://mega-brain-api-[random].onrender.com"

# Test 1: Frontend loads
echo "Testing frontend..."
curl -I $FRONTEND_URL | grep "200\|301" && echo "✓ Frontend responds" || echo "✗ Frontend failed"

# Test 2: Backend health
echo "Testing backend health..."
curl -s "$BACKEND_URL/health" | jq .status | grep -q "online" && echo "✓ Backend online" || echo "✗ Backend down"

# Test 3: Database connectivity
echo "Testing database..."
curl -s "$BACKEND_URL/api/sales" | jq . > /dev/null && echo "✓ Database accessible" || echo "✗ Database error"

# Test 4: CORS headers
echo "Testing CORS..."
curl -s -H "Origin: $FRONTEND_URL" "$BACKEND_URL/health" | grep -q "online" && echo "✓ CORS configured" || echo "✗ CORS issue"

# Test 5: WebSocket connectivity
echo "Testing WebSocket..."
wscat -c "wss://$(echo $BACKEND_URL | sed 's|https://||')" || echo "⚠ WebSocket check (requires wscat)"
```

### Step 6.2: Performance Validation

```bash
# Use Google PageSpeed Insights
# https://pagespeed.web.dev/?url=https://mega-brain-[random].vercel.app

# Expected metrics:
# - Largest Contentful Paint (LCP): < 2.5s
# - Cumulative Layout Shift (CLS): < 0.1
# - First Input Delay (FID): < 100ms
```

### Step 6.3: Security Audit

```bash
# Check HTTPS enforcement
curl -I $FRONTEND_URL | grep -i "strict-transport-security"

# Verify no hardcoded secrets
git log -p --all -S "sk-proj-\|pa--" | head -5

# Check API authentication
curl -s "$BACKEND_URL/api/protected" | grep -i "unauthorized\|forbidden" && echo "✓ Auth required"
```

### Step 6.4: Load Testing (Optional)

```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 "$FRONTEND_URL/"

# Using hey (better results)
go install github.com/rakyll/hey@latest
hey -n 100 -c 10 -m GET "$BACKEND_URL/health"
```

**Expected Results:**
```
Summary:
  Total:        5.123 secs
  Slowest:      1.234 secs
  Fastest:      0.234 secs
  Average:      0.512 secs
  Requests/sec: 19.52

Status code distribution:
  [200]  100 responses
```

---

## 🔐 PHASE 7: PRODUCTION HARDENING

### Step 7.1: Environment Variables Security

**Ensure all secrets are in Render/Vercel environment, NOT in code:**

```bash
# Audit: No secrets in code
git grep -l "sk-proj-\|postgresql://\|Bearer " -- "*.js" "*.ts" | wc -l

# Should return 0
```

### Step 7.2: Database Backup Strategy

**Supabase automatic backups:**
1. Go to Supabase Dashboard
2. Settings → Backups
3. Verify daily backups enabled
4. Test restore procedure

**Manual backup (recommended):**
```bash
pg_dump "$DATABASE_URL" > "backup-$(date +%Y-%m-%d).sql"
```

### Step 7.3: SSL/TLS Verification

```bash
# Check certificate validity
openssl s_client -connect mega-brain-api-[random].onrender.com:443 -showcerts

# Expected: "Verify return code: 0 (ok)"
```

### Step 7.4: Rate Limiting Configuration

Add to `server.js`:

```javascript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

// Apply to all requests
app.use(limiter);

// Or specific routes
app.get('/api/sales', limiter, (req, res) => {
  // ...
});
```

---

## 📈 PHASE 8: POST-DEPLOYMENT CHECKLIST

### Immediate (First Hour)
- [ ] All services responding (health checks passing)
- [ ] Frontend loads without JavaScript errors
- [ ] Dashboard displays data
- [ ] DataDog receiving metrics
- [ ] No critical alerts triggered
- [ ] Error rate < 1%
- [ ] Response time P99 < 500ms

### First Day
- [ ] Monitor error logs in DataDog
- [ ] Verify database is persisting data
- [ ] Check WebSocket connections stable
- [ ] Monitor resource usage (CPU, memory)
- [ ] Test backup/restore procedure
- [ ] Review security headers

### First Week
- [ ] Monitor daily metrics trends
- [ ] Verify automatic daily sales aggregation
- [ ] Check database query performance
- [ ] Review user feedback
- [ ] Optimize any slow queries
- [ ] Update documentation with production URLs

### Ongoing
- [ ] Weekly DataDog review
- [ ] Monthly cost optimization
- [ ] Quarterly security audit
- [ ] Database maintenance (VACUUM, ANALYZE)
- [ ] Dependency updates (security patches)
- [ ] Disaster recovery drill (restore from backup)

---

## 🆘 TROUBLESHOOTING GUIDE

### Frontend Issues

**Problem:** Blank page on Vercel
```
Solution:
1. Check build logs: Vercel Dashboard → Deployments → Build logs
2. Verify next.config.js is valid
3. Check NEXT_PUBLIC_API_URL is set
4. Clear Vercel cache and redeploy
```

**Problem:** API calls returning 404
```
Solution:
1. Verify NEXT_PUBLIC_API_URL is correct in Vercel env vars
2. Check backend is responding: curl $BACKEND_URL/health
3. Verify CORS is configured on backend
4. Check browser console for network errors
```

### Backend Issues

**Problem:** Render service keeps crashing
```
Solution:
1. Check Render build logs for errors
2. Verify DATABASE_URL is correct
3. Check Node.js version compatibility
4. Review error logs: Render Dashboard → Logs
5. Increase memory if needed
```

**Problem:** Database connection failing
```
Solution:
1. Verify DATABASE_URL in Render env vars
2. Check Supabase is accepting connections: psql $DATABASE_URL -c "SELECT 1"
3. Verify IP is whitelisted (Supabase Settings → Network)
4. Check SSL requirement: add ?sslmode=require to URL
```

### Monitoring Issues

**Problem:** DataDog not receiving data
```
Solution:
1. Verify DD_TRACE_ENABLED=true
2. Check API key is correct
3. Verify network allows DataDog endpoints
4. Check browser console for RUM errors
5. Review DataDog agent logs
```

---

## 📚 REFERENCE URLS

### Deployed Services
- **Frontend:** https://mega-brain-[random].vercel.app
- **Backend API:** https://mega-brain-api-[random].onrender.com
- **Database:** Supabase PostgreSQL (private)
- **Monitoring:** https://app.datadoghq.com/dashboard

### Documentation
- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs
- DataDog Docs: https://docs.datadoghq.com

### Support Contacts
- **Vercel Support:** https://vercel.com/support
- **Render Support:** https://render.com/support
- **Supabase Support:** https://supabase.com/support
- **DataDog Support:** https://www.datadoghq.com/support/

---

## 📋 DEPLOYMENT COMMAND REFERENCE

```bash
# Verify git is clean
git status
git log --oneline -5

# Push to GitHub
git push origin main
git tag v1.0.0-prod && git push origin v1.0.0-prod

# Test frontend build locally
cd frontend && npm run build && npm start

# Test backend locally
NODE_ENV=production node server.js

# Verify production databases
psql $DATABASE_URL -c "SELECT COUNT(*) FROM public.sales_live"

# Check service status
curl -s https://mega-brain-[random].vercel.app/health
curl -s https://mega-brain-api-[random].onrender.com/health

# Tail Render logs
render logs mega-brain-api

# Tail Vercel logs
vercel logs

# DataDog health
curl -s https://api.datadoghq.com/api/v1/validate \
  -H "DD-API-KEY: $DD_API_KEY"
```

---

**END OF PRODUCTION DEPLOYMENT STRATEGY**

*For questions or issues, refer to Troubleshooting Guide or contact platform support.*
