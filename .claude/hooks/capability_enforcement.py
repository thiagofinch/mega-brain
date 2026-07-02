#!/usr/bin/env python3
"""
capability_enforcement.py -- PreToolUse Hook: Capability Hard Routing (Wave 4)

Intercepts Bash/Write/Edit tool calls and validates external API calls against
the capability registry. Soft-blocks when a registered capability is found;
logs to discovery queue when no match found.

Hook event: PreToolUse
Matcher: Bash|Write|Edit
Timeout: 5000ms (fail-open if exceeded anyway)

Enforcement tiers:
    confidence >= 0.85  -> BLOCK (return decision: block)
    confidence 0.60-0.85 -> WARN (inject comment, let proceed)
    confidence < 0.60   -> PERMIT silently
    No external signal   -> PERMIT immediately (zero latency)

Override: BYPASS_CAPABILITY_ENFORCEMENT=true -> PERMIT + audit log

Config: mega-brain-core/core-config.yaml -> capability_enforcement block
    enabled: false  (opt-in OFF by default -- founder must flip)
    confidence_block: 0.85
    confidence_warn: 0.60
    discovery_threshold_count: 5
    discovery_threshold_days: 7

Note: config reload intra-session does NOT exist by design.
Registry cache is loaded once per session on first hook fire (session-scoped,
no file-watch invalidation). Changes to registry only reflect in next session.
This is an explicit design decision (ADR-TIL-003, D2 in decision-log).

Privacy: command_hash = SHA-256[:12] of first 256 chars of command.
NEVER logs full command. url_domain only.

Fail-open: ANY exception -> PERMIT + log enforcement_error. Hook crash NEVER
blocks agent work (PreToolUse is critical path).

Story: TIL-CAPABILITY-ENFORCEMENT (Wave 4)
ADR: ADR-TIL-001 (hooks dir = Python only), ADR-TIL-003 (enforcement design)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: add project root to sys.path for scripts/ imports
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

_SCRIPTS_PATH = str(PROJECT_ROOT / "scripts")
if _SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, _SCRIPTS_PATH)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = PROJECT_ROOT / ".data"
METRICS_PATH = DATA_DIR / "capability-hints-metrics.jsonl"
DISCOVERY_QUEUE = DATA_DIR / "capability-discovery-queue.jsonl"
CORE_CONFIG_PATH = PROJECT_ROOT / "mega-brain-core" / "core-config.yaml"

HOOK_TAG = "[capability_enforcement]"

# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG = {
    "enabled": False,
    "confidence_block": 0.85,
    "confidence_warn": 0.60,
    "discovery_threshold_count": 5,
    "discovery_threshold_days": 7,
}

# Module-level config cache (session-scoped, no reload by design -- see docstring)
_CONFIG_CACHE: dict | None = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _log(msg: str) -> None:
    print(f"{HOOK_TAG} {msg}", file=sys.stderr)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _command_hash(command: str) -> str:
    """SHA-256 of first 256 chars, truncated to 12 hex chars (privacy-safe dedup)."""
    return hashlib.sha256(command[:256].encode("utf-8")).hexdigest()[:12]


def _append_metrics(entry: dict) -> None:
    """Append one JSON line to metrics file. Best-effort, never raise."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with METRICS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _append_discovery(entry: dict) -> None:
    """
    Append to discovery queue with dedup by command_hash (AC5 @po concern #1).
    Reads last N lines to check for recent dups before appending.
    Best-effort, never raise.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        new_hash = entry.get("command_hash", "")
        new_domain = entry.get("url_domain", "")

        # Dedup check: scan existing entries for same command_hash
        # (prevents double-appending same command in same session)
        if new_hash and DISCOVERY_QUEUE.exists():
            try:
                # Read last 200 lines (bounded scan for performance)
                existing_text = DISCOVERY_QUEUE.read_text(encoding="utf-8")
                recent_lines = existing_text.splitlines()[-200:]
                for line in recent_lines:
                    try:
                        existing = json.loads(line)
                        if (
                            existing.get("command_hash") == new_hash
                            and existing.get("url_domain") == new_domain
                        ):
                            # Already logged this exact command+domain combo -> skip
                            return
                    except Exception:
                        continue
            except Exception:
                pass

        with DISCOVERY_QUEUE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    """
    Load capability_enforcement config from core-config.yaml.
    Session-scoped cache: NO reload intra-session by design (D2 in decision-log).
    If block absent or file missing -> returns defaults (enabled=False -> no-op).
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config = dict(_DEFAULT_CONFIG)
    try:
        import yaml

        raw = yaml.safe_load(CORE_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        block = raw.get("capability_enforcement") or {}
        if isinstance(block, dict):
            config.update({k: v for k, v in block.items() if k in config})
    except Exception:
        pass  # Fail-open: use defaults (enabled=False -> no-op)

    _CONFIG_CACHE = config
    return config


# ---------------------------------------------------------------------------
# OTel telemetry (best-effort, fail-open -- AC10)
# ---------------------------------------------------------------------------


def _emit_otel_span(
    event_type: str,
    capability_id: str,
    confidence: float,
    url_domain: str,
) -> None:
    """Emit OTel span for block/warn events. Fail-open."""
    try:
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from engine.intelligence.metrics.otel_capability_tracer import emit_capability_span

        emit_capability_span(
            capability_id=capability_id,
            capability_description="",
            prompt=url_domain,
            match_type=event_type,
            similarity_score=confidence,
            extra_attrs={
                "til.enforcement.capability_id": capability_id,
                "til.enforcement.confidence": confidence,
                "til.enforcement.url_domain": url_domain,
            },
        )
    except Exception:
        pass  # Fail-open always


# ---------------------------------------------------------------------------
# Main enforcement logic
# ---------------------------------------------------------------------------


def _extract_command(tool_name: str, tool_input: dict) -> str | None:
    """Extract the command/content string from tool input."""
    if tool_name == "Bash":
        return tool_input.get("command", "")
    elif tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        # For Edit: check new_string only (we care about what's being written)
        return tool_input.get("new_string", "")
    return None


def _has_url_api_pattern(content: str) -> bool:
    """Fast pre-check: does content contain any URL/API pattern? (O(n) scan)"""
    c = content.lower()
    return "http://" in c or "https://" in c or "api." in c


def _run(hook_data: dict) -> dict:
    """
    Core enforcement logic. Returns dict with 'decision' key.
    decision: "permit" | "block" | "warn"

    Fail-open contract: any exception in this function -> caller returns permit.
    """
    t0 = time.perf_counter()

    tool_name = hook_data.get("tool_name") or hook_data.get("toolName") or ""
    tool_input = hook_data.get("tool_input") or hook_data.get("toolInput") or {}
    agent_id = hook_data.get("agent_id") or hook_data.get("agentId") or "unknown"

    # Load config (session-scoped cache)
    config = _load_config()

    # No-op if enforcement disabled (AC8)
    if not config.get("enabled", False):
        return {"decision": "permit"}

    # Check bypass env var (AC4)
    bypass = os.environ.get("BYPASS_CAPABILITY_ENFORCEMENT", "").lower() in ("true", "1", "yes")
    if bypass:
        _append_metrics(
            {
                "timestamp": _now_iso(),
                "event_type": "enforcement_permit_bypass",
                "tool": tool_name,
                "agent": agent_id,
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            }
        )
        return {"decision": "permit"}

    # Extract command string
    command = _extract_command(tool_name, tool_input)
    if not command:
        return {"decision": "permit"}

    # Write/Edit fast PERMIT: if no URL/API pattern, skip entirely (AC po-concern #2)
    if tool_name in ("Write", "Edit") and not _has_url_api_pattern(command):
        return {"decision": "permit"}

    # Parse command for external API signals
    try:
        from til_enforcement.command_parser import (
            parse_bash_command,
            parse_write_edit_input,
        )

        if tool_name == "Bash":
            parse_result = parse_bash_command(command)
        else:
            parse_result = parse_write_edit_input(tool_name, tool_input)
    except Exception:
        return {"decision": "permit"}

    # No external signal -> PERMIT immediately
    if not parse_result.has_external_signal:
        return {"decision": "permit"}

    # Cross-reference against capability registry
    try:
        from til_enforcement.matcher import find_capability

        match = find_capability(
            url_domains=parse_result.url_domains,
            cli_tools=parse_result.cli_tools_detected,
            packages=parse_result.api_packages,
            capability_hints=parse_result.capability_hints,
        )
    except Exception:
        # Matcher failed -> PERMIT (fail-open)
        return {"decision": "permit"}

    cmd_hash = _command_hash(command)
    primary_domain = parse_result.primary_domain or ""

    confidence_block = config.get("confidence_block", 0.85)
    confidence_warn = config.get("confidence_warn", 0.60)
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    # No match or low confidence -> PERMIT + log to discovery queue
    if not match.capability_id or match.confidence < confidence_warn:
        if primary_domain:
            _append_discovery(
                {
                    "timestamp": _now_iso(),
                    "agent": agent_id,
                    "tool": tool_name,
                    "url_domain": primary_domain,
                    "command_hash": cmd_hash,
                }
            )
        return {"decision": "permit"}

    # Match found: enforce based on confidence tier
    if match.confidence >= confidence_block:
        # BLOCK
        _append_metrics(
            {
                "timestamp": _now_iso(),
                "event_type": "enforcement_block",
                "capability_id": match.capability_id,
                "confidence": match.confidence,
                "url_domain": primary_domain,
                "tool": tool_name,
                "agent": agent_id,
                "command_hash": cmd_hash,
                "latency_ms": latency_ms,
            }
        )
        _emit_otel_span("enforcement_block", match.capability_id, match.confidence, primary_domain)

        return {
            "decision": "block",
            "reason": (
                f"Use capability_resolver('{match.capability_id}') em vez de {tool_name} direto. "
                f"Razão: telemetria TIL-21 + drift detection + provider chain registrada. "
                f"Confiança: {match.confidence:.2f}. "
                f"Override: export BYPASS_CAPABILITY_ENFORCEMENT=true"
            ),
        }

    else:
        # WARN (0.60 <= confidence < 0.85)
        _append_metrics(
            {
                "timestamp": _now_iso(),
                "event_type": "enforcement_warn",
                "capability_id": match.capability_id,
                "confidence": match.confidence,
                "url_domain": primary_domain,
                "tool": tool_name,
                "agent": agent_id,
                "command_hash": cmd_hash,
                "latency_ms": latency_ms,
            }
        )
        _emit_otel_span("enforcement_warn", match.capability_id, match.confidence, primary_domain)

        return {
            "decision": "warn",
            "message": (
                f"[CAPABILITY HINT] Possível match: capability_resolver('{match.capability_id}') "
                f"(confiança {match.confidence:.2f}). Operação prossegue — considere usar canal registrado."
            ),
        }


def main() -> None:
    """Hook entrypoint. Reads stdin JSON, returns permit/block/warn to stdout."""
    t0 = time.perf_counter()

    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            sys.exit(0)
        try:
            hook_data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            sys.exit(0)

        result = _run(hook_data)
        decision = result.get("decision", "permit")

        if decision == "block":
            # Return block decision via JSON stdout (Claude Code PreToolUse protocol)
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": result.get("reason", "Capability enforcement block."),
                    }
                )
            )
            sys.exit(0)

        elif decision == "warn":
            # Warn: inject context but let proceed
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": result.get("message", ""),
                        }
                    }
                )
            )
            sys.exit(0)

        # PERMIT: exit 0 silently
        sys.exit(0)

    except Exception as e:
        # Fail-open: log to metrics but NEVER block
        try:
            _append_metrics(
                {
                    "timestamp": _now_iso(),
                    "event_type": "enforcement_error",
                    "error": f"{type(e).__name__}: {str(e)[:200]}",
                    "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                }
            )
        except Exception:
            pass
        # Exit 0 = PERMIT (fail-open)
        sys.exit(0)


if __name__ == "__main__":
    main()
