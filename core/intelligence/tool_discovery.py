#!/usr/bin/env python3
"""
TOOL DISCOVERY - Intelligence Layer v1.0
==========================================
Descobre ferramentas disponiveis para cada role de cargo.

Mapeia:
1. Essential tools (obrigatorias para funcionar)
2. Recommended tools (melhoram performance)
3. MCP available (integracao direta possivel)
4. Autonomy level (do SOW)
5. Command Loader (tasks obrigatorias por agente)

Inspiracao: Squad Creator *discover-tools, wf-discovery-tools.yaml

Versao: 1.0.0
Data: 2026-02-26
"""

import json
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

# ---------------------------------------------------------------------------
# TOOL REGISTRY (Knowledge base)
# ---------------------------------------------------------------------------
# Maps role categories to their tool ecosystems.
# This is a seed database - grows as more roles are discovered.

TOOL_REGISTRY = {
    # === SALES ===
    "CLOSER": {
        "essential": ["CRM (HubSpot/Pipedrive)", "Calendar (Calendly)", "Video Call (Zoom/Meet)"],
        "recommended": ["Proposal Tool (PandaDoc)", "WhatsApp Business", "Script Library"],
        "mcp_available": ["hubspot-mcp", "google-calendar-mcp", "zoom-mcp"],
    },
    "BDR": {
        "essential": ["CRM", "Dialer (JustCall/AirCall)", "Email Sequencer (Instantly/Smartlead)"],
        "recommended": ["LinkedIn Sales Navigator", "Lead Database (Apollo/ZoomInfo)", "Intent Data"],
        "mcp_available": ["hubspot-mcp", "gmail-mcp"],
    },
    "SDR": {
        "essential": ["CRM", "Dialer", "Email Sequencer"],
        "recommended": ["LinkedIn Sales Navigator", "Lead Database"],
        "mcp_available": ["hubspot-mcp", "gmail-mcp"],
    },
    "SDS": {
        "essential": ["CRM", "Phone System", "Scheduling Tool"],
        "recommended": ["Lead Scoring Tool", "Call Recording"],
        "mcp_available": ["hubspot-mcp"],
    },
    "SETTER": {
        "essential": ["CRM", "Calendar", "Messaging (WhatsApp/SMS)"],
        "recommended": ["Pre-qualification Form", "Script Library"],
        "mcp_available": ["hubspot-mcp", "google-calendar-mcp"],
    },
    "SALES-MANAGER": {
        "essential": ["CRM (Admin)", "Reporting Dashboard", "Video Call"],
        "recommended": ["Coaching Platform", "Performance Analytics", "Comp Calculator"],
        "mcp_available": ["hubspot-mcp", "google-sheets-mcp"],
    },
    "SALES-LEAD": {
        "essential": ["CRM (Admin)", "Reporting Dashboard"],
        "recommended": ["Team Chat (Slack)", "Training Platform"],
        "mcp_available": ["hubspot-mcp", "slack-mcp"],
    },
    "LNS": {
        "essential": ["CRM", "Order Management", "Communication Tool"],
        "recommended": ["Billing System", "Customer Portal"],
        "mcp_available": ["hubspot-mcp"],
    },
    "CUSTOMER-SUCCESS": {
        "essential": ["CRM", "Support Ticketing (Zendesk/Intercom)", "NPS Tool"],
        "recommended": ["Onboarding Platform", "Knowledge Base", "Health Score Dashboard"],
        "mcp_available": ["hubspot-mcp", "intercom-mcp"],
    },

    # === MARKETING ===
    "COPYWRITER": {
        "essential": ["Google Docs/Notion", "Reference Library", "Brief Template"],
        "recommended": ["Grammarly", "Headline Analyzer", "Swipe File", "AI Writing Assistant"],
        "mcp_available": ["google-drive-mcp", "notion-mcp"],
    },
    "FUNNEL-STRATEGIST": {
        "essential": ["Funnel Builder (ClickFunnels/Systeme)", "Analytics", "A/B Testing"],
        "recommended": ["Heatmap (Hotjar)", "Tag Manager", "Conversion Tracker"],
        "mcp_available": ["google-analytics-mcp"],
    },
    "MARKETER": {
        "essential": ["Marketing Platform (HubSpot/ActiveCampaign)", "Analytics", "CMS"],
        "recommended": ["Social Scheduler", "SEO Tool", "Design Tool"],
        "mcp_available": ["hubspot-mcp", "google-analytics-mcp"],
    },
    "LAUNCH-STRATEGIST": {
        "essential": ["Project Management (ClickUp)", "Email Platform", "Funnel Builder"],
        "recommended": ["Webinar Platform", "Payment Processor", "Deadline Funnel"],
        "mcp_available": ["clickup-mcp", "google-sheets-mcp"],
    },

    # === CONTENT/DESIGN ===
    "CONTENT-CREATOR": {
        "essential": ["Content Calendar (Notion/Trello)", "Video Editor", "Social Platforms"],
        "recommended": ["Canva", "Stock Media Library", "Scheduling Tool (Buffer/Later)"],
        "mcp_available": ["notion-mcp"],
    },
    "DESIGNER": {
        "essential": ["Design Tool (Figma/Canva)", "Brand Guidelines", "Asset Library"],
        "recommended": ["Mockup Tool", "Stock Photography", "Color Palette Generator"],
        "mcp_available": ["figma-mcp"],
    },
    "SOCIAL-MEDIA-MANAGER": {
        "essential": ["Social Scheduler (Buffer/Hootsuite)", "Analytics", "Content Calendar"],
        "recommended": ["Community Management Tool", "Listening Tool", "UGC Platform"],
        "mcp_available": ["notion-mcp"],
    },

    # === GROWTH ===
    "MEDIA-BUYER": {
        "essential": ["Ad Platforms (Meta/Google/TikTok)", "Analytics", "Tracking (UTMs/Pixels)"],
        "recommended": ["Creative Testing Tool", "Attribution Platform", "Reporting Dashboard"],
        "mcp_available": ["google-analytics-mcp", "google-sheets-mcp"],
    },
    "PPC-MANAGER": {
        "essential": ["Google Ads", "Analytics", "Keyword Research Tool"],
        "recommended": ["SEMrush/Ahrefs", "Landing Page Builder", "Bid Management"],
        "mcp_available": ["google-analytics-mcp"],
    },
    "GROWTH-HACKER": {
        "essential": ["Analytics Suite", "A/B Testing", "Email Platform"],
        "recommended": ["Product Analytics (Mixpanel)", "Referral Tool", "Viral Loop Builder"],
        "mcp_available": ["google-analytics-mcp"],
    },

    # === OPERATIONS ===
    "PROJECT-MANAGER": {
        "essential": ["Project Management (ClickUp/Asana)", "Communication (Slack)", "Docs (Notion)"],
        "recommended": ["Time Tracking", "Resource Planning", "Retrospective Tool"],
        "mcp_available": ["clickup-mcp", "slack-mcp", "notion-mcp"],
    },
    "OPS-MANAGER": {
        "essential": ["Project Management", "Reporting Dashboard", "Process Documentation"],
        "recommended": ["Automation (Zapier/N8N)", "SOP Builder", "KPI Dashboard"],
        "mcp_available": ["clickup-mcp", "google-sheets-mcp"],
    },
    "DATA-ANALYST": {
        "essential": ["BI Tool (Metabase/Looker)", "Spreadsheets (Sheets)", "SQL Access"],
        "recommended": ["Python/R Environment", "Data Pipeline (dbt)", "Visualization (Tableau)"],
        "mcp_available": ["google-sheets-mcp", "postgres-mcp"],
    },
    "TECH-LEAD": {
        "essential": ["IDE (VSCode)", "Git (GitHub)", "CI/CD (GitHub Actions)"],
        "recommended": ["Code Review Tool", "Monitoring (Datadog)", "Documentation (Notion)"],
        "mcp_available": ["github-mcp", "slack-mcp"],
    },

    # === HR ===
    "HR-DIRECTOR": {
        "essential": ["ATS (Lever/Greenhouse)", "HRIS (Gusto/BambooHR)", "Payroll"],
        "recommended": ["Engagement Survey", "Performance Review Tool", "Onboarding Platform"],
        "mcp_available": ["google-sheets-mcp", "slack-mcp"],
    },

    # === C-LEVEL ===
    "CRO": {
        "essential": ["CRM (Admin)", "Revenue Dashboard", "Forecasting Tool"],
        "recommended": ["Board Reporting", "Competitive Intelligence", "Strategic Planning"],
        "mcp_available": ["hubspot-mcp", "google-sheets-mcp"],
    },
    "CMO": {
        "essential": ["Marketing Dashboard", "Analytics Suite", "Budget Tracker"],
        "recommended": ["Brand Monitoring", "Market Research", "Creative Approval"],
        "mcp_available": ["google-analytics-mcp", "google-sheets-mcp"],
    },
    "COO": {
        "essential": ["OKR Tool", "Project Portfolio", "Financial Dashboard"],
        "recommended": ["Process Mapping", "Org Chart", "SOP Library"],
        "mcp_available": ["clickup-mcp", "google-sheets-mcp"],
    },
    "CFO": {
        "essential": ["Accounting (QBO/Xero)", "Financial Reporting", "Cash Flow Forecasting"],
        "recommended": ["Tax Planning", "Investor Reporting", "Budget vs Actual"],
        "mcp_available": ["google-sheets-mcp"],
    },
}

