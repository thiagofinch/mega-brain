"""
Tests for core.intelligence.dossier_tracer

Validates: fuzzy matching, citation injection, paragraph extraction,
coverage reporting, idempotency, and dry-run behavior.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from core.intelligence.dossier_tracer import (
    DNAEntry,
    TraceResult,
    _extract_paragraphs,
    _inject_citations,
    _is_traceable_paragraph,
    _match_paragraph_to_dna,
    _normalize,
    _slug_from_dossier_path,
    discover_dossiers,
    load_person_dna,
    trace_dossier,
    write_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_dna_entries() -> list[DNAEntry]:
    """Create sample DNA entries spanning multiple layers."""
    return [
        DNAEntry(
            entry_id="HEUR-TP-001",
            name="Price Raising Strategy",
            description="Price raising: clear pipeline before raise. Announce scarcity and urgency to boost cashflow.",
            layer="HEURISTICAS",
            person_slug="test-person",
        ),
        DNAEntry(
            entry_id="FW-TP-001",
            name="Do Document Delegate",
            description="Do Document Delegate: do it yourself first, document the process, then delegate with SOP ready.",
            layer="FRAMEWORKS",
            person_slug="test-person",
        ),
        DNAEntry(
            entry_id="FIL-TP-001",
            name="Philosophy Over Tactics",
            description="Philosophy over tactics. Mental models are more important than scripts. Flexibility beats memorization.",
            layer="FILOSOFIAS",
            person_slug="test-person",
        ),
        DNAEntry(
            entry_id="MM-TP-001",
            name="Bandwidth Trap",
            description="Most founders spend 80% time IN the business and 20% ON the business. Goal is to reverse this ratio.",
            layer="MODELOS-MENTAIS",
            person_slug="test-person",
        ),
        DNAEntry(
            entry_id="MET-TP-001",
            name="AIOS Implementation",
            description="AIOS implementation methodology step by step: context layer, data layer, intelligence layer, automate layer.",
            layer="METODOLOGIAS",
            person_slug="test-person",
        ),
    ]


@pytest.fixture
def sample_dossier_content() -> str:
    """Create a dossier-like markdown document."""
    return textwrap.dedent("""\
    # DOSSIE: Test Person

    > Em resumo: Expert in sales and scaling.

    ---

    ## Quem Sou

    Portfolio de negocios com faturamento alto. Especialista em escala e vendas.

    ---

    ## Modus Operandi

    ### Price Raising Strategy

    Clear your pipeline before any price raise. When you announce a price raise, you create scarcity and urgency which boosts cashflow immediately. This is a fundamental growth lever.

    ### Process Documentation

    Always do it yourself first, then document the entire process carefully, and finally delegate with the SOP ready. Never delegate what you have not documented. The chaos comes from delegating without process.

    ### Philosophy Over Tactics

    Philosophy is more important than tactics. If you have the right mental models, scripts and techniques come naturally. Flexibility in your approach always beats rigid memorization of scripts.

    ---

    ## Frameworks

    | Framework | Description |
    |-----------|-------------|
    | PPM | People Process Management |

    ```
    Code block content should be skipped
    This is inside a code block
    ```

    Most founders get trapped spending 80% of their time working IN the business doing must-dos and maintenance tasks, and only 20% working ON the business doing growth initiatives. The AIOS methodology exists to systematically reverse this ratio from 80/20 to 20/80.

    Building an AI operating system follows a step by step methodology: start with context layer where AI learns your business, then data layer to consolidate dashboards, then intelligence layer for meeting synthesis and daily briefs, then automate layer for task automation.

    ---

    ## Citacoes

    > "Because I choose to." -- Test Person
    """)


@pytest.fixture
def dossier_file(tmp_path: Path, sample_dossier_content: str) -> Path:
    """Write sample dossier to a temp file."""
    dossier = tmp_path / "DOSSIER-TEST-PERSON.md"
    dossier.write_text(sample_dossier_content, encoding="utf-8")
    return dossier


# ---------------------------------------------------------------------------
# Test: text normalization
# ---------------------------------------------------------------------------
class TestNormalize:
    def test_lowercase(self) -> None:
        assert _normalize("Hello WORLD") == "hello world"

    def test_strip_accents(self) -> None:
        result = _normalize("filosofía práctica")
        assert "a" in result  # accent stripped
        assert result == "filosofia practica"

    def test_collapse_whitespace(self) -> None:
        assert _normalize("  hello   world  ") == "hello world"

    def test_remove_punctuation(self) -> None:
        result = _normalize("Hello, world! (test)")
        assert result == "hello world test"  # punctuation -> space, then whitespace collapsed

    def test_empty_string(self) -> None:
        assert _normalize("") == ""


# ---------------------------------------------------------------------------
# Test: slug extraction from dossier path
# ---------------------------------------------------------------------------
class TestSlugExtraction:
    def test_standard_dossier(self) -> None:
        p = Path("/some/path/DOSSIER-ALEX-HORMOZI.md")
        assert _slug_from_dossier_path(p) == "alex-hormozi"

    def test_single_name(self) -> None:
        p = Path("/some/path/DOSSIER-PERSON.md")
        assert _slug_from_dossier_path(p) == "person"

    def test_lowercase_prefix(self) -> None:
        p = Path("/some/path/dossier-Test-Name.md")
        assert _slug_from_dossier_path(p) == "test-name"

    def test_no_prefix(self) -> None:
        p = Path("/some/path/RANDOM-FILE.md")
        assert _slug_from_dossier_path(p) == "random-file"


# ---------------------------------------------------------------------------
# Test: paragraph extraction
# ---------------------------------------------------------------------------
class TestParagraphExtraction:
    def test_extracts_paragraphs(self, sample_dossier_content: str) -> None:
        paras = _extract_paragraphs(sample_dossier_content)
        assert len(paras) > 0
        # Each paragraph tuple has (start, end, text)
        for start, end, text in paras:
            assert start <= end
            assert len(text.strip()) >= 30

    def test_skips_headers(self) -> None:
        content = "# Header\n\nReal paragraph text that is long enough to be traced.\n"
        paras = _extract_paragraphs(content)
        texts = [t for _, _, t in paras]
        assert not any(t.startswith("#") for t in texts)

    def test_skips_code_blocks(self, sample_dossier_content: str) -> None:
        paras = _extract_paragraphs(sample_dossier_content)
        texts = [t for _, _, t in paras]
        assert not any("Code block content" in t for t in texts)

    def test_skips_blockquotes(self) -> None:
        content = "> This is a blockquote\n\nThis is a real paragraph that exceeds the minimum length.\n"
        paras = _extract_paragraphs(content)
        texts = [t for _, _, t in paras]
        assert not any(t.startswith(">") for t in texts)

    def test_skips_table_rows(self) -> None:
        content = "| Col1 | Col2 |\n|------|------|\n| val  | val  |\n\nThis is a real paragraph that exceeds the minimum character count for tracing.\n"
        paras = _extract_paragraphs(content)
        texts = [t for _, _, t in paras]
        assert not any(t.startswith("|") for t in texts)

    def test_skips_short_text(self) -> None:
        content = "Short.\n\nAnother short line.\n"
        paras = _extract_paragraphs(content)
        assert len(paras) == 0


# ---------------------------------------------------------------------------
# Test: traceable paragraph detection
# ---------------------------------------------------------------------------
class TestIsTraceableParagraph:
    def test_normal_paragraph(self) -> None:
        assert _is_traceable_paragraph(
            "This is a normal paragraph with enough text to be considered traceable."
        )

    def test_too_short(self) -> None:
        assert not _is_traceable_paragraph("Short text.")

    def test_header(self) -> None:
        assert not _is_traceable_paragraph("# Header text that is long enough")

    def test_blockquote(self) -> None:
        assert not _is_traceable_paragraph("> Blockquote text that is long enough to count")

    def test_separator(self) -> None:
        assert not _is_traceable_paragraph("---")

    def test_code_fence(self) -> None:
        assert not _is_traceable_paragraph("```python this is code block")

    def test_empty(self) -> None:
        assert not _is_traceable_paragraph("")

    def test_table_row(self) -> None:
        assert not _is_traceable_paragraph("| Column1 | Column2 | Column3 |")


# ---------------------------------------------------------------------------
# Test: fuzzy matching
# ---------------------------------------------------------------------------
class TestFuzzyMatching:
    def test_high_similarity_match(self, sample_dna_entries: list[DNAEntry]) -> None:
        para = "Clear your pipeline before any price raise. Announce scarcity and urgency to boost cashflow."
        matches = _match_paragraph_to_dna(para, sample_dna_entries, threshold=0.4)
        assert len(matches) > 0
        assert matches[0][0].entry_id == "HEUR-TP-001"

    def test_no_match_below_threshold(self, sample_dna_entries: list[DNAEntry]) -> None:
        para = "Completely unrelated paragraph about quantum mechanics and black holes in space."
        matches = _match_paragraph_to_dna(para, sample_dna_entries, threshold=0.45)
        assert len(matches) == 0

    def test_max_citations_cap(self, sample_dna_entries: list[DNAEntry]) -> None:
        # Create a paragraph that could match everything
        para = ("Price raising clear pipeline scarcity urgency boost cashflow. "
                "Do document delegate SOP process. Philosophy mental models scripts "
                "flexibility memorization. Founders 80% IN business 20% ON business "
                "reverse ratio. AIOS implementation context data intelligence automate.")
        matches = _match_paragraph_to_dna(para, sample_dna_entries, threshold=0.1)
        assert len(matches) <= 3  # MAX_CITATIONS_PER_PARAGRAPH

    def test_already_cited_skip(self, sample_dna_entries: list[DNAEntry]) -> None:
        para = "Price raising strategy with scarcity and urgency ^[HEUR-TP-001] already cited here."
        matches = _match_paragraph_to_dna(para, sample_dna_entries, threshold=0.3)
        # Should not match HEUR-TP-001 again
        ids = [m.entry_id for m, _ in matches]
        assert "HEUR-TP-001" not in ids

    def test_empty_paragraph(self, sample_dna_entries: list[DNAEntry]) -> None:
        matches = _match_paragraph_to_dna("", sample_dna_entries)
        assert len(matches) == 0

    def test_matches_sorted_by_similarity(self, sample_dna_entries: list[DNAEntry]) -> None:
        para = "Philosophy and mental models are more important than tactics or scripts."
        matches = _match_paragraph_to_dna(para, sample_dna_entries, threshold=0.2)
        if len(matches) >= 2:
            scores = [s for _, s in matches]
            assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Test: citation injection
# ---------------------------------------------------------------------------
class TestCitationInjection:
    def test_adds_citations(self, sample_dna_entries: list[DNAEntry]) -> None:
        content = (
            "# Header\n\n"
            "Clear your pipeline before any price raise. "
            "Announce scarcity and urgency to boost cashflow.\n\n"
            "Unrelated short.\n"
        )
        paras = _extract_paragraphs(content)
        modified, log = _inject_citations(content, paras, sample_dna_entries, threshold=0.4)
        assert "^[HEUR-TP-001]" in modified
        assert len(log) > 0

    def test_no_modification_on_no_matches(self) -> None:
        content = "# Header\n\nCompletely unrelated paragraph about quantum mechanics and cosmic radiation.\n"
        entries = [
            DNAEntry("X-001", "Sales", "Sales closing techniques", "HEURISTICAS", "x")
        ]
        paras = _extract_paragraphs(content)
        modified, log = _inject_citations(content, paras, entries, threshold=0.9)
        assert modified == content
        assert len(log) == 0

    def test_citation_format(self, sample_dna_entries: list[DNAEntry]) -> None:
        content = (
            "Do it yourself first, then document the entire process carefully, "
            "and finally delegate with the SOP ready. Never delegate without process.\n"
        )
        paras = _extract_paragraphs(content)
        modified, log = _inject_citations(content, paras, sample_dna_entries, threshold=0.35)
        # Check citation format: ^[ID]
        import re
        citations = re.findall(r"\^\[[A-Z]+-[A-Z]+-\d+\]", modified)
        assert len(citations) > 0

    def test_idempotent_injection(self, sample_dna_entries: list[DNAEntry]) -> None:
        content = (
            "Clear your pipeline before any price raise. "
            "Announce scarcity and urgency to boost cashflow.\n"
        )
        paras = _extract_paragraphs(content)
        modified1, log1 = _inject_citations(content, paras, sample_dna_entries, threshold=0.4)

        # Run again on already-modified content
        paras2 = _extract_paragraphs(modified1)
        modified2, log2 = _inject_citations(modified1, paras2, sample_dna_entries, threshold=0.4)

        assert modified1 == modified2  # No double citations
        assert len(log2) == 0


# ---------------------------------------------------------------------------
# Test: DNAEntry properties
# ---------------------------------------------------------------------------
class TestDNAEntry:
    def test_citation_tag(self) -> None:
        entry = DNAEntry("HEUR-LO-001", "Test", "desc", "HEURISTICAS", "liam")
        assert entry.citation_tag == "^[HEUR-LO-001]"

    def test_citation_tag_old_format(self) -> None:
        entry = DNAEntry("heu_001", "Test", "desc", "HEURISTICAS", "hormozi")
        assert entry.citation_tag == "^[heu_001]"


# ---------------------------------------------------------------------------
# Test: trace_dossier integration
# ---------------------------------------------------------------------------
class TestTraceDossier:
    def test_traces_matching_dossier(
        self, dossier_file: Path, sample_dna_entries: list[DNAEntry]
    ) -> None:
        with patch(
            "core.intelligence.dossier_tracer.load_person_dna",
            return_value=sample_dna_entries,
        ):
            result = trace_dossier(dossier_file, dry_run=False, threshold=0.4)
            assert result.total_paragraphs > 0
            assert result.traced > 0
            assert result.coverage_pct > 0
            assert len(result.citations_added) > 0

            # Verify file was modified
            modified = dossier_file.read_text(encoding="utf-8")
            assert "^[" in modified

    def test_dry_run_no_modification(
        self, dossier_file: Path, sample_dna_entries: list[DNAEntry]
    ) -> None:
        original = dossier_file.read_text(encoding="utf-8")
        with patch(
            "core.intelligence.dossier_tracer.load_person_dna",
            return_value=sample_dna_entries,
        ):
            result = trace_dossier(dossier_file, dry_run=True, threshold=0.4)
            after = dossier_file.read_text(encoding="utf-8")
            assert original == after  # File unchanged
            assert result.traced > 0  # But matches were found

    def test_no_dna_entries(self, dossier_file: Path) -> None:
        with patch(
            "core.intelligence.dossier_tracer.load_person_dna",
            return_value=[],
        ):
            result = trace_dossier(dossier_file)
            assert result.traced == 0
            assert result.coverage_pct == 0.0
            assert len(result.citations_added) == 0

    def test_zero_coverage_not_modified(self, dossier_file: Path) -> None:
        original = dossier_file.read_text(encoding="utf-8")
        # Use entries that will never match
        unrelated_entries = [
            DNAEntry(
                "X-001", "Quantum", "Quantum entanglement photon decoherence",
                "HEURISTICAS", "nobody",
            )
        ]
        with patch(
            "core.intelligence.dossier_tracer.load_person_dna",
            return_value=unrelated_entries,
        ):
            result = trace_dossier(dossier_file, dry_run=False)
            after = dossier_file.read_text(encoding="utf-8")
            assert original == after
            assert result.coverage_pct == 0.0


# ---------------------------------------------------------------------------
# Test: report generation
# ---------------------------------------------------------------------------
class TestWriteReport:
    def test_writes_json_report(self, tmp_path: Path) -> None:
        results = [
            TraceResult(
                dossier="/path/to/DOSSIER-TEST.md",
                person="test-person",
                total_paragraphs=10,
                traced=3,
                coverage_pct=30.0,
                citations_added=[
                    {"entry_id": "HEUR-TP-001", "layer": "HEURISTICAS",
                     "similarity": 0.65, "paragraph_line": 5,
                     "paragraph_preview": "Test paragraph..."}
                ],
            ),
            TraceResult(
                dossier="/path/to/DOSSIER-EMPTY.md",
                person="empty-person",
                total_paragraphs=5,
                traced=0,
                coverage_pct=0.0,
                citations_added=[],
            ),
        ]
        with patch("core.intelligence.dossier_tracer.REPORT_PATH", tmp_path / "report.json"):
            path = write_report(results)
            assert path.exists()
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["total_dossiers"] == 2
            assert data["traced_dossiers"] == 1
            assert data["average_coverage_pct"] == 15.0
            assert len(data["dossiers"]) == 2
            assert data["dossiers"][0]["coverage_pct"] == 30.0
            assert data["dossiers"][1]["coverage_pct"] == 0.0


# ---------------------------------------------------------------------------
# Test: discover_dossiers (uses real filesystem)
# ---------------------------------------------------------------------------
class TestDiscoverDossiers:
    def test_finds_external_dossiers(self) -> None:
        dossiers = discover_dossiers()
        assert len(dossiers) > 0
        # All should be DOSSIER-*.md files
        for d in dossiers:
            assert d.stem.upper().startswith("DOSSIER-")
            assert d.suffix == ".md"

    def test_filter_by_person(self) -> None:
        dossiers = discover_dossiers(person_filter="alex-hormozi")
        assert len(dossiers) == 1
        assert "HORMOZI" in dossiers[0].stem.upper()

    def test_filter_nonexistent_person(self) -> None:
        dossiers = discover_dossiers(person_filter="nonexistent-person")
        assert len(dossiers) == 0

    def test_excludes_example_files(self) -> None:
        dossiers = discover_dossiers()
        for d in dossiers:
            assert "EXAMPLE" not in d.stem.upper()


# ---------------------------------------------------------------------------
# Test: load_person_dna (uses real filesystem)
# ---------------------------------------------------------------------------
class TestLoadPersonDNA:
    def test_loads_alex_hormozi(self) -> None:
        entries = load_person_dna("alex-hormozi")
        assert len(entries) > 0
        layers = {e.layer for e in entries}
        assert "HEURISTICAS" in layers
        assert "FRAMEWORKS" in layers

    def test_loads_jordan_lee(self) -> None:
        entries = load_person_dna("jordan-lee")
        assert len(entries) > 0
        # Jordan Lee uses INS-JL-XXX format
        assert any(e.entry_id.startswith("INS-JL") for e in entries)

    def test_loads_liam_ottley(self) -> None:
        entries = load_person_dna("liam-ottley")
        assert len(entries) > 0
        # Liam uses HEUR-LO, FW-LO, etc format
        assert any("LO" in e.entry_id for e in entries)

    def test_nonexistent_person_returns_empty(self) -> None:
        entries = load_person_dna("nobody-at-all")
        assert len(entries) == 0

    def test_all_entries_have_required_fields(self) -> None:
        entries = load_person_dna("alex-hormozi")
        for e in entries:
            assert e.entry_id
            assert e.description
            assert e.layer in (
                "HEURISTICAS", "FRAMEWORKS", "MODELOS-MENTAIS",
                "FILOSOFIAS", "METODOLOGIAS",
            )
            assert e.person_slug == "alex-hormozi"


# ---------------------------------------------------------------------------
# Test: CLI main
# ---------------------------------------------------------------------------
class TestCLI:
    def test_dry_run_returns_zero(self) -> None:
        from core.intelligence.dossier_tracer import main
        exit_code = main(["--dry-run"])
        assert exit_code == 0

    def test_filter_nonexistent_returns_one(self) -> None:
        from core.intelligence.dossier_tracer import main
        exit_code = main(["--person", "nonexistent-xyz"])
        assert exit_code == 1
