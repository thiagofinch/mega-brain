#!/bin/bash
# MegaBrain Hub — Session Orientation Hook
# Injects workspace signals, active goals, previous session state, and maintenance conditions at session start.
# Surgical port of Ars Contexta session-orient.sh — adapted to Hub conventions (ADR-GP002).

# Circuit breaker — hook must NEVER block a session under any failure mode
trap 'exit 0' ERR

# No set -e — silent failures required
set +e

# Guard: only run if vault exists
[ -d ".synapse/vault" ] || exit 0

# ── Session tracking (silent — no stdout) ──────────────────────
# SessionStart provides session info as JSON on stdin.
# Read it before any echo statements.

INPUT=$(cat)
SESSION_ID=""
if command -v jq &>/dev/null; then
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
else
  SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/"session_id":"//;s/"//')
fi

# Vault bootstrap
mkdir -p .synapse/vault/sessions/ || exit 0

TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S" 2>/dev/null || exit 0)

# Snapshot previous session before promotion (needed for AC7 injection below)
PREV_SESSION_SNAPSHOT=""

if [ -n "$SESSION_ID" ]; then
  # Promote previous session if it's a different ID
  if [ -f .synapse/vault/sessions/current.json ]; then
    PREV_SESSION_SNAPSHOT=$(cat .synapse/vault/sessions/current.json 2>/dev/null)

    if command -v jq &>/dev/null; then
      PREV_ID=$(jq -r '.id // empty' .synapse/vault/sessions/current.json 2>/dev/null)
      PREV_STARTED=$(jq -r '.started // empty' .synapse/vault/sessions/current.json 2>/dev/null)
    else
      PREV_ID=$(grep -o '"id":"[^"]*"' .synapse/vault/sessions/current.json | head -1 | sed 's/"id":"//;s/"//')
      PREV_STARTED=$(grep -o '"started":"[^"]*"' .synapse/vault/sessions/current.json | head -1 | sed 's/"started":"//;s/"//')
    fi

    if [ -n "$PREV_ID" ] && [ "$PREV_ID" != "$SESSION_ID" ]; then
      # Different session — promote previous to timestamped archive
      ARCHIVE_TS="${PREV_STARTED:-$TIMESTAMP}"
      mv .synapse/vault/sessions/current.json ".synapse/vault/sessions/${ARCHIVE_TS}.json" 2>/dev/null || true
    fi
  fi

  # Write current session
  cat > .synapse/vault/sessions/current.json 2>/dev/null << EOF
{
  "id": "$SESSION_ID",
  "started": "$TIMESTAMP",
  "status": "active"
}
EOF
fi

# ── Context injection (stdout → conversation) ──────────────────

echo "## Session Context"
echo ""

# Workspace signals: git branch + recent commits
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null || true)
  echo "**Branch:** ${BRANCH:-unknown}"
  echo ""
  echo "**Recent commits:**"
  git log --oneline -5 2>/dev/null || true
  echo ""
fi

# Doctor status hint
if [ -f ".synapse/metrics/hook-metrics.json" ]; then
  echo "**Metrics:** \`.synapse/metrics/hook-metrics.json\` exists — run \`npm run doctor\` to check repo health."
  echo ""
fi

# Active session count hint
SESSION_ARCH_COUNT=$(ls -1 .synapse/vault/sessions/*.json 2>/dev/null | grep -cv "current.json" 2>/dev/null || echo 0)
if [ "$SESSION_ARCH_COUNT" -gt 0 ] 2>/dev/null; then
  echo "**Sessions archived:** $SESSION_ARCH_COUNT"
  echo ""
fi

echo "---"
echo ""

# Previous session state (continuity) — from pre-promotion snapshot
if [ -n "$PREV_SESSION_SNAPSHOT" ]; then
  echo "**Previous session:**"
  echo "$PREV_SESSION_SNAPSHOT"
  echo ""
fi

# Active goals injection
if [ -f ".synapse/vault/goals.md" ]; then
  cat .synapse/vault/goals.md
  echo ""
fi

# Maintenance condition: archived sessions >= 10
SESS_COUNT=$(ls -1 .synapse/vault/sessions/*.json 2>/dev/null | grep -cv "current.json" 2>/dev/null || echo 0)
if [ "$SESS_COUNT" -ge 10 ] 2>/dev/null; then
  echo "CONDITION: $SESS_COUNT unprocessed sessions. Consider /remember --mine-sessions."
fi
