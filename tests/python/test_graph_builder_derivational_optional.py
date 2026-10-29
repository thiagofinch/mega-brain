"""graph_builder: the ``derivational_edges`` extension is optional (opt-in, default OFF)."""

import importlib
import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

import pytest

PKG = "engine.intelligence.rag"
EXT = f"{PKG}.derivational_edges"
GB_PATH = Path(__file__).resolve().parents[2] / "engine" / "intelligence" / "rag" / "graph_builder.py"


def _load_graph_builder(monkeypatch, ext):
    """Load a fresh copy of graph_builder with ``ext`` as the sibling extension.

    ``ext=None`` blocks the module (absent); a module object simulates it installed.
    """
    monkeypatch.setitem(sys.modules, EXT, ext)
    name = f"{PKG}.graph_builder_probe"
    spec = importlib.util.spec_from_file_location(name, GB_PATH)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, mod)
    spec.loader.exec_module(mod)
    return mod


def _fake_extension():
    mod = types.ModuleType(EXT)
    mod.__spec__ = importlib.machinery.ModuleSpec(EXT, None)
    mod.calls = []
    mod.extract_domains = lambda entry: (mod.calls.append("domains"), ["d"])[1]
    mod.extract_provenance = lambda entry: (mod.calls.append("prov"), {"src"})[1]
    mod.derive_edges = lambda atoms: (mod.calls.append("derive"), [])[1]
    mod.count_by_verb = lambda specs: {}
    return mod


def _minimal_dna(tmp_path):
    person = tmp_path / "dna" / "persons" / "alice"
    person.mkdir(parents=True)
    (person / "FILOSOFIAS.yaml").write_text(
        "filosofias:\n  - id: F1\n    nome: Crenca\n", encoding="utf-8"
    )
    return tmp_path / "dna" / "persons"


@pytest.fixture(autouse=True)
def _no_save(monkeypatch):
    monkeypatch.delenv("MB_DERIVATIONAL_EDGES_ENABLED", raising=False)


def test_import_without_extension(monkeypatch):
    gb = _load_graph_builder(monkeypatch, None)
    assert gb._derivational is None


def test_default_off_does_not_need_extension(monkeypatch, tmp_path):
    gb = _load_graph_builder(monkeypatch, None)
    monkeypatch.setattr(gb, "GRAPH_DIR", tmp_path / "graph", raising=False)
    graph = gb.build_graph(_minimal_dna(tmp_path), bucket="external")
    assert graph.built


@pytest.mark.parametrize("via", ["env", "param"])
def test_enabled_without_extension_raises_clear_error(monkeypatch, tmp_path, via):
    gb = _load_graph_builder(monkeypatch, None)
    kwargs = {}
    if via == "env":
        monkeypatch.setenv("MB_DERIVATIONAL_EDGES_ENABLED", "1")
    else:
        kwargs["derivational"] = True
    with pytest.raises(RuntimeError) as err:
        gb.build_graph(_minimal_dna(tmp_path), bucket="external", **kwargs)
    assert "derivational_edges" in str(err.value)
    assert "MB_DERIVATIONAL_EDGES_ENABLED" in str(err.value)


def test_param_false_overrides_env_without_extension(monkeypatch, tmp_path):
    gb = _load_graph_builder(monkeypatch, None)
    monkeypatch.setattr(gb, "GRAPH_DIR", tmp_path / "graph", raising=False)
    monkeypatch.setenv("MB_DERIVATIONAL_EDGES_ENABLED", "1")
    assert gb.build_graph(_minimal_dna(tmp_path), bucket="external", derivational=False).built


def test_extension_present_is_still_used(monkeypatch, tmp_path):
    ext = _fake_extension()
    gb = _load_graph_builder(monkeypatch, ext)
    monkeypatch.setattr(gb, "GRAPH_DIR", tmp_path / "graph", raising=False)
    assert gb._derivational is ext
    gb.build_graph(_minimal_dna(tmp_path), bucket="external", derivational=True)
    assert "derive" in ext.calls and "prov" in ext.calls


def test_extension_present_but_off_is_not_called(monkeypatch, tmp_path):
    ext = _fake_extension()
    gb = _load_graph_builder(monkeypatch, ext)
    monkeypatch.setattr(gb, "GRAPH_DIR", tmp_path / "graph", raising=False)
    gb.build_graph(_minimal_dna(tmp_path), bucket="external")
    assert ext.calls == []
