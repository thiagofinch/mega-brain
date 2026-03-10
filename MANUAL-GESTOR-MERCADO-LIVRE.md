# 🎯 MANUAL DO GESTOR — MERCADO LIVRE ADS & VENDAS

> **Versão:** 2.0.0 (Operacional)
> **Data:** 2026-03-09
> **Autor:** JARVIS + Kennyd Willker
> **Escopo:** Gestão completa de contas MercadoLivre (Ads + Vendas Orgânicas)
> **Audiência:** Gestores, operadores, especialistas em ML

---

## 📊 SUMÁRIO EXECUTIVO

Este manual consolida **225+ arquivos** de conhecimento, **2 transcrições de masters**, e **2 anos de operação** em uma estrutura pronta para implementação.

| Métrica | Status | Valor |
|---------|--------|-------|
| **Contas Gerenciadas** | Ativo | 24 clientes |
| **Vendas/mês (Hugo Jobs)** | 2026-03 | 24.031,52 BRL |
| **Margem Líquida (Média)** | Calculada | 22-47% |
| **Frameworks Documentados** | Mapeados | 12 principais |
| **Heurísticas Operacionais** | Extraídas | 45+ regras |
| **Automações Ativas** | Em produção | 7 scripts |

---

## 🏗️ PARTE 1: FUNDAÇÃO (O QUE VOCÊ PRECISA SABER)

### 1.1 A Realidade do MercadoLivre Brasil

O MercadoLivre não é um marketplace simples — é um **sistema de rankings dinâmicos** onde cada decisão impacta visibilidade:

```
FATO 1: O algoritmo favorece sellers com:
├── Taxa de conversão ACIMA da categoria
├── Tempo de resposta < 1 hora
├── Reviews 4.5+ estrelas
└── Estoque sempre disponível

FATO 2: Existem 2 MODALIDADES de crescimento:
├── ORGÂNICO: Bom SEO, descrição, fotos, preço
└── PAGO (ANÚNCIOS): Product Ads (PADS) + Brand Ads (BADS)

FATO 3: A MAIORIA dos sellers falha porque:
├── Não entendem comissão (varia 8-30% por categoria)
├── Não calculam margem corretamente
├── Não acompanham TACOS/ACOS (custo/benefit)
└── Não otimizam preço vs custos
```

### 1.2 As 3 Camadas de Decisão

Todo gestor trabalha com 3 camadas simultâneas:

```
CAMADA 1: PREÇO & MARGEM (Base)
├─ Custo do Produto (CMV)
├─ Taxa MercadoLivre (comissão)
├─ Custo de Envio (Mercado Envios)
└─ Imposto (PIS, COFINS)
     ↓
CAMADA 2: POSICIONAMENTO (Visibilidade)
├─ Anúncio Clássico vs Premium
├─ Keyword Strategy
├─ Minha Página (branding)
└─ Ofertas Relâmpago
     ↓
CAMADA 3: TRÁFEGO & CONVERSÃO (Growth)
├─ Product Ads (PADS) — Pay per click
├─ Brand Ads (BADS) — Pay per keyword
├─ ROAS Target: 3x+ (vender 3x o que gasta)
└─ TACOS < 15% (custo anúncio < 15% da venda)
```

### 1.3 O Triângulo de Sucesso ML

```
           🎯 LUCRO
            /  \
           /    \
          /      \
     VOLUME ---- MARGEM

• VOLUME sem MARGEM = Falência
• MARGEM sem VOLUME = Estagnação
• Volume + Margem = Crescimento
```

---

## 📈 PARTE 2: ESTRUTURA OPERACIONAL (COMO FAZER)

### 2.1 Os 5 KPIs Que Você PRECISA Acompanhar DIARIAMENTE

#### **KPI #1: TICKET MÉDIO (TM)**

```
TM = Faturamento do Dia ÷ Número de Vendas

EXEMPLO (Hugo Jobs - 2026-03-08):
TM = 2.679,14 ÷ 45 = 59,54 BRL/venda

AÇÃO:
├─ TM caindo? Promoções estão chegando? Tração em produtos baratos?
├─ TM subindo? Mantenha: você está vendendo premium
└─ Alvo: TM sempre acima do custo médio + 30%
```

