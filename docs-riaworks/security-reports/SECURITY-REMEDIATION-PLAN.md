# PLANO DE REMEDIACAO DE SEGURANCA - Mega Brain

**Data:** 2026-02-28
**Baseado em:** security-audit-report.md, recommendations.md, cyber-intelligence-report.md
**Elaborado por:** Engenheiro de Seguranca (Claude Opus 4.6)
**Total de Findings:** 27 (consolidado, sem duplicatas)

---

## RESUMO EXECUTIVO

```
+----------+-----------+-------------------------------------------------------+
| Severity | Qtd       | Resumo                                                |
+----------+-----------+-------------------------------------------------------+
| CRITICO  |  4        | CI/CD injection, permissoes locais, estrutura config  |
| MEDIO    | 10        | Shell injection, upload paths, prompt injection, logs |
| LOW      | 13        | Pinning, versioning, cache, consolidacao, tokens      |
+----------+-----------+-------------------------------------------------------+
| TOTAL    | 27        | Agrupados em 7 PRs por dominio funcional              |
+----------+-----------+-------------------------------------------------------+
```

---

## CLASSIFICACAO CONSOLIDADA DE FINDINGS

### CRITICOS (4)

| ID    | Finding                                                        | Fonte               | Arquivo(s)                                     |
|-------|----------------------------------------------------------------|----------------------|------------------------------------------------|
| C-01  | Injecao de comando via comentario de PR no GitHub Actions      | audit-report C1      | `.github/workflows/claude-code-pr.yml:82,110,118,123` |
| C-02  | `"Bash"` irrestrito no allow list de settings.local.json       | cyber-intel R1       | `.claude/settings.local.json`                  |
| C-03  | Aninhamento duplo de "permissions" em settings.local.json      | cyber-intel R3       | `.claude/settings.local.json`                  |
| C-04  | Deny list local NAO replica bloqueios de git push/npm publish  | cyber-intel R6       | `.claude/settings.local.json`                  |

### MEDIOS (10)

| ID    | Finding                                                        | Fonte               | Arquivo(s)                                     |
|-------|----------------------------------------------------------------|----------------------|------------------------------------------------|
| M-01  | `curl \| sh` sem pinning no CI (TruffleHog)                   | audit-report M1      | `.github/workflows/publish.yml:55`             |
| M-02  | `execSync` com interpolacao shell em push.js                   | audit-report M2      | `bin/push.js:90`                               |
| M-03  | Injecao AppleScript no notification_system.py                  | audit-report M3      | `.claude/hooks/notification_system.py:40-44`   |
| M-04  | `execSync` com interpolacao shell no installer.js (git clone)  | audit-report M4      | `bin/lib/installer.js:381`                     |
| M-05  | Upload Google Drive sem restricao de path                      | audit-report M5      | `.claude/skills/sync-docs/gdrive_sync.py`, `.claude/skills/convert-to-company-docs/convert.py` |
| M-06  | Paths de credenciais OAuth hardcoded com raw string            | audit-report M6      | `.claude/skills/sync-docs/reauth.py:25-26`     |
| M-07  | continuous_save.py loga ate 2000 chars de mensagens            | cyber-intel R4       | `.claude/hooks/continuous_save.py`             |
| M-08  | Sem checksums para arquivos de personalidade (prompt injection)| cyber-intel R5       | `.claude/hooks/session_start.py`               |
| M-09  | Sem whitelist/assinatura para SKILL.md injetados               | cyber-intel R7       | `.claude/hooks/skill_router.py`                |
| M-10  | Sem log de auditoria para memory_updater.py                    | cyber-intel R8       | `.claude/hooks/memory_updater.py`              |

### LOW (13)

