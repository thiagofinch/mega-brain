# Process Video Command

Process a video (YouTube or local) and extract knowledge automatically.

## Input
$ARGUMENTS (YouTube URL or local file path)

## PRIMEIRA AÇÃO OBRIGATÓRIA

> **ANTES de processar, LEIA `/system/SESSION-STATE.md`**
> Verificar se este vídeo já foi processado.

---

## Workflow

### Step 1: Detect Source Type
- Se URL contém "youtube.com" ou "youtu.be" → YouTube processing
- Se path termina em .mp4, .mp3, .wav, .m4a → Local file processing

### Step 2: Identify Source (OBRIGATÓRIO)

Identificar a fonte para organização correta:

| Identificador | Pessoa | Empresa | Padrão de Pasta |
|---------------|--------|---------|-----------------|
| HORMOZI | Alex Hormozi | Alex Hormozi | `ALEX HORMOZI/` |
| COLE-GORDON | Cole Gordon | Cole Gordon | `COLE GORDON/` |
| LEILA | Leila Hormozi | Alex Hormozi | `LEILA HORMOZI/` |
| CARDONE | Grant Cardone | Cardone Enterprises | `GRANT CARDONE (CARDONE ENTERPRISES)/` |

### Step 3: Identify Content Type

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| PODCASTS | Episódios, entrevistas | "The Game Podcast", "Role of HR" |
| MASTERMINDS | Eventos, palestras ao vivo | "Taki Moore Mastermind" |
| BLUEPRINTS | PDFs, playbooks, documentos | "Money Models" |
| COURSES | Módulos de cursos | "Sales Training Module 1" |
| VSL | Video Sales Letters | "VSL High Ticket" |
| SCRIPTS | Scripts de vendas | "Call Script v2" |

### Step 4: Extract Transcript

**For YouTube:**
```python
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Extract video ID
video_id = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url).group(1)

# Fetch transcript
api = YouTubeTranscriptApi()
transcript = api.fetch(video_id)
text = " ".join([entry['text'] for entry in transcript])
```

**For Local Files:**
```bash
whisper "arquivo.mp4" --language English --output_format txt --output_dir "pasta/"
```

### Step 5: Save Transcript

**Localização:**
```
inbox/PESSOA (EMPRESA)/TIPO/TITULO DO VIDEO [youtube.com_watch_v=ID].txt
```

**Exemplo:**
```
inbox/alex hormozi/PODCASTS/HOW I SCALED MY SALES TEAM [youtube.com_watch_v=abc123].txt
```

**Regras:**
- Pasta em CAIXA ALTA
- Nome do arquivo em CAIXA ALTA
- Incluir link do YouTube no nome `[youtube.com_watch_v=ID]`
- Manter .mp4 e .txt juntos na mesma pasta

### Step 6: Extract Knowledge

Após salvar transcrição, automaticamente executar:
1. `/extract-knowledge [path-da-transcrição]`

---

## Output

| Item | Descrição |
|------|-----------|
| Transcript path | Caminho completo do arquivo .txt |
| Source identified | Fonte identificada (HORMOZI, COLE-GORDON, etc.) |
| Content type | Tipo de conteúdo (PODCASTS, MASTERMINDS, etc.) |
| Knowledge extracted | Resumo do que foi extraído |
| Files created/updated | Lista de arquivos em `/knowledge/SOURCES/[FONTE]/` |

---

## Example Usage

```
/process-video https://www.youtube.com/watch?v=okA9Yt2KZuk

/process-video inbox/alex hormozi/PODCASTS/video.mp4
```

---

## Error Handling

| Erro | Ação |
|------|------|
| No transcript on YouTube | Baixar vídeo e transcrever localmente com Whisper |
| Whisper não instalado | `pip install openai-whisper` |
| Fonte não identificada | Perguntar ao usuário ou criar nova pasta |
| Invalid URL/path | Mostrar mensagem de erro clara |

---

## Integration Checklist

Após processar, verificar:

| ✅ | Sistema | Arquivo |
|----|---------|---------|
| [ ] | Glossário | `/system/GLOSSARY/*.md` |
| [ ] | Role-Tracking | `/agents/DISCOVERY/role-tracking.md` |
| [ ] | Registry | `/system/REGISTRY/processed-files.md` |
| [ ] | Session State | `/system/SESSION-STATE.md` |
