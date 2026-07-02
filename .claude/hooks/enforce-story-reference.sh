#!/bin/bash
# enforce-story-reference.sh — Constitutional Article III Enforcement
# PreToolUse hook: warns when git commit messages lack a story reference
#
# Story references accepted:
#   [Story X.Y]  or  [STORY-X.Y]  or  STORY-X.Y  or  Story X.Y
#   feat: description [Story 111.1]
#   fix(scope): description [STORY-70.6]
#
# Mode: WARN (logs warning but allows commit)
# To switch to BLOCK: change "allow" to "deny" in the output
#
# Story: STORY-111.4 (Epic 111 — Governance Enforcement Closure)
# Constitution: Article III — Story-Driven Development

INPUT=$(cat)

# Extract command from JSON
COMMAND=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try{console.log(JSON.parse(d).tool_input.command||'')}
    catch(e){process.exit(1)}
  });
" 2>/dev/null)

# Only check git commit commands
if ! echo "$COMMAND" | grep -qiE '\bgit\s+commit\b'; then
  exit 0
fi

# Skip merge commits, amend, and initial commits
if echo "$COMMAND" | grep -qiE '\-\-amend|\bmerge\b|initial commit'; then
  exit 0
fi

# Extract the commit message (between quotes after -m)
MSG=$(echo "$COMMAND" | grep -oP '(?<=-m\s["\x27]).*?(?=["\x27])' 2>/dev/null || echo "$COMMAND")

# Check for story reference patterns
if echo "$MSG" | grep -qiE '\[?Story[ -]?[0-9]+\.[0-9]+\]?|STORY-[A-Z]*[0-9]+'; then
  # Story reference found — allow
  exit 0
fi

# Check for conventional commit with Co-Authored-By (automated commits)
if echo "$COMMAND" | grep -qiE 'Co-Authored-By'; then
  exit 0
fi

# No story reference — WARN (not block)
echo "⚠️  [Art. III] Commit without story reference. Consider adding [Story X.Y] to the message." >&2
# Allow the commit (WARN mode) — change to deny to enforce
exit 0
