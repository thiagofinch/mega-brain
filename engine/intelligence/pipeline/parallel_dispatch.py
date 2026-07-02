"""
parallel_dispatch.py -- Parallel Slug Dispatch for /process-inbox
=================================================================

Integrates SlidingWorkerPool + slug_grouper + slug_lock + preflight
into a single dispatch function called by /process-inbox.

This module is PURE INTEGRATION -- zero new pool/queue logic.
It wires existing components from PIP-001 and PIP-003.

Configuration:
    PROCESS_INBOX_MAX_PARALLEL=2  (default, safe)
    PROCESS_INBOX_MAX_PARALLEL=3  (medium load)
    PROCESS_INBOX_MAX_PARALLEL=4  (max supported, Art. VII L3 boundary)

Values above 4 are capped with a warning.

Version: 1.0.0  [STORY-PIP-002]
"""

from __future__ import annotations

import json as _json
import logging
import os
import time as _time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.intelligence.pipeline.barrier import WorkerBarrier
from engine.intelligence.pipeline.merge_phase import post_barrier_pipeline
from engine.intelligence.pipeline.preflight import ManifestUpdater, PreFlightBootstrap
from engine.intelligence.pipeline.sliding_pool import SlidingWorkerPool
from engine.intelligence.pipeline.slug_grouper import group_files_by_slug
from engine.intelligence.pipeline.slug_lock import SlugLockManager
from engine.intelligence.pipeline.state_reaper import reap_stale_states

logger = logging.getLogger("pipeline.parallel_dispatch")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MAX_PARALLEL = 2
_MAX_PARALLEL_CAP = 4

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_MCE_BASE = _PROJECT_ROOT / ".claude" / "mission-control" / "mce"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def get_process_inbox_max_parallel() -> int:
    """Read PROCESS_INBOX_MAX_PARALLEL from env with default=2, cap=4.

    Returns:
        Worker count clamped to [1, 4].
    """
    raw = os.environ.get("PROCESS_INBOX_MAX_PARALLEL", "")
    if not raw.strip():
        return _DEFAULT_MAX_PARALLEL

    try:
        value = int(raw.strip())
    except ValueError:
        logger.warning(
            "Invalid PROCESS_INBOX_MAX_PARALLEL=%r, using default %d",
            raw,
            _DEFAULT_MAX_PARALLEL,
        )
        return _DEFAULT_MAX_PARALLEL

    if value > _MAX_PARALLEL_CAP:
        logger.warning(
            "PROCESS_INBOX_MAX_PARALLEL=%d exceeds max %d, capping at %d",
            value,
            _MAX_PARALLEL_CAP,
            _MAX_PARALLEL_CAP,
        )
        value = _MAX_PARALLEL_CAP

    return max(1, value)


# ---------------------------------------------------------------------------
# Worker Result
# ---------------------------------------------------------------------------


@dataclass
class SlugWorkerResult:
    """Result from processing a single slug group."""

    slug: str
    status: str  # "completed" | "failed"
    files_processed: int = 0
    files_failed: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Dispatch Result
# ---------------------------------------------------------------------------


@dataclass
class DispatchResult:
    """Aggregate result from parallel dispatch."""

    total_slugs: int = 0
    completed_slugs: int = 0
    failed_slugs: int = 0
    total_files_processed: int = 0
    total_files_failed: int = 0
    max_workers_used: int = 0
    results: list[SlugWorkerResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Worker Function
# ---------------------------------------------------------------------------


def _make_worker_fn(
    lock_manager: SlugLockManager,
    manifest_updater: ManifestUpdater,
    process_file_fn: Any,
    barrier: WorkerBarrier | None = None,
) -> Any:
    """Create a worker function that processes a slug group.

    The returned callable accepts a tuple of (slug, files) and:
    1. Acquires slug lock (serial within slug)
    2. Processes each file through the provided processor function
    3. Updates manifest with per-file status
    4. Releases lock on completion or exception
    5. Signals the barrier (if provided) as its final step

    Args:
        lock_manager: SlugLockManager instance for slug-level locking.
        manifest_updater: ManifestUpdater for thread-safe manifest writes.
        process_file_fn: Callable(file_path: Path) -> bool that processes
                         a single file. Returns True on success.
        barrier: Optional WorkerBarrier. When provided, each worker calls
                 barrier.worker_done() as its final step to synchronize
                 before Phase 4.5.

    Returns:
        Worker function compatible with SlidingWorkerPool.map().
    """

    def worker_fn(slug_group: tuple[str, list[Path]]) -> SlugWorkerResult:
        """Process all files in a slug group under an exclusive lock."""
        slug, files = slug_group
        result = SlugWorkerResult(slug=slug, status="completed")

        try:
            with lock_manager.lock(slug):
                for file_path in files:
                    file_key = f"{slug}/{file_path.name}"
                    try:
                        success = process_file_fn(file_path)
                        if success:
                            manifest_updater.mark_completed(file_key)
                            result.files_processed += 1
                        else:
                            manifest_updater.mark_failed(file_key, "process_file returned False")
                            result.files_failed += 1
                    except Exception as exc:
                        error_msg = f"{type(exc).__name__}: {exc}"
                        manifest_updater.mark_failed(file_key, error_msg)
                        result.files_failed += 1
                        logger.error(
                            "Worker[%s]: file %s failed: %s",
                            slug,
                            file_path.name,
                            error_msg,
                        )

        except Exception as exc:
            # Lock acquisition or catastrophic failure
            result.status = "failed"
            result.error = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Worker[%s]: slug-level failure: %s\n%s",
                slug,
                result.error,
                traceback.format_exc(),
            )
            # Mark all unprocessed files as failed
            processed_count = result.files_processed + result.files_failed
            for file_path in files[processed_count:]:
                file_key = f"{slug}/{file_path.name}"
                try:
                    manifest_updater.mark_failed(file_key, result.error or "unknown")
                except Exception:
                    pass  # Best-effort manifest update
            result.files_failed += len(files) - processed_count

        # Final status determination
        if result.files_failed > 0 and result.files_processed == 0:
            result.status = "failed"
        elif result.files_failed > 0:
            result.status = "failed"  # partial failure still counts as failed

        # Signal barrier as final step (try/finally guarantees no deadlock)
        if barrier is not None:
            output_data = {
                "files_processed": result.files_processed,
                "files_failed": result.files_failed,
            }
            barrier.worker_done(slug, result.status, output_data)

        return result

    return worker_fn


