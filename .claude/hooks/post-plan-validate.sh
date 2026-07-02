#!/usr/bin/env bash
# post-plan-validate.sh — auto-validate emitted plan YAMLs
#
# Story: STORY-PA-5.2
# MODE: WARN — promote to BLOCK after 2 weeks zero false positives
# Trigger: PostToolUse (file write)
# Behavior:
#   - When a YAML in outputs/plans/**/*.yaml is written, run validate-plan.js
#   - On exit 1: signal block with reason
# WARN_ONLY guard: if WARN_ONLY=true (default), log + exit 0

set -u

WARN_ONLY="${WARN_ONLY:-true}"
FILE_PATH="${CLAUDE_FILE_PATH:-${1:-}}"

# Only act on plan YAMLs
if [[ -z "$FILE_PATH" ]] || [[ "$FILE_PATH" != *outputs/plans/*.yaml ]]; then
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VALIDATOR="$REPO_ROOT/squads/orquestrador-global/scripts/validate-plan.js"

if [[ ! -f "$VALIDATOR" ]]; then
  echo "[post-plan-validate][WARN] validator script missing: $VALIDATOR" >&2
  exit 0
fi

OUT="$(node "$VALIDATOR" "$FILE_PATH" 2>&1)"
EXIT_CODE=$?

if [[ "$EXIT_CODE" == "0" ]]; then
  exit 0
fi

REASON="Plan validation failed for $FILE_PATH (exit $EXIT_CODE). See validator output for details."

if [[ "$WARN_ONLY" == "true" ]]; then
  echo "[post-plan-validate][WARN] $REASON" >&2
  echo "$OUT" >&2
  exit 0
else
  cat <<JSON
{"decision":"block","reason":"$REASON","validator_output":$(echo "$OUT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}
JSON
  exit 1
fi
