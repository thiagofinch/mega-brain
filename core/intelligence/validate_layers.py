#!/usr/bin/env python3
"""
Layer Validation Script for Mega Brain Repository

Validates classification conformance: checks that no L3/NEVER files are
tracked by git (would indicate accidental commit of personal/sensitive data).

Usage:
    python3 core/intelligence/validate_layers.py           # Validate only, exit 0/1
    python3 core/intelligence/validate_layers.py --report  # Validate + write reports
    python3 core/intelligence/validate_layers.py --verbose # Print each checked file

Exit codes:
    0 = PASS (no hard violations — CI green)
    1 = FAIL (hard violations found — CI red)
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Import from sibling module in same directory
sys.path.insert(0, str(Path(__file__).parent))
from audit_layers import classify_path, scan_repository


def _unquote_git_path(line: str) -> str:
    """Decode git's C-style quoted path (octal escapes + surrounding quotes).

    Git quotes paths containing non-ASCII or special characters, e.g.:
      "knowledge/dna 2/skills/unknown/benefi\\314\\201cios.md"
    This decodes octal escapes to bytes, then decodes as UTF-8.
    """
    if not (line.startswith('"') and line.endswith('"')):
        return line
    inner = line[1:-1]
    # Decode octal escapes (\\NNN) to raw bytes
    parts = []
    i = 0
    while i < len(inner):
        if inner[i] == '\\' and i + 3 < len(inner) and inner[i+1:i+4].isdigit():
            parts.append(int(inner[i+1:i+4], 8))
            i += 4
        elif inner[i] == '\\' and i + 1 < len(inner):
            # Other escape sequences
            esc = inner[i+1]
            if esc == 'n':
                parts.append(ord('\n'))
            elif esc == 't':
                parts.append(ord('\t'))
            elif esc == '\\':
                parts.append(ord('\\'))
            elif esc == '"':
                parts.append(ord('"'))
            else:
                parts.append(ord(inner[i]))
                parts.append(ord(esc))
            i += 2
        else:
            parts.append(ord(inner[i]))
            i += 1
    return bytes(parts).decode('utf-8', errors='replace')


def get_git_tracked_files(repo_root: Path) -> set:
    """Return the set of git-tracked file paths (relative to repo root)."""
    result = subprocess.run(
        ['git', 'ls-files'],
        capture_output=True, text=True, cwd=str(repo_root)
    )
    if result.returncode != 0:
        print(f"WARNING: git ls-files failed: {result.stderr.strip()}", file=sys.stderr)
        return set()
    lines = result.stdout.strip().splitlines()
    return {_unquote_git_path(line) for line in lines} if lines else set()


def validate_repository(repo_root: Path, verbose: bool = False) -> dict:
    """
    Validate layer conformance for git-tracked files.

    Returns a structured report dict.
    """
    tracked_files = get_git_tracked_files(repo_root)

    hard_violations = []   # L3 or NEVER files that are git-tracked
    soft_violations = []   # DELETE files still tracked
    review_tracked = []    # REVIEW files tracked (informational only)

    if verbose:
        print(f"Checking {len(tracked_files)} git-tracked files...")
        print()

    for rel_path_str in sorted(tracked_files):
        abs_path = repo_root / rel_path_str
        try:
            layer, reason = classify_path(abs_path, repo_root, is_file=True)
        except Exception as exc:
            if verbose:
                print(f"  [ERROR] {rel_path_str}: {exc}")
            continue

        if verbose:
            print(f"  [{layer}] {rel_path_str}")

        if layer in ('L3', 'NEVER'):
            hard_violations.append({
                'path': rel_path_str,
                'layer': layer,
                'reason': reason,
            })
        elif layer == 'DELETE':
            soft_violations.append({
                'path': rel_path_str,
                'layer': layer,
                'reason': reason,
            })
        elif layer == 'REVIEW':
            review_tracked.append({
                'path': rel_path_str,
                'reason': reason,
            })

    hard_count = len(hard_violations)
    soft_count = len(soft_violations)
    review_count = len(review_tracked)
    status = 'PASS' if hard_count == 0 else 'FAIL'

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'repo_root': str(repo_root),
        'git_tracked_files': len(tracked_files),
        'violations': {
            'hard': hard_violations,
            'soft': soft_violations,
        },
        'warnings': {
            'review_tracked': review_tracked,
        },
        'summary': {
            'hard_violation_count': hard_count,
            'soft_violation_count': soft_count,
            'review_tracked_count': review_count,
            'status': status,
        },
    }

    return report


def print_summary(report: dict) -> None:
    """Print a human-readable summary to stdout."""
    s = report['summary']
    status_icon = '✅' if s['status'] == 'PASS' else '❌'
    print()
    print('=' * 60)
    print('LAYER VALIDATION SUMMARY')
    print('=' * 60)
    print(f"Git-tracked files checked : {report['git_tracked_files']}")
    print(f"Hard violations (L3/NEVER): {s['hard_violation_count']}")
    print(f"Soft warnings (DELETE)    : {s['soft_violation_count']}")
    print(f"Review items tracked      : {s['review_tracked_count']}")
    print(f"Status                    : {status_icon} {s['status']}")
    print('=' * 60)

    if s['hard_violation_count'] > 0:
        print()
        print('HARD VIOLATIONS (must fix before merge):')
        for v in report['violations']['hard']:
            print(f"  [{v['layer']}] {v['path']} — {v['reason']}")

    if s['soft_violation_count'] > 0:
        print()
        print('SOFT WARNINGS (DELETE items still tracked):')
        for v in report['violations']['soft']:
            print(f"  [DELETE] {v['path']} — {v['reason']}")

    print()


def generate_markdown_report(report: dict, output_path: Path) -> None:
    """Write human-readable markdown validation report."""
    s = report['summary']
    status_icon = '✅ PASS' if s['status'] == 'PASS' else '❌ FAIL'

    with open(output_path, 'w') as f:
        f.write('# Mega Brain Layer Validation Report\n\n')
        f.write(f"**Generated:** {report['generated_at']}\n")
        f.write(f"**Repository:** {report['repo_root']}\n")
        f.write(f"**Git-tracked files checked:** {report['git_tracked_files']}\n\n")

        f.write(f"## Status: {status_icon}\n\n")
        f.write('| Metric | Count |\n')
        f.write('|--------|------:|\n')
        f.write(f"| Hard violations (L3/NEVER tracked by git) | {s['hard_violation_count']} |\n")
        f.write(f"| Soft warnings (DELETE tracked by git) | {s['soft_violation_count']} |\n")
        f.write(f"| Review items tracked | {s['review_tracked_count']} |\n\n")

        # Hard violations
        f.write('## Hard Violations\n\n')
        if report['violations']['hard']:
            f.write('These files are classified as L3 or NEVER but are tracked by git. '
                    'This is a security/privacy risk.\n\n')
            f.write('| Path | Layer | Reason |\n')
            f.write('|------|-------|--------|\n')
            for v in report['violations']['hard']:
                f.write(f"| `{v['path']}` | {v['layer']} | {v['reason']} |\n")
        else:
            f.write('No hard violations found.\n')

        # Soft warnings
        f.write('\n## Soft Warnings (DELETE items still tracked)\n\n')
        if report['violations']['soft']:
            f.write('These files are marked for deletion but are still in git index.\n\n')
            f.write('| Path | Reason |\n')
            f.write('|------|--------|\n')
            for v in report['violations']['soft']:
                f.write(f"| `{v['path']}` | {v['reason']} |\n")
        else:
            f.write('No DELETE items tracked by git.\n')

        # Review items
        f.write('\n## Review Items Tracked\n\n')
        review_list = report['warnings']['review_tracked']
        f.write(f"**{len(review_list)} REVIEW-classified files** are tracked by git. "
                'These need human classification but are not violations.\n')
        if review_list:
            f.write('\nFirst 20 paths:\n\n')
            for item in review_list[:20]:
                f.write(f"- `{item['path']}`\n")
            if len(review_list) > 20:
                f.write(f"\n*...and {len(review_list) - 20} more. Run with --report to see full list in JSON.*\n")

        # How to fix
        f.write('\n## How to Fix Violations\n\n')
        f.write('**L3 file accidentally committed:**\n')
        f.write('```bash\n')
        f.write('# Remove from git index (keeps local file)\n')
        f.write('git rm --cached <path>\n')
        f.write('# Add to .gitignore to prevent re-tracking\n')
        f.write('echo "<path>" >> .gitignore\n')
        f.write('```\n\n')
        f.write('**NEVER file accidentally committed:**\n')
        f.write('```bash\n')
        f.write('# Remove from git history entirely (use BFG or filter-branch)\n')
        f.write('git rm --cached <path>\n')
        f.write('echo "<path>" >> .gitignore\n')
        f.write('# If file contains secrets, rotate all credentials immediately\n')
        f.write('```\n\n')
        f.write('**Use as CI gate:**\n')
        f.write('```bash\n')
        f.write('python3 core/intelligence/validate_layers.py\n')
        f.write('# Exit code 0 = PASS, exit code 1 = FAIL\n')
        f.write('```\n')


def main():
    parser = argparse.ArgumentParser(
        description='Validate Mega Brain layer conformance (CI-runnable)'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Write JSON + Markdown reports to docs/audit/',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print each git-tracked file as it is checked',
    )
    args = parser.parse_args()

    # Resolve repo root: core/intelligence/ -> core/ -> mega-brain/
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    if not (repo_root / 'core').exists():
        print(f"ERROR: Could not find repo root. Expected core/ in {repo_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Repository: {repo_root}")
    print('Running layer validation...')

    report = validate_repository(repo_root, verbose=args.verbose)
    print_summary(report)

    if args.report:
        output_dir = repo_root / 'docs' / 'audit'
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / 'VALIDATION-REPORT.json'
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ JSON report written to: {json_path}")

        md_path = output_dir / 'VALIDATION-REPORT.md'
        generate_markdown_report(report, md_path)
        print(f"✅ Markdown report written to: {md_path}")
        print()

    # Exit 0 = PASS, exit 1 = FAIL (hard violations present)
    sys.exit(0 if report['summary']['hard_violation_count'] == 0 else 1)


if __name__ == '__main__':
    main()