# Autonomy levels from SOW
AUTONOMY_DESCRIPTIONS = {
    0: {"name": "Reference", "desc": "Consulta apenas. Nao executa."},
    1: {"name": "Assisted", "desc": "IA prepara, humano executa."},
    2: {"name": "Supervised", "desc": "IA executa, humano valida."},
    3: {"name": "Autonomous", "desc": "IA executa, humano monitora."},
    4: {"name": "Full Auto", "desc": "IA opera sozinha."},
}


# ---------------------------------------------------------------------------
# CORE: DISCOVER TOOLS FOR A ROLE
# ---------------------------------------------------------------------------
def discover_tools(role_name, registry=None):
    """
    Discover available tools for a role.

    Returns tool configuration with essential, recommended, mcp, and autonomy.
    """
    role_upper = role_name.upper()

    # Get from tool registry
    tools = TOOL_REGISTRY.get(role_upper, {
        "essential": ["Project Management Tool", "Communication Tool"],
        "recommended": ["Documentation Tool", "Analytics"],
        "mcp_available": [],
    })

    # Get autonomy from registry SOW data
    if registry:
        role_data = registry.get("roles", {}).get(role_upper, {})
        autonomy_level = role_data.get("autonomy_level", 50)
        executor_type = role_data.get("executor_type", "Hybrid")
    else:
        autonomy_level = 50
        executor_type = "Hybrid"

    # Map autonomy percentage to level
    if autonomy_level >= 80:
        autonomy_tier = 4
    elif autonomy_level >= 60:
        autonomy_tier = 3
    elif autonomy_level >= 40:
        autonomy_tier = 2
    elif autonomy_level >= 20:
        autonomy_tier = 1
    else:
        autonomy_tier = 0

    return {
        "role": role_upper,
        "executor_type": executor_type,
        "autonomy_level": autonomy_level,
        "autonomy_tier": autonomy_tier,
        "autonomy_description": AUTONOMY_DESCRIPTIONS.get(autonomy_tier, {}),
        "tools": {
            "essential": tools.get("essential", []),
            "recommended": tools.get("recommended", []),
            "mcp_available": tools.get("mcp_available", []),
        },
        "command_loader": _generate_command_loader(role_upper),
    }


