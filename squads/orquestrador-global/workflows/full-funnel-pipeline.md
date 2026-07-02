# Workflow: Full Funnel Pipeline

> Workflow cross-squad completo para colocar um funil no ar — da estratégia à implementação.
> Orquestra 6 squads em sequência com gates de aprovação.

---

## Metadata

```yaml
id: full-funnel-pipeline
name: Full Funnel Pipeline
description: Pipeline completo para criação de funil - estratégia, copy, estrutura, design, implementação e tráfego
version: 1.0.0
owner: orquestrador-global
trigger: "*execute funil completo" | "*full-funnel" | "*funnel-pipeline"
duration_estimate: 5-12 dias (depende do tipo de funil)
```

---

## Pré-requisitos

Antes de iniciar, o orquestrador DEVE coletar:

| Input | Obrigatório | Fonte |
|-------|-------------|-------|
| Produto/oferta | Sim | Usuário |
| Público-alvo (descrição) | Sim | Usuário |
| Faixa de preço | Sim | Usuário |
| Tipo de funil | Sim | Usuário ou auto-detect |
| Domínio/URL base | Não | Vault (`urls.yaml`) |
| Brand guidelines | Não | Files (`clients/index.yaml`) |
| Assets existentes (fotos, vídeos) | Não | Google Drive |

### Auto-detect Tipo de Funil

```yaml
regras:
  - preco <= 47: tripwire-funnel
  - preco 47-297 AND video: vsl-funnel
  - preco 47-997 AND texto: sales-letter-funnel
  - preco 297-2000: webinar-funnel
  - preco > 2000: application-funnel
  - lancamento: launch-funnel (PLF)
```

---

## Stage Dependencies & Flow

```yaml
dependency_graph:
  stage_1:
    outputs:
      - copy-platform.md
      - offer-design.md
      - product-pyramid.md
      - audience-insights.md
    required_by: [stage_2, stage_3, stage_6]
    blocks: stage_2

  stage_2:
    depends_on: [stage_1]
    outputs:
      - copy-package/*
      - email-sequences/*
    required_by: [stage_3, stage_5]
    blocks: stage_3

  stage_3:
    depends_on: [stage_1, stage_2]
    outputs:
      - funnel-map.md
      - page-specs/*
    required_by: [stage_4, stage_5]
    blocks: stage_4

  stage_4:
    depends_on: [stage_3]
    outputs:
      - design-specs/*
      - tokens.css
      - layouts/*
    required_by: [stage_5]
    blocks: stage_5

  stage_5:
    depends_on: [stage_2, stage_3, stage_4]
    outputs:
      - build/*.html
      - deployment-urls.md
      - tracking-config.md
    required_by: [stage_6]
    blocks: stage_6

  stage_6:
    depends_on: [stage_5]
    optional: true
    outputs:
      - campaign-plan.md
      - automation-config.md
```

---

## Stages

### Stage 1: Estratégia & Pesquisa

```yaml
stage: 1
name: Estratégia & Pesquisa
squads:
  primary: agora-direct-response
  support: deep-scraper
duration: 1-2 dias
gate: Aprovação do usuário (Copy Platform + Offer Design)

tasks:
  agora-direct-response:
    - task: find-big-idea
      agent: agora-idea-architect
      input: [produto, público-alvo, pesquisa]
      output: big-idea.md

    - task: create-usp
      agent: agora-idea-architect
      input: [big-idea, concorrentes]
      output: usp.md

    - task: build-copy-platform
      agent: agora-sales-engineer
      input: [big-idea, usp, avatar]
      output: copy-platform.md

    - task: design-offer
      agent: agora-offer-designer
      input: [produto, preço, product-pyramid]
      output: offer-design.md

    - task: choose-lead-type
      agent: agora-sales-engineer
      input: [avatar, awareness-level]
      output: lead-type.md

    - task: product-pyramid
      agent: agora-strategist
      input: [produto, preço]
      output: product-pyramid.md

  deep-scraper:
    parallel: true
    - task: competitor-analysis
      output: competitor-report.md
    - task: audience-research
      output: audience-insights.md

deliverables:
  - copy-platform.md      # USP + Big Idea + Big Promise + Claims + Proof
  - offer-design.md        # OSS, pricing, value stack, garantia
  - product-pyramid.md     # Free → Front → Back → VIP
  - lead-type.md           # Tipo de lead por awareness
  - competitor-report.md   # Análise competitiva
  - audience-insights.md   # Avatar profundo, dores, linguagem

gate_criteria:
  - [ ] Big Idea passa no Ogilvy 5Q Test (score >= 40)
  - [ ] USP atende 3 critérios (única, específica, desejável)
  - [ ] Copy Platform tem 5 componentes completos
  - [ ] Offer design tem preço, garantia e value stack
  - [ ] Usuário APROVANDO Copy Platform e Offer
```

