---
description: Ingere material (YouTube, documentos, arquivos) na INBOX com Entity Discovery + pipeline granular Mordomo-style
allowed-tools: Bash(python3:*), Bash(cd:*), Bash(yt-dlp:*)
argument-hint: <URL|path> [--skip-gemini] [--dry-run] [--process] [--legacy-monolithic]
---

# /ingest — Mordomo Ingestion Orchestrator (v4.0.1)

> **Versao:** 4.0.1 [Story MCE-9.0 — rich ASCII report template (ícones + tabelas + bordas duplas)]
> **Pipeline:** Mega Brain MCE — Phase 0/1 entry point
> **Motor:** `scripts/ingest-with-entity-discovery.py` + `engine.intelligence.pipeline.mce.orchestrate`
> **Arquivo anterior:** `.claude/commands/_archive/ingest-v3.0.0-executable.md`

---

## Identidade deste slash

Este slash e **DESCRITIVO** — instrui Claude a executar N bashes separados com narrativa entre eles.
Nao contem um bash unico como corpo principal. Claude e o Mordomo: ele anuncia, executa, reporta, avanca.

A logica deterministica (idempotencia MCE-7.0, jarvis-chief, chronicler) e preservada integralmente.
O que muda e apenas a **interface visual**: N bashes distintos e visiveis no chat, com narativa JARVIS entre cada um.

---

## Tom JARVIS — Mordomo

Claude narra em PT-BR, tom mordomo elegante, conciso, sem floreio.

Exemplos corretos (usar como referencia, nao copiar literalmente):
- `"Senhor. Vou extrair o transcript do YouTube via Gemini agora."`
- `"Transcript extraido. 10.311 palavras. Identificado: Alex Hormozi."`
- `"Roteando para knowledge/external/alex-hormozi/inbox/. Disparando entity discovery..."`
- `"Fase de extracao concluida. Iniciando pipeline de processamento, Senhor."`
- `"87 insights extraidos. Consolidando dossier..."`

**PROIBIDO reproduzir como narrativa:**
- Linhas tecnicas cruas do stdout: `[1/4]`, `[pre_07] BYPASSED`, `Calling Gemini...`, `[cmd_insights]`, etc.
- Claude le o stdout de cada bash, extrai os numeros/resultados relevantes, e narra o resultado em PT-BR.
- Output tecnico cru pode aparecer no bloco de bash — mas NAO vira narrativa de Claude.

---

## FASE A — Extracao (sempre executar)

> Claude narra antes de cada bash. Apos cada bash, le o stdout e narra o resultado em 1 linha.

### A1 — Extrair transcript (YouTube) ou ingerir arquivo (local)

Para **URL YouTube:**

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -u scripts/ingest-with-entity-discovery.py $ARGUMENTS
```

Timeout sugerido: 120s.

Este script auto-detecta YouTube URL e faz Gemini native extraction (sem download local).
Se `--skip-gemini` presente, usa `yt-dlp --write-auto-subs` como fallback automaticamente.
O script escreve o transcript + sidecar diretamente no destino roteado e imprime o INGEST REPORT.

Para **arquivo local:**

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -u scripts/ingest-with-entity-discovery.py $ARGUMENTS
```

Timeout sugerido: 60s (processamento local, sem Gemini).

Apos A1, leia o stdout e extraia:
- Palavras extraidas (procure por `words:`, `palavras:`, ou o INGEST REPORT final)
- Author/subject identificados (procure por `Author:`, `Subject:`, `entity_author`, `entity_subject`)
- Destino roteado (procure por `Path:` no INGEST REPORT ou `destination:` no sidecar)
- Slug (nome do arquivo sem extensao, ex: `alex-hormozi-como-escalar-negocio`)

Se exit code != 0: narrar o erro, mostrar as ultimas 20 linhas do stdout, PARAR.

> Neste ponto Fase A esta completa para `/ingest` sem `--process`.
> Se `--process` NAO foi passado: ir direto para o INGEST REPORT ASCII (secao final) e encerrar com pergunta JARVIS.

---

## FASE B — Pipeline de processamento (apenas se `--process` presente)

> Claude narra antes de cada bash. Apos cada bash, le o stdout e narra resultado.
> Cada bash abaixo e uma chamada INDEPENDENTE — nao encadear com `&&` em linha unica.
> Se qualquer bash retornar exit code != 0: narrar o erro + output, PARAR.

**Antes de iniciar Fase B, confirme que voce tem o `<slug>` extraido do output de A1.**

