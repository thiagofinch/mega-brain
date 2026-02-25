# Cost Tracking System

> **Fonte:** Ralph Inferno
> **Status:** Pending Import

## Descricao

Sistema de tracking de custos por operacao (tokens).

## Metricas Rastreadas

| Metrica | Descricao |
|---------|-----------|
| Tokens Input | Tokens de entrada por operacao |
| Tokens Output | Tokens de saida por operacao |
| Custo Estimado | Custo em USD por operacao |
| Acumulado Sessao | Total da sessao atual |
| Acumulado Projeto | Total do projeto |

## Output

Log em `/logs/cost-tracking.jsonl`:

```json
{
  "timestamp": "2026-01-17T05:41:00Z",
  "operation": "batch_processing",
  "tokens_input": 5000,
  "tokens_output": 2000,
  "cost_usd": 0.035,
  "session_total": 0.50,
  "project": "BILHON-OS"
}
```

## Arquivos a Importar

```
/_IMPORT/RALPH-INFERNO/core/lib/tokens.sh
```
