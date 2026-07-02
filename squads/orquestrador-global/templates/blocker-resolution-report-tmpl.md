# Blocker Resolution Report — `{blocker_id}`

> **Demanda:** {demand_summary}
> **Data:** {created_at}
> **Status:** {resolved | partial | approval_required | blocked_after_resolution_attempts}

## Blocker

| Campo | Valor |
|---|---|
| Tipo | {login_required / rate_limit / missing_tool / missing_credential / missing_capability / service_unavailable / other} |
| Subobjetivo bloqueado | {subobjective} |
| Evidência | `{command_or_url}` → `{status_or_error}` |
| Impacto | {impact} |

## L1 — Workaround Local

| Tentativa | Resultado | Artifact |
|---|---|---|
| {tool/command} | {success/partial/fail} | {path_or_none} |

## L2 — Capability Search

| Scope | Pattern | Matches | Verdict |
|---|---|---:|---|
| `{paths}` | `{pattern}` | {n} | {covered / gap / partial} |

## L3 — External Service Options

| Rank | Serviço | Resolve? | Credencial | Custo | Risco | Observação |
|---:|---|---|---|---|---|---|
| 1 | {service} | {yes/partial/no} | {env/token/cookies/none} | {estimate} | {low/medium/high} | {note} |

## Recomendação

{recommended_action}

## Approval Request

Preencher apenas quando necessário:

- **Aprovação necessária:** {yes/no}
- **O que aprovar:** {exact_request}
- **Env var/token/cookie:** `{name_or_none}`
- **Fallback se negado:** {fallback}

## Current Status

{current_status}

