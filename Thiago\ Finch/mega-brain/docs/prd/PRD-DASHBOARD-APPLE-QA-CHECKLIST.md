# QA-CHECKLIST: Dashboard Apple
## Test Plan & Validation Checklist

**Versão:** 1.0.0 | **Data:** 2026-03-06 | **Gerenciado por:** QA Lead

---

## ESTRUTURA

Este checklist é organizado por feature. Cada feature tem:
- Setup & Prerequisites
- Functional tests (caixa branca)
- Acceptance criteria (pass/fail)
- Performance benchmarks
- Edge cases & error scenarios
- Sign-off

---

## FEATURE-001: KPI CARDS

### Setup
```
- [ ] Database com dados de teste (100 pedidos por marketplace)
- [ ] APIs mock ou sandbox configuradas
- [ ] Frontend environment com Redux/Zustand
- [ ] Chrome DevTools aberto (Network, Performance, Storage)
```

### Test Cases

#### 1.1 Total Vendor Revenue (TVR)
```
TC-001-001: Render corretto
    [ ] Card exibe "R$ XX.XXX,XX" (BRL formatting)
    [ ] Breakdown mostra % por marketplace (soma = 100% ±0.1%)
    [ ] Trending seta ↑/↓ visível

TC-001-002: Cálculo correto
    [ ] Simular 5 pedidos em ML (R$ 100 cada = R$ 500)
    [ ] Simular 3 pedidos em TikTok (R$ 50 cada = R$ 150)
    [ ] TVR Total deve ser R$ 650,00
    [ ] Breakdown: ML 76.9%, TikTok 23.1%

TC-001-003: Update em tempo real
    [ ] Adicionar novo pedido (R$ 200 em ML)
    [ ] TVR deve atualizar para R$ 850,00 em < 500ms
    [ ] Trending deve mudar (de -5% para +30%)

TC-001-004: Edge cases
    [ ] TVR = R$ 0,00 se não há pedidos
    [ ] TVR muito grande (> R$ 1.000.000): formatting correto
    [ ] Valores negativos: não aparecer (validação backend)
```

#### 1.2 Net Margin % (NM%)
```
TC-001-005: Cálculo correto
    [ ] TVR = R$ 100, Comissões = R$ 20
    [ ] NM% = (100-20)/100 * 100 = 80%
    [ ] Mostrado como "80.0%"

TC-001-006: Threshold visual
    [ ] NM% > 20%: cor verde
    [ ] NM% 15-20%: cor amber
    [ ] NM% < 15%: cor vermelha
    [ ] Mudança de cor ocorre imediatamente ao atualizar

TC-001-007: Sparkline trending
    [ ] Mostra últimas 24h com 24 pontos
    [ ] Linha suave (não jittery)
    [ ] Hover mostra valor de cada hora

TC-001-008: Alert dispara
    [ ] Quando NM% < 15%, toast "Margin crítica" aparece
    [ ] Cor vermelha, icone ⚠️
    [ ] Dismissível com X button
```

#### 1.3 Comissões Pagas (CP)
```
TC-001-009: Soma correta
    [ ] ML: TVR R$ 100 * 16.5% = R$ 16,50
    [ ] TikTok: TVR R$ 100 * 5% = R$ 5,00
    [ ] Shopee: TVR R$ 100 * 5.3% = R$ 5,30
    [ ] CP Total = R$ 26,80

TC-001-010: Breakdown por marketplace
    [ ] Tabela com [Marketplace | Comissão | %]
    [ ] Somas batem com total
    [ ] Hover mostra composição (base + TI + frete)

TC-001-011: Alert > 25%
    [ ] Se marketplace tem comissão > 25%, alert amber
    [ ] "Comissão alta em [Marketplace]"
```

#### 1.4 Sales Last 24h (SL24)
```
TC-001-012: Contagem correta
    [ ] 48 pedidos completados últimas 24h
    [ ] Mostrado como "48 vendas"
    [ ] Breakdown: ML 20 (41.7%) | TikTok 15 (31.2%) | Shopee 10 (20.8%) | Amazon 2 (4.2%) | Magalu 1 (2.1%)

TC-001-013: Sparkline por hora
    [ ] 24 barras (0-23h)
    [ ] Altura proporcional ao número de pedidos
    [ ] Tooltip: "2h: 3 vendas"

TC-001-014: Trending
    [ ] Comparar vs 24h anterior
    [ ] Se 48 pedidos hoje vs 44 ontem = +9.1%
    [ ] Seta verde ↑

TC-001-015: Update real-time
    [ ] Novo pedido entra → SL24 aumenta em 1
    [ ] Sparkline se estende (nova hora se passou meia-noite)
```

