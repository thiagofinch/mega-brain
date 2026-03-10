# PRD-DASHBOARD-APPLE.md
## Product Requirements Document - Dashboard Premium Vendas & Marketplaces

**Versão:** 1.0.0
**Data:** 2026-03-06
**Proprietário do Produto:** Thiago Finch
**Status:** FINAL PARA DESENVOLVIMENTO

---

## EXECUTIVE SUMMARY

Dashboard premium em tempo real consolidando vendas, tarifas e métricas financeiras across múltiplos marketplaces. Design Apple-inspired (minimalista, dark mode automático, precisão visual). Real-time sync (<500ms), offline support (24h cache), responsive design. MVP com 5 marketplaces principais + extensibilidade arquitetural.

**Objetivo:** Visibilidade completa e confiável do vendedor sobre revenue, margem e comissões em um único painel.

---

## 1. ESCOPO MVP (MÍNIMO VIÁVEL)

### 1.1 Marketplaces Inclusos (CONFIRMADO)

| Marketplace | Prioridade | API Disponível | Status |
|-------------|-----------|-----------------|--------|
| **Mercado Livre** | P0 | Sim (MCP existente) | Incluir |
| **TikTok Shop** | P0 | Sim (API v2) | Incluir |
| **Shopee** | P0 | Sim (OAuth) | Incluir |
| **Amazon BR** | P1 | Sim (SP-API) | Incluir |
| **Magalu** | P1 | Sim (REST API) | Incluir |

**Nota:** P0 = MVP obrigatório, P1 = MVP estendido (validar com time)

### 1.2 Funcionalidades Core

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-001: DASHBOARD HOME (Real-time KPI Cards)                           │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Card: Total Vendor Revenue (soma consolidada + breakdown por marketplace) │
│ ✓ Card: Net Margin % (margem líquida com trending)                          │
│ ✓ Card: Comissões Pagas (total + por marketplace)                           │
│ ✓ Card: Sales Last 24h (velocidade de venda)                                │
│ ✓ Card: Avg Order Value (AOV cross-marketplace)                             │
│ ✓ Card: Return Rate (RMA % agregado)                                        │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-002: MARKETPLACE BREAKDOWN VIEW                                     │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Tabela/Cards com metrics por marketplace (Revenue, Comissão, AOV, RR)     │
│ ✓ Sorting: por revenue (DESC default), comissão, margem                     │
│ ✓ Filtering: por status (ativo/inativo), período (24h/7d/30d)               │
│ ✓ Comparação visual (% contribution ao total)                                │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-003: TIMELINE / HISTÓRICO (24H últimas)                             │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Gráfico: Revenue por hora (sparkline estilo Apple)                        │
│ ✓ Gráfico: Comissões acumuladas (area chart com gradient)                   │
│ ✓ Gráfico: Margin trending (line chart com threshold visual)                │
│ ✓ Data agregada por marketplace (overlay ou tabs)                           │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-004: TARIFAS MARKETPLACE (Breakdown de Custos)                      │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Tabela: Comissão base %, Taxa TI, Taxa Frete, Outras taxas               │
│ ✓ Cálculo visual: Total % por marketplace + simulação "se vender R$X"      │
│ ✓ Lastpass: data última atualização (timestamp)                             │
│ ✓ Edição manual: permitir override temporário (para testes/projeção)       │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-005: ALERT SYSTEM (Warnings & Anomalies)                            │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Alert: Margin abaixo de 15% (threshold configurável)                      │
│ ✓ Alert: Comissão acima de 25% em um marketplace                            │
│ ✓ Alert: Sincronização offline (últimas 24h)                                │
│ ✓ Alert: API desconectada (red status visual)                               │
│ ✓ Dismiss/snooze: user can clear ou ignorar por 1h                          │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-006: DARK MODE (Apple-standard)                                     │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Auto: detect system preference (prefers-color-scheme)                     │
│ ✓ Manual toggle: user can override no settings                              │
│ ✓ Colors: uso de semantic colors (iOS-style)                                │
│ ✓ Persistence: salvar preference no localStorage                            │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-007: REAL-TIME SYNC (<500ms)                                        │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Websocket ou polling (100ms intervals, batched updates)                   │
│ ✓ Update cascade: atualizar cards → atualizar charts → atualizar tables     │
│ ✓ Optimistic updates: mostrar loading state durante sync                    │
│ ✓ Error handling: retry automático com exponential backoff                  │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-008: OFFLINE SUPPORT (24H Cache)                                    │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Service Worker + IndexedDB: cache última 24h de dados                    │
│ ✓ Stale state: mostrar "dados de XXh atrás" com visual indicator            │
│ ✓ Sync on reconnect: atualizar automaticamente ao voltar online             │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-009: RESPONSIVE DESIGN                                              │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Desktop (1920px+): 4-column layout com todos os cards visíveis            │
│ ✓ Tablet (768-1024px): 2-column layout, tabela com scroll horizontal       │
│ ✓ Mobile (< 768px): 1-column layout, cards stackados, charts scrolláveis   │
│ ✓ Touch-friendly: buttons >= 44x44px, spacing generoso                      │
│ Status: MÍNIMO P0                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FEATURE-010: EXPORT & REPORTING (Basic)                                     │
│ ─────────────────────────────────────────────────────────────────────────────│
│ ✓ Export CSV: tabela de breakdown + tarifas                                  │
│ ✓ Export PDF: snapshot do dashboard com timestamp                            │
│ ✓ Share link: gerar link compartilhável (read-only, 7 dias expiração)      │
│ Status: P1 (nice-to-have para MVP)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Total de Features MVP: 10 (8 P0 obrigatórias + 2 P1 estendidas)**

---

## 2. MÉTRICAS KPI (DEFINIÇÃO DETALHADA)

### 2.1 Total Vendor Revenue (TVR)

**Definição:** Soma consolidada de revenue from all marketplaces (gross sales before commissions)

```
FÓRMULA:
TVR = SUM(marketplace_revenue) for all active marketplaces
    = ML.revenue + TikTok.revenue + Shopee.revenue + Amazon.revenue + Magalu.revenue

ORIGEM DOS DADOS:
├─ Mercado Livre: API /orders/v2/orders com status "pagado" (últimas 24h)
├─ TikTok: API /shop/order_list (order status = completed_sale)
├─ Shopee: API /v2/order/orders_get (order status = 100, 110, 120)
├─ Amazon: SP-API /orders/v0/orders (order status = Shipped, Delivered)
└─ Magalu: API /orders (status = pago)

CÁLCULO:
├─ TVR 24h = sum revenue últimas 24h (real-time)
├─ TVR 7d = sum revenue últimos 7 dias (cache diário)
├─ TVR 30d = sum revenue últimos 30 dias (cache diário)

THRESHOLD & TRENDING:
├─ Trending: % change vs período anterior (24h-1: last 24h vs previous 24h)
├─ Visual: verde se crescimento, amber se flat, vermelho se decline
├─ Update frequency: 5 minutos (batch de APIs)

FORMATO NA UI:
├─ Primário: "R$ 45.230,50" (24h)
├─ Secondary: "+12.3% vs yesterday" (trending com seta)
├─ Breakdown: "ML: 40% | TikTok: 30% | Shopee: 20% | Amazon: 7% | Magalu: 3%"
```

**Acceptance Criteria:**
- [ ] Soma exata com calls de teste em sandbox de cada API
- [ ] Update dentro de 5 min após pedido ser marcado como "pagado"
- [ ] Trending calculation > que 90% accuracy vs manual audit
- [ ] Breakdown percentuals = 100% (±0.1% floating point tolerance)

---

### 2.2 Net Margin % (NM)

**Definição:** Margem líquida após todas as comissões e taxas

```
FÓRMULA:
NM% = (TVR - Total_Commissions) / TVR * 100

Onde:
├─ TVR = Total Vendor Revenue (definiçãp acima)
├─ Total_Commissions = SUM(comissões de todas marketplaces)
│   ├─ Comissão base: configurável por marketplace (padrão: ML 16.5%, TikTok 5%, Shopee 3%, Amazon 7%, Magalu 4%)
│   ├─ Taxa TI: 1-2% variável por marketplace
│   ├─ Taxa frete: para marketplaces que cobram (Shopee, Magalu)
│   └─ Descontos/promoções: subtrair do TVR se aplicável
│
└─ OUTROS CUSTOS (opcional para future roadmap):
    ├─ Custo do produto (COGS): se data disponível no backend
    ├─ Despesas operacionais: manual entry
    └─ Devoluções/chargebacks: trackear separadamente

CÁLCULO POR MARKETPLACE:
NM%_ML = (TVR_ML - (TVR_ML * comissão_ML)) / TVR_ML * 100
NM%_TikTok = (TVR_TikTok - (TVR_TikTok * comissão_TikTok)) / TVR_TikTok * 100
... (aplicar para todos)

AGREGADO:
NM%_Total = (TVR_Total - Total_Commissions_All) / TVR_Total * 100

THRESHOLD & ALERTS:
├─ VERMELHO: NM% < 15% (crítico - vendedor está perdendo dinheiro)
├─ AMBER: NM% 15-20% (margem apertada)
├─ VERDE: NM% > 20% (saudável)

TRENDING:
├─ Mostrar trending com linha no card (sparkline)
├─ Atualizar trending a cada 1h com média móvel de 4h
├─ Comparar: NM% 24h vs NM% 7d média
```

