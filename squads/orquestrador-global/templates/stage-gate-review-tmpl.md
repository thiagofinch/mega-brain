# Stage Gate Review Template

> Template para apresentacao de entregas ao usuario em cada gate de aprovacao entre stages

## Metadata

```yaml
template:
  id: stage-gate-review
  name: Stage Gate Review
  agent: team-coordinator
  output_format: markdown
  requires_approval: true
```

---

# Stage Gate Review | Stage {{stage_number}} de {{total_stages}}

**Session:** {{session_id}}
**Timestamp:** {{timestamp}}
**Status:** Aguardando Revisao

---

## Progresso Geral

```
{{#each stages}}
[{{#if completed}}X{{else}}{{#if current}}>{{else}} {{/if}}{{/if}}] Stage {{number}}: {{name}} {{#if completed}}OK{{/if}}{{#if current}}<< VOCE ESTA AQUI{{/if}}
{{/each}}
```

### Barra de Progresso
```
Stages concluidos: {{completed_stages}} / {{total_stages}}
Squads executados: {{completed_squads}} / {{total_squads}}
```

---

## Stage {{stage_number}}: {{stage_name}}

### Squads Executados neste Stage

{{#each stage_squads}}
#### Squad {{squad_number}}: {{squad_name}}

| Campo | Valor |
|-------|-------|
| **Status** | {{status}} |
| **Agentes** | {{agents_used}} |
| **Duracao** | {{duration}} |
| **Padrao** | {{pattern_used}} |

**Entregas:**
{{#each deliverables}}
- **{{name}}**: {{description}}
  - Path: `{{path}}`
  - Tamanho: {{size}}
{{/each}}

**Decisoes Tomadas:**
{{#each decisions}}
- {{decision}}: {{rationale}}
{{/each}}

{{#if issues}}
**Problemas Encontrados:**
{{#each issues}}
- {{issue}}: {{resolution}}
{{/each}}
{{/if}}

---
{{/each}}

## Criterios de Aceite do Stage

{{#each acceptance_criteria}}
- [{{#if met}}x{{else}} {{/if}}] {{criterion}}
{{/each}}

---

## Contexto Acumulado

### Resumo dos Stages Anteriores

{{#each previous_stages}}
**Stage {{number}} ({{name}}):** {{summary}}
{{/each}}

### Dados Disponiveis para Proximo Stage

| Dado | Origem | Path |
|------|--------|------|
{{#each available_data}}
| {{name}} | Stage {{source_stage}} / {{source_squad}} | `{{path}}` |
{{/each}}

---

## Preview: Proximo Stage

{{#if has_next_stage}}

### Stage {{next_stage_number}}: {{next_stage_name}}

| Squad | Papel | Inputs que recebera |
|-------|-------|---------------------|
{{#each next_stage_squads}}
| {{name}} | {{role}} | {{inputs}} |
{{/each}}

**Dependencias do stage atual:**
{{#each next_stage_dependencies}}
- {{dependency}}
{{/each}}

{{else}}

> Este e o **stage final**. Apos aprovacao, a consolidacao final sera gerada.

{{/if}}

---

## Decisao

### Opcoes

{{#if has_next_stage}}
**1. Aprovar e Avancar**
> Aprovar entregas deste stage e iniciar Stage {{next_stage_number}}: {{next_stage_name}}.
> Todos os outputs serao passados como contexto para o proximo stage.
{{else}}
**1. Aprovar e Consolidar**
> Aprovar entregas deste stage final e gerar consolidacao de toda a execucao.
> Relatorio final sera gerado com entregas de todos os stages.
{{/if}}

**2. Solicitar Revisoes**
> Solicitar que um ou mais squads deste stage refacam ou ajustem entregas.
> Especificar: qual squad, o que revisar, criterio de aceite.
```
Formato: "Revisar [squad]: [o que ajustar]"
Exemplo: "Revisar copywriting: headlines precisam ser mais urgentes"
```

**3. Modificar Plano Restante**
> Alterar a composicao ou ordem dos stages seguintes.
> Opcoes: adicionar squad, remover squad, reordenar stages, mover squad entre stages.
```
Formato: "Modificar: [mudanca desejada]"
Exemplo: "Modificar: adicionar design-system ao stage 3"
```

**4. Pausar Execucao**
> Pausar a execucao. Todo progresso sera salvo.
> Pode retomar depois com `*execute-team --resume {session_id}`.
```
Estado salvo em: .data/team-outputs/{session_id}/
```

**5. Cancelar Execucao**
> Cancelar execucao restante. Outputs dos stages ja concluidos sao mantidos.
> Nenhum squad adicional sera executado.

---

### Responda com o numero da opcao (1-5) ou descreva o que deseja:

> Aguardando decisao do usuario...

---

**Stage {{stage_number}} de {{total_stages}}** | **Gerado por:** Team Coordinator v{{version}}
