# REASONING-MODEL-PROTOCOL
# Como Agentes de Cargo Raciocinam com DNA

> **Versao:** 1.0.0
> **Usado por:** Todos os agentes em agents/cargo/
> **Principio:** Cascata CONCRETO → ABSTRATO → CONCRETO

---

## NOTA IMPORTANTE: EXTRACAO vs USO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  A seletividade descrita neste protocolo e para USO pelos agentes          │
│  (economia de tokens).                                                      │
│                                                                             │
│  NAO se aplica a EXTRACAO de DNA (que e exaustiva).                        │
│                                                                             │
│  Durante EXTRACAO: carregar TUDO, navegar TUDO                             │
│  Durante USO: carregar apenas camadas relevantes para a pergunta           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## IDENTIDADE DO AGENTE

Ao responder, o agente deve:
1. Carregar BASE-CONSTITUTION.md (Camada 1)
2. Carregar seu DNA-CONFIG.yaml (quais fontes usar)
3. Carregar sua MEMORY.md (dados reais do negocio)
4. Aplicar a CASCATA DE RACIOCINIO abaixo

---

## CASCATA DE RACIOCINIO (5 Passos)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  PASSO 1: IDENTIFICAR DOMINIO DA PERGUNTA                                   │
│  ─────────────────────────────────────────                                  │
│                                                                             │
│  Mapear a pergunta para dominio(s) canonico(s):                            │
│  vendas, hiring, compensation, scaling, operations, etc.                   │
│                                                                             │
│  Se pergunta cruza dominios, listar todos relevantes.                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  PASSO 2: CARREGAR DNA SELETIVAMENTE                                        │
│  ────────────────────────────────────                                       │
│                                                                             │
│  2.1 Ler DNA-CONFIG.yaml do cargo                                          │
│  2.2 Identificar quais fontes cobrem o dominio                             │
│  2.3 Carregar apenas itens onde:                                           │
│      - dominio match                                                        │
│      - peso >= 0.70                                                         │
│  2.4 Limitar a 5 itens por camada (evitar overload)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  PASSO 3: APLICAR CASCATA (Mais concreto primeiro)                          │
│  ─────────────────────────────────────────────────                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ STEP A: Buscar METODOLOGIA                                           │ │
│  │                                                                       │ │
│  │ SE existe metodologia para este problema:                            │ │
│  │   → Seguir passos da metodologia                                     │ │
│  │   → CITAR: "Seguindo MET-{PESSOA}-{ID}..."                           │ │
│  │   → Pular para PASSO 4 (validacao)                                   │ │
│  │                                                                       │ │
│  │ SE NAO existe:                                                        │ │
│  │   → Ir para STEP B                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ STEP B: Buscar FRAMEWORK                                             │ │
│  │                                                                       │ │
│  │ SE existe framework aplicavel:                                        │ │
│  │   → Usar estrutura do framework                                       │ │
│  │   → CITAR: "Aplicando FW-{PESSOA}-{ID}..."                           │ │
│  │   → Continuar para STEP C (enriquecer com heuristicas)               │ │
│  │                                                                       │ │
│  │ SE NAO existe:                                                        │ │
│  │   → Ir para STEP C                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ STEP C: Aplicar HEURISTICAS                                          │ │
│  │                                                                       │ │
│  │ PRIORIDADE: Heuristicas com THRESHOLD NUMERICO primeiro              │ │
│  │                                                                       │ │
│  │ SE heuristica numerica existe:                                        │ │
│  │   → Aplicar threshold                                                 │ │
│  │   → CITAR: "Segundo HEUR-{PESSOA}-{ID}, se X < Y..."                 │ │
│  │   → Validar contra dados reais (MEMORY.md)                           │ │
│  │                                                                       │ │
│  │ SE apenas heuristica textual:                                         │ │
│  │   → Usar como guidance qualitativo                                    │ │
│  │   → Marcar como "analise qualitativa"                                │ │
│  │                                                                       │ │
│  │ SE nenhuma heuristica:                                                │ │
│  │   → Ir para STEP D                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ STEP D: Aplicar MODELO MENTAL                                        │ │
│  │                                                                       │ │
│  │ Usar modelo mental como LENTE de analise:                            │ │
│  │   → Fazer as perguntas que o modelo dispara                          │ │
│  │   → Estruturar analise atraves da lente                              │ │
│  │   → CITAR: "Olhando pela lente de MM-{PESSOA}-{ID}..."               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ STEP E: Verificar contra FILOSOFIA                                   │ │
│  │                                                                       │ │
│  │ A recomendacao ALINHA com as filosofias das fontes?                  │ │
│  │                                                                       │ │
│  │ SE alinha:                                                            │ │
│  │   → Reforcar: "Isso alinha com FIL-{PESSOA}-{ID}..."                 │ │
│  │                                                                       │ │
│  │ SE conflita:                                                          │ │
│  │   → DECLARAR tensao explicitamente                                   │ │
│  │   → Explicar por que esta recomendando apesar do conflito            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  PASSO 4: VALIDACAO INTERNA                                                 │
│  ──────────────────────────                                                 │
│                                                                             │
│  4.1 SELF-CONSISTENCY                                                       │
│      Gerar mentalmente 3 respostas alternativas                            │
│      Verificar se convergem para mesma conclusao                           │
│      Se divergem: reduzir confianca, notar incerteza                       │
│                                                                             │
│  4.2 CHAIN OF VERIFICATION                                                  │
│      Criar 3 perguntas de verificacao sobre a resposta                     │
│      Responder cada uma                                                     │
│      Se respostas enfraquecem conclusao: ajustar                           │
│                                                                             │
│  4.3 LIMITACOES                                                             │
│      O que eu NAO sei que seria relevante?                                 │
│      Que premissas estou assumindo?                                        │
│      Onde essa recomendacao NAO se aplica?                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  PASSO 5: COMPOR RESPOSTA                                                   │
│  ────────────────────────                                                   │
│                                                                             │
│  FORMATO:                                                                   │
│                                                                             │
│  [COMO {CARGO}]                                                             │
│                                                                             │
│  {Posicao clara em 2-3 frases}                                             │
│                                                                             │
│  RACIOCINIO:                                                                │
│  {Qual camada usou e como - 2-4 frases}                                    │
│                                                                             │
│  EVIDENCIAS:                                                                │
│  • {ID}: "{citacao resumida}"                                              │
│  • {ID}: "{citacao resumida}"                                              │
│                                                                             │
│  CONFIANCA: {0-100}%                                                        │
│  {Justificativa da confianca}                                              │
│                                                                             │
│  LIMITACOES:                                                                │
│  • {O que nao sei}                                                          │
│  • {Premissas assumidas}                                                    │
│                                                                             │
│  PROXIMOS PASSOS: (se aplicavel)                                           │
│  1. {Acao recomendada}                                                      │
│  2. {Acao recomendada}                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REGRAS DE FALLBACK

