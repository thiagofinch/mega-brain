# MCP Governance Rules - Mega Brain

> **Versão:** 1.0.0
> **Criado:** 2026-02-18
> **Referência:** Constitution Article VI, ANTHROPIC-STANDARDS.md § 3
> **Escopo:** Governance de TODOS os MCP servers configurados no Mega Brain

---

## MCP Servers Configurados

Fonte: `.mcp.json`

| MCP Server | Package | Propósito | Owner | Status |
|------------|---------|-----------|-------|--------|
| **mega-brain-knowledge** | `core.intelligence.rag.mcp_server` | RAG semântico local | @jarvis (system) | ATIVO |
| **n8n-mcp** | `n8n-mcp` | Automação de workflows via n8n | @devops (system) | ATIVO |
| **read-ai** | `mcp-remote` (OAuth) | Transcrições de reuniões via Read.ai | @jarvis (system) | ATIVO |
| ~~clickup~~ | ~~`@nazruden/clickup-server`~~ | ~~Gestão de tarefas~~ | — | REMOVIDO |
| ~~miro~~ | ~~`@llmindset/mcp-miro`~~ | ~~Quadros visuais~~ | — | REMOVIDO |
| ~~figma-local~~ | ~~`figma-developer-mcp`~~ | ~~Design assets~~ | — | REMOVIDO |
| ~~notion~~ | ~~`@notionhq/notion-mcp-server`~~ | ~~Knowledge base~~ | — | REMOVIDO |

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
| **mega-brain-knowledge** | Busca semântica no knowledge base (RAG) | Busca por nome de arquivo (usar Glob) |
| **n8n-mcp** | Criar/executar/listar workflows no n8n | Automações simples que Bash resolve |
| **read-ai** | Baixar transcrições de reuniões via API | Leitura de arquivos locais já baixados |

---

## Segurança

### Credenciais (ANTHROPIC-STANDARDS § 3.1)

**REGRA:** NUNCA tokens em plaintext em `.mcp.json`.

**Status atual:** Todos os MCPs usam `${ENV_VAR}` syntax (correto).

| MCP | Variável de Ambiente | Localização |
|-----|---------------------|-------------|
| mega-brain-knowledge | Nenhuma (local) | N/A |
| n8n-mcp | `N8N_API_URL`, `N8N_API_KEY` | Shell env |
| read-ai | OAuth token (via mcp-remote) | Gerenciado pelo MCP |

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
| 1.1.0 | 2026-03-11 | Atualizado: 3 MCPs ativos (mega-brain-knowledge, n8n, read-ai). Removidos: clickup, miro, figma-local, notion |
