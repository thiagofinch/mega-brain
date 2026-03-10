# INDEX: PRD Dashboard Apple
## Guia de Navegação Completo

**Criado:** 2026-03-06 | **Status:** FINAL PARA DESENVOLVIMENTO

---

## DOCUMENTOS ENTREGUES

### 1. PRD-DASHBOARD-APPLE.md (COMPLETO)
**Local:** `/docs/prd/PRD-DASHBOARD-APPLE.md`
**Tamanho:** ~15 KB | **Seções:** 10 principais + apêndices

Especificação completa do produto com:
- Escopo MVP (10 features P0/P1)
- 6 métricas KPI detalhadas (fórmulas, cálculos, thresholds)
- Data requirements (schema PostgreSQL, Redis cache)
- Integration dependencies (APIs de 5 marketplaces)
- Acceptance criteria para cada feature (testável, quantificável)
- Success metrics & KPIs de negócio
- Constraints & assumptions
- Roadmap pós-MVP (v1.1, v1.2, v2.0)
- Apêndices: arquitetura, API contracts, sync workflow

**Para quem:** Developers, Product Manager, Tech Lead
**Quando ler:** ANTES de qualquer implementação

---

### 2. PRD-DASHBOARD-APPLE-SUMMARY.md (QUICK REFERENCE)
**Local:** `/docs/prd/PRD-DASHBOARD-APPLE-SUMMARY.md`
**Tamanho:** ~3 KB | **Propósito:** Resumo executivo

Guia rápido para liderança & daily standups:
- Visão geral 30 segundos
- Checklist rápido (setup, sprints, features)
- 5 marketplaces confirmados
- 6 métricas KPI em uma página
- Acceptance criteria resumido
- Success metrics & constraints
- Roadmap pós-MVP
- Contatos & referências

**Para quem:** Dev Lead, QA Lead, Product Manager
**Quando usar:** Daily standups, quick lookups, team briefing

---

### 3. PRD-DASHBOARD-APPLE-QA-CHECKLIST.md (TESTE COMPLETO)
**Local:** `/docs/prd/PRD-DASHBOARD-APPLE-QA-CHECKLIST.md`
**Tamanho:** ~12 KB | **Seções:** 10 features + integration + load test

Plano de teste executável com:
- Test cases por feature (TC-XXX-YYY format)
- Acceptance criteria testável (checkboxes)
- Performance benchmarks
- Edge cases & error scenarios
- Security & compliance checklist
- Deployment checklist
- Load test template (100 updates/s)
- Final sign-off (QA, Dev, Product)

**Para quem:** QA Engineer, Test Lead
**Quando usar:** Development & QA phases

---

### 4. INDEX-PRD-DASHBOARD-APPLE.md (ESTE ARQUIVO)
**Local:** `/docs/prd/INDEX-PRD-DASHBOARD-APPLE.md`
**Propósito:** Navegação & referência cruzada

---

## NAVIGAÇÃO RÁPIDA

### Por Papel

**👨‍💼 Product Manager**
1. Ler: SUMMARY (3 min)
2. Ler: Seção 1 (Escopo) de PRD-COMPLETO (5 min)
3. Ler: Success Metrics (10 min)

**👨‍💻 Desenvolvedor**
1. Ler: SUMMARY (5 min)
2. Ler: Seção 3 (Data Requirements) de PRD-COMPLETO (20 min)
3. Ler: Seção 4 (Integration) de PRD-COMPLETO (15 min)
4. Implementar features in order (Sprints 1-5)

**🧪 QA Engineer**
1. Ler: QA-CHECKLIST complete (30 min)
2. Ler: Seção 5 (Acceptance Criteria) de PRD-COMPLETO (20 min)
3. Executar test cases durante development & QA phases

**📊 Tech Lead**
1. Ler: SUMMARY (5 min)
2. Ler: Seção 4 (Integration) de PRD-COMPLETO (15 min)
3. Ler: Apêndice A (Architecture) de PRD-COMPLETO (10 min)
4. Garantir alinhamento com arquitetura existente

---

### Por Fase do Projeto

#### SETUP (Semana 0)
- Ler: SUMMARY (visão geral)
- Ler: Seção 3 (Data Requirements)
- Ler: Seção 4 (Integration Dependencies)
- Ação: Setup PostgreSQL, Redis, APIs

#### DESENVOLVIMENTO (Semanas 1-4)
- Consultar: PRD-COMPLETO (cada feature)
- Consultar: Seção 5 (Acceptance Criteria)
- Implementar: Features em order (Sprints 1-5)

#### QA & TESTES (Semanas 3-5)
- Usar: QA-CHECKLIST.md
- Validar: Cada test case (TC-XXX-YYY)
- Sign-off: Quando todos features passarem

