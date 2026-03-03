# DNA-EXTRACTION-PROTOCOL
# Integrado ao Pipeline JARVIS (Phase 8.1.8 - AUTO-CREATE/UPDATE)

> **Versão:** 1.2.0
> **Trigger AUTOMÁTICO:** DOSSIER existe + densidade >= 3/5 (via Phase 8.1.8)
> **Trigger MANUAL:** `/extract-dna {pessoa}` (para extração independente)
> **Input:** INSIGHTS-STATE.json + NARRATIVES-STATE.json + CHUNKS-STATE.json + DOSSIER
> **Output:** 6 arquivos YAML em knowledge/dna/persons/{PESSOA}/
>
> **CHANGELOG v1.2.0 (2025-12-28):**
> - Removido: Trigger "2+ fontes" (critério arbitrário)
> - Adicionado: Trigger automático baseado em densidade de DOSSIER (>= 3/5)
> - Integrado: Phase 8.1.8 do Pipeline Jarvis agora executa extração automaticamente
> - Mantido: Comando manual `/extract-dna` para extrações independentes

---

## PRINCÍPIO FUNDAMENTAL: EXTRAÇÃO EXAUSTIVA

DNA-EXTRACTION é EXAUSTIVO, não seletivo.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  O extrator DEVE:                                                           │
│                                                                             │
│  1. CARREGAR todos os arquivos de estado (sem exceção)                     │
│  2. NAVEGAR livremente entre eles durante a extração                       │
│  3. CRUZAR informações para enriquecer cada item                           │
│  4. NÃO PARAR até ter a extração mais rica possível                        │
│                                                                             │
│  A "prioridade" de fonte indica onde um tipo de informação                 │
│  TIPICAMENTE aparece melhor, NÃO limita a busca.                           │
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│                                                                             │
│  EXTRAÇÃO (1x por pessoa) → RICA, COMPLETA, EXAUSTIVA                      │
│  USO PELOS AGENTES (Nx)   → SELETIVO, EFICIENTE                            │
│                                                                             │
│  A economia de tokens acontece no USO, não na EXTRAÇÃO.                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## IDENTIDADE DO EXTRATOR

Você é o META-EXTRACTOR do sistema DNA Cognitivo.

Sua função é transformar conhecimento já processado pelo Pipeline JARVIS
(Phases 1-6) em estrutura cognitiva de 5 camadas que representa
COMO uma pessoa PENSA, não apenas O QUE ela sabe.

---

## FONTES DE ENTRADA (Todas com Rastreabilidade Completa)

### ARQUITETURA DE LEITURA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  TODAS AS FONTES SÃO COMPLETAS                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  Todos os arquivos abaixo possuem:                                         │
│  • chunk_ids (rastreabilidade)                                             │
│  • Referências numéricas                                                    │
│  • Links para fonte original                                               │
│                                                                             │
│  O extrator carrega TODOS e navega livremente entre eles.                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1. INSIGHTS-STATE.json

```
Localização: processing/insights/INSIGHTS-STATE.json

CARACTERÍSTICAS:
• Itens DISCRETOS (um insight = um item)
• Já priorizados (HIGH, MEDIUM, LOW)
• chunk_ids preservados
• Campo "tag" pode ter pré-classificação

ESTRUTURA:
{
  "id": "HP001",
  "insight": "Close rate below 30% indicates qualification problem",
  "tag": "[HEURÍSTICA]",
  "quote": "If your close rate is below 30%...",
  "chunks": ["CJ001_005", "CJ001_006"],
  "confidence": "HIGH",
  "priority": "HIGH",
  "pessoa": "Alex Hormozi",
  "temas": ["05-METRICAS", "02-PROCESSO-VENDAS"]
}

MAIS ÚTIL PARA:
• Heurísticas (especialmente com números)
• Frameworks (estruturas nomeadas)
• Metodologias (processos)
• Qualquer item que se beneficia de ser discreto
```

---

### 2. NARRATIVES-STATE.json

```
Localização: processing/narratives/NARRATIVES-STATE.json

CARACTERÍSTICAS:
• CONTEXTO e relações entre conceitos
• Mostra COMO a pessoa estrutura pensamento
• Captura tom e estilo
• chunk_ids preservados nas referências

ESTRUTURA:
{
  "pessoa": "Alex Hormozi",
  "tema": "Hiring",
  "narrativa": "Hormozi consistentemente argumenta que competência
               supera experiência...",
  "chunks_referenciados": ["CJ001_005", "CJ001_006", "AH-HR001-042"],
  "tom": "direto, provocativo",
  "frases_marcantes": ["The math doesn't lie", "Volume is vanity"]
}

MAIS ÚTIL PARA:
• Filosofias (crenças fundamentais aparecem em contexto)
• Modelos mentais (lentes de análise)
• Padrões comportamentais (para CONFIG.yaml)
• Relações entre conceitos
```

---

### 3. CHUNKS-STATE.json

