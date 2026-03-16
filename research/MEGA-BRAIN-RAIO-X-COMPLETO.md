
# MEGA BRAIN — RAIO-X ESTRUTURAL COMPLETO

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                    ║
║    ███╗   ███╗███████╗ ██████╗  █████╗     ██████╗ ██████╗  █████╗ ██╗███╗   ██╗                                   ║
║    ████╗ ████║██╔════╝██╔════╝ ██╔══██╗    ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║                                   ║
║    ██╔████╔██║█████╗  ██║  ███╗███████║    ██████╔╝██████╔╝███████║██║██╔██╗ ██║                                   ║
║    ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║    ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║                                   ║
║    ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║    ██████╔╝██║  ██║██║  ██║██║██║ ╚████║                                   ║
║    ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝ ╚═══╝                                   ║
║                                                                                                                    ║
║    DOCUMENTACAO TECNICA COMPLETA — RAIO-X ESTRUTURAL v2.0                                                         ║
║    Versao: 2.0.0 | Data: 2026-03-15 | Autor: JARVIS                                                              ║
║                                                                                                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## INDICE GERAL

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  SECAO 1  -  VISAO GERAL (O QUE E O MEGA BRAIN)                 │
    │  SECAO 2  -  PIPELINE MCE (12 STEPS, SQUAD AGENTS)              │
    │  SECAO 3  -  KNOWLEDGE ARCHITECTURE (3 BUCKETS + WORKSPACE)     │
    │  SECAO 4  -  ARTIFACTS & STATE (CHUNKS, CANONICAL, INSIGHTS)    │
    │  SECAO 5  -  AGENT ECOSYSTEM (23 AGENTES + 2 SQUADS)           │
    │  SECAO 6  -  DNA SYSTEM (5 LAYERS + VOICE-DNA + MCE)           │
    │  SECAO 7  -  GOVERNANCE & RULES (SYNAPSE 26 RULES)             │
    │  SECAO 8  -  HOOKS SYSTEM (34 HOOKS x 5 EVENTS)                │
    │  SECAO 9  -  LOGGING ARCHITECTURE (13 JSONL + DUAL-LOCATION)   │
    │  SECAO 10 -  WORKSPACE (8 DEPARTAMENTOS + CLICKUP MIRROR)      │
    │  SECAO 11 -  .CLAUDE CORE (100 SKILLS, 34 HOOKS, RULES)        │
    │  SECAO 12 -  INTEGRATIONS (READ.AI, FIREFLIES, N8N, MCP)       │
    │  SECAO 13 -  CONCLAVE (3 MEMBROS, PROTOCOLO DE DEBATE)         │
    │  SECAO 14 -  PATHS CONTRACT (core/paths.py, 131 ROUTING KEYS)  │
    │  SECAO 15 -  TRACEABILITY CHAIN (VIDEO → AGENT)                │
    │  SECAO 16 -  TESTING & QUALITY (502 TESTS, RUFF, GOVERNANCE)   │
    │  SECAO 17 -  FLUXO COMPLETO PONTA A PONTA (MCE 12 STEPS)      │
    │  SECAO 18 -  MAPA COMPLETO DE TEMPLATES (22 TEMPLATES)         │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗                                                          ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║                                                          ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║                                                          ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║                                                          ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║                                                          ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝                                                          ====
====                                                                                                                ====
====     VISAO GERAL — O QUE E O MEGA BRAIN                                                                         ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 1.1 — DEFINICAO FUNDAMENTAL

Mega Brain e um sistema de gestao de conhecimento alimentado por IA que transforma materiais de especialistas (videos, PDFs, transcricoes) em playbooks estruturados, schemas de DNA cognitivo e agentes mind-clone. Tres buckets de conhecimento (external, business, personal) alimentam 23 agentes atraves de um pipeline MCE de 12 passos, governado por 26 regras Synapse e 34 hooks de ciclo de vida.

Imagine um corpo humano:
- A **boca** sao os 3 inbox buckets (external, business, personal)
- O **estomago** e o pipeline MCE de 12 passos
- O **cerebro** e a base de conhecimento processada (knowledge/ com 3 buckets)
- Os **orgaos** sao os 23 agentes especializados (agents/)
- O **sistema nervoso** e o Synapse engine + hooks + governance (core/engine/)
- A **memoria** sao os logs JSONL e state files (.claude/mission-control/)
- O **coracao** e a operacao da empresa (workspace/ com 8 departamentos)
- O **cerebelo** e o .claude/ com 100 skills e 34 hooks

```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    │     3 INBOX BUCKETS         MCE PIPELINE          KNOWLEDGE         │
    │     ┌───────────┐      ┌──────────────┐      ┌──────────────┐      │
    │     │           │      │              │      │              │      │
    │     │ external/ │─────>│  12-STEP MCE │─────>│  external/   │      │
    │     │ business/ │      │              │      │  business/   │      │
    │     │ personal/ │      │ Detect       │      │  personal/   │      │
    │     │           │      │ Ingest       │      │              │      │
    │     │ Cursos    │      │ Batch        │      │ DNA YAMLs    │      │
    │     │ Calls     │      │ Chunk (LLM)  │      │ Dossiers     │      │
    │     │ PDFs      │      │ Entity (LLM) │      │ Playbooks    │      │
    │     │ Videos    │      │ Insight (LLM)│      │ Sources      │      │
    │     │           │      │ MCE Layers   │      │              │      │
    │     └───────────┘      │ Consolidate  │      └──────┬───────┘      │
    │                        │ Finalize     │             │              │
    │                        └──────────────┘             v              │
    │                                              ┌──────────────┐      │
    │                                              │              │      │
    │                                              │   agents/    │      │
    │                                              │              │      │
    │                                              │  23 Agentes  │      │
    │                                              │  com DNA     │      │
    │                                              │  rastreavel  │      │
    │                                              │              │      │
    │                                              └──────────────┘      │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

## 1.2 — FONTES DE CONHECIMENTO (QUEM ALIMENTA O SISTEMA)

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                    FONTES PRIMARIAS DE DNA                           ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║                                                                      ║
    ║  ┌────────────────────┐    ┌────────────────────┐                   ║
    ║  │  ALEX HORMOZI      │    │  COLE GORDON       │                   ║
    ║  │  Acquisition.com   │    │  Closers.io        │                   ║
    ║  │  ─────────────────  │    │  ─────────────────  │                   ║
    ║  │  Scaling            │    │  High-Ticket Close │                   ║
    ║  │  Farm System        │    │  7 Beliefs         │                   ║
    ║  │  Unit Economics     │    │  Tonalidade        │                   ║
    ║  │  Compensation       │    │  Objecoes          │                   ║
    ║  └────────────────────┘    └────────────────────┘                   ║
    ║                                                                      ║
    ║  ┌────────────────────┐    ┌────────────────────┐                   ║
    ║  │  JEREMY MINER      │    │  JEREMY HAYNES     │                   ║
    ║  │  7th Level / NEPQ  │    │  Digital Agency    │                   ║
    ║  │  ─────────────────  │    │  ─────────────────  │                   ║
    ║  │  Neuro-Emotional    │    │  Paid Media        │                   ║
    ║  │  Tonality           │    │  Megalodon Ads     │                   ║
    ║  │  Discovery Qs       │    │  Call Funnels      │                   ║
    ║  │  Commitment Qs      │    │  Creative Strategy │                   ║
    ║  └────────────────────┘    └────────────────────┘                   ║
    ║                                                                      ║
    ║  ┌────────────────────┐    ┌────────────────────┐                   ║
    ║  │  FULL SALES SYSTEM │    │  THE SCALABLE CO.  │                   ║
    ║  │  Vinicius de Sa    │    │  Ryan Deiss        │                   ║
    ║  │  ─────────────────  │    │  ─────────────────  │                   ║
    ║  │  SDR Brasileiro    │    │  Scalable OS       │                   ║
    ║  │  4 Tipos de SDR    │    │  Value Engines     │                   ║
    ║  │  Dimensionamento   │    │  Meeting Rhythm    │                   ║
    ║  │  Onboarding        │    │  Playbook Creation │                   ║
    ║  └────────────────────┘    └────────────────────┘                   ║
    ║                                                                      ║
    ║  ┌────────────────────┐    ┌────────────────────┐                   ║
    ║  │  LIAM OTTLEY       │    │  SAM OVENS         │                   ║
    ║  │  AI Agency          │    │  Setterlun Univ.   │                   ║
    ║  │  ─────────────────  │    │  ─────────────────  │                   ║
    ║  │  AI Agent Building  │    │  Business DNA      │                   ║
    ║  │  Agency Scaling     │    │  Offer Code        │                   ║
    ║  │  MCP Architecture   │    │  Purple Ocean      │                   ║
    ║  │  Workflow Design    │    │  Consulting Model  │                   ║
    ║  └────────────────────┘    └────────────────────┘                   ║
    ║                                                                      ║
    ║  + G4 Educacao + Jordan Lee + Alan Nicolas + Pedro Valerio          ║
    ║  + Richard Linder + Client Accelerator + EAD Closer                 ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 1.3 — NUMEROS DO SISTEMA

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                  METRICAS DO MEGA BRAIN v2.0                     │
    ├──────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Fontes Primarias .................. 14 especialistas (DNA)      │
    │  Diretórios de Source .............. 15 diretorios               │
    │  Arquivos Source (raw) ............. 689 arquivos                │
    │  Chunks Processados ................ 2,297 chunks                │
    │  Entidades Canonicas ............... 17 entidades                │
    │  Insights Extraidos ................ 112 insights                │
    │  Agentes Ativos .................... 23 agentes registrados      │
    │  Agentes External (mind clones) .... 13 agentes (6 no INDEX)    │
    │  Squads de Sistema ................. 2 squads (10 membros)       │
    │  Skills Ativas ..................... 100 skills                   │
    │  Hooks de Automacao ................ 34 hooks                    │
    │  Regras Synapse .................... 26 regras (3 layers)        │
    │  ROUTING Keys (paths.py) ........... 131 keys                    │
    │  Playbooks ......................... 33 playbooks                │
    │  Dossiers External (persons) ....... 10 dossiers                 │
    │  Dossiers External (themes) ........ 23 dossiers                 │
    │  Dossiers Business (persons) ....... 6 dossiers                  │
    │  Dossiers Business (themes) ........ 6 dossiers                  │
    │  RAG Index (BM25) .................. 45MB                        │
    │  Testes Automatizados .............. 502 testes                   │
    │  MCP Servers ....................... 2 servidores                 │
    │  Deny Rules (security) ............. 12 regras                   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗     ██████╗                                                       ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ╚════██╗                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║     █████╔╝                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║    ██╔═══╝                                                       ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝    ███████╗                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚══════╝                                                      ====
====                                                                                                                ====
====     PIPELINE MCE — 12 STEPS COM SQUAD AGENTS                                                                   ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

O MCE (Mental Cognitive Extraction) Pipeline transforma conteudo bruto de especialistas em schemas de DNA estruturados, perfis comportamentais e agentes mind-clone. Combina modulos Python deterministicos para operacoes de arquivo com prompts LLM para extracao.

## 2.1 — VISAO MACRO DO PIPELINE (12 STEPS)

```
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    MCE PIPELINE — 12 STEPS                              │
    │                                                                         │
    │  INPUT                                                                  │
    │    │                                                                    │
    │    v                                                                    │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
    │  │ 0. DETECT   │─>│ 1. INGEST   │─>│ 2. BATCH    │  <-- DETERMINISTIC  │
    │  │   (init)    │  │   (Atlas)   │  │   (Atlas)   │                     │
    │  └─────────────┘  └─────────────┘  └─────────────┘                     │
    │                                          │                              │
    │                                          v                              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
    │  │ 3. CHUNK    │─>│ 4. ENTITY   │─>│ 5. INSIGHT  │  <-- LLM            │
    │  │   (Sage)    │  │   (Sage)    │  │   (Sage)    │                     │
    │  └─────────────┘  └─────────────┘  └─────────────┘                     │
    │                                          │                              │
    │                                          v                              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
    │  │ 6. BEHAV    │─>│ 7. IDENTITY │─>│ 8. VOICE    │  <-- LLM (MCE)      │
    │  │   (Sage)    │  │   (Sage)    │  │   (Sage)    │                     │
    │  └─────────────┘  └─────────────┘  └─────────────┘                     │
    │                                          │                              │
    │                                          v                              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
    │  │ 9. CHECK    │─>│10. COMPILE  │─>│11. FINALIZE │  <-- HUMAN + DET.   │
    │  │   (Lens)    │  │   (Forge)   │  │   (Echo)    │                     │
    │  └─────────────┘  └─────────────┘  └─────────────┘                     │
    │                                          │                              │
    │                                          v                              │
    │                                    ┌─────────────┐                      │
    │                                    │12. REPORT   │  <-- OUTPUT           │
    │                                    │   (Lens)    │                      │
    │                                    └─────────────┘                      │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 — DETALHAMENTO DOS 12 STEPS