#### 1.5 Average Order Value (AOV)
```
TC-001-016: Cálculo
    [ ] TVR R$ 650, SL24 = 48
    [ ] AOV = 650 / 48 = R$ 13,54

TC-001-017: Breakdown por marketplace
    [ ] ML: R$ 25,00 | TikTok: R$ 10,00 | Shopee: R$ 15,00 | etc
    [ ] Marketplace com maior AOV: destaque (gold star)

TC-001-018: Trending
    [ ] Mostrar vs 7d média
    [ ] Se 7d média = R$ 12,50, hoje R$ 13,54 = +8.3%
```

#### 1.6 Return Rate (RR%)
```
TC-001-019: Cálculo
    [ ] 48 pedidos, 2 devoluções
    [ ] RR% = 2/48 * 100 = 4.17%

TC-001-020: Threshold
    [ ] RR% < 2%: verde
    [ ] RR% 2-5%: amber
    [ ] RR% > 5%: vermelho

TC-001-021: Alert
    [ ] Se RR% > 5%, toast warning
    [ ] "Taxa de devolução alta"

TC-001-022: Trending
    [ ] Sparkline com 7d SMA
    [ ] Se sobe > 20% vs 7d, flag "⚠️ aumentando"
```

#### 1.7 Layout & Responsiveness
```
TC-001-023: Desktop 1920px
    [ ] 4 cards por linha
    [ ] 2 linhas (4 primeiros, depois 2 restantes)
    [ ] Gutter 24px

TC-001-024: Tablet 768px
    [ ] 2 cards por linha
    [ ] 3 linhas
    [ ] Gutter 16px

TC-001-025: Mobile 375px
    [ ] 1 card por linha
    [ ] 6 linhas (card stacked)
    [ ] Texto não trunca, wraps corretamente

TC-001-026: Orientation change
    [ ] iPhone landscape → layout muda para 2 cols
    [ ] Sem conteúdo loss
    [ ] Suave transition
```

#### 1.8 Performance
```
TC-001-027: Load time
    [ ] LCP < 1.5s
    [ ] Lighthouse: Performance >= 85

TC-001-028: Interaction
    [ ] FID < 100ms
    [ ] Click em card → resposta < 100ms

TC-001-029: Layout shift
    [ ] CLS < 0.1
    [ ] Cards não se movem durante load

TC-001-030: Memory
    [ ] Initial: ~30MB
    [ ] After 1h session: ainda ~30MB (no leaks)
    [ ] Task manager: % CPU < 5% idle
```

#### 1.9 Accessibility
```
TC-001-031: ARIA labels
    [ ] Cada card tem aria-label descritivo
    [ ] "Total Vendor Revenue, R$ 45.230,50"

TC-001-032: Keyboard navigation
    [ ] Tab: navega entre cards
    [ ] Enter/Space: expandir dropdown
    [ ] Escape: fechar dropdown

TC-001-033: Screen reader
    [ ] NVDA lê cards corretamente
    [ ] "Card 1 of 6, Total Vendor Revenue..."
    [ ] Valor lido em português

TC-001-034: Color contrast
    [ ] Text vs background >= 4.5:1
    [ ] Checksum com WebAIM contrast checker

TC-001-035: Lighthouse a11y
    [ ] Score >= 90
    [ ] No acessibility violations
```

### Sign-off
```
FEATURE-001 PASSED:
- [ ] Todos TC-001-* passaram
- [ ] Performance benchmarks atingidos
- [ ] Accessibility score >= 90
- [ ] Responsiveness testado (desktop/tablet/mobile)
- [ ] Production-ready

QA Lead: ________________  Data: ________
Dev Lead: _______________  Data: ________
```

---

## FEATURE-002: MARKETPLACE BREAKDOWN

### Test Cases

