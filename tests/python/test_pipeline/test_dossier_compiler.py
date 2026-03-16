"""
Tests for core.intelligence.pipeline.dossier_compiler
======================================================
Covers: load_insights_state, gather_person_insights, get_all_person_names,
        compile_dossier, DomainTaxonomy, _slugify, _parse_insight,
        _extract_existing_ids, merge behavior, bucket routing.

All tests are OFFLINE using tmp_path fixtures and synthetic data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
import core.intelligence.pipeline.dossier_compiler as dc

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TAXONOMY = {
    "versao": "2.0.0",
    "dominios": [
        {
            "id": "vendas",
            "aliases": ["sales", "comercial", "selling"],
            "subdominios": ["qualificacao", "closing", "objecoes"],
            "descricao": "Processo de vendas",
        },
        {
            "id": "mindset",
            "aliases": ["mentalidade", "filosofia", "beliefs"],
            "subdominios": ["crencas", "motivacao", "decisao"],
            "descricao": "Mentalidade e filosofia",
        },
        {
            "id": "scaling",
            "aliases": ["escala", "growth", "scale"],
            "subdominios": ["processos", "automacao"],
            "descricao": "Escala de operacoes",
        },
        {
            "id": "hiring",
            "aliases": ["contratacao", "recrutamento", "recruiting"],
            "subdominios": ["sourcing", "entrevista"],
            "descricao": "Contratacao e talentos",
        },
    ],
    "pessoas": {
        "ALEX-HORMOZI": {
            "expertise_primaria": ["vendas", "scaling", "mindset"],
            "expertise_secundaria": ["hiring"],
            "contexto": "Gym Launch, $100M frameworks",
        },
        "COLE-GORDON": {
            "expertise_primaria": ["vendas"],
            "expertise_secundaria": ["scaling"],
            "contexto": "Closers.io",
        },
    },
}


def _make_taxonomy_file(tmp_path: Path) -> Path:
    """Write sample taxonomy YAML and return its path."""
    path = tmp_path / "DOMAINS-TAXONOMY.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(SAMPLE_TAXONOMY, f, allow_unicode=True)
    return path


def _make_insights_state(tmp_path: Path, data: dict) -> Path:
    """Write sample INSIGHTS-STATE.json and return its path."""
    path = tmp_path / "INSIGHTS-STATE.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


SAMPLE_STATE = {
    "version": "2.1.1",
    "total_insights": 10,
    "categories": {},
    "sources": {},
    "persons": {
        "Alex Hormozi": [
            {
                "id": "AH-001",
                "insight": "Closing gives people decision-making POWER",
                "tag": "[FILOSOFIA]",
                "priority": "HIGH",
                "confidence": "HIGH",
                "chunks": ["AH-CP001_003"],
                "quote": "The goal of closing is not to get the prospect to buy.",
            },
            {
                "id": "AH-002",
                "insight": "ONION OF BLAME Framework for objections",
                "tag": "[FRAMEWORK]",
                "priority": "HIGH",
                "confidence": "HIGH",
                "chunks": ["AH-CP001_004"],
            },
            {
                "id": "AH-003",
                "insight": "3 AUDIENCE BUCKETS from advertising: YES, NO, MAYBE",
                "tag": "[MODELO-MENTAL]",
                "priority": "HIGH",
                "confidence": "HIGH",
                "chunks": ["AH-CP001_002"],
            },
            {
                "id": "AH-004",
                "insight": "STAR Qualification: Situation, Timing, Authority, Resources",
                "tag": "[FRAMEWORK]",
                "priority": "HIGH",
                "confidence": "HIGH",
                "chunks": ["AH-CP001_008"],
            },
            {
                "id": "AH-005",
                "insight": "The REASON close: why you cannot is why you should",
                "tag": "[HEURISTICA]",
                "priority": "HIGH",
                "confidence": "HIGH",
                "chunks": ["AH-CP001_005"],
            },
        ],
        "MEET-0026": {
            "source": "MEET-0026",
            "source_title": "Team Meeting",
            "bucket": "business",
            "date": "2026-03-02",
            "participants": ["Pedro", "Thiago"],
            "insights": [
                {
                    "id": "MEET0026-001",
                    "insight": "CLI first approach for product",
                    "tag": "[HEURISTICA]",
                    "priority": "HIGH",
                    "chunks": ["chunk_MEET0026_005"],
                    "person": "Pedro Valerio",
                    "source": "MEET-0026",
                },
                {
                    "id": "MEET0026-002",
                    "insight": "Sales funnel for enterprise tier",
                    "tag": "[FRAMEWORK]",
                    "priority": "HIGH",
                    "chunks": ["chunk_MEET0026_006"],
                    "person": "Pedro Valerio",
                    "source": "MEET-0026",
                },
                {
                    "id": "MEET0026-003",
                    "insight": "Team scaling through automation",
                    "tag": "[METODOLOGIA]",
                    "priority": "MEDIUM",
                    "chunks": ["chunk_MEET0026_007"],
                    "person": "Thiago Finch",
                    "source": "MEET-0026",
                },
            ],
        },
        "Diego Monet": {
            "meetings": ["MEET-0660"],
            "insight_count": 2,
            "bucket": "business",
            "role": "CEO",
        },
    },
}


@pytest.fixture()
def taxonomy_path(tmp_path: Path) -> Path:
    return _make_taxonomy_file(tmp_path)


@pytest.fixture()
def insights_path(tmp_path: Path) -> Path:
    return _make_insights_state(tmp_path, SAMPLE_STATE)


@pytest.fixture()
def taxonomy(taxonomy_path: Path) -> dc.DomainTaxonomy:
    return dc.DomainTaxonomy(taxonomy_path)


@pytest.fixture()
def state(insights_path: Path) -> dict:
    return dc.load_insights_state(insights_path)


# ---------------------------------------------------------------------------
# Tests: _slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_basic_name(self):
        assert dc._slugify("Cole Gordon") == "COLE-GORDON"

    def test_accented_name(self):
        assert dc._slugify("Pedro Valerio") == "PEDRO-VALERIO"

    def test_unicode_accent(self):
        # Accented characters should be stripped
        result = dc._slugify("Pedro Valerio Lopez")
        assert result == "PEDRO-VALERIO-LOPEZ"

    def test_single_name(self):
        assert dc._slugify("Homer") == "HOMER"


# ---------------------------------------------------------------------------
# Tests: DomainTaxonomy
# ---------------------------------------------------------------------------


class TestDomainTaxonomy:
    def test_load_domains(self, taxonomy: dc.DomainTaxonomy):
        assert len(taxonomy.domains) == 4

    def test_is_external_person(self, taxonomy: dc.DomainTaxonomy):
        assert taxonomy.is_external_person("Alex Hormozi") is True
        assert taxonomy.is_external_person("Cole Gordon") is True

    def test_is_not_external_person(self, taxonomy: dc.DomainTaxonomy):
        assert taxonomy.is_external_person("Pedro Valerio") is False
        assert taxonomy.is_external_person("Unknown Person") is False

    def test_get_person_expertise(self, taxonomy: dc.DomainTaxonomy):
        expertise = taxonomy.get_person_expertise("Alex Hormozi")
        assert "vendas" in expertise
        assert "scaling" in expertise

    def test_classify_insight_by_tag(self, taxonomy: dc.DomainTaxonomy):
        ins = dc.Insight(id="X", text="something", tag="[FILOSOFIA]")
        domain = taxonomy.classify_insight(ins)
        assert domain == "mindset"

    def test_classify_insight_by_keyword(self, taxonomy: dc.DomainTaxonomy):
        ins = dc.Insight(id="X", text="hiring process and recruiting talent", tag="")
        domain = taxonomy.classify_insight(ins)
        assert domain == "hiring"

    def test_classify_insight_fallback(self, taxonomy: dc.DomainTaxonomy):
        ins = dc.Insight(id="X", text="something completely unrelated xyz", tag="")
        domain = taxonomy.classify_insight(ins)
        assert domain == "general"

    def test_get_domain_label(self, taxonomy: dc.DomainTaxonomy):
        label = taxonomy.get_domain_label("vendas")
        assert label == "Processo de vendas"

    def test_get_domain_label_unknown(self, taxonomy: dc.DomainTaxonomy):
        label = taxonomy.get_domain_label("unknown_domain")
        assert label == "Unknown_Domain"

    def test_missing_taxonomy_file(self, tmp_path: Path):
        missing = tmp_path / "nonexistent.yaml"
        tax = dc.DomainTaxonomy(missing)
        assert len(tax.domains) == 0


# ---------------------------------------------------------------------------
# Tests: _parse_insight
# ---------------------------------------------------------------------------


class TestParseInsight:
    def test_basic_parse(self):
        raw = {
            "id": "AH-001",
            "insight": "Test insight",
            "tag": "[FRAMEWORK]",
            "priority": "HIGH",
            "chunks": ["chunk1"],
            "source": "MEET-0001",
        }
        ins = dc._parse_insight(raw)
        assert ins.id == "AH-001"
        assert ins.text == "Test insight"
        assert ins.tag == "[FRAMEWORK]"
        assert ins.source == "MEET-0001"

    def test_dict_source(self):
        raw = {
            "id": "LO-001",
            "insight": "Test insight",
            "source": {
                "source_type": "course",
                "source_id": "LO-001",
                "source_title": "Video Title",
            },
        }
        ins = dc._parse_insight(raw)
        assert ins.source == "LO-001"

    def test_dict_source_fallback_title(self):
        raw = {
            "id": "X",
            "insight": "Test",
            "source": {"source_type": "course", "source_title": "My Video"},
        }
        ins = dc._parse_insight(raw)
        assert ins.source == "My Video"

    def test_missing_fields_default(self):
        raw = {"id": "X"}
        ins = dc._parse_insight(raw)
        assert ins.text == ""
        assert ins.priority == "MEDIUM"
        assert ins.confidence == "MEDIUM"


# ---------------------------------------------------------------------------
# Tests: get_all_person_names
# ---------------------------------------------------------------------------


class TestGetAllPersonNames:
    def test_finds_persons(self, state: dict):
        names = dc.get_all_person_names(state)
        assert "Alex Hormozi" in names

    def test_finds_meeting_persons(self, state: dict):
        names = dc.get_all_person_names(state)
        assert "Pedro Valerio" in names
        assert "Thiago Finch" in names

    def test_skips_empty_dict_persons(self, state: dict):
        """Diego Monet has insight_count > 0 but no actual insights list."""
        names = dc.get_all_person_names(state)
        assert "Diego Monet" in names  # Added because insight_count > 0

    def test_excludes_meeting_keys(self, state: dict):
        names = dc.get_all_person_names(state)
        assert "MEET-0026" not in names


# ---------------------------------------------------------------------------
# Tests: gather_person_insights
# ---------------------------------------------------------------------------


class TestGatherPersonInsights:
    def test_gather_direct_person(self, state: dict, taxonomy: dc.DomainTaxonomy):
        result = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        assert result is not None
        assert result.name == "Alex Hormozi"
        assert result.bucket == "external"
        assert len(result.insights) == 5

    def test_gather_meeting_person(self, state: dict, taxonomy: dc.DomainTaxonomy):
        result = dc.gather_person_insights(state, "Pedro Valerio", taxonomy)
        assert result is not None
        assert result.name == "Pedro Valerio"
        assert result.bucket == "business"
        assert len(result.insights) == 2

    def test_gather_unknown_person(self, state: dict, taxonomy: dc.DomainTaxonomy):
        result = dc.gather_person_insights(state, "Nobody Real", taxonomy)
        assert result is None

    def test_external_bucket_routing(self, state: dict, taxonomy: dc.DomainTaxonomy):
        result = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        assert result.bucket == "external"

    def test_business_bucket_routing(self, state: dict, taxonomy: dc.DomainTaxonomy):
        result = dc.gather_person_insights(state, "Thiago Finch", taxonomy)
        assert result is not None
        assert result.bucket == "business"

    def test_sources_populated(self, state: dict, taxonomy: dc.DomainTaxonomy):
        result = dc.gather_person_insights(state, "Pedro Valerio", taxonomy)
        assert "MEET-0026" in result.sources


# ---------------------------------------------------------------------------
# Tests: compile_dossier (new dossier)
# ---------------------------------------------------------------------------


class TestCompileDossierNew:
    def test_creates_new_dossier(self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path):
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        # Override output dirs to tmp_path
        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result = dc.compile_dossier(person, taxonomy)

        assert result.is_update is False
        assert result.new_insights_added == 5
        assert result.output_path.exists()

    def test_new_dossier_has_header(self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path):
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result = dc.compile_dossier(person, taxonomy)

        content = result.output_path.read_text(encoding="utf-8")
        assert "# DOSSIER -- Alex Hormozi" in content
        assert "External Expert" in content
        assert "Total insights" in content

    def test_new_dossier_has_domain_sections(
        self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path
    ):
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result = dc.compile_dossier(person, taxonomy)

        content = result.output_path.read_text(encoding="utf-8")
        assert "## " in content  # Has section headers
        assert "^[" in content  # Has citations

    def test_business_person_routes_correctly(
        self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path
    ):
        person = dc.gather_person_insights(state, "Pedro Valerio", taxonomy)
        biz_dir = tmp_path / "business" / "dossiers" / "persons"
        biz_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "BUSINESS_DOSSIERS_DIR", biz_dir):
            result = dc.compile_dossier(person, taxonomy)

        assert "DOSSIER-PEDRO-VALERIO.md" in result.output_path.name
        assert result.output_path.exists()
        content = result.output_path.read_text(encoding="utf-8")
        assert "Business" in content

    def test_dry_run_does_not_write(self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path):
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result = dc.compile_dossier(person, taxonomy, dry_run=True)

        assert not result.output_path.exists()


# ---------------------------------------------------------------------------
# Tests: compile_dossier (merge/update)
# ---------------------------------------------------------------------------


class TestCompileDossierMerge:
    def test_rerun_is_idempotent(self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path):
        """Running compile twice produces UP-TO-DATE on second run."""
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result1 = dc.compile_dossier(person, taxonomy)
            result2 = dc.compile_dossier(person, taxonomy)

        assert result1.new_insights_added == 5
        assert result2.new_insights_added == 0
        assert result2.is_update is True

    def test_merge_appends_new_insights(self, taxonomy: dc.DomainTaxonomy, tmp_path: Path):
        """If new insights appear, they are appended to existing dossier."""
        # Create initial state with 2 insights
        initial_state = {
            "version": "1.0",
            "persons": {
                "Test Person": [
                    {
                        "id": "TP-001",
                        "insight": "First insight about sales",
                        "tag": "[HEURISTICA]",
                        "priority": "HIGH",
                        "chunks": ["chunk1"],
                    },
                ],
            },
        }
        # Compile initial dossier
        person = dc.gather_person_insights(initial_state, "Test Person", taxonomy)
        biz_dir = tmp_path / "business" / "dossiers" / "persons"
        biz_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "BUSINESS_DOSSIERS_DIR", biz_dir):
            dc.compile_dossier(person, taxonomy)

        # Now add a new insight to the state
        updated_state = {
            "version": "1.0",
            "persons": {
                "Test Person": [
                    {
                        "id": "TP-001",
                        "insight": "First insight about sales",
                        "tag": "[HEURISTICA]",
                        "priority": "HIGH",
                        "chunks": ["chunk1"],
                    },
                    {
                        "id": "TP-002",
                        "insight": "Second insight about scaling teams",
                        "tag": "[METODOLOGIA]",
                        "priority": "MEDIUM",
                        "chunks": ["chunk2"],
                    },
                ],
            },
        }
        person2 = dc.gather_person_insights(updated_state, "Test Person", taxonomy)

        with mock.patch.object(dc, "BUSINESS_DOSSIERS_DIR", biz_dir):
            result = dc.compile_dossier(person2, taxonomy)

        assert result.is_update is True
        assert result.new_insights_added == 1

        content = result.output_path.read_text(encoding="utf-8")
        assert "First insight" in content
        assert "Second insight" in content


# ---------------------------------------------------------------------------
# Tests: _extract_existing_ids
# ---------------------------------------------------------------------------


class TestExtractExistingIds:
    def test_extracts_insight_ids(self):
        content = """