**Acceptance Criteria:**
- [ ] Cálculo bate com spreadsheet de auditoria (validar 50 pedidos sample)
- [ ] Threshold alerts funcionam em tempo real (margin queda <15% dispara alert)
- [ ] Trending mostra corretamente direction (↑/↓) com accuracy >95%
- [ ] Suporta override manual de comissão (para testes/projeção)

---

### 2.3 Comissões Pagas (CP)

**Definição:** Total de comissões cobradas por todas as marketplaces

```
FÓRMULA:
CP = SUM(comissão_marketplace) for all marketplaces
   = (TVR_ML * taxa_ML) + (TVR_TikTok * taxa_TikTok) + ... + (TVR_Magalu * taxa_Magalu)

Onde taxa inclui:
├─ Comissão base % (varia por marketplace)
├─ Taxa TI %
├─ Taxa frete (se aplicável)
└─ Outras taxas específicas do marketplace

DETALHE POR MARKETPLACE:
├─ ML: Comissão base 16.5% + taxa TI 0.5% + frete 0%
├─ TikTok: Comissão 5% + taxa plataforma 0%
├─ Shopee: Comissão 3% + taxa TI 1.5% + frete variável
├─ Amazon: Comissão 7% + taxa de referência (variable)
└─ Magalu: Comissão 4% + taxa plataforma 0.5% + frete variável

CÁLCULO:
├─ CP 24h = soma comissões últimas 24h
├─ CP 7d = soma comissões últimos 7 dias
├─ CP 30d = soma comissões últimos 30 dias
├─ CP% do TVR = CP / TVR * 100 (métrica de eficiência)

BREAKDOWN VISUAL:
├─ Card principal: "R$ 3.450,20" (24h)
├─ Secondary: "%  da revenue = 7.62%"
├─ Breakdown por marketplace: tabela com Marketplace | CP 24h | % contribution

TRENDING:
├─ Mostrar % change vs período anterior
├─ Flag se comissão > 25% em marketplace específico (anomalia)
```

**Acceptance Criteria:**
- [ ] Comissão calculada corretamente para cada pedido (verificar com 20 pedidos sample)
- [ ] Soma de CP de todos marketplaces = CP total (±0.01 rounding tolerance)
- [ ] Breakdown percentuals por marketplace = 100%
- [ ] Alert dispara quando CP% > 25% em marketplace (customizable threshold)

---

### 2.4 Sales Last 24h (SL24)

**Definição:** Número de pedidos completados nas últimas 24h

```
FÓRMULA:
SL24 = COUNT(pedidos com status = "completed" AND timestamp >= now() - 24h)

POR MARKETPLACE:
├─ ML: Contar orders com status = "pagado"
├─ TikTok: Contar orders com status = "completed_sale"
├─ Shopee: Contar orders com status = 100, 110, 120
├─ Amazon: Contar orders com status = Shipped, Delivered
└─ Magalu: Contar orders com status = "pago"

AGREGADO:
SL24_Total = SUM(SL24_per_marketplace)

CÁLCULO ADICIONAL:
├─ SL24 = 48 (24h)
├─ SL per hour = 48 / 24 = 2 pedidos/hora (média)
├─ SL por marketplace (breakdown%)
├─ Trending: SL24 vs SL24_yesterday (% change)

VISUAL NA UI:
├─ Primário: "48 pedidos" (24h)
├─ Secondary: "+8.5% vs yesterday" (seta verde se crescimento)
├─ Sparkline: pedidos por hora (últimas 24h)
├─ Breakdown: "ML: 20 | TikTok: 15 | Shopee: 10 | Amazon: 2 | Magalu: 1"
```

**Acceptance Criteria:**
- [ ] Contagem exata de pedidos per API (validar com raw API call)
- [ ] Update em tempo real quando novo pedido entra (< 5 min delay)
- [ ] Trending accuracy >95% (vs manual audit)
- [ ] Suporta filtro por status (todos os completados, delivery confirmado, etc)

---

### 2.5 Average Order Value (AOV)

**Definição:** Valor médio por pedido across all marketplaces

```
FÓRMULA:
AOV = TVR / SL24
    = Total Revenue / Número de Pedidos

POR MARKETPLACE:
AOV_ML = TVR_ML / SL24_ML
AOV_TikTok = TVR_TikTok / SL24_TikTok
... (aplicar para todos)

PERÍODO:
├─ AOV 24h = TVR 24h / SL24
├─ AOV 7d = TVR 7d / SL7d
├─ AOV 30d = TVR 30d / SL30d

CÁLCULO:
├─ TVR 24h = R$ 45.230,50
├─ SL24 = 48 pedidos
├─ AOV = R$ 45.230,50 / 48 = R$ 942,30

COMPARISON VISUAL:
├─ Primário: "R$ 942,30" (24h AOV)
├─ Secondary: "+5.2% vs yesterday"
├─ Benchmark: "ML avg: R$1.050 | TikTok: R$650 | ..."
├─ Trending: sparkline da média móvel (24h)

INSIGHTS:
├─ Flag se AOV cai > 10% vs 7d média (pode indicar estratégia mudança)
├─ Sugerir marketplace com maior AOV para focus
```

**Acceptance Criteria:**
- [ ] Cálculo bate com verificação manual (TVR / count orders)
- [ ] Update em tempo real quando novo pedido entra
- [ ] Comparação AOV por marketplace mostra corretamente
- [ ] Trending com SMA (Simple Moving Average) de 4h é suave (não jittery)

---

### 2.6 Return Rate (RR)

**Definição:** Percentual de pedidos retornados/devolvidos

```
FÓRMULA:
RR% = COUNT(pedidos_devolvidos) / COUNT(pedidos_totais) * 100

PERÍODO:
├─ RR% 24h = COUNT(devoluções últimas 24h) / COUNT(pedidos últimas 24h) * 100
├─ RR% 7d = COUNT(devoluções últimas 7d) / COUNT(pedidos últimas 7d) * 100
├─ RR% 30d = COUNT(devoluções últimas 30d) / COUNT(pedidos últimas 30d) * 100

POR MARKETPLACE:
├─ ML: Usar campo "motivo_devolução" na API
├─ TikTok: Status de retorno (return_status field)
├─ Shopee: ordem com status = "return_completed"
├─ Amazon: Use FBA return metrics ou seller return data
└─ Magalu: Usar status "devolvido"

CÁLCULO:
├─ Total pedidos últimas 24h = 48
├─ Devoluções últimas 24h = 2
├─ RR% = 2/48 * 100 = 4.17%

THRESHOLDS & ALERTS:
├─ VERDE: RR% < 2% (muito bom)
├─ AMBER: RR% 2-5% (aceitável)
├─ VERMELHO: RR% > 5% (problema de qualidade)

TRENDING:
├─ Mostrar trending com sparkline (7d média)
├─ Alert se RR% sobe > 20% vs 7d média

BREAKDOWN:
├─ Por marketplace: qual tem maior RR%
├─ Por motivo: top reasons for return (se disponível na API)

VISUAL NA UI:
├─ Primário: "4.17%" (24h)
├─ Secondary: "2 devoluções de 48 pedidos"
├─ Trending: "-0.5% vs yesterday" (seta verde se melhorando)
├─ Comparison: "ML: 3% | TikTok: 6% | ..." (badges com cor)
```

**Acceptance Criteria:**
- [ ] Contagem correta de devoluções (validar com raw data de cada API)
- [ ] Cálculo percentage bate com manual audit
- [ ] Thresholds funcionam (alert vermelho quando RR% > 5%)
- [ ] Trending com precisão >95%
- [ ] Breakdown por marketplace mostra corretamente

---

### 2.7 Comissão por Marketplace (detalhe)

**Definição:** Breakdown de todas as taxas por marketplace

