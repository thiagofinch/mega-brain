"""
SafeStateWriter — Atomic read-modify-write for JSON state files.

Protects shared state files (CHUNKS-STATE.json, INSIGHTS-STATE.json,
CANONICAL-MAP.json, NARRATIVES-STATE.json) against concurrent write
corruption using:
- threading.Lock per file path (intra-process serialization)
- fcntl.flock(LOCK_EX) (inter-process serialization)
- os.replace() for atomic writes (no partial reads)

Also provides JSONL sidecar helpers for high-frequency per-slug writes
that avoid read-modify-write overhead entirely (append-only, O(1)).

Usage:
    from engine.intelligence.pipeline.state_writer import SafeStateWriter, JsonlSidecar

    # Atomic read-modify-write with exclusive lock:
    with SafeStateWriter(Path("CHUNKS-STATE.json")) as state:
        state["my-slug"] = {"chunks": [...]}
    # Lock released, file atomically replaced

    # High-frequency append (no lock needed — POSIX atomic for small writes):
    sidecar = JsonlSidecar(Path(".claude/mission-control/mce/alex-hormozi/extractions.jsonl"))
    sidecar.append({"chunk_id": "c1", "content": "..."})

    # Merge all JSONL lines into a dict (for post-barrier merge phase):
    merged = sidecar.read_all()
"""

import fcntl
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

# Module-level registry of per-path threading locks.
# fcntl.flock is advisory and only works across processes —
# within the same process, threads share the lock table, so
# we need a threading.Lock per file to serialize intra-process access.
_lock_registry: dict[str, threading.Lock] = {}
_registry_lock = threading.Lock()


def _get_file_lock(file_path: Path) -> threading.Lock:
    """Get or create a threading.Lock for the given file path."""
    key = str(file_path.resolve())
    with _registry_lock:
        if key not in _lock_registry:
            _lock_registry[key] = threading.Lock()
        return _lock_registry[key]


class SafeStateWriter:
    """
    Context manager that wraps a JSON state file with:
    1. threading.Lock — serializes access within the same process
    2. fcntl.flock(LOCK_EX) — serializes access across processes
    3. Read + parse current content (or {} if new file)
    4. Yield mutable dict for caller to modify
    5. Serialize + write to unique temp file
    6. os.replace() — atomic rename (POSIX guarantees no partial reads)
    7. Release both locks

    This guarantees that the read-modify-write cycle is atomic:
    no other process/thread can interleave between read and write.

    Args:
        file_path: Path to the JSON state file.
        indent: JSON indent for readability (default 2).
    """

    def __init__(self, file_path: Path, indent: int = 2):
        self.file_path = Path(file_path)
        self.indent = indent
        self._fd: int | None = None
        self._data: dict[str, Any] = {}
        self._thread_lock: threading.Lock | None = None

    def __enter__(self) -> dict[str, Any]:
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Acquire thread-level lock first (intra-process serialization)
        self._thread_lock = _get_file_lock(self.file_path)
        self._thread_lock.acquire()

        # Open (or create) the lock file for flock
        # Using a dedicated .lock file avoids issues with os.replace removing
        # the file while another process holds an flock on it.
        lock_file = self.file_path.with_suffix(self.file_path.suffix + ".lock")
        self._fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)

        # Acquire exclusive flock (inter-process serialization)
        fcntl.flock(self._fd, fcntl.LOCK_EX)

        # Read current content of the actual state file
        try:
            with open(self.file_path) as f:
                content = f.read()
            if content.strip():
                self._data = json.loads(content)
            else:
                self._data = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

        return self._data

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Write atomically: serialize to unique temp file, then os.replace
                # Use tempfile in same dir to guarantee same filesystem (for atomic rename)
                dir_path = self.file_path.parent
                fd_tmp, tmp_path_str = tempfile.mkstemp(
                    suffix=".tmp",
                    prefix=self.file_path.stem + "_",
                    dir=str(dir_path),
                )
                try:
                    with os.fdopen(fd_tmp, "w") as f:
                        json.dump(self._data, f, indent=self.indent, ensure_ascii=False)
                    os.replace(tmp_path_str, str(self.file_path))
                except BaseException:
                    # Clean up temp file on failure
                    try:
                        os.unlink(tmp_path_str)
                    except OSError:
                        pass
                    raise
        finally:
            # Release flock and close fd
            if self._fd is not None:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                except OSError:
                    pass
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None

            # Release thread lock
            if self._thread_lock is not None:
                self._thread_lock.release()
                self._thread_lock = None

        # Do not suppress exceptions
        return False


class JsonlSidecar:
    """
    Append-only JSONL sidecar file for high-frequency writes.

    Each slug writes extraction results to its own .jsonl file.
    POSIX guarantees atomic append for small writes (< PIPE_BUF, typically 4096 bytes),
    so no lock is needed for single-line appends.

    Merging into canonical JSON state happens at the barrier phase (PIP-005),
    NOT during parallel processing.

    Args:
        file_path: Path to the .jsonl sidecar file.
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)

    def append(self, record: dict[str, Any]) -> None:
        """
        Append a single JSON record as one line.
        Creates the file and parent directories if they don't exist.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(self.file_path, "a") as f:
            f.write(line)

    def read_all(self) -> list[dict[str, Any]]:
        """
        Read all lines from the JSONL file and return as a list of dicts.
        Returns empty list if file doesn't exist.
        """
        if not self.file_path.exists():
            return []

        records = []
        with open(self.file_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def merge_into(self, target_state_path: Path, key_field: str = "id") -> int:
        """
        Merge JSONL records into a target JSON state file using SafeStateWriter.

        Each record is stored under its key_field value in the state dict.
        This should ONLY be called during the post-barrier merge phase.

        Args:
            target_state_path: Path to the canonical JSON state file.
            key_field: Field in each record to use as the dict key.

        Returns:
            Number of records merged.
        """
        records = self.read_all()
        if not records:
            return 0

        with SafeStateWriter(target_state_path) as state:
            for record in records:
                key = record.get(key_field, str(len(state)))
                state[key] = record

        return len(records)

    def clear(self) -> None:
        """Remove the sidecar file after successful merge."""
        if self.file_path.exists():
            self.file_path.unlink(missing_ok=True)
