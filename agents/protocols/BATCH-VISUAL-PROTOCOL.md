# BATCH-VISUAL-PROTOCOL.md

> **Versão:** 2.0.0
> **Data:** 2026-01-05
> **Status:** OFICIAL - FONTE DE VERDADE
> **Decisão:** DEC-2026-0056 (atualizado DEC-2026-0105)

---

## ⚠️ QUICK REFERENCE - 3 TEMPLATES OFICIAIS

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                       ║
║   📄 ESTE DOCUMENTO É A FONTE DE VERDADE PARA TODOS OS LOGS                          ║
║   ❌ NÃO usar LOG-STRUCTURE-PROTOCOL.md para templates de log                         ║
║   ❌ NÃO inventar formatos novos                                                       ║
║   ✅ SEMPRE consultar este documento antes de gerar logs                              ║
║                                                                                       ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                       ║
║   TEMPLATE 1: LOG DE BATCH                                                            ║
║   ├─ Seções: 10                                                                       ║
║   ├─ Quando: Ao final de CADA batch                                                   ║
║   ├─ Output: /logs/batches/BATCH-NNN.md                                            ║
║   └─ Scroll → Seção "Estrutura Completa (10 Seções)"                                  ║
║                                                                                       ║
║   TEMPLATE 2: LOG DE SOURCE                                                           ║
║   ├─ Seções: 12                                                                       ║
║   ├─ Quando: TODOS batches de uma fonte concluídos                                    ║
║   ├─ Output: /logs/SOURCES/SOURCE-{FONTE}.md                                       ║
║   └─ Scroll → Seção "LOG DE SOURCE (Quando Fonte Completa) - 12 SEÇÕES"              ║
║                                                                                       ║
║   TEMPLATE 3: LOG DE MISSION                                                          ║
║   ├─ Seções: Cross-source + síntese                                                   ║
║   ├─ Quando: TODAS as fontes processadas                                              ║
║   ├─ Output: /logs/MISSIONS/MISSION-{ID}-FINAL.md                                  ║
║   └─ Scroll → Seção "LOG DE MISSÃO (Quando Missão Completa)"                         ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

### Hierarquia Visual

```
BATCH (cada batch)                   SOURCE (fonte completa)           MISSION (final)
─────────────────                    ────────────────────              ─────────────────

BATCH-001.md ─┐
BATCH-002.md ─┼─→ [Fonte OK] ──→ SOURCE-JEREMY-HAYNES.md ─┐
BATCH-003.md ─┤                                           │
BATCH-004.md ─┘                                           │
                                                          │
BATCH-005.md ─┐                                           │
...          ─┤                                           │
BATCH-020.md ─┘                                           │
                                                          │
BATCH-021.md ─┐                                           │
BATCH-028.md ─┘
```

---

## Propósito

Define o formato visual OBRIGATÓRIO para **TODOS** os tipos de logs do Pipeline Jarvis:
1. Logs de BATCH (cada batch individual)
2. Logs de SOURCE (fonte completa)
3. Logs de MISSION (missão completa)

Este formato é usado para comunicar progresso, métricas e extração de conhecimento de forma clara e consistente.

---

## Estrutura Completa (10 Seções)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. HEADER ASCII           → Identificação do batch + qualidade        │
│  2. MISSION PROGRESS       → Fases + barra de progresso                │
│  3. BATCH SUMMARY          → Source, subpasta, arquivos, anomalias     │
│  4. FRAMEWORKS EXTRAÍDOS   → Frameworks completos com estrutura        │
│  5. HEURÍSTICAS ★          → Top 15 com rating de estrelas             │
│  6. FILOSOFIAS             → Citações com atribuição                   │
│  7. PREVIEW DE IMPACTO     → 4 grids (Temas/Dossiês/Agentes/SOWs)      │
│  8. ACUMULADO DA MISSÃO    → Métricas totais + status por fonte        │
│  9. JARVIS STATUS          → Versão, checkpoint, decisões novas        │
│  10. PRÓXIMO               → Opções para próximo batch                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. HEADER ASCII

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│     ██████╗  █████╗ ████████╗ ██████╗██╗  ██╗    ███╗   ██╗███╗   ██╗       │
│     ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║    ████╗  ██║████╗  ██║       │
│     ██████╔╝███████║   ██║   ██║     ███████║    ██╔██╗ ██║██╔██╗ ██║       │
│     ██╔══██╗██╔══██║   ██║   ██║     ██╔══██║    ██║╚██╗██║██║╚██╗██║       │
│     ██████╔╝██║  ██║   ██║   ╚██████╗██║  ██║    ██║ ╚████║██║ ╚████║       │
│     ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝    ╚═╝  ╚═══╝╚═╝  ╚═══╝       │
│                                                                              │
│              {DESCRIÇÃO DO BATCH - SOURCE + SUBPASTA}                        │
│                                                                              │
│     {QUALIDADE_EMOJI} {QUALIDADE}                    {TIMESTAMP}            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Qualidade e Emojis:**
| Qualidade | Emoji | ROI |
|-----------|-------|-----|
| LEGENDARY | 🏆 | > 0.20 com frameworks completos |
| EXCELLENT | ⭐ | 0.35+ |
| GOOD | ✅ | 0.25-0.34 |
| ACCEPTABLE | 🔶 | 0.15-0.24 |
| LOW | ⚠️ | < 0.15 |