#### DEPLOYMENT (Semana 5)
- Ler: Deploy checklist (QA-CHECKLIST seção final)
- Monitorar: Success metrics
- Post-deployment: Health checks

---

## TABELA DE CONTEÚDOS

### PRD-DASHBOARD-APPLE.md

| Seção | Conteúdo | Páginas |
|-------|----------|---------|
| **1** | Escopo MVP (10 features) | 1-3 |
| **2** | Métricas KPI (6 principais) | 4-8 |
| **3** | Data Requirements (schema, flow) | 9-11 |
| **4** | Integration Dependencies | 12-14 |
| **5** | Acceptance Criteria (10 features) | 15-30 |
| **6** | Success Metrics & KPIs | 31 |
| **7** | Constraints & Assumptions | 32 |
| **8** | Roadmap Pós-MVP | 33 |
| **9** | Definições & Glossário | 34 |
| **10** | Approval & Sign-off | 35 |
| **A** | Technical Architecture Diagram | 36 |
| **B** | API Sync Workflow | 37 |

---

## FEATURES & STATUS

```
┌────────────────────────────────┬──────────┬────────────┐
│ Feature                        │ Priority │ Status     │
├────────────────────────────────┼──────────┼────────────┤
│ FEATURE-001: KPI Cards         │ P0       │ Dev Phase  │
│ FEATURE-002: Breakdown View    │ P0       │ Dev Phase  │
│ FEATURE-003: Timeline Charts   │ P0       │ Dev Phase  │
│ FEATURE-004: Tarifas           │ P0       │ Dev Phase  │
│ FEATURE-005: Alert System      │ P0       │ Dev Phase  │
│ FEATURE-006: Dark Mode         │ P0       │ Dev Phase  │
│ FEATURE-007: Real-time Sync    │ P0       │ Dev Phase  │
│ FEATURE-008: Offline Support   │ P0       │ Dev Phase  │
│ FEATURE-009: Responsive Design │ P0       │ Dev Phase  │
│ FEATURE-010: Export & Reporting│ P1       │ Post-MVP   │
└────────────────────────────────┴──────────┴────────────┘

P0 = Obrigatório MVP (4 semanas)
P1 = Post-MVP (semana 5+)
```

---

## MÉTRICAS KPI (QUICK LOOKUP)

| KPI | Fórmula | Origem | Update | Threshold |
|-----|---------|--------|--------|-----------|
| **TVR** | SUM(revenue) | APIs | 5 min | - |
| **NM%** | (TVR - Comissões) / TVR | Calc | 5 min | >20% verde |
| **CP** | SUM(comissão) | Calc | 5 min | >25% alert |
| **SL24** | COUNT(pedidos 24h) | APIs | Real-time | - |
| **AOV** | TVR / SL24 | Calc | 5 min | - |
| **RR%** | COUNT(returns) / COUNT(pedidos) | APIs | 5 min | <2% verde |

---

## MARKETPLACES CONFIRMADOS

| Marketplace | API | Taxa | Incluir |
|-------------|-----|------|---------|
| Mercado Livre | /orders (MCP) | 16.5% | ✅ P0 |
| TikTok Shop | /shop/order_list | 5.0% | ✅ P0 |
| Shopee | /v2/order/orders_get | 5.3% | ✅ P0 |
| Amazon BR | /orders (SP-API) | 8.5% | ✅ P0 |
| Magalu | /orders | 5.0% | ✅ P0 |

---

## CHECKLIST RÁPIDO PARA DEVS

### Antes de começar
```
[ ] Ler SUMMARY.md (5 min)
[ ] Ler Seção 3 (Data) do PRD (20 min)
[ ] Ler Seção 4 (Integration) do PRD (15 min)
[ ] Clonar repo e setup environment
[ ] Criar PostgreSQL schema (use script em Seção 3.1)
[ ] Configurar Redis
[ ] Testar acesso às 5 APIs de marketplace
```

### Durante implementation
```
[ ] Ler Seção 5 (Acceptance Criteria) para cada feature
[ ] Testar unit tests
[ ] Validar com Acceptance Criteria checklist
[ ] Fazer PR com reference ao feature específico
```

### Antes de QA
```
[ ] Código reviewed & merged
[ ] Acceptance criteria checklist completo
[ ] Performance benchmarks testados
[ ] Documentação atualizada
```

---

## ACCEPTANCE CRITERIA CHECKLISTS

Cada feature tem detailed AC em 2 locais:

1. **PRD-COMPLETO (Seção 5):**
   - Descrição detalhada
   - Fórmulas & cálculos
   - Edge cases
   - Performance reqs

2. **QA-CHECKLIST:**
   - Test cases executáveis (TC-XXX-YYY)
   - Setup instructions
   - Steps to reproduce
   - Expected results

