# Directory Contract -- Mega Brain

> **Version:** 4.0.0
> **Source of Truth:** `core/paths.py`
> **Enforcement:** `.claude/hooks/directory_contract_guard.py` (PreToolUse, WARN)
> **Keywords:** "directory", "output", "path", "onde salvar", "where to save", "bucket"
> **Last Updated:** 2026-03-13 (S13 workspace restructure -- ClickUp mirror + businesses DNA)

---

## 1. Knowledge Architecture (3 Buckets)

Three knowledge buckets, each with its own inbox and processed subdirectories.
Bucket 2 was split from the old `workspace/` into `knowledge/business/` (descriptive)
while `workspace/` became the prescriptive operations layer.

```
knowledge/
├── external/       <- Bucket 1: Expert Knowledge (L2)
│   │                  Courses, podcasts, masterminds, books
│   ├── inbox/          -> Raw expert materials (person/type organized)
│   ├── dna/            -> DNA schemas per person (5 layers)
│   │   └── persons/        -> One subdir per expert (alex-hormozi/, cole-gordon/, ...)
│   ├── dossiers/       -> Person + theme dossiers
│   │   ├── persons/        -> DOSSIER-{PERSON}.md
│   │   └── themes/         -> DOSSIER-{THEME}.md
│   ├── playbooks/      -> Actionable playbooks
│   └── sources/        -> Source compilations (per-expert, per-theme)
│
├── business/       <- Bucket 2: Company Operations (L3 except scaffold)
│   │                  Calls, meetings, internal docs, team collaboration
│   ├── inbox/          -> Raw business materials (pre-processing staging)
│   ├── people/         -> Collaborative DNA clones (team members, partners)
│   ├── dossiers/       -> Company + operation + theme dossiers
│   ├── insights/       -> Meeting insights (by-meeting, by-person, by-theme)
│   ├── narratives/     -> Connected stories across meetings/events
│   ├── decisions/      -> Strategic decisions (manual entry)
│   └── sops/           -> Auto-detected process drafts (promoted to workspace/_templates/)
│
└── personal/       <- Bucket 3: Founder Cognitive (L3 ONLY)
    │                  Private thought, personal comms, reflections
    ├── inbox/          -> Raw personal materials
    ├── calls/          -> Call transcripts
    ├── messages/       -> WhatsApp/Slack exports
    ├── email/          -> Email digests
    └── cognitive/      -> Mental models, reflections, journal
```

### Bucket Flow Summary

| Bucket | Input Source | Output Destination | Agent Type |
|--------|-------------|-------------------|------------|
| External | Courses, podcasts, books | `agents/external/` | Expert mind clones |
| Business | Calls, meetings, docs | `agents/business/` | Collaborator clones |
| Personal | Notes, messages, email | `agents/personal/` | Founder clone |

---

## 2. Workspace (Prescriptive Strata — ClickUp Mirror)

Workspace is NOT a knowledge bucket. It is the prescriptive operations layer:
how the company SHOULD function. L1 when template scaffolding, L2 when populated
with real business data. Structure mirrors ClickUp spaces for 1:1 mapping.

Scaffold template: `core/templates/workspace/WORKSPACE-SCAFFOLD.yaml`
ClickUp IDs: `workspace/_system/CLICKUP-IDS.json`