```
ESTRUTURA TABULAR (FEATURE-004: TARIFAS MARKETPLACE):

┌──────────────────┬────────────────┬──────────┬────────────┬────────────┐
│ Marketplace      │ Comissão Base  │ Taxa TI  │ Taxa Frete │ Total % +$ │
├──────────────────┼────────────────┼──────────┼────────────┼────────────┤
│ Mercado Livre    │ 16.5%          │ 0.5%     │ 0%         │ 17.0%      │
│ TikTok Shop      │ 5.0%           │ 0%       │ 0%         │ 5.0%       │
│ Shopee           │ 3.0%           │ 1.5%     │ 0.8%       │ 5.3%       │
│ Amazon BR        │ 7.0%           │ 1.5%     │ 0%         │ 8.5%       │
│ Magalu           │ 4.0%           │ 0.5%     │ 0.5%       │ 5.0%       │
└──────────────────┴────────────────┴──────────┴────────────┴────────────┘

LAST UPDATED: 2026-03-06 14:23 UTC

POR MARKETPLACE (DETALHADO):

MERCADO LIVRE:
├─ Comissão base: 16.5% (sobre valor do produto)
├─ Taxa de publicação: R$ 0,20 por item (fixa)
├─ Taxa TI: 0.5% (se usar Mercado Pago)
├─ Total estimado: 17.0%
└─ Last sync: API /pricing ou manual entry

TIKTOK SHOP:
├─ Comissão: 5% (fixa)
├─ Sem taxa TI se usar TikTok Pay
├─ Sem taxa frete
├─ Total: 5.0%
└─ Last sync: API /shop/fees

SHOPEE:
├─ Comissão: 3% (para categoria padrão)
├─ Taxa TI Shopee Pay: 1.5%
├─ Taxa frete: 0.8% (em média, variável por destino)
├─ Total: ~5.3%
└─ Last sync: API /fees?shop_id=XXX

AMAZON:
├─ Comissão de referência: 7% (variável por categoria)
├─ Taxa de publicação: variável
├─ Fulfillment fee: 0% (seller-fulfilled)
├─ Total: ~7-8.5%
└─ Last sync: SP-API /definitions/fees

MAGALU:
├─ Comissão: 4% (padrão)
├─ Taxa plataforma: 0.5%
├─ Taxa frete: 0.5%
├─ Total: 5.0%
└─ Last sync: API /settings/fees

SIMULAÇÃO (FEATURE):
├─ "Se vender R$ 1.000,00 em cada marketplace, qual a margin?"
├─ ML: 1.000 - (1.000 * 0.17) = R$ 830 | 83% margin
├─ TikTok: 1.000 - (1.000 * 0.05) = R$ 950 | 95% margin
├─ Shopee: 1.000 - (1.000 * 0.053) = R$ 947 | 94.7% margin
├─ Amazon: 1.000 - (1.000 * 0.085) = R$ 915 | 91.5% margin
├─ Magalu: 1.000 - (1.000 * 0.05) = R$ 950 | 95% margin
└─ Recomendação: Focar em TikTok/Shopee/Magalu (maior margin)
```

**Acceptance Criteria:**
- [ ] Tarifas baterem com APIs oficiais de cada marketplace
- [ ] Last updated timestamp reflete última sincronização
- [ ] Simulação calcula corretamente (testar 10 cenários)
- [ ] Permitir override manual (para testar cenários "what-if")

---

## 3. DATA REQUIREMENTS (ESTRUTURA DE DADOS)

### 3.1 Schema de Dados Backend

```yaml
# Database: MarketplaceMetrics (central aggregation)

Table: daily_metrics
  Columns:
    - metric_id: UUID (PK)
    - date: DATE
    - marketplace: ENUM (ML, TIKTOK, SHOPEE, AMAZON, MAGALU)
    - tvr: DECIMAL(12,2) [Total Vendor Revenue]
    - order_count: INT
    - return_count: INT
    - commission_total: DECIMAL(12,2)
    - commission_pct: DECIMAL(5,2)
    - timestamp_synced: TIMESTAMP
    - created_at: TIMESTAMP
    - updated_at: TIMESTAMP
  Indexes:
    - (date, marketplace) UNIQUE
    - (marketplace)
    - (timestamp_synced)

Table: hourly_metrics
  Columns:
    - metric_id: UUID (PK)
    - date: DATE
    - hour: INT (0-23)
    - marketplace: ENUM
    - tvr_incremental: DECIMAL(12,2)
    - order_count: INT
    - timestamp_synced: TIMESTAMP
    - created_at: TIMESTAMP
  Indexes:
    - (date, hour, marketplace) UNIQUE
    - (marketplace, timestamp_synced)

Table: marketplace_tariffs
  Columns:
    - tariff_id: UUID (PK)
    - marketplace: ENUM (UNIQUE per version)
    - commission_base_pct: DECIMAL(5,2)
    - commission_ti_pct: DECIMAL(5,2)
    - commission_freight_pct: DECIMAL(5,2)
    - other_fees_pct: DECIMAL(5,2)
    - total_pct: DECIMAL(5,2) [calculated]
    - effective_date: DATE
    - last_updated: TIMESTAMP
    - source: VARCHAR [API sync / manual entry]
  Indexes:
    - (marketplace, effective_date)

Table: raw_orders
  Columns:
    - order_id: VARCHAR (PK)
    - marketplace: ENUM
    - external_order_id: VARCHAR [API ID]
    - order_date: TIMESTAMP
    - order_amount: DECIMAL(12,2)
    - commission_charged: DECIMAL(12,2)
    - status: ENUM (completed, returned, cancelled, pending)
    - return_date: TIMESTAMP (nullable)
    - return_reason: VARCHAR (nullable)
    - last_synced: TIMESTAMP
    - created_at: TIMESTAMP
    - updated_at: TIMESTAMP
  Indexes:
    - (marketplace, last_synced)
    - (status, order_date)
    - (marketplace, status, order_date)

Table: sync_logs
  Columns:
    - log_id: UUID (PK)
    - marketplace: ENUM
    - sync_type: ENUM (hourly, daily, tariff_update)
    - status: ENUM (success, partial, failed)
    - records_processed: INT
    - error_message: VARCHAR (nullable)
    - sync_start: TIMESTAMP
    - sync_end: TIMESTAMP
    - duration_ms: INT
    - created_at: TIMESTAMP
  Indexes:
    - (marketplace, sync_start DESC)
```

### 3.2 Data Flow (Ingestão)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCES (APIs):                                                            │
│  ├─ Mercado Livre API (/orders, /fees)                                     │
│  ├─ TikTok Shop API (/shop/order_list, /shop/fees)                         │
│  ├─ Shopee API (/v2/order/orders_get, /v2/shop_category_get)             │
│  ├─ Amazon SP-API (/orders/v0/orders, /definitions/fees)                  │
│  └─ Magalu API (/orders, /settings/fees)                                   │
│                                                                             │
│  ↓                                                                          │
│                                                                             │
│  AGGREGATOR SERVICE (Lambda/Cloud Run):                                    │
│  ├─ Schedule: every 5 minutes for hourly_metrics                           │
│  ├─ Schedule: every night 00:05 UTC for daily_metrics & tariff sync       │
│  ├─ Batch: collect all orders from last sync point                         │
│  ├─ Transform: standardize across APIs (order_id, amount, commission)     │
│  ├─ Calculate: TVR, commission totals, return rates                        │
│  └─ Upsert: to hourly_metrics, daily_metrics, raw_orders                   │
│                                                                             │
│  ↓                                                                          │
│                                                                             │
│  VALIDATION LAYER:                                                          │
│  ├─ Assert: TVR >= 0                                                        │
│  ├─ Assert: commission_pct between 0 and 100                               │
│  ├─ Assert: order_count <= order_count_yesterday * 1.5 (sanity check)      │
│  ├─ Log: anomalies to monitoring system (Sentry/DataDog)                   │
│  └─ Retry: failed syncs with exponential backoff (max 3 attempts)          │
│                                                                             │
│  ↓                                                                          │
│                                                                             │
│  CACHE LAYER (Redis):                                                       │
│  ├─ Key: dashboard:tvr:24h:all → R$ 45.230,50 | TTL 5 min                │
│  ├─ Key: dashboard:margin:24h:all → 18.5% | TTL 5 min                    │
│  ├─ Key: dashboard:breakdown:{marketplace} → JSON | TTL 5 min             │
│  └─ Invalidate: on every update                                            │
│                                                                             │
│  ↓                                                                          │
│                                                                             │
│  FRONTEND (WebSocket):                                                       │
│  ├─ Subscribe: dashboard:tvr, dashboard:margin, dashboard:breakdown       │
│  ├─ Receive: updates every 5 min (or on change)                            │
│  ├─ Render: KPI cards with new values                                      │
│  └─ Transition: smooth animation (CSS fade-in-out)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 API Contracts (por marketplace)