Exemplo: FEATURE-001 (KPI Cards)
- PRD: Seção 5.1, páginas 15-17
- QA: Test cases TC-001-001 a TC-001-035

---

## PERFORMANCE TARGETS

```
┌──────────────────────────┬────────┬─────────┐
│ Métrica                  │ Target │ Critical│
├──────────────────────────┼────────┼─────────┤
│ Page Load Time (LCP)     │ <1.5s  │ <2.5s   │
│ Time to Interactive (FID)│ <100ms │ <300ms  │
│ Layout Shift (CLS)       │ <0.1   │ <0.25   │
│ Sync Latency (P95)       │ <500ms │ <1000ms │
│ Data Accuracy            │ >99.5% │ >95%    │
│ Uptime                   │ 99.9%  │ 99%     │
└──────────────────────────┴────────┴─────────┘
```

---

## SPRINTS ROADMAP

```
SPRINT 1 (Setup & API):
├─ Database & Redis setup
├─ ML API (usar MCP existente)
├─ TikTok API OAuth + orders
└─ Agregador Lambda (5 min sync)

SPRINT 2 (Mais APIs):
├─ Shopee API
├─ Amazon SP-API
├─ Magalu API
└─ Agregador: sincroniza todos 5

SPRINT 3 (Frontend P0):
├─ FEATURE-001: KPI Cards
├─ FEATURE-007: Real-time Sync
├─ FEATURE-002: Breakdown
└─ FEATURE-003: Timeline Charts

SPRINT 4 (Core Features):
├─ FEATURE-004: Tarifas
├─ FEATURE-005: Alerts
├─ FEATURE-006: Dark Mode
└─ FEATURE-008: Offline Support

SPRINT 5 (Polish & QA):
├─ FEATURE-009: Responsive Design
├─ Tests & QA
├─ Load testing (100 updates/s)
├─ Deployment prep
└─ FEATURE-010 (P1): Export CSV/PDF
```

---

## CONTATOS & ESCALAÇÃO

| Função | Nome | Contato |
|--------|------|---------|
| Product Owner | Thiago Finch | [email] |
| Tech Lead | [TBD] | [email] |
| Dev Lead | [TBD] | [email] |
| QA Lead | [TBD] | [email] |

---

## REFERENCIAS & LINKS

**Marketplace APIs:**
- Mercado Livre: https://developers.mercadolivre.com.br/
- TikTok Shop: https://developers.tiktok.com/doc/shop-api/
- Shopee: https://open.shopee.com.br/
- Amazon SP-API: https://developer.amazonservices.com/
- Magalu: [internal wiki]

**Tools & Documentation:**
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/documentation
- Socket.io: https://socket.io/docs/
- Recharts: https://recharts.org/

**Design System:**
- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
- Dark Mode: https://developer.apple.com/design/human-interface-guidelines/macos/visual-design/dark-mode/

---

## VERSIONING

| Documento | Versão | Data | Mudanças |
|-----------|--------|------|----------|
| PRD-COMPLETO | 1.0.0 | 2026-03-06 | Criação inicial |
| SUMMARY | 1.0.0 | 2026-03-06 | Criação inicial |
| QA-CHECKLIST | 1.0.0 | 2026-03-06 | Criação inicial |
| INDEX | 1.0.0 | 2026-03-06 | Criação inicial |

---

## COMO USAR ESTE INDEX

1. **Primeira vez aqui?** → Ler SUMMARY.md
2. **Que é que devo implementar?** → Ver SPRINTS ROADMAP acima
3. **Como testo FEATURE-X?** → Buscar "FEATURE-00X" em QA-CHECKLIST
4. **Qual é a fórmula de [KPI]?** → Ver MÉTRICAS KPI QUICK LOOKUP
5. **Qual é o threshold para [alerta]?** → Ler Seção 5 de PRD-COMPLETO
6. **O dashboard offline funciona como?** → Ler FEATURE-008 AC em PRD-COMPLETO
7. **Como é a arquitetura?** → Ver Apêndice A de PRD-COMPLETO

---

## APPROVAL FINAL

```
✅ PRD-DASHBOARD-APPLE.md         FINAL PARA DESENVOLVIMENTO
✅ PRD-DASHBOARD-APPLE-SUMMARY.md FINAL PARA DESENVOLVIMENTO
✅ PRD-DASHBOARD-APPLE-QA-CHECKLIST.md FINAL PARA QA
✅ INDEX-PRD-DASHBOARD-APPLE.md   GUIA DE NAVEGAÇÃO

Status: PRONTO PARA DEV + QA INICIAREM TRABALHO

Data: 2026-03-06
Verificado por: JARVIS
```

---

**INDEX v1.0.0 | Dashboard Apple PRD Suite**
*Última atualização: 2026-03-06*