### Stage 2: Criação de Copy

```yaml
stage: 2
name: Criação de Copy
squad: copywriting
duration: 2-4 dias
gate: Aprovação do usuário (copy principal)
depends_on: Stage 1 (aprovado)

tasks:
  # Escolher workflow baseado no tipo de funil
  workflow_selection:
    vsl-funnel: wf-vsl-production.yaml       # 8 agents, VSL script
    sales-letter-funnel: wf-sales-letter-rmbc.yaml  # 9 agents, sales letter
    webinar-funnel: webinar-script            # Jason Fladlien
    launch-funnel: wf-vsl-production.yaml + email launch sequence

  always_run:
    - task: email-sequences
      agent: gary-halbert + email-specialist
      input: [copy-platform, tipo-funil]
      output:
        - emails/cart-abandon-sequence.md     # 3-5 emails
        - emails/followup-sequence.md         # 3-5 emails
        - emails/onboarding-sequence.md       # 5-7 emails

    - task: offer-copy
      agent: dan-kennedy
      input: [offer-design, copy-platform]
      output:
        - offer-stack-copy.md                 # Copy do value stack
        - guarantee-copy.md                   # Copy da garantia
        - urgency-copy.md                     # Copy de urgência/escassez
        - upsell-copy.md                      # Copy de OTOs (1-3)
        - bump-copy.md                        # Copy dos order bumps

    - task: headline-variations
      agent: john-caples
      input: [big-idea, copy-platform]
      output: headlines.md                    # 10+ variações

deliverables:
  - copy-package/main-copy.md       # VSL script OU sales letter
  - copy-package/headlines.md        # 10+ headline variations
  - copy-package/offer-stack-copy.md # Copy do offer
  - copy-package/guarantee-copy.md   # Copy da garantia
  - copy-package/urgency-copy.md     # Copy de urgência
  - copy-package/upsell-copy.md      # Copy OTOs 1-3
  - copy-package/bump-copy.md        # Copy order bumps
  - copy-package/emails/             # Todas as email sequences
  - copy-package/strategy-brief.md   # Big Idea + mechanism + avatar

gate_criteria:
  - [ ] Copy principal completa (script ou letter)
  - [ ] 10+ headline variations geradas
  - [ ] Offer copy com value stack + garantia + urgência
  - [ ] Upsell copy para 1-3 OTOs
  - [ ] Email sequences completas (cart, followup, onboarding)
  - [ ] Usuário APROVA copy principal
```

### Stage 3: Estrutura de Funil

