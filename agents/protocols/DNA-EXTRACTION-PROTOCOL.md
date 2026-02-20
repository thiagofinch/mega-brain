# DNA-EXTRACTION-PROTOCOL.md

> **Phase:** 3.2 (após Narrative Synthesis, antes de Dossier Compilation)
> **Input:** NARRATIVES-STATE.json + INSIGHTS-STATE.json
> **Output:** `/processing/dna/{PESSOA}/`
> **Versão:** 1.0.0
> **Criado:** 2026-01-04

---

## PROPÓSITO

Extrair a **essência cognitiva** de uma pessoa/fonte - não apenas "o que disse", mas "como pensa". Isso alimenta diretamente os agentes com personalidade, tom de voz, e padrões de decisão.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│  INSIGHT EXTRACTION (Phase 2.1)          DNA EXTRACTION (Phase 3.2)                │
│  ───────────────────────────────────────────────────────────────────────────────   │
│                                                                                     │
│  ✅ Extrai INSIGHTS genéricos               ✅ Extrai 5 CAMADAS COGNITIVAS         │
│  ✅ MARCA se é heurística (flag)            ✅ CATEGORIZA por tipo cognitivo       │
│  ✅ MARCA se é framework (flag)             ✅ Gera SOUL.md (filosofias em prosa)  │
│  ✅ Atribui confidence/priority             ✅ Gera MEMORY.md (decisões padrão)    │
│                                             ✅ Gera DNA-CONFIG.yaml                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## AS 5 CAMADAS COGNITIVAS

| # | Camada | Descrição | Exemplo JH |
|---|--------|-----------|------------|
| 1 | **FILOSOFIAS** | Crenças, valores, axiomas fundamentais | "Philosophy beats tactics every time" |
| 2 | **MODELOS MENTAIS** | Formas de pensar, frameworks conceituais | "The confused mind always says no" |
| 3 | **HEURÍSTICAS ★** | Regras práticas COM NÚMEROS | "15-20+ peças em 72h aumenta show rate" |
| 4 | **FRAMEWORKS** | Sistemas nomeados com componentes | "4 Pillars: Volume, Variety, Velocity, Vintage" |
| 5 | **METODOLOGIAS** | Processos passo-a-passo | "Hammer Them Strategy: Day -3 to Day 0" |

### Critérios de Classificação

```
FILOSOFIA se:
  - É uma crença/valor/princípio
  - Não tem números específicos
  - É abstrato, não procedural
  - Exemplo: "You can't out-tactic a bad philosophy"

MODELO MENTAL se:
  - É uma forma de PENSAR sobre algo
  - Não é um processo, é uma lente
  - Exemplo: "3 Prospect Types: Hot, Warm, Cold"

HEURÍSTICA ★ se:
  - TEM NÚMERO ESPECÍFICO
  - É uma regra prática
  - Pode ser verificada/medida
  - Exemplo: "CTR < 2% → rotacionar a cada 72h"

FRAMEWORK se:
  - TEM NOME PRÓPRIO
  - Tem componentes identificáveis
  - Exemplo: "DSL - Deck Sales Letter Framework"

METODOLOGIA se:
  - É um PROCESSO com etapas
  - Tem sequência temporal
  - Exemplo: "Challenge Funnel: Day 1, Day 2, Day 3..."
```

---

## INPUT

### Fontes Primárias

1. **NARRATIVES-STATE.json** - Narrativas consolidadas por tema
2. **INSIGHTS-STATE.json** - Insights filtrados por fonte (ex: `JH-SOP*`)
3. **Chunks originais** - Para contexto quando necessário

### Filtro de Fonte

```python
# Extrair apenas insights da fonte específica
fonte = "JH-SOP"
insights = [i for i in all_insights if any(fonte in c for c in i["chunks"])]
```

---

## OUTPUT

### Estrutura de Diretório

