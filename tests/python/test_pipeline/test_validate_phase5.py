"""Tests for .claude/scripts/validate_phase5.py

All tests are OFFLINE -- no real filesystem outside tmp_path.
Every test builds its own directory structure via fixtures.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_phase5 as vp  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_FILES = ["AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml"]


def _build_complete_structure(root: Path) -> None:
    """Build a fully valid Phase 5 directory structure."""
    agents_ext = root / "agents" / "external"
    dna_persons = root / "knowledge" / "external" / "dna" / "persons"
    dossiers_persons = root / "knowledge" / "external" / "dossiers" / "persons"
    dossiers_themes = root / "knowledge" / "external" / "dossiers" / "themes"

    # Create two agents with all required files
    for name in ["alex-hormozi", "cole-gordon"]:
        agent_dir = agents_ext / name
        agent_dir.mkdir(parents=True, exist_ok=True)
        for fname in REQUIRED_FILES:
            (agent_dir / fname).write_text(f"# {fname} for {name}\n")

        # Matching DNA directory with a YAML
        dna_dir = dna_persons / name
        dna_dir.mkdir(parents=True, exist_ok=True)
        (dna_dir / "PHILOSOPHIES.yaml").write_text("philosophies: []\n")

    # Create dossiers
    dossiers_persons.mkdir(parents=True, exist_ok=True)
    (dossiers_persons / "DOSSIER-ALEX-HORMOZI.md").write_text("# Dossier\n")

    dossiers_themes.mkdir(parents=True, exist_ok=True)
    (dossiers_themes / "DOSSIER-SALES.md").write_text("# Sales dossier\n")


# ---------------------------------------------------------------------------
# Fixture: patch PROJECT_ROOT to tmp_path
# ---------------------------------------------------------------------------


@pytest.fixture()
def patched_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patch all module-level paths to use tmp_path as root."""
    root = tmp_path / "mega-brain"
    root.mkdir()

    monkeypatch.setattr(vp, "PROJECT_ROOT", root)
    monkeypatch.setattr(vp, "KNOWLEDGE_EXTERNAL", root / "knowledge" / "external")
    monkeypatch.setattr(vp, "AGENTS_EXTERNAL", root / "agents" / "external")
    monkeypatch.setattr(vp, "DNA_PERSONS", root / "knowledge" / "external" / "dna" / "persons")
    monkeypatch.setattr(vp, "DOSSIERS_PERSONS", root / "knowledge" / "external" / "dossiers" / "persons")
    monkeypatch.setattr(vp, "DOSSIERS_THEMES", root / "knowledge" / "external" / "dossiers" / "themes")
    monkeypatch.setattr(vp, "LOGS_BATCHES", root / "logs" / "batches")

    return root


# ---------------------------------------------------------------------------
# Tests: validate_phase5 returns 0 when all checks pass
# ---------------------------------------------------------------------------


