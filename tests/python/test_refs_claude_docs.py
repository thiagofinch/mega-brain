"""Garante que docs/configs de .claude nao citam caminhos ausentes da release publica."""
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
YAMLS = [
    ".claude/agents.yaml",
    ".claude/skills/chronicler/chronicler-registry.yaml",
    ".claude/skills/extract-knowledge/config.yaml",
    ".claude/skills/extract-session-heuristics/config.yaml",
]
MORTOS = [
    "mega-brain-core/constitution.md",
    "agents/persona-registry.yaml",
    "saas-api-readiness.yaml",
    "capability-registry.yaml",
    "squads/squad-creator-pro/",
    "services/etl/",
    "superagent-registry.yaml",
    "service-catalog.yaml",
    "engine/schemas/ingestion-guard.schema.json",
]
ARQUIVOS = [
    ".claude/CLAUDE.md",
    ".claude/agents.yaml",
    ".claude/rules/saas-tool-routing.md",
    ".claude/rules/session-preflight.md",
    ".claude/rules/clickup-description.md",
    ".claude/rules/skill-standards.md",
    ".claude/rules/online-publishing.md",
    ".claude/skills/chronicler/chronicler-registry.yaml",
    ".claude/skills/extract-knowledge/config.yaml",
    ".claude/skills/extract-session-heuristics/config.yaml",
]


@pytest.mark.parametrize("rel", YAMLS)
def test_yaml_valido(rel):
    assert isinstance(yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")), dict)


@pytest.mark.parametrize("rel", ARQUIVOS)
def test_sem_referencias_mortas(rel):
    texto = (ROOT / rel).read_text(encoding="utf-8")
    for morto in MORTOS:
        assert morto not in texto, f"{rel} cita {morto}"


@pytest.mark.skipif(
    shutil.which("node") is None or not (ROOT / "node_modules" / "js-yaml").exists(),
    reason="node ou js-yaml ausente",
)
def test_operator_bootstrap_degrada_sem_setter(tmp_path):
    lib = ROOT / ".claude/skills/extract-session-heuristics/scripts/lib"
    codigo = (
        "const b=require(process.argv[1]);"
        "const r=b.writeBackViaSetter('x');"
        "console.log(JSON.stringify({ok:r.success,err:r.stderr}));"
    )
    saida = subprocess.run(
        ["node", "-e", codigo, str(lib / "operator-bootstrap.js")],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
    )
    assert saida.returncode == 0, saida.stderr
    assert '"ok":false' in saida.stdout and "ausente" in saida.stdout
