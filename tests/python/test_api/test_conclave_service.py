"""Tests for core.api.conclave_service.

All tests use tmp_path fixtures to create mock agent directories --
no real agents or LLM calls are involved.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.api.conclave_service import (
    AgentPosition,
    ConclaveService,
    DebateResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def agents_root(tmp_path: Path) -> Path:
    """Create a minimal agent tree under tmp_path."""
    external = tmp_path / "external"
    external.mkdir()

    # Agent with SOUL + MEMORY
    hormozi = external / "alex-hormozi"
    hormozi.mkdir()
    (hormozi / "SOUL.md").write_text(
        "# Alex Hormozi\nI believe in volume. Offer creation is everything."
    )
    (hormozi / "MEMORY.md").write_text(
        "# Memory\n- LTV/CAC must be > 3x.\n- Grand Slam Offers."
    )
    (hormozi / "DNA-CONFIG.yaml").write_text("domains:\n  - sales\n")

    # Agent with SOUL only
    cole = external / "cole-gordon"
    cole.mkdir()
    (cole / "SOUL.md").write_text(
        "# Cole Gordon\nClosing is a process, not a trick."
    )

    # Cargo agent (nested)
    cargo = tmp_path / "cargo"
    sales = cargo / "sales"
    closer = sales / "closer"
    closer.mkdir(parents=True)
    (closer / "SOUL.md").write_text("# Closer\nI close deals.")
    (closer / "MEMORY.md").write_text("# Memory\nSold 500 deals.")

    return tmp_path


@pytest.fixture()
def empty_agents(tmp_path: Path) -> Path:
    """Create an agents directory with no valid agents."""
    (tmp_path / "external").mkdir()
    (tmp_path / "cargo").mkdir()
    return tmp_path


@pytest.fixture()
def service(agents_root: Path) -> ConclaveService:
    """ConclaveService wired to the fixture agents tree."""
    return ConclaveService(agents_dir=agents_root)


@pytest.fixture()
def empty_service(empty_agents: Path) -> ConclaveService:
    """ConclaveService with no available agents."""
    return ConclaveService(agents_dir=empty_agents)


# ---------------------------------------------------------------------------
# ConclaveService.__init__
# ---------------------------------------------------------------------------


class TestConclaveServiceInit:
    """Initialization with custom agents_dir."""

    def test_custom_agents_dir(self, tmp_path: Path) -> None:
        svc = ConclaveService(agents_dir=tmp_path / "my-agents")
        assert svc._agents_dir == tmp_path / "my-agents"

    def test_default_agents_dir_resolves(self) -> None:
        svc = ConclaveService()
        assert svc._agents_dir.name == "agents"
        assert svc._agents_dir.is_absolute()


# ---------------------------------------------------------------------------
# list_debatable_agents
# ---------------------------------------------------------------------------


class TestListDebatableAgents:
    """Tests for ConclaveService.list_debatable_agents."""

    def test_finds_external_agents(self, service: ConclaveService) -> None:
        agents = service.list_debatable_agents()
        ids = {a["id"] for a in agents}
        assert "alex-hormozi" in ids
        assert "cole-gordon" in ids

    def test_finds_cargo_agents(self, service: ConclaveService) -> None:
        agents = service.list_debatable_agents()
        ids = {a["id"] for a in agents}
        assert "closer" in ids

    def test_has_soul_always_true(self, service: ConclaveService) -> None:
        agents = service.list_debatable_agents()
        assert all(a["has_soul"] for a in agents)

    def test_has_memory_flag(self, service: ConclaveService) -> None:
        agents = service.list_debatable_agents()
        by_id = {a["id"]: a for a in agents}
        assert by_id["alex-hormozi"]["has_memory"] is True
        assert by_id["cole-gordon"]["has_memory"] is False

    def test_has_dna_flag(self, service: ConclaveService) -> None:
        agents = service.list_debatable_agents()
        by_id = {a["id"]: a for a in agents}
        assert by_id["alex-hormozi"]["has_dna"] is True
        assert by_id["cole-gordon"]["has_dna"] is False

    def test_empty_agents_returns_empty(
        self, empty_service: ConclaveService
    ) -> None:
        assert empty_service.list_debatable_agents() == []


# ---------------------------------------------------------------------------
# load_agent_context
# ---------------------------------------------------------------------------


class TestLoadAgentContext:
    """Tests for ConclaveService.load_agent_context."""

    def test_returns_none_for_nonexistent(
        self, service: ConclaveService
    ) -> None:
        assert service.load_agent_context("does-not-exist") is None

    def test_loads_soul_content(self, service: ConclaveService) -> None:
        ctx = service.load_agent_context("alex-hormozi")
        assert ctx is not None
        assert "volume" in ctx["soul"].lower()

    def test_includes_memory_when_present(
        self, service: ConclaveService
    ) -> None:
        ctx = service.load_agent_context("alex-hormozi")
        assert ctx is not None
        assert "memory" in ctx
        assert "LTV/CAC" in ctx["memory"]

    def test_excludes_memory_when_absent(
        self, service: ConclaveService
    ) -> None:
        ctx = service.load_agent_context("cole-gordon")
        assert ctx is not None
        assert "memory" not in ctx

    def test_context_has_id_and_category(
        self, service: ConclaveService
    ) -> None:
        ctx = service.load_agent_context("alex-hormozi")
        assert ctx is not None
        assert ctx["id"] == "alex-hormozi"
        assert ctx["category"] == "external"


# ---------------------------------------------------------------------------
# create_debate_prompt
# ---------------------------------------------------------------------------


class TestCreateDebatePrompt:
    """Tests for ConclaveService.create_debate_prompt."""

    def test_includes_topic(self, service: ConclaveService) -> None:
        prompt = service.create_debate_prompt(
            "Sales comp", [{"id": "a", "category": "ext", "soul": "X"}]
        )
        assert "Sales comp" in prompt

    def test_includes_all_agents(self, service: ConclaveService) -> None:
        contexts = [
            {"id": "agent-a", "category": "ext", "soul": "Soul A"},
            {"id": "agent-b", "category": "cargo", "soul": "Soul B"},
        ]
        prompt = service.create_debate_prompt("Topic", contexts)
        assert "agent-a" in prompt
        assert "agent-b" in prompt

    def test_includes_memory_when_present(
        self, service: ConclaveService
    ) -> None:
        contexts = [
            {
                "id": "x",
                "category": "ext",
                "soul": "Soul",
                "memory": "My memory data",
            }
        ]
        prompt = service.create_debate_prompt("Topic", contexts)
        assert "My memory data" in prompt

    def test_excludes_memory_when_absent(
        self, service: ConclaveService
    ) -> None:
        contexts = [{"id": "x", "category": "ext", "soul": "Soul"}]
        prompt = service.create_debate_prompt("Topic", contexts)
        assert "Memory (experience)" not in prompt


# ---------------------------------------------------------------------------
# debate
# ---------------------------------------------------------------------------


class TestDebate:
    """Tests for ConclaveService.debate."""

    def test_no_agents_returns_empty_result(
        self, empty_service: ConclaveService
    ) -> None:
        result = empty_service.debate("Some topic")
        assert result.positions == []
        assert "No agents available" in result.synthesis

    def test_with_valid_agents_returns_positions(
        self, service: ConclaveService
    ) -> None:
        result = service.debate(
            "Compensation structure",
            agents=["alex-hormozi", "cole-gordon"],
        )
        assert len(result.positions) == 2
        ids = {p.agent_id for p in result.positions}
        assert ids == {"alex-hormozi", "cole-gordon"}

    def test_debate_has_timestamp(self, service: ConclaveService) -> None:
        result = service.debate("Topic", agents=["alex-hormozi"])
        assert result.timestamp != ""
        assert "T" in result.timestamp  # ISO format

    def test_debate_has_debate_id(self, service: ConclaveService) -> None:
        result = service.debate("Topic", agents=["alex-hormozi"])
        assert result.debate_id.startswith("debate-")

    def test_debate_logs_to_jsonl(
        self, service: ConclaveService, tmp_path: Path
    ) -> None:
        # Point the log to a temporary location
        service._debates_log = tmp_path / "log" / "debates.jsonl"
        result = service.debate("Topic", agents=["alex-hormozi"])

        assert service._debates_log.exists()
        line = service._debates_log.read_text(encoding="utf-8").strip()
        entry = json.loads(line)
        assert entry["debate_id"] == result.debate_id
        assert entry["topic"] == "Topic"

    def test_max_agents_limits_participants(
        self, service: ConclaveService
    ) -> None:
        result = service.debate(
            "Topic",
            agents=["alex-hormozi", "cole-gordon", "closer"],
            max_agents=2,
        )
        assert len(result.positions) == 2

    def test_skips_nonexistent_agents(
        self, service: ConclaveService
    ) -> None:
        result = service.debate(
            "Topic", agents=["alex-hormozi", "ghost-agent"]
        )
        assert len(result.positions) == 1
        assert result.agents == ["alex-hormozi"]


# ---------------------------------------------------------------------------
# DebateResult serialization
# ---------------------------------------------------------------------------


class TestDebateResultSerialization:
    """Tests for DebateResult.to_dict / to_json."""

    def _make_result(self) -> DebateResult:
        return DebateResult(
            topic="Hiring strategy",
            agents=["ah", "cg"],
            positions=[
                AgentPosition(
                    agent_id="ah",
                    agent_name="Alex Hormozi",
                    category="external",
                    position="Hire slow, fire fast.",
                    key_points=["Culture fit first"],
                    confidence="HIGH",
                    sources_cited=["HEUR-AH-001"],
                )
            ],
            synthesis="Both agree on rigor.",
            consensus_points=["Rigor in hiring"],
            disagreement_points=[],
            recommendation="Implement structured interviews.",
            timestamp="2026-03-14T00:00:00+00:00",
            debate_id="debate-20260314000000",
        )

    def test_to_dict_returns_dict(self) -> None:
        d = self._make_result().to_dict()
        assert isinstance(d, dict)
        assert d["topic"] == "Hiring strategy"
        assert d["agents"] == ["ah", "cg"]

    def test_to_dict_has_positions(self) -> None:
        d = self._make_result().to_dict()
        assert len(d["positions"]) == 1
        pos = d["positions"][0]
        assert pos["agent_id"] == "ah"
        assert pos["confidence"] == "HIGH"

    def test_to_json_is_valid_json(self) -> None:
        j = self._make_result().to_json()
        parsed = json.loads(j)
        assert parsed["debate_id"] == "debate-20260314000000"

    def test_to_json_no_ascii_escape(self) -> None:
        result = DebateResult(
            topic="Compensacao em Real",
            agents=[],
            positions=[],
            synthesis="Consenso aqui.",
            timestamp="",
            debate_id="d1",
        )
        j = result.to_json()
        # Accented characters should NOT be escaped
        assert "Compensacao" in j
        assert "\\u" not in j


# ---------------------------------------------------------------------------
# AgentPosition dataclass
# ---------------------------------------------------------------------------


class TestAgentPosition:
    """Tests for AgentPosition field defaults."""

    def test_default_confidence(self) -> None:
        pos = AgentPosition(
            agent_id="a",
            agent_name="A",
            category="ext",
            position="My position",
        )
        assert pos.confidence == "MEDIUM"

    def test_default_lists_empty(self) -> None:
        pos = AgentPosition(
            agent_id="a",
            agent_name="A",
            category="ext",
            position="Pos",
        )
        assert pos.key_points == []
        assert pos.sources_cited == []

    def test_all_fields_set(self) -> None:
        pos = AgentPosition(
            agent_id="cg",
            agent_name="Cole Gordon",
            category="external",
            position="Close with conviction.",
            key_points=["Frame control", "Tonality"],
            confidence="HIGH",
            sources_cited=["MET-CG-005"],
        )
        assert pos.agent_id == "cg"
        assert pos.key_points == ["Frame control", "Tonality"]
        assert pos.sources_cited == ["MET-CG-005"]
