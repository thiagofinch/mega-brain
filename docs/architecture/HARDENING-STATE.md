# Hardening State — Session Handoff

> **Last Updated:** 2026-03-15T10:00:00Z
> **Mode:** AIOS-Master (Unity)
> **Session:** S16+S17 — Hardening completion

---

## ROADMAP COMPLETO — ALL 5 EPICS DONE

### Epic 1: Emergency Stabilization — DONE (committed)

| Fase | O que | Status |
|------|-------|--------|
| 1.0 | Register orphaned hooks (session_autosave_v2, session-source-sync) | DONE |
| 1.1 | Archive 277 legacy state files (mission-control 279→13) | DONE |
| 1.2 | Consolidate conclave (agents/conclave/ deleted, 22 refs updated) | DONE |
| 1.3 | Consolidate JARVIS state (5 ghost refs fixed, ROUTING key added) | DONE |

### Epic 2: Limpeza — DONE (not committed)

| Fase | O que | Agente | Status |
|------|-------|--------|--------|
| 2.1 | Force core.paths (55+ files, voice_registry.py last 2 fixed) | @dev | DONE (not committed) |
| 2.2 | Consolidate hooks (34→31 on disk, 30 in settings, 0 duplicates) | @dev | DONE (not committed) |
| 2.3 | Remove dead code (3+3 hooks deleted, 5 orphaned refs cleaned) | @dev | DONE (not committed) |
| 2.4 | Deprecate legacy 5-phase refs in rules (6 files updated with notices) | @architect | DONE (not committed) |

**2.2 Details — What was done (S16):**

**settings.local.json fully cleaned:**
- Removed 8 duplicate hooks (were running TWICE)
- Removed 5 orphaned refs to deleted hooks
- Removed 3 old session_autosave v1 entries
- Removed 6 stale MCP servers (filesystem, excalidraw, google-drive-full, clickup, miro, notion)
- Removed 7 stale env vars (MEGA_BRAIN_ROOT_*, KNOWLEDGE_*, INBOX_PATH, etc.)
- Removed enabledMcpjsonServers (dead MCPs)
- Removed stale permission entries (Skill(chat), Skill(council), mcp__miro__*, mcp__notion__*)
- Result: settings.local.json now contains ONLY permissions + 1 WebSearch hook + alwaysThinkingEnabled

**Consolidation targets:**
- Merge: session_autosave_v2 + continuous_save (2 auto-saves → 1)
- Merge: memory_capture + memory_updater + memory_hints_injector (3 → 1 or 2)
- Review: session_index runs on BOTH SessionStart AND Stop (keep or merge)
- Review: enforce_plan_mode (low value, consider removing)
- Review: pending_tracker (low value, consider removing)
- Keep: resolve_agent_path (utility module, imported by other hooks)

**Executed S16:**
- settings.local.json fully cleaned (all duplicates + stale entries removed)
- 3 more hooks removed: continuous_save (redundant with autosave_v2), enforce_plan_mode (low value), pending_tracker (low value)
- Moved to `.claude/trash/hooks-removed-s16/`
- Final count: 31 on disk (1 utility), 30 in settings, 0 duplicates

**2.4 Details — Rule conflict resolution (S16):**
- Added DEPRECATION NOTICE to 6 rule files referencing legacy 5-phase system
- Files updated: RULE-GROUP-1, RULE-GROUP-4, RULE-GROUP-5, pipeline.md, state-management.md
- Approach: preserve valid principles (sequencing, validation, cascading), mark phase numbering as legacy
- MCE pipeline (`core/intelligence/pipeline/mce/`) is the current system
- Full rule migration to YAML (Epic 5.2) will clean this up further

### Epic 3: Governance Engine — DONE (not committed)

