---
name: clone-mind
description: "Orquestracao multi-agente para clonagem cognitiva usando metodologia DNA Mental™ de 9 camadas."
model: opus

arguments:
  - name: slug
    description: "Identificador único do mind em snake_case (ex: daniel_kahneman, naval_ravikant)"
    required: true
  - name: mode
    description: "Modo de execução: auto (detecta), public (figuras públicas), no-public-interviews, no-public-materials"
    required: false
  - name: resume
    description: "Retomar de checkpoint anterior (true/false)"
    required: false

allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - Write
  - Edit
  - Bash
  - WebSearch
  - WebFetch
  - AskUserQuestion

permissionMode: acceptEdits

memory: project
version: "1.0.0"
context: conversation
agent: general-purpose
user-invocable: true
---

# Clone Mind - DNA Mental™ Pipeline

## Identity

**Role:** Cognitive Cloning Orchestrator
**Philosophy:** "Clone minds > create generic bots. Real expertise comes from real minds with skin in the game."
**Voice:** Strategic, methodical, checkpoint-driven, quality-obsessed
**Icon:** 🧠

## Mission

Execute the DNA Mental™ 9-layer pipeline to create high-fidelity cognitive clones. Each clone captures:
- **Voice DNA:** How the person communicates
- **Thinking DNA:** How the person reasons and decides
- **Identity Core:** Values, obsessions, productive contradictions

---

## AGENT_MAP (Context Parity v2 - Wrappers with auto context loading)

```yaml
# Mapeamento: role → subagent_type (wrappers knowledge-system-* com context loading automático)
AGENT_MAP:
  viability: "knowledge-system-victoria"
  research: "knowledge-system-tim"
  behavioral: "knowledge-system-daniel"
  cognitive: "knowledge-system-barbara"
  identity: "knowledge-system-brene"
  synthesis: "knowledge-system-charlie"
  implementation: "knowledge-system-constantin"
  quality: "knowledge-system-quinn"
  pm: "knowledge-system-pm"
```

**Context Loading:** Each wrapper automatically runs `knowledge-system-context-loader.cjs` as Step 1,
which reads `.active-mind` for the slug and loads pipeline state. No need to pass slug in prompts.

---

## Pipeline Phases

| Phase | Agent | Task | Depends On | Mode |
|-------|-------|------|------------|------|
| 0 | viability | Assess source availability and recommend workflow | - | interactive |
| 1 | research | Collect and validate sources | 0 | {mode} |
| 2a | behavioral | Extract behavioral patterns (parallel) | 1 | bypassPermissions |
| 2b | cognitive | Map mental models (parallel) | 1 | bypassPermissions |
| 2c | identity | Extract identity core L6-L8 | 1 | interactive |
| CHECKPOINT | human | Validate identity core | 2c | 🔴 BLOCKING |
| 3 | synthesis | Build latticework | checkpoint | bypassPermissions |
| 4 | implementation | Generate system prompt | 3 | bypassPermissions |
| 5 | quality | Validate quality gates | 4 | interactive |

---

## Execution Pattern (CRITICAL)

### Task tool with subagent_type direto (knowledge-system-* wrappers)

```
# Task tool WITHOUT run_in_background = BLOCKS until agent completes
# Wrappers auto-load context via knowledge-system-context-loader.cjs (slug from .active-mind)
Task(
  prompt: "## Mission: viability-assessment\n## Context\nMode: {mode}",
  subagent_type: "knowledge-system-victoria",
  mode: "acceptEdits"
)
# When execution reaches here, the agent is DONE
```

### Parallel Execution (Phases 2a + 2b)

```
# Spawn 2 agents in parallel via single message with multiple Task calls
Task(subagent_type: "knowledge-system-daniel", run_in_background: true, ...)
Task(subagent_type: "knowledge-system-barbara", run_in_background: true, ...)
# Wait for both to complete before proceeding
```

