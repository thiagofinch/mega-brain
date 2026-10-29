"""O gate de publicacao (bin/pre-publish-gate.js) bloqueia qualquer arquivo nao-L1 no pacote.

A release 2.0 renomeou core/ -> engine/ sem atualizar audit_layers.L1_PATTERNS, e o
classificador usava separador do SO (no Windows nenhum padrao com "/" casava).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "intelligence" / "validation"))

from audit_layers import classify_path  # noqa: E402


def _package_files():
    entries = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["files"]
    found = []
    for entry in entries:
        target = ROOT / entry
        if target.is_file():
            found.append(target)
        elif target.is_dir():
            found.extend(
                p for p in target.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
            )
    return found


def test_tudo_que_o_pacote_distribui_e_l1():
    files = _package_files()
    assert len(files) > 500
    violations = [
        (p.relative_to(ROOT).as_posix(), *classify_path(p, ROOT, is_file=True))
        for p in files
    ]
    violations = [v for v in violations if v[1] != "L1"]
    assert violations == []


@pytest.mark.parametrize(
    ("rel", "layer"),
    [
        ("engine/paths.py", "L1"),
        ("LICENSE", "L1"),
        (".env", "NEVER"),
        ("knowledge/external/dossiers/x.md", "L2"),
        ("inbox/material.txt", "L3"),
    ],
)
def test_classificacao_por_camada(rel, layer):
    assert classify_path(ROOT / rel, ROOT, is_file=True)[0] == layer
