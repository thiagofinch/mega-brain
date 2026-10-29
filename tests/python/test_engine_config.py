"""Tests for engine.config.get_config (interface used by engine callers)."""

import ast
from pathlib import Path

import pytest

from engine import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]
KEY = "MB_TEST_CONFIG_KEY"


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.delenv(KEY, raising=False)
    monkeypatch.setattr(cfg, "_ENV_FILE", tmp_path / ".env")
    cfg.reload_config()
    yield
    cfg.reload_config()


def _write_env(monkeypatch, text):
    cfg._ENV_FILE.write_text(text, encoding="utf-8")
    cfg.reload_config()


def test_missing_key_returns_none_and_default():
    assert cfg.get_config(KEY) is None
    assert cfg.get_config(KEY, "x") == "x"
    assert cfg.get_config(KEY, default="y") == "y"


def test_missing_env_file_does_not_break():
    assert not cfg._ENV_FILE.exists()
    assert cfg.get_config(KEY, "") == ""


def test_env_overrides_dotenv(monkeypatch):
    _write_env(monkeypatch, f"{KEY}=from_file\n")
    assert cfg.get_config(KEY) == "from_file"
    monkeypatch.setenv(KEY, "from_env")
    assert cfg.get_config(KEY) == "from_env"


def test_dotenv_does_not_touch_environ(monkeypatch):
    import os

    _write_env(monkeypatch, f"{KEY}=v\n")
    assert cfg.get_config(KEY) == "v"
    assert KEY not in os.environ


def test_empty_values_count_as_unset(monkeypatch):
    _write_env(monkeypatch, f"{KEY}=\n")
    assert cfg.get_config(KEY, "d") == "d"
    monkeypatch.setenv(KEY, "  ")
    assert cfg.get_config(KEY, "d") == "d"


def test_dotenv_parsing(monkeypatch):
    _write_env(
        monkeypatch,
        "# comment\n\nexport A_KEY=1\nB_KEY = \"two words\"\n"
        "C_KEY='x#y'\nD_KEY=val # trailing\nnot a line\n",
    )
    assert cfg.get_config("A_KEY") == "1"
    assert cfg.get_config("B_KEY") == "two words"
    assert cfg.get_config("C_KEY") == "x#y"
    assert cfg.get_config("D_KEY") == "val"


def test_dotenv_is_cached_until_reload(monkeypatch):
    _write_env(monkeypatch, f"{KEY}=one\n")
    assert cfg.get_config(KEY) == "one"
    cfg._ENV_FILE.write_text(f"{KEY}=two\n", encoding="utf-8")
    assert cfg.get_config(KEY) == "one"
    cfg.reload_config()
    assert cfg.get_config(KEY) == "two"


def test_callers_use_supported_signature():
    """Every caller passes (key[, default]) with at most 2 args."""
    bad = []
    for path in REPO_ROOT.rglob("*.py"):
        if any(p in path.parts for p in (".git", "tests", "node_modules")):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "get_config"
            ):
                kw = {k.arg for k in node.keywords}
                if len(node.args) + len(node.keywords) > 2 or not kw <= {"default"}:
                    bad.append(f"{path}:{node.lineno}")
    assert not bad, bad
