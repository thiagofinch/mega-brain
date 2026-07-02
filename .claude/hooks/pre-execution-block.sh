#!/usr/bin/env bash
# pre-execution-block.sh — P1 (plan-only) defense-in-depth at hook layer
#
# Story: STORY-PA-5.2
# MODE: WARN — promote to BLOCK after 2 weeks zero false positives
# Trigger: PreToolUse
# Behavior:
#   - if MEGABRAIN_ACTIVE_AGENT identifies plan-architect AND tool is execution-side-effect type → BLOCK
#   - else → no-op (exit 0)
# WARN_ONLY guard: if WARN_ONLY=true (default), log + exit 0; if WARN_ONLY=false, block

set -u

WARN_ONLY="${WARN_ONLY:-true}"
ACTIVE_AGENT="${MEGABRAIN_ACTIVE_AGENT:-}"

# Detect execution-side-effect tools by name (read from env if Claude Code provides it)
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

# Tools that produce execution side effects (not plan-only)
EXEC_TOOLS=("Bash" "Edit" "Write" "git" "TeamCreate" "TaskCreate")

is_exec_tool() {
  local name="$1"
  for t in "${EXEC_TOOLS[@]}"; do
    [[ "$name" == "$t" ]] && return 0
  done
  return 1
}

is_plan_architect() {
  case "$1" in
    plan-architect|orquestrador-global--plan-architect|@plan-architect|@orquestrador-global--plan-architect)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# Only act if plan-architect is active
if ! is_plan_architect "$ACTIVE_AGENT"; then
  exit 0
fi

# Only act if tool is exec-type
if [[ -n "$TOOL_NAME" ]] && ! is_exec_tool "$TOOL_NAME"; then
  exit 0
fi

REASON='plan-architect P1 enforcement: execution side effects are blocked. Use plan_only=true and emit plans only.'

if [[ "$WARN_ONLY" == "true" ]]; then
  # WARN mode: log + allow (do NOT block during grace period)
  echo "[pre-execution-block][WARN] $REASON" >&2
  exit 0
else
  # BLOCK mode (post-grace)
  cat <<JSON
{"decision":"block","reason":"$REASON"}
JSON
  exit 1
fi
