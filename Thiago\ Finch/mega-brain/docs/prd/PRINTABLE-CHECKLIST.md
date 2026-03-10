# PRINTABLE CHECKLIST: Dashboard Apple MVP
## Use this during development & QA

**Imprima este documento** | **Acompanhe com caneta** | **Envie foto quando completo**

---

## SPRINT 1: SETUP & APIs (Semana 1)

### Backend Setup
```
[ ] PostgreSQL 14+ instalado
    - Database: dashboard_apple
    - Tables: daily_metrics, hourly_metrics, raw_orders, marketplace_tariffs, sync_logs
    - Indexes: criados

[ ] Redis 7.x instalado
    - Conexão testada
    - TTL expiração configurada

[ ] Node.js / Python runtime pronto
    - Versão Node >= 18.x ou Python >= 3.9
    - Dependências instaladas

[ ] Database schema executado
    - Script de migration rodou
    - Tables verificadas (SELECT COUNT FROM each table = 0)
```

### Marketplace APIs - Setup
```
[ ] MERCADO LIVRE
    - [ ] MCP existente testado
    - [ ] API call /orders/v2/orders funciona
    - [ ] Sandbox data retrieves corretamente

[ ] TIKTOK SHOP
    - [ ] OAuth flow implementado
    - [ ] API key/token configurado
    - [ ] GET /shop/order_list retorna dados

[ ] SHOPEE
    - [ ] OAuth implementado
    - [ ] API endpoint testado
    - [ ] Dados de teste recebidos

[ ] AMAZON SP-API
    - [ ] AWS credentials configurados
    - [ ] SP-API client inicializado
    - [ ] GET /orders/v0/orders funciona

[ ] MAGALU
    - [ ] API key configurada
    - [ ] Endpoint testado
    - [ ] Dados de teste recebidos
```

### Agregador Lambda
```
[ ] Lambda function criada
    - [ ] Scheduled: 5 minutos
    - [ ] Role/permissions: acesso a RDS + Redis

[ ] Primeira execução testada
    - [ ] Fetch from 5 APIs: OK
    - [ ] Data insert em raw_orders: OK
    - [ ] Metrics calculated: OK
    - [ ] Redis cache updated: OK

[ ] Error handling implementado
    - [ ] Retry logic: exponential backoff
    - [ ] Logging: CloudWatch / similar
    - [ ] Alerts: se sync falhar
```

### Sign-off Sprint 1
```
✓ Backend ready
✓ 5 APIs conectadas
✓ Data flowing para database
✓ Agregador rodando a cada 5 min

Date: ______ | Dev Lead: _____________ | Signature: _________
```

---

## SPRINT 2: FRONTEND SETUP (Semana 2)

### Dev Environment
```
[ ] React/Next.js projeto inicializado
    - [ ] Tailwind ou styled-components configurado
    - [ ] ESLint & Prettier setup

[ ] State management (Redux / Zustand)
    - [ ] Store criado
    - [ ] Actions/reducers: setup básico
    - [ ] DevTools extension funcionando

[ ] HTTP client configurado
    - [ ] Axios ou Fetch
    - [ ] Interceptors para auth & error handling
    - [ ] Retry logic

[ ] WebSocket client
    - [ ] Socket.io instalado
    - [ ] Connection handler setup
    - [ ] Event listeners: subscriptions placeholder
```

### API Client Layer
```
[ ] Dashboard API client
    - [ ] GET /api/metrics/tvr (últimas 24h)
    - [ ] GET /api/metrics/breakdown (por marketplace)
    - [ ] GET /api/metrics/tariffs
    - [ ] GET /api/metrics/timeline (hourly)
    - [ ] All endpoints retornam mock data OK

[ ] WebSocket client
    - [ ] SUBSCRIBE: metrics:updated
    - [ ] SUBSCRIBE: alerts:new
    - [ ] SUBSCRIBE: sync:status
    - [ ] Handlers recebem events OK
```