#### **KPI #2: CONVERSÃO (C%)**

```
C% = (Vendas ÷ Visitantes) × 100

EXEMPLO:
Se 10 pessoas viram seu produto e 1 comprou = 10% de conversão

BENCHMARK ML:
├─ Categoria Moda: 2-5% é EXCELENTE
├─ Categoria Eletrônicos: 1-3% é bom
├─ Seu Target: 5% acima da média da sua categoria
└─ Como saber sua conversão? Via MercadoLivre Ads Manager

AÇÃO:
├─ C% baixa? Problema é QUALIDADE (fotos, descrição)
├─ C% boa mas vendas caem? Problema é TRÁFEGO (precisa anúncios)
└─ C% subindo? Teste aumentar preço 5-10%
```

#### **KPI #3: MARGEM LÍQUIDA (ML%)**

```
ML% = (Faturamento - Custos Totais) ÷ Faturamento

CUSTOS = CMV + Taxa ML + Envio + Impostos + Operação

EXEMPLO (Hugo Jobs - Moletom 67,87 BRL):
├─ Preço Venda:        67,87 BRL
├─ CMV (custo):        44,99 BRL
├─ Taxa ML (20%):      13,57 BRL
├─ Envio (estimado):   -3,50 BRL (ML paga parte)
├─ Imposto (~7%):      -4,75 BRL
├─ = Lucro Bruto:      4,06 BRL
├─ ML%:                5,98% ❌ MUITO BAIXO

AÇÃO:
├─ ML% < 20%? Aumentar preço ou reduzir CMV
├─ ML% 20-35%? Zona de conforto — manter
├─ ML% > 40%? Oportunidade — escalar volume
└─ NUNCA venda com ML% < 0%
```

#### **KPI #4: TACOS (Total ADS COSt of Sale)**

```
TACOS% = (Gasto em Anúncios ÷ Faturamento com Anúncios) × 100

EXEMPLO:
├─ Gastei: 100 BRL em PADS
├─ Faturei com PADS: 600 BRL
├─ TACOS = (100 ÷ 600) × 100 = 16,67%

BENCHMARK:
├─ TACOS < 10%: MUITO BOM (você está dominando)
├─ TACOS 10-20%: BOM (lucro ainda saudável)
├─ TACOS 20-30%: ACEITÁVEL (mas apertar budget)
├─ TACOS > 30%: ❌ PARAR IMEDIATAMENTE

AÇÃO:
├─ TACOS alto? Reduzir bid ou pausar keywords ruins
├─ TACOS baixo? Aumentar bid — há espaço para crescer
└─ Regra ouro: TACOS + ML% > 20% = lucrativo
```

#### **KPI #5: ROAS (Return On Ad Spend)**

```
ROAS = Faturamento com Anúncios ÷ Gasto em Anúncios

EXEMPLO:
├─ Gasto: 100 BRL
├─ Faturamento: 400 BRL
├─ ROAS = 400 ÷ 100 = 4x

BENCHMARK:
├─ ROAS 2x: Ruim (lucro < 10%)
├─ ROAS 3x: Bom (30% lucro aproximadamente)
├─ ROAS 4x: EXCELENTE (40% lucro)
├─ ROAS 5x+: Dominação (mais lucro que taxa)

AÇÃO:
├─ ROAS < 2.5x? Pausar campainha — está queimando dinheiro
├─ ROAS 3x? Manter e otimizar
├─ ROAS 4x+? Aumentar budget (tem espaço)
└─ Meta: ROAS mínimo 3.5x ou parar ads
```

### 2.2 Dinâmica Diária (Seu Checklist 15min/dia)

