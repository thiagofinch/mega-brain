"""
entropy.py -- Multi-agent Entropy Measurement
==============================================

Measures whether conclave / roundtable agents produce meaningfully
different outputs or collapse into echo chambers.

Three metrics (all 0-1 floats, stdlib only):

- **convergence_score**: How much agents agree (pairwise Jaccard,
  averaged).  High = echo chamber risk.
- **dominance_index**: Whether one agent's output dwarfs the others
  (longest / mean length ratio, normalised).  High = one voice drowns
  the rest.
- **output_diversity**: Lexical diversity across the combined corpus
  (unique-tokens / total-tokens).  Low = agents recycling the same
  vocabulary.

Usage::

    from engine.intelligence.metrics.entropy import compute_entropy_metrics

    outputs = {
        "CRITIC": "The reasoning is methodologically sound ...",
        "DEVILS-ADVOCATE": "The weakest premise is ...",
        "SYNTHESIZER": "Integrating both perspectives ...",
    }
    metrics = compute_entropy_metrics(outputs)
    # => {"convergence_score": 0.32, "dominance_index": 0.15,
    #     "output_diversity": 0.74, "flags": [], "agent_stats": {...}}

Version: 1.0.0
Date: 2026-03-25
Story: W3.2 (Pipeline Enhancement)
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("metrics.entropy")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOMINANCE_THRESHOLD = 0.7
CONVERGENCE_THRESHOLD = 0.9

# ---------------------------------------------------------------------------
# Tokeniser (stdlib only — simple whitespace + punctuation split)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Z0-9\u00C0-\u024F]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenisation.  Unicode-aware, no external deps."""
    return _TOKEN_RE.findall(text.lower())


# ---------------------------------------------------------------------------
# Pairwise Jaccard similarity
# ---------------------------------------------------------------------------


def _jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard similarity between two token sets.  Returns 0.0 if both empty."""
    if not set_a and not set_b:
        return 1.0  # two empty outputs are trivially identical
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 1.0
    return intersection / union


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convergence_score(agent_outputs: dict[str, str]) -> float:
    """Measure how much agents agree (0-1).

    Computes pairwise Jaccard similarity of tokenised outputs and returns
    the average.  A score near 1.0 means agents are essentially saying the
    same thing (echo chamber signal).

    Args:
        agent_outputs: Mapping of agent name to output text.

    Returns:
        Float in [0, 1].  Higher = more agreement.
    """
    names = list(agent_outputs.keys())
    if len(names) < 2:
        return 1.0  # single agent trivially agrees with itself

    token_sets: dict[str, set[str]] = {
        name: set(_tokenize(text)) for name, text in agent_outputs.items()
    }

    pair_count = 0
    total_sim = 0.0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            total_sim += _jaccard(token_sets[names[i]], token_sets[names[j]])
            pair_count += 1

    return round(total_sim / pair_count, 4) if pair_count > 0 else 1.0


def dominance_index(agent_outputs: dict[str, str]) -> float:
    """Measure whether one agent dominated the session (0-1).

    Ratio of the longest output's token count to the mean token count,
    normalised into [0, 1].  A score near 1.0 means one agent produced
    far more content than the others.

    Normalisation: ``(max / mean - 1) / (n - 1)`` where *n* is the number
    of agents.  This maps the theoretical range [1, n] of max/mean to [0, 1].

    Args:
        agent_outputs: Mapping of agent name to output text.

    Returns:
        Float in [0, 1].  Higher = more dominance.
    """
    if len(agent_outputs) < 2:
        return 0.0

    lengths = [len(_tokenize(text)) for text in agent_outputs.values()]
    max_len = max(lengths)
    mean_len = sum(lengths) / len(lengths)

    if mean_len == 0:
        return 0.0  # all outputs empty

    ratio = max_len / mean_len  # in [1, n]
    n = len(agent_outputs)
    # Normalise [1, n] -> [0, 1]
    normalised = (ratio - 1) / (n - 1) if n > 1 else 0.0
    return round(min(max(normalised, 0.0), 1.0), 4)


def output_diversity(agent_outputs: dict[str, str]) -> float:
    """Measure lexical diversity across all outputs (0-1).

    Ratio of unique tokens to total tokens across the combined corpus.
    A score near 1.0 means each word appears only once (high diversity).
    A score near 0.0 means heavy repetition.

    Args:
        agent_outputs: Mapping of agent name to output text.

    Returns:
        Float in [0, 1].  Higher = more diverse vocabulary.
    """
    all_tokens: list[str] = []
    for text in agent_outputs.values():
        all_tokens.extend(_tokenize(text))

    if not all_tokens:
        return 0.0

    unique_count = len(set(all_tokens))
    return round(unique_count / len(all_tokens), 4)


def compute_entropy_metrics(agent_outputs: dict[str, str]) -> dict[str, Any]:
    """Aggregate all entropy metrics for a conclave session.

    Args:
        agent_outputs: Mapping of agent name to raw output text.

    Returns:
        Structured dict with scores, per-agent stats, and flags::

            {
                "convergence_score": float,
                "dominance_index": float,
                "output_diversity": float,
                "flags": list[str],
                "agent_stats": {
                    "<name>": {"token_count": int, "unique_tokens": int}
                },
            }
    """
    conv = convergence_score(agent_outputs)
    dom = dominance_index(agent_outputs)
    div = output_diversity(agent_outputs)

    # Per-agent stats
    agent_stats: dict[str, dict[str, int]] = {}
    for name, text in agent_outputs.items():
        tokens = _tokenize(text)
        agent_stats[name] = {
            "token_count": len(tokens),
            "unique_tokens": len(set(tokens)),
        }

    # Flags
    flags: list[str] = []
    if dom > DOMINANCE_THRESHOLD:
        # Find the dominant agent
        dominant = max(agent_stats, key=lambda k: agent_stats[k]["token_count"])
        flags.append(
            f"HIGH_DOMINANCE: agent '{dominant}' produced disproportionate output "
            f"(dominance_index={dom})"
        )
        logger.warning("Dominance index %.2f exceeds threshold %.2f", dom, DOMINANCE_THRESHOLD)

    if conv > CONVERGENCE_THRESHOLD:
        flags.append(f"ECHO_CHAMBER: agents converging excessively " f"(convergence_score={conv})")
        logger.warning("Convergence score %.2f exceeds threshold %.2f", conv, CONVERGENCE_THRESHOLD)

    result: dict[str, Any] = {
        "convergence_score": conv,
        "dominance_index": dom,
        "output_diversity": div,
        "flags": flags,
        "agent_stats": agent_stats,
    }

    logger.info(
        "Entropy metrics: convergence=%.2f, dominance=%.2f, diversity=%.2f, flags=%d",
        conv,
        dom,
        div,
        len(flags),
    )

    return result
