# 📊 Dashboard Deployment Options

> **Status:** Dashboard v5.0 Pronto para Deploy
> **Data:** 2026-03-05
> **Localização Atual:** http://localhost:8000 (Python HTTP Server)
> **Repositório:** GitHub (rastreado em main)

---

## 🎯 O Que Mudou no Dashboard v5.0

### KPIs Adicionados

```
✅ FINANCEIRO (24h):
  └─ GMV (Faturamento Bruto)
  └─ Taxas Mercado Livre
  └─ Gastos em Ads
  └─ Lucro Líquido

✅ OPERACIONAL:
  └─ Total de Pedidos
  └─ Pedidos Pagos
  └─ Pedidos Cancelados
  └─ Ticket Médio

✅ CFO ANALYTICS (Críticos):
  └─ ROAS (Return on Ad Spend) → Target: ≥ 3:1 ✅
  └─ LTV/CAC Ratio
  └─ Margem Líquida % → Target: ≥ 20% ✅
  └─ CAC (Customer Acquisition) → Target: ≤ 15% da margem

✅ ALERTS AUTOMÁTICOS:
  └─ Alerta se Margem < 20% (crítico)
  └─ Alerta se ROAS < 3:1 (aviso)
  └─ Alerta se Cancelamento > 15% (aviso)
```

### Melhorias Visuais

- ✅ Dark mode completo (GitHub style)
- ✅ Cards coloridos com gradientes
- ✅ Responsive design (mobile + desktop)
- ✅ Auto-refresh 30 segundos
- ✅ Tabela detalhada de pedidos
- ✅ Status badges por pedido

---

## 🚀 OPÇÃO 1: GitHub Pages (RECOMENDADO)

### Pros
- ✅ 100% gratuito
- ✅ Sem servidor necessário
- ✅ CDN global automático
- ✅ Integrado ao repositório
- ✅ Deploy automático em cada push
- ✅ URL bonita: `https://github.com/seu-username/mega-brain/pages`

### Cons
- ❌ Apenas HTML/CSS/JS estático (sem backend)
- ❌ Dados precisam ser auto-contidos ou buscados via fetch

### Como Configurar

```bash
# 1. Na raiz do projeto, criar config
cat > docs/index.html << EOF
[Copiar conteúdo do index.html atual]
EOF

# 2. No GitHub, ir para Settings → Pages
# 3. Source: Deploy from branch
# 4. Branch: main / Folder: /docs

# 5. URL gerada: https://seu-username.github.io/mega-brain/
```

### Status: ✅ Pronto em 5 minutos

---

## 🌐 OPÇÃO 2: Vercel (MELHOR PERFORMANCE)

### Pros
- ✅ Deploy automático em cada push
- ✅ Edge functions (serverless)
- ✅ Analytics integrado
- ✅ Preview deployments
- ✅ Domínio personalizado
- ✅ 100% gratuito para projetos open-source

### Cons
- ❌ Requer conta Vercel
- ❌ Setup inicial mais demorado

### Como Configurar

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Deploy
cd mega-brain
vercel

# 3. Seguir prompt (selecionar projeto, branch, etc)
```

### URL Gerada
```
https://mega-brain.vercel.app/
```

### Status: ✅ Pronto em 10 minutos

---

## 🏠 OPÇÃO 3: Manter em Localhost (DESENVOLVIMENTO)

### Pros
- ✅ Nenhuma configuração
- ✅ Rápido para testes
- ✅ Controle total local

### Cons
- ❌ Não acessível remotamente
- ❌ Vai down quando computador desligar
- ❌ Impossível compartilhar com time

### Status: ✅ Já funcionando (http://localhost:8000)

---

## 📊 OPÇÃO 4: AWS S3 + CloudFront

### Pros
- ✅ Muito rápido (CDN)
- ✅ Escalável
- ✅ Confiável

### Cons
- ❌ Custa $$ (mesmo que pouco)
- ❌ Setup complexo

### Status: ❌ Não recomendado para este caso

---

## 🎯 RECOMENDAÇÃO: GitHub Pages + Vercel (Híbrido)

### Estratégia Ideal

```
┌─────────────────────────────────────────┐
│  Push para GitHub                       │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
GitHub Pages       Vercel Preview
(Production)       (Staging + Preview)
https://...github.io/    https://...vercel.app/
```

### Setup (20 minutos)

**PASSO 1: GitHub Pages**
```bash
cd mega-brain
mkdir -p docs
cp index.html docs/
git add docs/index.html
git commit -m "feat: Deploy dashboard to GitHub Pages"
git push
```

**Depois no GitHub:**
- Settings → Pages
- Source: main/docs
- Save

**Resultado:** `https://seu-user.github.io/mega-brain/`

