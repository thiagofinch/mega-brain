# SKILL-KNOWLEDGE-EXTRACTION
## Padrões para Extração de Conhecimento no Mega Brain

> **Auto-Trigger:** Processamento de conteúdo, extração de insights
> **Keywords:** "extrair", "processar", "insight", "chunk", "conhecimento"
> **Prioridade:** ALTA

---

## PROPÓSITO

Garantir que toda extração de conhecimento siga:
- Taxonomia DNA Cognitivo
- Rastreabilidade completa
- Qualidade consistente
- Integração com o sistema

---

## QUANDO USAR

### ✅ USAR quando:
- Processar vídeos, PDFs, transcrições
- Extrair insights de materiais
- Categorizar conhecimento
- Alimentar RAG

### ❌ NÃO USAR quando:
- Consultas (leitura apenas)
- Criação de playbooks (output, não extração)
- Documentação interna do sistema

---

## TAXONOMIA DNA COGNITIVO

### As 5 Camadas

| Tag | Camada | Descrição | Exemplo |
|-----|--------|-----------|---------|
| `[FILOSOFIA]` | Filosofia | Crenças fundamentais, valores | "Vendas é transferência de certeza" |
| `[MODELO-MENTAL]` | Modelo Mental | Formas de entender realidade | "Gap Analysis" |
| `[HEURISTICA]` | Heurística | Atalhos de decisão | "Se show rate < 70%, problema é qualificação" |
| `[FRAMEWORK]` | Framework | Estruturas de análise | "CLOSER Framework de 6 passos" |
| `[METODOLOGIA]` | Metodologia | Processos passo-a-passo | "Script de fechamento em 12 etapas" |

### Hierarquia de Abstração

```
FILOSOFIA (mais abstrato)
    ↓
MODELO MENTAL
    ↓
HEURÍSTICA
    ↓
FRAMEWORK
    ↓
METODOLOGIA (mais concreto)
```

### Critérios de Classificação

**FILOSOFIA:**
- Responde "Por que isso importa?"
- Não muda com contexto
- É uma crença/valor, não instrução

**MODELO MENTAL:**
- Responde "Como pensar sobre isso?"
- Framework de pensamento, não ação
- Ajuda a entender, não fazer

**HEURÍSTICA:**
- Responde "O que fazer em situação X?"
- Regra de bolso, atalho
- IF/THEN implícito

**FRAMEWORK:**
- Responde "Quais são os componentes?"
- Estrutura organizada
- Pode ser diagrama/lista

**METODOLOGIA:**
- Responde "Qual o passo a passo?"
- Sequência de ações
- Replicável

---

## ESTRUTURA DE INSIGHT

```json
{
  "id": "CG003-INS-042",
  "chunk_id": "CG003-CHK-015",
  "source_id": "CG003",
  "timestamp": "00:45:30",
  
  "content": "O insight extraído, em linguagem clara",
  
  "dna_layer": "[FRAMEWORK]",
  "confidence": 0.92,
  "priority": "HIGH",
  
  "themes": ["02-PROCESSO-VENDAS", "05-METRICAS"],
  
  "related_entities": {
    "persons": ["Cole Gordon"],
    "concepts": ["Show Rate", "Qualificação"],
    "frameworks": ["CLOSER Framework"]
  },
  
  "context": "Dito ao explicar por que times falham...",
  
  "verbatim_quote": "A frase exata se relevante",
  
  "actionable": true,
  "requires_validation": false
}
```

---

## REGRAS DE EXTRAÇÃO

### 1. Granularidade

| Tipo | Tamanho | Quando usar |
|------|---------|-------------|
| Micro-insight | 1-2 frases | Heurísticas, quotes |
| Insight padrão | 3-5 frases | Explicações, conceitos |
| Insight expandido | 1-2 parágrafos | Frameworks completos |

### 2. Threshold de Qualidade

| Critério | Mínimo | Ideal |
|----------|--------|-------|
| Confidence | 0.70 | 0.85+ |
| Clareza | Entendível | Acionável |
| Fonte | Identificável | Com timestamp |

### 3. Priorização

```
HIGH   → Insight acionável, específico, com métrica
MEDIUM → Insight conceitual, útil para contexto
LOW    → Insight complementar, nice-to-have
```

