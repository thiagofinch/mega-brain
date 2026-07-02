"""
step_plugin.py -- StepPlugin ABC + StepContext for MCE Pipeline
===============================================================

Defines the plugin contract that every pipeline step must implement.
This is the extensibility backbone: new steps subclass StepPlugin,
the orchestrator discovers them via StepRegistry, and executes them
through a uniform interface.

Architecture
------------
::

    StepPlugin (ABC)
       |
       |-- id, version, depends_on, step_type
       |-- execute(context) -> StepResult
       |-- validate_input(context) -> ValidationResult
       |-- get_prompt_template() -> Optional[str]
       |
       v
    StepContext (dataclass)
       |-- state, config (CascadeConfig), hook_bus (HookBus)
       |-- artifact_store, logger, slug, step_id, cost_tracker

Design Decisions
~~~~~~~~~~~~~~~~
- StepPlugin is an ABC, NOT a protocol, because we need to enforce
  that subclasses implement execute() and validate_input().  A protocol
  would be structural and allow silent failures.
- StepContext bundles all runtime dependencies so plugins never import
  global singletons directly -- makes testing trivial (inject mocks).
- ValidationResult is intentionally simple (bool + errors list).
  Complex validation chains compose multiple ValidationResults.

Constraints
~~~~~~~~~~~
- stdlib + typing only in this module (no LLM calls, no network).
- Every class is a dataclass or ABC -- no metaclass magic.
- Thread-safe by design: StepContext is immutable after construction.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-2.1 -- StepPlugin Interface + Registry
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# ---------------------------------------------------------------------------
# StepType enum
# ---------------------------------------------------------------------------


class StepType(str, Enum):
    """Classification of pipeline step execution mode.

    Determines how the orchestrator schedules and monitors the step:
    - DETERMINISTIC: Pure Python, no LLM calls, fully reproducible.
    - LLM: Requires an LLM call (prompt template expected).
    - HUMAN: Requires human input/checkpoint before proceeding.
    """

    DETERMINISTIC = "deterministic"
    LLM = "llm"
    HUMAN = "human"


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Result of input validation for a step.

    Attributes:
        valid: True if all preconditions are met.
        errors: List of human-readable error descriptions.
                Empty when valid is True.
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Allow ``if validation_result:`` idiom."""
        return self.valid

    @staticmethod
    def ok() -> ValidationResult:
        """Factory for a passing validation."""
        return ValidationResult(valid=True)

    @staticmethod
    def fail(errors: list[str]) -> ValidationResult:
        """Factory for a failing validation.

        Args:
            errors: Non-empty list of error descriptions.
        """
        return ValidationResult(valid=False, errors=errors)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Combine two results. Invalid if either is invalid.

        Args:
            other: Another ValidationResult to merge with.

        Returns:
            New ValidationResult with combined errors.
        """
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
        )


# ---------------------------------------------------------------------------
# StepContext
# ---------------------------------------------------------------------------


@dataclass
class StepContext:
    """Runtime context injected into every step execution.

    Bundles all dependencies so plugins never need to import global
    singletons.  This makes testing trivial -- inject mocks for any
    field.

    Attributes:
        state: Current pipeline state dict (mutable -- steps can
               add/modify keys for downstream steps).
        config: CascadeConfig instance for reading pipeline settings.
                Accepts any object with a ``get(key, default)`` method
                so tests can pass a plain dict wrapper.
        hook_bus: HookBus instance for emitting lifecycle events.
                  Accepts any object with ``emit()`` and
                  ``emit_blocking()`` methods.
        artifact_store: Mutable dict for steps to deposit artifacts
                        (files, dossiers, analysis results) keyed by
                        artifact name.
        logger: Python logger for the step.  Defaults to the MCE
                pipeline logger.
        slug: Persona slug being processed (e.g., "alex-hormozi").
        step_id: Unique identifier of the current step execution.
        cost_tracker: Optional dict tracking LLM cost accumulation.
                      Steps that make LLM calls should update
                      ``cost_tracker["total_usd"]`` and
                      ``cost_tracker["calls"]``.
    """

    state: dict[str, Any]
    config: Any  # CascadeConfig or mock with get(key, default)
    hook_bus: Any  # HookBus or mock with emit()/emit_blocking()
    artifact_store: dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("mce.step_plugin"))
    slug: str = ""
    step_id: str = ""
    cost_tracker: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# StepPlugin ABC
# ---------------------------------------------------------------------------


class StepPlugin(ABC):
    """Abstract base class for MCE pipeline steps.

    Every pipeline step MUST subclass this and implement:
    - ``id`` property: unique step identifier (e.g., "classify-dna-layer")
    - ``version`` property: semver string (e.g., "1.0.0")
    - ``depends_on`` property: list of step IDs that must run before this one
    - ``step_type`` property: StepType enum classifying execution mode
    - ``execute(context)``: main execution logic
    - ``validate_input(context)``: pre-flight check before execution

    Optional override:
    - ``get_prompt_template()``: return a prompt template string for LLM steps
    - ``is_concurrency_safe``: whether this step can run concurrently (default
      based on step_type: DETERMINISTIC=True, LLM=True, HUMAN=False)

    Example::

        class ClassifyDnaLayer(StepPlugin):

            @property
            def id(self) -> str:
                return "classify-dna-layer"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def depends_on(self) -> list[str]:
                return []

            @property
            def step_type(self) -> StepType:
                return StepType.DETERMINISTIC

            def execute(self, context: StepContext) -> dict:
                # ... classification logic ...
                return {"classification": "HEURISTICS"}

            def validate_input(self, context: StepContext) -> ValidationResult:
                if "raw_text" not in context.state:
                    return ValidationResult.fail(["Missing 'raw_text' in state"])
                return ValidationResult.ok()
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique step identifier (kebab-case, e.g., 'classify-dna-layer')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Step version following semver (e.g., '1.0.0')."""
        ...

    @property
    @abstractmethod
    def depends_on(self) -> list[str]:
        """List of step IDs that must complete before this step runs.

        Return an empty list for steps with no dependencies.
        """
        ...

    @property
    @abstractmethod
    def step_type(self) -> StepType:
        """Classification of execution mode (DETERMINISTIC, LLM, HUMAN)."""
        ...

    @abstractmethod
    def execute(self, context: StepContext) -> dict[str, Any]:
        """Execute the step logic.

        Args:
            context: Runtime context with state, config, hooks, etc.

        Returns:
            Dict with step-specific results.  The orchestrator will
            merge relevant keys into ``context.state`` for downstream
            steps.

        Raises:
            Any exception -- the orchestrator catches and routes to
            error handling / retry logic.
        """
        ...

    @abstractmethod
    def validate_input(self, context: StepContext) -> ValidationResult:
        """Validate that all preconditions are met before execution.

        Called by the orchestrator BEFORE ``execute()``.  If validation
        fails, the step is skipped and the failure is logged.

        Args:
            context: Runtime context to validate against.

        Returns:
            ValidationResult indicating pass/fail with error details.
        """
        ...

    def get_prompt_template(self) -> Optional[str]:
        """Return the prompt template for LLM-type steps.

        Override this for steps with ``step_type == StepType.LLM``.
        Returns None by default (no template needed for deterministic
        and human steps).

        Returns:
            Prompt template string with ``{placeholders}``, or None.
        """
        return None

    # -- Background/Foreground visibility (MCE21-3.4) -------------------------

    @property
    def is_background(self) -> bool:
        """Whether this step runs as a background (proactive) task.

        Background steps are tasks like Dream Task and RAG indexation
        that run proactively outside the primary pipeline flow.
        Foreground steps are the standard MCE pipeline execution steps.

        The DAG executor and pipeline manifest use this to separate
        background tasks from the primary execution sequence.

        Default is False (foreground). Background steps override
        this property to return True.

        Returns:
            True if this is a background/proactive step.
        """
        return False

    # -- Concurrency metadata (MCE21-1.4) -----------------------------------

    # Default concurrency safety by step type.
    # DETERMINISTIC and LLM steps are safe (stateless/read-only).
    # HUMAN steps are unsafe (require exclusive interaction).
    _CONCURRENCY_SAFE_DEFAULTS: dict[StepType, bool] = {
        StepType.DETERMINISTIC: True,
        StepType.LLM: True,
        StepType.HUMAN: False,
    }

    @property
    def is_concurrency_safe(self) -> bool:
        """Whether this step can safely run concurrently with other steps.

        The DAG executor uses this to decide scheduling strategy:
        - Safe steps (True): eligible for asyncio.gather (parallel).
        - Unsafe steps (False): run serially with exclusive lock.

        Default is derived from ``step_type``:
        - DETERMINISTIC: True (pure computation, no side effects)
        - LLM: True (stateless API calls, independent per step)
        - HUMAN: False (requires exclusive human interaction)

        Subclasses can override this property to declare custom
        concurrency behavior. For example, an LLM step that writes
        to a shared file should override to return False.

        Returns:
            True if the step is safe for concurrent execution.
        """
        return self._CONCURRENCY_SAFE_DEFAULTS.get(self.step_type, False)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"id={self.id!r} v={self.version!r} "
            f"type={self.step_type.value}>"
        )
