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
    """Lazy-load HHEM model. Raises ImportError if transformers not installed
    or the model cannot be instantiated.

    Loader: ``AutoModelForSequenceClassification.from_pretrained(..., trust_remote_code=True)``
    — the route Vectara publishes for HHEM-2.1-Open. The returned model exposes
    a ``.predict(text_pairs)`` API (see the model's ``modeling_hhem_v2.py``) that
    returns the probability the response is CONSISTENT with the passage.

    STORY-F0-HHEM (2026-07-02, @po Option A): the previous loader used
    ``pipeline("text-classification", ...)``, which is INCOMPATIBLE with
    transformers >= 4.5x — the pipeline tries to build an ``AutoTokenizer`` from
    ``HHEMv2Config`` and raises ``Unrecognized configuration class ... to build
    an AutoTokenizer``, so even with the model on disk the gate returned -1.0
    (non-blocking / dormant). The custom model carries its own tokenizer
    internally (from ``config.foundation``) and is invoked via ``.predict()``,
    which is the route this loader uses. Verified at runtime: load ~6s, predict
    ~62ms/pair after warmup; faithful/fabricated scores 0.34/0.99.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    try:
        from transformers import (  # type: ignore[import-untyped]
            AutoModelForSequenceClassification,
        )

        cache_dir = str(_model_cache_dir())
        _pipeline = AutoModelForSequenceClassification.from_pretrained(
            HHEM_MODEL_ID,
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
        # HHEM .predict() takes (passage, statement) pairs and returns the
        # probability the statement is CONSISTENT with the passage (in [0,1]).
        # Hallucination probability = 1 - consistency probability.
        pair = (context[:2000], response[:1000])
        raw = model.predict([pair])

        # raw is a 1-D tensor/array of consistency probabilities (one per pair).
        consistency = float(raw[0])
        if not (0.0 <= consistency <= 1.0):
            return -1.0
        return 1.0 - consistency
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
