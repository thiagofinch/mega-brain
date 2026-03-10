# PRD-DASHBOARD-APPLE - EXECUTIVE SUMMARY
## Checklist & Quick Reference

**Versão:** 1.0.0 | **Data:** 2026-03-06 | **Status:** APROVADO PARA DEV

---

## VISÃO GERAL (30 segundos)

Dashboard premium mostrando vendas ao vivo + tarifas de marketplace. Real-time sync (<500ms), dark mode automático, offline support (24h cache). MVP com 5 marketplaces (ML, TikTok, Shopee, Amazon, Magalu) + 10 features core.

**Target:** Visibilidade completa do vendedor sobre revenue, margem e comissões em um painel.

---

## CHECKLIST RÁPIDO PARA DEV & QA

### Antes de Começar
- [ ] Ler PRD-DASHBOARD-APPLE.md completo (seções 1-5)
- [ ] Revisar data requirements (schema em seção 3.1)
- [ ] Confirmar acesso a APIs: ML, TikTok, Shopee, Amazon, Magalu
- [ ] Setup PostgreSQL + Redis
- [ ] Criar database schema (usar script em 3.1)

### Sprints

**Sprint 1 (Setup & API):**
- [ ] Database schema criado + migrado
- [ ] Redis setup e configurado
- [ ] ML API integration (usar MCP existente)
- [ ] TikTok API OAuth + orders endpoint
- [ ] Agregador Lambda: coleta dados a cada 5 min

**Sprint 2 (Mais APIs):**
- [ ] Shopee API OAuth + orders endpoint
- [ ] Amazon SP-API + auth
- [ ] Magalu API + auth
- [ ] Agregador: sincroniza todos 5 marketplaces

**Sprint 3 (Frontend - P0):**
- [ ] FEATURE-001: KPI cards (TVR, Margin, Commission, Sales, AOV, Return)
- [ ] FEATURE-007: Real-time sync (WebSocket < 500ms)
- [ ] FEATURE-002: Marketplace breakdown table
- [ ] FEATURE-003: Timeline charts (revenue, commission, margin)

**Sprint 4 (Frontend - Core Features):**
- [ ] FEATURE-004: Tarifas breakdown + simulador
- [ ] FEATURE-005: Alert system (margin, comissão, offline, sync error)
- [ ] FEATURE-006: Dark mode (auto + manual toggle)
- [ ] FEATURE-008: Offline support (Service Worker + IndexedDB)

**Sprint 5 (Polish & QA):**
- [ ] FEATURE-009: Responsive design (desktop/tablet/mobile)
- [ ] FEATURE-010: Export CSV/PDF (P1, nice-to-have)
- [ ] Testes: unit + integration + E2E
- [ ] Load testing: 100 updates/s, < 500ms latência
- [ ] QA: validar todos acceptance criteria

---

## FEATURES OBRIGATÓRIAS (P0)

| Feature | Prioridade | Status |
|---------|-----------|--------|
| FEATURE-001: KPI Cards | P0 | Development |
| FEATURE-002: Breakdown View | P0 | Development |
| FEATURE-003: Timeline Charts | P0 | Development |
| FEATURE-004: Tarifas | P0 | Development |
| FEATURE-005: Alerts | P0 | Development |
| FEATURE-006: Dark Mode | P0 | Development |
| FEATURE-007: Real-time Sync | P0 | Development |
| FEATURE-008: Offline Support | P0 | Development |
| FEATURE-009: Responsive | P0 | Development |
| FEATURE-010: Export (CSV/PDF) | P1 | Post-MVP |

---

## MARKETPLACES CONFIRMADOS

| Marketplace | P0 | API | Status |
|-------------|----|----|--------|
| Mercado Livre | ✅ | Sim (MCP) | Usar MCP existente |
| TikTok Shop | ✅ | Sim (OAuth) | Implementar novo |
| Shopee | ✅ | Sim (OAuth) | Implementar novo |
| Amazon BR | ✅ | Sim (SP-API) | Implementar novo |
| Magalu | ✅ | Sim (API Key) | Implementar novo |

