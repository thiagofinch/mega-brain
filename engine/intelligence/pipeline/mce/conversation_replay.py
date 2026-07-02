"""
conversation_replay.py -- Conversation Replay & Run Diffing
============================================================

Post-mortem replay of MCE pipeline conversations and cross-run
comparison.  Reads existing JSONL audit logs (``mce-orchestrate.jsonl``
and ``mce-metrics.jsonl``) without introducing any new log format.

Two primary operations:

- **replay(slug)** -- reconstructs the full timeline of a pipeline run
  as a sorted ``List[ReplayEvent]``, one event per JSONL log entry
  matching the slug.

- **diff(slug, run_a, run_b)** -- compares two runs of the same slug
  and returns ``List[DiffEntry]`` with field-level differences.

Run identification:
    A "run" is delimited by consecutive JSONL entries for the same slug.
    Runs are separated by ``finalize`` commands (terminal boundary) or
    by a gap > 1 hour between entries.  Each run gets an ordinal ID
    (``run_0``, ``run_1``, ...) assigned chronologically.

Usage::

    from engine.intelligence.pipeline.mce.conversation_replay import (
        ReplayEvent,
        DiffEntry,
        replay,
        diff,
    )

    events = replay("alex-hormozi")
    diffs  = diff("alex-hormozi", "run_0", "run_1")

Constraints:
    - stdlib + json only (no LLM calls, no new dependencies).
    - Never mutates log files (read-only).
    - Operates on existing JSONL format -- no new log schema.

Version: 1.0.0
Date: 2026-04-01
Story: MCE21-2.2
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.conversation_replay")

# ---------------------------------------------------------------------------
# Paths: resolve LOGS directory with standalone fallback
# ---------------------------------------------------------------------------

try:
    from engine.paths import LOGS
except (ImportError, NameError, Exception):
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    LOGS = _ROOT / "logs"

_ORCHESTRATE_LOG = LOGS / "mce-orchestrate.jsonl"
_METRICS_LOG = LOGS / "mce-metrics.jsonl"

# Run-boundary gap threshold in seconds (1 hour).
_RUN_GAP_SECONDS: float = 3600.0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ReplayEvent:
    """A single event in a pipeline conversation timeline.

    Each event maps 1:1 to a JSONL log entry filtered by slug.

    Attributes:
        timestamp: ISO 8601 timestamp of the event.
        step_id: The pipeline command that produced this event
                 (e.g. ``"ingest"``, ``"batch"``, ``"finalize"``).
        action: Human-readable action description (success/failure + command).
        input_summary: Summarized input data (file path, slug, config).
        output_summary: Summarized output data (key results).
        duration_ms: Wall-clock duration of this step in milliseconds.
    """

    timestamp: str = ""
    step_id: str = ""
    action: str = ""
    input_summary: str = ""
    output_summary: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize for observability and logging."""
        return {
            "timestamp": self.timestamp,
            "step_id": self.step_id,
            "action": self.action,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "duration_ms": self.duration_ms,
        }


@dataclass
class DiffEntry:
    """A single field-level difference between two pipeline runs.

    Attributes:
        step_id: The pipeline step where the difference occurs.
        field: Dot-path to the differing field (e.g. ``"classification.confidence"``).
        run_a_value: Value in run A (or ``None`` if absent).
        run_b_value: Value in run B (or ``None`` if absent).
        change_type: One of ``"added"``, ``"removed"``, ``"changed"``.
    """

    step_id: str = ""
    field: str = ""
    run_a_value: Any = None
    run_b_value: Any = None
    change_type: str = ""  # "added" | "removed" | "changed"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for observability and logging."""
        return {
            "step_id": self.step_id,
            "field": self.field,
            "run_a_value": self.run_a_value,
            "run_b_value": self.run_b_value,
            "change_type": self.change_type,
        }


