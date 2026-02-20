# /mission-autopilot - EXECUÇÃO AUTÔNOMA COMPLETA

> **Sistema:** JARVIS Mission Autopilot v1.0
> **Modo:** Zero interrupções, checkpoints automáticos
> **Logs:** Visíveis no chat em tempo real

---

## SINTAXE

```
/mission-autopilot [planilha_id] [--flags]
```

| Flag | Descrição |
|------|-----------|
| `--from-phase N` | Iniciar da fase N (1-5) |
| `--dry-run` | Preview sem executar |
| `--verbose` | Logs expandidos (padrão: compactos) |
| `--skip-download` | Pular Fase 2 (já tem arquivos) |
| `--batch-size N` | Tamanho do batch na Fase 4 (padrão: 8) |

---

## COMPORTAMENTO

### PRINCÍPIO CORE

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   EXECUTAR → LOGAR → CHECKPOINT → CONTINUAR                                  │
│                                                                              │
│   • SEM perguntas de confirmação                                             │
│   • SEM pausas entre fases                                                   │
│   • COM logs visíveis no chat                                                │
│   • COM checkpoints salvos (recuperáveis)                                    │
│   • COM progresso em tempo real                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## EXECUÇÃO DETALHADA

Ao receber `/mission-autopilot [planilha_id]`:

### STEP 0: INICIALIZAÇÃO

```
DISPLAY:
═══════════════════════════════════════════════════════════════════════════════
     █████╗ ██╗   ██╗████████╗ ██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗
    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝
    ███████║██║   ██║   ██║   ██║   ██║██████╔╝██║██║     ██║   ██║   ██║
    ██╔══██║██║   ██║   ██║   ██║   ██║██╔═══╝ ██║██║     ██║   ██║   ██║
    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║     ██║███████╗╚██████╔╝   ██║
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝
═══════════════════════════════════════════════════════════════════════════════
                    JARVIS MISSION AUTOPILOT v1.0
                    Execução Autônoma das 5 Fases
═══════════════════════════════════════════════════════════════════════════════

📋 Planilha: [PLANILHA_ID]
🕐 Iniciado: [TIMESTAMP]
⚙️  Modo: AUTOPILOT (zero interrupções)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FASES A EXECUTAR:
┌────┬─────────────────────┬──────────────────────────────────────────────────┐
│ #  │ FASE                │ DESCRIÇÃO                                        │
├────┼─────────────────────┼──────────────────────────────────────────────────┤
│ 1  │ INVENTÁRIO          │ Mapear planilha vs INBOX                         │
│ 2  │ DOWNLOAD            │ Baixar arquivos faltantes                        │
│ 3  │ ORGANIZAÇÃO         │ Estruturar pastas e renomear                     │
│ 4  │ PIPELINE JARVIS     │ Chunking → Insights → Dossiers                   │
│ 5  │ ALIMENTAÇÃO         │ Atualizar agentes e knowledge base               │
└────┴─────────────────────┴──────────────────────────────────────────────────┘

⏳ Iniciando em 3 segundos...

```

THEN:
  CREATE mission if not exists
  SET autopilot_mode = true
  SET checkpoint_auto = true
  SAVE initial state to MISSION-STATE.json
  CONTINUE to Phase 1

---

### PHASE 1: INVENTÁRIO (Automático)

```
DISPLAY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ███████╗ █████╗ ███████╗███████╗     ██╗
                              ██╔════╝██╔══██╗██╔════╝██╔════╝    ███║
                              █████╗  ███████║███████╗█████╗      ╚██║
                              ██╔══╝  ██╔══██║╚════██║██╔══╝       ██║
                              ██║     ██║  ██║███████║███████╗     ██║
                              ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝     ╚═╝
                                        INVENTÁRIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

EXECUTE:
  1. python scripts/read_planilha_complete.py [planilha_id] --auto
  2. python scripts/compare_source_vs_inbox.py PLANILHA-COMPLETE-LIST.json

DISPLAY LOG (compacto):
```
┌─ FASE 1 CHECKPOINT ──────────────────────────────────────────────────────────┐
│                                                                              │
│  ✅ Planilha lida: [N] itens em [M] abas                                     │
│  ✅ Comparação: [X] no INBOX, [Y] faltantes, [Z]% match                      │
│                                                                              │
│  📁 Salvos:                                                                  │
│     • PLANILHA-COMPLETE-LIST.json                                            │
│     • COMPARISON-REPORT.json                                                 │
│     • INVENTORY.json                                                         │
│                                                                              │
│  ⏱️  Duração: [TIME]                                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SAVE checkpoint to:
  - MISSION-STATE.json (phase: 1, status: COMPLETE)
  - logs/AUTOPILOT/PHASE-1-CHECKPOINT-[TIMESTAMP].json

