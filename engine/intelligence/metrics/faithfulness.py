"""
faithfulness.py -- Deterministic Faithfulness Scoring for Conclave Outputs
==========================================================================

Measures what percentage of an agent's conclave output is grounded in
retrieved context.  Uses string-match / token-overlap ONLY -- zero LLM calls.

Runs ASYNC after conclave completion as post-processing.  Never in the
critical path.  Never inside qa_gates.py.

Key metric: **grounded_ratio** = claims_with_source_match / total_claims.
Agents with grounded_ratio < 0.5 are flagged as "high_bias_risk".

Usage::

    from engine.intelligence.metrics.faithfulness import score_conclave

    agent_outputs = {
        "CRITIC": "The framework uses a 4-step process ...",
        "SYNTHESIZER": "Integrating the data points ...",
    }
    contexts = {
        "CRITIC": "The framework uses a 4-step process for ...",
        "SYNTHESIZER": "Various data points were collected ...",
    }
    result = score_conclave(agent_outputs, contexts)
    # => {"agents": {"CRITIC": {"grounded_ratio": 0.85, ...}, ...},
    #     "flags": [...], "session_summary": {...}}

Version: 1.0.0
Date: 2026-03-25
Story: W4.3 (Pipeline Enhancement)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("metrics.faithfulness")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIGH_BIAS_THRESHOLD = 0.5

# Stopwords -- common words that should not count as grounding evidence.
# Kept minimal and English/Portuguese-focused.  Stdlib only.
_STOPWORDS = frozenset(
    {
        # English
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "shall",
        "may",
        "might",
        "can",
        "must",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "and",
        "but",
        "or",
        "nor",
        "not",
        "no",
        "so",
        "if",
        "than",
        "too",
        "very",
        "just",
        "about",
        "up",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "he",
        "she",
        "they",
        "we",
        "you",
        "i",
        "me",
        "my",
        "your",
        "his",
        "her",
        "our",
        "their",
        "which",
        "what",
        "who",
        "whom",
        "how",
        "when",
        "where",
        "why",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "only",
        "own",
        "same",
        "also",
        # Portuguese
        "o",
        "os",
        "um",
        "uma",
        "uns",
        "umas",
        "de",
        "da",
        "das",
        "dos",
        "em",
        "na",
        "nas",
        "nos",
        "por",
        "para",
        "com",
        "sem",
        "que",
        "se",
        "mas",
        "ou",
        "como",
        "mais",
        "muito",
        "tambem",
        "ja",
        "ainda",
        "ate",
        "entre",
        "sobre",
        "depois",
        "antes",
        "aqui",
        "ali",
        "la",
        "ele",
        "ela",
        "eles",
        "elas",
        "voce",
        "eu",
        "meu",
        "seu",
        "sua",
        "isso",
        "isto",
        "esse",
        "essa",
        "este",
        "esta",
    }
)

# Minimum word length to be considered a "key term" (after stopword removal)
_MIN_TERM_LENGTH = 3

# Minimum key terms a claim must have to be scorable
_MIN_CLAIM_TERMS = 2

# Fraction of key terms that must appear in context for a claim to be grounded
_GROUNDING_TERM_RATIO = 0.5

# ---------------------------------------------------------------------------
# Tokeniser (stdlib only -- mirrors entropy.py pattern)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Z0-9\u00C0-\u024F]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenisation.  Unicode-aware, no external deps."""
    return _TOKEN_RE.findall(text.lower())


def _key_terms(text: str) -> list[str]:
    """Extract key terms: tokenise, remove stopwords, filter short words."""
    return [t for t in _tokenize(text) if t not in _STOPWORDS and len(t) >= _MIN_TERM_LENGTH]


# ---------------------------------------------------------------------------
# Sentence splitter (stdlib only)
# ---------------------------------------------------------------------------

# Split on sentence-ending punctuation followed by whitespace or end-of-string.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def extract_claims(text: str) -> list[str]:
    """Split agent output into atomic claims (sentence-level).

    Filters out very short fragments (< 2 key terms) that are
    unlikely to be meaningful claims.

    Args:
        text: Raw agent output text.

    Returns:
        List of claim strings, each a sentence-level assertion.
    """
    if not text or not text.strip():
        return []

    raw_sentences = _SENTENCE_RE.split(text.strip())
    claims = []
    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue
        # Only keep sentences with enough key terms to be meaningful
        if len(_key_terms(sent)) >= _MIN_CLAIM_TERMS:
            claims.append(sent)
    return claims


# ---------------------------------------------------------------------------
# Grounding check
# ---------------------------------------------------------------------------


def check_grounding(claim: str, context: str) -> bool:
    """Check if a claim's key terms appear in the context.

    A claim is considered grounded if at least GROUNDING_TERM_RATIO
    of its key terms are found in the context token set.

    Args:
        claim: A single atomic claim (sentence).
        context: The retrieved context that should ground this claim.

    Returns:
        True if the claim is grounded in context.
    """
    claim_terms = _key_terms(claim)
    if not claim_terms:
        return True  # vacuously grounded (no key terms to check)

    context_tokens = set(_tokenize(context.lower())) if context else set()
    if not context_tokens:
        return False  # no context => cannot be grounded

    matched = sum(1 for term in claim_terms if term in context_tokens)
    ratio = matched / len(claim_terms)
    return ratio >= _GROUNDING_TERM_RATIO


