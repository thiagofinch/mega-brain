#!/usr/bin/env python3
"""
Agent Doctor - Layer 2 do META-AGENT System v1.0

FUNÇÃO: Diagnostica gaps de qualidade e PROPÕE fixes para revisão humana.
        NÃO aplica fixes automaticamente - salva em doctor_proposals.jsonl.

REGRA #28: META-AGENT QUALITY AWARENESS
PRINCÍPIO: DOCTOR PROPÕE, NÃO APLICA
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOGS_PATH = PROJECT_ROOT / "logs"
DOCTOR_PROPOSALS_LOG = LOGS_PATH / "doctor_proposals.jsonl"
DOCTOR_FIXES_LOG = LOGS_PATH / "doctor_fixes.jsonl"


# ═══════════════════════════════════════════════════════════════════════════
# MANDATORY HEADER TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════

MANDATORY_HEADER_TEMPLATE = '''## ⚠️ MANDATORY OUTPUT SECTIONS (NEVER SKIP)
<!-- MANDATORY -->

| Section | Required | Marker | Example |
|---------|----------|--------|---------|
{sections_table}

## MINIMUM OUTPUT REQUIREMENTS
{requirements_list}

## QUALITY CHECKLIST (score 0-100)
- Section present: +10 points each
- Section complete: +15 points each
- Format correct: +10 points each
- MINIMUM TO DELIVER: 70 points

<!-- End MANDATORY -->

'''


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSIS
# ═══════════════════════════════════════════════════════════════════════════

def diagnose_gap(agent_path: Path, missing_sections: List[str]) -> Dict:
    """
    Diagnostica a causa raiz do gap de qualidade e propõe estratégia de fix.

    Args:
        agent_path: Caminho para pasta do agente
        missing_sections: Lista de seções que faltaram no output

    Returns:
        dict com diagnóstico e proposta de fix
    """
    agent_md = agent_path / "AGENT.md"

    if not agent_md.exists():
        return {
            "root_cause": "agent_not_found",
            "fix_strategy": "create_agent",
            "changes_needed": [],
            "error": f"AGENT.md not found at {agent_md}"
        }

    try:
        content = agent_md.read_text(encoding='utf-8')
    except Exception as e:
        return {
            "root_cause": "read_error",
            "fix_strategy": "manual_review",
            "changes_needed": [],
            "error": str(e)
        }

    diagnosis = {
        "root_cause": None,
        "fix_strategy": None,
        "changes_needed": [],
        "agent_path": str(agent_path),
        "file_stats": {
            "total_lines": len(content.split('\n')),
            "total_chars": len(content)
        }
    }

    # Verificação 1: Tem MANDATORY_SECTIONS header?
    has_mandatory = "MANDATORY OUTPUT SECTIONS" in content or "<!-- MANDATORY -->" in content

    if not has_mandatory:
        diagnosis["root_cause"] = "no_mandatory_header"
        diagnosis["fix_strategy"] = "add_mandatory_header"
        diagnosis["changes_needed"].append({
            "action": "prepend",
            "description": "Add MANDATORY_SECTIONS header to top of file",
            "content_preview": generate_mandatory_header(missing_sections)[:200] + "..."
        })
    else:
        # MANDATORY existe, mas seções não estão completas
        diagnosis["root_cause"] = "incomplete_mandatory"
        diagnosis["fix_strategy"] = "update_mandatory_header"
        diagnosis["changes_needed"].append({
            "action": "update_mandatory",
            "description": "Update MANDATORY_SECTIONS with missing items",
            "missing": missing_sections
        })

    # Verificação 2: Arquivo muito longo (pode ser truncado)?
    lines = len(content.split('\n'))
    if lines > 200:
        diagnosis["changes_needed"].append({
            "action": "generate_compact_summary",
            "description": f"Agent file has {lines} lines - may be truncated in context",
            "reason": "Long files may lose MANDATORY sections when loaded",
            "suggested_max": 150
        })

    # Verificação 3: MANDATORY está no final (bad position)?
    if has_mandatory:
        mandatory_position = content.find("MANDATORY OUTPUT SECTIONS")
        if mandatory_position > len(content) * 0.3:  # Depois de 30% do arquivo
            diagnosis["changes_needed"].append({
                "action": "move_mandatory_to_top",
                "description": "MANDATORY section is not at the top of file",
                "current_position": f"{int(mandatory_position/len(content)*100)}% into file",
                "recommended": "First 50 lines"
            })

    return diagnosis


def generate_mandatory_header(missing_sections: List[str]) -> str:
    """
    Gera header MANDATORY_SECTIONS baseado nas seções faltantes.
    """
    # Mapeia seções para marcadores
    section_markers = {
        "ASCII Header": ("╔═══", "Large title with double border"),
        "Progress Bar": ("████", "Visual progress ████████░░"),
        "Metrics Panel": ("┌─ MÉTRICAS", "Metrics card with [explanations]"),
        "Changes Section": ("O QUE MUDOU", "What changed since last"),
        "Personal Notes": ("NOTAS DO", "Personal observations from agent"),
        "ASCII Boxes": ("┌───┐", "Structured information boxes"),
        "Explanations": ("[explanation]", "Technical terms with context"),
    }

    sections_table = ""
    requirements_list = ""

    for section in missing_sections:
        if section in section_markers:
            marker, example = section_markers[section]
            sections_table += f"| {section} | YES | `{marker}` | {example} |\n"
            requirements_list += f"- [ ] Include {section}\n"
        else:
            sections_table += f"| {section} | YES | `{section[:5]}` | Required element |\n"
            requirements_list += f"- [ ] Include {section}\n"

    return MANDATORY_HEADER_TEMPLATE.format(
        sections_table=sections_table.strip(),
        requirements_list=requirements_list.strip()
    )


# ═══════════════════════════════════════════════════════════════════════════
# PROPOSAL SYSTEM (NÃO APLICA AUTOMATICAMENTE)
# ═══════════════════════════════════════════════════════════════════════════

def create_fix_proposal(agent_path: Path, diagnosis: Dict) -> Dict:
    """
    Cria proposta de fix para revisão humana.

    IMPORTANTE: NÃO modifica arquivos diretamente.
    Salva proposta em doctor_proposals.jsonl para revisão.
    """
    proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    proposal = {
        "proposal_id": proposal_id,
        "timestamp": datetime.now().isoformat(),
        "agent": agent_path.name if agent_path else "unknown",
        "agent_path": str(agent_path) if agent_path else None,
        "diagnosis": {
            "root_cause": diagnosis.get("root_cause"),
            "fix_strategy": diagnosis.get("fix_strategy"),
            "file_stats": diagnosis.get("file_stats", {})
        },
        "proposed_changes": diagnosis.get("changes_needed", []),
        "status": "pending_approval",
        "reviewed_by": None,
        "review_date": None,
        "applied": False
    }

    # Salva proposta para revisão humana
    save_proposal(proposal)

    # Log que proposta foi criada (não aplicada)
    log_proposal_created(proposal)

    return {
        "success": True,
        "action": "proposed",
        "proposal_id": proposal_id,
        "review_required": True,
        "message": f"Fix proposal created: {proposal_id}. Awaiting human review."
    }


def save_proposal(proposal: Dict):
    """Salva proposta no log de proposals."""
    DOCTOR_PROPOSALS_LOG.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(DOCTOR_PROPOSALS_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(proposal, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error saving proposal: {e}")


def log_proposal_created(proposal: Dict):
    """Loga que proposta foi criada (para histórico/auditoria)."""
    DOCTOR_FIXES_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "proposal_id": proposal.get("proposal_id"),
        "agent": proposal.get("agent"),
        "root_cause": proposal.get("diagnosis", {}).get("root_cause"),
        "fix_strategy": proposal.get("diagnosis", {}).get("fix_strategy"),
        "status": "proposed_pending_review",
        "auto_applied": False
    }

    try:
        with open(DOCTOR_FIXES_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# PROPOSAL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def list_pending_proposals() -> List[Dict]:
    """Lista todas as propostas pendentes de aprovação."""
    if not DOCTOR_PROPOSALS_LOG.exists():
        return []

    pending = []
    try:
        with open(DOCTOR_PROPOSALS_LOG, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    proposal = json.loads(line)
                    if proposal.get("status") == "pending_approval":
                        pending.append(proposal)
    except Exception:
        pass

    return pending


def approve_proposal(proposal_id: str, reviewer: str = "human") -> Dict:
    """
    Marca proposta como aprovada (ainda não aplica).

    Para aplicar de fato, use apply_approved_proposal().
    """
    proposals = []
    approved = None

    if DOCTOR_PROPOSALS_LOG.exists():
        with open(DOCTOR_PROPOSALS_LOG, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    proposal = json.loads(line)
                    if proposal.get("proposal_id") == proposal_id:
                        proposal["status"] = "approved"
                        proposal["reviewed_by"] = reviewer
                        proposal["review_date"] = datetime.now().isoformat()
                        approved = proposal
                    proposals.append(proposal)

    if approved:
        # Reescreve arquivo com status atualizado
        with open(DOCTOR_PROPOSALS_LOG, "w", encoding='utf-8') as f:
            for p in proposals:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        return {"success": True, "proposal": approved}

    return {"success": False, "error": f"Proposal {proposal_id} not found"}


def reject_proposal(proposal_id: str, reason: str, reviewer: str = "human") -> Dict:
    """Marca proposta como rejeitada."""
    proposals = []
    rejected = None

    if DOCTOR_PROPOSALS_LOG.exists():
        with open(DOCTOR_PROPOSALS_LOG, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    proposal = json.loads(line)
                    if proposal.get("proposal_id") == proposal_id:
                        proposal["status"] = "rejected"
                        proposal["reviewed_by"] = reviewer
                        proposal["review_date"] = datetime.now().isoformat()
                        proposal["rejection_reason"] = reason
                        rejected = proposal
                    proposals.append(proposal)

    if rejected:
        with open(DOCTOR_PROPOSALS_LOG, "w", encoding='utf-8') as f:
            for p in proposals:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        return {"success": True, "proposal": rejected}

    return {"success": False, "error": f"Proposal {proposal_id} not found"}


# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def process_quality_gap(
    agent_path: Path,
    missing_sections: List[str],
    score: int
) -> Dict:
    """
    Processa um gap de qualidade detectado pelo WATCHDOG.

    Interface principal para integração com post_output_validator.py

    Args:
        agent_path: Path para a pasta do agente
        missing_sections: Seções que faltaram no output
        score: Score de qualidade (0-100)

    Returns:
        dict com resultado do processamento
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_path.name if agent_path else "unknown",
        "score": score,
        "missing": missing_sections
    }

    # Só processa se score for muito baixo (< 50)
    if score >= 50:
        result["action"] = "skipped"
        result["reason"] = "Score above proposal threshold (50)"
        return result

    # Diagnostica o problema
    diagnosis = diagnose_gap(agent_path, missing_sections)

    # Cria proposta (não aplica)
    proposal_result = create_fix_proposal(agent_path, diagnosis)

    result["diagnosis"] = diagnosis
    result["proposal"] = proposal_result
    result["action"] = "proposal_created"

    return result


# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            # Listar propostas pendentes
            pending = list_pending_proposals()
            print(f"Pending proposals: {len(pending)}\n")
            for p in pending:
                print(f"  {p['proposal_id']}: {p['agent']} - {p['diagnosis']['root_cause']}")

        elif command == "approve" and len(sys.argv) > 2:
            # Aprovar proposta
            proposal_id = sys.argv[2]
            result = approve_proposal(proposal_id)
            print(f"Approve result: {result}")

        elif command == "reject" and len(sys.argv) > 3:
            # Rejeitar proposta
            proposal_id = sys.argv[2]
            reason = sys.argv[3]
            result = reject_proposal(proposal_id, reason)
            print(f"Reject result: {result}")

        else:
            print("Usage:")
            print("  python agent_doctor.py list                    - List pending proposals")
            print("  python agent_doctor.py approve <proposal_id>   - Approve proposal")
            print("  python agent_doctor.py reject <proposal_id> <reason> - Reject proposal")

    else:
        # Test mode
        test_path = PROJECT_ROOT / ".claude" / "jarvis" / "sub-agents" / "chronicler"
        test_missing = ["ASCII Header", "Progress Bar", "Changes Section"]

        print(f"Testing diagnosis for: {test_path}\n")

        diagnosis = diagnose_gap(test_path, test_missing)
        print(f"Diagnosis:")
        print(f"  Root cause: {diagnosis['root_cause']}")
        print(f"  Fix strategy: {diagnosis['fix_strategy']}")
        print(f"  Changes needed: {len(diagnosis['changes_needed'])}")

        print("\nCreating proposal (not applying)...")
        result = create_fix_proposal(test_path, diagnosis)
        print(f"Result: {result}")
