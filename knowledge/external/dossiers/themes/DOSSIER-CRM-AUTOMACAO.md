# DOSSIER: CRM E AUTOMAÇÃO COMERCIAL

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ██████╗██████╗ ███╗   ███╗       █████╗ ██╗   ██╗████████╗ ██████╗       ║
║   ██╔════╝██╔══██╗████╗ ████║      ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗      ║
║   ██║     ██████╔╝██╔████╔██║█████╗███████║██║   ██║   ██║   ██║   ██║      ║
║   ██║     ██╔══██╗██║╚██╔╝██║╚════╝██╔══██║██║   ██║   ██║   ██║   ██║      ║
║   ╚██████╗██║  ██║██║ ╚═╝ ██║      ██║  ██║╚██████╔╝   ██║   ╚██████╔╝      ║
║    ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝      ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝       ║
║                                                                              ║
║   GO HIGH LEVEL | PIPELINE 6 NÍVEIS | 3 AUTOMAÇÕES CORE                     ║
║   SWEET SPOTS | FOLLOW-UP INFINITO | SALES FARMING                          ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  VERSÃO: 1.0.0                                                               ║
║  FONTE: Full Sales System (FSS) 100%                                         ║
║  BATCH: BATCH-120                                                            ║
║  ELEMENTOS: ~85 extraídos                                                    ║
║  ATUALIZADO: 2026-01-10                                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## EXECUTIVE SUMMARY

Este dossier documenta o sistema completo de CRM e Automação Comercial usando Go High Level como hub central. A filosofia central: **"Tudo que você puder automatizar sem perder personalização, faça para o time comercial ter mais facilidade."**

O framework inclui 6 níveis de follow-up, 3 automações core, sweet spots de agendamento, e integração multicanal - reduzindo perda de leads de 70-75% para quase 0%.

---

## FILOSOFIA CENTRAL

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  "PRIMEIRO CONTATO: AUTOMAÇÃO. SEGUNDO CONTATO EM DIANTE: HUMANO."          │
│                                                                              │
│  PRINCÍPIOS:                                                                 │
│  • Se a máquina pode fazer sem variação, faça a máquina fazer               │
│  • Liberar tempo comercial para vender, não para tarefas repetitivas        │
│  • Ligação humana dá conexão que aumenta percepção de valor                 │
│  • CRM é gestão 360º de vendas, marketing e atendimento                     │
│  • Tratar homem-hora da pessoa como se fosse seu                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## FRAMEWORK PRINCIPAL: PIPELINE DE 6 NÍVEIS DE FOLLOW-UP

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SISTEMA DE 6 NÍVEIS DE FOLLOW-UP                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ENTRADA    FU-1        FU-2         FU-3          FU-4        FU-5       │
│     │         │           │            │             │           │         │
│     ▼         ▼           ▼            ▼             ▼           ▼         │
│  ┌─────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐   │
│  │Lead │→│ Não    │→│ Engajou │→│Interessado│→│No-Show │→│Repescagem│   │
│  │Novo │  │Respondeu│  │Conversa│  │em Agendar│  │3 tent. │  │Atendidos│   │
│  └─────┘  └────────┘  └────────┘  └──────────┘  └────────┘  └─────────┘   │
│              │                         │                          │         │
│              │ 14 cadências            │ INFINITO                 │ 15 dias │
│              │ antes descarte          │ Perda 0%                 │ ultimato│
│              ▼                         ▼                          ▼         │
│         ┌─────────┐              ┌──────────┐               ┌─────────┐    │
│         │FU-4.5   │              │AGENDADO! │               │50% meta │    │
│         │Repesc.  │              │          │               │só aqui  │    │
│         │Mês      │              └──────────┘               │(V4)     │    │
│         │(SDR2)   │                                         └─────────┘    │
│         └─────────┘                                                        │
│              │                                                              │
│              ▼                                                              │
│         ┌─────────┐     ┌─────────────┐     ┌─────────────┐                │
│         │FU-6     │ ──▶ │SALES FARMING│ ──▶ │6 ciclos     │ ──▶ MARKETING │
│         │Transfer │     │(SDR2)       │     │2 em 2 meses │                │
│         └─────────┘     └─────────────┘     └─────────────┘                │
│                                                                              │
│  RESULTADO: Perda reduziu de 70-75% para quase 0%                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Detalhamento dos Níveis

