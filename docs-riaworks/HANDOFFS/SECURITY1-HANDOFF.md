# HANDOFF - Auditoria de Seguranca Mega Brain

**Data:** 2026-02-28
**Sessao anterior:** Auditoria estatica completa (8 vetores, 1420 arquivos)
**Proxima sessao:** Analise de inteligencia cibernetica (ataque + defesa)

---

## O Que Ja Foi Feito

Auditoria estatica completa do repositorio `mega-brain` cobrindo 8 vetores:

| Vetor | Status | Findings |
|-------|--------|----------|
| 1. Backdoors & Code Injection | Completo | 3 MEDIUM, 7 LOW |
| 2. Exfiltracao de Dados | Completo | 3 MEDIUM, 6 LOW |
| 3. Supply Chain | Completo | 1 MEDIUM, 3 LOW |
| 4. Credenciais & Secrets | Completo | Limpo |
| 5. File System Manipulation | Completo | Limpo |
| 6. Network / Port Exposure | Completo | Limpo |
| 7. Ofuscacao | Completo | Limpo |
| 8. Git & CI/CD | Completo | 1 CRITICAL, 1 MEDIUM |

**Resultado:** 1 CRITICAL, 6 MEDIUM, 12 LOW, 14 vetores limpos. Nota geral B+.

### Arquivos Gerados

```
docs-riaworks/
├── security-audit-report.md    ← Relatorio completo (portugues)
├── recommendations.md          ← 13 acoes priorizadas (portugues)
├── file-inventory.json         ← 1420 arquivos com SHA256
├── scan-scripts/
│   ├── generate_inventory.py   ← Script de inventario
│   └── README.md
└── HANDOFF.md                  ← Este arquivo
```

---

## O Que Falta: Analise de Inteligencia Cibernetica

A auditoria anterior foi **analise estatica pura** (grep, leitura de arquivos, pattern matching). Agora precisa de uma analise com **visao de inteligencia cibernetica**, cobrindo DOIS angulos:

### ANGULO 1: COMO DESENVOLVEDOR (quem faz fork/clona o repo)

Perguntas a responder:
- Se eu clonar este repo e rodar `npm install`, algum codigo executa automaticamente?
- Os hooks do Claude Code (28 scripts Python em `.claude/hooks/`) podem exfiltrar dados da minha maquina?
- O sistema de skills (`.claude/skills/`) tem acesso a quais recursos da minha maquina?
- Se eu rodar `/setup` ou `/jarvis-briefing`, o que acontece nos bastidores?
- Os MCP servers configurados em `.mcp.json` abrem conexoes para onde?
- O `settings.json` e `settings.local.json` concedem quais permissoes ao Claude Code?
- Se um hook ou skill for malicioso, qual e o blast radius maximo?

### ANGULO 2: COMO USUARIO (quem instala via `npx mega-brain-ai`)

Perguntas a responder:
- O que exatamente e publicado no npm? (analisar `files` no package.json e `.npmignore`)
- O pacote npm faz alguma requisicao HTTP ao ser instalado ou executado?
- O `bin/mega-brain.js` (entry point) faz chamadas externas?
- O setup wizard (`bin/lib/setup-wizard.js`) envia minhas API keys para algum lugar alem das APIs oficiais?
- O sistema de licenciamento/premium (`bin/lib/validate-email.js`, `bin/lib/installer.js`) envia quais dados para o Supabase?
- O Supabase recebe apenas email ou tambem recebe dados da minha maquina/ambiente?
- Se eu configurar todas as API keys no `.env`, algum codigo do pacote pode le-las e envia-las para terceiros?
- O `prepublishOnly` gate realmente bloqueia secrets ou e teatro?

### Analises Especificas Necessarias

1. **Trace de execucao do `npm install`**: Mapear EXATAMENTE o que executa (nenhum script lifecycle? confirmar)
2. **Trace de execucao do `npx mega-brain-ai`**: Mapear o fluxo completo desde o entry point
3. **Trace de execucao do `npx mega-brain-ai setup`**: Onde vao as API keys que eu digito?
4. **Trace de todas as chamadas HTTP**: Listar CADA endpoint externo que o codigo contata, com:
   - URL exata
   - Dados enviados (payload)
   - Motivo da chamada
   - Se e opt-in ou automatico
