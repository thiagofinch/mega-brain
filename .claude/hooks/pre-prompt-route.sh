#!/usr/bin/env bash
# pre-prompt-route.sh — opt-in default routing to plan-architect
#
# Ported from the-hub (STORY-PA-5.2).
# MODE: WARN — opt-in via MEGABRAIN_AUTO_ROUTE; even when active, only injects context.
# Trigger: UserPromptSubmit
# Behavior:
#   - If MEGABRAIN_AUTO_ROUTE not "true" → no-op (default state)
#   - If MEGABRAIN_AUTO_ROUTE=true:
#       - prompt has @-prefix → no-op (user already specified agent)
#       - prompt has bypass keyword (skip-router, direto:, no-route) → no-op
#       - else → inject suggestion to route via plan-architect (does NOT force)

set -u

WARN_ONLY="${WARN_ONLY:-true}"
AUTO_ROUTE="${MEGABRAIN_AUTO_ROUTE:-false}"

# No-op unless explicitly enabled
if [[ "$AUTO_ROUTE" != "true" ]]; then
  exit 0
fi

# Read user prompt from env
PROMPT="${CLAUDE_USER_PROMPT:-${1:-}}"

# No-op if user already specified an @-agent
if [[ "$PROMPT" =~ @[a-zA-Z][a-zA-Z0-9_-]* ]]; then
  exit 0
fi

# No-op on bypass keywords
if [[ "$PROMPT" =~ (skip-router|direto:|no-route) ]]; then
  exit 0
fi

SUGGESTION='Auto-route suggestion: rotear via plan-architect (orchestration-global). Bypass com prefixo "direto:" se quiser execucao direta.'

if [[ "$WARN_ONLY" == "true" ]]; then
  echo "[pre-prompt-route][WARN] $SUGGESTION" >&2
  exit 0
else
  cat <<JSON
{"hookEventName":"UserPromptSubmit","decision":"continue","additionalContext":"$SUGGESTION"}
JSON
  exit 0
fi
