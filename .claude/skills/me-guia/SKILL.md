---
name: me-guia
description: >
  Universal intent router and adaptive elicitation skill for the Mega Brain framework.
  Receives any user request (strategic, operational, creative, infrastructure, exploratory),
  extracts intent slots automatically, classifies confidence, resolves to existing squads/tasks/agents
  via hierarchical search, and generates incremental execution pipelines. Never invents tasks --
  always searches existing registries first and suggests creation via handoffs when gaps are found.
  Triggers: "me guia", "me ajuda", "o que eu faco", "como faco", "preciso de", "quero", any
  ambiguous request where the user doesn't know which agent/squad/task to use.
---

# Me Guia v1.0

Universal intent router for the Mega Brain framework. Transforms any user request into an
actionable execution plan using existing tasks, agents, and squads.

## Core Principle: Incremental, Never Invent

This skill NEVER fabricates tasks, agents, or capabilities. It operates strictly on what
EXISTS in the Mega Brain registries. When a gap is found, it transparently reports the gap and
offers to create the missing piece via the proper creation channels.

## When To Use

- User doesn't know which agent, squad, or task to invoke
- User describes a need, problem, or goal in natural language
- User wants to explore what the system can do for a given domain
- User has a multi-step need that may require a pipeline of tasks
- Any ambiguous request that doesn't clearly map to a single skill/command

## Phase 0: Automatic Slot Extraction

Before asking ANY question, parse the user's initial message to extract slots.

### Slots to Extract

| Slot | Description | Source Keywords |
|------|------------|-----------------|
| `domain` | Subject area / squad | Match against ecosystem-registry keywords |
| `action` | What verb (create, analyze, fix, explore...) | Verb analysis |
| `target` | What artifact or subject | Nouns, file paths, template names |
| `business` | Which business context | Match against workspace/businesses/ slugs |
| `state` | What exists today | References to files, templates, "already have" |

### How to Extract

1. Read the user's message
2. For each slot, attempt extraction from the message text
3. For `domain`: grep keywords against `.mega-brain/squad-runtime/ecosystem-registry.yaml`
4. For `target`: check if mentioned artifacts exist in `workspace/_templates/` or `outputs/`
5. For `state`: check if mentioned files exist in the workspace
6. Assign confidence per slot: ALTA (explicit match), MEDIA (inferred), BAIXA (guessed)

### Calculate Overall Confidence

```
overall_confidence = min(domain_confidence, action_confidence)
```

- Both ALTA = overall ALTA
- One MEDIA = overall MEDIA
- Any BAIXA = overall BAIXA

## Phase 1: Adaptive Elicitation

Question budget is determined by confidence. NEVER ask more than 3 questions total.

### ALTA Confidence (>0.85): 0 questions

Squad and action are clear. Confirm and proceed.

```
"Entendi: voce quer [action] no dominio [squad].
Vou buscar a melhor task para isso. Correto?"
```

If user confirms, skip to Phase 2.

### MEDIA Confidence (0.5-0.85): 1 disambiguation question

Squad is clear but task is ambiguous, or multiple squads match.

```
"Encontrei [N] opcoes para o que voce descreveu:
A) [squad/task A] -- [descricao]
B) [squad/task B] -- [descricao]
C) Nenhuma dessas -- me conte mais

Qual delas?"
```

### BAIXA Confidence (<0.5): Up to 3 questions via entry doors

Present the 4 entry doors. User picks the one that fits their mental state.

```
Como posso te ajudar?

A) "Sei o que quero"
   Diga: Quero [resultado final], a partir de [o que ja tenho], para [quem vai usar].

B) "Tenho um problema"
   Diga: Hoje [situacao atual] e o problema e [o que esta errado].

C) "Quero explorar"
   Diga: Area: [assunto]. Ja sei [X]. Nao sei [Y].

D) Fale livremente
   Descreva sua necessidade e eu faco as perguntas certas.
```

For door D, ask ONLY for missing required slots:
- Q1 (if `action` + `target` missing): "O que voce quer alcancar?"
- Q2 (if `state` missing): "O que existe hoje?"
- Q3 (if `domain` still ambiguous): "Para quem e o resultado?"

Skip any question whose slot was already extracted in Phase 0.

## Phase 2: Hierarchical Classification

Classification uses two levels to reduce search space.

### Level 1: Squad Resolution

1. Read `.mega-brain/squad-runtime/ecosystem-registry.yaml`
2. Match extracted `domain` keywords against squad `keywords` and `description`
3. Rank squads by match score
4. If top squad score > 0.7, select it
5. If top 2-3 squads are close, present disambiguation (Phase 1 MEDIA path)

