"""
policy_limits.py -- Policy Limits Enforcement for MCE Pipeline
===============================================================

Controls which actions each pipeline step is allowed to perform.
Enforces per-step restrictions via a YAML policy file, with ETag-based
caching to avoid reloading unchanged policies.

Architecture
------------
::

    dag_executor.py  -->  policy_limits.py  -->  hook_bus.py (on_policy_denied)
                     -->  config_cascade.py (per-slug override)

The PolicyLimiter sits between the DAG executor and step execution.
Before each step runs, the executor calls ``check(step_id, action)``
which returns a PolicyDecision (allowed/denied + reason).

Two modes:
- **whitelist** (default): only explicitly listed actions are allowed.
- **blacklist**: all actions are allowed except those explicitly denied.

Per-slug overrides can change mode and step policies for specific
personas, resolved via the CascadeConfig.

ETag Cache
~~~~~~~~~~
Policies are loaded from YAML once.  Subsequent ``load_policies()``
calls compare the file's mtime as a lightweight ETag -- if unchanged,
the cached policies are reused.  This avoids disk I/O on every check.

Hook Integration
~~~~~~~~~~~~~~~~
When a check returns denied, the bus emits ``on_policy_denied`` with
the step_id, action, and reason.  This is a non-blocking event --
the pipeline decides whether to halt or continue.

Constraints
~~~~~~~~~~~
- stdlib + PyYAML only (no external deps, no LLM calls, no network).
- Every function is DETERMINISTIC and side-effect-isolated.
- Thread-safe for concurrent reads (policies are immutable after load).

Version: 1.0.0
Date: 2026-04-01
Story: MCE21-1.1 -- Policy Limits Enforcement
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.policy_limits")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_POLICIES_PATH = Path(__file__).resolve().parent / "policies.yaml"

MODE_WHITELIST = "whitelist"
MODE_BLACKLIST = "blacklist"

_VALID_MODES = frozenset({MODE_WHITELIST, MODE_BLACKLIST})


# ---------------------------------------------------------------------------
# Policy Decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyDecision:
    """Result of a policy check.

    Attributes:
        allowed: True if the action is permitted for the step.
        reason: Human-readable explanation of the decision.
        step_id: The step that was checked.
        action: The action that was checked.
    """

    allowed: bool
    reason: str
    step_id: str
    action: str


# ---------------------------------------------------------------------------
# Parsed policy data structures
# ---------------------------------------------------------------------------


@dataclass
class StepPolicy:
    """Parsed policy for a single step.

    Attributes:
        allowed_actions: Actions explicitly allowed (whitelist mode).
        denied_actions: Actions explicitly denied (blacklist mode).
        max_calls: Optional maximum invocations per run.
    """

    allowed_actions: list[str]
    denied_actions: list[str]
    max_calls: int | None = None


@dataclass
class ParsedPolicies:
    """Complete parsed policy configuration.

    Attributes:
        mode: Global enforcement mode (whitelist or blacklist).
        defaults: Default actions applied when no step-specific rule exists.
        steps: Per-step policy definitions.
        overrides: Per-slug override policies.
        raw: The original raw YAML dict for introspection.
    """

    mode: str
    defaults: StepPolicy
    steps: dict[str, StepPolicy]
    overrides: dict[str, dict[str, Any]]
    raw: dict[str, Any]


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Load a YAML file safely, returning empty dict on failure."""
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.error("Failed to load policy YAML %s: %s", path, exc)
        return {}


# ---------------------------------------------------------------------------
# Parse helpers
# ---------------------------------------------------------------------------


def _parse_step_policy(raw: dict[str, Any] | None) -> StepPolicy:
    """Parse a step policy from a raw YAML dict."""
    if not raw or not isinstance(raw, dict):
        return StepPolicy(allowed_actions=[], denied_actions=[])

    allowed = raw.get("allowed_actions", [])
    if not isinstance(allowed, list):
        allowed = []

    denied = raw.get("denied_actions", [])
    if not isinstance(denied, list):
        denied = []

    max_calls = raw.get("max_calls")
    if max_calls is not None:
        try:
            max_calls = int(max_calls)
        except (ValueError, TypeError):
            max_calls = None

    return StepPolicy(
        allowed_actions=[str(a) for a in allowed],
        denied_actions=[str(a) for a in denied],
        max_calls=max_calls,
    )


