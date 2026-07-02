"""
coordinator_mode.py -- Coordinator Mode for mega-brain-chief
============================================================

Detects whether the MCE pipeline is active and injects the coordinator
prompt into the mega-brain-chief's system prompt.  This gives the chief
explicit synthesis rules, anti-patterns, and a decision matrix for
agent delegation.

Architecture
------------
The coordinator prompt lives in ``coordinator_prompt.md`` alongside this
module.  When pipeline is active (detected via ``PipelineStateMachine``
or ``TeammateContext``), the prompt is loaded and appended to the chief's
system prompt.

Data Flow::

    pipeline active?
         |
    YES  |  NO
     |   |   |
     v   |   v
    load prompt  |  return original prompt unchanged
     |           |
     v           |
    inject into system prompt

Public API
----------
- ``is_coordinator_mode()``           -- check if pipeline is active
- ``get_coordinator_prompt()``        -- load the coordinator prompt markdown
- ``inject_coordinator_context()``    -- append coordinator prompt to system prompt

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-1.4
"""

from __future__ import annotations

import logging
from pathlib import Path

from engine.intelligence.pipeline.mce.teammate_context import get_context

logger = logging.getLogger("mce.coordinator_mode")

# The coordinator prompt lives next to this module.
_PROMPT_PATH = Path(__file__).parent / "coordinator_prompt.md"

# Cache the prompt in memory after first load to avoid repeated disk I/O.
_prompt_cache: str | None = None


# ---------------------------------------------------------------------------
# is_coordinator_mode() -- detect pipeline activity
# ---------------------------------------------------------------------------


def is_coordinator_mode() -> bool:
    """Check whether the MCE pipeline is currently active.

    Coordinator mode is active when ALL of the following are true:

    1. A ``TeammateContext`` is set (an agent is running).
    2. The active agent is ``mega-brain-chief`` OR has ``is_lead=True``.

    This deliberately checks the context rather than a global flag so that
    the coordinator prompt is only injected into the correct agent's scope.

    Returns:
        ``True`` if the pipeline is active and the current agent is the
        coordinator, ``False`` otherwise.
    """
    ctx = get_context()
    if ctx is None:
        return False

    # The coordinator is either explicitly mega-brain-chief or any lead agent.
    if ctx.agent_id == "mega-brain-chief":
        return True

    if ctx.is_lead:
        return True

    return False


# ---------------------------------------------------------------------------
# get_coordinator_prompt() -- load markdown from disk (cached)
# ---------------------------------------------------------------------------


def get_coordinator_prompt(*, force_reload: bool = False) -> str:
    """Load the coordinator prompt from ``coordinator_prompt.md``.

    The prompt is cached in memory after the first load.  Pass
    ``force_reload=True`` to bypass the cache (useful for tests).

    Args:
        force_reload: If ``True``, re-read the file even if cached.

    Returns:
        The full coordinator prompt as a string.

    Raises:
        FileNotFoundError: If ``coordinator_prompt.md`` is missing.
    """
    global _prompt_cache

    if _prompt_cache is not None and not force_reload:
        logger.debug("Returning cached coordinator prompt (%d chars)", len(_prompt_cache))
        return _prompt_cache

    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Coordinator prompt not found at {_PROMPT_PATH}.  "
            "Ensure coordinator_prompt.md exists next to coordinator_mode.py."
        )

    _prompt_cache = _PROMPT_PATH.read_text(encoding="utf-8")
    logger.debug(
        "Loaded coordinator prompt from %s (%d chars, %d lines)",
        _PROMPT_PATH.name,
        len(_prompt_cache),
        _prompt_cache.count("\n") + 1,
    )
    return _prompt_cache


# ---------------------------------------------------------------------------
# inject_coordinator_context() -- append prompt to system prompt
# ---------------------------------------------------------------------------

# Delimiter used to mark where coordinator context begins inside
# the system prompt.  Makes it easy to detect if already injected.
_COORDINATOR_MARKER = "\n\n<!-- COORDINATOR_MODE_START -->\n"
_COORDINATOR_MARKER_END = "\n<!-- COORDINATOR_MODE_END -->\n"


def inject_coordinator_context(system_prompt: str) -> str:
    """Append the coordinator prompt to the given system prompt.

    If the pipeline is NOT active (``is_coordinator_mode()`` returns
    ``False``), the system prompt is returned unchanged.

    If the coordinator prompt is already injected (detected by the
    ``COORDINATOR_MODE_START`` marker), the system prompt is returned
    unchanged to avoid double-injection.

    Args:
        system_prompt: The base system prompt for mega-brain-chief.

    Returns:
        The enriched system prompt with coordinator context appended,
        or the original prompt if coordinator mode is not active.
    """
    if not is_coordinator_mode():
        logger.debug("Coordinator mode not active -- returning original prompt")
        return system_prompt

    # Guard against double injection.
    if _COORDINATOR_MARKER.strip() in system_prompt:
        logger.debug("Coordinator prompt already injected -- skipping")
        return system_prompt

    coordinator_prompt = get_coordinator_prompt()

    enriched = system_prompt + _COORDINATOR_MARKER + coordinator_prompt + _COORDINATOR_MARKER_END

    logger.info(
        "Coordinator context injected: +%d chars (%d total)",
        len(coordinator_prompt),
        len(enriched),
    )
    return enriched


# ---------------------------------------------------------------------------
# clear_prompt_cache() -- for testing
# ---------------------------------------------------------------------------


def clear_prompt_cache() -> None:
    """Clear the in-memory prompt cache.

    Useful in tests that need to verify re-loading behavior.
    """
    global _prompt_cache
    _prompt_cache = None
    logger.debug("Coordinator prompt cache cleared")
