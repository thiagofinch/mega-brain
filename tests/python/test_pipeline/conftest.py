"""
Shared fixtures for pipeline test modules.
==========================================
All tests are OFFLINE -- no real API calls, no real filesystem outside tmp_path.
Every fixture isolates module-level globals and paths via monkeypatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Sample text fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_meeting_transcript() -> str:
    """A realistic meeting transcript with company keywords and decisions."""
    return (
        "[MEET-0050] Bilhon Weekly -- 2026-03-12\n"
        "Participants: thiago@bilhon.com, joao@bilhon.com, maria@bilhon.com\n"
        "Organizer: thiago@bilhon.com\n\n"
        "Thiago: Bom, pessoal, vamos revisar os KPIs da semana.\n"
        "Joao: O MRR subiu 12% -- estamos em R$180k agora.\n"
        "Maria: Churn caiu para 4.2%, abaixo do target de 5%.\n"
        "Thiago: Otimo. Decidimos que vamos contratar mais um SDR.\n"
        "Action items:\n"
        "- Joao: publicar vaga no LinkedIn ate sexta\n"
        "- Maria: revisar scorecard do SDR\n"
        "- Thiago: aprovar budget com financeiro\n"
        "Proximos passos: revisao na weekly de segunda.\n"
    )


@pytest.fixture()
def sample_course_transcript() -> str:
    """A realistic expert course transcript with teaching patterns."""
    return (
        "Alex Hormozi - Ultimate Sales Training Module 3\n\n"
        "Let me teach you the framework I use to close high-ticket deals.\n"
        "Step one: qualify the lead using the BANT methodology.\n"
        "Step two: build rapport by mirroring their language.\n"
        "The way I do it is simple -- I ask three questions:\n"
        "1. What's your current revenue?\n"
        "2. Where do you want to be in 12 months?\n"
        "3. What's stopping you from getting there?\n\n"
        "Here's what separates the top 1% of closers from everyone else.\n"
        "It's not about the playbook. It's about the offer structure.\n"
        "A hundred million dollar offer has three components: the vehicle,\n"
        "the dream outcome, and the risk reversal.\n"
    )


@pytest.fixture()
def sample_personal_note() -> str:
    """A realistic personal note with first-person reflections."""
    return (
        "Diario pessoal -- 2026-03-10\n\n"
        "Eu acredito que estamos no caminho certo.\n"
        "Minha visao para a empresa mudou depois da conversa com o Ricardo.\n"
        "Eu decidi que vamos pivotar o modelo de pricing.\n"
        "Minha estrategia agora e focar em unit economics antes de escalar.\n"
        "Reflexao: preciso separar melhor o tempo entre operacao e estrategia.\n"
    )


# ---------------------------------------------------------------------------
# Temporary inbox fixture (creates 3-bucket structure)
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_inbox(tmp_path: Path) -> dict[str, Path]:
    """Create a temporary 3-bucket inbox structure.

    Returns dict with keys: 'external', 'business', 'personal', 'logs',
    'mission_control', 'root', 'workspace'.
    """
    root = tmp_path / "mega-brain"
    root.mkdir()

    external_inbox = root / "knowledge" / "external" / "inbox"
    business_inbox = root / "knowledge" / "business" / "inbox"
    personal_inbox = root / "knowledge" / "personal" / "inbox"
    workspace_inbox = root / "workspace" / "inbox"
    logs = root / "logs"
    mission_control = root / ".claude" / "mission-control"
    dna_persons = root / "knowledge" / "external" / "dna" / "persons"
    workspace_team = root / "workspace" / "team"

    for d in [
        external_inbox,
        business_inbox,
        personal_inbox,
        workspace_inbox,
        logs,
        mission_control,
        dna_persons,
        workspace_team,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "external": external_inbox,
        "business": business_inbox,
        "personal": personal_inbox,
        "workspace": workspace_inbox,
        "logs": logs,
        "mission_control": mission_control,
        "dna_persons": dna_persons,
        "workspace_team": workspace_team,
    }


# ---------------------------------------------------------------------------
# Mock LLM response fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm_response() -> dict:
    """A generic mock LLM response for tests that need one."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a mock LLM response for testing purposes."
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }


# ---------------------------------------------------------------------------
# Fake ScopeDecision (for smart_router tests)
# ---------------------------------------------------------------------------


@dataclass
class FakeScopeDecision:
    """Lightweight stand-in for ScopeDecision to avoid importing the classifier."""

    primary_bucket: str = "external"
    cascade_buckets: list[str] = field(default_factory=list)
    confidence: float = 0.90
    reasons: list[str] = field(default_factory=lambda: ["test-reason"])
    source_type: str = "course"
    detected_entities: list[str] = field(default_factory=list)
    signals: dict[str, object] = field(default_factory=dict)


@pytest.fixture()
def fake_decision() -> FakeScopeDecision:
    """Return a high-confidence external ScopeDecision."""
    return FakeScopeDecision()
