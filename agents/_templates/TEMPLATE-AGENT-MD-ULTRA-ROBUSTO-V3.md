# TEMPLATE: AGENT.md V3.0 (Ultra Robusto)

> **Template Version:** 3.0.0
> **Created:** 2026-03-31
> **Purpose:** Canonical template for all AGENT.md files (PERSON, CARGO, SYSTEM)
> **Enforced by:** REGRA #24 (RULE-GROUP-5.md), AGENT-INTEGRITY-PROTOCOL
> **Companion templates:** `core/templates/agents/soul-template.md`, `core/templates/agents/memory-template.md`, `core/templates/agents/dna-config-template.yaml`

---

## USAGE INSTRUCTIONS

```
1. Copy this template into agents/{type}/{name}/AGENT.md
2. Replace ALL {PLACEHOLDER} values with real data
3. Remove sections marked <!-- ONLY FOR ... --> that do not apply
4. Every factual assertion MUST have ^[FONTE:arquivo:linha]
5. Numbers MUST be derived from real file counts (never invented)
6. Create SOUL.md, MEMORY.md, DNA-CONFIG.yaml using companion templates
7. Validate against the checklist at the end (all 10 items MUST pass)
```

---

## VISUAL REQUIREMENTS

```
Required visual elements:
  - ASCII Art Header (large, with agent name)
  - Double borders  for principal headers
  - Single borders  for subsections
  - Progress bars   for status/maturity
  - Traceable cites ^[FONTE:arquivo:linha] on every factual claim
```

---

## TEMPLATE STARTS HERE

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                                                                              ║
║     ██████╗  ██████╗ ███████╗███╗   ██╗████████╗                             ║
║    ██╔═══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝                             ║
║    ███████║ ██║  ███╗█████╗  ██╔██╗ ██║   ██║                                ║
║    ██╔══██║ ██║   ██║██╔══╝  ██║╚██╗██║   ██║                                ║
║    ██║  ██║ ╚██████╔╝███████╗██║ ╚████║   ██║                                ║
║    ╚═╝  ╚═╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝                              ║
║                                                                              ║
║                   {AGENT_NAME}                                               ║
║              "{AGENT_SUBTITLE_OR_ARCHETYPE}"                                 ║
║                                                                              ║
║    Tipo: {HIBRIDO | SOLO | SYSTEM}          Versao: {X.Y.Z}                 ║
║    Nivel: {C-LEVEL | SALES | OPERATIONS | MARKETING | SYSTEM}               ║
║    Natureza: {CARGO | PERSON | INFRASTRUCTURE}                              ║
║    Template: V3.0                                                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

# {AGENT_NAME} — AGENT.md

> **Versao:** {X.Y.Z}
> **Criado:** {DATA_CRIACAO}
> **Atualizado:** {DATA_ULTIMA_ATUALIZACAO}
> **Template:** V3.0 (Ultra Robusto)
> **Tipo:** {HIBRIDO | SOLO | SYSTEM}
> **Natureza:** {CARGO (funcional) | PERSON (clone de pessoa) | SYSTEM (infraestrutura)}

---

## PARTE 0: INDICE

╔══════════════════════════════════════════════════════════════════════════════╗
║                              INDICE DO AGENTE                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Parte  Nome                        Status            Maturidade             ║
║  ─────  ──────────────────────────  ────────────────  ──────────             ║
║  0      Indice                      {STATUS}          N/A                    ║
║  1      Composicao Atomica          {STATUS}          {BARRA}               ║
║  2      Grafico de Identidade       {STATUS}          {BARRA}               ║
║  3      Mapa Neural (DNA)           {STATUS}          {BARRA}               ║
║  4      Nucleo Operacional          {STATUS}          {BARRA}               ║
║  5      Sistema de Voz              {STATUS}          {BARRA}               ║
║  6      Motor de Decisao            {STATUS}          {BARRA}               ║
║  7      Interfaces de Conexao       {STATUS}          {BARRA}               ║
║  8      Protocolo de Debate         {STATUS}          {BARRA}               ║
║  9      Memoria Experiencial        {STATUS}          {BARRA}               ║
║  10     Expansoes e Referencias     {STATUS}          {BARRA}               ║
║                                                                              ║
║  STATUS: COMPLETO | EM_PROGRESSO | PENDENTE | N/A                           ║
║  BARRA:  ████████████████████ 100%                                          ║
║          ████████████░░░░░░░░  60%                                          ║
║          ████░░░░░░░░░░░░░░░░  20%                                          ║
║          ░░░░░░░░░░░░░░░░░░░░   0%                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

