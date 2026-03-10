╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               🍎 NOVO DASHBOARD APPLE-STYLE - BRIEFING EXECUTIVO             ║
║                                                                              ║
║         Redesign Premium com Vendas Ao Vivo + Tarifas em Real-Time           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

---

## 🎯 OBJETIVO

Criar dashboard premium estilo Apple que mostre:
- **Vendas ao vivo** em tempo real
- **Tarifas de marketplace** atualizadas via API
- **Margem de lucro** calculada dinamicamente
- **Alertas visuais** para mudanças críticas

**Inspiração:** apple.com, App Store design system

---

## 👥 SQUAD DESIGNADO

| Agente | Responsabilidade | Prioridade |
|--------|-----------------|-----------|
| @UX-EXPERT | Design Apple-style (wireframes + Figma) | P0 |
| @PO | Escopo e prioridades | P0 |
| @ARCHITECT | Schema de dados ao vivo | P1 |
| @DATA-ENGINEER | Pipeline de vendas real-time | P1 |
| @DEV | Implementação React/Next | P1 |
| @QA | Testes de performance + accuracy | P2 |

---

## 🎨 DESIGN APPLE-STYLE

### Características Visuais

```
CORES
├─ Fundo: #FFFFFF (light) / #000000 (dark)
├─ Texto primário: #000000 / #FFFFFF
├─ Cards: rgba(255,255,255,0.8) / rgba(255,255,255,0.1)
└─ Acentos: #007AFF (iOS Blue), #34C759 (Green), #FF3B30 (Red)

TIPOGRAFIA
├─ Heading: SF Pro Display Bold (28px)
├─ Subheading: SF Pro Display Medium (18px)
├─ Body: SF Pro Display Regular (16px)
└─ Monospace: SF Mono (dados numéricos)

LAYOUT
├─ Padding: 20px, 40px, 60px (múltiplos de 20)
├─ Radius: 12px-16px (não sharp corners)
├─ Shadow: Subtle (blur 10px, alpha 0.1)
├─ Spacing: Grid 8px
└─ Full-width sections com safe areas
```

### Componentes Principais

```
1. HEADER
   ├─ Logo "Hugo Jobs"
   ├─ Data/Hora
   └─ Menu contextual (filtros)

2. HERO SECTION
   ├─ Número grande: Vendas de hoje (R$)
   ├─ Sparkline chart (últimas 24h)
   └─ % mudança vs ontem

3. CARDS 3-COLUNA (Glassmorphism)
   ├─ Card 1: Comissões pagas (MercadoLivre)
   ├─ Card 2: Frete total cobrado
   └─ Card 3: Margem líquida %

4. LIVE CHART
   ├─ Gráfico de linha suave (vendas por hora)
   ├─ Hover mostra valores exatos
   └─ Animação de entrada

5. TARIFAS MARKETPLACE
   ├─ Cards com ícone de cada plataforma
   ├─ Comissão % grande
   └─ "Atualizado há X minutos"

6. TOP PRODUTOS
   ├─ Lista com thumbnail + nome
   ├─ Vendas hoje + margem
   └─ Seta para trending up/down

7. FOOTER
   ├─ "Sincronizando..." com spinner
   ├─ Última atualização: HH:MM
   └─ Status da API (🟢 Online / 🔴 Offline)
```

---

## 📊 DADOS - FONTE E ESTRUTURA

### Origem dos Dados

```
VENDAS AO VIVO
├─ Fonte: API MercadoLivre (orders endpoint)
├─ Frequência: A cada 5 minutos
├─ Estrutura: {product_id, quantity, price, timestamp}
└─ Cache: Redis (5min TTL)

TARIFAS
├─ Fonte: MCP mercadolivre/get_commissions
├─ Frequência: A cada 1 hora (ou manual)
├─ Estrutura: {category_id, commission_pct, shipping_fee}
└─ Cache: Redis (1h TTL)

CÁLCULOS
├─ Margem: (price - cost) / price * 100
├─ Comissão: price * commission_pct
├─ Frete: shipping_fee (dinâmico por peso)
└─ Lucro líquido: price - cost - comissão - frete
```

### Schema do Banco (PostgreSQL)

```sql
-- Tabela de vendas ao vivo
CREATE TABLE sales_live (
  id UUID PRIMARY KEY,
  product_id INT,
  product_name VARCHAR(255),
  quantity INT,
  price DECIMAL(10, 2),
  commission DECIMAL(10, 2),
  shipping_cost DECIMAL(10, 2),
  margin_pct DECIMAL(5, 2),
  marketplace VARCHAR(50),
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_sales_timestamp ON sales_live(timestamp DESC);
CREATE INDEX idx_sales_marketplace ON sales_live(marketplace);

-- Tabela de tarifas (snapshot)
CREATE TABLE tariffs_snapshot (
  id UUID PRIMARY KEY,
  marketplace VARCHAR(50),
  category_id INT,
  category_name VARCHAR(255),
  commission_pct DECIMAL(5, 2),
  last_updated TIMESTAMP DEFAULT NOW()
);
```

