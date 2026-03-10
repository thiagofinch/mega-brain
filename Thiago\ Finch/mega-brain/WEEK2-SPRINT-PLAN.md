# WEEK 2 SPRINT PLAN
## Dashboard + Data Integration Sprint
**Period:** 2026-03-10 to 2026-03-14
**Prepared by:** JARVIS
**Last Updated:** 2026-03-06

---

## 📊 OVERVIEW

**Goal:** Build integrated Dashboard from Week 1 infrastructure foundation + introduce real-time data flow

**Definition of Done:**
1. ✅ PostgreSQL + Redis + N8N infrastructure live
2. ✅ Frontend connected to live API
3. ✅ Dashboard with 7 core components rendering
4. ✅ Real-time sales data flowing end-to-end
5. ✅ Performance benchmarks met (Lighthouse 90+)

**Team:** Data Engineer (Mon) + Frontend Dev (Tue-Fri)

---

## 🎯 PHASE BREAKDOWN

### MONDAY: Data Engineer Day 2 (Infrastructure Execution)

**Mission:** Complete PostgreSQL + Redis + N8N setup initiated in Week 1

**Tasks:**

#### T1: PostgreSQL Database Setup
- [ ] Choose execution path (Docker or Manual) from DOCKER-QUICK-START.md
- [ ] Execute docker-compose or manual installation
- [ ] Verify schema creation (3 tables, 10 indexes, 5 views)
- [ ] Confirm DDL: `SELECT COUNT(*) FROM information_schema.tables`
- [ ] Create DATA-ENGINEER-DAY1-REPORT.md with screenshots

**Estimated Time:** 30-45 minutes
**Success Criteria:** All 3 tables created, 10 indexes present, 5 views functional

---

#### T2: Redis Configuration
- [ ] Start Redis service (Docker or local)
- [ ] Configure TTL policies:
  - 5-min cache for sales_live queries
  - 1-hour cache for tariffs_snapshot
  - 30-sec cache for real-time updates
- [ ] Test cache hit/miss rates
- [ ] Verify ping and basic commands

**Estimated Time:** 15-20 minutes
**Success Criteria:** redis-cli ping returns PONG, SET/GET work, TTL policies configured

---

#### T3: N8N Workflow Integration
- [ ] Import workflow from scripts/n8n-workflow.json
- [ ] Configure API credentials for ML endpoint
- [ ] Set cron trigger for hourly sync
- [ ] Test DRY RUN with sample data
- [ ] Document workflow in N8N-WORKFLOW-README.md

**Estimated Time:** 20-30 minutes
**Success Criteria:** Workflow imports, DRY RUN successful, cron scheduled

---

#### T4: End-to-End Infrastructure Test
- [ ] Insert sample sales data into PostgreSQL
- [ ] Trigger N8N workflow manually
- [ ] Verify data in Redis cache
- [ ] Check logs for errors
- [ ] Create summary report

**Estimated Time:** 15-20 minutes
**Success Criteria:** Full data pipeline works, no errors in logs

---

### TUESDAY: Frontend Performance + Lighthouse Audit

**Mission:** Establish performance baseline, prepare for dashboard components

**Tasks:**

#### T5: Full Lighthouse Audit
- [ ] Install lighthouse CLI (if needed)
- [ ] Run full audit: `lighthouse http://localhost:3000 --view`
- [ ] Capture scores for:
  - [ ] Performance
  - [ ] Accessibility
  - [ ] Best Practices
  - [ ] SEO
- [ ] Document baselines in PERFORMANCE-BASELINE.md
- [ ] Identify optimization opportunities

**Estimated Time:** 20 minutes
**Expected Scores:**
- Performance: 85-95
- Accessibility: 90+
- Best Practices: 90+
- SEO: 100

**Success Criteria:** All scores ≥85

---