### Sign-off Sprint 2
```
✓ Frontend environment ready
✓ API clients working (with mocks)
✓ WebSocket connected

Date: ______ | Dev Lead: _____________ | Signature: _________
```

---

## SPRINT 3: CORE FEATURES (Semana 3)

### FEATURE-001: KPI Cards

```
[ ] TVR Card
    - [ ] Layout: Card component
    - [ ] Display: "R$ XX.XXX,XX" (BRL format)
    - [ ] Breakdown: % por marketplace (soma = 100%)
    - [ ] Trending: ↑/↓ com % vs yesterday
    - [ ] Real-time: atualiza quando novo pedido entra

[ ] Margin Card
    - [ ] Cálculo: (TVR - Comissões) / TVR * 100
    - [ ] Threshold visual: verde >20%, amber 15-20%, red <15%
    - [ ] Sparkline: últimas 24h
    - [ ] Alert: dispara quando <15%

[ ] Commission Card
    - [ ] Soma correta: SUM(comissões)
    - [ ] Breakdown por marketplace
    - [ ] Total % do TVR

[ ] Sales (SL24) Card
    - [ ] Contagem correta de pedidos completados
    - [ ] Sparkline por hora (24 barras)
    - [ ] Trending vs yesterday

[ ] AOV Card
    - [ ] Cálculo: TVR / SL24
    - [ ] Breakdown por marketplace
    - [ ] Destaca maior AOV

[ ] Return Rate Card
    - [ ] Cálculo: COUNT(returns) / COUNT(orders) * 100
    - [ ] Threshold colors
    - [ ] Trending 7-day SMA

[ ] Layout & Styling
    - [ ] Desktop: 4 cards per row
    - [ ] Tablet: 2 cards per row
    - [ ] Mobile: 1 card per row
    - [ ] Dark mode colors defined

[ ] Performance
    - [ ] Render time < 500ms
    - [ ] LCP < 1.5s
    - [ ] No layout shifts (CLS < 0.1)

TC Passing: ______ / 35 | Sign-off Date: ______ | QA: _________
```

### FEATURE-007: Real-time Sync

```
[ ] WebSocket connection
    - [ ] Connected on page load
    - [ ] Heartbeat every 30s
    - [ ] Auto-reconnect on drop

[ ] Update latency
    - [ ] New order in API → Dashboard < 500ms
    - [ ] Measured: P95 latency < 500ms
    - [ ] Test: 20 orders, P95 < 500ms ✓

[ ] Update cascade
    - [ ] API call → Agregador → DB → Redis → WebSocket → Frontend
    - [ ] Total time < 500ms
    - [ ] No data loss

[ ] Optimistic updates
    - [ ] Loading state shown while updating
    - [ ] Rollback if server rejects
    - [ ] Error message if failed

[ ] Error handling
    - [ ] Connection refused: retry 5s, 10s, 30s
    - [ ] Max 3 retries before error banner
    - [ ] Manual refresh button works

TC Passing: ______ / 8 | Sign-off Date: ______ | QA: _________
```

### FEATURE-002: Marketplace Breakdown

```
[ ] Table / Cards view
    - [ ] 5 rows (one per marketplace)
    - [ ] Columns: Marketplace | Revenue | Commission | Margin% | Orders
    - [ ] Values formatted correctly (R$ and %)
    - [ ] Total row: sums match

[ ] Sorting
    - [ ] Default: by Revenue DESC
    - [ ] Click headers to sort
    - [ ] Up/down arrows visible

[ ] Filtering
    - [ ] Filter by status: Active / Inactive
    - [ ] Filter by period: 24h / 7d / 30d
    - [ ] Filters apply instantly

[ ] Responsive
    - [ ] Desktop: full table visible
    - [ ] Tablet: horizontal scroll OK
    - [ ] Mobile: cards stacked

TC Passing: ______ / 10 | Sign-off Date: ______ | QA: _________
```

### FEATURE-003: Timeline Charts

