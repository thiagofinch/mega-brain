# Hook Installation Guide

> **Purpose:** Reinstalar os git hooks de segurança ao clonar o repositório.
> **Date:** 2026-02-22 (post-incident hardening)

---

## Por que isso é necessário?

Os git hooks (`.git/hooks/`) são **locais** — não vão para o GitHub. Ao clonar o repo em outra máquina, você precisa reinstalá-los manualmente.

Os Claude hooks (`.claude/hooks/`) SÃO tracked pelo git e vêm junto com o clone.

---

## Quick Install (Copy-Paste)

```bash
# Na raiz do mega-brain clonado:
cp system/docs/hooks/pre-commit .git/hooks/pre-commit
cp system/docs/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

---

## O que cada hook faz

### 1. Pre-Commit Hook (`.git/hooks/pre-commit`)

**Dispara em:** `git commit`
**Design:** fail-CLOSED (erro = bloqueia)

Escaneia **staged files** procurando:
- API keys (GitHub, Anthropic, OpenAI, AWS, ElevenLabs, Deepgram, Notion)
- Arquivos sensíveis (.env, credentials.json, .pem, .key, id_rsa)
- JWT tokens (Supabase)
- N8N webhook URLs
- Passwords/secrets hardcoded

**Exclusões:** `bin/pre-publish-gate.js` (contém regex de detecção, não secrets reais)

**Override (PERIGOSO):** `git commit --no-verify`

### 2. Pre-Push Hook (`.git/hooks/pre-push`)

**Dispara em:** `git push`
**Design:** fail-CLOSED (erro = bloqueia)

Escaneia **todos os arquivos tracked** procurando:
- Mesmos patterns de API keys
- Phantom files (tracked mas deveriam estar no .gitignore)
- Arquivos .env tracked

**Bypass validado:** Se `push.js` (via `mega-brain push`) já executou validação, seta `MEGA_BRAIN_PUSH_VALIDATED=true` e o hook permite o push.

**Override (PERIGOSO):** `git push --no-verify`

### 3. Pre-Publish Gate (`bin/pre-publish-gate.js`)

**Dispara em:** `npm publish` (via `prepublishOnly` no package.json)
**Design:** fail-CLOSED (erro = bloqueia)

Escaneia o **pacote npm** (output de `npm pack`) procurando:
- Arquivos proibidos (.env, .db, credentials, DOSSIE-SEGURANCA)
- API keys e tokens em conteúdo
- PII em massa (>3 emails por arquivo)
- CPF/CNPJ brasileiros

**Override:** Não existe (npm lifecycle obrigatório)

### 4. CI/CD Security Gate (`.github/workflows/publish.yml`)

**Dispara em:** Release ou workflow_dispatch
**Design:** fail-CLOSED (erro = bloqueia publish)

Executa antes do `npm publish`:
- `trufflehog filesystem` com `--only-verified`
- `npm pack` + descompacta + scan do tarball
- Pattern grep para API keys comuns

**Override:** Não existe (pipeline CI obrigatório)

---

## Claude Hooks (Tracked pelo Git)

Estes hooks já vêm com o clone. Configurados em `.claude/settings.json`:

| Hook | Tipo | Design | O que faz |
|------|------|--------|-----------|
| `claude_md_guard.py` | PreToolUse | fail-CLOSED | Bloqueia CLAUDE.md fora de locais autorizados |
| `creation_validator.py` | PreToolUse | fail-CLOSED | Valida criação de hooks, skills, MCP configs |

---

## Ferramentas Opcionais (Melhoram a Detecção)

```bash
# gitleaks — usado pelo pre-commit hook se disponível
brew install gitleaks     # macOS
# ou https://github.com/gitleaks/gitleaks/releases

# trufflehog — usado pelo pre-push hook e CI/CD
brew install trufflehog   # macOS
# ou https://github.com/trufflesecurity/trufflehog/releases
```

---

## Verificação

Após instalar, verifique:

```bash
# Hooks existem e são executáveis
ls -la .git/hooks/pre-commit .git/hooks/pre-push

# Teste o pre-commit (não deve bloquear um commit limpo)
echo "test" > /tmp/test.txt && git add /tmp/test.txt
git commit --dry-run  # Deve rodar o hook sem erro

# Teste o pre-push (deve bloquear push direto)
git push --dry-run 2>&1  # Deve mostrar scan de segurança
```

---

## Mapa Completo de Proteção

```
Layer 0: .gitignore (225 regras) — arquivos nem entram no tracking
Layer 1: pre-commit hook — bloqueia secrets no commit
Layer 2: pre-push hook — bloqueia push sem validação
Layer 3: push.js (921 linhas) — validação multicamada
Layer 4: pre-publish-gate.js — bloqueia secrets no npm pack
Layer 5: CI/CD trufflehog — bloqueia secrets na pipeline
Layer 6: .gitleaks.toml — config de patterns customizados
Layer 7: Claude Code deny list — bloqueia git push/npm publish no Claude
```

---

_Hook Installation Guide v1.0 — 2026-02-22_