#### T6: Performance Metrics Analysis
- [ ] Capture Core Web Vitals:
  - [ ] LCP (Largest Contentful Paint) - target <2.5s
  - [ ] CLS (Cumulative Layout Shift) - target <0.1
  - [ ] FID (First Input Delay) - target <100ms
- [ ] Run 10 tests for statistical significance
- [ ] Document variance and outliers
- [ ] Create optimization roadmap

**Estimated Time:** 30 minutes
**Success Criteria:** Metrics captured, roadmap created

---

#### T7: Component Testing Framework Setup
- [ ] Install Jest + React Testing Library
- [ ] Create example test for Header component
- [ ] Document testing patterns
- [ ] Create TEST-SETUP.md

**Estimated Time:** 25 minutes
**Success Criteria:** Jest configured, 2 tests passing

---

### WEDNESDAY-FRIDAY: Dashboard Components Development

**Mission:** Build 7 core dashboard components + integrate with live data

#### Core Components (7 Total)

1. **Dashboard Layout** (Container)
   - Grid-based 2-column layout
   - Responsive (mobile-first)
   - Dark/light theme support
   - Files: `components/Dashboard.tsx`

2. **Header Navigation** (Enhanced)
   - Logo + branding
   - User menu
   - Theme toggle
   - Files: Update existing `components/Header.tsx`

3. **Metrics Card** (Reusable)
   - Icon + label + value
   - Trend indicator (↑/↓)
   - Configurable colors
   - Files: `components/MetricCard.tsx`

4. **Sales Chart** (Chart.js)
   - Line chart: sales over time
   - Real-time updates
   - Responsive sizing
   - Files: `components/SalesChart.tsx`

5. **Pricing Table** (Data)
   - 3 plans (Basic, Pro, Enterprise)
   - Feature comparison
   - CTA button for each tier
   - Files: `components/PricingTable.tsx`

6. **Real-Time Activity Feed** (WebSocket)
   - Latest sales notifications
   - Auto-updating list
   - Time-relative formatting
   - Files: `components/ActivityFeed.tsx`

7. **API Status Monitor** (Health Check)
   - Service status indicators
   - Response times
   - Last sync timestamp
   - Files: `components/StatusMonitor.tsx`

---

## 📋 TASK BREAKDOWN BY COMPONENT

### T8: Metrics Card Component (WED AM)
**Time:** 90 minutes
**Files:**
- `app/components/MetricCard.tsx` (new)
- `app/components/MetricCard.stories.tsx` (storybook)
- `__tests__/MetricCard.test.tsx` (test)

**Checklist:**
- [ ] Component accepts: icon, label, value, trend
- [ ] Displays percentage change (↑/↓)
- [ ] Color coding (green/red/neutral)
- [ ] Responsive at 3 breakpoints
- [ ] Passes accessibility audit
- [ ] 3 unit tests passing
- [ ] Story in Storybook

---

### T9: Sales Chart Component (WED PM)
**Time:** 120 minutes
**Dependencies:** chart.js, react-chartjs-2
**Files:**
- `app/components/SalesChart.tsx` (new)
- `app/hooks/useSalesData.ts` (hook for fetching data)
- `__tests__/SalesChart.test.tsx` (test)

**Checklist:**
- [ ] Fetches data from /api/sales
- [ ] Renders line chart with date labels
- [ ] Updates every 30 seconds
- [ ] Responsive sizing
- [ ] Error handling if API fails
- [ ] Loading state while fetching
- [ ] 2 unit tests passing

---

### T10: Pricing Table Component (THU AM)
**Time:** 60 minutes
**Files:**
- `app/components/PricingTable.tsx` (new)
- `__tests__/PricingTable.test.tsx` (test)

**Checklist:**
- [ ] Fetches from /api/tarifas
- [ ] Displays 3 tiers in table
- [ ] Feature comparison grid
- [ ] CTA button for each plan
- [ ] Highlight "most popular" tier
- [ ] Responsive on mobile
- [ ] 2 unit tests passing

