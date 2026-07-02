# MOGA BRAIN: Explicacao Completa do Sistema

> **Versao:** 1.0.0 | **Data:** 2025-12-22
> **Proposito:** Explicar cinematograficamente o sistema para qualquer pessoa

---

# PROLOGO: A Metafora do Cerebro

Imagine um cerebro humano.

Voce le um livro. O que acontece?

1. Seus olhos capturam as palavras (INPUT)
2. Seu cerebro quebra em pedacos digeríveis (CHUNKING)
3. Identifica quem disse o que, sobre o que (ENTITY RESOLUTION)
4. Extrai o que importa - "isso e importante!" (INSIGHT EXTRACTION)
5. Conecta com outras coisas que voce ja sabe (NARRATIVE SYNTHESIS)
6. Cria uma "ficha mental" da pessoa ou tema (DOSSIER)
7. Distribui para as partes especializadas do cerebro (AGENT ENRICHMENT)
8. Guarda para consulta futura (KNOWLEDGE BASE)

**O Moga Brain faz EXATAMENTE isso. So que para conhecimento de negocios B2B.**

---

# CAPITULO 1: A LOGICA CENTRAL

## 1.1 O Problema que Resolve

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   ANTES (Caos)                          DEPOIS (Moga Brain)                      │
│   ═══════════════                       ═══════════════════                      │
│                                                                                  │
│   • 50 videos assistidos                • 260 chunks organizados                 │
│   • Notas soltas em 10 lugares          • 157 insights priorizados               │
│   • "Onde foi que eu vi isso?"          • 8 dossies de pessoas                   │
│   • Conhecimento perdido                • 10 dossies de temas                    │
│   • Depende da sua memoria              • 12 agentes especializados              │
│   • Nao escala                          • Consulta instantanea                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 1.2 A Formula Central

```
CONHECIMENTO BRUTO  →  PROCESSAMENTO  →  CONHECIMENTO UTILIZAVEL  →  DECISAO
     (Video)             (Pipeline)           (Dossie)              (Agente)
```

**Traduzindo:**

1. **Voce assiste** um video de Alex Hormozi sobre vendas
2. **O sistema processa** - quebra, analisa, extrai insights
3. **O sistema organiza** - cria dossie do Hormozi, atualiza tema "Vendas"
4. **Voce consulta** - "Como estruturar time de vendas?" → Agente CRO responde com conhecimento acumulado

---

# CAPITULO 2: A JORNADA COMPLETA (Pipeline Jarvis)

