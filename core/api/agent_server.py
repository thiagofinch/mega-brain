"""Agent API Server for Mega Brain.

FastAPI server that exposes mind-clone agents for programmatic queries.
Supports listing agents, getting agent details, and querying agent knowledge.

Run: uvicorn core.api.agent_server:app --port 8200
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    FastAPI = None  # type: ignore[assignment, misc]
    HTTPException = None  # type: ignore[assignment, misc]
    Query = None  # type: ignore[assignment, misc]
    JSONResponse = None  # type: ignore[assignment, misc]
    BaseModel = None  # type: ignore[assignment, misc]

from core.api.conclave_service import ConclaveService


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Resolve project root relative to this file: core/api/agent_server.py -> ../../
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"
AGENT_CATEGORIES = ["external", "cargo", "system", "business", "personal"]
AGENT_FILES = ("AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_agent_dir(path: Path) -> bool:
    """Return True if *path* looks like an agent directory (has at least one canonical file)."""
    if not path.is_dir():
        return False
    return any((path / f).exists() for f in AGENT_FILES)


def _category_for(agent_dir: Path) -> str:
    """Walk upward from *agent_dir* to find which top-level category it belongs to."""
    parts = agent_dir.relative_to(AGENTS_DIR).parts
    return parts[0] if parts else "unknown"


def _subcategory_for(agent_dir: Path) -> str | None:
    """Return the subcategory (e.g. 'sales' for cargo/sales/closer), or None."""
    parts = agent_dir.relative_to(AGENTS_DIR).parts
    if len(parts) >= 3:
        return parts[1]
    return None


def _parse_agent(agent_dir: Path) -> dict | None:
    """Parse an agent directory into a structured dict.

    Returns ``None`` when the directory does not exist or contains none of
    the canonical agent files.
    """
    if not _is_agent_dir(agent_dir):
        return None

    file_presence = {f: (agent_dir / f).exists() for f in AGENT_FILES}
    present_count = sum(file_presence.values())

    agent: dict = {
        "id": agent_dir.name,
        "category": _category_for(agent_dir),
        "subcategory": _subcategory_for(agent_dir),
        "path": str(agent_dir.relative_to(PROJECT_ROOT)),
        "files": file_presence,
        "completeness": present_count / len(AGENT_FILES) * 100,
    }

    # Extract a short summary from AGENT.md ----------------------------------
    agent_md = agent_dir / "AGENT.md"
    if agent_md.exists():
        try:
            text = agent_md.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith("#")
                    and not stripped.startswith(">")
                    and not stripped.startswith(("╔", "╚", "║", "┌", "└", "│", "├", "┤", "─"))
                    and not stripped.startswith("|")
                    and len(stripped) > 20
                ):
                    agent["summary"] = stripped[:200]
                    break
        except OSError:
            pass

    # Extract DNA metadata ---------------------------------------------------
    dna_config = agent_dir / "DNA-CONFIG.yaml"
    if dna_config.exists():
        try:
            config = yaml.safe_load(dna_config.read_text(encoding="utf-8"))
            if isinstance(config, dict):
                agent["dna_sources"] = config.get("dna_sources", [])
                agent["domains"] = config.get("domains", [])
        except (yaml.YAMLError, OSError):
            pass

    return agent


def _discover_agents(base: Path | None = None) -> list[dict]:
    """Walk *base*/agents and return parsed metadata for every agent found."""
    root = (base or PROJECT_ROOT) / "agents" if base else AGENTS_DIR
    agents: list[dict] = []

    for category in AGENT_CATEGORIES:
        cat_dir = root / category
        if not cat_dir.is_dir():
            continue
        _walk_for_agents(cat_dir, agents)

    return agents


def _walk_for_agents(directory: Path, accumulator: list[dict]) -> None:
    """Recursively walk *directory*, appending parsed agents to *accumulator*.

    A directory is treated as an agent when it contains canonical files.
    Otherwise we recurse into its children (to handle nesting like
    ``cargo/sales/closer/``).
    """
    if not directory.is_dir():
        return

    for child in sorted(directory.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        if _is_agent_dir(child):
            parsed = _parse_agent(child)
            if parsed:
                accumulator.append(parsed)
        else:
            # Recurse -- the child is likely a sub-category (e.g. cargo/sales/)
            _walk_for_agents(child, accumulator)


def _find_agent_dir(agent_id: str, base: Path | None = None) -> Path | None:
    """Locate the directory for *agent_id* across all categories."""
    root = (base or PROJECT_ROOT) / "agents" if base else AGENTS_DIR

    for category in AGENT_CATEGORIES:
        cat_dir = root / category
        if not cat_dir.is_dir():
            continue
        result = _search_dir(cat_dir, agent_id)
        if result:
            return result
    return None


def _search_dir(directory: Path, agent_id: str) -> Path | None:
    """DFS search for an agent directory named *agent_id* under *directory*."""
    if not directory.is_dir():
        return None

    for child in directory.iterdir():
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        if child.name == agent_id and _is_agent_dir(child):
            return child
        # Recurse into subcategories
        found = _search_dir(child, agent_id)
        if found:
            return found
    return None


def _get_agent_content(agent_id: str) -> dict | None:
    """Return full metadata **and** file contents for *agent_id*."""
    agent_dir = _find_agent_dir(agent_id)
    if agent_dir is None:
        return None

    agent = _parse_agent(agent_dir)
    if agent is None:
        return None

    # Attach raw text of markdown files
    for fname in ("AGENT.md", "SOUL.md", "MEMORY.md"):
        fpath = agent_dir / fname
        key = fname.lower().replace(".", "_").replace("-", "_")
        if fpath.exists():
            try:
                agent[key] = fpath.read_text(encoding="utf-8")
            except OSError:
                agent[key] = f"Error reading {fname}"
        else:
            agent[key] = None

    # Attach raw DNA-CONFIG
    dna_path = agent_dir / "DNA-CONFIG.yaml"
    if dna_path.exists():
        try:
            agent["dna_config_raw"] = dna_path.read_text(encoding="utf-8")
        except OSError:
            agent["dna_config_raw"] = None
    else:
        agent["dna_config_raw"] = None

    return agent


# ---------------------------------------------------------------------------
# FastAPI application factory
# ---------------------------------------------------------------------------


def create_app() -> "FastAPI":
    """Create and configure the FastAPI application."""
    if FastAPI is None:
        raise ImportError(
            "fastapi is required but not installed. "
            "Install with: pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="Mega Brain Agent API",
        description="Query mind-clone agents programmatically.",
        version="1.0.0",
    )

    # -- Routes --------------------------------------------------------------

    @app.get("/")
    async def root():
        return {"service": "Mega Brain Agent API", "version": "1.0.0"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        agents = _discover_agents()
        return {"status": "healthy", "agent_count": len(agents)}

    @app.get("/categories")
    async def list_categories():
        """List agent categories with counts."""
        agents = _discover_agents()
        categories: dict[str, int] = {}
        for a in agents:
            cat = a["category"]
            categories[cat] = categories.get(cat, 0) + 1
        return {"categories": categories}

    @app.get("/agents")
    async def list_agents(category: str | None = None):
        """List all available agents, optionally filtered by category."""
        agents = _discover_agents()
        if category:
            agents = [a for a in agents if a["category"] == category]
        return {"count": len(agents), "agents": agents}

    @app.get("/agents/{agent_id}")
    async def get_agent(agent_id: str):
        """Get detailed information about a specific agent including file contents."""
        agent = _get_agent_content(agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_id}' not found"
            )
        return agent

    @app.get("/agents/{agent_id}/soul")
    async def get_agent_soul(agent_id: str):
        """Get an agent's SOUL.md content."""
        agent = _get_agent_content(agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_id}' not found"
            )
        return {"agent_id": agent_id, "soul": agent.get("soul_md")}

    @app.get("/agents/{agent_id}/memory")
    async def get_agent_memory(agent_id: str):
        """Get an agent's MEMORY.md content."""
        agent = _get_agent_content(agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_id}' not found"
            )
        return {"agent_id": agent_id, "memory": agent.get("memory_md")}

    # -- Conclave routes ---------------------------------------------------

    if BaseModel is not None:

        class DebateRequest(BaseModel):
            """Request body for creating a new Conclave debate."""

            topic: str
            agents: Optional[list[str]] = None

    @app.get("/conclave/agents")
    async def list_debate_agents():
        """List agents available for Conclave debates."""
        service = ConclaveService()
        return {"agents": service.list_debatable_agents()}

    @app.post("/conclave/debate")
    async def create_debate(request: "DebateRequest"):
        """Create a new Conclave debate on a topic."""
        service = ConclaveService()
        result = service.debate(request.topic, request.agents)
        return result.to_dict()

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (for ``uvicorn core.api.agent_server:app``)
# ---------------------------------------------------------------------------

app = create_app() if FastAPI is not None else None
