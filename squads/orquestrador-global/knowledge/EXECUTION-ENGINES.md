# EXECUTION-ENGINES — Mecanismos de Execução Autônoma

## O que é um Execution Engine

Um execution engine é um módulo que recebe uma demanda classificada pelo orquestrador e a executa de forma autônoma, retornando um resultado padronizado. O orquestrador não conhece os detalhes internos da execução — apenas despacha e recebe o resultado.

**Princípio arquitetural:** Orquestrador = estratégia + routing. Engine = execução tática.

---

## Fronteira com o Ecossistema de Orquestração

Este documento lista engines de execução. Ele não esgota as capacidades de orquestração do Mega Brain/MEGABRAIN.

A análise completa do `orquestrador-global` precisa considerar também:

- primitives de swarm/paralelização: `swarm-execute`, `WorkflowOrchestrator` e `ParallelExecutor`;
- engine de contexto: SYNAPSE;
- memória e aprendizado: `ReasoningBank`, `QLearningRouter`, `packages/@megabrain/engine-memory`, `packages/core/memory` e WIS/learning;
- governança: Constitution, Agent Authority, Story-Driven Development, CODEOWNERS e gates.

Registry canônico desta fronteira: `squads/orquestrador-global/data/orchestration-ecosystem-registry.yaml`.

Documento operacional: `squads/orquestrador-global/knowledge/ORCHESTRATION-ECOSYSTEM.md`.

**Implicação:** example-squad é o engine SDC validado. Ele não representa sozinho todo o runtime/swarm do ecossistema.

---

## Mega Brain example-squad

### O que é

Mega Brain example-squad é o executor autônomo planejado do Story Development Cycle (SDC). Ele recebe uma story com status `Ready` e executa as 4 fases do SDC (create/validate/implement/qa-gate) de forma autônoma, com session isolation entre cada fase.

### Estado atual nesta branch

O boundary `orquestrador-global → Mega Brain example-squad` está em `validated_stub_v2`.

| Superfície | Estado |
|------------|--------|
| `dispatchToWorker(payload)` | Implementado e importável |
| CLI operacional | Implementado via `core/core/orchestration/megabrain-example-squad-ops.mjs dispatch` |
| Schemas JSON | Implementados em `schemas/contracts/` |
| Validação de story | Implementada: status, dependências, complexidade `SIMPLE`/`STANDARD` e architecture review |
| Manifesto de handoff | Implementado para chamadas não dry-run que passam constraints |
| Runtime state machine | Implementada com lock, runtime state e handoff inicial |
| Runtime adapter | Implementado em `core/core/orchestration/megabrain-example-squad-runtime.mjs` |
| Provider request SDC | Implementado: request YAML + prompt Markdown por fase |
| Validação de phase-result | Implementada via `validateWorkerPhaseResult()` e schema `megabrain-example-squad-phase-result.schema.json` |
| Backend de execução do provider | Implementado via `contract_file` e `agent_command` configuráveis |
| `squads/example-squad/` | Ausente nesta branch; não é o caminho canônico da ADR atual |

### Módulo de dispatch

- **Arquivo:** `core/core/orchestration/megabrain-example-squad-dispatch.mjs`
- **Função:** `dispatchToWorker(payload)` — entrada única para o orquestrador
- **Entry CLI:** `core/core/orchestration/megabrain-example-squad-ops.mjs dispatch`
- **Runtime adapter:** `core/core/orchestration/megabrain-example-squad-runtime.mjs`
- **Executor direto:** backend `contract_file` executa fases SDC consumindo phase-results tipados já existentes; backend `agent_command` chama um comando externo por fase e exige o mesmo phase-result tipado. Sem backend configurado, o boundary continua seguro e retorna `WORKER_PROVIDER_BACKEND_UNCONFIGURED`.

### Contrato de entrada (input)

```yaml
story_id: "42.1"                  # Identificador da story
workspace: "example-squad"       # Workspace slug
caller_agent: "orquestrador-global"  # Obrigatório — validação de autoridade
priority: "MEDIUM"                # HIGH | MEDIUM | LOW
mode: "yolo"                      # interactive | yolo | preflight
provider_backend: "contract_file"  # opcional
provider_result_dir: "outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/contract-file-provider"
provider_command: null             # obrigatório quando provider_backend=agent_command
provider_command_args: []           # opcional quando provider_backend=agent_command
provider_timeout_ms: null           # opcional quando provider_backend=agent_command
```

