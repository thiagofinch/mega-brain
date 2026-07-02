"""
sliding_pool.py -- Sliding Worker Pool
=======================================

Configurable worker pool that adjusts dynamically based on load.
Replaces fixed-size worker pools across the pipeline.

Configuration via environment variable::

    PIPELINE_WORKER_POOL_SIZE=8  # default: 4

The pool is "sliding" -- it scales between 1 and ``max_workers`` based
on the current queue depth and system load:

- Queue depth <= max_workers: uses ``min(queue_depth, max_workers)`` workers
- Queue depth > max_workers: uses full ``max_workers``
- On consecutive failures: reduces active workers by 1 (backpressure)
- On recovery: restores to previous level

This prevents resource exhaustion on small batches and provides
backpressure when the system is struggling.

Constraints:
    - stdlib only (concurrent.futures is stdlib since Python 3.2).
    - Thread-safe.

Version: 1.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

logger = logging.getLogger("pipeline.sliding_pool")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_POOL_SIZE = 4

# Auto-throttle thresholds: when file_count exceeds these, workers are capped
# to avoid API rate limits (especially OpenAI Embeddings).
_VOLUME_THRESHOLDS = [
    (200, 1),  # >= 200 files → 1 worker (very large batch)
    (100, 2),  # >= 100 files → 2 workers
    (50, 3),  # >=  50 files → 3 workers
    (0, None),  # < 50 files → use configured/default
]

T = TypeVar("T")


def get_max_workers(file_count: int | None = None) -> int:
    """Read max worker count from env var with automatic volume-based throttling.

    When ``file_count`` is provided, automatically caps workers to prevent
    API rate limits on large batches (embedding API has strict rate limits).

    Auto-throttle table (applied BEFORE env var cap):
        >= 200 files → 1 worker
        >= 100 files → 2 workers
        >=  50 files → 3 workers
        <   50 files → no auto-throttle

    Reads ``PIPELINE_WORKER_POOL_SIZE`` from the environment.
    Clamps to range [1, 32].

    Args:
        file_count: Total number of files to be processed. When provided,
                    triggers automatic throttling for large batches.

    Returns:
        Configured max worker count, potentially capped by volume.
    """
    # Step 1: get configured value
    raw = os.environ.get("PIPELINE_WORKER_POOL_SIZE", "")
    configured: int = DEFAULT_POOL_SIZE
    if raw.strip():
        try:
            configured = max(1, min(int(raw.strip()), 32))
        except ValueError:
            logger.warning(
                "Invalid PIPELINE_WORKER_POOL_SIZE=%r, using default %d",
                raw,
                DEFAULT_POOL_SIZE,
            )

    # Step 2: auto-throttle based on volume
    if file_count is not None and file_count > 0:
        for threshold, cap in _VOLUME_THRESHOLDS:
            if file_count >= threshold and cap is not None:
                if configured > cap:
                    logger.info(
                        "Auto-throttle: %d files → capping workers %d→%d "
                        "(prevents API rate limits)",
                        file_count,
                        configured,
                        cap,
                    )
                    configured = cap
                break

    return configured


def _get_max_workers_legacy() -> int:
    """Legacy shim — same as get_max_workers() without file_count."""
    raw = os.environ.get("PIPELINE_WORKER_POOL_SIZE", "")
    if raw.strip():
        try:
            val = int(raw.strip())
            return max(1, min(val, 32))
        except ValueError:
            logger.warning(
                "Invalid PIPELINE_WORKER_POOL_SIZE=%r, using default %d",
                raw,
                DEFAULT_POOL_SIZE,
            )
    return DEFAULT_POOL_SIZE


# ---------------------------------------------------------------------------
# Pool metrics
# ---------------------------------------------------------------------------


@dataclass
class PoolMetrics:
    """Tracks sliding pool performance metrics."""

    total_submitted: int = 0
    total_completed: int = 0
    total_failed: int = 0
    consecutive_failures: int = 0
    current_workers: int = 0
    max_workers: int = 0
    adjustments: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Return success rate as a percentage."""
        total = self.total_completed + self.total_failed
        if total == 0:
            return 100.0
        return (self.total_completed / total) * 100.0


# ---------------------------------------------------------------------------
# Sliding Worker Pool
# ---------------------------------------------------------------------------