#### 2.1 Tabela/Cards view
```
TC-002-001: Render correto
    [ ] 5 linhas (um por marketplace)
    [ ] Colunas: Marketplace | Revenue | Commission | Margin% | Orders
    [ ] Valores formatados (R$ para moeda, % para percentage)
    [ ] Total row: soma de todas as colunas

TC-002-002: Valores corretos
    [ ] ML: Revenue R$ 500, Commission R$ 82.50, Margin 83.5%, Orders 20
    [ ] Validar com cálculos manuais

TC-002-003: Proportions
    [ ] % contribution exibido (barras stacked ou badges)
    [ ] ML 76.9%, TikTok 23.1% (soma = 100% ±0.1%)
    [ ] Cores temáticas por marketplace
```

#### 2.2 Sorting
```
TC-002-004: Default sort
    [ ] Default: por Revenue DESC (maior para menor)
    [ ] ML primeiro (R$ 500), TikTok segundo (R$ 150)

TC-002-005: Clicável headers
    [ ] Click em "Revenue": sort ASC → DESC → ASC
    [ ] Icons ↑/↓ aparecem
    [ ] Click em "Commission": sort por comissão

TC-002-006: Multi-sort
    [ ] Sort por Revenue, depois por Margin
    [ ] Ou apenas último sort (depende de UX decision)
```

#### 2.3 Filtering
```
TC-002-007: Filter by status
    [ ] Toggle "Ativo/Inativo"
    [ ] Ativo: mostra todos 5 marketplace
    [ ] Inativo: esconde marketplace inativos (se houver)

TC-002-008: Filter by period
    [ ] Radio: 24h (default) / 7d / 30d
    [ ] Valores recalculam (TVR diferente em cada período)
    [ ] Trending muda

TC-002-009: Filtro reapplied
    [ ] After filter, página é instável? NÃO
    [ ] No flicker, smooth transition
```

#### 2.4 Drill-down
```
TC-002-010: Click marketplace
    [ ] Mostra últimos 10 pedidos
    [ ] Colunas: Order ID | Amount | Commission | Status | Date
    [ ] Back button volta para overview

TC-002-011: Pedido expandido
    [ ] Click em pedido → mostra detalhes
    [ ] Fees breakdown (base, TI, frete)
    [ ] Return status se aplicável
```

### Sign-off
```
FEATURE-002 PASSED:
- [ ] Todos TC-002-* passaram
- [ ] Sorting & filtering funcionam
- [ ] Drill-down funciona
- [ ] Responsiveness ok

QA Lead: ________________  Data: ________
```

---

## FEATURE-003: TIMELINE / HISTÓRICO

### Test Cases

#### 3.1 Charts render
```
TC-003-001: Revenue chart
    [ ] 24 barras (0-23h)
    [ ] Altura proporcional a revenue/hora
    [ ] Cor azul com gradient
    [ ] Tooltip: hora + valor + % do total

TC-003-002: Commission chart
    [ ] Area chart com gradient transparente
    [ ] Valores cumulativos
    [ ] Linha no topo mostra total

TC-003-003: Margin chart
    [ ] Line chart com 24 pontos
    [ ] Threshold linha vermelha em 15%
    [ ] Cor dinâmica (verde >20%, amber, vermelho <15%)

TC-003-004: Marketplace overlay
    [ ] Toggle para breakdown por marketplace
    [ ] Cores consistent com resto da UI
    [ ] Legenda clicável para toggle on/off
```

#### 3.2 Performance
```
TC-003-005: Render speed
    [ ] Charts renderizam < 500ms

TC-003-006: Animation smoothness
    [ ] Quando dados atualizam, transição suave 1s
    [ ] Não causa layout shift

TC-003-007: Interaction responsiveness
    [ ] Hover: tooltip aparece < 100ms
    [ ] Zoom/pan: suave (se implementado)
```

### Sign-off
```
FEATURE-003 PASSED:
- [ ] Todos TC-003-* passaram
- [ ] Charts visualmente corretos
- [ ] Performance ok

QA Lead: ________________  Data: ________
```

---

## FEATURE-004: TARIFAS MARKETPLACE

### Test Cases