Schema JSON: `schemas/contracts/megabrain-example-squad-dispatch.schema.json`

### Contrato de saída (output)

```yaml
status: "dry_run"                 # completed | blocked | failed | dry_run
story_id: "42.1"
run_id: "example-squad-dispatch-a1b2c3d4e5f6"
engine_status: "validated_stub_v2"
phases_completed: []
duration_ms: 0
tokens_used: 0
cost_usd: 0
commit_hash: null
blockers: []
model: null
manifest_path: null
constraint_check:
  performed: true
  passed: true
```

Schema JSON: `schemas/contracts/megabrain-example-squad-result.schema.json`

### Session Isolation (Opção B)

Cada fase SDC deve executar em um `Agent()` call isolado quando o provider de fase/agente example-squad existir. O contexto entre fases deve ser transmitido exclusivamente via handoff artifact (máximo 550 tokens):

```
Phase 1 (@sm) → handoff artifact → Phase 2 (@po) → handoff artifact → Phase 3 (@dev) → handoff artifact → Phase 4 (@qa)
```

**Invariante:** A fase N+1 NUNCA recebe o contexto completo da fase N. Apenas o handoff artifact.

Handoff artifacts planejados: `.data/megabrain-example-squad-handoffs/`

### Quando usar Mega Brain example-squad

| Critério | Detalhe |
|----------|---------|
| Story status | `Ready` (validada pelo @po) |
| Dependencies | Todas marcadas como `Done` |
| Complexity | `SIMPLE` ou `STANDARD` |
| Workspace | Com Mega Brain example-squad habilitado (ou `workspace_filter: []` para todos) |
| Architecture review | Não pode ter `requires_architecture_review: true` |

### Quando NÃO Usar Mega Brain example-squad

| Cenário | Razão | Alternativa |
|---------|-------|-------------|
| Stories com complexity `HIGH`, `CRITICAL` ou ausente | Risco alto ou metadado insuficiente para execução autônoma | Refinar com @po ou delegar manualmente |
| Multi-squad campaigns | example-squad só executa SDC (dev workflow) | Pipeline orchestration via `pipeline-ops.mjs` |
| Non-dev workflows | Content, sales, marketing workflows | Squads especializados |
| Stories sem AC claros | Risco de implementação incorreta | Refinar com @po primeiro |
| Architecture review needed | Precisa de decisão de @architect antes | Delegar a @architect |

### Configuração

Seção `megabrain_worker:` em `core-config.yaml`:

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `calibration_mode` | bool | `true` | `true` = dry-run (não executa fases reais) |
| `auto_dispatch` | bool | `false` | `true` = dispatch automático sem aprovação humana |
| `daily_budget_usd` | number | `10.0` | Limite de budget diário |
| `failure_notify` | bool | `true` | Notificar via WhatsApp em caso de falha |
| `max_concurrent` | number | `1` | Máximo de stories simultâneas (single-threaded) |

### Risk Classification

O dispatch de stories é classificado como risco **MEDIUM**:
- Executa com notificação
- Reversível via `git revert`
- Logado no audit trail

### Limitações

- Single-threaded: `max_concurrent: 1` — uma story por vez
- Sem dispatch paralelo de múltiplas stories
- Sem integração com outros execution engines (por enquanto)
- Dashboard UI para monitoramento em tempo real será Epic 43

---

## Fluxo de Dispatch

```
1. Orquestrador detecta story com status Ready
2. Verifica critérios de routing (dependencies Done, complexity SIMPLE/STANDARD, etc.)
3. Chama dispatchToWorker({ story_id, workspace, caller_agent, priority, mode })
4. Dispatch module:
   a. Valida input contract
   b. Verifica autoridade do caller
   c. Resolve a story em `docs/stories/`
   d. Verifica status, dependências, complexidade e architecture review
   e. Se `--dry-run`: retorna preview sem gravar artefatos
   f. Se constraints passam sem `--dry-run`: emite manifesto de handoff
   g. Renderiza provider request/prompt por fase
   h. Executa o provider backend configurado (`contract_file` ou `agent_command`)
   i. Valida o phase-result tipado
   j. Avança `create → validate → implement → qa_gate` por handoff artifacts
   k. Sem backend configurado, retorna `blocked` com `WORKER_PROVIDER_BACKEND_UNCONFIGURED`
5. Resultado retorna ao orquestrador
6. Orquestrador registra no audit trail e notifica se necessário
```