```
workspace/                      <- PRESCRIPTIVE -- how the company SHOULD function
├── workspace.yaml              -> Manifest (workspace identity + metadata)
├── structure.yaml              -> Org structure definition
├── relationships.yaml          -> Business relationships map
├── MASTER-INDEX.md             -> General workspace index
│
├── _system/                    -> Internal config, IDs, references
│   ├── config/
│   ├── _ref/
│   ├── CLICKUP-IDS.json
│   └── DRIVE-FOLDER-IDS.json
├── _templates/                 -> Validated SOPs (promoted from knowledge/business/sops/)
├── inbox/                      -> Triage staging area
│
├── businesses/                 -> Strategic DNA per Business Unit (12 folders each)
│   └── {bu}/                       -> bilhon/, clickmax/, furion-ai/, ...
│       ├── _preserved/             -> Backups, previous versions
│       ├── ai/                     -> AI agents, prompts, automations
│       ├── analytics/              -> Dashboards, KPIs, metrics
│       ├── brand/                  -> Identity, guidelines, voice
│       ├── company/                -> Context, state, corporate docs
│       ├── copy/                   -> Sales copy, landing pages, emails
│       ├── design-system/          -> Tokens, components, design guidelines
│       ├── evidence/               -> Cases, social proof, testimonials
│       ├── movement/               -> Brand narrative, manifesto, community
│       ├── operations/             -> SOPs, processes, playbooks
│       ├── products/               -> Specs, features, roadmap
│       └── tech/                   -> Stack, architecture, configs
│
├── aios/                       -> Space: AI Management (ClickUp 901313609429)
│   ├── squads/
│   ├── agents/
│   ├── tasks/
│   ├── checklists/
│   ├── templates/
│   ├── tools/
│   ├── knowledge/
│   ├── workflows/
│   └── library/
│
├── ops/                        -> Space: Bilhon Ops (ClickUp 901313609435)
│   ├── processos-sops/
│   │   ├── templates-de-tarefas/
│   │   └── gestao-de-processos/
│   ├── meetings/               -> Meeting dossiers (from pipeline)
│   ├── eventos/                -> Business events
│   └── sprints/
│       ├── backlog/
│       └── sprint-atual/
│
├── delivery/                   -> Space: Delivery (ClickUp 901313609439)
│   ├── prospeccao-leads/
│   ├── gestao-projetos/
│   ├── copy/
│   ├── edicao/
│   ├── producao-filmagem/
│   ├── account-cs/
│   ├── genai/
│   ├── content-factory/
│   ├── trafego-pago/
│   └── (each with operational subfolders)
│
├── comercial/                  -> Space: Comercial (ClickUp 901313609444)
│   └── crm/
│       ├── pipeline-sdr/
│       ├── pipeline-closer/
│       ├── clientes/
│       ├── parceiros/
│       ├── people/
│       └── propostas-comerciais/
│
├── gestao/                     -> Space: Gestao (ClickUp 901313609445)
│   ├── juridico/
│   ├── financeiro/
│   ├── administrativo/
│   └── acessos-ferramentas/
│
├── gente-cultura/              -> Space: Gente & Cultura (ClickUp 901313609446)
│   ├── okrs/
│   ├── recrutamento/
│   ├── equipe/                 -> SOWs, TAs, scorecards, ORGANOGRAM
│   └── educacional/
│
├── marketing/                  -> Space: Marketing (ClickUp 901313609456)
│   ├── performance-growth/
│   ├── campanhas-lancamentos/
│   └── creative-library/
│
└── strategy/                   -> Strategic documents (no ClickUp equivalent)
    └── decisions/
```

### Workspace vs Business Bucket

| Aspect | `workspace/` | `knowledge/business/` |
|--------|-------------|----------------------|
| Nature | Prescriptive (how things SHOULD work) | Descriptive (what actually happened) |
| Content | SOPs, org charts, strategy, config | Meeting notes, call transcripts, insights |
| Updates | Manual / deliberate | Automatic / pipeline-driven |
| Git | Tracked (L1 template, L2 populated) | Gitignored (L3 runtime data) |
| Analogy | Company handbook | Company diary |

### Businesses DNA vs Delivery Operations

| Aspect | `businesses/{bu}/` | `delivery/` space |
|--------|-------------------|-------------------|
| Nature | Strategic DNA per business unit | Day-to-day operational tracking |
| Content | Brand, copy, design-system, analytics | Task queues, sprints, delivery pipelines |
| Updates | Deliberate (strategic decisions) | Constant (daily operations) |
| Analogy | Birth certificate of the business | Daily agenda of the business |