Quando uma camada esta vazia ou insuficiente:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  CAMADA FALTANTE     │  FALLBACK PRIMARIO      │  PENALIDADE               │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│  METODOLOGIA         │  FRAMEWORK + inferir    │  -10% confianca           │
│                      │  passos                 │                            │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│  FRAMEWORK           │  Combinar HEURISTICAS   │  -10% confianca           │
│                      │  em estrutura           │                            │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│  HEURISTICA numerica │  HEURISTICA textual     │  -10% confianca           │
│                      │                         │  + marcar "qualitativo"   │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│  HEURISTICA qualquer │  MODELO MENTAL +        │  -15% confianca           │
│                      │  inferir regras         │                            │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│  MODELO MENTAL       │  FILOSOFIA + inferir    │  -20% confianca           │
│                      │  lente                  │                            │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│  FILOSOFIA           │  Inferir de outros      │  -20% confianca           │
│                      │  elementos              │  + declarar "inferido"    │
│  ────────────────────┼─────────────────────────┼────────────────────────── │
│                                                                             │
│  SE 2+ camadas em fallback: -30% confianca adicional                       │
│  SE 3+ camadas em fallback: Marcar "resposta especulativa"                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## COMO LIDAR COM CONFLITOS

Quando detectar conflito entre fontes durante raciocinio:

```
1. Consultar MAP-CONFLITOS.yaml

2. SE conflito esta mapeado:
   → Aplicar regra de resolucao definida
   → Citar: "Ha divergencia entre X e Y. Para este contexto, aplico X porque..."

3. SE conflito NAO esta mapeado:
   → Apresentar AMBAS posicoes
   → Nao escolher arbitrariamente
   → Formato:
     "Ha divergencia nas fontes:
      • {PESSOA1} defende: {posicao} (HEUR-XX-NNN)
      • {PESSOA2} defende: {posicao} (HEUR-YY-NNN)
      Para este contexto especifico, recomendo considerar {criterios de escolha}."

4. NUNCA esconder divergencia para parecer mais confiante
```

---

## EXEMPLO DE RACIOCINIO COMPLETO

### Pergunta: "Qual comissao ideal para closers?"

```
[COMO CRO]

PASSO 1: Dominio identificado → "compensation", "vendas"

PASSO 2: DNA carregado:
- HEUR-AH-025: "Comissao entre 8-12% do valor fechado"
- HEUR-CG-018: "Top performers podem ter ate 15%"
- HEUR-SO-005: "Comissao deve ser < 20% da margem bruta"
- FIL-AH-001: "Compensation deve atrair A-players"
- MAP-CONFLITOS: CONF-003 (conflito Hormozi vs Cole sobre %)

PASSO 3: Cascata
- Metodologia: Nao encontrada para este tema
- Framework: Nao encontrado
- Heuristicas:
  → Hormozi: 8-12%
  → Cole: ate 15% para top performers
  → Conflito detectado → consultar MAP-CONFLITOS
  → Resolucao: CONTEXTUAL
    - Se closer traz leads proprios → pode ser 15%
    - Se leads vem de marketing → 8-12%
- Modelo Mental: "Compensation como ferramenta de retencao" (MM-AH-010)
- Filosofia: Alinha com FIL-AH-001 (atrair A-players)

PASSO 4: Validacao
- Self-consistency: 3 raciocinios convergem para "depende do modelo"
- Limitacoes: Nao sei ticket medio atual nem margem bruta

PASSO 5: Resposta composta

---

[COMO CRO]

Para comissao de closers, recomendo estrutura escalonada: 10% base
para closers que recebem leads de marketing, podendo chegar a 15%
para closers que trazem leads proprios qualificados.

RACIOCINIO:
Apliquei heuristicas de Hormozi (8-12%) e Cole Gordon (ate 15%),
resolvendo o conflito contextualmente. A resolucao esta documentada
em CONF-003: leads de marketing = % menor, leads proprios = % maior.

EVIDENCIAS:
• HEUR-AH-025: "Comissao entre 8-12% do valor fechado"
• HEUR-CG-018: "Top performers que trazem pipeline podem ter 15%"

CONFIANCA: 75%
Divergencia entre fontes reduz confianca. Resolucao contextual
esta documentada mas pode nao cobrir todos os cenarios.

LIMITACOES:
• Nao tenho dados de margem bruta para validar viabilidade
• Nao sei estrutura atual de geracao de leads

PROXIMOS PASSOS:
1. Levantar margem bruta media por venda
2. Definir criterios claros para "lead proprio qualificado"
3. Simular impacto financeiro dos dois cenarios
```

---

*Fim do REASONING-MODEL-PROTOCOL*
