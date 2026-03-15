"""Extended MCP tools for Mega Brain.

Standalone tool functions that can be registered with any MCP server.
Each function takes simple inputs and returns JSON-serializable output.
No MCP dependency -- pure Python with pathlib + json only.

Tools:
    graph_query      -- Query the knowledge graph for entity relationships
    agent_lookup     -- Look up an agent by name across all categories
    dossier_search   -- Search dossiers by topic or person
    pipeline_status  -- Get current pipeline operational status
    quality_report   -- Get recent quality scores with optional filtering

Versao: 1.0.0
Data: 2026-03-14
"""

from __future__ import annotations

import json
from pathlib import Path

# Project root -- from core.paths single source of truth
from core.paths import ROOT as _PROJECT_ROOT


# ---------------------------------------------------------------------------
# TOOL 1: graph_query
# ---------------------------------------------------------------------------
def graph_query(
    entity: str,
    max_results: int = 10,
    *,
    root: Path | None = None,
) -> dict:
    """Query the knowledge graph for entity relationships.

    Args:
        entity: Entity name or partial match to search for.
        max_results: Maximum number of entities to return.
        root: Project root override (for testing).

    Returns:
        Dict with matched entities, related edges, and counts.
    """
    base = root or _PROJECT_ROOT
    graph_path = base / ".data" / "knowledge_graph" / "graph.json"

    if not graph_path.exists():
        return {"error": "Knowledge graph not found", "entities": [], "relationships": []}

    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"error": f"Failed to read graph: {exc}", "entities": [], "relationships": []}

    # Entities can be a dict (keyed by ID) or a list
    raw_entities = graph.get("entities", graph.get("nodes", {}))
    if isinstance(raw_entities, dict):
        entity_list = list(raw_entities.values())
    else:
        entity_list = list(raw_entities)

    # Search entities by name, label, or id
    query_lower = entity.lower()
    matches = []
    for ent in entity_list:
        searchable = " ".join(
            str(ent.get(field, ""))
            for field in ("name", "label", "id", "person")
        ).lower()
        if query_lower in searchable:
            matches.append(ent)

    # Find edges connected to matched entities
    match_ids = set()
    for m in matches:
        match_ids.add(m.get("id", ""))
        match_ids.add(m.get("name", ""))

    edges = graph.get("edges", graph.get("links", []))
    if isinstance(edges, dict):
        edges = list(edges.values())

    related_edges = []
    for edge in edges:
        src = edge.get("source", edge.get("from", ""))
        tgt = edge.get("target", edge.get("to", ""))
        if src in match_ids or tgt in match_ids:
            related_edges.append(edge)

    return {
        "query": entity,
        "entities": matches[:max_results],
        "relationships": related_edges[: max_results * 2],
        "total_entities": len(matches),
        "total_relationships": len(related_edges),
    }


