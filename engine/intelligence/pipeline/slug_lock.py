"""
Slug Lock Manager — OS-level exclusive locking per slug.

Ensures that within a slug, processing is strictly serial.
Between slugs, full parallelism is allowed.

Lock file location: .claude/mission-control/mce/{slug}/.lock

Uses fcntl.flock (POSIX) / msvcrt.locking (Windows) for OS-level exclusive locking.
Includes stale lock detection via PID check.

Usage:
    from engine.intelligence.pipeline.slug_lock import SlugLockManager

    lock_mgr = SlugLockManager(base_dir=Path(".claude/mission-control/mce"))

    # As context manager (recommended — auto-releases on crash/exception):
    with lock_mgr.lock("alex-hormozi"):
        process_files_for_slug("alex-hormozi")

    # Manual acquire/release:
    lock_mgr.acquire("alex-hormozi")
    try:
        process_files_for_slug("alex-hormozi")
    finally:
        lock_mgr.release("alex-hormozi")
"""

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from engine.intelligence.pipeline._file_lock import lock_file, unlock_file


def _win_pid_alive(pid: int) -> bool:
    """Windows PID check: there os.kill(pid, 0) sends CTRL_C_EVENT instead of probing."""
    import ctypes
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    still_active = 259
    error_access_denied = 5
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        # Access denied means the process exists but belongs to another user
        return ctypes.get_last_error() == error_access_denied
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True
        return code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


class SlugLockManager:
    """
    Manages exclusive lock files per slug using fcntl.flock.

    Args:
        base_dir: Base directory where slug subdirectories live.
                  Default: .claude/mission-control/mce/
    """

    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            base_dir = Path(".claude/mission-control/mce")
        self.base_dir = Path(base_dir)
        # Track open file descriptors per slug for this instance
        self._fds: dict[str, int] = {}

    def _lock_path(self, slug: str) -> Path:
        """Return the lock file path for a given slug."""
        return self.base_dir / slug / ".lock"

    def _is_pid_alive(self, pid: int) -> bool:
        """Check if a process with the given PID is still running."""
        if sys.platform == "win32":
            return _win_pid_alive(pid)
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def _clean_stale_lock(self, lock_path: Path) -> bool:
        """
        Check if a lock file is stale (holding PID is dead).
        If stale, remove it and return True.
        If not stale (or no PID info), return False.
        """
        if not lock_path.exists():
            return False

        try:
            content = lock_path.read_text().strip()
            if content:
                pid = int(content)
                if not self._is_pid_alive(pid):
                    # PID is dead — stale lock
                    lock_path.unlink(missing_ok=True)
                    return True
        except (ValueError, OSError):
            # Can't read PID or file gone — treat as cleanable
            pass

        return False

    def acquire(self, slug: str) -> None:
        """
        Acquire an exclusive lock for the given slug.
        Blocks if another process holds the lock.
        Cleans stale locks from dead processes before blocking.

        Args:
            slug: The slug identifier to lock.
        """
        lock_path = self._lock_path(slug)

        # Ensure the slug directory exists
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for stale lock before attempting
        self._clean_stale_lock(lock_path)

        # Open (or create) the lock file
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)

        # Block until exclusive lock is acquired
        lock_file(fd)

        # Write our PID for stale detection
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, str(os.getpid()).encode())

        self._fds[slug] = fd

    def release(self, slug: str) -> None:
        """
        Release the lock for the given slug.
        No-op if the lock is not held by this instance.

        Args:
            slug: The slug identifier to unlock.
        """
        fd = self._fds.pop(slug, None)
        if fd is None:
            return

        try:
            unlock_file(fd)
        except OSError:
            pass

        try:
            os.close(fd)
        except OSError:
            pass

        # Remove the lock file
        lock_path = self._lock_path(slug)
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass

    @contextmanager
    def lock(self, slug: str):
        """
        Context manager for acquiring/releasing a slug lock.

        Guarantees release even if an exception is raised (crash safety).

        Usage:
            with lock_mgr.lock("my-slug"):
                do_work()
        """
        self.acquire(slug)
        try:
            yield
        finally:
            self.release(slug)
