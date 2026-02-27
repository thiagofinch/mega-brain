# SKILL: Source Sync - Sincronização com Planilha

> **Versão:** 1.0.0
> **Criado:** 2026-01-13
> **Propósito:** Detectar NOVOS arquivos na planilha, taguear na fonte, baixar organizados.

---

## Comando

```
/source-sync [opções]
```

## Opções

| Opção | Descrição |
|-------|-----------|
| `--check` | Apenas verificar delta (não baixar) |
| `--force` | Forçar re-sincronização completa |
| `--source=XX` | Filtrar por fonte específica (JM, JH, CG, etc.) |
| `--execute` | Executar download após verificação |

---

## CONCEITO FUNDAMENTAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLANILHA (Google Sheets)                                                   │
│       │                                                                     │
│       ▼                                                                     │
│  COMPARAR com SNAPSHOT LOCAL (PLANILHA-INDEX.json)                          │
│       │                                                                     │
│       ├── NOVOS? → Gerar TAG na planilha → Baixar com [TAG]                │
│       │                                                                     │
│       └── IGUAIS? → Nada a fazer                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Diferença crítica vs Fase 2.5:**
- Fase 2.5: Tagueia LOCALMENTE (arquivo já baixado)
- Source Sync: Tagueia NA FONTE (planilha) ANTES de baixar

---

## MAPEAMENTO ABA → PREFIXO

```python
SHEET_TO_PREFIX = {
    "Jeremy Miner": "JM",
    "Jeremy Haynes Sales Training": "JH-ST",
    "Jeremy Haynes Inner Circle": "JH-IC",
    "Inner Circle Weekly Group Call Recordings": "JH-WK",
    "Agency Blueprint": "AOBA",
    "Cold Video Pitch": "PCVP",
    "Land Your First Agency Client": "LYFC",
    "Marketer Mindset Masterclass": "MMM",
    "30 Days Challenge": "30DC",
    "Scale The Agency": "STA",
    "Ultra High Ticket Closer": "UHTC",
    "The Scalable Company": "TSC",
    "Cole Gordon": "CG",
    "Sales Training BR": "EDC",
    "Alex Hormozi": "AH",
    "Jeremy Haynes Program": "CA",
}
```

---

## FLUXO DE TRABALHO

### PASSO 1: CARREGAR SNAPSHOT
```python
# Ler PLANILHA-INDEX.json (último estado conhecido)
snapshot = load_json("/.claude/mission-control/PLANILHA-INDEX.json")
# Contém: {entries: [{tag, name, sheet, row, link_drive}], timestamp}
```

### PASSO 2: LER PLANILHA ATUAL (MCP)
```python
# Via MCP gdrive
planilha_atual = mcp__gdrive__gsheets_read(spreadsheetId=PLANILHA_ID)
# Para cada aba, extrair: nome_video, TAG existente, link_drive
```

### PASSO 3: DETECTAR DELTA
```python
# Comparar snapshot vs atual
novos = [entry for entry in atual if entry['tag'] not in snapshot_tags]
# Separar: com_tag (já tagueados) vs sem_tag (precisam TAG)
```

### PASSO 4: EXIBIR RELATÓRIO
```
╔══════════════════════════════════════════════════════════════════════════════╗
║         SOURCE SYNC - RELATÓRIO DE DELTA                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  NOVOS ARQUIVOS DETECTADOS: 47                                               ║
║                                                                              ║
║  POR FONTE:                                                                  ║
║  ├── Jeremy Miner:       12 novos                                            ║
║  ├── Jeremy Haynes:      23 novos                                            ║
║  └── Cole Gordon:         8 novos                                            ║
║                                                                              ║
║  AÇÕES NECESSÁRIAS:                                                          ║
║  ├── TAGs a gerar:       15 (arquivos sem TAG)                               ║
║  ├── Downloads:          47 arquivos                                         ║
║  └── Destino: inbox/[FONTE]/[TIPO]/                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### PASSO 5: TAGUEAMENTO NA FONTE (com --execute)
```python
# Para cada arquivo SEM TAG na planilha:
for entry in novos_sem_tag:
    prefix = SHEET_TO_PREFIX[entry['sheet']]
    next_tag = generate_next_tag(prefix, existing_tags)
    # Escrever na planilha
    mcp__gdrive__gsheets_update_cell(
        fileId=PLANILHA_ID,
        range=f"{entry['sheet']}!I{entry['row']}",
        value=next_tag
    )