### Level 2: Task Resolution (within selected squad)

1. Search in order:
   a. `squads/{squad}/tasks/` -- squad-specific tasks
   b. `mega-brain-core/development/tasks/` -- core tasks matching squad domain
   c. `mega-brain-core/manifests/tasks.csv` -- flat index by name/category
   d. `mega-brain-core/data/entity-registry.yaml` -- entity keywords
2. Match `action` + `target` against task names, purposes, and keywords
3. Rank by relevance

### Mode Inference

MODE is never asked -- it is inferred from the gap between desired state and current state.

| User Wants (Q1) | User Has (Q2) | Inferred MODE |
|-----------------|----------------|---------------|
| Something new | Nothing or templates | CRIAR |
| Something new | Existing thing to improve | PLANEJAR |
| "Fix" / "broken" / error | Something with defect | RESOLVER |
| "Understand" / "how" | Something existing | ENTENDER |
| "Validate" / "audit" | Something apparently ready | VALIDAR |
| "Configure" / "setup" | Incomplete environment | CONFIGURAR |
| "Status" / "track" | Process in progress | GERENCIAR |
| "Don't know" / "explore" | Vague or nothing | EXPLORAR |

## Phase 3: Incremental Resolution (Never Invent)

For each step needed to fulfill the user's request, follow this strict protocol.

### Step 3.1: Search for Existing Task

```
For each pipeline step needed:
  1. Grep squad tasks: squads/{squad}/tasks/*.md
  2. Grep core tasks: mega-brain-core/development/tasks/*.md
  3. Grep entity registry: mega-brain-core/data/entity-registry.yaml
  4. Grep tasks manifest: mega-brain-core/manifests/tasks.csv
```

### Step 3.2: Evaluate Match

- **Exact match**: Task exists and its inputs/outputs align. USE IT.
- **Partial match**: Task exists but needs adaptation. PRESENT to user with explanation.
- **No match**: No task found for this step.

### Step 3.3: Handle No Match (Task Gap)

When no existing task matches a pipeline step:

1. **Report transparently**:
   ```
   Nao encontrei uma task existente para: [descricao do step]

   Tasks mais proximas encontradas:
   - [task-a] (squads/{squad}/tasks/) -- [por que nao serve]
   - [task-b] (mega-brain-core/tasks/) -- [por que nao serve]

   Sugestao: Criar uma task nova para [descricao].
   ```

2. **Determine creation target**:
   - If the task belongs to a **squad domain** (content, copy, design, etc.):
     Target: `@squad-chief` via `squads/squad-creator/tasks/create-task.md`
   - If the task belongs to the **Mega Brain core** (general dev, infra, framework):
     Target: `@mega-brain-master` via `mega-brain-core/development/tasks/create-task.md`

3. **Ask user confirmation**:
   ```
   Quer que eu crie essa task?
   - Responsavel: @squad-chief (squad: {squad_name}) | @mega-brain-master (core)
   - A task sera criada ANTES de executar o pipeline
   ```

4. **If user accepts, generate handoff**:

   For **squad task** (via @squad-chief):
   ```yaml
   handoff:
     to: squad-chief
     task: squads/squad-creator/tasks/create-task.md
     input:
       task_purpose: "[what the task should do]"
       squad_name: "[target squad]"
       agent: "[responsible agent in the squad]"
       io_signature:
         inputs: ["[artifacts the task will consume]"]
         outputs: ["[artifacts the task will produce]"]
       context: "[why this task is needed -- from elicitation]"
   ```

   For **core task** (via @mega-brain-master):
   ```yaml
   handoff:
     to: mega-brain-master
     task: mega-brain-core/development/tasks/create-task.md
     input:
       name: "[kebab-case-name]"
       agent: "[responsible agent]"
       purpose: "[what the task does]"
       inputs: ["[input fields]"]
       outputs: ["[output fields]"]
       context: "[why this task is needed]"
   ```

5. **Insert handoff at the BEGINNING of the pipeline**
   (task must exist before it can be executed)

6. **If user declines**, mark the step as `[GAP]` in the pipeline and continue.

### Incrementality Rules (NON-NEGOTIABLE)

1. NEVER invent a task that does not exist in the registries
2. NEVER assume a task exists without searching (grep)
3. ALWAYS show which tasks were found vs which are suggested for creation
4. ALWAYS ask user confirmation before creating any new task
5. Handoff MUST include `io_signature` so create-task knows expected inputs/outputs
6. Created tasks go to the BEGINNING of the pipeline (prerequisite)
7. Mark `[GAP]` when user declines creation -- pipeline continues without that step
8. NEVER skip the search step -- even if you "know" a task exists, verify it

