---
name: log-session
description: Chamado UNIVERSAL para tudo de log, memória e estado de sessão — grava log persistente, salva memória, lista próximos passos, atualiza process map (conductor), aplica taxonomy, envia ao reports endpoint (que mirrora pro ClickUp) E recupera status pra recomeçar de onde parou. Sub-formas: salva/checkpoint/escreve, status/retoma, ultimo, de <filtro>, sobre <titulo>, migra/retroativo.
version: 2.1.0
owner_squad: cos-reports
created_by: reports-system
megabrain_tier: Tier1
context: conversation
agent: general-purpose
user-invocable: true
argument-hint: "[salva|checkpoint|escreve|status|retoma|ultimo|de <filtro>|sobre <titulo>|migra|retroativo]"
---

# /log-session — Memória Persistente Universal de Sessões

> Atalho UNIVERSAL do ecossistema da sua organização pra TUDO relacionado a
> log, memória e gravação de dados de sessão. Serve pros DOIS sentidos:
> **gravar** (fechar/checkpoint de sessão) e **recuperar** (saber o status e recomeçar
> de onde parou). Disponível em todos os repositórios e pastas do ecossistema, para
> qualquer usuário e qualquer harness (Claude Code, Gemini CLI, Codex, Copilot, Antigravity).

## Trigger

| Invocação | Ação |
|---|---|
| `/log-session` (sem args) | **status do projeto atual + lista 10 últimos logs** |
| `/log-session salva` · `checkpoint` · `escreve` | **grava**: pipeline completo (log + memória + taxonomy + conductor + reports) |
| `/log-session status` · `retoma` · "de onde parei?" | **recupera**: lê últimos logs do projeto e apresenta contexto + próximos passos |
| `/log-session ultimo` | lê o log mais recente |
| `/log-session de <filtro>` | lista filtrado por conta/projeto/data/mismatch |
| `/log-session sobre <titulo>` | grava com título específico |
| `/log-session migra` · `retroativo` | cria log retroativo `.MISMATCH` |

Frases em chat equivalentes a `salva`: "salva a sessão", "grava o log", "coloca nos reports",
"fecha a sessão", "checkpoint". Equivalentes a `status`: "onde paramos?", "qual o status?", "retoma".

## Diretórios de logs (LOG_DIR) — acervo ESPELHADO, dual-write

| Lado | Path | Papel |
|---|---|---|
| Canônico (drive externo) | `${ARCHIVE_DRIVE}/outputs/log-session/` | canônico |
| Espelho (máquina local) | `${LOCAL_LOGS_DIR}/users/{user}/sessions/log-session/` | espelho 1:1 (paridade canônico ≡ espelho) |

- **Gravar (`salva`):** na máquina principal, escrever o log nos **DOIS lados** (dual-write). Drive canônico desmontado → gravar só no espelho local e AVISAR (NUNCA recriar pastas do drive canônico). Máquina de terceiros → `outputs/log-session/` na raiz do repo (gitignored).
- **Ler (`status`/`ultimo`/`de <filtro>`):** drive canônico montado → ler dele; senão → espelho local; senão → repo local.
- Se notar divergência entre os lados, igualar com cópia aditiva (`cp -n` nos 2 sentidos) — nunca deletar.

**Nomenclatura:** `DD-MM-YYYY_HH-MM_titulo-kebab-case_<conta>_<harness>[.MISMATCH].md`

Slugs de conta: `{username}-org` (derivado de `git config user.email`, ex.: `user@example.com` → `user-org`). Contas pessoais avulsas usam `{username}-pessoal`.
Slugs de harness: `claude-code` · `antigravity` · `google-ai` · `codex` · `copilot` · `web`.
Sufixo `.MISMATCH`: conta × harness × projeto trocados. Convenção completa: `${ARCHIVE_DRIVE}/outputs/log-session/README.md`.

## Modo `salva` / `checkpoint` / `escreve` — pipeline completo (7 passos)

### 1. Detectar contexto
- **Conta + harness:** `git config user.email` + path do terminal. Divergência do esperado → marcar `.MISMATCH` e ALERTAR antes de salvar.
- **Projeto:** cwd + git remote (ex.: `<repo-root>/apps/comercial` → `comercial`; `<repo-root>/mega-brain` → `mega-brain`).
- **Título:** fornecido via `sobre <titulo>`, senão gerar curto a partir do trabalho da sessão.
- **Horas:** estimar pelo tempo decorrido (default 1h se incerto).

### 2. Construir e gravar o log

```markdown
# {titulo}

**Data:** DD/MM/YYYY HH:MM (BRT)
**Conta:** {slug-conta}
**Harness:** {slug-harness}
**Projeto:** {slug-projeto}
**Mismatch:** {não | sim — esperado: <conta correta>}

## Contexto inicial
{o que estava rolando antes da sessão}

## O que foi feito
- ...

## Decisões-chave
- ...

## Pendências / próximos passos
- [ ] ... (esta lista É o ponto de retomada do modo `status`)

## Arquivos tocados
- /caminho/absoluto/...

## Memórias salvas
- {arquivos de memória criados/atualizados no passo 3, se houver}
```

Gravar com Write em `{DD-MM-YYYY}_{HH-MM}_{titulo-kebab}_{conta}_{harness}[.MISMATCH].md` — **UTF-8 sem BOM**, acentuação PT-BR correta — **nos DOIS lados** (drive canônico + espelho `${LOCAL_LOGS_DIR}/users/{user}/sessions/log-session/`), conforme a seção LOG_DIR.

### 3. Memória
Se a sessão produziu fato durável (decisão, convenção, armadilha, estado de projeto): salvar/atualizar memória pelo mecanismo do harness (no Claude Code: `~/.claude/projects/{project}/memory/` + index `MEMORY.md`). Listar os arquivos na seção "Memórias salvas" do log. Sem fato durável → pular (não poluir memória).

