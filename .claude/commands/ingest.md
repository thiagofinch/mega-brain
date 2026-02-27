---
description: Ingere material (YouTube, documentos, arquivos) na INBOX com metadados
allowed-tools: Bash(cd:*), Bash(python:*), Bash(yt-dlp:*)
argument-hint: [URL or path] [--person "Name"] [--type TYPE] [--process]
---

# INGEST - Ingestão de Material

> **Versão:** 1.0.0
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

### Step 3: Determinar Destino
```
DESTINATION = inbox/{PERSON} ({COMPANY})/{CONTENT_TYPE}/

IF YouTube:
  FILENAME = {VIDEO_TITLE} [youtube.com_watch_v={ID}].txt
ELSE:
  FILENAME = {ORIGINAL_NAME}.txt

SOURCE_ID = Generate hash (ex: CG005, JL010)
```

### Step 4: Salvar Conteúdo
```
CREATE directory if not exists: {DESTINATION}
WRITE content to: {DESTINATION}/{FILENAME}
WORD_COUNT = count words
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
   Path: inbox/{PESSOA}/{TIPO}/{arquivo}.txt
   Source ID: {SOURCE_ID}

📊 ESTATÍSTICAS
   Palavras: {WORD_COUNT}
   Duração estimada: {DURATION se disponível}
   Pessoa detectada: {PERSON_NAME}

⭐️ PRÓXIMA ETAPA
   Para processar: /process-jarvis "inbox/{PESSOA}/{TIPO}/{arquivo}.txt"
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