class SlidingWorkerPool:
    """Worker pool that adjusts concurrency dynamically based on load.

    The pool slides between 1 and ``max_workers`` based on:

    1. **Queue depth**: fewer tasks = fewer workers (no waste).
    2. **Backpressure**: consecutive failures reduce the active worker
       count, giving the system breathing room.
    3. **Recovery**: after a success following failures, active workers
       are restored incrementally.

    Args:
        max_workers: Maximum number of concurrent workers.
                     Defaults to ``PIPELINE_WORKER_POOL_SIZE`` env var.
        name: Optional name for logging.

    Example::

        pool = SlidingWorkerPool()
        results = pool.map(process_file, file_list)

        # Or submit individual tasks:
        future = pool.submit(process_file, file_path)
        result = future.result()
    """

    def __init__(
        self,
        max_workers: int | None = None,
        name: str = "pipeline",
    ) -> None:
        self._max_workers = max_workers if max_workers is not None else get_max_workers()
        self._active_workers = self._max_workers
        self._name = name
        self._lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None
        self.metrics = PoolMetrics(
            current_workers=self._active_workers,
            max_workers=self._max_workers,
        )

        logger.info(
            "SlidingWorkerPool[%s]: initialized (max_workers=%d)",
            self._name,
            self._max_workers,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def max_workers(self) -> int:
        """Return the configured maximum worker count."""
        return self._max_workers

    @property
    def active_workers(self) -> int:
        """Return the current active worker count (may be < max_workers)."""
        with self._lock:
            return self._active_workers

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
        """Submit a single task to the pool.

        Args:
            fn: Callable to execute.
            *args: Positional arguments for ``fn``.
            **kwargs: Keyword arguments for ``fn``.

        Returns:
            A :class:`Future` representing the pending result.
        """
        executor = self._get_or_create_executor()
        with self._lock:
            self.metrics.total_submitted += 1
        return executor.submit(fn, *args, **kwargs)

    def map(
        self,
        fn: Callable[..., T],
        items: list[Any],
        timeout: float | None = None,
    ) -> list[T | Exception]:
        """Process items concurrently with sliding concurrency.

        Adjusts the active worker count based on queue depth and
        failure rate.  Returns results in the same order as ``items``.

        Args:
            fn: Callable that takes a single item.
            items: List of items to process.
            timeout: Optional timeout per item in seconds.

        Returns:
            List of results (or Exception instances for failures),
            preserving input order.
        """
        if not items:
            return []

        # Slide workers based on queue depth
        effective_workers = self._compute_effective_workers(len(items))
        self._adjust_workers(effective_workers, reason=f"queue_depth={len(items)}")

        executor = self._get_or_create_executor()

        # Submit all tasks, tracking original order
        future_to_index: dict[Future[T], int] = {}
        for idx, item in enumerate(items):
            future = executor.submit(fn, item)
            future_to_index[future] = idx
            with self._lock:
                self.metrics.total_submitted += 1

        # Collect results in order
        results: list[T | Exception | None] = [None] * len(items)

        for future in as_completed(future_to_index, timeout=timeout):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
                self._on_success()
            except Exception as exc:
                results[idx] = exc
                self._on_failure()

        return results  # type: ignore[return-value]

    def shutdown(self, wait: bool = True) -> PoolMetrics:
        """Shutdown the pool and return final metrics.

        Args:
            wait: If *True*, wait for pending tasks to complete.

        Returns:
            Final :class:`PoolMetrics`.
        """
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None

        logger.info(
            "SlidingWorkerPool[%s]: shutdown (completed=%d, failed=%d, rate=%.1f%%)",
            self._name,
            self.metrics.total_completed,
            self.metrics.total_failed,
            self.metrics.success_rate,
        )
        return self.metrics

    # ------------------------------------------------------------------
    # Sliding logic
    # ------------------------------------------------------------------

    def _compute_effective_workers(self, queue_depth: int) -> int:
        """Compute the effective worker count based on queue depth.

        Args:
            queue_depth: Number of items waiting to be processed.

        Returns:
            Effective worker count (1..max_workers).
        """
        # Never more workers than items
        ideal = min(queue_depth, self._max_workers)
        # Ensure at least 1
        return max(1, ideal)

    def _adjust_workers(self, target: int, reason: str = "") -> None:
        """Adjust the active worker count, recreating the executor if needed."""
        with self._lock:
            old = self._active_workers
            self._active_workers = target
            self.metrics.current_workers = target

            if old != target:
                self.metrics.adjustments.append(
                    {
                        "from": old,
                        "to": target,
                        "reason": reason,
                        "timestamp": time.time(),
                    }
                )
                logger.info(
                    "SlidingWorkerPool[%s]: adjusted %d -> %d workers (%s)",
                    self._name,
                    old,
                    target,
                    reason,
                )

                # Recreate executor with new worker count
                if self._executor is not None:
                    # Shut down old executor (don't wait -- pending tasks
                    # continue on old threads; new submissions use new pool)
                    old_executor = self._executor
                    self._executor = None
                    old_executor.shutdown(wait=False)

    def _on_success(self) -> None:
        """Handle a successful task completion."""
        with self._lock:
            self.metrics.total_completed += 1
            if self.metrics.consecutive_failures > 0:
                # Recovery: restore one worker
                self.metrics.consecutive_failures = 0
                new_target = min(self._active_workers + 1, self._max_workers)
                if new_target != self._active_workers:
                    self._active_workers = new_target
                    self.metrics.current_workers = new_target
                    self.metrics.adjustments.append(
                        {
                            "from": self._active_workers - 1,
                            "to": new_target,
                            "reason": "recovery_after_failure",
                            "timestamp": time.time(),
                        }
                    )
                    logger.info(
                        "SlidingWorkerPool[%s]: recovery, restored to %d workers",
                        self._name,
                        new_target,
                    )

    def _on_failure(self) -> None:
        """Handle a failed task -- apply backpressure."""
        with self._lock:
            self.metrics.total_failed += 1
            self.metrics.consecutive_failures += 1

            # Backpressure: reduce workers on consecutive failures
            if self.metrics.consecutive_failures >= 2 and self._active_workers > 1:
                new_target = max(1, self._active_workers - 1)
                if new_target != self._active_workers:
                    self._active_workers = new_target
                    self.metrics.current_workers = new_target
                    self.metrics.adjustments.append(
                        {
                            "from": self._active_workers + 1,
                            "to": new_target,
                            "reason": f"backpressure (consecutive_failures={self.metrics.consecutive_failures})",
                            "timestamp": time.time(),
                        }
                    )
                    logger.info(
                        "SlidingWorkerPool[%s]: backpressure, reduced to %d workers",
                        self._name,
                        new_target,
                    )

    # ------------------------------------------------------------------
    # Executor management
    # ------------------------------------------------------------------

    def _get_or_create_executor(self) -> ThreadPoolExecutor:
        """Get or create the thread pool executor."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(
                        max_workers=self._active_workers,
                        thread_name_prefix=f"pipeline-{self._name}",
                    )
        return self._executor

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> SlidingWorkerPool:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.shutdown(wait=True)
