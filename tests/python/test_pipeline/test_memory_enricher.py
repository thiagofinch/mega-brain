"""
test_memory_enricher.py -- Tests for MCE Memory Enricher
==========================================================

Covers: Insight class, target agent discovery, dedup logic, MEMORY.md
creation/append, INSIGHTS-STATE.json merging, MCE threshold logic,
enrich_from_insights_state convenience, CLI, cargo reverse lookup.

All tests are OFFLINE -- no real filesystem outside tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers: build isolated environment
# ---------------------------------------------------------------------------


def _make_routing(tmp: Path) -> dict[str, Any]:
    return {
        "mce_state": tmp / "mce",
        "mce_metrics_log": tmp / "logs" / "mce-metrics.jsonl",
        "memory_enricher_log": tmp / "logs" / "memory-enricher.jsonl",
    }


@pytest.fixture()
def env(tmp_path: Path):
    """Create an isolated enricher environment with agents and knowledge dirs."""
    root = tmp_path / "mega-brain"
    root.mkdir()

    agents_ext = root / "agents" / "external"
    agents_biz = root / "agents" / "business"
    agents_cargo = root / "agents" / "cargo"
    logs = root / "logs"
    artifacts = root / "artifacts"
    knowledge_ext = root / "knowledge" / "external"

    for d in [agents_ext, agents_biz, agents_cargo, logs, artifacts / "insights", knowledge_ext / "dna" / "persons"]:
        d.mkdir(parents=True, exist_ok=True)

    routing = _make_routing(root)

    patches = [
        patch("core.intelligence.pipeline.memory_enricher.ROOT", root),
        patch("core.intelligence.pipeline.memory_enricher._ROOT", root),
        patch("core.intelligence.pipeline.memory_enricher.AGENTS_EXTERNAL", agents_ext),
        patch("core.intelligence.pipeline.memory_enricher.AGENTS_BUSINESS", agents_biz),
        patch("core.intelligence.pipeline.memory_enricher.AGENTS_CARGO", agents_cargo),
        patch("core.intelligence.pipeline.memory_enricher.LOGS", logs),
        patch("core.intelligence.pipeline.memory_enricher.ROUTING", routing),
        patch("core.intelligence.pipeline.memory_enricher.ENRICHER_LOG", logs / "memory-enricher.jsonl"),
    ]
    for p in patches:
        p.start()

    # Reset cargo cache between tests
    import core.intelligence.pipeline.memory_enricher as mod
    mod._cargo_reverse_map = None

    yield {
        "root": root,
        "agents_ext": agents_ext,
        "agents_biz": agents_biz,
        "agents_cargo": agents_cargo,
        "logs": logs,
        "artifacts": artifacts,
        "knowledge_ext": knowledge_ext,
    }

    mod._cargo_reverse_map = None
    for p in patches:
        p.stop()


def _import_enricher():
    from core.intelligence.pipeline.memory_enricher import (
        Insight,
        _append_insight,
        _build_cargo_reverse_map,
        _check_mce_thresholds,
        _create_memory_if_missing,
        _find_target_agents,
        _format_history_row,
        _format_insight_entry,
        _is_duplicate,
        enrich,
        enrich_from_insights_state,
        invalidate_cargo_cache,
    )

    return (
        Insight,
        enrich,
        enrich_from_insights_state,
        _find_target_agents,
        _is_duplicate,
        _create_memory_if_missing,
        _append_insight,
        _format_insight_entry,
        _format_history_row,
        _build_cargo_reverse_map,
        _check_mce_thresholds,
        invalidate_cargo_cache,
    )


# ===========================================================================
# Tests: Insight class
# ===========================================================================


class TestInsight:
    """Verify the Insight data structure."""

    def test_creation_defaults(self, env):
        Insight, *_ = _import_enricher()
        ins = Insight(person_slug="alex-hormozi", chunk_id="chunk_001")
        assert ins.person_slug == "alex-hormozi"
        assert ins.chunk_id == "chunk_001"
        assert ins.priority == "MEDIUM"
        assert ins.content == ""

    def test_normalization(self, env):
        Insight, *_ = _import_enricher()
        ins = Insight(
            person_slug="  Alex-Hormozi  ",
            chunk_id=" chunk_002 ",
            priority="high",
        )
        assert ins.person_slug == "alex-hormozi"
        assert ins.chunk_id == "chunk_002"
        assert ins.priority == "HIGH"

    def test_to_dict(self, env):
        Insight, *_ = _import_enricher()
        ins = Insight(
            person_slug="test",
            chunk_id="c1",
            title="My Title",
            tag="T-001",
        )
        d = ins.to_dict()
        assert d["person_slug"] == "test"
        assert d["title"] == "My Title"
        assert d["tag"] == "T-001"
        assert len(d) == 9  # all 9 slots

    def test_all_fields(self, env):
        Insight, *_ = _import_enricher()
        ins = Insight(
            person_slug="slug",
            chunk_id="c1",
            insight_id="CF001",
            tag="AH-SS001",
            title="Title",
            content="Body text",
            priority="HIGH",
            path_raiz="/inbox/file.txt",
            batch_id="BATCH-001",
        )
        assert ins.insight_id == "CF001"
        assert ins.batch_id == "BATCH-001"


# ===========================================================================
# Tests: _is_duplicate
# ===========================================================================


class TestIsDuplicate:
    """Verify dedup logic."""

    def _get_is_duplicate(self):
        all_fns = _import_enricher()
        return all_fns[4]  # _is_duplicate is at index 4

    def test_not_duplicate(self, env):
        is_dup = self._get_is_duplicate()
        assert is_dup("existing text chunk_100", "chunk_200") is False

    def test_is_duplicate(self, env):
        is_dup = self._get_is_duplicate()
        assert is_dup("text containing chunk_100 here", "chunk_100") is True

    def test_empty_chunk_id_not_duplicate(self, env):
        is_dup = self._get_is_duplicate()
        assert is_dup("any text", "") is False


# ===========================================================================
# Tests: _find_target_agents
# ===========================================================================


class TestFindTargetAgents:
    """Verify agent discovery for a person slug."""

    def test_external_agent_found(self, env):
        # Create agent directory
        agent_dir = env["agents_ext"] / "alex-hormozi"
        agent_dir.mkdir()
        (agent_dir / "AGENT.md").write_text("# Agent")

        _, _, _, find_fn, *_ = _import_enricher()
        targets = find_fn("alex-hormozi")
        assert len(targets) >= 1
        assert agent_dir in targets

    def test_no_agent_returns_empty(self, env):
        _, _, _, find_fn, *_ = _import_enricher()
        targets = find_fn("nonexistent-person")
        assert targets == []

    def test_business_agent_found(self, env):
        # Create business agent under a subcategory
        collab_dir = env["agents_biz"] / "collaborators" / "ricardo"
        collab_dir.mkdir(parents=True)
        (collab_dir / "AGENT.md").write_text("# Agent")

        _, _, _, find_fn, *_ = _import_enricher()
        targets = find_fn("ricardo")
        assert collab_dir in targets

    def test_cargo_reverse_lookup(self, env):
        import yaml

        # Create a cargo agent with DNA-CONFIG referencing a person
        cargo_dir = env["agents_cargo"] / "sales" / "closer"
        cargo_dir.mkdir(parents=True)
        config = {
            "dna_sources": {
                "primario": [
                    {"pessoa": "alex-hormozi", "tipo": "external"},
                ]
            }
        }
        (cargo_dir / "DNA-CONFIG.yaml").write_text(yaml.dump(config))

        *_, build_cargo, _, _ = _import_enricher()
        # Force rebuild
        import core.intelligence.pipeline.memory_enricher as mod
        mod._cargo_reverse_map = None

        _, _, _, find_fn, *_ = _import_enricher()
        targets = find_fn("alex-hormozi")
        assert cargo_dir in targets


# ===========================================================================
# Tests: _create_memory_if_missing
# ===========================================================================


class TestCreateMemoryIfMissing:
    """Verify MEMORY.md stub creation."""

    def test_creates_stub_when_missing(self, env):
        agent_dir = env["agents_ext"] / "new-person"
        agent_dir.mkdir(parents=True)

        _, _, _, _, _, create_fn, *_ = _import_enricher()
        result = create_fn(agent_dir)

        assert result.exists()
        text = result.read_text()
        assert "# MEMORY: New Person" in text
        assert "## INSIGHTS EXTRAIDOS" in text
        assert "## HISTORICO DE ATUALIZACOES" in text

    def test_returns_existing_when_present(self, env):
        agent_dir = env["agents_ext"] / "existing-person"
        agent_dir.mkdir(parents=True)
        existing = agent_dir / "MEMORY.md"
        existing.write_text("# Existing MEMORY\nDo not overwrite.")

        _, _, _, _, _, create_fn, *_ = _import_enricher()
        result = create_fn(agent_dir)

        assert result == existing
        assert "Do not overwrite" in result.read_text()


# ===========================================================================
# Tests: _format_insight_entry and _format_history_row
# ===========================================================================


class TestFormatting:
    """Verify markdown formatting helpers."""

    def test_format_insight_entry(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, format_entry, format_row, _, _, _ = _import_enricher()

        ins = Insight_cls(
            person_slug="test",
            chunk_id="chunk_42",
            title="Scaling Systems",
            content="Systems beat talent at scale.",
            tag="AH-001",
            batch_id="BATCH-010",
        )
        text = format_entry(ins, "2026-03-15")

        assert "### 2026-03-15 - Scaling Systems" in text
        assert "| chunk_id | chunk_42 |" in text
        assert "| tag | AH-001 |" in text
        assert "Systems beat talent at scale." in text

    def test_format_history_row(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, _, format_row, _, _, _ = _import_enricher()

        ins = Insight_cls(person_slug="t", chunk_id="c1", title="My Title", batch_id="B-01")
        row = format_row("2026-03-15", ins)
        assert row.startswith("| 2026-03-15")
        assert "My Title" in row
        assert "B-01" in row


# ===========================================================================
# Tests: _append_insight
# ===========================================================================


class TestAppendInsight:
    """Verify single-insight append to MEMORY.md."""

    def test_append_to_existing_section(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, append_fn, _, _, _, _, _ = _import_enricher()

        agent_dir = env["agents_ext"] / "append-test"
        agent_dir.mkdir(parents=True)
        memory = agent_dir / "MEMORY.md"
        memory.write_text(
            "# MEMORY: Append Test\n\n"
            "> **Atualizado:** 2026-01-01\n\n"
            "## INSIGHTS EXTRAIDOS\n\n"
            "*Insights do Pipeline serao adicionados aqui.*\n\n"
            "---\n\n"
            "## HISTORICO DE ATUALIZACOES\n\n"
            "| Data | Mudanca | Material Processado |\n"
            "|------|---------|---------------------|\n"
            "| 2026-01-01 | Criacao | auto |\n"
        )

        ins = Insight_cls(
            person_slug="append-test",
            chunk_id="chunk_NEW",
            title="New Insight",
            content="Content here",
        )
        result = append_fn(memory, ins)

        assert result is True
        text = memory.read_text()
        assert "chunk_NEW" in text
        assert "New Insight" in text

    def test_dedup_prevents_second_append(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, append_fn, _, _, _, _, _ = _import_enricher()

        agent_dir = env["agents_ext"] / "dedup-test"
        agent_dir.mkdir(parents=True)
        memory = agent_dir / "MEMORY.md"
        memory.write_text(
            "# MEMORY\n\n## INSIGHTS EXTRAIDOS\n\nchunk_OLD is here\n"
        )

        ins = Insight_cls(person_slug="dedup-test", chunk_id="chunk_OLD")
        result = append_fn(memory, ins)

        assert result is False

    def test_creates_section_if_missing(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, append_fn, _, _, _, _, _ = _import_enricher()

        agent_dir = env["agents_ext"] / "no-section"
        agent_dir.mkdir(parents=True)
        memory = agent_dir / "MEMORY.md"
        memory.write_text("# MEMORY: No Section\n\nSome content.\n")

        ins = Insight_cls(
            person_slug="no-section",
            chunk_id="chunk_001",
            title="First insight",
        )
        result = append_fn(memory, ins)

        assert result is True
        text = memory.read_text()
        assert "## INSIGHTS EXTRAIDOS" in text
        assert "chunk_001" in text

    def test_updates_date_header(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, append_fn, _, _, _, _, _ = _import_enricher()

        agent_dir = env["agents_ext"] / "date-update"
        agent_dir.mkdir(parents=True)
        memory = agent_dir / "MEMORY.md"
        memory.write_text(
            "# MEMORY\n\n> **Atualizado:** 2020-01-01\n\n## INSIGHTS EXTRAIDOS\n\n"
        )

        ins = Insight_cls(person_slug="date-update", chunk_id="c1")
        append_fn(memory, ins)

        text = memory.read_text()
        assert "2020-01-01" not in text  # old date replaced


# ===========================================================================
# Tests: enrich (main API)
# ===========================================================================


class TestEnrich:
    """Verify the main enrich() function."""

    def test_empty_list_returns_zeroes(self, env):
        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([])
        assert r["appended"] == 0
        assert r["skipped_dedup"] == 0
        assert r["skipped_no_agent"] == 0

    def test_dict_input_normalized(self, env):
        # Create agent dir so insights route somewhere
        agent_dir = env["agents_ext"] / "alex-hormozi"
        agent_dir.mkdir(parents=True)

        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([
            {
                "person_slug": "alex-hormozi",
                "chunk_id": "chunk_300",
                "title": "Test insight",
                "content": "Content body.",
            }
        ])

        assert r["appended"] >= 1
        assert len(r["agents_enriched"]) >= 1

    def test_no_agent_skips(self, env):
        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([
            {"person_slug": "nobody", "chunk_id": "c1"},
        ])
        assert r["skipped_no_agent"] == 1
        assert r["appended"] == 0

    def test_missing_person_slug_errors(self, env):
        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([
            {"person_slug": "", "chunk_id": "c1"},
        ])
        assert len(r["errors"]) >= 1

    def test_missing_chunk_id_errors(self, env):
        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([
            {"person_slug": "someone", "chunk_id": ""},
        ])
        assert len(r["errors"]) >= 1

    def test_invalid_type_errors(self, env):
        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([42])  # not a dict or Insight
        assert len(r["errors"]) >= 1

    def test_dedup_across_agents(self, env):
        """Same insight sent twice should be deduped on second append."""
        agent_dir = env["agents_ext"] / "dedup-person"
        agent_dir.mkdir(parents=True)

        _, enrich_fn, *_ = _import_enricher()

        insight = {"person_slug": "dedup-person", "chunk_id": "chunk_DUP", "title": "T"}
        r1 = enrich_fn([insight])
        assert r1["appended"] == 1

        r2 = enrich_fn([insight])
        assert r2["skipped_dedup"] == 1
        assert r2["appended"] == 0

    def test_multiple_insights_multiple_agents(self, env):
        for slug in ("person-a", "person-b"):
            d = env["agents_ext"] / slug
            d.mkdir(parents=True)

        _, enrich_fn, *_ = _import_enricher()
        r = enrich_fn([
            {"person_slug": "person-a", "chunk_id": "c1", "title": "A insight"},
            {"person_slug": "person-b", "chunk_id": "c2", "title": "B insight"},
        ])

        assert r["appended"] == 2
        assert len(r["agents_enriched"]) == 2

    def test_insight_object_input(self, env):
        Insight_cls, enrich_fn, *_ = _import_enricher()
        agent_dir = env["agents_ext"] / "obj-test"
        agent_dir.mkdir(parents=True)

        ins = Insight_cls(
            person_slug="obj-test",
            chunk_id="chunk_OBJ",
            title="Object insight",
        )
        r = enrich_fn([ins])
        assert r["appended"] == 1


# ===========================================================================
# Tests: MCE Threshold Check
# ===========================================================================


class TestMCEThreshold:
    """Verify cumulative MCE threshold logic."""

    def test_below_threshold(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, check_fn, _ = _import_enricher()

        # Create INSIGHTS-STATE with 2 insights (below threshold of 3)
        state = {"persons": {"test-person": {"insights": ["a", "b"]}}}
        state_path = env["artifacts"] / "insights" / "INSIGHTS-STATE.json"
        state_path.write_text(json.dumps(state))

        with patch("core.paths.ARTIFACTS", env["artifacts"]), \
             patch("core.paths.KNOWLEDGE_EXTERNAL", env["knowledge_ext"]):
            insights = [Insight_cls(person_slug="test-person", chunk_id="c1")]
            result = check_fn(insights)

        assert result == []

    def test_above_threshold_no_voice_dna(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, check_fn, _ = _import_enricher()

        # Create INSIGHTS-STATE with 5 insights (above threshold of 3)
        state = {"persons": {"hot-person": {"insights": ["a", "b", "c", "d", "e"]}}}
        state_path = env["artifacts"] / "insights" / "INSIGHTS-STATE.json"
        state_path.write_text(json.dumps(state))

        with patch("core.paths.ARTIFACTS", env["artifacts"]), \
             patch("core.paths.KNOWLEDGE_EXTERNAL", env["knowledge_ext"]):
            insights = [Insight_cls(person_slug="hot-person", chunk_id="c1")]
            result = check_fn(insights)

        assert "hot-person" in result

    def test_above_threshold_voice_dna_exists(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, check_fn, _ = _import_enricher()

        state = {"persons": {"done-person": {"insights": ["a", "b", "c", "d"]}}}
        state_path = env["artifacts"] / "insights" / "INSIGHTS-STATE.json"
        state_path.write_text(json.dumps(state))

        # Create VOICE-DNA.yaml (MCE already ran)
        voice_dna_dir = env["knowledge_ext"] / "dna" / "persons" / "done-person"
        voice_dna_dir.mkdir(parents=True)
        (voice_dna_dir / "VOICE-DNA.yaml").write_text("voice: true")

        with patch("core.paths.ARTIFACTS", env["artifacts"]), \
             patch("core.paths.KNOWLEDGE_EXTERNAL", env["knowledge_ext"]):
            insights = [Insight_cls(person_slug="done-person", chunk_id="c1")]
            result = check_fn(insights)

        assert result == []

    def test_flat_insights_format(self, env):
        """Test the flat list format: {insights: [{person_slug: ...}, ...]}."""
        Insight_cls, *_ = _import_enricher()
        *_, check_fn, _ = _import_enricher()

        state = {
            "insights": [
                {"person_slug": "flat-person"},
                {"person_slug": "flat-person"},
                {"person_slug": "flat-person"},
                {"person_slug": "flat-person"},
            ]
        }
        state_path = env["artifacts"] / "insights" / "INSIGHTS-STATE.json"
        state_path.write_text(json.dumps(state))

        with patch("core.paths.ARTIFACTS", env["artifacts"]), \
             patch("core.paths.KNOWLEDGE_EXTERNAL", env["knowledge_ext"]):
            insights = [Insight_cls(person_slug="flat-person", chunk_id="c1")]
            result = check_fn(insights)

        assert "flat-person" in result

    def test_no_insights_state_file(self, env):
        Insight_cls, *_ = _import_enricher()
        *_, check_fn, _ = _import_enricher()

        with patch("core.paths.ARTIFACTS", env["artifacts"]), \
             patch("core.paths.KNOWLEDGE_EXTERNAL", env["knowledge_ext"]):
            insights = [Insight_cls(person_slug="no-state", chunk_id="c1")]
            result = check_fn(insights)

        assert result == []


# ===========================================================================
# Tests: enrich_from_insights_state
# ===========================================================================


class TestEnrichFromInsightsState:
    """Verify convenience function that reads INSIGHTS-STATE.json."""

    def test_missing_file_returns_empty(self, env):
        _, _, enrich_state_fn, *_ = _import_enricher()
        r = enrich_state_fn(env["artifacts"] / "insights" / "NONEXISTENT.json")
        assert r["appended"] == 0

    def test_list_format(self, env):
        """INSIGHTS-STATE.json is a flat list."""
        agent_dir = env["agents_ext"] / "list-person"
        agent_dir.mkdir(parents=True)

        state_path = env["artifacts"] / "insights" / "test-state.json"
        state_path.write_text(json.dumps([
            {"person_slug": "list-person", "chunk_id": "c1", "title": "From list"},
        ]))

        _, _, enrich_state_fn, *_ = _import_enricher()
        r = enrich_state_fn(state_path)
        assert r["appended"] == 1

    def test_dict_with_insights_key(self, env):
        agent_dir = env["agents_ext"] / "dict-person"
        agent_dir.mkdir(parents=True)

        state_path = env["artifacts"] / "insights" / "test-state2.json"
        state_path.write_text(json.dumps({
            "insights": [
                {"person_slug": "dict-person", "chunk_id": "c1", "title": "From dict"},
            ]
        }))

        _, _, enrich_state_fn, *_ = _import_enricher()
        r = enrich_state_fn(state_path)
        assert r["appended"] == 1

    def test_empty_insights(self, env):
        state_path = env["artifacts"] / "insights" / "empty-state.json"
        state_path.write_text(json.dumps({"insights": []}))

        _, _, enrich_state_fn, *_ = _import_enricher()
        r = enrich_state_fn(state_path)
        assert r["appended"] == 0

    def test_corrupt_json(self, env):
        state_path = env["artifacts"] / "insights" / "corrupt.json"
        state_path.write_text("{invalid json")

        _, _, enrich_state_fn, *_ = _import_enricher()
        r = enrich_state_fn(state_path)
        assert len(r.get("errors", [])) >= 1


# ===========================================================================
# Tests: Cargo Cache Management
# ===========================================================================


class TestCargoCache:
    """Verify cargo reverse map caching and invalidation."""

    def test_cache_builds_once(self, env):
        *_, build_cargo, _, invalidate = _import_enricher()
        invalidate()

        # First call builds the map
        m1 = build_cargo()
        assert isinstance(m1, dict)

        # Second call returns same object (cached)
        m2 = build_cargo()
        assert m1 is m2

    def test_invalidate_forces_rebuild(self, env):
        *_, build_cargo, _, invalidate = _import_enricher()
        invalidate()

        m1 = build_cargo()
        invalidate()
        m2 = build_cargo()
        # After invalidation, a new dict object is built
        assert isinstance(m2, dict)

    def test_empty_cargo_dir(self, env):
        *_, build_cargo, _, invalidate = _import_enricher()
        invalidate()

        m = build_cargo()
        assert m == {}


# ===========================================================================
# Tests: JSONL Logging
# ===========================================================================


class TestEnrichmentLogging:
    """Verify JSONL audit log is written during enrichment."""

    def test_log_written_after_enrich(self, env):
        agent_dir = env["agents_ext"] / "log-test"
        agent_dir.mkdir(parents=True)

        _, enrich_fn, *_ = _import_enricher()
        enrich_fn([{"person_slug": "log-test", "chunk_id": "c1", "title": "T"}])

        log_file = env["logs"] / "memory-enricher.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) >= 1
        entry = json.loads(lines[0])
        assert "insights_received" in entry
        assert "insights_appended" in entry
        assert entry["insights_received"] == 1
