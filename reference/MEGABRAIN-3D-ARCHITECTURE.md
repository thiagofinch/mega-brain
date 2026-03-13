# Mega Brain 3D — Architecture

> **Version:** 2.0.0 | **Date:** 2026-03-13
> **Source of Truth:** `core/paths.py` (76+ routing keys)
> **Directory Contract:** `.claude/rules/directory-contract.md` (v3.0.0)
> **ROUTING key:** `ROUTING["architecture_doc"]`

---

## 1. Visao Geral — O Modelo Mental

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                          M E G A   B R A I N   3 D                           ║
║                                                                              ║
║   Sistema de gestao de conhecimento que transforma materiais brutos          ║
║   (videos, PDFs, transcricoes, reunioes) em agentes de IA clonados,         ║
║   playbooks acionaveis e decisoes estrategicas.                              ║
║                                                                              ║
║   Analogia: O cerebro da empresa.                                            ║
║     - Bucket 1 (External) = Livros que voce leu (conhecimento de fora)       ║
║     - Bucket 2 (Business) = Diario da empresa (o que aconteceu)              ║
║     - Bucket 3 (Personal) = Seus pensamentos privados                        ║
║     - Workspace            = Manual da empresa (como as coisas DEVEM ser)    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Arquitetura em 4 Camadas

```
                          ┌──────────────────────────┐
                          │      MEGA BRAIN ROOT     │
                          └────────────┬─────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
   ╔═══════════════════╗    ╔═══════════════════╗    ╔═══════════════════╗
   ║    knowledge/     ║    ║    workspace/     ║    ║     agents/      ║
   ║  (DESCRITIVO)     ║    ║  (PRESCRITIVO)    ║    ║   (EXECUTORES)   ║
   ║                   ║    ║                   ║    ║                   ║
   ║ O que ACONTECEU   ║    ║ Como DEVE ser     ║    ║ Quem EXECUTA     ║
   ║ Dados, fatos,     ║    ║ SOPs, estrutura,  ║    ║ Clones mentais,  ║
   ║ transcricoes      ║    ║ estrategia        ║    ║ cargos, sistema  ║
   ╚═══════════════════╝    ╚═══════════════════╝    ╚═══════════════════╝
            │                          │                          │
   ┌────────┼────────┐                 │              ┌───────────┼───────────┐
   │        │        │                 │              │     │     │     │     │
   ▼        ▼        ▼                 ▼              ▼     ▼     ▼     ▼     ▼
  B1       B2       B3           Operacional       ext   bus   per   cargo  sys
External Business Personal       Layer           (clones)    (founder) (hibridos)
```

---

