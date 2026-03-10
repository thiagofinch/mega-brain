# Architecture - Mega Brain

**System Architecture Documentation**
**Last Updated:** 2026-03-06

---

## Overview

Mega Brain is a two-part system:
1. **Knowledge Processing Engine** - AI pipeline for extracting and structuring expert knowledge
2. **Analytics Dashboard** - Next.js frontend for real-time business intelligence

---

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         MEGA BRAIN SYSTEM                                  │
├──────────────────────────────┬─────────────────────────────────────────────┤
│   KNOWLEDGE ENGINE (Core)    │   ANALYTICS DASHBOARD (Frontend)           │
│   ─────────────────────────  │   ─────────────────────────────────────────  │
│                              │                                             │
│   core/                      │   frontend/                                 │
│   ├── intelligence/          │   ├── app/                                  │
│   ├── workflows/             │   │   ├── api/         (REST endpoints)    │
│   ├── patterns/              │   │   ├── components/  (UI components)     │
│   ├── schemas/               │   │   └── hooks/       (React hooks)       │
│   ├── tasks/                 │   ├── lib/                                  │
│   └── templates/             │   │   ├── validation.ts                    │
│                              │   │   └── security.ts                      │
│   agents/                    │   ├── middleware.ts    (Security layer)     │
│   ├── conclave/              │   └── next.config.js   (Config)            │
│   ├── cargo/                 │                                             │
│   └── persons/               │                                             │
│                              │                                             │
├──────────────────────────────┴─────────────────────────────────────────────┤
│                      SHARED INFRASTRUCTURE                                 │
│   Redis (rate limiting) | PostgreSQL | CDN/Cloudflare | Monitoring         │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Next.js | 16.1.6+ | SSR/SSG/API routes |
| Language | TypeScript | 5.3.0+ | Type safety |
| UI | React | 18.2.0+ | Component model |
| Styling | Tailwind CSS | 3.3.0+ | Utility-first CSS |
| Charts | Recharts | 2.10.0+ | Data visualization |
| Animation | Framer Motion | 10.16.4+ | Smooth transitions |
| Data fetching | SWR | 2.2.0+ | Stale-while-revalidate |
| HTTP client | Axios | 1.6.0+ | API requests |
| Validation | Zod | 3.22.0+ | Schema validation |
| Rate limiting | rate-limiter-flexible | 3.0.0+ | API protection |

### Directory Structure

```
frontend/
├── app/
│   ├── api/
│   │   ├── health/
│   │   │   └── route.ts         # Health check endpoint
│   │   ├── sales/
│   │   │   └── route.ts         # Sales data endpoint
│   │   └── tarifas/
│   │       └── route.ts         # Tariff data endpoint
│   ├── components/
│   │   ├── Header.tsx            # Navigation component
│   │   └── Button.tsx            # Reusable button
│   ├── hooks/
│   │   ├── useApi.ts             # Generic API hook
│   │   ├── useSales.ts           # Sales data hook
│   │   ├── useTariffs.ts         # Tariff data hook
│   │   ├── useTheme.ts           # Theme management
│   │   ├── useWebSocket.ts       # WebSocket hook
│   │   └── index.ts              # Hook exports
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Main dashboard page
├── lib/
│   ├── types.ts                  # TypeScript types
│   ├── validation.ts             # Input validation
│   └── security.ts               # Security utilities
├── middleware.ts                  # Security middleware
├── next.config.js                # Next.js configuration
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
└── tailwind.config.ts            # Tailwind config
```

### API Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │                 CLIENT REQUEST                       │
                    └─────────────────────────────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │              middleware.ts                           │
                    │                                                     │
                    │  1. Rate Limiting (100 req/min per IP)              │
                    │  2. CSP nonce generation                            │
                    │  3. CORS validation                                 │
                    │  4. CSRF token validation (POST/PUT/DELETE)         │
                    │  5. Security headers                                │
                    └─────────────────────────────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │              API Route Handler                      │
                    │                                                     │
                    │  1. Input validation (lib/validation.ts)            │
                    │  2. Authentication check (if required)              │
                    │  3. Business logic                                  │
                    │  4. Error handling                                  │
                    │  5. Response formatting                             │
                    └─────────────────────────────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                  RESPONSE                           │
                    │                                                     │
                    │  - Security headers included                        │
                    │  - Rate limit headers included                      │
                    │  - Nonce included for CSP                          │
                    └─────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: CDN/WAF (Cloudflare)                                               │
│   - DDoS protection                                                         │
│   - WAF rules                                                               │
│   - Rate limiting at edge                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: TLS/HTTPS                                                          │
│   - TLS 1.3 minimum                                                         │
│   - HSTS with preload                                                       │
│   - Certificate auto-renewal                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: Application Security Headers                                       │
│   - CSP (no unsafe-inline, no unsafe-eval)                                  │
│   - X-Frame-Options: DENY                                                   │
│   - Permissions-Policy restrictive                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: Rate Limiting                                                      │
│   - 100 requests/minute per IP                                              │
│   - Redis-backed sliding window                                             │
│   - Exponential backoff for violations                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: Request Validation                                                 │
│   - CSRF token validation (POST/PUT/PATCH/DELETE)                           │
│   - CORS origin whitelist                                                   │
│   - Input validation schemas                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: Authentication & Authorization                                     │
│   - Bearer token validation                                                 │
│   - Route-level authorization guards                                        │
│   - Least privilege principle                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Security Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `middleware.ts` | `frontend/` | Rate limiting, CSP, CORS, CSRF |
| `lib/validation.ts` | `frontend/lib/` | Input validation schemas |
| `lib/security.ts` | `frontend/lib/` | Security utilities |
| `.gitleaks.toml` | Root | Secret detection config |
| `security-audit.md` | Root | Security findings |

