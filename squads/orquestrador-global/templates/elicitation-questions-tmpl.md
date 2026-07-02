<!-- Consumer: PA-6.1 (plan-architect L1 elicitation gate output) -->
<!-- Schema: elicitation produzida quando confidence < threshold; max 3 questions per blueprint §7.2 -->

# Elicitação — `{plan_id}`

> **Contexto:** {context_brief}
> **Confidence inicial:** {confidence_inicial} (< {threshold} → elicitação acionada)
> **Max questions:** 3 (information-gain ranked)

## Perguntas Priorizadas

### Pergunta 1 — `{dimension}`

**Pergunta:** {question}

**Por que precisa:** {why_needed}

**Info-gain score:** {score}

**Resposta esperada:** {format/example}

---

### Pergunta 2 — `{dimension}`

**Pergunta:** {question}

**Por que precisa:** {why_needed}

**Info-gain score:** {score}

**Resposta esperada:** {format/example}

---

### Pergunta 3 — `{dimension}` (opcional)

**Pergunta:** {question}

**Por que precisa:** {why_needed}

**Info-gain score:** {score}

**Resposta esperada:** {format/example}

---

## Regra de Parada

- Após 3 perguntas, `plan-architect` prossegue mesmo se confidence ainda < threshold
- Warning é incluído no plano: `confidence_after_elicitation: 0.X (< threshold) — proceed with caveats`

## Example

> **Contexto:** Demanda "Lançar curso de IA pra Black Friday"
> **Confidence inicial:** 0.62 (< 0.70 → elicitação acionada)
> **Max questions:** 3

### Pergunta 1 — `scope`

**Pergunta:** O lançamento inclui apenas o curso novo ou também upsell de cursos existentes?

**Por que precisa:** Scope determina se `megabrain-sales` squad é envolvido (upsell) ou apenas `course-creator` (novo). Diferença de ~$500 em estimativa.

**Info-gain score:** 0.85 (max var entre 2 caminhos completamente distintos)

**Resposta esperada:** "apenas curso novo" / "também upsell" / "decidir após análise"

---

### Pergunta 2 — `deadline`

**Pergunta:** Qual é o último dia útil aceitável para o curso estar publicado?

**Por que precisa:** "Black Friday" pode ser flexível (last week of Nov) ou rígido. Define se DAG precisa fast-track ou pode ter mais quality gates.

**Info-gain score:** 0.72

**Resposta esperada:** Data ISO ou "flexível na semana de BF"

---

### Pergunta 3 — `success_criteria`

**Pergunta:** Qual é o número mínimo de inscrições que torna o lançamento bem-sucedido?

**Por que precisa:** Define se DAG inclui pre-launch list-building (alto custo) ou apenas launch-week push.

**Info-gain score:** 0.68

**Resposta esperada:** Número absoluto ou "definir com @pm"
