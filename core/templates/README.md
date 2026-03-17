# Core Templates

Output templates and structural formats. Following Mega Brain patterns.

## Structure

```
templates/
├── agents/         # Agent file templates (SOUL, DNA-CONFIG, MEMORY)
├── logs/           # Log output templates (batch, execution, conclave)
├── debates/        # Debate dynamics configs
├── output/         # MCE pipeline output templates (post-step reports)
│   └── MCE-OUTPUT-TEMPLATES.md   # Unified 7-template file (v2.0)
├── phases/         # Phase output templates (legacy)
└── workspace/      # Workspace structure templates
```

## Pattern

Templates define OUTPUT FORMAT, not execution logic.
- Execution logic → `core/workflows/*.yaml`
- Atomic instructions → `core/tasks/*.md`
- Templates → `core/templates/*.md`

## MCE Output Templates (v2.0)

Unified template file consolidating legacy Phase 5 templates into the current
13-step MCE pipeline. Located at `output/MCE-OUTPUT-TEMPLATES.md`.

| # | Template | MCE Steps | When |
|---|----------|-----------|------|
| 1 | EXTRACTION SUMMARY | S03-S05 | After DNA extraction |
| 2 | PERSON AGENT | S10.4 | After mind-clone agent creation |
| 3 | CARGO AGENT ENRICHMENT | S10.4 | After cargo DNA enrichment |
| 4 | THEME DOSSIER | S10.1-S10.2 | After theme consolidation |
| 5 | WORKSPACE SYNC | S11 | After org structure sync |
| 6 | VALIDATION GATE | S12 | After final validation |
| 7 | SESSION CONSOLIDATION | Post-session | After all sources processed |

**Width contract:**
- Realtime panels (mce_step_logger.py): PW=62 inner, 66 total
- Output templates + session reports: RW=72 inner, 76 total

## Usage

Templates are loaded by:
- Workflows (to format outputs)
- Tasks (to structure results)
- Commands (to display logs)
- MCE hooks (mce_step_logger.py, mce_session_reporter.py)
