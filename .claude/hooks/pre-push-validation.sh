#!/bin/bash
# Pre-push validation — WI-T-020-S
# Runs critical validators before allowing push
# Policy: warn-open (does NOT block push)

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "Running pre-push validations..."
echo ""

node "$REPO_ROOT/scripts/validate-people-registry-paths.js" || {
  echo ""
  echo "WARNING: People registry path violations found. Review before pushing."
}

echo ""

node "$REPO_ROOT/scripts/validate-template-registry.js" || {
  echo ""
  echo "WARNING: Template coverage issues found. Review before pushing."
}

echo ""
echo "Pre-push validation complete."
exit 0  # Always allow push (warn-open policy)
