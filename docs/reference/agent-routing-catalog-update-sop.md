# Agent Routing Catalog Update SOP

**Owner:** `@pm` for operating procedure, `@qa` for validation, `@devops` for
CI/push authority.

Use this SOP when a change can alter public agent routing metadata or the
generated catalog.

## When To Refresh

Run `npm run build:agent-routing-index` after changing any of these inputs:

- `squads/**`, especially `config.yaml` and `agents/*.md`
- `.claude/skills/**`
- `.data/agent-routing-index.schema.json`
- `squads/mega-brain/data/chief-interface-registry.yaml`
- `squads/mega-brain/data/agent-registry.yaml`
- `docs/reference/rules/agent-routing.md`
- `docs/reference/rules/entry-point-heuristic.md`
- `docs/reference/rules/codex-agent-projection-sot-decision.md`
- `docs/reference/agent-routing-catalog-update-sop.md`
- `docs/reference/agent-routing-asi-integration-contract.md`
- ARCG scripts: `scripts/agents-recommend.js`,
  `scripts/build-agent-routing-index.js`,
  `scripts/validate-agent-routing.js`,
  `scripts/validate-agent-routing-fixtures.js`
- Recommendation fixtures in `tests/fixtures/agent-routing-recommendations.yaml`

## Standard Commands

```bash
npm run build:agent-routing-index
npm run validate:agent-routing -- --strict
npm run validate:agent-routing-fixtures
```

For CI-equivalent validation:

```bash
npm run validate:agent-routing:ci
```

## Interpreting Failures

`[STALE]` means a generated artifact no longer matches the source catalog.
Regenerate the index with `npm run build:agent-routing-index`, review the diff,
and keep only changes explained by the source edit.

Strict metadata failures mean a public candidate has missing, placeholder or
conflicting metadata. Fix the source of truth first. Do not patch only the
generated index.

Fixture failures mean recommendation behavior changed. Either correct the
catalog/ranking input or update the fixture with an explicit story-backed
reason.

## Source-of-Truth Rule

`.codex/agents` is projection-only for ARCG until a separate validated SOT
decision promotes it. It can be counted as advisory projection data, but it must
not outrank squad configs, canonical agent cards, `.claude/skills`, chief
registry or agent registry sources.

## Handoff

Record any non-obvious catalog refresh in `outputs/routing/catalog-governance/`
and link it from the relevant story. The output should name the changed source,
the generated artifacts affected, commands run and any unresolved warnings.
