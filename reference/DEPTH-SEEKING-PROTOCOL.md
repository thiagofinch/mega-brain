## FASE 1.5: DEPTH-SEEKING (NAVEGAÇÃO PROFUNDA)

> **Esta fase é ativada DURANTE a Fase 1 quando o agente precisa de contexto adicional.**

---

### 1.5.0 REGRA INQUEBRÁVEL: NAVEGAÇÃO PRÉVIA ATÉ A RAIZ

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ANTES DE ENTREGAR QUALQUER RESPOSTA FACTUAL:                              ║
║   O SISTEMA JÁ DEVE TER NAVEGADO ATÉ A RAIZ                                 ║
║                                                                              ║
║   Quando o usuário perguntar "de onde vem essa informação?"                 ║
║   A resposta IMEDIATA deve conter:                                          ║
║                                                                              ║
║   ┌────────────────────────────────────────────────────────────────────┐    ║
║   │ QUEM:    Nome da pessoa que disse (speaker)                        │    ║
║   │ QUANDO:  Data/contexto temporal                                    │    ║
║   │ ONDE:    Material exato (título, tipo, canal)                      │    ║
║   │ TEXTO:   Citação bruta original (não parafraseada)                 │    ║
║   │ PATH:    Caminho até o arquivo inbox                            │    ║
║   └────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║   SE NÃO CONSEGUIR FORNECER ESSES 5 ELEMENTOS = NÃO CITE COMO FATO         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**EXEMPLO DE RESPOSTA COM RAIZ PRÉ-CARREGADA:**

```
PERGUNTA: "Qual é a estrutura ideal de time de vendas outbound?"

RESPOSTA DO AGENTE:
─────────────────────────────────────────────────────────────────
A estrutura recomendada é a "Christmas Tree Structure":
- BDR (Business Development Rep) na base - faz 100 calls/dia
- SDS (Sales Development Specialist) no meio - qualifica e entrega valor
- BC (Business Consultant) no topo - fecha

RAIZ PRÉ-CARREGADA (pronta para "de onde vem?"):
─────────────────────────────────────────────────────────────────
├─ QUEM: Alex Hormozi
├─ QUANDO: ~2023, Taki Moore Mastermind (8-Figure+ Group)
├─ ONDE: "How I Scaled My Sales Team" - Apresentação em mastermind
├─ PATH: /inbox/alex hormozi/MASTERMINDS/
│        HOW I SCALED MY SALES TEAM [TAKI MOORE MASTERMIND].txt
└─ TEXTO BRUTO:
   "...and it looks like a christmas tree if you were to look at
    the org chart like this right you got the base of bdrs who feed
    half as many sds you then feed half as many bcs in this model
    if you replace a bdr mentally with what an advertisement used
    to do that's exactly how this functions..."
```

**APLICAÇÃO OBRIGATÓRIA:**

