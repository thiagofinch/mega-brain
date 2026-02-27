#!/usr/bin/env python3
"""
SOW GENERATOR - Intelligence Layer v1.0
========================================
Gera Statement of Work (SOW) dual-purpose para cada cargo detectado.

O SOW serve TANTO para:
1. Configurar agente IA (tools, tasks, autonomy level)
2. Servir como job description para contratar pessoa real

Inclui Executor Decision Tree (inspirado Squad Creator):
6 perguntas -> Worker | Agent | Hybrid | Human

Dependencias: Sprint 5 completo (business models)
Inspiracao: Squad Creator executor-decision-tree, task-anatomy

Versao: 1.0.0
Data: 2026-02-26
"""

import json
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, save_registry, load_taxonomy

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
AGENTS_DIR = BASE_DIR / "agents" / "cargo"
SOW_LOG_PATH = BASE_DIR / "logs" / "sow_generation.jsonl"

# ---------------------------------------------------------------------------
# EXECUTOR DECISION TREE
# ---------------------------------------------------------------------------
# Adapted from Squad Creator's 6-question decision tree.
# Maps role characteristics to executor types.

# Heuristics for auto-classifying roles based on registry data
ROLE_EXECUTOR_HINTS = {
    # Roles that are typically Worker (predictable, function-like)
    "worker_indicators": [
        "data entry", "report", "dashboard", "scheduling",
        "email sequence", "auto-responder", "template",
    ],
    # Roles that are typically Agent (need NLP, context understanding)
    "agent_indicators": [
        "content creation", "copywriting", "social media",
        "research", "analysis", "strategy",
    ],
    # Roles that are typically Hybrid (strategic + AI-assistable)
    "hybrid_indicators": [
        "sales", "closing", "negotiation", "pitch",
        "hiring", "interview", "management", "leadership",
        "consulting", "coaching",
    ],
    # Roles that are typically Human (high-stakes, judgment-critical)
    "human_indicators": [
        "legal", "compliance", "financial decision",
        "firing", "termination", "crisis",
    ],
}

# Domain-based default executor types
DOMAIN_EXECUTOR_DEFAULTS = {
    "vendas": "Hybrid",
    "outbound": "Agent",
    "hiring": "Hybrid",
    "compensation": "Human",
    "management": "Hybrid",
    "scaling": "Hybrid",
    "operations": "Agent",
    "marketing": "Agent",
    "offers": "Hybrid",
    "delivery": "Hybrid",
    "product": "Hybrid",
    "mindset": "Human",
    "copywriting": "Agent",
    "content": "Agent",
    "growth": "Agent",
    "design": "Agent",
    "technology": "Worker",
    "legal": "Human",
    "education": "Hybrid",
}

# Autonomy levels by executor type
AUTONOMY_LEVELS = {
    "Worker": 90,     # Near-full automation
    "Agent": 70,      # AI executes, human monitors
    "Hybrid": 50,     # AI prepares, human decides
    "Human": 10,      # Human drives, AI assists
}


