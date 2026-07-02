#!/usr/bin/env python3
"""
precompact_digest.py -- Mega Brain PreCompact Hook

Triggered before Claude Code compacts the session (auto or manual).
Captures a structured digest of the session that can be reinjected on
SessionStart of the next session, preserving critical decisions and
context across compactions.

Output: .synapse/sessions/digest-{timestamp}-{session_id_short}.json
Format:
{
    "timestamp": "2026-05-14T20:15:00Z",
    "session_id": "abc123",
    "matcher": "manual" | "auto",
    "transcript_path": "...",
    "summary": "first 500 chars of last 5 messages",
    "decisions": [],
    "files_modified": [],
    "open_tasks": []
}

The companion `session_start.py` hook reads the most recent digest on
SessionStart and emits it as additionalContext.

Fail-open: any error exits 0 silently.
"""

import json
import os
import re
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path


def main():
    try:
        input_data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    transcript_path = input_data.get("transcript_path", "")
    matcher = input_data.get("matcher", "auto")
    cwd = input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    project_root = Path(cwd)
    sessions_dir = project_root / ".synapse" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    short_id = session_id[:8] if session_id != "unknown" else "noid"
    digest_path = sessions_dir / f"digest-{timestamp}-{short_id}.json"

    digest = {
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "matcher": matcher,
        "transcript_path": transcript_path,
        "summary": "",
        "decisions": [],
        "files_modified": [],
        "open_tasks": [],
    }

    if transcript_path and Path(transcript_path).is_file():
        try:
            lines = Path(transcript_path).read_text(encoding="utf-8", errors="ignore").splitlines()
            last_messages = []
            files_seen = set()
            for ln in lines[-200:]:
                try:
                    entry = json.loads(ln)
                except Exception:
                    continue
                msg_type = entry.get("type") or entry.get("role")
                content = entry.get("content") or entry.get("message", {}).get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        (c.get("text", "") if isinstance(c, dict) else str(c)) for c in content
                    )
                content = str(content)[:300]
                if content and msg_type in ("user", "assistant"):
                    last_messages.append(f"[{msg_type}] {content}")
                for m in re.findall(r"/[A-Za-z0-9_./\-]+\.[a-z]{1,5}", content):
                    files_seen.add(m)
            digest["summary"] = " || ".join(last_messages[-5:])[:1500]
            digest["files_modified"] = sorted(files_seen)[:20]
        except Exception:
            pass

    try:
        digest_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
    except Exception:
        sys.exit(0)

    latest_path = sessions_dir / "_latest-digest.json"
    try:
        latest_path.write_text(json.dumps({"path": str(digest_path)}, ensure_ascii=False))
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
