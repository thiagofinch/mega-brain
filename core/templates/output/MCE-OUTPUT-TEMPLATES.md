# MCE OUTPUT TEMPLATES v2.0
# Mega Brain — Unified Output Templates for MCE Pipeline
#
# Consolidation of legacy Phase 5 templates (MOGA BRAIN) into
# the current 13-step MCE pipeline (S00-S12).
#
# Width Standard: RW=72 inner (76 total with borders ║...║)
# Matches: mce_session_reporter.py (Stop hook)
# Differs from: mce_step_logger.py (PW=62, realtime micro-panels)
#
# Box Drawing:
#   Double: ╔═╗║╚═╝╠╣  (primary sections)
#   Single: ┌─┐│└─┘├┤  (nested tables, sub-sections)
#
# Bars:
#   Fill bar : █ filled, ░ empty (20 chars default)
#   Tone bar : ● filled, ○ empty (10 chars)
#   Progress : S00● S01● S02◉ S03○ ... (done/current/pending)
#
# Status Icons:
#   ✅ done  |  ⚠️ attention  |  🔴 critical  |  🆕 new  |  ● active  |  ○ inactive
#
# Delta Notation: {before} → {after}  (+{delta})
#
# Variables use {PLACEHOLDER} syntax — replaced at render time.
#
# Path Mapping (Legacy → Current):
#   /00-INBOX/                    → knowledge/{bucket}/inbox/
#   /02-KNOWLEDGE/DNA/PERSONS/    → knowledge/external/dna/persons/{slug}/
#   /02-KNOWLEDGE/DOSSIERS/       → knowledge/external/dossiers/{type}/
#   /05-AGENTS/PERSONS/           → agents/external/{slug}/
#   /05-AGENTS/CARGO/             → agents/cargo/{area}/{cargo}/
#   /05-AGENTS/ORG-LIVE/          → workspace/
#   /04-SYSTEM/TEMPLATES/         → core/templates/
#
# ═══════════════════════════════════════════════════════════════════════════


---

## 1. EXTRACTION SUMMARY
## Maps to: Legacy 5.1 FOUNDATION
## MCE Steps: S03 (Chunk) → S04 (Entity) → S05 (Insight)
## When: After extracting DNA and creating person dossiers for a source