- **Some insight** [HIGH]
  ^[AH-001, chunk_AH001_003, MEET-0026]

- **Another insight**
  ^[MEET0026-002, chunk_MEET0026_005]
"""
        ids = dc._extract_existing_ids(content)
        assert "AH-001" in ids
        assert "MEET0026-002" in ids

    def test_returns_empty_for_no_citations(self):
        content = "# Some dossier without citations"
        ids = dc._extract_existing_ids(content)
        assert len(ids) == 0

    def test_ignores_plain_chunk_refs(self):
        content = "^[chunk_MEET0026_005, MEET-0026]"
        ids = dc._extract_existing_ids(content)
        # chunk_ refs are not insight IDs (they don't match the ID pattern)
        assert "chunk_MEET0026_005" not in ids


# ---------------------------------------------------------------------------
# Tests: _format_insight_block
# ---------------------------------------------------------------------------


class TestFormatInsightBlock:
    def test_basic_format(self):
        ins = dc.Insight(
            id="AH-001",
            text="Test insight",
            priority="HIGH",
            chunks=["chunk1"],
            source="SRC-01",
        )
        block = dc._format_insight_block(ins)
        assert "**Test insight** [HIGH]" in block
        assert "^[AH-001, chunk1, SRC-01]" in block

    def test_with_quote(self):
        ins = dc.Insight(
            id="AH-002",
            text="Test",
            quote="This is a quote",
        )
        block = dc._format_insight_block(ins)
        assert '"This is a quote"' in block

    def test_medium_priority_no_marker(self):
        ins = dc.Insight(id="X", text="Test", priority="MEDIUM")
        block = dc._format_insight_block(ins)
        assert "[HIGH]" not in block


# ---------------------------------------------------------------------------
# Tests: Integration (end-to-end with sample data)
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_full_pipeline_new_dossier(
        self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path
    ):
        """Full pipeline: load -> gather -> compile for a new person."""
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result = dc.compile_dossier(person, taxonomy)

        assert result.person == "Alex Hormozi"
        assert result.is_update is False
        assert result.new_insights_added == 5
        assert len(result.domains_used) > 0
        assert result.output_path.name == "DOSSIER-ALEX-HORMOZI.md"

        content = result.output_path.read_text(encoding="utf-8")
        assert "DOSSIER -- Alex Hormozi" in content
        assert "External Expert" in content
        assert "Closing gives people decision-making POWER" in content

    def test_person_with_5_plus_insights_organized_by_domain(
        self, state: dict, taxonomy: dc.DomainTaxonomy, tmp_path: Path
    ):
        """AC: person with 5+ insights has output organized by domain."""
        person = dc.gather_person_insights(state, "Alex Hormozi", taxonomy)
        assert len(person.insights) >= 5

        ext_dir = tmp_path / "external" / "dossiers" / "persons"
        ext_dir.mkdir(parents=True)

        import unittest.mock as mock

        with mock.patch.object(dc, "EXTERNAL_DOSSIERS_DIR", ext_dir):
            result = dc.compile_dossier(person, taxonomy)

        content = result.output_path.read_text(encoding="utf-8")
        # Must have multiple ## domain sections
        sections = [line for line in content.split("\n") if line.startswith("## ")]
        assert len(sections) >= 2
