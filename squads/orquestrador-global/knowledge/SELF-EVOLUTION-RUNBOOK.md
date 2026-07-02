# Self-Evolution Runbook -- Operational Guide

> **Workflow:** `squads/orquestrador-global/workflows/self-evolution-cycle.yaml`
> **Cadence:** Quarterly (Q3-Jul, Q4-Oct, Q1-Jan, Q2-Apr)
> **Owner:** @pm + @architect
> **Story:** 78.6

## Overview

Este runbook descreve os comandos CLI exatos para cada fase do ciclo trimestral de auto-evolução do Mega Brain. O ciclo integra 5 scripts do Epic 78 em um fluxo coordenado de 6 fases.

**Duração total:** ~5-6 semanas (esforco humano real: ~5 dias)
**Fases automaticas:** 1 (Collect) e 4 (Propose)
**Fases humanas:** 2 (Audit), 3 (Prioritize), 5 (Review), 6 (Apply)

---

## Pre-Requisitos

Antes de iniciar o ciclo, verificar que todos os scripts estão operacionais:

```bash
# Verificar que cada script responde ao --help
node core/scripts/ops/sdc-metrics-ops.mjs --help
node core/scripts/ops/remediation-ops.mjs --help
node core/scripts/ops/health-ops.mjs --help
node core/scripts/ops/framework-audit-ops.mjs --help
node core/scripts/ops/improvement-ops.mjs --help
node core/scripts/ops/blind-spot-trigger-ops.mjs --help
node core/scripts/ops/issue-log-ops.mjs --help
```

---

## Fase 1: Collect Metrics (1 dia -- Automatico)

**Owner:** Automatico (qualquer agente pode executar)
**Risk:** LOW -- auto-execute

### Objetivo

Coletar todas as métricas do trimestre como baseline para comparação ao final do ciclo.

### Comandos

```bash
# 1. Coletar metricas SDC do trimestre
#    Substitua {YYYY-MM-DD} pela data de inicio do trimestre
#    Ex: Q3-2026 -> --since=2026-07-01
node core/scripts/ops/sdc-metrics-ops.mjs collect --since={YYYY-MM-DD}

# 2. Dashboard SDC agregado (ultimos 3 meses)
node core/scripts/ops/sdc-metrics-ops.mjs dashboard --months=3 --json

# 3. Report de remediacoes (estado atual)
node core/scripts/ops/remediation-ops.mjs report --format=json

# 4. Trend de remediacoes (4 periodos)
node core/scripts/ops/remediation-ops.mjs trend --periods=4 --json

# 5. Health check governance
node core/scripts/ops/health-ops.mjs check --category=governance --format=json

# 6. Status do framework audit (ultimo resultado por target)
node core/scripts/ops/framework-audit-ops.mjs status --json

# 7. Historico de blind-spot triggers (90 dias)
node core/scripts/ops/blind-spot-trigger-ops.mjs history --days=90 --json
```

### Gate de Saida

- [ ] Todos os 7 comandos executaram sem erro
- [ ] sdc-metrics.jsonl tem pelo menos 1 entrada
- [ ] Outputs JSON são validos e parseaveis

### Outputs

Salvar outputs relevantes para referência:
- SDC dashboard JSON (baseline para comparação na Fase 6)
- Remediation report (contagem de open/closed por severity)
- Governance health score

---

## Fase 2: Full Audit (2 semanas -- Squad Chiefs + @architect)

**Owner:** Squad chiefs + @architect
**Risk:** LOW

### Objetivo

Executar auditoria completa do framework (7 targets) e blind-spot self-audits nos squads mais relevantes.

### Comandos -- Framework Audit

```bash
# Auditar todos os 7 targets do framework
node core/scripts/ops/framework-audit-ops.mjs audit --all

# Ou auditar targets individuais (se tempo limitado)
node core/scripts/ops/framework-audit-ops.mjs audit --target=constitution
node core/scripts/ops/framework-audit-ops.mjs audit --target=rules
node core/scripts/ops/framework-audit-ops.mjs audit --target=agents
node core/scripts/ops/framework-audit-ops.mjs audit --target=sdc_workflow
node core/scripts/ops/framework-audit-ops.mjs audit --target=synapse
node core/scripts/ops/framework-audit-ops.mjs audit --target=hooks
node core/scripts/ops/framework-audit-ops.mjs audit --target=config
```

