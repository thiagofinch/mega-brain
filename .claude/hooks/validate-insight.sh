#!/usr/bin/env bash
# validate-insight.sh — PostToolUse hook: validate insight schema on Write
# Fires when any .md file is written to .synapse/vault/insights/
# Checks: required fields present, scope valid, description non-empty

INPUT=$(cat)

# Extract file path from Claude Code PostToolUse event
FILE_PATH=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try {
      const e = JSON.parse(d);
      const p = e?.tool_input?.file_path ?? e?.tool_input?.new_file_path ?? '';
      console.log(p);
    } catch { process.exit(0); }
  });
" 2>/dev/null)

# Only check files in insights/ (not maps, not self/, not ops/)
if ! echo "$FILE_PATH" | grep -q '\.synapse/vault/insights/'; then
  exit 0
fi

# Skip map files
if echo "$FILE_PATH" | grep -q '\-map\.md$'; then
  exit 0
fi

# Check required fields
MISSING=""
for field in description scope confidence type status areas created; do
  if ! grep -q "^${field}:" "$FILE_PATH" 2>/dev/null; then
    MISSING="$MISSING $field"
  fi
done

# Check scope is valid
if grep -q "^scope:" "$FILE_PATH" 2>/dev/null; then
  scope=$(grep "^scope:" "$FILE_PATH" | head -1 | awk '{print $2}')
  if ! echo "hub default acme" | grep -qw "$scope"; then
    MISSING="$MISSING scope:invalid($scope)"
  fi
fi

# Check areas is not empty
if grep -q "^areas: \[\]" "$FILE_PATH" 2>/dev/null; then
  MISSING="$MISSING areas:empty"
fi

if [ -n "$MISSING" ]; then
  echo "[validate-insight] WARN: $(basename "$FILE_PATH") missing required fields:$MISSING" >&2
  echo "[validate-insight] Run: /arscontexta:validate to fix schema issues" >&2
fi

exit 0