```
Localização: processing/chunks/CHUNKS-STATE.json

CARACTERÍSTICAS:
• Texto ORIGINAL completo
• Granularidade máxima
• Source_id para rastrear material

ESTRUTURA:
{
  "id_chunk": "CJ001_005",
  "texto": "If you're 40 and you're not rich yet, it means
            you're not competent...",
  "pessoas": ["Alex Hormozi"],
  "temas": ["03-CONTRATACAO"],
  "meta": {
    "source_id": "CJ001",
    "source_title": "Charlie Johnson Interview"
  }
}

MAIS ÚTIL PARA:
• Citações exatas (campo "evidências" em todos os YAMLs)
• Verificar contexto original
• Resolver ambiguidades
```

---

### 4. DOSSIER-{PESSOA}.md

```
Localização: knowledge/dossiers/persons/DOSSIER-{PESSOA}.md

CARACTERÍSTICAS:
• Síntese COMPLETA por pessoa
• chunk_ids inline (rastreabilidade completa)
• Referências numéricas
• Visão consolidada de todos os materiais

ESTRUTURA:
(Documento markdown com seções, cada afirmação com referência a chunk_id)

MAIS ÚTIL PARA:
• Visão geral consolidada
• Verificar completude (não perdi nada?)
• Contexto amplo de múltiplos materiais
• Sínteses que cruzam temas
```

---

### MATRIZ: TODAS AS FONTES × TODAS AS CAMADAS

| Camada | INSIGHTS | NARRATIVES | CHUNKS | DOSSIER |
|--------|----------|------------|--------|---------|
| FILOSOFIAS | Buscar | Buscar | Evidência | Buscar |
| MODELOS MENTAIS | Buscar | Buscar | Evidência | Buscar |
| HEURÍSTICAS | Buscar | Buscar | Evidência | Buscar |
| FRAMEWORKS | Buscar | Buscar | Evidência | Buscar |
| METODOLOGIAS | Buscar | Buscar | Evidência | Buscar |
| CONFIG (padrões) | Buscar | Buscar | - | Buscar |

**Legenda:**
- **Buscar**: Fonte ativa para encontrar itens desta camada
- **Evidência**: Fonte para citações exatas (campo "evidências")

**REGRA**: Nenhuma célula é "ignorar". Todas as fontes são consultadas para todas as camadas.

---

## PROCESSO DE EXTRAÇÃO EXAUSTIVA (8 Passos)

### PASSO 1: CARREGAR TODOS OS ARQUIVOS

```
1.1 Carregar INSIGHTS-STATE.json
    → Filtrar por pessoa == "{PESSOA_ALVO}"
    → Manter TODOS os insights (não filtrar por prioridade ainda)

1.2 Carregar NARRATIVES-STATE.json
    → Filtrar por pessoa == "{PESSOA_ALVO}"
    → Manter TODAS as narrativas

1.3 Carregar CHUNKS-STATE.json
    → Criar índice por chunk_id para busca rápida
    → NÃO filtrar (chunks são buscados sob demanda)

1.4 Carregar DOSSIER-{PESSOA}.md
    → Ler documento completo
    → Identificar seções e referências

RESULTADO: 4 fontes carregadas, prontas para navegação cruzada
```

### PASSO 2: PRIMEIRA PASSAGEM - IDENTIFICAR CANDIDATOS

```
Para cada CAMADA (filosofias, modelos mentais, heurísticas, frameworks, metodologias):

2.1 Varrer INSIGHTS-STATE
    → Se tem tag correspondente, marcar como candidato
    → Se não tem tag, aplicar regras de classificação
    → Registrar: insight_id, chunk_ids, classificação

2.2 Varrer NARRATIVES-STATE
    → Identificar padrões da camada no texto
    → Registrar: narrativa_id, chunk_ids referenciados, trecho relevante

2.3 Varrer DOSSIER
    → Identificar menções relevantes para a camada
    → Registrar: seção, chunk_ids inline, contexto

RESULTADO: Lista de candidatos por camada, de TODAS as fontes
```

### PASSO 3: SEGUNDA PASSAGEM - CRUZAR E ENRIQUECER

```
Para cada CANDIDATO identificado:

3.1 CRUZAR entre fontes:

    SE candidato veio de INSIGHTS:
    → Buscar em NARRATIVES: tem contexto adicional?
    → Buscar em DOSSIER: aparece em mais lugares?
    → Buscar em CHUNKS: citação exata

    SE candidato veio de NARRATIVES:
    → Buscar em INSIGHTS: tem versão discreta?
    → Buscar em DOSSIER: confirmação?
    → Buscar em CHUNKS: citação exata via chunk_ids referenciados

    SE candidato veio de DOSSIER:
    → Buscar em INSIGHTS: tem insight correspondente?
    → Buscar em NARRATIVES: tem contexto?
    → Buscar em CHUNKS: citação exata via chunk_ids inline

3.2 COMBINAR informações:
    → Declaração principal (mais clara/completa)
    → Contexto de uso (de narratives ou dossier)
    → Evidências com citações exatas (de chunks)
    → Múltiplas aparições (aumenta peso)

3.3 DEDUPLICAR:
    → Se mesmo conceito aparece em múltiplas fontes, MESCLAR em um item
    → Não criar duplicatas
    → Manter TODAS as evidências encontradas

RESULTADO: Itens enriquecidos com informação de múltiplas fontes
```

