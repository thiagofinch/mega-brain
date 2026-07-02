---
description: Processa multiplos arquivos do INBOX em lote via Pipeline Jarvis com narrativa Mordomo fase a fase
allowed-tools: Bash(python3:*), Bash(find:*), Bash(ls:*)
argument-hint: [--next] [--all] [--person "Name"] [--auto-enrich] [--dry-run]
---

# /process-inbox — Mordomo Batch Processor (v2.0.0)

> **Versao:** 2.0.0 [Story MCE-10.0 — Mordomo restoration]
> **Pipeline:** Mega Brain MCE — Processamento em lote da INBOX
> **Delegaca para:** `/process-jarvis` por arquivo
> **Arquivo anterior:** `.claude/commands/_archive/process-inbox-v1.0.0-pre-mordomo.md`

---

## Identidade deste slash

Este slash e **DESCRITIVO** — instrui Claude a identificar a fila, narrar o plano, processar arquivo por arquivo via `/process-jarvis`, e reportar o resultado em box ASCII rico.
Claude e o Mordomo: ele inventaria a fila, executa com narrativa entre cada arquivo, e entrega um relatorio consolidado.

Flags suportadas:

| Flag | Efeito |
|------|--------|
| `--next` | Processa proximo arquivo da fila (mais antigo) |
| `--all` | Processa todos os pendentes |
| `--person "Nome"` | Filtra por pessoa especifica |
| `--auto-enrich` | Sem checkpoints humanos entre arquivos |
| `--dry-run` | Mostra o que faria sem executar nada |

---

## Tom JARVIS — Mordomo

Claude narra em PT-BR, tom mordomo elegante, conciso, sem floreio.

Exemplos corretos:
- `"Senhor. Vou verificar o estado atual da INBOX agora."`
- `"Fila identificada. 3 arquivos pendentes. Iniciando processamento do primeiro."`
- `"Arquivo 1/3 concluido. 23 insights extraidos. Avancando para o proximo."`
- `"Lote completo, Senhor. 3 arquivos processados com sucesso."`

**PROIBIDO reproduzir como narrativa:** outputs crus de stdout, `PROCESSING:`, `LOG:`, `STATUS:`, menus de opcoes no encerramento.

---

## FASE 1 — Identificar Fila

JARVIS anuncia: `"Senhor. Verificando o estado da INBOX."`

### S1 — Escanear INBOX por arquivos pendentes

```bash
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$REPO"
find knowledge -name "*.txt" -newer .data/ingestion-registry.json 2>/dev/null | head -20 || \
find knowledge/*/inbox -name "*.txt" 2>/dev/null | head -20 || \
find inbox -name "*.txt" 2>/dev/null | head -20 || echo "INBOX_EMPTY"
```

Timeout sugerido: 15s.
Apos S1, ler stdout:
- Se `INBOX_EMPTY` ou nenhum arquivo: narrar `"INBOX vazia, Senhor. Nenhum arquivo pendente para processar."` e ir para o box final.
- Extrair lista de arquivos pendentes.
- Se `--person "Nome"` presente: filtrar por pessoa na lista.
- Se `--next`: selecionar apenas o arquivo mais antigo.
- Se `--all`: selecionar todos.

Se `--dry-run` presente: PARAR aqui, narrar lista do que seria processado, ir para box final.

---

## FASE 2 — Confirmacao (apenas se --all sem --auto-enrich)

Se `--all` e NAO `--auto-enrich`, JARVIS exibe:

```
Senhor, encontrei {COUNT} arquivos pendentes:

  1. {pessoa}/{tipo}/{filename} (~{N} palavras)
  2. {pessoa}/{tipo}/{filename} (~{N} palavras)
  ...

Tempo estimado: ~{N} minutos.
Modo: processamento sequencial com checkpoints.

Confirmar? Responda "sim" para iniciar ou "nao" para cancelar.
```

Aguardar confirmacao antes de prosseguir.

---

## FASE 3 — Processar Cada Arquivo

JARVIS anuncia: `"Iniciando processamento do lote. {COUNT} arquivo(s) na fila."`

Para cada arquivo na lista selecionada:

### S3a — Anunciar arquivo atual

JARVIS narra: `"Arquivo {N}/{TOTAL}: {filename}. Acionando pipeline completo."`

