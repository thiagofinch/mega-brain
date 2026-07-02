---
name: vault-graph
description: "9-operation interactive graph analysis for the knowledge vault. Routes natural language to bash operations: health, triangles, bridges, clusters, hubs, siblings, forward, backward, query."
version: "1.0.0"
owner_squad: mega-brain
megabrain_tier: Tier2
context: inline
agent: general-purpose
user-invocable: true
argument-hint: "[operation] [note-title]"
---

# Vault Graph Analysis

9 operations for understanding vault structure. All implemented in bash, zero external dependencies.

## Operations

| Operation | What it finds | Use when |
|-----------|---------------|----------|
| `health` | Orphans, link density, coverage score | Weekly maintenance check |
| `triangles` | A→B, A→C, B↛C (synthesis gaps) | Finding synthesis opportunities |
| `bridges` | High-backlink notes (removal = disconnect) | Understanding critical structure |
| `clusters` | Low-connectivity isolated notes | Finding disconnected knowledge |
| `hubs` | Most referenced notes | Understanding influence flow |
| `siblings` | Same topic, no mutual link | Finding missed connections |
| `forward [note] [hops]` | N-hop forward traversal | Exploring knowledge frontier |
| `backward [note]` | All notes linking to this | Finding context and influence |
| `query [natural language]` | Routes to correct operation | When unsure which op to use |

## Usage

```
/vault-graph health
/vault-graph triangles
/vault-graph hubs
/vault-graph forward "capability algebra" 2
/vault-graph backward "resolve-executor"
/vault-graph query "find synthesis opportunities around routing"
```

## Implementation

All operations run via `.synapse/graph/operations/{operation}.sh`

To invoke from shell:
```bash
bash .synapse/graph/operations/health.sh [vault-path]
bash .synapse/graph/operations/triangles.sh [vault-path]
bash .synapse/graph/operations/bridges.sh [vault-path]
bash .synapse/graph/operations/clusters.sh [vault-path]
bash .synapse/graph/operations/hubs.sh [vault-path]
bash .synapse/graph/operations/siblings.sh [vault-path] [topic]
bash .synapse/graph/operations/forward.sh [vault-path] [note-title] [hops]
bash .synapse/graph/operations/backward.sh [vault-path] [note-title]
bash .synapse/graph/operations/query.sh [vault-path] "natural language query"
```

Default vault path if not specified: `.synapse/vault/insights`

## Outputs

Every operation produces 2 sections:
1. **Findings:** interpreted results using note titles, not file paths
2. **Actions:** specific commands to run next (e.g., `/vault-pipeline claim "synthesis opportunity found"`)

## Execution Protocol

When `/vault-graph {operation} [args]` is invoked:

1. Parse `$ARGUMENTS` — first token is operation name, remainder are operation-specific args
2. Map operation to script: `.synapse/graph/operations/{operation}.sh`
3. Run script with provided args via Bash tool
4. Present results in 2 sections: **Findings** (interpreted) and **Actions** (next steps)
5. For `query` operation: pass the full natural language string as second arg

## Operation Details

### health
Reports overall vault connectivity:
- Total note count (excluding index.md)
- Orphan count (notes with no `[[links]]`)
- Total link count
- Link density (links per note)
- Orphan rate (percentage)

### triangles
Finds synthesis opportunities — pairs of notes that both link to a common note but do not link to each other. Output format: `TRIANGLE: NoteA → B + C (no B↔C link)`

### bridges
Lists notes by incoming link count (descending). High-count notes are structural bridges — removing them would fragment the graph.

### clusters
Identifies notes with both low incoming (≤1) and low outgoing (≤1) connectivity. These are candidates for either enrichment or archival.

### hubs
Top-10 most referenced notes by incoming link count. Useful for understanding knowledge influence and entry points.

### siblings
Given a topic note, finds all notes that reference the same topic but lack mutual links. Accepts optional topic argument (default: `hub`).

### forward
Traverses N hops forward from a starting note, showing the knowledge frontier reachable from that note. Accepts note title and hop depth (default: 2).

### backward
Lists all notes containing a `[[link]]` to the target note. Shows direct intellectual predecessors and context providers.

### query
Natural language router. Maps query phrases to the appropriate operation. Examples:
- "find synthesis opportunities" → triangles
- "what are the hubs?" → hubs
- "find orphans" → health
- "backward from resolve-executor" → backward
