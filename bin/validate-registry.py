#!/usr/bin/env python3
"""Validates ecosystem-registry.yaml against the filesystem.

Checks:
  - Each agent path exists on disk (file or directory)
  - profile path exists if not null
  - id matches kebab-case regex
  - category is in the canonical category set
  - status is a valid enum value

Exit 0 if all checks pass, exit 1 with errors listed.
"""

import re
import sys
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Resolve repo root (two levels up from bin/)
REPO_ROOT = Path(__file__).parent.parent.resolve()
REGISTRY_PATH = REPO_ROOT / "agents" / "_registry" / "ecosystem-registry.yaml"

VALID_STATUSES = {"active", "deprecated", "archived"}

CANONICAL_CATEGORIES = {
    "system/pipeline-ops",
    "system/conclave",
    "system/dev-ops",
    "system/boardroom",
    "external/minds",
    "business/collaborators",
    "business/partners",
    "business/advisors",
    "business/alumni",
    "personal",
    "constitution",
}
# external/cargo/{dept} categories are validated by prefix
CARGO_PREFIX = "external/cargo/"

KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_canonical_category(category: str) -> bool:
    if category in CANONICAL_CATEGORIES:
        return True
    if category.startswith(CARGO_PREFIX):
        dept = category[len(CARGO_PREFIX):]
        # dept must be non-empty and kebab-case
        return bool(dept) and bool(KEBAB_CASE_RE.match(dept))
    return False


def validate_registry(registry_path: Path, repo_root: Path) -> list[str]:
    errors = []

    with open(registry_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        return ["Registry root is not a YAML mapping."]

    # Validate top-level registry block
    reg = data.get("registry", {})
    for field in ("version", "last_updated", "generator", "schema_version"):
        if not reg.get(field):
            errors.append(f"registry.{field} is missing or empty.")

    agents = data.get("agents")
    if not isinstance(agents, list):
        errors.append("Top-level 'agents' key is missing or not a list.")
        return errors

    seen_ids = {}
    for i, entry in enumerate(agents):
        label = f"agents[{i}] (id={entry.get('id', '<missing>')})"

        # Required fields present
        for field in ("id", "category", "path", "profile", "status", "capabilities", "tags"):
            if field not in entry:
                errors.append(f"{label}: missing required field '{field}'.")

        agent_id = entry.get("id", "")
        category = entry.get("category", "")
        path_val = entry.get("path", "")
        profile_val = entry.get("profile")
        status = entry.get("status", "")
        capabilities = entry.get("capabilities")
        tags = entry.get("tags")

        # id — kebab-case
        if agent_id:
            if not KEBAB_CASE_RE.match(agent_id):
                errors.append(f"{label}: id '{agent_id}' is not kebab-case.")
            # duplicate check
            if agent_id in seen_ids:
                errors.append(f"{label}: duplicate id '{agent_id}' (first at index {seen_ids[agent_id]}).")
            seen_ids[agent_id] = i

        # category — canonical set
        if category and not is_canonical_category(category):
            errors.append(f"{label}: category '{category}' is not in the canonical set.")

        # status — valid enum
        if status and status not in VALID_STATUSES:
            errors.append(f"{label}: status '{status}' is not valid (must be one of {sorted(VALID_STATUSES)}).")

        # path — must exist on disk (file or directory)
        if path_val:
            abs_path = repo_root / path_val
            if not abs_path.exists():
                errors.append(f"{label}: path '{path_val}' does not exist on disk.")

        # profile — if not null, must exist on disk
        if profile_val is not None:
            abs_profile = repo_root / profile_val
            if not abs_profile.exists():
                errors.append(f"{label}: profile '{profile_val}' does not exist on disk.")

        # capabilities and tags — must be lists
        if capabilities is not None and not isinstance(capabilities, list):
            errors.append(f"{label}: 'capabilities' must be a list.")
        if tags is not None and not isinstance(tags, list):
            errors.append(f"{label}: 'tags' must be a list.")

    return errors


def main() -> int:
    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found at {REGISTRY_PATH}", file=sys.stderr)
        return 1

    errors = validate_registry(REGISTRY_PATH, REPO_ROOT)

    if errors:
        print(f"FAIL — {len(errors)} error(s) found in {REGISTRY_PATH.relative_to(REPO_ROOT)}:")
        for err in errors:
            print(f"  • {err}")
        return 1

    print(f"OK — ecosystem-registry.yaml is valid ({REGISTRY_PATH.relative_to(REPO_ROOT)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
