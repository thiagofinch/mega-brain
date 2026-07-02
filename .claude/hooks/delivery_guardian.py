#!/usr/bin/env python3
"""
Delivery Guardian -- Final QA gate for pipeline completeness.
=============================================================

Triggers: Stop event
Exit codes: 0 = pass (or no pipeline ran), 1 = warning, 2 = BLOCK (veto)

Reads ACTUAL FILES on disk to verify pipeline outputs exist.
Does NOT trust logs or state files -- goes to the source.

Saves report to logs/delivery-guardian/DELIVERY-{date}-{slug}.json
"""

import json
import os
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
MCE_STATE_DIR = PROJECT_ROOT / ".claude" / "mission-control" / "mce"
LOGS_DIR = PROJECT_ROOT / ".data" / "logs" / "delivery-guardian"  # S15: logs under .data
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _detect_pipeline_slugs() -> list[str]:
    """Detect slugs processed THIS SESSION by checking MCE state dir.

    Uses WHITELIST approach: only validates slugs that match known
    knowledge entities (experts, meetings, collaborators). Ignores
    all test/debug directories regardless of naming.
    """
    import time

    slugs: list[str] = []
    if not MCE_STATE_DIR.exists():
        return slugs

    # 4-hour window for "this session"
    cutoff = time.time() - (4 * 3600)

    # Build whitelist from actual knowledge entities on disk
    known_slugs: set[str] = set()

    # External experts (from DNA persons)
    dna_persons = PROJECT_ROOT / "knowledge" / "external" / "dna" / "persons"
    if dna_persons.exists():
        known_slugs.update(d.name for d in dna_persons.iterdir() if d.is_dir())

    # Business entities (from inbox)
    biz_inbox = PROJECT_ROOT / "knowledge" / "business" / "inbox"
    if biz_inbox.exists():
        known_slugs.update(d.name for d in biz_inbox.iterdir() if d.is_dir())

    # Meeting slugs (meet-NNNN pattern)
    known_slugs.update(
        d.name for d in MCE_STATE_DIR.iterdir() if d.is_dir() and d.name.startswith("meet-")
    )

    for child in MCE_STATE_DIR.iterdir():
        if not child.is_dir():
            continue
        # Only validate known entities
        if child.name not in known_slugs:
            continue
        # Check for recent pipeline activity
        state_file = child / "pipeline_state.yaml"
        if state_file.exists() and state_file.stat().st_mtime > cutoff:
            slugs.append(child.name)

    return slugs


def _check_dir_has_files(path: Path, label: str, pattern: str = "*") -> dict:
    if not path.exists():
        return {
            "name": label,
            "passed": False,
            "path": str(path),
            "detail": f"Directory MISSING: {path}",
            "blocking": True,
        }
    files = [f for f in path.glob(pattern) if f.is_file()]
    return {
        "name": label,
        "passed": len(files) > 0,
        "path": str(path),
        "detail": f"{len(files)} files found" if files else f"Directory EMPTY: {path}",
        "blocking": True,
    }


def _resolve_bucket(slug: str) -> str:
    """Resolve which knowledge bucket a person-slug belongs to.

    The founder-in-call routing rule (STORY-MCE-FOUNDER-ROUTING) introduced the
    first person-slugs that live under `business/` instead of `external/`. The
    guardian must check the bucket where the slug ACTUALLY lives, otherwise a
    correctly-delivered business partner is flagged as missing (false BLOCK).
    """
    biz = PROJECT_ROOT / "knowledge" / "business"
    # Markers must survive the full lifecycle, including the STEP 37 inbox->processed
    # move (which deletes inbox/{slug}). A business person-slug is identified by ANY
    # of: agent dir, inbox, processed (post-move home), DNA persons, or a business
    # dossier. Without processed/ + dossier, a completed business run wrongly falls
    # back to external once its inbox entry is moved away.
    business_markers = [
        PROJECT_ROOT / "agents" / "business" / slug,
        biz / "inbox" / slug,
        biz / "processed" / slug,
        biz / "dna" / "persons" / slug,
    ]
    if any(p.exists() for p in business_markers):
        return "business"
    dossier_dir = biz / "dossiers" / "persons"
    if dossier_dir.exists() and any(dossier_dir.glob(f"*{slug}*")):
        return "business"
    return "external"


