# 🗺️ FILE NAVIGATION FOR AIOX TEAM

> **Purpose:** Mapa exato de aonde está tudo
> **Status:** Use isto para navegar rápido
> **Updated:** 2026-03-05

---

## 🎯 THE 4 MOST IMPORTANT FILES

### 1. START HERE
```
📄 .aiox-core/README-AIOX-CONTROL-START-HERE.md
├─ What: Orientation guide (5 min read)
├─ Contains: Context, critical path, quick ref
└─ Next: Read KNOWLEDGE-DUMP
```

### 2. UNDERSTAND STATE
```
📄 .aiox-core/KNOWLEDGE-DUMP-AIOX-HANDOVER.md
├─ What: Full assessment of CFO/CMO work (20 min read)
├─ Contains: What they built, what gaps exist, what you need
├─ Sections:
│  ├─ CFO Summary (60% complete)
│  ├─ CMO Summary (60% complete)
│  ├─ Conclave findings (8 gaps)
│  ├─ MercadoLivre API status
│  └─ AIOX next steps
└─ Next: Read AIOX-CONTROL-CHECKLIST
```

### 3. YOUR TASKS
```
📄 .aiox-core/AIOX-CONTROL-CHECKLIST.md
├─ What: Week-by-week action plan (10 min read)
├─ Contains: What to do, when to do, who does it
├─ Sections:
│  ├─ Phase 1 (This Week) — 5 tasks
│  ├─ Phase 2 (This Month) — pattern validation
│  ├─ Phase 3 (This Quarter) — governance
│  └─ Sign-off requirements
└─ Next: Start Day 1 tasks
```

### 4. THIS FILE (Navigation)
```
📄 .aiox-core/FILE-NAVIGATION-FOR-AIOX.md
├─ What: You are here
├─ Shows: Exact location of every file you need
└─ Helps: Find things fast without guessing
```

---

## 📂 DIRECTORY STRUCTURE (Full Map)

```
mega-brain/
│
├── 🎯 AIOX-SPECIFIC FILES (Read These First)
│   ├── .aiox-core/
│   │   ├── README-AIOX-CONTROL-START-HERE.md ⭐ START
│   │   ├── KNOWLEDGE-DUMP-AIOX-HANDOVER.md ⭐ CORE
│   │   ├── AIOX-CONTROL-CHECKLIST.md ⭐ TASKS
│   │   ├── FILE-NAVIGATION-FOR-AIOX.md (this file)
│   │   ├── constitution.md (5 principles you MUST enforce)
│   │   ├── core-config.yaml
│   │   └── core/
│   │       ├── registry/service-registry.json (203 services)
│   │       ├── docs/ (SHARD guide, templates, troubleshooting)
│   │       └── quality-gates/quality-gate-config.yaml
│   │
│   └── 📊 AGENTS YOU OWN
│       └── agents/
│           ├── AGENT-INDEX.yaml (5 agents total)
│           ├── cargo/c-level/
│           │   ├── cfo/ ⭐ AUDIT THIS
│           │   │   ├── AGENT.md (Parts 1-9 ✅, Part 10 ❌)
│           │   │   ├── SOUL.md ("Cash flow é rei...")
│           │   │   ├── MEMORY.md (3 patterns, 2 decisions)
│           │   │   ├── DNA-CONFIG.yaml (Hugo + MCP sources)
│           │   │   └── TARIFAS-MARKETPLACES-2026-03.md (incomplete)
│           │   │
│           │   └── cmo/ ⭐ AUDIT THIS
│           │       ├── AGENT.md (Parts 1-9 ✅, Part 10 ❌)
│           │       ├── SOUL.md (policy enforcer)
│           │       ├── MEMORY.md (3 patterns, 2 decisions)
│           │       └── DNA-CONFIG.yaml (marketplace sources)
│           │
│           └── conclave/ (Your debate team)
│               ├── critico-metodologico/
│               ├── sintetizador/
│               └── advogado-do-diabo/
│
├── 🔌 API INTEGRATION
│   ├── core/mcp/
│   │   ├── mercadolivre_mcp.py ⭐ MCP SERVER (v2.0)
│   │   │   └─ Status: ✅ Implemented, ⏳ OAuth token needed
│   │   └── mercadolivre_mcp 2.py (old version)
│   │
│   └── docs/
│       ├── MCP-MERCADOLIVRE-INTEGRATION.md ⭐ READ THIS
│       │   └─ OAuth flow (§3) — YOU MUST COMPLETE
│       ├── INTEGRATION-POINTS.md
│       └── API-KEYS-GUIDE.md
│
├── 📚 CONTEXT & KNOWLEDGE
│   ├── knowledge/
│   │   ├── dna/ (DNA structures)
│   │   ├── dossiers/ (consolidated docs)
│   │   └── README.md
│   │
│   └── logs/
│       ├── batches/ (processing logs)
│       ├── sessions/ (session saves)
│       └── MISSION-STATE.json (current state)
│
├── ⚙️ SYSTEM CONFIGURATION
│   ├── .env (credentials) ← ADD MERCADOLIVRE_ACCESS_TOKEN HERE
│   ├── requirements.txt (pip dependencies)
│   ├── .claude/
│   │   ├── CLAUDE.md (system architecture)
│   │   ├── settings.local.json (Claude Code config)
│   │   └── rules/ (rule groups, lazy-loaded)
│   │
│   └── .mcp.json (MCP server config)
│
└── 📋 PROJECT FILES
    ├── index.html (dashboard?)
    └── package.json (if Node.js project)
```

