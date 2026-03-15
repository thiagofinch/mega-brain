# DOSSIÊ: SISTEMA DIGESTIVO DO MEGA BRAIN

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🧠 MEGA BRAIN - SISTEMA DIGESTIVO DO CONHECIMENTO              ║
║                                                                              ║
║                      [ CHUNK ] ──────────► [ NARRATIVE ]                    ║
║                                                                              ║
║                           Versão 1.0 | 2026-01-12                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## SUMÁRIO EXECUTIVO

O Sistema Digestivo do JARVIS é um pipeline de **8 fases** que transforma conhecimento bruto (transcrições, documentos, vídeos) em artefatos estruturados e acionáveis. Cada fase é **incremental** (nunca deleta), **rastreável** (vinculada a chunks originais) e **multi-camada** (consolida progressivamente).

---

## VISÃO GERAL DO FLUXO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   RAW INPUT          PROCESSING           SYNTHESIS           OUTPUT        │
│   ─────────          ──────────           ─────────           ──────        │
│                                                                             │
│   inbox     →     CHUNKS        →      INSIGHTS     →      DOSSIERS     │
│   (brutos)           (semânticos)         (priorizados)       (narrativas) │
│                          │                     │                   │        │
│                          ▼                     ▼                   ▼        │
│                     ENTITIES            NARRATIVES              AGENTS      │
│                     (canônicos)         (consolidadas)          (DNA)       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FASE 1: CHUNKING (Primeira Mastigação)

### O Que É
Quebra de documentos brutos em pedaços semânticos processáveis.

### Entrada
- `/inbox/` - Arquivos brutos (.txt, .md, transcrições)
- Arquivos já tagueados: `[TAG] TITULO.txt`

### Saída
- `/processing/CHUNKS/*.json`
- `CHUNKS-STATE.json` (índice master)

### Estrutura do Chunk

```json
{
  "chunk_id": "AH-YT001_001",
  "source_id": "AH-YT001",
  "source_type": "youtube|podcast|course",
  "speaker": "Alex Hormozi",
  "corpus": "acquisition_com",
  "texto": "...",
  "temas": ["02-PROCESSO-VENDAS", "05-METRICAS"],
  "pessoas": ["Cole Gordon", "Jordan Lee"],
  "frameworks": ["CLOSER Framework"],
  "metricas": ["35% close rate", "$100k ACV"],
  "word_count": 297,
  "metadata": {
    "timestamp_start": "00:05:30",
    "timestamp_end": "00:08:45",
    "indexed_at": "2025-12-29T20:18:46"
  }
}
```

### Critérios de Corte
| Critério | Descrição |
|----------|-----------|
| Mudança de tópico | Novo assunto = novo chunk |
| Mudança de speaker | Podcasts/entrevistas |
| Conclusão de raciocínio | Framework completo |
| Limite de tokens | ~500-800 tokens |
| Transição temporal | Mudança de contexto |

### Scripts
- `/scripts/rag/chunker.py`
  - `chunk_by_tokens()` - Por tamanho
  - `chunk_markdown()` - Preserva headers
  - `chunk_plaintext()` - Texto simples

---

## FASE 2: ENTITY RESOLUTION (Canonicalização)

### O Que É
Normalização de entidades para forma canônica única.

### Entrada
- Chunks do step anterior

### Saída
- `/processing/CANONICAL/CANONICAL-MAP.json`

### Transformação
```
"Cole" + "Cole Gordon" + "CG" → COLE-GORDON
"CLOSER framework" + "Closer" → CLOSER-FRAMEWORK
"setter" + "SDR" → SDR
```

### Tipos de Entidade

| Tipo | Exemplo RAW | Canônico |
|------|-------------|----------|
| person | "Cole", "Cole Gordon" | COLE-GORDON |
| company | "Closers IO" | CLOSERS-IO |
| framework | "CLOSER framework" | CLOSER-FRAMEWORK |
| metric | "close rate" | CLOSE-RATE |
| role | "setter", "SDR" | SDR |
| concept | "high ticket" | HIGH-TICKET |

