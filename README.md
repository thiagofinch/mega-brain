<p align="center">
  <img src=".github/assets/banner.svg" alt="Mega Brain" width="100%">
</p>

<h1 align="center">Mega Brain</h1>

<p align="center">
  <strong>AI Knowledge Management System</strong>
  <br>
  Transform expert materials into structured playbooks, DNA schemas, and mind-clone agents.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.3.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/node-%3E%3D18-green?style=for-the-badge&logo=node.js" alt="Node">
  <img src="https://img.shields.io/badge/python-3.10%2B-yellow?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-UNLICENSED-red?style=for-the-badge" alt="License">
</p>

---

## What is Mega Brain?

Mega Brain is a [Claude Code](https://claude.ai/claude-code)-powered system that ingests expert materials — videos, PDFs, transcriptions, podcasts, training courses — and transforms them into structured knowledge. It produces playbooks, DNA schemas, and AI agents that reason with traced evidence.

Built for solo entrepreneurs and small teams who want to operationalize the expertise they have accumulated across dozens of courses, mentors, and resources.

## Quick Start

```bash
# 1. Install dependencies (only in the first run)
npm install

# 2. Install and configure
npx AIOX-GPS-ai setup

# 3. Fill in API keys when prompted (only OPENAI_API_KEY is required)

# 4. Open Claude Code and check system status
/jarvis-briefing
```

Setup auto-triggers on first use if `.env` is missing.

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| [Claude Code](https://claude.ai/claude-code) | Max or Pro plan | Core runtime |
| [Node.js](https://nodejs.org) | >= 18.0.0 | CLI and tooling |
| [Python](https://python.org) | >= 3.10 | Intelligence scripts |

### API Keys

| Key | Purpose | Required? |
|-----|---------|-----------|
| `OPENAI_API_KEY` | Whisper transcription | **Yes** |
| `VOYAGE_API_KEY` | Semantic embeddings (RAG) | Recommended |
| `GOOGLE_CLIENT_ID` | Google Drive import | Optional |

Run `/setup` in Claude Code to configure keys interactively. Keys are stored in `.env` (gitignored).

## Features

### Knowledge Pipeline

- **Ingest** any format — videos, PDFs, transcriptions, podcasts, training courses
- **Extract** structured DNA across 5 knowledge layers (philosophies, mental models, heuristics, frameworks, methodologies)
- **Build** playbooks, dossiers, and theme-based knowledge bases with full source traceability

### AI Agents

- **Mind Clones** — AI agents that reason like specific experts, grounded in their actual materials
- **Cargo Agents** — Functional role agents (Sales, Marketing, Operations, Finance) that synthesize knowledge from multiple sources
- **Conclave** — Multi-agent deliberation sessions with evidence-based debate and structured output

### Developer Experience

- **20+ hooks** for automated validation, session management, and quality control
- **Slash commands** for common operations (`/ingest`, `/save`, `/resume`, `/conclave`)
- **Skill system** with keyword-based auto-routing
- **Session persistence** with auto-save and resume

## Architecture

```
AIOX-GPS/
├── core/           -> Processing engine (tasks, workflows, protocols, schemas)
├── agents/         -> AI agent definitions (conclave, cargo, minds, templates)
├── bin/            -> CLI tools and entry points
├── .claude/        -> Claude Code integration (hooks, skills, commands, rules)
├── knowledge/      -> Knowledge base (playbooks, dossiers, DNA schemas)
├── artifacts/      -> Pipeline processing stages (chunks, insights, narratives)
├── inbox/          -> Raw materials input directory
├── docs/           -> Documentation, PRDs, plans
└── logs/           -> Session and processing logs
```

### Layer System

Content is organized into three distribution layers:

| Layer | Content | Distribution |
|-------|---------|--------------|
| **L1** (Community) | Core engine, templates, hooks, skills, CLI | npm package (public) |
| **L2** (Pro) | Populated knowledge base, mind clones, pipeline | Premium (tracked) |
| **L3** (Personal) | Your materials, sessions, environment config | Local only (gitignored) |

## Community vs Pro

| Feature | Community (L1) | Pro (L2) |
|---------|---------------|----------|
| CLI and setup wizard | Yes | Yes |
| Core engine and templates | Yes | Yes |
| Skills and hooks | Yes | Yes |
| Agent templates and examples | Yes | Yes |
| Populated knowledge base | -- | Yes |
| Mind clone agents | -- | Yes |
| Pipeline processing | -- | Yes |
| Council / Conclave | -- | Yes |

## Commands

Use these slash commands inside Claude Code:

| Command | Description |
|---------|-------------|
| `/jarvis-briefing` | System status and health score |
| `/ingest` | Ingest new material into the pipeline |
| `/process-jarvis` | Run the 5-phase processing pipeline |
| `/conclave` | Multi-agent deliberation session |
| `/save` | Save current session state |
| `/resume` | Resume previous session |
| `/setup` | Environment setup wizard |

## DNA Schema

Knowledge is extracted and structured in 5 layers:

| Layer | Name | Description |
|-------|------|-------------|
| L1 | **Philosophies** | Core beliefs and worldview |
| L2 | **Mental Models** | Thinking and decision frameworks |
| L3 | **Heuristics** | Practical rules and decision shortcuts |
| L4 | **Frameworks** | Structured methodologies and processes |
| L5 | **Methodologies** | Step-by-step implementations |

Every piece of extracted knowledge traces back to its source material with file path, line number, and original context.

## Validation

Verify the package before publishing:

```bash
# Check that only L1 content is in the package
npm run validate:layers

# Full pre-publish gate (secrets scan + layer validation)
node bin/pre-publish-gate.js
```


## Production Deployment

### Frontend Setup

The `frontend/` directory contains a Next.js application.

```bash
# Install dependencies
cd frontend
npm ci

# Run security audit before deploying
npm run security:audit
# Must return ZERO high severity vulnerabilities

# Build for production
npm run build

# Start in production
npm run start
```

### Environment Variables

Copy `.env.example` to `.env` and configure all required variables:

```bash
cp .env.example .env
# Edit .env with your values
```

**Required for production:**
```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_WEBSOCKET_URL=wss://your-api-domain.com/ws
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_SECRET=<generate-random-string>
REDIS_HOST=redis.internal
REDIS_PASSWORD=<secure-password>
```

### Security Hardening

This system includes:

- **CSP** - Strict Content Security Policy with no `unsafe-inline` or `unsafe-eval`
- **CSRF Protection** - Token-based protection on all state-changing endpoints
- **Rate Limiting** - 100 requests/minute per IP
- **Input Validation** - All API endpoints validate and sanitize inputs
- **CORS Whitelist** - Only configured origins can access the API

See [SECURITY-AUDIT.md](SECURITY-AUDIT.md) for the full security assessment.

### Dependency Audit

Check for vulnerabilities before deploying:

```bash
cd frontend
npm audit --audit-level=high

# Fix automatically (safe fixes only)
npm audit fix
```

### Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Step-by-step deployment runbook |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |
| [API.md](API.md) | REST API endpoint documentation |
| [SECURITY-AUDIT.md](SECURITY-AUDIT.md) | Security assessment and findings |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

UNLICENSED — See [package.json](package.json) for details.