```
    ╔═══════╤══════════════════════╤═══════════════╤═══════════════════════════════════════╗
    ║ Step  │ Nome                 │ Tipo          │ Script / Prompt                       ║
    ╠═══════╪══════════════════════╪═══════════════╪═══════════════════════════════════════╣
    ║  0    │ Detect               │ Deterministic │ orchestrate.py                        ║
    ║  1    │ Ingest               │ Deterministic │ scope_classifier.py + smart_router.py ║
    ║  2    │ Batch                │ Deterministic │ batch_auto_creator.py                 ║
    ║  3    │ Chunk                │ LLM           │ prompt-1.1-chunking.md                ║
    ║  4    │ Entity Resolution    │ LLM           │ prompt-1.2-entity-resolution.md       ║
    ║  5    │ Insight Extraction   │ LLM           │ prompt-2.1-insight-extraction.md      ║
    ║  6    │ MCE Behavioral       │ LLM           │ prompt-mce-behavioral.md              ║
    ║  7    │ MCE Identity         │ LLM           │ prompt-mce-identity.md                ║
    ║  8    │ MCE Voice            │ LLM           │ prompt-mce-voice.md                   ║
    ║  9    │ Identity Checkpoint  │ Human Review  │ human-review (UNICO passo manual)     ║
    ║ 10    │ Consolidation        │ LLM           │ dossier-compilation.md + Template V3  ║
    ║ 11    │ Finalize             │ Deterministic │ orchestrate.py finalize               ║
    ╚═══════╧══════════════════════╧═══════════════╧═══════════════════════════════════════╝
```

**Step 1 — 6 Sinais de Classificacao:**

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  # │ Sinal              │ O que verifica                        │
    │ ───┼────────────────────┼──────────────────────────────────────  │
    │ S1 │ Path pattern       │ Diretorio implica bucket              │
    │ S2 │ Participant names  │ Pessoas conhecidas → external/business│
    │ S3 │ Content keywords   │ Marcadores de especialista/empresa    │
    │ S4 │ File metadata      │ Tipo de fonte (curso, call, doc)      │
    │ S5 │ Entity match       │ Lookup no CANONICAL-MAP               │
    │ S6 │ Historical pattern │ Classificacoes anteriores             │
    └──────────────────────────────────────────────────────────────────┘
```

## 2.3 — STATE MACHINE

```
    init ──> chunking ──> entities ──> knowledge_extraction ──> mce_extraction
                                                                     │
                                                           identity_checkpoint
                                                               │       │
                                                           (APPROVE) (REVISE → loop)
                                                               │
                                                          consolidation ──> agent_generation
                                                                                │
                                                                           validation ──> complete
```

**Resume:** `/pipeline-mce {SLUG}` — retoma do primeiro step incompleto automaticamente.
**Persistencia:** `.claude/mission-control/mce/{SLUG}/pipeline_state.yaml`

## 2.4 — KNOWLEDGE OPS SQUAD (5 AGENTES)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  Squad Agent │ Role              │ Steps  │ Responsabilidade     │
    │ ─────────────┼───────────────────┼────────┼────────────────────  │
    │  Atlas       │ The Classifier    │ 0-2    │ Deteccao, class.,    │
    │              │                   │        │ roteamento           │
    │  Sage        │ The Extractor     │ 3-8    │ Chunking, entidades, │
    │              │                   │        │ insights, MCE layers │
    │  Lens        │ The Validator     │ 9, 12  │ Checkpoint, valid.   │
    │  Forge       │ The Compiler      │ 10     │ Dossiers, DNA YAMLs  │
    │  Echo        │ The Cloner        │ 10-11  │ Agentes, memory      │
    └──────────────────────────────────────────────────────────────────┘

    Localizacao: agents/system/knowledge-ops/
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗     ██████╗                                                       ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ╚════██╗                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║     █████╔╝                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ╚═══██╗                                                      ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝    ██████╔╝                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚═════╝                                                       ====
====                                                                                                                ====
====     KNOWLEDGE ARCHITECTURE — 3 BUCKETS + WORKSPACE                                                             ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

O Mega Brain organiza conhecimento em 3 buckets isolados + 1 centro operacional:

## 3.1 — ARQUITETURA DOS 3 BUCKETS

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║                     ┌───────────────────┐                            ║
    ║                     │    knowledge/      │                            ║
    ║                     └─────────┬─────────┘                            ║
    ║                               │                                      ║
    ║           ┌───────────────────┼───────────────────┐                  ║
    ║           v                   v                   v                  ║
    ║  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        ║
    ║  │   external/     │ │   business/     │ │   personal/     │        ║
    ║  │   (L2 Pro)      │ │   (L3)          │ │   (L3)          │        ║
    ║  ├─────────────────┤ ├─────────────────┤ ├─────────────────┤        ║
    ║  │ dna/persons/    │ │ inbox/          │ │ calls/          │        ║
    ║  │   14 experts    │ │ people/         │ │ cognitive/      │        ║
    ║  │ dossiers/       │ │ dossiers/       │ │ email/          │        ║
    ║  │   persons/ (10) │ │   persons/ (6)  │ │ messages/       │        ║
    ║  │   themes/ (23)  │ │   themes/ (6)   │ │                 │        ║
    ║  │ playbooks/ (33) │ │ insights/       │ │                 │        ║
    ║  │ sources/ (15)   │ │ narratives/     │ │                 │        ║
    ║  │ inbox/          │ │ decisions/      │ │                 │        ║
    ║  │                 │ │ sops/           │ │                 │        ║
    ║  └─────────────────┘ └─────────────────┘ └─────────────────┘        ║
    ║                                                                      ║
    ║  Cada bucket tem RAG index isolado:                                  ║
    ║  external → .data/rag_expert/                                        ║
    ║  business → .data/rag_business/                                      ║
    ║  personal → (via personal_data ROUTING key)                          ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 3.2 — WORKSPACE (4o PILAR)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  workspace/ — Centro Operacional da Empresa                      │
    │  NAO e knowledge. E prescritivo (SOPs, processos, estrutura).    │
    │                                                                  │
    │  L1 template (estrutura), L2 quando populado com dados reais.    │
    │                                                                  │
    │  Detalhado na SECAO 10.                                          │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 3.3 — RAG PIPELINES (5 MODOS)

```
    ╔═══════╤════════════════════╤══════════════════════════════════════╗
    ║ Mode  │ Nome               │ Descricao                            ║
    ╠═══════╪════════════════════╪══════════════════════════════════════╣
    ║  A    │ BM25               │ Busca factual rapida (~3.6s)         ║
    ║  B    │ Hybrid             │ BM25 + Semantic (~3s)                ║
    ║  C    │ Graph + Hybrid     │ Cross-expert com grafo (~5.8s)       ║
    ║  D    │ Full               │ Hierarquico completo (~2.5s)         ║
    ║  E    │ Contextual         │ Context-aware adaptativo             ║
    ╚═══════╧════════════════════╧══════════════════════════════════════╝

    Index BM25: .data/rag_index/ (45MB)
    Knowledge Graph: .data/knowledge_graph/graph.json
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗     ██╗  ██╗                                                      ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ██║  ██║                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ███████║                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║    ╚════██║                                                      ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝         ██║                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝         ╚═╝                                                      ====
====                                                                                                                ====
====     ARTIFACTS & STATE — CHUNKS, CANONICAL, INSIGHTS                                                            ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 4.1 — 3 ARTIFACTS PERSISTENTES