| ID    | Finding                                                        | Fonte               | Arquivo(s)                                     |
|-------|----------------------------------------------------------------|----------------------|------------------------------------------------|
| L-01  | GitHub Actions nao pinadas por SHA                             | audit-report L1      | `.github/workflows/*.yml`                      |
| L-02  | npm install global no CI sem versao pinada                     | audit-report L2      | `.github/workflows/claude-code-pr.yml:99`      |
| L-03  | Divergencia de versao package.json vs package-lock.json        | audit-report L3      | `package.json`, `package-lock.json`            |
| L-04  | Token na URL do git clone (visivel em logs)                    | audit-report L4      | `bin/lib/installer.js:373`                     |
| L-05  | Deny list nao alinhada com ANTHROPIC-STANDARDS.md              | audit-report L5      | `.claude/settings.local.json:55-63`            |
| L-06  | Dois hooks sem timeout configurado                             | audit-report L6      | `settings.json` (gsd-check-update.js, gsd-context-monitor.js) |
| L-07  | Arquivos .pyc no disco (bytecode cache)                        | audit-report L7      | `.claude/hooks/__pycache__/`, etc.             |
| L-08  | Workflows de review de PR duplicados (3 workflows)             | audit-report I3      | `claude.yml`, `claude-code-review.yml`, `claude-code-pr.yml` |
| L-09  | Validar formato do token premium antes de uso                  | recommendations #12  | `bin/lib/installer.js`                         |
| L-10  | Usar GIT_ASKPASS para clone autenticado                        | recommendations #13  | `bin/lib/installer.js`                         |
| L-11  | gsd-check-update.js faz acesso a rede com processo detached    | cyber-intel R9       | `.claude/hooks/gsd-check-update.js`            |
| L-12  | Layer validation do pre-publish gate e warn (nao fail-closed)  | cyber-intel R10      | `bin/pre-publish-gate.js`                      |
| L-13  | Permissoes locais amplas (Write/Edit/**/*) em settings.local   | audit-report I2      | `.claude/settings.local.json`                  |

---

## AGRUPAMENTO POR PR (7 PRs)

Cada PR agrupa findings por dominio funcional para facilitar code review e testing.

---

### PR 1: [CRITICO] Fix CI/CD Command Injection + Supply Chain Hardening

**Prioridade:** P0 - IMEDIATA (bloqueia producao)
**Branch:** `fix/cicd-security-hardening`
**Reviewer:** Security Lead

#### Checklist:

```
FINDINGS: C-01, M-01, L-01, L-02, L-08

CI/CD Command Injection (C-01):
[ ] claude-code-pr.yml:82  - Mover interpolacao ${{ }} para bloco env:
[ ] claude-code-pr.yml:110 - Mover interpolacao ${{ }} para bloco env:
[ ] claude-code-pr.yml:118 - Mover interpolacao ${{ }} para bloco env:
[ ] claude-code-pr.yml:123 - Mover interpolacao ${{ }} para bloco env:
[ ] Testar com comentario de PR contendo metacaracteres shell

TruffleHog Supply Chain (M-01):
[ ] publish.yml:55 - Substituir curl|sh por GitHub Action oficial pinada
[ ] Usar trufflesecurity/trufflehog@v3.88.0 (ou SHA do commit)

GitHub Actions SHA Pinning (L-01):
[ ] Substituir actions/checkout@v4 por SHA completo em TODOS os workflows
[ ] Substituir actions/setup-node@v4 por SHA completo em TODOS os workflows
[ ] Substituir TODAS as actions de terceiros por SHA completo

npm Version Pinning (L-02):
[ ] claude-code-pr.yml:99 - Pinar @anthropic-ai/claude-code em versao especifica

Workflows Duplicados (L-08):
[ ] Avaliar consolidacao de claude.yml + claude-code-review.yml + claude-code-pr.yml
[ ] Documentar decisao (manter separados OU consolidar)

TESTES:
[ ] Criar PR de teste com comentario malicioso (ex: "; echo pwned; echo ")
[ ] Verificar que trufflehog scan funciona com action pinada
[ ] Confirmar que workflows executam corretamente apos SHA pinning
```

**Arquivos afetados:**
- `.github/workflows/claude-code-pr.yml`
- `.github/workflows/publish.yml`
- `.github/workflows/claude.yml`
- `.github/workflows/claude-code-review.yml`
- Outros workflows em `.github/workflows/`

---

### PR 2: [CRITICO] Fix Claude Code Permissions & Deny Lists

**Prioridade:** P0 - IMEDIATA
**Branch:** `fix/permissions-hardening`
**Reviewer:** Security Lead

#### Checklist:

