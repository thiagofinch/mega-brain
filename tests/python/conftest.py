"""
Root conftest.py for Mega Brain test suite.
============================================
Provides global fixtures and re-exports from submodules.

Test markers (defined in pyproject.toml):
- @pytest.mark.unit: Fast isolated tests
- @pytest.mark.integration: Tests that touch filesystem
- @pytest.mark.e2e: End-to-end pipeline tests
- @pytest.mark.slow: Tests that take >5s
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Global fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the mega-brain project root directory."""
    return PROJECT_ROOT


@pytest.fixture()
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set minimal environment variables for testing."""
    monkeypatch.setenv("MEGA_BRAIN_TEST_MODE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key-not-real")


# Re-export pipeline fixtures for convenience
from tests.python.test_pipeline.conftest import (
    fake_decision,
    mock_llm_response,
    sample_course_transcript,
    sample_meeting_transcript,
    sample_personal_note,
    tmp_inbox,
)

__all__ = [
    "fake_decision",
    "mock_env_vars",
    "mock_llm_response",
    "project_root",
    "sample_course_transcript",
    "sample_meeting_transcript",
    "sample_personal_note",
    "tmp_inbox",
]
