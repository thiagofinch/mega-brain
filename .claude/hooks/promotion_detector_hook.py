#!/usr/bin/env python3
"""PostToolUse hook: promotion-detector apos o cmd_finalize (no-op nesta distribuicao).

Na instalacao completa, disparava o detector de promocao (script auxiliar)
sem bloquear, logo depois de o cmd_finalize do pipeline MCE escrever seus
artefatos. Esse detector nao faz parte desta distribuicao publica, entao o
hook e um no-op silencioso: consome o stdin, nao escreve log nem imprime nada.
Segue registrado em settings.json para nao alterar a fiacao.

Fail-open: nunca bloqueia o pipeline.

Hook: PostToolUse | Matcher: Write|Edit|Bash | Timeout: 8000ms
Story: STORY-MCE-6.0 Phase 6
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        sys.stdin.read()  # contrato do hook: consumir o stdin
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
