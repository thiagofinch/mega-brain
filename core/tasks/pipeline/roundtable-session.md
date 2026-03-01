# Roundtable Session

```yaml
---
task: TSK-051
execution_type: Agent
responsible: "@jarvis"
---
```

---

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Conduct Roundtable Session |
| status | active |
| responsible_executor | @jarvis |
| execution_type | Agent |
| input | 3-4 activated clone contexts, discussion topic, optional constraints |
| output | Structured roundtable transcript with synthesis |
| action_items | 9 steps across 5 phases |
| acceptance_criteria | All phases completed, all clones participated, synthesis produced |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| clone_contexts | object[] | yes | Array of 3-4 loaded clone contexts (SOUL + MEMORY + DNA-CONFIG per clone) |
| topic | string | yes | Central topic or question for the roundtable |
| constraints | string | no | Specific constraints or focus areas (e.g., "focus on B2B SaaS", "budget under 50k") |
| desired_outcome | string | no | What the user wants from the session (e.g., "action plan", "comparison", "decision") |
| speaking_order | string | no | "alphabetical" (default), "relevance" (most relevant to topic speaks first) |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| roundtable_transcript | markdown | chat | Full structured roundtable output shown in chat |
| session_file | file | logs/clone-sessions/RT-{YYYY-MM-DD}-{topic}.md | Saved transcript |
| agreement_matrix | table | within transcript | Matrix showing agreement/disagreement by topic |
| synthesis | section | within transcript | System analysis with consensus, tensions, recommendations |

---

## Execution

### Phase 1: Opening Statements

**Quality Gate:** QG-ROUNDTABLE-OPENING

1. Establish speaking order (alphabetical or by relevance to topic)
2. For each clone in order:
   a. Run Identity Checkpoint (4 checks) for this clone
   b. Generate opening statement (2-3 paragraphs) in clone's authentic voice
   c. Statement must cite at least one DNA element (framework, heuristic, or philosophy)
   d. Statement must directly address the topic
3. Validate that each clone's opening is distinct from the others (different angle, different voice)

**Failure condition:** A clone's opening statement fails the Identity Checkpoint or is generic.

### Phase 2: Directed Questions

**Quality Gate:** QG-ROUNDTABLE-QUESTIONS

1. Analyze opening statements to identify:
   - Areas of disagreement between clones
   - Claims that need deeper exploration
   - Assumptions that should be challenged
2. Formulate 2-3 directed questions targeting specific clones
3. For each question:
   a. Pose the question to the target clone
   b. Generate the clone's response (in their voice, citing DNA)
   c. If another clone would naturally respond or challenge, include their response
4. Questions must probe substance, not just surface positions

**Failure condition:** Questions are generic or do not probe the actual disagreements.

### Phase 3: Cross-Debate

**Quality Gate:** QG-ROUNDTABLE-DEBATE

1. Identify the 2-3 strongest points of tension from Phases 1-2
2. For each tension point:
   a. Have the disagreeing clones directly address each other
   b. Each must reference specific claims made in earlier phases
   c. Each must cite their DNA when supporting their position
   d. Responses should be substantive (not just "I disagree")
3. Ensure balanced participation -- no clone dominates the debate

**Failure condition:** Cross-debate is superficial or one clone dominates.

### Phase 4: Final Positions

**Quality Gate:** QG-ROUNDTABLE-FINALS

1. Each clone gives a concise final statement (1-2 paragraphs)
2. Clones may update their position based on the discussion
3. Each clone declares a confidence level (0-100%) with justification
4. Final positions are presented in a summary table

**Failure condition:** A clone's final position contradicts their DNA without acknowledging it.

### Phase 5: Synthesis

**Quality Gate:** QG-ROUNDTABLE-SYNTHESIS