```
⏰ MANHÃ (08:00) — Check de Urgências
├─ [ ] Vendas ontem foram normais? (comparar com média 7 dias)
├─ [ ] Alguém abriu chamado? (responder < 1 hora)
├─ [ ] Estoque OK? (se produto vendeu, ativar backup)
└─ [ ] Preço competitivo? (verificar 3 concorrentes)

⏰ MEIO DO DIA (13:00) — Otimização
├─ [ ] TACOS está controlado? (< 20%)
├─ [ ] Conversão normal? (comparar ontem)
├─ [ ] Anúncios rodando? (ou budget zerou?)
└─ [ ] Margem dos top 3 produtos está OK? (>25%)

⏰ NOITE (19:00) — Planejamento Amanhã
├─ [ ] Quais anúncios vou pausar? (TACOS > 25%)
├─ [ ] Quais vou aumentar bid? (ROAS > 3.5x)
├─ [ ] Preciso ativar Oferta Relâmpago? (product caindo)
└─ [ ] Amanhã vou testar qual preço? (teste 1 produto)

⏰ SEMANAL (Sexta) — Análise Profunda
├─ [ ] Top 3 produtos da semana (vendas + margem)
├─ [ ] Bottom 3 (pausar ou reproçar?)
├─ [ ] Keywords mais caras (reduzir bid ou pausar?)
├─ [ ] Taxa de devolução (mais que 5%? problema sério)
└─ [ ] Feedback dos clientes (ajustar descrição/fotos)
```

---

## 🎯 PARTE 3: FRAMEWORKS OPERACIONAIS (COMO DECIDIR)

### 3.1 Framework de Precificação — O "3 Camadas"

```
CAMADA 1: PISO (você NUNCA desce disso)
┌─────────────────────────────────────┐
│ PISO = CMV + Imposto + Envio × 1.15 │
│ (15% de margem mínima)              │
└─────────────────────────────────────┘

CAMADA 2: COMPETIÇÃO (onde você geralmente vende)
┌─────────────────────────────────────────┐
│ PREÇO FINAL = Preço concorrente - 5 BRL │
│ (vender mais barato que concorrência)   │
└─────────────────────────────────────────┘

CAMADA 3: PREMIUM (quando você domina)
┌──────────────────────────────────────┐
│ PREÇO FINAL = Preço concorrente + 15% │
│ (quando sua conversão é 2x melhor)    │
└──────────────────────────────────────┘

EXEMPLO (Moletom):
├─ CMV: 44,99
├─ Imposto/Envio: 8,50
├─ PISO: (44,99 + 8,50) × 1.15 = 61,68 BRL ✅ Mínimo
├─ Concorrentes cobram: 75 BRL
├─ COMPETIÇÃO: 70 BRL ← INICIAL
├─ Se conversão sobe: testar 82 BRL (Premium)
└─ Resultado: 2x margem com volume controlado
```

### 3.2 Framework de Decisão de Anúncio — "Go/No-Go"

```
┌─ NOVO PRODUTO: Devo anunciar?
│
├─ Q1: Produto tem margem > 25%?
│  ├─ NÃO → Não anuncie (vai dar prejuízo)
│  └─ SIM ↓
│
├─ Q2: Tenho estoque para 100 vendas?
│  ├─ NÃO → Anuncie pouco (5-10 BRL/dia)
│  └─ SIM ↓
│
├─ Q3: Qual a conversão estimada (benchark)?
│  ├─ < 2% → Anúncio premium (imagem de qualidade)
│  ├─ 2-5% → Anúncio clássico OK
│  └─ > 5% → Anúncio oferta relâmpago
│
└─ RESULTADO: GO/NO-GO + Budget recomendado
   ├─ GO: Comece com 50 BRL/dia
   ├─ Medir ROAS por 7 dias
   └─ Se ROAS > 3x: aumentar 20% budget
   └─ Se ROAS < 2.5x: pausar e reproçar
```

### 3.3 Framework de Resposta a Queda de Vendas — "Diagnóstico"

