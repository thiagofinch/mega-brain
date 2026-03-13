#!/usr/bin/env python3
"""
Sync package.json files field with L1 audit classifications.

Reads audit_layers.py classifications, computes optimal files array,
and can apply it to package.json.

Usage:
    python3 core/intelligence/sync_package_files.py --print      # JSON to stdout
    python3 core/intelligence/sync_package_files.py --apply       # Update package.json
    python3 core/intelligence/sync_package_files.py --diff        # Show changes
    python3 core/intelligence/sync_package_files.py --npmignore   # Print .npmignore
    python3 core/intelligence/sync_package_files.py --npmignore --apply  # Write .npmignore
    python3 core/intelligence/sync_package_files.py --allowlist   # Print allowlist
    python3 core/intelligence/sync_package_files.py --allowlist --apply  # Write allowlist
"""
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from audit_layers import scan_repository, classify_path, L2_PATTERNS, L3_PATTERNS, NEVER_PATTERNS

# Files auto-included by npm (do NOT add to files array)
NPM_AUTO_INCLUDED = {
    'package.json',
    'README.md',
    'README',
    'CHANGELOG.md',
    'CHANGELOG',
    'LICENSE',
    'LICENSE.md',
    'LICENCE',
    'LICENCE.md',
}

# L1 paths to EXCLUDE from npm package
# (development-only content that shouldn't ship to consumers)
EXCLUDE_FROM_PACKAGE = {
    '.planning',       # GSD planning system (dev-only)
    'docs/audit',      # Generated audit reports (dev-only)
    '.npmignore',      # npm uses it but doesn't pack it
    'package-lock.json',  # npm excludes this from pack
}


def _is_excluded(rel_path: str) -> bool:
    """Check if a path should be excluded from the package."""
    # Check exact match for root files
    if rel_path in EXCLUDE_FROM_PACKAGE:
        return True
    # Check directory prefix match
    for excl in EXCLUDE_FROM_PACKAGE:
        if rel_path.startswith(excl + '/'):
            return True
    return False


def compute_files_array(repo_root: Path) -> list:
    """
    Compute the optimal package.json files array from L1 audit.

    Algorithm:
    1. Get all L1-classified files from audit
    2. Remove npm auto-included files and excluded paths
    3. Group files by directory
    4. For each directory, check if ALL files in that dir (across ALL layers) are L1
    5. If pure L1 dir: use directory glob
    6. If mixed: recurse into subdirectories or list individual files
    7. Deduplicate and sort
    """
    data = scan_repository(repo_root)

    # Build map of ALL file classifications by directory
    all_files_by_dir = defaultdict(list)  # dir -> [(rel_path, layer)]
    l1_files = set()

    for item in data['classifications']:
        if item['type'] != 'file':
            continue
        rel = item['path']
        layer = item['layer']

        # Skip npm auto-included root files
        if rel in NPM_AUTO_INCLUDED:
            continue
        # Skip excluded paths
        if _is_excluded(rel):
            continue

        parts = rel.split('/')
        if len(parts) == 1:
            dir_key = '.'
        else:
            dir_key = '/'.join(parts[:-1])

        all_files_by_dir[dir_key].append((rel, layer))

        if layer == 'L1':
            l1_files.add(rel)

    if not l1_files:
        return []

    # Build set of all directories and their purity status
    # A directory is "pure L1" if ALL files within it (recursively) are L1
    dir_purity = {}  # dir_path -> bool (True = all files are L1)

    # First, compute purity for leaf directories
    for dir_key, items in all_files_by_dir.items():
        is_pure = all(layer == 'L1' for _, layer in items)
        dir_purity[dir_key] = is_pure

    # Now compute purity for parent directories (a parent is pure only if all
    # its children directories are also pure AND its own files are all L1)
    all_dirs = sorted(dir_purity.keys(), key=lambda d: d.count('/'), reverse=True)

    # Build parent -> children map
    children_map = defaultdict(set)
    for d in all_dirs:
        parts = d.split('/')
        if len(parts) > 1:
            parent = '/'.join(parts[:-1])
            children_map[parent].add(d)

    # Propagate purity upward
    for d in all_dirs:
        if d in children_map:
            # This dir has subdirectories - it's pure only if itself AND all children are pure
            if dir_purity.get(d, True):  # own files pure?
                dir_purity[d] = all(dir_purity.get(child, False) for child in children_map[d])
            # else already False

    # Now find the optimal set of entries
    entries = set()
    covered_files = set()

    def _find_deepest_pure_ancestor(file_path: str) -> str:
        """Find the deepest directory that is pure L1 and covers this file."""
        parts = file_path.split('/')
        if len(parts) == 1:
            return None  # Root file, no directory to use

        # Check from shallowest to deepest to find the SHALLOWEST pure ancestor
        # (this gives maximum coverage with minimum entries)
        best = None
        for i in range(1, len(parts)):
            dir_path = '/'.join(parts[:i])
            if dir_purity.get(dir_path, False):
                best = dir_path
                break  # Use shallowest pure ancestor for maximum rollup

        return best

    # Process all L1 files
    for f in sorted(l1_files):
        if f in covered_files:
            continue

        ancestor = _find_deepest_pure_ancestor(f)
        if ancestor and ancestor != '.':
            # Use directory glob
            entry = ancestor + '/'
            if entry not in entries:
                entries.add(entry)
                # Mark all L1 files under this directory as covered
                for other_f in l1_files:
                    if other_f.startswith(ancestor + '/'):
                        covered_files.add(other_f)
        else:
            # Individual file (root-level or in mixed directory)
            entries.add(f)
            covered_files.add(f)

    # Deduplicate: remove subdirectory entries if parent directory covers them
    final_entries = set()
    sorted_entries = sorted(entries)
    for entry in sorted_entries:
        # Check if any existing entry already covers this one
        is_covered = False
        for existing in final_entries:
            if existing.endswith('/') and entry.startswith(existing):
                is_covered = True
                break
        if not is_covered:
            final_entries.add(entry)

    return sorted(final_entries)


