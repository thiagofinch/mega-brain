#!/usr/bin/env python3
"""
Chronicler Emission Backstop -- Story MCE-14.6

Stop-event hook que garante emissao do Chronicler MCE Pipeline Log v3.0
para qualquer pipeline que terminou em estado 'complete' sem ter emitido
o log (escape route de exit paths novos nao cobertos por cmd_finalize/
cmd_auto_advance/cmd_recover).

Idempotente: skip se marker chronicler-emitted.json ja existe.
Fire-and-forget: spawna subprocess emit-chronicler e sai.

Constraints:
- stdlib + PyYAML apenas
- Exit 0 sempre -- nunca bloqueia Stop event
- Silent skip em qualquer erro de leitura de state
- Nao espera subprocess (fire-and-forget, start_new_session=True)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # PyYAML deve estar disponivel, mas se faltar, skip silent
    sys.exit(0)

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def find_gaps(root: Path) -> list[str]:
    """Retorna lista de slugs com state=complete mas sem marker chronicler-emitted.json."""
    mce_dir = root / ".claude" / "mission-control" / "mce"
    if not mce_dir.exists():
        return []

    gaps: list[str] = []
    for slug_dir in mce_dir.iterdir():
        if not slug_dir.is_dir():
            continue

        state_yaml = slug_dir / "pipeline_state.yaml"
        marker = slug_dir / "chronicler-emitted.json"

        if not state_yaml.exists():
            continue
        if marker.exists():
            continue  # ja emitido -- idempotencia

        try:
            data = yaml.safe_load(state_yaml.read_text(encoding="utf-8"))
        except Exception:
            continue  # malformed ou permissao -- skip silent

        if not isinstance(data, dict):
            continue
        if data.get("state") != "complete":
            continue

        gaps.append(slug_dir.name)

    return gaps


def spawn_emit(root: Path, slug: str) -> None:
    """Fire-and-forget subprocess para emitir chronicler de um slug."""
    cmd = [
        sys.executable,
        "-m",
        "engine.intelligence.pipeline.mce.orchestrate",
        "emit-chronicler",
        slug,
    ]
    subprocess.Popen(
        cmd,
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
        env=os.environ.copy(),
    )
    # Nao chama .wait() -- fire-and-forget intencional


def main() -> int:
    try:
        gaps = find_gaps(PROJECT_ROOT)
        for slug in gaps:
            spawn_emit(PROJECT_ROOT, slug)
        # Nao imprime nada quando nao ha gaps -- saida rapida e limpa
    except Exception as exc:
        # Hook nunca bloqueia Stop event em caso de excecao inesperada
        print(
            f"[chronicler_emission_backstop] warning: {exc}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
