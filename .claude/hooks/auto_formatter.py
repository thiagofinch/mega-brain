#!/usr/bin/env python3
"""
AUTO FORMATTER HOOK
===================
Formata código automaticamente após Write/Edit.

Baseado em Boris Cherny: "bun run format || true"

Formatters suportados:
- Python: black, autopep8
- JavaScript/TypeScript: prettier
- JSON: jq
- YAML: yamlfmt
- Markdown: prettier

Usage (via hook):
    python3 auto_formatter.py "$TOOL_INPUT"
"""

import sys
import os
import subprocess
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))

# File extensions and their formatters
FORMATTERS = {
    '.py': ['black', '--quiet', '--line-length', '100'],
    '.js': ['prettier', '--write'],
    '.ts': ['prettier', '--write'],
    '.jsx': ['prettier', '--write'],
    '.tsx': ['prettier', '--write'],
    '.json': ['prettier', '--write'],
    '.md': ['prettier', '--write', '--prose-wrap', 'always'],
    '.yaml': ['prettier', '--write'],
    '.yml': ['prettier', '--write'],
}

# Alternative formatters if primary not available
FALLBACK_FORMATTERS = {
    '.py': ['autopep8', '--in-place', '--aggressive'],
}


def extract_file_path(tool_input: str) -> str:
    """Extract file path from tool input"""
    # Try to parse as JSON first
    try:
        data = json.loads(tool_input)
        return data.get('file_path', '')
    except:
        pass

    # Try regex for file_path
    match = re.search(r'"file_path"\s*:\s*"([^"]+)"', tool_input)
    if match:
        return match.group(1)

    # Try to find any path-like string
    match = re.search(r'(/[^\s"]+\.\w+)', tool_input)
    if match:
        return match.group(1)

    return ''


def check_formatter_available(formatter: list) -> bool:
    """Check if formatter is installed"""
    try:
        subprocess.run(
            [formatter[0], '--version'],
            capture_output=True,
            timeout=5
        )
        return True
    except:
        return False


def format_file(filepath: str) -> tuple[bool, str]:
    """Format a file using appropriate formatter"""
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    ext = Path(filepath).suffix.lower()

    if ext not in FORMATTERS:
        return True, f"No formatter for {ext}"

    formatter = FORMATTERS[ext]

    # Check if formatter is available
    if not check_formatter_available(formatter):
        # Try fallback
        if ext in FALLBACK_FORMATTERS:
            formatter = FALLBACK_FORMATTERS[ext]
            if not check_formatter_available(formatter):
                return True, f"No formatter available for {ext}"
        else:
            return True, f"Formatter {formatter[0]} not installed"

    # Run formatter
    try:
        cmd = formatter + [filepath]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, f"Formatted with {formatter[0]}"
        else:
            # Don't fail on formatter errors - just report
            return True, f"Formatter warning: {result.stderr[:100]}"

    except subprocess.TimeoutExpired:
        return True, "Formatter timeout"
    except Exception as e:
        return True, f"Formatter error: {str(e)[:100]}"


def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    tool_input = sys.argv[1]
    filepath = extract_file_path(tool_input)

    if not filepath:
        sys.exit(0)

    # Skip non-code files
    ext = Path(filepath).suffix.lower()
    if ext not in FORMATTERS:
        sys.exit(0)

    # Skip files outside project
    if str(PROJECT_ROOT) not in filepath:
        sys.exit(0)

    # Format
    success, message = format_file(filepath)

    if success:
        print(f"✨ {message}: {Path(filepath).name}")
    else:
        print(f"⚠️ {message}")

    sys.exit(0)


if __name__ == '__main__':
    main()