---

## MÉTRICAS KPI (6 PRINCIPAIS)

### 1. Total Vendor Revenue (TVR)
- **Fórmula:** SUM(revenue de todos marketplaces)
- **Origem:** APIs de pedidos (status = completed)
- **Update:** 5 minutos
- **AC:** Soma bate com APIs, ±0.1% tolerance

### 2. Net Margin % (NM%)
- **Fórmula:** (TVR - Comissões) / TVR * 100
- **Thresholds:** Verde >20%, Amber 15-20%, Vermelho <15%
- **Alert:** Dispara quando < 15%
- **AC:** Bate com spreadsheet de auditoria (50 pedidos sample)

### 3. Comissões Pagas (CP)
- **Fórmula:** SUM(comissão de cada marketplace)
- **Por marketplace:** ML 16.5%, TikTok 5%, Shopee 5.3%, Amazon 8.5%, Magalu 5%
- **Alert:** Se > 25% em um marketplace
- **AC:** Soma dos marketplaces = total ±0.01 tolerance

### 4. Sales Last 24h (SL24)
- **Fórmula:** COUNT(pedidos completados últimas 24h)
- **Trending:** vs 24h anterior (% change)
- **Update:** Real-time quando novo pedido entra
- **AC:** Contagem exata per API

### 5. Average Order Value (AOV)
- **Fórmula:** TVR / SL24
- **Por marketplace:** mostrar breakdown
- **Trending:** vs 7d média
- **AC:** Bate com TVR / count manual

### 6. Return Rate (RR%)
- **Fórmula:** COUNT(devoluções) / COUNT(pedidos totais) * 100
- **Thresholds:** Verde <2%, Amber 2-5%, Vermelho >5%
- **Trending:** 7d SMA
- **AC:** Contagem correta de devoluções per API

---

## ACCEPTANCE CRITERIA SUMMARY

### Que deve passar na QA

```
FEATURE-001 KPI Cards:
✓ Valores corretos (TVR, Margin, Commission, Sales, AOV, Return)
✓ Trending funciona (↑/↓ com % change)
✓ Breakdown soma = 100%
✓ Updates < 500ms após novo pedido
✓ Accessibility: Lighthouse >= 90, ARIA labels, keyboard nav

FEATURE-007 Real-time Sync:
✓ WebSocket latência < 500ms (P95)
✓ Update cascade: novo pedido → DB → broadcast → frontend < 500ms
✓ Retry automático com exponential backoff
✓ Optimistic updates com loading state

FEATURE-008 Offline:
✓ Service Worker registrado
✓ IndexedDB com últimas 24h de dados
✓ Stale state banner quando offline
✓ Sync automático ao reconectar
✓ Sem dados perdidos

FEATURE-009 Responsive:
✓ Desktop 1920px: 4 cols layout
✓ Tablet 768-1024: 2 cols layout
✓ Mobile <768: 1 col stack
✓ Touch targets >= 44x44px
✓ Lighthouse mobile score >= 90

FEATURE-006 Dark Mode:
✓ Auto detect system preference
✓ Manual toggle em settings
✓ Persist em localStorage
✓ Color contrast >= 4.5:1 WCAG AA
✓ Smooth 0.3s transition

FEATURE-004 Tarifas:
✓ Tarifas corretas per API (validar com 20 pedidos)
✓ Simulador calcula corretamente (10 cenários test)
✓ Override temporário funciona
✓ Last updated timestamp reflete sync

FEATURE-005 Alerts:
✓ Margin < 15%: dispara vermelho
✓ Commission > 25%: dispara amber
✓ Offline: banner com timestamp
✓ API down: red status badge
✓ Dismiss & snooze 1h funciona
```

---

## DATA SCHEMA (RÁPIDO)

### Tabelas Principais
```sql
daily_metrics (date, marketplace, tvr, order_count, return_count, commission_total)
hourly_metrics (date, hour, marketplace, tvr_incremental, order_count)
raw_orders (order_id, marketplace, amount, commission, status, return_date)
marketplace_tariffs (marketplace, commission_base%, ti%, freight%, effective_date)
sync_logs (marketplace, sync_type, status, records_processed, duration_ms)
```

