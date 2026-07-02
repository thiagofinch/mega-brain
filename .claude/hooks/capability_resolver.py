#!/usr/bin/env python3
"""
capability_resolver.py -- Capability Resolver Engine (MegaBrain)

Pure module that resolves a capability ID to its best available provider.
No child processes, no side effects beyond cache.

Usage:
    from capability_resolver import resolve
    result = resolve('supabase_query')

Part of the Tool Intelligence Layer (MegaBrain Python-first architecture).

TIL-21 addition:
    Each successful resolve() call emits an OTel GenAI span via
    engine.intelligence.metrics.otel_capability_tracer. The span captures
    `gen_ai.tool.name` (capability_id) and the resolved provider type so
    drift analysis can correlate "declared pra_que" with "what provider
    actually answered the call". Fail-open: missing module = silent skip.
"""

import json
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
MCP_PATH = PROJECT_ROOT / ".mcp.json"

# Module-level cache
_cache: dict = {}
_registry_data = None
_mcp_data = None
_mcp_loaded = False
_env_loaded = False


def _ensure_env():
    """Load .env once if not already loaded."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        # Manual .env parser fallback
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # Strip surrounding quotes
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value
            except Exception:
                pass


def _load_yaml(path: Path):
    """Load YAML file. Tries PyYAML, falls back to basic parser."""
    if yaml is not None:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    # Minimal fallback: won't work for complex YAML, but lets the module load
    raise ImportError("PyYAML (pyyaml) is required: pip3 install pyyaml")


def _load_registry():
    """Load and cache the capability registry from disk."""
    global _registry_data
    if _registry_data is not None:
        return _registry_data
    try:
        _registry_data = _load_yaml(REGISTRY_PATH)
        return _registry_data
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _load_mcp():
    """Load and cache .mcp.json from disk."""
    global _mcp_data, _mcp_loaded
    if _mcp_loaded:
        return _mcp_data
    try:
        with open(MCP_PATH, encoding="utf-8") as f:
            _mcp_data = json.load(f)
    except Exception:
        _mcp_data = {"mcpServers": {}}
    _mcp_loaded = True
    return _mcp_data


def _check_provider_available(
    provider: dict, mcp_servers: dict, service_adapter: str | None
) -> bool:
    """Check if a single provider is currently available. Boolean only -- never reads env values."""
    ptype = provider.get("type", "")

    if ptype == "mcp":
        key = provider.get("mcp_server_key", "")
        return key in mcp_servers

    if ptype == "api":
        env_key = provider.get("env_key")
        if env_key is None:
            env_ok = True
        else:
            env_ok = env_key in os.environ
        # credential_file fallback
        cred_file = provider.get("credential_file")
        file_ok = (PROJECT_ROOT / cred_file).exists() if cred_file else False
        cred_ok = env_ok or file_ok
        # service_adapter check
        adapter_ok = (PROJECT_ROOT / service_adapter).exists() if service_adapter else True
        return cred_ok and adapter_ok

    if ptype == "user-action":
        return True

    return False


def resolve(capability_id: str) -> dict:
    """
    Resolve a capability ID to its best available provider.

    Returns dict with:
        capability_id, resolved_provider, available, fallback_chain,
        user_action_required, context_cost_estimate, error?
    """
    # Warm path
    if capability_id in _cache:
        return _cache[capability_id]

    _ensure_env()

    # Load registry (fail-open)
    registry = _load_registry()
    if not registry:
        return {
            "capability_id": capability_id,
            "resolved_provider": None,
            "available": False,
            "fallback_chain": [],
            "user_action_required": {
                "action": "python3 .claude/hooks/sync_capability_status.py",
                "reason": "registry not found",
            },
            "context_cost_estimate": None,
        }

    capabilities = registry.get("capabilities", {})
    capability = capabilities.get(capability_id) if capabilities else None

    if not capability:
        result = {
            "capability_id": capability_id,
            "resolved_provider": None,
            "available": False,
            "fallback_chain": [],
            "user_action_required": False,
            "context_cost_estimate": None,
            "error": "capability not found",
        }
        _cache[capability_id] = result
        return result

    # Load MCP config
    mcp = _load_mcp()
    mcp_servers = mcp.get("mcpServers", {})

    # Walk providers in priority order
    providers = sorted(capability.get("providers", []), key=lambda p: p.get("priority", 99))
    service_adapter = capability.get("service_adapter")

    resolved_provider = None
    fallback_chain = []

    for provider in providers:
        is_available = _check_provider_available(provider, mcp_servers, service_adapter)

        if resolved_provider is None and is_available:
            resolved_provider = provider
        elif is_available:
            fallback_chain.append(
                {
                    "id": provider.get("id", ""),
                    "type": provider.get("type", ""),
                    "available": True,
                }
            )
        else:
            fallback_chain.append(
                {
                    "id": provider.get("id", ""),
                    "type": provider.get("type", ""),
                    "available": False,
                    "status": provider.get("status", "unknown"),
                }
            )

    is_user_action = (resolved_provider or {}).get("type") == "user-action"

    result = {
        "capability_id": capability_id,
        "resolved_provider": {
            "id": resolved_provider["id"],
            "type": resolved_provider["type"],
            "mechanism": resolved_provider["type"],
        }
        if resolved_provider
        else None,
        "available": resolved_provider is not None and not is_user_action,
        "user_action_required": {"action": resolved_provider.get("instructions", "")}
        if is_user_action
        else False,
        "fallback_chain": fallback_chain,
        "context_cost_estimate": (resolved_provider or {}).get("context_cost_estimate"),
    }

    _cache[capability_id] = result

    # TIL-21: OTel span emission (fail-open). Only emit when the capability
    # actually resolved to an available provider — we are tracing real usage,
    # not failed lookups.
    try:
        if result.get("available") and result.get("resolved_provider"):
            import sys as _sys

            if str(PROJECT_ROOT) not in _sys.path:
                _sys.path.insert(0, str(PROJECT_ROOT))
            from engine.intelligence.metrics.otel_capability_tracer import (
                emit_capability_span,
            )

            cap_desc = (capability or {}).get("description") or ""
            provider = result.get("resolved_provider") or {}
            emit_capability_span(
                capability_id=capability_id,
                capability_description=cap_desc,
                prompt=None,  # resolver doesn't see the prompt — only the cap id
                match_type="resolve",
                extra_attrs={
                    "til.provider.type": provider.get("type", ""),
                    "til.provider.id": provider.get("id", ""),
                },
            )
    except Exception:
        # Fail-open
        pass

    return result


def clear_cache():
    """Clear the in-process cache. Useful for testing."""
    global _cache, _registry_data, _mcp_data, _mcp_loaded, _env_loaded
    _cache = {}
    _registry_data = None
    _mcp_data = None
    _mcp_loaded = False
    _env_loaded = False