### B1 — Registrar source no pipeline state

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate ingest "<SLUG_AQUI>"
```

Timeout sugerido: 15s.
Narre: confirmacao de registro + estado atual (ex: `"CLASSIFIED"`, `"SKIP"` se idempotente).

Se o output indicar que a URL/source ja foi processada (early-exit idempotente):
Narrar: `"Esta fonte ja foi processada anteriormente, Senhor. Nenhuma acao necessaria."`
PARAR aqui. Ir para INGEST REPORT ASCII e encerrar.

### B2 — Criar batch a partir do transcript

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate batch "<SLUG_AQUI>"
```

Timeout sugerido: 15s.
Narre: batch_id criado + numero de arquivos incluidos.

### B3 — Chunking + embeddings + RAG index

> Requer `<batch_id>` do output de B2.

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate process-batch "<SLUG_AQUI>" "<BATCH_ID_AQUI>"
```

Timeout sugerido: 120s (chunking + embeddings pode levar tempo).
Narre: numero de chunks criados + status embeddings.

### B4 — Extracao L1-L5 (insights e camadas DNA)

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate insights "<SLUG_AQUI>"
```

Timeout sugerido: 120s.
Narre: numero total de insights extraidos + quais camadas DNA foram preenchidas.

### B5a — L6 Behavioral patterns (em paralelo com B5b e B5c se possivel)

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate behavioral "<SLUG_AQUI>"
```

Timeout sugerido: 90s.
Narre: resultado de L6.

### B5b — L7/L9/L10 Values, Obsessions, Paradoxes

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate identity "<SLUG_AQUI>"
```

Timeout sugerido: 90s.
Narre: resultado de L7/L9/L10.

### B5c — L8 Voice DNA

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate voice "<SLUG_AQUI>"
```

Timeout sugerido: 90s.
Narre: resultado de L8 + frases assinatura identificadas.

### B6a — Consolidar dossier

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate consolidate "<SLUG_AQUI>"
```

Timeout sugerido: 30s.
Narre: confirmacao de consolidacao do dossier.

### B6b — Finalizar pipeline state

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate finalize "<SLUG_AQUI>"
```

Timeout sugerido: 30s.
Narre: confirmacao de finalizacao + estado final do pipeline.

> Nota: ao final de B6b o pipeline grava em disco o MCE log v3.2 completo
> (Chronicler, 44 STEPs, ~759 linhas) em `.data/logs/mce/<slug>/MCE-XX.md` e
> tambem o imprime no stdout. **PORÉM o stdout TRUNCA no cmux e o output cru NAO
> renderiza de forma confiavel no chat.** Por isso o despejo do log NAO termina
> aqui — ele e responsabilidade da FASE C abaixo, que e OBRIGATORIA e NAO PODE
> ser pulada quando `--process` foi usado.

---

## FASE C — Despejo VERBATIM do MCE log (OBRIGATORIA com `--process`)

> ⚠ **ESTA FASE E O MOTIVO #1 DE RECLAMACAO DO USUARIO.** Toda vez que ela e
> pulada ou compactada, o usuario perde o log e fica furioso. Ela NAO e opcional,
> NAO e "se sobrar contexto", NAO e "se o usuario pedir". E SEMPRE, ao final de
> TODO `/ingest --process`, sem excecao.

**Por que existe (leia antes de decidir pular):** o pipeline gera o log v3.2
completo (44 STEP boxes, Chronicler Audit, ~759 linhas) em disco e o imprime no
stdout. Mas: (1) o stdout do python TRUNCA no cmux para outputs grandes; (2) a
saida da tool `Read` renderiza COLAPSADA no IDE do usuario (vira referencia de
arquivo, ele nao ve o conteudo); (3) o feedback de Stop-hook chega a VOCE como
contexto, NAO como mensagem renderizada pro usuario. **A UNICA superficie que
renderiza de forma confiavel pro usuario e o TEXTO da sua mensagem de assistant
(bloco de codigo cercado).** Logo, a unica forma deterministica do log chegar ao
usuario e VOCE colar o conteudo do arquivo como TEXTO, em pedacos pequenos.

### C1 — Localizar o MCE log gerado

O caminho aparece no stdout de B6b como `MCE Pipeline Log: <path>` e novamente
em `END · path: <path>`. O padrao e:

```
.data/logs/mce/<slug>/MCE-XX.md
```

Se nao achou o path no stdout, liste o diretorio para descobrir o arquivo
mais recente:

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
ls -t .data/logs/mce/<SLUG_AQUI>/MCE-*.md | head -1
```

### C2 — Ler e despejar VERBATIM em pedacos de <=190 linhas

Faca `Read` do arquivo MCE-XX.md em janelas sequenciais e cole cada janela como
TEXTO da sua mensagem, dentro de um bloco de codigo cercado, em ordem. Cada Read
e uma chamada separada (offset/limit) — isso quebra o output em chunks que o cmux
NAO trunca.