```
MERCADO LIVRE:
GET /orders/v2/orders?sort=date_desc&limit=50&status=paid
Response:
{
  "paging": {"total": 1000, "offset": 0, "limit": 50},
  "orders": [
    {
      "id": "12345678",
      "buyer": {...},
      "seller": {...},
      "total_amount": 199.90,
      "status": "paid",
      "date_created": "2026-03-06T14:23:00Z",
      "date_closed": "2026-03-06T14:25:00Z"
    }
  ]
}

Extract: order_id, total_amount, date_created
Calculate: commission = total_amount * 0.165 (16.5% default)
Upsert: to raw_orders with marketplace='ML'

────────────────────────────────────────────────────────────────────

TIKTOK SHOP:
GET /shop/order_list?status=completed_sale
Response:
{
  "data": {
    "orders": [
      {
        "order_id": "TIKTOK_123456789",
        "order_amount": 299.90,
        "order_status": "completed_sale",
        "create_time": 1678032180,
        "platform_fee": 14.99,  # 5%
        "commission": 14.99
      }
    ]
  }
}

Extract: order_id, order_amount, create_time
Commission: order_amount * 0.05
Upsert: to raw_orders with marketplace='TIKTOK'

────────────────────────────────────────────────────────────────────

SHOPEE:
GET /v2/order/orders_get?status=100,110,120
Response:
{
  "response": {
    "orders": [
      {
        "order_sn": "SHOPEE_123456789",
        "total_amount": 199.90,
        "shop_commission": 5.99,  # 3% base + 1.5% TI + 0.8% freight
        "order_status": 100,  # completed
        "create_time": 1678032180
      }
    ]
  }
}

Extract: order_sn, total_amount, create_time
Commission: total_amount * 0.053 (3% + 1.5% + 0.8%)
Upsert: to raw_orders with marketplace='SHOPEE'

────────────────────────────────────────────────────────────────────

AMAZON:
GET /orders/v0/orders?CreatedAfter=2026-03-05&OrderStatuses=Shipped,Delivered
Response:
{
  "Payload": {
    "Orders": [
      {
        "AmazonOrderId": "AMAZON_123456789",
        "PurchaseDate": "2026-03-06T14:23:00Z",
        "OrderTotal": {"CurrencyCode": "BRL", "Amount": "199.90"},
        "OrderStatus": "Shipped",
        "FulfillmentChannel": "MFN"  # Merchant Fulfilled Network
      }
    ]
  }
}

Extract: AmazonOrderId, OrderTotal, PurchaseDate
Commission: OrderTotal * 0.085 (7% referral + 1.5% for Mercado Pago)
Upsert: to raw_orders with marketplace='AMAZON'

────────────────────────────────────────────────────────────────────

MAGALU:
GET /orders?status=pago
Response:
{
  "data": [
    {
      "id": "MAGALU_123456789",
      "created_at": "2026-03-06T14:23:00Z",
      "total_value": 199.90,
      "status": "pago",
      "commission_rate": 0.05  # 5%
    }
  ]
}

Extract: id, total_value, created_at
Commission: total_value * commission_rate (typically 0.05 = 5%)
Upsert: to raw_orders with marketplace='MAGALU'
```

---

## 4. INTEGRATION DEPENDENCIES

### 4.1 External APIs & SDKs

| Dependência | Versão | Tipo | Status |
|-------------|--------|------|--------|
| **ML SDK** | 2.x | REST + MCP (existing) | Usar MCP existente |
| **TikTok API** | v2.0 | REST + OAuth | Implementar novo |
| **Shopee API** | v2.0 | REST + OAuth | Implementar novo |
| **Amazon SP-API** | 2.0 | REST + auth | Implementar novo |
| **Magalu API** | 1.0 | REST + API Key | Implementar novo |
| **Redis** | 7.x+ | In-memory cache | Usar existente ou setup |
| **PostgreSQL** | 14+ | Primary DB | Usar existente |

### 4.2 Internal Dependencies

```
Frontend (React/Next.js):
├─ Components: Card, Chart (recharts), Table, Alert
├─ State: Redux/Zustand (real-time state sync)
├─ WebSocket: Socket.io ou native WS
├─ Offline: Service Worker + IndexedDB
└─ Charts: Recharts, Chart.js ou D3

Backend (Node.js / Python):
├─ API Gateway: Express.js / FastAPI
├─ Database: PostgreSQL (+ Sequelize/SQLAlchemy ORM)
├─ Cache: Redis (ioredis / redis-py)
├─ Scheduler: Bull / Celery (periodic tasks)
├─ WebSocket: Socket.io / websockets
├─ Logging: Winston / Python logging (Sentry)
├─ Monitoring: DataDog / NewRelic
└─ Auth: JWT / OAuth2

Infrastructure:
├─ Hosting: AWS (Lambda + RDS) ou GCP (Cloud Run + CloudSQL)
├─ Message Queue: SQS / Pub/Sub (for async processing)
├─ CDN: CloudFront / Cloudflare (static assets)
└─ Monitoring: CloudWatch / Cloud Logging
```

### 4.3 Setup Instructions (Priority)

**Week 1 (Setup):**
- [ ] Setup database schema (create tables per 3.1)
- [ ] Setup Redis cache
- [ ] Implement ML API integration (usar MCP existente)
- [ ] Implement TikTok API integration + OAuth

**Week 2 (Integrations):**
- [ ] Implement Shopee API + OAuth
- [ ] Implement Amazon SP-API
- [ ] Implement Magalu API
- [ ] Setup aggregator service (Lambda/Cloud Run)

**Week 3 (Frontend):**
- [ ] Implement KPI cards (FEATURE-001)
- [ ] Implement real-time sync (FEATURE-007)
- [ ] Implement offline support (FEATURE-008)

**Week 4 (Polish):**
- [ ] Dark mode (FEATURE-006)
- [ ] Responsive design (FEATURE-009)
- [ ] Testing + QA

---

## 5. ACCEPTANCE CRITERIA (POR FEATURE)

