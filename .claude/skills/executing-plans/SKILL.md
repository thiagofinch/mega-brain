---
name: 08-SKILL-EXECUTING-PLANS
description: Use quando tiver um plano de processamento para executar com checkpoints de revisão
---

> **Auto-Trigger:** Executar plano de processamento, implementar pipeline com checkpoints
> **Keywords:** "executar", "plano", "execução", "pipeline", "checkpoint", "batch", "jarvis"
> **Prioridade:** ALTA

---

# Executing Plans - Mega Brain

## Overview

Carrega plano, revisa criticamente, executa tarefas em batches, reporta para revisão entre batches.

**Princípio central:** Execução em batch com checkpoints para revisão do usuário.

**Anunciar no início:** "Estou usando a skill executing-plans para implementar este plano."

## O Processo

### Step 1: Carregar e Revisar Plano
1. Ler arquivo do plano (geralmente em `knowledge/playbooks/drafts/`)
2. Revisar criticamente - identificar questões ou preocupações
3. Se houver preocupações: Levantar antes de começar
4. Se ok: Criar TodoWrite e prosseguir

### Step 2: Executar Batch
**Default: Primeiras 3 tarefas**

Para cada tarefa:
1. Marcar como in_progress
2. Seguir cada passo exatamente
3. Executar verificações conforme especificado
4. Marcar como completed

### Step 3: Reportar
Quando batch completo:
```
┌─ BATCH N COMPLETO ─────────────────────────────────────────────────────┐
│                                                                         │
│  ✅ TAREFAS CONCLUÍDAS:                                                │
│  ├─ [Tarefa 1]: [resultado]                                            │
│  ├─ [Tarefa 2]: [resultado]                                            │
│  └─ [Tarefa 3]: [resultado]                                            │
│                                                                         │
│  📊 VERIFICAÇÕES:                                                       │
│  ├─ [verificação 1]: ✅                                                 │
│  └─ [verificação 2]: ✅                                                 │
│                                                                         │
│  Pronto para feedback.                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Step 4: Continuar
Baseado no feedback:
- Aplicar mudanças se necessário
- Executar próximo batch
- Repetir até completar

### Step 5: Completar Processamento

Após todas tarefas completas e verificadas:
- Atualizar SESSION-STATE.md
- Atualizar EVOLUTION-LOG.md se houve mudança estrutural
- Seguir regras de fim de sessão do CLAUDE.md

## Quando Parar e Pedir Ajuda

**PARAR execução imediatamente quando:**
- Encontrar blocker mid-batch (dependência faltando, verificação falha)
- Plano tem gaps críticos que impedem começar
- Não entender uma instrução
- Verificação falha repetidamente

**Pedir clarificação ao invés de adivinhar.**

## Contexto Mega Brain

### Tipos de Planos

| Tipo de Plano | Exemplo |
|---------------|---------|
| Processamento INBOX | "Processar 5 arquivos novos via Jarvis" |
| Criação de Agente | "Criar agente SALES-COORDINATOR" |
| Reestruturação | "Migrar THEMES para SOURCES" |
| Batch Council | "Deliberar 3 decisões estratégicas" |

### Integrações com Pipeline Jarvis

Ao executar planos de processamento:
- Steps 1.1-2.1: Podem rodar em paralelo (usar dispatching-parallel-agents)
- Steps 3.1-4.0: Consolidação (rodar sequencialmente)
- Steps 8.7-8.10: Finalização e logs inteligentes

### Checkpoints Obrigatórios

| Após Step | Checkpoint |
|-----------|------------|
| 2.1 (Insights) | Revisar insights extraídos |
| 4.0 (Dossiers) | Revisar dossiês gerados |
| 8.8 (Briefing) | Apresentar briefing executivo |

## Lembrar

- Revisar plano criticamente primeiro
- Seguir passos do plano exatamente
- Não pular verificações
- Entre batches: reportar e aguardar
- Parar quando bloqueado, não adivinhar
- Atualizar SESSION-STATE após completar
