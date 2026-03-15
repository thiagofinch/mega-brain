# Synapse Rules Digest (Auto-Generated)

> Generated: 2026-03-15 19:46 UTC
> Source: core/engine/rules/*.yaml
> Rules: 26 across 3 layers

## L0: Constitution (block/warn -- always active)

- ⛔ **no-secrets-in-files** [block]: Never store API keys, tokens, or credentials in tracked files. Use .env and reference-only entries.
- ⚠ **no-hardcoded-paths** [warn]: Use core.paths ROUTING constants, not hardcoded paths
- ⚠ **epistemic-honesty** [warn]: Separate facts (with sources) from recommendations. Declare confidence level. Never present hypothesis as fact.
- ⛔ **agent-integrity** [block]: All agent content must be 100% traceable to sources. Zero invention. Every assertion needs ^[SOURCE] citation.
- ⛔ **formal-workflow-required** [block]: Todo briefing de projeto/epic DEVE seguir o fluxo formal: @pm (PRD) -> @architect (viabilidade) -> @sm (stories com DoD) -> @po (backlog priorizado) -> execucao por story (@dev -> @qa -> @devops). Nunca pular direto para codigo.
- ⛔ **agent-traceability** [block]: All agent files (AGENT.md, SOUL.md, MEMORY.md) must have traceable citations to source files. Navigation chain AGENT -> SOUL -> MEMORY -> DNA -> SOURCES must be verifiable.
- ⛔ **no-invention** [block]: Never invent content for agents. Fortifying (expanding within DNA limits) is allowed; inventing (creating content not in sources) is prohibited. If information is not found after 5 search iterations, declare it absent.
- ⛔ **mcp-credentials-env-only** [block]: MCP server configurations must never contain plaintext tokens. All credentials must use environment variables via shell profile or .env file.

## L1: Global Rules (project-wide)

- ⚠ **sequential-processing** [warn]: Do not advance pipeline steps without completing the current one. Phases are sequential and blocking.
- ℹ **dual-location-logging** [info]: Pipeline processing generates logs in both markdown and JSONL (dual-location). If it was not logged, it was not processed.
- ⚠ **directory-contract** [warn]: All output must land in paths defined by core/paths.py ROUTING. See reference/DIRECTORY-CONTRACT.md for the full contract.
- ⚠ **template-enforcement** [warn]: Agent creation must follow Template V3 structure with all 11 mandatory parts and traceable citations.
- ⚠ **cascading-mandatory** [warn]: Knowledge cascading to dossiers, playbooks, and agents is mandatory after extraction. Existing dossiers must be updated, not ignored.
- ⚠ **hook-timeout-required** [warn]: Every hook in settings.json must have a timeout value (30s recommended). Hooks must use proper exit codes 0 (success), 1 (warning), 2 (block).
- ℹ **mcp-native-tools-first** [info]: Always prefer native Claude Code tools (Read, Write, Edit, Glob, Grep, Bash) over MCP servers for local file operations.
- ⚠ **session-persistence** [warn]: Session state must be saved automatically at key checkpoints (batch completion, significant actions, before destructive operations). Use .claude/sessions/ for logs.
- ℹ **plan-mode-complex-tasks** [info]: Complex tasks (new features, multi-file refactors, large batches) should use plan mode before execution. Plans save to docs/plans/.
- ⚠ **source-marking** [warn]: Every file entering the pipeline must have clear source identification. Format [SOURCE]_[ORIGINAL_NAME].[ext]. No anonymous files allowed.

## L6: Keyword Rules (keyword-triggered)

- ℹ **batch-processing-rules** [info]: Batch processing: log every batch with template V2 (14 sections), update MISSION-STATE.json, verify before advancing. Show complete log in chat.  tags: batch, pipeline, processing
- ℹ **agent-creation-rules** [info]: Agent creation: use Template V3 with 11 mandatory parts, ASCII headers, progress bars, traceable citations ^[SOURCE:file:line]. Validate all parts before saving.  tags: agent, create, dossier
- ℹ **github-workflow-rules** [info]: Code changes: follow Issue -> Branch -> PR -> Merge workflow. Never commit directly to main. 6 verification levels required before merge.  tags: github, git, push, pr, branch
- ℹ **phase5-execution** [info]: Phase 5 execution: use official templates per subfase (5.1-5.6), process one source at a time (isolation), advance automatically between subfases without asking, cascade to dossiers/agents/playbooks.  tags: phase, dossier, cascading, agent
- ℹ **conclave-protocol** [info]: Conclave (council debate): agents in /agents/ are activated only via /conclave for formal multi-agent deliberation. Sub-agents in /.claude/jarvis/sub-agents/ handle day-to-day delegation.  tags: conclave, council, debate
- ℹ **source-sync-rules** [info]: Source sync: before processing new content, run /source-sync to compare planilha snapshot vs local files. Tag at source (planilha) before download. Update PLANILHA-INDEX.json after sync.  tags: sync, planilha, download
- ℹ **session-management** [info]: Session management: read MISSION-STATE.json at session start, report exact position with numbers (phase, batch, percentage). Save session on completion, significant actions, and before exit.  tags: session, save, resume, state
- ℹ **knowledge-bucket-routing** [info]: Knowledge bucket routing: expert content -> knowledge/external/, company content -> knowledge/business/, personal content -> knowledge/personal/, operational docs -> workspace/. Each bucket has isolated RAG index.  tags: bucket, inbox, knowledge, personal, external, business

## Protocol References

For full protocol documents, see:
- Agent cognition: `reference/AGENT-COGNITION-PROTOCOL.md`
- Agent integrity: `reference/AGENT-INTEGRITY-PROTOCOL.md`
- Epistemic standards: `reference/EPISTEMIC-PROTOCOL.md`
- Directory contract: `reference/DIRECTORY-CONTRACT.md`

---

*Auto-generated. Do not edit. Regenerate: `python3 -m core.governance.engine digest`*
