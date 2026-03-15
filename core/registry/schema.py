"""
Worker Registry Schema Validator v1.0

Validates worker-registry.yaml entries:
  - Required fields: id, type, path, status
  - type must be one of: pipeline, mce, rag, hook, agent, utility
  - path must exist on filesystem
  - routing_key (if set) must exist in ROUTING dict

Usage:
  python3 -m core.registry.schema           # validate all entries
  python3 -m core.registry.schema --discover # find unregistered workers

Epic 3.4 — Governance Engine
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT / "core" / "registry" / "worker-registry.yaml"

VALID_TYPES = {"pipeline", "mce", "rag", "hook", "agent", "utility"}
VALID_STATUSES = {"active", "deprecated", "experimental"}

# Directories to scan for unregistered workers
DISCOVERY_DIRS = {
    "pipeline": ROOT / "core" / "intelligence" / "pipeline",
    "mce": ROOT / "core" / "intelligence" / "pipeline" / "mce",
    "rag": ROOT / "core" / "intelligence" / "rag",
    "hook": ROOT / ".claude" / "hooks",
}


def load_registry() -> list[dict]:
    """Load worker registry YAML."""
    if not REGISTRY_PATH.exists():
        return []
    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f) or {}
    return data.get("workers", [])


def validate(workers: list[dict]) -> tuple[int, list[str]]:
    """Validate all worker entries. Returns (pass_count, error_list)."""
    errors = []
    passed = 0

    ids_seen = set()
    for i, w in enumerate(workers):
        prefix = f"Worker #{i+1}"

        # Required fields
        for field in ("id", "type", "path", "status"):
            if field not in w:
                errors.append(f"{prefix}: missing required field '{field}'")

        wid = w.get("id", f"unknown-{i}")
        prefix = f"[{wid}]"

        # Unique ID
        if wid in ids_seen:
            errors.append(f"{prefix}: duplicate id")
        ids_seen.add(wid)

        # Valid type
        wtype = w.get("type", "")
        if wtype not in VALID_TYPES:
            errors.append(f"{prefix}: invalid type '{wtype}' (valid: {VALID_TYPES})")

        # Valid status
        status = w.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"{prefix}: invalid status '{status}'")

        # Path exists
        wpath = w.get("path", "")
        if wpath and not (ROOT / wpath).exists():
            errors.append(f"{prefix}: path not found: {wpath}")

        # Routing key exists in ROUTING
        rkey = w.get("routing_key")
        if rkey:
            try:
                sys.path.insert(0, str(ROOT))
                from core.paths import ROUTING
                if rkey not in ROUTING:
                    errors.append(f"{prefix}: routing_key '{rkey}' not in ROUTING dict")
            except ImportError:
                pass

        if not any(wid in e for e in errors):
            passed += 1

    return passed, errors


def discover_unregistered(workers: list[dict]) -> list[str]:
    """Find .py files in known dirs that aren't registered."""
    registered_paths = {w.get("path", "") for w in workers}
    unregistered = []

    for _category, scan_dir in DISCOVERY_DIRS.items():
        if not scan_dir.exists():
            continue
        for py_file in sorted(scan_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            rel = str(py_file.relative_to(ROOT))
            if rel not in registered_paths:
                unregistered.append(rel)

    return unregistered


def main():
    workers = load_registry()

    if "--discover" in sys.argv:
        unregistered = discover_unregistered(workers)
        if unregistered:
            print(f"[Registry] {len(unregistered)} unregistered workers found:")
            for u in unregistered:
                print(f"  • {u}")
        else:
            print("[Registry] All workers in scanned dirs are registered.")
        return

    passed, errors = validate(workers)
    total = len(workers)

    if errors:
        print(f"[Registry] {passed}/{total} valid, {len(errors)} errors:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"[Registry] {passed}/{total} workers valid ✅")
        sys.exit(0)


if __name__ == "__main__":
    main()
