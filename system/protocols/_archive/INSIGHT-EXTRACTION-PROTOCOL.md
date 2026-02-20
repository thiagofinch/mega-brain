# INSIGHT EXTRACTION PROTOCOL (Prompt 2.1)

> **Versão:** 1.0.0
> **Pipeline:** Jarvis → Etapa 2.1
> **Output:** `/processing/insights/INSIGHTS-STATE.json`

---

## PROPÓSITO

Extrair insights acionáveis dos chunks, organizados por:
- Pessoa (o que essa pessoa pensa/faz)
- Tema (o que sabemos sobre esse assunto)
- Prioridade (HIGH/MEDIUM/LOW)

---

## INPUTS

### Input A: chunks_resolved (output do Prompt 1.2)
```json
{
  "chunks_resolved": {
    "chunks": [
      {
        "id_chunk": "chunk_001",
        "content": "...",
        "mentions_canonical": {
          "persons": ["Alex Hormozi"],
          "themes": ["comissionamento"]
        }
      }
    ]
  }
}
```

### Input B: insights_state (estado acumulado anterior)
```json
{
  "insights_state": {
    "persons": { /* insights existentes */ },
    "themes": { /* insights existentes */ }
  }
}
```

---

## TAREFA

### 1. Para cada chunk, extrair insights sobre:

#### PESSOA mencionada:
- O que essa pessoa PENSA sobre algo?
- O que essa pessoa FAZ ou recomenda?
- Qual padrão comportamental/decisório aparece?

#### TEMA mencionado:
- Que conhecimento factual é transmitido?
- Que framework ou modelo é apresentado?
- Que métrica ou benchmark é mencionado?

### 2. Classificação de Prioridade

| Prioridade | Critério | Exemplo |
|------------|----------|---------|
| **HIGH** | Decisão, framework, número específico, recomendação direta | "25-30% comissão para closers" |
| **MEDIUM** | Contexto, explicação, nuance | "Isso funciona melhor em high-ticket" |
| **LOW** | Opinião genérica, anedota, filler | "Eu sempre digo que..." |

### 3. Estrutura do Insight

```json
{
  "id_insight": "insight_{chunk_id}_{sequential}",
  "id_chunk": "chunk_001",
  "insight": "Hormozi recomenda comissão de 25-30% para closers em high-ticket",
  "insight_type": "recommendation|fact|pattern|metric|framework",
  "priority": "high|medium|low",
  "entity_type": "person|theme",
  "entity_canonical": "Alex Hormozi",
  "related_themes": ["comissionamento", "closer"],
  "evidence": "Citação exata ou referência do chunk",
  "confidence": "high|medium|low",
  "source": {
    "source_type": "call|video|doc",
    "source_title": "Título",
    "source_datetime": "YYYY-MM-DD"
  }
}
```

---

## OUTPUT

