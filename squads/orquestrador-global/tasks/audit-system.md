---
task: audit-system
name: audit-system
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@capability-cartographer'
responsavel_type: Agent
atomic_layer: Molecule
elicit: false
estimated_time: 30-60min
model: sonnet
Entrada:
- campo: brief
  tipo: markdown
  obrigatorio: true
  default: null
Saida:
- campo: deliverable
  tipo: markdown
pre_condition: Squad ecosystem accessible (squads/, ecosystem-registry.yaml available)
post_condition: Audit report generated with inventory, gaps, routing metrics, quality scores, and prioritized action plan
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: audit-system
squad: orquestrador-global
status: ready
execution_type: hybrid
orchestration_boundary:
  live_routing_performed: false
  external_dispatch_performed: false
  workspace_write_performed: false
megabrain_validation:
  last_run: "20260514-validate-deep"
  validated_at: "2026-05-15T00:00:00Z"
  validator: mega-brain/megabrain-chief
  mode: deep
  squad: orquestrador-global
  status: pass
  evidence:
    - schema_contract_normalized
    - task_boundary_declared
    - plan_only_orchestration_preserved
---

# audit-system

**Task ID:** audit-system
**Squad:** orquestrador-global
**Type:** audit
**Complexity:** medium
**Estimated Tokens:** 1500-2000

---

## Objetivo

Realizar auditoria completa do ecossistema de squads, identificando gaps de capacidade, problemas de qualidade, e oportunidades de melhoria.

---

## Trigger Phrases

- "auditar sistema"
- "status do ecossistema"
- "saúde dos squads"
- "diagnóstico do sistema"
- "gaps de capacidade"

---

## Agents Envolvidos

| Agent | Role | Contribuição |
|-------|------|--------------|
| supervisor-sistema | Lead | Monitoramento e diagnóstico |
| indexador-squads | Dados | Inventário de squads |
| roteador | Análise | Dados de roteamento |

---

## Input Obrigatório

```yaml
audit_input:
  escopo:
    tipo: "completo | squads | routing | quality"
    periodo: "últimos 30 dias (para métricas)"

  foco:
    areas: ["todas" | lista específica]
```

---

## Framework de Auditoria

### FASE 1: Inventário (@indexador-squads)

```markdown
## 1. Inventário do Ecossistema

### Totais
| Métrica | Quantidade |
|---------|------------|
| Squads | X |
| Agentes | X |
| Tasks | X |
| Workflows | X |
| Checklists | X |
| Templates | X |

### Squads por Domínio
| Domínio | Squads | Agentes | Tasks |
|---------|--------|---------|-------|
| Marketing | X | Y | Z |
| Desenvolvimento | X | Y | Z |
| Vendas | X | Y | Z |
| Operações | X | Y | Z |
| Estratégia | X | Y | Z |

### Top 5 Squads (por completude)
| Squad | Agentes | Tasks | Workflows | Score |
|-------|---------|-------|-----------|-------|
| [squad 1] | X | Y | Z | W% |
| [squad 2] | X | Y | Z | W% |
| [squad 3] | X | Y | Z | W% |
| [squad 4] | X | Y | Z | W% |
| [squad 5] | X | Y | Z | W% |
```

### FASE 2: Análise de Gaps (@supervisor-sistema)

```markdown
## 2. Gaps Identificados

### Gaps de Capacidade
| Gap | Descrição | Impacto | Solução |
|-----|-----------|---------|---------|
| [gap 1] | [descrição] | Alto/Médio/Baixo | Criar squad / Expandir existente |
| [gap 2] | [descrição] | Alto/Médio/Baixo | [solução] |

### Solicitações Não Atendidas (últimos 30 dias)
| Tipo de Solicitação | Frequência | Status |
|--------------------|------------|--------|
| [tipo 1] | X vezes | Sem squad |
| [tipo 2] | X vezes | Parcial |

### Domínios Descobertos
- [ ] [Domínio 1] - Capacidade coberta
- [ ] [Domínio 2] - Capacidade coberta
- [ ] [Domínio 3] - Gap identificado
- [ ] [Domínio 4] - Gap identificado

### Recomendações de Novos Squads
| Prioridade | Squad Sugerido | Domínio | Justificativa |
|------------|---------------|---------|---------------|
| P0 | [nome] | [domínio] | [razão] |
| P1 | [nome] | [domínio] | [razão] |
```

### FASE 3: Métricas de Roteamento (@roteador)

```markdown
## 3. Performance do Roteamento

### Métricas Gerais (últimos 30 dias)
| Métrica | Valor | Meta | Status |
|---------|-------|------|--------|
| Solicitações totais | X | - | - |
| Roteamento direto | X% | >80% | 🟢/🟡/🔴 |
| Roteamento com confirmação | X% | <15% | 🟢/🟡/🔴 |
| Escalações | X% | <5% | 🟢/🟡/🔴 |
| Precisão | X% | >90% | 🟢/🟡/🔴 |

### Roteamento por Squad
| Squad | Solicitações | % do Total | Satisfação |
|-------|-------------|------------|------------|
| [squad 1] | X | Y% | Z% |
| [squad 2] | X | Y% | Z% |
| [squad 3] | X | Y% | Z% |

### Falhas de Roteamento
| Data | Solicitação | Problema | Ação Tomada |
|------|-------------|----------|-------------|
| [data] | [resumo] | [problema] | [ação] |

### Latência
| Métrica | Valor | Meta |
|---------|-------|------|
| Tempo médio de classificação | Xms | <2000ms |
| Tempo médio de roteamento | Xms | <1000ms |
| p99 | Xms | <5000ms |
```