### FEATURE-001: Dashboard Home (KPI Cards)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - DASHBOARD HOME                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. TOTAL VENDOR REVENUE CARD                                               │
│    [ ] Exibe valor correto em R$ (BRL formatting)                         │
│    [ ] Trending visually correct (↑ green se crescimento)                 │
│    [ ] Breakdown mostra % por marketplace (soma = 100%)                   │
│    [ ] Updates em tempo real (< 500ms após novo pedido)                  │
│    [ ] Accessible: aria-label, semantic HTML, keyboard navigation         │
│                                                                             │
│ 2. NET MARGIN % CARD                                                       │
│    [ ] Cálculo correto: (TVR - Comissões) / TVR * 100                    │
│    [ ] Threshold visual (verde >20%, amber 15-20%, vermelho <15%)        │
│    [ ] Sparkline trending mostra últimas 24h com precisão                 │
│    [ ] Tooltip on hover mostra breakdown de comissões                     │
│    [ ] Alerta dispara quando < 15% com dismiss option                    │
│                                                                             │
│ 3. COMISSÕES PAGAS CARD                                                    │
│    [ ] Soma correta de comissões (validar com 20 pedidos)                 │
│    [ ] Mostra R$ total e % do TVR                                         │
│    [ ] Breakdown por marketplace com drill-down                            │
│    [ ] Histórico últimas 24h visível em dropdown                          │
│                                                                             │
│ 4. SALES LAST 24H CARD                                                     │
│    [ ] Contagem correta de pedidos completados                            │
│    [ ] Sparkline mostra pedidos/hora                                       │
│    [ ] Trending vs yesterday com % change                                  │
│    [ ] Atualiza em tempo real quando novo pedido entra                    │
│                                                                             │
│ 5. AOV CARD                                                                 │
│    [ ] Cálculo correto: TVR / número de pedidos                           │
│    [ ] Mostra valores por marketplace                                      │
│    [ ] Comparativo vs 7d média                                             │
│    [ ] Destaca marketplace com maior AOV (gold star)                       │
│                                                                             │
│ 6. RETURN RATE CARD                                                         │
│    [ ] Cálculo correto: devoluções / pedidos totais * 100                │
│    [ ] Threshold visual (verde <2%, amber 2-5%, vermelho >5%)            │
│    [ ] Mostra count (e.g., "2 devoluções de 48")                         │
│    [ ] Trending com linha (7d SMA)                                         │
│                                                                             │
│ 7. LAYOUT & RESPONSIVENESS                                                 │
│    [ ] Desktop (1920px): 4 cards por linha (2x3 grid com últimas 2)      │
│    [ ] Tablet (768-1024): 2 cards por linha (3x2 grid)                    │
│    [ ] Mobile (<768): 1 card por linha (single column)                    │
│    [ ] Cards não truncam texto, wrapping correto                          │
│    [ ] Spacing consistente (16px gutters)                                 │
│                                                                             │
│ 8. PERFORMANCE                                                              │
│    [ ] Primeira renderização < 1.5s (LCP)                                │
│    [ ] Interatividade (FID) < 100ms                                       │
│    [ ] Cumulative Layout Shift (CLS) < 0.1                                │
│    [ ] Memory usage < 50MB (no leaks com 1h sessão)                      │
│                                                                             │
│ 9. ACCESSIBILITY                                                            │
│    [ ] Lighthouse accessibility score >= 90                               │
│    [ ] ARIA labels em todos os cards                                      │
│    [ ] Keyboard navigation com Tab, Enter                                 │
│    [ ] Color contrast ratio >= 4.5:1 (WCAG AA)                           │
│    [ ] Screen reader readable (teste com NVDA)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-002: Marketplace Breakdown View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - MARKETPLACE BREAKDOWN                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. TABELA / CARDS VIEW                                                     │
│    [ ] Exibe todos 5 marketplaces (ML, TikTok, Shopee, Amazon, Magalu)    │
│    [ ] Colunas: Marketplace | Revenue | Commission | Margin% | Orders     │
│    [ ] Valores formatados corretamente (R$ para moeda, % para percentual)  │
│    [ ] Soma de todas as linhas = totais do dashboard (validar 100%)       │
│    [ ] Cores temáticas por marketplace (visual consistency)                │
│                                                                             │
│ 2. SORTING & FILTERING                                                     │
│    [ ] Default sort: por revenue DESC (maior para menor)                   │
│    [ ] Sortable: clicável em cada header (↑/↓ icons)                      │
│    [ ] Filter by status: toggle "ativo / inativo"                          │
│    [ ] Filter by period: radio buttons (24h / 7d / 30d)                   │
│    [ ] Filtro aplica instantaneamente (no lag)                             │
│                                                                             │
│ 3. VISUAL COMPARAÇÃO                                                        │
│    [ ] % contribution ao total exibido (barras stacked ou badges)          │
│    [ ] Trending: setas ↑/↓ para cada métrica vs período anterior           │
│    [ ] Destaca marketplace com maior revenue (bold)                        │
│    [ ] Destaca marketplace com melhor margin (gold star)                   │
│                                                                             │
│ 4. RESPONSIVENESS                                                           │
│    [ ] Desktop: tabela com scroll horizontal se > 5 colunas               │
│    [ ] Tablet: 2-3 colunas principais + scroll                            │
│    [ ] Mobile: cards empilhados (1 por marketplace)                       │
│    [ ] Touch-friendly: tap-to-sort, swipe-to-filter                       │
│                                                                             │
│ 5. DRILL-DOWN (NICE-TO-HAVE)                                              │
│    [ ] Click em marketplace → mostra últimos 10 pedidos                   │
│    [ ] Mostra detalhes: order_id, amount, commission, status              │
│    [ ] Volta para overview com back button                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-003: Timeline / Histórico

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - TIMELINE / HISTÓRICO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. GRÁFICO: REVENUE POR HORA                                              │
│    [ ] Eixo X: 24 barras (0-23h), timestamp legível                      │
│    [ ] Eixo Y: valor em R$, scale automático                              │
│    [ ] Cor: sparkline em azul (gradient mais escuro em topo)               │
│    [ ] Tooltip: hover mostra hora + valor + % do daily total              │
│    [ ] Responsivo: redimensiona sem distorcer                             │
│                                                                             │
│ 2. GRÁFICO: COMISSÕES ACUMULADAS                                          │
│    [ ] Area chart com gradiente (começa transparente)                      │
│    [ ] Eixo X: 24h timeline                                               │
│    [ ] Eixo Y: valor cumulativo em R$                                     │
│    [ ] Linha no topo mostra total acumulado                               │
│    [ ] Tooltip: mostra valor acumulado até aquela hora                    │
│                                                                             │
│ 3. GRÁFICO: MARGIN TRENDING                                               │
│    [ ] Line chart com 24 pontos (1 por hora)                              │
│    [ ] Eixo Y: 0-100% (margem percentage)                                 │
│    [ ] Threshold visual: linha vermelha em 15% (alerting zone)            │
│    [ ] Cor da linha: verde se > 20%, amber se 15-20%, vermelho se < 15%   │
│    [ ] Ponto destacado: hora atual                                         │
│                                                                             │
│ 4. MARKETPLACE OVERLAY                                                      │
│    [ ] Toggle/tabs para ver breakdown por marketplace                      │
│    [ ] Default: "all marketplaces" (soma total)                            │
│    [ ] Cores: cada marketplace tem sua cor (consistent com resto do UI)    │
│    [ ] Legenda: clicável para toggle on/off linhas específicas             │
│                                                                             │
│ 5. PERFORMANCE                                                              │
│    [ ] Charts renderizam < 500ms                                          │
│    [ ] Smooth animation quando dados atualizam (1s transition)             │
│    [ ] Não causa layout shift ou janky scrolling                           │
│    [ ] WebGL rendering (se D3/Canvas, não SVG ineficiente)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-004: Tarifas Marketplace

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - TARIFAS MARKETPLACE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. TABELA PRINCIPAL                                                        │
│    [ ] 5 linhas (1 por marketplace)                                        │
│    [ ] Colunas: Marketplace | Base | TI | Frete | Total%                  │
│    [ ] Valores em % com 2 casas decimais                                   │
│    [ ] Total% = Base + TI + Frete (validar soma)                          │
│    [ ] Last Updated timestamp abaixo da tabela                             │
│                                                                             │
│ 2. EDIÇÃO MANUAL (OVERRIDE)                                                │
│    [ ] Click em célula → input editable aparece                            │
│    [ ] Validação: apenas números 0-100 permitidos                          │
│    [ ] Total% recalcula automaticamente                                    │
│    [ ] "Salvar" e "Cancelar" botões                                        │
│    [ ] Override é temporário (sessão local, não persiste)                  │
│    [ ] Visual indicator: célula editada em yellow/amber                    │
│                                                                             │
│ 3. SIMULAÇÃO ("SE VENDER")                                                 │
│    [ ] Input: "Se vender R$ 1.000,00"                                     │
│    [ ] Output tabela: Marketplace | Gross | Commission | Net | Margin%    │
│    [ ] Cálculos: Net = Gross - Commission, Margin% = Net/Gross*100        │
│    [ ] Recomendação: destacar marketplace com melhor margin (gold star)   │
│    [ ] Dinâmico: atualiza real-time enquanto digita                       │
│                                                                             │
│ 4. FONTE DE DADOS                                                           │
│    [ ] Tarifas vêm de APIs oficiais (não hardcoded)                       │
│    [ ] Last sync reflete última atualização automática                     │
│    [ ] Botão "Sync now" para forçar atualização                            │
│    [ ] Avisar se tarifa > 30 dias desatualizada                            │
│                                                                             │
│ 5. RESPONSIVENESS                                                           │
│    [ ] Desktop: tabela com spacing generoso                                │
│    [ ] Tablet: coluna "Frete" pode esconder se espaço limitado             │
│    [ ] Mobile: cards empilhados (1 por marketplace)                        │
│    [ ] Simulação: input + resultado em cards separados                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-005: Alert System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - ALERT SYSTEM                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. ALERT: MARGIN < 15%                                                     │
│    [ ] Dispara quando NM% cai abaixo 15%                                  │
│    [ ] Toast notification: "⚠️ Margin < 15%" (vermelho)                    │
│    [ ] Aparece por 5s (ou até dismiss)                                    │
│    [ ] Persistir no top-right corner até user dismiss                      │
│    [ ] Sound alert (optional, user can mute)                               │
│                                                                             │
│ 2. ALERT: COMISSÃO > 25%                                                   │
│    [ ] Monitora comissão por marketplace                                   │
│    [ ] Dispara quando comissão_pct > 25% em algum marketplace              │
│    [ ] Toast notification: "MARKETPLACE com comissão alta"                │
│    [ ] Offer action: "view tariffs" button para ir a FEATURE-004           │
│                                                                             │
│ 3. ALERT: SYNC OFFLINE                                                     │
│    [ ] Dispara quando API desconectada por > 10min                         │
│    [ ] Banner: "📴 Offline - exibindo cache de XXh atrás"                 │
│    [ ] Cor: amber background, preto ou dark gray text                      │
│    [ ] Ação: "Reconectar" button ou automático quando online                │
│    [ ] Tooltip: explica que dados podem estar desatualizados               │
│                                                                             │
│ 4. ALERT: API DESCONECTADA (RED STATUS)                                    │
│    [ ] Monitora status de cada API                                         │
│    [ ] Visual indicator: badge/dot vermelho próximo ao marketplace         │
│    [ ] Tooltip: "ML desconectado há Xmin"                                 │
│    [ ] Retry automático a cada 30s                                         │
│    [ ] Alert persistir até status = conectado                              │
│                                                                             │
│ 5. DISMISS & SNOOZE                                                         │
│    [ ] X button na notificação → dismiss (remover imediatamente)           │
│    [ ] "Snooze 1h" button → hide até 1h depois                             │
│    [ ] Se mesmo alert dispara novamente dentro 1h, não mostrar             │
│    [ ] Local storage: guardar snooze state                                 │
│                                                                             │
│ 6. ALERT HISTORY                                                            │
│    [ ] Dropdown/icon em navbar mostra últimas 10 alerts                    │
│    [ ] Timestamp, severity, ação taken                                     │
│    [ ] Clear all history button                                            │
│    [ ] Cada alert com "details" link                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-006: Dark Mode

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - DARK MODE                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. SISTEMA DETECTION                                                        │
│    [ ] Deteta prefers-color-scheme: dark (system preference)               │
│    [ ] Default: seguir system setting                                      │
│    [ ] Se system não define, default para light                            │
│    [ ] Não flicker ao carregar (cuidado com FOUC)                         │
│                                                                             │
│ 2. MANUAL TOGGLE                                                            │
│    [ ] Settings page ou navbar: Dark Mode toggle (on/off)                 │
│    [ ] Icon: sun (light) / moon (dark)                                     │
│    [ ] Estado persiste em localStorage com chave "theme-preference"        │
│    [ ] Override sistema setting se user escolhe manualmente                │
│                                                                             │
│ 3. SEMANTIC COLORS (APPLE STYLE)                                           │
│    [ ] Background: #000000 (dark), #ffffff (light)                         │
│    [ ] Secondary BG: #1c1c1e (dark), #f5f5f7 (light)                      │
│    [ ] Text: #f5f5f7 (dark), #1d1d1d (light)                              │
│    [ ] Text Secondary: #a1a1a6 (dark), #86868b (light)                    │
│    [ ] Accent: #0a84ff (blue - same em ambos)                             │
│    [ ] Red (error): #ff453a, Green (success): #34c759                     │
│                                                                             │
│ 4. COMPONENT THEMING                                                        │
│    [ ] Cards: dark gray background em dark mode                            │
│    [ ] Charts: cores adjustadas para legibilidade                          │
│    [ ] Table: alternating row colors visible em dark                       │
│    [ ] Input fields: border color contrast > 4.5:1                         │
│    [ ] Buttons: hover state visible em dark mode                           │
│                                                                             │
│ 5. IMAGES & ICONS                                                           │
│    [ ] Logos/icons: adaptados para dark (inverso se necessário)            │
│    [ ] SVG icons: usam currentColor para automático contraste               │
│    [ ] Imagens: não invertidas, contexto preservado                        │
│    [ ] Transparência: ajustada para legibilidade                           │
│                                                                             │
│ 6. TRANSITION & ACCESSIBILITY                                              │
│    [ ] Smooth transition entre temas (0.3s)                                │
│    [ ] Prefers-reduced-motion: respeitar (sem transition)                 │
│    [ ] Lighthouse color contrast: >= 4.5:1 em ambos temas                 │
│    [ ] NVDA/JAWS: descrevem cores corretamente                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-007: Real-Time Sync

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - REAL-TIME SYNC (<500MS)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. CONNECTION METHOD                                                        │
│    [ ] Implementar WebSocket (Socket.io ou nativa)                         │
│    [ ] Fallback: polling 100ms se WebSocket falha                          │
│    [ ] Batching: máximo 1 update por segundo (não spam)                    │
│    [ ] Reconnect automático com exponential backoff                        │
│                                                                             │
│ 2. LATÊNCIA (<500MS)                                                        │
│    [ ] Novo pedido entra em API → aparece no dashboard < 500ms            │
│    [ ] Medição: timestamp na API - timestamp no client                     │
│    [ ] Test: gerar 100 pedidos fake, medir latência média                 │
│    [ ] P95 latência < 500ms (máximo aceitável)                             │
│                                                                             │
│ 3. UPDATE CASCADE                                                           │
│    [ ] Novo pedido recebido → atualiza raw_orders (DB)                    │
│    [ ] ↓ recalcula hourly_metrics (TVR, commission, etc)                   │
│    [ ] ↓ broadcast via WebSocket                                           │
│    [ ] ↓ frontend recebe → atualiza state (Redux/Zustand)                  │
│    [ ] ↓ re-render cards, charts, tables                                   │
│    [ ] Total time: < 500ms                                                 │
│                                                                             │
│ 4. OPTIMISTIC UPDATES                                                       │
│    [ ] Cliente otimista: mostrar loading state durante update               │
│    [ ] Spinner/skeleton em cards afetados                                  │
│    [ ] Se servidor rejeita: rollback para valor anterior                   │
│    [ ] Erro notification: "Erro ao sincronizar, retentando..."            │
│                                                                             │
│ 5. ERROR HANDLING & RETRY                                                  │
│    [ ] Connection refused: retry em 5s, depois 10s, depois 30s              │
│    [ ] Max 3 tentativas antes de mostrar error banner                      │
│    [ ] Manual refresh button: forçar sync agora                            │
│    [ ] Sentry logging: registrar todas tentativas falhadas                 │
│                                                                             │
│ 6. PERFORMANCE                                                              │
│    [ ] Memory: não vazar listeners de WebSocket                            │
│    [ ] CPU: não exceder 10% CPU durante idle (batching funciona)           │
│    [ ] Network: < 1KB por update (compress JSON)                           │
│    [ ] DevTools Network: observar tamanho de cada payload                  │
│                                                                             │
│ 7. TESTING                                                                  │
│    [ ] Unit test: mock WebSocket, verificar update flow                    │
│    [ ] Integration test: real conexão com staging API                      │
│    [ ] Load test: 100 updates/s, sistema mantém < 500ms latência          │
│    [ ] Chaos test: simular disconnect, reconectar, latência aumentada      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-008: Offline Support

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - OFFLINE SUPPORT (24H CACHE)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. SERVICE WORKER                                                           │
│    [ ] Registrar Service Worker on app load                                │
│    [ ] Cache strategy: network-first com cache fallback                    │
│    [ ] Offline detection: navigator.onLine + NetInfo API                  │
│    [ ] Update SW: check every minute para nova versão                      │
│                                                                             │
│ 2. INDEXEDDB STORAGE                                                        │
│    [ ] Criar database "dashboardCache" com 2 stores:                       │
│    │   - hourly_metrics: key (date:hour:marketplace)                      │
│    │   - daily_metrics: key (date:marketplace)                            │
│    │                                                                       │
│    [ ] Store últimas 24h de dados completos                                │
│    [ ] Auto-expire: deletar dados > 24h antigos                            │
│    [ ] Size limit: máximo 50MB (indexedDB quota típica)                    │
│                                                                             │
│ 3. STALE STATE HANDLING                                                     │
│    [ ] Quando offline: mostrar cached data                                 │
│    [ ] Banner: "📴 Exibindo dados de 2h atrás" (timestamp visível)        │
│    [ ] Cor: amber background                                               │
│    [ ] Tooltip: "Reconecte para dados atualizados"                        │
│    [ ] Cards: dim/opacity reduzida para indicar stale data                 │
│                                                                             │
│ 4. SYNC ON RECONNECT                                                        │
│    [ ] Detectar reconexão (online event listener)                          │
│    [ ] Trigger imediato de fetch para últimos dados                        │
│    [ ] Comparar timestamps: só update se servidor > cache                  │
│    [ ] Smooth transition: fade out stale data, fade in novo                │
│    [ ] Remover banner offline                                              │
│                                                                             │
│ 5. CONFLICT RESOLUTION                                                      │
│    [ ] Se dados locais > servidor (relógio do client adiantado):          │
│    │   - Prefer servidor como source of truth                             │
│    │   - Avisar user: "Sincronização corrigida"                           │
│    │   - Log: registrar discrepância                                      │
│                                                                             │
│ 6. TESTING                                                                  │
│    [ ] DevTools: Application > Storage > IndexedDB verificar dados         │
│    [ ] Chrome DevTools Network: throttle para offline                      │
│    [ ] Verificar que dashboard funciona offline                            │
│    [ ] Desconectar internet, refreshar página, dados ainda aparecem        │
│    [ ] Reconectar, dados sincronizam em < 5s                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-009: Responsive Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - RESPONSIVE DESIGN                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. DESKTOP (1920px+)                                                        │
│    [ ] 4-column layout: 4 cards por linha (2 linhas)                       │
│    [ ] Remaining 2 cards: stretch to 2-column span ou segunda linha        │
│    [ ] Gutter: 24px entre cards                                            │
│    [ ] No horizontal scroll                                                │
│    [ ] Charts: full width com height 300px                                 │
│                                                                             │
│ 2. TABLET (768-1024px)                                                      │
│    [ ] 2-column layout: 2 cards por linha                                  │
│    [ ] Gutter: 16px                                                        │
│    [ ] Tabela: horizontal scroll se necessário                             │
│    [ ] Charts: reescalados para caber                                      │
│    [ ] Touch targets: >= 44x44px (todo button/tap area)                    │
│                                                                             │
│ 3. MOBILE (<768px)                                                          │
│    [ ] 1-column layout: cards stackados verticalmente                      │
│    [ ] Full width menos 16px padding (ambos lados)                         │
│    [ ] Cards: margin bottom 12px                                           │
│    [ ] Tabelas: cards estilo com key: value layout                         │
│    [ ] Charts: height 200px, swipeable (carousel se múltiplos)             │
│    [ ] Input fields: font-size >= 16px (prevent zoom on focus)             │
│                                                                             │
│ 4. ORIENTATION CHANGES                                                      │
│    [ ] Portrait → Landscape: layout muda fluidamente                       │
│    [ ] No content loss, no horizontal scroll                               │
│    [ ] Test: iPhone 12/13, iPad, Android devices                           │
│                                                                             │
│ 5. TOUCH-FRIENDLY                                                           │
│    [ ] Buttons: >= 44x44px (Apple HIG standard)                            │
│    [ ] Spacing: >= 8px entre interactive elements                          │
│    [ ] Tap feedback: visual feedback (ripple ou scale)                     │
│    [ ] No hover-only controls (hover não funciona em touch)                │
│    [ ] Swipe gestures: se implementar (carousel, drawer)                   │
│                                                                             │
│ 6. TESTING DEVICE                                                           │
│    [ ] Chrome DevTools: iPhone 12, iPad Pro, Pixel 5                       │
│    [ ] Real device testing: pelo menos 1 iOS e 1 Android                   │
│    [ ] Browser: Chrome, Safari (iOS), Firefox                              │
│    [ ] Lighthouse: Mobile score >= 90 (performance + accessibility)        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FEATURE-010: Export & Reporting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCEPTANCE CRITERIA - EXPORT & REPORTING (P1 - NICE-TO-HAVE)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. EXPORT CSV                                                               │
│    [ ] Button: "⬇ Export CSV" na marketplace breakdown                     │
│    [ ] Dados: Marketplace | Revenue | Commission | Margin% | Orders       │
│    [ ] Formato: RFC 4180 (valid CSV, escapable quotes)                     │
│    [ ] Encoding: UTF-8                                                     │
│    [ ] Filename: "marketplace-report-YYYY-MM-DD.csv"                       │
│    [ ] Tarifas também exportáveis separadamente                            │
│                                                                             │
│ 2. EXPORT PDF                                                               │
│    [ ] Button: "📄 Export PDF"                                             │
│    [ ] Conteúdo: snapshot do dashboard com timestamp                       │
│    [ ] Header: logo, data/hora, período                                    │
│    [ ] Página 1: KPI cards overview                                        │
│    [ ] Página 2: Marketplace breakdown tabela                              │
│    [ ] Página 3: Charts (revenue, margin, commission)                      │
│    [ ] Página 4: Tarifa details                                            │
│    [ ] Footer: "Generated on YYYY-MM-DD HH:MM UTC"                         │
│                                                                             │
│ 3. SHARE LINK                                                               │
│    [ ] Button: "🔗 Share"                                                  │
│    [ ] Modal: "Share your dashboard"                                       │
│    [ ] Gera link único: https://dashboard.app/share/ABC123                │
│    [ ] Link expiração: 7 dias (ou user-configurable)                       │
│    [ ] Permissões: read-only, não pode editar override tariffs             │
│    [ ] Mostrar: "Shared with password" option                              │
│    [ ] Copy to clipboard button                                            │
│                                                                             │
│ 4. SHARED LINK VIEWING                                                      │
│    [ ] Access sem login: read-only view                                    │
│    [ ] Mostrar data do snapshot + "expires on XXX"                         │
│    [ ] Disable: edit buttons, export, share                                │
│    [ ] Footer: "Read-only shared view"                                     │
│    [ ] Se expirado: mostrar "Link expired"                                 │
│                                                                             │
│ NOTA: P1 = implementar após MVP se tempo permitir                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. SUCCESS METRICS & KPIs