O pipeline produz 3 arquivos de estado que crescem incrementalmente:

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  artifacts/                                                          ║
    ║  ├── chunks/CHUNKS-STATE.json          2,297 chunks                  ║
    ║  │   Append-only. Dedup por id_chunk.                                ║
    ║  │   Cada chunk: ~300 palavras, metadados de source.                 ║
    ║  │                                                                   ║
    ║  ├── canonical/CANONICAL-MAP.json      17 entidades                  ║
    ║  │   PERSISTENT across all runs. READ existing → MERGE.              ║
    ║  │   NUNCA overwrite. Maps name variants → canonical form.           ║
    ║  │                                                                   ║
    ║  └── insights/INSIGHTS-STATE.json      112 insights                  ║
    ║      SINGLE file que cresce. NUNCA criar variantes per-meeting.      ║
    ║      Contem: insights[], behavioral_patterns[], identity{}           ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 4.2 — STATE FILES POR SLUG (MCE Pipeline)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  .claude/mission-control/mce/{SLUG}/                             │
    │  ├── pipeline_state.yaml    FSM state + historico de transicao   │
    │  ├── metadata.yaml          Progresso por fase, sources proc.    │
    │  └── metrics.yaml           Wall-clock timing por fase           │
    │                                                                  │
    │  .claude/mission-control/                                        │
    │  ├── BATCH-REGISTRY.json    Tracking de todos os batches         │
    │  ├── TRIAGE-QUEUE.json      Fila de triagem do smart router      │
    │  ├── WATCHER-STATE.json     Estado do inbox watcher              │
    │  ├── READ-AI-STATE.json     Estado da integracao Read.ai         │
    │  ├── FIREFLIES-STATE.json   Estado da integracao Fireflies       │
    │  ├── PHASE-GATE-STATE.json  Estado do phase gate                 │
    │  └── DISCOVERY-STATE.json   Estado do agent discovery            │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 4.3 — OUTPUTS DO STEP 10 (CONSOLIDATION)

Cada pessoa processada gera 10-15 arquivos:

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  #  │ Artifact          │ Path                                   │
    │ ────┼───────────────────┼──────────────────────────────────────  │
    │  1  │ Dossier           │ knowledge/external/dossiers/persons/   │
    │  2  │ Source themes     │ knowledge/external/sources/{slug}/     │
    │  3  │ PHILOSOPHIES.yaml │ knowledge/external/dna/persons/{SLUG}/ │
    │  4  │ MENTAL-MODELS     │ knowledge/external/dna/persons/{SLUG}/ │
    │  5  │ HEURISTICS.yaml   │ knowledge/external/dna/persons/{SLUG}/ │
    │  6  │ FRAMEWORKS.yaml   │ knowledge/external/dna/persons/{SLUG}/ │
    │  7  │ METHODOLOGIES     │ knowledge/external/dna/persons/{SLUG}/ │
    │  8  │ VOICE-DNA.yaml    │ knowledge/external/dna/persons/{SLUG}/ │
    │  9  │ AGENT.md          │ agents/external/{SLUG}/                │
    │ 10  │ SOUL.md           │ agents/external/{SLUG}/                │
    │ 11  │ MEMORY.md         │ agents/external/{SLUG}/                │
    │ 12  │ DNA-CONFIG.yaml   │ agents/external/{SLUG}/                │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗     ███████╗                                                      ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ██╔════╝                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ███████╗                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║    ╚════██║                                                      ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝    ███████║                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚══════╝                                                      ====
====                                                                                                                ====
====     AGENT ECOSYSTEM — 23 AGENTES + 2 SQUADS                                                                    ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 5.1 — ARQUITETURA DE 3 CAMADAS

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║                        JARVIS (Orquestrador)                         ║
    ║                              │                                       ║
    ║              ┌───────────────┼───────────────┐                       ║
    ║              v               v               v                       ║
    ║   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                ║
    ║   │   LAYER 1    │ │   LAYER 2    │ │   LAYER 3    │                ║
    ║   │    CARGO     │ │   EXTERNAL   │ │   CONCLAVE   │                ║
    ║   │   (Hibrido)  │ │   (Solo)     │ │   (Meta)     │                ║
    ║   │  DNA misto   │ │ DNA 100%     │ │ Sem DNA      │                ║
    ║   │  14 agentes  │ │ 6 no INDEX   │ │ 3 membros    │                ║
    ║   │  Automatico  │ │ /consult     │ │ Avalia proc. │                ║
    ║   └──────────────┘ └──────────────┘ └──────────────┘                ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 5.2 — CARGO AGENTS (14 AGENTES REGISTRADOS)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  C-LEVEL (4):                                                    │
    │  ├── cfo        agents/cargo/c-level/cfo/                        │
    │  ├── coo        agents/cargo/c-level/coo/                        │
    │  ├── cmo        agents/cargo/c-level/cmo/                        │
    │  └── cro        agents/cargo/c-level/cro/                        │
    │                                                                  │
    │  SALES (9):                                                      │
    │  ├── sds                 SDR Specialist                          │
    │  ├── lns                 Lead Nurturing Specialist               │
    │  ├── bdr                 Business Development Rep                │
    │  ├── nepq-specialist     NEPQ Methodology                       │
    │  ├── sales-coordinator   Coordenacao de time                     │
    │  ├── sales-manager       Gestao de time                          │
    │  ├── sales-lead          Lideranca de vendas                     │
    │  ├── customer-success    CS e retencao                           │
    │  └── closer              Fechamento high-ticket                  │
    │                                                                  │
    │  MARKETING (1):                                                  │
    │  └── paid-media-specialist   Trafego pago                        │
    │                                                                  │
    │  Diretórios adicionais em agents/cargo/:                         │
    │  content/, design/, general/, growth/, hr/, operations/, tech/    │
    │  (templates preparados, agentes ainda nao registrados no INDEX)   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 5.3 — EXTERNAL AGENTS (MIND CLONES)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  6 REGISTRADOS NO AGENT-INDEX.yaml (com has_soul + has_memory):  │
    │  ├── the-scalable-company   Ryan Deiss / Scalable OS             │
    │  ├── cole-gordon            Closers.io / High-Ticket             │
    │  ├── jeremy-haynes          Megalodon / Paid Media               │
    │  ├── liam-ottley            AI Agency / MCP Architecture         │
    │  ├── alex-hormozi           Acquisition.com / Scaling            │
    │  └── jeremy-miner           7th Level / NEPQ                     │
    │                                                                  │
    │  7 ADICIONAIS NO FILESYSTEM (nao registrados no INDEX):          │
    │  ├── alan-nicolas           │  pedro-valerio                     │
    │  ├── full-sales-system      │  g4-educacao                       │
    │  ├── jordan-lee             │  richard-linder                    │
    │  └── sam-oven                                                    │
    │                                                                  │
    │  14 DNA PERSON DIRS em knowledge/external/dna/persons/:          │
    │  alan-nicolas, alex-hormozi, cole-gordon, full-sales-system,     │
    │  g4-educacao, jeremy-haynes, jeremy-miner, jordan-lee,           │
    │  liam-ottley, pedro-valerio, richard-linder, sam-oven,           │
    │  the-scalable-company, thiago-finch                              │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 5.4 — CONCLAVE (3 MEMBROS)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  agents/system/conclave/                                         │
    │  ├── critico-metodologico/   Avalia PROCESSO (score 0-100)       │
    │  ├── advogado-do-diabo/      ATACA premissas, identifica riscos  │
    │  └── sintetizador/           INTEGRA tudo em decisao final       │
    │                                                                  │
    │  Detalhado na SECAO 13.                                          │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 5.5 — SYSTEM SQUADS (2 SQUADS, 10 AGENTES)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  KNOWLEDGE OPS SQUAD — agents/system/knowledge-ops/              │
    │  ├── atlas/     The Classifier   (Steps 0-2)                     │
    │  ├── sage/      The Extractor    (Steps 3-8)                     │
    │  ├── lens/      The Validator    (Steps 9, 12)                   │
    │  ├── forge/     The Compiler     (Step 10)                       │
    │  └── echo/      The Cloner       (Steps 10-11)                   │
    │                                                                  │
    │  DEV OPS SQUAD — agents/system/dev-ops/                          │
    │  ├── anvil/     The Builder                                      │
    │  ├── compass/   The Designer                                     │
    │  ├── hawk/      The Tester                                       │
    │  ├── rocket/    The Deployer                                     │
    │  └── beacon/    The Planner                                      │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 5.6 — ESTRUTURA DE ARQUIVOS POR AGENTE

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  agents/{type}/{slug}/                                           │
    │  ├── AGENT.md          Definicao completa (Template V3, 11 pts) │
    │  ├── SOUL.md           Filosofia, inner game, identidade         │
    │  ├── MEMORY.md         Insights acumulados, scripts, citacoes    │
    │  └── DNA-CONFIG.yaml   Rastreabilidade de fontes + pesos         │
    │                                                                  │
    │  Cadeia obrigatoria:                                             │
    │  AGENT → SOUL → MEMORY → DNA → SOURCES (verificavel)            │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██████╗                                                      ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ██╔════╝                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ███████╗                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║    ██╔═══██╗                                                     ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝    ╚██████╔╝                                                     ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═════╝                                                      ====
