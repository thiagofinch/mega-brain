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
WORKSPACE = ROOT / "workspace"  # Business data (L1 template, L2 populated)

# ── WORKSPACE SUBDIRS (L1 template, L2 populated) ──────────────
WORKSPACE_ORG = WORKSPACE / "org"
WORKSPACE_TEAM = WORKSPACE / "team"
WORKSPACE_FINANCE = WORKSPACE / "finance"
WORKSPACE_MEETINGS = WORKSPACE / "meetings"
WORKSPACE_AUTOMATIONS = WORKSPACE / "automations"
WORKSPACE_TOOLS = WORKSPACE / "tools"
WORKSPACE_INBOX = WORKSPACE / "inbox"

# ── GITIGNORED (L3 / Runtime) ────────────────────────────────────
LOGS = ROOT / "logs"
KNOWLEDGE = ROOT / "knowledge"
KNOWLEDGE_EXTERNAL = KNOWLEDGE / "external"
KNOWLEDGE_PERSONAL = KNOWLEDGE / "personal"
KNOWLEDGE_BUSINESS = KNOWLEDGE / "business"

# Backward compat: root inbox/ no longer exists (S03 distributed to bucket inboxes).
# Points to workspace inbox as closest equivalent for any remaining references.
INBOX = WORKSPACE / "inbox"

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

# ── WORKSPACE STRATA SUBDIRS (S04 restructure) ─────────────────
WORKSPACE_BUSINESSES = WORKSPACE / "businesses"
WORKSPACE_DOMAINS = WORKSPACE / "domains"
WORKSPACE_TEMPLATES = WORKSPACE / "_templates"
WORKSPACE_PROVIDERS = WORKSPACE / "providers"
WORKSPACE_CONFIG = WORKSPACE / "config"
WORKSPACE_REF = WORKSPACE / "_ref"
WORKSPACE_STRATEGY = WORKSPACE / "strategy"
WORKSPACE_EVENTS = WORKSPACE / "events"

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
    "sow_output": AGENTS / "sua-empresa" / "sow",
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
    # Workspace subdirs (legacy)
    "workspace_org": WORKSPACE_ORG,
    "workspace_team": WORKSPACE_TEAM,
    "workspace_finance": WORKSPACE_FINANCE,
    "workspace_meetings": WORKSPACE_MEETINGS,
    "workspace_automations": WORKSPACE_AUTOMATIONS,
    "workspace_tools": WORKSPACE_TOOLS,
    # Workspace Strata subdirs (S04)
    "workspace_businesses": WORKSPACE_BUSINESSES,
    "workspace_domains": WORKSPACE_DOMAINS,
    "workspace_templates": WORKSPACE_TEMPLATES,
    "workspace_providers": WORKSPACE_PROVIDERS,
    "workspace_strategy": WORKSPACE_STRATEGY,
    "workspace_events": WORKSPACE_EVENTS,
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
    "ux_by_area": WORKSPACE_ORG / "UX-BY-AREA.md",
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
}

# ── PROHIBITED DIRECTORIES ───────────────────────────────────────
# New files MUST NOT be created in these directories.
PROHIBITED = [
    ROOT / "docs",  # Use REFERENCE instead
]