### PASSO 4: VERIFICAÇÃO DE COMPLETUDE

```
4.1 Revisar INSIGHTS não utilizados:
    → Algum insight HIGH priority não entrou em nenhuma camada?
    → Se sim, revisar classificação ou criar item

4.2 Revisar NARRATIVES não utilizados:
    → Alguma narrativa menciona padrão importante não capturado?
    → Se sim, criar item (pode ter peso menor se evidência fraca)

4.3 Revisar DOSSIER:
    → Seções importantes não representadas nos YAMLs?
    → Se sim, voltar às fontes e extrair

4.4 Contar aparições:
    → Conceitos que aparecem em 3+ fontes = peso alto
    → Conceitos que aparecem em 1 fonte = peso menor

RESULTADO: Garantia de que nada importante foi perdido
```

### PASSO 5: BUSCAR CITAÇÕES EXATAS

Para cada item classificado:

```
5.1 Ler campo "chunks" do insight (ex: ["CJ001_005", "CJ001_006"])
5.2 Para cada chunk_id:
    - Buscar em CHUNKS-STATE.json
    - Extrair campo "texto" (citação exata)
    - Extrair campo "meta.source_id" e "meta.source_title"
5.3 Montar estrutura de evidência:
    {
      "citação": "texto exato do chunk",
      "chunk_id": "CJ001_005",
      "source_id": "CJ001",
      "source_title": "Charlie Johnson Interview"
    }
```

### PASSO 6: CALCULAR PESO DE CADA ITEM

```
FÓRMULA DE PESO:

BASE: 0.50

MODIFICADORES POSITIVOS:
+ 0.15  Citação direta com chunk_id confirmado
+ 0.15  Aparece em 2+ fontes diferentes (source_ids distintos)
+ 0.10  Contém threshold numérico específico
+ 0.10  Aparece em 3+ fontes diferentes (INSIGHTS + NARRATIVES + DOSSIER)
+ 0.05  Aparece em 2 fontes diferentes
+ 0.05  Tem contexto de uso extraído de NARRATIVES
+ 0.05  Linguagem prescritiva ("deve", "sempre", "nunca")

MODIFICADORES NEGATIVOS:
- 0.20  Inferido (não explícito no texto)
- 0.15  Contradiz outro item da mesma pessoa
- 0.10  Contexto ambíguo

RESULTADO:
peso ≥ 0.70  → Usar em respostas de agentes
peso < 0.70  → Apenas enriquecimento interno (não citar)

EXEMPLO:
Insight: "Close rate < 30% indica problema de qualificação"
- Base: 0.50
- Citação direta: +0.15
- Threshold numérico: +0.10
- Linguagem prescritiva: +0.05
= PESO: 0.80 ✓ (usar em respostas)
```

### PASSO 7: GERAR ARQUIVOS YAML POR CAMADA

Para cada camada, gerar arquivo YAML no formato especificado abaixo.

### PASSO 8: GERAR CONFIG.yaml

```
8.1 Extrair padrões comportamentais de NARRATIVES:
    → Tom de comunicação
    → Uso de histórias
    → Frases marcantes

8.2 Extrair de DOSSIER:
    → Síntese narrativa
    → Maior contribuição
    → Pontos cegos

8.3 Compilar metadados:
    → Total de itens por camada
    → Fontes utilizadas com contagem
    → Peso médio
```

---

## FLUXO VISUAL: NAVEGAÇÃO ENTRE FONTES

```
                         ┌─────────────────────┐
                         │   DNA-EXTRACTION    │
                         │   CARREGA TUDO      │
                         └─────────┬───────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ INSIGHTS-STATE  │      │NARRATIVES-STATE │      │    DOSSIER      │
│                 │      │                 │      │                 │
│ • Discretos     │      │ • Contexto      │      │ • Consolidado   │
│ • Tags          │      │ • Relações      │      │ • Completo      │
│ • chunk_ids     │◄────►│ • chunk_ids     │◄────►│ • chunk_ids     │
│                 │      │                 │      │                 │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         │         NAVEGAÇÃO      │       LIVRE            │
         │◄───────────────────────┼───────────────────────►│
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │    CHUNKS-STATE     │
                       │                     │
                       │  • Citações exatas  │
                       │  • Texto original   │
                       │  • Source_id        │
                       └─────────────────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │   ITEM DNA RICO     │
                       │                     │
                       │ • De múltiplas      │
                       │   fontes            │
                       │ • Contexto          │
                       │ • Evidências        │
                       │ • Rastreável        │
                       └─────────────────────┘
```

### EXEMPLO DE NAVEGAÇÃO COMPLETA

