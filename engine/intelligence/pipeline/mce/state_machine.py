"""
state_machine.py -- Pipeline State Machine for MCE
===================================================

Finite state machine governing MCE pipeline phase transitions.
Uses the ``transitions`` library for declarative state/transition definitions.

16 operational states aligned 1:1 with the 12 SKILL steps, plus
``failed`` and ``paused`` (18 total).

Persists state to YAML at::

    .claude/mission-control/mce/{slug}/pipeline_state.yaml

On every transition the state file is saved.  On construction the state
file is loaded (if it exists) so the pipeline can resume from where it
left off.  Legacy state names are auto-migrated via ``STATE_MIGRATION``.

Execution mode (parallel/sequential/streaming) is persisted alongside
the state.  On resume the mode is restored from the state file, not
from config.  A mismatch between state and config emits a warning but
the persisted mode always prevails (unless overridden via CLI).

Usage::

    from engine.intelligence.pipeline.mce.state_machine import PipelineStateMachine

    sm = PipelineStateMachine("alex-hormozi")
    sm.start_ingest()         # init -> ingesting
    sm.start_batch()          # ingesting -> batching
    sm.start_chunking()       # batching -> chunking
    sm.start_entities()       # chunking -> entity_resolution
    # ...
    sm.finish()               # reporting -> complete

    # Resume in a new session:
    sm2 = PipelineStateMachine("alex-hormozi")
    print(sm2.state)          # picks up wherever it was saved
    print(sm2.execution_mode) # restored from state file

Version: 2.2.0
Date: 2026-04-01
Epic: MCE-V2.1 / Story MCE21-3.2
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

try:
    from engine.paths import ROUTING
except ImportError:
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    _MISSION_CONTROL = _ROOT / ".claude" / "mission-control"
    ROUTING = {"mce_state": _MISSION_CONTROL / "mce"}

logger = logging.getLogger("mce.state_machine")

# ---------------------------------------------------------------------------
# State & Transition Definitions (v2 -- 16 operational + failed + paused)
# ---------------------------------------------------------------------------

STATES: list[str] = [
    "init",
    "ingesting",
    "batching",
    "chunking",
    "entity_resolution",
    "insight_extraction",
    "mce_behavioral",
    "mce_identity",
    "mce_voice",
    "identity_checkpoint",
    "consolidation",
    "rag_indexation",
    "agent_generation",
    "finalizing",
    "reporting",
    "complete",
    "failed",
    "paused",
]

TRANSITIONS: list[dict[str, Any]] = [
    {"trigger": "start_ingest", "source": "init", "dest": "ingesting"},
    {"trigger": "start_batch", "source": "ingesting", "dest": "batching"},
    {
        "trigger": "start_chunking",
        "source": "batching",
        "dest": "chunking",
        "conditions": "can_start_chunking",
    },
    {
        "trigger": "start_entities",
        "source": "chunking",
        "dest": "entity_resolution",
        "conditions": "can_start_entities",
    },
    {
        "trigger": "start_insights",
        "source": "entity_resolution",
        "dest": "insight_extraction",
        "conditions": "can_start_knowledge",
    },
    {"trigger": "start_behavioral", "source": "insight_extraction", "dest": "mce_behavioral"},
    {"trigger": "start_identity", "source": "mce_behavioral", "dest": "mce_identity"},
    {"trigger": "start_voice", "source": "mce_identity", "dest": "mce_voice"},
    {
        "trigger": "checkpoint",
        "source": "mce_voice",
        "dest": "identity_checkpoint",
        "conditions": "can_checkpoint",
    },
    {
        "trigger": "approve",
        "source": "identity_checkpoint",
        "dest": "consolidation",
        "conditions": "can_approve",
    },
    {"trigger": "revise", "source": "identity_checkpoint", "dest": "mce_identity"},
    {"trigger": "start_rag_index", "source": "consolidation", "dest": "rag_indexation"},
    {
        "trigger": "start_agents",
        "source": "rag_indexation",
        "dest": "agent_generation",
        "conditions": "can_start_agents",
    },
    {"trigger": "start_finalize", "source": "agent_generation", "dest": "finalizing"},
    {
        "trigger": "start_report",
        "source": "finalizing",
        "dest": "reporting",
        "conditions": "can_validate",
    },
    {"trigger": "finish", "source": "reporting", "dest": "complete", "conditions": "can_finish"},
    {"trigger": "fail", "source": "*", "dest": "failed"},
    {"trigger": "pause", "source": "*", "dest": "paused"},
    {"trigger": "recover", "source": ["failed", "paused"], "dest": "init"},
]

# Maps legacy state names to their v2 equivalents.
# Used at load time so existing pipeline_state.yaml files keep working.
STATE_MIGRATION: dict[str, str] = {
    "knowledge_extraction": "insight_extraction",
    "mce_extraction": "mce_behavioral",
    "validation": "reporting",
    "entities": "entity_resolution",
}

# ---------------------------------------------------------------------------
# Execution Mode Definitions (Story MCE21-2.3)
# ---------------------------------------------------------------------------

#: Valid execution modes for the MCE pipeline coordinator.
#: - ``sequential``: Steps run one after another (default, safest).
#: - ``parallel``: Independent steps run concurrently.
#: - ``streaming``: Chunks stream through the pipeline without batching.
VALID_EXECUTION_MODES: frozenset[str] = frozenset(
    {
        "sequential",
        "parallel",
        "streaming",
    }
)

#: Default execution mode when nothing is configured or persisted.
DEFAULT_EXECUTION_MODE: str = "sequential"


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

    Execution mode (``parallel``/``sequential``/``streaming``) is persisted
    in the state file and restored on resume.  When a mismatch is detected
    between the persisted mode and the config cascade, a warning is logged
    and the **persisted mode prevails** (principle: state > config).

    A CLI override via ``FeatureGates`` takes highest precedence over both
    the persisted state and the config cascade.

    Args:
        slug: Persona slug (e.g. ``"alex-hormozi"``).  Used to derive
              the state-file path.
        auto_load: If *True* (default), attempt to load existing state
                   from disk on construction.
        config: Optional ``CascadeConfig`` instance.  Used to detect
                mode mismatches and resolve the config-level mode.
        feature_gates: Optional ``FeatureGates`` instance.  When provided,
                       a CLI ``--mode`` override is checked and takes
                       highest precedence.
    """

    def __init__(
        self,
        slug: str,
        *,
        auto_load: bool = True,
        config: Any | None = None,
        feature_gates: Any | None = None,
    ) -> None:
        self.slug: str = slug
        self._state_path: Path = _state_path(slug)
        self._history: list[dict[str, str]] = []
        self._config = config
        self._feature_gates = feature_gates

        # Session pause/resume tracking (Story MCE21-3.2).
        # ``_paused_from`` stores the state the machine was in before pause.
        # ``_step_cursor`` stores the step index within the paused state.
        self._paused_from: str | None = None
        self._step_cursor: int | None = None

        # Determine initial state -- either from disk or "init".
        # Legacy state names are auto-migrated via STATE_MIGRATION.
        initial_state = "init"
        persisted_mode: str | None = None

        if auto_load:
            loaded = self._load()
            if loaded is not None:
                raw_state = loaded.get("state", "init")
                initial_state = STATE_MIGRATION.get(raw_state, raw_state)
                if initial_state != raw_state:
                    logger.info(
                        "Migrated legacy state %r -> %r for %s",
                        raw_state,
                        initial_state,
                        slug,
                    )
                self._history = loaded.get("history", [])
                persisted_mode = loaded.get("execution_mode")
                self._paused_from = loaded.get("paused_from")
                self._step_cursor = loaded.get("step_cursor")

        # Resolve execution_mode through the 3-level precedence chain:
        #   1. CLI override (via feature_gates)  -- highest
        #   2. Persisted state file              -- mid
        #   3. Config cascade / default          -- lowest
        self._execution_mode: str = self._resolve_execution_mode(persisted_mode)

        # Build the machine.  ``transitions`` attaches triggers as methods
        # on *self* (e.g. ``self.start_chunking()``).
        self._machine = Machine(
            model=self,
            states=STATES,
            transitions=TRANSITIONS,
            initial=initial_state,
            auto_transitions=False,
            send_event=True,
        )

        # Register an after-state-change callback to persist.
        self._machine.after_state_change = "_on_state_change"  # type: ignore[attr-defined]

    # -- QA gate condition delegates ----------------------------------------
    # These are called by the ``transitions`` library when a transition has
    # ``conditions``.  They delegate to ``qa_gates`` condition functions.
    # Wrapped in try/except so tests (that mock qa_gates away) still work.

    def _qa_condition(self, fn_name: str, event: Any = None) -> bool:
        """Call a qa_gates condition function by name, with graceful degradation."""
        try:
            from engine.intelligence.pipeline.mce import qa_gates

            fn = getattr(qa_gates, fn_name, None)
            if fn is None:
                return True
            return fn(event)
        except Exception:
            return True  # graceful degradation: allow transition

    def can_start_chunking(self, event: Any = None) -> bool:
        return self._qa_condition("can_start_chunking", event)

    def can_start_entities(self, event: Any = None) -> bool:
        return self._qa_condition("can_start_entities", event)

    def can_start_knowledge(self, event: Any = None) -> bool:
        return self._qa_condition("can_start_knowledge", event)

    def can_checkpoint(self, event: Any = None) -> bool:
        return self._qa_condition("can_checkpoint", event)

    def can_approve(self, event: Any = None) -> bool:
        return self._qa_condition("can_approve", event)

    def can_start_agents(self, event: Any = None) -> bool:
        return self._qa_condition("can_start_agents", event)

    def can_validate(self, event: Any = None) -> bool:
        return self._qa_condition("can_validate", event)

    def can_finish(self, event: Any = None) -> bool:
        return self._qa_condition("can_finish", event)

    # -- execution mode resolution ------------------------------------------

    def _resolve_execution_mode(self, persisted_mode: str | None) -> str:
        """Resolve execution_mode through the 3-level precedence chain.

        Precedence (highest to lowest):
            1. CLI override via ``FeatureGates.get_mode("execution_mode")``
            2. Persisted mode from state file
            3. Config cascade ``config.get("execution_mode")``
            4. Hardcoded default (``sequential``)

        When the persisted mode differs from the config cascade mode,
        a warning is emitted but the persisted mode prevails (unless
        a CLI override is active).

        Args:
            persisted_mode: Mode loaded from the state file, or *None*
                            if no state file existed.

        Returns:
            The resolved execution mode string.
        """
        # 1. CLI override via feature_gates (highest precedence)
        cli_mode = self._get_cli_mode_override()
        if cli_mode is not None:
            validated = self._validate_mode(cli_mode)
            if persisted_mode and validated != persisted_mode:
                logger.info(
                    "CLI override: execution_mode %r -> %r for %s",
                    persisted_mode,
                    validated,
                    self.slug,
                )
            return validated

        # 2. Persisted mode from state file
        if persisted_mode is not None:
            validated = self._validate_mode(persisted_mode)
            # Check for mismatch with config
            config_mode = self._get_config_mode()
            if config_mode is not None and config_mode != validated:
                logger.warning(
                    "Mode mismatch for %s: state has %r, config has %r. "
                    "Using persisted state mode (state prevails).",
                    self.slug,
                    validated,
                    config_mode,
                )
            return validated

        # 3. Config cascade
        config_mode = self._get_config_mode()
        if config_mode is not None:
            return self._validate_mode(config_mode)

        # 4. Hardcoded default
        return DEFAULT_EXECUTION_MODE

    def _get_cli_mode_override(self) -> str | None:
        """Check feature_gates for a CLI --mode override.

        Returns the mode string if a CLI override is active, None otherwise.
        """
        if self._feature_gates is None:
            return None
        try:
            # FeatureGates.get_mode("execution_mode") resolves through
            # CascadeConfig with gate_mode_execution_mode prefix first,
            # then direct key.  CLI args sit at level 1 of the cascade,
            # so if --mode was passed, it surfaces here.
            mode = self._feature_gates.get_mode("execution_mode")
            if mode is not None:
                return str(mode)
        except Exception:
            pass
        return None

    def _get_config_mode(self) -> str | None:
        """Read execution_mode from the config cascade (no CLI).

        Returns the mode string if config provides one, None otherwise.
        """
        if self._config is None:
            return None
        try:
            mode = self._config.get("execution_mode")
            if mode is not None:
                return str(mode)
        except Exception:
            pass
        return None

    @staticmethod
    def _validate_mode(mode: str) -> str:
        """Validate and normalize an execution mode string.

        If the mode is not in ``VALID_EXECUTION_MODES``, logs a warning
        and falls back to ``DEFAULT_EXECUTION_MODE``.
        """
        normalized = str(mode).strip().lower()
        if normalized in VALID_EXECUTION_MODES:
            return normalized
        logger.warning(
            "Invalid execution_mode %r, falling back to %r",
            mode,
            DEFAULT_EXECUTION_MODE,
        )
        return DEFAULT_EXECUTION_MODE

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

        The execution_mode is always included in the persisted data
        so that resume can restore it without re-reading config.

        Returns:
            Path to the written file.
        """
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "slug": self.slug,
            "state": self.state,
            "execution_mode": self._execution_mode,
            "updated_at": _now_iso(),
            "history": self._history,
        }

        # Session backgrounding fields (MCE21-3.2).
        # Only written when non-None to keep the state file clean.
        if self._paused_from is not None:
            data["paused_from"] = self._paused_from
        if self._step_cursor is not None:
            data["step_cursor"] = self._step_cursor

        self._state_path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        logger.debug(
            "Saved MCE state for %s -> %s (mode=%s)", self.slug, self.state, self._execution_mode
        )
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

    # -- execution mode public API ------------------------------------------

    @property
    def execution_mode(self) -> str:
        """Return the current execution mode (``parallel``/``sequential``/``streaming``)."""
        return self._execution_mode

    def set_execution_mode(self, mode: str) -> None:
        """Set execution mode and persist immediately.

        Args:
            mode: One of ``"parallel"``, ``"sequential"``, ``"streaming"``.

        Raises:
            ValueError: If *mode* is not a valid execution mode.
        """
        normalized = mode.strip().lower()
        if normalized not in VALID_EXECUTION_MODES:
            raise ValueError(
                f"Invalid execution_mode {mode!r}. "
                f"Must be one of: {', '.join(sorted(VALID_EXECUTION_MODES))}"
            )
        old = self._execution_mode
        self._execution_mode = normalized
        if old != normalized:
            logger.info(
                "Execution mode changed for %s: %s -> %s",
                self.slug,
                old,
                normalized,
            )
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

    def _last_valid_state(self) -> str:
        """Find the last non-fail/non-pause state from history.

        Walks backwards through transition history and returns the first
        ``to`` state that is not ``"failed"`` or ``"paused"``.  Falls back
        to ``"init"`` if no valid state is found.
        """
        for entry in reversed(self._history):
            target = entry.get("to", "")
            if target not in ("failed", "paused"):
                return target
        return "init"

    def recover_to_last(self) -> str:
        """Recover to the last valid state (not ``init``).

        Unlike the standard ``recover`` trigger which always goes to ``init``,
        this method jumps directly to the last valid pipeline state before
        the fail/pause occurred.

        Returns:
            The state name that was recovered to.
        """
        target = self._last_valid_state()
        source = self.state
        self._machine.set_state(target)
        entry: dict[str, str] = {
            "from": source,
            "to": target,
            "trigger": "recover_to_last",
            "timestamp": _now_iso(),
        }
        self._history.append(entry)
        self.save()
        logger.info("Recovered %s: %s -> %s (smart recovery)", self.slug, source, target)
        return target

    # -- session backgrounding (MCE21-3.2) -----------------------------------

    def pause_session(self, step_cursor: int | None = None) -> str:
        """Intentionally pause the session, recording the exact point.

        Unlike ``pause()`` (the raw ``transitions`` trigger), this method
        stores the pre-pause state and an optional step cursor so that
        ``resume_from_pause()`` can jump back to the exact position.

        Args:
            step_cursor: Optional step index within the current state.
                         Persisted as ``step_cursor`` in the state file.

        Returns:
            The state the machine was in before pausing.
        """
        if self.state == "paused":
            logger.warning("Already paused for %s -- ignoring duplicate pause", self.slug)
            return self._paused_from or "init"

        source = self.state
        self._paused_from = source
        self._step_cursor = step_cursor

        # Use the transitions trigger to go to 'paused'.
        # This fires _on_state_change which saves automatically.
        self.pause()

        logger.info(
            "Session paused for %s: %s (step_cursor=%s)",
            self.slug,
            source,
            step_cursor,
        )
        return source

    def resume_from_pause(self) -> str:
        """Resume from an intentional pause, returning to the pre-pause state.

        This is fundamentally different from ``recover_to_last()``:

        - ``recover_to_last()`` is for **crash recovery** -- it walks history
          backwards to find the last valid state.
        - ``resume_from_pause()`` is for **intentional resume** -- it reads
          the ``paused_from`` field that was explicitly saved during pause.

        Returns:
            The state name that was resumed to.

        Raises:
            RuntimeError: If the machine is not in ``paused`` state or if
                          no ``paused_from`` state was recorded.
        """
        if self.state != "paused":
            raise RuntimeError(
                f"Cannot resume_from_pause: state is {self.state!r}, " f"expected 'paused'"
            )

        if self._paused_from is None:
            raise RuntimeError(
                "Cannot resume_from_pause: no paused_from state recorded. "
                "This session may have been paused by the raw 'pause' trigger "
                "instead of pause_session(). Use recover_to_last() instead."
            )

        target = self._paused_from
        source = self.state

        self._machine.set_state(target)
        entry: dict[str, str] = {
            "from": source,
            "to": target,
            "trigger": "resume_from_pause",
            "timestamp": _now_iso(),
        }
        self._history.append(entry)

        # Clear pause metadata now that we've resumed.
        resumed_cursor = self._step_cursor
        self._paused_from = None
        self._step_cursor = None
        self.save()

        logger.info(
            "Session resumed for %s: %s -> %s (step_cursor was %s)",
            self.slug,
            source,
            target,
            resumed_cursor,
        )
        return target

    @property
    def paused_from(self) -> str | None:
        """Return the state the machine was in before pausing, or None."""
        return self._paused_from

    @property
    def step_cursor(self) -> int | None:
        """Return the step cursor saved during pause, or None."""
        return self._step_cursor

    # -- reset ----------------------------------------------------------------

    def reset(self) -> None:
        """Hard-reset the machine to ``init`` and clear history.

        Also resets execution_mode to the default and clears pause metadata.
        Saves immediately so the reset is durable.
        """
        self._machine.set_state("init")
        self._history = []
        self._execution_mode = DEFAULT_EXECUTION_MODE
        self._paused_from = None
        self._step_cursor = None
        self.save()

    def __repr__(self) -> str:
        return (
            f"PipelineStateMachine(slug={self.slug!r}, "
            f"state={self.state!r}, mode={self._execution_mode!r})"
        )