| Nível | Nome | Cadências | Ação |
|-------|------|-----------|------|
| FU-1 | Não Respondeu | Até 14 | Cadência padrão, depois descarta |
| FU-2 | Engajou Conversa | Diferenciada | Mais personalização |
| FU-3 | Interessado Agendar | **INFINITO** | Nunca abandona, perda 0% |
| FU-4 | No-Show | 3 tentativas | Reagendamento ativo |
| FU-4.5 | Repescagem Mês | SDR2 | Nova abordagem |
| FU-5 | Atendidos Não Compraram | 15 dias | Ultimato mensal |
| FU-6 | Sales Farming | 6 ciclos | 2 em 2 meses, depois marketing |

---

## FRAMEWORK: 3 AUTOMAÇÕES CORE

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  AUTOMAÇÃO 1: RÁPIDA CONTACTAÇÃO                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐   20min delay   ┌─────────────────┐                    │
│  │  Aplicação /    │ ──────────────▶ │   WhatsApp      │                    │
│  │   Webinar       │   (Devzap)      │  Automático     │                    │
│  └─────────────────┘                 └─────────────────┘                    │
│                                                                              │
│  ┌─────────────────┐   2min delay    ┌─────────────────┐                    │
│  │     Funil       │ ──────────────▶ │   WhatsApp      │                    │
│  │   Aquisição     │   (Devzap)      │  Automático     │                    │
│  └─────────────────┘                 └─────────────────┘                    │
│                                                                              │
│  REGRA: Webinar finaliza → já manda calendário (pessoa fresca)              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  AUTOMAÇÃO 2: REMINDERS DE AGENDAMENTO                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AGENDOU → EMAIL1 → [DIA] → EMAIL2 → [TARDE] → EMAIL3+SMS                   │
│                                ↓                                             │
│           [1h ANTES] → EMAIL4+SMS → [10min] → EMAIL5+SMS                    │
│                                ↓                                             │
│                   NOTIFICAÇÃO INTERNA → LIGAÇÃO SDR                          │
│                                                                              │
│  TOTAL: 4 emails + 2 SMS + ligação SDR + notificação interna                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  AUTOMAÇÃO 3: SALES FARMING                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  APRESENTOU → [DIA SEGUINTE] → EMAIL AGRADECIMENTO                          │
│       ↓                                                                      │
│  [15 DIAS] → FOLLOW-UP 5 → ULTIMATO MÊS                                     │
│       ↓                                                                      │
│  NÃO COMPROU → 1 SEMANA → SEQUÊNCIA EMAILS+SMS → SALES FARMING              │
│       ↓                                                                      │
│  6 CICLOS (2 em 2 meses) → DESCARTADO PARA MARKETING                        │
│                                                                              │
│  RESULTADO V4: 50% da meta só com follow-up day                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## FRAMEWORK: SWEET SPOTS DE AGENDAMENTO

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PRIORIDADES DE HORÁRIO (B2B)                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PRIORIDADE 1 (SWEET SPOTS)      PRIORIDADE 1.5        PRIORIDADE 2       │
│   ══════════════════════          ═══════════════       ═══════════════    │
│         17:00h                         20:00h               15:30h          │
│         18:30h                    (se cliente quiser)   (intermediário)     │
│   (cliente terminou dia)                                                    │
│                                                                              │
│                              PRIORIDADE 3                                   │
│                              ═══════════════                                │
│                                   14:00h                                    │
│                             (cliente em rush)                               │
│                                                                              │
│   REGRA ABSOLUTA: Nunca marcar de manhã                                     │
│   "Venda de manhã é muito mais difícil - pessoa em rush não está no         │
│    humor de venda"                                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Grade de Horários Closers

| B2C (Noturno) | B2B (Vespertino) |
|---------------|------------------|
| 17:00h | 14:00h |
| 18:30h | 15:30h |
| 20:00h | 17:00h |
| 21:30h | 18:30h |

- **Duração**: 1h30 por apresentação com fechamento
- **Espaçamento**: 1h a 1h30 entre atendimentos
- **Máximo**: 4 atendimentos/dia por closer

