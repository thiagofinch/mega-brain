---
name: 09-SKILL-WRITING-PLANS
description: Use quando tiver spec ou requirements para tarefa multi-step, antes de executar
---

> **Auto-Trigger:** Spec ou requirements para tarefa multi-step, antes de executar
> **Keywords:** "plano", "planejamento", "planning", "escrever", "spec", "requirements"
> **Prioridade:** MÉDIA

---

# Writing Plans - Mega Brain

## Overview

Escreve planos de implementação compreensivos assumindo que o executor tem zero contexto sobre o projeto. Documenta tudo que precisa saber: quais arquivos tocar, passos exatos, verificações, como testar.

**Anunciar no início:** "Estou usando a skill writing-plans para criar o plano de implementação."

**Salvar planos em:** `knowledge/playbooks/drafts/YYYY-MM-DD-<nome-feature>.md`

## Granularidade de Tasks

**Cada passo é uma ação (2-5 minutos):**
- "Verificar arquivos no INBOX" - step
- "Rodar Jarvis Step 1.1" - step
- "Verificar chunks gerados" - step
- "Rodar Jarvis Step 2.1" - step
- "Verificar insights" - step

## Header do Plano

**Todo plano DEVE começar com:**

```markdown
# [Nome da Feature] - Plano de Implementação

**Objetivo:** [Uma frase descrevendo o que será construído]

**Arquitetura:** [2-3 frases sobre a abordagem]

**Dependências:** [Protocolos, arquivos, skills necessárias]

---
```

## Estrutura de Task

```markdown
### Task N: [Nome do Componente]

**Arquivos:**
- Criar: `path/exato/arquivo.md`
- Modificar: `path/exato/existente.json`
- Verificar: `path/exato/output/`

**Step 1: Verificar pré-condições**

- Checar se `inbox/` tem arquivos pendentes
- Verificar SESSION-STATE.md

**Step 2: Executar processamento**

```bash
# Comando exato ou descrição da ação
```

**Step 3: Verificar output**

- Checar se chunks foram gerados
- Validar JSON de estado

**Step 4: Atualizar registros**

- Atualizar SESSION-STATE.md
- Marcar arquivo como processado
```

## Tipos de Planos Mega Brain

### 1. Plano de Processamento INBOX

```markdown
### Task 1: Scan INBOX

**Arquivos:**
- Input: `inbox/**/*.txt`
- Output: Lista de arquivos pendentes

**Step 1:** Listar arquivos não processados
**Step 2:** Categorizar por fonte (Hormozi, Cole Gordon, etc.)
**Step 3:** Priorizar por relevância

---

### Task 2: Processar [ARQUIVO]

**Arquivos:**
- Input: `inbox/[PATH]/arquivo.txt`
- Output: `processing/chunks/[ID].json`

**Step 1:** Rodar Jarvis Step 1.1 (Chunking)
**Step 2:** Verificar chunks gerados
**Step 3:** Rodar Jarvis Step 2.1 (Insights)
**Step 4:** Verificar insights extraídos
```

### 2. Plano de Criação de Agente

```markdown
### Task 1: Definir SOUL

**Arquivos:**
- Criar: `agents/[AREA]/[CARGO]/SOUL.md`
- Referência: `agents/_TEMPLATES/SOUL-TEMPLATE.md`

**Step 1:** Copiar template
**Step 2:** Preencher dados do cargo
**Step 3:** Validar citações de fonte

---

### Task 2: Criar MEMORY

**Arquivos:**
- Criar: `agents/[AREA]/[CARGO]/MEMORY.md`
- Input: `knowledge/SOURCES/[PESSOA]/`

**Step 1:** Buscar insights relevantes
**Step 2:** Estruturar MEMORY com chunk_ids
**Step 3:** Validar rastreabilidade
```

### 3. Plano de Reestruturação

```markdown
### Task 1: Backup

**Arquivos:**
- Backup: `system/BACKUPS/YYYY-MM-DD/`

**Step 1:** Criar pasta de backup
**Step 2:** Copiar arquivos afetados
**Step 3:** Verificar backup completo

---

### Task 2: Migrar [COMPONENTE]

**Arquivos:**
- De: `[PATH_ANTIGO]/`
- Para: `[PATH_NOVO]/`

**Step 1:** Criar estrutura nova
**Step 2:** Mover arquivos
**Step 3:** Atualizar referências em CLAUDE.md
**Step 4:** Validar integridade
```

## Lembrar

- Paths exatos sempre
- Comandos completos no plano
- Cada step verificável
- Referenciar protocolos relevantes
- Incluir verificações após cada step

## Execution Handoff

Após salvar o plano, oferecer escolha:

**"Plano completo e salvo em `knowledge/playbooks/drafts/<filename>.md`. Duas opções:**

**1. Execução Subagente (esta sessão)** - Dispatch agente por task, review entre tasks

**2. Execução Direta (esta sessão)** - Executar tasks sequencialmente com checkpoints

**Qual abordagem?"**

**Se Execução Subagente:**
- Usar skill: dispatching-parallel-agents

**Se Execução Direta:**
- Usar skill: executing-plans
