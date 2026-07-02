#!/usr/bin/env python3
"""
check_capability_freshness.py — passive freshness lint for capability registry.

Closes TIL-17 AC4 (technical validation freshness) + TIL-14 AC6 (business
context freshness). Reads agents/_registry/capability-registry.yaml and emits
warnings to stderr when:

  - capability.last_validated is older than 180 days (technical staleness)
  - capability.business_context.revisado_em is older than 90 days (business)

This script is INTENTIONALLY NON-BLOCKING in Wave 1.5:

  - Exit code is always 0, regardless of staleness (do not break sessions)
  - Warnings to stderr only — wiring into SessionStart hook is Wave 2
  - No `settings.json` registration in this build (the artifact exists,
    ready to be wired by @devops once Wave 2 alarm policy is decided)

Usage:
    python3 .claude/hooks/check_capability_freshness.py
    python3 .claude/hooks/check_capability_freshness.py --json   # machine-readable
    python3 .claude/hooks/check_capability_freshness.py --strict # exit 1 if stale

ADR-TIL-001 compliance: hooks under .claude/hooks/ MUST be Python (stdlib +
PyYAML only). No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    print(
        "ERROR: PyYAML not installed. Install with: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


TECHNICAL_STALE_DAYS = 180  # TIL-17 AC4
BUSINESS_STALE_DAYS = 90  # TIL-14 AC6


@dataclass
class StalenessFinding:
    capability_id: str
    field: str  # 'last_validated' | 'business_context.revisado_em'
    last_seen: str  # ISO date string from registry
    age_days: int
    threshold_days: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "field": self.field,
            "last_seen": self.last_seen,
            "age_days": self.age_days,
            "threshold_days": self.threshold_days,
        }


def project_root() -> Path:
    """Resolve repo root from CLAUDE_PROJECT_DIR or upward search for .git."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists():
            return candidate
    return Path.cwd().resolve()


def parse_date(value: Any) -> date | None:
    """Accept YYYY-MM-DD strings or full ISO datetimes; return date or None."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            # ISO 8601 with optional time: take the date portion.
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
    return None


def scan_registry(registry: dict[str, Any], today: date | None = None) -> list[StalenessFinding]:
    """Return findings for capabilities whose timestamps exceed thresholds."""
    today = today or date.today()
    findings: list[StalenessFinding] = []
    capabilities = registry.get("capabilities") or {}
    for cap_id, body in capabilities.items():
        if not isinstance(body, dict):
            continue

        # TIL-17: technical validation freshness.
        last_validated = parse_date(body.get("last_validated"))
        if last_validated is not None:
            age = (today - last_validated).days
            if age > TECHNICAL_STALE_DAYS:
                findings.append(
                    StalenessFinding(
                        capability_id=cap_id,
                        field="last_validated",
                        last_seen=last_validated.isoformat(),
                        age_days=age,
                        threshold_days=TECHNICAL_STALE_DAYS,
                    )
                )

        # TIL-14: business context freshness.
        bc = body.get("business_context")
        if isinstance(bc, dict):
            revisado_em = parse_date(bc.get("revisado_em"))
            if revisado_em is not None:
                age = (today - revisado_em).days
                if age > BUSINESS_STALE_DAYS:
                    findings.append(
                        StalenessFinding(
                            capability_id=cap_id,
                            field="business_context.revisado_em",
                            last_seen=revisado_em.isoformat(),
                            age_days=age,
                            threshold_days=BUSINESS_STALE_DAYS,
                        )
                    )

    return findings


def render_warnings(findings: list[StalenessFinding]) -> str:
    if not findings:
        return ""
    lines = [
        "[capability-freshness] Stale entries detected (informational, non-blocking):",
    ]
    for f in findings:
        lines.append(
            f"  - {f.capability_id}.{f.field} = {f.last_seen} "
            f"(age {f.age_days}d, threshold {f.threshold_days}d)"
        )
    lines.append("  Recommendation: ask @devops to refresh these entries via the tool-onboarder.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="check_capability_freshness.py",
        description="Passive freshness lint for capability-registry.yaml.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON to stdout (for tooling).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any stale entries are found (default: exit 0 always).",
    )
    parser.add_argument(
        "--registry",
        type=str,
        default=None,
        help="Override path to capability-registry.yaml (default: <root>/agents/_registry/...).",
    )
    args = parser.parse_args(argv)

    root = project_root()
    registry_path = (
        Path(args.registry).resolve()
        if args.registry
        else root / "agents" / "_registry" / "capability-registry.yaml"
    )

    if not registry_path.exists():
        print(
            f"[capability-freshness] registry not found: {registry_path}",
            file=sys.stderr,
        )
        return 0  # do not break sessions if registry is missing

    try:
        with registry_path.open("r", encoding="utf-8") as fh:
            registry = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        print(f"[capability-freshness] failed to parse registry: {exc}", file=sys.stderr)
        return 0

    findings = scan_registry(registry)

    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        msg = render_warnings(findings)
        if msg:
            print(msg, file=sys.stderr)

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
