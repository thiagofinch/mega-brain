#!/bin/bash
# enforce-prompt-safety.sh — STORY-116.2 Security Hardening
# PreToolUse hook: scans prompt content for injection threats using prompt-guard.js
#
# Mode: WARN (sprint 1 — warn-first mode)
# To switch to BLOCK mode after sprint validation:
#   Change SAFETY_MODE below from "warn" to "block"
#
# Constitution: Article V — Quality First
# Story: STORY-116.2 (EPIC-116 — MegaBrain Engine Absorption)

# ---- SPRINT TOGGLE ----
# Set to "block" after sprint 1 validation completes
SAFETY_MODE="warn"
# -----------------------

INPUT=$(cat)

REPO=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO" ]; then
  exit 0
fi

GUARD_SCRIPT="$REPO/mega-brain-core/core/permissions/prompt-guard.js"

# If guard script not present, skip silently
if [ ! -f "$GUARD_SCRIPT" ]; then
  exit 0
fi

# Extract the prompt/content to scan from the hook input JSON.
# We scan the full tool input as a string to catch injection in any field.
SCAN_PAYLOAD=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data', c => d += c);
  process.stdin.on('end', () => {
    try {
      const parsed = JSON.parse(d);
      // Concatenate all string values from tool_input for scanning
      const values = [];
      function collect(obj) {
        if (typeof obj === 'string') values.push(obj);
        else if (obj && typeof obj === 'object') Object.values(obj).forEach(collect);
      }
      collect(parsed.tool_input || {});
      console.log(values.join(' '));
    } catch(e) {
      process.exit(0);
    }
  });
" 2>/dev/null)

if [ -z "$SCAN_PAYLOAD" ]; then
  exit 0
fi

# Fix TD-116.2-001: SCAN_PAYLOAD must be exported for child node process to inherit
export SCAN_PAYLOAD

# Run prompt guard scan
SCAN_RESULT=$(node -e "
const { scan } = require('$GUARD_SCRIPT');
const input = process.env.SCAN_PAYLOAD || '';
try {
  const result = scan(input);
  if (!result.safe) {
    const threats = result.threats.map(t => t.id + ':' + t.name + '(' + t.severity + ')').join(', ');
    console.log(JSON.stringify({ safe: false, threats, maxSeverity: result.maxSeverity }));
  } else {
    console.log(JSON.stringify({ safe: true }));
  }
} catch(e) {
  console.log(JSON.stringify({ safe: true, error: e.message }));
}
" 2>/dev/null)

if [ -z "$SCAN_RESULT" ]; then
  exit 0
fi

IS_SAFE=$(echo "$SCAN_RESULT" | node -e "
  let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
    try{console.log(JSON.parse(d).safe);}catch{console.log('true');}
  });" 2>/dev/null)

if [ "$IS_SAFE" = "false" ]; then
  THREATS=$(echo "$SCAN_RESULT" | node -e "
    let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
      try{const p=JSON.parse(d);console.log(p.threats||'unknown');}catch{console.log('unknown');}
    });" 2>/dev/null)
  MAX_SEV=$(echo "$SCAN_RESULT" | node -e "
    let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{
      try{const p=JSON.parse(d);console.log(p.maxSeverity||'HIGH');}catch{console.log('HIGH');}
    });" 2>/dev/null)

  if [ "$SAFETY_MODE" = "block" ]; then
    REASON="[STORY-116.2] Prompt injection threat detected (${MAX_SEV}): ${THREATS}. Tool call blocked. Set SAFETY_MODE=warn in enforce-prompt-safety.sh for warn-only mode."
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' \
      "$(echo "$REASON" | tr '"' "'" | tr '\n' ' ')"
    exit 0
  else
    # WARN mode — log to stderr and allow
    echo "[WARN][enforce-prompt-safety] Prompt injection threat detected (${MAX_SEV}): ${THREATS}. Tool call allowed (warn-first sprint mode)." >&2
    exit 0
  fi
fi

# Safe — allow
exit 0
