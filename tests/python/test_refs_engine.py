"""Referencias a artefatos ausentes na release publica: degradacao limpa no engine."""

from __future__ import annotations

import importlib
import json
import inspect
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_mce_init_nao_exporta_render_pipeline_audit():
    mce = importlib.import_module("engine.intelligence.pipeline.mce")
    assert "render_pipeline_audit" not in mce.__all__
    assert not hasattr(mce, "render_pipeline_audit")


def test_trigger_cascading_sem_modulo_retorna_false(tmp_path):
    from engine.intelligence.pipeline.batch_auto_creator import trigger_cascading

    assert trigger_cascading(tmp_path / "batch.md") is False


def test_theme_router_sem_config_usa_auto_discovery():
    from engine.intelligence.pipeline.mce.theme_router import ThemeRouter

    router = ThemeRouter()
    path = router.resolve({"category": "METODOLOGIA"})
    assert path.name == "dossier-metodologia.md"
    assert router.resolve({}).name == "dossier-general.md"


def test_theme_router_com_config_explicita(tmp_path):
    from engine.intelligence.pipeline.mce.theme_router import ThemeRouter

    cfg = tmp_path / "routes.yaml"
    cfg.write_text(
        yaml.safe_dump({"routes": {"vendas": {"dossier_path": "x/dossier-vendas.md"}}}),
        encoding="utf-8",
    )
    router = ThemeRouter(config_path=cfg)
    assert router.resolve({"category": "vendas"}).name == "dossier-vendas.md"


def test_theme_agent_map_sem_config_fica_desligado():
    from engine.intelligence.pipeline.mce.theme_agent_map import ThemeAgentMap

    tmap = ThemeAgentMap()
    assert tmap._loaded is False


def test_context_scorer_config_padrao_e_env(monkeypatch):
    from engine.intelligence import context_scorer

    monkeypatch.delenv("MCE_CROSS_EXPERT_THRESHOLD", raising=False)
    assert context_scorer._load_cross_expert_config()["similarity_threshold"] == 0.65
    monkeypatch.setenv("MCE_CROSS_EXPERT_THRESHOLD", "0.8")
    assert context_scorer._load_cross_expert_config()["similarity_threshold"] == 0.8


def test_scope_classifier_pesos_embutidos():
    from engine.intelligence.pipeline import scope_classifier as sc

    weights = sc._load_weights()
    assert weights == sc._DEFAULT_WEIGHTS
    assert weights is not sc._DEFAULT_WEIGHTS
    assert sc.PATH_INBOX_WEIGHT == 10


def test_pgvector_get_client_sem_providers_da_erro_claro(monkeypatch):
    from engine.intelligence.rag.pgvector_store import PgVectorStore

    monkeypatch.delenv("DATABASE_URL", raising=False)
    store = PgVectorStore(bucket="external")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        store._get_client()


def test_hybrid_query_rrf_sem_backend_retorna_none(monkeypatch):
    from engine.intelligence.rag import hybrid_query

    for var in ("DATABASE_URL", "SUPABASE_URL"):
        monkeypatch.delenv(var, raising=False)
    assert hybrid_query._try_rrf_retrieve("q", "external", 5) is None


def test_orchestrate_sem_referencia_a_governanca_ausente():
    from engine.intelligence.pipeline.mce import orchestrate

    assert not hasattr(orchestrate, "_run_lifecycle_governance_safe")
    src = inspect.getsource(orchestrate)
    assert "engine.governance" not in src
    assert "registry_publisher" not in src


def test_pipeline_heal_pula_file_registry_ausente(tmp_path):
    from engine.intelligence.pipeline.pipeline_heal import PipelineHealDetector

    det = PipelineHealDetector(project_root=tmp_path)
    assert det._check_file_registry("SRC-1") is None
    report = det.detect("SRC-1")
    assert all(c.step_id != "P8.1.2" for c in report.checks)


def test_pipeline_heal_nav_map_aponta_para_knowledge_external(tmp_path):
    from engine.intelligence.pipeline.pipeline_heal import PipelineHealDetector

    nav = tmp_path / "knowledge" / "external"
    nav.mkdir(parents=True)
    (nav / "NAVIGATION-MAP.json").write_text(json.dumps({"SRC-1": {}}), encoding="utf-8")
    det = PipelineHealDetector(project_root=tmp_path)
    assert det._check_nav_map("SRC-1").passed is True


def test_orglive_default_bu_sem_config_de_workspace(monkeypatch):
    from engine.intelligence.pipeline.mce import orglive_sync

    monkeypatch.setattr(orglive_sync, "_workspace_businesses", lambda: ROOT / "nao-existe")
    monkeypatch.setenv("MEGA_BRAIN_DEFAULT_BU", "acme")
    assert orglive_sync._resolve_default_bu() == "acme"


def test_qa_gates_sem_referencia_a_mce_yaml_ausente():
    from engine.intelligence.pipeline.mce import qa_gates

    assert not hasattr(qa_gates, "_load_gates")
    assert "workflows/mce.yaml" not in inspect.getsource(qa_gates)


def test_rebuild_nao_importa_tagging_ausente():
    from engine.intelligence.rag import rebuild

    src = inspect.getsource(rebuild)
    assert "from .tagging" not in src
    assert rebuild._source_content_sha("") is None
    assert rebuild._source_content_sha("nao/existe.txt") is None


def test_rebuild_sha_de_arquivo_existente(tmp_path):
    import hashlib

    from engine.intelligence.rag import rebuild

    f = tmp_path / "a.txt"
    f.write_bytes(b"conteudo")
    assert rebuild._source_content_sha(str(f)) == hashlib.sha256(b"conteudo").hexdigest()


def test_embedder_fallback_ollama_ausente_levanta_erro_tipado(monkeypatch):
    from engine.intelligence.pipeline import embedder

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(embedder.EmbeddingFailedError):
        embedder.embed_chunks([{"chunk_id": "c1", "text": "ola mundo"}])


def test_yaml_workflows_validos_e_alvos_existem():
    wf = ROOT / "engine" / "workflows" / "wf-conclave.yaml"
    cr = ROOT / "engine" / "jarvis" / "agent-creator" / "workflows" / "wf-create-agent.yaml"
    for f in (wf, cr):
        yaml.safe_load(f.read_text(encoding="utf-8"))
    for rel in (
        "agents/system/conclave/critic.md",
        "agents/system/conclave/devils-advocate.md",
        "agents/system/conclave/synthesizer.md",
        "engine/jarvis/protocols/CONSTITUTION.md",
        "agents/_templates/TEMPLATE-AGENT-MD-ULTRA-ROBUSTO-V3.md",
        "engine/templates/agents/soul-template.md",
        "agents/_registry/ecosystem-registry.yaml",
    ):
        assert (ROOT / rel).is_file(), rel
        assert rel in wf.read_text(encoding="utf-8") + cr.read_text(encoding="utf-8")


def test_qrels_baseline_json_valido():
    path = ROOT / "engine" / "intelligence" / "rag" / "qrels-baseline.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "tests/rag" not in data["_description"]


def test_activation_generator_sem_master_registry():
    from engine.intelligence.agents import activation_generator

    assert not hasattr(activation_generator, "_update_master_registry")
    assert "_master-registry" not in inspect.getsource(activation_generator)
