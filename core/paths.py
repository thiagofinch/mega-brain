"""
core/paths.py — Directory Contract (machine-readable)

Single Source of Truth for all output paths in the Mega Brain system.
Equivalent to a centralized path registry.

Usage:
    from core.paths import ROUTING, LOGS, ARTIFACTS
    output_path = ROUTING["audit_report"] / "AUDIT-REPORT.json"
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── TRACKED (L1/L2) ──────────────────────────────────────────────
CORE = ROOT / "core"
AGENTS = ROOT / "agents"
REFERENCE = ROOT / "reference"
BIN = ROOT / "bin"
SYSTEM = ROOT / "system"
PLANNING = ROOT / ".planning"
CLAUDE = ROOT / ".claude"
RULES = CLAUDE / "rules"
SKILLS = CLAUDE / "skills"
HOOKS = CLAUDE / "hooks"
COMMANDS = CLAUDE / "commands"
WORKSPACE = ROOT / "workspace"  # Prescriptive business ops (L1 template, L2 populated)

# ── WORKSPACE: SYSTEM & TEMPLATES ─────────────────────────────────
WORKSPACE_SYSTEM = WORKSPACE / "_system"
WORKSPACE_TEMPLATES = WORKSPACE / "_templates"
WORKSPACE_INBOX = WORKSPACE / "inbox"

# ── WORKSPACE: 7 DEPARTMENTAL SPACES (ClickUp mirror) ────────────
WORKSPACE_AIOS = WORKSPACE / "aios"
WORKSPACE_OPS = WORKSPACE / "ops"
WORKSPACE_DELIVERY = WORKSPACE / "delivery"
WORKSPACE_COMERCIAL = WORKSPACE / "comercial"
WORKSPACE_GESTAO = WORKSPACE / "gestao"
WORKSPACE_GENTE_CULTURA = WORKSPACE / "gente-cultura"
WORKSPACE_MARKETING = WORKSPACE / "marketing"
WORKSPACE_STRATEGY = WORKSPACE / "strategy"

# ── WORKSPACE: BUSINESSES (DNA per BU, 12 folders each) ──────────
WORKSPACE_BUSINESSES = WORKSPACE / "businesses"

# ── WORKSPACE: KEY SUB-PATHS (pipeline output targets) ───────────
WORKSPACE_MEETINGS = WORKSPACE_OPS / "meetings"
WORKSPACE_EVENTOS = WORKSPACE_OPS / "eventos"
WORKSPACE_SPRINTS = WORKSPACE_OPS / "sprints"
WORKSPACE_FINANCE = WORKSPACE_GESTAO / "financeiro"
WORKSPACE_JURIDICO = WORKSPACE_GESTAO / "juridico"
WORKSPACE_ADMIN = WORKSPACE_GESTAO / "administrativo"
WORKSPACE_FERRAMENTAS = WORKSPACE_GESTAO / "acessos-ferramentas"
WORKSPACE_TEAM = WORKSPACE_GENTE_CULTURA / "equipe"
WORKSPACE_OKRS = WORKSPACE_GENTE_CULTURA / "okrs"
WORKSPACE_RECRUTAMENTO = WORKSPACE_GENTE_CULTURA / "recrutamento"
WORKSPACE_EDUCACIONAL = WORKSPACE_GENTE_CULTURA / "educacional"
WORKSPACE_WORKFLOWS = WORKSPACE_AIOS / "workflows"
WORKSPACE_CRM = WORKSPACE_COMERCIAL / "crm"

# Backward compat aliases (old names → new locations)
WORKSPACE_ORG = WORKSPACE_ADMIN  # was: WORKSPACE / "org"
WORKSPACE_AUTOMATIONS = WORKSPACE_WORKFLOWS  # was: WORKSPACE / "automations"
WORKSPACE_TOOLS = WORKSPACE_FERRAMENTAS  # was: WORKSPACE / "tools"

# Backward compat: root inbox/ no longer exists (S03 distributed to bucket inboxes).
INBOX = WORKSPACE / "inbox"

# ── GITIGNORED (L3 / Runtime) ────────────────────────────────────
LOGS = ROOT / "logs"
KNOWLEDGE = ROOT / "knowledge"
KNOWLEDGE_EXTERNAL = KNOWLEDGE / "external"
KNOWLEDGE_PERSONAL = KNOWLEDGE / "personal"
KNOWLEDGE_BUSINESS = KNOWLEDGE / "business"

# ── PERSONAL SUBDIRS (L3 only) ─────────────────────────────────
PERSONAL_EMAIL = KNOWLEDGE_PERSONAL / "email"
PERSONAL_MESSAGES = KNOWLEDGE_PERSONAL / "messages"
PERSONAL_CALLS = KNOWLEDGE_PERSONAL / "calls"
PERSONAL_COGNITIVE = KNOWLEDGE_PERSONAL / "cognitive"

# ── BUSINESS BUCKET SUBDIRS (L3 except scaffold) ──────────────
BUSINESS_INBOX = KNOWLEDGE_BUSINESS / "inbox"
BUSINESS_PEOPLE = KNOWLEDGE_BUSINESS / "people"
BUSINESS_DOSSIERS = KNOWLEDGE_BUSINESS / "dossiers"
BUSINESS_INSIGHTS = KNOWLEDGE_BUSINESS / "insights"
BUSINESS_NARRATIVES = KNOWLEDGE_BUSINESS / "narratives"
BUSINESS_DECISIONS = KNOWLEDGE_BUSINESS / "decisions"
BUSINESS_SOPS = KNOWLEDGE_BUSINESS / "sops"

# ── AGENT CATEGORY SUBDIRS (S06 reorganization) ────────────────
AGENTS_EXTERNAL = AGENTS / "external"
AGENTS_BUSINESS = AGENTS / "business"
AGENTS_PERSONAL = AGENTS / "personal"
AGENTS_SYSTEM = AGENTS / "system"
AGENTS_SYSTEM_KNOWLEDGE_OPS = AGENTS_SYSTEM / "knowledge-ops"
AGENTS_SYSTEM_DEV_OPS = AGENTS_SYSTEM / "dev-ops"
AGENTS_CARGO = AGENTS / "cargo"

PROCESSING = ROOT / "processing"
ARTIFACTS = ROOT / "artifacts"
DATA = ROOT / ".data"
RESEARCH = ROOT / "research"

# ── STATE (Gitignored, high-frequency writes) ────────────────────
MISSION_CONTROL = CLAUDE / "mission-control"
SESSIONS = CLAUDE / "sessions"
JARVIS = CLAUDE / "jarvis"
RAG_INDEX = DATA / "rag_index"
RAG_EXPERT = DATA / "rag_expert"
RAG_BUSINESS = DATA / "rag_business"
KNOWLEDGE_GRAPH = DATA / "knowledge_graph"
TRASH = CLAUDE / "trash"
AGENT_DISCOVERY = AGENTS / "discovery"

# ── BUSINESS UNIT TEMPLATE (12 standard folders per BU) ──────────
BU_TEMPLATE_DIRS = [
    "_preserved",
    "ai",
    "analytics",
    "brand",
    "company",
    "copy",
    "design-system",
    "evidence",
    "movement",
    "operations",
    "products",
    "tech",
]

# ── OUTPUT ROUTING ───────────────────────────────────────────────
# Scripts MUST use these constants instead of hardcoding paths.
# New scripts: import from here. Existing scripts: migrate incrementally.
ROUTING = {
    # Audit & validation outputs
    "audit_report": ARTIFACTS / "audit",
    "layer_validation": LOGS,
    # Session & state
    "session_log": SESSIONS,
    "mission_state": MISSION_CONTROL,
    "pipeline_state": MISSION_CONTROL,
    "skill_index": MISSION_CONTROL,
    "autosave_state": MISSION_CONTROL,
    "jarvis_state": JARVIS / "STATE.json",
    # Logs (append-only JSONL)
    "batch_log": LOGS / "batches",
    "handoff": LOGS / "handoffs",
    "cascade_log": LOGS,
    "tool_usage": LOGS,
    "quality_gaps": LOGS,
    "dossier_trigger": LOGS,
    "bucket_processing": LOGS / "bucket-processing",
    "autonomous_log": LOGS,
    # Knowledge & RAG
    "rag_chunks": RAG_EXPERT,
    "rag_vectors": RAG_EXPERT,
    "graph": KNOWLEDGE_GRAPH,
    "memory_split": KNOWLEDGE_EXTERNAL / "dna" / "persons",
    "nav_map": KNOWLEDGE_EXTERNAL,
    # Processing pipeline
    "entity_registry": PROCESSING,
    "speakers": PROCESSING,
    "diarization": PROCESSING,
    "voice_embeddings": DATA / "voice_embeddings",
    # Agent outputs
    "sow_output": WORKSPACE / "gente-cultura" / "equipe" / "sow",
    "generated_skill": SKILLS,
    # Downloads
    "download": INBOX,
    # Trash (never delete, always move here)
    "trash": TRASH,
    # Knowledge buckets
    "workspace_data": WORKSPACE,
    "personal_data": KNOWLEDGE_PERSONAL,
    "rag_expert": RAG_EXPERT,
    "rag_business": RAG_BUSINESS,
    "workspace_inbox": WORKSPACE_INBOX,
    "personal_inbox": KNOWLEDGE_PERSONAL / "inbox",
    "external_inbox": KNOWLEDGE_EXTERNAL / "inbox",
    # ── Workspace: Departmental Spaces (S13 restructure) ────────
    # AIOS
    "workspace_aios": WORKSPACE_AIOS,
    "workspace_workflows": WORKSPACE_WORKFLOWS,
    "workspace_aios_tools": WORKSPACE_AIOS / "tools",
    "workspace_aios_agents": WORKSPACE_AIOS / "agents",
    "workspace_aios_squads": WORKSPACE_AIOS / "squads",
    "workspace_aios_knowledge": WORKSPACE_AIOS / "knowledge",
    # OPS
    "workspace_ops": WORKSPACE_OPS,
    "workspace_meetings": WORKSPACE_MEETINGS,
    "workspace_eventos": WORKSPACE_EVENTOS,
    "workspace_sprints": WORKSPACE_SPRINTS,
    "workspace_processos_sops": WORKSPACE_OPS / "processos-sops",
    # DELIVERY
    "workspace_delivery": WORKSPACE_DELIVERY,
    "workspace_prospeccao": WORKSPACE_DELIVERY / "prospeccao-leads",
    "workspace_gestao_projetos": WORKSPACE_DELIVERY / "gestao-projetos",
    "workspace_account_cs": WORKSPACE_DELIVERY / "account-cs",
    "workspace_content_factory": WORKSPACE_DELIVERY / "content-factory",
    "workspace_trafego_pago": WORKSPACE_DELIVERY / "trafego-pago",
    "workspace_genai": WORKSPACE_DELIVERY / "genai",
    "workspace_edicao": WORKSPACE_DELIVERY / "edicao",
    "workspace_producao": WORKSPACE_DELIVERY / "producao-filmagem",
    "workspace_copy_delivery": WORKSPACE_DELIVERY / "copy",
    # COMERCIAL
    "workspace_comercial": WORKSPACE_COMERCIAL,
    "workspace_crm": WORKSPACE_CRM,
    "workspace_pipeline_sdr": WORKSPACE_CRM / "pipeline-sdr",
    "workspace_pipeline_closer": WORKSPACE_CRM / "pipeline-closer",
    "workspace_clientes": WORKSPACE_CRM / "clientes",
    "workspace_propostas": WORKSPACE_CRM / "propostas-comerciais",
    # GESTÃO
    "workspace_gestao": WORKSPACE_GESTAO,
    "workspace_finance": WORKSPACE_FINANCE,
    "workspace_juridico": WORKSPACE_JURIDICO,
    "workspace_admin": WORKSPACE_ADMIN,
    "workspace_ferramentas": WORKSPACE_FERRAMENTAS,
    # GENTE & CULTURA
    "workspace_gente_cultura": WORKSPACE_GENTE_CULTURA,
    "workspace_team": WORKSPACE_TEAM,
    "workspace_team_sow": WORKSPACE_TEAM / "sow",
    "workspace_team_scorecards": WORKSPACE_TEAM / "scorecards",
    "workspace_team_cargos": WORKSPACE_TEAM / "cargos",
    "workspace_team_pessoas": WORKSPACE_TEAM / "pessoas",
    "workspace_okrs": WORKSPACE_OKRS,
    "workspace_recrutamento": WORKSPACE_RECRUTAMENTO,
    "workspace_educacional": WORKSPACE_EDUCACIONAL,
    # MARKETING
    "workspace_marketing": WORKSPACE_MARKETING,
    "workspace_performance": WORKSPACE_MARKETING / "performance-growth",
    "workspace_campanhas": WORKSPACE_MARKETING / "campanhas-lancamentos",
    "workspace_creative_library": WORKSPACE_MARKETING / "creative-library",
    # STRATEGY
    "workspace_strategy": WORKSPACE_STRATEGY,
    "workspace_decisions": WORKSPACE_STRATEGY / "decisions",
    # BUSINESSES (DNA per BU)
    "workspace_businesses": WORKSPACE_BUSINESSES,
    # _SYSTEM
    "workspace_system": WORKSPACE_SYSTEM,
    "workspace_templates": WORKSPACE_TEMPLATES,
    # Business bucket (S01)
    "business_inbox": BUSINESS_INBOX,
    "business_people": BUSINESS_PEOPLE,
    "business_dossiers": BUSINESS_DOSSIERS,
    "business_insights": BUSINESS_INSIGHTS,
    "business_narratives": BUSINESS_NARRATIVES,
    "business_decisions": BUSINESS_DECISIONS,
    "business_sops": BUSINESS_SOPS,
    # Agent categories (S06)
    "agents_external": AGENTS_EXTERNAL,
    "agents_business": AGENTS_BUSINESS,
    "agents_personal": AGENTS_PERSONAL,
    "agents_system": AGENTS_SYSTEM,
    "agents_cargo": AGENTS_CARGO,
    # System squad subdirs
    "agents_knowledge_ops": AGENTS_SYSTEM_KNOWLEDGE_OPS,
    "agents_dev_ops": AGENTS_SYSTEM_DEV_OPS,
    # Personal subdirs
    "personal_email": PERSONAL_EMAIL,
    "personal_messages": PERSONAL_MESSAGES,
    "personal_calls": PERSONAL_CALLS,
    "personal_cognitive": PERSONAL_COGNITIVE,
    # Reference docs
    "architecture_doc": REFERENCE / "MEGABRAIN-3D-ARCHITECTURE.md",
    "implementation_log": REFERENCE / "IMPLEMENTATION-LOG.md",
    "onboarding_guide": REFERENCE / "ONBOARDING-GUIDE.md",
    "ux_by_area": WORKSPACE_ADMIN / "UX-BY-AREA.md",
    # Log templates (L1 — mechanism, not data)
    "workspace_log_template": CORE / "templates" / "logs" / "WORKSPACE-LOG-TEMPLATE.md",
    "personal_log_template": CORE / "templates" / "logs" / "PERSONAL-LOG-TEMPLATE.md",
    # Read.ai integration
    "read_ai_log": LOGS / "read-ai-harvest",
    "read_ai_state": MISSION_CONTROL / "READ-AI-STATE.json",
    "read_ai_staging": PROCESSING / "read-ai-staging",
    # Phase gate state
    "phase_gate_state": MISSION_CONTROL / "PHASE-GATE-STATE.json",
    # Agent discovery
    "discovery_state": MISSION_CONTROL / "DISCOVERY-STATE.json",
    "role_tracking": AGENT_DISCOVERY / "role-tracking.md",
    "agent_creation_log": LOGS / "agent-creation.jsonl",
    # Inbox watcher
    "watcher_state": MISSION_CONTROL / "WATCHER-STATE.json",
    "watcher_log": LOGS / "inbox-watcher.jsonl",
    # Smart router (Phase 1.3)
    "smart_router_log": LOGS / "smart-router.jsonl",
    "triage_queue": MISSION_CONTROL / "TRIAGE-QUEUE.json",
    # Batch auto-creator (Phase 1.4)
    "batch_registry": MISSION_CONTROL / "BATCH-REGISTRY.json",
    "batch_auto_creator_log": LOGS / "batch-auto-creator.jsonl",
    # Memory enricher (Phase 1.5)
    "memory_enricher_log": LOGS / "memory-enricher.jsonl",
    # Workspace sync (Phase 1.6)
    "workspace_sync_log": LOGS / "workspace-sync.jsonl",
    # MCE Pipeline (EPIC 3)
    "mce_state": MISSION_CONTROL / "mce",
    "mce_metrics_log": LOGS / "mce-metrics.jsonl",
    "mce_cache": DATA / "mce_cache",
    # Skill Seekers Bridge (Phase 2 integration)
    "ss_bridge_config": CORE / "intelligence" / "pipeline" / "ss_bridge_config.yaml",
    "ss_bridge_log": LOGS / "ss-bridge.jsonl",
    # Inbox processor (Phase 2 integration)
    "inbox_processor_log": LOGS / "inbox-processor",
}

# ── PROHIBITED DIRECTORIES ───────────────────────────────────────
# New files MUST NOT be created in these directories.
PROHIBITED = [
    ROOT / "docs",  # Use REFERENCE instead
    WORKSPACE / "domains",  # Removed S13: replaced by departmental spaces
    WORKSPACE / "providers",  # Removed S13: replaced by gestao/acessos-ferramentas
]
