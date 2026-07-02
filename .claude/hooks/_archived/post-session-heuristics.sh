#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# Claude Code Hook: Post-Session Heuristics Extraction
# ═══════════════════════════════════════════════════════════════════════════════
#
# HUMAN-GATED. Never auto-extracts. Always asks first.
#
# Flow:
#   1. Check eligibility (deterministic, $0)
#   2. If eligible: SUGGEST to human, show what was found
#   3. Human decides: extract or skip
#   4. If human approves: generate context for /extract-session-heuristics
#
# Usage:
#   bash .claude/hooks/post-session-heuristics.sh           # eligibility + suggestion
#   bash .claude/hooks/post-session-heuristics.sh --context  # generate context (after human approval)
#
# Anti-patterns prevented:
#   - Runner sessions (megabrain-map, knowledge-system, copy) filtered out by author detection
#   - Mechanical commits (outputs, score_cards) filtered out by path analysis
#   - No heuristics extracted without human confirmation
# ═══════════════════════════════════════════════════════════════════════════════

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:-suggest}"

# ── Thresholds ──
MIN_DURATION_MINUTES=20
MIN_HUMAN_DECISIONS=2
MIN_CODE_FILES=5

# ── Detect session type (multi-signal) ──
# Signal 1: Co-Authored-By = interactive (but /commit in other window = false positive)
# Signal 2: Commit message length (multi-line = real session, 1-line chore = mechanical)
# Signal 3: Time spread (30min+ between first/last = real session, <5min burst = batch commit)
# Signal 4: Handoff file generated in window = definitive proof of real session

ALL_COMMITS=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --oneline 2>/dev/null || true)
TOTAL_COMMITS=$(echo "$ALL_COMMITS" | grep -c '.' 2>/dev/null || echo 0)

if [[ "$TOTAL_COMMITS" -eq 0 ]]; then
  echo "⏭️  No commits in last 4 hours."
  exit 0
fi

# Signal 1: Co-Authored-By present
INTERACTIVE_COMMITS=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --grep="Co-Authored-By" --oneline 2>/dev/null | wc -l | tr -d ' ')

# Signal 2: Non-mechanical commits (exclude chore(outputs), score_card, baseline)
SUBSTANTIVE_COMMITS=$(echo "$ALL_COMMITS" | grep -ciE '^[a-f0-9]+ (feat|refactor|fix)' 2>/dev/null || echo 0)
MECHANICAL_COMMITS=$(echo "$ALL_COMMITS" | grep -ciE '(chore\(outputs\)|score.card|baseline|metrics\.jsonl)' 2>/dev/null || echo 0)

# Signal 3: Time spread
FIRST_TS=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --format="%at" 2>/dev/null | tail -1)
LAST_TS=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --format="%at" 2>/dev/null | head -1)
if [[ -n "$FIRST_TS" && -n "$LAST_TS" && "$FIRST_TS" != "$LAST_TS" ]]; then
  DURATION_MINUTES=$(( (LAST_TS - FIRST_TS) / 60 ))
else
  DURATION_MINUTES=0
fi

# Signal 4: Handoff file in window (strongest signal)
HANDOFF_IN_WINDOW=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --diff-filter=A --name-only --oneline 2>/dev/null | grep -c 'docs/sessions/.*handoff' || echo 0)

# Combined decision
# The ONLY reliable signal: duration ≥ 20min
# No /commit burst from another window lasts 20min. Period.
# Commits are unreliable: user sometimes doesn't commit at all during session.
IS_REAL_SESSION=false

if [[ "$DURATION_MINUTES" -ge "$MIN_DURATION_MINUTES" ]]; then
  IS_REAL_SESSION=true
fi

if [[ "$IS_REAL_SESSION" != true ]]; then
  echo "⏭️  Not a substantive interactive session."
  echo "   Co-Authored: ${INTERACTIVE_COMMITS} | Substantive: ${SUBSTANTIVE_COMMITS} | Mechanical: ${MECHANICAL_COMMITS} | Duration: ${DURATION_MINUTES}min | Handoff: ${HANDOFF_IN_WINDOW}"
  exit 0
fi

if [[ "$TOTAL_COMMITS" -eq 0 ]]; then
  echo "⏭️  No commits in last 4 hours. Nothing to extract."
  exit 0
fi

# ── Filter: exclude runner/mechanical commits ──
# Runner commits: contain known runner signatures
RUNNER_COMMITS=$(echo "$ALL_COMMITS" | grep -ciE '(chore\(outputs\)|score.card|megabrain-map|megabrain-validate|baseline|metrics\.jsonl)' 2>/dev/null || echo 0)

# Human decision commits: feat/refactor/fix that are NOT about outputs
HUMAN_DECISIONS=$(echo "$ALL_COMMITS" | grep -iE '^[a-f0-9]+ (feat|refactor|fix)' | grep -cvE '(outputs|score.card|baseline|metrics)' 2>/dev/null || echo 0)

