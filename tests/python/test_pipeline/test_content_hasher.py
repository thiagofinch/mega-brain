"""Tests for content_hasher — incremental pipeline processing via SHA256 hashes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.intelligence.pipeline.content_hasher import (
    HashRegistry,
    hash_file,
    hash_text,
)

# ---------------------------------------------------------------------------
# hash_file / hash_text
# ---------------------------------------------------------------------------


class TestHashFile:
    """Tests for the hash_file() function."""

    def test_consistent_hash_for_same_content(self, tmp_path: Path) -> None:
        """Same content produces identical SHA256 on repeated calls."""
        f = tmp_path / "a.txt"
        f.write_text("hello world", encoding="utf-8")
        assert hash_file(f) == hash_file(f)

    def test_different_hash_for_different_content(self, tmp_path: Path) -> None:
        """Different content produces different SHA256."""
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello", encoding="utf-8")
        f2.write_text("world", encoding="utf-8")
        assert hash_file(f1) != hash_file(f2)

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError when the file does not exist."""
        with pytest.raises(FileNotFoundError):
            hash_file(tmp_path / "ghost.txt")


class TestHashText:
    """Tests for the hash_text() function."""

    def test_consistent_hash(self) -> None:
        """Same string produces identical SHA256."""
        assert hash_text("pickle") == hash_text("pickle")

    def test_different_strings_differ(self) -> None:
        """Different strings produce different SHA256."""
        assert hash_text("pickle") != hash_text("rick")


# ---------------------------------------------------------------------------
# HashRegistry
# ---------------------------------------------------------------------------


class TestHashRegistry:
    """Tests for the HashRegistry class."""

    def test_creates_registry_file_on_first_save(self, tmp_path: Path) -> None:
        """Registry file is created when the first entry is saved."""
        reg_file = tmp_path / "reg.json"
        reg = HashRegistry(reg_file)

        f = tmp_path / "data.txt"
        f.write_text("content", encoding="utf-8")
        reg.register(f)

        assert reg_file.exists()

    def test_is_processed_false_for_new_file(self, tmp_path: Path) -> None:
        """A file never registered returns False."""
        reg = HashRegistry(tmp_path / "reg.json")
        f = tmp_path / "new.txt"
        f.write_text("new", encoding="utf-8")
        assert reg.is_processed(f) is False

    def test_register_marks_file_processed(self, tmp_path: Path) -> None:
        """After register(), is_processed() returns True."""
        reg = HashRegistry(tmp_path / "reg.json")
        f = tmp_path / "doc.txt"
        f.write_text("document", encoding="utf-8")

        reg.register(f, batch_id="BATCH-001")
        assert reg.is_processed(f) is True

    def test_is_processed_false_after_content_change(self, tmp_path: Path) -> None:
        """If file content changes after registration, is_processed() returns False."""
        reg = HashRegistry(tmp_path / "reg.json")
        f = tmp_path / "mutable.txt"
        f.write_text("v1", encoding="utf-8")
        reg.register(f)

        # mutate
        f.write_text("v2", encoding="utf-8")
        assert reg.is_processed(f) is False

    def test_filter_new_returns_only_unprocessed(self, tmp_path: Path) -> None:
        """filter_new() keeps files not yet registered or changed."""
        reg = HashRegistry(tmp_path / "reg.json")

        old = tmp_path / "old.txt"
        old.write_text("old", encoding="utf-8")
        reg.register(old)

        new = tmp_path / "new.txt"
        new.write_text("new", encoding="utf-8")

        result = reg.filter_new([old, new])
        assert result == [new]

    def test_unregister_allows_reprocessing(self, tmp_path: Path) -> None:
        """After unregister(), is_processed() returns False."""
        reg = HashRegistry(tmp_path / "reg.json")
        f = tmp_path / "file.txt"
        f.write_text("data", encoding="utf-8")
        reg.register(f)

        assert reg.unregister(f) is True
        assert reg.is_processed(f) is False

    def test_unregister_returns_false_for_unknown(self, tmp_path: Path) -> None:
        """Unregistering an unknown file returns False."""
        reg = HashRegistry(tmp_path / "reg.json")
        assert reg.unregister(tmp_path / "nope.txt") is False

    def test_clear_resets_all(self, tmp_path: Path) -> None:
        """clear() wipes the registry; all files become unprocessed."""
        reg = HashRegistry(tmp_path / "reg.json")
        f = tmp_path / "file.txt"
        f.write_text("data", encoding="utf-8")
        reg.register(f)

        reg.clear()
        assert reg.count() == 0
        assert reg.is_processed(f) is False

    def test_register_batch_handles_multiple(self, tmp_path: Path) -> None:
        """register_batch() marks every listed file as processed."""
        reg = HashRegistry(tmp_path / "reg.json")
        files = []
        for i in range(3):
            f = tmp_path / f"f{i}.txt"
            f.write_text(f"content-{i}", encoding="utf-8")
            files.append(f)

        reg.register_batch(files, batch_id="BATCH-042")
        for f in files:
            assert reg.is_processed(f) is True

    def test_count_returns_correct_value(self, tmp_path: Path) -> None:
        """count() reflects the number of registered files."""
        reg = HashRegistry(tmp_path / "reg.json")
        assert reg.count() == 0

        f = tmp_path / "a.txt"
        f.write_text("a", encoding="utf-8")
        reg.register(f)
        assert reg.count() == 1

    def test_stats_returns_expected_keys(self, tmp_path: Path) -> None:
        """stats() dict has the documented keys."""
        reg = HashRegistry(tmp_path / "reg.json")
        s = reg.stats()
        assert "total_files" in s
        assert "registry_path" in s
        assert "registry_exists" in s

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        """A new HashRegistry instance picks up entries saved by a prior one."""
        reg_file = tmp_path / "reg.json"
        f = tmp_path / "persist.txt"
        f.write_text("persist", encoding="utf-8")

        reg1 = HashRegistry(reg_file)
        reg1.register(f, batch_id="B-99")

        reg2 = HashRegistry(reg_file)
        assert reg2.is_processed(f) is True
        assert reg2.count() == 1

    def test_corrupted_registry_falls_back_to_empty(self, tmp_path: Path) -> None:
        """If the registry file is corrupted JSON, start fresh instead of crashing."""
        reg_file = tmp_path / "reg.json"
        reg_file.write_text("{bad json", encoding="utf-8")

        reg = HashRegistry(reg_file)
        assert reg.count() == 0

    def test_register_stores_batch_id(self, tmp_path: Path) -> None:
        """The batch_id is persisted alongside the hash."""
        reg_file = tmp_path / "reg.json"
        f = tmp_path / "tagged.txt"
        f.write_text("tagged", encoding="utf-8")

        reg = HashRegistry(reg_file)
        reg.register(f, batch_id="BATCH-007")

        raw = json.loads(reg_file.read_text(encoding="utf-8"))
        entry = raw[str(f)]
        assert entry["batch_id"] == "BATCH-007"
        assert "processed_at" in entry
        assert "hash" in entry

    def test_filter_new_with_all_processed(self, tmp_path: Path) -> None:
        """filter_new() returns empty list when all files are already processed."""
        reg = HashRegistry(tmp_path / "reg.json")
        files = []
        for i in range(3):
            f = tmp_path / f"done{i}.txt"
            f.write_text(f"done-{i}", encoding="utf-8")
            files.append(f)
        reg.register_batch(files)

        assert reg.filter_new(files) == []
