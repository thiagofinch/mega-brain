"""Imports que quebravam na release publica: read_ai_router, typed_schema e config da voz."""

from __future__ import annotations

import importlib
import sys
from unittest import mock

import pytest


def test_read_ai_harvester_usa_meeting_router():
    mod = importlib.import_module("engine.intelligence.pipeline.read_ai_harvester")
    from engine.intelligence.pipeline.meeting_router import MeetingRouter

    assert mod.MeetingRouter is MeetingRouter


def test_read_ai_harvester_roteia_reuniao(tmp_path):
    from engine.intelligence.pipeline.read_ai_config import ReadAIConfig
    from engine.intelligence.pipeline.read_ai_harvester import ReadAIHarvester

    cfg = ReadAIConfig(
        company_name="Acme",
        company_domains=["acme.com"],
        company_keywords=["acme"],
        log_dir=tmp_path / "log",
        state_path=tmp_path / "state.json",
        staging_dir=tmp_path / "staging",
        empresa_dir=tmp_path / "empresa",
        pessoal_dir=tmp_path / "pessoal",
    )
    h = ReadAIHarvester(cfg)
    staging = tmp_path / "staging"
    staging.mkdir()
    f = staging / "m1.txt"
    f.write_text("x", encoding="utf-8")
    data = h._extract_router_data(
        {"id": "m1", "title": "Acme weekly", "organizer_email": "a@acme.com", "participants": []}
    )
    decision = h.router.classify_meeting(data)
    dest = h.router.move_file(f, decision, "[MEET-0001]", cfg.empresa_dir, cfg.pessoal_dir)
    assert decision.bucket == "empresa"
    assert dest.parent == cfg.empresa_dir and dest.exists()


def test_ontology_layer_sem_typed_schema():
    mod = importlib.import_module("engine.intelligence.rag.ontology_layer")
    legacy = ["filosofia", "modelo_mental", "heuristica", "framework", "metodologia"]
    assert mod.LAYER_HIERARCHY == legacy
    # Hot-path ligado, mas sem typed_schema publico: cai nos 5 tipos legados.
    assert mod._build_layer_hierarchy(enabled=True) == legacy


@pytest.mark.parametrize("name", ["adaptive_router", "graph_query"])
def test_rag_modulos_dependentes_de_ontology_layer_importam(name):
    importlib.import_module(f"engine.intelligence.rag.{name}")


def test_voice_importa_config_por_pacote(monkeypatch):
    # As dependencias de terceiros da voz (anthropic, sounddevice...) estao em
    # engine/jarvis/voice/requirements.txt: as ausentes sao substituidas por stubs
    # para isolar o que este teste verifica (o import de `config` por pacote).
    for mod in [m for m in sys.modules if m.startswith("engine.jarvis.voice")]:
        monkeypatch.delitem(sys.modules, mod)
    for dep in ("anthropic", "sounddevice", "elevenlabs", "deepgram"):
        try:
            importlib.import_module(dep)
        except ImportError:
            monkeypatch.setitem(sys.modules, dep, mock.MagicMock())
    pkg = None
    for _ in range(15):
        try:
            pkg = importlib.import_module("engine.jarvis.voice")
            break
        except ModuleNotFoundError as exc:
            assert exc.name and not exc.name.startswith(("engine", "config")), exc
            monkeypatch.setitem(sys.modules, exc.name, mock.MagicMock())
    assert pkg is not None
    from engine.jarvis.voice.config import Config

    assert pkg.Config is Config
    connector = importlib.import_module("engine.jarvis.voice.mega_brain_connector")
    assert connector.Config is Config
