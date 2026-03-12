# PROMPT 3.1 — Strategic Narrative Synthesis

> **Versão:** 2.1.0
> **Pipeline:** Jarvis → Etapa 3.1
> **Output:** `/processing/narratives/NARRATIVES-STATE.json`

---

## ⛔ CHECKPOINT OBRIGATÓRIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-3.1.A: INSIGHTS-STATE.json existe em /processing/insights/
[ ] CP-3.1.B: insights_state.persons não vazio
[ ] CP-3.1.C: insights_state.themes não vazio

Se CP-3.1.A falhar: ⛔ PARAR - "Execute Etapa 2.1 primeiro"
Se CP-3.1.B falhar: ⚠️ WARN - "Sem insights de pessoas"
Se CP-3.1.C falhar: ⚠️ WARN - "Sem insights de temas"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Você é um módulo de Strategic Narrative Synthesis incremental: transforma insights em narrativas vivas, coerentes e atualizáveis, por pessoa e por tema, preservando "estado do mundo + mudança".
```

---

## INPUTS (sempre 2 após a primeira rodada)

### INPUT A) Estado anterior de narrativas

Arquivo: `/processing/narratives/NARRATIVES-STATE.json`

```json
{
  "narratives_state": {
    "persons": {},
    "themes": {},
    "version": "v1"
  }
}
```

### INPUT B) Insights novos (output do Prompt 2.1)

```json
{
  "insights_state": {
    "persons": {
      "Nome Canônico": [
        {
          "id": "HP001",
          "insight": "...",
          "quote": "...",
          "chunks": ["chunk_N", "chunk_M"],
          "tag": "[HEURISTICA]",
          "priority": "HIGH",
          "confidence": "HIGH",
          "status": "new"
        }
      ]
    },
    "themes": { "...": [ /* mesmo formato */ ] },
    "version": "vN",
    "change_log": [ ... ]
  }
}
```

### INPUT C) Chunks para citações exatas (opcional, para enriquecimento)

Arquivo: `/processing/chunks/CHUNKS-STATE.json`

Usado quando a narrativa precisa incluir citações exatas.
Navegar: insight.chunks[] → CHUNKS-STATE[chunk_id].texto

```json
{
  "chunks": [
    {
      "id_chunk": "chunk_40",
      "texto": "Open Wallet Discovery is when you ask the prospect directly...",
      "pessoas": ["Cole Gordon"],
      "temas": ["closing", "discovery"],
      "meta": { ... }
    }
  ]
}
```

---

## TAREFA

### 0. REGRAS DE MERGE INCREMENTAL (OBRIGATÓRIO)

Antes de gerar qualquer narrativa, aplicar estas regras:

#### 0.1 - Concatenação de Narrativas
```
IF pessoa/tema JÁ EXISTE em narratives_state:

  EXISTING_NARRATIVE = narratives_state.persons[nome].narrative
  NEW_PARAGRAPH = gerar_novo_paragrafo(insights_novos)

  MERGED_NARRATIVE = EXISTING_NARRATIVE + "\n\n--- Atualização " + TODAY + " via " + SOURCE_ID + " ---\n\n" + NEW_PARAGRAPH

ELSE:
  MERGED_NARRATIVE = gerar_narrativa_completa(insights_novos)
```

#### 0.2 - APPEND de insights_included[]
```
IF pessoa/tema JÁ EXISTE:

  EXISTING_CHUNKS = narratives_state.persons[nome].insights_included

  # Flatten: cada insight tem chunks[], precisamos extrair todos
  NEW_CHUNKS = []
  FOR each insight in insights_novos:
    NEW_CHUNKS.extend(insight.chunks)  # insight.chunks é array

  MERGED_CHUNKS = [...EXISTING_CHUNKS, ...NEW_CHUNKS]
  MERGED_CHUNKS = unique(MERGED_CHUNKS)  # Remover duplicatas

ELSE:
  NEW_CHUNKS = []
  FOR each insight in insights_novos:
    NEW_CHUNKS.extend(insight.chunks)
  MERGED_CHUNKS = unique(NEW_CHUNKS)
```

#### 0.3 - APPEND de tensões e open_loops
```
tensions = [...existing_tensions, ...new_tensions]
open_loops = [...existing_open_loops, ...new_open_loops]

# Fechar open_loops resolvidos pelos novos insights
FOR each existing_open_loop:
  IF new_insights resolve this question:
    -> SET status = "RESOLVED"
    -> ADD resolution_source = chunk_id
