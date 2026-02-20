# Mega Brain - Architecture Documentation

## Overview

This folder contains comprehensive architecture documentation for the Mega Brain knowledge management system.

## Documentation Structure

```
docs/architecture/
├── README.md                    # This file
├── 01-system-context.md         # High-level system view (C4 Level 1)
├── 02-components.md             # Component breakdown (C4 Level 2)
├── 03-data-flow.md              # Data transformation pipelines
├── 04-integrations.md           # External APIs and MCPs
└── diagrams/
    ├── system-overview.mmd      # Main system diagram
    ├── component-diagram.mmd    # Component relationships
    └── data-flow.mmd            # Sequence diagram
```

## Quick Navigation

| Document | Description | Audience |
|----------|-------------|----------|
| [System Context](01-system-context.md) | What the system does and who uses it | All stakeholders |
| [Components](02-components.md) | Internal structure and configuration | Developers |
| [Data Flow](03-data-flow.md) | How data moves through the system | Developers |
| [Integrations](04-integrations.md) | External dependencies and APIs | DevOps, Developers |

## Diagrams

All diagrams are in Mermaid format (`.mmd`). To view them:

### Option 1: VS Code
Install the "Markdown Preview Mermaid Support" extension

### Option 2: Online
Paste content into [Mermaid Live Editor](https://mermaid.live/)

### Option 3: CLI
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagrams/system-overview.mmd -o system-overview.png
```

## Key Architectural Decisions

1. **Local Processing**: All content processed locally for privacy
2. **AI-Powered Extraction**: Using Claude Code for intelligent analysis
3. **Theme-Based Organization**: 10 predefined knowledge themes
4. **Source Attribution**: Every insight traced back to source

## Technology Stack

| Layer | Technology |
|-------|------------|
| AI Runtime | Claude Code CLI |
| Configuration | JSON, Markdown |
| Scripts | Python 3.x |
| Transcription | youtube-transcript-api, AssemblyAI |
| MCP | @anthropic-ai/mcp-server-filesystem |

## Generated

This documentation was auto-generated using:
```
/documentation/create-architecture-documentation
```

Last updated: December 2024