---

## HEURÍSTICAS QUANTIFICADAS

### Sistema de Follow-Up

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MÉTRICAS DE FOLLOW-UP                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Follow-up 1: até 14 cadências antes de descartar                           │
│  Follow-up 3: perda reduziu de 70-75% para quase 0%                         │
│  Follow-up 4: até 3 tentativas de reagendamento (no-show)                   │
│  Follow-up 5: V4 atingiu 50% da meta só com follow-up day                   │
│  Sales Farming: 6 ciclos de 2 em 2 meses                                    │
│  Conversão geral: 20% = 80% assistiu e não comprou (repescagem)             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Delays de Automação

| Gatilho | Delay | Ação |
|---------|-------|------|
| Aplicação/Webinar | 20 minutos | WhatsApp automático |
| Funil Aquisição | 2 minutos | WhatsApp automático |
| Agendamento | Imediato | Sequência de 4 emails + 2 SMS |
| Apresentação | 1 dia | Email agradecimento |
| Não comprou | 15 dias | Follow-up 5 ultimato |

### CRM Configuração

- 72 horas para criação de conta
- 1-2 administradores máximo
- 5 campos obrigatórios cadastro
- 3 registros DNS: DMARC, SPF, DKIM
- 4+ canais integrados: Instagram, Email, SMS, WhatsApp
- 6 pipelines principais

---

## FRAMEWORK: 6 PIPELINES INTEGRADOS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ESTRUTURA DE PIPELINES                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐      ┌───────────────┐      ┌─────────────┐              │
│   │ PROSPECÇÃO  │      │SOCIAL SELLING │      │ PRÉ-VENDAS  │              │
│   │ (Outbound)  │      │   (SDR2)      │      │   (SDR1)    │              │
│   └──────┬──────┘      └───────┬───────┘      └──────┬──────┘              │
│          │                     │                     │                      │
│          │    ┌────────────────┴─────────────────────┘                      │
│          │    │                                                             │
│          │    ▼                                                             │
│          │ ┌────────────────────────────────────────┐                       │
│          │ │             VENDAS (Closers)           │                       │
│          │ │  Agendada → Follow → Perdida → Ganha   │                       │
│          │ └────────────────┬───────────────────────┘                       │
│          │                  │                                               │
│          │    ┌─────────────┴──────────────┐                               │
│          │    │                            │                               │
│          │    ▼                            ▼                               │
│          │ ┌─────────────┐          ┌───────────────┐                       │
│          │ │SALES FARMING│          │   SUCESSO DO  │                       │
│          │ │  (SDR2)     │          │    CLIENTE    │                       │
│          │ │ 6 ciclos    │          │   (Revenda)   │                       │
│          └─┴─────────────┘          └───────────────┘                       │
│                                                                              │
│   AUTOMAÇÕES: Movimentações entre pipelines via tags                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## FRAMEWORK: AUTOMAÇÃO IF/ELSE COM TAGS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LÓGICA DE EXCLUSÃO INTELIGENTE                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                    ┌─────────────────┐                                      │
│                    │  GATILHO ENTRY  │                                      │
│                    │ (DM, Form, Tag) │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│                             ▼                                               │
│                    ┌─────────────────┐                                      │
│                    │  TEM TAG        │                                      │
│                    │  PRÉ-VENDAS?    │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│               ┌─────────────┴─────────────┐                                │
│               │                           │                                │
│              SIM                         NÃO                               │
│               │                           │                                │
│               ▼                           ▼                                │
│        ┌────────────┐            ┌────────────────┐                        │
│        │  ENCERRA   │            │ ADD TAG        │                        │
│        │  (já sendo │            │ SOCIAL SELLING │                        │
│        │   tratado) │            └────────┬───────┘                        │
│        └────────────┘                     │                                │
│                                           ▼                                │
│                                  ┌────────────────┐                        │
│                                  │ CRIAR TAREFA   │                        │
│                                  │ OPORTUNIDADE   │                        │
│                                  │ Pipeline SS    │                        │
│                                  └────────────────┘                        │
│                                                                              │
│   REGRA: Evita duplicação de trabalho entre pipelines                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## METODOLOGIAS CRÍTICAS

