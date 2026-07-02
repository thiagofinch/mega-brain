"""
rule_loader.py -- Declarative Rule Loader for MCE Pipeline Permission Rules
============================================================================

Loads step transition preconditions from ``step_rules.yaml`` and evaluates
them against the current pipeline state (via ``validate_step``).

This module is the declarative complement to qa_gates.py: while qa_gates
executes imperative checks per step, rule_loader reads which steps a
transition *requires* from YAML and delegates the actual validation to
qa_gates.

Architecture
------------
::

    step_rules.yaml  -->  rule_loader.py  -->  qa_gates.validate_step()
                                                   |
                     <--  RuleResult  <-----------+

The rule_loader NEVER duplicates validation logic.  It reads the YAML
to know *which* steps to validate, then calls ``validate_step()`` for each.

Override per slug
-----------------
When Config Cascade (MCE2-1.6) is available, slug-specific overrides are
loaded from::

    .claude/mission-control/mce/{slug}/step_rules_override.yaml

The override merges with (and takes precedence over) the base rules.

Import Direction
~~~~~~~~~~~~~~~~
This module imports ``qa_gates.validate_step`` -- NOT the condition functions.
The condition functions in qa_gates.py delegate to this module, so the
dependency arrow is::

    qa_gates.can_start_X()  -->  rule_loader.check_preconditions()
                                       |
                                       +--> qa_gates.validate_step()

Constraints
~~~~~~~~~~~
- stdlib + PyYAML ONLY (no external deps, no LLM calls)
- Every function is DETERMINISTIC
- Never crashes -- catches all exceptions, returns failed RuleResult with detail

Version: 1.0.0
Story: MCE2-1.5
Date: 2026-04-01
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.rule_loader")

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class RuleResult:
    """Result of evaluating preconditions for a pipeline step transition.

    Attributes:
        passed: True if ALL blocking preconditions passed.
        failed_rules: List of failed precondition descriptions.
        details: Human-readable summary of the evaluation.
        step_results: Raw validate_step results for each checked step.
    """

    passed: bool
    failed_rules: list[str] = field(default_factory=list)
    details: str = ""
    step_results: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Rule Cache (module-level singleton)
# ---------------------------------------------------------------------------

_rules_cache: dict[str, Any] | None = None
_rules_path_cached: str | None = None


def _default_rules_path() -> Path:
    """Return the default path to step_rules.yaml (same directory as this file)."""
    return Path(__file__).parent / "step_rules.yaml"


def _load_yaml_safe(path: Path) -> dict[str, Any] | None:
    """Load a YAML file safely, returning None on any error."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.warning("Failed to load YAML from %s: %s", path, exc)
        return None


# ---------------------------------------------------------------------------
# RuleLoader
# ---------------------------------------------------------------------------