---

## 2. MISSION PROGRESS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  MISSION PROGRESS                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│      ┏━━━━━━━━━━━┓    ┏━━━━━━━━━━━┓    ┏━━━━━━━━━━━┓    ┏━━━━━━━━━━━┓    ┏━━━━━━━━━━━┓   │
│      ┃    ✅     ┃    ┃    ✅     ┃    ┃    ✅     ┃    ┃   ⚡🔄    ┃    ┃    ⏳     ┃   │
│      ┃  PHASE 1  ┃ →  ┃  PHASE 2  ┃ →  ┃  PHASE 3  ┃ →  ┃  PHASE 4  ┃ →  ┃  PHASE 5  ┃   │
│      ┗━━━━━━━━━━━┛    ┗━━━━━━━━━━━┛    ┗━━━━━━━━━━━┛    ┗━━━━━━━━━━━┛    ┗━━━━━━━━━━━┛   │
│       INVENTÁRIO       DOWNLOAD       ORGANIZAÇÃO       PIPELINE       ALIMENTAÇÃO      │
│                                                         BATCH {NN}                       │
│                                                                              │
│      ████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  {XX.X}%  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Ícones de Status:**
| Status | Ícone |
|--------|-------|
| Completo | ✅ |
| Em andamento | ⚡🔄 |
| Pendente | ⏳ |

**Cálculo da Barra:**
- Total de caracteres: 60
- Preenchidos = (progress_percent / 100) * 60
- Vazios = 60 - preenchidos

---

## 3. BATCH SUMMARY

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BATCH-{NNN} SUMMARY                                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   📂 SOURCE         {Nome da Fonte}                                          │
│   📁 SUBPASTA       {Subpasta específica}                                    │
│   📄 ARQUIVOS       {N} processados {detalhes}                               │
│   ⚠️  ANOMALIA       {Descrição se houver}                                   │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────┐   ┌─────────────────────────────┐         │
│   │  MÉTRICAS DO BATCH          │   │  SPEAKERS DETECTADOS        │         │
│   ├─────────────────────────────┤   ├─────────────────────────────┤         │
│   │  Chunks Est.     {NNN}      │   │  {Nome}        {Role}       │         │
│   │  Insights        {NN}       │   │  {Nome}        {Role}       │         │
│   │  Heurísticas ★   {NN}       │   │  {Nome}        {Role}       │         │
│   │  Frameworks      {NN}       │   │  {Nome}        {Role}       │         │
│   │  Filosofias      {N}        │   │  {Nome}        {Role}       │         │
│   │  ROI             {X.XX}     │   │                             │         │
│   └─────────────────────────────┘   └─────────────────────────────┘         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. FRAMEWORKS EXTRAÍDOS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  FRAMEWORKS EXTRAÍDOS                                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  {NOME DO FRAMEWORK} ({Autor})                                     │    │
│   ├────────────────────────────────────────────────────────────────────┤    │
│   │  1. {Step 1}           → {Descrição}                               │    │
│   │  2. {Step 2}           → {Descrição}                               │    │
│   │  3. {Step 3}           → {Descrição}                               │    │
│   │  ...                                                               │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│   [Repetir para cada framework principal - máximo 3-4 por batch]            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Variante com barra visual (para timing/percentuais):**
```
│   │  {Label}              {valor}   ████████████░░░░░░░░░░░░░░░   │    │
```