```
╔════════════════════════════════════════════════════════════════════════════╗
║  STEP 03-05 — EXTRACTION SUMMARY              [ {SLUG_UPPER} ]          ║
║  Bucket: {BUCKET_ICON}          Pipeline: MCE v2.0          ⏱ {HH:MM}  ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ DNA EXTRACTION — DELTA DESTA EXECUÇÃO                               ║
║                                                                          ║
║    Filosofias:      {N_ANTES} → {N_DEPOIS}  (+{D})  {BAR_20} {%}%       ║
║    Modelos Mentais: {N_ANTES} → {N_DEPOIS}  (+{D})  {BAR_20} {%}%       ║
║    Heurísticas:     {N_ANTES} → {N_DEPOIS}  (+{D})  {BAR_20} {%}% ★★★   ║
║    Frameworks:      {N_ANTES} → {N_DEPOIS}  (+{D})  {BAR_20} {%}%       ║
║    Metodologias:    {N_ANTES} → {N_DEPOIS}  (+{D})  {BAR_20} {%}%       ║
║                                                                          ║
║    TOTAL ELEMENTOS: {TOTAL_ANTES} → {TOTAL_DEPOIS}  (+{DELTA_TOTAL})    ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ ARQUIVOS PROCESSADOS                                                ║
║                                                                          ║
║    ORIGEM: knowledge/{BUCKET}/inbox/{PASTA_FONTE}/                       ║
║                                                                          ║
║    ┌──────┬──────────────────────────────────┬────────┬──────┬─────────┐ ║
║    │  #   │ ARQUIVO                          │ CHUNKS │ INS. │ STATUS  │ ║
║    ├──────┼──────────────────────────────────┼────────┼──────┼─────────┤ ║
║    │  001 │ {NOME_ARQUIVO_1}                 │   {N}  │  {N} │ ✅ OK   │ ║
║    │  002 │ {NOME_ARQUIVO_2}                 │   {N}  │  {N} │ ✅ OK   │ ║
║    │  ... │ ...                              │   ...  │  ... │ ...     │ ║
║    │  {N} │ {NOME_ARQUIVO_N}                 │   {N}  │  {N} │ ✅ OK   │ ║
║    └──────┴──────────────────────────────────┴────────┴──────┴─────────┘ ║
║                                                                          ║
║    TOTAL: {N} arquivos | {N} chunks | {N} insights extraídos             ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ TOP INSIGHTS EXTRAÍDOS (Híbrido: Top 5 + Contagem)                  ║
║                                                                          ║
║    HEURÍSTICAS (Top 5 de {TOTAL}):                                       ║
║    ┌─────────────┬──────────────────────────────────┬──────┬───────────┐ ║
║    │  ID         │ INSIGHT                          │ LAYER│ CONF.     │ ║
║    ├─────────────┼──────────────────────────────────┼──────┼───────────┤ ║
║    │  HEU-{}-001 │ "{TEXTO}"                        │ L3   │ ████░ 85% │ ║
║    │  HEU-{}-002 │ "{TEXTO}"                        │ L3   │ ████░ 82% │ ║
║    │  HEU-{}-003 │ "{TEXTO}"                        │ L3   │ ███░░ 78% │ ║
║    │  HEU-{}-004 │ "{TEXTO}"                        │ L3   │ ███░░ 75% │ ║
║    │  HEU-{}-005 │ "{TEXTO}"                        │ L3   │ ███░░ 72% │ ║
║    └─────────────┴──────────────────────────────────┴──────┴───────────┘ ║
║    + {N} heurísticas [knowledge/external/dna/persons/{SLUG}/HEURIST...]  ║
║                                                                          ║
║    FRAMEWORKS (Top 3 de {TOTAL}):                                        ║
║    ┌─────────────┬──────────────────────────────────┬──────┬───────────┐ ║
║    │  ID         │ FRAMEWORK                        │ STEPS│ CONF.     │ ║
║    ├─────────────┼──────────────────────────────────┼──────┼───────────┤ ║
║    │  FRA-{}-001 │ "{NOME}"                         │  {N} │ ████░ 90% │ ║
║    │  FRA-{}-002 │ "{NOME}"                         │  {N} │ ████░ 85% │ ║
║    │  FRA-{}-003 │ "{NOME}"                         │  {N} │ ███░░ 80% │ ║
║    └─────────────┴──────────────────────────────────┴──────┴───────────┘ ║
║    + {N} frameworks [knowledge/external/dna/persons/{SLUG}/FRAMEWOR...]  ║
║                                                                          ║
║    FILOSOFIAS (Top 3 de {TOTAL}):                                        ║
║    ┌─────────────┬──────────────────────────────────┬──────┬───────────┐ ║
║    │  ID         │ FILOSOFIA                        │ IMPL.│ CONF.     │ ║
║    ├─────────────┼──────────────────────────────────┼──────┼───────────┤ ║
║    │  FIL-{}-001 │ "{TEXTO}"                        │  {T} │ ████░ 88% │ ║
║    │  FIL-{}-002 │ "{TEXTO}"                        │  {T} │ ████░ 85% │ ║
║    │  FIL-{}-003 │ "{TEXTO}"                        │  {T} │ ███░░ 80% │ ║
║    └─────────────┴──────────────────────────────────┴──────┴───────────┘ ║
║    + {N} filosofias [knowledge/external/dna/persons/{SLUG}/FILOSOF...]   ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ ARTEFATOS CRIADOS                                                   ║
║                                                                          ║
║    knowledge/external/dna/persons/{SLUG}/                                ║
║    ├── ✅ DNA-CONFIG.yaml         [CRIADO/ATUALIZADO]                    ║
║    ├── ✅ FILOSOFIAS.yaml         (+{N} elementos)                       ║
║    ├── ✅ MODELOS-MENTAIS.yaml    (+{N} elementos)                       ║
║    ├── ✅ HEURISTICAS.yaml        (+{N} elementos)                       ║
║    ├── ✅ FRAMEWORKS.yaml         (+{N} elementos)                       ║
║    └── ✅ METODOLOGIAS.yaml       (+{N} elementos)                       ║
║                                                                          ║
║    knowledge/external/dossiers/persons/                                   ║
║    └── ✅ DOSSIER-{SLUG}.md       [CRIADO/ATUALIZADO] ({N} seções)       ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CHECKPOINT — EXTRACTION VALIDATION                                  ║
║                                                                          ║
║    [✓] Todos os arquivos fonte processados                               ║
║    [✓] 5 camadas de DNA extraídas                                        ║
║    [✓] DNA-CONFIG.yaml criado com metadados                              ║
║    [✓] DOSSIER da pessoa criado/atualizado                               ║
║    [✓] Rastreabilidade chunk_id → insight_id mantida                     ║
║                                                                          ║
║    STATUS: ✅ EXTRACTION SUMMARY COMPLETA                                ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PIPELINE PROGRESS  {N}/12 steps  [{PCT}%]                           ║
║    {BAR_30}                                                              ║
║    S00●  S01●  S02●  S03●  S04●  S05◉  S06○                             ║
║    S07○  S08○  S09○  S10○  S11○  S12○                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## 2. PERSON AGENT
## Maps to: Legacy 5.2 PERSON AGENTS
## MCE Step: S10.4 (Agent Compilation — external agent creation)
## When: After creating or updating a mind-clone PERSON agent

```
╔════════════════════════════════════════════════════════════════════════════╗
║  STEP 10 — AGENT COMPILATION (PERSON)          [ {SLUG_UPPER} ]          ║
║  Bucket: 📚 EXTERNAL          Pipeline: MCE v2.0          ⏱ {HH:MM}    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ RESUMO DO AGENTE                                                    ║
║                                                                          ║
║    ╔══════════════════════════════════════════════════════════════════╗   ║
║    ║  AGENT: {NOME_FONTE}                                            ║   ║
║    ║  TIPO : PERSON (Espelho)        NATUREZA: ISOLADO (100%)        ║   ║
║    ║  DNA  : 100% {NOME_FONTE}       VERSÃO  : {X.X.X}              ║   ║
║    ║                                                                  ║   ║
║    ║  EXPERTISE:                                                      ║   ║
║    ║  {AREA_1}:   {BAR_20} {N}%                                      ║   ║
║    ║  {AREA_2}:   {BAR_20} {N}%                                      ║   ║
║    ║  {AREA_3}:   {BAR_20} {N}%                                      ║   ║
║    ║  {AREA_4}:   {BAR_20} {N}%                                      ║   ║
║    ║                                                                  ║   ║
║    ║  FILOSOFIA CENTRAL:                                              ║   ║
║    ║  "{FILOSOFIA_PRINCIPAL}"                                         ║   ║
║    ╚══════════════════════════════════════════════════════════════════╝   ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ ARQUIVOS DO AGENTE                                                  ║
║                                                                          ║
║    agents/external/{SLUG}/                                               ║
║    ┌───────────────┬────────────────┬───────────────────┬──────────────┐ ║
║    │ ARQUIVO       │ STATUS         │ DELTA             │ DETALHES     │ ║
║    ├───────────────┼────────────────┼───────────────────┼──────────────┤ ║
║    │ AGENT.md      │ ✅ {C/U}       │ {A}→{D} (+{N} ln)│ 11/11 parts  │ ║
║    │ SOUL.md       │ ✅ {C/U}       │ {A}→{D} (+{N} ln)│ Persona OK   │ ║
║    │ DNA-CONFIG    │ ✅ {C/U}       │ 100% {FONTE}      │ Rastreável   │ ║
║    │ MEMORY.md     │ ✅ {C/U}       │ Log iniciado      │ Pronto       │ ║
║    └───────────────┴────────────────┴───────────────────┴──────────────┘ ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CONTEÚDO DO AGENT.md (11 PARTS — Template V3)                       ║
║                                                                          ║
║    ┌──────┬────────────────────┬──────┬─────────────────────────────────┐ ║
║    │ PART │ NOME               │ ELEM.│ TOP ITEM                        │ ║
║    ├──────┼────────────────────┼──────┼─────────────────────────────────┤ ║
║    │   0  │ IDENTITY CARD      │   1  │ Card visual completo            │ ║
║    │   1  │ FILOSOFIAS         │ {N}  │ "{TOP}"                         │ ║
║    │   2  │ MODELOS MENTAIS    │ {N}  │ "{TOP}"                         │ ║
║    │   3  │ HEURÍSTICAS ★★★    │ {N}  │ "{TOP_COM_NUMERO}"              │ ║
║    │   4  │ FRAMEWORKS         │ {N}  │ {TOP_FRAMEWORK}                 │ ║
║    │   5  │ METODOLOGIAS       │ {N}  │ {TOP_METODOLOGIA}               │ ║
║    │   6  │ TENSÕES/CONEXÕES   │  —   │ C:{N} / T:{N}                   │ ║
║    │   7  │ MÉTRICAS/BENCH.    │ {N}  │ {TOP_METRICA}: {VALOR}          │ ║
║    │   8  │ VOZ/COMUNICAÇÃO    │ {N}  │ Tom: {TOM_DOMINANTE}            │ ║
║    │   9  │ GAPS/LIMITAÇÕES    │ {N}  │ Escalar: {AGENTES}              │ ║
║    │  10  │ EVOLUÇÃO           │   1  │ Changelog v{X.X.X}              │ ║
║    └──────┴────────────────────┴──────┴─────────────────────────────────┘ ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CONEXÕES COM CARGO AGENTS                                           ║
║                                                                          ║
║    ┌──────────────────┬────────┬────────────────────────────────────────┐ ║
║    │ CARGO            │ PESO   │ ÁREAS DE CONTRIBUIÇÃO                  │ ║
║    ├──────────────────┼────────┼────────────────────────────────────────┤ ║
║    │ {CARGO_1}        │  {N}%  │ {AREAS}                                │ ║
║    │ {CARGO_2}        │  {N}%  │ {AREAS}                                │ ║
║    │ {CARGO_3}        │  {N}%  │ {AREAS}                                │ ║
║    └──────────────────┴────────┴────────────────────────────────────────┘ ║
║                                                                          ║
║    REFERENCIADO EM DOSSIERS:                                             ║
║    ├── knowledge/external/dossiers/persons/DOSSIER-{SLUG}.md             ║
║    ├── knowledge/external/dossiers/themes/DOSSIER-{TEMA_1}.md            ║
║    └── knowledge/external/dossiers/themes/DOSSIER-{TEMA_2}.md            ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CHECKPOINT — PERSON AGENT VALIDATION                                ║
║                                                                          ║
║    [✓] AGENT.md criado com 11 parts completas (Template V3)              ║
║    [✓] SOUL.md define personalidade e voz                                ║
║    [✓] DNA-CONFIG.yaml rastreia 100% para fonte única                    ║
║    [✓] MEMORY.md inicializado                                            ║
║    [✓] Conexões com CARGO agents mapeadas                                ║
║                                                                          ║
║    STATUS: ✅ PERSON AGENT COMPILATION COMPLETA                          ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PIPELINE PROGRESS  {N}/12 steps  [{PCT}%]                           ║
║    {BAR_30}                                                              ║
║    S00●  S01●  S02●  S03●  S04●  S05●  S06●                             ║
║    S07●  S08●  S09●  S10◉  S11○  S12○                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## 3. CARGO AGENT ENRICHMENT
## Maps to: Legacy 5.3 CARGO AGENTS
## MCE Step: S10.4 (Agent Compilation — cargo enrichment)
## When: After creating new CARGO agents or enriching existing ones with new source DNA

