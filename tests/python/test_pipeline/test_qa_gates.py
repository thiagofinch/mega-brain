"""
test_qa_gates.py -- Unit tests for MCE Pipeline Governance Sprint 1
====================================================================

Covers:
  - qa_gates.py: validate_step, validate_handoff, get_gate_status,
    condition functions (can_*), JSONL logging
  - mce_checkpoints.yaml: structure, counts, schema
  - mce.yaml: quality gates, veto conditions, schema
  - memory_enricher.py: dedup word-boundary fix
  - cascading.py: import smoke test

All tests are OFFLINE -- no real filesystem outside tmp_path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Project root on sys.path (conftest.py does this, but belt-and-suspenders)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helpers: isolated qa_gates environment
# ---------------------------------------------------------------------------


def _make_qa_env(tmp: Path) -> dict[str, Any]:
    """Build directory scaffold that qa_gates expects."""
    root = tmp / "mega-brain"
    root.mkdir()

    logs = root / "logs"
    logs.mkdir()
    (logs / "handoffs").mkdir()

    artifacts = root / "artifacts"
    (artifacts / "chunks").mkdir(parents=True)
    (artifacts / "canonical").mkdir(parents=True)
    (artifacts / "insights").mkdir(parents=True)

    knowledge_ext = root / "knowledge" / "external"
    (knowledge_ext / "dna" / "persons").mkdir(parents=True)
    (knowledge_ext / "dossiers" / "persons").mkdir(parents=True)
    (knowledge_ext / "sources").mkdir(parents=True)

    agents_ext = root / "agents" / "external"
    agents_ext.mkdir(parents=True)

    mission_control = root / ".claude" / "mission-control" / "mce"
    mission_control.mkdir(parents=True)

    return {
        "root": root,
        "logs": logs,
        "artifacts": artifacts,
        "knowledge_ext": knowledge_ext,
        "agents_ext": agents_ext,
        "mission_control": mission_control,
    }


@pytest.fixture()
def qa_env(tmp_path: Path):
    """Create isolated qa_gates environment and patch all path constants."""
    dirs = _make_qa_env(tmp_path)
    root = dirs["root"]
    logs = dirs["logs"]
    artifacts = dirs["artifacts"]
    knowledge_ext = dirs["knowledge_ext"]
    agents_ext = dirs["agents_ext"]
    mission_control = dirs["mission_control"]

    routing = {
        "quality_gaps": logs,
        "handoff": logs / "handoffs",
        "mce_state": mission_control,
    }

    patches = [
        patch("core.intelligence.pipeline.mce.qa_gates.LOGS", logs),
        patch("core.intelligence.pipeline.mce.qa_gates.ARTIFACTS", artifacts),
        patch("core.intelligence.pipeline.mce.qa_gates.KNOWLEDGE_EXTERNAL", knowledge_ext),
        patch("core.intelligence.pipeline.mce.qa_gates.AGENTS_EXTERNAL", agents_ext),
        patch("core.intelligence.pipeline.mce.qa_gates.MISSION_CONTROL", mission_control),
        patch("core.intelligence.pipeline.mce.qa_gates.ROUTING", routing),
        # Patch derived paths that use ROUTING/LOGS/etc. at module level
        patch("core.intelligence.pipeline.mce.qa_gates._QA_LOG", logs / "quality-gaps.jsonl"),
        patch(
            "core.intelligence.pipeline.mce.qa_gates._HANDOFF_LOG",
            logs / "handoffs" / "mce-handoffs.jsonl",
        ),
        patch("core.intelligence.pipeline.mce.qa_gates._MCE_STATE_DIR", mission_control),
        # Patch artifact paths
        patch(
            "core.intelligence.pipeline.mce.qa_gates.CHUNKS_STATE",
            artifacts / "chunks" / "CHUNKS-STATE.json",
        ),
        patch(
            "core.intelligence.pipeline.mce.qa_gates.CANONICAL_MAP",
            artifacts / "canonical" / "CANONICAL-MAP.json",
        ),
        patch(
            "core.intelligence.pipeline.mce.qa_gates.INSIGHTS_STATE",
            artifacts / "insights" / "INSIGHTS-STATE.json",
        ),
    ]
    for p in patches:
        p.start()

    # Reset caches between tests
    import core.intelligence.pipeline.mce.qa_gates as mod

    mod._checkpoints_cache = None
    mod._gates_cache = None

    yield dirs

    mod._checkpoints_cache = None
    mod._gates_cache = None
    for p in patches:
        p.stop()


def _import_qa_gates():
    """Import qa_gates public API lazily to ensure patches are applied."""
    from core.intelligence.pipeline.mce.qa_gates import (
        can_approve,
        can_checkpoint,
        can_finish,
        can_start_agents,
        can_start_chunking,
        can_start_entities,
        can_start_knowledge,
        can_validate,
        get_gate_status,
        validate_handoff,
        validate_step,
    )

    return {
        "validate_step": validate_step,
        "validate_handoff": validate_handoff,
        "get_gate_status": get_gate_status,
        "can_start_chunking": can_start_chunking,
        "can_start_entities": can_start_entities,
        "can_start_knowledge": can_start_knowledge,
        "can_checkpoint": can_checkpoint,
        "can_approve": can_approve,
        "can_start_agents": can_start_agents,
        "can_validate": can_validate,
        "can_finish": can_finish,
    }


# ===========================================================================
# SECTION 1: qa_gates.py tests
# ===========================================================================


class TestValidateStep:
    """Verify validate_step returns correct structures and handles edge cases."""

    def test_validate_step_returns_correct_structure(self, qa_env):
        """Test 1: validate_step(3, 'test') returns dict with required keys."""
        fns = _import_qa_gates()
        result = fns["validate_step"](3, "test")

        assert isinstance(result, dict)
        assert "passed" in result
        assert "checks" in result
        assert "blocking_failures" in result
        assert "timestamp" in result
        assert "step" in result
        assert "slug" in result
        assert isinstance(result["passed"], bool)
        assert isinstance(result["checks"], list)
        assert isinstance(result["blocking_failures"], list)
        assert result["step"] == 3
        assert result["slug"] == "test"

    def test_validate_step_fails_for_missing_artifacts(self, qa_env):
        """Test 2: step 3 with no CHUNKS-STATE.json returns passed=False."""
        fns = _import_qa_gates()
        # No CHUNKS-STATE.json exists in the tmp environment
        result = fns["validate_step"](3, "test")

        assert result["passed"] is False
        assert len(result["blocking_failures"]) > 0

    def test_validate_step_invalid_step_number(self, qa_env):
        """Test 3: step 99 returns passed=True with warning (graceful degradation)."""
        fns = _import_qa_gates()
        result = fns["validate_step"](99, "test")

        # Per the code: no validator -> passed=True with warning
        # This is by design for forward-compat (new steps added later).
        assert isinstance(result, dict)
        assert "passed" in result
        assert result.get("warning") is not None or result["passed"] is True


class TestValidateHandoff:
    """Verify validate_handoff returns correct structure."""

    def test_validate_handoff_structure(self, qa_env):
        """Test 4: validate_handoff(3, 4, 'test') returns correct keys."""
        fns = _import_qa_gates()
        result = fns["validate_handoff"](3, 4, "test")

        assert isinstance(result, dict)
        assert "passed" in result
        assert "from_step" in result
        assert "to_step" in result
        assert "slug" in result
        assert "checks" in result
        assert "artifacts_required" in result
        assert "artifacts_present" in result
        assert "timestamp" in result
        assert result["from_step"] == 3
        assert result["to_step"] == 4
        assert result["slug"] == "test"


class TestGetGateStatus:
    """Verify get_gate_status returns overview structure."""

    def test_get_gate_status_structure(self, qa_env):
        """Test 5: returns dict with slug and steps keys."""
        fns = _import_qa_gates()
        result = fns["get_gate_status"]("test-person")

        assert isinstance(result, dict)
        assert "slug" in result
        assert "steps" in result
        assert result["slug"] == "test-person"
        assert isinstance(result["steps"], dict)
        # Should have entries for steps 1-12
        for step_num in range(1, 13):
            assert step_num in result["steps"]


class TestConditionFunctions:
    """Verify condition functions exist and accept event parameter."""

    def test_condition_functions_exist(self, qa_env):
        """Test 6: all 8 can_* functions are callable."""
        fns = _import_qa_gates()
        condition_names = [
            "can_start_chunking",
            "can_start_entities",
            "can_start_knowledge",
            "can_checkpoint",
            "can_approve",
            "can_start_agents",
            "can_validate",
            "can_finish",
        ]
        for name in condition_names:
            assert name in fns, f"Missing condition function: {name}"
            assert callable(fns[name]), f"{name} is not callable"

    def test_condition_functions_accept_event(self, qa_env):
        """Test 7: can_start_chunking(event=None) works without error."""
        fns = _import_qa_gates()
        # All condition functions should accept event=None gracefully
        # (transitions library sends event objects, but None is valid for testing)
        result = fns["can_start_chunking"](event=None)
        assert isinstance(result, bool)


class TestNoImportCycle:
    """Verify qa_gates does NOT import state_machine."""

    def test_no_import_cycle_with_state_machine(self, qa_env):
        """Test 8: importing qa_gates does NOT import state_machine."""
        import ast

        qa_gates_path = (
            PROJECT_ROOT
            / "core"
            / "intelligence"
            / "pipeline"
            / "mce"
            / "qa_gates.py"
        )
        source = qa_gates_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)

        for mod in imported_modules:
            assert "state_machine" not in mod, (
                f"qa_gates.py imports '{mod}' which contains 'state_machine' -- "
                "this creates a circular import"
            )


class TestJSONLLogging:
    """Verify validate_step writes to JSONL log."""

    def test_jsonl_logging(self, qa_env):
        """Test 9: validate_step writes to quality_gaps JSONL path."""
        fns = _import_qa_gates()
        fns["validate_step"](3, "log-test-slug")

        log_file = qa_env["logs"] / "quality-gaps.jsonl"
        assert log_file.exists(), "quality-gaps.jsonl was not created"

        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) >= 1, "No entries written to JSONL"

        entry = json.loads(lines[0])
        assert "step" in entry
        assert "slug" in entry
        assert "passed" in entry
        assert entry["slug"] == "log-test-slug"


# ===========================================================================
# SECTION 2: mce_checkpoints.yaml tests
# ===========================================================================


class TestCheckpointsYAML:
    """Validate mce_checkpoints.yaml structure and content."""

    @pytest.fixture(scope="class")
    def checkpoints_data(self) -> dict[str, Any]:
        cp_path = PROJECT_ROOT / "core" / "intelligence" / "pipeline" / "mce" / "mce_checkpoints.yaml"
        with open(cp_path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def test_checkpoints_yaml_valid(self, checkpoints_data):
        """Test 10: file loads without error."""
        assert checkpoints_data is not None
        assert isinstance(checkpoints_data, dict)

    def test_checkpoints_count_minimum(self, checkpoints_data):
        """Test 11: at least 100 checkpoints."""
        cps = checkpoints_data.get("checkpoints", [])
        assert len(cps) >= 100, f"Only {len(cps)} checkpoints (expected >= 100)"

    def test_all_steps_covered(self, checkpoints_data):
        """Test 12: steps 1-12 all have at least 1 checkpoint."""
        cps = checkpoints_data.get("checkpoints", [])
        steps_present = {cp.get("step_number") for cp in cps}
        for step in range(1, 13):
            assert step in steps_present, f"Step {step} has no checkpoints"

    def test_checkpoint_schema(self, checkpoints_data):
        """Test 13: each checkpoint has required fields."""
        cps = checkpoints_data.get("checkpoints", [])
        required_fields = {"id", "step_number", "check_type"}
        for cp in cps:
            for field in required_fields:
                assert field in cp, (
                    f"Checkpoint {cp.get('id', '?')} missing field '{field}'"
                )
            # check_type must be deterministic or llm
            assert cp["check_type"] in ("deterministic", "llm"), (
                f"Checkpoint {cp['id']} has invalid check_type: {cp['check_type']}"
            )
            # blocking must be present (boolean)
            assert "blocking" in cp, (
                f"Checkpoint {cp['id']} missing 'blocking' field"
            )

    def test_no_duplicate_ids(self, checkpoints_data):
        """Test 14: all checkpoint IDs are unique."""
        cps = checkpoints_data.get("checkpoints", [])
        ids = [cp.get("id") for cp in cps]
        duplicates = [x for x in ids if ids.count(x) > 1]
        assert len(duplicates) == 0, f"Duplicate checkpoint IDs: {set(duplicates)}"


# ===========================================================================
# SECTION 3: mce.yaml tests
# ===========================================================================


class TestMCEYAML:
    """Validate mce.yaml quality gates and veto conditions."""

    @pytest.fixture(scope="class")
    def mce_data(self) -> dict[str, Any]:
        mce_path = PROJECT_ROOT / "core" / "engine" / "rules" / "workflows" / "mce.yaml"
        with open(mce_path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def test_mce_yaml_valid(self, mce_data):
        """Test 15: file loads without error."""
        assert mce_data is not None
        assert isinstance(mce_data, dict)

    def test_quality_gates_count(self, mce_data):
        """Test 16: 10-15 gates defined."""
        gates = mce_data.get("quality_gates", [])
        assert 10 <= len(gates) <= 15, f"Found {len(gates)} gates (expected 10-15)"

    def test_veto_conditions_count(self, mce_data):
        """Test 17: 10-15 vetos defined."""
        vetos = mce_data.get("veto_conditions", [])
        assert 10 <= len(vetos) <= 15, f"Found {len(vetos)} vetos (expected 10-15)"

    def test_gate_schema(self, mce_data):
        """Test 18: each gate has id, description, severity, step_applies_to."""
        gates = mce_data.get("quality_gates", [])
        for gate in gates:
            assert "id" in gate, f"Gate missing 'id': {gate}"
            assert "description" in gate, f"Gate {gate['id']} missing 'description'"
            assert "severity" in gate, f"Gate {gate['id']} missing 'severity'"
            assert "step_applies_to" in gate, f"Gate {gate['id']} missing 'step_applies_to'"
            assert gate["severity"] in ("block", "warn", "info"), (
                f"Gate {gate['id']} has invalid severity: {gate['severity']}"
            )
            assert isinstance(gate["step_applies_to"], list), (
                f"Gate {gate['id']} step_applies_to must be a list"
            )

    def test_veto_schema(self, mce_data):
        """Test 19: each veto has id, trigger_condition, action."""
        vetos = mce_data.get("veto_conditions", [])
        for veto in vetos:
            assert "id" in veto, f"Veto missing 'id': {veto}"
            assert "trigger_condition" in veto, f"Veto {veto['id']} missing 'trigger_condition'"
            assert "action" in veto, f"Veto {veto['id']} missing 'action'"
            assert veto["action"] in ("block", "escalate"), (
                f"Veto {veto['id']} has invalid action: {veto['action']}"
            )


# ===========================================================================
# SECTION 4: memory_enricher.py dedup tests
# ===========================================================================


class TestMemoryEnricherDedup:
    """Verify word-boundary dedup regex in memory_enricher.py."""

    def _get_is_duplicate(self):
        from core.intelligence.pipeline.memory_enricher import _is_duplicate

        return _is_duplicate

    def test_is_duplicate_word_boundary(self):
        """Test 20: chunk_1 does NOT match chunk_10."""
        is_dup = self._get_is_duplicate()
        text = "Some text with chunk_10 and chunk_100 mentioned."
        assert is_dup(text, "chunk_1") is False, (
            "chunk_1 should NOT match chunk_10 (word boundary bug)"
        )

    def test_is_duplicate_exact_match(self):
        """Test 21: chunk_1 DOES match chunk_1."""
        is_dup = self._get_is_duplicate()
        text = "Previously we had chunk_1 inserted here."
        assert is_dup(text, "chunk_1") is True, (
            "chunk_1 should match exact chunk_1 occurrence"
        )

    def test_is_duplicate_empty_id(self):
        """Test 22: empty chunk_id returns False."""
        is_dup = self._get_is_duplicate()
        assert is_dup("any text content", "") is False


# ===========================================================================
# SECTION 5: cascading.py import test
# ===========================================================================


class TestCascading:
    """Verify cascading.py module imports without error."""

    def test_cascading_imports(self):
        """Test 23: module imports without error."""
        try:
            import core.intelligence.pipeline.mce.cascading as cascading_mod

            assert hasattr(cascading_mod, "run_post_extraction_cascade")
            assert callable(cascading_mod.run_post_extraction_cascade)
        except ImportError as exc:
            pytest.fail(f"cascading.py import failed: {exc}")
