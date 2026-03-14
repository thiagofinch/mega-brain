# Story 1.1: Security -- Remove Exposed API Keys + Fix Insecure Deserialization

> **Story ID:** STORY-TD-1.1
> **Epic:** EPIC-TD-001
> **Sprint:** 1
> **Priority:** P0 CRITICAL
> **Debitos:** TD-032 (API key in auto-memory), TD-033 (pickle.load without validation)

---

## Context

A Fireflies API key (`fe9bae31-e325-4892-b0ce-4a6f31584f87`) sits in plaintext inside the Claude auto-memory file at `~/.claude/projects/.../memory/MEMORY.md`. This file persists across all Claude Code sessions and could leak via backup, cloud sync, or project sharing. Separately, `core/intelligence/speakers/voice_embedder.py` uses `pickle.load()` to deserialize speaker voice embeddings -- a known remote code execution vector (CWE-502) if the data source is ever external.

These are the two security debits with the highest urgency. Neither has dependencies, making them safe first fixes.

---

## Tasks

### TD-032: Remove Exposed Secrets

- [ ] Open `~/.claude/projects/-Users-thiagofinch-Documents-Projects-mega-brain/memory/MEMORY.md`
- [ ] Remove the plaintext Fireflies API key value (`fe9bae31-e325-4892-b0ce-4a6f31584f87`)
- [ ] Remove the plaintext N8N webhook URL (`https://thiagofinch.app.n8n.cloud/webhook/35f17dcc-...`)
- [ ] Replace both with reference-only entries: "Fireflies API key stored in `.env` as `FIREFLIES_API_KEY`" and "N8N webhook URL stored in `.env` as `N8N_WEBHOOK_URL`"
- [ ] Rotate the Fireflies API key via the Fireflies dashboard (Settings -> API -> Generate New Key)
- [ ] Update the new key in `.env` as `FIREFLIES_API_KEY`
- [ ] Update `core/intelligence/pipeline/fireflies_config.py` to read from `.env` if it currently references the old key
- [ ] Add a rule to `.claude/rules/` prohibiting plaintext secrets in memory files (3 lines: "NEVER store API keys, tokens, or webhook URLs as plaintext values in MEMORY.md or auto-memory files. Use reference-only entries pointing to `.env`.")

### TD-033: Replace pickle with Safe Deserialization

- [ ] Open `core/intelligence/speakers/voice_embedder.py` line 63
- [ ] Replace `pickle.load()` with `json.load()` or `numpy.load(allow_pickle=False)`
- [ ] Update the corresponding save function to use the same format (JSON or numpy `.npy`)
- [ ] If existing `.pkl` files exist in `.data/voice_embeddings/`, add a one-time migration function that converts `.pkl` to the new format
- [ ] Add a comment at the save/load site: "# Security: pickle deserialization is a known RCE vector (CWE-502). Use JSON or numpy instead."
- [ ] Search for any other `pickle.load` or `pickle.loads` usage: `grep -r "pickle.load" core/`

---

## Acceptance Criteria

- [ ] `grep -i "fe9bae31\|35f17dcc" ~/.claude/projects/*/memory/MEMORY.md` returns 0 matches
- [ ] `grep -r "pickle.load" core/` returns 0 results
- [ ] Fireflies API key has been rotated (old key no longer valid)
- [ ] `.env` contains the new `FIREFLIES_API_KEY` value
- [ ] `core/intelligence/pipeline/fireflies_sync.py` still connects to Fireflies API successfully with new key
- [ ] Voice embedder save/load cycle works: save embeddings, load them back, verify data integrity

---

## Technical Notes

**TD-032 -- Key Rotation:**
The exposed key is `fe9bae31-e325-4892-b0ce-4a6f31584f87`. Even though the auto-memory file is outside the git repo, it has been in the memory for multiple sessions and could exist in backups. Rotation is non-optional.

Fireflies key rotation: Dashboard -> Settings -> Integrations -> API -> Regenerate. Update `.env` immediately.

**TD-033 -- Pickle Replacement:**
The voice_embedder stores speaker voice embeddings as numpy arrays. The recommended replacement is `numpy.save()` / `numpy.load(allow_pickle=False)` for the embedding vectors, which preserves the ndarray format without the security risk. If metadata is stored alongside embeddings, use a JSON sidecar file.

If no `.pkl` files exist in `.data/voice_embeddings/` (the directory may be empty or absent), skip the migration step.

---

## Effort Estimate

| Task | Hours |
|------|-------|
| Remove secrets from memory + add rule | 0.5h |
| Rotate Fireflies key + update .env | 0.5h |
| Replace pickle with JSON/numpy | 1.5h |
| Migration of existing .pkl files (if any) | 0.5h |
| **Total** | **3h** |

---

## Dependencies

None. This story has zero dependencies and should be executed first in Sprint 1.

---

## Definition of Done

- [ ] No plaintext secrets exist in any memory file outside `.env`
- [ ] Old Fireflies API key is invalidated (rotated)
- [ ] New key works (Fireflies sync test passes)
- [ ] Zero instances of `pickle.load` in the codebase
- [ ] Voice embedder load/save cycle produces correct results with new format
- [ ] Rule prohibiting secrets in memory files is committed
