#!/usr/bin/env python3
"""
bin/apply-rename-manifest.py — Bulk Rename Executor

Reads rename-manifest.json (or a custom path) and applies renames bottom-up.
Uses git mv for tracked files, shutil.move for untracked.

Usage:
    python3 bin/apply-rename-manifest.py                          # Apply casing renames
    python3 bin/apply-rename-manifest.py --semantic               # Apply semantic renames only
    python3 bin/apply-rename-manifest.py --manifest custom.json   # Custom manifest path

Story 4.2 | Epic AGENT-ARCH | ADR-004 D1
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_PATHS = {".git", ".claude", "node_modules", ".env", ".venv"}


def is_tracked(path: str) -> bool:
    """Check if a file/dir is tracked by git."""
    result = subprocess.run(
        ["git", "ls-files", path],
        capture_output=True, text=True, cwd=ROOT
    )
    return bool(result.stdout.strip())


def is_dir_with_untracked(path: Path) -> bool:
    """Check if directory contains untracked files."""
    if not path.is_dir():
        return False
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", str(path)],
        capture_output=True, text=True, cwd=ROOT
    )
    return bool(result.stdout.strip())


def git_mv(old: str, new: str) -> bool:
    """Execute git mv, return True on success."""
    result = subprocess.run(
        ["git", "mv", old, new],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        return False
    return True


def safe_rename(old_path: Path, new_path: Path, old_rel: str, new_rel: str) -> str:
    """Rename a file or directory, handling tracked/untracked cases."""
    # Ensure parent directory exists
    new_path.parent.mkdir(parents=True, exist_ok=True)

    if old_path.is_file():
        if is_tracked(old_rel):
            if git_mv(old_rel, new_rel):
                return "git_mv"
            else:
                # Fallback: manual move + git add
                shutil.move(str(old_path), str(new_path))
                subprocess.run(["git", "add", new_rel], cwd=ROOT, capture_output=True)
                return "shutil+add"
        else:
            shutil.move(str(old_path), str(new_path))
            return "shutil"

    elif old_path.is_dir():
        if is_dir_with_untracked(old_path):
            # Mixed dir: copy, then git rm old, then git add new
            shutil.copytree(str(old_path), str(new_path), dirs_exist_ok=True)
            subprocess.run(["git", "rm", "-r", "--cached", old_rel],
                         capture_output=True, cwd=ROOT)
            shutil.rmtree(str(old_path))
            subprocess.run(["git", "add", new_rel], capture_output=True, cwd=ROOT)
            return "copytree"
        elif is_tracked(old_rel):
            if git_mv(old_rel, new_rel):
                return "git_mv"
            else:
                shutil.move(str(old_path), str(new_path))
                subprocess.run(["git", "add", new_rel], cwd=ROOT, capture_output=True)
                return "shutil+add"
        else:
            shutil.move(str(old_path), str(new_path))
            return "shutil"

    return "skip"


def should_skip(path: str) -> bool:
    """Check if path contains a skip directory."""
    parts = Path(path).parts
    return any(p in SKIP_PATHS for p in parts)


def apply_manifest(manifest_path: Path):
    """Apply all renames from the manifest."""
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        entries = json.load(f)

    total = len(entries)
    applied = 0
    skipped = 0
    missing = 0

    print(f"Applying {total} renames from {manifest_path.name}...")

    for i, entry in enumerate(entries):
        old_rel = entry["old_path"]
        new_rel = entry["new_path"]
        old_path = ROOT / old_rel
        new_path = ROOT / new_rel

        if should_skip(old_rel):
            skipped += 1
            continue

        if not old_path.exists():
            missing += 1
            continue

        if old_path == new_path or old_rel == new_rel:
            skipped += 1
            continue

        # Handle case-only renames on case-insensitive filesystems (macOS)
        # git mv handles this via two-step rename
        if old_rel.lower() == new_rel.lower() and old_rel != new_rel:
            # Case-only rename: use intermediate name
            tmp_rel = old_rel + ".tmp-rename"
            tmp_path = ROOT / tmp_rel
            if is_tracked(old_rel):
                subprocess.run(["git", "mv", old_rel, tmp_rel],
                             capture_output=True, cwd=ROOT)
                subprocess.run(["git", "mv", tmp_rel, new_rel],
                             capture_output=True, cwd=ROOT)
            else:
                shutil.move(str(old_path), str(tmp_path))
                shutil.move(str(tmp_path), str(new_path))
            applied += 1
            if (applied % 100) == 0:
                print(f"  Progress: {applied}/{total}...")
            continue

        method = safe_rename(old_path, new_path, old_rel, new_rel)
        if method != "skip":
            applied += 1
        else:
            skipped += 1

        if (applied % 100) == 0 and applied > 0:
            print(f"  Progress: {applied}/{total}...")

    print(f"\nCompleted: {applied} applied, {skipped} skipped, {missing} missing (already renamed)")


def apply_semantic_renames():
    """Apply semantic renames from semantic-renames.json."""
    semantic_path = ROOT / "semantic-renames.json"
    if not semantic_path.exists():
        # Create the default semantic renames
        renames = [
            {
                "old_path": "agents/system/pipeline-ops",
                "new_path": "agents/system/pipeline-ops"
            }
        ]
        with open(semantic_path, "w") as f:
            json.dump(renames, f, indent=2)
        print(f"Created {semantic_path} with {len(renames)} entries")

    with open(semantic_path) as f:
        entries = json.load(f)

    for entry in entries:
        old_rel = entry["old_path"]
        new_rel = entry["new_path"]
        old_path = ROOT / old_rel
        new_path = ROOT / new_rel

        if not old_path.exists():
            print(f"  SKIP (not found): {old_rel}")
            continue

        if new_path.exists():
            print(f"  SKIP (target exists): {new_rel}")
            continue

        print(f"  Renaming: {old_rel} -> {new_rel}")
        method = safe_rename(old_path, new_path, old_rel, new_rel)
        print(f"    Method: {method}")

    print("Semantic renames complete.")


def main():
    parser = argparse.ArgumentParser(description="Apply rename manifest")
    parser.add_argument("--manifest", default="rename-manifest.json",
                       help="Path to manifest JSON (default: rename-manifest.json)")
    parser.add_argument("--semantic", action="store_true",
                       help="Apply semantic renames only (pipeline-ops -> pipeline-ops)")
    args = parser.parse_args()

    if args.semantic:
        apply_semantic_renames()
    else:
        manifest_path = ROOT / args.manifest
        apply_manifest(manifest_path)


if __name__ == "__main__":
    main()