```
FINDINGS: C-02, C-03, C-04, L-05, L-06, L-13

Bash Irrestrito (C-02):
[ ] settings.local.json - Substituir "Bash" irrestrito por patterns especificos
[ ] Definir whitelist de comandos permitidos (ex: "Bash(git:*)", "Bash(npm:*)", "Bash(python3:*)")
[ ] Ou remover "Bash" do allow e usar aprovacao manual

Aninhamento Duplo de Permissions (C-03):
[ ] settings.local.json - Corrigir estrutura: remover "permissions" aninhado dentro de "permissions"
[ ] Validar que a estrutura final e aceita pelo Claude Code

Deny List Incompleta (C-04 + L-05):
[ ] Adicionar "Bash(curl:*)" ao deny
[ ] Adicionar "Bash(wget:*)" ao deny
[ ] Adicionar "Read(*.env)" ao deny
[ ] Adicionar "Write(*.env)" ao deny
[ ] Adicionar "Edit(*.env)" ao deny
[ ] Adicionar "Read(*/.env)" ao deny
[ ] Adicionar "Write(*/.env)" ao deny
[ ] Adicionar "Edit(*/.env)" ao deny
[ ] Adicionar "Read(~/.ssh/*)" ao deny
[ ] Adicionar "Write(~/.ssh/*)" ao deny
[ ] Adicionar "Edit(~/.ssh/*)" ao deny
[ ] Replicar bloqueios de git push do settings.json
[ ] Replicar bloqueios de npm publish do settings.json

Hooks Sem Timeout (L-06):
[ ] settings.json - Adicionar "timeout": 30 em gsd-check-update.js
[ ] settings.json - Adicionar "timeout": 30 em gsd-context-monitor.js

Permissoes Amplas (L-13):
[ ] Avaliar reducao de Write(**/*) e Edit(**/*) para paths especificos
[ ] Documentar decisao se manter amplo (justificativa de dev local)

TESTES:
[ ] Validar que Claude Code inicia sem erros de config
[ ] Testar que comandos necessarios ainda funcionam
[ ] Testar que deny list bloqueia curl, wget, .env, .ssh
[ ] Confirmar que git push e npm publish sao bloqueados
```

**Arquivos afetados:**
- `.claude/settings.local.json`
- `.claude/settings.json`

---

### PR 3: [MEDIO] Fix Shell Injection in Node.js CLI Tools

**Prioridade:** P1 - ALTA (1 semana)
**Branch:** `fix/shell-injection-cli`
**Reviewer:** Backend Dev

#### Checklist:

```
FINDINGS: M-02, M-04, L-04, L-09, L-10

push.js Shell Injection (M-02):
[ ] bin/push.js:90 - Substituir execSync(`git ${cmd}`) por execFileSync('git', [...args])
[ ] Refatorar callers para passar argumentos como array (nao string)
[ ] Verificar que escaping de mensagens de commit funciona

installer.js Shell Injection (M-04):
[ ] bin/lib/installer.js:381 - Substituir execSync(`git clone ...`) por execFileSync('git', ['clone', ...])
[ ] Validar que authUrl nao contem metacaracteres

Token na URL (L-04):
[ ] bin/lib/installer.js:373 - Considerar uso de GIT_ASKPASS (L-10)
[ ] Implementar GIT_ASKPASS ou http.extraHeader para evitar token na URL

Validacao de Token (L-09):
[ ] bin/lib/installer.js - Adicionar regex validation: /^[a-zA-Z0-9_-]+$/
[ ] Rejeitar tokens com caracteres especiais antes de uso

TESTES:
[ ] Testar git push via push.js com mensagens contendo caracteres especiais
[ ] Testar git clone via installer.js com token valido
[ ] Testar que tokens invalidos sao rejeitados
[ ] Verificar que nenhum token aparece em logs
```

**Arquivos afetados:**
- `bin/push.js`
- `bin/lib/installer.js`

---

### PR 4: [MEDIO] Harden Python Hooks (Injection + Logging + Audit)

**Prioridade:** P1 - ALTA (1 semana)
**Branch:** `fix/hooks-security-hardening`
**Reviewer:** Backend Dev

#### Checklist:

```
FINDINGS: M-03, M-07, M-10, L-07, L-11

AppleScript Injection (M-03):
[ ] notification_system.py:40-44 - Escapar aspas duplas em message e title
[ ] Implementar: message.replace('\\', '\\\\').replace('"', '\\"')
[ ] Implementar: title.replace('\\', '\\\\').replace('"', '\\"')
[ ] Implementar: sound.replace('\\', '\\\\').replace('"', '\\"')

Logging Excessivo (M-07):
[ ] continuous_save.py - Reduzir truncamento de 2000 para 200 chars
[ ] OU: Logar apenas metadados (timestamp, tool, status) sem conteudo de mensagens
[ ] Avaliar se conteudo de mensagens e realmente necessario nos logs

Audit Log para memory_updater (M-10):
[ ] memory_updater.py - Adicionar logging de TODAS as modificacoes em arquivo de auditoria
[ ] Formato: {timestamp, arquivo_modificado, tipo_modificacao, diff_resumido}
[ ] Local do log: logs/memory-audit.jsonl

Bytecode Cache (L-07):
[ ] Adicionar .claude/hooks/__pycache__/ ao .git/info/exclude
[ ] Adicionar .claude/skills/**/__pycache__/ ao .git/info/exclude
[ ] OU: Limpar e adicionar __pycache__ ao .gitignore se nao estiver

gsd-check-update.js Network Access (L-11):
[ ] Avaliar substituir verificacao online por offline/manual
[ ] Se manter online: adicionar timeout explicito e error handling
[ ] Documentar que este e o UNICO hook com acesso a rede

TESTES:
[ ] Testar notificacao com titulo contendo aspas: "Test "with" quotes"
[ ] Verificar que continuous_save nao loga conteudo sensivel
[ ] Verificar que memory_updater gera audit log
[ ] Confirmar que __pycache__ nao aparece em git status
```

