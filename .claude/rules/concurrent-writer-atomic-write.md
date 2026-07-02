---
paths:
  - "apps/**"
  - "packages/**"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/*.css"
  - "**/*.scss"
---

# Concurrent-Writer Atomic Write

> Stub for auto-load. Full content: `minds/knowledge_architect/heuristics/AN_KE_163.md`

## Principle

If you are about to make **≥2 Edits in the same file** AND that file is under a linter, prettier, hot-reload, or any process that may rewrite it between your operations, **STOP using sequential Edits — use a single Write with the final desired content**.

## Why

Linter/auto-format/hot-reload may rewrite the file between your Edit operations. Symptom: `git diff` shows a state different from what you just wrote, or 30+ manual edits silently revert. Sequential Edits assume nobody else writes the file.

## Detection

```
About to Edit file X for the 2nd, 3rd, ... time?
└── Is X under a watcher (linter, prettier, hot-reload, hook)?
    └── YES → switch to Write atomic. Build full content, then write once.
```

## Anti-Pattern

```
Edit(file, "foo", "bar")     # success
Edit(file, "baz", "qux")     # success — but linter ran between, file was reformatted
Edit(file, ...)              # FAIL: old_string not found (because linter rewrote it)
```

## Source

AN_KE_163 — active heuristic.
