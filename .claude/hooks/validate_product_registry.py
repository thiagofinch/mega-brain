#!/usr/bin/env python3
"""
validate_product_registry.py — PreToolUse hook
Validates product registry and L3-product writes against governance rules.

Triggered on: Write/Edit to files matching */L3-product/* or */product-registry.yaml
Exit codes: 0=pass, 1=warn, 2=block

Rules enforced:
1. Checkout platforms (checkout-platform, hotmart, eduzz) forbidden as business_unit for non-SaaS
2. stage must be valid enum
3. first-idea requires source_evidence
4. official:true threshold enforcement
5. Product Profile Mirror: offerbook.yaml + PROFILE.md pair
"""

import json
import os
import sys
from pathlib import Path

# Read hook input from stdin
try:
    hook_input = json.loads(sys.stdin.read())
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

tool_name = hook_input.get("tool_name", "")
tool_input = hook_input.get("tool_input", {})

# Only trigger on Write/Edit to L3-product paths or product-registry.yaml
file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
if not file_path:
    sys.exit(0)

if "L3-product" not in file_path and "product-registry" not in file_path:
    sys.exit(0)

# Constants
CHECKOUT_PLATFORMS = ["checkout-platform", "hotmart", "eduzz", "kiwify", "monetizze"]
VALID_STAGES = ["launched", "validation", "designing", "first-idea"]
VALID_PRODUCT_TYPES = [
    "course",
    "saas",
    "service",
    "marketplace",
    "community",
    "mentorship",
    "portfolio",
]
VALID_BUS = [
    "acme",
]

warnings = []
blockers = []


def validate_yaml_content(content):
    """Validate product registry YAML content for governance violations."""
    try:
        import yaml

        data = yaml.safe_load(content)
    except Exception:
        return

    if not isinstance(data, dict):
        return

    # Collect all product entries from any section
    products = []
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "slug" in item:
                    products.append(item)

    for product in products:
        slug = product.get("slug", "unknown")
        bu = product.get("business_unit", "")
        stage = product.get("stage", "")
        ptype = product.get("product_type", "")
        official = product.get("official", False)
        source = product.get("source_evidence")
        validated_by = product.get("validated_by")

        # Rule 1: Checkout platforms cannot be business_unit (except for SaaS products)
        if bu in CHECKOUT_PLATFORMS and ptype != "saas":
            blockers.append(
                f"BLOCKER: '{slug}' has business_unit='{bu}' which is a checkout platform, "
                f"not a revenue owner. Use the actual BU that owns the revenue."
            )

        # Rule 2: Stage must be valid
        if stage and stage not in VALID_STAGES:
            warnings.append(
                f"HIGH: '{slug}' has invalid stage='{stage}'. Valid: {', '.join(VALID_STAGES)}"
            )

        # Rule 3: first-idea requires source_evidence
        if stage == "first-idea" and not source:
            warnings.append(
                f"HIGH: '{slug}' is stage='first-idea' but has no source_evidence. "
                f"Rule: first-idea must specify source call ID or document."
            )

        # Rule 4: official:true threshold
        if official:
            if stage == "first-idea":
                warnings.append(
                    f"MEDIUM: '{slug}' is official=true but stage='first-idea'. "
                    f"Official products must have stage != first-idea."
                )
            if not source:
                warnings.append(f"MEDIUM: '{slug}' is official=true but has no source_evidence.")
            if not validated_by:
                warnings.append(f"MEDIUM: '{slug}' is official=true but has no validated_by.")


# If writing to product-registry.yaml, validate its content
if "product-registry" in file_path and tool_name in ("Write", "Edit"):
    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    if content:
        validate_yaml_content(content)

# If writing to L3-product, check Profile Mirror rule
if "L3-product" in file_path and tool_name == "Write":
    p = Path(file_path)
    product_dir = p.parent
    if product_dir.name != "L3-product" and product_dir.name != ".staging":
        offerbook = product_dir / "offerbook.yaml"
        profile = product_dir / "PROFILE.md"

        if p.name == "offerbook.yaml" and not profile.exists():
            warnings.append(
                f"MEDIUM: Writing offerbook.yaml to '{product_dir.name}/' but PROFILE.md "
                f"does not exist. Product Profile Mirror rule requires both."
            )
        elif p.name == "PROFILE.md" and not offerbook.exists():
            warnings.append(
                f"MEDIUM: Writing PROFILE.md to '{product_dir.name}/' but offerbook.yaml "
                f"does not exist. Product Profile Mirror rule requires both."
            )

# Output results
if blockers:
    output = {"blockers": blockers, "warnings": warnings}
    print(json.dumps(output))
    sys.exit(2)
elif warnings:
    output = {"warnings": warnings}
    print(json.dumps(output))
    sys.exit(1)
else:
    sys.exit(0)