## 2.0 Visao Cinematografica

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                           A JORNADA DE UM VIDEO                                  │
│                                                                                  │
│   🎬 VIDEO BRUTO                                                                 │
│      │                                                                           │
│      │ "How I Scaled My Sales Team" - Alex Hormozi                              │
│      │  2 horas de conteudo denso                                               │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 1: TRANSCRICAO                                                      │  │
│   │  ─────────────────────                                                    │  │
│   │  Audio → Texto                                                            │  │
│   │  "O sistema pega a API do YouTube ou usa AssemblyAI para                  │  │
│   │   transformar audio em texto com timestamps"                              │  │
│   │                                                                           │  │
│   │  OUTPUT: arquivo .txt com 78.000 caracteres                               │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 2: CHUNKING (Quebra Semantica)                                      │  │
│   │  ────────────────────────────────────                                     │  │
│   │  Texto grande → Pedacos digeríveis (~300 palavras cada)                   │  │
│   │                                                                           │  │
│   │  REGRAS:                                                                  │  │
│   │  • Nao cortar no meio de uma ideia                                        │  │
│   │  • Preservar contexto (quem disse, quando)                                │  │
│   │  • Cada chunk e uma "unidade de pensamento"                               │  │
│   │                                                                           │  │
│   │  OUTPUT: 30 chunks (chunk_AH001_001 ate chunk_AH001_030)                  │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 3: ENTITY RESOLUTION (Quem e Quem)                                  │  │
│   │  ───────────────────────────────────────                                  │  │
│   │  Identifica TODAS as entidades mencionadas                                │  │
│   │                                                                           │  │
│   │  EXEMPLO:                                                                 │  │
│   │  • "Hormozi" = "Alex Hormozi" = "@AlexHormozi" → CANONICAL: Alex Hormozi  │  │
│   │  • "Leila" = "minha esposa" → CANONICAL: Leila Hormozi                    │  │
│   │  • "closer" = "framework de vendas" → CANONICAL: CLOSER_FRAMEWORK         │  │
│   │                                                                           │  │
│   │  OUTPUT: CANONICAL-MAP.json atualizado                                    │  │
│   │          (+2 pessoas, +6 conceitos neste video)                           │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 4: INSIGHT EXTRACTION (O Que Importa)                               │  │
│   │  ──────────────────────────────────────────                               │  │
│   │  De cada chunk, extrai INSIGHTS acionaveis                                │  │
│   │                                                                           │  │
│   │  FORMATO DE INSIGHT:                                                      │  │
│   │  ┌─────────────────────────────────────────────────────────────────────┐ │  │
│   │  │ ID: SRC001                                                            │ │  │
│   │  │ INSIGHT: "Christmas Tree Structure: BDR→SDS→BC"                      │ │  │
│   │  │ CHUNKS: [AH001_002, AH001_003]                                       │ │  │
│   │  │ CONFIANCA: HIGH                                                      │ │  │
│   │  │ PRIORIDADE: HIGH                                                     │ │  │
│   │  │ CATEGORIA: sales_structure                                           │ │  │
│   │  └─────────────────────────────────────────────────────────────────────┘ │  │
│   │                                                                           │  │
│   │  OUTPUT: 42 insights (HIGH: 35, MEDIUM: 7)                               │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 5: NARRATIVE SYNTHESIS (Conectando os Pontos)                       │  │
│   │  ─────────────────────────────────────────────────                        │  │
│   │  Agrupa insights por PESSOA ou TEMA                                       │  │
│   │                                                                           │  │
│   │  PERGUNTA: "O que o Alex Hormozi REALMENTE pensa sobre vendas?"           │  │
│   │                                                                           │  │
│   │  O sistema conecta:                                                       │  │
│   │  • Insights deste video                                                   │  │
│   │  • Insights de OUTROS videos do Hormozi                                   │  │
│   │  • Padroes que se repetem                                                 │  │
│   │  • Contradicoes (se houver)                                               │  │
│   │                                                                           │  │
│   │  OUTPUT: NARRATIVES-STATE.json (filosofia consolidada)                    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 6: DOSSIER COMPILATION (Ficha Completa)                             │  │
│   │  ────────────────────────────────────────────                             │  │
│   │  Cria DOIS tipos de dossie:                                               │  │
│   │                                                                           │  │
│   │  A) DOSSIE DE PESSOA (MULTI-FONTE)                                        │  │
│   │     "Tudo que Alex Hormozi disse sobre TODOS os temas"                    │  │
│   │     → DOSSIER-ALEX-HORMOZI.md                                             │  │
│   │                                                                           │  │
│   │  B) DOSSIE DE TEMA (MULTI-FONTE)                                          │  │
│   │     "Tudo que TODOS disseram sobre estrutura de time"                     │  │
│   │     → DOSSIER-01-ESTRUTURA-TIME.md                                        │  │
│   │                                                                           │  │
│   │  C) SOURCE (UNI-FONTE) ← Novo em v3.18                                    │  │
│   │     "Tudo que Alex Hormozi disse sobre UM tema específico"                │  │
│   │     → SOURCES/alex-hormozi/ESTRUTURA-TIME.md                              │  │
│   │                                                                           │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 7: AGENT ENRICHMENT (Distribuindo Conhecimento)                     │  │
│   │  ───────────────────────────────────────────────────                      │  │
│   │  O sistema identifica QUAIS AGENTES se beneficiam deste conteudo          │  │
│   │                                                                           │  │
│   │  ESTE VIDEO → afeta:                                                      │  │
│   │  • AGENT-CLOSER (framework CLOSER, objecoes)                              │  │
│   │  • AGENT-SALES-MANAGER (estrutura time, Farm System)                      │  │
│   │  • AGENT-CRO (estrategia de scaling, channels)                            │  │
│   │  • AGENT-BDR (Christmas Tree, prospeccao)                                 │  │
│   │                                                                           │  │
│   │  CADA AGENTE recebe os insights relevantes na sua MEMORY                  │  │
│   │                                                                           │  │
│   │  OUTPUT: 4 MEMORYs atualizadas                                            │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│      │                                                                           │
│      ▼                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  FASE 8: FINALIZATION (Registro e Log)                                    │  │
│   │  ─────────────────────────────────────                                    │  │
│   │  • Atualiza SESSION-STATE.md                                              │  │
│   │  • Registra no file-registry.json (hash MD5)                              │  │
│   │  • Gera EXECUTION REPORT                                                  │  │
│   │  • Re-indexa RAG (busca semantica)                                        │  │
│   │                                                                           │  │
│   │  O video agora e CONHECIMENTO PERMANENTE                                  │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# CAPITULO 3: A ESTRUTURA DE PASTAS (Anatomia do Cerebro)

