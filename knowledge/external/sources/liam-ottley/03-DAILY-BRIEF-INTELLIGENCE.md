# LIAM OTTLEY — Daily Brief e Intelligence Layer

[[HOME|← Home]] | [[MOC-SOURCES|📚 Sources]] | [[MOC-PESSOAS|👤 Pessoas]] | [[MOC-TEMAS|📦 Temas]]

> **Em resumo:** O Daily Brief é o produto mais tangível da camada L3-INTELLIGENCE do AIOS. Um PDF de 5-10 páginas entregue via Telegram toda manhã antes das 8am, sintetizando reuniões, Slack, métricas e decisões pendentes. Liam processa 80 calls de 6 streams diferentes em um único documento digestível. O founder começa o dia sabendo tudo — sem assistir nenhuma reunião.
>
> **Versao:** 1.0 | **Atualizado:** 2026-03-16
> **Densidade:** ◐◐◐◯◯ (3)

---

## Filosofia Central

A camada de inteligência do AIOS transforma ruído em sinal. O problema do founder moderno não é falta de informação — é excesso. Reuniões demais, Slack demais, dashboards demais. A L3-INTELLIGENCE resolve isso com síntese automatizada. [chunk_639]

O Daily Brief é a manifestação prática: antes das 8am, o founder recebe via Telegram um PDF de 5-10 páginas com tudo que precisa saber. Não é um resumo genérico — é um SWOT diário personalizado para o negócio. [chunk_549, chunk_550]

> "Daily Brief: 5-10pg PDF via Telegram toda manhã." — [chunk_549, chunk_550]

---

## Modus Operandi

### Arquitetura do Daily Brief

```
┌────────────────────────────────────────────────────────────┐
│                    DAILY BRIEF PIPELINE                     │
├────────────────────────────────────────────────────────────┤
│                                                             │
│   INPUTS (6 streams):                                       │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│   │ Meetings │ │  Slack   │ │  Email   │                   │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘                   │
│        │             │            │                          │
│   ┌────┴─────┐ ┌─────┴────┐ ┌────┴─────┐                   │
│   │   CRM    │ │  Metrics │ │ Calendar │                   │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘                   │
│        │             │            │                          │
│        └─────────────┼────────────┘                          │
│                      ▼                                       │
│           ┌──────────────────┐                               │
│           │  L3-INTELLIGENCE │                               │
│           │   (synthesis)    │                               │
│           └────────┬─────────┘                               │
│                    ▼                                         │
│           ┌──────────────────┐                               │
│           │  PDF 5-10 pages  │                               │
│           │  Daily SWOT      │                               │
│           └────────┬─────────┘                               │
│                    ▼                                         │
│           ┌──────────────────┐                               │
│           │  Telegram < 8am  │                               │
│           └──────────────────┘                               │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

[chunk_549, chunk_550, chunk_639, chunk_649]

### Volume de Processamento

Liam menciona que o sistema processa **80 calls across 6 streams** para gerar cada Daily Brief. São reuniões de múltiplas empresas, times, e projetos — tudo sintetizado em um único documento. [chunk_649]

> "Daily Brief: 5-10pg PDF, 80 calls across 6 streams." — [chunk_649]

### L3-INTELLIGENCE: SWOT Diário

A camada de inteligência não é apenas resumo — é **análise**. O Daily Brief inclui: [chunk_639]

- **Strengths:** O que está funcionando — métricas acima do target
- **Weaknesses:** O que precisa de atenção — gaps identificados
- **Opportunities:** O que apareceu — leads, parcerias, ideias
- **Threats:** O que pode dar errado — riscos identificados

> "L3-INTELLIGENCE: Daily SWOT + synthesis before 8am." — [chunk_639]

### Meeting Synthesis

O componente mais valioso: o founder não precisa assistir reuniões. O sistema grava (via Fireflies), transcreve, e sintetiza os pontos-chave. Decisões tomadas, action items, próximos passos — tudo no Brief sem precisar de 1 hora em cada call. [chunk_549, chunk_550, chunk_639]

---

## Arsenal Técnico

### Especificações do Daily Brief

| Componente | Detalhe | Chunk |
|------------|---------|-------|
| **Formato** | PDF, 5-10 páginas | [chunk_549, chunk_550] |
| **Entrega** | Telegram, antes das 8am | [chunk_549, chunk_550] |
| **Inputs** | 6 streams (meetings, Slack, email, CRM, metrics, calendar) | [chunk_649] |
| **Volume** | 80 calls processadas | [chunk_649] |
| **Análise** | SWOT diário personalizado | [chunk_639] |
| **Frequência** | Diário, 7 dias/semana | [chunk_549] |

### Stack de Captura

| Ferramenta | Papel no Brief |
|------------|----------------|
| **Fireflies** | Gravação e transcrição de meetings |
| **Slack** | Mensagens e decisões de equipe |
| **Claude Code** | Síntese e geração do PDF |
| **Telegram** | Canal de entrega ao founder |

---

## Armadilhas

### Brief Sem Ação

Um Daily Brief que é só resumo não serve. Precisa ter action items, decisões pendentes, e flags de urgência. Senão o founder lê e não faz nada — informação sem ação é ruído. [chunk_639]

### Overload de Dados

Se o Brief tem 30 páginas, ninguém lê. O limite de 5-10 páginas é intencional — forçar priorização. O que não cabe, não é importante o suficiente. [chunk_549, chunk_550]

---

## Citações-Chave

> "Daily Brief: 5-10pg PDF via Telegram toda manhã." — [chunk_549, chunk_550] contexto: formato e canal

> "L3-INTELLIGENCE: Daily SWOT + synthesis before 8am." — [chunk_639] contexto: camada de inteligência

> "Daily Brief: 5-10pg PDF, 80 calls across 6 streams." — [chunk_649] contexto: volume de processamento

---

## Metadados

| Campo | Valor |
|-------|-------|
| **Fonte** | Liam Ottley |
| **Tema** | 03-DAILY-BRIEF-INTELLIGENCE |
| **Chunks** | chunk_549, chunk_550, chunk_639, chunk_649 |
| **Insights** | INS-LO-016, INS-LO-027, INS-LO-036 |
| **Protocolo** | Narrative Metabolism v2.0 |
| **Pipeline** | MCE v1.0 |

---

## Fontes Relacionadas

- [Perfil completo Liam Ottley](../../dossiers/persons/DOSSIER-LIAM-OTTLEY.md)
- [DNA: Liam Ottley](../../dna/persons/liam-ottley/)

---

*Compilado via Narrative Metabolism Protocol v1.0*
*Mega Brain System v3.21.0*
