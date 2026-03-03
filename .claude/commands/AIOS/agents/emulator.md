# emulator

> **Pipeline Position:** Phase 8 - Clone Activation (Production)
> **Handoff from:** @debate (Phase 7)
> **Alias:** Mirror

Load and activate the Emulator/Mirror agent from `.aiox/development/agents/emulator.md`

## Commands

| Command | Description |
|---------|-------------|
| `*help` | Show available commands |
| `*activate {slug}` | Activate a clone |
| `*list-minds` | Available clones |
| `*dual {c1} {c2}` | Two-clone mode |
| `*roundtable {c1} {c2} {c3}` | Council session |
| `*advice` | Get advice from active clone |
| `*status` | Clone metadata |
| `*exit` | Return to Mirror mode |

## Direct Activation

```
@emulator alex-hormozi     # Activates as Alex Hormozi directly
@emulator *activate cole-gordon
```

## Modes

- **Single**: One clone active
- **Dual**: Two clones in conversation
- **Roundtable**: 3-4 clones in council
