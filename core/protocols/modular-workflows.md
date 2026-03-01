# MODULAR WORKFLOW ARCHITECTURE
# Composable Pipeline Building Blocks

> **Version:** 1.0.0
> **Status:** ACTIVE
> **Created:** 2026-02-28
> **Purpose:** Enable composable, reusable workflow modules that can be combined into complex pipelines
> **References:** `wf-pipeline-full.yaml`, `wf-extract-dna.yaml`, `wf-conclave.yaml`

---

## 1. OVERVIEW

```
+==============================================================================+
|                                                                              |
|   MODULAR WORKFLOWS decompose monolithic pipelines into reusable modules     |
|   that can be composed, chained, and parallelized. Each module has           |
|   defined inputs, outputs, and quality gates.                                |
|                                                                              |
|   Current state: 4 monolithic workflows (pipeline, dna, conclave, ingest)    |
|   Target state: Library of composable modules with standardized interfaces   |
|                                                                              |
+==============================================================================+
```

### Why Modular Workflows

| Problem | Monolithic Workflows | Modular Architecture |
|---------|---------------------|---------------------|
| Adding a step | Edit entire YAML, risk breaking flow | Add module, compose into chain |
| Reusing logic | Copy-paste between workflows | Import module by ID |
| Parallel execution | Manual orchestration | Declared in composition |
| Testing | Run entire pipeline | Test module in isolation |
| New pipelines | Write from scratch | Compose from existing modules |

---

## 2. MODULE SPECIFICATION

### 2.1 Module Structure

```yaml
# Every module follows this interface
module:
  id: "mod-chunk-text"              # Unique identifier
  name: "Text Chunker"              # Human-readable name
  version: "1.0.0"
  category: "PROCESSING"            # INGESTION | PROCESSING | EXTRACTION | OUTPUT
  description: "Splits text into semantic chunks"

  interface:
    inputs:
      - name: text
        type: string
        required: true
      - name: max_tokens
        type: integer
        default: 500
    outputs:
      - name: chunks
        type: array
        schema: "chunks-state.schema.json"
      - name: chunk_count
        type: integer

  quality_gate:
    conditions:
      - "chunk_count > 0"
      - "avg_chunk_size >= 100"
      - "avg_chunk_size <= max_tokens"
    on_failure: "HALT"              # HALT | WARN | RETRY

  execution:
    type: "task"                    # task | script | workflow
    ref: "tasks/pipeline/chunk-text.md"
    timeout: 300                    # seconds
    retries: 2

  metadata:
    author: "jarvis"
    tags: ["pipeline", "chunking", "text"]
    dependencies: []                # Other module IDs required
```

### 2.2 Module Categories

| Category | Purpose | Examples |
|----------|---------|---------|
| INGESTION | Bring material into the system | file-reader, youtube-transcriber, docx-parser |
| PROCESSING | Transform and prepare content | text-chunker, deduplicator, language-detector |
| EXTRACTION | Extract structured knowledge | insight-extractor, dna-layer-extractor, theme-detector |
| OUTPUT | Generate final artifacts | agent-builder, dossier-generator, mind-mapper |
| VALIDATION | Verify quality and integrity | source-validator, integrity-checker, quality-scorer |
| ORCHESTRATION | Control flow and routing | batch-router, parallel-dispatcher, checkpoint-manager |

---

## 3. COMPOSITION SYNTAX

### 3.1 Sequential Chain

```yaml
composition:
  id: "comp-basic-pipeline"
  name: "Basic Processing Pipeline"
  type: "sequential"

  chain:
    - module: "mod-read-file"
    - module: "mod-chunk-text"
      inputs:
        text: "${prev.content}"
        max_tokens: 500
    - module: "mod-extract-insights"
      inputs:
        chunks: "${prev.chunks}"
    - module: "mod-classify-dna-layer"
      inputs:
        insights: "${prev.insights}"
```

### 3.2 Parallel Execution

```yaml
composition:
  id: "comp-parallel-extraction"
  name: "Parallel DNA Extraction"
  type: "parallel"

  branches:
    - name: "philosophies"
      module: "mod-extract-dna-layer"
      inputs:
        layer: "L1"
        insights: "${input.insights}"

    - name: "mental_models"
      module: "mod-extract-dna-layer"
      inputs:
        layer: "L2"
        insights: "${input.insights}"

    - name: "heuristics"
      module: "mod-extract-dna-layer"
      inputs:
        layer: "L3"
        insights: "${input.insights}"

  merge:
    module: "mod-assemble-dna"
    inputs:
      layers: "${branches.*}"
```

### 3.3 Conditional Routing

```yaml
composition:
  id: "comp-smart-ingest"
  name: "Smart Ingestion Router"
  type: "conditional"

  router:
    input: "${file.extension}"
    routes:
      - when: "txt"
        module: "mod-read-text"
      - when: "docx"
        module: "mod-read-docx"
      - when: "pdf"
        module: "mod-read-pdf"
      - when: "xlsx"
        module: "mod-read-xlsx"
      - default:
        module: "mod-read-generic"
```

---

## 4. MODULE REGISTRY

### 4.1 Registry File

```
core/workflows/modules/
├── MODULE-REGISTRY.yaml       # Central index of all modules
├── ingestion/
│   ├── mod-read-text.yaml
│   ├── mod-read-docx.yaml
│   └── mod-youtube-transcribe.yaml
├── processing/
│   ├── mod-chunk-text.yaml
│   └── mod-deduplicate.yaml
├── extraction/
│   ├── mod-extract-insights.yaml
│   └── mod-extract-dna-layer.yaml
├── output/
│   ├── mod-build-agent.yaml
│   └── mod-generate-dossier.yaml
└── validation/
    ├── mod-validate-source.yaml
    └── mod-check-integrity.yaml
```

### 4.2 Registry Schema

```yaml
registry:
  version: "1.0.0"
  modules:
    - id: "mod-chunk-text"
      category: "PROCESSING"
      version: "1.0.0"
      path: "processing/mod-chunk-text.yaml"
      status: "ACTIVE"
    # ...
```

---

## 5. MIGRATION PATH

### From Monolithic to Modular

```
PHASE 1: Extract modules from existing workflows
  - wf-pipeline-full.yaml → 8 modules
  - wf-extract-dna.yaml → 3 modules
  - wf-ingest.yaml → 4 modules
  - wf-conclave.yaml → 5 modules

PHASE 2: Standardize interfaces
  - Define input/output schemas for each module
  - Add quality gates
  - Write module tests

PHASE 3: Recompose
  - Rebuild existing workflows using compositions
  - Validate output equivalence with monolithic versions

PHASE 4: Extend
  - Create new modules (youtube, brownfield, etc.)
  - Build new compositions impossible with monolithic approach
```

---

## 6. QUALITY GATES

Every module transition passes through a quality gate:

```
+------------------------------------------------------------------------------+
|  QUALITY GATE LEVELS:                                                        |
|                                                                              |
|  HALT   - Stop pipeline, require human intervention                          |
|  RETRY  - Attempt module again (max retries from config)                     |
|  WARN   - Log warning, continue with degraded output                         |
|  SKIP   - Skip module, pass input directly to next                           |
|                                                                              |
|  DEFAULT: HALT (fail-safe)                                                   |
+------------------------------------------------------------------------------+
```

---

*Modular Workflow Architecture v1.0.0 -- Mega Brain*
