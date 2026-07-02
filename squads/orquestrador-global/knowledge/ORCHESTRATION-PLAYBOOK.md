# Orchestration Playbook — Multi-Squad Execution

**Version:** 1.0.0
**Squad:** orquestrador-global
**Last Updated:** 2026-03-11

---

## Purpose

This playbook defines how to orchestrate multi-squad executions: from demand classification to consolidated delivery. It covers demand routing decisions, dependency mapping, parallel execution patterns, stage gate protocols, conflict resolution, and logging standards.

The `orquestrador-global` is the central nervous system of Mega Brain. When a demand arrives that requires more than one squad, this playbook governs how it gets executed.

---

## 1. Demand Classification

### 1.1 Classification Framework

Every demand that arrives at the orchestrator goes through classification before routing:

**Step 1: Identify the demand type**

| Demand Type | Description | Example |
|------------|-------------|---------|
| `content` | Content production (copy, vídeo, social, email) | "Escreve um VSL para o MPG" |
| `marketing` | Campaign strategy, ads, funnels, launches | "Preciso de um funil completo para GPO" |
| `dev` | Code, integrations, automations, platforms | "Cria automação no n8n para sequência de emails" |
| `advisory` | Strategic decision, analysis, planning | "Qual é a melhor estratégia de lançamento?" |
| `research` | Market research, competitor analysis, data | "Analisa o mercado de pós-operatório" |
| `operations` | Project tracking, reporting, process improvement | "Atualiza o status de todas as campanhas ativas" |

**Step 2: Identify demand scope**

| Scope | Squads Required | Duration | Log Required |
|-------|----------------|----------|-------------|
| `single` | 1 squad | < 30 min | No |
| `sequential` | 2-3 squads in order | 1-4 hours | Yes |
| `parallel` | 2-4 squads simultaneously | 1-4 hours | Yes |
| `campaign` | 4-7 squads | 1-3 days | Yes |
| `launch` | 8+ squads | Days-weeks | Yes (full execution log) |

**Step 3: Identify the entry point**

- Single squad → route directly, do not create orchestration overhead
- Multi-squad → proceed to dependency mapping and execution plan

### 1.2 Classification Decision Tree

```
Demand arrives
    │
    ▼
Ambiguous? ─Yes─→ Ask clarifying question (max 1)
    │No
    ▼
Single squad sufficient? ─Yes─→ Route directly to squad chief
    │No
    ▼
Dependencies between squads? ─No─→ Parallel execution plan
    │Yes
    ▼
Sequential dependencies → Sequential execution plan
    │
    ▼
Critical path identified? ─No─→ Map dependencies first
    │Yes
    ▼
Create execution plan → Log → Execute
```

---

## 2. Squad Selection Criteria

### 2.1 Primary Squad Routing Rules

When a demand arrives, select squads based on:

**Rule 1: Match domain to squad's primary domain**

| Demand Domain | Primary Squad | Backup Squad |
|--------------|--------------|-------------|
| Sales copy (VSL, sales letter, email sequences) | `copywriting` | — |
| Paid advertising (Meta, Google, TikTok) | `traffic-squad` | `media-buy` |
| Visual creative assets | `creative-studio` | — |
| Landing pages, funnels, HTML | `funnel-creator` | `design-system` |
| Course content, curriculum | `infoproduct-creation` | — |
| SEO content strategy | `seo` | `copywriting` |
| Organic social content | `content-ecosystem` | `copywriting` |
| Market analysis | `market-research` | `data-analytics` |
| CRM automations | `marketing-automation` | `full-stack-dev` |
| Platform development | `full-stack-dev` | `core-dev` |
| Strategic decisions | `conselho` | — |
| YouTube lives | `youtube-lives` | `content-ecosystem` |
| Vídeo production | `video-production` | `media-production` |

**Rule 2: Prefer quality over speed**

If the demand is high-stakes (launch, premium product, high-budget campaign), activate the specialist squad even if it takes longer. Do not route to generalist squads to save time.

**Rule 3: Check squad load before assignment**

If a squad has more than 3 active tasks in ClickUp with status "In Progress", note the load and either:
- Queue the demand (add to backlog with priority)
- Split the demand and route sub-components to available squads

### 2.2 Multi-Squad Demand Examples

**Full funnel creation:**
```
copywriting (sales copy)
    + funnel-creator (HTML/landing page)
    + creative-studio (visual assets)
    + traffic-squad (ad strategy)
```

**Product launch:**
```
copywriting (launch emails + VSL)
    + funnel-creator (funnel pages)
    + creative-studio (creatives)
    + traffic-squad (paid traffic)
    + marketing-automation (email sequences)
    + content-ecosystem (organic content)
    + youtube-lives (live event)
    + conselho (launch strategy review)
```

**Content repurposing sprint:**
```
content-ecosystem (original long-form)
    + copywriting (email adaptation)
    + creative-studio (social visuals)
    + seo (optimization)
```

---

## 3. Dependency Mapping

### 3.1 Types of Dependencies

