---
description: Ingere e processa um video (YouTube ou arquivo local) com deteccao automatica de fonte, transcript e pipeline completo opcionalanl
allowed-tools: Bash(python3:*), Bash(yt-dlp:*), Bash(whisper:*)
argument-hint: <YouTube-URL|caminho-local> [--skip-gemini] [--process] [--dry-run]
---

# /process-video — Mordomo Video Processor (v1.0.0)

> **Versao:** 1.0.0 [Story MCE-10.0 — Mordomo restoration]
> **Pipeline:** Mega Brain MCE — Variante de ingest para video/audio
> **Motor:** `scripts/ingest-with-entity-discovery.py` (mesma base do /ingest)
> **Arquivo anterior:** `.claude/commands/_archive/process-video-vpre-mordomo.md`

---

## Identidade deste slash

Este slash e **DESCRITIVO** — instrui Claude a executar N bashes separados com narrativa JARVIS entre eles.
Variante do `/ingest` especializada em video/audio. Detecta automaticamente se e URL YouTube ou arquivo local.

Flags suportadas:

| Flag | Efeito |
|------|--------|
| (sem flag) | Extracao de transcript apenas (Fase A) |
| `--skip-gemini` | Pula Speaker Visual Gate, usa yt-dlp + filename |
| `--process` | Executa pipeline completo apos transcript (Fase B) |
| `--dry-run` | Preview sem escrever nada em disco |

---

## Tom JARVIS — Mordomo

Claude narra em PT-BR, tom mordomo elegante, conciso, sem floreio.

Exemplos corretos:
- `"Senhor. Vou extrair o transcript do video agora."`
- `"Fonte identificada: YouTube. Iniciando extracao via Gemini native."`
- `"Transcript extraido. 8.700 palavras. Speaker: Alex Hormozi. Roteando para knowledge/external/..."`
- `"Extracao concluida. Processamento completo disponivel com a flag --process, Senhor."`

**PROIBIDO reproduzir como narrativa:** linhas tecnicas cruas como `[pre_07] BYPASSED`, `Calling Gemini...`, `entity_author:`, etc.

---

## FASE A — Deteccao e Extracao

JARVIS anuncia: `"Senhor. Identificando tipo de fonte e iniciando extracao."`

### PV1 — Detectar tipo de fonte

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
ARG=$(echo "$ARGUMENTS" | awk '{print $1}')
if echo "$ARG" | grep -qE 'youtube\.com|youtu\.be'; then
  echo "SOURCE_TYPE: YOUTUBE"
  VIDEO_ID=$(echo "$ARG" | grep -oE '[a-zA-Z0-9_-]{11}' | tail -1)
  echo "VIDEO_ID: $VIDEO_ID"
elif echo "$ARG" | grep -qE '\.(mp4|mp3|wav|m4a|mkv)$'; then
  echo "SOURCE_TYPE: LOCAL_MEDIA"
  echo "FILE: $ARG"
else
  echo "SOURCE_TYPE: UNKNOWN"
fi
```

Timeout sugerido: 5s.
Narre: tipo detectado (YouTube ou arquivo local).

Se `SOURCE_TYPE: UNKNOWN`: narrar `"Fonte nao reconhecida, Senhor. Fornecer URL YouTube ou path de arquivo .mp4/.mp3/.wav."` e PARAR.

### PV2 — Extrair transcript

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -u scripts/ingest-with-entity-discovery.py $ARGUMENTS
```

Timeout sugerido: 120s (YouTube pode demorar; processamento local mais rapido).

Apos PV2, ler stdout e extrair:
- Palavras extraidas
- Author/subject identificados (entity_author, entity_subject)
- Destino roteado (Path: no INGEST REPORT)
- Slug
- Source utilizado (gemini-native | youtube-captions | whisper)

Se exit code != 0: narrar o erro, mostrar ultimas 20 linhas do stdout, PARAR.

> Se `--process` NAO foi passado: ir direto para VIDEO REPORT ASCII e encerrar com pergunta JARVIS.

---

## FASE B — Pipeline de Processamento (apenas se --process presente)

JARVIS anuncia: `"Transcript disponivel. Iniciando pipeline completo de processamento."`

Cada bash abaixo e uma chamada INDEPENDENTE — nao encadear com `&&`.
Se qualquer bash retornar exit code != 0: narrar o erro + output, PARAR.

Confirmar que voce tem o `<slug>` extraido do output de PV2 antes de continuar.

### PV-B1 — Registrar source no pipeline state

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate ingest "<SLUG_AQUI>"
```

Timeout sugerido: 15s.
Narre: confirmacao de registro + estado (CLASSIFIED, SKIP se idempotente).

Se output indicar que a fonte ja foi processada:
Narrar: `"Esta fonte ja foi processada anteriormente, Senhor. Nenhuma acao necessaria."`
PARAR. Ir para VIDEO REPORT ASCII.

### PV-B2 — Criar batch

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate batch "<SLUG_AQUI>"
```