---

### T11: Activity Feed Component (THU PM)
**Time:** 90 minutes
**Dependencies:** WebSocket hook
**Files:**
- `app/components/ActivityFeed.tsx` (new)
- `app/hooks/useWebSocket.ts` (hook - already exists!)
- `__tests__/ActivityFeed.test.tsx` (test)

**Checklist:**
- [ ] Uses existing useWebSocket hook
- [ ] Displays latest activities
- [ ] Auto-scrolls to new items
- [ ] Relative time formatting (e.g., "2 min ago")
- [ ] Max 10 items visible (scrollable)
- [ ] Loading skeleton
- [ ] 2 unit tests passing

---

### T12: Status Monitor Component (FRI AM)
**Time:** 60 minutes
**Files:**
- `app/components/StatusMonitor.tsx` (new)
- `__tests__/StatusMonitor.test.tsx` (test)

**Checklist:**
- [ ] Calls /api/health every 10 seconds
- [ ] Shows 3 service statuses: API, DB, Cache
- [ ] Color indicators (green/yellow/red)
- [ ] Response time for each
- [ ] Last check timestamp
- [ ] Error messages if unhealthy
- [ ] 2 unit tests passing

---

### T13: Dashboard Layout Integration (FRI PM)
**Time:** 120 minutes
**Files:**
- `app/page.tsx` (refactor - replace home)
- `app/components/Dashboard.tsx` (new)
- `app/styles/dashboard.css` (new)

**Checklist:**
- [ ] Imports all 7 components
- [ ] Grid layout: 2-column on desktop, 1-column on mobile
- [ ] Responsive breakpoints: mobile (320px), tablet (768px), desktop (1024px)
- [ ] All 7 components rendering
- [ ] Dark mode toggle works
- [ ] No console errors
- [ ] Lighthouse performance still ≥85

---

## 📊 COMPONENT DEPENDENCY MATRIX

```
Dashboard (page.tsx)
├── Header (existing + enhanced)
├── MetricCard (x4 instances)
├── SalesChart (new)
├── PricingTable (new)
├── ActivityFeed (new)
├── StatusMonitor (new)
└── Global Theme Context

Hooks Used:
├── useApi (existing)
├── useSalesData (new - extends useApi)
├── useWebSocket (existing)
├── useTheme (existing)
└── useMetrics (new helper)
```

---

## 🏗️ ARCHITECTURE DECISIONS

### Data Flow
```
PostgreSQL → N8N → API Routes → Frontend Hooks → Components
   ↓
Redis Cache → API Routes → Frontend Components (if cache hit)
```

### Component Patterns
- Functional components with hooks
- TypeScript strict mode
- Tailwind CSS for styling
- SWR for data fetching
- Custom hooks for reusable logic
- Error boundaries for safety

### Testing Strategy
- Unit tests for each component (Jest + React Testing Library)
- Snapshot tests for UI stability
- Integration tests for data flow
- E2E tests for full user journey (future)

---

## 🎮 SPRINT CEREMONIES

### Daily Standup (10 min)
- **Time:** 9:00 AM (before work)
- **Format:** What did I do? What's blocking? What's next?
- **Owner:** Tech Lead

### Mid-Day Check-In (5 min)
- **Time:** 12:00 PM
- **Format:** Any blockers right now?
- **Owner:** Tech Lead

### End-of-Day Sync (10 min)
- **Time:** 5:00 PM
- **Format:** PRs ready? Ready for next day?
- **Owner:** Tech Lead

### Friday Sprint Retrospective (30 min)
- **Time:** 4:00 PM Friday
- **Format:** What went well? What to improve? Metrics.
- **Owner:** Senhor (review)

---

## 📈 SUCCESS METRICS

### Code Quality
- [ ] All components >80% test coverage
- [ ] Zero ESLint violations
- [ ] TypeScript strict mode passing
- [ ] No console warnings in browser

