# DEBATE-PROTOCOL
# Debate Estruturado entre Agentes de Cargo

> **Versao:** 1.1.0
> **Trigger:** Comando /debate ou decisao que requer multiplas perspectivas
> **Participantes:** Agentes de CARGO (CRO, CFO, SM, etc.)
> **Output:** Sintese com consensos, divergencias e tensoes produtivas
> **Dinamica:** Regida por DEBATE-DYNAMICS-PROTOCOL.md
> **Config:** DEBATE-DYNAMICS-CONFIG.yaml

---

## PROTOCOLOS RELACIONADOS

| Protocolo | Path | Funcao |
|-----------|------|--------|
| DEBATE-DYNAMICS | `./DEBATE-DYNAMICS-PROTOCOL.md` | Dinamica de rodadas e timeouts |
| CONCLAVE-PROTOCOL | `./CONCLAVE-PROTOCOL.md` | Meta-avaliacao pelo Conselho |
| CONSTITUICAO-BASE | `core/templates/CONSTITUICAO-BASE.md` | Principios fundamentais |

---

## PROPOSITO

O debate entre agentes de cargo serve para:
1. Obter MULTIPLAS PERSPECTIVAS sobre uma decisao
2. Identificar PONTOS CEGOS de cada lente
3. Explicitar TENSOES entre objetivos diferentes
4. Preparar input para o CONSELHO (se necessario)

---

## ESTRUTURA DO DEBATE (3 Fases)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 1: POSICOES INDIVIDUAIS (Paralelo)                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  Cada agente de cargo responde ISOLADAMENTE:                               │
│  • Sem ver respostas dos outros                                            │
│  • Aplicando REASONING-MODEL-PROTOCOL completo                             │
│  • Gerando: posicao + raciocinio + evidencias + confianca + limitacoes     │
│                                                                             │
│  Formato de output por agente:                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [POSICAO: {CARGO}]                                                  │   │
│  │                                                                     │   │
│  │ RECOMENDACAO:                                                       │   │
│  │ {Posicao clara em 2-3 frases}                                      │   │
│  │                                                                     │   │
│  │ RACIOCINIO:                                                         │   │
│  │ {Camadas de DNA usadas e como}                                     │   │
│  │                                                                     │   │
│  │ EVIDENCIAS:                                                         │   │
│  │ • {ID}: "{citacao}"                                                │   │
│  │                                                                     │   │
│  │ CONFIANCA: {0-100}%                                                 │   │
│  │                                                                     │   │
│  │ LIMITACOES:                                                         │   │
│  │ • {O que nao sei}                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 2: REBATIDAS CRUZADAS (Apos ver posicoes dos outros)                  │
│  ═════════════════════════════════════════════════════════                  │
│                                                                             │
│  Cada agente agora VE as posicoes dos outros e:                            │
│                                                                             │
│  2.1 Identifica CONCORDANCIAS:                                             │
│      "Concordo com {CARGO} sobre {ponto especifico}"                       │
│      → Reforca a posicao, pode citar DNA adicional                         │
│                                                                             │
│  2.2 Identifica DIVERGENCIAS:                                               │
│      "Discordo de {CARGO} sobre {ponto} porque..."                         │
│      → Citar DNA proprio que fundamenta divergencia                        │
│      → NAO e ataque pessoal, e confronto de evidencias                     │
│                                                                             │
│  2.3 Identifica PONTOS CEGOS nos outros:                                    │
│      "{CARGO} nao considerou {aspecto} que afeta {consequencia}"           │
│      → Trazer perspectiva que o outro nao tem                              │
│                                                                             │
│  Formato:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [REBATIDA: {CARGO}]                                                 │   │
│  │                                                                     │   │
│  │ CONCORDO COM:                                                       │   │
│  │ • {CARGO X} sobre {ponto}: {por que}                               │   │
│  │                                                                     │   │
│  │ DISCORDO DE:                                                        │   │
│  │ • {CARGO Y} sobre {ponto}: {por que + evidencia propria}           │   │
│  │                                                                     │   │
│  │ PONTO CEGO IDENTIFICADO:                                            │   │
│  │ • {CARGO Z} nao considerou: {aspecto}                              │   │
│  │                                                                     │   │
│  │ MANTENHO MINHA POSICAO? {Sim/Nao/Parcialmente}                     │   │
│  │ {Se mudou, explicar por que}                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FASE 3: SINTESE DO DEBATE                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  Apos rebatidas, gerar sintese estruturada:                                │
│                                                                             │
│  3.1 PONTOS DE CONSENSO                                                     │
│      O que TODOS os cargos concordam                                       │
│      → Estes sao os pontos mais seguros                                    │
│                                                                             │
│  3.2 PONTOS DE DIVERGENCIA                                                  │
│      Onde cargos discordam                                                  │
│      → Explicitar natureza da divergencia:                                 │
│        - Divergencia de DADOS? (cada um tem info diferente)               │
│        - Divergencia de PRIORIDADES? (objetivos diferentes)               │
│        - Divergencia de TIMING? (curto vs longo prazo)                    │
│        - Divergencia de RISCO? (aversao diferente)                        │
│                                                                             │
│  3.3 TENSOES PRODUTIVAS                                                     │
│      Divergencias que NAO devem ser resolvidas                             │
│      → Sao features, nao bugs                                              │
│      → Exemplo: CFO quer conservar, CRO quer investir                      │
│        - Tensao saudavel que evita extremos                                │
│                                                                             │
│  3.4 LACUNAS IDENTIFICADAS                                                  │
│      Informacoes que NINGUEM tinha                                         │
│      → Precisam ser buscadas antes de decidir                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FORMATO DE OUTPUT DO DEBATE