# ---------------------------------------------------------------------------
# SOW TEMPLATE
# ---------------------------------------------------------------------------
def generate_sow(role_name, registry=None):
    """
    Generate a dual-purpose SOW for a role.

    Returns dict with ai_config, human_config, shared, executor_decision.
    """
    if registry is None:
        registry = load_registry()

    roles = registry.get("roles", {})
    role_data = roles.get(role_name, {})
    taxonomy = load_taxonomy()
    cargo_taxonomy = taxonomy.get("cargos", {}).get(role_name, {})

    # Gather data from registry
    responsibilities = role_data.get("responsibilities", [])
    domain_ids = role_data.get("domain_ids", [])
    reports_to = role_data.get("reports_to")
    direct_reports = role_data.get("direct_reports", [])
    weighted_score = role_data.get("weighted_score", 0)
    sources = role_data.get("sources", [])

    # Taxonomy domains
    if not domain_ids and cargo_taxonomy:
        domain_ids = (cargo_taxonomy.get("dominios_primarios", []) +
                      cargo_taxonomy.get("dominios_secundarios", []))

    # Executor Decision
    executor_decision = _evaluate_executor_type(
        role_name, responsibilities, domain_ids, role_data
    )
    executor_type = executor_decision["result"]
    autonomy = AUTONOMY_LEVELS.get(executor_type, 50)

    # Build SOW
    sow = {
        "role_id": role_name,
        "canonical_name": role_name.replace("-", " ").title(),
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),

        # === AI CONFIG ===
        "ai_config": {
            "executor_type": executor_type,
            "autonomy_level": autonomy,
            "tools_required": _suggest_tools(role_name, domain_ids),
            "tasks_assigned": _suggest_tasks(role_name, responsibilities),
            "decision_authority": _decision_authority(executor_type),
            "escalation_triggers": _escalation_triggers(executor_type, role_name),
        },

        # === HUMAN CONFIG ===
        "human_config": {
            "job_title": role_name.replace("-", " ").title(),
            "department": _primary_department(domain_ids),
            "reports_to": reports_to,
            "manages": direct_reports,
            "responsibilities": responsibilities[:10],
            "kpis": _suggest_kpis(role_name, domain_ids),
            "skills_required": _suggest_skills(role_name, domain_ids),
        },

        # === SHARED ===
        "shared": {
            "domains": domain_ids,
            "competencies": _extract_competencies(responsibilities),
            "frameworks_used": [],  # Populated by skill_generator later
            "knowledge_sources": sources[:10],
        },

        # === EXECUTOR DECISION ===
        "executor_decision": executor_decision,

        # === METADATA ===
        "metadata": {
            "weighted_score": weighted_score,
            "source_count": len(sources),
            "responsibility_count": len(responsibilities),
        },
    }

    return sow


def generate_sow_markdown(sow):
    """Render SOW as markdown for human reading and agent configuration."""
    role = sow["role_id"]
    canonical = sow["canonical_name"]
    ai = sow["ai_config"]
    human = sow["human_config"]
    shared = sow["shared"]
    ed = sow["executor_decision"]

    lines = [
        f"# SOW: {canonical}",
        f"",
        f"> **Role ID:** {role}",
        f"> **Executor Type:** {ai['executor_type']}",
        f"> **Autonomy Level:** {ai['autonomy_level']}%",
        f"> **Generated:** {sow['generated_at'][:10]}",
        f"> **Version:** {sow['version']}",
        f"",
        f"---",
        f"",
        f"## AI Agent Configuration",
        f"",
        f"**Executor Type:** {ai['executor_type']}",
        f"**Autonomy:** {ai['autonomy_level']}%",
        f"**Decision Authority:** {ai['decision_authority']}",
        f"",
        f"### Tools Required",
    ]

    for tool in ai["tools_required"]:
        lines.append(f"- {tool}")

    lines.extend([
        f"",
        f"### Tasks Assigned",
    ])
    for task in ai["tasks_assigned"]:
        lines.append(f"- {task}")

    lines.extend([
        f"",
        f"### Escalation Triggers",
    ])
    for trigger in ai["escalation_triggers"]:
        lines.append(f"- {trigger}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## Job Description (Human)",
        f"",
        f"**Job Title:** {human['job_title']}",
        f"**Department:** {human['department']}",
        f"**Reports To:** {human['reports_to'] or 'TBD'}",
    ])

    if human["manages"]:
        lines.append(f"**Manages:** {', '.join(human['manages'])}")

    lines.extend([
        f"",
        f"### Responsibilities",
    ])
    for resp in human["responsibilities"]:
        lines.append(f"- {resp}")

    lines.extend([
        f"",
        f"### KPIs",
    ])
    for kpi in human["kpis"]:
        lines.append(f"- {kpi}")

    lines.extend([
        f"",
        f"### Skills Required",
    ])
    for skill in human["skills_required"]:
        lines.append(f"- {skill}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## Executor Decision Analysis",
        f"",
        f"| Question | Answer |",
        f"|----------|--------|",
        f"| 1. Output 100% previsivel? | {'Sim' if ed['question_1_predictable'] else 'Nao'} |",
        f"| 2. Pode ser funcao pura? | {'Sim' if ed['question_2_pure_function'] else 'Nao'} |",
        f"| 3. Precisa NLP? | {'Sim' if ed['question_3_nlp_required'] else 'Nao'} |",
        f"| 4. Impacto de erro? | {ed['question_4_error_impact']} |",
        f"| 5. Requer julgamento estrategico? | {'Sim' if ed['question_5_strategic'] else 'Nao'} |",
        f"| 6. IA pode assistir? | {'Sim' if ed['question_6_ai_assist'] else 'Nao'} |",
        f"",
        f"**Result:** {ed['result']}",
        f"**Rationale:** {ed['rationale']}",
        f"",
        f"---",
        f"",
        f"## Shared Context",
        f"",
        f"**Domains:** {', '.join(shared['domains'])}",
        f"**Sources:** {sow['metadata']['source_count']}",
        f"**Weighted Score:** {sow['metadata']['weighted_score']}",
        f"",
        f"---",
        f"Auto-generated by Mega Brain Intelligence Layer | {sow['generated_at'][:10]}",
    ])

    return "\n".join(lines)