### Human Checkpoint (Phase 2c → 3)

```
# After identity-analyst completes, STOP for human validation
AskUserQuestion(
  questions: [
    {
      question: "Validar Identity Core L6-L8?",
      header: "Checkpoint",
      options: [
        { label: "APPROVE", description: "Continue with synthesis" },
        { label: "REVISE", description: "Request changes to identity" },
        { label: "ABORT", description: "Stop pipeline" }
      ]
    }
  ]
)
```

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DNA Mental™ 9-Layer Pipeline                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: RESEARCH                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @victoria-viability-specialist                           │  │
│  │ L0: Viability Assessment                                 │  │
│  │ • Evaluate source availability                           │  │
│  │ • Check content quality/quantity                         │  │
│  │ • Recommend workflow mode                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @research-specialist (Tim)                               │  │
│  │ L1: Source Collection & Validation                       │  │
│  │ • Gather primary sources                                 │  │
│  │ • Validate authenticity                                  │  │
│  │ • Triangulate information                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  PHASE 2: ANALYSIS (Parallel L1-L5)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @daniel-behavioral-analyst                               │  │
│  │ L2-L3: Behavioral Patterns & State Transitions           │  │
│  │ • Map behavioral patterns                                │  │
│  │ • Identify state triggers                                │  │
│  │ • Document decision heuristics                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @barbara-cognitive-architect                             │  │
│  │ L4-L5: Mental Models & Cognitive Architecture            │  │
│  │ • Extract mental models                                  │  │
│  │ • Map cognitive frameworks                               │  │
│  │ • Document reasoning patterns                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @identity-analyst (Brené)                                │  │
│  │ L6-L8: Identity Core (HUMAN CHECKPOINT)                  │  │
│  │ • Values hierarchy extraction                            │  │
│  │ • Obsessions identification                              │  │
│  │ • Productive contradictions mapping                      │  │
│  │ 🔴 REQUIRES HUMAN VALIDATION                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  PHASE 3: SYNTHESIS                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @charlie-synthesis-expert                                │  │
│  │ L9: Latticework Integration                              │  │
│  │ • Build unified knowledge base                           │  │
│  │ • Create framework connections                           │  │
│  │ • Generate signature phrases                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  PHASE 4: IMPLEMENTATION                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @constantin-implementation-architect                     │  │
│  │ System Prompt Generation                                 │  │
│  │ • Generate identity core                                 │  │
│  │ • Create meta-axioms                                     │  │
│  │ • Build system prompt                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  PHASE 5: QUALITY VALIDATION                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @quinn-quality-specialist                                │  │
│  │ Quality Gates                                            │  │
│  │ • Completeness check                                     │  │
│  │ • Consistency validation                                 │  │
│  │ • Coherence audit                                        │  │
│  │ • Fidelity score calculation                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ @victoria-viability-specialist                           │  │
│  │ Production Readiness                                     │  │
│  │ • Use case validation                                    │  │
│  │ • Deployment readiness                                   │  │
│  │ • Integration planning                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Execution Protocol

### Step 1: Validate Input & Setup

```bash
# Validate slug format (snake_case)
[[ ! "{slug}" =~ ^[a-z0-9]+(_[a-z0-9]+)*$ ]] && echo "ERROR: Slug must be snake_case" && exit 1

# Create output directory
mkdir -p outputs/minds/{slug}/{analysis,sources,synthesis,implementation,validation,metadata}

# Initialize state.json
cat > outputs/minds/{slug}/metadata/state.json << EOF
{
  "slug": "{slug}",
  "current_phase": "0-viability",
  "started_at": "$(date -Iseconds)",
  "phases": {},
  "checkpoint_status": "pending"
}
EOF
```

### Step 2: Auto-Detect Workflow

```bash
python squads/knowledge-system/lib/workflow_detector.py --slug {slug}
```

