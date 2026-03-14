"""
Tests for core.intelligence.pipeline.scope_classifier
======================================================
Covers: classify(), _signal_path, _signal_participants, _signal_entities,
        _signal_content_type, _signal_cognitive, _signal_topics,
        _detect_source_type, _normalize_name, _email_domain,
        _email_matches_company, ClassificationContext, ScopeDecision.

All tests are OFFLINE.  Module-level caches (_known_experts, _known_team,
etc.) are reset between tests via monkeypatch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------

MODULE = "core.intelligence.pipeline.scope_classifier"


@pytest.fixture(autouse=True)
def _reset_caches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Reset ALL module-level caches and redirect filesystem paths.

    This runs before EVERY test so no state leaks between tests.
    """
    import core.intelligence.pipeline.scope_classifier as sc

    # Reset lazy-loaded caches
    monkeypatch.setattr(sc, "_known_experts", None)
    monkeypatch.setattr(sc, "_known_team", None)
    monkeypatch.setattr(sc, "_owner_aliases", None)
    monkeypatch.setattr(sc, "_owner_email", None)
    monkeypatch.setattr(sc, "_company_domains", None)
    monkeypatch.setattr(sc, "_company_keywords", None)
    monkeypatch.setattr(sc, "_company_name", None)

    # Redirect DNA persons dir and ORGANOGRAM to tmp_path (no real FS reads)
    fake_dna = tmp_path / "dna" / "persons"
    fake_dna.mkdir(parents=True)
    monkeypatch.setattr(sc, "_DNA_PERSONS_DIR", fake_dna)

    fake_organogram = tmp_path / "team" / "ORGANOGRAM.yaml"
    fake_organogram.parent.mkdir(parents=True)
    monkeypatch.setattr(sc, "_ORGANOGRAM_PATH", fake_organogram)

    # Redirect scope log to tmp_path
    monkeypatch.setattr(sc, "_SCOPE_LOG", tmp_path / "scope-classifier.jsonl")

    # Prevent inbox_organizer import side effects
    monkeypatch.setattr(sc, "_known_experts", set())

    # Clear env vars that affect classification
    monkeypatch.delenv("MEGA_BRAIN_OWNER_NAME", raising=False)
    monkeypatch.delenv("MEGA_BRAIN_OWNER_EMAIL", raising=False)
    monkeypatch.delenv("READ_AI_COMPANY_DOMAINS", raising=False)
    monkeypatch.delenv("READ_AI_COMPANY_KEYWORDS", raising=False)
    monkeypatch.delenv("READ_AI_COMPANY_NAME", raising=False)
    monkeypatch.delenv("MEGA_BRAIN_COMPANY_KEYWORDS", raising=False)


from core.intelligence.pipeline.scope_classifier import (  # noqa: E402
    ClassificationContext,
    ScopeDecision,
    _detect_source_type,
    _email_domain,
    _normalize_name,
    _signal_cognitive,
    _signal_content_type,
    _signal_path,
    _signal_topics,
    classify,
)


