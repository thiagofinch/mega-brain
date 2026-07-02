# Squad Capability Index Template

> Template para indexar capacidades de um squad no SQUAD-REGISTRY

## Metadata

```yaml
template:
  id: squad-capability-index
  name: Squad Capability Index
  agent: indexador-squads
  output_format: yaml
```

---

# Squad Index Entry | {{squad_id}}

**Indexado em:** {{indexed_at}}
**Última atualização:** {{last_updated}}
**Indexador version:** {{indexer_version}}

---

## Identificação

```yaml
squad:
  id: {{squad_id}}
  name: {{squad_name}}
  version: {{squad_version}}
  status: {{status}}  # active | inactive | deprecated
  type: {{squad_type}}  # persona | functional | hybrid | infrastructure
  path: {{squad_path}}
```

---

## Domínio

```yaml
domain:
  primary: {{primary_domain}}
  secondary:
    - {{secondary_1}}
    - {{secondary_2}}

  scope: {{scope}}  # narrow | moderate | broad

  keywords:
    - {{keyword_1}}
    - {{keyword_2}}
    - {{keyword_3}}
    - {{keyword_4}}
    - {{keyword_5}}
```

---

## Problemas Resolvidos

```yaml
problems_solved:
  - id: P1
    description: "{{problem_1}}"
    keywords: [{{p1_keywords}}]
    priority: {{p1_priority}}

  - id: P2
    description: "{{problem_2}}"
    keywords: [{{p2_keywords}}]
    priority: {{p2_priority}}

  - id: P3
    description: "{{problem_3}}"
    keywords: [{{p3_keywords}}]
    priority: {{p3_priority}}
```

---

## Capacidades

### Capabilities Matrix

```yaml
capabilities:
  # Capacidades de criação
  create:
    - type: {{create_1_type}}
      description: "{{create_1_desc}}"
      agent: {{create_1_agent}}
      command: "{{create_1_cmd}}"
    - type: {{create_2_type}}
      description: "{{create_2_desc}}"
      agent: {{create_2_agent}}
      command: "{{create_2_cmd}}"

  # Capacidades de análise
  analyze:
    - type: {{analyze_1_type}}
      description: "{{analyze_1_desc}}"
      agent: {{analyze_1_agent}}
      command: "{{analyze_1_cmd}}"

  # Capacidades de geração
  generate:
    - type: {{generate_1_type}}
      description: "{{generate_1_desc}}"
      agent: {{generate_1_agent}}
      command: "{{generate_1_cmd}}"

  # Capacidades de otimização
  optimize:
    - type: {{optimize_1_type}}
      description: "{{optimize_1_desc}}"
      agent: {{optimize_1_agent}}
      command: "{{optimize_1_cmd}}"
```

---

## Agentes

```yaml
agents:
  chief:
    id: {{chief_id}}
    role: {{chief_role}}
    entry_point: true
    commands:
      - {{chief_cmd_1}}
      - {{chief_cmd_2}}

  specialists:
    - id: {{spec_1_id}}
      role: {{spec_1_role}}
      expertise:
        - {{spec_1_exp_1}}
        - {{spec_1_exp_2}}
      frameworks:
        - {{spec_1_fw_1}}
      best_for:
        - {{spec_1_best_1}}
        - {{spec_1_best_2}}
      commands:
        - {{spec_1_cmd_1}}

    - id: {{spec_2_id}}
      role: {{spec_2_role}}
      expertise:
        - {{spec_2_exp_1}}
        - {{spec_2_exp_2}}
      frameworks:
        - {{spec_2_fw_1}}
      best_for:
        - {{spec_2_best_1}}
      commands:
        - {{spec_2_cmd_1}}

  total_count: {{total_agents}}
```

---

## Comandos

```yaml
commands:
  global:
    - command: "*{{global_cmd_1}}"
      description: "{{global_cmd_1_desc}}"
      routes_to: {{global_cmd_1_agent}}
    - command: "*{{global_cmd_2}}"
      description: "{{global_cmd_2_desc}}"
      routes_to: {{global_cmd_2_agent}}

  activation:
    prefix: "@{{activation_prefix}}"
    aliases:
      - "@{{alias_1}}"
      - "@{{alias_2}}"
```

---

## Workflows

```yaml
workflows:
  - id: {{wf_1_id}}
    name: {{wf_1_name}}
    trigger: {{wf_1_trigger}}
    stages: {{wf_1_stages}}
    agents_involved:
      - {{wf_1_agent_1}}
      - {{wf_1_agent_2}}
    outputs:
      - {{wf_1_output_1}}

  - id: {{wf_2_id}}
    name: {{wf_2_name}}
    trigger: {{wf_2_trigger}}
    stages: {{wf_2_stages}}
    agents_involved:
      - {{wf_2_agent_1}}
    outputs:
      - {{wf_2_output_1}}
```

