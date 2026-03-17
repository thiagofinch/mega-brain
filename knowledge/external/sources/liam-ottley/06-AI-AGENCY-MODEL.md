# LIAM OTTLEY — AI Agency Model

[[HOME|← Home]] | [[MOC-SOURCES|📚 Sources]] | [[MOC-PESSOAS|👤 Pessoas]] | [[MOC-TEMAS|📦 Temas]]

> **Em resumo:** Liam detalha o modelo de negócio para AI agencies: como vender, quanto cobrar, como fazer discovery, e como se posicionar. A regra de ouro é "sell OUTCOME, not TECHNOLOGY" — o cliente não quer saber sobre Claude Code, quer saber quanto vai economizar. Pricing ancorado em custo humano (40-60% savings), margens de 80%+, e posicionamento como "AI transformation partner" em vez de "AI developer."
>
> **Versao:** 1.0 | **Atualizado:** 2026-03-16
> **Densidade:** ◐◐◐◐◯ (4)

---

## Filosofia Central

O erro fatal de quem entra no mercado de AI: vender tecnologia. O cliente não quer ouvir sobre models, APIs, Claude Code, ou agent frameworks. O cliente quer ouvir: "Vou economizar $3K/mês no seu SDR e ele vai trabalhar 24/7." [chunk_651]

Liam insiste em posicionamento como "AI transformation partner" — não "AI developer." A diferença é estratégica: developer é commodity (quem faz mais barato ganha). Transformation partner é consultoria (quem entrega mais valor ganha). [chunk_655]

> "Position as 'AI transformation partner' not 'AI developer'." — [chunk_655]

---

## Modus Operandi

### 4-Step AI Agency Sales

O framework de vendas que Liam ensina: [chunk_651]

```
┌────────────────────────────────────────────────────────────┐
│              4-STEP AI AGENCY SALES PROCESS                │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   STEP 1: LEAD GENERATION                                   │
│   └─ Content formula: "I helped [client] save [X]          │
│      by deploying [agent] for [task]"                       │
│   └─ One case study with real numbers > 100 posts           │
│                                                             │
│   STEP 2: DISCOVERY                                         │
│   └─ 80% listening / 20% talking                            │
│   └─ Map workflows, find repetitive bottlenecks             │
│   └─ Identify tasks that humans hate doing                  │
│                                                             │
│   STEP 3: PROPOSAL (ROI-focused)                            │
│   └─ Anchor to human cost: "SDR costs $5K/mo"              │
│   └─ Show savings: "AI SDR = $2-3K/mo = 40-60% savings"    │
│   └─ Bundle: 3-5 agents per client                          │
│                                                             │
│   STEP 4: ONBOARDING                                        │
│   └─ Start simple: 1 agent, 1 task                          │
│   └─ Prove value, then expand                               │
│   └─ Monthly retainer model                                 │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

> "AI Agency 4-Step Sales: sell OUTCOME not TECHNOLOGY." — [chunk_651]

### Discovery: 80% Listening

A fase de discovery é onde a maioria das AI agencies falha. Eles chegam com solução pronta antes de entender o problema. Liam insiste: **80% ouvindo, 20% falando**. [chunk_654]

O processo:
1. Mapear todos os workflows do cliente
2. Identificar tarefas repetitivas
3. Encontrar bottlenecks (onde as coisas param)
4. Priorizar por impacto econômico
5. Só então propor solução

> "80% listening in discovery, map workflows first." — [chunk_654]

### Agent Architecture

Cada agent deployado segue uma arquitetura de 4 componentes: [chunk_652]

```
┌──────────────────────────────────────────────────────┐
│              AGENT ARCHITECTURE                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│   ┌──────────────┐    ┌──────────────┐               │
│   │   CONTEXT    │    │    TOOLS     │               │
│   │ (knowledge,  │    │ (APIs, DBs,  │               │
│   │  history,    │    │  external    │               │
│   │  brand)      │    │  services)   │               │
│   └──────┬───────┘    └──────┬───────┘               │
│          │                   │                       │
│          └─────────┬─────────┘                       │
│                    ▼                                 │
│          ┌──────────────────┐                        │
│          │    WORKFLOWS     │                        │
│          │ (step-by-step    │                        │
│          │  procedures)     │                        │
│          └────────┬─────────┘                        │
│                   ▼                                  │
│          ┌──────────────────┐                        │
│          │   GUARDRAILS     │                        │
│          │ (limits, escal-  │                        │
│          │  ation, HITL)    │                        │
│          └──────────────────┘                        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

> "Agent Architecture: Context+Tools+Workflows+Guardrails." — [chunk_652]

---

## Arsenal Técnico

### Pricing Framework

| Componente | Benchmark | Detalhes | Chunk |
|------------|-----------|----------|-------|
| **Anchor** | Custo humano | SDR = $5K/mês, Support = $4K/mês | [chunk_653] |
| **Discount** | 40-60% | AI agent custa menos que humano | [chunk_653] |
| **Agent price** | $1.5-3K/mês | Por agent deployado | [chunk_653] |
| **Sweet spot** | 3-5 agents/cliente | Retainer de $4.5-15K/mês | [chunk_653] |
| **Margem** | 80%+ | Custo real mínimo (APIs + hosting) | [chunk_653] |