```
MOGA BRAIN/
│
├── inbox/                    ← ENTRADA (Olhos e Ouvidos)
│   │                              Material bruto chega aqui
│   ├── ALEX HORMOZI/
│   ├── COLE GORDON/
│   └── JORDAN LEE/
│
├── processing/               ← PROCESSAMENTO (Cortex)
│   │                              Onde a digestao acontece
│   ├── chunks/                  ← Pedacos semanticos
│   ├── canonical/               ← Mapa de entidades
│   ├── insights/                ← Insights extraidos
│   └── narratives/              ← Narrativas consolidadas
│
├── knowledge/                ← CONHECIMENTO (Memoria de Longo Prazo)
│   │                              Informacao organizada e pronta para uso
│   ├── DOSSIERS/
│   │   ├── PERSONS/             ← Fichas de pessoas
│   │   └── THEMES/              ← Fichas de temas
│   └── SOURCES/                 ← Pessoa × Tema
│
├── knowledge/playbooks/                 ← OUTPUT (Acoes)
│   │                              Playbooks e materiais finais
│   ├── drafts/
│   └── final/
│
├── system/                   ← SISTEMA NERVOSO (Controle)
│   │                              Estado, logs, evolucao
│   ├── SESSION-STATE.md         ← Estado atual
│   ├── EVOLUTION-LOG.md         ← Historico de mudancas
│   └── OPEN-LOOPS.json          ← Tarefas pendentes
│
├── agents/                   ← ESPECIALISTAS (Lobos Cerebrais)
│   │                              Conhecimento especializado
│   ├── C-LEVEL/                 ← Agentes estrategicos (CRO, CFO, CMO, COO)
│   ├── SALES/                   ← Agentes de vendas (Closer, BDR, SDS, etc)
│   ├── ORG-LIVE/                ← Cargos humanos (ROLEs, JDs, MEMORYs)
│   └── PROTOCOLS/               ← Regras do sistema
│
└── logs/                     ← REGISTROS (Memoria Episodica)
    ├── EXECUTION/               ← Logs de execucao
    ├── AUDIT/                   ← Auditoria de decisoes
    └── DIGEST/                  ← Diagnosticos
```

---

# CAPITULO 4: OS DOIS TIPOS DE AGENTES