CONTINUE to Phase 2 (NO PAUSE)

---

### PHASE 2: DOWNLOAD (Automático)

```
DISPLAY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ███████╗ █████╗ ███████╗███████╗    ██████╗
                              ██╔════╝██╔══██╗██╔════╝██╔════╝    ╚════██╗
                              █████╗  ███████║███████╗█████╗       █████╔╝
                              ██╔══╝  ██╔══██║╚════██║██╔══╝      ██╔═══╝
                              ██║     ██║  ██║███████║███████╗    ███████╗
                              ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝    ╚══════╝
                                        DOWNLOAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

IF files_missing > 0:
  EXECUTE:
    python scripts/download_missing_from_source.py COMPARISON-REPORT.json

  DISPLAY progress (streaming):
  ```
  ⬇️  Baixando [1/N]: arquivo1.txt... ✅
  ⬇️  Baixando [2/N]: arquivo2.txt... ✅
  ⬇️  Baixando [3/N]: arquivo3.txt... ✅
  ...
  ```

ELSE:
  DISPLAY: "✅ Nenhum arquivo faltante. Pulando download."

DISPLAY LOG:
```
┌─ FASE 2 CHECKPOINT ──────────────────────────────────────────────────────────┐
│                                                                              │
│  ✅ Downloads: [X] arquivos ([Y] MB)                                         │
│  ✅ Erros: [N] (ver ERROR-QUARANTINE/)                                       │
│  ✅ Taxa sucesso: [Z]%                                                       │
│                                                                              │
│  📁 Salvos:                                                                  │
│     • DOWNLOAD-LOG.json                                                      │
│                                                                              │
│  ⏱️  Duração: [TIME]                                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SAVE checkpoint
CONTINUE to Phase 3 (NO PAUSE)

---

### PHASE 3: ORGANIZAÇÃO (Automático)

```
DISPLAY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ███████╗ █████╗ ███████╗███████╗    ██████╗
                              ██╔════╝██╔══██╗██╔════╝██╔════╝    ╚════██╗
                              █████╗  ███████║███████╗█████╗       █████╔╝
                              ██╔══╝  ██╔══██║╚════██║██╔══╝       ╚═══██╗
                              ██║     ██║  ██║███████║███████╗    ██████╔╝
                              ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝    ╚═════╝
                                       ORGANIZAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

EXECUTE sequentially:
  1. python scripts/inbox_auto_organize.py --execute
  2. python scripts/reorganize_by_planilha.py --execute
  3. python scripts/clean_duplicates.py --execute

DISPLAY LOG:
```
┌─ FASE 3 CHECKPOINT ──────────────────────────────────────────────────────────┐
│                                                                              │
│  ✅ Arquivos organizados: [X]                                                │
│  ✅ Renomeados: [Y]                                                          │
│  ✅ Duplicatas removidas: [Z]                                                │
│  ✅ Pastas criadas: [N]                                                      │
│                                                                              │
│  📁 Salvos:                                                                  │
│     • ORG-LOG.json                                                           │
│                                                                              │
│  ⏱️  Duração: [TIME]                                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SAVE checkpoint
CONTINUE to Phase 4 (NO PAUSE)

---

### PHASE 4: PIPELINE JARVIS (Automático, Multi-Batch)

```
DISPLAY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ███████╗ █████╗ ███████╗███████╗    ██╗  ██╗
                              ██╔════╝██╔══██╗██╔════╝██╔════╝    ██║  ██║
                              █████╗  ███████║███████╗█████╗      ███████║
                              ██╔══╝  ██╔══██║╚════██║██╔══╝      ╚════██║
                              ██║     ██║  ██║███████║███████╗         ██║
                              ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝         ╚═╝
                                     PIPELINE JARVIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Arquivos a processar: [TOTAL]
📦 Batches estimados: [N] (de [BATCH_SIZE] arquivos)

```

IDENTIFY new files:
  python scripts/identify_new_files.py --output NEW-FILES-TO-PROCESS.json

SPLIT into batches of [BATCH_SIZE]

