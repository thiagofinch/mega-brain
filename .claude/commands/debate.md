---
description: Debate estruturado entre cargos com sintese de consensos e divergencias
argument-hint: [cargo1,cargo2,...] [decisao] - Ex: cro,cfo "Investir R$200k em ads?"
---

# /debate - Debate entre Cargos

## Descricao
Simula debate estruturado entre agentes de cargo, gerando sintese com consensos e divergencias.

## Uso
```
/debate [cargo1,cargo2,...] [pergunta ou decisao]
```

## Argumentos
- `cargos`: Lista de cargos separados por virgula (cro,cfo,sm)
- `pergunta`: A decisao a ser debatida

## Exemplos
```
/debate cro,cfo "Investir R$200k em ads no proximo trimestre?"
/debate cro,cfo,closer "Mudar modelo de comissao de % para fixo?"
```

---

## INSTRUCOES DE EXECUCAO

Seguir /system/protocols/conclave/DEBATE-PROTOCOL.md

```
═══════════════════════════════════════════════════════════════════════════════
DEBATE: {pergunta ou decisao}
DATA: {data atual}
PARTICIPANTES: {lista de cargos}
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: POSICOES INDIVIDUAIS                                                │
└─────────────────────────────────────────────────────────────────────────────┘

PARA CADA CARGO:

1. CARREGAR:
   - BASE-CONSTITUTION.md
   - DNA-CONFIG.yaml do cargo (se existir)
   - MEMORY.md do cargo (se existir)

2. APLICAR REASONING-MODEL-PROTOCOL.md

3. GERAR posicao no formato:

┌─ POSICAO: {CARGO} ──────────────────────────────────────────────────────────┐
│                                                                             │
│ RECOMENDACAO:                                                               │
│ {Posicao clara em 2-3 frases}                                              │
│                                                                             │
│ RACIOCINIO:                                                                 │
│ {Camadas de DNA usadas e como}                                             │
│                                                                             │
│ EVIDENCIAS:                                                                 │
│ • {ID}: "{citacao}"                                                        │
│ • {ID}: "{citacao}"                                                        │
│                                                                             │
│ CONFIANCA: {0-100}%                                                         │
│                                                                             │
│ LIMITACOES:                                                                 │
│ • {O que nao sei}                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: REBATIDAS CRUZADAS                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

CADA CARGO agora VE as posicoes dos outros e gera:

┌─ REBATIDA: {CARGO} ─────────────────────────────────────────────────────────┐
│                                                                             │
│ CONCORDO COM:                                                               │
│ • {CARGO X} sobre {ponto}: {por que}                                       │
│                                                                             │
│ DISCORDO DE:                                                                │
│ • {CARGO Y} sobre {ponto}: {por que + evidencia propria}                   │
│                                                                             │
│ PONTO CEGO IDENTIFICADO:                                                    │
│ • {CARGO Z} nao considerou: {aspecto}                                      │
│                                                                             │
│ MANTENHO MINHA POSICAO? {Sim/Nao/Parcialmente}                             │
│ {Se mudou, explicar por que}                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: SINTESE DO DEBATE                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
PONTOS DE CONSENSO (Alta confianca para decisao)
═══════════════════════════════════════════════════════════════════════════════

• {Ponto 1 que todos concordam}
• {Ponto 2 que todos concordam}

═══════════════════════════════════════════════════════════════════════════════
PONTOS DE DIVERGENCIA
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ DIVERGENCIA 1: {tema}                                                       │
│ ─────────────────────                                                       │
│ Natureza: {dados/prioridades/timing/risco}                                 │
│                                                                             │
│ • {CARGO1} defende: {posicao}                                              │
│ • {CARGO2} defende: {posicao}                                              │
│                                                                             │
│ Impacto se nao resolvido: {consequencia}                                   │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
TENSOES PRODUTIVAS (Nao resolver - sao features)
═══════════════════════════════════════════════════════════════════════════════

• {Tensao 1}: {Por que e produtiva}

═══════════════════════════════════════════════════════════════════════════════
LACUNAS IDENTIFICADAS
═══════════════════════════════════════════════════════════════════════════════

• {Informacao que ninguem tinha e precisa ser buscada}

═══════════════════════════════════════════════════════════════════════════════
```

---

## QUANDO ESCALAR PARA CONCLAVE

```
SE qualquer das condicoes:
  • Divergencia nao resolvida em tema CRITICO
  • Confianca media < 70%
  • Valor em risco > R$100k
  • Decisao irreversivel

ENTAO:
  Sugerir ao usuario: "Recomendo /conclave para meta-avaliacao"
```

---

## NOTAS

- Cada cargo defende SUA LENTE (CRO olha revenue, CFO olha unit economics)
- Divergencia explicita > consenso artificial
- Citar evidencias de DNA sempre que possivel
