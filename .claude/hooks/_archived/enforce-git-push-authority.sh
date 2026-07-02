#!/bin/bash
# enforce-git-push-authority.sh (project-level override)
# PreToolUse hook: blocks "git push" unless @devops agent is active
# Fix: checks MEGABRAIN_ACTIVE_AGENT env var — allows push for devops/github-devops
# Uses node (not jq) for JSON parsing — works on Windows/Git Bash
# FAIL-CLOSED: if parsing fails, blocks the command

INPUT=$(cat)

# Extract command from JSON using node (available on all Mega Brain systems)
COMMAND=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try{console.log(JSON.parse(d).tool_input.command||'')}
    catch(e){process.exit(1)}
  });
" 2>/dev/null)

# Fail-closed: if node parsing failed, block the command
if [ $? -ne 0 ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Hook failed to parse input — blocking for safety. Contact @devops."}}'
  exit 0
fi

# Only check git push commands
if echo "$COMMAND" | grep -qiE '\bgit\s+push\b'; then
  # Allow if @devops agent is active (devops or github-devops for backward compat)
  if [ "$MEGABRAIN_ACTIVE_AGENT" = "devops" ] || [ "$MEGABRAIN_ACTIVE_AGENT" = "github-devops" ]; then
    exit 0
  fi

  # Also check if the command itself sets the env var inline (e.g., MEGABRAIN_ACTIVE_AGENT=devops git push)
  if echo "$COMMAND" | grep -qiE 'MEGABRAIN_ACTIVE_AGENT=devops'; then
    exit 0
  fi

  # Block for all other agents
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Git push is EXCLUSIVE to @devops agent. Activate @devops for push operations."}}'
  exit 0
fi

# Allow all other commands
exit 0
