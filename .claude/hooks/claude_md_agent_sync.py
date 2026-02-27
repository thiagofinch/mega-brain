#!/usr/bin/env python3
"""
CLAUDE.md Agent Sync Hook
Updates the Agents section in CLAUDE.md when agent structure changes.

Hook Events: PostToolUse (Write/Edit to agents/ or persona-registry.yaml)
Version: 1.0.0
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent
CLAUDE_MD = BASE_DIR / ".claude" / "CLAUDE.md"
PERSONA_REGISTRY = BASE_DIR / "agents" / "persona-registry.yaml"
AGENTS_DIR = BASE_DIR / "agents"
SYNC_LOG = BASE_DIR / "logs" / "claude-md-sync.jsonl"


def parse_stdin():
    """Parse JSON from stdin."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def should_trigger(file_path: str) -> bool:
    """Check if this file change should trigger sync."""
    triggers = [
        'persona-registry.yaml',
        'AGENT-INDEX.yaml',
        'agents.yaml'
    ]
    return any(t in file_path for t in triggers)


def count_agents() -> dict:
    """Count agents by type."""
    counts = {
        'minds': 0,
        'cargo': 0,
        'conclave': 0,
        'total': 0
    }

    # Count minds
    minds_dir = AGENTS_DIR / "minds"
    if minds_dir.exists():
        counts['minds'] = len([d for d in minds_dir.iterdir()
                               if d.is_dir() and not d.name.startswith('_')])

    # Count conclave
    conclave_dir = AGENTS_DIR / "conclave"
    if conclave_dir.exists():
        counts['conclave'] = len([d for d in conclave_dir.iterdir() if d.is_dir()])

    # Count cargo (recursive)
    cargo_dir = AGENTS_DIR / "cargo"
    if cargo_dir.exists():
        for group in cargo_dir.iterdir():
            if group.is_dir():
                counts['cargo'] += len([d for d in group.iterdir() if d.is_dir()])

    counts['total'] = counts['minds'] + counts['cargo'] + counts['conclave']
    return counts


def update_claude_md():
    """Update the Agents section in CLAUDE.md."""
    if not CLAUDE_MD.exists():
        return False

    content = CLAUDE_MD.read_text()
    counts = count_agents()

    # Build new agents section
    new_section = f"""## Agents

Defined in `AGENT-INDEX.yaml`, activated via slash commands.

| Type | Count | Purpose |
|------|-------|---------|
| CARGO | {counts['cargo']} | Functional roles (Sales, Marketing, Ops) |
| MINDS | {counts['minds']} | Expert mind clones |
| CONCLAVE | {counts['conclave']} | Multi-perspective deliberation |
| SYSTEM | 2 | JARVIS, Agent-Creator |

**Total Active Agents:** {counts['total']}"""

    # Find and replace the Agents section
    # Pattern matches from "## Agents" to the next "##" or end
    pattern = r'## Agents\n.*?(?=\n## |\Z)'

    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        CLAUDE_MD.write_text(new_content)
        return True

    return False


def log_sync(file_path: str, success: bool):
    """Log sync operation."""
    SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "trigger_file": file_path,
        "success": success,
        "counts": count_agents()
    }

    with open(SYNC_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def main():
    """Main hook execution."""
    try:
        data = parse_stdin()

        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})

        if tool_name not in ['Write', 'Edit']:
            print(json.dumps({"continue": True}))
            return

        file_path = tool_input.get('file_path', '')

        # Check if this should trigger sync
        if not should_trigger(file_path):
            print(json.dumps({"continue": True}))
            return

        # Update CLAUDE.md
        success = update_claude_md()
        log_sync(file_path, success)

        if success:
            counts = count_agents()
            print(json.dumps({
                "continue": True,
                "message": f"📝 CLAUDE.md agents section synced ({counts['total']} agents)"
            }))
        else:
            print(json.dumps({"continue": True}))

    except Exception as e:
        print(json.dumps({
            "continue": True,
            "warning": f"CLAUDE.md sync error: {str(e)}"
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