### 4. Deduplicação

Antes de registrar, verificar:
- [ ] CANONICAL-MAP.json para conceito existente
- [ ] Glossário para termo equivalente
- [ ] RAG para insight similar (>85% similaridade)

---

## FORMATO DE CHUNK

```markdown
## CHUNK: [SOURCE_ID]-CHK-[XXX]

**Timestamp:** [HH:MM:SS - HH:MM:SS]
**Speaker:** [Nome se identificável]
**Confiança transcrição:** [0.XX]

---

### Conteúdo

[Texto do chunk - mínimo 200, máximo 1000 caracteres]

---

### Insights Extraídos

1. **[ID-INS-001]** `[DNA-TAG]`
   [Insight em linguagem clara]
   
2. **[ID-INS-002]** `[DNA-TAG]`
   [Insight em linguagem clara]

---

### Entidades

- **Pessoas:** [Lista]
- **Conceitos:** [Lista]
- **Métricas:** [Lista]

---

### Conexões

- Relacionado a: [IDs de outros chunks]
- Complementa: [IDs de insights existentes]
- Contradiz: [Se houver contradição]
```

---

## PROCESSO DE EXTRAÇÃO

### Fase 1: Segmentação
```
1. Identificar breaks naturais (pausas, mudança de tema)
2. Criar chunks de 200-1000 caracteres
3. Manter contexto suficiente em cada chunk
4. Registrar timestamps
```

### Fase 2: Classificação
```
1. Para cada chunk, identificar:
   - Quem está falando
   - Tema principal
   - Se contém insight acionável
   
2. Aplicar tag DNA apropriada
3. Definir prioridade
```

### Fase 3: Extração
```
1. Extrair insight em linguagem clara
2. Preservar quote verbatim se relevante
3. Identificar entidades mencionadas
4. Mapear para taxonomia existente
```

### Fase 4: Validação
```
1. Verificar duplicatas
2. Resolver conflitos com conhecimento existente
3. Atribuir confidence score
4. Conectar com insights relacionados
```

### Fase 5: Registro
```
1. Salvar em formato JSON estruturado
2. Indexar no RAG
3. Atualizar CANONICAL-MAP se novo conceito
4. Registrar em SESSION-STATE
```

---

## TRATAMENTO DE CONFLITOS

Quando novo insight contradiz existente:

```markdown
## CONFLITO DETECTADO

**Insight Existente:** [ID]
[Conteúdo do insight existente]
**Fonte:** [ID] | **Data:** [Data]

**Novo Insight:** [ID]
[Conteúdo do novo insight]
**Fonte:** [ID] | **Data:** [Data]

---

### Análise

| Aspecto | Existente | Novo |
|---------|-----------|------|
| Confiança | X.XX | X.XX |
| Especificidade | [Alta/Média/Baixa] | [Alta/Média/Baixa] |
| Recência | [Data] | [Data] |

### Resolução

[ ] Manter existente (novo é menos confiável)
[ ] Substituir por novo (mais recente/confiável)
[ ] Manter ambos (contextos diferentes)
[ ] Criar síntese (complementares)

**Decisão:** [Explicação]
```

---

## ANTI-PATTERNS (NUNCA FAZER)

1. ❌ Extrair sem verificar duplicatas
2. ❌ Insight sem source_id
3. ❌ Classificar DNA sem critério claro
4. ❌ Chunks muito grandes (>1000 chars)
5. ❌ Perder contexto ao segmentar
6. ❌ Ignorar contradições
7. ❌ Confidence arbitrário
8. ❌ Traduzir/interpretar em vez de extrair

---

## CHECKLIST PÓS-EXTRAÇÃO

- [ ] Todos insights têm source_id
- [ ] Tags DNA aplicadas corretamente
- [ ] Duplicatas verificadas
- [ ] Entidades mapeadas
- [ ] Confidence scores atribuídos
- [ ] Indexado no RAG
- [ ] SESSION-STATE atualizado
- [ ] CANONICAL-MAP atualizado (se novos conceitos)

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Domínio:** Processamento
- **Prioridade:** ALTA
- **Dependências:** SKILL-DOCS-MEGABRAIN
