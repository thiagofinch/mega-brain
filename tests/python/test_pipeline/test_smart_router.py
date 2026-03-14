"""
Tests for core.intelligence.pipeline.smart_router
==================================================
Covers: route(), detect_current_bucket, move_to_bucket, create_reference,
        handle_cascades, add_to_triage_queue, _resolve_collision, _is_ref_file,
        RouteResult, ACTION constants.

All tests are OFFLINE.  Filesystem operations use tmp_path.
Module-level path constants are monkeypatched to tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------

MODULE = "core.intelligence.pipeline.smart_router"


@pytest.fixture(autouse=True)
def _patch_router_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all module-level paths to tmp_path."""
    import core.intelligence.pipeline.smart_router as sr

    external = tmp_path / "knowledge" / "external" / "inbox"
    business = tmp_path / "knowledge" / "business" / "inbox"
    personal = tmp_path / "knowledge" / "personal" / "inbox"

    for d in [external, business, personal]:
        d.mkdir(parents=True)

    bucket_inboxes = {
        "external": external,
        "business": business,
        "personal": personal,
    }

    monkeypatch.setattr(sr, "BUCKET_INBOXES", bucket_inboxes)
    monkeypatch.setattr(sr, "SMART_ROUTER_LOG", tmp_path / "smart-router.jsonl")
    monkeypatch.setattr(sr, "TRIAGE_QUEUE", tmp_path / "TRIAGE-QUEUE.json")

    # Also monkeypatch inbox_organizer import inside trigger_organizer
    # to avoid real filesystem operations
    monkeypatch.setattr(
        sr, "trigger_organizer", lambda bucket, result: result.organized_buckets.append(bucket)
    )

    return bucket_inboxes


from core.intelligence.pipeline.smart_router import (  # noqa: E402
    ACTION_MOVE,
    ACTION_NOOP,
    ACTION_TRIAGE,
    AUTO_ROUTE_THRESHOLD,
    SKIP_THRESHOLD,
    RouteResult,
    _is_ref_file,
    _resolve_collision,
    add_to_triage_queue,
    create_reference,
    detect_current_bucket,
    handle_cascades,
    move_to_bucket,
    route,
)

from dataclasses import dataclass, field


@dataclass
class FakeScopeDecision:
    """Lightweight stand-in for ScopeDecision (duplicated from conftest for import safety)."""

    primary_bucket: str = "external"
    cascade_buckets: list[str] = field(default_factory=list)
    confidence: float = 0.90
    reasons: list[str] = field(default_factory=lambda: ["test-reason"])
    source_type: str = "course"
    detected_entities: list[str] = field(default_factory=list)
    signals: dict[str, object] = field(default_factory=dict)