def generate_all_sows(registry=None, save=True):
    """Generate SOWs for all roles that meet established threshold."""
    if registry is None:
        registry = load_registry()

    roles = registry.get("roles", {})
    generated = []
    skipped = []

    for role_name, role_data in roles.items():
        ws = role_data.get("weighted_score", 0)
        sources = role_data.get("sources", [])

        # Only generate for established roles (ws >= 10, sources >= 2)
        if ws >= 10 and len(sources) >= 2:
            sow = generate_sow(role_name, registry=registry)
            md = generate_sow_markdown(sow)

            if save:
                _save_sow(role_name, sow, md)

            # Update registry
            role_data["sow_generated"] = True
            role_data["sow_path"] = f"agents/cargo/{_domain_dir(sow)}/{role_name.lower()}/SOW.md"
            role_data["executor_type"] = sow["ai_config"]["executor_type"]
            role_data["autonomy_level"] = sow["ai_config"]["autonomy_level"]

            generated.append({
                "role": role_name,
                "executor_type": sow["ai_config"]["executor_type"],
                "autonomy": sow["ai_config"]["autonomy_level"],
                "weighted_score": ws,
            })
        else:
            skipped.append({
                "role": role_name,
                "reason": f"ws={ws}, sources={len(sources)}",
            })

    if save:
        save_registry(registry)
        _log_generation(generated)

    return {
        "generated": len(generated),
        "skipped": len(skipped),
        "details": generated,
        "skipped_details": skipped[:10],
    }


# ---------------------------------------------------------------------------
# EXECUTOR DECISION TREE
# ---------------------------------------------------------------------------
def _evaluate_executor_type(role_name, responsibilities, domain_ids, role_data):
    """
    Run 6-question executor decision tree.

    Returns decision dict with all questions answered and result.
    """
    resp_text = " ".join(responsibilities).lower()
    role_lower = role_name.lower().replace("-", " ")

    # Q1: Is the output 100% predictable?
    q1 = _is_output_predictable(role_lower, resp_text)

    # Q2: Can this be a pure function?
    q2 = q1  # If predictable, likely pure function

    # Q3: Does it require NLP / natural language understanding?
    q3 = _requires_nlp(role_lower, resp_text, domain_ids)

    # Q4: What's the error impact?
    q4 = _error_impact(role_lower, domain_ids)

    # Q5: Requires strategic judgment?
    q5 = _requires_strategic_judgment(role_lower, resp_text, domain_ids)

    # Q6: Can AI assist or prepare?
    q6 = not q1  # If not fully predictable, AI can at least assist

    # Decision logic
    if q1 and q2:
        result = "Worker"
        rationale = "Output previsivel e pode ser funcao pura. Automacao completa."
    elif q5 and not q6:
        result = "Human"
        rationale = "Requer julgamento estrategico e IA nao pode assistir adequadamente."
    elif q5 and q6:
        result = "Hybrid"
        rationale = "Requer julgamento estrategico mas IA pode preparar e assistir."
    elif q3 and q4 in ("HIGH", "CRITICAL"):
        result = "Hybrid"
        rationale = "Precisa NLP com alto impacto de erro. IA executa, humano valida."
    elif q3:
        result = "Agent"
        rationale = "Precisa NLP mas impacto de erro e gerenciavel. IA executa com monitoramento."
    else:
        # Fallback: use domain default
        result = _domain_default_executor(domain_ids)
        rationale = f"Classificacao por dominio primario ({domain_ids[0] if domain_ids else 'geral'})."

    return {
        "question_1_predictable": q1,
        "question_2_pure_function": q2,
        "question_3_nlp_required": q3,
        "question_4_error_impact": q4,
        "question_5_strategic": q5,
        "question_6_ai_assist": q6,
        "result": result,
        "rationale": rationale,
    }