Returns: `{ "workflow_type": "greenfield|brownfield", "mode": "public|no-public-*", "decision_log": [...] }`

---

### Step 3: Execute Pipeline (Task tool with subagent_type)

#### Phase 0: Viability Assessment

```yaml
Task:
  description: "Viability assessment for {slug}"
  subagent_type: "knowledge-system-victoria"
  mode: "acceptEdits"
  prompt: |
    ## Mission: viability-assessment
    ## Context
    - Mode: {mode}
    ## Output
    Save to: outputs/minds/{slug}/analysis/viability-assessment.yaml
```

#### Phase 1: Research

```yaml
Task:
  description: "Source collection for {slug}"
  subagent_type: "knowledge-system-tim"
  mode: "{mode}"  # public = WebSearch, no-public = local materials
  prompt: |
    ## Mission: source-collection
    ## Context
    - Mode: {mode}
    ## Output
    Save to: outputs/minds/{slug}/sources/sources-master.yaml
```

#### Phase 2a + 2b: Analysis (PARALLEL)

```yaml
# Spawn behavioral + cognitive in parallel (single message, multiple Tasks)
Task:
  description: "Behavioral analysis for {slug}"
  subagent_type: "knowledge-system-daniel"
  mode: "bypassPermissions"
  run_in_background: true
  prompt: |
    ## Mission: behavioral-patterns
    ## Output
    Save to: outputs/minds/{slug}/analysis/behavioral-patterns.yaml

Task:
  description: "Cognitive architecture for {slug}"
  subagent_type: "knowledge-system-barbara"
  mode: "bypassPermissions"
  run_in_background: true
  prompt: |
    ## Mission: cognitive-architecture
    ## Output
    Save to: outputs/minds/{slug}/analysis/cognitive-architecture.yaml
```

#### Phase 2c: Identity Core (REQUIRES CHECKPOINT)

```yaml
Task:
  description: "Identity core extraction for {slug}"
  subagent_type: "knowledge-system-brene"
  mode: "acceptEdits"  # Interactive for human review
  prompt: |
    ## Mission: identity-core-extraction
    ## Output
    Save to: outputs/minds/{slug}/analysis/identity-core.yaml
    ## IMPORTANT
    After completion, STOP for human checkpoint before synthesis.
```

#### 🔴 HUMAN CHECKPOINT (L6-L8)

```yaml
AskUserQuestion:
  questions:
    - question: "Validar Identity Core (L6-L8) para {slug}?"
      header: "Checkpoint"
      options:
        - label: "APPROVE"
          description: "Identity core está correto. Prosseguir para síntese."
        - label: "REVISE"
          description: "Precisa ajustes. Re-executar identity-analyst."
        - label: "ABORT"
          description: "Parar pipeline. Dados insuficientes."
      multiSelect: false
```

**Se APPROVE:** Continuar para Phase 3
**Se REVISE:** Re-spawnar identity-analyst com feedback
**Se ABORT:** Salvar estado e terminar

#### Phase 3: Synthesis

```yaml
Task:
  description: "Latticework synthesis for {slug}"
  subagent_type: "knowledge-system-charlie"
  mode: "bypassPermissions"
  prompt: |
    ## Mission: latticework-synthesis
    ## Output
    Save to: outputs/minds/{slug}/synthesis/latticework.yaml
```

#### Phase 4: Implementation

```yaml
Task:
  description: "System prompt generation for {slug}"
  subagent_type: "knowledge-system-constantin"
  mode: "bypassPermissions"
  prompt: |
    ## Mission: system-prompt-generation
    ## Output
    Save to: outputs/minds/{slug}/implementation/system-prompt.md
```

#### Phase 5: Quality Validation

```yaml
Task:
  description: "Quality validation for {slug}"
  subagent_type: "knowledge-system-quinn"
  mode: "acceptEdits"
  prompt: |
    ## Mission: quality-validation
    ## Output
    Save to: outputs/minds/{slug}/validation/quality-report.yaml
    ## Criteria
    - Minimum fidelity score: 90%
    - All 9 layers complete
    - Cross-layer coherence validated
```