> "AI Workforce Pricing: 40-60% human cost savings, 80%+ margins." — [chunk_653]

### Content Formula para Lead Gen

| Elemento | Exemplo |
|----------|---------|
| **Template** | "I helped [client] save [X] by deploying [agent] for [task]" |
| **Real** | "I helped a SaaS company save $8K/mo by deploying an AI SDR team for outbound" |
| **Regra** | 1 case study com números reais > 100 posts teóricos |
| **Chunk** | [chunk_651] |

### Posicionamento

| Posição | Percepção do Mercado | Pricing Power |
|---------|---------------------|---------------|
| "AI Developer" | Commodity, price-driven | Baixo |
| "AI Agency" | Serviço, scope-driven | Médio |
| "AI Transformation Partner" | Consultoria, value-driven | Alto |
| **Chunk** | [chunk_655] | |

---

## Armadilhas

### Vender Features em Vez de Outcomes

"Nosso agent usa GPT-4o com RAG e function calling" — zero clientes se importam com isso. "Nosso agent faz 500 outreach/dia e qualifica leads automaticamente" — todos os clientes querem isso. [chunk_651]

### Precificar por Horas

O modelo de agency tradicional (cobrar por hora de desenvolvimento) é a antítese do AI Workforce. O cliente paga retainer mensal por output, não por esforço. Cobrar por hora penaliza eficiência. [chunk_653]

### Pular Discovery

Chegar com solução pronta sem mapear workflows do cliente resulta em agent que resolve o problema errado. Os 80% de listening existem por uma razão. [chunk_654]

---

## Citações-Chave

> "AI Agency 4-Step Sales: sell OUTCOME not TECHNOLOGY." — [chunk_651] contexto: framework de vendas

> "Agent Architecture: Context+Tools+Workflows+Guardrails." — [chunk_652] contexto: estrutura de cada agent

> "AI Workforce Pricing: 40-60% human cost savings, 80%+ margins." — [chunk_653] contexto: unit economics

> "80% listening in discovery, map workflows first." — [chunk_654] contexto: processo de discovery

> "Position as 'AI transformation partner' not 'AI developer'." — [chunk_655] contexto: posicionamento estratégico

---

---

## Adições do Run Autônomo 2026-03-16 (chunks 656-690)

### Monetization Path Completo (4 Etapas)

Liam refina o modelo de monetização em 4 etapas que geram fluxo de caixa progressivo: [chunk_678]

| Etapa | Produto | Preço | Propósito |
|-------|---------|-------|-----------|
| **Diagnose** | AI Workforce Assessment | $2-5K one-time | Posicionar como trusted advisor antes de implementar |
| **Design & Implement** | Single agent → Full workforce | $2-5K → $10-50K+ | Entrega principal com margem alta |
| **Manage & Scale** | Monthly retainer 3-5 agents | $4.5-15K/mo | Receita recorrente escalável |
| **Expand** | Upsell interno ou novo cliente | Via case study | Compounding do portfólio |

> "Your journey to monetization follows a simple progression. Diagnose, design, deliver, and scale." — [chunk_678] (LO-017)

### Cold Email Niche Testing (30 Days)

Framework de aquisição para quem está começando sem network: [chunk_679]

1. **Escolher 4 nichos** de serviços
2. **Escrever 1 email** focado em resultado por niche: *"I help [niche] replace [specific process] with an AI workforce that runs 24/7 for less than the cost of one employee."*
3. **Enviar 500 emails/niche** = 2000 total
4. **Rastrear 30 dias**: open rate, replies, calls
5. **Identificar vencedor** e dobrar down

> "After 30 days, you identify which niche and message has performed best, then you double down on that." — [chunk_679] (LO-019)

### Warm Outreach First-Client Formula

Para quem tem network, o caminho mais rápido para o primeiro cliente: [chunk_679]

**Regra:** Não vender diretamente — pedir referrals. Reduz pressão, expande alcance.

**Template:** *"Hey [nome], estou construindo sistemas de AI workforce que automatizam [operação específica], oferecendo alguns assessments complementares para construir cases. Você conhece alguém que poderia se beneficiar?"*

**Lógica:** Complementary assessment = risco zero para o cliente + case study com números reais para você.

> "The key is that you're not selling to them directly. You're asking them for referrals, which essentially lowers the pressure and expands your reach." — [chunk_679] (LO-025)

## Metadados

| Campo | Valor |
|-------|-------|
| **Fonte** | Liam Ottley |
| **Tema** | 06-AI-AGENCY-MODEL |
| **Chunks** | chunk_651, chunk_652, chunk_653, chunk_654, chunk_655, chunk_678, chunk_679 |
| **Insights** | INS-LO-038, INS-LO-039, INS-LO-040, INS-LO-041, INS-LO-042, LO-017, LO-019, LO-025 |
| **Protocolo** | Narrative Metabolism v2.0 |
| **Pipeline** | MCE v1.0 → v1.2.0 (Run Autônomo 2026-03-16) |

---

## Fontes Relacionadas

- [Perfil completo Liam Ottley](../../dossiers/persons/DOSSIER-LIAM-OTTLEY.md)
- [DNA: Liam Ottley](../../dna/persons/liam-ottley/)

---

*Compilado via Narrative Metabolism Protocol v1.0*
*Mega Brain System v3.21.0*
