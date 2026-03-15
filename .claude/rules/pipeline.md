---
paths:
  - "jarvis*.py"
  - "pipeline*.py"
  - "process*.py"
  - "extract*.py"
  - "batch*.py"
---

# Regras do Pipeline

> **NOTICE:** The legacy 5-phase system (Phases 1-5) is DEPRECATED.
> The current pipeline is MCE (Mental Cognitive Extraction) with 12 steps.
> See: `core/intelligence/pipeline/mce/` and `/pipeline-mce` skill.
> The principles below (sequencing, validation, DNA extraction) remain valid.

## Pipeline Principles (valid for both legacy and MCE)

- **Sequential processing** — do not advance without completing the current step
- **Batch-based** — process materials in manageable batches
- **State tracking** — update state after each step
- **Validation gates** — verify before advancing

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
