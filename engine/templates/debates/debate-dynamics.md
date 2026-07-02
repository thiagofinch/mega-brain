# DEBATE-DYNAMICS-PROTOCOL
# Dinamica de Debate, Convergencia e Controles de Producao

> **Versao:** 1.0.0
> **Tipo:** Protocolo Central de Orquestracao
> **Dependencias:** DEBATE-PROTOCOL.md, CONCLAVE-PROTOCOL.md, CONSTITUICAO-BASE.md
> **Configuracao:** DEBATE-DYNAMICS-CONFIG.yaml

---

## PROPOSITO

Este protocolo governa a DINAMICA do debate entre agentes:
- Quantas rodadas de debate ocorrem
- Quando considerar que houve convergencia
- Como lidar com loops infinitos
- Quando escalar para humano
- Limites de tempo e recursos

---

## ARQUITETURA DO FLUXO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO COMPLETO COM CHECKPOINTS                          │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   ENTRADA   │
                              │  (Pergunta) │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  CHECKPOINT │
                              │  ROTEAMENTO │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌──────▼──────┐  ┌─────▼─────┐
              │  SIMPLES  │   │   DEBATE    │  │  COUNCIL  │
              │ (1 Cargo) │   │ (2+ Cargos) │  │ (Critico) │
              └─────┬─────┘   └──────┬──────┘  └─────┬─────┘
                    │                │                │
                    │         ┌──────▼──────┐        │
                    │         │   RODADA 1  │        │
                    │         │  (Paralelo) │        │
                    │         └──────┬──────┘        │
                    │                │                │
                    │         ┌──────▼──────┐        │
                    │         │  CHECKPOINT │        │
                    │         │ CONVERGENCIA│        │
                    │         └──────┬──────┘        │
                    │                │                │
                    │      ┌────────┼────────┐       │
                    │      │                 │       │
                    │ ┌────▼────┐      ┌─────▼─────┐ │
                    │ │ >= 70%  │      │  < 70%    │ │
                    │ │CONVERGE │      │ DIVERGE   │ │
                    │ └────┬────┘      └─────┬─────┘ │
                    │      │                 │       │
                    │      │          ┌──────▼──────┐│
                    │      │          │  RODADA 2   ││
                    │      │          │ (Rebatidas) ││
                    │      │          └──────┬──────┘│
                    │      │                 │       │
                    │      │          ┌──────▼──────┐│
                    │      │          │  CHECKPOINT ││
                    │      │          │ CONVERGENCIA││
                    │      │          └──────┬──────┘│
                    │      │                 │       │
                    │      │       ┌─────────┼───────┐
                    │      │       │                 │
                    │      │  ┌────▼────┐     ┌─────▼─────┐
                    │      │  │ >= 70%  │     │  < 70%    │
                    │      │  │CONVERGE │     │ DIVERGE   │
                    │      │  └────┬────┘     └─────┬─────┘
                    │      │       │                 │
                    │      │       │          ┌──────▼──────┐
                    │      │       │          │  RODADA 3   │
                    │      │       │          │  (Final)    │
                    │      │       │          └──────┬──────┘
                    │      │       │                 │
                    │      │       │          ┌──────▼──────┐
                    │      │       │          │ CIRCUIT     │
                    │      │       │          │ BREAKER     │
                    │      │       │          └──────┬──────┘
                    │      │       │                 │
                    └──────┴───────┴─────────────────┘
                                     │
                              ┌──────▼──────┐
                              │   SINTESE   │
                              └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌──────▼──────┐  ┌─────▼─────┐
              │ CONFIANCA │   │  CONFIANCA  │  │ CONFIANCA │
              │  >= 70%   │   │  50-69%     │  │   < 50%   │
              └─────┬─────┘   └──────┬──────┘  └─────┬─────┘
                    │                │                │
              ┌─────▼─────┐   ┌──────▼──────┐  ┌─────▼─────┐
              │  EMITIR   │   │   COUNCIL   │  │  ESCALAR  │
              │  DECISAO  │   │ (3 Membros) │  │  HUMANO   │
              └───────────┘   └──────┬──────┘  └───────────┘
                                     │
                              ┌──────▼──────┐
                              │   DECISAO   │
                              │    FINAL    │
                              └─────────────┘