Timeout sugerido: 15s.
Narre: batch_id criado + numero de arquivos.

### PV-B3 — Chunking + embeddings + RAG

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate process-batch "<SLUG_AQUI>" "<BATCH_ID_AQUI>"
```

Timeout sugerido: 120s.
Narre: chunks criados + status embeddings.

### PV-B4 — Extracao de insights L1-L5

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate insights "<SLUG_AQUI>"
```

Timeout sugerido: 120s.
Narre: total de insights + breakdown por prioridade.

### PV-B5 — Extracao L6/L7/L8/L9/L10 (behavioral, identity, voice)

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate behavioral "<SLUG_AQUI>"
```

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate identity "<SLUG_AQUI>"
```

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate voice "<SLUG_AQUI>"
```

Timeout sugerido: 90s cada.
Narre: resultado de cada camada.

### PV-B6 — Consolidar e finalizar

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate consolidate "<SLUG_AQUI>"
```

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate finalize "<SLUG_AQUI>"
```

Timeout sugerido: 30s cada.
Narre: confirmacao de consolidacao + estado final do pipeline.

---

## VIDEO REPORT ASCII — sempre renderizar ao final

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           VIDEO REPORT                                        ║
║                          <ISO timestamp>                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─ 🎬  VIDEO PROCESSADO ──────────────────────────────────────────────────────┐
│                                                                              │
│   🔗 Fonte:       <URL ou path original>                                     │
│   🎬 Titulo:      <titulo extraido ou nome do arquivo>                       │
│   👤 Speaker:     <person/author identificado>                               │
│   📺 Tipo:        YOUTUBE | LOCAL_MP4 | LOCAL_AUDIO                          │
│   ⏱️  Duracao:    <mm:ss se disponivel>                                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📁  DESTINO ────────────────────────────────────────────────────────────────┐
│                                                                              │
│   📂 Bucket:      <external | business | personal>                           │
│   📍 Path:        knowledge/<bucket>/inbox/<author>/                         │
│   📄 Arquivo:     <slug>.transcript.txt                                      │
│   🔒 Canal:       LOCKED (agent dir exists) | 🆕 NEW                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📊  ESTATISTICAS ──────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────┐        │
│   │ Palavras         │ <N>                                          │        │
│   │ Source           │ gemini-native | youtube-captions | whisper   │        │
│   │ Gemini status    │ ✅ ok | ⚠️ timeout → fallback | ⏭️ bypassed   │       │
│   │ Tempo total      │ ~<Xs>                                        │        │
│   └──────────────────┴──────────────────────────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

# Adicionar apenas se --process foi usado:
┌─ ⚙️  PIPELINE ───────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────┐        │
│   │ Chunks           │ <N>                                          │        │
│   │ Insights         │ <N> total (🔴 HIGH:<N> 🟡 MED:<N> 🟢 LOW:<N>)│        │
│   │ DNA Layers       │ L1-L10 (<N> preenchidas)                     │        │
│   │ RAG gate         │ ✅ PASS | ⚠️ WARN | ❌ FAIL                   │       │
│   └──────────────────┴──────────────────────────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ⭐  RESULTADO ─────────────────────────────────────────────────────────────┐
│                                                                              │
│   <briefing em 1-2 linhas sobre o que foi extraido e o proximo passo>        │
│                                                                              │
│   ⚙  <comando exato do proximo passo>                                        │
│   ⏱  Tempo estimado: <Xmin>                                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Regras de renderizacao:**
- Omitir bloco PIPELINE se `--process` nao foi usado.
- Campos opcionais (Duracao) omitir quando nao aplicaveis.
- Largura aproximada de 79 caracteres.

---

## Pergunta JARVIS de encerramento

Apos o box ASCII, Claude encerra com 1 pergunta concisa. Exemplos:
- `"Transcript disponivel, Senhor. Posso disparar o pipeline completo agora?"`
- `"Video processado. Deseja que eu execute uma busca RAG para validar os insights extraidos?"`
- `"Extracao concluida. Quer revisar o dossier atualizado de {PESSOA}, Senhor?"`

---

## Idempotencia MCE-7.0 (preservada)

Se o mesmo video for processado 2x:
- PV-B1 retorna early-exit com `SKIP`
- Claude narra: `"Esta fonte ja foi processada anteriormente, Senhor. Nenhuma acao necessaria."`
- Total de bashes: <= 2. Tempo total: < 30s.

---

## References

- Motor de extracao: `scripts/ingest-with-entity-discovery.py`
- CLI pipeline: `engine/intelligence/pipeline/mce/orchestrate.py`
- Jarvis chief: `engine/intelligence/pipeline/jarvis_chief.py`
- Story origem: `docs/stories/epic-mce-port-jarvis-v2.1/STORY-MCE-10.0-mordomo-multi-slash.md`
- Referencia de estrutura: `.claude/commands/ingest.md` (v4.0.1)
- Constitution: Art. XII (Pipeline MCE Integrity)