====                                                                                                                ====
====     DNA SYSTEM — 5 LAYERS + VOICE-DNA + MCE BEHAVIORAL                                                         ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 6.1 — AS 5 CAMADAS COGNITIVAS (DNA SCHEMA)

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  knowledge/external/dna/persons/{SLUG}/                              ║
    ║                                                                      ║
    ║  ┌──────┬──────────────────┬──────────────────────────────────────┐  ║
    ║  │Layer │ Arquivo YAML     │ Conteudo                             │  ║
    ║  ├──────┼──────────────────┼──────────────────────────────────────┤  ║
    ║  │ L1   │ PHILOSOPHIES     │ Crencas, visao de mundo, "porques"   │  ║
    ║  │ L2   │ MENTAL-MODELS    │ Lentes de pensamento, frameworks     │  ║
    ║  │ L3   │ HEURISTICS       │ Regras de decisao com thresholds     │  ║
    ║  │ L4   │ FRAMEWORKS       │ Estruturas nomeadas e replicaveis    │  ║
    ║  │ L5   │ METHODOLOGIES    │ Processos passo-a-passo              │  ║
    ║  └──────┴──────────────────┴──────────────────────────────────────┘  ║
    ║                                                                      ║
    ║  + VOICE-DNA.yaml  (Step 8 output — perfil de voz)                   ║
    ║  + DNA-CONFIG.yaml (em agents/{type}/{slug}/ — rastreabilidade)       ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 6.2 — VOICE-DNA (6 DIMENSOES DE TOM)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  VOICE-DNA.yaml (extraido no Step 8 — MCE Voice)                 │
    │                                                                  │
    │  6 Dimensoes de Tom (escala 0-10):                                │
    │  ├── Certainty    Nivel de certeza nas afirmacoes                 │
    │  ├── Authority    Grau de autoridade projetado                    │
    │  ├── Warmth       Calor humano, empatia                          │
    │  ├── Directness   Quao direto/indireto                           │
    │  ├── Humor        Uso de humor como ferramenta                    │
    │  └── Formality    Formal vs casual                               │
    │                                                                  │
    │  + Signature phrases (frases marca registrada)                   │
    │  + Behavioral states (como reage sob pressao, em vitoria, etc.)  │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 6.3 — MCE BEHAVIORAL LAYERS (STEPS 6-7)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Step 6: MCE BEHAVIORAL                                          │
    │  ├── decision patterns      Como a pessoa toma decisoes          │
    │  ├── reaction patterns      Como reage a situacoes               │
    │  ├── habit patterns         Habitos recorrentes                   │
    │  └── communication patterns Como se comunica                     │
    │  Cada pattern precisa 2+ chunk_ids como evidencia.               │
    │                                                                  │
    │  Step 7: MCE IDENTITY                                            │
    │  ├── value_hierarchy        Hierarquia de valores (Tier 1-3)     │
    │  ├── obsessions             1 MASTER + N secondaries             │
    │  └── paradoxes              Contradicoes internas da pessoa      │
    │  Regra: Exatamente 1 MASTER obsession. Min 1 Tier 1 value.      │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 6.4 — CADEIA DE RASTREABILIDADE COMPLETA

```
    ┌──────────────────────────────────────────────────────────────────────┐
    │                                                                      │
    │  VIDEO ORIGINAL                                                      │
    │  "Liam Ottley - How to Build AI Agents.mp4"                          │
    │       │                                                              │
    │       v                                                              │
    │  TRANSCRICAO (knowledge/external/sources/{slug}/raw/)                │
    │  "[LO-0001] 1 - How to Build AI Agents.txt"                         │
    │       │                                                              │
    │       v                                                              │
    │  CHUNK (artifacts/chunks/CHUNKS-STATE.json)                          │
    │  chunk_LO01_001: "AI agents need structured workflows..."            │
    │       │                                                              │
    │       v                                                              │
    │  ENTIDADE CANONICA (artifacts/canonical/CANONICAL-MAP.json)          │
    │  "Liam" + "Ottley" + "LO" → "Liam Ottley" (conf: 0.95)             │
    │       │                                                              │
    │       v                                                              │
    │  INSIGHT (artifacts/insights/INSIGHTS-STATE.json)                    │
    │  LO01-FW001: "MCP Architecture Pattern" | tag: FRAMEWORK | HIGH     │
    │       │                                                              │
    │       v                                                              │
    │  MCE BEHAVIORAL (INSIGHTS-STATE behavioral_patterns[])               │
    │  decision_pattern: "Build systems before scaling"                    │
    │       │                                                              │
    │       v                                                              │
    │  DNA YAML (knowledge/external/dna/persons/liam-ottley/)              │
    │  FRAMEWORKS.yaml: "MCP Architecture Pattern" | weight: 0.95         │
    │  VOICE-DNA.yaml: certainty=8, authority=7, humor=4                   │
    │       │                                                              │
    │       v                                                              │
    │  DOSSIER (knowledge/external/dossiers/persons/DOSSIER-LIAM-OTTLEY)   │
    │  Compilacao com [chunk_LO01_001] inline                              │
    │       │                                                              │
    │       v                                                              │
    │  AGENTE (agents/external/liam-ottley/)                               │
    │  AGENT.md + SOUL.md + MEMORY.md + DNA-CONFIG.yaml                    │
    │       │                                                              │
    │       v                                                              │
    │  RESPOSTA AO USUARIO                                                 │
    │  "Segundo Liam Ottley, a arquitetura MCP..."                         │
    │  [Fonte: LO-0001, AI Agency Content]                                 │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗     ███████╗                                                      ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ╚════██║                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║        ██╔╝                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║       ██╔╝                                                       ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝       ██║                                                        ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝       ╚═╝                                                        ====
====                                                                                                                ====
====     GOVERNANCE & RULES — SYNAPSE 26 RULES + CONSTITUTION ENGINE                                                ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 7.1 — SYNAPSE ENGINE (3 LAYERS, 26 REGRAS)

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  core/engine/synapse.py — Motor de resolucao de regras               ║
    ║  core/engine/rules/     — Definicoes YAML                            ║
    ║  .claude/rules/synapse-digest.md — Digest auto-gerado                ║
    ║                                                                      ║
    ║  ┌────────┬──────────────────┬───────┬────────────────────────────┐  ║
    ║  │ Layer  │ Nome             │ Rules │ Severidade                 │  ║
    ║  ├────────┼──────────────────┼───────┼────────────────────────────┤  ║
    ║  │ L0     │ Constitution     │ 8     │ block (4), warn (2)        │  ║
    ║  │ L1     │ Global Rules     │ 10    │ warn (7), info (3)         │  ║
    ║  │ L6     │ Keyword Rules    │ 8     │ info (8) — lazy loading    │  ║
    ║  └────────┴──────────────────┴───────┴────────────────────────────┘  ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 7.2 — L0 CONSTITUTION (8 REGRAS — BLOCK/WARN)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  BLOCK (4 regras — bloqueiam execucao):                          │
    │  ├── no-secrets-in-files     Nunca credentials em tracked files  │
    │  ├── agent-integrity         100% rastreavel a sources           │
    │  ├── agent-traceability      Cadeia AGENT→SOUL→MEMORY→DNA       │
    │  ├── no-invention            Zero invencao. Fortify OK, invent NO│
    │  ├── formal-workflow-required PRD→architect→SM→PO→exec           │
    │  └── mcp-credentials-env-only MCP sem plaintext tokens           │
    │                                                                  │
    │  WARN (2 regras — alertam mas nao bloqueiam):                    │
    │  ├── no-hardcoded-paths      Usar core.paths ROUTING             │
    │  └── epistemic-honesty       Separar fatos de recomendacoes      │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 7.3 — L1 GLOBAL (10 REGRAS)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  WARN (7):                                                       │
    │  ├── sequential-processing    Fases sao sequenciais e blocking   │
    │  ├── directory-contract       Output via core/paths.py ROUTING   │
    │  ├── template-enforcement     Template V3 com 11 partes          │
    │  ├── cascading-mandatory      Cascading apos extracao            │
    │  ├── hook-timeout-required    Timeout em todo hook (30s rec.)    │
    │  ├── session-persistence      Autosave em checkpoints            │
    │  └── source-marking           Todo arquivo com [SOURCE]_[NAME]   │
    │                                                                  │
    │  INFO (3):                                                       │
    │  ├── dual-location-logging    Logs em .md E .jsonl               │
    │  ├── mcp-native-tools-first   Preferir tools nativos sobre MCP   │
    │  └── plan-mode-complex-tasks  Plan mode para tarefas complexas   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 7.4 — L6 KEYWORD RULES (8 REGRAS — LAZY LOADING)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Ativadas por keyword detection no prompt do usuario:            │
    │                                                                  │
    │  batch-processing-rules      batch, pipeline, processing         │
    │  agent-creation-rules        agent, create, dossier              │
    │  github-workflow-rules       github, git, push, pr, branch       │
    │  phase5-execution            phase, dossier, cascading, agent    │
    │  conclave-protocol           conclave, council, debate           │
    │  source-sync-rules           sync, planilha, download            │
    │  session-management          session, save, resume, state        │
    │  knowledge-bucket-routing    bucket, inbox, knowledge            │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 7.5 — CONSTITUTION AUTO-GENERATION ENGINE

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  core/governance/engine.py                                       │
    │                                                                  │
    │  Le 9 fontes:                                                    │
    │  ├── AGENT-INDEX.yaml          Registro de agentes               │
    │  ├── settings.json             Hooks e deny rules                │
    │  ├── core/paths.py             Contrato de diretorios            │
    │  ├── core/engine/rules/*.yaml  Regras L0, L1, L6                 │
    │  ├── pyproject.toml            Versao e deps                     │
    │  ├── .mcp.json                 Servidores MCP                    │
    │  └── ...                                                         │
    │                                                                  │
    │  Gera 5 documentos:                                              │
    │  ├── docs/architecture/constitution.md    Sistema completo       │
    │  ├── docs/architecture/source-tree.md     Arvore de diretorios   │
    │  ├── .claude/rules/synapse-digest.md      Digest de regras       │
    │  ├── .claude/CLAUDE.md (secao Agents)     Auto-update do total   │
    │  └── docs/architecture/pipeline-logging-guide.md (referencia)    │
    │                                                                  │
    │  Trigger: PostToolUse hook governance_auto_update.py              │
    │  Tempo de execucao: ~0.04s                                       │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      █████╗                                                       ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ██╔══██╗                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚█████╔╝                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║    ██╔══██╗                                                      ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝    ╚█████╔╝                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚════╝                                                       ====
====                                                                                                                ====
====     HOOKS SYSTEM — 34 HOOKS x 5 EVENTS                                                                         ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 8.1 — DISTRIBUICAO POR EVENTO

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  Configurados em: .claude/settings.json                              ║
    ║  Linguagem: Python 3, stdlib + PyYAML only                           ║
    ║  Timeout padrao: 5s (hooks leves) a 15s (governance)                 ║
    ║                                                                      ║
    ║  ┌────────────────────┬───────┬────────────────────────────────────┐ ║
    ║  │ Evento             │ Count │ Hooks                              │ ║
    ║  ├────────────────────┼───────┼────────────────────────────────────┤ ║
    ║  │ SessionStart       │   7   │ session_start.py                   │ ║
    ║  │                    │       │ skill_indexer.py                    │ ║
    ║  │                    │       │ inbox_age_alert.py                  │ ║
    ║  │                    │       │ session_index.py                    │ ║
    ║  │                    │       │ session_autosave_v2.py              │ ║
    ║  │                    │       │ session-source-sync.py              │ ║
    ║  │                    │       │ startup_health.py                   │ ║
    ║  ├────────────────────┼───────┼────────────────────────────────────┤ ║
    ║  │ UserPromptSubmit   │   5   │ skill_router.py                    │ ║
    ║  │                    │       │ quality_watchdog.py                 │ ║
    ║  │                    │       │ user_prompt_submit.py               │ ║
    ║  │                    │       │ memory_hints_injector.py            │ ║
    ║  │                    │       │ memory_updater.py                   │ ║
    ║  ├────────────────────┼───────┼────────────────────────────────────┤ ║
    ║  │ PreToolUse         │   5   │ claude_md_guard.py                  │ ║
    ║  │ (matcher Write|    │       │ creation_validator.py               │ ║
    ║  │  Edit)             │       │ directory_contract_guard.py         │ ║
    ║  │                    │       │ pre_commit_audit.py                 │ ║
    ║  │                    │       │ agent_deprecation_guard.py          │ ║
    ║  ├────────────────────┼───────┼────────────────────────────────────┤ ║
    ║  │ PostToolUse        │  13   │ post_tool_use.py                   │ ║
    ║  │ (12 global +       │       │ enforce_dual_location.py           │ ║
    ║  │  1 Write|Edit)     │       │ pipeline_checkpoint.py             │ ║
    ║  │                    │       │ agent_creation_trigger.py           │ ║
    ║  │                    │       │ agent_index_updater.py              │ ║
    ║  │                    │       │ claude_md_agent_sync.py             │ ║
    ║  │                    │       │ agent_memory_persister.py           │ ║
    ║  │                    │       │ memory_capture.py                   │ ║
    ║  │                    │       │ post_batch_cascading.py             │ ║
    ║  │                    │       │ pipeline_phase_gate.py              │ ║
    ║  │                    │       │ pipeline_orchestrator.py            │ ║
    ║  │                    │       │ pipeline_guard.py                   │ ║
    ║  │                    │       │ governance_auto_update.py (W|E)     │ ║
    ║  ├────────────────────┼───────┼────────────────────────────────────┤ ║
    ║  │ Stop               │   4   │ stop_hook_completeness.py          │ ║
    ║  │                    │       │ session_end.py                      │ ║
    ║  │                    │       │ memory_manager_stop.py              │ ║
    ║  │                    │       │ session_index.py                    │ ║
    ║  └────────────────────┴───────┴────────────────────────────────────┘ ║
    ║                                                                      ║
    ║  TOTAL: 34 hooks (7 + 5 + 5 + 13 + 4)                               ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 8.2 — DENY RULES (12 REGRAS DE SEGURANCA)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Configurados em: .claude/settings.json → permissions.deny       │
    │                                                                  │
    │  BASH:                                                           │
    │  ├── Bash(rm:-rf *)          Bloqueio de delete recursivo        │
    │  ├── Bash(curl:*)            Bloqueio de downloads               │
    │  └── Bash(wget:*)            Bloqueio de downloads               │
    │                                                                  │
    │  .ENV (6 regras — Read + Write + Edit para *.env e */.env):      │
    │  ├── Read(*.env)  / Read(*/.env)                                 │
    │  ├── Write(*.env) / Write(*/.env)                                │
    │  └── Edit(*.env)  / Edit(*/.env)                                 │
    │                                                                  │
    │  SSH (3 regras):                                                 │
    │  ├── Read(~/.ssh/*)                                              │
    │  ├── Write(~/.ssh/*)                                             │
    │  └── Edit(~/.ssh/*)                                              │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      █████╗                                                       ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ██╔══██╗                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██████║                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ╚═══██║                                                      ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     █████╔╝                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚════╝                                                       ====
====                                                                                                                ====
====     LOGGING ARCHITECTURE — 13 JSONL + DUAL-LOCATION                                                            ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 9.1 — ESTRATEGIA DUAL-LOCATION

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Toda acao do pipeline gera logs em DOIS locais:                 │
    │                                                                  │
    │                   ┌────────────────────┐                         │
    │                   │  PIPELINE ACTION   │                         │
    │                   └─────────┬──────────┘                         │
    │                             │                                    │
    │              ┌──────────────┴──────────────┐                     │
    │              v                              v                    │
    │       ┌─────────────┐              ┌──────────────┐             │
    │       │ HUMAN LOG   │              │ MACHINE LOG  │             │
    │       │   (.md)     │              │  (.jsonl)    │             │
    │       └──────┬──────┘              └──────┬───────┘             │
    │              │                             │                    │
    │    logs/mce/{SLUG}/              logs/*.jsonl +                 │
    │    MCE-{TAG}.md                  .claude/mission-control/       │
    │                                  mce/{SLUG}/*.yaml              │
    │                                                                  │
    │  REGRA: Se nao foi logado, nao foi processado.                   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 9.2 — OS 13 ARQUIVOS JSONL

```
    ╔═══════╤═══════════════════════════════╤════════════════════════════════╗
    ║  #    │ Log File                      │ O que registra                 ║
    ╠═══════╪═══════════════════════════════╪════════════════════════════════╣
    ║  1    │ mce-orchestrate.jsonl         │ Cada comando MCE               ║
    ║  2    │ mce-metrics.jsonl             │ Wall-clock timing por fase     ║
    ║  3    │ scope-classifier.jsonl        │ 6-signal classification        ║
    ║  4    │ smart-router.jsonl            │ Decisoes de roteamento         ║
    ║  5    │ batch-auto-creator.jsonl      │ Criacao de batches             ║
    ║  6    │ memory-enricher.jsonl         │ Insight → MEMORY.md routing    ║
    ║  7    │ workspace-sync.jsonl          │ Business → workspace sync      ║
    ║  8    │ agent-creation.jsonl          │ MCE threshold triggers         ║
    ║  9    │ agent-index-updates.jsonl     │ AGENT-INDEX.yaml changes       ║
    ║ 10    │ pipeline-checkpoints.jsonl    │ Pipeline state snapshots       ║
    ║ 11    │ pipeline-guard.jsonl          │ Output path validation         ║
    ║ 12    │ claude-md-sync.jsonl          │ CLAUDE.md auto-updates         ║
    ║ 13    │ prompts.jsonl                 │ Prompt execution tracking      ║
    ╚═══════╧═══════════════════════════════╧════════════════════════════════╝

    Localizacao: logs/ (L3 — gitignored)