---

## Como Usar (CLI Operacional)

O script operacional existente nesta branch é `core/core/orchestration/megabrain-example-squad-ops.mjs`. Ele expõe apenas o subcomando `dispatch` e delega ao boundary validável `megabrain-example-squad-dispatch.mjs`.

### Rodar regressão determinística do boundary example-squad

```bash
node core/core/orchestration/megabrain-example-squad-smoke.mjs
```

Resultado esperado: `Mega Brain example-squad smoke PASS (13 checks)`. O smoke cobre sintaxe, schemas, YAMLs, scanner de prontidão do backlog, dry-run, blockers esperados, escrita isolada sem backend, execução completa via `contract_file`, execução completa via `agent_command`, falha de `agent_command`, CLI, lock contention e phase-result validation.

### Escanear prontidão do backlog real

```bash
node core/core/orchestration/megabrain-example-squad-backlog-readiness.mjs \
  --format json \
  --limit 25
```

Resultado esperado: relatório read-only com `ready_total`, `routable_total`, blockers dominantes e `po_triage_queue`. Se `routable_total` for `0`, o próximo passo é PO classificar `complexity` em uma candidata real antes de qualquer dispatch autônomo.

### Validar uma story roteável sem gravar artefatos

```bash
node core/core/orchestration/megabrain-example-squad-ops.mjs dispatch \
  --story example-squad-EVAL-READY \
  --story-file outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/STORY-example-squad-EVAL-READY.md \
  --workspace hub \
  --priority HIGH \
  --mode preflight \
  --dry-run \
  --verbose
```

Resultado esperado: `status: dry_run`, `constraint_check.passed: true`, `blockers: []`.

### Bloquear uma story Ready com metadado incompleto

```bash
node core/core/orchestration/megabrain-example-squad-ops.mjs dispatch \
  --story 124.1 \
  --workspace hub \
  --priority HIGH \
  --mode preflight \
  --dry-run \
  --verbose
```

Resultado esperado: exit code `1` e blocker `COMPLEXITY_NOT_ROUTABLE`, porque `124.1` está `Ready`, mas não declara `complexity: SIMPLE` ou `complexity: STANDARD`.

### Rejeitar uma story fora das constraints

```bash
node core/core/orchestration/megabrain-example-squad-ops.mjs dispatch \
  --story 99.1 \
  --workspace hub \
  --priority HIGH \
  --mode preflight \
  --dry-run \
  --verbose
```

Resultado esperado: exit code `1` e blocker `STORY_STATUS_NOT_READY`, porque `99.1` está `Done`.

### Emitir manifesto sem backend configurado

```bash
node core/core/orchestration/megabrain-example-squad-ops.mjs dispatch \
  --story example-squad-EVAL-READY \
  --story-file outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/STORY-example-squad-EVAL-READY.md \
  --workspace hub \
  --priority HIGH \
  --mode preflight
```

Resultado esperado nesta branch: manifesto em `outputs/dispatches/`, runtime state em `.data/megabrain-example-squad-runs/`, handoff inicial em `.data/megabrain-example-squad-handoffs/`, provider request/prompt em `.data/megabrain-example-squad-runs/<run>/`, audit trail em `.data/`, schema/validador de phase-result disponível, e `status: blocked` com blocker `WORKER_PROVIDER_BACKEND_UNCONFIGURED`, porque nenhum backend foi informado nessa chamada.

### Executar fases com backend `contract_file`

```bash
node core/core/orchestration/megabrain-example-squad-ops.mjs dispatch \
  --story example-squad-EVAL-READY \
  --story-file outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/STORY-example-squad-EVAL-READY.md \
  --workspace hub \
  --priority HIGH \
  --mode preflight \
  --provider-backend contract_file \
  --provider-result-dir outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/contract-file-provider \
  --verbose
```

