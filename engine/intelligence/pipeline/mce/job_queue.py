"""
engine/intelligence/pipeline/mce/job_queue.py -- Durable MCE job claim/lease.
============================================================================
psycopg2 port of gbrain's token-fenced minion queue (gbrain
``src/core/minions/queue.ts`` @ 4ee530f) onto the ``mce_jobs`` table created
in STORY-GBA-W2.5. This is the ADAPT half of PEÇA 2 items 2 & 3:

  - ``claim``     <- queue.ts:605  (UPDATE ... FOR UPDATE SKIP LOCKED RETURNING)
  - ``renew_lock``<- queue.ts:1083 (extend lock_until iff lock_token matches)
  - heartbeat     <- src/core/minions/lock-renewal-tick.ts (renew on TTL/2,
                     voluntary release before another worker can reclaim)
  - release paths <- completeJob:798 / failJob:906 / releaseLeaseFullJob:1050
                     (every mutation token-fenced: WHERE lock_token = %s)

Story: STORY-GBA-W2.6 — Fase 3 (Durabilidade de ingestão), Risk: HIGH.

WHY token-fence (the whole point of this story)
-----------------------------------------------
Two workers must NEVER process the same slug at once. ``FOR UPDATE SKIP LOCKED``
gives mutual exclusion at claim time. The ``lock_token`` (``f"{pid}:{time_ns}"``)
gives mutual exclusion AFTER claim: every subsequent mutation of the job carries
``WHERE lock_token = %s``. If worker A's lease expires and worker B reclaims the
row (writing a fresh token), A's stale token no longer matches — so A's renew /
finalize-of-the-job becomes a 0-rows-affected no-op. The DB, not application
trust, is the arbiter. This is gbrain's exact invariant
(queue.ts ``renewLock``/``completeJob``/``failJob`` all guard on ``lock_token``).

⛔ RNF-1 BOUNDARY (caixa-preta intocável)
-----------------------------------------
This module ENVOLVES ``cmd_finalize`` POR FORA. It imports nothing from and
mutates nothing in the 6 frozen cascade files (``cascading.py``,
``propagation_tracker.py``, ``agent_auto_creator.py``, ``associative_memory.py``,
``ontology_layer.py``, ``hhem_gate.py``). The lease wraps the unit of work; the
cascade stays terminal and untouched. ``git diff`` MUST be empty on those 6.

Schema note (No-Invention, W2.5 is law)
---------------------------------------
The W2.5 ``mce_jobs`` ``chk_mce_jobs_status`` CHECK admits
``waiting/active/completed/failed/delayed/dead`` (mirrors gbrain ``minion_jobs``).
The story's AC prose says ``status='pending'``/``status='processing'``; those
are the *generic* names for the SAME states. We honor the committed schema:
``waiting`` == "pending" (claimable) and ``active`` == "processing" (leased).
No new status value is invented.

Unit of work: the **slug** (Decision D4 — lease per-slug). ``claim`` will not
hand out a slug that already has a live lease (status='active' AND
lock_until > now()); ``FOR UPDATE SKIP LOCKED`` + the status/lock_until filter
enforce that without the caller needing app-level locks.

Connection discipline (gbrain "session-mode pool", queue.ts:609 comment)
------------------------------------------------------------------------
gbrain insists claim+renewLock share a *direct* (session-mode) connection the
pooler can't recycle mid-hold, or the lock orphans. We honor that by holding ONE
psycopg2 connection per :class:`JobLease` for its whole lifetime (claim → renew
heartbeat → release) instead of borrowing a fresh connection per call.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("mce.job_queue")

# ---------------------------------------------------------------------------
# Status vocabulary (W2.5 schema is law — no invented values)
# ---------------------------------------------------------------------------
STATUS_WAITING = "waiting"  # claimable ("pending" in AC prose)
STATUS_ACTIVE = "active"  # leased/processing ("processing" in AC prose)
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_DELAYED = "delayed"
STATUS_DEAD = "dead"

# Default lease TTL. gbrain's worker uses a configured ``lockDuration``; the
# heartbeat renews on TTL/2 (lock-renewal-tick.ts). 30s mirrors gbrain's
# common default and W2.7's reaper will sweep leases stale past lock_until.
DEFAULT_LEASE_MS = int(os.getenv("MCE_LEASE_MS", "30000"))


# ---------------------------------------------------------------------------
# Token generation — gbrain worker.ts:515  `${workerId}:${Date.now()}`
# ---------------------------------------------------------------------------
def make_lock_token() -> str:
    """Build a token-fence token: ``f"{pid}:{time_ns}"``.

    Story AC literal format. ``pid`` scopes the token to this process; the
    monotonic-ish ``time_ns`` suffix makes it unique even if the same pid
    claims the same slug twice across reclaims (a fresh token each claim is
    what lets the old token's mutations become no-ops). gbrain uses a
    per-worker UUID + ``Date.now()``; we follow the W2.6 spec's ``pid:time``.
    """
    return f"{os.getpid()}:{time.time_ns()}"


# ---------------------------------------------------------------------------
# Connection resolution — reuse the EXACT BrainEngine DSN as W2.5 / content_hash
# ---------------------------------------------------------------------------
def get_connection(dsn: str | None = None):
    """Open a raw psycopg2 connection.

    Mirrors ``scripts/migrate_mce_jobs_to_db.py::get_connection`` so claims land
    in the SAME database as ``mce_jobs`` and ``content_hashes`` — no separate
    DSN, no hardcoded credentials (Constitution Art. VI). An explicit ``dsn``
    (used by the characterization test against a disposable docker Postgres)
    overrides the resolved one.
    """
    import psycopg2

    if dsn:
        return psycopg2.connect(dsn)

    # Lazy import: keep engine.config out of module import time so the test can
    # inject a dsn without a configured BrainEngine environment.
    from engine.config import get_config

    resolved = get_config("BRAIN_ENGINE_DSN")
    if resolved:
        return psycopg2.connect(resolved)

    return psycopg2.connect(
        host=get_config("BRAIN_ENGINE_HOST", default="localhost"),
        port=get_config("BRAIN_ENGINE_PORT", default="5432"),
        dbname=get_config("BRAIN_ENGINE_DBNAME", default="megabrain"),
        user=get_config("BRAIN_ENGINE_USER", default="postgres"),
        password=get_config("BRAIN_ENGINE_PASSWORD", default=""),
    )


# ---------------------------------------------------------------------------
# Claimed-job snapshot
# ---------------------------------------------------------------------------
@dataclass
class ClaimedJob:
    """A row claimed by :func:`claim_job`, with the fencing token that owns it."""

    id: int
    slug: str
    status: str
    lock_token: str
    attempts_made: int
    max_attempts: int


# ---------------------------------------------------------------------------
# enqueue — add a slug as a waiting job (idempotent on live duplicates)
# ---------------------------------------------------------------------------
def enqueue(conn, slug: str) -> int | None:
    """Insert a ``waiting`` job for ``slug`` unless one is already live.

    "Live" = a row for this slug in ``waiting`` or ``active`` (mirrors
    ``FileQueue.add``'s "already pending/processing → skip" dedup). Returns the
    new job id, or ``None`` when a live job for the slug already exists.

    Not in the gbrain port (gbrain enqueues elsewhere) — this is the minimal
    seam the mega-brain ingestion path needs to feed the durable queue. Kept
    here so claim has work to hand out; touches only ``mce_jobs``.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO mce_jobs (slug, status)
            SELECT %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM mce_jobs
                WHERE slug = %s AND status IN (%s, %s)
            )
            RETURNING id
            """,
            (slug, STATUS_WAITING, slug, STATUS_WAITING, STATUS_ACTIVE),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# claim — ADAPT of gbrain queue.ts:605
# ---------------------------------------------------------------------------
def claim_job(
    conn,
    lock_token: str,
    lease_ms: int = DEFAULT_LEASE_MS,
    slug: str | None = None,
) -> ClaimedJob | None:
    """Claim the next waiting job, token-fenced, via FOR UPDATE SKIP LOCKED.

    Faithful psycopg2 port of gbrain ``claim`` (queue.ts:605):

        UPDATE mce_jobs SET status='active', lock_token=%s,
               lock_until = now() + (lease_ms * interval '1 ms'),
               attempts_made = attempts_made + 1
         WHERE id = (
             SELECT id FROM mce_jobs
             WHERE status='waiting'  [AND slug=%s]
             ORDER BY created_at ASC, id ASC
             FOR UPDATE SKIP LOCKED
             LIMIT 1
         )
         RETURNING ...

    Mutual exclusion: ``FOR UPDATE SKIP LOCKED`` makes two concurrent claimers
    skip each other's locked candidate row, so each claims a DISTINCT job (or
    None) — never the same one. The lease per-slug invariant (D4) is implicit:
    once claimed the job flips to ``active`` (no longer ``waiting``), so it can't
    be re-handed-out until released or reaped.

    ``slug`` optionally narrows the claim to one slug (used by tests / targeted
    re-claim). ``ORDER BY created_at, id`` reproduces gbrain's priority/FIFO
    ordering using the columns ``mce_jobs`` actually has (no ``priority`` column
    in W2.5 → fall back to insertion order, deterministic via the id tiebreak).

    Returns a :class:`ClaimedJob` on success, ``None`` when nothing claimable.
    """
    interval = f"{int(lease_ms)} milliseconds"
    slug_filter = "AND slug = %s" if slug is not None else ""
    params: list[Any] = [lock_token, interval]
    if slug is not None:
        params.append(slug)

    sql = f"""
        UPDATE mce_jobs SET
            status = '{STATUS_ACTIVE}',
            lock_token = %s,
            lock_until = now() + %s::interval,
            attempts_made = attempts_made + 1
        WHERE id = (
            SELECT id FROM mce_jobs
            WHERE status = '{STATUS_WAITING}'
            {slug_filter}
            ORDER BY created_at ASC, id ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        RETURNING id, slug, status, lock_token, attempts_made, max_attempts
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    conn.commit()
    if row is None:
        return None
    return ClaimedJob(
        id=row[0],
        slug=row[1],
        status=row[2],
        lock_token=row[3],
        attempts_made=row[4],
        max_attempts=row[5],
    )


# ---------------------------------------------------------------------------
# renew_lock — ADAPT of gbrain queue.ts:1083
# ---------------------------------------------------------------------------
def renew_lock(conn, job_id: int, lock_token: str, lease_ms: int = DEFAULT_LEASE_MS) -> bool:
    """Extend ``lock_until`` iff ``lock_token`` still matches (token-fence).

    Faithful port of gbrain ``renewLock``:

        UPDATE mce_jobs SET lock_until = now() + (lease_ms * interval '1 ms')
         WHERE id = %s AND lock_token = %s AND status = 'active'
         RETURNING id

    Returns ``True`` if the lease was extended, ``False`` if the token no longer
    matches (the job was reclaimed by another worker, or it left ``active``).
    A ``False`` here is the worker's signal that it LOST the lock and must stop
    — exactly gbrain's ``TickResult.lock_lost``. This is the no-op the
    token-fence AC verifies: stale token → 0 rows affected → ``False``.
    """
    interval = f"{int(lease_ms)} milliseconds"
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE mce_jobs SET lock_until = now() + %s::interval
            WHERE id = %s AND lock_token = %s AND status = '{STATUS_ACTIVE}'
            RETURNING id
            """,
            (interval, job_id, lock_token),
        )
        renewed = cur.fetchone() is not None
    conn.commit()
    return renewed


# ---------------------------------------------------------------------------
# release paths — token-fenced (completeJob:798 / failJob:906 / lease bounce)
# ---------------------------------------------------------------------------
def complete_job(conn, job_id: int, lock_token: str) -> bool:
    """Flip a leased job to ``completed`` (token-fenced). gbrain completeJob.

    Returns ``False`` (no-op) if the token mismatched — i.e. the job was
    reclaimed mid-flight; the stale worker MUST NOT mark it complete.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE mce_jobs SET
                status = '{STATUS_COMPLETED}',
                lock_token = NULL,
                lock_until = NULL
            WHERE id = %s AND status = '{STATUS_ACTIVE}' AND lock_token = %s
            RETURNING id
            """,
            (job_id, lock_token),
        )
        ok = cur.fetchone() is not None
    conn.commit()
    return ok


def fail_job(
    conn,
    job_id: int,
    lock_token: str,
    error_text: str,
    new_status: str = STATUS_FAILED,
) -> bool:
    """Flip a leased job to a terminal/retry status (token-fenced). gbrain failJob.

    ``new_status`` ∈ {``delayed`` (retry), ``failed``, ``dead``}. Returns
    ``False`` if the token mismatched (job already reclaimed → no-op).
    """
    if new_status not in (STATUS_DELAYED, STATUS_FAILED, STATUS_DEAD):
        raise ValueError(f"invalid fail status: {new_status!r}")
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE mce_jobs SET
                status = %s,
                error_text = %s,
                lock_token = NULL,
                lock_until = NULL
            WHERE id = %s AND status = '{STATUS_ACTIVE}' AND lock_token = %s
            RETURNING id
            """,
            (new_status, error_text, job_id, lock_token),
        )
        ok = cur.fetchone() is not None
    conn.commit()
    return ok