```

### PASSO 6: DOWNLOAD ORGANIZADO
```python
# Baixar com nome já tagueado:
for entry in novos:
    content = mcp__gdrive__gdrive_read_file(fileId=entry['file_id'])
    filename = f"[{entry['tag']}] {entry['original_name']}.txt"
    save_to_inbox(content, filename, source_folder=entry['source'])
```

### PASSO 7: ATUALIZAR SNAPSHOT
```python
# Adicionar novos ao índice
snapshot['entries'].extend(novos)
snapshot['timestamp'] = datetime.now().isoformat()
save_json(snapshot, "/.claude/mission-control/PLANILHA-INDEX.json")
```

---

## ARQUIVOS DO SISTEMA

| Arquivo | Propósito |
|---------|-----------|
| `.claude/mission-control/PLANILHA-INDEX.json` | Snapshot da planilha (915+ entries) |
| `.claude/mission-control/SOURCE-SYNC-STATE.json` | Estado da última sincronização |
| `.claude/mission-control/DELTA-PENDING.json` | Arquivos novos pendentes |
| `.claude/scripts/source-sync.py` | Script de detecção de delta |
| `.claude/hooks/session-source-sync.py` | Hook de início de sessão |

---

## INTEGRAÇÃO COM FASES

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANTES (Manual):                                                            │
│                                                                             │
│  Fase 1 (Download) → Fase 2 (Organização) → Fase 2.5 (Tags) → Fase 3       │
│       ↑                    ↑                      ↑                         │
│     Manual              Manual                 Scripts                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  DEPOIS (Source Sync):                                                      │
│                                                                             │
│  /source-sync ─────────────────────────────────────────────→ Fase 4        │
│       │                                                                     │
│       └── Detecta + Tagueia na fonte + Baixa organizado                    │
│                                                                             │
│  Fases 1, 2, 2.5, 3 SUBSTITUÍDAS por um único comando                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REGRA #25 - SOURCE SYNC OBRIGATÓRIO

**ANTES DE PROCESSAR NOVOS CONTEÚDOS, EXECUTAR /source-sync.**

### Regras Absolutas:

- **NÃO PODE** baixar arquivos manualmente sem usar /source-sync
- **NÃO PODE** ignorar alerta de delta pendente
- **NÃO PODE** processar no Pipeline sem sincronização
- **DEVE** sempre verificar snapshot antes de baixar
- **DEVE** atualizar snapshot após cada sincronização

```
⚠️ SYNC ANTES DE DOWNLOAD
⚠️ TAG NA FONTE, NÃO NO LOCAL
⚠️ SNAPSHOT É A VERDADE
```

---

## ALERTAS DE SESSÃO

O hook verifica no início de cada sessão:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SOURCE SYNC - ALERTAS DE SESSÃO                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  [PENDING_DELTA]                                                             │
│    ⚠️ 47 arquivos NOVOS detectados aguardando download                       │
│    → Execute /source-sync para processar                                     │
│                                                                              │
│  [STALE_SYNC]                                                                │
│    ⚠️ Última sincronização há 8 dias                                         │
│    → Considere executar /source-sync --check                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## COMANDOS RÁPIDOS

```bash
# Verificar delta (sem baixar)
/source-sync --check

# Executar sincronização completa
/source-sync --execute

# Filtrar por fonte específica
/source-sync --source=JM --execute

# Forçar re-sincronização
/source-sync --force --execute
```

---

*Skill criada para MISSION-2026-001 | JARVIS v3.33.0*