---

## 3. Agent Categories (5 Types + Support)

Agents are organized by knowledge source, not by function.

```
agents/
├── external/       <- Expert mind clones (fed by knowledge/external/)
│   └── {person}/       -> alex-hormozi/, cole-gordon/, jeremy-miner/, ...
│       ├── AGENT.md
│       ├── SOUL.md
│       ├── MEMORY.md
│       └── DNA-CONFIG.yaml
│
├── business/       <- Collaborator clones (fed by knowledge/business/)
│   └── {person}/       -> Team members, partners
│
├── personal/       <- Founder clone (fed by knowledge/personal/ + all sources)
│   └── {founder}/
│
├── cargo/          <- Functional roles (hybrid -- multiple DNA sources)
│   ├── c-level/        -> CFO, CRO, CMO, COO, ...
│   ├── sales/          -> CLOSER, SDR, ...
│   ├── marketing/      -> COPYWRITER, MEDIA-BUYER, ...
│   └── operations/     -> OPS-MANAGER, ...
│
├── system/         <- Infrastructure agents
│   └── conclave/, boardroom/, jarvis/, ...
│
├── discovery/      <- Auto-generated role tracking
│   └── role-tracking.md
│
├── sua-empresa/    <- Company-specific agent outputs
│   └── sow/            -> Statements of Work
│
├── constitution/   <- Governance rules for agent behavior
│
└── _templates/     <- Agent creation templates
    └── TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md
```

### Agent Type Matrix

| Type | Source Bucket | DNA Weight | Voice | Example |
|------|-------------|------------|-------|---------|
| External | `knowledge/external/` | 1.0 (single source) | Expert's own voice | Alex Hormozi |
| Business | `knowledge/business/` | 1.0 (single source) | Collaborator's voice | Team member |
| Personal | `knowledge/personal/` + all | 1.0 (founder) | Founder's voice | Thiago |
| Cargo | Multiple buckets | 0.0-1.0 (weighted) | Role-appropriate hybrid | CFO, CRO |
| System | N/A (config-driven) | N/A | System voice | JARVIS, Conclave |

---

## 4. All Directories and Purpose

| Directory | Category | What Belongs | Git Status |
|-----------|----------|-------------|------------|
| `core/` | Engine | tasks, workflows, intelligence, paths.py, templates | Tracked (L1) |
| `agents/external/` | Expert Agents | Mind clones of external experts | Tracked (L2) |
| `agents/business/` | Business Agents | Collaborator clones | Tracked (L2) |
| `agents/personal/` | Personal Agents | Founder clone | Gitignored (L3) |
| `agents/cargo/` | Cargo Agents | Functional role hybrids | Tracked (L2) |
| `agents/system/` | System Agents | Conclave, boardroom, JARVIS | Tracked (L1) |
| `agents/discovery/` | Agent Discovery | Auto-generated role tracking | Gitignored (L3) |
| `agents/sua-empresa/` | Company Agents | SOW generation outputs | Tracked (L2) |
| `agents/_templates/` | Templates | Agent creation templates (V3) | Tracked (L1) |
| `agents/constitution/` | Governance | Agent behavior rules | Tracked (L1) |
| `reference/` | Documentation | Guides, protocols, templates | Tracked (L1) |
| `bin/` | CLI Tools | npm executables | Tracked (L1) |
| `system/` | System Config | JARVIS state, DNA, soul | Tracked (L1) |
| `.planning/` | GSD Plans | Phases, roadmap, state | Tracked (L1) |
| `.claude/` | Config + Runtime | Hooks, skills, commands, rules | Tracked (L1) |
| `workspace/` | Operations | Prescriptive business structure | Tracked (L1 template, L2 populated) |
| `knowledge/external/` | Bucket 1 | Expert dna, dossiers, playbooks | Tracked (L2) |
| `knowledge/business/` | Bucket 2 | Company operations data | Gitignored (L3 except scaffold) |
| `knowledge/personal/` | Bucket 3 | Cognitive, email, calls | Gitignored (L3) |
| `artifacts/` | Generated Output | Audit reports, validation | Gitignored (L3) |
| `logs/` | Session Logs | Batches, JSONL audit trails | Gitignored (L3) |
| `processing/` | Pipeline Artifacts | Speakers, entities, diarization | Gitignored (L3) |
| `research/` | Ad-hoc Analysis | Blueprints, deep-dives | Gitignored (L3) |
| `.data/` | Indexes | RAG, knowledge graph, embeddings | Gitignored (L3) |

