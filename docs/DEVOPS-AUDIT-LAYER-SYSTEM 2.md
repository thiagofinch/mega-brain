# Mega Brain — DevOps Audit: Layer System & Distribution Architecture

> **Version:** 1.0.0
> **Date:** 2026-03-01
> **Audience:** DevOps engineers, security auditors, maintainers
> **Purpose:** Complete technical description of the 3-layer distribution system, CLI installer, email validation gate, and multi-remote push architecture

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Layer Architecture](#2-layer-architecture)
3. [Git Remote Topology](#3-git-remote-topology)
4. [npm Package (Layer 1)](#4-npm-package-layer-1)
5. [Pre-Publish Security Gate](#5-pre-publish-security-gate)
6. [CLI Installer & Setup Flow](#6-cli-installer--setup-flow)
7. [Email Validation System](#7-email-validation-system)
8. [Smart Push System](#8-smart-push-system)
9. [.gitignore Strategy](#9-gitignore-strategy)
10. [Manifest Files](#10-manifest-files)
11. [Security Controls Summary](#11-security-controls-summary)
12. [Audit Checklist](#12-audit-checklist)

---

## 1. Executive Summary

Mega Brain is an AI Knowledge Management System distributed as an npm package (`mega-brain-ai`). The codebase uses a **3-layer distribution model** to separate public open-source content (L1), premium paid content (L2), and personal user data (L3) — all managed from a single local repository with 3 different git remotes.

**Key facts:**
- Package name: `mega-brain-ai` (public on npmjs.com)
- Current version: `1.3.0`
- License: `UNLICENSED` (proprietary)
- Node.js requirement: `>=18.0.0` (uses native `fetch`)
- Module system: ES Modules (`"type": "module"`)
- Email validation backend: Supabase (PostgreSQL RPC)

---

## 2. Layer Architecture

### 2.1 Layer Definitions

| Layer | Name | Distribution | Git Remote | Visibility |
|-------|------|-------------|------------|------------|
| **L1** | Community | npm registry (public) | `origin` | Public |
| **L2** | Premium | Private GitHub repo | `premium` | MoneyClub buyers only |
| **L3** | Personal | Private backup repo | `backup` | Owner only |

### 2.2 Content Classification

```
L1 (Community) — The open-source shell
├── core/              → Processing engine (Python + YAML)
├── bin/               → CLI binaries (Node.js)
├── .claude/           → Claude Code integration (hooks, skills, rules, commands)
├── agents/conclave/   → Multi-agent deliberation templates
├── agents/_templates/ → Agent creation templates
├── docs/              → Documentation
├── .github/           → CI/CD workflows, manifests
└── *.gitkeep          → Empty directory structure markers

L2 (Premium) — L1 + populated knowledge content
├── agents/minds/      → Expert mind-clone agents (populated)
├── agents/cargo/      → Functional role agents (populated)
├── knowledge/dossiers/→ Person and theme dossiers
├── knowledge/playbooks/→ Actionable playbooks
├── knowledge/dna/     → Cognitive DNA schemas
├── knowledge/sources/ → Source material references
└── artifacts/         → Pipeline processing outputs

L3 (Personal) — Everything, including user-specific data
├── inbox/             → Raw input materials
├── logs/              → Processing and session logs
├── .claude/sessions/  → Claude Code session history
├── .claude/mission-control/ → Orchestration state
├── agents/sua-empresa/→ Company-specific agent data
├── .env               → API keys and credentials
└── .mcp.json          → MCP server configurations
```

### 2.3 Classification Priority

When a file matches multiple patterns, the highest-priority classification wins:

```
DELETE > NEVER > L3 > L2 > L1 > REVIEW
```

The programmatic classifier lives at `core/intelligence/audit_layers.py` and implements pattern arrays (`L1_PATTERNS`, `L2_PATTERNS`, `L3_PATTERNS`, `NEVER_PATTERNS`, `DELETE_PATTERNS`).

---

## 3. Git Remote Topology

### 3.1 Remote Configuration

```
origin  → https://github.com/thiagofinch/mega-brain.git        (L1 — public)
premium → https://github.com/thiagofinch/mega-brain-premium.git (L2 — private)
backup  → https://github.com/thiagofinch/mega-brain-full.git    (L3 — private)
```

### 3.2 Data Flow

```
Local Repository (all 3 layers coexist)
│
├──[git push origin main]──────────→ mega-brain.git (L1 only)
│   Uses: .gitignore to exclude L2/L3
│   Method: Standard git push (respects .gitignore)
│
├──[git push premium main --force]─→ mega-brain-premium.git (L1 + L2)
│   Uses: layer1-allowlist.txt + layer2-manifest.txt
│   Method: Temporary commit with git add -f, then git reset HEAD~1
│
└──[git push backup main --force]──→ mega-brain-full.git (L1 + L2 + L3)
    Uses: layer3-manifest.txt + git add -f
    Method: Temporary commit with git add -f, then git reset HEAD~1
    Safety: git reset HEAD -- .env (always unstaged)
```

### 3.3 Important: Ephemeral Commits

Layers 2 and 3 use a **temporary commit pattern**:
1. Force-add gitignored files (`git add -f`)
2. Create a commit
3. Force-push to the target remote
4. Immediately `git reset HEAD~1` to remove the commit from local history

This means **local `main` branch always reflects L1 state**. The L2 and L3 commits only exist on their respective remotes.

---

## 4. npm Package (Layer 1)

### 4.1 Package Identity

```json
{
  "name": "mega-brain-ai",
  "version": "1.3.0",
  "type": "module",
  "license": "UNLICENSED",
  "engines": { "node": ">=18.0.0" }
}
```

### 4.2 Binary Entry Points

```json
{
  "bin": {
    "mega-brain-ai": "bin/cli.js",
    "mega-brain": "bin/cli.js",
    "mega-brain-push": "bin/push.js"
  }
}
```

Users install with: `npx mega-brain-ai install`

### 4.3 Files Field (L1 Content Control)

The `files` field in `package.json` is the **primary gatekeeper** for what enters the npm package. It contains ~150 explicit entries defining exactly which files/directories are included.

Key inclusions:
- `.claude/` — Hooks, skills, rules, commands, agent templates
- `core/` — Processing engine
- `bin/` — CLI tools
- `agents/conclave/`, `agents/_templates/`, `agents/constitution/`
- `docs/` — Public documentation
- `knowledge/` — Only `.gitkeep` structure markers and navigation files

Key exclusions (NOT in `files`, therefore NOT in npm):
- `agents/minds/`, `agents/cargo/` (L2 premium content)
- `inbox/`, `logs/` (L3 personal data)
- `.env`, `.mcp.json` (secrets)
- `.planning/` (development artifacts)

### 4.4 Dependencies

```json
{
  "chalk": "^5.3.0",
  "inquirer": "^9.2.0",
  "ora": "^7.0.0",
  "boxen": "^7.1.0",
  "gradient-string": "^2.0.2"
}
```

All dependencies are for CLI UX (colors, prompts, spinners, boxes). No server-side or database dependencies are bundled.

### 4.5 Scripts

```json
{
  "start": "node bin/mega-brain.js",
  "install-wizard": "node bin/mega-brain.js install",
  "validate": "node bin/mega-brain.js validate",
  "validate:layers": "node bin/validate-package.js",
  "prepublishOnly": "node bin/pre-publish-gate.js"
}
```

---

## 5. Pre-Publish Security Gate

**File:** `bin/pre-publish-gate.js`
**Trigger:** Runs automatically via `prepublishOnly` script before every `npm publish`
**Design:** Fail-CLOSED — if scanning fails, publish is BLOCKED (exit 1)

### 5.1 Security Scan Pipeline

```
Step 1: Clean __pycache__ directories
Step 2: Get list of files that would be published (npm pack --dry-run --json)
Step 3: Check file names against FORBIDDEN_FILE_PATTERNS
Step 4: Scan file contents for SECRET_PATTERNS (regex)
Step 5: Optional trufflehog deep scan (if installed)
Step 6: Layer validation (only L1 files allowed)
         ↓
     VERDICT: 0 issues → PASS → publish proceeds
              >0 issues → BLOCKED → exit 1
```

### 5.2 Secret Detection Patterns

The gate scans for 13 categories of secrets:

| Pattern | Examples |
|---------|----------|
| GitHub tokens | `ghp_*`, `github_pat_*`, `gho_*`, `ghs_*`, `ghr_*` |
| Anthropic keys | `sk-ant-*` (90+ chars) |
| OpenAI keys | `sk-*` (48 chars) |
| AWS keys | `AKIA*` (16 chars) |
| ElevenLabs | `sk_*` (48 hex chars) |
| N8N webhooks | `*.app.n8n.cloud/webhook*` |
| Notion tokens | `ntn_*`, `secret_*` |
| JWT tokens | `eyJ*.eyJ*.*` (Supabase, etc.) |
| Generic secrets | `password/api_key/secret/token = "..."` |
| Brazilian CPF | `XXX.XXX.XXX-XX` |
| Brazilian CNPJ | `XX.XXX.XXX/XXXX-XX` |
| Bulk emails | >3 email addresses per file (PII indicator) |

### 5.3 Forbidden File Patterns

Files that MUST NEVER appear in the package:

```
.env, .env.*, credentials.json, service.account.*.json,
*.pem, *.key, id_rsa, id_ed25519, *.sqlite, *.db,
memory.db, DOSSIE-SEGURANCA*, trufflehog*
```

### 5.4 Layer Validation

After secret scanning, the gate calls `validatePackageSync()` from `bin/validate-package.js`:

1. Runs `npm pack --dry-run --json` to get the file list
2. Classifies each file using `core/intelligence/audit_layers.py` (Python subprocess)
3. Any file classified as non-L1 → VIOLATION → publish BLOCKED

```
bin/validate-package.js
    │
    ├── getPackFiles()         → npm pack --dry-run --json
    ├── classifyFiles()        → Python subprocess → audit_layers.classify_path()
    └── validatePackageSync()  → Returns {status: PASSED|FAILED, violations: [...]}
```

Exit codes:
- `0` = PASSED (all files are L1)
- `1` = FAILED (non-L1 files found)
- `2` = ERROR (could not run validation)

---

## 6. CLI Installer & Setup Flow

**File:** `bin/mega-brain.js` (entry point via `bin/cli.js`)

### 6.1 Available Commands

```
npx mega-brain-ai install [name]  → Install Mega Brain (Premium or Community)
npx mega-brain-ai setup           → Configure API keys (interactive wizard)
npx mega-brain-ai validate <email>→ Validate MoneyClub buyer email
npx mega-brain-ai push [--layer N]→ Push to Layer 1/2/3 remote
npx mega-brain-ai upgrade         → Upgrade Community to Premium
npx mega-brain-ai status          → Show Pro license status
npx mega-brain-ai features        → List available vs locked features
```

### 6.2 Auto-Setup Trigger

```javascript
// Auto-trigger setup if .env is missing (skip for install/setup/push)
const skipEnvCheck = ['install', 'setup', 'push'].includes(command);
if (!skipEnvCheck) {
  const projectEnv = resolve(process.cwd(), '.env');
  if (!existsSync(projectEnv)) {
    // → Runs setup wizard automatically
  }
}
```

If a user runs any command (except install/setup/push) and `.env` doesn't exist, the setup wizard is triggered automatically.

### 6.3 Install Flow (Simplified)

```
npx mega-brain-ai install
    │
    ├── Show ASCII banner
    ├── Prompt: email validation (MoneyClub buyer check)
    │   ├── Valid email + premium_token → PREMIUM install path
    │   └── Invalid email → COMMUNITY install path (free tier)
    ├── Clone/setup repository structure
    ├── Run setup wizard (API keys)
    └── Show completion message with next steps
```

---

## 7. Email Validation System

**File:** `bin/lib/validate-email.js`

### 7.1 Architecture

```
Client (Node.js CLI)
    │
    │  POST /rest/v1/rpc/validate_buyer_email
    │  Headers: apikey, Authorization (Bearer)
    │  Body: { buyer_email: "user@example.com" }
    │
    ▼
Supabase (PostgreSQL)
    │
    │  RPC function: validate_buyer_email
    │  Protected by: Row Level Security (RLS)
    │
    ▼
Response: { valid, name, reason, install_count, premium_token }
```

### 7.2 Connection Details

```javascript
const SUPABASE_URL = process.env.SUPABASE_URL
  || 'https://lgbzktgbhowxiwppycbi.supabase.co';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY
  || 'eyJhbGciOiJIUzI1NiIs...';  // Public anon key (safe by design)
```

**Important:** The Supabase anon key is hardcoded intentionally. This is standard Supabase practice — anon keys are public and protected by Row Level Security (RLS). They allow the CLI to work without prior `.env` setup.

Reference: https://supabase.com/docs/guides/auth#api-keys

### 7.3 Security Controls

| Control | Implementation |
|---------|---------------|
| Rate limiting | Max 3 attempts per session (`MAX_ATTEMPTS = 3`) |
| Timeout | 10 seconds per request (`AbortSignal.timeout(10000)`) |
| Input sanitization | `email.trim().toLowerCase()` |
| Format validation | Basic `@` check before API call |
| No Supabase client | Uses native `fetch` to avoid WebSocket handle leaks |

### 7.4 Response Schema

```javascript
{
  valid: boolean,        // true if email is a registered buyer
  name: string|null,     // buyer's name (for personalization)
  reason: string|null,   // error code if invalid
  installCount: number,  // how many times this email has installed
  premium_token: string|null  // token for premium content access
}
```

### 7.5 Error Codes

| Code | Portuguese Message |
|------|-------------------|
| `email_not_found` | Email nao autorizado. Acesse a pagina do produto para adquirir acesso. |
| `invalid_email_format` | Formato de email invalido. Verifique e tente novamente. |
| `max_attempts_exceeded` | Numero maximo de tentativas excedido. Reinicie o instalador. |
| `timeout` | Tempo de conexao esgotado. Verifique sua internet e tente novamente. |
| `network_error` | Erro de conexao. Verifique sua internet e tente novamente. |
| `validation_error` | Erro na validacao. Tente novamente em alguns minutos. |

### 7.6 Premium Token Flow

```
Email validated → premium_token returned
    │
    └── Used by installer to:
        ├── Clone premium content from L2 repo
        ├── Unlock premium features in the CLI
        └── Track active installations per buyer
```

---

## 8. Smart Push System

**File:** `bin/push.js` (1057 lines)
**Binary:** `mega-brain-push` or `mega-brain push`

### 8.1 Push Flows by Layer

#### Layer 1 (Community → origin)

```
1. Validate: phantom files, API keys in tracked files, .env in tracking
2. git add -A (respects .gitignore — L2/L3 excluded)
3. Prompt for commit message
4. git commit
5. git push origin main
6. Ask about npm publish
7. Auto-sync to backup (Layer 3)
```

#### Layer 2 (Premium → premium)

```
1. Validate: excluded personas, .env in manifest, agent-memory in manifest
2. Read layer1-allowlist.txt + layer2-manifest.txt
3. git add -f for each path (force-add gitignored L2 content)
4. git commit
5. git push premium main --force
6. git reset HEAD~1 (remove temporary commit from local)
7. Auto-sync to backup (Layer 3)
```

#### Layer 3 (Full Backup → backup)

```
1. No validation (everything goes)
2. git add -A (tracked files)
3. git add -f for each path in layer3-manifest.txt
4. git reset HEAD -- .env, .mcp.json, credentials.json (safety net)
5. Prompt for commit message
6. git commit
7. git push backup main --force
8. git reset HEAD~1 (remove temporary commit from local)
```

### 8.2 Pre-Push Validation

**Layer 1 checks:**
- Phantom files (tracked but should be ignored per `.gitignore`)
- Sensitive tokens in tracked files (GitHub PATs, `sk-ant-*`, `ghp_*`, etc.)
- `.env` files in git tracking

**Layer 2 checks:**
- Excluded personas not in manifest paths
- No `.env` paths in manifest
- No `.claude/agent-memory/` in manifest

**Layer 3:** No validation (it's a full backup)

### 8.3 Secret Files Safety Net

The following files are ALWAYS unstaged before any push (Layer 3):

```javascript
const SECRET_FILES = [
  '.env', '.env.local', '.env.production', '.env.development',
  '.mcp.json', 'credentials.json', 'token.json', 'token_write.json',
  'settings.local.json', '.claude/settings.local.json',
];
```

---

## 9. .gitignore Strategy

The `.gitignore` implements L1 distribution rules. Key sections:

### 9.1 Layer 3 (Personal Data) — Always Gitignored

```gitignore
.data/                      # Local data store
.env, .env.*                # Credentials
.mcp.json                   # MCP server configs with tokens
.claude/sessions/           # Session history
.claude/mission-control/    # Orchestration state
.claude/agent-memory/       # Runtime agent memory
agents/minds/**             # Expert mind clones (except .gitkeep)
agents/cargo/**             # Functional agents (except .gitkeep)
agents/sua-empresa/**       # Company data (except .gitkeep + README)
inbox/**                    # Raw input materials (except .gitkeep)
artifacts/chunks/**         # Pipeline chunks (except .gitkeep)
knowledge/dossiers/**       # Dossiers (except .gitkeep)
knowledge/playbooks/**      # Playbooks (except .gitkeep)
knowledge/dna/**            # DNA schemas (except .gitkeep)
logs/**                     # Logs (except .gitkeep + README)
```

### 9.2 .gitkeep Preservation Pattern

The `.gitignore` uses the `!` negation pattern to keep directory structure markers:

```gitignore
inbox/**                    # Ignore all inbox content
!inbox/.gitkeep             # But keep the structure marker
!inbox/README.md            # And the README
```

This ensures the npm package ships with the directory structure but no user content.

### 9.3 Secrets — Never Committed

```gitignore
.env, .env.local, .env.*.local, .env.production, .env.development
*.key, *.pem, *.p12, *.pfx, *.crt, *.cer, *.secret, *.credentials
credentials.json, token.json, token_write.json
settings.local.json
.mcp.json, mcp_servers.json
```

---

## 10. Manifest Files

Located in `.github/`:

### 10.1 `layer1-allowlist.txt`

Lists all paths that belong in the L1 (Community) package. Used by the Layer 2 push flow to ensure Layer 2 includes all of Layer 1 as its base.

### 10.2 `layer2-manifest.txt`

Lists additional premium-only paths to add on top of Layer 1:
- `agents/minds/` — Expert mind clones
- `agents/cargo/` — Functional role agents
- `knowledge/dossiers/` — Dossiers
- `knowledge/playbooks/` — Playbooks
- etc.

Has a `LAYER 3 EXCLUSIONS` section that marks paths to skip.

### 10.3 `layer3-manifest.txt`

Lists paths for full backup that are normally gitignored:
- `inbox/`
- `logs/`
- `.claude/sessions/`
- `.claude/mission-control/`
- etc.

Has an `ALWAYS EXCLUDED` section (secrets that never leave the machine).

### 10.4 `layer-rules.yaml`

YAML-formatted rules for automated classification.

---

## 11. Security Controls Summary

### 11.1 Defense in Depth

```
Layer 0: .gitignore
    → Prevents L2/L3/secrets from entering L1 git history
    │
Layer 1: .claude/settings.json deny list
    → Blocks destructive commands (rm -rf, sudo, git push --force, git reset --hard)
    │
Layer 2: pre-publish-gate.js (prepublishOnly)
    → Scans npm pack output for secrets, forbidden files, non-L1 content
    → Fail-CLOSED design (if scan fails, publish is blocked)
    │
Layer 3: validate-package.js
    → Cross-references npm pack files against audit_layers.py classification
    → Any non-L1 file = FAILED
    │
Layer 4: push.js validation
    → Layer-specific checks before git push
    → Secret files always unstaged (safety net)
    │
Layer 5: trufflehog (optional)
    → Deep verified secret scanning if trufflehog is installed
    │
Layer 6: .gitleaks.toml
    → Gitleaks configuration for CI/CD pipeline scanning
```

### 11.2 Credential Management

| Credential | Storage | Access Method |
|-----------|---------|---------------|
| API keys (OpenAI, Voyage, etc.) | `.env` file (gitignored) | `process.loadEnvFile()` |
| Supabase anon key | Hardcoded in `validate-email.js` | Direct (public by design, RLS-protected) |
| MCP server tokens | Shell environment (`~/.zshrc`) | `${ENV_VAR}` syntax in `.mcp.json` |
| GitHub tokens | Shell environment | Git credential helper |
| npm auth | `~/.npmrc` | `npm login` |

### 11.3 Blocked Operations (settings.json)

```json
{
  "deny": [
    "Bash(rm -rf *)",
    "Bash(sudo *)",
    "Bash(chmod 777 *)",
    "Bash(git push --force *)",
    "Bash(git push --force)",
    "Bash(git reset --hard *)"
  ]
}
```

---

## 12. Audit Checklist

### 12.1 Package Integrity

```
[ ] Run `npm pack --dry-run` — verify only L1 files listed
[ ] Run `node bin/validate-package.js` — expect exit 0
[ ] Run `node bin/pre-publish-gate.js` — expect exit 0
[ ] Verify no .env files in npm pack output
[ ] Verify no JWT tokens in npm pack output (except Supabase anon key)
[ ] Verify no agents/minds/ or agents/cargo/ in npm pack output
[ ] Verify no inbox/ or logs/ content in npm pack output
```

### 12.2 Git Remote Security

```
[ ] origin (public) — only L1 content committed
[ ] premium (private) — L1 + L2 only, no L3
[ ] backup (private) — L1 + L2 + L3, but NO secrets (.env, .mcp.json)
[ ] No force-push to origin (blocked by settings.json)
[ ] Force-push to premium/backup only via push.js (with safety net)
```

### 12.3 Supabase Security

```
[ ] Anon key is PUBLIC (expected — protected by RLS)
[ ] validate_buyer_email is an RPC function (not direct table access)
[ ] Rate limited: 3 attempts per session
[ ] 10-second timeout per request
[ ] Input sanitized: trim + lowercase
```

### 12.4 CI/CD

```
[ ] prepublishOnly script runs before every npm publish
[ ] .gitleaks.toml configured for pipeline scanning
[ ] GitHub workflows exist in .github/workflows/
[ ] CODEOWNERS file defines required reviewers
```

### 12.5 File Classification

```
[ ] Run `python3 core/intelligence/audit_layers.py` for full audit
[ ] Review docs/audit/AUDIT-REPORT.json for current classification
[ ] Verify all REVIEW items have been classified
[ ] Verify all DELETE items have been removed
```

---

## Appendix A: File Structure Overview

```
mega-brain/
├── .claude/                    [L1] Claude Code integration
│   ├── CLAUDE.md               [L1] Project instructions
│   ├── hooks/                  [L1] 20+ Python hooks
│   ├── skills/                 [L1] Skill definitions
│   ├── rules/                  [L1] Lazy-loaded rule groups
│   ├── commands/               [L1] Slash commands
│   ├── settings.json           [L1] Hook + permission config
│   ├── sessions/               [L3] Session history (gitignored)
│   └── mission-control/        [L3] Orchestration state (gitignored)
├── agents/
│   ├── conclave/               [L1] Multi-agent templates
│   ├── _templates/             [L1] Agent creation templates
│   ├── constitution/           [L1] Agent governance
│   ├── minds/                  [L2] Expert mind clones (gitignored)
│   ├── cargo/                  [L2] Functional agents (gitignored)
│   └── sua-empresa/            [L3] Company data (gitignored)
├── bin/
│   ├── cli.js                  [L1] Entry point (2 lines)
│   ├── mega-brain.js           [L1] Main CLI (137 lines)
│   ├── push.js                 [L1] Smart push system (1057 lines)
│   ├── pre-publish-gate.js     [L1] Security gate (230 lines)
│   ├── validate-package.js     [L1] Layer validator (191 lines)
│   └── lib/
│       ├── validate-email.js   [L1] Supabase email validation (113 lines)
│       ├── installer.js        [L1] Installation logic
│       ├── setup-wizard.js     [L1] API key configuration
│       ├── ascii-art.js        [L1] CLI visuals
│       └── pro-commands.js     [L1] Premium feature commands
├── core/                       [L1] Processing engine
│   ├── intelligence/           [L1] Python scripts (audit_layers.py, etc.)
│   ├── workflows/              [L1] YAML orchestration
│   ├── schemas/                [L1] JSON schemas
│   └── templates/              [L1] Log and agent templates
├── docs/                       [L1] Documentation
├── knowledge/                  [L2] Knowledge base (gitignored except .gitkeep)
├── inbox/                      [L3] Raw materials (gitignored)
├── logs/                       [L3] Session logs (gitignored)
├── .github/
│   ├── layer1-allowlist.txt    Manifest: L1 paths
│   ├── layer2-manifest.txt     Manifest: L2 paths (premium)
│   ├── layer3-manifest.txt     Manifest: L3 paths (backup)
│   ├── layer-rules.yaml        Classification rules
│   └── workflows/              CI/CD pipelines
├── package.json                npm package definition
├── .gitignore                  L1 distribution rules
├── .gitleaks.toml              Secret scanning config
└── .env                        [NEVER] Credentials (gitignored)
```

---

## Appendix B: Validation Commands

```bash
# Validate npm package contains only L1 content
node bin/validate-package.js

# Validate with JSON output (for CI)
node bin/validate-package.js --json

# Run full layer audit
python3 core/intelligence/audit_layers.py

# Dry-run npm publish (see what would be published)
npm pack --dry-run

# Run pre-publish security gate manually
node bin/pre-publish-gate.js

# Smart push with dry-run
mega-brain push --dry-run --layer 1
mega-brain push --dry-run --layer 2
mega-brain push --dry-run --layer 3
```

---

*Document generated from source code analysis on 2026-03-01.*
*All file paths, line counts, and code excerpts verified against the actual codebase.*