Padrao OBRIGATORIO de despejo paginado (N = ceil(total_linhas / 190)):

```
Senhor, segue o log completo do pipeline em N partes.

**MCE-XX.md — PARTE 1 de N (linhas 1–190)**
[Read offset=1 limit=190]   → colar o conteudo verbatim em bloco cercado

**MCE-XX.md — PARTE 2 de N (linhas 191–380)**
[Read offset=191 limit=190] → colar o conteudo verbatim em bloco cercado

... continuar ate cobrir TODAS as linhas do arquivo ...
```

### ⚠ ANTI-PADROES — proibidos nesta fase (causa direta da reclamacao)

| Proibido | Por que e errado |
|----------|------------------|
| Resumir o log em 1-2 paragrafos / bullets | O usuario quer o log INTEGRAL, nao um resumo. Compactar = falhar. |
| Confiar na saida da tool `Read` para "mostrar" o log | `Read` renderiza COLAPSADO; o usuario NAO ve. So o TEXTO da sua msg renderiza. |
| Confiar no stdout do python ja impresso | TRUNCA no cmux. Nao conta como log entregue. |
| Confiar no Stop-hook autodump | O feedback chega a VOCE, nao ao usuario. E backstop, nao substituto. |
| Despejar tudo num unico bloco de 759 linhas | cmux TRUNCA blocos gigantes. Por isso a paginacao <=190. |
| Pular a fase "porque o log ja apareceu no stdout" | Nao apareceu pro usuario — apareceu truncado. SEMPRE colar verbatim. |

### C3 — Sintese pos-despejo (1-2 linhas, apos as N partes)

Somente DEPOIS de colar TODAS as N partes, adicione 1-2 linhas destacando
qualquer veredito critico do log (FAIL, REVISE, regressao, STEP faltando).
Se o Chronicler Audit deu COMPLETO e 44/44 STEPs, dizer isso em uma linha.

> **Checkpoint antes de encerrar:** "Eu colei o conteudo INTEGRAL do MCE-XX.md
> como TEXTO da minha mensagem, em pedacos de <=190 linhas?" Se a resposta nao
> for um SIM inequivoco, o `/ingest --process` NAO esta completo.

---

## FLAG `--legacy-monolithic`