FOR EACH batch IN batches:

  DISPLAY:
  ```
  ┌─ BATCH [X]/[TOTAL] ────────────────────────────────────────────────────────┐
  │                                                                            │
  │  📂 Fonte: [SOURCE_NAME]                                                   │
  │  📄 Arquivos: [LIST]                                                       │
  │                                                                            │
  │  ⏳ Phase 1: Initialization... ✅                                          │
  │  ⏳ Phase 2: Chunking ([N] chunks)... ✅                                    │
  │  ⏳ Phase 3: Entity Resolution... ✅                                        │
  │  ⏳ Phase 4: Insight Extraction ([N] insights)... ✅                        │
  │  ⏳ Phase 5: Narrative Synthesis... ✅                                      │
  │  ⏳ Phase 6: Dossier Compilation... ✅                                      │
  │  ⏳ Phase 7: Agent Enrichment... ✅                                         │
  │  ⏳ Phase 8: Finalization... ✅                                             │
  │                                                                            │
  │  ✅ BATCH [X] COMPLETO                                                     │
  │                                                                            │
  │  📈 Métricas:                                                              │
  │     • Chunks: [N]                                                          │
  │     • Insights: [N] (H:[X] M:[Y] L:[Z])                                    │
  │     • Heurísticas ★★★★★: [N]                                               │
  │     • Frameworks: [N]                                                      │
  │                                                                            │
  │  ⏱️  Duração: [TIME]                                                       │
  │                                                                            │
  └────────────────────────────────────────────────────────────────────────────┘
  ```

  SAVE batch checkpoint to:
    - logs/batches/BATCH-[NNN].md
    - .claude/mission-control/batch-logs/BATCH-[NNN].json

  UPDATE MISSION-STATE.json (batch_current++, metrics++)

  CONTINUE to next batch (NO PAUSE)

END FOR

DISPLAY PHASE 4 SUMMARY:
```
┌─ FASE 4 CHECKPOINT ──────────────────────────────────────────────────────────┐
│                                                                              │
│  ✅ Batches processados: [X]/[X]                                             │
│  ✅ Arquivos processados: [Y]                                                │
│  ✅ Chunks criados: [Z]                                                      │
│  ✅ Insights extraídos: [N]                                                  │
│  ✅ Heurísticas ★★★★★: [M]                                                   │
│                                                                              │
│  📁 Salvos:                                                                  │
│     • logs/batches/BATCH-001.md ... BATCH-[N].md                         │
│     • .claude/mission-control/batch-logs/                                    │
│                                                                              │
│  ⏱️  Duração total Fase 4: [TIME]                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SAVE checkpoint
CONTINUE to Phase 5 (NO PAUSE)

---

### PHASE 5: ALIMENTAÇÃO (Automático)

```
DISPLAY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              ███████╗ █████╗ ███████╗███████╗    ███████╗
                              ██╔════╝██╔══██╗██╔════╝██╔════╝    ██╔════╝
                              █████╗  ███████║███████╗█████╗      ███████╗
                              ██╔══╝  ██╔══██║╚════██║██╔══╝      ╚════██║
                              ██║     ██║  ██║███████║███████╗    ███████║
                              ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝    ╚══════╝
                                       ALIMENTAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

EXECUTE cascading for all processed content:
  1. Update PERSON agents (SOUL, MEMORY, DNA)
  2. Update CARGO agents contributions
  3. Update/Create Theme Dossiers
  4. Update sua-empresa SOWs
  5. Validate integrity

FOR EACH source_person processed:
  DISPLAY:
  ```
  🧠 Alimentando: [PERSON_NAME]
     • AGENT.md: ✅ atualizado
     • SOUL.md: ✅ atualizado
     • MEMORY.md: ✅ +[N] elementos
     • DNA-CONFIG.yaml: ✅ +[M] itens nas 5 camadas
  ```

DISPLAY LOG:
```
┌─ FASE 5 CHECKPOINT ──────────────────────────────────────────────────────────┐
│                                                                              │
│  ✅ PERSON Agents atualizados: [LIST]                                        │
│  ✅ CARGO Agents enriquecidos: [LIST]                                        │
│  ✅ Theme Dossiers atualizados: [N]                                          │
│  ✅ Validação de integridade: PASSED                                         │
│                                                                              │
│  📁 Salvos:                                                                  │
│     • FEED-LOG.json                                                          │
│     • agents/*/MEMORY.md (atualizados)                                    │
│     • knowledge/dossiers/ (atualizados)                                   │
│                                                                              │
│  ⏱️  Duração: [TIME]                                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

SAVE final checkpoint

---

### STEP FINAL: RELATÓRIO COMPLETO

```
DISPLAY:
═══════════════════════════════════════════════════════════════════════════════
     ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗     ███████╗████████╗███████╗
    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║     ██╔════╝╚══██╔══╝██╔════╝
    ██║     ██║   ██║██╔████╔██║██████╔╝██║     █████╗     ██║   █████╗
    ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝     ██║   ██╔══╝
    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ███████╗███████╗   ██║   ███████╗
     ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚══════╝
═══════════════════════════════════════════════════════════════════════════════
                        MISSION AUTOPILOT COMPLETA
═══════════════════════════════════════════════════════════════════════════════

