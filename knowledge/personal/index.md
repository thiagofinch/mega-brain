# Knowledge / Personal

> **Bucket 3** -- Founder's cognitive data. NEVER committed.
> **Layer:** L3 ONLY -- 100% gitignored, zero exceptions.
> **paths.py constant:** `KNOWLEDGE_PERSONAL`

## Purpose

This bucket contains the **founder's personal** cognitive data: private calls,
journaling, personal reflections, email threads, and message archives. This is
the most sensitive bucket and must NEVER be committed to version control.

## Structure

```
knowledge/personal/
  _calls/           -- Call recordings, transcripts, summaries
  _cognitive/       -- Personal reflections, decision journals
  _email/           -- Email threads and correspondence
  _messages/        -- WhatsApp, Slack DMs, private messages
  inbox/            -- Triage area for new personal content
    pending/        -- Awaiting classification
    rejected/       -- Did not pass quality gate
```

## Security Model

This bucket has a **dedicated `.gitignore`** at its root that blocks everything
except `.gitignore` itself and `index.md`:

```
# knowledge/personal/.gitignore
*
!.gitignore
!index.md
```

This is a **failsafe**: even if the parent `.gitignore` rules are misconfigured,
this local `.gitignore` ensures no personal data leaks into the repository.

## Routing

```python
from core.paths import KNOWLEDGE_PERSONAL, ROUTING

ROUTING["personal_data"]   # -> knowledge/personal/
ROUTING["personal_inbox"]  # -> knowledge/personal/inbox/
```

## Privacy Rules

1. **NEVER** commit any file from this bucket
2. **NEVER** reference personal content in tracked files (no paths, no quotes)
3. **NEVER** include personal data in agent MEMORY.md files that are tracked
4. Agents may READ from personal/ during sessions but must NOT persist references
5. RAG indexes built from personal/ content stay in `.data/` (also gitignored)

## Relationship to Other Buckets

- Personal insights that become business-relevant should be COPIED (not moved)
  to workspace/ after sanitization
- Personal learning goals may reference external/ experts
- The founder's "mind clone" agent in agents/persons/ may draw from this bucket
  during live sessions only
