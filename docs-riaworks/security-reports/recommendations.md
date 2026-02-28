# Recomendacoes de Seguranca - Repositorio Mega Brain

**Data:** 2026-02-28
**Prioridade:** Ordenadas por severidade e impacto

---

## IMEDIATO (Antes do Uso em Producao)

### 1. CORRIGIR: Injecao de Comando em `claude-code-pr.yml` [CRITICO]

**Arquivo:** `.github/workflows/claude-code-pr.yml`
**Linhas:** 82, 110, 118, 123

**Problema:** Conteudo de comentario de PR e interpolado diretamente em comandos shell via `${{ }}`, permitindo execucao arbitraria de codigo por qualquer usuario do GitHub que possa comentar em um PR.

**Correcao:** Substituir interpolacao direta por variaveis de ambiente:

```yaml
# ANTES (VULNERAVEL):
- name: Parse Claude command
  run: |
    COMMENT="${{ fromJson(steps.pr-details.outputs.result).comment }}"

# DEPOIS (SEGURO):
- name: Parse Claude command
  env:
    COMMENT: ${{ fromJson(steps.pr-details.outputs.result).comment }}
    PR_TITLE: ${{ fromJson(steps.pr-details.outputs.result).title }}
    PR_BODY: ${{ fromJson(steps.pr-details.outputs.result).body }}
  run: |
    # Variaveis agora sao seguramente escapadas pelo runtime do GitHub Actions
    COMMAND=$(echo "$COMMENT" | sed -n 's/.*@\.claude\s*\(.*\)/\1/p' | head -1)
```

Aplicar o mesmo padrao nas linhas 110, 118 e 123.

**Impacto:** Elimina a unica vulnerabilidade CRITICA do repositorio.

---

### 2. CORRIGIR: Pinar Instalacao do TruffleHog no CI [MEDIO]

**Arquivo:** `.github/workflows/publish.yml:55`

**Correcao:** Substituir `curl | sh` por GitHub Action pinada:

```yaml
# ANTES (ARRISCADO):
- name: Install TruffleHog
  run: curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

# DEPOIS (SEGURO):
- name: TruffleHog Scan
  uses: trufflesecurity/trufflehog@v3.88.0  # pinado em versao especifica
  with:
    extra_args: --only-verified
```

---

## ALTA PRIORIDADE (Em 1 Semana)

### 3. ENDURECER: Substituir `execSync` por `execFileSync` nos Caminhos Criticos

**Arquivos:**
- `bin/push.js:90` - execucao de comandos git
- `bin/lib/installer.js:381` - git clone com token

**Correcao para push.js:**
```javascript
// ANTES:
return execSync(`git ${cmd}`, { cwd: PROJECT_ROOT, encoding: 'utf-8' });

// DEPOIS:
const args = cmd.split(/\s+/);  // ou melhor: passar args como array do caller
return execFileSync('git', args, { cwd: PROJECT_ROOT, encoding: 'utf-8' });
```

**Correcao para installer.js:**
```javascript
// ANTES:
execSync(`git clone --depth 1 "${authUrl}" "${tempDir}"`, { stdio: 'inherit' });

// DEPOIS:
execFileSync('git', ['clone', '--depth', '1', authUrl, tempDir], { stdio: 'inherit' });
```

### 4. ENDURECER: Sanitizar Inputs do AppleScript

**Arquivo:** `.claude/hooks/notification_system.py:40-44`

```python
# ANTES:
script = f'''display notification "{message}" with title "{title}" sound name "{sound}"'''

# DEPOIS:
safe_message = message.replace('\\', '\\\\').replace('"', '\\"')
safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
safe_sound = sound.replace('\\', '\\\\').replace('"', '\\"')
script = f'''display notification "{safe_message}" with title "{safe_title}" sound name "{safe_sound}"'''
```

### 5. ENDURECER: Adicionar Validacao de Path no Upload do Google Drive

**Arquivos:** `.claude/skills/sync-docs/gdrive_sync.py`, `.claude/skills/convert-to-company-docs/convert.py`