---

## 5. HEURÍSTICAS ★

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  HEURÍSTICAS ★ (TOP 15)                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ★★★★★  {valor}        {Descrição da heurística}                           │
│   ★★★★★  {valor}        {Descrição da heurística}                           │
│   ★★★★☆  {valor}        {Descrição da heurística}                           │
│   ★★★★☆  {valor}        {Descrição da heurística}                           │
│   ★★★☆☆  {valor}        {Descrição da heurística}                           │
│   ...                                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Rating de Estrelas:**
| Rating | Critério |
|--------|----------|
| ★★★★★ | Benchmark crítico, validado, acionável imediatamente |
| ★★★★☆ | Muito útil, contexto específico |
| ★★★☆☆ | Útil, mas precisa adaptação |
| ★★☆☆☆ | Interessante, baixa prioridade |
| ★☆☆☆☆ | Referência apenas |

---

## 6. FILOSOFIAS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  FILOSOFIAS                                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   💬 "{Citação exata}"                                          — {Autor}   │
│   💬 "{Citação exata}"                                          — {Autor}   │
│   💬 "{Citação exata}"                                          — {Autor}   │
│   ...                                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. PREVIEW DE IMPACTO

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PREVIEW DE IMPACTO (PHASE 5)                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────────────────────────────┐  ┌───────────────────────────────┐  │
│   │  TEMAS A INCREMENTAR              │  │  DOSSIÊS A ATUALIZAR          │  │
│   ├───────────────────────────────────┤  ├───────────────────────────────┤  │
│   │  {TEMA}              +{NN} ins.   │  │  DOSSIER-{NOME}       +{NNN}  │  │
│   │  {TEMA}              +{NN} ins.   │  │  DOSSIER-{NOME}       +{NN}   │  │
│   │  {TEMA}              +{NN} ins.   │  │  DOSSIER-{NOME}       +{NN}   │  │
│   └───────────────────────────────────┘  └───────────────────────────────┘  │
│                                                                              │
│   ┌───────────────────────────────────┐  ┌───────────────────────────────┐  │
│   │  AGENTES A ALIMENTAR              │  │  ORG-LIVE SOWs                │  │
│   ├───────────────────────────────────┤  ├───────────────────────────────┤  │
│   │  {AGENTE}       {seções}          │  │  {SOW}         +{N} resp/mét  │  │
│   │  {AGENTE}       {seções}          │  │  {SOW}         +{N} resp/mét  │  │
│   └───────────────────────────────────┘  └───────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. ACUMULADO DA MISSÃO

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ACUMULADO DA MISSÃO                                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐ │
│   │   BATCHES      │ │    FILES       │ │   INSIGHTS     │ │  HEURÍSTICAS │ │
│   │      {NN}      │ │     {NNN}      │ │     {NNNN}     │ │     {NNN}    │ │
│   └────────────────┘ └────────────────┘ └────────────────┘ └──────────────┘ │
│                                                                              │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐ │
│   │  FRAMEWORKS    │ │  FILOSOFIAS    │ │    MODELS      │ │   PERSONS    │ │
│   │     {NNN}      │ │     {NNN}      │ │      {NN}      │ │     {NN}     │ │
│   └────────────────┘ └────────────────┘ └────────────────┘ └──────────────┘ │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  SOURCES STATUS                                                    │    │
│   ├────────────────────────────────────────────────────────────────────┤    │
│   │  {✅/🔄/⏳} {Source}     {STATUS}     │ {N} insights  │ {N} batches │    │
│   │  {✅/🔄/⏳} {Source}     {STATUS}     │ {N} insights  │ {N} batches │    │
│   │  ...                                                               │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. JARVIS STATUS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🤖 JARVIS STATUS                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   VERSION        {X.X.X}                                                     │
│   CHECKPOINT     CP-{YYYY-MM-DD}-BATCH{NNN}                                  │
│   HEALTH         {🟢/🟡/🔴} {STATUS}                                         │
│                                                                              │
│   DECISÕES NOVAS (DEC-{NNNN} a DEC-{NNNN}):                                  │
│   ├── {Decisão 1}                                                            │
│   ├── {Decisão 2}                                                            │
│   ├── {Decisão 3}                                                            │
│   └── {Decisão N}                                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. PRÓXIMO

