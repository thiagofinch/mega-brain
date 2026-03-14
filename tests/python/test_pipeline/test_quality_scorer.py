"""Tests for core.intelligence.validation.quality_scorer.

All tests are OFFLINE -- no real API calls, no real filesystem outside tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.intelligence.validation.quality_scorer import (
    QualityScore,
    _grade,
    get_trend,
    load_scores,
    persist_score,
    score_agent,
    score_batch,
)

# ---------------------------------------------------------------------------
# _grade() boundary tests
# ---------------------------------------------------------------------------


class TestGrade:
    """Verify letter grade assignment at every boundary."""

    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (0, "F"),
            (29, "F"),
            (30, "D"),
            (49, "D"),
            (50, "C"),
            (69, "C"),
            (70, "B"),
            (89, "B"),
            (90, "A"),
            (100, "A"),
        ],
    )
    def test_grade_boundaries(self, score: int, expected: str) -> None:
        assert _grade(score) == expected


# ---------------------------------------------------------------------------
# score_batch() tests
# ---------------------------------------------------------------------------


class TestScoreBatch:
    """Verify batch scoring logic."""

    def test_well_formed_batch_scores_above_zero(self, tmp_path: Path) -> None:
        """A batch with proper sections should score > 0."""
        batch = tmp_path / "BATCH-050.md"
        batch.write_text(
            "# BATCH 050\n"
            "---\n"
            "## CONTEXTO DA MISSAO\n"
            "### DESTINO DO CONHECIMENTO\n"
            "### ARQUIVOS PROCESSADOS\n"
            "---\n"
            "## FONTE: Alex Hormozi\n\n"
            "### PHILOSOPHIES\n"
            "- Cash is king ^[FONTE:SOUL.md:70]\n"
            "### MENTAL MODELS\n"
            "- LTV/CAC framework ^[FONTE:MEMORY.md:42]\n"
            "### HEURISTICS\n"
            "- Margem minima 40% ^[FONTE:HEUR-AH-025]\n"
            "### FRAMEWORKS\n"
            "- Value Ladder ^[FONTE:FW-AH-001]\n"
            "### METHODOLOGIES\n"
            "- CLOSER method ^[FONTE:MET-AH-003]\n"
            + "\n".join(f"- Item {i}" for i in range(50))  # enough lines
            + "\n",
            encoding="utf-8",
        )
        result = score_batch(batch)
        assert result.total > 0
        assert result.item_type == "batch"
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_rich_batch_scores_high(self, tmp_path: Path) -> None:
        """A batch with all DNA layers, good structure, and citations scores high."""
        batch = tmp_path / "BATCH-099.md"
        lines = [
            "# BATCH 099 - Cole Gordon",
            "---",
            "## CONTEXTO DA MISSAO",
            "FONTE: Cole Gordon",
            "### DESTINO DO CONHECIMENTO",
            "### ARQUIVOS PROCESSADOS",
            "### BATCH SUMMARY",
            "---",
            "## PHILOSOPHIES",
            "- Sales is service ^[FONTE:SOUL.md:10]",
            "## MENTAL MODELS",
            "- Conviction selling ^[FONTE:MM-CG-001]",
            "## HEURISTICS",
            "- Close rate > 30% ^[FONTE:HEUR-CG-010]",
            "## FRAMEWORKS",
            "- 5 Armas ^[FONTE:FW-CG-005]",
            "## METHODOLOGIES",
            "- Objection isolation ^[FONTE:MET-CG-002]",
        ]
        # Add citations and list items
        for i in range(15):
            lines.append(f"- Insight {i} ^[FONTE:chunk_{i}]")
        # Pad to 50+ lines
        lines.extend([f"- Padding line {i}" for i in range(40)])
        batch.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = score_batch(batch, batch_id="BATCH-099")
        assert result.total >= 50  # Should score well
        assert result.item_id == "BATCH-099"

    def test_minimal_file_scores_low(self, tmp_path: Path) -> None:
        """A near-empty batch file should score very low."""
        batch = tmp_path / "BATCH-EMPTY.md"
        batch.write_text("Hello world\n", encoding="utf-8")
        result = score_batch(batch)
        assert result.total < 30
        assert result.grade in ("D", "F")

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """Scoring a nonexistent batch raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            score_batch(tmp_path / "DOES-NOT-EXIST.md")

    def test_batch_id_override(self, tmp_path: Path) -> None:
        """The batch_id parameter overrides stem-based ID."""
        batch = tmp_path / "some-file.md"
        batch.write_text("# Content\n", encoding="utf-8")
        result = score_batch(batch, batch_id="CUSTOM-ID")
        assert result.item_id == "CUSTOM-ID"

    def test_batch_id_defaults_to_stem(self, tmp_path: Path) -> None:
        """Without batch_id, item_id defaults to file stem."""
        batch = tmp_path / "BATCH-042.md"
        batch.write_text("# Content\n", encoding="utf-8")
        result = score_batch(batch)
        assert result.item_id == "BATCH-042"


