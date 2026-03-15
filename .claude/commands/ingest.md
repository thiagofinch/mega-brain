---
description: Ingere material (YouTube, documentos, arquivos) na INBOX com metadados
allowed-tools: Bash(cd:*), Bash(python:*), Bash(yt-dlp:*)
argument-hint: [URL or path] [--person "Name"] [--type TYPE] [--process]
---

# INGEST - Ingestão de Material

> **Versão:** 2.0.0
> **Workflow:** `core/workflows/wf-ingest.yaml`
> **Pipeline:** Jarvis v2.1 → Etapa de Entrada

---

## SINTAXE

```
/ingest [SOURCE] [FLAGS]
```

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| YouTube URL | Link de vídeo para transcrever | `/ingest https://youtube.com/watch?v=xxx` |
| Local path | Arquivo já existente | `/ingest /path/to/file.txt` |
| Google Drive | Link de documento | `/ingest https://docs.google.com/...` |

---

## FLAGS OPCIONAIS

```
--person "Nome Pessoa"    # Define pessoa manualmente (senão detecta do path)
--type PODCAST           # Define tipo (PODCAST, MASTERCLASS, COURSE, etc.)
--process                # Já inicia processamento após ingestão
```

---

## EXECUÇÃO

### Step 1: Identificar Tipo de Fonte
```
IF $SOURCE starts with "http":
  IF contains "youtube.com" or "youtu.be":
    -> TYPE = "YOUTUBE"
    -> Fetch transcript via youtube-transcript-api
  ELSE IF contains "docs.google.com":
    -> TYPE = "GDOC"
    -> Download content
  ELSE:
    -> TYPE = "WEB"
    -> Fetch page content
ELSE:
  -> TYPE = "LOCAL"
  -> Read file directly
```

### Step 2: Extrair/Detectar Metadados
```
IF --person provided:
  PERSON = $person_flag
ELSE:
  DETECT from URL title or filename

IF --type provided:
  CONTENT_TYPE = $type_flag
ELSE:
  INFER from source (PODCAST, MASTERCLASS, COURSE, VSL, etc.)
```

### Step 3: Determine Bucket and Filename
```
BUCKET DETECTION (use scope_classifier logic):
  IF expert content (course, podcast, masterclass, YouTube expert) → bucket = "external"
  IF company meeting, internal doc → bucket = "business"
  IF personal note, founder reflection → bucket = "personal"

DESTINATION = knowledge/{BUCKET}/inbox/

IF YouTube:
  FILENAME = {VIDEO_TITLE} [youtube.com_watch_v={ID}].txt
ELSE:
  FILENAME = {ORIGINAL_NAME}.txt

DO NOT create entity or content-type subdirectories manually.
The organize_inbox() function handles entity detection + content type classification automatically.
```

### Step 4: Save Content and Auto-Organize
```
CREATE directory if not exists: {DESTINATION}
WRITE content to: {DESTINATION}/{FILENAME}
WORD_COUNT = count words

THEN run auto-organize:
  python3 -c "from core.intelligence.pipeline.inbox_organizer import organize_inbox; r = organize_inbox('{BUCKET}'); print(f'Organized: {r[\"organized\"]} files')"

This auto-detects:
  - ENTITY from filename (e.g., "Alex Hormozi" → alex-hormozi/)
  - CONTENT TYPE from keywords (e.g., "youtube.com" → youtube/, "podcast" → podcasts/)
  - Moves file to: knowledge/{BUCKET}/inbox/{ENTITY}/{CONTENT_TYPE}/{FILENAME}
```

### Step 5: Gerar INGEST REPORT
```
═══════════════════════════════════════════════════════════════════════════════
                              INGEST REPORT
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 MATERIAL INGERIDO
   Fonte: {URL ou PATH original}
   Tipo: {VIDEO | DOCUMENTO | AUDIO}

📁 DESTINO
   Bucket: {BUCKET}
   Drop: knowledge/{BUCKET}/inbox/{FILENAME}
   Organized to: knowledge/{BUCKET}/inbox/{ENTITY}/{CONTENT_TYPE}/{FILENAME}

📊 ESTATÍSTICAS
   Palavras: {WORD_COUNT}
   Duração estimada: {DURATION se disponível}
   Pessoa detectada: {PERSON_NAME}

⭐️ PRÓXIMA ETAPA
   Para processar: /process-jarvis "knowledge/{BUCKET}/inbox/{ENTITY}/{CONTENT_TYPE}/{arquivo}.txt"
   Ou: /inbox para ver todos pendentes

═══════════════════════════════════════════════════════════════════════════════
```

### Step 6: Se --process flag
```
IF --process flag present:
  -> EXECUTE: /process-jarvis "{DESTINATION}/{FILENAME}"
```

---

## LOG

Append to `/logs/AUDIT/audit.jsonl`:
```json
{
  "timestamp": "ISO",
  "operation": "INGEST",
  "source": "$SOURCE",
  "destination": "{DESTINATION}/{FILENAME}",
  "source_id": "{SOURCE_ID}",
  "word_count": {WORD_COUNT},
  "status": "SUCCESS"
}
```

---

## KNOWN SOURCES

| Detecta | PERSON | COMPANY |
|---------|--------|---------|
| "hormozi", "acquisition" | Alex Hormozi | Alex Hormozi |
| "cole gordon", "closers" | Cole Gordon | Cole Gordon |
| "leila" | Leila Hormozi | Alex Hormozi |
| "setterlun", "sam ovens" | Sam Ovens | Setterlun University |
| "jordan lee" | Jordan Lee | AI Business |
| "jeremy haynes" | Jeremy Haynes | - |

---

## CONTENT TYPES

| Tipo | Detecta |
|------|---------|
| PODCASTS | "podcast", "episode", "ep", "interview" |
| MASTERCLASS | "masterclass", "mastermind", "training" |
| COURSES | "course", "module", "lesson", "aula" |
| BLUEPRINTS | "blueprint", "pdf", "playbook", "guide" |
| VSL | "vsl", "webinar", "sales letter" |
| SCRIPTS | "script", "template", "copy" |
| MARKETING | "ad", "marketing", "launch" |

---

## EXEMPLOS

```bash
# YouTube video
/ingest https://youtube.com/watch?v=abc123

# YouTube com pessoa específica
/ingest https://youtube.com/watch?v=abc123 --person "Cole Gordon"

# Arquivo local
/ingest "/path/to/transcription.txt" --type MASTERCLASS

# Ingerir e já processar
/ingest https://youtube.com/watch?v=abc123 --process
```