## 4.1 A Diferenca Fundamental

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   AGENTES IA (C-LEVEL + SALES)          ORG-LIVE (ROLES + JDS + MEMORY)         │
│   ════════════════════════════          ═══════════════════════════════         │
│                                                                                  │
│   🤖 SAO CONSULTORES VIRTUAIS           👤 SAO DOCUMENTOS PARA HUMANOS          │
│                                                                                  │
│   Voce PERGUNTA para eles:              Voce USA para:                          │
│   "Como estruturo meu time?"            • Contratar pessoas                     │
│   "Qual metrica devo usar?"             • Treinar funcionarios                  │
│   "Como fecho essa venda?"              • Definir responsabilidades             │
│                                                                                  │
│   ELES RESPONDEM com base em:           ELES DESCREVEM:                         │
│   • Todo conhecimento processado        • O que a pessoa FAZ                    │
│   • Frameworks de especialistas         • Para quem reporta                     │
│   • Melhores praticas do mercado        • Quais OKRs deve bater                 │
│                                                                                  │
│   ┌───────────────────────────┐         ┌───────────────────────────┐           │
│   │ AGENT-CLOSER              │         │ ROLE-CLOSER               │           │
│   │ "Sou expert em fechamento.│         │ "O Closer e o profissional│           │
│   │  Uso 7 Beliefs, CLOSER    │         │  que faz 3 ofertas/dia,   │           │
│   │  framework, Tonality..."  │         │  reporta ao Sales Manager,│           │
│   │                           │         │  foca 100% em fechamento."│           │
│   └───────────────────────────┘         └───────────────────────────┘           │
│                                                                                  │
│   PUBLICO: Voce (founder)               PUBLICO: RH, gestores, candidatos       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 4.2 O Fluxo de Alimentacao

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                    COMO O CONHECIMENTO FLUI                                      │
│                                                                                  │
│   MATERIAL BRUTO                                                                 │
│        │                                                                         │
│        ▼                                                                         │
│   ┌─────────────────┐                                                            │
│   │ Pipeline Jarvis │ ← Processa, extrai insights                               │
│   └────────┬────────┘                                                            │
│            │                                                                     │
│            ▼                                                                     │
│   ┌─────────────────┐                                                            │
│   │   DOSSIERS      │ ← Conhecimento consolidado por pessoa/tema                │
│   └────────┬────────┘                                                            │
│            │                                                                     │
│            ├──────────────────────────────┐                                      │
│            ▼                              ▼                                      │
│   ┌─────────────────┐            ┌─────────────────┐                            │
│   │  AGENTS (IA)    │            │  ORG-LIVE       │                            │
│   │                 │            │  (Humanos)      │                            │
│   │ • Frameworks    │            │                 │                            │
│   │ • Metodologias  │ ─────────► │ • Responsabili- │                            │
│   │ • Best practices│  HERDA     │   dades         │                            │
│   │ • Metricas      │            │ • OKRs          │                            │
│   │                 │            │ • Processos     │                            │
│   └─────────────────┘            └─────────────────┘                            │
│                                                                                  │
│   AGENT-CLOSER conhece:          ROLE-CLOSER aplica:                            │
│   "7 Beliefs Framework"          "Usar 7 Beliefs no discovery"                  │
│                                  "Meta: 3 ofertas/dia"                          │
│                                  "Reportar ao Sales Manager"                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 4.3 Os 12 Agentes IA

| Categoria | Agente | Expertise |
|-----------|--------|-----------|
| **C-LEVEL** | CRO | Revenue, ofertas, pricing, metodologias de vendas |
| | CFO | Financas, margens, unit economics, esteira de produtos |
| | CMO | Marketing, posicionamento, Purple Ocean, ICP |
| | COO | Operacoes, entrega, DIY/DWY/DFY, Employee Experience |
| **SALES** | CLOSER | Fechamento, 7 Beliefs, Tonality, Objection Handling |
| | BDR | Prospeccao outbound, cold calling |
| | SDS | Qualificacao, Discovery profundo |
| | LNS | Nurture, Show Rate, Sales Farming |
| | SALES-MANAGER | Gestao de time, QC de calls, coaching |
| | SALES-LEAD | Player-coach, lideranca operacional |
| | SALES-COORDINATOR | Admin, CRM, atribuicao de leads |
| | CUSTOMER-SUCCESS | Pos-venda, NPS, LTV, Health Score |

## 4.4 Os Cargos Humanos (ORG-LIVE)

Cada cargo tem 3 documentos:

| Documento | Proposito | Exemplo |
|-----------|-----------|---------|
| **ROLE** | Definicao completa do cargo | ROLE-CLOSER.md |
| **JD** | Job Description para contratacao | JD-CLOSER.md |
| **MEMORY** | Base de conhecimento do cargo | MEMORY-CLOSER.md |

---

# CAPITULO 5: OS PADROES DE ESCOLHA