```yaml
stage: 3
name: Estrutura de Funil & Page Specs
squad: funnel-creator
duration: 1-2 dias
gate: Aprovação do usuário (funnel map + page specs)
depends_on: Stage 2 (aprovado)

tasks:
  - task: funnel-architecture
    agent: funnel-chief
    input: [copy-package, offer-design, product-pyramid, tipo-funil]
    output: funnel-map.md
    description: |
      Define o fluxo completo: quais páginas, ordem, OTOs, condicionais.
      Consultar FUNNEL-PAGE-REQUIREMENTS.md para lista de páginas por tipo.

  - task: page-spec-from-copy
    agent: funnel-chief + specialist
    input: [copy-package, funnel-map]
    output: page-specs/*.md
    description: |
      Para CADA página do funil, gera uma page-spec seguindo o formato
      definido em COPY-TO-PAGE-BRIDGE.md seção 3.
      Inclui: copy por seção, componentes, assets, interações.

  - task: conversion-optimization
    agent: funnel-chief
    input: [page-specs, audience-insights]
    output: conversion-notes.md
    description: |
      Notas de otimização de conversão para cada página.
      Referência: métricas benchmark em FUNNEL-PAGE-REQUIREMENTS.md seção 5.

deliverables:
  - funnel-spec/funnel-map.md           # Fluxo visual do funil
  - funnel-spec/page-specs/opt-in.md    # Spec da opt-in page
  - funnel-spec/page-specs/vsl-page.md  # Spec da VSL page (ou sales-page)
  - funnel-spec/page-specs/order-page.md # Spec da order page
  - funnel-spec/page-specs/oto1.md      # Spec do OTO1
  - funnel-spec/page-specs/oto2.md      # Spec do OTO2
  - funnel-spec/page-specs/downsell.md  # Spec do downsell
  - funnel-spec/page-specs/thank-you.md # Spec da thank you
  - funnel-spec/conversion-notes.md     # Notas de otimização

gate_criteria:
  - [ ] Funnel map com todas as páginas e fluxos
  - [ ] Page spec para cada página (formato COPY-TO-PAGE-BRIDGE)
  - [ ] Assets necessários listados por página
  - [ ] Interações documentadas (timers, popups, scroll)
  - [ ] Usuário APROVA estrutura de funil
```

### Stage 4: Design

```yaml
stage: 4
name: Design de Páginas
squad: design-system
duration: 2-3 dias
gate: Aprovação do usuário (design das páginas principais)
depends_on: Stage 3 (aprovado)

tasks:
  - task: design-token-system
    agent: jina-anne
    input: [brand-guidelines, page-specs]
    output: design-specs/tokens.css
    description: |
      Criar design tokens como CSS custom properties.
      Cores, tipografia, espaçamento, sombras, animações.

  - task: page-layouts
    agent: una-kravets
    input: [page-specs, tokens]
    output: design-specs/layouts/*.md
    skill: frontend-design-hybrid
    description: |
      OBRIGATÓRIO usar frontend-design-hybrid SKILL.
      Para cada page-spec, criar layout com:
      - Grid system (CSS Grid + Container Queries)
      - Responsive breakpoints
      - Micro-interactions
      - Visual atmosphere

  - task: component-specs
    agent: brad-frost
    input: [layouts, tokens]
    output: design-specs/components.md
    description: |
      Atomic Design: átomos → moléculas → organismos.
      Especificar cada componente reutilizável.

  - task: accessibility-review
    agent: heydon-pickering
    input: [layouts, components]
    output: design-specs/accessibility.md
    description: |
      WCAG 2.1 AA compliance para todas as páginas.
      Focus management, keyboard navigation, screen reader.

deliverables:
  - design-specs/tokens.css            # CSS custom properties
  - design-specs/layouts/*.md          # Layout por página
  - design-specs/components.md         # Component library
  - design-specs/interactions.md       # Micro-interactions
  - design-specs/accessibility.md      # A11y requirements

gate_criteria:
  - [ ] Design tokens definidos (cores, tipo, espaçamento)
  - [ ] Layout de cada página definido
  - [ ] Componentes documentados (Atomic Design)
  - [ ] Acessibilidade WCAG 2.1 AA
  - [ ] Usuário APROVA design das páginas principais
```

### Stage 5: Implementação & Deploy

