"""
Tests for core.intelligence.pipeline.agent_auto_creator
========================================================
Covers: slugify, count_all_person_insights, determine_bucket,
        get_agent_dir, generate_agent_skeleton, check_and_create_agent,
        scan_all_persons, log_creation.

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

MODULE = "core.intelligence.pipeline.agent_auto_creator"


@pytest.fixture(autouse=True)
def _patch_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all module-level paths to tmp_path."""
    import core.intelligence.pipeline.agent_auto_creator as aac

    agents_external = tmp_path / "agents" / "external"
    agents_business = tmp_path / "agents" / "business"
    artifacts = tmp_path / "artifacts"
    data = tmp_path / ".data"
    insights_path = artifacts / "insights" / "INSIGHTS-STATE.json"
    creations_log = data / "agent_memory" / "system" / "agent_creations.jsonl"

    agents_external.mkdir(parents=True)
    agents_business.mkdir(parents=True)
    (artifacts / "insights").mkdir(parents=True)
    creations_log.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(aac, "AGENTS_EXTERNAL", agents_external)
    monkeypatch.setattr(aac, "AGENTS_BUSINESS", agents_business)
    monkeypatch.setattr(aac, "ARTIFACTS", artifacts)
    monkeypatch.setattr(aac, "DATA", data)
    monkeypatch.setattr(aac, "ROOT", tmp_path)
    monkeypatch.setattr(aac, "INSIGHTS_STATE_PATH", insights_path)
    monkeypatch.setattr(aac, "AGENT_CREATIONS_LOG", creations_log)


from core.intelligence.pipeline.agent_auto_creator import (
    MCE_INSIGHT_THRESHOLD,
    check_and_create_agent,
    count_all_person_insights,
    determine_bucket,
    generate_agent_skeleton,
    get_agent_dir,
    scan_all_persons,
    slugify,
)

# ===========================================================================
# SLUGIFY TESTS
# ===========================================================================


class TestSlugify:
    def test_basic_name(self):
        assert slugify("Alex Hormozi") == "alex-hormozi"

    def test_single_word(self):
        assert slugify("Duarte") == "duarte"

    def test_accented_name(self):
        assert slugify("Pedro Valerio") == "pedro-valerio"

    def test_unicode_accents(self):
        assert slugify("Jose da Silva") == "jose-da-silva"

    def test_extra_spaces(self):
        assert slugify("  John   Doe  ") == "john-doe"

    def test_special_characters(self):
        assert slugify("O'Brien-Smith") == "o-brien-smith"

    def test_already_slug(self):
        assert slugify("alex-hormozi") == "alex-hormozi"


# ===========================================================================
# COUNT INSIGHTS TESTS
# ===========================================================================


def _make_state(
    categories_insights: dict | None = None,
    persons: dict | None = None,
    insights_list: list | None = None,
    behavioral_patterns: dict | None = None,
) -> dict:
    """Helper to build a minimal INSIGHTS-STATE structure."""
    state: dict = {}
    if categories_insights is not None:
        cats = {}
        for person_slug, count in categories_insights.items():
            cats[f"cat-{person_slug}"] = {
                "insights": [
                    {"id": f"{person_slug}-{i}", "source_person": person_slug}
                    for i in range(count)
                ]
            }
        state["categories"] = cats

    if persons is not None:
        state["persons"] = persons

    if insights_list is not None:
        state["insights"] = insights_list

    if behavioral_patterns is not None:
        state["behavioral_patterns"] = behavioral_patterns

    return state


