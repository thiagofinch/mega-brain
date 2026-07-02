# Intent Classification Template

> Template para classificação estruturada de intenções do usuário

## Metadata

```yaml
template:
  id: intent-classification
  name: Intent Classification
  agent: classificador-intencao
  output_format: yaml
```

---

# Intent Classification | {{classification_id}}

**Input ID:** {{input_id}}
**Timestamp:** {{timestamp}}
**Versão do Classificador:** {{classifier_version}}

---

## Input Original

### Texto do Usuário

```
{{user_input}}
```

### Contexto Adicional

| Campo | Valor |
|-------|-------|
| **Canal** | {{channel}} |
| **Sessão** | {{session_id}} |
| **Histórico** | {{history_context}} |
| **Idioma detectado** | {{language}} |

---

## Pré-processamento

### Normalização

| Etapa | Input | Output |
|-------|-------|--------|
| Lowercase | {{original}} | {{lowercase}} |
| Remove noise | {{lowercase}} | {{cleaned}} |
| Tokenization | {{cleaned}} | {{tokens}} |

### Correções Aplicadas

| Tipo | Original | Corrigido |
|------|----------|-----------|
| {{correction_1_type}} | {{correction_1_orig}} | {{correction_1_fixed}} |
| {{correction_2_type}} | {{correction_2_orig}} | {{correction_2_fixed}} |

---

## Classificação Estruturada

### Intent Object

```yaml
intent:
  # Identificação
  id: {{intent_id}}
  timestamp: {{timestamp}}

  # Intenção Principal
  primary:
    category: {{primary_category}}
    action: {{primary_action}}
    confidence: {{primary_confidence}}

  # Intenção Secundária (se houver)
  secondary:
    category: {{secondary_category}}
    action: {{secondary_action}}
    confidence: {{secondary_confidence}}

  # Domínio
  domain:
    name: {{domain_name}}
    subdomain: {{subdomain}}
    confidence: {{domain_confidence}}

  # Tipo de Ação
  action_type: {{action_type}}  # create | read | update | delete | analyze | generate

  # Entidades Extraídas
  entities:
    - type: {{entity_1_type}}
      value: "{{entity_1_value}}"
      start: {{entity_1_start}}
      end: {{entity_1_end}}
      confidence: {{entity_1_conf}}
    - type: {{entity_2_type}}
      value: "{{entity_2_value}}"
      start: {{entity_2_start}}
      end: {{entity_2_end}}
      confidence: {{entity_2_conf}}

  # Atributos Contextuais
  context:
    urgency: {{urgency}}           # low | medium | high | critical
    complexity: {{complexity}}      # simple | moderate | complex
    specificity: {{specificity}}    # vague | partial | specific
    sentiment: {{sentiment}}        # positive | neutral | negative
    formality: {{formality}}        # informal | neutral | formal

  # Metadados
  metadata:
    token_count: {{token_count}}
    language: {{language}}
    classifier_version: {{classifier_version}}
    processing_time_ms: {{processing_time}}
```

---

## Análise de Confiança

### Scores por Componente

| Componente | Score | Threshold | Status |
|------------|-------|-----------|--------|
| **Intenção primária** | {{conf_primary}}% | 70% | {{status_primary}} |
| **Domínio** | {{conf_domain}}% | 70% | {{status_domain}} |
| **Entidades** | {{conf_entities}}% | 60% | {{status_entities}} |
| **Contexto** | {{conf_context}}% | 50% | {{status_context}} |
| **Overall** | {{conf_overall}}% | 65% | {{status_overall}} |

### Confidence Breakdown

```
Primary Intent:  [{{bar_primary}}] {{conf_primary}}%
Domain:          [{{bar_domain}}] {{conf_domain}}%
Entities:        [{{bar_entities}}] {{conf_entities}}%
Context:         [{{bar_context}}] {{conf_context}}%
─────────────────────────────────────────────
OVERALL:         [{{bar_overall}}] {{conf_overall}}%
```

---

## Taxonomia de Intenções

### Categorias de Primeiro Nível

| Categoria | Descrição | Match |
|-----------|-----------|-------|
| `create` | Criar algo novo | {{match_create}} |
| `analyze` | Analisar dados/conteúdo | {{match_analyze}} |
| `generate` | Gerar conteúdo | {{match_generate}} |
| `query` | Buscar informação | {{match_query}} |
| `modify` | Alterar existente | {{match_modify}} |
| `delete` | Remover algo | {{match_delete}} |
| `help` | Pedir ajuda/orientação | {{match_help}} |
| `config` | Configurar sistema | {{match_config}} |

### Subcategorias Detectadas