---

## 5. Output Routing (who writes where)

All routing constants are defined in `core/paths.py` via the `ROUTING` dict.
Scripts MUST use these constants instead of hardcoding paths.

### Audit and Validation

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| `audit_layers.py` | `artifacts/audit/` | `ROUTING["audit_report"]` |
| `validate_layers.py` | `artifacts/audit/` | `ROUTING["audit_report"]` |

### Session and State

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| `session_autosave_v2.py` | `.claude/sessions/` | `ROUTING["session_log"]` |
| `skill_indexer.py` | `.claude/mission-control/` | `ROUTING["skill_index"]` |
| Mission state updates | `.claude/mission-control/` | `ROUTING["mission_state"]` |
| Pipeline state | `.claude/mission-control/` | `ROUTING["pipeline_state"]` |
| Phase gate state | `.claude/mission-control/PHASE-GATE-STATE.json` | `ROUTING["phase_gate_state"]` |
| Discovery state | `.claude/mission-control/DISCOVERY-STATE.json` | `ROUTING["discovery_state"]` |
| Read.ai state | `.claude/mission-control/READ-AI-STATE.json` | `ROUTING["read_ai_state"]` |

### Logs (append-only JSONL)

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| `post_batch_cascading.py` | `logs/batches/` | `ROUTING["batch_log"]` |
| `stop_hook_completeness.py` | `logs/handoffs/` | `ROUTING["handoff"]` |
| Cascade log | `logs/` | `ROUTING["cascade_log"]` |
| Tool usage log | `logs/` | `ROUTING["tool_usage"]` |
| Quality gaps log | `logs/` | `ROUTING["quality_gaps"]` |
| Dossier trigger log | `logs/` | `ROUTING["dossier_trigger"]` |
| Bucket processing log | `logs/bucket-processing/` | `ROUTING["bucket_processing"]` |
| Autonomous log | `logs/` | `ROUTING["autonomous_log"]` |
| Agent creation log | `logs/agent-creation.jsonl` | `ROUTING["agent_creation_log"]` |
| Read.ai harvest log | `logs/read-ai-harvest/` | `ROUTING["read_ai_log"]` |

### Knowledge and RAG

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| `chunker.py` | `.data/rag_expert/` | `ROUTING["rag_chunks"]` |
| Vector embeddings | `.data/rag_expert/` | `ROUTING["rag_vectors"]` |
| `graph_builder.py` | `.data/knowledge_graph/` | `ROUTING["graph"]` |
| `memory_splitter.py` | `knowledge/external/dna/persons/` | `ROUTING["memory_split"]` |
| `nav_map_builder.py` | `knowledge/external/` | `ROUTING["nav_map"]` |

### Processing Pipeline

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| Entity registry | `processing/` | `ROUTING["entity_registry"]` |
| Speaker detection | `processing/` | `ROUTING["speakers"]` |
| Diarization | `processing/` | `ROUTING["diarization"]` |
| Voice embeddings | `.data/voice_embeddings/` | `ROUTING["voice_embeddings"]` |
| Read.ai staging | `processing/read-ai-staging/` | `ROUTING["read_ai_staging"]` |

