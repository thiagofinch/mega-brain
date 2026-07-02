# MODEL Strategy
## Model Assignment Guide for Mega Brain-Core Agent Teams

---

## Overview

Mega Brain-Core Agent Teams use three Claude model tiers. Model assignment is based on the cognitive complexity required by each agent role, balancing quality, speed, and cost.

| Model | Tier | Use Case | Strengths |
|-------|------|----------|-----------|
| claude-opus-4-6 | Premium (DEFAULT for Orchestrator) | Chiefs, Architects, Senior decision-makers, Orchestrator sessions | Complex reasoning, nuanced judgment, multi-step planning, strategic orchestration |
| claude-sonnet-4-6 | Standard | Implementers, Writers, Builders | Balance of speed and quality, strong at execution |
| claude-haiku-4-5 | Economy | Researchers, Classifiers, Simple tasks | Speed-optimized, high throughput, low cost |

---

## Model Assignment Principles

### Default Model for Orchestrator Sessions
**🎯 Claude Opus 4.6 is the DEFAULT model for all Orchestrator (orquestrador-global) sessions.**
- Orchestrator requires maximum reasoning capability for routing decisions
- Benefits from latest model improvements in classification and strategic thinking
- Justifies premium cost due to centralized decision-making role

### When to Use Opus
- **Role**: Chiefs, Architects, Strategic advisors, Quality gatekeepers, **Orchestrator agents**
- **Tasks**: Orchestration, task decomposition, synthesis, final decisions, complex analysis, routing decisions
- **Why**: These roles require deep reasoning, nuanced judgment, and the ability to evaluate and synthesize multiple inputs
- **Cost implication**: Use sparingly; typically 1-2 opus agents per team (except Orchestrator which always uses opus)

### When to Use Sonnet
- **Role**: Implementers, Writers, Builders, Specialists, Reviewers
- **Tasks**: Code writing, content creation, copy production, reviews, platform-specific work
- **Why**: Excellent execution quality with significantly lower cost and faster response than opus
- **Cost implication**: Primary workhorse model; most agents in a team will be sonnet

### When to Use Haiku
- **Role**: Researchers, Classifiers, Data collectors, Simple processors
- **Tasks**: Data gathering, classification, tagging, sentiment scoring, simple transformations
- **Why**: Speed-optimized for high-throughput tasks that don't require deep reasoning
- **Cost implication**: Cheapest option; ideal for tasks that need volume over depth

---

## Per-Squad Model Breakdown

### Tier 1 Squads (Full Support)

#### full-stack-dev
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| dev-chief | opus | Orchestration, task decomposition, architectural decisions |
| architect | opus | System design requires deep technical reasoning |
| builder | sonnet | Code implementation is execution-focused |
| reviewer | sonnet | Code review needs quality but not full opus reasoning |

**Opus:Sonnet:Haiku ratio** = 2:2:0

#### copywriting
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| copywriting-chief | opus | Brief analysis, angle selection, quality synthesis |
| copywriter-1 | sonnet | Copy production from assigned angle |
| copywriter-2 | sonnet | Copy production from assigned angle |
| copywriter-3 | sonnet | Copy production from assigned angle (optional) |

**Opus:Sonnet:Haiku ratio** = 1:2-3:0

#### youtube-content
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| briefing-creator (chief) | opus | Content strategy, brief creation, quality gate |
| researcher | haiku | Data collection and trend scraping is volume work |
| scriptwriter | sonnet | Script writing needs quality but is execution-focused |
| title-writer | sonnet | Title optimization is creative execution |
| thumbnail-strategist | sonnet | Visual strategy requires creativity, not deep reasoning |

**Opus:Sonnet:Haiku ratio** = 1:3:1

#### deep-scraper
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| scraper-1 | sonnet | Source scraping requires structured extraction |
| scraper-2 | sonnet | Source scraping requires structured extraction |
| scraper-3 | sonnet | Source scraping requires structured extraction |
| classifier-1 | haiku | Classification and tagging is pattern matching |
| classifier-2 | haiku | Sentiment scoring is straightforward (optional) |

**Opus:Sonnet:Haiku ratio** = 0:3:1-2

> Note: deep-scraper has no opus agent in team mode. The chief role remains outside the team (caller orchestrates).

---

### Tier 2 Squads (Basic Support)

#### design-system
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| design-system-chief | opus | Design decisions, token architecture |
| implementer | sonnet | Component building, CSS authoring |
| reviewer | sonnet | Accessibility audit, pattern validation |

**Opus:Sonnet:Haiku ratio** = 1:2:0

#### media-buy
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| media-buy-chief | opus | Strategy, budget decisions |
| specialist-1 | sonnet | Platform-specific campaign creation |
| specialist-2 | sonnet | Platform-specific campaign creation |

**Opus:Sonnet:Haiku ratio** = 1:2:0

#### youtube-lives
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| youtube-lives-chief | opus | Orchestration, scheduling decisions |
| researcher | haiku | Performance data collection |
| scriptwriter | sonnet | Live script/pauta creation |
| copy-creator | sonnet | Notification copy |
| thumbnail-creator | sonnet | Live thumbnail strategy |

**Opus:Sonnet:Haiku ratio** = 1:3:1

#### content-marketing
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| content-chief | opus | Strategy and editorial oversight |
| editorial-strategist | sonnet | Content planning |
| writer | sonnet | Content creation |
| distribution-specialist | sonnet | Platform adaptation |

**Opus:Sonnet:Haiku ratio** = 1:3:0

#### data-analytics
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| data-chief | opus | Problem framing, hypothesis synthesis |
| analyst-1 | sonnet | Analytical work (e.g., funnel analysis) |
| analyst-2 | sonnet | Analytical work (e.g., cohort analysis) |
| analyst-3 | sonnet | Analytical work (e.g., unit economics) (optional) |