# ---------------------------------------------------------------------------
# TOOL 2: agent_lookup
# ---------------------------------------------------------------------------
def agent_lookup(
    name: str,
    *,
    root: Path | None = None,
) -> dict:
    """Look up an agent by name across all categories.

    Args:
        name: Agent name (e.g., 'alex-hormozi', 'closer', 'cfo').
        root: Project root override (for testing).

    Returns:
        Dict with agent metadata: category, files, completeness, path.
    """
    base = root or _PROJECT_ROOT
    agents_dir = base / "agents"
    categories = ["external", "cargo", "system", "business", "personal"]

    if not agents_dir.exists():
        return {"error": "agents/ directory not found"}

    name_lower = name.lower()

    for category in categories:
        cat_dir = agents_dir / category
        if not cat_dir.exists():
            continue

        # Direct match at category level
        agent_dir = cat_dir / name
        if agent_dir.is_dir():
            return _build_agent_info(agent_dir, category)

        # Search in subdirs (cargo has c-level/, sales/, etc.)
        for subdir in sorted(cat_dir.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith(("_", ".")):
                continue

            agent_dir = subdir / name
            if agent_dir.is_dir():
                return _build_agent_info(agent_dir, category)

        # Fuzzy match -- check if name is a substring of dir name
        for item in cat_dir.rglob("*"):
            if item.is_dir() and name_lower in item.name.lower() and _has_agent_files(item):
                return _build_agent_info(item, category)

    return {
        "error": f"Agent '{name}' not found",
        "suggestion": "Try: alex-hormozi, cole-gordon, closer, cfo",
    }


def _has_agent_files(d: Path) -> bool:
    """Check if directory looks like an agent directory."""
    return any((d / f).exists() for f in ("AGENT.md", "SOUL.md", "DNA-CONFIG.yaml"))


def _build_agent_info(agent_dir: Path, category: str) -> dict:
    """Extract agent metadata from its directory."""
    expected_files = ["AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml"]
    files = {f: (agent_dir / f).exists() for f in expected_files}
    present = sum(files.values())
    total = len(expected_files)

    # Try to read first meaningful line of AGENT.md for summary
    summary = ""
    agent_md = agent_dir / "AGENT.md"
    if agent_md.exists():
        try:
            lines = agent_md.read_text(encoding="utf-8").splitlines()[:20]
            for line in lines:
                stripped = line.strip()
                # Skip blank lines, markdown headers, horizontal rules, and blockquotes
                if (
                    not stripped
                    or stripped.startswith("#")
                    or stripped.startswith("---")
                    or stripped.startswith(">")
                    or stripped.startswith("```")
                ):
                    continue
                summary = stripped[:150]
                break
        except OSError:
            pass

    return {
        "name": agent_dir.name,
        "category": category,
        "path": str(agent_dir),
        "files": files,
        "completeness": f"{present}/{total}",
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# TOOL 3: dossier_search
# ---------------------------------------------------------------------------
def dossier_search(
    query: str,
    max_results: int = 5,
    *,
    root: Path | None = None,
) -> dict:
    """Search dossiers by topic or person name.

    Args:
        query: Search term to match against dossier filenames and content.
        max_results: Maximum results to return.
        root: Project root override (for testing).

    Returns:
        Dict with matching dossiers, their paths, and preview text.
    """
    base = root or _PROJECT_ROOT
    dossier_dirs = [
        base / "knowledge" / "external" / "dossiers" / "persons",
        base / "knowledge" / "external" / "dossiers" / "themes",
        base / "knowledge" / "external" / "dossiers" / "system",
        base / "knowledge" / "business" / "dossiers",
    ]

    query_lower = query.lower()
    matches = []

    for d in dossier_dirs:
        if not d.exists():
            continue
        for f in sorted(d.rglob("*.md")):
            if query_lower in f.name.lower():
                preview = _read_preview(f)
                matches.append(
                    {
                        "name": f.stem,
                        "path": str(f),
                        "category": d.name,
                        "preview": preview,
                    }
                )

    return {
        "query": query,
        "results": matches[:max_results],
        "total": len(matches),
    }


def _read_preview(filepath: Path, max_chars: int = 200) -> str:
    """Read first few lines of a file for preview."""
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()[:5]
        return " ".join(line.strip() for line in lines if line.strip())[:max_chars]
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# TOOL 4: pipeline_status
# ---------------------------------------------------------------------------
def pipeline_status(
    *,
    root: Path | None = None,
) -> dict:
    """Get current pipeline operational status.

    Args:
        root: Project root override (for testing).

    Returns:
        Dict with mission state, session info, and next action.
    """
    base = root or _PROJECT_ROOT
    state_file = base / ".claude" / "mission-control" / "MISSION-STATE.json"

    if not state_file.exists():
        return {"status": "unknown", "error": "MISSION-STATE.json not found"}

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"status": "error", "error": str(exc)}

    return {
        "status": "active",
        "current_state": state.get("current_state", {}),
        "session": state.get("session", {}),
        "next_action": state.get("next_action", {}),
    }


# ---------------------------------------------------------------------------
# TOOL 5: quality_report
# ---------------------------------------------------------------------------
def quality_report(
    item_type: str | None = None,
    limit: int = 10,
    *,
    root: Path | None = None,
) -> dict:
    """Get recent quality scores with optional filtering.

    Args:
        item_type: Filter by item type (e.g. 'batch', 'agent', 'dossier').
        limit: Max number of recent scores to return.
        root: Project root override (for testing).

    Returns:
        Dict with recent scores, averages, and totals.
    """
    base = root or _PROJECT_ROOT
    scores_file = base / ".data" / "quality_scores.jsonl"

    if not scores_file.exists():
        return {"scores": [], "total": 0, "message": "No quality scores recorded yet"}

    scores: list[dict] = []
    try:
        for line in scores_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                score = json.loads(line)
                if item_type is None or score.get("item_type") == item_type:
                    scores.append(score)
            except json.JSONDecodeError:
                continue
    except OSError as exc:
        return {"scores": [], "total": 0, "error": str(exc)}

    # Return most recent entries
    recent = scores[-limit:] if scores else []
    avg_score = (
        sum(s.get("total", s.get("score", 0)) for s in recent) / len(recent)
        if recent
        else 0.0
    )

    return {
        "scores": recent,
        "total": len(scores),
        "showing": len(recent),
        "average_score": round(avg_score, 1),
        "filter": item_type or "all",
    }


# ---------------------------------------------------------------------------
# TOOL DEFINITIONS (MCP schema format)
# ---------------------------------------------------------------------------
EXTENDED_TOOLS = [
    {
        "name": "graph_query",
        "description": (
            "Query the knowledge graph for entity relationships. "
            "Search entities by name and discover connected edges. "
            "Returns matched entities and their relationships."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity name or partial match to search for",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of entities to return (default 10)",
                    "default": 10,
                },
            },
            "required": ["entity"],
        },
    },
    {
        "name": "agent_lookup",
        "description": (
            "Look up an agent by name across all categories "
            "(external, cargo, system, business, personal). "
            "Returns agent metadata, file completeness, and summary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent name (e.g. 'alex-hormozi', 'closer', 'cfo')",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "dossier_search",
        "description": (
            "Search dossiers by topic or person name across external "
            "and business knowledge buckets. Returns matching dossier "
            "names, paths, and preview text."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to match against dossier names",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "pipeline_status",
        "description": (
            "Get current pipeline operational status including mission state, "
            "session info, and next recommended action."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "quality_report",
        "description": (
            "Get recent quality scores with optional filtering by item type. "
            "Returns scores, averages, and trend data."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {
                    "type": "string",
                    "description": "Filter by type (e.g. 'batch', 'agent', 'dossier')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max recent scores to return (default 10)",
                    "default": 10,
                },
            },
        },
    },
]

# Handler dispatch map for MCP server registration
EXTENDED_TOOL_HANDLERS = {
    "graph_query": lambda params: graph_query(
        entity=params.get("entity", ""),
        max_results=params.get("max_results", 10),
    ),
    "agent_lookup": lambda params: agent_lookup(
        name=params.get("name", ""),
    ),
    "dossier_search": lambda params: dossier_search(
        query=params.get("query", ""),
        max_results=params.get("max_results", 5),
    ),
    "pipeline_status": lambda params: pipeline_status(),
    "quality_report": lambda params: quality_report(
        item_type=params.get("item_type"),
        limit=params.get("limit", 10),
    ),
}