### Estrutura CANONICAL-MAP.json

```json
{
  "entities": {
    "cole-gordon": {
      "type": "person",
      "aliases": ["Cole", "Cole Gordon", "CG"],
      "chunk_refs": ["CG-ST001_001", "CG-ST001_005"],
      "source_count": 5,
      "total_mentions": 47
    },
    "CLOSER-FRAMEWORK": {
      "type": "framework",
      "aliases": ["closer", "The CLOSER Framework"],
      "chunk_refs": ["AH-YT001_003", "CG-ST001_012"],
      "source_count": 2,
      "components": ["C", "L", "O", "S", "E", "R"]
    }
  }
}
```

---

## FASE 3: INSIGHT EXTRACTION (Priorização)

### O Que É
Extração de conhecimento acionável e priorizado dos chunks.

### Entrada
- Chunks + Canonical Map

### Saída
- `/processing/INSIGHTS/INSIGHTS-STATE.json`

### O Que É Um Insight

```json
{
  "id": "SP-CG001",
  "insight": "7 Beliefs Framework: Qualquer objeção mapeia a uma de 7 crenças",
  "chunks": ["CG-ST001_012", "CG-ST001_015"],
  "confidence": "HIGH",
  "priority": "HIGH",
  "source_person": "cole-gordon",
  "frameworks_mentioned": ["7-BELIEFS", "DISCOVERY"],
  "metrics_cited": {
    "close_rate": "35%",
    "show_rate": "80%"
  }
}
```

### 8 Categorias de Insight

| Categoria | Descrição |
|-----------|-----------|
| `sales_process` | Técnicas de fechamento, objeções, scripts |
| `team_structure` | Hierarquia, funções, pipeline |
| `hiring_training` | Recrutamento, onboarding, desenvolvimento |
| `pricing_offers` | Precificação, ofertas, âncoras |
| `lead_generation` | Prospecção, funil, qualificação |
| `metrics_kpis` | Métricas, benchmarks, targets |
| `mindset_culture` | Mentalidade, filosofia, liderança |
| `compensation` | Comissionamento, OTE, incentivos |

---

## FASE 4: NARRATIVE SYNTHESIS (Consolidação)

### O Que É
Criação de histórias coerentes por pessoa/tema a partir dos insights.

### Entrada
- Insights agrupados por pessoa

### Saída
- `/processing/NARRATIVES/NARRATIVES-STATE.json`

### Estrutura da Narrativa

```json
{
  "person": "cole-gordon",
  "theme": "02-PROCESSO-VENDAS",
  "narrative": {
    "core_philosophy": "Filosofia supera táticas. Mental models corretos geram scripts naturais.",
    "key_frameworks": ["7-BELIEFS", "6-PHASE-CALL-FLOW", "4-PILLARS-PITCH"],
    "tactical_insights": [
      "Discovery é onde trust é construída, não em rapport",
      "Internal pressure > external pressure",
      "Objeções são sintomas, prevenção é upstream"
    ],
    "metrics_benchmarks": {
      "close_rate": "35%",
      "show_rate": "80%"
    },
    "contradictions": [],
    "unique_contributions": [
      "Framework das 7 Crenças única de Cole",
      "Ênfase em filosofia vs scripts (diferente de Alex)"
    ]
  },
  "insight_ids": ["SP-CG001", "SP-CG002"],
  "chunk_coverage": ["CG-ST001_001", "CG-ST001_005"]
}
```

---

## FASE 5: DNA CONSOLIDATION (5 Camadas Cognitivas)

### O Que É
Estruturação do conhecimento de uma pessoa em 5 camadas cognitivas.

### Trigger de Criação
```
SE: DOSSIER-{PESSOA}.md existe
    + densidade >= 3 de 5 temas cobertos
ENTÃO: Criar DNA completo
```