## 3. Os 3 Buckets de Conhecimento

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   BUCKET 1: EXTERNAL (Expert Knowledge)                      ║
║                   Caminho: knowledge/external/                               ║
║                   Layer: L2 (Pro) — Git Tracked                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ENTRADA:  Cursos, podcasts, masterminds, livros                            ║
║   SAIDA:    agents/external/ (clones de especialistas)                       ║
║   RAG:      .data/rag_expert/                                                ║
║                                                                              ║
║   knowledge/external/                                                        ║
║   ├── inbox/                <- Material bruto (staging area)                 ║
║   │   └── {pessoa}/             Organizado por especialista                  ║
║   │       └── {tipo}/           transcriptions/, pdfs/, videos/              ║
║   ├── dna/                  <- DNA Cognitivo (5 camadas)                     ║
║   │   └── persons/              Um subdir por expert                         ║
║   │       ├── alex-hormozi/     FILOSOFIAS, MODELOS, HEURISTICAS,            ║
║   │       ├── cole-gordon/      FRAMEWORKS, METODOLOGIAS (.yaml)             ║
║   │       └── jeremy-miner/                                                  ║
║   ├── dossiers/             <- Dossieres consolidados                        ║
║   │   ├── persons/              DOSSIER-ALEX-HORMOZI.md                      ║
║   │   └── themes/               DOSSIER-SALES-METHODOLOGY.md                ║
║   ├── playbooks/            <- Playbooks acionaveis                          ║
║   └── sources/              <- Compilacoes por expert/tema                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                   BUCKET 2: BUSINESS (Company Operations)                    ║
║                   Caminho: knowledge/business/                               ║
║                   Layer: L3 (Personal) — Gitignored                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ENTRADA:  Reunioes, calls, docs internos, colaboracao                      ║
║   SAIDA:    agents/business/ (clones de colaboradores)                       ║
║   RAG:      .data/rag_business/                                              ║
║                                                                              ║
║   knowledge/business/                                                        ║
║   ├── inbox/                <- Material bruto (pre-processamento)            ║
║   │   └── {pessoa}/             Organizado por colaborador                   ║
║   │       └── calls/            Transcricoes de reunioes                     ║
║   ├── people/               <- DNA de colaboradores/parceiros                ║
║   ├── dossiers/             <- Dossieres de operacao/temas                   ║
║   ├── insights/             <- Insights de reunioes                          ║
║   │   ├── by-meeting/           MEET-0001.md, MEET-0002.md, ...              ║
║   │   ├── by-person/            alan-nicolas.md, ...                         ║
║   │   └── by-theme/             enterprise-strategy.md, ...                  ║
║   ├── narratives/           <- Historias conectadas entre eventos             ║
║   ├── decisions/            <- Decisoes estrategicas (entrada manual)        ║
║   └── sops/                 <- SOPs auto-detectados (RASCUNHO)               ║
║                                 Promovidos para workspace/_templates/        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                   BUCKET 3: PERSONAL (Founder Cognitive)                     ║
║                   Caminho: knowledge/personal/                               ║
║                   Layer: L3 (Personal) — Gitignored — NUNCA indexado         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ENTRADA:  Notas pessoais, mensagens, emails, reflexoes                     ║
║   SAIDA:    agents/personal/ (clone do founder)                              ║
║   RAG:      NUNCA indexado (privacidade absoluta)                            ║
║                                                                              ║
║   knowledge/personal/                                                        ║
║   ├── inbox/                <- Material bruto pessoal                        ║
║   ├── calls/                <- Transcricoes de calls pessoais                ║
║   ├── messages/             <- WhatsApp, Slack exports                       ║
║   ├── email/                <- Email digests                                 ║
║   └── cognitive/            <- Modelos mentais, reflexoes, diario            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Workspace — A Camada Prescritiva

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WORKSPACE (Prescriptive Operations Layer)                  ║
║                    Caminho: workspace/                                        ║
║                    Layer: L1 template, L2 quando populado                     ║
║                    NAO e um bucket. E o MANUAL da empresa.                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   workspace/                                                                 ║
║   ├── workspace.yaml        <- Manifesto (identidade do workspace)           ║
║   ├── structure.yaml        <- Definicao de organograma                      ║
║   ├── relationships.yaml    <- Mapa de relacionamentos                       ║
║   ├── businesses/           <- Subdirs por marca/negocio                     ║
║   │   └── {brand}/              acme-edu/, acme-ai/, etc.                    ║
║   ├── domains/              <- Regras cross-cutting (vendas, mkt, ops)       ║
║   ├── _templates/           <- SOPs VALIDADOS (promovidos do business)       ║
║   ├── providers/            <- Adaptadores de ferramentas                    ║
║   ├── config/               <- Configuracao global                           ║
║   ├── _ref/                 <- Fundacoes de referencia                       ║
║   ├── team/                 <- SOW, TAS, scorecards                          ║
║   ├── strategy/             <- Documentos estrategicos                       ║
║   ├── events/               <- Eventos de negocio                            ║
║   ├── meetings/             <- Dossieres de reunioes                         ║
║   ├── org/                  <- Estrutura organizacional                      ║
║   ├── finance/              <- DRE, KPIs, cash flow                          ║
║   ├── automations/          <- Configs de ferramentas                        ║
║   ├── tools/                <- Log de ferramentas detectadas                 ║
║   └── inbox/                <- Triagem (backward compat)                     ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   DIFERENCA CRITICA:                                                         ║
║                                                                              ║
║   ┌─────────────────────────┐    ┌──────────────────────────┐                ║
║   │ knowledge/business/     │    │ workspace/               │                ║
║   │                         │    │                          │                ║
║   │ DESCRITIVO              │    │ PRESCRITIVO              │                ║
║   │ "O que aconteceu"       │    │ "Como deve ser"          │                ║
║   │                         │    │                          │                ║
║   │ Diario da empresa       │    │ Manual da empresa        │                ║
║   │ Pipeline automatico     │    │ Atualizacao deliberada   │                ║
║   │ Gitignored (L3)         │    │ Tracked (L1/L2)          │                ║
║   └─────────────────────────┘    └──────────────────────────┘                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Agentes — Os Executores

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                       5 CATEGORIAS DE AGENTES                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   agents/                                                                    ║
║   │                                                                          ║
║   ├── external/         CLONES DE ESPECIALISTAS                              ║
║   │   ├── alex-hormozi/     Alimentado por: knowledge/external/              ║
║   │   ├── cole-gordon/      DNA Weight: 1.0 (fonte unica)                    ║
║   │   ├── jeremy-miner/     Voz: do proprio expert                           ║
║   │   └── ...               Arquivos: AGENT.md, SOUL.md, MEMORY.md,          ║
║   │                                   DNA-CONFIG.yaml                        ║
║   │                                                                          ║
║   ├── business/         CLONES DE COLABORADORES                              ║
║   │   └── {pessoa}/         Alimentado por: knowledge/business/              ║
║   │                         DNA Weight: 1.0 (fonte unica)                    ║
║   │                         Voz: do colaborador                              ║
║   │                                                                          ║
║   ├── personal/         CLONE DO FOUNDER                                     ║
║   │   └── {founder}/        Alimentado por: knowledge/personal/ + ALL        ║
║   │                         DNA Weight: 1.0 (founder)                        ║
║   │                         Voz: do founder                                  ║
║   │                         Layer: L3 (gitignored)                           ║
║   │                                                                          ║
║   ├── cargo/            PAPEIS FUNCIONAIS (HIBRIDOS)                         ║
║   │   ├── c-level/          CFO, CRO, CMO, COO                               ║
║   │   ├── sales/            Closer, SDR, BDR, Sales Manager                  ║
║   │   ├── marketing/        Copywriter, Media Buyer                          ║
║   │   └── operations/       Ops Manager                                      ║
║   │                         Alimentado por: MULTIPLOS buckets                ║
║   │                         DNA Weight: 0.0-1.0 (ponderado)                  ║
║   │                         Voz: hibrida, apropriada ao cargo                ║
║   │                                                                          ║
║   ├── system/           INFRAESTRUTURA                                       ║
║   │   ├── conclave/         Debate multi-agente                              ║
║   │   ├── boardroom/        Sala de decisao                                  ║
║   │   ├── knowledge-ops/    Squad: classificacao, extracao, curadoria         ║
║   │   └── dev-ops/          Squad: build, test, deploy                       ║
║   │                                                                          ║
║   ├── sua-empresa/      OUTPUTS ORGANIZACIONAIS                              ║
║   │   └── sow/              Statements of Work gerados                       ║
║   │                                                                          ║
║   ├── _templates/       TEMPLATES DE CRIACAO                                 ║
║   │   └── TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md                             ║
║   │                                                                          ║
║   └── constitution/     GOVERNANCA DE AGENTES                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Mecanismo de Cascateamento — Fluxo Completo

