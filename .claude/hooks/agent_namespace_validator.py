#!/usr/bin/env python3
"""
Agent Namespace Validator — PreToolUse Hook v1.0

Valida que agentes namespaced em .claude/agents/ sigam o formato canônico
{squad}--{agent}.md (padrão the-hub adotado pelo mega-brain).

REGRAS ENFORCED:
- Nome do arquivo DEVE ser {squad}--{agent}.md (regex: ^[a-z0-9-]+--[a-z0-9-]+\\.md$)
- {squad} DEVE existir como pasta em squads/ (validação cruzada)
- frontmatter DEVE ter `name: {squad}--{agent}` batendo com filename
- frontmatter DEVE ter `agent: {squad}--{agent}` batendo
- frontmatter DEVE ter `context` ∈ {fork, conversation}
- frontmatter DEVE ter `description` não-vazia

EXIT CODES:
- 0: Passou (validação OK) ou arquivo não é de agente namespaced (irrelevante)
- 2: Erro (bloqueia Write/Edit) — formato inválido

ERROR HANDLING: fail-OPEN
  - Internal exceptions → exit(0) ALLOW (não bloqueia em erros internos)

Executado via settings.json PreToolUse hook.
Trigger: matcher=Write|Edit em path .claude/agents/

Version: 1.0.0
"""

import json
import os
import re
import sys
from datetime import UTC
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SQUADS_DIR = PROJECT_ROOT / "squads"
LOG_FILE = PROJECT_ROOT / ".data" / "logs" / "agent_namespace_validations.jsonl"

NAMESPACE_PATTERN = re.compile(r"^([a-z0-9-]+)--([a-z0-9-]+)\.md$")
ALLOWED_CONTEXT = {"fork", "conversation"}


def log(event: dict) -> None:
    """Append to validation log (never blocks)."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone

        event["timestamp"] = datetime.now(UTC).isoformat()
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass


def parse_stdin() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def get_target_path(payload: dict) -> str:
    """Extract target file path from hook payload."""
    tool_input = payload.get("tool_input", {})
    return tool_input.get("file_path", "")


def get_target_content(payload: dict) -> str:
    """Extract proposed file content (Write tool only)."""
    tool_input = payload.get("tool_input", {})
    return tool_input.get("content", "") or tool_input.get("new_string", "")


def is_namespaced_agent_file(path: str) -> bool:
    """Check if path is .claude/agents/*.md namespaced."""
    if not path:
        return False
    p = Path(path)
    try:
        p.relative_to(AGENTS_DIR)
    except ValueError:
        return False
    return p.suffix == ".md" and not p.name.startswith(".")


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from content (between --- markers)."""
    if not content.startswith("---"):
        return {}
    lines = content.split("\n")
    fm_lines = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)
    fm = {}
    for line in fm_lines:
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def validate(path: str, content: str) -> tuple[bool, list[str]]:
    """Run all validations. Returns (passed, errors)."""
    errors = []
    filename = Path(path).name

    # 1. Filename pattern
    m = NAMESPACE_PATTERN.match(filename)
    if not m:
        errors.append(
            f"Filename '{filename}' não bate com padrão {{squad}}--{{agent}}.md "
            f"(ex: visual-knowledge-squad--funnel-cartographer.md). "
            f"Use kebab-case, double-dash separator."
        )
        return False, errors

    squad_name, agent_name = m.group(1), m.group(2)

    # 2. Squad must exist
    squad_path = SQUADS_DIR / squad_name
    if not squad_path.is_dir():
        errors.append(
            f"Squad '{squad_name}' não existe em squads/. "
            f"Crie squads/{squad_name}/ antes de adicionar agentes."
        )

    # 3. Frontmatter validation (content may be empty on Edit — skip)
    if content:
        fm = parse_frontmatter(content)
        expected_name = f"{squad_name}--{agent_name}"

        if not fm:
            errors.append(
                "Frontmatter YAML ausente. Agente namespaced precisa de --- ... --- no topo."
            )
        else:
            if fm.get("name") != expected_name:
                errors.append(
                    f"frontmatter.name='{fm.get('name')}' não bate com filename "
                    f"esperado '{expected_name}'."
                )
            if fm.get("agent") and fm.get("agent") != expected_name:
                errors.append(
                    f"frontmatter.agent='{fm.get('agent')}' não bate com filename "
                    f"esperado '{expected_name}'."
                )
            ctx = fm.get("context")
            if ctx and ctx not in ALLOWED_CONTEXT:
                errors.append(
                    f"frontmatter.context='{ctx}' inválido. Use um de: {sorted(ALLOWED_CONTEXT)}."
                )
            desc = fm.get("description", "").strip()
            if not desc:
                errors.append("frontmatter.description vazia. Adicione 1-2 frases sobre o agente.")

    return len(errors) == 0, errors


def main():
    try:
        payload = parse_stdin()
        target = get_target_path(payload)

        if not is_namespaced_agent_file(target):
            sys.exit(0)  # Not our concern

        content = get_target_content(payload)
        passed, errors = validate(target, content)

        log(
            {
                "file": target,
                "passed": passed,
                "errors": errors,
                "tool": payload.get("tool_name", "?"),
            }
        )

        if not passed:
            # Bloqueia execução com mensagem clara
            print("VETO: Agent Namespace Validator", file=sys.stderr)
            print(f"   Path: {target}", file=sys.stderr)
            print(
                "   Rule: agentes em .claude/agents/ devem seguir formato {squad}--{agent}.md",
                file=sys.stderr,
            )
            for err in errors:
                print(f"   - {err}", file=sys.stderr)
            print(
                "   Exemplo válido: .claude/agents/visual-knowledge-squad--funnel-cartographer.md",
                file=sys.stderr,
            )
            sys.exit(2)

        sys.exit(0)

    except Exception as e:
        # fail-OPEN
        log({"error": str(e), "fail_open": True})
        sys.exit(0)


if __name__ == "__main__":
    main()
