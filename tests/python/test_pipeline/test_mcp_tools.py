"""Tests for extended MCP tools (mcp_tools.py).

Each tool is tested with:
  - Missing/empty filesystem (graceful error handling)
  - Valid filesystem data (correct results)
  - Edge cases (fuzzy match, filters, empty results)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.intelligence.rag.mcp_tools import (
    agent_lookup,
    dossier_search,
    graph_query,
    pipeline_status,
    quality_report,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_graph(tmp_path: Path) -> Path:
    """Create a mock knowledge graph."""
    graph_dir = tmp_path / ".data" / "knowledge_graph"
    graph_dir.mkdir(parents=True)

    graph = {
        "entities": {
            "PESSOA:alex-hormozi": {
                "id": "PESSOA:alex-hormozi",
                "type": "pessoa",
                "label": "Alex Hormozi",
                "person": "alex-hormozi",
                "domains": ["vendas"],
                "weight": 1.0,
            },
            "FW-AH-001": {
                "id": "FW-AH-001",
                "type": "framework",
                "label": "Value Equation",
                "person": "alex-hormozi",
                "domains": ["offers"],
                "weight": 0.9,
            },
            "PESSOA:cole-gordon": {
                "id": "PESSOA:cole-gordon",
                "type": "pessoa",
                "label": "Cole Gordon",
                "person": "cole-gordon",
                "domains": ["vendas"],
                "weight": 1.0,
            },
        },
        "edges": [
            {
                "source": "PESSOA:alex-hormozi",
                "target": "FW-AH-001",
                "rel_type": "TEM",
                "weight": 1.0,
            },
        ],
        "stats": {"total_entities": 3, "total_edges": 1},
    }

    (graph_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    return tmp_path


@pytest.fixture()
def mock_agents(tmp_path: Path) -> Path:
    """Create mock agent directories."""
    # External agent
    ext = tmp_path / "agents" / "external" / "alex-hormozi"
    ext.mkdir(parents=True)
    (ext / "AGENT.md").write_text("# Alex Hormozi\nExpert in offers and sales.", encoding="utf-8")
    (ext / "SOUL.md").write_text("# SOUL", encoding="utf-8")
    (ext / "MEMORY.md").write_text("# MEMORY", encoding="utf-8")
    (ext / "DNA-CONFIG.yaml").write_text("version: 1.0", encoding="utf-8")

    # Cargo agent nested
    cargo = tmp_path / "agents" / "cargo" / "c-level" / "cfo"
    cargo.mkdir(parents=True)
    (cargo / "AGENT.md").write_text("# CFO\nChief Financial Officer", encoding="utf-8")
    (cargo / "SOUL.md").write_text("# SOUL", encoding="utf-8")

    # System agent
    sys_agent = tmp_path / "agents" / "system" / "conclave"
    sys_agent.mkdir(parents=True)
    (sys_agent / "AGENT.md").write_text("# Conclave", encoding="utf-8")

    return tmp_path


@pytest.fixture()
def mock_dossiers(tmp_path: Path) -> Path:
    """Create mock dossier files."""
    persons = tmp_path / "knowledge" / "external" / "dossiers" / "persons"
    themes = tmp_path / "knowledge" / "external" / "dossiers" / "themes"
    persons.mkdir(parents=True)
    themes.mkdir(parents=True)

    (persons / "DOSSIER-ALEX-HORMOZI.md").write_text(
        "# Dossier Alex Hormozi\nExpert in $100M offers and gym launch.",
        encoding="utf-8",
    )
    (themes / "DOSSIER-OBJECTION-HANDLING.md").write_text(
        "# Objection Handling\nTechniques for handling sales objections.",
        encoding="utf-8",
    )
    (themes / "DOSSIER-PRICING.md").write_text(
        "# Pricing\nPremium pricing strategies.",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture()
def mock_mission_state(tmp_path: Path) -> Path:
    """Create mock MISSION-STATE.json."""
    mc = tmp_path / ".claude" / "mission-control"
    mc.mkdir(parents=True)

    state = {
        "current_state": {
            "phase": 4,
            "phase_name": "Pipeline",
            "status": "IN_PROGRESS",
            "source_code": "CG",
            "batch_current": 3,
            "batch_total": 8,
            "percent_complete": 37.5,
        },
        "session": {
            "id": "SESSION-2026-03-14-001",
            "is_active": True,
        },
        "next_action": {
            "description": "Process BATCH-004 Cole Gordon",
        },
    }

    (mc / "MISSION-STATE.json").write_text(json.dumps(state), encoding="utf-8")
    return tmp_path


@pytest.fixture()
def mock_quality_scores(tmp_path: Path) -> Path:
    """Create mock quality_scores.jsonl."""
    data_dir = tmp_path / ".data"
    data_dir.mkdir(parents=True)

    scores = [
        {"item_type": "batch", "item_id": "BATCH-001", "total": 85},
        {"item_type": "batch", "item_id": "BATCH-002", "total": 72},
        {"item_type": "agent", "item_id": "closer", "total": 90},
        {"item_type": "dossier", "item_id": "DOSSIER-AH", "total": 68},
        {"item_type": "batch", "item_id": "BATCH-003", "total": 78},
    ]

    lines = [json.dumps(s) for s in scores]
    (data_dir / "quality_scores.jsonl").write_text("\n".join(lines), encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# TESTS: graph_query
# ---------------------------------------------------------------------------
class TestGraphQuery:
    def test_returns_empty_when_no_graph(self, tmp_path: Path) -> None:
        result = graph_query("hormozi", root=tmp_path)
        assert "error" in result
        assert result["entities"] == []

    def test_finds_entities_by_name(self, mock_graph: Path) -> None:
        result = graph_query("hormozi", root=mock_graph)
        assert result["total_entities"] >= 1
        ids = [e["id"] for e in result["entities"]]
        assert "PESSOA:alex-hormozi" in ids

    def test_finds_related_edges(self, mock_graph: Path) -> None:
        result = graph_query("hormozi", root=mock_graph)
        assert result["total_relationships"] >= 1
        edge = result["relationships"][0]
        assert edge["source"] == "PESSOA:alex-hormozi"
        assert edge["target"] == "FW-AH-001"

    def test_no_match_returns_empty_list(self, mock_graph: Path) -> None:
        result = graph_query("nonexistent-person", root=mock_graph)
        assert result["total_entities"] == 0
        assert result["entities"] == []

    def test_respects_max_results(self, mock_graph: Path) -> None:
        result = graph_query("", max_results=1, root=mock_graph)
        # Empty query matches all entities, but limited to 1
        assert len(result["entities"]) <= 1


# ---------------------------------------------------------------------------
# TESTS: agent_lookup
# ---------------------------------------------------------------------------
class TestAgentLookup:
    def test_returns_error_for_nonexistent(self, mock_agents: Path) -> None:
        result = agent_lookup("nonexistent-agent", root=mock_agents)
        assert "error" in result

    def test_finds_external_agent(self, mock_agents: Path) -> None:
        result = agent_lookup("alex-hormozi", root=mock_agents)
        assert result["name"] == "alex-hormozi"
        assert result["category"] == "external"
        assert result["completeness"] == "4/4"
        assert result["files"]["AGENT.md"] is True

    def test_finds_nested_cargo_agent(self, mock_agents: Path) -> None:
        result = agent_lookup("cfo", root=mock_agents)
        assert result["name"] == "cfo"
        assert result["category"] == "cargo"
        assert result["files"]["AGENT.md"] is True
        assert result["files"]["SOUL.md"] is True
        assert result["files"]["MEMORY.md"] is False  # not created in fixture

    def test_returns_summary_from_agent_md(self, mock_agents: Path) -> None:
        result = agent_lookup("alex-hormozi", root=mock_agents)
        assert "offers" in result["summary"].lower() or "sales" in result["summary"].lower()

    def test_no_agents_dir(self, tmp_path: Path) -> None:
        result = agent_lookup("anything", root=tmp_path)
        assert "error" in result


# ---------------------------------------------------------------------------
# TESTS: dossier_search
# ---------------------------------------------------------------------------
class TestDossierSearch:
    def test_returns_empty_for_no_match(self, mock_dossiers: Path) -> None:
        result = dossier_search("nonexistent-topic", root=mock_dossiers)
        assert result["total"] == 0
        assert result["results"] == []

    def test_finds_dossier_by_person(self, mock_dossiers: Path) -> None:
        result = dossier_search("hormozi", root=mock_dossiers)
        assert result["total"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "DOSSIER-ALEX-HORMOZI" in names

    def test_finds_dossier_by_theme(self, mock_dossiers: Path) -> None:
        result = dossier_search("objection", root=mock_dossiers)
        assert result["total"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "DOSSIER-OBJECTION-HANDLING" in names

    def test_includes_preview(self, mock_dossiers: Path) -> None:
        result = dossier_search("pricing", root=mock_dossiers)
        assert result["total"] >= 1
        assert "Premium pricing" in result["results"][0]["preview"]

    def test_respects_max_results(self, mock_dossiers: Path) -> None:
        result = dossier_search("dossier", max_results=1, root=mock_dossiers)
        assert len(result["results"]) <= 1

    def test_no_dossier_dirs(self, tmp_path: Path) -> None:
        result = dossier_search("anything", root=tmp_path)
        assert result["total"] == 0


# ---------------------------------------------------------------------------
# TESTS: pipeline_status
# ---------------------------------------------------------------------------
class TestPipelineStatus:
    def test_returns_unknown_when_no_state(self, tmp_path: Path) -> None:
        result = pipeline_status(root=tmp_path)
        assert result["status"] == "unknown"
        assert "error" in result

    def test_returns_state_from_file(self, mock_mission_state: Path) -> None:
        result = pipeline_status(root=mock_mission_state)
        assert result["status"] == "active"
        assert result["current_state"]["phase"] == 4
        assert result["current_state"]["percent_complete"] == 37.5
        assert result["session"]["is_active"] is True
        assert "Cole Gordon" in result["next_action"]["description"]

    def test_handles_corrupt_json(self, tmp_path: Path) -> None:
        mc = tmp_path / ".claude" / "mission-control"
        mc.mkdir(parents=True)
        (mc / "MISSION-STATE.json").write_text("{broken json", encoding="utf-8")
        result = pipeline_status(root=tmp_path)
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# TESTS: quality_report
# ---------------------------------------------------------------------------
class TestQualityReport:
    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        result = quality_report(root=tmp_path)
        assert result["total"] == 0
        assert result["scores"] == []
        assert "No quality scores" in result.get("message", "")

    def test_returns_recent_scores(self, mock_quality_scores: Path) -> None:
        result = quality_report(root=mock_quality_scores)
        assert result["total"] == 5
        assert result["showing"] == 5
        assert result["average_score"] > 0

    def test_filters_by_item_type(self, mock_quality_scores: Path) -> None:
        result = quality_report(item_type="batch", root=mock_quality_scores)
        assert result["filter"] == "batch"
        assert result["total"] == 3
        assert all(s["item_type"] == "batch" for s in result["scores"])

    def test_respects_limit(self, mock_quality_scores: Path) -> None:
        result = quality_report(limit=2, root=mock_quality_scores)
        assert result["showing"] == 2
        assert result["total"] == 5  # total is still 5, just showing 2

    def test_handles_empty_lines(self, tmp_path: Path) -> None:
        data_dir = tmp_path / ".data"
        data_dir.mkdir(parents=True)
        content = '{"item_type":"batch","total":80}\n\n{"item_type":"batch","total":70}\n'
        (data_dir / "quality_scores.jsonl").write_text(content, encoding="utf-8")
        result = quality_report(root=tmp_path)
        assert result["total"] == 2

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        data_dir = tmp_path / ".data"
        data_dir.mkdir(parents=True)
        content = '{"item_type":"batch","total":80}\nNOT JSON\n{"item_type":"agent","total":90}\n'
        (data_dir / "quality_scores.jsonl").write_text(content, encoding="utf-8")
        result = quality_report(root=tmp_path)
        assert result["total"] == 2
