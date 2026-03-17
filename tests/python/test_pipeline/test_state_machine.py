"""
test_state_machine.py -- Tests for MCE PipelineStateMachine
=============================================================

Covers: state transitions, persistence, recovery from failed states,
history logging, edge cases.

All tests are OFFLINE -- no real filesystem outside tmp_path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers: patch ROUTING so state files land in tmp_path
# ---------------------------------------------------------------------------


def _make_routing(tmp_path: Path) -> dict[str, Any]:
    """Return a ROUTING dict pointing mce_state at tmp_path."""
    return {"mce_state": tmp_path / "mce"}


@pytest.fixture()
def _patch_routing(tmp_path: Path):
    """Monkeypatch ROUTING in both state_machine and its helper module.

    Also patches the qa_gates import so conditions are not applied.
    Without this, condition functions check for pipeline artifacts on disk
    that don't exist in tests, causing transitions to silently block.
    """
    routing = _make_routing(tmp_path)
    with (
        patch("core.intelligence.pipeline.mce.state_machine.ROUTING", routing),
        patch.dict(
            "sys.modules",
            {"core.intelligence.pipeline.mce.qa_gates": None},
        ),
    ):
        yield routing


# ---------------------------------------------------------------------------
# Import under test (deferred so patches can land first)
# ---------------------------------------------------------------------------


def _import_sm():
    from core.intelligence.pipeline.mce.state_machine import (
        STATES,
        TRANSITIONS,
        PipelineStateMachine,
    )

    return PipelineStateMachine, STATES, TRANSITIONS


# ---------------------------------------------------------------------------
# Tests: Construction & Initial State
# ---------------------------------------------------------------------------


class TestConstruction:
    """Verify default and persisted initial states."""

    def test_default_initial_state(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("test-persona")
        assert sm.state == "init"
        assert sm.slug == "test-persona"

    def test_history_starts_empty(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("test-persona")
        assert sm.history == []

    def test_auto_load_false_ignores_disk(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        # Create a state file on disk with state=chunking
        state_dir = tmp_path / "mce" / "load-test"
        state_dir.mkdir(parents=True)
        (state_dir / "pipeline_state.yaml").write_text(
            yaml.dump({"state": "chunking", "history": [{"note": "old"}]})
        )
        sm = PSM("load-test", auto_load=False)
        assert sm.state == "init"
        assert sm.history == []

    def test_auto_load_resumes_from_disk(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        state_dir = tmp_path / "mce" / "resume-test"
        state_dir.mkdir(parents=True)
        history = [{"from": "init", "to": "chunking", "trigger": "start_chunking", "timestamp": "t1"}]
        (state_dir / "pipeline_state.yaml").write_text(
            yaml.dump({"state": "chunking", "history": history})
        )
        sm = PSM("resume-test")
        assert sm.state == "chunking"
        assert len(sm.history) == 1


# ---------------------------------------------------------------------------
# Tests: Valid Transitions (Happy Path)
# ---------------------------------------------------------------------------


class TestValidTransitions:
    """Walk through the full happy-path pipeline."""

    def test_full_pipeline_sequence(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("happy-path")

        sm.start_chunking()
        assert sm.state == "chunking"

        sm.start_entities()
        assert sm.state == "entities"

        sm.start_mce()
        assert sm.state == "mce_extraction"

        sm.checkpoint()
        assert sm.state == "identity_checkpoint"

        sm.approve()
        assert sm.state == "consolidation"

        sm.start_agents()
        assert sm.state == "agent_generation"

        sm.start_validation()
        assert sm.state == "validation"

        sm.finish()
        assert sm.state == "complete"
        assert sm.is_terminal is True

    def test_knowledge_extraction_path(self, _patch_routing):
        """Verify the entities -> knowledge_extraction transition."""
        PSM, _, _ = _import_sm()
        sm = PSM("knowledge-path")
        sm.start_chunking()
        sm.start_entities()
        sm.start_knowledge()
        assert sm.state == "knowledge_extraction"

    def test_revise_loops_back_to_mce(self, _patch_routing):
        """identity_checkpoint -> mce_extraction via revise."""
        PSM, _, _ = _import_sm()
        sm = PSM("revise-test")
        sm.start_chunking()
        sm.start_entities()
        sm.start_mce()
        sm.checkpoint()
        assert sm.state == "identity_checkpoint"
        sm.revise()
        assert sm.state == "mce_extraction"


# ---------------------------------------------------------------------------
# Tests: Invalid Transitions
# ---------------------------------------------------------------------------


class TestInvalidTransitions:
    """Verify that invalid transitions raise MachineError."""

    def test_cannot_finish_from_init(self, _patch_routing):
        from transitions.core import MachineError

        PSM, _, _ = _import_sm()
        sm = PSM("invalid-test")
        with pytest.raises(MachineError):
            sm.finish()

    def test_cannot_approve_from_init(self, _patch_routing):
        from transitions.core import MachineError

        PSM, _, _ = _import_sm()
        sm = PSM("invalid-test")
        with pytest.raises(MachineError):
            sm.approve()

    def test_cannot_start_agents_from_init(self, _patch_routing):
        from transitions.core import MachineError

        PSM, _, _ = _import_sm()
        sm = PSM("invalid-test")
        with pytest.raises(MachineError):
            sm.start_agents()


# ---------------------------------------------------------------------------
# Tests: Wildcard Transitions (fail, pause from any state)
# ---------------------------------------------------------------------------


class TestWildcardTransitions:
    """fail and pause should work from any state."""

    def test_fail_from_init(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("fail-test")
        sm.fail()
        assert sm.state == "failed"
        assert sm.is_terminal is True

    def test_fail_from_chunking(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("fail-test-2")
        sm.start_chunking()
        sm.fail()
        assert sm.state == "failed"

    def test_pause_from_entities(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("pause-test")
        sm.start_chunking()
        sm.start_entities()
        sm.pause()
        assert sm.state == "paused"
        assert sm.paused is True

    def test_recover_from_failed(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("recover-test")
        sm.fail()
        sm.recover()
        assert sm.state == "init"

    def test_recover_from_paused(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("recover-pause")
        sm.start_chunking()
        sm.pause()
        sm.recover()
        assert sm.state == "init"


# ---------------------------------------------------------------------------
# Tests: Persistence (save / load)
# ---------------------------------------------------------------------------


class TestPersistence:
    """Verify YAML persistence round-trips."""

    def test_save_creates_file(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        sm = PSM("save-test")
        sm.start_chunking()
        saved_path = sm.save()
        assert saved_path.exists()
        data = yaml.safe_load(saved_path.read_text())
        assert data["state"] == "chunking"
        assert data["slug"] == "save-test"

    def test_state_path_property(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        sm = PSM("path-test")
        assert sm.state_path == tmp_path / "mce" / "path-test" / "pipeline_state.yaml"

    def test_auto_save_on_transition(self, _patch_routing, tmp_path):
        """Each transition triggers _on_state_change -> save."""
        PSM, _, _ = _import_sm()
        sm = PSM("autosave-test")
        sm.start_chunking()
        assert sm.state_path.exists()
        data = yaml.safe_load(sm.state_path.read_text())
        assert data["state"] == "chunking"

    def test_round_trip_preserves_history(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        sm = PSM("roundtrip")
        sm.start_chunking()
        sm.start_entities()
        assert len(sm.history) == 2

        # Load in a new instance
        sm2 = PSM("roundtrip")
        assert sm2.state == "entities"
        assert len(sm2.history) == 2
        assert sm2.history[0]["trigger"] == "start_chunking"
        assert sm2.history[1]["trigger"] == "start_entities"


# ---------------------------------------------------------------------------
# Tests: History Logging
# ---------------------------------------------------------------------------


class TestHistory:
    """Verify history entries are properly recorded."""

    def test_history_entry_structure(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("history-test")
        sm.start_chunking()
        entry = sm.history[0]
        assert entry["from"] == "init"
        assert entry["to"] == "chunking"
        assert entry["trigger"] == "start_chunking"
        assert "timestamp" in entry

    def test_history_accumulates(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("accumulate")
        sm.start_chunking()
        sm.start_entities()
        sm.start_mce()
        assert len(sm.history) == 3

    def test_history_is_defensive_copy(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("copy-test")
        sm.start_chunking()
        h = sm.history
        h.clear()
        assert len(sm.history) == 1  # original not affected


# ---------------------------------------------------------------------------
# Tests: Reset
# ---------------------------------------------------------------------------


class TestReset:
    """Verify hard reset clears state and history."""

    def test_reset_returns_to_init(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("reset-test")
        sm.start_chunking()
        sm.start_entities()
        sm.reset()
        assert sm.state == "init"
        assert sm.history == []

    def test_reset_persists_to_disk(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        sm = PSM("reset-persist")
        sm.start_chunking()
        sm.reset()
        data = yaml.safe_load(sm.state_path.read_text())
        assert data["state"] == "init"
        assert data["history"] == []


# ---------------------------------------------------------------------------
# Tests: Convenience Properties
# ---------------------------------------------------------------------------


class TestConvenienceProperties:
    """Verify is_terminal, paused, repr."""

    def test_is_terminal_false_for_init(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("terminal-test")
        assert sm.is_terminal is False

    def test_paused_false_for_init(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("paused-test")
        assert sm.paused is False

    def test_repr_contains_slug_and_state(self, _patch_routing):
        PSM, _, _ = _import_sm()
        sm = PSM("repr-test")
        r = repr(sm)
        assert "repr-test" in r
        assert "init" in r


# ---------------------------------------------------------------------------
# Tests: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases: corrupt file, missing file, etc."""

    def test_load_corrupt_yaml_falls_back_to_init(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        state_dir = tmp_path / "mce" / "corrupt"
        state_dir.mkdir(parents=True)
        (state_dir / "pipeline_state.yaml").write_text("{{invalid yaml ::::")
        sm = PSM("corrupt")
        assert sm.state == "init"

    def test_load_non_dict_yaml_falls_back_to_init(self, _patch_routing, tmp_path):
        PSM, _, _ = _import_sm()
        state_dir = tmp_path / "mce" / "non-dict"
        state_dir.mkdir(parents=True)
        (state_dir / "pipeline_state.yaml").write_text('"just a string"')
        sm = PSM("non-dict")
        assert sm.state == "init"

    def test_constants_defined(self, _patch_routing):
        _, STATES, TRANSITIONS = _import_sm()
        assert "init" in STATES
        assert "complete" in STATES
        assert "failed" in STATES
        assert len(TRANSITIONS) >= 10