| Métrica | Target | Medição | Frequência |
|---------|--------|---------|-----------|
| **Page Load Time (LCP)** | < 1.5s | Lighthouse + RUM (Real User Monitoring) | Daily |
| **Time to Interactive (FID)** | < 100ms | Chrome Analytics | Daily |
| **Cumulative Layout Shift** | < 0.1 | Web Vitals API | Daily |
| **Uptime** | 99.9% | StatusPage + healthchecks | Realtime |
| **API Latency (P95)** | < 500ms | DataDog APM | Realtime |
| **Sync Accuracy** | > 99.5% | Audit scripts (TVR vs APIs) | Daily |
| **Data Freshness** | < 5 min | Timestamp comparison | Realtime |
| **User Adoption** | > 80% of team | Login tracking | Weekly |
| **Feature Usage** | > 70% for core features | Analytics events | Weekly |
| **Error Rate** | < 0.5% | Sentry error tracking | Realtime |

---

## 7. CONSTRAINTS & ASSUMPTIONS

### Constraints

```
TÉCNICOS:
├─ Browser support: Chrome, Safari, Firefox (últimas 2 versões)
├─ Mobile: iOS 14+, Android 10+
├─ Database: PostgreSQL 14+ (não NoSQL)
├─ Storage: máximo 10GB para 6 meses de dados
├─ API rate limits: ML 100/min, TikTok 1000/day, Shopee 1000/day, Amazon SP-API varies, Magalu 500/day
├─ Offline cache: máximo 24h (storage quota 50MB)
└─ Real-time: latência rede típica 100-200ms

NEGÓCIOS:
├─ Budget: $50K para desenvolvimento (setup + integração)
├─ Timeline: 4 semanas para MVP
├─ Team: 1 fullstack + 1 QA
├─ Marketplace data: 30 dias de histórico (não lifetime)
├─ Dark mode: opcional (não essencial para MVP)
└─ Export/Share: nice-to-have, pode esperar v1.1

LEGAIS:
├─ Compliance: LGPD (Brasil) - dados vendedor são PII
├─ Auth: vendedor só vê seu próprio data
├─ Encryption: TLS 1.2+ em trânsito, encryption em repouso recomendado
└─ Data retention: deletar dados > 90 dias por LGPD direito ao esquecimento
```

