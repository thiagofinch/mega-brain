"""Tests for engine.paths — every symbol imported by the repo exists and is a safe Path."""

from __future__ import annotations

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def _imported_symbols() -> set[str]:
    """Collect every name imported via ``from engine.paths import ...`` in the repo."""
    names: set[str] = set()
    for py in REPO.rglob("*.py"):
        if _SKIP_DIRS & set(py.relative_to(REPO).parts):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "engine.paths" and not node.level:
                names.update(a.name for a in node.names if a.name != "*")
    return names


SYMBOLS = sorted(_imported_symbols())


@pytest.fixture(scope="module")
def paths_module():
    return importlib.import_module("engine.paths")


def test_scan_found_symbols():
    assert "ROOT" in SYMBOLS and "ROUTING" in SYMBOLS
    assert len(SYMBOLS) >= 40


@pytest.mark.parametrize("name", SYMBOLS)
def test_symbol_exists(paths_module, name):
    assert hasattr(paths_module, name), f"engine.paths.{name} is imported but not defined"


@pytest.mark.parametrize("name", [s for s in SYMBOLS if s != "ROUTING"])
def test_symbol_is_absolute_path_under_root(paths_module, name):
    value = getattr(paths_module, name)
    root = paths_module.ROOT
    assert isinstance(value, Path)
    assert value.is_absolute()
    assert value == root or root in value.parents


def test_root_is_repo_root(paths_module):
    assert paths_module.ROOT == REPO
    assert (paths_module.ROOT / "engine" / "paths.py").is_file()


def test_routing_values_are_paths_under_root(paths_module):
    routing = paths_module.ROUTING
    for key in (
        "external_inbox",
        "business_inbox",
        "personal_inbox",
        "workspace_inbox",
        "mce_state",
        "watcher_state",
        "watcher_log",
        "read_ai_log",
        "read_ai_state",
        "read_ai_staging",
        "hhem_model",
    ):
        assert key in routing, key
    for key, value in routing.items():
        assert isinstance(value, Path), key
        assert value.is_absolute(), key
        assert paths_module.ROOT in value.parents, key


def test_import_has_no_disk_side_effects():
    """Importing engine.paths from a fresh interpreter must not create anything."""

    def snapshot() -> set[str]:
        return {p.relative_to(REPO).as_posix() for p in REPO.rglob("*") if ".git" not in p.parts}

    before = snapshot()
    code = "import engine.paths"
    env = {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=REPO,
        env={**os.environ, **env},
        check=True,
    )
    after = snapshot()
    created = {p for p in after - before if "__pycache__" not in p}
    assert not created, f"import created: {sorted(created)}"