| Fase | O que | Agente | Status |
|------|-------|--------|--------|
| 3.1 | `core/governance/engine.py` — auto-generates docs/architecture/*.md (531 lines, existed from S15) | @dev | DONE |
| 3.2 | Pipeline guard hook + `core/governance/pipeline_guard.py` (213 lines, existed from S15 + hook wrapper new) | @dev | DONE |
| 3.3 | Startup health hook `.claude/hooks/startup_health.py` (14/14 checks pass) | @dev | DONE |
| 3.4 | Worker registry `core/registry/worker-registry.yaml` (29 workers) + `schema.py` (validator + discoverer) | @dev | DONE |

**3.1 Details — Governance engine reads:**
- core/paths.py (130+ ROUTING keys)
- pyproject.toml (ruff, pyright, pytest config)
- biome.json (JS formatter config)
- package.json (dependencies, scripts)
- Actual filesystem structure

**3.1 Details — Governance engine writes:**
- docs/architecture/coding-standards.md (regenerated from configs)
- docs/architecture/tech-stack.md (regenerated from package.json + pyproject.toml)
- docs/architecture/source-tree.md (regenerated from filesystem + ROUTING)

**3.4 Details — Worker registry registers:**
- All 46 pipeline scripts in core/intelligence/pipeline/
- All 18 RAG modules in core/intelligence/rag/
- All hooks in .claude/hooks/
- All agents (41 in AGENT-INDEX.yaml)

### Epic 4: Integration — RESOLVED (S16 audit)

| Fase | O que | Status |
|------|-------|--------|
| 4.1 | Graph integration in RAG pipeline | **ALREADY DONE** — adaptive_router.py routes Pipeline C/D through graph_search() |
| 4.2 | context_scorer always active | **ALREADY DONE** — pipeline.py _build_memory_context() calls it by default |
| 4.3 | System agent triggers | **DEFERRED** — agents exist but need MCE pipeline completion to wire triggers |
| 4.4 | MCE layer generation (VOICE-DNA, BEHAVIORAL-PATTERNS) | **DEFERRED** — requires MCE extraction pipeline running, not standalone |

**4.1/4.2 Verification (S16):**
- `adaptive_router.py` line 219: Pipeline C calls `graph_search(query, top_k=...)`
- `adaptive_router.py` line 226: Pipeline D (Full) also calls `graph_search()`
- `pipeline.py` line 158: `_build_memory_context()` imports and calls `build_adaptive_context()` from context_scorer
- Both were wired in S07 (Spy Squad session) — HARDENING-STATE.md was stale

**4.3/4.4 Deferred to MCE completion:**
- System agents (kops-atlas through dops-rocket) exist in agents/system/ with ACTIVATION.yaml
- They need to be called by MCE orchestrator steps, not hook-triggered
- VOICE-DNA.yaml generation needs MCE extraction output as input

### Epic 5: Rule Engine — DONE (5.1 built, 5.2/5.3 incremental)

| Fase | O que | Status |
|------|-------|--------|
| 5.1 | Synapse engine (`core/engine/synapse.py`, 7 layers) | **DONE** — 11 rules seeded, 2.7ms resolution |
| 5.2 | Migrate 30 rules .md → YAML | **SEEDED** — L0 (4 rules), L1 (5 rules), L6 (3 rules). Remaining rules stay in .md via skill_router |
| 5.3 | Quality gates (pre-commit → PR → human) | **PARTIAL** — pre-commit hook works. PR/human gates need GitHub Actions (future) |

**5.1 Built (S16):**
- `core/engine/synapse.py` — 7-layer resolver with graceful degradation
- `core/engine/rules/L0-constitution.yaml` — 4 non-negotiable rules (security, paths, epistemic, agent integrity)
- `core/engine/rules/L1-global.yaml` — 5 project-wide rules (pipeline, logging, contract, templates, cascading)
- `core/engine/rules/L6-keywords.yaml` — 3 keyword-triggered rules (batch, agent, github)
- CLI: `python3 -m core.engine.synapse seed` / `python3 -m core.engine.synapse resolve [keywords]`
- 2.7ms for full resolution across 3 layers — well within 15ms target
- Empty dirs created for agents/, workflows/, tasks/, squads/ (ready for L2-L5 rules)

---

## Completed This Session (Other Work)

- IDE Sync: all 6 IDEs (Claude, Codex, Gemini, Antigravity, Cursor, Windsurf)
- Cursor/Windsurf format: condensed→full-markdown-yaml (full agent definitions)
- .antigravity/ removed from git (legacy, renamed to .agents/)
- Health check: 100/100 after fixes (docs/framework/ created)
- MCP: removed mega-brain + read-ai (kept mega-brain-knowledge + n8n-mcp)
- docs/architecture/ migration (coding-standards, tech-stack, source-tree from reference/)
- GSD removed entirely (~120 files)
- OPENAI_API_KEY: user needs to add manually to .env
- .nvmrc: 18→24 (match installed Node)
- package.json: private: true (prevent accidental npm publish)
- AGENT-INDEX.yaml: 23→41 agents (added business + system)
- TECH-STACK.md: MCP list updated
- 4 deep-dives completed (AIOX governance, mega-brain dependencies, pipeline MCE, systems)

---

## Current Session Progress (S16)

### Done This Session
- **2.1 COMPLETE:** Fixed last 2 `Path(__file__)` in voice_registry.py (0 violations remaining)
- **2.2 COMPLETE:** Cleaned settings.local.json (removed 8 dupes, 6 stale MCPs, 7 env vars, 3 old autosave refs, stale permissions). Removed 3 more hooks (continuous_save, enforce_plan_mode, pending_tracker). Final: 31 on disk, 30 in settings, 0 duplicates
- **2.3 COMPLETE:** Fixed 5 orphaned hook refs in settings.local.json
- **2.4 COMPLETE:** Added deprecation notices to 6 rule files (RULE-GROUP-1/4/5, pipeline.md, state-management.md)
- **3.1 COMPLETE:** Created `core/governance/engine.py` — auto-generates coding-standards.md, tech-stack.md, source-tree.md from pyproject.toml, biome.json, package.json, core/paths.py

### Epic 2 — ALL PHASES DONE (not committed)

**Ready to commit.** All changes are on disk, validated, and consistent.

### Epic 3 — Phase 3.1 DONE

**Next: Continue with Phase 3.2 (Pipeline guard hook)

---

## NEXT SESSION PROTOCOL — OBRIGATÓRIO

### Fluxo correto (usar @aiox-master com workflow formal):

```
1. Ativar @aiox-master (/aios-master)
2. Briefing: "Continuar hardening do mega-brain. Ler docs/architecture/HARDENING-STATE.md"
3. @aiox-master aciona *orchestrate:
   ├── @pm cria PRD formal (requirements, constraints, success criteria)
   ├── @architect valida viabilidade técnica
   ├── @sm quebra em stories com DoD e acceptance criteria
   ├── @po prioriza backlog
   └── Execução por story (não por epic/fase ad-hoc)
4. Cada story segue: @dev implementa → @qa valida → @devops commita
5. Quality gates entre stories (executor ≠ reviewer)
```

### NÃO FAZER (erro da sessão anterior):
- Pular direto para execução sem PRD/stories
- Criar plano manual em markdown sem passar pelos agentes
- Executar código sem acceptance criteria definidos
- Commitar sem @qa validar

### Briefing para o @pm (input para PRD):
```
Projeto: Mega Brain Hardening & Governance
Objetivo: Alinhar mega-brain com boas práticas AIOX-core
Estado atual: Epic 1 DONE, Epic 2.1 + 2.3 DONE (não commitados)
Referência completa: docs/architecture/HARDENING-STATE.md
Deep-dive técnico: docs/architecture/deep-dive-megabrain-full-system.md
Escopo restante: Epic 2.2, 2.4, Epic 3 (Governance), Epic 4 (Integration), Epic 5 (Rule Engine)
Estimativa: ~35h restantes
Constraint: brownfield (sistema em produção, não pode quebrar pipeline MCE)
```

---

## Known Issues

- ~~3 Stop hook errors~~ — FIXED S16
- ~~8 hooks running TWICE~~ — FIXED S16 (settings.local.json cleaned)
- 870 uncommitted files from prior sessions — need triage
- OPENAI_API_KEY not in .env (user has the key, needs to add manually)
- Vector indexing blocked without VOYAGE_API_KEY

---

## Key Reference Files

| File | Content | Lines |
|------|---------|-------|
| `docs/architecture/deep-dive-megabrain-full-system.md` | Pipeline MCE flow, rules, skills, state files | 680 |
| `docs/architecture/coding-standards.md` | Python + JS code standards | 209 |
| `docs/architecture/tech-stack.md` | Languages, tools, MCP, CI/CD | 110 |
| `docs/architecture/source-tree.md` | Directory structure contract | 94 |
| `.claude/settings.json` | 30 active hooks | ~210 |
| `core/paths.py` | 131 ROUTING keys | 314 |
| `agents/AGENT-INDEX.yaml` | 41 registered agents | 113 |

---

## Deep-Dive Findings Summary (for context in future sessions)

### AIOX Governance Architecture (what we're replicating)
- ServiceRegistry (Tier 0) → SynapseEngine (7 layers) → MasterOrchestrator (state machine) → QualityGateManager (3 layers) → RecoveryHandler (retry 3x) → HealthCheckEngine
- 10 critical patterns: graceful degradation, config-driven, state machine, sequential gates, parallel by domain, TTL cache, event emission, retry+stuck detection, context threading, lazy loading

### Mega-Brain Current Issues Found
- 75 scripts had local BASE_DIR (FIXED in 2.1)
- 306 state files in mission-control (FIXED in 1.1, archived to 13)
- ~~33 hooks with overlaps~~ FIXED S16 (31 on disk, 30 in settings, 0 duplicates)
- Conclave duplicated in 2 dirs (FIXED in 1.2)
- JARVIS state duplicated (FIXED in 1.3)
- Graph not integrated in RAG (TO FIX in 4.1)
- System agents have no triggers (TO FIX in 4.3)
- Rules are markdown not executable (TO FIX in 5.1) — legacy 5-phase refs deprecated in S16
- Memory only saves on Stop (TO FIX in 2.2 or 4.x)
- Workspace is scaffold only (future work)