def _parse_policies(raw: dict[str, Any]) -> ParsedPolicies:
    """Parse a raw YAML dict into a structured ParsedPolicies object."""
    mode = raw.get("mode", MODE_WHITELIST)
    if mode not in _VALID_MODES:
        logger.warning(
            "Invalid policy mode '%s', falling back to '%s'",
            mode,
            MODE_WHITELIST,
        )
        mode = MODE_WHITELIST

    # Defaults
    defaults_raw = raw.get("defaults", {})
    defaults = _parse_step_policy(defaults_raw)

    # Steps
    steps: dict[str, StepPolicy] = {}
    steps_raw = raw.get("steps", {})
    if isinstance(steps_raw, dict):
        for step_id, step_data in steps_raw.items():
            steps[str(step_id)] = _parse_step_policy(step_data)

    # Overrides
    overrides: dict[str, dict[str, Any]] = {}
    overrides_raw = raw.get("overrides", {})
    if isinstance(overrides_raw, dict):
        for slug, slug_data in overrides_raw.items():
            if isinstance(slug_data, dict):
                overrides[str(slug)] = slug_data

    return ParsedPolicies(
        mode=mode,
        defaults=defaults,
        steps=steps,
        overrides=overrides,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# PolicyLimiter
# ---------------------------------------------------------------------------


class PolicyLimiter:
    """Policy limits enforcer for the MCE pipeline.

    Loads policies from YAML, caches with ETag (mtime-based), and checks
    step/action pairs against whitelist or blacklist rules.

    Parameters
    ----------
    policies_path:
        Path to the policies YAML file.  Defaults to ``policies.yaml``
        shipped alongside this module.
    config:
        Optional ``CascadeConfig`` instance for per-slug override
        resolution.  When a slug is provided to ``check()``, the config
        cascade is consulted for slug-specific policy overrides.
    hook_bus:
        Optional ``HookBus`` instance.  When provided, denied actions
        emit ``on_policy_denied`` events for observability.
    """

    def __init__(
        self,
        policies_path: Path | None = None,
        *,
        config: Any | None = None,
        hook_bus: Any | None = None,
    ) -> None:
        self._path = policies_path or _DEFAULT_POLICIES_PATH
        self._config = config
        self._hook_bus = hook_bus

        # ETag cache state
        self._cached_etag: float | None = None
        self._policies: ParsedPolicies | None = None

        # Call tracking (for max_calls enforcement)
        self._call_counts: dict[str, int] = {}

    # -- Loading with ETag Cache -------------------------------------------

    def load_policies(self, path: Path | None = None) -> ParsedPolicies:
        """Load policies from YAML with ETag-based caching.

        If the file's mtime has not changed since the last load, the
        cached policies are returned without re-reading the file.

        Args:
            path: Override the configured policies path.  If None, uses
                  the path from construction.

        Returns:
            Parsed policies object.

        Raises:
            FileNotFoundError: If the policies file does not exist and
                               no cached policies are available.
        """
        target = path or self._path

        # Compute ETag from file mtime
        try:
            current_etag = os.path.getmtime(target)
        except OSError:
            if self._policies is not None:
                logger.warning(
                    "Policies file '%s' not found, using cached policies",
                    target,
                )
                return self._policies
            raise FileNotFoundError(f"Policies file not found: {target}")

        # ETag cache hit
        if (
            self._policies is not None
            and self._cached_etag is not None
            and current_etag == self._cached_etag
        ):
            logger.debug("Policies cache hit (ETag unchanged)")
            return self._policies

        # Cache miss -- reload
        raw = _load_yaml_safe(target)
        if not raw:
            if self._policies is not None:
                logger.warning(
                    "Failed to parse policies from '%s', using cached",
                    target,
                )
                return self._policies
            # Return permissive defaults if nothing loaded
            raw = {"mode": MODE_WHITELIST, "defaults": {"allowed_actions": []}, "steps": {}}

        self._policies = _parse_policies(raw)
        self._cached_etag = current_etag

        logger.info(
            "Loaded policies: mode=%s, %d steps, %d overrides",
            self._policies.mode,
            len(self._policies.steps),
            len(self._policies.overrides),
        )

        return self._policies

    # -- Policy Check ------------------------------------------------------

    def check(
        self,
        step_id: str,
        action: str,
        *,
        slug: str | None = None,
    ) -> PolicyDecision:
        """Check if a step is allowed to perform an action.

        Resolution order:
            1. Per-slug override (if slug provided and override exists)
            2. Per-step policy
            3. Global defaults

        When mode is whitelist: action must be in allowed_actions.
        When mode is blacklist: action must NOT be in denied_actions.

        Args:
            step_id: Pipeline step identifier.
            action: Action the step wants to perform.
            slug: Optional persona slug for per-slug override lookup.

        Returns:
            PolicyDecision with allowed/denied status and reason.
        """
        # Ensure policies are loaded
        if self._policies is None:
            self.load_policies()

        assert self._policies is not None  # guaranteed after load

        # Resolve effective mode and step policy
        mode, step_policy = self._resolve_effective_policy(
            step_id,
            slug,
        )

        # Check max_calls if configured
        if step_policy.max_calls is not None:
            count = self._call_counts.get(step_id, 0)
            if count >= step_policy.max_calls:
                decision = PolicyDecision(
                    allowed=False,
                    reason=(
                        f"Step '{step_id}' exceeded max_calls limit "
                        f"({count}/{step_policy.max_calls})"
                    ),
                    step_id=step_id,
                    action=action,
                )
                self._emit_denied(decision)
                return decision

        # Mode-based check
        if mode == MODE_WHITELIST:
            decision = self._check_whitelist(step_id, action, step_policy)
        else:
            decision = self._check_blacklist(step_id, action, step_policy)

        # Track call count on allowed
        if decision.allowed:
            self._call_counts[step_id] = self._call_counts.get(step_id, 0) + 1

        # Emit hook on denied
        if not decision.allowed:
            self._emit_denied(decision)

        return decision

    # -- Internal Resolution -----------------------------------------------

    def _resolve_effective_policy(
        self,
        step_id: str,
        slug: str | None,
    ) -> tuple[str, StepPolicy]:
        """Resolve the effective mode and step policy.

        Priority: slug override > step-specific > global defaults.
        """
        assert self._policies is not None

        mode = self._policies.mode

        # Check for per-slug override first
        if slug and slug in self._policies.overrides:
            override = self._policies.overrides[slug]

            # Slug can override the mode
            slug_mode = override.get("mode")
            if slug_mode in _VALID_MODES:
                mode = slug_mode

            # Slug can override step policies
            slug_steps = override.get("steps", {})
            if isinstance(slug_steps, dict) and step_id in slug_steps:
                return mode, _parse_step_policy(slug_steps[step_id])

        # Step-specific policy
        if step_id in self._policies.steps:
            return mode, self._policies.steps[step_id]

        # Global defaults
        return mode, self._policies.defaults

    def _check_whitelist(
        self,
        step_id: str,
        action: str,
        policy: StepPolicy,
    ) -> PolicyDecision:
        """Check action against whitelist policy."""
        if action in policy.allowed_actions:
            return PolicyDecision(
                allowed=True,
                reason=f"Action '{action}' is whitelisted for step '{step_id}'",
                step_id=step_id,
                action=action,
            )
        return PolicyDecision(
            allowed=False,
            reason=(
                f"Action '{action}' is not whitelisted for step '{step_id}'. "
                f"Allowed: {policy.allowed_actions}"
            ),
            step_id=step_id,
            action=action,
        )

    def _check_blacklist(
        self,
        step_id: str,
        action: str,
        policy: StepPolicy,
    ) -> PolicyDecision:
        """Check action against blacklist policy."""
        if action in policy.denied_actions:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Action '{action}' is blacklisted for step '{step_id}'. "
                    f"Denied: {policy.denied_actions}"
                ),
                step_id=step_id,
                action=action,
            )
        return PolicyDecision(
            allowed=True,
            reason=f"Action '{action}' is not blacklisted for step '{step_id}'",
            step_id=step_id,
            action=action,
        )

    # -- Hook Emission -----------------------------------------------------

    def _emit_denied(self, decision: PolicyDecision) -> None:
        """Emit on_policy_denied hook when an action is blocked."""
        if self._hook_bus is None:
            return

        try:
            self._hook_bus.emit(
                "on_policy_denied",
                {
                    "step_id": decision.step_id,
                    "action": decision.action,
                    "reason": decision.reason,
                    "allowed": decision.allowed,
                },
            )
        except Exception as exc:
            # Hook emission failure must never block the policy check
            logger.error("Failed to emit on_policy_denied: %s", exc)

    # -- Introspection -----------------------------------------------------

    @property
    def policies(self) -> ParsedPolicies | None:
        """Current loaded policies, or None if not yet loaded."""
        return self._policies

    @property
    def mode(self) -> str:
        """Current enforcement mode."""
        if self._policies is None:
            return MODE_WHITELIST
        return self._policies.mode

    @property
    def call_counts(self) -> dict[str, int]:
        """Current call counts per step."""
        return dict(self._call_counts)

    @property
    def cached_etag(self) -> float | None:
        """Current cached ETag (file mtime), or None if not loaded."""
        return self._cached_etag

    def reset_call_counts(self) -> None:
        """Reset all per-step call counters.

        Should be called at the start of each pipeline run.
        """
        self._call_counts.clear()

    def __repr__(self) -> str:
        if self._policies is None:
            return "PolicyLimiter(not loaded)"
        return (
            f"PolicyLimiter(mode={self._policies.mode!r}, "
            f"steps={len(self._policies.steps)}, "
            f"overrides={len(self._policies.overrides)}, "
            f"etag={self._cached_etag})"
        )