## 5.1 Como o Sistema Decide Qual Agente Atualizar

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   INSIGHT EXTRAIDO                                                               │
│   ═══════════════                                                                │
│   "Christmas Tree Structure: BDR→SDS→BC"                                         │
│                                                                                  │
│   CATEGORIAS IDENTIFICADAS                                                       │
│   ════════════════════════                                                       │
│   → sales_structure                                                              │
│   → team_scaling                                                                 │
│   → org_design                                                                   │
│                                                                                  │
│   MAPEAMENTO TEMA → AGENTE                                                       │
│   ════════════════════════                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ sales_structure  →  AGENT-SALES-MANAGER + AGENT-BDR + AGENT-SDS        │   │
│   │ team_scaling     →  AGENT-CRO + AGENT-COO                              │   │
│   │ org_design       →  AGENT-COO + AGENT-CFO                              │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   RESULTADO: 5 agentes recebem este insight                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Como o Sistema Cria Novos Agentes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   ROLE-TRACKING: Sistema de Threshold                                            │
│   ═══════════════════════════════════                                            │
│                                                                                  │
│   O sistema conta quantas vezes uma FUNCAO e mencionada no material.             │
│   Se atinge THRESHOLD (10+ mencoes), sugere criar agente.                        │
│                                                                                  │
│   EXEMPLO REAL:                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ Funcao              │ Mencoes │ Status                                  │   │
│   ├─────────────────────┼─────────┼─────────────────────────────────────────┤   │
│   │ Lead Nurture Spec.  │   12    │ ✅ CRIADO (threshold atingido)          │   │
│   │ HR Director         │    8    │ ⏳ RASTREAR (+2 para criar)             │   │
│   │ Sales Ops           │    5    │ 👀 MONITORAR                            │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   QUANDO LNS ATINGIU 10 MENCOES:                                                 │
│   → Sistema alertou: "LNS mencionado 12x. Criar agente?"                        │
│   → Agente criado: AGENT-LNS.md                                                  │
│   → Memory criada: MEMORY-LNS.md                                                 │
│   → Role criado: ROLE-LNS.md                                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 5.3 Prioridade de Insights

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   SISTEMA DE PRIORIDADE                                                          │
│   ═════════════════════                                                          │
│                                                                                  │
│   ┌────────────────────┬─────────────────────────────────────────────────────┐  │
│   │ Prioridade         │ Criterio                                            │  │
│   ├────────────────────┼─────────────────────────────────────────────────────┤  │
│   │ 🔴 HIGH            │ Framework acionavel, metrica especifica, numero    │  │
│   │                    │ concreto, processo replicavel                       │  │
│   │                    │ Ex: "Close rate 25-35% e o benchmark"               │  │
│   ├────────────────────┼─────────────────────────────────────────────────────┤  │
│   │ 🟡 MEDIUM          │ Conselho geral, principio, filosofia               │  │
│   │                    │ Ex: "Contrate por competencia, nao experiencia"     │  │
│   ├────────────────────┼─────────────────────────────────────────────────────┤  │
│   │ 🟢 LOW             │ Contexto, historia pessoal, anedota                │  │
│   │                    │ Ex: "Quando comecei em 2010..."                     │  │
│   └────────────────────┴─────────────────────────────────────────────────────┘  │
│                                                                                  │
│   INSIGHTS HIGH sao os que REALMENTE alimentam os agentes.                       │
│   MEDIUM e LOW sao guardados para contexto.                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# CAPITULO 6: AS PIPELINES EXISTENTES

