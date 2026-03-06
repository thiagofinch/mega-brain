# MEGA BRAIN: A MAQUINA COMPLETA
### Pipeline Intelligence Layer v4.0 — Documentacao Oficial

```
 ╔══════════════════════════════════════════════════════════════════════════╗
 ║                                                                        ║
 ║   ██╗███╗   ███╗███████╗ ██████╗  █████╗                              ║
 ║   ██║████╗ ████║██╔════╝██╔════╝ ██╔══██╗                             ║
 ║   ██║██╔████╔██║█████╗  ██║  ███╗███████║                             ║
 ║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║                             ║
 ║   ██║██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║                             ║
 ║   ╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝                             ║
 ║                                                                        ║
 ║   ██████╗ ██████╗  █████╗ ██╗███╗   ██╗                               ║
 ║   ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║                               ║
 ║   ██████╔╝██████╔╝███████║██║██╔██╗ ██║                               ║
 ║   ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║                               ║
 ║   ██████╔╝██║  ██║██║  ██║██║██║ ╚████║                               ║
 ║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝                               ║
 ║                                                                        ║
 ║            INTELLIGENCE LAYER v4.0 — PIPELINE COMPLETA                 ║
 ║                                                                        ║
 ║   "De qualquer conteudo ingerido, o Mega Brain automaticamente:        ║
 ║    detecta entidades, infere cargos, trigga dossiers, cria agentes     ║
 ║    com Skills operacionais, mapeia cadeias organizacionais, e          ║
 ║    prepara SOWs que servem tanto para configurar agentes IA quanto     ║
 ║    para contratar pessoas reais."                                      ║
 ║                                                                        ║
 ║   Data: 2026-02-26                                                     ║
 ║   Versao: 4.0.0                                                        ║
 ║   Autor: JARVIS (Chronicler)                                           ║
 ╚══════════════════════════════════════════════════════════════════════════╝
```

---

## INDICE

