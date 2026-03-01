# Activate Clone

```yaml
---
task: TSK-050
execution_type: Agent
responsible: "@jarvis"
---
```

---

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Activate Mind Clone |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | Clone identifier (name or ID), interaction mode |
| output | Activated clone session, confirmation message |
| action_items | 8 steps |
| acceptance_criteria | Clone loaded, identity checkpoint passed, response generated |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| clone_id | string | yes | Name or ID of the clone to activate (e.g., "alex-hormozi", "AH") |
| mode | enum | no | Interaction mode: "single" (default), "dual", "roundtable" |
| clone_ids | string[] | conditional | Required for dual/roundtable: list of clone identifiers |
| topic | string | conditional | Required for dual/roundtable: discussion topic |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| activation_status | message | chat | Confirmation with clone identity card |
| session_state | state | in-memory | Active clone context for response generation |
| session_log | file | logs/clone-sessions/ | Session transcript (saved on deactivation) |

---

## Execution

### Phase 1: Discovery

**Quality Gate:** QG-CLONE-DISCOVERY

1. Parse the activation command to extract clone_id and mode
2. Search for clone directory in this order:
   - `agents/minds/{clone_id}/`
   - `agents/persons/{clone_id}/`
   - `agents/cargo/*/{clone_id}/`
3. If clone_id is ambiguous (e.g., "alex"), list candidates and ask for clarification
4. Verify that all three required files exist in the clone directory:
   - SOUL.md (REQUIRED)
   - MEMORY.md (REQUIRED)
   - DNA-CONFIG.yaml (REQUIRED)
5. If any required file is missing, abort with clear error message

**Failure condition:** Clone directory not found or required files missing.

### Phase 2: Loading

**Quality Gate:** QG-CLONE-LOADING

1. Read SOUL.md completely -- extract identity, beliefs, voice, reasoning patterns, decision rules
2. Read MEMORY.md completely -- extract experience patterns, expressions, insights, analogies
3. Read DNA-CONFIG.yaml completely -- extract 5-layer DNA structure, source weights, domain coverage
4. Read AGENT.md if it exists -- extract expertise domains and frameworks
5. For dual/roundtable: repeat steps 1-4 for each additional clone

**Failure condition:** File read error or corrupted/empty files.

### Phase 3: Embodiment

**Quality Gate:** QG-IDENTITY-CHECKPOINT

1. Calibrate voice: adopt clone's vocabulary, tone, phrases, analogies
2. Calibrate reasoning: load clone's mental models, frameworks, heuristics as primary reasoning tools
3. Calibrate values: align with clone's stated philosophies and decision rules
4. Run Identity Checkpoint (4 checks):
   - VOICE: Am I using their characteristic phrases and tone?
   - REASONING: Am I using their mental models and frameworks?
   - VALUES: Does my response align with their stated beliefs?
   - BOUNDARIES: Am I staying within their documented knowledge?
5. If checkpoint fails (3+ failures): re-read SOUL.md and restart Phase 3

**Failure condition:** Identity checkpoint fails after 2 attempts.

### Phase 4: Activation Confirmation

**Quality Gate:** QG-ACTIVATION-COMPLETE

1. Display activation confirmation with clone identity card
2. Include: name, archetype, expertise domains, DNA layer counts, source count, defining phrase
3. Indicate interaction mode and deactivation command
4. Begin responding as the clone

**Failure condition:** None (informational phase).

---

## Acceptance Criteria

- [ ] Clone directory located successfully
- [ ] All 3 required files (SOUL.md, MEMORY.md, DNA-CONFIG.yaml) loaded completely
- [ ] Identity checkpoint passed (4/4 checks)
- [ ] Activation confirmation displayed with correct clone metadata
- [ ] First response generated in clone's authentic voice
- [ ] DNA cascade reasoning applied (per REASONING-MODEL-PROTOCOL)
- [ ] Epistemic honesty maintained (clone admits when topic is outside their scope)

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| roundtable-session (TSK-051) | mode == "roundtable" | Loaded clone contexts, topic |
| (self - response loop) | mode == "single" | Active clone context |
| (self - dual protocol) | mode == "dual" | Two loaded clone contexts, topic |
| deactivate | User says /deactivate | Session log for optional MEMORY.md update |

---

## Scripts de Suporte (opcional)

| Script | Location | Invoked When |
|--------|----------|--------------|
| clone_resolver.py | core/intelligence/ | Fuzzy matching clone names (planned) |

---

## Notes

- The emulator has no personality of its own. It is a vessel for the loaded clone.
- In dual and roundtable modes, the emulator acts as a silent moderator, ensuring each clone gets equal voice and the protocol structure is followed.
- Clone sessions should be saved to `logs/clone-sessions/` on deactivation for future reference.
- If new insights emerge during a session that are not in the clone's MEMORY.md, offer to update it on deactivation.
- Maximum 4 clones in a roundtable to manage cognitive load and output quality.
- The Identity Checkpoint runs silently before every response in single mode, not just at activation.

---

**Template Version:** 1.0.0 (HO-TP-001)