```
[ ] Revenue chart (24h)
    - [ ] 24 bars (0-23h)
    - [ ] Height proportional to revenue
    - [ ] Tooltip: hour + value + % of total
    - [ ] Color: blue gradient

[ ] Commission chart
    - [ ] Area chart with gradient
    - [ ] Cumulative values
    - [ ] Top line shows total

[ ] Margin chart
    - [ ] Line chart with 24 points
    - [ ] Red threshold line at 15%
    - [ ] Dynamic color (green >20%, amber, red <15%)

[ ] Marketplace overlay
    - [ ] Toggle to see breakdown per marketplace
    - [ ] Legend clickable to toggle on/off
    - [ ] Colors consistent with UI

[ ] Performance
    - [ ] Charts render < 500ms
    - [ ] Smooth animation on update
    - [ ] No jank or layout shift

TC Passing: ______ / 5 | Sign-off Date: ______ | QA: _________
```

### Sign-off Sprint 3
```
✓ FEATURE-001: KPI Cards PASSED
✓ FEATURE-002: Breakdown PASSED
✓ FEATURE-003: Timeline PASSED
✓ FEATURE-007: Real-time Sync PASSED

Date: ______ | Dev Lead: _____________ | QA Lead: ________
```

---

## SPRINT 4: REMAINING FEATURES (Semana 4)

### FEATURE-004: Tarifas

```
[ ] Tariff table
    - [ ] 5 rows with correct rates
    - [ ] ML: 16.5%, TikTok: 5.0%, Shopee: 5.3%, Amazon: 8.5%, Magalu: 5.0%
    - [ ] Total % = sum of components
    - [ ] Last updated timestamp

[ ] Edit/Override
    - [ ] Click cell to edit
    - [ ] Input validation: 0-100
    - [ ] Total% recalculates automatically
    - [ ] Save/Cancel buttons
    - [ ] Override is local (not persistent)

[ ] Simulator
    - [ ] Input: "If sell R$ 1.000"
    - [ ] Calculate: Gross, Commission, Net, Margin%
    - [ ] Highlight best margin marketplace
    - [ ] Real-time update as user types

TC Passing: ______ / 6 | Sign-off Date: ______ | QA: _________
```

### FEATURE-005: Alerts

```
[ ] Margin alert
    - [ ] Dispara when NM% < 15%
    - [ ] Toast red: "⚠️ Margin < 15%"
    - [ ] Dismissible

[ ] Commission alert
    - [ ] Dispara when commission > 25%
    - [ ] Toast amber: "High commission in [Marketplace]"
    - [ ] View Tariffs link works

[ ] Offline alert
    - [ ] Dispara when disconnected > 10min
    - [ ] Banner: "📴 Offline - showing 2h old data"
    - [ ] Amber background

[ ] API disconnect alert
    - [ ] Badge red next to marketplace
    - [ ] Tooltip: "Disconnected for 5min"
    - [ ] Retries every 30s

[ ] Dismiss & Snooze
    - [ ] X button dismisses
    - [ ] Snooze 1h button
    - [ ] Persists to localStorage

TC Passing: ______ / 9 | Sign-off Date: ______ | QA: _________
```

### FEATURE-006: Dark Mode

```
[ ] System detection
    - [ ] Detects prefers-color-scheme: dark
    - [ ] Loads correct theme on page load
    - [ ] No FOUC (flash of unstyled content)

[ ] Manual toggle
    - [ ] Settings toggle: Light / Dark
    - [ ] Persists to localStorage
    - [ ] Overrides system setting

[ ] Colors
    - [ ] Dark: #000000 bg, #f5f5f7 text
    - [ ] Light: #ffffff bg, #1d1d1d text
    - [ ] Contrast >= 4.5:1 (WCAG AA)

[ ] Components
    - [ ] Cards: dark gray in dark mode
    - [ ] Charts: visible in both
    - [ ] Inputs: border visible in both
    - [ ] Icons: using currentColor

[ ] Transition
    - [ ] Smooth 0.3s transition
    - [ ] Respects prefers-reduced-motion

TC Passing: ______ / 9 | Sign-off Date: ______ | QA: _________
```