Este e o coracao do sistema. Mostra como dados brutos viram agentes inteligentes.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              PIPELINE DE CASCATEAMENTO: MATERIAL BRUTO → AGENTE              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        MATERIAL CHEGA                                   │
  │   (video, PDF, transcricao, reuniao, email, nota pessoal)              │
  └────────────────────────────┬────────────────────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                   CLASSIFICACAO AUTOMATICA                              │
  │                   scope_classifier.py                                   │
  │                                                                         │
  │   "De quem e esse material? Qual o escopo?"                            │
  │                                                                         │
  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
  │   │ Curso do Hormozi │  │ Reuniao com time │  │ Nota no WhatsApp│       │
  │   │ Score: 0.95      │  │ Score: 0.79      │  │ Score: 0.88     │       │
  │   │ → EXTERNAL       │  │ → BUSINESS       │  │ → PERSONAL      │       │
  │   └─────────────────┘  └─────────────────┘  └─────────────────┘       │
  │                                                                         │
  │   Criterios:                                                            │
  │   • Expert reconhecido (DNA existente)?    → EXTERNAL                   │
  │   • Colaborador/parceiro da empresa?       → BUSINESS                   │
  │   • Conteudo pessoal do founder?           → PERSONAL                   │
  │   • Nao sabe?                              → workspace/inbox/ (triagem) │
  └────────────────────────────┬────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
  ╔═══════════════╗  ╔═══════════════╗  ╔═══════════════╗
  ║   EXTERNAL    ║  ║   BUSINESS    ║  ║   PERSONAL    ║
  ║   PIPELINE    ║  ║   PIPELINE    ║  ║   PIPELINE    ║
  ╚═══════╤═══════╝  ╚═══════╤═══════╝  ╚═══════╤═══════╝
          │                  │                  │
          ▼                  ▼                  ▼
