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

Versao: 1.1.0
Data: 2026-03-07
Updated: 2026-05-27 [Story MCE-11.10] — cross-expert slot injection
"""

import os
import re

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

# ---------------------------------------------------------------------------
# CROSS-EXPERT INTENT CLASSIFICATION (MCE-11.10)
# ---------------------------------------------------------------------------

# Keywords that signal a cross-expert comparison intent.
# Broader set than adaptive_router's cross_expert patterns — covers PT-BR + EN.
_CROSS_EXPERT_KEYWORDS: list[str] = [
    "compare",
    "comparar",
    "comparacao",
    "comparison",
    "vs",
    "versus",
    "outros experts",
    "outros especialistas",
    "other experts",
    "perspectiva",
    "perspectivas",
    "perspective",
    "o que outros",
    "what others",
    "consensus",
    "consenso",
    "convergencia",
    "convergence",
    "divergencia",
    "divergence",
    "quem mais",
    "who else",
    "outros pensam",
    "think about",
    "pensam sobre",
    "concordam",
    "agree",
    "discordam",
    "disagree",
    "visao de outros",
    "other views",
]

# Compiled regex: matches any keyword (word-boundary safe for multi-word phrases)
_CROSS_EXPERT_RE = re.compile(
    r"(?:" + "|".join(re.escape(kw) for kw in _CROSS_EXPERT_KEYWORDS) + r")",
    re.IGNORECASE,
)


def _classify_cross_expert_intent(query: str) -> bool:
    """Return True when the query indicates a cross-expert comparison intent.

    Used by build_adaptive_context() to decide whether to populate the
    cross_expert slot.  Threshold: any single keyword match triggers injection.

    Args:
        query: The raw user query string.

    Returns:
        True if cross-expert intent detected, False otherwise.
    """
    return bool(_CROSS_EXPERT_RE.search(query))


# ---------------------------------------------------------------------------
# CROSS-EXPERT CONFIG (MCE-11.10)
# ---------------------------------------------------------------------------


def _load_cross_expert_config() -> dict:
    """Load cross-expert configuration from YAML file.

    Falls back to sensible defaults if config file is absent or malformed.
    Config file: engine/config/cross-expert-config.yaml
    """
    # Read threshold from env first — allows runtime override without file edit
    env_threshold = os.environ.get("MCE_CROSS_EXPERT_THRESHOLD")

    defaults: dict = {
        "similarity_threshold": float(env_threshold) if env_threshold else 0.65,
        "max_chars": 8000,
        "enabled_for": ["person-agents", "cargo-agents"],
        "auto_inject_on_intent": True,
    }

    try:
        import pathlib

        # Resolve config path relative to repo root (portable — no hardcoded user path)
        repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
        config_path = repo_root / "engine" / "config" / "cross-expert-config.yaml"

        if not config_path.exists():
            return defaults

        # PyYAML is stdlib-adjacent — already used by hooks
        import yaml  # type: ignore[import]

        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        cfg = data.get("cross_expert", {})

        # Env var overrides file threshold
        threshold = (
            float(env_threshold)
            if env_threshold
            else float(cfg.get("similarity_threshold", defaults["similarity_threshold"]))
        )

        return {
            "similarity_threshold": threshold,
            "max_chars": int(cfg.get("max_chars", defaults["max_chars"])),
            "enabled_for": cfg.get("enabled_for", defaults["enabled_for"]),
            "auto_inject_on_intent": bool(
                cfg.get("auto_inject_on_intent", defaults["auto_inject_on_intent"])
            ),
        }
    except Exception:
        return defaults


# ---------------------------------------------------------------------------
# CROSS-EXPERT SLOT FORMATTER (MCE-11.10)
# ---------------------------------------------------------------------------


def _format_cross_expert_connections(raw: dict, max_chars: int, threshold: float) -> str:
    """Format find_cross_expert_connections() output into the slot string.

    Filters results by PPR similarity score >= threshold.
    Wraps in visual delimiters per AC4.
    Truncates to max_chars.

    Args:
        raw: dict returned by find_cross_expert_connections()
        max_chars: Maximum characters for the slot (default 8000)
        threshold: Minimum PPR score to include a result

    Returns:
        Formatted string, or "" if no results pass threshold.
    """
    cross = raw.get("cross_expert", {})
    if not cross:
        return ""

    lines: list[str] = []
    for person, entries in cross.items():
        for entry in entries:
            score = entry.get("score", 0.0)
            if score < threshold:
                continue
            label = entry.get("label", "").strip()
            entity_type = entry.get("entity_type", "")
            source_id = entry.get("entity_id", "")
            if label:
                lines.append(
                    f"[{person}] [{entity_type}] {label}  (score={score:.4f}, id={source_id})"
                )

    if not lines:
        return ""

    content = "\n".join(lines)
    # Delimiters per AC4
    block = f"--- PERSPECTIVAS CROSS-EXPERT ---\n{content}\n--- FIM PERSPECTIVAS ---"

    # Truncate to budget (preserve delimiters)
    if len(block) > max_chars:
        # Truncate content, keep closing delimiter
        closing = "\n--- FIM PERSPECTIVAS ---"
        header = "--- PERSPECTIVAS CROSS-EXPERT ---\n"
        available = max_chars - len(header) - len(closing)
        truncated_content = content[: max(0, available)]
        block = f"{header}{truncated_content}{closing}"

    return block


# ---------------------------------------------------------------------------
# CORE FUNCTIONS
# ---------------------------------------------------------------------------


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
    4. Cross-expert connections (MCE-11.10) — injected silently when intent detected

    Returns formatted context string.
    """
    # Lazy imports to avoid circular deps
    from engine.intelligence.rag.adaptive_router import classify_intent

    if intent is None:
        intent = classify_intent(query)

    max_chars = score_context_budget(intent)
    if max_chars == 0:
        return ""

    parts = []
    chars_used = 0

    # Agent-specific memory
    if agent_id:
        from engine.intelligence.memory_manager import get_store

        store = get_store(agent_id)
        if store.count > 0:
            agent_budget = int(max_chars * 0.7)  # 70% for agent memory
            agent_ctx = store.export_for_context(query=query, max_chars=agent_budget)
            if agent_ctx:
                parts.append(f"## Agent Memory ({agent_id})\n{agent_ctx}")
                chars_used += len(parts[-1])

    # Shared memory
    if include_shared:
        from engine.intelligence.memory_manager import get_shared_store

        shared = get_shared_store()
        if shared.count > 0:
            shared_budget = max_chars - chars_used
            if shared_budget > 500:
                shared_ctx = shared.export_for_context(query=query, max_chars=shared_budget)
                if shared_ctx:
                    parts.append(f"## Shared Decisions\n{shared_ctx}")
                    chars_used += len(parts[-1])

    # Cross-expert injection (MCE-11.10)
    # Triggered when: (a) intent already classified as cross_expert by adaptive_router,
    # OR (b) keyword scan detects cross-expert comparison signal in raw query.
    cfg = _load_cross_expert_config()
    if cfg.get("auto_inject_on_intent", True):
        is_cross_expert = (intent == "cross_expert") or _classify_cross_expert_intent(query)
        if is_cross_expert:
            try:
                from engine.intelligence.rag.associative_memory import find_cross_expert_connections

                # source_person: extract from agent_id slug if available
                # e.g. "alex-hormozi" → "alex-hormozi"
                source_person = agent_id if agent_id else None

                raw = find_cross_expert_connections(
                    concept=query,
                    source_person=source_person,
                )

                slot_budget = min(
                    cfg.get("max_chars", 8000),
                    max_chars - chars_used,
                )
                if slot_budget > 100:
                    cross_ctx = _format_cross_expert_connections(
                        raw,
                        max_chars=slot_budget,
                        threshold=cfg.get("similarity_threshold", 0.65),
                    )
                    if cross_ctx:
                        parts.append(cross_ctx)
            except Exception:
                # Graceful fallback per AC6 — never break context building
                pass

    return "\n\n".join(parts)


def get_context_config(query: str) -> dict:
    """Get full context configuration for a query.

    Returns dict with intent, pipeline, and context budget.
    Useful for hooks that need to decide how much context to inject.
    """
    from engine.intelligence.rag.adaptive_router import (
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
