---
paths:
  - "workspace/**"
  - "workspace/businesses/**"
  - "workspace/domains/**"
---

# Workspace Document Rules

Applies when editing files in `workspace/`.

## Workspace Structure

The workspace is domain-centric, organized as follows:

```
workspace/
  workspace.yaml              -- Manifest (company, businesses, domains)
  businesses/{bu}/             -- Business-specific data
    company/                   -- Company profile
    operations/                -- Team structure
    products/                  -- Product portfolio
  domains/                     -- Domain definitions (entities + workflows)
    brand/
    decisions/
    finance/
    meetings/
    operations/
    products/
    projects/
    team/
    tech/
  _system/                     -- System configuration
    canonical-sources.yaml     -- Source of truth mapping
    clickup-mappings.yaml      -- ClickUp integration mappings
    config/                    -- Provider interfaces, infrastructure sync
```

## Document Governance

1. **Format:** All workspace documents are YAML
2. **States:** PLACEHOLDER -> DRAFT -> POPULATED -> VALIDATED -> APPROVED -> STALE -> ARCHIVED
3. **Owner:** Each domain has an owner -- only that owner should modify its entities/workflows
4. **Dependencies:** Check upstream/downstream dependencies before editing

## Domain Structure

Each domain directory contains:
- `entities.yaml` -- Entity definitions for that domain
- `workflows.yaml` -- Workflow definitions (where applicable)

## Business Data

Business-specific data lives under `workspace/businesses/{bu}/` and is organized by concern:
- `company/` -- Company profile, legal identity
- `operations/` -- Team structure, operational processes
- `products/` -- Product portfolio, catalog

## PT-BR Acentuacao (NON-NEGOTIABLE)

SEMPRE usar acentuacao correta em portugues brasileiro:
- nao (nunca "nao"), e, voce, esta, operacao, gestao, modulo
- conteudo, industria, eficiencia, cenario, proporcao
- heuristicas, validacao, metodologia, proprietaria
