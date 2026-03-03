# PRD: JARVIS MEGA BRAIN v3.0
## Sistema de Inteligência Autônomo Completo

---

## Executive Summary

Sistema JARVIS/MEGA BRAIN completo com arquitetura Python, composto por:
- **Knowledge Engine** vetorial (ChromaDB + SQLite FTS)
- **Sistema de Agentes** multi-perspectiva (Position + Person + Council)
- **Debate Engine** estruturado multi-rodadas
- **Query Engine** com 30 perguntas críticas e gap analysis
- **Pipeline de Ingestão** com classificação automática
- **JARVIS Server** (FastAPI) com CLI
- **Infraestrutura** de deployment (Docker + Nginx + Prometheus)

**Baseado em:** JARVIS-MEGA-BRAIN-FULL-IMPLEMENTATION.md (10 partes consolidadas)

**Status PRD v2.0:** PAUSADO (80% pendente - Fases 3-8)

---

## Norte-Estrela

> **"Sistema de inteligência autônomo que faz 30 perguntas críticas antes de responder, debate perspectivas de múltiplos especialistas, e opera 24/7 com contexto completo da [SUA EMPRESA]."**

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEGA BRAIN SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   USER → API → JARVIS ORCHESTRATOR                                          │
│                      │                                                      │
│          ┌───────────┼───────────┐                                          │
│          ▼           ▼           ▼                                          │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐                                    │
│   │  QUERY   │ │  AGENTS  │ │  DEBATE  │                                    │
│   │  ENGINE  │ │  SYSTEM  │ │  ENGINE  │                                    │
│   │          │ │          │ │          │                                    │
│   │ 30 Pergs │ │ CRO/CMO  │ │ Council  │                                    │
│   │ Gap Anal │ │ Hormozi  │ │ Synth    │                                    │
│   │ Caveats  │ │ Cole     │ │ Templates│                                    │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘                                    │
│        │            │            │                                          │
│        └────────────┼────────────┘                                          │
│                     ▼                                                       │
│             ┌──────────────┐                                                │
│             │  KNOWLEDGE   │                                                │
│             │    ENGINE    │                                                │
│             │              │                                                │
│             │ ChromaDB     │                                                │
│             │ SQLite+FTS   │                                                │
│             └──────┬───────┘                                                │
│                    │                                                        │
│        ┌───────────┼───────────┐                                            │
│        ▼           ▼           ▼                                            │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                                       │
│   │ [SUA EMPRESA]  │ │   DNA   │ │PIPELINE │                                       │
│   │  BANK   │ │ LIBRARY │ │ JARVIS  │                                       │
│   │         │ │         │ │         │                                       │
│   │ Empresa │ │ Hormozi │ │ Intake  │                                       │
│   │ Calls   │ │ Cole    │ │ Process │                                       │
│   └─────────┘ └─────────┘ └─────────┘                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Diferença do PRD v2.0

| Aspecto | PRD v2.0 | PRD v3.0 |
|---------|----------|----------|
| Foco | Skills e automações N8N | Arquitetura Python completa |
| Agentes | Skills ativados por comando | Agentes Python com orchestrator |
| Knowledge | Arquivos Markdown | ChromaDB + SQLite FTS |
| Query | Simples | 30 perguntas críticas + gap analysis |
| Debate | Council básico | Debate Engine multi-rodadas |
| Deploy | Local | Docker + Nginx + Prometheus |

---

## Estrutura de Diretórios Final

```
MEGA-BRAIN/
├── src/
│   ├── __init__.py
│   ├── config.py                    # Configurações centralizadas
│   ├── main.py                      # Entry point
│   │
│   ├── core/                        # Componentes fundamentais
│   │   ├── __init__.py
│   │   ├── types.py                 # Tipos e enums
│   │   ├── brain.py                 # Cliente Claude
│   │   └── base_agent.py            # Classe base agentes
│   │
│   ├── knowledge/                   # Knowledge Engine
│   │   ├── __init__.py
│   │   ├── chunker.py               # Chunking semântico
│   │   ├── embedder.py              # Embeddings Voyage/OpenAI
│   │   ├── vector_store.py          # ChromaDB wrapper
│   │   ├── structured_store.py      # SQLite + FTS
│   │   └── engine.py                # Knowledge Engine principal
│   │
│   ├── pipeline/                    # Pipeline de Ingestão
│   │   ├── __init__.py
│   │   ├── intake.py                # Intake Manager
│   │   ├── classifier.py            # Classificador de conteúdo
│   │   └── pipeline.py              # Pipeline unificado
│   │
│   ├── agents/                      # Sistema de Agentes
│   │   ├── __init__.py
│   │   ├── position_agents.py       # CRO, CMO, COO, CFO
│   │   ├── person_agents.py         # Digital Twins (Hormozi, etc)
│   │   ├── council.py               # Council System
│   │   └── orchestrator.py          # Orquestrador principal
│   │
│   ├── debate/                      # Sistema de Debates
│   │   ├── __init__.py
│   │   └── engine.py                # Debate Engine
│   │
│   ├── query/                       # Query Inteligente
│   │   ├── __init__.py
│   │   └── engine.py                # Query Engine (30 perguntas)
│   │
│   ├── server/                      # JARVIS Server
│   │   ├── __init__.py
│   │   └── app.py                   # FastAPI App
│   │
│   └── utils/                       # Utilitários
│       └── __init__.py
│
├── data/                            # Dados (gitignore)
│   ├── [sua-empresa]-bank/
│   ├── dna-library/
│   ├── knowledge-engine/
│   │   ├── chroma/
│   │   └── structured.db
│   └── inbox/
│
├── cli/
│   └── jarvis                       # CLI principal
│
├── scripts/
│   ├── backup.sh
│   ├── deploy.sh
│   ├── health_check.sh
│   └── setup.sh
│
├── monitoring/
│   ├── prometheus.yml
│   └── alerts.yml
│
├── nginx/
│   └── nginx.conf
│
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── Dockerfile.prod
├── docker-compose.yml
├── docker-compose.prod.yml
├── CLAUDE.md
└── RUNBOOK.md
```

---

# FASES DE IMPLEMENTAÇÃO

---

## FASE 1: CORE INFRASTRUCTURE
**Prioridade:** CRÍTICA
**Dependências:** Nenhuma

### US-V3-001: Criar Estrutura de Diretórios e Setup

**Descrição:** Criar toda a estrutura de diretórios do projeto e scripts de setup.

