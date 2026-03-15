"""
cache.py -- Two-Level Cache for MCE Pipeline
=============================================

L1: In-memory LRU dict (dies on process exit).
L2: Disk-based JSON files in ``.data/mce_cache/`` with 7-day TTL.

Cache key is SHA256 of ``(text + task)``.  Designed to wrap around
``GeminiAnalyzer.analyze()`` calls to avoid re-analyzing identical content.

Usage::

    from core.intelligence.pipeline.mce.cache import MCECache

    cache = MCECache()
    result = cache.get("abc123sha...")  # None on miss

    cache.set("abc123sha...", "HEURISTICS")
    result = cache.get("abc123sha...")  # "HEURISTICS"

    # Stats
    print(cache.stats)  # CacheStats(hits_l1=1, hits_l2=0, misses=1)

    # Cached wrapper
    from core.intelligence.pipeline.mce.cache import make_cache_key
    key = make_cache_key("some text", "classify_dna_layer")

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.cache")

# ---------------------------------------------------------------------------
# Imports: core.paths (with standalone fallback)
# ---------------------------------------------------------------------------

from core.paths import DATA, ROUTING

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_L1_MAX_SIZE: int = 1000
DEFAULT_TTL_SECONDS: int = 7 * 24 * 60 * 60  # 7 days


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_cache_key(text: str, task: str) -> str:
    """Generate a deterministic cache key from text and task.

    Uses SHA256 to produce a fixed-length hex string.

    Args:
        text: The input text.
        task: The task identifier.

    Returns:
        64-character hex string.
    """
    content = f"{task}:{text}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Cache Stats
# ---------------------------------------------------------------------------


@dataclass
class CacheStats:
    """Tracks cache hit/miss counters."""

    hits_l1: int = 0
    hits_l2: int = 0
    misses: int = 0

    @property
    def total_hits(self) -> int:
        return self.hits_l1 + self.hits_l2

    @property
    def total_requests(self) -> int:
        return self.hits_l1 + self.hits_l2 + self.misses

    @property
    def hit_rate(self) -> float:
        """Return hit rate as a float 0.0-1.0.  Returns 0.0 if no requests."""
        total = self.total_requests
        if total == 0:
            return 0.0
        return self.total_hits / total

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits_l1": self.hits_l1,
            "hits_l2": self.hits_l2,
            "misses": self.misses,
            "total_hits": self.total_hits,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 3),
        }


# ---------------------------------------------------------------------------
# L1: Memory Cache (LRU)
# ---------------------------------------------------------------------------


class _L1Cache:
    """In-memory LRU cache backed by ``OrderedDict``.

    Evicts least-recently-used entries when ``max_size`` is exceeded.
    Dies on process exit by design.
    """

    __slots__ = ("_data", "_max_size")

    def __init__(self, max_size: int = DEFAULT_L1_MAX_SIZE) -> None:
        self._data: OrderedDict[str, str] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> str | None:
        """Get value by key, returning None on miss. Moves to end (MRU)."""
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def set(self, key: str, value: str) -> None:
        """Set key-value pair. Evicts LRU if at capacity."""
        if key in self._data:
            self._data.move_to_end(key)
            self._data[key] = value
            return

        if len(self._data) >= self._max_size:
            self._data.popitem(last=False)  # Evict LRU

        self._data[key] = value

    def clear(self) -> None:
        """Clear all entries."""
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)


# ---------------------------------------------------------------------------
# L2: Disk Cache (JSON files, TTL-based)
# ---------------------------------------------------------------------------


class _L2Cache:
    """Disk-based cache using individual JSON files per key.

    Each entry is stored as a JSON file named ``{key}.json`` inside the
    cache directory.  Entries older than ``ttl_seconds`` are treated as
    expired (lazy eviction on read).

    Directory structure::

        .data/mce_cache/
        ├── abc123sha....json
        ├── def456sha....json
        └── ...
    """

    __slots__ = ("_dir", "_ttl")

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        if cache_dir is None:
            cache_dir = Path(ROUTING.get("mce_cache", DATA / "mce_cache"))
        self._dir = cache_dir
        self._ttl = ttl_seconds

    def get(self, key: str) -> str | None:
        """Get value by key from disk.  Returns None on miss or expiry."""
        path = self._key_path(key)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        # Check TTL
        stored_at = data.get("stored_at", 0)
        if time.time() - stored_at > self._ttl:
            # Expired -- remove lazily
            try:
                path.unlink()
            except OSError:
                pass
            return None

        return data.get("value")

    def set(self, key: str, value: str) -> None:
        """Write key-value pair to disk as a JSON file."""
        self._dir.mkdir(parents=True, exist_ok=True)

        entry = {
            "key": key,
            "value": value,
            "stored_at": time.time(),
        }

        path = self._key_path(key)
        try:
            path.write_text(
                json.dumps(entry, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write L2 cache entry %s: %s", key[:12], exc)

    def clear(self) -> None:
        """Remove all cache files from disk."""
        if not self._dir.exists():
            return
        for path in self._dir.glob("*.json"):
            try:
                path.unlink()
            except OSError:
                pass

    def _key_path(self, key: str) -> Path:
        """Return the file path for a given cache key."""
        return self._dir / f"{key}.json"

    @property
    def cache_dir(self) -> Path:
        return self._dir

    def __len__(self) -> int:
        if not self._dir.exists():
            return 0
        return sum(1 for _ in self._dir.glob("*.json"))


# ---------------------------------------------------------------------------
# MCECache (unified two-level)
# ---------------------------------------------------------------------------


@dataclass
class MCECache:
    """Two-level cache for MCE pipeline analysis results.

    L1 (memory) is checked first, then L2 (disk).  On ``set``, both
    levels are written.

    Args:
        l1_max_size: Maximum entries in the in-memory LRU cache.
        cache_dir: Override disk cache directory (default: ``.data/mce_cache/``).
        ttl_seconds: Time-to-live for L2 disk entries (default: 7 days).
    """

    l1_max_size: int = DEFAULT_L1_MAX_SIZE
    cache_dir: Path | None = None
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    stats: CacheStats = field(default_factory=CacheStats)
    _l1: _L1Cache = field(default=None, repr=False)  # type: ignore[assignment]
    _l2: _L2Cache = field(default=None, repr=False)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._l1 = _L1Cache(max_size=self.l1_max_size)
        self._l2 = _L2Cache(cache_dir=self.cache_dir, ttl_seconds=self.ttl_seconds)

    def get(self, key: str) -> str | None:
        """Look up a cached value.

        Checks L1 (memory) first, then L2 (disk).  On L2 hit, the
        value is promoted to L1 for faster subsequent access.

        Args:
            key: Cache key (use :func:`make_cache_key` to generate).

        Returns:
            Cached value string, or *None* on miss.
        """
        # L1 check
        val = self._l1.get(key)
        if val is not None:
            self.stats.hits_l1 += 1
            logger.debug("Cache L1 HIT: %s", key[:12])
            return val

        # L2 check
        val = self._l2.get(key)
        if val is not None:
            self.stats.hits_l2 += 1
            # Promote to L1
            self._l1.set(key, val)
            logger.debug("Cache L2 HIT (promoted to L1): %s", key[:12])
            return val

        # Miss
        self.stats.misses += 1
        logger.debug("Cache MISS: %s", key[:12])
        return None

    def set(self, key: str, value: str) -> None:
        """Store a value in both cache levels.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._l1.set(key, value)
        self._l2.set(key, value)

    def clear(self) -> None:
        """Flush both cache levels and reset stats."""
        self._l1.clear()
        self._l2.clear()
        self.stats = CacheStats()
        logger.info("MCE cache cleared (both levels)")

    @property
    def l1_size(self) -> int:
        """Number of entries in L1 (memory)."""
        return len(self._l1)

    @property
    def l2_size(self) -> int:
        """Number of entries in L2 (disk)."""
        return len(self._l2)

    def __repr__(self) -> str:
        return f"MCECache(l1={self.l1_size}, l2={self.l2_size}, hit_rate={self.stats.hit_rate:.1%})"
