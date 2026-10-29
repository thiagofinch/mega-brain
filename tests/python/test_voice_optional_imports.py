"""Pacote engine.jarvis.voice importavel sem as dependencias opcionais de voz."""

from __future__ import annotations

import ast
import builtins
import importlib
import sys
from pathlib import Path

import pytest

# Dependencias base da voz (engine/jarvis/voice/requirements.txt). Sem elas o
# pacote de voz nao e utilizavel e estes testes nao se aplicam.
for _base in ("numpy", "requests", "fastapi", "uvicorn", "flask"):
    pytest.importorskip(_base)

PKG = "engine.jarvis.voice"
VOICE_DIR = Path(__file__).resolve().parents[2] / "engine" / "jarvis" / "voice"
OPTIONAL = ("anthropic", "pyaudio", "sounddevice", "elevenlabs", "torch", "flask_cors")
MODULES = [
    "config",
    "jarvis_narrator",
    "jarvis_terminal",
    "main",
    "mega_brain_connector",
    "orchestrator",
    "server",
    "stt_handler",
    "test_mic",
    "transition_phrases",
    "tts_handler",
    "tts_sesame",
    "vapi_setup",
    "vapi_update_assistant",
    "vapi_update_full_ptbr",
    "vapi_webhook_server",
    "voice_humanizer",
]
ENV_KEYS = (
    "ANTHROPIC_API_KEY",
    "ELEVENLABS_API_KEY",
    "VAPI_API_KEY",
    "VAPI_ASSISTANT_ID",
    "VAPI_VOICE_ID_V5_BR",
)


@pytest.fixture
def sem_opcionais(monkeypatch: pytest.MonkeyPatch):
    """Simula ambiente sem as dependencias opcionais e com credenciais de teste."""
    for key in ENV_KEYS:
        monkeypatch.setenv(key, "teste")
    real_import = builtins.__import__

    def fake(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name.split(".")[0] in OPTIONAL:
            raise ImportError(f"blocked for test: {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake)
    for mod in [m for m in sys.modules if m == PKG or m.startswith(PKG + ".")]:
        monkeypatch.delitem(sys.modules, mod)
    for mod in OPTIONAL:
        monkeypatch.delitem(sys.modules, mod, raising=False)


def test_pacote_importa_sem_opcionais(sem_opcionais):
    importlib.import_module(PKG)


@pytest.mark.parametrize("name", MODULES)
def test_modulo_importa_sem_opcionais(sem_opcionais, name):
    importlib.import_module(f"{PKG}.{name}")


def test_orchestrator_falha_claro_sem_anthropic(sem_opcionais):
    mod = importlib.import_module(f"{PKG}.orchestrator")
    assert mod.Anthropic is None
    orch = mod.JarvisOrchestrator.__new__(mod.JarvisOrchestrator)
    orch.config = mod.Config
    with pytest.raises((ImportError, ValueError)):
        orch.__init__()


def test_tts_handler_falha_claro_sem_elevenlabs(sem_opcionais):
    mod = importlib.import_module(f"{PKG}.tts_handler")
    assert mod.ELEVENLABS_V2 is None
    with pytest.raises(ImportError, match="pip install elevenlabs"):
        mod.TTSHandler()
    with pytest.raises(ImportError, match="pip install elevenlabs"):
        mod.TTSHandlerSimple()


def test_tts_sesame_device_cpu_sem_torch(sem_opcionais):
    mod = importlib.import_module(f"{PKG}.tts_sesame")
    assert mod.DEVICE == "cpu"
    with pytest.raises(ImportError, match="pip install torch"):
        mod.SesameTTSHandler()


@pytest.mark.parametrize("name", ["vapi_update_assistant", "vapi_update_full_ptbr"])
def test_vapi_update_tem_sintaxe_valida(name):
    ast.parse((VOICE_DIR / f"{name}.py").read_text(encoding="utf-8"))


SEM_CREDENCIAIS = [
    "jarvis_narrator",
    "jarvis_terminal",
    "vapi_update_assistant",
    "vapi_update_full_ptbr",
]


@pytest.mark.parametrize("name", SEM_CREDENCIAIS)
def test_modulo_importa_sem_credenciais(monkeypatch, name):
    """Import nao exige chave de API; a falta so e reportada ao usar."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("engine.config.get_config", lambda key, default=None: default)
    for mod in [m for m in sys.modules if m == PKG or m.startswith(PKG + ".")]:
        monkeypatch.delitem(sys.modules, mod)
    importlib.import_module(f"{PKG}.{name}")


def test_vapi_falha_claro_sem_credenciais(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("engine.config.get_config", lambda key, default=None: default)
    for mod in [m for m in sys.modules if m == PKG or m.startswith(PKG + ".")]:
        monkeypatch.delitem(sys.modules, mod)
    mod = importlib.import_module(f"{PKG}.vapi_update_assistant")
    with pytest.raises(ValueError, match="VAPI_API_KEY"):
        mod.update_assistant()