### Metodologia: Follow-Up Day (Estratégia V4)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  FOLLOW-UP DAY - 50% DA META EM UM DIA                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Identificar todos que assistiram mas não compraram                      │
│  2. Juntar em lista de Follow-up Nível 5                                    │
│  3. Definir dia específico para mutirão                                     │
│  4. Time inteiro focado em repescagem                                       │
│  5. Oferecer ultimato: "última chance de garantir preço"                    │
│                                                                              │
│  RESULTADO V4: 50% da meta só com follow-up day                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Metodologia: Sincronização Status-Movimento

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  CLOSER ARRASTA CARD → SISTEMA FAZ O RESTO                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   AÇÃO DO CLOSER              AUTOMAÇÃO EXECUTA                             │
│   ════════════════            ══════════════════                            │
│                                                                              │
│   Move para "Não Compareceu"                                                │
│        ├──▶ Status agendamento → NO SHOW                                    │
│        ├──▶ Remove tag "Agendamento"                                        │
│        └──▶ Move para "Reagendamento" na origem                             │
│                                                                              │
│   Move para "Venda Ganha"                                                   │
│        ├──▶ Status agendamento → SHOW                                       │
│        ├──▶ Oportunidade → GANHA + Insere valor                             │
│        └──▶ Cria oportunidade em "Sucesso do Cliente"                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## FILOSOFIAS-CHAVE

| # | Filosofia |
|---|-----------|
| 1 | "Tudo que você puder automatizar sem perder personalização, faça" |
| 2 | "Primeiro contato: automação. Segundo contato em diante: humano" |
| 3 | "Antes perdíamos 70-75% dos leads, agora quase ninguém" |
| 4 | "Sweet spots são horários onde cliente terminou o dia" |
| 5 | "Lead que demonstrou interesse é muito melhor - dar mais atenção" |
| 6 | "Pessoa que assistiu e não comprou é lead valioso - fazer repescagem" |
| 7 | "CRM é gestão 360º de vendas, marketing e atendimento" |

---

## MODELOS MENTAIS

### Automação Inteligente

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PRIMEIRO CONTATO = BAIXO VALOR → AUTOMAÇÃO                                 │
│  RELACIONAMENTO = ALTO VALOR → HUMANO                                       │
│  OBJETIVO: Liberar tempo comercial para vender                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Oportunidade vs Contato

- **Contato**: dado de pessoa
- **Oportunidade**: potencial de receita
- Nem todo contato vira oportunidade

---

## CROSS-REFERENCES

### Agentes que Consomem

| Agente | Elementos Utilizados |
|--------|---------------------|
| CRM-AGENT | Configuração High Level, pipelines |
| AUTOMATION-AGENT | 3 automações core, If/Else, webhooks |
| SDR-AGENT | Sistema 6 níveis follow-up, cadências |
| CLOSER-AGENT | Agenda sweet spots, sincronização status |
| LNS-AGENT | Sequências de nutrição, Sales Farming |

### Dossiers Relacionados

| Dossier | Conexão |
|---------|---------|
| DOSSIER-5-PILARES-PRE-VENDAS | Follow-up e reminder sequences |
| DOSSIER-SHOW-RATES | Sweet spots e lembretes |
| DOSSIER-HIERARQUIA-SDR | Distribuição SDR1/SDR2 |
| DOSSIER-CALL-FUNNELS | Pipeline de vendas |

### Batches Fonte

| Batch | Contribuição |
|-------|--------------|
| BATCH-120 | 100% do conteúdo (85 elementos) |

---

## RASTREABILIDADE

```yaml
versao: 1.0.0
criado: 2026-01-10
fonte_primaria: Full Sales System
batches: [BATCH-120]
elementos_totais: 85
cascateado_por: REGRA-22
mission: MISSION-2026-001
phase: 5.6
```

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  DOSSIER-CRM-AUTOMACAO v1.0.0                                               ║
║  85 elementos | Full Sales System 100%                                       ║
║  "Automação + Personalização = Escala com Qualidade"                        ║
║                                                                              ║
║  Gerado por: JARVIS v3.33.0                                                 ║
║  Missão: MISSION-2026-001 | Phase 5.6                                       ║
║  Timestamp: 2026-01-10T16:35:00Z                                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