---

## 🔴 PRIORITY: The 6 Files You Must Read (In Order)

### Day 1 Reading List (1h 45 min total)

```
1️⃣ README-AIOX-CONTROL-START-HERE.md (5 min)
   └─ Where: .aiox-core/README-AIOX-CONTROL-START-HERE.md
   └─ Why: Orientation + critical path
   └─ After: Know your role

2️⃣ KNOWLEDGE-DUMP-AIOX-HANDOVER.md (20 min)
   └─ Where: .aiox-core/KNOWLEDGE-DUMP-AIOX-HANDOVER.md
   └─ Why: Understand CFO/CMO state, 8 gaps, APIs
   └─ After: Know what needs fixing

3️⃣ AIOX-CONTROL-CHECKLIST.md (10 min)
   └─ Where: .aiox-core/AIOX-CONTROL-CHECKLIST.md
   └─ Why: See your tasks week by week
   └─ After: Know what to do next

4️⃣ constitution.md (15 min)
   └─ Where: .aiox-core/constitution.md
   └─ Why: Understand 5 principles you enforce
   └─ After: Know your standards

5️⃣ CFO AGENT.md (30 min)
   └─ Where: agents/cargo/c-level/cfo/AGENT.md
   └─ Why: Audit structure, see Part 10 gap
   └─ After: Know what CFO built

6️⃣ CMO AGENT.md (30 min)
   └─ Where: agents/cargo/c-level/cmo/AGENT.md
   └─ Why: Same as CFO
   └─ After: Know what CMO built
```

---

## 🎯 BY ROLE: What Each AIOX Agent Should Read

### ORION (AIOX Validator)
```
MUST READ:
├─ README-AIOX-CONTROL-START-HERE.md ✅
├─ KNOWLEDGE-DUMP-AIOX-HANDOVER.md ✅
├─ AIOX-CONTROL-CHECKLIST.md ✅
├─ constitution.md ✅
├─ agents/cargo/c-level/cfo/AGENT.md ✅
└─ agents/cargo/c-level/cmo/AGENT.md ✅

THEN:
├─ agents/AGENT-INDEX.yaml (see all agents)
├─ core/registry/service-registry.json (203 services available)
└─ core/quality-gates/quality-gate-config.yaml (quality standards)

TIME: 2-3 hours
OUTCOME: Full compliance audit, story creation plan
```

