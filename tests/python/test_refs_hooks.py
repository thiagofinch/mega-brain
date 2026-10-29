"""Referencias a artefatos ausentes na release publica: hooks degradam sem ruido."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"


def _run_hook(name: str, payload: dict | None = None, cwd: Path = ROOT):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(cwd), "PYTHONUTF8": "1"}
    runner = ["node"] if name.endswith(".js") else [sys.executable, "-B"]
    return subprocess.run(
        [*runner, str(HOOKS / name)],
        input=json.dumps(payload or {}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(cwd),
        timeout=30,
    )


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"hook_{name}", HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "name",
    [
        "brain_first_lookup.py",
        "stop_workspace_audit.py",
        "promotion_detector_hook.py",
        "memory_persistence.py",
        "constitution_gate.py",
        "capability_enforcement.py",
        "governance_auto_update.py",
        "structure-validation.py",
    ],
)
def test_hook_sem_artefato_sai_limpo(name):
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(ROOT / "mega-brain-core" / "constitution.md")},
        "hook_event_name": "Stop",
    }
    r = _run_hook(name, payload)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == ""
    assert r.stderr.strip() == ""


def test_precompact_digest_e_noop_silencioso():
    import shutil

    if shutil.which("node") is None:
        pytest.skip("node indisponivel")
    r = _run_hook("precompact-session-digest.js")
    assert r.returncode == 0
    assert r.stdout.strip() == "" and r.stderr.strip() == ""


def test_startup_health_alinhado_com_engine_paths():
    mod = _load("startup_health")
    assert "docs/governance/rules" not in mod.CRITICAL_DIRS
    import engine.paths as paths

    for name in mod.PATHS_SPOT_CHECKS:
        assert hasattr(paths, name)
    r = _run_hook("startup_health.py")
    assert r.returncode == 0
    assert "Missing" not in r.stdout
    assert "artifacts/audit" not in r.stdout


def test_workspace_contract_guard_sem_consulta_a_registry():
    mod = _load("workspace_contract_guard")
    assert not hasattr(mod, "_schema_check")
    src = (HOOKS / "workspace_contract_guard.py").read_text(encoding="utf-8")
    assert "engine.governance" not in src


def test_pipeline_orchestrator_usa_compilador_existente():
    src = (HOOKS / "pipeline_orchestrator.py").read_text(encoding="utf-8")
    assert "dossier_compiler_adapter" not in src
    from engine.intelligence.dossier.dossier_compiler import compile_dossier

    assert callable(compile_dossier)


def test_pipeline_orchestrator_create_repetido_nao_duplica_dossie(tmp_path, monkeypatch):
    # O V1 anexa secao incremental se o dossie existe; um CREATE repetido so pode criar.
    import engine.intelligence.dossier.dossier_compiler as v1

    monkeypatch.setattr(v1, "_BUCKET_MAP", {"external": tmp_path})
    calls = []
    monkeypatch.setattr(v1, "compile_dossier", lambda **kw: calls.append(kw) or tmp_path / "x.md")
    mod = _load("pipeline_orchestrator")
    trigger_log = tmp_path / "triggers.jsonl"
    trigger_log.write_text(json.dumps({"decision": "CREATE", "tema": "vendas", "category": "themes"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(mod, "_TRIGGER_LOG", trigger_log)
    monkeypatch.setattr(mod, "_log_event", lambda *a, **k: None)

    assert mod._route_dossier_compiler(str(trigger_log)) is True
    assert len(calls) == 1
    (tmp_path / "dossiers" / "themes").mkdir(parents=True)
    (tmp_path / "dossiers" / "themes" / "DOSSIER-VENDAS.md").write_text("# Vendas\n", encoding="utf-8")
    assert mod._route_dossier_compiler(str(trigger_log)) is True
    assert len(calls) == 1


def test_memory_capture_grava_via_memory_manager(tmp_path, monkeypatch):
    import engine.intelligence.memory_manager as mm

    monkeypatch.setattr(mm, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(mm, "_stores", {})
    mod = _load("memory_capture")
    assert mod._HAS_MEMORY_MANAGER is True
    mod.write_memory_entry("dev", {"summary": "resumo da execucao", "tool": "Agent"})
    lines = (tmp_path / "dev" / "memories.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["content"] == "resumo da execucao"


def test_memory_manager_stop_poda_agentes(tmp_path, monkeypatch):
    import engine.intelligence.memory_manager as mm

    monkeypatch.setattr(mm, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(mm, "_stores", {})
    mm.memory_write("qa", "memoria util", importance=0.9)
    mod = _load("memory_manager_stop")
    assert mod._HAS_MEMORY_MANAGER is True
    monkeypatch.setattr(mod, "_MM_DIR", tmp_path)
    stats = mod._mm_cleanup_all()
    assert stats and stats[0]["agent_id"] == "qa"
    assert stats[0]["after"] == 1


def test_structure_validation_sem_workspace_yaml_nao_quebra(tmp_path):
    r = _run_hook("structure-validation.py", cwd=tmp_path)
    assert r.returncode == 0
    assert "Traceback" not in r.stderr


def test_session_start_compila_em_python_311():
    import ast

    ast.parse((HOOKS / "session_start.py").read_text(encoding="utf-8"))
    mod = _load("session_start")
    texto = mod.generate_personality_injection({})
    assert "Elogio invertido" in texto and "De fato, senhor." in texto


def test_hook_auditor_sem_falsos_positivos():
    r = _run_hook("hook_auditor.py")
    assert r.returncode == 0
    assert "Issues" not in r.stdout


def test_memory_persistence_e_noop_sem_provider():
    mod = _load("memory_persistence")
    assert mod.handle_stop({})["result"] == "skip"
    assert mod.handle_session_start({})["result"] == "skip"
    src = (HOOKS / "memory_persistence.py").read_text(encoding="utf-8")
    assert "memory_supabase" not in src.replace("provider de memoria Supabase", "")


def test_invalidate_capability_embeddings_usa_glob_do_diretorio_registry():
    mod = _load("invalidate_capability_embeddings")
    assert mod._matches_trigger("agents/_registry/qualquer.yaml")
    assert mod._matches_trigger(".claude/skills/x/business-context.md")
    assert not mod._matches_trigger("README.md")