### FASE 4: Qualidade dos Squads (@supervisor-sistema)

```markdown
## 4. Análise de Qualidade

### Quality Score por Squad
| Squad | Estrutura | Documentação | Testes | Score |
|-------|-----------|--------------|--------|-------|
| [squad 1] | X/10 | Y/10 | Z/10 | W/10 |
| [squad 2] | X/10 | Y/10 | Z/10 | W/10 |

### Problemas de Qualidade
| Squad | Problema | Severidade | Ação |
|-------|----------|------------|------|
| [squad 1] | [problema] | Alta/Média/Baixa | [ação] |
| [squad 2] | [problema] | Alta/Média/Baixa | [ação] |

### Checklist de Qualidade
Para cada squad verificar:
- [ ] Config.yaml válido e completo
- [ ] Todos agentes têm arquivos .md
- [ ] Tasks documentadas
- [ ] Workflows funcionais
- [ ] Checklists existem
- [ ] Templates úteis

### Squads que Precisam de Atenção
| Squad | Issues | Prioridade |
|-------|--------|------------|
| [squad 1] | X issues | P0 |
| [squad 2] | X issues | P1 |
```

### FASE 5: Recomendações (@supervisor-sistema)

```markdown
## 5. Plano de Ação

### Ações Imediatas (P0)
| # | Ação | Responsável | Prazo |
|---|------|-------------|-------|
| 1 | [ação] | [squad] | [data] |
| 2 | [ação] | [squad] | [data] |

### Ações de Curto Prazo (P1)
| # | Ação | Responsável | Prazo |
|---|------|-------------|-------|
| 1 | [ação] | [squad] | [data] |
| 2 | [ação] | [squad] | [data] |

### Ações de Médio Prazo (P2)
| # | Ação | Responsável | Prazo |
|---|------|-------------|-------|
| 1 | [ação] | [squad] | [data] |
| 2 | [ação] | [squad] | [data] |

### Monitoramento Contínuo
| Métrica | Frequência | Alerta Se |
|---------|------------|-----------|
| Routing accuracy | Diário | < 85% |
| Unmatched requests | Semanal | > 20% |
| Squad health | Semanal | < 70% |
```

---

## Output Esperado

```markdown
# RELATÓRIO DE AUDITORIA DO SISTEMA

**Data:** [data]
**Período:** [período analisado]
**Auditor:** Orquestrador Global

---

## Resumo Executivo

| Dimensão | Status | Score |
|----------|--------|-------|
| Cobertura | 🟢/🟡/🔴 | X% |
| Qualidade | 🟢/🟡/🔴 | X% |
| Roteamento | 🟢/🟡/🔴 | X% |
| **Geral** | **🟢/🟡/🔴** | **X%** |

---

## Números do Ecossistema

- **Squads:** X
- **Agentes:** X
- **Tasks:** X
- **Workflows:** X

---

## Top 3 Problemas

1. **[Problema 1]** - Impacto: [alto/médio]
2. **[Problema 2]** - Impacto: [alto/médio]
3. **[Problema 3]** - Impacto: [médio/baixo]

---

## Top 3 Gaps

1. **[Gap 1]** - Solução: [solução]
2. **[Gap 2]** - Solução: [solução]
3. **[Gap 3]** - Solução: [solução]

---

## Plano de Ação

### Esta Semana
- [ ] [Ação 1]
- [ ] [Ação 2]

### Este Mês
- [ ] [Ação 3]
- [ ] [Ação 4]

---

## Próxima Auditoria

**Data sugerida:** [data]
**Foco:** [áreas de foco]
```

---

## Completion Criteria

- [ ] Inventário completo realizado
- [ ] Gaps identificados
- [ ] Métricas de roteamento analisadas
- [ ] Qualidade dos squads avaliada
- [ ] Problemas priorizados
- [ ] Plano de ação definido
- [ ] Relatório gerado

---

## Related Files

- knowledge/SQUAD-REGISTRY.md
- workflows/auditoria-sistema.md

---

## Version

```yaml
version: 1.0.0
created: 2026-02-04
author: Squad Creator
last_update: 2026-02-04
```

## Validation

```yaml
validation:
  schema_version: 1
  when: "post"
  checks:
    - id: "has-ecosystem-inventory"
      type: "assertion"
      expression: "output.content && (output.content.includes('Squads') || output.content.includes('Agentes') || output.content.includes('Inventário'))"
      message: "A auditoria deve conter inventário do ecossistema com contagem de squads, agentes e tasks"
      severity: "CRITICAL"

    - id: "has-gap-analysis"
      type: "assertion"
      expression: "output.content && (output.content.includes('Gap') || output.content.includes('gap') || output.content.includes('Problemas') || output.content.includes('Problema'))"
      message: "A auditoria deve conter análise de gaps de capacidade e problemas identificados"
      severity: "CRITICAL"

    - id: "has-action-plan"
      type: "assertion"
      expression: "output.content && (output.content.includes('Plano de Ação') || output.content.includes('Ações Imediatas') || output.content.includes('Recomend'))"
      message: "A auditoria deve conter plano de ação com recomendações priorizadas"
      severity: "HIGH"
  on_fail: "retry"
  max_retries: 2
  escalate_to: "@megabrain-master"
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*

## Quality Gate
- [ ] Processo documentado com inputs, outputs e owner definidos
- [ ] Checklist de validação aplicado antes da entrega
- [ ] Métricas de qualidade verificadas contra threshold
- [ ] Handoff preparado com contexto para próximo agente
- [ ] Bloqueios escalados em até 24h se não resolvidos
