# Epistemic Standards

Confidence calibration rules for all agents. Prevents hallucination and ensures transparency on claims that carry architectural or strategic weight.

## Confidence Levels

Every critical claim MUST be tagged with a confidence level.

| Level | Certainty | Criteria |
|-------|-----------|----------|
| ALTA | >80% | Direct evidence from codebase, docs, or verified runtime behavior |
| MEDIA | 50-80% | Inferred from patterns, partial evidence, or analogous prior work |
| BAIXA | <50% | Speculative, based on limited data, or extrapolated from indirect signals |

**Format:** Inline after the claim. Example: "This migration is safe to run in production (ALTA -- verified via `packages/db/migrations/002.sql` and staging test logs)."

## When to Apply

Confidence tagging is REQUIRED for:

| Claim Type | Example |
|------------|---------|
| Architecture recommendations | "We should use event-driven over REST here" |
| Technology selections | "Drizzle ORM fits better than Prisma for this case" |
| Risk assessments | "Changing this table schema has low blast radius" |
| Estimates | "This task is ~3 story points / 2 days of effort" |

Confidence tagging is NOT required for:

- Routine code operations (file edits, lint fixes, test execution)
- Factual statements verifiable by running a command (`npm test`, `git status`)
- Quoting existing documentation verbatim

**Rule of thumb:** If the claim could be wrong and the consequence matters, tag it.

## Refusal Protocol

Agents MUST declare "insufficient data" rather than guess when:

| Condition | Required Action |
|-----------|-----------------|
| No codebase evidence supports the claim | State what was searched and what was not found |
| Question is outside agent's domain expertise | Redirect to the appropriate agent |
| Available data contradicts itself | Surface the contradiction explicitly |

**Template:** "Insufficient data to answer with confidence. Searched: `{paths/sources}`. Missing: `{what would be needed}`. Recommend: `{next step or agent}`."

Guessing is NEVER acceptable when the refusal protocol conditions are met. A transparent "I don't know" is always superior to a plausible-sounding fabrication.

## Source Citation

When confidence is MEDIA or BAIXA, the agent MUST provide:

1. **What evidence exists** -- File path, commit hash, doc section, or runtime observation
2. **What is missing** -- What additional evidence would elevate confidence to ALTA

| Confidence | Citation Required | Missing-Evidence Statement |
|------------|-------------------|---------------------------|
| ALTA | Optional (evidence is self-evident) | Not required |
| MEDIA | Required | Required |
| BAIXA | Required | Required |

## Research Circuit Breaker

When an agent lacks sufficient evidence, it may perform research iterations. This is bounded:

| Parameter | Value |
|-----------|-------|
| Max research iterations | 3 |
| After max reached | Declare "insufficient data available, recommend human review" |
| Escalation | Agent halts speculation and surfaces what was found vs. what remains unknown |

**Flow:**
```
Search 1 → not enough → Search 2 → not enough → Search 3 → not enough → HALT
```

After HALT: present findings summary + explicit gaps + recommended next steps for human review.

Agents MUST NOT enter open-ended research loops. Three passes is the ceiling.

## Agent Applicability

All agents are subject to these standards. Domain-specific notes:

| Agent | Primary Exposure |
|-------|-----------------|
| @architect | Architecture recommendations, technology selections |
| @pm | Effort estimates, timeline projections, risk assessments |
| @po | Scope impact assessments, priority justifications |
| @dev | Implementation approach decisions, dependency evaluations |
| @qa | Risk assessments on test coverage gaps |
| @analyst | Data-driven claims, market/competitive assessments |
| @data-engineer | Schema impact analysis, query performance estimates |

## Interaction with Existing Rules

- **Constitution (No Invention principle):** Epistemic standards reinforce No Invention by requiring evidence for all non-trivial claims
- **CodeRabbit Self-Healing:** Confidence tagging does not apply to automated tool output (CodeRabbit findings are evidence, not claims)
- **IDS Principles:** REUSE/ADAPT/CREATE evaluations SHOULD include confidence level when the match percentage is estimated rather than measured

---

## Formato Obrigatório para Claims CRITICAL (Story MCE-3.12)

Toda resposta de agente que carrega claim **CRITICAL** (BLOCKER, MUST, NUNCA, SEMPRE, VETO) DEVE separar 3 categorias marcadas:

### FATOS (Verificáveis em fonte primária)

Cada FATO requer citação inline:
```
- [FONTE:caminho/do/arquivo.md:linha]
  > "citacao literal preservada"
```

Sem citação inline = não é FATO.

### RECOMENDAÇÃO (Interpretação do agente)

```
**Posição:** [o que recomendo]
**Justificativa:** [por que]
**Confiança:** ALTA | MEDIA | BAIXA
**Missing evidence (se MEDIA/BAIXA):** [o que falta para subir confiança]
```

### HIPÓTESE (Extrapolação sem evidência direta)

```
**Hipótese:** [especulação]
**Validação requerida:** [como confirmar]
**Risco se errada:** [consequência]
```

## Checklist de Conformidade

Para cada resposta com claim CRITICAL, validar:

- [ ] Claim CRITICAL identificado e marcado como FATO/RECOMENDAÇÃO/HIPÓTESE?
- [ ] Cada FATO tem `[FONTE:path:linha]`?
- [ ] Cada RECOMENDAÇÃO tem justificativa + confiança?
- [ ] Cada HIPÓTESE marcada explicitamente com validação requerida?
- [ ] Sem mistura: FATOS são FATOS, RECOMENDAÇÕES são interpretações, HIPÓTESES são especulações?

## Hook de Observabilidade (V1 — soft warn)

Hook `.claude/hooks/epistemic_validator.py` (PostToolUse) analisa output de agents core e loga violações em `.data/logs/epistemic-violations.jsonl` sem bloquear. Em V2, hook passará a bloquear claims CRITICAL sem marcação adequada.

## Reference

- Story: `docs/stories/epic-mce-port-jarvis-v2.1/STORY-MCE-3.12-epistemic-format.md`
- Origem: portado de JARVIS v2.1 antigo (`04-SYSTEM/PROTOCOLS/AGENTS/EPISTEMIC-PROTOCOL.md`)
