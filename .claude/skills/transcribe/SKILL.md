---
name: transcribe
description: "Esta skill deve ser usada para transcrever vídeos e áudios locais com Whisper.cpp"
version: "1.0.0"
context: conversation
agent: general-purpose
user-invocable: true
---

# Transcribe

Transcreve vídeos e áudios locais (Whisper.cpp) ou de URLs YouTube (ETL pipeline).
Detecta automaticamente se o input é arquivo local ou link.

## Quick Start

```
/transcribe https://www.youtube.com/watch?v=VIDEO_ID       # YouTube via ETL (legendas)
/transcribe https://youtu.be/VIDEO_ID --lang en             # YouTube com idioma específico
/transcribe https://www.youtube.com/watch?v=VIDEO_ID --clean # YouTube + limpeza LLM
/transcribe /path/to/video.mp4                              # Local via Whisper.cpp (2x speed)
/transcribe /path/to/video.mp4 --lang pt                    # Local, força português
/transcribe /path/to/video.mp4 --no-speed                   # Local, timestamps exatos
```

## Activation

1. Parse argumentos (input obrigatório, --lang opcional)
2. **Detectar tipo de input:** URL ou arquivo local
3. **Se URL YouTube** → ETL pipeline (`youtube-transcript.js` + opcional `youtube-clean-transcript.js`)
4. **Se arquivo local** → Whisper.cpp pipeline (extrair áudio → transcrever → fix timestamps)
5. Salvar em `outputs/transcriptions/{slug}/`

---

## SKILL DEFINITION