# ---------------------------------------------------------------------------
# score_agent() tests
# ---------------------------------------------------------------------------


class TestScoreAgent:
    """Verify agent directory scoring logic."""

    def test_complete_agent_scores_high(self, tmp_path: Path) -> None:
        """An agent dir with all files and good structure scores well."""
        agent = tmp_path / "alex-hormozi"
        agent.mkdir()

        # AGENT.md with V3 template markers
        (agent / "AGENT.md").write_text(
            "\u2554" + "=" * 40 + "\u2557\n"  # ASCII box top
            "## PARTE 1: COMPOSICAO ATOMICA\n"
            "## PARTE 2: GRAFICO DE IDENTIDADE\n"
            "## PARTE 3: MAPA NEURAL\n"
            "## PARTE 4: NUCLEO OPERACIONAL\n"
            "## PARTE 5: SISTEMA DE VOZ\n"
            "## PARTE 6: MOTOR DE DECISAO\n"
            "## PARTE 7: INTERFACES DE CONEXAO\n"
            "## PARTE 8: PROTOCOLO DE DEBATE\n"
            "## PARTE 9: MEMORIA EXPERIENCIAL\n"
            "## PARTE 10: EXPANSAO E REFERENCIAS\n",
            encoding="utf-8",
        )

        # SOUL.md with citations
        (agent / "SOUL.md").write_text(
            "# SOUL\n"
            "Cash is king ^[FONTE:inbox/hormozi:70]\n"
            "Unit economics first ^[FONTE:inbox/hormozi:80]\n"
            "Build offers ^[chunk_42]\n",
            encoding="utf-8",
        )

        # MEMORY.md with citations
        (agent / "MEMORY.md").write_text(
            "# MEMORY\n"
            "| Insight | Source |\n"
            "| LTV/CAC 3x | ^[FONTE:HEUR-AH-025] |\n"
            "| Margem 40% | ^[FONTE:HEUR-AH-030] |\n",
            encoding="utf-8",
        )

        # DNA-CONFIG.yaml
        (agent / "DNA-CONFIG.yaml").write_text(
            "version: 1.0\nsources:\n  - alex-hormozi\n",
            encoding="utf-8",
        )

        result = score_agent(agent)
        assert result.total > 40  # All files exist, has structure and citations
        assert result.item_type == "agent"
        assert result.item_id == "alex-hormozi"

    def test_empty_agent_dir_scores_low(self, tmp_path: Path) -> None:
        """An agent directory with no files scores 0."""
        agent = tmp_path / "empty-agent"
        agent.mkdir()
        result = score_agent(agent)
        assert result.total == 0
        assert result.grade == "F"

    def test_partial_agent_dir(self, tmp_path: Path) -> None:
        """An agent dir with only AGENT.md still gets partial score."""
        agent = tmp_path / "partial-agent"
        agent.mkdir()
        (agent / "AGENT.md").write_text(
            "## PARTE 1\n## PARTE 2\n## PARTE 3\n## PARTE 4\n## PARTE 5\n## PARTE 6\n",
            encoding="utf-8",
        )
        result = score_agent(agent)
        assert result.coverage > 0  # 1/4 files
        assert result.total > 0

    def test_nonexistent_dir_raises(self, tmp_path: Path) -> None:
        """Scoring a nonexistent directory raises NotADirectoryError."""
        with pytest.raises(NotADirectoryError):
            score_agent(tmp_path / "ghost-agent")

    def test_file_not_dir_raises(self, tmp_path: Path) -> None:
        """Scoring a file (not directory) raises NotADirectoryError."""
        f = tmp_path / "not-a-dir.txt"
        f.write_text("oops")
        with pytest.raises(NotADirectoryError):
            score_agent(f)


# ---------------------------------------------------------------------------
# persist_score() / load_scores() tests
# ---------------------------------------------------------------------------