## 6.1 Mapa Completo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                         TODAS AS PIPELINES DO SISTEMA                            │
│                                                                                  │
│   1. PIPELINE JARVIS (Principal)                                                 │
│      ════════════════════════════                                                │
│      Proposito: Processar material bruto → conhecimento estruturado              │
│      Fases: 8 (Chunking → Entity → Insight → Narrative → Dossier → Agent)       │
│      Trigger: /process-jarvis [arquivo] ou /jarvis-full                         │
│                                                                                  │
│   2. PIPELINE DE TRANSCRICAO                                                     │
│      ════════════════════════════                                                │
│      Proposito: Audio/Video → Texto                                              │
│      Tools: youtube-transcript-api, AssemblyAI, transcribe_full.py              │
│      Trigger: /process-video [URL]                                               │
│                                                                                  │
│   3. PIPELINE RAG (Busca Semantica)                                              │
│      ════════════════════════════════                                            │
│      Proposito: Indexar conhecimento para busca por similaridade                 │
│      Tools: ChromaDB + Voyage AI embeddings                                      │
│      Trigger: python rag_index.py --knowledge                                    │
│                                                                                  │
│   4. PIPELINE DE INGESTAO                                                        │
│      ════════════════════════════                                                │
│      Proposito: Organizar material novo no INBOX                                 │
│      Trigger: /ingest [URL ou caminho]                                           │
│                                                                                  │
│   5. PIPELINE ORG-LIVE                                                           │
│      ══════════════════════                                                      │
│      Proposito: Alimentar cargos humanos com conhecimento de agentes             │
│      Fases: Phase 8.1.6 do Jarvis                                                │
│      Trigger: Automatico apos Phase 7                                            │
│                                                                                  │
│   6. PIPELINE DE LOGS                                                            │
│      ═══════════════════                                                         │
│      Proposito: Registrar decisoes, sessoes, War Rooms                           │
│      Tools: decision_logger.py, trace_generator.py                               │
│      Trigger: Automatico ou /log                                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 Pipeline Jarvis em Detalhe

```
Phase 1: INITIALIZATION
    ├── Valida arquivo existe
    ├── Extrai metadados do path
    ├── Carrega state files
    └── Verifica se ja processado

Phase 2: CHUNKING
    ├── Le conteudo completo
    ├── Quebra em ~300 palavras
    ├── Preserva contexto
    └── Gera IDs unicos

Phase 3: ENTITY RESOLUTION
    ├── Identifica pessoas mencionadas
    ├── Identifica conceitos
    ├── Mapeia sinonimos → canonical
    └── Atualiza CANONICAL-MAP.json

Phase 4: INSIGHT EXTRACTION
    ├── Extrai insights de cada chunk
    ├── Classifica por prioridade
    ├── Categoriza por tema
    └── Atualiza INSIGHTS-STATE.json

Phase 5: NARRATIVE SYNTHESIS
    ├── Agrupa insights por pessoa
    ├── Agrupa insights por tema
    ├── Identifica padroes
    └── Atualiza NARRATIVES-STATE.json

Phase 6: DOSSIER COMPILATION
    ├── 6.5: Cria/atualiza DOSSIER-PESSOA
    ├── 6.5: Cria/atualiza DOSSIER-TEMA
    └── 6.6: Cria SOURCE (pessoa × tema)

Phase 7: AGENT ENRICHMENT
    ├── Identifica agentes relevantes
    ├── Atualiza MEMORYs
    └── Propaga para ORG-LIVE

Phase 8: FINALIZATION
    ├── Atualiza SESSION-STATE.md
    ├── Registra em file-registry
    ├── Gera EXECUTION REPORT
    └── Re-indexa RAG
```

---

# CAPITULO 7: PROTOCOLOS DE SEGURANCA