**Opus:Sonnet:Haiku ratio** = 1:2-3:0

#### project-management
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| pm-orchestrator | opus | Process decisions, orchestration |
| diagnostician | sonnet | Process analysis |
| architect | sonnet | Workspace structuring |
| automation-engineer | sonnet | Workflow automation |

**Opus:Sonnet:Haiku ratio** = 1:3:0

---

### Tier 3 Squads (Experimental)

#### conselho
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| advisor-1 | opus | Strategic perspective requires deep reasoning |
| advisor-2 | opus | Strategic perspective requires deep reasoning |
| advisor-3 | opus | Strategic perspective requires deep reasoning |

**Opus:Sonnet:Haiku ratio** = 3:0:0

> Special case: All opus because advisory decisions are high-stakes and require nuanced judgment.

#### strategy
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| strategy-chief | opus | Strategic framing and final recommendation |
| strategist | opus | Scenario planning requires deep reasoning |
| analyst | sonnet | Data gathering and market analysis is execution |

**Opus:Sonnet:Haiku ratio** = 2:1:0

#### comercial
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| comercial-chief | opus | Sales strategy oversight |
| sdr | sonnet | Lead prospecting and qualification |
| closer | sonnet | Deal closing scripts |
| post-sales | sonnet | Onboarding sequences |

**Opus:Sonnet:Haiku ratio** = 1:3:0

#### community
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| community-chief | opus | Community strategy |
| engagement-specialist | sonnet | Engagement tasks |
| welcome-host | sonnet | Onboarding sequences |

**Opus:Sonnet:Haiku ratio** = 1:2:0

#### communication
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| communication-chief | opus | Communication strategy, triage |
| feedback-specialist | sonnet | Feedback structuring |
| negotiator | sonnet | Negotiation support |

**Opus:Sonnet:Haiku ratio** = 1:2:0

#### strategy-example-squad (brand agents)
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| brand-chief | opus | Brand positioning decisions |
| authority-builder | sonnet | Content creation |
| pitch-designer | sonnet | Pitch and bio design |

**Opus:Sonnet:Haiku ratio** = 1:2:0
> NOTE: These agents were moved from personal-brand (content-ecosystem) to strategy-example-squad squad (2026-02-08)

#### example-squad
| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| assistente-operacional | opus | Operations orchestration |
| suporte-cliente | sonnet | Customer support |
| especialista-vendas | sonnet | Sales tasks |
| copywriter | sonnet | Marketing copy |

**Opus:Sonnet:Haiku ratio** = 1:3:0

---

## Cost Optimization Guidelines

### 1. Minimize Opus Usage
- Maximum 1-2 opus agents per team (exception: conselho with all-opus)
- Only use opus for roles that genuinely require complex reasoning
- If a chief role is primarily dispatching (not reasoning), consider sonnet

### 2. Maximize Haiku for Volume Work
- Data collection, scraping, classification -> always haiku
- Simple transformations and tagging -> haiku
- If the task can be defined as a clear template with variable inputs -> haiku

### 3. Sonnet as Default
- When unsure, default to sonnet
- Sonnet handles 80% of agent workloads effectively
- Upgrade to opus only when quality issues are observed

### 4. Batch Size Awareness
- Haiku agents can handle larger batches (more items per task)
- Opus agents should get fewer, higher-complexity tasks
- Sonnet agents: moderate batch sizes

### 5. Cost Estimation Fórmula
```
Team Cost = (opus_agents x opus_rate x avg_tokens)
          + (sonnet_agents x sonnet_rate x avg_tokens)
          + (haiku_agents x haiku_rate x avg_tokens)
```

Approximate relative cost multipliers (per token):
| Model | Input Cost | Output Cost |
|-------|-----------|-------------|
| opus | 5x | 5x |
| sonnet | 1x (baseline) | 1x (baseline) |
| haiku | 0.2x | 0.2x |

---

## When to Override Defaults

### Upgrade to Higher Model
- Task produces consistently low-quality output with assigned model
- Task involves critical business decisions (even if not a "chief" role)
- Task requires cross-domain reasoning (combining multiple knowledge áreas)
- User explicitly requests higher quality for a specific workflow

### Downgrade to Lower Model
- Task is simpler than initially estimated
- Cost constraints are tight
- Speed is prioritized over quality
- Task is highly structured/template-based

### Override Decision Process
1. Run the task with the default model assignment
2. Evaluate output quality against acceptance criteria
3. If quality is insufficient, upgrade one tier
4. If quality is fine but speed/cost is a concern, downgrade one tier
5. Document the override reason for future reference

---

## Model ID Reference

| Model Name | Model ID | Context Window | Default For |
|-----------|----------|----------------|-------------|
| Claude Opus 4.6 | claude-opus-4-6-20250929 | 200K | **Orchestrator Sessions** |
| Claude Sonnet 4.6 | claude-sonnet-4-6-20250929 | 200K | General Tasks |
| Claude Haiku 4.5 | claude-haiku-4-5-20251001 | 200K | Volume Tasks |

### How to Apply Model in Current Session

**For Orchestrator (orquestrador-global) sessions:**
- The model preference is configured in `squads/orquestrador-global/config.yaml`
- Default: `claude-opus-4-6` for all orchestrator agents
- Current session model: Determined by Claude Code's model selector
- To ensure Opus 4.6 in current session: Request model change via Claude Code interface or use model parameter in API calls

---

## Metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-06 |
| Maintained By | Orchestrator (orquestrador-global) |
| Related | TEAM-REGISTRY.md, TEAM-PATTERNS.md |
