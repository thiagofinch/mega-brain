# AGENT AUTHORITY MATRIX - MEGA BRAIN

> **Versão:** 1.0.0
> **Criado:** 2026-02-18
> **Referência:** Constitution Article IV
> **Escopo:** Define domínios exclusivos e permissões de cada categoria de agente

---

## CATEGORIAS DE AGENTES

O Mega Brain organiza agentes em 5 categorias com domínios distintos:

```
agents/
├── persons/          ← PERSON agents (7): experts cujo conhecimento é extraído
├── cargo/            ← CARGO agents (5 dirs): posições funcionais
├── council/          ← COUNCIL agents (3): decisão coletiva
├── autonomous/       ← SYSTEM agents (4): operações automatizadas
├── sub-agents/       ← PIPELINE agents (4): sub-agentes do JARVIS
├── boardroom/        ← GOVERNANCE: sistema de decisão estratégica
├── sua-empresa/      ← ORG: organograma vivo
├── shared-memory/    ← SHARED: memória compartilhada entre agentes
├── discovery/        ← DISCOVERY: exploração de novos experts
├── constitution/     ← META: regras do próprio sistema de agentes
├── protocols/        ← META: protocolos operacionais dos agentes
├── _templates/       ← META: templates para criação de novos agentes
└── archive/          ← ARCHIVE: agentes desativados
```

---

## AUTHORITY MATRIX

### PERSON Agents


| Permissão | Pode? | Escopo |
|-----------|-------|--------|
| Ler knowledge base | SIM | `knowledge/` (global) |
| Escrever em próprio dossier | SIM | `knowledge/dossiers/persons/{slug}/` |
| Escrever em person memory | SIM | `.claude/agent-memory/{slug}/MEMORY.md` |
| Escrever em dossier alheio | NÃO | Violação de Source Isolation (Article II) |
| Modificar chunks | NÃO | Requer pipeline (Article I) |
| Decisões estratégicas | NÃO | Domínio do COUNCIL |

**Runtime Memory:** `.claude/agent-memory/{slug}/MEMORY.md`
**Definição:** `agents/persons/{slug}/`

---

### CARGO Agents

**Agentes:** closer, bdr, sales-manager, cro, cfo, coo, cmo (em `agents/cargo/`)

| Permissão | Pode? | Escopo |
|-----------|-------|--------|
| Ler knowledge base | SIM | `knowledge/` (global) |
| Ler dossiers de persons | SIM | Cross-reference para decisões |
| Escrever em cargo memory | SIM | `.claude/agent-memory/{cargo}/MEMORY.md` |
| Escrever em cargo dir | SIM | `agents/cargo/{cargo-group}/` |
| Modificar dossiers de persons | NÃO | Domínio do PERSON agent |
| Executar pipeline | NÃO | Domínio do PIPELINE |

**Runtime Memory:** `.claude/agent-memory/{cargo}/MEMORY.md`
**Definição:** `agents/cargo/{group}/{cargo}.md`

---

### COUNCIL Agents

**Agentes:** advogado-do-diabo, critico-metodologico, sintetizador

| Permissão | Pode? | Escopo |
|-----------|-------|--------|
| Ler TUDO | SIM | Acesso global de leitura |
| Facilitar debates | SIM | `agents/council/`, War Rooms |
| Registrar decisões | SIM | `agents/boardroom/outputs/` |
| Solicitar dados | SIM | Via PERSON/CARGO agents |
| Modificar dados diretamente | NÃO | Opinar sim, alterar não |
| Executar pipeline | NÃO | Domínio do PIPELINE |

**Runtime Memory:** `.claude/agent-memory/{council-agent}/MEMORY.md`
**Definição:** `agents/council/{agent}/`

---

### SYSTEM Agents (Autonomous)

**Agentes:** jarvis (orchestrator), pipeline-master, sentinel-org, devops

| Permissão | Pode? | Escopo |
|-----------|-------|--------|
| Executar pipeline | SIM | `processing/`, batch logs |
| Gerenciar state files | SIM | `.claude/jarvis/STATE.json` |
| Gerenciar logs | SIM | `logs/` |
| Gerenciar hooks | SIM | `.claude/hooks/` |
| Gerenciar MCP | SIM (devops only) | `.mcp.json` |
| Modificar knowledge | NÃO (apenas via pipeline) | Article I protege |
| Modificar agentes | NÃO | Domínio do META |

**Runtime Memory:** `.claude/agent-memory/{agent}/MEMORY.md`
**Definição:** `agents/autonomous/`, `agents/sub-agents/`

---

