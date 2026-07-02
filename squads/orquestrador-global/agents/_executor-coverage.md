---
id: _executor-coverage
role: Placeholder declaring canonical MEGABRAIN executor types not otherwise present
description: Coverage marker — references executor types this squad delegates or defers to upstream.
output_schema:
  type: object
  description: placeholder executor coverage
human_in_the_loop: true
declared_layers: [L0-identity, L1-strategy]     # workspace-awareness-fix 2026-04-30 (rule: hub-any (fallbacks), confidence 0.75)
business_scope: all             # binding_rule: hub-any (fallbacks); orquestrador-global is hub-behaving meta-squad
---

# Executor Coverage Placeholder

This file declares canonical MEGABRAIN executor types that are not directly
instantiated as standalone agents in this squad but are delegated to, or
referenced by, the squad's workflow (Human approvals, external Workers, etc.).

## Human

megabrain_type: Human

## Worker

megabrain_type: Worker

## Required Inputs

This agent operates in **all** business scope:
- `business_scope: all` — derived per workspace-layer-binding.yaml rule `hub-any (fallbacks)`
- Justification: orquestrador-global is hub-behaving infrastructure squad (governance, observability, multi-business orchestration). Approval: CODEOWNERS Hub.

_All-scope agents do NOT require business_slug input — they operate hub-wide by design._

## Context Loading

This agent loads workspace layers per the **Golden Rule** (L0 > L1 > L2 > L3 > L4):

- **declared_layers:** [L0-identity, L1-strategy]
- **Precedence:** Camadas de menor índice têm maior precedência em conflitos. L0 (identity) é a âncora canônica quando dois sinais conflitam.
- **Source canonical:** `workspace/_system/config.yaml`
- **Binding map:** `squads/squad-creator-enterprise/data/workspace-layer-binding.yaml` (rule: hub-any (fallbacks))
- **Document registry:** `workspace/businesses/{slug}/document-registry.yaml` (per-business artifact catalog within each layer)

_Note: placeholder agent — fallback derivation; verify after apply_