### Agent Outputs

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| `sow_generator.py` | `agents/sua-empresa/sow/` | `ROUTING["sow_output"]` |
| Generated skills | `.claude/skills/` | `ROUTING["generated_skill"]` |
| Role tracking | `agents/discovery/role-tracking.md` | `ROUTING["role_tracking"]` |
| Agent creation trigger | `agents/discovery/` | `ROUTING["discovery_state"]` |

### Downloads and Inboxes

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| `organized_downloader.py` | `workspace/inbox/` | `ROUTING["download"]` |
| External inbox | `knowledge/external/inbox/` | `ROUTING["external_inbox"]` |
| Business inbox | `knowledge/business/inbox/` | `ROUTING["business_inbox"]` |
| Personal inbox | `knowledge/personal/inbox/` | `ROUTING["personal_inbox"]` |
| Workspace inbox | `workspace/inbox/` | `ROUTING["workspace_inbox"]` |

### Workspace Strata

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| Workspace data (general) | `workspace/` | `ROUTING["workspace_data"]` |
| Businesses | `workspace/businesses/` | `ROUTING["workspace_businesses"]` |
| Domains | `workspace/domains/` | `ROUTING["workspace_domains"]` |
| Templates (promoted SOPs) | `workspace/_templates/` | `ROUTING["workspace_templates"]` |
| Providers | `workspace/providers/` | `ROUTING["workspace_providers"]` |
| Strategy | `workspace/strategy/` | `ROUTING["workspace_strategy"]` |
| Events | `workspace/events/` | `ROUTING["workspace_events"]` |
| Org structure | `workspace/org/` | `ROUTING["workspace_org"]` |
| Team data | `workspace/team/` | `ROUTING["workspace_team"]` |
| Finance | `workspace/finance/` | `ROUTING["workspace_finance"]` |
| Meetings | `workspace/meetings/` | `ROUTING["workspace_meetings"]` |
| Automations | `workspace/automations/` | `ROUTING["workspace_automations"]` |
| Tools | `workspace/tools/` | `ROUTING["workspace_tools"]` |

### Business Bucket

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| Business people | `knowledge/business/people/` | `ROUTING["business_people"]` |
| Business dossiers | `knowledge/business/dossiers/` | `ROUTING["business_dossiers"]` |
| Business insights | `knowledge/business/insights/` | `ROUTING["business_insights"]` |
| Business narratives | `knowledge/business/narratives/` | `ROUTING["business_narratives"]` |
| Business decisions | `knowledge/business/decisions/` | `ROUTING["business_decisions"]` |
| Business SOPs | `knowledge/business/sops/` | `ROUTING["business_sops"]` |

### Personal Bucket

| Script/Hook | Writes To | ROUTING Key |
|-------------|-----------|-------------|
| Personal data (general) | `knowledge/personal/` | `ROUTING["personal_data"]` |
| Email | `knowledge/personal/email/` | `ROUTING["personal_email"]` |
| Messages | `knowledge/personal/messages/` | `ROUTING["personal_messages"]` |
| Calls | `knowledge/personal/calls/` | `ROUTING["personal_calls"]` |
| Cognitive | `knowledge/personal/cognitive/` | `ROUTING["personal_cognitive"]` |

### Agent Category Routing

| Agent Type | Writes To | ROUTING Key |
|------------|-----------|-------------|
| External agents | `agents/external/` | `ROUTING["agents_external"]` |
| Business agents | `agents/business/` | `ROUTING["agents_business"]` |
| Personal agents | `agents/personal/` | `ROUTING["agents_personal"]` |
| System agents | `agents/system/` | `ROUTING["agents_system"]` |
| Cargo agents | `agents/cargo/` | `ROUTING["agents_cargo"]` |

### Reference Documents