def generate_npmignore(repo_root: Path) -> str:
    """Generate .npmignore content from audit layer classifications."""
    lines = []
    lines.append("# ===========================================")
    lines.append("# .npmignore - Mega Brain npm package")
    lines.append("# ===========================================")
    lines.append("# AUTO-GENERATED from audit layer classifications.")
    lines.append("# Source of truth: core/intelligence/audit_layers.py")
    lines.append("# Regenerate: python3 core/intelligence/sync_package_files.py --npmignore --apply")
    lines.append("#")
    lines.append("# Defense-in-depth: package.json \"files\" is the")
    lines.append("# primary whitelist. This file is the SECOND layer.")
    lines.append("# ===========================================")
    lines.append("")

    # Python build artifacts
    lines.append("# === PYTHON BUILD ARTIFACTS (NEVER ship) ===")
    lines.append("__pycache__/")
    lines.append("**/__pycache__/")
    lines.append("**/*.pyc")
    lines.append("**/*.pyo")
    lines.append("**/*.pyd")
    lines.append("*.egg-info/")
    lines.append("")

    # L2 content
    lines.append("# === L2 CONTENT (Premium -- not in public package) ===")
    lines.append("# Source: L2_PATTERNS in audit_layers.py")
    for pattern in sorted(L2_PATTERNS):
        lines.append(pattern.rstrip('/') + '/')
    lines.append("")

    # L3 content
    lines.append("# === L3 CONTENT (Personal -- never distributed) ===")
    lines.append("# Source: L3_PATTERNS in audit_layers.py")
    for pattern in sorted(L3_PATTERNS):
        lines.append(pattern.rstrip('/') + '/')
    lines.append("")

    # NEVER content
    lines.append("# === NEVER CONTENT (Secrets/sensitive) ===")
    lines.append("# Source: NEVER_PATTERNS in audit_layers.py")
    for pattern in sorted(NEVER_PATTERNS):
        if pattern.endswith('/'):
            lines.append(pattern)
        elif '.' in pattern and not pattern.startswith('.'):
            # File pattern
            lines.append(pattern)
        else:
            # Could be extension or exact match
            lines.append(pattern)
    lines.append(".env.*")
    lines.append("")

    # Development-only
    lines.append("# === DEVELOPMENT-ONLY (not for consumers) ===")
    lines.append(".planning/")
    lines.append("docs/audit/")
    lines.append("docs/plans/")
    lines.append("docs/validation/")
    lines.append("")

    # Runtime state
    lines.append("# === RUNTIME STATE (per-user, not template) ===")
    lines.append(".claude/agent-memory/")
    lines.append(".claude/monitoring/")
    lines.append(".claude/learning-system/")
    lines.append(".claude/aios/")
    lines.append(".claude/jarvis/STATE.json")
    lines.append(".claude/jarvis/DECISIONS-LOG.md")
    lines.append(".claude/jarvis/CONTEXT-STACK.json")
    lines.append(".claude/jarvis/PENDING.md")
    lines.append(".claude/jarvis/CURRENT-TASK.md")
    lines.append(".claude/settings.local.json")
    lines.append(".claude/audit-*.json")
    lines.append("")

    # Company-specific
    lines.append("# === COMPANY-SPECIFIC CONTENT ===")
    lines.append(".claude/skills/ask-company/")
    lines.append(".claude/skills/process-company-inbox/")
    lines.append(".claude/skills/*-company-*")
    lines.append("")

    # L2-only skills
    lines.append("# === L2-ONLY SKILLS (premium layer) ===")
    l2_skills = [
        "council", "executor", "fase-2-5-tagging", "finance-agent",
        "gdrive-transcription-downloader", "hybrid-source-reading",
        "ler-planilha", "smart-download-tagger", "source-sync",
        "sync-docs", "talent-agent", "chronicler", "gemini-fallback",
        "jarvis", "jarvis-briefing", "resume", "save", "verify",
    ]
    for skill in sorted(l2_skills):
        lines.append(f".claude/skills/{skill}/")
    lines.append("")

    # Media files
    lines.append("# === MEDIA FILES ===")
    for ext in ["*.mp4", "*.mp3", "*.wav", "*.m4a", "*.mov", "*.avi", "*.mkv"]:
        lines.append(ext)
    lines.append("")

    # Large/binary files
    lines.append("# === LARGE/BINARY FILES ===")
    for ext in ["*.b64", "*.db", "*.sqlite", "*.pdf", "*.zip", "*.tar", "*.gz", "*.bz2"]:
        lines.append(ext)
    lines.append("")

    # OS & IDE
    lines.append("# === OS & IDE ===")
    lines.append(".DS_Store")
    lines.append("Thumbs.db")
    lines.append(".vscode/")
    lines.append(".idea/")
    lines.append(".obsidian/")
    lines.append("")

    # Build artifacts
    lines.append("# === BUILD ARTIFACTS ===")
    lines.append("dist/")
    lines.append("build/")
    lines.append(".venv*/")
    lines.append("venv/")
    lines.append("vendor/")
    lines.append("chroma_db/")
    lines.append(".chroma/")
    lines.append("")

    # Backups & temp
    lines.append("# === BACKUPS & TEMP ===")
    lines.append("*_BACKUP_*.py")
    lines.append("*.bak")
    lines.append("*.tmp")
    lines.append("")

    # Git
    lines.append("# === GIT (npm handles this, but explicit) ===")
    lines.append(".git/")

    return '\n'.join(lines) + '\n'