**Acceptance Criteria:**
- [ ] Criar estrutura `src/` com subpastas: core, knowledge, pipeline, agents, debate, query, server, utils
- [ ] Criar todos os arquivos `__init__.py`
- [ ] Criar `cli/jarvis` (executável Python)
- [ ] Criar `scripts/setup.sh` com:
  - Verificação de Python 3.11+
  - Criação de venv
  - Instalação de requirements
  - Criação de diretórios data/
  - Cópia de .env.example para .env
- [ ] Criar `scripts/backup.sh` (backup + rotação 7 dias)
- [ ] Criar `scripts/deploy.sh` (build + deploy + health check)
- [ ] Criar `scripts/health_check.sh`
- [ ] Criar `requirements.txt` com todas as dependências
- [ ] Criar `.env.example` com todas as variáveis
- [ ] Criar `.gitignore` completo

**Arquivos a criar:**
```
- src/__init__.py
- src/core/__init__.py
- src/knowledge/__init__.py
- src/pipeline/__init__.py
- src/agents/__init__.py
- src/debate/__init__.py
- src/query/__init__.py
- src/server/__init__.py
- src/utils/__init__.py
- cli/jarvis
- scripts/setup.sh
- scripts/backup.sh
- scripts/deploy.sh
- scripts/health_check.sh
- requirements.txt
- .env.example
- .gitignore
```

---

### US-V3-002: Implementar Core Types

**Descrição:** Criar todos os tipos, enums e dataclasses base do sistema.

**Acceptance Criteria:**
- [ ] Criar `src/core/types.py` com:

**Enums:**
```python
AgentType = POSITION | PERSON | COUNCIL | SYSTEM
VoteType = APPROVE | REJECT | MODIFY | ABSTAIN | DEFER
ConsensusType = UNANIMOUS | MAJORITY | COMPROMISE | SYNTHESIS | NO_CONSENSUS
QuestionCategory = CONTEXT | DATA | STRATEGIC | RISK | TIMELINE | RESOURCE | STAKEHOLDER | SUCCESS | EXECUTION
QuestionPriority = CRITICAL | HIGH | MEDIUM | LOW
ConfidenceLevel = HIGH | MEDIUM | LOW | VERY_LOW
DataSource = [SUA EMPRESA]_BANK | DNA_LIBRARY | USER_PROVIDED | INFERRED | UNKNOWN
FileStatus = PENDING | PROCESSING | COMPLETED | FAILED | SKIPPED
FileType = MARKDOWN | TEXT | PDF | DOCX | JSON | AUDIO | VIDEO | UNKNOWN
ContentDestination = [SUA EMPRESA]_BANK | DNA_LIBRARY | UNKNOWN
[Sua Empresa]Category = CALL | FINANCIAL | TEAM | DECISION | PRODUCT | PROCESS | CLIENT | GENERAL
PipelineStage = INTAKE | CLASSIFICATION | CHUNKING | ENTITY_RESOLUTION | INSIGHT_EXTRACTION | INDEXING | COMPLETED | FAILED
DebateType = QUICK | COUNCIL | FULL | ADVERSARIAL
CouncilRole = CRITIC | DEVIL_ADVOCATE | RISK_ASSESSOR | FACT_CHECKER | SYNTHESIZER
```

**Dataclasses:**
```python
@dataclass CriticalQuestion: id, question, category, priority, why_important, possible_sources, answer?, source?, confidence?
@dataclass GapAnalysis: total_questions, answered, unanswered, critical_gaps, coverage_score, confidence_level, can_proceed
@dataclass AgentConfig: name, type, description, system_prompt, temperature, activation_keywords, knowledge_sources?
@dataclass AgentResponse: agent_id, agent_name, content, confidence, metadata
@dataclass FileRecord: id, path, filename, file_type, size_bytes, hash_md5, status, detected_source, metadata, timestamps
@dataclass ChunkConfig: max_chunk_size, min_chunk_size, overlap, respect_sentences, respect_paragraphs
@dataclass PipelineJob: id, file_id, filename, stage, classification, chunks, entities, insights, errors, timestamps
@dataclass DebatePosition: participant, position, arguments, vote, confidence, conditions
@dataclass DebateSynthesis: summary, consensus_type, agreements, disagreements, recommendation, action_items
@dataclass CouncilEvaluation: role, assessment, issues_found, recommendations, vote, confidence
```

---

### US-V3-003: Implementar Config Settings

**Descrição:** Criar sistema de configuração centralizado com Pydantic.

**Acceptance Criteria:**
- [ ] Criar `src/config.py` com class Settings(BaseSettings):
  - API Keys: anthropic_api_key, voyage_api_key, openai_api_key
  - Paths: base_path, knowledge_path, [sua-empresa]_bank_path, dna_library_path, inbox_path, chroma_path, sqlite_path
  - Server: host, port, debug
  - Redis: redis_url
  - Models: claude_model, embedding_model, max_tokens
  - Night Mode: night_start_hour, night_end_hour
  - Knowledge Engine: chunk_size, chunk_overlap, max_search_results
  - Query Engine: max_questions, min_coverage_to_respond
- [ ] Método `ensure_directories()` para criar pastas necessárias
- [ ] Carregar de .env automaticamente
- [ ] Instância global `settings = Settings()`

---

### US-V3-004: Implementar Brain Client (Claude)

**Descrição:** Cliente para comunicação com Claude API.

**Acceptance Criteria:**
- [ ] Criar `src/core/brain.py` com class ClaudeBrain:
  - Inicialização com anthropic client
  - Método `async think(prompt, temperature=0.7, max_tokens=4096) -> str`
  - Método `async think_json(prompt, temperature=0.5) -> Dict` com parse JSON
  - Método `async extract_entities(text) -> List[Dict]`
  - Retry logic com tenacity (3 tentativas, exponential backoff)
  - Logging de requests/responses
  - Tratamento de rate limits

---

### US-V3-005: Implementar Base Agent

**Descrição:** Classe base para todos os agentes.

**Acceptance Criteria:**
- [ ] Criar `src/core/base_agent.py` com class BaseAgent:
  - `__init__(config: AgentConfig, brain_client, knowledge_engine)`
  - `async think(task: str, context: Dict) -> AgentResponse` (abstract)
  - `should_activate(query: str) -> bool` (verifica activation_keywords)
  - `async gather_context(query: str) -> str` (busca no knowledge)
  - `async call_brain(prompt: str) -> str` (wrapper do brain)
  - `get_system_prompt() -> str`
  - Propriedades: id, name, type, description

---

