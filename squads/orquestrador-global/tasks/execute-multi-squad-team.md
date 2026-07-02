---
task: execute-multi-squad-team
name: 'Task: Execute Multi-Squad Team (Staged)'
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@plan-architect'
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
pre_condition: Demand and squad_sequence provided; participating squad configs accessible
post_condition: Staged execution completed with per-stage gate approvals and final consolidated output saved
performance:
  error_handling: graceful with fallback + retry
domain: operational
task_id: execute-multi-squad-team
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

# Task: Execute Multi-Squad Team (Staged)

## Metadata
```yaml
id: execute-multi-squad-team
name: Execucao Staged Multi-Squad via Agent Teams
version: 2.0.0
executor: team-coordinator
workflow: executar-com-team
estimated_time: variable (depends on number of squads and stages)
```

## Purpose

Executar demandas que requerem multiplos squads, agrupados em stages com gates de aprovacao.
Cada stage pode conter 1+ squads. Ao final de cada stage, o usuario revisa entregas antes de avancar.
Backward compatible: demandas single-squad rodam sem stages.

---

## Input Requirements

| Campo | Tipo | Obrigatorio | Exemplo |
|-------|------|-------------|---------|
| demand | string | Sim | "Criar sales page para curso X" |
| squad_sequence | list | Sim | ["deep-scraper", "copywriting", "design-system", "creative-studio", "full-stack-dev"] |
| stage_definitions | list | Nao | (ver abaixo) |
| context_initial | object | Nao | {produto: "Curso X", publico: "Y"} |
| skip_gates | boolean | Nao | false (default) |

### stage_definitions format

```yaml
stage_definitions:
  - stage: 1
    name: "Pesquisa & Inteligencia"
    squads: ["deep-scraper"]
    gate_criteria:
      - "Pesquisa de mercado completa"
      - "Analise de concorrentes documentada"

  - stage: 2
    name: "Copy + Design System"
    squads: ["copywriting", "design-system"]
    gate_criteria:
      - "Sales page copy aprovada"
      - "Design tokens definidos"

  - stage: 3
    name: "Assets Visuais"
    squads: ["creative-studio"]
    gate_criteria:
      - "Assets visuais criados"
      - "Consistencia com design system"

  - stage: 4
    name: "Desenvolvimento"
    squads: ["full-stack-dev"]
    gate_criteria:
      - "Pagina implementada e funcional"
      - "Responsivo mobile/desktop"
```

Se `stage_definitions` nao for fornecido, o Maestro gera automaticamente com base nos squads.

---

## Execution Flow

### Decisao de Modo (Step 0.0)

```
SE len(squad_sequence) == 1 OU skip_gates == true:
  → Fase 1 (Planejamento Sequencial legacy — sem stages)
  → Executar como v1: squad unico, sem gates

SE len(squad_sequence) >= 2 E skip_gates != true:
  → Fase 0 (Validacao e Stage Setup)
  → Fase 2 (Loop de Execucao Staged com gates)

Ambos os caminhos terminam em Fase 3 (Consolidacao Final)
```

---

### Fase 0: Validacao e Stage Setup

> Usado quando: multi-squad (2+ squads) com gates habilitados

**Step 0.1: Validar Squads**
- Para cada squad na lista: verificar se e suportado (tier_1, tier_2, tier_3)
- Rejeitar squads nao suportados com mensagem clara

**Step 0.2: Gerar ou Validar Stages**
- Se `stage_definitions` fornecido: validar que todos os squads estao cobertos
- Se nao fornecido: gerar stages automaticamente:
  - Regra: squads com dependencia logica ficam em stages separados
  - Squads paralelos (sem dependencia entre si) ficam no mesmo stage
  - Exemplo: deep-scraper (stage 1) → copywriting + design-system (stage 2) → creative-studio (stage 3) → full-stack-dev (stage 4)

**Step 0.3: Consultar Chiefs**
- Para cada squad nos stages: executar task `consult-chief`
- Input: squad_id + demand_context + available_inputs do stage anterior
- Output: chief_report por squad

**Step 0.4: Gerar Plano Master Staged**
- Usar template `team-execution-plan-tmpl` com secoes staged
- Incluir chief reports por squad
- Incluir gates de aprovacao com criterios
- Apresentar para aprovacao do usuario

**Step 0.5: Obter Aprovacao**
- Opcoes: Aprovar Plano Completo | Aprovar Apenas Stage 1 | Modificar Plano | Cancelar
- Se "Apenas Stage 1": marcar stages 2+ como `pending_approval`
- Se "Modificar": ajustar e re-apresentar

---

### Fase 1: Planejamento Sequencial (backward compat)

> Usado quando: single-squad OU skip_gates=true OU apenas 1 stage

- Receber lista de squads
- Para cada squad: carregar team-config, validar suporte
- Definir ordem de execucao e pontos de handoff
- Apresentar plano sequencial ao usuario

---

### Fase 2: Loop de Execucao Staged

> Loop duplo: outer = stages, inner = squads dentro do stage

