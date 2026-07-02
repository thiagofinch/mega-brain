#!/usr/bin/env python3
# CONNECTED — W1-001.6: delegates to engine/memory_manager.py
"""
memory_manager_stop.py — Stop hook
Delegates cleanup to engine/memory_manager.cleanup_all() on session end.
Fail-open: always exits 0.
"""

import json
import os
import sys
from datetime import datetime

STATE_PATH = os.path.join(os.path.dirname(__file__), ".memory-state.json")

_project_root = os.environ.get(
    "CLAUDE_PROJECT_DIR", os.path.join(os.path.dirname(__file__), "..", "..")
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from engine.memory_manager import cleanup_all as _mm_cleanup_all

    _HAS_MEMORY_MANAGER = True
except ImportError:
    _HAS_MEMORY_MANAGER = False


def reset_state():
    try:
        state = {
            "prompt_count": 0,
            "active_agent": None,
            "session_start": None,
            "last_cleanup": datetime.now().isoformat(),
        }
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass


def main():
    try:
        if _HAS_MEMORY_MANAGER:
            stats = _mm_cleanup_all() or []
            cleaned = [s for s in stats if s.get("removed", 0) > 0]
            if cleaned:
                summary = [
                    f"  {s.get('agent_id', '?')}: {s.get('before', 0)}->{s.get('after', 0)}"
                    for s in cleaned
                ]
                print("[memory-cleanup] " + "; ".join(summary), file=sys.stderr)
        reset_state()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