# ---------------------------------------------------------------------------
# JSONL Reading
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read all lines from a JSONL file.  Returns empty list on failure."""
    if not path.exists():
        logger.debug("JSONL file not found: %s", path)
        return []
    entries: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict):
                        entries.append(entry)
                except json.JSONDecodeError:
                    logger.debug("Skipped malformed JSONL line %d in %s", line_num, path)
    except OSError as exc:
        logger.warning("Failed to read JSONL %s: %s", path, exc)
    return entries


def _filter_by_slug(entries: list[dict[str, Any]], slug: str) -> list[dict[str, Any]]:
    """Filter JSONL entries by slug (matches 'slug' or 'pipeline' field)."""
    result: list[dict[str, Any]] = []
    for entry in entries:
        entry_slug = entry.get("slug") or entry.get("pipeline") or ""
        if entry_slug == slug:
            result.append(entry)
    return result


def _parse_timestamp(ts: str) -> datetime:
    """Parse an ISO 8601 timestamp string to a timezone-aware datetime.

    Handles both ``+00:00`` and ``Z`` suffixes.  Falls back to
    ``datetime.min`` (UTC) if parsing fails so sorting still works.
    """
    if not ts:
        return datetime.min.replace(tzinfo=UTC)
    try:
        # Python 3.11+ handles Z natively; older versions need the replace.
        cleaned = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return datetime.min.replace(tzinfo=UTC)


# ---------------------------------------------------------------------------
# Run Segmentation
# ---------------------------------------------------------------------------


def _segment_runs(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Segment a slug's entries into distinct runs.

    A run boundary is detected when:
    1. A ``finalize`` command appears (terminal step).
    2. The time gap between consecutive entries exceeds ``_RUN_GAP_SECONDS``.

    Returns:
        Dict mapping ``run_0``, ``run_1``, ... to their entry lists.
    """
    if not entries:
        return {}

    # Sort by timestamp first
    sorted_entries = sorted(entries, key=lambda e: _parse_timestamp(e.get("timestamp", "")))

    runs: dict[str, list[dict[str, Any]]] = {}
    current_run: list[dict[str, Any]] = []
    run_idx = 0

    for i, entry in enumerate(sorted_entries):
        current_run.append(entry)

        # Check for run boundary
        is_finalize = entry.get("command") == "finalize"
        is_last = i == len(sorted_entries) - 1

        # Check time gap to next entry
        has_gap = False
        if not is_last:
            current_ts = _parse_timestamp(entry.get("timestamp", ""))
            next_ts = _parse_timestamp(sorted_entries[i + 1].get("timestamp", ""))
            gap_seconds = (next_ts - current_ts).total_seconds()
            has_gap = gap_seconds > _RUN_GAP_SECONDS

        if is_finalize or has_gap or is_last:
            if current_run:
                runs[f"run_{run_idx}"] = current_run
                current_run = []
                run_idx += 1

    return runs


# ---------------------------------------------------------------------------
# Event Extraction
# ---------------------------------------------------------------------------


def _summarize_input(entry: dict[str, Any]) -> str:
    """Extract a human-readable input summary from a JSONL entry."""
    command = entry.get("command", "")
    parts: list[str] = []

    if command == "ingest":
        fp = entry.get("file_path", "")
        if fp:
            parts.append(f"file={Path(fp).name}")
    elif command == "batch":
        scan = entry.get("scan_summary", {})
        if isinstance(scan, dict):
            parts.append(f"files_scanned={scan.get('files_scanned', '?')}")
    elif command == "finalize":
        state = entry.get("state", {})
        if isinstance(state, dict):
            parts.append(f"from_state={state.get('current', '?')}")
    elif command == "full":
        fp = entry.get("file_path", "")
        if fp:
            parts.append(f"file={Path(fp).name}")

    slug = entry.get("slug", "")
    if slug:
        parts.insert(0, f"slug={slug}")

    return "; ".join(parts) if parts else f"slug={entry.get('slug', 'unknown')}"


def _summarize_output(entry: dict[str, Any]) -> str:
    """Extract a human-readable output summary from a JSONL entry."""
    command = entry.get("command", "")
    parts: list[str] = []
    success = entry.get("success", False)

    if command == "ingest":
        cls_data = entry.get("classification", {})
        if isinstance(cls_data, dict):
            bucket = cls_data.get("primary_bucket", "?")
            conf = cls_data.get("confidence", 0)
            parts.append(f"bucket={bucket}")
            parts.append(f"confidence={conf}")
        routing = entry.get("routing", {})
        if isinstance(routing, dict):
            action = routing.get("action", "?")
            parts.append(f"route={action}")

    elif command == "batch":
        batches = entry.get("batches_for_slug", [])
        parts.append(f"batches_created={len(batches)}")

    elif command == "finalize":
        enrichment = entry.get("enrichment", {})
        if isinstance(enrichment, dict):
            appended = enrichment.get("appended", 0)
            parts.append(f"enriched={appended}")
        metrics = entry.get("metrics", {})
        if isinstance(metrics, dict):
            duration = metrics.get("total_duration_seconds", 0)
            parts.append(f"total_duration={duration}s")
        state = entry.get("state", {})
        if isinstance(state, dict):
            parts.append(f"status={state.get('metadata_status', '?')}")

    elif command == "full":
        state = entry.get("state", {})
        if isinstance(state, dict):
            parts.append(f"final_state={state.get('current', '?')}")

    if not success:
        error = entry.get("error", "")
        if error:
            parts.append(f"error={error[:80]}")

    return "; ".join(parts) if parts else ("ok" if success else "failed")