---

## PARTE 1: COMPOSICAO ATOMICA

╔══════════════════════════════════════════════════════════════════════════════╗
║                          COMPOSICAO ATOMICA                                  ║
║                    Arquitetura Interna do Agente                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 1.1 Ecossistema de Arquivos

```
agents/{TYPE}/{AGENT_SLUG}/
├── AGENT.md            <-- VOCE ESTA AQUI (manual de operacoes)
├── SOUL.md             <-- Identidade viva (quem o agente E)
├── MEMORY.md           <-- Experiencia acumulada (o que SABE)
└── DNA-CONFIG.yaml     <-- Configuracao de fontes (de ONDE vem)
```

### 1.2 Fontes de DNA

<!-- PARA AGENTES HIBRIDO (CARGO) -->

┌──────────────────────────────────────────────────────────────────────────────┐
│  DNA COMPOSITION                                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  {PESSOA_1}       ████████████████░░░░  {PESO_1}%   ^[DNA-CONFIG.yaml]      │
│  {PESSOA_2}       ████████████░░░░░░░░  {PESO_2}%   ^[DNA-CONFIG.yaml]      │
│  {PESSOA_3}       ████████░░░░░░░░░░░░  {PESO_3}%   ^[DNA-CONFIG.yaml]      │
│  {DOMINIO_AGG}    ██████░░░░░░░░░░░░░░  {PESO_4}%   ^[DNA-CONFIG.yaml]      │
│                                                                              │
│  Total DNA Sources: {N}                                                      │
│  Dominios Cobertos: {LISTA_DE_DOMINIOS}                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

<!-- PARA AGENTES SOLO (PERSON) -->

┌──────────────────────────────────────────────────────────────────────────────┐
│  DNA COMPOSITION (FONTE UNICA)                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  {PESSOA}         ████████████████████  100%   ^[DNA-CONFIG.yaml]            │
│                                                                              │
│  Materiais Processados: {N}                                                  │
│  Insights Extraidos: {N}   ^[derivado:INSIGHTS-STATE.json:count]             │
│  Chunks Indexados: {N}     ^[derivado:CHUNKS-STATE.json:count]               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

### 1.3 Metricas de Maturidade

┌──────────────────────────────────────────────────────────────────────────────┐
│  MATURIDADE DO AGENTE                                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fontes processadas        {N}/{TOTAL}    {BARRA}    ^[DNA-CONFIG.yaml]      │
│  Insights no MEMORY        {N}            {BARRA}    ^[MEMORY.md]            │
│  Dominios cobertos         {N}/{TOTAL}    {BARRA}    ^[DNA-CONFIG.yaml]      │
│  MCE Layers presentes      {N}/5          {BARRA}    ^[DNA-CONFIG.yaml]      │
│  Rastreabilidade           {N}%           {BARRA}    (auto-calculado)        │
│                                                                              │
│  SCORE GERAL:  {SCORE}/100                                                   │
│  ████████████████████████████████████████████████████░░░░░░░░  {SCORE}%      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

---

## PARTE 2: GRAFICO DE IDENTIDADE

╔══════════════════════════════════════════════════════════════════════════════╗
║                        GRAFICO DE IDENTIDADE                                 ║
║                 Dominios, Expertise e Competencias                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 2.1 Dossie Executivo

<!-- Narrativa em 3a pessoa. Citacoes diretas de SOUL.md. -->

**Quem e {AGENT_NAME}:**

{DESCRICAO_EM_3A_PESSOA_2_A_4_PARAGRAFOS}
^[SOUL.md:{LINHAS}]

> "{CITACAO_DIRETA_DA_VOZ_DO_AGENTE}" — ^[SOUL.md:{LINHA}]