### FEATURE-008: Offline Support

```
[ ] Service Worker
    - [ ] Registered on page load
    - [ ] Status: activated and running
    - [ ] Cache strategy: network-first

[ ] IndexedDB
    - [ ] Database created: "dashboardCache"
    - [ ] Stores: hourly_metrics, daily_metrics
    - [ ] Contains last 24h of data

[ ] Offline detection
    - [ ] Shows cached data when offline
    - [ ] Banner: "📴 Offline - 2h old data"
    - [ ] Cards dimmed/opacity reduced

[ ] Reconnect sync
    - [ ] Detects when online
    - [ ] Fetches new data
    - [ ] Syncs in < 5s
    - [ ] Smooth fade transition

[ ] No data loss
    - [ ] During offline: read-only mode
    - [ ] On reconnect: no conflicts
    - [ ] Data matches server 100%

TC Passing: ______ / 8 | Sign-off Date: ______ | QA: _________
```

### Sign-off Sprint 4
```
✓ FEATURE-004: Tarifas PASSED
✓ FEATURE-005: Alerts PASSED
✓ FEATURE-006: Dark Mode PASSED
✓ FEATURE-008: Offline PASSED

Date: ______ | Dev Lead: _____________ | QA Lead: ________
```

---

## SPRINT 5: RESPONSIVE & QA (Semana 5)

### FEATURE-009: Responsive Design

```
[ ] Desktop (1920px)
    - [ ] 4 cards per row
    - [ ] 2 rows
    - [ ] 24px gutter
    - [ ] No horizontal scroll

[ ] Tablet (768-1024px)
    - [ ] 2 cards per row
    - [ ] 3 rows
    - [ ] 16px gutter
    - [ ] Table has horizontal scroll

[ ] Mobile (<768px)
    - [ ] 1 card per row
    - [ ] Full width minus 16px padding
    - [ ] Text wraps (no truncate)
    - [ ] Charts 200px height

[ ] Touch-friendly
    - [ ] Buttons >= 44x44px
    - [ ] Spacing >= 8px
    - [ ] Tap feedback visible
    - [ ] Font >= 16px (no zoom)

[ ] Orientation changes
    - [ ] Portrait → Landscape: smooth
    - [ ] No content loss
    - [ ] No horizontal scroll

[ ] Lighthouse Mobile
    - [ ] Score >= 90
    - [ ] Performance >= 85
    - [ ] Accessibility >= 90

TC Passing: ______ / 7 | Sign-off Date: ______ | QA: _________
```

### Performance Testing

```
[ ] Load Time
    - [ ] LCP < 1.5s (target)
    - [ ] Measured: ______ ms (date: ______)
    - [ ] ✓ PASSED or [ ] FAILED

[ ] Interactivity
    - [ ] FID < 100ms
    - [ ] CLS < 0.1
    - [ ] Measured: ______ ms

[ ] Real-time Sync
    - [ ] P95 latency < 500ms
    - [ ] Tested with 20 orders
    - [ ] Actual: ______ ms
    - [ ] ✓ PASSED or [ ] FAILED

[ ] Memory
    - [ ] Initial: ______ MB
    - [ ] After 1h: ______ MB
    - [ ] Delta: ______ MB (should be < 5)
    - [ ] ✓ No leaks or [ ] Found leaks

[ ] Load Test (100 updates/s)
    - [ ] Error rate < 0.5%
    - [ ] P95 < 500ms
    - [ ] No timeouts
    - [ ] Memory stable
    - [ ] CPU < 80%
    - [ ] ✓ PASSED or [ ] FAILED
```

### QA Sign-off