# ---------------------------------------------------------------------------
# Reaper — ADAPT of gbrain handleStalled (queue.ts:1144) + handleTimeouts (:647)
# ---------------------------------------------------------------------------
#
# The reaper is the crash-recovery sweep the worker runs each tick. It is the
# piece that turns a leased queue into a *durable* one: without it, a job whose
# worker crashed (lease expired, row stuck in 'active') would be a silent orphan
# forever. The reaper reclaims those.
#
# Two DISTINCT failure modes, two DISTINCT outcomes (the port-spec's crux):
#
#   stall   → RETRY.  Job is 'active' but its lease EXPIRED (``lock_until < now()``).
#             A dead lease means the worker that held it is gone (crashed / lost
#             the box / got OOM-killed) without releasing. The work itself never
#             got a verdict. So we give it another crack: requeue to 'waiting'
#             (clearing the lease+token so a fresh worker can claim it) while
#             ``stalled_counter`` is under budget; once the post-increment
#             counter reaches ``max_stalled`` it goes to the dead-letter instead
#             of looping forever.
#
#   timeout → DEAD.   Job is 'active', its WALL-CLOCK budget passed
#             (``timeout_at < now()``) but its lease is STILL VALID
#             (``lock_until > now()``). A live lease means a worker is *still
#             holding it* — it just ran too long. Requeueing would race the live
#             worker (two runs of the same slug). So a wall-clock overrun is
#             terminal: dead-letter direct, NO requeue. The ``lock_until > now()``
#             guard is exactly what keeps handleTimeouts off the rows
#             handleStalled is already requeueing.
#
# ORDER (worker loop): ``handle_stalled`` runs BEFORE ``handle_timeouts`` every
# tick (gbrain's worker.ts ordering). Stall recovery gets first crack: a job
# that is BOTH stalled (lease expired) AND past timeout_at is handled by
# handle_stalled first (its lease is < now(), so the handle_timeouts guard
# ``lock_until > now()`` excludes it). Reverse the order and a crashed-but-
# also-overran job would be killed instead of retried — wrong outcome.
#
# RNF-1: the reaper mutates ONLY ``mce_jobs``. It decides requeue/dead and the
# released job re-enters the pipeline through the SAME claim path
# (``cmd_finalize`` stays wrapped POR FORA). Nothing here imports or touches the
# 6 frozen cascade files.


