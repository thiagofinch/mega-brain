"""
agent_selector.py -- Deterministic Agent Selector for MCE Pipeline
==================================================================

Maps pipeline steps to agents using an explicit lookup table.  Selection
is ALWAYS by ``agent_id`` -- never by description, name, or fuzzy match.

Architecture
------------
The agent registry is a frozen lookup table derived from config.yaml.
Each agent declares its ``mce_steps``.  The selector inverts this into
a ``step_id -> agent_id`` mapping for O(1) lookup.

Data Flow::

    step_id  --->  STEP_TO_AGENT  --->  agent_id (exact)
                        |
                   agent_id  --->  AGENT_REGISTRY  --->  AgentInfo

Public API
----------
- ``AgentInfo``          -- frozen dataclass with agent metadata
- ``AGENT_REGISTRY``     -- dict[str, AgentInfo] keyed by agent_id
- ``STEP_TO_AGENT``      -- dict[str, str] mapping step_id to agent_id
- ``select_agent()``     -- resolve agent_id for a given step
- ``get_agent_info()``   -- get full AgentInfo by agent_id
- ``list_agents()``      -- list all registered agents
- ``list_steps()``       -- list all steps with their assigned agents

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-1.5
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("mce.agent_selector")


# ---------------------------------------------------------------------------
# AgentInfo dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentInfo:
    """Immutable metadata for a pipeline agent.

    Attributes:
        agent_id:    Unique identifier (kebab-case).
        name:        Human-readable name (e.g. "The Gatekeeper").
        role:        Short role description.
        tier:        Agent tier (1-8 or "conclave").
        mce_steps:   Pipeline steps this agent handles.
        when_to_use: Explicit description of when to select this agent.
        megabrain_type: Executor type (Worker, Agent, Clone).
        human_in_the_loop: Whether human intervention is required.
    """

    agent_id: str
    name: str = ""
    role: str = ""
    tier: int | str = 0
    mce_steps: tuple[str, ...] = ()
    when_to_use: str = ""
    megabrain_type: str = "Agent"
    human_in_the_loop: bool = False


# ---------------------------------------------------------------------------
# AGENT_REGISTRY -- canonical agent definitions
# ---------------------------------------------------------------------------

#: Master registry of all 13 pipeline agents + 3 conclave agents.
#: Derived from config.yaml ``agents[]`` section with ``whenToUse`` added.
#:
#: This is the SINGLE SOURCE OF TRUTH for agent selection at runtime.
#: config.yaml is the source of truth at the project level; this registry
#: is the compiled, in-memory version for the Python pipeline.
AGENT_REGISTRY: dict[str, AgentInfo] = {
    "gate": AgentInfo(
        agent_id="gate",
        name="The Gatekeeper",
        role="Intake classification, routing, and batching",
        tier=1,
        mce_steps=("0", "1", "2"),
        when_to_use=(
            "Use for classifying incoming material (audio, transcript, PDF), "
            "routing to the correct pipeline path, and grouping files into batches."
        ),
        megabrain_type="Worker",
    ),
    "parse": AgentInfo(
        agent_id="parse",
        name="The Parser",
        role="Semantic chunking specialist",
        tier=2,
        mce_steps=("3",),
        when_to_use=(
            "Use for splitting transcripts and documents into semantically coherent "
            "chunks optimized for downstream entity resolution and extraction."
        ),
        megabrain_type="Agent",
    ),
    "canon": AgentInfo(
        agent_id="canon",
        name="The Cartographer",
        role="Entity resolution and canonical mapping",
        tier=2,
        mce_steps=("4",),
        when_to_use=(
            "Use for deduplicating and normalizing entities (people, organizations, "
            "concepts) across chunks into a canonical entity map."
        ),
        megabrain_type="Agent",
    ),
    "dig": AgentInfo(
        agent_id="dig",
        name="The Excavator",
        role="Insight extraction and DNA tag classification (L1-L5)",
        tier=3,
        mce_steps=("5",),
        when_to_use=(
            "Use for extracting DNA layers L1 (filosofias), L2 (modelos mentais), "
            "L3 (heuristicas), L4 (frameworks), L5 (metodologias) from chunks."
        ),
        megabrain_type="Agent",
    ),
    "behav": AgentInfo(
        agent_id="behav",
        name="The Behaviorist",
        role="Behavioral pattern recognition (L6)",
        tier=4,
        mce_steps=("6",),
        when_to_use=(
            "Use for detecting recurring behavioral patterns (L6): decision habits, "
            "communication styles, conflict responses, leadership patterns."
        ),
        megabrain_type="Agent",
    ),
    "psych": AgentInfo(
        agent_id="psych",
        name="The Psychologist",
        role="Identity profiling -- values (L7), obsessions (L9), paradoxes (L10)",
        tier=4,
        mce_steps=("7",),
        when_to_use=(
            "Use for deep identity extraction: L7 (core values and beliefs), "
            "L9 (obsessions and fixations), L10 (internal paradoxes and tensions)."
        ),
        megabrain_type="Agent",
    ),
    "voice": AgentInfo(
        agent_id="voice",
        name="The Linguist",
        role="Voice DNA extraction (L8)",
        tier=4,
        mce_steps=("8",),
        when_to_use=(
            "Use for extracting Voice DNA (L8): speech patterns, vocabulary "
            "fingerprint, rhythm, tone, signature phrases, forbidden words."
        ),
        megabrain_type="Agent",
    ),
    "guard": AgentInfo(
        agent_id="guard",
        name="The Sentinel",
        role="Identity checkpoint -- human validation",
        tier=5,
        mce_steps=("9",),
        when_to_use=(
            "Use at the identity checkpoint (step 9) where human validation is "
            "required before proceeding to compilation. GATE -- blocks pipeline."
        ),
        megabrain_type="Agent",
        human_in_the_loop=True,
    ),
    "scribe": AgentInfo(
        agent_id="scribe",
        name="The Chronicler",
        role="Narrative synthesis -- dossiers and source compilations",
        tier=6,
        mce_steps=("10.1", "10.2"),
        when_to_use=(
            "Use for compiling knowledge dossiers (step 10.1) and source document "
            "compilations (step 10.2) from validated extraction outputs."
        ),
        megabrain_type="Agent",
    ),
    "weave": AgentInfo(
        agent_id="weave",
        name="The Assembler",
        role="DNA YAML assembly -- 10 layers (L1-L10)",
        tier=6,
        mce_steps=("10.3",),
        when_to_use=(
            "Use for assembling the final DNA-CONFIG.yaml by merging all 10 DNA "
            "layers (L1-L10) into the canonical YAML schema."
        ),
        megabrain_type="Agent",
    ),
    "clone": AgentInfo(
        agent_id="clone",
        name="The Architect",
        role="Mind-clone agent generation (Template V3)",
        tier=7,
        mce_steps=("10.4", "10.5"),
        when_to_use=(
            "Use for generating mind-clone agent files (AGENT.md, SOUL.md, MEMORY.md, "
            "DNA-CONFIG.yaml, ACTIVATION.yaml) from compiled DNA data."
        ),
        megabrain_type="Clone",
        human_in_the_loop=True,
    ),
    "index": AgentInfo(
        agent_id="index",
        name="The Librarian",
        role="RAG indexation, graph enrichment, domain contracts, Conclave readiness",
        tier=7,
        mce_steps=("post-pipeline",),
        when_to_use=(
            "Use after the main pipeline completes for RAG vector indexation, "
            "knowledge graph enrichment, domain contract validation, and "
            "preparing Conclave-ready summaries."
        ),
        megabrain_type="Agent",
    ),
    "ops": AgentInfo(
        agent_id="ops",
        name="The Operator",
        role="Finalization, memory enrichment, workspace sync, report",
        tier=8,
        mce_steps=("11", "12"),
        when_to_use=(
            "Use for pipeline finalization (step 11: memory enrichment, workspace "
            "sync) and report generation (step 12: pipeline summary and metrics)."
        ),
        megabrain_type="Worker",
    ),
    # Conclave agents -- deliberation, not pipeline steps
    "critico": AgentInfo(
        agent_id="critico",
        name="Critico",
        role="Methodological critic",
        tier="conclave",
        mce_steps=(),
        when_to_use=(
            "Use in Conclave deliberation when methodological rigor needs evaluation: "
            "scoring quality, fact-checking claims, assessing evidence strength."
        ),
        megabrain_type="Agent",
        human_in_the_loop=True,
    ),
    "advogado-diabo": AgentInfo(
        agent_id="advogado-diabo",
        name="Advogado Diabo",
        role="Devil's advocate",
        tier="conclave",
        mce_steps=(),
        when_to_use=(
            "Use in Conclave deliberation to stress-test dominant positions: "
            "counter-arguments, bias detection, challenging assumptions."
        ),
        megabrain_type="Agent",
        human_in_the_loop=True,
    ),
    "sintetizador-conclave": AgentInfo(
        agent_id="sintetizador-conclave",
        name="Sintetizador Conclave",
        role="Integration architect for conclave synthesis",
        tier="conclave",
        mce_steps=(),
        when_to_use=(
            "Use in Conclave deliberation to produce the final synthesis: "
            "integrate critic and devil's advocate positions into a resolution."
        ),
        megabrain_type="Agent",
        human_in_the_loop=True,
    ),
}


# ---------------------------------------------------------------------------
# STEP_TO_AGENT -- inverted index for O(1) step lookup
# ---------------------------------------------------------------------------


def _build_step_index() -> dict[str, str]:
    """Build the step_id -> agent_id lookup table.

    Iterates over AGENT_REGISTRY and creates an entry for each step
    declared in the agent's ``mce_steps``.

    Returns:
        Dict mapping step_id (str) to agent_id (str).

    Raises:
        ValueError: If two agents claim the same step (config error).
    """
    index: dict[str, str] = {}
    for agent_id, info in AGENT_REGISTRY.items():
        for step in info.mce_steps:
            step_str = str(step)
            if step_str in index:
                raise ValueError(
                    f"Step '{step_str}' claimed by both '{index[step_str]}' and "
                    f"'{agent_id}'.  Each step must have exactly one owner."
                )
            index[step_str] = agent_id
    return index


#: Inverted index: step_id -> agent_id.  Built once at import time.
STEP_TO_AGENT: dict[str, str] = _build_step_index()


# ---------------------------------------------------------------------------
# select_agent() -- deterministic agent selection
# ---------------------------------------------------------------------------


def select_agent(
    step_id: str | int | float,
    *,
    available_agents: dict[str, AgentInfo] | None = None,
) -> str:
    """Select the agent responsible for a given pipeline step.

    Selection is ALWAYS deterministic and explicit:
    1. Normalize ``step_id`` to string.
    2. Look up in ``STEP_TO_AGENT``.
    3. If ``available_agents`` is provided, verify the agent is in the set.
    4. Return the exact ``agent_id``.

    This function NEVER does fuzzy matching, description search, or
    heuristic selection.  If the step is not mapped, it raises.

    Args:
        step_id:          The pipeline step to look up (e.g. ``5``, ``"10.3"``).
        available_agents: Optional subset of agents currently available.
                          If provided, the selected agent must be in this dict.
                          If ``None``, the full AGENT_REGISTRY is used.

    Returns:
        The ``agent_id`` (str) responsible for this step.

    Raises:
        KeyError: If no agent is mapped to the given step.
        RuntimeError: If the mapped agent is not in ``available_agents``.
    """
    step_str = str(step_id).strip()

    if step_str not in STEP_TO_AGENT:
        raise KeyError(
            f"No agent mapped to step '{step_str}'.  "
            f"Known steps: {sorted(STEP_TO_AGENT.keys())}"
        )

    agent_id = STEP_TO_AGENT[step_str]

    if available_agents is not None and agent_id not in available_agents:
        raise RuntimeError(
            f"Agent '{agent_id}' is mapped to step '{step_str}' but is not "
            f"in the available agents set.  Available: {sorted(available_agents.keys())}"
        )

    logger.debug("Step '%s' -> agent '%s'", step_str, agent_id)
    return agent_id


# ---------------------------------------------------------------------------
# get_agent_info() -- get full metadata for an agent
# ---------------------------------------------------------------------------


def get_agent_info(agent_id: str) -> AgentInfo:
    """Return the ``AgentInfo`` for a given agent_id.

    Args:
        agent_id: The agent identifier (e.g. ``"dig"``, ``"guard"``).

    Returns:
        The ``AgentInfo`` dataclass for this agent.

    Raises:
        KeyError: If the agent_id is not in the registry.
    """
    if agent_id not in AGENT_REGISTRY:
        raise KeyError(
            f"Agent '{agent_id}' not found in registry.  "
            f"Known agents: {sorted(AGENT_REGISTRY.keys())}"
        )
    return AGENT_REGISTRY[agent_id]


# ---------------------------------------------------------------------------
# list_agents() / list_steps() -- introspection
# ---------------------------------------------------------------------------


def list_agents() -> list[AgentInfo]:
    """Return all registered agents sorted by tier then agent_id.

    Returns:
        List of ``AgentInfo`` objects.
    """

    def sort_key(info: AgentInfo) -> tuple[str, str]:
        # "conclave" agents sort after numeric tiers.
        tier_str = str(info.tier).zfill(3) if isinstance(info.tier, int) else f"zzz_{info.tier}"
        return (tier_str, info.agent_id)

    return sorted(AGENT_REGISTRY.values(), key=sort_key)


def list_steps() -> list[tuple[str, str]]:
    """Return all step-to-agent mappings sorted by step.

    Returns:
        List of ``(step_id, agent_id)`` tuples, sorted by step.
    """

    def step_sort_key(item: tuple[str, str]) -> float:
        step = item[0]
        if step == "post-pipeline":
            return 999.0
        try:
            return float(step)
        except ValueError:
            return 998.0

    return sorted(STEP_TO_AGENT.items(), key=step_sort_key)
