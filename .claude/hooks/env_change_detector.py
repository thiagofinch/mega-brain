#!/usr/bin/env python3
"""
env_change_detector.py -- PostToolUse hook: detect new/rotated env keys, queue onboarding

Story: STORY-TIL-AUTOONBOARD (Wave 3, Awareness Layer)
Pattern model: .claude/hooks/invalidate_capability_embeddings.py

Trigger:
  PostToolUse on Write|Edit when target file path ends in `.env`
  (NOT `.env.example`, `.env.staging`, etc -- exact suffix match).

Flow:
  1. Parse current .env (KEY=value lines, skip blanks + `#` comments).
  2. Load snapshot from .data/env-snapshot.json (JSON map: key -> "sha256:hex").
  3. First-run guard (AC10): if snapshot missing AND .env has keys,
     bootstrap snapshot with current hashes, log INFO, exit 0 (no triggers).
  4. Diff:
        ADD     -> trigger gap check
        UPDATE  -> trigger gap check (credential rotation)
        DELETE  -> log INFO, remove from snapshot (AC11), no trigger
  5. For each ADD/UPDATE: cross-reference 3 sources:
        - services/INDEX.json (substring search for key name)
        - agents/_registry/capability-registry.yaml (substring search)
        - agents/_registry/ecosystem-registry.yaml (substring search)
     If ALL three mention the key -> already registered, skip.
     Else -> append entry to .data/env-change-pending-onboard.jsonl.
  6. Atomically update .data/env-snapshot.json.

Queue entry schema (jsonl):
  {"timestamp": "ISO", "key_name": "NEW_API_KEY",
   "action": "ADD|UPDATE", "snapshot_hash": "sha256:...",
   "gaps": ["services-index", "capability-registry", ...],
   "status": "pending-manual-trigger"}

AC12 decision: queue-only v1. Subprocess invocation deferred (TIL-AUTOONBOARD-V2).

Fail-open absolute: top-level try/except -> exit 0 on any exception.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import UTC, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
HOOK_TAG = "[env_change_detector]"

ENV_FILE = PROJECT_ROOT / ".env"
SNAPSHOT_FILE = PROJECT_ROOT / ".data" / "env-snapshot.json"
QUEUE_FILE = PROJECT_ROOT / ".data" / "env-change-pending-onboard.jsonl"

SERVICES_INDEX = PROJECT_ROOT / "services" / "INDEX.json"
CAPABILITY_REGISTRY = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
ECOSYSTEM_REGISTRY = PROJECT_ROOT / "agents" / "_registry" / "ecosystem-registry.yaml"

SNAPSHOT_SCHEMA_VERSION = "1.0"


def _log(msg: str) -> None:
    print(f"{HOOK_TAG} {msg}", file=sys.stderr)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _extract_file_path(event: dict) -> str | None:
    """Read tool_input.file_path / filePath / path from hook event."""
    tool_input = event.get("tool_input") or {}
    fp = tool_input.get("file_path") or tool_input.get("filePath") or tool_input.get("path")
    if not fp:
        return None
    return str(fp)


def _is_env_file(path_str: str) -> bool:
    """True only if the path's final component is exactly `.env`."""
    try:
        name = Path(path_str).name
    except (ValueError, OSError):
        return False
    return name == ".env"


def _parse_env(env_path: Path) -> dict[str, str]:
    """Parse KEY=value lines, skip blanks and `#` comments. Value kept raw (no quote strip)."""
    keys: dict[str, str] = {}
    if not env_path.exists():
        return keys
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return keys
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if not key:
            continue
        keys[key] = value
    return keys


