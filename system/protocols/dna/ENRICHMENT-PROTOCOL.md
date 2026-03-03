# ENRICHMENT-PROTOCOL
# Agregacao de DNA e Mapeamento de Conflitos

> **Versao:** 1.0.0
> **Trigger:** Executar apos 2+ pessoas terem DNA extraido
> **Input:** knowledge/dna/persons/*/
> **Output:** knowledge/dna/AGGREGATED/ + knowledge/dna/MAPS/

---

## PROPOSITO

Este protocolo define como:
1. AGREGAR DNA de multiplas pessoas por DOMINIO
2. Identificar CONVERGENCIAS (onde concordam)
3. Identificar DIVERGENCIAS (onde discordam)
4. Criar REGRAS DE RESOLUCAO para conflitos

---

## PARTE A: AGREGACAO POR DOMINIO

### A.1 Processo de Agregacao (por camada)

Para cada camada (FILOSOFIAS, HEURISTICAS, etc.), executar:

```
PASSO 1: Coletar todos os itens de todas as pessoas
         Filtrar: peso >= 0.70 (apenas itens confiaveis)

PASSO 2: Agrupar por DOMINIO
         Usar DOMAINS-TAXONOMY.yaml para normalizacao

PASSO 3: Identificar CONVERGENCIAS
         Conceitos similares em 2+ pessoas

PASSO 4: Identificar DIVERGENCIAS
         Posicoes conflitantes entre pessoas

PASSO 5: Identificar COMPLEMENTARIDADES
         Contribuicoes unicas de uma pessoa

PASSO 6: Gerar AGG-{DOMINIO}.yaml
```

### A.2 Criterios de Classificacao

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  CONSENSO FORTE (peso_agregado: 0.90-1.00)                                  │
│  ─────────────────────────────────────────                                  │
│  • 3+ pessoas concordam                                                     │
│  • Thresholds numericos similares (variacao < 20%)                         │
│  • Mesma direcao de acao recomendada                                       │
│                                                                             │
│  CONSENSO PARCIAL (peso_agregado: 0.70-0.89)                                │
│  ───────────────────────────────────────────                                │
│  • 2 pessoas concordam                                                      │
│  • OU 3+ com variacoes significativas                                      │
│                                                                             │
│  COMPLEMENTARIDADE (peso_agregado: 0.60-0.75)                               │
│  ─────────────────────────────────────────────                              │
│  • Contribuicao unica de 1 pessoa                                          │
│  • Nao contradiz os outros, apenas adiciona                                │
│                                                                             │
│  CONFLITO (vai para MAP-CONFLITOS.yaml)                                     │
│  ───────────────────────────────────────                                    │
│  • 2+ pessoas com posicoes OPOSTAS                                         │
│  • Thresholds numericos divergentes (variacao > 50%)                       │
│  • Acoes recomendadas contraditorias                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A.3 Formato AGG-{DOMINIO}.yaml

```yaml
# knowledge/dna/AGGREGATED/AGG-VENDAS.yaml

dominio: "vendas"
versao: "1.0.0"
data_agregacao: "{DATA_ISO}"
pessoas_incluidas:
  - "alex-hormozi"
  - "cole-gordon"
  - "SAM-OVEN"
  - "JORDAN-LEE"

# ════════════════════════════════════════════════════════════════════════════
# HEURISTICAS AGREGADAS (a camada mais importante para decisoes)
# ════════════════════════════════════════════════════════════════════════════

heuristicas:

  consensos_fortes:
    - id: "AGG-HEUR-VENDAS-001"
      regra: "{Regra onde 3+ concordam}"
      threshold:
        valor: {numero consensual}
        operador: "{operador}"
        unidade: "{unidade}"
        variacao_entre_fontes: "{X-Y%}"  # Range das fontes

      fontes:
        - pessoa: "alex-hormozi"
          id_original: "HEUR-AH-015"
          threshold_original: {valor}
          citacao: "{citacao}"
        - pessoa: "cole-gordon"
          id_original: "HEUR-CG-008"
          threshold_original: {valor}
          citacao: "{citacao}"
        - pessoa: "SAM-OVEN"
          id_original: "HEUR-SO-003"
          threshold_original: {valor}
          citacao: "{citacao}"

      sintese: "{Versao unificada da regra}"
      peso_agregado: 0.95

  consensos_parciais:
    - id: "AGG-HEUR-VENDAS-010"
      regra: "{Regra onde 2 concordam}"
      fontes:
        - pessoa: "alex-hormozi"
          id_original: "HEUR-AH-020"
        - pessoa: "cole-gordon"
          id_original: "HEUR-CG-012"

      sintese: "{Versao unificada}"
      ressalva: "{Por que so 2 concordam, o que os outros pensam}"
      peso_agregado: 0.78

  complementaridades:
    - id: "AGG-HEUR-VENDAS-020"
      regra: "{Regra unica de uma pessoa}"
      fonte_unica: "JORDAN-LEE"
      id_original: "HEUR-JL-005"

      valor_adicionado: "{Por que e valioso mesmo sendo de 1 fonte}"
      peso_agregado: 0.65

# ════════════════════════════════════════════════════════════════════════════
# FILOSOFIAS AGREGADAS
# ════════════════════════════════════════════════════════════════════════════

filosofias:

  consensos_fortes:
    - id: "AGG-FIL-VENDAS-001"
      conceito: "{Filosofia compartilhada}"
      fontes:
        - pessoa: "alex-hormozi"
          id_original: "FIL-AH-001"
          declaracao: "{como ele expressa}"
        - pessoa: "cole-gordon"
          id_original: "FIL-CG-003"
          declaracao: "{como ele expressa}"

      sintese: "{Versao unificada}"
      peso_agregado: 0.92

# ════════════════════════════════════════════════════════════════════════════
# MODELOS MENTAIS AGREGADOS
# ════════════════════════════════════════════════════════════════════════════

modelos_mentais:
  # Mesmo formato de consensos/complementaridades

# ════════════════════════════════════════════════════════════════════════════
# FRAMEWORKS AGREGADOS
# ════════════════════════════════════════════════════════════════════════════

frameworks:
  # Mesmo formato

# ════════════════════════════════════════════════════════════════════════════
# METODOLOGIAS AGREGADAS
# ════════════════════════════════════════════════════════════════════════════

metodologias:
  # Mesmo formato
```

---

## PARTE B: MAPEAMENTO DE CONFLITOS

### B.1 Quando Mapear Conflito

```
CONFLITO existe quando:

1. THRESHOLDS DIVERGENTES
   Hormozi: "CAC < 8% do LTV"
   Cole: "CAC pode ser ate 15% se closer e bom"
   → Divergencia > 50%

2. ACOES CONTRADITORIAS
   Hormozi: "Demitir imediatamente se performance < X"
   Jordan: "Dar coaching intensivo antes de demitir"
   → Acoes opostas para mesmo trigger

3. FILOSOFIAS INCOMPATIVEIS
   Sam: "Constraints first - resolver gargalo antes de escalar"
   Jeremy: "Scale fast - resolver problemas enquanto cresce"
   → Abordagens fundamentalmente diferentes
```

### B.2 Formato MAP-CONFLITOS.yaml

```yaml
# knowledge/dna/MAPS/MAP-CONFLITOS.yaml

versao: "1.0.0"
data_mapeamento: "{DATA_ISO}"
total_conflitos: {N}

conflitos:

  - id: "CONF-001"
    tema: "{Sobre o que discordam}"
    dominios:
      - "compensation"
      - "management"

    natureza: "{threshold, acao, filosofia}"
    severidade: "{alta, media, baixa}"  # Quao impactante e a divergencia

    posicoes:
      hormozi:
        stance: "{Posicao dele}"
        intensidade: "forte"  # forte, moderada, leve
        evidencias:
          - id: "HEUR-AH-025"
            citacao: "{texto}"
        logica: "{Por que ele pensa assim}"

      cole_gordon:
        stance: "{Posicao dele}"
        intensidade: "moderada"
        evidencias:
          - id: "HEUR-CG-018"
            citacao: "{texto}"
        logica: "{Por que ele pensa assim}"

    analise: |
      {Por que eles discordam? Contextos diferentes? Valores diferentes?
       Experiencias diferentes? Publico-alvo diferente?}

    resolucao:
      tipo: "contextual"  # contextual, hierarquica, complementar, irresolvivel

      # Para CONTEXTUAL:
      regra: |
        IF contexto == "startup early-stage" THEN
          → Aplicar posicao de {PESSOA}
        ELSE IF contexto == "empresa estabelecida" THEN
          → Aplicar posicao de {PESSOA}
        ELSE
          → Apresentar ambas posicoes ao usuario

      # Para HIERARQUICA:
      # prioridade: "{PESSOA}" # Quem prevalece por padrao
      # justificativa: "{Por que essa pessoa prevalece}"

      # Para COMPLEMENTAR:
      # sintese: "{Como combinar as duas posicoes}"

      # Para IRRESOLVIVEL:
      # acao: "apresentar_ambas"
      # nota: "Decisao requer input humano"

  - id: "CONF-002"
    # ... proximo conflito
```

### B.3 Regras de Resolucao

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  TIPOS DE RESOLUCAO                                                         │
│                                                                             │
│  1. CONTEXTUAL (mais comum)                                                 │
│     "Depende do contexto"                                                   │
│     Criar regras IF/THEN baseadas em:                                      │
│     - Estagio da empresa (startup, scale-up, enterprise)                   │
│     - Tamanho do time                                                       │
│     - Ticket medio                                                          │
│     - Mercado (B2B, B2C, high-ticket, low-ticket)                          │
│                                                                             │
│  2. HIERARQUICA                                                             │
│     "Pessoa X prevalece neste tema"                                        │
│     Quando:                                                                 │
│     - Uma pessoa tem expertise claramente superior no tema                 │
│     - Uma pessoa tem mais evidencias                                       │
│     Exemplo: Cole Gordon prevalece em temas de closing                     │
│                                                                             │
│  3. COMPLEMENTAR                                                            │
│     "Ambos estao certos, em aspectos diferentes"                           │
│     Quando:                                                                 │
│     - Posicoes parecem conflitar mas na verdade cobrem aspectos diferentes │
│     Exemplo: Um fala de conversao, outro fala de volume                    │
│                                                                             │
│  4. IRRESOLVIVEL                                                            │
│     "Requer decisao humana"                                                │
│     Quando:                                                                 │
│     - Conflito e genuino e nao ha criterio objetivo                       │
│     - Depende de valores/preferencias do decisor                          │
│     Acao: Apresentar ambas posicoes claramente                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PARTE C: ENRIQUECIMENTO DE AGENTES DE CARGO

### C.1 Criar DNA-CONFIG.yaml para cada cargo

Apos ter AGG-*.yaml e MAP-CONFLITOS.yaml, criar configs:

```yaml
# agents/cargo/C-LEVEL/CRO/DNA-CONFIG.yaml

cargo: "CRO"
versao: "1.0.0"
data_configuracao: "{DATA_ISO}"

# CONSTITUICAO (Camada 1)
constituicao:
  path: "/agents/CONSTITUTION/BASE-CONSTITUTION.md"

# MEMORIA DO NEGOCIO (dados reais da empresa)
memoria:
  path: "./MEMORY.md"

# FONTES DE DNA
dna_sources:

  # DNA de pessoas especificas, filtrado por dominio
  primario:
    - pessoa: "alex-hormozi"
      path: "/knowledge/dna/persons/alex-hormozi"
      dominios_usados:
        - "vendas"
        - "scaling"
        - "offers"
      peso: 0.85

    - pessoa: "SAM-OVEN"
      path: "/knowledge/dna/persons/SAM-OVEN"
      dominios_usados:
        - "scaling"
        - "unit-economics"
      peso: 0.75

    - pessoa: "cole-gordon"
      path: "/knowledge/dna/persons/cole-gordon"
      dominios_usados:
        - "vendas"
        - "compensation"
      peso: 0.80

  # DNA agregado por dominio
  agregado:
    - dominio: "vendas"
      path: "/knowledge/dna/AGGREGATED/AGG-VENDAS.yaml"
      peso: 0.90  # Agregado tem peso alto

    - dominio: "scaling"
      path: "/knowledge/dna/AGGREGATED/AGG-SCALING.yaml"
      peso: 0.85

# MAPA DE CONFLITOS
conflitos:
  path: "/knowledge/dna/MAPS/MAP-CONFLITOS.yaml"

# REGRAS DE RESOLUCAO ESPECIFICAS DO CARGO
resolucao_de_conflitos:

  regra_geral: |
    1. Se ha CONSENSO FORTE no agregado → usar sem ressalva
    2. Se ha CONSENSO PARCIAL → usar com nota de contexto
    3. Se ha CONFLITO → consultar MAP-CONFLITOS
       3.1 Se resolucao e CONTEXTUAL → aplicar regra
       3.2 Se resolucao e HIERARQUICA → usar pessoa prioritaria
       3.3 Se IRRESOLVIVEL → apresentar ambas posicoes

  regras_especificas:
    - tema: "compensation de closers"
      pessoa_prioritaria: "cole-gordon"
      justificativa: "Especialidade principal dele"

    - tema: "unit economics de aquisicao"
      pessoa_prioritaria: "alex-hormozi"
      justificativa: "Experiencia com scale"

# PROTOCOLO DE RACIOCINIO
raciocinio:
  path: "/system/protocols/dna/REASONING-MODEL-PROTOCOL.md"
```

---

*Fim do ENRICHMENT-PROTOCOL*
