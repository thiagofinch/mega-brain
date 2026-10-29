#!/usr/bin/env python3
"""
Brain-First Lookup Hook -- PreToolUse (no-op nesta distribuicao)
================================================================
Na instalacao completa, consultava o cerebro local primeiro (gate de
recuperacao "brain-first") antes de buscas externas (WebSearch/WebFetch) e
imprimia um resumo dos acertos locais. O gate de recuperacao que ele usava nao
faz parte desta distribuicao publica, entao o hook e um no-op silencioso:
consome o stdin, nao imprime nada e nunca bloqueia.

Hook: PreToolUse (matcher: WebSearch|WebFetch) | Timeout: 10s
Story: W4-001.4

EXIT CODES:
  0 -- ALLOW (sempre)
"""

import sys


def main() -> None:
    try:
        sys.stdin.read()  # contrato do hook: consumir o stdin
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
