# ARCHIVED 2026-04-16 — W3-001.6
# Logic consolidated into .claude/hooks/governance_auto_update.py (v2.0.0)
# Not referenced in settings.json

#!/usr/bin/env python3
"""Governance Cascade Hook — PostToolUse (Write/Edit)

Detects when source code modules are modified and reports which
governance documents need propagation updates.

Strategy A: Static registry lookup (.claude/governance/cascade-registry.yaml)
Strategy B: Dynamic grep fallback for modules not in registry (auto-learns)

Output: JSON with "result" key containing governance propagation report.
Displayed in chat as a concise ESC-style log.

Hook contract:
  - Exit 0: success (always, this is advisory not blocking)
  - Output: JSON to stdout with governance cascade report
  - Timeout: 10s max (registry lookup is fast, grep fallback bounded)

Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / ".claude" / "governance" / "cascade-registry.yaml"
GOVERNANCE_DIRS = [
    "CLAUDE.md",
    ".claude/CLAUDE.md",
    "mega-brain-core/constitution.md",
    "docs/governance/rules/",
]

# Patterns that trigger governance cascade check
WATCHED_PATTERNS = [
    "engine/**/*.py",
    "agents/**/*.md",
    "workspace/**/*.yaml",
    ".claude/hooks/*.py",
    ".claude/skills/*/SKILL.md",
    "squads/*/config.yaml",
    "services/**/*.js",
    "mega-brain-core/constitution.md",
    "engine/paths.py",
]


# ---------------------------------------------------------------------------
# Registry loading (Strategy A)
# ---------------------------------------------------------------------------


def _load_registry() -> list[dict]:
    """Load cascade registry YAML. Falls back to empty if missing."""
    if not REGISTRY_PATH.exists():
        return []
    try:
        import yaml

        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("mappings", [])
    except Exception:
        return []


def _match_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file path matches a glob-like pattern."""
    # Normalize to relative path from project root
    try:
        rel = str(Path(file_path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        rel = file_path

    # fnmatch doesn't handle ** well, so we do a simple check
    if "**" in pattern:
        prefix = pattern.split("**")[0].rstrip("/")
        suffix = pattern.split("**")[-1].lstrip("/")
        return rel.startswith(prefix) and (not suffix or fnmatch(rel, f"*{suffix}"))
    return fnmatch(rel, pattern)


# ---------------------------------------------------------------------------
# Dynamic scan (Strategy B fallback)
# ---------------------------------------------------------------------------


def _grep_governance_docs(keywords: list[str]) -> list[dict]:
    """Grep governance docs for keyword references. Bounded to 5s."""
    hits = []
    for gov_path in GOVERNANCE_DIRS:
        full = PROJECT_ROOT / gov_path
        if not full.exists():
            continue

        files_to_scan = []
        if full.is_file():
            files_to_scan = [full]
        elif full.is_dir():
            files_to_scan = list(full.glob("*.md"))

        for f in files_to_scan:
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                for kw in keywords:
                    if re.search(kw, content, re.IGNORECASE):
                        rel = str(f.relative_to(PROJECT_ROOT))
                        hits.append(
                            {
                                "path": rel,
                                "matched_keyword": kw,
                                "source": "dynamic_scan",
                            }
                        )
                        break  # one hit per file is enough
            except OSError:
                continue
    return hits


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------


def check_cascade(modified_file: str) -> dict:
    """Check if a modified file triggers governance cascade needs.

    Returns dict with:
      - triggered: bool
      - file: str (the modified file)
      - governance_docs: list of docs that may need updating
      - propagation_score: str (X/Y format)
    """
    result = {
        "triggered": False,
        "file": modified_file,
        "governance_docs": [],
        "propagation_score": "N/A",
    }

    # Check if file matches any watched pattern
    is_watched = any(_match_pattern(modified_file, p) for p in WATCHED_PATTERNS)
    if not is_watched:
        return result

    result["triggered"] = True

    # Strategy A: registry lookup
    registry = _load_registry()
    docs_from_registry = []
    fallback_keywords = []

    for mapping in registry:
        pattern = mapping.get("source_pattern", "")
        if _match_pattern(modified_file, pattern):
            for doc in mapping.get("governance_docs", []):
                docs_from_registry.append(
                    {
                        "path": doc["path"],
                        "section": doc.get("section", ""),
                        "source": "registry",
                    }
                )
            fallback_keywords.extend(mapping.get("keywords", []))

    # Strategy B: dynamic grep fallback if registry found nothing
    docs_from_scan = []
    if not docs_from_registry and fallback_keywords:
        docs_from_scan = _grep_governance_docs(fallback_keywords)
    elif not docs_from_registry:
        # Extract keywords from filename
        stem = Path(modified_file).stem.replace("_", " ").replace("-", " ")
        words = [w for w in stem.split() if len(w) > 3]
        if words:
            docs_from_scan = _grep_governance_docs(words[:3])

    # Merge results (dedup by path)
    seen_paths = set()
    all_docs = []
    for d in docs_from_registry + docs_from_scan:
        if d["path"] not in seen_paths:
            seen_paths.add(d["path"])
            all_docs.append(d)

    result["governance_docs"] = all_docs
    total = len(all_docs)
    result["propagation_score"] = f"0/{total}" if total > 0 else "N/A"

    return result


# ---------------------------------------------------------------------------
# Hook entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """PostToolUse hook entry point. Reads tool input from stdin."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"result": "no input"}))
            sys.exit(0)

        event = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        print(json.dumps({"result": "parse error"}))
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Only trigger on Write or Edit
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"result": "not a write operation"}))
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({"result": "no file_path"}))
        sys.exit(0)

    cascade = check_cascade(file_path)

    if not cascade["triggered"]:
        print(json.dumps({"result": "no governance cascade needed"}))
        sys.exit(0)

    # Build human-readable report for chat display
    lines = [f"[GOVERNANCE] {Path(file_path).name} modified"]
    for doc in cascade["governance_docs"]:
        section = f" ({doc['section']})" if doc.get("section") else ""
        source_tag = " [scan]" if doc["source"] == "dynamic_scan" else ""
        lines.append(f"  -> {doc['path']}{section} — NEEDS REVIEW{source_tag}")

    lines.append(f"  Propagation needed: {cascade['propagation_score']}")

    report = "\n".join(lines)

    output = {
        "result": report,
        "cascade": cascade,
    }

    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
