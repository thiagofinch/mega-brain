"""
state_machine.py -- Pipeline State Machine for MCE
===================================================

Simple finite state machine governing MCE pipeline phase transitions.
Uses the ``transitions`` library for declarative state/transition definitions.

Persists state to YAML at::

    .claude/mission-control/mce/{slug}/pipeline_state.yaml

On every transition the state file is saved.  On construction the state
file is loaded (if it exists) so the pipeline can resume from where it
left off.

Usage::

    from core.intelligence.pipeline.mce.state_machine import PipelineStateMachine

    sm = PipelineStateMachine("alex-hormozi")
    sm.start_chunking()       # init -> chunking
    sm.start_entities()       # chunking -> entities
    sm.start_knowledge()      # entities -> knowledge_extraction
    # ...
    sm.finish()               # validation -> complete

    # Resume in a new session:
    sm2 = PipelineStateMachine("alex-hormozi")
    print(sm2.state)          # picks up wherever it was saved

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from transitions import Machine

# ---------------------------------------------------------------------------
# Imports: core.paths (with standalone fallback)
# ---------------------------------------------------------------------------

from core.paths import ROUTING

logger = logging.getLogger("mce.state_machine")

# ---------------------------------------------------------------------------
# State & Transition Definitions
# ---------------------------------------------------------------------------

STATES: list[str] = [
    "init",
    "chunking",
    "entities",
    "knowledge_extraction",
    "mce_extraction",
    "identity_checkpoint",
    "consolidation",
    "agent_generation",
    "validation",
    "complete",
    "failed",
    "paused",
]

# Base transitions WITHOUT conditions -- used when qa_gates is not available
# (e.g. in tests, or when the module cannot be imported).  The conditions
# are layered on at runtime inside __init__ only when qa_gates loads OK.
TRANSITIONS: list[dict[str, Any]] = [
    {"trigger": "start_chunking", "source": "init", "dest": "chunking"},
    {"trigger": "start_entities", "source": "chunking", "dest": "entities"},
    {"trigger": "start_knowledge", "source": "entities", "dest": "knowledge_extraction"},
    {"trigger": "start_mce", "source": "entities", "dest": "mce_extraction"},
    {"trigger": "checkpoint", "source": "mce_extraction", "dest": "identity_checkpoint"},
    {"trigger": "approve", "source": "identity_checkpoint", "dest": "consolidation"},
    {"trigger": "revise", "source": "identity_checkpoint", "dest": "mce_extraction"},
    {"trigger": "start_agents", "source": "consolidation", "dest": "agent_generation"},
    {"trigger": "start_validation", "source": "agent_generation", "dest": "validation"},
    {"trigger": "finish", "source": "validation", "dest": "complete"},
    {"trigger": "fail", "source": "*", "dest": "failed"},
    {"trigger": "pause", "source": "*", "dest": "paused"},
    {"trigger": "recover", "source": ["failed", "paused"], "dest": "init"},
]

# Condition mappings -- only applied when qa_gates is available.
# Keys are trigger names, values are condition function name lists.
_CONDITION_MAP: dict[str, list[str]] = {
    "start_chunking": ["can_start_chunking"],
    "start_entities": ["can_start_entities"],
    "start_knowledge": ["can_start_knowledge"],
    "checkpoint": ["can_checkpoint"],
    "approve": ["can_approve"],
    "start_agents": ["can_start_agents"],
    "start_validation": ["can_validate"],
    "finish": ["can_finish"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _state_dir(slug: str) -> Path:
    """Return the directory for a given persona slug's MCE state files."""
    base: Path = ROUTING.get("mce_state", Path(".claude/mission-control/mce"))
    return Path(base) / slug


def _state_path(slug: str) -> Path:
    """Return the YAML state file path for a given persona slug."""
    return _state_dir(slug) / "pipeline_state.yaml"


# ---------------------------------------------------------------------------
# PipelineStateMachine
# ---------------------------------------------------------------------------


