#!/bin/bash
# Validate orquestrador-global squad essentials
# Usage: bash scripts/validate-essentials.sh

set -euo pipefail

SQUAD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SQUAD_NAME="orquestrador-global"
ERRORS=0

echo "🔍 Validating $SQUAD_NAME essentials..."
echo ""

# Structure checks
check_exists() {
  if [ -e "$SQUAD_DIR/$1" ]; then
    echo "✅ $1"
  else
    echo "❌ $1 — MISSING"
    ERRORS=$((ERRORS + 1))
  fi
}

echo "=== Structure ==="
check_exists "config.yaml"
check_exists "context.yaml"
check_exists "README.md"
check_exists "agents"
check_exists "tasks"
check_exists "knowledge"

echo ""
echo "=== Quality ==="

# Check config.yaml has score
if grep -q "score:" "$SQUAD_DIR/config.yaml" 2>/dev/null; then
  SCORE=$(grep "score:" "$SQUAD_DIR/config.yaml" | head -1 | awk '{print $2}')
  echo "✅ Score: $SCORE"
else
  echo "❌ Score missing in config.yaml"
  ERRORS=$((ERRORS + 1))
fi

# Check agents have ACTIVATION-NOTICE
AGENTS_TOTAL=$(find "$SQUAD_DIR/agents" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
AGENTS_V4=$(grep -rl "ACTIVATION-NOTICE" "$SQUAD_DIR/agents" 2>/dev/null | wc -l | tr -d ' ')
echo "📊 Agents v4.0+: $AGENTS_V4 / $AGENTS_TOTAL"

# Check tasks have frontmatter
TASKS_TOTAL=$(find "$SQUAD_DIR/tasks" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
TASKS_FM=$(grep -rl "^---" "$SQUAD_DIR/tasks" 2>/dev/null | wc -l | tr -d ' ')
echo "📊 Tasks with frontmatter: $TASKS_FM / $TASKS_TOTAL"

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ All checks passed!"
else
  echo "❌ $ERRORS checks failed"
fi

exit $ERRORS