# Code files changed (exclude outputs/, docs/sessions/, *.jsonl)
CODE_FILES=$(cd "$REPO_ROOT" && git diff --name-only HEAD~"${TOTAL_COMMITS}" 2>/dev/null | grep -cvE '^(outputs/|docs/sessions/|.*\.jsonl$|.*score_card\.yaml$)' 2>/dev/null || echo 0)

# Duration estimate
FIRST_TS=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --format="%at" 2>/dev/null | tail -1)
LAST_TS=$(cd "$REPO_ROOT" && git log --since="4 hours ago" --format="%at" 2>/dev/null | head -1)
if [[ -n "$FIRST_TS" && -n "$LAST_TS" && "$FIRST_TS" != "$LAST_TS" ]]; then
  DURATION_MINUTES=$(( (LAST_TS - FIRST_TS) / 60 ))
else
  DURATION_MINUTES=0
fi

# Runner ratio: if >70% are mechanical, this was a runner session
if [[ "$TOTAL_COMMITS" -gt 0 ]]; then
  RUNNER_RATIO=$((RUNNER_COMMITS * 100 / TOTAL_COMMITS))
else
  RUNNER_RATIO=0
fi

# ── Eligibility ──
ELIGIBLE=true
SKIP_REASONS=()

if [[ "$RUNNER_RATIO" -gt 70 ]]; then
  ELIGIBLE=false
  SKIP_REASONS+=("runner session (${RUNNER_RATIO}% mechanical commits)")
fi

if [[ "$DURATION_MINUTES" -lt "$MIN_DURATION_MINUTES" ]]; then
  ELIGIBLE=false
  SKIP_REASONS+=("duration ${DURATION_MINUTES}min < ${MIN_DURATION_MINUTES}min")
fi

if [[ "$HUMAN_DECISIONS" -lt "$MIN_HUMAN_DECISIONS" ]]; then
  ELIGIBLE=false
  SKIP_REASONS+=("human decisions ${HUMAN_DECISIONS} < ${MIN_HUMAN_DECISIONS}")
fi

if [[ "$CODE_FILES" -lt "$MIN_CODE_FILES" ]]; then
  ELIGIBLE=false
  SKIP_REASONS+=("code files ${CODE_FILES} < ${MIN_CODE_FILES}")
fi

# ── Mode: --context (generate context after human approval) ──
if [[ "$MODE" == "--context" ]]; then
  if [[ "$ELIGIBLE" != true ]]; then
    echo "⚠️  Session not eligible. Run without --context to see reasons."
    exit 1
  fi

  HUMAN_COMMIT_LIST=$(echo "$ALL_COMMITS" | grep -iE '^[a-f0-9]+ (feat|refactor|fix)' | grep -vE '(outputs|score.card|baseline|metrics)' | head -20)
  FILES_SUMMARY=$(cd "$REPO_ROOT" && git diff --stat HEAD~"${TOTAL_COMMITS}" 2>/dev/null | grep -vE '(outputs/|\.jsonl|score_card)' | tail -10)

  cat <<EOF
Session Context (auto-generated, runner commits filtered):

Duration: ~${DURATION_MINUTES} minutes
Total commits: ${TOTAL_COMMITS} (${RUNNER_COMMITS} mechanical, ${HUMAN_DECISIONS} human decisions)
Code files changed: ${CODE_FILES} (excluding outputs/)

Human decision commits:
${HUMAN_COMMIT_LIST}

Code files summary:
${FILES_SUMMARY}
EOF
  exit 0
fi

# ── Mode: suggest (default — NEVER auto-extract) ──
if [[ "$ELIGIBLE" == true ]]; then
  echo ""
  echo "🧠 Session may contain extractable heuristics"
  echo ""
  echo "   Duration:        ~${DURATION_MINUTES}min"
  echo "   Human decisions: ${HUMAN_DECISIONS} (of ${TOTAL_COMMITS} total commits)"
  echo "   Code files:      ${CODE_FILES}"
  echo "   Runner ratio:    ${RUNNER_RATIO}% mechanical"
  echo ""
  echo "   Human decision commits:"
  echo "$ALL_COMMITS" | grep -iE '^[a-f0-9]+ (feat|refactor|fix)' | grep -vE '(outputs|score.card|baseline|metrics)' | head -5 | sed 's/^/     /'
  echo ""
  echo "   ⚠️  REQUIRES YOUR APPROVAL to extract."
  echo "   To proceed:  /extract-session-heuristics"
  echo "   To generate context: bash .claude/hooks/post-session-heuristics.sh --context"
  echo ""
else
  echo "⏭️  Session not eligible for heuristic extraction"
  for reason in "${SKIP_REASONS[@]}"; do
    echo "   - $reason"
  done
fi

exit 0
