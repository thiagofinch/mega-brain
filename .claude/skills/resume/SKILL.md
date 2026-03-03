# RESUME SESSION - Recuperação de Contexto

> **Auto-Trigger:** Quando usuário quer retomar sessão anterior
> **Keywords:** "resume", "retomar", "onde paramos", "última sessão", "continuar"
> **Prioridade:** ALTA
> **Tools:** Read, Glob, Bash

## Quando NÃO Ativar
- Quando o usuário está apenas perguntando sobre o projeto (sem querer retomar)
- Quando é primeira sessão (sem sessões anteriores)

## Trigger
`/resume` ou ao iniciar nova conversa

## Objetivo
Recuperar o contexto COMPLETO da última sessão para continuar de onde parou.

## Execução

### 1. Carregar Session Index (PRIMEIRO)
Ler `.claude/sessions/SESSION-INDEX.json` para obter lista de sessões com UUIDs.

Este índice contém:
- **uuid**: ID da sessão (usável com `claude --resume <UUID>`)
- **started**: Quando a sessão começou
- **last_activity**: Última atividade registrada
- **first_prompt**: Primeiro prompt do usuário (para busca por keyword)
- **transcript**: Caminho para transcript interno do Claude Code

### 2. Localizar Última Sessão
Ler `.claude/sessions/LATEST-SESSION.md` para contexto da sessão mais recente.

### 3. Carregar Contexto
Ler o arquivo de sessão completo e extrair:
- Estado da missão
- Fase atual
- Pendências
- Próximos passos
- Decisões tomadas
- Notas importantes

### 4. Apresentar Resumo de Retomada

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🔄 RETOMANDO SESSÃO                                                         │
│                                                                              │
│  Última atividade: [DATA/HORA]                                              │
│  UUID: [SESSION-UUID]                                                        │
│  Duração desde última sessão: [X horas/dias]                                │
│                                                                              │
│  📍 ONDE PARAMOS:                                                            │
│  Missão: [NOME]                                                              │
│  Fase: [N] de 5 - [NOME_FASE]                                               │
│  Progresso: [X]%                                                             │
│                                                                              │
│  📋 PENDÊNCIAS HERDADAS:                                                     │
│  - [Pendência 1]                                                             │
│  - [Pendência 2]                                                             │
│                                                                              │
│  ➡️ PRÓXIMO PASSO PLANEJADO:                                                 │
│  [Descrição do próximo passo]                                                │
│                                                                              │
│  💡 DECISÕES ANTERIORES:                                                     │
│  - [Decisão relevante]                                                       │
│                                                                              │
│  💾 PARA RETOMAR TRANSCRIPT COMPLETO:                                        │
│  claude --resume [UUID]                                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5. Perguntar Confirmação
"Quer continuar de onde paramos ou precisa de algo diferente?"

### 6. Listar Sessões Antigas (Opcional)
Se usuário pedir, ler SESSION-INDEX.json e listar todas as sessões:

```
/resume list - mostra todas as sessões salvas com UUIDs
/resume search <keyword> - busca por keyword no first_prompt
/resume [SESSION-ID] - carrega sessão específica
```

**Formato de listagem:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📋 SESSÕES DISPONÍVEIS (últimas 10)                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. [DATA] [HORA] - "primeiro prompt resumido..."                            │
│     UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                               │
│     ➡ claude --resume <UUID>                                                 │
│                                                                              │
│  2. [DATA] [HORA] - "primeiro prompt resumido..."                            │
│     UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                               │
│     ➡ claude --resume <UUID>                                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7. Buscar por Keyword
Quando o usuário disser `/resume search <termo>`:
1. Ler SESSION-INDEX.json
2. Filtrar sessões onde `first_prompt` contém o termo
3. Listar resultados com UUIDs para `--resume`

## Output
Contexto recuperado + resumo visual + UUID para --resume + confirmação do usuário
