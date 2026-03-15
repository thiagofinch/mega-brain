"""
Tests for core.intelligence.pipeline.inbox_organizer
=====================================================
Covers: detect_entity, detect_content_type, classify_file,
        _is_already_organized, organize_inbox, _slugify,
        entity alias resolution, content type edge cases,
        entity detection from directory context.

All tests are offline (no network calls). Filesystem isolation
is achieved through tmp_path fixtures and monkeypatching the
module-level constants BUCKET_INBOXES, DNA_PERSONS_DIR, and LOGS.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MODULE = "core.intelligence.pipeline.inbox_organizer"


# Test-only aliases — these are NOT real names; they simulate the user's config.
_TEST_ENTITY_ALIASES: dict[str, str] = {
    "hormozi": "alex-hormozi",
    "alex hormozi": "alex-hormozi",
    "cole": "cole-gordon",
    "cole gordon": "cole-gordon",
    "acme-co": "acme-co",
    "acme": "acme-co",
    "outsider": "outsider",
    "otodus": "outsider",
    "outsider 2.0": "outsider",
    "otodus system": "outsider",
    "finch": "founder-name",
    "krueger": "collaborator-a",
    "acme-brand": "acme-co",
    "billion": "acme-co",
}


@pytest.fixture()
def _patch_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all module-level paths to tmp_path so tests never touch the real FS."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    logs = tmp_path / "logs"
    logs.mkdir()

    dna = tmp_path / "dna" / "persons"
    dna.mkdir(parents=True)

    monkeypatch.setattr(
        f"{MODULE}.BUCKET_INBOXES",
        {"external": inbox, "business": inbox, "personal": inbox},
    )
    monkeypatch.setattr(f"{MODULE}.DNA_PERSONS_DIR", dna)
    monkeypatch.setattr(f"{MODULE}.LOGS", logs)
    monkeypatch.setattr(f"{MODULE}.ENTITY_ALIASES", dict(_TEST_ENTITY_ALIASES))

    return inbox, logs, dna


@pytest.fixture()
def organized_inbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Full-cycle fixture: inbox + logs + a known DNA entity (alex-hormozi)."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    logs = tmp_path / "logs"
    logs.mkdir()

    # Create a fake DNA persons dir with one known entity
    dna = tmp_path / "dna" / "persons" / "alex-hormozi"
    dna.mkdir(parents=True)

    monkeypatch.setattr(
        f"{MODULE}.BUCKET_INBOXES",
        {"external": inbox, "business": inbox, "personal": inbox},
    )
    monkeypatch.setattr(f"{MODULE}.DNA_PERSONS_DIR", tmp_path / "dna" / "persons")
    monkeypatch.setattr(f"{MODULE}.LOGS", logs)

    return inbox, logs


# ---------------------------------------------------------------------------
# Imports (after fixtures are defined so module loads with real paths first)
# ---------------------------------------------------------------------------
from core.intelligence.pipeline.inbox_organizer import (
    _is_already_organized,
    _slugify,
    classify_file,
    detect_content_type,
    detect_entity,
    organize_inbox,
)


# ===========================================================================
# 1. TestExternalYoutubeIngest
# ===========================================================================
class TestExternalYoutubeIngest:
    """YouTube files with URL fragments in filename."""

    def test_youtube_url_fragment_detected_as_youtube(self, _patch_paths):
        fp = Path("/inbox/How to Build AI [youtube.com_watch_v=abc].txt")
        assert detect_content_type(fp) == "youtube"

    def test_youtube_file_entity_unclassified(self, _patch_paths):
        fp = Path("/inbox/How to Build AI [youtube.com_watch_v=abc].txt")
        entity = detect_entity(fp)
        assert entity == "_unclassified"

    def test_youtube_file_classify_returns_tuple(self, _patch_paths):
        fp = Path("/inbox/How to Build AI [youtube.com_watch_v=abc].txt")
        entity, ctype = classify_file(fp)
        assert entity == "_unclassified"
        assert ctype == "youtube"


# ===========================================================================
# 2. TestExternalExpertDetection
# ===========================================================================
class TestExternalExpertDetection:
    """Files with expert names in filename are detected correctly."""

    def test_hormozi_filename_detects_entity(self, _patch_paths):
        _, _, dna = _patch_paths
        # Create the DNA dir so it appears in known entities
        (dna / "alex-hormozi").mkdir(exist_ok=True)
        fp = Path("/inbox/Alex Hormozi - Sales Module 3.txt")
        assert detect_entity(fp) == "alex-hormozi"

    def test_expert_file_content_type_is_courses(self, _patch_paths):
        fp = Path("/inbox/Alex Hormozi - Sales Module 3.txt")
        assert detect_content_type(fp) == "courses"

    def test_cole_gordon_closer_framework(self, _patch_paths):
        _, _, dna = _patch_paths
        (dna / "cole-gordon").mkdir(exist_ok=True)
        fp = Path("/inbox/Cole Gordon - Closer Framework Module 1.docx")
        entity, ctype = classify_file(fp)
        assert entity == "cole-gordon"
        assert ctype == "courses"


# ===========================================================================
# 3. TestBusinessMeetingClassification
# ===========================================================================
class TestBusinessMeetingClassification:
    """Meeting files with [MEET-XXXX] tags classify correctly."""

    def test_meet_tag_detected_as_calls(self, _patch_paths):
        fp = Path("/inbox/[MEET-0050] Acme-Co Weekly.txt")
        assert detect_content_type(fp) == "calls"

    def test_company_entity_detected(self, _patch_paths):
        fp = Path("/inbox/[MEET-0050] Acme Weekly.txt")
        assert detect_entity(fp) == "acme-co"


# ===========================================================================
# 4. TestPersonalProjectDetection
# ===========================================================================
class TestPersonalProjectDetection:
    """Personal project files via known aliases (outsider, otodus)."""

    def test_outsider_alias_in_filename(self, _patch_paths):
        fp = Path("/inbox/[MEET-0085] Planning Outsider 2.0 & Otodus System.txt")
        entity = detect_entity(fp)
        assert entity == "outsider"

    def test_planning_file_detected_as_calls(self, _patch_paths):
        fp = Path("/inbox/[MEET-0085] Planning Outsider 2.0 & Otodus System.txt")
        ctype = detect_content_type(fp)
        assert ctype == "calls"


# ===========================================================================
# 5. TestAlreadyOrganizedSkip
# ===========================================================================
class TestAlreadyOrganizedSkip:
    """_is_already_organized correctly distinguishes depth levels."""

    def test_depth_1_not_organized(self, tmp_path: Path):
        """File at inbox/file.txt -> NOT organized."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        f = inbox / "file.txt"
        f.touch()
        assert _is_already_organized(f, inbox) is False

    def test_depth_2_not_organized(self, tmp_path: Path):
        """File at inbox/entity/file.txt -> NOT organized (only 2 parts)."""
        inbox = tmp_path / "inbox"
        entity_dir = inbox / "alex-hormozi"
        entity_dir.mkdir(parents=True)
        f = entity_dir / "file.txt"
        f.touch()
        assert _is_already_organized(f, inbox) is False

    def test_depth_3_organized(self, tmp_path: Path):
        """File at inbox/entity/type/file.txt -> IS organized."""
        inbox = tmp_path / "inbox"
        deep = inbox / "alex-hormozi" / "courses"
        deep.mkdir(parents=True)
        f = deep / "file.txt"
        f.touch()
        assert _is_already_organized(f, inbox) is True

    def test_outside_inbox_returns_false(self, tmp_path: Path):
        """File completely outside inbox root -> False (ValueError caught)."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        outside = tmp_path / "elsewhere" / "file.txt"
        outside.parent.mkdir(parents=True)
        outside.touch()
        assert _is_already_organized(outside, inbox) is False


# ===========================================================================
# 6. TestFullOrganizeCycle
# ===========================================================================
class TestFullOrganizeCycle:
    """End-to-end organize_inbox tests with real file moves."""

    def test_three_files_moved_correctly(self, organized_inbox):
        inbox, logs = organized_inbox
        # Drop three files
        (inbox / "Alex Hormozi - Module 1.txt").write_text("content")
        (inbox / "[MEET-0001] Team Standup.txt").write_text("content")
        (inbox / "Random Podcast Episode 5.txt").write_text("content")

        result = organize_inbox("external")

        assert result["organized"] == 3
        assert result["errors"] == []

    def test_already_organized_files_skipped(self, organized_inbox):
        inbox, logs = organized_inbox
        # Create an already-organized file (depth 3)
        deep = inbox / "alex-hormozi" / "courses"
        deep.mkdir(parents=True)
        (deep / "existing.txt").write_text("organized")

        result = organize_inbox("external")

        assert result["already_organized"] == 1
        assert result["organized"] == 0

    def test_unsupported_extension_skipped(self, organized_inbox):
        inbox, logs = organized_inbox
        # .exe is not in SUPPORTED_EXTENSIONS
        (inbox / "malware.exe").write_text("nope")

        result = organize_inbox("external")

        assert result["skipped"] == 1
        assert result["organized"] == 0

    def test_unknown_bucket_returns_error(self, organized_inbox):
        result = organize_inbox("galactic_federation")

        assert "error" in result
        assert result["organized"] == 0

    def test_jsonl_log_written(self, organized_inbox):
        inbox, logs = organized_inbox
        (inbox / "Alex Hormozi - Training 1.txt").write_text("data")

        organize_inbox("external")

        log_file = logs / "inbox-organizer" / "organize-external.jsonl"
        assert log_file.exists()
        entries = log_file.read_text().strip().split("\n")
        assert len(entries) >= 1
        parsed = json.loads(entries[-1])
        assert parsed["bucket"] == "external"
        assert "timestamp" in parsed

    def test_organize_business_bucket(self, organized_inbox):
        inbox, logs = organized_inbox
        (inbox / "[MEET-0099] Weekly Review.txt").write_text("content")

        result = organize_inbox("business")

        assert result["organized"] == 1
        assert result["bucket"] == "business"

    def test_organize_personal_bucket(self, organized_inbox):
        inbox, logs = organized_inbox
        (inbox / "Personal journal entry.txt").write_text("thoughts")

        result = organize_inbox("personal")

        assert result["organized"] == 1
        assert result["bucket"] == "personal"


# ===========================================================================
# 7. TestEntityAliasResolution
# ===========================================================================
class TestEntityAliasResolution:
    """ENTITY_ALIASES map correctly resolves alternative names."""

    def test_hormozi_alias(self, _patch_paths):
        fp = Path("/inbox/hormozi sales training.txt")
        assert detect_entity(fp) == "alex-hormozi"

    def test_brand_alias_resolves_to_parent(self, _patch_paths):
        fp = Path("/inbox/acme-brand campaign report.txt")
        assert detect_entity(fp) == "acme-co"

    def test_otodus_resolves_to_outsider(self, _patch_paths):
        fp = Path("/inbox/otodus system design.txt")
        assert detect_entity(fp) == "outsider"

    def test_cole_alias(self, _patch_paths):
        # "cole" is an alias for cole-gordon
        fp = Path("/inbox/cole closer training.txt")
        assert detect_entity(fp) == "cole-gordon"

    def test_finch_resolves_to_founder(self, _patch_paths):
        fp = Path("/inbox/finch personal notes.txt")
        assert detect_entity(fp) == "founder-name"

    def test_krueger_resolves_to_collaborator(self, _patch_paths):
        fp = Path("/inbox/krueger strategy doc.txt")
        assert detect_entity(fp) == "collaborator-a"

    def test_billion_resolves_to_acme(self, _patch_paths):
        fp = Path("/inbox/billion meeting notes.txt")
        assert detect_entity(fp) == "acme-co"


# ===========================================================================
# 8. TestContentTypeEdgeCases
# ===========================================================================
class TestContentTypeEdgeCases:
    """Content type detection handles edge cases and extension fallbacks."""

    def test_masterclass_keyword(self, _patch_paths):
        fp = Path("/inbox/Ultimate Masterclass on Offers.txt")
        assert detect_content_type(fp) == "masterclasses"

    def test_mastermind_keyword(self, _patch_paths):
        fp = Path("/inbox/Inner Circle Mastermind Q4.txt")
        assert detect_content_type(fp) == "masterminds"

    def test_podcast_keyword(self, _patch_paths):
        fp = Path("/inbox/Podcast EP 45 Revenue Growth.txt")
        assert detect_content_type(fp) == "podcasts"

    def test_mp3_extension_fallback(self, _patch_paths):
        fp = Path("/inbox/random_audio_file.mp3")
        assert detect_content_type(fp) == "podcasts"

    def test_pdf_extension_fallback(self, _patch_paths):
        fp = Path("/inbox/annual_report.pdf")
        assert detect_content_type(fp) == "documents"

    def test_mp4_extension_fallback(self, _patch_paths):
        fp = Path("/inbox/clip_of_something.mp4")
        assert detect_content_type(fp) == "youtube"

    def test_misc_fallback_unknown_extension(self, _patch_paths):
        fp = Path("/inbox/something_weird.txt")
        assert detect_content_type(fp) == "misc"

    def test_script_keyword(self, _patch_paths):
        fp = Path("/inbox/Sales Script Template v2.txt")
        assert detect_content_type(fp) == "scripts"

    def test_blueprint_keyword(self, _patch_paths):
        fp = Path("/inbox/Revenue Blueprint 2026.txt")
        assert detect_content_type(fp) == "documents"


# ===========================================================================
# 9. TestSlugify
# ===========================================================================
class TestSlugify:
    """_slugify converts names to kebab-case correctly."""

    def test_spaces_to_hyphens(self):
        assert _slugify("Alex Hormozi") == "alex-hormozi"

    def test_underscores_to_hyphens(self):
        assert _slugify("COLE_GORDON") == "cole-gordon"

    def test_parentheses_removed(self):
        assert _slugify("Jeremy Haynes (EAD)") == "jeremy-haynes-ead"

    def test_multiple_spaces_collapsed(self):
        assert _slugify("Sam   Oven") == "sam-oven"

    def test_empty_string(self):
        assert _slugify("") == ""


# ===========================================================================
# 10. TestEntityFromDirectory
# ===========================================================================
class TestEntityFromDirectory:
    """Entity detection uses parent/grandparent directory names."""

    def test_entity_from_parent_dir(self, _patch_paths):
        _, _, dna = _patch_paths
        (dna / "alex-hormozi").mkdir(exist_ok=True)
        fp = Path("/inbox/alex-hormozi/some_random_file.txt")
        assert detect_entity(fp) == "alex-hormozi"

    def test_entity_from_grandparent_dir(self, _patch_paths):
        _, _, dna = _patch_paths
        (dna / "cole-gordon").mkdir(exist_ok=True)
        fp = Path("/inbox/cole-gordon/courses/lesson_1.txt")
        assert detect_entity(fp) == "cole-gordon"


# ===========================================================================
# Bonus: Additional coverage
# ===========================================================================
class TestOrganizeEdgeCases:
    """Extra edge cases for organize_inbox."""

    def test_dotfile_skipped(self, organized_inbox):
        inbox, _ = organized_inbox
        (inbox / ".DS_Store").write_text("x")

        result = organize_inbox("external")

        assert result["organized"] == 0
        assert result["skipped"] == 0  # .DS_Store is in SKIP_NAMES, filtered at rglob level

    def test_ref_yaml_skipped(self, organized_inbox):
        inbox, _ = organized_inbox
        (inbox / "some-file.ref.yaml").write_text("ref: true")

        result = organize_inbox("external")

        assert result["skipped"] == 1
        assert result["organized"] == 0

    def test_nonexistent_inbox_returns_zero(self, tmp_path, monkeypatch):
        nonexistent = tmp_path / "ghost_inbox"
        monkeypatch.setattr(
            f"{MODULE}.BUCKET_INBOXES",
            {"external": nonexistent},
        )
        monkeypatch.setattr(f"{MODULE}.DNA_PERSONS_DIR", tmp_path / "dna")
        monkeypatch.setattr(f"{MODULE}.LOGS", tmp_path / "logs")

        result = organize_inbox("external")

        assert result["organized"] == 0
        assert result["already_organized"] == 0

    def test_moves_list_contains_entity_and_type(self, organized_inbox):
        inbox, _ = organized_inbox
        (inbox / "Alex Hormozi - Offer Creation.txt").write_text("data")

        result = organize_inbox("external")

        assert len(result["moves"]) == 1
        move = result["moves"][0]
        assert "entity" in move
        assert "content_type" in move
        assert "destination" in move

    def test_file_actually_moved_on_disk(self, organized_inbox):
        inbox, _ = organized_inbox
        src = inbox / "Alex Hormozi - Module 5.txt"
        src.write_text("module 5 content")

        organize_inbox("external")

        # Source should no longer exist
        assert not src.exists()
        # Destination should exist
        dest = inbox / "alex-hormozi" / "courses" / "Alex Hormozi - Module 5.txt"
        assert dest.exists()
        assert dest.read_text() == "module 5 content"

    def test_classify_file_returns_correct_tuple(self, _patch_paths):
        _, _, dna = _patch_paths
        (dna / "jeremy-miner").mkdir(exist_ok=True)
        fp = Path("/inbox/Jeremy Miner - Masterclass on Closing.txt")
        entity, ctype = classify_file(fp)
        assert entity == "jeremy-miner"
        assert ctype == "masterclasses"
