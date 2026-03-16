#!/usr/bin/env python3
"""
memory_capture.py -- PostToolUse Hook
=====================================
Captures agent execution results and writes to agent memory.
Captures kops-*, dops-*, and devops-megabrain agent completions.

Output fields per AC (W3.2):
  agent_name, task_summary, files_modified, outcome, timestamp

Exit codes:
  0 = Always (never blocks, never warns)
Trigger: PostToolUse (all tools)
Timeout: 30000
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_DIR = ROOT / ".data" / "agent_memory"

TRACKED_PREFIXES = ("kops-", "dops-", "devops-megabrain")


def extract_files_from_result(result_text: str) -> list[str]:
    """Extract file paths mentioned in the agent result text.

    Looks for common path patterns in the result summary.
    """
    if not result_text:
        return []

    # Match paths that look like project files (contain / and a file extension,
    # or are known project directories)
    patterns = [
        # Absolute paths
        r"(/[a-zA-Z0-9_./-]+\.[a-z]{1,5})",
        # Relative project paths (core/, agents/, knowledge/, .claude/, etc.)
        r"(?:^|\s)((?:core|agents|knowledge|workspace|\.claude|\.data|artifacts|docs)"
        r"/[a-zA-Z0-9_./-]+)",
    ]

    files: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, result_text)
        for m in matches:
            cleaned = m.strip().rstrip(".,;:)")
            if cleaned and cleaned not in files and len(cleaned) > 5:
                files.append(cleaned)

    return files[:20]  # Cap at 20 to keep entry size reasonable


def determine_outcome(result_text: str) -> str:
    """Determine task outcome from result text.

    Returns: 'success', 'partial', 'error', or 'unknown'
    """
    if not result_text:
        return "unknown"

    lower = result_text.lower()

    # Error indicators
    error_signals = ["error", "failed", "exception", "traceback", "could not", "unable to"]
    if any(s in lower for s in error_signals):
        # Check if it was recovered
        recovery_signals = ["fixed", "resolved", "recovered", "retry succeeded"]
        if any(s in lower for s in recovery_signals):
            return "partial"
        return "error"

    # Success indicators
    success_signals = [
        "complete", "success", "done", "created", "updated",
        "written", "saved", "built", "passed", "verified",
    ]
    if any(s in lower for s in success_signals):
        return "success"

    # If there is substantial output, likely succeeded
    if len(result_text) > 100:
        return "success"

    return "unknown"


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        hook_input = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")

    # Capture Agent tool completions (squad dispatch)
    if tool_name == "Agent":
        tool_input = hook_input.get("tool_input", {})
        tool_result = hook_input.get("tool_result", "")

        agent_name = tool_input.get("subagent_type", "")
        if not agent_name or not any(agent_name.startswith(p) for p in TRACKED_PREFIXES):
            sys.exit(0)

        prompt = tool_input.get("prompt", "")
        result_str = str(tool_result)[:2000] if tool_result else ""
        files = extract_files_from_result(result_str)
        outcome = determine_outcome(result_str)

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_name": agent_name,
            "task_summary": prompt[:200],
            "files_modified": files,
            "outcome": outcome,
            "result_summary": result_str[:300],
            "type": "execution",
            "importance": 0.5,
        }

        _write_entry(agent_name, entry)
        sys.exit(0)

    # Capture Write/Edit tool completions for file tracking
    # (enriches recent agent entries with files_modified data)
    if tool_name in ("Write", "Edit"):
        tool_input = hook_input.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if not file_path:
            sys.exit(0)

        # Check if there is a recent agent execution entry to enrich
        # by looking at the most recent entry across all tracked agent dirs
        _enrich_latest_entry_with_file(file_path)

    sys.exit(0)


def _write_entry(agent_name: str, entry: dict) -> None:
    """Write a memory entry to the agent's JSONL file."""
    agent_dir = MEMORY_DIR / agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    memory_file = agent_dir / "memories.jsonl"

    try:
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Fail silently -- never block


def _enrich_latest_entry_with_file(file_path: str) -> None:
    """Add a file_path to the most recent execution entry if it was written
    within the last 60 seconds. This captures files modified during agent
    dispatch that happen via Write/Edit tools.
    """
    now = datetime.now(UTC)

    # Scan tracked agent dirs for the most recent entry
    if not MEMORY_DIR.exists():
        return

    for agent_dir in MEMORY_DIR.iterdir():
        if not agent_dir.is_dir():
            continue
        if not any(agent_dir.name.startswith(p) for p in TRACKED_PREFIXES):
            continue

        memory_file = agent_dir / "memories.jsonl"
        if not memory_file.exists():
            continue

        try:
            lines = memory_file.read_text(encoding="utf-8").strip().split("\n")
            if not lines:
                continue

            # Check last entry
            last_entry = json.loads(lines[-1])
            if last_entry.get("type") != "execution":
                continue

            # Check if entry is recent (within 60 seconds)
            entry_time = last_entry.get("timestamp", "")
            try:
                entry_dt = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
                delta = (now - entry_dt).total_seconds()
                if delta > 60:
                    continue
            except (ValueError, TypeError):
                continue

            # Enrich with file path
            existing_files = last_entry.get("files_modified", [])
            short_path = file_path.replace(str(ROOT) + "/", "")
            if short_path not in existing_files:
                existing_files.append(short_path)
                last_entry["files_modified"] = existing_files

                # Rewrite the last line
                lines[-1] = json.dumps(last_entry, ensure_ascii=False)
                memory_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        except (json.JSONDecodeError, OSError):
            continue


if __name__ == "__main__":
    main()