| Contexto | Navegação até RAIZ |
|----------|-------------------|
| Resposta direta ao usuário | ✅ OBRIGATÓRIA antes de responder |
| Debate entre agentes | ✅ OBRIGATÓRIA para cada afirmação |
| Consulta entre agentes | ✅ OBRIGATÓRIA para validar fonte |
| Citação em documento | ✅ OBRIGATÓRIA no momento de escrever |
| Inferência/especulação | ⚠️ Declarar como tal, sem fonte |

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  PRINCÍPIO: TODA INFORMAÇÃO DEVE SER RASTREÁVEL ATÉ A RAIZ                 │
│                                                                             │
│  Quando um ^[FONTE:arquivo:linha] é encontrado, o sistema DEVE             │
│  navegar até o conteúdo original ANTES de entregar a resposta.             │
│                                                                             │
│  RAIZ = O arquivo bruto original (inbox/*.txt, transcrições, etc.)      │
│                                                                             │
│  Se não navegar = não pode afirmar como fato                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.5.1 TRIGGERS PARA BUSCA DE PROFUNDIDADE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ⚠️ NAVEGAÇÃO É OBRIGATÓRIA ANTES DE RESPONDER - NÃO OPCIONAL             │
│                                                                             │
│  QUANDO NAVEGAR ATÉ A RAIZ (SEMPRE):                                        │
│                                                                             │
│  1. RESPOSTA FACTUAL AO USUÁRIO                                             │
│     └─ QUALQUER afirmação factual = NAVEGAR ANTES                          │
│     └─ Ter RAIZ pronta para "de onde vem?"                                 │
│     └─ 5 elementos: QUEM, QUANDO, ONDE, TEXTO, PATH                        │
│                                                                             │
│  2. DEBATE / WAR ROOM                                                       │
│     └─ TODA afirmação em debate = rastro até FONTE                         │
│     └─ Agente que não prova a fonte PERDE o ponto                          │
│     └─ Vence quem tem RAIZ mais sólida                                     │
│                                                                             │
│  3. CONSULTA ENTRE AGENTES                                                  │
│     └─ Agente A pergunta a Agente B = B deve provar fonte                  │
│     └─ "Eu acho" não vale - "A fonte diz" vale                             │
│                                                                             │
│  4. CRIAÇÃO/ATUALIZAÇÃO DE DOCUMENTOS                                       │
│     └─ Todo texto em AGENT.md = ^[FONTE:arquivo:linha]                     │
│     └─ Todo insight em MEMORY.md = ^[chunk_id] → RAIZ                      │
│                                                                             │
│  NAVEGAÇÃO PARCIAL (apenas se RAIZ já foi validada nesta sessão):          │
│     └─ Citação JÁ FOI VERIFICADA nesta sessão (cache)                      │
│     └─ Contexto SOUL/MEMORY é suficiente E já foi validado                 │
│                                                                             │
│  NUNCA RESPONDER SEM NAVEGAÇÃO QUANDO:                                      │
│     └─ É debate/decisão crítica                                            │
│     └─ Há conflito entre fontes                                            │
│     └─ Usuário questiona a veracidade                                      │
│     └─ Afirmação é base para decisão de negócio                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5.2 HIERARQUIA DE NAVEGAÇÃO (Surface → Root)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  CAMADA 0: SUPERFÍCIE (já carregado na Fase 0)                             │
│  ──────────────────────────────────────────────                             │
│  AGENT.md ─────────────────────────────────────────────────────────────→   │
│     │                                                                       │
│     │ ^[SOUL.md:linha]                                                      │
│     ▼                                                                       │
│  SOUL.md ──────────────────────────────────────────────────────────────→   │
│     │                                                                       │
│     │ ^[MEMORY.md:linha]                                                    │
│     ▼                                                                       │
│  MEMORY.md ────────────────────────────────────────────────────────────→   │
│     │                                                                       │
│     │ ^[DNA-CONFIG.yaml]                                                    │
│     ▼                                                                       │
│  DNA-CONFIG.yaml ──────────────────────────────────────────────────────→   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  CAMADA 1: DNA ESTRUTURADO                                                  │
│  ─────────────────────────────                                              │
│     │                                                                       │
│     │ Paths definidos em DNA-CONFIG.yaml                                   │
│     ▼                                                                       │
│  /knowledge/external/dna/persons/{PESSOA}/DNA.yaml ──────────────────────────→   │
│     │                                                                       │
│     │ insight_ids referenciados                                             │
│     ▼                                                                       │
│  /knowledge/external/dna/persons/{PESSOA}/INSIGHTS.yaml ─────────────────────→   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  CAMADA 2: PROCESSAMENTO (Pipeline Jarvis)                                  │
│  ─────────────────────────────────────────                                  │
│     │                                                                       │
│     │ chunk_ids nos insights                                                │
│     ▼                                                                       │
│  /processing/insights/INSIGHTS-STATE.json ──────────────────────────→   │
│     │                                                                       │
│     │ chunk_id → localização                                                │
│     ▼                                                                       │
│  /processing/chunks/CHUNKS-STATE.json ──────────────────────────────→   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  CAMADA 3: RAIZ (Conteúdo Original)                                         │
│  ─────────────────────────────────                                          │
│     │                                                                       │
│     │ source_file no chunk                                                  │
│     ▼                                                                       │
│  /inbox/{FONTE}/{ARQUIVO}.txt ─────────────────────────── 🌱 RAIZ      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5.3 MECANISMO DE RESOLUÇÃO DE REFERÊNCIAS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FORMATO DE REFERÊNCIA: ^[ARQUIVO:linha] ou ^[ARQUIVO:linha-fim]           │
│                                                                             │
│  ALGORITMO DE RESOLUÇÃO:                                                    │
│                                                                             │
│  1. PARSE DA REFERÊNCIA                                                     │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ Input:  ^[SOUL.md:44-62]                                         │   │
│     │ Output: {arquivo: "SOUL.md", inicio: 44, fim: 62}                │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. RESOLUÇÃO DE PATH                                                       │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ SE arquivo é relativo (SOUL.md, MEMORY.md):                      │   │
│     │   → Resolver relativo ao diretório do agente                     │   │
│     │   → Ex: /agents/cargo/C-LEVEL/CFO/SOUL.md                    │   │
│     │                                                                   │   │
│     │ SE arquivo é absoluto (/knowledge/...):                       │   │
│     │   → Usar path absoluto diretamente                               │   │
│     │                                                                   │   │
│     │ SE arquivo usa ID (CG001_012):                                   │   │
│     │   → Consultar CHUNKS-STATE.json para localização                 │   │
│     │   → Navegar até source_file                                      │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. CARREGAMENTO DE CONTEXTO                                                │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ Carregar linhas [inicio] a [fim]                                 │   │
│     │                                                                   │   │
│     │ SE contexto insuficiente:                                        │   │
│     │   → Expandir ±5 linhas para contexto                            │   │
│     │                                                                   │   │
│     │ SE ainda insuficiente:                                           │   │
│     │   → Navegar para camada mais profunda (seguir referências)      │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. RETORNO AO AGENTE                                                       │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ Retornar conteúdo com metadados:                                 │   │
│     │ {                                                                 │   │
│     │   "fonte": "/agents/cargo/C-LEVEL/CFO/SOUL.md",              │   │
│     │   "linhas": "44-62",                                             │   │
│     │   "conteudo": "...",                                             │   │
│     │   "contexto_expandido": true/false                               │   │
│     │ }                                                                 │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5.4 NAVEGAÇÃO POR chunk_id (PIPELINE JARVIS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  QUANDO: Referência usa chunk_id (ex: CG001_012, AH003_045)                │
│                                                                             │
│  PASSO 1: Consultar CHUNKS-STATE.json                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ GET /processing/chunks/CHUNKS-STATE.json                          │  │
│  │                                                                       │  │
│  │ Buscar: "CG001_012"                                                   │  │
│  │ Retorno:                                                              │  │
│  │ {                                                                      │  │
│  │   "chunk_id": "CG001_012",                                            │  │
│  │   "source_file": "/inbox/COLE GORDON/PODCASTS/video.txt",         │  │
│  │   "start_line": 450,                                                  │  │
│  │   "end_line": 478,                                                    │  │
│  │   "content_preview": "..."                                            │  │
│  │ }                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PASSO 2: Navegar para source_file                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ READ source_file linhas start_line:end_line                          │  │
│  │                                                                       │  │
│  │ → Retorna conteúdo original da transcrição                           │  │
│  │ → Este é o conteúdo RAIZ (máxima profundidade)                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PASSO 3: Consultar INSIGHTS-STATE.json (opcional)                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ SE quiser saber que insights foram extraídos desse chunk:            │  │
│  │                                                                       │  │
│  │ GET /processing/insights/INSIGHTS-STATE.json                      │  │
│  │ FILTER where chunk_ids contains "CG001_012"                          │  │
│  │                                                                       │  │
│  │ → Retorna lista de insights derivados                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5.5 REGRAS DE CACHE E ECONOMIA DE TOKENS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ECONOMIA DE TOKENS (CRÍTICO)                                               │
│                                                                             │
│  1. LAZY LOADING                                                            │
│     └─ Só carregar profundidade quando REALMENTE necessário                │
│     └─ Camada 0 (AGENT, SOUL, MEMORY, DNA-CONFIG) sempre carregado        │
│     └─ Camadas 1, 2, 3 apenas sob demanda                                  │
│                                                                             │
│  2. CACHE DE SESSÃO                                                         │
│     └─ Se um chunk/arquivo foi carregado nesta sessão, não recarregar     │
│     └─ Manter mapa de contextos já expandidos                              │
│                                                                             │
│  3. LIMITE DE PROFUNDIDADE                                                  │
│     └─ Máximo 3 níveis de navegação por pergunta                          │
│     └─ Se após 3 níveis não encontrou, declarar "não encontrado"          │
│     └─ Aplicar CIRCUIT BREAKER do EPISTEMIC-PROTOCOL                      │
│                                                                             │
│  4. PRIORIDADE DE NAVEGAÇÃO                                                 │
│     └─ Preferir arquivos menores primeiro                                  │
│     └─ Preferir linhas específicas a arquivo inteiro                       │
│     └─ Preferir INSIGHTS-STATE a CHUNKS-STATE (mais processado)           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5.6 EXEMPLO DE FLUXO COMPLETO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  CENÁRIO: Usuário pergunta sobre uma heurística específica                 │
│                                                                             │
│  1. AGENTE LÊ em AGENT.md (Fase 0):                                        │
│     > "Cash flow é rei, margem é rainha" ^[SOUL.md:37-38]                  │
│                                                                             │
│  2. TRIGGER: Usuário pede mais contexto                                     │
│     > "Me explica melhor essa filosofia"                                   │
│                                                                             │
│  3. FASE 1.5 ATIVADA:                                                       │
│     │                                                                       │
│     ├─→ PASSO 1: Parse ^[SOUL.md:37-38]                                    │
│     │   Resultado: {arquivo: "SOUL.md", linhas: 37-38}                     │
│     │                                                                       │
│     ├─→ PASSO 2: Resolver path                                              │
│     │   /agents/cargo/C-LEVEL/CFO/SOUL.md                               │
│     │                                                                       │
│     ├─→ PASSO 3: Carregar linhas 37-38                                      │
│     │   "Empresas não morrem de fome - morrem de indigestão.               │
│     │    Cash flow é rei, margem é rainha, e eu protejo a coroa."          │
│     │                                                                       │
│     ├─→ PASSO 4: Contexto suficiente? SIM                                   │
│     │                                                                       │
│     └─→ RETORNO: Agente agora tem contexto completo                        │
│                                                                             │
│  4. SE CONTEXTO INSUFICIENTE:                                               │
│     │                                                                       │
│     ├─→ Expandir ±5 linhas (32-43)                                         │
│     │                                                                       │
│     ├─→ SE ainda insuficiente:                                              │
│     │   Verificar se há ^[FONTE] dentro de SOUL.md                         │
│     │   Navegar para próxima camada (DNA, INSIGHTS, RAIZ)                  │
│     │                                                                       │
│     └─→ LIMITE: Máximo 3 navegações profundas                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

