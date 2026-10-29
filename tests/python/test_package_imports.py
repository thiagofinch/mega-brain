"""Imports por pacote: entity_normalizer e audit_layers não podem ser módulos de topo."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES = [
    "engine.intelligence.dossier.dossier_trigger",
    "engine.intelligence.dossier.review_dashboard",
    "engine.intelligence.dossier.theme_analyzer",
    "engine.intelligence.entities.business_model_detector",
    "engine.intelligence.entities.org_chain_detector",
    "engine.intelligence.entities.role_detector",
    "engine.intelligence.pipeline.sync_package_files",
    "engine.intelligence.validation.validate_layers",
    "engine.intelligence.validation.verify_classifications",
]

LOOSE = {"entity_normalizer", "audit_layers"}


@pytest.mark.parametrize("name", MODULES)
def test_import_by_package(name):
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:
        assert exc.name not in LOOSE, f"import solto restante: {exc}"
        if exc.name in {"engine.paths", "engine.config"}:
            pytest.skip(f"depende de {exc.name} (criado em paralelo)")
        raise


@pytest.mark.parametrize("name", MODULES)
def test_no_loose_sibling_import(name):
    src = (ROOT / (name.replace(".", "/") + ".py")).read_text(encoding="utf-8")
    for loose in LOOSE:
        assert f"from {loose} import" not in src.replace("engine.intelligence.entities." + loose, "").replace("engine.intelligence.validation." + loose, "")
