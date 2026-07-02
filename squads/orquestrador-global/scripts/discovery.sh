#!/bin/bash
# Discovery: gather context for orquestrador-global squad
# Usage: bash scripts/discovery.sh

set -euo pipefail

SQUAD_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔍 orquestrador-global Squad Discovery"
echo "========================="
echo ""

echo "## Domain: Orquestração global"
echo "## Primary deliverable: plano de execução"
echo "## Standard inputs: objetivo, squads, timeline"
echo ""

echo "### Knowledge Base"
if [ -d "$SQUAD_DIR/knowledge" ]; then
  find "$SQUAD_DIR/knowledge" -name '*.md' | sort | while read f; do
    NAME=$(basename "$f")
    LINES=$(wc -l < "$f" | tr -d ' ')
    echo "  📄 $NAME ($LINES lines)"
  done
else
  echo "  (empty)"
fi

echo ""
echo "### Agent Roster"
if [ -d "$SQUAD_DIR/agents" ]; then
  find "$SQUAD_DIR/agents" -name '*.md' | sort | while read f; do
    NAME=$(basename "$f" .md)
    ROLE=$(grep -m1 "role:" "$f" 2>/dev/null | sed 's/.*role:s*//' || echo "unknown")
    echo "  🤖 $NAME — $ROLE"
  done
else
  echo "  (empty)"
fi

echo ""
echo "### Active Tasks"
if [ -d "$SQUAD_DIR/tasks" ]; then
  TASK_COUNT=$(find "$SQUAD_DIR/tasks" -name '*.md' -o -name '*.yaml' | wc -l | tr -d ' ')
  echo "  Total: $TASK_COUNT tasks"
fi

echo ""
echo "### Data Files"
if [ -d "$SQUAD_DIR/data" ]; then
  find "$SQUAD_DIR/data" -type f | sort | while read f; do
    echo "  📊 $(basename "$f")"
  done
else
  echo "  (empty)"
fi