1. Identify and document consensus points (what ALL clones agree on)
2. Identify and document key tensions (where they disagree, with citations from each side)
3. Build agreement matrix (topic x clone: agree/disagree/nuanced)
4. If desired_outcome was specified, generate actionable recommendations
5. Clearly mark synthesis as SYSTEM ANALYSIS (not a clone's opinion)
6. Save complete transcript to `logs/clone-sessions/`

**Failure condition:** Synthesis misrepresents a clone's position or presents system opinion as clone opinion.

---

## Acceptance Criteria

- [ ] All 5 phases completed in order
- [ ] Each clone spoke in every applicable phase
- [ ] Each clone maintained their distinct voice throughout (no voice blending)
- [ ] Identity Checkpoint passed for each clone before their first statement
- [ ] Every factual claim is traceable to a clone's DNA elements
- [ ] No clone dominated the discussion (balanced participation)
- [ ] Agreement matrix accurately reflects positions
- [ ] Synthesis is clearly marked as system analysis
- [ ] Tensions are documented with source citations from both sides
- [ ] Transcript saved to logs/clone-sessions/
- [ ] Maximum 4 clones participated (hard limit)

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| deactivate | Session complete | Session log, clone contexts |
| activate-clone (TSK-050) | User requests follow-up single clone session | Clone context from roundtable |
| (MEMORY update) | New insights emerged during session | Insights per clone for MEMORY.md review |

---

## Roundtable Moderation Rules

```
+-----------------------------------------------------------------------------+
|                                                                             |
|  THE EMULATOR AS MODERATOR:                                                 |
|                                                                             |
|  1. NEUTRALITY                                                              |
|     +-- The emulator does NOT take sides                                    |
|     +-- All clones get equal speaking time                                  |
|     +-- The emulator does NOT inject its own opinion                        |
|     +-- Synthesis is clearly labeled as system analysis                     |
|                                                                             |
|  2. QUALITY ENFORCEMENT                                                     |
|     +-- If a clone makes a claim, it must be traceable to DNA              |
|     +-- If a clone's response is generic, the emulator re-generates it     |
|     +-- If a clone goes off-topic, the emulator redirects                  |
|                                                                             |
|  3. CONFLICT MANAGEMENT                                                     |
|     +-- Disagreements are documented, not resolved by force                |
|     +-- Each side's sources are cited                                       |
|     +-- "Unresolved" is a valid status for a tension                        |
|     +-- The user decides how to handle unresolved tensions                 |
|                                                                             |
|  4. PARTICIPATION BALANCE                                                   |
|     +-- Track word count per clone across all phases                       |
|     +-- If imbalance > 40%, actively redirect to underrepresented clone    |
|     +-- Each clone must speak in at least 3 of the 4 speaking phases       |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Clone has no knowledge on the topic | Clone states "This isn't my area of expertise" in their voice; still participates on adjacent aspects |
| Two clones have identical positions | Emulator probes for nuances; highlights subtle differences in reasoning or emphasis |
| User requests 5+ clones | Reject: "Roundtable supports a maximum of 4 participants for quality reasons" |
| Clone contradicts itself across phases | Flag it: "Note: {Clone} appears to have shifted position between Phase 1 and Phase 4" |
| Topic is too broad | Emulator narrows it: "To keep the discussion focused, I'll frame this as: {narrowed topic}" |
| User wants to interject mid-roundtable | Pause the roundtable, address user question, resume where left off |

---

## Notes

- Roundtable sessions are the most complex interaction mode. Quality depends on maintaining distinct voices across all clones throughout all phases.
- The 4-clone limit exists because beyond that, voice distinction degrades and the output becomes unwieldy.
- The agreement matrix is the highest-value output for decision-making -- ensure it is accurate.
- Sessions should typically take 3-5 minutes of generation time. If rushing, quality drops.
- The synthesis phase is where the emulator adds the most value: connecting positions, identifying patterns, and (if requested) making recommendations.
- All recommendations in the synthesis must cite which clones' positions informed them.

---

**Template Version:** 1.0.0 (HO-TP-001)