### PIPELINE Agents (Sub-agents do JARVIS)

**Agentes:** Definidos em `agents/sub-agents/` (critic, synthesizer, etc.)

| Permissão | Pode? | Escopo |
|-----------|-------|--------|
| Processar chunks | SIM | `processing/chunks/` |
| Extrair insights | SIM | `processing/insights/` |
| Gerar narrativas | SIM | `processing/narratives/` |
| Alimentar dossiers | SIM | Via `mission_feed.py` |
| Bypass enforcement | NÃO | Article I é NON-NEGOTIABLE |
| Decisões estratégicas | NÃO | Domínio do COUNCIL |

**Runtime Memory:** `.claude/agent-memory/{agent}/MEMORY.md`
**Definição:** `agents/sub-agents/`

---

## REGRAS DE INTERAÇÃO

### Delegação Obrigatória

| De | Para | Quando |
|----|------|--------|
| Qualquer agente | PIPELINE | Precisa processar novo material |
| Qualquer agente | COUNCIL | Decisão que afeta múltiplos domínios |
| PERSON agent | CARGO agent | Insight precisa virar ação prática |
| CARGO agent | PERSON agent | Precisa de referência teórica |
| Qualquer agente | DEVOPS (system) | Operações de infraestrutura |

### Conflitos

Quando dois agentes têm visões conflitantes:

1. **Mesmo domínio:** O agente mais específico prevalece (PERSON > genérico)
2. **Domínios diferentes:** Escalar para COUNCIL (debate)
3. **Constitution vs agente:** Constitution SEMPRE prevalece
4. **Dados vs opinião:** Dados prevalecem (Princípio do Empirismo)

---

## MEMORY ARCHITECTURE

### Separação Fundamental

```
DEFINIÇÃO (quem o agente É)          MEMÓRIA (o que o agente APRENDEU)
─────────────────────────────        ─────────────────────────────────
agents/persons/{slug}/               .claude/agent-memory/{slug}/MEMORY.md
agents/cargo/{group}/                .claude/agent-memory/{cargo}/MEMORY.md
agents/council/{agent}/              .claude/agent-memory/{agent}/MEMORY.md
agents/autonomous/{agent}.md         .claude/agent-memory/{agent}/MEMORY.md
agents/sub-agents/{agent}.md         .claude/agent-memory/{agent}/MEMORY.md
```

**REGRA:** Definição e Memória NUNCA se misturam.
- Definição: estática, versionada, descreve capacidades
- Memória: dinâmica, acumulativa, descreve experiência
- Hooks gerenciam o ciclo READ/WRITE automaticamente

### Lifecycle Hooks

| Hook | Evento | Ação |
|------|--------|------|
| `skill_router.py` | UserPromptSubmit | READ: Carrega MEMORY.md |
| `memory_hints_injector.py` | UserPromptSubmit | INJECT: Memory hints bracket-aware |
| `post_batch_cascading.py` | PostToolUse | WRITE: Persiste batch learnings |
| `agent_memory_persister.py` | SessionEnd | WRITE: Persiste resumo da sessão |

---

## SHARED RESOURCES

### Shared Memory (`agents/shared-memory/`)

| Arquivo | Propósito | Quem Escreve | Quem Lê |
|---------|-----------|--------------|---------|
| `ALERTS.yaml` | Alertas cross-domain | SYSTEM agents | TODOS |
| `CONTEXTS.yaml` | Contextos ativos | JARVIS | TODOS |
| `DECISIONS.yaml` | Decisões do Council | COUNCIL agents | TODOS |
| `QUEUE.yaml` | Fila de tarefas | JARVIS | PIPELINE agents |
| `STATES.yaml` | Estados dos agentes | SYSTEM agents | TODOS |
| `_INDEX.md` | Índice e descrição | META | TODOS |

### Boardroom (`agents/boardroom/`)

Usado para decisões estratégicas que envolvem múltiplos domínios.
- **Acesso de escrita:** COUNCIL agents + JARVIS
- **Acesso de leitura:** TODOS
- **Workflows:** `boardroom/workflows/`

---

## ENFORCEMENT

Violações de authority são tratadas conforme Constitution Article IV:

| Tipo | Severidade | Ação |
|------|-----------|------|
| Escrita cross-domain | WARNING | Log + notificação |
| Bypass de pipeline | BLOCK | Article I enforcement |
| Modificação de Constitution | BLOCK | Requer aprovação humana |
| Criação de agente sem template | WARNING | Sugestão de usar `_templates/` |

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2026-02-18 | Criação: 5 categorias, authority matrix, memory architecture |