```

## 9.3 — HUMAN-READABLE LOG (MCE TEMPLATE)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md                │
    │  423 linhas, preenchimento progressivo                           │
    │                                                                  │
    │  Status markers:                                                 │
    │  ├── [*] PENDENTE       Step nao executado ainda                 │
    │  ├── [~] EM ANDAMENTO   Step em execucao                         │
    │  └── [@] COMPLETO       Step finalizado com dados                │
    │                                                                  │
    │  Output path: logs/mce/{SLUG}/MCE-{TAG}.md                       │
    │                                                                  │
    │  Progress bar:                                                   │
    │  Classification   [@@@@@@@@@@@] 100%                             │
    │  Organization     [@@@@@@@@@@@] 100%                             │
    │  Chunking         [~~~~~~~~~~~]  IN PROGRESS                     │
    │  Entity Res.      [-----------]  PENDENTE                        │
    │  ...                                                             │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗ ██████╗                                                  ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║██╔═████╗                                                 ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║██║██╔██║                                                 ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║████╔╝██║                                                 ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║╚██████╔╝                                                 ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝ ╚═════╝                                                  ====
====                                                                                                                ====
====     WORKSPACE — 8 DEPARTAMENTOS + CLICKUP MIRROR                                                               ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 10.1 — ESTRUTURA DEPARTAMENTAL

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  workspace/ — L1 template, L2 quando populado                        ║
    ║                                                                      ║
    ║  ├── _system/                  Configuracao do workspace             ║
    ║  │   ├── config/               Mapeamentos e IDs                    ║
    ║  │   ├── CLICKUP-IDS.json      IDs das Spaces do ClickUp            ║
    ║  │   ├── DRIVE-FOLDER-IDS.json IDs do Google Drive                  ║
    ║  │   └── SETUP-PENDING.md      Itens pendentes de setup             ║
    ║  │                                                                   ║
    ║  ├── _templates/               SOPs validados                       ║
    ║  │   ├── content/              Templates de conteudo                 ║
    ║  │   ├── delivery/             Templates de delivery                 ║
    ║  │   ├── hiring/               Templates de contratacao              ║
    ║  │   ├── operations/           Templates operacionais                ║
    ║  │   └── sales-process/        Templates comerciais                  ║
    ║  │                                                                   ║
    ║  ├── aios/                     Centro de AI Operations               ║
    ║  │   ├── agents/               Registro de agentes ativos            ║
    ║  │   ├── squads/               Definicao de squads                   ║
    ║  │   ├── workflows/            Automacoes e fluxos                   ║
    ║  │   ├── tools/                Ferramentas configuradas              ║
    ║  │   ├── knowledge/            Base de conhecimento AI               ║
    ║  │   ├── checklists/           Checklists operacionais               ║
    ║  │   ├── tasks/                Task definitions                      ║
    ║  │   ├── templates/            Templates de AI                       ║
    ║  │   └── library/              Biblioteca de recursos                ║
    ║  │                                                                   ║
    ║  ├── ops/                      Operacoes                             ║
    ║  │   ├── meetings/             Atas e logs de reunioes               ║
    ║  │   ├── eventos/              Eventos e conferencias                ║
    ║  │   ├── sprints/              Logs de sprint                        ║
    ║  │   └── processos-sops/       SOPs operacionais                     ║
    ║  │                                                                   ║
    ║  ├── delivery/                 Entrega de servicos                   ║
    ║  │   ├── prospeccao-leads/     Pipeline de leads                     ║
    ║  │   ├── gestao-projetos/      Gestao de projetos                    ║
    ║  │   ├── account-cs/           Customer Success                      ║
    ║  │   ├── content-factory/      Producao de conteudo                   ║
    ║  │   ├── trafego-pago/         Trafego pago                          ║
    ║  │   ├── genai/                GenAI delivery                        ║
    ║  │   ├── edicao/               Edicao de video                       ║
    ║  │   ├── producao-filmagem/    Producao e filmagem                    ║
    ║  │   └── copy/                 Copywriting                           ║
    ║  │                                                                   ║
    ║  ├── comercial/                Comercial                             ║
    ║  │   └── crm/                  CRM central                           ║
    ║  │       ├── pipeline-sdr/     Pipeline SDR                          ║
    ║  │       ├── pipeline-closer/  Pipeline Closer                       ║
    ║  │       ├── clientes/         Base de clientes                       ║
    ║  │       └── propostas-comerciais/                                    ║
    ║  │                                                                   ║
    ║  ├── gestao/                   Gestao                                ║
    ║  │   ├── financeiro/           Financas                              ║
    ║  │   ├── juridico/             Juridico                              ║
    ║  │   ├── administrativo/       Admin                                 ║
    ║  │   └── acessos-ferramentas/  Ferramentas e acessos                 ║
    ║  │                                                                   ║
    ║  ├── gente-cultura/            Gente & Cultura (RH)                  ║
    ║  │   ├── equipe/               Time (SOW, scorecards, cargos)        ║
    ║  │   ├── okrs/                 OKRs                                  ║
    ║  │   ├── recrutamento/         Recrutamento                          ║
    ║  │   └── educacional/          Treinamento e educacao                ║
    ║  │                                                                   ║
    ║  ├── marketing/                Marketing                             ║
    ║  │   ├── performance-growth/   Growth e performance                   ║
    ║  │   ├── campanhas-lancamentos/ Campanhas                            ║
    ║  │   └── creative-library/     Biblioteca de criativos                ║
    ║  │                                                                   ║
    ║  ├── strategy/                 Estrategia                            ║
    ║  │   └── decisions/            Registro de decisoes                   ║
    ║  │                                                                   ║
    ║  ├── businesses/               DNA por Business Unit                  ║
    ║  │   (12 folders padrao por BU: ai, analytics, brand, company,       ║
    ║  │    copy, design-system, evidence, movement, operations,           ║
    ║  │    products, tech, _preserved)                                    ║
    ║  │                                                                   ║
    ║  └── inbox/                    Inbox do workspace                     ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗██╗                                                       ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║███║                                                      ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║╚██║                                                      ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║ ██║                                                      ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║ ██║                                                      ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝ ╚═╝                                                      ====
====                                                                                                                ====
====     .CLAUDE CORE — 100 SKILLS, 34 HOOKS, RULES, SESSIONS                                                       ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 11.1 — ANATOMIA DO .CLAUDE

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  .claude/                                                            ║
    ║  ├── CLAUDE.md              Sistema overview (auto-updated)          ║
    ║  ├── settings.json          Hooks + deny rules (distributed)         ║
    ║  ├── settings.local.json    Local overrides                          ║
    ║  │                                                                   ║
    ║  ├── hooks/ (34 scripts)    Automacao Python                         ║
    ║  │   Detalhado na SECAO 8                                            ║
    ║  │                                                                   ║
    ║  ├── skills/ (100 dirs)     Skills ativaveis por slash command        ║
    ║  │   Cada skill: SKILL.md (definicao) + assets opcionais             ║
    ║  │   Categorias principais:                                          ║
    ║  │   ├── Pipeline:    pipeline-mce, pipeline-jarvis, ingest          ║
    ║  │   ├── Knowledge:   knowledge-extraction, graph-search,            ║
    ║  │   │                memory-search, shared-memory                   ║
    ║  │   ├── Session:     save, resume, session-launcher                 ║
    ║  │   ├── Agent:       agent-creation, clone-mind, squad-creator      ║
    ║  │   ├── Dev:         commit, code-review, deploy, gha,             ║
    ║  │   │                feature-dev, story-cycle, epic-cycle           ║
    ║  │   ├── Research:    deep-research, tech-research, x-research      ║
    ║  │   ├── Content:     copy, storytelling, book-summary              ║
    ║  │   ├── Integration: read-ai-harvester, transcribe,                ║
    ║  │   │                gdrive-transcription-downloader               ║
    ║  │   └── System:      jarvis-briefing, jarvis, verify,              ║
    ║  │                    validation-test, teaching                      ║
    ║  │                                                                   ║
    ║  ├── commands/              Slash commands (agents/)                  ║
    ║  │                                                                   ║
    ║  ├── rules/                 Regras on-demand (6 grupos)              ║
    ║  │   ├── synapse-digest.md  Digest auto-gerado (26 regras)          ║
    ║  │   ├── RULE-GROUP-1.md    Phases, pipeline, batch                  ║
    ║  │   ├── RULE-GROUP-2.md    Sessions, save, resume                   ║
    ║  │   ├── RULE-GROUP-3.md    Parallel, templates, KPIs                ║
    ║  │   ├── RULE-GROUP-4.md    Agents, dossiers, cascading              ║
    ║  │   ├── RULE-GROUP-5.md    Source-sync, integrity                   ║
    ║  │   └── RULE-GROUP-6.md    Skills, sub-agents, GitHub               ║
    ║  │                                                                   ║
    ║  ├── mission-control/       Centro de controle (state files)          ║
    ║  │   ├── mce/{SLUG}/        Estado por pipeline MCE                  ║
    ║  │   ├── BATCH-REGISTRY.json                                        ║
    ║  │   ├── TRIAGE-QUEUE.json                                          ║
    ║  │   ├── WATCHER-STATE.json                                         ║
    ║  │   ├── READ-AI-STATE.json                                         ║
    ║  │   ├── FIREFLIES-STATE.json                                       ║
    ║  │   └── ...                                                        ║
    ║  │                                                                   ║
    ║  ├── sessions/              Sessoes salvas                           ║
    ║  ├── agent-memory/          Memoria persistente por agente            ║
    ║  ├── jarvis/                Identidade JARVIS + sub-agents            ║
    ║  └── trash/                 Lixeira (nunca delete, sempre move)       ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗██████╗                                                   ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║╚════██╗                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║ █████╔╝                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║██╔═══╝                                                   ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║███████╗                                                  ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝╚══════╝                                                  ====
====                                                                                                                ====
====     INTEGRATIONS — READ.AI, FIREFLIES, N8N, MCP                                                                ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 12.1 — MCP SERVERS (2 ATIVOS)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Configurados em: .mcp.json                                      │
    │                                                                  │
    │  ├── mega-brain-knowledge     RAG knowledge access tools         │
    │  └── n8n-mcp                  N8N workflow management            │
    │                                                                  │
    │  Gmail e Google Calendar: disponiveis como deferred tools        │
    │  (nao MCP servers, mas integracoes Claude nativas)               │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 12.2 — READ.AI

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Tipo: OAuth via MCP Remote                                      │
    │  Config: .mcp.json → read-ai server (mcp-remote)                 │
    │  Pipeline: core/intelligence/pipeline/read_ai_{config,oauth}.py  │
    │  State: .claude/mission-control/READ-AI-STATE.json               │
    │  Meetings harvested: 10+ (MEET-0001 a MEET-0010)                 │
    │  Owner: thiago@bilhon.com                                        │
    │  Status: OAuth token OK, API /v1/meetings precisa investigacao   │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 12.3 — FIREFLIES.AI

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Tipo: GraphQL API (Bearer token, NAO OAuth)                     │
    │  API: api.fireflies.ai/graphql                                   │
    │  Account: contato@thiagofinch.com                                │
    │  Config: core/intelligence/pipeline/fireflies_config.py          │
    │  Sync: core/intelligence/pipeline/fireflies_sync.py (poll 5min)  │
    │  State: .claude/mission-control/FIREFLIES-STATE.json             │
    │  Meetings: 50 (30 empresa + 20 pessoal)                          │
    │  Tag sequence: MEET-XXXX (compartilhado com Read.ai)             │
    │  LaunchAgent: ~/Library/LaunchAgents/com.bilhon.fireflies-sync   │
    │  Status: LIVE                                                    │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 12.4 — N8N

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  MCP: n8n-mcp (via .mcp.json)                                    │
    │  Cloud: n8n.io (NAO self-hosted)                                 │
    │  Webhook: Read.ai → N8N → Mega Brain                             │
    │  URL de producao: .env → N8N_WEBHOOK_URL                         │
    │  Bug conhecido: Webhooks criados via API retornam 404            │
    │  Workaround: Criar webhook workflows via N8N UI manualmente      │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗██████╗                                                   ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║╚════██╗                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║ █████╔╝                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║ ╚═══██╗                                                  ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║██████╔╝                                                  ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝╚═════╝                                                   ====
====                                                                                                                ====
====     CONCLAVE — 3 MEMBROS, PROTOCOLO DE DEBATE                                                                  ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 13.1 — O TRIBUNAL DE DECISOES

```
    ┌──────────────────────────────────────────────────────────────────────┐
    │                                                                      │
    │  COUNCIL — Ativado via /conclave                                     │
    │  Trigger: 2+ agentes debatem | /board | decisao HIGH impact          │
    │                                                                      │
    │  ┌──────────────────────────────────────────────────────────────┐    │
    │  │  MEMBRO 1: CRITICO METODOLOGICO                              │    │
    │  │  Avalia qualidade do PROCESSO (nao do conteudo)               │    │
    │  │  Score 0-100 (Premissas + Evidencias + Logica +              │    │
    │  │  Alternativas + Conflitos, 20pts cada)                       │    │
    │  ├──────────────────────────────────────────────────────────────┤    │
    │  │  MEMBRO 2: ADVOGADO DO DIABO                                 │    │
    │  │  ATACA premissas, identifica riscos                          │    │
    │  │  "Em 12 meses, do que nos arrependeriamos?"                  │    │
    │  ├──────────────────────────────────────────────────────────────┤    │
    │  │  MEMBRO 3: SINTETIZADOR                                      │    │
    │  │  Integra tudo em decisao final                               │    │
    │  │  Confianca 0-100% + riscos + criterios de reversao           │    │
    │  └──────────────────────────────────────────────────────────────┘    │
    │                                                                      │
    │  THRESHOLDS:                                                         │
    │  >= 70%: EMITIR decisao final                                        │
    │  50-69%: EMITIR com ressalvas                                        │
    │  < 50%:  ESCALAR para humano (NAO re-rodar)                          │
    │                                                                      │
    │  7 REGRAS INVIOLAVEIS:                                               │
    │  1. Council NAO tem DNA de dominio                                  │
    │  2. Critico avalia PROCESSO, nao corretude                          │
    │  3. Advogado ATACA, nao confirma                                    │
    │  4. Sintetizador INTEGRA, nao medeia                                │
    │  5. < 50%: ESCALAR, nao re-rodar                                    │
    │  6. UMA passagem por query (anti-loop)                              │
    │  7. Transparencia total                                             │
    │                                                                      │
    │  Templates: core/templates/debates/                                   │
    │  ├── CONCLAVE-LOG-TEMPLATE-v2.md                                     │
    │  ├── conclave-protocol.md                                            │
    │  ├── debate-dynamics-config.yaml                                     │
    │  └── debate-protocol.md                                              │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗██╗  ██╗                                                  ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║██║  ██║                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║███████║                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║╚════██║                                                  ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║     ██║                                                  ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝     ╚═╝                                                  ====