**Arquivos afetados:**
- `.claude/hooks/notification_system.py`
- `.claude/hooks/continuous_save.py`
- `.claude/hooks/memory_updater.py`
- `.claude/hooks/gsd-check-update.js` (avaliacao)
- `.gitignore` ou `.git/info/exclude`

---

### PR 5: [MEDIO] Harden Prompt Injection Defenses

**Prioridade:** P2 - MEDIA (2 semanas)
**Branch:** `fix/prompt-injection-defenses`
**Reviewer:** Security Lead + Backend Dev

#### Checklist:

```
FINDINGS: M-08, M-09

Checksums para Arquivos de Personalidade (M-08):
[ ] session_start.py - Implementar verificacao de integridade dos arquivos lidos
[ ] Criar manifest com SHA256 dos arquivos de personalidade esperados:
    [ ] JARVIS-SOUL.md
    [ ] JARVIS-DNA-PERSONALITY.md
    [ ] JARVIS-MEMORY.md
    [ ] Outros arquivos injetados no contexto
[ ] Na inicializacao: calcular hash e comparar com manifest
[ ] Se hash diverge: AVISAR (warn) mas nao bloquear
[ ] Local do manifest: .claude/jarvis/INTEGRITY-MANIFEST.json

Whitelist para SKILL.md Injetados (M-09):
[ ] skill_router.py - Implementar whitelist de skills confiáveis
[ ] Opcao A: Whitelist de paths permitidos (hardcoded ou em config)
[ ] Opcao B: Verificacao de hash dos SKILL.md antes de injecao
[ ] Opcao C: Assinatura digital (mais complexo, avaliar necessidade)
[ ] Se skill nao esta na whitelist: AVISAR e NAO injetar

TESTES:
[ ] Modificar um arquivo de personalidade e verificar que aviso aparece
[ ] Criar SKILL.md fora da whitelist e verificar que nao e injetado
[ ] Confirmar que skills legitimos continuam funcionando
[ ] Testar que session_start funciona mesmo com manifest ausente (graceful degradation)
```

**Arquivos afetados:**
- `.claude/hooks/session_start.py`
- `.claude/hooks/skill_router.py`
- `.claude/jarvis/INTEGRITY-MANIFEST.json` (novo)

---

### PR 6: [MEDIO] Harden Google Drive Integration

**Prioridade:** P2 - MEDIA (2 semanas)
**Branch:** `fix/gdrive-path-validation`
**Reviewer:** Backend Dev

#### Checklist:

```
FINDINGS: M-05, M-06

Path Restriction no Upload (M-05):
[ ] gdrive_sync.py - Adicionar validacao de path no upload_file()
[ ] convert.py - Adicionar validacao de path no upload_file()
[ ] Definir ALLOWED_DIRS = ['knowledge/', 'docs/', 'agents/', 'core/']
[ ] Rejeitar uploads de paths fora dos diretorios permitidos
[ ] Adicionar logging de todos os uploads (path, destino, timestamp)

OAuth Path Correction (M-06):
[ ] reauth.py:25 - Substituir Path(r"~/.config/...") por Path.home() / ".config" / ...
[ ] reauth.py:26 - Substituir Path(r"~/.config/...") por Path.home() / ".config" / ...
[ ] Adicionar verificacao de permissoes do arquivo (600)
[ ] Testar que expansao de ~ funciona em Windows e Linux/Mac

TESTES:
[ ] Testar upload de arquivo dentro de ALLOWED_DIRS (deve funcionar)
[ ] Testar upload de arquivo fora de ALLOWED_DIRS (deve rejeitar)
[ ] Testar upload de path com traversal (../../etc/passwd) (deve rejeitar)
[ ] Testar que reauth.py encontra credenciais corretamente apos fix
[ ] Verificar que permissoes 600 sao checadas
```

**Arquivos afetados:**
- `.claude/skills/sync-docs/gdrive_sync.py`
- `.claude/skills/convert-to-company-docs/convert.py`
- `.claude/skills/sync-docs/reauth.py`

---

