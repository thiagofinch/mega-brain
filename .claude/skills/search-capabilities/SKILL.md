---
name: search-capabilities
description: "Natural-language search across the Tool Intelligence Layer capability registry. Returns the top-5 capabilities that match a free-form query (e.g. 'I need to create a video'). Backed by semantic embeddings with keyword fallback."
version: "1.0.0"
owner_squad: infra-ops
megabrain_tier: Tier1
context: fork
agent: general-purpose
user-invocable: true
argument-hint: "[query string]"
status: active
---

# search-capabilities

Semantic + keyword tool discovery over `agents/_registry/capability-registry.yaml`.

## When to use

- The user asks for a tool or capability in natural language ("how do I send a Slack message", "I need to update a Google Sheet", "create a video with TTS").
- The capability-hint injector emitted the meta-hint `Tool discovery: search_capabilities('your need')` and you need to act on it.
- You are searching for a capability whose name you don't remember but whose intent you know.

## When NOT to use

- You already know the exact `capability_id`. Read the registry directly.
- You need full provider chain resolution including env-var checks — use `enforcement_check` / `sync_capability_status.py` instead.
- You need to *register* a new capability — use `@devops` + the tool-onboarder skill, not this one.

## Invocation

```bash
python3 .claude/hooks/search_capabilities.py "your natural language query"
```

Add `--json` for machine-readable output, `--top-k N` to widen the result set (default 5).

## What it returns

A structured block:

```
Found N relevant capabilities:

[1] {capability_id} ({cosine score})
    Title: ...
    Description: ...
    Business context: ...
    Provider chain: ...

[2] ...
```

## How it picks results

1. **Semantic search** via `.data/capability-embeddings.npy` (OpenAI text-embedding-3-large, 1536d).
2. **Keyword fallback** when the embedding cache or `OPENAI_API_KEY` is missing — substring scan against `capability-keyword-index.json`.
3. Both paths fail-open: returns an empty result set rather than raising.

## Budget

| Path | Budget |
|------|--------|
| Warm (embedding cache hit) | < 200 ms |
| Cold (cache miss, API call) | < 2 s |
| Keyword fallback | < 50 ms |

## References

- Implementation: `.claude/hooks/search_capabilities.py`
- Embedding builder: `.claude/hooks/build_capability_embeddings.py`
- Capability registry: `agents/_registry/capability-registry.yaml`
- Story: `docs/stories/epic-til-foundation/STORY-TIL-19-tool-search-tool-defer-loading.md`
- ADR: `docs/adr/ADR-TIL-001` (Python hooks boundary)
