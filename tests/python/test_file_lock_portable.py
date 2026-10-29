"""Testes do lock de arquivo portavel (POSIX + Windows)."""

import importlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = "engine.intelligence.pipeline"
MODULES = [
    "agent_gatekeeper",
    "preflight",
    "semantic_logger",
    "slug_lock",
    "state_writer",
    "parallel_dispatch",
]

sys.path.insert(0, str(ROOT))
from engine.intelligence.pipeline._file_lock import lock_file, unlock_file  # noqa: E402


@pytest.mark.parametrize("name", MODULES)
def test_import_sem_fcntl(name):
    try:
        importlib.import_module(f"{PKG}.{name}")
    except ModuleNotFoundError as exc:
        if exc.name in ("fcntl", "msvcrt"):
            raise
        pytest.skip(f"dependencia ausente fora do escopo do lock: {exc.name}")


def test_lock_unlock_fd(tmp_path):
    fd = os.open(str(tmp_path / "a.lock"), os.O_CREAT | os.O_RDWR)
    try:
        os.write(fd, b"dados")
        pos = os.lseek(fd, 0, os.SEEK_CUR)
        lock_file(fd)
        assert os.lseek(fd, 0, os.SEEK_CUR) == pos
        unlock_file(fd)
        lock_file(fd, blocking=False)
        unlock_file(fd)
    finally:
        os.close(fd)


def test_lock_unlock_file_object(tmp_path):
    with open(tmp_path / "q.jsonl", "a+", encoding="utf-8") as fh:
        lock_file(fh)
        fh.write("x\n")
        unlock_file(fh)


def test_conteudo_legivel_com_lock_por_outro_handle(tmp_path):
    p = tmp_path / "m.json"
    fd = os.open(str(p), os.O_CREAT | os.O_RDWR)
    try:
        lock_file(fd)
        os.write(fd, b'{"a": 1}')
        with open(p, encoding="utf-8") as other:
            assert other.read() == '{"a": 1}'
        unlock_file(fd)
    finally:
        os.close(fd)


def test_conflito_nao_bloqueante_entre_processos(tmp_path):
    path = tmp_path / "c.lock"
    code = textwrap.dedent(
        """
        import os, sys
        sys.path.insert(0, sys.argv[1])
        from engine.intelligence.pipeline._file_lock import lock_file
        fd = os.open(sys.argv[2], os.O_CREAT | os.O_RDWR)
        try:
            lock_file(fd, blocking=False)
        except BlockingIOError:
            sys.exit(42)
        sys.exit(0)
        """
    )
    env = dict(os.environ, PYTHONUTF8="1")

    def child():
        return subprocess.run(
            [sys.executable, "-B", "-c", code, str(ROOT), str(path)], env=env
        ).returncode

    fd = os.open(str(path), os.O_CREAT | os.O_RDWR)
    try:
        lock_file(fd)
        assert child() == 42
        unlock_file(fd)
        assert child() == 0
    finally:
        os.close(fd)


def test_conflito_nao_bloqueante_mesmo_processo(tmp_path):
    if sys.platform != "win32":
        pytest.skip("flock em dois fds do mesmo processo: validado no teste de processos")
    path = tmp_path / "d.lock"
    a = os.open(str(path), os.O_CREAT | os.O_RDWR)
    b = os.open(str(path), os.O_CREAT | os.O_RDWR)
    try:
        lock_file(a)
        with pytest.raises(BlockingIOError):
            lock_file(b, blocking=False)
        unlock_file(a)
        lock_file(b, blocking=False)
        unlock_file(b)
    finally:
        os.close(a)
        os.close(b)
