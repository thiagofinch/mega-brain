---
description: Visualiza o DNA Cognitivo extraido de uma pessoa ou dominio agregado
argument-hint: [pessoa|dominio] [--camada CAMADA] - Ex: alex-hormozi ou vendas
---

# /view-dna - Visualizar DNA Cognitivo

## Descricao
Visualiza o DNA Cognitivo extraido de uma pessoa ou dominio agregado.

## Uso
```
/view-dna [pessoa|dominio] [--camada CAMADA]
```

## Argumentos
- `pessoa|dominio`: Nome da pessoa (alex-hormozi) ou dominio agregado (vendas, hiring)
- `--camada`: Opcional. Filtrar por camada especifica (filosofias, heuristicas, etc.)

## Exemplos
```
/view-dna alex-hormozi
/view-dna alex-hormozi --camada heuristicas
/view-dna vendas
```

---

## INSTRUCOES DE EXECUCAO

### SE input e PESSOA:

```
1. VERIFICAR se DNA existe:
   /knowledge/dna/persons/{PESSOA}/

   SE NAO existir:
     "DNA de {PESSOA} ainda nao foi extraido.
      Execute: /extract-dna {pessoa}"

2. CARREGAR arquivos:
   - FILOSOFIAS.yaml
   - MODELOS-MENTAIS.yaml
   - HEURISTICAS.yaml
   - FRAMEWORKS.yaml
   - METODOLOGIAS.yaml
   - CONFIG.yaml

3. GERAR VISUALIZACAO:

═══════════════════════════════════════════════════════════════════════════════
DNA COGNITIVO: {PESSOA}
═══════════════════════════════════════════════════════════════════════════════

SINTESE:
{Conteudo de CONFIG.yaml → sintese.em_uma_frase}

{Conteudo de CONFIG.yaml → sintese.paragrafo}

DISTRIBUICAO:
┌────────────────────┬────────┬────────────┐
│ CAMADA             │ ITENS  │ PESO MEDIO │
├────────────────────┼────────┼────────────┤
│ Filosofias         │ {N}    │ {X.XX}     │
│ Modelos Mentais    │ {N}    │ {X.XX}     │
│ Heuristicas        │ {N}    │ {X.XX}     │
│   (com numero)     │ ({N})  │            │
│ Frameworks         │ {N}    │ {X.XX}     │
│ Metodologias       │ {N}    │ {X.XX}     │
├────────────────────┼────────┼────────────┤
│ TOTAL              │ {N}    │ {X.XX}     │
└────────────────────┴────────┴────────────┘

TOP HEURISTICAS (peso >= 0.80):
┌─────────────────────────────────────────────────────────────────────────────┐
│ {ID}: {regra}                                                               │
│ Threshold: {valor} {operador} {unidade}                                     │
│ Peso: {X.XX}                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
... (listar top 5)

TOP FILOSOFIAS:
• {ID}: {declaracao} (peso: {X.XX})
... (listar top 3)

FONTES UTILIZADAS:
• {source_id}: {source_title} - {N} chunks

═══════════════════════════════════════════════════════════════════════════════
```

### SE input e DOMINIO:

```
1. VERIFICAR se agregado existe:
   /knowledge/dna/AGGREGATED/AGG-{DOMINIO}.yaml

   SE NAO existir:
     "Agregacao do dominio {DOMINIO} ainda nao foi criada.
      Primeiro extrair DNA de 2+ pessoas, depois agregar."

2. CARREGAR AGG-{DOMINIO}.yaml

3. GERAR VISUALIZACAO:

═══════════════════════════════════════════════════════════════════════════════
DNA AGREGADO: {DOMINIO}
═══════════════════════════════════════════════════════════════════════════════

PESSOAS INCLUIDAS:
• {PESSOA1}
• {PESSOA2}
• ...

CONSENSOS FORTES (3+ pessoas concordam):
┌─────────────────────────────────────────────────────────────────────────────┐
│ {ID}: {regra/conceito}                                                      │
│ Peso agregado: {X.XX}                                                       │
│ Fontes: {PESSOA1} + {PESSOA2} + {PESSOA3}                                  │
└─────────────────────────────────────────────────────────────────────────────┘

CONSENSOS PARCIAIS (2 pessoas):
• {ID}: {regra} - {PESSOA1} + {PESSOA2}

COMPLEMENTARIDADES (1 pessoa):
• {ID}: {regra} - Apenas {PESSOA}

CONFLITOS MAPEADOS:
(ver MAP-CONFLITOS.yaml)

═══════════════════════════════════════════════════════════════════════════════
```

### SE --camada especificado:

```
Filtrar output para mostrar apenas a camada solicitada com mais detalhes:

═══════════════════════════════════════════════════════════════════════════════
{CAMADA} DE {PESSOA}
═══════════════════════════════════════════════════════════════════════════════

{Listar TODOS os itens da camada com detalhes completos}

Para cada item:
┌─────────────────────────────────────────────────────────────────────────────┐
│ ID: {id}                                                                    │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│ {Conteudo principal do item}                                               │
│                                                                             │
│ Evidencias:                                                                 │
│ • "{citacao}" - {source_title} ({chunk_id})                                │
│                                                                             │
│ Dominios: {lista}                                                           │
│ Peso: {X.XX}                                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
```

---

## NOTAS

- Use --camada heuristicas para ver os itens mais acionaveis
- Itens com peso < 0.70 nao sao usados em respostas de agentes
- Para conflitos entre pessoas, consultar MAP-CONFLITOS.yaml
