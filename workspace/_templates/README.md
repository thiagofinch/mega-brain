# Workspace Templates

Structured YAML templates for workspace governance. Every operational artifact -- from company profiles to incident reports -- has a template that defines its schema.

---

## Directory Structure

```
workspace/_templates/
  company/            Company identity and strategy
    company-profile.yaml
    icp.yaml
    brand.yaml
    elevator-pitch.yaml
  operations/         Operational processes and rituals
    meeting-notes.yaml
    sprint-review.yaml
    retrospective.yaml
    incident-report.yaml
    process-sop.yaml
  sales-process/      Sales pipeline and client management
    lead-qualification.yaml
    proposal.yaml
    pipeline-stage.yaml
    client-handoff.yaml
  content/            Content creation and publishing
    content-brief.yaml
    editorial-calendar.yaml
    production-checklist.yaml
  delivery/           Project delivery and client reporting
    project-kickoff.yaml
    deliverable-checklist.yaml
    client-report.yaml
  hiring/             Hiring and onboarding
    job-description.yaml
    scorecard.yaml
    onboarding-checklist.yaml
  analytics/          Business intelligence and reporting
    cohort-analysis.yaml
    executive-report.yaml
    health-score-report.yaml
    attribution-report.yaml
  brand/              Brand strategy and activation
    brandbook.yaml
    archetype-profile.yaml
    activation-system.yaml
  products/           Product profiles, launch campaigns and curriculum
    product-profile.yaml
    launch-campaign.yaml
    curriculum-detail.yaml
    PRODUCT-PROFILE-BRIEFING.md
  ai/                 AI strategy and governance
    strategy.yaml
```

---

## _meta Block (Governance)

Every YAML template MUST include a `_meta:` block placed after the comment header and before `metadata:`. This block provides governance-level information used by `scaffold.py` and workspace tooling.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | yes | Semantic version of the template (`MAJOR.MINOR.PATCH`) |
| `owner` | string | yes | Governance owner responsible for the template (see owner mapping below) |
| `target_layer` | string | yes | Workspace layer where instances of this template are placed. Must match `TEMPLATE-LAYER-MAP.yaml` |
| `state` | string | yes | Lifecycle state of the file. Always `"TEMPLATE"` for files in `_templates/` |

**Owner mapping by category:**

| Category | Owner |
|----------|-------|
| ai/ | caio-architect |
| analytics/ | data-chief |
| brand/ | cmo-architect |
| company/ | c-level |
| content/ | content-strategist |
| delivery/ | coo-orchestrator |
| hiring/ | people-ops |
| operations/ | coo-orchestrator |
| products/ | pm |
| sales-process/ | hormozi-chief |

**Valid `target_layer` values:**

| Layer | TTL | Content |
|-------|-----|---------|
| L0-identity | 365d | Company DNA, legal, founder, core processes |
| L1-strategy | 90d | ICP, BMC, lean canvas, offerbook, pricing |
| L2-tactical | 60d | Brand, campaigns, design system, movement |
| L3-product | 30d | Product specs, features, roadmap, curriculum |
| L4-operational | 7d | SOPs, meeting notes, sprint reviews, incidents |

Example:

```yaml
_meta:
  version: "1.0.0"
  owner: "coo-orchestrator"
  target_layer: "L4-operational"
  state: "TEMPLATE"
```

The canonical mapping from template filename to `target_layer` is defined in `TEMPLATE-LAYER-MAP.yaml`. When `target_layer` in a template disagrees with the mapping file, the mapping file wins.

---

## Metadata Block (Required)

Every YAML template MUST include a `metadata:` block as the first section with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `canonical_scope` | string | yes | Full path from workspace root (e.g., `workspace/_templates/company/icp.yaml`) |
| `owner` | string | yes | Role responsible for this template (e.g., `ceo`, `cmo`, `cro`, `coo`, `cfo`, `cto`) |
| `version` | string | yes | Semantic version following `MAJOR.MINOR.PATCH` |
| `last_updated` | string | yes | ISO date of last modification (`YYYY-MM-DD`) |
| `description` | string | yes | One-line description of what the template captures |

Example:

```yaml
metadata:
  canonical_scope: "workspace/_templates/operations/meeting-notes.yaml"
  owner: "coo"
  version: "1.0.0"
  last_updated: "2026-03-23"
  description: "Meeting notes template with date, participants, agenda, decisions, action items, and follow-up"
```

---

## Field Definition Format

After the metadata block, templates define their schema in a `fields:` section. Each field specifies:

| Property | Required | Description |
|----------|----------|-------------|
| `type` | yes | Data type: `string`, `number`, `date`, `boolean`, `enum`, `list`, `object` |
| `required` | yes | Whether this field must be filled (`true` or `false`) |
| `description` | yes | What this field captures |
| `options` | only for `enum` | Allowed values for enum fields |
| `properties` | only for `object` | Nested field definitions |

Example:

```yaml
fields:
  severity:
    type: enum
    required: true
    description: "Incident severity level"
    options: [critical, high, medium, low]

  impact:
    type: object
    required: true
    description: "Scope and consequences"
    properties:
      affected_systems:
        type: list
        required: true
        description: "Systems affected by the incident"
```

---

## Naming Conventions

- File names: **kebab-case** with `.yaml` extension (e.g., `content-brief.yaml`)
- Directory names: **kebab-case** (e.g., `sales-process/`)
- Field names: **snake_case** within YAML (e.g., `first_contact_date`)
- Enum values: **kebab-case** (e.g., `in-progress`, `at-risk`)

---

## How to Add a New Template

1. Identify which category the template belongs to (company, operations, sales-process, content, delivery, hiring, analytics, brand, products, ai)
2. If no existing category fits, create a new directory under `workspace/_templates/`
3. Create the YAML file following the naming convention
4. Include the `metadata:` block with all 5 required fields
5. Define the `fields:` section with type, required, and description for each field
6. Keep the template focused: 15-30 fields maximum
7. Update this README to include the new template in the directory structure

---

## Template Ownership by Role

| Role | Templates |
|------|-----------|
| CEO | `company-profile`, `elevator-pitch`, `executive-report` |
| CMO | `icp`, `brand`, `content-brief`, `editorial-calendar`, `production-checklist`, `brandbook`, `archetype-profile`, `activation-system`, `attribution-report`, `product-profile`, `launch-campaign` |
| CRO | `lead-qualification`, `proposal`, `pipeline-stage`, `client-handoff` |
| COO | `meeting-notes`, `sprint-review`, `retrospective`, `incident-report`, `process-sop`, `project-kickoff`, `deliverable-checklist`, `client-report`, `job-description`, `scorecard`, `onboarding-checklist`, `health-score-report` |
| CFO | `cohort-analysis` |
| CTO | `ai/strategy` |

---

## Product Templates: Enrichment Model

The `products/` templates introduce a 3-layer enrichment model not present in other templates:

| Layer | Name | Behavior |
|-------|------|----------|
| 1 | **Staging** | Pipeline writes insights to `.staging/` directory. Never touches the profile directly. |
| 2 | **Draft** | When threshold is met, field is promoted to profile with `status: draft`. |
| 3 | **Confirmed** | Human reviews and confirms. Pipeline never overwrites confirmed fields. |

**Write protection levels** (per field):

| Level | Rule | Examples |
|-------|------|---------|
| `auto_fill` | Pipeline writes freely if field is empty | Tags, team members, automation stack |
| `auto_suggest` | Pipeline writes but marks as `draft` | ICP traits, pain points, objections, testimonials |
| `human_only` | Pipeline never writes, only creates alert | Pricing, metrics, positioning, legal structure |

**Relationship between templates:**

```
product-profile.yaml (1 per product, permanent)
     |
     +-- campaigns/2026-03-challenge.md  (launch-campaign, per event)
     +-- campaigns/2026-06-webinar.md
     |
     +-- curriculum/{slug}-curriculum.yaml (curriculum-detail, companion)
     |     +-- courses[]
     |           +-- modules[]
     |                 +-- lessons[] (title, synopsis, duration, format, materials)
     |
     +-- .staging/                        (pipeline insights awaiting promotion)
         +-- MEET-0043.yaml
         +-- MEET-0060.yaml
```

**Curriculum companion file:**
- `product-profile.yaml` Section 15 contains the curriculum INDEX (summary, totals, course list, retention fields)
- `curriculum-detail.yaml` contains the full tree (course > module > lesson with all fields)
- This split prevents the profile from bloating to 4000+ lines for products with hundreds of lessons

Results from `launch-campaign.results.retroalimentacao` feed back into the `product-profile` (validated angles, new testimonials, new objections, ICP refinements).

---

## Integration with Mega Brain

These templates are used by:

- **Cargo agents** (in `agents/cargo/`) that produce structured outputs following these schemas
- **MCE pipeline** (in `engine/intelligence/pipeline/`) that routes extracted knowledge into the correct template format
- **Workspace artifacts** (in `workspace/businesses/`) that are populated instances of these templates
