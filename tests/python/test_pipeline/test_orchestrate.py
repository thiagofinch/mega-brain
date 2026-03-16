"""
test_orchestrate.py -- Tests for MCE Pipeline Orchestrator
============================================================

Covers: cmd_ingest, cmd_batch, cmd_finalize, cmd_status, cmd_full, main,
helper functions (_slug_from_path, _build_result, _append_jsonl).

All tests are OFFLINE -- no real filesystem outside tmp_path.
Heavy deps (scope_classifier, smart_router, etc.) are mocked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fake dataclass stubs for lazy imports
# ---------------------------------------------------------------------------


@dataclass
class FakeClassificationCtx:
    text: str = ""
    filename: str = ""
    file_path: str = ""


@dataclass
class FakeDecision:
    primary_bucket: str = "external"
    cascade_buckets: list[str] = field(default_factory=list)
    confidence: float = 0.90
    source_type: str = "course"
    reasons: list[str] = field(default_factory=lambda: ["test-reason"])


@dataclass
class FakeRouteResult:
    action: str = "moved"
    moved_to: str = "/tmp/fake-moved"
    references_created: list[str] = field(default_factory=list)


@dataclass
class FakeScanResult:
    batches_created: list[Any] = field(default_factory=list)
    files_scanned: int = 5
    files_already_batched: int = 0
    files_below_threshold: int = 1
    duration_ms: float = 100.0


@dataclass
class FakeBatchInfo:
    batch_id: str = "BATCH-001-AH"
    source_name: str = "alex-hormozi"
    source_code: str = "AH"
    file_count: int = 3
    total_size_bytes: int = 50000


@dataclass
class FakeSyncResult:
    synced: list[str] = field(default_factory=list)
    skipped: int = 0
    errors: int = 0


# ---------------------------------------------------------------------------
# Helpers: patch ROUTING + paths so all state lands in tmp_path
# ---------------------------------------------------------------------------


def _make_routing(tmp: Path) -> dict[str, Any]:
    return {
        "mce_state": tmp / "mce",
        "mce_metrics_log": tmp / "logs" / "mce-metrics.jsonl",
    }


@pytest.fixture()
def env(tmp_path: Path):
    """Set up an isolated environment for orchestrate tests.

    Patches ROUTING in orchestrate.py AND all 3 supporting MCE modules
    (state_machine, metadata_manager, metrics) plus the LOGS/_ORCHESTRATE_LOG
    constants so all files land in tmp_path.
    """
    routing = _make_routing(tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    artifacts = tmp_path / "artifacts"
    (artifacts / "insights").mkdir(parents=True, exist_ok=True)
    mc = tmp_path / ".claude" / "mission-control"
    mc.mkdir(parents=True, exist_ok=True)

    patches = [
        # Orchestrate module itself
        patch("core.intelligence.pipeline.mce.orchestrate.ROUTING", routing),
        patch("core.intelligence.pipeline.mce.orchestrate.LOGS", logs_dir),
        patch("core.intelligence.pipeline.mce.orchestrate.ARTIFACTS", artifacts),
        patch("core.intelligence.pipeline.mce.orchestrate.MISSION_CONTROL", mc),
        patch(
            "core.intelligence.pipeline.mce.orchestrate._ORCHESTRATE_LOG",
            logs_dir / "mce-orchestrate.jsonl",
        ),
        # State machine
        patch("core.intelligence.pipeline.mce.state_machine.ROUTING", routing),
        # Metadata manager
        patch("core.intelligence.pipeline.mce.metadata_manager.ROUTING", routing),
        # Metrics
        patch("core.intelligence.pipeline.mce.metrics.ROUTING", routing),
        patch("core.intelligence.pipeline.mce.metrics.LOGS", logs_dir),
    ]
    for p in patches:
        p.start()

    yield {
        "tmp": tmp_path,
        "routing": routing,
        "logs": logs_dir,
        "artifacts": artifacts,
    }

    for p in patches:
        p.stop()


def _import_orchestrate():
    from core.intelligence.pipeline.mce.orchestrate import (
        _append_jsonl,
        _build_result,
        _slug_from_path,
        cmd_batch,
        cmd_finalize,
        cmd_full,
        cmd_ingest,
        cmd_status,
        main,
    )

    return (
        cmd_ingest,
        cmd_batch,
        cmd_finalize,
        cmd_status,
        cmd_full,
        main,
        _slug_from_path,
        _build_result,
        _append_jsonl,
    )


# ---------------------------------------------------------------------------
# Fake workflow detector (always returns greenfield)
# ---------------------------------------------------------------------------

_FAKE_WF_MODE = MagicMock(
    mode="greenfield", has_agent=False, has_dna=False, has_mce=False,
    to_dict=lambda: {
        "mode": "greenfield",
        "has_agent": False,
        "has_dna": False,
        "has_mce": False,
        "new_sources": [],
        "delta_sources": [],
    },
)


# ===========================================================================
# Tests: _slug_from_path
# ===========================================================================


class TestSlugFromPath:
    """Verify slug extraction from various inbox path patterns."""

    def test_external_inbox_path(self, env):
        _, _, _, _, _, _, slug_fn, _, _ = _import_orchestrate()
        p = "/knowledge/external/inbox/alex-hormozi/transcript.txt"
        assert slug_fn(p) == "alex-hormozi"

    def test_business_inbox_path(self, env):
        _, _, _, _, _, _, slug_fn, _, _ = _import_orchestrate()
        p = "/knowledge/business/inbox/MEETINGS/furion/call-001.txt"
        assert slug_fn(p) == "furion"

    def test_sources_path(self, env):
        _, _, _, _, _, _, slug_fn, _, _ = _import_orchestrate()
        p = "/knowledge/external/sources/cole-gordon/raw/video.txt"
        assert slug_fn(p) == "cole-gordon"

    def test_skip_generic_dirs(self, env):
        _, _, _, _, _, _, slug_fn, _, _ = _import_orchestrate()
        p = "/knowledge/external/inbox/EXTERNAL/real-person/file.txt"
        assert slug_fn(p) == "real-person"

    def test_skip_uppercase_slug_dirs(self, env):
        _, _, _, _, _, _, slug_fn, _, _ = _import_orchestrate()
        p = "/knowledge/personal/inbox/PESSOAL/note.txt"
        # PESSOAL is in _SLUG_SKIP_DIRS, so should walk up
        result = slug_fn(p)
        assert result != "pessoal"


# ===========================================================================
# Tests: _build_result
# ===========================================================================


class TestBuildResult:
    """Verify standardized result dict construction."""

    def test_success_result(self, env):
        _, _, _, _, _, _, _, build_fn, _ = _import_orchestrate()
        r = build_fn("ingest", success=True, slug="test", duration_ms=42.5)
        assert r["command"] == "ingest"
        assert r["success"] is True
        assert r["slug"] == "test"
        assert r["duration_ms"] == 42.5
        assert "timestamp" in r

    def test_failure_result(self, env):
        _, _, _, _, _, _, _, build_fn, _ = _import_orchestrate()
        r = build_fn("batch", success=False, error="boom")
        assert r["success"] is False
        assert r["error"] == "boom"

    def test_extras_included(self, env):
        _, _, _, _, _, _, _, build_fn, _ = _import_orchestrate()
        r = build_fn("status", success=True, custom_key="value")
        assert r["custom_key"] == "value"


# ===========================================================================
# Tests: _append_jsonl
# ===========================================================================


class TestAppendJsonl:
    """Verify audit log writing."""

    def test_appends_to_jsonl_file(self, env):
        _, _, _, _, _, _, _, _, append_fn = _import_orchestrate()
        append_fn({"event": "test", "value": 42})
        log_file = env["logs"] / "mce-orchestrate.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["event"] == "test"

    def test_multiple_appends(self, env):
        _, _, _, _, _, _, _, _, append_fn = _import_orchestrate()
        append_fn({"n": 1})
        append_fn({"n": 2})
        log_file = env["logs"] / "mce-orchestrate.jsonl"
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2


# ===========================================================================
# Tests: cmd_ingest
# ===========================================================================


class TestCmdIngest:
    """Verify the ingest command."""

    def test_file_not_found(self, env):
        cmd_ingest, *_ = _import_orchestrate()
        r = cmd_ingest("/nonexistent/path/file.txt")
        assert r["success"] is False
        assert "not found" in r["error"].lower()

    def test_not_a_file(self, env, tmp_path):
        cmd_ingest, *_ = _import_orchestrate()
        d = tmp_path / "a-directory"
        d.mkdir()
        r = cmd_ingest(str(d))
        assert r["success"] is False
        assert "not a file" in r["error"].lower()

    @patch("core.intelligence.pipeline.mce.orchestrate._import_workspace_sync")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_inbox_organizer")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_smart_router")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_scope_classifier")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_successful_ingest(
        self, mock_wf, mock_sc, mock_sr, mock_org, mock_ws, env, tmp_path
    ):
        # Setup mocks
        mock_classify = MagicMock(return_value=FakeDecision())
        mock_sc.return_value = (mock_classify, FakeClassificationCtx)

        mock_route = MagicMock(return_value=FakeRouteResult())
        mock_sr.return_value = mock_route

        mock_organize = MagicMock(return_value={"organized": 2})
        mock_org.return_value = mock_organize

        # Create a real file to ingest
        inbox = tmp_path / "knowledge" / "external" / "inbox" / "test-person"
        inbox.mkdir(parents=True)
        src = inbox / "transcript.txt"
        src.write_text("Hello world -- this is test content for ingestion.")

        cmd_ingest, *_ = _import_orchestrate()
        r = cmd_ingest(str(src))

        assert r["success"] is True
        assert r["command"] == "ingest"
        assert "classification" in r
        assert r["classification"]["primary_bucket"] == "external"
        assert r["classification"]["confidence"] == 0.9
        assert "routing" in r
        assert "workflow" in r
        assert r["workflow"]["mode"] == "greenfield"
        assert "state" in r

    @patch("core.intelligence.pipeline.mce.orchestrate._import_scope_classifier")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_classification_failure(self, mock_wf, mock_sc, env, tmp_path):
        mock_classify = MagicMock(side_effect=RuntimeError("LLM down"))
        mock_sc.return_value = (mock_classify, FakeClassificationCtx)

        src = tmp_path / "bad-file.txt"
        src.write_text("content")

        cmd_ingest, *_ = _import_orchestrate()
        r = cmd_ingest(str(src))

        assert r["success"] is False
        assert "classification failed" in r["error"].lower()

    @patch("core.intelligence.pipeline.mce.orchestrate._import_inbox_organizer")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_smart_router")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_scope_classifier")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_routing_failure(self, mock_wf, mock_sc, mock_sr, mock_org, env, tmp_path):
        mock_classify = MagicMock(return_value=FakeDecision())
        mock_sc.return_value = (mock_classify, FakeClassificationCtx)
        mock_route = MagicMock(side_effect=OSError("Disk full"))
        mock_sr.return_value = mock_route

        src = tmp_path / "route-fail.txt"
        src.write_text("content")

        cmd_ingest, *_ = _import_orchestrate()
        r = cmd_ingest(str(src))

        assert r["success"] is False
        assert "routing failed" in r["error"].lower()

    @patch("core.intelligence.pipeline.mce.orchestrate._import_inbox_organizer")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_smart_router")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_scope_classifier")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_inbox_org_failure_non_fatal(
        self, mock_wf, mock_sc, mock_sr, mock_org, env, tmp_path
    ):
        """Inbox organization failure should NOT fail the overall ingest."""
        mock_classify = MagicMock(return_value=FakeDecision())
        mock_sc.return_value = (mock_classify, FakeClassificationCtx)
        mock_route = MagicMock(return_value=FakeRouteResult())
        mock_sr.return_value = mock_route
        mock_organize = MagicMock(side_effect=RuntimeError("org fail"))
        mock_org.return_value = mock_organize

        src = tmp_path / "org-fail.txt"
        src.write_text("content")

        cmd_ingest, *_ = _import_orchestrate()
        r = cmd_ingest(str(src))

        assert r["success"] is True
        assert r["organization"]["organized"] == 0


# ===========================================================================
# Tests: cmd_batch
# ===========================================================================


class TestCmdBatch:
    """Verify the batch command."""

    @patch("core.intelligence.pipeline.mce.orchestrate._import_batch_auto_creator")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_successful_batch(self, mock_wf, mock_bac, env):
        fake_batch = FakeBatchInfo()
        scan = FakeScanResult(batches_created=[fake_batch])
        mock_bac.return_value = MagicMock(return_value=scan)

        _, cmd_batch, *_ = _import_orchestrate()
        r = cmd_batch("alex-hormozi")

        assert r["success"] is True
        assert r["command"] == "batch"
        assert r["slug"] == "alex-hormozi"
        assert len(r["batches_for_slug"]) == 1
        assert r["batches_for_slug"][0]["batch_id"] == "BATCH-001-AH"

    @patch("core.intelligence.pipeline.mce.orchestrate._import_batch_auto_creator")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_batch_creation_failure(self, mock_wf, mock_bac, env):
        mock_bac.return_value = MagicMock(side_effect=RuntimeError("scan exploded"))

        _, cmd_batch, *_ = _import_orchestrate()
        r = cmd_batch("test-slug")

        assert r["success"] is False
        assert "batch creation failed" in r["error"].lower()

    @patch("core.intelligence.pipeline.mce.orchestrate._import_batch_auto_creator")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_batch_no_matching_slug(self, mock_wf, mock_bac, env):
        """Batches exist but none match the requested slug."""
        other_batch = FakeBatchInfo(source_name="other-person")
        scan = FakeScanResult(batches_created=[other_batch])
        mock_bac.return_value = MagicMock(return_value=scan)

        _, cmd_batch, *_ = _import_orchestrate()
        r = cmd_batch("alex-hormozi")

        assert r["success"] is True
        assert r["batches_for_slug"] == []
        assert r["scan_summary"]["total_batches_created"] == 1

    @patch("core.intelligence.pipeline.mce.orchestrate._import_batch_auto_creator")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_batch_empty_scan(self, mock_wf, mock_bac, env):
        scan = FakeScanResult(batches_created=[])
        mock_bac.return_value = MagicMock(return_value=scan)

        _, cmd_batch, *_ = _import_orchestrate()
        r = cmd_batch("empty-slug")

        assert r["success"] is True
        assert r["batches_for_slug"] == []


# ===========================================================================
# Tests: cmd_finalize
# ===========================================================================


class TestCmdFinalize:
    """Verify the finalize command."""

    @patch("core.intelligence.pipeline.mce.orchestrate._import_workspace_sync")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_memory_enricher")
    def test_finalize_no_insights_file(self, mock_me, mock_ws, env):
        # No INSIGHTS-STATE.json => enrichment skipped
        mock_ws.return_value = MagicMock(return_value=FakeSyncResult())

        _, _, cmd_finalize, *_ = _import_orchestrate()
        r = cmd_finalize("test-slug")

        assert r["success"] is True
        assert r["enrichment"]["skipped"] == "INSIGHTS-STATE.json not found"
        mock_me.assert_not_called()

    @patch("core.intelligence.pipeline.mce.orchestrate._import_workspace_sync")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_memory_enricher")
    def test_finalize_with_insights(self, mock_me, mock_ws, env):
        # Create INSIGHTS-STATE.json
        insights_path = env["artifacts"] / "insights" / "INSIGHTS-STATE.json"
        insights_path.write_text(json.dumps({"insights": []}))

        mock_enrich = MagicMock(return_value={"appended": 3, "skipped_dedup": 1, "agents_enriched": ["a/b"]})
        mock_me.return_value = mock_enrich
        mock_ws.return_value = MagicMock(return_value=FakeSyncResult(synced=["f1.md", "f2.md"]))

        _, _, cmd_finalize, *_ = _import_orchestrate()
        r = cmd_finalize("enriched-slug")

        assert r["success"] is True
        assert r["enrichment"]["appended"] == 3
        assert r["enrichment"]["skipped_dedup"] == 1
        assert r["workspace_sync"]["synced"] == 2

    @patch("core.intelligence.pipeline.mce.orchestrate._import_workspace_sync")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_memory_enricher")
    def test_finalize_enrichment_failure_non_fatal(self, mock_me, mock_ws, env):
        insights_path = env["artifacts"] / "insights" / "INSIGHTS-STATE.json"
        insights_path.write_text(json.dumps({"insights": []}))

        mock_enrich = MagicMock(side_effect=RuntimeError("enricher crashed"))
        mock_me.return_value = mock_enrich
        mock_ws.return_value = MagicMock(return_value=FakeSyncResult())

        _, _, cmd_finalize, *_ = _import_orchestrate()
        r = cmd_finalize("fail-enrich")

        assert r["success"] is True
        assert "error" in r["enrichment"]

    @patch("core.intelligence.pipeline.mce.orchestrate._import_workspace_sync")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_memory_enricher")
    def test_finalize_sync_failure_non_fatal(self, mock_me, mock_ws, env):
        mock_ws.return_value = MagicMock(side_effect=RuntimeError("sync crash"))

        _, _, cmd_finalize, *_ = _import_orchestrate()
        r = cmd_finalize("fail-sync")

        assert r["success"] is True
        assert "error" in r["workspace_sync"]

    @patch("core.intelligence.pipeline.mce.orchestrate._import_workspace_sync")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_memory_enricher")
    def test_finalize_marks_metadata_complete(self, mock_me, mock_ws, env):
        mock_ws.return_value = MagicMock(return_value=FakeSyncResult())

        _, _, cmd_finalize, *_ = _import_orchestrate()
        r = cmd_finalize("complete-slug")

        assert r["success"] is True
        assert r["state"]["metadata_status"] == "complete"


# ===========================================================================
# Tests: cmd_status
# ===========================================================================


class TestCmdStatus:
    """Verify the status command."""

    def test_status_all_empty(self, env):
        _, _, _, cmd_status, *_ = _import_orchestrate()
        r = cmd_status(None)

        assert r["success"] is True
        assert r["count"] == 0
        assert r["active_pipelines"] == []

    def test_status_all_discovers_pipelines(self, env, tmp_path):
        # Create 2 MCE pipeline dirs
        for slug in ("person-a", "person-b"):
            d = tmp_path / "mce" / slug
            d.mkdir(parents=True)

        _, _, _, cmd_status, *_ = _import_orchestrate()
        r = cmd_status(None)

        assert r["success"] is True
        assert r["count"] == 2
        slugs = [p["slug"] for p in r["active_pipelines"]]
        assert "person-a" in slugs
        assert "person-b" in slugs

    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_status_single_slug(self, mock_wf, env):
        _, _, _, cmd_status, *_ = _import_orchestrate()
        r = cmd_status("new-slug")

        assert r["success"] is True
        assert r["slug"] == "new-slug"
        assert r["state_machine"]["current_state"] == "init"
        assert r["workflow"]["mode"] == "greenfield"
        assert r["metadata"] is None  # no saved metadata yet

    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_status_output_structure(self, mock_wf, env):
        _, _, _, cmd_status, *_ = _import_orchestrate()
        r = cmd_status("struct-slug")

        assert "state_machine" in r
        assert "workflow" in r
        assert "metadata" in r
        assert "metrics" in r
        assert "timestamp" in r
        assert "duration_ms" in r


# ===========================================================================
# Tests: cmd_full
# ===========================================================================


class TestCmdFull:
    """Verify the full shortcut command."""

    @patch("core.intelligence.pipeline.mce.orchestrate._import_batch_auto_creator")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_inbox_organizer")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_smart_router")
    @patch("core.intelligence.pipeline.mce.orchestrate._import_scope_classifier")
    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_full_success(self, mock_wf, mock_sc, mock_sr, mock_org, mock_bac, env, tmp_path):
        mock_classify = MagicMock(return_value=FakeDecision())
        mock_sc.return_value = (mock_classify, FakeClassificationCtx)
        mock_sr.return_value = MagicMock(return_value=FakeRouteResult())
        mock_org.return_value = MagicMock(return_value={"organized": 1})
        mock_bac.return_value = MagicMock(return_value=FakeScanResult())

        src = tmp_path / "full-test.txt"
        src.write_text("content for full pipeline test")

        _, _, _, _, cmd_full, *_ = _import_orchestrate()
        r = cmd_full(str(src))

        assert r["success"] is True
        assert r["command"] == "full"
        assert "ingest" in r
        assert "batch" in r
        assert "status" in r

    def test_full_fails_on_missing_file(self, env):
        _, _, _, _, cmd_full, *_ = _import_orchestrate()
        r = cmd_full("/does/not/exist.txt")

        assert r["success"] is False
        assert "ingest step failed" in r["error"].lower()


# ===========================================================================
# Tests: main (CLI entry point)
# ===========================================================================


class TestMain:
    """Verify CLI argument parsing and dispatching."""

    def test_help_returns_zero(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["--help"]) == 0

    def test_no_args_returns_zero(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn([]) == 0

    def test_unknown_command(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["bogus"]) == 1

    def test_ingest_missing_arg(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["ingest"]) == 1

    def test_batch_missing_arg(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["batch"]) == 1

    def test_finalize_missing_arg(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["finalize"]) == 1

    def test_full_missing_arg(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["full"]) == 1

    @patch("core.intelligence.pipeline.mce.orchestrate.detect_workflow", return_value=_FAKE_WF_MODE)
    def test_status_no_slug_ok(self, mock_wf, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["status"]) == 0

    def test_ingest_nonexistent_returns_1(self, env):
        _, _, _, _, _, main_fn, *_ = _import_orchestrate()
        assert main_fn(["ingest", "/nonexistent.txt"]) == 1
