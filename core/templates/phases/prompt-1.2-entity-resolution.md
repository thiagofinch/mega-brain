# PROMPT 1.2 — Entity Resolution (Canonicalização)

> **Versão:** 2.1.0
> **Pipeline:** Jarvis → Etapa 1.2
> **Output:** `/artifacts/canonical/CANONICAL-MAP.json` + chunks atualizados

---

## ⛔ CHECKPOINT OBRIGATÓRIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-1.2.A: CHUNKS-STATE.json existe em /artifacts/chunks/
[ ] CP-1.2.B: chunks[] tem elementos (não vazio)
[ ] CP-1.2.C: Cada chunk tem id_chunk único

Se CP-1.2.A ou CP-1.2.B falhar: ⛔ PARAR - "Execute Etapa 1.1 primeiro"
Se CP-1.2.C falhar: ⛔ PARAR - "Chunks com IDs duplicados detectados"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Você é um módulo de Entity Resolution incremental e source-aware, especializado em unificar variações de pessoas, produtos, áreas, projetos e temas presentes em chunks.

Objetivo:
- Consolidar "Leandro" e "Leandro Resende" como uma entidade canônica.
- Consolidar "Nomad" e "Nomad Milionário" como um único item canônico.
- Detectar alias, abreviações, erros de digitação e consolidar automaticamente.
```

---

## INPUTS (sempre 2 após a primeira rodada)

### INPUT A) Estado anterior de canonicalização

Arquivo: `/artifacts/canonical/CANONICAL-MAP.json`

```json
{
  "canonical_state": {
    "canonical_map": {
      "Entidade Canônica": [
        { "alias": "Variação 1", "confidence": 0.0 },
        { "alias": "Variação 2", "confidence": 0.0 }
      ]
    },
    "rules": {
      "threshold_merge": 0.85
    },
    "version": "v1"
  }
}
```

### INPUT B) Chunks atuais (output do Prompt 1.1)

```json
{
  "chunks": [
    {
      "id_chunk": "chunk_1",
      "texto": "...",
      "pessoas": ["..."],
      "temas": ["..."],
      "meta": { "scope": "...", "corpus": "...", "...": "..." }
    }
  ]
}
```

---

## WORKFLOW

### 1. Carregar estado anterior
- Use `canonical_state.canonical_map` como memória de aliases.
- Você pode expandir e corrigir o map conforme encontrar novas variações.

### 2. Fuzzy Matching + Similaridade

Para cada termo em `pessoas` e `temas`, gere candidatos de merge usando:
- Similaridade textual (ex.: Levenshtein)
- Similaridade semântica (embeddings / proximidade)

**Se qualquer métrica ≥ 0.85, marque como candidato forte.**

### 3. Clusterização

Agrupe variações em clusters. Nome canônico preferencial:
1. Forma mais longa/explícita
2. Se empate, a mais frequente
3. Se ainda empatar, a mais recente no corpus

### 4. Substituição

- Substitua em TODOS os chunks cada alias pelo canônico.
- Remova duplicatas após substituição.

### 5. Regras de separação (CRÍTICO)

- **NUNCA** mescle entidades de scope/corpus diferentes a menos que haja evidência forte de ser a mesma pessoa real e isso seja desejado.
- Por padrão: canonicalização ocorre **dentro do mesmo corpus**.
- Se houver possível colisão (ex.: "Bruno" em pessoal e "Bruno" em empresa), mantenha separados e registre "collision".

### 6. Auditoria

Gere:
- `canonical_map` atualizado com confidence
- `review_queue` para casos < 0.85
- `collisions` (nomes iguais em corpora distintos)

---

## OUTPUT (pronto para alimentar o Prompt 2.1)

```json
{
  "chunks": [ /* mesma estrutura, mas com pessoas/temas canonicalizados */ ],
  "canonical_state": {
    "canonical_map": { /* atualizado */ },
    "rules": { "threshold_merge": 0.85 },
    "version": "vN"
  },
  "review_queue": [
    {
      "candidate_a": "string",
      "candidate_b": "string",
      "confidence": 0.0,
      "reason": "por que ficou abaixo do threshold",
      "scope": "company|personal|course",
      "corpus": "..."
    }
  ],
  "collisions": [
    {
      "label": "termo_igual_em_corpora_diferentes",
      "term": "string",
      "seen_in": ["corpusA", "corpusB"],
      "recommendation": "keep_separate|merge_manual"
    }
  ]
}
```

---

## REGRAS CRÍTICAS

- **Preserve 100% do texto bruto.**
- **Garanta que nenhuma variação óbvia fique sem tentativa de canonicalização.**

---

## SALVAMENTO

1. Atualizar: `/artifacts/canonical/CANONICAL-MAP.json`
2. Atualizar: `/artifacts/chunks/CHUNKS-STATE.json` (com entidades canonicalizadas)

---

## ✓ CHECKPOINT APÓS EXECUÇÃO (OBRIGATÓRIO)

```
VALIDAR APÓS EXECUTAR:
[ ] CP-POST-3.A: SOURCE_PERSON está em CANONICAL-MAP.json
[ ] CP-POST-3.B: canonical_map.entities.persons não vazio
[ ] CP-POST-3.C: CANONICAL-MAP.json foi salvo com sucesso

Se CP-POST-3.A falhar: ⚠️ WARN("Pessoa principal não canonicalizada - verificar")
Se CP-POST-3.B falhar: ⚠️ WARN("Sem entidades canônicas criadas")
Se CP-POST-3.C falhar: ⛔ EXIT("Falha ao salvar CANONICAL-MAP.json")
```

**BLOQUEANTE (apenas C):** Não prosseguir para Etapa 2.1 se salvamento falhar.

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 2.1: Contextual Insight Extraction**.