```
PARA CADA stage na lista de stages:
  │
  ├── Step 2.1: Iniciar Stage
  │   - Criar diretorio: stage-{N}/
  │   - Logar inicio do stage
  │
  ├── PARA CADA squad no stage:
  │   │
  │   ├── Step 2.2a: Preparar Contexto
  │   │   - Se primeiro squad do primeiro stage: usar context_initial
  │   │   - Se squad subsequente no MESMO stage: usar context_initial + outputs de stages anteriores
  │   │   - Se squad em stage > 1: carregar outputs de TODOS os stages anteriores
  │   │   - Montar briefing com contexto acumulado
  │   │
  │   ├── Step 2.2b: Executar Squad
  │   │   - Chamar execute-team para o squad atual
  │   │   - Passar contexto acumulado
  │   │   - Aguardar conclusao
  │   │
  │   ├── Step 2.2c: Salvar Outputs do Squad
  │   │   - Salvar em: .data/team-outputs/{session-id}/stage-{S}/squad-{NN}-{name}/
  │   │   - Gerar handoff document usando team-context-handoff-tmpl
  │   │
  │   └── Step 2.2d: Shutdown Squad Team
  │       - Desligar team atual (team-shutdown)
  │       - Verificar outputs salvos
  │
  ├── Step 2.3: Consolidar Stage
  │   - Coletar outputs de todos os squads do stage
  │   - Gerar stage-summary.md em stage-{S}/ usando template `stage-summary-tmpl`
  │   - Conteudo: entregas por squad, decisoes, problemas, metricas, criterios de aceite
  │
  └── Step 2.4: Gate de Aprovacao
      - Apresentar entregas usando template stage-gate-review-tmpl
      - Mostrar: entregas por squad, criterios de aceite, preview proximo stage
      - Aguardar decisao do usuario:
        │
        ├── (1) APROVAR → Avancar para proximo stage
        │
        ├── (2) SOLICITAR REVISOES → Re-executar squad(s) especifico(s)
        │   - Identificar qual(is) squad(s) revisar
        │   - Re-executar apenas o(s) squad(s) indicado(s)
        │   - Manter outputs dos outros squads intactos
        │   - Voltar ao Gate com entregas atualizadas
        │
        ├── (3) MODIFICAR PLANO → Alterar stages restantes
        │   - Receber instrucoes de modificacao
        │   - Recalcular stages seguintes
        │   - Re-apresentar plano atualizado para aprovacao
        │
        ├── (4) PAUSAR → Salvar estado e parar
        │   - Salvar: stage atual, outputs acumulados, plano restante
        │   - Mensagem: "Execucao pausada em Stage {N}. Retome com *execute-team --resume {session_id}"
        │
        └── (5) CANCELAR → Encerrar execucao
            - Manter outputs dos stages ja concluidos
            - Gerar relatorio parcial
            - Mensagem: "Execucao cancelada. Outputs dos stages 1-{N} mantidos em {path}"
```

---

### Fase 3: Consolidacao Final

**Step 3.1: Gerar Execution Logs**
Conforme regra `.claude/rules/execution-logging.md`, gerar em `.data/executions/{YYYY-MM-DD}_{demanda-slug}/`:
- `00-master-plan.md` — Plano master staged (ja gerado na Fase 0, copiar para executions)
- `{NN}-{squad}-input.md` — Para cada squad: briefing/input recebido
- `{NN}-{squad}-output.md` — Para cada squad: output/entregas
- `99-execution-summary.md` — Relatorio consolidado final

> NOTA: Os outputs de squad ficam em DUAS localizacoes:
> - `.data/team-outputs/{session-id}/stage-{S}/squad-{NN}-{name}/` (outputs brutos)
> - `.data/executions/{YYYY-MM-DD}_{slug}/` (logs estruturados conforme regra)

**Step 3.2: Consolidar Resultados**
- Coletar todos os outputs de todos os stages
- Gerar `99-execution-summary.md` com: status por stage/squad, entregas finais, licoes aprendidas
- Apresentar resultado final ao usuario

**Step 3.3: Persistir em SuperMemory**
- Salvar summary no SuperMemory (containerTag: "megabrain-master")
- Incluir: demanda, squads, status, entregas, licoes

---

## Output Structure

### Single-Squad (backward compat)
```
.data/team-outputs/{session-id}/
  squad-1-{name}/
    [outputs]
```

### Multi-Squad Staged
```
.data/team-outputs/{session-id}/
  stage-1/
    squad-01-{name}/
      [outputs]
    stage-summary.md
  stage-2/
    squad-02-{name}/
      [outputs]
    squad-03-{name}/
      [outputs]
    stage-summary.md
  stage-3/
    squad-04-{name}/
      [outputs]
    stage-summary.md
  stage-4/
    squad-05-{name}/
      [outputs]
    stage-summary.md
```

### Execution Logs (parallel)
```
.data/executions/{YYYY-MM-DD}_{slug}/
  00-master-plan.md
  01-deep-scraper-input.md
  01-deep-scraper-output.md
  02-copywriting-input.md
  02-copywriting-output.md
  03-design-system-input.md
  03-design-system-output.md
  04-creative-studio-input.md
  04-creative-studio-output.md
  05-full-stack-dev-input.md
  05-full-stack-dev-output.md
  99-execution-summary.md
```

