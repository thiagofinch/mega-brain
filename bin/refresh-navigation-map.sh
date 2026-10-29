#!/usr/bin/env bash
# refresh-navigation-map.sh — Debounced rebuild of NAVIGATION-MAP.json (Story MCE-3.6).
#
# Triggered manually or via post_write hook in `.claude/settings.json` when a
# dossier under `knowledge/**/dossiers/**/*.md` is modified. Enforces a 60s
# debounce window using a sentinel file in `.data/`.
#
# Usage:
#   bin/refresh-navigation-map.sh             # debounced
#   bin/refresh-navigation-map.sh --force     # bypass debounce
#   MCE_NAV_MAP_DISABLED=1 bin/refresh-navigation-map.sh  # opt-out
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEBOUNCE_FILE="${ROOT}/.data/.navigation-map.last-build"
DEBOUNCE_SECONDS=60

if [ "${MCE_NAV_MAP_DISABLED:-0}" = "1" ]; then
  echo "[refresh-navigation-map] disabled via MCE_NAV_MAP_DISABLED"
  exit 0
fi

FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
  esac
done

mkdir -p "$(dirname "$DEBOUNCE_FILE")"

if [ "$FORCE" -eq 0 ] && [ -f "$DEBOUNCE_FILE" ]; then
  now=$(date +%s)
  last=$(cat "$DEBOUNCE_FILE" 2>/dev/null || echo 0)
  if [ -n "$last" ] && [ "$((now - last))" -lt "$DEBOUNCE_SECONDS" ]; then
    remaining=$((DEBOUNCE_SECONDS - (now - last)))
    echo "[refresh-navigation-map] debounced (${remaining}s left). Use --force to override."
    exit 0
  fi
fi

# O gerador do NAVIGATION-MAP nao faz parte desta distribuicao: nada a reconstruir.
echo "[refresh-navigation-map] o gerador do NAVIGATION-MAP nao existe nesta distribuicao; nada a reconstruir."