#### 4.1 Tabela principal
```
TC-004-001: Render correto
    [ ] 5 linhas com tarifas corretas
    [ ] ML: 16.5% + 0.5% TI = 17.0%
    [ ] TikTok: 5.0%
    [ ] Shopee: 3% + 1.5% + 0.8% = 5.3%
    [ ] Amazon: 7% + 1.5% = 8.5%
    [ ] Magalu: 4% + 0.5% + 0.5% = 5.0%

TC-004-002: Sync status
    [ ] "Last Updated: 2026-03-06 14:23 UTC"
    [ ] Timestamp reflete última sincronização com API

TC-004-003: Edição manual
    [ ] Click em célula → input aparece
    [ ] Tipo number, 0-100 permitido
    [ ] Save/Cancel buttons
    [ ] Total% recalcula automaticamente
    [ ] Override é local (não persiste)
```

#### 4.2 Simulação
```
TC-004-004: Calcular
    [ ] Input: "R$ 1.000,00"
    [ ] ML: Gross 1000, Commission 170, Net 830, Margin 83%
    [ ] TikTok: 1000, 50, 950, 95%
    [ ] Validar com calculadora manual

TC-004-005: Recomendação
    [ ] Destaca marketplace com melhor margin (ouro)
    [ ] "Foco em TikTok (95% margin)"

TC-004-006: Dinâmico
    [ ] Mude input para R$ 5.000
    [ ] Valores recalculam imediatamente
    [ ] Sem lag
```

### Sign-off
```
FEATURE-004 PASSED:
- [ ] Tarifas corretas (validar com APIs)
- [ ] Cálculos bate com manual
- [ ] Simulador funciona

QA Lead: ________________  Data: ________
```

---

## FEATURE-005: ALERT SYSTEM

### Test Cases

#### 5.1 Alerts disparam
```
TC-005-001: Margin < 15%
    [ ] NM% cai para 14%
    [ ] Toast vermelho aparece: "⚠️ Margin < 15%"
    [ ] Persiste até dismiss
    [ ] Sound alert (se ativo)

TC-005-002: Commission > 25%
    [ ] Commission em um marketplace > 25%
    [ ] Alert amber: "Comissão alta em [Marketplace]"
    [ ] "View Tariffs" button funciona

TC-005-003: Sync offline
    [ ] Simular desconexão de internet
    [ ] Banner amber: "📴 Offline - dados de 2h atrás"
    [ ] Timestamp atualiza

TC-005-004: API desconectada
    [ ] Mock API responde com erro
    [ ] Badge vermelho próximo ao marketplace
    [ ] Tooltip: "ML desconectado há 5min"
    [ ] Retry automático a cada 30s
```

#### 5.2 Dismiss & Snooze
```
TC-005-005: Dismiss
    [ ] X button no toast
    [ ] Alert desaparece imediatamente

TC-005-006: Snooze 1h
    [ ] "Snooze 1h" button
    [ ] Toast desaparece
    [ ] Se mesmo alert dispara em < 1h, não mostrar
    [ ] Após 1h, mostrar novamente se ainda aplicável

TC-005-007: Local storage
    [ ] localStorage['snoozed_alerts'] contém snoozes
    [ ] Persiste após reload da página
```

#### 5.3 Alert history
```
TC-005-008: Dropdown
    [ ] Icon/badge em navbar
    [ ] Click → dropdown com últimas 10 alerts
    [ ] Timestamp, severity, ação

TC-005-009: Clear history
    [ ] Button "Clear all"
    [ ] Deleta histórico localmente
```

### Sign-off
```
FEATURE-005 PASSED:
- [ ] Todos os alerts disparam corretamente
- [ ] Dismiss & snooze funcionam
- [ ] Alert history ok

QA Lead: ________________  Data: ________
```

---

## FEATURE-006: DARK MODE

### Test Cases

#### 6.1 Sistema detection
```
TC-006-001: Detect system
    [ ] System em dark mode
    [ ] Dashboard carrega em dark theme
    [ ] Sem FOUC (flash of unstyled content)

TC-006-002: Detect light
    [ ] System em light mode
    [ ] Dashboard carrega em light theme

TC-006-003: No system preference
    [ ] Default para light
```