| Dependency Type | Description | Action Required |
|----------------|-------------|----------------|
| `hard-sequential` | Squad B cannot start until Squad A delivers | Force sequential order |
| `soft-sequential` | Squad B is better with Squad A's output, but can start | Brief Squad B with best available info, update when A delivers |
| `parallel-independent` | Squads can work simultaneously with no dependencies | Schedule for parallel execution |
| `feedback-loop` | Squad A needs feedback from Squad B's output to optimize | Plan for one feedback iteration |

### 3.2 Common Dependency Patterns

**Copy → Creative dependency (hard-sequential):**
Copy must be produced before creative assets. The visual team needs headlines, CTAs, and copy angles before generating images. Do not start creative production without at minimum:
- Primary headline
- CTA text
- Product name and key benefit

**Strategy → Execution dependency (soft-sequential):**
For launches, the `conselho` strategic review should precede execution squads starting. However, if the strategy is well-defined, execution can begin while `conselho` reviews.

**Creative → Traffic dependency (soft-sequential):**
Ad assets should be ready before traffic squad launches campaigns. However, traffic squad can prepare targeting, audience, and campaign structure while creatives are being produced.

**Dev → Marketing automation dependency (hard-sequential):**
Any automation workflows in n8n or ActiveCampaign need to be built and tested before a live campaign launches sequences.

### 3.3 Dependency Map Format

```yaml
# Example: Full Funnel Demand
demand_id: "2026-03-11_funil-mcpm-lancamento"
squads:
  - id: "copywriting"
    tasks: ["VSL script", "landing page copy", "email sequence (7 emails)"]
    depends_on: []  # starts first
    estimated_duration: "4 hours"

  - id: "funnel-creator"
    tasks: ["landing page HTML", "upsell page", "obrigado page"]
    depends_on: ["copywriting"]  # needs copy first
    estimated_duration: "3 hours"

  - id: "creative-studio"
    tasks: ["hero image", "ad creatives (5 variants)"]
    depends_on: ["copywriting"]  # needs headlines and CTAs
    estimated_duration: "2 hours"

  - id: "traffic-squad"
    tasks: ["campaign structure", "targeting setup"]
    depends_on: ["creative-studio", "funnel-creator"]  # needs all assets
    estimated_duration: "1 hour"
```

---

## 4. Parallel Execution Patterns

### 4.1 When to Parallelize

Parallelize when:
- Two squads have no dependencies between them
- Both squads' outputs are needed for a third downstream squad
- Time is a constraint (launch deadline)

Do NOT parallelize when:
- One squad's output fundamentally shapes the other's work
- Budget is limited and sequential would catch problems early
- The orchestrator cannot monitor multiple squads simultaneously

### 4.2 Parallel Execution Coordination Protocol

When running squads in parallel:

1. **Brief all parallel squads simultaneously** — send briefs at the same time
2. **Set sync checkpoints** — agree on when squads will check in (e.g., at 50% completion)
3. **Define merge point** — which squad consolidates the outputs? (usually the orchestrator)
4. **Conflict resolution rule** — if parallel squads produce conflicting outputs, which takes priority?

**Priority hierarchy when parallel squads conflict:**
1. Copy (messaging) takes priority over visual (creative must match copy)
2. Strategy (conselho) takes priority over execution squads
3. User feedback overrides any squad's recommendation

### 4.3 Wave-Based Execution

For complex multi-squad executions, organize into waves:

```
Wave 1 (Parallel): Research + Strategy
    market-research + conselho
    ↓
Wave 2 (Parallel): Content Production
    copywriting + creative-studio
    ↓
Wave 3 (Parallel): Implementation
    funnel-creator + marketing-automation
    ↓
Wave 4 (Parallel): Launch
    traffic-squad + content-ecosystem + youtube-lives
    ↓
Wave 5 (Parallel): Monitoring
    data-analytics + traffic-squad
```

---

## 5. Stage Gate Protocols

### 5.1 What Is a Stage Gate?

A stage gate is a mandatory review checkpoint before the execution moves to the next wave or squad. Gates prevent wasteful rework by catching problems before they compound.

**Gate decision options:**
- `approved` — proceed to next stage
- `approved-with-conditions` — proceed but note specific required changes
- `revised` — revise current stage outputs before proceeding
- `paused` — user needs to provide additional information
- `cancelled` — demand cancelled or fundamentally changed

### 5.2 Gate Configuration by Demand Scale

| Scale | Gates Required | Gate Authority |
|-------|---------------|---------------|
| `QUICK` (< 30 min) | No gates | Self-approved |
| `SMALL` (1-2 squads) | 1 gate at completion | Orchestrator |
| `MEDIUM` (2-4 squads) | Gate after Wave 1, gate at completion | User review |
| `LARGE` (4+ squads) | Gate after each wave | User review required |
| `EPIC` / `LAUNCH` | Gate after every squad delivers | User review required |

### 5.3 Gate Review Format

When presenting a gate review to the user:

```markdown
## Stage Gate Review — {Demand Title}

**Current Stage:** Wave 1 — Research + Strategy
**Squads Completed:** market-research, conselho
**Next Stage:** Wave 2 — Copy + Creative

### Deliverables Produced
1. market-research: [summary of key findings]
2. conselho: [strategic recommendations]

### Files Generated
- .data/executions/{dir}/01-market-research-output.md
- .data/executions/{dir}/01-conselho-output.md

### Recommendation
[Orchestrator recommendation for next wave]

### Gate Question
Approve to proceed with Wave 2 (copywriting + creative-studio)?
[ ] Approved
[ ] Approved with conditions: ___
[ ] Request revisions: ___
[ ] Pause — additional info needed: ___
```

---

## 6. Conflict Resolution

### 6.1 Types of Conflicts

**Output conflicts:** Two squads produce outputs that contradict each other.
- Example: copywriting produces "R$297" price; funnel-creator uses "R$247" on the page.
- Resolution: Apply `.claude/rules/copy-consistency-review.md` — copy takes priority on all factual claims.

**Priority conflicts:** Two squads claim the same resource or timeline slot.
- Resolution: Higher-impact squad (revenue-generating) takes priority over supporting squad.

**Scope conflicts:** Squad interprets the brief differently than intended.
- Resolution: Always return to the original user request as the source of truth. Re-brief the squad.

**Quality conflicts:** Squad A delivers below the minimum standard required by Squad B.
- Resolution: The receiving squad (B) documents the specific deficiency. Orchestrator sends back to Squad A for revision before B proceeds.

### 6.2 Escalation Path

```
Conflict detected
    │
    ▼
Can be resolved with existing brief? ─Yes─→ Orchestrator resolves + logs decision
    │No
    ▼
Impacts user-facing deliverable? ─Yes─→ Escalate to user for decision
    │No (internal only)
    ▼
Orchestrator applies priority rules + logs reasoning
```

---

## 7. Execution Logging Best Practices

### 7.1 Mandatory Logging Events

Log to `.data/executions/{YYYY-MM-DD}_{slug}/`:

| Event | File to Create | When |
|-------|---------------|------|
| Plan approved | `00-master-plan.md` | Before any squad starts |
| Squad receives brief | `{NN}-{squad}-input.md` | Before squad begins |
| Squad delivers | `{NN}-{squad}-output.md` | After squad completes |
| Gate decision | Append to audit.jsonl | At every gate |
| Execution complete | `99-execution-summary.md` | After all squads done |

### 7.2 Audit Trail Commands

```bash
# Set execution scale at start
node core/scripts/ops/ids-ops.mjs set-scale MEDIUM

# Log squad start
node core/scripts/ops/ids-ops.mjs audit-append \
  --dir="2026-03-11_funil-mcpm" \
  --agent=roteador \
  --action=squad_started \
  --details='{"squad":"copywriting","task":"VSL script"}'

# Log stage gate
node core/scripts/ops/ids-ops.mjs audit-append \
  --dir="2026-03-11_funil-mcpm" \
  --agent=roteador \
  --action=stage_gate \
  --details='{"stage":1,"decision":"approved","squads_completed":["copywriting"]}'

# Log completion
node core/scripts/ops/ids-ops.mjs audit-append \
  --dir="2026-03-11_funil-mcpm" \
  --agent=roteador \
  --action=execution_complete \
  --details='{"status":"success","squads":4,"duration_hours":6}'
```

### 7.3 SuperMemory Backup

After any multi-squad execution, save summary to SuperMemory:

```yaml
containerTag: "megabrain-master"
content: |
  tipo: execucao_multi-squad
  data: YYYY-MM-DD
  demanda: [título da demanda]
  squads: [lista de squads]
  resultado: [status e entregáveis principais]
  aprendizado: [o que funcionou / o que melhorar]
  logs: .data/executions/{dir}/
```

---

## 8. Performance Metrics for Orchestration

### 8.1 Orchestration KPIs

Track these metrics per execution:

| Metric | Definition | Target |
|--------|-----------|--------|
| Routing accuracy | % of demands routed to correct squad on first try | > 90% |
| Re-routing rate | % of demands that needed re-routing | < 10% |
| Gate approval rate | % of gates that pass without revision requested | > 75% |
| On-time delivery | % of executions completed within estimated duration | > 80% |
| Conflict rate | Conflicts per 10 multi-squad executions | < 2 |

### 8.2 Continuous Improvement

After each execution, the orchestrator should assess:
- Was the demand classified correctly?
- Were the right squads selected?
- Were dependencies identified before they caused rework?
- Did the stage gates catch problems early?
- What would be done differently?

Document insights in SuperMemory (`containerTag: megabrain-master`) for future reference.

---

*Playbook Version: 1.0.0 | Created: 2026-03-11*
*References: MULTI-SQUAD-PLAYBOOK.md, ORCHESTRATION-MATURITY-FRAMEWORK.md, ORCHESTRATION-PROCESS.md*
*Tools: ids-ops.mjs, execution-logging.md*