# ---------------------------------------------------------------------------
# Main Dispatch Function
# ---------------------------------------------------------------------------


def dispatch_parallel(
    file_list: list[Path],
    process_file_fn: Any,
    project_root: Path | None = None,
    max_parallel: int | None = None,
    rag_rebuild_fn: Any | None = None,
    wave_3_merge_fn: Any | None = None,
) -> DispatchResult:
    """Dispatch slug groups through SlidingWorkerPool for parallel processing.

    This is the main entry point called by /process-inbox. It orchestrates:
    1. Pre-flight (reap stale states, bootstrap manifest)
    2. Group files by slug
    3. Determine worker count from env var (never hardcoded)
    4. Dispatch via SlidingWorkerPool.map() with WorkerBarrier
    5. Execute serial merge phase (Phase 4.5 RAG rebuild + wave-3-merge)
    6. Collect and return results

    Args:
        file_list: All files to process (already identified by /process-inbox).
        process_file_fn: Callable(file_path: Path) -> bool that processes a
                         single file through the MCE pipeline.
        project_root: Project root directory. Defaults to auto-detection.
        max_parallel: Override for max parallel workers. If None, reads
                      PROCESS_INBOX_MAX_PARALLEL env var.
        rag_rebuild_fn: Optional callable for Phase 4.5 RAG rebuild.
                        Called exactly once after all workers complete.
        wave_3_merge_fn: Optional callable for wave-3-merge.
                         Called serially after RAG rebuild.

    Returns:
        DispatchResult with per-slug outcomes.
    """
    root = project_root or _PROJECT_ROOT
    mce_base = root / ".claude" / "mission-control" / "mce"

    # --- Step 0: Pre-flight ---
    logger.info("dispatch_parallel: running pre-flight...")
    reap_stale_states()

    bootstrap = PreFlightBootstrap(mce_base=mce_base)
    pending_files = bootstrap.run(file_list)

    if not pending_files:
        logger.info("dispatch_parallel: no pending files after pre-flight")
        return DispatchResult()

    # --- Step 1: Group by slug ---
    slug_groups = group_files_by_slug(pending_files)
    slug_items: list[tuple[str, list[Path]]] = list(slug_groups.items())

    logger.info(
        "dispatch_parallel: %d files across %d slugs",
        len(pending_files),
        len(slug_items),
    )

    # --- Step 2: Determine worker count ---
    if max_parallel is not None:
        worker_count = max(1, min(max_parallel, _MAX_PARALLEL_CAP))
    else:
        worker_count = get_process_inbox_max_parallel()

    # Use sliding_pool.get_max_workers for volume-based throttle (AC 1)
    from engine.intelligence.pipeline.sliding_pool import get_max_workers

    volume_capped = get_max_workers(file_count=len(pending_files))
    # Take the minimum of env-configured and volume-capped
    effective_workers = min(worker_count, volume_capped, len(slug_items))
    effective_workers = max(1, effective_workers)

    logger.info(
        "dispatch_parallel: using %d workers " "(env=%d, volume_cap=%d, slugs=%d)",
        effective_workers,
        worker_count,
        volume_capped,
        len(slug_items),
    )

    # --- Step 3: Create worker dependencies + barrier ---
    lock_manager = SlugLockManager(base_dir=mce_base)
    manifest_updater = ManifestUpdater()
    barrier = WorkerBarrier(expected_count=len(slug_items))
    worker_fn = _make_worker_fn(lock_manager, manifest_updater, process_file_fn, barrier=barrier)

    # --- Step 4: Dispatch via SlidingWorkerPool.map() with barrier (PIP-005) ---
    pool = SlidingWorkerPool(max_workers=effective_workers, name="process-inbox")

    try:
        raw_results = pool.map(worker_fn, slug_items)
    finally:
        pool.shutdown(wait=True)

    # --- Step 4.5: Wait for barrier + serial merge phase (PIP-005) ---
    # Note: pool.map() already blocks until all workers complete, and each
    # worker calls barrier.worker_done() as its final step. The main thread
    # now calls wait_all() to synchronize and collect barrier results.
    barrier_results = barrier.wait_all()

    # Execute Phase 4.5 (RAG rebuild) + wave-3-merge serially
    merge_outcome = post_barrier_pipeline(
        worker_results=barrier_results,
        rag_rebuild_fn=rag_rebuild_fn,
        wave_3_merge_fn=wave_3_merge_fn,
    )

    logger.info(
        "dispatch_parallel: merge phase outcome — RAG=%s, Merge=%s",
        merge_outcome["rag_rebuild_status"],
        merge_outcome["wave_3_merge_status"],
    )

    # --- Step 5: Collect results ---
    dispatch_result = DispatchResult(
        total_slugs=len(slug_items),
        max_workers_used=effective_workers,
    )

    for raw in raw_results:
        if isinstance(raw, Exception):
            # Pool-level exception (should not happen with our worker_fn
            # catching internally, but defensive)
            slug_result = SlugWorkerResult(
                slug="unknown",
                status="failed",
                error=str(raw),
            )
        else:
            slug_result = raw

        dispatch_result.results.append(slug_result)

        if slug_result.status == "completed":
            dispatch_result.completed_slugs += 1
        else:
            dispatch_result.failed_slugs += 1

        dispatch_result.total_files_processed += slug_result.files_processed
        dispatch_result.total_files_failed += slug_result.files_failed

    logger.info(
        "dispatch_parallel: complete — %d/%d slugs succeeded, " "%d files processed, %d failed",
        dispatch_result.completed_slugs,
        dispatch_result.total_slugs,
        dispatch_result.total_files_processed,
        dispatch_result.total_files_failed,
    )

    return dispatch_result