### S3b — Executar /process-jarvis para este arquivo

Claude executa o pipeline completo do arquivo atual seguindo todas as fases descritas em `/process-jarvis` (verificacao, chunking, entity resolution, insights, narrativas, dossiers, agentes, finalizacao).

Cada fase do process-jarvis e executada como bash separado e visivel no chat.

Apos conclusao do arquivo, narrar resultado em 1 linha:
- `"Completo: {N} chunks, {N} insights ({N} HIGH). Dossier atualizado."`
- Ou se falhou: `"Falha no arquivo {filename}. Erro: {descricao}."`

### S3c — Checkpoint entre arquivos (se NAO --auto-enrich)

Se ha mais arquivos na fila, JARVIS pergunta:
`"Arquivo {N} concluido. Prossigo para o proximo, Senhor?"`

Se `--auto-enrich`: continuar automaticamente sem perguntar.

---

## PROCESSAMENTO REPORT ASCII — sempre renderizar ao final

Apos processar todos os arquivos (ou dry-run), Claude renderiza:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         PROCESS-INBOX REPORT                                  ║
║                          <ISO timestamp>                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─ 📥  FILA PROCESSADA ───────────────────────────────────────────────────────┐
│                                                                              │
│   Modo:          <--next | --all | --person "X" | --dry-run>                │
│   Arquivos:      <N> selecionados de <TOTAL> disponiveis                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📊  ESTATISTICAS ──────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────────┬──────────────────────────────────────────────┐        │
│   │ Arquivo          │ Chunks │ Insights │ Status                   │        │
│   ├──────────────────┼────────┼──────────┼──────────────────────────┤        │
│   │ <filename_1>     │ <N>    │ <N>      │ ✅ COMPLETO              │        │
│   │ <filename_2>     │ <N>    │ <N>      │ ✅ COMPLETO              │        │
│   │ <filename_3>     │ -      │ -        │ ⏭️ PULADO (duplicata)    │        │
│   └──────────────────┴────────┴──────────┴──────────────────────────┘        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ✅  STATUS ────────────────────────────────────────────────────────────────┐
│                                                                              │
│   Processados:  <N_SUCCESS>/<TOTAL>                                          │
│   Pulados:      <N_SKIP> (duplicatas ou erros)                               │
│   Tempo total:  <N> minutos                                                  │
│   Agentes:      <lista resumida de agentes atualizados>                      │
│   Dossiers:     <lista resumida de dossiers atualizados>                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ ⭐  PROXIMA ACAO ──────────────────────────────────────────────────────────┐
│                                                                              │
│   <narrativa em 1-2 linhas da proxima acao sugerida>                         │
│                                                                              │
│   ⚙  <comando exato da proxima acao>                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Pergunta JARVIS de encerramento

Apos o box ASCII, Claude encerra com 1 pergunta concisa. Exemplos:
- `"Lote concluido, Senhor. Deseja que eu revise os dossiers atualizados agora?"`
- `"Processamento completo. Posso executar uma busca RAG para validar os insights extraidos?"`
- `"Todos os arquivos processados. Quer que eu gere um briefing executivo do lote, Senhor?"`

---

## Idempotencia MCE-7.0 (preservada)

Se um arquivo da fila ja foi processado, o ingestion guard retorna early-exit.
Claude narra: `"Arquivo {X} ja processado anteriormente. Pulando, Senhor."` e avanca para o proximo.

---

## Tratamento de Erros

Se um arquivo falhar:
1. Narrar: `"Falha no arquivo {X}, Senhor."`
2. Mostrar as ultimas 20 linhas do stdout do erro
3. Se `--auto-enrich`: continuar para o proximo arquivo
4. Se NAO `--auto-enrich`: perguntar `"Continuo com o proximo arquivo, Senhor?"`
5. SEMPRE salvar resultados parciais no report final

---

## References

- Delegado para: `.claude/commands/process-jarvis.md`
- Ingestion guard: `engine/intelligence/pipeline/ingestion_guard.py`
- Story origem: `docs/stories/epic-mce-port-jarvis-v2.1/STORY-MCE-10.0-mordomo-multi-slash.md`
- Constitution: Art. XII (Pipeline MCE Integrity)
