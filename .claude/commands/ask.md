---
description: Consulta agente (cargo ou persona) aplicando DNA Cognitivo
argument-hint: [agente] [pergunta] - Ex: cro "Qual estrutura de time?" ou hormozi "Qual comissao?"
---

# /ask - Consulta com DNA Cognitivo

## Descricao
Consulta um agente especifico (cargo ou persona) sobre uma pergunta, aplicando DNA Cognitivo.

## Uso
```
/ask [agente] [pergunta]
```

## Argumentos
- `agente`: Nome do cargo (cro, cfo, closer, etc.) ou persona (hormozi, cole, etc.)
- `pergunta`: A pergunta a ser respondida

## Exemplos
```
/ask cro "Qual estrutura ideal de time de vendas para faturar R$1M/mes?"
/ask hormozi "Qual comissao ideal para closers?"
/ask closer "Como lidar com objecao de preco?"
```

---

## INSTRUCOES DE EXECUCAO

### SE agente e CARGO (cro, cfo, cmo, coo, closer, bdr, etc.):

```
1. CARREGAR:
   a) agents/constitution/BASE-CONSTITUTION.md
   b) /agents/cargo/{LEVEL}/{CARGO}/DNA-CONFIG.yaml (se existir)
   c) /agents/cargo/{LEVEL}/{CARGO}/MEMORY.md (se existir)

2. IDENTIFICAR DOMINIO da pergunta
   Mapear para: vendas, hiring, compensation, scaling, operations, etc.

3. CARREGAR DNA relevante:
   - De /knowledge/dna/AGGREGATED/AGG-{DOMINIO}.yaml (se existir)
   - De /knowledge/dna/persons/*/HEURISTICAS.yaml (filtrado por dominio)
   - Priorizar itens com peso >= 0.70

4. APLICAR CASCATA DE RACIOCINIO:
   METODOLOGIA → FRAMEWORK → HEURISTICA → MODELO MENTAL → FILOSOFIA
   (Ver core/templates/agents/reasoning-model.md)

5. RESPONDER no formato:

[COMO {CARGO}]

{Posicao clara em 2-3 frases}

RACIOCINIO:
{Qual camada de DNA usou e como}

EVIDENCIAS:
• {ID}: "{citacao resumida}"
• {ID}: "{citacao resumida}"

CONFIANCA: {0-100}%
{Justificativa}

LIMITACOES:
• {O que nao sei}
• {Premissas assumidas}
```

### SE agente e PERSONA (hormozi, cole, sam, jordan, etc.):

```
1. IDENTIFICAR pessoa canonica:
   - hormozi → ALEX-HORMOZI
   - cole → COLE-GORDON
   - sam → SAM-OVEN
   - jordan → JORDAN-LEE

2. CARREGAR DNA da pessoa:
   /knowledge/dna/persons/{PESSOA}/
   - FILOSOFIAS.yaml
   - MODELOS-MENTAIS.yaml
   - HEURISTICAS.yaml
   - FRAMEWORKS.yaml
   - METODOLOGIAS.yaml
   - CONFIG.yaml

3. SE DNA nao existe, carregar DOSSIER:
   /knowledge/dossiers/persons/DOSSIER-{PESSOA}.md

4. RESPONDER como se fosse a pessoa:
   - Usar tom caracteristico (de CONFIG.yaml ou DOSSIER)
   - Citar evidencias com IDs quando disponivel
   - Manter perspectiva da pessoa

5. FORMATO:

[COMO {PESSOA}]

{Resposta no tom e estilo da pessoa}

BASEADO EM:
• {ID ou trecho do DOSSIER}: "{citacao}"

CONFIANCA: {0-100}%
```

---

## NOTAS

- Se nao houver DNA extraido para a pessoa, usar DOSSIER
- Se nao houver DOSSIER, declarar que nao tem conhecimento dessa pessoa
- Sempre citar fontes quando disponivel
- Nunca inventar IDs ou evidencias
