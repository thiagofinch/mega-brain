# PLAYBOOK-SCORECARDS

> **Versao:** 1.0.0
> **Criado em:** 2026-01-13
> **Ultima atualizacao:** 2026-01-13
> **Fontes:** The Scalable Company (BATCH-088), Ryan Deiss
> **Objetivo:** Framework completo para construcao e implementacao de scorecards empresariais

---

## FRAMEWORK MASTER: 3-Step Scorecard Build

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    3-STEP SCORECARD BUILD PROCESS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: IDENTIFY DASHBOARD CATEGORIES                                      │
│  ├── Use High Output Team Canvas teams                                      │
│  ├── Growth | Fulfillment | Operations | Finance                            │
│  └── Maximum 5-7 categories on company scorecard                            │
│                                                                             │
│  STEP 2: BRAINSTORM METRICS (Beach Vacation Question)                       │
│  ├── "You're on vacation, just your phone..."                               │
│  ├── "What 3-5 numbers do you want to see for [TEAM]?"                      │
│  └── Forces prioritization to CRITICAL metrics only                         │
│                                                                             │
│  STEP 3: BACKTEST PREVIOUS MONTH/QUARTER                                    │
│  ├── Take proposed metrics                                                  │
│  ├── Attempt to gather actual historical data                               │
│  ├── Validates: Can we actually measure this?                               │
│  └── If fails: build tracking system OR choose different metric             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## BEACH VACATION QUESTION (Metric Selection)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE BEACH VACATION QUESTION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROMPT:                                                                    │
│  "You're on vacation at the beach, no laptop, just your phone.              │
│   What are the 3-5 numbers you want to see for [TEAM]?"                     │
│                                                                             │
│  PURPOSE:                                                                   │
│  • Forces prioritization to CRITICAL metrics only                           │
│  • Eliminates vanity metrics                                                │
│  • Creates focus on what actually moves business                            │
│                                                                             │
│  CONSTRAINTS:                                                               │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  • Maximum 3-5 metrics per team                             │           │
│  │  • Should be checkable quickly                              │           │
│  │  • Must indicate health of that function                    │           │
│  │  • "On an island, do you care about this metric?"           │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  FILOSOFIA: If it doesn't pass the Beach Vacation test,                     │
│             it doesn't belong on the company scorecard.                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## COMPANY vs TEAM SCORECARD ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCORECARD HIERARCHY                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROBLEMA: Metric overload - teams tracking 20+ metrics                     │
│  SOLUCAO: Separar North Star (company) de Operational (team)                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  COMPANY SCORECARD (ISLAND TEST = YES)                      │           │
│  │  "Would you care about this metric if on vacation?"         │           │
│  │                                                             │           │
│  │  • Total Sales                                              │           │
│  │  • Revenue                                                  │           │
│  │  • NPS                                                      │           │
│  │  • Gross Margin                                             │           │
│  │  • Profit                                                   │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  TEAM SCORECARD (ISLAND TEST = NO)                          │           │
│  │  "Departmental metrics that feed North Stars"               │           │
│  │                                                             │           │
│  │  Marketing: Leads, CPC, Conversion Rate                     │           │
│  │  Sales: Pipeline, Show Rate, Close Rate                     │           │
│  │  Ops: SLA Compliance, Ticket Resolution Time                │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  HEURISTICA: Max 3-5 metricas por team scorecard                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MIND METHODOLOGY (Profit-First Metrics)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MIND = Most Important Number and Drivers                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌───────────────────┐                                    │
│                    │  MOST IMPORTANT   │                                    │
│                    │     NUMBER        │                                    │
│                    │  (Usually PROFIT) │                                    │
│                    └─────────┬─────────┘                                    │
│                              │                                              │
│           ┌──────────────────┼──────────────────┐                          │
│           ↓                  ↓                  ↓                          │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│    │   DRIVER 1   │  │   DRIVER 2   │  │   DRIVER 3   │                    │
│    │   Revenue    │  │     COGS     │  │   Expenses   │                    │
│    └──────────────┘  └──────────────┘  └──────────────┘                    │
│                                                                             │
│  PRINCIPE: Start with profit, work backwards to drivers                     │
│                                                                             │
│  PROFIT TARGETS:                                                            │
│  • 25% net profit = minimum target for healthy business                     │
│  • 40% net profit = target for online/digital business                      │
│                                                                             │
│  PROCESSO:                                                                  │
│  1. Define Most Important Number (usually Profit)                           │
│  2. Identify 3-5 key drivers                                                │
│  3. Build scorecard around drivers                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## BACKTESTING METHODOLOGY

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKTESTING = Measure in Reverse                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROCESSO:                                                                  │
│  1. Take proposed metrics                                                   │
│  2. Go back 1 month or 1 quarter                                            │
│  3. Attempt to gather actual data for each metric                           │
│  4. Validate: Can we actually measure this?                                 │
│                                                                             │
│  PURPOSES:                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  Validates data availability                                │           │
│  │  Creates baseline for future targets                        │           │
│  │  Reveals gaps in tracking systems                           │           │
│  │  Proves metric is measurable                                │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  IF METRIC FAILS BACKTEST:                                                  │
│  • Option A: Build tracking system first                                    │
│  • Option B: Choose different metric you CAN measure                        │
│                                                                             │
│  REGRA: If you can't measure it historically,                               │
│         you can't measure it going forward.                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MANUAL vs AUTOMATED SCORECARDS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MANUAL vs AUTOMATED SCORECARDS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MANUAL + SUBJECTIVE (RECOMMENDED)                                          │
│  ├── Data input manually each week                                          │
│  ├── Color coding set by metric owner (not algorithm)                       │
│  └── BENEFITS:                                                              │
│      ├── Greater insights (team truly knows numbers)                        │
│      ├── Greater ownership (can't blame formula)                            │
│      └── Team develops "Matrix vision" for patterns                         │
│                                                                             │
│  AUTOMATED + OBJECTIVE (NOT RECOMMENDED)                                    │
│  └── PROBLEMS:                                                              │
│      ├── Team divorced from what numbers mean                               │
│      ├── "Tens of thousands of dollars" wasted                              │
│      └── No one has sense of what numbers "should be"                       │
│                                                                             │
│  FILOSOFIA: "Resist the urge to build automated scorecards"                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## HEURISTICAS QUANTIFICADAS

| Heuristica | Valor | Contexto |
|------------|-------|----------|
| Max metricas per team | 3-5 | Company scorecard level |
| Max categories | 5-7 | Dashboard categories |
| Backtest period | 1 month or 1 quarter | Standard validation |
| Profit target (min) | 25% | Healthy business |
| Profit target (digital) | 40% | Online/digital business |
| Objectives focus | 3 max | "10 objectives = hit 1, 3 objectives = hit 3" |
| Targets over benchmark | 10-20% | Stretch but achievable |

---

## IMPLEMENTACAO PASSO A PASSO

### Semana 1: Categorias
1. Mapear High Output Team Canvas
2. Identificar 5-7 categorias principais
3. Definir equipes responsaveis

### Semana 2: Metricas
1. Reunir cada equipe
2. Aplicar Beach Vacation Question
3. Listar 3-5 metricas por equipe

### Semana 3: Backtesting
1. Pegar metricas propostas
2. Tentar coletar dados do ultimo mes/trimestre
3. Validar quais sao mensuraveis

### Semana 4: Implementacao
1. Criar template de scorecard
2. Definir owners de cada metrica
3. Estabelecer ritmo semanal de atualizacao

---

## CASCATEAMENTO

```yaml
cascateamento:
  timestamp: 2026-01-13T10:57:00Z
  source_batches: ["BATCH-088"]
  source_name: "The Scalable Company (Ryan Deiss)"
  chunk_ids: ["TSC-088-FW-001", "TSC-088-M-001", "TSC-088-M-002", "TSC-088-M-003", "TSC-088-H-001"]
```

---

*PLAYBOOK-SCORECARDS v1.0.0 - Framework completo para scorecard empresarial*
*Criado: 2026-01-13 (BATCH-088 Cascading)*
