#!/usr/bin/env python3
"""PostToolUse hook: Log ClickUp API calls to clickup-api.log.jsonl"""
import json, sys, os, re
from datetime import datetime

LOG_FILE = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".data", "logs", "clickup-api.log.jsonl")

def main():
    data = json.loads(sys.stdin.read())
    cmd = data.get("tool_input", {}).get("command", "")

    if not re.search(r'api\.clickup\.com|clickup|supabase', cmd, re.IGNORECASE):
        return

    entry = {
        "ts": datetime.now().isoformat(),
        "tool": data.get("tool_name", "Bash"),
        "cmd": cmd[:300],
        "exit": data.get("tool_result", {}).get("exitCode", None),
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    main()