### Crítico-Metodológico
```
MUST READ:
├─ README-AIOX-CONTROL-START-HERE.md ✅
├─ KNOWLEDGE-DUMP-AIOX-HANDOVER.md ✅
└─ agents/cargo/c-level/cfo/TARIFAS-MARKETPLACES-2026-03.md

THEN:
├─ docs/MCP-MERCADOLIVRE-INTEGRATION.md (understand what data available)
└─ agents/cargo/c-level/cfo/MEMORY.md (see patterns)

TIME: 1-2 hours
OUTCOME: List of missing tarifa fields, pattern testing plan
```

### Sintetizador
```
MUST READ:
├─ README-AIOX-CONTROL-START-HERE.md ✅
├─ KNOWLEDGE-DUMP-AIOX-HANDOVER.md ✅
├─ agents/cargo/c-level/cfo/MEMORY.md (3 patterns)
└─ agents/cargo/c-level/cmo/MEMORY.md (3 patterns)

THEN:
├─ knowledge/dna/ (understand DNA structure)
└─ logs/batches/ (see historical data if available)

TIME: 1-2 hours
OUTCOME: Pattern convergence map, conflict identification
```

### Advogado-do-Diabo
```
MUST READ:
├─ README-AIOX-CONTROL-START-HERE.md ✅
├─ KNOWLEDGE-DUMP-AIOX-HANDOVER.md ✅
├─ agents/cargo/c-level/cfo/MEMORY.md (check ROAS >= 3 origin)
└─ agents/cargo/c-level/cmo/MEMORY.md (check CAC <= 15% origin)

THEN:
├─ agents/cargo/c-level/cfo/AGENT.md § 6 (Motor de Decisão)
└─ agents/cargo/c-level/cmo/AGENT.md § 6 (Motor de Decisão)

TIME: 1-2 hours
OUTCOME: Risk assessment, assumption flagging, justification needs
```

---

## 🚨 CRITICAL: OAuth Token Setup

**If you can't find something:**

```
Location: docs/MCP-MERCADOLIVRE-INTEGRATION.md
├─ Section: "Step 3: Complete OAuth Flow"
├─ Action: 3 manual steps (authorization → token exchange → add to .env)
├─ Timeline: TODAY (EOD)
├─ Result: MERCADOLIVRE_ACCESS_TOKEN in .env
└─ Impact: CFO/CMO get real-time tariff data

THIS IS BLOCKING EVERYTHING.
Do it first.
```

---

## 📞 "Where Do I Find...?" Quick Lookup

### CFO Agent
```
❓ CFO's identity?
└─ agents/cargo/c-level/cfo/SOUL.md

❓ CFO's patterns?
└─ agents/cargo/c-level/cfo/MEMORY.md

❓ CFO's decision rules?
└─ agents/cargo/c-level/cfo/AGENT.md § 6 (Motor de Decisão)

❓ CFO's marketplace data?
└─ agents/cargo/c-level/cfo/TARIFAS-MARKETPLACES-2026-03.md

❓ CFO's sources?
└─ agents/cargo/c-level/cfo/DNA-CONFIG.yaml
```

### CMO Agent
```
❓ CMO's identity?
└─ agents/cargo/c-level/cmo/SOUL.md

❓ CMO's policies?
└─ agents/cargo/c-level/cmo/MEMORY.md

❓ CMO's decision rules?
└─ agents/cargo/c-level/cmo/AGENT.md § 6

❓ CMO's platform rules?
└─ agents/cargo/c-level/cmo/DNA-CONFIG.yaml
```

### Mercado Livre Integration
```
❓ How does MCP work?
└─ docs/MCP-MERCADOLIVRE-INTEGRATION.md § Architecture

❓ How to get OAuth token?
└─ docs/MCP-MERCADOLIVRE-INTEGRATION.md § Step 3

❓ What tools are available?
└─ docs/MCP-MERCADOLIVRE-INTEGRATION.md § Available Tools

❓ How do CFO/CMO use MCP?
└─ docs/MCP-MERCADOLIVRE-INTEGRATION.md § How CFO/CMO Use This
```