def _is_output_predictable(role_lower, resp_text):
    """Q1: Is output 100% predictable?"""
    predictable_keywords = ["data entry", "report generation", "template",
                            "scheduling", "auto-", "automated"]
    return any(kw in role_lower or kw in resp_text for kw in predictable_keywords)


def _requires_nlp(role_lower, resp_text, domain_ids):
    """Q3: Does it require NLP?"""
    nlp_domains = {"copywriting", "content", "marketing", "vendas", "outbound"}
    nlp_keywords = ["write", "create", "draft", "respond", "communicate",
                     "pitch", "present", "negotiate", "coach"]
    has_nlp_domain = bool(set(domain_ids) & nlp_domains)
    has_nlp_keyword = any(kw in resp_text for kw in nlp_keywords)
    return has_nlp_domain or has_nlp_keyword


def _error_impact(role_lower, domain_ids):
    """Q4: What's the error impact?"""
    critical_domains = {"legal", "compensation"}
    high_domains = {"vendas", "hiring", "management"}
    if set(domain_ids) & critical_domains:
        return "CRITICAL"
    if set(domain_ids) & high_domains:
        return "HIGH"
    return "MEDIUM"


def _requires_strategic_judgment(role_lower, resp_text, domain_ids):
    """Q5: Requires strategic judgment?"""
    strategic_keywords = ["strategy", "decision", "judgment", "evaluate",
                          "negotiate", "hire", "fire", "budget", "prioritize"]
    strategic_roles = ["manager", "director", "head", "lead", "chief", "vp",
                       "cro", "cmo", "coo", "cfo"]
    has_strategic_keyword = any(kw in resp_text for kw in strategic_keywords)
    is_strategic_role = any(sr in role_lower for sr in strategic_roles)
    return has_strategic_keyword or is_strategic_role


def _domain_default_executor(domain_ids):
    """Get default executor type from domain."""
    for did in domain_ids:
        if did in DOMAIN_EXECUTOR_DEFAULTS:
            return DOMAIN_EXECUTOR_DEFAULTS[did]
    return "Hybrid"


# ---------------------------------------------------------------------------
# SUGGESTION HELPERS
# ---------------------------------------------------------------------------
def _suggest_tools(role_name, domain_ids):
    """Suggest tools based on role and domain."""
    tools = []
    role_lower = role_name.lower()

    if any(d in domain_ids for d in ["vendas", "outbound"]):
        tools.extend(["CRM (HubSpot/Pipedrive)", "Calendar (Calendly)"])
    if "outbound" in domain_ids:
        tools.extend(["Dialer (JustCall)", "Email Sequencer"])
    if "copywriting" in domain_ids:
        tools.extend(["Google Docs", "Reference Library"])
    if "content" in domain_ids:
        tools.extend(["Social Media Scheduler", "Design Tool (Canva)"])
    if "growth" in domain_ids:
        tools.extend(["Ad Platform (Meta/Google)", "Analytics Dashboard"])
    if "technology" in domain_ids:
        tools.extend(["IDE", "Git", "CI/CD Pipeline"])
    if "operations" in domain_ids:
        tools.extend(["Project Management (ClickUp)", "Reporting Dashboard"])

    if "closer" in role_lower:
        tools.extend(["Zoom/Google Meet", "Proposal Tool (PandaDoc)"])
    if "bdr" in role_lower or "sdr" in role_lower:
        tools.extend(["LinkedIn Sales Navigator", "Lead Database"])

    return list(dict.fromkeys(tools))[:10]  # dedupe, cap at 10


