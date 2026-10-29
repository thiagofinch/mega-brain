"""Optional dependencies must not break imports (watchdog, dynamic_security)."""

from __future__ import annotations

import builtins
import importlib
import sys

import pytest

WATCHER = "engine.intelligence.pipeline.inbox_watcher"
STORE = "engine.intelligence.rag.postgres_store"


def _block(monkeypatch: pytest.MonkeyPatch, prefixes: tuple[str, ...]) -> None:
    """Make imports of the given module prefixes raise ImportError."""
    real_import = builtins.__import__

    def fake(name, globals=None, locals=None, fromlist=(), level=0):
        base = name
        if level and globals:
            base = f"{globals.get('__package__', '')}.{name}".strip(".")
        if any(base == p or base.startswith(p + ".") for p in prefixes):
            raise ImportError(f"blocked for test: {base}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake)
    for mod in [m for m in sys.modules if m == WATCHER or m == STORE]:
        monkeypatch.delitem(sys.modules, mod)


def test_inbox_watcher_imports_without_watchdog(monkeypatch):
    _block(monkeypatch, ("watchdog",))
    mod = importlib.import_module(WATCHER)
    assert mod.Observer is None
    assert issubclass(mod.InboxHandler, object)


def test_run_daemon_without_watchdog_fails_clearly(monkeypatch, tmp_path, caplog):
    _block(monkeypatch, ("watchdog",))
    mod = importlib.import_module(WATCHER)
    monkeypatch.setattr(mod, "WATCHED_DIRS", {"t": tmp_path / "inbox"})
    monkeypatch.setattr(mod, "startup_sweep", lambda *a, **k: None)
    monkeypatch.setattr(mod.WatcherState, "write", lambda self: None)
    assert mod.run_daemon(once=False) == 1
    assert "pip install watchdog" in caplog.text
    # --once never needs the observer
    assert mod.run_daemon(once=True) == 0


def test_postgres_store_imports_without_dynamic_security(monkeypatch):
    _block(monkeypatch, ("engine.intelligence.rag.dynamic_security",))
    mod = importlib.import_module(STORE)
    assert mod.FILTERABLE_IDENTITY_COLUMNS == frozenset({"visibility", "client_id"})
    assert {"visibility", "client_id", "person", "bu"} <= mod._FILTERABLE_COLUMNS


def test_fallback_whitelist_is_closed(monkeypatch):
    _block(monkeypatch, ("engine.intelligence.rag.dynamic_security",))
    mod = importlib.import_module(STORE)
    # the phantom ``persona`` column and arbitrary keys must stay out of SQL
    assert "persona" not in mod._FILTERABLE_COLUMNS
    assert "id; DROP TABLE x" not in mod._FILTERABLE_COLUMNS


def test_rag_package_imports():
    importlib.import_module("engine.intelligence.rag")
