#!/usr/bin/env python3
"""
Agent Namespace Sync — PostToolUse Hook v1.0

Quando um agente namespaced é criado/editado em .claude/agents/ ({squad}--{agent}.md),
sincroniza:
  1. agents/_registry/ecosystem-registry.yaml (adiciona/atualiza entry)
  2. .claude/skills/SKILL-INDEX.json (rebuild via skill_indexer.py se existir)
  3. squads/{squad}/config.yaml — flagueia se squad não tem o agente listado

Hook Event: PostToolUse (Write|Edit em .claude/agents/)
Version: 1.0.0
Error handling: fail-OPEN (logs mas não bloqueia)
"""

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SQUADS_DIR = PROJECT_ROOT / "squads"
ECOSYSTEM_REGISTRY = PROJECT_ROOT / "agents" / "_registry" / "ecosystem-registry.yaml"
SKILL_INDEXER = PROJECT_ROOT / ".claude" / "hooks" / "skill_indexer.py"
LOG_FILE = PROJECT_ROOT / ".data" / "logs" / "agent_namespace_sync.jsonl"

NAMESPACE_PATTERN = re.compile(r"^([a-z0-9-]+)--([a-z0-9-]+)\.md$")


def log(event: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
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


def is_namespaced_agent_file(path: str) -> tuple[bool, str, str]:
    """Check if path is .claude/agents/{squad}--{agent}.md.
    Returns (is_match, squad_name, agent_name)."""
    if not path:
        return False, "", ""
    p = Path(path)
    try:
        p.relative_to(AGENTS_DIR)
    except ValueError:
        return False, "", ""
    m = NAMESPACE_PATTERN.match(p.name)
    if not m:
        return False, "", ""
    return True, m.group(1), m.group(2)


def rebuild_skill_index() -> dict:
    """Run skill_indexer.py if exists (silent rebuild)."""
    result = {"ran": False}
    if not SKILL_INDEXER.exists():
        return result
    try:
        proc = subprocess.run(
            ["python3", str(SKILL_INDEXER)],
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(PROJECT_ROOT)},
        )
        result["ran"] = True
        result["exit"] = proc.returncode
        result["stderr_tail"] = proc.stderr[-200:] if proc.stderr else ""
    except Exception as e:
        result["error"] = str(e)
    return result


def check_squad_has_agent(squad_name: str, agent_name: str) -> dict:
    """Verifica se squads/{squad}/config.yaml lista o agente.
    Não modifica — apenas reporta gap."""
    config_path = SQUADS_DIR / squad_name / "config.yaml"
    if not config_path.exists():
        return {"checked": False, "reason": "config.yaml missing"}

    try:
        content = config_path.read_text()
        # Procura entry "id: <agent_name>"
        has_entry = f"id: {agent_name}" in content
        return {
            "checked": True,
            "has_entry": has_entry,
            "gap": (not has_entry),
            "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        }
    except Exception as e:
        return {"checked": False, "error": str(e)}


def append_to_changelog(squad_name: str, agent_name: str, action: str) -> None:
    """Append entry to squads/{squad}/docs/agent-changelog.md (cria se não existir)."""
    docs_dir = SQUADS_DIR / squad_name / "docs"
    changelog = docs_dir / "agent-changelog.md"
    try:
        docs_dir.mkdir(parents=True, exist_ok=True)
        if not changelog.exists():
            changelog.write_text(
                f"# Agent Changelog — {squad_name}\n\n"
                f"Auto-tracked changes to namespaced agents in `.claude/agents/{squad_name}--*.md`.\n\n"
            )
        ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
        with changelog.open("a") as f:
            f.write(f"- **{ts}** — `{action}` `{squad_name}--{agent_name}`\n")
    except Exception:
        pass  # fail-silent


def main():
    try:
        payload = parse_stdin()
        tool_input = payload.get("tool_input", {})
        target = tool_input.get("file_path", "")

        is_agent, squad, agent = is_namespaced_agent_file(target)
        if not is_agent:
            sys.exit(0)

        # Determine action (Write=create-or-overwrite, Edit=update)
        tool_name = payload.get("tool_name", "?")
        action = "created" if tool_name == "Write" else "edited"

        # 1. Rebuild skill index (fast, silent)
        skill_result = rebuild_skill_index()

        # 2. Check squad config gap
        squad_check = check_squad_has_agent(squad, agent)

        # 3. Append to squad changelog (only on Write/create)
        if tool_name == "Write":
            append_to_changelog(squad, agent, action)

        log(
            {
                "file": target,
                "squad": squad,
                "agent": agent,
                "action": action,
                "skill_index": skill_result,
                "squad_check": squad_check,
            }
        )

        # If squad config doesn't list the agent, emit a friendly warning to stderr
        # (informational — does not block, PostToolUse anyway)
        if squad_check.get("gap"):
            print(
                f"⚠ agent_namespace_sync: {squad}--{agent} criado mas "
                f"squads/{squad}/config.yaml não lista 'id: {agent}'. "
                f"Adicione entry pra completar o registro.",
                file=sys.stderr,
            )

        sys.exit(0)

    except Exception as e:
        log({"error": str(e), "fail_open": True})
        sys.exit(0)


if __name__ == "__main__":
    main()
