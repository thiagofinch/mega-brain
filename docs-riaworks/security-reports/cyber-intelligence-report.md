# CYBER INTELLIGENCE REPORT - Mega Brain
## Analise de Inteligencia Cibernetica (Ataque + Defesa)

**Data:** 2026-02-28
**Escopo:** Repositorio `mega-brain` - analise de runtime, HTTP trace, hooks, permissoes
**Metodo:** 4 agentes paralelos com analise de codigo-fonte (evidencia, nao suposicao)
**Complementa:** Auditoria estatica anterior (8 vetores, 1420 arquivos, nota B+)

---

## PERGUNTA CENTRAL - RESPOSTA

```
"Com este pacote instalado na minha maquina e minhas API keys
 configuradas no .env, existe ALGUM mecanismo pelo qual meus
 dados, credenciais ou informacoes do meu ambiente possam ser
 enviados para servidores externos sem meu conhecimento?"
```

### RESPOSTA: NAO para o pacote npm. SIM (parcial) para o ambiente de desenvolvimento.

**Para o USUARIO npm (npx mega-brain-ai):**
- `npm install` NAO executa nenhum codigo (zero lifecycle hooks)
- API keys vao APENAS para seus provedores originais (OpenAI, Voyage) durante validacao
- O unico dado enviado externamente e o EMAIL do usuario (para Supabase, no fluxo premium)
- Nenhum dado da maquina, ambiente ou filesystem e transmitido
- **VEREDICTO: SEGURO**

**Para o DESENVOLVEDOR (clone do repo + Claude Code):**
- 28 hooks Python executam automaticamente e tem acesso ao filesystem
- 1 hook JavaScript (`gsd-check-update.js`) faz acesso a rede
- `settings.local.json` concede permissoes excessivas (Bash irrestrito)
- Hooks podem injetar instrucoes no contexto de Claude via prompt injection por filesystem
- **VEREDICTO: RISCO MEDIO - mitigavel com as recomendacoes abaixo**

---

## ANGULO 1: COMO USUARIO (npx mega-brain-ai)

### 1.1 Trace de Execucao: npm install

```
COMANDO: npm install mega-brain-ai
RESULTADO: SEGURO

EVIDENCIA (package.json linhas 152-158):
  "scripts": {
    "start": "node bin/mega-brain.js",
    "prepublishOnly": "node bin/pre-publish-gate.js"
  }

  NAO EXISTE: preinstall, postinstall, prepare
  UNICO script automatico: prepublishOnly (roda no npm publish, NAO no install)

DEPENDENCIAS (5 total, todas conhecidas):
  chalk ^5.3.0, inquirer ^9.2.0, ora ^7.0.0, boxen ^7.1.0, gradient-string ^2.0.2
  Nenhuma dependencia suspeita ou de nicho.
```

### 1.2 Trace de Execucao: npx mega-brain-ai

```
ENTRY POINT: bin/cli.js -> bin/mega-brain.js

FLUXO:
1. Carrega .env local (se existir) via process.loadEnvFile()
2. Mostra banner ASCII
3. Se .env nao existe -> oferece setup wizard (interativo)
4. Roteia para subcomando (install, validate, push, setup, etc.)

CHAMADAS HTTP: ZERO neste arquivo
ACESSO A .env: Apenas leitura local (nao transmite)
```

### 1.3 Trace de Execucao: npx mega-brain-ai setup

```
ARQUIVO: bin/lib/setup-wizard.js

FLUXO:
1. Pede API keys via prompt interativo (inquirer)
2. Valida OpenAI key -> GET https://api.openai.com/v1/models (so header Auth)
3. Valida Voyage key -> POST https://api.voyageai.com/v1/embeddings (payload: ["test"])
4. Escreve .env LOCAL com as chaves
5. Instala PyYAML via pip

DADOS ENVIADOS: Apenas as API keys para seus PROPRIOS provedores
DADOS NAO ENVIADOS: Nenhum dado da maquina, filesystem, ou ambiente
OPT-IN: SIM - usuario digita as keys manualmente
```

### 1.4 Trace de Todas as Chamadas HTTP