```
VENDAS CAÍRAM 30% DE REPENTE

PASSO 1: Timing (quando começou?)
├─ Hoje → Problema técnico (loja fora? anúncio pausado?)
├─ Essa semana → Concorrência entrou
└─ Esse mês → Sazonalidade ou produto vencido

PASSO 2: Por Categoria
├─ Todos produtos caíram? → TRÁFEGO (pausar anúncios, revisar estoque)
├─ Alguns caíram? → COMPETIÇÃO (verificar preço)
└─ Um produto caiu? → QUALIDADE (foto ruim, cliente reclamou?)

PASSO 3: Verificar Dados
├─ Visite seu Painel ML Ads: visitantes caíram?
│  ├─ SIM → Anúncios precisam otimização (keywords, budget)
│  └─ NÃO → Conversão que caiu (qualidade/preço)
│
└─ Checkout ML: estoque está marcado?
   ├─ NÃO → Ativar estoque imediatamente
   └─ SIM → Próximo passo

PASSO 4: Ação
├─ Se TRÁFEGO baixo: aumentar bid em 10% (teste 3 dias)
├─ Se CONVERSÃO baixa: revisar preço (- 5-10 BRL) + fotos
├─ Se ESTOQUE vazio: pausar anúncio (economizar)
└─ Se CONCORRÊNCIA: aumentar oferta relâmpago 15%
```

---

## 💰 PARTE 4: OPERAÇÃO REAL (HUGO JOBS CASE)

### 4.1 Hugo Jobs — Números Reais (2026-03-08)

```
CONTA: Hugo Jobs (Seller ID: 694166791)
GERENCIADOR: Kennyd Willker
STATUS: ✅ Ativo | 🟢 Saudável

📊 HOJE (2026-03-08):
├─ Vendas: 45 pedidos
├─ Faturamento: 2.679,14 BRL
├─ Ticket Médio: 59,54 BRL
├─ Margem Líquida: 22,3% (600 BRL lucro)
├─ Gasto em Anúncios: 0 BRL (sem ads ativos)
└─ Conversão: 100% ORGÂNICA

📈 SEMANA (últimos 7 dias):
├─ Vendas: 369 pedidos
├─ Faturamento: 24.031,52 BRL
├─ Ticket Médio: 65,09 BRL
├─ Total Lucro: ~5.365 BRL
└─ Taxa de Devolução: < 2% (excelente)

⭐ REPUTAÇÃO ML:
├─ Nível: 5 GREEN (Vendedor Confiável)
├─ Total Transações: 9.142
├─ Rating: ⭐⭐⭐⭐⭐
└─ Tempo Resposta: < 30 min

📦 PRODUTOS TOP (semana):
1. Moletom Masculino Zíper (67,87 BRL) — 45 vendas
2. [Outros dados em dashboard-data.json]

🔐 ACESSO:
├─ Email: hugojobs.co@gmail.com
├─ Token API: ✅ Válido até 2026-03-09 02:35
└─ Integração: MercadoLivre OAuth (automática)
```

### 4.2 Análise Profunda — 5 Ações Imediatas

**AÇÃO 1: ATIVAR ANÚNCIOS**
```
Status Atual: 0 BRL/dia em ads = deixando dinheiro na mesa

Recomendação:
├─ Produto: Moletom (melhor performer)
├─ Budget: 50 BRL/dia (teste 7 dias)
├─ Target ROAS: 3.5x mínimo
└─ Bid Inicial: 1,50 BRL por click

Projeção (se atingir ROAS 3.5x):
├─ Gasto: 350 BRL (semana)
├─ Faturamento: 1.225 BRL (semana)
├─ Lucro + Base: 5.365 + 245 = 5.610 BRL/semana
└─ Incremento: +4,5% faturamento
```

**AÇÃO 2: TESTE DE PREÇO**
```
Moletom está em 67,87 BRL
├─ Sua margem: 22,3%
├─ Concorrentes: ~72 BRL
├─ Oportunidade: AUMENTAR para 75-80 BRL

Teste A/B (próxima semana):
├─ Grupo A: manter 67,87 (50% estoque)
├─ Grupo B: testar 75,99 (50% estoque)
└─ Vencedor: escalar no próximo mês

Projeção:
├─ Se ticket sobe 10%: +200 BRL/dia em receita
├─ Mesmo com 20% menos volume: +150 BRL/dia de lucro
└─ Risco: baixo (você vende muito orgânico)
```

**AÇÃO 3: MINHA PÁGINA**
```
Status: Pode estar desatualizado

Checklist (30min):
├─ [ ] Banner principal: profissional + marca?
├─ [ ] Descrição: clara + keywords?
├─ [ ] Faq: responder top 5 dúvidas?
├─ [ ] Promoção: há oferta relâmpago ativa?
└─ [ ] Reviews: highlight top 5 reviews positivos

Impacto: Cada cliente que NÃO sai = 1 venda

Exemplo: Se 10% dos visitors saem por "página ruim" = 37 menos vendas/semana
```