5. **Analise de dados enviados ao Supabase**: O que exatamente vai para `dyvrlpxcgpoizfjsptda.supabase.co`?
6. **Analise dos hooks em runtime**: Quando o Claude Code executa, quais hooks disparam e o que fazem com os dados?
7. **Mapeamento de exfiltracao teorica**: Se eu fosse um atacante e tivesse controle sobre este codigo, quais seriam os vetores mais faceis para vazar dados do usuario?
8. **Teste do pre-publish gate**: Ele realmente detecta secrets? Simular com dados falsos.

### Foco Principal

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  PERGUNTA CENTRAL:                                                           ║
║                                                                              ║
║  "Com este pacote instalado na minha maquina e minhas API keys              ║
║   configuradas no .env, existe ALGUM mecanismo — intencional ou             ║
║   acidental — pelo qual meus dados, credenciais ou informacoes              ║
║   do meu ambiente possam ser enviados para servidores externos              ║
║   sem meu conhecimento ou consentimento explicito?"                         ║
║                                                                              ║
║  Responder com EVIDENCIAS, nao com suposicoes.                              ║
║  Mostrar o codigo exato que faz ou nao faz cada coisa.                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Contexto Tecnico para a Proxima Sessao

### Arquivos-chave para analisar:

```
ENTRY POINTS (usuario executa):
├── bin/mega-brain.js              ← Entry point principal (npx mega-brain-ai)
├── bin/lib/setup-wizard.js        ← Setup interativo (pede API keys)
├── bin/lib/validate-email.js      ← Validacao de licenca via Supabase
├── bin/lib/installer.js           ← Instalador do premium (git clone com token)
├── bin/lib/feature-gate.js        ← Gate de features pro vs community
└── bin/pre-publish-gate.js        ← Gate de seguranca pre-publish

HOOKS (executam automaticamente no Claude Code):
├── .claude/hooks/*.py             ← 28 hooks Python (SessionStart, PreToolUse, etc)
├── .claude/hooks/gsd-check-update.js  ← Verifica atualizacoes do GSD
└── .claude/settings.json          ← Configuracao de hooks e permissoes

INTEGRACAO EXTERNA:
├── .claude/skills/sync-docs/      ← Upload para Google Drive
├── .claude/skills/convert-to-company-docs/  ← Upload para Google Drive
└── .mcp.json (template)           ← Configuracao de MCP servers

SUPABASE:
├── Endpoint: dyvrlpxcgpoizfjsptda.supabase.co
├── Funcao RPC: validate_buyer_email
└── Anon key hardcoded em validate-email.js (publico por design do Supabase)
```

### Findings da auditoria anterior relevantes:

- **C1 (CRITICAL)**: Injecao de comando no CI via PR comments — NAO afeta usuario local
- **M5 (MEDIUM)**: Upload GDrive sem restricao de path — afeta usuario com Google Drive configurado
- **M6 (MEDIUM)**: Paths OAuth hardcoded — afeta usuario com Google Drive configurado
- **Nenhum backdoor encontrado** na analise estatica
- **Nenhuma exfiltracao intencional** encontrada
- **Todos os hooks usam apenas stdlib + PyYAML** (sem requests, sem urllib)

---

## Como Comecar a Proxima Sessao

```
Prompt sugerido:

"Leia docs-riaworks/HANDOFF.md para contexto completo.
Realize a analise de inteligencia cibernetica descrita no handoff,
com foco na pergunta central: como usuario com o pacote instalado
e API keys configuradas, meus dados podem vazar?
Analise os dois angulos: desenvolvedor (clone) e usuario (npm install).
Trace cada chamada HTTP, cada acesso a .env, cada hook que dispara.
Salve resultados em docs-riaworks/."
```

---

*Handoff criado em 2026-02-28 — Auditoria estatica completa, analise de inteligencia cibernetica pendente.*
