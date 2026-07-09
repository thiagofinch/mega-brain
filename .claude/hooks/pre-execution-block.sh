#!/usr/bin/env bash
# pre-execution-block.sh — P1 (plan-only) defense-in-depth at hook layer
#
# Story: STORY-PA-5.2
# Node:  N3 of FROZEN plan 2026-07-07_wave1-ft-execution-bridge (SOT R5)
# GRACE PERIOD CLOSED 2026-07-07 — hook now ENFORCES (BLOCK) by default.
#   Previously WARN_ONLY defaulted to true AND the hook was not registered in
#   settings, so it never blocked anything. Both are now fixed: default flipped
#   to enforcing, and the hook is registered under hooks.PreToolUse.
# Trigger: PreToolUse
# Behavior:
#   - if MEGABRAIN_ACTIVE_AGENT identifies plan-architect AND tool is execution-side-effect type:
#       * Write/Edit whose target path is under outputs/plans/ → ALLOW (plan emission is the job)
#       * Write/Edit outside outputs/plans/ → BLOCK
#       * other exec tools (Bash git push, TeamCreate, etc.) → BLOCK
#   - else (not plan-architect, or non-exec tool) → no-op (exit 0)
# WARN_ONLY guard: if WARN_ONLY=true, log + exit 0 (escape hatch for false positives);
#                  default is WARN_ONLY=false → enforce.

set -u

WARN_ONLY="${WARN_ONLY:-false}"
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

# Read the PreToolUse stdin JSON payload (may be empty when invoked outside Claude Code).
# PreToolUse hooks receive tool_input JSON on stdin; we extract .tool_input.file_path.
STDIN_PAYLOAD=""
if [ ! -t 0 ]; then
  STDIN_PAYLOAD="$(cat 2>/dev/null || true)"
fi

extract_file_path() {
  local payload="$1"
  [[ -z "$payload" ]] && return 0
  if command -v jq >/dev/null 2>&1; then
    jq -r '.tool_input.file_path // empty' <<<"$payload" 2>/dev/null
  else
    # grep/sed fallback: pull the first "file_path":"..." value from the JSON
    printf '%s' "$payload" \
      | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' \
      | head -n1 \
      | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/'
  fi
}

# Is a given path under outputs/plans/ ? Handles relative ("outputs/plans/...")
# and absolute paths that contain the repo-relative "outputs/plans/" segment.
is_plan_path() {
  local p="$1"
  [[ -z "$p" ]] && return 1
  case "$p" in
    outputs/plans/*|./outputs/plans/*|*/outputs/plans/*)
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

# PATH ALLOWLIST: Write/Edit targeting outputs/plans/ is the plan-architect's job.
# The P1 promise is "blocks Write OUTSIDE outputs/plans/", not "blocks Write entirely".
if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" ]]; then
  FILE_PATH="$(extract_file_path "$STDIN_PAYLOAD")"
  if is_plan_path "$FILE_PATH"; then
    # Allowed: plan emission under outputs/plans/
    exit 0
  fi
fi

REASON='plan-architect P1 enforcement: execution side effects are blocked. Emit plans only under outputs/plans/ (plan_only=true).'

if [[ "$WARN_ONLY" == "true" ]]; then
  # WARN mode: log + allow (escape hatch — NOT the default post-grace)
  echo "[pre-execution-block][WARN] $REASON" >&2
  exit 0
else
  # BLOCK mode (default post-grace, 2026-07-07)
  cat <<JSON
{"decision":"block","reason":"$REASON"}
JSON
  exit 1
fi
