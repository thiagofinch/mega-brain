# 🎛️ .antigravity/

> **Sistema de Extensões e Overrides Locais**

Esta pasta permite customizações locais sem modificar o core do Mega Brain.

## Estrutura

```
.antigravity/
└── rules/          # Regras customizadas (override do .claude/rules/)
    └── .gitkeep
```

## Como Usar

### Adicionar Override de Regra

Crie um arquivo `.md` em `rules/` com o mesmo nome da regra original:

```markdown
# Override: RULE-GROUP-1.md

> Este arquivo sobrescreve comportamentos específicos do RULE-GROUP-1

## Modificações Locais

- [Suas customizações aqui]
```

### Prioridade de Carregamento

1. `.claude/rules/*.md` (regras base)
2. `.antigravity/rules/*.md` (overrides - maior prioridade)

## Padrão Mega Brain

Este sistema permite extensões locais sem poluir o repositório principal, seguindo padrões Mega Brain de override e customização.

## Gitignore

Por padrão, o conteúdo de `.antigravity/rules/` é **trackeado** no git. Se quiser regras locais não commitadas, adicione ao `.gitignore`:

```gitignore
.antigravity/rules/*.local.md
```
