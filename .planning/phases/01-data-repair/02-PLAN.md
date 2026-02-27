---
wave: 1
depends_on: []
files_modified:
  - scripts/validate_json_integrity.py
requirements:
  - DATA-02
---

# Plan: JSON Validation Script

## Purpose

Create a script to validate all JSON files in the project, reporting any parse errors.

## Implementation

Create `scripts/validate_json_integrity.py`:

```python
#!/usr/bin/env python3
"""Validate JSON integrity across the project."""

import json
import sys
from pathlib import Path

def validate_json_files(root: Path) -> dict:
    results = {"valid": [], "invalid": [], "skipped": []}

    for json_file in root.rglob("*.json"):
        # Skip node_modules, .git, etc.
        if any(p in json_file.parts for p in ["node_modules", ".git", "vendor"]):
            results["skipped"].append(str(json_file))
            continue

        try:
            json.loads(json_file.read_text())
            results["valid"].append(str(json_file))
        except json.JSONDecodeError as e:
            results["invalid"].append({"file": str(json_file), "error": str(e)})

    return results

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    results = validate_json_files(root)

    print(f"Valid: {len(results['valid'])}")
    print(f"Invalid: {len(results['invalid'])}")

    for item in results["invalid"]:
        print(f"  ERROR: {item['file']}")
        print(f"         {item['error']}")

    sys.exit(1 if results["invalid"] else 0)
```

## Verification

```bash
python3 scripts/validate_json_integrity.py .
# Exit code 0 = all valid
```

## Usage

Run after any batch processing or state updates to ensure integrity.
