#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# Session Regression: Analyze ALL historical sessions for decision patterns
# ═══════════════════════════════════════════════════════════════════════════════
#
# Reads all handoff .md files, extracts decisions, finds repetitions,
# and cross-references with existing heuristics.
#
# Usage:
#   bash .claude/hooks/session-regression.sh                    # full report
#   bash .claude/hooks/session-regression.sh --decisions-only   # just decisions
#   bash .claude/hooks/session-regression.sh --gaps-only        # decisions not yet heuristics

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:-full}"
SESSIONS_DIR="$REPO_ROOT/docs/sessions"
HEURISTICS_DIR="$REPO_ROOT/squads/squad-creator-pro/minds/knowledge-architect/heuristics"
CARDS_FILE="$HEURISTICS_DIR/decision-cards.yaml"

# ═══════════════════════════════════════════════════════════════
# PHASE 1: Collect all handoff files
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════"
echo "SESSION REGRESSION — Historical Decision Analysis"
echo "$(date +%Y-%m-%d\ %H:%M:%S)"
echo "═══════════════════════════════════════════════════════════"
echo ""

HANDOFFS=()
while IFS= read -r f; do
  [[ -f "$f" ]] && HANDOFFS+=("$f")
done < <(find "$SESSIONS_DIR" -name "*.md" -not -name "README*" -not -name "baseline*" 2>/dev/null | sort)

echo "Handoffs found: ${#HANDOFFS[@]}"
echo ""

# Count interactive vs runner commits for context
TOTAL_REPO_COMMITS=$(cd "$REPO_ROOT" && git log --since="30 days ago" --oneline 2>/dev/null | wc -l | tr -d ' ')
INTERACTIVE_REPO_COMMITS=$(cd "$REPO_ROOT" && git log --since="30 days ago" --grep="Co-Authored-By" --oneline 2>/dev/null | wc -l | tr -d ' ')
RUNNER_REPO_COMMITS=$((TOTAL_REPO_COMMITS - INTERACTIVE_REPO_COMMITS))
echo "Last 30 days: ${TOTAL_REPO_COMMITS} commits (${INTERACTIVE_REPO_COMMITS} interactive, ${RUNNER_REPO_COMMITS} autonomous runner)"
echo ""

# ═══════════════════════════════════════════════════════════════
# PHASE 2: Extract decisions from each handoff
# ═══════════════════════════════════════════════════════════════

echo "-- PHASE 2: Decision Extraction --"
echo ""

TOTAL_DECISIONS=0
ALL_DECISIONS_FILE=$(mktemp)

for handoff in "${HANDOFFS[@]}"; do
  name=$(basename "$handoff" .md)
  date_part=$(echo "$name" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo "unknown")

  decisions=$(grep -niE '(decisao|decision|decided|escolhemos|optamos|migramos|criamos|extraimos|split|replaced|refactored|created|removed|added|chose|selected)' "$handoff" 2>/dev/null | head -15)
  decision_count=$(echo "$decisions" | grep -c '.' 2>/dev/null || echo 0)

  section_decisions=$(awk '/^## (DECISIONS|Decisions|Decision)/{found=1;next} /^## /{found=0} found && /\|/' "$handoff" 2>/dev/null | head -10)

  total=$((decision_count))
  TOTAL_DECISIONS=$((TOTAL_DECISIONS + total))

  if [[ "$total" -gt 0 ]]; then
    echo "  $date_part | $total decisions | $name"
    echo "$decisions" | while IFS= read -r line; do
      [[ -n "$line" ]] && echo "$date_part|$name|$line" >> "$ALL_DECISIONS_FILE"
    done
    if [[ -n "$section_decisions" ]]; then
      echo "$section_decisions" | while IFS= read -r line; do
        [[ -n "$line" ]] && echo "$date_part|$name|TABLE:$line" >> "$ALL_DECISIONS_FILE"
      done
    fi
  fi
done

echo ""
echo "  Total decisions extracted: $TOTAL_DECISIONS"
echo ""

if [[ "$MODE" == "--decisions-only" ]]; then
  echo "-- All Decisions --"
  cat "$ALL_DECISIONS_FILE"
  rm -f "$ALL_DECISIONS_FILE"
  exit 0
