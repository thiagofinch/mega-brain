"""Conclave Service -- Multi-agent debate orchestration.

Provides programmatic access to the Mega Brain Conclave system.
Agents debate a topic from their unique perspectives, then a
synthesis is produced combining their viewpoints.

Usage::

    service = ConclaveService()
    result = service.debate(
        "How should we structure sales compensation?",
        agents=["alex-hormozi", "cole-gordon", "jeremy-miner"],
    )
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class AgentPosition:
    """An agent's position in a debate."""

    agent_id: str
    agent_name: str
    category: str
    position: str  # The agent's stance/argument
    key_points: list[str] = field(default_factory=list)
    confidence: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    sources_cited: list[str] = field(default_factory=list)


@dataclass
class DebateResult:
    """Result of a Conclave debate."""

    topic: str
    agents: list[str]
    positions: list[AgentPosition]
    synthesis: str
    consensus_points: list[str] = field(default_factory=list)
    disagreement_points: list[str] = field(default_factory=list)
    recommendation: str = ""
    timestamp: str = ""
    debate_id: str = ""

    def to_dict(self) -> dict:
        """Serialize the debate result to a plain dict."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the debate result to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

# Valid confidence levels for agent positions.
VALID_CONFIDENCE_LEVELS = frozenset({"HIGH", "MEDIUM", "LOW"})


class ConclaveService:
    """Orchestrates multi-agent debates.

    Each agent's perspective is loaded from their SOUL.md and MEMORY.md
    to ensure responses reflect their actual knowledge and worldview.
    """

    # Agent categories that can participate in debates.
    _DEBATABLE_CATEGORIES = ("external", "cargo")

    # Maximum character slice loaded from each agent file.
    _SOUL_CHAR_LIMIT = 3000
    _MEMORY_CHAR_LIMIT = 2000

    def __init__(self, agents_dir: str | Path | None = None) -> None:
        if agents_dir is None:
            # Resolve relative to this file: core/api/conclave_service.py -> ../../agents
            agents_dir = Path(__file__).resolve().parent.parent.parent / "agents"
        self._agents_dir = Path(agents_dir)
        self._debates_log = (
            Path(__file__).resolve().parent.parent.parent
            / ".data"
            / "conclave_debates.jsonl"
        )

    # -- Public API ---------------------------------------------------------

    def list_debatable_agents(self) -> list[dict]:
        """List agents that can participate in debates.

        An agent needs at least ``SOUL.md`` to participate (defines their
        perspective).
        """
        agents: list[dict] = []

        for cat in self._DEBATABLE_CATEGORIES:
            cat_dir = self._agents_dir / cat
            if not cat_dir.exists():
                continue
            for soul_file in cat_dir.rglob("SOUL.md"):
                agent_dir = soul_file.parent
                agents.append(
                    {
                        "id": agent_dir.name,
                        "category": cat,
                        "has_soul": True,
                        "has_memory": (agent_dir / "MEMORY.md").exists(),
                        "has_dna": (agent_dir / "DNA-CONFIG.yaml").exists(),
                    }
                )

        return agents

    def load_agent_context(self, agent_id: str) -> dict | None:
        """Load an agent's context for debate participation.

        Returns ``None`` when the agent cannot be found.
        """
        search_cats = ("external", "cargo", "system")

        for cat in search_cats:
            cat_dir = self._agents_dir / cat
            if not cat_dir.exists():
                continue

            for soul_file in cat_dir.rglob("SOUL.md"):
                if soul_file.parent.name == agent_id:
                    agent_dir = soul_file.parent
                    context: dict = {
                        "id": agent_id,
                        "category": cat,
                    }

                    # SOUL.md -- identity and voice
                    context["soul"] = soul_file.read_text(encoding="utf-8")[
                        : self._SOUL_CHAR_LIMIT
                    ]

                    # MEMORY.md -- experience (optional)
                    memory_file = agent_dir / "MEMORY.md"
                    if memory_file.exists():
                        context["memory"] = memory_file.read_text(
                            encoding="utf-8"
                        )[: self._MEMORY_CHAR_LIMIT]

                    return context

        return None

    def create_debate_prompt(
        self, topic: str, agent_contexts: list[dict]
    ) -> str:
        """Create the debate prompt template.

        This generates the prompt that would be sent to an LLM to simulate
        the debate.  In production, this would be forwarded to Claude/GPT.
        For now, it returns the structured prompt string.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        prompt_parts = [
            f"# Conclave Debate: {topic}\n",
            f"## Date: {now}\n",
            f"## Participants: {len(agent_contexts)} agents\n",
            "---\n",
        ]

        for ctx in agent_contexts:
            prompt_parts.append(f"### Agent: {ctx['id']} ({ctx['category']})")
            soul_excerpt = ctx.get("soul", "N/A")[:500]
            prompt_parts.append(f"**Soul (identity):**\n{soul_excerpt}\n")
            if ctx.get("memory"):
                memory_excerpt = ctx["memory"][:500]
                prompt_parts.append(
                    f"**Memory (experience):**\n{memory_excerpt}\n"
                )
            prompt_parts.append("---\n")

        prompt_parts.append(f"\n## Topic for Debate\n\n{topic}\n")
        prompt_parts.append("\n## Instructions\n")
        prompt_parts.append(
            "Each agent should provide their position based on "
            "their SOUL and MEMORY."
        )
        prompt_parts.append(
            "Then synthesize consensus and disagreements."
        )

        return "\n".join(prompt_parts)

    def debate(
        self,
        topic: str,
        agents: list[str] | None = None,
        max_agents: int = 3,
    ) -> DebateResult:
        """Run a Conclave debate on a topic.

        Args:
            topic: The question or topic to debate.
            agents: Specific agent IDs to include.  If ``None``,
                auto-selects from available agents.
            max_agents: Maximum number of agents (default 3).

        Returns:
            :class:`DebateResult` with positions and synthesis.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        debate_id = (
            f"debate-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        )

        # Resolve which agents to include
        if agents is None:
            available = self.list_debatable_agents()
            agents = [a["id"] for a in available[:max_agents]]

        # Load each agent's context
        contexts: list[dict] = []
        for agent_id in agents[:max_agents]:
            ctx = self.load_agent_context(agent_id)
            if ctx:
                contexts.append(ctx)

        if not contexts:
            return DebateResult(
                topic=topic,
                agents=agents,
                positions=[],
                synthesis="No agents available for debate.",
                timestamp=now_iso,
                debate_id=debate_id,
            )

        # Generate the structured debate prompt (for LLM consumption)
        prompt = self.create_debate_prompt(topic, contexts)

        # Create placeholder positions (in production these come from the LLM)
        positions = [
            AgentPosition(
                agent_id=ctx["id"],
                agent_name=ctx["id"],
                category=ctx["category"],
                position=(
                    f"[Position pending -- submit prompt to LLM for "
                    f"{ctx['id']}'s perspective on: {topic}]"
                ),
                confidence="MEDIUM",
            )
            for ctx in contexts
        ]

        result = DebateResult(
            topic=topic,
            agents=[c["id"] for c in contexts],
            positions=positions,
            synthesis=(
                f"[Synthesis pending -- {len(contexts)} agents loaded, "
                f"prompt generated ({len(prompt)} chars)]"
            ),
            recommendation=(
                "Submit the generated prompt to an LLM "
                "for full debate simulation."
            ),
            timestamp=now_iso,
            debate_id=debate_id,
        )

        # Persist an audit entry
        self._log_debate(result, prompt)

        return result

    # -- Private helpers ----------------------------------------------------

    def _log_debate(self, result: DebateResult, prompt: str) -> None:
        """Append a debate entry to the JSONL audit log."""
        self._debates_log.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "debate_id": result.debate_id,
            "topic": result.topic,
            "agents": result.agents,
            "agent_count": len(result.positions),
            "prompt_length": len(prompt),
            "timestamp": result.timestamp,
        }
        with open(self._debates_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
