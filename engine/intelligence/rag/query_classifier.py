"""TF-IDF + SVM Query Classifier for bucket routing.

Classifies queries to knowledge buckets (external/business/personal).
Used as a hint by bucket_query_router.py for LOW confidence decisions.

Story: STORY-RAG-10 (S10) — Phase 2 Wave 6
Date: 2026-04-12

Model: TF-IDF (1-2gram, 5000 features) + LinearSVC — 93.1% accuracy
Trained by: scripts/train_query_classifier.py
Model path: .data/models/query_classifier/classifier.joblib

TRANSCEND T5 preserved:
  bucket_query_router.py heuristics are the authority.
  This classifier provides a hint for LOW confidence decisions only.
  classifier_confidence >= 0.70 → use classifier bucket as hint
  classifier_confidence < 0.70  → heuristics take full control

RAGRouter-Bench reference: TF-IDF+SVM at 93.2% accuracy (Compare S14-C3).
"""

from __future__ import annotations

import warnings
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[3] / ".data" / "models" / "query_classifier"
_classifier = None  # Lazy-loaded singleton


def _load_model():
    """Lazy-load classifier. Returns None if unavailable."""
    global _classifier
    if _classifier is not None:
        return _classifier

    model_path = MODEL_DIR / "classifier.joblib"
    if not model_path.exists():
        return None

    try:
        import joblib  # type: ignore

        _classifier = joblib.load(model_path)
        return _classifier
    except Exception as e:
        warnings.warn(f"[QueryClassifier] model load failed: {e}", stacklevel=2)
        return None


def classify_query(text: str) -> tuple[str, float]:
    """Classify a query to its target knowledge bucket.

    Args:
        text: The query string.

    Returns:
        (bucket, confidence) where bucket is "external"|"business"|"personal"
        and confidence is in [0.0, 1.0].
        Returns ("external", 0.0) if model is unavailable (safe fallback).
    """
    model = _load_model()
    if model is None:
        return ("external", 0.0)  # Safe fallback to most-populated bucket

    try:
        # LinearSVC doesn't have predict_proba; use decision_function for confidence
        decision = model.decision_function([text])[0]
        predicted_idx = decision.argmax()
        classes = model.classes_

        # Normalize decision scores to [0,1] confidence
        exp_scores = [max(0.0, d) for d in decision]
        total = sum(exp_scores) or 1.0
        confidence = exp_scores[predicted_idx] / total

        # Cap to [0.50, 1.0] range (LinearSVC confidence is not calibrated)
        confidence = min(1.0, max(0.50, confidence))

        return (str(classes[predicted_idx]), round(confidence, 3))
    except Exception:
        return ("external", 0.0)


# ---------------------------------------------------------------------------
# PUBLIC CONSTANTS (for consumers)
# ---------------------------------------------------------------------------
HIGH_CONFIDENCE_THRESHOLD = 0.70  # >= this → use classifier directly
# < this  → defer to heuristics
