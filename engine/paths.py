"""
paths.py — Single Source of Truth for repository paths
======================================================

Central path table imported by the pipeline, RAG, agents and hooks
(``from engine.paths import KNOWLEDGE_EXTERNAL, LOGS, ROUTING, ...``).

Layout follows the architecture documented in ``.claude/CLAUDE.md``:

  - ``knowledge/{external,business,personal}`` — the three isolated buckets
    (Constitution Art. XIII)
  - ``agents/{external,business,personal,cargo}`` — knowledge agents
  - ``workspace/`` — business data (L0-L4, Art. XIV)
  - ``.data/`` — runtime data (RAG indexes, logs, artifacts) — gitignored
  - ``.claude/mission-control/`` — pipeline state

``ROUTING`` maps symbolic names (``"external_inbox"``, ``"mce_state"``, ...) to
paths for callers that resolve destinations by key instead of by constant.

Constraints: leaf module — stdlib only. Importing it never touches the disk;
callers create the directories they write to.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# REPOSITORY ROOT AND TOP-LEVEL DIRECTORIES
# ---------------------------------------------------------------------------

ROOT: Path = Path(__file__).resolve().parent.parent

# Python framework package (engine/) — hosts intelligence/, workflows/, ...
CORE: Path = ROOT / "engine"
CLAUDE: Path = ROOT / ".claude"
COMMANDS: Path = CLAUDE / "commands"
MISSION_CONTROL: Path = CLAUDE / "mission-control"

AGENTS: Path = ROOT / "agents"
WORKSPACE: Path = ROOT / "workspace"
INBOX: Path = ROOT / "inbox"
PROCESSING: Path = ROOT / "processing"

# Runtime data (gitignored)
DATA: Path = ROOT / ".data"
LOGS: Path = DATA / "logs"
ARTIFACTS: Path = DATA / "artifacts"
RAG_INDEX: Path = DATA / "rag_index"  # external bucket
RAG_BUSINESS: Path = DATA / "rag_business"  # business bucket
KNOWLEDGE_GRAPH: Path = DATA / "knowledge_graph"  # graph.json

# ---------------------------------------------------------------------------
# KNOWLEDGE BUCKETS
# ---------------------------------------------------------------------------

KNOWLEDGE: Path = ROOT / "knowledge"
KNOWLEDGE_EXTERNAL: Path = KNOWLEDGE / "external"
KNOWLEDGE_BUSINESS: Path = KNOWLEDGE / "business"
KNOWLEDGE_PERSONAL: Path = KNOWLEDGE / "personal"

# External bucket (experts)
EXTERNAL_DNA_PERSONS: Path = KNOWLEDGE_EXTERNAL / "dna" / "persons"
EXTERNAL_DNA_DOMAINS: Path = KNOWLEDGE_EXTERNAL / "dna" / "domains"
EXTERNAL_SOURCES: Path = KNOWLEDGE_EXTERNAL / "sources"
EXTERNAL_DOSSIERS_PERSONS_BY_THEME: Path = KNOWLEDGE_EXTERNAL / "dossiers" / "persons-by-theme"

# Business bucket
BUSINESS_INSIGHTS: Path = KNOWLEDGE_BUSINESS / "insights"
BUSINESS_DECISIONS: Path = KNOWLEDGE_BUSINESS / "decisions"
BUSINESS_DOSSIERS: Path = KNOWLEDGE_BUSINESS / "dossiers"
BUSINESS_SOPS: Path = KNOWLEDGE_BUSINESS / "sops"

# Personal bucket — processed material lands in knowledge/personal/_{subdir}/
PERSONAL_EMAIL: Path = KNOWLEDGE_PERSONAL / "_email"
PERSONAL_MESSAGES: Path = KNOWLEDGE_PERSONAL / "_messages"
PERSONAL_CALLS: Path = KNOWLEDGE_PERSONAL / "_calls"
PERSONAL_COGNITIVE: Path = KNOWLEDGE_PERSONAL / "_cognitive"

# ---------------------------------------------------------------------------
# AGENTS
# ---------------------------------------------------------------------------

AGENTS_EXTERNAL: Path = AGENTS / "external"
AGENTS_BUSINESS: Path = AGENTS / "business"
AGENTS_CARGO: Path = AGENTS / "cargo"

# ---------------------------------------------------------------------------
# WORKSPACE
# ---------------------------------------------------------------------------

WORKSPACE_INBOX: Path = WORKSPACE / "inbox"
WORKSPACE_BUSINESSES: Path = WORKSPACE / "businesses"
WORKSPACE_TEMPLATES: Path = WORKSPACE / "_templates"
WORKSPACE_STRATEGY: Path = WORKSPACE / "strategy"
# workspace/team/ per workspace_sync.py and scope_classifier.py. bucket_processor.py
# also routes the "team" subdir here, although ingest-empresa.md lists workspace/_team/.
WORKSPACE_TEAM: Path = WORKSPACE / "team"

# Processed workspace material lands in workspace/_{subdir}/ (team is the exception above)
WORKSPACE_ORG: Path = WORKSPACE / "_org"
WORKSPACE_FINANCE: Path = WORKSPACE / "_finance"
WORKSPACE_MEETINGS: Path = WORKSPACE / "_meetings"
WORKSPACE_AUTOMATIONS: Path = WORKSPACE / "_automations"
WORKSPACE_TOOLS: Path = WORKSPACE / "_tools"

# ---------------------------------------------------------------------------
# ROUTING TABLE
# ---------------------------------------------------------------------------

ROUTING: dict[str, Path] = {
    # Bucket inboxes
    "external_inbox": KNOWLEDGE_EXTERNAL / "inbox",
    "business_inbox": KNOWLEDGE_BUSINESS / "inbox",
    "personal_inbox": KNOWLEDGE_PERSONAL / "inbox",
    "workspace_inbox": WORKSPACE_INBOX,
    # Business bucket
    "business_insights": BUSINESS_INSIGHTS,
    "business_dossiers": BUSINESS_DOSSIERS,
    "business_dossiers_companies": BUSINESS_DOSSIERS / "companies",
    "business_people": KNOWLEDGE_BUSINESS / "people",
    "business_dna": KNOWLEDGE_BUSINESS / "dna",
    "business_dna_persons": KNOWLEDGE_BUSINESS / "dna" / "persons",
    "business_sops": BUSINESS_SOPS,
    "business_sources": KNOWLEDGE_BUSINESS / "sources",
    "agents_business": AGENTS_BUSINESS,
    # MCE pipeline state
    "mce_state": MISSION_CONTROL / "mce",
    "mce_cache": DATA / "mce_cache",
    "batch_registry": MISSION_CONTROL / "BATCH-REGISTRY.json",
    "batch_log": LOGS / "batches",
    "batch_auto_creator_log": LOGS / "batch-auto-creator.jsonl",
    "mce_metrics_log": LOGS / "mce-metrics.jsonl",
    "quality_gaps": LOGS,
    "handoff": LOGS / "handoffs",
    "memory_enricher_log": LOGS / "memory-enricher.jsonl",
    "workspace_sync_log": LOGS / "workspace-sync.jsonl",
    # The folders below are a convention of this module: the callers only name the
    # files (or accept None), the public tree documents no location for them.
    # Inbox watcher
    "watcher_state": MISSION_CONTROL / "WATCHER-STATE.json",
    "watcher_log": LOGS / "inbox-watcher.jsonl",
    # Read.ai harvest
    "read_ai_log": LOGS / "read-ai-harvest",
    "read_ai_state": MISSION_CONTROL / "READ-AI-HARVEST-STATE.json",
    "read_ai_staging": DATA / "read_ai_staging",
    # Skill Seekers bridge
    "ss_bridge_config": DATA / "ss_bridge" / "config.yaml",
    "ss_bridge_log": LOGS / "ss-bridge.jsonl",
    # RAG verification
    "conclave_faithfulness_log": LOGS / "conclave-faithfulness.jsonl",
    "hhem_model": DATA / "models" / "hhem",
}
