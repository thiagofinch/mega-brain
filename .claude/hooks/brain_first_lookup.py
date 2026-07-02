#!/usr/bin/env python3
"""
Brain-First Lookup Hook -- PreToolUse
======================================
Intercepts tool calls that might trigger external API lookups and ensures
the local brain is queried FIRST via the brain_first_gate.

When a tool call contains a query-like pattern (search terms, knowledge
requests), this hook runs brain_first_retrieve and prints a summary so the
LLM can incorporate local results before reaching for external tools.

Hook: PreToolUse (matcher: all tools) | Timeout: 10s
Story: W4-001.4
AC: Hook exists, gate implemented with 4 steps

EXIT CODES:
  0 -- ALLOW (always, this hook never blocks -- it informs)

ERROR HANDLING: fail-OPEN
  - Internal exceptions -> exit(0) ALLOW
"""

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Tool input extraction
# ---------------------------------------------------------------------------


def _get_tool_input() -> dict:
    """Read tool input from stdin (Claude Code hook protocol)."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _extract_query(tool_input: dict) -> str | None:
    """Extract a query string from the tool input if it looks like a search.

    Returns None if this tool call is not a search/lookup action.
    """
    tool_name = tool_input.get("tool_name", "")

    # Only intercept tools that look like external lookups
    search_tools = {
        "WebSearch",
        "WebFetch",
        "web_search",
        "web_fetch",
        "tavily_search",
        "exa_search",
        "google_search",
        "bing_search",
        "perplexity_search",
    }

    if tool_name not in search_tools:
        return None

    # Extract query from common parameter names
    tool_params = tool_input.get("tool_input", {})
    if isinstance(tool_params, str):
        try:
            tool_params = json.loads(tool_params)
        except (json.JSONDecodeError, TypeError):
            return tool_params if len(tool_params) > 5 else None

    for key in ("query", "search_query", "q", "url", "prompt", "question"):
        val = tool_params.get(key)
        if val and isinstance(val, str) and len(val) > 3:
            return val

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        tool_input = _get_tool_input()
        query = _extract_query(tool_input)

        if not query:
            # Not a search tool -- let it through silently
            sys.exit(0)

        # Attempt brain-first retrieval
        try:
            from engine.intelligence.retrieval.brain_first_gate import (
                brain_first_retrieve,
            )

            result = brain_first_retrieve(query, top_k=5)

            if result.results and result.source != "none":
                count = len(result.results)
                print(
                    f"[BrainFirst] Local hit: {count} results from "
                    f"{result.source} (top_score={result.top_score:.2f}, "
                    f"{result.elapsed_ms:.0f}ms). "
                    f"Consider using local knowledge before external API."
                )
            elif result.needs_external:
                print(
                    f"[BrainFirst] Local sources insufficient "
                    f"(top_score={result.top_score:.2f}). "
                    f"External lookup proceeding."
                )
            # If no results and no external flag, stay silent

        except ImportError:
            # BrainEngine not available -- hook is optional
            pass
        except Exception as e:
            # fail-OPEN: never block on internal errors
            print(f"[BrainFirst] gate error (non-blocking): {str(e)[:80]}")

    except Exception:
        # Absolute fail-OPEN: never crash the hook chain
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