| Subcategoria | Score | Relevância |
|--------------|-------|------------|
| {{subcat_1}} | {{subcat_1_score}} | {{subcat_1_rel}} |
| {{subcat_2}} | {{subcat_2_score}} | {{subcat_2_rel}} |
| {{subcat_3}} | {{subcat_3_score}} | {{subcat_3_rel}} |

---

## Entidades Detalhadas

### Entidade 1: {{entity_1_type}}

| Campo | Valor |
|-------|-------|
| **Valor** | {{entity_1_value}} |
| **Tipo** | {{entity_1_type}} |
| **Normalizado** | {{entity_1_normalized}} |
| **Posição** | {{entity_1_start}}-{{entity_1_end}} |
| **Confiança** | {{entity_1_conf}}% |
| **Contexto** | "...{{entity_1_context}}..." |

### Entidade 2: {{entity_2_type}}

| Campo | Valor |
|-------|-------|
| **Valor** | {{entity_2_value}} |
| **Tipo** | {{entity_2_type}} |
| **Normalizado** | {{entity_2_normalized}} |
| **Posição** | {{entity_2_start}}-{{entity_2_end}} |
| **Confiança** | {{entity_2_conf}}% |

### Tipos de Entidades Suportadas

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `squad_name` | Nome de squad | "copywriting" |
| `agent_name` | Nome de agente | "@jon-benson" |
| `command` | Comando do sistema | "*vsl" |
| `content_type` | Tipo de conteúdo | "email", "vsl" |
| `platform` | Plataforma | "instagram", "youtube" |
| `person` | Nome de pessoa | "um cliente" |
| `date` | Data/período | "amanhã", "Q1" |
| `product` | Produto/serviço | "Manual PG" |
| `metric` | Métrica de negócio | "conversão", "CPA" |

---

## Slots Identificados

### Template Matching

```yaml
template: "{{slot_template}}"
slots:
  - name: {{slot_1_name}}
    value: {{slot_1_value}}
    required: {{slot_1_required}}
    filled: {{slot_1_filled}}
  - name: {{slot_2_name}}
    value: {{slot_2_value}}
    required: {{slot_2_required}}
    filled: {{slot_2_filled}}
```

### Slots Faltantes

| Slot | Obrigatório | Sugestão de Pergunta |
|------|-------------|----------------------|
| {{missing_1}} | {{missing_1_req}} | "{{missing_1_question}}" |
| {{missing_2}} | {{missing_2_req}} | "{{missing_2_question}}" |

---

## Ambiguidades Detectadas

### Interpretações Alternativas

| # | Interpretação | Confiança | Diferença |
|---|---------------|-----------|-----------|
| 1 | {{interp_1}} | {{interp_1_conf}}% | (principal) |
| 2 | {{interp_2}} | {{interp_2_conf}}% | -{{interp_diff_2}}% |
| 3 | {{interp_3}} | {{interp_3_conf}}% | -{{interp_diff_3}}% |

### Recomendação

```
{{ambiguity_recommendation}}
```

---

## Mapeamento para Squads

### Squad Hints

```yaml
routing_hints:
  suggested_squads:
    - squad: {{hint_squad_1}}
      confidence: {{hint_conf_1}}
      reason: {{hint_reason_1}}
    - squad: {{hint_squad_2}}
      confidence: {{hint_conf_2}}
      reason: {{hint_reason_2}}

  keywords_matched:
    - {{keyword_1}}
    - {{keyword_2}}
    - {{keyword_3}}

  domain_match: {{domain_match}}
  task_type_match: {{task_type_match}}
```

---

## Output para Roteador

### Payload de Classificação

```json
{
  "classification_id": "{{classification_id}}",
  "intent": {
    "primary": "{{primary_action}}",
    "domain": "{{domain_name}}",
    "action_type": "{{action_type}}"
  },
  "entities": {{entities_json}},
  "context": {
    "urgency": "{{urgency}}",
    "complexity": "{{complexity}}"
  },
  "confidence": {{conf_overall}},
  "routing_hints": {
    "suggested_squads": [{{suggested_squads}}],
    "keywords": [{{keywords_list}}]
  },
  "requires_clarification": {{requires_clarification}},
  "clarification_questions": [{{clarification_questions}}]
}
```

---

## Métricas de Processamento

| Métrica | Valor |
|---------|-------|
| **Tempo de pré-processamento** | {{time_preprocess}}ms |
| **Tempo de classificação** | {{time_classify}}ms |
| **Tempo de extração de entidades** | {{time_entities}}ms |
| **Tempo total** | {{time_total}}ms |

---

**Classificado por:** Classificador de Intenção v{{classifier_version}}
**Timestamp:** {{timestamp}}
