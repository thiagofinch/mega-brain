"""
plugin_loader.py -- Plugin Lifecycle Manager for MCE Pipeline
=============================================================

Orchestrates the full lifecycle of StepPlugin plugins: discovery from
multiple directories, validation of ABC compliance, registration in the
StepRegistry, and teardown/cleanup.

Architecture
------------
::

    PluginLoader
      |-- discover(directory)       # scan .py files, find StepPlugin subclasses
      |-- validate(plugin)          # check ABC contract compliance
      |-- register(plugin, registry)# validate then register
      |-- load_all(dirs, registry)  # multi-dir discover + validate + register
      |-- cleanup(registry)         # unregister all tracked plugins

    Flow:
      directories[] --> discover() --> validate() --> register() --> StepRegistry
                            |              |
                       error? skip     error? skip
                       (log warning)   (log warning)

Design Decisions
~~~~~~~~~~~~~~~~
- PluginLoader is stateless per operation but tracks registered IDs for
  cleanup.  This allows a clean teardown between pipeline runs without
  leaving orphan plugins in the registry.
- Invalid plugins are logged and skipped, never crash the pipeline.
  This follows the "let it degrade gracefully" principle -- a broken
  plugin should not take down the entire pipeline.
- Validation checks 4 things: isinstance(StepPlugin), id format,
  version format, depends_on format.  Structural checks only -- no
  runtime execution during validation.
- Deduplication follows first-wins: if a step_id is already registered,
  subsequent discoveries with the same ID are skipped with a warning.

Constraints
~~~~~~~~~~~
- stdlib only (re, importlib, pathlib, logging).
- No LLM calls, no network, no file writes.
- Thread-safe for reads; registration is append-only per load_all call.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-2.6 -- Plugin Lifecycle
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from engine.intelligence.pipeline.mce.step_plugin import StepPlugin
from engine.intelligence.pipeline.mce.step_registry import StepRegistry

logger = logging.getLogger("mce.plugin_loader")

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

# Semver-ish: major.minor.patch with optional pre-release
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?$")

# Step ID: kebab-case, 2-80 chars
_STEP_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,78}[a-z0-9]$")


@dataclass
class PluginValidationResult:
    """Result of validating a StepPlugin instance.

    Attributes:
        valid: True if the plugin passes all validation checks.
        errors: List of human-readable error descriptions.
        plugin_id: The plugin's declared ID (may be None if validation
                   failed before ID could be read).
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    plugin_id: Optional[str] = None

    def __bool__(self) -> bool:
        return self.valid

    @staticmethod
    def ok(plugin_id: str) -> PluginValidationResult:
        return PluginValidationResult(valid=True, plugin_id=plugin_id)

    @staticmethod
    def fail(errors: list[str], plugin_id: Optional[str] = None) -> PluginValidationResult:
        return PluginValidationResult(valid=False, errors=errors, plugin_id=plugin_id)


# ---------------------------------------------------------------------------
# PluginLoader
# ---------------------------------------------------------------------------