### As 5 Camadas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  CAMADA 1: FILOSOFIAS.yaml                                                  │
│  └── Crenças fundamentais, "Por quê?" faz o que faz                        │
│      Exemplo: "Filosofia supera tática. Sempre."                           │
│                                                                             │
│  CAMADA 2: MODELOS-MENTAIS.yaml                                             │
│  └── Frameworks de decisão internalizados                                   │
│      Exemplo: "Escada de Valor", "Flywheel"                                │
│                                                                             │
│  CAMADA 3: HEURISTICAS.yaml                                                 │
│  └── Regras rápidas COM NÚMEROS                                            │
│      Exemplo: "Se close rate < 20%, problema está no qualifying"           │
│                                                                             │
│  CAMADA 4: FRAMEWORKS.yaml                                                  │
│  └── Processos estruturados que ensina                                      │
│      Exemplo: "CLOSER Framework", "7 Beliefs"                              │
│                                                                             │
│  CAMADA 5: METODOLOGIAS.yaml                                                │
│  └── Sistemas completos e abrangentes                                       │
│      Exemplo: "100M Offers System", "Sales Machine"                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Localização

```
knowledge/dna/persons/{PESSOA}/
├── CONFIG.yaml           # Voice, patterns, coverage
├── FILOSOFIAS.yaml       # Camada 1
├── MODELOS-MENTAIS.yaml  # Camada 2
├── HEURISTICAS.yaml      # Camada 3
├── FRAMEWORKS.yaml       # Camada 4
├── METODOLOGIAS.yaml     # Camada 5
└── SOUL.md               # Identidade narrativa
```

### Exemplo: CONFIG.yaml

```yaml
person:
  canonical: "cole-gordon"
  display_name: "Cole Gordon"
  company: "Closers.io"

voice:
  tone: "direto, pedagógico, filosofia-first"
  vocabulary: ["beliefs", "consistency", "conviction"]
  signature_phrases:
    - "Filosofia supera tática"
    - "Objeções são sintomas"

behavioral_patterns:
  decision_style: "conviction-based, not tactics-first"
  communication_style: "teaching + challenge"

coverage:
  total_sources: 30
  total_chunks: 373
  total_insights: 48
  themes_covered: ["02-PROCESSO-VENDAS", "03-CONTRATACAO", "05-METRICAS"]
```

---

## FASE 6: AGGREGATION (Cross-Source)

### O Que É
Consolidação de insights de múltiplas fontes/pessoas em artefatos por tema.

### Entrada
- Narrativas de múltiplas pessoas

### Saída
- `/processing/AGGREGATED/AGG-*.yaml`

### Estrutura AGG

```yaml
# AGG-VENDAS.yaml
theme: "02-PROCESSO-VENDAS"
version: "2.1.0"
last_updated: "2026-01-10T18:30:00Z"

consensus:
  description: "O que TODAS as fontes concordam"
  points:
    - "Discovery é crítica"
    - "Close rate = função do qualifying"

divergence:
  - item: "Script vs Improviso"
    cole: "Filosofia > Script"
    alex: "Frameworks estruturados"
    jeremy: "Adaptabilidade"

frameworks:
  - name: "CLOSER Framework"
    source: "cole-gordon"
  - name: "3-Framework System"
    source: "alex-hormozi"

metrics_across_sources:
  close_rate:
    cole: "35%"
    alex: "variable"
    jeremy: "varies by ICP"

open_questions:
  - "Como cada um estrutura a economia das calls?"
```

---

## FASE 7: DOSSIER COMPILATION (Output Final)

### O Que É
Compilação de narrativas em documentos legíveis para humanos.

### Entrada
- Narrativas + AGGs + DNA

### Saída
- `/knowledge/dossiers/persons/DOSSIER-{PESSOA}.md`
- `/knowledge/dossiers/THEMES/DOSSIER-{TEMA}.md`

### Estrutura Dossier PESSOA

