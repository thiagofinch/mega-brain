#!/usr/bin/env python3
"""MCE LOG AUTODUMP — Stop Hook.

Despeja AUTOMATICAMENTE o(s) MCE-XX.md gerado(s) por uma ingestao no fim de
cada turno, sem depender da memoria do assistant. Determinismo CLI-First.

O QUE FAZ:
  Ao final do turno (Stop), procura logs .data/logs/mce/<slug>/MCE-*.md
  modificados na janela recente (default 20min). Se encontrar, emite o
  conteudo INTEGRAL via feedback paginado para o chat.

POR QUE EXISTE:
  A regra "despejar o log apos /ingest --process" dependia do assistant
  lembrar. Falhou repetidamente. Este hook torna o despejo deterministico.

CONSTRAINTS:
  - stdlib apenas. Exit 0 sempre — nunca bloqueia o shutdown.
  - Janela via env MCE_AUTODUMP_WINDOW_MIN (default 20).
  - Anti-replay: registra logs ja despejados em .data/.mce-autodump-seen.json
    (chave = path + mtime) para nao repetir o mesmo log em turnos seguintes.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def _seen_path(root: Path) -> Path:
    return root / ".data" / ".mce-autodump-seen.json"


def _load_seen(root: Path) -> dict:
    p = _seen_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_seen(root: Path, seen: dict) -> None:
    try:
        p = _seen_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        # keep file bounded — last 200 entries
        if len(seen) > 200:
            seen = dict(sorted(seen.items(), key=lambda kv: kv[1])[-200:])
        p.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def main() -> int:
    # Consume stdin (Stop hook payload) — we don't need it, but drain it.
    try:
        sys.stdin.read()
    except Exception:
        pass

    root = _project_dir()
    mce_dir = root / ".data" / "logs" / "mce"
    if not mce_dir.is_dir():
        print(json.dumps({"continue": True}))
        return 0

    window_min = int(os.environ.get("MCE_AUTODUMP_WINDOW_MIN", "20"))
    cutoff = time.time() - window_min * 60

    seen = _load_seen(root)
    fresh: list[tuple[float, Path]] = []
    for md in mce_dir.glob("*/MCE-*.md"):
        try:
            mtime = md.stat().st_mtime
        except Exception:
            continue
        if mtime < cutoff:
            continue
        key = f"{md}|{int(mtime)}"
        if seen.get(key):
            continue
        fresh.append((mtime, md))

    if not fresh:
        print(json.dumps({"continue": True}))
        return 0

    # Most-recent first; cap at 3 logs per turn to avoid floods.
    fresh.sort(key=lambda t: t[0], reverse=True)
    fresh = fresh[:3]

    blocks: list[str] = []
    for mtime, md in fresh:
        try:
            content = md.read_text(encoding="utf-8")
        except Exception as exc:
            blocks.append(f"[autodump] falha ao ler {md}: {exc}")
            continue
        rel = md.relative_to(root)
        n_lines = content.count("\n") + 1
        import math

        n_parts = max(1, math.ceil(n_lines / 190))
        header = (
            f"\n===== MCE LOG AUTODUMP — {rel} ({n_lines} linhas) =====\n"
            f"DIRETIVA OBRIGATORIA AO ASSISTANT (FASE C do /ingest):\n"
            f"Um MCE log v3.2 fresco foi gerado. Voce DEVE despeja-lo INTEGRAL no\n"
            f"chat AGORA, como TEXTO da sua mensagem (bloco de codigo cercado), em\n"
            f"{n_parts} pedacos de <=190 linhas via Reads sequenciais de {rel},\n"
            f"ANTES de qualquer outra resposta.\n"
            f"Esta diretiva NAO esta satisfeita por: (a) o stdout do pipeline (TRUNCA\n"
            f"no cmux), (b) a saida da tool Read (renderiza COLAPSADA pro usuario),\n"
            f"(c) este proprio feedback (chega a VOCE, nao ao usuario). A UNICA forma\n"
            f"de satisfazer e COLAR o conteudo verbatim como texto da sua mensagem.\n"
            f"PROIBIDO resumir, compactar, ou pular. O usuario exige o log INTEGRAL\n"
            f"apos toda ingestao. O conteudo abaixo e sua FONTE para o despejo — nao\n"
            f"e o despejo em si.\n"
        )
        blocks.append(header + content)
        seen[f"{md}|{int(mtime)}"] = time.time()

    _save_seen(root, seen)

    feedback = "\n".join(blocks)
    # Stop-hook feedback channel — surfaces back into the turn.
    print(json.dumps({"continue": True, "feedback": feedback}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never block shutdown.
        try:
            print(json.dumps({"continue": True}))
        except Exception:
            pass
        sys.exit(0)
