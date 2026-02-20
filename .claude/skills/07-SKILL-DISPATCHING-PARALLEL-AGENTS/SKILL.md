---
name: 07-SKILL-DISPATCHING-PARALLEL-AGENTS
description: Use quando tiver 2+ tarefas independentes que podem ser processadas em paralelo sem dependências
---

> **Auto-Trigger:** 2+ arquivos INBOX, múltiplos processamentos, paralelização de tarefas
> **Keywords:** "paralelo", "agents", "dispatch", "múltiplos", "batch", "concorrente", "INBOX"
> **Prioridade:** ALTA

---

# Dispatching Parallel Agents - Mega Brain

## Overview

Quando há múltiplos arquivos no INBOX ou tarefas independentes, processá-los sequencialmente desperdiça tempo. Cada processamento é independente e pode acontecer em paralelo.

**Princípio central:** Dispatch de um agente por domínio independente. Deixá-los trabalhar concorrentemente.

## Quando Usar

**Usar quando:**
- 3+ arquivos no INBOX de fontes diferentes
- Múltiplas extrações de conhecimento independentes
- Cada processamento pode ser entendido sem contexto dos outros
- Sem estado compartilhado entre investigações

**NÃO usar quando:**
- Arquivos são da mesma fonte (processar juntos para consistência)
- Precisa entender o estado completo do sistema
- Agentes interfeririam uns com os outros (editando mesmos arquivos)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DECISÃO: PARALELO OU SEQUENCIAL?                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Múltiplos arquivos? ──NO──→ Processo único                            │
│        │                                                                │
│       YES                                                               │
│        │                                                                │
│  São independentes? ──NO──→ Processar juntos (mesma fonte/tema)        │
│        │                                                                │
│       YES                                                               │
│        │                                                                │
│  ┌─────▼─────┐                                                         │
│  │ PARALLEL  │                                                         │
│  │ DISPATCH  │                                                         │
│  └───────────┘                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## O Padrão

### 1. Identificar Domínios Independentes

Agrupar por o que será processado:
- Arquivo A: Cole Gordon - Cole Gordon
- Arquivo B: Alex Hormozi - Alex Hormozi

Cada domínio é independente - processar Cole Gordon não afeta Hormozi.

### 2. Criar Tasks de Agente Focadas

Cada agente recebe:
- **Escopo específico:** Um arquivo ou fonte
- **Objetivo claro:** Extrair chunks e insights
- **Constraints:** Não modificar outros arquivos
- **Output esperado:** Resumo do que foi extraído

### 3. Dispatch em Paralelo

```
Task("Processar CG-SM002.txt via Pipeline Jarvis Steps 1-3")
Task("Processar AH-HR003.txt via Pipeline Jarvis Steps 1-3")
// Todos rodam concorrentemente
```

### 4. Revisar e Integrar

Quando agentes retornam:
- Ler cada resumo
- Verificar se não há conflitos em canonical/entities
- Rodar consolidação (Steps 4-6 do Jarvis)
- Integrar todos os outputs

## Estrutura do Prompt de Agente

```markdown
Processar arquivo: inbox/COLE GORDON/PODCASTS/CG-SM002.txt

Pipeline Jarvis Steps 1.1 a 2.1:
1. Chunking semântico → processing/chunks/
2. Entity Resolution → processing/canonical/
3. Insight Extraction → processing/insights/

Constraints:
- NÃO modificar arquivos de outras fontes
- Seguir protocolos existentes em agents/protocols/
- Atualizar INSIGHTS-STATE.json com novos insights

Retornar: Resumo de chunks gerados, entidades encontradas, insights extraídos.
```

## Erros Comuns

| ❌ Errado | ✅ Correto |
|-----------|-----------|
| "Processar todo o INBOX" | "Processar CG-SM002.txt" |
| Sem contexto do arquivo | Incluir path completo e fonte |
| Sem constraints | "NÃO modificar outros arquivos" |
| Output vago | "Retornar resumo de extrações" |

## Exemplo Real - Mega Brain

**Cenário:** 5 arquivos novos no INBOX de 3 fontes diferentes

**Arquivos:**
- Cole Gordon: CG-SM002.txt, CG-SM003.txt
- Alex Hormozi: AH-HR002.txt

**Decisão:**
- CG arquivos → 1 agente (mesma fonte)
- AH arquivo → 1 agente

**Dispatch:**
```
Agent 1 → Processar CG-SM002.txt + CG-SM003.txt
Agent 2 → Processar AH-HR002.txt
```

**Resultados:**
- Agent 1: 45 chunks, 23 insights sobre Sales Management
- Agent 2: 30 chunks, 18 insights sobre Hiring

**Integração:** Consolidar insights-state.json, rodar Steps 4-6

## Benefícios

1. **Paralelização** - Múltiplos processamentos simultâneos
2. **Foco** - Cada agente tem escopo narrow
3. **Independência** - Agentes não interferem
4. **Velocidade** - 3 problemas resolvidos no tempo de 1

## Verificação

Após agentes retornarem:
1. **Revisar cada resumo** - Entender o que foi extraído
2. **Checar conflitos** - Agentes editaram mesmos arquivos?
3. **Validar integridade** - JSONs de estado estão consistentes?
4. **Rodar consolidação** - Steps 4-6 do Pipeline Jarvis

---

## INTEGRACAO COM JARVIS_PARALLEL_DISPATCHER.PY

O sistema agora possui um dispatcher automatizado em `scripts/jarvis_parallel_dispatcher.py`.

### Uso Programatico

```python
import sys
sys.path.insert(0, "scripts")
from jarvis_parallel_dispatcher import get_dispatcher, analyze_for_parallelism

# Analisar prompt
analysis = analyze_for_parallelism("Processar proximos 3 batches")
# Retorna: {"can_parallelize": True, "reason": "Multiplos batches detectado"}

# Criar tarefas
dispatcher = get_dispatcher()
tasks = dispatcher.create_parallel_tasks(prompt, context)
commands = dispatcher.generate_task_commands(tasks)
```

### Logs Gerados

| Arquivo | Conteudo |
|---------|----------|
| `logs/dispatch.jsonl` | Acoes de dispatch |
| `system/active_parallel_tasks.json` | Tarefas ativas |
| `/tmp/claude/.../tasks/*.output` | Output de cada agente |

### Monitoramento

```bash
# Ver progresso de um agente
tail -50 /tmp/claude/<project-path>/tasks/[id].output

# Status de todas as tarefas
python scripts/jarvis_parallel_dispatcher.py
```