#### 6.2 Manual toggle
```
TC-006-004: Settings toggle
    [ ] Settings page (ou navbar icon)
    [ ] Toggle: Light / Dark
    [ ] Estado persiste em localStorage

TC-006-005: Override system
    [ ] System = dark, user escolhe light
    [ ] Dashboard em light (override funciona)
    [ ] localStorage['theme-preference'] = 'light'
```

#### 6.3 Colors & contrast
```
TC-006-006: Dark theme colors
    [ ] Background: #000000 ou próximo
    [ ] Text: #f5f5f7
    [ ] Contrast >= 4.5:1 (WebAIM checker)

TC-006-007: Light theme colors
    [ ] Background: #ffffff
    [ ] Text: #1d1d1d
    [ ] Contrast >= 4.5:1

TC-006-008: Component theming
    [ ] Cards: dark gray em dark mode
    [ ] Charts: cores visíveis em ambos
    [ ] Tables: alternating rows visible
    [ ] Inputs: border color ok

TC-006-009: Images & icons
    [ ] SVG icons: currentColor (automático contraste)
    [ ] Logos: visíveis em ambos temas
    [ ] Não invertidas desnecessariamente
```

#### 6.4 Transitions
```
TC-006-010: Smooth transition
    [ ] Toggle dark/light: transição 0.3s
    [ ] Suave, sem flicker

TC-006-011: Prefers-reduced-motion
    [ ] System settings: reduced motion = ON
    [ ] Toggle: sem transição (instant)
```

### Sign-off
```
FEATURE-006 PASSED:
- [ ] Dark & light mode funcionam
- [ ] Contrast >= 4.5:1
- [ ] Persistence ok

QA Lead: ________________  Data: ________
```

---

## FEATURE-007: REAL-TIME SYNC

### Test Cases

#### 7.1 Connection & latency
```
TC-007-001: WebSocket connection
    [ ] DevTools: WS connection estabelecida
    [ ] Connect em < 1s
    [ ] Heartbeat a cada 30s (keep-alive)

TC-007-002: Latência < 500ms
    [ ] Adicionar pedido em backend
    [ ] Timestamp: backend (T1) - frontend (T2) < 500ms
    [ ] Testar 20 pedidos, calcular P95

TC-007-003: Fallback polling
    [ ] Se WebSocket falha, usar polling 100ms
    [ ] Ainda < 500ms
    [ ] Network tab: requests a cada 100ms

TC-007-004: Batching
    [ ] Múltiplos updates: máximo 1/s (não spam)
    [ ] Se 10 pedidos chegam em 100ms: batch em 1 update
```

#### 7.2 Update cascade
```
TC-007-005: Flow completo
    [ ] Novo pedido em ML API
    [ ] → Agregador fetch (5 min)
    [ ] → Upsert raw_orders
    [ ] → Recalcula hourly_metrics
    [ ] → Broadcast WebSocket
    [ ] → Frontend recebe
    [ ] → Redux/Zustand update
    [ ] → Re-render cards
    [ ] Total < 500ms

TC-007-006: Multiple updates
    [ ] Pedir 100 pedidos simultâneos
    [ ] Cada um < 500ms latência
    [ ] Nenhum é perdido
    [ ] TVR final correto
```

#### 7.3 Error handling
```
TC-007-007: Connection refused
    [ ] Backend offline
    [ ] Retry automático: 5s, 10s, 30s
    [ ] Máximo 3 tentativas
    [ ] Alert: "Erro ao sincronizar, retentando..."

TC-007-008: Timeout
    [ ] Simular slow network (throttle 10 Mbps)
    [ ] Se timeout > 5s, retry
    [ ] Não perde dados

TC-007-009: Reconnect
    [ ] Backend volta online
    [ ] Detecta automático
    [ ] Refetch últimos dados
    [ ] Sem duplicatas
```

### Sign-off
```
FEATURE-007 PASSED:
- [ ] Latência < 500ms (P95)
- [ ] Update cascade correto
- [ ] Error handling ok
- [ ] Load test 100 updates/s: passed

QA Lead: ________________  Data: ________
```

---

## FEATURE-008: OFFLINE SUPPORT

### Test Cases

