# Workflow Claude Code - Boris Cherny + Continuous Claude

# **Template Universal** - Aplicável a qualquer projeto de desenvolvimento

> Este documento combina o melhor do Método Boris Cherny (criador do Claude Code @ Anthropic) com as práticas do Continuous Claude v3, criando um workflow completo e produtivo.
> 

---

# 🎯 Por Que Este Workflow?

## O Problema

O método Boris Cherny original é poderoso, mas foi criado para o contexto interno da Anthropic. Ao aplicá-lo em projetos reais, desenvolvedores enfrentam: **alto consumo de tokens** em sessões longas, **falta de análise de código estruturada**, **setup limitado ao macOS**, e **ausência de templates reutilizáveis**.

## A Solução

Este workflow evolui o método original com melhorias práticas testadas em produção:

**💰 Redução de Consumo de Tokens**

O sistema de Skills carrega conhecimento **sob demanda** via activation patterns. Em vez de manter todo o contexto o tempo todo, Claude ativa apenas o conhecimento necessário para cada tarefa. Resultado: sessões mais longas com menos tokens.

**🔍 Análise de Código Profunda**

Agentes especializados fazem **análise automática** de segurança, performance e qualidade antes de cada PR. Não é só lint e typecheck — é auditoria real com severidade classificada e recomendações acionáveis.

**⚡ 6 Níveis de Verificação vs 3**

Triplicamos os pontos de feedback: hooks automáticos, testes, build, verificação visual, staging e auditoria de segurança. Mais feedback = menos erros em produção.

**📦 Templates Prontos**

Comece a produzir em minutos com templates para componentes, hooks, API routes e estrutura de testes. Sem precisar reinventar padrões a cada projeto.

**🐧 Multiplataforma**

Setup funciona em macOS, Linux e WSL. Scripts de inicialização automatizados com tmux eliminam configuração manual.

**📖 Documentação de Troubleshooting**

Problemas comuns já estão mapeados com soluções testadas. Menos tempo debugando o workflow, mais tempo desenvolvendo.

---

# ⚡ O Que Mudou: Boris Original vs Este Workflow

Antes de mergulhar no conteúdo, entenda as **principais evoluções** deste workflow em relação ao método Boris Cherny original:

## Comparativo Rápido