====                                                                                                                ====
====     PATHS CONTRACT — core/paths.py, 131 ROUTING KEYS                                                           ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 14.1 — CATEGORIAS DE ROUTING

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  core/paths.py — Single Source of Truth para todos os paths          ║
    ║  131 ROUTING keys organizados por categoria:                         ║
    ║                                                                      ║
    ║  ┌───────────────┬───────┬──────────────────────────────────────┐   ║
    ║  │ Categoria     │ Keys  │ Exemplos                             │   ║
    ║  ├───────────────┼───────┼──────────────────────────────────────┤   ║
    ║  │ workspace     │  54   │ workspace_aios, workspace_meetings,  │   ║
    ║  │               │       │ workspace_crm, workspace_team, ...   │   ║
    ║  │ business      │   7   │ business_inbox, business_dossiers,   │   ║
    ║  │               │       │ business_insights, business_sops     │   ║
    ║  │ personal      │   7   │ personal_email, personal_calls,      │   ║
    ║  │               │       │ personal_cognitive, personal_inbox   │   ║
    ║  │ agents        │   7   │ agents_external, agents_cargo,       │   ║
    ║  │               │       │ agents_knowledge_ops, agents_dev_ops │   ║
    ║  │ rag           │   4   │ rag_chunks, rag_vectors, rag_expert, │   ║
    ║  │               │       │ rag_business                         │   ║
    ║  │ mce           │   3   │ mce_state, mce_metrics_log, mce_cache│   ║
    ║  │ batch         │   3   │ batch_log, batch_registry,           │   ║
    ║  │               │       │ batch_auto_creator_log               │   ║
    ║  │ read          │   3   │ read_ai_log, read_ai_state,          │   ║
    ║  │               │       │ read_ai_staging                      │   ║
    ║  │ ss            │   2   │ ss_bridge_config, ss_bridge_log      │   ║
    ║  │ watcher       │   2   │ watcher_state, watcher_log           │   ║
    ║  │ memory        │   2   │ memory_enricher_log, memory_split    │   ║
    ║  │ (outros 37)   │  37   │ session_log, mission_state,          │   ║
    ║  │               │       │ audit_report, entity_registry, ...   │   ║
    ║  └───────────────┴───────┴──────────────────────────────────────┘   ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 14.2 — 4 BUCKET PATHS

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Bucket     │ Base Path               │ Inbox                    │
    │ ────────────┼─────────────────────────┼──────────────────────    │
    │  External   │ knowledge/external/     │ knowledge/external/inbox │
    │  Business   │ knowledge/business/     │ knowledge/business/inbox │
    │  Personal   │ knowledge/personal/     │ knowledge/personal/inbox │
    │  Workspace  │ workspace/              │ workspace/inbox          │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 14.3 — PROHIBITED DIRECTORIES

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Novos arquivos NAO PODEM ser criados em:                        │
    │                                                                  │
    │  ├── docs/                Usar reference/ em vez                  │
    │  ├── workspace/domains/   Removido S13: departamental spaces     │
    │  └── workspace/providers/ Removido S13: gestao/acessos-ferramentas│
    │                                                                  │
    │  Guard: directory_contract_guard.py (PreToolUse)                  │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗███████╗                                                  ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║██╔════╝                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║███████╗                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║╚════██║                                                  ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║███████║                                                  ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝╚══════╝                                                  ====
