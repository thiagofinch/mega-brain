#!/usr/bin/env python3
"""
MEMORY MANAGER - Programmatic Memory API for Agents
=====================================================
Replaces file-based MEMORY.md editing with structured CRUD operations.

Backed by JSONL files per agent in .data/agent_memory/.
Supports: write, search, prune, consolidate, score.

Composite scoring: 0.5 * semantic_sim + 0.3 * recency + 0.2 * importance
Based on CrewAI/Mem0 best practices (Spy Squad research 2026-03-07).

Versao: 1.0.0
Data: 2026-03-07
"""

import hashlib
import json
import math
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
from core.paths import ROOT, DATA

MEMORY_DIR = DATA / "agent_memory"
SHARED_STORE = MEMORY_DIR / "_shared"
CONSOLIDATION_THRESHOLD = 0.85  # Cosine sim above this = merge candidates
PRUNE_MIN_SCORE = 0.1  # Entries below this get pruned
PRUNE_MAX_AGE_DAYS = 90  # Entries older than this lose score
MAX_ENTRIES_DEFAULT = 200  # Default max entries per agent

# Composite scoring weights (CrewAI validated defaults)
W_SEMANTIC = 0.5
W_RECENCY = 0.3
W_IMPORTANCE = 0.2


# ---------------------------------------------------------------------------
# MEMORY ENTRY MODEL
# ---------------------------------------------------------------------------
@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""

    content: str
    agent_id: str
    entry_id: str = ""
    scope: str = "long_term"  # long_term | session | core
    importance: float = 0.5  # 0.0 to 1.0
    tags: list[str] = field(default_factory=list)
    source: str = ""  # ^[FONTE:...] or batch ID
    created_at: float = 0.0  # Unix timestamp
    last_referenced: float = 0.0  # Unix timestamp
    reference_count: int = 0
    pinned: bool = False  # Pinned entries survive pruning

    def __post_init__(self):
        if not self.entry_id:
            content_hash = hashlib.md5(
                f"{self.agent_id}:{self.content[:100]}:{self.created_at}".encode()
            ).hexdigest()[:10]
            self.entry_id = f"mem_{content_hash}"
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.last_referenced == 0.0:
            self.last_referenced = self.created_at

    @property
    def age_days(self) -> float:
        return (time.time() - self.created_at) / 86400

    @property
    def recency_score(self) -> float:
        """Exponential decay based on last reference time."""
        days_since = (time.time() - self.last_referenced) / 86400
        return math.exp(-0.05 * days_since)  # Half-life ~14 days

    @property
    def composite_score(self) -> float:
        """Overall score combining importance, recency, and reference count."""
        ref_score = min(self.reference_count / 10.0, 1.0)
        return (
            W_IMPORTANCE * self.importance + W_RECENCY * self.recency_score + W_SEMANTIC * ref_score
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# MEMORY STORE (per-agent JSONL backend)
# ---------------------------------------------------------------------------
class MemoryStore:
    """JSONL-backed memory store for a single agent."""

    def __init__(self, agent_id: str, store_dir: Path | None = None):
        self.agent_id = agent_id
        self.dir = (store_dir or MEMORY_DIR) / agent_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file = self.dir / "memories.jsonl"
        self._entries: dict[str, MemoryEntry] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._entries = {}
        if self.file.exists():
            for line in self.file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = MemoryEntry.from_dict(data)
                    self._entries[entry.entry_id] = entry
                except (json.JSONDecodeError, TypeError):
                    continue
        self._loaded = True

    def _save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(e.to_dict(), ensure_ascii=False)
            for e in sorted(self._entries.values(), key=lambda x: -x.composite_score)
        ]
        self.file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @property
    def entries(self) -> list[MemoryEntry]:
        self._ensure_loaded()
        return list(self._entries.values())

    @property
    def count(self) -> int:
        self._ensure_loaded()
        return len(self._entries)

    # ── CRUD ────────────────────────────────────────────────────────

    def write(self, content: str, **kwargs) -> MemoryEntry:
        """Write a new memory entry.

        Args:
            content: The memory content
            **kwargs: importance, tags, source, scope, pinned
        """
        self._ensure_loaded()
        entry = MemoryEntry(
            content=content,
            agent_id=self.agent_id,
            **kwargs,
        )
        self._entries[entry.entry_id] = entry
        self._save()
        return entry

    def read(self, entry_id: str) -> MemoryEntry | None:
        """Read a specific memory entry and increment reference count."""
        self._ensure_loaded()
        entry = self._entries.get(entry_id)
        if entry:
            entry.reference_count += 1
            entry.last_referenced = time.time()
            self._save()
        return entry

    def update(self, entry_id: str, **kwargs) -> MemoryEntry | None:
        """Update fields of an existing entry."""
        self._ensure_loaded()
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        for k, v in kwargs.items():
            if hasattr(entry, k) and k not in ("entry_id", "agent_id"):
                setattr(entry, k, v)
        self._save()
        return entry

    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        self._ensure_loaded()
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._save()
            return True
        return False

    # ── SEARCH ──────────────────────────────────────────────────────

    def search(
        self, query: str, top_k: int = 10, scope: str | None = None, tags: list[str] | None = None
    ) -> list[MemoryEntry]:
        """Search memories by keyword relevance + composite score.

        Uses keyword matching weighted by composite_score.
        For semantic search, use the RAG pipeline instead.
        """
        self._ensure_loaded()
        query_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", query.lower()))
        if not query_tokens:
            return self.top(top_k, scope=scope, tags=tags)

        scored: list[tuple[MemoryEntry, float]] = []
        for entry in self._entries.values():
            if scope and entry.scope != scope:
                continue
            if tags and not set(tags) & set(entry.tags):
                continue

            content_lower = entry.content.lower()
            content_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", content_lower))
            overlap = query_tokens & content_tokens
            if not overlap:
                continue

            keyword_score = len(overlap) / max(len(query_tokens), 1)
            # Composite: keyword relevance (acts as semantic proxy) + recency + importance
            final_score = (
                W_SEMANTIC * keyword_score
                + W_RECENCY * entry.recency_score
                + W_IMPORTANCE * entry.importance
            )
            scored.append((entry, final_score))

            # Increment reference (this entry was relevant)
            entry.reference_count += 1
            entry.last_referenced = time.time()

        scored.sort(key=lambda x: -x[1])
        if scored:
            self._save()
        return [e for e, _ in scored[:top_k]]

    def top(
        self, n: int = 10, scope: str | None = None, tags: list[str] | None = None
    ) -> list[MemoryEntry]:
        """Get top N entries by composite score."""
        self._ensure_loaded()
        entries = list(self._entries.values())
        if scope:
            entries = [e for e in entries if e.scope == scope]
        if tags:
            entries = [e for e in entries if set(tags) & set(e.tags)]
        entries.sort(key=lambda e: -e.composite_score)
        return entries[:n]

    # ── PRUNE ───────────────────────────────────────────────────────

    def prune(
        self, max_entries: int = MAX_ENTRIES_DEFAULT, min_score: float = PRUNE_MIN_SCORE
    ) -> dict:
        """Remove low-value entries, keeping pinned and high-scoring ones.

        Strategy:
        1. Never prune pinned entries
        2. Never prune core scope entries
        3. Remove entries below min_score
        4. If still over max_entries, remove lowest scoring
        """
        self._ensure_loaded()
        before = len(self._entries)

        # Separate protected vs pruneable
        protected = {eid: e for eid, e in self._entries.items() if e.pinned or e.scope == "core"}
        pruneable = {eid: e for eid, e in self._entries.items() if eid not in protected}

        # Remove below min_score
        pruned_ids = []
        for eid, entry in list(pruneable.items()):
            if entry.composite_score < min_score:
                pruned_ids.append(eid)
                del pruneable[eid]

        # If still over limit, remove lowest scoring
        if len(protected) + len(pruneable) > max_entries:
            sorted_pruneable = sorted(pruneable.items(), key=lambda x: x[1].composite_score)
            excess = len(protected) + len(pruneable) - max_entries
            for eid, _ in sorted_pruneable[:excess]:
                pruned_ids.append(eid)
                del pruneable[eid]

        # Rebuild entries
        self._entries = {**protected, **pruneable}
        self._save()

        return {
            "before": before,
            "after": len(self._entries),
            "pruned": len(pruned_ids),
            "pruned_ids": pruned_ids,
            "protected": len(protected),
        }

    # ── CONSOLIDATE ─────────────────────────────────────────────────

    def consolidate(self) -> dict:
        """Merge near-duplicate entries using token overlap as similarity proxy.

        If two entries have > CONSOLIDATION_THRESHOLD token overlap,
        they are candidates for merging. The merged entry keeps
        the higher importance, combined tags, and summed reference counts.
        """
        self._ensure_loaded()
        merged_count = 0
        entries_list = list(self._entries.values())
        to_remove: set[str] = set()

        for i, a in enumerate(entries_list):
            if a.entry_id in to_remove:
                continue
            a_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", a.content.lower()))
            if not a_tokens:
                continue

            for b in entries_list[i + 1 :]:
                if b.entry_id in to_remove:
                    continue
                b_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", b.content.lower()))
                if not b_tokens:
                    continue

                # Jaccard similarity
                intersection = len(a_tokens & b_tokens)
                union = len(a_tokens | b_tokens)
                similarity = intersection / max(union, 1)

                if similarity >= CONSOLIDATION_THRESHOLD:
                    # Merge b into a
                    if len(b.content) > len(a.content):
                        a.content = b.content  # Keep longer version
                    a.importance = max(a.importance, b.importance)
                    a.reference_count += b.reference_count
                    a.tags = list(set(a.tags + b.tags))
                    a.last_referenced = max(a.last_referenced, b.last_referenced)
                    to_remove.add(b.entry_id)
                    merged_count += 1

        for eid in to_remove:
            del self._entries[eid]

        if to_remove:
            self._save()

        return {
            "merged": merged_count,
            "removed": len(to_remove),
            "remaining": len(self._entries),
        }

    # ── EXPORT ──────────────────────────────────────────────────────

    def export_for_context(
        self, query: str | None = None, max_entries: int = 20, max_chars: int = 8000
    ) -> str:
        """Export memories formatted for LLM context injection.

        If query provided, uses search relevance.
        Otherwise uses composite score ranking.
        """
        if query:
            entries = self.search(query, top_k=max_entries)
        else:
            entries = self.top(max_entries)

        lines = []
        total = 0
        for entry in entries:
            line = f"- [{entry.scope}] {entry.content}"
            if entry.source:
                line += f" {entry.source}"
            if total + len(line) > max_chars:
                break
            lines.append(line)
            total += len(line)

        return "\n".join(lines)

    def stats(self) -> dict:
        """Get memory store statistics."""
        self._ensure_loaded()
        scopes: dict[str, int] = {}
        total_refs = 0
        pinned = 0
        for e in self._entries.values():
            scopes[e.scope] = scopes.get(e.scope, 0) + 1
            total_refs += e.reference_count
            if e.pinned:
                pinned += 1

        return {
            "agent_id": self.agent_id,
            "total_entries": len(self._entries),
            "by_scope": scopes,
            "pinned": pinned,
            "total_references": total_refs,
            "avg_importance": (
                sum(e.importance for e in self._entries.values()) / max(len(self._entries), 1)
            ),
            "avg_composite_score": (
                sum(e.composite_score for e in self._entries.values()) / max(len(self._entries), 1)
            ),
        }