### PR 7: [LOW] Package Hygiene & Pre-Publish Hardening

**Prioridade:** P3 - BAIXA (1 mes)
**Branch:** `chore/package-hygiene`
**Reviewer:** Backend Dev

#### Checklist:

```
FINDINGS: L-03, L-12

Version Sync (L-03):
[ ] Executar npm install para sincronizar package.json e package-lock.json
[ ] Verificar que versoes coincidem apos sync
[ ] Commitar package-lock.json atualizado

Pre-Publish Gate Hardening (L-12):
[ ] pre-publish-gate.js - Avaliar tornar layer validation fail-closed
[ ] Se layer validation falha: exit(1) ao inves de warn
[ ] Documentar decisao

TESTES:
[ ] npm install executa sem erros
[ ] npm pack gera pacote correto
[ ] pre-publish-gate bloqueia se layer validation falha
```

**Arquivos afetados:**
- `package.json`
- `package-lock.json`
- `bin/pre-publish-gate.js`

---

## ORDEM DE EXECUCAO

```
SEMANA 1 (P0 - CRITICO):
  PR 1: CI/CD Security Hardening ........... [C-01, M-01, L-01, L-02, L-08]
  PR 2: Permissions & Deny Lists ........... [C-02, C-03, C-04, L-05, L-06, L-13]

SEMANA 2 (P1 - ALTO):
  PR 3: Shell Injection CLI Tools .......... [M-02, M-04, L-04, L-09, L-10]
  PR 4: Hooks Security Hardening ........... [M-03, M-07, M-10, L-07, L-11]

SEMANA 3-4 (P2 - MEDIO):
  PR 5: Prompt Injection Defenses .......... [M-08, M-09]
  PR 6: Google Drive Integration ........... [M-05, M-06]

SEMANA 4+ (P3 - BAIXO):
  PR 7: Package Hygiene .................... [L-03, L-12]
```

---

## MATRIZ DE RASTREABILIDADE

| Finding ID | PR  | Severity | Status   |
|------------|-----|----------|----------|
| C-01       | PR1 | CRITICO  | PENDENTE |
| C-02       | PR2 | CRITICO  | PENDENTE |
| C-03       | PR2 | CRITICO  | PENDENTE |
| C-04       | PR2 | CRITICO  | PENDENTE |
| M-01       | PR1 | MEDIO    | PENDENTE |
| M-02       | PR3 | MEDIO    | PENDENTE |
| M-03       | PR4 | MEDIO    | PENDENTE |
| M-04       | PR3 | MEDIO    | PENDENTE |
| M-05       | PR6 | MEDIO    | PENDENTE |
| M-06       | PR6 | MEDIO    | PENDENTE |
| M-07       | PR4 | MEDIO    | PENDENTE |
| M-08       | PR5 | MEDIO    | PENDENTE |
| M-09       | PR5 | MEDIO    | PENDENTE |
| M-10       | PR4 | MEDIO    | PENDENTE |
| L-01       | PR1 | LOW      | PENDENTE |
| L-02       | PR1 | LOW      | PENDENTE |
| L-03       | PR7 | LOW      | PENDENTE |
| L-04       | PR3 | LOW      | PENDENTE |
| L-05       | PR2 | LOW      | PENDENTE |
| L-06       | PR2 | LOW      | PENDENTE |
| L-07       | PR4 | LOW      | PENDENTE |
| L-08       | PR1 | LOW      | PENDENTE |
| L-09       | PR3 | LOW      | PENDENTE |
| L-10       | PR3 | LOW      | PENDENTE |
| L-11       | PR4 | LOW      | PENDENTE |
| L-12       | PR7 | LOW      | PENDENTE |
| L-13       | PR2 | LOW      | PENDENTE |

---

## NOTAS PARA O DEV

1. **PR 1 e PR 2 sao BLOQUEANTES** - Nenhum outro PR deve ser mergeado antes deles
2. **PR 1 requer teste manual** - Criar PR de teste com payload malicioso no comentario
3. **PR 2 requer backup** - Salvar settings.local.json antes de modificar (config local)
4. **PR 3 requer testes de regressao** - push.js e installer.js sao usados em producao
5. **PR 5 e mais complexo** - Implementar checksums pode impactar performance de startup
6. **PR 6 e cross-platform** - Path expansion precisa funcionar em Windows E macOS/Linux
7. **Falsos positivos (L8-L12 do audit)** foram EXCLUIDOS desta lista - ja validados como seguros

---

*Plano gerado em 2026-02-28 - Consolidacao de 3 relatorios de seguranca*
*27 findings | 7 PRs | 4 semanas estimadas*