#### 8.1 Service Worker & cache
```
TC-008-001: SW registration
    [ ] DevTools: Application > Service Workers
    [ ] Status: "activated and running"
    [ ] Cache Storage: "dashboard-cache-v1" existe

TC-008-002: IndexedDB storage
    [ ] DevTools: Application > IndexedDB
    [ ] Database: "dashboardCache"
    [ ] Stores: "hourly_metrics", "daily_metrics"
    [ ] Dados: últimas 24h

TC-008-003: Cache strategy
    [ ] Network-first: tenta servidor primeiro
    [ ] Se fail: usa cache
    [ ] Headers: Cache-Control validados
```

#### 8.2 Offline detection & stale state
```
TC-008-004: Detectar offline
    [ ] Desconectar internet (DevTools)
    [ ] Dashboard mostra cached data
    [ ] Banner: "📴 Offline - dados de 2h atrás"

TC-008-005: Stale state visual
    [ ] Cards: dim/opacity reduzida
    [ ] Text: "Último update: 2h atrás"
    [ ] Cor: amber background banner

TC-008-006: Funcionalidade offline
    [ ] Pode clicar em cards (expandir)
    [ ] Pode mudar dark mode
    [ ] Export funciona (com cached data)
    [ ] Não pode editar tarifas (read-only offline)
```

#### 8.3 Reconnect sync
```
TC-008-007: Detectar reconexão
    [ ] Reconectar internet
    [ ] Evento "online" detectado
    [ ] Imediatamente start fetch para dados novos

TC-008-008: Sync automático
    [ ] Fetch últimos dados
    [ ] Comparar timestamps: servidor > cache
    [ ] Update cards com dados novos
    [ ] Fade out stale, fade in novo (1s)

TC-008-009: Sem dados perdidos
    [ ] Durante offline, usuario não fez mudanças (read-only)
    [ ] Ao sync: nenhum conflito
    [ ] Dados bateam com servidor (100%)
```

#### 8.4 Size & expiration
```
TC-008-010: Cache size
    [ ] 24h de dados: < 10MB
    [ ] IndexedDB quota: 50MB disponível
    [ ] Não exceeder limite

TC-008-011: Auto-expire
    [ ] Dados > 24h: auto-deletados
    [ ] Cron job/service worker: check diariamente
    [ ] DevTools: verificar que dados antigos sumem
```

### Sign-off
```
FEATURE-008 PASSED:
- [ ] Service Worker funciona
- [ ] IndexedDB cache ok
- [ ] Offline mode funcional
- [ ] Sync automático ao reconectar

QA Lead: ________________  Data: ________
```

---

## FEATURE-009: RESPONSIVE DESIGN

### Test Cases

#### 9.1 Desktop (1920px+)
```
TC-009-001: Layout desktop
    [ ] Chrome DevTools: Desktop 1920x1080
    [ ] 4 cards por linha
    [ ] 2 linhas totais
    [ ] Gutter 24px
    [ ] No horizontal scroll

TC-009-002: Charts & tables
    [ ] Charts: full width
    [ ] Table: visível inteira (sem scroll horizontal)

TC-009-003: Touch targets
    [ ] Buttons: >= 44x44px (ok para mouse)
    [ ] Hover: visual feedback
```

#### 9.2 Tablet (768-1024px)
```
TC-009-004: Layout tablet
    [ ] iPad Pro 1024x768
    [ ] 2 cards por linha
    [ ] 3 linhas
    [ ] Gutter 16px

TC-009-005: Table
    [ ] Scroll horizontal permitido
    [ ] Headers sticky (frozen coluna primeira)

TC-009-006: Touch-friendly
    [ ] Buttons: >= 44x44px
    [ ] Spacing: 8px entre elementos
    [ ] Tap feedback visível
```

#### 9.3 Mobile (<768px)
```
TC-009-007: Layout mobile
    [ ] iPhone 12 375x812
    [ ] 1 card por linha
    [ ] Full width menos padding 16px
    [ ] Cards stackados

TC-009-008: Cards mobile
    [ ] Texto não trunca, wraps
    [ ] Imagens scale down

TC-009-009: Tables mobile
    [ ] Cards estilo (key: value)
    [ ] Vertical layout
    [ ] Readable

TC-009-010: Charts mobile
    [ ] Height 200px
    [ ] Horizontal scroll permitido
    [ ] Swipe to navigate

TC-009-011: Inputs mobile
    [ ] Font-size >= 16px (prevent zoom on focus)
    [ ] Touch targets >= 44x44px
```