📋 Missão: [MISSION_ID]
🕐 Início: [START_TIME]
🏁 Fim: [END_TIME]
⏱️  Duração total: [TOTAL_TIME]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESUMO POR FASE

┌────┬─────────────────────┬──────────┬──────────────────────────────────────┐
│ #  │ FASE                │ TEMPO    │ RESULTADO                            │
├────┼─────────────────────┼──────────┼──────────────────────────────────────┤
│ 1  │ Inventário          │ [TIME]   │ [N] itens mapeados                   │
│ 2  │ Download            │ [TIME]   │ [N] arquivos baixados                │
│ 3  │ Organização         │ [TIME]   │ [N] arquivos organizados             │
│ 4  │ Pipeline Jarvis     │ [TIME]   │ [N] batches, [M] insights            │
│ 5  │ Alimentação         │ [TIME]   │ [N] agentes atualizados              │
└────┴─────────────────────┴──────────┴──────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 MÉTRICAS FINAIS

│ Arquivos processados     │ [TOTAL]
│ Chunks criados           │ [TOTAL]
│ Insights extraídos       │ [TOTAL] (H:[X] M:[Y] L:[Z])
│ Heurísticas ★★★★★        │ [TOTAL]
│ Frameworks               │ [TOTAL]
│ Metodologias             │ [TOTAL]
│ Agentes atualizados      │ [LIST]
│ Dossiers criados/atualizados │ [TOTAL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 ARQUIVOS GERADOS

• MISSION-STATE.json (atualizado)
• PLANILHA-COMPLETE-LIST.json
• COMPARISON-REPORT.json
• INVENTORY.json
• DOWNLOAD-LOG.json
• ORG-LOG.json
• logs/batches/BATCH-001.md ... BATCH-[N].md
• logs/AUTOPILOT/AUTOPILOT-COMPLETE-[TIMESTAMP].md
• FEED-LOG.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ MISSÃO COMPLETA

"Senhor, todas as 5 fases foram executadas com sucesso.
 [N] arquivos processados, [M] insights extraídos, [K] agentes atualizados.
 O conhecimento está pronto para consulta."

                                                           - J.A.R.V.I.S.

═══════════════════════════════════════════════════════════════════════════════
```

SAVE final report to:
  - logs/AUTOPILOT/AUTOPILOT-COMPLETE-[TIMESTAMP].md
  - logs/FULL/MISSION-[ID]-COMPLETE.md

UPDATE MISSION-STATE.json:
  - status: "COMPLETE"
  - completed_at: [TIMESTAMP]
  - autopilot_completed: true

---

## RECUPERAÇÃO DE FALHAS

Se o autopilot falhar em qualquer ponto:

```
1. Estado é preservado em MISSION-STATE.json
2. Último checkpoint salvo em logs/AUTOPILOT/
3. Para retomar: /mission-autopilot --from-phase [N]
4. Ou: /mission resume (modo manual)
```

---

## EXEMPLOS

```bash
# Executar do zero
/mission-autopilot [YOUR_SHEET_ID_HERE]

# Retomar da Fase 4
/mission-autopilot --from-phase 4

# Preview sem executar
/mission-autopilot [YOUR_SHEET_ID_HERE] --dry-run

# Com batch size maior
/mission-autopilot [YOUR_SHEET_ID_HERE] --batch-size 12

# Pular download (já tem arquivos)
/mission-autopilot --from-phase 3 --skip-download
```

---

## DIFERENÇA VS /mission resume

| Aspecto | /mission resume | /mission-autopilot |
|---------|-----------------|---------------------|
| Interrupções | PARA após cada ação | ZERO paradas |
| Confirmação | Pede a cada fase | Nenhuma |
| Logs | No final | Em tempo real |
| Checkpoints | Manuais | Automáticos |
| Uso | Controle total | Set-and-forget |

---

## LOGS GERADOS

```
logs/
├── AUTOPILOT/
│   ├── PHASE-1-CHECKPOINT-[TIMESTAMP].json
│   ├── PHASE-2-CHECKPOINT-[TIMESTAMP].json
│   ├── PHASE-3-CHECKPOINT-[TIMESTAMP].json
│   ├── PHASE-4-CHECKPOINT-[TIMESTAMP].json
│   ├── PHASE-5-CHECKPOINT-[TIMESTAMP].json
│   └── AUTOPILOT-COMPLETE-[TIMESTAMP].md
├── BATCHES/
│   └── BATCH-XXX.md (um por batch)
└── FULL/
    └── MISSION-[ID]-COMPLETE.md
```

---

## AVISO

Este comando executa TODAS as 5 fases SEM interrupções.

Use com planilhas já validadas. Para primeira execução ou debug, prefira `/mission resume` que permite controle granular.

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2026-01-14 | Criação inicial |
