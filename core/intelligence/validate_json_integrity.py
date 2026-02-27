#!/usr/bin/env python3
"""
JSON Integrity Validator

Scans all .json files in the project (excluding node_modules, .git)
and validates they contain valid JSON.

Exit codes:
  0 = All JSON files are valid
  1 = One or more JSON files are invalid
"""

import json
import sys
from pathlib import Path

# Directories to exclude from scan
EXCLUDED_DIRS = {
    "node_modules",
    ".git",
    ".env",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}


def should_exclude(path: Path) -> bool:
    """Check if path should be excluded from scan."""
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def validate_json_file(file_path: Path) -> bool:
    """
    Validate a single JSON file.

    Returns:
        True if valid JSON, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"❌ FAIL: {file_path}")
        print(f"   JSON Error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: {file_path}")
        print(f"   Error: {e}")
        return False


def main():
    """Main validation function."""
    # Start from project root (resolve dynamically)
    project_root = Path(__file__).resolve().parents[2]

    # Collect all JSON files
    json_files = []
    for json_file in project_root.rglob("*.json"):
        if not should_exclude(json_file):
            json_files.append(json_file)

    if not json_files:
        print("⚠️  No JSON files found to validate")
        return 0

    print(f"📋 Validating {len(json_files)} JSON files...\n")

    passed = 0
    failed = 0

    for json_file in sorted(json_files):
        # Print relative path for readability
        rel_path = json_file.relative_to(project_root)

        if validate_json_file(json_file):
            print(f"✅ PASS: {rel_path}")
            passed += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Passed: {passed}/{len(json_files)}")
    print(f"❌ Failed: {failed}/{len(json_files)}")

    if failed == 0:
        print(f"\n🎉 All JSON files are valid!")
        return 0
    else:
        print(f"\n⚠️  {failed} JSON file(s) failed validation")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
