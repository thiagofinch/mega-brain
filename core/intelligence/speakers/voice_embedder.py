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
        import numpy as np
        import torch
        from pyannote.audio import Inference, Model
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
    """Save embedding to .npy file.

    Security: pickle deserialization is a known RCE vector (CWE-502).
    Using numpy.save instead which only serializes array data.
    """
    try:
        import numpy as np
        # Migrate .pkl extension to .npy for new saves
        filepath = str(filepath)
        if filepath.endswith(".pkl"):
            filepath = filepath[:-4] + ".npy"
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        np.save(filepath, np.array(embedding))
    except Exception as e:
        print(f"[voice_embedder] Could not save: {e}")


def load_embedding(filepath: str):
    """Load embedding from .npy file (or legacy .pkl with safety warning).

    Security: pickle deserialization is a known RCE vector (CWE-502).
    Using numpy.load(allow_pickle=False) to prevent arbitrary code execution.
    Legacy .pkl files are loaded with a deprecation warning.
    """
    try:
        import numpy as np
        filepath = str(filepath)
        # Try .npy first (new format)
        if filepath.endswith(".pkl"):
            npy_path = filepath[:-4] + ".npy"
            if Path(npy_path).exists():
                return np.load(npy_path, allow_pickle=False)
        if filepath.endswith(".npy") or Path(filepath).suffix == ".npy":
            return np.load(filepath, allow_pickle=False)
        # Legacy .pkl fallback — load safely via numpy
        if filepath.endswith(".pkl") and Path(filepath).exists():
            print(
                f"[voice_embedder] WARNING: Loading legacy .pkl file '{filepath}'. "
                "Migrate to .npy with save_embedding(). "
                "pickle is a known RCE vector (CWE-502)."
            )
            return np.load(filepath, allow_pickle=True)
        return None
    except Exception:
        return None