@dataclass
class ReapResult:
    """What a single reaper sweep did (counts + the affected slugs).

    ``requeued`` — stalled jobs sent back to 'waiting' (reclaimable).
    ``dead`` — jobs dead-lettered, split by cause: ``max-stall`` (stall budget
    exhausted) vs ``timeout`` (wall-clock overrun with a live lease). Kept
    distinct because they mean different things operationally (a flood of
    ``timeout`` deaths = jobs genuinely too slow; a flood of ``max-stall`` =
    workers crash-looping).
    """

    requeued: list[str]
    dead_max_stall: list[str]
    dead_timeout: list[str]

    @property
    def dead(self) -> list[str]:
        return self.dead_max_stall + self.dead_timeout


def handle_stalled(conn) -> ReapResult:
    """Reclaim jobs whose lease expired (crashed worker). gbrain handleStalled.

    Faithful psycopg2 port of gbrain ``handleStalled`` (queue.ts:1144) — the
    single-CTE form that has "no off-by-one" (gbrain's own comment). It does the
    whole thing in ONE statement so the detect → decide → mutate is atomic and a
    job can't slip between a SELECT and a later UPDATE:

        WITH stalled AS (
          SELECT id, stalled_counter, max_stalled
          FROM mce_jobs
          WHERE status = 'active' AND lock_until < now()
          FOR UPDATE SKIP LOCKED          -- don't fight a concurrent reaper/claim
        ),
        requeued AS (
          UPDATE mce_jobs SET status='waiting', stalled_counter = stalled_counter+1,
                 lock_token=NULL, lock_until=NULL
          WHERE id IN (SELECT id FROM stalled WHERE stalled_counter + 1 < max_stalled)
          RETURNING slug, 'requeued' AS action
        ),
        dead_lettered AS (
          UPDATE mce_jobs SET status='dead', stalled_counter = stalled_counter+1,
                 attempts_made = attempts_made+1, error_text='max stalled count exceeded',
                 lock_token=NULL, lock_until=NULL
          WHERE id IN (SELECT id FROM stalled WHERE stalled_counter + 1 >= max_stalled)
          RETURNING slug, 'dead' AS action
        )
        SELECT slug, action FROM requeued UNION ALL SELECT slug, action FROM dead_lettered

    The decision boundary is gbrain's EXACT predicate ``stalled_counter + 1``
    (compare the *post-increment* value against ``max_stalled``): a job is
    requeued while the count it WOULD have stays under budget, dead-lettered once
    it reaches it. We preserve this verbatim rather than reimplement it as
    ``stalled_counter < max_stalled`` (which would be off-by-one vs the source).

    ``FOR UPDATE SKIP LOCKED`` mirrors the claim path: a row another worker is
    mid-claiming (or another reaper is mid-reaping) is skipped this tick and
    caught next, never double-handled.

    Returns a :class:`ReapResult`; the ``dead`` here are all ``max-stall``.
    Token-fence safety: clearing ``lock_token`` on requeue means the crashed
    worker's stale token (if it ever revives) no longer matches → its mutations
    are no-ops (same invariant as W2.6).
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            WITH stalled AS (
                SELECT id, stalled_counter, max_stalled
                FROM mce_jobs
                WHERE status = '{STATUS_ACTIVE}' AND lock_until < now()
                FOR UPDATE SKIP LOCKED
            ),
            requeued AS (
                UPDATE mce_jobs SET
                    status = '{STATUS_WAITING}',
                    stalled_counter = stalled_counter + 1,
                    lock_token = NULL,
                    lock_until = NULL
                WHERE id IN (
                    SELECT id FROM stalled WHERE stalled_counter + 1 < max_stalled
                )
                RETURNING slug, 'requeued' AS action
            ),
            dead_lettered AS (
                UPDATE mce_jobs SET
                    status = '{STATUS_DEAD}',
                    stalled_counter = stalled_counter + 1,
                    attempts_made = attempts_made + 1,
                    error_text = 'max stalled count exceeded',
                    lock_token = NULL,
                    lock_until = NULL
                WHERE id IN (
                    SELECT id FROM stalled WHERE stalled_counter + 1 >= max_stalled
                )
                RETURNING slug, 'dead' AS action
            )
            SELECT slug, action FROM requeued
            UNION ALL
            SELECT slug, action FROM dead_lettered
            """
        )
        rows = cur.fetchall()
    conn.commit()

    requeued: list[str] = []
    dead: list[str] = []
    for slug, action in rows:
        (requeued if action == "requeued" else dead).append(slug)
    if requeued or dead:
        logger.info(
            "reaper handle_stalled: requeued=%d dead(max-stall)=%d", len(requeued), len(dead)
        )
    return ReapResult(requeued=requeued, dead_max_stall=dead, dead_timeout=[])


