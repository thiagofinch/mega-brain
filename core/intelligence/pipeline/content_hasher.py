"""Content hashing for incremental pipeline processing.

Maintains a registry of SHA256 hashes for processed files.
When pipeline runs, only new/changed files are processed.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_REGISTRY = Path(".data/content_hashes.json")


def hash_file(file_path: str | Path) -> str:
    """Compute SHA256 hash of a file's content."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_text(text: str) -> str:
    """Compute SHA256 hash of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class HashRegistry:
    """Persistent registry of file content hashes.

    Tracks which files have been processed by storing their
    SHA256 hash. On next run, only files with new/changed
    hashes are selected for processing.
    """

    def __init__(self, registry_path: str | Path | None = None):
        self._path = Path(registry_path or DEFAULT_REGISTRY)
        self._hashes: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """Load registry from disk."""
        if self._path.exists():
            try:
                self._hashes = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._hashes = {}

    def _save(self) -> None:
        """Persist registry to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._hashes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def is_processed(self, file_path: str | Path) -> bool:
        """Check if a file has been processed (hash matches)."""
        file_path = Path(file_path)
        key = str(file_path)

        if key not in self._hashes:
            return False

        current_hash = hash_file(file_path)
        return self._hashes[key]["hash"] == current_hash

    def register(self, file_path: str | Path, batch_id: str | None = None) -> None:
        """Register a file as processed."""
        file_path = Path(file_path)
        self._hashes[str(file_path)] = {
            "hash": hash_file(file_path),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "batch_id": batch_id,
        }
        self._save()

    def register_batch(
        self, file_paths: list[str | Path], batch_id: str | None = None
    ) -> None:
        """Register multiple files as processed."""
        for fp in file_paths:
            fp = Path(fp)
            self._hashes[str(fp)] = {
                "hash": hash_file(fp),
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "batch_id": batch_id,
            }
        self._save()

    def filter_new(self, file_paths: list[str | Path]) -> list[Path]:
        """Filter list to only new/changed files (not yet processed)."""
        new_files = []
        for fp in file_paths:
            fp = Path(fp)
            if not self.is_processed(fp):
                new_files.append(fp)
        return new_files

    def unregister(self, file_path: str | Path) -> bool:
        """Remove a file from the registry (force reprocessing)."""
        key = str(Path(file_path))
        if key in self._hashes:
            del self._hashes[key]
            self._save()
            return True
        return False

    def clear(self) -> None:
        """Clear all hashes (force full reprocess)."""
        self._hashes = {}
        self._save()

    def count(self) -> int:
        """Return number of registered files."""
        return len(self._hashes)

    def stats(self) -> dict:
        """Return registry statistics."""
        return {
            "total_files": len(self._hashes),
            "registry_path": str(self._path),
            "registry_exists": self._path.exists(),
        }
