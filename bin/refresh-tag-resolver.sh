#!/usr/bin/env bash
# refresh-tag-resolver.sh — Wrapper for Story MCE-3.7
#
# Generates .data/tag-resolver.json by scanning knowledge/**/inbox for tagged files.
# Run on demand when inbox content changes significantly.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# O gerador do tag-resolver nao faz parte desta distribuicao: nada a gerar.
echo "[refresh-tag-resolver] o gerador do tag-resolver nao existe nesta distribuicao; nada a gerar."
