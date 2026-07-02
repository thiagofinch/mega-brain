#!/usr/bin/env python3
"""
build_capability_embeddings.py -- Build semantic embedding cache for capabilities (TIL-12)

Generates two artifacts under .data/:
  - capability-embeddings.npy        : numpy float32 array, shape [N, DIMENSIONS]
  - capability-embeddings-meta.json  : {version, model, dimensions, built_at, capabilities[{index, capability_id, hash}]}

Embedding contract:
  - Provider/model/dimensions MUST come from engine.intelligence.rag.embedding_config
    (canonical per Roundtable RT-2026-04-16-001 — text-embedding-3-large @ 1536d).
  - Embedding text per capability = "{title|id}. {description}. {pra_que}"
    (NO nao_use_para — anti-pattern phrasing pollutes positive semantic match space).
  - Hash = sha256 hex of the exact embedded UTF-8 text (lets consumers detect
    drift before triggering a rebuild).

Fail-open semantics:
  - Missing OPENAI_API_KEY -> log warning, exit 0 (do NOT crash hint pipeline).
  - Missing numpy -> log warning, exit 0.
  - Missing registry -> log warning, exit 0 (Wave 0 behavior).

Mirrors the pattern of build_capability_keyword_index.py.

Story: TIL-12 (Wave 2 — Embedding Hints + LLM Re-rank)
ADR: ADR-TIL-001 (Path C — hooks dir is Python only)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
HOOK_TAG = "[build_capability_embeddings]"

# Make engine importable (canonical embedding contract lives there)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
DATA_DIR = PROJECT_ROOT / ".data"
EMB_PATH = DATA_DIR / "capability-embeddings.npy"
META_PATH = DATA_DIR / "capability-embeddings-meta.json"
STALE_SENTINEL = DATA_DIR / "capability-embeddings.stale"


def _log(msg: str) -> None:
    print(f"{HOOK_TAG} {msg}", file=sys.stderr)


def _load_canonical_embedding_config() -> tuple[str, int]:
    """Return (model, dimensions) from canonical source. Never hard-code."""
    from engine.intelligence.rag.embedding_config import DIMENSIONS, MODEL

    return MODEL, int(DIMENSIONS)


def _build_embedding_text(cap_id: str, cap: dict) -> str:
    """Concatenate title (or id), description, and business_context.pra_que.

    Intentionally EXCLUDES nao_use_para (anti-pattern text) to avoid polluting
    positive semantic space.
    """
    title = (cap.get("title") or cap_id).strip()
    description = (cap.get("description") or "").strip()
    bc = cap.get("business_context") or {}
    pra_que = (bc.get("pra_que") or "").strip()

    parts = [title]
    if description:
        parts.append(description)
    if pra_que:
        parts.append(pra_que)
    return ". ".join(parts)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    # --- Imports guarded for fail-open ---
    try:
        import numpy as np
    except ImportError:
        _log("numpy not installed; skipping embedding cache build (fail-open).")
        return 0

    try:
        import yaml
    except ImportError:
        _log("PyYAML not installed; skipping (fail-open).")
        return 0

    # --- Canonical embedding contract ---
    try:
        model, dimensions = _load_canonical_embedding_config()
    except Exception as e:
        _log(f"Failed to load canonical embedding config: {e}; aborting (fail-open).")
        return 0

    # --- API key gate ---
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        _log("OPENAI_API_KEY missing/empty; skipping embedding cache build (fail-open).")
        return 0

    # --- Registry ---
    if not REGISTRY_PATH.exists():
        _log(f"Registry not found at {REGISTRY_PATH}; nothing to embed (fail-open).")
        return 0

    try:
        registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        _log(f"YAML parse failed: {e}; aborting (fail-open).")
        return 0

    capabilities = registry.get("capabilities", {}) or {}
    if not capabilities:
        _log("Registry has no capabilities; nothing to embed.")
        return 0

    # Stable order for reproducibility (matches numpy row index)
    cap_ids = sorted(capabilities.keys())
    texts: list[str] = []
    hashes: list[str] = []
    for cid in cap_ids:
        text = _build_embedding_text(cid, capabilities[cid])
        texts.append(text)
        hashes.append(_sha256_hex(text))

    # --- Embedding via canonical helper ---
    try:
        from engine.intelligence.rag.hybrid_index import _openai_embed
    except Exception as e:
        _log(f"Failed to import canonical _openai_embed: {e}; aborting (fail-open).")
        return 0

    try:
        vectors = _openai_embed(texts, model=model, api_key=api_key, dimensions=dimensions)
    except Exception as e:
        _log(f"Embedding API call failed: {e}; aborting (fail-open).")
        return 0

    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.shape != (len(cap_ids), dimensions):
        _log(
            f"Shape mismatch: got {matrix.shape}, expected ({len(cap_ids)}, {dimensions}); aborting."
        )
        return 0

    # --- Persist artifacts ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMB_PATH, matrix)

    meta = {
        "version": "1.0.0",
        "model": model,
        "dimensions": dimensions,
        "built_at": datetime.now(UTC).isoformat(),
        "capabilities": [
            {"index": i, "capability_id": cid, "hash": f"sha256:{hashes[i]}"}
            for i, cid in enumerate(cap_ids)
        ],
    }
    META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # Clear the stale sentinel (rebuild is fresh)
    if STALE_SENTINEL.exists():
        try:
            STALE_SENTINEL.unlink()
        except OSError:
            pass

    _log(
        f"built {len(cap_ids)} embeddings ({model}, {dimensions}d) -> {EMB_PATH.name} + {META_PATH.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
