# Squad Router -- Intelligent Agent Routing

> **Auto-Trigger:** qual agente, quem responde, who handles, delegar, delegate, route task, squad router
> **Keywords:** "squad-router", "/squad-router", "/route", "qual agente", "quem responde", "who handles", "delegate", "delegar tarefa", "route task", "which agent"
> **Prioridade:** ALTA
> **Tools:** Read (AGENT-INDEX, agent files)

## When NOT to Activate

- Direct slash commands that already target a specific agent or skill
- Conclave sessions (use `/conclave`)
- Pipeline execution (use `/pipeline-mce`)
- JARVIS briefing (use `/jarvis-briefing`)

---

## WHAT THIS SKILL DOES

Single source of truth for task delegation. Answers "which agent handles this?"
by matching the user's intent against a decision tree covering all 40+ agents
in the system: AIOX native agents, Knowledge Ops squad (kops-*), Dev Ops squad
(dops-*), cargo agents, external expert mind-clones, and conclave council.

## EXECUTION

### Step 1: Classify the Task Domain

Read the user's request and classify it into ONE of these domains:

| # | Domain | Description |
|---|--------|-------------|
| 1 | DEVELOPMENT | Writing code, fixing bugs, implementing features |
| 2 | ARCHITECTURE | System design, tech decisions, structure, routing |
| 3 | QUALITY | Testing, validation, reviews, quality gates |
| 4 | DEPLOYMENT | Git push, PRs, releases, CI/CD, branching |
| 5 | PLANNING | PRDs, epics, stories, sprint planning, estimates |
| 6 | KNOWLEDGE-OPS | Pipeline processing, ingestion, extraction, DNA, agents |
| 7 | SALES | Closing, objection handling, scripts, compensation, NEPQ |
| 8 | BUSINESS-OPS | C-level strategy, marketing, revenue, finance, operations |
| 9 | EXPERT-CONSULT | Ask a specific expert for their methodology or framework |
| 10 | DELIBERATION | Multi-perspective debate, council session |
| 11 | DATA | Database schema, queries, ETL, RAG, knowledge graph |
| 12 | DESIGN | UI/UX, frontend design, wireframes, design systems |

### Step 2: Route Using the Decision Tree

---

## DECISION TREE

### Domain 1: DEVELOPMENT

```
Is the task about writing or modifying Python/JS code?
  YES --> Is it a Mega Brain core/ script or hook?
    YES --> dops-anvil (Feature Builder)
           Path: agents/system/dev-ops/anvil/
           "Built it. From scratch. Works."
    NO  --> @dev (Neo)
           AIOX native dev agent
           General-purpose code implementation
```

**Signal words:** build, implement, code, fix, bug, refactor, script, function, class, module, create file, write code

---

### Domain 2: ARCHITECTURE

```
Is the task about system structure or technical decisions?
  YES --> Is it Mega Brain internal architecture (buckets, routing, paths)?
    YES --> dops-compass (System Architect)
           Path: agents/system/dev-ops/compass/
           "Why this way and not that way?"
    NO  --> @architect (The Architect)
           AIOX native architect agent
           Full-stack system architecture, tech stack, API design
```

**Signal words:** architecture, design system, tech stack, structure, routing, API, trade-off, infrastructure, scale, deployment strategy

---

### Domain 3: QUALITY

```
Is the task about testing or validation?
  YES --> Is it MCE pipeline validation (chunk_ids, DNA fidelity)?
    YES --> kops-lens (Quality Curator)
           Path: agents/system/knowledge-ops/lens/
           "Show me the chunk_id."
    NO  --> Is it code testing (pytest, unit tests, integration)?
      YES --> dops-hawk (Quality Tester)
             Path: agents/system/dev-ops/hawk/
             "Did you test the edge case?"
      NO  --> @qa (Agent Smith)
             AIOX native QA agent
             General quality gates, code reviews, acceptance criteria
```

**Signal words:** test, validate, review, quality, coverage, regression, edge case, verify, check, lint

---

### Domain 4: DEPLOYMENT

```
Is the task about git operations or shipping?
  YES --> Is it Mega Brain git ops (staging, commits, PRs)?
    YES --> dops-rocket (Git Deployer)
           Path: agents/system/dev-ops/rocket/
           "Staged. Committed. Clean."
    NO  --> @devops (Link)
           AIOX native devops agent
           CI/CD, releases, infrastructure, git push
```

**CRITICAL RULE:** Only @devops and dops-rocket can execute `git push`. All other agents MUST delegate push operations to one of these two.

