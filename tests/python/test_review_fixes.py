"""Regressoes achadas na revisao das correcoes de import (state_writer, locks, PID, .env, voz)."""

import errno
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.config import _parse_env_line  # noqa: E402
from engine.intelligence.pipeline import _file_lock  # noqa: E402
from engine.intelligence.pipeline.parallel_dispatch import SubagentBridge  # noqa: E402
from engine.intelligence.pipeline.slug_lock import SlugLockManager  # noqa: E402
from engine.intelligence.pipeline.state_writer import SafeStateWriter  # noqa: E402


def test_safe_state_writer_grava_json(tmp_path):
    # a variavel local "lock_file" escondia a funcao importada (TypeError em toda plataforma)
    target = tmp_path / "state.json"
    with SafeStateWriter(target) as data:
        data["fase"] = 3
    with SafeStateWriter(target) as data:
        data["batch"] = 7
    assert json.loads(target.read_text(encoding="utf-8")) == {"fase": 3, "batch": 7}


def test_subagent_bridge_atualiza_manifest_sem_fcntl(tmp_path):
    bridge = SubagentBridge("slug-teste", project_root=tmp_path)
    bridge.start_file("inbox/a.txt")
    bridge.complete_file("inbox/a.txt", success=False, error="falhou")
    manifest = json.loads((tmp_path / ".data" / "PROCESSED-MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["slug-teste/a.txt"] == {"status": "failed", "error": "falhou", "slug": "slug-teste"}


def test_pid_vivo_e_encerrado(tmp_path):
    mgr = SlugLockManager(base_dir=tmp_path)
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    assert mgr._is_pid_alive(os.getpid()) is True
    assert mgr._is_pid_alive(proc.pid) is False


@pytest.mark.skipif(sys.platform != "win32", reason="caminho msvcrt")
def test_lock_windows_nao_trava_em_erro_que_nao_e_contencao(monkeypatch, tmp_path):
    fd = os.open(str(tmp_path / "x.lock"), os.O_CREAT | os.O_RDWR)

    def falha(*_args):
        raise OSError(errno.EBADF, "bad file descriptor")

    monkeypatch.setattr(_file_lock.msvcrt, "locking", falha)
    try:
        with pytest.raises(OSError) as info:
            _file_lock.lock_file(fd)
        assert info.value.errno == errno.EBADF
        assert not isinstance(info.value, BlockingIOError)
    finally:
        os.close(fd)


@pytest.mark.parametrize(
    ("linha", "esperado"),
    [
        ("OPENAI_API_KEY=   # preencher", ("OPENAI_API_KEY", "")),
        ("OPENAI_API_KEY=sk-x # comentario", ("OPENAI_API_KEY", "sk-x")),
        ('NOME="valor # com hash"', ("NOME", "valor # com hash")),
    ],
)
def test_env_comentarios(linha, esperado):
    assert _parse_env_line(linha) == esperado


def test_importar_servidores_de_voz_nao_grava_no_repo():
    # o conector era criado no import e gravava engine/jarvis/.claude/ dentro da arvore
    code = (
        "import importlib\n"
        "for m in ('engine.jarvis.voice.server', 'engine.jarvis.voice.vapi_webhook_server'):\n"
        "    try:\n"
        "        importlib.import_module(m)\n"
        "    except ModuleNotFoundError:\n"
        "        pass  # fastapi/flask opcionais\n"
    )
    antes = {p for p in ROOT.rglob("STATE.json") if ".git" not in p.parts}
    subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, check=True, capture_output=True)
    depois = {p for p in ROOT.rglob("STATE.json") if ".git" not in p.parts}
    assert depois == antes
    assert not (ROOT / "engine" / "jarvis" / ".claude").exists()
