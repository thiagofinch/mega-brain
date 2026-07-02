"""HHEM-2.1-Open Gate — Local hallucination detection.

Integrates vectara/hallucination_evaluation_model (HuggingFace) as a
secondary gate when self_rag faithfulness < 0.60. Zero API cost.

Story: STORY-RAG-8 (S8) — Phase 2 Wave 5
Date: 2026-04-12

Model: vectara/hallucination_evaluation_model (~400MB, T5-base)
Cached at: .data/models/hhem/  (ROUTING["hhem_model"])

Architecture:
  self_rag heuristic (~1ms)        ← primary, always runs, zero-LLM
    ↓ faithfulness < 0.60
  HHEM gate (~50-200ms)            ← this module, zero API cost
    ↓ hhem_score > 0.40
  hallucination_warning = True     ← flag only, never blocks
    ↓ future Phase 2
  LLM NLI (claude-haiku-4-5)      ← ABSORB A5, not in this story

Constitution: heuristic_gate.py (TRANSCEND T2) is NEVER modified.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
HHEM_MODEL_ID = "vectara/hallucination_evaluation_model"
HHEM_TRIGGER_THRESHOLD = 0.60  # Run HHEM when faithfulness < this
HHEM_WARN_THRESHOLD = 0.40  # Flag warning when hhem_score > this


# Model cache path (ROUTING["hhem_model"])
def _model_cache_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    d = root / ".data" / "models" / "hhem"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# HHEM GATE (lazy-loaded singleton)
# ---------------------------------------------------------------------------
_pipeline = None  # HuggingFace pipeline, loaded on first use


def _load_model():
    """Lazy-load HHEM model. Raises ImportError if transformers not installed."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    try:
        from transformers import pipeline as hf_pipeline  # type: ignore[import-untyped]

        cache_dir = str(_model_cache_dir())
        _pipeline = hf_pipeline(
            "text-classification",
            model=HHEM_MODEL_ID,
            cache_dir=cache_dir,
            trust_remote_code=True,
        )
        return _pipeline
    except Exception as e:
        raise ImportError(f"HHEM model load failed: {e}") from e


def hhem_score(query: str, context: str, response: str) -> float:
    """Compute hallucination probability for a (context, response) pair.

    Uses HHEM-2.1-Open to evaluate if the response is hallucinated
    relative to the provided context.

    Args:
        query: Original user query (not used by HHEM directly, kept for API symmetry).
        context: Retrieved chunks text (source of truth).
        response: Generated response to evaluate.

    Returns:
        float in [0.0, 1.0]:
          0.0 = model says response is FAITHFUL (not hallucinated)
          1.0 = model says response is HALLUCINATED

    Returns -1.0 if model is unavailable (non-blocking).
    """
    try:
        model = _load_model()
    except ImportError:
        return -1.0  # Model not available — non-blocking

    try:
        # HHEM input format: "passage: {context} statement: {response}"
        text = f"passage: {context[:2000]} statement: {response[:1000]}"
        result = model(text, truncation=True, max_length=512)

        # HHEM output: [{"label": "hallucinated"|"consistent", "score": float}]
        if isinstance(result, list) and result:
            label = result[0].get("label", "").lower()
            score = float(result[0].get("score", 0.5))
            # If label is "consistent", hallucination probability = 1 - score
            if "consistent" in label or "factual" in label:
                return 1.0 - score
            return score
        return -1.0
    except Exception:
        return -1.0


def check_response(
    query: str,
    context: str,
    response: str,
    faithfulness_score: float,
) -> dict:
    """Run HHEM gate if faithfulness is below trigger threshold.

    Args:
        query: Original query.
        context: Retrieved context used to generate response.
        response: Generated response.
        faithfulness_score: Heuristic faithfulness from self_rag.

    Returns:
        {
            "triggered": bool,        # Was HHEM invoked?
            "hhem_score": float,      # Hallucination probability (-1 if not run)
            "hallucination_warning": bool,  # True if hhem_score > HHEM_WARN_THRESHOLD
            "available": bool,        # Is the HHEM model available?
        }
    """
    if faithfulness_score >= HHEM_TRIGGER_THRESHOLD:
        # High-confidence response — skip HHEM (zero overhead)
        return {
            "triggered": False,
            "hhem_score": -1.0,
            "hallucination_warning": False,
            "available": True,
        }

    # Faithfulness < 0.60 — invoke HHEM
    score = hhem_score(query, context, response)
    available = score >= 0.0
    warning = available and score > HHEM_WARN_THRESHOLD

    return {
        "triggered": True,
        "hhem_score": score,
        "hallucination_warning": warning,
        "available": available,
    }