def validate_slug(slug: str) -> dict:
    """Run all delivery checks for a single slug (bucket-aware).

    Partner-aware (STORY-MCE-FOUNDER-ROUTING): a business-bucket person-slug is
    typically a negotiation/partner counterpart, NOT an expert we mind-clone.
    For those, agent promotion is correctly gated by the Identity Checkpoint
    (STEP 22) — a thin single-call counterpart legitimately does NOT promote an
    agent or write per-layer DNA yamls. So for business slugs, `dna_yamls_exist`
    and `agent_files_exist` are INFORMATIONAL, not blocking. The real delivery
    bar for a business partner is: dossier + insights + chunks. External experts
    (meant to become agents) keep all five checks blocking.
    """
    checks: list[dict] = []
    bucket = _resolve_bucket(slug)
    kb_root = PROJECT_ROOT / "knowledge" / bucket
    agent_artifacts_required = bucket != "business"

    # 1. DNA yamls (non-blocking for business partners — see docstring)
    dna_dir = kb_root / "dna" / "persons" / slug
    dna_check = _check_dir_has_files(dna_dir, "dna_yamls_exist", "*.yaml")
    dna_check["blocking"] = agent_artifacts_required
    checks.append(dna_check)

    # 2. Dossier exists (blocking for all — the partner deliverable IS the dossier)
    dossier_dir = kb_root / "dossiers" / "persons"
    dossier_found = any(dossier_dir.glob(f"*{slug}*")) if dossier_dir.exists() else False
    checks.append(
        {
            "name": "dossier_exists",
            "passed": dossier_found,
            "path": str(dossier_dir),
            "blocking": True,
            "detail": "Dossier found" if dossier_found else f"No dossier matching '{slug}'",
        }
    )

    # 3. Agent files (non-blocking for business partners — promotion is gated by
    #    the Identity Checkpoint on evidence sufficiency, legitimately variable)
    agent_dir = PROJECT_ROOT / "agents" / bucket / slug
    agent_check = _check_dir_has_files(agent_dir, "agent_files_exist", "*.md")
    agent_check["blocking"] = agent_artifacts_required
    checks.append(agent_check)

    # 4. Insights state
    insights = PROJECT_ROOT / "artifacts" / "insights" / "INSIGHTS-STATE.json"
    checks.append(
        {
            "name": "insights_state_exists",
            "passed": insights.exists(),
            "path": str(insights),
            "blocking": True,
            "detail": "Found" if insights.exists() else "MISSING",
        }
    )

    # 5. Chunks state
    chunks = PROJECT_ROOT / "artifacts" / "chunks" / "CHUNKS-STATE.json"
    checks.append(
        {
            "name": "chunks_state_exists",
            "passed": chunks.exists(),
            "path": str(chunks),
            "blocking": True,
            "detail": "Found" if chunks.exists() else "MISSING",
        }
    )

    blocking_failures = [c["name"] for c in checks if not c["passed"] and c.get("blocking")]

    return {
        "slug": slug,
        "bucket": bucket,
        "passed": len(blocking_failures) == 0,
        "score": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        "checks": checks,
        "blocking_failures": blocking_failures,
        "timestamp": _now_iso(),
    }


def _save_report(report: dict) -> Path:
    date_str = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    path = LOGS_DIR / f"DELIVERY-{date_str}-{report.get('slug', 'unknown')}.json"
    try:
        path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
        )
    except Exception:
        pass
    return path


def main():
    try:
        _stdin = sys.stdin.read()
        slugs = _detect_pipeline_slugs()

        if not slugs:
            print(
                json.dumps(
                    {
                        "decision": "approve",
                        "reason": "[Delivery Guardian] No pipeline activity detected. Pass.",
                    }
                )
            )
            sys.exit(0)

        all_passed = True
        failures = []

        for slug in slugs:
            report = validate_slug(slug)
            _save_report(report)
            if not report["passed"]:
                all_passed = False
                failures.append(f"{slug}: {', '.join(report['blocking_failures'])}")

        if all_passed:
            print(
                json.dumps(
                    {
                        "decision": "approve",
                        "reason": f"[Delivery Guardian] All checks PASSED for {', '.join(slugs)}",
                    }
                )
            )
            sys.exit(0)
        else:
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": f"[Delivery Guardian] BLOCKED — {'; '.join(failures)}",
                    }
                )
            )
            sys.exit(2)

    except Exception as e:
        print(
            json.dumps(
                {
                    "decision": "approve",
                    "reason": f"[Delivery Guardian] Internal error (fail-open): {e}",
                }
            )
        )
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        slugs = _detect_pipeline_slugs()
        print(f"Detected slugs: {slugs}" if slugs else "No pipeline slugs detected.")
        for slug in slugs:
            print(json.dumps(validate_slug(slug), indent=2))
    else:
        main()
