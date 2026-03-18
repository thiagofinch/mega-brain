---
description: Ingere material pessoal do founder e roteia para knowledge/personal/inbox/
allowed-tools: Bash(cd:*), Bash(python:*), Read, Write, Edit, Glob, Grep
argument-hint: [path or URL] [--type TYPE]
---

# INGEST-PESSOAL - Ingestão de Material Pessoal (Bucket 3)

> **Versão:** 1.0.0
> **Pipeline:** Jarvis v2.1 → Routing para `knowledge/personal/inbox/` → `bucket_processor.py personal`
> **Bucket:** 3 (Cognitive Layer) — 🟢
> **Layer:** L3 EXCLUSIVO — NUNCA exposto em L1/L2

---

## PROPÓSITO

Processa material **pessoal do founder** (emails, mensagens, calls, reflexões, journaling) e roteia para `knowledge/personal/inbox/`. O `bucket_processor.py` classifica e distribui para os subdirs corretos (`_email/`, `_messages/`, `_calls/`, `_cognitive/`).

**Diferença dos outros comandos:**
- `/ingest` → `knowledge/external/inbox/` (expert minds) — 🔵
- `/ingest-empresa` → `workspace/inbox/` (dados do negócio) — 🔴
- `/ingest-pessoal` → `knowledge/personal/inbox/` (dados cognitivos) — 🟢

---

## SINTAXE

```
/ingest-pessoal [SOURCE] [FLAGS]
```

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| Local path | Arquivo ou pasta | `/ingest-pessoal ./notas-reuniao.md` |
| Texto direto | Reflexão inline | `/ingest-pessoal "Hoje percebi que..."` |
| Call recording | Transcrição de call | `/ingest-pessoal ./call-2026-03-07.txt` |

---

## FLAGS OPCIONAIS

```
--type EMAIL|MESSAGES|CALLS|COGNITIVE    # Força subdir de destino
--batch                                   # Processa todos os arquivos de uma pasta
--process                                 # Após salvar, executa bucket_processor.py
```

---

## ROUTING RULES

| Tipo de Conteúdo | Detecta | Destino Inbox | Destino Final |
|------------------|---------|---------------|---------------|
| Email | "email", "e-mail", "inbox", "newsletter", "digest" | `personal/inbox/email/` | `personal/_email/` |
| Mensagens | "whatsapp", "telegram", "mensagem", "chat", "DM" | `personal/inbox/messages/` | `personal/_messages/` |
| Calls | "ligação", "call", "telefonema", "gravação", "transcrição" | `personal/inbox/calls/` | `personal/_calls/` |
| Cognitivo | "reflexão", "journal", "diário", "insight", "aprendizado", "saúde" | `personal/inbox/cognitive/` | `personal/_cognitive/` |

---

## EXECUÇÃO

### Step 1: Identificar Fonte

```
IF $SOURCE is path:
  READ file content
ELSE IF $SOURCE is text:
  USE as inline content
  GENERATE filename: YYYY-MM-DD-{first_words}.md
```

### Step 2: Classificar Tipo

```
IF --type provided:
  SUBDIR = $type_flag (lowercase)
ELSE:
  ANALYZE content keywords → match routing table above
  DEFAULT: cognitive (quando ambíguo)
```

### Step 3: Salvar no Inbox

```
DESTINATION = knowledge/personal/inbox/{SUBDIR}/{FILENAME}
CREATE directory if not exists
WRITE content to DESTINATION
```

### Step 4: Processar (se --process)

```
IF --process flag:
  python3 core/intelligence/pipeline/bucket_processor.py personal
```

### Step 5: Report

```
════════════════════════════════════════════════════════════════════════════════
                    🟢 INGEST-PESSOAL REPORT
                    {TIMESTAMP}
════════════════════════════════════════════════════════════════════════════════

  ⚠️  DOCUMENTO L3 — CONFIDENCIAL

  MATERIAL PROCESSADO
   Fonte: {SOURCE}
   Tipo detectado: {TYPE}

  DESTINO
   Inbox: knowledge/personal/inbox/{SUBDIR}/{FILENAME}
   Final: knowledge/personal/_{SUBDIR}/{FILENAME} (após bucket_processor)

  SEGURANÇA
   Layer: L3 (gitignored, failsafe .gitignore ativo)
   Exposição: ZERO — nunca aparece em commits

  PRÓXIMA ETAPA
   - Processar inbox: python3 core/intelligence/pipeline/bucket_processor.py personal
   - Ver status: python3 core/intelligence/pipeline/bucket_processor.py

════════════════════════════════════════════════════════════════════════════════
```

---

## SEGURANÇA

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⚠️  REGRAS DE SEGURANÇA L3 — INVIOLÁVEIS                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. NUNCA expor conteúdo pessoal em L1 ou L2                                │
│  2. NUNCA commitar arquivos de knowledge/personal/                          │
│  3. Failsafe: knowledge/personal/.gitignore bloqueia TUDO                   │
│  4. RAG personal é isolado (NÃO mistura com rag_expert/rag_business)        │
│  5. Logs de processamento vão para logs/ (gitignored também)                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## EXEMPLOS

```bash
# Reflexão pessoal
/ingest-pessoal "Hoje na call com investidor percebi que preciso focar mais em unit economics"

# Transcrição de call pessoal
/ingest-pessoal ./call-mentor-2026-03-07.txt --type calls

# Email importante
/ingest-pessoal ./email-parceiro.md --type email

# Batch: processar pasta de notas
/ingest-pessoal ./notas-semana/ --batch

# Ingerir e já processar
/ingest-pessoal ./journal-marco.md --process
```