# ---------------------------------------------------------------------------
# SubagentBridge — ponte entre subagentes Claude e a infra Python (PIP-002)
# ---------------------------------------------------------------------------
#
# Quando /process-inbox spawna N subagentes Claude em paralelo (via Agent tool),
# cada subagente executa /process-jarvis para seu slug. Antes e depois, o
# subagente usa esta bridge para coordenar com a infraestrutura Python:
#
#   Subagente Claude (process-jarvis para slug "acme"):
#     1. bridge = SubagentBridge("acme")
#     2. bridge.acquire_lock()          # exclusividade dentro do slug
#     3. bridge.start_file("arquivo.md")
#     4. [executa process-jarvis 8 fases via LLM]
#     5. bridge.complete_file("arquivo.md", success=True)
#     6. bridge.release_lock()
#     7. bridge.signal_done(files_ok=N, files_fail=0)
#
# O orchestrador Claude aguarda todos os subagentes e então chama
# run_post_barrier() para o merge serial (Phase 4.5 + wave-3-merge).
#
# Uso:
#   from engine.intelligence.pipeline.parallel_dispatch import SubagentBridge
#   bridge = SubagentBridge(slug, project_root=Path("."))

_Path = Path


class SubagentBridge:
    """Bridge entre subagente Claude e infraestrutura Python de coordenação."""

    SIGNAL_DIR_NAME = "subagent-signals"

    def __init__(self, slug: str, project_root: _Path | None = None):
        self.slug = slug
        self._root = project_root or _Path(__file__).resolve().parents[3]
        self._signal_dir = self._root / ".data" / self.SIGNAL_DIR_NAME
        self._signal_dir.mkdir(parents=True, exist_ok=True)
        self._lock_mgr = SlugLockManager(self._root / ".claude" / "mission-control" / "mce")
        self._manifest_path = self._root / ".data" / "PROCESSED-MANIFEST.json"
        self._lock_ctx = None

    # -- Lock --

    def acquire_lock(self) -> None:
        """Adquirir lock exclusivo para este slug. Chame antes de process-jarvis."""
        self._lock_ctx = self._lock_mgr.lock(self.slug)
        self._lock_ctx.__enter__()

    def release_lock(self) -> None:
        """Liberar lock. Chame após concluir todas as fases do slug."""
        if self._lock_ctx is not None:
            self._lock_ctx.__exit__(None, None, None)
            self._lock_ctx = None

    # -- Manifest --

    def start_file(self, file_path: str) -> None:
        """Registrar arquivo como in_progress no manifest."""
        self._update_manifest(file_path, "in_progress")

    def complete_file(self, file_path: str, success: bool = True, error: str = "") -> None:
        """Registrar arquivo como completed ou failed no manifest."""
        status = "completed" if success else "failed"
        self._update_manifest(file_path, status, error=error)

    def _update_manifest(self, file_path: str, status: str, error: str = "") -> None:
        import fcntl

        key = f"{self.slug}/{_Path(file_path).name}"
        try:
            lock_path = self._manifest_path.with_suffix(".lock")
            with open(lock_path, "w") as lf:
                fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
                try:
                    manifest = {}
                    if self._manifest_path.exists():
                        with open(self._manifest_path) as f:
                            manifest = _json.load(f)
                    manifest[key] = {"status": status, "error": error, "slug": self.slug}
                    with open(self._manifest_path, "w") as f:
                        _json.dump(manifest, f, indent=2)
                finally:
                    fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
        except Exception as exc:
            logger.warning("SubagentBridge[%s]: manifest update failed: %s", self.slug, exc)

    # -- Signal --

    def signal_done(self, files_ok: int = 0, files_fail: int = 0) -> None:
        """Sinalizar ao orchestrador que este slug terminou. Escreve arquivo de sinal."""
        signal = {
            "slug": self.slug,
            "status": "completed" if files_fail == 0 else "failed",
            "files_ok": files_ok,
            "files_fail": files_fail,
            "ts": _time.time(),
        }
        signal_path = self._signal_dir / f"{self.slug}.done.json"
        with open(signal_path, "w") as f:
            _json.dump(signal, f)

    # -- Orchestrator side --

    @classmethod
    def wait_all_signals(
        cls,
        expected_slugs: list[str],
        project_root: _Path | None = None,
        timeout_seconds: int = 14400,  # 4 horas
        poll_interval: float = 5.0,
    ) -> dict[str, dict]:
        """Aguardar todos os slugs sinalizarem done. Chamado pelo orchestrador Claude.

        Returns:
            Dict slug → signal dict
        """
        root = project_root or _Path(__file__).resolve().parents[3]
        signal_dir = root / ".data" / cls.SIGNAL_DIR_NAME
        signal_dir.mkdir(parents=True, exist_ok=True)

        pending = set(expected_slugs)
        results: dict[str, dict] = {}
        deadline = _time.time() + timeout_seconds

        while pending and _time.time() < deadline:
            for slug in list(pending):
                sig_path = signal_dir / f"{slug}.done.json"
                if sig_path.exists():
                    with open(sig_path) as f:
                        results[slug] = _json.load(f)
                    pending.discard(slug)
            if pending:
                _time.sleep(poll_interval)

        if pending:
            logger.warning("wait_all_signals: timed out waiting for slugs: %s", pending)
            for slug in pending:
                results[slug] = {"slug": slug, "status": "timeout", "files_ok": 0, "files_fail": 0}

        return results

    @classmethod
    def clear_signals(cls, project_root: _Path | None = None) -> None:
        """Limpar sinais de runs anteriores antes de iniciar novo batch."""
        root = project_root or _Path(__file__).resolve().parents[3]
        signal_dir = root / ".data" / cls.SIGNAL_DIR_NAME
        if signal_dir.exists():
            for sig in signal_dir.glob("*.done.json"):
                sig.unlink(missing_ok=True)


def run_post_barrier(
    slug_results: dict[str, dict],
    project_root: _Path | None = None,
) -> dict:
    """Executar Phase 4.5 (RAG rebuild) + wave-3-merge serialmente.

    Chamado pelo orchestrador Claude após wait_all_signals() retornar.
    Substitui o barrier interno para o fluxo de subagentes.

    Args:
        slug_results: Retorno de wait_all_signals()
        project_root: Raiz do projeto

    Returns:
        Dict com rag_rebuild_status e wave_3_merge_status
    """
    # Converte para formato esperado por post_barrier_pipeline
    barrier_results = [
        {
            "slug": slug,
            "status": data.get("status", "unknown"),
            "output": {
                "files_processed": data.get("files_ok", 0),
                "files_failed": data.get("files_fail", 0),
            },
        }
        for slug, data in slug_results.items()
    ]
    return post_barrier_pipeline(worker_results=barrier_results)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    "DispatchResult",
    "SlugWorkerResult",
    "SubagentBridge",
    "dispatch_parallel",
    "get_process_inbox_max_parallel",
    "run_post_barrier",
]
