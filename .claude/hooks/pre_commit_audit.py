#!/usr/bin/env python3
"""
Pre-Commit Layer Audit Hook — Mega Brain

Classifies staged files into layers (L1/L2/L3/NEVER) and:
- BLOCKS commits containing NEVER files or secrets (exit 1)
- WARNS on L3 leaks, stale templates
- INFO on .gitignore / package.json drift

Uses classify_path() from core/intelligence/validation/audit_layers.py.

Exit codes:
  0 = pass (clean or warnings-only)
  1 = block (NEVER files staged or secrets detected)

Bypass: MEGA_BRAIN_LAYER_PUSH=true (used by push.js temporary commits)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ── Resolve repo root ──────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent          # .claude/hooks/
REPO_ROOT = SCRIPT_DIR.parent.parent                   # mega-brain/

# ── Import classify_path from audit_layers ─────────────────────────────────

sys.path.insert(0, str(REPO_ROOT / "core" / "intelligence" / "validation"))
from audit_layers import classify_path  # noqa: E402

# ── ANSI colors ────────────────────────────────────────────────────────────

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
NC = "\033[0m"

# ── Secret patterns (fast subset — full set in pre-publish-gate.js) ────────

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9]{36}"),          # GitHub PAT
    re.compile(r"sk-ant-[A-Za-z0-9\-]{90,}"),    # Anthropic
    re.compile(r"sk-[A-Za-z0-9]{48}"),            # OpenAI
    re.compile(r"AKIA[0-9A-Z]{16}"),              # AWS
    re.compile(r"ntn_[A-Za-z0-9]{40,}"),          # Notion
]

# ── Template registry (personal file → template) ──────────────────────────

TEMPLATE_REGISTRY = {
    ".env": ".env.example",
    ".mcp.json": ".mcp.example.json",
    ".claude/settings.json": ".claude/settings.example.json",
}

# ── Binary extensions to skip during secret scanning ───────────────────────

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".7z",
    ".mp3", ".mp4", ".wav", ".webm", ".ogg",
    ".pyc", ".pyo", ".so", ".dylib", ".dll",
    ".sqlite", ".db",
}


# ── Helper functions ───────────────────────────────────────────────────────

def get_staged_files() -> list[str]:
    """Return list of staged file paths (excludes deletes)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            return []
        return [f for f in result.stdout.strip().split("\n") if f]
    except Exception:
        return []


def classify_staged(files: list[str]) -> dict[str, tuple[str, str]]:
    """Classify each staged file. Returns {filepath: (layer, reason)}."""
    result = {}
    for f in files:
        full_path = REPO_ROOT / f
        layer, reason = classify_path(full_path, REPO_ROOT, is_file=True)
        result[f] = (layer, reason)
    return result


def check_security(files: list[str], classifications: dict[str, tuple[str, str]]) -> list[str]:
    """
    BLOCK-level: check for NEVER files and secret patterns in staged content.
    Returns list of blocking issues.
    """
    issues = []

    # Check NEVER-layer files
    for f, (layer, reason) in classifications.items():
        if layer == "NEVER":
            issues.append(f"{RED}BLOCKED:{NC} {f} is NEVER-layer ({reason}). Remove: git reset HEAD -- {f}")

    # Scan staged file contents for secret patterns
    for f in files:
        full_path = REPO_ROOT / f
        ext = full_path.suffix.lower()
        if ext in BINARY_EXTENSIONS:
            continue
        if not full_path.exists():
            continue
        try:
            content = full_path.read_text(errors="ignore")
        except Exception:
            continue
        for pattern in SECRET_PATTERNS:
            match = pattern.search(content)
            if match:
                redacted = match.group()[:12] + "**REDACTED**"
                issues.append(f"{RED}BLOCKED:{NC} Secret in {f} → {redacted}")
                break  # one match per file is enough to block

    return issues


def check_layer_leaks(classifications: dict[str, tuple[str, str]]) -> list[str]:
    """WARN-level: L3 or DELETE files staged."""
    warnings = []
    for f, (layer, _reason) in classifications.items():
        if layer == "L3":
            warnings.append(f"{YELLOW}WARNING:{NC} L3 file staged: {f}")
        elif layer == "DELETE":
            warnings.append(f"{YELLOW}WARNING:{NC} DELETE-marked file staged: {f}")
    return warnings