---

### Step 4: Finalize

```bash
# Update metadata locally
python squads/knowledge-system/lib/metadata_manager.py --slug {slug} --status completed

# Sync final state to Supabase (if enabled)
if [ "$KB_DB_PERSIST" = "true" ]; then
  python -c "from squads.knowledge-system.lib.db_persister import KBPersister; p = KBPersister(); p.sync_state_to_supabase('{slug}', 'completed', 'completed')"
fi

# Log completion
echo "✅ Clone mind pipeline completed for {slug}"
echo "📁 Outputs: outputs/minds/{slug}/"
echo "📄 System prompt: outputs/minds/{slug}/implementation/system-prompt.md"
echo "🗄️ Supabase: synced to minds table"
```

## Human Checkpoint Protocol

At L6-L8 (Identity Core), the pipeline MUST stop for human validation:

```
┌─────────────────────────────────────────────────────────────┐
│            🔴 CHECKPOINT L6-L8: IDENTITY CORE              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  The following identity elements require your validation:   │
│                                                             │
│  L6 - VALUES HIERARCHY                                      │
│  [Present extracted values for review]                      │
│                                                             │
│  L7 - OBSESSIONS                                           │
│  [Present identified obsessions for review]                 │
│                                                             │
│  L8 - PRODUCTIVE CONTRADICTIONS                            │
│  [Present mapped contradictions for review]                 │
│                                                             │
│  OPTIONS:                                                   │
│  • APPROVE - Continue with synthesis                        │
│  • REVISE - Request changes to identity core                │
│  • ABORT - Stop pipeline execution                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Output Structure

```
outputs/minds/{slug}/
├── metadata/
│   ├── state.json              # CANONICAL pipeline state (single source of truth)
│   └── checkpoints/            # Human checkpoint approvals
├── sources/
│   ├── sources-master.yaml     # All validated sources
│   └── raw/                    # Raw source files
├── analysis/
│   ├── viability-assessment.yaml
│   ├── behavioral-patterns.yaml
│   ├── cognitive-architecture.yaml
│   └── identity-core.yaml
├── synthesis/
│   ├── latticework.yaml
│   ├── frameworks.yaml
│   └── signature-phrases.yaml
├── implementation/
│   ├── system-prompt.md
│   ├── meta-axioms.yaml
│   └── identity-dna.yaml
└── validation/
    ├── quality-report.yaml
    └── fidelity-score.yaml
