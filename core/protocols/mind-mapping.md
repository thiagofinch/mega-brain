# MIND MAPPING PROTOCOL
# Cognitive Structure Visualization & Mental Model Networks

> **Version:** 1.0.0
> **Status:** ACTIVE
> **Created:** 2026-02-28
> **Purpose:** Map and visualize interconnections between mental models, frameworks, and heuristics across DNA layers
> **References:** `agent-cognition.md`, `dna-mental-extraction.md`, `epistemic-standards.md`

---

## 1. OVERVIEW

```
+==============================================================================+
|                                                                              |
|   MIND MAPPING transforms flat DNA extractions into interconnected           |
|   cognitive networks, revealing how an expert's mental models relate,        |
|   reinforce, and sometimes contradict each other.                            |
|                                                                              |
|   Output: A navigable concept map per person showing how their thinking      |
|   elements connect across all 5 DNA layers.                                  |
|                                                                              |
+==============================================================================+
```

### Why Mind Mapping

| Problem | Without Mind Mapping | With Mind Mapping |
|---------|---------------------|------------------|
| DNA is flat lists | L1-L5 are isolated silos | Cross-layer connections visible |
| Reasoning paths unclear | Agent picks random DNA element | Agent follows mapped reasoning chains |
| Expert coherence hidden | Individual elements seem unrelated | Philosophical backbone emerges |
| Cross-person comparison | Compare element by element | Compare reasoning networks |

### Integration with Existing Architecture

- **DNA Extraction (wf-extract-dna.yaml):** Mind Mapping runs AFTER DNA extraction, consuming the 5-layer output
- **Agent Cognition Protocol:** The cascading reasoning (L5 -> L4 -> L3 -> L2 -> L1) uses mind map edges to select relevant elements
- **Conclave Debates:** Mind maps reveal where experts' networks overlap or diverge, informing debate dynamics

---

## 2. CONCEPT MAP STRUCTURE

### 2.1 Node Types

Every DNA element becomes a node in the concept map:

```
+------------------------------------------------------------------------------+
|  NODE TYPES (mapped from DNA layers):                                        |
|                                                                              |
|  [PHI] PHILOSOPHY    (L1) - Core belief / worldview                          |
|  [MM]  MENTAL MODEL  (L2) - Thinking framework                              |
|  [HEU] HEURISTIC     (L3) - Decision shortcut / rule of thumb               |
|  [FW]  FRAMEWORK     (L4) - Structured methodology                          |
|  [MET] METHODOLOGY   (L5) - Step-by-step implementation                     |
|                                                                              |
|  METADATA PER NODE:                                                          |
|  - id: DNA element ID (e.g., PHI-AH-003)                                    |
|  - label: Short name                                                         |
|  - layer: L1-L5                                                              |
|  - source_person: Who originated this element                                |
|  - strength: 0.0-1.0 (how central to the person's thinking)                 |
|  - frequency: How often referenced in source material                        |
|  - chunk_ids: Traceability to source                                         |
+------------------------------------------------------------------------------+
```

### 2.2 Edge Types

Edges define HOW elements relate:

| Edge Type | Symbol | Meaning | Example |
|-----------|--------|---------|---------|
| SUPPORTS | `-->` | Element A reinforces Element B | PHI-AH-003 --> HEU-AH-025 |
| CONTRADICTS | `--X` | Element A conflicts with Element B | PHI-CG-001 --X PHI-AH-007 |
| IMPLEMENTS | `==>` | Element A is a concrete application of B | MET-CG-005 ==> FW-CG-002 |
| EXTENDS | `~~>` | Element A adds nuance to Element B | HEU-JM-012 ~~> MM-JM-003 |
| REQUIRES | `-->!` | Element A depends on Element B | FW-AH-008 -->! PHI-AH-001 |
| SPECIALIZES | `->>` | Element A is a domain-specific version of B | HEU-CG-018 ->> HEU-AH-025 |

### 2.3 Edge Detection Methods

```
+------------------------------------------------------------------------------+
|  METHOD 1: EXPLICIT REFERENCE (Highest confidence)                           |
|  - Source material directly links two concepts                               |
|  - Example: "My commission structure (HEU) is based on the                   |
|    principle that cash flow is king (PHI)"                                    |
|  - Confidence: 0.9-1.0                                                       |
|                                                                              |
|  METHOD 2: CO-OCCURRENCE (Medium confidence)                                 |
|  - Two elements appear in the same chunk repeatedly                          |
|  - Threshold: >= 3 co-occurrences across different materials                 |
|  - Confidence: 0.6-0.8                                                       |
|                                                                              |
|  METHOD 3: SEMANTIC SIMILARITY (Lower confidence)                            |
|  - Elements share vocabulary, concepts, or logical structure                 |
|  - Requires embedding comparison (Voyage AI)                                 |
|  - Threshold: cosine similarity > 0.82                                       |
|  - Confidence: 0.4-0.6                                                       |
|                                                                              |
|  METHOD 4: LOGICAL INFERENCE (Lowest confidence)                             |
|  - System infers relationship from structure                                 |
|  - Example: A methodology that uses a framework's steps                      |
|  - Confidence: 0.3-0.5                                                       |
|  - MUST be flagged as "inferred" in output                                   |
+------------------------------------------------------------------------------+
```

---

## 3. MAPPING WORKFLOW

### 3.1 Input Requirements