class TestCountAllPersonInsights:
    def test_empty_state(self):
        counts = count_all_person_insights({})
        assert counts == {}

    def test_categories_only(self):
        state = _make_state(categories_insights={"alex-hormozi": 5, "cole-gordon": 2})
        counts = count_all_person_insights(state)
        assert counts["Alex Hormozi"] == 5
        assert counts["Cole Gordon"] == 2

    def test_persons_only(self):
        state = _make_state(persons={
            "Jordan Lee": [
                {"id": "JL-001", "insight": "test1"},
                {"id": "JL-002", "insight": "test2"},
            ],
        })
        counts = count_all_person_insights(state)
        assert counts["Jordan Lee"] == 2

    def test_persons_skips_meet_ids(self):
        state = _make_state(persons={
            "MEET-0026": [{"id": "M-001"}],
            "Jane Doe": [{"id": "JD-001"}],
        })
        counts = count_all_person_insights(state)
        assert "MEET-0026" not in counts
        assert counts["Jane Doe"] == 1

    def test_insights_list(self):
        state = _make_state(insights_list=[
            {"person": "Thiago Finch", "id": "TF-001"},
            {"person": "Thiago Finch", "id": "TF-002"},
            {"person": "Thiago Finch", "id": "TF-003"},
        ])
        counts = count_all_person_insights(state)
        assert counts["Thiago Finch"] == 3

    def test_behavioral_patterns(self):
        state = _make_state(behavioral_patterns={
            "thiago-finch": {
                "person": "Thiago Finch",
                "bucket": "business",
                "patterns": [{"p": 1}, {"p": 2}],
            }
        })
        counts = count_all_person_insights(state)
        assert counts["Thiago Finch"] == 2

    def test_cumulative_across_sources(self):
        """The key test: insights accumulate across ALL sources."""
        state = _make_state(
            categories_insights={"jane-doe": 2},
            persons={"Jane Doe": [{"id": "JD-P1"}]},
            insights_list=[{"person": "Jane Doe", "id": "JD-I1"}],
            behavioral_patterns={
                "jane-doe": {
                    "person": "Jane Doe",
                    "patterns": [{"p": 1}],
                }
            },
        )
        counts = count_all_person_insights(state)
        # 2 (categories) + 1 (persons) + 1 (insights) + 1 (behavioral) = 5
        assert counts["Jane Doe"] == 5

    def test_persons_empty_list_skipped(self):
        state = _make_state(persons={"Empty Person": []})
        counts = count_all_person_insights(state)
        # Empty list should not add to count
        assert counts.get("Empty Person", 0) == 0


# ===========================================================================
# DETERMINE BUCKET TESTS
# ===========================================================================


class TestDetermineBucket:
    def test_behavioral_patterns_business(self):
        state = _make_state(behavioral_patterns={
            "john-doe": {
                "person": "John Doe",
                "bucket": "business",
                "patterns": [],
            }
        })
        assert determine_bucket("John Doe", state) == "business"

    def test_behavioral_patterns_external(self):
        state = _make_state(behavioral_patterns={
            "guru": {
                "person": "Guru",
                "bucket": "external",
                "patterns": [],
            }
        })
        assert determine_bucket("Guru", state) == "external"

    def test_persons_scope_course(self):
        state = _make_state(persons={
            "Expert Person": [{"scope": "course", "corpus": "expert-person"}]
        })
        assert determine_bucket("Expert Person", state) == "external"

    def test_persons_scope_business(self):
        state = _make_state(persons={
            "Biz Person": [{"scope": "business", "corpus": "biz"}]
        })
        assert determine_bucket("Biz Person", state) == "business"

    def test_existing_external_agent_dir(self, tmp_path: Path):
        """If agent dir already exists in external, route to external."""
        import core.intelligence.pipeline.agent_auto_creator as aac
        (aac.AGENTS_EXTERNAL / "known-expert").mkdir(parents=True)
        state = _make_state()
        assert determine_bucket("Known Expert", state) == "external"

    def test_existing_business_agent_dir(self, tmp_path: Path):
        """If agent dir already exists in business, route to business."""
        import core.intelligence.pipeline.agent_auto_creator as aac
        (aac.AGENTS_BUSINESS / "collaborators" / "biz-guy").mkdir(parents=True)
        state = _make_state()
        assert determine_bucket("Biz Guy", state) == "business"

    def test_default_is_external(self):
        state = _make_state()
        assert determine_bucket("Unknown Person", state) == "external"


# ===========================================================================
# GET AGENT DIR TESTS
# ===========================================================================


