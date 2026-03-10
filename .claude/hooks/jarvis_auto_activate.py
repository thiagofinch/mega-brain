#!/usr/bin/env python3
"""
JARVIS Auto-Activation Hook
Activates JARVIS system whenever a new session starts
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def activate_jarvis():
    """Activate JARVIS on session start"""

    try:
        # Paths
        jarvis_dir = Path(".claude/jarvis")
        state_file = jarvis_dir / "MISSION-STATE.json"
        memory_file = jarvis_dir / "JARVIS-MEMORY.md"

        # Check if files exist
        if not state_file.exists():
            print("⚠️  JARVIS state file not found")
            return False

        if not memory_file.exists():
            print("⚠️  JARVIS memory file not found")
            return False

        # Load current state
        with open(state_file) as f:
            state = json.load(f)

        # Update to ACTIVE
        old_status = state.get("status", "UNKNOWN")
        state["status"] = "ACTIVE"
        state["phase"] = "SESSION_ACTIVE"
        state["timestamp"] = datetime.utcnow().isoformat() + "Z"
        state["auto_activated"] = True

        # Save updated state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Print activation message
        print("\n" + "=" * 80)
        print("🤖 JARVIS ACTIVATED (Auto-Start)")
        print("=" * 80)
        print(f"✅ Status: {state['status']}")
        print(f"✅ Version: {state['version']}")
        print(f"✅ Session: {state.get('session_id', 'SESSION-ACTIVE')}")
        print(f"✅ Memory: {memory_file.name} ({len(memory_file.read_text().splitlines())} lines)")
        print("=" * 80 + "\n")

        return True

    except Exception as e:
        print(f"❌ JARVIS activation failed: {e}")
        return False

if __name__ == "__main__":
    success = activate_jarvis()
    sys.exit(0 if success else 1)
