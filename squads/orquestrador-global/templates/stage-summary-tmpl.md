# Stage Summary Template

> Template para resumo de entregas ao final de cada stage, antes de apresentar o gate ao usuario

## Metadata

```yaml
template:
  id: stage-summary
  name: Stage Summary
  agent: team-coordinator
  output_format: markdown
  requires_approval: false
```

---

# Stage {{stage_number}} Summary: {{stage_name}}

**Session:** {{session_id}}
**Timestamp:** {{timestamp}}
**Status:** {{stage_status}}

---

## Squads Executados

{{#each squads}}
### {{squad_number}}. {{squad_name}}

| Campo | Valor |
|-------|-------|
| **Status** | {{status}} |
| **Agentes Utilizados** | {{agents_count}} ({{agents_list}}) |
| **Padrao** | {{pattern}} |
| **Duracao** | {{duration}} |
| **Inicio** | {{start_time}} |
| **Fim** | {{end_time}} |

#### Entregas

| Arquivo | Descricao | Tamanho |
|---------|-----------|---------|
{{#each deliverables}}
| `{{path}}` | {{description}} | {{size}} |
{{/each}}

#### Decisoes Tomadas
{{#each decisions}}
- **{{decision}}**: {{rationale}}
{{/each}}

{{#if issues}}
#### Problemas Encontrados
{{#each issues}}
- **{{issue}}**: {{resolution}} ({{severity}})
{{/each}}
{{/if}}

#### Autoavaliacao
- **Qualidade:** {{quality_score}}/5
- **Completude:** {{completeness_score}}/5
- **Notas:** {{quality_notes}}

---
{{/each}}

## Resumo Consolidado do Stage

### Entregas Principais
{{#each key_deliverables}}
- {{deliverable}} (de {{source_squad}})
{{/each}}

### Dados Gerados para Proximos Stages

| Dado | Tipo | Squad de Origem | Path |
|------|------|-----------------|------|
{{#each outputs_for_next}}
| {{name}} | {{type}} | {{source_squad}} | `{{path}}` |
{{/each}}

### Criterios de Aceite do Stage

{{#each acceptance_criteria}}
- [{{#if met}}x{{else}} {{/if}}] {{criterion}}
{{/each}}

### Metricas

| Metrica | Valor |
|---------|-------|
| **Squads executados** | {{squads_completed}} / {{squads_total}} |
| **Duracao total do stage** | {{stage_duration}} |
| **Qualidade media** | {{avg_quality}}/5 |
| **Problemas encontrados** | {{issues_count}} |
| **Problemas resolvidos** | {{issues_resolved}} |

---

## Contexto Acumulado

### Stages Anteriores Concluidos
{{#each previous_stages}}
- **Stage {{number}} ({{name}}):** {{status}} — {{summary}}
{{/each}}

### Total Acumulado
- **Stages concluidos:** {{completed_stages}} de {{total_stages}}
- **Squads executados:** {{completed_squads}} de {{total_squads}}
- **Tempo total acumulado:** {{cumulative_duration}}

---

**Proximo passo:** Apresentar gate de aprovacao ao usuario (template: stage-gate-review-tmpl)

**Gerado por:** Team Coordinator v{{version}} | **Timestamp:** {{timestamp}}
