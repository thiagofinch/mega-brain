#!/usr/bin/env python3
"""
search_capabilities.py -- Natural-language capability discovery tool (TIL-19 AC2/4/5)

A CLI / library entry point that returns the top-5 capabilities from
agents/_registry/capability-registry.yaml that match a free-form query.

Usage (CLI):
    python3 .claude/hooks/search_capabilities.py "I need to create a video"

Output (stdout):
    Found N relevant capabilities:

    [1] {capability_id} ({score})
        Title: {title}
        Description: {description}
        Business context: {pra_que}
        Provider chain: {summary}

    [2] ...

Architecture:
  - Reuses the embedding cache built by build_capability_embeddings.py
    (.data/capability-embeddings.npy + capability-embeddings-meta.json).
  - Embedding contract is canonical (text-embedding-3-large, 1536d) per
    engine.intelligence.rag.embedding_config.
  - Fail-open semantics: if numpy/cache/API key are missing, falls back
    to keyword search against agents/_registry/capability-keyword-index.json.

Budget (TIL-19 AC5):
  - Warm path (cache hit): < 200ms
  - Cold path (cache miss / API call): < 2s
  - Fail-open path (keyword fallback): < 50ms

Story: TIL-19 (Tool Search + Defer-Loading)
ADR: ADR-TIL-001 (hooks dir = Python only)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
KW_INDEX_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-keyword-index.json"
DATA_DIR = PROJECT_ROOT / ".data"
EMB_PATH = DATA_DIR / "capability-embeddings.npy"
META_PATH = DATA_DIR / "capability-embeddings-meta.json"

TOP_K = 5


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_registry() -> dict | None:
    try:
        import yaml  # PyYAML
    except ImportError:
        return None
    try:
        return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return None


def _load_kw_index() -> dict | None:
    try:
        with KW_INDEX_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _normalize(text: str) -> str:
    import unicodedata

    text = (text or "").lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# Embedding search
# ---------------------------------------------------------------------------


def _embedding_search(query: str, top_k: int = TOP_K) -> list[tuple[str, float]] | None:
    """Cosine top-k via .data/capability-embeddings.npy. Returns None if unavailable."""
    try:
        import numpy as np
    except ImportError:
        return None
    if not EMB_PATH.exists() or not META_PATH.exists():
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from engine.intelligence.rag.embedding_config import DIMENSIONS, MODEL
        from engine.intelligence.rag.hybrid_index import _openai_embed
    except Exception:
        return None

    try:
        import numpy as np

        matrix = np.load(EMB_PATH)
        with META_PATH.open(encoding="utf-8") as f:
            meta = json.load(f)
        cap_ids = [c["capability_id"] for c in meta.get("capabilities", [])]
        if matrix.shape[0] != len(cap_ids) or matrix.shape[1] != int(DIMENSIONS):
            return None
    except Exception:
        return None

    try:
        qvec = _openai_embed(
            [query[:8000]], model=MODEL, api_key=api_key, dimensions=int(DIMENSIONS)
        )
        q = np.asarray(qvec[0], dtype=np.float32)
    except Exception:
        return None

    try:

        def _norm(a):
            n = np.linalg.norm(a, axis=-1, keepdims=True)
            n = np.where(n == 0, 1.0, n)
            return a / n

        mat_n = _norm(matrix)
        q_n = _norm(q[None, :])[0]
        scores = (mat_n @ q_n).astype(np.float32)
        order = np.argsort(-scores)[: max(1, top_k)]
        return [(cap_ids[int(i)], float(scores[int(i)])) for i in order]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Keyword fallback search
# ---------------------------------------------------------------------------


def _keyword_search(query: str, top_k: int = TOP_K) -> list[tuple[str, float]]:
    """Substring keyword match. Score = number of matched keywords / total keywords for the cap."""
    idx = _load_kw_index() or {}
    entries = idx.get("entries") or []
    q = _normalize(query)
    if not q:
        return []

    hits: dict[str, int] = {}
    cap_kw_counts: dict[str, int] = {}
    for e in entries:
        cid = e.get("capability_id") or ""
        kw = (e.get("keyword") or "").strip()
        if not cid or not kw:
            continue
        cap_kw_counts[cid] = cap_kw_counts.get(cid, 0) + 1
        if kw in q:
            hits[cid] = hits.get(cid, 0) + 1

    ranked = []
    for cid, n in hits.items():
        denom = max(1, cap_kw_counts.get(cid, 1))
        ranked.append((cid, float(n) / float(denom)))
    ranked.sort(key=lambda t: -t[1])
    return ranked[:top_k]


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _provider_summary(cap: dict) -> str:
    providers = cap.get("providers") or []
    if not providers:
        return "(no providers)"
    parts = []
    for p in providers:
        pid = (p or {}).get("id") or "?"
        ptype = (p or {}).get("type") or "?"
        prio = (p or {}).get("priority")
        parts.append(f"{pid}:{ptype}" + (f"@p{prio}" if prio is not None else ""))
    return " > ".join(parts)


def format_results(query: str, results: list[tuple[str, float]], registry: dict | None) -> str:
    caps = (registry or {}).get("capabilities") or {}
    if not results:
        return f'No relevant capabilities found for query: "{query}"'

    lines = [f"Found {len(results)} relevant capabilities:", ""]
    for i, (cid, score) in enumerate(results, 1):
        c = caps.get(cid) or {}
        title = (c.get("title") or cid).strip()
        desc = (c.get("description") or "").strip() or "(no description)"
        bc = c.get("business_context") or {}
        pra_que = (bc.get("pra_que") or "").strip() or "(no business context)"
        chain = _provider_summary(c)
        lines.append(f"[{i}] {cid} ({score:.3f})")
        lines.append(f"    Title: {title}")
        lines.append(f"    Description: {desc}")
        lines.append(f"    Business context: {pra_que}")
        lines.append(f"    Provider chain: {chain}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Public API + CLI
# ---------------------------------------------------------------------------


def search_capabilities(query: str, top_k: int = TOP_K) -> dict:
    """Return structured search result. Pure library entry point (no I/O side effects beyond reads).

    Returns:
        {
          "query": str,
          "mode": "embedding" | "keyword" | "empty",
          "results": [{"capability_id": str, "score": float, ...}, ...],
          "formatted": str,  # human-readable block (also printed by CLI)
        }
    """
    registry = _load_registry()
    mode = "embedding"
    pairs = _embedding_search(query, top_k=top_k)
    if pairs is None:
        mode = "keyword"
        pairs = _keyword_search(query, top_k=top_k)
        if not pairs:
            mode = "empty"
            pairs = []
    elif not pairs:
        mode = "empty"

    caps = (registry or {}).get("capabilities") or {}
    results_struct = []
    for cid, score in pairs:
        c = caps.get(cid) or {}
        results_struct.append(
            {
                "capability_id": cid,
                "score": float(score),
                "title": (c.get("title") or cid).strip(),
                "description": (c.get("description") or "").strip(),
                "pra_que": ((c.get("business_context") or {}).get("pra_que") or "").strip(),
                "provider_chain": _provider_summary(c),
            }
        )

    formatted = format_results(query, pairs, registry)
    return {"query": query, "mode": mode, "results": results_struct, "formatted": formatted}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or not argv[1].strip():
        sys.stderr.write('Usage: search_capabilities.py "<query>" [--json] [--top-k N]\n')
        return 2

    want_json = "--json" in argv
    top_k = TOP_K
    if "--top-k" in argv:
        try:
            i = argv.index("--top-k")
            top_k = max(1, int(argv[i + 1]))
        except Exception:
            pass

    query = argv[1]
    result = search_capabilities(query, top_k=top_k)

    if want_json:
        # Drop the formatted block in JSON mode for cleanliness
        payload = {k: v for k, v in result.items() if k != "formatted"}
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(result["formatted"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