#### 9.4 Orientation changes
```
TC-009-012: Portrait → Landscape
    [ ] iPhone: rotate device
    [ ] Layout muda de 1-col para 2-col
    [ ] Suave, sem content loss
    [ ] Sem horizontal scroll

TC-009-013: Landscape → Portrait
    [ ] Mude back
    [ ] Volta para 1-col
    [ ] Suave
```

#### 9.5 Lighthouse mobile
```
TC-009-014: Lighthouse
    [ ] Mobile score >= 90
    [ ] Performance >= 85
    [ ] Accessibility >= 90
    [ ] Best practices >= 90
    [ ] SEO >= 90 (opcional para dashboard)

TC-009-015: Web Vitals
    [ ] LCP < 2.5s (mobile target)
    [ ] FID < 100ms
    [ ] CLS < 0.1
```

### Sign-off
```
FEATURE-009 PASSED:
- [ ] Desktop layout ok
- [ ] Tablet layout ok
- [ ] Mobile layout ok
- [ ] Lighthouse mobile >= 90

QA Lead: ________________  Data: ________
```

---

## FEATURE-010: EXPORT & REPORTING (P1)

### Test Cases

#### 10.1 Export CSV
```
TC-010-001: Generate CSV
    [ ] Click "Export CSV"
    [ ] Dialog: "Saving marketplace-report-2026-03-06.csv"
    [ ] File downloads

TC-010-002: CSV format
    [ ] Open em Excel
    [ ] Encoding UTF-8 ok
    [ ] Headers: Marketplace, Revenue, Commission, Margin%, Orders
    [ ] Dados: 5 linhas + header + total

TC-010-003: Values
    [ ] ML: 500, 82.5, 83.5%, 20
    [ ] Totals: soma correta
    [ ] RFC 4180 compliant
```

#### 10.2 Export PDF
```
TC-010-004: Generate PDF
    [ ] Click "Export PDF"
    [ ] Dialog: "Generating report..."
    [ ] PDF downloads: "dashboard-report-2026-03-06.pdf"

TC-010-005: PDF content
    [ ] Página 1: KPI cards (TVR, Margin, Commission, etc)
    [ ] Página 2: Breakdown table
    [ ] Página 3: Charts (revenue, margin, commission)
    [ ] Página 4: Tariffs
    [ ] Footer: "Generated 2026-03-06 14:35 UTC"

TC-010-006: Printable
    [ ] Print PDF (Cmd+P)
    [ ] Layouts ok
    [ ] Sem elementos desnecessários
```

#### 10.3 Share link
```
TC-010-007: Generate share
    [ ] Click "Share"
    [ ] Modal: "Share your dashboard"
    [ ] Link: https://dashboard.app/share/ABC123
    [ ] Copy button

TC-010-008: Expiração
    [ ] 7 dias expiração
    [ ] Ou configurável em settings
    [ ] Link após 7 dias: "Expired"

TC-010-009: Permissões
    [ ] Read-only: sem edit buttons
    [ ] Sem export/share buttons
    [ ] Footer: "Read-only shared view"
```

### Sign-off
```
FEATURE-010 PASSED:
- [ ] CSV export funciona
- [ ] PDF export funciona
- [ ] Share link funciona
- [ ] (P1 - Post-MVP)

QA Lead: ________________  Data: ________
```

---

## INTEGRATION TESTS

### Test Cases

#### INT-001: End-to-end user flow
```
[ ] User login
[ ] Dashboard loads (< 1.5s)
[ ] Vê KPI cards corretos
[ ] Clica em marketplace → breakdown
[ ] Clica em tarifas → simulador funciona
[ ] Edita override → calcula
[ ] Gera alert (margin baixa) → dismiss
[ ] Troca para dark mode → cores ok
[ ] Offline (DevTools) → cached data
[ ] Online → sync automático
[ ] Export CSV → abre em Excel
[ ] Share link → read-only ok
```

#### INT-002: Real-time multi-user
```
[ ] 2 browsers: mesma conta
[ ] Browser 1: novo pedido chega
[ ] Browser 1 vê atualização
[ ] Browser 2: ???
    - [ ] Se WebSocket compartilhado: Browser 2 vê também
    - [ ] Se não: Browser 2 vê após próxima sync (5 min)
    - [ ] (Depende de design decision)
```

