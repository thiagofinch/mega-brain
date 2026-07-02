---
name: ingerir-files
description: "Orquestra cadeia completa de ingestao de transcricoes Fireflies (multi-account com dedup) -> /process-jarvis -> founder briefing cruzado com mission.md/north-star.yaml -> entrega via Z-API + Baileys (texto + audio ElevenLabs). Disparavel via terminal local OU via WhatsApp atraves do command_router."
version: "0.2.0"
owner_squad: pipeline-ops
megabrain_tier: Tier2
context: conversation
agent: general-purpose
user-invocable: true
argument-hint: "[mode: dashboard|run|status] [--window-days N]"
status: active
---

# SKILL: /ingerir-files

Pipeline multi-fase Fireflies → /process-jarvis → founder briefing → entrega WhatsApp+áudio.

## Comandos
- `dashboard` — preview calls disponíveis
- `run [--window-days N]` — execução completa
- `status` — estado do sync

## Estrutura
- scripts/ingest.py — entry-point orchestrator
- scripts/state.py — state manager
- scripts/multi_fireflies.py — sync 2 accounts
- scripts/dashboard.py — Fase 1 preview
- scripts/briefing.py — Fase 5 alignment scorer
- scripts/tts_zapi.py — Fase 6 TTS + delivery
- templates/briefing-template.md
- data/alignment-rubric.yaml

## Anchors
- workspace/businesses/{slug}/L0-identity/mission.md
- workspace/businesses/{slug}/L1-strategy/product-vision/north-star.yaml

Disparável via WhatsApp através do command_router com `/ingerir Nd`.