```
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ⚡ PRÓXIMO: BATCH-{NNN}                                                    │
│                                                                              │
│   OPÇÃO A: {Descrição da opção A}                                            │
│   OPÇÃO B: {Descrição da opção B}                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## LOG DE SOURCE (Quando Fonte Completa) - 12 SEÇÕES OBRIGATÓRIAS

> **⚠️ IMPORTANTE:** Este é o formato OFICIAL e COMPLETO para logs de SOURCE.
> **NÃO** usar LOG-STRUCTURE-PROTOCOL.md - este protocolo é a fonte de verdade.

Quando TODOS os batches de uma fonte são processados, gerar LOG DE SOURCE com **12 seções obrigatórias**:

### ESTRUTURA COMPLETA (12 Seções)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1️⃣  HEADER ASCII         → SOURCE + JARVIS version + timestamp        │
│  2️⃣  PROGRESS BAR         → 5 fases + sources completed                │
│  3️⃣  SOURCE HEADER        → ASCII da fonte + quote característico      │
│  4️⃣  BATCHES PROCESSADOS  → Todos os batches em boxes                  │
│  5️⃣  SPEAKERS DETECTADOS  → Tabela com role e frameworks               │
│  6️⃣  GRIDS DE MÉTRICAS    → 4 grids (Volume/dna/Knowledge/Agentes)     │
│  7️⃣  QUALITY INDICATORS   → Health check com indicadores              │
│  8️⃣  FRAMEWORKS EXTRAÍDOS → Lista visual de todos frameworks          │
│  9️⃣  HEURÍSTICAS ★        → Top heurísticas com números e estrelas    │
│  🔟  RASTREABILIDADE      → Diagrama de fluxo INBOX→PROCESSING→LOGS   │
│  1️⃣1️⃣ PRÓXIMOS PASSOS     → Comando + próxima fonte + status          │
│  📋  BRIEFING EXECUTIVO   → Em uma frase + decisões + próximos        │
└─────────────────────────────────────────────────────────────────────────┘
```

### TEMPLATE COMPLETO:

```markdown
# SOURCE-{ID} | {NOME DA FONTE} - FONTE COMPLETA

╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║   ███████╗ ██████╗ ██╗   ██╗██████╗  ██████╗███████╗     ██╗██████╗                             ║
║   ██╔════╝██╔═══██╗██║   ██║██╔══██╗██╔════╝██╔════╝     ██║██╔══██╗                            ║
║   ███████╗██║   ██║██║   ██║██████╔╝██║     █████╗       ██║██║  ██║                            ║
║   ╚════██║██║   ██║██║   ██║██╔══██╗██║     ██╔══╝       ██║██║  ██║                            ║
║   ███████║╚██████╔╝╚██████╔╝██║  ██║╚██████╗███████╗     ██║██████╔╝                            ║
║   ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝     ╚═╝╚═════╝                             ║
║                                                                                                  ║
║                        🤖 JARVIS MISSION CONTROL v{VERSION}                                      ║
║                        📊 SOURCE COMPLETE - {NOME}                                               ║
║                                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════╣
║  📋 {MISSION-ID}                                          🕐 {TIMESTAMP}                        ║
║  📊 Batches: {RANGE} ({N} total)                          ⏱️  Source: 100% COMPLETE             ║
║  📁 Source: {NOME}                                        📍 Mission Progress: {XX.X}%          ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

══════════════════════════════════════════════════════════════════════════════
1️⃣ HEADER - Identificação da Fonte
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  SOURCE IDENTIFICATION                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Mission ID:      {MISSION-ID}                                                  │
│  Executor:        JARVIS v{VERSION}                                             │
│  Source ID:       SOURCE-{ID}                                                   │
│                                                                                 │
│  Source:          {Nome completo}                                               │
│  Fundadores:      {Lista}                                                       │
│  Especialidade:   {Área de expertise}                                           │
│  Mercado:         {Mercado principal}                                           │
│                                                                                 │
│  Cursos:          {Lista de cursos/módulos}                                     │
│  Arquivos:        {N} válidos                                                   │
│  Batches:         {N} (BATCH-XXX → BATCH-YYY)                                   │
│                                                                                 │
│  Started:         {DATA/HORA}                                                   │
│  Completed:       {DATA/HORA}                                                   │
│  Status:          ✅ COMPLETE                                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
2️⃣ PROGRESS BAR - Visão Geral das 5 Fases
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  PHASE 1        PHASE 2        PHASE 3        PHASE 4 ⚡      PHASE 5          │
│  INVENTORY      DOWNLOAD       ORGANIZATION   PIPELINE        FEEDING          │
│                                                                                 │
│     ✅             ✅              ✅            🔄              ⏳             │
│  COMPLETE       COMPLETE        COMPLETE     IN PROGRESS      PENDING          │
│                                                                                 │
│  ████████████   ████████████   ████████████   █████████░░░   ░░░░░░░░░░░░     │
│    100%           100%           100%          {XX.X}%         0%              │
│                                                                                 │
│  ──────────────────────────────────────────────────────────────────────────    │
│  OVERALL PROGRESS:  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░  {XX.X}%         │
│                                                                                 │
│  SOURCES COMPLETED:                                                             │
│  ├─ ✅ {SOURCE 1}        ({N} files, {N} batches)  BATCH-XXX → YYY             │
│  ├─ ✅ {SOURCE 2}        ({N} files, {N} batches)  BATCH-XXX → YYY             │
│  └─ ✅ {SOURCE ATUAL}    ({N} files, {N} batches)  BATCH-XXX → YYY ← ATUAL     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
3️⃣ SOURCE HEADER - {Nome} (Fonte Completa)
══════════════════════════════════════════════════════════════════════════════

╔═════════════════════════════════════════════════════════════════════════════════╗
║                                                                                 ║
║   {ASCII ART DO NOME DA FONTE}                                                  ║
║                                                                                 ║
║   ✅ SOURCE COMPLETE                                          {QUALITY}         ║
║                                                                                 ║
║   "{Quote característico que resume a fonte}"                                   ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝

══════════════════════════════════════════════════════════════════════════════
4️⃣ BATCHES PROCESSADOS - {N} Batches {SOURCE}
══════════════════════════════════════════════════════════════════════════════

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  {SOURCE} - {N} BATCHES PROCESSADOS                                   STATUS  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                               ┃
┃  ┌──────────────────────────────────────────────────────────────────────────┐ ┃
┃  │ BATCH-XXX │ {Descrição}                                 {QUALITY}       │ ┃
┃  │     {N} arquivos │ {N} insights │ {Frameworks principais}              │ ┃
┃  │     OUTPUT: {O que foi extraído}                                        │ ┃
┃  └──────────────────────────────────────────────────────────────────────────┘ ┃
┃                              ↓                                                ┃
┃  [REPETIR PARA CADA BATCH]                                                    ┃
┃                                                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

══════════════════════════════════════════════════════════════════════════════
5️⃣ SPEAKERS DETECTADOS - {N} Instrutores
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  🎤 SPEAKERS {SOURCE}                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────┬─────────────────┬─────────────────────┬──────────────────────────────┐ │
│  │ #  │ Speaker          │ Role               │ Frameworks Associados        │ │
│  ├────┼─────────────────┼─────────────────────┼──────────────────────────────┤ │
│  │  1 │ {Nome}           │ {Role}             │ {Frameworks}                 │ │
│  │  2 │ {Nome}           │ {Role}             │ {Frameworks}                 │ │
│  │... │ ...              │ ...                │ ...                          │ │
│  └────┴─────────────────┴─────────────────────┴──────────────────────────────┘ │
│                                                                                 │
│  ✨ DESTAQUE: {Speaker principal} ({N}+ insights)                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
6️⃣ GRIDS DE MÉTRICAS - 4 Tabelas Consolidadas
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  📊 GRID 1: VOLUME (Arquivos, Chunks, Insights)                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┬──────────────┬──────────────┬──────────────┐              │
│  │    Métrica      │  SOURCE      │  ACUMULADO   │   TARGET     │              │
│  ├─────────────────┼──────────────┼──────────────┼──────────────┤              │
│  │ 📄 Arquivos     │      {N}     │     {N}      │     {N}      │              │
│  │ 🧩 Chunks       │    ~{N}      │   ~{N}       │   ~{N}       │              │
│  │ 💡 Insights     │     {N}      │    {N}       │   ~{N}+      │              │
│  │ 📦 Batches      │      {N}     │      {N}     │      {N}     │              │
│  └─────────────────┴──────────────┴──────────────┴──────────────┘              │
│  ROI (insights/chunk): {X.XX} [🟢 {STATUS}]                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  🧬 GRID 2: DNA COGNITIVO (5 Camadas)                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┬──────────────┬──────────────┐                          │
│  │      Camada         │  SOURCE      │  ACUMULADO   │                          │
│  ├─────────────────────┼──────────────┼──────────────┤                          │
│  │ 🧠 Filosofias       │      {N}     │      {N}     │                          │
│  │ 🔄 Modelos Mentais  │      {N}     │      {N}     │                          │
│  │ ★  Heurísticas      │     {N}      │     {N}      │  ← Com números!          │
│  │ 📐 Frameworks       │      {N}     │      {N}     │                          │
│  │ 📋 Metodologias     │      {N}     │      {N}     │                          │
│  └─────────────────────┴──────────────┴──────────────┘                          │
│  ★ Densidade de heurísticas: {XX}% do total de insights                         │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  📚 GRID 3: KNOWLEDGE (Narrativas, Temas)                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┬──────────────┬──────────────┐                      │
│  │        Métrica          │  SOURCE      │  ACUMULADO   │                      │
│  ├─────────────────────────┼──────────────┼──────────────┤                      │
│  │ 📖 Narrativas           │       {N}    │     ~{N}     │                      │
│  │ 🏷️ Temas Consolidados   │       {N}    │      {N}     │                      │
│  │ 🔍 Temas Únicos         │       {N}    │      {N}     │  ← NOVOS!            │
│  │ 👤 Speakers             │      {N}     │     ~{N}     │                      │
│  │ 🛠️ Tools Detectadas     │       {N}    │     ~{N}     │                      │
│  └─────────────────────────┴──────────────┴──────────────┘                      │
│  TEMAS ÚNICOS: {Lista dos temas exclusivos}                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  👥 GRID 4: AGENTES (Dossiês, MEMORYs, SOWs)                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┬──────────────┬──────────────┐                      │
│  │        Métrica          │  SOURCE      │  ACUMULADO   │                      │
│  ├─────────────────────────┼──────────────┼──────────────┤                      │
│  │ 📁 Dossiês PERSONS      │   +{N} (new) │      {N}     │ {Lista}              │
│  │ 📁 Dossiês THEMES       │   +{N} (new) │      {N}     │ {Lista}              │
│  │ 🧠 MEMORYs Atualizados  │       {N}    │      {N}     │ (após Phase 5)       │
│  │ 📋 SOWs ORG-LIVE        │      +{N}    │      {N}     │ {Lista}              │
│  └─────────────────────────┴──────────────┴──────────────┘                      │
│  ℹ️ Agentes serão alimentados em Phase 5 (FEEDING)                              │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
7️⃣ QUALITY INDICATORS - Indicadores de Qualidade
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ QUALITY INDICATORS                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────┬────────────┬─────────────────────────────────┐│
│  │ Indicator                    │   Value    │ Status                          ││
│  ├──────────────────────────────┼────────────┼─────────────────────────────────┤│
│  │ 🏥 Health Status             │    {OK}    │ {🟢/🟡/🔴 STATUS}               ││
│  │ 📈 ROI (insights/chunk)      │   {X.XX}   │ {STATUS + threshold}            ││
│  │ ★  Heuristics with numbers   │  {N}/{N}   │ {XX}% (target: >10%)            ││
│  │ 📐 Named frameworks          │     {N}    │ {Lista resumida}                ││
│  │ ⚠️ Anomalies                 │      {N}   │ {Descrição se houver}           ││
│  │ ❌ Contradictions            │      {N}   │ {Lista se houver}               ││
│  │ 🔗 Collisions                │      {N}   │ {Status}                        ││
│  │ 📊 Temas saturados           │      {N}   │ {Status threshold 200}          ││
│  │ 🔄 Propagation gaps          │      {N}   │ {Status referências}            ││
│  │ 🏆 Batch LEGENDARY           │      {N}   │ {Lista}                         ││
│  └──────────────────────────────┴────────────┴─────────────────────────────────┘│
│  OVERALL HEALTH: {QUALITY} ({Descrição})                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
8️⃣ FRAMEWORKS EXTRAÍDOS - {N} Frameworks
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  📐 KEY FRAMEWORKS - {SOURCE} ({N} total)                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  🎯 {CATEGORIA 1}                                                               │
│  ├─ {Framework} 📐                                                              │
│  │  └─ "{Quote}" - {Autor}                                                      │
│  ├─ {Framework} 📐                                                              │
│  └─ ...                                                                         │
│                                                                                 │
│  🤝 {CATEGORIA 2}                                                               │
│  ├─ {Framework} 📐                                                              │
│  └─ ...                                                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
9️⃣ HEURÍSTICAS COM NÚMEROS - Ouro Extraído ({N} total)
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  ★ HEURISTICS WITH NUMBERS - {SOURCE} (TOP {N})                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  {CATEGORIA 1}                                                                  │
│  ├─ ★★★★★ {valor} {descrição}                                                   │
│  ├─ ★★★★★ {valor} {descrição}                                                   │
│  └─ ...                                                                         │
│                                                                                 │
│  {CATEGORIA 2}                                                                  │
│  ├─ ★★★★★ {valor} {descrição}                                                   │
│  └─ ...                                                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
🔟 RASTREABILIDADE - Diagrama de Fluxo
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  🔗 TRACEABILITY DIAGRAM                                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐     │
│   │                  │      │                  │      │                  │     │
│   │   inbox       │ ───→ │   processing  │ ───→ │   knowledge   │     │
│   │   /{SOURCE}/     │      │   /chunks/       │      │   /dossiers/     │     │
│   │                  │      │   /insights/     │      │   /SOURCES/      │     │
│   │   {N} arquivos   │      │   {N} chunks     │      │   (pending)      │     │
│   │   ({N} batches)  │      │   {N} insights   │      │                  │     │
│   └──────────────────┘      └──────────────────┘      └──────────────────┘     │
│                                      │                                          │
│                                      ↓                                          │
│                             ┌──────────────────┐                                │
│                             │                  │                                │
│                             │   logs        │                                │
│                             │   /SOURCES/      │                                │
│                             │                  │                                │
│                             │   SOURCE-{ID}.md │                                │
│                             │                  │                                │
│                             └──────────────────┘                                │
│                                                                                 │
│   {SOURCE} BATCHES BREAKDOWN:                                                   │
│   ├─ BATCH-XXX: {desc}   {N} files │ {N} ins │ {frameworks}                    │
│   ├─ ...                                                                        │
│   └─ BATCH-YYY: {desc}   {N} files │ {N} ins │ {frameworks}                    │
│                                                                                 │
│   RASTREABILIDADE: SOURCE → CHUNK_ID → INSIGHT → DOSSIER                        │
│   STATUS: ✅ Íntegra até Phase 2.1 (Insight Extraction)                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
1️⃣1️⃣ PRÓXIMOS PASSOS - Ação Requerida
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ NEXT STEPS                                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  📍 PRÓXIMA FONTE: {NOME}                                                       │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ COMANDO:  /mission resume                                                   ││
│  │                                                                             ││
│  │ AÇÃO:     Processará BATCH-XXX (primeira batch {FONTE})                     ││
│  │ RESTANTE: ~{N} batches (~{N} arquivos)                                      ││
│  │ FILES:    ~{N} arquivos                                                     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  📊 SOURCES COMPLETED ({N}/{N}):                                                │
│  ├─ ✅ {SOURCE}     {N} files │ {N} batches  │ COMPLETE                        │
│  └─ ...                                                                         │
│                                                                                 │
│  📊 SOURCES PENDING ({N}/{N}):                                                  │
│  ├─ ⏳ {SOURCE}     ~{N} files │ ~{N} batches │ NEXT                            │
│  └─ ...                                                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
📋 BRIEFING EXECUTIVO
══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│  📋 EXECUTIVE BRIEFING                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  EM UMA FRASE:                                                                  │
│  "{Resumo da fonte em 1-2 linhas}"                                              │
│                                                                                 │
│  O QUE APRENDEMOS:                                                              │
│  • {Insight principal 1}                                                        │
│  • {Insight principal 2}                                                        │
│  • ...                                                                          │
│                                                                                 │
│  POSICIONAMENTO ÚNICO {SOURCE}:                                                 │
│  • {Diferencial 1}                                                              │
│  • {Diferencial 2}                                                              │
│  • ...                                                                          │
│                                                                                 │
│  DECISÕES AUTOMÁTICAS TOMADAS (DEC-{XXXX} a DEC-{YYYY}):                        │
│  • {Decisão 1}                                                                  │
│  • {Decisão 2}                                                                  │
│  • ...                                                                          │
│                                                                                 │
│  PRÓXIMOS PASSOS:                                                               │
│  1. {Ação 1}                                                                    │
│  2. {Ação 2}                                                                    │
│  3. {Ação 3}                                                                    │
│                                                                                 │
│  STATUS DE SAÚDE: {QUALITY} ({Descrição})                                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║   🤖 JARVIS MISSION CONTROL                                                                      ║
║   "{Summary message}"                                                                            ║
║                                                                                                  ║
║   📍 Próxima fonte: {NOME}                                                                       ║
║   ⚡ Aguardando /mission resume para BATCH-XXX                                                   ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

                                Generated by JARVIS v{VERSION}
                                    {TIMESTAMP}
```

