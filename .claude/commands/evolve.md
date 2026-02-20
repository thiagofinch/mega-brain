# /evolve - Evolução Autônoma do Sistema

---
name: evolve
description: Ativa agentes de evolução para melhorar o Mega Brain
version: 1.0.0
author: JARVIS
triggers:
  - /evolve
  - evolua o sistema
  - melhore o projeto
---

## PROPÓSITO

Ativar o ciclo de evolução autônoma do Mega Brain, coordenando os agentes:
- **EVOLVER** - Identifica gaps e implementa melhorias
- **CRITIC** - Questiona e valida mudanças
- **BENCHMARK** - Compara com melhores práticas

---

## COMANDOS

### Evolução Completa

```
/evolve                    → Ciclo completo (scan + analyze + propose + execute)
```

### Modos Específicos

```
/evolve --scan             → Apenas escaneia o sistema (read-only)
/evolve --analyze          → Scan + análise de gaps
/evolve --propose          → Scan + análise + propostas (sem execução)
/evolve --execute [id]     → Executa melhoria específica aprovada
/evolve --report           → Gera relatório de evolução
```

### Opções

```
/evolve --quick            → Versão rápida (apenas métricas)
/evolve --deep             → Análise profunda (todas as dimensões)
/evolve --auto             → Executa melhorias automáticas (low-risk)
/evolve --dry-run          → Simula sem fazer mudanças
```

---

## WORKFLOW DE EXECUÇÃO

```
/evolve (ciclo completo)
│
├── 1. SCAN
│   ├── Ler MISSION-STATE.json
│   ├── Verificar integridade de arquivos
│   ├── Catalogar estado atual
│   └── Gerar SCAN-SNAPSHOT.json
│
├── 2. ANALYZE
│   ├── Comparar com estado ideal
│   ├── Identificar gaps por categoria:
│   │   ├── KNOWLEDGE (fontes, dossiers, DNAs)
│   │   ├── AUTOMATION (scripts, workflows)
│   │   ├── AGENTS (MEMORYs, definições)
│   │   └── SYSTEM (logs, configs, docs)
│   └── Calcular health score
│
├── 3. PROPOSE
│   ├── Gerar lista de melhorias
│   ├── Priorizar por impacto/esforço
│   ├── Classificar por risco:
│   │   ├── AUTO (executar automaticamente)
│   │   ├── REVIEW (requer aprovação)
│   │   └── MAJOR (requer planejamento)
│   └── Consultar AGENT-CRITIC
│
├── 4. EXECUTE (melhorias AUTO apenas)
│   ├── Executar melhorias low-risk
│   ├── Logar todas as ações
│   └── Atualizar estados
│
└── 5. REPORT
    ├── Gerar EVOLUTION-REPORT.md
    ├── Listar melhorias REVIEW pendentes
    └── Sugerir próximos passos
```

---

## CATEGORIAS DE MELHORIA

### AUTO (Execução Automática)

```
Melhorias que podem ser executadas sem aprovação:
├── Limpeza de arquivos temporários
├── Regeneração de índices
├── Atualização de timestamps
├── Correção de typos em docs
├── Normalização de formatação
└── Atualização de métricas
```

### REVIEW (Requer Aprovação)

```
Melhorias que requerem validação:
├── Novos comandos
├── Novos agentes
├── Mudanças em templates
├── Refatoração de scripts
└── Atualizações de regras
```

### MAJOR (Requer Planejamento)

```
Mudanças estruturais:
├── Mudanças em CLAUDE.md
├── Nova arquitetura
├── Novas integrações (MCPs)
├── Refatoração grande
└── Mudanças em pipeline
```

---

## OUTPUT ESPERADO

### Após /evolve

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         EVOLUTION CYCLE COMPLETE                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Timestamp: YYYY-MM-DD HH:MM                                                ║
║  Duration: X minutes                                                        ║
║  Health Score: XX/100 (↑/↓ vs last)                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                              SCAN RESULTS                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  Files scanned:        XXXX                                                 │
│  Agents verified:      XX                                                   │
│  Commands checked:     XX                                                   │
│  Scripts analyzed:     XX                                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                              GAPS IDENTIFIED                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│  [CRITICAL] X gaps                                                          │
│  [HIGH]     X gaps                                                          │
│  [MEDIUM]   X gaps                                                          │
│  [LOW]      X gaps                                                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           ACTIONS TAKEN (AUTO)                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  ✅ [action 1]                                                              │
│  ✅ [action 2]                                                              │
│  ✅ [action 3]                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         PENDING REVIEW (X items)                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  1. [REVIEW] [description] - /evolve --execute 001                          │
│  2. [REVIEW] [description] - /evolve --execute 002                          │
│  3. [MAJOR]  [description] - Requires planning                              │
└──────────────────────────────────────────────────────────────────────────────┘

➡️  Top 3 recommendations:
   1. [recommendation]
   2. [recommendation]
   3. [recommendation]
```

---

## INTEGRAÇÃO COM AGENTES

```
/evolve invoca:
├── AGENT-EVOLVER → Executa o ciclo de evolução
├── AGENT-CRITIC → Valida propostas antes de executar
├── AGENT-BENCHMARK → Fornece referências de melhores práticas
└── JARVIS → Coordena e reporta
```

---

## SCHEDULING (Futuro)

```
Quando integrado com GitHub Actions:
├── Diário (06:00 UTC): /evolve --quick
├── Semanal (Sunday): /evolve --deep + /benchmark
└── On-demand: Via comando ou trigger
```

---

## LOGS

```
Location: /logs/EVOLUTION/
├── EVOLUTION-YYYY-MM-DD.md       → Relatório diário
├── EVOLUTION-ACTIONS.jsonl        → Ações executadas
├── EVOLUTION-PROPOSALS.jsonl      → Propostas pendentes
└── EVOLUTION-METRICS.json         → Histórico de health scores
```

---

**JARVIS COMMAND v1.0.0**
*Evolução contínua do Mega Brain*