def _hash_value(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_snapshot(path: Path) -> dict | None:
    """Return snapshot dict or None if missing/corrupted."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        _log(f"WARN snapshot read failed ({e}) -- treating as missing (fail-open)")
        return None


def _write_snapshot_atomic(path: Path, data: dict) -> None:
    """Write snapshot via temp + rename (atomic on POSIX)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix=".env-snapshot.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp_path, path)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _new_snapshot(env_keys: dict[str, str]) -> dict:
    return {
        "version": SNAPSHOT_SCHEMA_VERSION,
        "last_updated": _now_iso(),
        "keys": {k: _hash_value(v) for k, v in env_keys.items()},
    }


def _cross_reference(key_name: str) -> list[str]:
    """Return list of registry slugs where `key_name` is NOT mentioned.
    Empty list = key is fully registered (no gap)."""
    gaps: list[str] = []
    for slug, path in (
        ("services-index", SERVICES_INDEX),
        ("capability-registry", CAPABILITY_REGISTRY),
        ("ecosystem-registry", ECOSYSTEM_REGISTRY),
    ):
        try:
            if not path.exists():
                # Missing registry counts as a gap (system can't confirm coverage).
                gaps.append(slug)
                continue
            content = path.read_text(encoding="utf-8")
            if key_name not in content:
                gaps.append(slug)
        except OSError:
            gaps.append(slug)
    return gaps


def _mask(key: str) -> str:
    if len(key) <= 4:
        return key + "***"
    return key[:4] + "***"


def _append_queue(entry: dict) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _process_diff(
    current: dict[str, str], snapshot: dict
) -> tuple[list[tuple[str, str, str]], list[str]]:
    """
    Returns (triggers, deletes):
      triggers: list of (action, key_name, new_hash) for ADD/UPDATE
      deletes:  list of key_name removed from .env
    """
    snap_keys: dict[str, str] = (snapshot.get("keys") or {}) if isinstance(snapshot, dict) else {}
    triggers: list[tuple[str, str, str]] = []
    for k, v in current.items():
        new_hash = _hash_value(v)
        if k not in snap_keys:
            triggers.append(("ADD", k, new_hash))
        elif snap_keys.get(k) != new_hash:
            triggers.append(("UPDATE", k, new_hash))
    deletes = [k for k in snap_keys if k not in current]
    return triggers, deletes


def _run() -> int:
    # Parse hook event from stdin.
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return 0

    file_path = _extract_file_path(event)
    if not file_path:
        return 0
    if not _is_env_file(file_path):
        return 0

    # Only act on .env at the repository root (avoid stray .env files elsewhere).
    try:
        target_abs = Path(file_path).resolve()
    except (OSError, ValueError):
        return 0
    if target_abs != ENV_FILE.resolve():
        # Different .env (e.g., in a subdir of an unrelated repo) -- ignore.
        return 0

    current = _parse_env(ENV_FILE)
    snapshot = _load_snapshot(SNAPSHOT_FILE)

    # AC10: First-run guard.
    if snapshot is None:
        new_snap = _new_snapshot(current)
        try:
            _write_snapshot_atomic(SNAPSHOT_FILE, new_snap)
        except OSError as e:
            _log(f"WARN snapshot bootstrap write failed: {e} (fail-open)")
            return 0
        _log(
            f"INFO env_change_detector: snapshot bootstrap -- "
            f"{len(current)} keys recorded, no triggers fired"
        )
        return 0

    triggers, deletes = _process_diff(current, snapshot)

    # AC11: log + remove deletes from snapshot.
    for k in deletes:
        _log(f"INFO key deleted from .env: {_mask(k)} -- removed from snapshot, no trigger")

    # Process ADD/UPDATE: cross-reference, queue if gap.
    for action, key_name, new_hash in triggers:
        gaps = _cross_reference(key_name)
        if not gaps:
            _log(
                f"INFO key {_mask(key_name)} ({action}) already registered "
                f"in all 3 registries -- no gap, no queue"
            )
            continue
        entry = {
            "timestamp": _now_iso(),
            "key_name": key_name,
            "action": action,
            "snapshot_hash": new_hash,
            "gaps": gaps,
            "status": "pending-manual-trigger",
        }
        try:
            _append_queue(entry)
            _log(
                f"INFO queued onboarding for {_mask(key_name)} "
                f"action={action} gaps={','.join(gaps)}"
            )
        except OSError as e:
            _log(f"WARN queue write failed for {_mask(key_name)}: {e} (fail-open)")

    # Update snapshot to reflect current .env (covers ADD, UPDATE, DELETE).
    if triggers or deletes:
        new_snap = {
            "version": SNAPSHOT_SCHEMA_VERSION,
            "last_updated": _now_iso(),
            "keys": {k: _hash_value(v) for k, v in current.items()},
        }
        try:
            _write_snapshot_atomic(SNAPSHOT_FILE, new_snap)
        except OSError as e:
            _log(f"WARN snapshot write failed: {e} (fail-open)")

    return 0


def main() -> int:
    try:
        return _run()
    except Exception as e:
        _log(f"WARN unexpected error: {type(e).__name__}: {e} -- continuing without trigger")
        return 0


if __name__ == "__main__":
    sys.exit(main())
