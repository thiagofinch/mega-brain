#!/usr/bin/env python3
"""
Quality Watchdog - Layer 1 do META-AGENT System v1.0

FUNÇÃO: Detecta agentes em prompts e injeta MANDATORY_SECTIONS no contexto.
        Faz parte do sistema de enforcement de qualidade (warn, não block).

REGRA #28: META-AGENT QUALITY AWARENESS
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
AGENTS_PATH = PROJECT_ROOT / "agents"
JARVIS_SUBAGENTS = PROJECT_ROOT / ".claude" / "jarvis" / "sub-agents"
LOGS_PATH = PROJECT_ROOT / "logs"
QUALITY_GAPS_LOG = LOGS_PATH / "quality_gaps.jsonl"


# ═══════════════════════════════════════════════════════════════════════════
# AGENT DETECTION
# ═══════════════════════════════════════════════════════════════════════════

# Keywords para sub-agents JARVIS
SUBAGENT_KEYWORDS = {
    "chronicler": ["log bonito", "log visual", "chronicler", "formatar log", "status formatado", "resumo visual"],
}

# Dynamic caches (populated on first use)
_PERSON_KEYWORDS_CACHE = None
_CARGO_KEYWORDS_CACHE = None


def _scan_agents_directory(subdir: str) -> Dict:
    """
    Dynamically scan agents/{subdir}/ to build keyword map.
    Each subdirectory name becomes an agent key, and keywords are
    generated from the directory name parts.
    """
    keywords = {}
    scan_path = AGENTS_PATH / subdir
    if not scan_path.exists():
        return keywords

    for entry in scan_path.iterdir():
        if entry.is_dir():
            agent_name = entry.name.lower()
            # Generate keywords from directory name
            parts = agent_name.replace('-', ' ').replace('_', ' ').split()
            kws = [agent_name.replace('-', ' ')]  # full name as keyword
            # Add individual meaningful parts (skip very short ones)
            for part in parts:
                if len(part) >= 3:
                    kws.append(part)
            # Also add the hyphenated form
            if '-' in agent_name or '_' in agent_name:
                kws.append(agent_name)
            keywords[agent_name] = list(set(kws))

    return keywords


def _get_person_keywords() -> Dict:
    """Lazily load person keywords from agents/persons/ directory."""
    global _PERSON_KEYWORDS_CACHE
    if _PERSON_KEYWORDS_CACHE is None:
        _PERSON_KEYWORDS_CACHE = _scan_agents_directory("persons")
    return _PERSON_KEYWORDS_CACHE


def _get_cargo_keywords() -> Dict:
    """Lazily load cargo keywords from agents/cargo/ directory (recursive)."""
    global _CARGO_KEYWORDS_CACHE
    if _CARGO_KEYWORDS_CACHE is None:
        _CARGO_KEYWORDS_CACHE = {}
        cargo_path = AGENTS_PATH / "cargo"
        if cargo_path.exists():
            # Scan all subdirectories recursively for agent folders containing AGENT.md
            for agent_md in cargo_path.rglob("AGENT.md"):
                agent_dir = agent_md.parent
                agent_name = agent_dir.name.lower()
                parts = agent_name.replace('-', ' ').replace('_', ' ').split()
                kws = [agent_name.replace('-', ' ')]
                for part in parts:
                    if len(part) >= 3:
                        kws.append(part)
                _CARGO_KEYWORDS_CACHE[agent_name] = list(set(kws))
    return _CARGO_KEYWORDS_CACHE


def detect_agent_in_prompt(prompt: str) -> Dict:
    """
    Detecta qual agente está sendo requisitado no prompt.

    Returns:
        dict: {type: "subagent"|"person"|"cargo"|None, name: str|None}
    """
    prompt_lower = prompt.lower()

    # Detecta sub-agent JARVIS (prioridade mais alta)
    for agent, keywords in SUBAGENT_KEYWORDS.items():
        if any(kw in prompt_lower for kw in keywords):
            return {"type": "subagent", "name": agent}

    # Detecta PERSON agent (dynamically from agents/persons/ directory)
    for agent, keywords in _get_person_keywords().items():
        if any(kw in prompt_lower for kw in keywords):
            return {"type": "person", "name": agent}

    # Detecta CARGO agent (dynamically from agents/cargo/ directory)
    for agent, keywords in _get_cargo_keywords().items():
        if any(kw in prompt_lower for kw in keywords):
            return {"type": "cargo", "name": agent}

    return {"type": None, "name": None}


# ═══════════════════════════════════════════════════════════════════════════
# MANDATORY SECTIONS EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_mandatory_sections(agent_path: Path) -> Dict:
    """
    Extrai MANDATORY_SECTIONS do header do AGENT.md.

    Prioridade:
    1. Bloco formal <!-- MANDATORY --> ... <!-- End MANDATORY -->
    2. Seção ## ⚠️ MANDATORY OUTPUT SECTIONS
    3. Fallback: primeiras 50 linhas
    """
    agent_md = agent_path / "AGENT.md"
    if not agent_md.exists():
        return {"found": False, "content": "", "lines": 0}

    try:
        content = agent_md.read_text(encoding='utf-8')
    except Exception as e:
        return {"found": False, "content": "", "lines": 0, "error": str(e)}

    # Método 1: Bloco formal com comentários HTML
    match = re.search(
        r'<!-- MANDATORY -->(.+?)<!-- End MANDATORY -->',
        content,
        re.DOTALL | re.IGNORECASE
    )
    if match:
        return {
            "found": True,
            "method": "html_comments",
            "content": match.group(1).strip(),
            "lines": len(match.group(1).split('\n'))
        }

    # Método 2: Seção com header markdown
    match = re.search(
        r'## ⚠️ MANDATORY OUTPUT SECTIONS.*?(?=## [^⚠️]|$)',
        content,
        re.DOTALL | re.IGNORECASE
    )
    if match:
        return {
            "found": True,
            "method": "markdown_header",
            "content": match.group(0).strip(),
            "lines": len(match.group(0).split('\n'))
        }

    # Método 3: Fallback - primeiras 50 linhas (para agents sem MANDATORY formal)
    lines = content.split('\n')[:50]
    return {
        "found": False,
        "method": "fallback_header",
        "content": '\n'.join(lines),
        "lines": 50
    }


def resolve_agent_path(agent_info: Dict) -> Optional[Path]:
    """Resolve o caminho do agente baseado no tipo."""
    if not agent_info.get("name"):
        return None

    agent_name = agent_info["name"].upper()

    if agent_info["type"] == "subagent":
        return JARVIS_SUBAGENTS / agent_name
    elif agent_info["type"] == "person":
        return AGENTS_PATH / "persons" / agent_name
    elif agent_info["type"] == "cargo":
        # Cargo agents têm estrutura diferente
        cargo_paths = {
            "CRO": AGENTS_PATH / "cargo" / "C-LEVEL" / "CRO",
            "CFO": AGENTS_PATH / "cargo" / "C-LEVEL" / "CFO",
            "SALES-MANAGER": AGENTS_PATH / "cargo" / "SALES" / "SALES-MANAGER",
            "closer": AGENTS_PATH / "cargo" / "SALES" / "closer",
            "SDR": AGENTS_PATH / "cargo" / "SALES" / "SDR",
        }
        return cargo_paths.get(agent_name)

    return None


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT INJECTION
# ═══════════════════════════════════════════════════════════════════════════

def inject_quality_context(prompt: str) -> str:
    """
    Injeta contexto de qualidade se agente detectado.

    Retorna string vazia se nenhum agente detectado.
    """
    agent_info = detect_agent_in_prompt(prompt)

    if not agent_info.get("name"):
        return ""

    agent_path = resolve_agent_path(agent_info)
    if not agent_path or not agent_path.exists():
        return ""

    mandatory = extract_mandatory_sections(agent_path)

    # Sempre injeta contexto se agente detectado
    context = f"""