def _suggest_tasks(role_name, responsibilities):
    """Suggest tasks based on role name and responsibilities."""
    tasks = []
    role_lower = role_name.lower()

    if "closer" in role_lower:
        tasks = ["Execute sales call framework", "Handle objections", "Review pipeline"]
    elif "bdr" in role_lower or "sdr" in role_lower:
        tasks = ["Execute outbound sequences", "Qualify leads", "Book meetings"]
    elif "setter" in role_lower:
        tasks = ["Pre-qualify prospects", "Schedule appointments", "Follow up leads"]
    elif "copywriter" in role_lower:
        tasks = ["Write sales copy", "Create email sequences", "Draft ad copy"]
    elif "content" in role_lower:
        tasks = ["Create content calendar", "Produce content", "Manage distribution"]
    elif "media" in role_lower or "ppc" in role_lower:
        tasks = ["Manage ad campaigns", "Optimize ROAS", "Scale winning ads"]
    elif "manager" in role_lower:
        tasks = ["Run 1-on-1s", "Review team metrics", "Coach team members"]
    elif "designer" in role_lower:
        tasks = ["Create visual assets", "Maintain brand guidelines", "Design creatives"]
    else:
        # Generic from responsibilities
        tasks = [f"Execute: {r[:60]}" for r in responsibilities[:5]]

    return tasks[:8]


def _suggest_kpis(role_name, domain_ids):
    """Suggest KPIs based on role."""
    role_lower = role_name.lower()

    if "closer" in role_lower:
        return ["Close rate (%)", "Revenue per close ($)", "Show rate (%)", "Cash collected ($)"]
    if "bdr" in role_lower or "sdr" in role_lower:
        return ["Calls per day", "Meetings booked per week", "Lead qualification rate (%)"]
    if "setter" in role_lower:
        return ["Appointments set per day", "Show rate (%)", "Qualification accuracy (%)"]
    if "media" in role_lower or "ppc" in role_lower:
        return ["ROAS", "CPA ($)", "Ad spend managed ($)", "Conversion rate (%)"]
    if "copywriter" in role_lower:
        return ["Conversion rate (%)", "Copy pieces delivered", "A/B test win rate (%)"]
    if "content" in role_lower:
        return ["Content pieces per week", "Engagement rate (%)", "Follower growth (%)"]
    if "manager" in role_lower or "director" in role_lower:
        return ["Team target attainment (%)", "Employee retention (%)", "Ramp time (days)"]
    if "data" in role_lower or "analyst" in role_lower:
        return ["Reports delivered on time (%)", "Data accuracy (%)", "Insights acted upon"]

    return ["Target attainment (%)", "Tasks completed on time (%)"]


def _suggest_skills(role_name, domain_ids):
    """Suggest required skills."""
    skills = []
    for d in domain_ids:
        if d == "vendas":
            skills.extend(["Negotiation", "Communication", "Objection handling"])
        elif d == "outbound":
            skills.extend(["Cold calling", "Email outreach", "Lead qualification"])
        elif d == "copywriting":
            skills.extend(["Persuasive writing", "Research", "Headline crafting"])
        elif d == "content":
            skills.extend(["Content creation", "Social media management", "Storytelling"])
        elif d == "growth":
            skills.extend(["Paid advertising", "Analytics", "A/B testing"])
        elif d == "technology":
            skills.extend(["Programming", "System design", "Debugging"])
        elif d == "management":
            skills.extend(["Leadership", "Coaching", "Performance management"])
    return list(dict.fromkeys(skills))[:8]


def _primary_department(domain_ids):
    """Map primary domain to department name."""
    dept_map = {
        "vendas": "Sales", "outbound": "Sales",
        "marketing": "Marketing", "copywriting": "Marketing",
        "content": "Content", "growth": "Growth/Marketing",
        "operations": "Operations", "technology": "Engineering",
        "hiring": "Human Resources", "management": "Management",
        "design": "Design", "legal": "Legal",
    }
    for d in domain_ids:
        if d in dept_map:
            return dept_map[d]
    return "General"


def _decision_authority(executor_type):
    """Map executor type to decision authority description."""
    if executor_type == "Worker":
        return "Executa tarefas predefinidas sem decisao"
    elif executor_type == "Agent":
        return "Pode decidir dentro de parametros definidos, escala excecoes"
    elif executor_type == "Hybrid":
        return "Prepara e sugere, humano decide em casos criticos"
    elif executor_type == "Human":
        return "Humano decide, IA apenas assiste com informacao"
    return "Indefinido"