## FASE 2: KNOWLEDGE ENGINE
**Prioridade:** CRÍTICA
**Dependências:** Fase 1

### US-V3-006: Implementar Semantic Chunker

**Descrição:** Sistema de chunking semântico inteligente.

**Acceptance Criteria:**
- [ ] Criar `src/knowledge/chunker.py` com class SemanticChunker:
  - ChunkConfig com: max_chunk_size=1000, min_chunk_size=100, overlap=100
  - Detectar headers markdown (# ## ### etc)
  - Detectar headers texto (CAPS, numbered sections)
  - `_split_by_headers(text) -> List[Dict]`
  - `_chunk_section(text, header) -> List[str]`
  - `_chunk_by_sentences(text) -> List[str]`
  - `_add_overlap(chunks) -> List[Dict]`
  - `chunk(text, metadata) -> List[Dict]` retorna chunks com content e metadata
  - Respeitar parágrafos quando possível
  - Respeitar sentenças (não cortar no meio)

---

### US-V3-007: Implementar Text Embedder

**Descrição:** Gerador de embeddings com Voyage AI e fallback OpenAI.

**Acceptance Criteria:**
- [ ] Criar `src/knowledge/embedder.py` com class TextEmbedder:
  - Inicialização com voyage_api_key e openai_api_key
  - Lazy loading de clients (_voyage_client, _openai_client)
  - `async embed(text: str) -> List[float]`
  - `async embed_batch(texts: List[str]) -> List[List[float]]`
  - Voyage AI como preferencial (model: voyage-large-2)
  - Fallback para OpenAI (model: text-embedding-3-small)
  - `get_dimensions() -> int` retorna dimensão do modelo
  - Tratamento de erros com fallback

---

### US-V3-008: Implementar Vector Store (ChromaDB)

**Descrição:** Wrapper para ChromaDB com persistência.

**Acceptance Criteria:**
- [ ] Criar `src/knowledge/vector_store.py` com class VectorStore:
  - Inicialização com persist_path
  - Lazy loading do client ChromaDB
  - Collections: [sua-empresa]_bank, dna_library
  - `get_or_create_collection(name, metadata) -> Collection`
  - `async add(collection_name, ids, embeddings, documents, metadatas)`
  - `async query(collection_name, query_embedding, n_results, where, include) -> Dict`
  - `async delete(collection_name, ids?, where?)`
  - `get_stats(collection_name?) -> Dict`

---

### US-V3-009: Implementar Structured Store (SQLite FTS)

**Descrição:** Store estruturado com SQLite e Full-Text Search.

**Acceptance Criteria:**
- [ ] Criar `src/knowledge/structured_store.py` com class StructuredStore:
  - Inicialização com db_path
  - `_init_db()` cria tabelas:
    - documents (id, content, source, category, metadata, timestamps)
    - documents_fts (FTS5 virtual table)
    - entities (id, canonical_name, entity_type, aliases, metadata)
    - insights (id, tag, content, source_document, confidence, metadata)
  - Triggers para sincronizar FTS automaticamente
  - `async insert_document(doc_id, content, source, category, metadata)`
  - `async search_fts(query, source?, category?, limit) -> List[Dict]`
  - `async insert_entity(entity_id, canonical_name, entity_type, aliases, metadata)`
  - `async insert_insight(insight_id, tag, content, source_document, confidence, metadata)`
  - `async get_insights_by_tag(tag, limit) -> List[Dict]`
  - `get_stats() -> Dict`

---

### US-V3-010: Implementar Knowledge Engine Principal

**Descrição:** Motor de conhecimento unificado combinando vector + FTS.

**Acceptance Criteria:**
- [ ] Criar `src/knowledge/engine.py` com class KnowledgeEngine:
  - Inicialização com chroma_path, sqlite_path, api_keys, brain
  - Instanciar: VectorStore, StructuredStore, TextEmbedder, SemanticChunker
  - Collections: COLLECTIONS = {"[sua-empresa]": "[sua-empresa]_bank", "dna": "dna_library"}
  - `async index_document(document_id, content, metadata, source)`:
    1. Chunkar documento
    2. Gerar embeddings batch
    3. Indexar no vector store
    4. Indexar no structured store
  - `async search(query, source?, n_results, use_hybrid) -> List[Dict]`:
    1. Busca vetorial em collections relevantes
    2. Busca FTS (se hybrid)
    3. Combinar, dedupe por hash, ordenar por score
  - `async get_context_for_query(query, max_tokens, source) -> str`
  - `get_stats() -> Dict`
  - Deduplicação por hash MD5

---

## FASE 3: PIPELINE DE INGESTÃO
**Prioridade:** ALTA
**Dependências:** Fase 2

### US-V3-011: Implementar Intake Manager

**Descrição:** Gerenciador de entrada de arquivos.

**Acceptance Criteria:**
- [ ] Criar `src/pipeline/intake.py` com class IntakeManager:
  - FileRecord dataclass completa
  - SUPPORTED_EXTENSIONS por FileType
  - Inicialização com inbox_path, processed_path, registry_path
  - `_load_registry()` / `_save_registry()` (JSON persistente)
  - `_calculate_hash(file_path) -> str` (MD5)
  - `_detect_file_type(file_path) -> FileType`
  - `_generate_id(file_path) -> str`
  - `scan_inbox() -> List[FileRecord]`:
    - Escanear recursivamente
    - Calcular hash para detectar duplicatas
    - Registrar novos arquivos
  - `get_pending_files() -> List[FileRecord]`
  - `update_status(file_id, status, error_message?, metadata?)`
  - `set_detected_source(file_id, source)`
  - `move_to_processed(file_id) -> bool`
  - `get_stats() -> Dict`

---

### US-V3-012: Implementar Content Classifier

**Descrição:** Classificador de conteúdo ([Sua Empresa] Bank vs DNA Library).

**Acceptance Criteria:**
- [ ] Criar `src/pipeline/classifier.py` com class ContentClassifier:
  - [SUA EMPRESA]_KEYWORDS por [Sua Empresa]Category (call, financial, team, decision, product, process, client)
  - [SUA EMPRESA]_PATTERNS (regex: nossa empresa, [sua-empresa], call transcription, etc)
  - DNA_PATTERNS (regex: [FILOSOFIA], [FRAMEWORK], segundo hormozi, etc)
  - `_count_keyword_matches(text, keywords_dict) -> Dict[str, int]`
  - `_check_patterns(text, patterns) -> int`
  - `classify(content, filename?, metadata?) -> Dict`:
    - destination: [sua-empresa] ou dna
    - confidence: 0.0-1.0
    - category: categoria específica
    - scores: [sua-empresa]_score, dna_score
    - matches: detalhes
  - `async classify_with_ai(content, filename?) -> Dict` (usar brain para casos ambíguos)

---

### US-V3-013: Implementar Pipeline Unificado

**Descrição:** Orquestrador do pipeline de processamento.

**Acceptance Criteria:**
- [ ] Criar `src/pipeline/pipeline.py` com class JarvisPipeline:
  - PipelineJob dataclass completa
  - Inicialização com intake_manager, classifier, knowledge_engine, brain_client
  - `async process_file(file_record: FileRecord) -> PipelineJob`:
    1. INTAKE: Ler conteúdo (_read_file)
    2. CLASSIFICATION: Classificar ([sua-empresa]/dna)
    3. CHUNKING: Quebrar em chunks (_chunk_content)
    4. ENTITY_RESOLUTION: Extrair entidades (_resolve_entities)
    5. INSIGHT_EXTRACTION: Extrair insights com tags DNA (_extract_insights)
    6. INDEXING: Indexar no Knowledge Engine (_index_content)
    7. COMPLETED: Atualizar status
  - `_read_file(file_record) -> str` (suportar md, txt, json, pdf, docx)
  - `_chunk_content(content, classification) -> List[Dict]`
  - `_resolve_entities(chunks) -> List[Dict]`
  - `_extract_insights(chunks, classification) -> List[Dict]` com tags [FILOSOFIA], [FRAMEWORK], etc
  - `_index_content(chunks, entities, insights, classification, file_record)`
  - `async process_all_pending() -> List[PipelineJob]`
  - `get_job(job_id) -> PipelineJob`
  - `get_stats() -> Dict`

---

## FASE 4: SISTEMA DE AGENTES
**Prioridade:** ALTA
**Dependências:** Fases 1-3

### US-V3-014: Implementar Position Agents

**Descrição:** Agentes de cargo (C-Level).

**Acceptance Criteria:**
- [ ] Criar `src/agents/position_agents.py` com:

**POSITION_CONFIGS dict com AgentConfig para:**

**CRO (Chief Revenue Officer):**
- Responsabilidades: Receita, pipeline, conversão, time de vendas, comissões
- KPIs: MRR/ARR, pipeline value, win rate, sales cycle, CAC, LTV/CAC
- activation_keywords: vendas, sales, receita, revenue, pipeline, conversão, closer, comissão, quota, meta

**CMO (Chief Marketing Officer):**
- Responsabilidades: Leads, brand, posicionamento, canais, conteúdo, funis
- KPIs: CPL, MQLs/SQLs, conversão funil, brand metrics, engagement, ROI campanhas
- activation_keywords: marketing, leads, campanha, funil, conteúdo, marca, brand, tráfego, cpl, aquisição

**COO (Chief Operating Officer):**
- Responsabilidades: Processos, eficiência, delivery, infraestrutura, automações
- KPIs: Produtividade, tempo entrega, taxa erro, NPS, custo/operação, automação rate
- activation_keywords: operação, processo, eficiência, automação, delivery, sop, qualidade, gargalo, escala

**CFO (Chief Financial Officer):**
- Responsabilidades: Saúde financeira, cash flow, investimentos, custos, compliance
- KPIs: EBITDA, burn rate, runway, gross margin, operating margin, unit economics
- activation_keywords: financeiro, caixa, margem, investimento, custo, orçamento, roi, payback, runway

**class PositionAgent(BaseAgent):**
- `async think(task, context) -> AgentResponse`
- System prompt específico por cargo
- Busca contexto no knowledge engine

**Factory function:**
- `create_position_agent(role, brain_client, knowledge_engine) -> PositionAgent`

---

### US-V3-015: Implementar Person Agents (Digital Twins)

**Descrição:** Agentes de pessoa/mentor que replicam o pensamento.

**Acceptance Criteria:**
- [ ] Criar `src/agents/person_agents.py` com:

**PERSON_CONFIGS dict com AgentConfig para:**

**HORMOZI (Alex Hormozi):**
- Expertise: Ofertas, escala, value equation, acquisition
- Filosofia: "Make offers so good people feel stupid saying no", Volume negates luck, Skills pay bills
- Frameworks: Value Equation, Grand Slam Offer, Lead Magnet Creation
- Heurísticas: 10x Test, Name Test, FOMO Check
- Tom: Direto, confiante, data-driven, usa números específicos
- activation_keywords: hormozi, oferta, offer, value equation, grand slam, escala, scale, acquisition

**COLE_GORDON:**
- Expertise: Vendas high-ticket, estrutura de times, objection handling
- Filosofia: "Sales is a process, not a personality", Commission creates alignment
- Frameworks: CLOSER Framework, Commission Structure Design, Objection Handling Matrix
- Heurísticas: 80/20 Discovery, Pain Stack, Objection = Question
- Tom: Calmo, consultivo, curioso, nunca parece vendendo
- activation_keywords: cole gordon, closer, vendas, sales, comissão, script, objeção, discovery

- Expertise: Gestão, OKRs, métricas, cultura
- Filosofia: Gestão por indicadores, Norte Verdadeiro, Cultura de alta performance
- Frameworks: OKRs, Norte Verdadeiro, Gestão 4.0
- Tom: Analítico, orientado a indicadores, pragmático
- activation_keywords: g4, okr, gestão, métrica, kpi, norte verdadeiro, indicador, performance

**BRUNSON (Russell Brunson):**
- Expertise: Funis, copy, lançamentos, value ladder
- Filosofia: Funis são a nova forma de fazer negócios, Hook Story Offer
- Frameworks: Hook Story Offer, Value Ladder, Perfect Webinar
- Tom: Entusiasmado, storytelling, exemplos pessoais
- activation_keywords: brunson, funil, funnel, copy, landing, webinar, lançamento, value ladder, clickfunnels

**PEDRO_VALERIO:**
- Expertise: Automação, processos, ClickUp, operações
- Filosofia: Task First, Automação libera tempo, Processo bom roda sem você
- Frameworks: Task First, Automation Flow, Process Documentation
- Tom: Prático, objetivo, focado em execução
- activation_keywords: pedro, valério, clickup, automação, processo, task, tarefa, workflow, sop, operação

**class PersonAgent(BaseAgent):**
- Fala em primeira pessoa
- `async think(task, context) -> AgentResponse`
- DNA completo no system prompt

**Factory function:**
- `create_person_agent(person, brain_client, knowledge_engine) -> PersonAgent`

---

### US-V3-016: Implementar Council System

**Descrição:** Sistema de meta-avaliadores (Council).

**Acceptance Criteria:**
- [ ] Criar `src/agents/council.py` com:

**CouncilRole enum:** CRITIC, DEVIL_ADVOCATE, RISK_ASSESSOR, FACT_CHECKER, SYNTHESIZER

**CouncilEvaluation dataclass:** role, assessment, issues_found, recommendations, vote, confidence

**COUNCIL_CONFIGS dict com AgentConfig para:**

**CRITIC (Methodological Critic):**
- Avalia qualidade lógica e metodológica
- Procura: saltos lógicos, premissas não fundamentadas, vieses, generalização indevida
- Abordagem: Rigoroso mas construtivo

**DEVIL_ADVOCATE:**
- Apresenta contra-argumentos fortes
- Pergunta: "E se estivermos completamente errados?", "Qual o pior cenário?"
- Abordagem: Propositalmente contrário, stress test intelectual

**RISK_ASSESSOR:**
- Mapeia e avalia riscos (probabilidade x impacto)
- Categorias: Financeiro, Operacional, Reputacional, Legal, Estratégico, Pessoas
- Abordagem: Sistemático, quantifica, sugere mitigação

**FACT_CHECKER:**
- Verifica fatos e dados
- Classifica: FATO VERIFICADO, NÃO VERIFICADO, OPINIÃO, PROJEÇÃO, INCONSISTÊNCIA
- Abordagem: Preciso, objetivo, aponta lacunas

**SYNTHESIZER:**
- Integra perspectivas divergentes
- Busca: Padrões, pontos de concordância, próximos passos acionáveis
- Abordagem: Diplomático, prioriza ação

**class CouncilAgent(BaseAgent):**
- `async evaluate(proposal, context) -> CouncilEvaluation`

**class CouncilSystem:**
- Inicialização cria todos os agentes do council
- `async evaluate(proposal, context, roles?) -> Dict`:
  1. Coletar avaliações de cada role (exceto SYNTHESIZER)
  2. Contar votos
  3. SYNTHESIZER sintetiza no final
  4. Retornar: evaluations, votes, synthesis, recommendation
- `_determine_recommendation(votes, evaluations) -> str` (APPROVE/REJECT/MODIFY/NEEDS_DISCUSSION)

---

### US-V3-017: Implementar Agent Orchestrator

**Descrição:** Orquestrador principal que coordena todos os agentes.

**Acceptance Criteria:**
- [ ] Criar `src/agents/orchestrator.py` com class AgentOrchestrator:
  - Inicialização com brain_client, knowledge_engine
  - `_init_agents()`:
    - Criar todos os Position Agents
    - Criar todos os Person Agents
    - Criar CouncilSystem
  - `async process(query, context?, require_council?, specific_agents?) -> Dict`:
    1. Selecionar agentes (auto ou específicos)
    2. Coletar respostas de cada agente
    3. Council evaluation (se necessário)
    4. Sintetizar resposta final
    5. Retornar: query, agents_used, responses, council_evaluation, final_response, processing_time
  - `async consult_expert(expert, question, context) -> AgentResponse`
  - `async _select_agents(query) -> List[str]` (baseado em keywords)
  - `_get_agent(agent_id) -> BaseAgent`
  - `async _synthesize(query, responses, council_result) -> str`
  - `get_available_agents() -> Dict` (lista todos)

---

## FASE 5: DEBATE ENGINE
**Prioridade:** MÉDIA
**Dependências:** Fase 4

### US-V3-018: Implementar Debate Engine

**Descrição:** Sistema de debates estruturados multi-perspectiva.

**Acceptance Criteria:**
- [ ] Criar `src/debate/engine.py` com class DebateEngine:

**DNA_PERSPECTIVES dict com focus, style, key_questions para cada mentor**

**DebateType enum:** QUICK, COUNCIL, FULL, ADVERSARIAL

**DebatePosition dataclass:** participant, position, arguments, vote, confidence, conditions

**DebateSynthesis dataclass:** summary, consensus_type, agreements, disagreements, recommendation, action_items

**Métodos:**
- `async quick_decision(topic, participants?) -> Dict`:
  - 1 rodada, 2-3 participantes
  - Retorna positions e recommendation

- `async full_debate(topic, participants?, num_rounds=2, include_council=True) -> Dict`:
  1. Rodadas de debate (primeira posição, depois respostas)
  2. Síntese final
  3. Council evaluation (opcional)
  4. Retorna: type, topic, participants, rounds, synthesis, council_evaluation

- `async _get_position(participant, topic) -> DebatePosition`
- `async _get_response(participant, topic, previous_positions) -> DebatePosition`
- `async _synthesize(topic, rounds) -> Dict`
- `async _council_evaluate(topic, rounds, synthesis) -> Dict`
- `_position_to_dict(pos) -> Dict`
- `_quick_recommendation(positions) -> str`

---

## FASE 6: QUERY ENGINE (30 PERGUNTAS)
**Prioridade:** ALTA
**Dependências:** Fases 2, 4

### US-V3-019: Implementar Intelligent Query Engine

**Descrição:** Engine que faz 30 perguntas críticas antes de responder.

**Acceptance Criteria:**
- [ ] Criar `src/query/engine.py` com class IntelligentQueryEngine:

**DOMAIN_QUESTIONS dict com perguntas por domínio:**

**VENDAS (10 perguntas):**
- Qual o ticket médio atual? [DATA, CRITICAL]
- Quantos closers no time? [DATA, HIGH]
- Qual a taxa de conversão atual? [DATA, CRITICAL]
- Qual o ciclo de vendas médio? [DATA, HIGH]
- Qual o CAC atual? [DATA, CRITICAL]
- Qual o LTV? [DATA, HIGH]
- Qual o ICP definido? [STRATEGIC, HIGH]
- Existe processo de vendas documentado? [EXECUTION, MEDIUM]
- Qual a estrutura de comissão? [DATA, HIGH]
- Qual a meta mensal? [DATA, CRITICAL]

**MARKETING (7 perguntas):**
- Quais canais de aquisição ativos? [CONTEXT, HIGH]
- Qual o budget de marketing? [DATA, HIGH]
- Qual o CPL por canal? [DATA, CRITICAL]
- Quantos leads qualificados por mês? [DATA, CRITICAL]
- Qual a taxa de conversão do funil? [DATA, HIGH]
- Existe estratégia de conteúdo? [STRATEGIC, MEDIUM]
- Quem são os competidores diretos? [CONTEXT, HIGH]

**OPERACOES (5 perguntas):**
- Qual a estrutura atual do time? [CONTEXT, HIGH]
- Existem processos documentados? [EXECUTION, HIGH]
- Quais ferramentas são usadas? [CONTEXT, MEDIUM]
- Qual a produtividade por pessoa? [DATA, HIGH]
- Quais são os gargalos atuais? [RISK, CRITICAL]

**FINANCEIRO (5 perguntas):**
- Qual o MRR/ARR atual? [DATA, CRITICAL]
- Qual a margem bruta? [DATA, HIGH]
- Qual o runway atual? [DATA, CRITICAL]
- Qual o burn rate mensal? [DATA, HIGH]
- Qual a meta de crescimento? [STRATEGIC, HIGH]

**GENERIC (8 perguntas):**
- Qual o problema específico a resolver? [CONTEXT, CRITICAL]
- Qual a situação atual? [CONTEXT, HIGH]
- O que já foi tentado? [CONTEXT, MEDIUM]
- Qual o resultado esperado? [SUCCESS, HIGH]
- Qual o prazo? [TIMELINE, MEDIUM]
- Quem são os stakeholders? [STAKEHOLDER, MEDIUM]
- Quais os recursos disponíveis? [RESOURCE, HIGH]
- O que pode dar errado? [RISK, HIGH]

**Métodos:**
- `async query(query, user_context?, max_questions=30, force_response=False) -> Dict`:
  1. Detectar domínio
  2. Gerar perguntas críticas
  3. Tentar responder perguntas (context + knowledge)
  4. Análise de gaps
  5. Gerar resposta (se can_proceed ou force)
  6. Retornar: query, domain, questions stats, gap_analysis, response, can_proceed, caveats

- `_detect_domain(query) -> str` (VENDAS, MARKETING, OPERACOES, FINANCEIRO, GENERIC)
- `_generate_questions(query, domain, max_questions) -> List[CriticalQuestion]`
- `async _answer_questions(questions, user_context) -> tuple[answered, unanswered]`
- `_find_in_context(question, context) -> str?`
- `_analyze_gaps(query, answered, unanswered) -> Dict`:
  - Calcular coverage ponderado por prioridade
  - Determinar confidence level
  - can_proceed = no critical_gaps AND coverage >= 50%
- `async _generate_response(query, answered, unanswered, gap_analysis) -> str`
- `_generate_caveats(gap_analysis) -> List[str]`

---

## FASE 7: JARVIS SERVER
**Prioridade:** ALTA
**Dependências:** Fases 1-6

### US-V3-020: Implementar FastAPI Server

**Descrição:** Servidor HTTP completo com todos os endpoints.

**Acceptance Criteria:**
- [ ] Criar `src/server/app.py` com:

**Request/Response Models (Pydantic):**
```python
AskRequest: question, context?, require_council?
ConsultRequest: expert, question, context?
DebateRequest: topic, participants?, num_rounds?, include_council?
QueryRequest: query, context?, max_questions?, force_response?
SearchRequest: query, source?, n_results?
```

**JarvisApp class:**
- `async initialize()`:
  - Criar diretórios
  - Inicializar Brain
  - Inicializar Knowledge Engine
  - Inicializar Orchestrator
  - Inicializar Debate Engine
  - Inicializar Query Engine
- `async shutdown()`
- `get_status() -> Dict`

**FastAPI app com lifespan:**
- CORS middleware (allow all origins)

**Core Routes:**
- `GET /` → Root info
- `GET /health` → Health check
- `GET /status` → Status completo

**API Routes:**
- `POST /api/ask` → Pergunta geral (orchestrator.process)
- `POST /api/consult` → Consultar expert específico
- `POST /api/debate` → Iniciar debate
- `POST /api/query` → Query inteligente (30 perguntas)
- `POST /api/search` → Busca no knowledge
- `GET /api/agents` → Listar agentes disponíveis

**Webhook Routes:**
- `POST /webhook/clickup`
- `POST /webhook/drive`
- `POST /webhook/generic`

---

### US-V3-021: Implementar CLI

**Descrição:** Interface de linha de comando para JARVIS.

**Acceptance Criteria:**
- [ ] Criar `cli/jarvis` (Python executável) com class JarvisCLI:

**Métodos:**
- `async _request(method, endpoint, data?, timeout?) -> Dict`
- `async ask(question, council?) -> print response`
- `async consult(expert, question) -> print response`
- `async debate(topic, participants?) -> print rounds + synthesis`
- `async query(question, force?) -> print coverage + response + caveats`
- `async status() -> print JSON`
- `async search(query, n?) -> print results`

**Comandos via argparse:**
```bash
jarvis ask "pergunta" [--council/-c]
jarvis consult EXPERT "pergunta"
jarvis debate "topic" [--participants/-p NOME1 NOME2]
jarvis query "pergunta" [--force/-f]
jarvis search "query" [-n 10]
jarvis status
```

---

### US-V3-022: Implementar Main Entry Point

**Descrição:** Entry point da aplicação.

**Acceptance Criteria:**
- [ ] Criar `src/main.py`:
  - ASCII art banner "MEGA BRAIN"
  - Print host:port
  - `uvicorn.run("src.server.app:app", ...)`

---

## FASE 8: DATA STRUCTURES
**Prioridade:** MÉDIA
**Dependências:** Fases 1-2

### US-V3-023: Estruturar [Sua Empresa] Bank Schemas

**Descrição:** Schemas JSON para dados da empresa.

**Acceptance Criteria:**
- [ ] Criar `data/[sua-empresa]-bank/` com:

**calls.json:**
```json
{
  "schema_version": "1.0",
  "calls": [{
    "id": "call_uuid",
    "type": "sales|onboarding|support|strategy|1on1",
    "date": "ISO8601",
    "duration_minutes": 45,
    "participants": [{ "name", "role", "email" }],
    "client": { "name", "company", "segment", "ticket_potential" },
    "outcome": { "status", "deal_value", "next_steps", "objections_raised", "objections_handled" },
    "transcription_file": "path",
    "insights_extracted": [],
    "tags": [],
    "metadata": { "source", "recording_url", "processed_at" }
  }]
}
```

**team.json:**
```json
{
  "schema_version": "1.0",
  "organization": { "name", "founded", "industry", "stage" },
  "departments": [{
    "name": "Sales",
    "head": "person_id",
    "structure": {
      "closers": [{
        "id", "name", "role", "hire_date",
        "metrics": { "quota_monthly", "avg_ticket", "conversion_rate", "calls_per_day" },
        "compensation": { "base_salary", "commission_structure", "commission_rates" },
        "skills": [], "certifications": [], "reports_to"
      }],
      "sdrs": [], "managers": []
    }
  }],
  "roles_hierarchy": {}
}
```

**financials.json:**
```json
{
  "schema_version": "1.0",
  "currency": "BRL",
  "periods": [{
    "period": "2025-01",
    "type": "monthly",
    "revenue": { "mrr", "arr", "new_mrr", "churned_mrr", "expansion_mrr", "net_new_mrr" },
    "sales": { "total_deals", "total_value", "avg_ticket", "pipeline_value", "conversion_rate" },
    "costs": { "cac", "ltv", "ltv_cac_ratio", "payback_months", "gross_margin", "operating_margin" },
    "headcount": { "total", "sales", "marketing", "product", "operations", "leadership" }
  }],
  "targets": {}
}
```

**decisions.json:**
```json
{
  "schema_version": "1.0",
  "decisions": [{
    "id", "date", "title", "category", "status",
    "context": { "situation", "problem", "constraints", "stakeholders" },
    "options_considered": [{ "option", "pros", "cons", "estimated_impact", "estimated_effort" }],
    "decision": { "chosen_option", "rationale", "conditions", "risks_accepted", "success_criteria", "review_date" },
    "debate_log": { "participants", "key_arguments", "dissenting_views", "consensus_type" },
    "outcome": { "status", "results", "lessons_learned", "would_decide_differently" }
  }]
}
```

**products.json:**
```json
{
  "schema_version": "1.0",
  "products": [{
    "id", "name", "type", "status",
    "pricing": { "model", "price", "currency", "billing_frequency", "tiers" },
    "value_proposition": { "headline", "dream_outcome", "perceived_likelihood", "time_to_result", "effort_required" },
    "metrics": { "total_sales", "total_revenue", "avg_ltv", "churn_rate", "nps", "completion_rate" },
    "target_audience": { "icp", "segments", "pain_points", "alternatives" }
  }]
}
```

---

### US-V3-024: Estruturar DNA Library

**Descrição:** Estrutura de pastas e templates para DNA Library.

**Acceptance Criteria:**
- [ ] Criar estrutura `data/dna-library/`:
```
dna-library/
├── HORMOZI/
│   ├── DNA.md
│   ├── sources/
│   ├── frameworks/
│   └── quotes/
├── COLE_GORDON/
│   ├── DNA.md
│   ├── sources/
│   ├── frameworks/
│   └── quotes/
├── BRUNSON/
└── PEDRO_VALERIO/
```

- [ ] Criar template DNA.md com seções:
  - IDENTIDADE: Nome, Expertise, Empresa, Filosofia Central
  - CAMADA 1: FILOSOFIA (crenças fundamentais)
  - CAMADA 2: MODELOS MENTAIS
  - CAMADA 3: HEURÍSTICAS (regras práticas)
  - CAMADA 4: FRAMEWORKS
  - CAMADA 5: METODOLOGIAS
  - PADRÕES DE LINGUAGEM: Frases, palavras, tom
  - RED FLAGS: O que evitaria
  - PERGUNTAS CARACTERÍSTICAS
  - FONTES PROCESSADAS

- [ ] Criar DNA.md completo do HORMOZI conforme documento
- [ ] Criar DNA.md completo do COLE_GORDON conforme documento

---

## FASE 9: DEPLOYMENT & MONITORING
**Prioridade:** MÉDIA
**Dependências:** Fases 1-7

### US-V3-025: Implementar Docker Setup (Dev)

**Descrição:** Configuração Docker para desenvolvimento.

**Acceptance Criteria:**
- [ ] Criar `Dockerfile`:
  - Base: python:3.11-slim
  - Instalar deps
  - Copiar src/ e cli/
  - Criar diretórios /data
  - Healthcheck
  - CMD: python -m src.main

- [ ] Criar `docker-compose.yml`:
  - Service jarvis (build local, port 8000, env vars, volumes)
  - Service redis (redis:7-alpine, port 6379)
  - Volumes: megabrain-data, redis-data
  - Network: megabrain-network

---

### US-V3-026: Implementar Docker Setup (Prod)

**Descrição:** Configuração Docker para produção.

**Acceptance Criteria:**
- [ ] Criar `Dockerfile.prod` (multi-stage):
  - Builder stage: pip wheel
  - Production stage: user non-root, gunicorn

- [ ] Criar `docker-compose.prod.yml`:
  - Service nginx (ports 80/443, rate limiting)
  - Service jarvis (gunicorn, 4 workers, resource limits)
  - Service redis (maxmemory 512mb)
  - Service prometheus (port 9090, retention 30d)
  - Service grafana (port 3000)

---

### US-V3-027: Implementar Nginx Config

**Descrição:** Configuração Nginx para reverse proxy.

**Acceptance Criteria:**
- [ ] Criar `nginx/nginx.conf`:
  - Upstream jarvis (keepalive 32)
  - Rate limiting zones: api (10r/s), webhooks (50r/s)
  - Location / (proxy para jarvis)
  - Location /api/ (rate limit + timeout 120s)
  - Location /webhook/ (rate limit 100 burst)
  - Location /health (sem rate limit)
  - Headers: X-Real-IP, X-Forwarded-For, X-Forwarded-Proto

---

### US-V3-028: Implementar Monitoring

**Descrição:** Configuração Prometheus + Alertas.

**Acceptance Criteria:**
- [ ] Criar `monitoring/prometheus.yml`:
  - scrape_interval: 15s
  - Job prometheus (localhost:9090)
  - Job jarvis (jarvis:8000/metrics)

- [ ] Criar `monitoring/alerts.yml`:
  - JarvisServerDown: up{job="jarvis"} == 0 for 1m → critical
  - HighResponseTime: p95 > 5s for 5m → warning
  - HighErrorRate: 5xx rate > 5% for 5m → warning

---

### US-V3-029: Criar Documentação Operacional

**Descrição:** Documentação para operação do sistema.

**Acceptance Criteria:**
- [ ] Criar `RUNBOOK.md`:
  - Seção 1: Inicialização (primeiro setup, com Docker)
  - Seção 2: Comandos Úteis (CLI, API)
  - Seção 3: Troubleshooting (servidor não inicia, erros API, alta latência)
  - Seção 4: Manutenção (backup, atualização, limpeza)
  - Seção 5: Contatos

- [ ] Criar `CLAUDE.md` (para Claude Code):
  - Sobre o projeto
  - Comandos rápidos
  - Estrutura de pastas
  - Lista de agentes
  - Convenções (Python 3.11+, type hints, async/await)

---

## Dependências do Sistema

```
requirements.txt:

# Web Framework
fastapi==0.109.2
uvicorn[standard]==0.27.1
gunicorn==21.2.0
pydantic==2.6.1
pydantic-settings==2.1.0
python-multipart==0.0.9

# AI / ML
anthropic==0.18.1
voyageai==0.2.1
openai==1.12.0

# Vector Database
chromadb==0.4.22

# Database
aiosqlite==0.19.0
sqlalchemy==2.0.25

# HTTP Client
httpx==0.26.0
aiohttp==3.9.3

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.1
orjson==3.9.13
tenacity==8.2.3

# Document Processing
python-docx==1.1.0
pypdf2==3.0.1
openpyxl==3.1.2

# Async
asyncio-throttle==1.0.2
aiofiles==23.2.1

# Monitoring
prometheus-client==0.19.0
structlog==24.1.0

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.1.0
```

---

## Success Metrics

| Métrica | Target |
|---------|--------|
| Tempo de resposta p95 | < 5s |
| Uptime | 99.9% |
| Perguntas críticas por query | 30 |
| Coverage mínimo para responder | 50% |
| Position Agents disponíveis | 4 (CRO, CMO, COO, CFO) |
| Council Roles disponíveis | 5 |

---

## Ordem de Implementação Sugerida

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 1: FOUNDATION (Fases 1-2)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  US-V3-001 a US-V3-010                                                      │
│  - Estrutura de diretórios e setup                                          │
│  - Core types, config, brain, base_agent                                    │
│  - Knowledge Engine completo (chunker, embedder, vector, structured, engine)│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 2: PIPELINE + AGENTES (Fases 3-4)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  US-V3-011 a US-V3-017                                                      │
│  - Pipeline de ingestão (intake, classifier, pipeline)                      │
│  - Position Agents (CRO, CMO, COO, CFO)                                     │
│  - Council System                                                           │
│  - Orchestrator                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 3: ENGINES + SERVER (Fases 5-7)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  US-V3-018 a US-V3-022                                                      │
│  - Debate Engine                                                            │
│  - Query Engine (30 perguntas críticas)                                     │
│  - FastAPI Server                                                           │
│  - CLI                                                                      │
│  - Main entry point                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 4: DATA + DEPLOY (Fases 8-9)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  US-V3-023 a US-V3-029                                                      │
│  - [Sua Empresa] Bank schemas                                                      │
│  - DNA Library estruturada                                                  │
│  - Docker setup (dev + prod)                                                │
│  - Nginx config                                                             │
│  - Monitoring (Prometheus + alerts)                                         │
│  - Documentação operacional                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Relação com PRD v2.0

**PRD v2.0 focou em:**
- ✅ Contexto [SUA EMPRESA] estruturado (skills, arquivos)
- ✅ Integração N8N/ClickUp
- ✅ Skills de agentes (talent-agent, finance-agent, council, executor)

**PRD v3.0 implementa:**
- 🆕 Arquitetura Python completa standalone
- 🆕 Knowledge Engine vetorial (ChromaDB + SQLite FTS)
- 🆕 Query Engine com 30 perguntas críticas
- 🆕 Debate Engine multi-perspectiva
- 🆕 Deploy com Docker/Prometheus/Grafana

**Recomendação:** Implementar v3.0 em paralelo ao que foi feito no v2.0. Os skills existentes (talent-agent, finance-agent, etc) continuam funcionando. A infraestrutura Python adiciona uma camada de server independente.

---

## Resumo de User Stories

| ID | Fase | Título | Prioridade |
|----|------|--------|------------|
| US-V3-001 | 1 | Estrutura de Diretórios e Setup | CRÍTICA |
| US-V3-002 | 1 | Core Types | CRÍTICA |
| US-V3-003 | 1 | Config Settings | CRÍTICA |
| US-V3-004 | 1 | Brain Client (Claude) | CRÍTICA |
| US-V3-005 | 1 | Base Agent | CRÍTICA |
| US-V3-006 | 2 | Semantic Chunker | CRÍTICA |
| US-V3-007 | 2 | Text Embedder | CRÍTICA |
| US-V3-008 | 2 | Vector Store (ChromaDB) | CRÍTICA |
| US-V3-009 | 2 | Structured Store (SQLite FTS) | CRÍTICA |
| US-V3-010 | 2 | Knowledge Engine Principal | CRÍTICA |
| US-V3-011 | 3 | Intake Manager | ALTA |
| US-V3-012 | 3 | Content Classifier | ALTA |
| US-V3-013 | 3 | Pipeline Unificado | ALTA |
| US-V3-014 | 4 | Position Agents | ALTA |
| US-V3-015 | 4 | Person Agents (Digital Twins) | ALTA |
| US-V3-016 | 4 | Council System | ALTA |
| US-V3-017 | 4 | Agent Orchestrator | ALTA |
| US-V3-018 | 5 | Debate Engine | MÉDIA |
| US-V3-019 | 6 | Query Engine (30 Perguntas) | ALTA |
| US-V3-020 | 7 | FastAPI Server | ALTA |
| US-V3-021 | 7 | CLI | ALTA |
| US-V3-022 | 7 | Main Entry Point | ALTA |
| US-V3-023 | 8 | [Sua Empresa] Bank Schemas | MÉDIA |
| US-V3-024 | 8 | DNA Library Structure | MÉDIA |
| US-V3-025 | 9 | Docker Setup (Dev) | MÉDIA |
| US-V3-026 | 9 | Docker Setup (Prod) | MÉDIA |
| US-V3-027 | 9 | Nginx Config | MÉDIA |
| US-V3-028 | 9 | Monitoring | MÉDIA |
| US-V3-029 | 9 | Documentação Operacional | MÉDIA |

**Total:** 29 User Stories em 9 Fases / 4 Sprints

---

**Documento criado por JARVIS**
**Data:** 2026-01-12
**Versão:** 3.0.0
**Fonte:** JARVIS-MEGA-BRAIN-FULL-IMPLEMENTATION.md (10 partes)
**PRD anterior:** prd-[sua-empresa]-mega-brain-v2.md (PAUSADO)
