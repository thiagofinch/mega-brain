# Elicitation Framework — `intent-parser` Inline Logic

> **Consumer:** `agents/intent-parser.md` (inline elicitation step per blueprint §13.1 row 3)
> **Story:** STORY-PA-2.1
> **Princípio:** pergunte SE e SOMENTE SE confidence < threshold; max 3 perguntas; priorize por information-gain

---

## Quando elicitar

**Threshold gate (default 0.7 em `data/intent-taxonomy.yaml`):**

- `parsed.confidence ≥ 0.7` → não pergunta. Prossegue silenciosamente.
- `parsed.confidence < 0.7` → elicitação acionada. Max 3 perguntas.
- Se após 3 perguntas confidence ainda < 0.7 → emite plano com warning, não loopa.

**Anti-pattern:** perguntar "por garantia" mesmo com alta confidence. Cada pergunta é fricção; só vale a pena se reduz incerteza materialmente.

---

## Information-Gain Ranking

Cada pergunta candidata tem um **info-gain score** que aproxima quanto a resposta vai reduzir variance no plano. Score 0-1.

**Formula heurística:**

```
info_gain = variance_reduction × downstream_impact

variance_reduction = max(0, prior_variance - posterior_variance)
downstream_impact = N de nós do DAG afetados por essa decisão
```

**Algoritmo:**

1. Liste todas as perguntas candidatas (uma por dimensão da seção abaixo)
2. Para cada candidata, estime info-gain
3. Ordene desc por score
4. Pegue as 3 com maior gain
5. Apresente em ordem (não pergunte tudo de uma vez — apresentar 1-3 numeradas é OK)

---

## 4 Dimensões de Elicitação

### 1. Scope

**Foco:** O que está IN e o que está OUT do trabalho.

**Boa pergunta:**
> "O lançamento inclui apenas o curso novo OU também upsell de cursos existentes?"

**Por que é boa:** Variance alta entre os dois caminhos (squads diferentes envolvidos), downstream impact alto (~$500 diferença em estimativa).

**Anti-pattern:**
> "Você quer fazer um lançamento bom?"

**Por que é ruim:** Resposta óbvia (sim), zero info-gain.

---

### 2. Deadline

**Foco:** Quando precisa estar pronto.

**Boa pergunta:**
> "Qual é o último dia útil aceitável para o curso estar publicado?"

**Por que é boa:** Variance alta entre "flexível" vs "rígido", afeta paralelização do DAG.

**Anti-pattern:**
> "Quando você precisa?"

**Por que é ruim:** Vago. Resposta vai ser "rápido" — não-acionável.

---

### 3. Success Criteria

**Foco:** Como saber se deu certo.

**Boa pergunta:**
> "Qual é o número mínimo de inscrições que torna o lançamento bem-sucedido?"

**Por que é boa:** Threshold mensurável; define se DAG inclui pre-launch list-building (alto custo) ou apenas launch-week push.

**Anti-pattern:**
> "Quer que dê certo?"

**Por que é ruim:** Resposta óbvia, zero info-gain.

---

### 4. Constraints

**Foco:** Restrições não-óbvias que limitam o solution space.

**Boa pergunta:**
> "Existe alguma BU que NÃO pode ser envolvida nesse lançamento (ex: separação fiscal, política interna)?"

**Por que é boa:** Restrições não-óbvias têm downstream impact alto (mudam business_units no parsed output).

**Anti-pattern:**
> "Tem alguma restrição?"

**Por que é ruim:** Genérico demais; respondente vai dizer "não" mesmo quando há restrição. Deve ser específico (BU? budget? tech? prazo?).

---

## Max-3 Rule

**Por que 3 e não 5 ou 10:**

- Pergunta 1: cobre dimensão de maior info-gain
- Pergunta 2: cobre segunda dimensão (já reduziu metade da variance)
- Pergunta 3: cobre terceira (margem decrescente)
- Pergunta 4+: usuário se cansa, qualidade das respostas cai, plano pode ser feito com confidence parcial e warning

**Se 3 perguntas não bastarem:** emita plano com `confidence_after_elicitation: 0.X (< threshold) — proceed with caveats` no audit log e marque hipóteses parciais como `falsifiable_assumptions`.

---

## Anti-Question Patterns

| Pattern | Por que evitar |
|---|---|
| **Múltiplas perguntas em uma** | "Qual o prazo, budget e BU?" → resposta confusa, sem nesting; melhor 3 perguntas separadas. |
| **Pergunta com resposta óbvia** | "Você quer que o produto funcione?" → zero info-gain. |
| **Pergunta que revela ignorância demais** | "O que é uma SOP?" → user perde confiança no agente. |
| **Pergunta que requer pesquisa do user** | "Qual o ARR do segmento?" → user vai abandonar. |
| **Pergunta sobre detalhe técnico que o agente deveria saber** | "Qual framework usar?" → o plan-architect decide isso, não pergunta. |

---

## Examples — Good Elicitation Round

**Demanda:** "Quero lançar curso de IA pra Black Friday"
**Confidence inicial:** 0.62

**3 perguntas com info-gain ranked:**

1. **(scope, gain 0.85)** "O lançamento inclui apenas o curso novo ou também upsell de cursos existentes?"
2. **(deadline, gain 0.72)** "Qual é o último dia útil aceitável para o curso estar publicado?"
3. **(success, gain 0.68)** "Qual é o número mínimo de inscrições que torna o lançamento bem-sucedido?"

**Após respostas:** confidence sobe para 0.88. Plano segue.

---

## Telemetria (audit trail)

Cada elicitação registra em `audit.elicitation_log`:

```yaml
audit:
  elicitation_triggered: true
  initial_confidence: 0.62
  questions_asked: 3
  questions:
    - dimension: scope
      info_gain: 0.85
      answer: "apenas curso novo"
    - dimension: deadline
      info_gain: 0.72
      answer: "última semana de novembro"
    - dimension: success
      info_gain: 0.68
      answer: "100 inscrições"
  final_confidence: 0.88
  threshold_met: true
```

Telemetria alimenta `wf-plan-quality-loop` (BL-2 backlog) para auto-tunagem futura.
