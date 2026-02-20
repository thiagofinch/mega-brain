---
description: Compara perspectivas de 2+ pessoas sobre uma pergunta (sem sintetizar)
argument-hint: [pessoa1,pessoa2,...] [pergunta] - Ex: hormozi,cole "Qual comissao ideal?"
---

# /compare - Comparacao entre Personas

## Descricao
Compara as perspectivas de 2+ pessoas sobre uma pergunta, mostrando convergencias e divergencias SEM sintetizar.

## Uso
```
/compare [pessoa1,pessoa2,...] [pergunta]
```

## Argumentos
- `pessoas`: Lista de personas separadas por virgula (hormozi,cole,sam)
- `pergunta`: A pergunta para comparacao

## Exemplos
```
/compare hormozi,cole "Qual comissao ideal para closers?"
/compare hormozi,cole,sam "Como estruturar compensation de time de vendas?"
```

---

## INSTRUCOES DE EXECUCAO

```
1. PARA CADA PESSOA na lista:

   a) CARREGAR DNA (se existir):
      /knowledge/dna/persons/{PESSOA}/

   b) SE NAO existir DNA, carregar DOSSIER:
      /knowledge/dossiers/persons/DOSSIER-{PESSOA}.md

   c) IDENTIFICAR posicao sobre a pergunta:
      - Buscar heuristicas relevantes
      - Buscar filosofias relacionadas
      - Buscar frameworks aplicaveis

2. GERAR OUTPUT no formato:

═══════════════════════════════════════════════════════════════════════════════
COMPARACAO: {pergunta}
PESSOAS: {lista de pessoas}
═══════════════════════════════════════════════════════════════════════════════

┌─ PERSPECTIVA: {PESSOA 1} ───────────────────────────────────────────────────┐
│                                                                             │
│ POSICAO:                                                                    │
│ {Resumo da posicao em 2-3 frases}                                          │
│                                                                             │
│ EVIDENCIAS:                                                                 │
│ • {ID}: "{citacao}"                                                        │
│ • {ID}: "{citacao}"                                                        │
│                                                                             │
│ NUMEROS/THRESHOLDS (se houver):                                            │
│ • {metrica}: {valor}                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ PERSPECTIVA: {PESSOA 2} ───────────────────────────────────────────────────┐
│                                                                             │
│ POSICAO:                                                                    │
│ {Resumo da posicao em 2-3 frases}                                          │
│                                                                             │
│ ... (mesmo formato)                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
CONVERGENCIAS (onde concordam)
═══════════════════════════════════════════════════════════════════════════════

• {Ponto de convergencia 1}
  Evidencia: {PESSOA1} ({ID}) + {PESSOA2} ({ID})

• {Ponto de convergencia 2}
  ...

═══════════════════════════════════════════════════════════════════════════════
DIVERGENCIAS (onde discordam)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ DIVERGENCIA 1: {tema}                                                       │
│ ─────────────────────                                                       │
│                                                                             │
│ • {PESSOA1}: {posicao} ({ID})                                              │
│ • {PESSOA2}: {posicao} ({ID})                                              │
│                                                                             │
│ Natureza: {thresholds diferentes / acoes diferentes / filosofias opostas} │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
```

3. REGRAS IMPORTANTES:

   - NAO sintetizar ou recomendar qual posicao seguir
   - NAO resolver divergencias
   - APENAS apresentar as perspectivas lado a lado
   - CITAR evidencias sempre que disponivel
   - SE uma pessoa nao tem posicao clara, declarar explicitamente
```

---

## NOTAS

- Este comando NAO recomenda qual perspectiva seguir
- Para obter recomendacao, usar /debate ou /conclave
- Se uma pessoa nao tem conhecimento sobre o tema, declarar