### Comandos -- Blind Spot Triggers

```bash
# Verificar triggers poll-mode pendentes
node core/scripts/ops/blind-spot-trigger-ops.mjs evaluate --poll --json

# Ver status de contadores por squad
node core/scripts/ops/blind-spot-trigger-ops.mjs status
```

### Ações Humanas

1. **@architect** revisa os 7 targets e documenta findings
2. **Squad chiefs** executam blind-spot self-audit nos squads com triggers disparados
3. Squads prioritarios: aqueles que apareceram no `blind-spot-triggers.json` da Fase 1

### Gate de Saida

- [ ] Framework audit executou para todos os 7 targets
- [ ] Pelo menos 5 squads completaram self-audit
- [ ] Findings documentados com severity e squad responsável

---

## Fase 3: Prioritize Findings (2 dias -- @pm + conselho)

**Owner:** @pm + conselho
**Risk:** MEDIUM -- requer julgamento humano

### Objetivo

Priorizar todos os achados e selecionar top 20 remediacoes para o trimestre.

### Comandos

```bash
# 1. Listar issues abertos (ordenados por severity)
node core/scripts/ops/issue-log-ops.mjs list --status=open --sort=severity

# 2. Calcular RPN (severity x occurrence x detection)
node core/scripts/ops/issue-log-ops.mjs prioritize

# 3. Verificar remediacoes estagnadas (sem update > 14 dias)
node core/scripts/ops/remediation-ops.mjs stale --days=14

# 4. Verificar escalations pendentes (CRITICAL >14d, HIGH >30d)
node core/scripts/ops/remediation-ops.mjs escalations

# 5. Estatisticas do issue log (MTTR, aging, top RPN)
node core/scripts/ops/issue-log-ops.mjs stats
```

### Ações Humanas

1. **@pm** consolida findings das fases 1 e 2 com issues existentes
2. **Conselho** revisa e válida priorizacao (trade-offs estrategicos)
3. Selecionar **top 20** remediacoes para gerar proposals
4. Para cada item, definir owner e deadline estimado

### Gate de Saida

- [ ] Top 20 remediacoes selecionadas com RPN
- [ ] Cada item tem owner e deadline
- [ ] Conselho aprovou a priorizacao

---

## Fase 4: Generate Proposals (3 dias -- Automatico + @architect)

**Owner:** Automatico + @architect
**Risk:** LOW

### Objetivo

Gerar improvement proposals automaticamente para os top 20 findings.

### Comandos

```bash
# 1. Gerar proposals para findings CRITICAL (max 10)
node core/scripts/ops/improvement-ops.mjs batch --severity=critical --max=10

# 2. Gerar proposals para findings HIGH (max 10)
node core/scripts/ops/improvement-ops.mjs batch --severity=high --max=10

# 3. Listar proposals geradas
node core/scripts/ops/improvement-ops.mjs list --status=pending
```

### Ações Humanas

1. **@architect** revisa proposals que afetam constitution, rules, ou architecture
2. Marcar proposals de alto impacto como `architect-approved` ou `needs-revision`
3. Proposals que não afetam architecture podem prosseguir sem review

### Gate de Saida

- [ ] Pelo menos 10 proposals geradas
- [ ] Proposals de constitution/architecture revisadas por @architect
- [ ] Cada proposal tem risk e effort estimados

---

## Fase 5: Review & Approve (1 semana -- Humano)

**Owner:** Humano (owner do squad afetado)
**Risk:** HIGH -- requer aprovacao humana

### Objetivo

Revisar cada proposal e decidir: approve, reject, ou defer.

### Comandos

```bash
# Listar proposals pendentes de revisao
node core/scripts/ops/improvement-ops.mjs list --status=pending
```

### Ações Humanas

Para cada proposal:

1. **Ler** a suggested change e risk assessment
2. **Decidir:**
   - `approve` -- implementar neste ciclo
   - `reject` -- não implementar (documentar motivo)
   - `defer` -- mover para próximo ciclo (documentar justificativa)