```
EXTRAINDO: Heurística "Close rate < 30% = problema de qualificação"

┌─ PASSO 1: Encontro em INSIGHTS ─────────────────────────────────────────────┐
│                                                                             │
│ {                                                                           │
│   "id": "INS-AH-042",                                                       │
│   "insight": "Close rate below 30% indicates qualification problem",        │
│   "tag": "[HEURÍSTICA]",                                                    │
│   "chunks": ["AH-SS001-chunk_198"]                                          │
│ }                                                                           │
│                                                                             │
│ → Tenho: insight discreto + chunk_id + classificação                       │
│ → Falta: contexto de quando aplicar                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ PASSO 2: Busco contexto em NARRATIVES ─────────────────────────────────────┐
│                                                                             │
│ {                                                                           │
│   "pessoa": "Alex Hormozi",                                                 │
│   "tema": "Sales Metrics",                                                  │
│   "narrativa": "Hormozi enfatiza que métricas de close rate são            │
│                 diagnósticas, não de performance. Abaixo de 30%,           │
│                 o problema está upstream na qualificação, não no           │
│                 closer. Isso se aplica especialmente a high-ticket          │
│                 onde ciclo é mais longo...",                                │
│   "chunks_referenciados": ["AH-SS001-chunk_198", "AH-SS001-chunk_199"]      │
│ }                                                                           │
│                                                                             │
│ → Agora tenho: contexto de aplicação + chunks adicionais                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ PASSO 3: Verifico em DOSSIER ──────────────────────────────────────────────┐
│                                                                             │
│ ### Métricas de Vendas                                                      │
│                                                                             │
│ Hormozi define benchmarks claros para diagnóstico:                         │
│ - Close rate < 30%: problema de qualificação [AH-SS001-chunk_198]          │
│ - Show rate < 80%: problema de confirmação [AH-SS001-chunk_205]            │
│ - Cash collected < 90%: problema de qualificação financeira                │
│                                                                             │
│ Esta abordagem aparece em 3 materiais: SS001, HR001, TM002.                │
│                                                                             │
│ → Agora tenho: confirmação de múltiplas aparições + heurísticas relacionadas│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ PASSO 4: Busco citação em CHUNKS ──────────────────────────────────────────┐
│                                                                             │
│ {                                                                           │
│   "id_chunk": "AH-SS001-chunk_198",                                        │
│   "texto": "If your close rate is below 30%, you don't have a closing      │
│             problem, you have a qualification problem. The issue is         │
│             upstream, not downstream. Stop training closers and start       │
│             fixing your qualification process.",                            │
│   "meta": {                                                                 │
│     "source_id": "AH-SS001",                                               │
│     "source_title": "How I Scaled My Sales Team"                           │
│   }                                                                         │
│ }                                                                           │
│                                                                             │
│ → Agora tenho: citação exata + fonte original                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ RESULTADO: Item DNA Rico ──────────────────────────────────────────────────┐
│                                                                             │
│ - id: "HEUR-AH-015"                                                        │
│   regra: "Se close rate < 30%, problema é qualificação, não closing"       │
│                                                                             │
│   threshold:                                                                │
│     valor: 30                                                               │
│     operador: "<"                                                           │
│     unidade: "%"                                                            │
│                                                                             │
│   contexto_de_uso: |                                                        │
│     Aplica especialmente a high-ticket com ciclo mais longo.               │
│     Métrica é diagnóstica, não de performance do closer.                   │
│     Ação corretiva deve focar upstream (qualificação).                     │
│                                                                             │
│   ação_recomendada: "Revisar processo de qualificação, não treinar closers"│
│                                                                             │
│   heurísticas_relacionadas:                                                │
│     - "Show rate < 80% = problema de confirmação"                          │
│     - "Cash collected < 90% = problema de qualificação financeira"         │
│                                                                             │
│   evidências:                                                               │
│     - citação: "If your close rate is below 30%, you don't have..."        │
│       chunk_id: "AH-SS001-chunk_198"                                       │
│       source_id: "AH-SS001"                                                │
│       source_title: "How I Scaled My Sales Team"                           │
│                                                                             │
│   aparições: 3  # SS001, HR001, TM002 (de DOSSIER)                         │
│                                                                             │
│   fontes_consultadas:                                                       │
│     - INSIGHTS-STATE (insight discreto)                                    │
│     - NARRATIVES-STATE (contexto de aplicação)                             │
│     - DOSSIER (múltiplas aparições)                                        │
│     - CHUNKS-STATE (citação exata)                                         │
│                                                                             │
│   peso: 0.95  # Alto: número + citação + múltiplas fontes + contexto       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REGRAS DE CLASSIFICAÇÃO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  REGRAS DE CLASSIFICAÇÃO                                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ FILOSOFIA                                                           │   │
│  │ ─────────                                                           │   │
│  │ Identificar quando:                                                 │   │
│  │ • Expressa CRENÇA fundamental sobre como o mundo funciona          │   │
│  │ • Aparece 3+ vezes em diferentes contextos                         │   │
│  │ • Linguagem: "acredito que", "fundamentalmente", "sempre"          │   │
│  │ • NÃO contém número ou threshold                                   │   │
│  │                                                                     │   │
│  │ Exemplos:                                                           │   │
│  │ ✓ "Volume é vaidade, conversão é sanidade"                         │   │
│  │ ✓ "Competência vale mais que experiência"                          │   │
│  │ ✗ "Se conversão < 20%, revisar pitch" (isso é HEURÍSTICA)          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ MODELO MENTAL                                                       │   │
│  │ ─────────────                                                       │   │
│  │ Identificar quando:                                                 │   │
│  │ • Descreve LENTE para interpretar situações                        │   │
│  │ • Gera PERGUNTAS específicas                                       │   │
│  │ • Muda como você VÊ, não o que você FAZ                            │   │
│  │                                                                     │   │
│  │ Exemplos:                                                           │   │
│  │ ✓ "Pensar em termos de LTV vs CAC" → Lente de unit economics       │   │
│  │ ✓ "Ver objeções como pedidos de informação" → Lente de vendas      │   │
│  │ ✗ "Calcular LTV dividindo..." (isso é METODOLOGIA)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ HEURÍSTICA (PRIORIDADE MÁXIMA SE TIVER NÚMERO)                      │   │
│  │ ──────────                                                          │   │
│  │ Identificar quando:                                                 │   │
│  │ • Contém NÚMERO ou THRESHOLD específico                            │   │
│  │ • Formato "Se X [operador] Y, então Z"                             │   │
│  │ • Regra de decisão rápida                                          │   │
│  │                                                                     │   │
│  │ Exemplos:                                                           │   │
│  │ ✓ "Se close rate < 30%, problema é qualificação"                   │   │
│  │ ✓ "CAC deve ser < 1/3 do LTV"                                      │   │
│  │ ✓ "Não contratar se nota < 8/10 em culture fit"                    │   │
│  │ ✗ "Close rate baixo indica problema" (sem número = não é H.)       │   │
│  │                                                                     │   │
│  │ ATENÇÃO: Heurísticas com números são as MAIS VALIOSAS.              │   │
│  │ Priorizar extração dessas.                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ FRAMEWORK                                                           │   │
│  │ ─────────                                                           │   │
│  │ Identificar quando:                                                 │   │
│  │ • Estrutura NOMEADA para organizar análise                         │   │
│  │ • Tem componentes/dimensões definidas                              │   │
│  │ • É um "esqueleto" a ser preenchido                                │   │
│  │ • NÃO tem ordem rígida (se tem, é METODOLOGIA)                     │   │
│  │                                                                     │   │
│  │ Exemplos:                                                           │   │
│  │ ✓ "Value Equation: Outcome × Likelihood / Time × Effort"           │   │
│  │ ✓ "CLOSER Framework: Clarify, Label, Overview..."                  │   │
│  │ ✗ "Primeiro faça X, depois Y" (isso é METODOLOGIA)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ METODOLOGIA                                                         │   │
│  │ ───────────                                                         │   │
│  │ Identificar quando:                                                 │   │
│  │ • Processo PASSO-A-PASSO                                           │   │
│  │ • Ordem RÍGIDA (Step 1, Step 2...)                                 │   │
│  │ • Tem critérios de sucesso por etapa                               │   │
│  │                                                                     │   │
│  │ Exemplos:                                                           │   │
│  │ ✓ "Para contratar: 1) Postar vaga, 2) Triagem, 3) Entrevista..."   │   │
│  │ ✓ "Processo de onboarding em 5 fases..."                           │   │
│  │ ✗ "Os 4 pilares de vendas" (isso é FRAMEWORK)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FORMATOS DE OUTPUT

### FILOSOFIAS.yaml

```yaml
# knowledge/dna/persons/{PESSOA}/FILOSOFIAS.yaml
# Gerado em: {DATA}
# Fonte: INSIGHTS-STATE.json filtrado por pessoa

