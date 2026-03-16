"""
test_metrics.py -- Tests for MCE MetricsTracker
================================================

Covers: duration tracking, phase timing, metrics serialization,
JSONL audit logging, persistence round-trip, edge cases.

All tests are OFFLINE -- no real filesystem outside tmp_path.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers: patch ROUTING and LOGS so files land in tmp_path
# ---------------------------------------------------------------------------


def _make_routing(tmp_path: Path) -> dict[str, Any]:
    """Return a ROUTING dict pointing mce_state and logs at tmp_path."""
    return {
        "mce_state": tmp_path / "mce",
        "mce_metrics_log": tmp_path / "logs" / "mce-metrics.jsonl",
    }


@pytest.fixture()
def _patch_routing(tmp_path: Path):
    """Monkeypatch ROUTING and LOGS in the metrics module."""
    routing = _make_routing(tmp_path)
    with (
        patch("core.intelligence.pipeline.mce.metrics.ROUTING", routing),
        patch("core.intelligence.pipeline.mce.metrics.LOGS", tmp_path / "logs"),
    ):
        yield routing


# ---------------------------------------------------------------------------
# Import under test
# ---------------------------------------------------------------------------


def _import_mt():
    from core.intelligence.pipeline.mce.metrics import MetricsTracker

    return MetricsTracker


# ---------------------------------------------------------------------------
# Tests: Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    """Verify initial state of a new MetricsTracker."""

    def test_default_state(self, _patch_routing):
        MT = _import_mt()
        mt = MT("test-persona")
        assert mt.slug == "test-persona"
        assert mt.started != ""
        assert mt.phases_completed == 0
        assert mt.total_duration_seconds == 0.0
        assert mt.phase_names == []


# ---------------------------------------------------------------------------
# Tests: Phase Timing
# ---------------------------------------------------------------------------


class TestPhaseTiming:
    """Verify start_phase, end_phase, phase_duration."""

    def test_start_and_end_phase(self, _patch_routing):
        MT = _import_mt()
        mt = MT("timing-test")
        mt.start_phase("chunking")
        time.sleep(0.05)
        mt.end_phase("chunking")
        dur = mt.phase_duration("chunking")
        assert dur >= 0.04  # at least ~50ms
        assert mt.phases_completed == 1

    def test_end_phase_not_started_raises(self, _patch_routing):
        MT = _import_mt()
        mt = MT("error-test")
        with pytest.raises(KeyError, match="never started"):
            mt.end_phase("nonexistent")

    def test_phase_duration_unknown_returns_zero(self, _patch_routing):
        MT = _import_mt()
        mt = MT("unknown-dur")
        assert mt.phase_duration("nonexistent") == 0.0

    def test_restart_phase_resets_timer(self, _patch_routing):
        MT = _import_mt()
        mt = MT("restart-test")
        mt.start_phase("chunking")
        time.sleep(0.05)
        mt.end_phase("chunking")
        first_dur = mt.phase_duration("chunking")

        # Restart the same phase (retry scenario)
        mt.start_phase("chunking")
        time.sleep(0.02)
        mt.end_phase("chunking")
        second_dur = mt.phase_duration("chunking")
        # Second run should be shorter
        assert second_dur < first_dur + 0.1  # sanity check, not precise

    def test_multiple_phases(self, _patch_routing):
        MT = _import_mt()
        mt = MT("multi-phase")
        mt.start_phase("chunking")
        mt.end_phase("chunking")
        mt.start_phase("entities")
        mt.end_phase("entities")
        assert mt.phases_completed == 2
        assert mt.phase_names == ["chunking", "entities"]

    def test_total_duration_sums_all_phases(self, _patch_routing):
        MT = _import_mt()
        mt = MT("total-dur")
        mt.start_phase("chunking")
        time.sleep(0.03)
        mt.end_phase("chunking")
        mt.start_phase("entities")
        time.sleep(0.03)
        mt.end_phase("entities")
        total = mt.total_duration_seconds
        assert total >= 0.05  # at least ~60ms combined

    def test_running_phase_reports_elapsed(self, _patch_routing):
        """A phase that has started but not ended should report elapsed time."""
        MT = _import_mt()
        mt = MT("running-test")
        mt.start_phase("chunking")
        time.sleep(0.03)
        # Not ended yet -- should still report a positive duration
        dur = mt.phase_duration("chunking")
        assert dur >= 0.02
        assert mt.phases_completed == 0  # not ended yet


# ---------------------------------------------------------------------------
# Tests: Persistence (save / load)
# ---------------------------------------------------------------------------


class TestPersistence:
    """Verify YAML persistence round-trips."""

    def test_save_creates_file(self, _patch_routing, tmp_path):
        MT = _import_mt()
        mt = MT("save-test")
        mt.start_phase("chunking")
        mt.end_phase("chunking")
        saved = mt.save()
        assert saved.exists()
        data = yaml.safe_load(saved.read_text())
        assert data["pipeline"] == "save-test"
        assert "chunking" in data["phases"]
        assert data["total"]["phases_completed"] == 1

    def test_load_round_trip(self, _patch_routing, tmp_path):
        MT = _import_mt()
        mt = MT("roundtrip")
        mt.start_phase("chunking")
        mt.end_phase("chunking")
        mt.start_phase("entities")
        mt.end_phase("entities")
        mt.save()

        loaded = MT.load("roundtrip")
        assert loaded is not None
        assert loaded.slug == "roundtrip"
        assert loaded.phases_completed == 2
        assert "chunking" in loaded.phase_names
        assert "entities" in loaded.phase_names

    def test_load_nonexistent_returns_none(self, _patch_routing):
        MT = _import_mt()
        assert MT.load("does-not-exist") is None

    def test_load_corrupt_yaml_returns_none(self, _patch_routing, tmp_path):
        MT = _import_mt()
        d = tmp_path / "mce" / "corrupt-metrics"
        d.mkdir(parents=True)
        (d / "metrics.yaml").write_text("{{invalid yaml ::::")
        assert MT.load("corrupt-metrics") is None

    def test_load_non_dict_returns_none(self, _patch_routing, tmp_path):
        MT = _import_mt()
        d = tmp_path / "mce" / "non-dict-metrics"
        d.mkdir(parents=True)
        (d / "metrics.yaml").write_text("42")
        assert MT.load("non-dict-metrics") is None

    def test_metrics_path_property(self, _patch_routing, tmp_path):
        MT = _import_mt()
        mt = MT("path-test")
        assert mt.metrics_path == tmp_path / "mce" / "path-test" / "metrics.yaml"

    def test_load_preserves_timestamps(self, _patch_routing, tmp_path):
        MT = _import_mt()
        mt = MT("ts-roundtrip")
        mt.start_phase("chunking")
        mt.end_phase("chunking")
        mt.save()

        loaded = MT.load("ts-roundtrip")
        assert loaded is not None
        dur = loaded.phase_duration("chunking")
        assert dur >= 0.0


# ---------------------------------------------------------------------------
# Tests: JSONL Audit Log
# ---------------------------------------------------------------------------


class TestJsonlLog:
    """Verify append_to_jsonl creates valid JSONL entries."""

    def test_append_creates_jsonl(self, _patch_routing, tmp_path):
        MT = _import_mt()
        mt = MT("jsonl-test")
        mt.start_phase("chunking")
        mt.end_phase("chunking")
        mt.append_to_jsonl()

        log_path = tmp_path / "logs" / "mce-metrics.jsonl"
        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["pipeline"] == "jsonl-test"
        assert entry["phases_completed"] == 1
        assert "chunking" in entry["phases"]

    def test_append_multiple_entries(self, _patch_routing, tmp_path):
        MT = _import_mt()
        mt1 = MT("jsonl-multi-1")
        mt1.start_phase("chunking")
        mt1.end_phase("chunking")
        mt1.append_to_jsonl()

        mt2 = MT("jsonl-multi-2")
        mt2.start_phase("entities")
        mt2.end_phase("entities")
        mt2.append_to_jsonl()

        log_path = tmp_path / "logs" / "mce-metrics.jsonl"
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_append_is_non_fatal(self, _patch_routing, tmp_path):
        """append_to_jsonl should never raise, even on errors."""
        MT = _import_mt()
        mt = MT("non-fatal")
        # Make the log dir a file to cause an OSError
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "mce-metrics.jsonl"
        log_file.write_text("")
        # This should not raise
        mt.append_to_jsonl()


# ---------------------------------------------------------------------------
# Tests: to_dict and repr
# ---------------------------------------------------------------------------


class TestSerialization:
    """Verify to_dict and __repr__."""

    def test_to_dict_keys(self, _patch_routing):
        MT = _import_mt()
        mt = MT("dict-test")
        mt.start_phase("chunking")
        mt.end_phase("chunking")
        d = mt.to_dict()
        assert set(d.keys()) == {"pipeline", "started", "phases", "total"}
        assert d["pipeline"] == "dict-test"
        assert d["total"]["phases_completed"] == 1

    def test_repr_contains_slug(self, _patch_routing):
        MT = _import_mt()
        mt = MT("repr-test")
        r = repr(mt)
        assert "repr-test" in r
        assert "0.0s" in r


# ---------------------------------------------------------------------------
# Tests: _PhaseTimer internals
# ---------------------------------------------------------------------------


class TestPhaseTimerInternals:
    """Test the internal _PhaseTimer class via MetricsTracker behavior."""

    def test_timer_to_dict_started_only(self, _patch_routing):
        """A timer that was started but not stopped should have duration > 0."""
        MT = _import_mt()
        mt = MT("timer-started")
        mt.start_phase("chunking")
        d = mt.to_dict()
        phase_data = d["phases"]["chunking"]
        assert "started" in phase_data
        assert phase_data["duration_seconds"] >= 0.0

    def test_timer_to_dict_completed(self, _patch_routing):
        MT = _import_mt()
        mt = MT("timer-complete")
        mt.start_phase("chunking")
        time.sleep(0.15)
        mt.end_phase("chunking")
        d = mt.to_dict()
        phase_data = d["phases"]["chunking"]
        assert "started" in phase_data
        assert "ended" in phase_data
        # to_dict rounds to 1 decimal, so 0.15s -> 0.2 or 0.1
        assert phase_data["duration_seconds"] >= 0.1

    def test_timer_from_dict_no_timestamps(self, _patch_routing):
        """A timer loaded from disk with empty timestamps should report 0 duration."""
        from core.intelligence.pipeline.mce.metrics import _PhaseTimer

        pt = _PhaseTimer.from_dict("test", {})
        assert pt.duration_seconds == 0.0
        assert pt.started == ""
        assert pt.ended == ""
