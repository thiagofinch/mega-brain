"""Referencias ausentes na area scripts/bin degradam de forma limpa."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASH = shutil.which("bash")


@pytest.mark.skipif(BASH is None, reason="bash indisponivel")
@pytest.mark.parametrize(
    "script,missing",
    [
        ("refresh-tag-resolver.sh", "scripts/create-tag-resolver.py"),
        ("refresh-navigation-map.sh", "scripts/build-navigation-map.py"),
    ],
)
def test_refresh_scripts_degradam_sem_script_ausente(script, missing):
    src = (ROOT / "bin" / script).read_text(encoding="utf-8")
    assert missing not in src
    r = subprocess.run(
        [BASH, str(ROOT / "bin" / script), "--force"],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
    )
    assert r.returncode == 0
    assert "nao existe" in r.stdout or "não existe" in r.stdout


def test_mega_brain_js_mensagem_clara_sem_operations():
    src = (ROOT / "bin" / "mega-brain.js").read_text(encoding="utf-8")
    assert "operations.py" not in src and "engine.operations" not in src
    assert "SLASH_ONLY_COMMANDS" in src


def test_routing_index_nao_cita_arquivos_ausentes():
    src = (ROOT / "scripts" / "build-agent-routing-index.js").read_text(encoding="utf-8")
    assert "tool-capability-registry" not in src
    assert "routing-semantics-spec" not in src
