"""
feature_gates.py -- Feature Gate System for MCE Pipeline
=========================================================

Controls which pipeline steps, variants, and modes are active.
Provides a clean boolean/string interface so pipeline code can ask
"should I run this?" without knowing where the answer comes from.

Resolution hierarchy (first match wins):
    1. CascadeConfig (CLI > env > slug > squad > defaults.yaml)
    2. gates_config.yaml (gate-specific defaults)
    3. Hardcoded fallbacks (True for steps, "v1" for variants)

Usage::

    gates = FeatureGates(config=cascade_config)

    if gates.gate("streaming"):
        enable_streaming()

    if gates.is_step_enabled("mce_behavioral"):
        run_behavioral_step()

    template = f"prompt_{gates.variant('chunk')}.txt"
    # -> "prompt_v1.txt" or "prompt_v2.txt"

Constraints:
    - stdlib + PyYAML only (no LLM calls, no network).
    - Immutable after construction (all state set in __init__).
    - Thread-safe for reads.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-2.2
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.feature_gates")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GATES_CONFIG_PATH = Path(__file__).resolve().parent / "gates_config.yaml"

# Step gate prefix used in CascadeConfig lookups.
# e.g. "gate_step_mce_behavioral" -> checks if mce_behavioral step is on.
_STEP_PREFIX = "gate_step_"

# Variant gate prefix.  e.g. "gate_variant_chunk" -> "v1" or "v2"
_VARIANT_PREFIX = "gate_variant_"

# Mode gate prefix.  e.g. "gate_mode_qa" -> "strict" or "warning"
_MODE_PREFIX = "gate_mode_"

# Hardcoded fallbacks when nothing else provides a value
_FALLBACK_STEP = True
_FALLBACK_VARIANT = "v1"
_FALLBACK_MODE_DEFAULTS: dict[str, Any] = {
    "qa": "warning",
    "parallel": False,
    "streaming": False,
    "isolation": True,
}


# ---------------------------------------------------------------------------
# YAML loader (safe, returns empty dict on failure)
# ---------------------------------------------------------------------------


def _load_gates_yaml(path: Path) -> dict[str, Any]:
    """Load gates_config.yaml and return its contents.

    Returns an empty dict when the file does not exist, is empty,
    or contains invalid YAML -- never raises.
    """
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("Failed to load gates config %s: %s", path, exc)
        return {}


# ---------------------------------------------------------------------------
# FeatureGates
# ---------------------------------------------------------------------------


class FeatureGates:
    """Feature gate system for the MCE pipeline.

    Parameters
    ----------
    config:
        Optional ``CascadeConfig`` instance.  When provided, the cascade
        is checked first for gate overrides (using prefixed keys like
        ``gate_step_mce_behavioral`` or ``gate_mode_qa``).
    gates_config_path:
        Path to ``gates_config.yaml``.  Defaults to the file shipped
        alongside this module.  Useful for testing with a custom config.
    """

    def __init__(
        self,
        config: Any | None = None,
        *,
        gates_config_path: Path | None = None,
    ) -> None:
        self._config = config

        # Load gates_config.yaml
        path = gates_config_path or _GATES_CONFIG_PATH
        raw = _load_gates_yaml(path)

        self._steps: dict[str, bool] = {}
        steps_raw = raw.get("steps", {})
        if isinstance(steps_raw, dict):
            self._steps = {k: bool(v) for k, v in steps_raw.items()}

        self._variants: dict[str, str] = {}
        variants_raw = raw.get("variants", {})
        if isinstance(variants_raw, dict):
            self._variants = {k: str(v) for k, v in variants_raw.items()}

        self._modes: dict[str, Any] = {}
        modes_raw = raw.get("modes", {})
        if isinstance(modes_raw, dict):
            self._modes = dict(modes_raw)

        if raw:
            logger.debug(
                "Loaded gates config: %d steps, %d variants, %d modes",
                len(self._steps),
                len(self._variants),
                len(self._modes),
            )

    # -- Resolution helpers -------------------------------------------------

    def _resolve_from_cascade(self, key: str) -> Any | None:
        """Try to resolve a key from CascadeConfig.

        Returns None if no config is set or the key is not found.
        """
        if self._config is None:
            return None
        value = self._config.get(key)
        return value

    # -- Public API ---------------------------------------------------------

    def gate(self, name: str) -> bool:
        """Check if a named feature gate is enabled.

        Resolution order:
            1. CascadeConfig with prefixed key (``gate_step_*``,
               ``gate_mode_*``) or direct key
            2. gates_config.yaml (steps -> modes -> fallback)
            3. Hardcoded default (True for steps, mode-specific for modes)

        Parameters
        ----------
        name:
            Gate name.  Can be a step name (``"mce_behavioral"``),
            a mode name (``"streaming"``), or any custom gate.

        Returns
        -------
        bool
            Whether the gate is enabled.
        """
        # 1. Check cascade: prefixed step key
        cascade_val = self._resolve_from_cascade(f"{_STEP_PREFIX}{name}")
        if cascade_val is not None:
            return bool(cascade_val)

        # 1b. Check cascade: prefixed mode key
        cascade_val = self._resolve_from_cascade(f"{_MODE_PREFIX}{name}")
        if cascade_val is not None:
            return bool(cascade_val)

        # 1c. Check cascade: direct key (for modes like "parallel",
        #     "streaming" that also exist in defaults.yaml)
        cascade_val = self._resolve_from_cascade(name)
        if cascade_val is not None:
            return bool(cascade_val)

        # 2. Check gates_config.yaml: steps section
        if name in self._steps:
            return self._steps[name]

        # 2b. Check gates_config.yaml: modes section
        if name in self._modes:
            return bool(self._modes[name])

        # 3. Hardcoded fallback
        if name in _FALLBACK_MODE_DEFAULTS:
            return bool(_FALLBACK_MODE_DEFAULTS[name])

        return _FALLBACK_STEP

    def variant(self, name: str) -> str:
        """Get the active variant for a named feature.

        Resolution order:
            1. CascadeConfig with prefixed key (``gate_variant_*``)
            2. gates_config.yaml variants section
            3. Hardcoded default (``"v1"``)

        Parameters
        ----------
        name:
            Variant name (e.g. ``"chunk"``, ``"entity"``).

        Returns
        -------
        str
            The active variant string (e.g. ``"v1"``, ``"v2"``).
        """
        # 1. Check cascade
        cascade_val = self._resolve_from_cascade(f"{_VARIANT_PREFIX}{name}")
        if cascade_val is not None:
            return str(cascade_val)

        # 2. Check gates_config.yaml
        if name in self._variants:
            return self._variants[name]

        # 3. Hardcoded fallback
        return _FALLBACK_VARIANT

    def is_step_enabled(self, step_id: str) -> bool:
        """Check if a specific pipeline step should run.

        Convenience method that delegates to ``gate()`` with the step
        name.  Exists for semantic clarity in pipeline code::

            if gates.is_step_enabled("mce_behavioral"):
                run_behavioral_extraction(...)

        Parameters
        ----------
        step_id:
            Step identifier matching a key in gates_config.yaml
            ``steps`` section (e.g. ``"mce_behavioral"``,
            ``"chunking"``, ``"finalize"``).

        Returns
        -------
        bool
            Whether the step should execute.
        """
        return self.gate(step_id)

    def get_mode(self, name: str) -> Any:
        """Get a mode value (string, bool, or numeric).

        Unlike ``gate()`` which always returns bool, ``get_mode()``
        returns the raw value so callers can distinguish between
        ``qa="strict"`` and ``qa="warning"``.

        Resolution order:
            1. CascadeConfig with prefixed key (``gate_mode_*``)
            2. CascadeConfig with direct key (for ``qa_mode``,
               ``parallel``, etc. that exist in defaults.yaml)
            3. gates_config.yaml modes section
            4. Hardcoded fallback

        Parameters
        ----------
        name:
            Mode name (e.g. ``"qa"``, ``"parallel"``, ``"streaming"``).

        Returns
        -------
        Any
            The mode value.
        """
        # 1. Cascade: prefixed mode key
        cascade_val = self._resolve_from_cascade(f"{_MODE_PREFIX}{name}")
        if cascade_val is not None:
            return cascade_val

        # 1b. Cascade: direct key (e.g. "qa_mode" in defaults.yaml)
        cascade_val = self._resolve_from_cascade(name)
        if cascade_val is not None:
            return cascade_val

        # For "qa" also check "qa_mode" in cascade (defaults.yaml uses this key)
        if name == "qa":
            cascade_val = self._resolve_from_cascade("qa_mode")
            if cascade_val is not None:
                return cascade_val

        # 2. Gates config
        if name in self._modes:
            return self._modes[name]

        # 3. Hardcoded fallback
        return _FALLBACK_MODE_DEFAULTS.get(name)

    @property
    def all_steps(self) -> dict[str, bool]:
        """Return a copy of all step gates with their resolved values."""
        result: dict[str, bool] = {}
        for step_name in self._steps:
            result[step_name] = self.gate(step_name)
        return result

    @property
    def all_variants(self) -> dict[str, str]:
        """Return a copy of all variant gates with their resolved values."""
        result: dict[str, str] = {}
        for var_name in self._variants:
            result[var_name] = self.variant(var_name)
        return result

    @property
    def all_modes(self) -> dict[str, Any]:
        """Return a copy of all mode gates with their resolved values."""
        result: dict[str, Any] = {}
        for mode_name in self._modes:
            result[mode_name] = self.get_mode(mode_name)
        return result

    def __repr__(self) -> str:
        enabled = sum(1 for v in self._steps.values() if v)
        total = len(self._steps)
        has_cascade = "with" if self._config else "without"
        return (
            f"FeatureGates({enabled}/{total} steps enabled, "
            f"{len(self._variants)} variants, "
            f"{len(self._modes)} modes, "
            f"{has_cascade} cascade)"
        )
