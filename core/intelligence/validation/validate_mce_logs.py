#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   MCE LOG VALIDATOR                                                          ║
║   core/intelligence/validation/validate_mce_logs.py                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   Verifica que todos os steps esperados (3-10) estão logados para um slug.   ║
║   Útil para CI/CD e para debug pós-execução de pipeline.                    ║
║                                                                              ║
║   USAGE:                                                                     ║
║     python3 -m core.intelligence.validation.validate_mce_logs <slug>         ║
║     python3 validate_mce_logs.py alex-hormozi                               ║
║     python3 validate_mce_logs.py --all                                       ║
║     python3 validate_mce_logs.py alex-hormozi --verbose                      ║
║     python3 validate_mce_logs.py alex-hormozi --report                       ║
║                                                                              ║
║   EXIT CODES:                                                                ║
║     0  — todos os steps logados (PASS)                                       ║
║     1  — steps faltando (FAIL)                                               ║
║     2  — erro de setup (arquivo não encontrado, etc.)                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Project root: this file lives at core/intelligence/validation/
ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_PATH = ROOT / "logs" / "mce-step-logger.jsonl"

EXPECTED_STEPS = {3, 4, 5, 6, 7, 8, 9, 10}

STEP_NAMES = {
    3:  "chunking",
    4:  "entity_resolution",
    5:  "insight_extraction",
    6:  "mce_behavioral",
    7:  "mce_identity",
    8:  "mce_voice",
    9:  "identity_checkpoint",
    10: "consolidation",
}

# Sub-steps expected within Step 10
STEP10_SUBSTEPS = {"10.1_dossier", "10.3_dna_yaml", "10.4_agent"}

# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

W = 62


def _row(content: str) -> str:
    return f"│  {content[:W].ljust(W)}  │"


def _top() -> str:
    return f"┌{'─' * (W + 4)}┐"


def _bottom() -> str:
    return f"└{'─' * (W + 4)}┘"


def _div() -> str:
    return f"├{'─' * (W + 4)}┤"


def _section(title: str) -> str:
    return _row(f"▸ {title}")


# ─────────────────────────────────────────────────────────────────────────────
# LOG READING
# ─────────────────────────────────────────────────────────────────────────────


def _read_entries(slug: str | None = None) -> list[dict]:
    """Read all entries from mce-step-logger.jsonl, optionally filtered by slug."""
    if not LOG_PATH.exists():
        print(f"ERROR: Log file not found: {LOG_PATH}", file=sys.stderr)
        sys.exit(2)

    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if slug is None or entry.get("slug") == slug:
                    entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def _all_slugs() -> list[str]:
    """Return all unique slugs in the log file."""
    slugs: set[str] = set()
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line.strip())
                s = e.get("slug", "")
                if s and s != "unknown":
                    slugs.add(s)
            except Exception:
                pass
    return sorted(slugs)


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION LOGIC
# ─────────────────────────────────────────────────────────────────────────────


