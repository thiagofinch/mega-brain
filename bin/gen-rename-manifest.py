#!/usr/bin/env python3
"""
bin/gen-rename-manifest.py — Rename Manifest Generator

Scans agents/, outputs/, knowledge/, processing/, artifacts/ for files and
directories whose basenames violate the lowercase kebab-case convention.
Outputs rename-manifest.json sorted bottom-up (files before dirs).

Usage:
    python bin/gen-rename-manifest.py            # Generate manifest
    python bin/gen-rename-manifest.py --dry-run   # Print summary only

Story 4.1 | Epic AGENT-ARCH | ADR-004 D1
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories to scan
SCAN_ROOTS = ["agents", "outputs", "knowledge", "processing", "artifacts"]

# Directories to skip entirely
SKIP_DIRS = {".git", ".claude", "node_modules", "__pycache__", ".env", ".venv", ".data"}

# Files with conventional uppercase names (never rename)
UPPERCASE_ALLOWLIST = {
    "README.md",
    "CLAUDE.md",
    "AGENT-INDEX.yaml",
    "MASTER-AGENT.md",
    "SHARED-RULES.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "LICENSE.md",
    "Dockerfile",
    "Makefile",
}

# Patterns for allowlisted filenames
UPPERCASE_PATTERNS = [
    re.compile(r"^ADR-.*\.md$"),
    re.compile(r"^SPEC-.*\.md$"),
    re.compile(r"^EPIC-.*\.md$"),
    re.compile(r"^STORY-.*\.md$"),
]

# The target convention (allows dots for versioned files like w0.1, meet-0007)
KEBAB_CASE = re.compile(r"^[a-z0-9]+([-.][a-z0-9]+)*$")

# Extension-stripped check: we check the stem, not the full basename
# Files like "foo.py" have stem "foo", extension ".py"
# Dirs have no extension


def is_allowlisted(basename: str) -> bool:
    if basename in UPPERCASE_ALLOWLIST:
        return True
    if basename.startswith("."):
        return True
    for pattern in UPPERCASE_PATTERNS:
        if pattern.match(basename):
            return True
    return False


def to_kebab_case(name: str) -> str:
    """Convert a name to lowercase kebab-case."""
    import unicodedata
    # Normalize unicode (é → e, ã → a, etc.)
    result = unicodedata.normalize("NFKD", name)
    result = result.encode("ascii", "ignore").decode("ascii")
    result = result.lower()
    # Replace common separators with hyphens
    result = result.replace("_", "-").replace(" ", "-")
    # Remove brackets, parens, ampersands, plus, commas, quotes
    result = re.sub(r"[\[\]\(\)&+,;:'\"!@#$%^*={}|\\/<>?~`]", "", result)
    # Clean dot-hyphen and hyphen-dot sequences
    result = re.sub(r"\.-", "-", result)
    result = re.sub(r"-\.", "-", result)
    # Collapse multiple hyphens and dots
    result = re.sub(r"\.+", ".", result)
    result = re.sub(r"-+", "-", result)
    result = result.strip("-.")
    return result


def stem_violates(basename: str) -> bool:
    """Check if the stem of a filename violates kebab-case."""
    if is_allowlisted(basename):
        return False

    p = Path(basename)
    stem = p.stem
    # For dotfiles or hidden files, skip
    if stem == "" or stem.startswith("."):
        return False

    return not KEBAB_CASE.match(stem)


def dir_violates(dirname: str) -> bool:
    """Check if a directory name violates kebab-case."""
    if dirname.startswith(".") or dirname in SKIP_DIRS:
        return False
    if is_allowlisted(dirname):
        return False
    return not KEBAB_CASE.match(dirname)


def compute_new_basename(basename: str, is_dir: bool) -> str:
    """Compute the kebab-case version of a basename."""
    if is_dir:
        return to_kebab_case(basename)

    p = Path(basename)
    stem = to_kebab_case(p.stem)
    suffix = p.suffix.lower()
    return f"{stem}{suffix}"


def scan_violations(scan_root: Path) -> list[dict]:
    """Walk bottom-up and collect all violations."""
    violations = []

    if not scan_root.exists():
        return violations

    for dirpath, dirnames, filenames in os.walk(scan_root, topdown=False):
        dirpath = Path(dirpath)

        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        # Check files first (bottom-up: files before dirs)
        for fname in sorted(filenames):
            if stem_violates(fname):
                old_rel = str((dirpath / fname).relative_to(ROOT))
                new_basename = compute_new_basename(fname, is_dir=False)
                new_rel = str((dirpath / new_basename).relative_to(ROOT))
                violations.append({"old_path": old_rel, "new_path": new_rel})

        # Check directory names
        for dname in sorted(dirnames):
            if dir_violates(dname):
                old_rel = str((dirpath / dname).relative_to(ROOT))
                new_dname = to_kebab_case(dname)
                new_rel = str((dirpath / new_dname).relative_to(ROOT))
                violations.append({"old_path": old_rel, "new_path": new_rel})

    return violations


def main():
    parser = argparse.ArgumentParser(description="Generate rename manifest for lowercase kebab-case convention")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing JSON")
    args = parser.parse_args()

    all_violations = []
    summary = {}

    for scan_name in SCAN_ROOTS:
        scan_path = ROOT / scan_name
        violations = scan_violations(scan_path)
        all_violations.extend(violations)
        summary[scan_name] = len(violations)

    total = len(all_violations)

    if args.dry_run:
        print(f"Rename Manifest — Dry Run")
        print(f"{'=' * 40}")
        print(f"Total violations found: {total}")
        print()
        for root_name, count in summary.items():
            print(f"  {root_name}/: {count} violations")
        if total > 0:
            print()
            print("Sample violations (first 10):")
            for v in all_violations[:10]:
                print(f"  {v['old_path']} -> {v['new_path']}")
        sys.exit(0)

    manifest_path = ROOT / "rename-manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(all_violations, f, indent=2, ensure_ascii=False)

    print(f"Wrote {total} entries to {manifest_path}")
    for root_name, count in summary.items():
        print(f"  {root_name}/: {count}")


if __name__ == "__main__":
    main()