**Localização:** `/logs/SOURCES/SOURCE-{FONTE}.md`


---

## LOG DE MISSÃO (Quando Missão Completa)

Quando TODAS as fontes são processadas, gerar LOG DE MISSÃO final:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ███╗   ███╗██╗███████╗███████╗██╗ ██████╗ ███╗   ██╗                       │
│   ████╗ ████║██║██╔════╝██╔════╝██║██╔═══██╗████╗  ██║                       │
│   ██╔████╔██║██║███████╗███████╗██║██║   ██║██╔██╗ ██║                       │
│   ██║╚██╔╝██║██║╚════██║╚════██║██║██║   ██║██║╚██╗██║                       │
│   ██║ ╚═╝ ██║██║███████║███████║██║╚██████╔╝██║ ╚████║                       │
│   ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝                       │
│                                                                              │
│              {MISSION-ID} - COMPLETE                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

[+ Comparativo entre fontes, conflitos cross-source, síntese final]
```

**Localização:** `/logs/MISSIONS/MISSION-{ID}-FINAL.md`

---

## Hierarquia de Logs

```
BATCH (por batch)                    SOURCE (por fonte)              MISSION (final)
─────────────────                    ────────────────                ─────────────────

BATCH-001.md ─┐
BATCH-002.md ─┼─→ [Fonte completa] ─→ SOURCE-JEREMY-HAYNES.md ─┐
BATCH-003.md ─┤                                                 │
BATCH-004.md ─┘                                                 │
                                                                │