---

## Templates

```yaml
templates:
  - id: {{tmpl_1_id}}
    name: {{tmpl_1_name}}
    agent: {{tmpl_1_agent}}
    use_case: "{{tmpl_1_use}}"

  - id: {{tmpl_2_id}}
    name: {{tmpl_2_name}}
    agent: {{tmpl_2_agent}}
    use_case: "{{tmpl_2_use}}"

  total_count: {{total_templates}}
```

---

## Integrações

```yaml
integrations:
  internal_squads:
    upstream:
      - squad: {{upstream_1}}
        relationship: {{upstream_1_rel}}
      - squad: {{upstream_2}}
        relationship: {{upstream_2_rel}}

    downstream:
      - squad: {{downstream_1}}
        relationship: {{downstream_1_rel}}

  external_services:
    - service: {{ext_1_service}}
      type: {{ext_1_type}}
      purpose: {{ext_1_purpose}}
```

---

## Routing Metadata

### Para Matching de Intenções

```yaml
routing:
  # Triggers de alta confiança
  high_confidence_triggers:
    - "{{trigger_1}}"
    - "{{trigger_2}}"
    - "{{trigger_3}}"

  # Frases de exemplo que devem rotear para este squad
  example_phrases:
    - "{{phrase_1}}"
    - "{{phrase_2}}"
    - "{{phrase_3}}"

  # Padrões regex
  patterns:
    - pattern: "{{regex_1}}"
      confidence_boost: {{boost_1}}
    - pattern: "{{regex_2}}"
      confidence_boost: {{boost_2}}

  # Exclusões (não rotear mesmo se match)
  exclusions:
    - "{{exclusion_1}}"
    - "{{exclusion_2}}"

  # Peso base para scoring
  base_weight: {{base_weight}}

  # Tipos de task suportados
  supported_task_types:
    - {{task_type_1}}
    - {{task_type_2}}
    - {{task_type_3}}
```

---

## Quality Signals

```yaml
quality:
  # Métricas históricas
  metrics:
    success_rate: {{success_rate}}%
    avg_latency: {{avg_latency}}ms
    satisfaction_score: {{satisfaction}}
    usage_count_30d: {{usage_30d}}

  # Documentação
  documentation:
    readme: {{has_readme}}
    agent_docs: {{agent_docs_count}}
    templates: {{templates_count}}
    workflows: {{workflows_count}}

  # Completude
  completeness_score: {{completeness}}%

  # Última atividade
  last_used: {{last_used}}
  last_modified: {{last_modified}}
```

---

## Indexação Automática

### Campos Extraídos Automaticamente

| Campo | Fonte | Valor |
|-------|-------|-------|
| **ID** | config.yaml → name | {{squad_id}} |
| **Domínio** | config.yaml → domain | {{primary_domain}} |
| **Agentes** | agents/*.md | {{total_agents}} |
| **Workflows** | workflows/*.md | {{total_workflows}} |
| **Templates** | templates/*.md | {{total_templates}} |
| **Keywords** | README.md + config.yaml | {{keywords_count}} |

### Validação

| Check | Status | Detalhes |
|-------|--------|----------|
| Estrutura válida | {{check_structure}} | {{detail_structure}} |
| Chief definido | {{check_chief}} | {{detail_chief}} |
| Domínio preenchido | {{check_domain}} | {{detail_domain}} |
| Keywords suficientes | {{check_keywords}} | {{detail_keywords}} |
| Problemas definidos | {{check_problems}} | {{detail_problems}} |

---

## Registry Entry (Final)

```yaml
# Entry para SQUAD-REGISTRY.yaml
{{squad_id}}:
  name: {{squad_name}}
  version: {{squad_version}}
  domain: {{primary_domain}}
  type: {{squad_type}}
  status: {{status}}

  chief: {{chief_id}}
  agents: {{total_agents}}

  expertise:
    - {{expertise_1}}
    - {{expertise_2}}
    - {{expertise_3}}

  keywords:
    - {{keyword_1}}
    - {{keyword_2}}
    - {{keyword_3}}

  entry_command: "@{{activation_prefix}}"

  routing:
    triggers: [{{trigger_1}}, {{trigger_2}}]
    task_types: [{{task_type_1}}, {{task_type_2}}]
    base_weight: {{base_weight}}

  quality:
    success_rate: {{success_rate}}
    completeness: {{completeness}}
    last_updated: {{last_updated}}
```

---

**Indexado por:** Indexador de Squads v{{indexer_version}}
**Hash de verificação:** {{verification_hash}}
**Próxima reindexação:** {{next_reindex}}