```

---

## PARAMETROS GLOBAIS

> **Configuracao completa:** `core/templates/debates/DEBATE-DYNAMICS-CONFIG.yaml`

### Resumo dos Parametros

| Parametro | Valor | Descricao |
|-----------|-------|-----------|
| `debate.rounds.min` | 1 | Minimo de rodadas |
| `debate.rounds.typical` | 2 | Rodadas tipicas |
| `debate.rounds.max` | 3 | Maximo antes de circuit breaker |
| `convergence.threshold` | 70% | % de concordancia para convergir |
| `timeout.per_agent` | 30s | Tempo max por agente |
| `timeout.per_round` | 120s | Tempo max por rodada |
| `timeout.total` | 300s | Tempo max total do debate |
| `circuit_breaker.max_iterations` | 5 | Max iteracoes totais |
| `circuit_breaker.max_refinements` | 2 | Max loops de refinamento |
| `rag.internal_queries` | PERMITIDO | Consultas ao RAG interno |
| `rag.max_queries` | 5 | Max consultas por debate |
| `rag.timeout` | 15s | Timeout por consulta RAG |
| `external_search` | PROIBIDO | Busca externa na web |

---

## DINAMICA DE RODADAS

### Rodada 1: Posicoes Iniciais (Paralelo)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ RODADA 1: POSICOES INICIAIS                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ EXECUCAO: Paralela (todos agentes respondem simultaneamente)                    │
│ TIMEOUT: 30s por agente                                                         │
│                                                                                 │
│ CADA AGENTE GERA:                                                               │
│ • Posicao clara (2-3 frases)                                                    │
│ • Raciocinio (quais camadas DNA usou)                                           │
│ • Evidencias (IDs citados)                                                      │
│ • Confianca (0-100%)                                                            │
│ • Limitacoes (o que nao sabe)                                                   │
│                                                                                 │
│ OUTPUT: Array de posicoes para calculo de convergencia                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Checkpoint de Convergencia

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ CHECKPOINT: CALCULO DE CONVERGENCIA                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ FORMULA:                                                                        │
│                                                                                 │
│   convergencia = (pontos_concordancia / pontos_totais) * 100                    │
│                                                                                 │
│ PONTOS DE CONCORDANCIA:                                                         │
│ • Mesma recomendacao final                                                      │
│ • Mesmas premissas base                                                         │
│ • Mesmos riscos identificados                                                   │
│ • Mesmo timing proposto                                                         │
│                                                                                 │
│ DECISAO:                                                                        │
│ ┌───────────────────────────────────────────────────────────────────────────┐  │
│ │ SE convergencia >= 70%  → CONVERGIU (pular para Sintese)                 │  │
│ │ SE convergencia < 70%   → DIVERGIU (iniciar proxima rodada)              │  │
│ │ SE rodada == max_rounds → CIRCUIT BREAKER (forcar sintese)               │  │
│ └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Rodada 2: Rebatidas Cruzadas

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ RODADA 2: REBATIDAS CRUZADAS                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ TRIGGER: Convergencia < 70% na Rodada 1                                         │
│ EXECUCAO: Sequencial (agentes veem posicoes dos outros)                         │
│ TIMEOUT: 30s por agente                                                         │
│                                                                                 │
│ CADA AGENTE:                                                                    │
│ 1. VE as posicoes de todos os outros                                            │
│ 2. Identifica CONCORDANCIAS (reforcar com DNA adicional)                        │
│ 3. Identifica DIVERGENCIAS (confronto de evidencias)                            │
│ 4. Identifica PONTOS CEGOS nos outros                                           │
│ 5. Declara se MANTEM posicao (Sim/Nao/Parcialmente)                             │
│                                                                                 │
│ OBJETIVO: Aproximar posicoes atraves de confronto de evidencias                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Rodada 3: Refinamento Final

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ RODADA 3: REFINAMENTO FINAL                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ TRIGGER: Convergencia < 70% na Rodada 2                                         │
│ EXECUCAO: Foco em divergencias especificas                                      │
│ TIMEOUT: 30s por agente                                                         │
│                                                                                 │
│ ESCOPO REDUZIDO:                                                                │
│ • NAO re-debater pontos de consenso                                             │
│ • FOCAR apenas nas divergencias identificadas                                   │
│ • Tentar uma ultima aproximacao                                                 │
│                                                                                 │
│ SE ainda < 70% apos Rodada 3:                                                   │
│ → Circuit Breaker ativado                                                       │
│ → Forcar sintese com divergencias explicitas                                    │
│ → Escalar para Council ou Humano                                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## CIRCUIT BREAKER

### Triggers de Ativacao

```yaml
circuit_breaker:
  triggers:
    - condition: "rodadas >= max_rounds (3)"
      action: "Forcar sintese com divergencias"

    - condition: "iteracoes >= max_iterations (5)"
      action: "Parar imediatamente e escalar"

    - condition: "refinamentos >= max_refinements (2)"
      action: "Declarar impasse e escalar"

    - condition: "timeout_total >= 300s"
      action: "Abortar e escalar com estado atual"

    - condition: "loop detectado (mesmas posicoes 2x)"
      action: "Parar e escalar"