BATCH-005.md ─┐                                                 │
BATCH-006.md ─┼─→ [Fonte completa] ─→ SOURCE-COLE-GORDON.md ───┼─→ MISSION-FINAL.md
BATCH-007.md ─┘                                                 │
                                                                │
BATCH-008.md ─┐                                                 │
BATCH-019.md ─┘
```

---

## Regras de Aplicação

1. **SEMPRE** usar este formato para logs de batch em Phase 4
2. **NUNCA** simplificar os boxes ou remover seções
3. **SEMPRE** incluir Preview de Impacto (Phase 5 visibility)
4. **SEMPRE** manter alinhamento consistente (80 caracteres de largura)
5. **GERAR** log de SOURCE quando fonte completa
6. **GERAR** log de MISSION quando missão completa

---

## Decisões Relacionadas

- **DEC-2026-0041:** LOG-STRUCTURE-PROTOCOL (3 níveis de log)
- **DEC-2026-0056:** BATCH-VISUAL-PROTOCOL (formato visual oficial)

---

**Protocolo oficializado em:** 2026-01-04
**Autor:** [OWNER] + JARVIS


---

## Cascateamento Executado

**Data:** 2026-02-18 21:32
**Regra aplicada:** REGRA #22 (Cascateamento Multi-Destino)
**Sistema:** AIOS Core

### Resumo

| Tipo | Quantidade | Sucesso |
|------|------------|---------|
| Agentes | 0 | 0 |
| Playbooks | 0 | 0 |
| DNAs | 0 | 0 |
| Dossiers | 0 | 0 |

### Detalhes


---

*Cascateamento automatico via `post_batch_cascading.py` (AIOS Core)*