```markdown
# DOSSIER: Cole Gordon

## Filosofia Central
> Filosofia supera táticas...

## Frameworks Principais
- 7-Beliefs
- 6-Phase Call Flow
- 4-Pillars Pitch

## Insights por Tema
### 02-PROCESSO-VENDAS
- Discovery é onde trust é construída
- Internal pressure > external
- Objeções são sintomas

## Métricas Citadas
- Close rate: 35%
- Show rate: 80%

## Citações Diretas
> "Filosofia supera tática. Sempre."

## Conexões com Outros
- Cole vs Alex: Filosofia vs Volume
- Cole vs Jeremy: Teaching vs Coaching

## Fontes Processadas
- 30 batches
- ~373 DNA elements
```

### Estrutura Dossier TEMA

```markdown
# DOSSIER: 02-PROCESSO-VENDAS

## Overview
Processo de venda, técnicas de fechamento, descoberta de necessidades

## Abordagens por Pessoa
### Cole Gordon
- 7 Beliefs para qualificar

### Alex Hormozi
- CLOSER Framework

## Consensos Cross-Source
1. Discovery é crítica
2. Close rate é função de qualifying

## Divergências Interessantes
| Aspecto | Cole | Alex | Jeremy |
|---------|------|------|--------|
| Script vs Improviso | Filosofia | Frameworks | Adaptável |

## Frameworks Consolidados
1. CLOSER Framework (Alex)
2. 7-Beliefs (Cole)
```

---

## FASE 8: AGENT ENRICHMENT (Opcional)

### O Que É
Alimentação de agentes de IA com o conhecimento processado.

### Entrada
- Dossiers + DNA + AGGs

### Saída
- `/agents/cargo/*/MEMORY.md`
- `/agents/persons/*/SOUL.md`
- `/agents/ORG-LIVE/ROLES/*.md`

### Mapeamento TEMA → AGENTES

```python
THEME_TO_AGENTS = {
    "02-PROCESSO-VENDAS": ["closer", "SDS", "LNS"],
    "03-CONTRATACAO": ["TALENT", "HR"],
    "05-METRICAS": ["CFO", "ANALYST"]
}
```

### Fluxo de Enriquecimento

```
INSIGHT (com tema)
    │
    ▼
THEME_TO_AGENTS[tema] → Lista de agentes
    │
    ▼
Para cada agente:
    ├── Atualizar MEMORY.md (adicionar insight com ^[FONTE])
    ├── Atualizar SOUL.md (se PERSON agent)
    └── Propagar para ORG-LIVE via ORG-PROTOCOL
```

---

## ARQUIVOS DE ESTADO

| Arquivo | Propósito | Localização |
|---------|-----------|-------------|
| `CHUNKS-STATE.json` | Índice de chunks | `/processing/CHUNKS/` |
| `CANONICAL-MAP.json` | Entidades normalizadas | `/processing/CANONICAL/` |
| `INSIGHTS-STATE.json` | Insights categorizados | `/processing/INSIGHTS/` |
| `NARRATIVES-STATE.json` | Narrativas por pessoa | `/processing/NARRATIVES/` |

---

