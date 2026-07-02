# Blocker Resolution Protocol

## Purpose

External blockers are not final answers. When a demand hits missing access, missing data, missing tooling, missing skills, platform restrictions, credentials, service limits or unavailable agents, the `orquestrador-global` must actively search for a resolution path before returning to the user.

The correct output is either:

- a resolved path with evidence;
- a ranked set of viable options with one recommended next action;
- or an approval request for the smallest credential, cost or risk-bearing step needed to proceed.

## Trigger Conditions

Apply this protocol when any of these appears:

- login required;
- rate limit;
- missing API token;
- unavailable connector;
- missing local CLI/package;
- missing skill, agent, squad or service;
- external platform blocks public access;
- input file absent but can be acquired through a known route;
- execution cannot continue without user approval, legal approval or paid service.

## Resolution Ladder

### L0 — Confirm the Blocker

Record concrete evidence:

- command or URL attempted;
- status/error;
- artifact path, if any;
- what is blocked and what is still possible.

Do not stop at this step.

### L1 — Local No-Approval Workaround

Try routes that do not require new credentials or paid services:

- installed CLIs (`yt-dlp`, `ffmpeg`, `whisper`, `gh`, vendor CLIs);
- existing repo scripts;
- open-source packages already available;
- public metadata;
- files already supplied by the user.

If a local workaround succeeds partially, continue with the available subset and record the remaining gap.

### L2 — Existing Capability Search

Search the repo capability surface before inventing:

- `squads/**/config.yaml`;
- `squads/**/tasks/**`;
- `squads/**/workflows/**`;
- `.claude/skills/**`;
- `.agents/skills/**`;
- `services/**`;
- `apps/**`;
- `packages/**`.

If a capability exists, route or hand off to it.

### L3 — External Service Candidate

When local/repo capability is insufficient, identify external services that can solve the blocker. Rank by:

1. fit to the exact blocker;
2. official/authorized path;
3. credential scope required;
4. cost and latency;
5. compliance and platform risk;
6. integration complexity.

For Instagram/social extraction, preferred classes are:

- official API or approved export when available;
- Apify actor with explicit API token and dataset export;
- user-provided browser cookies for local `yt-dlp` only when the user approves;
- manual capture/export when service automation is not appropriate.

### L4 — Approval Gate

Ask for approval only when needed for one of these:

- API token or credential;
- paid run;
- browser cookies/session export;
- account login;
- install of non-trivial external service;
- action with legal/platform/compliance risk.

The approval request must be specific:

- recommended option;
- exact credential/env var needed;
- estimated cost/risk;
- expected output;
- fallback if denied.

### L5 — Persist Resolution Artifact

For MEDIUM+ or recurring blockers, emit a blocker-resolution artifact alongside the run:

```text
blocker-resolution-report.md
```

It must include:

- blocker evidence;
- attempted local workarounds;
- existing capability search;
- external service options;
- recommended option;
- approval required or not;
- current status.

### L6 — Only Then Mark Blocked

The final status may be `blocked` only after:

- local workaround was attempted or ruled out with evidence;
- repo capabilities were searched;
- external service candidates were ranked;
- required approval was requested when necessary.

## Required Language

Avoid final responses like:

```text
Não consigo acessar, precisa fornecer o arquivo.
```

Use:

```text
O acesso público falhou por login/rate-limit. Tentei local com X e consegui Y. Falta Z. Melhor próximo caminho: Apify actor com APIFY_TOKEN, custo estimado N, output dataset JSON. Aprova usar esse serviço?
```

## Plan-Architect Rule

Because `plan-architect` is plan-only, it must not run the remediation itself. It must add remediation nodes, approval gates and service candidates to the DAG.

Required plan fields when a blocker exists:

- blocker node;
- local workaround node;
- capability search node;
- service candidate node;
- approval gate when needed;
- fallback branch.

## Execution Rule

Execution agents may run local no-approval workarounds. They may not use credentials, paid services, browser cookies or account login without explicit approval.

## Acceptance Criteria

A blocker response passes when:

- it contains evidence;
- at least one workaround was tried or a specific approval-gated option was proposed;
- the recommended option is clear;
- the process did not invent unavailable source data;
- the next action is executable.

