# /benchmark - Comparação com Melhores Práticas

---
name: benchmark
description: Compara o Mega Brain com as melhores práticas da indústria
version: 1.0.0
author: JARVIS
triggers:
  - /benchmark
  - compare com melhores práticas
  - benchmark do sistema
---

## PROPÓSITO

Executar análise comparativa do Mega Brain contra as melhores práticas de:
- Arquitetura de conhecimento (Notion, Obsidian, PARA, Zettelkasten)
- Automação e IA (Claude Code workflows, Langchain, CrewAI)
- Gestão de vendas (Hormozi, Cole Gordon, Miner, Sandler)
- Gestão de projetos (Shape Up, OKRs, EOS, GTD)

---

## COMANDOS

### Benchmark Completo

```
/benchmark                        → Executa benchmark completo (todas as dimensões)
```

### Modos Específicos

```
/benchmark --dimension knowledge   → Apenas arquitetura de conhecimento
/benchmark --dimension automation  → Apenas automação e IA
/benchmark --dimension sales       → Apenas vendas
/benchmark --dimension projects    → Apenas gestão de projetos
```

### Opções

```
/benchmark --quick                 → Versão rápida (scores apenas)
/benchmark --compare [source]      → Compara com fonte específica
/benchmark --history               → Mostra evolução dos scores
/benchmark --gaps                  → Lista apenas gaps identificados
```

---

## WORKFLOW DE EXECUÇÃO

```
/benchmark
│
├── 1. COLETA
│   ├── Snapshot do estado atual
│   ├── Buscar referências (context7, web)
│   ├── Coletar métricas atuais
│   └── Identificar mudanças desde último benchmark
│
├── 2. ANÁLISE
│   ├── Comparar com cada área de benchmark
│   ├── Calcular scores por dimensão (0-100)
│   ├── Identificar gaps críticos
│   └── Priorizar por impacto
│
├── 3. SCORING
│   │
│   │  DIMENSÕES (25% cada):
│   │  ├── Knowledge Architecture
│   │  │   ├── structure_clarity
│   │  │   ├── navigation_ease
│   │  │   ├── linking_quality
│   │  │   ├── update_freshness
│   │  │   └── discovery_support
│   │  │
│   │  ├── Automation Maturity
│   │  │   ├── task_automation_rate
│   │  │   ├── error_handling
│   │  │   ├── self_healing
│   │  │   ├── async_capability
│   │  │   └── integration_breadth
│   │  │
│   │  ├── Sales Excellence
│   │  │   ├── playbook_coverage
│   │  │   ├── script_quality
│   │  │   ├── objection_handling
│   │  │   ├── metrics_tracking
│   │  │   └── team_structure
│   │  │
│   │  └── Project Management
│   │      ├── goal_clarity
│   │      ├── progress_tracking
│   │      ├── prioritization
│   │      ├── execution_rate
│   │      └── review_cadence
│   │
│   └── Overall Score = weighted_avg(all_dimensions)
│
├── 4. RECOMENDAÇÕES
│   ├── Gerar lista de melhorias ordenada
│   ├── Estimar esforço vs impacto
│   ├── Criar action items específicos
│   └── Propor próximos passos
│
└── 5. REPORT
    ├── Gerar BENCHMARK-REPORT-YYYY-WW.md
    ├── Atualizar BENCHMARK-SCORES.json
    └── Criar propostas em /evolve queue
```

---

## OUTPUT ESPERADO

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         BENCHMARK REPORT                                     ║
║                    Mega Brain vs Melhores Práticas                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Data: YYYY-MM-DD                                                            ║
║  Overall Score: XX/100                                                       ║
║  Trend: ↑/↓/→ vs last week                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                           SCORES POR DIMENSÃO                                │
├──────────────────────────────────────────────────────────────────────────────┤
│  Knowledge Architecture  │ ████████████████████░░░░ │ 80/100 │ ↑ +5         │
│  Automation Maturity     │ ██████████████████░░░░░░ │ 72/100 │ ↑ +3         │
│  Sales Excellence        │ ██████████████████████░░ │ 88/100 │ → 0          │
│  Project Management      │ ██████████████░░░░░░░░░░ │ 56/100 │ ↓ -2         │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                            TOP 5 GAPS                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  1. [CRITICAL] ClickUp integration missing                                   │
│     Reference: Process Auditor AIOS                                            │
│     Impact: HIGH | Effort: MEDIUM                                            │
│                                                                              │
│  2. [HIGH] No automated KPI tracking                                         │
│     Reference: OKR methodology                                               │
│     Impact: HIGH | Effort: HIGH                                              │
│                                                                              │
│  3. [MEDIUM] Web agents not configured                                       │
│     Reference: Boris Churney workflow                                        │
│     Impact: MEDIUM | Effort: LOW                                             │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                       PRÁTICAS DESCOBERTAS                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  ✨ [context7] New documentation pattern for skills                          │
│  ✨ [web] ClickUp + n8n integration best practices                           │
│  ✨ [internal] Council debate improving decision quality                     │
└──────────────────────────────────────────────────────────────────────────────┘

➡️  RECOMENDAÇÕES:
   1. Instalar ClickUp MCP e configurar integração
   2. Configurar web agents no claude.ai
   3. Criar dashboard de KPIs automatizado
```

---

## INTERPRETAÇÃO DE SCORES

```yaml
score_interpretation:
  90-100: "World class - referência para outros"
  80-89:  "Excellent - poucos gaps"
  70-79:  "Good - algumas melhorias necessárias"
  60-69:  "Needs improvement - gaps significativos"
  below_60: "Critical - ação urgente necessária"
```

---

## INTEGRAÇÃO

### Com AGENT-BENCHMARK

O comando `/benchmark` ativa o AGENT-BENCHMARK que:
1. Executa a coleta e análise
2. Consulta fontes externas (context7, web)
3. Gera relatório estruturado
4. Cria propostas para `/evolve`

### Com /evolve

Gaps identificados são automaticamente:
1. Categorizados por risco (AUTO/REVIEW/MAJOR)
2. Adicionados à queue do EVOLVER
3. Priorizados por impacto/esforço

---

## AGENDAMENTO

```
Manual:     /benchmark (on-demand)
Automático: Domingo 06:00 UTC (via GitHub Actions - futuro)
Trigger:    Quando health score < 70
```

---

## LOGS

```
Location: /logs/BENCHMARK/
├── BENCHMARK-YYYY-WW.md          → Relatório semanal
├── BENCHMARK-SCORES.json         → Histórico de scores
├── BENCHMARK-GAPS.jsonl          → Gaps identificados
└── BENCHMARK-PRACTICES.jsonl     → Práticas descobertas
```

---

**JARVIS COMMAND v1.0.0**
*Nunca pare de comparar com os melhores*