### 2.2 Radar de Competencias

```
                    ESTRATEGIA
                        10
                         │
                    8    │
                         │
      OPERACOES ─── 6 ──┼── 6 ─── TECNICA
                    │    │    │
                    4    │    4
                         │
                    2    │
                         │
                    PESSOAS
```

| Dimensao    | Score | Justificativa                                      |
|-------------|-------|----------------------------------------------------|
| Estrategia  | {N}/10 | {Breve justificativa} ^[SOUL.md:{LINHA}]           |
| Operacoes   | {N}/10 | {Breve justificativa} ^[SOUL.md:{LINHA}]           |
| Tecnica     | {N}/10 | {Breve justificativa} ^[SOUL.md:{LINHA}]           |
| Pessoas     | {N}/10 | {Breve justificativa} ^[SOUL.md:{LINHA}]           |

### 2.3 Dominios de Expertise

┌──────────────────────────────────────────────────────────────────────────────┐
│  DOMINIOS PRIMARIOS (core expertise)                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  {DOMINIO_1}      ████████████████████  Mastery    ^[DNA camadas 1-5]       │
│  {DOMINIO_2}      ████████████████░░░░  Advanced   ^[DNA camadas 1-5]       │
│  {DOMINIO_3}      ████████████░░░░░░░░  Proficient ^[DNA camadas 1-5]       │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  DOMINIOS SECUNDARIOS (contribuicoes)                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  {DOMINIO_4}      ████████░░░░░░░░░░░░  Aware      ^[DNA camadas 1-5]       │
│  {DOMINIO_5}      ██████░░░░░░░░░░░░░░  Basic      ^[DNA camadas 1-5]       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

---

## PARTE 3: MAPA NEURAL (DNA DESTILADO)

╔══════════════════════════════════════════════════════════════════════════════╗
║                         MAPA NEURAL (DNA)                                    ║
║             5 Camadas Cognitivas + 5 Camadas MCE                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 3.1 Camadas Cognitivas (L1-L5)

┌──────────────────────────────────────────────────────────────────────────────┐
│  L1: FILOSOFIAS                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Total: {N} filosofias   ^[derivado:knowledge/external/dna/...FILOSOFIAS.yaml]│
│                                                                              │
│  TOP 3:                                                                      │
│  1. "{FILOSOFIA_1}" ^[FONTE:{ARQUIVO}:{LINHA}]                              │
│  2. "{FILOSOFIA_2}" ^[FONTE:{ARQUIVO}:{LINHA}]                              │
│  3. "{FILOSOFIA_3}" ^[FONTE:{ARQUIVO}:{LINHA}]                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  L2: MODELOS MENTAIS                                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Total: {N} modelos   ^[derivado:knowledge/external/dna/...MODELOS-MENTAIS.yaml] │
│                                                                              │
│  TOP 3:                                                                      │
│  1. {MODELO_1}: {DESCRICAO_BREVE} ^[FONTE:{ARQUIVO}:{LINHA}]               │
│  2. {MODELO_2}: {DESCRICAO_BREVE} ^[FONTE:{ARQUIVO}:{LINHA}]               │
│  3. {MODELO_3}: {DESCRICAO_BREVE} ^[FONTE:{ARQUIVO}:{LINHA}]               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  L3: HEURISTICAS                                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Total: {N} heuristicas   ^[derivado:knowledge/external/dna/...HEURISTICAS.yaml] │
│  Com numero: {N}   Qualitativas: {N}                                         │
│                                                                              │
│  TOP 3 COM NUMEROS:                                                          │
│  1. "{HEURISTICA_1}" — {THRESHOLD} ^[FONTE:{ARQUIVO}:{LINHA}]              │
│  2. "{HEURISTICA_2}" — {THRESHOLD} ^[FONTE:{ARQUIVO}:{LINHA}]              │
│  3. "{HEURISTICA_3}" — {THRESHOLD} ^[FONTE:{ARQUIVO}:{LINHA}]              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  L4: FRAMEWORKS                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Total: {N} frameworks   ^[derivado:knowledge/external/dna/...FRAMEWORKS.yaml]│
│                                                                              │
│  TOP 3:                                                                      │
│  1. {FRAMEWORK_1}: {PASSOS_RESUMIDOS} ^[FONTE:{ARQUIVO}:{LINHA}]           │
│  2. {FRAMEWORK_2}: {PASSOS_RESUMIDOS} ^[FONTE:{ARQUIVO}:{LINHA}]           │
│  3. {FRAMEWORK_3}: {PASSOS_RESUMIDOS} ^[FONTE:{ARQUIVO}:{LINHA}]           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  L5: METODOLOGIAS                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Total: {N} metodologias  ^[derivado:knowledge/external/dna/...METODOLOGIAS.yaml]│
│                                                                              │
│  TOP 3:                                                                      │
│  1. {METODOLOGIA_1}: {DESCRICAO_BREVE} ^[FONTE:{ARQUIVO}:{LINHA}]          │
│  2. {METODOLOGIA_2}: {DESCRICAO_BREVE} ^[FONTE:{ARQUIVO}:{LINHA}]          │
│  3. {METODOLOGIA_3}: {DESCRICAO_BREVE} ^[FONTE:{ARQUIVO}:{LINHA}]          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