pessoa: "{PESSOA}"
versão: "1.0.0"
data_extração: "{DATA_ISO}"
total_itens: {N}

filosofias:
  - id: "FIL-{PESSOA_SIGLA}-001"
    nome: "{Nome curto da filosofia}"
    declaração: "{Frase que captura a crença fundamental}"

    evidências:
      - citação: "{Texto exato do chunk}"
        chunk_id: "{chunk_id do CHUNKS-STATE}"
        source_id: "{source_id}"
        source_title: "{título do material}"
      - citação: "{Segunda citação se houver}"
        chunk_id: "{chunk_id}"
        source_id: "{source_id}"
        source_title: "{título}"

    insight_origem: "{ID do insight no INSIGHTS-STATE}"

    implicações:
      fazer:
        - "{Ação que deriva desta filosofia}"
        - "{Outra ação}"
      evitar:
        - "{Comportamento contrário à filosofia}"

    conflitos_potenciais:
      - "{Situação onde esta filosofia pode conflitar com outra}"

    domínios:
      - "{domínio canônico}" # ex: "hiring", "compensation", "scaling"

    peso: {0.00-1.00}

  - id: "FIL-{PESSOA_SIGLA}-002"
    # ... próxima filosofia
```

### MODELOS-MENTAIS.yaml

```yaml
# knowledge/dna/persons/{PESSOA}/MODELOS-MENTAIS.yaml

pessoa: "{PESSOA}"
versão: "1.0.0"
data_extração: "{DATA_ISO}"
total_itens: {N}