### Performance
- [ ] Lighthouse Performance ≥85
- [ ] LCP <2.5s
- [ ] CLS <0.1
- [ ] FID <100ms
- [ ] API response times <200ms

### Functionality
- [ ] All 7 components rendering
- [ ] Data flowing from API to UI
- [ ] Real-time updates working
- [ ] Responsive at 3+ breakpoints
- [ ] Dark mode toggling

### Business
- [ ] Dashboard shows actual sales data
- [ ] Pricing tiers displayed correctly
- [ ] User can see service health
- [ ] No critical bugs reported

---

## 📋 DELIVERABLES CHECKLIST

By end of Week 2:

**Code:**
- [ ] 7 new components (280+ lines of TSX)
- [ ] 2 new hooks (100+ lines of TS)
- [ ] 3+ test files (150+ lines of tests)
- [ ] Updated package.json with new deps
- [ ] `.env.local` with API endpoints

**Documentation:**
- [ ] WEEK2-COMPONENT-SUMMARY.md
- [ ] PERFORMANCE-BASELINE.md
- [ ] N8N-WORKFLOW-README.md
- [ ] DATA-ENGINEER-DAY1-REPORT.md
- [ ] COMPONENT-INVENTORY.md (what exists, what tested)

**Git:**
- [ ] Feature branches for each component
- [ ] 8-12 PRs with reviews
- [ ] Merge to main when complete
- [ ] `feat: Week 2 dashboard sprint complete` commit

**Data:**
- [ ] PostgreSQL populated with sample data
- [ ] Redis caching configured
- [ ] N8N workflow syncing hourly
- [ ] Dashboard pulling live data

---

## ⚠️ KNOWN RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|-----------|
| PostgreSQL setup fails | Blocks all data flow | Docker fallback available, manual guide provided |
| Chart.js performance | Slow rendering with large datasets | Implement data pagination, limit to 30 days |
| WebSocket connection drops | Real-time updates stop | Auto-reconnect with exponential backoff |
| API rate limiting | Dashboard can't refresh | Implement request queuing, cache aggressively |
| Lighthouse score drops | Performance regression | Monitor Core Web Vitals, test before merge |

---

## 📅 TIMELINE

```
MON:  Data Engineer Day 2      (Infrastructure)      [Complete by 3 PM]
TUE:  Performance + Testing    (Baseline + Setup)    [Complete by EOD]
WED:  Components 1-2           (Metrics, Chart)      [2 components done]
THU:  Components 3-4           (Table, Feed)         [2 components done]
FRI:  Components 5-7 + Review  (Status, Layout)      [All done + QA]
```

---

## ✅ WEEK 2 READINESS CHECKLIST

Before starting Week 2:

- [x] E2E baseline documented (done)
- [x] Infrastructure setup guides ready (ready)
- [x] Frontend running with 7 commits (yes)
- [x] API endpoints working (yes)
- [x] Performance tooling available (installed Lighthouse)
- [x] Component hooks prepared (yes)
- [x] Testing framework installed (ready)
- [x] Documentation templates created (yes)

**Status:** ✅ READY FOR WEEK 2 SPRINT

---

## 🚀 EXECUTION COMMAND

When ready to start Week 2:

```bash
cd "/Users/kennydwillker/Documents/GitHub/Thiago Finch/mega-brain"

# Create feature branch
git checkout -b feat/week2-dashboard

# Start with Data Engineer Day 2
# Follow: DATA-ENGINEER-DAY1-SETUP-GUIDE.md (Docker or Manual)

# Then frontend development
# Create components following WEEK2-SPRINT-PLAN.md

# Track progress in this file as items complete
```

---

*Week 2 Sprint Plan prepared by JARVIS on 2026-03-06*
*Ready for execution starting 2026-03-10 (Monday)*
*Last review: 2026-03-06 10:15 UTC*