### Content Security Policy

**Policy:**
```
default-src 'self'
script-src 'self' 'nonce-{random}'
style-src 'self'
img-src 'self' data: https: blob:
font-src 'self' data:
connect-src 'self' https: wss:
frame-ancestors 'none'
base-uri 'self'
form-action 'self'
report-uri {CSP_REPORT_URI}
```

**Design Decisions:**
- No `unsafe-inline` - prevents XSS through inline event handlers
- No `unsafe-eval` - prevents arbitrary code execution
- Nonce-based approach for dynamic scripts (better than hash-based)
- `frame-ancestors 'none'` - prevents clickjacking
- CSP violations reported to backend for monitoring

---

## Data Flow Architecture

### Sales Dashboard

```
Mercado Livre API
       │
       ▼
ML MCP Server (Python)
       │
       ▼
Backend (Python/FastAPI)    ←→    Redis Cache (5min TTL)
       │
       ▼
/api/sales (Next.js)
       │
       ▼
Dashboard (React/Recharts)
```

### Tariff Data

```
Mercado Livre Tariff API
       │
       ▼
ML MCP Server
       │
       ▼
/api/tarifas (Next.js)
       │
       ▼
Tariff Display Components
```

---

## Knowledge Engine Architecture

### Pipeline Phases

```
PHASE 1: DOWNLOAD
   Input: Google Drive links / manual uploads
   Output: Raw files in /inbox/

PHASE 2: ORGANIZATION
   Input: /inbox/ files
   Output: Organized, tagged files

PHASE 3: DE-PARA (Source Mapping)
   Input: Organized files + control spreadsheet
   Output: Verified mapping

PHASE 4: PIPELINE
   Input: Organized files
   Process: Chunking → Extraction → Insight generation
   Output: Batches in /logs/batches/

PHASE 5: AGENTS
   Input: Processed batches
   Process: DNA synthesis → Agent creation
   Output: PERSON agents + CARGO agents + Theme dossiers
```

### Agent Architecture

```
/agents/
├── AGENT-INDEX.yaml              # Registry of all agents
├── conclave/                     # Council system (multi-agent)
│   └── CONCLAVE-PROTOCOL.md
├── cargo/                        # Role-based agents
│   ├── C-LEVEL/
│   │   ├── CFO/
│   │   │   ├── AGENT.md          # Role definition
│   │   │   ├── SOUL.md           # Personality
│   │   │   ├── MEMORY.md         # Experiential memory
│   │   │   └── DNA-CONFIG.yaml   # Knowledge sources
│   │   └── CRO/
│   └── SALES/
│       └── CLOSER/
└── persons/                      # Expert mind clones
    └── {EXPERT_NAME}/
        ├── AGENT.md
        ├── SOUL.md
        ├── MEMORY.md
        └── DNA-CONFIG.yaml
```

---

## Infrastructure

### Production Infrastructure

```
Internet
   │
   ▼
Cloudflare CDN/WAF/DDoS
   │
   ▼
Load Balancer
   │
   ├── Frontend (Next.js) Container
   │   Port 3000
   │
   ├── Redis Cache
   │   Port 6379 (TLS)
   │
   └── PostgreSQL Database
       Port 5432 (TLS)
```

### Environment Configuration

| Environment | Frontend | API | Database |
|-------------|----------|-----|---------|
| Development | localhost:3000 | localhost:3001 | localhost:5432 |
| Staging | staging.domain.com | api-staging.domain.com | db-staging |
| Production | domain.com | api.domain.com | db.internal |

---

## Monitoring Architecture

### Observability Stack

```
Application Logs          Performance Metrics        Error Tracking
      │                         │                          │
      ▼                         ▼                          ▼
   Splunk /              DataDog / New Relic           Sentry
   CloudWatch            (p50, p95, p99)           (stack traces)
      │                         │                          │
      └─────────────────────────┴──────────────────────────┘
                                │
                          Alert Manager
                    (PagerDuty / Slack alerts)
```

### Key Metrics

| Category | Metric | Alert Threshold |
|----------|--------|----------------|
| Performance | API response time p95 | > 1000ms |
| Errors | Error rate | > 1% |
| Security | CSP violations | Any |
| Security | Auth failures | > 50/hour |
| Security | Rate limit hits | > 100/hour |
| Infrastructure | CPU | > 80% |
| Infrastructure | Memory | > 85% |
| Infrastructure | Disk | < 10% free |

---

## Security Architecture Review

### Completed (v1.0)

- CSRF protection on all state-changing operations
- Rate limiting (100 req/min per IP)
- CSP headers hardened (no unsafe-inline)
- CORS whitelist configured
- Input validation on all endpoints
- Gitleaks secret detection configured
- HSTS enabled for production

### Planned (v1.1)

- JWT-based authentication
- Role-Based Access Control (RBAC)
- Audit logging (who did what, when)
- Secrets Manager integration (AWS/GCP)
- Automated security scanning in CI/CD
- Security monitoring dashboard

---

**Last Updated:** 2026-03-06
**Version:** 1.0.0
**Status:** Production Ready (pending dependency upgrade)
