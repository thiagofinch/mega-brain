"""
Voice Embedder — Extracts a unique embedding vector from an audio segment.
Uses pyannote.audio SpeakerEmbedding when available.
"""
from pathlib import Path


def extract_embedding(audio_file: str, segment_start: float = None, segment_end: float = None):
    """
    Extract speaker embedding from audio file (or segment thereof).
    Returns numpy array or None if pyannote not available.
    """
    try:
        import torch
        import numpy as np
        from pyannote.audio import Model, Inference
        from pyannote.core import Segment

        model = Model.from_pretrained("pyannote/embedding",
                                      use_auth_token=False)
        inference = Inference(model, window="whole")

        if segment_start is not None and segment_end is not None:
            embedding = inference.crop(audio_file,
                                       Segment(segment_start, segment_end))
        else:
            embedding = inference(audio_file)
        return embedding
    except ImportError:
        return None
    except Exception as e:
        print(f"[voice_embedder] Warning: {e}")
        return None


def cosine_similarity(a, b) -> float:
    """Cosine similarity between two embedding vectors."""
    try:
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
    except Exception:
        return 0.0


def save_embedding(embedding, filepath: str):
    """Save embedding to .pkl file."""
    try:
        import pickle
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(embedding, f)
    except Exception as e:
        print(f"[voice_embedder] Could not save: {e}")


def load_embedding(filepath: str):
    """Load embedding from .pkl file."""
    try:
        import pickle
        with open(filepath, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None