```
+------------------------------------------------------------------------------+
|  REQUIRED INPUTS:                                                            |
|                                                                              |
|  1. Completed DNA extraction (all 5 layers populated)                        |
|  2. Source chunks with IDs (for traceability)                                |
|  3. INSIGHTS-STATE.json (for co-occurrence analysis)                         |
|                                                                              |
|  OPTIONAL INPUTS:                                                            |
|  4. Existing mind maps from other persons (for cross-person edges)           |
|  5. Domain glossary (for semantic similarity calibration)                    |
+------------------------------------------------------------------------------+
```

### 3.2 Process Steps

```
STEP 1: NODE EXTRACTION
  - Parse DNA-CONFIG.yaml for all elements
  - Create node for each element with metadata
  - Calculate strength score from chunk frequency

STEP 2: EXPLICIT EDGE DETECTION
  - Scan source chunks for cross-references between elements
  - When element A's description mentions element B, create edge
  - Assign confidence based on explicitness

STEP 3: CO-OCCURRENCE ANALYSIS
  - Build co-occurrence matrix from chunks
  - Filter pairs with >= 3 co-occurrences
  - Create edges with medium confidence

STEP 4: SEMANTIC CLUSTERING
  - Group elements by semantic similarity
  - Identify clusters (reasoning chains)
  - Create edges within clusters

STEP 5: CROSS-LAYER CHAIN DETECTION
  - Trace reasoning paths from L5 up to L1
  - Every methodology should connect to at least one philosophy
  - Flag orphan elements (no connections)

STEP 6: VALIDATION
  - Review orphan elements (possible missing edges)
  - Verify contradictions are genuine (not misclassification)
  - Human review queue for low-confidence edges

STEP 7: OUTPUT GENERATION
  - Generate MIND-MAP.yaml (machine-readable)
  - Generate MIND-MAP.md (human-readable visualization)
  - Update DNA-CONFIG.yaml with connection metadata
```

---

## 4. OUTPUT FORMAT

### 4.1 YAML Schema (Machine-Readable)

```yaml
mind_map:
  person: "ALEX-HORMOZI"
  version: "1.0.0"
  generated: "2026-03-01"
  source_dna: "knowledge/dna/persons/ALEX-HORMOZI/DNA.yaml"

  nodes:
    - id: "PHI-AH-001"
      label: "Volume negates luck"
      layer: L1
      strength: 0.95
      frequency: 47
      cluster: "WORK_ETHIC"

  edges:
    - from: "PHI-AH-001"
      to: "HEU-AH-025"
      type: SUPPORTS
      confidence: 0.92
      evidence: "chunk_034, chunk_089"
      detection_method: EXPLICIT_REFERENCE

  clusters:
    - id: "WORK_ETHIC"
      label: "Volume & Work Ethic"
      nodes: ["PHI-AH-001", "HEU-AH-025", "MET-AH-003"]
      description: "Core reasoning chain around massive action"

  orphans: []

  statistics:
    total_nodes: 87
    total_edges: 134
    avg_connections_per_node: 3.1
    orphan_count: 0
    cross_layer_chains: 12
```

### 4.2 Markdown Output (Human-Readable)

```markdown
# Mind Map: ALEX HORMOZI

## Reasoning Chains (L5 -> L1)

### Chain 1: VOLUME & WORK ETHIC
MET-AH-003 (100 Calls/Day) ==> FW-AH-008 (Sales Machine)
  --> HEU-AH-025 (Volume > Skill)
    --> MM-AH-001 (Input/Output Ratio)
      --> PHI-AH-001 (Volume Negates Luck)

### Chain 2: OFFER CREATION
MET-AH-012 (Value Equation) ==> FW-AH-015 (Grand Slam Offer)
  --> HEU-AH-030 (40% Margin Minimum)
    --> MM-AH-007 (Scarcity + Urgency)
      --> PHI-AH-003 (Charge What You're Worth)

## Cross-Person Connections (if applicable)
PHI-AH-001 (Volume) --X PHI-CG-005 (Quality Over Quantity)
  Type: CONTRADICTS | Confidence: 0.78
  Note: Different contexts - AH for outbound volume, CG for call quality
```

---

## 5. APPLICATIONS

### 5.1 Agent Reasoning Enhancement

Mind maps improve agent cognition by providing:

1. **Reasoning chain shortcuts:** Agent can follow mapped chains instead of searching all layers
2. **Contradiction awareness:** Agent knows which elements conflict before answering
3. **Cluster-based retrieval:** Load an entire reasoning cluster, not just individual elements

### 5.2 Cross-Person Analysis

When mind maps exist for multiple persons:

1. **Overlap detection:** Which concepts do experts agree on?
2. **Unique contributions:** Which elements are original to one person?
3. **Debate fuel:** Contradictions between persons become structured debate topics

### 5.3 Knowledge Gap Detection

Orphan analysis reveals:

1. **Methodologies without philosophy:** Implementation without clear "why"
2. **Philosophies without implementation:** Beliefs not operationalized
3. **Isolated heuristics:** Rules without reasoning chain support

---

## 6. QUALITY METRICS

| Metric | Target | Minimum |
|--------|--------|---------|
| Orphan rate | <5% | <10% |
| Avg connections/node | >3.0 | >2.0 |
| Cross-layer chains | >10 | >5 |
| High-confidence edges (>0.8) | >60% | >40% |
| Human-validated edges | >30% | >15% |

---

## 7. LIMITATIONS

- Mind maps are DERIVED artifacts -- they reflect what was extracted, not everything the expert knows
- Semantic similarity can produce false positives for related but distinct concepts
- Cross-person edges require both persons' DNA to be fully extracted
- Mind maps need re-generation when significant new material is processed

---

*Mind Mapping Protocol v1.0.0 -- Mega Brain*
