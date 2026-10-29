"""
File Lock — advisory inter-process lock portavel (POSIX + Windows).

Em POSIX usa ``fcntl.flock`` exatamente como os modulos do pipeline faziam
antes (LOCK_EX / LOCK_SH / LOCK_NB / LOCK_UN). No Windows, onde ``fcntl`` nao
existe, usa ``msvcrt.locking``.

Notas do caminho Windows:
- ``msvcrt.locking`` trava N bytes a partir da posicao atual do arquivo. Aqui
  travamos 1 byte numa posicao sentinela bem alem do conteudo (``_LOCK_OFFSET``),
  entao os dados reais nunca ficam bloqueados para leitura por outros handles
  (o lock do Windows e obrigatorio, nao advisory). Travar alem do EOF e valido.
- A posicao do descritor e salva e restaurada em cada chamada.
- Nao ha lock compartilhado: ``shared=True`` vira exclusivo no Windows.
- Lock bloqueante = laco de tentativas nao bloqueantes (LK_NBLCK) com sleep,
  sem limite de tempo (o LK_LOCK nativo desiste apos ~10 s).
- Lock nao bloqueante que falha levanta ``BlockingIOError``, como o ``fcntl``.

Usage:
    from engine.intelligence.pipeline._file_lock import lock_file, unlock_file

    lock_file(fd)                    # exclusivo, bloqueia (flock LOCK_EX)
    lock_file(fd, blocking=False)    # BlockingIOError se ocupado
    unlock_file(fd)
"""

from __future__ import annotations

import errno
import os
import sys
import time
from typing import IO

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import msvcrt
else:
    import fcntl

# Byte sentinela (Windows): longe do conteudo para nao bloquear leituras.
_LOCK_OFFSET = 1 << 30
_RETRY_INTERVAL = 0.05
# Erros que o msvcrt.locking usa para "byte ja travado por outro handle".
_CONTENTION_ERRNOS = {errno.EACCES, errno.EDEADLK, errno.EAGAIN}


def _fileno(handle: int | IO) -> int:
    return handle if isinstance(handle, int) else handle.fileno()


def lock_file(handle: int | IO, *, blocking: bool = True, shared: bool = False) -> None:
    """Adquire lock no descritor (int) ou arquivo aberto.

    Args:
        handle: fd inteiro ou objeto de arquivo.
        blocking: se False e o lock estiver ocupado, levanta BlockingIOError.
        shared: lock compartilhado (LOCK_SH). No Windows vira exclusivo.
    """
    fd = _fileno(handle)
    if not _IS_WINDOWS:
        flags = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
        if not blocking:
            flags |= fcntl.LOCK_NB
        fcntl.flock(fd, flags)
        return

    saved = os.lseek(fd, 0, os.SEEK_CUR)
    try:
        while True:
            os.lseek(fd, _LOCK_OFFSET, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return
            except OSError as exc:
                # So "ocupado" e contencao; fd invalido, sem suporte etc. sobem como no flock
                if exc.errno not in _CONTENTION_ERRNOS:
                    raise
                if not blocking:
                    raise BlockingIOError(*exc.args) from exc
            time.sleep(_RETRY_INTERVAL)
    finally:
        os.lseek(fd, saved, os.SEEK_SET)


def unlock_file(handle: int | IO) -> None:
    """Libera o lock adquirido por ``lock_file`` (OSError se nao estava travado)."""
    fd = _fileno(handle)
    if not _IS_WINDOWS:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return

    saved = os.lseek(fd, 0, os.SEEK_CUR)
    try:
        os.lseek(fd, _LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.lseek(fd, saved, os.SEEK_SET)
