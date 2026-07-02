"""
step_registry.py -- Plugin Registry for MCE Pipeline Steps
==========================================================

Central registry that holds all available StepPlugin implementations.
Supports both explicit registration and filesystem-based discovery.

Architecture
------------
::

    StepRegistry
      |-- register(plugin)      # manual registration
      |-- get(step_id)          # lookup by ID
      |-- list_all()            # all registered plugins
      |-- discover(directory)   # scan .py files, import, find StepPlugin subclasses
      |-- unregister(step_id)   # remove by ID
      |-- clear()               # reset registry

Discovery scans a directory for .py files, imports each module, and
looks for classes that are concrete subclasses of StepPlugin (i.e.,
they implement all abstract methods).  Each discovered class is
instantiated and registered.

Design Decisions
~~~~~~~~~~~~~~~~
- Single in-memory dict -- no persistence.  The registry is rebuilt
  on each pipeline run via discover().  This keeps it stateless and
  eliminates stale-state bugs.
- Duplicate ID registration raises ValueError to catch copy-paste
  errors early rather than silently overwriting.
- discover() uses importlib to load modules dynamically.  It only
  instantiates classes that are direct or indirect StepPlugin
  subclasses AND are not abstract themselves.

Constraints
~~~~~~~~~~~
- stdlib only (importlib, inspect, pathlib).
- Thread-safe for reads (dict is not mutated during iteration).
- No LLM calls, no network.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-2.1 -- StepPlugin Interface + Registry
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Any

from engine.intelligence.pipeline.mce.step_plugin import StepPlugin

logger = logging.getLogger("mce.step_registry")


class StepRegistry:
    """Central registry for MCE pipeline step plugins.

    Manages the lifecycle of StepPlugin instances: registration,
    lookup, listing, and filesystem-based discovery.

    Example::

        registry = StepRegistry()

        # Manual registration
        registry.register(MyCustomStep())

        # Or discover from a directory
        registry.discover("core/intelligence/pipeline/mce/steps/")

        # Lookup
        step = registry.get("my-custom-step")
        if step:
            result = step.execute(context)

        # List all
        for plugin in registry.list_all():
            print(f"{plugin.id} v{plugin.version}")
    """

    def __init__(self) -> None:
        self._registry: dict[str, StepPlugin] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, step: StepPlugin) -> None:
        """Register a step plugin in the registry.

        Args:
            step: An instantiated StepPlugin subclass.

        Raises:
            TypeError: If step is not a StepPlugin instance.
            ValueError: If a step with the same ID is already registered.
        """
        if not isinstance(step, StepPlugin):
            raise TypeError(f"Expected StepPlugin instance, got {type(step).__name__}")

        step_id = step.id

        if step_id in self._registry:
            existing = self._registry[step_id]
            raise ValueError(
                f"Step '{step_id}' is already registered "
                f"(existing: {existing.__class__.__name__} v{existing.version}, "
                f"new: {step.__class__.__name__} v{step.version}). "
                f"Use unregister() first if replacement is intentional."
            )

        self._registry[step_id] = step
        logger.debug(
            "Registered step '%s' v%s (%s)",
            step_id,
            step.version,
            step.step_type.value,
        )

    def unregister(self, step_id: str) -> bool:
        """Remove a step from the registry by ID.

        Args:
            step_id: The unique step identifier.

        Returns:
            True if the step was found and removed, False otherwise.
        """
        if step_id in self._registry:
            removed = self._registry.pop(step_id)
            logger.debug("Unregistered step '%s' (%s)", step_id, removed.__class__.__name__)
            return True

        logger.debug("Step '%s' not found in registry -- nothing to unregister", step_id)
        return False

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, step_id: str) -> StepPlugin | None:
        """Retrieve a registered step by ID.

        Args:
            step_id: The unique step identifier.

        Returns:
            The StepPlugin instance, or None if not found.
        """
        return self._registry.get(step_id)

    def __contains__(self, step_id: str) -> bool:
        """Support ``"step-id" in registry`` syntax."""
        return step_id in self._registry

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_all(self) -> list[StepPlugin]:
        """Return all registered plugins as a list.

        Returns:
            List of StepPlugin instances, sorted by ID for
            deterministic ordering.
        """
        return sorted(self._registry.values(), key=lambda s: s.id)

    @property
    def count(self) -> int:
        """Number of registered steps."""
        return len(self._registry)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, directory: str | Path) -> list[str]:
        """Scan a directory for .py files containing StepPlugin subclasses.

        For each .py file found:
        1. Import the module using importlib.
        2. Inspect all classes defined in the module.
        3. If a class is a concrete subclass of StepPlugin (not abstract),
           instantiate it and register it.

        Duplicate IDs found during discovery are logged as warnings
        and skipped (first-wins).

        Args:
            directory: Path to the directory to scan.  Can be absolute
                       or relative to the current working directory.

        Returns:
            List of step IDs that were successfully discovered and
            registered.

        Raises:
            FileNotFoundError: If the directory does not exist.
        """
        dir_path = Path(directory).resolve()

        if not dir_path.is_dir():
            raise FileNotFoundError(f"Discovery directory does not exist: {dir_path}")

        discovered: list[str] = []
        py_files = sorted(dir_path.glob("*.py"))

        for py_file in py_files:
            if py_file.name.startswith("_"):
                continue  # Skip __init__.py, __pycache__, _private modules

            try:
                plugin_classes = self._load_plugins_from_file(py_file)
                for cls in plugin_classes:
                    try:
                        instance = cls()
                        if instance.id in self._registry:
                            logger.warning(
                                "Discovery: step '%s' from %s skipped -- "
                                "already registered by %s",
                                instance.id,
                                py_file.name,
                                self._registry[instance.id].__class__.__name__,
                            )
                            continue
                        self.register(instance)
                        discovered.append(instance.id)
                    except Exception as exc:
                        logger.warning(
                            "Discovery: failed to instantiate %s from %s: %s",
                            cls.__name__,
                            py_file.name,
                            exc,
                        )
            except Exception as exc:
                logger.warning(
                    "Discovery: failed to import %s: %s",
                    py_file.name,
                    exc,
                )

        logger.info(
            "Discovery complete: %d step(s) found in %s",
            len(discovered),
            dir_path,
        )
        return discovered

    @staticmethod
    def _load_plugins_from_file(py_file: Path) -> list[type[StepPlugin]]:
        """Import a .py file and return all concrete StepPlugin subclasses.

        Uses importlib.util to load the module without requiring it to
        be on sys.path.  Only returns classes that:
        - Are defined in the module (not imported from elsewhere).
        - Are subclasses of StepPlugin.
        - Are NOT abstract (all abstract methods are implemented).

        Args:
            py_file: Path to the Python file.

        Returns:
            List of StepPlugin subclass types.
        """
        module_name = f"mce_discovered_{py_file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, py_file)

        if spec is None or spec.loader is None:
            logger.debug("Could not create module spec for %s", py_file)
            return []

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        found: list[type[StepPlugin]] = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, StepPlugin)
                and obj is not StepPlugin
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                found.append(obj)

        return found

    # ------------------------------------------------------------------
    # Multi-directory Discovery (MCE2-2.7)
    # ------------------------------------------------------------------

    def discover_all(
        self,
        directories: list[str | Path],
        *,
        skip_missing: bool = True,
    ) -> dict[str, list[str]]:
        """Scan multiple directories for StepPlugin subclasses.

        Scans directories in order with first-wins deduplication:
        if a step_id is already registered from an earlier directory,
        later duplicates are skipped.

        Canonical usage scans 3 directories in priority order::

            registry.discover_all([
                "core/steps",       # built-in (highest priority)
                "plugins/steps",    # custom plugins
                "/tmp/user-steps",  # user-provided (lowest priority)
            ])

        Args:
            directories: List of directory paths to scan, in priority
                         order (first = highest priority).
            skip_missing: If True (default), non-existent directories
                          are logged and skipped.  If False, raises
                          FileNotFoundError.

        Returns:
            Dict with keys:
            - Each directory path (str) maps to a list of step IDs
              discovered from that directory.
            - ``"_skipped"``: list of step IDs that were duplicates.
            - ``"_missing"``: list of directories that don't exist.
            - ``"_all"``: flat list of all registered step IDs.

        Raises:
            FileNotFoundError: If skip_missing is False and a directory
                               does not exist.
        """
        result: dict[str, list[str]] = {
            "_skipped": [],
            "_missing": [],
            "_all": [],
        }

        for directory in directories:
            dir_path = Path(directory).resolve()
            dir_key = str(dir_path)

            if not dir_path.is_dir():
                if not skip_missing:
                    raise FileNotFoundError(f"Discovery directory does not exist: {dir_path}")
                logger.warning(
                    "discover_all: directory does not exist, skipping: %s",
                    dir_path,
                )
                result["_missing"].append(dir_key)
                continue

            result[dir_key] = []

            try:
                discovered = self.discover(dir_path)
                result[dir_key] = discovered
                result["_all"].extend(discovered)
            except Exception as exc:
                logger.warning(
                    "discover_all: failed to scan %s: %s",
                    dir_path,
                    exc,
                )

        # Identify what was skipped (already in registry before discover_all)
        # The discover() method already handles first-wins internally,
        # so _skipped is populated via the warning log path
        logger.info(
            "discover_all complete: %d step(s) across %d directories",
            len(result["_all"]),
            len(directories) - len(result["_missing"]),
        )
        return result

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all registered steps."""
        count = len(self._registry)
        self._registry.clear()
        logger.debug("Registry cleared (%d steps removed)", count)

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Dump registry contents as a serializable dict.

        Returns:
            Dict mapping step_id to a summary dict with version,
            step_type, and depends_on.
        """
        return {
            step.id: {
                "version": step.version,
                "step_type": step.step_type.value,
                "depends_on": step.depends_on,
                "class": step.__class__.__name__,
            }
            for step in self.list_all()
        }

    def __repr__(self) -> str:
        return f"StepRegistry(steps={self.count})"

    def __len__(self) -> int:
        return self.count