| # | Endpoint | Arquivo | Dados Enviados | Opt-In | Risco |
|---|----------|---------|----------------|--------|-------|
| 1 | Supabase RPC `validate_buyer_email` | validate-email.js:48 | `{ buyer_email: "..." }` (so email) | SIM | LOW |
| 2 | OpenAI `/v1/models` | setup-wizard.js:287 | Header Auth com key do usuario | SIM | NONE |
| 3 | Voyage `/v1/embeddings` | setup-wizard.js:318 | Key + `["test"]` | SIM | NONE |
| 4 | GitHub git clone (premium) | installer.js:373 | Token efemero do Supabase | SIM | LOW |
| 5 | npm registry (versao GSD) | gsd-check-update.js:45 | Nome do pacote apenas | SEMI | NONE |

**Total: 5 chamadas HTTP em todo o codebase. Zero telemetria, zero analytics, zero tracking.**

### 1.5 Analise do Supabase

```
ENDPOINT: ${SUPABASE_URL}/rest/v1/rpc/validate_buyer_email
CREDENCIAIS: SUPABASE_URL e SUPABASE_ANON_KEY carregados de env vars (NAO hardcoded)
NOTA: O ID "dyvrlpxcgpoizfjsptda" aparece APENAS em docs-riaworks/ (documentacao),
      NUNCA em codigo executavel.

DADOS ENVIADOS AO SUPABASE:
  { "buyer_email": "email@example.com" }
  NADA MAIS. Zero dados de maquina, zero API keys, zero fingerprint.

DADOS RECEBIDOS DO SUPABASE:
  { valid, name, reason, install_count, premium_token }

O premium_token e usado para git clone do repo premium (efemero, deletado apos uso).
```

### 1.6 Analise do Pre-Publish Gate

```
ARQUIVO: bin/pre-publish-gate.js
DESIGN: Fail-CLOSED (bloqueia npm publish se encontrar problemas)

DEFESAS (5 camadas):
  Camada 1: package.json "files" whitelist (so L1 entra no npm)
  Camada 2: .npmignore exclui .env, credentials, .mcp.json, keys
  Camada 3: pre-publish-gate.js escaneia 14 regex patterns de secrets
  Camada 4: Forbidden file patterns (.env, .pem, .key, id_rsa, .sqlite)
  Camada 5: Trufflehog opcional + GitHub Actions independente

PATTERNS DETECTADOS:
  - GitHub tokens (ghp_, github_pat_, gho_, ghs_, ghr_)
  - Anthropic (sk-ant-), OpenAI (sk-), AWS (AKIA)
  - JWT/Supabase, Notion, ElevenLabs, N8N webhooks
  - Generic: password|api_key|secret|token assignments
  - PII brasileiro: CPF, CNPJ

BYPASS POSSIVEL? So com --ignore-scripts deliberado.
VEREDICTO: Gate REAL, nao teatro. Bloqueia publish com exit(1).
```

---

## ANGULO 2: COMO DESENVOLVEDOR (clone + Claude Code)

### 2.1 Hooks Python - Inventario Completo (28 hooks)

**NENHUM hook Python faz acesso a rede.** Todos usam apenas stdlib + PyYAML.

| Risco | Hooks | Justificativa |
|-------|-------|---------------|
| **HIGH** | `continuous_save.py` | Loga conteudo de mensagens (ate 2000 chars) em JSONL |
| **HIGH** | `post_batch_cascading.py` | Escrita ampla em agents/knowledge + PyYAML dependency + 30s timeout |
| **HIGH** | `gsd-check-update.js` | UNICO com acesso a rede (npm view) + processo detached |
| **MEDIUM** | `session_start.py` | Injeta prompt de personalidade (8+ arquivos lidos e consolidados) |
| **MEDIUM** | `skill_router.py` | Injeta conteudo de SKILL.md/AGENT.md no contexto por keyword match |
| **MEDIUM** | `quality_watchdog.py` | Injeta blocos MANDATORY de AGENT.md no contexto |
| **MEDIUM** | `memory_updater.py` | Modifica memoria persistente baseado em pattern matching |
| **MEDIUM** | `claude_md_agent_sync.py` | Modifica CLAUDE.md (instrucoes do sistema) |
| **LOW** | 17 outros hooks | Escrita limitada a logs/estado, sem rede |
| **NONE** | 3 hooks (guards + statusline) | Somente leitura ou protecao (fail-closed) |

### 2.2 Blast Radius - Se Um Hook Fosse Comprometido