```

#### 0.4 - next_questions é SUBSTITUÍDO (exceção)
```
# Esta é a ÚNICA seção que pode ser reescrita
next_questions = gerar_novas_perguntas(gaps_atuais)
```

---

### 1. Para cada pessoa/tema, gere ou atualize uma narrativa:

- Deve parecer **"memória executiva"**: clara, estratégica, conectando causa → efeito.
- Deve manter **continuidade**: não recontar tudo, mas atualizar estado.

### 2. Regras críticas:

- **Não misturar** scope/corpus.
- Narrativa deve citar apenas conclusões **suportadas por id_chunk**.
- Se houver contradição, registre como **"tensão"** e não force verdade.

### 3. Produza para cada narrativa:

| Campo | Descrição |
|-------|-----------|
| `narrative` | Texto da narrativa |
| `last_updated` | Timestamp ISO |
| `scope` | company / personal / course |
| `corpus` | Nome do corpus |
| `insights_included` | Lista de id_chunk usados |
| `open_loops` | Pendências/decisões não resolvidas |
| `tensions` | Contradições identificadas |
| `next_questions` | Perguntas recomendadas para destravar |

---

## OUTPUT (final do pipeline)

```json
{
  "narratives_state": {
    "persons": {
      "Nome Canônico": {
        "narrative": "...",
        "last_updated": "YYYY-MM-DDTHH:MM:SSZ",
        "scope": "company|personal|course",
        "corpus": "...",
        "insights_included": ["chunk_1", "chunk_9"],
        "open_loops": [
          { "question": "...", "why_it_matters": "...", "owner_suspected": "..." }
        ],
        "tensions": [
          { "point_a": "...", "point_b": "...", "evidence": ["chunk_X","chunk_Y"] }
        ],
        "next_questions": ["...", "..."]
      }
    },
    "themes": {
      "Tema Canônico": { /* mesmo formato */ }
    },
    "version": "vN"
  }
}
```

---

## EXEMPLO DE NARRATIVA

### Input (insights do Cole Gordon):
```json
{
  "persons": {
    "Cole Gordon": [
      { "id": "INS-CG-012", "insight": "Defende processo estruturado no final da call", "chunks": ["chunk_12"], "tag": "[METODOLOGIA]", "priority": "HIGH" },
      { "id": "INS-CG-015", "insight": "Usa linguagem 100% definitiva para forçar honestidade", "chunks": ["chunk_15"], "tag": "[HEURISTICA]", "priority": "HIGH" },
      { "id": "INS-CG-018", "insight": "Categoriza objeções em Uncertainty, Support, Financial", "chunks": ["chunk_18"], "tag": "[FRAMEWORK]", "priority": "HIGH" }
    ]
  }
}
```

### Output (narrativa):
```json
{
  "persons": {
    "Cole Gordon": {
      "narrative": "Cole Gordon posiciona-se como defensor de PROCESSO sobre técnica no fechamento de vendas. Sua principal tese é que a maioria dos closers falha no final da call por falta de estrutura, não por falta de habilidade. Propõe o framework COMMITTING PHASE (Questions → Small Temp → What's Next) seguido de TIE DOWNS com linguagem definitiva ('100%') para isolar objeções reais. Diferencia objeções de INCERTEZA (verdadeiras) de LOGÍSTICA (Support/Financial), argumentando que só se deve tratar logística após resolver uncertainty.",
      "last_updated": "2025-12-15T15:30:00Z",
      "scope": "course",
      "corpus": "cursos",
      "insights_included": ["chunk_12", "chunk_15", "chunk_18"],
      "open_loops": [
        { "question": "Como funciona o Open Wallet Discovery?", "why_it_matters": "Mencionado mas não detalhado", "owner_suspected": "Cole Gordon" }
      ],
      "tensions": [],
      "next_questions": ["Buscar mais fontes de Cole sobre financial logistics"]
    }
  }
}
```

### Exemplo de MERGE (segunda rodada):

#### Estado ANTES (NARRATIVES-STATE.json):
```json
{
  "persons": {
    "Cole Gordon": {
      "narrative": "Cole Gordon posiciona-se como defensor de PROCESSO sobre técnica...",
      "insights_included": ["chunk_12", "chunk_15", "chunk_18"],
      "tensions": [],
      "open_loops": [
        { "question": "Como funciona o Open Wallet Discovery?", "status": "ABERTO" }
      ]
    }
  }
}
```

#### Novos insights (Input B):
```json
{
  "persons": {
    "Cole Gordon": [
      {
        "id": "INS-CG-040",
        "insight": "Open Wallet Discovery: perguntar 'quanto você pagaria para resolver isso?'",
        "chunks": ["chunk_40"],
        "tag": "[METODOLOGIA]",
        "priority": "HIGH"
      }
    ]
  }
}
```

#### Estado DEPOIS (MERGE aplicado):
```json
{
  "persons": {
    "Cole Gordon": {
      "narrative": "Cole Gordon posiciona-se como defensor de PROCESSO sobre técnica...\n\n--- Atualização 2024-12-16 via CG004 ---\n\nNova revelação sobre Open Wallet Discovery: técnica de perguntar diretamente ao prospect quanto pagaria para resolver o problema, validando budget antes de apresentar preço.",
      "insights_included": ["chunk_12", "chunk_15", "chunk_18", "chunk_40"],
      "tensions": [],
      "open_loops": [
        { "question": "Como funciona o Open Wallet Discovery?", "status": "RESOLVED", "resolution_source": "chunk_40" }
      ]
    }
  }
}
```

**Note:** `insights_included` fez APPEND (não substituiu), narrativa CONCATENOU, open_loop foi RESOLVIDO.

---

## SALVAMENTO

Salvar estado atualizado em: `/processing/narratives/NARRATIVES-STATE.json`

---

## ✓ CHECKPOINT APÓS EXECUÇÃO (OBRIGATÓRIO)

```
VALIDAR APÓS EXECUTAR:
[ ] CP-POST-5.A: narratives_state.persons[$SOURCE_PERSON].narrative existe
[ ] CP-POST-5.B: narrative.length > 100 caracteres
[ ] CP-POST-5.C: NARRATIVES-STATE.json foi salvo com sucesso

Se CP-POST-5.A falhar: ⛔ EXIT("Phase 5 não produziu narrativa para pessoa principal")
Se CP-POST-5.B falhar: ⛔ EXIT("Phase 5 produziu narrativa muito curta")
Se CP-POST-5.C falhar: ⛔ EXIT("Falha ao salvar NARRATIVES-STATE.json")
```

**BLOQUEANTE:** Não prosseguir para Etapa 4.0 se qualquer checkpoint falhar.

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 4.0: Dossier Compilation** (transformar JSON em Markdown acionável).
