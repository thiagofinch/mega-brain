# MCP Governance Rules - Mega Brain

> **Versão:** 1.0.0
> **Criado:** 2026-02-18
> **Referência:** Constitution Article VI, ANTHROPIC-STANDARDS.md § 3
> **Escopo:** Governance de TODOS os MCP servers configurados no Mega Brain

---

## MCP Servers Configurados

Fonte: `.mcp.json`

| MCP Server | Package | Propósito | Owner |
|------------|---------|-----------|-------|
| **n8n-mcp** | `n8n-mcp` | Automação de workflows via n8n | @devops (system) |
| **clickup** | `@nazruden/clickup-server` | Gestão de tarefas e projetos | @jarvis (system) |
| **miro** | `@llmindset/mcp-miro` | Quadros visuais e brainstorming | @council |
| **figma-local** | `figma-developer-mcp` | Design assets e componentes | Uso manual |
| **notion** | `@notionhq/notion-mcp-server` | Knowledge base externa | @jarvis (system) |

---

## Regras de Uso

### Prioridade de Ferramentas

SEMPRE preferir ferramentas nativas do Claude Code sobre MCP:

| Tarefa | USE ISTO | NÃO ISTO |
|--------|----------|----------|
| Ler arquivos locais | `Read` tool | MCP |
| Escrever arquivos | `Write` / `Edit` tools | MCP |
| Executar comandos | `Bash` tool | MCP |
| Buscar arquivos | `Glob` tool | MCP |
| Buscar conteúdo | `Grep` tool | MCP |

### Quando Usar MCP

| MCP | Usar Quando | NÃO Usar Quando |
|-----|-------------|-----------------|
| **n8n-mcp** | Criar/executar/listar workflows no n8n | Automações simples que Bash resolve |
| **clickup** | Criar/atualizar/listar tasks no ClickUp | Gestão local de tarefas |
| **miro** | Criar boards visuais, brainstorming visual | Diagramas simples em markdown |
| **figma-local** | Extrair design tokens, inspecionar componentes | Leitura de arquivos locais |
| **notion** | Consultar/atualizar páginas no Notion | Documentação local |

---

## Segurança

### Credenciais (ANTHROPIC-STANDARDS § 3.1)

**REGRA:** NUNCA tokens em plaintext em `.mcp.json`.

**Status atual:** Todos os MCPs usam `${ENV_VAR}` syntax (correto).

| MCP | Variável de Ambiente | Localização |
|-----|---------------------|-------------|
| n8n-mcp | `N8N_API_URL`, `N8N_API_KEY` | Shell env |
| clickup | `CLICKUP_PERSONAL_TOKEN` | Shell env |
| miro | `MIRO_TOKEN` | Shell env (via args) |
| figma-local | `FIGMA_API_KEY` | Shell env (via args) |
| notion | `NOTION_TOKEN` | Shell env |

### Checklist de Segurança (por MCP)

```
[ ] Credenciais em variáveis de ambiente (não plaintext)
[ ] Escopo de acesso mínimo necessário (principle of least privilege)
[ ] Timeout configurado no hook que chama o MCP
[ ] Log de uso em sessions (quem usou, quando, para quê)
[ ] Rotação de tokens documentada
```

---

## Administração

### Quem Gerencia MCPs

**Owner:** @devops (system agent) — EXCLUSIVO

Outros agentes são CONSUMIDORES, não administradores.

| Operação | Quem Pode |
|----------|-----------|
| Adicionar novo MCP | @devops (com aprovação humana) |
| Remover MCP | @devops (com aprovação humana) |
| Atualizar credenciais | @devops |
| Listar MCPs ativos | Qualquer agente |
| Usar MCP | Agente com permissão (ver tabela acima) |

### Adicionando Novo MCP

1. Verificar se funcionalidade não é coberta por ferramentas nativas
2. Verificar ANTHROPIC-STANDARDS compliance (timeout, credenciais, error handling)
3. Adicionar em `.mcp.json` com `${ENV_VAR}` syntax
4. Documentar neste arquivo (tabela de MCPs + regras de uso)
5. Configurar variáveis de ambiente no shell

---

## Monitoramento

### Health Check

Verificar periodicamente:
- MCPs respondendo (não em timeout)
- Credenciais válidas (tokens não expirados)
- Uso dentro do esperado (sem chamadas excessivas)

### Anomalias

| Anomalia | Ação |
|----------|------|
| MCP em timeout recorrente | Verificar conexão, reiniciar se necessário |
| Token expirado | Rotacionar via @devops |
| Uso excessivo | Revisar se agente correto está usando |
| MCP não usado por 30+ dias | Considerar remoção |

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2026-02-18 | Criação: 5 MCPs documentados, security rules, admin procedures |
