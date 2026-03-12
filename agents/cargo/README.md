# Cargo Roles (L4)

Operational functional roles detected via pipeline.

## Groups

| Group | Agents | Description |
|-------|--------|-------------|
| c-level | CRO, CFO, CMO, COO | Executive advisors |
| sales | Closer, BDR, SDR, Sales Manager | Sales team |
| marketing | Media Buyer, Content Creator | Marketing team |
| operations | Project Manager, CS | Operations team |
| tech | Developer roles | Technical team |
| hr | Recruiter, HR Manager | People team |

## Creation Trigger

Cargo agents are created when `role_detector.py` detects threshold >= 5 mentions.

## Structure per Cargo

```
{group}/{role-id}/
├── AGENT.md    # Role definition (Template V3)
├── SOUL.md     # Communication style
└── MEMORY.md   # Role-specific knowledge
```

## Memory Location

Persistent memory: `.claude/agent-memory/{role-id}/MEMORY.md`