```
CENARIO: Hook Python comprometido (ex: session_start.py)

ACESSO LEITURA:  Qualquer arquivo acessivel pelo usuario do OS (sem sandbox)
ACESSO ESCRITA:  Qualquer local com permissao do usuario (sem sandbox)
ACESSO REDE:     Se adicionar "import socket/urllib" -> exfiltracao trivial
PERSISTENCIA:    Pode modificar outros hooks, CLAUDE.md, settings.json
ESCALACAO:       Pode injetar instrucoes no prompt que Claude segue cegamente

BLAST RADIUS MAXIMO:
  - session_start.py comprometido -> controle total do comportamento de Claude
  - continuous_save.py comprometido -> historico completo de interacoes exposto
  - post_batch_cascading.py comprometido -> corrupcao de toda a knowledge base
```

### 2.3 Permissoes do Claude Code

```
settings.json (distribuido, trackeado):
  DENY LIST:
    - rm -rf *, sudo *, chmod 777 *
    - git push (TODAS as variacoes bloqueadas)
    - npm publish (TODAS as variacoes bloqueadas)
    - git reset --hard *
  VEREDICTO: BEM configurado

settings.local.json (local, gitignored):
  ALLOW LIST (PROBLEMATICO):
    - "Bash"              <- IRRESTRITO (qualquer comando auto-aprovado)
    - "Write(**/*)"       <- Escrita em qualquer arquivo
    - "Edit(**/*)"        <- Edicao de qualquer arquivo
    - "WebFetch"          <- Acesso web
    - mcp__playwright__*  <- Automacao de browser completa
    - mcp__puppeteer__*   <- Automacao de browser completa

  DENY LIST (MAIS FRACA que settings.json):
    - So bloqueia rm -rf /, mkfs, dd if=/dev/zero
    - NAO replica bloqueios de git push, npm publish, sudo

  BUG ESTRUTURAL: "permissions" aninhado dentro de "permissions" (ambiguidade)

  VEREDICTO: RISCO ALTO para ambiente local de desenvolvimento
```

### 2.4 MCP Servers

```
.mcp.json: NAO EXISTE no disco (corretamente gitignored)
Documentacao referencia 5 MCPs: n8n, clickup, miro, figma, notion
Todos usam ${ENV_VAR} syntax (sem tokens plaintext)

RISCO VIA SKILLS:
  - source-sync: ESCREVE tags em Google Sheets (bidirectional)
  - sync-docs: UPLOAD para Google Drive + tenta git push (bloqueado por deny)
  - convert-to-company-docs: UPLOAD para Google Docs
  Todos sao OPT-IN (requerem comando explicito)
```

### 2.5 Vetor de Prompt Injection via Filesystem

```
VETOR IDENTIFICADO (NOVO):

Hooks que injetam conteudo de arquivos no contexto de Claude:
  1. session_start.py   -> injeta JARVIS-SOUL.md, DNA-PERSONALITY.md
  2. skill_router.py    -> injeta SKILL.md (100 linhas) por keyword match
  3. quality_watchdog.py -> injeta blocos MANDATORY de AGENT.md

SE um arquivo malicioso fosse adicionado ao repo (SKILL.md ou AGENT.md):
  -> Suas instrucoes seriam injetadas automaticamente no contexto
  -> Claude seguiria as instrucoes acreditando serem legitimas
  -> Nenhuma verificacao de integridade/assinatura existe

MITIGACAO ATUAL: Nenhuma. Confianca total no filesystem.
```

---

## MAPEAMENTO DE EXFILTRACAO TEORICA

### Se eu fosse um atacante com controle sobre este codigo:

| # | Vetor | Dificuldade | Impacto | Detectabilidade |
|---|-------|-------------|---------|-----------------|
| 1 | Adicionar `import urllib` em hook Python existente | FACIL | ALTO (exfiltrar .env, mensagens) | MEDIO (code review) |
| 2 | Criar SKILL.md malicioso com keywords comuns | FACIL | ALTO (prompt injection persistente) | BAIXO (parece skill normal) |
| 3 | Modificar session_start.py para injetar instrucoes | MEDIO | CRITICO (controle total de Claude) | MEDIO (diff visivel) |
| 4 | Comprometer pacote PyYAML (supply chain) | DIFICIL | ALTO (execucao em todos os hooks YAML) | BAIXO (transparente) |
| 5 | Publicar versao maliciosa do npm package | DIFICIL | ALTO (todos os usuarios afetados) | ALTO (pre-publish gate) |
| 6 | Exploitar settings.local.json Bash irrestrito | MEDIO | ALTO (qualquer comando) | BAIXO (local only) |