### Redis Cache Keys
```
dashboard:tvr:24h:all → R$ 45.230,50 | TTL 5 min
dashboard:margin:24h:all → 18.5% | TTL 5 min
dashboard:breakdown:{marketplace} → JSON | TTL 5 min
```

---

## SUCCESS METRICS (MEASURABLE)

| Métrica | Target | Como Medir |
|---------|--------|-----------|
| Load time (LCP) | < 1.5s | Lighthouse + RUM |
| Interactivity (FID) | < 100ms | Chrome Analytics |
| Sync latency (P95) | < 500ms | Backend logs |
| Data accuracy | > 99.5% | Audit scripts vs APIs |
| Uptime | 99.9% | StatusPage |
| Data freshness | < 5 min | Timestamp comparison |

---

## CONSTRAINTS CRÍTICOS

```
TÉCNICOS:
├─ Browser: Chrome, Safari, Firefox (últimas 2 versões)
├─ Mobile: iOS 14+, Android 10+
├─ DB: PostgreSQL 14+
├─ Real-time: WebSocket < 500ms latência
├─ Offline cache: máximo 24h, 50MB max
└─ Rate limits: variam por marketplace (ML 100/min, TikTok 1000/day, etc)

NEGÓCIOS:
├─ Timeline: 4 semanas MVP
├─ Budget: $50K dev + integração
├─ Team: 1 fullstack + 1 QA
├─ Dados: 30 dias histórico (não lifetime)
└─ Dark mode & Export: nice-to-have (P1)
```

---

## ROADMAP PÓS-MVP

**v1.1:** Export CSV/PDF, advanced filtering, email alerts, settings
**v1.2:** Predictive analytics, benchmarking, drill-down por categoria, histórico > 30d
**v2.0:** Multi-currency, multi-user, mobile app, COGS integration, API pública

---

## SIGN-OFF CHECKLIST

**Antes de passar para DEV:**
- [ ] PRD revisado e aprovado (FINAL)
- [ ] Marketplaces confirmados (5 principais)
- [ ] API access obtido (teste OAuth flows)
- [ ] Database schema revisado
- [ ] Arquitetura validada (Redis, PostgreSQL, WebSocket)
- [ ] Estimativa de esforço: 4 sprints = ~4 semanas

**Antes de QA:**
- [ ] Todas features implementadas
- [ ] Todas acceptance criteria testadas
- [ ] Performance benchmarks atingidos
- [ ] Load testing passou (100 updates/s)
- [ ] Accessibility validado (Lighthouse >= 90)

**Go-Live:**
- [ ] Monitoring setup (DataDog, Sentry)
- [ ] Runbook de deployment
- [ ] Backup strategy
- [ ] Support documentation
- [ ] User training/onboarding

---

## ARQUIVOS RELACIONADOS

| Arquivo | Propósito |
|---------|-----------|
| PRD-DASHBOARD-APPLE.md | PRD completa (10 seções) |
| PRD-DASHBOARD-APPLE-SUMMARY.md | Este arquivo (quick ref) |
| (Futuro) DASHBOARD-APPLE-STYLE-BRIEF.md | Design system / visual guidelines |
| (Futuro) DASHBOARD-APPLE-API-CONTRACTS.md | API request/response specs |
| (Futuro) DASHBOARD-APPLE-TEST-PLAN.md | Estratégia de testes |

---

## CONTATOS & REFERÊNCIAS

**Product Owner:** Thiago Finch
**Eng Lead:** [TBD]
**QA Lead:** [TBD]

**Marketplace API Docs:**
- ML: https://developers.mercadolivre.com.br/
- TikTok: https://developers.tiktok.com/doc/shop-api/
- Shopee: https://open.shopee.com.br/
- Amazon: https://developer.amazonservices.com/
- Magalu: [internal wiki]

---

**PRD v1.0.0 FINAL - Ready for Development**
*Last updated: 2026-03-06 | Generated by JARVIS*

