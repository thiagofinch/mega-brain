#!/usr/bin/env python3
"""
sync_capability_status.py -- Sync provider status fields no SOT unificado de capabilities

Story 212.W1.1 (ADR-ONTOLOGIA-OPERACIONAL D1): opera sobre o SOT
(agents/_registry/capability-sot.yaml), NÃO mais sobre a vista TIL. Atualiza o campo
`status` de cada provider do eixo TIL (capabilities.<id>.til.providers[]) conforme a
realidade de env/MCP e, em seguida, delega a REGENERAÇÃO das 2 vistas ao gerador
determinístico (scripts/generate-capability-views.js --write). Assim o js-yaml continua
sendo o ÚNICO formatador canônico do SOT + vistas (sem ping-pong cross-lib).

Modos:
    (default)   -- edita os status no SOT (line-level, preserva formatação) + regenera vistas
    --check     -- read-only, exit 1 se algum status divergir da realidade (env/MCP)
    --dry-run   -- mostra o que mudaria, sem escrever

Exit codes:
    0 -- changes applied successfully  (ou --check em sincronia / --dry-run com mudanças)
    1 -- parse/runtime error
    2 -- no changes needed (already in sync)
    3 -- invalid argument

Security: NEVER logs env var values -- only key names and boolean availability.

Ported from: Megabrain EPIC-127 (STORY-127.2). Re-targeted ao SOT em 212.W1.1.
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
SOT_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-sot.yaml"
MCP_JSON_PATH = PROJECT_ROOT / ".mcp.json"
GENERATOR = PROJECT_ROOT / "scripts" / "generate-capability-views.js"


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


def regenerate_views() -> bool:
    """Delega a regeneração das 2 vistas ao gerador determinístico (js-yaml)."""
    import subprocess

    try:
        result = subprocess.run(
            ["node", str(GENERATOR), "--write"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=30,
            text=True,
        )
        if result.returncode != 0:
            print(
                f"Error: gerador de vistas falhou (exit {result.returncode}):\n{result.stderr}",
                file=sys.stderr,
            )
            return False
        return True
    except Exception as e:
        print(f"Error: falha ao invocar o gerador de vistas: {e}", file=sys.stderr)
        return False


def rebuild_keyword_index():
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

    # Load SOT
    try:
        raw_yaml = SOT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: SOT not found: {SOT_PATH}", file=sys.stderr)
        sys.exit(1)

    try:
        sot = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        print(f"Error: YAML parse failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not sot or not sot.get("capabilities"):
        print("Error: No 'capabilities' key found in SOT.", file=sys.stderr)
        sys.exit(1)

    mcp_keys = load_mcp_keys()

    changes = []
    total_providers = 0
    til_cap_ids = set()

    # Itera SOMENTE o eixo TIL de cada capability (capabilities.<id>.til.providers[]).
    for cap_id, entry in sot["capabilities"].items():
        if not isinstance(entry, dict):
            continue
        til = entry.get("til")
        if not isinstance(til, dict):
            continue
        til_cap_ids.add(cap_id)
        providers = til.get("providers")
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

    # Report
    print("")
    print("Capability Status Sync (SOT)")
    print("=" * 28)
    print(f"SOT:               {SOT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"TIL providers:     {total_providers}")
    print(f"Already correct:   {total_providers - len(changes)}")
    print(f"Updated:           {len(changes)}")

    for c in changes:
        print(f"  {c['provider_id']} ({c['capability']}): {c['from']} -> {c['to']}")

    print("")

    if check_mode:
        if changes:
            print("DRIFT DETECTED: SOT status does not match environment.")
            sys.exit(1)
        print("OK: SOT status matches environment.")
        sys.exit(0)

    if dry_run_mode:
        if not changes:
            print("No changes needed.")
        else:
            print("Dry run complete. No files modified.")
        sys.exit(0 if changes else 2)

    # Default mode -- write status into the SOT (line-level, preserva formatação),
    # depois regenera as vistas via gerador determinístico.
    if not changes:
        print("Already in sync. No file modified.")
        sys.exit(2)

    lines = raw_yaml.split("\n")
    change_map = {}  # (capability, provider_id) -> (from, to)
    for c in changes:
        change_map[(c["capability"], c["provider_id"])] = (c["from"], c["to"])

    # Walk lines. current_cap só é atualizado para chaves de 2 espaços que sejam
    # capability ids CONHECIDOS do eixo TIL (desambigua de til_view/resolver_view).
    current_cap = None
    current_provider_id = None
    updated_lines = []
    for line in lines:
        cap_match = re.match(r"^  ([\w-]+):$", line)
        if cap_match and cap_match.group(1) in til_cap_ids:
            current_cap = cap_match.group(1)
            current_provider_id = None

        id_match = re.match(r"^(\s+)- id: (.+)$", line)
        if id_match:
            current_provider_id = id_match.group(2).strip()

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

    if change_map:
        # Algum status esperado não foi encontrado na linha esperada — aborta LOUD
        # em vez de escrever um SOT parcialmente sincronizado.
        print(
            f"Error: {len(change_map)} status change(s) não localizados no SOT "
            f"(formato inesperado): {list(change_map.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    updated_yaml = "\n".join(updated_lines)

    try:
        SOT_PATH.write_text(updated_yaml, encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to write SOT: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"SOT updated: {SOT_PATH}")

    # Regenera as 2 vistas a partir do SOT atualizado (js-yaml determinístico).
    if not regenerate_views():
        sys.exit(1)
    print("Views regenerated from SOT.")

    # Rebuild keyword index (lê a vista TIL regenerada)
    rebuild_keyword_index()

    sys.exit(0)


if __name__ == "__main__":
    main()
