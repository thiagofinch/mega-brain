#!/usr/bin/env bash
# Thin wrapper for refresh-registry.py
# Usage: bin/refresh-registry.sh [--output /path/to/output.yaml]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/refresh-registry.py" "$@"