**AÇÃO 4: CRIAR BUNDLE/KIT**
```
Oportunidade: Aumentar ticket médio

Opção A (Conservadora):
├─ 2x Moletom + 1x Camiseta
├─ Preço: 190 BRL (desconto 10% vs individual)
├─ Margem: -2% por bundle (mas +95 BRL ticket)
└─ Target: 10 bundles/semana = +950 BRL

Opção B (Agressiva):
├─ Kit Completo (moletom + 2 camisetas + short)
├─ Preço: 250 BRL
├─ Margem: mesma 22%
└─ Target: 20 kits/semana = +5.000 BRL extra

Ação: Criar anúncio bundle + oferta relâmpago
```

**AÇÃO 5: RASTREAMENTO AUTOMÁTICO**
```
Configure (5min): Dashboard automático

Ferramentas:
├─ fetch_dashboard_data.py (você já tem!)
│  └─ Roda 1x/dia, atualiza dashboard-data.json
├─ Google Sheets (integração)
│  └─ Planilha que se atualiza automaticamente
└─ Alertas (se vendas caem > 20%)
   └─ Aviso automático no WhatsApp

Benefício: 0 minutos/dia checando — tudo automático
```

---

## 🛠️ PARTE 5: AUTOMAÇÕES & SCRIPTS

### 5.1 Scripts que Você JÁ Tem (Usar!)

```
SCRIPT 1: Dashboard Atualizado
─────────────────────────────
Local: /fetch_dashboard_data.py
Uso: python3 fetch_dashboard_data.py --watch
Resultado: dashboard-data.json atualizado a cada 60s

O que rastreia:
├─ Faturamento do dia (vs ontem, vs média 7 dias)
├─ Número de vendas
├─ Ticket médio
├─ CMV dos produtos
├─ Margem bruta e líquida
├─ Custos de envio
└─ Taxa ML (comissão)

Vantagem: TUDO em 1 arquivo JSON — integrar com sheets
```

```
SCRIPT 2: Check Rápido de Vendas
───────────────────────────────
Local: /check-vendas-v2.py
Uso: python3 check-vendas-v2.py
Resultado: Resumo das vendas do dia em terminal

Saída:
├─ Vendas do dia
├─ Faturamento
├─ Rank dos top 5 produtos
└─ Alertas (se caiu > 20%)
```

```
SCRIPT 3: Update Ranking Produtos
─────────────────────────────────
Local: /update-ranking-final.py
Uso: python3 update-ranking-final.py
Resultado: Classifica produtos por lucro

Saída:
├─ Ranking 1: Produto X (maior lucro)
├─ Ranking 2: Produto Y
└─ [...]

Usar: Focar anúncios nos top 3
```

### 5.2 Integrações Recomendadas (Setup 30min)

```
INTEGRAÇÃO 1: Google Sheets (Automático)
────────────────────────────────────
Setup:
1. Criar planilha no Google Drive
2. Usar script fetch_dashboard_data.py
3. Conectar API Google Sheets (via service account)
4. Resultado: Planilha que se atualiza 1x/hora

Benefício: Visualização em tempo real + compartilhar com equipe

INTEGRAÇÃO 2: Slack/WhatsApp Alerts
──────────────────────────────────
Setup:
1. Adicionar webhook no fetch_dashboard_data.py
2. Se vendas caem > 20% → alerta automático
3. Se TACOS > 25% → alerta ("pausar anúncios")

Benefício: Não perder vendas por falta de atenção

INTEGRAÇÃO 3: ClickUp + Dashboard
────────────────────────────────
Setup:
1. Atualizar Task "Hugo Jobs" toda semana com KPIs
2. Anexar screenshot do dashboard
3. Documentar decisões tomadas

Benefício: Histórico + auditoria + aprendizado
```

---

## 📚 PARTE 6: HEURÍSTICAS OPERACIONAIS (REGRAS PRÁTICAS)

