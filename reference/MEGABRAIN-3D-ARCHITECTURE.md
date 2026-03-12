# Mega Brain 3D — Architecture

> **Version:** 1.0.0 | **Date:** 2026-03-07
> **paths.py:** `ROUTING["architecture_doc"]`

---

## Three Dimensions of Context

```
                         MEGA BRAIN 3D
                              |
          +-------------------+-------------------+
          |                   |                   |
    EXTERNAL (B1)       WORKSPACE (B2)      PERSONAL (B3)
    Expert Knowledge    Business Data       Cognitive Layer
    L1/L2               L1 template/L2      L3 ONLY
          |                   |                   |
    knowledge/external/  workspace/         knowledge/personal/
```

## Source Tree

```
mega-brain/
├── knowledge/
│   ├── external/              B1: Expert Knowledge (L2)
│   │   ├── dna/                  DNA schemas per person
│   │   ├── dossiers/             Person + theme dossiers
│   │   │   ├── persons/
│   │   │   ├── themes/
│   │   │   └── system/
│   │   ├── playbooks/            Actionable playbooks
│   │   ├── sources/              Raw organized by expert
│   │   │   ├── alex-hormozi/
│   │   │   ├── cole-gordon/
│   │   │   ├── jeremy-haynes/
│   │   │   ├── jeremy-miner/
│   │   │   └── ...
│   │   └── inbox/                Entry point for expert materials
│   │       ├── documents/
│   │       ├── pdfs/
│   │       ├── transcriptions/
│   │       └── videos/
│   │
│   └── personal/              B3: Cognitive Layer (L3 ONLY)
│       ├── email/                Processed email digests
│       ├── messages/             WhatsApp, Telegram
│       ├── calls/                Personal call transcripts
│       ├── cognitive/            Journal, reflections, mental models
│       └── inbox/                Entry point for personal materials
│           ├── calls/
│           ├── email/
│           ├── notes/
│           ├── voice-memos/
│           └── whatsapp/
│
├── workspace/                 B2: Business Intelligence (ROOT level)
│   ├── org/                      Organization structure
│   ├── team/                     Job descriptions, roles, employee clones
│   ├── finance/                  DRE, KPIs, cash flow, budget
│   ├── meetings/                 Meeting transcripts by area
│   ├── automations/              N8N workflows, integrations
│   ├── tools/                    Tool configs, connector specs
│   │   ├── SLACK-CONNECTOR.md
│   │   ├── MEETING-RECORDER-DECISION.md
│   │   └── FINANCE-CONNECTORS.md
│   └── inbox/                    Entry point for business materials
│       ├── calls/
│       ├── documents/
│       ├── financial/
│       ├── meetings/
│       └── slack/
│
├── core/paths.py              Machine-readable directory contract
├── core/intelligence/
│   └── pipeline/
│       └── bucket_processor.py   Unified 3-bucket processor
└── .data/
    ├── rag_expert/               RAG index for B1 (external only)
    └── rag_business/             RAG index for B2 (workspace only)
```

## Pipeline Architecture

**Decision:** Single pipeline with conditional branches (documented in `core/PIPELINE-ARCHITECTURE-DECISION.md`).

```
Material arrives → inbox/{bucket}/ → bucket_processor.py classifies → destination subdir
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
              external branch       workspace branch      personal branch
              (5-phase JARVIS)      (normalize+classify)  (sanitize+classify)
                    |                     |                     |
              knowledge/external/   workspace/{subdir}/   knowledge/personal/{subdir}/
                    |                     |                     |
              .data/rag_expert/     .data/rag_business/   NEVER indexed
```

## Layer Security

| Layer | What | Git | RAG Index | Council Access |
|-------|------|-----|-----------|----------------|
| L1 | Templates, structure, mechanisms | Tracked | N/A | Always |
| L2 | Expert content, populated workspace | Tracked (premium) | rag_expert, rag_business | Via mode |
| L3 | Personal data, .env, sessions | Gitignored | Never | full-3d only |

**Enforcement:**
- `.gitignore` whitelist pattern (default-deny)
- `knowledge/personal/.gitignore` blocks everything except .gitignore and index.md
- RAG indexes are bucket-isolated: `rag_expert` (B1), `rag_business` (B2), personal never indexed
- Council modes control access: `expert-only`, `business`, `full-3d`, `personal`, `company-only`
- AGENT-INDEX.yaml declares `bucket: [...]` per agent

## Council Modes

| Mode | B1 (External) | B2 (Workspace) | B3 (Personal) |
|------|:---:|:---:|:---:|
| `expert-only` | Yes | - | - |
| `business` | Yes | Yes | - |
| `full-3d` | Yes | Yes | Yes |
| `personal` | - | - | Yes |
| `company-only` | - | Yes | - |

When a bucket is unavailable, agents MUST declare: "This response does not consider [bucket] data."

## Path Contract

Every directory and file location is defined in `core/paths.py`. No script should hardcode paths.

```python
from core.paths import (
    WORKSPACE, WORKSPACE_ORG, WORKSPACE_FINANCE,
    KNOWLEDGE_EXTERNAL, KNOWLEDGE_PERSONAL,
    PERSONAL_COGNITIVE, PERSONAL_EMAIL,
    ROUTING
)
```
