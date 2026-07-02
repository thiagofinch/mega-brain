#!/usr/bin/env python3
"""
Hook: Validate workspace structure before commit/push
Blocks commits that violate workspace.yaml governance rules.

RULE ENFORCEMENT:
- Forbidden patterns → BLOCK commit
- Orphaned files → BLOCK commit
- Invalid naming → BLOCK commit
- Empty folders → WARN (non-blocking)

Installation:
  cp workspace/.claude/hooks/structure-validation.py .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit

Usage:
  Runs automatically on: git commit, git push
  Manual run: python workspace/.claude/hooks/structure-validation.py

Author: @architect (The Architect)
Date: 2026-02-14
"""

import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import yaml


class WorkspaceValidator:
    """Validate workspace structure against governance rules"""

    def __init__(self):
        self.workspace_root = self._find_workspace_root()
        self.config = self._load_config()
        self.errors = []
        self.warnings = []

    def _find_workspace_root(self) -> str:
        """Find workspace/ directory"""
        # Try current directory and parents
        current = Path(".")
        for _ in range(5):  # Check up to 5 levels up
            if (current / "workspace" / "workspace.yaml").exists():
                return str(current / "workspace")
            current = current.parent

        # Fallback
        return "workspace"

    def _load_config(self) -> dict:
        """Load workspace.yaml governance section"""
        config_path = Path(self.workspace_root) / "workspace.yaml"

        if not config_path.exists():
            self.errors.append(f"❌ workspace.yaml not found at {config_path}")
            return {}

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
                return data.get("governance", {})
        except Exception as e:
            self.errors.append(f"❌ Error loading workspace.yaml: {e}")
            return {}

    def validate(self) -> bool:
        """Run all validations. Return True if all pass."""
        if not self.config:
            print("⚠️  Could not load governance config. Skipping validation.")
            return True

        print("🔍 Validating workspace structure...")

        self._validate_required_folders()
        self._validate_required_files()
        self._validate_forbidden_patterns()
        self._validate_naming_rules()
        self._validate_orphaned_files()
        self._validate_empty_folders()
        self._validate_people_registry_path()
        self._check_ecosystem_drift()

        # Report results
        if self.errors:
            self._print_errors()
            return False

        if self.warnings:
            self._print_warnings()

        print("✅ Workspace structure validation passed")
        return True

    def _validate_required_folders(self):
        """Check all required folders exist"""
        required = self.config.get("structure", {}).get("required_folders", [])

        for folder_spec in required:
            path = os.path.join(self.workspace_root, folder_spec["path"])
            if not os.path.isdir(path):
                self.errors.append(
                    f"❌ Required folder missing: {folder_spec['path']}\n"
                    f"   Owner: {folder_spec.get('owner', 'unknown')}"
                )

    def _validate_required_files(self):
        """Check all required files exist"""
        required = self.config.get("structure", {}).get("required_folders", [])

        for folder_spec in required:
            # Skip product folders (they're dynamic)
            if "structure" in folder_spec:
                continue

            for file in folder_spec.get("required_files", []):
                file_path = os.path.join(self.workspace_root, folder_spec["path"], file)
                if not os.path.isfile(file_path):
                    self.errors.append(
                        f"❌ Required file missing: {folder_spec['path']}{file}\n"
                        f"   Guardian: {folder_spec.get('owner', 'unknown')}"
                    )

    def _validate_forbidden_patterns(self):
        """Block forbidden file/folder names"""
        forbidden = self.config.get("structure", {}).get("forbidden_patterns", [])

        if not forbidden:
            return

        for root, dirs, files in os.walk(self.workspace_root):
            # Skip .git and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            # Check files
            for file in files:
                if self._matches_any_pattern(file, forbidden):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.workspace_root)
                    self.errors.append(
                        f"❌ Forbidden file pattern: {rel_path}\n"
                        f"   Blocked patterns: {', '.join(forbidden)}"
                    )

            # Check directories
            for dir in dirs:
                if self._matches_any_pattern(dir, forbidden):
                    full_path = os.path.join(root, dir)
                    rel_path = os.path.relpath(full_path, self.workspace_root)
                    self.errors.append(
                        f"❌ Forbidden folder pattern: {rel_path}\n"
                        f"   Use git branches or tags instead of versioning in filenames"
                    )

    def _validate_naming_rules(self):
        """Validate product names are snake_case"""
        naming = self.config.get("structure", {}).get("naming_rules", {})
        products_pattern = naming.get("products", {}).get("pattern")

        if not products_pattern:
            return

        products_path = os.path.join(self.workspace_root, "products")

        if os.path.isdir(products_path):
            for product_dir in os.listdir(products_path):
                product_full = os.path.join(products_path, product_dir)
                if os.path.isdir(product_full) and not product_dir.startswith("."):
                    if not re.match(products_pattern, product_dir):
                        self.errors.append(
                            f"❌ Product name not snake_case: {product_dir}\n"
                            f"   Use: product_name (lowercase, underscores only)\n"
                            f"   Pattern: {products_pattern}"
                        )

    def _validate_orphaned_files(self):
        """Check for files in workspace root"""
        allowed_root_files = {
            "workspace.yaml",
            "README.md",
            "STRUCTURE.md",
            ".gitkeep",
            ".gitignore",
            "config.md",
            "structure.yaml",
            "relationships.yaml",
            "synapse-integration.yaml",
            "index.json",
            "user.md",
            "validate-structure.sh",
            "PRODUCT_OFFERBOOK_SYSTEM.md",
        }

        root_files = [
            f
            for f in os.listdir(self.workspace_root)
            if os.path.isfile(os.path.join(self.workspace_root, f))
            and not f.startswith(".")
            and f not in allowed_root_files
        ]

        if root_files:
            self.errors.append(
                f"❌ Orphaned files in workspace root:\n"
                f"   {', '.join(root_files)}\n"
                f"   Move these to appropriate folders (company/, tech/, ai/, products/)"
            )

    def _validate_empty_folders(self):
        """Check for empty folders (unless .gitkeep exists)"""
        for root, dirs, files in os.walk(self.workspace_root):
            # Skip .git
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            if len(files) == 0 and root != self.workspace_root:
                # Check for .gitkeep (intentional empty folder)
                gitkeep_path = os.path.join(root, ".gitkeep")
                if not os.path.exists(gitkeep_path):
                    rel_path = os.path.relpath(root, self.workspace_root)
                    self.warnings.append(f"⚠️  Empty folder (add .gitkeep or delete): {rel_path}")

    def _validate_people_registry_path(self):
        """Validate people-registry.yaml lives at L0-identity for L0-L4 BUs.
        ADR-WI-001: people-registry is identity data (TTL 365d), not strategy."""
        businesses_dir = Path(self.workspace_root) / "businesses"
        if not businesses_dir.exists():
            return

        for bu_dir in sorted(businesses_dir.iterdir()):
            if not bu_dir.is_dir() or bu_dir.name.startswith("."):
                continue

            l0_dir = bu_dir / "l0-identity"
            if not l0_dir.exists():
                continue  # Skip 12-folder BUs (no L0-L4 hierarchy)

            # Check for stale location
            stale_path = bu_dir / "l1-strategy" / "people-registry.yaml"
            if stale_path.exists():
                self.warnings.append(
                    f"⚠️  Stale people-registry at L1: {bu_dir.name}/l1-strategy/people-registry.yaml\n"
                    f"     Should be at l0-identity/ per ADR-WI-001. Move with: git mv"
                )

            # Check canonical location exists
            canonical_path = l0_dir / "people-registry.yaml"
            if not canonical_path.exists():
                self.warnings.append(
                    f"⚠️  Missing people-registry: {bu_dir.name}/l0-identity/people-registry.yaml\n"
                    f"     Run scaffold or create PLACEHOLDER per WI-T-020-MB"
                )

    def _check_ecosystem_drift(self):
        """Advisory check: detect squads on filesystem not in ecosystem-registry.
        NEVER blocks — only warns. Runs in <1 second."""
        try:
            # Find project root (parent of workspace/)
            project_root = Path(self.workspace_root).parent
            squads_dir = project_root / "squads"
            registry_path = squads_dir / "mega-brain" / "data" / "ecosystem-registry.yaml"

            if not squads_dir.exists() or not registry_path.exists():
                return

            # Get filesystem squad names
            fs_squads = set()
            for entry in squads_dir.iterdir():
                if entry.is_dir() and not entry.name.startswith("."):
                    if (entry / "config.yaml").exists():
                        fs_squads.add(entry.name)

            # Get registered squad names
            with open(registry_path) as f:
                registry = yaml.safe_load(f)
            registered = set()
            for squad in (registry or {}).get("squads", []):
                if isinstance(squad, dict) and "name" in squad:
                    registered.add(squad["name"])

            # Detect drift
            new_squads = fs_squads - registered
            removed_squads = registered - fs_squads

            if new_squads:
                self.warnings.append(
                    f"⚠️  Ecosystem drift: {len(new_squads)} unregistered squad(s): "
                    f"{', '.join(sorted(new_squads))}. Run *sync-ecosystem"
                )
            if removed_squads:
                self.warnings.append(
                    f"⚠️  Ecosystem drift: {len(removed_squads)} registered but missing squad(s): "
                    f"{', '.join(sorted(removed_squads))}. Run *sync-ecosystem"
                )
        except Exception:
            pass  # Advisory only — never fail on drift check errors

    def _matches_any_pattern(self, name: str, patterns: list[str]) -> bool:
        """Check if name matches any pattern (fnmatch)"""
        return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)

    def _print_errors(self):
        """Print errors and block commit"""
        print("\n" + "=" * 70)
        print("❌ WORKSPACE STRUCTURE VALIDATION FAILED")
        print("=" * 70)
        print("\nFix the errors below before committing:\n")

        for i, error in enumerate(self.errors, 1):
            print(f"{i}. {error}\n")

        print("=" * 70)
        print("For help, see: workspace/STRUCTURE.md")
        print("=" * 70)

    def _print_warnings(self):
        """Print warnings (non-blocking)"""
        if not self.warnings:
            return

        print("\n⚠️  Warnings (non-blocking):")
        for warning in self.warnings:
            print(f"  {warning}")


def main():
    """Main entry point. Exit codes: 0=pass, 1=warnings, 2=errors (Anthropic standard)."""
    validator = WorkspaceValidator()

    if not validator.validate():
        sys.exit(2)  # Errors found — block

    if validator.warnings:
        sys.exit(1)  # Warnings only — notify but don't block

    sys.exit(0)


if __name__ == "__main__":
    main()
