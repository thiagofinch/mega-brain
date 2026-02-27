---
paths:
  - "jarvis*.py"
  - "pipeline*.py"
  - "process*.py"
  - "extract*.py"
  - "batch*.py"
---

# Regras do Pipeline Jarvis

## 🎯 Fases (BLOQUEANTES)

```
FASE 1 → FASE 2 → FASE 3 → FASE 4 → FASE 5
   │         │         │         │         │
   ▼         ▼         ▼         ▼         ▼
Inventário Download Organização Pipeline Alimentação
```

**NÃO avançar fase sem completar a anterior.**

## 📊 Critérios de conclusão por fase

| Fase | Completa quando |
|------|-----------------|
| 1 - Inventário | Todas fontes mapeadas, totais conhecidos |
| 2 - Download | Todos arquivos baixados, quarentena vazia |
| 3 - Organização | Estrutura validada, arquivos renomeados |
| 4 - Pipeline | Todos batches processados, DNA extraído |
| 5 - Alimentação | Todos agentes alimentados |

## 🧬 DNA Cognitivo (extrair sempre)

| Tag | O que é | Exemplo |
|-----|---------|---------|
| [FILOSOFIA] | Crenças fundamentais | "Dinheiro é trocar valor" |
| [MODELO-MENTAL] | Forma de entender | "Funil de vendas" |
| [HEURISTICA] | Atalho de decisão | "Se lead não responde em 24h, descartar" |
| [FRAMEWORK] | Estrutura de análise | "CLOSER framework" |
| [METODOLOGIA] | Processo passo-a-passo | "7 passos do fechamento" |

## 📦 Batches

- Processar em batches de ~10 arquivos
- Logar cada batch (MD + JSON)
- Atualizar MISSION-STATE.json após cada batch
- Nunca processar batch sem verificar fase atual

## ⚠️ Antes de processar

1. Ler MISSION-STATE.json
2. Confirmar fase atual
3. Verificar último batch processado
4. Verificar se é último batch da SOURCE (trigger consolidação)
5. Verificar se é último batch da FASE (trigger PHASE-COMPLETE)

## 🔗 Referência

Para templates de batch: `@/reference/JARVIS-LOGGING-SYSTEM-V3.md`