====                                                                                                                ====
====     TRACEABILITY CHAIN — VIDEO → CHUNK → ENTITY → INSIGHT → MCE → DNA → AGENT                                 ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 15.1 — CADEIA COMPLETA (12 ELOS)

```
    ┌──────────────────────────────────────────────────────────────────────┐
    │                                                                      │
    │  1. VIDEO ORIGINAL                                                   │
    │     "Cole Gordon - How to Close High-Ticket.mp4"                     │
    │           │                                                          │
    │           v                                                          │
    │  2. TRANSCRICAO → knowledge/external/sources/{slug}/raw/             │
    │     "[CG-0042] 42 - How to Close High-Ticket.txt"                    │
    │           │                                                          │
    │           v                                                          │
    │  3. SCOPE CLASSIFICATION (Step 1)                                    │
    │     bucket=external, confidence=0.92, signals=[S1,S2,S5]             │
    │           │                                                          │
    │           v                                                          │
    │  4. CHUNK (Step 3) → artifacts/chunks/CHUNKS-STATE.json              │
    │     chunk_CG42_001: "O sistema e mais importante que o closer..."    │
    │     ~300 palavras, metadados preservados                             │
    │           │                                                          │
    │           v                                                          │
    │  5. ENTITY RESOLUTION (Step 4) → artifacts/canonical/CANONICAL-MAP   │
    │     "Cole" + "CG" + "Gordon" → "Cole Gordon" (conf: 0.95)           │
    │     MERGE com map existente. NUNCA overwrite.                        │
    │           │                                                          │
    │           v                                                          │
    │  6. INSIGHT EXTRACTION (Step 5) → artifacts/insights/INSIGHTS-STATE  │
    │     CG42-HP001: "Sistemas > Individuos"                              │
    │     tag: FILOSOFIA | priority: HIGH | confidence: HIGH               │
    │           │                                                          │
    │           v                                                          │
    │  7. MCE BEHAVIORAL (Step 6) → INSIGHTS-STATE.behavioral_patterns[]   │
    │     decision_pattern: "Build systems before people"                  │
    │     evidence: [chunk_CG42_001, chunk_CG42_003]                       │
    │           │                                                          │
    │           v                                                          │
    │  8. MCE IDENTITY (Step 7) → INSIGHTS-STATE.identity{}                │
    │     value_hierarchy: {tier1: "Scalability", tier2: "Process"}        │
    │     obsessions: {master: "Repeatable Playbooks"}                     │
    │           │                                                          │
    │           v                                                          │
    │  9. MCE VOICE (Step 8) → knowledge/external/dna/persons/{SLUG}/     │
    │     VOICE-DNA.yaml: certainty=9, authority=8, directness=9           │
    │           │                                                          │
    │           v                                                          │
    │  10. DNA YAMLs (Step 10) → knowledge/external/dna/persons/{SLUG}/   │
    │      PHILOSOPHIES.yaml: "Sistemas > Individuos" | weight: 0.95      │
    │      FRAMEWORKS.yaml + HEURISTICS.yaml + METHODOLOGIES.yaml + ...   │
    │           │                                                          │
    │           v                                                          │
    │  11. DOSSIER (Step 10) → knowledge/external/dossiers/persons/       │
    │      DOSSIER-COLE-GORDON.md com [chunk_CG42_001] inline              │
    │           │                                                          │
    │           v                                                          │
    │  12. AGENTE (Step 10) → agents/external/cole-gordon/                 │
    │      AGENT.md + SOUL.md + MEMORY.md + DNA-CONFIG.yaml                │
    │      Cadeia: AGENT → SOUL → MEMORY → DNA → SOURCES (verificavel)    │
    │           │                                                          │
    │           v                                                          │
    │  RESPOSTA AO USUARIO                                                 │
    │  "Segundo Cole Gordon, o sistema e mais importante que o closer      │
    │   individual. [Fonte: CG-0042, EAD-CLOSER]"                         │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗ ██████╗                                                  ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║██╔════╝                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║███████╗                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║██╔═══██╗                                                 ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║╚██████╔╝                                                 ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝ ╚═════╝                                                  ====
====                                                                                                                ====
====     TESTING & QUALITY — 502 TESTS, RUFF, GOVERNANCE                                                            ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

## 16.1 — SUITE DE TESTES

```
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  502 testes coletados, 0 falhas                                      ║
    ║  Tempo de colecao: 0.22s                                             ║
    ║                                                                      ║
    ║  Categorias:                                                         ║
    ║  ├── Layer classification tests     44 testes                        ║
    ║  ├── RAG chunker tests              13 testes                        ║
    ║  ├── Bucket processor tests         22 testes                        ║
    ║  ├── Memory manager tests           28 testes                        ║
    ║  ├── Context scorer tests           14 testes                        ║
    ║  ├── Persona tests                  91 testes                        ║
    ║  └── Outros (pipeline, agents...)  290 testes                        ║
    ║                                                                      ║
    ║  Executor: pytest (configurado em pyproject.toml)                    ║
    ║  Lint: ruff (0 erros em core/ + .claude/hooks/)                      ║
    ║  Type check: pyright (configurado em pyproject.toml)                 ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
