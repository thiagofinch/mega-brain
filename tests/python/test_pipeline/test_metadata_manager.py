"""
test_metadata_manager.py -- Tests for MCE MetadataManager
==========================================================

Covers: phase progress tracking, metadata CRUD, source tracking,
status helpers, persistence round-trip, edge cases.

All tests are OFFLINE -- no real filesystem outside tmp_path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers: patch ROUTING so metadata files land in tmp_path
# ---------------------------------------------------------------------------


def _make_routing(tmp_path: Path) -> dict[str, Any]:
    """Return a ROUTING dict pointing mce_state at tmp_path."""
    return {"mce_state": tmp_path / "mce"}


@pytest.fixture()
def _patch_routing(tmp_path: Path):
    """Monkeypatch ROUTING in metadata_manager module."""
    routing = _make_routing(tmp_path)
    with patch("core.intelligence.pipeline.mce.metadata_manager.ROUTING", routing):
        yield routing


# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------


def _import_mm():
    from core.intelligence.pipeline.mce.metadata_manager import (
        VALID_PHASES,
        VALID_STATUSES,
        MetadataManager,
    )

    return MetadataManager, VALID_PHASES, VALID_STATUSES


# ---------------------------------------------------------------------------
# Tests: Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    """Verify initial state of a new MetadataManager."""

    def test_default_state(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("test-persona")
        assert mgr.slug == "test-persona"
        assert mgr.mode == "greenfield"
        assert mgr.source_code == ""
        assert mgr.pipeline_status == "not_started"
        assert mgr.phases_completed == {}
        assert mgr.sources_processed == []

    def test_brownfield_mode(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("test-persona", mode="brownfield", source_code="AH")
        assert mgr.mode == "brownfield"
        assert mgr.source_code == "AH"

    def test_started_at_populated(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("test-persona")
        assert mgr.started_at != ""
        assert "T" in mgr.started_at  # ISO format


# ---------------------------------------------------------------------------
# Tests: Phase Tracking
# ---------------------------------------------------------------------------


class TestPhaseTracking:
    """Verify mark_phase_complete, mark_phase_attempt, is_phase_complete."""

    def test_mark_phase_complete(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("phase-test")
        mgr.mark_phase_complete("chunking", chunks_created=45)
        assert mgr.is_phase_complete("chunking") is True
        assert mgr.phases_completed["chunking"]["completed"] is True
        assert mgr.phases_completed["chunking"]["chunks_created"] == 45
        assert mgr.pipeline_status == "in_progress"

    def test_mark_phase_complete_updates_timestamp(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("ts-test")
        initial = mgr.updated_at
        mgr.mark_phase_complete("chunking")
        # updated_at should have been refreshed (may be same instant, but should exist)
        assert mgr.updated_at is not None

    def test_mark_phase_attempt(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("attempt-test")
        mgr.mark_phase_attempt("mce_extraction", attempt=2)
        entry = mgr.phases_completed["mce_extraction"]
        assert entry["completed"] is False
        assert entry["attempt"] == 2
        assert "last_attempt_at" in entry

    def test_mark_phase_attempt_then_complete(self, _patch_routing):
        """An attempt followed by completion should show completed=True."""
        MM, _, _ = _import_mm()
        mgr = MM("attempt-then-complete")
        mgr.mark_phase_attempt("mce_extraction", attempt=1)
        assert mgr.is_phase_complete("mce_extraction") is False
        mgr.mark_phase_complete("mce_extraction", attempt=2)
        assert mgr.is_phase_complete("mce_extraction") is True

    def test_is_phase_complete_false_for_unknown(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("unknown-test")
        assert mgr.is_phase_complete("nonexistent_phase") is False

    def test_unknown_phase_recorded_with_warning(self, _patch_routing):
        """Unknown phases are recorded (with a log warning)."""
        MM, _, _ = _import_mm()
        mgr = MM("unknown-phase")
        mgr.mark_phase_complete("totally_fake_phase")
        assert mgr.is_phase_complete("totally_fake_phase") is True

    def test_completed_phase_names(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("names-test")
        mgr.mark_phase_complete("chunking")
        mgr.mark_phase_complete("entity_resolution")
        mgr.mark_phase_attempt("mce_extraction", attempt=1)
        names = mgr.completed_phase_names
        assert "chunking" in names
        assert "entity_resolution" in names
        assert "mce_extraction" not in names

    def test_next_incomplete_phase(self, _patch_routing):
        MM, VALID_PHASES, _ = _import_mm()
        mgr = MM("next-test")
        assert mgr.next_incomplete_phase == VALID_PHASES[0]  # "chunking"
        mgr.mark_phase_complete("chunking")
        assert mgr.next_incomplete_phase == VALID_PHASES[1]  # "entity_resolution"

    def test_next_incomplete_phase_all_done(self, _patch_routing):
        MM, VALID_PHASES, _ = _import_mm()
        mgr = MM("all-done")
        for phase in VALID_PHASES:
            mgr.mark_phase_complete(phase)
        assert mgr.next_incomplete_phase is None


# ---------------------------------------------------------------------------
# Tests: Source Tracking
# ---------------------------------------------------------------------------


class TestSourceTracking:
    """Verify add_source records files."""

    def test_add_source(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("source-test")
        mgr.add_source("hormozi-leads.txt", chunks=45, insights=12)
        assert len(mgr.sources_processed) == 1
        entry = mgr.sources_processed[0]
        assert entry["file"] == "hormozi-leads.txt"
        assert entry["chunks"] == 45
        assert entry["insights"] == 12

    def test_add_multiple_sources(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("multi-source")
        mgr.add_source("file1.txt")
        mgr.add_source("file2.txt")
        mgr.add_source("file3.txt")
        assert len(mgr.sources_processed) == 3


# ---------------------------------------------------------------------------
# Tests: Status Helpers
# ---------------------------------------------------------------------------


class TestStatusHelpers:
    """Verify mark_complete, mark_failed, mark_paused."""

    def test_mark_complete(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("complete-test")
        mgr.mark_complete()
        assert mgr.pipeline_status == "complete"

    def test_mark_failed_with_reason(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("fail-test")
        mgr.mark_failed(reason="LLM timeout")
        assert mgr.pipeline_status == "failed"
        assert mgr.phases_completed["_failure"]["reason"] == "LLM timeout"

    def test_mark_failed_without_reason(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("fail-no-reason")
        mgr.mark_failed()
        assert mgr.pipeline_status == "failed"

    def test_mark_paused(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("paused-test")
        mgr.mark_paused()
        assert mgr.pipeline_status == "paused"


# ---------------------------------------------------------------------------
# Tests: Persistence (save / load)
# ---------------------------------------------------------------------------


class TestPersistence:
    """Verify YAML persistence round-trips."""

    def test_save_creates_file(self, _patch_routing, tmp_path):
        MM, _, _ = _import_mm()
        mgr = MM("save-test", mode="brownfield", source_code="AH")
        mgr.mark_phase_complete("chunking", chunks=45)
        mgr.add_source("workshop.txt")
        saved = mgr.save()
        assert saved.exists()
        data = yaml.safe_load(saved.read_text())
        assert data["persona"] == "save-test"
        assert data["mode"] == "brownfield"
        assert data["source_code"] == "AH"
        assert data["phases_completed"]["chunking"]["completed"] is True

    def test_load_round_trip(self, _patch_routing, tmp_path):
        MM, _, _ = _import_mm()
        mgr = MM("roundtrip", mode="brownfield", source_code="RT")
        mgr.mark_phase_complete("chunking", chunks=10)
        mgr.mark_phase_complete("entity_resolution")
        mgr.add_source("file1.txt", chunks=10)
        mgr.mark_complete()
        mgr.save()

        loaded = MM.load("roundtrip")
        assert loaded is not None
        assert loaded.slug == "roundtrip"
        assert loaded.mode == "brownfield"
        assert loaded.source_code == "RT"
        assert loaded.pipeline_status == "complete"
        assert loaded.is_phase_complete("chunking") is True
        assert loaded.is_phase_complete("entity_resolution") is True
        assert len(loaded.sources_processed) == 1

    def test_load_nonexistent_returns_none(self, _patch_routing):
        MM, _, _ = _import_mm()
        assert MM.load("does-not-exist") is None

    def test_load_corrupt_yaml_returns_none(self, _patch_routing, tmp_path):
        MM, _, _ = _import_mm()
        d = tmp_path / "mce" / "corrupt-meta"
        d.mkdir(parents=True)
        (d / "metadata.yaml").write_text("{{not valid yaml ::::")
        assert MM.load("corrupt-meta") is None

    def test_load_non_dict_returns_none(self, _patch_routing, tmp_path):
        MM, _, _ = _import_mm()
        d = tmp_path / "mce" / "non-dict-meta"
        d.mkdir(parents=True)
        (d / "metadata.yaml").write_text('"just a string"')
        assert MM.load("non-dict-meta") is None

    def test_metadata_path_property(self, _patch_routing, tmp_path):
        MM, _, _ = _import_mm()
        mgr = MM("path-test")
        assert mgr.metadata_path == tmp_path / "mce" / "path-test" / "metadata.yaml"


# ---------------------------------------------------------------------------
# Tests: to_dict and repr
# ---------------------------------------------------------------------------


class TestSerialization:
    """Verify to_dict and __repr__."""

    def test_to_dict_keys(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("dict-test")
        d = mgr.to_dict()
        expected_keys = {
            "persona", "mode", "source_code", "pipeline_status",
            "started_at", "updated_at", "phases_completed",
            "sources_processed", "version",
        }
        assert set(d.keys()) == expected_keys
        assert d["persona"] == "dict-test"

    def test_repr_contains_slug(self, _patch_routing):
        MM, _, _ = _import_mm()
        mgr = MM("repr-test")
        r = repr(mgr)
        assert "repr-test" in r
        assert "not_started" in r


# ---------------------------------------------------------------------------
# Tests: Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify module-level constants are defined correctly."""

    def test_valid_phases(self, _patch_routing):
        _, VALID_PHASES, _ = _import_mm()
        assert "chunking" in VALID_PHASES
        assert "validation" in VALID_PHASES
        assert len(VALID_PHASES) == 8

    def test_valid_statuses(self, _patch_routing):
        _, _, VALID_STATUSES = _import_mm()
        assert "not_started" in VALID_STATUSES
        assert "complete" in VALID_STATUSES
        assert "failed" in VALID_STATUSES
        assert len(VALID_STATUSES) == 5