## DIAGRAMA COMPLETO DO FLUXO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  inbox (RAW)                                                             │
│  ├─ [CG-ST001] Cole-Sales-Training-001.txt                                 │
│  └─ [AH-YT001] Alex-30-Min-Sales-Video.md                                  │
│          │                                                                  │
│          ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 1: CHUNKING                                                   │   │
│  │  → processing/CHUNKS/CG-ST001-chunks.json                       │   │
│  │  → 27 chunks criados                                               │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 2: ENTITY RESOLUTION                                          │   │
│  │  "Cole" + "Cole Gordon" → COLE-GORDON                              │   │
│  │  → CANONICAL-MAP.json                                              │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 3: INSIGHT EXTRACTION                                         │   │
│  │  → "7 Beliefs Framework elimina objeções"                          │   │
│  │  → INSIGHTS-STATE.json                                             │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 4: NARRATIVE SYNTHESIS                                        │   │
│  │  → Narrativa: "Cole Gordon - Processo de Vendas"                   │   │
│  │  → NARRATIVES-STATE.json                                           │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 5: DNA CONSOLIDATION (se trigger met)                         │   │
│  │  → knowledge/dna/persons/cole-gordon/                           │   │
│  │     ├─ CONFIG.yaml                                                  │   │
│  │     ├─ FILOSOFIAS.yaml                                              │   │
│  │     ├─ MODELOS-MENTAIS.yaml                                         │   │
│  │     ├─ HEURISTICAS.yaml                                             │   │
│  │     ├─ FRAMEWORKS.yaml                                              │   │
│  │     └─ METODOLOGIAS.yaml                                            │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 6: AGGREGATION                                                │   │
│  │  → processing/AGGREGATED/AGG-VENDAS.yaml                        │   │
│  │     ├─ Consensos (Cole + Alex + Jeremy)                            │   │
│  │     └─ Divergências                                                 │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 7: DOSSIER COMPILATION                                        │   │
│  │  → knowledge/dossiers/persons/DOSSIER-COLE-GORDON.md             │   │
│  │  → knowledge/dossiers/THEMES/DOSSIER-02-PROCESSO-VENDAS.md       │   │
│  └──────────────────┬──────────────────────────────────────────────────┘   │
│                     │                                                      │
│                     ▼                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FASE 8: AGENT ENRICHMENT                                           │   │
│  │  → agents/cargo/sales/closer/MEMORY.md                          │   │
│  │  → agents/persons/cole-gordon/SOUL.md                           │   │
│  │  → agents/ORG-LIVE/ROLES/ROLE-CLOSER.md                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PRINCÍPIOS DO SISTEMA

| Princípio | Descrição |
|-----------|-----------|
| **INCREMENTAL** | Nunca deleta, apenas adiciona/refina |
| **RASTREÁVEL** | Todo insight liga a chunks específicos |
| **MULTI-CAMADA** | 8 categorias, 5 camadas DNA, 2+ níveis consolidação |
| **CROSS-SOURCE** | AGGs consolidam múltiplas pessoas/fontes |
| **TRIGGER-BASED** | DNA criado automaticamente quando threshold atingido |
| **AGENT-AWARE** | Cada artefato sabe qual agente deve receber |

---

## ARQUITETURA DE PASTAS

```
inbox/                              # Raw entrada
├─ [TAG] TITULO.txt

processing/                         # Pipeline intermediário
├─ CHUNKS/
│  ├─ CHUNKS-STATE.json
│  └─ SOURCE-ID-chunks.json
├─ CANONICAL/
│  └─ CANONICAL-MAP.json
├─ INSIGHTS/
│  └─ INSIGHTS-STATE.json
├─ NARRATIVES/
│  └─ NARRATIVES-STATE.json
└─ AGGREGATED/
   └─ AGG-*.yaml

knowledge/                          # Output final
├─ DOSSIERS/
│  ├─ PERSONS/
│  │  └─ DOSSIER-{PESSOA}.md
│  └─ THEMES/
│     └─ DOSSIER-{TEMA}.md
├─ DNA/
│  └─ PERSONS/{PESSOA}/
│     └─ (6 YAMLs + SOUL.md)
└─ sources/
   └─ {pessoa}/

agents/                             # Agentes de IA
├─ cargo/{area}/{role}/
│  └─ MEMORY.md
├─ persons/{pessoa}/
│  └─ SOUL.md
└─ ORG-LIVE/
   └─ ROLES/

scripts/                            # Motores
├─ rag/chunker.py
├─ rag/indexer.py
├─ jarvis_pipeline.py
└─ narrative_synthesis_*.py
```

---

## METADADOS

```yaml
dossie:
  titulo: "Sistema Digestivo do Mega Brain"
  versao: "1.0"
  criado_em: "2026-01-12"
  autor: "JARVIS"
  tipo: "system-documentation"

cobertura:
  fases: 8
  arquivos_estado: 4
  camadas_dna: 5
  categorias_insight: 8
```

---

*Dossiê gerado por JARVIS para documentação do sistema Mega Brain.*