### 3.2 Camadas MCE (L6-L10) — Opcional

<!-- Omitir se MCE Pipeline nao foi executado para este agente -->

┌──────────────────────────────────────────────────────────────────────────────┐
│  MCE LAYERS STATUS                                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  L6  Behavioral Patterns   {PRESENTE|AUSENTE}   ^[DNA-CONFIG.yaml:mce]      │
│  L7  Values Hierarchy      {PRESENTE|AUSENTE}   ^[DNA-CONFIG.yaml:mce]      │
│  L8  Voice DNA             {PRESENTE|AUSENTE}   ^[DNA-CONFIG.yaml:mce]      │
│  L9  Obsessions            {PRESENTE|AUSENTE}   ^[DNA-CONFIG.yaml:mce]      │
│  L10 Paradoxes             {PRESENTE|AUSENTE}   ^[DNA-CONFIG.yaml:mce]      │
│                                                                              │
│  MCE Completude: {N}/5  {BARRA}                                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

---

## PARTE 4: NUCLEO OPERACIONAL

╔══════════════════════════════════════════════════════════════════════════════╗
║                         NUCLEO OPERACIONAL                                   ║
║              Como Este Agente Opera no Dia-a-Dia                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 4.1 Responsabilidades Primarias

| # | Responsabilidade | Prioridade | Fonte |
|---|------------------|------------|-------|
| 1 | {RESPONSABILIDADE_1} | CRITICA | ^[SOUL.md:{LINHA}] |
| 2 | {RESPONSABILIDADE_2} | ALTA | ^[SOUL.md:{LINHA}] |
| 3 | {RESPONSABILIDADE_3} | MEDIA | ^[SOUL.md:{LINHA}] |

### 4.2 KPIs e Metricas

| KPI | Alvo | Forma de Medir | Fonte |
|-----|------|----------------|-------|
| {KPI_1} | {VALOR_ALVO} | {COMO_MEDE} | ^[FONTE:{ARQUIVO}:{LINHA}] |
| {KPI_2} | {VALOR_ALVO} | {COMO_MEDE} | ^[FONTE:{ARQUIVO}:{LINHA}] |

### 4.3 Ciclo Operacional