---

## ⚡ PERFORMANCE

```
REQUISITOS
├─ Carregamento inicial: < 1s
├─ Sincronização de dados: < 500ms
├─ Animações: 60 FPS
├─ Responsivo: iPad (1024px) + Mobile (375px)
└─ Offline support: Últimos 24h de dados em cache

OTIMIZAÇÕES
├─ Code splitting (React Suspense)
├─ Image optimization (WebP + lazy loading)
├─ API batching (2-3 req/seg max)
├─ WebSocket para vendas ao vivo
├─ Service Worker para offline
└─ SWR para data fetching + caching
```

---

## 📱 RESPONSIVIDADE

```
Desktop (1440px)
├─ 3 colunas de cards
├─ Chart em full width
└─ Tabela com scroll horizontal

Tablet (1024px - iPad)
├─ 2 colunas de cards
├─ Chart responsivo
└─ Sidebar colapsável

Mobile (375px - iPhone)
├─ 1 coluna (stacked)
├─ Chart scrollable
├─ Cards em carrossel
└─ Menu em bottom sheet
```

---

## 🔄 FLUXO DE DADOS (Real-Time)

```
MercadoLivre API
    ↓
N8N Webhook (a cada 5min)
    ↓
PostgreSQL (sales_live table)
    ↓
Redis Cache (5min TTL)
    ↓
WebSocket (push to dashboard)
    ↓
React Component (re-render)
    ↓
Smooth animation (spring physics)
    ↓
User vê número atualizar ao vivo ✨
```

---

## 📋 REQUISITOS FUNCIONAIS

- [ ] Dashboard carrega em < 1s
- [ ] Vendas atualizam a cada 5 minutos
- [ ] Tarifas sincronizadas com MercadoLivre API
- [ ] Margem calculada em tempo real
- [ ] Alertas para comissão > 20%
- [ ] Dark mode automático (preferência do sistema)
- [ ] Offline funciona (últimas 24h)
- [ ] Mobile responsivo
- [ ] Temas claros/escuros sem flash
- [ ] Sem lag em gráficos

---

## 🎬 TIMELINE

```
SEMANA 1: Design + Setup
├─ Seg: UX faz wireframes/Figma
├─ Ter: ARCHITECT desenha pipeline
├─ Qua: DEV setup projeto (Next.js + TailwindCSS)
├─ Qui: DATA-ENGINEER implementa ETL
└─ Sex: Code review + ajustes

SEMANA 2: Implementação + Testes
├─ Seg: DEV implementa componentes principais
├─ Ter: Integração com API ML (dados ao vivo)
├─ Qua: Performance optimization + QA testes
├─ Qui: Staging deployment
└─ Sex: Review final, pronto para produção
```

---

## 🛠️ TECH STACK

```
Frontend
├─ Next.js 14 (React 18)
├─ TailwindCSS (utility-first)
├─ Framer Motion (animações)
├─ Recharts (gráficos)
├─ SWR (data fetching)
└─ TypeScript

Backend (Existente)
├─ MCP mercadolivre
├─ PostgreSQL (sales + tariffs)
├─ Redis (cache)
├─ WebSocket (real-time push)
└─ N8N (webhooks)

DevOps
├─ Vercel (hosting Next.js)
├─ Docker (local dev)
└─ GitHub Actions (CI/CD)
```

---

## 📞 PRÓXIMOS PASSOS

1. ✅ UX-EXPERT cria wireframes (Figma link)
2. ✅ PO aprova escopo
3. ✅ ARCHITECT valida pipeline
4. ✅ DEV inicia projeto
5. ✅ DATA-ENGINEER conecta APIs

**Comando para iniciar:**

```
@aiox-master: Orquestra novo Dashboard Apple-Style
├─ UX: Crie wireframes (referência: apple.com design)
├─ PO: Valide escopo (vendas live + tarifas)
├─ ARCHITECT: Valide pipeline de dados
├─ DEV: Setup Next.js + TailwindCSS
└─ DATA-ENGINEER: Conecte APIs (ML, N8N, PostgreSQL)
```

---

## ✨ DIFERENCIAL vs DASHBOARD ATUAL

| Aspecto | Atual | Novo Apple-Style |
|---------|-------|------------------|
| Dados | Estático | Real-time (5min) |
| Design | Genérico | Premium Apple |
| Performance | ~3s | < 1s |
| Mobile | Limitado | Full responsive |
| Dark mode | Manual | Automático |
| Animações | Nenhuma | Smooth + natural |
| Offline | Não | Sim (24h cache) |

---

```
Briefing v1.0
Criado por: JARVIS
Data: 2026-03-06
Status: PRONTO PARA SQUAD
```
