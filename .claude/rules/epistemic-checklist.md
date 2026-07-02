# Epistemic Checklist — Quick Reference

> Use antes de finalizar respostas com claim CRITICAL.
> Story origem: MCE-3.12

## Detectar Claim CRITICAL

Claim e CRITICAL quando contem:

- Palavras-chave: NUNCA, SEMPRE, MUST, BLOCKER, CRITICAL, VETO, REQUIRED
- Decisao arquitetural irrevogavel
- Risk assessment com blast radius alto
- Recomendacao de tecnologia/abordagem

## Checklist (5 perguntas)

- [ ] **C1:** Identifiquei se a resposta carrega claim CRITICAL?
- [ ] **C2:** Separei em 3 secoes (FATOS / RECOMENDACAO / HIPOTESE) se sim?
- [ ] **C3:** Cada FATO tem `[FONTE:path:linha]` inline?
- [ ] **C4:** Cada RECOMENDACAO tem `Posicao + Justificativa + Confianca`?
- [ ] **C5:** Cada HIPOTESE marca explicitamente "sem evidencia direta"?

## Exemplos Rapidos

### ✅ CORRETO

```
## FATOS
- [FONTE:engine/intelligence/pipeline/mce/orchestrate.py:4644]
  > "cmd_full encadeia 12 cmds"

## RECOMENDACAO
**Posicao:** portar Quick Wins primeiro
**Justificativa:** 50% valor / 15% esforco (audit appendix C)
**Confianca:** ALTA
```

### ❌ ERRADO (claim CRITICAL sem marcacao)

```
NUNCA permitir pipeline rodar sem CHECKPOINT-ENFORCEMENT.
```

(Faltou: e isso FATO? RECOMENDACAO? Hipotese? Cite fonte.)

### ✅ CORRECAO

```
## RECOMENDACAO
**Posicao:** Pipeline NUNCA deve rodar sem CHECKPOINT-ENFORCEMENT
**Justificativa:** Sem CP, atalhos viram silent failures (audit appendix A.4)
**Confianca:** ALTA
```

## Quando NAO Aplicar

- Conversa casual (sem decisao tecnica)
- Resposta a pergunta factual simples
- Code edit operacional rotineiro
- Confirmacao "vou rodar X" antes de tool call

## Referencia

`.claude/rules/epistemic-standards.md` — regra completa