```

### Formato de Saida do Circuit Breaker

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ CIRCUIT BREAKER ATIVADO                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ MOTIVO: {trigger_condition}                                                     │
│ RODADAS EXECUTADAS: {n} de {max}                                                │
│ CONVERGENCIA FINAL: {X}%                                                        │
│                                                                                 │
│ ESTADO DO DEBATE:                                                               │
│ • Consensos alcancados: {lista}                                                 │
│ • Divergencias nao resolvidas: {lista}                                          │
│ • Agentes em conflito: {lista}                                                  │
│                                                                                 │
│ ACAO: Escalando para {COUNCIL | HUMANO}                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## CONSULTAS RAG

### Regras de Consulta

```yaml
rag_policy:
  internal:
    status: PERMITIDO
    max_queries: 5
    timeout_per_query: 15s
    scope: "knowledge/, processing/insights/"

  external:
    status: PROIBIDO
    reason: "Controle de qualidade e rastreabilidade"

  durante_debate:
    - Agentes podem consultar RAG para buscar evidencias
    - Cada consulta conta contra o limite (5 total)
    - Timeout de 15s por consulta
    - Resultados citados com chunk_id

  formato_citacao:
    padrao: "[RAG:{chunk_id}]"
    exemplo: "[RAG:CG001_042]"
```

### Quando Consultar RAG

```
PERMITIDO:
✅ Buscar evidencia para fundamentar posicao
✅ Verificar se tema ja foi abordado na knowledge base
✅ Encontrar citacao exata de fonte processada
✅ Resolver divergencia com dados do sistema

PROIBIDO:
❌ Buscar informacao na web externa
❌ Consultar APIs externas
❌ Fazer mais de 5 consultas por debate
❌ Consultas que excedam 15s
```

---

## ESCALACAO PARA COUNCIL

### Triggers de Escalacao

```yaml
escalation_triggers:
  para_council:
    - convergencia_final < 70%
    - confianca_sintese < 70%
    - divergencia_critica: true
    - valor_em_risco > "R$100k"
    - decisao_irreversivel: true

  para_humano:
    - confianca < 50%
    - circuit_breaker: "max_iterations"
    - tipo_incerteza: "fora_do_escopo"
    - risco: "CATASTROFICO"
```

### Fluxo de Escalacao

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE ESCALACAO                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

DEBATE CONCLUIDO
      │
      ▼
┌─────────────────┐
│  Confianca      │
│  da Sintese?    │
└────────┬────────┘
         │
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
 >= 70%                    < 70%
    │                         │
    ▼                         ▼
┌─────────┐           ┌─────────────┐
│ EMITIR  │           │  Valor em   │
│ DECISAO │           │  Risco?     │
└─────────┘           └──────┬──────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                   ▼                   ▼
              > R$100k            <= R$100k
                   │                   │
                   ▼                   ▼
           ┌─────────────┐     ┌─────────────┐
           │   COUNCIL   │     │  Confianca  │
           │ OBRIGATORIO │     │    >= 50%?  │
           └──────┬──────┘     └──────┬──────┘
                  │                   │
                  │            ┌──────┴──────┐
                  │            │             │
                  │            ▼             ▼
                  │         >= 50%        < 50%
                  │            │             │
                  │            ▼             ▼
                  │     ┌─────────┐   ┌─────────┐
                  │     │ COUNCIL │   │ ESCALAR │
                  │     │ OPCIONAL│   │ HUMANO  │
                  │     └────┬────┘   └─────────┘
                  │          │
                  └──────────┘
                        │
                        ▼
               ┌─────────────┐
               │   COUNCIL   │
               │  EXECUTA    │
               └──────┬──────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
    >= 60%                      < 60%
         │                         │
         ▼                         ▼
   ┌─────────┐               ┌─────────┐
   │ EMITIR  │               │ ESCALAR │
   │ DECISAO │               │ HUMANO  │
   └─────────┘               └─────────┘
```

---

## TIMEOUTS

### Tabela de Timeouts

| Escopo | Timeout | Acao ao Exceder |
|--------|---------|-----------------|
| Agente individual | 30s | Usar posicao parcial, marcar timeout |
| Rodada completa | 120s | Encerrar rodada, calcular convergencia |
| Debate total | 300s | Circuit breaker, forcar sintese |
| Consulta RAG | 15s | Abortar consulta, continuar sem |
| Council completo | 180s | Forcar sintese do Sintetizador |

