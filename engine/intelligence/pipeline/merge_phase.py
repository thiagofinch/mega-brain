"""
merge_phase.py -- Post-Barrier Serial Merge Phase
==================================================

Executes Phase 4.5 (RAG rebuild) and wave-3-merge ONCE, serially,
after all parallel workers have completed via the WorkerBarrier.

This module guarantees:
- rag_rebuild() is called exactly ONCE per batch (not per worker)
- wave_3_merge() runs AFTER rag_rebuild (never concurrently with workers)
- Both functions receive ALL slug outputs from ALL workers

Version: 1.0.0  [STORY-PIP-005]
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger("pipeline.merge_phase")


def post_barrier_pipeline(
    worker_results: list[dict[str, Any]],
    rag_rebuild_fn: Callable[[list[dict[str, Any]]], Any] | None = None,
    wave_3_merge_fn: Callable[[list[dict[str, Any]]], Any] | None = None,
) -> dict[str, Any]:
    """Execute serial merge phase after all workers complete.

    This function runs AFTER WorkerBarrier.wait_all() returns.
    It executes Phase 4.5 (RAG rebuild) and wave-3-merge sequentially.

    Args:
        worker_results: List of worker result dicts from barrier.wait_all().
            Each dict has keys: slug, status, output.
        rag_rebuild_fn: Callable that rebuilds the RAG/BM25 index.
            Receives the full worker_results list. If None, uses
            the default rag_rebuild() from the pipeline engine.
        wave_3_merge_fn: Callable that performs the final merge.
            Receives the full worker_results list. If None, uses
            the default wave_3_merge() from the pipeline engine.

    Returns:
        Dict with merge phase outcome:
            - workers_total: int
            - workers_completed: int
            - workers_failed: int
            - rag_rebuild_status: "completed" | "skipped" | "failed"
            - wave_3_merge_status: "completed" | "skipped" | "failed"
            - error: str | None
    """
    total = len(worker_results)
    completed = sum(1 for r in worker_results if r["status"] == "completed")
    failed = total - completed

    logger.info(
        "[BARRIER] All %d workers complete. Starting serial merge phase. "
        "(completed=%d, failed=%d)",
        total,
        completed,
        failed,
    )

    outcome: dict[str, Any] = {
        "workers_total": total,
        "workers_completed": completed,
        "workers_failed": failed,
        "rag_rebuild_status": "skipped",
        "wave_3_merge_status": "skipped",
        "error": None,
    }

    # Collect all slug outputs (even from failed workers, if they have partial output)
    all_outputs = [r for r in worker_results if r.get("output") is not None]

    # --- Phase 4.5: RAG Rebuild (exactly once) ---
    if rag_rebuild_fn is not None:
        try:
            logger.info(
                "[BARRIER] Phase 4.5: RAG rebuild starting "
                "(collecting outputs from %d workers)...",
                len(all_outputs),
            )
            rag_rebuild_fn(worker_results)
            outcome["rag_rebuild_status"] = "completed"
            logger.info("[BARRIER] Phase 4.5: RAG rebuild completed.")
        except Exception as exc:
            outcome["rag_rebuild_status"] = "failed"
            outcome["error"] = f"rag_rebuild failed: {exc}"
            logger.error("[BARRIER] Phase 4.5: RAG rebuild FAILED: %s", exc)
            # Continue to wave-3-merge even if RAG fails -- it operates
            # on slug dirs, not the BM25 index
    else:
        logger.info("[BARRIER] Phase 4.5: RAG rebuild skipped (no rag_rebuild_fn provided)")

    # --- Wave-3 Merge (serial, after RAG) ---
    if wave_3_merge_fn is not None:
        try:
            logger.info(
                "[BARRIER] Wave-3 merge starting " "(merging outputs from %d workers)...",
                len(all_outputs),
            )
            wave_3_merge_fn(worker_results)
            outcome["wave_3_merge_status"] = "completed"
            logger.info("[BARRIER] Wave-3 merge completed.")
        except Exception as exc:
            outcome["wave_3_merge_status"] = "failed"
            error_msg = f"wave_3_merge failed: {exc}"
            if outcome["error"]:
                outcome["error"] += f"; {error_msg}"
            else:
                outcome["error"] = error_msg
            logger.error("[BARRIER] Wave-3 merge FAILED: %s", exc)
    else:
        logger.info("[BARRIER] Wave-3 merge skipped (no wave_3_merge_fn provided)")

    logger.info(
        "[BARRIER] Serial merge phase complete. " "RAG=%s, Merge=%s",
        outcome["rag_rebuild_status"],
        outcome["wave_3_merge_status"],
    )

    return outcome


__all__ = ["post_barrier_pipeline"]