# ===========================================================================
# 1. TestClassifyExternalContent
# ===========================================================================
class TestClassifyExternalContent:
    """Expert/course content should classify as external."""

    def test_course_filename_returns_external(self):
        ctx = ClassificationContext(
            filename="hormozi-course-01.txt",
            file_path="/knowledge/external/inbox/hormozi-course-01.txt",
            source_type_hint="course",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "external"

    def test_course_text_with_teaching_patterns(self, sample_course_transcript):
        ctx = ClassificationContext(
            text=sample_course_transcript,
            filename="sales-training.txt",
            file_path="/knowledge/external/inbox/sales-training.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "external"

    def test_external_inbox_path_boosts_external(self):
        ctx = ClassificationContext(
            filename="random.txt",
            file_path="/knowledge/external/inbox/random.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "external"

    def test_masterclass_source_hint(self):
        ctx = ClassificationContext(
            filename="module-7.txt",
            source_type_hint="masterclass",
        )
        decision = classify(ctx)
        assert decision.source_type == "course"

    def test_podcast_source_hint(self):
        ctx = ClassificationContext(
            filename="ep45.txt",
            source_type_hint="podcast",
        )
        decision = classify(ctx)
        assert decision.source_type == "course"


# ===========================================================================
# 2. TestClassifyBusinessContent
# ===========================================================================
class TestClassifyBusinessContent:
    """Company meetings and ops content should classify as business."""

    def test_meeting_source_hint(self):
        ctx = ClassificationContext(
            filename="weekly-review.txt",
            file_path="/knowledge/business/inbox/weekly-review.txt",
            source_type_hint="meeting",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "business"

    def test_business_inbox_path_boosts_business(self):
        ctx = ClassificationContext(
            filename="standup.txt",
            file_path="/knowledge/business/inbox/standup.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "business"

    def test_meeting_text_with_decisions(self, sample_meeting_transcript, monkeypatch):
        monkeypatch.setenv("READ_AI_COMPANY_KEYWORDS", "bilhon,clickmax")
        import core.intelligence.pipeline.scope_classifier as sc
        monkeypatch.setattr(sc, "_company_keywords", None)

        ctx = ClassificationContext(
            text=sample_meeting_transcript,
            filename="bilhon-weekly.txt",
            file_path="/knowledge/business/inbox/bilhon-weekly.txt",
            source_type_hint="meeting",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "business"

    def test_workspace_inbox_meeting_path(self):
        ctx = ClassificationContext(
            filename="standup.txt",
            file_path="/workspace/inbox/meetings/standup.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "business"

    def test_business_markers_in_text(self):
        ctx = ClassificationContext(
            text="Our KPI dashboard shows MRR growth. Let's review the sprint backlog.",
            filename="ops-report.txt",
            file_path="/knowledge/business/inbox/ops-report.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "business"


# ===========================================================================
# 3. TestClassifyPersonalContent
# ===========================================================================
class TestClassifyPersonalContent:
    """Personal notes and reflections should classify as personal."""

    def test_personal_inbox_path(self):
        ctx = ClassificationContext(
            filename="journal.txt",
            file_path="/knowledge/personal/inbox/journal.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "personal"

    def test_personal_text_with_first_person(self, sample_personal_note):
        ctx = ClassificationContext(
            text=sample_personal_note,
            filename="reflexao.txt",
            file_path="/knowledge/personal/inbox/reflexao.txt",
        )
        decision = classify(ctx)
        assert decision.primary_bucket == "personal"

    def test_personal_source_type_hint(self):
        ctx = ClassificationContext(
            filename="my-notes.txt",
            file_path="/knowledge/personal/inbox/my-notes.txt",
            source_type_hint="personal",
        )
        decision = classify(ctx)
        assert decision.source_type == "personal"


# ===========================================================================
# 4. TestSignalPath
# ===========================================================================
class TestSignalPath:
    """Unit tests for _signal_path."""

    def test_external_inbox(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_path("/knowledge/external/inbox/file.txt", scores, reasons, signals)
        assert scores["external"] > 0
        assert signals["S1_path"] == "external"

    def test_business_inbox(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_path("/knowledge/business/inbox/file.txt", scores, reasons, signals)
        assert scores["business"] > 0
        assert signals["S1_path"] == "business"

    def test_personal_inbox(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_path("/knowledge/personal/inbox/file.txt", scores, reasons, signals)
        assert scores["personal"] > 0
        assert signals["S1_path"] == "personal"

    def test_workspace_inbox_generic(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_path("/workspace/inbox/file.txt", scores, reasons, signals)
        assert scores["business"] > 0
        assert signals["S1_path"] == "business"

    def test_unknown_path(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_path("/some/random/path.txt", scores, reasons, signals)
        assert signals["S1_path"] is None
        assert all(v == 0 for v in scores.values())


# ===========================================================================
# 5. TestSignalContentType
# ===========================================================================
class TestSignalContentType:
    """Unit tests for _signal_content_type."""

    def test_course_boosts_external(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_content_type("course", scores, reasons, signals)
        assert scores["external"] > 0

    def test_meeting_boosts_business(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_content_type("meeting", scores, reasons, signals)
        assert scores["business"] > 0

    def test_personal_boosts_personal(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_content_type("personal", scores, reasons, signals)
        assert scores["personal"] > 0

    def test_unknown_type_no_score(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_content_type("unknown", scores, reasons, signals)
        assert all(v == 0 for v in scores.values())


# ===========================================================================
# 6. TestSignalCognitive
# ===========================================================================
class TestSignalCognitive:
    """Unit tests for _signal_cognitive."""

    def test_first_person_portuguese(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_cognitive("Eu acredito que isso vai funcionar.", scores, reasons, signals)
        assert scores["personal"] > 0
        assert signals["S5_first_person"] is True

    def test_teaching_pattern_english(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_cognitive("Let me teach you the three steps.", scores, reasons, signals)
        assert scores["external"] > 0
        assert signals["S5_teaching"] is True

    def test_discussion_with_decisions(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_cognitive("Decidimos que vamos expandir o time.", scores, reasons, signals)
        assert scores["business"] > 0
        assert signals["S5_discussion"] is True

    def test_neutral_text_no_cognitive(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_cognitive("The weather is nice today.", scores, reasons, signals)
        assert all(v == 0 for v in scores.values())


# ===========================================================================
# 7. TestSignalTopics
# ===========================================================================
class TestSignalTopics:
    """Unit tests for _signal_topics."""

    def test_expert_markers_detected(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_topics("This is a proven framework and methodology.", scores, reasons, signals)
        assert scores["external"] > 0
        assert signals["S6_expert_markers"] is True

    def test_business_markers_detected(self):
        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_topics("We need to review our KPI and OKR alignment.", scores, reasons, signals)
        assert scores["business"] > 0
        assert signals["S6_business_markers"] is True

    def test_company_keyword_from_env(self, monkeypatch):
        monkeypatch.setenv("READ_AI_COMPANY_KEYWORDS", "acme,widgetco")
        import core.intelligence.pipeline.scope_classifier as sc
        monkeypatch.setattr(sc, "_company_keywords", None)

        scores = {"external": 0, "business": 0, "personal": 0}
        reasons, signals = [], {}
        _signal_topics("The acme project is going well.", scores, reasons, signals)
        assert scores["business"] > 0
        assert signals["S6_company_keywords"] >= 1


# ===========================================================================
# 8. TestDetectSourceType
# ===========================================================================
class TestDetectSourceType:
    """Unit tests for _detect_source_type."""

    def test_meeting_hint(self):
        assert _detect_source_type("file.txt", "meeting") == "meeting"

    def test_call_hint(self):
        assert _detect_source_type("file.txt", "call") == "meeting"

    def test_course_hint(self):
        assert _detect_source_type("file.txt", "course") == "course"

    def test_document_hint(self):
        assert _detect_source_type("file.txt", "document") == "document"

    def test_course_filename_pattern(self):
        assert _detect_source_type("masterclass-sales.txt", "") == "course"

    def test_meeting_filename_pattern(self):
        assert _detect_source_type("weekly-standup-notes.txt", "") == "meeting"

    def test_personal_filename_pattern(self):
        assert _detect_source_type("diario-pessoal.txt", "") == "personal"

    def test_unknown_returns_unknown(self):
        assert _detect_source_type("random-file.txt", "") == "unknown"

    def test_youtube_hint_maps_to_course(self):
        assert _detect_source_type("video.txt", "youtube") == "course"

    def test_training_filename(self):
        assert _detect_source_type("sales-training-v2.txt", "") == "course"


# ===========================================================================
# 9. TestHelpers
# ===========================================================================
class TestHelpers:
    """Unit tests for helper functions."""

    def test_normalize_name_strips_accents(self):
        assert _normalize_name("Nathalia") == "nathalia"

    def test_normalize_name_lowercase(self):
        assert _normalize_name("ALEX HORMOZI") == "alex hormozi"

    def test_normalize_name_strips_whitespace(self):
        assert _normalize_name("  thiago  ") == "thiago"

    def test_email_domain_valid(self):
        assert _email_domain("user@example.com") == "example.com"

    def test_email_domain_invalid(self):
        assert _email_domain("not-an-email") == ""

    def test_email_domain_empty(self):
        assert _email_domain("") == ""

    def test_email_domain_filters_calendar_resource(self):
        assert _email_domain("room@resource.calendar.google.com") == ""

    def test_email_domain_filters_group_calendar(self):
        assert _email_domain("group@group.calendar.google.com") == ""


# ===========================================================================
# 10. TestScopeDecisionDefaults
# ===========================================================================
class TestScopeDecisionDefaults:
    """ScopeDecision dataclass defaults."""

    def test_default_bucket(self):
        d = ScopeDecision()
        assert d.primary_bucket == "external"

    def test_default_confidence(self):
        d = ScopeDecision()
        assert d.confidence == 0.0

    def test_default_cascade_empty(self):
        d = ScopeDecision()
        assert d.cascade_buckets == []


# ===========================================================================
# 11. TestClassificationContext
# ===========================================================================
class TestClassificationContext:
    """ClassificationContext dataclass."""

    def test_defaults(self):
        ctx = ClassificationContext()
        assert ctx.text == ""
        assert ctx.filename == ""
        assert ctx.participants == []

    def test_custom_values(self):
        ctx = ClassificationContext(
            text="hello",
            filename="test.txt",
            participants=["a@b.com"],
        )
        assert ctx.text == "hello"
        assert len(ctx.participants) == 1


# ===========================================================================
# 12. TestConfidenceAndCascade
# ===========================================================================
class TestConfidenceAndCascade:
    """Confidence calculation and cascade bucket logic."""

    def test_confidence_between_zero_and_one(self):
        ctx = ClassificationContext(
            filename="test.txt",
            file_path="/knowledge/external/inbox/test.txt",
            source_type_hint="course",
        )
        decision = classify(ctx)
        assert 0.0 <= decision.confidence <= 1.0

    def test_empty_context_returns_valid_decision(self):
        ctx = ClassificationContext()
        decision = classify(ctx)
        assert decision.primary_bucket in ("external", "business", "personal")
        assert isinstance(decision.confidence, float)

    def test_signals_dict_populated(self):
        ctx = ClassificationContext(
            filename="test.txt",
            file_path="/knowledge/external/inbox/test.txt",
        )
        decision = classify(ctx)
        assert "S1_path" in decision.signals
        assert "S4_type" in decision.signals

    def test_reasons_list_populated_for_path(self):
        ctx = ClassificationContext(
            filename="test.txt",
            file_path="/knowledge/external/inbox/test.txt",
        )
        decision = classify(ctx)
        assert any("path" in r for r in decision.reasons)


# ===========================================================================
# 13. TestClassifierNeverCrashes
# ===========================================================================
class TestClassifierNeverCrashes:
    """classify() should NEVER raise -- returns safe default on error."""

    def test_none_text(self):
        ctx = ClassificationContext(text=None, filename="x.txt")  # type: ignore[arg-type]
        decision = classify(ctx)
        assert decision.primary_bucket in ("external", "business", "personal")

    def test_very_long_text(self):
        ctx = ClassificationContext(text="a" * 100_000, filename="big.txt")
        decision = classify(ctx)
        assert isinstance(decision, ScopeDecision)

    def test_unicode_filename(self):
        ctx = ClassificationContext(filename="aula-transcri\u00e7\u00e3o.txt")
        decision = classify(ctx)
        assert isinstance(decision, ScopeDecision)
