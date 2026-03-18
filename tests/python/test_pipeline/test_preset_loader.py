"""Tests for pipeline preset loader."""

import pytest

from core.configs.preset_loader import VALID_PRESETS, list_presets, load_preset

REQUIRED_TOP_LEVEL_KEYS = {
    "name",
    "description",
    "version",
    "ingestion",
    "chunking",
    "extraction",
    "output",
}


class TestLoadPreset:
    """Tests for load_preset function."""

    def test_load_course_preset(self):
        config = load_preset("course")
        assert isinstance(config, dict)
        assert config["name"] == "course"
        assert REQUIRED_TOP_LEVEL_KEYS.issubset(config.keys())

    def test_load_meeting_preset_scope(self):
        config = load_preset("meeting")
        assert config["ingestion"]["scope"] == "business"

    def test_load_podcast_preset(self):
        config = load_preset("podcast")
        assert config["name"] == "podcast"
        assert config["ingestion"]["scope"] == "external"

    def test_load_book_preset(self):
        config = load_preset("book")
        assert config["name"] == "book"
        assert config["chunking"]["max_tokens"] == 3000

    def test_invalid_preset_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown preset"):
            load_preset("invalid")

    def test_all_presets_have_required_keys(self):
        for name in VALID_PRESETS:
            config = load_preset(name)
            missing = REQUIRED_TOP_LEVEL_KEYS - set(config.keys())
            assert not missing, f"Preset '{name}' missing keys: {missing}"


class TestListPresets:
    """Tests for list_presets function."""

    def test_returns_four_items(self):
        presets = list_presets()
        assert len(presets) == 4

    def test_each_preset_has_metadata(self):
        presets = list_presets()
        for p in presets:
            assert "name" in p
            assert "description" in p
            assert "scope" in p
            assert p["description"] != "ERROR"

    def test_course_scope_is_external(self):
        presets = list_presets()
        course = next(p for p in presets if p["name"] == "course")
        assert course["scope"] == "external"

    def test_meeting_scope_is_business(self):
        presets = list_presets()
        meeting = next(p for p in presets if p["name"] == "meeting")
        assert meeting["scope"] == "business"