fi

# ═══════════════════════════════════════════════════════════════
# PHASE 3: Find recurring patterns
# ═══════════════════════════════════════════════════════════════

echo "-- PHASE 3: Recurring Patterns --"
echo ""

echo "  Top decision themes (by keyword frequency):"
echo ""

cat "$ALL_DECISIONS_FILE" | tr '[:upper:]' '[:lower:]' | \
  grep -oE '(shared|extract|consolidat|migrat|refactor|split|batch|fallback|guardrail|token|validator|runner|pipeline|module|pattern|template|format|schema|test|audit|hook|heuristic|security|json|yaml)' | \
  sort | uniq -c | sort -rn | head -15 | while read -r count word; do
    bar=$(printf '%*s' "$count" '' | tr ' ' '#')
    printf "    %-15s %3d %s\n" "$word" "$count" "$bar"
  done

echo ""

echo "  Decisions appearing in 2+ sessions (PATTERN CANDIDATES):"
echo ""

cat "$ALL_DECISIONS_FILE" | \
  sed 's/.*|//' | tr '[:upper:]' '[:lower:]' | \
  grep -oE '(created?|refactored?|migrated?|extracted?|replaced?|added|removed|split|consolidated?) [a-z_.-]+' | \
  sort | uniq -c | sort -rn | head -10 | while read -r count pattern; do
    if [[ "$count" -ge 2 ]]; then
      echo "    ${count}x: $pattern"
    fi
  done

echo ""

# ═══════════════════════════════════════════════════════════════
# PHASE 4: Cross-reference with existing heuristics
# ═══════════════════════════════════════════════════════════════

if [[ "$MODE" == "--gaps-only" || "$MODE" == "full" ]]; then
  echo "-- PHASE 4: Cross-Reference with Existing Heuristics --"
  echo ""

  if [[ -f "$CARDS_FILE" ]]; then
    HEURISTIC_COUNT=$(grep -c '^  - id:' "$CARDS_FILE" 2>/dev/null || echo 0)
    echo "  Existing heuristics: $HEURISTIC_COUNT"
    echo ""

    heuristic_keywords=$(grep 'rule:' "$CARDS_FILE" 2>/dev/null | tr '[:upper:]' '[:lower:]' | \
      grep -oE '(compare|batch|shared|fallback|audit|format|test|research|bug|module|consumer|fan-out|resume|repair|generator|tier)' | \
      sort -u)

    echo "  Decision themes NOT covered by existing heuristics:"
    echo ""

    all_themes=$(cat "$ALL_DECISIONS_FILE" | tr '[:upper:]' '[:lower:]' | \
      grep -oE '(shared|extract|consolidat|migrat|refactor|split|batch|fallback|guardrail|token|validator|runner|pipeline|module|pattern|template|format|schema|test|audit|hook|heuristic|security|json|yaml)' | \
      sort -u)

    gaps=0
    for theme in $all_themes; do
      if ! echo "$heuristic_keywords" | grep -qi "$theme" 2>/dev/null; then
        count=$(cat "$ALL_DECISIONS_FILE" | tr '[:upper:]' '[:lower:]' | grep -c "$theme" || echo 0)
        if [[ "$count" -ge 3 ]]; then
          echo "    '$theme' appears ${count}x in decisions but has no heuristic"
          gaps=$((gaps + 1))
        fi
      fi
    done

    if [[ "$gaps" -eq 0 ]]; then
      echo "    No significant gaps found"
    fi
  else
    echo "  decision-cards.yaml not found. Cannot cross-reference."
  fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# PHASE 5: Summary
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo "  Sessions analyzed:  ${#HANDOFFS[@]}"
echo "  Decisions found:    $TOTAL_DECISIONS"
echo "  Existing heuristics: $(grep -c '^  - id:' "$CARDS_FILE" 2>/dev/null || echo 0)"
echo ""
echo "  Next: Review patterns above and decide which merit formalization."
echo "═══════════════════════════════════════════════════════════"

rm -f "$ALL_DECISIONS_FILE"