3. **Registrar** decisão via CLI:
   ```bash
   # Aprovar
   node core/scripts/ops/improvement-ops.mjs approve --id={proposal-id}

   # Rejeitar
   node core/scripts/ops/improvement-ops.mjs reject --id={proposal-id} --reason="motivo"

   # Deferir para proximo ciclo
   node core/scripts/ops/improvement-ops.mjs defer --id={proposal-id} --reason="motivo"
   ```

### Gate de Saida

- [ ] Todas as proposals tem decisão (approve/reject/defer)
- [ ] Proposals rejeitadas tem justificativa documentada
- [ ] Pelo menos 3 proposals aprovadas

---

## Fase 6: Apply & Measure (2 semanas -- @dev)

**Owner:** @dev
**Risk:** MEDIUM

### Objetivo

Implementar proposals aprovadas e medir impacto comparando com baseline da Fase 1.

### Comandos -- Implementação

```bash
# 1. Listar proposals aprovadas
node core/scripts/ops/improvement-ops.mjs list --status=approved

# 2. Para cada proposal aprovada:
#    - Criar story se necessario (mudancas maiores)
#    - Implementar change
#    - Rodar validacao
npm run lint
```

### Comandos -- Medicao de Impacto

```bash
# 3. Re-coletar metricas (mesmos comandos da Fase 1)
node core/scripts/ops/sdc-metrics-ops.mjs dashboard --months=1 --json
node core/scripts/ops/health-ops.mjs check --category=governance --format=json
node core/scripts/ops/remediation-ops.mjs status --json

# 4. Comparar com baseline da Fase 1
#    (manual: comparar JSONs side-by-side)
```

### Comandos -- Relatório do Ciclo

```bash
# 5. Gerar relatorio usando template
#    Template: squads/orquestrador-global/templates/self-evolution-report-tmpl.md
#    Output:   core/reports/self-evolution-{YYYY-QN}.md
```

### Comandos -- Atualizar Cadence

```bash
# 6. Marcar ciclo como completo e agendar proximo
node core/scripts/ops/cadence-ops.mjs complete \
  --audit=self-evolution-cycle \
  --squad=orquestrador-global
```

### Gate de Saida

- [ ] Todas as proposals aprovadas implementadas (ou deferidas com motivo)
- [ ] Métricas pos-ciclo coletadas
- [ ] Relatório do ciclo gerado em `core/reports/self-evolution-{YYYY-QN}.md`
- [ ] Cadence entry atualizada com `next_due` do próximo trimestre
- [ ] `npm run lint` passa

---

## Troubleshooting

### Script não encontrado

```bash
# Verificar que o script existe
ls -la core/scripts/ops/{script-name}.mjs
```

Se `improvement-ops.mjs` não existir, verificar status da Story 78.3.

### Dados insuficientes para métricas

No primeiro ciclo, os dados podem ser limitados. Isso é esperado:
- SDC metrics dependem de stories com status tracking
- Remediation data depende de issues registrados
- O primeiro ciclo serve como baseline

### Ciclo interrompido

Se o ciclo for interrompido, retomar da fase onde parou. Cada fase e independente
(exceto dependencias sequenciais). Use o campo `skip_phases` no input do workflow
para pular fases já completadas.

---

## Calendário Trimestral

| Trimestre | Início | Deadline |
|-----------|--------|----------|
| Q3 2026 | 2026-07-01 | 2026-08-15 |
| Q4 2026 | 2026-10-01 | 2026-11-15 |
| Q1 2027 | 2027-01-01 | 2027-02-15 |
| Q2 2027 | 2027-04-01 | 2027-05-15 |

---

## Referência

| Script | Story | Função |
|--------|-------|--------|
| `framework-audit-ops.mjs` | 78.1 | Audit targets do framework |
| `remediation-ops.mjs` | 78.2 | Remediation tracking |
| `improvement-ops.mjs` | 78.3 | Improvement proposals |
| `sdc-metrics-ops.mjs` | 78.4 | SDC quality metrics |
| `health-ops.mjs` (governance) | 78.5 | Governance health monitor |
| `blind-spot-trigger-ops.mjs` | 69.15-69.18 | Event-driven triggers |
| `issue-log-ops.mjs` | 31.1 | Centralized issue log |
| `cadence-ops.mjs` | -- | Cadence scheduling |