### Vetores BLOQUEADOS efetivamente:

| Vetor | Por que esta bloqueado |
|-------|----------------------|
| Secrets no npm package | Pre-publish gate (5 camadas de defesa) |
| git push acidental | settings.json deny list (4 patterns) |
| npm publish acidental | settings.json deny list (2 patterns) |
| .env no git | .gitignore + .npmignore + pre-publish gate |
| Credenciais MCP hardcoded | .mcp.json gitignored + ${ENV_VAR} syntax |
| Hooks importando modulos de rede | Nenhum importa atualmente (verificavel por grep) |

---

## MATRIZ DE RISCO CONSOLIDADA

| Componente | Risco npm User | Risco Developer | Evidencia |
|------------|---------------|-----------------|-----------|
| npm install | NONE | N/A | Zero lifecycle hooks |
| npx mega-brain-ai | LOW | N/A | So banner + routing |
| Setup wizard | LOW | LOW | Keys vao so para provedores |
| Supabase call | LOW | LOW | So email, opt-in |
| Pre-publish gate | NONE (defesa) | NONE (defesa) | Fail-closed, 14 regex |
| Python hooks | N/A | **HIGH** | 28 hooks, sem sandbox, filesystem completo |
| gsd-check-update.js | N/A | **HIGH** | Unico com rede + detached process |
| settings.local.json | N/A | **HIGH** | Bash irrestrito, deny fraca |
| Prompt injection filesystem | N/A | **MEDIUM** | SKILL.md/AGENT.md injetados sem verificacao |
| MCP servers | N/A | **MEDIUM** | Write access a Google Sheets via skills |
| continuous_save.py | N/A | **MEDIUM** | Loga conteudo de mensagens |

---

## RECOMENDACOES PRIORIZADAS

### CRITICAS (fazer imediatamente)

| # | Acao | Componente | Esforco |
|---|------|-----------|---------|
| R1 | Corrigir settings.local.json: substituir `"Bash"` irrestrito por patterns especificos | Permissoes | 30min |
| R2 | Adicionar timeout a gsd-check-update.js e gsd-context-monitor.js | Hooks | 5min |
| R3 | Corrigir aninhamento duplo de "permissions" em settings.local.json | Permissoes | 15min |

### ALTAS (fazer esta semana)

| # | Acao | Componente | Esforco |
|---|------|-----------|---------|
| R4 | Reduzir truncamento de continuous_save.py de 2000 para 200 chars (ou so metadados) | Hooks | 15min |
| R5 | Implementar checksums para arquivos de personalidade lidos por session_start.py | Hooks | 2h |
| R6 | Adicionar deny rules de git push e npm publish no settings.local.json | Permissoes | 10min |

### MEDIAS (fazer este mes)

| # | Acao | Componente | Esforco |
|---|------|-----------|---------|
| R7 | Implementar whitelist/assinatura para SKILL.md injetados por skill_router.py | Hooks | 4h |
| R8 | Adicionar log de auditoria para modificacoes do memory_updater.py | Hooks | 2h |
| R9 | Considerar substituir gsd-check-update.js por verificacao offline/manual | Hooks | 1h |
| R10 | Tornar layer validation do pre-publish gate fail-closed (nao warn) | Gate | 1h |

---

## NOTA FINAL

```
NOTA GERAL: B+  (mesma da auditoria estatica - confirmada em runtime)

PARA USUARIO NPM:        A   (excelente - defesa em profundidade real)
PARA DESENVOLVEDOR:       B-  (bom, mas settings.local.json e hooks precisam hardening)

ZERO backdoors encontrados.
ZERO exfiltracao intencional encontrada.
ZERO telemetria/analytics/tracking.

Os riscos identificados sao todos ACIDENTAIS (permissoes excessivas,
logging verboso, falta de sandbox) e NAO MALICIOSOS.
```

---

*Relatorio gerado em 2026-02-28 por analise de inteligencia cibernetica com 4 agentes paralelos.*
*Complementa security-audit-report.md (auditoria estatica) e recommendations.md (13 acoes).*
