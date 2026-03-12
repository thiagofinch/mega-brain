# Mega Brain - System Context

## Overview

Mega Brain is an intelligent knowledge management system designed for building high-ticket B2B sales playbooks. The system processes video content, transcriptions, and documents to extract, classify, and organize actionable sales knowledge into a structured knowledge base.

## Purpose

Transform unstructured sales content (videos, podcasts, courses) into organized, searchable, and actionable knowledge documents that can be used to train sales teams and build consistent playbooks.

## Target Domain

- **Industry**: B2B Sales
- **Ticket Size**: High-ticket ($10k+)
- **Focus Areas**: Outbound sales, team structure, compensation, hiring, metrics

---

## System Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                        MEGA BRAIN SYSTEM                        │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐ │
│  │ inbox │───▶│ Processing   │───▶│ KNOWLEDGE/            │ │
│  │          │    │ Pipeline     │    │ (10 theme folders)    │ │
│  └──────────┘    └──────────────┘    └───────────────────────┘ │
│       ▲               │                                         │
│       │               ▼                                         │
│  ┌────┴─────┐   ┌──────────────┐                               │
│  │ .claude/ │   │ scripts/     │                               │
│  │ configs  │   │ utilities    │                               │
│  └──────────┘   └──────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │ YouTube │          │Assembly │
    │   API   │          │   AI    │
    └─────────┘          └─────────┘
```

---

## External Actors

### Human Actors

| Actor | Role | Interactions |
|-------|------|--------------|
| **Content Curator** | Identifies and drops content into INBOX | Adds videos, URLs, documents |
| **Knowledge Consumer** | Uses extracted knowledge | Reads KNOWLEDGE files |
| **System Administrator** | Configures and maintains system | Edits .claude/ configs |

### System Actors

| System | Purpose | Integration Type |
|--------|---------|------------------|
| **YouTube** | Source of video transcripts | API (youtube-transcript-api) |
| **AssemblyAI** | Transcription service for local files | REST API |
| **Claude Code** | AI-powered extraction and analysis | Native (CLI) |

---

## Key Interactions

### 1. Content Ingestion
```
User drops content → inbox/
                         ↓
              /scan-inbox detects new files
                         ↓
              Suggests processing action
```

### 2. Video Processing
```
YouTube URL → youtube-transcript-api → Transcript (.txt)
Local Video → AssemblyAI API → Transcript (.txt)
```

### 3. Knowledge Extraction
```
Transcript → b2b-sales-expert agent → Theme classification
                                          ↓
                              KNOWLEDGE/[theme]/[topic].md
```

---

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| **Accuracy** | Preserve exact numbers and metrics from sources |
| **Traceability** | Every piece of knowledge must have source attribution |
| **Organization** | Knowledge organized by 10 predefined themes |
| **Language** | Output in Portuguese (BR) |
| **Specificity** | Actionable insights only, no generic advice |

---

## Constraints

1. **Data Privacy**: Local processing, no cloud storage of sensitive content
2. **API Dependencies**: Requires AssemblyAI API key for local file transcription
3. **Format Support**: Limited to specific video/audio formats (MP4, MP3, WAV, M4A)
4. **Language**: Primary focus on English content sources, Portuguese output

---

## Context Diagram (C4 Level 1)

```
┌─────────────┐         ┌─────────────────────────────┐
│   Content   │         │                             │
│   Curator   │────────▶│                             │
└─────────────┘  drops  │                             │
                content │                             │
                        │        MEGA BRAIN           │
┌─────────────┐         │                             │
│  Knowledge  │◀────────│   Knowledge Management      │
│  Consumer   │  reads  │        System               │
└─────────────┘ playbook│                             │
                        │                             │
                        └──────────┬──────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │ YouTube  │  │ Assembly │  │  Claude  │
              │   API    │  │    AI    │  │   Code   │
              └──────────┘  └──────────┘  └──────────┘
```
