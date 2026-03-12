# ANTHROPIC STANDARDS ENFORCEMENT

> **Versão:** 1.0.0
> **Criado:** 2026-01-14
> **Status:** ATIVO
> **Propósito:** Documento central de enforcement de boas práticas Anthropic

---

## VISÃO GERAL

Este documento define as regras OBRIGATÓRIAS para conformidade com as boas práticas oficiais da Anthropic para Claude Code. Toda criação ou modificação de hooks, skills, MCP configs, ou SDK sub-agents DEVE seguir estas regras.

---

## 1. REGRAS PARA HOOKS

### 1.1 Timeout Obrigatório

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGRA: Todo hook DEVE ter "timeout": 30                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✅ CORRETO:                                                                 │
│  {                                                                           │
│    "type": "command",                                                        │
│    "command": "python3 'script.py'",                                         │
│    "timeout": 30                                                             │
│  }                                                                           │
│                                                                              │
│  ❌ INCORRETO:                                                               │
│  {                                                                           │
│    "type": "command",                                                        │
│    "command": "python3 'script.py'"                                          │
│  }                                                                           │
│                                                                              │
│  MOTIVO: Previne hang do CLI se hook travar                                  │
│  VALOR: 30 segundos (padrão Anthropic recomendado)                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Error Handling (Exit Codes)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGRA: Usar exit codes apropriados, NÃO suprimir erros                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EXIT CODES:                                                                 │
│  ├── 0 = Sucesso (hook passou)                                               │
│  ├── 1 = Aviso (continua mas notifica)                                       │
│  └── 2 = Erro/Bloqueio (para execução)                                       │
│                                                                              │
│  ❌ EVITAR (padrão problemático):                                            │
│  "command": "script.py 2>/dev/null || true"                                  │
│                                                                              │
│  ✅ PREFERIR (tratamento adequado):                                          │
│  try:                                                                        │
│      # código                                                                │
│      sys.exit(0)  # sucesso                                                  │
│  except NonCriticalError:                                                    │
│      print(json.dumps({"warning": str(e)}))                                  │
│      sys.exit(1)  # aviso                                                    │
│  except CriticalError:                                                       │
│      print(json.dumps({"error": str(e)}))                                    │
│      sys.exit(2)  # bloqueio                                                 │
│                                                                              │
│  NOTA: 2>/dev/null || true pode ocultar bugs críticos                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Estrutura de Hook

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ESTRUTURA OBRIGATÓRIA DE HOOK:                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  {                                                                           │
│    "type": "command",           // OBRIGATÓRIO                               │
│    "command": "...",            // OBRIGATÓRIO                               │
│    "timeout": 30                // OBRIGATÓRIO (esta regra)                  │
│  }                                                                           │
│                                                                              │
│  LIFECYCLE EVENTS DISPONÍVEIS:                                               │
│  ├── PreToolUse      → Antes de executar ferramenta                          │
│  ├── PostToolUse     → Após executar ferramenta                              │
│  ├── UserPromptSubmit→ Quando usuário envia mensagem                         │
│  ├── SessionStart    → Início de sessão                                      │
│  ├── Stop            → Fim de sessão                                         │
│  ├── Notification    → Eventos de notificação                                │
│  └── SubagentStop    → Quando sub-agente termina                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. REGRAS PARA SKILLS

### 2.1 Header Obrigatório

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGRA: Todo SKILL.md DEVE ter header padronizado                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  HEADER OBRIGATÓRIO (primeiras linhas):                                      │
│                                                                              │
│  > **Auto-Trigger:** [Quando ativar automaticamente]                         │
│  > **Keywords:** "keyword1", "keyword2", "keyword3"                          │
│  > **Prioridade:** [ALTA | MÉDIA | BAIXA]                                    │
│  > **Tools:** [Lista de tools que a skill usa]                               │
│                                                                              │
│  SEÇÃO OBRIGATÓRIA "Quando NÃO Ativar":                                      │
│                                                                              │
│  ## Quando NÃO Ativar                                                        │
│  - [Situação 1 onde NÃO usar]                                                │
│  - [Situação 2 onde NÃO usar]                                                │
│                                                                              │
│  MOTIVO: Permite auto-routing via skill_router.py                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Estrutura de Skill

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ESTRUTURA DE DIRETÓRIO:                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  /.claude/skills/                                                            │
│  └── [nome-da-skill]/                                                        │
│      ├── SKILL.md           ← Instruções (OBRIGATÓRIO)                       │
│      ├── README.md          ← Documentação (opcional)                        │
│      └── [recursos]/        ← Scripts, templates (opcional)                  │
│                                                                              │
│  SEÇÕES OBRIGATÓRIAS NO SKILL.md:                                            │
│  1. Header com Auto-Trigger, Keywords, Prioridade, Tools                     │
│  2. Descrição do propósito                                                   │
│  3. Instruções de uso                                                        │
│  4. "Quando NÃO Ativar"                                                      │
│  5. Exemplos de uso                                                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. REGRAS PARA MCP (Model Context Protocol)