# ---------------------------------------------------------------------------
# SHARED MEMORY STORE (cross-agent)
# ---------------------------------------------------------------------------
class SharedMemoryStore(MemoryStore):
    """Shared memory store that all agents can read/write.

    Stores inter-agent agreements, conclave decisions,
    and cross-cutting knowledge.
    """

    def __init__(self):
        super().__init__(agent_id="_shared", store_dir=MEMORY_DIR)

    def write(self, content: str, **kwargs) -> MemoryEntry:
        """Write to shared store. Requires agents_involved tag."""
        agents = kwargs.pop("agents_involved", [])
        tags = kwargs.get("tags", [])
        tags.extend([f"agent:{a}" for a in agents])
        kwargs["tags"] = tags
        return super().write(content, **kwargs)

    def search_by_agent(self, agent_id: str, top_k: int = 10) -> list[MemoryEntry]:
        """Search shared memories that involve a specific agent."""
        return self.search(f"agent:{agent_id}", top_k=top_k, tags=[f"agent:{agent_id}"])


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------
_stores: dict[str, MemoryStore] = {}


def get_store(agent_id: str) -> MemoryStore:
    """Get or create a memory store for an agent."""
    if agent_id not in _stores:
        _stores[agent_id] = MemoryStore(agent_id)
    return _stores[agent_id]