```yaml
stage: 5
name: Implementação & Deploy
squad: full-stack-dev
duration: 2-4 dias
gate: Páginas live e funcionais
depends_on: Stage 4 (aprovado)

tasks:
  - task: implementation
    agent: dev-chief + kent-c-dodds
    input: [page-specs, design-specs, assets]
    output: build/*.html
    skill: frontend-design-hybrid
    description: |
      Implementar cada página como HTML/CSS/JS.
      Usar design tokens do Stage 4.
      OBRIGATÓRIO usar frontend-design-hybrid SKILL.
      Single-file HTML quando possível (facilita deploy).

  - task: tracking-setup
    agent: dev-chief
    input: [funnel-map, page-specs]
    output: tracking-config.md
    description: |
      Configurar tracking:
      - Meta Pixel (PageView, ViewContent, AddToCart, Purchase)
      - Google Analytics (GA4 events)
      - CAPI (Conversions API server-side)
      - UTM parameter handling

  - task: deploy
    agent: kelsey-hightower
    input: [build/*, domínio]
    output: deployment-urls.md
    tools:
      - mcp__hostinger-api__hosting_deployStaticWebsite
      - mcp__hostinger-api__hosting_createWebsiteV1
    description: |
      Deploy para Hostinger via MCP.
      Configurar domínio/subdomínio.
      SSL automático.

  - task: qa-testing
    agent: dev-chief
    input: [deployment-urls]
    output: qa-report.md
    description: |
      Testar todas as páginas:
      - Links funcionais
      - Formulários submetem
      - Vídeos carregam
      - Mobile responsivo
      - Tracking disparando
      - Checkout funciona

deliverables:
  - build/*.html                       # Páginas implementadas
  - deployment-urls.md                 # URLs de produção
  - tracking-config.md                 # Config de tracking
  - qa-report.md                       # Relatório de QA

gate_criteria:
  - [ ] Todas as páginas implementadas e responsivas
  - [ ] Deploy no Hostinger com SSL
  - [ ] Tracking configurado (Pixel + GA4)
  - [ ] QA completo sem bugs críticos
  - [ ] Checkout functional testado
  - [ ] Usuário CONFIRMA pages live
```

### Stage 6: Tráfego & Automação (Opcional)

```yaml
stage: 6
name: Tráfego & Automação
squads:
  primary: traffic-squad | media-buy
  support: marketing-automation
duration: 2-3 dias
gate: Campanhas ativas e automações funcionais
depends_on: Stage 5 (aprovado)
optional: true

tasks:
  traffic-squad:
    - task: campaign-structure
      input: [deployment-urls, audience-insights, creative-assets]
      output: campaign-plan.md

    - task: creative-brief
      input: [headlines, audience-insights]
      output: ad-creatives-brief.md

  marketing-automation:
    - task: email-automation
      input: [email-sequences, funnel-map]
      output: automation-config.md
      tools:
        - n8n workflows
        - ActiveCampaign (via n8n)
      description: |
        Configurar automações de email:
        - Cart abandonment trigger
        - Post-purchase onboarding
        - Follow-up nurture sequence

deliverables:
  - campaign-plan.md                   # Estrutura de campanhas
  - ad-creatives-brief.md             # Brief para criativos
  - automation-config.md              # Configuração de automações
```

---

## Execution Logging

Este workflow DEVE seguir o protocolo de logging:

```yaml
directory: .data/executions/{YYYY-MM-DD}_funnel-{slug}/
files:
  - 00-master-plan.md                 # Plano aprovado
  - 01-agora-direct-response-input.md
  - 01-agora-direct-response-output.md
  - 02-copywriting-input.md
  - 02-copywriting-output.md
  - 03-funnel-creator-input.md
  - 03-funnel-creator-output.md
  - 04-design-system-input.md
  - 04-design-system-output.md
  - 05-full-stack-dev-input.md
  - 05-full-stack-dev-output.md
  - 06-traffic-automation-input.md    # (se Stage 6 executado)
  - 06-traffic-automation-output.md
  - 99-execution-summary.md
```