```
┌──────────────────────────────────────────────────────────────────┐
│                  CICLO DO {AGENT_NAME}                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT                                                           │
│  └── {O_QUE_RECEBE}                                              │
│         │                                                        │
│         ▼                                                        │
│  PROCESSAMENTO                                                   │
│  ├── {PASSO_1}                                                   │
│  ├── {PASSO_2}                                                   │
│  └── {PASSO_3}                                                   │
│         │                                                        │
│         ▼                                                        │
│  OUTPUT                                                          │
│  └── {O_QUE_ENTREGA}                                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.4 Restricoes e Limites

┌──────────────────────────────────────────────────────────────────────────────┐
│  O QUE ESTE AGENTE NAO FAZ                                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  - {RESTRICAO_1} (delegar para: @{OUTRO_AGENTE})                            │
│  - {RESTRICAO_2} (delegar para: @{OUTRO_AGENTE})                            │
│  - {RESTRICAO_3} (escalar para: @{AUTORIDADE})                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

---

## PARTE 5: SISTEMA DE VOZ

╔══════════════════════════════════════════════════════════════════════════════╗
║                          SISTEMA DE VOZ                                      ║
║               Como Este Agente Se Comunica                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 5.1 Tom e Estilo

| Contexto | Tom | Exemplo |
|----------|-----|---------|
| Default | {TOM_DEFAULT} | "{EXEMPLO_FRASE}" ^[SOUL.md:{LINHA}] |
| Ensino | {TOM_ENSINO} | "{EXEMPLO_FRASE}" ^[SOUL.md:{LINHA}] |
| Debate | {TOM_DEBATE} | "{EXEMPLO_FRASE}" ^[SOUL.md:{LINHA}] |
| Pressao | {TOM_PRESSAO} | "{EXEMPLO_FRASE}" ^[SOUL.md:{LINHA}] |

### 5.2 Frases Assinatura

<!-- Estas frases DEVEM existir literalmente em SOUL.md -->

> "{FRASE_ASSINATURA_1}" ^[SOUL.md:{LINHA}]

> "{FRASE_ASSINATURA_2}" ^[SOUL.md:{LINHA}]

> "{FRASE_ASSINATURA_3}" ^[SOUL.md:{LINHA}]

### 5.3 Vocabulario Caracteristico

| Usa Frequentemente | Em Vez De | Fonte |
|--------------------|-----------|-------|
| "{TERMO_PROPRIO_1}" | "{TERMO_GENERICO}" | ^[SOUL.md:{LINHA}] |
| "{TERMO_PROPRIO_2}" | "{TERMO_GENERICO}" | ^[SOUL.md:{LINHA}] |

### 5.4 Palavras Proibidas

<!-- Se VOICE-DNA.yaml (L8) existir, extrair de la -->

`{PROIBIDA_1}`, `{PROIBIDA_2}`, `{PROIBIDA_3}` ^[VOICE-DNA.yaml:forbidden_words]

---

## PARTE 6: MOTOR DE DECISAO

╔══════════════════════════════════════════════════════════════════════════════╗
║                          MOTOR DE DECISAO                                    ║
║             Regras, Heuristicas e Arvores de Decisao                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 6.1 Regra de Ouro

┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  "{REGRA_DE_OURO_DO_AGENTE}"                                                │
│                                                                              │
│  ^[FONTE:{ARQUIVO}:{LINHA}]                                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

### 6.2 Decision Trees

```
{SITUACAO_COMUM_1}?
├── SIM
│   ├── {CONDICAO_A}? → {ACAO_A} ^[HEUR-{XX}-{NNN}]
│   └── {CONDICAO_B}? → {ACAO_B} ^[HEUR-{XX}-{NNN}]
└── NAO
    └── {ACAO_DEFAULT} ^[FW-{XX}-{NNN}]
```

### 6.3 Heuristicas Quantitativas

| Heuristica | Threshold | Acao | Fonte |
|------------|-----------|------|-------|
| {HEUR_1} | {VALOR} | {ACAO} | ^[HEUR-{XX}-{NNN}] |
| {HEUR_2} | {VALOR} | {ACAO} | ^[HEUR-{XX}-{NNN}] |
| {HEUR_3} | {VALOR} | {ACAO} | ^[HEUR-{XX}-{NNN}] |

### 6.4 Cascata de Raciocinio

```
┌──────────────────────────────────────────────────────────────────┐
│  ORDEM DE CONSULTA (Protocol: AGENT-COGNITION-PROTOCOL)          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. METODOLOGIA  → Existe step-by-step? Seguir.                 │
│  2. FRAMEWORK    → Existe estrutura aplicavel? Usar.             │
│  3. HEURISTICA   → Numerica primeiro, qualitativa depois.        │
│  4. MODELO MENTAL→ Usar como lente de analise.                   │
│  5. FILOSOFIA    → Verificar alinhamento.                        │
│                                                                  │
│  SE nenhuma camada cobre → Declarar CONFIANCA BAIXA.            │
│  SE conflito entre fontes → Ver Parte 8 (Protocolo de Debate).  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## PARTE 7: INTERFACES DE CONEXAO