class TestValidatePhase5Pass:
    """validate_phase5() returns 0 when structure is complete."""

    def test_returns_zero_on_complete_structure(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        assert vp.validate_phase5() == 0

    def test_skips_hidden_and_template_dirs(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        # Add dirs that should be skipped
        hidden = patched_root / "agents" / "external" / ".hidden"
        hidden.mkdir(parents=True)
        template = patched_root / "agents" / "external" / "_templates"
        template.mkdir(parents=True)
        assert vp.validate_phase5() == 0


# ---------------------------------------------------------------------------
# Tests: validate_phase5 returns 1 on failures
# ---------------------------------------------------------------------------


class TestValidatePhase5Fail:
    """validate_phase5() returns 1 when issues are found."""

    def test_returns_one_when_agent_missing_files(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        # Remove SOUL.md from one agent
        soul = patched_root / "agents" / "external" / "alex-hormozi" / "SOUL.md"
        soul.unlink()
        assert vp.validate_phase5() == 1

    def test_returns_one_when_dna_missing(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        # Remove entire DNA directory for one agent
        import shutil

        dna_dir = patched_root / "knowledge" / "external" / "dna" / "persons" / "cole-gordon"
        shutil.rmtree(dna_dir)
        assert vp.validate_phase5() == 1

    def test_returns_one_when_agents_dir_missing(self, patched_root: Path) -> None:
        """CRITICAL issue when agents/external/ does not exist at all."""
        # Don't create anything
        assert vp.validate_phase5() == 1

    def test_returns_one_when_dna_root_missing(self, patched_root: Path) -> None:
        """CRITICAL issue when knowledge/external/dna/persons/ is absent."""
        _build_complete_structure(patched_root)
        import shutil

        shutil.rmtree(patched_root / "knowledge" / "external" / "dna" / "persons")
        assert vp.validate_phase5() == 1


# ---------------------------------------------------------------------------
# Tests: check_agent_completeness
# ---------------------------------------------------------------------------


class TestCheckAgentCompleteness:
    """check_agent_completeness() lists missing files."""

    def test_no_issues_when_complete(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        issues = vp.check_agent_completeness()
        assert issues == []

    def test_lists_missing_files(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        # Remove two files from alex-hormozi
        (patched_root / "agents" / "external" / "alex-hormozi" / "MEMORY.md").unlink()
        (patched_root / "agents" / "external" / "alex-hormozi" / "DNA-CONFIG.yaml").unlink()

        issues = vp.check_agent_completeness()
        assert len(issues) == 1
        assert issues[0]["agent"] == "alex-hormozi"
        assert "MEMORY.md" in issues[0]["message"]
        assert "DNA-CONFIG.yaml" in issues[0]["message"]

    def test_critical_when_dir_missing(self, patched_root: Path) -> None:
        """Returns CRITICAL if agents/external/ does not exist."""
        issues = vp.check_agent_completeness()
        assert len(issues) == 1
        assert issues[0]["type"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Tests: check_dna_exists
# ---------------------------------------------------------------------------


class TestCheckDnaExists:
    """check_dna_exists() detects missing DNA dirs."""

    def test_no_issues_when_all_present(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        issues = vp.check_dna_exists()
        assert issues == []

    def test_detects_missing_dna_dir(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        import shutil

        shutil.rmtree(patched_root / "knowledge" / "external" / "dna" / "persons" / "alex-hormozi")

        issues = vp.check_dna_exists()
        assert len(issues) == 1
        assert issues[0]["agent"] == "alex-hormozi"
        assert issues[0]["type"] == "HIGH"

    def test_critical_when_dna_root_missing(self, patched_root: Path) -> None:
        issues = vp.check_dna_exists()
        assert len(issues) == 1
        assert issues[0]["type"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Tests: check_dossiers_current
# ---------------------------------------------------------------------------


class TestCheckDossiersCurrent:
    """check_dossiers_current() detects empty/missing dossier dirs."""

    def test_no_issues_when_present(self, patched_root: Path) -> None:
        _build_complete_structure(patched_root)
        issues = vp.check_dossiers_current()
        assert issues == []

    def test_detects_missing_person_dossiers_dir(self, patched_root: Path) -> None:
        """MEDIUM issue when person dossiers directory is absent."""
        _build_complete_structure(patched_root)
        import shutil

        shutil.rmtree(patched_root / "knowledge" / "external" / "dossiers" / "persons")

        issues = vp.check_dossiers_current()
        person_issues = [i for i in issues if "person" in i["message"]]
        assert len(person_issues) == 1
        assert person_issues[0]["type"] == "MEDIUM"

    def test_detects_empty_theme_dossiers(self, patched_root: Path) -> None:
        """MEDIUM issue when theme dossiers dir exists but is empty."""
        _build_complete_structure(patched_root)
        # Remove the theme dossier file but keep dir
        (patched_root / "knowledge" / "external" / "dossiers" / "themes" / "DOSSIER-SALES.md").unlink()

        issues = vp.check_dossiers_current()
        theme_issues = [i for i in issues if "theme" in i["message"]]
        assert len(theme_issues) == 1
        assert theme_issues[0]["type"] == "MEDIUM"

    def test_detects_outdated_dossier_vs_batch(self, patched_root: Path) -> None:
        """HIGH issue when dossier is older than latest batch (RULE #21)."""
        _build_complete_structure(patched_root)

        # Create a batch log directory with a recent batch
        batch_dir = patched_root / "logs" / "batches"
        batch_dir.mkdir(parents=True, exist_ok=True)
        batch_file = batch_dir / "BATCH-099.md"
        batch_file.write_text("# Batch 099\n")

        # Make the dossier older than the batch
        import time

        old_time = time.time() - 86400  # 24 hours ago
        dossier = patched_root / "knowledge" / "external" / "dossiers" / "themes" / "DOSSIER-SALES.md"
        os.utime(dossier, (old_time, old_time))

        issues = vp.check_dossiers_current()
        outdated = [i for i in issues if "Outdated" in i.get("message", "")]
        assert len(outdated) >= 1
        assert outdated[0]["type"] == "HIGH"


# ---------------------------------------------------------------------------
# Tests: --fix flag
# ---------------------------------------------------------------------------


class TestFixFlag:
    """The --fix flag shows detailed fix instructions."""

    def test_fix_output_includes_fix_instructions(self, patched_root: Path, capsys: pytest.CaptureFixture) -> None:
        _build_complete_structure(patched_root)
        # Remove a file to trigger a failure
        (patched_root / "agents" / "external" / "cole-gordon" / "AGENT.md").unlink()

        result = vp.validate_phase5(fix=True)
        assert result == 1

        captured = capsys.readouterr()
        assert "FIXES NEEDED" in captured.out
        assert "cole-gordon" in captured.out
