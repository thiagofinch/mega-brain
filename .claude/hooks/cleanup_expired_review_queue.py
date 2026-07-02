#!/usr/bin/env python3
"""cleanup_expired_review_queue.py — SessionStart hook (Story MCE-4.4 AC7).

Scans all REVIEW-QUEUE.json files in .data/artifacts/canonical/*/REVIEW-QUEUE.json.
For each item where ttl < now AND status is PENDING or IN_REVIEW:
  - Updates status to EXPIRED.
  - Writes via atomic write.

Rules:
  - NEVER modifies RESOLVED, DISMISSED, or already-EXPIRED items.
  - Emits summary to stderr: "Cleanup: N items expired across K slugs"
  - Exceptions are caught and logged to stderr; hook always exits 0.
  - Kill switch: MCE_CLEANUP_EXPIRED_DISABLED=1 → silent exit 0.

Atomic write: temp file in same dir + os.replace (Veto V2 compliant).
Exit code: always 0 (Veto V6 — session must never be blocked by cleanup).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------

if os.environ.get("MCE_CLEANUP_EXPIRED_DISABLED", "").strip() == "1":
    sys.exit(0)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
_CANONICAL_ROOT = _PROJECT_ROOT / ".data" / "artifacts" / "canonical"

# Statuses that the cleanup hook is allowed to transition to EXPIRED
_EXPIRABLE_STATUSES = {"PENDING", "IN_REVIEW"}


# ---------------------------------------------------------------------------
# Atomic write helper
# ---------------------------------------------------------------------------


def _atomic_write_json(data: dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, str(target))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# TTL check
# ---------------------------------------------------------------------------


def _is_expired(ttl_str: str | None, now: datetime) -> bool:
    """Return True if ttl_str parses to a datetime before now."""
    if not ttl_str:
        return False
    try:
        ttl_dt = datetime.fromisoformat(ttl_str)
        # Normalize to UTC if no tzinfo
        if ttl_dt.tzinfo is None:
            ttl_dt = ttl_dt.replace(tzinfo=UTC)
        return ttl_dt < now
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Main cleanup logic
# ---------------------------------------------------------------------------


def _process_queue_file(path: Path, now: datetime) -> int:
    """Process a single REVIEW-QUEUE.json file. Returns number of items expired."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[cleanup_expired_review_queue] WARN: could not read {path}: {exc}", file=sys.stderr)
        return 0

    if not isinstance(raw, dict):
        return 0

    items = raw.get("items")
    if not isinstance(items, list):
        return 0

    expired_count = 0
    modified = False

    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status", "")
        if status not in _EXPIRABLE_STATUSES:
            continue  # RESOLVED, DISMISSED, EXPIRED — never touch
        if _is_expired(item.get("ttl"), now):
            item["status"] = "EXPIRED"
            expired_count += 1
            modified = True

    if modified:
        raw["last_updated"] = now.isoformat()
        try:
            _atomic_write_json(raw, path)
        except Exception as exc:
            print(
                f"[cleanup_expired_review_queue] WARN: could not write {path}: {exc}",
                file=sys.stderr,
            )
            return 0

    return expired_count


def main() -> None:
    if not _CANONICAL_ROOT.exists():
        # No canonical dir yet — nothing to do
        sys.exit(0)

    queue_files = list(_CANONICAL_ROOT.glob("*/REVIEW-QUEUE.json"))

    if not queue_files:
        sys.exit(0)

    now = datetime.now(UTC)
    total_expired = 0
    slugs_affected = 0

    for path in queue_files:
        try:
            count = _process_queue_file(path, now)
            if count > 0:
                total_expired += count
                slugs_affected += 1
        except Exception as exc:
            # Non-fatal — log and continue
            print(
                f"[cleanup_expired_review_queue] WARN: error processing {path}: {exc}",
                file=sys.stderr,
            )

    if total_expired > 0:
        print(
            f"[cleanup_expired_review_queue] Cleanup: {total_expired} items expired across {slugs_affected} slugs",
            file=sys.stderr,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never let any unhandled exception block the session
        print(f"[cleanup_expired_review_queue] FATAL (non-blocking): {exc}", file=sys.stderr)
    sys.exit(0)
