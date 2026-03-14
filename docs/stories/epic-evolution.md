# Epic: Evolucao Mega Brain -- Integracao Skill Seekers + Novas Capacidades

> **Versao:** 1.0.0
> **Data:** 2026-03-14
> **Autor:** Beth Smith (The Horse Surgeon)
> **Baseline:** v1.4.0 (Plan 1 Hardening COMPLETE -- 181 tests, 0 duplicate modules, CI real)
> **Target:** v2.0.0
> **Source Docs:**
> - `docs/plans/comparacao-cirurgica-2026-03-14.md` (45-item surgical comparison)
> - `docs/plans/surgical-merge-plan-2026-03-14.md` (3-phase integration plan)
> **Prerequisite:** Plan 1 (epic-technical-debt.md) DONE. All P0 debts resolved.

---

## Objetivo

Transform Mega Brain from an internal knowledge management tool into a platform
with automated ingestion, persistent vector storage, and multi-platform intelligence
distribution.

Plan 1 cleaned the foundation. Plan 2 builds on it.

```
+---------------------------------------------------------------------------+
| v1.4.0 (current)              -->             v2.0.0 (target)             |
|                                                                           |
| Manual file ingestion                Automated PDF/DOCX/Video pipeline    |
| JSON chunk files (2,812)             ChromaDB persistent vector store     |
| Warn-only quality watchdog           Numeric quality scorer (0-100)       |
| Full reprocessing every run          Incremental delta processing         |
| RAG via BM25 + optional vectors      Dedicated embedding server + cache   |
| No REST API                          Agent query endpoints                |
| 3 basic MCP tools                    8+ MCP tools (graph, agents, etc.)   |
| 181 tests                            250+ tests                           |
+---------------------------------------------------------------------------+
```

---

## Sprint Map

```
+--------+---------------------+----------+----------+---------------------+
| SPRINT | FOCUS               | DURATION | EFFORT   | DEPENDENCY          |
+--------+---------------------+----------+----------+---------------------+
|   3    | Quick Wins          | 1 week   |   ~6h    | None (start now)    |
|   4    | Infrastructure      | 2-3 wks  |  ~40h    | Sprint 3 complete   |
|   5    | Capabilities        | 4-6 wks  |  ~60h    | Sprint 4.1 / 4.2    |
|   6    | Game Changers       | horizon  |  ~80h    | PRD required first  |
+--------+---------------------+----------+----------+---------------------+
|        | TOTAL               |          | ~186h    |                     |
+--------+---------------------+----------+----------+---------------------+
```

---

## Sprint 3 -- Quick Wins (1 week, ~6h)

Zero-risk additions. Every item makes the system better regardless of
whether later sprints proceed. No external dependencies.

| #   | Story                | Effort | Risk | File                              |
|-----|----------------------|--------|------|-----------------------------------|
| 3.1 | PDF Extraction       |  ~1h   | LOW  | `story-3.1-pdf-extraction.md`     |
| 3.2 | DOCX Extraction      |  ~1h   | LOW  | `story-3.2-docx-extraction.md`    |
| 3.3 | Preset Configs       |  ~2h   | LOW  | `story-3.3-preset-configs.md`     |
| 3.4 | SS Bridge            |  ~2h   | LOW  | `story-3.4-ss-bridge.md`          |

**Gate:** All 4 stories DONE before Sprint 4 starts.

---

## Sprint 4 -- Infrastructure (2-3 weeks, ~40h)

The structural upgrades that unlock Sprint 5 capabilities.

| #   | Story                     | Effort | Risk | Dependencies            |
|-----|---------------------------|--------|------|-------------------------|
| 4.1 | Vector DB (ChromaDB)      |  ~8h   | MED  | Sprint 3 complete       |
| 4.2 | Embedding Server          |  ~8h   | MED  | Story 4.1               |
| 4.3 | Incremental Updates       | ~16h   | HIGH | GSD plan required       |
| 4.4 | Quality Scorer            |  ~8h   | LOW  | None                    |

### Story 4.1: Vector DB Integration (ChromaDB)

**Objective:** Replace JSON chunk files with a persistent vector store.

Tasks:
- pip install chromadb, add to pyproject.toml optional-dependencies
- Create `core/intelligence/rag/vector_store.py` with abstract VectorStore interface
- Create ChromaStore implementation (first concrete backend)
- Update `hybrid_index.py` to use ChromaDB instead of JSON files
- Keep BM25 for lexical search (hybrid = BM25 + vector)
- Migrate existing 2,812 chunks from `.data/rag_expert/` to ChromaDB
- Write tests: test_vector_store.py (CRUD, search, persistence)

