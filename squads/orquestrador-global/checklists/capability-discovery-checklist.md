# Capability Discovery Checklist (PA-6.1)

> Run before invoking dag-architect (synthesis depends on accurate cache).

- [ ] capability-cache.json exists and parseable
- [ ] Cache age < TTL (default 3600s) OR --force re-scan executed
- [ ] All 11 categories scanned (agents, skills, squads, tasks, workflows, templates, MCPs, hooks, apps, services, packages)
- [ ] No category returned 0 (sanity check — if 0, scanner bug or filesystem issue)
- [ ] capability-manifest.yaml mtime hashes match current file mtimes (no drift)
- [ ] Selected capabilities (post-ranking) all have score > selection_threshold.escalate_or_create (data/scoring-weights.yaml)
- [ ] If gap detected (no capability fits) → capability-gap-report.md generated (template PA-0.2)
