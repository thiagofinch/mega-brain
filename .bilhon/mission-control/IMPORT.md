# Mission Control Import Reference

> **Tipo:** Import Reference
> **Fonte:** /.claude/mission-control/
> **Status:** Active

## Descricao

Esta pasta e uma referencia para o mission control localizado em `/.claude/mission-control/`.

## Estrutura Mission Control

```
/.claude/mission-control/
├── MISSION-STATE.json          # Estado da missao atual
├── MISSION-PROGRESS.md         # Progresso visual
├── SKILL-INDEX.json            # Indice de skills (auto-gerado)
├── SOURCE-SYNC-STATE.json      # Estado do source-sync
├── PLANILHA-INDEX.json         # Snapshot da planilha
├── BATCH-LOGS/                 # Logs de batches processados
└── TEMPLATES/                  # Templates de logs
```

## Integracao com BILHON OS

Mission Control integra com BILHON OS para:
- Tracking de estado de missoes
- Logging de batches
- Sincronizacao com planilha (source-sync)