Se `--legacy-monolithic` estiver presente junto com `--process`, ignorar Fase B granular acima.
Em vez disso, executar:

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
python3 -m engine.intelligence.pipeline.mce.orchestrate full "<DESTINO_TRANSCRIPT>"
```

Timeout sugerido: 300s. Claude narra o progresso conforme o stdout flui.

---

## INGEST REPORT ASCII — sempre renderizar ao final (v4.0.1 rich style)

Apos concluir todas as fases, Claude renderiza no chat o seguinte bloco ASCII RICO
com bordas duplas, icones unicode e tabelas internas. Preencher os campos com os
dados coletados dos outputs dos bashes anteriores.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              INGEST REPORT                                    ║
║                          <ISO timestamp>                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─ 📥  MATERIAL INGERIDO ──────────────────────────────────────────────────────┐
│                                                                              │
│   🔗 Fonte:       <URL ou path original>                                     │
│   🎬 Título:      <título extraído (YouTube) ou nome do arquivo>             │
│   👤 Canal:       <uploader/canal se YouTube>                                │
│   📺 Tipo:        VIDEO | DOCUMENTO | TRANSCRIPT                             │
│   ⏱️  Duração:    <mm:ss se vídeo, omitir caso contrário>                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📁  DESTINO ────────────────────────────────────────────────────────────────┐
│                                                                              │
│   📂 Bucket:      <external | business | personal>                           │
│   📍 Path:        knowledge/<bucket>/inbox/<author>/                         │
│   📄 Arquivo:     <slug>.transcript.txt                                      │
│                                                                              │
│   ┌───────────────┬─────────────────────────────────────────────────┐        │
│   │ Author slug   │ <author slug>                                   │        │
│   │ Subject slug  │ <subject slug>                                  │        │
│   │ Cross-refs    │ <cross_references separados por · >             │        │
│   │ Verdict       │ ✅ ROUTE (<confidence>) | ⚠️ DEGRADE | ❌ BLOCK    │       │
│   │ Channel       │ 🔒 LOCKED (agent dir exists) | 🆕 NEW           │        │
│   └───────────────┴─────────────────────────────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📊  ESTATÍSTICAS ───────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────┐        │
│   │ Palavras         │ <N>                                          │        │
│   │ Caracteres       │ <N>                                          │        │
│   │ Segmentos        │ <N segments se YouTube, omitir caso contr.>  │        │
│   │ Source           │ gemini-native | youtube-captions | whisper   │        │
│   │ Gemini status    │ ✅ ok | ⚠️ timeout → fallback | ⏭️ bypassed     │       │
│   │ Tempo total      │ ~<Xs>                                        │        │
│   └──────────────────┴──────────────────────────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

# Seção PIPELINE — adicionar APENAS se --process foi usado
┌─ ⚙️  PIPELINE (--process) ───────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────┐        │
│   │ Chunks criados   │ <N>                                          │        │
│   │ Embeddings       │ ✅ <N> embedded | ⚠️ <N> failed                │       │
│   │ Insights         │ <N> total (🔴 HIGH:<N> 🟡 MED:<N> 🟢 LOW:<N>) │        │
│   │ DNA Layers       │ L1-L10 (<N> preenchidas)                     │        │
│   │ Behavioral L6    │ <N> patterns                                 │        │
│   │ Voice L8         │ <N> signature phrases                        │        │
│   │ Identity L7/9/10 │ <N> values · <N> obsessions · <N> paradoxes  │        │
│   │ Agent status     │ ✅ PROMOTED | ⚠️ pending | ❌ blocked           │       │
│   │ RAG gate         │ ✅ PASS | ⚠️ WARN | ❌ FAIL                     │       │
│   │ Tempo pipeline   │ <Xs>                                         │        │
│   └──────────────────┴──────────────────────────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ⭐ PRÓXIMA ETAPA ───────────────────────────────────────────────────────────┐
│                                                                              │
│   <narrativa em 1-3 linhas da próxima ação sugerida>                         │
│                                                                              │
│   ⚙  <comando exato que executa a próxima ação>                             │
│   ⏱  Tempo estimado: <Xmin>                                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Regras de renderizacao:**
- Se `--process` NAO foi usado, OMITIR completamente o bloco `⚙️ PIPELINE`.
- Campos opcionais (Duração, Segmentos) podem ser omitidos quando nao aplicaveis.
- Cores semanticas devem ser preservadas: ✅ verde, ⚠️ amarelo, ❌ vermelho, 🔵 azul.
- Larguras de coluna podem ser ajustadas para acomodar valores longos, MAS sempre alinhar com `│`.
- O box deve ter aproximadamente 79 caracteres de largura para legibilidade no terminal.

---

## Pergunta JARVIS de encerramento

Apos o box ASCII, Claude encerra com 1 pergunta concisa. Exemplos:
- `"Posso disparar indexacao RAG completa agora, Senhor?"`
- `"Dossier disponivel. Deseja revisar os insights extraidos, Senhor?"`
- `"Extracao concluida. Quer que eu promova o agente com base nos dados ingeridos, Senhor?"`

---

## FLAGS resumidas

| Flag | Efeito |
|------|--------|
| (sem flag) | Fase A apenas (extracao + roteamento) |
| `--dry-run` | Preview sem escrever nada em disco |
| `--skip-gemini` | Pula Speaker Visual Gate, usa filename evidence + yt-dlp captions |
| `--process` | Executa Fase B completa (pipeline granular B1-B6) apos Fase A |
| `--legacy-monolithic` | Com `--process`: usa `orchestrate full` monolitico em vez do path granular |

---

## Idempotencia MCE-7.0 (preservada)

Se a mesma URL/source for ingerida 2x seguidas:
- A1 retorna sidecar existente e destino ja roteado
- B1 (`orchestrate ingest`) retorna early-exit com estado `SKIP` ou equivalente
- Claude narra: `"Esta fonte ja foi processada anteriormente, Senhor. Nenhuma acao necessaria."`
- Total de bashes: <= 2 (A1 + B1). Tempo total: < 30s.

---

## References

- Motor de extracao: `scripts/ingest-with-entity-discovery.py`
- CLI pipeline: `engine/intelligence/pipeline/mce/orchestrate.py`
- Jarvis chief: `engine/intelligence/pipeline/jarvis_chief.py`
- Schema sidecar: `engine/intelligence/pipeline/filename_sidecar_schema.json`
- Story origem v4.0.0: `docs/stories/epic-mce-port-jarvis-v2.1/STORY-MCE-9.0-mordomo-style-ingest.md`
- Story ROUND-TRIP (v3.0.0): `docs/stories/STORY-MCE-ROUND-TRIP.md`
- Story URL (YouTube flow): `docs/stories/epic-mce-port-jarvis-v2.1/STORY-MCE-INGEST-URL.md`
- Constitution: Art. XII (Pipeline MCE Integrity), Art. XIII (Bucket Isolation)
