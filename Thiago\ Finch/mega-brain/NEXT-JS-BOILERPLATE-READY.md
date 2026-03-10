# 🚀 Mega Brain Frontend - Next.js 14 Boilerplate

> Production-ready dashboard com React 18, TypeScript, TailwindCSS e Framer Motion

## 📋 Status

✅ **ESTRUTURA COMPLETA** | ✅ **COMPONENTES** | ✅ **HOOKS** | ✅ **STYLING** | ⏳ **DEPLOYMENT**

---

## 📦 O Que Está Incluído

### Project Structure
```
frontend/
├── app/
│   ├── api/              # Backend routes (Next.js API)
│   │   ├── health/
│   │   ├── sales/
│   │   ├── tarifas/
│   │   └── products/
│   ├── components/       # Reusable UI components
│   │   ├── Header.tsx
│   │   ├── HeroSection.tsx
│   │   ├── Card.tsx
│   │   ├── ChartContainer.tsx
│   │   ├── TarifasGrid.tsx
│   │   ├── TopProducts.tsx
│   │   └── Footer.tsx
│   ├── hooks/            # Custom React hooks
│   │   ├── useSales.ts
│   │   ├── useTariffs.ts
│   │   └── useTheme.ts
│   ├── lib/              # Utilities
│   │   ├── api.ts        # Client SDK
│   │   ├── calc.ts       # Calculations
│   │   └── types.ts      # TypeScript interfaces
│   ├── globals.css       # Tailwind + Custom CSS
│   ├── layout.tsx        # Root layout
│   ├── page.tsx          # Homepage
│   └── providers.tsx     # Theme provider
├── public/               # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── vercel.json          # Vercel deployment config
```

### Componentes Criados

| Componente | Descrição | Features |
|-----------|-----------|----------|
| **Header** | Barra superior fixa | Logo, clock, theme toggle |
| **HeroSection** | 4 cards principais | GMV, Pedidos, Ticket, Conversão |
| **Card** | Componente reutilizável | Trend indicators, icons, variants |
| **ChartContainer** | Wrapper para gráficos | Loading states, titles |
| **TarifasGrid** | Grid 5 colunas | Marketplace fees, real-time updates |
| **TopProducts** | Tabela de top 10 | Rankings, margins, trends |
| **Footer** | Rodapé com status | Version, sync indicator |

### Hooks Customizados

```typescript
// Sales data with SWR caching
useSales(hours = 24)
useSalesDaily()

// Tariffs data with 1h cache
useTariffs()
useTariff(marketplace)

// Theme management
useTheme() // Returns: { theme, toggle, mounted }
```

### API Routes

| Endpoint | Método | Cache | Response |
|----------|--------|-------|----------|
| `/api/health` | GET | No | `{ status, version }` |
| `/api/sales` | GET | No | `SalesData` |
| `/api/sales/daily` | GET | No | `SalesData` |
| `/api/tarifas` | GET | 1h | `TarifaData[]` |
| `/api/tarifas/:marketplace` | GET | 1h | `TarifaData` |

### Styling Features

- **TailwindCSS** utility-first
- **Dark mode** (system preference + toggle)
- **Custom CSS variables** para temas
- **Glassmorphism** components
- **Responsive breakpoints** (sm, md, lg, xl)
- **Animations** (Framer Motion)
- **Custom scrollbar** styling

---

## 🛠️ Setup Local

### 1. Clone e instale

```bash
cd mega-brain/frontend
npm install
# ou
yarn install
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.local.example .env.local
```

Edite `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### 3. Rodar em desenvolvimento

```bash
npm run dev
```

Acesse: **http://localhost:3000**

### 4. Build para produção

```bash
npm run build
npm start
```

---

## 🎨 Customização

### Cores (Tailwind)

Edit `tailwind.config.ts`:
```typescript
colors: {
  primary: { 50, 100, 500, 600, 700, 900 },
  secondary: { 50, 500, 600, 700, 900 },
  accent: { 50, 500, 600, 700 },
}
```

### CSS Variables

Edit `app/globals.css`:
```css
:root {
  --bg-primary: #ffffff;
  --text-primary: #0f172a;
  --accent: #0ea5e9;
}
```

### Tema (Light/Dark)

Tema automático baseado em preferência do sistema. Click no ícone de sol/lua para toggle manual.

---

## 📊 Tipos TypeScript

```typescript
// Sales
interface SalesData {
  gmv: number
  orders: number
  avgTicket: number
  trend: number
  lastUpdated: string
  history: SalesMetric[]
}

