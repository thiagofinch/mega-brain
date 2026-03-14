"""
Tests for core.intelligence.pipeline.batch_auto_creator
=======================================================
Covers: derive_source_code, collect_batchable_files, load_or_init_registry,
        save_registry, _is_file_batched, register_files, write_batch_json,
        write_batch_md, scan_and_create, BatchResult, ScanResult.

All tests are OFFLINE.  All filesystem operations use tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------

MODULE = "core.intelligence.pipeline.batch_auto_creator"


@pytest.fixture(autouse=True)
def _patch_batch_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all module-level paths to tmp_path and mock downstream triggers."""
    import core.intelligence.pipeline.batch_auto_creator as ba

    external_inbox = tmp_path / "knowledge" / "external" / "inbox"
    external_inbox.mkdir(parents=True)

    logs = tmp_path / "logs" / "batches"
    logs.mkdir(parents=True)

    mission_control = tmp_path / ".claude" / "mission-control"
    mission_control.mkdir(parents=True)

    batch_json_dir = mission_control / "batch-logs"
    batch_json_dir.mkdir(parents=True)

    registry_path = mission_control / "BATCH-REGISTRY.json"

    auto_log = tmp_path / "logs" / "batch-auto-creator.jsonl"

    routing = {
        "external_inbox": external_inbox,
        "business_inbox": tmp_path / "knowledge" / "business" / "inbox",
        "personal_inbox": tmp_path / "knowledge" / "personal" / "inbox",
        "batch_log": logs,
        "batch_registry": registry_path,
        "batch_auto_creator_log": auto_log,
    }

    monkeypatch.setattr(ba, "ROUTING", routing)
    monkeypatch.setattr(ba, "BATCH_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(ba, "BATCH_JSON_DIR", batch_json_dir)
    monkeypatch.setattr(ba, "BATCH_MD_DIR", logs)
    monkeypatch.setattr(ba, "AUTO_CREATOR_LOG", auto_log)
    monkeypatch.setattr(ba, "SCAN_BUCKETS", ["external"])
    monkeypatch.setattr(ba, "MIN_FILES", 3)

    # Mock all downstream triggers (cascading, enrichment, workspace sync)
    monkeypatch.setattr(ba, "trigger_cascading", lambda md_path: True)
    monkeypatch.setattr(ba, "trigger_memory_enrichment", lambda bid, slug, files: True)
    monkeypatch.setattr(ba, "trigger_workspace_sync", lambda: True)

    return {
        "external_inbox": external_inbox,
        "logs": logs,
        "mission_control": mission_control,
        "batch_json_dir": batch_json_dir,
        "registry_path": registry_path,
        "auto_log": auto_log,
    }


from core.intelligence.pipeline.batch_auto_creator import (
    BatchResult,
    ScanResult,
    _extract_batch_number,
    _is_file_batched,
    collect_batchable_files,
    derive_source_code,
    load_or_init_registry,
    register_files,
    save_registry,
    scan_and_create,
    write_batch_json,
    write_batch_md,
)


# ===========================================================================
# 1. TestDeriveSourceCode
# ===========================================================================
class TestDeriveSourceCode:
    """derive_source_code maps entity slugs to 2-3 char codes."""

    def test_known_mapping_hormozi(self):
        assert derive_source_code("alex-hormozi") == "AH"

    def test_known_mapping_cole(self):
        assert derive_source_code("cole-gordon") == "CG"

    def test_known_mapping_jeremy_haynes(self):
        assert derive_source_code("jeremy-haynes") == "JH"

    def test_unknown_generates_initials(self):
        assert derive_source_code("new-person") == "NP"

    def test_three_word_name(self):
        assert derive_source_code("the-scalable-company") == "TSC"

    def test_single_word_slug(self):
        code = derive_source_code("mononym")
        assert code == "M"

    def test_empty_slug_returns_unk(self):
        assert derive_source_code("") == "UNK"


# ===========================================================================
# 2. TestExtractBatchNumber
# ===========================================================================
class TestExtractBatchNumber:
    """_extract_batch_number parses numeric portion of batch IDs."""

    def test_standard_format(self):
        assert _extract_batch_number("BATCH-128-JH") == 128

    def test_simple_format(self):
        assert _extract_batch_number("BATCH-001") == 1

    def test_no_match_returns_zero(self):
        assert _extract_batch_number("INVALID") == 0


# ===========================================================================
# 3. TestCollectBatchableFiles
# ===========================================================================
class TestCollectBatchableFiles:
    """collect_batchable_files finds eligible files under a person dir."""

    def test_finds_txt_files(self, _patch_batch_paths):
        paths = _patch_batch_paths
        person_dir = paths["external_inbox"] / "alex-hormozi" / "courses"
        person_dir.mkdir(parents=True)
        (person_dir / "lesson1.txt").write_text("content")
        (person_dir / "lesson2.txt").write_text("content")

        files = collect_batchable_files(paths["external_inbox"] / "alex-hormozi")

        assert len(files) == 2

    def test_skips_ref_yaml(self, _patch_batch_paths):
        paths = _patch_batch_paths
        person_dir = paths["external_inbox"] / "test-person"
        person_dir.mkdir(parents=True)
        (person_dir / "file.ref.yaml").write_text("ref: true")
        (person_dir / "actual.txt").write_text("content")

        files = collect_batchable_files(person_dir)

        assert len(files) == 1
        assert files[0].name == "actual.txt"

    def test_skips_dotfiles(self, _patch_batch_paths):
        paths = _patch_batch_paths
        person_dir = paths["external_inbox"] / "test-person"
        person_dir.mkdir(parents=True)
        (person_dir / ".DS_Store").write_text("x")
        (person_dir / ".hidden").write_text("x")
        (person_dir / "visible.txt").write_text("content")

        files = collect_batchable_files(person_dir)

        assert len(files) == 1

    def test_skips_unsupported_extensions(self, _patch_batch_paths):
        paths = _patch_batch_paths
        person_dir = paths["external_inbox"] / "test-person"
        person_dir.mkdir(parents=True)
        (person_dir / "image.jpg").write_text("x")
        (person_dir / "data.csv").write_text("x")
        (person_dir / "valid.md").write_text("content")

        files = collect_batchable_files(person_dir)

        assert len(files) == 1
        assert files[0].name == "valid.md"

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        files = collect_batchable_files(tmp_path / "nonexistent")
        assert files == []

    def test_nested_files_found(self, _patch_batch_paths):
        paths = _patch_batch_paths
        person_dir = paths["external_inbox"] / "test-person"
        deep = person_dir / "courses" / "module1"
        deep.mkdir(parents=True)
        (deep / "lesson.txt").write_text("content")

        files = collect_batchable_files(person_dir)

        assert len(files) == 1


# ===========================================================================
# 4. TestRegistry
# ===========================================================================
class TestRegistry:
    """Registry load, save, and file tracking."""

    def test_load_creates_fresh_registry(self, _patch_batch_paths):
        registry = load_or_init_registry()
        assert registry["version"] == 1
        assert registry["next_batch_number"] >= 1
        assert isinstance(registry["files"], dict)

    def test_save_and_reload(self, _patch_batch_paths):
        registry = load_or_init_registry()
        registry["next_batch_number"] = 42
        save_registry(registry)

        reloaded = load_or_init_registry()
        assert reloaded["next_batch_number"] == 42

    def test_is_file_batched_false_for_new(self, _patch_batch_paths):
        registry = load_or_init_registry()
        fp = Path("/some/new/file.txt")
        assert _is_file_batched(registry, fp) is False

    def test_is_file_batched_true_after_register(self, _patch_batch_paths):
        registry = load_or_init_registry()
        fp = Path("/some/file.txt")
        register_files(registry, "BATCH-001-AH", "alex-hormozi", "AH", [str(fp)])
        assert _is_file_batched(registry, fp) is True

    def test_register_files_updates_batches(self, _patch_batch_paths):
        registry = load_or_init_registry()
        register_files(
            registry,
            "BATCH-001-CG",
            "cole-gordon",
            "CG",
            ["/path/a.txt", "/path/b.txt"],
        )
        assert "BATCH-001-CG" in registry["batches"]
        assert registry["batches"]["BATCH-001-CG"]["file_count"] == 2

    def test_legacy_file_detection(self, _patch_batch_paths):
        registry = load_or_init_registry()
        registry["files"]["legacy:old-file"] = {
            "batch_id": "BATCH-099-JH",
            "batched_at": "2026-01-01",
            "legacy": True,
        }
        fp = Path("/any/path/old-file.txt")
        assert _is_file_batched(registry, fp) is True


# ===========================================================================
# 5. TestWriteBatchJson
# ===========================================================================
class TestWriteBatchJson:
    """write_batch_json creates properly formatted JSON files."""

    def test_json_file_created(self, _patch_batch_paths):
        paths = _patch_batch_paths
        json_path = write_batch_json(
            "BATCH-001-AH",
            "AH",
            "alex-hormozi",
            ["/path/file1.txt", "/path/file2.txt"],
            total_size=5000,
        )
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert data["batch_id"] == "BATCH-001-AH"
        assert data["files_count"] == 2
        assert data["auto_created"] is True

    def test_json_contains_source_info(self, _patch_batch_paths):
        json_path = write_batch_json(
            "BATCH-010-CG",
            "CG",
            "cole-gordon",
            ["/path/file.txt"],
            total_size=1000,
        )
        data = json.loads(json_path.read_text())
        assert data["source"] == "CG"
        assert data["source_name"] == "Cole Gordon"


# ===========================================================================
# 6. TestWriteBatchMd
# ===========================================================================
class TestWriteBatchMd:
    """write_batch_md creates properly formatted Markdown files."""

    def test_md_file_created(self, _patch_batch_paths):
        md_path = write_batch_md(
            "BATCH-001-AH",
            "AH",
            "alex-hormozi",
            ["/path/file1.txt", "/path/file2.txt"],
            total_size=5000,
        )
        assert md_path.exists()
        content = md_path.read_text()
        assert "BATCH-001-AH" in content
        assert "alex-hormozi" in content

    def test_md_contains_file_table(self, _patch_batch_paths):
        md_path = write_batch_md(
            "BATCH-005-JH",
            "JH",
            "jeremy-haynes",
            ["/path/a.txt", "/path/b.txt", "/path/c.txt"],
            total_size=9000,
        )
        content = md_path.read_text()
        assert "a.txt" in content
        assert "b.txt" in content
        assert "c.txt" in content


# ===========================================================================
# 7. TestScanAndCreate
# ===========================================================================
class TestScanAndCreate:
    """Integration tests for scan_and_create."""

    def _populate_person(self, inbox: Path, entity: str, count: int):
        """Helper to create N batchable files under person/courses/."""
        person_dir = inbox / entity / "courses"
        person_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            (person_dir / f"lesson-{i + 1}.txt").write_text(f"lesson {i + 1} content")

    def test_creates_batch_when_above_threshold(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 5)

        result = scan_and_create()

        assert len(result.batches_created) >= 1
        assert result.files_scanned == 5

    def test_no_batch_when_below_threshold(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 2)

        result = scan_and_create()

        assert len(result.batches_created) == 0
        assert "alex-hormozi" in result.files_below_threshold

    def test_force_batches_below_threshold(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 1)

        result = scan_and_create(force=True)

        assert len(result.batches_created) >= 1

    def test_dry_run_writes_nothing(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 5)

        result = scan_and_create(dry_run=True)

        assert len(result.batches_created) >= 1
        batch = result.batches_created[0]
        assert batch.json_path == "(dry-run)"
        # Registry should NOT be saved
        assert not paths["registry_path"].exists()

    def test_already_batched_files_skipped(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 5)

        # First run creates batches
        scan_and_create()

        # Second run should skip all files
        result2 = scan_and_create()
        assert len(result2.batches_created) == 0
        assert result2.files_already_batched == 5

    def test_multiple_persons(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 4)
        self._populate_person(paths["external_inbox"], "cole-gordon", 3)

        result = scan_and_create()

        assert result.persons_scanned == 2
        assert len(result.batches_created) >= 2
        batch_names = [b.source_name for b in result.batches_created]
        assert "alex-hormozi" in batch_names
        assert "cole-gordon" in batch_names

    def test_scan_result_has_duration(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 3)

        result = scan_and_create()

        assert result.duration_ms >= 0

    def test_underscore_dirs_skipped(self, _patch_batch_paths):
        paths = _patch_batch_paths
        hidden = paths["external_inbox"] / "_templates"
        hidden.mkdir()
        (hidden / "template.txt").write_text("template")

        result = scan_and_create()

        assert result.persons_scanned == 0
        assert result.files_scanned == 0


# ===========================================================================
# 8. TestBatchResultDefaults
# ===========================================================================
class TestBatchResultDefaults:
    """BatchResult and ScanResult dataclass defaults."""

    def test_batch_result_defaults(self):
        b = BatchResult()
        assert b.batch_id == ""
        assert b.files == []
        assert b.cascading_triggered is False

    def test_scan_result_defaults(self):
        s = ScanResult()
        assert s.batches_created == []
        assert s.files_scanned == 0
        assert s.duration_ms == 0


# ===========================================================================
# 9. TestRegistryBootstrap
# ===========================================================================
class TestRegistryBootstrap:
    """Registry bootstrapping from existing batch-log JSON files."""

    def test_bootstrap_from_existing_json(self, _patch_batch_paths):
        paths = _patch_batch_paths
        existing = paths["batch_json_dir"] / "BATCH-050-JH.json"
        existing.write_text(
            json.dumps(
                {
                    "batch_id": "BATCH-050-JH",
                    "source": "JH",
                    "source_name": "Jeremy Haynes",
                    "files_processed": ["file1.txt", "file2.txt"],
                    "files_count": 2,
                    "generated_at": "2026-01-15T00:00:00Z",
                    "status": "COMPLETE",
                }
            )
        )

        registry = load_or_init_registry()

        assert "BATCH-050-JH" in registry["batches"]
        assert registry["next_batch_number"] == 51

    def test_bootstrap_handles_corrupt_json(self, _patch_batch_paths):
        paths = _patch_batch_paths
        corrupt = paths["batch_json_dir"] / "BATCH-001-XX.json"
        corrupt.write_text("not valid json{{{")

        registry = load_or_init_registry()

        assert registry["version"] == 1
        assert "BATCH-001-XX" not in registry.get("batches", {})


# ===========================================================================
# 10. TestDualLocationLogs
# ===========================================================================
class TestDualLocationLogs:
    """Verify dual-location logging (JSON + MD per REGRA #8)."""

    def test_both_json_and_md_created(self, _patch_batch_paths):
        paths = _patch_batch_paths
        self._populate_person(paths["external_inbox"], "alex-hormozi", 3)

        result = scan_and_create()

        assert len(result.batches_created) >= 1
        batch = result.batches_created[0]
        assert Path(batch.json_path).exists()
        assert Path(batch.md_path).exists()

    def _populate_person(self, inbox: Path, entity: str, count: int):
        person_dir = inbox / entity / "courses"
        person_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            (person_dir / f"lesson-{i + 1}.txt").write_text(f"lesson {i + 1}")
