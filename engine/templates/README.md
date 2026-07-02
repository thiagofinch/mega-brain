# Core Templates

Output templates and structural formats. Following Mega Brain patterns.

## Structure

```
templates/
├── agents/         # Agent file templates (SOUL, DNA-CONFIG, MEMORY)
├── logs/           # Log output templates (batch, execution, conclave)
├── debates/        # Debate dynamics configs
└── phases/         # Phase output templates
```

## Pattern

Templates define OUTPUT FORMAT, not execution logic.
- Execution logic → `core/workflows/*.yaml`
- Atomic instructions → `core/tasks/*.md`
- Templates → `core/templates/*.md`

## Usage

Templates are loaded by:
- Workflows (to format outputs)
- Tasks (to structure results)
- Commands (to display logs)
