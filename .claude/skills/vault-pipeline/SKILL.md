---
name: vault-pipeline
description: "5-phase knowledge vault processing pipeline: seed → extract → reflect → reweave → verify. Uses Ralph Orchestrator for resumable queue-based execution."
version: "1.0.0"
owner_squad: mega-brain
megabrain_tier: Tier2
context: inline
agent: general-purpose
user-invocable: true
argument-hint: "[source-path] [type: claim|enrichment|source]"
---

# Vault Pipeline — 5-Phase Knowledge Processing

Processes a knowledge source through 5 sequential phases, each in isolated context via Ralph Orchestrator. Fully resumable — interrupted sessions pick up from queue state.

## Phases

### Phase 1: Seed
- Detect source type (file, URL, session transcript)
- Create queue entry in .synapse/queue/queue.yaml via ralph.enqueue()
- Move source to .synapse/queue/archive/{batch}/

### Phase 2: Extract
- Read source from archive
- Extract atomic notes (one claim per note)
- Each note follows insight-note.md template: description, scope, confidence, type, areas, relevant_insights
- Write to .synapse/vault/insights/ with prose titles (claim as title)

### Phase 3: Reflect (Dual-Discovery)
- For each new note, run dual-discovery (see .synapse/methodology/dual-discovery.md):
  1. MOC navigation: read domain maps → find related notes
  2. Semantic search: grep for keywords in .synapse/vault/insights/
- Apply articulation test to each candidate connection
- Add bidirectional links for passing connections

### Phase 4: Reweave
- Backward pass: for EXISTING notes, ask "if written today with everything we now know, what changes?"
- Actions: sharpen claim (vague → specific), split note (1 → N), challenge claim (new evidence contradicts)
- Record reweave trace

### Phase 5: Verify
- Articulation test on all new connections
- Link health check (no dangling [[links]])
- MOC coherence (all new notes appear in at least 1 domain map)
- Discovery trace completeness (was dual-discovery executed?)

## Usage

```
/vault-pipeline docs/sessions/2026-04/session-notes.md source
/vault-pipeline "my observation about capability routing" claim
```

## Queue Integration

Uses .synapse/orchestration/ralph.js for phase tracking.
After each phase, MUST output:

```
=== RALPH HANDOFF ===
Phase: {phase_name}
Work Done: {summary of what was created/modified}
Files Modified: [list]
Queue Update: advance to next phase
Learnings: {any insights about the process itself}
===================
```

## Dependencies

- .synapse/orchestration/ralph.js (queue management)
- .synapse/vault/templates/insight-note.md (note template)
- .synapse/methodology/dual-discovery.md (dual-discovery methodology)
- .claude/skills/arscontexta-extract/SKILL.md (extraction methodology)
