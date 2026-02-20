# Contributing to Mega Brain

> **JARVIS Workflow Documentation**
> Este documento descreve o workflow completo para contribuir com o projeto Mega Brain,
> baseado no método Boris Cherny + Continuous Claude v3.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEGA BRAIN DEVELOPMENT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. ISSUE    →    2. BRANCH    →    3. DEVELOP    →    4. COMMIT          │
│      │                 │                  │                  │              │
│      │                 │                  │                  │              │
│      ▼                 ▼                  ▼                  ▼              │
│   [FEAT]          feat/issue-XX      Plan Mode +        refs #XX            │
│   [FIX]           fix/issue-XX       Claude Code        Atomic              │
│   [PIPELINE]      pipeline/XX                                               │
│   [AGENT]         agent/XX                                                  │
│                                                                             │
│                                                                             │
│   5. PR       →    6. VERIFY    →    7. MERGE                              │
│      │                 │                  │                                 │
│      ▼                 ▼                  ▼                                 │
│   Fixes #XX       6 Levels          Squash +                               │
│   Checklist       Pipeline          Delete Branch                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Issue First

Toda mudança começa com uma Issue.

### Issue Templates

| Template | Prefixo | Uso |
|----------|---------|-----|
| `feature.md` | `[FEAT]` | Nova funcionalidade |
| `bug.md` | `[FIX]` | Correção de bug |
| `pipeline.md` | `[PIPELINE]` | Tarefas do Pipeline JARVIS |
| `agent.md` | `[AGENT]` | Criação/atualização de agentes |

### Exemplo

```
Title: [FEAT] Adicionar validação automática de dossiers

Description:
Implementar script que valida automaticamente se dossiers estão
atualizados em relação aos batches processados.

Critérios de Aceite:
- [ ] Script compara datas de modificação
- [ ] Gera relatório de dossiers desatualizados
- [ ] Integra com Fase 5.4 do Pipeline
```

---

## 2. Branch Pattern

Após criar a Issue, crie um branch seguindo o padrão:

```
tipo/issue-XX-descricao-curta
```

### Exemplos

```bash
# Feature
git checkout -b feat/issue-42-dossier-validation

# Bug fix
git checkout -b fix/issue-15-cascading-error

# Pipeline task
git checkout -b pipeline/issue-23-phase4-batch-processing

# Agent update
git checkout -b agent/issue-31-hormozi-template-v3
```

---

## 3. Development with Claude

### Plan Mode OBRIGATÓRIO

Antes de qualquer implementação que modifique arquivos:

1. Entre em Plan Mode (`Shift+Tab` 2x)
2. Descreva o que será feito
3. Liste arquivos que serão modificados
4. Identifique dependências
5. Aguarde aprovação

### Quando Usar Plan Mode

| Situação | Plan Mode? |
|----------|------------|
| Nova feature | ✅ SIM |
| Bug fix | ✅ SIM |
| Refatoração | ✅ SIM |
| Criação de agente | ✅ SIM |
| Pergunta simples | ❌ NÃO |
| Status check | ❌ NÃO |
| Busca de informação | ❌ NÃO |

### Paralelismo

Para máxima produtividade, use múltiplos terminais:

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Terminal 1: Feature principal                                           │
│  Terminal 2: Testes                                                      │
│  Terminal 3: Documentação                                                │
│  Terminal 4: Logs e monitoramento                                        │
│  Terminal 5: Tarefas ad-hoc                                              │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Commit Pattern

### Formato

```
tipo(escopo): descrição curta

refs #XX

Descrição detalhada se necessário.
```

### Tipos

| Tipo | Uso |
|------|-----|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `refactor` | Refatoração |
| `test` | Testes |
| `chore` | Manutenção |

### Exemplos

```bash
# Feature
git commit -m "feat(validation): add dossier date comparison

refs #42

Implements automatic validation of dossier modification dates
against batch processing dates."

# Bug fix
git commit -m "fix(cascading): resolve duplicate destination writes

refs #15

Prevents multiple writes to same destination file during
batch cascading process."
```