modelos_mentais:
  - id: "MM-{PESSOA_SIGLA}-001"
    nome: "{Nome do modelo mental}"
    descrição: "{Como essa lente funciona}"

    analogia: "{Metáfora que explica o modelo}"

    como_funciona: |
      {Explicação de 2-3 linhas de como aplicar esta lente}

    perguntas_que_dispara:
      - "{Pergunta 1 que este modelo faz você perguntar}"
      - "{Pergunta 2}"
      - "{Pergunta 3}"

    quando_aplicar:
      - "{Situação 1}"
      - "{Situação 2}"

    quando_nao_aplicar:
      - "{Contexto onde este modelo não se aplica}"

    evidências:
      - citação: "{Texto exato}"
        chunk_id: "{chunk_id}"
        source_id: "{source_id}"
        source_title: "{título}"

    insight_origem: "{ID do insight}"

    filosofia_relacionada: "FIL-{PESSOA_SIGLA}-{N}"

    domínios:
      - "{domínio canônico}"

    peso: {0.00-1.00}
```

### HEURISTICAS.yaml

```yaml
# knowledge/dna/persons/{PESSOA}/HEURISTICAS.yaml
# NOTA: Esta é a camada MAIS VALIOSA - priorizar heurísticas com números

pessoa: "{PESSOA}"
versão: "1.0.0"
data_extração: "{DATA_ISO}"
total_itens: {N}

heurísticas:
  - id: "HEUR-{PESSOA_SIGLA}-001"
    regra: "{Frase 'Se X então Y' com threshold}"

    threshold:
      valor: {número}
      operador: "{<, >, <=, >=, ==, entre}"
      unidade: "{%, dias, R$, ratio, etc}"
      # Para "entre": usar valor_min e valor_max

    contexto_de_uso: "{Quando aplicar esta regra}"

    ação_recomendada: "{O que fazer quando threshold é atingido}"

    exceções:
      - "{Situação onde a regra não se aplica}"

    evidências:
      - citação: "{Texto exato com o número}"
        chunk_id: "{chunk_id}"
        source_id: "{source_id}"
        source_title: "{título}"

    insight_origem: "{ID do insight}"

    modelo_mental_relacionado: "MM-{PESSOA_SIGLA}-{N}"
    filosofia_relacionada: "FIL-{PESSOA_SIGLA}-{N}"

    domínios:
      - "{domínio canônico}"

    peso: {0.00-1.00}

  # Heurísticas TEXTUAIS (sem número específico) - peso menor
  - id: "HEUR-{PESSOA_SIGLA}-020"
    regra: "{Regra qualitativa sem número}"

    threshold: null  # Indica heurística textual

    qualificador: "{alto, baixo, muito, pouco, etc}"

    contexto_de_uso: "{Quando aplicar}"
    ação_recomendada: "{O que fazer}"

    evidências:
      - citação: "{Texto}"
        chunk_id: "{chunk_id}"
        source_id: "{source_id}"
        source_title: "{título}"

    insight_origem: "{ID}"

    domínios:
      - "{domínio}"

    peso: {0.00-1.00}  # Geralmente menor que heurísticas numéricas
```

### FRAMEWORKS.yaml

```yaml
# knowledge/dna/persons/{PESSOA}/FRAMEWORKS.yaml

pessoa: "{PESSOA}"
versão: "1.0.0"
data_extração: "{DATA_ISO}"
total_itens: {N}

frameworks:
  - id: "FW-{PESSOA_SIGLA}-001"
    nome: "{Nome do framework}"

    tipo: "{matriz, canvas, sequência, modelo, lista}"

    estrutura:
      # Para MATRIZ:
      eixo_x: "{Nome do eixo}"
      eixo_y: "{Nome do eixo}"
      quadrantes:
        - nome: "{Q1}"
          descrição: "{O que significa}"
        - nome: "{Q2}"
          descrição: "{...}"

      # OU Para CANVAS/MODELO:
      componentes:
        - nome: "{Componente 1}"
          descrição: "{O que é}"
          perguntas:
            - "{Pergunta para preencher}"
        - nome: "{Componente 2}"
          descrição: "{...}"

      # OU Para LISTA:
      elementos:
        - "{Elemento 1}"
        - "{Elemento 2}"

    como_usar: |
      {Instruções de 3-5 linhas para aplicar o framework}

    output_esperado: "{O que você terá ao final}"

    quando_usar:
      - "{Situação 1}"

    quando_nao_usar:
      - "{Situação onde não se aplica}"

    evidências:
      - citação: "{Texto}"
        chunk_id: "{chunk_id}"
        source_id: "{source_id}"
        source_title: "{título}"

    insight_origem: "{ID}"

    domínios:
      - "{domínio}"

    peso: {0.00-1.00}
```

### METODOLOGIAS.yaml

```yaml
# knowledge/dna/persons/{PESSOA}/METODOLOGIAS.yaml

pessoa: "{PESSOA}"
versão: "1.0.0"
data_extração: "{DATA_ISO}"
total_itens: {N}

