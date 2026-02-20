# Plan Mode Protocol

> **Quando e Como Usar Plan Mode no JARVIS**
> Protocolo completo para planejamento antes da execução.

---

## O Que É Plan Mode

Plan Mode é um estado especial onde o Claude:
- **Apenas lê e analisa** - não modifica arquivos
- **Cria um plano detalhado** - antes de executar
- **Aguarda aprovação** - do usuário antes de agir

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLAN MODE vs NORMAL MODE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   NORMAL MODE                         PLAN MODE                             │
│   ┌───────────┐                       ┌───────────┐                        │
│   │  Recebe   │                       │  Recebe   │                        │
│   │  Tarefa   │                       │  Tarefa   │                        │
│   └─────┬─────┘                       └─────┬─────┘                        │
│         │                                   │                              │
│         ▼                                   ▼                              │
│   ┌───────────┐                       ┌───────────┐                        │
│   │  Executa  │                       │  Analisa  │                        │
│   │ Diretamente│                      │   Lê      │                        │
│   └─────┬─────┘                       │ Pesquisa  │                        │
│         │                             └─────┬─────┘                        │
│         │                                   │                              │
│         │                                   ▼                              │
│         │                             ┌───────────┐                        │
│         │                             │   Cria    │                        │
│         │                             │   Plano   │                        │
│         │                             └─────┬─────┘                        │
│         │                                   │                              │
│         │                                   ▼                              │
│         │                             ┌───────────┐                        │
│         │                             │  Aguarda  │                        │
│         │                             │ Aprovação │                        │
│         │                             └─────┬─────┘                        │
│         │                                   │                              │
│         ▼                                   ▼                              │
│   ┌───────────┐                       ┌───────────┐                        │
│   │ Resultado │                       │  Executa  │                        │
│   └───────────┘                       │   (só com │                        │
│                                       │ aprovação)│                        │
│                                       └───────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quando Usar Plan Mode

### OBRIGATÓRIO (REGRA #13)

| Situação | Plan Mode? |
|----------|------------|
| Nova feature | ✅ **OBRIGATÓRIO** |
| Bug fix | ✅ **OBRIGATÓRIO** |
| Refatoração de código | ✅ **OBRIGATÓRIO** |
| Criação de agente | ✅ **OBRIGATÓRIO** |
| Processamento de batch grande (>10 arquivos) | ✅ **OBRIGATÓRIO** |
| Alteração em múltiplos arquivos | ✅ **OBRIGATÓRIO** |
| Qualquer tarefa > 30 minutos | ✅ **OBRIGATÓRIO** |
| Múltiplas abordagens possíveis | ✅ **OBRIGATÓRIO** |

### OPCIONAL (Pode Pular)

| Situação | Plan Mode? |
|----------|------------|
| Pergunta simples | ❌ Desnecessário |
| Status check | ❌ Desnecessário |
| Busca de informação | ❌ Desnecessário |
| Leitura de arquivo único | ❌ Desnecessário |
| Verificação rápida | ❌ Desnecessário |

---

## Como Ativar Plan Mode

### Método 1: Teclado

```
Shift+Tab → Shift+Tab (2x)
```

### Método 2: Comando

```
"Entre em plan mode"
"Vamos planejar primeiro"
"Plan this before executing"
```

### Método 3: Automático (Hook)

O hook `enforce_plan_mode.py` detecta keywords e sugere Plan Mode:

```python
# Keywords que ativam sugestão de Plan Mode:
modifying_keywords = [
    "criar", "atualizar", "modificar", "implementar",
    "adicionar", "remover", "refatorar", "corrigir",
    "create", "update", "modify", "implement",
    "add", "remove", "refactor", "fix"
]
```

---

## Fluxo do Plan Mode

### 1. Entrada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📋 PLAN MODE ACTIVATED                                                     │
│                                                                             │
│  Você está em modo de planejamento.                                         │
│  Ações permitidas: Read, Search, Analyze                                    │
│  Ações bloqueadas: Write, Edit, Delete                                      │
│                                                                             │
│  O plano será salvo em: /.claude/plans/[nome].md                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Análise

JARVIS executa:
- Leitura de arquivos relevantes
- Pesquisa de código existente
- Identificação de dependências
- Mapeamento de impacto

### 3. Criação do Plano

O plano inclui:

```markdown
# Plano: [Nome da Tarefa]

## Objetivo
[O que será feito]

## Análise
[O que foi descoberto durante análise]

## Arquivos Afetados
- [ ] arquivo1.py - Modificação
- [ ] arquivo2.md - Criação
- [ ] arquivo3.json - Atualização

## Dependências
- Requer: X
- Afeta: Y
- Cascateia para: Z

## Etapas
1. Primeiro passo
2. Segundo passo
3. Terceiro passo

## Riscos
- Risco 1: Mitigação
- Risco 2: Mitigação

## Verificação
- [ ] Level 1: Lint
- [ ] Level 2: Tests
- [ ] Level 3: Build
- [ ] Level 4: Visual
- [ ] Level 5: Staging
- [ ] Level 6: Security

## Status
AGUARDANDO APROVAÇÃO
```