Acceptance Criteria:
- RAG queries return results from ChromaDB, not JSON files
- Query latency <= 5s for top-10 results
- JSON backup preserved in `.data/rag_expert/` during 30-day validation
- VectorStore ABC allows swapping to Qdrant/FAISS later

### Story 4.2: Embedding Server

**Objective:** Dedicated FastAPI service for batch embedding generation with cache.

Tasks:
- Create `core/intelligence/rag/embedding_server.py` (FastAPI app)
- Support VoyageAI (primary) and sentence-transformers (fallback)
- Local cache in `.data/embedding_cache/` (hash-based dedup)
- Batch processing endpoint: POST /embed with list of texts
- Update `hybrid_index.py` to call embedding server instead of VoyageAI directly
- Create docker-compose.yml (first Docker artifact) for rag-server
- Write tests: test_embedding_server.py

Acceptance Criteria:
- Embedding server responds at localhost:8100/embed
- Cache prevents re-embedding identical texts
- hybrid_index.py uses server instead of direct API calls
- Works without VOYAGE_API_KEY (uses sentence-transformers fallback)

### Story 4.3: Incremental Updates

**Objective:** Content hashing + delta processing so pipeline skips already-processed files.

Tasks:
- Create `core/intelligence/pipeline/content_hasher.py` (SHA256 per file)
- Hash registry in `.data/content_hashes.json`
- Update `batch_governor.py` to filter out already-hashed files before batch creation
- Register hashes after successful processing
- Add --force flag to bypass hash check for full reprocess
- Write tests: test_content_hasher.py, test_batch_governor_incremental.py

Acceptance Criteria:
- Re-running pipeline on same data skips already-processed files
- --force flag triggers full reprocessing
- New files (not in hash registry) are processed normally
- Hash registry survives session restarts

### Story 4.4: Quality Scorer

**Objective:** Replace warn-only quality_watchdog.py with numeric scoring (0-100).

Tasks:
- Create `core/intelligence/validation/quality_scorer.py`
- Scoring dimensions: coverage, clarity, completeness, traceability
- Persist scores in `.data/quality_scores.jsonl`
- Integrate with existing `quality_watchdog.py` (score logged alongside warn)
- Score < 50: warn (existing behavior) + log
- Score >= 70: pass silently + log
- Write tests: test_quality_scorer.py

Acceptance Criteria:
- Every processed batch receives a numeric quality score
- Scores are persisted in `.data/quality_scores.jsonl`
- Score trends visible across batches (improving/degrading)
- Existing quality_watchdog.py behavior preserved (warn, not block)

---

## Sprint 5 -- Capabilities (4-6 weeks, ~60h)

New capabilities that extend the system surface area.

| #   | Story                     | Effort | Risk | Dependencies            |
|-----|---------------------------|--------|------|-------------------------|
| 5.1 | Video Pipeline            | ~16h   | MED  | Story 4.1 (Vector DB)   |
| 5.2 | Agent API                 | ~16h   | MED  | Story 4.2 (Embed Srv)   |
| 5.3 | MCP Server Expansion      | ~12h   | LOW  | Story 4.2 (Embed Srv)   |
| 5.4 | Conclave as a Service     | ~16h   | MED  | Story 5.2 (Agent API)   |

### Story 5.1: Video Pipeline

**Objective:** OCR + local Whisper + frame extraction for YouTube courses and video materials.

Tasks:
- Create `core/intelligence/pipeline/video/` module directory
- Implement frame extraction (opencv-python, key frames by scene change)
- Implement OCR on slides (pytesseract or easyocr)
- Implement local transcription (faster-whisper, no API dependency)
- Create `/ingest-video` skill in `.claude/skills/ingest-video/SKILL.md`
- Output lands in `knowledge/external/inbox/{source}/` as .txt
- MCE pipeline processes video transcripts without modification
- Write tests: test_video_pipeline.py (mock video, verify output format)

Acceptance Criteria:
- YouTube URL produces transcript + slide text in inbox
- Local video file produces same output
- Output is compatible with existing MCE pipeline
- Works without Skill Seekers installed (native implementation)

### Story 5.2: Agent API

**Objective:** REST endpoint to query mind-clone agents programmatically.

Tasks:
- Create `core/api/agent_server.py` (FastAPI)
- GET /agents -- list all agents with metadata
- GET /agents/{name} -- agent details (AGENT.md parsed to JSON)
- POST /agents/{name}/query -- query agent with context (uses RAG + DNA)
- POST /agents/{name}/debate -- two agents debate a topic
- Authentication: API key via header (stored in .env)
- Write tests: test_agent_api.py