def _validate_slug(slug: str, entries: list[dict], verbose: bool = False) -> dict:
    """
    Validate log completeness for a slug.
    Returns a result dict with pass/fail details.
    """
    found_steps: dict[int, list[dict]] = defaultdict(list)
    step10_substeps: set[str] = set()
    validation_failures: dict[int, list[str]] = defaultdict(list)

    for e in entries:
        step = e.get("step", -1)
        if isinstance(step, int):
            found_steps[step].append(e)
            if step == 10:
                substep = e.get("metrics", {}).get("substep", "")
                if substep:
                    step10_substeps.add(substep)
            # Check for validation failures
            vdict = e.get("validation", {})
            for k, val in vdict.items():
                if isinstance(val, bool) and not val and not k.endswith("_count"):
                    validation_failures[step].append(k)

    missing_steps = EXPECTED_STEPS - set(found_steps.keys())
    missing_substeps = STEP10_SUBSTEPS - step10_substeps if 10 in found_steps else set()

    # Build per-step status
    step_status = {}
    for step in EXPECTED_STEPS:
        if step not in found_steps:
            step_status[step] = "MISSING"
        elif validation_failures.get(step):
            step_status[step] = "WARN"
        else:
            step_status[step] = "PASS"

    total_entries = sum(len(v) for v in found_steps.values())
    all_pass = len(missing_steps) == 0

    return {
        "slug":               slug,
        "pass":               all_pass,
        "missing_steps":      sorted(missing_steps),
        "missing_substeps":   sorted(missing_substeps),
        "total_entries":      total_entries,
        "step_status":        step_status,
        "validation_failures": dict(validation_failures),
        "found_steps":        sorted(found_steps.keys()),
        "step10_substeps":    sorted(step10_substeps),
        "timestamps":         {
            step: entries[-1].get("timestamp", "")
            for step, entries in found_steps.items()
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT FORMATTERS
# ─────────────────────────────────────────────────────────────────────────────


def _print_result(result: dict, verbose: bool = False) -> None:
    slug    = result["slug"]
    passing = result["pass"]
    missing = result["missing_steps"]

    status_line = "✅ PASS" if passing else f"❌ FAIL  ({len(missing)} steps faltando)"
    lines = [
        _top(),
        _row(f"MCE LOG VALIDATOR  —  slug: {slug}"),
        _div(),
        _row(f"Status         : {status_line}"),
        _row(f"Total Entradas : {result['total_entries']}"),
        _row(f"Steps Cobertos : {sorted(result['found_steps'])}"),
    ]

    if missing:
        lines.append(_row(""))
        lines.append(_section("STEPS FALTANDO"))
        for s in missing:
            lines.append(_row(f"  ❌ Step {s:02d} — {STEP_NAMES.get(s, '?')}"))

    if result.get("missing_substeps"):
        lines.append(_section("STEP 10 — SUB-STEPS FALTANDO"))
        for ss in result["missing_substeps"]:
            lines.append(_row(f"  ⚠️  {ss}"))

    if verbose:
        lines.append(_div())
        lines.append(_section("STATUS POR STEP"))
        status_icons = {"PASS": "✅", "WARN": "⚠️ ", "MISSING": "❌"}
        for step in sorted(EXPECTED_STEPS):
            status = result["step_status"].get(step, "MISSING")
            icon   = status_icons.get(status, "?")
            sname  = STEP_NAMES.get(step, "?")
            ts_raw = result["timestamps"].get(step, "")
            ts     = ts_raw[-8:-3] if ts_raw else "--:--"
            lines.append(_row(f"  {icon} S{step:02d} {sname:<22s} @ {ts}"))

        # Validation failures
        for step, failures in result["validation_failures"].items():
            if failures:
                lines.append(_row(f"     ↳ S{step:02d} check failures: {', '.join(failures)}"))

        # Step 10 substeps
        if 10 in result["found_steps"]:
            lines.append(_row(f"  S10 substeps: {', '.join(result['step10_substeps'])}"))

    lines.append(_bottom())
    print("\n".join(lines))


def _print_all_slugs_summary(results: list[dict]) -> None:
    passing = [r for r in results if r["pass"]]
    failing = [r for r in results if not r["pass"]]

    lines = [
        _top(),
        _row(f"MCE LOG VALIDATOR — TODOS OS SLUGS  ({len(results)} slugs)"),
        _div(),
        _row(f"  ✅ PASS : {len(passing)}"),
        _row(f"  ❌ FAIL : {len(failing)}"),
        _div(),
    ]
    for r in sorted(results, key=lambda x: (not x["pass"], x["slug"])):
        mark = "✅" if r["pass"] else "❌"
        missing_str = f"  missing: {r['missing_steps']}" if r["missing_steps"] else ""
        lines.append(_row(f"  {mark}  {r['slug']:<30s}{missing_str}"))
    lines.append(_bottom())
    print("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate MCE step log completeness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 validate_mce_logs.py alex-hormozi
  python3 validate_mce_logs.py alex-hormozi --verbose
  python3 validate_mce_logs.py --all
""",
    )
    p.add_argument("slug", nargs="?", help="Slug to validate (e.g. alex-hormozi)")
    p.add_argument("--all",     action="store_true", help="Validate all slugs in log file")
    p.add_argument("--verbose", action="store_true", help="Show per-step breakdown")
    p.add_argument("--report",  action="store_true", help="Output full JSON report")
    p.add_argument(
        "--log",
        default=str(LOG_PATH),
        help=f"Path to mce-step-logger.jsonl (default: {LOG_PATH})",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    # Allow --log override
    global LOG_PATH
    LOG_PATH = Path(args.log)

    if args.all:
        slugs = _all_slugs()
        if not slugs:
            print("No slugs found in log file.")
            sys.exit(2)
        results = []
        for slug in slugs:
            entries = _read_entries(slug)
            results.append(_validate_slug(slug, entries, args.verbose))
        _print_all_slugs_summary(results)
        any_fail = any(not r["pass"] for r in results)
        sys.exit(1 if any_fail else 0)

    if not args.slug:
        parser.print_help()
        sys.exit(2)

    entries = _read_entries(args.slug)
    if not entries:
        print(f"\n  ⚠️  Nenhuma entrada encontrada para slug: '{args.slug}'")
        print(f"  Verifique se o slug está correto e se a pipeline foi executada.\n")
        sys.exit(1)

    result = _validate_slug(args.slug, entries, args.verbose)

    if args.report:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_result(result, args.verbose)

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