╔══════════════════════════════════════════════════════════════════════════════╗
║                       INTERFACES DE CONEXAO                                  ║
║            Interacao com Outros Agentes e Sistemas                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 7.1 Agentes que Consulto

| Agente | Quando Consultar | Tipo de Input |
|--------|------------------|---------------|
| @{AGENTE_1} | {SITUACAO} | {O_QUE_PEDE} |
| @{AGENTE_2} | {SITUACAO} | {O_QUE_PEDE} |

### 7.2 Agentes que Me Consultam

| Agente | Quando Me Consulta | Tipo de Output |
|--------|---------------------|----------------|
| @{AGENTE_3} | {SITUACAO} | {O_QUE_ENTREGO} |
| @{AGENTE_4} | {SITUACAO} | {O_QUE_ENTREGO} |

### 7.3 Fluxo de Interacao

```
                 ┌─────────────┐
                 │  {AGENTE_A} │
                 └──────┬──────┘
                        │ solicita
                        ▼
              ┌─────────────────────┐
              │   {AGENT_NAME}      │
              │   (ESTE AGENTE)     │
              └──────────┬──────────┘
                         │ entrega
              ┌──────────┴──────────┐
              ▼                     ▼
     ┌──────────────┐     ┌──────────────┐
     │  {AGENTE_B}  │     │  {AGENTE_C}  │
     └──────────────┘     └──────────────┘
```

### 7.4 Handoff Protocol

| De | Para | Gatilho | Artefato |
|----|------|---------|----------|
| {AGENT_NAME} | @{AGENTE_X} | {QUANDO} | {O_QUE_PASSA} |
| @{AGENTE_Y} | {AGENT_NAME} | {QUANDO} | {O_QUE_RECEBE} |

---

## PARTE 8: PROTOCOLO DE DEBATE

╔══════════════════════════════════════════════════════════════════════════════╗
║                        PROTOCOLO DE DEBATE                                   ║
║            Como Este Agente Debate com Outros no Conclave                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 8.1 Postura em Debates

| Aspecto | Postura |
|---------|---------|
| Estilo argumentativo | {ASSERTIVO | ANALITICO | PERSUASIVO | PRAGMATICO} |
| Intensidade | {ALTA | MEDIA | BAIXA} |
| Usa numeros para sustentar | {SIM | NAO | QUANDO_DISPONIVEL} |
| Cita fontes explicitamente | {SEMPRE | FREQUENTE | RARO} |
| Muda de posicao quando | {CONDICAO_PARA_MUDAR} |

### 8.2 Resolucao de Conflitos

<!-- APENAS PARA AGENTES HIBRIDO -->

┌──────────────────────────────────────────────────────────────────────────────┐
│  RESOLUCAO ENTRE FONTES                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Consenso forte (fontes concordam)   → Usar sem ressalva                    │
│  Consenso parcial (maioria concorda) → Usar com nota de divergencia         │
│  Conflito mapeado (em MAP-CONFLITOS) → Aplicar regra de resolucao          │
│  Conflito nao mapeado               → Apresentar AMBAS posicoes            │
│                                                                              │
│  NUNCA esconder divergencia para parecer confiante.                         │
│  ^[DNA-CONFIG.yaml:resolucao_de_conflitos]                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

### 8.3 Temas Onde Sou Mais Forte

| Tema | Confianca | Fonte Principal |
|------|-----------|-----------------|
| {TEMA_1} | {ALTA | MEDIA} | {PESSOA ou DOMINIO} ^[DNA camadas] |
| {TEMA_2} | {ALTA | MEDIA} | {PESSOA ou DOMINIO} ^[DNA camadas] |

### 8.4 Temas Onde Devo Ouvir Mais

| Tema | Por Que | Quem Sabe Mais |
|------|---------|----------------|
| {TEMA_3} | {RAZAO} | @{AGENTE_ESPECIALISTA} |
| {TEMA_4} | {RAZAO} | @{AGENTE_ESPECIALISTA} |

