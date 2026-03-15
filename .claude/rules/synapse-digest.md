# Synapse Rules Digest (Auto-Generated)

> Generated: 2026-03-15 16:00 UTC
> Source: core/engine/rules/*.yaml
> Rules: 13 across 3 layers

## L0: Constitution (block/warn -- always active)

- ⛔ **no-secrets-in-files** [block]: Never store API keys, tokens, or credentials in tracked files
- ⚠ **no-hardcoded-paths** [warn]: Use core.paths ROUTING constants, not hardcoded paths
- ⚠ **epistemic-honesty** [warn]: Separate facts (with sources) from recommendations. Declare confidence level.
- ⛔ **agent-integrity** [block]: All agent content must be 100% traceable to sources. Zero invention.
- ⛔ **formal-workflow-required** [block]: Todo briefing de projeto/epic DEVE seguir o fluxo formal: @pm (PRD) → @architect (viabilidade) → @sm (stories com DoD) → @po (backlog priorizado) → execução por story (@dev → @qa → @devops). Nunca pular direto para código.

## L1: Global Rules (project-wide)

- ⚠ **sequential-processing** [warn]: Do not advance pipeline steps without completing the current one
- ℹ **dual-location-logging** [info]: Pipeline processing generates logs in both markdown and JSONL
- ⚠ **directory-contract** [warn]: All output must land in paths defined by core/paths.py ROUTING
- ⚠ **template-enforcement** [warn]: Agent creation must follow Template V3 structure
- ⚠ **cascading-mandatory** [warn]: Knowledge cascading to dossiers, playbooks, agents is mandatory after extraction

## L6: Keyword Rules (keyword-triggered)

- ℹ **batch-processing-rules** [info]: Batch processing: log every batch, update state, verify before advancing  tags: batch, pipeline, processing
- ℹ **agent-creation-rules** [info]: Agent creation: use Template V3, include 11 parts, traceable citations  tags: agent, create, dossier
- ℹ **github-workflow-rules** [info]: Code changes: follow Issue→Branch→PR→Merge workflow  tags: github, git, push, pr, branch

## Protocol References

For full protocol documents, see:
- Agent cognition: `reference/AGENT-COGNITION-PROTOCOL.md`
- Agent integrity: `reference/AGENT-INTEGRITY-PROTOCOL.md`
- Epistemic standards: `reference/EPISTEMIC-PROTOCOL.md`
- Directory contract: `reference/DIRECTORY-CONTRACT.md`

---

*Auto-generated. Do not edit. Regenerate: `python3 -m core.governance.engine digest`*