```

### 6.1 Pipeline EXTERNAL (5 Fases JARVIS)

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                    EXTERNAL PIPELINE (5 Fases)                          │
  │                    Material de ESPECIALISTAS                            │
  └─────────────────────────────────────────────────────────────────────────┘

  FASE 1          FASE 2          FASE 3          FASE 4          FASE 5
  Download        Organizacao     De-Para         Pipeline        Agentes
  ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐
  │ Baixar │ ──► │Organi-│ ──► │Validar│ ──► │Extrair│ ──► │ Criar │
  │ do     │      │ zar no│      │planilha│      │DNA em │      │agentes│
  │ Drive  │      │ inbox │      │vs local│      │batches│      │  AI   │
  └───────┘      └───────┘      └───────┘      └───────┘      └───────┘
                                                    │
                                        ┌───────────┼───────────┐
                                        │           │           │
                                        ▼           ▼           ▼
                                   ┌────────┐ ┌────────┐ ┌────────┐
                                   │  DNA   │ │DOSSIER │ │PLAYBOOK│
                                   │5 layers│ │person +│ │ acao   │
                                   │ .yaml  │ │ theme  │ │ direta │
                                   └───┬────┘ └───┬────┘ └───┬────┘
                                       │          │          │
                                       └────┬─────┘          │
                                            │                │
                                            ▼                │
                            ┌──────────────────────────────┐ │
                            │    agents/external/{pessoa}/ │ │
                            │                              │ │
                            │  AGENT.md  ← Template V3     │◄┘
                            │  SOUL.md   ← Identidade/Voz  │
                            │  MEMORY.md ← Insights        │
                            │  DNA-CONFIG.yaml ← Fontes    │
                            └──────────────────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │   .data/rag_expert/      │
                              │   BM25 + Vectors + Graph  │
                              └──────────────────────────┘
```

### 6.2 Pipeline BUSINESS (Reunioes/Calls)

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                    BUSINESS PIPELINE                                    │
  │          Reunioes, calls, documentos internos                          │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Fireflies   │     │   Read.ai    │     │   Manual     │
  │  (auto-poll) │     │  (webhook)   │     │  (upload)    │
  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │  knowledge/business/inbox/   │
              │  {pessoa}/calls/MEET-XXXX    │
              └──────────────┬───────────────┘
                             │
                    ┌────────┼────────┐
                    │        │        │
                    ▼        ▼        ▼
              ┌────────┐┌────────┐┌────────┐
              │INSIGHTS││DOSSIER ││ PEOPLE │
              │by-meet ││empresa ││  DNA   │
              │by-person│        ││clones  │
              │by-theme│        ││        │
              └───┬────┘└───┬────┘└───┬────┘
                  │         │         │
                  │         │         ▼
                  │         │   ┌───────────────────────┐
                  │         │   │ agents/business/      │
                  │         │   │ {colaborador}/        │
                  │         │   │ AGENT + SOUL + MEMORY │
                  │         │   └───────────────────────┘
                  │         │
                  ▼         ▼
            ┌───────────────────────────────┐
            │    .data/rag_business/        │
            │    Indexado separadamente     │
            └───────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  CASCATEAMENTO ESPECIAL: SOP PROMOTION                                 │
  │                                                                         │
  │  Quando o pipeline detecta um PROCESSO REPETITIVO em reunioes:         │
  │                                                                         │
  │  knowledge/business/sops/    ──── RASCUNHO (auto-detectado)            │
  │          │                                                              │
  │          ▼  [revisao humana + validacao]                                │
  │          │                                                              │
  │  workspace/_templates/       ──── OFICIAL (promovido)                  │
  │                                                                         │
  │  Analogia: Anotacao no diario → Regra no manual da empresa             │
  └─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Pipeline PERSONAL

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                    PERSONAL PIPELINE                                    │
  │          Notas, mensagens, emails, reflexoes do founder                │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ WhatsApp │  │  Email   │  │  Notas   │  │ Calls    │
  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │              │             │              │
       └──────────────┼─────────────┼──────────────┘
                      │             │
                      ▼             ▼
         ┌──────────────────────────────────────┐
         │     knowledge/personal/inbox/        │
         └──────────────────┬───────────────────┘
                            │
                   ┌────────┼────────┐
                   │        │        │
                   ▼        ▼        ▼
             ┌────────┐┌────────┐┌────────┐
             │messages││ email  ││cogniti-│
             │  .md   ││  .md   ││ ve.md  │
             └────────┘└────────┘└────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │  agents/personal/        │
              │  {founder}/              │
              │  Clone cognitivo         │
              │  NUNCA indexado no RAG   │
              └──────────────────────────┘
