#!/usr/bin/env bash
# Cross-platform Python runner for Claude Code hooks.
# Tries multiple Python commands. Exits silently if none found.
# On Windows, python3 can be a Microsoft Store redirect (not real Python),
# so we test with --version before using it.

SCRIPT="$1"
shift

# Try python3 (Mac/Linux native, some Windows)
if command -v python3 &>/dev/null; then
  if python3 --version &>/dev/null; then
    exec python3 "$SCRIPT" "$@"
  fi
fi

# Try python (Windows default, some Linux)
if command -v python &>/dev/null; then
  if python --version 2>&1 | grep -qi "python 3"; then
    exec python "$SCRIPT" "$@"
  fi
fi

# Try py -3 (Windows Python Launcher)
if command -v py &>/dev/null; then
  if py -3 --version &>/dev/null; then
    exec py -3 "$SCRIPT" "$@"
  fi
fi

# No Python found — exit silently (hooks are optional)
exit 0