# ---------------------------------------------------------------------------
# Compute grounded ratio for a single agent
# ---------------------------------------------------------------------------


def compute_grounded_ratio(agent_output: str, retrieved_context: str) -> float:
    """Compute the fraction of claims grounded in context.

    Args:
        agent_output: Raw text output from one agent.
        retrieved_context: The context that was provided to the agent.

    Returns:
        Float in [0.0, 1.0].  1.0 = every claim is grounded.
        Returns 1.0 if no scorable claims (vacuously faithful).
    """
    claims = extract_claims(agent_output)
    if not claims:
        return 1.0  # no claims => vacuously faithful

    grounded_count = sum(1 for claim in claims if check_grounding(claim, retrieved_context))
    return round(grounded_count / len(claims), 4)


# ---------------------------------------------------------------------------
# Score entire conclave session
# ---------------------------------------------------------------------------


def score_conclave(
    agent_outputs: dict[str, str],
    contexts: dict[str, str],
) -> dict[str, Any]:
    """Compute per-agent faithfulness for a conclave session.

    Args:
        agent_outputs: Mapping of agent name to raw output text.
        contexts: Mapping of agent name to retrieved context.
            Agents missing from contexts get grounded_ratio=0.0.

    Returns:
        Structured dict::

            {
                "agents": {
                    "<name>": {
                        "grounded_ratio": float,
                        "total_claims": int,
                        "grounded_claims": int,
                        "ungrounded_claims": list[str],
                        "high_bias_risk": bool,
                    }
                },
                "flags": list[str],
                "session_summary": {
                    "mean_grounded_ratio": float,
                    "agents_scored": int,
                    "agents_flagged": int,
                },
            }
    """
    agents_result: dict[str, dict[str, Any]] = {}
    flags: list[str] = []
    total_ratio_sum = 0.0
    agents_scored = 0
    agents_flagged = 0

    for agent_name, output in agent_outputs.items():
        context = contexts.get(agent_name, "")
        claims = extract_claims(output)
        total_claims = len(claims)

        grounded_claims = 0
        ungrounded: list[str] = []

        for claim in claims:
            if check_grounding(claim, context):
                grounded_claims += 1
            else:
                ungrounded.append(claim)

        ratio = round(grounded_claims / total_claims, 4) if total_claims > 0 else 1.0
        is_high_bias = ratio < HIGH_BIAS_THRESHOLD and total_claims > 0

        agents_result[agent_name] = {
            "grounded_ratio": ratio,
            "total_claims": total_claims,
            "grounded_claims": grounded_claims,
            "ungrounded_claims": ungrounded,
            "high_bias_risk": is_high_bias,
        }

        total_ratio_sum += ratio
        agents_scored += 1

        if is_high_bias:
            agents_flagged += 1
            flags.append(
                f"HIGH_BIAS_RISK: agent '{agent_name}' has grounded_ratio="
                f"{ratio} (< {HIGH_BIAS_THRESHOLD})"
            )
            logger.warning(
                "Agent '%s' grounded_ratio=%.2f below threshold %.2f",
                agent_name,
                ratio,
                HIGH_BIAS_THRESHOLD,
            )

    mean_ratio = round(total_ratio_sum / agents_scored, 4) if agents_scored > 0 else 0.0

    result: dict[str, Any] = {
        "agents": agents_result,
        "flags": flags,
        "session_summary": {
            "mean_grounded_ratio": mean_ratio,
            "agents_scored": agents_scored,
            "agents_flagged": agents_flagged,
        },
    }

    logger.info(
        "Faithfulness scored: %d agents, mean_grounded_ratio=%.2f, flagged=%d",
        agents_scored,
        mean_ratio,
        agents_flagged,
    )

    return result


# ---------------------------------------------------------------------------
# JSONL logging (mirrors entropy.py pattern)
# ---------------------------------------------------------------------------


def log_faithfulness_jsonl(
    session_id: str,
    result: dict[str, Any],
    log_path: Path | None = None,
) -> Path | None:
    """Append faithfulness result to JSONL log.

    Non-fatal: swallows all exceptions so it never blocks the caller.

    Args:
        session_id: Unique conclave session identifier.
        result: Output from score_conclave().
        log_path: Override path for testing.  Defaults to ROUTING entry.

    Returns:
        Path to the log file, or None on error.
    """
    try:
        if log_path is None:
            from engine.paths import ROUTING

            log_path = ROUTING.get("conclave_faithfulness_log")
            if log_path is None:
                logger.error("No ROUTING entry for conclave_faithfulness_log")
                return None

        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Build serialisable entry (strip ungrounded_claims for log brevity)
        agents_summary = {}
        for name, data in result.get("agents", {}).items():
            agents_summary[name] = {
                "grounded_ratio": data["grounded_ratio"],
                "total_claims": data["total_claims"],
                "grounded_claims": data["grounded_claims"],
                "high_bias_risk": data["high_bias_risk"],
            }

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "agents": agents_summary,
            "flags": result.get("flags", []),
            "session_summary": result.get("session_summary", {}),
        }

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info("Faithfulness logged to %s", log_path)
        return log_path

    except Exception:
        logger.exception("Failed to log faithfulness (non-fatal)")
        return None