```
╔════════════════════════════════════════════════════════════════════════════╗
║  STEP 10 — CARGO AGENT ENRICHMENT              [ {SLUG_UPPER} ]         ║
║  Bucket: 📚 EXTERNAL          Pipeline: MCE v2.0          ⏱ {HH:MM}    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ GATILHOS E ALERTAS                                                  ║
║                                                                          ║
║    🔴 THRESHOLDS ATINGIDOS (Criar novo agente):                          ║
║    ┌──────────────────┬────────┬───────────┬───────────────────────────┐ ║
║    │ ROLE             │ MENÇÕES│ THRESHOLD │ STATUS                    │ ║
║    ├──────────────────┼────────┼───────────┼───────────────────────────┤ ║
║    │ {ROLE_1}         │  {N}   │    10     │ 🔴 CRIAR! {BAR_20}       │ ║
║    │ {ROLE_2}         │  {N}   │    10     │ ⚠️ MONITOR {BAR_20}      │ ║
║    │ {ROLE_3}         │  {N}   │    10     │ ○ TRACKING {BAR_20}      │ ║
║    └──────────────────┴────────┴───────────┴───────────────────────────┘ ║
║                                                                          ║
║    AÇÃO: Criar AGENT-{ROLE_1} em agents/cargo/{AREA}/{ROLE_1}/          ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ NOVOS CARGO AGENTS CRIADOS                                          ║
║                                                                          ║
║    ╔══════════════════════════════════════════════════════════════════╗   ║
║    ║  🆕 NOVO AGENTE: {NOME_CARGO}                                   ║   ║
║    ║  PATH: agents/cargo/{AREA}/{CARGO}/                              ║   ║
║    ║  NATUREZA: HÍBRIDO                                               ║   ║
║    ║                                                                  ║   ║
║    ║  DNA COMPOSITION:                                                ║   ║
║    ║  ├── {FONTE_1}: {N}% {BAR_20}                                   ║   ║
║    ║  ├── {FONTE_2}: {N}% {BAR_20}                                   ║   ║
║    ║  └── {FONTE_3}: {N}% {BAR_20}                                   ║   ║
║    ║                                                                  ║   ║
║    ║  MISSÃO: {MISSAO_DO_CARGO}                                       ║   ║
║    ║                                                                  ║   ║
║    ║  KPIs CORE:                                                      ║   ║
║    ║  ├── {KPI_1}: {VALOR}                                           ║   ║
║    ║  ├── {KPI_2}: {VALOR}                                           ║   ║
║    ║  └── {KPI_3}: {VALOR}                                           ║   ║
║    ║                                                                  ║   ║
║    ║  ARQUIVOS CRIADOS:                                               ║   ║
║    ║  ├── ✅ AGENT.md         (11 parts — Template V3)                ║   ║
║    ║  ├── ✅ SOUL.md          (personalidade)                         ║   ║
║    ║  ├── ✅ DNA-CONFIG.yaml  (rastreável)                            ║   ║
║    ║  └── ✅ MEMORY.md        (inicializado)                          ║   ║
║    ╚══════════════════════════════════════════════════════════════════╝   ║
║                                                                          ║
║    {REPETIR BLOCO ╔═══╝ PARA CADA NOVO AGENTE}                          ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CARGO AGENTS ENRIQUECIDOS (Incrementos)                             ║
║                                                                          ║
║    ┌──────────────┬──────────┬───────────────┬───────┬─────────────────┐ ║
║    │ AGENTE       │ ANTES    │ DEPOIS        │ DELTA │ NOVOS ELEMENTOS │ ║
║    ├──────────────┼──────────┼───────────────┼───────┼─────────────────┤ ║
║    │ CLOSER       │ CG:100%  │ CG:80%+JM:20%│+{SRC} │ +{N} heu, +{N} │ ║
║    │ BDR          │ CG:70%   │ CG:60%+..    │+{SRC} │ +{N} met       │ ║
║    │ SALES-MANAGER│ CG:80%   │ CG:60%+AH:40%│+{SRC} │ +{N} fil       │ ║
║    └──────────────┴──────────┴───────────────┴───────┴─────────────────┘ ║
║                                                                          ║
║    DETALHES DOS INCREMENTOS:                                             ║
║                                                                          ║
║    ┌────────────────────────────────────────────────────────────────────┐ ║
║    │ CLOSER (+{FONTE})                                                  │ ║
║    │ ────────────────────────────────────────────────────────────────── │ ║
║    │ Top 3 Novos Insights:                                              │ ║
║    │ ├── HEU-{ID}: "{TEXTO}"                                           │ ║
║    │ ├── HEU-{ID}: "{TEXTO}"                                           │ ║
║    │ └── FRA-{ID}: {NOME_FRAMEWORK} ({N} etapas)                       │ ║
║    │                                                                    │ ║
║    │ + {N} outros [agents/cargo/sales/closer/AGENT.md]                  │ ║
║    └────────────────────────────────────────────────────────────────────┘ ║
║                                                                          ║
║    {REPETIR BLOCO ┌───┘ PARA CADA AGENTE ENRIQUECIDO}                   ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CONFLITOS DETECTADOS                                                ║
║                                                                          ║
║    ┌────┬──────────┬──────────────────────────┬────────────────────────┐ ║
║    │ #  │ AGENTE   │ CONFLITO                 │ RESOLUÇÃO              │ ║
║    ├────┼──────────┼──────────────────────────┼────────────────────────┤ ║
║    │  1 │ CLOSER   │ {SRC_A} diz X, {B} diz Y│ Contexto HT → {SRC_A} │ ║
║    │  2 │ BDR      │ Métrica: {N}% vs {N}%    │ Média ponderada: {N}%  │ ║
║    └────┴──────────┴──────────────────────────┴────────────────────────┘ ║
║                                                                          ║
║    Conflitos registrados em: artifacts/conflicts/MAP-CONFLITOS.yaml      ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CHECKPOINT — CARGO ENRICHMENT VALIDATION                            ║
║                                                                          ║
║    [✓] Novos CARGO agents criados: {N}                                   ║
║    [✓] CARGO agents enriquecidos: {N}                                    ║
║    [✓] DNA-CONFIG.yaml atualizado com novos pesos                        ║
║    [✓] Conflitos identificados e resolvidos: {N}                         ║
║    [✓] Role tracking atualizado                                          ║
║                                                                          ║
║    STATUS: ✅ CARGO ENRICHMENT COMPLETA                                  ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PIPELINE PROGRESS  {N}/12 steps  [{PCT}%]                           ║
║    {BAR_30}                                                              ║
║    S00●  S01●  S02●  S03●  S04●  S05●  S06●                             ║
║    S07●  S08●  S09●  S10◉  S11○  S12○                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## 4. THEME DOSSIER
## Maps to: Legacy 5.4 THEME DOSSIERS
## MCE Step: S10.1 (Dossier Compilation) + S10.2 (Source Docs)
## When: After consolidating cross-cutting theme dossiers

```
╔════════════════════════════════════════════════════════════════════════════╗
║  STEP 10 — THEME DOSSIER CONSOLIDATION         [ {SLUG_UPPER} ]         ║
║  Bucket: 📚 EXTERNAL          Pipeline: MCE v2.0          ⏱ {HH:MM}    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ RESUMO DE DOSSIERS — DELTA DESTA EXECUÇÃO                           ║
║                                                                          ║
║    knowledge/external/dossiers/themes/                                    ║
║                                                                          ║
║    DOSSIERS CRIADOS:      {N_ANTES} → {N_DEPOIS}  (+{DELTA})            ║
║    DOSSIERS ATUALIZADOS:  {N}                                            ║
║    SEÇÕES ADICIONADAS:    {N}                                            ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ NOVOS DOSSIERS DE TEMA                                              ║
║                                                                          ║
║    ┌────────────────────────────────────┬──────────────┬─────────────┐   ║
║    │ DOSSIER                           │ COMPOSIÇÃO   │ STATUS      │   ║
║    ├────────────────────────────────────┼──────────────┼─────────────┤   ║
║    │ DOSSIER-{TEMA_1}.md               │ Multi-source │ 🆕 NOVO     │   ║
║    │ DOSSIER-{TEMA_2}.md               │ {SRC} 100%   │ 🆕 NOVO     │   ║
║    └────────────────────────────────────┴──────────────┴─────────────┘   ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ DOSSIERS ATUALIZADOS                                                ║
║                                                                          ║
║    ┌────────────────────────────────────┬──────────┬────────┬─────────┐  ║
║    │ DOSSIER                           │ ANTES    │ DEPOIS │ DELTA   │  ║
║    ├────────────────────────────────────┼──────────┼────────┼─────────┤  ║
║    │ DOSSIER-01-ESTRUTURA-TIME.md      │ {N} sec  │ {N} sec│ +{N}    │  ║
║    │ DOSSIER-02-PROCESSO-VENDAS.md     │ {N} sec  │ {N} sec│ +{N}    │  ║
║    │ DOSSIER-CLOSER-FRAMEWORK.md       │ {N} sec  │ {N} sec│ +{N}    │  ║
║    └────────────────────────────────────┴──────────┴────────┴─────────┘  ║
║                                                                          ║
║    SEÇÕES ADICIONADAS:                                                   ║
║    ┌────────────────────────────────────────────────────────────────────┐ ║
║    │ DOSSIER-02-PROCESSO-VENDAS.md                                      │ ║
║    │ ├── +{SECAO_1} (novo de {FONTE})                                   │ ║
║    │ └── +{SECAO_2} (expandido com {FONTE})                             │ ║
║    └────────────────────────────────────────────────────────────────────┘ ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CROSS-REFERENCES VERIFICADAS                                        ║
║                                                                          ║
║    [✓] Person dossiers linkados a theme dossiers: {N}                    ║
║    [✓] Agent files referenciam dossiers corretos: {N}                    ║
║    [✓] Source docs indexados em _INDEX.md: {N}                           ║
║    [✓] DNA YAMLs citados em dossiers: {N}                               ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CHECKPOINT — THEME DOSSIER VALIDATION                               ║
║                                                                          ║
║    [✓] Novos dossiers criados: {N}                                       ║
║    [✓] Dossiers atualizados: {N}                                         ║
║    [✓] Cross-references OK                                               ║
║                                                                          ║
║    STATUS: ✅ THEME DOSSIER CONSOLIDATION COMPLETA                       ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PIPELINE PROGRESS  {N}/12 steps  [{PCT}%]                           ║
║    {BAR_30}                                                              ║
║    S00●  S01●  S02●  S03●  S04●  S05●  S06●                             ║
║    S07●  S08●  S09●  S10◉  S11○  S12○                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## 5. WORKSPACE SYNC
## Maps to: Legacy 5.5 ORG-LIVE
## MCE Step: S11 (Memory Enricher + Workspace Sync)
## When: After syncing organizational structure (roles, JDs, SOWs, scaling triggers)