```
/processing/dna/{PESSOA}/
├── DNA-CONFIG.yaml      ← Estrutura das 5 camadas
├── SOUL.md              ← Filosofias em formato de prosa
└── MEMORY.md            ← Decisões padrão + precedentes
```

### DNA-CONFIG.yaml (Schema)

```yaml
# DNA-CONFIG.yaml
version: "1.0.0"
pessoa: "jeremy-haynes"
fonte_ids: ["JH-SOP001", "JH-SOP002", "..."]
extracted_at: "2026-01-04T16:00:00Z"
total_items: 50

filosofias:
  count: 8
  items:
    - id: "FIL001"
      texto: "Philosophy beats tactics every time"
      chunks: ["JH-SOP019_003"]
      confidence: "HIGH"
    - id: "FIL002"
      texto: "The confused mind always says no"
      chunks: ["JH-SOP002_015"]
      confidence: "HIGH"

modelos_mentais:
  count: 5
  items:
    - id: "MM001"
      texto: "3 Prospect Types: Hot (ready now), Warm (interested), Cold (unaware)"
      chunks: ["JH-SOP003_008", "JH-SOP004_012"]
      confidence: "HIGH"

heuristicas:
  count: 18
  items:
    - id: "HEU001"
      texto: "15-20+ peças de conteúdo em janela de 72h antes da call aumenta show rate"
      numeros: "15-20+, 72h"
      chunks: ["JH-SOP002_001", "JH-SOP002_002"]
      confidence: "HIGH"
      prioridade: "ALTA"
    - id: "HEU002"
      texto: "CPE target: $0.01-0.02 para escala"
      numeros: "$0.01-0.02"
      chunks: ["JH-SOP011_005"]
      confidence: "HIGH"

frameworks:
  count: 12
  items:
    - id: "FW001"
      nome: "4 Pillars"
      componentes: ["Volume", "Variety", "Velocity", "Vintage"]
      chunks: ["JH-SOP002_003"]
      confidence: "HIGH"
    - id: "FW002"
      nome: "Hammer Them Strategy"
      componentes: ["Pre-call content", "72h window", "15-20+ pieces"]
      chunks: ["JH-SOP002_001"]
      confidence: "HIGH"

metodologias:
  count: 7
  items:
    - id: "MET001"
      nome: "Challenge Funnel"
      etapas:
        - "Day 1: Hook + Problem"
        - "Day 2: Authority positioning"
        - "Day 3: Solution reveal"
        - "Day 4: Close"
      chunks: ["JH-SOP030_001", "JH-SOP030_015"]
      confidence: "HIGH"
```

### SOUL.md (Template)

```markdown
# SOUL.md - Jeremy Haynes

> Extraído automaticamente via DNA-EXTRACTION-PROTOCOL.md
> Fonte: 31 SOPs Jeremy Haynes
> Data: 2026-01-04

---

## QUEM SOU

Jeremy Haynes é [descrição derivada das filosofias]...

## O QUE ACREDITO

### Filosofias Fundamentais

1. **"Philosophy beats tactics every time"** ^[JH-SOP019_003]
   - [contexto e implicação]

2. **"The confused mind always says no"** ^[JH-SOP002_015]
   - [contexto e implicação]

[...]

## COMO PENSO

### Modelos Mentais

[Modelos mentais em prosa, com referências]

## MINHAS REGRAS ★

### Heurísticas (com números)

| Regra | Números | Fonte |
|-------|---------|-------|
| [heurística 1] | [números] | ^[chunk_id] |

[...]
```

### MEMORY.md (Template)