```python
# Adicionar no inicio de upload_file():
import os
ALLOWED_DIRS = ['knowledge/', 'docs/', 'agents/', 'core/']
rel_path = os.path.relpath(local_path, PROJECT_ROOT)
if not any(rel_path.startswith(d) for d in ALLOWED_DIRS):
    raise ValueError(f"Upload restrito: {rel_path} esta fora dos diretorios permitidos")
```

---

## MEDIA PRIORIDADE (Em 1 Mes)

### 6. Pinar GitHub Actions com Commit SHAs

**Arquivos:** Todos os `.github/workflows/*.yml`

```yaml
# ANTES:
- uses: actions/checkout@v4

# DEPOIS (exemplo - verificar SHA atual):
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

### 7. Alinhar Deny List com ANTHROPIC-STANDARDS.md

**Arquivo:** `.claude/settings.local.json`

Adicionar padroes de deny faltantes:
```json
"deny": [
  "Bash(curl:*)",
  "Bash(wget:*)",
  "Read(*.env)",
  "Write(*.env)",
  "Edit(*.env)",
  "Read(*/.env)",
  "Write(*/.env)",
  "Edit(*/.env)",
  "Read(~/.ssh/*)",
  "Write(~/.ssh/*)",
  "Edit(~/.ssh/*)"
]
```

### 8. Adicionar Timeouts nos Hooks que Estao Sem

**Arquivo:** `.claude/settings.json`

Adicionar `"timeout": 30` nas entradas dos hooks `gsd-check-update.js` e `gsd-context-monitor.js`.

### 9. Corrigir Expansao de Path do OAuth

**Arquivo:** `.claude/skills/sync-docs/reauth.py:25-26`

```python
# ANTES (~ nao expandido com raw string):
OAUTH_KEYS = Path(r"~/.config/mcp-gdrive/gcp-oauth.keys.json")

# DEPOIS:
OAUTH_KEYS = Path.home() / ".config" / "mcp-gdrive" / "gcp-oauth.keys.json"
```

### 10. Sincronizar Versoes do package.json e package-lock.json

```bash
npm install  # Vai regenerar o lock file com versao correspondente
```

---

## BAIXA PRIORIDADE (Boas Praticas)

### 11. Consolidar Workflows Duplicados de Review de PR

Tres workflows respondem a eventos de PR. Considerar consolidar em um ou dois para economizar creditos de API:
- `claude.yml`
- `claude-code-review.yml`
- `claude-code-pr.yml`

### 12. Validar Formato do Token Premium

**Arquivo:** `bin/lib/installer.js`

Antes de usar o token do Supabase:
```javascript
if (!/^[a-zA-Z0-9_-]+$/.test(token)) {
  throw new Error('Formato de token invalido recebido');
}
```

### 13. Usar GIT_ASKPASS para Clone Autenticado

**Arquivo:** `bin/lib/installer.js`

Ao inves de embutir token na URL:
```javascript
const env = { ...process.env, GIT_ASKPASS: 'echo', GIT_TOKEN: token };
execFileSync('git', ['clone', '--depth', '1', repoUrl, tempDir], { env, stdio: 'inherit' });
```

---

## Scorecard Resumido

| Area | Nota | Observacoes |
|------|------|-------------|
| Sem Backdoors/Malware | **A+** | Zero eval, exec, reverse shells, desserializacao |
| Gerenciamento de Credenciais | **A** | Tudo via env vars, .gitignore abrangente |
| Supply Chain | **A-** | Deps minimas, pacotes legitimos, lock file existe |
| Seguranca CI/CD | **D** | Falha CRITICA de injecao no workflow de PR |
| Defesa contra Injecao de Codigo | **B** | Alguma interpolacao shell, superficie de ataque limitada |
| Exposicao de Rede | **A+** | Sem portas abertas, sem servidores, sem WebSockets |
| Ofuscacao | **A+** | Codigo limpo e legivel em todo o repo |
| Sistema de Arquivos | **A+** | Sem symlinks, sem binarios, sem path traversal |

**Nota Geral: B+** (seria A- apos corrigir C1)

---

*Recomendacoes geradas em 2026-02-28 por Claude Opus 4.6*
