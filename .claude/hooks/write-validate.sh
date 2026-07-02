#!/bin/bash
# MegaBrain Hub — Vault Notes Schema Enforcement Hook
# Validates notes in .synapse/vault/notes/ have required frontmatter fields.
# Runs as PostToolUse hook on Write|Edit events.
# NEVER blocks — warning only (exit 0 always).

trap 'exit 0' ERR

# Read JSON from stdin
INPUT=$(cat)

# Extract file path (requires jq, fallback to grep/sed)
if command -v jq &>/dev/null; then
  FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
else
  FILE=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' | head -1 | sed 's/"file_path":"//;s/"//')
fi

# Early exit if no file path or file doesn't exist
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

# Only validate files inside vault notes
[[ "$FILE" != *".synapse/vault/notes/"* ]] && exit 0

# Schema validation
WARNS=""
if ! head -20 "$FILE" | grep -q "^description:"; then
  WARNS="${WARNS}Missing description field. "
fi
if ! head -20 "$FILE" | grep -q "^topics:"; then
  WARNS="${WARNS}Missing topics field. "
fi
if ! head -1 "$FILE" | grep -q "^---$"; then
  WARNS="${WARNS}Missing YAML frontmatter. "
fi

if [ -n "$WARNS" ]; then
  FILENAME=$(basename "$FILE" .md)
  echo "{\"additionalContext\": \"Schema warnings for $FILENAME: $WARNS\"}"
fi

exit 0