---

## Quality Gates

### Gate 0: Planejamento
- [ ] Todos os squads na sequencia sao suportados?
- [ ] Stages agrupados logicamente?
- [ ] Chief reports gerados para cada squad?
- [ ] Plano staged aprovado pelo usuario?

### Gate per Stage: Revisao de Entregas
- [ ] Todos os squads do stage concluiram?
- [ ] Outputs salvos corretamente?
- [ ] Stage summary gerado?
- [ ] Criterios de aceite do gate revisados?
- [ ] Usuario aprovou entregas do stage?

### Gate Final: Consolidacao
- [ ] Todos os stages concluidos e aprovados?
- [ ] Outputs finais coletados?
- [ ] Relatorio consolidado gerado?
- [ ] Nenhum output perdido?
- [ ] Summary salvo no SuperMemory?

---

## Rollback Points

```yaml
rollback:
  squad_falha:
    acao: "Salvar progresso parcial. Oferecer re-execucao do squad no gate"
    mensagem: "Squad {name} falhou. Resultados parciais salvos. Escolha no gate: revisar ou pular"

  context_perdido:
    acao: "Reconstruir contexto a partir de outputs salvos nos stages anteriores"
    mensagem: "Reconstruindo contexto a partir dos outputs de stages 1-{N}..."

  gate_revisao:
    acao: "Re-executar squad especifico sem perder outputs dos demais"
    mensagem: "Re-executando {squad} com feedback: {feedback}. Outros outputs mantidos."

  sequencia_interrompida:
    acao: "Salvar estado completo do stage para retomada"
    mensagem: "Execucao pausada em Stage {N}. Pode retomar com *execute-team --resume {session_id}"

  plano_modificado:
    acao: "Recalcular stages restantes mantendo outputs aprovados"
    mensagem: "Plano atualizado. Stages 1-{N} mantidos. Stages {N+1}+ recalculados."
```

---

## Example

### Input
```yaml
demand: "Criar sales page para curso de um nicho de saúde avancada"
squad_sequence: ["deep-scraper", "copywriting", "design-system", "creative-studio", "full-stack-dev"]
context_initial:
  produto: "Curso de um nicho de saúde Avancada"
  publico: "Profissionais de saude"
  preco: "R$ 997"
```

### Auto-generated Stages
```yaml
stage_definitions:
  - stage: 1
    name: "Pesquisa & Inteligencia"
    squads: ["deep-scraper"]
    gate_criteria:
      - "Pesquisa de mercado completa"
      - "Analise de concorrentes documentada"
      - "Perfil de audiencia definido"

  - stage: 2
    name: "Copy + Design System"
    squads: ["copywriting", "design-system"]
    gate_criteria:
      - "Sales page copy completa"
      - "Design tokens e componentes definidos"

  - stage: 3
    name: "Assets Visuais"
    squads: ["creative-studio"]
    gate_criteria:
      - "Imagens e assets criados"
      - "Consistencia com design system"

  - stage: 4
    name: "Desenvolvimento"
    squads: ["full-stack-dev"]
    gate_criteria:
      - "Pagina implementada"
      - "Responsivo e funcional"
```

### Processing
```
=== STAGE 1: Pesquisa & Inteligencia ===
Squad 1: deep-scraper → Pesquisa de mercado e audiencia
  Output: relatorio, tendencias, competitors
  Saved: stage-1/squad-01-deep-scraper/
  Stage Summary: stage-1/stage-summary.md

>>> GATE 1: Revisao de pesquisa <<<
  Usuario: "Aprovar" ✓

=== STAGE 2: Copy + Design System ===
Squad 2: copywriting → Sales page copy
  Input: outputs do stage 1 + context_initial
  Output: sales-page-copy.md, headlines.md
  Saved: stage-2/squad-02-copywriting/

Squad 3: design-system → Design tokens
  Input: outputs do stage 1 + context_initial
  Output: tokens.md, components.md
  Saved: stage-2/squad-03-design-system/

  Stage Summary: stage-2/stage-summary.md

>>> GATE 2: Revisao copy + design <<<
  Usuario: "Revisar copywriting: headlines mais urgentes"
  → Re-executa copywriting com feedback
  → Novo output salvo
  Usuario: "Aprovar" ✓

=== STAGE 3: Assets Visuais ===
Squad 4: creative-studio → Assets
  Input: outputs dos stages 1 + 2
  Output: hero-image.png, section-assets/
  Saved: stage-3/squad-04-creative-studio/

>>> GATE 3: Revisao assets <<<
  Usuario: "Aprovar" ✓

=== STAGE 4: Desenvolvimento ===
Squad 5: full-stack-dev → Implementacao
  Input: outputs de todos os stages anteriores
  Output: pagina implementada
  Saved: stage-4/squad-05-full-stack-dev/

>>> GATE FINAL <<<
  Usuario: "Aprovar" ✓

=== CONSOLIDACAO ===
  Relatorio final gerado
  Summary salvo no SuperMemory
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
