#!/bin/bash
# Layer 3: Memory Shell — Injeta contexto git ao iniciar sessão
# Executar como hook PreToolUse ou manualmente com: source .claude/hooks/memory.sh

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
  echo "Não é um repo git."
  exit 0
fi

echo "=== MEMORY.SH — Layer 3 Context Injection ==="
echo ""
echo "Branch: $(git branch --show-current)"
echo "Last 5 commits:"
git log --oneline -5
echo ""
echo "Modified files (unstaged):"
git diff --name-only | head -10
echo ""
echo "Staged files:"
git diff --cached --name-only | head -10
echo ""
echo "Untracked (top 10):"
git ls-files --others --exclude-standard | head -10
echo ""

# Check PRIMER.md
if [ -f "$REPO_ROOT/PRIMER.md" ]; then
  echo "=== PRIMER.md detected — Layer 2 active ==="
  head -5 "$REPO_ROOT/PRIMER.md"
fi

echo "=== END MEMORY.SH ==="
