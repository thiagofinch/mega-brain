#!/usr/bin/env python3
"""
REVIEW DASHBOARD - Intelligence Layer v1.0
============================================
CLI dashboard para gerenciar human checkpoints e review queue.

4 Human Checkpoints:
HC-1: Novo role pronto para criacao de agente
HC-2: Business model com role_chain >= 4 niveis
HC-3: Skills geradas >= 5 para persona
HC-4: Merge candidates na review_queue

Inspiracao: MMOS 6 human checkpoints (layers 5-8 obrigatorios)

Versao: 1.0.0
Data: 2026-02-26
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, save_registry

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
REVIEW_QUEUE_PATH = BASE_DIR / "processing" / "canonical" / "review_queue.jsonl"
SKILLS_REGISTRY_PATH = BASE_DIR / "knowledge" / "dna" / "_dna-skills-registry.yaml"
REVIEW_LOG_PATH = BASE_DIR / "logs" / "review_decisions.jsonl"

# ---------------------------------------------------------------------------
# HUMAN CHECKPOINTS DEFINITION
# ---------------------------------------------------------------------------
CHECKPOINTS = {
    "HC-1": {
        "name": "Agent Creation Approval",
        "trigger": "Novo role com weighted_score >= 10 pronto para criacao de agente",
        "question": "Este cargo deve virar agente? [Aprovar/Rejeitar/Adiar]",
        "context_fields": ["sow_path", "weighted_score", "sources", "executor_type", "responsibilities"],
    },
    "HC-2": {
        "name": "Business Model Validation",
        "trigger": "Business model detectado com role_chain >= 4 niveis",
        "question": "Hierarquia organizacional correta? [Aprovar/Editar/Rejeitar]",
        "context_fields": ["role_chain", "departments", "team_size_estimate", "revenue_signals"],
    },
    "HC-3": {
        "name": "Skills Review",
        "trigger": "Skills geradas >= 5 para um persona",
        "question": "Skills refletem os frameworks reais? [Aprovar por skill]",
        "context_fields": ["skills_count", "skill_ids", "persona"],
    },
    "HC-4": {
        "name": "Entity Merge Review",
        "trigger": "review_queue.jsonl tem entidades pendentes",
        "question": "Merge candidates: sao a mesma entidade? [Merge/Manter separado]",
        "context_fields": ["raw_name", "candidate_canonical", "score", "entity_type"],
    },
}


# ---------------------------------------------------------------------------
# CORE: GATHER PENDING ITEMS
# ---------------------------------------------------------------------------
def gather_pending_reviews(registry=None):
    """
    Gather all pending review items across all checkpoints.

    Returns dict with items per checkpoint type.
    """
    if registry is None:
        registry = load_registry()

    pending = {
        "HC-1": [],  # Agent creation pending
        "HC-2": [],  # Business model validation
        "HC-3": [],  # Skills review
        "HC-4": [],  # Entity merge
    }

    # --- HC-1: Roles ready for agent creation ---
    roles = registry.get("roles", {})
    for role_name, role_data in roles.items():
        ws = role_data.get("weighted_score", 0)
        sources = len(role_data.get("sources", []))
        has_agent = role_data.get("has_agent", False)
        sow_generated = role_data.get("sow_generated", False)
        executor_type = role_data.get("executor_type", "?")

        if ws >= 10 and sources >= 2 and not has_agent:
            pending["HC-1"].append({
                "role": role_name,
                "weighted_score": ws,
                "sources": sources,
                "executor_type": executor_type,
                "sow_generated": sow_generated,
                "responsibilities": len(role_data.get("responsibilities", [])),
            })

    pending["HC-1"].sort(key=lambda x: -x["weighted_score"])

    # --- HC-2: Business models to validate ---
    persons = registry.get("persons", {})
    for person_name, person_data in persons.items():
        bm = person_data.get("business_model", {})
        if bm and bm.get("detected"):
            role_chain = bm.get("role_chain", {})
            if len(role_chain) >= 4:
                pending["HC-2"].append({
                    "person": person_name,
                    "departments": bm.get("departments", []),
                    "team_size": bm.get("team_size_estimate", "?"),
                    "role_chain_depth": len(role_chain),
                    "role_consolidation": len(bm.get("role_consolidation", [])),
                })

    # --- HC-3: Skills pending review ---
    try:
        import yaml
        if SKILLS_REGISTRY_PATH.exists():
            with open(SKILLS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                skills_reg = yaml.safe_load(f) or {}
            for persona, data in skills_reg.get("personas", {}).items():
                count = data.get("skills_count", 0)
                if count >= 5:
                    pending["HC-3"].append({
                        "persona": persona,
                        "skills_count": count,
                        "skill_ids": data.get("skills", [])[:5],
                    })
    except Exception:
        pass

    # --- HC-4: Merge candidates from review queue ---
    if REVIEW_QUEUE_PATH.exists():
        with open(REVIEW_QUEUE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("status") == "pending":
                        pending["HC-4"].append(entry)
                except json.JSONDecodeError:
                    continue

    return pending


# ---------------------------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------------------------
def display_dashboard(pending):
    """Display the review dashboard."""
    total_pending = sum(len(v) for v in pending.values())

    print()
    print("=" * 60)
    print("  MEGA BRAIN - REVIEW DASHBOARD")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total pending: {total_pending}")
    print("=" * 60)

    # HC-1: Agents
    items = pending["HC-1"]
    if items:
        print(f"\n  AGENTS PENDENTES DE APROVACAO (HC-1): {len(items)}")
        print(f"  {'─' * 50}")
        for i, item in enumerate(items[:10], 1):
            sow_icon = "SOW" if item["sow_generated"] else "---"
            print(f"  [{i:2d}] {item['role']:25s}  ws={item['weighted_score']:6.1f}  "
                  f"src={item['sources']}  exec={item['executor_type']:8s}  {sow_icon}")
    else:
        print(f"\n  AGENTS PENDENTES (HC-1): Nenhum")

    # HC-2: Business Models
    items = pending["HC-2"]
    if items:
        print(f"\n  BUSINESS MODELS P/ VALIDACAO (HC-2): {len(items)}")
        print(f"  {'─' * 50}")
        for i, item in enumerate(items, 1):
            print(f"  [{i:2d}] {item['person']:25s}  chain_depth={item['role_chain_depth']}  "
                  f"team={item['team_size']}  depts={len(item['departments'])}")
    else:
        print(f"\n  BUSINESS MODELS (HC-2): Nenhum")

    # HC-3: Skills
    items = pending["HC-3"]
    if items:
        print(f"\n  SKILLS PENDENTES DE REVISAO (HC-3): {len(items)}")
        print(f"  {'─' * 50}")
        for i, item in enumerate(items, 1):
            print(f"  [{i:2d}] {item['persona']:25s}  {item['skills_count']} skills geradas")
    else:
        print(f"\n  SKILLS (HC-3): Nenhum")

    # HC-4: Merges
    items = pending["HC-4"]
    if items:
        print(f"\n  MERGES PENDENTES (HC-4): {len(items)}")
        print(f"  {'─' * 50}")
        for i, item in enumerate(items[:10], 1):
            print(f"  [{i:2d}] \"{item.get('raw_name', '?')}\" <-> "
                  f"\"{item.get('candidate_canonical', '?')}\" "
                  f"(score: {item.get('score', 0):.2f}, type: {item.get('entity_type', '?')})")
    else:
        print(f"\n  MERGES (HC-4): Nenhum")

    print()
    print(f"  {'=' * 50}")
    print(f"  Acoes: [numero] detalhar | approve/reject [id] | exit")
    print(f"  {'=' * 50}")


def display_summary_json(pending):
    """Output summary as JSON (for programmatic use)."""
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_pending": sum(len(v) for v in pending.values()),
        "by_checkpoint": {k: len(v) for k, v in pending.items()},
        "hc1_agents": [
            {"role": i["role"], "ws": i["weighted_score"], "exec": i["executor_type"]}
            for i in pending["HC-1"][:5]
        ],
        "hc4_merges": len(pending["HC-4"]),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# ACTIONS
# ---------------------------------------------------------------------------
def approve_agent(role_name, registry=None):
    """Approve an agent for creation (HC-1)."""
    if registry is None:
        registry = load_registry()

    roles = registry.get("roles", {})
    if role_name not in roles:
        print(f"  [ERROR] Role '{role_name}' nao encontrado.")
        return False

    roles[role_name]["human_approved"] = True
    roles[role_name]["approved_at"] = datetime.now(timezone.utc).isoformat()
    save_registry(registry)

    _log_decision("approve_agent", role_name, "approved")
    print(f"  [OK] {role_name} aprovado para criacao de agente.")
    return True


def reject_agent(role_name, registry=None):
    """Reject an agent creation (HC-1)."""
    if registry is None:
        registry = load_registry()

    roles = registry.get("roles", {})
    if role_name not in roles:
        print(f"  [ERROR] Role '{role_name}' nao encontrado.")
        return False

    roles[role_name]["human_approved"] = False
    roles[role_name]["rejected_at"] = datetime.now(timezone.utc).isoformat()
    save_registry(registry)

    _log_decision("reject_agent", role_name, "rejected")
    print(f"  [OK] {role_name} rejeitado.")
    return True


def approve_merge(raw_name, canonical, registry=None):
    """Approve a merge candidate (HC-4)."""
    if registry is None:
        registry = load_registry()

    # Update review queue
    if REVIEW_QUEUE_PATH.exists():
        lines = []
        with open(REVIEW_QUEUE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if (entry.get("raw_name") == raw_name and
                            entry.get("candidate_canonical") == canonical):
                        entry["status"] = "merged"
                    lines.append(json.dumps(entry, ensure_ascii=False))
                except json.JSONDecodeError:
                    lines.append(line.strip())

        with open(REVIEW_QUEUE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    _log_decision("approve_merge", f"{raw_name} -> {canonical}", "merged")
    print(f"  [OK] Merged: '{raw_name}' -> '{canonical}'")
    return True


def _log_decision(action, entity, result):
    """Log review decision."""
    REVIEW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "entity": entity,
        "result": result,
    }
    with open(REVIEW_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        pending = gather_pending_reviews()
        display_summary_json(pending)

    elif len(sys.argv) > 2 and sys.argv[1] == "approve":
        role = sys.argv[2].upper()
        approve_agent(role)

    elif len(sys.argv) > 2 and sys.argv[1] == "reject":
        role = sys.argv[2].upper()
        reject_agent(role)

    else:
        pending = gather_pending_reviews()
        display_dashboard(pending)


if __name__ == "__main__":
    main()