### SEMPRE incluir `refs #XX`

Isso vincula o commit à Issue automaticamente.

---

## 5. Pull Request

### Criando o PR

```bash
# Push do branch
git push -u origin feat/issue-42-dossier-validation

# Criar PR (via gh CLI ou GitHub UI)
gh pr create --title "[FEAT] Add dossier validation" --body "Fixes #42"
```

### PR Template

O PR template inclui:
- Summary
- Related Issue (`Fixes #XX`)
- Type of Change
- JARVIS Context
- 6-Level Verification Checklist

### SEMPRE usar `Fixes #XX`

Isso fecha a Issue automaticamente quando o PR é merged.

---

## 6. Verification Pipeline

### 6 Níveis de Verificação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LEVEL 1: HOOKS/LINT                                                        │
│  ├── Python syntax check                                                    │
│  ├── YAML/JSON validation                                                   │
│  └── Pre-commit hooks                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 2: TESTS                                                             │
│  ├── Unit tests pass                                                        │
│  ├── Integration tests pass                                                 │
│  └── No regression                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 3: BUILD/INTEGRITY                                                   │
│  ├── Scripts execute without errors                                         │
│  ├── No circular imports                                                    │
│  └── Dependencies documented                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 4: VISUAL VERIFICATION                                               │
│  ├── Output format correct                                                  │
│  ├── ASCII art renders properly                                             │
│  └── Logs follow dual-location pattern                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 5: STAGING/INTEGRATION                                               │
│  ├── Tested with real data                                                  │
│  ├── State files update correctly                                           │
│  └── Integration with workflows verified                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 6: SECURITY AUDIT                                                    │
│  ├── No hardcoded secrets                                                   │
│  ├── File permissions appropriate                                           │
│  └── Input validation in place                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### GitHub Actions

O workflow `verification.yml` executa automaticamente em cada PR:
- Level 1-3: Automático
- Level 4-6: Manual verification required

---

## 7. Merge

### Requisitos para Merge

- [ ] Issue vinculada
- [ ] 6 níveis de verificação passando
- [ ] Código revisado
- [ ] Conflitos resolvidos
- [ ] Branch atualizado com main

### Após Merge

1. Issue fecha automaticamente (`Fixes #XX`)
2. Branch pode ser deletado
3. GitHub Actions executa verificação final

---

## JARVIS Rules to Follow

### Regras Críticas

| Regra | Descrição |
|-------|-----------|
| #1 | Fases são bloqueantes |
| #8 | Logging dual-location obrigatório |
| #13 | Plan Mode para tarefas que modificam arquivos |
| #30 | GitHub Workflow obrigatório |

### Compounding Engineering

Erros repetidos viram regras permanentes:

```
Erro detectado → Análise → Nova regra no CLAUDE.md → Enforcement via hook
```

---

## Quick Reference

```bash
# 1. Criar branch
git checkout -b feat/issue-XX-description

# 2. Desenvolver com Claude (Plan Mode)
# ... implementação ...

# 3. Commit com referência
git commit -m "feat(scope): description

refs #XX"

# 4. Push
git push -u origin feat/issue-XX-description

# 5. Criar PR
gh pr create --title "[FEAT] Title" --body "Fixes #XX"

# 6. Aguardar verificação e merge
```

---

## Resources

- [Verification Levels](docs/VERIFICATION-LEVELS.md)
- [Plan Mode Protocol](docs/PLAN-MODE-PROTOCOL.md)
- [CLAUDE.md](CLAUDE.md) - Regras invioláveis
- [Issue Templates](.github/ISSUE_TEMPLATE/)
- [PR Template](.github/PULL_REQUEST_TEMPLATE.md)

---

> 🤖 This workflow is powered by JARVIS + Boris Cherny + Continuous Claude methodology.