| Document | Path | ROUTING Key |
|----------|------|-------------|
| Architecture doc | `reference/MEGABRAIN-3D-ARCHITECTURE.md` | `ROUTING["architecture_doc"]` |
| Implementation log | `reference/IMPLEMENTATION-LOG.md` | `ROUTING["implementation_log"]` |
| Onboarding guide | `reference/ONBOARDING-GUIDE.md` | `ROUTING["onboarding_guide"]` |
| UX by area | `workspace/org/UX-BY-AREA.md` | `ROUTING["ux_by_area"]` |

### Log Templates (L1 -- mechanism, not data)

| Template | Path | ROUTING Key |
|----------|------|-------------|
| Workspace log template | `core/templates/logs/WORKSPACE-LOG-TEMPLATE.md` | `ROUTING["workspace_log_template"]` |
| Personal log template | `core/templates/logs/PERSONAL-LOG-TEMPLATE.md` | `ROUTING["personal_log_template"]` |

### Trash (never delete, always move here)

| Operation | Path | ROUTING Key |
|-----------|------|-------------|
| Soft delete | `.claude/trash/` | `ROUTING["trash"]` |

---

## 6. RAG Isolation

Each knowledge bucket has its own isolated RAG index to prevent cross-contamination.

| Bucket | RAG Index Path | paths.py Constant | Content |
|--------|---------------|-------------------|---------|
| External (experts) | `.data/rag_expert/` | `RAG_EXPERT` | Expert courses, frameworks, methodologies |
| Business (company) | `.data/rag_business/` | `RAG_BUSINESS` | Meeting insights, call transcripts, SOPs |
| Personal (founder) | `knowledge/personal/index/` | via `KNOWLEDGE_PERSONAL` | Private reflections, personal notes |

### RAG Query Routing

| Query Type | Primary Index | Fallback |
|------------|--------------|----------|
| "What does Hormozi say about X?" | `rag_expert` | None |
| "What happened in last week's meeting?" | `rag_business` | None |
| "What did I think about X?" | `rag_personal` | None |
| "How should we structure sales?" | `rag_expert` | `rag_business` |
| Cross-expert synthesis | `rag_expert` (graph-enhanced) | None |

---

## 7. Prohibitions

| What | Why | Use Instead |
|------|-----|-------------|
| `docs/` | Deprecated directory | `reference/` |
| `knowledge/` root files | Must go into a specific bucket | `external/`, `business/`, or `personal/` |
| `{company}/` at root | Old company dir, migrated | `workspace/businesses/{company}/` |
| `inbox/` at root | Distributed to bucket inboxes (S03) | `knowledge/{bucket}/inbox/` or `workspace/inbox/` |
| `workspace/domains/` | Removed S13: replaced by departmental spaces | `workspace/{space}/` (aios, ops, delivery, etc.) |
| `workspace/providers/` | Removed S13: replaced by gestao subfolder | `workspace/gestao/acessos-ferramentas/` |
| `workspace/team/` | Removed S13: migrated to gente-cultura | `workspace/gente-cultura/equipe/` |
| `workspace/finance/` | Removed S13: migrated to gestao | `workspace/gestao/financeiro/` |
| `workspace/meetings/` | Removed S13: migrated to ops | `workspace/ops/meetings/` |
| `workspace/org/` | Removed S13: migrated to gestao | `workspace/gestao/administrativo/` |
| `workspace/automations/` | Removed S13: migrated to aios | `workspace/aios/workflows/` |
| `workspace/tools/` | Removed S13: migrated to gestao | `workspace/gestao/acessos-ferramentas/` |
| Company files at workspace root | Must go into businesses/{bu}/company/ | `workspace/businesses/bilhon/company/` |
| New top-level dirs | Filesystem contract violation | Update this contract first |
| Hardcoded paths in scripts | Breaks when dirs move | Import from `core/paths.py` |
| L3 data in L1/L2 | Security / privacy leak | Keep in gitignored dirs only |
| Agent files outside `agents/` | Breaks agent discovery | Use appropriate `agents/{type}/` |
| SOPs directly in `workspace/_templates/` | Must be validated first | Start in `knowledge/business/sops/`, promote when validated |