### Comportamento em Timeout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ TIMEOUT: AGENTE INDIVIDUAL (30s)                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ SE agente nao responder em 30s:                                                 │
│ 1. Marcar agente como "TIMEOUT"                                                 │
│ 2. Usar resposta parcial se disponivel                                          │
│ 3. SE nenhuma resposta: excluir do calculo de convergencia                      │
│ 4. Registrar no log: "TIMEOUT: {CARGO} em {FASE}"                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ TIMEOUT: DEBATE TOTAL (300s)                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│ SE debate exceder 300s:                                                         │
│ 1. PARAR imediatamente todas as operacoes                                       │
│ 2. Gerar sintese com estado atual                                               │
│ 3. Marcar confianca como "REDUZIDA POR TIMEOUT"                                 │
│ 4. Escalar para humano se confianca < 50%                                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## LOOP PREVENTION

### Deteccao de Loop

```yaml
loop_detection:
  method: "hash de posicoes"

  algoritmo:
    1. Apos cada rodada, gerar hash das posicoes
    2. Comparar com hash da rodada anterior
    3. SE hash == hash_anterior:
         - Incrementar loop_counter
    4. SE loop_counter >= 2:
         - LOOP DETECTADO
         - Ativar circuit breaker

  sinais_de_loop:
    - Mesmas posicoes em rodadas consecutivas
    - Mesmos argumentos repetidos
    - Nenhuma mudanca de confianca
    - Rebatidas identicas
```

### Acao em Loop Detectado

```
LOOP DETECTADO → PARAR IMEDIATAMENTE

1. Nao executar mais rodadas
2. Gerar sintese com estado atual
3. Declarar: "IMPASSE - Posicoes estabilizaram sem convergencia"
4. Escalar para Council com flag IMPASSE=true
5. Council decide se escala para humano
```

---

## FORMATO DE LOG

### Log de Execucao do Debate

```yaml
debate_log:
  session_id: "{UUID}"
  timestamp_inicio: "{ISO}"
  timestamp_fim: "{ISO}"

  query: "{pergunta original}"
  participantes: ["{CARGO1}", "{CARGO2}", "..."]

  rodadas:
    - numero: 1
      tipo: "posicoes_iniciais"
      duracao_ms: {N}
      convergencia: {X}%
      agentes_responderam: [...]
      agentes_timeout: [...]

    - numero: 2
      tipo: "rebatidas"
      duracao_ms: {N}
      convergencia: {X}%
      mudancas_posicao: {N}

  rag_queries:
    total: {N}
    sucesso: {N}
    timeout: {N}
    chunks_citados: [...]

  resultado:
    convergencia_final: {X}%
    confianca_sintese: {X}%
    escalado_para: "{COUNCIL | HUMANO | NENHUM}"
    circuit_breaker: {true | false}

  metricas:
    tempo_total_ms: {N}
    tokens_consumidos: {N}
    rodadas_executadas: {N}
```

---

## INTEGRACAO COM OUTROS PROTOCOLOS

### Dependencias

```
DEBATE-DYNAMICS-PROTOCOL
         │
         ├──► DEBATE-PROTOCOL.md (estrutura das rodadas)
         │
         ├──► CONCLAVE-PROTOCOL.md (escalacao para meta-avaliacao)
         │
         ├──► CONSTITUICAO-BASE.md (principios fundamentais)
         │
         ├──► EPISTEMIC-PROTOCOL.md (anti-alucinacao)
         │
         └──► REASONING-MODEL-PROTOCOL.md (modelo de raciocinio)
```

### Ordem de Aplicacao

```
1. CONSTITUICAO-BASE.md      → Define principios inviolaveis
2. DEBATE-DYNAMICS-PROTOCOL  → Define dinamica e limites
3. DEBATE-PROTOCOL.md        → Define estrutura das rodadas
4. CONCLAVE-PROTOCOL.md      → Define meta-avaliacao
5. EPISTEMIC-PROTOCOL.md     → Aplica em todas as respostas
```

---

## CHECKLIST DE VALIDACAO

Antes de executar debate, verificar:

```
[ ] Pergunta esta clara e especifica?
[ ] Agentes corretos foram selecionados?
[ ] Timeouts estao configurados?
[ ] RAG esta disponivel (se necessario)?
[ ] Circuit breaker esta ativo?
[ ] Log de execucao esta iniciado?
```

Durante debate, monitorar:

```
[ ] Nenhum agente em timeout prolongado?
[ ] Convergencia esta progredindo?
[ ] Loop nao detectado?
[ ] Tempo total < 300s?
[ ] Consultas RAG < 5?
```

Apos debate, validar:

```
[ ] Sintese foi gerada?
[ ] Confianca foi calculada?
[ ] Escalacao (se necessaria) foi feita?
[ ] Log foi finalizado?
[ ] Decisao final esta clara e acionavel?
```

---

*Fim do DEBATE-DYNAMICS-PROTOCOL*
