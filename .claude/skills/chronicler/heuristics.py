#!/usr/bin/env python3
"""
Chronicler Truth-Amplifier Heuristics — 6 Rules
================================================

Each rule reads payload + history and returns either:
  None  — no warning needed
  str   — warning banner string to prepend to the canonical box

Rules are applied by the render() dispatcher before wrapping the output.

STORY-MCE-6.0 Phase 4 (2026-05-22).
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Rule 1: Gates failed
# ---------------------------------------------------------------------------


def heuristic_gates_failed(payload: dict, history: list[dict]) -> str | None:
    """If gates_passed < gates_total → red header warning.

    Signal: payload.metrics.gates.{passed, total}
    """
    gates = payload.get("metrics", {}).get("gates", {})
    if not gates:
        return None
    passed = gates.get("passed", 0) or 0
    total = gates.get("total", 0) or 0
    if total > 0 and passed < total:
        failed = total - passed
        return f"⚠ {failed} gate(s) FAILED — see detail below  [heuristic: gates_failed]"
    return None


# ---------------------------------------------------------------------------
# Rule 2: Contradictions
# ---------------------------------------------------------------------------


def heuristic_contradictions(payload: dict, history: list[dict]) -> str | None:
    """If contradictions_count > 0 in metrics → warning.

    Signal: payload.metrics.contradictions_count OR payload.metrics.contradictions
    """
    m = payload.get("metrics", {})
    count = (
        m.get("contradictions_count")
        or m.get("contradictions")
        or (len(m.get("contradiction_list", [])))
        or 0
    )
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 0

    if count > 0:
        return (
            f"⚠ {count} contradiction(s) detected in this phase  [heuristic: contradictions]"
        )
    return None


# ---------------------------------------------------------------------------
# Rule 3: Embeddings regression
# ---------------------------------------------------------------------------


def heuristic_embeddings_regression(payload: dict, history: list[dict]) -> str | None:
    """If current embeddings < previous embeddings for same slug → regression warning.

    Signal: payload.metrics.embeddings vs history[-1].metrics.embeddings (same slug)
    """
    m = payload.get("metrics", {})
    curr = m.get("embeddings") or m.get("embeddings_count")
    if curr is None:
        return None

    slug = payload.get("slug", "")
    prev_entry = None
    for h in reversed(history):
        if h.get("slug") == slug and h.get("template_id") == payload.get("template_id"):
            prev_entry = h
            break

    if not prev_entry:
        return None

    prev_m = prev_entry.get("metrics", {})
    prev = prev_m.get("embeddings") or prev_m.get("embeddings_count")
    if prev is None:
        return None

    try:
        if int(curr) < int(prev):
            drop = int(prev) - int(curr)
            return (
                f"⚠ Embeddings regression: {curr} < {prev} (dropped {drop})  "
                f"[heuristic: embeddings_regression]"
            )
    except (TypeError, ValueError):
        pass
    return None


# ---------------------------------------------------------------------------
# Rule 4: Slow phase
# ---------------------------------------------------------------------------


def heuristic_slow_phase(payload: dict, history: list[dict]) -> str | None:
    """If duration_s > 300 (5 min) for a single phase → slow warning.

    Signal: payload.metrics.duration_s
    """
    m = payload.get("metrics", {})
    dur = m.get("duration_s")
    if dur is None:
        dur_ms = m.get("duration_ms")
        if dur_ms is not None:
            dur = float(dur_ms) / 1000.0

    if dur is None:
        return None

    try:
        dur_f = float(dur)
    except (TypeError, ValueError):
        return None

    if dur_f > 300:
        return (
            f"⚠ Slow phase: {dur_f:.0f}s (threshold: 300s)  [heuristic: slow_phase]"
        )
    return None


# ---------------------------------------------------------------------------
# Rule 5: Zero insights on long source
# ---------------------------------------------------------------------------


def heuristic_zero_insights_long_source(payload: dict, history: list[dict]) -> str | None:
    """If insights == 0 AND source_minutes >= 30 → quality warning.

    Long source (>=30 min) that yielded zero insights is suspicious.
    Signal: payload.metrics.insights, payload.metrics.source_minutes
    """
    m = payload.get("metrics", {})
    insights = m.get("insights") or m.get("insights_count") or m.get("person_insights", 0) or 0
    source_minutes = m.get("source_minutes", 0) or 0

    try:
        insights = int(insights)
        source_minutes = float(source_minutes)
    except (TypeError, ValueError):
        return None

    if insights == 0 and source_minutes >= 30:
        return (
            f"⚠ Zero insights on {source_minutes:.0f}min source — check extraction quality  "
            f"[heuristic: zero_insights_long_source]"
        )
    return None


# ---------------------------------------------------------------------------
# Rule 6: Routing unverified
# ---------------------------------------------------------------------------


def heuristic_routing_unverified(payload: dict, history: list[dict]) -> str | None:
    """If routing_verified is explicitly False in metrics → warning.

    Signal: payload.metrics.routing_verified == False
    """
    m = payload.get("metrics", {})
    routing_verified = m.get("routing_verified")

    # Only trigger if explicitly set to False (None = not applicable)
    if routing_verified is False:
        bucket = m.get("bucket", "?")
        slug = payload.get("slug", "?")
        return (
            f"⚠ Routing unverified for {slug} → bucket:{bucket}  "
            f"[heuristic: routing_unverified]"
        )
    return None


# ---------------------------------------------------------------------------
# Aggregator — called by render() dispatcher
# ---------------------------------------------------------------------------

_ALL_HEURISTICS = [
    heuristic_gates_failed,
    heuristic_contradictions,
    heuristic_embeddings_regression,
    heuristic_slow_phase,
    heuristic_zero_insights_long_source,
    heuristic_routing_unverified,
]


def check_all_heuristics(payload: dict, history: list[dict]) -> list[str]:
    """Run all 6 heuristics and return a list of warning banners (may be empty).

    Args:
        payload: current PHASE-STREAM.jsonl entry
        history: previous entries for context

    Returns:
        List of warning banner strings (empty if all rules pass).
    """
    warnings = []
    for rule_fn in _ALL_HEURISTICS:
        try:
            result = rule_fn(payload, history)
            if result:
                warnings.append(result)
        except Exception as exc:
            # Heuristics must never crash the render pipeline
            warnings.append(
                f"⚠ Heuristic {rule_fn.__name__} raised: {exc}  [heuristic: internal_error]"
            )
    return warnings
