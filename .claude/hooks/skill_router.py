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

import json
import os
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
SKILLS_PATH = PROJECT_ROOT / ".claude" / "skills"
SUBAGENTS_PATH = PROJECT_ROOT / ".claude" / "jarvis" / "sub-agents"
SQUADS_PATH = PROJECT_ROOT / ".squads"
AGENT_MEMORY_PATH = PROJECT_ROOT / ".claude" / "agent-memory"
INDEX_PATH = PROJECT_ROOT / ".claude" / "mission-control" / "SKILL-INDEX.json"

# Cargo agents with persistent memory in .claude/agent-memory/
# Maps keywords → agent-memory directory name
CARGO_AGENT_KEYWORDS = {
    "closer": "closer",
    "business consultant": "closer",
    "/ask closer": "closer",
    "cfo": "cfo",
    "chief financial": "cfo",
    "/ask cfo": "cfo",
    "cro": "cro",
    "chief revenue": "cro",
    "/ask cro": "cro",
}


def scan_skills() -> list[tuple[Path, str]]:
    """Lista todas as pastas de skills válidas com tipo."""
    items = []

    # Scan skills
    if SKILLS_PATH.exists():
        for item in SKILLS_PATH.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    items.append((item, "skill"))

    # Scan sub-agents
    if SUBAGENTS_PATH.exists():
        for item in SUBAGENTS_PATH.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                agent_md = item / "AGENT.md"
                if agent_md.exists():
                    items.append((item, "sub-agent"))

    # Scan squads (.squads/*/config.yaml or config/squad.yaml)
    if SQUADS_PATH.exists():
        for item in SQUADS_PATH.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                config_yaml = item / "config.yaml"
                alt_config = item / "config" / "squad.yaml"
                if config_yaml.exists() or alt_config.exists():
                    items.append((item, "squad"))

    return items


def _derive_squad_keywords(name: str, description: str, entry_agent: str) -> list[str]:
    """Derive keywords from squad config fields."""
    keywords = set()
    # Squad name and variants
    keywords.add(name.lower())
    keywords.add(name.lower().replace("-", " "))
    if entry_agent:
        keywords.add(entry_agent.lower())
        keywords.add(entry_agent.lower().replace("-", " "))
    # Extract significant words from description (>3 chars, not stopwords)
    stopwords = {
        "squad", "agents", "agent", "para", "com", "que", "uma", "use",
        "quando", "ativar", "executar", "missoes", "dominio", "based",
        "the", "and", "for", "with", "from", "this", "that", "elite",
    }
    if description:
        words = re.findall(r"[a-zA-Z\u00C0-\u017F]{4,}", description.lower())
        for w in words:
            if w not in stopwords and len(w) <= 20:
                keywords.add(w)
    return [k for k in sorted(keywords) if len(k) > 2][:15]


def extract_squad_metadata(squad_path: Path) -> dict:
    """Extract metadata from a squad's config.yaml."""
    config_file = squad_path / "config.yaml"
    if not config_file.exists():
        config_file = squad_path / "config" / "squad.yaml"
    if not config_file.exists():
        return {}

    # Parse YAML
    config = {}
    if yaml:
        try:
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            config = {}
    else:
        # Fallback: regex extraction when PyYAML unavailable
        try:
            text = config_file.read_text(encoding="utf-8")
            for field in ("name", "entry_agent", "description", "slashPrefix"):
                m = re.search(rf'^{field}:\s*["\']?([^"\'\n]+)', text, re.M)
                if m:
                    config[field] = m.group(1).strip()
        except Exception:
            return {}

    # Handle nested config (some squads use squad.name, pack.name, etc.)
    if "squad" in config and isinstance(config["squad"], dict):
        inner = config["squad"]
        config = {**inner, **{k: v for k, v in config.items() if k != "squad"}}
    if "pack" in config and isinstance(config["pack"], dict):
        inner = config["pack"]
        for k in ("name", "description", "slash_prefix"):
            if k in inner and k not in config:
                config[k] = inner[k]

    name = config.get("name", squad_path.name)
    description = config.get("description", "")
    entry_agent = config.get("entry_agent", "")
    slash_prefix = config.get("slashPrefix", config.get("slash_prefix", ""))

    # Count agents
    agents_dir = squad_path / "agents"
    agent_count = 0
    if agents_dir.exists():
        agent_count = len([f for f in agents_dir.iterdir() if f.suffix == ".md"])

    keywords = _derive_squad_keywords(name, description, entry_agent)

    return {
        "path": str(squad_path.relative_to(PROJECT_ROOT)),
        "name": squad_path.name,
        "type": "squad",
        "entry_agent": entry_agent,
        "slash_prefix": slash_prefix,
        "agent_count": agent_count,
        "description": description[:200] if description else "",
        "keywords": keywords,
        "priority": "MÉDIA",
    }


