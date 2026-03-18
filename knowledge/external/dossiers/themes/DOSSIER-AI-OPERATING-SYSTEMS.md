# DOSSIER: AI OPERATING SYSTEMS (AIOS)

> **Version:** 1.0.0
> **Created:** 2026-03-12
> **Last Updated:** 2026-03-12
> **Primary Source:** Liam Ottley (LO-001, LO-002, LO-003)
> **Contributing Sources:** (Pending — cross-reference as more sources are processed)

---

## DEFINITION

An AI Operating System (AIOS) is a comprehensive AI-powered layer that wraps around an
existing business model to automate operations, augment decision-making, and free founder
bandwidth. It is NOT a chatbot, NOT a single automation tool, and NOT a workflow builder.
It is an integrated system that understands the business fully (context), connects to all
data sources (data), synthesizes information (intelligence), takes action (automate), and
creates new capabilities (build).

The term was coined and popularized by **Liam Ottley** of Morningside AI, who describes
AIOS as "the third major shift" in business history:

```
Industrial Revolution  →  changed how we MAKE
Internet               →  changed how we REACH
AIOS                   →  changes how we RUN
```

---

## THE 5-LAYER ARCHITECTURE

The AIOS is built in 5 concentric layers. Each layer wraps around the business model and
compounds on the previous layer. The order is critical — skipping layers creates fragile systems.

```
                    ┌─────────────────────────────────────────┐
                    │            LAYER 5: BUILD               │
                    │     Create new capabilities              │
                    │  ┌─────────────────────────────────┐    │
                    │  │       LAYER 4: AUTOMATE          │    │
                    │  │     Act on intelligence           │    │
                    │  │  ┌─────────────────────────┐     │    │
                    │  │  │   LAYER 3: INTELLIGENCE  │     │    │
                    │  │  │   Make sense of data      │     │    │
                    │  │  │  ┌───────────────────┐   │     │    │
                    │  │  │  │  LAYER 2: DATA     │   │     │    │
                    │  │  │  │  Connect sources   │   │     │    │
                    │  │  │  │  ┌─────────────┐  │   │     │    │
                    │  │  │  │  │ L1: CONTEXT  │  │   │     │    │
                    │  │  │  │  │  Understand  │  │   │     │    │
                    │  │  │  │  │  the biz     │  │   │     │    │
                    │  │  │  │  └─────────────┘  │   │     │    │
                    │  │  │  └───────────────────┘   │     │    │
                    │  │  └─────────────────────────┘     │    │
                    │  └─────────────────────────────────┘    │
                    └─────────────────────────────────────────┘
```

### Layer Details

| Layer | Name | Purpose | Implementation | Failure Mode |
|-------|------|---------|---------------|-------------|
| L1 | **Context** | System understands the business | CLAUDE.md, context files, SOPs, team docs | AI gives generic, wrong answers |
| L2 | **Data** | System connects to reality | MCP servers, APIs, database connections | AI is blind to what is happening |
| L3 | **Intelligence** | System synthesizes understanding | RAG pipeline, knowledge graph, analytics | AI has data but no insight |
| L4 | **Automate** | System takes action | Skills, cron jobs, webhooks, agent actions | AI understands but cannot act |
| L5 | **Build** | System creates new capabilities | Epic cycles, development pipeline, self-improvement | System is static, cannot evolve |

---

## THREE KPIs OF AIOS

An AIOS is measured by exactly three KPIs. If all three are improving month over month,
the system is working. If any is flat or declining, there is a specific layer failure.

| KPI | What It Measures | Target | Diagnostic |
|-----|-----------------|--------|------------|
| **Away-From-Desk Autonomy** | Can the business run without the founder physically present? | Full day from phone | If NO: Layer 4 (Automate) or Layer 6 (Mobile Bridge) has gaps |
| **Task Automation %** | What fraction of operational tasks are handled by AI? | 60-70% within 30 days | If LOW: Layer 1 (Context) incomplete or Task Audit not done |
| **Revenue Per Employee** | How much output does each human produce with AI leverage? | Increasing month/month | If FLAT: AI workforce not deployed effectively |

---

## CLAUDE CODE AIOS STACK

Liam's specific technology stack for AIOS implementation:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CLAUDE CODE AIOS STACK                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ENGINE:   Claude Code                                                       │
│            AI reasoning + execution layer                                    │
│            Complex multi-step tasks, code gen, file management               │
│                                                                              │
│  CONTEXT:  CLAUDE.md + structured context files                              │
│            Business rules, SOPs, team info, product details                  │
│            Loaded at session start, referenced throughout                    │
│                                                                              │
│  DATA:     MCP servers                                                       │
│            Typed interfaces to external systems                              │
│            CRM, email, calendar, analytics, databases                        │
│                                                                              │
│  SKILLS:   Claude Code skills                                                │
│            Reusable capabilities triggered by keywords/commands              │
│            /daily-brief, /process-inbox, /source-sync                        │
│                                                                              │
│  CRON:     Scheduled tasks                                                   │
│            Automated recurring actions on schedule                           │
│            Daily briefs, weekly reports, inbox processing                    │
│                                                                              │
│  MOBILE:   Telegram bot                                                      │
│            Mobile command interface (away-from-desk bridge)                  │
│            Send commands, receive updates, approve decisions                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## MAPPING TO MEGA BRAIN

