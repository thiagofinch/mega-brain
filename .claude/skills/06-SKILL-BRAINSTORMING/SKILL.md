---
name: 06-SKILL-BRAINSTORMING
description: "Use ANTES de criar playbooks, estruturar agentes, ou modificar a arquitetura do Mega Brain. Explora intenção, requisitos e design antes da implementação."
---

> **Auto-Trigger:** Antes de criar playbooks, estruturar agentes, design de conhecimento
> **Keywords:** "brainstorm", "ideias", "ideação", "playbook", "design", "estrutura", "agentes", "arquitetura"
> **Prioridade:** MÉDIA

---

# Brainstorming para Mega Brain

## Overview

Transforma ideias em designs estruturados através de diálogo colaborativo. Usado para:
- Criar novos playbooks de vendas
- Estruturar novos agentes (SOUL, MEMORY, DNA)
- Redesenhar arquiteturas de conhecimento
- Planejar pipelines de processamento

**Anunciar no início:** "Estou usando a skill de brainstorming para explorar essa ideia."

## O Processo

**Entendendo a ideia:**
- Verificar o estado atual do projeto (arquivos, agentes existentes, SESSION-STATE)
- Fazer perguntas uma de cada vez para refinar a ideia
- Preferir múltipla escolha quando possível
- Foco: propósito, restrições, critérios de sucesso

**Explorando abordagens:**
- Propor 2-3 abordagens diferentes com trade-offs
- Apresentar opções conversacionalmente com recomendação
- Liderar com a opção recomendada e explicar o porquê

**Apresentando o design:**
- Quando entender o que será construído, apresentar o design
- Dividir em seções de 200-300 palavras
- Perguntar após cada seção se está correto até agora
- Cobrir: estrutura, componentes, fluxo de dados, integração com sistema existente

## Após o Design

**Documentação:**
- Escrever design validado em `knowledge/playbooks/drafts/YYYY-MM-DD-<topico>-design.md`
- Atualizar SESSION-STATE.md com novo design

**Implementação (se continuar):**
- Perguntar: "Pronto para implementar?"
- Para processamento de conteúdo: usar Pipeline Jarvis
- Para criação de agentes: seguir Agent Integrity Protocol

## Princípios Chave

- **Uma pergunta de cada vez** - Não sobrecarregar
- **Múltipla escolha preferida** - Mais fácil de responder
- **YAGNI** - Remover features desnecessárias
- **Explorar alternativas** - Sempre 2-3 abordagens
- **Validação incremental** - Apresentar em seções, validar cada uma
- **Ser flexível** - Voltar e clarificar quando necessário

## Quando Usar

| Situação | Usar? |
|----------|-------|
| Criar novo playbook de vendas | ✅ |
| Estruturar novo agente | ✅ |
| Redesenhar taxonomy de temas | ✅ |
| Planejar processamento em lote | ✅ |
| Processar arquivo simples | ❌ (usar Pipeline Jarvis direto) |
| Corrigir erro em arquivo | ❌ |