## 7.1 Epistemic Protocol (Anti-Alucinacao)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   REGRA: Agentes NUNCA inventam informacao                                       │
│   ════════════════════════════════════════                                       │
│                                                                                  │
│   FORMATO OBRIGATORIO DE RESPOSTA:                                               │
│                                                                                  │
│   ## FATOS                                                                       │
│   - [FONTE:SRC004:linha45] > "Citacao exata do material"                         │
│   - [FONTE:AH001:linha123] > "Outra citacao"                                    │
│                                                                                  │
│   ## RECOMENDACAO                                                                │
│   POSICAO: [O que eu recomendo]                                                  │
│   JUSTIFICATIVA: [Por que recomendo isso]                                        │
│   CONFIANCA: ALTA/MEDIA/BAIXA - [Justificativa]                                 │
│                                                                                  │
│   ## LIMITACOES                                                                  │
│   - [O que NAO sei]                                                              │
│   - [Areas de incerteza]                                                         │
│                                                                                  │
│   ⚠️ FRASES OBRIGATORIAS quando nao sabe:                                        │
│   • "Nao encontrei fonte para isso"                                              │
│   • "Isso e minha interpretacao, nao um fato documentado"                        │
│   • "Preciso de mais contexto para responder com confianca"                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 7.2 Enforcement Protocol

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   REGRAS INVIOLAVEIS DO PIPELINE                                                 │
│   ══════════════════════════════                                                 │
│                                                                                  │
│   ⛔ NUNCA pular etapas                                                          │
│   ⛔ NUNCA ir de INBOX direto para KNOWLEDGE                                     │
│   ⛔ NUNCA deletar chunks ou insights (apenas adicionar)                         │
│   ⛔ NUNCA processar sem registrar                                               │
│                                                                                  │
│   ✅ SEMPRE passar por TODAS as 8 fases                                          │
│   ✅ SEMPRE manter rastreabilidade (insight → chunk → arquivo)                   │
│   ✅ SEMPRE atualizar state files                                                │
│   ✅ SEMPRE citar fonte original                                                 │
│                                                                                  │
│   CHECKPOINTS:                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ Antes de cada fase, validar:                                            │   │
│   │ □ Fase anterior foi concluida                                           │   │
│   │ □ State files estao atualizados                                         │   │
│   │ □ Nenhum erro pendente                                                  │   │
│   │                                                                         │   │
│   │ Se falhar: PARAR e reportar                                             │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# CAPITULO 8: CASOS DE USO PRATICOS

## 8.1 "Quero entender como estruturar meu time de vendas"

```
VOCE: "Como devo estruturar meu time de vendas?"

SISTEMA:
1. Identifica que e pergunta para AGENT-CRO + AGENT-SALES-MANAGER
2. Busca no RAG por "estrutura time vendas"
3. Encontra:
   - DOSSIER-01-ESTRUTURA-TIME.md (multi-fonte)
   - Insights de Hormozi (Christmas Tree)
   - Insights de Cole Gordon (4 fases de saida)

RESPOSTA DO AGENTE:
"Baseado nas fontes processadas, existem 3 modelos principais:

1. CHRISTMAS TREE (Hormozi) [FONTE:AH001]
   BDR (base larga) → SDS (meio) → BC (topo estreito)

2. 4 FASES DE SAIDA (Cole Gordon) [FONTE:SRC004]
   Founder → Sales Lead → Coordinator → Manager

   SDR qualifica → Closer fecha

RECOMENDACAO: Comecar com modelo 3 (mais simples), migrar para 1 ao escalar.
CONFIANCA: ALTA - 3 fontes concordam em separar qualificacao de fechamento."
```

## 8.2 "Preciso contratar um closer"

```
VOCE: "Como contratar um closer?"

SISTEMA:
1. Identifica que e pergunta para AGENT-SALES-MANAGER
2. Busca ORG-LIVE para documento pratico
3. Encontra:
   - JD-CLOSER.md (Job Description pronto)
   - ROLE-CLOSER.md (Responsabilidades)
   - MEMORY-CLOSER.md (Base de conhecimento)

RESPOSTA:
"Tenho um JD pronto para voce usar:

📄 JD-CLOSER.md
- Requisitos: 2+ anos high-ticket, 25%+ close rate
- Responsabilidades: 3 ofertas/dia, reuniao diaria 9h
- Compensacao: R$3k fixo + 3-5% comissao

📋 ROLE-CLOSER.md
- Reporta a: Sales Manager ou Closer Chefe
- Nao faz: prospeccao, qualificacao, gestao

📚 MEMORY-CLOSER.md
- Frameworks: 7 Beliefs, CLOSER, 6-Phase Call Flow
- Metricas: Close Rate >25%, 3 ofertas/dia

Quer que eu gere o anuncio de vaga?"
```

## 8.3 "O que o Cole Gordon pensa sobre objections?"

