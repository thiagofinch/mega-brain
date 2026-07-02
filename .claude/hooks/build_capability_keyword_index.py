#!/usr/bin/env python3
"""
build_capability_keyword_index.py -- Build keyword index for intent detection

Generates agents/_registry/capability-keyword-index.json with:
- entries: list of {keyword, capability_id, priority}
- resolvedCapabilities: dict of pre-resolved capability results

Keywords are pre-normalized: lowercase, no accents (via unicodedata).

Part of the Tool Intelligence Layer (MegaBrain Python-first architecture).
"""

import json
import os
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required.", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
INDEX_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-keyword-index.json"


def normalize_keyword(kw: str) -> str:
    """Lowercase and strip accents."""
    kw = kw.lower().strip()
    # NFD decomposition, strip combining chars
    nfkd = unicodedata.normalize("NFKD", kw)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def main():
    try:
        raw = REGISTRY_PATH.read_text(encoding="utf-8")
        registry = yaml.safe_load(raw)
    except FileNotFoundError:
        print(f"Error: Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: YAML parse failed: {e}", file=sys.stderr)
        sys.exit(1)

    capabilities = registry.get("capabilities", {})
    if not capabilities:
        print("Warning: No capabilities found in registry.", file=sys.stderr)
        sys.exit(0)

    # Import resolver for pre-calculation
    resolved_caps = {}
    try:
        sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "hooks"))
        from capability_resolver import clear_cache, resolve

        clear_cache()
        for cap_id in capabilities:
            resolved_caps[cap_id] = resolve(cap_id)
    except Exception as e:
        print(f"Warning: Could not pre-resolve capabilities: {e}", file=sys.stderr)

    # Build entries
    entries = []
    for cap_id, cap in capabilities.items():
        keywords = cap.get("keywords", [])
        if not keywords:
            continue
        # Priority from first provider
        providers = cap.get("providers", [])
        priority = providers[0].get("priority", 99) if providers else 99

        for kw in keywords:
            normalized = normalize_keyword(kw)
            if normalized:
                entries.append(
                    {
                        "keyword": normalized,
                        "capability_id": cap_id,
                        "priority": priority,
                    }
                )

    index = {
        "version": "1.0.0",
        "generated_by": "build_capability_keyword_index.py",
        "entries_count": len(entries),
        "capabilities_count": len(capabilities),
        "entries": entries,
        "resolvedCapabilities": resolved_caps,
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"Keyword index built: {len(entries)} entries, {len(capabilities)} capabilities")
    print(f"Written to: {INDEX_PATH}")
    sys.exit(0)


if __name__ == "__main__":
    main()