class TestPersistence:
    """Verify JSONL persistence round-trip."""

    @staticmethod
    def _make_score(item_id: str = "TEST-001", total: int = 75) -> QualityScore:
        return QualityScore(
            item_id=item_id,
            item_type="batch",
            coverage=20,
            clarity=20,
            completeness=20,
            traceability=15,
            total=total,
            grade=_grade(total),
            timestamp="2026-03-14T12:00:00+00:00",
            details={"coverage": "test"},
        )

    def test_persist_creates_file(self, tmp_path: Path) -> None:
        """persist_score creates the JSONL file and parent dirs."""
        scores_file = tmp_path / "sub" / "scores.jsonl"
        score = self._make_score()
        persist_score(score, scores_file)
        assert scores_file.exists()
        lines = scores_file.read_text().strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["item_id"] == "TEST-001"

    def test_persist_appends(self, tmp_path: Path) -> None:
        """Multiple persist calls append to the same file."""
        scores_file = tmp_path / "scores.jsonl"
        persist_score(self._make_score("A"), scores_file)
        persist_score(self._make_score("B"), scores_file)
        persist_score(self._make_score("C"), scores_file)
        lines = scores_file.read_text().strip().splitlines()
        assert len(lines) == 3

    def test_load_scores_roundtrip(self, tmp_path: Path) -> None:
        """Scores written with persist can be loaded back."""
        scores_file = tmp_path / "scores.jsonl"
        original = self._make_score("ROUND-TRIP", 82)
        persist_score(original, scores_file)

        loaded = load_scores(scores_file)
        assert len(loaded) == 1
        assert loaded[0].item_id == "ROUND-TRIP"
        assert loaded[0].total == 82
        assert loaded[0].grade == "B"

    def test_load_scores_empty_file(self, tmp_path: Path) -> None:
        """Loading from a nonexistent file returns empty list."""
        scores_file = tmp_path / "nonexistent.jsonl"
        assert load_scores(scores_file) == []

    def test_load_scores_skips_blank_lines(self, tmp_path: Path) -> None:
        """Blank lines in JSONL are skipped gracefully."""
        scores_file = tmp_path / "scores.jsonl"
        score = self._make_score()
        persist_score(score, scores_file)
        # Append a blank line
        with open(scores_file, "a") as f:
            f.write("\n\n")
        loaded = load_scores(scores_file)
        assert len(loaded) == 1


# ---------------------------------------------------------------------------
# get_trend() tests
# ---------------------------------------------------------------------------


class TestGetTrend:
    """Verify trend retrieval for specific items."""

    def test_trend_returns_totals(self, tmp_path: Path) -> None:
        """get_trend returns list of total scores for a given item_id."""
        scores_file = tmp_path / "scores.jsonl"
        for total in [60, 70, 85]:
            persist_score(
                QualityScore(
                    item_id="TREND-ITEM",
                    item_type="batch",
                    coverage=15,
                    clarity=15,
                    completeness=15,
                    traceability=15,
                    total=total,
                    grade=_grade(total),
                    timestamp="2026-03-14T12:00:00+00:00",
                    details={},
                ),
                scores_file,
            )
        # Add a different item to make sure filtering works
        persist_score(
            QualityScore(
                item_id="OTHER-ITEM",
                item_type="batch",
                coverage=5,
                clarity=5,
                completeness=5,
                traceability=5,
                total=20,
                grade="F",
                timestamp="2026-03-14T12:00:00+00:00",
                details={},
            ),
            scores_file,
        )

        trend = get_trend("TREND-ITEM", scores_file)
        assert trend == [60, 70, 85]

    def test_trend_empty_for_unknown_item(self, tmp_path: Path) -> None:
        """get_trend returns empty list for item with no scores."""
        scores_file = tmp_path / "scores.jsonl"
        assert get_trend("UNKNOWN", scores_file) == []


# ---------------------------------------------------------------------------
# QualityScore dataclass tests
# ---------------------------------------------------------------------------


class TestQualityScoreDataclass:
    """Verify the QualityScore dataclass structure."""

    def test_has_all_fields(self) -> None:
        """QualityScore has all required fields."""
        score = QualityScore(
            item_id="test",
            item_type="batch",
            coverage=25,
            clarity=25,
            completeness=25,
            traceability=25,
            total=100,
            grade="A",
            timestamp="2026-01-01T00:00:00Z",
            details={"key": "value"},
        )
        assert score.item_id == "test"
        assert score.item_type == "batch"
        assert score.coverage == 25
        assert score.clarity == 25
        assert score.completeness == 25
        assert score.traceability == 25
        assert score.total == 100
        assert score.grade == "A"
        assert score.timestamp == "2026-01-01T00:00:00Z"
        assert score.details == {"key": "value"}

    def test_grade_matches_total(self) -> None:
        """Verify grade is consistent with total score."""
        for total, expected_grade in [(95, "A"), (75, "B"), (55, "C"), (35, "D"), (10, "F")]:
            score = QualityScore(
                item_id="x",
                item_type="batch",
                coverage=0,
                clarity=0,
                completeness=0,
                traceability=0,
                total=total,
                grade=_grade(total),
                timestamp="",
                details={},
            )
            assert score.grade == expected_grade