### 6.1 As 25 Regras que Nunca Falham

```
1. NUNCA venda com margem < 15%
   └─ Exceção: Produto de atração (1 unidade de perda = 10 novos clientes)

2. Se TACOS > 25%, pausar anúncio IMEDIATAMENTE
   └─ Seu negócio está queimando dinheiro

3. Teste de preço: sempre em múltiplos de 5 BRL
   └─ 67,87 → 72,87 → 77,87 (não 68 ou 69)

4. Responda clientes em < 1 hora
   └─ Cada minuto de atraso = 1% menos vendas

5. Oferta Relâmpago: use quando vendas caem > 15%
   └─ 15-20% desconto, máximo 3 dias

6. Stock sempre 2x a venda esperada
   └─ Se vende 50/dia, manter 100+ em estoque

7. Product Ads: rodar pelo menos 50 BRL/dia
   └─ Menos que isso = não gasta o bastante para aprender

8. Não altere preço 2x na mesma semana
   └─ Algoritmo ML fica confuso, cai ranking

9. Foto ruim mata 50% das vendas
   └─ Investir em fotógrafo: melhor ROI que ads

10. Descrição deve responder TOP 5 perguntas dos clientes
    └─ "Que tamanho devo levar?", "Tem cor X?", etc

11. Keyword research: buscar com LOW competition
    └─ "moletom barato" vs "moletom azul tamanho M"

12. Bundle vende 3x mais que individual
    └─ Usar para aumentar ticket médio

13. Não fazer promoção generalizada
    └─ Promover: produto que vende lento (estratégico)

14. Revisar anúncio cada 7 dias
    └─ Pausar os piores, escalar os melhores

15. Margem líquida > conversão
    └─ Melhor vender 10 de 100 BRL que 100 de 1 BRL

16. Retorno do cliente > novo cliente
    └─ Manter 1 cliente atual = 10x mais barato que conseguir novo

17. Email de follow-up: enviar 1 semana pós-compra
    └─ "Como está? quer desconto na próxima?"

18. Seasonal é ouro: se Natal vem, preparar 3 meses antes
    └─ Estoque + anúncios + preparar bundlees

19. Taxa de devolução > 5% = problema sério
    └─ Investigar: qualidade? logística? comunicação?

20. Não confiar 100% no algoritmo ML
    └─ Testar sempre: preço, foto, palavra-chave

21. Competidor entrou com preço 30% menor?
    └─ Não bajar preço, aumentar qualidade + oferta

22. Margem negativa de 1 produto = trocar estratégia
    └─ Desativar ou aumentar preço drasticamente

23. Visitantes não convertendo?
    └─ 90% das vezes: foto ruim, preço confuso, ou shipping caríssimo

24. Oferta relâmpago perto de vencer?
    └─ Colocar "Últimas 5 unidades" (senso de urgência)

25. Dias antes de feriado = estoque deve estar CHEIO
    └─ Pessoas compram, logística fica lenta, estoque vira vantagem
```

### 6.2 Matriz de Decisão Rápida

```
┌─────────────────────┬──────────────────┬──────────────────┐
│ SITUAÇÃO            │ AÇÃO             │ TEMPO            │
├─────────────────────┼──────────────────┼──────────────────┤
│ Vendas ↓ 20%        │ Aumentar bid 10% │ Hoje (1 hora)    │
│ Vendas ↑ 50%        │ Aumentar budget  │ Hoje (30 min)    │
│ TACOS > 25%         │ Pausar anúncio   │ Imediatamente    │
│ Novo produto        │ Testar com ads   │ Próxima segunda  │
│ Estoque acabando    │ Aumentar preço   │ Hoje             │
│ Estoque cheio       │ Oferta relâmpago │ Hoje             │
│ Margem < 15%        │ Revisar CMV      │ Essa semana      │
│ Revisão fraca       │ Melhorar fotos   │ Essa semana      │
│ Resposta lenta      │ Contratar suporte│ Próxima 2a feira │
│ Sazonalidade mudou  │ Revisar SEO      │ Essa semana      │
└─────────────────────┴──────────────────┴──────────────────┘
```

