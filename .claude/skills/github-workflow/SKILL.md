> **Auto-Trigger:** Quando usuário menciona GitHub, issues, PRs, branches, ou workflow de código
> **Keywords:** "github", "issue", "pull request", "pr", "branch", "merge", "commit", "workflow"
> **Prioridade:** ALTA
> **Tools:** Bash, Read, Write

---

# /github-workflow - Guia do Fluxo GitHub

## Propósito

Este skill guia o usuário através do fluxo GitHub obrigatório definido na **REGRA #30**.
Todo código modificado DEVE seguir este workflow: **Issue → Branch → PR → Merge**.

---

## Workflow Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GITHUB WORKFLOW OBRIGATÓRIO                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CRIAR ISSUE                                                             │
│     ├── Prefixo correto: [FEAT], [FIX], [REFACTOR], [DOCS]                 │
│     ├── Título descritivo                                                   │
│     └── Critérios de aceite claros                                         │
│                                                                             │
│  2. CRIAR BRANCH                                                            │
│     ├── Formato: tipo/issue-XX-descricao                                   │
│     ├── Exemplos:                                                          │
│     │   feat/issue-42-add-auth                                             │
│     │   fix/issue-15-memory-leak                                           │
│     │   refactor/issue-8-cleanup-hooks                                     │
│     └── git checkout -b tipo/issue-XX-desc                                 │
│                                                                             │
│  3. FAZER COMMITS                                                           │
│     ├── Mensagens descritivas                                              │
│     ├── Referência à issue: refs #XX                                       │
│     └── Exemplo: "Add auth module refs #42"                                │
│                                                                             │
│  4. ABRIR PULL REQUEST                                                      │
│     ├── Título claro                                                       │
│     ├── "Fixes #XX" no body (auto-fecha issue)                             │
│     ├── Checklist de 6 níveis de verificação                               │
│     └── Usar template: .github/PULL_REQUEST_TEMPLATE.md                    │
│                                                                             │
│  5. VERIFICAR (6 Níveis)                                                    │
│     ├── 1. Lint/Hooks                                                      │
│     ├── 2. Tests                                                           │
│     ├── 3. Build/Integrity                                                 │
│     ├── 4. Visual                                                          │
│     ├── 5. Staging                                                         │
│     └── 6. Security                                                        │
│                                                                             │
│  6. MERGE                                                                   │
│     └── Apenas após todos os níveis passarem                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Templates de Issue

### [FEAT] - Nova Funcionalidade
```bash
gh issue create --title "[FEAT] Descrição curta" --body "## Descrição
[Detalhe da feature]

## Critérios de Aceite
- [ ] Critério 1
- [ ] Critério 2

## Contexto JARVIS
- Fase: [X]
- Regras afetadas: [lista]"
```

### [FIX] - Correção de Bug
```bash
gh issue create --title "[FIX] Descrição do bug" --body "## Bug
[Descrição do problema]

## Reprodução
1. Passo 1
2. Passo 2

## Comportamento Esperado
[O que deveria acontecer]

## Logs/Screenshots
[Se aplicável]"
```

### [REFACTOR] - Refatoração
```bash
gh issue create --title "[REFACTOR] Área de refatoração" --body "## Objetivo
[Por que refatorar]

## Escopo
- Arquivos afetados: [lista]
- Impacto: [baixo/médio/alto]

## Abordagem
[Como será feito]"
```

---

## Comandos Úteis

### Criar Issue
```bash
gh issue create --title "[TIPO] Título" --label "tipo"
```

### Criar Branch
```bash
git checkout -b feat/issue-XX-descricao
```

### Abrir PR
```bash
gh pr create --title "Título do PR" --body "Fixes #XX

## Summary
- Change 1
- Change 2

## Verification Checklist
- [ ] 1. Hooks/Lint passed
- [ ] 2. Tests passed
- [ ] 3. Build successful
- [ ] 4. Visual verification
- [ ] 5. Staging tested
- [ ] 6. Security audit"
```

### Verificar Status
```bash
gh pr status
gh pr checks
```

---

## 6 Níveis de Verificação

| Nível | Nome | Comando | O que Verifica |
|-------|------|---------|----------------|
| 1 | Lint/Hooks | `pre-commit run --all` | Formatação, style |
| 2 | Tests | `pytest` / `npm test` | Testes automatizados |
| 3 | Build | `python -m py_compile **/*.py` | Integridade do código |
| 4 | Visual | Manual | Revisão visual do output |
| 5 | Staging | Deploy staging | Funciona em ambiente real |
| 6 | Security | `bandit` / manual | Vulnerabilidades |

---

## Quando NÃO Ativar

- Perguntas gerais sobre git (não sobre o workflow específico)
- Quando usuário já está no meio de um workflow e sabe o que fazer
- Consultas sobre histórico de commits sem intenção de modificar

---

## Regras Relacionadas

- **REGRA #30**: GitHub Workflow Obrigatório
- **REGRA #13**: Plan Mode para modificações
- **REGRA #8**: Logging obrigatório

---

## Exemplos de Uso

**Usuário:** "Como faço para criar uma issue de feature?"
**JARVIS:** [Ativa este skill, mostra template de issue FEAT]

**Usuário:** "Preciso fazer um PR para a issue #42"
**JARVIS:** [Ativa este skill, guia através do processo de PR]

**Usuário:** "Qual o workflow do GitHub?"
**JARVIS:** [Ativa este skill, mostra diagrama completo]

---

*Para verificação completa de 6 níveis, use `/verify-6-levels`*