| Aspecto | Boris Original | Este Workflow (v2.0) |
| --- | --- | --- |
| **Memória** | Apenas [CLAUDE.md](http://CLAUDE.md) | [CLAUDE.md](http://CLAUDE.md) + Skills modulares + Agents especializados |
| **Agentes** | Genéricos (verify-app, code-simplifier) | Expandidos com **security-audit** e **performance-checker** |
| **Conhecimento** | Regras no [CLAUDE.md](http://CLAUDE.md) | Sistema de **Skills** com activation patterns |
| **Setup** | iTerm2 com 5 abas | **tmux** com script automatizado + suporte Linux/WSL |
| **Verificação** | Build + Test + Lint | **6 níveis** incluindo E2E e verificação visual |
| **Templates** | Não inclusos | Templates completos para **componentes, hooks e API routes** |
| **Troubleshooting** | Não documentado | Seção completa com **problemas comuns e soluções** |
| **Universalidade** | Focado em stack específico | **Template genérico** adaptável a qualquer projeto |

## 🆕 Novidades Exclusivas

### 1. Sistema de Skills (do Continuous Claude)

```
Skills ≠ Agentes

• Agentes = Tarefas específicas (executam ações)
• Skills = Pacotes de conhecimento (informam decisões)
```

Skills incluem **activation patterns** - Claude sabe quando ativar cada conhecimento automaticamente.

### 2. Agentes de Segurança e Performance

Além dos agentes originais, adicionamos:

- [**security-audit.md**](http://security-audit.md): Checklist de vulnerabilidades com níveis de severidade
- [**performance-checker.md**](http://performance-checker.md): Análise de re-renders, memoization, bundle impact

### 3. Setup Multiplataforma

- **tmux** como alternativa ao iTerm2 (funciona em Linux/WSL)
- Script `claude-workspace` para inicialização automática
- Configuração de notificações cross-platform

### 4. Templates Prontos para Uso

- Componente React com TypeScript
- Custom Hook pattern
- API Route (Next.js App Router)
- Estrutura de testes

### 5. Verificação em 6 Níveis

```
Nível 1: Automático (Hooks) → Formatação, Lint, TypeCheck
Nível 2: Testes → Unit, Integration, E2E
Nível 3: Build → Compilação, Bundle analysis
Nível 4: Visual → Chrome extension, Storybook
Nível 5: Produção → Staging, Smoke tests, Monitoring
Nível 6: Segurança → Audit automatizado
```

### 6. Troubleshooting Documentado

Seção completa com:

- Problemas comuns e suas soluções
- Comandos de debug
- Dicas de otimização de contexto

## 🔄 O Que Mantivemos (Core do Boris)

✅ [**CLAUDE.md**](http://CLAUDE.md) como memória institucional - continua sendo o coração do sistema

✅ **Plan Mode obrigatório** - nunca executar sem plano aprovado

✅ **Múltiplos Claudes paralelos** - 5+ instâncias simultâneas

✅ **Compounding Engineering** - cada erro vira regra permanente

✅ **Verificação como multiplicador** - 2-3x qualidade com feedback loop

✅ **Slash commands** - /commit-push-pr, /code-simplifier, etc.

✅ **Integração GitHub** - @claude em PRs para atualizar [CLAUDE.md](http://CLAUDE.md)

---

# 📋 Índice

1. Visão Geral e Filosofia
2. Setup Inicial do Ambiente
3. Estrutura de Diretórios
4. [CLAUDE.md](http://CLAUDE.md) - Template Universal
5. Pipeline de Desenvolvimento (Plan → Execute → Verify)
6. Sistema de Agentes Especializados
7. Slash Commands Essenciais
8. Hooks e Automações
9. Skills do Continuous Claude
10. Integração GitHub e CI/CD
11. MCP Servers e Extensões
12. Verificação de Qualidade
13. Templates de Arquivos
14. Checklist de Implementação
15. Troubleshooting

---

# 1. Visão Geral e Filosofia

## 1.1 Conceito Central

O workflow combina duas abordagens poderosas:

**Boris Cherny Method**

- Múltiplos Claudes trabalhando em paralelo
- [CLAUDE.md](http://CLAUDE.md) como memória institucional
- Plan Mode obrigatório antes de execução
- Verificação como multiplicador de qualidade

**Continuous Claude v3**

- Skills modulares e reutilizáveis
- Agentes especializados por domínio
- Activation patterns inteligentes
- Self-improvement contínuo

## 1.2 Princípios Fundamentais

| Princípio | Boris | Continuous | Combinado |
| --- | --- | --- | --- |
| Paralelismo | 5-10 Claudes simultâneos | Agentes especializados | Multi-agent orchestration |
| Memória | [CLAUDE.md](http://CLAUDE.md) | Skills + Context | Memória hierárquica |
| Verificação | Tests + Build | Self-validation | Loop de feedback triplo |
| Aprendizado | Erros → Regras | Pattern recognition | Evolução contínua |

## 1.3 Modelo Mental

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (Você)                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│  │ Claude  │  │ Claude  │  │ Claude  │  │ Claude  │  │ Claude  ││
│  │  #1     │  │  #2     │  │  #3     │  │  #4     │  │  #5     ││
│  │ Feature │  │  Bugs   │  │  Docs   │  │  Tests  │  │ Explore ││
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘│
│       │            │            │            │            │     │
│       └────────────┴────────────┼────────────┴────────────┘     │
│                                 │                               │
│                    ┌────────────▼────────────┐                  │
│                    │      [CLAUDE.md](http://CLAUDE.md)          │                  │
│                    │   (Memória Compartilhada)│                  │
│                    └─────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## 1.4 Métricas de Sucesso

| Métrica | Baseline | Com Workflow |
| --- | --- | --- |
| PRs por dia | 2-3 | 10-20+ |
| Qualidade (rework) | 30% | 10% |
| Tempo para feature | 1-2 dias | 2-4 horas |
| Bugs em produção | Alto | Mínimo |

---

# 2. Setup Inicial do Ambiente

## 2.1 Requisitos

**Software Necessário**

```bash
# macOS
brew install --cask iterm2
brew install gh tmux

# Instalar Claude Code
npm install -g @anthropic/claude-code

# Autenticar
claude auth login
gh auth login
```

**Linux/WSL**

```bash
# Instalar tmux para múltiplas sessões
sudo apt install tmux gh

# Claude Code
npm install -g @anthropic/claude-code
```

## 2.2 Configuração do Terminal

**iTerm2 (Recomendado para Mac)**

```
iTerm2 → Settings → Profiles → Terminal
☑️ "Send notification when bell rings"
☑️ "Flash visual bell"
```

**tmux Configuration (~/.tmux.conf)**

```bash
# Habilitar mouse
set -g mouse on

# Prefixo mais fácil
set -g prefix C-a
unbind C-b
bind C-a send-prefix

# Split intuitivo
bind | split-window -h
bind - split-window -v

# Notificações
set -g visual-activity on
set -g visual-bell on

# Status bar informativa
set -g status-right '#(date +%H:%M) | #S'
```

## 2.3 Estrutura de Workspaces

```bash
# Criar workspace para múltiplos checkouts
mkdir -p ~/dev/PROJECT_NAME-workspace
cd ~/dev/PROJECT_NAME-workspace

# Clonar múltiplas cópias (uma por Claude)
git clone <repo-url> main      # Claude 1: Feature principal
git clone <repo-url> fixes     # Claude 2: Bug fixes
git clone <repo-url> docs      # Claude 3: Documentação
git clone <repo-url> tests     # Claude 4: Testes
git clone <repo-url> explore   # Claude 5: Exploração
```

## 2.4 Script de Inicialização

Criar `~/bin/claude-workspace`:

```bash
#!/bin/bash
# claude-workspace - Iniciar workspace com múltiplos Claudes

PROJECT=$1
WORKSPACE=~/dev/$PROJECT-workspace

if [ -z "$PROJECT" ]; then
    echo "Uso: claude-workspace <nome-projeto>"
    exit 1
fi

# Iniciar sessão tmux
tmux new-session -d -s $PROJECT -c $WORKSPACE/main

# Criar janelas para cada Claude
tmux new-window -t $PROJECT -n 'fixes' -c $WORKSPACE/fixes
tmux new-window -t $PROJECT -n 'docs' -c $WORKSPACE/docs
tmux new-window -t $PROJECT -n 'tests' -c $WORKSPACE/tests
tmux new-window -t $PROJECT -n 'explore' -c $WORKSPACE/explore

# Voltar para primeira janela
tmux select-window -t $PROJECT:0

# Anexar à sessão
tmux attach -t $PROJECT
```

---

# 3. Estrutura de Diretórios

## 3.1 Estrutura Padrão do Projeto

```
/seu-projeto/
├── .claude/
│   ├── settings.json          # Configurações do Claude Code
│   ├── commands/              # Slash commands customizados
│   │   ├── [commit-push-pr.md](http://commit-push-pr.md)
│   │   ├── [code-simplifier.md](http://code-simplifier.md)
│   │   ├── [test-and-fix.md](http://test-and-fix.md)
│   │   ├── [review-changes.md](http://review-changes.md)
│   │   └── [quick-commit.md](http://quick-commit.md)
│   ├── agents/                # Sub-agentes especializados
│   │   ├── [verify-app.md](http://verify-app.md)
│   │   ├── [performance-checker.md](http://performance-checker.md)
│   │   ├── [security-audit.md](http://security-audit.md)
│   │   └── [code-reviewer.md](http://code-reviewer.md)
│   └── skills/                # Skills do Continuous Claude
│       ├── [SKILL.md](http://SKILL.md)           # Índice de skills
│       ├── frontend/
│       ├── backend/
│       ├── testing/
│       └── devops/
├── [CLAUDE.md](http://CLAUDE.md)                  # Memória institucional (RAIZ)
├── docs/
│   └── guides/
│       └── [PIPELINE.md](http://PIPELINE.md)        # Guia detalhado do pipeline
└── ...
```

## 3.2 Arquivos Obrigatórios

| Arquivo | Propósito | Localização |
| --- | --- | --- |
| [CLAUDE.md](http://CLAUDE.md) | Memória compartilhada | Raiz do projeto |
| settings.json | Config do Claude Code | .claude/ |
| [commit-push-pr.md](http://commit-push-pr.md) | Workflow de commit | .claude/commands/ |
| [verify-app.md](http://verify-app.md) | Agente de verificação | .claude/agents/ |

---

# 4. [CLAUDE.md](http://CLAUDE.md) - Template Universal

## 4.1 Estrutura Recomendada

```markdown
# [NOME DO PROJETO] - Claude Code Guidelines

> Última atualização: [DATA]
> Versão: [X.Y.Z]

## 🎯 Visão do Projeto

[Descrição em 2-3 frases do que o projeto faz e seu objetivo principal]

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Runtime | Node/Bun/Python | X.Y.Z |
| Framework | Next.js/Django/etc | X.Y.Z |
| Database | PostgreSQL/MongoDB | X.Y.Z |
| ORM | Prisma/Drizzle/etc | X.Y.Z |

## 📦 Package Manager

- ✅ Sempre usar: `[bun/npm/pnpm/yarn]`
- ❌ Nunca usar: `[alternativas não permitidas]`

## 🔧 Comandos Principais

# Desenvolvimento

[pkg] run dev

# Build

[pkg] run build

# Testes

[pkg] run test

# Lint

[pkg] run lint

# Type check

[pkg] run typecheck

## 📁 Estrutura de Pastas

src/

├── app/          # [Descrição]

├── components/   # [Descrição]

├── lib/          # [Descrição]

├── hooks/        # [Descrição]

└── types/        # [Descrição]

## ✅ Regras de Código - FAZER

1. [Regra positiva 1]
2. [Regra positiva 2]
3. [Regra positiva 3]

## ❌ Regras de Código - NÃO FAZER

1. [Proibição 1 - motivo]
2. [Proibição 2 - motivo]
3. [Proibição 3 - motivo]

## 🎨 Padrões de Naming

| Tipo | Convenção | Exemplo |
|------|-----------|----------|
| Componentes | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase com use | `useAuth.ts` |
| Utils | camelCase | `formatDate.ts` |
| Types | PascalCase | `UserType.ts` |
| Constants | UPPER_SNAKE | `API_BASE_URL` |

## 🧪 Estratégia de Testes

- Unit tests: [Framework - Jest/Vitest]
- Integration: [Abordagem]
- E2E: [Framework - Playwright/Cypress]

## 🚀 Workflow de Deploy

1. Branch: `feature/xxx` → PR para `main`
2. CI: [Testes que rodam]
3. Deploy: [Ambiente e processo]

## 📝 Convenções de Commit

Formato: `tipo(escopo): descrição`

| Tipo | Uso |
|------|-----|
| feat | Nova funcionalidade |
| fix | Correção de bug |
| refactor | Refatoração |
| docs | Documentação |
| test | Testes |
| chore | Manutenção |

## 🐛 Erros Conhecidos e Soluções

### [Erro 1]
- **Problema**: [Descrição]
- **Solução**: [Como resolver]

### [Erro 2]
- **Problema**: [Descrição]
- **Solução**: [Como resolver]

## 📚 Padrões Aprendidos

<!-- Adicione aqui padrões descobertos durante o desenvolvimento -->

### [Data] - [Título]
- **Contexto**: [O que aconteceu]
- **Aprendizado**: [O que aprendemos]
- **Ação**: [Regra adicionada]

## 🔗 Links Úteis

- Repo: [URL]
- Docs: [URL]
- CI/CD: [URL]
- Monitoring: [URL]
```

## 4.2 Regra de Ouro do [CLAUDE.md](http://CLAUDE.md)

> **Toda vez que Claude comete um erro, adicione ao [CLAUDE.md](http://CLAUDE.md) para que não aconteça novamente.**
> 

Exemplos de adições:

```markdown
## ❌ Regras de Código - NÃO FAZER

4. Nunca criar componentes com mais de 200 linhas - dividir em subcomponentes
5. Nunca usar `any` em TypeScript - sempre tipar corretamente
6. Nunca commitar diretamente na main - sempre usar feature branches
```

---

# 5. Pipeline de Desenvolvimento

## 5.1 O Fluxo Completo: Plan → Execute → Verify

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLAN MODE (Obrigatório)                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. Descrever a tarefa com contexto completo             │    │
│  │ 2. Claude propõe plano detalhado                        │    │
│  │ 3. Revisar e iterar até aprovar                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                    EXECUTE (Auto-Accept)                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 4. Aprovar plano e mudar para auto-accept               │    │
│  │ 5. Claude executa todas as mudanças                     │    │
│  │ 6. Monitorar progresso (hooks formatam automaticamente) │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                    VERIFY (Triplo Feedback)                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 7. Build: npm run build (erros de compilação)           │    │
│  │ 8. Test: npm run test (regressões)                      │    │
│  │ 9. Lint: npm run lint (estilo e qualidade)              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                    SIMPLIFY & SHIP                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 10. /code-simplifier (limpar e otimizar)                │    │
│  │ 11. /commit-push-pr (criar PR automaticamente)          │    │
│  │ 12. Atualizar [CLAUDE.md](http://CLAUDE.md) se necessário                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 5.2 Plan Mode - Detalhado

**Entrar em Plan Mode:**

```
Shift + Tab (duas vezes)
```

**Template de Prompt para Planejar:**

```
## Contexto
[Descreva o estado atual do código/feature]

## Problema
[Descreva claramente o que precisa ser resolvido]

## Objetivo
[Liste os resultados esperados]

## Restrições
- [Limitação 1]
- [Limitação 2]

## Arquivos Relevantes
- src/path/to/file.ts
- src/path/to/another.ts

## Requisitos Técnicos
1. [Requisito 1]
2. [Requisito 2]
```

**Exemplo Real:**

```
## Contexto
O componente BlockEngine está lento ao carregar mais de 50 blocos.
Atualmente renderiza todos de uma vez.

## Problema  
Delay de 3 segundos no primeiro render.
Usuários reclamando de performance.

## Objetivo
1. Implementar lazy loading dos blocos
2. Adicionar virtualização para listas longas
3. Manter funcionalidade existente

## Restrições
- Não quebrar testes existentes
- Manter compatibilidade com API atual
- Bundle size não pode aumentar mais de 10KB

## Arquivos Relevantes
- src/components/BlockEngine.tsx
- src/hooks/useBlocks.ts
- src/types/block.ts

## Requisitos Técnicos
1. Usar react-window para virtualização
2. Implementar Intersection Observer
3. Adicionar skeleton loading
```

## 5.3 Verificação - A Regra Mais Importante

> "Provavelmente a coisa mais importante para ter ótimos resultados com Claude Code: **dê a Claude uma forma de verificar seu trabalho**. Se Claude tem esse feedback loop, vai 2-3x a qualidade do resultado final." — Boris Cherny
> 

**Níveis de Verificação:**

| Nível | Ferramenta | O que pega |
| --- | --- | --- |
| 1 | TypeScript | Erros de tipo |
| 2 | Lint | Estilo e padrões |
| 3 | Tests | Regressões |
| 4 | Build | Erros de compilação |
| 5 | E2E | Fluxos quebrados |
| 6 | Browser | UI/UX issues |

---

# 6. Sistema de Agentes Especializados

## 6.1 Conceito de Agentes

Agentes são "mini-Claudes" especializados em tarefas específicas. Cada agente tem:

- Escopo definido
- Checklist próprio
- Comandos específicos
- Critérios de sucesso

## 6.2 Agente: [verify-app.md](http://verify-app.md)

```markdown
# Agente de Verificação da Aplicação

Você é um agente especializado em verificar que a aplicação funciona corretamente.

## Checklist de Verificação

### 1. Build

npm run build 2>&1

- [ ] Deve completar sem erros
- [ ] Verificar warnings relevantes
- [ ] Bundle size dentro do limite

### 2. Testes

npm run test 2>&1

- [ ] Todos os testes devem passar
- [ ] Cobertura não deve diminuir
- [ ] Sem testes pulados sem motivo

### 3. Lint

npm run lint 2>&1

- [ ] Zero erros
- [ ] Warnings documentados

### 4. TypeScript

npm run typecheck 2>&1

- [ ] Zero erros de tipo
- [ ] Sem suppressions novos

### 5. Verificação Visual (se aplicável)
- [ ] Abrir em browser
- [ ] Testar fluxos principais
- [ ] Verificar responsividade

## Output Esperado

## Relatório de Verificação

### Build

✅ Passou | ❌ Falhou

[Detalhes se falhou]

### Testes

✅ X/Y passaram | ❌ X falhas

[Lista de falhas se houver]

### Lint

✅ Limpo | ⚠️ X warnings | ❌ X erros

[Detalhes relevantes]

### TypeScript

✅ Sem erros | ❌ X erros

[Detalhes se houver]

### Veredicto Final

✅ APROVADO - Pode fazer PR

❌ REPROVADO - [Motivo principal]
```

## 6.3 Agente: [code-simplifier.md](http://code-simplifier.md)

```markdown
# Agente Simplificador de Código

Você é um agente especializado em simplificar e melhorar código recém-escrito.

## Análise Inicial

git diff HEAD~1 --name-only

## Critérios de Simplificação

### 1. Duplicação
- Identificar código repetido
- Extrair para funções/hooks reutilizáveis
- DRY (Don't Repeat Yourself)

### 2. Complexidade
- Funções > 30 linhas → dividir
- Componentes > 150 linhas → dividir
- Nesting > 3 níveis → refatorar
- Cyclomatic complexity > 10 → simplificar

### 3. Naming
- Variáveis descritivas
- Funções indicam ação
- Sem abreviações obscuras
- Consistência com codebase

### 4. TypeScript
- Adicionar tipos específicos
- Remover `any` desnecessário
- Usar generics quando apropriado
- Inferência onde possível

### 5. Performance
- Identificar re-renders
- Sugerir memoization
- Verificar dependências de hooks
- Lazy loading onde apropriado

### 6. Limpeza
- Remover código comentado
- Remover imports não usados
- Remover variáveis mortas
- Remover console.logs

## Output

Para cada melhoria:
1. Mostrar código atual
2. Explicar o problema
3. Mostrar solução
4. Aplicar mudança
```

## 6.4 Agente: [security-audit.md](http://security-audit.md)

```markdown
# Agente de Auditoria de Segurança

Você é um agente especializado em identificar vulnerabilidades de segurança.

## Análise

git diff HEAD~1

## Checklist de Segurança

### 1. Injeção
- [ ] SQL Injection (queries parametrizadas?)
- [ ] XSS (sanitização de input?)
- [ ] Command Injection (shell seguro?)

### 2. Autenticação
- [ ] Tokens expostos em código?
- [ ] Senhas hardcoded?
- [ ] Sessions seguras?

### 3. Dados Sensíveis
- [ ] Logs sem dados sensíveis?
- [ ] Erros não expõem internals?
- [ ] PII protegida?

### 4. Dependências
- [ ] Versões seguras?
- [ ] Vulnerabilidades conhecidas?

### 5. Headers & CORS
- [ ] CORS configurado corretamente?
- [ ] Headers de segurança presentes?

## Severidade

| Nível | Ação |
|-------|------|
| 🔴 Critical | Bloquear PR |
| 🟠 High | Resolver antes do merge |
| 🟡 Medium | Resolver em 1 semana |
| 🟢 Low | Backlog |

## Output

## Relatório de Segurança

### Vulnerabilidades Encontradas

[Lista com severidade]

### Recomendações

[Ações específicas]

### Veredicto

✅ SEGURO | ⚠️ ATENÇÃO | ❌ BLOQUEADO

```

## 6.5 Agente: [performance-checker.md](http://performance-checker.md)

```markdown
# Agente de Performance

Você é um agente especializado em análise de performance.

## Análise

git diff HEAD~1 --name-only

## Verificações

### 1. Re-renders
- Componentes sem React.memo que deveriam ter
- Props que mudam referência desnecessariamente
- Context providers mal posicionados

### 2. Memoization
- useCallback para funções em props
- useMemo para cálculos pesados
- Dependências corretas nos arrays

### 3. Lazy Loading
- Componentes grandes → React.lazy
- Rotas → lazy loading
- Imports dinâmicos para features opcionais

### 4. Bundle Impact
- Novas dependências adicionadas
- Tree shaking funcionando
- Code splitting efetivo

### 5. Data Fetching
- Queries cacheadas
- Fetches não duplicados
- Sem waterfall de requests

## Métricas Alvo

| Métrica | Valor |
|---------|-------|
| LCP | < 2.5s |
| FID | < 100ms |
| CLS | < 0.1 |
| Bundle inicial | < 200KB |

## Output

## Relatório de Performance

### Issues Encontrados

[Lista com severidade e impacto]

### Recomendações

[Soluções específicas com código]

### Estimativa de Melhoria

[Ganhos esperados]

```

---

# 7. Slash Commands Essenciais

## 7.1 /[commit-push-pr.md](http://commit-push-pr.md)

O comando mais usado - dezenas de vezes por dia.

```markdown
# Commit, Push e Criar PR

Execute o fluxo completo de commit até PR.

## Coleta de Contexto

git status

git diff --stat

git branch --show-current

git log --oneline -3

## Instruções

### 1. Stage

git add -A

### 2. Commit
Analise as mudanças e crie mensagem seguindo Conventional Commits:
- Formato: `tipo(escopo): descrição`
- Tipos: feat, fix, refactor, docs, test, chore, perf
- Escopo: módulo/componente afetado
- Descrição: imperativo, lowercase, sem ponto final

Exemplos:
- `feat(auth): add social login with Google`
- `fix(blocks): resolve memory leak on unmount`
- `refactor(api): simplify error handling`

git commit -m "[mensagem gerada]"

### 3. Push

git push -u origin $(git branch --show-current)

### 4. Criar PR

gh pr create --fill

Se precisar de mais contexto:

gh pr create --title "[título]" --body "[descrição]"

## Output

## PR Criado ✅

**Link**: [URL do PR]

**Branch**: [nome]

**Commits**: [quantidade]

### Mudanças

[Resumo das alterações]
```

## 7.2 /[quick-commit.md](http://quick-commit.md)

```markdown
# Quick Commit

Commit rápido sem criar PR.

git status

git diff --stat

1. Stage mudanças relevantes
2. Criar commit com mensagem descritiva
3. NÃO fazer push

Use quando:
- Work in progress
- Checkpoint intermediário
- Múltiplos commits antes de PR
```

## 7.3 /[test-and-fix.md](http://test-and-fix.md)

```markdown
# Testar e Corrigir

Execute testes e corrija falhas automaticamente.

npm run test 2>&1

## Se houver falhas:

1. Analisar cada erro
2. Identificar causa raiz
3. Implementar correção
4. Re-executar testes
5. Repetir até todos passarem

## Se todos passarem:

✅ Todos os [X] testes passaram

## Output

## Resultado dos Testes

**Status**: ✅ Passou | ❌ [X] falhas

**Total**: [X] testes

**Duração**: [X]s

### Correções Aplicadas (se houver)

1. [Descrição da correção 1]
2. [Descrição da correção 2]
```

## 7.4 /[review-changes.md](http://review-changes.md)

```markdown
# Review de Mudanças

Faça code review das mudanças não commitadas.

git diff

## Critérios de Review

### 1. Correção
- O código faz o que deveria?
- Edge cases tratados?
- Erros handled?

### 2. Qualidade
- Segue padrões do projeto?
- Legível e manutenível?
- Bem documentado?

### 3. Performance
- Problemas óbvios?
- Complexidade adequada?

### 4. Segurança
- Vulnerabilidades?
- Dados expostos?

### 5. Testes
- Mudanças testadas?
- Cobertura adequada?

## Output

## Code Review

### Aprovação

✅ APROVADO | ⚠️ APROVADO COM RESSALVAS | ❌ MUDANÇAS NECESSÁRIAS

### Feedback

[Lista de observações]

### Sugestões de Melhoria

[Lista de sugestões opcionais]
```

## 7.5 /[init-project.md](http://init-project.md)

```markdown
# Inicializar Projeto para Claude Code

Configure um novo projeto com toda a estrutura necessária.

## Criar Estrutura

mkdir -p .claude/commands

mkdir -p .claude/agents

mkdir -p .claude/skills

## Criar Arquivos Base

1. Criar [CLAUDE.md](http://CLAUDE.md) com template padrão
2. Criar .claude/settings.json
3. Criar comandos essenciais
4. Criar agentes principais

## Verificar

ls -la .claude/

cat [CLAUDE.md]

## Output

✅ Projeto inicializado para Claude Code

Arquivos criados:

- [CLAUDE.md](http://CLAUDE.md)
- .claude/settings.json
- .claude/commands/[commit-push-pr.md]
- .claude/commands/[code-simplifier.md]
- .claude/agents/[verify-app.md]
```

---

# 8. Hooks e Automações

## 8.1 settings.json Completo

```json
{
  "model": "opus-4.5",
  "thinking": true,
  
  "permissions": {
    "allow": [
      "npm run *",
      "bun run *",
      "pnpm run *",
      "yarn *",
      "git status",
      "git diff *",
      "git add *",
      "git commit *",
      "git push *",
      "git pull",
      "git checkout *",
      "git branch *",
      "git log *",
      "gh pr *",
      "gh issue *",
      "cat *",
      "ls *",
      "tree *",
      "head *",
      "tail *",
      "grep *",
      "find *",
      "mkdir *",
      "touch *",
      "cp *",
      "mv *"
    ],
    "deny": [
      "rm -rf /",
      "rm -rf ~",
      "sudo *",
      "chmod 777 *",
      "curl * | sh",
      "wget * | sh"
    ]
  },
  
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run format --silent || true"
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "npm run lint --silent || true"
      }
    ],
    "PreCommit": [
      {
        "type": "command",
        "command": "npm run typecheck --silent"
      }
    ]
  },
  
  "context": {
    "include": [
      "[CLAUDE.md](http://CLAUDE.md)",
      "package.json",
      "tsconfig.json"
    ],
    "exclude": [
      "node_modules/**",
      "dist/**",
      ".git/**",
      "*.lock"
    ]
  }
}
```

## 8.2 Explicação dos Hooks

| Hook | Quando executa | Uso típico |
| --- | --- | --- |
| PostToolUse | Após Write/Edit | Formatação automática |
| Stop | Quando Claude para | Lint final |
| PreCommit | Antes de commit | Typecheck |
| PrePush | Antes de push | Testes |

## 8.3 Scripts de Package.json Recomendados

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "validate": "npm run typecheck && npm run lint && npm run test",
    "prepare": "husky install"
  }
}
```

---

# 9. Skills do Continuous Claude

## 9.1 Conceito de Skills

Skills são pacotes de conhecimento especializado que Claude pode "ativar" quando necessário. Diferente de agentes (que são tarefas), skills são conhecimentos.

## 9.2 Estrutura de um Skill

```markdown
# [NOME DO SKILL]

## Activation Patterns

Quando este skill deve ser ativado:
- [Pattern 1: palavras-chave ou contexto]
- [Pattern 2]
- [Pattern 3]

## Conhecimento Base

### [Área 1]
[Informações essenciais]

### [Área 2]
[Informações essenciais]

## Padrões e Templates

### Template 1: [Nome]

[template]

### Template 2: [Nome]

[template]

## Anti-Patterns

❌ [O que não fazer]
❌ [O que não fazer]

## Referências

- [Link para documentação]
- [Link para exemplos]
```

## 9.3 Skill: React/Next.js

```markdown
# React/Next.js Skill

## Activation Patterns

- Criação de componentes React
- Páginas Next.js
- Server Components vs Client Components
- App Router patterns

## Conhecimento Base

### Server vs Client Components

| Tipo | Quando usar | Marcação |
|------|-------------|----------|
| Server | Data fetching, acesso a DB | Default (sem marcação) |
| Client | Interatividade, hooks, eventos | 'use client' no topo |

### Padrões de Componente

// Server Component (default)

export default async function Page() {

const data = await fetchData()

return <Component data={data} />

}

// Client Component

'use client'

export function InteractiveComponent() {

const [state, setState] = useState()

return <button onClick={() => setState(...)}>...</button>

}

### File-based Routing (App Router)

app/

├── page.tsx           # /

├── about/page.tsx     # /about

├── blog/

│   ├── page.tsx       # /blog

│   └── [slug]/page.tsx # /blog/:slug

├── layout.tsx         # Layout compartilhado

├── loading.tsx        # Loading UI

├── error.tsx          # Error boundary

└── not-found.tsx      # 404

### Data Fetching Patterns

// Server Component - fetch direto

async function getData() {

const res = await fetch('https://api.example.com/data', {

cache: 'force-cache', // ou 'no-store', ou revalidate

})

return res.json()

}

// Client Component - SWR ou TanStack Query

'use client'

import useSWR from 'swr'

function Profile() {

const { data, error, isLoading } = useSWR('/api/user', fetcher)

// ...

}

## Anti-Patterns

❌ useState/useEffect em Server Components
❌ fetch sem tratamento de erro
❌ Props drilling excessivo (usar Context ou Zustand)
❌ Componentes com mais de 200 linhas
```

## 9.4 Skill: TypeScript

```markdown
# TypeScript Skill

## Activation Patterns

- Definição de tipos
- Generics
- Utility types
- Type guards

## Conhecimento Base

### Tipos Básicos

// Primitivos

type Primitive = string | number | boolean | null | undefined

// Arrays

type StringArray = string[]

type NumberArray = Array<number>

// Objects

interface User {

id: string

name: string

email?: string // opcional

readonly createdAt: Date // imutável

}

// Functions

type Handler = (event: Event) => void

type AsyncFetcher = <T>(url: string) => Promise<T>

### Utility Types

// Partial - todos opcionais

type PartialUser = Partial<User>

// Required - todos obrigatórios  

type RequiredUser = Required<User>

// Pick - selecionar propriedades

type UserPreview = Pick<User, 'id' | 'name'>

// Omit - excluir propriedades

type UserWithoutEmail = Omit<User, 'email'>

// Record - objeto com chaves tipadas

type UserMap = Record<string, User>

### Generics

// Função genérica

function first<T>(arr: T[]): T | undefined {

return arr[0]

}

// Interface genérica

interface Response<T> {

data: T

status: number

message: string

}

// Constraints

function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {

return obj[key]

}

### Type Guards

// Type predicate

function isUser(value: unknown): value is User {

return (

typeof value === 'object' &&

value !== null &&

'id' in value &&

'name' in value

)

}

// Discriminated unions

type Result<T> = 

| { success: true; data: T } |
| --- |
| { success: false; error: string } |

function handleResult<T>(result: Result<T>) {

if (result.success) {

// [result.data](http://result.data) é T aqui

} else {

// result.error é string aqui

}

}

## Anti-Patterns

❌ `any` - usar `unknown` e fazer type narrowing
❌ Type assertions desnecessárias (`as`)
❌ `@ts-ignore` sem comentário explicativo
❌ Tipos inline complexos (extrair para type/interface)
```

## 9.5 Skill: Testing

```markdown
# Testing Skill

## Activation Patterns

- Criar testes unitários
- Criar testes de integração
- Mocking
- Test coverage

## Conhecimento Base

### Estrutura de Teste (Vitest/Jest)

import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('ComponentName', () => {

beforeEach(() => {

// Setup antes de cada teste

})

it('should do something', () => {

// Arrange

const input = 'test'

// Act

const result = doSomething(input)

// Assert

expect(result).toBe('expected')

})

it('should handle edge case', () => {

expect(() => doSomething(null)).toThrow()

})

})

### Testing React Components

import { render, screen, fireEvent } from '@testing-library/react'

import { UserProfile } from './UserProfile'

describe('UserProfile', () => {

it('renders user name', () => {

render(<UserProfile user={{ name: 'John' }} />)

expect(screen.getByText('John')).toBeInTheDocument()

})

it('calls onEdit when button clicked', async () => {

const onEdit = vi.fn()

render(<UserProfile user={{ name: 'John' }} onEdit={onEdit} />)

[fireEvent.click](http://fireEvent.click)(screen.getByRole('button', { name: /edit/i }))

expect(onEdit).toHaveBeenCalledTimes(1)

})

})

### Mocking

// Mock de módulo

vi.mock('./api', () => ({

fetchUser: vi.fn().mockResolvedValue({ id: 1, name: 'John' })

}))

// Mock de função

const mockFn = vi.fn()

mockFn.mockReturnValue('value')

mockFn.mockResolvedValue('async value')

mockFn.mockImplementation((x) => x * 2)

// Verificar chamadas

expect(mockFn).toHaveBeenCalled()

expect(mockFn).toHaveBeenCalledWith('arg')

expect(mockFn).toHaveBeenCalledTimes(2)

## Padrões de Teste

| Tipo | Proporção | Foco |
|------|-----------|------|
| Unit | 70% | Funções isoladas |
| Integration | 20% | Módulos juntos |
| E2E | 10% | Fluxos completos |

## Anti-Patterns

❌ Testes que dependem de ordem de execução
❌ Testes com side effects compartilhados
❌ Mocking excessivo (testar implementação, não comportamento)
❌ Testes flaky (resultados inconsistentes)
```

---

# 10. Integração GitHub e CI/CD

## 10.1 GitHub Action para @claude

Instalar a action que permite mencionar @claude em PRs:

```bash
claude /install-github-action
```

## 10.2 Uso em Code Review

```
# Em um comentário de PR:

@claude adiciona ao [CLAUDE.md](http://CLAUDE.md) a regra:
"Nunca usar forEach para arrays grandes, preferir for...of"

# Claude vai:
# 1. Abrir [CLAUDE.md](http://CLAUDE.md)
# 2. Adicionar a regra na seção apropriada
# 3. Commitar a mudança no PR
```

## 10.3 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Type check
        run: npm run typecheck
      
      - name: Lint
        run: npm run lint
      
      - name: Test
        run: npm run test -- --coverage
      
      - name: Build
        run: npm run build
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        if: always()

  deploy-preview:
    needs: validate
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Deploy preview steps...
```

## 10.4 Compounding Engineering

Conceito de Dan Shipper: cada PR torna o time mais inteligente.

```
┌─────────────────────────────────────────────────────────────────┐
│                 COMPOUNDING ENGINEERING                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Erro identificado durante code review                      │
│                      ↓                                           │
│   2. @claude adiciona regra ao [CLAUDE.md](http://CLAUDE.md)                        │
│                      ↓                                           │
│   3. Todos os Claudes (e humanos) aprendem                      │
│                      ↓                                           │
│   4. Erro nunca mais acontece                                    │
│                      ↓                                           │
│   5. Qualidade do projeto aumenta continuamente                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# 11. MCP Servers e Extensões

## 11.1 Configuração do .mcp.json

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-slack"],
      "env": {
        "SLACK_TOKEN": "${SLACK_TOKEN}"
      }
    },
    "github": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "notion": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-notion"],
      "env": {
        "NOTION_TOKEN": "${NOTION_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "sentry": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-sentry"],
      "env": {
        "SENTRY_TOKEN": "${SENTRY_TOKEN}"
      }
    }
  }
}
```

## 11.2 Casos de Uso

| MCP Server | Uso |
| --- | --- |
| Slack | Buscar discussões, postar updates |
| GitHub | Criar issues, PRs, buscar código |
| Notion | Ler specs, atualizar docs |
| Postgres | Queries diretas, debug de dados |
| Sentry | Ver erros em produção |

## 11.3 Chrome Extension

Para testes visuais automatizados:

```bash
claude chrome install
```

Claude pode:

- Abrir o app no browser
- Testar UI visualmente
- Verificar UX
- Capturar screenshots

---

# 12. Verificação de Qualidade

## 12.1 Checklist de Qualidade

```markdown
## Pre-PR Checklist

### Código
- [ ] Build passa sem erros
- [ ] Todos os testes passam
- [ ] Lint sem erros
- [ ] TypeScript sem erros
- [ ] Sem console.logs
- [ ] Sem código comentado

### Funcionalidade
- [ ] Feature funciona como especificado
- [ ] Edge cases tratados
- [ ] Error handling adequado
- [ ] Loading states implementados

### Performance
- [ ] Sem re-renders desnecessários
- [ ] Bundle size aceitável
- [ ] Lazy loading onde apropriado

### Segurança
- [ ] Sem dados sensíveis expostos
- [ ] Input sanitizado
- [ ] Auth/authz verificado

### Documentação
- [ ] [CLAUDE.md](http://CLAUDE.md) atualizado se necessário
- [ ] Comentários em código complexo
- [ ] README atualizado se necessário
```

## 12.2 Níveis de Verificação

```
Nível 1: Automático (Hooks)
├── Formatação (Prettier)
├── Lint (ESLint)
└── Type check (TypeScript)

Nível 2: Testes
├── Unit tests
├── Integration tests
└── E2E tests (críticos)

Nível 3: Build
├── Compilação
├── Bundle analysis
└── Tree shaking

Nível 4: Visual (Opcional)
├── Chrome extension
├── Storybook
└── Visual regression

Nível 5: Produção
├── Staging deploy
├── Smoke tests
└── Monitoring
```

---

# 13. Templates de Arquivos

## 13.1 Template: Novo Componente React

```tsx
// src/components/[ComponentName]/[ComponentName].tsx
import { type FC } from 'react'
import { cn } from '@/lib/utils'
import type { [ComponentName]Props } from './types'

export const [ComponentName]: FC<[ComponentName]Props> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  )
}

[ComponentName].displayName = '[ComponentName]'

// src/components/[ComponentName]/types.ts
import type { HTMLAttributes, ReactNode } from 'react'

export interface [ComponentName]Props extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode
}

// src/components/[ComponentName]/index.ts
export { [ComponentName] } from './[ComponentName]'
export type { [ComponentName]Props } from './types'
```

## 13.2 Template: Novo Hook

```tsx
// src/hooks/use[HookName].ts
import { useState, useCallback, useEffect } from 'react'

interface Use[HookName]Options {
  // opções do hook
}

interface Use[HookName]Return {
  // retorno do hook
}

export function use[HookName](options: Use[HookName]Options = {}): Use[HookName]Return {
  const [state, setState] = useState()

  const handler = useCallback(() => {
    // lógica
  }, [])

  useEffect(() => {
    // side effects
    return () => {
      // cleanup
    }
  }, [])

  return {
    // retorno
  }
}
```

## 13.3 Template: API Route (Next.js)

```tsx
// app/api/[resource]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const RequestSchema = z.object({
  // validação
})

export async function GET(request: NextRequest) {
  try {
    // lógica
    return NextResponse.json({ data: result })
  } catch (error) {
    console.error('[API] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const validated = RequestSchema.parse(body)
    
    // lógica
    
    return NextResponse.json({ data: result }, { status: 201 })
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation error', details: error.errors },
        { status: 400 }
      )
    }
    console.error('[API] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

---

# 14. Checklist de Implementação

## Fase 1: Setup Básico (30 min)

- [ ]  Instalar iTerm2/tmux
- [ ]  Configurar notificações do terminal
- [ ]  Instalar Claude Code CLI
- [ ]  Autenticar gh e claude
- [ ]  Criar [CLAUDE.md](http://CLAUDE.md) na raiz do projeto
- [ ]  Criar estrutura .claude/

## Fase 2: Configuração (1 hora)

- [ ]  Criar .claude/settings.json
- [ ]  Criar /commit-push-pr command
- [ ]  Criar /code-simplifier command
- [ ]  Criar /test-and-fix command
- [ ]  Criar verify-app agent
- [ ]  Configurar hooks de formatação

## Fase 3: GitHub Integration (30 min)

- [ ]  Instalar GitHub Action (claude /install-github-action)
- [ ]  Testar @claude em um PR de teste
- [ ]  Configurar CI/CD workflow
- [ ]  Setup de branch protection rules

## Fase 4: Workspace Paralelo (30 min)

- [ ]  Criar workspace com múltiplos checkouts
- [ ]  Criar script claude-workspace
- [ ]  Testar 2-3 Claudes simultâneos
- [ ]  Configurar tmux/iTerm para workflow

## Fase 5: Prática Diária (Contínuo)

- [ ]  Usar Plan Mode consistentemente
- [ ]  Usar /commit-push-pr regularmente
- [ ]  Atualizar [CLAUDE.md](http://CLAUDE.md) a cada erro
- [ ]  Experimentar com mais sessões paralelas
- [ ]  Criar novos commands para workflows repetidos

## Fase 6: Otimização (Contínuo)

- [ ]  Adicionar skills específicos do projeto
- [ ]  Criar mais agents especializados
- [ ]  Adicionar MCP servers conforme necessário
- [ ]  Refinar [CLAUDE.md](http://CLAUDE.md) baseado em experiência
- [ ]  Documentar padrões descobertos

---

# 15. Troubleshooting

## 15.1 Problemas Comuns

### Claude não segue as regras do [CLAUDE.md](http://CLAUDE.md)

**Causa**: [CLAUDE.md](http://CLAUDE.md) muito longo ou mal estruturado.

**Solução**:

1. Manter [CLAUDE.md](http://CLAUDE.md) conciso (< 500 linhas)
2. Usar formatação clara com headers
3. Priorizar regras importantes no topo
4. Usar emojis para destaque visual

### Hooks não executam

**Causa**: settings.json mal configurado.

**Solução**:

```bash
# Verificar sintaxe
cat .claude/settings.json | python -m json.tool

# Verificar localização
ls -la .claude/
```

### PRs com conflitos frequentes

**Causa**: Múltiplos Claudes trabalhando nos mesmos arquivos.

**Solução**:

1. Dividir tarefas por módulo/pasta
2. Usar branches nomeadas claramente
3. Fazer merges frequentes da main
4. Comunicar escopo entre sessões

### Performance lenta do Claude

**Causa**: Contexto muito grande.

**Solução**:

1. Adicionar arquivos ao exclude no settings.json
2. Usar .gitignore efetivo
3. Limpar histórico de chat periodicamente
4. Iniciar novas sessões para tarefas diferentes

### Claude "esquece" instruções

**Causa**: Contexto excedido ou sessão muito longa.

**Solução**:

1. Referir ao [CLAUDE.md](http://CLAUDE.md) explicitamente
2. Iniciar nova sessão para tarefas longas
3. Usar Plan Mode para recontextualizar
4. Quebrar tarefas grandes em menores

## 15.2 Comandos de Debug

```bash
# Verificar status do Claude Code
claude --version
claude status

# Verificar autenticação
claude auth status
gh auth status

# Logs de debug
claude --debug

# Resetar configurações
claude config reset
```

---

# 📚 Referências

## Documentação Oficial

| Recurso | Link |
| --- | --- |
| Claude Code Docs | https://code.claude.com/docs |
| Slash Commands | https://code.claude.com/docs/en/slash-commands |
| Sub-agents | https://code.claude.com/docs/en/sub-agents |
| Hooks | https://code.claude.com/docs/en/hooks-guide |
| MCP Servers | https://code.claude.com/docs/en/mcp |

## Referências Externas

- Thread Original Boris Cherny: https://x.com/bcherny/
- Compounding Engineering (Dan Shipper)
- Continuous Claude v3: https://github.com/parcadei/Continuous-Claude-v3

---

# ✅ Conclusão

Este workflow combina o melhor de dois mundos:

**Do Boris Cherny:**

- Paralelismo com múltiplos Claudes
- [CLAUDE.md](http://CLAUDE.md) como memória institucional
- Plan Mode obrigatório
- Verificação como multiplicador de qualidade

**Do Continuous Claude:**

- Skills modulares e reutilizáveis
- Agents especializados
- Self-improvement contínuo
- Activation patterns inteligentes

**Resultado:**

Um desenvolvedor operando com a produtividade de um time inteiro, com qualidade consistente e aprendizado contínuo.

---

> **Versão**: 2.0
**Última atualização**: Janeiro 2026
**Autor**: Bruno Moreira - @zbrunomoreira
>