// Tarifas
interface TarifaData {
  id: string
  name: string
  marketplace: 'mercadolivre' | 'shopee' | 'amazon' | 'b2w' | 'próprio'
  commission: number
  totalFee: number
  lastUpdated: string
}

// Products
interface ProductData {
  id: string
  sku: string
  name: string
  price: number
  cost: number
  margin: number
  sales24h: number
  revenue24h: number
  trend: 'up' | 'down' | 'neutral'
}
```

---

## 🔄 Data Fetching (SWR)

```typescript
// Hook automático com cache
const { data, error, isLoading, refresh } = useSales(24)

// Manual refresh
refresh()

// Error handling
if (error) return <div>Erro ao carregar</div>
if (isLoading) return <Skeleton />
```

---

## 🚀 Deployment (Vercel)

### 1. Push para GitHub

```bash
git init
git add .
git commit -m "feat: Next.js 14 boilerplate"
git remote add origin https://github.com/seu-user/mega-brain-frontend.git
git push -u origin main
```

### 2. Connect no Vercel

1. Acesse https://vercel.com/new
2. Selecione repo GitHub
3. Framework = Next.js
4. Build command = `npm run build`
5. Output dir = `.next`
6. Environment: `NEXT_PUBLIC_API_URL=...`
7. Deploy!

### 3. Vercel Preview URL

Após deploy:
- Production: `https://mega-brain-frontend.vercel.app`
- Preview: Automático para cada PR

---

## ✅ Testing Checklist

- [ ] Página carrega sem errors (`npm run build`)
- [ ] Header responsivo (mobile, tablet, desktop)
- [ ] Dark mode toggle funciona
- [ ] Componentes animam suavemente
- [ ] API routes retornam dados (mock)
- [ ] SWR cache funciona
- [ ] Responsive em 3 breakpoints
- [ ] Sem console errors/warnings

---

## 📈 Próximos Passos

1. **Conectar API backend real**
   - Substituir mocks em `/api/`
   - Atualizar `NEXT_PUBLIC_API_URL`

2. **Adicionar gráficos**
   - Recharts já importado
   - Criar componentes: AreaChart, BarChart, LineChart

3. **WebSocket real-time**
   - Implementar em `/api/websocket`
   - Auto-refresh de dados

4. **Autenticação**
   - NextAuth.js integração
   - Proteção de rotas

5. **Analytics**
   - Google Analytics
   - Sentry error tracking

---

## 📝 Scripts Disponíveis

```bash
npm run dev      # Desenvolvimento (http://localhost:3000)
npm run build    # Build para produção
npm start        # Rodar build
npm run lint     # ESLint check
```

---

## 🔐 Segurança

- ✅ CSP headers configurados
- ✅ CORS headers
- ✅ Security headers (X-Frame-Options, etc)
- ✅ SRI para recursos externos
- ✅ No hardcoded secrets
- ✅ Environment variables para sensíveis

---

## 📚 Documentação

- [Next.js 14 Docs](https://nextjs.org/docs)
- [TailwindCSS](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [SWR - React Hooks for Data Fetching](https://swr.vercel.app/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---

## 🤝 Contribuindo

1. Fork o repo
2. Crie uma branch (`git checkout -b feature/novo-componente`)
3. Commit changes (`git commit -am 'feat: novo componente'`)
4. Push (`git push origin feature/novo-componente`)
5. Abra um PR

---

## 📞 Suporte

- Issues: GitHub Issues
- Docs: Ver `/frontend/README.md`
- Vercel Docs: https://vercel.com/docs

---

## 📄 Licença

MIT © Mega Brain

---

## 🎯 Deploy Status

| Ambiente | Status | URL |
|----------|--------|-----|
| Local | ✅ | http://localhost:3000 |
| Vercel | ⏳ | [Setup em progresso...] |
| API Backend | ⏳ | [Conectar depois...] |

---

**Boilerplate criado:** 2026-03-06
**Version:** 0.1.0
**Next.js:** 14.0.0
**React:** 18.2.0
**TypeScript:** 5.3.0