def handle_timeouts(conn) -> ReapResult:
    """Dead-letter jobs that overran wall-clock while the lease is STILL live.

    Faithful port of gbrain ``handleTimeouts`` (queue.ts:647). The whole point
    is the ``lock_until > now()`` guard:

        UPDATE mce_jobs SET status='dead', error_text='timeout exceeded',
               lock_token=NULL, lock_until=NULL
         WHERE status = 'active'
           AND timeout_at IS NOT NULL
           AND timeout_at < now()
           AND lock_until > now()        -- ⛔ lease STILL valid → not a stall
         RETURNING slug

    Without the guard this would also grab stalled jobs (lease expired) and
    KILL them — but a stalled job's worker is gone and the work deserves a
    RETRY, not death. ``lock_until > now()`` restricts this sweep to jobs a
    worker is *still actively holding* but that blew their time budget. Those
    are terminal: requeueing would race the live worker (double-process the same
    slug). gbrain's own comment: "stall → retry, timeout → dead." Order in the
    worker loop (handle_stalled first) plus this guard make the two sweeps
    disjoint within a tick.

    Honest scope (gbrain's documented limitation, preserved): a 1-tick TOCTOU
    window remains — a job whose ``lock_until`` expires *between* handle_stalled
    and handle_timeouts in the same tick may be missed this tick, but is caught
    next tick (after re-claim). It is never double-handled.

    Returns a :class:`ReapResult`; the ``dead`` here are all ``timeout``.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE mce_jobs SET
                status = '{STATUS_DEAD}',
                error_text = 'timeout exceeded',
                lock_token = NULL,
                lock_until = NULL
            WHERE status = '{STATUS_ACTIVE}'
              AND timeout_at IS NOT NULL
              AND timeout_at < now()
              AND lock_until > now()
            RETURNING slug
            """
        )
        rows = cur.fetchall()
    conn.commit()

    dead = [r[0] for r in rows]
    if dead:
        logger.info("reaper handle_timeouts: dead(timeout)=%d", len(dead))
    return ReapResult(requeued=[], dead_max_stall=[], dead_timeout=dead)


