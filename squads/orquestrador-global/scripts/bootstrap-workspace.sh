#!/bin/bash
# Bootstrap workspace for orquestrador-global squad
# Usage: bash scripts/bootstrap-workspace.sh [project-dir]

set -euo pipefail

SQUAD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="${1:-.}"

echo "🚀 Bootstrapping orquestrador-global workspace..."
echo "   Squad dir: $SQUAD_DIR"
echo "   Project dir: $PROJECT_DIR"

# Verify essential files exist
ESSENTIALS=(
  "config.yaml"
  "context.yaml"
  "README.md"
)

for file in "${ESSENTIALS[@]}"; do
  if [ ! -f "$SQUAD_DIR/$file" ]; then
    echo "⚠️  Missing: $file"
  else
    echo "✅ Found: $file"
  fi
done

# Count components
echo ""
echo "📊 Squad Components:"
echo "   Agents:     $(find "$SQUAD_DIR/agents" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
echo "   Tasks:      $(find "$SQUAD_DIR/tasks" -name '*.md' -o -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"
echo "   Knowledge:  $(find "$SQUAD_DIR/knowledge" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
echo "   Checklists: $(find "$SQUAD_DIR/checklists" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
echo "   Templates:  $(find "$SQUAD_DIR/templates" -type f 2>/dev/null | wc -l | tr -d ' ')"

echo ""
echo "✅ orquestrador-global workspace ready!"