## Phase 4: Pipeline Generation

When multiple tasks are needed, generate a pipeline document.

### Single Task (no pipeline needed)

If resolution finds exactly one task, delegate directly:
```
Encontrei: {task_name} ({squad}/{agent})
Descricao: {task_purpose}
Modo: {YOLO | Interactive | Pre-Flight}

Executar agora?
```

### Multiple Tasks (pipeline)

Generate a markdown pipeline and save to `outputs/me-guia/{slug}/pipeline.md`:

```markdown
# Pipeline: {title from user's goal}
**Gerado por:** me-guia v1.0
**Data:** {YYYY-MM-DD}
**MODE:** {inferred mode}
**Confidence:** {ALTA|MEDIA|BAIXA}

## Contexto
- **Objetivo:** {Q1 answer}
- **Estado atual:** {Q2 answer}
- **Consumidor:** {Q3 answer}

## Steps

### [CRIAR] Step 0: Criar task "{new-task-name}"
- **Handoff:** @squad-chief | @mega-brain-master
- **Task:** create-task
- **Input:** {handoff input yaml}
- **Status:** [ ] Pendente
- **AC:** Task file exists in {path}

### [EXISTENTE] Step 1: {task-name}
- **Squad:** {squad}
- **Agent:** {agent}
- **Task:** {task file path}
- **Input:** {what this step receives}
- **Output:** {what this step produces}
- **Status:** [ ] Pendente
- **AC:** {acceptance criteria}

### [GAP] Step 2: {description}
- **Motivo:** Nenhuma task existente. Usuario declinou criacao.
- **Impacto:** {what is lost by skipping}

## Progresso
- Total steps: {N}
- Existentes: {N}
- A criar: {N}
- Gaps: {N}
```

## Phase 5: Delegation

### Single task
Activate the resolved agent and execute the task directly.
Use the appropriate skill or command: `/SquadName:agents:agent-name` or `@agent-name`.

### Pipeline
1. Present the pipeline to the user for confirmation
2. On confirmation, execute steps sequentially
3. After each step, update the checkbox in the pipeline file
4. Pause at elicitation points (tasks with `has_elicitation: true`)
5. If a step fails, report and ask: continue, skip, or abort

## Phase 6: Resolution Logging

After every invocation, append to `outputs/me-guia/resolution-log.yaml`:

```yaml
- timestamp: "{ISO-8601}"
  user_input: "{raw input}"
  slots_extracted:
    domain: "{value}" # confidence: ALTA|MEDIA|BAIXA
    action: "{value}"
    target: "{value}"
    business: "{value}"
    state: "{value}"
  overall_confidence: "{ALTA|MEDIA|BAIXA}"
  questions_asked: {0-3}
  squad_matched: "{squad or null}"
  tasks_matched: ["{task1}", "{task2}"]
  tasks_created: ["{new-task or empty}"]
  gaps_found: ["{gap descriptions or empty}"]
  pipeline_generated: {true|false}
  user_confirmed: {true|false}
  outcome: "{completed|partial|aborted}"
```

This log drives future improvements:
- Squads with frequent matches get priority for squad-io.yaml creation
- Tasks frequently created via handoff become candidates for permanent inclusion
- Gaps that recur indicate missing capabilities to address

## Registry Files Used

| Registry | Path | Purpose |
|----------|------|---------|
| Ecosystem Registry | `.mega-brain/squad-runtime/ecosystem-registry.yaml` | Squad keywords, descriptions, agent lists |
| Entity Registry | `mega-brain-core/data/entity-registry.yaml` | 498 entities with purpose, keywords |
| Tasks Manifest | `mega-brain-core/manifests/tasks.csv` | 197 tasks with name, category, elicitation flag |
| Squad Tasks | `squads/*/tasks/*.md` | Squad-specific task definitions |
| Core Tasks | `mega-brain-core/development/tasks/*.md` | Core framework task definitions |
| Workspace Templates | `workspace/_templates/` | Template availability for input matching |

## Handoff Targets

| Target | Agent | Task File | When |
|--------|-------|-----------|------|
| Squad task creation | @squad-chief | `squads/squad-creator/tasks/create-task.md` | Gap in squad domain |
| Core task creation | @mega-brain-master | `mega-brain-core/development/tasks/create-task.md` | Gap in core domain |

## What This Skill Does NOT Do

- Does NOT execute tasks itself -- it routes and delegates
- Does NOT create tasks without user confirmation
- Does NOT replace existing workflows (story-cycle, epic-cycle, etc.)
- Does NOT require new registries to function (uses existing ones)
- Does NOT guess when data is insufficient -- asks or reports gaps