```
╔════════════════════════════════════════════════════════════════════════════╗
║  STEP 11 — WORKSPACE SYNC                      [ {SLUG_UPPER} ]         ║
║  Bucket: 🗂️  WORKSPACE          Pipeline: MCE v2.0          ⏱ {HH:MM}  ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ ROLES DEFINIDOS                                                     ║
║                                                                          ║
║    ┌────────────┬──────────────────────────────────────────┬───────────┐ ║
║    │ ÁREA       │ ROLES                                    │ TOTAL     │ ║
║    ├────────────┼──────────────────────────────────────────┼───────────┤ ║
║    │ C-LEVEL    │ CEO, CFO, CMO, COO, CRO                  │     5     │ ║
║    │ SALES      │ CLOSER, BDR, LNS, SALES-MGR, NEPQ, SDS  │     8     │ ║
║    │ MARKETING  │ PAID-MEDIA-SPEC, CUSTOMER-SUCCESS         │     2     │ ║
║    │ OUTROS     │ ...                                       │    {N}    │ ║
║    └────────────┴──────────────────────────────────────────┴───────────┘ ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ SCALING TRIGGERS (Gatilhos de Contratação)                          ║
║                                                                          ║
║    workspace/team/SCALING-TRIGGERS.yaml                                  ║
║                                                                          ║
║    🔴 THRESHOLDS ATINGIDOS:                                              ║
║    ┌─────────────────┬─────────────────────────┬────────────────────────┐ ║
║    │ CARGO           │ GATILHO                 │ STATUS                 │ ║
║    ├─────────────────┼─────────────────────────┼────────────────────────┤ ║
║    │ {CARGO_1}       │ {GATILHO}               │ 🔴 CONTRATAR!          │ ║
║    └─────────────────┴─────────────────────────┴────────────────────────┘ ║
║                                                                          ║
║    ⚠️ PRÓXIMOS A ATINGIR:                                                ║
║    ┌─────────────────┬────────┬───────────┬────────────────────────────┐ ║
║    │ CARGO           │ ATUAL  │ THRESHOLD │ FALTAM                     │ ║
║    ├─────────────────┼────────┼───────────┼────────────────────────────┤ ║
║    │ {CARGO_2}       │  {N}   │    {T}    │ {T-N} para gatilho         │ ║
║    └─────────────────┴────────┴───────────┴────────────────────────────┘ ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ MEMORIES ATUALIZADAS                                                ║
║                                                                          ║
║    ┌───────────────────┬─────────┬─────────┬──────────────────────────┐  ║
║    │ MEMORY            │ ANTES   │ DEPOIS  │ NOVA ENTRADA             │  ║
║    ├───────────────────┼─────────┼─────────┼──────────────────────────┤  ║
║    │ MEMORY-CLOSER.md  │ v{X.X}  │ v{X.Y}  │ Processado {FONTE}       │  ║
║    │ MEMORY-{ROLE}.md  │ v{X.X}  │ v{X.Y}  │ Processado {FONTE}       │  ║
║    └───────────────────┴─────────┴─────────┴──────────────────────────┘  ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CHECKPOINT — WORKSPACE SYNC VALIDATION                              ║
║                                                                          ║
║    [✓] Novos ROLES criados: {N}                                          ║
║    [✓] MEMORIES atualizadas: {N}                                         ║
║    [✓] SCALING-TRIGGERS atualizado                                       ║
║    [✓] Workspace index files atualizados                                 ║
║                                                                          ║
║    STATUS: ✅ WORKSPACE SYNC COMPLETA                                    ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PIPELINE PROGRESS  {N}/12 steps  [{PCT}%]                           ║
║    {BAR_30}                                                              ║
║    S00●  S01●  S02●  S03●  S04●  S05●  S06●                             ║
║    S07●  S08●  S09●  S10●  S11◉  S12○                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## 6. VALIDATION GATE
## Maps to: Legacy 5.6 VALIDATION
## MCE Step: S12 (Finalization)
## When: After validating all cross-references and final states for a source

```
╔════════════════════════════════════════════════════════════════════════════╗
║  STEP 12 — VALIDATION GATE                     [ {SLUG_UPPER} ]         ║
║  Bucket: {BUCKET_ICON}          Pipeline: MCE v2.0          ⏱ {HH:MM}  ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ CHECKLIST DE VALIDAÇÃO COMPLETA                                     ║
║                                                                          ║
║    EXTRACTION (Steps 3-5):                                               ║
║    [✓] DNA extraído em 5 camadas                                         ║
║    [✓] DNA-CONFIG.yaml criado com metadados                              ║
║    [✓] DOSSIER-{SLUG}.md criado/atualizado                               ║
║                                                                          ║
║    BEHAVIORAL + IDENTITY (Steps 6-8):                                    ║
║    [✓] Padrões comportamentais extraídos                                 ║
║    [✓] Hierarquia de valores definida                                    ║
║    [✓] VOICE-DNA.yaml completo (6 dimensões)                             ║
║                                                                          ║
║    PERSON AGENT (Step 10):                                               ║
║    [✓] AGENT.md com 11 parts (Template V3)                               ║
║    [✓] SOUL.md define personalidade e voz                                ║
║    [✓] DNA-CONFIG.yaml rastreável                                        ║
║    [✓] MEMORY.md inicializado                                            ║
║                                                                          ║
║    CARGO AGENTS (Step 10):                                               ║
║    [✓] Novos agents criados: {N}                                         ║
║    [✓] Agents enriquecidos: {N}                                          ║
║    [✓] Conflitos resolvidos: {N}                                         ║
║    [✓] Role tracking atualizado                                          ║
║                                                                          ║
║    THEME DOSSIERS (Step 10):                                             ║
║    [✓] Novos dossiers: {N}                                               ║
║    [✓] Dossiers atualizados: {N}                                         ║
║    [✓] Cross-references OK                                               ║
║                                                                          ║
║    WORKSPACE SYNC (Step 11):                                             ║
║    [✓] ROLES criados: {N}                                                ║
║    [✓] MEMORIES atualizadas: {N}                                         ║
║    [✓] SCALING-TRIGGERS atualizado                                       ║
║                                                                          ║
║    INDEXES:                                                              ║
║    [✓] _INDEX.md files atualizados                                       ║
║    [✓] Todas referências válidas                                         ║
║    [✓] Estados finais OK                                                 ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ RESUMO FINAL DA FONTE                                               ║
║                                                                          ║
║    ╔══════════════════════════════════════════════════════════════════╗   ║
║    ║  {SLUG_UPPER} — PROCESSAMENTO COMPLETO                          ║   ║
║    ╠══════════════════════════════════════════════════════════════════╣   ║
║    ║                                                                  ║   ║
║    ║  ENTRADA:                                                        ║   ║
║    ║  ├── Batches: {N}                                                ║   ║
║    ║  ├── Arquivos: {N}                                               ║   ║
║    ║  ├── Chunks: {N}                                                 ║   ║
║    ║  └── Insights brutos: {N}                                        ║   ║
║    ║                                                                  ║   ║
║    ║  SAÍDA — DNA:                                                    ║   ║
║    ║  ├── Filosofias:      {N}  {BAR_20} {%}%                        ║   ║
║    ║  ├── Modelos Mentais: {N}  {BAR_20} {%}%                        ║   ║
║    ║  ├── Heurísticas:     {N}  {BAR_20} {%}% ★★★                    ║   ║
║    ║  ├── Frameworks:      {N}  {BAR_20} {%}%                        ║   ║
║    ║  └── Metodologias:    {N}  {BAR_20} {%}%                        ║   ║
║    ║                                                                  ║   ║
║    ║  SAÍDA — ARTEFATOS:                                              ║   ║
║    ║  ├── PERSON Agent: 1 (4 arquivos)                                ║   ║
║    ║  ├── CARGO Agents: {N} criados, {N} enriquecidos                 ║   ║
║    ║  ├── Theme Dossiers: {N} criados, {N} atualizados                ║   ║
║    ║  └── Workspace Roles: {N}                                        ║   ║
║    ╚══════════════════════════════════════════════════════════════════╝   ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ INDEX FILES ATUALIZADOS                                             ║
║                                                                          ║
║    [✓] knowledge/external/dna/_INDEX.md                                  ║
║    [✓] knowledge/external/dossiers/_INDEX.md                             ║
║    [✓] agents/AGENT-INDEX.yaml                                           ║
║    [✓] knowledge/external/sources/{SLUG}/_INDEX.md                       ║
║                                                                          ║
║    STATUS: ✅ VALIDATION GATE — FONTE COMPLETA                           ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PIPELINE PROGRESS  12/12 steps  [100%]                              ║
║    ██████████████████████████████                                        ║
║    S00●  S01●  S02●  S03●  S04●  S05●  S06●                             ║
║    S07●  S08●  S09●  S10●  S11●  S12●                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## 7. SESSION CONSOLIDATION
## Maps to: Legacy 5.FINAL CONSOLIDADO
## When: After processing ALL sources — cross-source analysis and grand totals
## Rendered by: mce_session_reporter.py (Stop hook) or manual invocation