[QUALITY WATCHDOG ACTIVATED]
Agent detected: {agent_info['name']}
Type: {agent_info['type']}
Path: {agent_path}

"""

    if mandatory.get("found"):
        context += f"""--- MANDATORY SECTIONS (MUST INCLUDE IN OUTPUT) ---
{mandatory['content']}
--- END MANDATORY SECTIONS ---

⚠️ OUTPUT WILL BE VALIDATED AGAINST THESE REQUIREMENTS
⚠️ Quality scoring active - minimum recommended: 70/100
"""
    else:
        context += f"""--- AGENT HEADER (First 50 lines) ---
{mandatory['content']}
--- END HEADER ---

ℹ️ No formal MANDATORY_SECTIONS found. Using header as reference.
"""

    return context


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def log_quality_gap(agent: str, score: int, missing: list, agent_type: str = "unknown"):
    """
    Loga gap de qualidade para análise do DOCTOR (Layer 2).

    Não bloqueia - apenas registra para análise posterior.
    """
    # Garantir que diretório existe
    QUALITY_GAPS_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "agent_type": agent_type,
        "score": score,
        "missing_sections": missing,
        "status": "gap_detected",
        "action_taken": "logged_for_review"
    }

    try:
        with open(QUALITY_GAPS_LOG, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # Falha silenciosa - não deve interromper fluxo
        pass


def log_watchdog_activation(agent_info: Dict, mandatory_found: bool):
    """Loga ativação do watchdog para auditoria."""
    log_file = LOGS_PATH / "watchdog_activations.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_info.get("name"),
        "type": agent_info.get("type"),
        "mandatory_found": mandatory_found
    }

    try:
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def process_prompt(prompt: str) -> Dict:
    """
    Processa prompt e retorna contexto de qualidade se aplicável.

    Interface principal para integração com user_prompt_submit.py
    """
    agent_info = detect_agent_in_prompt(prompt)

    result = {
        "agent_detected": agent_info.get("name") is not None,
        "agent_info": agent_info,
        "context": "",
        "mandatory_found": False
    }

    if agent_info.get("name"):
        context = inject_quality_context(prompt)
        result["context"] = context
        result["mandatory_found"] = "MANDATORY SECTIONS" in context

        # Log activation
        log_watchdog_activation(agent_info, result["mandatory_found"])

    return result


# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    Hook entry point for Claude Code UserPromptSubmit event.
    Reads JSON from stdin, outputs JSON to stdout.
    """
    import sys

    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        prompt = hook_input.get('prompt', '')
        if not prompt:
            print(json.dumps({'continue': True}))
            return

        result = process_prompt(prompt)

        feedback = result.get('context') if result.get('agent_detected') else None

        print(json.dumps({
            'continue': True,
            'feedback': feedback if feedback else None
        }))

    except Exception:
        print(json.dumps({'continue': True}))


def cli_test():
    """CLI test mode - run directly for debugging."""
    import sys

    if len(sys.argv) > 1:
        test_prompt = " ".join(sys.argv[1:])
    else:
        test_prompt = "me dá um log bonito do conteúdo do Alex Hormozi"

    print(f"Testing prompt: {test_prompt}\n")

    result = process_prompt(test_prompt)

    print(f"Agent detected: {result['agent_detected']}")
    print(f"Agent info: {result['agent_info']}")
    print(f"Mandatory found: {result['mandatory_found']}")
    print(f"\nContext to inject:\n{result['context'][:500]}...")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        cli_test()
    else:
        main()