```markdown
# MEMORY.md - Jeremy Haynes

> Decisões padrão e precedentes extraídos via DNA-EXTRACTION-PROTOCOL.md
> Atualizado: 2026-01-04

---

## DECISÕES PADRÃO

Quando consultado, Jeremy Haynes tipicamente decide:

### Sobre Ads
- Se CTR < 2% → "Rotacionar a cada 72h" ^[JH-SOP006_003]
- Se CPE > $0.03 → "Verificar targeting primeiro" ^[JH-SOP011_008]

### Sobre Funnels
- [decisões padrão sobre funnels]

### Sobre Hiring
- [decisões padrão sobre hiring]

---

## FRAMEWORKS QUE APLICO

| Framework | Quando Usar | Referência |
|-----------|-------------|------------|
| Hammer Them | 72h antes de calls | ^[JH-SOP002] |
| 4 Pillars | Qualquer ad strategy | ^[JH-SOP002] |
| DSL | High-ticket funnels | ^[JH-SOP016] |

---

## METODOLOGIAS DISPONÍVEIS

### Challenge Funnel
[Metodologia completa com etapas]

### Book Funnel
[Metodologia completa com etapas]
```

---

## PROCESSO DE EXTRAÇÃO

### Passo 1: Coletar Insights da Fonte

```
PARA cada insight em INSIGHTS-STATE.json:
  SE chunk_id contém "{FONTE_ID}":
    ADICIONAR ao pool de extração
```

### Passo 2: Classificar em 5 Camadas

```
PARA cada insight no pool:
  ANALISAR texto do insight
  CLASSIFICAR em uma das 5 camadas usando critérios
  ATRIBUIR ID único (FIL001, MM001, HEU001, FW001, MET001)
  MANTER chunk_ids para rastreabilidade
```

### Passo 3: Gerar DNA-CONFIG.yaml

```
COMPILAR todas as classificações em YAML estruturado
VALIDAR contagens
SALVAR em /processing/dna/{PESSOA}/DNA-CONFIG.yaml
```

### Passo 4: Gerar SOUL.md

```
TRANSFORMAR filosofias e modelos mentais em prosa
MANTER referências ^[chunk_id]
SEGUIR template
SALVAR em /processing/dna/{PESSOA}/SOUL.md
```

### Passo 5: Gerar MEMORY.md

```
COMPILAR heurísticas como "decisões padrão"
LISTAR frameworks e quando usar
DETALHAR metodologias com etapas
MANTER referências
SALVAR em /processing/dna/{PESSOA}/MEMORY.md
```

---

## VALIDAÇÃO

Antes de considerar Phase 3.2 completa:

```
□ DNA-CONFIG.yaml existe e é YAML válido?
□ Todas as 5 camadas têm pelo menos 1 item?
□ Todos os chunk_ids são válidos (existem em CHUNKS-STATE.json)?
□ SOUL.md foi gerado?
□ MEMORY.md foi gerado?
□ Contagem total bate com insights processados?
```

---

## INTEGRAÇÃO COM PIPELINE

### Antes de DNA Extraction (Phase 3.1)
- NARRATIVES-STATE.json deve estar atualizado
- Narrativas consolidadas por tema

### Depois de DNA Extraction (Phase 4.0)
- DOSSIER-COMPILATION pode REFERENCIAR DNA
- Exemplo em DOSSIER-JEREMY-HAYNES.md:
  ```markdown
  ## Filosofias de JH
  Ver: `/processing/dna/jeremy-haynes/SOUL.md`
  ```

### Agent Feeding (Phase 5.0)
- DNA já está pronto
- AGENT.md pode incorporar SOUL.md e MEMORY.md diretamente

---

## REGRAS INVIOLÁVEIS

```
❌ NUNCA inventar conteúdo não presente nas fontes
❌ NUNCA classificar sem chunk_id de rastreabilidade
❌ NUNCA gerar SOUL.md sem DNA-CONFIG.yaml primeiro
❌ NUNCA pular camadas (todas as 5 devem ser tentadas)

✅ SEMPRE manter rastreabilidade via chunk_ids
✅ SEMPRE validar YAML antes de salvar
✅ SEMPRE gerar os 3 arquivos (DNA, SOUL, MEMORY)
✅ SEMPRE seguir templates
```

---

**Versão:** 1.0.0
**Autor:** JARVIS + [OWNER]
**Última atualização:** 2026-01-04