def reap(conn) -> ReapResult:
    """One reaper sweep: ``handle_stalled`` THEN ``handle_timeouts`` (the order).

    This is the function the worker loop calls each tick. The order is load-
    bearing (see the module note): stall recovery first so a crashed-AND-overran
    job is retried, not killed. Returns the merged :class:`ReapResult` of both
    sweeps so a worker can log/meter requeues vs the two death causes.
    """
    stalled = handle_stalled(conn)
    timed_out = handle_timeouts(conn)
    return ReapResult(
        requeued=stalled.requeued,
        dead_max_stall=stalled.dead_max_stall,
        dead_timeout=timed_out.dead_timeout,
    )


# ---------------------------------------------------------------------------
# STORY-GBA-W2.8 — replay-safe re-processability signal (D3)
#
# The crash window the spike exposed: the ingestion guard registers a
# content_hash BEFORE cmd_finalize propagates it. If the worker crashes in that
# window, the entry is registered-but-not-propagated; a re-run's guard returns
# DUPLICATE → skip → the file is stuck forever (registered, never cascaded).
#
# The fix is a SIGNAL the reaper/re-run consults: an entry that is registered
# but whose ``content_hashes.metadata.fully_propagated`` is not true (set only
# AFTER cmd_finalize completes, by the orchestrator) is RE-PROCESSABLE — it must
# NOT be DUPLICATE-skipped. The ``propagation_tracker.overall == INCOMPLETE``
# signal (READ-ONLY reuse, never edited) is the secondary corroborating source.
#
# RNF-1: this reads ``content_hashes`` only; it does NOT reorder the guard nor
# alter the 6 verdict keys. The guard stays byte-identical; the decision to
# re-process despite a DUPLICATE verdict is the REAPER's, taken here.
# ---------------------------------------------------------------------------
def is_reprocessable_despite_duplicate(identity_key: str) -> bool:
    """True if a registered content_hash must be RE-PROCESSED (not DUPLICATE-skipped).

    Returns True when the entry is registered but NOT proven fully propagated
    (``fully_propagated`` absent/false). This is the crash-recovery direction:
    a half-propagated file gets another crack instead of being skipped forever.

    Returns False when the entry is fully propagated (idempotency preserved: the
    6 verdicts keep DUPLICATE-skipping a genuinely-done file) OR when the entry
    is unknown to the registry (a NEW file is handled by the guard's own NEW
    verdict, not by this signal).

    Fail-open: any registry error returns False (defer to the guard's normal
    verdict) so a flaky DB never forces an infinite re-process loop.
    """
    try:
        from engine.intelligence.pipeline.ingestion_guard import DbIngestionRegistry

        reg = DbIngestionRegistry()
        try:
            existing = reg.lookup(identity_key)
            if existing is None:
                # Not registered → not this signal's concern (guard says NEW).
                return False
            # Registered: re-processable iff NOT proven fully propagated.
            return not reg.is_fully_propagated(identity_key)
        finally:
            try:
                reg.close()
            except Exception:
                pass
    except Exception as exc:
        logger.warning(
            "is_reprocessable_despite_duplicate: registry error for %s: %s (fail-open=False)",
            identity_key,
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Heartbeat — ADAPT of lock-renewal-tick.ts (renew on TTL/2, release on loss)
# ---------------------------------------------------------------------------
class Heartbeat:
    """Background thread that renews a lease on TTL/2 until stopped.

    Port of gbrain's ``setInterval(runLockRenewalTick, ...)`` worker wiring
    (worker.ts:769 / lock-renewal-tick.ts). Each tick calls :func:`renew_lock`;
    on a token-fence failure (``False`` → ``lock_lost``) it stops itself and
    sets :attr:`lost`, so the owning worker can observe the lost lock and abort
    — instead of grinding on a job another worker already owns.

    Interval = ``lease_ms / 2`` (the AC's TTL/2): renew well before the lease
    can expire so a healthy worker never lets another reclaim its slug.
    """

    def __init__(self, conn, job_id: int, lock_token: str, lease_ms: int = DEFAULT_LEASE_MS):
        self._conn = conn
        self._job_id = job_id
        self._lock_token = lock_token
        self._lease_ms = lease_ms
        self._interval_s = max(0.001, (lease_ms / 2) / 1000.0)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.lost = False  # set True if a tick observed a token-fence failure

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name=f"mce-heartbeat-{self._job_id}", daemon=True
        )
        self._thread.start()

    def _run(self) -> None:
        # Renew on TTL/2 cadence until told to stop or the lock is lost.
        while not self._stop.wait(self._interval_s):
            try:
                if not renew_lock(self._conn, self._job_id, self._lock_token, self._lease_ms):
                    # Token-fence failure: job was reclaimed → lock lost.
                    self.lost = True
                    logger.warning(
                        "heartbeat lost lock for job %s (token=%s) — reclaimed",
                        self._job_id,
                        self._lock_token,
                    )
                    return
            except Exception:
                # Best-effort like gbrain's tick: a transient renew error does
                # not crash the worker; the next tick retries. If it persists
                # past lock_until, the reaper (W2.7) reclaims the slug.
                logger.exception("heartbeat renew error for job %s", self._job_id)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval_s * 2 + 1.0)
            self._thread = None