# ===========================================================================
# 1. TestDetectCurrentBucket
# ===========================================================================
class TestDetectCurrentBucket:
    """detect_current_bucket maps file paths to bucket names."""

    def test_external_bucket(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "test.txt"
        fp.touch()
        assert detect_current_bucket(fp) == "external"

    def test_business_bucket(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["business"] / "test.txt"
        fp.touch()
        assert detect_current_bucket(fp) == "business"

    def test_personal_bucket(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["personal"] / "test.txt"
        fp.touch()
        assert detect_current_bucket(fp) == "personal"

    def test_unknown_path(self, tmp_path):
        fp = tmp_path / "somewhere" / "else.txt"
        fp.parent.mkdir(parents=True)
        fp.touch()
        assert detect_current_bucket(fp) == "unknown"


# ===========================================================================
# 2. TestMoveToucket
# ===========================================================================
class TestMoveToBucket:
    """move_to_bucket moves files between bucket inboxes."""

    def test_move_from_external_to_business(self, _patch_router_paths):
        inboxes = _patch_router_paths
        src = inboxes["external"] / "meeting.txt"
        src.write_text("meeting content")

        dest = move_to_bucket(src, "business")

        assert not src.exists()
        assert dest.exists()
        assert dest.read_text() == "meeting content"
        assert str(inboxes["business"]) in str(dest)

    def test_collision_appends_timestamp(self, _patch_router_paths):
        inboxes = _patch_router_paths
        existing = inboxes["business"] / "file.txt"
        existing.write_text("original")
        src = inboxes["external"] / "file.txt"
        src.write_text("new content")

        dest = move_to_bucket(src, "business")

        assert dest.exists()
        assert existing.exists()
        assert dest != existing

    def test_source_not_found_raises(self, _patch_router_paths):
        ghost = Path("/nonexistent/ghost.txt")
        with pytest.raises(FileNotFoundError):
            move_to_bucket(ghost, "business")

    def test_unknown_bucket_raises(self, _patch_router_paths):
        inboxes = _patch_router_paths
        src = inboxes["external"] / "test.txt"
        src.touch()
        with pytest.raises(ValueError, match="Unknown target bucket"):
            move_to_bucket(src, "galactic_federation")


# ===========================================================================
# 3. TestCreateReference
# ===========================================================================
class TestCreateReference:
    """create_reference writes .ref.yaml files."""

    def test_ref_yaml_created(self, _patch_router_paths):
        inboxes = _patch_router_paths
        original = inboxes["external"] / "course.txt"
        original.write_text("course content")
        decision = FakeScopeDecision(cascade_buckets=["business"])

        ref_path = create_reference(original, "business", decision)

        assert ref_path.exists()
        assert ref_path.name == "course.ref.yaml"
        assert str(inboxes["business"]) in str(ref_path)

    def test_ref_not_duplicated(self, _patch_router_paths):
        inboxes = _patch_router_paths
        original = inboxes["external"] / "course.txt"
        original.write_text("content")
        decision = FakeScopeDecision()

        ref1 = create_reference(original, "business", decision)
        ref2 = create_reference(original, "business", decision)

        assert ref1 == ref2

    def test_ref_content_has_original_path(self, _patch_router_paths):
        inboxes = _patch_router_paths
        original = inboxes["external"] / "course.txt"
        original.write_text("content")
        decision = FakeScopeDecision()

        ref_path = create_reference(original, "business", decision)
        content = ref_path.read_text()

        assert str(original) in content


# ===========================================================================
# 4. TestRoute
# ===========================================================================
class TestRoute:
    """Integration tests for route()."""

    def test_high_confidence_moves_file(self, _patch_router_paths, monkeypatch):
        import core.intelligence.pipeline.smart_router as sr

        # Restore real trigger_organizer behavior for this test
        monkeypatch.setattr(sr, "trigger_organizer", lambda b, r: r.organized_buckets.append(b))

        inboxes = _patch_router_paths
        fp = inboxes["external"] / "meeting.txt"
        fp.write_text("meeting")
        decision = FakeScopeDecision(primary_bucket="business", confidence=0.90)

        result = route(fp, decision)

        assert result.action == ACTION_MOVE
        assert result.destination_bucket == "business"
        assert result.moved_to != ""

    def test_already_in_correct_bucket(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "course.txt"
        fp.write_text("course")
        decision = FakeScopeDecision(primary_bucket="external", confidence=0.95)

        result = route(fp, decision)

        assert result.action == ACTION_NOOP

    def test_low_confidence_triage(self, _patch_router_paths, monkeypatch):
        import core.intelligence.pipeline.smart_router as sr

        # We need to mock add_to_triage_queue to avoid real filesystem writes
        triage_calls = []
        monkeypatch.setattr(sr, "add_to_triage_queue", lambda fp, d, b: triage_calls.append(b))

        inboxes = _patch_router_paths
        fp = inboxes["external"] / "ambiguous.txt"
        fp.write_text("could be anything")
        decision = FakeScopeDecision(primary_bucket="business", confidence=0.50)

        result = route(fp, decision)

        assert result.action == ACTION_TRIAGE
        assert "confidence" in result.triage_reason

    def test_very_low_confidence_skipped(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "noise.txt"
        fp.write_text("noise")
        decision = FakeScopeDecision(primary_bucket="business", confidence=0.10)

        result = route(fp, decision)

        assert result.action == ACTION_NOOP
        assert "skip threshold" in result.triage_reason

    def test_ref_file_skipped(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "something.ref.yaml"
        fp.write_text("ref: true")
        decision = FakeScopeDecision(confidence=0.99)

        result = route(fp, decision)

        assert result.action == ACTION_NOOP
        assert "ref file" in result.triage_reason

    def test_nonexistent_file_noop(self, _patch_router_paths):
        fp = Path("/nonexistent/ghost.txt")
        decision = FakeScopeDecision(confidence=0.99)

        result = route(fp, decision)

        assert result.action == ACTION_NOOP

    def test_unknown_location_noop(self, tmp_path):
        fp = tmp_path / "random" / "place.txt"
        fp.parent.mkdir(parents=True)
        fp.touch()
        decision = FakeScopeDecision(confidence=0.99)

        result = route(fp, decision)

        assert result.action == ACTION_NOOP
        assert "not in any recognized bucket" in result.triage_reason


# ===========================================================================
# 5. TestHandleCascades
# ===========================================================================
class TestHandleCascades:
    """handle_cascades creates .ref.yaml files in cascade buckets."""

    def test_cascade_creates_reference(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "course.txt"
        fp.write_text("course")
        decision = FakeScopeDecision(cascade_buckets=["business"])
        result = RouteResult(
            file_path=str(fp),
            destination_bucket="external",
        )

        handle_cascades(fp, decision, result)

        assert len(result.references_created) == 1
        ref_path = Path(result.references_created[0])
        assert ref_path.exists()

    def test_no_cascade_when_empty(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "simple.txt"
        fp.touch()
        decision = FakeScopeDecision(cascade_buckets=[])
        result = RouteResult(file_path=str(fp), destination_bucket="external")

        handle_cascades(fp, decision, result)

        assert result.references_created == []

    def test_cascade_skips_same_bucket(self, _patch_router_paths):
        inboxes = _patch_router_paths
        fp = inboxes["external"] / "test.txt"
        fp.touch()
        decision = FakeScopeDecision(cascade_buckets=["external"])
        result = RouteResult(file_path=str(fp), destination_bucket="external")

        handle_cascades(fp, decision, result)

        assert result.references_created == []


# ===========================================================================
# 6. TestTriageQueue
# ===========================================================================
class TestTriageQueue:
    """add_to_triage_queue manages the triage JSON file."""

    def test_queue_created_on_first_add(self, _patch_router_paths, tmp_path, monkeypatch):
        import core.intelligence.pipeline.smart_router as sr

        queue_path = tmp_path / "TRIAGE-QUEUE.json"
        monkeypatch.setattr(sr, "TRIAGE_QUEUE", queue_path)

        fp = tmp_path / "ambiguous.txt"
        fp.touch()
        decision = FakeScopeDecision(confidence=0.50)

        add_to_triage_queue(fp, decision, "external")

        assert queue_path.exists()
        data = json.loads(queue_path.read_text())
        assert len(data["entries"]) == 1
        assert data["entries"][0]["resolved"] is False

    def test_queue_appends_entries(self, _patch_router_paths, tmp_path, monkeypatch):
        import core.intelligence.pipeline.smart_router as sr

        queue_path = tmp_path / "TRIAGE-QUEUE.json"
        monkeypatch.setattr(sr, "TRIAGE_QUEUE", queue_path)

        for i in range(3):
            fp = tmp_path / f"file{i}.txt"
            fp.touch()
            add_to_triage_queue(fp, FakeScopeDecision(confidence=0.40 + i * 0.1), "external")

        data = json.loads(queue_path.read_text())
        assert len(data["entries"]) == 3


# ===========================================================================
# 7. TestHelpers
# ===========================================================================
class TestHelpers:
    """Helper function unit tests."""

    def test_is_ref_file_true(self):
        assert _is_ref_file(Path("something.ref.yaml")) is True

    def test_is_ref_file_false(self):
        assert _is_ref_file(Path("something.txt")) is False

    def test_is_ref_file_partial_match(self):
        assert _is_ref_file(Path("ref.yaml.bak")) is False

    def test_resolve_collision_no_collision(self, tmp_path):
        dest = tmp_path / "new-file.txt"
        assert _resolve_collision(dest) == dest

    def test_resolve_collision_with_existing(self, tmp_path):
        existing = tmp_path / "file.txt"
        existing.write_text("original")

        resolved = _resolve_collision(existing)

        assert resolved != existing
        assert resolved.suffix == ".txt"


# ===========================================================================
# 8. TestRouteResultDefaults
# ===========================================================================
class TestRouteResultDefaults:
    """RouteResult dataclass defaults."""

    def test_default_action(self):
        r = RouteResult()
        assert r.action == ACTION_NOOP

    def test_default_references_empty(self):
        r = RouteResult()
        assert r.references_created == []

    def test_default_confidence_zero(self):
        r = RouteResult()
        assert r.confidence == 0.0

    def test_default_organized_empty(self):
        r = RouteResult()
        assert r.organized_buckets == []


# ===========================================================================
# 9. TestRouteLogging
# ===========================================================================
class TestRouteLogging:
    """Verify that route() writes JSONL log entries."""

    def test_log_file_created(self, _patch_router_paths, tmp_path, monkeypatch):
        import core.intelligence.pipeline.smart_router as sr

        log_path = tmp_path / "smart-router.jsonl"
        monkeypatch.setattr(sr, "SMART_ROUTER_LOG", log_path)

        inboxes = _patch_router_paths
        fp = inboxes["external"] / "test.txt"
        fp.write_text("content")
        decision = FakeScopeDecision(primary_bucket="external", confidence=0.95)

        route(fp, decision)

        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["action"] == ACTION_NOOP
