# Mega Brain - AI Knowledge Management System

## Project Identity
Mega Brain is an AI-powered knowledge management system that transforms expert materials (videos, PDFs, transcriptions) into structured playbooks, DNA schemas, and mind-clone agents.

## Architecture
```
inbox/          -> Raw materials (videos, PDFs, transcriptions)
artifacts/      -> Pipeline stages (chunks, canonical, insights, narratives)
knowledge/      -> Structured knowledge base (dossiers, playbooks, DNA)
agents/         -> AI agents (persons, cargo, council)
system/         -> Protocols, schemas, documentation
.claude/        -> Claude Code integration (hooks, skills, commands)
bin/            -> CLI tools and installer
```

## DNA Schema (5 Knowledge Layers)
| Layer | Name | Description |
|-------|------|-------------|
| L1 | PHILOSOPHIES | Core beliefs and worldview |
| L2 | MENTAL-MODELS | Thinking and decision frameworks |
| L3 | HEURISTICS | Practical rules and decision shortcuts |
| L4 | FRAMEWORKS | Structured methodologies and processes |
| L5 | METHODOLOGIES | Step-by-step implementations |

## Non-Negotiable Rules
1. All credentials in `.env` only — never hardcode API keys
2. Python hooks use `pathlib.Path` for cross-platform compatibility
3. Follow naming conventions: folders=lowercase, configs=SCREAMING-CASE, scripts=snake_case
4. `.env` is gitignored — never commit credentials
5. Run `npx mega-brain-ai setup` for initial configuration

## Configuration
- `.env` is the ONLY source of truth for credentials
- Required: `OPENAI_API_KEY` (Whisper transcription)
- Recommended: `VOYAGE_API_KEY` (semantic search)
- Optional: `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` (Drive import)

## For full documentation, see `.claude/CLAUDE.md`
