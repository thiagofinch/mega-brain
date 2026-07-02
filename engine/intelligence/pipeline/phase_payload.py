"""Phase payload emitter for Chronicler render layer.

Each pipeline cmd emits a structured payload describing its phase
outcome. Chronicler later consumes these payloads to render canonical
boxes + free-form boxes in the chat.

Payloads are append-only JSONL at:
  artifacts/pipeline/{slug}/PHASE-STREAM.jsonl

This module is the canonical interface between pipeline cmds and the
render layer (Constitution Art. XII — Pipeline MCE Integrity).

Phase 3 of STORY-MCE-6.0 (2026-05-22).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from engine.paths import ARTIFACTS


def emit_phase_payload(
    *,
    slug: str,
    template_id: str,
    status: str,
    metrics: dict[str, Any],
    ascii_block: str,
    schema_version: str = "1.0.0",
    artifacts_root: Path | None = None,
) -> Path:
    """Append a phase payload to PHASE-STREAM.jsonl.

    Writes are append-only and non-blocking. Any write failure is silently
    swallowed (logged to stderr only) so callers are never broken by this.

    Args:
        slug: bucket-relative slug (e.g. "alex-hormozi")
        template_id: canonical template name (see chronicler-registry.yaml).
                     Maps to a render function in the Chronicler skill.
        status: "ok" | "warning" | "fail" | "silent"
        metrics: arbitrary structured metrics for this phase (cmd-specific)
        ascii_block: the verbatim ASCII box already emitted to stdout.
                     Stored so Chronicler can re-emit or diff against history.
        schema_version: payload schema version (default 1.0.0)
        artifacts_root: optional override for artifacts/ root path.
                        Defaults to artifacts/pipeline/{slug}/ relative to cwd.

    Returns:
        Path to PHASE-STREAM.jsonl after append.
    """
    root = artifacts_root or (ARTIFACTS / "pipeline" / slug)
    root.mkdir(parents=True, exist_ok=True)
    out = root / "PHASE-STREAM.jsonl"

    entry = {
        "ts": time.time(),
        "slug": slug,
        "template_id": template_id,
        "status": status,
        "metrics": metrics,
        "ascii_block": ascii_block,
        "schema_version": schema_version,
    }

    try:
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        import sys

        print(
            f"[phase_payload] WARNING: could not write to {out}: {exc}",
            file=sys.stderr,
            flush=True,
        )

    return out
