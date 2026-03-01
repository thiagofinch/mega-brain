#!/usr/bin/env python3
"""
Skill Router - Sistema de Roteamento Semântico v2.0

Escaneia SKILLS e SUB-AGENTS, extrai metadados e faz matching com prompts.

REGRA #27: Skills são auto-ativadas quando keywords matcham no prompt do usuário.

v2.0 CHANGES:
- Adicionado suporte a SUB-AGENTS (/.claude/jarvis/sub-agents/)
- Campo "type": "skill" | "sub-agent" no índice
- Sub-agents têm AGENT.md + opcional SOUL.md
- Separação clara: sub-agents são súbditos do JARVIS, não do Council

ARQUITETURA:
┌─────────────────────────────────────────────────────────────────────────────┐
│  /.claude/skills/                    → SKILLS (auto-routing)               │
│  /.claude/jarvis/sub-agents/         → SUB-AGENTS (auto-routing)           │
│  /agents/                         → CONCLAVE ONLY (via /conclave)       │
└─────────────────────────────────────────────────────────────────────────────┘
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
SKILLS_PATH = PROJECT_ROOT / ".claude" / "skills"
SUBAGENTS_PATH = PROJECT_ROOT / ".claude" / "jarvis" / "sub-agents"
INDEX_PATH = PROJECT_ROOT / ".claude" / "mission-control" / "SKILL-INDEX.json"
WHITELIST_PATH = PROJECT_ROOT / ".claude" / "SKILL-WHITELIST.json"

# M-09: Allowed base directories for skill/sub-agent resolution
ALLOWED_SKILL_PREFIXES = (
    os.path.normpath('.claude/skills/'),
    os.path.normpath('.claude/jarvis/sub-agents/'),
)


def scan_skills() -> List[Tuple[Path, str]]:
    """Lista todas as pastas de skills válidas com tipo."""
    items = []

    # Scan skills
    if SKILLS_PATH.exists():
        for item in SKILLS_PATH.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    items.append((item, "skill"))

    # Scan sub-agents
    if SUBAGENTS_PATH.exists():
        for item in SUBAGENTS_PATH.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                agent_md = item / "AGENT.md"
                if agent_md.exists():
                    items.append((item, "sub-agent"))

    return items


def extract_metadata(item_path: Path, item_type: str) -> Dict:
    """Extrai metadados de SKILL.md ou AGENT.md."""

    if item_type == "skill":
        md_file = item_path / "SKILL.md"
    else:
        md_file = item_path / "AGENT.md"

    if not md_file.exists():
        return {}

    try:
        content = md_file.read_text(encoding='utf-8')
    except Exception:
        return {}

    # Extrai header (primeiras 40 linhas para garantir captura)
    lines = content.split('\n')[:40]
    header = '\n'.join(lines)

    metadata = {
        "path": str(item_path.relative_to(PROJECT_ROOT)),
        "name": item_path.name,
        "type": item_type,
        "auto_trigger": "",
        "keywords": [],
        "priority": "MÉDIA",
        "description": ""
    }

    # Auto-Trigger (múltiplos formatos)
    for pattern in [r'\*\*Auto-Trigger:\*\*\s*(.+)', r'> \*\*Auto-Trigger:\*\*\s*(.+)']:
        match = re.search(pattern, header)
        if match:
            metadata["auto_trigger"] = match.group(1).strip()
            break

    # Keywords - múltiplos formatos suportados
    for pattern in [r'\*\*Keywords:\*\*\s*(.+)', r'> \*\*Keywords:\*\*\s*(.+)']:
        match = re.search(pattern, header)
        if match:
            raw = match.group(1).strip()
            # Parse keywords (pode ser "a", "b", "c" ou a, b, c ou [a, b, c])
            keywords = re.findall(r'["\']?([^",\'\[\]]+)["\']?', raw)
            metadata["keywords"] = [k.strip().lower() for k in keywords if k.strip() and len(k.strip()) > 1]
            break

    # Prioridade
    for pattern in [r'\*\*Prioridade:\*\*\s*(ALTA|MÉDIA|BAIXA)', r'> \*\*Prioridade:\*\*\s*(ALTA|MÉDIA|BAIXA)']:
        match = re.search(pattern, header, re.I)
        if match:
            metadata["priority"] = match.group(1).upper()
            break

    # Description (primeira linha após # Header)
    match = re.search(r'^#\s+[^\n]+\n+##?\s*([^\n]+)', content)
    if match:
        metadata["description"] = match.group(1).strip()

    # Para sub-agents, verificar se tem SOUL.md
    if item_type == "sub-agent":
        soul_path = item_path / "SOUL.md"
        metadata["has_soul"] = soul_path.exists()

    return metadata


def build_index() -> Dict:
    """Constrói índice completo de skills e sub-agents."""
    items = scan_skills()

    index = {
        "version": "2.0.0",
        "skills_count": 0,
        "subagents_count": 0,
        "total_count": len(items),
        "skills": {},
        "subagents": {},
        "keyword_map": {}
    }

    for item_path, item_type in items:
        metadata = extract_metadata(item_path, item_type)
        if metadata and metadata.get("keywords"):
            item_name = metadata["name"]

            if item_type == "skill":
                index["skills"][item_name] = metadata
                index["skills_count"] += 1
            else:
                index["subagents"][item_name] = metadata
                index["subagents_count"] += 1

            # Popula keyword_map (unificado)
            for keyword in metadata.get("keywords", []):
                if keyword not in index["keyword_map"]:
                    index["keyword_map"][keyword] = []
                index["keyword_map"][keyword].append({
                    "name": item_name,
                    "type": item_type,
                    "path": metadata["path"],
                    "priority": metadata["priority"]
                })

    # Salva índice
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return index


def match_prompt(prompt: str, index: Dict = None) -> List[Dict]:
    """Retorna skills e sub-agents que matcham com o prompt."""
    if index is None:
        if INDEX_PATH.exists():
            try:
                with open(INDEX_PATH, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            except Exception:
                index = build_index()
        else:
            index = build_index()

    prompt_lower = prompt.lower()
    matches = []
    seen_items = set()

    # Ordem de prioridade
    priority_order = {"ALTA": 0, "MÉDIA": 1, "BAIXA": 2}

    for keyword, item_list in index.get("keyword_map", {}).items():
        # Match por palavra inteira ou substring significativa
        if keyword in prompt_lower:
            for item_info in item_list:
                item_name = item_info["name"]
                if item_name not in seen_items:
                    seen_items.add(item_name)
                    matches.append({
                        "name": item_name,
                        "type": item_info["type"],
                        "path": item_info["path"],
                        "priority": item_info["priority"],
                        "matched_keyword": keyword
                    })

    # Ordena por prioridade
    matches.sort(key=lambda x: priority_order.get(x["priority"], 1))

    return matches


def get_skill_instructions(skill_path: str) -> str:
    """Retorna instruções principais da skill para injeção."""
    full_path = PROJECT_ROOT / skill_path / "SKILL.md"
    if not full_path.exists():
        return ""

    try:
        content = full_path.read_text(encoding='utf-8')
    except Exception:
        return ""

    # Retorna primeiras 100 linhas (instruções principais)
    lines = content.split('\n')[:100]
    return '\n'.join(lines)


def get_skill_summary(skill_path: str) -> str:
    """Retorna resumo curto da skill (primeiras 20 linhas)."""
    full_path = PROJECT_ROOT / skill_path / "SKILL.md"
    if not full_path.exists():
        return ""

    try:
        content = full_path.read_text(encoding='utf-8')
    except Exception:
        return ""

    lines = content.split('\n')[:20]
    return '\n'.join(lines)


def get_subagent_context(subagent_path: str) -> str:
    """Retorna contexto completo do sub-agent (AGENT.md + SOUL.md se existir)."""
    base_path = PROJECT_ROOT / subagent_path

    context_parts = []

    # AGENT.md (obrigatório)
    agent_md = base_path / "AGENT.md"
    if agent_md.exists():
        try:
            content = agent_md.read_text(encoding='utf-8')
            # Primeiras 150 linhas do AGENT.md
            lines = content.split('\n')[:150]
            context_parts.append("=== AGENT INSTRUCTIONS ===\n" + '\n'.join(lines))
        except Exception:
            pass

    # SOUL.md (opcional - personalidade)
    soul_md = base_path / "SOUL.md"
    if soul_md.exists():
        try:
            content = soul_md.read_text(encoding='utf-8')
            # Primeiras 50 linhas do SOUL.md (personalidade é mais compacta)
            lines = content.split('\n')[:50]
            context_parts.append("\n=== AGENT PERSONALITY ===\n" + '\n'.join(lines))
        except Exception:
            pass

    return '\n'.join(context_parts)


def get_item_context(item_path: str, item_type: str) -> str:
    """Retorna contexto apropriado baseado no tipo."""
    if item_type == "skill":
        return get_skill_summary(item_path)
    else:
        return get_subagent_context(item_path)


#================================
# M-09: SECURITY - WHITELIST & PATH VALIDATION
#================================

def is_path_safe(item_path: str) -> bool:
    """
    M-09: Validate that skill/sub-agent path doesn't escape expected directories.
    Prevents path traversal attacks via crafted SKILL.md paths.
    """
    normalized = os.path.normpath(item_path)
    return any(normalized.startswith(prefix) for prefix in ALLOWED_SKILL_PREFIXES)


def load_whitelist() -> Dict:
    """Load skill/sub-agent whitelist. Empty dict = no whitelist (trust all)."""
    if not WHITELIST_PATH.exists():
        return {}
    try:
        with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def is_skill_trusted(item_name: str, item_type: str, whitelist: Dict) -> bool:
    """
    M-09: Check if skill/sub-agent is in the trusted whitelist.
    If no whitelist file exists, all items in valid paths are trusted (graceful degradation).
    """
    if not whitelist:
        return True  # No whitelist file = trust all (backward compatible)

    blocked_list = whitelist.get('blocked', [])
    if item_name in blocked_list:
        return False

    if item_type == "skill":
        trusted_list = whitelist.get('trusted_skills', [])
    else:
        trusted_list = whitelist.get('trusted_subagents', [])

    if '*' in trusted_list:
        return True  # Wildcard = trust all of this type

    return item_name in trusted_list


def log_security_event(event_type: str, item_name: str, item_path: str):
    """M-09: Log security events for skill routing."""
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'skill-security.jsonl'

    entry = {
        'timestamp': datetime.now().isoformat(),
        'event': event_type,
        'item_name': item_name,
        'item_path': item_path
    }

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


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

        matches = match_prompt(prompt)

        if not matches:
            print(json.dumps({'continue': True}))
            return

        top = matches[0]
        item_type = top.get('type', 'skill')
        item_name = top.get('name', 'unknown')

        # M-09: Path safety check — block path traversal
        if not is_path_safe(top['path']):
            log_security_event('path_traversal_blocked', item_name, top['path'])
            print(json.dumps({'continue': True}))
            return

        # M-09: Whitelist check — block unwhitelisted items
        whitelist = load_whitelist()
        if not is_skill_trusted(item_name, item_type, whitelist):
            log_security_event('unwhitelisted_blocked', item_name, top['path'])
            type_label = "skill" if item_type == "skill" else "sub-agent"
            print(json.dumps({
                'continue': True,
                'feedback': f"[SECURITY] {type_label} '{item_name}' not in trusted whitelist. Skipping auto-injection."
            }))
            return

        context = get_item_context(top['path'], item_type)

        if context:
            type_label = "SKILL" if item_type == "skill" else "SUB-AGENT"
            feedback = f"[{type_label} AUTO-ACTIVATED: {item_name}]\n"
            feedback += f"Keyword: \"{top['matched_keyword']}\"\n"
            feedback += f"Priority: {top['priority']}\n\n"
            feedback += context

            print(json.dumps({'continue': True, 'feedback': feedback}))
        else:
            print(json.dumps({'continue': True}))

    except Exception:
        print(json.dumps({'continue': True}))


def cli_test():
    """CLI test mode - run directly for debugging."""
    index = build_index()
    print(f"Skills indexadas: {index['skills_count']}")
    print(f"Sub-agents indexados: {index['subagents_count']}")
    print(f"Total: {index['total_count']}")
    print(f"Keywords mapeadas: {len(index['keyword_map'])}")

    print("\nKeywords disponíveis:")
    for kw in sorted(index['keyword_map'].keys()):
        items = [f"{s['name']} ({s['type']})" for s in index['keyword_map'][kw]]
        print(f"  '{kw}' → {items}")

    test_prompts = [
        "preciso analisar este PDF",
        "criar uma planilha excel",
        "jarvis, status do sistema",
        "processar vídeo do youtube"
    ]

    for test_prompt in test_prompts:
        matches = match_prompt(test_prompt, index)
        print(f"\nMatches para '{test_prompt}':")
        if matches:
            for m in matches:
                print(f"  - {m['name']} ({m['type']}, keyword: {m['matched_keyword']}, priority: {m['priority']})")
        else:
            print("  (nenhum match)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        cli_test()
    else:
        main()