---

## Quality Gates & Success Criteria per Phase

### Stage 1: Estratégia & Pesquisa — Success Metrics

| Deliverable | Success Criteria | Measurable |
|-------------|------------------|-----------|
| Big Idea | Passes Ogilvy 5Q test (score ≥ 40) | Score documented in big-idea.md |
| USP | Meets 3 criteria: unique, specific, desirable | All 3 criteria explicitly stated |
| Copy Platform | Contains 5 components: Big Idea, Big Promise, Claims, Proof, Mechanism | All sections present and complete |
| Offer Design | Price point, guarantee period, value stack, payment terms defined | All elements in offer-design.md |
| Product Pyramid | Free → Front → Back → VIP with pricing | All tiers with clear progression |
| Audience Research | Avatar profile with psychographics, pain points, language | Minimum 5 pain points identified |

### Stage 2: Criação de Copy — Success Metrics

| Deliverable | Success Criteria | Measurable |
|-------------|------------------|-----------|
| Main Copy (VSL/Letter) | Complete script with all sections | Page count ≥ 3 pages for letter, 15+ min VSL |
| Headlines | 10+ variations tested mentally | At least 10 distinct variations provided |
| Email Sequences | Cart (3), Followup (3), Onboarding (5) complete | 11+ emails total, each 100-300 words |
| Offer Copy | Value stack, guarantee, urgency documented | All 3 components present |
| Upsells/Bumps | 1-3 OTOs and order bumps priced/positioned | Clear pricing relative to main offer |

### Stage 3: Estrutura de Funil — Success Metrics

| Deliverable | Success Criteria | Measurable |
|-------------|------------------|-----------|
| Funnel Map | All pages, flow, OTOs, conditionals documented | Visual map with 6+ pages minimum |
| Page Specs | Spec for every page in funnel | 1 spec per page, COPY-TO-PAGE-BRIDGE format |
| Conversion Notes | Optimization guidance per page | Minimum 2 notes per page |
| Assets List | All required images, vídeos, forms identified | Count of assets by page documented |

### Stage 4: Design — Success Metrics

| Deliverable | Success Criteria | Measurable |
|-------------|------------------|-----------|
| Design Tokens | Colors, typography, spacing, animations defined | 20+ CSS custom properties |
| Layouts | Responsive grids, breakpoints, interactions | Mobile (320px), Tablet (768px), Desktop (1024px) |
| Components | Atomic Design hierarchy documented | 3+ molecules, 5+ organisms specified |
| Accessibility | WCAG 2.1 AA compliance verified | All pages pass axe DevTools scan |

### Stage 5: Implementação & Deploy — Success Metrics

| Deliverable | Success Criteria | Measurable |
|-------------|------------------|-----------|
| HTML Pages | All pages implemented, responsive, functional | Lighthouse score ≥ 80 on mobile |
| Deploy | Live on domain with SSL/HTTPS | HTTPS shows green lock, no mixed content |
| Tracking | Pixel/GA4/CAPI events firing | All conversion events visible in GTM preview |
| QA Report | All critical bugs resolved | 0 critical bugs, ≤3 minor issues |

---

## Risk & Mitigation by Phase

### Stage 1 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Big Idea rejected by user | Restart Stage 1, delay 3-5 days | Medium | Early feedback session, 3 idea options |
| Product data incomplete | Cannot define positioning | High | Pre-call data collection from user |
| Competitive positioning unclear | Copy lacks differentiation | Medium | Deep-scraper parallel research |
| Avatar definition too broad | Generic copy, low conversion | Medium | Audience-research refinement, 3 personas |