### 3.1 Credenciais Seguras

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGRA: NUNCA tokens em plaintext em configurações                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ❌ PROIBIDO (exposição de credenciais):                                     │
│  "env": {                                                                    │
│    "API_KEY": "sk-1234567890abcdef..."                                       │
│  }                                                                           │
│                                                                              │
│  ✅ CORRETO (variáveis de ambiente):                                         │
│  "env": {}                                                                   │
│                                                                              │
│  Com credenciais em ~/.zshrc ou ~/.bashrc:                                   │
│  export API_KEY="sk-1234567890abcdef..."                                     │
│                                                                              │
│  CREDENCIAIS SENSÍVEIS:                                                      │
│  ├── API keys (N8N, OpenAI, Anthropic, etc.)                                 │
│  ├── Tokens de acesso (ClickUp, Miro, Notion, etc.)                          │
│  ├── Secrets e passwords                                                     │
│  └── Qualquer string que dê acesso a recursos                                │
│                                                                              │
│  MOTIVO: settings.local.json pode ser commitado ou vazado                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Estrutura de MCP Server

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ESTRUTURA PADRÃO:                                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  "mcpServers": {                                                             │
│    "nome-do-servidor": {                                                     │
│      "command": "npx",          // ou caminho do executável                  │
│      "args": [                                                               │
│        "-y",                                                                 │
│        "@org/mcp-server-name"                                                │
│      ],                                                                      │
│      "env": {}                  // VAZIO - usar env vars do shell            │
│    }                                                                         │
│  }                                                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. REGRAS PARA SDK SUB-AGENTS

### 4.1 Princípio de Menor Privilégio

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGRA: Sub-agents DEVEM ter allowedTools e maxTurns explícitos              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CONFIGURAÇÕES OBRIGATÓRIAS:                                                 │
│  {                                                                           │
│    "allowedTools": ["Tool1", "Tool2"],  // Lista explícita                   │
│    "maxTurns": 15                        // Limite de iterações              │
│  }                                                                           │
│                                                                              │
│  NÍVEIS DE ACESSO RECOMENDADOS:                                              │
│                                                                              │
│  ANALYZER (leitura apenas):                                                  │
│  allowedTools: ["Read", "Glob", "Grep"]                                      │
│  maxTurns: 15                                                                │
│                                                                              │
│  RESEARCHER (leitura + web):                                                 │
│  allowedTools: ["Read", "Glob", "Grep", "WebFetch", "WebSearch"]             │
│  maxTurns: 20                                                                │
│                                                                              │
│  WRITER (leitura + escrita):                                                 │
│  allowedTools: ["Read", "Glob", "Grep", "Write", "Edit"]                     │
│  maxTurns: 25                                                                │
│                                                                              │
│  EXECUTOR (leitura + escrita + bash):                                        │
│  allowedTools: ["Read", "Glob", "Grep", "Write", "Edit", "Bash"]             │
│  maxTurns: 30                                                                │
│                                                                              │
│  ❌ NUNCA:                                                                   │
│  allowedTools: ["*"]  // Acesso total é proibido                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Estrutura de Sub-Agent

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  LOCALIZAÇÃO E ESTRUTURA:                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  /.claude/jarvis/sub-agents/                                                 │
│  └── [NOME-DO-SUBAGENT]/                                                     │
│      ├── AGENT.md           ← Definição (OBRIGATÓRIO)                        │
│      ├── SOUL.md            ← Personalidade (OBRIGATÓRIO)                    │
│      └── CONFIG.yaml        ← Configurações (opcional)                       │
│                                                                              │
│  HEADER OBRIGATÓRIO NO AGENT.md:                                             │
│                                                                              │
│  > **Auto-Trigger:** [Quando ativar]                                         │
│  > **Keywords:** "keyword1", "keyword2"                                      │
│  > **Prioridade:** [ALTA | MÉDIA | BAIXA]                                    │
│  > **allowedTools:** ["Tool1", "Tool2"]                                      │
│  > **maxTurns:** [número]                                                    │
│                                                                              │
│  NOTA: Sub-agents são "súbditos" do JARVIS, diferentes dos                   │
│        agents em /agents/ que são para o Council                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. REGRAS PARA PERMISSIONS