**Signal words:** push, commit, branch, PR, pull request, release, deploy, tag, merge, CI/CD, pipeline (CI), staging

---

### Domain 5: PLANNING

```
Is the task about planning or prioritization?
  YES --> Is it a PRD or product strategy?
    YES --> @pm (Niobe)
           AIOX native PM agent
           PRDs, product vision, feature strategy
    NO  --> Is it story creation or sprint structure?
      YES --> @sm (The Keymaker)
             AIOX native SM agent
             Stories, DoD, sprint planning, ceremonies
      NO  --> Is it backlog prioritization or acceptance criteria?
        YES --> @po (Seraph)
               AIOX native PO agent
               Backlog ordering, RICE/MoSCoW, AC refinement
        NO  --> dops-beacon (Strategic Planner)
               Path: agents/system/dev-ops/beacon/
               "The plan is the product."
               Phase breakdowns, effort estimates, epic structures
```

**Signal words:** plan, PRD, story, epic, sprint, backlog, priority, estimate, acceptance criteria, DoD, roadmap

---

### Domain 6: KNOWLEDGE-OPS (MCE Pipeline)

```
Is the task about content processing or knowledge extraction?
  YES --> Which pipeline step?

    CLASSIFY / ROUTE content:
      --> kops-atlas (Bucket Classifier)
          Path: agents/system/knowledge-ops/atlas/
          "Classified. Routed. Next."
          Uses: scope_classifier.py, smart_router.py

    EXTRACT knowledge (chunks, DNA, insights, MCE):
      --> kops-sage (Knowledge Extractor)
          Path: agents/system/knowledge-ops/sage/
          "Every insight has a source. Every source has a chunk."
          Uses: MCE prompt chain, chunker, entity extraction

    VALIDATE extraction quality:
      --> kops-lens (Quality Curator)
          Path: agents/system/knowledge-ops/lens/
          "Show me the chunk_id."
          Uses: 7 MCE validation checks

    COMPILE dossiers / cascade knowledge:
      --> kops-forge (Knowledge Compiler)
          Path: agents/system/knowledge-ops/forge/
          "Built. Linked. Delivered."
          Uses: dossier_compiler.py, cascading rules

    GENERATE agent files (AGENT.md, SOUL.md, MEMORY.md):
      --> kops-echo (Agent Cloner)
          Path: agents/system/knowledge-ops/echo/
          "Every agent is a faithful reflection of its sources."
          Uses: Template V3.2, activation_generator.py

    FULL PIPELINE (all steps):
      --> Use /pipeline-mce skill directly
          The skill orchestrates kops-* agents in sequence
```

**Signal words:** ingest, process, extract, DNA, chunk, MCE, pipeline, classify, bucket, dossier, compile, clone, agent creation, knowledge, insight

---

### Domain 7: SALES

```
Is the task about sales methodology or execution?
  YES --> What specific area?

    CLOSING / objection handling / scripts:
      --> closer (Cargo Agent)
          Path: agents/cargo/sales/closer/

    PROSPECTING / outbound / cold outreach:
      --> bdr (Cargo Agent)
          Path: agents/cargo/sales/bdr/

    INBOUND / lead qualification:
      --> sds (Cargo Agent)
          Path: agents/cargo/sales/sds/

    LINKEDIN / social selling:
      --> lns (Cargo Agent)
          Path: agents/cargo/sales/lns/

    NEPQ methodology / question-based selling:
      --> nepq-specialist (Cargo Agent)
          Path: agents/cargo/sales/nepq-specialist/

    SALES TEAM coordination / pipeline management:
      --> sales-coordinator (Cargo Agent)
          Path: agents/cargo/sales/sales-coordinator/

    SALES LEADERSHIP / team strategy:
      --> sales-lead (Cargo Agent)
          Path: agents/cargo/sales/sales-lead/

    SALES MANAGEMENT / KPIs / coaching:
      --> sales-manager (Cargo Agent)
          Path: agents/cargo/sales/sales-manager/

    CUSTOMER SUCCESS / retention / churn:
      --> customer-success (Cargo Agent)
          Path: agents/cargo/sales/customer-success/

    REVENUE STRATEGY (cross-cutting):
      --> cro (C-Level Cargo Agent)
          Path: agents/cargo/c-level/cro/
```

**Signal words:** close, sell, prospect, lead, pipeline (sales), objection, script, commission, compensation, NEPQ, customer success, churn, upsell, retention

---

### Domain 8: BUSINESS-OPS