---

## 8. How to Use

### Python Scripts

```python
from core.paths import (
    ROUTING,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_PERSONAL,
    WORKSPACE,
    AGENTS_EXTERNAL,
    AGENTS_CARGO,
)

# Correct: use constants from paths.py
output = ROUTING["audit_report"] / "report.json"
dna_path = KNOWLEDGE_EXTERNAL / "dna" / "persons" / "alex-hormozi"
workspace = ROUTING["workspace_businesses"] / "acme-edu"
meeting = ROUTING["business_insights"] / "by-meeting" / "MEET-0001.md"

# Correct: agent routing
new_agent = AGENTS_EXTERNAL / "jeremy-haynes" / "AGENT.md"
cargo_agent = AGENTS_CARGO / "sales" / "closer" / "AGENT.md"

# WRONG: hardcoded paths (will break on reorganization)
output = Path("knowledge/dna/persons/alex-hormozi")     # PROHIBITED (stale)
output = Path("agents/external/alex-hormozi")             # PROHIBITED (hardcoded)
output = Path("inbox/raw-file.txt")                      # PROHIBITED (root inbox removed)
```

### Decision Tree: Where Does This File Go?

```
Is it RAW, unprocessed material?
├── YES -> Which bucket?
│   ├── Expert content (course, podcast, book) -> knowledge/external/inbox/
│   ├── Company content (meeting, call, doc)   -> knowledge/business/inbox/
│   ├── Personal content (note, message, email)-> knowledge/personal/inbox/
│   └── Not sure                               -> workspace/inbox/ (triage later)
│
└── NO, it is PROCESSED output ->
    ├── DNA schema?                -> knowledge/external/dna/persons/{person}/
    ├── Dossier about a person?    -> knowledge/external/dossiers/persons/
    ├── Dossier about a theme?     -> knowledge/external/dossiers/themes/
    ├── Meeting insight?           -> knowledge/business/insights/
    ├── Detected SOP?             -> knowledge/business/sops/
    ├── Validated SOP (promoted)?  -> workspace/_templates/
    ├── Agent file?               -> agents/{type}/{name}/
    ├── Audit/validation report?   -> artifacts/audit/
    ├── Log file?                 -> logs/{category}/
    ├── RAG index data?           -> .data/{rag_bucket}/
    └── Org/strategy doc?         -> workspace/{appropriate_subdir}/
```

---

## 9. Layer System

| Layer | Content | Git Status | Examples |
|-------|---------|------------|----------|
| L1 (Community) | Engine, templates, config | Tracked (npm package) | `core/`, `.claude/`, `bin/`, `agents/_templates/` |
| L2 (Pro) | Populated knowledge + agents | Tracked (premium) | `knowledge/external/`, `agents/external/`, `agents/cargo/` |
| L3 (Personal) | Runtime data, private content | Gitignored | `.data/`, `knowledge/personal/`, `knowledge/business/`, `logs/` |

---

## 10. SOP Promotion Flow

Auto-detected SOPs follow a validation pipeline before becoming official templates.

```
knowledge/business/sops/     (auto-detected, draft)
        |
        v  [human review + validation]
        |
workspace/_templates/         (promoted, official)
```

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-12-01 | Initial contract |
| 2.0.0 | 2026-03-05 | Added workspace at root, 3-bucket architecture |
| 3.0.0 | 2026-03-09 | S12 full rewrite: knowledge/business/ bucket, agent categories (5 types), workspace strata, 76+ routing keys, SOP promotion flow, decision tree |
| 4.0.0 | 2026-03-13 | S13 workspace restructure: 7 departmental spaces (ClickUp mirror), businesses DNA (12 folders per BU), removed flat dirs (domains, providers, team, finance, org, meetings, automations, tools), 100+ routing keys, WORKSPACE-SCAFFOLD.yaml template, CLICKUP-IDS.json |
