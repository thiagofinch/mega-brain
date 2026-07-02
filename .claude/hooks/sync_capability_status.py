#!/usr/bin/env python3
"""
sync_capability_status.py -- Sync provider status fields in capability-registry.yaml

Modes:
    (default)   -- updates capability-registry.yaml in-place
    --check     -- read-only, exit 1 if any status diverges from reality
    --dry-run   -- shows what would change without writing

Exit codes:
    0 -- changes applied successfully
    1 -- parse/runtime error
    2 -- no changes needed (already in sync)
    3 -- invalid argument

Security: NEVER logs env var values -- only key names and boolean availability.

Part of the Tool Intelligence Layer (MegaBrain Python-first architecture).
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
MCP_JSON_PATH = PROJECT_ROOT / ".mcp.json"


def _ensure_env():
    """Load .env into os.environ."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value
            except Exception:
                pass


def load_mcp_keys() -> set:
    try:
        with open(MCP_JSON_PATH, encoding="utf-8") as f:
            parsed = json.load(f)
        return set((parsed.get("mcpServers") or parsed).keys())
    except Exception:
        return set()


def resolve_status(provider: dict, mcp_keys: set) -> str:
    ptype = provider.get("type", "")

    if ptype == "user-action":
        return "available"

    if ptype == "mcp":
        key = provider.get("mcp_server_key", "")
        return "available" if key in mcp_keys else "requires_install"

    if ptype == "api":
        env_key = provider.get("env_key")
        if not env_key:
            return "available"
        env_ok = env_key in os.environ
        cred_file = provider.get("credential_file")
        file_ok = (PROJECT_ROOT / cred_file).exists() if cred_file else False
        return "available" if (env_ok or file_ok) else "requires_key"

    return provider.get("status", "unknown")


def main():
    args = sys.argv[1:]
    valid_flags = {"--check", "--dry-run"}
    unknown = [a for a in args if a not in valid_flags]

    if unknown:
        print(f"Error: Unknown argument(s): {', '.join(unknown)}", file=sys.stderr)
        print("Usage: sync_capability_status.py [--check | --dry-run]", file=sys.stderr)
        sys.exit(3)

    check_mode = "--check" in args
    dry_run_mode = "--dry-run" in args

    if check_mode and dry_run_mode:
        print("Error: --check and --dry-run are mutually exclusive.", file=sys.stderr)
        sys.exit(3)

    _ensure_env()

    # Load registry
    try:
        raw_yaml = REGISTRY_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    try:
        registry = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        print(f"Error: YAML parse failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not registry or not registry.get("capabilities"):
        print("Error: No 'capabilities' key found in registry.", file=sys.stderr)
        sys.exit(1)

    mcp_keys = load_mcp_keys()

    changes = []
    total_providers = 0

    for cap_id, cap in registry["capabilities"].items():
        providers = cap.get("providers")
        if not providers or not isinstance(providers, list):
            continue
        for provider in providers:
            total_providers += 1
            expected = resolve_status(provider, mcp_keys)
            current = provider.get("status", "unknown")
            if current != expected:
                changes.append(
                    {
                        "capability": cap_id,
                        "provider_id": provider.get("id", "?"),
                        "from": current,
                        "to": expected,
                    }
                )
                provider["status"] = expected

    # Report
    print("")
    print("Capability Status Sync")
    print("=" * 22)
    print(f"Providers checked: {total_providers}")
    print(f"Already correct:   {total_providers - len(changes)}")
    print(f"Updated:           {len(changes)}")

    for c in changes:
        print(f"  {c['provider_id']} ({c['capability']}): {c['from']} -> {c['to']}")

    print("")

    if check_mode:
        if changes:
            print("DRIFT DETECTED: Registry status does not match environment.")
            sys.exit(1)
        print("OK: Registry status matches environment.")
        sys.exit(0)

    if dry_run_mode:
        if not changes:
            print("No changes needed.")
        else:
            print("Dry run complete. No files modified.")
        sys.exit(0 if changes else 2)

    # Default mode -- write
    if not changes:
        print("Already in sync. No file modified.")
        sys.exit(2)

    # Line-level replacement to preserve YAML formatting.
    # Strategy: find each "- id: X" block and replace status within that block only.
    # We process line-by-line to avoid cross-block regex issues with duplicate provider IDs.
    lines = raw_yaml.split("\n")
    change_map = {}  # (capability, provider_id) -> to_status
    for c in changes:
        key = (c["capability"], c["provider_id"])
        change_map[key] = (c["from"], c["to"])

    # Walk lines: track current capability and current provider
    current_cap = None
    current_provider_id = None
    updated_lines = []
    for line in lines:
        # Detect capability block (2-space indent, key followed by colon)
        cap_match = re.match(r"^  (\w+):$", line)
        if cap_match:
            current_cap = cap_match.group(1)

        # Detect provider id (6 spaces + "- id:")
        id_match = re.match(r"^(\s+)- id: (.+)$", line)
        if id_match:
            current_provider_id = id_match.group(2).strip()

        # Detect status line and replace if needed
        status_match = re.match(r"^(\s+status: )(.+)$", line)
        if status_match and current_cap and current_provider_id:
            key = (current_cap, current_provider_id)
            if key in change_map:
                from_val, to_val = change_map[key]
                current_status = status_match.group(2).strip()
                if current_status == from_val:
                    line = f"{status_match.group(1)}{to_val}"
                    del change_map[key]

        updated_lines.append(line)

    updated_yaml = "\n".join(updated_lines)

    try:
        REGISTRY_PATH.write_text(updated_yaml, encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to write registry: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Registry updated: {REGISTRY_PATH}")

    # Rebuild keyword index
    try:
        import subprocess

        subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / ".claude" / "hooks" / "build_capability_keyword_index.py"),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