1. [Visao Geral da Maquina](#1-visao-geral-da-maquina)
2. [Fase 0: Ingestao de Conteudo](#2-fase-0-ingestao-de-conteudo)
3. [Fase 1: MODO 1 — Destinos Declarados](#3-fase-1-modo-1--destinos-declarados)
4. [Fase 2: MODO 2 — Inferencia Inteligente](#4-fase-2-modo-2--inferencia-inteligente)
5. [Fase 3: MODO 3 — Gatilhos de Threshold](#5-fase-3-modo-3--gatilhos-de-threshold)
6. [Fase 4: Merge e Cascateamento](#6-fase-4-merge-e-cascateamento)
7. [Fase 5: MODO 4 — Analise de Inteligencia](#7-fase-5-modo-4--analise-de-inteligencia) **[NOVO v4.0]**
8. [Fase 6: MODO 5 — Enforcement de Qualidade](#8-fase-6-modo-5--enforcement-de-qualidade) **[NOVO v4.0]**
9. [Fase 7: Validacao e Manifest](#9-fase-7-validacao-e-manifest)
10. [Human Checkpoints e Review Queue](#10-human-checkpoints-e-review-queue) **[NOVO v4.0]**
11. [Mapa Completo de Scripts](#11-mapa-completo-de-scripts)
12. [Mapa Completo de Hooks](#12-mapa-completo-de-hooks)
13. [Todos os Thresholds e Gatilhos](#13-todos-os-thresholds-e-gatilhos)
14. [Estrutura de Diretorios](#14-estrutura-de-diretorios)
15. [KPIs de Sucesso](#15-kpis-de-sucesso)

---

## 1. VISAO GERAL DA MAQUINA

A melhor forma de entender o Mega Brain e como uma **fabrica de conhecimento**.
Conteudo bruto entra por um lado. Do outro lado saem:
agentes inteligentes, dossiers tematicos, skills executaveis,
organogramas empresariais, e SOWs que servem para IA e humanos.

```
 ╔═══════════════════════════════════════════════════════════════════════════════╗
 ║                     A MAQUINA MEGA BRAIN — VISAO AEREA                      ║
 ╠═══════════════════════════════════════════════════════════════════════════════╣
 ║                                                                             ║
 ║  ENTRADA (Qualquer Conteudo)                                                ║
 ║  ═══════════════════════════                                                ║
 ║  Videos YouTube, PDFs, Podcasts, Transcricoes, Artigos, Cursos              ║
 ║       │                                                                     ║
 ║       ▼                                                                     ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐     ║
 ║  │                    INGESTAO & CHUNKING                             │     ║
 ║  │  Conteudo bruto → Chunks semanticos (JSON) → Insights curados     │     ║
 ║  │  processing/chunks/*.json    processing/insights/*.json            │     ║
 ║  └───────────────────────────────────┬─────────────────────────────────┘     ║
 ║                                      │                                      ║
 ║                                      ▼                                      ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐     ║
 ║  │              BATCH.md (Documento de Lote)                          │     ║
 ║  │  Markdown com: metadata, chunks ref, DESTINO DO CONHECIMENTO       │     ║
 ║  │  "Para onde este conhecimento deve ir"                             │     ║
 ║  └───────────────────────────────────┬─────────────────────────────────┘     ║
 ║                                      │                                      ║
 ║                                      ▼                                      ║
 ║  ╔═════════════════════════════════════════════════════════════════════╗     ║
 ║  ║           ORQUESTRADOR: post_batch_cascading.py v4.0              ║     ║
 ║  ║                    (O CORACAO DA MAQUINA)                         ║     ║
 ║  ║                                                                   ║     ║
 ║  ║   MODO 1 ──► Destinos Declarados (o autor disse)                  ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║   MODO 2 ──► Inferencia Inteligente (IA descobre)                 ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║   MODO 3 ──► Gatilhos de Threshold (limites atingidos)            ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║   MERGE ──► Combina tudo (declarado tem prioridade)               ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║   CASCADE ──► Grava nos destinos fisicos                          ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║ ┌─────────────────────────────────────────────────────────┐       ║     ║
 ║  ║ │  ★ MODO 4 ──► Business Model + SOW + Skills  [NOVO]    │       ║     ║
 ║  ║ │  ★ MODO 5 ──► Quality Gates + APEX Scoring   [NOVO]    │       ║     ║
 ║  ║ └─────────────────────────────────────────────────────────┘       ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║   VALIDATE ──► REGRA #26 (integridade)                            ║     ║
 ║  ║      │                                                            ║     ║
 ║  ║      ▼                                                            ║     ║
 ║  ║   MANIFEST ──► Registra 13 steps executados                       ║     ║
 ║  ╚═════════════════════════════════════════════════════════════════════╝     ║
 ║                                      │                                      ║
 ║                                      ▼                                      ║
 ║  SAIDAS (Artefatos Gerados)                                                 ║
 ║  ══════════════════════════                                                 ║
 ║                                                                             ║
 ║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         ║
 ║  │ AGENTES  │ │ DOSSIERS │ │  SKILLS  │ │   SOWs   │ │PLAYBOOKS │         ║
 ║  │ de Cargo │ │Tematicos │ │Executav. │ │Dual-Purp.│ │Operacion.│         ║
 ║  │ agents/  │ │knowledge/│ │knowledge/│ │ agents/  │ │knowledge/│         ║
 ║  │ cargo/   │ │dossiers/ │ │dna/skills│ │cargo/SOW │ │playbooks/│         ║
 ║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         ║
 ║                                                                             ║
 ╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Em uma frase:** Conteudo entra como video/PDF, e sai como agentes operacionais
com ferramentas, skills, SOWs, e quality gates — tudo rastreavel.

---

## 2. FASE 0: INGESTAO DE CONTEUDO

Antes de qualquer processamento, o conteudo bruto precisa ser transformado
em formato que a maquina entende.

```
 ╔═════════════════════════════════════════════════════════════════╗
 ║                     FASE 0: INGESTAO                          ║
 ╠═════════════════════════════════════════════════════════════════╣
 ║                                                                ║
 ║  FONTES DE CONTEUDO                                            ║
 ║  ══════════════════                                            ║
 ║                                                                ║
 ║  YouTube ──┐                                                   ║
 ║  PDFs ─────┤                                                   ║
 ║  Podcasts ─┤──► TRANSCRICAO ──► CHUNKING ──► CHUNKS (JSON)    ║
 ║  Cursos ───┤                                                   ║
 ║  Artigos ──┘                                                   ║
 ║                                                                ║
 ║  Cada CHUNK e um pedaco semantico com:                         ║
 ║  ┌─────────────────────────────────────────────────────┐       ║
 ║  │ {                                                   │       ║
 ║  │   "chunk_id": "CG-SM001-042",                      │       ║
 ║  │   "source": "Cole Gordon - Sales Masterclass",      │       ║
 ║  │   "text": "The CLOSER needs to master NEPQ...",     │       ║
 ║  │   "speaker": "Cole Gordon",                         │       ║
 ║  │   "themes": ["vendas", "objecoes"],                 │       ║
 ║  │   "frameworks": ["NEPQ"],                           │       ║
 ║  │   "key_concepts": ["discovery call", "pain points"] │       ║
 ║  │ }                                                   │       ║
 ║  └─────────────────────────────────────────────────────┘       ║
 ║                                                                ║
 ║  Localizacao:                                                  ║
 ║  processing/chunks/*.json     (96 chunks ativos)               ║
 ║  processing/insights/*.json   (8 insights curados)             ║
 ║                                                                ║
 ║  Apos chunking, um BATCH.md e criado com os destinos.          ║
 ║  Esse BATCH.md e o que dispara toda a maquina.                 ║
 ║                                                                ║
 ╚═════════════════════════════════════════════════════════════════╝
```

**Exemplo concreto:** Voce baixa 3 videos do Cole Gordon sobre vendas.
Cada video e transcrito e dividido em ~30 chunks semanticos. Esses chunks
contem frases como *"The closer needs to handle objections using NEPQ"*.
E nessa frase que a maquina inteira comeca a trabalhar.

---

## 3. FASE 1: MODO 1 — DESTINOS DECLARADOS

O primeiro passo e ler o que o **autor do batch** declarou explicitamente.

```
 ╔═════════════════════════════════════════════════════════════════╗
 ║             FASE 1: MODO 1 — DESTINOS DECLARADOS              ║
 ╠═════════════════════════════════════════════════════════════════╣
 ║                                                                ║
 ║  REGRA #22: "DESTINO DO CONHECIMENTO nao e informativa —      ║
 ║              e ORDEM DE EXECUCAO."                             ║
 ║                                                                ║
 ║  O batch contem uma secao assim:                               ║
 ║                                                                ║
 ║  ┌─────────────────────────────────────────────────┐           ║
 ║  │  ## DESTINO DO CONHECIMENTO                     │           ║
 ║  │                                                 │           ║
 ║  │  AGENTES A ALIMENTAR:                           │           ║
 ║  │  - CLOSER (frameworks: NEPQ, Objection Loop)    │           ║
 ║  │  - BDR (frameworks: Cold Call Script)            │           ║
 ║  │                                                 │           ║
 ║  │  PLAYBOOKS A ENRIQUECER:                        │           ║
 ║  │  - PLAYBOOK-VENDAS-001                          │           ║
 ║  │                                                 │           ║
 ║  │  DNA A CONSOLIDAR:                              │           ║
 ║  │  - DNA-VENDAS (3 novos frameworks)              │           ║
 ║  │                                                 │           ║
 ║  │  DOSSIERS:                                      │           ║
 ║  │  - Dossier Objecoes em Vendas                   │           ║
 ║  └─────────────────────────────────────────────────┘           ║
 ║                                                                ║
 ║  Script: extract_destinations() no orquestrador                ║
 ║  Input:  Texto markdown do batch                               ║
 ║  Output: Lista de destinos por tipo                            ║
 ║                                                                ║
 ║  ┌─────────────────────────────────────────────────┐           ║
 ║  │  {                                              │           ║
 ║  │    "agents":    [CLOSER, BDR],                  │           ║
 ║  │    "playbooks": [PLAYBOOK-VENDAS-001],          │           ║
 ║  │    "dnas":      [DNA-VENDAS],                   │           ║
 ║  │    "dossiers":  [Dossier Objecoes]              │           ║
 ║  │  }                                              │           ║
 ║  └─────────────────────────────────────────────────┘           ║
 ║                                                                ║
 ║  IMPORTANTE: Declarado tem PRIORIDADE sobre inferido.          ║
 ║  Se o autor disse "vai pro CLOSER", vai pro CLOSER.            ║
 ║                                                                ║
 ╚═════════════════════════════════════════════════════════════════╝
```

---

## 4. FASE 2: MODO 2 — INFERENCIA INTELIGENTE

Aqui e onde a maquina comeca a pensar sozinha. Mesmo que o autor
NAO tenha declarado destinos, a IA descobre para onde o conhecimento deve ir.

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                FASE 2: MODO 2 — INFERENCIA INTELIGENTE                   ║
 ╠═════════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  Tres scripts trabalham em conjunto para inferir destinos:                 ║
 ║                                                                           ║
 ║  ┌───────────────────────────────────────────────────────────────┐        ║
 ║  │                                                               │        ║
 ║  │   TEXTO DO BATCH: "The closer needs to master NEPQ and        │        ║
 ║  │   handle objections. Our BDR team of 8 generates leads.       │        ║
 ║  │   We hired a copywriter for the sales pages."                 │        ║
 ║  │                                                               │        ║
 ║  └───────────┬───────────────────┬───────────────────┬───────────┘        ║
 ║              │                   │                   │                     ║
 ║              ▼                   ▼                   ▼                     ║
 ║  ┌───────────────┐  ┌────────────────┐  ┌──────────────────────┐         ║
 ║  │ ROLE DETECTOR │  │ THEME ANALYZER │  │ ENTITY NORMALIZER    │         ║
 ║  │  v2.0         │  │  v1.0          │  │  v1.0                │         ║
 ║  │               │  │                │  │                      │         ║
 ║  │ 3 niveis de   │  │ Extrai temas   │  │ Canonicaliza nomes   │         ║
 ║  │ deteccao:     │  │ de qualquer    │  │ (fuzzy matching):    │         ║
 ║  │               │  │ formato:       │  │                      │         ║
 ║  │ DIRETO (1.0x) │  │ - key_concepts │  │ "Sam oven" ──►      │         ║
 ║  │ "closer" no   │  │ - temas[]      │  │   "Sam Ovens"       │         ║
 ║  │ texto         │  │ - themes[]     │  │                      │         ║
 ║  │               │  │ - metadata     │  │ "Hormozi" ──►        │         ║
 ║  │ INFERIDO(0.7x)│  │                │  │   "Alex Hormozi"     │         ║
 ║  │ "handle       │  │ Normaliza via  │  │                      │         ║
 ║  │  objections"  │  │ DOMAINS-       │  │ Thresholds:          │         ║
 ║  │ implica       │  │ TAXONOMY       │  │ >= 0.85: review      │         ║
 ║  │ CLOSER        │  │                │  │ >= 0.95: auto-merge  │         ║
 ║  │               │  │                │  │                      │         ║
 ║  │ EMERGENTE     │  │                │  │                      │         ║
 ║  │ (0.5x)        │  │                │  │                      │         ║
 ║  │ "we hired a   │  │                │  │                      │         ║
 ║  │ copywriter"   │  │                │  │                      │         ║
 ║  │ detecta novo  │  │                │  │                      │         ║
 ║  │ cargo         │  │                │  │                      │         ║
 ║  └───────┬───────┘  └───────┬────────┘  └──────────┬───────────┘         ║
 ║          │                  │                       │                     ║
 ║          ▼                  ▼                       ▼                     ║
 ║  ┌─────────────────────────────────────────────────────────────┐          ║
 ║  │              ENTITY-REGISTRY.json (v16)                    │          ║
 ║  │              "Single Source of Truth"                       │          ║
 ║  │                                                            │          ║
 ║  │  persons: 50  │  roles: 236  │  themes: 448  │  total: 734│          ║
 ║  │                                                            │          ║
 ║  │  Cada role acumula weighted_score:                         │          ║
 ║  │                                                            │          ║
 ║  │  CLOSER: direct=15 inferred=8 emergent=2                   │          ║
 ║  │          weighted_score = 15×1.0 + 8×0.7 + 2×0.5 = 21.6  │          ║
 ║  │          status: "active" (>= 10)                          │          ║
 ║  │                                                            │          ║
 ║  │  COPYWRITER: direct=3 inferred=12 emergent=1               │          ║
 ║  │          weighted_score = 3×1.0 + 12×0.7 + 1×0.5 = 11.9  │          ║
 ║  │          status: "active" (>= 10)                          │          ║
 ║  │                                                            │          ║
 ║  │  PODCAST-HOST: direct=0 inferred=0 emergent=2              │          ║
 ║  │          weighted_score = 0 + 0 + 2×0.5 = 1.0             │          ║
 ║  │          status: "emergent_candidate" (< 3)                │          ║
 ║  └─────────────────────────────────────────────────────────────┘          ║
 ║                                                                           ║
 ║  Scripts envolvidos:                                                      ║
 ║  ┌──────────────────────┬──────────────────────────────────────┐          ║
 ║  │ role_detector.py     │ Detecta cargos em 3 niveis          │          ║
 ║  │ theme_analyzer.py    │ Extrai temas de qualquer formato    │          ║
 ║  │ entity_normalizer.py │ Canonicaliza e deduplicacao fuzzy   │          ║
 ║  │ _ROLE_PATTERNS.yaml  │ Vocabulario de 33+ cargos com regex │          ║
 ║  │ DOMAINS-TAXONOMY.yaml│ 19 dominios para classificacao      │          ║
 ║  └──────────────────────┴──────────────────────────────────────┘          ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

**Exemplo concreto:**
O texto diz *"we hired a copywriter for the sales pages"*.
- **DIRETO:** Nao mencionou "COPYWRITER" como cargo formal → 0 pontos diretos
- **INFERIDO:** "hired a copywriter" bate no pattern `contrat[ao]r?\s+(?:a|um)\s+(\w+)` → +0.7
- **EMERGENTE:** Pattern generico `hired\s+a\s+(\w+)` tambem captura → +0.5
- **Total:** 1.2 pontos neste batch. Acumula com batches anteriores.

---

## 5. FASE 3: MODO 3 — GATILHOS DE THRESHOLD

Apos a deteccao, o sistema verifica: "Alguma entidade atingiu o limiar
para criar algo novo?"

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║             FASE 3: MODO 3 — GATILHOS DE THRESHOLD                       ║
 ╠═════════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  Dois scripts avaliam os thresholds:                                      ║
 ║                                                                           ║
 ║  ┌───────────────────────────────────────────────────────────────┐        ║
 ║  │  DOSSIER TRIGGER (dossier_trigger.py)                        │        ║
 ║  │                                                               │        ║
 ║  │  Para cada TEMA no registry, verifica:                        │        ║
 ║  │                                                               │        ║
 ║  │  ┌──────────────────────────────────────────────────┐         │        ║
 ║  │  │  Tema "Objecoes em Vendas":                      │         │        ║
 ║  │  │    occurrences: 23  (precisa >= 15)  ......  OK  │         │        ║
 ║  │  │    sources: 3       (precisa >= 2)   ......  OK  │         │        ║
 ║  │  │    frameworks: 4    (precisa >= 2)   ......  OK  │         │        ║
 ║  │  │    relevance: 27.5  (precisa >= 25)  ......  OK  │         │        ║
 ║  │  │    has_dossier: false                            │         │        ║
 ║  │  │    ─────────────────────────────────────         │         │        ║
 ║  │  │    RESULTADO: ★ CRIAR DOSSIER                    │         │        ║
 ║  │  └──────────────────────────────────────────────────┘         │        ║
 ║  └───────────────────────────────────────────────────────────────┘        ║
 ║                                                                           ║
 ║  ┌───────────────────────────────────────────────────────────────┐        ║
 ║  │  AGENT TRIGGER (agent_trigger.py v2.0) — 3 TIERS             │        ║
 ║  │                                                               │        ║
 ║  │  Para cada ROLE no registry, classifica em 3 niveis:          │        ║
 ║  │                                                               │        ║
 ║  │  ┌───────────────────────────────────────────────────────┐    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  TIER 1: ESTABLISHED (ws >= 10, sources >= 2)         │    │        ║
 ║  │  │  ════════════════════════════════════════════          │    │        ║
 ║  │  │  Acao: ★ CRIAR AGENTE                                 │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  Exemplos:                                            │    │        ║
 ║  │  │    CLOSER    ws=21.6  src=3  ──► CRIAR                │    │        ║
 ║  │  │    BDR       ws=14.2  src=2  ──► CRIAR                │    │        ║
 ║  │  │    COPYWRITER ws=11.9 src=2  ──► CRIAR                │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  ─────────────────────────────────────────────        │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  TIER 2: EMERGING (ws >= 5, sources >= 1)             │    │        ║
 ║  │  │  ════════════════════════════════════════              │    │        ║
 ║  │  │  Acao: Monitorar (status: "tracking")                 │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  Exemplos:                                            │    │        ║
 ║  │  │    CMO       ws=7.3   src=1  ──► MONITORAR            │    │        ║
 ║  │  │    DESIGNER  ws=5.5   src=1  ──► MONITORAR            │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  ─────────────────────────────────────────────        │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  TIER 3: EMERGENT (ws >= 3, sources >= 1)             │    │        ║
 ║  │  │  ════════════════════════════════════════              │    │        ║
 ║  │  │  Acao: Observar (status: "emergent_candidate")        │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  │  Exemplos:                                            │    │        ║
 ║  │  │    PODCAST-HOST ws=1.0  ──► OBSERVAR                  │    │        ║
 ║  │  │    VIDEOGRAPHER ws=3.2  ──► OBSERVAR                  │    │        ║
 ║  │  │                                                       │    │        ║
 ║  │  └───────────────────────────────────────────────────────┘    │        ║
 ║  └───────────────────────────────────────────────────────────────┘        ║
 ║                                                                           ║
 ║  Configuracao: trigger_config.yaml (v2.0)                                 ║
 ║                                                                           ║
 ║  Relevance Score (Dossiers):                                              ║
 ║  ┌────────────────────────────────────────────────────────┐               ║
 ║  │  cross_source_weight:  3.0  (bonus por fonte extra)    │               ║
 ║  │  framework_weight:     2.0  (bonus por framework)      │               ║
 ║  │  methodology_weight:   2.0  (bonus por metodologia)    │               ║
 ║  │  heuristic_weight:     1.5  (bonus por heuristica)     │               ║
 ║  │  philosophy_weight:    1.0  (bonus por filosofia)      │               ║
 ║  └────────────────────────────────────────────────────────┘               ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

**Exemplo concreto:** Apos 5 batches do Cole Gordon, o role CLOSER acumulou
weighted_score 21.6 e aparece em 3 fontes distintas. O agent_trigger diz:
*"CLOSER atingiu Tier 1 (established). CRIAR AGENTE."*

---

## 6. FASE 4: MERGE E CASCATEAMENTO

Agora os tres modos convergem. Destinos declarados, inferidos e triggados
sao combinados e o sistema grava fisicamente nos destinos.

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║              FASE 4: MERGE + CASCATEAMENTO FISICO                        ║
 ╠═════════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  MERGE: 3 fontes combinadas com prioridade                               ║
 ║                                                                           ║
 ║  ┌──────────┐   ┌──────────┐   ┌──────────┐                             ║
 ║  │ MODO 1   │ + │ MODO 2   │ + │ MODO 3   │                             ║
 ║  │Declarado │   │ Inferido │   │ Triggers │                             ║
 ║  │PRIORIDADE│   │          │   │          │                             ║
 ║  │ MAXIMA   │   │          │   │          │                             ║
 ║  └─────┬────┘   └─────┬────┘   └─────┬────┘                             ║
 ║        │              │              │                                    ║
 ║        └──────────────┼──────────────┘                                    ║
 ║                       │                                                   ║
 ║                       ▼                                                   ║
 ║              ┌────────────────┐                                           ║
 ║              │ DEDUPLICACAO   │  Se CLOSER aparece nos 3,                 ║
 ║              │ + MERGE        │  usa o do MODO 1 (declarado).             ║
 ║              └────────┬───────┘                                           ║
 ║                       │                                                   ║
 ║          ┌────────────┼────────────┬────────────┐                        ║
 ║          ▼            ▼            ▼            ▼                        ║
 ║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                   ║
 ║  │ cascade  │ │ cascade  │ │ cascade  │ │ cascade  │                   ║
 ║  │  _to_    │ │  _to_    │ │  _to_    │ │  _to_    │                   ║
 ║  │ agents() │ │playbooks │ │  dnas()  │ │dossiers()│                   ║
 ║  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘                   ║
 ║       │            │            │            │                           ║
 ║       ▼            ▼            ▼            ▼                           ║
 ║  agents/       knowledge/   knowledge/   knowledge/                      ║
 ║  cargo/        playbooks/   dna/         dossiers/                       ║
 ║  persons/                   persons/     themes/                         ║
 ║                                                                           ║
 ║  O que cada cascade faz:                                                  ║
 ║  1. Encontra o artefato existente OU cria novo                           ║
 ║  2. Extrai CONTEUDO REAL dos frameworks (nao so nomes)                   ║
 ║  3. Appenda ao arquivo do destino                                        ║
 ║  4. Loga no cascading.jsonl                                              ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 7. FASE 5: MODO 4 — ANALISE DE INTELIGENCIA

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                                                                           ║
 ║  ██╗███╗   ██╗ ██████╗ ██╗   ██╗ ██████╗     ██╗   ██╗██╗  ██╗ ██████╗  ║
 ║  ████╗  ██║██╔═══██╗██║   ██║██╔═══██╗    ██║   ██║██║  ██║██╔═══██╗ ║
 ║  ██╔██╗ ██║██║   ██║██║   ██║██║   ██║    ██║   ██║███████║██║   ██║ ║
 ║  ██║╚██╗██║██║   ██║╚██╗ ██╔╝██║   ██║    ╚██╗ ██╔╝╚════██║██║   ██║ ║
 ║  ██║ ╚████║╚██████╔╝ ╚████╔╝ ╚██████╔╝     ╚████╔╝      ██║╚██████╔╝ ║
 ║  ╚═╝  ╚═══╝ ╚═════╝   ╚═══╝   ╚═════╝       ╚═══╝       ╚═╝ ╚═════╝  ║
 ║                                                                           ║
 ║      FASE 5: MODO 4 — ANALISE DE INTELIGENCIA  [★ NOVO v4.0]            ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  Tres sub-etapas executam em sequencia:                                   ║
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  ★ MODO 4a: BUSINESS MODEL DETECTOR                                │  ║
 ║  │  ═══════════════════════════════════                                │  ║
 ║  │  Script: business_model_detector.py                                 │  ║
 ║  │                                                                     │  ║
 ║  │  O que faz:                                                         │  ║
 ║  │  Analisa chunks e descobre a ESTRUTURA ORGANIZACIONAL               │  ║
 ║  │  de cada pessoa mencionada.                                         │  ║
 ║  │                                                                     │  ║
 ║  │  Detecta:                                                           │  ║
 ║  │  ┌─────────────────────────────────────────────────────┐            │  ║
 ║  │  │  DEPARTAMENTOS                                      │            │  ║
 ║  │  │  "Our sales team" ──► Dept: Sales                   │            │  ║
 ║  │  │  "Head of Marketing" ──► Dept: Marketing            │            │  ║
 ║  │  │                                                     │            │  ║
 ║  │  │  TEAM SIZES                                         │            │  ║
 ║  │  │  "team of 12" ──► 12 pessoas                        │            │  ║
 ║  │  │  "grew to 200 employees" ──► 200 pessoas            │            │  ║
 ║  │  │                                                     │            │  ║
 ║  │  │  REVENUE SIGNALS                                    │            │  ║
 ║  │  │  "revenue of $100M" ──► $100M                       │            │  ║
 ║  │  │  "ticket medio de R$5.000" ──► R$5K                 │            │  ║
 ║  │  │                                                     │            │  ║
 ║  │  │  ROLE CONSOLIDATION                                 │            │  ║
 ║  │  │  "She also handles marketing" ──► 1 pessoa, 2 jobs  │            │  ║
 ║  │  │  "wears many hats" ──► consolidacao detectada        │            │  ║
 ║  │  │                                                     │            │  ║
 ║  │  │  ROLE CHAIN (Hierarquia)                            │            │  ║
 ║  │  │  CEO ──► COO ──► Sales Manager ──► Closer           │            │  ║
 ║  │  │     └──► CRO ──► BDR Lead ──► BDR                  │            │  ║
 ║  │  │         └──► CMO ──► Content Lead                   │            │  ║
 ║  │  └─────────────────────────────────────────────────────┘            │  ║
 ║  │                                                                     │  ║
 ║  │  Grava no ENTITY-REGISTRY:                                          │  ║
 ║  │  persons["Alex Hormozi"].business_model = {                         │  ║
 ║  │    departments: ["Sales", "Marketing", "Ops", "Acquisition"],       │  ║
 ║  │    team_size_estimate: "50-200",                                    │  ║
 ║  │    revenue_signals: ["$100M+"],                                     │  ║
 ║  │    role_chain: { CEO -> COO -> ... },                               │  ║
 ║  │    role_consolidation: [...]                                        │  ║
 ║  │  }                                                                  │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  ★ MODO 4b: SOW GENERATOR (Dual-Purpose)                           │  ║
 ║  │  ════════════════════════════════════════                           │  ║
 ║  │  Script: sow_generator.py                                           │  ║
 ║  │                                                                     │  ║
 ║  │  O que faz:                                                         │  ║
 ║  │  Para cada cargo com weighted_score suficiente, gera um             │  ║
 ║  │  SOW (Statement of Work) que serve TANTO para configurar            │  ║
 ║  │  agente IA quanto como job description para contratar humano.       │  ║
 ║  │                                                                     │  ║
 ║  │  EXECUTOR DECISION TREE (6 perguntas):                              │  ║
 ║  │  ┌──────────────────────────────────────────────────────────┐       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  │  Q1: Output 100% previsivel?                             │       │  ║
 ║  │  │      SIM ──► WORKER (automacao pura)                     │       │  ║
 ║  │  │      NAO ──► continua                                    │       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  │  Q2: Pode ser funcao pura (input → output)?              │       │  ║
 ║  │  │      SIM ──► WORKER                                      │       │  ║
 ║  │  │      NAO ──► continua                                    │       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  │  Q3: Precisa interpretar linguagem natural?              │       │  ║
 ║  │  │      NAO ──► WORKER                                      │       │  ║
 ║  │  │      SIM ──► continua                                    │       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  │  Q4: Impacto de erro e significativo?                    │       │  ║
 ║  │  │      SIM ──► HYBRID (humano valida)                      │       │  ║
 ║  │  │      NAO ──► continua                                    │       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  │  Q5: Requer julgamento estrategico?                      │       │  ║
 ║  │  │      SIM ──► HYBRID ou HUMAN                             │       │  ║
 ║  │  │      NAO ──► AGENT                                       │       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  │  Q6: IA pode assistir/preparar?                          │       │  ║
 ║  │  │      SIM ──► HYBRID (IA prepara, humano decide)          │       │  ║
 ║  │  │      NAO ──► HUMAN (100% humano)                         │       │  ║
 ║  │  │                                                          │       │  ║
 ║  │  └──────────────────────────────────────────────────────────┘       │  ║
 ║  │                                                                     │  ║
 ║  │  Resultado por cargo:                                               │  ║
 ║  │  ┌──────────────────────────────────────────────┐                   │  ║
 ║  │  │  CLOSER ──────────► Hybrid  (vende, IA prep) │                   │  ║
 ║  │  │  DATA-ANALYST ───► Agent   (opera com dados) │                   │  ║
 ║  │  │  BDR ─────────────► Hybrid  (outbound + IA)  │                   │  ║
 ║  │  │  REPORT-MAKER ───► Worker  (output previsiv) │                   │  ║
 ║  │  │  CEO ─────────────► Human   (100% estrateg.) │                   │  ║
 ║  │  └──────────────────────────────────────────────┘                   │  ║
 ║  │                                                                     │  ║
 ║  │  Grava: agents/cargo/{dominio}/{role}/SOW.md + SOW.json             │  ║
 ║  │  44 SOWs gerados atualmente                                         │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  ★ MODO 4c: SKILL GENERATOR (NERO Pipeline)                        │  ║
 ║  │  ═══════════════════════════════════════════                        │  ║
 ║  │  Script: skill_generator.py                                         │  ║
 ║  │                                                                     │  ║
 ║  │  O que faz:                                                         │  ║
 ║  │  Le os chunks/insights de cada persona e converte FRAMEWORKS        │  ║
 ║  │  mencionados em SKILLS EXECUTAVEIS (SKILL.md).                      │  ║
 ║  │                                                                     │  ║
 ║  │  Pipeline: Framework no DNA ──► SKILL.md executavel                 │  ║
 ║  │                                                                     │  ║
 ║  │  Exemplo:                                                           │  ║
 ║  │  Chunk diz: "I use the CLOSER Framework: C=Clarify, L=Label..."     │  ║
 ║  │                                                                     │  ║
 ║  │  Gera SKILL.md:                                                     │  ║
 ║  │  ┌──────────────────────────────────────────────────────┐           │  ║
 ║  │  │  # CLOSER Framework                                  │           │  ║
 ║  │  │  > Skill ID: dna-alex-hormozi-closer-framework       │           │  ║
 ║  │  │  > Source: DNA Layer 4 - Alex Hormozi                │           │  ║
 ║  │  │  > Type: sequential                                  │           │  ║
 ║  │  │                                                      │           │  ║
 ║  │  │  ## Quando Usar                                      │           │  ║
 ║  │  │  Calls de vendas high-ticket ($5K+)                  │           │  ║
 ║  │  │                                                      │           │  ║
 ║  │  │  ## Quando NAO Usar                                  │           │  ║
 ║  │  │  Vendas transacionais de baixo valor                 │           │  ║
 ║  │  │                                                      │           │  ║
 ║  │  │  ## Workflow                                          │           │  ║
 ║  │  │  1. Clarify the problem                              │           │  ║
 ║  │  │  2. Label the emotion                                │           │  ║
 ║  │  │  3. Overview the past attempts                       │           │  ║
 ║  │  │  4. Sell the solution                                │           │  ║
 ║  │  │  5. Explain away concerns                            │           │  ║
 ║  │  │  6. Reinforce the decision                           │           │  ║
 ║  │  │                                                      │           │  ║
 ║  │  │  ## Evidencia                                        │           │  ║
 ║  │  │  "The CLOSER framework is what I used to close       │           │  ║
 ║  │  │   over $100M in sales..." — Alex Hormozi             │           │  ║
 ║  │  └──────────────────────────────────────────────────────┘           │  ║
 ║  │                                                                     │  ║
 ║  │  Registra em: knowledge/dna/_dna-skills-registry.yaml               │  ║
 ║  │  530 skills geradas atualmente                                      │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. FASE 6: MODO 5 — ENFORCEMENT DE QUALIDADE

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                                                                           ║
 ║      FASE 6: MODO 5 — ENFORCEMENT DE QUALIDADE  [★ NOVO v4.0]           ║
 ║      "Nada ruim passa. Nada generico e criado."                          ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  ★ MODO 5a: QUALITY GATES (6 gates + 8 vetos)                      │  ║
 ║  │  ═════════════════════════════════════════════                      │  ║
 ║  │  Config: quality_gates.yaml                                         │  ║
 ║  │  Script: viability_scorer.py (funcao check_quality_gates)           │  ║
 ║  │                                                                     │  ║
 ║  │  6 GATES DE QUALIDADE:                                              │  ║
 ║  │  ┌──────────────────────────────────────────────────────────────┐   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  QG-1.1  ENTITY VIABILITY         [auto]                    │   │  ║
 ║  │  │  ────────────────────────────────────────                    │   │  ║
 ║  │  │  Pergunta: "Entidade tem evidencia suficiente?"              │   │  ║
 ║  │  │  Criterio: weighted_score >= 10 E sources >= 2              │   │  ║
 ║  │  │  Passa: marca como "active"                                  │   │  ║
 ║  │  │  Falha: marca como "tracking" (nao cria agente)             │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  QG-1.2  ENTITY DEDUPLICATION     [auto]                    │   │  ║
 ║  │  │  ────────────────────────────────────────                    │   │  ║
 ║  │  │  Pergunta: "Ja existe entidade igual?"                       │   │  ║
 ║  │  │  Criterio: fuzzy score < 0.85 contra existentes             │   │  ║
 ║  │  │  Passa: cria nova                                            │   │  ║
 ║  │  │  Falha: vai pra review_queue (merge manual)                 │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  QG-2.1  DOSSIER QUALITY          [auto]                    │   │  ║
 ║  │  │  ────────────────────────────────────────                    │   │  ║
 ║  │  │  Pergunta: "Dossier tem substancia?"                         │   │  ║
 ║  │  │  Criterio: relevance >= 25 E occurrences >= 15              │   │  ║
 ║  │  │            E sources >= 2 E frameworks >= 2                  │   │  ║
 ║  │  │  Passa: cria dossier                                         │   │  ║
 ║  │  │  Falha: marca como "candidate" (monitorar)                  │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  QG-3.1  AGENT CREATION QUALITY   [hybrid]                  │   │  ║
 ║  │  │  ────────────────────────────────────────                    │   │  ║
 ║  │  │  Pergunta: "Agente tem base pra existir?"                    │   │  ║
 ║  │  │  Criterio: SOW gerado E 3+ responsibilities                 │   │  ║
 ║  │  │            E domain match E ws >= 10                         │   │  ║
 ║  │  │  Passa: cria agente                                          │   │  ║
 ║  │  │  Falha: bloqueia (requer aprovacao humana)                  │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  QG-4.1  SKILL QUALITY            [auto]                    │   │  ║
 ║  │  │  ────────────────────────────────────────                    │   │  ║
 ║  │  │  Pergunta: "Skill e executavel?"                             │   │  ║
 ║  │  │  Criterio: source verificavel E 3+ workflow steps           │   │  ║
 ║  │  │            E evidence > 50 chars                             │   │  ║
 ║  │  │  Passa: publica skill                                        │   │  ║
 ║  │  │  Falha: marca como "draft"                                  │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  QG-5.1  BUSINESS MODEL CONSIST.  [hybrid]                  │   │  ║
 ║  │  │  ────────────────────────────────────────                    │   │  ║
 ║  │  │  Pergunta: "Modelo de negocio faz sentido?"                  │   │  ║
 ║  │  │  Criterio: sem ciclos na hierarquia E depts com roles       │   │  ║
 ║  │  │            E revenue consistente com team_size               │   │  ║
 ║  │  │  Passa: valida modelo                                        │   │  ║
 ║  │  │  Falha: flag pra revisao humana                              │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  └──────────────────────────────────────────────────────────────┘   │  ║
 ║  │                                                                     │  ║
 ║  │  8 CONDICOES DE VETO (bloqueantes — nao podem ser overridden):      │  ║
 ║  │  ┌──────────────────────────────────────────────────────────────┐   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  VC-001  < 2 fontes          ──► VETO criar agente          │   │  ║
 ║  │  │  VC-002  Sem domain match    ──► VETO (add taxonomy antes)  │   │  ║
 ║  │  │  VC-003  Hierarquia circular ──► VETO (corrigir antes)      │   │  ║
 ║  │  │  VC-004  Agente generico     ──► VETO (minds first!)       │   │  ║
 ║  │  │  VC-005  Skill sem evidencia ──► VETO publicar (fica draft) │   │  ║
 ║  │  │  VC-006  Duplicata >= 0.95   ──► VETO (auto-merge)         │   │  ║
 ║  │  │  VC-007  SOW vazio           ──► VETO publicar              │   │  ║
 ║  │  │  VC-008  Dossier sem fonte   ──► VETO criar                 │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  └──────────────────────────────────────────────────────────────┘   │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  ★ MODO 5b: APEX VIABILITY SCORING (5 Dimensoes)                   │  ║
 ║  │  ════════════════════════════════════════════════                   │  ║
 ║  │  Script: viability_scorer.py                                        │  ║
 ║  │                                                                     │  ║
 ║  │  Avalia CADA PERSONA em 5 dimensoes antes de criar agente:          │  ║
 ║  │                                                                     │  ║
 ║  │  ┌──────────────────────────────────────────────────────────────┐   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  A  AVAILABILITY    (peso 1.0)  Volume de conteudo           │   │  ║
 ║  │  │  ─────────────────────────────────────────────────           │   │  ║
 ║  │  │  10h+ conteudo, 3+ tipos de fonte ........... 10 pts        │   │  ║
 ║  │  │  5-10h, 2 tipos ............................ 7 pts          │   │  ║
 ║  │  │  1-5h, 1 tipo .............................. 5 pts          │   │  ║
 ║  │  │  < 1h ....................................... 3 pts          │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  P  PERSONA CLARITY (peso 0.9)  Consistencia de voz         │   │  ║
 ║  │  │  ─────────────────────────────────────────────────           │   │  ║
 ║  │  │  Voice consistente, frameworks unicos ...... 10 pts         │   │  ║
 ║  │  │  Voice identificavel, alguns frameworks .... 7 pts          │   │  ║
 ║  │  │  Voice variavel ............................. 5 pts          │   │  ║
 ║  │  │  Sem voice distinta ......................... 3 pts          │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  E  EVOLUTION       (peso 0.8)  Cobertura temporal           │   │  ║
 ║  │  │  ─────────────────────────────────────────────────           │   │  ║
 ║  │  │  5+ anos, evolucao visivel .................. 10 pts         │   │  ║
 ║  │  │  2-5 anos ................................... 7 pts          │   │  ║
 ║  │  │  1-2 anos ................................... 5 pts          │   │  ║
 ║  │  │  < 1 ano .................................... 3 pts          │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  X  EXPERTISE       (peso 0.9)  Frameworks originais         │   │  ║
 ║  │  │  ─────────────────────────────────────────────────           │   │  ║
 ║  │  │  10+ frameworks originais ................... 10 pts         │   │  ║
 ║  │  │  5-10 frameworks ............................ 7 pts          │   │  ║
 ║  │  │  2-5 frameworks ............................. 5 pts          │   │  ║
 ║  │  │  < 2 frameworks ............................. 3 pts          │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  S  STRATEGIC FIT   (peso 0.8)  Alinhamento com dominios     │   │  ║
 ║  │  │  ─────────────────────────────────────────────────           │   │  ║
 ║  │  │  Alinhamento direto com dominios core ....... 10 pts         │   │  ║
 ║  │  │  Alinhamento parcial ........................ 7 pts          │   │  ║
 ║  │  │  Tangencial ................................. 5 pts          │   │  ║
 ║  │  │  Sem alinhamento ............................ 3 pts          │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  └──────────────────────────────────────────────────────────────┘   │  ║
 ║  │                                                                     │  ║
 ║  │  Decisao:                                                           │  ║
 ║  │  ┌──────────────────────────────────────────────────────────────┐   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  APEX >= 7.0  ──►  ✅ GO         Criar agente completo      │   │  ║
 ║  │  │  APEX 5.0-6.9 ──►  ⚠️  CONDICIONAL  Criar com ressalvas    │   │  ║
 ║  │  │  APEX < 5.0   ──►  ❌ NO-GO      Apenas tracking            │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  │  Exemplos reais:                                             │   │  ║
 ║  │  │  Alex Hormozi   APEX=8.82  ──► GO                           │   │  ║
 ║  │  │  Cole Gordon    APEX=6.36  ──► CONDICIONAL                  │   │  ║
 ║  │  │  Sam Ovens      APEX=5.91  ──► CONDICIONAL                  │   │  ║
 ║  │  │  Desconhecido X APEX=2.10  ──► NO-GO                        │   │  ║
 ║  │  │                                                              │   │  ║
 ║  │  └──────────────────────────────────────────────────────────────┘   │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  ★ MODO 5c: TOOL DISCOVERY + COMMAND LOADER                        │  ║
 ║  │  ═══════════════════════════════════════════                        │  ║
 ║  │  Script: tool_discovery.py                                          │  ║
 ║  │                                                                     │  ║
 ║  │  Para cada cargo, descobre ferramentas necessarias:                  │  ║
 ║  │                                                                     │  ║
 ║  │  ┌───────────────────────────────────────────────────────────┐      │  ║
 ║  │  │  CLOSER:                                                  │      │  ║
 ║  │  │    Essential: CRM, Calendar, Video Call                   │      │  ║
 ║  │  │    Recommended: Proposal Tool, WhatsApp Business          │      │  ║
 ║  │  │    MCP Available: hubspot-mcp, google-calendar-mcp        │      │  ║
 ║  │  │                                                           │      │  ║
 ║  │  │  BDR:                                                     │      │  ║
 ║  │  │    Essential: CRM, Dialer, Email Sequencer                │      │  ║
 ║  │  │    Recommended: LinkedIn Sales Navigator                  │      │  ║
 ║  │  │    MCP Available: hubspot-mcp, gmail-mcp                  │      │  ║
 ║  │  │                                                           │      │  ║
 ║  │  │  COPYWRITER:                                              │      │  ║
 ║  │  │    Essential: Google Docs, Reference Library              │      │  ║
 ║  │  │    Recommended: Grammarly, Headline Analyzer              │      │  ║
 ║  │  │    MCP Available: google-drive-mcp                        │      │  ║
 ║  │  └───────────────────────────────────────────────────────────┘      │  ║
 ║  │                                                                     │  ║
 ║  │  COMMAND LOADER (regra critica):                                    │  ║
 ║  │  "Ao ativar este agente, CARREGAR tasks ANTES de executar."         │  ║
 ║  │                                                                     │  ║
 ║  │  ┌───────────────────────────────────────────────────────────┐      │  ║
 ║  │  │  Agente CLOSER — Tasks Obrigatorias:                     │      │  ║
 ║  │  │                                                           │      │  ║
 ║  │  │  *execute-close    closer-call-framework.md               │      │  ║
 ║  │  │  *objection-handle closer-objections.md                   │      │  ║
 ║  │  │  *pipeline-review  closer-pipeline.md                     │      │  ║
 ║  │  └───────────────────────────────────────────────────────────┘      │  ║
 ║  │                                                                     │  ║
 ║  │  AUTONOMY LEVELS:                                                   │  ║
 ║  │  ┌───────────────────────────────────────────────────────────┐      │  ║
 ║  │  │  Level 0: Reference   (consulta apenas)                   │      │  ║
 ║  │  │  Level 1: Assisted    (IA prepara, humano executa)        │      │  ║
 ║  │  │  Level 2: Supervised  (IA executa, humano valida)         │      │  ║
 ║  │  │  Level 3: Autonomous  (IA opera, humano monitora)         │      │  ║
 ║  │  │  Level 4: Full Auto   (IA sozinha)                        │      │  ║
 ║  │  └───────────────────────────────────────────────────────────┘      │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 9. FASE 7: VALIDACAO E MANIFEST

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║           FASE 7: VALIDACAO + PIPELINE MANIFEST  [★ NOVO v4.0]           ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  REGRA #26: "So marca como completo se validacao passar."                 ║
 ║                                                                           ║
 ║  Apos todos os 5 MODOs executarem, o sistema:                             ║
 ║                                                                           ║
 ║  1. VALIDATE: Verifica integridade do cascateamento                       ║
 ║     - Destinos declarados existem fisicamente?                            ║
 ║     - Referencias estao corretas?                                         ║
 ║     - Se FALHA: NAO marca como completo, retorna com erro                 ║
 ║                                                                           ║
 ║  ★ 2. PIPELINE MANIFEST: Registra TODOS os steps                         ║
 ║     Cada batch gera um manifest com 13 steps rastreados:                  ║
 ║                                                                           ║
 ║  ┌──────────────────────────────────────────────────────────────────┐     ║
 ║  │  PIPELINE MANIFEST — BATCH-045                                   │     ║
 ║  │  ════════════════════════════════                                │     ║
 ║  │                                                                  │     ║
 ║  │  Step                    Status     Resultado                    │     ║
 ║  │  ──────────────────────  ─────────  ───────────────────────      │     ║
 ║  │  modo1_explicit          completed  agents=2, dossiers=1         │     ║
 ║  │  modo2_inferred          completed  agents=3, dossiers=2         │     ║
 ║  │  modo3_triggers          completed  new_agents=1                 │     ║
 ║  │  merge                   completed  total=4 agents               │     ║
 ║  │  cascade                 completed  4 agents, 2 dossiers         │     ║
 ║  │  ★ modo4_business_model  completed  3 departments detected       │     ║
 ║  │  ★ modo4_sow             completed  22 SOWs generated            │     ║
 ║  │  ★ modo4_skills          completed  530 skills                   │     ║
 ║  │  ★ modo5_quality_gates   completed  4 checked, 0 blocked         │     ║
 ║  │  ★ modo5_viability       completed  50 persons scored            │     ║
 ║  │  ★ modo5_tool_discovery  completed  37 roles with tools          │     ║
 ║  │  validation              completed  PASSED                       │     ║
 ║  │  ★ review_queue          completed  17 pending items             │     ║
 ║  │  ──────────────────────  ─────────  ───────────────────────      │     ║
 ║  │  COVERAGE: 13/13 (100%)                                         │     ║
 ║  │                                                                  │     ║
 ║  └──────────────────────────────────────────────────────────────────┘     ║
 ║                                                                           ║
 ║  Se qualquer step falhar ou for pulado, o manifest registra:              ║
 ║  "ATENCAO: 2 steps pulados" no feedback do hook.                          ║
 ║                                                                           ║
 ║  Gravado em: logs/pipeline_manifests.jsonl                                ║
 ║  (Auditavel. Apos 50 batches, basta ler o log.)                          ║
 ║                                                                           ║
 ║  3. MARK: Adiciona secao "Cascateamento Executado" ao batch               ║
 ║     Batch fica marcado como processado. Nao roda de novo.                 ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. HUMAN CHECKPOINTS E REVIEW QUEUE

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║       HUMAN CHECKPOINTS & REVIEW QUEUE  [★ NOVO v4.0]                    ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  Script: review_dashboard.py                                              ║
 ║  "Nem tudo deve ser automatico. Humano decide nos pontos criticos."       ║
 ║                                                                           ║
 ║  4 CHECKPOINTS:                                                           ║
 ║                                                                           ║
 ║  ┌─────────────────────────────────────────────────────────────────────┐  ║
 ║  │                                                                     │  ║
 ║  │  HC-1: AGENT CREATION APPROVAL                                      │  ║
 ║  │  ══════════════════════════════                                     │  ║
 ║  │  Trigger: Role com ws >= 10, pronto pra virar agente               │  ║
 ║  │  Pergunta: "Este cargo deve virar agente?"                          │  ║
 ║  │  Opcoes: [Aprovar] [Rejeitar] [Adiar]                              │  ║
 ║  │  Contexto mostrado: SOW, weighted_score, sources, executor_type     │  ║
 ║  │                                                                     │  ║
 ║  │  Exemplo: COPYWRITER (ws=11.9, 2 sources, executor=Agent)          │  ║
 ║  │           ──► Humano decide se cria o agente ou espera mais dados   │  ║
 ║  │                                                                     │  ║
 ║  │  ─────────────────────────────────────────────────────────          │  ║
 ║  │                                                                     │  ║
 ║  │  HC-2: BUSINESS MODEL VALIDATION                                    │  ║
 ║  │  ════════════════════════════════                                   │  ║
 ║  │  Trigger: Business model com role_chain >= 4 niveis                 │  ║
 ║  │  Pergunta: "Hierarquia organizacional correta?"                     │  ║
 ║  │  Opcoes: [Aprovar] [Editar] [Rejeitar]                             │  ║
 ║  │  Contexto: role_chain visual, evidence, consolidation               │  ║
 ║  │                                                                     │  ║
 ║  │  Exemplo: Alex Hormozi: CEO→COO→Sales Mgr→Closer (4 niveis)       │  ║
 ║  │           ──► Humano valida se a hierarquia faz sentido             │  ║
 ║  │                                                                     │  ║
 ║  │  ─────────────────────────────────────────────────────────          │  ║
 ║  │                                                                     │  ║
 ║  │  HC-3: SKILLS REVIEW                                                │  ║
 ║  │  ════════════════════                                               │  ║
 ║  │  Trigger: >= 5 skills geradas para um persona                       │  ║
 ║  │  Pergunta: "Skills refletem os frameworks reais?"                   │  ║
 ║  │  Opcoes: [Aprovar todas] [Aprovar por skill] [Rejeitar]            │  ║
 ║  │  Contexto: lista de skills, quotes originais, nomes dos frameworks  │  ║
 ║  │                                                                     │  ║
 ║  │  Exemplo: Alex Hormozi com 262 skills geradas                      │  ║
 ║  │           ──► Humano revisa se as skills fazem sentido              │  ║
 ║  │                                                                     │  ║
 ║  │  ─────────────────────────────────────────────────────────          │  ║
 ║  │                                                                     │  ║
 ║  │  HC-4: ENTITY MERGE REVIEW                                          │  ║
 ║  │  ══════════════════════════                                         │  ║
 ║  │  Trigger: Entidades na review_queue com fuzzy match                 │  ║
 ║  │  Pergunta: "Sao a mesma entidade?"                                  │  ║
 ║  │  Opcoes: [Merge] [Manter separado]                                  │  ║
 ║  │  Contexto: nomes, similarity score, tipo de entidade                │  ║
 ║  │                                                                     │  ║
 ║  │  Exemplo: "Sam oven" (score 0.92) <-> "Sam Ovens"                  │  ║
 ║  │           ──► Humano confirma se e a mesma pessoa                   │  ║
 ║  │                                                                     │  ║
 ║  └─────────────────────────────────────────────────────────────────────┘  ║
 ║                                                                           ║
 ║  Dashboard CLI:                                                           ║
 ║  ┌──────────────────────────────────────────────────────────────────┐     ║
 ║  │  $ python3 scripts/review_dashboard.py                           │     ║
 ║  │                                                                  │     ║
 ║  │  ══════════════════════════════════════════                       │     ║
 ║  │    MEGA BRAIN - REVIEW DASHBOARD                                 │     ║
 ║  │    2026-02-26 12:00:00                                           │     ║
 ║  │    Total pending: 17                                             │     ║
 ║  │  ══════════════════════════════════════════                       │     ║
 ║  │                                                                  │     ║
 ║  │    AGENTS PENDENTES (HC-1): 10                                   │     ║
 ║  │    ──────────────────────────────                                │     ║
 ║  │    [1] CLOSER         ws=21.6  src=3  exec=Hybrid    SOW         │     ║
 ║  │    [2] BDR            ws=14.2  src=2  exec=Hybrid    SOW         │     ║
 ║  │    [3] COPYWRITER     ws=11.9  src=2  exec=Agent     SOW         │     ║
 ║  │    ...                                                           │     ║
 ║  │                                                                  │     ║
 ║  │    SKILLS PENDENTES (HC-3): 3                                    │     ║
 ║  │    ──────────────────────────────                                │     ║
 ║  │    [11] alex-hormozi    262 skills geradas                       │     ║
 ║  │    [12] cole-gordon     251 skills geradas                       │     ║
 ║  │    ...                                                           │     ║
 ║  │                                                                  │     ║
 ║  │    MERGES PENDENTES (HC-4): 4                                    │     ║
 ║  │    ──────────────────────────────                                │     ║
 ║  │    [14] "Sam oven" <-> "Sam Ovens" (score: 0.92)                │     ║
 ║  │    ...                                                           │     ║
 ║  │                                                                  │     ║
 ║  └──────────────────────────────────────────────────────────────────┘     ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 11. MAPA COMPLETO DE SCRIPTS

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                    INVENTARIO DE SCRIPTS                                  ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  scripts/                                                                 ║
 ║  ├── FUNDACAO (Sprints 1-3, ja existiam)                                 ║
 ║  │   ├── entity_normalizer.py ···· Canonicaliza entidades (fuzzy match)  ║
 ║  │   ├── role_detector.py ········ Detecta cargos em 3 niveis            ║
 ║  │   ├── theme_analyzer.py ······· Extrai temas multi-formato            ║
 ║  │   ├── bootstrap_registry.py ··· Popula registry inicial               ║
 ║  │   ├── dossier_trigger.py ······ Avalia thresholds de dossiers         ║
 ║  │   ├── agent_trigger.py ········ Triggers tiered de agentes (3 tiers)  ║
 ║  │   └── org_chain_detector.py ··· Hierarquia e KPIs                     ║
 ║  │                                                                       ║
 ║  ├── CONFIGURACAO                                                        ║
 ║  │   ├── trigger_config.yaml ····· Thresholds + pesos + KPIs            ║
 ║  │   ├── _ROLE_PATTERNS.yaml ····· 33+ cargos com regex PT-BR + EN      ║
 ║  │   └── ★ quality_gates.yaml ···· 6 gates + 8 vetos  [NOVO v4.0]      ║
 ║  │                                                                       ║
 ║  └── ★ INTELLIGENCE LAYER v4.0 (Sprints 5-10) [TODOS NOVOS]            ║
 ║      ├── ★ business_model_detector.py · Detecta org/hierarquia/revenue  ║
 ║      ├── ★ sow_generator.py ··········· SOW dual-purpose + Executor DT  ║
 ║      ├── ★ skill_generator.py ·········· Framework DNA → SKILL.md       ║
 ║      ├── ★ viability_scorer.py ········· APEX 5D scoring + quality check║
 ║      ├── ★ tool_discovery.py ··········· Tools por cargo + Command Load ║
 ║      └── ★ review_dashboard.py ········· 4 Human Checkpoints + CLI      ║
 ║                                                                           ║
 ║  TOTAL: 16 scripts + 3 configs = 19 arquivos                             ║
 ║  ★ = Novo na v4.0 (7 scripts + 1 config = 8 novos)                      ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 12. MAPA COMPLETO DE HOOKS

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                    INVENTARIO DE HOOKS (.claude/hooks/)                   ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  CICLO DE SESSAO                                                          ║
 ║  ├── session_start.py ········ Carrega personalidade, DNA, briefing      ║
 ║  ├── session_autosave_v2.py ·· Auto-save a cada 30min (REGRA #11)       ║
 ║  ├── session_end.py ·········· Cleanup + save final                      ║
 ║  └── session-source-sync.py ·· Sync source files                         ║
 ║                                                                           ║
 ║  VALIDACAO & QUALIDADE                                                    ║
 ║  ├── creation_validator.py ··· Valida antes de criar (REGRA #22)         ║
 ║  ├── claude_md_guard.py ······ Protege estrutura CLAUDE.md               ║
 ║  ├── quality_watchdog.py ····· Monitora violacoes de regras              ║
 ║  └── stop_hook_completeness.py Verifica @stop hook                       ║
 ║                                                                           ║
 ║  GESTAO DE CONHECIMENTO                                                   ║
 ║  ├── continuous_save.py ······ Persistencia de sessao                     ║
 ║  ├── memory_hints_injector.py  Injeta snippets de memoria                ║
 ║  ├── memory_updater.py ······· Atualiza JARVIS-MEMORY                    ║
 ║  ├── ledger_updater.py ······· Registra acoes no ACTION-LEDGER           ║
 ║  └── agent_memory_persister.py Persiste estado interno do agente         ║
 ║                                                                           ║
 ║  EXECUCAO & CONTROLE                                                      ║
 ║  ├── skill_router.py ········· Roteia prompt para skill correta          ║
 ║  ├── skill_indexer.py ········· Indexa skills disponiveis                 ║
 ║  ├── enforce_plan_mode.py ···· Exige plano antes de executar             ║
 ║  └── enforce_dual_location.py  Arquivo em 2 locais (REGRA #19)          ║
 ║                                                                           ║
 ║  MONITORAMENTO & ALERTAS                                                  ║
 ║  ├── inbox_age_alert.py ······ Alerta inbox items antigos                ║
 ║  ├── pending_tracker.py ······ Reporta tarefas pendentes                 ║
 ║  ├── notification_system.py ·· Envia notificacoes                        ║
 ║  └── ralph_wiggum.py ········· Humor + insights aleatorios               ║
 ║                                                                           ║
 ║  PIPELINE (O CORACAO)                                                     ║
 ║  ├── ★ post_batch_cascading.py  ORQUESTRADOR v4.0 (5 MODOs, 2441 ln)   ║
 ║  ├── post_tool_use.py ········· Cleanup pos-execucao                     ║
 ║  └── user_prompt_submit.py ···· Validacao pre-execucao                   ║
 ║                                                                           ║
 ║  TOTAL: 24 hooks                                                          ║
 ║  ★ = Atualizado na v4.0                                                  ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 13. TODOS OS THRESHOLDS E GATILHOS

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                 TABELA MESTRA DE THRESHOLDS                              ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  CRIACAO DE DOSSIER                                                       ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Occurrences >= 15   (tema aparece 15+ vezes)              │           ║
 ║  │  Sources >= 2        (em 2+ fontes distintas)              │           ║
 ║  │  Frameworks >= 2     (2+ frameworks associados)            │           ║
 ║  │  Relevance >= 25.0   (score composto)                      │           ║
 ║  │  NAO alias           (canonicalizacao)                      │           ║
 ║  │  Domain match        (no DOMAINS-TAXONOMY)                  │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  ATUALIZACAO DE DOSSIER                                                   ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Stale >= 30 dias    (dossier nao atualizado em 30+ dias)  │           ║
 ║  │  New elements >= 5   (5+ novos insights disponiveis)       │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  CRIACAO DE AGENTE (3 TIERS)                                              ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  ESTABLISHED: ws >= 10 E sources >= 2  ──► CRIAR          │           ║
 ║  │  EMERGING:    ws >= 5  E sources >= 1  ──► MONITORAR      │           ║
 ║  │  EMERGENT:    ws >= 3  E sources >= 1  ──► OBSERVAR       │           ║
 ║  │                                                            │           ║
 ║  │  Promocao: ws >= 15 E sources >= 2 ──► Sobe de tier       │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  ★ VIABILITY SCORING (APEX)                  [NOVO v4.0]                 ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  APEX >= 7.0  ──► GO (criar agente completo)              │           ║
 ║  │  APEX 5.0-6.9 ──► CONDICIONAL (criar com ressalvas)       │           ║
 ║  │  APEX < 5.0   ──► NO-GO (apenas tracking)                 │           ║
 ║  │  AUTO-REJECTION: < 5.0 ──► tracking automatico             │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  CANONICALIZACAO (Fuzzy Match)                                            ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Score >= 0.95  ──► Auto-merge (VETO VC-006)              │           ║
 ║  │  Score >= 0.85  ──► Review queue (merge manual)            │           ║
 ║  │  Score < 0.85   ──► Entidade nova                          │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  PESOS DE DETECCAO                                                        ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Role Direto:      1.0x   ("The closer handles...")        │           ║
 ║  │  Role Inferido:    0.7x   ("handles objections" → CLOSER)  │           ║
 ║  │  Role Emergente:   0.5x   ("hired a copywriter" → novo)    │           ║
 ║  │                                                            │           ║
 ║  │  Dossier cross_source:   3.0   (bonus por fonte extra)     │           ║
 ║  │  Dossier framework:      2.0   (bonus por framework)       │           ║
 ║  │  Dossier methodology:    2.0   (bonus por metodologia)     │           ║
 ║  │  Dossier heuristic:      1.5   (bonus por heuristica)      │           ║
 ║  │  Dossier philosophy:     1.0   (bonus por filosofia)       │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  ★ HUMAN CHECKPOINTS                        [NOVO v4.0]                  ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  HC-1: ws >= 10 + pronto pra agente  ──► Humano aprova    │           ║
 ║  │  HC-2: role_chain >= 4 niveis        ──► Humano valida    │           ║
 ║  │  HC-3: skills >= 5 por persona       ──► Humano revisa    │           ║
 ║  │  HC-4: entidades no review_queue     ──► Humano decide    │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 14. ESTRUTURA DE DIRETORIOS

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                    ARVORE DO PROJETO                                      ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  mega-brain/                                                              ║
 ║  │                                                                       ║
 ║  ├── .claude/                                                            ║
 ║  │   └── hooks/                    24 hooks (ciclo de vida da sessao)     ║
 ║  │       └── ★ post_batch_cascading.py   ORQUESTRADOR v4.0              ║
 ║  │                                                                       ║
 ║  ├── scripts/                      19 arquivos (Intelligence Layer)       ║
 ║  │   ├── entity_normalizer.py      Fundacao: canonicalizacao              ║
 ║  │   ├── role_detector.py          Fundacao: deteccao 3 niveis           ║
 ║  │   ├── theme_analyzer.py         Fundacao: extracao multi-formato      ║
 ║  │   ├── agent_trigger.py          Fundacao: triggers tiered             ║
 ║  │   ├── dossier_trigger.py        Fundacao: triggers de dossier         ║
 ║  │   ├── org_chain_detector.py     Fundacao: hierarquia                  ║
 ║  │   ├── bootstrap_registry.py     Fundacao: populacao inicial           ║
 ║  │   ├── ★ business_model_detector.py  [NOVO] Detecta org/revenue       ║
 ║  │   ├── ★ sow_generator.py           [NOVO] SOW dual-purpose           ║
 ║  │   ├── ★ skill_generator.py          [NOVO] Framework → Skill         ║
 ║  │   ├── ★ viability_scorer.py         [NOVO] APEX 5D scoring           ║
 ║  │   ├── ★ tool_discovery.py           [NOVO] Tools + Command Loader    ║
 ║  │   ├── ★ review_dashboard.py         [NOVO] Human Checkpoints         ║
 ║  │   ├── trigger_config.yaml       Config de thresholds + KPIs          ║
 ║  │   ├── _ROLE_PATTERNS.yaml       33+ cargos com regex                 ║
 ║  │   └── ★ quality_gates.yaml      [NOVO] 6 gates + 8 vetos            ║
 ║  │                                                                       ║
 ║  ├── processing/                   Pipeline de dados                     ║
 ║  │   ├── chunks/                   96 chunks semanticos (JSON)           ║
 ║  │   ├── insights/                 8 insights curados                    ║
 ║  │   ├── canonical/                                                      ║
 ║  │   │   ├── ENTITY-REGISTRY.json  ★ v16, 734 entidades (SSOT)         ║
 ║  │   │   └── review_queue.jsonl    ★ Fila de merge manual [NOVO]       ║
 ║  │   ├── dna/                      DNA narrativas por persona            ║
 ║  │   └── narratives/               Narrativas consolidadas              ║
 ║  │                                                                       ║
 ║  ├── knowledge/                    Base de conhecimento                   ║
 ║  │   ├── dna/                                                            ║
 ║  │   │   ├── DOMAINS-TAXONOMY.yaml 19 dominios (atualizado v2.0)        ║
 ║  │   │   ├── ★ _dna-skills-registry.yaml  [NOVO] Inventario skills     ║
 ║  │   │   ├── ★ skills/            [NOVO] 530 SKILL.md gerados          ║
 ║  │   │   │   ├── alex-hormozi/    262 skills                            ║
 ║  │   │   │   ├── cole-gordon/     (via persona)                         ║
 ║  │   │   │   └── .../                                                   ║
 ║  │   │   ├── aggregated/          Conhecimento consolidado              ║
 ║  │   │   ├── maps/                Mapeamentos                           ║
 ║  │   │   └── persons/             DNA por persona                       ║
 ║  │   ├── dossiers/                Dossiers tematicos                    ║
 ║  │   │   ├── themes/              Temas (vendas, objecoes, etc.)        ║
 ║  │   │   ├── persons/             Dossiers por pessoa                   ║
 ║  │   │   └── system/              Dossiers de sistema                   ║
 ║  │   └── playbooks/               37 playbooks operacionais             ║
 ║  │                                                                       ║
 ║  ├── agents/                       Agentes inteligentes                  ║
 ║  │   ├── cargo/                    Agentes de cargo                     ║
 ║  │   │   ├── sales/               CLOSER, BDR, SDS, SETTER, LNS...     ║
 ║  │   │   │   └── closer/                                                ║
 ║  │   │   │       ├── AGENT.md                                           ║
 ║  │   │   │       ├── ★ SOW.md     [NOVO] Statement of Work             ║
 ║  │   │   │       └── ★ SOW.json   [NOVO] Config do agente              ║
 ║  │   │   ├── c-level/             CRO, CFO, CMO, COO                    ║
 ║  │   │   ├── marketing/           Agentes de marketing                  ║
 ║  │   │   └── design/              Designer                              ║
 ║  │   ├── persons/                  Mind-clones (Cole Gordon, etc.)       ║
 ║  │   ├── council/                  Conclave multi-agente                 ║
 ║  │   └── protocols/                Protocolos operacionais              ║
 ║  │                                                                       ║
 ║  └── logs/                         Rastreabilidade                       ║
 ║      ├── cascading.jsonl           Log de cascateamento                  ║
 ║      ├── ★ pipeline_manifests.jsonl [NOVO] Manifests por batch          ║
 ║      ├── ★ sow_generation.jsonl    [NOVO] Log de SOWs gerados          ║
 ║      ├── ★ viability_scoring.jsonl [NOVO] Log de scores APEX           ║
 ║      └── .../                      Outros logs operacionais             ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

## 15. KPIs DE SUCESSO

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                    KPIs DE SUCESSO DA PIPELINE                           ║
 ╠═══════════════════════════════════════════════════════════════════════════╣
 ║                                                                           ║
 ║  DETECCAO                                                                 ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Roles detectados:          Target: 33+ (antes: 18)       │           ║
 ║  │  Dominios cobertos:         Target: 7+  (antes: 1)        │           ║
 ║  │  Precisao de inferencia:    Target: > 80%                  │           ║
 ║  │  Roles emergentes:          Target: 5 por 100 batches      │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  TRIGGERS                                                                 ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Novos dossiers / 100 batches:    Target: 3-5              │           ║
 ║  │  Novos agentes / 100 batches:     Target: 1-2              │           ║
 ║  │  Taxa de falso positivo:          Target: < 10%            │           ║
 ║  │  Latencia do trigger:             Target: < 30 segundos    │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  REGISTRY                                                                 ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Taxa de deduplicacao:            Target: > 95%            │           ║
 ║  │  Entidades orfas (sem fonte):     Target: < 5%             │           ║
 ║  │  Cobertura weighted_score:        Target: 100%             │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  ★ QUALIDADE                                [NOVO v4.0]                   ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Dossier min frameworks:          Target: >= 2             │           ║
 ║  │  Agente min responsibilities:     Target: >= 3             │           ║
 ║  │  Role chain max depth:            Target: <= 6             │           ║
 ║  │  Skills com workflow 3+ steps:    Target: 100%             │           ║
 ║  │  Pipeline manifest coverage:      Target: 13/13 (100%)    │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ║  BASELINES (melhoria mensuravel)                                          ║
 ║  ┌────────────────────────────────────────────────────────────┐           ║
 ║  │  Roles pre-v2: 18         ──►  Pos-v4: 236               │           ║
 ║  │  Dominios pre-v2: 1       ──►  Pos-v4: 19                │           ║
 ║  │  SOWs pre-v4: 0           ──►  Pos-v4: 44                │           ║
 ║  │  Skills pre-v4: 0         ──►  Pos-v4: 530               │           ║
 ║  │  Quality gates pre-v4: 0  ──►  Pos-v4: 6 gates + 8 vetos│           ║
 ║  │  Human checkpoints: 0     ──►  Pos-v4: 4 checkpoints     │           ║
 ║  │  Pipeline manifest: nao   ──►  Pos-v4: 13 steps tracked  │           ║
 ║  └────────────────────────────────────────────────────────────┘           ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```

---

```
 ╔═════════════════════════════════════════════════════════════════════════════╗
 ║                                                                           ║
 ║                         FIM DO DOCUMENTO                                  ║
 ║                                                                           ║
 ║  ★ = Implementado na v4.0 (esta sessao)                                  ║
 ║                                                                           ║
 ║  Este documento cobre a maquina completa do Mega Brain:                   ║
 ║  - 5 MODOs de processamento (3 existentes + 2 novos)                     ║
 ║  - 19 scripts de Intelligence Layer (7 existentes + 8 novos + 4 configs) ║
 ║  - 24 hooks de ciclo de vida                                             ║
 ║  - 6 quality gates + 8 veto conditions                                   ║
 ║  - 5 dimensoes APEX de viability scoring                                 ║
 ║  - 4 human checkpoints com review dashboard                              ║
 ║  - 13 steps rastreados no pipeline manifest                              ║
 ║  - 734 entidades no ENTITY-REGISTRY (50 persons, 236 roles, 448 themes) ║
 ║  - 530 skills geradas, 44 SOWs dual-purpose                             ║
 ║                                                                           ║
 ║  Para executar o review dashboard:                                        ║
 ║  $ python3 scripts/review_dashboard.py                                    ║
 ║                                                                           ║
 ║  Para ver o manifest do ultimo batch:                                     ║
 ║  $ tail -1 logs/pipeline_manifests.jsonl | python3 -m json.tool           ║
 ║                                                                           ║
 ║  Mega Brain Intelligence Layer v4.0                                       ║
 ║  Documentado por JARVIS (Chronicler) — 2026-02-26                        ║
 ║                                                                           ║
 ╚═════════════════════════════════════════════════════════════════════════════╝
```