```

---

## 7. Arvore de Decisao — "Onde Vai Esse Arquivo?"

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              DECISION TREE: ROTEAMENTO DE MATERIAL                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

  O arquivo e BRUTO (nao processado)?
  │
  ├── SIM ────────────────────────────────────────────────────────────────────
  │   │
  │   │   De quem e?
  │   │
  │   ├── Especialista externo ──────────► knowledge/external/inbox/
  │   │   (Hormozi, Miner, Haynes...)       {pessoa}/{tipo}/
  │   │
  │   ├── Colaborador / Parceiro ────────► knowledge/business/inbox/
  │   │   (time interno, reunioes)          {pessoa}/calls/
  │   │
  │   ├── Conteudo pessoal ──────────────► knowledge/personal/inbox/
  │   │   (notas, emails, WhatsApp)
  │   │
  │   └── Nao sei ──────────────────────► workspace/inbox/
  │       (triagem posterior)                (fallback)
  │
  └── NAO (ja processado) ───────────────────────────────────────────────────
      │
      │   Que tipo de output?
      │
      ├── DNA schema (5 camadas) ────────► knowledge/external/dna/persons/{pessoa}/
      │
      ├── Dossier de pessoa ─────────────► knowledge/external/dossiers/persons/
      │
      ├── Dossier de tema ───────────────► knowledge/external/dossiers/themes/
      │
      ├── Insight de reuniao ────────────► knowledge/business/insights/
      │   │                                  by-meeting/, by-person/, by-theme/
      │   │
      │   └── Detectou SOP? ─────────────► knowledge/business/sops/  (rascunho)
      │                                      │
      │                                      ▼  [validacao humana]
      │                                    workspace/_templates/  (oficial)
      │
      ├── Arquivo de agente ─────────────► agents/{tipo}/{nome}/
      │   (AGENT.md, SOUL.md, etc.)
      │
      ├── Relatorio/auditoria ───────────► artifacts/audit/
      │
      ├── Log de processamento ──────────► logs/{categoria}/
      │
      ├── Indice RAG ────────────────────► .data/{rag_bucket}/
      │
      └── Doc estrategico ───────────────► workspace/{subdir}/
          (org, strategy, finance)
```

---

## 8. Fluxo de Alimentacao dos Agentes

```
╔══════════════════════════════════════════════════════════════════════════════╗
║            QUEM ALIMENTA QUEM — Mapa de Dependencias                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

  ┌────────────────────┐          ┌──────────────────────────────────────┐
  │ knowledge/external/│          │         agents/external/             │
  │                    │          │                                      │
  │  dna/persons/AH/   │─────────►│  alex-hormozi/                      │
  │  dossiers/persons/  │─────────►│    AGENT.md  ← dna + dossier       │
  │  sources/AH/        │─────────►│    SOUL.md   ← voz + identidade    │
  │  playbooks/         │─────────►│    MEMORY.md ← insights acumulados │
  │                    │          │    DNA-CONFIG ← mapa de fontes      │
  └────────────────────┘          └──────────────────────────────────────┘

  ┌────────────────────┐          ┌──────────────────────────────────────┐
  │knowledge/business/ │          │         agents/business/             │
  │                    │          │                                      │
  │  people/{pessoa}/   │─────────►│  {colaborador}/                     │
  │  insights/by-person/│─────────►│    AGENT.md  ← DNA colaborador     │
  │  dossiers/          │─────────►│    SOUL.md   ← como a pessoa fala  │
  │                    │          │    MEMORY.md ← reunioes, decisoes   │
  └────────────────────┘          └──────────────────────────────────────┘

  ┌────────────────────┐          ┌──────────────────────────────────────┐
  │knowledge/personal/ │          │         agents/personal/             │
  │  + ALL buckets     │          │                                      │
  │                    │─────────►│  {founder}/                          │
  │  cognitive/         │─────────►│    AGENT.md  ← todos os buckets    │
  │  calls/             │─────────►│    SOUL.md   ← voz do founder     │
  │  messages/          │─────────►│    MEMORY.md ← tudo acumulado     │
  └────────────────────┘          └──────────────────────────────────────┘

  ┌────────────────────┐          ┌──────────────────────────────────────┐
  │  MULTIPLOS BUCKETS │          │         agents/cargo/                │
  │                    │          │                                      │
  │  external/ ─(0.8)──│─────────►│  sales/closer/                      │
  │  business/ ─(0.5)──│─────────►│    AGENT.md  ← mix ponderado       │
  │  personal/ ─(0.2)──│─────────►│    SOUL.md   ← voz do cargo        │
  │                    │          │    DNA-CONFIG ← pesos por fonte     │
  │  Peso 0.0 a 1.0    │          │                                      │
  └────────────────────┘          └──────────────────────────────────────┘
```