```
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║  MCE SESSION — CROSS-SOURCE CONSOLIDATION                                ║
║  Pipeline: MCE v2.0          Mission: {MISSION_ID}          ⏱ {TOTAL}   ║
║  Fontes Processadas: {N} de {TOTAL}                                      ║
║                                                                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ▸ VISÃO GERAL CROSS-SOURCE                                            ║
║                                                                          ║
║    ╔══════════════════════════════════════════════════════════════════╗   ║
║    ║  ESTATÍSTICAS CONSOLIDADAS                                       ║   ║
║    ╠══════════════════════════════════════════════════════════════════╣   ║
║    ║                                                                  ║   ║
║    ║  ┌──────────────────┬────────┬──────────┬──────────────────────┐ ║   ║
║    ║  │ FONTE            │BATCHES │ ELEMENTOS│ CONTRIBUTION         │ ║   ║
║    ║  ├──────────────────┼────────┼──────────┼──────────────────────┤ ║   ║
║    ║  │ {FONTE_1}        │  {N}   │  ~{N}    │ {BAR_20} {%}%        │ ║   ║
║    ║  │ {FONTE_2}        │  {N}   │  ~{N}    │ {BAR_20} {%}%        │ ║   ║
║    ║  │ {FONTE_3}        │  {N}   │  ~{N}    │ {BAR_20} {%}%        │ ║   ║
║    ║  │ ...              │  ...   │  ...     │ ...                  │ ║   ║
║    ║  ├──────────────────┼────────┼──────────┼──────────────────────┤ ║   ║
║    ║  │ TOTAL            │  {N}   │  ~{N}    │ {BAR_20} 100%        │ ║   ║
║    ║  └──────────────────┴────────┴──────────┴──────────────────────┘ ║   ║
║    ║                                                                  ║   ║
║    ║  DISTRIBUIÇÃO POR CAMADA (AGREGADO):                             ║   ║
║    ║  Filosofias:      ~{N}   {BAR_20}  ~{%}%                        ║   ║
║    ║  Modelos Mentais: ~{N}   {BAR_20}  ~{%}%                        ║   ║
║    ║  Heurísticas:   ~{N}     {BAR_20}  ~{%}%  ★★★                   ║   ║
║    ║  Frameworks:      ~{N}   {BAR_20}  ~{%}%                        ║   ║
║    ║  Metodologias:    ~{N}   {BAR_20}  ~{%}%                        ║   ║
║    ║  Outros:          ~{N}   {BAR_20}  ~{%}%                        ║   ║
║    ╚══════════════════════════════════════════════════════════════════╝   ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ INVENTÁRIO DE AGENTES                                               ║
║                                                                          ║
║    agents/external/ (PERSON AGENTS — Espelhos):                          ║
║    ┌──────────────────┬──────────┬──────────────────────────┬──────────┐ ║
║    │ AGENTE           │ ELEMENTOS│ EXPERTISE                │ STATUS   │ ║
║    ├──────────────────┼──────────┼──────────────────────────┼──────────┤ ║
║    │ {AGENT_1}        │   ~{N}   │ {EXPERTISE}              │ ✅       │ ║
║    │ {AGENT_2}        │   ~{N}   │ {EXPERTISE}              │ ✅       │ ║
║    │ ...              │   ...    │ ...                      │ ...      │ ║
║    └──────────────────┴──────────┴──────────────────────────┴──────────┘ ║
║                                                                          ║
║    agents/cargo/ (CARGO AGENTS — Híbridos):                              ║
║    ┌──────────┬──────────────┬──────────────────────────┬──────────────┐ ║
║    │ ÁREA     │ AGENTE       │ DNA COMPOSITION          │ STATUS       │ ║
║    ├──────────┼──────────────┼──────────────────────────┼──────────────┤ ║
║    │ C-LEVEL  │ CFO          │ AH 60% + JL 40%          │ ✅           │ ║
║    │ C-LEVEL  │ CMO          │ JH 70% + AH 30%          │ ✅           │ ║
║    │ SALES    │ CLOSER       │ CG 40% + JM 40% + F 20%  │ ✅           │ ║
║    │ SALES    │ BDR          │ G4 50% + CG 30% + F 20%  │ ✅           │ ║
║    │ ...      │ ...          │ ...                      │ ...          │ ║
║    └──────────┴──────────────┴──────────────────────────┴──────────────┘ ║
║                                                                          ║
║    TOTAL: {N} PERSON Agents + {N} CARGO Agents = {TOTAL} Agentes        ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ INVENTÁRIO DE DOSSIERS                                              ║
║                                                                          ║
║    knowledge/external/dossiers/persons/:                                  ║
║    ┌────────────────────────────┬──────────┬────────────────────────────┐ ║
║    │ DOSSIER                   │ ELEMENTOS│ STATUS                      │ ║
║    ├────────────────────────────┼──────────┼────────────────────────────┤ ║
║    │ DOSSIER-{PERSON_1}        │   ~{N}   │ ✅ COMPLETE                 │ ║
║    │ DOSSIER-{PERSON_2}        │   ~{N}   │ ✅ COMPLETE                 │ ║
║    │ DOSSIER-{PERSON_3}        │   ~{N}   │ ⚠️ PARTIAL                  │ ║
║    └────────────────────────────┴──────────┴────────────────────────────┘ ║
║                                                                          ║
║    knowledge/external/dossiers/themes/:                                   ║
║    ┌──────────────────────────────────┬──────────────┬──────────────────┐ ║
║    │ DOSSIER                         │ COMPOSIÇÃO   │ STATUS           │ ║
║    ├──────────────────────────────────┼──────────────┼──────────────────┤ ║
║    │ DOSSIER-01-ESTRUTURA-TIME       │ Multi-source │ ✅ COMPLETE      │ ║
║    │ DOSSIER-02-PROCESSO-VENDAS      │ Multi-source │ ✅ COMPLETE      │ ║
║    │ DOSSIER-CLOSER-FRAMEWORK        │ CG+JM        │ ✅ COMPLETE      │ ║
║    │ DOSSIER-NEPQ-METHODOLOGY        │ JM 100%      │ 🆕 NOVO         │ ║
║    │ ...                             │ ...          │ ...              │ ║
║    └──────────────────────────────────┴──────────────┴──────────────────┘ ║
║                                                                          ║
║    TOTAL: {N} Person + {N} Theme = {TOTAL} Dossiers                      ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ CONFLITOS CROSS-SOURCE                                              ║
║                                                                          ║
║    ┌────┬────────────┬─────────────────────────┬──────────────────────┐  ║
║    │ #  │ TEMA       │ FONTE A vs FONTE B      │ RESOLUÇÃO            │  ║
║    ├────┼────────────┼─────────────────────────┼──────────────────────┤  ║
║    │  1 │ Close Rate │ CG: >30% │ JM: >25%     │ Contexto HT          │  ║
║    │  2 │ Show Rate  │ JH: >50% │ CG: >40%     │ Média 45%            │  ║
║    │  3 │ Comissão   │ {A}: 10% │ {B}: 15%     │ Por ticket           │  ║
║    └────┴────────────┴─────────────────────────┴──────────────────────┘  ║
║                                                                          ║
║    TOTAL: {N} conflitos | {N} resolvidos | {N} pendentes                 ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ MATRIZ DE CONEXÕES (Quem alimenta quem)                             ║
║                                                                          ║
║    ┌────────────────┬────────┬─────┬─────┬──────┬─────┬─────┬────────┐  ║
║    │                │ CLOSER │ BDR │ LNS │ NEPQ │ CRO │ CMO │ SALES-M│  ║
║    ├────────────────┼────────┼─────┼─────┼──────┼─────┼─────┼────────┤  ║
║    │ Jeremy Miner   │  40%   │  -  │  -  │ 100% │ 30% │  -  │    -   │  ║
║    │ Cole Gordon    │  40%   │ 30% │ 20% │   -  │ 40% │  -  │   40%  │  ║
║    │ Jeremy Haynes  │   -    │  -  │ 80% │   -  │  -  │ 70% │    -   │  ║
║    │ Alex Hormozi   │   -    │  -  │  -  │   -  │  -  │ 30% │   30%  │  ║
║    │ ...            │  ...   │ ... │ ... │  ... │ ... │ ... │   ...  │  ║
║    └────────────────┴────────┴─────┴─────┴──────┴─────┴─────┴────────┘  ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ ALERTAS E AÇÕES PENDENTES                                           ║
║                                                                          ║
║    🔴 CRÍTICO:                                                           ║
║    ├── [{N}] Conflitos não resolvidos                                    ║
║    └── [{N}] Agents com DNA desatualizado                                ║
║                                                                          ║
║    ⚠️ ATENÇÃO:                                                           ║
║    ├── [{N}] Dossiers PARTIAL (fontes com pouco conteúdo)                ║
║    ├── [{N}] Playbooks referenciados mas inexistentes                    ║
║    └── [{N}] Roles com threshold próximo de criar novo agent             ║
║                                                                          ║
║    ✅ INFO:                                                              ║
║    ├── [{N}] Novos agentes criados nesta sessão                          ║
║    ├── [{N}] Agentes enriquecidos                                        ║
║    └── [{N}] Novos dossiers de tema                                      ║
║                                                                          ║
╟────────────────────────────────────────────────────────────────────────────╢
║    ▸ PRÓXIMAS AÇÕES SUGERIDAS                                            ║
║                                                                          ║
║    [1] Ver detalhes de um agente específico                              ║
║    [2] Revisar conflitos pendentes                                       ║
║    [3] Iniciar criação de Playbooks                                      ║
║    [4] Consultar um agente (/ask {AGENT_NAME})                           ║
║    [5] Exportar relatório (/save)                                        ║
║    [6] Indexar todos os artefatos (/rag-health)                          ║
║                                                                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║  ✅ MCE SESSION COMPLETE — {N} fontes | {N} agentes | {N} dossiers       ║
║  "Se não foi logado, não foi processado." — JARVIS                       ║
╚════════════════════════════════════════════════════════════════════════════╝
```


