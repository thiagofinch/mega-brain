#!/usr/bin/env python3
"""
HYBRID INDEX - Phase 3.2
=========================
Dual-strategy indexing: vector (canonical embedding gateway, OpenAI/1536) + BM25.

Vector backend: pgvector via store_resolver (PgVectorStore on Supabase OR
PostgresStore on generic Postgres). When a backend IS configured but its query
fails, that error is RAISED — never silently masked by a local-JSON re-search
(STORY-GBA-F1.4: silent-degrade removed). The legacy local-JSON vector path
survives ONLY as the BM25-only fallback for the zero-backend OSS clone, where
no Postgres is configured at all.

Versao: 1.2.0
Data: 2026-04-12
Changelog: S1 voyage-4, S2 pgvector integration (local JSON fallback preserved),
           W5 migrated embeddings to OpenAI/1536, F0.2 consolidated on gateway,
           F1.4 removed silent Postgres->JSON fallback (fail-loud on backend error)
"""

import json
import math
import os
import time
from collections import Counter
from pathlib import Path

from .chunker import Chunk, chunk_all, content_sha
from .embedding_config import get_embedding_config


# Dense vector backend — resolved by env via store_resolver (STORY-GBA-F1.2).
# Imported lazily to avoid crashing if no backend (DATABASE_URL/SUPABASE_URL)
# is configured. The resolver picks PostgresStore (DATABASE_URL) or
# PgVectorStore (SUPABASE_URL); when neither is set it raises
# StoreResolutionError, which we degrade to None to keep the BM25-only path.
def _get_pgvector_store(bucket: str = "external"):
    """Return the resolved VectorStore if a backend is configured, else None."""
    try:
        from .store_resolver import get_vector_store, is_any_backend_configured

        if not is_any_backend_configured():
            return None
        return get_vector_store(bucket=bucket)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Auto-load .env if OPENAI_API_KEY not in environment (canonical embedding key).
# STORY-GBA-F0.2: this previously pre-loaded VOYAGE_API_KEY, a key the OpenAI/1536
# embedding path never reads — stale dead code. The path resolves OPENAI_API_KEY
# via get_config below; this loader now warms the matching key into os.environ.
if not os.environ.get("OPENAI_API_KEY"):
    _env_file = BASE_DIR / ".env"
    if _env_file.exists():
        for _line in _env_file.read_text().splitlines():
            if _line.startswith("OPENAI_API_KEY=") and not _line.startswith("#"):
                os.environ["OPENAI_API_KEY"] = _line.split("=", 1)[1].strip()
                break
INDEX_DIR = BASE_DIR / ".data" / "rag_index"
VECTOR_INDEX_FILE = INDEX_DIR / "vectors.json"
BM25_INDEX_FILE = INDEX_DIR / "bm25.json"
CHUNKS_FILE = INDEX_DIR / "chunks.json"

# STORY-RAW-3 (EPIC-RAG-RAW-INDEXATION): raw transcript embeddings written by the
# ingest pipeline live under .data/artifacts/embeddings/<slug>/BATCH-*-embeddings.json.
# These are the 1536d vectors already computed for the raw chunks that STORY-RAW-1
# made index-visible. RAW-3 reuses them by content_sha so a durable rebuild of a
# just-ingested transcript costs 0 OpenAI calls and restores chunks==vectors parity.
ARTIFACTS_EMBEDDINGS_DIR = BASE_DIR / ".data" / "artifacts" / "embeddings"

# Default bucket for a raw-embedding slug — mirrors chunker.SOURCE_BUCKET
# ["artifacts_chunks"]="external" (the common case: external expert transcripts).
# Only artifact embeddings whose resolved bucket matches the bucket being built
# are seeded, preserving Art. XIII isolation.
_ARTIFACT_EMBEDDING_DEFAULT_BUCKET = "external"

# Embedding config resolved from canonical source (embedding_config.py)
_emb_cfg = get_embedding_config()
EMBEDDING_PROVIDER = _emb_cfg["provider"]
EMBEDDING_MODEL = _emb_cfg["model"]
EMBEDDING_DIM = _emb_cfg["dimensions"]

OPENAI_BATCH_SIZE = 100  # Max items per Embeddings API call (W5 migration from Voyage)


