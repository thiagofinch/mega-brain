#!/usr/bin/env python3
"""PreToolUse hook: Block destructive ClickUp API calls and dangerous commands."""
import json, sys, re

def main():
    data = json.loads(sys.stdin.read())
    cmd = data.get("tool_input", {}).get("command", "")

    # Block DELETE calls to ClickUp API
    if re.search(r'curl.*-X\s*DELETE.*api\.clickup\.com', cmd, re.IGNORECASE):
        print(json.dumps({
            "decision": "block",
            "reason": "ClickUp DELETE blocked by R3. Use delete script with --confirm, or ask o fundador (R2)."
        }))
        return

    # Block bulk operations without --dry-run
    if re.search(r'(bulk|batch|mass|all-tasks)', cmd) and '--dry-run' not in cmd:
        print(json.dumps({
            "decision": "block",
            "reason": "Bulk operations require --dry-run first."
        }))
        return

    # Block dangerous git operations
    blocked = [
        (r'git\s+push\s+--force', "git push --force blocked"),
        (r'git\s+reset\s+--hard', "git reset --hard blocked"),
        (r'rm\s+-rf\s+/', "rm -rf on root blocked"),
    ]
    for pattern, reason in blocked:
        if re.search(pattern, cmd, re.IGNORECASE):
            print(json.dumps({"decision": "block", "reason": reason}))
            return

    print(json.dumps({"decision": "approve"}))

if __name__ == "__main__":
    main()