class TestGetAgentDir:
    def test_external_bucket(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        result = get_agent_dir("John Doe", "external")
        assert result == aac.AGENTS_EXTERNAL / "john-doe"

    def test_business_bucket(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        result = get_agent_dir("Jane Smith", "business")
        assert result == aac.AGENTS_BUSINESS / "collaborators" / "jane-smith"


# ===========================================================================
# GENERATE SKELETON TESTS
# ===========================================================================


class TestGenerateAgentSkeleton:
    def test_contains_person_name(self):
        skeleton = generate_agent_skeleton("Jordan Lee", 45, "external")
        assert "JORDAN LEE" in skeleton
        assert "jordan-lee" in skeleton

    def test_contains_template_version(self):
        skeleton = generate_agent_skeleton("Test Person", 5, "external")
        assert "AGENT-MD-ULTRA-ROBUSTO-V3" in skeleton

    def test_external_layer(self):
        skeleton = generate_agent_skeleton("Expert", 10, "external")
        assert "layer: L3" in skeleton
        assert "Mind Clone" in skeleton

    def test_business_layer(self):
        skeleton = generate_agent_skeleton("Collaborator", 5, "business")
        assert "layer: L2" in skeleton
        assert "BUSINESS COLLABORATOR" in skeleton

    def test_insight_count_in_skeleton(self):
        skeleton = generate_agent_skeleton("Test", 42, "external")
        assert "42" in skeleton

    def test_has_dependencies_section(self):
        skeleton = generate_agent_skeleton("Test", 5, "external")
        assert "## DEPENDENCIES" in skeleton
        assert "READS" in skeleton
        assert "DEPENDS_ON" in skeleton

    def test_has_dashboard(self):
        skeleton = generate_agent_skeleton("Test", 5, "external")
        assert "DASHBOARD DE STATUS" in skeleton
        assert "PENDING" in skeleton

    def test_has_frontmatter(self):
        skeleton = generate_agent_skeleton("Test Person", 5, "external")
        assert "id: test-person" in skeleton
        assert 'version: "0.1.0"' in skeleton
        assert "auto_created: true" in skeleton


# ===========================================================================
# CHECK AND CREATE AGENT TESTS
# ===========================================================================


class TestCheckAndCreateAgent:
    def test_below_threshold_returns_skip(self):
        state = _make_state(persons={"Low Person": [{"id": "LP-001"}]})
        result = check_and_create_agent("Low Person", state=state)
        assert result["action"] == "skip"
        assert result["insight_count"] == 1

    def test_existing_agent_returns_noop(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        # Create existing agent
        agent_dir = aac.AGENTS_EXTERNAL / "expert-one"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text("existing")

        state = _make_state(persons={
            "Expert One": [{"id": f"E-{i}"} for i in range(5)]
        })
        result = check_and_create_agent("Expert One", state=state)
        assert result["action"] == "noop"

    def test_creates_agent_above_threshold(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        state = _make_state(persons={
            "New Expert": [
                {"id": "NE-001", "insight": "i1"},
                {"id": "NE-002", "insight": "i2"},
                {"id": "NE-003", "insight": "i3"},
            ]
        })
        result = check_and_create_agent("New Expert", state=state)
        assert result["action"] == "created"
        assert result["insight_count"] == 3
        assert result["bucket"] == "external"

        # Verify file was actually created
        agent_file = aac.AGENTS_EXTERNAL / "new-expert" / "AGENT.md"
        assert agent_file.exists()
        content = agent_file.read_text()
        assert "NEW EXPERT" in content
        assert "AGENT-MD-ULTRA-ROBUSTO-V3" in content

    def test_dry_run_does_not_create(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        state = _make_state(persons={
            "Dry Run Person": [{"id": f"DR-{i}"} for i in range(5)]
        })
        result = check_and_create_agent("Dry Run Person", state=state, dry_run=True)
        assert result["action"] == "would_create"

        # Verify file was NOT created
        agent_file = aac.AGENTS_EXTERNAL / "dry-run-person" / "AGENT.md"
        assert not agent_file.exists()

    def test_creation_is_idempotent(self, tmp_path: Path):
        """Running twice on same person should create then noop."""
        state = _make_state(persons={
            "Idempotent Person": [{"id": f"IP-{i}"} for i in range(4)]
        })
        result1 = check_and_create_agent("Idempotent Person", state=state)
        assert result1["action"] == "created"

        result2 = check_and_create_agent("Idempotent Person", state=state)
        assert result2["action"] == "noop"

    def test_business_bucket_routing(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        state = _make_state(
            persons={
                "Biz Collaborator": [{"id": f"BC-{i}"} for i in range(3)]
            },
            behavioral_patterns={
                "biz-collaborator": {
                    "person": "Biz Collaborator",
                    "bucket": "business",
                    "patterns": [],
                }
            },
        )
        result = check_and_create_agent("Biz Collaborator", state=state)
        assert result["action"] == "created"
        assert result["bucket"] == "business"

        agent_file = aac.AGENTS_BUSINESS / "collaborators" / "biz-collaborator" / "AGENT.md"
        assert agent_file.exists()


# ===========================================================================
# LOG CREATION TESTS
# ===========================================================================


class TestLogCreation:
    def test_logs_to_jsonl(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        state = _make_state(persons={
            "Log Test": [{"id": f"LT-{i}"} for i in range(4)]
        })
        check_and_create_agent("Log Test", state=state)

        log_file = aac.AGENT_CREATIONS_LOG
        assert log_file.exists()

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["event"] == "agent_auto_created"
        assert entry["person"] == "Log Test"
        assert entry["slug"] == "log-test"
        assert entry["bucket"] == "external"
        assert entry["insight_count"] == 4
        assert entry["trigger"] == "mce_threshold"
        assert entry["threshold"] == MCE_INSIGHT_THRESHOLD

    def test_log_appends(self, tmp_path: Path):
        """Multiple creations append to the same log file."""
        import core.intelligence.pipeline.agent_auto_creator as aac
        state = _make_state(persons={
            "Person A": [{"id": f"PA-{i}"} for i in range(3)],
            "Person B": [{"id": f"PB-{i}"} for i in range(4)],
        })
        check_and_create_agent("Person A", state=state)
        check_and_create_agent("Person B", state=state)

        log_file = aac.AGENT_CREATIONS_LOG
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2


# ===========================================================================
# SCAN ALL PERSONS TESTS
# ===========================================================================


class TestScanAllPersons:
    def test_scan_creates_qualifying_agents(self, tmp_path: Path):
        state = _make_state(persons={
            "Expert A": [{"id": f"EA-{i}"} for i in range(5)],
            "Expert B": [{"id": f"EB-{i}"} for i in range(3)],
            "MEET-0001": [{"id": "M-001"}],
            "Below": [{"id": "BL-001"}],
        })
        results = scan_all_persons(state=state)

        created = [r for r in results if r["action"] == "created"]
        skipped = [r for r in results if r["action"] == "skip"]

        assert len(created) == 2  # Expert A and Expert B
        assert len(skipped) == 1  # Below
        # MEET-0001 should not appear at all
        assert not any(r["person"] == "MEET-0001" for r in results)

    def test_scan_skips_existing(self, tmp_path: Path):
        import core.intelligence.pipeline.agent_auto_creator as aac
        # Pre-create an agent
        (aac.AGENTS_EXTERNAL / "preexisting" / "AGENT.md").parent.mkdir(parents=True)
        (aac.AGENTS_EXTERNAL / "preexisting" / "AGENT.md").write_text("exists")

        state = _make_state(persons={
            "Preexisting": [{"id": f"PE-{i}"} for i in range(10)],
        })
        results = scan_all_persons(state=state)
        assert results[0]["action"] == "noop"

    def test_scan_dry_run(self, tmp_path: Path):
        state = _make_state(persons={
            "Dry Expert": [{"id": f"DE-{i}"} for i in range(4)],
        })
        results = scan_all_persons(state=state, dry_run=True)
        assert results[0]["action"] == "would_create"

    def test_scan_sorted_by_count_descending(self, tmp_path: Path):
        state = _make_state(persons={
            "Low": [{"id": f"L-{i}"} for i in range(3)],
            "High": [{"id": f"H-{i}"} for i in range(10)],
            "Mid": [{"id": f"M-{i}"} for i in range(6)],
        })
        results = scan_all_persons(state=state)
        counts = [r["insight_count"] for r in results]
        assert counts == sorted(counts, reverse=True)


# ===========================================================================
# THRESHOLD BOUNDARY TESTS
# ===========================================================================


class TestThresholdBoundary:
    def test_exactly_at_threshold(self, tmp_path: Path):
        """Exactly 3 insights should trigger creation."""
        state = _make_state(persons={
            "Boundary": [{"id": f"B-{i}"} for i in range(MCE_INSIGHT_THRESHOLD)]
        })
        result = check_and_create_agent("Boundary", state=state)
        assert result["action"] == "created"

    def test_one_below_threshold(self):
        """2 insights should NOT trigger creation."""
        state = _make_state(persons={
            "Almost": [{"id": f"A-{i}"} for i in range(MCE_INSIGHT_THRESHOLD - 1)]
        })
        result = check_and_create_agent("Almost", state=state)
        assert result["action"] == "skip"

    def test_zero_insights(self):
        result = check_and_create_agent("Nobody", state={})
        assert result["action"] == "skip"
        assert result["insight_count"] == 0