# ---------------------------------------------------------------------------
# BM25 LOCAL INDEX
# ---------------------------------------------------------------------------
class BM25Index:
    """Simple BM25 index using term frequencies."""

    def __init__(self):
        self.doc_freqs: dict[str, int] = {}  # term -> num docs containing it
        self.doc_lengths: list[int] = []
        self.avg_doc_length: float = 0.0
        self.term_freqs: list[dict[str, int]] = []  # per-doc term frequencies
        self.n_docs: int = 0
        self.k1: float = 1.5
        self.b: float = 0.75

    def build(self, documents: list[str]) -> None:
        """Build BM25 index from document texts."""
        self.n_docs = len(documents)
        self.doc_freqs = {}
        self.doc_lengths = []
        self.term_freqs = []

        for doc in documents:
            tokens = _tokenize(doc)
            tf = Counter(tokens)
            self.term_freqs.append(dict(tf))
            self.doc_lengths.append(len(tokens))

            for term in set(tokens):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avg_doc_length = sum(self.doc_lengths) / max(self.n_docs, 1)

    def query(self, query_text: str, top_k: int = 30) -> list[tuple[int, float]]:
        """Search BM25 index. Returns [(doc_index, score), ...]."""
        query_tokens = _tokenize(query_text)
        scores: list[float] = [0.0] * self.n_docs

        for term in query_tokens:
            if term not in self.doc_freqs:
                continue
            df = self.doc_freqs[term]
            idf = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)

            for i in range(self.n_docs):
                tf = self.term_freqs[i].get(term, 0)
                if tf == 0:
                    continue
                dl = self.doc_lengths[i]
                norm_tf = (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_doc_length, 1))
                )
                scores[i] += idf * norm_tf

        # Top-k
        indexed_scores = [(i, s) for i, s in enumerate(scores) if s > 0]
        indexed_scores.sort(key=lambda x: -x[1])
        return indexed_scores[:top_k]

    def to_dict(self) -> dict:
        return {
            "doc_freqs": self.doc_freqs,
            "doc_lengths": self.doc_lengths,
            "avg_doc_length": self.avg_doc_length,
            "term_freqs": self.term_freqs,
            "n_docs": self.n_docs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BM25Index":
        idx = cls()
        idx.doc_freqs = data["doc_freqs"]
        idx.doc_lengths = data["doc_lengths"]
        idx.avg_doc_length = data["avg_doc_length"]
        idx.term_freqs = data["term_freqs"]
        idx.n_docs = data["n_docs"]
        return idx


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer: lowercase, split on non-alphanum, filter short."""
    import re

    tokens = re.findall(r"[a-z\u00e0-\u024f]{2,}", text.lower())
    return tokens


# ---------------------------------------------------------------------------
# VECTOR INDEX (OpenAI text-embedding-3-large / 1536d)
# ---------------------------------------------------------------------------
def _openai_embed(
    texts: list[str], model: str, api_key: str, dimensions: int = EMBEDDING_DIM
) -> list[list[float]]:
    """Call OpenAI Embeddings API. Returns list of embedding vectors.

    S2a fix (2026-04-24, DECISION-F1):
    text-embedding-3-large defaults to 3072d. We explicitly pass `dimensions`
    from canonical config (1536d) to produce reduced-dim vectors matching
    metadata.json and Supabase pgvector schema. Without this param, API emits
    3072d vectors while metadata/Supabase expect 1536/1024 → silent mismatch
    that breaks cosine similarity.
    Ref: docs/stories/epic-rag-integrity-recovery/DECISION-F1.md

    Timeout fix (2026-06-01, liam-ottley ingest):
    Migrated from urllib.request.urlopen → requests.post with separate
    (connect, read) timeouts. urllib `timeout=120` was not enforced on TLS
    keep-alive hangs (TCP ESTABLISHED but no data flow → 8min+ stall observed).
    requests enforces both connect (10s) and read (120s) timeouts properly.
    Symptom that motivated fix: cmd_rag_index stalled on batch 1/45 forever.
    """
    import requests

    payload = {"input": texts, "model": model, "dimensions": dimensions}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    resp = requests.post(
        "https://api.openai.com/v1/embeddings",
        json=payload,
        headers=headers,
        timeout=(10, 120),  # (connect, read) — read timeout enforced on TLS keep-alive
    )
    resp.raise_for_status()
    data = resp.json()
    vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
    # Sanity check: API must return dim matching our request
    if vectors and len(vectors[0]) != dimensions:
        raise ValueError(
            f"OpenAI returned dim={len(vectors[0])} but requested dim={dimensions} — "
            f"possible API regression or account restriction"
        )
    return vectors


class VectorIndex:
    """Vector similarity index using OpenAI text-embedding-3-large (1536d)."""

    def __init__(self):
        self.vectors: list[list[float]] = []
        self.dim: int = EMBEDDING_DIM
        # STORY-GBA-W2.4: model:dim provenance of the loaded artifact. None until
        # set by from_dict (legacy artifact) or stamped at to_dict (write time).
        self.signature: str | None = None

    def build(self, texts: list[str], batch_size: int = OPENAI_BATCH_SIZE) -> None:
        """Build vector index by embedding all texts via OpenAI API.

        Full-rebuild path (incremental=False default upstream). Embeds every
        text from scratch. Behavior unchanged — delegates to _embed_texts which
        preserves the exact batching, backoff, and zero-vector fallback contract.
        """
        self.vectors = []

        from engine.config import get_config

        api_key = get_config("OPENAI_API_KEY")
        if not api_key:
            print("[VectorIndex] OPENAI_API_KEY not set — using zero vectors as fallback.")
            self.vectors = [[0.0] * self.dim for _ in texts]
            return

        self.vectors = self._embed_texts(texts, api_key, batch_size)

    def _embed_texts(
        self, texts: list[str], api_key: str, batch_size: int = OPENAI_BATCH_SIZE
    ) -> list[list[float]]:
        """Embed a list of texts via OpenAI, batched, with 429 backoff.

        Returns a list of vectors aligned 1:1 to ``texts`` (same order, same
        length). On per-batch failure, fills that batch with zero vectors —
        identical to the legacy inline loop so the full-rebuild path is
        bit-for-bit unchanged. Used by both build() (all texts) and
        build_incremental() (only the EMBED delta).
        """
        out: list[list[float]] = []
        if not texts:
            return out

        total_batches = math.ceil(len(texts) / batch_size)

        # Batch embed with exponential backoff on 429
        for i in range(0, len(texts), batch_size):
            batch_num = i // batch_size
            batch = texts[i : i + batch_size]
            batch = [t[:8000] for t in batch]

            max_retries = 5
            for attempt in range(max_retries):
                try:
                    out.extend(_openai_embed(batch, EMBEDDING_MODEL, api_key))
                    print(
                        f"[VectorIndex] Batch {batch_num + 1}/{total_batches} embedded ({len(batch)} chunks)"
                    )
                    break
                except Exception as e:
                    is_rate_limit = "429" in str(e) or "Too Many Requests" in str(e)
                    if is_rate_limit and attempt < max_retries - 1:
                        wait = min(2**attempt * 2, 60)  # 2s, 4s, 8s, 16s, 32s
                        print(
                            f"[VectorIndex] Batch {batch_num + 1}/{total_batches} rate-limited, retrying in {wait}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait)
                    else:
                        print(
                            f"[VectorIndex] Batch {batch_num + 1}/{total_batches} failed after {attempt + 1} attempts: {e}"
                        )
                        out.extend([[0.0] * self.dim for _ in batch])
                        break

            if i + batch_size < len(texts):
                time.sleep(1.0)  # rate-limit guard between successful batches

        return out

    def build_incremental(
        self,
        texts: list[str],
        prior_map: dict[str, list[float]],
        batch_size: int = OPENAI_BATCH_SIZE,
    ) -> dict:
        """Build the vector list incrementally, reusing prior vectors by content_sha.

        STORY-MCE-INCREMENTAL-RAG-INDEX. Embeds ONLY texts whose content_sha is
        absent from ``prior_map`` (or whose cached vector fails the 1536d guard);
        reuses the cached vector for the rest. The output list is assembled in the
        EXACT order of ``texts`` with a strict 1:1 length invariant —
        ``len(self.vectors) == len(texts)`` by construction. This is the single
        most important correctness property: it preserves the positional
        vector[i] <-> chunk[i] contract the Art. XV gate and query() rely on, and
        self-heals any prior drift because every chunk ends with exactly one vector.

        Args:
            texts: new full chunk-text set, in chunk order.
            prior_map: {content_sha -> vector} from the existing index.
            batch_size: OpenAI embeddings batch size.

        Returns:
            Stats dict: {reused, embedded, total}.
        """
        from engine.config import get_config

        # Resolve identity + reuse-eligibility per text, preserving order.
        shas = [content_sha(t) for t in texts]

        def _reusable(sha: str) -> list[float] | None:
            vec = prior_map.get(sha)
            if vec is None:
                return None
            # 1536d invariant (DECISION-F1 / AC8): a cached vector with the wrong
            # dimension is a cache MISS — re-embed rather than poison the file.
            if not isinstance(vec, list) or len(vec) != self.dim:
                return None
            return vec

        # Indices (into texts) that must be embedded fresh.
        embed_positions = [i for i, sha in enumerate(shas) if _reusable(sha) is None]

        api_key = get_config("OPENAI_API_KEY")
        if not api_key:
            # No key: fall back to zero vectors for the EMBED set, reuse the rest.
            # Still length-invariant.
            print(
                "[VectorIndex] OPENAI_API_KEY not set — incremental embed uses zero "
                "vectors for new/changed chunks."
            )
            fresh = {i: [0.0] * self.dim for i in embed_positions}
        else:
            embed_texts = [texts[i] for i in embed_positions]
            fresh_vectors = self._embed_texts(embed_texts, api_key, batch_size)
            fresh = dict(zip(embed_positions, fresh_vectors, strict=True))

        # Assemble strictly in new-chunk order. Every position is filled exactly
        # once — either from prior_map (reuse) or from the fresh embed set.
        assembled: list[list[float]] = []
        for i, sha in enumerate(shas):
            if i in fresh:
                assembled.append(fresh[i])
            else:
                reused = _reusable(sha)
                # _reusable cannot be None here: positions where it was None are
                # exactly embed_positions, all of which are in `fresh`.
                assembled.append(reused)  # type: ignore[arg-type]

        self.vectors = assembled
        stats = {
            "reused": len(texts) - len(embed_positions),
            "embedded": len(embed_positions),
            "total": len(texts),
        }
        # STORY-B1: expose the last incremental reuse stats so callers (the
        # rebuild script) can report "reused N/M by content_sha" without
        # re-deriving it. Pure read-side attribute; no behavior change.
        self._last_incremental_stats = stats
        return stats

    def query(
        self, query_text: str, top_k: int = 30, bucket: str = "external"
    ) -> list[tuple[int, float]]:
        """Search by vector similarity. Returns [(doc_index, score), ...].

        Resolution (STORY-GBA-F1.4 — no silent degrade):

        * A vector backend IS configured (``pgstore is not None``): pgvector is
          the production path. If embedding or ``pgstore.search`` fails, the
          exception PROPAGATES — a configured-but-broken Postgres is a real
          fault, not a cue to fall back. Silently re-searching a stale local
          JSON index here would hide outages and serve wrong results.
        * NO backend configured (``pgstore is None``): this is the zero-config
          OSS clone. Only here may we use the local-JSON vector path, which is
          the BM25-only fallback's vector companion.
        """
        from engine.config import get_config

        api_key = get_config("OPENAI_API_KEY")

        # -- Production path: a backend is resolved → fail-loud on any error --
        pgstore = _get_pgvector_store(bucket)
        if pgstore is not None:
            if not api_key:
                raise RuntimeError(
                    "Vector backend is configured but OPENAI_API_KEY is missing — "
                    "cannot embed the query. Set OPENAI_API_KEY; refusing to fall "
                    "back to the local JSON index (STORY-GBA-F1.4: no silent degrade)."
                )
            # Let embedding/search exceptions propagate: a configured backend that
            # fails is an explicit error, NOT a trigger for a JSON re-search.
            query_vec = _openai_embed([query_text[:8000]], EMBEDDING_MODEL, api_key)[0]
            results = pgstore.search(query_vec, top_k=top_k)
            return [(i, r.score) for i, r in enumerate(results)]

        # -- Zero-backend OSS path: local JSON vectors (BM25-only companion) --
        if not self.vectors:
            return []

        if not api_key:
            return []

        try:
            query_vec = _openai_embed([query_text[:8000]], EMBEDDING_MODEL, api_key)[0]
        except Exception:
            return []

        # Cosine similarity against local JSON vectors
        scores = []
        for i, doc_vec in enumerate(self.vectors):
            sim = _cosine_sim(query_vec, doc_vec)
            if sim > 0:
                scores.append((i, sim))

        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]

    def to_dict(self) -> dict:
        """Serialize the vector artifact, stamping the ``model:dim`` signature.

        STORY-GBA-W2.4 (D2): every embedding artifact now carries a top-level
        ``signature`` (``model:dim``, e.g. ``text-embedding-3-large:1536``)
        recording the embedding space it was produced in. This is the provenance
        the drift quarantine in ``_load_prior_vector_map`` reads to decide
        whether prior vectors are still reuse-eligible. Resolved fresh from the
        canonical gateway at write time so the stamp always reflects the config
        that actually produced these vectors.

        Zero schema change to ``content_hashes`` — the signature is a single
        extra key on ``vectors.json`` only.
        """
        from .embedding_config import get_artifact_signature

        return {
            "vectors": self.vectors,
            "dim": self.dim,
            "signature": get_artifact_signature(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VectorIndex":
        idx = cls()
        idx.vectors = data.get("vectors", [])
        idx.dim = data.get("dim", EMBEDDING_DIM)
        # Legacy artifacts (pre-W2.4) have no signature → None. The loader treats
        # a missing signature as STALE (re-embed), so we surface it as-is here.
        idx.signature = data.get("signature")
        return idx


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# ARTIFACT EMBEDDING REUSE (STORY-RAW-3 — EPIC-RAG-RAW-INDEXATION)
# ---------------------------------------------------------------------------
def _artifact_signature_ok(embedding_model: object) -> bool:
    """Signature quarantine for an artifact embedding envelope (AC-4).

    The artifact stamps ``embedding_model`` as ``"<model>@<dim>d"`` (e.g.
    ``"text-embedding-3-large@1536d"``), a different surface form than the
    running config's ``model:dim`` signature (``"text-embedding-3-large:1536"``).
    We do NOT string-compare the two forms; we assert the artifact was produced
    by the SAME model at the SAME dimension as the active embedding space:

      * the active model id is a substring of the artifact's ``embedding_model``
        (``text-embedding-3-large`` ⊂ ``text-embedding-3-large@1536d``), and
      * the active dimension appears as ``@<dim>d`` (or ``:<dim>``) in the stamp.

    A stamp that is missing, malformed, or from a different model/dimension is
    rejected — its vectors are not reuse-eligible (no cross-space contamination,
    NO FALLBACK to a fabricated vector). Per-vector ``len == EMBEDDING_DIM`` is
    re-checked downstream in ``build_incremental._reusable`` as a second guard.
    """
    if not isinstance(embedding_model, str) or not embedding_model:
        return False
    model = EMBEDDING_MODEL
    dim = EMBEDDING_DIM
    if model not in embedding_model:
        return False
    return f"@{dim}d" in embedding_model or f":{dim}" in embedding_model


def _load_artifact_embedding_map(bucket: str) -> dict[str, list[float]]:
    """Build {content_sha -> vector} from ``.data/artifacts/embeddings/<slug>/``.

    STORY-RAW-3. The ingest pipeline persists the raw transcript chunks'
    already-computed 1536d embeddings under
    ``.data/artifacts/embeddings/<slug>/BATCH-*-embeddings.json``. Each item
    carries the verbatim ``text`` it was embedded from, so the reuse key is
    ``content_sha(text)`` — IDENTICAL to the key ``build_incremental`` derives
    from the raw chunk's text (both go through ``chunker.content_sha``). This is
    the join that lets a durable rebuild reuse these vectors instead of paying
    the OpenAI Embeddings API again (0 calls for an unchanged transcript).

    Isolation (Art. XIII): a slug is seeded ONLY when its routed bucket
    (``person_paths.resolve_bucket(slug)``) equals ``bucket``. A business-routed
    slug's embeddings never seed an external build, and vice versa — exactly the
    routing ``chunk_all`` applies to the matching raw chunks (chunker.py:1157).

    Quarantine (AC-4): an envelope whose ``embedding_model`` fails
    ``_artifact_signature_ok`` is skipped wholesale (wrong space). Any individual
    item whose vector is not a length-``EMBEDDING_DIM`` list is skipped.

    Idempotency: keyed by ``content_sha``; re-reading the same artifacts (or
    overlapping re-ingest batches with identical text) yields identical keys →
    last-writer-wins is safe (same text ⇒ same vector). Returns ``{}`` when the
    artifacts dir is absent (zero-config clone / fresh install) — the caller then
    behaves exactly as pre-RAW-3 (full embed).
    """
    if not ARTIFACTS_EMBEDDINGS_DIR.exists():
        return {}

    # Same per-slug router chunk_all uses, so the seeded content_shas correspond
    # to chunks that actually land in THIS bucket (lazy import: avoid a circular
    # import with the pipeline.mce layer; mirrors chunker.py:1146).
    try:
        from engine.intelligence.pipeline.mce.person_paths import resolve_bucket
    except Exception:  # pragma: no cover — defensive: never block the rebuild
        resolve_bucket = None  # type: ignore[assignment]

    emb_map: dict[str, list[float]] = {}

    for slug_dir in sorted(ARTIFACTS_EMBEDDINGS_DIR.iterdir()):
        if not slug_dir.is_dir() or slug_dir.name.startswith(("_", ".")):
            continue
        slug = slug_dir.name

        if resolve_bucket is not None:
            try:
                slug_bucket = resolve_bucket(slug)
            except Exception:  # pragma: no cover — defensive
                slug_bucket = _ARTIFACT_EMBEDDING_DEFAULT_BUCKET
        else:
            slug_bucket = _ARTIFACT_EMBEDDING_DEFAULT_BUCKET

        if slug_bucket != bucket:
            continue  # Art. XIII: only this bucket's slugs seed this build.

        for artifact_file in sorted(slug_dir.glob("BATCH-*-embeddings.json")):
            try:
                with open(artifact_file, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, json.JSONDecodeError):
                # Unparseable artifact → skip (NO FALLBACK); the chunk re-embeds.
                continue

            if not isinstance(data, dict):
                continue
            if not _artifact_signature_ok(data.get("embedding_model")):
                continue  # signature quarantine — wrong space, not reuse-eligible.

            items = data.get("embeddings", [])
            if not isinstance(items, list):
                continue

            for it in items:
                if not isinstance(it, dict):
                    continue
                text = it.get("text")
                vec = it.get("embedding")
                if not isinstance(text, str) or not text:
                    continue
                if not isinstance(vec, list) or len(vec) != EMBEDDING_DIM:
                    continue  # per-vector dim guard (second half of AC-4).
                emb_map[content_sha(text)] = vec

    return emb_map


# ---------------------------------------------------------------------------
# HYBRID INDEX
# ---------------------------------------------------------------------------
class HybridIndex:
    """Combined vector + BM25 index with local JSON storage."""

    def __init__(self):
        self.chunks: list[dict] = []
        self.bm25 = BM25Index()
        self.vector = VectorIndex()
        self.built: bool = False

    @classmethod
    def build_for_bucket(
        cls,
        bucket: str,
        skip_vectors: bool = True,
        incremental: bool = False,
        index_dir: Path | None = None,
    ) -> "HybridIndex":
        """Build a HybridIndex scoped to a single bucket.

        S1 fix (2026-04-24, DECISION-F3): this is the canonical entry point
        for per-bucket rebuilds invoked by rebuild.py and MCE pipeline
        cmd_finalize. Uses chunker.chunk_all() (F3=B canonical pipeline)
        and filters by Chunk.bucket attribute (Art. XIII isolation).

        Args:
            bucket: "external" | "business" | "personal"
            skip_vectors: If True (default), only build BM25. Set False for
                full vector embedding (requires OPENAI_API_KEY).
            incremental: If True (STORY-MCE-INCREMENTAL-RAG-INDEX), reuse prior
                vectors by content_sha and embed only new/changed chunks. Requires
                ``index_dir`` (the bucket's on-disk index) to load prior state.
                Default False = full rebuild, behavior bit-for-bit unchanged (AC9).
            index_dir: The bucket's index directory. Required for incremental;
                Art. XIII isolation is preserved because only this single bucket
                dir is read/written.

        Returns:
            HybridIndex instance populated with chunks from the specified
            bucket only. Caller is responsible for calling .save(bucket_dir).
        """
        if bucket not in ("external", "business", "personal"):
            raise ValueError(f"Invalid bucket '{bucket}'. Must be: external | business | personal")

        all_chunks = chunk_all()
        filtered = [c for c in all_chunks if c.bucket == bucket]

        if not filtered:
            # Empty bucket is valid (e.g. fresh install) — still return an
            # empty index so save() produces empty-but-valid JSON files.
            idx = cls()
            idx.built = True
            return idx

        idx = cls()
        idx.build(
            filtered,
            skip_vectors=skip_vectors,
            incremental=incremental,
            index_dir=index_dir,
            bucket=bucket,
        )
        return idx

    def build(
        self,
        chunks: list[Chunk] | None = None,
        skip_vectors: bool = False,
        incremental: bool = False,
        index_dir: Path | None = None,
        bucket: str | None = None,
    ) -> dict:
        """Build both indexes from chunks.

        Args:
            chunks: List of Chunk objects. If None, chunks entire KB.
            skip_vectors: If True, only build BM25 (faster, no API calls).
            incremental: If True (and not skip_vectors), reuse existing vectors
                keyed by content_sha — embedding ONLY new/changed chunks. Requires
                ``index_dir`` to locate the prior chunks.json + vectors.json.
                Default False reproduces the full-rebuild path bit-for-bit (AC9).
            index_dir: Bucket index directory used to load prior state when
                ``incremental=True``. Ignored otherwise.
            bucket: Bucket being built ("external" | "business" | "personal").
                STORY-RAW-3: threaded so ``_load_prior_vector_map`` can pre-seed
                the prior map with this bucket's raw artifact embeddings (only
                that bucket's slugs — Art. XIII). ``None`` (legacy callers /
                whole-KB builds) skips artifact seeding, preserving prior behavior.

        Returns stats dict.
        """
        if chunks is None:
            chunks = chunk_all()

        # ---- STORY-A1: content_sha write-gate (deterministic keep-first dedup) --
        # The builder used to map chunks 1:1 into `texts`/`self.chunks` with zero
        # uniqueness check, so the same text arriving via two source paths was
        # indexed twice (~45% of the business index was structural duplication).
        # We now drop the 2nd+ occurrence of any `content_sha` already seen,
        # keeping the FIRST occurrence in input order. This is deterministic
        # (same input order -> same kept set) and POSITIONAL: `texts`,
        # `self.chunks` and the vectors built from them stay aligned at index i
        # because we filter all three from the SAME single pass.
        #
        # Backward-compat (RN-7): a chunk whose `content_sha` is missing/empty
        # (legacy or hand-built) is NEVER deduped — it always survives — so this
        # gate can only remove provable exact-content duplicates, never crash on
        # an item lacking the key.
        deduped_chunks: list[Chunk] = []
        texts: list[str] = []
        seen_sha: set[str] = set()
        dup_dropped = 0
        sample_dropped_sha: list[str] = []
        for c in chunks:
            sha = content_sha(c.text) if c.text else ""
            if sha and sha in seen_sha:
                dup_dropped += 1
                if len(sample_dropped_sha) < 5:
                    sample_dropped_sha.append(sha)
                continue
            if sha:
                seen_sha.add(sha)
            deduped_chunks.append(c)
            texts.append(c.text)

        chunks = deduped_chunks
        self.chunks = [c.to_dict() for c in chunks]

        if dup_dropped:
            import sys as _sys

            print(
                f"[dedup] {dup_dropped + len(chunks)} chunks → {len(chunks)} únicos "
                f"({dup_dropped} duplicados descartados; "
                f"amostra content_sha={sample_dropped_sha})",
                file=_sys.stderr,
            )

        # BM25
        t0 = time.time()
        self.bm25.build(texts)
        bm25_time = time.time() - t0

        # Vector
        vector_time = 0.0
        vector_stats: dict = {}
        if not skip_vectors:
            t0 = time.time()
            if incremental:
                prior_map = self._load_prior_vector_map(index_dir, bucket=bucket)
                vector_stats = self.vector.build_incremental(texts, prior_map)
            else:
                self.vector.build(texts)
            vector_time = time.time() - t0

        self.built = True
        return {
            "total_chunks": len(chunks),
            "bm25_time_s": round(bm25_time, 2),
            "vector_time_s": round(vector_time, 2),
            "vectors_built": not skip_vectors,
            "incremental": incremental and not skip_vectors,
            "vector_stats": vector_stats,
        }

    def _load_prior_vector_map(
        self, index_dir: Path | None, bucket: str | None = None
    ) -> dict[str, list[float]]:
        """Build {content_sha -> vector} from prior on-disk state for reuse.

        STORY-MCE-INCREMENTAL-RAG-INDEX. Reads the bucket's existing chunks.json
        and vectors.json and zips them **only up to min(len)** — this is exactly
        how prior drift is quarantined: when chunks(53558) > vectors(49732), the
        3,826 trailing chunks have no entry in the map and fall into EMBED,
        reconciling the drift on the first incremental run (AC4).

        STORY-RAW-3 (pre-seed): when ``bucket`` is given, the map is FIRST seeded
        with this bucket's raw artifact embeddings (``.data/artifacts/embeddings/
        <slug>/BATCH-*-embeddings.json``, keyed by ``content_sha(text)`` via
        :func:`_load_artifact_embedding_map`), THEN overlaid by the on-disk
        prior map. The raw chunks that STORY-RAW-1 made index-visible but which
        have no entry in the old ``vectors.json`` (the chunks≠vectors gap) are
        thereby reused from disk instead of re-embedded — 0 OpenAI calls,
        ``len(vectors)==len(chunks)`` restored. The on-disk prior wins on key
        collisions (identical text ⇒ identical vector, so precedence is benign).
        ``bucket=None`` reproduces the exact pre-RAW-3 map (no seeding).

        Falls back to an empty map (=> full embed) when:
          - index_dir is None or missing
          - chunks.json or vectors.json is absent (first build / BM25-only history)
          - files are unparseable

        Collision-hardening (AC: edge case): if a prior chunk dict carries a
        stored content_sha that does NOT match the sha recomputed from its stored
        text, that entry is skipped (treated as a miss) — cheap guard against a
        stale/forged sha mapping to the wrong vector.

        Signature quarantine (STORY-GBA-W2.4): the artifact's ``model:dim``
        signature is compared against the running config's signature BEFORE any
        per-chunk reuse. If they differ — a model or dimension swap — the entire
        prior map is discarded ({} => re-embed everything), because vectors from
        a different embedding space are not reuse-eligible no matter how many
        content_shas still match. Legacy artifacts (pre-W2.4) carry no signature;
        the absence is treated as STALE (default: re-embed) — we cannot prove a
        signature-less artifact came from the current space, and silently reusing
        it is exactly the cross-space contamination this story exists to prevent.
        This extends the existing content_sha hit criterion (W2.3): a vector is
        reusable iff content_sha matches AND signature matches.
        """
        # ---- STORY-RAW-3 artifact seed (this bucket), computed up front ------
        # The artifact embedding map is keyed on content_sha(text) of the EXACT
        # text each vector was embedded from (chunker.content_sha) — it is
        # positionally exact by construction, unlike the on-disk prior whose
        # reuse-eligibility is a positional zip (the documented drift quarantine
        # below). Computed here so it can both (a) survive every early-return as
        # the sole reuse source on a first/short build, and (b) OVERLAY the
        # on-disk prior at the end so a content_sha present in both resolves to
        # the artifact's exact vector. Overlay is strictly safe: identical text
        # ⇒ identical OpenAI vector, so the artifact entry can only CORRECT a
        # drifted positional on-disk entry, never corrupt a correct one. This
        # also self-heals legacy chunks↔vectors positional drift for any chunk
        # whose raw embedding is on disk.
        artifact_seed: dict[str, list[float]] = (
            _load_artifact_embedding_map(bucket) if bucket else {}
        )

        d = index_dir or INDEX_DIR
        chunks_path = d / "chunks.json"
        vectors_path = d / "vectors.json"

        if not chunks_path.exists() or not vectors_path.exists():
            return dict(artifact_seed)

        try:
            with open(chunks_path, encoding="utf-8") as f:
                prior_chunks = json.load(f)
            with open(vectors_path, encoding="utf-8") as f:
                prior_vec_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return dict(artifact_seed)

        prior_vectors = prior_vec_data.get("vectors", []) if isinstance(prior_vec_data, dict) else []
        if not isinstance(prior_chunks, list) or not isinstance(prior_vectors, list):
            return dict(artifact_seed)

        # ---- Signature quarantine (STORY-GBA-W2.4) -------------------------
        # Reject the WHOLE on-disk prior map on a model:dim mismatch (or a legacy
        # signature-less artifact). This is the single comparison point for the
        # signature half of the W2.3 hit criterion — keeping it here (artifact
        # granularity, D2) means neither build_incremental nor the ingestion
        # _reuse_partition need a second signature check: a mismatch simply
        # yields an empty prior map, forcing a full re-embed in both paths.
        # (STORY-RAW-3: a stale on-disk signature discards only the on-disk
        # contribution; the artifact seed stands on its own already-quarantined
        # signature check, so reuse of fresh raw embeddings is not lost.)
        from .embedding_config import get_artifact_signature

        prior_signature = (
            prior_vec_data.get("signature") if isinstance(prior_vec_data, dict) else None
        )
        if prior_signature != get_artifact_signature():
            return dict(artifact_seed)

        prior_map: dict[str, list[float]] = {}
        # Quarantine drift: only the first min(len) positions are reuse-eligible.
        for chunk, vec in zip(prior_chunks, prior_vectors, strict=False):
            if not isinstance(chunk, dict) or not isinstance(vec, list):
                continue
            text = chunk.get("text", "")
            sha = chunk.get("content_sha") or content_sha(text)
            # Collision/staleness guard: stored sha must match the embedded text.
            if sha != content_sha(text):
                continue
            # Last-writer-wins on duplicate sha is fine — identical text => identical
            # OpenAI vector, so either entry is correct.
            prior_map[sha] = vec

        # STORY-RAW-3: overlay the content_sha-exact artifact seed LAST so it wins
        # on any collision with the positional on-disk prior (correcting legacy
        # drift; identical-text guarantee makes this overlay correctness-preserving).
        prior_map.update(artifact_seed)

        return prior_map

    def save(self, index_dir: Path | None = None) -> None:
        """Save index to disk.

        Defensive behavior (bug fix 2026-04-24): if self.vector.vectors is
        empty (BM25-only rebuild), DO NOT overwrite an existing vectors.json
        that has content. Otherwise the smoke test `rebuild --bucket X`
        (default skip_vectors=True) silently invalidates an expensive
        full rebuild.
        """
        d = index_dir or INDEX_DIR
        d.mkdir(parents=True, exist_ok=True)

        with open(d / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False)

        with open(d / "bm25.json", "w", encoding="utf-8") as f:
            json.dump(self.bm25.to_dict(), f)

        vectors_path = d / "vectors.json"
        if self.vector.vectors:
            with open(vectors_path, "w", encoding="utf-8") as f:
                json.dump(self.vector.to_dict(), f)
        elif vectors_path.exists():
            # Preserve existing vectors.json — this save is BM25-only.
            import sys

            print(
                f"[HybridIndex.save] WARN: vectors empty, preserving existing "
                f"{vectors_path.name} (size={vectors_path.stat().st_size}). "
                f"Use rebuild --full to regenerate vectors.",
                file=sys.stderr,
            )
        else:
            # Fresh index, no existing file — write empty placeholder
            with open(vectors_path, "w", encoding="utf-8") as f:
                json.dump(self.vector.to_dict(), f)

        # ── metadata.json live-count stamp (PART A / STORY-EXTERNAL-CONSOLIDATION) ──
        # Root cause of the phantom 395/4988/7826 chunk-count ambiguity: the rich
        # metadata.json (rebuilt_at, embedding_*, snapshot, ...) was ONLY written by
        # scripts/rebuild_all_indexes.py. Every other save path — incremental,
        # targeted re-index, BM25-only — funnels through THIS .save() and left
        # metadata.json untouched, so the sidecar "chunks" silently drifted from the
        # real chunks.json length. Stamping the live count here makes the sidecar
        # self-consistent on EVERY save: merge into any existing metadata to preserve
        # the rich fields, then overwrite "chunks" to len(self.chunks) (the SoT).
        try:
            from datetime import UTC, datetime

            meta_path = d / "metadata.json"
            meta: dict = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    if not isinstance(meta, dict):
                        meta = {}
                except (json.JSONDecodeError, OSError):
                    meta = {}
            meta["chunks"] = len(self.chunks)
            meta["bm25_built"] = True
            meta["vectors_built"] = bool(self.vector.vectors) or meta.get(
                "vectors_built", False
            )
            meta["stamped_at"] = datetime.now(UTC).isoformat()
            meta.setdefault("index_dir", str(d))
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as meta_err:  # never let a sidecar stamp fail the save
            import sys

            print(
                f"[HybridIndex.save] WARN: metadata.json stamp failed: {meta_err}",
                file=sys.stderr,
            )

    def load(self, index_dir: Path | None = None) -> bool:
        """Load index from disk. Returns True if loaded."""
        d = index_dir or INDEX_DIR
        chunks_path = d / "chunks.json"
        bm25_path = d / "bm25.json"

        if not chunks_path.exists():
            return False

        with open(chunks_path, encoding="utf-8") as f:
            self.chunks = json.load(f)

        if bm25_path.exists():
            with open(bm25_path, encoding="utf-8") as f:
                self.bm25 = BM25Index.from_dict(json.load(f))

        vectors_path = d / "vectors.json"
        if vectors_path.exists():
            with open(vectors_path, encoding="utf-8") as f:
                self.vector = VectorIndex.from_dict(json.load(f))

        self.built = True
        return True

    def get_chunk(self, index: int) -> dict:
        """Get chunk dict by index."""
        if 0 <= index < len(self.chunks):
            return self.chunks[index]
        return {}


# ---------------------------------------------------------------------------
# PRIOR-MAP REUSE EXPOSURE (STORY-GBA-W2.3)
# ---------------------------------------------------------------------------
def load_prior_vector_map_for_bucket(bucket: str) -> dict[str, list[float]]:
    """Expose the rebuild's prior {content_sha -> vector} map to the INGESTION path.

    STORY-GBA-W2.3 — REUSE INTERNO. The ingestion embedder
    (``pipeline/embedder.py::embed_chunks``) needs the SAME prior-vector map that
    ``HybridIndex.build(incremental=True)`` consults at line 548, so a re-ingested
    document reuses already-computed vectors by ``content_sha`` instead of paying
    for the OpenAI Embeddings API again.

    This is a thin adapter, NOT a second source of truth:

      1. it resolves ``bucket`` -> on-disk index dir via the canonical
         ``bucket_query_router.BUCKET_INDEX_DIRS`` map (the same one query/health
         use), and
      2. it DELEGATES to the existing, unchanged
         ``HybridIndex._load_prior_vector_map`` — the identical loader that reads
         ``chunks.json`` + ``vectors.json``, applies the min(len) drift quarantine
         and the stored-sha collision guard.

    No reading logic is duplicated here; the rebuild's behavior is byte-for-byte
    untouched (RNF-1: ``build``/``build_incremental``/``_load_prior_vector_map``
    keep their exact shape). An unknown bucket, or a bucket whose index has no
    prior state on disk, returns ``{}`` — which makes the ingestion side embed
    everything, i.e. the pre-W2.3 behavior (safe backward-compat default).

    Args:
        bucket: knowledge bucket name ("external" | "business" | "personal").

    Returns:
        {content_sha -> vector} for reuse, or ``{}`` when no prior state exists.
    """
    try:
        from engine.intelligence.rag.bucket_query_router import BUCKET_INDEX_DIRS
    except Exception:  # pragma: no cover — router import is stable in-repo
        return {}

    index_dir = BUCKET_INDEX_DIRS.get(bucket)
    if index_dir is None:
        return {}

    # Delegate to the SAME loader the rebuild path uses (no second SOT).
    return HybridIndex()._load_prior_vector_map(index_dir)


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------
_index: HybridIndex | None = None


def get_index() -> HybridIndex:
    """Get or create the hybrid index singleton.

    NOTE: bucket-agnostic — loads the default ``INDEX_DIR`` (external/RAG_INDEX).
    For bucket-scoped local retrieval use :func:`get_index_for_bucket`, which is
    what ``hybrid_query.hybrid_search`` uses on the local-JSON fallback path so a
    ``bucket="business"`` query never silently searches the external index
    (STORY-RAG-BUSINESS-BUCKET-ROUTING).
    """
    global _index
    if _index is None:
        _index = HybridIndex()
        if not _index.load():
            _index = HybridIndex()
    return _index


# Per-bucket index cache for the local-JSON retrieval fallback. Keyed by bucket
# so a query for one bucket can never load another bucket's index dir (Art. XIII
# isolation at the retrieval layer, mirroring the build-time isolation in
# build_for_bucket).
_bucket_index_cache: dict[str, HybridIndex] = {}


def get_index_for_bucket(bucket: str) -> HybridIndex:
    """Get or create the local HybridIndex for a specific bucket.

    Loads ``.data/rag_index`` (external), ``.data/rag_business`` (business), or
    ``knowledge/personal/index`` (personal) — the SAME dirs ``rebuild.py`` writes.
    Unknown buckets fall back to the external default (defensive; callers pass a
    validated bucket). Cached per bucket so repeated queries don't re-read the
    (large) JSON each call.
    """
    cached = _bucket_index_cache.get(bucket)
    if cached is not None:
        return cached

    from engine.paths import KNOWLEDGE_PERSONAL, RAG_BUSINESS, RAG_INDEX

    bucket_dirs = {
        "external": RAG_INDEX,
        "business": RAG_BUSINESS,
        "personal": KNOWLEDGE_PERSONAL / "index",
    }
    index_dir = bucket_dirs.get(bucket, INDEX_DIR)

    idx = HybridIndex()
    if not idx.load(index_dir):
        idx = HybridIndex()  # empty-but-valid (bucket has no index yet)
    _bucket_index_cache[bucket] = idx
    return idx


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build hybrid RAG index")
    parser.add_argument("--full", action="store_true", help="Full build with vector embeddings")
    parser.add_argument(
        "--bm25-only", action="store_true", help="Build only BM25 index (no API calls)"
    )
    args = parser.parse_args()

    skip_vectors = args.bm25_only or not args.full

    print(f"\n{'=' * 60}")
    print("HYBRID INDEX BUILDER")
    print(f"{'=' * 60}")
    if skip_vectors:
        print("[BM25-only mode — no vector embeddings]\n")
    else:
        print(f"[Full mode — embedding model: {EMBEDDING_MODEL}]\n")

    idx = HybridIndex()
    stats = idx.build(skip_vectors=skip_vectors)

    print(f"Chunks indexed: {stats['total_chunks']}")
    print(f"BM25 build time: {stats['bm25_time_s']}s")
    if stats["vectors_built"]:
        print(f"Vector build time: {stats['vector_time_s']}s")

    idx.save()
    print(f"\nIndex saved to: {INDEX_DIR}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