def discover_all_tools(registry=None, save=True):
    """Discover tools for all roles in registry."""
    if registry is None:
        registry = load_registry()

    roles = registry.get("roles", {})
    results = []

    for role_name, role_data in roles.items():
        ws = role_data.get("weighted_score", 0)
        if ws < 5:  # Skip insignificant roles
            continue

        discovery = discover_tools(role_name, registry=registry)
        results.append(discovery)

        # Update registry
        if save:
            role_data["tools_discovered"] = True
            role_data["tools_essential"] = len(discovery["tools"]["essential"])
            role_data["tools_mcp"] = len(discovery["tools"]["mcp_available"])
            role_data["autonomy_tier"] = discovery["autonomy_tier"]

    if save:
        save_registry(registry)

    return results


# ---------------------------------------------------------------------------
# COMMAND LOADER GENERATOR
# ---------------------------------------------------------------------------
def _generate_command_loader(role_name):
    """
    Generate Command Loader pattern for an agent.

    Defines mandatory tasks and commands that must be loaded
    when the agent is activated (Squad Creator CRITICAL_LOADER_RULE).
    """
    role_lower = role_name.lower().replace("-", " ")

    # Task templates per role category
    task_map = {
        "closer": [
            {"command": "*execute-close", "task": "closer-call-framework.md", "desc": "Framework de call completo"},
            {"command": "*objection-handle", "task": "closer-objections.md", "desc": "Tratamento de objecoes"},
            {"command": "*pipeline-review", "task": "closer-pipeline.md", "desc": "Review de pipeline"},
        ],
        "bdr": [
            {"command": "*outbound-sequence", "task": "bdr-sequence.md", "desc": "Sequencia de outbound"},
            {"command": "*qualify-lead", "task": "bdr-qualification.md", "desc": "Qualificacao de lead"},
            {"command": "*cold-call", "task": "bdr-cold-call.md", "desc": "Script de cold call"},
        ],
        "setter": [
            {"command": "*pre-qualify", "task": "setter-prequalify.md", "desc": "Pre-qualificacao"},
            {"command": "*book-call", "task": "setter-booking.md", "desc": "Agendamento de call"},
        ],
        "copywriter": [
            {"command": "*write-copy", "task": "copy-creation.md", "desc": "Criacao de copy"},
            {"command": "*audit-copy", "task": "copy-audit.md", "desc": "Audit de copy existente"},
        ],
        "media buyer": [
            {"command": "*campaign-setup", "task": "media-campaign.md", "desc": "Setup de campanha"},
            {"command": "*optimize-ads", "task": "media-optimization.md", "desc": "Otimizacao de ads"},
        ],
        "content creator": [
            {"command": "*create-content", "task": "content-creation.md", "desc": "Criacao de conteudo"},
            {"command": "*content-calendar", "task": "content-planning.md", "desc": "Planejamento de conteudo"},
        ],
        "sales manager": [
            {"command": "*team-review", "task": "manager-review.md", "desc": "Review de equipe"},
            {"command": "*run-1on1", "task": "manager-1on1.md", "desc": "Conduzir 1-on-1"},
            {"command": "*comp-plan", "task": "manager-compensation.md", "desc": "Plano de compensacao"},
        ],
        "data analyst": [
            {"command": "*run-analysis", "task": "analyst-report.md", "desc": "Rodar analise"},
            {"command": "*build-dashboard", "task": "analyst-dashboard.md", "desc": "Construir dashboard"},
        ],
    }

    # Find best match
    for key, tasks in task_map.items():
        if key in role_lower:
            return {
                "critical_rule": "Ao ativar este agente, CARREGAR as tasks associadas ANTES de executar.",
                "mandatory_tasks": tasks,
            }

    # Generic fallback
    return {
        "critical_rule": "Ao ativar este agente, CARREGAR as tasks associadas ANTES de executar.",
        "mandatory_tasks": [
            {"command": f"*execute-{role_name.lower()}", "task": f"{role_name.lower()}-main.md", "desc": "Task principal"},
        ],
    }