```yaml
skill:
  name: Transcribe
  id: transcribe
  icon: 🎙️

config:
  whisper_cli: "${WHISPER_CPP_CLI:-$HOME/whisper.cpp/build/bin/whisper-cli}"
  whisper_model: "${WHISPER_CPP_MODEL:-$HOME/whisper.cpp/models/ggml-large-v3.bin}"
  output_dir: "outputs/transcriptions"
  etl_dir: "infrastructure/services/etl"

  # Otimizações de áudio (modo local)
  audio:
    sample_rate: 16000
    channels: 1
    codec: "pcm_s16le"
    speed: 2.0

  # Formatos de output
  formats:
    - txt
    - srt
    - json

arguments:
  - name: input
    required: true
    description: "URL YouTube ou caminho do vídeo/áudio local"
  - name: --lang
    required: false
    default: "en"
    options: ["auto", "pt", "en", "es", "fr", "de", "it", "ja", "zh"]
    description: "Idioma (default: en para YouTube, auto para local)"
  - name: --format
    required: false
    default: "all"
    options: ["txt", "srt", "json", "all"]
    description: "Formato de output"
  - name: --clean
    required: false
    default: false
    description: "Limpar transcript com LLM (só para YouTube, usa youtube-clean-transcript.js)"
  - name: --no-speed
    required: false
    default: false
    description: "Desativa aceleração 2x (só para modo local)"

veto_conditions:
  - id: VETO_FILE_NOT_FOUND
    trigger: "Local file does not exist"
    action: "STOP + Error: 'Arquivo não encontrado: {input}'"

  - id: VETO_INVALID_FORMAT
    trigger: "Local file is not video or audio"
    action: "STOP + Error: 'Formato não suportado. Use: mp4, mov, mkv, avi, mp3, wav, m4a'"

  - id: VETO_WHISPER_NOT_INSTALLED
    trigger: "Whisper CLI not found (modo local)"
    action: "STOP + Error: 'Whisper.cpp não instalado. Execute: cd ~/whisper.cpp && make'"

  - id: VETO_INVALID_URL
    trigger: "URL is not a valid YouTube link"
    action: "STOP + Error: 'URL não reconhecida. Suportado: youtube.com/watch?v=, youtu.be/'"

constraints:
  supported_urls:
    - "youtube.com/watch?v="
    - "youtu.be/"
    - "youtube.com/shorts/"
  supported_formats:
    video: ["mp4", "mov", "mkv", "avi", "webm", "m4v"]
    audio: ["mp3", "wav", "m4a", "flac", "ogg", "aac"]
  max_duration: 14400

workflow:
  phases:
    0_route:
      name: "Detectar e Rotear"
      execution: |
        1. Analisar input:
           - Se contém "youtube.com/watch?v=", "youtu.be/", ou "youtube.com/shorts/"
             → MODE = "youtube"
           - Se é caminho de arquivo (começa com / ou ~/ ou ./)
             → MODE = "local"
           - Senão → VETO_INVALID_URL ou VETO_FILE_NOT_FOUND

        2. Se MODE = "youtube":
           - Extrair video ID do URL (11 chars após v= ou após youtu.be/)
           - Obter título do vídeo via yt-dlp:
             ```bash
             yt-dlp --print title "URL" 2>/dev/null
             ```
           - Gerar slug a partir do TÍTULO (não do ID):
             lowercase, remover caracteres especiais, kebab-case
             Ex: "OpenClaw: The Viral AI Agent... - Peter Steinberger | Lex Fridman Podcast #491"
             → "openclaw-peter-steinberger-lex-fridman-491"
           - Ir para fase 1_youtube

        3. Se MODE = "local":
           - Ir para fase 1_local_validate
      output: "MODE (youtube|local), video_id ou file_path, slug"

    1_youtube:
      name: "YouTube ETL Pipeline"
      description: |
        Usa infraestrutura ETL existente. Zero download de vídeo.
        Extrai legendas direto da API do YouTube (rápido, gratuito).
        Output é markdown formatado com speakers identificados.
      execution: |
        1. Extrair transcript JSON via ETL (contém segments com offsets):
           ```bash
           node infrastructure/services/etl/bin/youtube-transcript.js {video_id} \
             --lang {lang} \
             --format json \
             --output /tmp/transcribe-yt
           ```

        2. Processar JSON em markdown formatado com speakers:
           - Ler segments do JSON
           - Decode HTML entities (double unescape)
           - Detectar trocas de speaker via marcador "- " no início dos segments
           - Para podcasts/entrevistas: identificar host vs guest pelo contexto
           - Heurísticas de atribuição:
             * Perguntas (terminam em ?) → geralmente o host
             * Explicações técnicas longas → geralmente o guest
             * "So,...", "I mean,...", "What about..." → geralmente host
             * Alternância padrão entre speakers
           - Merge turns consecutivos do mesmo speaker
           - Adicionar timestamps a cada ~10 minutos como section headers

        3. Gerar markdown com estrutura:
           ```markdown
           # {Título do Vídeo}

           > **Source:** [URL](URL)
           > **Duration:** H:MM:SS (X min)
           > **Speakers:** Speaker A (host), Speaker B (guest)
           > **Segments:** N
           > **Extracted:** YYYY-MM-DD

           ---

           ## Highlights
           (clips do início, antes da intro)

           ## Introduction
           (narração do host)

           ## Conversation

           ### [MM:SS]
           **Speaker A:** texto...
           **Speaker B:** texto...
           ```

        4. Se --clean flag ativo, limpar transcript com LLM:
           ```bash
           node infrastructure/services/etl/bin/youtube-clean-transcript.js \
             --file {slug}.txt \
             > {slug}-clean.txt
           ```

        5. Salvar em outputs/transcriptions/{slug}/:
           - {slug}.md (markdown formatado com speakers)
           - {slug}.json (raw segments para processamento futuro)
      output: "outputs/transcriptions/{slug}/ com .md e .json"

    1_local_validate:
      name: "Validação (Modo Local)"
      execution: |
        1. Verificar se arquivo existe:
           ```bash
           test -f "{input}" && echo "OK" || echo "NOT_FOUND"
           ```

        2. Verificar formato suportado:
           - Extrair extensão do arquivo
           - Validar contra lista de formatos suportados

        3. Verificar Whisper instalado:
           ```bash
           test -f "${WHISPER_CPP_CLI:-$HOME/whisper.cpp/build/bin/whisper-cli}" && echo "OK"
           ```

        4. Obter metadata do arquivo:
           ```bash
           ffprobe -v quiet -show_format -show_streams "{input}" 2>&1 | grep -E "duration|codec_name|sample_rate"
           ```
      output: "file_info (duration, has_audio, format)"

    2_local_extract_audio:
      name: "Extração de Áudio Otimizado (Modo Local)"
      description: |
        Converte para WAV 16kHz mono - formato ideal para Whisper.
        Mono economiza 50% de processamento vs stereo sem perda de qualidade na transcrição.
      execution: |
        1. Criar diretório temporário:
           ```bash
           mkdir -p /tmp/transcribe
           ```

        2. Gerar slug do arquivo:
           - basename sem extensão
           - lowercase, replace spaces com hyphens

        3. Determinar speed factor:
           - Se --no-speed: speed = 1.0
           - Senão: speed = 2.0

        4. Extrair áudio otimizado:
           ```bash
           # Com speed=2.0 (default):
           ffmpeg -y -i "{input}" \
             -ar 16000 \
             -ac 1 \
             -af "atempo=2.0" \
             -c:a pcm_s16le \
             /tmp/transcribe/{slug}.wav 2>&1 | tail -3

           # Com --no-speed (speed=1.0):
           ffmpeg -y -i "{input}" \
             -ar 16000 \
             -ac 1 \
             -c:a pcm_s16le \
             /tmp/transcribe/{slug}.wav 2>&1 | tail -3
           ```

        5. Verificar extração:
           ```bash
           test -f /tmp/transcribe/{slug}.wav && echo "OK"
           ```
      output: "audio_path, speed_factor"

    3_local_transcribe:
      name: "Transcrição com Whisper (Modo Local)"
      execution: |
        1. Determinar idioma:
           - Se --lang especificado: usar diretamente
           - Se "auto": deixar Whisper detectar (não passar -l)

        2. Executar transcrição:
           ```bash
           "${WHISPER_CPP_CLI:-$HOME/whisper.cpp/build/bin/whisper-cli}" \
             -m "${WHISPER_CPP_MODEL:-$HOME/whisper.cpp/models/ggml-large-v3.bin}" \
             -f /tmp/transcribe/{slug}.wav \
             {-l {lang} se não auto} \
             -pp \
             -otxt -osrt -oj \
             -of /tmp/transcribe/{slug}
           ```

        3. Capturar timing do Whisper para relatório
      output: "transcription files in /tmp/transcribe/"

    3_5_local_fix_timestamps:
      name: "Corrigir Timestamps (Modo Local, se speed != 1.0)"
      description: |
        O Whisper gera timestamps baseados no áudio acelerado.
        Precisamos multiplicar pelo speed factor para alinhar com o vídeo original.
      execution: |
        1. Se speed_factor == 1.0: SKIP esta fase

        2. Corrigir SRT (multiplicar timestamps por speed_factor):
           ```bash
           python3 -c "
           import re
           import sys

           speed = float(sys.argv[1])
           with open(sys.argv[2], 'r') as f:
               content = f.read()

           def fix_time(match):
               h, m, s, ms = int(match[1]), int(match[2]), int(match[3]), int(match[4])
               total_ms = (h * 3600 + m * 60 + s) * 1000 + ms
               total_ms = int(total_ms * speed)
               h = total_ms // 3600000
               m = (total_ms % 3600000) // 60000
               s = (total_ms % 60000) // 1000
               ms = total_ms % 1000
               return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

           fixed = re.sub(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', fix_time, content)
           with open(sys.argv[2], 'w') as f:
               f.write(fixed)
           " {speed_factor} /tmp/transcribe/{slug}.srt
           ```

        3. Corrigir JSON (multiplicar start/end por speed_factor):
           ```bash
           python3 -c "
           import json
           import sys

           speed = float(sys.argv[1])
           with open(sys.argv[2], 'r') as f:
               data = json.load(f)

           if 'transcription' in data:
               for segment in data['transcription']:
                   if 'timestamps' in segment:
                       ts = segment['timestamps']
                       ts['from'] = str(float(ts['from'].replace('s','')) * speed) + 's'
                       ts['to'] = str(float(ts['to'].replace('s','')) * speed) + 's'
                   if 'offsets' in segment:
                       off = segment['offsets']
                       off['from'] = int(off['from'] * speed)
                       off['to'] = int(off['to'] * speed)

           with open(sys.argv[2], 'w') as f:
               json.dump(data, f, indent=2, ensure_ascii=False)
           " {speed_factor} /tmp/transcribe/{slug}.json
           ```

        4. TXT não precisa ajuste (sem timestamps)
      output: "timestamps corrigidos"

    4_organize_output:
      name: "Organizar Output"
      execution: |
        1. Criar diretório de output:
           ```bash
           mkdir -p outputs/transcriptions/{slug}
           ```

        2. Se MODE = "local", mover arquivos do /tmp:
           ```bash
           mv /tmp/transcribe/{slug}.txt outputs/transcriptions/{slug}/
           mv /tmp/transcribe/{slug}.srt outputs/transcriptions/{slug}/
           mv /tmp/transcribe/{slug}.json outputs/transcriptions/{slug}/
           ```

        3. Se MODE = "youtube", arquivos já estão no diretório correto

        4. Criar README com metadata:
           - Source (URL ou file path)
           - Mode (youtube-etl ou whisper-local)
           - Duration
           - Language
           - Transcription time
           - Word count

        5. Limpar temporários (modo local):
           ```bash
           rm -f /tmp/transcribe/{slug}.wav
           ```
      output: "outputs/transcriptions/{slug}/"

    5_report:
      name: "Relatório Final"
      execution: |
        Mostrar ao usuário:
        - Source (URL ou arquivo)
        - Modo utilizado (YouTube ETL / Whisper Local)
        - Duração do vídeo
        - Tempo de processamento
        - Idioma
        - Arquivos gerados com paths
        - Preview das primeiras linhas do .txt

output_structure:
  folder_pattern: "outputs/transcriptions/{slug}"
  slug_source:
    youtube: "Título do vídeo (kebab-case, sem caracteres especiais)"
    local: "Nome do arquivo (basename sem extensão, kebab-case)"
  files:
    youtube_mode:
      - name: "{slug}.md"
        content: "Markdown formatado com speakers, timestamps, highlights, intro e conversation"
      - name: "{slug}.json"
        content: "JSON raw com segments e metadata (para reprocessamento)"
      - name: "{slug}-clean.txt"
        content: "Texto limpo por LLM (opcional, só com --clean)"
    local_mode:
      - name: "{slug}.txt"
        content: "Transcrição em texto puro"
      - name: "{slug}.srt"
        content: "Legendas com timestamps"
      - name: "{slug}.json"
        content: "JSON estruturado com segments e metadata"
      - name: "README.md"
        content: "Metadata da transcrição"

examples:
  - command: "/transcribe https://www.youtube.com/watch?v=YFjfBk8HI5o"
    description: "YouTube: extrai legendas via ETL (rápido, sem download)"

  - command: "/transcribe https://youtu.be/YFjfBk8HI5o --lang en"
    description: "YouTube: legendas em inglês"

  - command: "/transcribe https://www.youtube.com/watch?v=YFjfBk8HI5o --clean"
    description: "YouTube: extrai + limpa com LLM (pontuação, parágrafos)"

  - command: "/transcribe ~/Movies/Ads2.mov"
    description: "Local: Whisper.cpp com 2x speed (default)"

  - command: "/transcribe ~/Movies/Ads2.mov --lang pt"
    description: "Local: força transcrição em português"

  - command: "/transcribe video.mp4 --no-speed"
    description: "Local: sem aceleração (timestamps exatos)"

  - command: "/transcribe video.mp4 --lang pt --no-speed --format srt"
    description: "Local: legendas em português com timestamps exatos"
```

---

## Execution Flow

```
Input (URL ou File)
       │
       ▼
┌────────────────┐
│  0. Route      │ → YouTube URL? → ETL Pipeline
│                │ → Local file?  → Whisper Pipeline
└──────┬─────────┘
       │
       ├── YouTube ─────────────────────┐
       │                                ▼
       │                   ┌─────────────────────┐
       │                   │ 1. youtube-transcript│ → ETL: legendas via API
       │                   └──────┬──────────────┘
       │                          │
       │                          ▼ (se --clean)
       │                   ┌─────────────────────────┐
       │                   │ 1b. clean-transcript    │ → LLM: pontuação + parágrafos
       │                   └──────┬──────────────────┘
       │                          │
       ├── Local ───────────┐     │
       │                    ▼     │
       │        ┌──────────────┐  │
       │        │ 1. Validate  │  │
       │        └──────┬───────┘  │
       │               ▼          │
       │        ┌──────────────┐  │
       │        │ 2. Extract   │  │
       │        └──────┬───────┘  │
       │               ▼          │
       │        ┌──────────────┐  │
       │        │ 3. Whisper   │  │
       │        └──────┬───────┘  │
       │               ▼          │
       │        ┌──────────────┐  │
       │        │3.5 Fix Times │  │
       │        └──────┬───────┘  │
       │               │          │
       │               ▼          ▼
       │        ┌──────────────────┐
       └───────►│  4. Organize     │ → outputs/transcriptions/{slug}/
                └──────┬───────────┘
                       ▼
                ┌──────────────────┐
                │  5. Report       │ → Summary + Preview
                └──────────────────┘
```

## Performance Reference (M3 Ultra)

### Com 2x Speed (Default)

Pesquisa demonstrou que 2x **mantém ou melhora** qualidade (WER 5.1-5.8% vs 5-6% em 1x).

| Duração | Tempo estimado | Velocidade | Melhoria |
|---------|----------------|------------|----------|
| 1 min   | ~2s            | ~30-40x    | 50%      |
| 5 min   | ~8-10s         | ~30-40x    | 50%      |
| 30 min  | ~1 min         | ~30x       | 50%      |
| 1 hora  | ~2-2.5 min     | ~25-30x    | 50%      |
| 4 horas | ~10-12 min     | ~20-25x    | 50%      |

### Com --no-speed (1x, timestamps exatos)

Use apenas quando precisar de timestamps 100% exatos para legendas críticas.

| Duração | Tempo estimado | Velocidade |
|---------|----------------|------------|
| 1 min   | ~3-4s          | ~15-20x    |
| 5 min   | ~15-20s        | ~15-20x    |
| 30 min  | ~2 min         | ~15x       |
| 1 hora  | ~4-5 min       | ~12-15x    |
| 4 horas | ~20-25 min     | ~10-12x    |