def check_template_freshness(files: list[str]) -> list[str]:
    """WARN-level: personal file staged but template not updated alongside."""
    warnings = []
    staged_set = set(files)

    for personal, template in TEMPLATE_REGISTRY.items():
        if personal not in staged_set:
            continue
        # Personal file is staged — check if template is also staged
        if template not in staged_set:
            template_path = REPO_ROOT / template
            if template_path.exists():
                warnings.append(
                    f"{YELLOW}WARNING:{NC} {personal} modified but {template} not updated"
                )
    return warnings


def check_gitignore_drift(files: list[str], classifications: dict[str, tuple[str, str]]) -> list[str]:
    """INFO-level: staged files whose layer doesn't match .gitignore expectations."""
    infos = []

    gitignore_path = REPO_ROOT / ".gitignore"
    if not gitignore_path.exists():
        return infos

    for f, (layer, _reason) in classifications.items():
        # L3/NEVER file that somehow passes .gitignore = drift
        if layer in ("L3", "NEVER"):
            # These would already be caught by check_security / check_layer_leaks
            # This check is for when a file is classified L3 but .gitignore allows it
            if f in files:
                infos.append(
                    f"{CYAN}DRIFT:{NC} {f} classified {layer} but passes .gitignore — "
                    f"consider adding to .gitignore"
                )

    return infos


def check_package_json_drift(classifications: dict[str, tuple[str, str]]) -> list[str]:
    """INFO-level: L1 files not in package.json 'files', or non-L1 entries in 'files'."""
    infos = []

    pkg_path = REPO_ROOT / "package.json"
    if not pkg_path.exists():
        return infos

    try:
        pkg = json.loads(pkg_path.read_text())
    except Exception:
        return infos

    pkg_files = set(pkg.get("files", []))
    if not pkg_files:
        return infos

    # Files npm auto-includes regardless of "files" array
    npm_auto_included = {"package.json", "package-lock.json", "README.md", "LICENSE", "CHANGELOG.md"}

    # Check staged L1 files that aren't covered by any package.json entry
    for f, (layer, _reason) in classifications.items():
        if layer != "L1":
            continue
        if f in npm_auto_included:
            continue
        # Check if file or any parent directory is in package.json files
        covered = False
        for entry in pkg_files:
            entry_clean = entry.rstrip("/")
            if f == entry_clean or f.startswith(entry_clean + "/"):
                covered = True
                break
        if not covered:
            infos.append(f"{CYAN}DRIFT:{NC} {f} is L1 but not covered by package.json files[]")

    return infos


def format_report(
    files: list[str],
    classifications: dict[str, tuple[str, str]],
    blocks: list[str],
    warnings: list[str],
    infos: list[str],
) -> str:
    """Format the final report with ANSI colors."""
    lines = []

    # Layer summary
    layer_counts: dict[str, int] = {}
    for _f, (layer, _reason) in classifications.items():
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    summary_parts = [f"{layer}:{count}" for layer, count in sorted(layer_counts.items())]
    summary = " ".join(summary_parts)

    if blocks:
        status = f"{RED}{BOLD}BLOCKED{NC}"
    elif warnings:
        status = f"{YELLOW}WARNINGS{NC}"
    else:
        status = f"{GREEN}PASSED{NC}"

    lines.append(f"[pre-commit] {len(files)} files staged — {summary} — {status}")

    # Block-level issues
    for msg in blocks:
        lines.append(f"  {RED}\u2716{NC} {msg}")

    # Warnings
    for msg in warnings:
        lines.append(f"  {YELLOW}\u26a0{NC} {msg}")

    # Info/drift
    for msg in infos:
        lines.append(f"  {CYAN}\u2139{NC} {msg}")

    # Footer
    if blocks:
        lines.append("")
        lines.append(f"{RED}Commit blocked. Fix issues above.{NC}")
    elif warnings:
        lines.append("")
        lines.append("Commit proceeds with warnings.")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> int:
    # Bypass for push.js temporary commits
    if os.environ.get("MEGA_BRAIN_LAYER_PUSH") == "true":
        return 0

    files = get_staged_files()
    if not files:
        print(f"[pre-commit] No staged files — {GREEN}PASSED{NC}")
        return 0

    classifications = classify_staged(files)

    blocks = check_security(files, classifications)
    warnings = check_layer_leaks(classifications)
    warnings.extend(check_template_freshness(files))
    infos = check_gitignore_drift(files, classifications)
    infos.extend(check_package_json_drift(classifications))

    report = format_report(files, classifications, blocks, warnings, infos)
    print(report)

    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