```
═══════════════════════════════════════════════════════════════════════════════
DEBATE: {Pergunta ou decisao}
DATA: {DATA_ISO}
PARTICIPANTES: {Lista de cargos}
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: POSICOES INDIVIDUAIS                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ POSICAO: CRO ──────────────────────────────────────────────────────────────┐
│                                                                             │
│ RECOMENDACAO:                                                               │
│ {Posicao do CRO}                                                            │
│                                                                             │
│ RACIOCINIO:                                                                 │
│ {Como chegou a essa conclusao}                                              │
│                                                                             │
│ EVIDENCIAS:                                                                 │
│ • HEUR-AH-025: "{citacao}"                                                 │
│ • FW-SO-003: "{citacao}"                                                   │
│                                                                             │
│ CONFIANCA: 80%                                                              │
│                                                                             │
│ LIMITACOES:                                                                 │
│ • {O que nao sei}                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ POSICAO: CFO ──────────────────────────────────────────────────────────────┐
│                                                                             │
│ RECOMENDACAO:                                                               │
│ {Posicao do CFO}                                                            │
│                                                                             │
│ ... (mesmo formato)                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ POSICAO: SALES MANAGER ────────────────────────────────────────────────────┐
│                                                                             │
│ ... (mesmo formato)                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: REBATIDAS CRUZADAS                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ REBATIDA: CRO ─────────────────────────────────────────────────────────────┐
│                                                                             │
│ CONCORDO COM:                                                               │
│ • CFO sobre necessidade de validar unit economics antes de escalar         │
│                                                                             │
│ DISCORDO DE:                                                                │
│ • CFO sobre timeline: 6 meses e muito conservador                          │
│   Evidencia: HEUR-AH-030 "Mercados rapidos requerem decisoes em 30 dias"  │
│                                                                             │
│ PONTO CEGO IDENTIFICADO:                                                    │
│ • SM nao considerou impacto em moral do time com meta agressiva            │
│                                                                             │
│ MANTENHO POSICAO: Sim, com ajuste de timeline para 90 dias                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

... (rebatidas dos outros cargos)

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
│ DIVERGENCIA 1: {Tema}                                                       │
│ ─────────────────────                                                       │
│ Natureza: {dados/prioridades/timing/risco}                                 │
│                                                                             │
│ • CRO defende: {posicao}                                                    │
│ • CFO defende: {posicao}                                                    │
│                                                                             │
│ Impacto se nao resolvido: {consequencia}                                   │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
TENSOES PRODUTIVAS (Nao resolver - sao features)
═══════════════════════════════════════════════════════════════════════════════

• {Tensao 1}: {Por que e produtiva, nao problematica}

═══════════════════════════════════════════════════════════════════════════════
LACUNAS IDENTIFICADAS
═══════════════════════════════════════════════════════════════════════════════

• {Informacao que ninguem tinha e precisa ser buscada}

═══════════════════════════════════════════════════════════════════════════════
```

---

## REGRAS DO DEBATE

```
1. CADA AGENTE DEFENDE SUA LENTE
   CRO olha por revenue, CFO por unit economics, SM por operacao
   Nao tentar "ser neutro" - a parcialidade e proposital

2. EVIDENCIAS OBRIGATORIAS
   Toda afirmacao deve citar DNA (ID)
   Sem evidencia = opiniao, nao posicao fundamentada

3. NAO FORCAR CONSENSO
   Divergencia explicita > consenso artificial
   Tensao e feature, nao bug

4. MANTER TOM DO CARGO
   CRO fala como CRO (agressivo em growth)
   CFO fala como CFO (conservador em risco)
   Nao homogeneizar vozes

5. REBATIDA E SOBRE EVIDENCIAS
   "Discordo porque meu DNA diz X" ✓
   "Discordo porque voce esta errado" ✗

6. PONTOS CEGOS SAO CONTRIBUICAO
   Identificar o que o outro nao viu e ajuda, nao ataque
```

---

## QUANDO ESCALAR PARA CONSELHO

Apos sintese do debate, verificar conforme DEBATE-DYNAMICS-CONFIG.yaml:

```
SE qualquer das condicoes:
  • Convergencia final < 70% (threshold padrao)
  • Confianca da sintese < 70%
  • Divergencia nao resolvida em tema CRITICO
  • Valor em risco > R$100k
  • Decisao irreversivel

ENTAO:
  → Escalar para CONCLAVE-PROTOCOL
  → Debate vira INPUT para o Conselho

SE confianca < 50%:
  → Escalar direto para HUMANO
  → Nao passar pelo Council
```

---

## LIMITES DE OPERACAO

| Parametro | Valor | Fonte |
|-----------|-------|-------|
| Rodadas max | 3 | DEBATE-DYNAMICS-CONFIG |
| Timeout/agente | 30s | DEBATE-DYNAMICS-CONFIG |
| Timeout/rodada | 120s | DEBATE-DYNAMICS-CONFIG |
| Timeout total | 300s | DEBATE-DYNAMICS-CONFIG |
| Convergencia min | 70% | DEBATE-DYNAMICS-CONFIG |
| Max consultas RAG | 5 | DEBATE-DYNAMICS-CONFIG |

> **Nota:** Para detalhes completos de timeouts, circuit breakers e escalacao,
> consulte DEBATE-DYNAMICS-PROTOCOL.md

---

*Fim do DEBATE-PROTOCOL*