def generate_allowlist(files_array: list, repo_root: Path) -> str:
    """Generate layer1-allowlist.txt from package.json files array."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    lines = []
    lines.append("# Layer 1 Allowlist - PUBLIC content (free/community)")
    lines.append("# ==============================================================")
    lines.append("# AUTO-GENERATED from package.json files field.")
    lines.append("# Regenerate: python3 core/intelligence/sync_package_files.py --allowlist --apply")
    lines.append("#")
    lines.append("# ONLY paths listed here are included in Layer 1 (public repo).")
    lines.append("# Everything else is PREMIUM by default (Layer 2+).")
    lines.append("#")
    lines.append("# SYNCED WITH: package.json \"files\" field")
    lines.append(f"# AUDITED: {now}")
    lines.append("# ==============================================================")
    lines.append("")

    # Group entries by top-level directory
    groups = defaultdict(list)
    for entry in files_array:
        parts = entry.split('/')
        top = parts[0]
        groups[top].append(entry)

    # Category labels
    labels = {
        '.': 'Root files',
        '.antigravity': 'IDE integration (Antigravity)',
        '.claude': 'Claude Code integration',
        '.cursor': 'IDE integration (Cursor)',
        '.github': 'GitHub integration',
        '.windsurf': 'IDE integration (Windsurf)',
        'agents': 'Agent system',
        'artifacts': 'Artifact scaffolding',
        'bin': 'CLI tools',
        'core': 'Core engine',
        'docs': 'Documentation',
        'inbox': 'Inbox scaffolding',
        'knowledge': 'Knowledge scaffolding',
        'logs': 'Logs scaffolding',
        'reference': 'Reference materials',
    }

    for top in sorted(groups.keys()):
        label = labels.get(top, top)
        lines.append(f"# --- {label} ---")
        for entry in sorted(groups[top]):
            lines.append(entry)
        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Sync package.json files field with L1 audit classifications.',
    )
    parser.add_argument(
        '--print', dest='print_mode', action='store_true',
        help='Print computed files array as JSON to stdout',
    )
    parser.add_argument(
        '--apply', action='store_true',
        help='Apply changes to the target file (package.json, .npmignore, or allowlist)',
    )
    parser.add_argument(
        '--diff', action='store_true',
        help='Show diff between current and computed files array',
    )
    parser.add_argument(
        '--npmignore', action='store_true',
        help='Generate .npmignore content',
    )
    parser.add_argument(
        '--allowlist', action='store_true',
        help='Generate layer1-allowlist.txt content',
    )
    args = parser.parse_args()

    if not any([args.print_mode, args.apply, args.diff, args.npmignore, args.allowlist]):
        parser.print_help()
        sys.exit(1)

    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent  # mega-brain/

    if not (repo_root / 'core').exists():
        print(f"ERROR: Could not find repo root. Expected core/ in {repo_root}", file=sys.stderr)
        sys.exit(1)

    # Handle --npmignore
    if args.npmignore:
        content = generate_npmignore(repo_root)
        if args.apply:
            npmignore_path = repo_root / '.npmignore'
            npmignore_path.write_text(content)
            line_count = len(content.strip().split('\n'))
            print(f"Wrote .npmignore ({line_count} lines)", file=sys.stderr)
        else:
            print(content)
        return 0

    # Handle --allowlist
    if args.allowlist:
        files_array = compute_files_array(repo_root)
        content = generate_allowlist(files_array, repo_root)
        if args.apply:
            allowlist_path = repo_root / '.github' / 'layer1-allowlist.txt'
            allowlist_path.parent.mkdir(parents=True, exist_ok=True)
            allowlist_path.write_text(content)
            entry_count = len(files_array)
            print(f"Wrote .github/layer1-allowlist.txt ({entry_count} entries)", file=sys.stderr)
        else:
            print(content)
        return 0

    # Compute files array
    files_array = compute_files_array(repo_root)

    if args.print_mode:
        print(json.dumps(files_array, indent=2))
        return 0

    if args.diff:
        pkg_path = repo_root / 'package.json'
        with open(pkg_path) as f:
            pkg = json.load(f)
        current = set(pkg.get('files', []))
        computed = set(files_array)

        added = sorted(computed - current)
        removed = sorted(current - computed)

        if not added and not removed:
            print("No changes - package.json files field is already in sync.")
        else:
            if added:
                print(f"+ Added ({len(added)}):")
                for e in added:
                    print(f"  + {e}")
            if removed:
                print(f"- Removed ({len(removed)}):")
                for e in removed:
                    print(f"  - {e}")
            print(f"\nCurrent: {len(current)} entries -> Computed: {len(computed)} entries")
        return 0

    if args.apply:
        pkg_path = repo_root / 'package.json'
        with open(pkg_path) as f:
            pkg = json.load(f)

        old_count = len(pkg.get('files', []))
        pkg['files'] = files_array

        with open(pkg_path, 'w') as f:
            json.dump(pkg, f, indent=2)
            f.write('\n')

        print(f"Updated package.json: {old_count} entries -> {len(files_array)} entries", file=sys.stderr)
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