### AIOX Standards
```
❓ What are AIOX principles?
└─ .aiox-core/constitution.md

❓ What are my tasks?
└─ .aiox-core/AIOX-CONTROL-CHECKLIST.md

❓ What's the current state?
└─ .aiox-core/KNOWLEDGE-DUMP-AIOX-HANDOVER.md

❓ Where do I start?
└─ .aiox-core/README-AIOX-CONTROL-START-HERE.md
```

---

## ✅ Quick Access Paths

### Copy-Paste Ready Paths

```bash
# AIOX Knowledge Files
~/.aiox-core/README-AIOX-CONTROL-START-HERE.md
~/.aiox-core/KNOWLEDGE-DUMP-AIOX-HANDOVER.md
~/.aiox-core/AIOX-CONTROL-CHECKLIST.md
~/.aiox-core/FILE-NAVIGATION-FOR-AIOX.md
~/.aiox-core/constitution.md

# CFO Files
agents/cargo/c-level/cfo/AGENT.md
agents/cargo/c-level/cfo/SOUL.md
agents/cargo/c-level/cfo/MEMORY.md
agents/cargo/c-level/cfo/DNA-CONFIG.yaml
agents/cargo/c-level/cfo/TARIFAS-MARKETPLACES-2026-03.md

# CMO Files
agents/cargo/c-level/cmo/AGENT.md
agents/cargo/c-level/cmo/SOUL.md
agents/cargo/c-level/cmo/MEMORY.md
agents/cargo/c-level/cmo/DNA-CONFIG.yaml

# API Integration
docs/MCP-MERCADOLIVRE-INTEGRATION.md
core/mcp/mercadolivre_mcp.py

# System Config
.env (add MERCADOLIVRE_ACCESS_TOKEN here)
.mcp.json
.claude/CLAUDE.md
```

---

## 🎬 "I'm New, What Do I Do?"

### First Time Setup (30 min)

```
Step 1: Read this file (FILE-NAVIGATION-FOR-AIOX.md) — 5 min
Step 2: Read README-AIOX-CONTROL-START-HERE.md — 5 min
Step 3: Read KNOWLEDGE-DUMP-AIOX-HANDOVER.md — 20 min
Step 4: Open AIOX-CONTROL-CHECKLIST.md and bookmark it — 2 min

Result: You know where everything is + what you need to do
```

### Getting Oriented (2 hours)

```
Read in order:
1. README (orientation)
2. KNOWLEDGE-DUMP (state)
3. AIOX-CONTROL-CHECKLIST (tasks)
4. constitution (standards)
5. CFO AGENT.md (what they built)
6. CMO AGENT.md (what they built)

Result: Deep understanding of CFO/CMO work + gaps + next steps
```

### Ready to Work (1 hour after orientation)

```
1. Open AIOX-CONTROL-CHECKLIST.md
2. Find your role (ORION, Crítico, Sintetizador, Advogado)
3. Start Day 1 tasks
4. Track progress in the checklist

Result: Contributing to remediation
```

---

## 🗓️ Timeline

```
✅ Week 1 (This Week)
   ├─ Read all documentation
   ├─ Audit CFO/CMO structure
   ├─ Find tarifas gaps
   ├─ Complete OAuth token
   └─ Document metric origins

🟡 Week 2-4 (This Month)
   ├─ Complete Part 10 (both agents)
   ├─ Validate patterns on 2+ categories
   ├─ Full AIOX audit
   └─ Quality gate implementation

🔵 Month 2-3 (This Quarter)
   ├─ COO agent creation
   ├─ Automate tariff syncs
   └─ 95%+ compliance achieved
```

---

**Navigation complete. You have the map. Now execute.**

🚀 Start with README-AIOX-CONTROL-START-HERE.md