def _entry_to_replay_event(entry: dict[str, Any]) -> ReplayEvent:
    """Convert a raw JSONL entry into a ReplayEvent."""
    command = entry.get("command", "unknown")
    success = entry.get("success", False)
    action_verb = "completed" if success else "failed"

    return ReplayEvent(
        timestamp=entry.get("timestamp", ""),
        step_id=command,
        action=f"{command} {action_verb}",
        input_summary=_summarize_input(entry),
        output_summary=_summarize_output(entry),
        duration_ms=entry.get("duration_ms", 0.0),
    )


# ---------------------------------------------------------------------------
# Diff Engine
# ---------------------------------------------------------------------------


def _flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dot-separated key paths.

    Example::

        {"a": {"b": 1, "c": 2}} -> {"a.b": 1, "a.c": 2}
    """
    result: dict[str, Any] = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, full_key))
        else:
            result[full_key] = value
    return result


def _diff_entries(
    step_id: str,
    entry_a: dict[str, Any],
    entry_b: dict[str, Any],
    skip_fields: frozenset[str] | None = None,
) -> list[DiffEntry]:
    """Compare two JSONL entries field-by-field and return differences.

    Args:
        step_id: The step identifier for context.
        entry_a: Flattened entry from run A.
        entry_b: Flattened entry from run B.
        skip_fields: Fields to exclude from comparison (timestamps, etc.).

    Returns:
        List of DiffEntry for each differing field.
    """
    if skip_fields is None:
        skip_fields = frozenset({"timestamp", "duration_ms"})

    flat_a = _flatten_dict(entry_a)
    flat_b = _flatten_dict(entry_b)

    diffs: list[DiffEntry] = []
    all_keys = sorted(set(flat_a.keys()) | set(flat_b.keys()))

    for key in all_keys:
        if key in skip_fields:
            continue

        in_a = key in flat_a
        in_b = key in flat_b

        if in_a and not in_b:
            diffs.append(
                DiffEntry(
                    step_id=step_id,
                    field=key,
                    run_a_value=flat_a[key],
                    run_b_value=None,
                    change_type="removed",
                )
            )
        elif not in_a and in_b:
            diffs.append(
                DiffEntry(
                    step_id=step_id,
                    field=key,
                    run_a_value=None,
                    run_b_value=flat_b[key],
                    change_type="added",
                )
            )
        elif flat_a[key] != flat_b[key]:
            diffs.append(
                DiffEntry(
                    step_id=step_id,
                    field=key,
                    run_a_value=flat_a[key],
                    run_b_value=flat_b[key],
                    change_type="changed",
                )
            )

    return diffs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def replay(slug: str, log_dir: str | None = None) -> list[ReplayEvent]:
    """Reconstruct the full timeline of a pipeline slug from JSONL logs.

    Reads ``mce-orchestrate.jsonl`` and ``mce-metrics.jsonl``, filters
    by slug, and returns a chronologically sorted list of ReplayEvents.

    Args:
        slug: The persona/source slug (e.g. ``"alex-hormozi"``).
        log_dir: Optional override for the logs directory.  If ``None``,
                 uses the default LOGS path from ``core.paths``.

    Returns:
        List of ReplayEvent sorted by timestamp (ascending).
        Empty list if no logs found for the slug.
    """
    if log_dir is not None:
        orch_path = Path(log_dir) / "mce-orchestrate.jsonl"
        metrics_path = Path(log_dir) / "mce-metrics.jsonl"
    else:
        orch_path = _ORCHESTRATE_LOG
        metrics_path = _METRICS_LOG

    # Read orchestrate entries (primary source)
    orch_entries = _filter_by_slug(_read_jsonl(orch_path), slug)

    # Read metrics entries (supplementary -- phase-level timing)
    metrics_entries = _filter_by_slug(_read_jsonl(metrics_path), slug)

    # Convert orchestrate entries to ReplayEvents
    events: list[ReplayEvent] = []
    for entry in orch_entries:
        events.append(_entry_to_replay_event(entry))

    # Convert metrics entries to ReplayEvents (phase summaries)
    for entry in metrics_entries:
        phases = entry.get("phases", {})
        phase_names = ", ".join(phases.keys()) if isinstance(phases, dict) else "?"
        total_dur = entry.get("total_duration_seconds", 0)

        events.append(
            ReplayEvent(
                timestamp=entry.get("timestamp", ""),
                step_id="metrics_summary",
                action="pipeline metrics recorded",
                input_summary=f"slug={slug}; phases={entry.get('phases_completed', 0)}",
                output_summary=f"total_duration={total_dur}s; phases=[{phase_names}]",
                duration_ms=total_dur * 1000 if isinstance(total_dur, (int, float)) else 0.0,
            )
        )

    # Sort by timestamp
    events.sort(key=lambda e: _parse_timestamp(e.timestamp))

    logger.info(
        "Replay for %s: %d events (%d orchestrate, %d metrics)",
        slug,
        len(events),
        len(orch_entries),
        len(metrics_entries),
    )
    return events


def diff(slug: str, run_a: str, run_b: str, log_dir: str | None = None) -> list[DiffEntry]:
    """Compare two pipeline runs for the same slug.

    Identifies runs from the JSONL logs, then compares them step-by-step
    to find field-level differences.

    Args:
        slug: The persona/source slug.
        run_a: Run identifier (e.g. ``"run_0"``).
        run_b: Run identifier (e.g. ``"run_1"``).
        log_dir: Optional override for the logs directory.

    Returns:
        List of DiffEntry describing all differences between the two runs.
        Empty list if runs are identical or not found.

    Raises:
        ValueError: If ``run_a`` or ``run_b`` are not found in the logs.
    """
    if log_dir is not None:
        orch_path = Path(log_dir) / "mce-orchestrate.jsonl"
    else:
        orch_path = _ORCHESTRATE_LOG

    all_entries = _filter_by_slug(_read_jsonl(orch_path), slug)
    runs = _segment_runs(all_entries)

    if run_a not in runs:
        raise ValueError(
            f"Run {run_a!r} not found for slug {slug!r}. Available: {sorted(runs.keys())}"
        )
    if run_b not in runs:
        raise ValueError(
            f"Run {run_b!r} not found for slug {slug!r}. Available: {sorted(runs.keys())}"
        )

    entries_a = runs[run_a]
    entries_b = runs[run_b]

    # Index entries by command (step_id) for alignment
    by_command_a: dict[str, list[dict[str, Any]]] = {}
    for e in entries_a:
        cmd = e.get("command", "unknown")
        by_command_a.setdefault(cmd, []).append(e)

    by_command_b: dict[str, list[dict[str, Any]]] = {}
    for e in entries_b:
        cmd = e.get("command", "unknown")
        by_command_b.setdefault(cmd, []).append(e)

    all_commands = sorted(set(by_command_a.keys()) | set(by_command_b.keys()))
    diffs: list[DiffEntry] = []

    for cmd in all_commands:
        list_a = by_command_a.get(cmd, [])
        list_b = by_command_b.get(cmd, [])

        # Compare paired entries (by position within same command)
        max_len = max(len(list_a), len(list_b))
        for i in range(max_len):
            step_label = f"{cmd}[{i}]" if max_len > 1 else cmd

            if i >= len(list_a):
                # Entry only in run_b
                diffs.append(
                    DiffEntry(
                        step_id=step_label,
                        field="(entire step)",
                        run_a_value=None,
                        run_b_value="present",
                        change_type="added",
                    )
                )
                continue

            if i >= len(list_b):
                # Entry only in run_a
                diffs.append(
                    DiffEntry(
                        step_id=step_label,
                        field="(entire step)",
                        run_a_value="present",
                        run_b_value=None,
                        change_type="removed",
                    )
                )
                continue

            # Both exist -- compare field by field
            diffs.extend(_diff_entries(step_label, list_a[i], list_b[i]))

    logger.info(
        "Diff for %s (%s vs %s): %d differences found",
        slug,
        run_a,
        run_b,
        len(diffs),
    )
    return diffs


def list_runs(slug: str, log_dir: str | None = None) -> list[str]:
    """List available run IDs for a slug.

    Convenience function for discovering run identifiers before calling
    ``diff()``.

    Args:
        slug: The persona/source slug.
        log_dir: Optional override for the logs directory.

    Returns:
        Sorted list of run identifiers (``["run_0", "run_1", ...]``).
    """
    if log_dir is not None:
        orch_path = Path(log_dir) / "mce-orchestrate.jsonl"
    else:
        orch_path = _ORCHESTRATE_LOG

    all_entries = _filter_by_slug(_read_jsonl(orch_path), slug)
    runs = _segment_runs(all_entries)
    return sorted(runs.keys())