Mega Brain has independently built an AIOS that maps almost 1:1 to Liam's architecture.
This table documents the equivalences:

| Liam's Layer | Liam's Implementation | Mega Brain Equivalent | Status |
|-------------|----------------------|----------------------|--------|
| **L1 Context** | CLAUDE.md + context files | `CLAUDE.md` + `.claude/rules/` (30 rules, 6 rule groups) + `system/` (JARVIS identity) | BUILT |
| **L2 Data** | MCP servers | `n8n-mcp` (automation) + `read-ai` (meetings) + `mega-brain-knowledge` (RAG) + Fireflies integration | BUILT |
| **L3 Intelligence** | RAG + knowledge graph | `core/intelligence/rag/` (BM25 + hybrid + graph) + `core/intelligence/pipeline/` (MCE) + knowledge graph (1,302 entities) | BUILT |
| **L4 Automate** | Skills + cron | `.claude/skills/` (20+ skills) + `.claude/hooks/` (20+ hooks) + LaunchAgents (Fireflies cron) | BUILT |
| **L5 Build** | Epic cycles | GSD workflow (`.planning/`) + development pipeline + epic cycles + this very session | BUILT |
| **Mobile** | Telegram bot | NOT YET BUILT — identified gap | PENDING |

### Identified Gaps from Liam's Framework

| Gap | Liam's Approach | Mega Brain Status | Priority |
|-----|----------------|-------------------|----------|
| **Mobile Bridge** | Telegram bot for away-from-desk command | Not implemented | MEDIUM |
| **Task Audit Formalization** | Structured task audit matrix as first step | Informal (not documented) | LOW |
| **Daily Brief Automation** | Automated morning brief as first AIOS milestone | `/jarvis-briefing` exists but not automated via cron | MEDIUM |
| **AI Workforce Packaging** | Package AIOS components for sale ($3K-$10K+) | Not applicable (internal system) | N/A |

---

## AI WORKFORCE CONCEPT

Beyond individual AIOS, Liam describes **AI Workforces** — digital teams that replace
entire departments. This is the second-order application of AIOS principles.

| Department | AI Team Roles | Coordinator |
|-----------|--------------|-------------|
| **Marketing** | Content creator, distributor, analytics, SEO, social media | Marketing coordinator agent |
| **Sales** | Lead qualifier, outreach, follow-up, proposal | Sales coordinator agent |
| **Operations** | Task router, scheduler, documentation, QA | Ops coordinator agent |
| **Creative** | Design, copywriting, video editing, brand consistency | Creative coordinator agent |

In Mega Brain terms, this maps to the **agents/cargo/** architecture where functional role
agents (CLOSER, CRO, CFO, CMO) serve as the equivalent of Liam's department-level AI teams.

---

## KEY PREDICTIONS

| Prediction | Source | Timeframe |
|-----------|--------|-----------|
| 15% of day-to-day work decisions made by agentic AI | Gartner (cited by Liam) | By 2028 |
| First one-person billion-dollar company | Sam Altman (cited by Liam) | Near-term |
| "Bloodbath" for small businesses that don't adopt AI workforces | Liam Ottley | Already happening |

---

## CROSS-REFERENCES

| Theme | Related Dossiers | Connection |
|-------|-----------------|-----------|
| Automation | (pending DOSSIER-AUTOMATION) | AIOS Layer 4 = automation layer |
| Sales Operations | DOSSIER-SALES (if exists) | AI workforce for sales department |
| Founder Productivity | (pending) | Bandwidth inversion (80/20 → 20/80) |
| Revenue Efficiency | (pending) | Revenue per employee as primary metric |

---

## SOURCE MATERIAL

| ID | Title | Type | Key Contribution |
|----|-------|------|-----------------|
| LO-001 | The AI Operating System — What It Is and Why You Need One | YouTube | 5-layer architecture, AIOS definition, implementation sequence |
| LO-002 | I Built an AI Workforce — Here's What Happened | YouTube | AI workforce concept, department replacement, $3K-$10K pricing |
| LO-003 | How I Made $1M in 7 Days Using AI | YouTube | 7-day sprint methodology, proof of AIOS capability |

---

## METADATA

| Field | Value |
|-------|-------|
| Theme Slug | `ai-operating-systems` |
| DNA Path | `knowledge/external/dna/persons/liam-ottley/` |
| Dossier Path | `knowledge/external/dossiers/themes/DOSSIER-AI-OPERATING-SYSTEMS.md` |
| Primary Expert | Liam Ottley |
| Contributing Experts | (none yet — update as more sources contribute) |
| Total DNA Elements | 27 (from Liam Ottley) |

---

*Dossier compiled by Pickle Rick (The Resourceful Builder) -- 2026-03-12*