def get_shared_store() -> SharedMemoryStore:
    """Get the shared memory store."""
    key = "_shared"
    if key not in _stores:
        _stores[key] = SharedMemoryStore()
    return _stores[key]


def memory_write(agent_id: str, content: str, **kwargs) -> MemoryEntry:
    """Write a memory entry for an agent."""
    return get_store(agent_id).write(content, **kwargs)


def memory_search(agent_id: str, query: str, top_k: int = 10) -> list[MemoryEntry]:
    """Search an agent's memories."""
    return get_store(agent_id).search(query, top_k=top_k)


def memory_prune(agent_id: str, max_entries: int = MAX_ENTRIES_DEFAULT) -> dict:
    """Prune an agent's low-value memories."""
    return get_store(agent_id).prune(max_entries=max_entries)


def memory_consolidate(agent_id: str) -> dict:
    """Consolidate near-duplicate memories for an agent."""
    return get_store(agent_id).consolidate()


def shared_write(content: str, **kwargs) -> MemoryEntry:
    """Write to the shared cross-agent memory store."""
    return get_shared_store().write(content, **kwargs)


def shared_search(query: str, top_k: int = 10) -> list[MemoryEntry]:
    """Search the shared cross-agent memory store."""
    return get_shared_store().search(query, top_k=top_k)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print(
            "  memory_manager.py write <agent_id> <content> [--importance 0.8] [--tags tag1,tag2]"
        )
        print("  memory_manager.py search <agent_id> <query> [--top-k 10]")
        print("  memory_manager.py prune <agent_id> [--max-entries 200]")
        print("  memory_manager.py consolidate <agent_id>")
        print("  memory_manager.py stats <agent_id>")
        print("  memory_manager.py shared-write <content> [--agents a1,a2]")
        print("  memory_manager.py shared-search <query>")
        sys.exit(1)

    cmd = sys.argv[1]
    agent_id = sys.argv[2]

    print(f"\n{'=' * 60}")
    print("MEMORY MANAGER")
    print(f"{'=' * 60}\n")

    if cmd == "write":
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        importance = 0.5
        tags: list[str] = []
        for i, arg in enumerate(sys.argv):
            if arg == "--importance" and i + 1 < len(sys.argv):
                importance = float(sys.argv[i + 1])
            if arg == "--tags" and i + 1 < len(sys.argv):
                tags = sys.argv[i + 1].split(",")
        entry = memory_write(agent_id, content, importance=importance, tags=tags)
        print(f"Written: {entry.entry_id}")
        print(f"Content: {entry.content[:100]}...")
        print(f"Importance: {entry.importance}")
        print(f"Score: {entry.composite_score:.3f}")

    elif cmd == "search":
        query = sys.argv[3] if len(sys.argv) > 3 else ""
        top_k = 10
        for i, arg in enumerate(sys.argv):
            if arg == "--top-k" and i + 1 < len(sys.argv):
                top_k = int(sys.argv[i + 1])
        results = memory_search(agent_id, query, top_k=top_k)
        print(f"Results for '{query}' ({len(results)}):\n")
        for r in results:
            print(
                f"  [{r.entry_id}] score={r.composite_score:.3f} "
                f"refs={r.reference_count} imp={r.importance}"
            )
            print(f"    {r.content[:120]}...")
            print()

    elif cmd == "prune":
        max_entries = MAX_ENTRIES_DEFAULT
        for i, arg in enumerate(sys.argv):
            if arg == "--max-entries" and i + 1 < len(sys.argv):
                max_entries = int(sys.argv[i + 1])
        result = memory_prune(agent_id, max_entries=max_entries)
        print(f"Before: {result['before']}")
        print(f"After: {result['after']}")
        print(f"Pruned: {result['pruned']}")
        print(f"Protected: {result['protected']}")

    elif cmd == "consolidate":
        result = memory_consolidate(agent_id)
        print(f"Merged: {result['merged']}")
        print(f"Removed: {result['removed']}")
        print(f"Remaining: {result['remaining']}")

    elif cmd == "stats":
        s = get_store(agent_id).stats()
        print(f"Agent: {s['agent_id']}")
        print(f"Total: {s['total_entries']}")
        print(f"Pinned: {s['pinned']}")
        print(f"Scopes: {s['by_scope']}")
        print(f"Avg importance: {s['avg_importance']:.2f}")
        print(f"Avg composite: {s['avg_composite_score']:.3f}")
        print(f"Total refs: {s['total_references']}")

    elif cmd == "shared-write":
        content = agent_id  # agent_id slot used as content
        agents: list[str] = []
        for i, arg in enumerate(sys.argv):
            if arg == "--agents" and i + 1 < len(sys.argv):
                agents = sys.argv[i + 1].split(",")
        entry = shared_write(content, agents_involved=agents)
        print(f"Shared entry: {entry.entry_id}")

    elif cmd == "shared-search":
        query = agent_id
        results = shared_search(query)
        print(f"Shared results for '{query}' ({len(results)}):")
        for r in results:
            print(f"  [{r.entry_id}] {r.content[:100]}...")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