Resultado esperado: `status: completed`, `phases_completed: [create, validate, implement, qa_gate]`, quatro provider requests, quatro phase-results validados e quatro handoff artifacts.

### Executar fases com backend `agent_command`

```bash
node core/core/orchestration/megabrain-example-squad-ops.mjs dispatch \
  --story example-squad-EVAL-READY \
  --story-file outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/STORY-example-squad-EVAL-READY.md \
  --workspace hub \
  --priority HIGH \
  --mode preflight \
  --provider-backend agent_command \
  --provider-command "$(command -v node)" \
  --provider-command-arg outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/agent-command-provider.mjs \
  --provider-timeout-ms 30000 \
  --verbose
```

Resultado esperado: `status: completed`, `phases_completed: [create, validate, implement, qa_gate]`, quatro provider requests, quatro phase-results validados e quatro provider executions. O comando recebe `--phase`, `--run-id`, `--agent`, `--request`, `--prompt`, `--handoff`, `--output` e `--schema`, além das variáveis `MEGABRAIN_WORKER_*` equivalentes.

### Batch, status e histórico

Batch, status e histórico ainda não existem nesta CLI. Enquanto isso, o orquestrador deve tratar cada story como uma chamada explícita e consultar os manifestos em `outputs/dispatches/`.

### Fluxo do orquestrador

Quando o orquestrador identifica uma story Ready para implementação:

1. Verifica critérios de routing (dependencies Done, complexity SIMPLE/STANDARD)
2. Chama `megabrain-example-squad-ops.mjs dispatch --story X --workspace Y`
3. O boundary valida input, autoridade, story e constraints
4. Se `--dry-run` → retorna preview sem gravar
5. Se OK sem `--dry-run` e sem backend → emite manifesto/handoff e bloqueia com blocker acionável
6. Se OK sem `--dry-run` e com `contract_file` → executa fases a partir dos phase-results tipados
7. Se OK sem `--dry-run` e com `agent_command` → chama um provider externo por fase e valida o phase-result gerado
8. Resultado é logado no `megabrain-example-squad-dispatch-log.jsonl` e `audit-trail.jsonl` quando um manifesto é emitido

### Uso programático (dentro de scripts/hooks)

```javascript
import { dispatchToWorker } from 'core/core/orchestration/megabrain-example-squad-dispatch.mjs';

const result = await dispatchToWorker({
  story_id: 'example-squad-EVAL-READY',
  story_file: 'outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/STORY-example-squad-EVAL-READY.md',
  workspace: 'hub',
  caller_agent: 'orquestrador-global',
  priority: 'HIGH',
  mode: 'preflight',
  provider_backend: 'contract_file',
  provider_result_dir: 'outputs/eval/megabrain-example-squad/20260502-validated-stub-v2/fixtures/contract-file-provider',
  dry_run: true,
});

if (result.constraint_check.passed && result.status === 'dry_run') {
  // Story pode ser convertida em manifesto de handoff.
} else if (result.status === 'blocked') {
  // Constraints falharam, backend não configurado, phase-result inválido ou fase bloqueada.
} else if (result.status === 'failed') {
  // Erro de input/resolução — verificar result.blockers.
}
```

---

## Referência

- **Dispatch CLI:** `core/core/orchestration/megabrain-example-squad-ops.mjs dispatch`
- **Dispatch module:** `core/core/orchestration/megabrain-example-squad-dispatch.mjs`
- **Runtime adapter:** `core/core/orchestration/megabrain-example-squad-runtime.mjs`
- **SDC provider backend:** `contract_file`, `agent_command`
- **Checkpoint:** não presente nesta branch
- **Task router:** não presente nesta branch
- **Input schema:** `schemas/contracts/megabrain-example-squad-dispatch.schema.json`
- **Output schema:** `schemas/contracts/megabrain-example-squad-result.schema.json`
- **Phase-result schema:** `schemas/contracts/megabrain-example-squad-phase-result.schema.json`
- **Engine registry:** `squads/orquestrador-global/data/execution-engine-registry.yaml`
- **Gap ativo:** `squads/orquestrador-global/data/infrastructure-map.yaml#GAP-INFRA-008`
