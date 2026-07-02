# Features Template — Schema Reference

## Purpose

This template set is the canonical schema for documenting **SaaS features/modules** — the internal building blocks of a product, distinct from the product itself and from sellable courses.

## When to use

| You are documenting... | Use template |
|---|---|
| An internal SaaS module (CRM, Flows, Checkout) | **features/** (this template) |
| A commercial product with pricing/offer/ICP | `products/product-profile.yaml` + `product-offerbook/` |
| A course with modules and lessons | `products/curriculum-detail.yaml` |
| A company-level narrative | `product-narrative/` |

## Directory contract

```
workspace/businesses/{bu}/features/
├── _INDEX.yaml                   ← registry of all features in this BU
├── README.md                     ← catalog / map for humans
└── {feature-slug}/
    ├── FEATURE.md                ← narrative (context, stories, decisions)
    └── feature-spec.yaml         ← structured machine-readable spec
```

## Two files per feature, on purpose

| File | Audience | Kind of truth |
|---|---|---|
| `FEATURE.md` | Humans (PMs, designers, exec) | Narrative — why it exists, how it composes, how it evolves |
| `feature-spec.yaml` | Agents, automations, dashboards | Structured — machine-queryable fields with IDs, stages, metrics |

Both reference the same feature and must stay in sync. The YAML is the source of truth for automation; the MD is the source of truth for humans.

## Linkage with other schemas

- **`offerbook.yaml`** of the parent product lists features in `features_registry.items: [feature-slug-1, feature-slug-2, ...]`.
- Each `feature-spec.yaml` has `identity.parent_product: {product-slug}` pointing back.
- The `_INDEX.yaml` of `features/` is the authoritative catalog for search, aggregation, and validation.

## Field cheat-sheet

| Field | Required | Why it matters |
|---|---|---|
| `identity.feature_id` | yes | Stable canonical ID (e.g. `CLK-001`) — never change |
| `identity.feature_slug` | yes | Must match directory name |
| `identity.parent_product` | yes | Link back to owning product |
| `lifecycle.stage` | yes | `planned \| in-progress \| beta \| live \| deprecated \| sunset` |
| `composability.depends_on` | yes | Feature graph — critical for impact analysis |
| `composability.can_be_micro_offer` | no | Flags product-led growth candidates |
| `technical.ai_powered` | yes | Required for AI roadmap tracking |
| `ownership.tech_lead` | yes | Single person accountable |
| `metrics.north_star` | recommended | One metric that captures feature health |
| `evidence.sources` | yes | Every claim must be traceable to a call/doc |

## Lifecycle states

```
planned ──▶ in-progress ──▶ beta ──▶ live ──▶ deprecated ──▶ sunset
                                       │
                                       └──▶ (major-rewrite) ──▶ planned
```

## Confidence levels

- **high** — direct quote from multiple calls, shipped code exists
- **medium** — summarized from 1-2 calls, not yet validated
- **low** — inferred, needs human validation before acting on

## Versioning

- Schema version lives in `_meta.schema_version` (semver)
- Breaking changes to the schema → major bump, migration script required
- Feature spec itself has no version — evolves in place, git is the audit log