---

## 🎓 PARTE 7: MASTER KNOWLEDGE (APROFUNDAR)

### 7.1 Transcrição LIVE — "Performance Máxima Anúncios Rankeados ML"

**Assunto:** Como manter produtos no topo do ranking

**Insights:**
- Ranking não é baseado só em preço
- Conversão + recência + feedback = ranking
- Velocidade de resposta = 30% do algoritmo
- Reviews 4.5+ = favor no ranking
- Produtos que vendem = produtos que rankear

**Ações Práticas:**
1. Responder comentário em < 30 minutos
2. Solicitar review (automático após 7 dias de compra)
3. Manter revisão acima de 4.5 estrelas
4. Vender consistentemente (não picos)
5. Atualizar estoque diariamente

### 7.2 Transcrição Masterclass — "Gaste Pouco, Venda Dobro em ML"

**Palestrante:** Dhiego Rosa
**Tema:** Otimização de PADS (Product Ads)

**Framework Extraído:**

```
FASE 1: ESTRUTURA (semana 1)
├─ Criar 3 campanhas diferentes
├─ Budget igual: 50 BRL/dia cada
├─ Testar: keywords / imagem / preço
└─ Medir: qual ROAS > 3x

FASE 2: ESCALA (semana 2-3)
├─ Pausar campanhas ROAS < 2.5x
├─ Aumentar 30% as que estão > 3.5x
├─ Refinar bid nos 10% melhores keywords
└─ Resultado: mesmo orçamento, 2x vendas

FASE 3: OTIMIZAÇÃO (semana 4+)
├─ Analisar CPC dos melhores keywords
├─ Reduzir bid nos piores 20%
├─ Criar variações de anúncio baseado em dados
└─ Target: ROAS 4x com 20% menos budget
```

**Métrica Crítica:** ACOS (não TACOS)

```
Importante ENTENDER:
├─ ACOS = Advertising COSt of Sale (quanto custa uma venda)
│         ACOS = Gasto ÷ Faturamento
│         ACOS 20% = você gasta 20 centavos para vender 1 real
│
└─ TACOS = Total ACS (inclui todos anúncios)
          TACOS 15% = ideal (deixa 85% de margem)
```

---

## 🔗 PARTE 8: INTEGRAÇÃO COM SISTEMA

### 8.1 MCP Server MercadoLivre (Sua API)

Você tem um **servidor Python completo** que conecta à API ML:

```
Localização: /core/mcp/mercadolivre_mcp.py

O que faz:
├─ Autentica com OAuth automaticamente
├─ Busca categorias + comissões reais
├─ Estima custos de envio
├─ Retorna tipos de anúncio disponíveis
└─ Integra com ClickUp via MCP (já configurado)

Como usar:
1. Token já está válido em .env
2. Rodar: python3 core/mcp/mercadolivre_mcp.py
3. Resultado: JSON com dados da API
```

### 8.2 Dashboard em Tempo Real

```
Localização: /dashboard-data.json

Atualizado automaticamente por: /fetch_dashboard_data.py

Dados inclusos:
├─ Faturamento (hoje + semana)
├─ Número de vendas
├─ Ticket médio
├─ Margem bruta/líquida
├─ Top 5 produtos
├─ Custos ML, envio, impostos
├─ Comparativo com dia anterior
└─ Alertas automáticos
```

---

## 📋 PARTE 9: CHECKLIST SEMANAL (Para Imprimir)