### 5.1 Deny List Obrigatória

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGRA: Configurar deny list para comandos perigosos                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DENY LIST MÍNIMA OBRIGATÓRIA:                                               │
│                                                                              │
│  "deny": [                                                                   │
│    // Comandos destrutivos                                                   │
│    "Bash(rm:-rf *)",                                                         │
│    "Bash(rm:* -rf *)",                                                       │
│                                                                              │
│    // Downloads externos (risco de código malicioso)                         │
│    "Bash(curl:*)",                                                           │
│    "Bash(wget:*)",                                                           │
│                                                                              │
│    // Arquivos sensíveis - SSH                                               │
│    "Read(~/.ssh/*)",                                                         │
│    "Write(~/.ssh/*)",                                                        │
│    "Edit(~/.ssh/*)",                                                         │
│                                                                              │
│    // Arquivos sensíveis - Environment                                       │
│    "Read(*.env)",                                                            │
│    "Write(*.env)",                                                           │
│    "Edit(*.env)",                                                            │
│    "Read(*/.env)",                                                           │
│    "Write(*/.env)",                                                          │
│    "Edit(*/.env)"                                                            │
│  ]                                                                           │
│                                                                              │
│  MOTIVO: Protege contra execução acidental de comandos perigosos             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. CHECKLIST DE VALIDAÇÃO

### 6.1 Ao Criar Hook

```
[ ] Tem "timeout": 30?
[ ] Error handling com exit codes (0, 1, 2)?
[ ] Evita 2>/dev/null || true?
[ ] Registrado em settings.local.json?
[ ] Testado isoladamente?
```

### 6.2 Ao Criar Skill

```
[ ] Header com Auto-Trigger, Keywords, Prioridade, Tools?
[ ] Seção "Quando NÃO Ativar"?
[ ] Estrutura de diretório correta?
[ ] Instruções claras de uso?
[ ] Exemplos incluídos?
```

### 6.3 Ao Criar/Modificar MCP Config

```
[ ] Nenhum token em plaintext?
[ ] Credenciais em variáveis de ambiente?
[ ] env: {} vazio no settings.local.json?
[ ] ~/.zshrc atualizado com exports?
```

### 6.4 Ao Criar Sub-Agent

```
[ ] allowedTools explícito (não ["*"])?
[ ] maxTurns definido?
[ ] Header com Keywords para auto-routing?
[ ] AGENT.md + SOUL.md presentes?
[ ] Localizado em /.claude/jarvis/sub-agents/?
```

---

## 7. REFERÊNCIAS

- **Boas Práticas Anthropic:** https://docs.anthropic.com/claude-code
- **Hook Lifecycle:** settings.local.json → hooks
- **MCP Protocol:** https://modelcontextprotocol.io
- **REGRA #27:** Auto-routing de skills e sub-agents
- **REGRA #28:** Ativação visível obrigatória

---

## 8. ENFORCEMENT AUTOMÁTICO

Este documento é referenciado por:

1. **creation_validator.py** (PreToolUse) - Valida criações
2. **quality_watchdog.py** - Detecta não-conformidades
3. **CLAUDE.md** - Referência @.claude/rules/ANTHROPIC-STANDARDS.md

Qualquer criação de hook, skill, MCP config, ou sub-agent que viole estas regras será AVISADA (warn, not block) pelo sistema de validação.

---

**FIM DO DOCUMENTO**

*Consider it done, senhor.*