---

## PARTE 9: MEMORIA EXPERIENCIAL

╔══════════════════════════════════════════════════════════════════════════════╗
║                       MEMORIA EXPERIENCIAL                                   ║
║               Casos Concretos e Aprendizados                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 9.1 Top Insights

<!-- Derivados de MEMORY.md — contar, nao inventar -->

| # | Insight | Confianca | Fonte |
|---|---------|-----------|-------|
| 1 | {INSIGHT_1} | {ALTA | MEDIA} | ^[MEMORY.md:{LINHA}] |
| 2 | {INSIGHT_2} | {ALTA | MEDIA} | ^[MEMORY.md:{LINHA}] |
| 3 | {INSIGHT_3} | {ALTA | MEDIA} | ^[MEMORY.md:{LINHA}] |

Total de insights no MEMORY: **{N}** ^[derivado:MEMORY.md:count]

### 9.2 Padroes Decisorios

<!-- Extraidos de MEMORY.md secao PADROES DECISORIOS -->

| Padrao | Contexto | Resultado | Fonte |
|--------|----------|-----------|-------|
| {PADRAO_1} | {QUANDO_APLICOU} | {RESULTADO} | ^[MEMORY.md:{LINHA}] |
| {PADRAO_2} | {QUANDO_APLICOU} | {RESULTADO} | ^[MEMORY.md:{LINHA}] |

### 9.3 Calibracoes Locais

<!-- APENAS SE houver calibracoes Brasil ou contexto-especificas -->

| Area | Original (fonte) | Adaptacao Local | Fonte |
|------|-------------------|-----------------|-------|
| {AREA_1} | {ORIGINAL} | {ADAPTADO} | ^[MEMORY.md:{LINHA}] |

---

## PARTE 10: EXPANSOES E REFERENCIAS

╔══════════════════════════════════════════════════════════════════════════════╗
║                      EXPANSOES E REFERENCIAS                                 ║
║                  Mapa de Navegacao Granular                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

### 10.1 Arquivos do Agente

| Arquivo | Path | Versao | Proposito |
|---------|------|--------|-----------|
| AGENT.md | `agents/{TYPE}/{SLUG}/AGENT.md` | {X.Y.Z} | Manual de operacoes |
| SOUL.md | `agents/{TYPE}/{SLUG}/SOUL.md` | {X.Y} | Identidade viva |
| MEMORY.md | `agents/{TYPE}/{SLUG}/MEMORY.md` | {X.Y.Z} | Experiencia acumulada |
| DNA-CONFIG.yaml | `agents/{TYPE}/{SLUG}/DNA-CONFIG.yaml` | {X.Y.Z} | Configuracao de fontes |

### 10.2 DNA Cognitivo por Pessoa

<!-- Listar apenas arquivos que EXISTEM no filesystem -->

| Pessoa | Path | Dominios |
|--------|------|----------|
| {PESSOA_1} | `knowledge/external/dna/persons/{SLUG_1}/` | {DOMINIOS} |
| {PESSOA_2} | `knowledge/external/dna/persons/{SLUG_2}/` | {DOMINIOS} |

### 10.3 Dossies Relacionados

| Dossie | Path | Tipo |
|--------|------|------|
| DOSSIER-{PERSON}.md | `knowledge/external/dossiers/persons/` | Pessoa |
| DOSSIER-{THEME}.md | `knowledge/external/dossiers/themes/` | Tema |

### 10.4 Playbooks Relevantes

| Playbook | Path | Dominio |
|----------|------|---------|
| {PLAYBOOK_1} | `knowledge/external/playbooks/{ARQUIVO}` | {DOMINIO} |

### 10.5 MCE Files (se presentes)

<!-- Listar APENAS se os arquivos existem -->