---

## 9. Isolamento RAG — Zero Contaminacao

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ISOLAMENTO RAG POR BUCKET                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   Cada bucket tem seu proprio indice. NUNCA se misturam.                     ║
║                                                                              ║
║   ┌─────────────┐     ┌──────────────────────┐     ┌─────────────┐          ║
║   │   BUCKET 1  │     │   .data/rag_expert/  │     │ "O que o    │          ║
║   │  EXTERNAL   │────►│   BM25 + Vectors     │◄────│  Hormozi    │          ║
║   │             │     │   + Knowledge Graph   │     │  diz sobre  │          ║
║   └─────────────┘     └──────────────────────┘     │  vendas?"   │          ║
║                                                     └─────────────┘          ║
║   ┌─────────────┐     ┌──────────────────────┐     ┌─────────────┐          ║
║   │   BUCKET 2  │     │  .data/rag_business/ │     │ "O que      │          ║
║   │  BUSINESS   │────►│   BM25 + Vectors     │◄────│  decidimos  │          ║
║   │             │     │                      │     │  na ultima  │          ║
║   └─────────────┘     └──────────────────────┘     │  reuniao?"  │          ║
║                                                     └─────────────┘          ║
║   ┌─────────────┐                                                            ║
║   │   BUCKET 3  │     NUNCA INDEXADO                                         ║
║   │  PERSONAL   │     Privacidade absoluta                                   ║
║   │             │     Acesso apenas via agents/personal/                      ║
║   └─────────────┘                                                            ║
║                                                                              ║
║   ROTEAMENTO DE QUERIES:                                                     ║
║                                                                              ║
║   "O que Hormozi diz sobre X?"         → rag_expert                          ║
║   "O que aconteceu na reuniao?"        → rag_business                        ║
║   "O que EU penso sobre X?"            → rag_personal (local)                ║
║   "Como estruturar vendas?"            → rag_expert, fallback rag_business   ║
║   "Sintese cross-expert sobre X?"      → rag_expert (graph-enhanced)         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. Sistema de Layers — Seguranca por Camada

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                       SISTEMA DE 3 LAYERS                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   L1 (Community)                                                             ║
║   ════════════════                                                           ║
║   Git: TRACKED | Distribuido via npm                                         ║
║   │                                                                          ║
║   ├── core/                Engine, tasks, workflows, paths.py                ║
║   ├── .claude/             Hooks, skills, commands, rules                    ║
║   ├── bin/                 CLI executaveis                                   ║
║   ├── agents/_templates/   Templates de criacao de agentes                   ║
║   ├── agents/system/       Conclave, boardroom, JARVIS                       ║
║   ├── agents/constitution/ Governanca                                        ║
║   ├── system/              Estado do JARVIS                                  ║
║   ├── reference/           Documentacao                                      ║
║   ├── workspace/           Template structure (vazio, apenas scaffold)        ║
║   └── .planning/           GSD plans                                         ║
║                                                                              ║
║   L2 (Pro)                                                                   ║
║   ════════════════                                                           ║
║   Git: TRACKED (premium) | Conhecimento populado                             ║
║   │                                                                          ║
║   ├── knowledge/external/  DNA, dossiers, playbooks, sources                 ║
║   ├── agents/external/     Clones de especialistas                           ║
║   ├── agents/cargo/        Papeis funcionais hibridos                        ║
║   ├── agents/sua-empresa/  SOW outputs                                       ║
║   └── workspace/ (populado) Com dados reais de negocio                       ║
║                                                                              ║
║   L3 (Personal)                                                              ║
║   ════════════════                                                           ║
║   Git: GITIGNORED | Dados privados, runtime                                 ║
║   │                                                                          ║
║   ├── knowledge/business/  Reunioes, calls, insights                         ║
║   ├── knowledge/personal/  Email, WhatsApp, reflexoes                        ║
║   ├── agents/personal/     Clone do founder                                  ║
║   ├── agents/discovery/    Role tracking auto-gerado                         ║
║   ├── .data/               RAG indexes, knowledge graph, embeddings          ║
║   ├── logs/                Session logs, batch logs                           ║
║   ├── artifacts/           Relatorios de auditoria                           ║
║   ├── processing/          Speakers, entities, diarization                   ║
║   └── research/            Analises ad-hoc                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 11. Cascateamento Cross-Bucket — Conexoes Entre Mundos