```
FEATURE TESTING:
[ ] FEATURE-001: KPI Cards ........................... PASSED
[ ] FEATURE-002: Breakdown ........................... PASSED
[ ] FEATURE-003: Timeline ............................ PASSED
[ ] FEATURE-004: Tarifas ............................. PASSED
[ ] FEATURE-005: Alerts .............................. PASSED
[ ] FEATURE-006: Dark Mode ........................... PASSED
[ ] FEATURE-007: Real-time Sync ..................... PASSED
[ ] FEATURE-008: Offline Support .................... PASSED
[ ] FEATURE-009: Responsive Design .................. PASSED

CROSS-FEATURE TESTS:
[ ] End-to-end user flow ............................. PASSED
[ ] API integration (5 marketplaces) ................ PASSED
[ ] WebSocket + offline combo ........................ PASSED

PERFORMANCE:
[ ] Load time < 1.5s (LCP) ........................... PASSED
[ ] Interactivity < 100ms (FID) ..................... PASSED
[ ] Layout shift < 0.1 (CLS) ......................... PASSED
[ ] Sync latency < 500ms (P95) ...................... PASSED
[ ] Load test 100 updates/s .......................... PASSED

SECURITY & COMPLIANCE:
[ ] LGPD compliance (PII protection) ................ OK
[ ] Auth (vendor sees only own data) ............... OK
[ ] TLS 1.2+ ........................................ OK
[ ] No XSS vulnerabilities ........................... OK
[ ] No SQL injection vulnerabilities ................ OK
[ ] Secrets not in code .............................. OK

ACCESSIBILITY:
[ ] Lighthouse a11y score >= 90 ..................... SCORE: ______
[ ] ARIA labels on all interactive elements ........ OK
[ ] Keyboard navigation working ..................... OK
[ ] Screen reader compatible ......................... OK

ALL SYSTEMS GO FOR PRODUCTION ✅
```

---

## FINAL SIGN-OFF

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  DASHBOARD APPLE MVP - DEVELOPMENT COMPLETE                  ║
║                                                               ║
║  Feature Status:    9/9 PASSED ✅                             ║
║  Test Status:       65/65 Test Cases PASSED ✅                ║
║  Performance:       All targets MET ✅                        ║
║  Security:          Audit PASSED ✅                           ║
║  QA Approval:       ________________ (QA Lead Signature)     ║
║  Dev Lead Approval: ________________ (Dev Lead Signature)     ║
║  Product Approval:  ________________ (Product Owner Sig.)    ║
║                                                               ║
║  GO-LIVE DATE: ________________                              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## QUICK REFERENCE

### Feature Checklist at a Glance
```
P0 OBRIGATÓRIOS:
├─ [ ] FEATURE-001 (KPI Cards)
├─ [ ] FEATURE-002 (Breakdown)
├─ [ ] FEATURE-003 (Timeline)
├─ [ ] FEATURE-004 (Tarifas)
├─ [ ] FEATURE-005 (Alerts)
├─ [ ] FEATURE-006 (Dark Mode)
├─ [ ] FEATURE-007 (Real-time)
├─ [ ] FEATURE-008 (Offline)
└─ [ ] FEATURE-009 (Responsive)

P1 (POST-MVP):
└─ [ ] FEATURE-010 (Export)
```

### Success Criteria at a Glance
```
PERFORMANCE:
├─ [ ] LCP < 1.5s
├─ [ ] FID < 100ms
├─ [ ] CLS < 0.1
├─ [ ] Sync latency < 500ms (P95)
└─ [ ] Load test 100 updates/s: PASSED

QUALITY:
├─ [ ] All 65 test cases: PASSED
├─ [ ] Lighthouse >= 90 (desktop)
├─ [ ] Lighthouse >= 90 (mobile)
├─ [ ] 0 critical bugs
├─ [ ] 0 security vulnerabilities
└─ [ ] LGPD compliance: OK

GO-LIVE:
├─ [ ] Monitoring setup (DataDog/Sentry)
├─ [ ] Backup & restore tested
├─ [ ] Runbook documented
├─ [ ] Team trained
└─ [ ] Stakeholders notified
```

---

**PRINTABLE-CHECKLIST v1.0.0**
*Dashboard Apple MVP - Use during development*

Print this, check boxes as you go, send photo when done! 📋✅