class RuleLoader:
    """Loads and evaluates declarative step transition rules from YAML.

    Usage::

        loader = RuleLoader()
        result = loader.check_preconditions("chunking", slug="alex-hormozi")
        if result.passed:
            # safe to transition
            ...
        else:
            # preconditions not met
            for rule in result.failed_rules:
                print(f"Failed: {rule}")
    """

    def __init__(self, path: str | Path | None = None) -> None:
        """Initialize the RuleLoader.

        Args:
            path: Path to step_rules.yaml.  If None, uses the default
                  location (same directory as this module).
        """
        self._path = Path(path) if path else _default_rules_path()
        self._rules: dict[str, Any] | None = None

    def load_rules(self, path: str | Path | None = None) -> dict[str, Any]:
        """Load rules from YAML, with caching.

        Args:
            path: Optional override path.  If provided, replaces the
                  instance path and reloads.

        Returns:
            The parsed rules dict.  Empty dict if file missing or invalid.
        """
        if path is not None:
            self._path = Path(path)
            self._rules = None  # invalidate cache

        if self._rules is not None:
            return self._rules

        data = _load_yaml_safe(self._path)
        if data is None:
            logger.warning(
                "step_rules.yaml not found or invalid at %s -- "
                "rule_loader will return pass-through results",
                self._path,
            )
            self._rules = {}
            return self._rules

        self._rules = data
        version = data.get("version", "unknown")
        rules_count = len(data.get("rules", {}))
        logger.info(
            "Loaded step_rules.yaml v%s (%d rules) from %s",
            version,
            rules_count,
            self._path,
        )
        return self._rules

    def get_rule(self, step_id: str) -> dict[str, Any] | None:
        """Get the rule definition for a specific step_id.

        Args:
            step_id: The step identifier (e.g., "chunking", "entity_resolution").

        Returns:
            The rule dict, or None if not found.
        """
        rules = self.load_rules()
        all_rules = rules.get("rules", {})
        return all_rules.get(step_id)

    def load_slug_override(self, slug: str) -> dict[str, Any] | None:
        """Load slug-specific rule overrides (Config Cascade integration point).

        When MCE2-1.6 Config Cascade is available, this method loads
        overrides from the slug's state directory.

        Args:
            slug: Person slug (e.g., "alex-hormozi").

        Returns:
            Override rules dict, or None if no override exists.
        """
        # Resolve override path relative to the MCE state directory.
        # Uses the same directory convention as state_machine.py.
        try:
            from engine.paths import MISSION_CONTROL, ROUTING

            mce_state_dir = Path(ROUTING.get("mce_state", MISSION_CONTROL / "mce"))
        except ImportError:
            mce_state_dir = (
                Path(__file__).resolve().parent.parent.parent.parent.parent
                / ".claude"
                / "mission-control"
                / "mce"
            )

        override_path = mce_state_dir / slug / "step_rules_override.yaml"
        if not override_path.exists():
            return None

        override_data = _load_yaml_safe(override_path)
        if override_data is not None:
            logger.info("Loaded slug override rules for %s from %s", slug, override_path)
        return override_data

    def get_effective_rule(self, step_id: str, slug: str | None = None) -> dict[str, Any] | None:
        """Get the effective rule for a step, with slug override applied.

        The merge strategy is: slug override preconditions REPLACE base
        preconditions entirely (not merged).  This ensures predictable
        behavior -- a slug either uses the default rules or its own.

        Args:
            step_id: The step identifier.
            slug: Optional person slug for override lookup.

        Returns:
            The effective rule dict, or None if not found.
        """
        base_rule = self.get_rule(step_id)
        if slug is None or base_rule is None:
            return base_rule

        override_data = self.load_slug_override(slug)
        if override_data is None:
            return base_rule

        override_rules = override_data.get("rules", {})
        override_rule = override_rules.get(step_id)
        if override_rule is None:
            return base_rule

        # Merge: override replaces preconditions entirely
        merged = dict(base_rule)
        merged["preconditions"] = override_rule.get(
            "preconditions", base_rule.get("preconditions", [])
        )
        if "postconditions" in override_rule:
            merged["postconditions"] = override_rule["postconditions"]
        if "extra_kwargs" in override_rule:
            merged["extra_kwargs"] = override_rule["extra_kwargs"]

        logger.debug("Applied slug override for %s/%s", slug, step_id)
        return merged

    def check_preconditions(
        self,
        step_id: str,
        slug: str = "__unknown__",
        current_state: dict[str, Any] | None = None,
    ) -> RuleResult:
        """Evaluate preconditions for a pipeline step transition.

        Reads the rule for ``step_id`` from YAML, then calls
        ``qa_gates.validate_step()`` for each required precondition step.

        Args:
            step_id: The target step (e.g., "chunking", "entity_resolution").
            slug: Person slug for per-slug validation context.
            current_state: Optional dict of current pipeline state (unused
                          in v1, reserved for future state-based rules).

        Returns:
            RuleResult with pass/fail verdict and details.
        """
        rule = self.get_effective_rule(step_id, slug=slug)

        if rule is None:
            # No rule defined -- pass through (backward compat)
            logger.debug("No rule found for step_id=%s -- pass through", step_id)
            return RuleResult(
                passed=True,
                details=f"No declarative rule for '{step_id}' -- allowing transition",
            )

        preconditions = rule.get("preconditions", [])
        if not preconditions:
            return RuleResult(
                passed=True,
                details=f"Rule '{step_id}' has no preconditions -- allowing transition",
            )

        extra_kwargs = rule.get("extra_kwargs", {})
        failed_rules: list[str] = []
        step_results: list[dict[str, Any]] = []
        all_details: list[str] = []

        for precond in preconditions:
            step_num = precond.get("step")
            step_name = precond.get("step_name", f"step_{step_num}")
            is_blocking = precond.get("blocking", True)
            required_status = precond.get("status", "passed")

            if step_num is None:
                logger.warning("Precondition missing 'step' field in rule '%s'", step_id)
                continue

            # Delegate to qa_gates.validate_step for the actual check
            try:
                from engine.intelligence.pipeline.mce.qa_gates import validate_step

                result = validate_step(step_num, slug, **extra_kwargs)
            except Exception as exc:
                logger.warning(
                    "validate_step(%d, %s) failed: %s",
                    step_num,
                    slug,
                    exc,
                )
                result = {"passed": False, "blocking_failures": [str(exc)]}

            step_results.append(result)
            step_passed = result.get("passed", False)

            if required_status == "passed" and not step_passed:
                blocking_failures = result.get("blocking_failures", [])
                detail = (
                    f"Step {step_num} ({step_name}) FAILED"
                    f" -- blocking_failures: {blocking_failures}"
                )
                all_details.append(detail)
                if is_blocking:
                    failed_rules.append(
                        f"step {step_num} ({step_name}): {', '.join(blocking_failures)}"
                    )
            else:
                all_details.append(f"Step {step_num} ({step_name}) PASSED")

        passed = len(failed_rules) == 0
        summary = (
            f"Rule '{step_id}': {len(preconditions)} preconditions checked, "
            f"{len(failed_rules)} failed"
        )

        return RuleResult(
            passed=passed,
            failed_rules=failed_rules,
            details=summary + " | " + " | ".join(all_details),
            step_results=step_results,
        )

    def invalidate_cache(self) -> None:
        """Clear the internal rules cache, forcing a reload on next access."""
        self._rules = None
        logger.debug("Rule cache invalidated")


# ---------------------------------------------------------------------------
# Module-level convenience (singleton loader)
# ---------------------------------------------------------------------------

_default_loader: RuleLoader | None = None


def get_loader(path: str | Path | None = None) -> RuleLoader:
    """Get or create the module-level singleton RuleLoader.

    Args:
        path: Optional path override.  If provided, creates a new loader.

    Returns:
        The singleton RuleLoader instance.
    """
    global _default_loader
    if _default_loader is None or path is not None:
        _default_loader = RuleLoader(path)
    return _default_loader


def load_rules(path: str | Path | None = None) -> dict[str, Any]:
    """Convenience: load rules via the singleton loader.

    Args:
        path: Optional path override.

    Returns:
        Parsed rules dict.
    """
    return get_loader(path).load_rules()


def check_preconditions(
    step_id: str,
    slug: str = "__unknown__",
    current_state: dict[str, Any] | None = None,
) -> RuleResult:
    """Convenience: check preconditions via the singleton loader.

    Args:
        step_id: Target step identifier.
        slug: Person slug.
        current_state: Optional current state dict.

    Returns:
        RuleResult with verdict and details.
    """
    return get_loader().check_preconditions(step_id, slug, current_state)