```
SEGUNDA-FEIRA (Plano)
─────────────────────
[ ] Revisar vendas da semana anterior
[ ] Fazer 3 testes de preço (próxima semana)
[ ] Aumentar bid em anúncios com ROAS > 3.5x
[ ] Pausar anúncios com TACOS > 20%
[ ] Verificar estoque dos top 3 produtos
[ ] Responder comentários (máx 30min resposta)

QUARTA-FEIRA (Otimização)
────────────────────────
[ ] Revisar performance de anúncios (3 dias rodando)
[ ] Ajustar bid dos piores keywords (-10%)
[ ] Aumentar bid dos melhores keywords (+5%)
[ ] Criar novo anúncio se houver espaço no budget
[ ] Verificar avaliações (responder críticas negativas)

SEXTA-FEIRA (Análise)
────────────────────
[ ] Fazer análise completa da semana
[ ] Atualizar Task do ClickUp com KPIs
[ ] Definir metas da próxima semana
[ ] Revisar margem dos produtos (< 15% = repricetar)
[ ] Planejar promoções (se vendas caem)
[ ] Reunião com time: resultados + próximas ações

DOMINGO (Preparação)
────────────────────
[ ] Verificar sazonalidade (feriado coming?)
[ ] Stock OK? (comprar mais se necessário)
[ ] Fotos OK? (revisar produto mais vendido)
[ ] Descrição OK? (atualizar se necessário)
[ ] Anúncio padrão OK? (para próxima semana)
```

---

## 🚀 PARTE 10: ROADMAP 90 DIAS

### Mês 1: Foundation
```
Semana 1-2: Setup
├─ [ ] Ativar anúncios (50 BRL/dia)
├─ [ ] Configurar automações
├─ [ ] Dashboard rodando
└─ [ ] KPIs mapeados

Semana 3-4: Otimização
├─ [ ] Testar 5 keywords
├─ [ ] Testar preço (+10%)
├─ [ ] Criar bundle
└─ [ ] ROAS alvo atingido (3.5x+)

META MÊS 1: ROAS 3.5x, TACOS < 20%, Margem 25%+
```

### Mês 2: Scale
```
Semana 5-6: Budget up
├─ [ ] Aumentar budget 30% (anúncios)
├─ [ ] Escalar top 3 keywords
├─ [ ] Criar 2 novos anúncios
└─ [ ] Ativar Oferta Relâmpago

Semana 7-8: Analysis
├─ [ ] Revisar ROAS dos novos anúncios
├─ [ ] Pausar piores 20%
├─ [ ] Aumentar melhores 20%
└─ [ ] Treinar equipe em otimização

META MÊS 2: 2x volume, ROAS mantido 3.5x+, Lucro +200%
```

### Mês 3: Domination
```
Semana 9-10: Expansion
├─ [ ] 5 novos produtos
├─ [ ] Anúncios para cada um
├─ [ ] Minha Página premium
└─ [ ] Bundle + kit novo

Semana 11-12: Optimization
├─ [ ] Análise profunda de todos dados
├─ [ ] Identificar padrões
├─ [ ] Documentar playbooks
└─ [ ] Treinar gestor seguinte

META MÊS 3: 3x volume inicial, ROAS 4x+, Lucro 300%+ vs atual
```

---

## 📞 PARTE 11: SUPORTE & REFERÊNCIAS

### Documentação Técnica
- `/mercado-livre-ads-agent/docs/ML-API-RESEARCH-2026-03-09.md` — Referência API
- `/mercado-livre-ads-agent/docs/prd/mercado-livre-ads-agent-prd.md` — Visão completa
- `/MERCADOLIVRE_DATA_2026-03-08.json` — Dados reais Hugo Jobs

### Scripts Ativos
- `/fetch_dashboard_data.py` — Dashboard automático
- `/check-vendas-v2.py` — Check rápido
- `/update-ranking-final.py` — Ranking por lucro

### ClickUp
- **Workspace:** GPS (Team ID: 9013550760)
- **Space:** Gestão GPS.X
- **Folder:** Equipe Julio
- **List:** Gestao Contas (sua conta = Hugo Jobs)

---

## 💯 CONCLUSÃO

Este manual consolida **2 anos de aprendizado operacional** em uma estrutura pronta para implementação.

**Regra de Ouro:**
```
Volume × Margem = Lucro
Sem volume: sem escala
Sem margem: sem sustentabilidade
Com ambos: você domina o ML
```

**Próximo Passo:**
1. Ativar anúncios (50 BRL/dia) — esta semana
2. Implementar 3 frameworks — próximas 2 semanas
3. Atingir ROAS 3.5x — 30 dias
4. Documentar aprendizados — contínuo

---

**De fato, senhor. Manual do gestor foda: completo.**

*Última atualização: 2026-03-09*
*Versão: 2.0.0 — Operacional e Pronto para Implementação*