### Assumptions

```
1. APIs de marketplace estão sempre disponíveis (ou com SLA aceitável)
2. Marketplace tarifas mudam < 1x por mês (caching 30 dias aceitável)
3. Usuário tem conexão estável (latência < 1s típico)
4. Volume: máximo 1000 pedidos/dia por vendor (não e-commerce em escala)
5. Servidor backend: sempre online durante business hours (real-time sync viável)
6. Usuário browser moderno com suporte a WebSocket, IndexedDB, Service Workers
7. Conversão de moedas: sempre BRL (não multi-moeda)
8. Timezone: sempre UTC (não timezone do usuário)
9. Dados de teste: marketplace fornecerão sandbox API com dados fake
10. Single user: cada sessão é um vendor vendo apenas seus dados
```

---

## 8. ROADMAP (PÓS-MVP)

### v1.1 (Semana 5-6)
- [ ] Export CSV/PDF (FEATURE-010)
- [ ] Advanced filtering (período customizado, range de data)
- [ ] Email alerts (diários com resumo)
- [ ] Settings: configurar thresholds de alert
- [ ] Webhook integration (notificar sistema externo)

### v1.2 (Semana 7-8)
- [ ] Predictive analytics (ML model para forecast vendas)
- [ ] Competitor benchmarking (compara sua margin vs setor)
- [ ] Drill-down por categoria (não só por marketplace)
- [ ] Histórico > 30 dias (com compressão de dados)
- [ ] Mobile app native (iOS/Android)

### v2.0 (Roadmap futuro)
- [ ] Multi-currency (USD, EUR, etc)
- [ ] Multi-user (time do seller vê dashboard compartilhado)
- [ ] Integração com e-commerce platform (Shopify, WooCommerce)
- [ ] COGS integration (calcular real margin, não só comissão)
- [ ] API pública (3rd parties podem integrar)
- [ ] Marketplace novo: Etsy, B2Brazil, etc