class PipelineStateMachine:
    """Finite state machine for MCE pipeline phase transitions.

    Wraps the ``transitions.Machine`` with YAML persistence so state
    survives across sessions.

    Args:
        slug: Persona slug (e.g. ``"alex-hormozi"``).  Used to derive
              the state-file path.
        auto_load: If *True* (default), attempt to load existing state
                   from disk on construction.
        enable_gates: If *True* (default), attempt to load ``qa_gates``
                      condition functions.  When *False* (or when the
                      import fails), transitions are unconditional --
                      useful for unit tests that don't need artifact
                      validation.
    """

    def __init__(
        self, slug: str, *, auto_load: bool = True, enable_gates: bool = True
    ) -> None:
        self.slug: str = slug
        self._state_path: Path = _state_path(slug)
        self._history: list[dict[str, str]] = []
        self._qa_gates_available: bool = False

        # Determine initial state -- either from disk or "init".
        initial_state = "init"
        if auto_load:
            loaded = self._load()
            if loaded is not None:
                initial_state = loaded.get("state", "init")
                self._history = loaded.get("history", [])

        # Bind qa_gates condition functions as methods on self.
        # The transitions library resolves string condition names (e.g.
        # "can_start_chunking") by looking them up as attributes on the model
        # object.  Import is deferred to __init__ (not module-level) to avoid
        # a circular import: state_machine -> qa_gates is allowed, but
        # qa_gates must never import state_machine.
        if enable_gates:
            try:
                from core.intelligence.pipeline.mce.qa_gates import (
                    can_approve,
                    can_checkpoint,
                    can_finish,
                    can_start_agents,
                    can_start_chunking,
                    can_start_entities,
                    can_start_knowledge,
                    can_validate,
                )

                self.can_start_chunking = can_start_chunking
                self.can_start_entities = can_start_entities
                self.can_start_knowledge = can_start_knowledge
                self.can_checkpoint = can_checkpoint
                self.can_approve = can_approve
                self.can_start_agents = can_start_agents
                self.can_validate = can_validate
                self.can_finish = can_finish
                self._qa_gates_available = True
            except Exception:
                logger.warning(
                    "qa_gates not available — transitions will not be gated"
                )

        # Build transitions: add conditions only if qa_gates loaded successfully.
        # When qa_gates is NOT available (e.g. in unit tests), transitions are
        # unconditional so triggers fire without requiring artifact files on disk.
        if self._qa_gates_available:
            transitions = []
            for t in TRANSITIONS:
                t_copy = dict(t)
                trigger = t_copy["trigger"]
                if trigger in _CONDITION_MAP:
                    t_copy["conditions"] = _CONDITION_MAP[trigger]
                transitions.append(t_copy)
        else:
            transitions = list(TRANSITIONS)

        # Build the machine.  ``transitions`` attaches triggers as methods
        # on *self* (e.g. ``self.start_chunking()``).
        self._machine = Machine(
            model=self,
            states=STATES,
            transitions=transitions,
            initial=initial_state,
            auto_transitions=False,
            send_event=True,
        )

        # Register an after-state-change callback to persist.
        self._machine.after_state_change = "_on_state_change"  # type: ignore[attr-defined]

    # -- persistence --------------------------------------------------------

    def _load(self) -> dict[str, Any] | None:
        """Load state from YAML on disk.  Returns *None* if file missing."""
        if not self._state_path.exists():
            return None
        try:
            text = self._state_path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                logger.info("Loaded MCE state for %s: state=%s", self.slug, data.get("state"))
                return data
        except (yaml.YAMLError, OSError) as exc:
            logger.warning("Failed to load MCE state for %s: %s", self.slug, exc)
        return None

    def save(self) -> Path:
        """Persist current state to YAML.

        Returns:
            Path to the written file.
        """
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "slug": self.slug,
            "state": self.state,
            "updated_at": _now_iso(),
            "history": self._history,
        }

        self._state_path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        logger.debug("Saved MCE state for %s -> %s", self.slug, self.state)
        return self._state_path

    # -- callbacks ----------------------------------------------------------

    def _on_state_change(self, event: Any) -> None:
        """Called by ``transitions`` after every state change."""
        entry: dict[str, str] = {
            "from": str(event.transition.source),
            "to": str(event.transition.dest),
            "trigger": str(event.event.name),
            "timestamp": _now_iso(),
        }
        self._history.append(entry)
        self.save()

    # -- convenience --------------------------------------------------------

    @property
    def is_terminal(self) -> bool:
        """Return *True* if the machine is in a terminal state.

        Note: ``is_complete`` and ``is_failed`` are auto-generated by
        the ``transitions`` library as ``is_{state}`` convenience checks.
        This property covers both terminal states in one call.
        """
        return self.state in ("complete", "failed")

    @property
    def paused(self) -> bool:
        """Return *True* if the machine is paused.

        Named ``paused`` (not ``is_paused``) to avoid collision with
        the ``transitions`` library auto-generated ``is_paused`` attribute.
        """
        return self.state == "paused"

    @property
    def history(self) -> list[dict[str, str]]:
        """Return the transition history (list of dicts)."""
        return list(self._history)

    @property
    def state_path(self) -> Path:
        """Return the path to the YAML state file."""
        return self._state_path

    def reset(self) -> None:
        """Hard-reset the machine to ``init`` and clear history.

        Saves immediately so the reset is durable.
        """
        self._machine.set_state("init")
        self._history = []
        self.save()

    def __repr__(self) -> str:
        return f"PipelineStateMachine(slug={self.slug!r}, state={self.state!r})"