def extract_metadata(item_path: Path, item_type: str) -> dict:
    """Extrai metadados de SKILL.md, AGENT.md, ou config.yaml."""

    if item_type == "squad":
        return extract_squad_metadata(item_path)

    if item_type == "skill":
        md_file = item_path / "SKILL.md"
    else:
        md_file = item_path / "AGENT.md"

    if not md_file.exists():
        return {}

    try:
        content = md_file.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"continue": True, "warning": f"skill_router: failed to read {md_file}: {e}"}))
        return {}

    # Extrai header (primeiras 40 linhas para garantir captura)
    lines = content.split("\n")[:40]
    header = "\n".join(lines)

    metadata = {
        "path": str(item_path.relative_to(PROJECT_ROOT)),
        "name": item_path.name,
        "type": item_type,
        "auto_trigger": "",
        "keywords": [],
        "priority": "MÉDIA",
        "description": "",
    }

    # Auto-Trigger (múltiplos formatos)
    for pattern in [r"\*\*Auto-Trigger:\*\*\s*(.+)", r"> \*\*Auto-Trigger:\*\*\s*(.+)"]:
        match = re.search(pattern, header)
        if match:
            metadata["auto_trigger"] = match.group(1).strip()
            break

    # Keywords - múltiplos formatos suportados
    for pattern in [r"\*\*Keywords:\*\*\s*(.+)", r"> \*\*Keywords:\*\*\s*(.+)"]:
        match = re.search(pattern, header)
        if match:
            raw = match.group(1).strip()
            # Parse keywords (pode ser "a", "b", "c" ou a, b, c ou [a, b, c])
            keywords = re.findall(r'["\']?([^",\'\[\]]+)["\']?', raw)
            metadata["keywords"] = [
                k.strip().lower() for k in keywords if k.strip() and len(k.strip()) > 1
            ]
            break

    # Prioridade
    for pattern in [
        r"\*\*Prioridade:\*\*\s*(ALTA|MÉDIA|BAIXA)",
        r"> \*\*Prioridade:\*\*\s*(ALTA|MÉDIA|BAIXA)",
    ]:
        match = re.search(pattern, header, re.I)
        if match:
            metadata["priority"] = match.group(1).upper()
            break

    # Description (primeira linha após # Header)
    match = re.search(r"^#\s+[^\n]+\n+##?\s*([^\n]+)", content)
    if match:
        metadata["description"] = match.group(1).strip()

    # Para sub-agents, verificar se tem SOUL.md
    if item_type == "sub-agent":
        soul_path = item_path / "SOUL.md"
        metadata["has_soul"] = soul_path.exists()

    return metadata


def _ensure_squad_skill(squad_name: str, metadata: dict) -> None:
    """Auto-generate SKILL.md for a squad that doesn't have one yet."""
    skill_dir = SKILLS_PATH / squad_name
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        return

    desc = metadata.get("description", "")[:150]
    entry = metadata.get("entry_agent", squad_name + "-chief")
    count = metadata.get("agent_count", 0)
    squad_path = metadata.get("path", f".squads/{squad_name}")

    content = f"""---
name: {squad_name}
description: |
  {squad_name.replace('-', ' ').title()} Squad - {count} agents. {desc}

  Use quando: ativar o squad {squad_name} para executar missoes do dominio.
---

# {squad_name.replace('-', ' ').title()} Squad

Squad com **{count} agentes** especializados.

## Activation

O orchestrador principal e `{entry}`. Para ativar:

1. Leia `{squad_path}/agents/{entry}.md` e adote a persona
2. Carregue config: `{squad_path}/config.yaml`
3. Siga o mission router do chief para delegar trabalho

## Squad Directory

`{squad_path}/`
"""
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_md.write_text(content, encoding="utf-8")
    except Exception:
        pass  # Non-blocking: skill creation is best-effort