### 4. Taxonomy
Aplicar a classificação funcional do ecossistema (skill de taxonomy do ambiente, ou as convenções dela se a skill não estiver disponível) pra gerar as **tags** kebab-case do log e da entry do reports.

### 5. Process map HTML (conductor)
Se a sessão pertence a um track do conductor (`${ARCHIVE_DRIVE}/conductor/tracks/{track}/`): atualizar o `index.html` do track (mapa de processo — fases concluídas, pendências, datas). Se não houver track associado, pular sem perguntar.

### 6. Enviar entry pro reports endpoint

```bash
curl -s -X POST {{REPORTS_BASE_URL}}/api/report/ingest \
  -H "Content-Type: application/json" \
  -H "x-webhook-secret: ${REPORTS_WEBHOOK_SECRET}" \
  -d '{"entries":[{
    "username": "{username}",
    "source": "manual",
    "project_id": "{slug-projeto}",
    "task": "{titulo}",
    "category": "{dev|planning|infra|admin|deploy|qa|review|...}",
    "hours": {horas},
    "date": "{YYYY-MM-DD}",
    "deliverable": "{resumo 1-2 frases do que entregou}",
    "description": "{contexto + decisões}",
    "tags": ["{tags-do-passo-4}"]
  }]}'
```

- Secret: 1Password vault da sua organização, item do reports webhook (`op read`); fallback env `WEBHOOK_SECRET`. **NUNCA hardcodar.**
- Sources válidas: `git, github, clickup, fireflies, n8n, supabase, calendar, clint, manual, seed, cloudflare, hybridops`. **NUNCA `session`** (erro silencioso). Default: `manual`.
- Categories válidas: `dev, design, meeting, planning, review, admin, captacao, edicao, pos, qa, security, infra, deploy, call, sales, support`.
- Confirmar `{ingested: 1}` na resposta. Erro de validação → corrigir source/category e retentar.

### 7. ClickUp
- **Criação do card é AUTOMÁTICA**: trigger Postgres `report_entries_clickup_mirror` → N8N → card no Backlog ClickUp `{{CLICKUP_BACKLOG_LIST_ID}}` em ~5s. **NÃO chamar a API do ClickUp pra criar.**
- Se a sessão trabalhou numa **task ClickUp já existente**: atualizar a task (status/comentário via MCP ClickUp ou skill `clickup`), seguindo o formato Journey Log das rules.

### Confirmação ao usuário

```
Log salvo:
- File: {LOG_DIR}/{arquivo}.md
- Memória: {n} arquivo(s) atualizado(s) (ou "—")
- Conductor: track {nome} atualizado (ou "—")
- Reports: {{REPORTS_BASE_URL}}/{username}/log/{id} ({ingested:1})
- ClickUp: card auto-criado via trigger (~5s) | task {id} atualizada
- Próximos passos registrados: {n} itens
```

## Modo `status` / `retoma` — recomeçar de onde parou

1. Detectar projeto atual (cwd + git remote).
2. `ls -t {LOG_DIR}` filtrado pelo projeto → ler os 2–3 logs mais recentes.
3. Cruzar com memória do harness e, se houver, com o track do conductor.
4. Apresentar: **última sessão** (quando, o quê) · **decisões-chave** · **PRÓXIMOS PASSOS** (a lista de pendências do último log, como ponto de partida) · alertas de `.MISMATCH`.
5. Oferecer: "continuar do item 1?" — e seguir trabalhando.

## Modos auxiliares

- **`ultimo`:** `ls -t {LOG_DIR}/*.md | head -1` → Read.
- **lista (sem args):** `ls -t {LOG_DIR}/*.md | head -10` → exibir data + título + conta extraídos do filename (e em seguida o status curto do projeto atual).
- **`de <filtro>`:** `ls -t {LOG_DIR} | grep -i "{filtro}" | head -10`. Filtros úteis: projeto, conta, `DD-MM`, `mismatch`.
- **`migra` / `retroativo`:** pedir data/hora retroativa, título, conta correta vs usada, resumo → gravar com `.MISMATCH`.

## Regras

1. **PT-BR sempre** — títulos, descrições, tags em português com acentuação correta.
2. **UTF-8 sem BOM** — nunca gravar/propagar mojibake (Ã©, Ã£ etc.); se encontrar log corrompido, corrigir o encoding antes de reaproveitar.
3. **Mismatch é importante** — detectou → ALERTAR antes de salvar.
4. **Não duplicar** — 2x `salva` em <5min → perguntar se atualiza o último ou cria novo.
5. **Logs são append-only** — nunca deletar/reescrever logs antigos; correção = novo log referenciando o antigo.
6. **Segredos** — webhook secret e API keys SEMPRE via 1Password/env. Nunca no log, nunca na skill.
7. **Push é do @devops** — esta skill grava arquivos e chama APIs; nunca faz `git push`.
8. **Graceful degradation** — reports fora do ar ou drive canônico desmontado NÃO bloqueiam o log local: gravar o arquivo, avisar o que falhou e o que fazer depois.

## Provenance

- v1.0 — pasta + convenção `outputs/log-session`. v1 estendida — pipeline reports + ClickUp mirror.
- v2.0 — chamado universal: status/retomada, memória, taxonomy, conductor process map, distribuição pra todos os repos/harnesses do ecossistema. Ingest via `/api/report/ingest`.
- v2.1 — acervo espelhado no espelho local (`${LOCAL_LOGS_DIR}/users/{user}/sessions/log-session/`) + dual-write canônico+espelho na máquina principal.
