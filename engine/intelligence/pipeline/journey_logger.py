"""Journey Logger — append-only audit trail for entity lifecycle events.

Constitution Art. IX (Journey Log Mandatory):
    - Toda entidade que nasce DEVE ativar registro no journey log
    - Toda entidade que morre DEVE consolidar seu log antes de encerramento
    - Transicoes de estado DEVEM ser registradas com from_state, to_state, timestamp
    - Journey logs sao append-only — NUNCA deletar ou editar entries existentes
    - Metadata minima: entity_id, entity_type, event_type, from_state, to_state,
      timestamp, triggered_by

Story: MCE-INGEST-ROBUSTNESS (Wave 2, AC-8) — 2026-05-27.

Initial focus: bucket decisions across multiple pipeline layers.
Extensible to other lifecycle events (slug_promoted, dossier_consolidated, ...).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Repo root resolution — fail-safe
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[3]
_LOG_DIR = _REPO_ROOT / ".data" / "logs" / "journey"
_BUCKET_LOG = _LOG_DIR / "bucket-decisions.jsonl"
_GENERIC_LOG = _LOG_DIR / "lifecycle-events.jsonl"


def _ensure_dir() -> None:
    """Idempotent dir creation."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    """Append a JSON object as one line. Fail-open."""
    try:
        _ensure_dir()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        # Journey log failure must never crash a pipeline (Art. XII)
        pass


def emit_bucket_decision(
    *,
    entity_id: str,
    entity_type: str,
    from_state: str | None,
    to_state: str,
    triggered_by: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    """Append a bucket-decision event to bucket-decisions.jsonl.

    Schema (Constitution Art. IX minimum + bucket-specific extras):
        entity_id:    str  — slug or unique identifier of the entity
        entity_type:  str  — "person" | "company" | "meeting" | "slug"
        event_type:   str  — "bucket_decided" (fixed for this fn)
        from_state:   str | None — previous bucket or None for first decision
        to_state:     str  — bucket decided ("business" | "external" | "personal")
        timestamp:    str  — ISO 8601 UTC
        triggered_by: str  — fully qualified caller (e.g. "FirefliesSync.MeetingRouter")
        evidence:     dict — caller-specific signals for audit

    Conflict detection: if the same entity_id appears with divergent to_state
    across triggered_by sources within the log, downstream tools can flag WARN.
    """
    entry: dict[str, Any] = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "event_type": "bucket_decided",
        "from_state": from_state,
        "to_state": to_state,
        "timestamp": _now_iso(),
        "triggered_by": triggered_by,
        "evidence": evidence or {},
    }
    _append_jsonl(_BUCKET_LOG, entry)


def emit_lifecycle_event(
    *,
    entity_id: str,
    entity_type: str,
    event_type: str,
    from_state: str | None,
    to_state: str | None,
    triggered_by: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Generic append-only lifecycle event (entity birth, death, transition).

    Constitution Art. IX universal recorder. Use for events that don't fit
    a specialized recorder (bucket decisions use emit_bucket_decision).
    """
    entry: dict[str, Any] = {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "event_type": event_type,
        "from_state": from_state,
        "to_state": to_state,
        "timestamp": _now_iso(),
        "triggered_by": triggered_by,
        "payload": payload or {},
    }
    _append_jsonl(_GENERIC_LOG, entry)


def detect_bucket_conflicts() -> list[dict[str, Any]]:
    """Scan bucket-decisions.jsonl for entities with divergent decisions.

    Returns list of conflict dicts: {entity_id, decisions: [{to_state, triggered_by, timestamp}, ...]}

    Used by CLI ``python3 -m engine.intelligence.pipeline.journey_logger conflicts``.
    """
    if not _BUCKET_LOG.exists():
        return []
    decisions: dict[str, list[dict[str, Any]]] = {}
    try:
        with _BUCKET_LOG.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                eid = e.get("entity_id")
                if not eid:
                    continue
                decisions.setdefault(eid, []).append({
                    "to_state": e.get("to_state"),
                    "triggered_by": e.get("triggered_by"),
                    "timestamp": e.get("timestamp"),
                })
    except Exception:
        return []
    conflicts = []
    for eid, dec_list in decisions.items():
        states = {d.get("to_state") for d in dec_list if d.get("to_state")}
        if len(states) > 1:
            conflicts.append({"entity_id": eid, "states": sorted(states), "decisions": dec_list})
    return conflicts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_tail(args) -> int:
    if not _BUCKET_LOG.exists():
        print("(no bucket-decisions.jsonl yet)")
        return 0
    n = args.n
    try:
        lines = _BUCKET_LOG.read_text(encoding="utf-8").strip().split("\n")
    except Exception:
        return 1
    for ln in lines[-n:]:
        try:
            e = json.loads(ln)
            print(
                f"{e.get('timestamp','')} | {e.get('entity_id',''):30s} | "
                f"{(e.get('from_state') or '-'):8s} -> {e.get('to_state',''):10s} | "
                f"{e.get('triggered_by','')}"
            )
        except Exception:
            print(ln)
    return 0


def _cmd_conflicts(args) -> int:
    conflicts = detect_bucket_conflicts()
    if not conflicts:
        print("No bucket-decision conflicts detected.")
        return 0
    print(f"⚠ {len(conflicts)} entity/entities have divergent bucket decisions:\n")
    for c in conflicts:
        print(f"  - {c['entity_id']} -> states: {c['states']}")
        for d in c["decisions"]:
            print(
                f"      {d.get('timestamp','')} | {d.get('triggered_by','')} -> "
                f"{d.get('to_state','')}"
            )
    return 0 if not args.fail else 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="journey_logger",
        description="Journey log inspector (Story MCE-INGEST-ROBUSTNESS AC-8)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_tail = sub.add_parser("tail", help="Show last N bucket-decision entries")
    sp_tail.add_argument("-n", type=int, default=20)
    sp_tail.set_defaults(func=_cmd_tail)

    sp_conf = sub.add_parser("conflicts", help="Detect entities with divergent decisions")
    sp_conf.add_argument("--fail", action="store_true", help="Exit 1 if conflicts found")
    sp_conf.set_defaults(func=_cmd_conflicts)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    import sys
    sys.exit(main())
