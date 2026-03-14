#!/usr/bin/env python3
"""
ADAPTIVE CONTEXT SCORER - GAP-07 Implementation
=================================================
Replaces hard-coded 200-line memory truncation with intelligent scoring.
Connects adaptive_router intent classification with memory_manager export.

Intent -> max_chars mapping:
  greeting     -> 0 chars (no memory needed)
  meta         -> 0 chars
  factual_simple -> 2000 chars
  factual_complex -> 4000 chars
  analytical   -> 8000 chars
  cross_expert -> 8000 chars
  hierarchical -> 12000 chars

Versao: 1.0.0
Data: 2026-03-07
"""

# ---------------------------------------------------------------------------
# INTENT → CONTEXT SIZE MAPPING
# ---------------------------------------------------------------------------
INTENT_CONTEXT_MAP = {
    "greeting": 0,
    "meta": 0,
    "factual_simple": 2000,
    "factual_complex": 4000,
    "analytical": 8000,
    "cross_expert": 8000,
    "hierarchical": 12000,
}

DEFAULT_MAX_CHARS = 4000


def score_context_budget(intent: str) -> int:
    """Get the context budget (max chars) for a given intent."""
    return INTENT_CONTEXT_MAP.get(intent, DEFAULT_MAX_CHARS)


def build_adaptive_context(
    query: str,
    agent_id: str | None = None,
    intent: str | None = None,
    include_shared: bool = True,
) -> str:
    """Build context string adapted to query intent.

    Combines:
    1. Intent classification (from adaptive_router)
    2. Agent-specific memory (from memory_manager)
    3. Shared memory (cross-agent decisions)

    Returns formatted context string.
    """
    # Lazy imports to avoid circular deps
    from core.intelligence.rag.adaptive_router import classify_intent

    if intent is None:
        intent = classify_intent(query)

    max_chars = score_context_budget(intent)
    if max_chars == 0:
        return ""

    parts = []
    chars_used = 0

    # Agent-specific memory
    if agent_id:
        from core.intelligence.memory_manager import get_store

        store = get_store(agent_id)
        if store.count > 0:
            agent_budget = int(max_chars * 0.7)  # 70% for agent memory
            agent_ctx = store.export_for_context(query=query, max_chars=agent_budget)
            if agent_ctx:
                parts.append(f"## Agent Memory ({agent_id})\n{agent_ctx}")
                chars_used += len(parts[-1])

    # Shared memory
    if include_shared:
        from core.intelligence.memory_manager import get_shared_store

        shared = get_shared_store()
        if shared.count > 0:
            shared_budget = max_chars - chars_used
            if shared_budget > 500:
                shared_ctx = shared.export_for_context(query=query, max_chars=shared_budget)
                if shared_ctx:
                    parts.append(f"## Shared Decisions\n{shared_ctx}")

    return "\n\n".join(parts)


def get_context_config(query: str) -> dict:
    """Get full context configuration for a query.

    Returns dict with intent, pipeline, and context budget.
    Useful for hooks that need to decide how much context to inject.
    """
    from core.intelligence.rag.adaptive_router import (
        classify_intent,
        select_pipeline,
    )

    intent = classify_intent(query)
    pipeline = select_pipeline(query, intent)

    return {
        "query": query,
        "intent": intent,
        "pipeline": pipeline.value,
        "max_chars": score_context_budget(intent),
        "needs_retrieval": pipeline.value != "E",
        "needs_memory": score_context_budget(intent) > 0,
    }
