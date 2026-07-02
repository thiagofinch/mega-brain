#!/bin/bash
# post-edit-lint.sh — PostToolUse hook for Edit/Write
# Zero context tokens: runs as shell, only outputs warnings
# Catches: grep -P, bash 4+ features, YAML syntax errors
# Compatible: macOS, Linux, WSL, Git Bash

INPUT=$(cat)

# Extract edited file path from hook JSON
FILE=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try{
      const p=JSON.parse(d);
      console.log(p.tool_input.file_path||p.tool_input.filePath||'');
    }catch(e){process.exit(1)}
  });
" 2>/dev/null)

# If parsing failed or no file, silently exit
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

WARNINGS=""

# --- Shell script checks ---
if echo "$FILE" | grep -qE '\.sh$'; then

  # grep -P (not available on macOS)
  if grep -nE 'grep\s+(-[a-zA-Z]*P|-P)' "$FILE" 2>/dev/null; then
    WARNINGS="${WARNINGS}[LINT] grep -P detected — use grep -E instead (macOS compat)\n"
  fi

  # bash 4+ associative arrays with set -u
  if grep -qE 'declare\s+-A' "$FILE" 2>/dev/null && grep -qE 'set\s+-[a-zA-Z]*u' "$FILE" 2>/dev/null; then
    WARNINGS="${WARNINGS}[LINT] declare -A + set -u detected — associative arrays cause unbound var errors on bash 3 (macOS)\n"
  fi

  # Problematic brace expansion in defaults: ${var:-{}}
  if grep -nE '\$\{[^}]+:-\{' "$FILE" 2>/dev/null; then
    WARNINGS="${WARNINGS}[LINT] Brace expansion in parameter default detected — can cause unexpected behavior\n"
  fi

  # grep -P in variables/aliases
  if grep -nE "alias.*grep.*-P|GREP.*-P" "$FILE" 2>/dev/null; then
    WARNINGS="${WARNINGS}[LINT] grep -P in alias/variable — use grep -E for portability\n"
  fi

fi

# --- YAML syntax check ---
if echo "$FILE" | grep -qE '\.ya?ml$'; then
  # Use node + js-yaml (already a project dependency) for parity with CI
  YAML_ERR=$(node -e "
    try {
      const yaml = require('js-yaml');
      const fs = require('fs');
      yaml.load(fs.readFileSync('$FILE','utf8'));
    } catch(e) {
      console.log('[YAML] ' + e.message.split('\n')[0]);
      process.exit(1);
    }
  " 2>/dev/null)

  if [ $? -ne 0 ] && [ -n "$YAML_ERR" ]; then
    WARNINGS="${WARNINGS}${YAML_ERR}\n"
  fi
fi

# --- Output warnings if any ---
if [ -n "$WARNINGS" ]; then
  # PostToolUse hooks output to stderr as user-visible warnings
  printf "$WARNINGS" >&2
fi

exit 0
