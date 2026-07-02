#!/usr/bin/env python3

"""
product-completeness.py - Pre-commit hook for product offerbook tracking

Purpose:
  Tracks product completeness and shows progress (NEVER blocks commits)
  Follows the process-architect principle: "Process can be gradual, but always visible"

Behavior:
  ⏳ < 100%: Show progress, record in manifest, allow commit
  ✅ 100%: Show completion, record in manifest, allow commit

  NEVER blocks - processes need flexibility to evolve

Usage (auto-installed in git hooks):
  git commit -m "my changes"
  -> Hook runs automatically
  -> Shows completeness % for each product
  -> Records progress in workspace/products/.completeness-manifest
  -> Allows commit (no blocking ever)

Exit Codes:
  0 = Always (hook NEVER blocks)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
GRAY = "\033[0;37m"
NC = "\033[0m"


class ProductProgressTracker:
    def __init__(self, workspace_root):
        self.workspace_root = workspace_root
        self.products_dir = os.path.join(workspace_root, "products")
        self.manifest_file = os.path.join(self.products_dir, ".completeness-manifest.json")
        self.manifest = self.load_manifest()

    def load_manifest(self):
        """Load or create completeness manifest"""
        if os.path.exists(self.manifest_file):
            try:
                with open(self.manifest_file) as f:
                    return json.load(f)
            except:
                return {"products": {}, "history": []}
        return {"products": {}, "history": []}

    def save_manifest(self):
        """Save completeness manifest"""
        try:
            with open(self.manifest_file, "w") as f:
                json.dump(self.manifest, f, indent=2)
        except Exception:
            pass

    def count_yaml_status_fields(self, filepath):
        """Count COMPLETE vs INCOMPLETE status fields"""
        try:
            with open(filepath) as f:
                content = f.read()
            complete = len(re.findall(r'status:\s*"?COMPLETE"?', content))
            incomplete = len(re.findall(r'status:\s*"?INCOMPLETE"?', content))
            return complete, incomplete
        except:
            return 0, 0

    def get_yaml_declared_fields(self, filepath):
        """Read declared required/completed fields from metadata when available."""
        try:
            with open(filepath) as f:
                content = f.read()
            required_match = re.search(r"^\s*required_fields:\s*(\d+)\s*$", content, re.MULTILINE)
            completed_match = re.search(r"^\s*completed_fields:\s*(\d+)\s*$", content, re.MULTILINE)
            if required_match and completed_match:
                required = int(required_match.group(1))
                completed = int(completed_match.group(1))
                if completed > required:
                    completed = required
                return required, completed
            return None, None
        except:
            return None, None

    def validate_product_files(self, product_path, product_name):
        """Validate all required files in a product"""
        required_files = {
            "icp.yaml": 47,
            "brand.yaml": 42,
            "offerbook.yaml": None,
            "analytics.yaml": None,
            "overview.md": None,
        }

        total_required = 0
        total_complete = 0
        missing_files = []
        issues = {}

        for filename, expected_fields in required_files.items():
            filepath = os.path.join(product_path, filename)

            if not os.path.exists(filepath):
                missing_files.append(filename)
                continue

            if expected_fields is None:
                continue

            declared_required, declared_completed = self.get_yaml_declared_fields(filepath)
            if declared_required is not None and declared_completed is not None:
                total = declared_required
                complete = declared_completed
            else:
                complete, _incomplete = self.count_yaml_status_fields(filepath)
                total = expected_fields

            total_required += total
            total_complete += complete

            if complete < total:
                missing = total - complete
                issues[filename] = {"complete": complete, "total": total, "missing": missing}

        # Calculate percentage
        if total_required > 0:
            percentage = (total_complete * 100) // total_required
        else:
            percentage = 0

        return {
            "product": product_name,
            "percentage": percentage,
            "complete_fields": total_complete,
            "total_fields": total_required,
            "missing_files": missing_files,
            "file_issues": issues,
            "timestamp": datetime.now().isoformat(),
        }

    def track_all_products(self):
        """Track all products and update manifest"""
        if not os.path.isdir(self.products_dir):
            return []

        product_dirs = [
            d
            for d in os.listdir(self.products_dir)
            if os.path.isdir(os.path.join(self.products_dir, d))
            and not d.startswith("_")
            and not d.startswith(".")
        ]

        results = []
        for product_name in sorted(product_dirs):
            product_path = os.path.join(self.products_dir, product_name)
            result = self.validate_product_files(product_path, product_name)
            results.append(result)

            # Update manifest
            self.manifest["products"][product_name] = {
                "percentage": result["percentage"],
                "last_updated": result["timestamp"],
                "status": "COMPLETE" if result["percentage"] == 100 else "IN_PROGRESS",
                "fields": {"complete": result["complete_fields"], "total": result["total_fields"]},
            }

            # Add to history
            self.manifest["history"].append(
                {
                    "product": product_name,
                    "percentage": result["percentage"],
                    "timestamp": result["timestamp"],
                    "action": "commit",
                }
            )

        # Keep only last 100 history entries
        if len(self.manifest["history"]) > 100:
            self.manifest["history"] = self.manifest["history"][-100:]

        self.save_manifest()
        return results

    def print_progress_bar(self, percentage):
        """Draw visual progress bar"""
        filled = percentage // 10
        empty = 10 - filled

        if percentage == 100:
            color = GREEN
        elif percentage >= 75:
            color = YELLOW
        else:
            color = RED

        bar = f"{color}[{'█' * filled}{'░' * empty}]{NC} {percentage}%"
        return bar

    def report(self, results):
        """Print formatted progress report"""
        print("")
        print(f"{BLUE}╔════════════════════════════════════════╗{NC}")
        print(f"{BLUE}║  Product Completeness Progress Report  ║{NC}")
        print(f"{BLUE}╚════════════════════════════════════════╝{NC}")
        print("")

        if not results:
            return

        for result in results:
            product = result["product"]
            percentage = result["percentage"]
            complete = result["complete_fields"]
            total = result["total_fields"]
            status = "✅" if percentage == 100 else "⏳"

            bar = self.print_progress_bar(percentage)
            print(f"{status} {product:30} {bar}  {complete}/{total}")

            # Show what's missing (if < 100%)
            if percentage < 100:
                if result["missing_files"]:
                    files = ", ".join(result["missing_files"])
                    print(f"   {GRAY}Missing files: {files}{NC}")

                if result["file_issues"]:
                    for filename, issue in result["file_issues"].items():
                        remaining = issue["total"] - issue["complete"]
                        print(f"   {GRAY}{filename}: +{remaining} fields to fill{NC}")

        print("")

        # Summary
        complete_count = sum(1 for r in results if r["percentage"] == 100)
        total_count = len(results)
        avg_percentage = sum(r["percentage"] for r in results) // total_count if results else 0

        print(f"{BLUE}Summary:{NC}")
        print(f"  Complete: {GREEN}{complete_count}/{total_count}{NC}")
        print(f"  Average:  {self.print_progress_bar(avg_percentage)}")
        print("")

        if complete_count == total_count:
            print(f"{GREEN}🎉 All products are 100% complete!{NC}")
        else:
            remaining = total_count - complete_count
            print(f"{YELLOW}⏳ {remaining} product(s) in progress{NC}")
            print(f"{GRAY}Continue filling fields at your own pace — no blocking{NC}")

        print("")


def main():
    hook_dir = Path(__file__).resolve().parent
    repo_root = hook_dir.parent.parent
    workspace_root = repo_root / "workspace"
    if not workspace_root.exists():
        workspace_root = repo_root

    tracker = ProductProgressTracker(str(workspace_root))
    results = tracker.track_all_products()
    tracker.report(results)

    # ALWAYS return 0 - NEVER block commits
    sys.exit(0)


if __name__ == "__main__":
    main()
