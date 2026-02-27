---
description: Extrai DNA Cognitivo (5 camadas) de uma pessoa a partir de INSIGHTS e CHUNKS
argument-hint: [pessoa] (alex-hormozi, cole-gordon, sam-oven, etc.)
---

# /extract-dna - Extracao de DNA Cognitivo

## Descricao
Extrai DNA Cognitivo (5 camadas) de uma pessoa a partir de INSIGHTS-STATE.json + outras fontes.

## Uso
```
/extract-dna [pessoa]
```

## Argumentos
- `pessoa`: Nome canonico da pessoa (alex-hormozi, cole-gordon, sam-oven, etc.)

## Exemplos
```
/extract-dna alex-hormozi
/extract-dna cole-gordon
```

---

## INSTRUCOES DE EXECUCAO

> **Workflow:** `core/workflows/wf-extract-dna.yaml`
> **Task:** `core/tasks/extract-dna.md`
> **Templates:** `core/templates/agents/`

```
═══════════════════════════════════════════════════════════════════════════════
EXTRACAO DE DNA: {PESSOA}
═══════════════════════════════════════════════════════════════════════════════

PASSO 1: VERIFICAR PRE-REQUISITOS

[ ] DOSSIER existe: /knowledge/dossiers/persons/DOSSIER-{PESSOA}.md
[ ] INSIGHTS-STATE.json tem insights desta pessoa
[ ] CHUNKS-STATE.json tem chunks desta pessoa

SE faltando pre-requisitos:
  ERRO: "Pessoa {PESSOA} nao tem dados suficientes para extracao.
         Falta: {lista do que falta}
         Execute primeiro o pipeline Jarvis para esta pessoa."

PASSO 2: CARREGAR FONTES

2.1 Carregar INSIGHTS-STATE.json
    → Filtrar por pessoa == "{PESSOA}"
    → Contar: {N} insights encontrados

2.2 Carregar NARRATIVES-STATE.json
    → Filtrar por pessoa == "{PESSOA}"
    → Contar: {N} narrativas encontradas

2.3 Carregar CHUNKS-STATE.json
    → Criar indice por chunk_id

2.4 Carregar DOSSIER-{PESSOA}.md
    → Ler documento completo

STATUS:
• Insights: {N}
• Narrativas: {N}
• Chunks: {N total no indice}
• DOSSIER: {linhas}

PASSO 3: EXTRAIR POR CAMADA

Para cada camada, aplicar regras de classificacao e gerar YAML:

3.1 FILOSOFIAS
    - Crencas fundamentais
    - Aparecem 3+ vezes em contextos diferentes
    - NAO contem numero/threshold

    → Gerar: /knowledge/dna/persons/{PESSOA}/FILOSOFIAS.yaml

3.2 MODELOS MENTAIS
    - Lentes de analise
    - Geram perguntas especificas
    - Mudam como voce VE

    → Gerar: /knowledge/dna/persons/{PESSOA}/MODELOS-MENTAIS.yaml

3.3 HEURISTICAS (PRIORIDADE MAXIMA)
    - Regras com THRESHOLD NUMERICO
    - Formato "Se X entao Y"
    - AS MAIS VALIOSAS

    → Gerar: /knowledge/dna/persons/{PESSOA}/HEURISTICAS.yaml

3.4 FRAMEWORKS
    - Estruturas nomeadas
    - Componentes definidos
    - NAO tem ordem rigida

    → Gerar: /knowledge/dna/persons/{PESSOA}/FRAMEWORKS.yaml

3.5 METODOLOGIAS
    - Processos passo-a-passo
    - Ordem RIGIDA
    - Criterios de sucesso por etapa

    → Gerar: /knowledge/dna/persons/{PESSOA}/METODOLOGIAS.yaml

PASSO 4: CALCULAR PESOS

Para cada item, calcular peso:

BASE: 0.50
+ 0.15  Citacao direta com chunk_id
+ 0.15  Aparece em 2+ fontes diferentes
+ 0.10  Threshold numerico especifico
+ 0.10  Aparece em 3+ fontes
+ 0.05  Contexto de NARRATIVES
+ 0.05  Linguagem prescritiva
- 0.20  Inferido
- 0.15  Contradiz outro item
- 0.10  Contexto ambiguo

PASSO 5: GERAR CONFIG.yaml

→ Gerar: /knowledge/dna/persons/{PESSOA}/CONFIG.yaml

Conteudo:
- Padroes comportamentais
- Sintese narrativa
- Metadados de extracao

PASSO 6: VALIDAR E REPORTAR

═══════════════════════════════════════════════════════════════════════════════
EXTRACAO CONCLUIDA: {PESSOA}
═══════════════════════════════════════════════════════════════════════════════

ARQUIVOS GERADOS:
• FILOSOFIAS.yaml      - {N} itens
• MODELOS-MENTAIS.yaml - {N} itens
• HEURISTICAS.yaml     - {N} itens ({N} com threshold numerico)
• FRAMEWORKS.yaml      - {N} itens
• METODOLOGIAS.yaml    - {N} itens
• CONFIG.yaml          - 1 arquivo

ESTATISTICAS:
• Total de itens: {N}
• Itens com peso >= 0.70: {N} ({%})
• Insights processados: {N}
• Chunks referenciados: {N}

PESO MEDIO: {X.XX}

PROXIMOS PASSOS:
1. Revisar HEURISTICAS.yaml (camada mais valiosa)
2. Verificar se todos os itens tem chunk_ids
3. Ajustar pesos se necessario
4. Executar /view-dna {PESSOA} para visualizar

═══════════════════════════════════════════════════════════════════════════════
```

---

## NOTAS

- NUNCA extrair sem chunk_id
- PRIORIZAR heuristicas com numeros
- MANTER genealogia completa (insight_origem + chunk_id + source_id)
- Itens com peso < 0.70 nao sao usados em respostas de agentes