def generate_command_loader_md(discovery):
    """Generate Command Loader markdown section for agent template."""
    cl = discovery["command_loader"]
    lines = [
        "## COMMAND LOADER",
        f"> REGRA CRITICA: {cl['critical_rule']}",
        "",
        "### Tasks Obrigatorias",
        "| Comando | Task | Descricao |",
        "|---------|------|-----------|",
    ]
    for task in cl["mandatory_tasks"]:
        lines.append(f"| {task['command']} | {task['task']} | {task['desc']} |")

    lines.extend([
        "",
        "### Tools Disponiveis",
        "| Tool | Tipo | Status |",
        "|------|------|--------|",
    ])
    for tool in discovery["tools"]["essential"]:
        lines.append(f"| {tool} | Essential | Pendente |")
    for tool in discovery["tools"]["mcp_available"]:
        lines.append(f"| {tool} | MCP | Configuravel |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== TOOL DISCOVERY v1.0 ===\n")
        results = discover_all_tools(save=True)

        for d in results:
            print(f"  {d['role']:25s}  executor={d['executor_type']:8s}  "
                  f"autonomy={d['autonomy_level']}% (tier {d['autonomy_tier']})")
            print(f"    Essential: {', '.join(d['tools']['essential'][:3])}")
            if d["tools"]["mcp_available"]:
                print(f"    MCP: {', '.join(d['tools']['mcp_available'])}")
            print()

        print(f"  Total roles with tools: {len(results)}")

    elif len(sys.argv) > 1 and sys.argv[1] != "--help":
        role = sys.argv[1].upper()
        print(f"\n=== Tool Discovery for {role} ===\n")
        d = discover_tools(role)
        print(f"  Executor Type: {d['executor_type']}")
        print(f"  Autonomy: {d['autonomy_level']}% (Tier {d['autonomy_tier']})")
        print(f"\n  Essential Tools:")
        for t in d["tools"]["essential"]:
            print(f"    - {t}")
        print(f"\n  Recommended Tools:")
        for t in d["tools"]["recommended"]:
            print(f"    - {t}")
        if d["tools"]["mcp_available"]:
            print(f"\n  MCP Available:")
            for t in d["tools"]["mcp_available"]:
                print(f"    - {t}")
        print(f"\n  Command Loader:")
        for task in d["command_loader"]["mandatory_tasks"]:
            print(f"    {task['command']:25s} -> {task['task']}")

    else:
        print("Uso:")
        print("  python3 tool_discovery.py --all        # Discover tools for all roles")
        print("  python3 tool_discovery.py CLOSER        # Discover tools for specific role")
        sys.exit(1)


if __name__ == "__main__":
    main()