def build_index() -> dict:
    """Constrói índice completo de skills, sub-agents e squads."""
    items = scan_skills()

    index = {
        "version": "3.0.0",
        "skills_count": 0,
        "subagents_count": 0,
        "squads_count": 0,
        "total_count": len(items),
        "skills": {},
        "subagents": {},
        "squads": {},
        "keyword_map": {},
    }

    for item_path, item_type in items:
        metadata = extract_metadata(item_path, item_type)
        if metadata and metadata.get("keywords"):
            item_name = metadata["name"]

            if item_type == "skill":
                index["skills"][item_name] = metadata
                index["skills_count"] += 1
            elif item_type == "squad":
                index["squads"][item_name] = metadata
                index["squads_count"] += 1
                # Auto-generate SKILL.md if missing
                _ensure_squad_skill(item_name, metadata)
            else:
                index["subagents"][item_name] = metadata
                index["subagents_count"] += 1

            # Popula keyword_map (unificado)
            for keyword in metadata.get("keywords", []):
                if keyword not in index["keyword_map"]:
                    index["keyword_map"][keyword] = []
                index["keyword_map"][keyword].append(
                    {
                        "name": item_name,
                        "type": item_type,
                        "path": metadata["path"],
                        "priority": metadata["priority"],
                    }
                )

    # Salva índice
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return index


def match_prompt(prompt: str, index: dict = None) -> list[dict]:
    """Retorna skills e sub-agents que matcham com o prompt."""
    if index is None:
        if INDEX_PATH.exists():
            try:
                with open(INDEX_PATH, encoding="utf-8") as f:
                    index = json.load(f)
            except Exception as e:
                print(json.dumps({"continue": True, "warning": f"skill_router: failed to load index, rebuilding: {e}"}))
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
                    matches.append(
                        {
                            "name": item_name,
                            "type": item_info["type"],
                            "path": item_info["path"],
                            "priority": item_info["priority"],
                            "matched_keyword": keyword,
                        }
                    )

    # Ordena por prioridade
    matches.sort(key=lambda x: priority_order.get(x["priority"], 1))

    return matches


def get_skill_instructions(skill_path: str) -> str:
    """Retorna instruções principais da skill para injeção."""
    full_path = PROJECT_ROOT / skill_path / "SKILL.md"
    if not full_path.exists():
        return ""

    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"continue": True, "warning": f"skill_router: failed to read skill {full_path}: {e}"}))
        return ""

    # Retorna primeiras 100 linhas (instruções principais)
    lines = content.split("\n")[:100]
    return "\n".join(lines)


def get_skill_summary(skill_path: str) -> str:
    """Retorna resumo curto da skill (primeiras 20 linhas)."""
    full_path = PROJECT_ROOT / skill_path / "SKILL.md"
    if not full_path.exists():
        return ""

    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"continue": True, "warning": f"skill_router: failed to read skill summary {full_path}: {e}"}))
        return ""

    lines = content.split("\n")[:20]
    return "\n".join(lines)


def get_subagent_context(subagent_path: str) -> str:
    """Retorna contexto completo do sub-agent (AGENT.md + SOUL.md se existir)."""
    base_path = PROJECT_ROOT / subagent_path

    context_parts = []

    # AGENT.md (obrigatório)
    agent_md = base_path / "AGENT.md"
    if agent_md.exists():
        try:
            content = agent_md.read_text(encoding="utf-8")
            # Primeiras 150 linhas do AGENT.md
            lines = content.split("\n")[:150]
            context_parts.append("=== AGENT INSTRUCTIONS ===\n" + "\n".join(lines))
        except Exception as e:
            print(json.dumps({"continue": True, "warning": f"skill_router: failed to read AGENT.md {agent_md}: {e}"}))

    # SOUL.md (opcional - personalidade)
    soul_md = base_path / "SOUL.md"
    if soul_md.exists():
        try:
            content = soul_md.read_text(encoding="utf-8")
            # Primeiras 50 linhas do SOUL.md (personalidade é mais compacta)
            lines = content.split("\n")[:50]
            context_parts.append("\n=== AGENT PERSONALITY ===\n" + "\n".join(lines))
        except Exception as e:
            print(json.dumps({"continue": True, "warning": f"skill_router: failed to read SOUL.md {soul_md}: {e}"}))

    return "\n".join(context_parts)


