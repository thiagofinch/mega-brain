#!/usr/bin/env python3
"""
Layer Audit Script for Mega Brain Repository

Classifies every file and folder in the repository into layers:
- L1 (Community): Core engine, empty structures
- L2 (Premium): L1 + populated content
- L3 (Personal): Never distributed
- NEVER: Always gitignored
- DELETE: Marked for removal
- REVIEW: Needs human review

Output: JSON + Markdown reports in docs/audit/
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional

# Classification patterns (from CONTEXT.md)
L1_PATTERNS = [
    # Core engine
    'bin/',
    'core/',
    '.claude/',
    'agents/conclave/',
    'agents/_templates/',
    'docs/',
    # Empty structures with .gitkeep
    'inbox/.gitkeep',
    'knowledge/.gitkeep',
    'agents/minds/.gitkeep',
    'agents/cargo/.gitkeep',
    'artifacts/insights/.gitkeep',
    'artifacts/chunks/.gitkeep',
    'artifacts/extractions/.gitkeep',
    # Root project files (no slash = exact filename match in classify_path)
    'package.json',
    'package-lock.json',
    'requirements.txt',
    '.gitignore',
    '.gitattributes',
    '.npmignore',
    '.env.example',
    '.gitleaks.toml',
    'README.md',
    'CONTRIBUTING.md',
    'QUICK-START.md',
    # GitHub integration (CI/CD, templates, assets)
    '.github/',
    # GSD planning system
    '.planning/',
    # IDE integration configs (community-distributed)
    '.cursor/',
    '.windsurf/',
    '.antigravity/',
    # Root container directories (structural scaffolding)
    'agents',
    'artifacts',
    'knowledge',
    # Agents community scaffold (boardroom = L1 audio/podcast system)
    'agents/boardroom/',
    'agents/constitution/',
    'agents/AGENT-INDEX.yaml',
    'agents/MASTER-AGENT.md',
    'agents/README.md',
    'agents/persona-registry.yaml',
    # Artifacts scaffold (README and gitkeep in subdirs not yet covered)
    'artifacts/README.md',
    'artifacts/canonical/',
    'artifacts/narratives/',
    'artifacts/dna/',
    # Knowledge scaffold
    'knowledge/README.md',
    'knowledge/NAVIGATION-MAP.json',
    'knowledge/TAG-RESOLVER.json',
]

L2_PATTERNS = [
    # Populated content (everything L1 + absorbed)
    'agents/minds/',
    'agents/cargo/',
    'knowledge/dossiers/',
    'knowledge/playbooks/',
    'knowledge/dna/',
    'knowledge/sources/',
    'artifacts/insights/',
    'artifacts/chunks/',
    'artifacts/extractions/',
]

L3_PATTERNS = [
    # Personal - never distributed
    'inbox/',
    'logs/',
    '.claude/sessions/',
    '.claude/mission-control/',
    'agents/sua-empresa/',
]

NEVER_PATTERNS = [
    # Always gitignored
    '.env',
    'credentials.json',
    'token.json',
    '.key',
    '.pem',
    '.secret',
    '.mcp.json',
    'settings.local.json',
    'node_modules/',
    '.DS_Store',
]

DELETE_PATTERNS = [
    # Obsolete agents
    'finance-agent',
    'talent-agent',
]

# macOS Finder duplicate pattern: "BASENAME 2.ext" where ext is a short extension (no spaces)
# Matches: "README 2.md", "TAG-RESOLVER 2.json", "HEURISTICAS 2.yaml"
# Does NOT match: "[PAF-0028] 2. Como começar.txt" (has space after dot)
_MACOS_DUP_RE = re.compile(r' 2\.[a-zA-Z0-9]{1,10}$')

# Directories to skip during scan
SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env',
    # Gitignored data directories (not tracked, would inflate REVIEW count)
    'archive', '_IMPORT', '_import', '.venv-rag', '.chroma', '.data',
    'D:', 'chroma_db', '.layer-sync', 'vendor',
    '.obsidian', '.vscode', '.idea',
}


def classify_path(path: Path, repo_root: Path, is_file: bool) -> Tuple[str, str]:
    """
    Classify a path into a layer.

    Returns: (layer, reason)
    Priority: DELETE > NEVER > L3 > L2 > L1 > REVIEW
    """
    rel_path = str(path.relative_to(repo_root))
    name = path.name

    # Check DELETE patterns
    for pattern in DELETE_PATTERNS:
        if pattern in rel_path:
            return ('DELETE', f'Obsolete: {pattern}')

    # Note: macOS Finder duplicate check is below, after layer checks

    # Check NEVER patterns
    for pattern in NEVER_PATTERNS:
        if pattern.endswith('/'):
            # Directory pattern
            if rel_path.startswith(pattern.rstrip('/')):
                return ('NEVER', 'Secrets/sensitive config')
        elif '.' in pattern:
            # File with extension: exact name match (avoid .env matching .env.example)
            if name == pattern:
                return ('NEVER', 'Secrets/sensitive config')
        else:
            # Extension pattern (e.g. .key, .pem)
            if name.endswith(pattern) or pattern in name:
                return ('NEVER', 'Secrets/sensitive config')

    # Check L3 patterns (most specific first)
    for pattern in L3_PATTERNS:
        if rel_path.startswith(pattern.rstrip('/')):
            # Exception: .gitkeep files in L3 dirs are L1
            if name == '.gitkeep':
                return ('L1', 'Empty structure marker')
            # Exception: README.md files in L3 dirs are L1 (documentation scaffold)
            if name == 'README.md':
                return ('L1', 'Documentation scaffold')
            # Exception: _example/ subdirectories are community scaffold content (L1)
            if '/_example/' in rel_path or rel_path.endswith('/_example'):
                return ('L1', 'Community example scaffold')
            return ('L3', 'Personal data')

    # Check L2 patterns
    for pattern in L2_PATTERNS:
        if rel_path.startswith(pattern.rstrip('/')):
            # Exception: .gitkeep files are L1
            if name == '.gitkeep':
                return ('L1', 'Empty structure marker')
            # Exception: empty directories (only .gitkeep) are L1
            if not is_file and path.is_dir():
                children = list(path.iterdir())
                if len(children) == 1 and children[0].name == '.gitkeep':
                    return ('L1', 'Empty structure (only .gitkeep)')
            return ('L2', 'Premium content')

    # Check L1 patterns
    for pattern in L1_PATTERNS:
        if pattern.endswith('.gitkeep'):
            # Exact match for .gitkeep paths
            if rel_path == pattern:
                return ('L1', 'Empty structure marker')
        elif '/' in pattern:
            # Directory prefix match
            if rel_path.startswith(pattern.rstrip('/')):
                return ('L1', 'Core engine')
        else:
            # Root-level file exact match (package.json, README.md, etc.)
            if rel_path == pattern:
                return ('L1', 'Root project file')

    # Check macOS Finder duplicates AFTER layer checks (e.g. "README 2.md")
    # These are files that didn't match any layer pattern — likely stale copies
    if _MACOS_DUP_RE.search(name):
        return ('DELETE', f'Stale duplicate: {name}')

    # Default to REVIEW if no clear match
    return ('REVIEW', 'Unclear classification')


def scan_repository(repo_root: Path, verbose: bool = False) -> Dict:
    """
    Scan entire repository and classify all items.

    Returns structured data dictionary.
    """
    classifications = []
    summary = {
        'L1': 0,
        'L2': 0,
        'L3': 0,
        'NEVER': 0,
        'DELETE': 0,
        'REVIEW': 0,
    }

    delete_candidates = []
    review_needed = []

    if verbose:
        print(f"Scanning repository: {repo_root}")

    # Walk the repository
    for root, dirs, files in os.walk(repo_root):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        root_path = Path(root)

        # Classify directories
        for dirname in dirs:
            dir_path = root_path / dirname
            try:
                layer, reason = classify_path(dir_path, repo_root, is_file=False)

                rel_path = str(dir_path.relative_to(repo_root))
                classifications.append({
                    'path': rel_path + '/',
                    'layer': layer,
                    'type': 'directory',
                    'reason': reason,
                })

                summary[layer] += 1

                if layer == 'DELETE':
                    delete_candidates.append({
                        'path': rel_path + '/',
                        'reason': reason,
                    })
                elif layer == 'REVIEW':
                    review_needed.append({
                        'path': rel_path + '/',
                        'reason': reason,
                    })

                if verbose:
                    print(f"  [{layer}] {rel_path}/")

            except Exception as e:
                if verbose:
                    print(f"  [ERROR] {dir_path}: {e}")

        # Classify files
        for filename in files:
            file_path = root_path / filename
            try:
                layer, reason = classify_path(file_path, repo_root, is_file=True)

                rel_path = str(file_path.relative_to(repo_root))
                classifications.append({
                    'path': rel_path,
                    'layer': layer,
                    'type': 'file',
                    'reason': reason,
                })

                summary[layer] += 1

                if layer == 'DELETE':
                    delete_candidates.append({
                        'path': rel_path,
                        'reason': reason,
                    })
                elif layer == 'REVIEW':
                    review_needed.append({
                        'path': rel_path,
                        'reason': reason,
                    })

                if verbose:
                    print(f"  [{layer}] {rel_path}")

            except Exception as e:
                if verbose:
                    print(f"  [ERROR] {file_path}: {e}")

    total_items = sum(summary.values())

    return {
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'repo_root': str(repo_root),
        'summary': {
            'total_items': total_items,
            'by_layer': summary,
        },
        'classifications': classifications,
        'delete_candidates': delete_candidates,
        'review_needed': review_needed,
    }


def generate_markdown_report(data: Dict, output_path: Path) -> None:
    """Generate human-readable markdown report."""
    with open(output_path, 'w') as f:
        f.write("# Mega Brain Layer Audit Report\n\n")
        f.write(f"**Generated:** {data['generated_at']}\n")
        f.write(f"**Repository:** {data['repo_root']}\n")
        f.write(f"**Total Items Classified:** {data['summary']['total_items']}\n\n")

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Layer | Count | % |\n")
        f.write("|-------|-------:|---:|\n")

        total = data['summary']['total_items']
        for layer, count in sorted(data['summary']['by_layer'].items()):
            pct = (count / total * 100) if total > 0 else 0
            f.write(f"| {layer} | {count} | {pct:.1f}% |\n")

        # Delete candidates
        f.write("\n## Delete Candidates\n\n")
        if data['delete_candidates']:
            f.write("| Path | Reason |\n")
            f.write("|------|--------|\n")
            for item in data['delete_candidates']:
                f.write(f"| {item['path']} | {item['reason']} |\n")
        else:
            f.write("*No items marked for deletion.*\n")

        # Review needed
        f.write("\n## Needs Review\n\n")
        if data['review_needed']:
            f.write("| Path | Reason |\n")
            f.write("|------|--------|\n")
            for item in data['review_needed']:
                f.write(f"| {item['path']} | {item['reason']} |\n")
        else:
            f.write("*All items classified clearly.*\n")

        # Layer breakdown
        f.write("\n## Layer Breakdown\n\n")

        # Group classifications by layer
        by_layer = {}
        for item in data['classifications']:
            layer = item['layer']
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(item['path'])

        # L1
        f.write("### L1 (Community - npm package)\n\n")
        if 'L1' in by_layer:
            for path in sorted(by_layer['L1'])[:20]:  # First 20
                f.write(f"- {path}\n")
            if len(by_layer['L1']) > 20:
                f.write(f"\n*...and {len(by_layer['L1']) - 20} more items*\n")
        else:
            f.write("*No L1 items found.*\n")

        # L2
        f.write("\n### L2 (Premium - populated)\n\n")
        if 'L2' in by_layer:
            for path in sorted(by_layer['L2'])[:20]:
                f.write(f"- {path}\n")
            if len(by_layer['L2']) > 20:
                f.write(f"\n*...and {len(by_layer['L2']) - 20} more items*\n")
        else:
            f.write("*No L2 items found.*\n")

        # L3
        f.write("\n### L3 (Personal - never distributed)\n\n")
        if 'L3' in by_layer:
            for path in sorted(by_layer['L3'])[:20]:
                f.write(f"- {path}\n")
            if len(by_layer['L3']) > 20:
                f.write(f"\n*...and {len(by_layer['L3']) - 20} more items*\n")
        else:
            f.write("*No L3 items found.*\n")

        # NEVER
        f.write("\n### NEVER (gitignored in all layers)\n\n")
        if 'NEVER' in by_layer:
            for path in sorted(by_layer['NEVER']):
                f.write(f"- {path}\n")
        else:
            f.write("*No NEVER items found.*\n")


def main():
    parser = argparse.ArgumentParser(
        description='Audit Mega Brain repository layer classification'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='docs/audit',
        help='Output directory for reports (default: docs/audit)',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose output during scan',
    )

    args = parser.parse_args()

    # Determine repo root (parent of core/)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent  # mega-brain/

    if not (repo_root / 'core').exists():
        print(f"ERROR: Could not find repo root. Expected core/ in {repo_root}")
        sys.exit(1)

    print(f"Repository root: {repo_root}")
    print("Starting layer audit...\n")

    # Scan repository
    data = scan_repository(repo_root, verbose=args.verbose)

    # Create output directory
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    json_path = output_dir / 'AUDIT-REPORT.json'
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ JSON report written to: {json_path}")

    # Write Markdown report
    md_path = output_dir / 'AUDIT-REPORT.md'
    generate_markdown_report(data, md_path)
    print(f"✅ Markdown report written to: {md_path}")

    # Print summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)
    print(f"Total items classified: {data['summary']['total_items']}")
    for layer, count in sorted(data['summary']['by_layer'].items()):
        pct = (count / data['summary']['total_items'] * 100) if data['summary']['total_items'] > 0 else 0
        print(f"  {layer:8s}: {count:4d} ({pct:5.1f}%)")

    if data['delete_candidates']:
        print(f"\n⚠️  {len(data['delete_candidates'])} items marked for deletion")

    if data['review_needed']:
        print(f"⚠️  {len(data['review_needed'])} items need review")

    print("\nAudit complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