```
VOCE: "O que o Cole Gordon pensa sobre objecoes?"

SISTEMA:
1. Busca DOSSIER-COLE-GORDON.md
2. Busca SOURCES/cole-gordon/PROCESSO-VENDAS.md
3. Filtra insights com categoria "objection_framework"

RESPOSTA:
"Cole Gordon tem uma filosofia clara sobre objecoes:

[FONTE:SRC004] '7 Beliefs Framework'
- Toda objecao vem de uma das 7 crencas nao resolvidas
- Pain, Doubt, Cost, Desire, Money, Support, Trust

[FONTE:SRC004] 'Pacing First Objection'
- Nunca argumentar contra a objecao
- Primeiro concordar, depois explorar

[FONTE:SRC004] 'Tie Down Questions'
- Usar perguntas que forcam consistencia
- 'Faz sentido, certo?' → Prospect se compromete

Ver tambem: DOSSIER-02-PROCESSO-VENDAS.md para visao multi-fonte."
```

---

# CAPITULO 9: COMANDOS DISPONIVEIS

| Comando | Proposito |
|---------|-----------|
| `/chat` | Abre o Moga Brain, mostra dashboard |
| `/process-jarvis` | Processa arquivo pelo pipeline completo |
| `/jarvis-full` | Pipeline completo sem paradas |
| `/ingest` | Adiciona material ao INBOX |
| `/inbox` | Lista materiais pendentes |
| `/scan-inbox` | Escaneia INBOX e sugere acoes |
| `/agents` | Status dos agentes e MEMORYs |
| `/dossiers` | Status dos dossies |
| `/loops` | Lista open loops pendentes |
| `/log` | Visualiza logs especificos |
| `/rag-search` | Busca semantica na knowledge base |
| `/config` | Configuracoes do sistema |
| `/system-digest` | Diagnostico completo |

---

# CAPITULO 10: ESTATISTICAS ATUAIS

| Metrica | Valor |
|---------|-------|
| Total Chunks | 260 |
| Total Insights | 157 |
| Pessoas Mapeadas | 11 |
| Dossies de Pessoas | 8 |
| Dossies de Temas | 10 |
| Agentes IA | 12 |
| Cargos ORG-LIVE | 13 |
| Frameworks Identificados | 60+ |
| Fontes Processadas | 40+ |

---

# EPILOGO: O Poder do Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   SEM MOGA BRAIN                         COM MOGA BRAIN                          │
│   ══════════════                         ═════════════                           │
│                                                                                  │
│   "Onde foi que eu vi aquilo             "CRO, como estruturo meu time?"        │
│    sobre estrutura de time?"             → Resposta instantanea com fontes      │
│                                                                                  │
│   "O Hormozi ou o Cole Gordon            "Mostra as diferencas entre            │
│    que falou sobre isso?"                 Hormozi e Cole Gordon sobre X"        │
│                                          → Comparativo citado                   │
│                                                                                  │
│   "Preciso rever 50 horas de             "Qual o framework de objection         │
│    video para encontrar..."               handling do Cole Gordon?"             │
│                                          → 7 Beliefs em 10 segundos             │
│                                                                                  │
│   "Tenho que criar um JD                 "/agents CLOSER → JD-CLOSER.md         │
│    do zero"                               pronto para usar"                     │
│                                                                                  │
│   "Conhecimento perdido                  "Todo insight e permanente,            │
│    quando esqueço"                        rastreavel, consultavel"              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# GLOSSARIO RAPIDO

| Termo | Significado |
|-------|-------------|
| **Chunk** | Pedaco semantico de ~300 palavras |
| **Insight** | Informacao acionavel extraida de chunk |
| **Dossie** | Ficha completa de pessoa ou tema |
| **Agent** | Consultor virtual especializado |
| **ROLE** | Definicao de cargo humano |
| **MEMORY** | Base de conhecimento de um agente |
| **Pipeline Jarvis** | Processo de digestao de material |
| **RAG** | Sistema de busca semantica |
| **ORG-LIVE** | Sistema de cargos humanos vivos |
| **Canonical** | Forma padronizada de uma entidade |

---

*MOGA BRAIN v3.29.0 - Sistema de Inteligencia Operacional*
*Documento criado em 2025-12-22*
