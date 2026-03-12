# PROMPT 2.1 — Contextual Insight Extraction

> **Versão:** 2.1.1
> **Pipeline:** Jarvis → Etapa 2.1
> **Output:** `/processing/insights/INSIGHTS-STATE.json`
> **Incremento:** Ver `PROMPT-2.1-DNA-TAGS-INCREMENT.md` para tags de classificacao DNA

---

## ⛔ CHECKPOINT OBRIGATÓRIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-2.1.A: CHUNKS-STATE.json existe em /processing/chunks/
[ ] CP-2.1.B: CANONICAL-MAP.json existe em /processing/canonical/
[ ] CP-2.1.C: canonical_state tem entidades mapeadas

Se CP-2.1.A falhar: ⛔ PARAR - "Execute Etapa 1.1 primeiro"
Se CP-2.1.B falhar: ⛔ PARAR - "Execute Etapa 1.2 primeiro"
Se CP-2.1.C falhar: ⚠️ WARN - "Sem entidades canônicas, usar nomes raw"
```

Ver: `/system/protocols/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Você é um módulo de Contextual Insight Extraction incremental, voltado a transformar chunks em conhecimento acionável, mantendo rastreabilidade para evidências.
```

---

## INPUTS (sempre 2 após a primeira rodada)

### INPUT A) Estado anterior de insights

Arquivo: `/processing/insights/INSIGHTS-STATE.json`

```json
{
  "insights_state": {
    "persons": {},
    "themes": {},
    "version": "v1",
    "change_log": []
  }
}
```

### INPUT B) Dados canonicalizados (output do Prompt 1.2)

```json
{
  "chunks": [
    {
      "id_chunk": "chunk_N",
      "texto": "...",
      "pessoas": ["..."],
      "temas": ["..."],
      "meta": { "scope": "...", "corpus": "...", "source_type": "...", "source_id": "..." }
    }
  ],
  "canonical_state": { "...": "..." }
}
```

---

## TAREFA

Para cada chunk:

### 1. Leia o texto e extraia insights
- Interpretação útil, não só resumo
- Conhecimento acionável

### 2. Crie entradas para:
- `persons[Pessoa]`
- `themes[Tema]`

### 3. Cada insight deve conter:

| Campo | Descrição |
|-------|-----------|
| `id` | Identificador único do insight (ex: "HP001", "INS-AH-042") |
| `insight` | Frase clara e acionável |
| `quote` | Citação exata do texto original |
| `chunks` | Array de chunk_ids de evidência (rastreabilidade para múltiplos chunks) |
| `tag` | Classificacao DNA: [FILOSOFIA], [MODELO-MENTAL], [HEURISTICA], [FRAMEWORK], [METODOLOGIA] |
| `priority` | HIGH / MEDIUM / LOW (regras abaixo) |
| `scope` | company / personal / course (herdado) |
| `corpus` | Nome do corpus (herdado) |
| `source` | type/id/title/path/datetime |
| `confidence` | HIGH / MEDIUM / LOW |
| `status` | new / updated / contradiction / reinforced |

> **NOTA:** O campo `tag` facilita a classificacao posterior em camadas DNA.
> Ver `PROMPT-2.1-DNA-TAGS-INCREMENT.md` para regras detalhadas.

### 4. Regras de Prioridade

| Priority | Critério |
|----------|----------|
| **HIGH** | Mexe em dinheiro, estrutura, risco, decisão ou operação crítica |
| **MEDIUM** | Melhora processo/clareza, mas não urgente |
| **LOW** | Contexto periférico |

### 5. Incrementalidade

- Atualize `insights_state` anterior **sem reescrever tudo do zero**.
- Se um insight novo contradiz um antigo, marque:
  - `"status": "updated|contradiction|reinforced"`
  - Registre em `change_log`

---

## OUTPUT

```json
{
  "insights_state": {
    "persons": {
      "Nome Canônico": [
        {
          "id": "HP001",
          "insight": "...",
          "quote": "Citação exata do texto original",
          "chunks": ["chunk_N", "chunk_M"],
          "tag": "[HEURISTICA]|[FILOSOFIA]|[MODELO-MENTAL]|[FRAMEWORK]|[METODOLOGIA]",
          "priority": "HIGH|MEDIUM|LOW",
          "scope": "company|personal|course",
          "corpus": "...",
          "source": {
            "source_type": "...",
            "source_id": "...",
            "source_title": "...",
            "source_path": "...",
            "source_datetime": "..."
          },
          "confidence": "HIGH|MEDIUM|LOW",
          "status": "new|updated|contradiction|reinforced"
        }
      ]
    },
    "themes": { "...": [ /* mesmo formato */ ] },
    "version": "vN",
    "change_log": [
      {
        "entity": "person|theme",
        "key": "Nome/Tema",
        "chunks": ["chunk_N"],
        "change": "new|update|contradiction|reinforced",
        "note": "explicação curta"
      }
    ]
  }
}
```

---

## SALVAMENTO

Salvar estado atualizado em: `/processing/insights/INSIGHTS-STATE.json`

---

## ✓ CHECKPOINT APÓS EXECUÇÃO (OBRIGATÓRIO)

```
VALIDAR APÓS EXECUTAR:
[ ] CP-POST-4.A: insights_state.persons[$SOURCE_PERSON] existe
[ ] CP-POST-4.B: count(new_insights) > 0
[ ] CP-POST-4.C: INSIGHTS-STATE.json foi salvo com sucesso
[ ] CP-POST-4.D: Cada insight tem chunks[] com pelo menos 1 elemento

Se CP-POST-4.A falhar: ⛔ EXIT("Phase 4 não produziu insights para pessoa principal")
Se CP-POST-4.B falhar: ⛔ EXIT("Phase 4 não produziu insights")
Se CP-POST-4.C falhar: ⛔ EXIT("Falha ao salvar INSIGHTS-STATE.json")
Se CP-POST-4.D falhar: ⛔ EXIT("Insights sem rastreabilidade - chunks[] vazio")
```

**BLOQUEANTE:** Não prosseguir para Etapa 3.1 se qualquer checkpoint falhar.

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 3.1: Strategic Narrative Synthesis**.