class PluginLoader:
    """Manages the full lifecycle of MCE pipeline step plugins.

    Discovers plugins from filesystem directories, validates them against
    the StepPlugin ABC contract, registers them in a StepRegistry, and
    can clean up (unregister) all plugins it previously registered.

    Example::

        loader = PluginLoader()
        registry = StepRegistry()

        # Load from multiple directories (built-in > custom > user)
        stats = loader.load_all(
            directories=["core/steps", "plugins/steps", "/tmp/user-steps"],
            registry=registry,
        )
        print(f"Loaded {stats['registered']} plugins, skipped {stats['skipped']}")

        # Later, teardown
        loader.cleanup(registry)
    """

    def __init__(self) -> None:
        self._registered_ids: list[str] = []

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, directory: str | Path) -> list[StepPlugin]:
        """Scan a directory for .py files containing StepPlugin subclasses.

        Imports each .py file (skipping _-prefixed files), inspects
        classes, instantiates concrete StepPlugin subclasses.

        Invalid files or classes that fail instantiation are logged as
        warnings and skipped -- never crashes.

        Args:
            directory: Path to scan.  Must exist and be a directory.

        Returns:
            List of instantiated StepPlugin instances found in the
            directory.  May be empty if no valid plugins exist.

        Raises:
            FileNotFoundError: If directory does not exist.
        """
        dir_path = Path(directory).resolve()

        if not dir_path.is_dir():
            raise FileNotFoundError(f"Plugin directory does not exist: {dir_path}")

        plugins: list[StepPlugin] = []
        py_files = sorted(dir_path.glob("*.py"))

        for py_file in py_files:
            if py_file.name.startswith("_"):
                continue

            try:
                classes = StepRegistry._load_plugins_from_file(py_file)
                for cls in classes:
                    try:
                        instance = cls()
                        plugins.append(instance)
                        logger.debug(
                            "Discovered plugin '%s' v%s from %s",
                            instance.id,
                            instance.version,
                            py_file.name,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Failed to instantiate %s from %s: %s",
                            cls.__name__,
                            py_file.name,
                            exc,
                        )
            except Exception as exc:
                logger.warning(
                    "Failed to import %s: %s",
                    py_file.name,
                    exc,
                )

        logger.info(
            "Discovered %d plugin(s) in %s",
            len(plugins),
            dir_path,
        )
        return plugins

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, plugin: StepPlugin) -> PluginValidationResult:
        """Validate a StepPlugin instance for ABC contract compliance.

        Checks:
        1. Is an instance of StepPlugin (type check).
        2. id property returns a valid kebab-case string.
        3. version property returns a valid semver string.
        4. depends_on property returns a list of strings.
        5. step_type property returns a valid StepType enum value.
        6. execute and validate_input are callable.

        Args:
            plugin: The StepPlugin instance to validate.

        Returns:
            PluginValidationResult with pass/fail and error details.
        """
        errors: list[str] = []
        plugin_id: Optional[str] = None

        # 1. Type check
        if not isinstance(plugin, StepPlugin):
            return PluginValidationResult.fail(
                [f"Not a StepPlugin instance: {type(plugin).__name__}"]
            )

        # 2. ID format
        try:
            plugin_id = plugin.id
            if not isinstance(plugin_id, str):
                errors.append(f"id must be str, got {type(plugin_id).__name__}")
            elif not _STEP_ID_RE.match(plugin_id):
                errors.append(
                    f"id '{plugin_id}' does not match kebab-case pattern "
                    f"(2-80 chars, lowercase alphanumeric + hyphens)"
                )
        except Exception as exc:
            errors.append(f"id property raised: {exc}")

        # 3. Version format
        try:
            version = plugin.version
            if not isinstance(version, str):
                errors.append(f"version must be str, got {type(version).__name__}")
            elif not _SEMVER_RE.match(version):
                errors.append(
                    f"version '{version}' does not match semver pattern "
                    f"(e.g., '1.0.0' or '1.0.0-beta.1')"
                )
        except Exception as exc:
            errors.append(f"version property raised: {exc}")

        # 4. depends_on format
        try:
            depends_on = plugin.depends_on
            if not isinstance(depends_on, list):
                errors.append(f"depends_on must be list, got {type(depends_on).__name__}")
            else:
                for i, dep in enumerate(depends_on):
                    if not isinstance(dep, str):
                        errors.append(f"depends_on[{i}] must be str, got {type(dep).__name__}")
        except Exception as exc:
            errors.append(f"depends_on property raised: {exc}")

        # 5. step_type
        try:
            from engine.intelligence.pipeline.mce.step_plugin import StepType

            step_type = plugin.step_type
            if not isinstance(step_type, StepType):
                errors.append(f"step_type must be StepType enum, got {type(step_type).__name__}")
        except Exception as exc:
            errors.append(f"step_type property raised: {exc}")

        # 6. Callable check
        if not callable(getattr(plugin, "execute", None)):
            errors.append("execute is not callable")
        if not callable(getattr(plugin, "validate_input", None)):
            errors.append("validate_input is not callable")

        if errors:
            return PluginValidationResult.fail(errors, plugin_id=plugin_id)

        return PluginValidationResult.ok(plugin_id=plugin_id)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, plugin: StepPlugin, registry: StepRegistry) -> PluginValidationResult:
        """Validate and register a single plugin in the registry.

        Runs full validation first.  If valid and not a duplicate,
        registers in the StepRegistry.

        Args:
            plugin: The StepPlugin instance to register.
            registry: The StepRegistry to add the plugin to.

        Returns:
            PluginValidationResult.  If registration succeeds, valid=True.
            If validation fails or duplicate detected, valid=False with
            error details.
        """
        result = self.validate(plugin)
        if not result:
            logger.warning(
                "Plugin validation failed for '%s': %s",
                result.plugin_id or "<unknown>",
                "; ".join(result.errors),
            )
            return result

        step_id = plugin.id

        # Dedup: first wins
        if step_id in registry:
            msg = (
                f"Step '{step_id}' already registered -- "
                f"skipping duplicate from {plugin.__class__.__name__}"
            )
            logger.warning(msg)
            return PluginValidationResult.fail([msg], plugin_id=step_id)

        try:
            registry.register(plugin)
            self._registered_ids.append(step_id)
            logger.info(
                "Registered plugin '%s' v%s (%s)",
                step_id,
                plugin.version,
                plugin.step_type.value,
            )
            return PluginValidationResult.ok(plugin_id=step_id)
        except (TypeError, ValueError) as exc:
            return PluginValidationResult.fail([f"Registration failed: {exc}"], plugin_id=step_id)

    # ------------------------------------------------------------------
    # Multi-directory loading
    # ------------------------------------------------------------------

    def load_all(
        self,
        directories: list[str | Path],
        registry: StepRegistry,
    ) -> dict[str, int]:
        """Discover, validate, and register plugins from multiple directories.

        Scans directories in order.  First-wins deduplication: if a
        step_id is found in an earlier directory, later duplicates are
        skipped.  This ensures:
          - core/steps/ (built-in) takes priority over
          - plugins/steps/ (custom) which takes priority over
          - user_dir (user-provided)

        Non-existent directories are logged as warnings and skipped.

        Args:
            directories: List of directory paths to scan, in priority
                         order (first = highest priority).
            registry: The StepRegistry to populate.

        Returns:
            Stats dict with keys:
            - ``registered``: Number of plugins successfully registered.
            - ``skipped``: Number of plugins skipped (invalid or duplicate).
            - ``directories_scanned``: Number of valid directories scanned.
            - ``directories_missing``: Number of directories that don't exist.
            - ``errors``: List of error messages for skipped plugins.
        """
        stats: dict[str, int | list[str]] = {
            "registered": 0,
            "skipped": 0,
            "directories_scanned": 0,
            "directories_missing": 0,
            "errors": [],
        }

        for directory in directories:
            dir_path = Path(directory).resolve()

            if not dir_path.is_dir():
                logger.warning(
                    "Plugin directory does not exist, skipping: %s",
                    dir_path,
                )
                stats["directories_missing"] += 1
                continue

            stats["directories_scanned"] += 1

            try:
                plugins = self.discover(directory)
            except Exception as exc:
                logger.warning(
                    "Discovery failed for %s: %s",
                    dir_path,
                    exc,
                )
                stats["errors"].append(f"Discovery failed for {dir_path}: {exc}")
                continue

            for plugin in plugins:
                result = self.register(plugin, registry)
                if result:
                    stats["registered"] += 1
                else:
                    stats["skipped"] += 1
                    stats["errors"].extend(result.errors)

        logger.info(
            "load_all complete: %d registered, %d skipped, %d dirs scanned, %d dirs missing",
            stats["registered"],
            stats["skipped"],
            stats["directories_scanned"],
            stats["directories_missing"],
        )
        return stats

    # ------------------------------------------------------------------
    # Cleanup / Teardown
    # ------------------------------------------------------------------

    def cleanup(self, registry: StepRegistry) -> int:
        """Unregister all plugins that were registered by this loader.

        Iterates through tracked IDs and removes each from the registry.
        Clears the internal tracking list afterward.

        Args:
            registry: The StepRegistry to clean up.

        Returns:
            Number of plugins successfully unregistered.
        """
        removed = 0
        for step_id in self._registered_ids:
            if registry.unregister(step_id):
                removed += 1
                logger.debug("Cleanup: unregistered '%s'", step_id)
            else:
                logger.debug(
                    "Cleanup: '%s' was already removed from registry",
                    step_id,
                )

        self._registered_ids.clear()
        logger.info("Cleanup complete: %d plugin(s) unregistered", removed)
        return removed

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def registered_ids(self) -> list[str]:
        """List of step IDs registered by this loader instance."""
        return list(self._registered_ids)

    def __repr__(self) -> str:
        return f"PluginLoader(tracked={len(self._registered_ids)})"