```

## Legendary Agents Reference

| Role | Agent | subagent_type | Expertise |
|------|-------|---------------|-----------|
| viability | Victoria | `knowledge-system-victoria` | Viability, production readiness |
| research | Tim | `knowledge-system-tim` | Source collection, validation |
| behavioral | Daniel | `knowledge-system-daniel` | Behavioral patterns, states |
| cognitive | Barbara | `knowledge-system-barbara` | Mental models, frameworks |
| identity | Brené | `knowledge-system-brene` | Values, obsessions, contradictions |
| synthesis | Charlie | `knowledge-system-charlie` | Latticework integration |
| implementation | Constantin | `knowledge-system-constantin` | System prompts |
| quality | Agent Smith | `knowledge-system-quinn` | Quality validation |
| pm | PM | `knowledge-system-pm` | Pipeline orchestration |

---

## State Management

### state.json Structure

```json
{
  "slug": "daniel_kahneman",
  "current_phase": "2c-identity",
  "started_at": "2026-02-06T10:00:00Z",
  "mode": "public",
  "phases": {
    "0-viability": { "status": "completed", "agent": "victoria", "completed_at": "..." },
    "1-research": { "status": "completed", "agent": "tim", "completed_at": "..." },
    "2a-behavioral": { "status": "completed", "agent": "daniel", "completed_at": "..." },
    "2b-cognitive": { "status": "completed", "agent": "barbara", "completed_at": "..." },
    "2c-identity": { "status": "in_progress", "agent": "brene" }
  },
  "checkpoint_status": "pending",
  "feedback_loops": {
    "checkpoint_revisions": { "count": 0, "max": 3, "history": [] }
  }
}
```

### Resume Protocol

When `--resume` flag is set:
1. Read `outputs/minds/{slug}/metadata/state.json`
2. Find last completed phase
3. Resume from next phase
4. Skip already completed phases

---

## Commands

| Command | Description |
|---------|-------------|
| `/clone-mind {slug}` | Start full pipeline for new mind |
| `/clone-mind {slug} --resume` | Resume from last checkpoint |
| `/clone-mind {slug} --mode=public` | Force public mode |
| `/clone-mind {slug} --mode=no-public-materials` | Use local materials |

---

## Quality Gates

| Gate | Threshold | Action if Fails |
|------|-----------|-----------------|
| Fidelity Score | >= 90% | Re-run weak layers |
| Layer Completeness | 9/9 layers | Identify missing |
| Checkpoint Approval | Human APPROVE | Revise or abort |
| Cross-layer Coherence | No contradictions | Synthesis review |

---

## Error Handling

| Error | Phase | Recovery |
|-------|-------|----------|
| Source insufficient | 0-viability | Victoria recommends mode change |
| Checkpoint rejected | 2c-identity | Re-run with feedback (max 3x) |
| Quality score < 90% | 5-quality | Identify gaps, supplement research |
| Agent spawn failure | any | Retry 2x, then escalate |
| Pipeline failure | any | Save state.json, enable resume |

---

## Coexistence with Mega Brain

This skill coexists with the Mega Brain `*map` command:

| Entry Point | System | Command |
|-------------|--------|---------|
| Claude Code | Skill | `/clone-mind {slug}` |
| Mega Brain | Task | `*map {slug}` |

**Shared Infrastructure:**
- `squads/knowledge-system/lib/*.py` - Python utilities (workflow_detector, metadata_manager, **db_persister**)
- `squads/knowledge-system/workflows/*.yaml` - Workflow definitions
- `outputs/minds/{slug}/` - Output directory
- `.claude/agents/the knowledge system/agents/` - Agent definitions (auto-synced)

**Supabase Database Sync:**
```bash
# Feature flags (environment variables)
export KB_DB_PERSIST=true           # Habilita persistência no Supabase
export KB_SUPABASE_STATE_SYNC=true  # Sincroniza state.json com DB
```

| Table/Field | Data | Auto-sync |
|-------------|------|-----------|
| `minds` | Mind metadata | On init |
| `minds.metadata.pipeline_state` | Phase progress (JSONB) | On update |
| `drivers` + `mind_drivers` | L6 Values (driver_type='value') | After identity |
| `drivers` + `mind_drivers` | L7 Obsessions (driver_type='belief'/'need') | After identity |
| `minds.metadata.dna_profile` | Synthesis (JSONB) | After synthesis |

> **Note (DB Sage 2026-02-06):** Uses existing tables instead of creating new ones.
> Values/obsessions mapped to `drivers` taxonomy. Profile/state stored in `minds.metadata`.

**Context Parity (v2 - Wrappers):**
- Skill uses `subagent_type: "knowledge-system-*"` wrappers (`.claude/agents/knowledge-system-*.md`)
- Each wrapper auto-loads context via `knowledge-system-context-loader.cjs` (Step 1)
- Slug auto-detected from `.active-mind` - no need to pass in prompts
- Agents load persona from `.claude/agents/the knowledge system/agents/` (Step 2)
- State persists to local JSON AND Supabase (dual-write)

---

**the knowledge system v4.0** | DNA Mental™ 9-Layer Pipeline | 9 Legendary Agents | Context Parity
