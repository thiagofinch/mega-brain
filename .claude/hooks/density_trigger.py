#!/usr/bin/env python3
"""density_trigger.py — Auto-trigger cmd_consolidate when dossier density >= 3.

Story MCE-3.16, AC3. Ported from JARVIS v2.1 DNA-EXTRACTION-PROTOCOL v1.2.

Behavior:
  - Listens to PostToolUse Write|Edit.
  - When a touched path matches `knowledge/{bucket}/dossiers/persons/dossier-*.md`,
    re-computes density via `engine.intelligence.density`.
  - If density >= 3 AND the slug hasn't been triggered yet (or density grew),
    forks `python3 -m engine.intelligence.pipeline.mce.orchestrate consolidate <slug>`
    in the background.
  - Records flag `.data/density-triggers/<slug>.json` with last_density,
    triggers_count, last_triggered_at. Enforces retry_budget=3.

Env knobs:
  MCE_DENSITY_TRIGGER_DISABLED=1   skip entirely (kill switch)
  MCE_DENSITY_TRIGGER_DRY_RUN=1    compute + log but do NOT fork consolidate
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
TRIGGER_FLAG_DIR = PROJECT_DIR / ".data" / "density-triggers"
TRIGGER_THRESHOLD = 3
RETRY_BUDGET = 3
HOOK_TIMEOUT_S = 8  # AC V5: < 10s


def _parse_payload() -> dict:
    if sys.stdin.isatty():
        return {}
    try:
        return json.load(sys.stdin) or {}
    except (json.JSONDecodeError, ValueError):
        return {}


def _candidate_paths(payload: dict) -> list[str]:
    tool_input = payload.get("tool_input") or {}
    paths = [
        tool_input.get("file_path"),
        tool_input.get("path"),
        tool_input.get("notebook_path"),
    ]
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            paths.append(edit.get("file_path"))
    return [str(p) for p in paths if p]


def _match_dossier(path_str: str) -> tuple[str | None, str | None]:
    """Return (slug, bucket) if path is a person dossier, else (None, None)."""
    p = Path(path_str)
    parts = p.parts
    # Heuristic: looking for `.../knowledge/{bucket}/dossiers/persons/dossier-X.md`
    if "knowledge" not in parts or "dossiers" not in parts or "persons" not in parts:
        return None, None
    if not p.name.startswith("dossier-") or p.suffix.lower() != ".md":
        return None, None
    try:
        idx = parts.index("knowledge")
        bucket = parts[idx + 1]
    except (ValueError, IndexError):
        return None, None
    slug = p.stem[len("dossier-") :]
    return slug, bucket


def _load_flag(slug: str) -> dict:
    flag_path = TRIGGER_FLAG_DIR / f"{slug}.json"
    if not flag_path.is_file():
        return {}
    try:
        return json.loads(flag_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_flag(slug: str, data: dict) -> None:
    TRIGGER_FLAG_DIR.mkdir(parents=True, exist_ok=True)
    flag_path = TRIGGER_FLAG_DIR / f"{slug}.json"
    try:
        flag_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"[density_trigger] cannot persist flag: {exc}\n")


def _should_trigger(prev: dict, density: int) -> bool:
    """Idempotency check.

    Trigger when:
      - never triggered before (prev is empty), OR
      - density grew since last successful trigger, AND
      - we still have budget left.
    """
    if not prev:
        return True
    triggers = int(prev.get("triggers_count", 0))
    last_density = int(prev.get("last_density", 0))
    if triggers >= RETRY_BUDGET and density <= last_density:
        return False
    return density > last_density or triggers < RETRY_BUDGET


def _fire_consolidate(slug: str, bucket: str) -> bool:
    """Spawn background consolidate. Returns True on launch, False on dry-run."""
    if os.environ.get("MCE_DENSITY_TRIGGER_DRY_RUN") == "1":
        return False
    log_dir = PROJECT_DIR / ".data" / "logs" / "density-triggers"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{slug}.log"
    try:
        with open(log_file, "ab") as fp:
            fp.write(
                f"\n--- consolidate {slug} ({bucket}) "
                f"{datetime.now(UTC).isoformat()} ---\n".encode()
            )
            subprocess.Popen(
                [
                    "python3",
                    "-m",
                    "engine.intelligence.pipeline.mce.orchestrate",
                    "consolidate",
                    slug,
                ],
                cwd=str(PROJECT_DIR),
                stdout=fp,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        sys.stderr.write(f"[density_trigger] spawn failed: {exc}\n")
        return False
    return True


def process_dossier(slug: str, bucket: str) -> dict:
    """Public entry point used by tests too. Returns the outcome dict."""
    # Import here so test imports don't pay the cost
    from engine.intelligence.density import compute_dossier_density

    info = compute_dossier_density(slug, bucket, root=PROJECT_DIR)
    density = int(info.get("density", 0))
    prev = _load_flag(slug)

    outcome = {
        "slug": slug,
        "bucket": bucket,
        "density": density,
        "previous": prev,
        "fired": False,
        "skipped_reason": None,
    }

    if density < TRIGGER_THRESHOLD:
        outcome["skipped_reason"] = f"density {density} < {TRIGGER_THRESHOLD}"
        return outcome
    if not _should_trigger(prev, density):
        outcome["skipped_reason"] = "idempotency: retry budget exhausted or no growth"
        return outcome

    launched = _fire_consolidate(slug, bucket)
    outcome["fired"] = launched

    triggers_count = int(prev.get("triggers_count", 0)) + (1 if launched else 0)
    _save_flag(
        slug,
        {
            "slug": slug,
            "bucket": bucket,
            "last_density": density,
            "last_triggered_at": datetime.now(UTC).isoformat(),
            "triggers_count": triggers_count,
            "retry_budget": RETRY_BUDGET,
            "dry_run": not launched and os.environ.get("MCE_DENSITY_TRIGGER_DRY_RUN") == "1",
        },
    )
    return outcome


def main() -> int:
    if os.environ.get("MCE_DENSITY_TRIGGER_DISABLED") == "1":
        return 0
    payload = _parse_payload()
    for cand in _candidate_paths(payload):
        slug, bucket = _match_dossier(cand)
        if not slug or not bucket:
            continue
        try:
            outcome = process_dossier(slug, bucket)
        except Exception as exc:
            sys.stderr.write(f"[density_trigger] non-fatal: {exc}\n")
            continue
        if outcome["fired"]:
            sys.stderr.write(
                f"[density_trigger] {slug} density={outcome['density']} → consolidate spawned\n"
            )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write(f"[density_trigger] crashed: {exc}\n")
        sys.exit(0)