Acceptance Criteria:
- At least 1 REST endpoint serves agent queries
- Response includes agent identity, DNA sources, and RAG-backed answer
- API key required for all endpoints
- Swagger docs available at /docs

### Story 5.3: MCP Server Expansion

**Objective:** Add 5 new tools to the mega-brain MCP server.

Tasks:
- Add `graph_query` tool: query knowledge graph by entity/relationship
- Add `agent_lookup` tool: find agents by expertise or domain
- Add `dossier_search` tool: search person and theme dossiers
- Add `pipeline_status` tool: show current pipeline state and progress
- Add `memory_search` tool: search agent memory across all agents
- Update `core/intelligence/rag/mcp_server.py` with new tool registrations
- Update `.claude/rules/mcp-governance.md` with new tool documentation
- Write tests: test_mcp_tools.py

Acceptance Criteria:
- All 5 new tools accessible from Claude Code session
- Each tool returns structured JSON responses
- graph_query supports entity name and relationship type filters
- pipeline_status reads from MISSION-STATE.json

### Story 5.4: Conclave as a Service

**Objective:** API endpoint for multi-agent debates, accessible outside Claude Code.

Tasks:
- Create POST /conclave/debate endpoint in agent_server.py
- Request body: topic, participants (agent names), rounds (1-5)
- Response: structured debate with positions, evidence, synthesis
- Each agent loads its SOUL.md + MEMORY.md + DNA for authentic voice
- Rate limiting: max 5 debates per hour
- Write tests: test_conclave_api.py

Acceptance Criteria:
- API accepts debate request with 2-5 agents and a topic
- Each agent responds in character with DNA-backed evidence
- Final synthesis combines positions into actionable recommendation
- Debate transcript is stored in logs/conclave/

---

## Sprint 6 -- Game Changers (horizon, ~80h)

Conceptual stories. Each requires its own PRD before execution.

| #   | Story                           | Effort | Dependencies                    |
|-----|---------------------------------|--------|---------------------------------|
| 6.1 | Skill Marketplace               | ~20h   | Sprint 5 complete + PRD         |
| 6.2 | Real-Time Coaching              | ~20h   | Story 5.2 (Agent API) + PRD     |
| 6.3 | Knowledge Sync Hub              | ~20h   | Story 5.1 (Video) + PRD         |
| 6.4 | Cross-Expert Knowledge Graph UI | ~20h   | Story 5.3 (MCP Expand) + PRD    |

### Story 6.1: Skill Marketplace (concept)

Package DNA packs (expert knowledge schemas) as distributable, installable skills.
Users could install "Hormozi Sales DNA" or "Cole Gordon Closer Framework" into their
own Mega Brain instance. Requires licensing model and packaging format definition.

### Story 6.2: Real-Time Coaching (concept)

Live mind-clone suggestions during sales calls. Agent listens to call transcript
in real-time (via Fireflies/Read.ai webhooks) and suggests responses, objection
handling, or closing techniques based on the relevant expert DNA. Requires
sub-second latency and WebSocket architecture.

### Story 6.3: Knowledge Sync Hub (concept)

Auto-ingest from YouTube channels, RSS feeds, and podcast directories. Monitored
sources are polled on schedule, new content is automatically downloaded, transcribed,
and processed through the MCE pipeline. Requires source registry and scheduling.

### Story 6.4: Cross-Expert Knowledge Graph UI (concept)

Interactive web visualization of the knowledge graph (1,302 entities, 2,508 edges).
Filter by expert, domain, or concept. Click a node to see all connected insights,
the experts who contributed, and the source materials. Built with D3.js or similar.

---

## Success Criteria (v2.0.0)

```
+----+-------------------------------------------------+----------+
| #  | CRITERION                                       | SPRINT   |
+----+-------------------------------------------------+----------+
|  1 | PDF/DOCX files process automatically            | Sprint 3 |
|  2 | Pipeline presets exist for 4+ use cases          | Sprint 3 |
|  3 | SS bridge calls Skill Seekers CLI via subprocess | Sprint 3 |
|  4 | RAG queries return results from ChromaDB         | Sprint 4 |
|  5 | Pipeline processes only deltas (not full re-runs)| Sprint 4 |
|  6 | Quality scores are numeric and persisted          | Sprint 4 |
|  7 | Embedding server responds with cache              | Sprint 4 |
|  8 | At least 1 REST endpoint serves agent queries     | Sprint 5 |
|  9 | MCP server exposes 8+ tools                       | Sprint 5 |
| 10 | Test count > 250                                  | Sprint 5 |
+----+-------------------------------------------------+----------+
```

