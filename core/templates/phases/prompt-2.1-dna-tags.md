# PROMPT 2.1 — DNA Tags Increment
# Incremento para adicionar classificacao de camadas DNA durante extracao de insights

> **Versao:** 1.0.0
> **Aplica-se a:** PROMPT-2.1-INSIGHT-EXTRACTION.md
> **Proposito:** Adicionar tags de classificacao para facilitar extracao de DNA

---

## OBJETIVO

Durante a extracao de insights (Phase 2.1), adicionar campo `tag` que pre-classifica
o insight em uma das 5 camadas do DNA Cognitivo:

```
[FILOSOFIA]        → Crenca fundamental, principio
[MODELO-MENTAL]    → Lente de analise, forma de ver
[HEURISTICA]       → Regra com threshold numerico
[FRAMEWORK]        → Estrutura nomeada com componentes
[METODOLOGIA]      → Processo passo-a-passo
```

---

## REGRAS DE CLASSIFICACAO

### [FILOSOFIA]
```
IDENTIFICA QUANDO:
• Declaracao de crenca ou valor
• Frase "Eu acredito que...", "A verdade e que..."
• Principio sem numero ou threshold
• Aparece em contextos diversos (generaliza)

EXEMPLOS:
• "Volume is vanity, profit is sanity"
• "Competence over experience"
• "If in doubt, fire them"
```

### [MODELO-MENTAL]
```
IDENTIFICA QUANDO:
• Pergunta que muda como voce VE algo
• Forma de estruturar analise
• "Pense assim...", "A forma de ver isso e..."
• Gera INSIGHT, nao ACAO direta

EXEMPLOS:
• "Always ask: what would make this fail?"
• "Think of hiring like farming, not hunting"
• "View objections as buying signals"
```

### [HEURISTICA]
```
IDENTIFICA QUANDO:
• Tem NUMERO ou THRESHOLD
• Formato "Se X entao Y"
• Regra acionavel com gatilho claro
• Pode ser verificada

EXEMPLOS:
• "If close rate < 30%, problem is upstream"
• "Ramp time should be 90 days max"
• "Show rate below 80% means confirmation problem"

PRIORIDADE MAXIMA:
Heuristicas com numeros sao os itens mais valiosos do DNA.
```

### [FRAMEWORK]
```
IDENTIFICA QUANDO:
• Estrutura NOMEADA (acronimo ou nome proprio)
• Tem COMPONENTES definidos
• NAO tem ordem rigida de execucao
• E uma FERRAMENTA de analise ou construcao

EXEMPLOS:
• "5 Armas do Closer"
• "SPIN Questions"
• "$100M Offer Framework"
```

### [METODOLOGIA]
```
IDENTIFICA QUANDO:
• Processo com PASSOS sequenciais
• Ordem IMPORTA (Passo 1 antes de Passo 2)
• Tem criterio de sucesso por etapa
• E um PROCESSO, nao uma ferramenta

EXEMPLOS:
• "3-step onboarding process"
• "Call flow from intro to close"
• "Hiring funnel methodology"
```

---

## ATUALIZACAO DO OUTPUT

### Novo campo no insight

```json
{
  "id": "INS-AH-042",
  "insight": "Close rate below 30% indicates qualification problem",
  "quote": "If your close rate is below 30%, you don't have a closing problem...",
  "chunks": ["AH-SS001-chunk_198"],
  "tag": "[HEURISTICA]",
  "priority": "HIGH",
  "scope": "company",
  "corpus": "Sales Scaling",
  ...
}
```

### Multiplas tags (quando aplicavel)

```json
{
  "tag": "[HEURISTICA][FILOSOFIA]"
}
```

Usar multiplas tags quando insight claramente se encaixa em mais de uma camada.

---

## REGRAS DE PRIORIDADE PARA TAGS

```
1. HEURISTICA prevalece quando tem numero
   "Fire at 30 days" → [HEURISTICA] (nao [FILOSOFIA])

2. METODOLOGIA prevalece quando tem passos
   "Step 1: X, Step 2: Y" → [METODOLOGIA] (nao [FRAMEWORK])

3. Na duvida, usar tag menos especifica
   Se nao tem certeza entre HEURISTICA e FILOSOFIA → [FILOSOFIA]
```

---

## INTEGRACAO COM DNA-EXTRACTION

Quando o DNA-EXTRACTION-PROTOCOL processar INSIGHTS-STATE.json:

1. Filtrar por tag para acelerar classificacao
2. `[HEURISTICA]` → vai para HEURISTICAS.yaml
3. `[FILOSOFIA]` → vai para FILOSOFIAS.yaml
4. etc.

A tag NAO e definitiva - DNA-EXTRACTION pode reclassificar se necessario.
A tag acelera o processo, nao o substitui.

---

## CHECKPOINT

```
VALIDAR APOS EXECUTAR:
[ ] Todos os insights HIGH priority tem tag
[ ] Tags usam formato padrao [NOME]
[ ] Nao ha tags fora das 5 camadas
```

---

## EXEMPLO COMPLETO

### Input (chunk)
```
"If your close rate is below 30%, you don't have a closing problem,
you have a qualification problem. The issue is upstream."
```

### Output (insight com tag)
```json
{
  "id": "INS-AH-042",
  "insight": "Close rate below 30% indicates qualification problem, not closing problem",
  "quote": "If your close rate is below 30%, you don't have a closing problem, you have a qualification problem.",
  "chunks": ["AH-SS001-chunk_198"],
  "tag": "[HEURISTICA]",
  "priority": "HIGH",
  "scope": "company",
  "corpus": "Sales Scaling",
  "source": {
    "source_type": "video",
    "source_id": "AH-SS001",
    "source_title": "How I Scaled My Sales Team"
  },
  "confidence": "HIGH",
  "status": "new"
}
```

---

## NOTAS

- Tags sao opcionais para insights LOW priority
- Tags facilitam mas NAO substituem classificacao no DNA-EXTRACTION
- Insights podem mudar de camada durante extracao completa
- O valor esta na consistencia, nao na perfeicao
