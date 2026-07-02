"""
pipeline_manifest_watcher.py -- PostToolUse hook to rebuild manifest
Fires when any truth source is modified.
Non-fatal, ~5 lines of logic.

Version: 1.0.0
Date: 2026-03-29
Source: MEGABRAIN-LOG-SYSTEM-IMPL.md PARTE 8
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

WATCHED = {"mce_checkpoints.yaml", "mce-workflow-rules.yaml", "SKILL.md", "state_machine.py"}
logger = logging.getLogger("hooks.manifest_watcher")


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            return
        payload = json.loads(raw)
        inp = payload.get("tool_input", {})
        path_str = inp.get("path", "") or inp.get("file_path", "") or ""
        if Path(path_str).name in WATCHED:
            from engine.intelligence.pipeline.mce.pipeline_manifest_builder import build_manifest

            build_manifest(force=True)
            print(
                f"[manifest_watcher] PIPELINE-MANIFEST.json rebuilt ({Path(path_str).name} changed)",
                flush=True,
            )
    except Exception as exc:
        logger.debug("manifest_watcher: %s", exc)


if __name__ == "__main__":
    main()