def get_item_context(item_path: str, item_type: str) -> str:
    """Retorna contexto apropriado baseado no tipo."""
    if item_type == "skill":
        return get_skill_summary(item_path)
    else:
        return get_subagent_context(item_path)


def detect_cargo_agent(prompt: str) -> str | None:
    """Detecta se o prompt ativa um cargo agent. Retorna nome do agent-memory dir ou None."""
    prompt_lower = prompt.lower()
    for keyword, agent_name in CARGO_AGENT_KEYWORDS.items():
        if keyword in prompt_lower:
            return agent_name
    return None


def get_agent_memory(agent_name: str) -> str:
    """Carrega MEMORY.md compacto de .claude/agent-memory/{agent}/."""
    memory_file = AGENT_MEMORY_PATH / agent_name / "MEMORY.md"
    if not memory_file.exists():
        return ""
    try:
        return memory_file.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"continue": True, "warning": f"skill_router: failed to read agent memory {memory_file}: {e}"}))
        return ""


def main():
    """
    Hook entry point for Claude Code UserPromptSubmit event.
    Reads JSON from stdin, outputs JSON to stdout.
    """
    import sys

    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        prompt = hook_input.get("prompt", "")
        if not prompt:
            print(json.dumps({"continue": True}))
            return

        feedback_parts = []

        # Check for cargo agent activation → inject agent-memory
        cargo_agent = detect_cargo_agent(prompt)
        if cargo_agent:
            memory = get_agent_memory(cargo_agent)
            if memory:
                feedback_parts.append(f"[AGENT-MEMORY LOADED: {cargo_agent.upper()}]\n\n{memory}")

        # Check for skill/sub-agent matches
        matches = match_prompt(prompt)

        if matches:
            top = matches[0]
            item_type = top.get("type", "skill")
            item_name = top.get("name", "unknown")

            context = get_item_context(top["path"], item_type)

            if context:
                type_label = "SKILL" if item_type == "skill" else "SUB-AGENT"
                part = f"[{type_label} AUTO-ACTIVATED: {item_name}]\n"
                part += f'Keyword: "{top["matched_keyword"]}"\n'
                part += f"Priority: {top['priority']}\n\n"
                part += context
                feedback_parts.append(part)

        if feedback_parts:
            print(json.dumps({"continue": True, "feedback": "\n\n---\n\n".join(feedback_parts)}))
        else:
            print(json.dumps({"continue": True}))

    except Exception as e:
        print(json.dumps({"continue": True, "error": str(e)}))


def cli_test():
    """CLI test mode - run directly for debugging."""
    index = build_index()
    print(f"Skills indexadas: {index['skills_count']}")
    print(f"Squads indexados: {index['squads_count']}")
    print(f"Sub-agents indexados: {index['subagents_count']}")
    print(f"Total escaneados: {index['total_count']}")
    print(f"Keywords mapeadas: {len(index['keyword_map'])}")

    print("\nKeywords disponíveis:")
    for kw in sorted(index["keyword_map"].keys()):
        items = [f"{s['name']} ({s['type']})" for s in index["keyword_map"][kw]]
        print(f"  '{kw}' → {items}")

    test_prompts = [
        "preciso analisar este PDF",
        "criar uma planilha excel",
        "jarvis, status do sistema",
        "processar vídeo do youtube",
    ]

    for test_prompt in test_prompts:
        matches = match_prompt(test_prompt, index)
        print(f"\nMatches para '{test_prompt}':")
        if matches:
            for m in matches:
                print(
                    f"  - {m['name']} ({m['type']}, keyword: {m['matched_keyword']}, priority: {m['priority']})"
                )
        else:
            print("  (nenhum match)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        cli_test()
    else:
        main()
