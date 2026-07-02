"""
dag.py -- DAG Engine for MCE Pipeline Step Dependencies
=========================================================

Models step dependencies as a Directed Acyclic Graph (DAG) and provides
topological ordering, parallel group detection, critical path analysis,
and ready-step resolution.

Architecture
------------
::

    dag_definition.yaml  -->  DAGEngine.__init__(deps)
                                |
                                |-- topological_sort()   -> ordered list
                                |-- get_ready_steps()    -> next runnable
                                |-- get_parallel_groups() -> fan-out groups
                                |-- get_critical_path()  -> longest path
                                |-- mark_completed()     -> advance state
                                |-- is_complete()        -> all done?

Design Decisions
~~~~~~~~~~~~~~~~
- Kahn's algorithm for topological sort because it naturally detects
  cycles (if the sorted result is shorter than the node count, there
  is a cycle).  DFS-based topo sort would also work but does not give
  us cycle detection for free.
- DAGEngine is stateful (tracks completed steps) but immutable in its
  dependency graph.  This means one DAGEngine per pipeline execution.
- get_parallel_groups() identifies steps that share the same topological
  level (all deps satisfied at the same time).  This is the fan-out
  signal for DAGExecutor.

Constraints
~~~~~~~~~~~
- stdlib only (no external deps, no LLM calls).
- Thread-safe for reads (completed set is only mutated via mark_completed).
- Deterministic: same input always produces same sort order.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-3.1 -- DAG Engine + Refatorar Orchestrate
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.dag")


# ---------------------------------------------------------------------------
# DAG Definition Loader
# ---------------------------------------------------------------------------


def load_dag_definition(path: str | Path | None = None) -> dict[str, list[str]]:
    """Load step dependencies from dag_definition.yaml.

    Args:
        path: Path to the YAML file.  Defaults to the file shipped
              alongside this module.

    Returns:
        Dict mapping step_id -> list of dependency step_ids.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ValueError: If the YAML structure is invalid.
    """
    if path is None:
        path = Path(__file__).resolve().parent / "dag_definition.yaml"
    else:
        path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"DAG definition not found: {path}")

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict) or "steps" not in raw:
        raise ValueError(
            f"Invalid DAG definition: expected dict with 'steps' key, " f"got {type(raw).__name__}"
        )

    steps = raw["steps"]
    if not isinstance(steps, dict):
        raise ValueError(f"Invalid 'steps' section: expected dict, got {type(steps).__name__}")

    # Normalize: ensure every value is a list of strings
    result: dict[str, list[str]] = {}
    for step_id, deps in steps.items():
        if deps is None:
            result[str(step_id)] = []
        elif isinstance(deps, list):
            result[str(step_id)] = [str(d) for d in deps]
        else:
            raise ValueError(
                f"Invalid deps for step '{step_id}': expected list or null, "
                f"got {type(deps).__name__}"
            )

    return result


# ---------------------------------------------------------------------------
# DAGEngine
# ---------------------------------------------------------------------------


class DAGEngine:
    """Directed Acyclic Graph engine for MCE pipeline step dependencies.

    Accepts a dependency map and provides topological ordering,
    ready-step detection, parallel group identification, and
    critical path analysis.

    Args:
        dependencies: Dict mapping step_id -> list of dependency step_ids.
                      Steps with no dependencies should map to an empty list.

    Raises:
        ValueError: If a circular dependency is detected during construction.

    Example::

        deps = {
            "ingesting": [],
            "batching": ["ingesting"],
            "chunking": ["batching"],
            "mce_behavioral": ["insight_extraction"],
            "mce_identity": ["insight_extraction"],
            "mce_voice": ["insight_extraction"],
            "identity_checkpoint": ["mce_behavioral", "mce_identity", "mce_voice"],
        }
        dag = DAGEngine(deps)
        order = dag.topological_sort()
        ready = dag.get_ready_steps()  # -> ["ingesting"]
    """

    def __init__(self, dependencies: dict[str, list[str]]) -> None:
        self._deps = dict(dependencies)  # step -> [deps]
        self._completed: set[str] = set()
        self._all_steps: list[str] = list(dependencies.keys())

        # Build reverse adjacency (step -> list of dependents)
        self._dependents: dict[str, list[str]] = defaultdict(list)
        for step, deps in self._deps.items():
            for dep in deps:
                self._dependents[dep].append(step)

        # Validate: all deps reference existing steps
        all_step_ids = set(self._all_steps)
        for step, deps in self._deps.items():
            for dep in deps:
                if dep not in all_step_ids:
                    raise ValueError(
                        f"Step '{step}' depends on '{dep}' which is not "
                        f"defined in the dependency map"
                    )

        # Pre-compute and validate (will raise on cycle)
        self._topo_order = self._kahn_sort()
        self._levels = self._compute_levels()
        self._critical_path = self._compute_critical_path()

        logger.debug(
            "DAGEngine initialized: %d steps, %d levels, critical path length=%d",
            len(self._all_steps),
            len(self._levels),
            len(self._critical_path),
        )

    # -- Topological Sort (Kahn's Algorithm) --------------------------------

    def _kahn_sort(self) -> list[str]:
        """Compute topological order using Kahn's algorithm.

        Returns:
            Ordered list of step IDs.

        Raises:
            ValueError: If a cycle is detected (sorted count < total count).
        """
        # Build in-degree map
        in_degree: dict[str, int] = {s: 0 for s in self._all_steps}
        for step, deps in self._deps.items():
            in_degree[step] = len(deps)

        # Start with zero-degree nodes (no dependencies)
        queue: deque[str] = deque()
        for step in self._all_steps:
            if in_degree[step] == 0:
                queue.append(step)

        # Sort the initial queue for deterministic output
        queue = deque(sorted(queue))

        result: list[str] = []
        while queue:
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree of dependents
            for dependent in sorted(self._dependents.get(current, [])):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Cycle detection: if we processed fewer nodes than exist, there is a cycle
        if len(result) != len(self._all_steps):
            processed = set(result)
            stuck = [s for s in self._all_steps if s not in processed]
            raise ValueError(f"Circular dependency detected. Steps involved in cycle: " f"{stuck}")

        return result

    # -- Level Computation --------------------------------------------------

    def _compute_levels(self) -> list[list[str]]:
        """Compute topological levels (steps at the same level can run in parallel).

        Level 0: steps with no dependencies
        Level N: steps whose deps are all in levels < N

        Returns:
            List of lists, where each inner list contains steps at that level.
        """
        step_level: dict[str, int] = {}

        for step in self._topo_order:
            deps = self._deps[step]
            if not deps:
                step_level[step] = 0
            else:
                step_level[step] = max(step_level[dep] for dep in deps) + 1

        # Group by level
        max_level = max(step_level.values()) if step_level else 0
        levels: list[list[str]] = [[] for _ in range(max_level + 1)]
        for step, level in step_level.items():
            levels[level].append(step)

        # Sort within each level for determinism
        for level in levels:
            level.sort()

        return levels

    # -- Critical Path ------------------------------------------------------

    def _compute_critical_path(self) -> list[str]:
        """Compute the critical path (longest path through the DAG).

        Uses dynamic programming on the topological order.  Each step's
        'distance' is 1 + max(distance of deps).  The critical path is
        the chain of steps with maximum cumulative distance.

        Returns:
            List of step IDs on the critical path, ordered from start to end.
        """
        dist: dict[str, int] = {}
        predecessor: dict[str, str | None] = {}

        for step in self._topo_order:
            deps = self._deps[step]
            if not deps:
                dist[step] = 1
                predecessor[step] = None
            else:
                best_dep = max(deps, key=lambda d: dist[d])
                dist[step] = dist[best_dep] + 1
                predecessor[step] = best_dep

        # Find the endpoint (step with max distance)
        if not dist:
            return []

        end = max(dist, key=lambda s: dist[s])

        # Trace back
        path: list[str] = []
        current: str | None = end
        while current is not None:
            path.append(current)
            current = predecessor[current]

        path.reverse()
        return path

    # -- Public API ---------------------------------------------------------

    def topological_sort(self) -> list[str]:
        """Return the topological order of all steps.

        Returns:
            List of step IDs in dependency-safe execution order.
            Steps at the same dependency level appear in alphabetical order.
        """
        return list(self._topo_order)

    def get_ready_steps(self, completed: set[str] | None = None) -> list[str]:
        """Get steps that are ready to execute (all deps satisfied).

        Args:
            completed: Override the internal completed set.  If None,
                       uses the internally tracked completed steps.

        Returns:
            List of step IDs whose dependencies are all in the completed set
            and that have not been completed themselves.
        """
        done = completed if completed is not None else self._completed

        ready: list[str] = []
        for step in self._topo_order:
            if step in done:
                continue
            deps = self._deps[step]
            if all(dep in done for dep in deps):
                ready.append(step)

        return sorted(ready)

    def get_parallel_groups(self) -> list[list[str]]:
        """Return groups of steps that can execute simultaneously.

        Each group is a topological level where all steps have their
        dependencies satisfied by steps in earlier levels.

        Returns:
            List of lists.  Each inner list contains 1+ step IDs that
            can run in parallel.  Groups are ordered by execution level.
        """
        return [list(level) for level in self._levels]

    def mark_completed(self, step_id: str) -> None:
        """Mark a step as completed.

        Args:
            step_id: The step to mark as done.

        Raises:
            ValueError: If step_id is not in the dependency map.
        """
        if step_id not in self._deps:
            raise ValueError(
                f"Unknown step '{step_id}'. " f"Valid steps: {sorted(self._deps.keys())}"
            )
        self._completed.add(step_id)
        logger.debug(
            "DAG: marked '%s' complete (%d/%d done)",
            step_id,
            len(self._completed),
            len(self._all_steps),
        )

    def get_critical_path(self) -> list[str]:
        """Return the critical path (longest dependency chain).

        Returns:
            List of step IDs on the critical path, from start to end.
        """
        return list(self._critical_path)

    def is_complete(self) -> bool:
        """Check if all steps have been completed.

        Returns:
            True if every step in the DAG has been marked completed.
        """
        return len(self._completed) == len(self._all_steps)

    # -- Introspection ------------------------------------------------------

    @property
    def steps(self) -> list[str]:
        """All step IDs in the DAG."""
        return list(self._all_steps)

    @property
    def completed(self) -> set[str]:
        """Set of completed step IDs."""
        return set(self._completed)

    @property
    def remaining(self) -> list[str]:
        """Steps not yet completed, in topological order."""
        return [s for s in self._topo_order if s not in self._completed]

    @property
    def levels(self) -> list[list[str]]:
        """Topological levels (same as get_parallel_groups)."""
        return self.get_parallel_groups()

    @property
    def level_count(self) -> int:
        """Number of topological levels."""
        return len(self._levels)

    def dependencies_of(self, step_id: str) -> list[str]:
        """Return the direct dependencies of a step.

        Args:
            step_id: The step to query.

        Returns:
            List of step IDs that must complete before this step.
        """
        if step_id not in self._deps:
            raise ValueError(f"Unknown step: {step_id}")
        return list(self._deps[step_id])

    def dependents_of(self, step_id: str) -> list[str]:
        """Return steps that depend on the given step.

        Args:
            step_id: The step to query.

        Returns:
            List of step IDs that have this step as a dependency.
        """
        if step_id not in self._deps:
            raise ValueError(f"Unknown step: {step_id}")
        return sorted(self._dependents.get(step_id, []))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the DAG state for diagnostics/logging.

        Returns:
            Dict with steps, levels, critical_path, and completion state.
        """
        return {
            "total_steps": len(self._all_steps),
            "completed": len(self._completed),
            "remaining": len(self._all_steps) - len(self._completed),
            "is_complete": self.is_complete(),
            "levels": self._levels,
            "level_count": self.level_count,
            "critical_path": self._critical_path,
            "critical_path_length": len(self._critical_path),
            "topological_order": self._topo_order,
        }

    def __repr__(self) -> str:
        return (
            f"DAGEngine(steps={len(self._all_steps)}, "
            f"completed={len(self._completed)}, "
            f"levels={self.level_count})"
        )
