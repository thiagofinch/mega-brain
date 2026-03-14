"""Tests for core.api.agent_server helper functions.

All tests use tmp_path fixtures to create mock agent directories -- no real
FastAPI server is started.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from core.api.agent_server import (
    AGENT_FILES,
    _discover_agents,
    _find_agent_dir,
    _get_agent_content,
    _is_agent_dir,
    _parse_agent,
    create_app,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def full_agent(tmp_path: Path) -> Path:
    """Create a complete agent with all 4 canonical files."""
    agent = tmp_path / "agents" / "external" / "test-expert"
    agent.mkdir(parents=True)
    (agent / "AGENT.md").write_text(
        "# Test Expert\n\nThis is a complete test agent for unit testing purposes."
    )
    (agent / "SOUL.md").write_text("# Soul\nI am a test expert agent.")
    (agent / "MEMORY.md").write_text("# Memory\nNo memories yet.")
    (agent / "DNA-CONFIG.yaml").write_text(
        "domains:\n  - testing\n  - qa\ndna_sources:\n  - test-source-1\n"
    )
    return tmp_path


@pytest.fixture()
def partial_agent(tmp_path: Path) -> Path:
    """Create an agent with only AGENT.md (25 % completeness)."""
    agent = tmp_path / "agents" / "external" / "incomplete-agent"
    agent.mkdir(parents=True)
    (agent / "AGENT.md").write_text(
        "# Incomplete Agent\n\nThis agent only has AGENT.md present."
    )
    return tmp_path


@pytest.fixture()
def nested_agent(tmp_path: Path) -> Path:
    """Create a cargo-style nested agent (cargo/sales/closer)."""
    agent = tmp_path / "agents" / "cargo" / "sales" / "closer"
    agent.mkdir(parents=True)
    (agent / "AGENT.md").write_text(
        "# Closer Agent\n\nHigh-ticket sales closing specialist."
    )
    (agent / "SOUL.md").write_text("# Soul\nI close deals.")
    return tmp_path


@pytest.fixture()
def multi_agent(tmp_path: Path) -> Path:
    """Create multiple agents across categories for list tests."""
    # External agent
    ext = tmp_path / "agents" / "external" / "hormozi"
    ext.mkdir(parents=True)
    (ext / "AGENT.md").write_text("# Alex Hormozi\n\nBusiness scaling expert.")
    (ext / "SOUL.md").write_text("# Soul\nI scale businesses.")
    (ext / "MEMORY.md").write_text("# Memory\nKey insights here.")
    (ext / "DNA-CONFIG.yaml").write_text("domains: [sales, offers]\ndna_sources: [ah-1]")

    # Cargo nested agent
    cargo = tmp_path / "agents" / "cargo" / "c-level" / "cfo"
    cargo.mkdir(parents=True)
    (cargo / "AGENT.md").write_text("# CFO Agent\n\nFinancial oversight and strategy.")
    (cargo / "SOUL.md").write_text("# Soul\nI protect the numbers.")

    # System nested agent
    sys_agent = tmp_path / "agents" / "system" / "knowledge-ops" / "atlas"
    sys_agent.mkdir(parents=True)
    (sys_agent / "AGENT.md").write_text("# Atlas\n\nScope classifier for knowledge pipeline.")

    return tmp_path


# ---------------------------------------------------------------------------
# _is_agent_dir
# ---------------------------------------------------------------------------


class TestIsAgentDir:
    def test_true_for_dir_with_agent_md(self, full_agent: Path) -> None:
        agent_dir = full_agent / "agents" / "external" / "test-expert"
        assert _is_agent_dir(agent_dir) is True

    def test_true_for_dir_with_partial_files(self, partial_agent: Path) -> None:
        agent_dir = partial_agent / "agents" / "external" / "incomplete-agent"
        assert _is_agent_dir(agent_dir) is True

    def test_false_for_nonexistent(self, tmp_path: Path) -> None:
        assert _is_agent_dir(tmp_path / "nope") is False

    def test_false_for_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert _is_agent_dir(empty) is False

    def test_false_for_file(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("hello")
        assert _is_agent_dir(f) is False


# ---------------------------------------------------------------------------
# _parse_agent
# ---------------------------------------------------------------------------


class TestParseAgent:
    def test_full_agent_returns_complete_dict(self, full_agent: Path) -> None:
        agent_dir = full_agent / "agents" / "external" / "test-expert"
        # Monkey-patch PROJECT_ROOT and AGENTS_DIR for the test
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            result = _parse_agent(agent_dir)

        assert result is not None
        assert result["id"] == "test-expert"
        assert result["category"] == "external"
        assert result["completeness"] == 100.0
        assert all(result["files"].values())

    def test_partial_agent_25_percent(self, partial_agent: Path) -> None:
        agent_dir = partial_agent / "agents" / "external" / "incomplete-agent"
        with patch("core.api.agent_server.PROJECT_ROOT", partial_agent), \
             patch("core.api.agent_server.AGENTS_DIR", partial_agent / "agents"):
            result = _parse_agent(agent_dir)

        assert result is not None
        assert result["completeness"] == 25.0
        assert result["files"]["AGENT.md"] is True
        assert result["files"]["SOUL.md"] is False

    def test_nonexistent_returns_none(self, tmp_path: Path) -> None:
        result = _parse_agent(tmp_path / "nope")
        assert result is None

    def test_summary_extracted(self, full_agent: Path) -> None:
        agent_dir = full_agent / "agents" / "external" / "test-expert"
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            result = _parse_agent(agent_dir)

        assert result is not None
        assert "summary" in result
        assert "complete test agent" in result["summary"]

    def test_dna_domains_extracted(self, full_agent: Path) -> None:
        agent_dir = full_agent / "agents" / "external" / "test-expert"
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            result = _parse_agent(agent_dir)

        assert result is not None
        assert result.get("domains") == ["testing", "qa"]
        assert result.get("dna_sources") == ["test-source-1"]

    def test_empty_dir_returns_none(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        result = _parse_agent(empty)
        assert result is None

    def test_nested_agent_has_subcategory(self, nested_agent: Path) -> None:
        agent_dir = nested_agent / "agents" / "cargo" / "sales" / "closer"
        with patch("core.api.agent_server.PROJECT_ROOT", nested_agent), \
             patch("core.api.agent_server.AGENTS_DIR", nested_agent / "agents"):
            result = _parse_agent(agent_dir)

        assert result is not None
        assert result["category"] == "cargo"
        assert result["subcategory"] == "sales"

    def test_invalid_yaml_handled_gracefully(self, tmp_path: Path) -> None:
        agent_dir = tmp_path / "agents" / "external" / "bad-yaml"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text("# Bad YAML Agent\n\nThis agent has broken YAML.")
        (agent_dir / "DNA-CONFIG.yaml").write_text("{{invalid: yaml: [broken")

        with patch("core.api.agent_server.PROJECT_ROOT", tmp_path), \
             patch("core.api.agent_server.AGENTS_DIR", tmp_path / "agents"):
            result = _parse_agent(agent_dir)

        assert result is not None
        assert result["id"] == "bad-yaml"
        # Should not have domains/dna_sources since YAML was invalid
        assert "domains" not in result


# ---------------------------------------------------------------------------
# Completeness calculation
# ---------------------------------------------------------------------------


class TestCompleteness:
    def test_0_percent(self, tmp_path: Path) -> None:
        """A directory with none of the canonical files is not an agent."""
        d = tmp_path / "agents" / "external" / "ghost"
        d.mkdir(parents=True)
        result = _parse_agent(d)
        assert result is None  # Not recognized as an agent at all

    def test_25_percent(self, partial_agent: Path) -> None:
        agent_dir = partial_agent / "agents" / "external" / "incomplete-agent"
        with patch("core.api.agent_server.PROJECT_ROOT", partial_agent), \
             patch("core.api.agent_server.AGENTS_DIR", partial_agent / "agents"):
            result = _parse_agent(agent_dir)
        assert result is not None
        assert result["completeness"] == 25.0

    def test_50_percent(self, nested_agent: Path) -> None:
        agent_dir = nested_agent / "agents" / "cargo" / "sales" / "closer"
        with patch("core.api.agent_server.PROJECT_ROOT", nested_agent), \
             patch("core.api.agent_server.AGENTS_DIR", nested_agent / "agents"):
            result = _parse_agent(agent_dir)
        assert result is not None
        assert result["completeness"] == 50.0

    def test_75_percent(self, tmp_path: Path) -> None:
        agent_dir = tmp_path / "agents" / "external" / "three-files"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text("# Three Files\n\nAgent with three canonical files.")
        (agent_dir / "SOUL.md").write_text("# Soul")
        (agent_dir / "MEMORY.md").write_text("# Memory")

        with patch("core.api.agent_server.PROJECT_ROOT", tmp_path), \
             patch("core.api.agent_server.AGENTS_DIR", tmp_path / "agents"):
            result = _parse_agent(agent_dir)
        assert result is not None
        assert result["completeness"] == 75.0

    def test_100_percent(self, full_agent: Path) -> None:
        agent_dir = full_agent / "agents" / "external" / "test-expert"
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            result = _parse_agent(agent_dir)
        assert result is not None
        assert result["completeness"] == 100.0


# ---------------------------------------------------------------------------
# _discover_agents
# ---------------------------------------------------------------------------


class TestDiscoverAgents:
    def test_discovers_across_categories(self, multi_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", multi_agent), \
             patch("core.api.agent_server.AGENTS_DIR", multi_agent / "agents"):
            agents = _discover_agents(multi_agent)

        assert len(agents) == 3
        ids = {a["id"] for a in agents}
        assert ids == {"hormozi", "cfo", "atlas"}

    def test_empty_agents_dir(self, tmp_path: Path) -> None:
        (tmp_path / "agents").mkdir()
        with patch("core.api.agent_server.PROJECT_ROOT", tmp_path), \
             patch("core.api.agent_server.AGENTS_DIR", tmp_path / "agents"):
            agents = _discover_agents(tmp_path)
        assert agents == []

    def test_skips_underscore_dirs(self, tmp_path: Path) -> None:
        """Directories starting with _ (like _templates) should be skipped."""
        ext = tmp_path / "agents" / "external" / "_example"
        ext.mkdir(parents=True)
        (ext / "AGENT.md").write_text("# Example\n\nShould be skipped.")

        real = tmp_path / "agents" / "external" / "real-agent"
        real.mkdir(parents=True)
        (real / "AGENT.md").write_text("# Real Agent\n\nThis should be discovered.")

        with patch("core.api.agent_server.PROJECT_ROOT", tmp_path), \
             patch("core.api.agent_server.AGENTS_DIR", tmp_path / "agents"):
            agents = _discover_agents(tmp_path)

        assert len(agents) == 1
        assert agents[0]["id"] == "real-agent"


# ---------------------------------------------------------------------------
# _find_agent_dir / _get_agent_content
# ---------------------------------------------------------------------------


class TestFindAndGetContent:
    def test_find_direct_agent(self, full_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            found = _find_agent_dir("test-expert")
        assert found is not None
        assert found.name == "test-expert"

    def test_find_nested_agent(self, nested_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", nested_agent), \
             patch("core.api.agent_server.AGENTS_DIR", nested_agent / "agents"):
            found = _find_agent_dir("closer")
        assert found is not None
        assert found.name == "closer"

    def test_not_found_returns_none(self, full_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            found = _find_agent_dir("nonexistent-agent")
        assert found is None

    def test_get_content_returns_none_for_missing(self, full_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            result = _get_agent_content("does-not-exist")
        assert result is None

    def test_get_content_includes_file_text(self, full_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", full_agent), \
             patch("core.api.agent_server.AGENTS_DIR", full_agent / "agents"):
            result = _get_agent_content("test-expert")

        assert result is not None
        assert "agent_md" in result
        assert "# Test Expert" in result["agent_md"]
        assert "soul_md" in result
        assert "I am a test expert agent" in result["soul_md"]
        assert "memory_md" in result
        assert result["dna_config_raw"] is not None
        assert "testing" in result["dna_config_raw"]

    def test_get_content_missing_files_are_none(self, partial_agent: Path) -> None:
        with patch("core.api.agent_server.PROJECT_ROOT", partial_agent), \
             patch("core.api.agent_server.AGENTS_DIR", partial_agent / "agents"):
            result = _get_agent_content("incomplete-agent")

        assert result is not None
        assert result["agent_md"] is not None  # Exists
        assert result["soul_md"] is None  # Missing
        assert result["memory_md"] is None  # Missing
        assert result["dna_config_raw"] is None  # Missing


# ---------------------------------------------------------------------------
# create_app
# ---------------------------------------------------------------------------


class TestCreateApp:
    def test_creates_fastapi_instance(self) -> None:
        application = create_app()
        assert application is not None
        assert application.title == "Mega Brain Agent API"

    def test_raises_when_fastapi_missing(self) -> None:
        with patch("core.api.agent_server.FastAPI", None):
            with pytest.raises(ImportError, match="fastapi is required"):
                create_app()