---

## IMPLEMENTATION NOTES

### Variables

All variables use `{PLACEHOLDER}` syntax — replaced at render time.

| Variable | Source | Example |
|----------|--------|---------|
| `{SLUG}` | Person/entity slug (lowercase) | `cole-gordon` |
| `{SLUG_UPPER}` | Formatted slug | `COLE GORDON` |
| `{BUCKET_ICON}` | Bucket emoji + name | `📚 EXTERNAL` |
| `{HH:MM}` | Current time | `15:30` |
| `{N}`, `{TOTAL}`, `{DELTA}` | Numeric counters | `15`, `128`, `+23` |
| `{N_ANTES}`, `{N_DEPOIS}` | Before/after delta | `45`, `58` |
| `{%}` | Percentage | `39.5` |
| `{BAR_20}` | 20-char fill bar | `████████████░░░░░░░░` |
| `{BAR_30}` | 30-char fill bar | `████████████████████████░░░░░░` |
| `{PCT}` | Pipeline percentage | `83` |
| `{MISSION_ID}` | Mission identifier | `MISSION-2026-001` |
| `{C/U}` | Created/Updated | `CRIADO` |

### Conditional Sections

- If no new agents created, show: "Nenhum novo agente criado nesta execução"
- If no conflicts detected, show: "Nenhum conflito detectado ✅"
- If section has zero items, collapse to single status line

### Bar Rendering

```
Fill bar (20 chars): ████████████████░░░░  80%
Fill bar (30 chars): ██████████████████████████░░░░  87%
Tone bar (10 chars): ●●●●●●●○○○  7/10
Progress symbols:    ● done   ◉ current   ○ pending
```

### Width Contract

| Context | Inner Width | Total Width | Source |
|---------|-------------|-------------|--------|
| Step Logger (realtime) | PW=62 | 66 chars | mce_step_logger.py |
| Output Templates (post-step) | RW=72 | 76 chars | This file |
| Session Report (end-of-session) | RW=72 | 76 chars | mce_session_reporter.py |

### Execution Order

```
Per source (sequential):
  EXTRACTION SUMMARY  (Steps 3-5)  → Template 1
  PERSON AGENT        (Step 10.4)  → Template 2
  CARGO ENRICHMENT    (Step 10.4)  → Template 3
  THEME DOSSIERS      (Step 10.1-2)→ Template 4
  WORKSPACE SYNC      (Step 11)    → Template 5
  VALIDATION GATE     (Step 12)    → Template 6
  ────────────────────────────────────────
After ALL sources processed:
  SESSION CONSOLIDATION            → Template 7
```