### Stage 2 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Copy rejected after creation | Rewrite adds 3-5 days | Medium | Mid-stage user feedback on outline |
| Email sequences too long | Poor deliverability, low engagement | Low | Pre-built templates, word-count limits |
| Offer copy dilutes main promise | Confusion reduces conversions | Low | Consistency review before gate |
| Headline weakness | Low CTR on ads/landing page | Medium | A/B test top 3 headlines early |

### Stage 3 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Page count exceeds capacity | Dev timeline extends | Medium | Limit pages: opt-in, VSL, order, OTO1, TY |
| Asset requirements too ambitious | Design/dev delays | Medium | Asset audit at stage start |
| Funnel logic errors discovered | Rebuild flow + conditions | Low | Flowchart review by PM |
| Page specs unclear for designers | Design misinterpretation | Medium | Spec template + designer kickoff call |

### Stage 4 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Design requires brand approval | Approval delays 2-3 days | Medium | Brand guidelines locked in Stage 1 |
| Accessibility compliance issues | Rework required, delay release | Low | Heydon Pickering review included |
| Design tokens conflict | Component inconsistency | Low | Token system designed first, reviewed |
| Mobile responsiveness broken | QA failure, cannot launch | Low | Mobile-first design approach |

### Stage 5 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Development takes longer than estimated | Launch delay 2-5 days | Medium | Frontend-design-hybrid skill enforced |
| Tracking misconfiguration | Data loss, campaign blind | High | Tracking setup verified in QA |
| Hosting issues with deploy | Cannot launch | Low | VPS health check before deploy |
| Browser compatibility issues | Users cannot convert | Low | Browser testing on Chrome, Safari, Firefox |

### Stage 6 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Creative brief incomplete | Ads miss target | Medium | Briefing from Stage 1 copy + audience |
| Automation routing broken | Leads lost or wrong sequence | Medium | n8n workflow testing before activation |
| Budget exhausted quickly | Campaign stops | Low | Budget pacing rules configured |

---

## Handoff Protocol between Stages

### Stage 1 → Stage 2 Handoff

**Deliverables to pass:**
- copy-platform.md (Big Idea, Big Promise, Claims, Proof)
- offer-design.md (positioning, pricing, guarantee)
- product-pyramid.md
- audience-insights.md (avatar, language)

**Handoff checklist:**
- [ ] User has APPROVED copy platform
- [ ] User has APPROVED offer design
- [ ] Big Idea document is reviewed and locked
- [ ] Competitor analysis complete
- [ ] Avatar psychographics documented
- [ ] Copywriting squad has read all documents
- [ ] Initial copy outline started

**Handoff meeting:**
- Agora-direct-response chief → Copywriting chief
- Duration: 30 min
- Document: create-copy-briefing.md with copy angles, tone, target objections

### Stage 2 → Stage 3 Handoff

**Deliverables to pass:**
- copy-package/ (main copy, headlines, all sequences)
- All approved email sequences

**Handoff checklist:**
- [ ] Main copy APPROVED by user
- [ ] 10+ headlines generated and ranked
- [ ] Email sequences APPROVED
- [ ] Copy consistency review passed
- [ ] Funnel-creator squad has received copy package
- [ ] Page specs outline created

**Handoff meeting:**
- Copywriting chief → Funnel-creator chief
- Duration: 45 min
- Document: funnel-architecture-briefing.md with page flow, OTOs, conditionals

### Stage 3 → Stage 4 Handoff

**Deliverables to pass:**
- funnel-map.md (visual architecture)
- page-specs/ (all page specifications)
- conversion-notes.md

**Handoff checklist:**
- [ ] Funnel map APPROVED by user
- [ ] Page specs complete for all pages
- [ ] Asset requirements documented
- [ ] Design-system squad has received specs
- [ ] Tokens and layout brief prepared

**Handoff meeting:**
- Funnel-creator chief → Design-system chief
- Duration: 60 min
- Document: design-briefing.md with brand alignment, token requirements, component list

### Stage 4 → Stage 5 Handoff