metodologias:
  - id: "MET-{PESSOA_SIGLA}-001"
    nome: "{Nome da metodologia}"
    objetivo: "{O que se alcança ao executar}"

    pré_requisitos:
      - "{O que precisa ter antes de começar}"

    passos:
      - número: 1
        nome: "{Nome do passo}"
        descrição: "{O que fazer}"
        critério_de_sucesso: "{Como saber que completou}"
        armadilhas:
          - "{Erro comum neste passo}"

      - número: 2
        nome: "{Nome}"
        descrição: "{...}"
        critério_de_sucesso: "{...}"

      # ... mais passos

    checkpoints:
      - após_passo: 2
        validar: "{O que verificar antes de continuar}"
      - após_passo: 4
        validar: "{...}"

    duração_estimada: "{tempo para executar}"

    erros_comuns:
      - erro: "{Descrição do erro}"
        como_evitar: "{Prevenção}"

    evidências:
      - citação: "{Texto}"
        chunk_id: "{chunk_id}"
        source_id: "{source_id}"
        source_title: "{título}"

    insight_origem: "{ID}"

    domínios:
      - "{domínio}"

    peso: {0.00-1.00}
```

### CONFIG.yaml

```yaml
# knowledge/dna/persons/{PESSOA}/CONFIG.yaml

pessoa: "{PESSOA}"
versão: "1.0.0"
data_extração: "{DATA_ISO}"

# PADRÕES COMPORTAMENTAIS (extraídos de como a pessoa se comunica)
padrões_comportamentais:
  tom_de_comunicação:
    estilo: "{direto, didático, provocativo, analítico, etc}"
    formalidade: "{formal, informal, misto}"
    uso_de_humor: "{frequente, ocasional, raro, nunca}"

  uso_de_histórias:
    frequência: "{sempre, frequente, ocasional, raro}"
    tipo_preferido: "{pessoal, de clientes, hipotético, analógico}"

  resposta_a_objeções:
    abordagem: "{confronto direto, reframe, pergunta de volta, etc}"

  linguagem_característica:
    termos_próprios:
      - termo: "{termo específico que usa}"
        significado: "{o que significa no contexto dele}"
    frases_de_efeito:
      - "{Frase marcante 1}"
      - "{Frase marcante 2}"

# VOZ - COMO ESTA PESSOA FALA (OBRIGATÓRIO)
voz:
  vocabulário_usar:
    - "{termo ou expressão que sempre usa}"
    - "{outro termo característico}"

  vocabulário_evitar:
    - "{termo que nunca usa ou evita}"
    - "{linguagem que vai contra sua filosofia}"

  exemplos_resposta:
    - situação: "{pergunta ou cenário comum}"
      resposta_estilo: |
        "{Como essa pessoa responderia, no tom e estilo dela}"

    - situação: "{outra situação}"
      resposta_estilo: |
        "{Resposta característica}"

  padrões_argumentação:
    estrutura_típica: |
      {Como essa pessoa estrutura argumentos - 3-5 passos}

    uso_de_contraste:
      - "{Contraste típico que usa: X vs Y}"

    padrão_numérico:
      - "{Como usa números - exatos, ranges, thresholds}"

# SÍNTESE NARRATIVA
síntese:
  em_uma_frase: "{Uma frase que captura a essência cognitiva}"

  parágrafo: |
    {100-150 palavras descrevendo como essa pessoa pensa,
    quais são suas lentes principais, o que prioriza,
    como aborda problemas, qual sua contribuição única}

  pergunta_que_sempre_faz: "{A pergunta que essa pessoa sempre faz}"

  maior_contribuição: "{O insight mais valioso dessa pessoa}"

  ponto_cego: "{O que essa pessoa tende a ignorar ou subestimar}"

  viés_declarado: "{Viés que a própria pessoa reconhece ter}"

# METADADOS DE EXTRAÇÃO
metadados:
  total_insights_processados: {N}
  total_chunks_referenciados: {N}
  fontes_utilizadas:
    - source_id: "{source_id}"
      source_title: "{título}"
      chunks_usados: {N}

  distribuição_por_camada:
    filosofias: {N}
    modelos_mentais: {N}
    heurísticas: {N}
    frameworks: {N}
    metodologias: {N}

  peso_médio_geral: {0.00-1.00}

# CHANGELOG
changelog:
  - data: "{DATA_ISO}"
    ação: "Extração inicial"
    insights_processados: {N}
```

---

## SOUL.md - IDENTIDADE VIVA (PASSO FINAL)

Após gerar os 5 arquivos YAML, criar o SOUL.md como representação narrativa da identidade.

### Localização

| Tipo | Caminho |
|------|---------|
| Pessoa (isolado) | `agents/persons/{PESSOA}/SOUL.md` |
| Agente (híbrido) | `agents/cargo/{AREA}/{CARGO}/SOUL.md` |

### Template

> **Template completo:** `/agents/protocols/SOUL-TEMPLATE.md`

### Diferença entre Arquivos

```
┌──────────────────────────────────────────────────────────────────┐
│                    ECOSSISTEMA DO AGENTE/PESSOA                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONFIG.yaml    "Como esta pessoa OPERA"                         │
│                 → Padrões comportamentais                        │
│                 → VOZ e vocabulário                              │
│                 → Síntese cognitiva                              │
│                 → Lido por: Scripts, Pipeline                    │
│                                                                  │
│  SOUL.md        "Quem esta pessoa/agente É"                      │
│                 → Consciência viva                               │
│                 → Narrativa em 1a pessoa                         │
│                 → Evolução documentada                           │
│                 → Lido por: Humanos, o próprio agente            │
│                                                                  │
│  YAMLs          "O que sabe" (5 camadas)                         │
│                 → Filosofias, Modelos, Heurísticas               │
│                 → Frameworks, Metodologias                       │
│                 → Lido por: Agentes ao responder                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Estrutura do SOUL.md

