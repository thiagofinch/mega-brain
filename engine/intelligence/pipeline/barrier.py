"""
barrier.py -- Worker Barrier for Serial Merge Phase
====================================================

Synchronization barrier that ensures Phase 4.5 (RAG rebuild) and
wave-3-merge execute only ONCE after ALL parallel workers complete.

Uses threading.Barrier internally (Python stdlib). The barrier is
initialized with expected_count + 1 (for the main thread) so that
all workers AND the main thread must arrive before release.

Failure handling: failed workers still call worker_done() with
status="failed" to release the barrier -- no deadlocks on failure.

Version: 1.0.0  [STORY-PIP-005]
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger("pipeline.barrier")


class WorkerBarrier:
    """Synchronization barrier for parallel pipeline workers.

    The barrier collects completion signals from all workers before
    allowing the main thread to proceed to the serial merge phase.

    Args:
        expected_count: Number of workers expected to report completion.

    Example::

        barrier = WorkerBarrier(expected_count=4)

        # Each worker calls on completion (success or failure):
        barrier.worker_done("alex-hormozi", "completed", {"files": 12})
        barrier.worker_done("cole-gordon", "failed", {"error": "timeout"})

        # Main thread waits:
        results = barrier.wait_all()
        # -> [{"slug": "alex-hormozi", ...}, {"slug": "cole-gordon", ...}]
    """

    def __init__(self, expected_count: int) -> None:
        if expected_count < 1:
            raise ValueError(f"expected_count must be >= 1, got {expected_count}")

        self._expected_count = expected_count
        # +1 for the main thread that calls wait_all()
        self._barrier = threading.Barrier(expected_count + 1)
        self._results: list[dict[str, Any]] = []
        self._lock = threading.Lock()

        logger.info("[BARRIER] Initialized: expecting %d workers", expected_count)

    @property
    def expected_count(self) -> int:
        """Return the number of workers this barrier expects."""
        return self._expected_count

    def worker_done(
        self,
        slug: str,
        status: str,
        output: dict[str, Any] | None = None,
    ) -> None:
        """Signal that a worker has completed (successfully or not).

        This method is called by each worker as its FINAL step.
        It records the result and then waits at the barrier until
        all other workers (and the main thread) arrive.

        Args:
            slug: The slug identifier for this worker.
            status: Completion status -- "completed" or "failed".
            output: Optional dict with worker output data.
        """
        with self._lock:
            self._results.append(
                {
                    "slug": slug,
                    "status": status,
                    "output": output,
                }
            )

        logger.info(
            "[BARRIER] Worker reported: slug=%s status=%s (%d/%d)",
            slug,
            status,
            len(self._results),
            self._expected_count,
        )

        # Worker waits here until all parties arrive
        self._barrier.wait()

    def wait_all(self) -> list[dict[str, Any]]:
        """Block until all workers have reported, then return results.

        This is called by the MAIN thread. It blocks until all
        expected workers have called worker_done().

        Returns:
            List of dicts with keys: slug, status, output.
            One entry per worker, in the order they reported.
        """
        logger.info(
            "[BARRIER] Main thread waiting for %d workers...",
            self._expected_count,
        )

        # Main thread waits here -- releases when all workers arrive
        self._barrier.wait()

        logger.info(
            "[BARRIER] All %d workers complete. Barrier released.",
            self._expected_count,
        )

        return self._results


__all__ = ["WorkerBarrier"]