---

## 9. DEFINIÇÕES & GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| **TVR** | Total Vendor Revenue (receita bruta antes de comissões) |
| **NM%** | Net Margin % (receita após comissões) |
| **CP** | Comissões Pagas (total de taxas cobradas) |
| **SL24** | Sales Last 24h (número de pedidos) |
| **AOV** | Average Order Value (preço médio por pedido) |
| **RR%** | Return Rate (% de devoluções) |
| **Marketplace** | Platform que vende produtos (ML, TikTok, etc) |
| **Commission Rate** | % cobrado pelo marketplace |
| **Tariff** | Estrutura de comissão e taxas |
| **Real-time Sync** | Atualização de dados < 500ms |
| **Offline Support** | Funcionar sem conexão com cache de 24h |
| **Responsive** | Adaptar layout para desktop/tablet/mobile |
| **Dark Mode** | Tema escuro do interface |
| **Stale Data** | Dados desatualizados (cache > X tempo) |
| **Optimistic Update** | Mostrar resultado esperado antes do servidor confirmar |

---

## 10. APPROVAL & SIGN-OFF

```
Product Owner:     Thiago Finch              Date: 2026-03-06
Engineering Lead:  ________________          Date: ________
QA Lead:          ________________          Date: ________
Stakeholder:      ________________          Date: ________
```

---

## APÊNDICE A: TECHNICAL ARCHITECTURE DIAGRAM

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                      DASHBOARD APPLE - ARCHITECTURE                          │
│                                                                              │
│  ┌────────────────────────────────────┐      ┌──────────────────────────┐  │
│  │      FRONTEND (React/Next.js)       │      │   BACKEND (Node/Python)  │  │
│  │                                    │      │                          │  │
│  │  ┌────────────────────────────┐    │      │  ┌──────────────────────┐ │  │
│  │  │   KPI Cards               │    │      │  │  API Gateway (Express) │  │  │
│  │  │   - TVR, Margin, Commission│   │      │  │                      │  │  │
│  │  │   - Sales, AOV, Return    │    │      │  └──────────────────────┘  │  │
│  │  │   (with animations)       │    │      │         ↓                 │  │
│  │  └────────────────────────────┘    │      │  ┌──────────────────────┐  │  │
│  │           ↑                        │      │  │  Aggregator Service   │  │  │
│  │           │ (WebSocket)            │      │  │  (Lambda/Cloud Run)   │  │  │
│  │           │                        │      │  │                      │  │  │
│  │  ┌────────────────────────────┐    │      │  │  - Sync APIs (5min)  │  │  │
│  │  │   Charts (Recharts/D3)     │    │      │  │  - Calculate metrics │  │  │
│  │  │   - Revenue sparkline      │    │      │  │  - Upsert DB         │  │  │
│  │  │   - Commission area chart  │    │      │  │  - Broadcast change  │  │  │
│  │  │   - Margin line chart      │    │      │  └──────────────────────┘  │  │
│  │  └────────────────────────────┘    │      │         ↓                 │  │
│  │           ↑                        │      │  ┌──────────────────────┐  │  │
│  │           │                        │      │  │  PostgreSQL (RDS)    │  │  │
│  │  ┌────────────────────────────┐    │      │  │                      │  │  │
│  │  │   Breakdown Table          │    │      │  │  Tables:             │  │  │
│  │  │   - By marketplace         │    │      │  │  - daily_metrics     │  │  │
│  │  │   - Sort/Filter            │    │      │  │  - hourly_metrics    │  │  │
│  │  └────────────────────────────┘    │      │  │  - raw_orders        │  │  │
│  │           ↑                        │      │  │  - marketplace_tariffs│  │  │
│  │           │                        │      │  │  - sync_logs         │  │  │
│  │  ┌────────────────────────────┐    │      │  └──────────────────────┘  │  │
│  │  │   Tariffs Table            │    │      │         ↓                 │  │
│  │  │   - Commission breakdown   │    │      │  ┌──────────────────────┐  │  │
│  │  │   - Simulator              │    │      │  │  Redis (Cache)       │  │  │
│  │  │   - Edit/override          │    │      │  │                      │  │  │
│  │  └────────────────────────────┘    │      │  │  Keys:               │  │  │
│  │           ↑                        │      │  │  - dashboard:tvr:*   │  │  │
│  │           │                        │      │  │  - dashboard:margin:*│  │  │
│  │  ┌────────────────────────────┐    │      │  │  - dashboard:*       │  │  │
│  │  │   Alerts                   │    │      │  └──────────────────────┘  │  │
│  │  │   - Toast notifications   │    │      │         ↑                 │  │
│  │  │   - Snooze/dismiss        │    │      │         │                 │  │
│  │  └────────────────────────────┘    │      │  ┌──────────────────────┐  │  │
│  │           ↑                        │      │  │  WebSocket Server    │  │  │
│  │           │                        │      │  │  (Socket.io)         │  │  │
│  │  ┌────────────────────────────┐    │      │  │                      │  │  │
│  │  │   State Management         │    │      │  │  - Subscribe events  │  │  │
│  │  │   (Redux/Zustand)          │    │      │  │  - Publish updates   │  │  │
│  │  │   - Metrics state          │    │      │  │  - Handle errors     │  │  │
│  │  │   - UI state (dark/light)  │    │      │  └──────────────────────┘  │  │
│  │  └────────────────────────────┘    │      │                          │  │
│  │           ↑                        │      │  EXTERNAL APIs:            │  │
│  │           │                        │      │  ├─ Mercado Livre         │  │
│  │  ┌────────────────────────────┐    │      │  ├─ TikTok Shop           │  │
│  │  │   Service Worker           │    │      │  ├─ Shopee                │  │
│  │  │   (Offline Cache)          │    │      │  ├─ Amazon SP-API         │  │
│  │  │   - IndexedDB store        │    │      │  └─ Magalu                │  │
│  │  │   - Stale state handling   │    │      │                          │  │
│  │  └────────────────────────────┘    │      └──────────────────────────┘  │
│  │                                    │                                    │
│  └────────────────────────────────────┘                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## APÊNDICE B: API SYNC WORKFLOW

```
EVERY 5 MINUTES (Aggregator Lambda):

1. FETCH FROM MARKETPLACE APIS
   ├─ Mercado Livre: GET /orders/v2/orders?status=paid (últimas 5 min)
   ├─ TikTok: GET /shop/order_list?status=completed_sale
   ├─ Shopee: GET /v2/order/orders_get (status 100,110,120)
   ├─ Amazon: GET /orders/v0/orders (Shipped, Delivered)
   └─ Magalu: GET /orders (status pago)

2. TRANSFORM & DEDUPLICATE
   ├─ Extract: order_id, amount, date, commission
   ├─ Compare: contra raw_orders já existentes
   └─ Detect: novos pedidos (não existem em DB)

3. CALCULATE METRICS (HOURLY)
   ├─ SUM(order_amount) = TVR incrementado
   ├─ SUM(commission) = CP incrementado
   ├─ COUNT(order_id) = SL incrementado
   ├─ COUNT(returns) = RR incrementado
   └─ Calcular: AOV, NM%, etc

4. UPSERT TO DATABASE
   ├─ INSERT raw_orders (new orders)
   └─ UPDATE hourly_metrics (latest hour)

5. INVALIDATE CACHE
   ├─ Redis DEL dashboard:tvr:*
   ├─ Redis DEL dashboard:margin:*
   ├─ Redis DEL dashboard:breakdown:*
   └─ Redis DEL dashboard:*

6. BROADCAST UPDATE
   ├─ Query: SELECT * FROM hourly_metrics WHERE hour = current_hour
   ├─ Emit: WebSocket event "metrics:updated" com novo dados
   └─ Frontend recebe: atualiza state → re-render

NIGHTLY (00:05 UTC - Aggregator Lambda):

1. ROLL UP HOURLY TO DAILY
   ├─ SUM all hourly_metrics de 00:00-23:59
   └─ INSERT daily_metrics

2. SYNC TARIFFS
   ├─ GET /pricing de cada marketplace
   ├─ Compare: contra marketplace_tariffs última versão
   ├─ IF changed: INSERT nova versão com effective_date
   └─ Broadcast: alert "Tarifas atualizadas"

3. CLEANUP
   ├─ DELETE raw_orders > 90 dias (LGPD compliance)
   ├─ DELETE hourly_metrics > 30 dias (archive to S3)
   └─ Vacuum PostgreSQL (optimize indexes)
```

---

**PRD-DASHBOARD-APPLE.md v1.0.0 | FINAL PARA DESENVOLVIMENTO**