**Deliverables to pass:**
- design-specs/ (tokens, layouts, components, interactions)
- accessibility checklist (WCAG 2.1 AA)

**Handoff checklist:**
- [ ] Design APPROVED by user
- [ ] Design tokens finalized
- [ ] All layouts reviewed for responsiveness
- [ ] Accessibility audit completed
- [ ] Dev-chief has received design package
- [ ] Hosting environment ready

**Handoff meeting:**
- Design-system chief → Dev-chief
- Duration: 60 min
- Document: implementation-briefing.md with build approach, frontend stack, tracking requirements

### Stage 5 → Stage 6 Handoff (Optional)

**Deliverables to pass:**
- build/*.html (all deployed pages)
- deployment-urls.md
- tracking-config.md (verified firing)
- qa-report.md

**Handoff checklist:**
- [ ] All pages LIVE and tested
- [ ] Tracking VERIFIED in GTM preview mode
- [ ] QA report with 0 critical bugs
- [ ] Traffic-squad has campaign-plan draft
- [ ] Marketing-automation has automation specs

**Handoff meeting:**
- Dev-chief → Traffic-squad chief + Marketing-automation chief
- Duration: 45 min
- Document: launch-checklist.md with live URLs, tracking IDs, automation triggers

---

## Rollback Procedures

### Rollback Scenarios by Stage

#### If Stage 1 approval fails (Issue: Big Idea rejected)

```yaml
action: Roll back to Stage 1
steps:
  1. Stop all downstream work (pause Stage 2 squad)
  2. Save existing work to .data/executions/{date}/rollback/
  3. Agora-direct-response generates 3 alternative Big Ideas
  4. Re-submit for user approval
  5. Once approved, resume Stage 2
impact: Adds 3-5 days to timeline
```

#### If Stage 2 approval fails (Issue: Copy quality low)

```yaml
action: Continue Stage 2 (no rollback needed)
steps:
  1. Copywriting squad revises based on feedback
  2. User reviews revised copy
  3. If still rejected, escalate to Story-Chief for review
  4. Once approved, proceed to Stage 3
impact: Adds 2-3 days to timeline
```

#### If Stage 3 approval fails (Issue: Funnel structure flawed)

```yaml
action: Redesign funnel (partial Stage 3 restart)
steps:
  1. Pause Stage 4 squad (design on hold)
  2. Funnel-creator reviews flow with user
  3. Identify breaking points (missing page, wrong sequence, etc.)
  4. Redesign funnel-map.md
  5. Update affected page-specs/
  6. Re-approve with user
  7. Resume Stage 4 with updated specs
impact: Adds 2-3 days to timeline
```

#### If Stage 4 approval fails (Issue: Design doesn't match brand)

```yaml
action: Design revision (Stage 4 continue)
steps:
  1. Pause Stage 5 squad
  2. Design-system chief reviews brand alignment with user
  3. Identify specific components/colors/layouts to fix
  4. Revise design-specs/
  5. Re-submit for user approval
  6. Once approved, resume Stage 5
impact: Adds 1-2 days to timeline
```

#### If Stage 5 QA fails (Issue: Critical bugs found)

```yaml
action: Bug fix + re-QA (Stage 5 continue)
steps:
  1. Dev-chief triages bugs (critical vs non-critical)
  2. Fix critical bugs (must-fix for launch)
  3. Document non-critical bugs in backlog
  4. Re-run QA on critical items
  5. Once 0 critical bugs, approve for launch
impact: Adds 1-3 days depending on bug complexity
```

#### If Stage 5 deploy fails (Issue: SSL error, domain not resolving)

```yaml
action: Hosting issue resolution
steps:
  1. Dev-chief contacts Hostinger support or uses API
  2. Diagnose issue: SSL, DNS, or server config
  3. Fix and test
  4. Re-verify domain + SSL + page load
  5. Resume from deployment
impact: Adds 4-24 hours depending on issue
```

#### If Stage 6 campaign approval fails (Issue: Audience targeting wrong)

```yaml
action: Campaign redesign (optional — can proceed without Stage 6)
steps:
  1. Pause ad activation
  2. Traffic-squad reviews audience with user
  3. Adjust targeting in campaign-plan.md
  4. Re-brief creative team if needed
  5. Re-submit campaign for approval
  6. Once approved, activate ads
impact: Adds 1-2 days (or skip Stage 6 entirely)
```

---

## Checkpoint Verification Checklist

### Pre-Stage Checkpoints (Go/No-Go Gates)

**Before starting Stage 2:**
- [ ] Stage 1 gate criteria 100% met
- [ ] Copy platform document is locked (no revisions pending)
- [ ] Offer design has final pricing + guarantee
- [ ] Audience avatar is detailed (not generic)
- [ ] Copywriting squad roster confirmed
- [ ] Deadline for Stage 2 set and communicated

**Before starting Stage 3:**
- [ ] Stage 2 gate criteria 100% met
- [ ] Main copy is user-approved (signature on copy-platform)
- [ ] 10+ headlines ranked by predicted effectiveness
- [ ] All email sequences drafted and approved
- [ ] Funnel-creator squad roster confirmed
- [ ] Hosting environment (domain, SSL) confirmed

**Before starting Stage 4:**
- [ ] Stage 3 gate criteria 100% met
- [ ] Funnel map is locked (no flow changes pending)
- [ ] Page specs complete for every page
- [ ] Asset list is final and count confirmed
- [ ] Design-system squad roster confirmed
- [ ] Brand guidelines approved and locked

**Before starting Stage 5:**
- [ ] Stage 4 gate criteria 100% met
- [ ] Design approved by user (visual sign-off)
- [ ] Design tokens and component library complete
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Dev-chief has build estimate and timeline
- [ ] Hosting account and domain manager informed

**Before starting Stage 6:**
- [ ] Stage 5 gate criteria 100% met
- [ ] All pages live and QA-cleared (0 critical bugs)
- [ ] Tracking verified in GTM preview (all events firing)
- [ ] Checkout functional test completed
- [ ] Traffic-squad has audience data from Stage 1
- [ ] Budget and creative assets available

---

## Quick Start

### Comando: `*full-funnel`

```
Uso: *full-funnel [tipo] [produto] [preço]

Exemplos:
  *full-funnel vsl "Método Agenda Mágica" R$297
  *full-funnel webinar "Programa de Mentoria" R$1997
  *full-funnel tripwire "Mini-Curso SEO" R$27
  *full-funnel launch "Curso Completo XYZ" R$497
  *full-funnel sales-letter "Suplemento ABC" R$197
```

---

## Variações por Tipo de Funil

| Tipo | Stages Usados | Copy Principal | Páginas |
|------|---------------|----------------|---------|
| VSL | 1-6 | wf-vsl-production | opt-in, VSL, order, OTO1-2, downsell, TY |
| Sales Letter | 1-6 | wf-sales-letter-rmbc | opt-in, advertorial, sales page, order, OTO1-2, TY |
| Webinar | 1-6 | webinar script | registration, confirmation, room, replay, order, TY |
| Tripwire | 1-5 | offer copy | opt-in, tripwire TY+offer, order, OTO1-2, TY |
| Launch (PLF) | 1-6 | PLF content | registration, PLC1-3, cart open, order, TY |
| Application | 1-5 | sales page | VSL/page, application form, confirmation |

---

*Criado por @squad-creator (Craft) — 2026-02-09*
*Workflow mestre para criação de funis completos no Mega Brain.*

## MEGABRAIN Deep Validation

- Last run: `20260514-validate-deep`
- Validator: `mega-brain/megabrain-chief`
- Mode: `deep`
- Workflow ID: `full-funnel-pipeline`
- Status: `pass`
- External execution: not performed during structural validation.