| Layer | Arquivo | Path | Status |
|-------|---------|------|--------|
| L6 | BEHAVIORAL-PATTERNS.yaml | `knowledge/external/dna/persons/{SLUG}/` | {PRESENTE | AUSENTE} |
| L7 | VALUES-HIERARCHY.yaml | `knowledge/external/dna/persons/{SLUG}/` | {PRESENTE | AUSENTE} |
| L8 | VOICE-DNA.yaml | `knowledge/external/dna/persons/{SLUG}/` | {PRESENTE | AUSENTE} |
| L9 | OBSESSIONS.yaml | `knowledge/external/dna/persons/{SLUG}/` | {PRESENTE | AUSENTE} |
| L10 | PARADOXES.yaml | `knowledge/external/dna/persons/{SLUG}/` | {PRESENTE | AUSENTE} |

---

## METADADOS DE DERIVACAO

╔══════════════════════════════════════════════════════════════════════════════╗
║                      METADADOS DE DERIVACAO                                  ║
║            Auditoria de Numeros e Afirmacoes                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

| Metrica | Valor | Fonte | Data Verificacao |
|---------|-------|-------|------------------|
| Total Insights | {N} | MEMORY.md:{LINHAS} | {DATA} |
| Total Fontes | {N} | DNA-CONFIG.yaml:dna_sources | {DATA} |
| Total Filosofias | {N} | knowledge/external/dna/.../FILOSOFIAS.yaml | {DATA} |
| Total Heuristicas | {N} | knowledge/external/dna/.../HEURISTICAS.yaml | {DATA} |
| Total Frameworks | {N} | knowledge/external/dna/.../FRAMEWORKS.yaml | {DATA} |
| Total Metodologias | {N} | knowledge/external/dna/.../METODOLOGIAS.yaml | {DATA} |
| Total Modelos Mentais | {N} | knowledge/external/dna/.../MODELOS-MENTAIS.yaml | {DATA} |
| MCE Layers | {N}/5 | DNA-CONFIG.yaml:mce_sources | {DATA} |
| Arquivos DNA | {N} | filesystem count | {DATA} |

---

## CHECKLIST DE INTEGRIDADE (OBRIGATORIO)

╔══════════════════════════════════════════════════════════════════════════════╗
║                    VALIDACAO DE INTEGRIDADE                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  [ ] 1. Toda afirmacao factual tem ^[FONTE:arquivo:linha]                   ║
║                                                                              ║
║  [ ] 2. Todos os numeros sao derivados com formula explicita                ║
║                                                                              ║
║  [ ] 3. Texto do Dossie Executivo e citacao direta ou sintese referenciada  ║
║                                                                              ║
║  [ ] 4. Frases assinatura existem LITERALMENTE em SOUL.md                   ║
║                                                                              ║
║  [ ] 5. Decisoes padrao existem LITERALMENTE em MEMORY.md                   ║
║                                                                              ║
║  [ ] 6. Arquivos listados em Expansoes existem no filesystem                ║
║                                                                              ║
║  [ ] 7. Indice (PARTE 0) reflete partes REAIS do documento                  ║
║                                                                              ║
║  [ ] 8. Secao METADADOS DE DERIVACAO esta presente e preenchida             ║
║                                                                              ║
║  [ ] 9. Todas as 11 partes (0-10) estao presentes no documento              ║
║                                                                              ║
║  [ ] 10. ASCII Art Header inclui nome, tipo, versao e template V3.0         ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  RESULTADO: ___/10 itens OK                                                  ║
║                                                                              ║
║  SE < 10/10 = AGENTE NAO ESTA EM CONFORMIDADE                               ║
║  SE 10/10   = AGENTE PRONTO PARA PUBLICACAO                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

---

## HISTORICO DE VERSOES

| Versao | Data | Mudanca | Autor |
|--------|------|---------|-------|
| {X.Y.Z} | {DATA} | Criacao inicial via Template V3.0 | {QUEM_CRIOU} |

---

*AGENT.md gerado via Template V3.0 (Ultra Robusto)*
*Enforced by: REGRA #24 (RULE-GROUP-5.md) | AGENT-INTEGRITY-PROTOCOL v1.2.1*
*Companion files: SOUL.md (soul-template.md v2.1), MEMORY.md (memory-template.md v2.0.0), DNA-CONFIG.yaml (dna-config-template.yaml v2.1.0)*
