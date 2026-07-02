# Team Context Handoff

> Template para passagem de contexto entre squads em execução multi-squad

## Metadata

```yaml
template:
  id: team-context-handoff
  name: Team Context Handoff
  agent: team-coordinator
  output_format: markdown
```

---

# Context Handoff | {{session_id}}

**From Squad:** {{prev_squad_name}} (Squad {{prev_squad_number}})
**To Squad:** {{next_squad_name}} (Squad {{next_squad_number}})
**Timestamp:** {{timestamp}}

---

## Demanda Original

```
{{original_demand}}
```

---

## Outputs do Squad Anterior

### Arquivos Gerados
| # | Arquivo | Tipo | Descrição |
|---|---------|------|-----------|
{{#each files}}
| {{index}} | {{filename}} | {{type}} | {{description}} |
{{/each}}

### Decisões Tomadas
{{#each decisions}}
- **{{topic}}:** {{decision}} (Motivo: {{reason}})
{{/each}}

### Resultados Principais
```
{{key_results}}
```

---

## Contexto Acumulado

### De Squads Anteriores
{{#each previous_contexts}}
#### Squad {{number}}: {{name}}
- **Entregou:** {{deliverables}}
- **Decisões-chave:** {{key_decisions}}
{{/each}}

### Dados Disponíveis
| Dado | Localização | Formato |
|------|-------------|---------|
{{#each available_data}}
| {{name}} | {{path}} | {{format}} |
{{/each}}

---

## Briefing para Próximo Squad

### Objetivo
{{next_squad_objective}}

### Contexto Relevante
{{relevant_context}}

### Restrições
{{#each constraints}}
- {{this}}
{{/each}}

### Entregáveis Esperados
{{#each expected_deliverables}}
- {{this}}
{{/each}}

---

## Estado da Execução

| Campo | Valor |
|-------|-------|
| **Squads Completados** | {{completed_count}}/{{total_count}} |
| **Tempo Decorrido** | {{elapsed_time}} |
| **Erros Encontrados** | {{error_count}} |
| **Status Geral** | {{overall_status}} |

---

**Gerado por:** Team Coordinator v1.0.0
**Timestamp:** {{timestamp}}
