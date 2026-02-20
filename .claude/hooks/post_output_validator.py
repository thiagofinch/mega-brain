#!/usr/bin/env python3
"""
Post Output Validator - Layer 1 do META-AGENT System v1.0

FUNÇÃO: Valida compliance do output vs especificação do agente.
        AVISA sobre gaps mas NÃO BLOQUEIA entrega.

REGRA #28: META-AGENT QUALITY AWARENESS (WARN, NOT BLOCK)
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOGS_PATH = PROJECT_ROOT / "logs"
VALIDATION_LOG = LOGS_PATH / "output_validations.jsonl"


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY MARKERS
# ═══════════════════════════════════════════════════════════════════════════

# Marcadores padrão para outputs visuais (usado por CHRONICLER e similares)
VISUAL_MARKERS = [
    {
        "name": "ASCII Header",
        "pattern": r"╔═+.*═+╗",
        "weight": 10,
        "description": "Cabeçalho com bordas duplas"
    },
    {
        "name": "Progress Bar",
        "pattern": r"[█▓░]{5,}|████+",
        "weight": 10,
        "description": "Barras de progresso visuais"
    },
    {
        "name": "Metrics Panel",
        "pattern": r"┌─.*(?:MÉTRICA|PAINEL|MÉTRICAS)",
        "weight": 10,
        "description": "Painel de métricas estruturado"
    },
    {
        "name": "Changes Section",
        "pattern": r"O QUE MUDOU|NOVIDADES|MUDANÇAS",
        "weight": 15,
        "description": "Seção de mudanças/novidades"
    },
    {
        "name": "Personal Notes",
        "pattern": r"NOTAS DO|OBSERVAÇÕES|— \w+$",
        "weight": 10,
        "description": "Notas pessoais do agente"
    },
    {
        "name": "ASCII Boxes",
        "pattern": r"[┌┐└┘├┤│─┬┴┼]{3,}",
        "weight": 5,
        "description": "Caixas ASCII estruturadas"
    },
    {
        "name": "Explanations",
        "pattern": r"\[[^\]]{10,}\]",
        "weight": 5,
        "description": "Explicações entre colchetes"
    },
    {
        "name": "Section Dividers",
        "pattern": r"[═─━]{10,}",
        "weight": 5,
        "description": "Divisores de seção"
    },
]

# Marcadores para outputs analíticos
ANALYTICAL_MARKERS = [
    {
        "name": "Data Points",
        "pattern": r"\d+[%,.]?\d*",
        "weight": 5,
        "description": "Números e porcentagens"
    },
    {
        "name": "Bullet Points",
        "pattern": r"^[\s]*[-•*]\s",
        "weight": 3,
        "description": "Lista com bullets"
    },
    {
        "name": "Headers",
        "pattern": r"^#{1,3}\s",
        "weight": 3,
        "description": "Headers markdown"
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# QUALITY SCORING
# ═══════════════════════════════════════════════════════════════════════════

def calculate_quality_score(
    output: str,
    markers: List[Dict] = None,
    agent_type: str = "visual"
) -> Dict:
    """
    Calcula score de qualidade do output.

    Args:
        output: Texto do output a validar
        markers: Lista de marcadores customizados (opcional)
        agent_type: "visual" ou "analytical" para selecionar marcadores

    Returns:
        dict com score, passing, details, missing
    """
    if markers is None:
        markers = VISUAL_MARKERS if agent_type == "visual" else ANALYTICAL_MARKERS

    score = 0
    max_score = sum(m["weight"] for m in markers)
    details = []
    missing = []
    found = []

    for marker in markers:
        pattern = marker["pattern"]
        weight = marker["weight"]
        name = marker["name"]

        if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
            score += weight
            details.append(f"✅ {name}: +{weight}")
            found.append(name)
        else:
            missing.append(name)
            details.append(f"❌ {name}: 0")

    # Normaliza para 100
    normalized_score = int((score / max_score) * 100) if max_score > 0 else 0

    return {
        "score": normalized_score,
        "raw_score": score,
        "max_score": max_score,
        "passing": normalized_score >= 70,
        "details": details,
        "missing": missing,
        "found": found,
        "markers_checked": len(markers)
    }


def validate_output(output: str, agent_name: str, agent_type: str = "visual") -> Dict:
    """
    Valida output completo. AVISA mas NÃO BLOQUEIA.

    Esta é a função principal chamada após geração de output.
    MODIFICAÇÃO CRÍTICA: action = "warn" em vez de "block"

    Args:
        output: Texto do output gerado
        agent_name: Nome do agente que gerou
        agent_type: Tipo do agente ("visual", "analytical")

    Returns:
        dict com resultado da validação
    """
    result = calculate_quality_score(output, agent_type=agent_type)

    result["agent"] = agent_name
    result["agent_type"] = agent_type
    result["timestamp"] = datetime.now().isoformat()

    if not result["passing"]:
        # MODIFICAÇÃO: Avisa em vez de bloquear
        result["warning"] = (
            f"⚠️ Quality score: {result['score']}/100\n"
            f"Missing elements: {', '.join(result['missing'])}\n"
            f"Consider adding these elements for better quality."
        )
        result["action"] = "warn"  # NÃO "block"
        result["recommendation"] = "Output delivered with quality warning"
    else:
        result["action"] = "pass"
        result["recommendation"] = "Output quality acceptable"

    # Log validation
    log_validation(result)

    return result


def validate_against_spec(output: str, spec: str, agent_name: str) -> Dict:
    """
    Valida output contra especificação customizada.

    Para casos onde MANDATORY_SECTIONS define requisitos específicos.
    """
    result = {
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "spec_based": True,
        "requirements_met": [],
        "requirements_missing": []
    }

    # Extrai requisitos da spec
    requirements = extract_requirements_from_spec(spec)

    score = 0
    for req in requirements:
        if re.search(req["pattern"], output, re.IGNORECASE | re.DOTALL):
            result["requirements_met"].append(req["name"])
            score += req.get("weight", 10)
        else:
            result["requirements_missing"].append(req["name"])

    max_score = sum(r.get("weight", 10) for r in requirements)
    result["score"] = int((score / max_score) * 100) if max_score > 0 else 100
    result["passing"] = result["score"] >= 70

    if not result["passing"]:
        result["action"] = "warn"
        result["warning"] = f"Score: {result['score']}. Missing: {result['requirements_missing']}"
    else:
        result["action"] = "pass"

    return result


def extract_requirements_from_spec(spec: str) -> List[Dict]:
    """
    Extrai requisitos de uma spec MANDATORY_SECTIONS.

    Formato esperado na spec:
    | Section | Required | Marker | Example |
    """
    requirements = []

    # Tenta extrair da tabela markdown
    table_pattern = r'\|\s*([^|]+)\s*\|\s*YES\s*\|\s*`([^`]+)`\s*\|'
    matches = re.findall(table_pattern, spec, re.IGNORECASE)

    for name, marker in matches:
        requirements.append({
            "name": name.strip(),
            "pattern": re.escape(marker.strip()),
            "weight": 10
        })

    # Se não encontrou tabela, usa marcadores padrão
    if not requirements:
        return [{"name": "default", "pattern": ".", "weight": 100}]

    return requirements


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def log_validation(result: Dict):
    """Loga resultado da validação."""
    VALIDATION_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": result.get("timestamp", datetime.now().isoformat()),
        "agent": result.get("agent", "unknown"),
        "score": result.get("score", 0),
        "passing": result.get("passing", False),
        "action": result.get("action", "unknown"),
        "missing": result.get("missing", []),
        "found": result.get("found", [])
    }

    try:
        with open(VALIDATION_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Falha silenciosa


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def should_trigger_doctor(result: Dict, threshold: int = 50) -> bool:
    """
    Determina se deve acionar o DOCTOR (Layer 2) para propor fixes.

    Threshold mais baixo (50) aciona propostas de melhoria.
    Threshold 70 é apenas warning.
    """
    return result.get("score", 100) < threshold


def format_warning_message(result: Dict) -> str:
    """Formata mensagem de warning para exibição."""
    if result.get("action") == "pass":
        return ""

    return f"""
┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️ QUALITY WARNING                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Agent: {result.get('agent', 'unknown'):<54} │
│  Score: {result.get('score', 0)}/100 {'(PASSING)' if result.get('passing') else '(BELOW THRESHOLD)':>43} │
├─────────────────────────────────────────────────────────────────────┤
│  Missing: {', '.join(result.get('missing', []))[:53]:<53} │
└─────────────────────────────────────────────────────────────────────┘
"""


# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test output
    test_output = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ALEX HORMOZI - DNA CONSOLIDADO                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─ MÉTRICAS ─────────────────────────────────────────────────────────────────────┐
│  Total elementos: 260                                                          │
│  Progresso: ████████████████████░░░░░░░░░░░░░░░░░░░░ 50%                       │
└────────────────────────────────────────────────────────────────────────────────┘

O QUE MUDOU DESDE O ÚLTIMO LOG:
- Adicionados 30 novos frameworks
- Atualizado DNA-CONFIG.yaml

NOTAS DO CHRONICLER:
"O conhecimento do Hormozi está consolidando bem."

— Chronicler
"""

    result = validate_output(test_output, "chronicler", "visual")

    print(f"Score: {result['score']}/100")
    print(f"Passing: {result['passing']}")
    print(f"Action: {result['action']}")
    print(f"\nDetails:")
    for detail in result['details']:
        print(f"  {detail}")

    if result.get('warning'):
        print(f"\n{result['warning']}")

    print(format_warning_message(result))