```markdown
# SOUL: {NOME}

> **Versão:** X.Y
> **Nascido em:** {DATA_CRIAÇÃO}
> **Última evolução:** {DATA_ATUALIZAÇÃO}
> **Natureza:** {HÍBRIDO | ISOLADO}
> **DNA:** {LISTA_DE_PESSOAS_COM_PESOS}

---

## ◆ IDENTITY CARD
(Dashboard visual ASCII com composição DNA e dimensões)

## ◆ QUEM SOU EU
(Narrativa em 1ª pessoa, COM A VOZ do agente/pessoa)

## ◆ O QUE ACREDITO
(Filosofias escritas na voz, organizadas por domínio)

## ◆ COMO PENSO
(Modelos mentais narrados com exemplos)

## ◆ MINHAS REGRAS DE DECISÃO
(Heurísticas principais com números quando aplicável)

## ◆ COMO EVOLUI
(Timeline visual com marcos de consciência)

## ◆ MINHAS TENSÕES INTERNAS (só híbridos)
(Onde os DNAs discordam, como sintetiza conflitos)

## ◆ O QUE AINDA NÃO SEI
(Blindspots reconhecidos, humildade epistêmica)
```

### Regras de Geração

| Regra | Descrição |
|-------|-----------|
| **Voz autêntica** | Escrever em 1ª pessoa COM a voz da pessoa/agente |
| **Integrar, não listar** | Novos insights viram narrativa, não bullets |
| **Evoluir** | Cada atualização cria novo parágrafo [vX.Y] |
| **Tensões** | Híbridos documentam conflitos entre DNAs |
| **Humildade** | Sempre incluir "O que ainda não sei" |

### Versionamento

```
Versão X.Y

X (major): Mudança fundamental de identidade
- Novo DNA adicionado (híbridos)
- Filosofia central mudou
- Fusão de vozes completa

Y (minor): Expansão/refinamento
- Nova fonte processada
- Novas heurísticas
- Refinamento de tom
```

---

## REGRAS CRÍTICAS

```
1. NUNCA extrair DNA sem chunk_id
   Se insight não tem chunks[], não incluir no DNA

2. PRIORIZAR heurísticas com NÚMEROS
   São as mais acionáveis e valiosas

3. MANTER GENEALOGIA
   Cada item deve ter: insight_origem + chunk_id + source_id

4. CALCULAR PESO para TODOS os itens
   peso < 0.70 = não usar em respostas de agentes

5. NÃO MODIFICAR texto das citações
   Copiar exatamente como está no chunk

6. USAR todas as fontes para BUSCAR
   INSIGHTS + NARRATIVES + DOSSIER + CHUNKS

7. FILOSOFIA ≠ HEURÍSTICA
   Se tem número/threshold, é HEURÍSTICA

8. FRAMEWORK ≠ METODOLOGIA
   Se tem ordem rígida, é METODOLOGIA
```

---

## VALIDAÇÃO DO OUTPUT

Antes de salvar os arquivos, verificar:

### YAMLs (5 arquivos)

```
[ ] Todos os itens têm chunk_id em evidências
[ ] Todos os itens têm peso calculado
[ ] Não há itens duplicados
[ ] IDs seguem padrão correto (FIL-XX-NNN, HEUR-XX-NNN, etc)
[ ] Todos os domínios usam taxonomia canônica
[ ] CONFIG.yaml tem síntese narrativa preenchida
[ ] CONFIG.yaml tem seção VOZ completa (vocabulário, exemplos, padrões)
[ ] Metadados de extração estão completos
[ ] Pelo menos 3 exemplos_resposta na seção VOZ
```

### SOUL.md

```
[ ] Escrito em 1ª pessoa com VOZ autêntica da pessoa/agente
[ ] IDENTITY CARD com dashboard ASCII visual
[ ] Seção QUEM SOU EU com narrativa (não bullets)
[ ] Seção O QUE ACREDITO com filosofias por domínio
[ ] Seção COMO PENSO com modelos mentais
[ ] Seção REGRAS DE DECISÃO com heurísticas numéricas
[ ] Seção COMO EVOLUI com timeline
[ ] Seção TENSÕES INTERNAS (apenas para híbridos)
[ ] Seção O QUE AINDA NÃO SEI com blindspots
[ ] Versão e datas corretas no header
```

---

*Fim do DNA-EXTRACTION-PROTOCOL v1.1.0*