```
╔══════════════════════════════════════════════════════════════════════════════╗
║           CASCATEAMENTO: COMO OS BUCKETS SE CONECTAM                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

  O sistema NAO e isolado. Existem 4 pontos de conexao entre buckets:


  ┌─ CONEXAO 1: CARGO AGENTS (Mix Ponderado) ──────────────────────────────┐
  │                                                                         │
  │  agents/cargo/ puxa DNA de MULTIPLOS buckets com pesos:                │
  │                                                                         │
  │  knowledge/external/ ──(peso 0.8)──┐                                   │
  │                                     ├──► agents/cargo/sales/closer/     │
  │  knowledge/business/ ──(peso 0.5)──┤    DNA-CONFIG.yaml define pesos   │
  │                                     │                                   │
  │  knowledge/personal/ ──(peso 0.2)──┘                                   │
  │                                                                         │
  │  Resolucao de conflito: MAP-CONFLITOS.yaml ou apresentar ambas posicoes│
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─ CONEXAO 2: SOP PROMOTION (Business → Workspace) ──────────────────────┐
  │                                                                         │
  │  Pipeline detecta processo repetitivo em reunioes:                     │
  │                                                                         │
  │  knowledge/business/sops/    ──── RASCUNHO (auto-detectado)            │
  │          │                                                              │
  │          ▼  [revisao humana]                                           │
  │          │                                                              │
  │  workspace/_templates/       ──── OFICIAL (promovido)                  │
  │                                                                         │
  │  REGRA: Nunca escrever direto em workspace/_templates/.                │
  │         Sempre comecar em knowledge/business/sops/.                    │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─ CONEXAO 3: FOUNDER AGENT (Todos → Personal) ──────────────────────────┐
  │                                                                         │
  │  agents/personal/{founder}/ tem acesso a TODOS os buckets:             │
  │                                                                         │
  │  knowledge/external/  ──────┐                                          │
  │                              ├──► agents/personal/{founder}/            │
  │  knowledge/business/  ──────┤    O unico agente com visao 360          │
  │                              │                                          │
  │  knowledge/personal/  ──────┘                                          │
  │                                                                         │
  │  O founder clone e o unico que pode cruzar TODOS os contextos.         │
  └─────────────────────────────────────────────────────────────────────────┘

  ┌─ CONEXAO 4: CONCLAVE (Cross-Bucket Debate) ────────────────────────────┐
  │                                                                         │
  │  /conclave ativa debate multi-agente:                                  │
  │                                                                         │
  │  agents/external/hormozi  ── "Aqui esta o que eu faria..."             │
  │  agents/cargo/cfo         ── "Os numeros dizem que..."                 │
  │  agents/business/parceiro ── "Na ultima reuniao decidimos..."          │
  │                                                                         │
  │  Council Modes controlam acesso:                                       │
  │  ┌──────────────┬──────────┬──────────┬──────────┐                    │
  │  │ Mode         │ External │ Business │ Personal │                    │
  │  ├──────────────┼──────────┼──────────┼──────────┤                    │
  │  │ expert-only  │    SIM   │    ---   │    ---   │                    │
  │  │ business     │    SIM   │    SIM   │    ---   │                    │
  │  │ full-3d      │    SIM   │    SIM   │    SIM   │                    │
  │  │ personal     │    ---   │    ---   │    SIM   │                    │
  │  │ company-only │    ---   │    SIM   │    ---   │                    │
  │  └──────────────┴──────────┴──────────┴──────────┘                    │
  │                                                                         │
  │  Se bucket indisponivel, agente DECLARA:                               │
  │  "Esta resposta nao considera dados de [bucket]."                      │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Infra de Suporte

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    INFRAESTRUTURA DE SUPORTE                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   core/                           ENGINE                                     ║
║   ├── paths.py                    Contrato de diretorios (76+ keys)          ║
║   ├── intelligence/               Scripts de processamento                   ║
║   │   ├── pipeline/               Pipeline MCE, Fireflies, Read.ai           ║
║   │   ├── rag/                    Chunker, BM25, vectors, graph              ║
║   │   └── validation/             Validacao de integridade                   ║
║   ├── templates/                  Templates de logs, agentes                 ║
║   └── tasks/                      Task definitions                           ║
║                                                                              ║
║   .claude/                        CLAUDE CODE INTEGRATION                    ║
║   ├── hooks/                      20+ hooks Python (lifecycle events)        ║
║   ├── skills/                     47+ skills disponiveis                     ║
║   ├── commands/                   Comandos customizados                      ║
║   ├── rules/                      30 regras em 6 grupos                      ║
║   ├── mission-control/            Estado da missao, indexes                   ║
║   ├── sessions/                   Logs de sessao                             ║
║   └── jarvis/                     Estado, memoria, sub-agentes do JARVIS     ║
║                                                                              ║
║   .data/                          INDEXES (L3 — gitignored)                  ║
║   ├── rag_expert/                 BM25 + vectors para Bucket 1               ║
║   ├── rag_business/               BM25 + vectors para Bucket 2               ║
║   ├── knowledge_graph/            Grafo de entidades (1300+ nos)             ║
║   ├── agent_memory/               JSONL de memoria de agentes                ║
║   └── voice_embeddings/           Embeddings de voz                          ║
║                                                                              ║
║   logs/                           LOGS (L3 — append-only JSONL)              ║
║   ├── batches/                    Logs de batches processados                ║
║   ├── sessions/                   Logs de sessao                             ║
║   ├── decisions/                  Logs de decisoes                           ║
║   └── read-ai-harvest/            Logs de coleta Read.ai                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 13. Proibicoes

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         O QUE NUNCA FAZER                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  docs/                  → PROIBIDO. Usar reference/                          │
│  inbox/ na raiz         → PROIBIDO. Distribuido nos 3 bucket inboxes         │
│  {empresa}/ na raiz     → PROIBIDO. Usar workspace/businesses/{marca}/       │
│  knowledge/ root files  → PROIBIDO. Deve ir em external/, business/ ou       │
│                           personal/                                          │
│  Novo diretorio raiz    → PROIBIDO. Atualizar directory-contract.md primeiro │
│  Paths hardcoded        → PROIBIDO. Importar de core/paths.py               │
│  L3 em L1/L2            → PROIBIDO. Dados privados em dirs gitignored        │
│  Agentes fora de agents/→ PROIBIDO. Quebra agent discovery                   │
│  SOPs direto em         → PROIBIDO. Comecar em knowledge/business/sops/,     │
│  workspace/_templates/    promover apos validacao humana                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Path Contract (Como Usar)

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

# CORRETO: usar constantes de paths.py
output = ROUTING["audit_report"] / "report.json"
dna = KNOWLEDGE_EXTERNAL / "dna" / "persons" / "alex-hormozi"
meeting = ROUTING["business_insights"] / "by-meeting" / "MEET-0001.md"
agent = AGENTS_EXTERNAL / "jeremy-haynes" / "AGENT.md"

# ERRADO: paths hardcoded (quebram em reorganizacao)
Path("knowledge/dna/persons/alex-hormozi")   # STALE
Path("agents/minds/alex-hormozi")             # OLD STRUCTURE
Path("inbox/raw-file.txt")                    # ROOT INBOX REMOVED
```

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-03-07 | Initial 3D architecture (3 buckets, stale workspace model) |
| 2.0.0 | 2026-03-13 | Full rewrite: knowledge/business/ bucket, workspace as prescriptive layer, 5 agent types, cascading mechanisms, decision tree, SOP promotion flow, RAG isolation, layer security, cross-bucket connections |
