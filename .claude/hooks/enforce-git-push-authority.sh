#!/bin/bash
# enforce-git-push-authority.sh (project-level override)
# PreToolUse hook: blocks "git push" unless @devops agent is active
# Fix: checks MEGABRAIN_ACTIVE_AGENT env var — allows push for devops/github-devops
# Uses node (not jq) for JSON parsing — works on Windows/Git Bash
# FAIL-CLOSED on git push: if parsing fails AND command looks like push, block.
# FAIL-OPEN on other commands: if parsing fails for non-push, allow through.

INPUT=$(cat)

# Try node first (preferred — handles all JSON edge cases)
COMMAND=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try{console.log(JSON.parse(d).tool_input.command||'')}
    catch(e){process.exit(1)}
  });
" 2>/dev/null)
NODE_EXIT=$?

# If node parsing failed, try Python as fallback
if [ $NODE_EXIT -ne 0 ]; then
  COMMAND=$(echo "$INPUT" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  print(d.get('tool_input',{}).get('command',''))
except:
  sys.exit(1)
" 2>/dev/null)
  PYTHON_EXIT=$?

  # If both parsers failed: apply targeted fail-closed ONLY if raw input looks like git push
  if [ $PYTHON_EXIT -ne 0 ]; then
    if echo "$INPUT" | grep -qiE '"command"\s*:\s*"[^"]*git\s+push'; then
      echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Hook failed to parse input and command appears to be git push — blocking for safety. Contact @devops."}}'
      exit 0
    fi
    # Non-push command, parsing failed — allow through (fail-open for non-push)
    exit 0
  fi
fi

# Only check git push commands
if echo "$COMMAND" | grep -qiE '\bgit\s+push\b'; then
  # Accept either MEGABRAIN_ACTIVE_AGENT (legacy) or MEGABRAIN_ACTIVE_AGENT (canonical after framework rename).
  # Accepted values: devops | github-devops | megabrain-devops (any squad's devops short name).
  ACTIVE_AGENT="${MEGABRAIN_ACTIVE_AGENT:-${MEGABRAIN_ACTIVE_AGENT:-}}"
  case "$ACTIVE_AGENT" in
    devops|github-devops|megabrain-devops) exit 0 ;;
  esac

  # Also accept inline env var set on the command itself (either prefix, accepted values above).
  if echo "$COMMAND" | grep -qiE '(Mega Brain|Mega Brain)_ACTIVE_AGENT=(devops|github-devops|megabrain-devops)'; then
    exit 0
  fi

  # Block for all other agents — build a helpful error message
  ACTIVE="${ACTIVE_AGENT:-unknown}"
  REASON="BLOCKED: \`git push\` is exclusive to @devops (Constitution II). Current agent: @${ACTIVE}. Set MEGABRAIN_ACTIVE_AGENT=devops (or MEGABRAIN_ACTIVE_AGENT=devops for legacy) before invoking, or delegate to a devops subagent."
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"${REASON}\"}}"
  exit 0
fi

# Allow all other commands
exit 0