---

## Budget

```
+----------+----------+----------+
| SPRINT   | EFFORT   | COST     |
+----------+----------+----------+
| Sprint 3 |   ~6h    | R$  900  |
| Sprint 4 |  ~40h    | R$6,000  |
| Sprint 5 |  ~60h    | R$9,000  |
| Sprint 6 |  ~80h    | R$12,000 |
+----------+----------+----------+
| TOTAL    | ~186h    | R$27,900 |
+----------+----------+----------+
```

---

## Dependency Graph

```
Sprint 3 (no deps -- START NOW)
  |
  +-- Story 3.1: PDF Extraction ----+
  +-- Story 3.2: DOCX Extraction ---+-- All independent, parallel OK
  +-- Story 3.3: Preset Configs ----+
  +-- Story 3.4: SS Bridge ---------+
  |
  v
Sprint 4 (depends on Sprint 3 complete)
  |
  +-- Story 4.1: Vector DB (ChromaDB) -----+
  |     |                                   |
  |     v                                   |
  +-- Story 4.2: Embedding Server ----------+-- Story 4.4 has no deps
  |     |                                   |
  |     v                                   v
  +-- Story 4.3: Incremental Updates    Story 4.4: Quality Scorer
  |
  v
Sprint 5 (partial deps)
  |
  +-- Story 5.1: Video Pipeline -------- depends on 4.1
  +-- Story 5.2: Agent API ------------- depends on 4.2
  +-- Story 5.3: MCP Expansion --------- depends on 4.2
  +-- Story 5.4: Conclave as Service --- depends on 5.2
  |
  v
Sprint 6 (horizon -- requires PRD per story)
```

---

## Risk Matrix

```
+----+--------------------------------+---------+--------+--------------------------+
| #  | RISK                           | PROB    | IMPACT | MITIGATION               |
+----+--------------------------------+---------+--------+--------------------------+
| R1 | ChromaDB migration loses data  | LOW     | HIGH   | Keep JSON backup 30 days |
| R2 | Incremental hash breaks repro  | MEDIUM  | HIGH   | --force flag for full run |
| R3 | SS subprocess fails silently   | MEDIUM  | MEDIUM | Exit code + stderr check |
| R4 | Video pipeline pulls 2GB deps  | CERTAIN | LOW    | Separate install script  |
| R5 | Agent API exposes internal data| LOW     | HIGH   | API key auth required    |
| R6 | Embedding server adds latency  | MEDIUM  | MEDIUM | Local cache + batch ops  |
+----+--------------------------------+---------+--------+--------------------------+
```

---

## Rollback Strategy

Sprint 3: All items create NEW files only. Rollback = delete the files.

Sprint 4: Each story is independently reversible:
- 4.1: Revert hybrid_index.py to JSON backend
- 4.2: Delete embedding_server.py
- 4.3: Delete content_hasher.py, revert batch_governor.py
- 4.4: Delete quality_scorer.py

Sprint 5: Each capability is behind its own module:
- 5.1: Delete video/ directory
- 5.2: Delete api/ directory
- 5.3: Revert mcp_server.py
- 5.4: Remove conclave endpoint from agent_server.py

---

## What NOT To Do

```
+---------------------------------------------------------------------------+
| 1. DO NOT pip install skill-seekers in MB's venv                          |
|    Reason: langchain + llama-index + pytorch contaminate dependencies     |
|                                                                           |
| 2. DO NOT fork Skill Seekers                                              |
|    Reason: Maintenance burden. Use as external CLI tool via subprocess.    |
|                                                                           |
| 3. DO NOT adopt K8s manifests                                             |
|    Reason: Single-user local tool. Overengineering.                       |
|                                                                           |
| 4. DO NOT refactor CLI to match SS's click-based structure                |
|    Reason: Slash commands are the real CLI inside Claude Code.             |
|                                                                           |
| 5. DO NOT start Sprint 4 before Sprint 3 is DONE                         |
|    Reason: Foundation before infrastructure. Always.                      |
|                                                                           |
| 6. DO NOT start Sprint 6 without a PRD per story                          |
|    Reason: Concepts are not stories. They need definition first.          |
+---------------------------------------------------------------------------+
```

---

Beth -- The operation was a success. Project delivered.