```
Is the task about business strategy or operations?
  YES --> What functional area?

    FINANCE / budgets / P&L / cash flow:
      --> cfo (C-Level Cargo Agent)
          Path: agents/cargo/c-level/cfo/

    REVENUE / growth / monetization:
      --> cro (C-Level Cargo Agent)
          Path: agents/cargo/c-level/cro/

    MARKETING strategy / brand / positioning:
      --> cmo (C-Level Cargo Agent)
          Path: agents/cargo/c-level/cmo/

    OPERATIONS / processes / team management:
      --> coo (C-Level Cargo Agent)
          Path: agents/cargo/c-level/coo/

    PAID MEDIA / ads / traffic:
      --> paid-media-specialist (Cargo Agent)
          Path: agents/cargo/marketing/paid-media-specialist/

    MARKET RESEARCH / competitive analysis:
      --> @analyst (Merovingian)
          AIOX native analyst agent
```

**Signal words:** finance, budget, revenue, marketing, operations, P&L, strategy, ads, traffic, brand, ROI, ROAS, CAC, LTV

---

### Domain 9: EXPERT-CONSULT

```
Does the user want to consult a specific expert's methodology?
  YES --> Route to the matching external mind-clone agent.

  Available experts (agents/external/):
    alex-hormozi     --> Offers, pricing, value equation, scaling
    cole-gordon      --> Sales systems, closer training, remote sales
    jeremy-haynes    --> Paid media, ad agencies, client acquisition
    jeremy-miner     --> NEPQ, question-based selling
    jordan-lee       --> Agency scaling, ops, SOPs
    liam-ottley      --> AI automation agencies, AAA model
    pedro-valerio    --> Brazilian digital marketing, launches
    richard-linder   --> Paid traffic, media buying
    sam-oven          --> Consulting, funnels, mindset
    alan-nicolas     --> AI agents, prompt engineering
    g4-educacao      --> Education methodology
    the-scalable-company --> Scaling playbook

  Activation: Use /conclave for multi-expert debate,
              or /ask {expert-slug} for single-expert consultation.
```

**Signal words:** Hormozi, Cole, Jeremy, offer, value equation, NEPQ, agency, consulting, scaling, ask [name]

---

### Domain 10: DELIBERATION

```
Does the task require multi-perspective analysis?
  YES --> /conclave
         Activates council agents:
           critico-metodologico  --> Methodological critique
           sintetizador          --> Synthesizer (finds common ground)
           advogado-do-diabo     --> Devil's advocate (challenges assumptions)
         Path: agents/system/conclave/

  The conclave is a FORMAL session. It is not for quick questions.
  Use it when a decision has multiple valid paths and you need
  structured debate before committing.
```

**Signal words:** conclave, debate, council, deliberate, multiple perspectives, pros and cons, devil's advocate, trade-off analysis (strategic)

---

### Domain 11: DATA

```
Is the task about data infrastructure or queries?
  YES --> Is it RAG / knowledge graph / embeddings?
    YES --> @data-engineer (Tank) + relevant skills:
           /rag-health    --> RAG index status
           /graph-search  --> Knowledge graph queries
           /memory-search --> Agent memory search
    NO  --> @data-engineer (Tank)
           AIOX native data-engineer agent
           Database schema, ETL, queries, indexes
```

**Signal words:** database, schema, query, SQL, RAG, embeddings, index, chunk, knowledge graph, ETL, migration

---

### Domain 12: DESIGN

```
Is the task about visual design or user experience?
  YES --> @ux-design-expert (Trinity)
         AIOX native UX/design agent
         UI/UX, wireframes, design systems, frontend architecture
```

**Signal words:** design, wireframe, UI, UX, component, layout, responsive, accessibility, figma, mockup

---

## FALLBACK: "I Don't Know Which Agent"

When the task does not clearly match any domain above:

1. **Keyword analysis:** Extract the 3 most significant nouns/verbs from the request
2. **Fuzzy match:** Compare against signal words in each domain
3. **Top 2 suggestions:** Present the two most likely agents with reasoning

**Output format for ambiguous routing:**

```
ROUTING ANALYSIS
================
Task: "{user request summary}"

Best match:  {agent_name} ({agent_role})
  Reason:    {why this agent fits}
  Activate:  {command or path}

Runner-up:   {agent_name} ({agent_role})
  Reason:    {why this could also fit}
  Activate:  {command or path}

Confidence: {HIGH | MEDIUM | LOW}
```

