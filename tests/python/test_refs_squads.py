"""Referencias a artefatos ausentes na release publica (area squads)."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
OG = ROOT / "squads" / "orquestrador-global"
SCRIPT = OG / "scripts" / "detect-stalled-nodes.js"

NODE = shutil.which("node")


def _env_with_stub_modules(tmp: Path) -> dict:
    # js-yaml e declarado em package.json mas pode nao estar instalado; stub minimo
    mod = tmp / "node_modules" / "js-yaml"
    mod.mkdir(parents=True)
    (mod / "index.js").write_text(
        "module.exports={load:()=>({}),dump:()=>''};", encoding="utf-8"
    )
    env = dict(os.environ)
    env["NODE_PATH"] = str(tmp / "node_modules")
    return env


@pytest.mark.skipif(NODE is None, reason="node ausente")
def test_detect_stalled_nodes_sem_registry_degrada_limpo():
    with tempfile.TemporaryDirectory() as t:
        r = subprocess.run(
            [NODE, str(SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=_env_with_stub_modules(Path(t)),
        )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["valid"] is True
    assert out["stalled_count"] == 0
    assert out["registry_found"] is False


@pytest.mark.skipif(NODE is None, reason="node ausente")
def test_detect_stalled_nodes_registry_explicito_ausente_falha_claro():
    with tempfile.TemporaryDirectory() as t:
        r = subprocess.run(
            [NODE, str(SCRIPT), str(Path(t) / "nao-existe.yaml")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=_env_with_stub_modules(Path(t)),
        )
    assert r.returncode == 2
    assert "registry nao encontrado" in r.stderr


@pytest.mark.parametrize(
    "rel",
    [
        "config.yaml",
        "context.yaml",
        "squad.yaml",
        "data/execution-adapter-registry.yaml",
        "data/token-registry.yaml",
        "tasks/basic-orchestration-setup.yaml",
        "tasks/dispatch-to-megabrain-worker.yaml",
        "workflows/demand-to-delivery.yaml",
    ],
)
def test_yaml_editados_validos_sem_refs_mortas(rel):
    text = (OG / rel).read_text(encoding="utf-8")
    yaml.safe_load(text)
    for morto in (
        ".claude/rules/execution-logging.md",
        ".claude/skills/swarm-execute/SKILL.md",
        "squads/mega-brain/data/composition-rules.yaml",
        "docs/errata.md",
        "knowledge/TEAM-PATTERNS.md",
        "knowledge/TEAM-REGISTRY.md",
        "MASTER-PLAN-OG-RUNTIME-CLOSURE",
        ".claude/rules/on-demand/delegation-protocol.md",
        ".claude/skills/orquestrador-global/SKILL.md",
    ):
        assert morto not in text, (rel, morto)


def test_executor_ref_aponta_para_arquivo_existente():
    cfg = yaml.safe_load((OG / "config.yaml").read_text(encoding="utf-8"))
    ref = cfg["megabrain_extensions"]["executor_ref"]
    assert (ROOT / ref).is_file()
