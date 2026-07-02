# RESUME SESSION - Recuperacao de Contexto

> **Auto-Trigger:** Quando usuario quer retomar sessao anterior
> **Keywords:** "resume", "retomar", "onde paramos", "ultima sessao", "continuar"
> **Prioridade:** ALTA
> **Tools:** Read, Glob, Bash

## Quando NAO Ativar
- Quando o usuario esta apenas perguntando sobre o projeto (sem querer retomar)
- Quando e primeira sessao (sem sessoes anteriores)

## Trigger
`/resume` ou ao iniciar nova conversa

## Objetivo
Recuperar contexto da ultima sessao usando dados factuais (git log, branch state, SESSION-INDEX).
NAO carregar snapshots de conversa -- o material bruto vive no `claude --resume <UUID>`.

## Fontes de Contexto (em ordem de prioridade)

1. **SESSION-INDEX.json** -- lista de sessoes com UUIDs para `--resume`
2. **git log / git status** -- o que foi feito e o que esta pendente
3. **git branch** -- em qual branch estamos e qual e o trabalho em andamento
4. **JARVIS STATE** -- `.claude/jarvis/STATE.json` para estado de missao/pipeline
5. **PENDING.md** -- `.claude/jarvis/PENDING.md` para pendencias

## O que NAO usar
- ~~LATEST-SESSION.md~~ (removido -- era snapshot de conversa)
- ~~CURRENT-SESSION.md~~ (removido -- era snapshot de conversa)
- ~~current.jsonl~~ (removido -- duplicava transcripts do --resume)
- Qualquer arquivo que contenha logs de mensagens/respostas da conversa

## Execucao

### 1. Carregar Session Index
Ler `.claude/sessions/SESSION-INDEX.json` para obter UUID da ultima sessao.

### 2. Levantar Estado Factual
Em paralelo:
- `git log --oneline -15` -- commits recentes
- `git status` -- mudancas pendentes
- `git branch -v` -- branches ativas
- Ler `.claude/jarvis/STATE.json` se existir

### 3. Apresentar Resumo

Formato conciso:

```
RETOMANDO SESSAO

Branch: [branch-name]
Ultimo commit: [hash] [message] ([data])
UUID ultima sessao: [uuid]

O QUE FOI FEITO (ultimos commits):
- [commit 1]
- [commit 2]

ESTADO ATUAL:
- [N] arquivos modificados nao commitados
- [descricao do trabalho em andamento]

PARA RETOMAR TRANSCRIPT COMPLETO:
claude --resume [UUID]
```

### 4. Perguntar
"Quer continuar de onde paramos ou precisa de algo diferente?"

### 5. Listar Sessoes (se pedido)

```
/resume list   -- mostra ultimas 10 sessoes com UUIDs
/resume search <keyword> -- busca por keyword no first_prompt
```

## Principio Central

**Sessoes = ponteiros para material bruto, nao copias do material.**

O `claude --resume <UUID>` ja tem o transcript completo. Esta skill apenas ajuda a encontrar o UUID certo e mostrar contexto factual (git, state) para orientar a retomada.