# ---------------------------------------------------------------------------
# JobLease — claim + heartbeat + release over ONE held connection (session-mode)
# ---------------------------------------------------------------------------
class JobLease:
    """Context manager: claim a job, heartbeat it, release on exit.

    Wraps the lifecycle gbrain's worker drives by hand (claim → setInterval
    renew → completeJob/failJob). Holds a SINGLE connection for the whole lease
    (gbrain's "session-mode pool" discipline, queue.ts:609) so the heartbeat
    and the claim share a connection the caller controls end-to-end.

    Usage::

        with JobLease(dsn=...) as lease:
            job = lease.claim()
            if job is None:
                ...            # nothing to do
            else:
                ... do work on job.slug ...
                # exit → complete_job(token) if no error, else fail_job

    On a clean ``with`` exit the job is completed; on an exception it is failed
    (retryable → ``delayed`` until max_attempts, then ``failed``). Both are
    token-fenced: if the heartbeat already observed a lost lock, the release is
    a no-op and the reclaiming worker stays authoritative.
    """

    def __init__(
        self,
        conn=None,
        dsn: str | None = None,
        lease_ms: int = DEFAULT_LEASE_MS,
        slug: str | None = None,
    ):
        self._owns_conn = conn is None
        self._conn = conn if conn is not None else get_connection(dsn)
        self._lease_ms = lease_ms
        self._slug = slug
        self._token = make_lock_token()
        self._job: ClaimedJob | None = None
        self._heartbeat: Heartbeat | None = None

    @property
    def token(self) -> str:
        return self._token

    @property
    def job(self) -> ClaimedJob | None:
        return self._job

    def claim(self) -> ClaimedJob | None:
        """Claim the next job and start the heartbeat. None if nothing waiting."""
        self._job = claim_job(self._conn, self._token, self._lease_ms, slug=self._slug)
        if self._job is not None:
            self._heartbeat = Heartbeat(self._conn, self._job.id, self._token, self._lease_ms)
            self._heartbeat.start()
        return self._job

    def renew(self) -> bool:
        """Manual renew (heartbeat does this automatically). Token-fenced."""
        if self._job is None:
            return False
        return renew_lock(self._conn, self._job.id, self._token, self._lease_ms)

    def complete(self) -> bool:
        if self._job is None:
            return False
        self._stop_heartbeat()
        return complete_job(self._conn, self._job.id, self._token)

    def fail(self, error_text: str, retry: bool = True) -> bool:
        if self._job is None:
            return False
        self._stop_heartbeat()
        # Retry as 'delayed' until attempts exhaust max_attempts, then terminal.
        if retry and self._job.attempts_made < self._job.max_attempts:
            status = STATUS_DELAYED
        else:
            status = STATUS_FAILED
        return fail_job(self._conn, self._job.id, self._token, error_text, status)

    def _stop_heartbeat(self) -> None:
        if self._heartbeat is not None:
            self._heartbeat.stop()
            self._heartbeat = None

    def __enter__(self) -> JobLease:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if self._job is not None:
                if exc_type is None:
                    self.complete()
                else:
                    self.fail(f"{exc_type.__name__}: {exc}", retry=True)
        finally:
            self._stop_heartbeat()
            if self._owns_conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
        return False  # never swallow exceptions
