"""
MCE Pipeline Hooks -- Observable, non-blocking pipeline extensions
=================================================================

Hooks register themselves on the HookBus and react to pipeline events
without blocking execution.  Each hook is a self-contained module that
follows the Observer Pattern:

    hook_bus.emit("post_llm_call", payload)
        --> CostHook handler fires in a daemon thread
        --> accumulates cost data silently

Available hooks:
- **CostHook**: Tracks per-call and aggregate LLM costs via post_llm_call

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-1.9 -- Cost Hook
"""

from engine.intelligence.pipeline.mce.hooks.cost_hook import CostHook

__all__ = [
    "CostHook",
]
__version__ = "1.0.0"