### 4. Aprovação

JARVIS apresenta:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           PLANO PRONTO PARA REVISÃO                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Arquivos a criar:     3                                                    ║
║  Arquivos a modificar: 2                                                    ║
║  Cascateamentos:       4 destinos                                           ║
║                                                                              ║
║  Plano salvo em: /.claude/plans/rustling-stirring-rain.md                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Opções:                                                                    ║
║  [1] Aprovar e executar                                                     ║
║  [2] Solicitar ajustes                                                      ║
║  [3] Cancelar                                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 5. Execução

Após aprovação:
- Sai do Plan Mode
- Executa conforme plano aprovado
- Marca itens como completos
- Gera logs de execução

---

## Boas Práticas

### Refinamento Iterativo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NÃO fazer:                          FAZER:                                 │
│                                                                             │
│  Plano v1 → Executar                 Plano v1 → Revisar                    │
│                                            ↓                               │
│                                      Plano v2 → Revisar                    │
│                                            ↓                               │
│                                      Plano v3 → Aprovar → Executar         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Perguntas Obrigatórias

Antes de finalizar o plano, JARVIS pergunta:

```
"Algo mais que devo considerar antes de executar?"
"Há algum requisito que não mencionei?"
"Este plano cobre todas as suas necessidades?"
```

### Granularidade

| Tarefa | Plano |
|--------|-------|
| Pequena (1-2 arquivos) | Plano simples, 1 página |
| Média (3-5 arquivos) | Plano detalhado, 2-3 páginas |
| Grande (6+ arquivos) | Plano extenso, com sub-etapas |

---

## Template de Plano

```markdown
# PLANO: [Título]

## Metadata
- **Criado:** YYYY-MM-DD HH:MM
- **Autor:** JARVIS
- **Status:** AGUARDANDO APROVAÇÃO
- **Versão:** 1.0.0

---

## 1. OBJETIVO

[Descrição clara do que será feito]

---

## 2. ANÁLISE

### Contexto Atual
[Estado atual do sistema]

### Descobertas
[O que foi encontrado durante análise]

### Dependências
[O que precisa existir/funcionar]

---

## 3. ARQUIVOS

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| path/file1.py | CRIAR | Nova funcionalidade |
| path/file2.md | MODIFICAR | Adicionar seção |
| path/file3.json | ATUALIZAR | Novo campo |

---

## 4. ETAPAS

### Etapa 1: [Nome]
- [ ] Sub-tarefa 1.1
- [ ] Sub-tarefa 1.2

### Etapa 2: [Nome]
- [ ] Sub-tarefa 2.1
- [ ] Sub-tarefa 2.2

### Etapa 3: [Nome]
- [ ] Sub-tarefa 3.1
- [ ] Sub-tarefa 3.2

---

## 5. CASCATEAMENTOS

| Artefato | Destino | Impacto |
|----------|---------|---------|
| Framework X | Agent Y | +1 método |
| Metodologia Z | Dossier W | Atualização |

---

## 6. RISCOS

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Risco 1 | Baixa | Ação A |
| Risco 2 | Média | Ação B |

---

## 7. VERIFICAÇÃO

- [ ] Level 1: Hooks/Lint
- [ ] Level 2: Tests
- [ ] Level 3: Build
- [ ] Level 4: Visual
- [ ] Level 5: Staging
- [ ] Level 6: Security

---

## 8. APROVAÇÃO

**Status:** AGUARDANDO APROVAÇÃO

[ ] Aprovar e executar
[ ] Solicitar ajustes
[ ] Cancelar
```

---

## Comandos Úteis

| Comando | Ação |
|---------|------|
| `Shift+Tab 2x` | Entrar em Plan Mode |
| "Entre em plan mode" | Entrar em Plan Mode |
| "Mostre o plano" | Exibir plano atual |
| "Ajuste o plano" | Solicitar modificações |
| "Aprove o plano" | Aprovar para execução |
| "Cancele o plano" | Cancelar e sair |

---

## Integração com JARVIS

### Regra #13 (Atualizada)

```
PLAN MODE É OBRIGATÓRIO PARA QUALQUER TAREFA QUE MODIFIQUE ARQUIVOS.

Exceções (pode pular):
- Respostas informativas
- Buscas simples
- Status checks
```

### Hook de Enforcement

O hook `enforce_plan_mode.py` detecta automaticamente quando Plan Mode deveria
ser usado e sugere ativação.

---

> 🤖 Plan Mode economiza tempo no longo prazo.
> Plano ruim = Execução ruim = Retrabalho.
> Sempre refinar. Sempre confirmar.
