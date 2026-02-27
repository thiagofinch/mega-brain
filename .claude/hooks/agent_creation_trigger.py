#!/usr/bin/env python3
"""
Agent Creation Trigger Hook
Listens for role_detector signals and triggers agent creation workflow.

Hook Events: PostToolUse (Write to role-tracking.md)
Version: 1.0.0
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Thresholds
CARGO_THRESHOLD = 5
EXECUTIVE_THRESHOLD = 10

BASE_DIR = Path(__file__).parent.parent.parent
ROLE_TRACKING = BASE_DIR / "agents" / "discovery" / "role-tracking.md"
PERSONA_REGISTRY = BASE_DIR / "agents" / "persona-registry.yaml"
CREATION_LOG = BASE_DIR / "logs" / "agent-creation.jsonl"


def parse_stdin():
    """Parse JSON from stdin (Claude Code hook format)."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def check_thresholds(role_tracking_content: str) -> list:
    """
    Parse role-tracking.md and find roles that hit thresholds.
    Returns list of dicts with role data.
    """
    agents_to_create = []

    # Simple parsing - look for threshold indicators
    lines = role_tracking_content.split('\n')
    for line in lines:
        if '🔴 THRESHOLD' in line or '🔴 CRIAR AGENTE' in line:
            # Extract role info
            parts = line.split('|')
            if len(parts) >= 3:
                role_name = parts[1].strip()
                mentions = parts[2].strip()
                try:
                    mention_count = int(mentions.split()[0])
                    if mention_count >= EXECUTIVE_THRESHOLD:
                        agents_to_create.append({
                            'layer': 'L2',
                            'id': role_name.lower().replace(' ', '-'),
                            'name': role_name,
                            'mentions': mention_count,
                            'type': 'executive'
                        })
                    elif mention_count >= CARGO_THRESHOLD:
                        agents_to_create.append({
                            'layer': 'L4',
                            'id': role_name.lower().replace(' ', '-'),
                            'name': role_name,
                            'mentions': mention_count,
                            'type': 'cargo'
                        })
                except ValueError:
                    continue

    return agents_to_create


def agent_exists(agent_id: str) -> bool:
    """Check if agent already exists in persona-registry."""
    if not PERSONA_REGISTRY.exists():
        return False

    content = PERSONA_REGISTRY.read_text()
    return f"id: {agent_id}" in content


def log_creation_trigger(agent_data: dict, status: str):
    """Log agent creation trigger to JSONL."""
    CREATION_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_data.get('id'),
        "layer": agent_data.get('layer'),
        "name": agent_data.get('name'),
        "mentions": agent_data.get('mentions'),
        "status": status,
        "trigger": "role_threshold"
    }

    with open(CREATION_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def generate_creation_instruction(agents: list) -> str:
    """Generate instruction for JARVIS to create agents."""
    if not agents:
        return ""

    instructions = []
    for agent in agents:
        if not agent_exists(agent['id']):
            instructions.append(
                f"🏭 **AGENT CREATION TRIGGERED**\n"
                f"   Layer: {agent['layer']}\n"
                f"   ID: {agent['id']}\n"
                f"   Name: {agent['name']}\n"
                f"   Mentions: {agent['mentions']}\n"
                f"   \n"
                f"   Execute: `/create-agent --layer {agent['layer']} --id {agent['id']} --name \"{agent['name']}\"`"
            )
            log_creation_trigger(agent, "TRIGGERED")
        else:
            log_creation_trigger(agent, "ALREADY_EXISTS")

    return '\n\n'.join(instructions)


def main():
    """Main hook execution."""
    try:
        data = parse_stdin()

        # Only trigger on writes to role-tracking.md
        tool_name = data.get('tool_name', '')
        tool_input = data.get('tool_input', {})

        if tool_name not in ['Write', 'Edit']:
            print(json.dumps({"continue": True}))
            return

        file_path = tool_input.get('file_path', '')
        if 'role-tracking' not in file_path.lower():
            print(json.dumps({"continue": True}))
            return

        # Read role-tracking content
        if ROLE_TRACKING.exists():
            content = ROLE_TRACKING.read_text()
            agents = check_thresholds(content)

            if agents:
                instruction = generate_creation_instruction(agents)
                if instruction:
                    print(json.dumps({
                        "continue": True,
                        "message": instruction
                    }))
                    return

        print(json.dumps({"continue": True}))

    except Exception as e:
        # Don't block on errors
        print(json.dumps({
            "continue": True,
            "warning": f"Agent creation trigger error: {str(e)}"
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