```

## 16.2 — GOVERNANCE AUTO-UPDATE

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  core/governance/engine.py                                       │
    │  Tempo de execucao: ~0.04s                                       │
    │                                                                  │
    │  Trigger: governance_auto_update.py (PostToolUse, Write|Edit)    │
    │                                                                  │
    │  Quando um arquivo fonte muda (AGENT-INDEX.yaml, settings.json,  │
    │  paths.py, rules/*.yaml), o hook detecta e regenera:            │
    │  ├── docs/architecture/constitution.md                           │
    │  ├── docs/architecture/source-tree.md                            │
    │  ├── .claude/rules/synapse-digest.md                             │
    │  └── .claude/CLAUDE.md (secao de contagem de agentes)            │
    │                                                                  │
    │  Pipeline guard: core/governance/pipeline_guard.py                │
    │  Valida que outputs usam ROUTING paths do core/paths.py          │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

## 16.3 — LAYER SYSTEM

```
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  Layer │ Conteudo                     │ Git Status                │
    │ ───────┼──────────────────────────────┼───────────────────────    │
    │  L1    │ core/, .claude/, bin/, docs/ │ Tracked (npm package)     │
    │  L2    │ agents/cargo, knowledge/     │ Tracked (premium)         │
    │        │ external/ (populated)        │                           │
    │  L3    │ .data/, .env, agents/        │ Gitignored                │
    │        │ external/, knowledge/personal│                           │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗███████╗                                                  ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║╚════██║                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║    ██╔╝                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║   ██╔╝                                                   ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║   ██║                                                    ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝   ╚═╝                                                    ====
====                                                                                                                ====
====     FLUXO COMPLETO PONTA A PONTA — MCE 12 STEPS                                                                ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

```
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║   VIDEO → TRANSCRICAO → INBOX BUCKET → Step 0 (detect) →                    ║
    ║   Step 1 (classify 6 signals + route + organize) →                           ║
    ║   Step 2 (batch min 3 files) →                                               ║
    ║   Step 3 (chunk ~300 palavras, LLM) →                                        ║
    ║   Step 4 (entity resolution, CANONICAL-MAP merge) →                          ║
    ║   Step 5 (insight extraction + DNA tags) →                                   ║
    ║   Step 6 (MCE behavioral patterns, 2+ evidence) →                            ║
    ║   Step 7 (MCE identity: values, obsessions, paradoxes) →                     ║
    ║   Step 8 (MCE voice: 6 tone dimensions) →                                   ║
    ║   Step 9 (identity checkpoint — UNICO passo humano) →                        ║
    ║   Step 10 (consolidation: dossier + 5 DNA YAMLs + agent files) →             ║
    ║   Step 11 (finalize: memory enrichment + workspace sync + metrics) →         ║
    ║   Step 12 (report: 10-point validation + completion log)                     ║
    ║                                                                              ║
    ║   ROTEAMENTO DE CONSULTA:                                                    ║
    ║   Pergunta simples (1 dominio)  → 1 CARGO agent responde                    ║
    ║   Pergunta complexa (2+ dominios) → debate CARGO + COUNCIL                  ║
    ║   /consult {pessoa}             → EXTERNAL agent solo (DNA 100%)             ║
    ║   /conclave                     → Critico + Advogado + Sintetizador          ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
```

---

```
========================================================================================================================
========================================================================================================================
====                                                                                                                ====
====     ███████╗███████╗ ██████╗ █████╗  ██████╗      ██╗ █████╗                                                   ====
====     ██╔════╝██╔════╝██╔════╝██╔══██╗██╔═══██╗    ███║██╔══██╗                                                  ====
====     ███████╗█████╗  ██║     ███████║██║   ██║    ╚██║╚█████╔╝                                                  ====
====     ╚════██║██╔══╝  ██║     ██╔══██║██║   ██║     ██║██╔══██╗                                                  ====
====     ███████║███████╗╚██████╗██║  ██║╚██████╔╝     ██║╚█████╔╝                                                  ====
====     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝     ╚═╝ ╚════╝                                                   ====
====                                                                                                                ====
====     MAPA COMPLETO DE TEMPLATES — 22 TEMPLATES ATUAIS                                                           ====
====                                                                                                                ====
========================================================================================================================
========================================================================================================================
```

```
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║   TEMPLATES DE PIPELINE (14):                                                ║
    ║   core/templates/phases/                                                     ║
    ║   ├── prompt-1.1-chunking.md              Chunking semantico                ║
    ║   ├── prompt-1.2-entity-resolution.md     Resolucao de entidades            ║
    ║   ├── prompt-2.1-insight-extraction.md    Extracao de insights              ║
    ║   ├── prompt-2.1-dna-tags.md              Tagging DNA                       ║
    ║   ├── prompt-3.1-narrative.md             Sintese narrativa                 ║
    ║   ├── prompt-mce-behavioral.md            Padroes comportamentais           ║
    ║   ├── prompt-mce-identity.md              Identidade (valores, obsessoes)   ║
    ║   ├── prompt-mce-voice.md                 Perfil de voz (6 dimensoes)       ║
    ║   ├── prompt-visual-extraction.md         Extracao visual                   ║
    ║   ├── dossier-compilation.md              Compilacao de dossier             ║
    ║   ├── sources-compilation.md              Compilacao de fontes              ║
    ║   ├── narrative-metabolism.md              Metabolismo narrativo             ║
    ║   ├── narrative-synthesis.md              Sintese narrativa                 ║
    ║   └── phase4-checkpoint.md                Checkpoint da fase 4              ║
    ║                                                                              ║
    ║   TEMPLATES DE LOGS (7):                                                     ║
    ║   core/templates/logs/                                                       ║
    ║   ├── MCE-PIPELINE-LOG-TEMPLATE.md        Log MCE (423 linhas)              ║
    ║   ├── WORKSPACE-LOG-TEMPLATE.md           Log de workspace                  ║
    ║   ├── PERSONAL-LOG-TEMPLATE.md            Log pessoal                       ║
    ║   ├── LOG-TEMPLATES.md                    Indice de templates               ║
    ║   ├── log-structure.md                    Estrutura de log                  ║
    ║   ├── batch-visual-template.md            Template visual de batch          ║
    ║   └── visual-diff.md                      Template de diff visual           ║
    ║                                                                              ║
    ║   TEMPLATES DE AGENTES (6):                                                  ║
    ║   core/templates/agents/                                                     ║
    ║   ├── dna-config-template.yaml            Template de DNA-CONFIG             ║
    ║   ├── enrichment-protocol.md              Protocolo de enriquecimento       ║
    ║   ├── memory-template.md                  Template de MEMORY.md             ║
    ║   ├── reasoning-model.md                  Modelo de raciocinio              ║
    ║   ├── soul-template.md                    Template de SOUL.md               ║
    ║   └── template-evolution.md               Evolucao de template              ║
    ║   + agents/_templates/TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md (master)        ║
    ║                                                                              ║
    ║   TEMPLATES DE DEBATE (6):                                                   ║
    ║   core/templates/debates/                                                    ║
    ║   ├── CONCLAVE-LOG-TEMPLATE-v2.md         Log do conclave                   ║
    ║   ├── conclave-log-template.md            Log v1 (legacy)                   ║
    ║   ├── conclave-protocol.md                Protocolo do conclave             ║
    ║   ├── debate-dynamics-config.yaml         Config de dinamica                ║
    ║   ├── debate-dynamics.md                  Dinamica de debate                ║
    ║   └── debate-protocol.md                  Protocolo de debate               ║
    ║                                                                              ║
    ║   TEMPLATES DE WORKSPACE (1):                                                ║
    ║   core/templates/workspace/                                                  ║
    ║   └── WORKSPACE-SCAFFOLD.yaml             Scaffold de workspace             ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
```

---

```
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║   MAPA RESUMO — TODAS AS PASTAS                                              ║
    ║                                                                              ║
    ║   PASTA              │ ANALOGIA           │ FUNCAO                           ║
    ║   ═══════════════════╪══════════════════════╪═════════════════════════════    ║
    ║   .claude/           │ Cerebelo             │ Coordenacao (JARVIS)           ║
    ║   core/              │ DNA do Sistema       │ Engine, paths, governance      ║
    ║   agents/            │ Orgaos               │ 23 agentes + 2 squads         ║
    ║   knowledge/         │ Cerebro (3 buckets)  │ DNA, Dossiers, Playbooks      ║
    ║   workspace/         │ Coracao              │ Operacao empresa (8 depts)     ║
    ║   artifacts/         │ Estomago             │ Chunks, canonical, insights    ║
    ║   logs/              │ Memoria LP           │ 13 JSONL + MCE logs            ║
    ║   reference/         │ Biblioteca           │ Protocolos, PRDs, exemplos     ║
    ║   bin/               │ Caixa Ferramentas    │ CLI, install, setup            ║
    ║   docs/              │ Arquivo (deprecated) │ Architecture, plans            ║
    ║   .data/             │ Sinapses             │ RAG indexes, graph, cache      ║
    ║   research/          │ Laboratorio (L3)     │ Analises, blueprints           ║
    ║   processing/        │ Bancada              │ Staging, entity registry       ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
```

---

```
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║   PRINCIPIOS DE DESIGN (8):                                                  ║
    ║                                                                              ║
    ║   1. 100% RASTREABILIDADE    — Cada fato → chunk → source → arquivo         ║
    ║   2. INCREMENTAL             — Merge/append, nunca replace                  ║
    ║   3. BUCKET ISOLATION        — 3 buckets + workspace, nunca misturar        ║
    ║   4. ENFORCEMENT FIRST       — 26 regras + 34 hooks bloqueiam atalhos       ║
    ║   5. EMPIRISMO OBRIGATORIO   — Evidencia + confianca obrigatorios           ║
    ║   6. EXTRACAO EXAUSTIVA      — DNA puxa de TODAS as fontes                  ║
    ║   7. GOVERNANCA CONSTITUCIONAL — L0 block, L1 warn, L6 keyword             ║
    ║   8. DUAL-LOCATION LOGGING   — Se nao foi logado, nao foi processado       ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
```

---

```
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║                          FIM DO RAIO-X COMPLETO v2.0                         ║
    ║                                                                              ║
    ║   "De fato, senhor. O sistema esta documentado.                              ║
    ║    23 agentes. 26 regras. 34 hooks. 131 routing keys.                        ║
    ║    502 testes. Zero invencao."                                                ║
    ║                                                                              ║
    ║                                              — J.A.R.V.I.S.                  ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
```