**PASSO 2: Vercel (Opcional mas recomendado)**
```bash
npm install -g vercel
vercel
# Seguir prompts interativos
```

**Resultado:** `https://mega-brain.vercel.app/`

---

## 📋 Checklist de Deployment

### GitHub Pages (Essencial)
```
[ ] Criar pasta docs/
[ ] Copiar index.html para docs/
[ ] Git add + commit
[ ] Git push
[ ] Ir em GitHub Settings → Pages
[ ] Selecionar main/docs como source
[ ] Aguardar build (2-5 min)
[ ] Testar URL https://seu-user.github.io/mega-brain/
```

### Vercel (Recomendado)
```
[ ] npm install -g vercel
[ ] Conectar GitHub account
[ ] vercel deploy
[ ] Selecionar projeto e branch
[ ] Testar URL https://seu-projeto.vercel.app/
[ ] Configurar domínio personalizado (opcional)
```

---

## 🔄 Fluxo de Atualização

### GitHub Pages (Automático)
```
Developer faz push
       │
       ▼
GitHub Actions roda
       │
       ▼
Deploy automático para GitHub Pages
       │
       ▼
Site atualizado em 2-5 minutos
```

### Vercel (Semi-automático)
```
Developer faz push
       │
       ▼
GitHub webhook notifica Vercel
       │
       ▼
Vercel roda build
       │
       ▼
Preview gerado automaticamente
       │
       ▼
Deploy para production em 30s
```

---

## 💡 O Que o Dashboard Indica

### Seção 1: Saúde Financeira
```
💰 GMV = Total vendido
🏦 Taxas = Quanto Mercado Livre cobra
📢 Ads = Quanto você gastou em publicidade
✅ Lucro Líquido = O que sobra (GMV - Taxas - Ads)
```

### Seção 2: Métricas Operacionais
```
📦 Pedidos = Quantidade total
✅ Pagos = Quantos foram confirmados (%)
❌ Cancelados = Quantos caíram (%)
📈 Ticket Médio = Valor médio por pedido pago
```

### Seção 3: CFO Analytics (CRÍTICA)
```
⚠️ ROAS = Quanto você faturou para cada R$ de ad
   → Se ROAS < 3:1 = Ads estão caros

💡 Margem % = Quanto sobra em percentual
   → Se < 20% = Negócio não está saudável

🎯 CAC = Custo para adquirir cada cliente
   → Se > 15% da margem = Muito caro
```

### Alerts Automáticos
```
🔴 CRÍTICO: Margem < 20% (impossível escalar)
🟡 AVISO: ROAS < 3:1 (ads não estão pagando)
🟠 AVISO: Cancelamento > 15% (algo errado com produto/shipping)
```

---

## 🎬 PRÓXIMOS PASSOS (Recomendação)

### Hoje (Imediato)
1. ✅ Escolher: GitHub Pages OU Vercel OU Híbrido
2. ✅ Se GitHub Pages: 5 min de setup
3. ✅ Se Vercel: 10 min de setup
4. ✅ Testar URL

### Esta Semana
1. ✅ Validar dados (confirmar GMV, fees, ads)
2. ✅ Adicionar autenticação (proteger dashboard)
3. ✅ Conectar ao Mercado Livre API em tempo real (em vez de JSON estático)

### Este Mês
1. ✅ Adicionar histórico (gráficos de 30 dias)
2. ✅ Integrar com CFO agent para análises automáticas
3. ✅ Criar alertas via Slack/Email

---

## 🔐 Segurança

### Aviso Importante
```
⚠️ Dashboard atual mostra dados públicos (sem auth)
⚠️ Se for publicar, adicionar autenticação ANTES

Opções:
1. GitHub Private Repo + GitHub Pages (requerer login)
2. Vercel com senha (vercel password)
3. Cloudflare Workers (proxy com auth)
```

---

## 📌 Decisão Final: CEO

### Recomendação AIOX: **Vercel**

**Por quê?**
- ✅ Mais rápido que GitHub Pages
- ✅ Preview automático de cada push
- ✅ Suporta funções serverless (para análises futuras)
- ✅ Analytics integrado
- ✅ Não precisa de pasta docs

**Alternativa:** GitHub Pages + Vercel (usar Vercel para staging, GitHub Pages para prod)

---

**Senhor, qual opção você prefere? Vou deploitar em 10 minutos.**

1. **GitHub Pages** (simples, grátis)
2. **Vercel** (recomendado, melhor perf)
3. **Híbrido** (ambos para redundância)
4. **Manter local** (por enquanto)