#### INT-003: API integration
```
[ ] ML API: 10 pedidos → Dashboard mostra 10
[ ] TikTok API: 10 pedidos → Dashboard mostra 10
[ ] Shopee API: 10 pedidos → Dashboard mostra 10
[ ] Amazon API: 10 pedidos → Dashboard mostra 10
[ ] Magalu API: 10 pedidos → Dashboard mostra 10
[ ] Total: 50 pedidos, TVR correto
```

---

## PERFORMANCE LOAD TEST

### Test Setup
```
Load: 100 updates/second
Duration: 5 minutes
Success Criteria:
- [ ] P95 latência < 500ms
- [ ] Error rate < 0.5%
- [ ] No timeouts
- [ ] Memory stable (no leaks)
- [ ] CPU < 80% sustained
```

### Results Template
```
Load test: 100 updates/s for 5min

┌─────────────────────────────────────┐
│ Latency (ms)                        │
├─────────────────────────────────────┤
│ Min:     [____]                     │
│ P50:     [____]                     │
│ P95:     [____]  ← MUST BE < 500ms │
│ P99:     [____]                     │
│ Max:     [____]                     │
└─────────────────────────────────────┘

Errors: [____] / 30000 requests
Error rate: [____]% ← MUST BE < 0.5%

Memory:
  Start: [____] MB
  End:   [____] MB
  Δ:     [____] MB ← MUST BE < 5MB

CPU: [____]% average ← MUST BE < 80%

PASSED: [ ] YES [ ] NO
```

---

## SECURITY & COMPLIANCE

### Checklist
```
[ ] LGPD: Dados vendedor são PII (seguro)
[ ] Auth: Vendedor só vê seus dados (não pode acessar outros)
[ ] TLS: Todas conexões >= TLS 1.2
[ ] CORS: Configurado corretamente (não ["*"])
[ ] XSS: Nenhuma injeta input (sanitize)
[ ] SQL injection: ORM (Sequelize/SQLAlchemy) usado
[ ] CSRF: Tokens em POST/PUT requests
[ ] Encryption: Dados sensíveis encriptados em repouso (AES-256)
[ ] Secrets: Não em code (env vars apenas)
[ ] Logging: Senhas/tokens não logadas
[ ] API rate limit: Aplicado (prevent DDoS)
[ ] Backups: Diários, testadas restauração
```

---

## DEPLOYMENT CHECKLIST

### Pre-deployment
```
[ ] Código: reviewed & tested
[ ] Migrations: rolled out com down script
[ ] Secrets: setadas em production
[ ] Monitoring: DataDog/Sentry configurado
[ ] Alerts: thresholds setadas
[ ] Runbook: documented
[ ] Rollback plan: pronto
[ ] Stakeholders: notificados
```

### Post-deployment
```
[ ] Health checks: passando
[ ] Logs: sem erros
[ ] Alerts: sem anomalias
[ ] Performance: no regressions
[ ] Users: feedback ok
[ ] Data: sync ok
```

---

## FINAL SIGN-OFF

```
QA SIGN-OFF:
Product: Dashboard Apple
Version: 1.0.0
Date: ________________

All features tested and passed:
[ ] FEATURE-001 (KPI Cards)
[ ] FEATURE-002 (Breakdown)
[ ] FEATURE-003 (Timeline)
[ ] FEATURE-004 (Tarifas)
[ ] FEATURE-005 (Alerts)
[ ] FEATURE-006 (Dark Mode)
[ ] FEATURE-007 (Real-time Sync)
[ ] FEATURE-008 (Offline)
[ ] FEATURE-009 (Responsive)
[ ] FEATURE-010 (Export) - P1

Performance: PASSED
Security: PASSED
Accessibility: PASSED
Compliance: PASSED

Status: APPROVED FOR PRODUCTION ✅

QA Lead: _________________  Assinatura: _________
Dev Lead: ________________  Assinatura: _________
Product Owner: ___________  Assinatura: _________
```

---

**QA-CHECKLIST v1.0.0 | Dashboard Apple MVP**
*Generated: 2026-03-06 | Updated: as needed*

