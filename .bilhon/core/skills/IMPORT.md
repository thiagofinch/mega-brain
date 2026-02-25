# Skills Import Reference

> **Tipo:** Import Reference
> **Fonte:** /.claude/skills/
> **Status:** Active

## Descricao

Esta pasta e uma referencia para as skills localizadas em `/.claude/skills/`.

## Skills Disponíveis

As skills do Mega Brain estao em `/.claude/skills/`:

- `/pdf` - Processamento de PDFs
- `/xlsx` - Processamento de Excel
- `/source-sync` - Sincronizacao com planilha
- `/council` - Debate de agentes
- `/save` - Salvar sessao
- `/resume` - Recuperar sessao
- `/verify` - Verificacao pos-sessao

## Auto-Ativacao

Skills sao auto-ativadas quando keywords matcham no prompt.

Cada SKILL.md tem:
```markdown
> **Auto-Trigger:** [Quando ativar]
> **Keywords:** "keyword1", "keyword2"
> **Prioridade:** ALTA
```

## Novas Skills BILHON OS

Skills especificas do BILHON OS serao adicionadas conforme implementadas:

- [ ] `/health` - Health check rapido
- [ ] `/project` - Iniciar novo projeto
- [ ] `/quality` - Executar quality gates