def _escalation_triggers(executor_type, role_name):
    """Generate escalation triggers based on executor type."""
    if executor_type == "Worker":
        return ["Erro de execucao", "Input fora do padrao"]
    elif executor_type == "Agent":
        return ["Confianca < 70%", "Erro repetido 2x", "Caso nao coberto por regras"]
    elif executor_type == "Hybrid":
        return ["Decisao acima do threshold de autonomia", "Excecao de processo",
                "Impacto financeiro > threshold", "Conflito entre regras"]
    elif executor_type == "Human":
        return ["IA detecta inconsistencia", "Prazo critico", "Compliance check"]
    return []


def _extract_competencies(responsibilities):
    """Extract competency keywords from responsibilities."""
    comps = set()
    for r in responsibilities:
        r_lower = r.lower()
        if any(kw in r_lower for kw in ["sell", "vend", "close", "deal"]):
            comps.add("Sales execution")
        if any(kw in r_lower for kw in ["lead", "manag", "coach", "train"]):
            comps.add("People management")
        if any(kw in r_lower for kw in ["write", "copy", "draft", "creat"]):
            comps.add("Content creation")
        if any(kw in r_lower for kw in ["analyz", "report", "metric", "data"]):
            comps.add("Analytics")
        if any(kw in r_lower for kw in ["strategy", "plan", "design", "architect"]):
            comps.add("Strategic planning")
    return list(comps)[:6]


def _domain_dir(sow):
    """Determine directory name for SOW storage."""
    domains = sow["shared"]["domains"]
    domain_to_dir = {
        "vendas": "sales", "outbound": "sales", "marketing": "marketing",
        "copywriting": "marketing", "content": "content", "growth": "growth",
        "operations": "operations", "technology": "tech", "hiring": "hr",
        "management": "management", "design": "design", "legal": "legal",
    }
    for d in domains:
        if d in domain_to_dir:
            return domain_to_dir[d]
    return "general"


def _save_sow(role_name, sow, md):
    """Save SOW files."""
    domain = _domain_dir(sow)
    sow_dir = AGENTS_DIR / domain / role_name.lower()
    sow_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    with open(sow_dir / "SOW.json", "w", encoding="utf-8") as f:
        json.dump(sow, f, indent=2, ensure_ascii=False)

    # Save Markdown
    with open(sow_dir / "SOW.md", "w", encoding="utf-8") as f:
        f.write(md)


def _log_generation(generated):
    """Log SOW generation to JSONL."""
    SOW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    for entry in generated:
        log_entry = {
            "timestamp": now,
            "trigger_type": "sow_generation",
            "role": entry["role"],
            "executor_type": entry["executor_type"],
            "autonomy": entry["autonomy"],
            "weighted_score": entry["weighted_score"],
        }
        with open(SOW_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== SOW GENERATOR v1.0: Generate All ===\n")
        result = generate_all_sows(save=True)
        print(f"SOWs generated:  {result['generated']}")
        print(f"Roles skipped:   {result['skipped']}")

        if result["details"]:
            print(f"\n--- Generated SOWs ---")
            for d in result["details"]:
                print(f"  {d['role']:25s}  executor={d['executor_type']:8s}  "
                      f"autonomy={d['autonomy']}%  ws={d['weighted_score']:.1f}")

        if result["skipped_details"]:
            print(f"\n--- Skipped (top 10) ---")
            for s in result["skipped_details"]:
                print(f"  {s['role']:25s}  reason: {s['reason']}")

    elif len(sys.argv) > 1 and sys.argv[1] != "--help":
        role = sys.argv[1].upper()
        print(f"\n=== SOW for {role} ===\n")
        sow = generate_sow(role)
        md = generate_sow_markdown(sow)
        print(md)

    else:
        print("Uso:")
        print("  python3 sow_generator.py --all       # Gerar SOWs para todos os roles")
        print("  python3 sow_generator.py CLOSER       # Gerar SOW para role especifico")
        sys.exit(1)


if __name__ == "__main__":
    main()
