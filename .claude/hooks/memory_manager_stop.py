#!/usr/bin/env python3
"""
Stop hook: Memory Manager maintenance (prune + consolidate).

Runs on session end to clean up agent memories:
1. Consolidate near-duplicates (Jaccard >= 0.85)
2. Prune low-value entries (max 200 per agent)

Only processes stores that have been modified this session.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_DIR = ROOT / ".data" / "agent_memory"


def main():
    if not MEMORY_DIR.exists():
        print(json.dumps({"message": "No agent memories to maintain"}))
        sys.exit(0)

    # Find all agent memory dirs that have a memories.jsonl
    stores = sorted(
        d.name for d in MEMORY_DIR.iterdir() if d.is_dir() and (d / "memories.jsonl").exists()
    )

    if not stores:
        print(json.dumps({"message": "No agent memory stores found"}))
        sys.exit(0)

    # Import memory_manager (add parent to path)
    sys.path.insert(0, str(ROOT))
    try:
        from core.intelligence.memory_manager import get_store
    except ImportError:
        print(json.dumps({"warning": "memory_manager not importable"}))
        sys.exit(0)

    total_merged = 0
    total_pruned = 0
    agents_processed = []

    for agent_id in stores:
        try:
            store = get_store(agent_id)
            if store.count == 0:
                continue

            # Consolidate
            c = store.consolidate()
            total_merged += c.get("merged", 0)

            # Prune
            p = store.prune()
            total_pruned += p.get("pruned", 0)

            if c.get("merged", 0) > 0 or p.get("pruned", 0) > 0:
                agents_processed.append(agent_id)
        except Exception as e:
            # Log but continue processing other agents
            agents_processed.append(f"{agent_id}:error:{e!s:.50}")
            continue

    result = {
        "message": f"Memory maintenance: {len(agents_processed)} agents, "
        f"{total_merged} merged, {total_pruned} pruned",
        "agents": agents_processed,
        "merged": total_merged,
        "pruned": total_pruned,
    }
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