If confidence is LOW, ask the user one clarifying question before routing.

---

## QUICK REFERENCE TABLE

| Agent | Type | Domain | One-Liner |
|-------|------|--------|-----------|
| @dev | AIOX | Development | General code implementation |
| @devops | AIOX | Deployment | CI/CD, git push, releases |
| @architect | AIOX | Architecture | Full-stack system design |
| @qa | AIOX | Quality | Quality gates, code reviews |
| @pm | AIOX | Planning | PRDs, product strategy |
| @po | AIOX | Planning | Backlog, acceptance criteria |
| @sm | AIOX | Planning | Stories, sprint planning |
| @analyst | AIOX | Business-Ops | Market research, competitive analysis |
| @data-engineer | AIOX | Data | Database, RAG, ETL, knowledge graph |
| @ux-design-expert | AIOX | Design | UI/UX, wireframes, frontend architecture |
| kops-atlas | Knowledge Ops | Knowledge-Ops | Bucket classification and routing |
| kops-sage | Knowledge Ops | Knowledge-Ops | MCE extraction, DNA, insights |
| kops-lens | Knowledge Ops | Knowledge-Ops | Pipeline validation, chunk fidelity |
| kops-forge | Knowledge Ops | Knowledge-Ops | Dossier compilation, cascading |
| kops-echo | Knowledge Ops | Knowledge-Ops | Agent file generation, cloning |
| dops-anvil | Dev Ops | Development | Feature building (Mega Brain core) |
| dops-compass | Dev Ops | Architecture | Internal architecture review |
| dops-hawk | Dev Ops | Quality | Code testing (pytest, unit tests) |
| dops-rocket | Dev Ops | Deployment | Git staging, commits, PRs |
| dops-beacon | Dev Ops | Planning | Phase breakdowns, effort estimates |
| closer | Cargo | Sales | Closing, objection handling |
| bdr | Cargo | Sales | Prospecting, outbound |
| sds | Cargo | Sales | Inbound, lead qualification |
| lns | Cargo | Sales | LinkedIn, social selling |
| nepq-specialist | Cargo | Sales | NEPQ question-based selling |
| sales-coordinator | Cargo | Sales | Pipeline management |
| sales-lead | Cargo | Sales | Sales team leadership |
| sales-manager | Cargo | Sales | KPIs, coaching |
| customer-success | Cargo | Sales | Retention, churn prevention |
| cfo | Cargo C-Level | Business-Ops | Finance, budgets, P&L |
| cro | Cargo C-Level | Business-Ops | Revenue, growth |
| cmo | Cargo C-Level | Business-Ops | Marketing strategy |
| coo | Cargo C-Level | Business-Ops | Operations, processes |
| paid-media-specialist | Cargo | Business-Ops | Ads, paid traffic |
| conclave | System | Deliberation | Multi-agent council debate |

---

## DISAMBIGUATION RULES

These rules resolve conflicts when a task could match multiple agents:

1. **kops-* vs @dev:** If the task involves knowledge/ files or MCE pipeline artifacts, route to kops-*. If it involves core/ Python scripts, route to dops-anvil or @dev.

2. **dops-compass vs @architect:** If the question is about Mega Brain internal structure (bucket isolation, directory contract, paths.py routing), use dops-compass. For external project architecture or tech stack decisions, use @architect.

3. **dops-hawk vs @qa:** If the task is "run pytest" or "write unit tests," use dops-hawk. If the task is "review this PR" or "run quality gate," use @qa.

4. **dops-rocket vs @devops:** For day-to-day git staging and commits within Mega Brain, use dops-rocket. For git push to remote, CI/CD configuration, or release management, use @devops.

5. **dops-beacon vs @pm:** If the task is creating a technical implementation plan with phases, use dops-beacon. If the task is writing a PRD or defining product strategy, use @pm.

6. **cro vs sales-manager:** If the question is strategic (revenue model, growth levers, monetization), use cro. If the question is operational (team KPIs, coaching, pipeline metrics), use sales-manager.

7. **Expert agents vs cargo agents:** If the user asks "what would Hormozi do?", route to the expert agent. If the user asks "how should we handle this objection?", route to the cargo agent (closer) which has DNA from multiple experts baked in.

---

## ACTIVATION

This skill is triggered by:
- `/squad-router` -- Full routing analysis
- `/route` -- Shorthand alias
- Natural language: "which agent handles...", "who should I ask about...", "delegate this to..."

The routing is deterministic. Follow the decision tree exactly. Do not improvise agent assignments.