### insights_state (atualizado)
```json
{
  "insights_state": {
    "version": "1.0.0",
    "last_updated": "YYYY-MM-DD HH:MM:SS",
    "total_insights": 156,

    "persons": {
      "Alex Hormozi": [
        {
          "id_insight": "insight_chunk001_001",
          "id_chunk": "chunk_001",
          "insight": "Recomenda comissão de 25-30% para closers de high-ticket",
          "insight_type": "recommendation",
          "priority": "high",
          "related_themes": ["comissionamento", "closer", "high-ticket"],
          "evidence": "\"A estrutura de comissão que funciona é simples: 25-30% do valor do deal para o closer.\"",
          "confidence": "high",
          "source": {
            "source_type": "video",
            "source_title": "Podcast Ep. 234",
            "source_datetime": "2025-12-12"
          }
        },
        {
          "id_insight": "insight_chunk003_001",
          "id_chunk": "chunk_003",
          "insight": "Prioriza velocidade de execução sobre planejamento perfeito",
          "insight_type": "pattern",
          "priority": "high",
          "related_themes": ["gestão", "execução", "decisão"],
          "evidence": "\"Ship it. You can fix it later.\"",
          "confidence": "high",
          "source": { /* ... */ }
        }
      ],

      "Cole Gordon": [
        {
          "id_insight": "insight_chunk015_001",
          "id_chunk": "chunk_015",
          "insight": "Framework CLOSER para estruturar calls de vendas",
          "insight_type": "framework",
          "priority": "high",
          "related_themes": ["fechamento", "processo-vendas", "closer"],
          "evidence": "\"CLOSER: Clarify, Label, Overview, Sell, Explain, Reinforce\"",
          "confidence": "high",
          "source": { /* ... */ }
        }
      ]
    },

    "themes": {
      "comissionamento": [
        {
          "id_insight": "insight_chunk001_001",
          "id_chunk": "chunk_001",
          "insight": "Benchmark de 25-30% para closers em high-ticket",
          "insight_type": "metric",
          "priority": "high",
          "related_persons": ["Alex Hormozi"],
          "evidence": "\"25-30% do valor do deal para o closer\"",
          "confidence": "high",
          "source": { /* ... */ }
        },
        {
          "id_insight": "insight_chunk008_001",
          "id_chunk": "chunk_008",
          "insight": "Comissão baixa (10-15%) causa perda de talentos",
          "insight_type": "fact",
          "priority": "medium",
          "related_persons": ["Alex Hormozi"],
          "evidence": "\"Você está competindo com quem paga o dobro\"",
          "confidence": "high",
          "source": { /* ... */ }
        }
      ],

      "estrutura-time": [
        /* ... insights sobre estrutura de time ... */
      ]
    },

    "stats": {
      "by_priority": { "high": 45, "medium": 78, "low": 33 },
      "by_type": { "recommendation": 34, "fact": 56, "pattern": 23, "metric": 18, "framework": 25 },
      "by_person": { "Alex Hormozi": 47, "Cole Gordon": 32: 28 }
    }
  }
}
```

---

## REGRAS DE EXTRAÇÃO

### FAZER:
- Extrair insight mesmo que chunk tenha múltiplos
- Preservar citação exata como evidência
- Classificar prioridade com rigor (não tudo é HIGH)
- Linkar insight tanto à pessoa quanto aos temas
- Manter rastreabilidade completa (chunk_id → insight)

### NÃO FAZER:
- Inventar insights não presentes no chunk
- Elevar prioridade de opinião genérica
- Criar insight duplicado de chunk anterior
- Perder números/métricas específicas

---

## REGRAS DE MERGE

### Ao processar novo chunk:

1. **Insight novo sobre pessoa existente:**
   - ADICIONAR à lista da pessoa
   - Verificar se não é duplicata

2. **Insight novo sobre tema existente:**
   - ADICIONAR à lista do tema
   - Cross-reference com pessoa se aplicável

3. **Insight que CONFIRMA existente:**
   - ADICIONAR como insight separado (reforça confiança)
   - Linkar via `related_insights: ["insight_anterior_id"]`

4. **Insight que CONTRADIZ existente:**
   - ADICIONAR como insight separado
   - Marcar `contradiction_with: ["insight_id"]`
   - NÃO resolver — documentar tensão

---

## DEDUPLICAÇÃO

Antes de adicionar, verificar se insight similar já existe:

| Critério | Ação |
|----------|------|
| Mesma pessoa + mesmo insight + mesma fonte | SKIP (duplicata exata) |
| Mesma pessoa + mesmo insight + fonte diferente | ADD (reforço) |
| Mesma pessoa + insight similar + mais detalhado | ADD (refinamento) |
| Pessoa diferente + mesmo tema | ADD (perspectiva diferente) |

---

## SALVAMENTO

```
/processing/insights/INSIGHTS-STATE.json
```
(Arquivo único, atualizado incrementalmente)

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 3.1: Narrative Synthesis** para síntese narrativa por entidade.
