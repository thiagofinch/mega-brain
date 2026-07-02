---
paths:
  - ".mega-brain/handoffs/**"
  - "docs/sessions/**"
  - "docs/handoffs/**"
---

# Agent Handoff Protocol

Applies when switching between agents or when context compaction occurs.

## When to Create Handoff

Create a handoff artifact when:
1. Agent switching (e.g., `@dev` → `@devops` for push)
2. Context window approaching limit
3. Session ending with work in progress
4. Cross-squad collaboration needed

## Handoff Artifact Format

```yaml
# .mega-brain/handoffs/handoff-{from}-to-{to}-{date}.yaml
handoff:
  from: "@dev"
  to: "@devops"
  date: "2026-03-09"
  story: "Story X.Y"
  branch: "feat/X.Y-feature-name"

context:
  what_was_done:
    - "Created feature page at apps/myapp/src/pages/feature.tsx"
    - "Integrated authentication integration"

  what_remains:
    - "Push to remote"
    - "Create PR"

  files_modified:
    - apps/myapp/src/pages/feature.tsx
    - apps/myapp/src/hooks/use-feature.ts

  decisions_made:
    - "Used authentication method per Story X.Y AC"

  blockers: []
```

## Handoff Location

Store at: `.mega-brain/handoffs/` (gitignored -- runtime state only)

## Key Principle

Handoff artifacts carry ~400 tokens of context instead of reloading
full agent personas (~3-5K tokens). This preserves context window budget.

---

## Artifact-Handoff Protocol

Handoffs that carry artifacts follow the Artifact-Handoff Protocol with 3 scopes:

### Scopes

| Scope | Description | Signoff | Accountable |
|-------|-------------|---------|-------------|
| `intra_processo` | Dentro do mesmo processo/workflow | Não requerido | Agent pode ser |
| `intra_bu` | Entre squads da mesma BU | Recomendado | Human recomendado |
| `inter_bu` | Entre Business Units diferentes | **Obrigatório** | **Human obrigatório** |

### Inter-BU Handoff Template

```yaml
# .mega-brain/handoffs/handoff-{from}-to-{to}-{date}.yaml
handoff:
  from: "@agent-origem"
  to: "@agent-destino"
  date: "YYYY-MM-DD"
  story: "Story X.Y"
  scope: inter_bu  # intra_processo | intra_bu | inter_bu

  # REQUIRED for inter_bu scope
  signoff:
    required: true
    approver: "nome-do-humano-accountable"
    approved_at: null  # Preenchido após aprovação
    approved: false

artifacts:
  - id: "artifact-id"
    type: "artifact-type"
    template: "path/to/template"
    status: validated  # draft | validated | approved

context:
  what_was_done: []
  what_remains: []
  files_modified: []
  decisions_made: []
  blockers: []
```

### Rules

1. **intra_processo:** Standard handoff format (existing protocol above)
2. **intra_bu:** Standard format + `artifacts[]` section recommended
3. **inter_bu:** Full format with `signoff` section **mandatory** -- Constitution Article VIII
4. Human signoff is **non-negotiable** for inter-BU handoffs
5. Artifacts MUST be validated against their template before handoff (Constitution Article X)
