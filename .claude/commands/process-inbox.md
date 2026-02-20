---
description: Processa multiplos arquivos do INBOX em lote via Pipeline Jarvis
argument-hint: [--next] [--all] [--person "Name"] [--auto-enrich]
---

# PROCESS-INBOX - Processar INBOX em Lote

> **Versão:** 1.0.0

---

## SINTAXE

```
/process-inbox [FLAGS]
```

| Flag | Descrição |
|------|-----------|
| `--next` | Processa próximo arquivo da fila (mais antigo) |
| `--all` | Processa todos pendentes (com confirmação) |
| `--person "Nome"` | Processa todos de uma pessoa |
| `--auto-enrich` | Sem checkpoints humanos |
| `--dry-run` | Mostra o que faria sem executar |

---

## EXECUÇÃO

### Step 1: Identificar Arquivos
```
RUN /inbox logic to get PENDING files

IF --person:
  FILTER by person name
IF --next:
  SELECT oldest file only
IF --all:
  SELECT all pending files
```

### Step 2: Confirmação (se --all)
```
IF --all AND NOT --auto-enrich:
  SHOW:

═══════════════════════════════════════════════════════════════════════════════
                         CONFIRMAÇÃO - PROCESSAMENTO EM LOTE
═══════════════════════════════════════════════════════════════════════════════

Arquivos a processar: {COUNT}

   1. {PERSON}/{TYPE}/{filename}.txt (~{WORDS} palavras)
   2. {PERSON}/{TYPE}/{filename}.txt (~{WORDS} palavras)
   ...

Tempo estimado: {ESTIMATE} (baseado em ~1 min por 1000 palavras)

⚠️  Modo: {"COM checkpoint humano" | "AUTOMÁTICO (--auto-enrich)"}

Continuar? [S/n]: _
═══════════════════════════════════════════════════════════════════════════════
```

### Step 3: Processar Cada Arquivo
```
FOR each FILE in selected_files:

  LOG: "━━━ Processando {N}/{TOTAL}: {filename} ━━━"

  EXECUTE: /process-jarvis "{FILE_PATH}" {flags}

  IF NOT --auto-enrich AND checkpoint reached:
    -> WAIT for human decision
    -> IF /continue: proceed
    -> IF /abort: stop batch

  LOG: "✅ Completo: {filename}"
```

### Step 4: Relatório Final
```
═══════════════════════════════════════════════════════════════════════════════
                    PROCESSAMENTO EM LOTE - COMPLETO
═══════════════════════════════════════════════════════════════════════════════

📊 RESULTADOS:

   Total processados: {SUCCESS}/{TOTAL}
   Tempo total: {DURATION}

┌─────────────────────────────────────────────────────────────────────────────┐
│ ARQUIVO                          │ CHUNKS │ INSIGHTS │ STATUS              │
├─────────────────────────────────────────────────────────────────────────────┤
│ {filename_1}                     │ {N}    │ {N}      │ ✅ SUCCESS          │
│ {filename_2}                     │ {N}    │ {N}      │ ✅ SUCCESS          │
│ {filename_3}                     │ -      │ -        │ ⏭️ SKIPPED          │
└─────────────────────────────────────────────────────────────────────────────┘

🧠 AGENTES ATUALIZADOS:
   • CLOSER: +{N} insights
   • CRO: +{N} insights
   • SALES-MANAGER: +{N} insights

📁 DOSSIERS ATUALIZADOS:
   • DOSSIER-{PERSON_1}.md
   • DOSSIER-{PERSON_2}.md

⭐️ PRÓXIMOS PASSOS
   Ver estado: /system-digest
   Ver inbox: /inbox

═══════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Processar próximo da fila
/process-inbox --next

# Processar todos de uma pessoa
/process-inbox --person "Cole Gordon"

# Processar tudo automaticamente
/process-inbox --all --auto-enrich

# Ver o que seria processado
/process-inbox --all --dry-run
```

---

## COMPORTAMENTO DE ERRO

```
IF file processing fails:
  LOG error
  ASK: "Continuar com próximo arquivo? [S/n]"
  IF yes: continue
  IF no: abort batch

ALWAYS:
  Save partial results
  Generate partial report
```
