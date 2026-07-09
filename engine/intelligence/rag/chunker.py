#!/usr/bin/env python3
"""
CHUNKER - Hybrid RAG Phase 3.1
================================
Recursive 5-level delimiter hierarchy splitting with semantic preservation.
Default: 1500 chars (~375 tokens), 150 char overlap (~10%).
Metadata per chunk: source_file, person, domain, layer, chunk_id.

Hierarchy (highest to lowest priority):
  L1: ``\\n\\n\\n`` -- major section breaks
  L2: ``\\n\\n``    -- paragraph breaks
  L3: ``\\n``       -- line breaks
  L4: ``. `` / ``! `` / ``? `` -- sentence boundaries
  L5: `` ``         -- word boundaries (fallback)

Versao: 2.0.0
Data: 2026-04-16
Story: W2-001.3
Changelog:
  2.0.0 - Rewrite: 5-level recursive delimiter hierarchy (W2-001.3)
  1.1.0 - CHUNK_SIZE 2048->2000, CHUNK_OVERLAP 307->200 (S4 recalibration)
"""

import hashlib
import json
import logging
import math
import os
import re
from collections.abc import Callable, Sequence
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # mega-brain/
CHUNK_SIZE = 1500  # ~375 tokens (4 chars/token avg) — W2-001.3 default
CHUNK_OVERLAP = 150  # ~10% overlap
MIN_CHUNK_SIZE = 100  # Skip chunks smaller than this

# ---------------------------------------------------------------------------
# SEMANTIC CHUNKING (STORY-GBA-F3.5 — PORT LITERAL from refbrain REDACTED:
#   src/core/chunkers/semantic.ts)
# ---------------------------------------------------------------------------
# Topic-boundary chunking: embed sentences, compute adjacent cosine similarity,
# smooth the similarity curve with a Savitzky-Golay filter, then cut at the
# local minima (where adjacent sentences are LEAST similar = a topic shift).
# Falls back to the recursive (size-based) splitter whenever the semantic path
# can't converge — short/homogeneous docs, too-few sentences, or any failure.
#
# The Savitzky-Golay parameters are PORTED LITERALLY from refbrain's
# findBoundariesSavGol: window=5, polyorder=3, deriv=1. We compute the 1st
# derivative of the (cosine) similarity series and mark a local minimum at every
# zero-crossing of that derivative going negative→positive — identical to the TS
# `derivative[i-1] < 0 && derivative[i] >= 0` test.
SEMANTIC_CHUNKING_DEFAULT = True  # semantic is the default (size-based via config)

# ---------------------------------------------------------------------------
# INGEST-PATH SEMANTIC TOGGLE (STORY-ENABLE-REFBRAIN-FULL — feature A)
# ---------------------------------------------------------------------------
# The per-document API (``split_text`` / ``chunk_markdown``) already defaults to
# semantic (``SEMANTIC_CHUNKING_DEFAULT``). The FULL-INDEX / ingest path
# (``_chunk_text_like_file``, consumed by the MCE pipeline via
# ``pipeline.chunker.chunk_document``) historically PINNED ``semantic=False``
# (size-based recursive) to stay offline during whole-knowledge-base sweeps.
#
# This flag flips the ingest path's DEFAULT to semantic (ON), with env override.
# It is FAIL-SAFE by construction: ``_semantic_split`` degrades to the recursive
# splitter whenever the semantic path can't converge — no embedding key, an
# embedding provider error, short/homogeneous docs (< SEMANTIC_MIN_SENTENCES),
# or any exception. So flipping the default never breaks ingestion; it only
# improves chunk cohesion where an embedder + enough sentences are available.
#
# Env contract (truthy = on): "1", "true", "yes", "on" (case-insensitive).
# Default (unset) = ON. Set MCE_SEMANTIC_CHUNK_ENABLED=0 to restore the legacy
# size-based recursive ingest path.
#
# ⚠ CONSISTENCY: enabling semantic CHANGES CHUNK BOUNDARIES. An index built with
# the recursive splitter and then extended with semantic chunks is internally
# inconsistent (mixed boundary regimes for the same corpus). A FULL RE-INDEX of
# the affected buckets is required for boundary consistency. This flag only
# governs how NEW chunks are produced; it does NOT trigger a re-index.
_SEMANTIC_ENV_VAR = "MCE_SEMANTIC_CHUNK_ENABLED"
_TRUTHY = {"1", "true", "yes", "on"}


def ingest_path_semantic_enabled() -> bool:
    """Resolve whether the ingest/full-index path should use semantic chunking.

    Default (env unset) = ON. ``MCE_SEMANTIC_CHUNK_ENABLED=0`` (or any non-truthy
    value) forces the legacy size-based recursive splitter on the ingest path.

    Determinism (RN-1): pure function of the env var; same env → same verdict.
    """
    raw = os.getenv(_SEMANTIC_ENV_VAR)
    if raw is None:
        return True  # default ON
    return raw.strip().lower() in _TRUTHY

# refbrain SemanticChunkOptions defaults (semantic.ts): chunkSize=300 (words),
# chunkOverlap=50 (words). The recursive fallback inside the mega-brain operates
# on CHARS, so word-size limits are converted at the call boundary only.
SG_WINDOW = 5  # Savitzky-Golay window length (refbrain literal)
SG_POLYORDER = 3  # Savitzky-Golay polynomial order (refbrain literal)
SG_DERIV = 1  # 1st derivative — find minima via zero-crossings (refbrain literal)
SEMANTIC_MIN_SENTENCES = 4  # refbrain: `sentences.length <= 3` → recursive fallback
SEMANTIC_LOW_SIM_PERCENTILE = 0.2  # refbrain: keep minima below 20th-pct similarity
SEMANTIC_MIN_BOUNDARY_DISTANCE = 2  # refbrain: enforceMinDistance(..., 2)
SEMANTIC_OVERSIZE_FACTOR = 1.5  # refbrain: wordCount > chunkSize * 1.5 → sub-split

# 5-level recursive delimiter hierarchy (ordered highest to lowest)
# Sentence-end delimiters (L4) use a regex pattern to split *after* punctuation
# so the period/exclamation/question mark stays with the preceding text.
DELIMITER_HIERARCHY: list[str] = [
    "\n\n\n",  # L1: major section breaks
    "\n\n",  # L2: paragraph breaks
    "\n",  # L3: line breaks
    r"(?<=[.!?]) ",  # L4: sentence boundary (lookbehind keeps punctuation on left)
    " ",  # L5: word boundary (fallback)
]

# What to index — 3 buckets (S3: Constitution Art. XIII isolation via bucket field)
# External bucket: expert knowledge (courses, podcasts, books)
# Business bucket: company operations (meetings, calls, docs)
# Personal bucket: founder cognitive (reflections, notes, calls)
INDEX_SOURCES = {
    # --- Bucket: external ---
    "dna": BASE_DIR / "knowledge" / "external" / "dna" / "persons",
    # STORY-EXTERNAL-CONSOLIDATION: programs/orgs/systems re-modeled out of the
    # persons namespace live here. Still bucket=external; indexed so their DNA
    # (e.g. benckmarking-sua-organizacao ~621 chunks) stays retrievable, just not as a person.
    "dna_themes": BASE_DIR / "knowledge" / "external" / "dna" / "themes",
    "dossiers_persons": BASE_DIR / "knowledge" / "external" / "dossiers" / "persons",
    "dossiers_themes": BASE_DIR / "knowledge" / "external" / "dossiers" / "themes",
    "playbooks": BASE_DIR / "knowledge" / "external" / "playbooks",
    # --- Bucket: business ---
    "business_inbox": BASE_DIR / "knowledge" / "business" / "inbox",
    "business_insights": BASE_DIR / "knowledge" / "business" / "insights",
    "business_dossiers": BASE_DIR / "knowledge" / "business" / "dossiers",
    "business_sops": BASE_DIR / "knowledge" / "business" / "sops",
    "business_dna": BASE_DIR / "knowledge" / "business" / "dna",
    "business_decisions": BASE_DIR / "knowledge" / "business" / "decisions",
    "business_narratives": BASE_DIR / "knowledge" / "business" / "narratives",
    "business_people": BASE_DIR / "knowledge" / "business" / "people",
    "business_sources": BASE_DIR / "knowledge" / "business" / "sources",
    "business_advisory": BASE_DIR / "knowledge" / "business" / "advisory-board",
    "business_dossiers_persons": BASE_DIR / "knowledge" / "business" / "dossiers" / "persons",
    "business_dossiers_themes": BASE_DIR / "knowledge" / "business" / "dossiers" / "themes",
    "business_dossiers_operations": BASE_DIR / "knowledge" / "business" / "dossiers" / "operations",
    "business": [
        "workspace/businesses/*/company/**/*.md",
        "workspace/businesses/*/company/**/*.txt",
        "workspace/businesses/*/company/**/*.yaml",
        "workspace/businesses/*/company/**/*.yml",
        "workspace/businesses/*/products/**/*.md",
        "workspace/businesses/*/products/**/*.txt",
        "workspace/businesses/*/products/**/*.yaml",
        "workspace/businesses/*/products/**/*.yml",
        "workspace/businesses/*/brand/**/*.md",
        "workspace/businesses/*/brand/**/*.txt",
        "workspace/businesses/*/brand/**/*.yaml",
        "workspace/businesses/*/brand/**/*.yml",
        "workspace/businesses/*/operations/**/*.md",
        "workspace/businesses/*/operations/**/*.txt",
        "workspace/businesses/*/operations/**/*.yaml",
        "workspace/businesses/*/operations/**/*.yml",
        "workspace/businesses/*/L0-identity/**/*.md",
        "workspace/businesses/*/L0-identity/**/*.txt",
        "workspace/businesses/*/L0-identity/**/*.yaml",
        "workspace/businesses/*/L0-identity/**/*.yml",
        "workspace/businesses/*/L1-strategy/**/*.md",
        "workspace/businesses/*/L1-strategy/**/*.txt",
        "workspace/businesses/*/L1-strategy/**/*.yaml",
        "workspace/businesses/*/L1-strategy/**/*.yml",
        "workspace/businesses/*/L2-tactical/**/*.md",
        "workspace/businesses/*/L2-tactical/**/*.txt",
        "workspace/businesses/*/L2-tactical/**/*.yaml",
        "workspace/businesses/*/L2-tactical/**/*.yml",
        "workspace/businesses/*/L3-product/**/*.md",
        "workspace/businesses/*/L3-product/**/*.txt",
        "workspace/businesses/*/L3-product/**/*.yaml",
        "workspace/businesses/*/L3-product/**/*.yml",
        "workspace/_templates/**/*.md",
        "workspace/_templates/**/*.txt",
        "workspace/_templates/**/*.yaml",
        "workspace/_templates/**/*.yml",
        "workspace/strategy/**/*.md",
        "workspace/strategy/**/*.txt",
        "workspace/strategy/**/*.yaml",
        "workspace/strategy/**/*.yml",
    ],
    # --- Bucket: personal ---
    "personal_cognitive": BASE_DIR / "knowledge" / "personal" / "cognitive",
    "personal_dna": BASE_DIR / "knowledge" / "personal" / "dna",
    # --- Raw transcript artifacts (STORY-RAW-1 — EPIC-RAG-RAW-INDEXATION) ---
    # The single, durable INDEX SOURCE for raw transcript chunks produced by the
    # ingest pipeline. Each ``<slug>/BATCH-*-chunks.json`` is normalized by
    # STORY-RAW-2's ``normalize_artifact_chunks`` and tagged ``layer="transcript"``.
    # Bucket is resolved PER SLUG at runtime (``person_paths.resolve_bucket``),
    # NOT statically here — a single dir holds slugs that route to external,
    # business OR personal. The static ``SOURCE_BUCKET`` entry below records the
    # DEFAULT only; the per-slug resolver is authoritative (ADR-RAG-006 §2).
    "artifacts_chunks": BASE_DIR / ".data" / "artifacts" / "chunks",
}

# Bucket mapping: source key → bucket name (for Art. XIII isolation)
SOURCE_BUCKET: dict[str, str] = {
    "dna": "external",
    "dossiers_persons": "external",
    "dossiers_themes": "external",
    "playbooks": "external",
    "business_inbox": "business",
    "business_insights": "business",
    "business_dossiers": "business",
    "business_sops": "business",
    "business_dna": "business",
    "business_decisions": "business",
    "business_narratives": "business",
    "business_people": "business",
    "business_sources": "business",
    "business_advisory": "business",
    "business_dossiers_persons": "business",
    "business_dossiers_themes": "business",
    "business_dossiers_operations": "business",
    "personal_cognitive": "personal",
    "personal_dna": "personal",
    # Raw transcript artifacts default to external (the common case — expert
    # videos). The TRUE bucket is resolved per-slug at runtime via
    # ``person_paths.resolve_bucket`` inside ``chunk_all`` (a slug like
    # ``sua-organizacao`` may route to personal/business). This static entry is the
    # fallback/default only — Art. XIII isolation is honored by the per-slug
    # resolver, not by this map.
    "artifacts_chunks": "external",
}


# ---------------------------------------------------------------------------
# CONTENT IDENTITY (STORY-MCE-INCREMENTAL-RAG-INDEX)
# ---------------------------------------------------------------------------
# Number of leading characters that are actually embedded by the vector index.
# Must mirror the truncation applied in hybrid_index._openai_embed / VectorIndex.build
# (``t[:8000]``). Hashing exactly the embedded slice makes "same text -> reuse vector"
# always sound: two chunks differing only past char 8000 share one OpenAI vector,
# matching what the API actually received.
EMBED_TRUNCATE_CHARS = 8000


def content_sha(text: str) -> str:
    """Stable content-identity key for incremental vector reuse.

    Hashes the exact slice that gets embedded (``text[:8000]``) with SHA-256,
    truncated to 16 hex chars (64 bits) — birthday-collision probability at
    54k chunks is ~1e-11. This is the cache key for incremental indexing:
    if a chunk's content_sha is already mapped to a vector, the embedding is
    reused instead of re-calling the OpenAI Embeddings API.

    Decision: keyed on full-text content (not chunk_id) because the embedding
    is a pure function of the embedded text. chunk_id hashes only text[:100]
    + start_char + source_file, so it both collides (shared 100-char prefix)
    and drifts (start_char mutates on re-chunk) — defeating reuse.
    Ref: STORY-MCE-INCREMENTAL-RAG-INDEX section 3.
    """
    return hashlib.sha256(text[:EMBED_TRUNCATE_CHARS].encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# BOUNDARY CACHE — skip re-chunking unchanged source files (RAG rebuild fix)
# ---------------------------------------------------------------------------
# ROOT CAUSE (architect + faulthandler, 2026-06-28): chunk_all() RE-CHUNKS every
# file on every rebuild. With MCE_SEMANTIC_CHUNK_ENABLED on (default), the
# semantic splitter embeds each file SENTENCE-BY-SENTENCE through the OpenAI API
# just to decide chunk boundaries — tens of thousands of sequential POSTs across
# ~1987 business files, taking hours / hanging cmd_finalize (CPU ~0,
# network-bound). The existing ``incremental=True`` only reuses the FINAL vectors
# by content_sha AFTER chunk_all already paid for every boundary embed.
#
# FIX (skip-unchanged boundary cache, risk LOW): when a source file's content is
# unchanged versus the persisted index, REUSE the chunks that already exist in
# that index VERBATIM (same text/offsets) — ZERO boundary embeddings. Only new or
# changed files (e.g. a newly-ingested entity) go through ``_semantic_split``.
#
# This is NOT a fabricated fallback (`.claude/rules/extraction-no-fallbacks.md`):
# the reused chunks are REAL chunks previously computed by this same chunker over
# this same file. We re-emit observed truth, never an invented default. On ANY
# divergence — file content drift, missing/corrupt cache, signature/mode mismatch,
# or read error — we re-chunk that file (current behavior, bit-for-bit), so the
# cache can only make an unchanged file faster, never change WHAT is indexed.
#
# Invalidation (3 conditions, ALL must hold to reuse a file's prior chunks):
#   1. content_sha(source_file_text) == content_sha of the SAME file at index time
#      (file unchanged). Computed with the SAME utf-8 read used to chunk it
#      (``Path.read_text(encoding="utf-8")``) so the sha matches bit-for-bit.
#   2. The active embedding signature == the prior index's signature (no model/dim
#      swap — boundaries from a different embedding space are not reusable).
#   3. The active semantic mode == the prior index's mode (semantic vs recursive
#      produce different boundaries; mixing regimes is internally inconsistent).
# A None signature/mode (cache built without that provenance) is treated as
# "cannot prove same space/mode" → re-chunk (conservative, never reuse blind).


class _BoundaryCache:
    """Reuse-or-rechunk decisions for unchanged source files during chunk_all.

    Seeded from a prior index's ``chunks.json`` (grouped by ``source_file``) plus
    the prior embedding ``signature`` and ``semantic`` mode. ``reuse_for(path)``
    returns the prior chunk dicts for *path* iff the live file is byte-identical to
    the indexed version AND the active signature/mode match the prior index;
    otherwise ``None`` (caller re-chunks). Fail-safe by construction: every error
    path returns ``None``.
    """

    __slots__ = (
        "_active_semantic",
        "_active_signature",
        "_compatible",
        "_prior_fingerprint",
        "prior_chunks_by_source",
    )

    def __init__(
        self,
        prior_chunks_by_source: dict[str, list[dict]] | None,
        *,
        prior_signature: str | None = None,
        prior_semantic: bool | None = None,
        active_signature: str | None = None,
        active_semantic: bool | None = None,
    ) -> None:
        self.prior_chunks_by_source: dict[str, list[dict]] = (
            prior_chunks_by_source or {}
        )
        self._active_signature = active_signature
        self._active_semantic = (
            active_semantic
            if active_semantic is not None
            else ingest_path_semantic_enabled()
        )
        # Global compatibility gate (conditions 2 + 3). If the prior index was
        # built in a different embedding space OR a different chunking mode, the
        # WHOLE cache is unusable — every reuse_for() returns None. A missing
        # (None) prior signature/mode cannot be proven compatible → treat as
        # incompatible (conservative; re-chunk everything, current behavior).
        sig_ok = (
            prior_signature is not None
            and active_signature is not None
            and prior_signature == active_signature
        )
        mode_ok = prior_semantic is not None and prior_semantic == self._active_semantic
        self._compatible = bool(self.prior_chunks_by_source) and sig_ok and mode_ok
        # Lazily-computed {source_file -> content_sha(file_text)} of the indexed
        # version, derived ON DEMAND from the live file at reuse time (so a file
        # deleted/changed since indexing simply misses). We DON'T precompute a
        # whole-corpus fingerprint up front; the per-file read happens once at the
        # decision point. Cache is keyed by source_file to avoid double reads.
        self._prior_fingerprint: dict[str, str] = {}

    @property
    def active(self) -> bool:
        """True when the cache is eligible to serve ANY reuse (compat gate passed)."""
        return self._compatible

    def reuse_for(self, source_file: str, file_text: str) -> list[dict] | None:
        """Prior chunk dicts for *source_file* iff its content is unchanged.

        ``file_text`` is the live ``Path.read_text(encoding="utf-8")`` content the
        caller already loaded (single read; the caller would read it to chunk it
        anyway). Returns the prior chunk dicts (verbatim) on an unchanged file, or
        ``None`` when changed/absent/incompatible (caller re-chunks).
        """
        if not self._compatible:
            return None
        prior = self.prior_chunks_by_source.get(source_file)
        if not prior:
            return None
        try:
            live_fp = content_sha(file_text)
        except Exception:  # pragma: no cover — defensive: never block chunking
            return None
        # The prior index does NOT persist a per-file fingerprint, so we derive it
        # from the prior chunks' reconstructed source text. The reconstruction must
        # equal the live file for an UNCHANGED file: chunk_all writes chunk texts
        # by concatenating split_text() outputs per section (no lossy transform on
        # the recursive/semantic JOIN beyond the splitter's own ` `-join), so a
        # robust, transform-agnostic equality test is to compare the live file's
        # fingerprint against the fingerprint we recorded for the same path when
        # the cache was seeded from disk. See seed_boundary_cache(): it records the
        # indexed file's fingerprint by reading the on-disk source ONCE.
        prior_fp = self._prior_fingerprint.get(source_file)
        if prior_fp is None:
            return None
        if prior_fp != live_fp:
            return None
        return prior

    def set_prior_fingerprint(self, source_file: str, fingerprint: str) -> None:
        """Record the indexed file's content fingerprint (set at seed time)."""
        self._prior_fingerprint[source_file] = fingerprint


def seed_boundary_cache(
    prior_chunks: list[dict] | None,
    *,
    prior_signature: str | None = None,
    prior_semantic: bool | None = None,
    active_signature: str | None = None,
    active_semantic: bool | None = None,
) -> "_BoundaryCache":
    """Build a :class:`_BoundaryCache` from a prior index's ``chunks.json`` list.

    Groups *prior_chunks* by ``source_file`` and, for each source file that still
    exists on disk, reads it ONCE to record the indexed-content fingerprint
    (``content_sha(file_text)``). At chunk_all() time, an unchanged file matches
    this fingerprint and its prior chunks are reused verbatim (zero boundary
    embeddings); a changed/new file misses and is re-chunked.

    FAIL-SAFE: a chunk dict without ``source_file``/``text`` is ignored; a file
    that can't be read at seed time simply has no fingerprint (=> never reused =>
    re-chunked). Passing ``prior_chunks=None`` yields an inert cache (``active``
    False) so callers get current full-rebuild behavior bit-for-bit.

    NOTE on the fingerprint join (transform-agnostic): we DON'T trust a stored
    per-chunk sha to reconstruct the file. We compute the fingerprint of the LIVE
    on-disk file at seed time; the same function runs on the live file at reuse
    time. If the file is byte-identical between seed and chunk passes (the common
    case in a single rebuild), the two fingerprints match and reuse is sound. The
    only thing the prior chunks supply is the REUSED OUTPUT (their verbatim text/
    offsets), never the equality decision.
    """
    cache = _BoundaryCache(
        None,
        prior_signature=prior_signature,
        prior_semantic=prior_semantic,
        active_signature=active_signature,
        active_semantic=active_semantic,
    )
    if not prior_chunks:
        return cache

    grouped: dict[str, list[dict]] = {}
    for ch in prior_chunks:
        if not isinstance(ch, dict):
            continue
        sf = ch.get("source_file")
        if not isinstance(sf, str) or not sf:
            continue
        grouped.setdefault(sf, []).append(ch)
    cache.prior_chunks_by_source = grouped

    # Re-evaluate the compat gate now that we have grouped chunks (the __init__
    # gate ran against an empty group set because we passed None above).
    sig_ok = (
        prior_signature is not None
        and active_signature is not None
        and prior_signature == active_signature
    )
    mode_ok = (
        prior_semantic is not None and prior_semantic == cache._active_semantic
    )
    cache._compatible = bool(grouped) and sig_ok and mode_ok

    if not cache._compatible:
        # No point reading 2k+ files off disk if the cache can't serve anyway.
        return cache

    # Record the indexed-content fingerprint by reading each source file ONCE.
    # Pure disk I/O (no network) — seconds for ~2k files, not the hours the
    # per-sentence boundary embeds cost. A read error → no fingerprint → re-chunk.
    for sf in grouped:
        try:
            file_text = (BASE_DIR / sf).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # file gone/binary/moved → never reuse → re-chunk (fail-safe)
        try:
            cache.set_prior_fingerprint(sf, content_sha(file_text))
        except Exception:  # pragma: no cover — defensive
            continue

    return cache


# Process-local boundary cache, set by chunk_all(boundary_cache=...) and consumed
# by the text-file chunk helper. Threaded as an explicit arg through chunk_all →
# _chunk_text_like_file would touch many call-sites; a module-scoped handle keeps
# the change surgical and the default (None) preserves bit-for-bit behavior.
_ACTIVE_BOUNDARY_CACHE: "_BoundaryCache | None" = None


def _reuse_or_none(
    filepath: Path, person: str = "", domain: str = "", layer: str = ""
) -> "list[Chunk] | None":
    """If the active boundary cache has unchanged prior chunks for *filepath*,
    rebuild ``Chunk`` objects from them (verbatim) and return them; else ``None``.

    Reads *filepath* once (utf-8) to fingerprint it — the SAME read the chunker
    would do — so a hit avoids the expensive ``_semantic_split`` entirely while a
    miss falls through to the normal chunker (which reads the file again; that
    extra read only happens on the rare changed/new file).
    """
    cache = _ACTIVE_BOUNDARY_CACHE
    if cache is None or not cache.active:
        return None
    try:
        rel_path = str(filepath.relative_to(BASE_DIR))
    except ValueError:
        return None
    try:
        file_text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    prior = cache.reuse_for(rel_path, file_text)
    if not prior:
        return None
    # Rebuild Chunk objects from the prior dicts verbatim. We keep text/offsets/
    # section EXACTLY as indexed; person/domain/layer come from THIS pass's
    # routing (they are metadata the caller assigns, not part of the chunk text,
    # so honoring the live routing keeps attribution correct without altering the
    # reused content or its content_sha).
    rebuilt: list[Chunk] = []
    for ch in prior:
        text = ch.get("text")
        if not isinstance(text, str) or not text:
            # A prior chunk without text can't be reused soundly → abort reuse for
            # this file and let the caller re-chunk (fail-safe, no partial reuse).
            return None
        rebuilt.append(
            Chunk(
                text=text,
                source_file=rel_path,
                person=person or ch.get("person", ""),
                domain=domain or ch.get("domain", ""),
                layer=layer or ch.get("layer", ""),
                section=ch.get("section", ""),
                start_char=ch.get("start_char", 0),
                end_char=ch.get("end_char", 0),
                metadata=ch.get("metadata", {}) or {},
            )
        )
    return rebuilt


# ---------------------------------------------------------------------------
# STAGING GUARD (STORY-A2 — anti-staging index guard)
# ---------------------------------------------------------------------------
# Catch-all staging folders inside the business bucket (``_unclassified/`` and
# its ``misc/`` mirror) were being indexed as if they were final routed sources,
# producing the exact mirroring that duplicates content (e.g. the same CFO memo
# present in ``_unclassified/`` AND ``_unclassified/misc/``). This guard refuses
# to index any path whose *segments* include a staging marker, regardless of the
# file name (the existing ``name.startswith("_")`` check only inspected the file
# name, never the parent directory segments — which is why staged files slipped
# through).
#
# Determinism (RN-1): pure function of the path string; same path -> same verdict.
# Bucket isolation (RN-5): only enforced on the business indexing paths by the
# callers; external/personal staging is out of scope (Art. XIII).
_STAGING_SEGMENTS = ("_unclassified", "unclassified", "misc")


def is_staging_path(path: "str | Path") -> bool:
    """True if *path* lives under a business staging/catch-all segment.

    Staging segments (case-insensitive, matched on whole path components):
        ``_unclassified``, ``unclassified``, ``misc``.

    Matching is on path SEGMENTS, not substrings, so a legitimately named file
    such as ``dossiers/miscellaneous-notes.md`` is NOT flagged (its segment is
    ``miscellaneous-notes.md``, not ``misc``), while
    ``inbox/_unclassified/misc/x.md`` IS flagged.
    """
    p = Path(path)
    return any(seg.lower() in _STAGING_SEGMENTS for seg in p.parts)


# ---------------------------------------------------------------------------
# CHUNK MODEL
# ---------------------------------------------------------------------------
class Chunk:
    """A text chunk with metadata."""

    __slots__ = (
        "bucket",
        "chunk_id",
        "domain",
        "end_char",
        "layer",
        "metadata",
        "person",
        # relevance_score is written by rag.relevance_scorer.score_chunks(); it
        # was absent from __slots__, so score_chunks() raised AttributeError on
        # every real Chunk — dead-on-arrival in production, not just under test.
        "relevance_score",
        "section",
        "source_file",
        "start_char",
        "text",
    )

    def __init__(self, text: str, source_file: str, **kwargs):
        self.text = text
        self.source_file = source_file
        self.bucket = kwargs.get("bucket", "external")  # Art. XIII: always set
        self.person = kwargs.get("person", "")
        self.domain = kwargs.get("domain", "")
        self.layer = kwargs.get("layer", "")
        self.section = kwargs.get("section", "")
        self.start_char = kwargs.get("start_char", 0)
        self.end_char = kwargs.get("end_char", 0)
        self.metadata = kwargs.get("metadata", {})
        # Optional; assigned later by relevance_scorer. None == not yet scored.
        self.relevance_score = kwargs.get("relevance_score", None)
        # Generate deterministic chunk_id
        content_hash = hashlib.md5(
            f"{source_file}:{self.start_char}:{text[:100]}".encode()
        ).hexdigest()[:8]
        self.chunk_id = kwargs.get("chunk_id", f"ch_{content_hash}")

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            # content_sha: stable identity key for incremental vector reuse
            # (STORY-MCE-INCREMENTAL-RAG-INDEX). Derived from the embedded slice
            # of the full text, NOT chunk_id (which is the weaker text[:100] hash).
            "content_sha": content_sha(self.text),
            "text": self.text,
            "source_file": self.source_file,
            "bucket": self.bucket,  # Art. XIII isolation field
            "person": self.person,
            "domain": self.domain,
            "layer": self.layer,
            "section": self.section,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "char_count": len(self.text),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# RAW ARTIFACT NORMALIZER (STORY-RAW-2 — EPIC-RAG-RAW-INDEXATION)
# ---------------------------------------------------------------------------
# The ingest pipeline writes raw transcript chunks to
# ``.data/artifacts/chunks/<slug>/BATCH-*-chunks.json``. Those files carry MORE
# THAN ONE on-disk shape across the pipeline's history. This normalizer reads
# any of the three observed shapes and returns one canonical ``Chunk`` list, so
# STORY-RAW-1's ``chunk_all`` consumes raw chunks without caring about schema
# drift. NO FALLBACK (`.claude/rules/extraction-no-fallbacks.md`): an
# unrecognized shape or a chunk without usable text is SKIPPED with a structured
# warning — never fabricated into a default Chunk.
#
# The three shapes (ADR-RAG-006 §2/§4 + STORY-RAW-2 census):
#   (i)   envelope dict   ``{"batch_id":..., "chunks":[...], "count":N}``  (current — Liam)
#   (ii)  flat list       ``[ {chunk}, {chunk}, ... ]``                    (legacy flat)
#   (iii) layer map       ``{"L1":[...], "L2":[...], ...}``                (legacy per-layer)
RAW_TRANSCRIPT_LAYER = "transcript"


def _extract_artifact_chunk_dicts(
    data: object, path: Path
) -> list[dict] | None:
    """Resolve the raw inner-chunk dict list from any known artifact shape.

    Returns the list of inner chunk dicts for shapes (i), (ii), (iii). Returns
    ``None`` when the shape is NOT recognized (caller skips with a warning — NO
    FALLBACK). An empty-but-valid shape returns ``[]`` (recognized, just empty).
    """
    # Shape (ii): flat list[dict]
    if isinstance(data, list):
        return [c for c in data if isinstance(c, dict)]

    if isinstance(data, dict):
        # Shape (i): envelope dict — the live array is under "chunks".
        if "chunks" in data and isinstance(data["chunks"], list):
            return [c for c in data["chunks"] if isinstance(c, dict)]

        # Shape (iii): layer map — values are lists of chunk dicts.
        # Only treat as a layer map when EVERY value is a list (so we don't
        # silently misread an unknown dict shape as a layer map). An empty
        # dict is not a layer map.
        values = list(data.values())
        if values and all(isinstance(v, list) for v in values):
            collected: list[dict] = []
            for bucket_list in values:
                collected.extend(c for c in bucket_list if isinstance(c, dict))
            return collected

        # Recognized-dict-but-unknown → NO FALLBACK.
        logger.warning(
            "raw-2 normalizer: unknown dict shape in %s (keys=%s) — skipped, no fabricated chunks",
            path,
            sorted(data.keys()),
        )
        return None

    # Any other top-level type (str, int, None, ...) → unknown shape.
    logger.warning(
        "raw-2 normalizer: unknown top-level type %s in %s — skipped, no fabricated chunks",
        type(data).__name__,
        path,
    )
    return None


def normalize_artifact_chunks(
    path: Path, *, person: str, bucket: str
) -> list[Chunk]:
    """Normalize a raw chunk artifact on disk into canonical ``Chunk`` objects.

    Reads ``path`` (a ``BATCH-*-chunks.json`` under
    ``.data/artifacts/chunks/<slug>/``), detects the on-disk shape, and returns
    a canonical ``Chunk`` per inner chunk. Each returned ``Chunk``:

      * keeps ``text`` verbatim,
      * preserves ``chunk_id`` (the join bridge to the embeddings artifact in
        STORY-RAW-3) when present; otherwise the deterministic ``Chunk`` id is
        derived,
      * carries ``content_sha`` derived from ``text`` (via ``Chunk.to_dict`` /
        ``content_sha`` — the existing 1536d-reuse key), NOT from the artifact,
      * is tagged ``person`` (= slug of the dir) and ``bucket`` (= slug routing),
      * records ``source_file = str(path)`` (the artifact path),
      * is tagged ``layer = "transcript"`` (raw transcript origin).

    NO FALLBACK (`extraction-no-fallbacks.md`): an unrecognized shape skips the
    whole batch with a warning; a chunk without usable text is skipped with a
    warning. Nothing is fabricated.

    Args:
        path: Path to the ``BATCH-*-chunks.json`` artifact.
        person: Person slug (e.g. ``"liam-ottley"``) — the dir name.
        bucket: Resolved bucket for the slug (``"external"`` | ``"business"``).

    Returns:
        list[Chunk]: canonical chunks (possibly empty). Never raises on shape
        drift — drift is logged and skipped.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "raw-2 normalizer: cannot read/parse %s (%s) — skipped, no fabricated chunks",
            path,
            exc,
        )
        return []

    raw_chunks = _extract_artifact_chunk_dicts(data, path)
    if raw_chunks is None:
        # Unknown shape already warned inside _extract_artifact_chunk_dicts.
        return []

    chunks: list[Chunk] = []
    skipped_no_text = 0
    for raw in raw_chunks:
        text = raw.get("text")
        if not isinstance(text, str) or not text.strip():
            skipped_no_text += 1
            continue

        kwargs: dict = {
            "person": person,
            "bucket": bucket,
            "layer": RAW_TRANSCRIPT_LAYER,
            "domain": raw.get("domain", ""),
            "section": raw.get("section", ""),
            "start_char": raw.get("start_char", 0),
            "end_char": raw.get("end_char", 0),
            "metadata": raw.get("metadata", {}) or {},
        }
        # Preserve the artifact's chunk_id (join bridge to embeddings — RAW-3).
        # Only pass it through when present + non-empty; otherwise Chunk derives
        # its deterministic id.
        artifact_chunk_id = raw.get("chunk_id")
        if isinstance(artifact_chunk_id, str) and artifact_chunk_id:
            kwargs["chunk_id"] = artifact_chunk_id

        chunks.append(Chunk(text=text, source_file=str(path), **kwargs))

    if skipped_no_text:
        logger.warning(
            "raw-2 normalizer: skipped %d chunk(s) without usable text in %s — no fabricated chunks",
            skipped_no_text,
            path,
        )

    return chunks


# ---------------------------------------------------------------------------
# SPLITTING
# ---------------------------------------------------------------------------
def _split_by_sections(text: str) -> list[dict]:
    """Split markdown text by ## headers, preserving hierarchy."""
    sections = []
    lines = text.split("\n")
    current_section = ""
    current_lines: list[str] = []
    current_start = 0
    char_offset = 0

    for _i, line in enumerate(lines):
        line_len = len(line) + 1  # +1 for newline
        if line.startswith("## "):
            if current_lines:
                content = "\n".join(current_lines)
                sections.append(
                    {
                        "section": current_section,
                        "content": content,
                        "start_char": current_start,
                    }
                )
            current_section = line[3:].strip()
            current_lines = [line]
            current_start = char_offset
        else:
            current_lines.append(line)
        char_offset += line_len

    if current_lines:
        content = "\n".join(current_lines)
        sections.append(
            {
                "section": current_section,
                "content": content,
                "start_char": current_start,
            }
        )

    return sections


def _recursive_split(
    text: str,
    max_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    delimiters: list[str] | None = None,
) -> list[str]:
    """Recursively split *text* into chunks using a 5-level delimiter hierarchy.

    Algorithm:
      1. If the text fits within *max_size*, return it as a single chunk.
      2. Try the highest-priority delimiter that actually appears in the text.
      3. Greedily merge splits into chunks that stay under *max_size*.
      4. If any merged chunk still exceeds *max_size*, recurse with the
         **next** delimiter down the hierarchy.
      5. Apply *overlap* by prepending the tail of the previous chunk.
      6. Hard-split as a last resort (no delimiters left).

    This guarantees that chunks never break mid-sentence when a sentence
    boundary is available, and never break mid-paragraph when a paragraph
    boundary is available, etc.
    """
    if delimiters is None:
        delimiters = DELIMITER_HIERARCHY

    # Base: text fits already
    if len(text) <= max_size:
        return [text] if len(text) >= MIN_CHUNK_SIZE else []

    # Try each delimiter in priority order
    for idx, sep in enumerate(delimiters):
        # Use re.split for regex patterns (L4 lookbehind), plain split otherwise
        is_regex = sep.startswith("(?")
        if is_regex:
            parts = re.split(sep, text)
        else:
            parts = text.split(sep)

        if len(parts) <= 1:
            # This delimiter doesn't appear -- try the next one
            continue

        # The join separator: for regex patterns the delimiter is zero-width
        # (lookbehind), so parts already contain the punctuation. Join with " ".
        join_sep = " " if is_regex else sep

        # Greedily merge parts into chunks that respect max_size
        remaining_delimiters = delimiters[idx + 1 :]
        merged_chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = (current + join_sep + part) if current else part

            if len(candidate) <= max_size:
                current = candidate
            else:
                # Flush current if non-empty
                if current:
                    merged_chunks.append(current)
                # If the part alone exceeds max_size, recurse deeper
                if len(part) > max_size and remaining_delimiters:
                    sub_chunks = _recursive_split(
                        part, max_size, overlap=0, delimiters=remaining_delimiters
                    )
                    merged_chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current and len(current) >= MIN_CHUNK_SIZE:
            merged_chunks.append(current)
        elif current and merged_chunks:
            # Attach tiny tail to previous chunk if it won't blow max_size
            combined = merged_chunks[-1] + join_sep + current
            if len(combined) <= max_size:
                merged_chunks[-1] = combined
            else:
                # Keep as separate small chunk rather than violating max_size
                merged_chunks.append(current)

        if not merged_chunks:
            continue

        # Apply overlap between consecutive chunks
        if overlap > 0 and len(merged_chunks) > 1:
            overlapped: list[str] = [merged_chunks[0]]
            for i in range(1, len(merged_chunks)):
                prev = merged_chunks[i - 1]
                tail = prev[-overlap:]
                overlapped.append(tail + merged_chunks[i])
            merged_chunks = overlapped

        return merged_chunks

    # Last resort: hard character split (no useful delimiter found)
    step = max(max_size - overlap, 1)
    chunks: list[str] = []
    for i in range(0, len(text), step):
        chunk = text[i : i + max_size]
        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# SEMANTIC SPLITTING (STORY-GBA-F3.5)
# Port of refbrain REDACTED:src/core/chunkers/semantic.ts — Savitzky-Golay
# topic-boundary detection with recursive fallback.
# ---------------------------------------------------------------------------

# Type of the sentence-embedding callable: list[str] -> list[list[float]].
EmbedFn = Callable[[list[str]], list[Sequence[float]]]


def _default_embed_fn(sentences: list[str]) -> list[list[float]]:
    """Sentence embedder routed through the F0.2 canonical gateway.

    Reuses ``embedding_config.embed_texts`` so sentence vectors live in the
    SAME space as document/query vectors (no divergent embedding path). Imported
    lazily so importing ``chunker`` never forces the embedding stack to load and
    tests can run without network by injecting their own ``embed_fn``.
    """
    from engine.intelligence.rag.embedding_config import embed_texts

    return embed_texts(sentences, input_type="document")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences (refbrain splitSentences).

    Splits on sentence-ending punctuation (``.!?``) followed by whitespace,
    keeping the punctuation with the preceding sentence (lookbehind). Mirrors
    the TS ``text.split(/(?<=[.!?])\\s+/)`` then trim+filter-empty.
    """
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if s.strip()]


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors (refbrain cosineSimilarity).

    Returns 0.0 when either vector has zero magnitude (matches the TS
    ``denom === 0 ? 0`` guard) instead of dividing by zero.
    """
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=False):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    return 0.0 if denom == 0 else dot / denom


def _adjacent_similarities(embeddings: list[Sequence[float]]) -> list[float]:
    """Cosine similarity of each adjacent embedding pair.

    Returns a series of length ``len(embeddings) - 1`` (refbrain
    computeAdjacentSimilarities).
    """
    return [
        _cosine_similarity(embeddings[i], embeddings[i + 1])
        for i in range(len(embeddings) - 1)
    ]


def _percentile(values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile (refbrain percentile).

    Sorts ascending and indexes at ``floor(p * len)``, clamped to the last
    element — identical to the TS implementation (NOT linear interpolation).
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = math.floor(p * len(ordered))
    return ordered[min(idx, len(ordered) - 1)]


def _enforce_min_distance(boundaries: list[int], min_dist: int) -> list[int]:
    """Drop boundaries closer than ``min_dist`` to the previous kept one.

    Greedy left-to-right pass (refbrain enforceMinDistance).
    """
    if len(boundaries) <= 1:
        return list(boundaries)
    result = [boundaries[0]]
    for b in boundaries[1:]:
        if b - result[-1] >= min_dist:
            result.append(b)
    return result


def _find_boundaries_percentile(similarities: list[float]) -> list[int]:
    """Percentile-only boundary detection (refbrain findBoundariesPercentile).

    Fallback used when the series is too short for Savitzky-Golay or the SG
    pass raises. A boundary is placed AFTER any position whose similarity is
    below the 20th percentile (a local dip = topic shift).
    """
    if not similarities:
        return []
    threshold = _percentile(similarities, SEMANTIC_LOW_SIM_PERCENTILE)
    boundaries = [i + 1 for i, s in enumerate(similarities) if s < threshold]
    return _enforce_min_distance(boundaries, SEMANTIC_MIN_BOUNDARY_DISTANCE)


def _find_boundaries_savgol(similarities: list[float]) -> list[int]:
    """Savitzky-Golay boundary detection (refbrain findBoundariesSavGol).

    PORT LITERAL of the refbrain parameters: ``savgol_filter(sims, window=5,
    polyorder=3, deriv=1)`` produces the smoothed 1st derivative of the
    adjacent-similarity curve. A local MINIMUM is a zero-crossing of that
    derivative going negative→positive (``deriv[i-1] < 0 and deriv[i] >= 0``).
    Minima are then filtered to keep only those where the similarity sits below
    the 20th percentile (real topic shift, not noise), and finally thinned so no
    two boundaries are closer than 2 sentences.
    """
    from scipy.signal import savgol_filter  # scipy 1.16.3 — Savitzky-Golay

    derivative = savgol_filter(
        similarities,
        window_length=SG_WINDOW,
        polyorder=SG_POLYORDER,
        deriv=SG_DERIV,
    )

    minima: list[int] = []
    for i in range(1, len(derivative)):
        if derivative[i - 1] < 0 and derivative[i] >= 0:
            minima.append(i)

    threshold = _percentile(similarities, SEMANTIC_LOW_SIM_PERCENTILE)
    filtered = [
        i for i in minima if similarities[min(i, len(similarities) - 1)] < threshold
    ]
    return _enforce_min_distance(filtered, SEMANTIC_MIN_BOUNDARY_DISTANCE)


def _find_boundaries(similarities: list[float]) -> list[int]:
    """Topic boundaries from the adjacent-similarity series (refbrain findBoundaries).

    Uses Savitzky-Golay when the series is long enough (>= window), otherwise
    the percentile fallback; any SG failure also degrades to percentile.
    """
    if len(similarities) < SG_WINDOW:
        return _find_boundaries_percentile(similarities)
    try:
        return _find_boundaries_savgol(similarities)
    except Exception:
        return _find_boundaries_percentile(similarities)


def _group_at_boundaries(sentences: list[str], boundaries: list[int]) -> list[list[str]]:
    """Slice sentences into groups at the boundary indices (refbrain groupAtBoundaries).

    Each boundary ``b`` cuts BEFORE sentence ``b``; the final group runs to the
    end. Returns ``[sentences]`` (one group) when no usable boundary exists.
    """
    groups: list[list[str]] = []
    start = 0
    for b in boundaries:
        if b > start and b < len(sentences):
            groups.append(sentences[start:b])
            start = b
    if start < len(sentences):
        groups.append(sentences[start:])
    return groups if groups else [sentences]


def _semantic_split(
    text: str,
    *,
    embed_fn: EmbedFn | None = None,
    max_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split *text* into topic-coherent chunks (refbrain chunkTextSemantic).

    Pipeline (PORT LITERAL of semantic.ts):
      1. Split into sentences. ``<= 3`` sentences → recursive fallback.
      2. Embed every sentence via the F0.2 gateway (or an injected ``embed_fn``).
      3. Compute adjacent cosine similarities.
      4. Find topic boundaries (Savitzky-Golay minima, percentile-filtered).
      5. Group sentences at the boundaries.
      6. Recursively (size-) split any group that overflows ``max_size`` so the
         semantic boundaries never produce an over-long chunk.

    ANY failure (no embedder, embedding-count mismatch, provider error) degrades
    to the recursive size-based splitter — semantic chunking can only improve
    cohesion, never break ingestion (fail-safe, mirrors the TS ``catch``).

    Note on units: refbrain measures group size in WORDS (chunkSize=300); the
    mega-brain recursive splitter operates in CHARS. We keep the mega-brain's
    char-based ``max_size`` so the fallback path is identical to the legacy
    behaviour, and apply the refbrain ``* 1.5`` oversize rule on that same scale.
    """
    fn = embed_fn or _default_embed_fn

    try:
        sentences = _split_sentences(text)
        if len(sentences) < SEMANTIC_MIN_SENTENCES:
            return _recursive_split(text, max_size=max_size, overlap=overlap)

        embeddings = list(fn(sentences))
        if len(embeddings) != len(sentences):
            return _recursive_split(text, max_size=max_size, overlap=overlap)

        similarities = _adjacent_similarities(embeddings)
        boundaries = _find_boundaries(similarities)
        groups = _group_at_boundaries(sentences, boundaries)

        chunks: list[str] = []
        for group in groups:
            group_text = " ".join(group).strip()
            if not group_text:
                continue
            if len(group_text) > max_size * SEMANTIC_OVERSIZE_FACTOR:
                chunks.extend(
                    _recursive_split(group_text, max_size=max_size, overlap=overlap)
                )
            else:
                chunks.append(group_text)
        # If grouping yielded nothing usable, fall back rather than drop the doc.
        return chunks or _recursive_split(text, max_size=max_size, overlap=overlap)
    except Exception:
        # Any failure falls back to the recursive size-based splitter.
        return _recursive_split(text, max_size=max_size, overlap=overlap)


def split_text(
    text: str,
    *,
    semantic: bool | None = None,
    embed_fn: EmbedFn | None = None,
    max_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split *text* into chunks. Semantic (Savitzky-Golay) by default.

    ``semantic=None`` resolves to ``SEMANTIC_CHUNKING_DEFAULT`` (True). Pass
    ``semantic=False`` to force the legacy size-based recursive splitter. The
    semantic path itself degrades to the recursive splitter on short/homogeneous
    docs or any failure, so this is always safe.
    """
    use_semantic = SEMANTIC_CHUNKING_DEFAULT if semantic is None else semantic
    if use_semantic:
        return _semantic_split(text, embed_fn=embed_fn, max_size=max_size, overlap=overlap)
    return _recursive_split(text, max_size=max_size, overlap=overlap)


# ---------------------------------------------------------------------------
# FILE CHUNKERS
# ---------------------------------------------------------------------------
def chunk_markdown(
    filepath: Path,
    person: str = "",
    domain: str = "",
    layer: str = "",
    *,
    semantic: bool | None = None,
    embed_fn: EmbedFn | None = None,
) -> list[Chunk]:
    """Chunk a markdown file preserving ## section hierarchy.

    Within each ``##`` section the body is split by ``split_text`` — semantic
    (Savitzky-Golay topic boundaries) by default (STORY-GBA-F3.5), degrading to
    the size-based recursive splitter on short/homogeneous sections or any
    failure. Pass ``semantic=False`` to force size-based, or inject ``embed_fn``
    for a custom/deterministic sentence embedder.
    """
    try:
        text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    rel_path = str(filepath.relative_to(BASE_DIR))
    sections = _split_by_sections(text)
    chunks = []

    for sec_info in sections:
        sec_name = sec_info["section"]
        sec_content = sec_info["content"]
        sec_start = sec_info["start_char"]

        sub_chunks = split_text(sec_content, semantic=semantic, embed_fn=embed_fn)
        offset = 0
        for i, sub_text in enumerate(sub_chunks):
            start = sec_start + offset
            chunks.append(
                Chunk(
                    text=sub_text,
                    source_file=rel_path,
                    person=person,
                    domain=domain,
                    layer=layer,
                    section=sec_name,
                    start_char=start,
                    end_char=start + len(sub_text),
                    metadata={"section_index": i},
                )
            )
            offset += len(sub_text)

    return chunks


def chunk_yaml(filepath: Path, person: str = "", layer: str = "") -> list[Chunk]:
    """Chunk a DNA YAML file — one chunk per entry."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return []

    rel_path = str(filepath.relative_to(BASE_DIR))
    chunks = []

    if not isinstance(data, dict):
        return []

    # Find the list of entries (e.g. heuristicas, frameworks, etc.)
    entries_list = None
    for v in data.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            entries_list = v
            break

    if not entries_list:
        return []

    layer_name = filepath.stem.lower()
    for i, entry in enumerate(entries_list):
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id", f"{layer_name}_{i}")
        # Serialize entry to text for embedding
        text_parts = [f"ID: {entry_id}"]
        for k, v in entry.items():
            if k == "id":
                continue
            if isinstance(v, str):
                text_parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                text_parts.append(f"{k}: {', '.join(str(x) for x in v)}")
            elif isinstance(v, dict):
                text_parts.append(f"{k}: {v}")

        text = "\n".join(text_parts)
        domains = entry.get("dominios", [])
        domain = domains[0] if domains else ""

        chunks.append(
            Chunk(
                text=text,
                source_file=rel_path,
                person=person,
                domain=domain,
                layer=layer_name,
                section=entry_id,
                chunk_id=entry_id,
                metadata={"entry_index": i, "domains": domains},
            )
        )

    return chunks


def _iter_glob_specs(specs: list[str]) -> list[Path]:
    """Resolve relative glob specs from BASE_DIR into unique existing files."""
    seen: set[str] = set()
    files: list[Path] = []

    for spec in specs:
        for path in sorted(BASE_DIR.glob(spec)):
            if not path.is_file() or path.name.startswith(("_", ".")):
                continue
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)

    return files


# Honest strategy label for the ingest path. ``_chunk_text_like_file`` now
# resolves its semantic mode from ``ingest_path_semantic_enabled()`` (feature A),
# so the label is DYNAMIC: it must report what the path ACTUALLY did this run,
# not a hardcoded value. The MCE chronicler (STEP 09) reads
# ``ingest_path_chunk_strategy()`` so it stays truthful when the flag changes.


def ingest_path_chunk_strategy() -> str:
    """Honest, current strategy label for the ingest/full-index path.

    Reflects the live ``MCE_SEMANTIC_CHUNK_ENABLED`` resolution so the MCE
    chronicler (STEP 09) reports the strategy actually used this run.
    """
    if ingest_path_semantic_enabled():
        return "semantic (Savitzky-Golay topic boundaries, recursive fallback)"
    return "recursive (size-based, semantic=False)"


# Backward-compat module attribute. Historical callers import the NAME
# ``INGEST_PATH_CHUNK_STRATEGY`` directly (log_generator.py, orchestrate.py).
# Resolved ONCE at import time from the current env so those legacy reads keep
# working; new/precise callers should prefer ``ingest_path_chunk_strategy()``
# (a fresh resolution) when the flag may change within a process.
INGEST_PATH_CHUNK_STRATEGY = ingest_path_chunk_strategy()


def _chunk_text_like_file(
    filepath: Path,
    person: str = "",
    domain: str = "",
    layer: str = "",
    *,
    semantic: bool | None = None,
) -> list[Chunk]:
    """Send markdown and plain-text files through the same chunker path.

    The ingest/full-index path resolves its chunking mode from
    ``ingest_path_semantic_enabled()`` (feature A — STORY-ENABLE-REFBRAIN-FULL).
    Default is SEMANTIC (Savitzky-Golay topic boundaries); set
    ``MCE_SEMANTIC_CHUNK_ENABLED=0`` to restore the legacy size-based recursive
    splitter.

    ``semantic`` override (FU-1 — network gate under skip_vectors):
      * ``None`` (default) → resolve from ``ingest_path_semantic_enabled()``
        (the env-var contract — unchanged behaviour).
      * ``False`` → FORCE the recursive size-based splitter, regardless of the
        env var. Callers pass this when the run must NOT touch the network. A
        local graph+vault rebuild (``rebuild(skip_vectors=True)``) promises not
        to embed, yet semantic chunking embeds sentences via OpenAI to place its
        topic boundaries — so without this gate a "local" rebuild would still
        make network calls. ``skip_vectors=True`` therefore implies semantic OFF
        for that rebuild (no reliance on the env var).
      * ``True`` → force semantic (symmetric with ``False``; rarely needed).

    FAIL-SAFE: ``chunk_markdown`` → ``split_text`` → ``_semantic_split`` degrades
    to the recursive splitter when there is no embedding key, on any embedding
    provider error, for short/homogeneous docs (< SEMANTIC_MIN_SENTENCES), or any
    exception. Flipping the default never breaks ingestion (offline runs simply
    fall back to recursive, exactly as before).

    BOUNDARY CACHE (RAG rebuild fix): when an active ``_BoundaryCache`` holds
    unchanged prior chunks for this file, they are reused verbatim — skipping the
    per-sentence boundary embeds entirely. A miss (new/changed file, no cache,
    incompatible signature/mode) falls through to the normal semantic chunker.
    """
    # BOUNDARY CACHE (#71): a cache hit returns the prior chunks verbatim,
    # skipping BOTH the semantic-mode resolution and the (network-bound) semantic
    # split entirely. Checked FIRST so an unchanged file costs zero embeds.
    reused = _reuse_or_none(filepath, person=person, domain=domain, layer=layer)
    if reused is not None:
        return reused
    # FU-1 network gate (main): resolve the effective semantic mode. ``None`` →
    # env-var contract (ingest_path_semantic_enabled); ``False`` forces the
    # deterministic recursive splitter (no network); ``True`` forces semantic.
    resolved = ingest_path_semantic_enabled() if semantic is None else semantic
    return chunk_markdown(
        filepath,
        person=person,
        domain=domain,
        layer=layer,
        semantic=resolved,
    )


# ---------------------------------------------------------------------------
# FULL INDEX
# ---------------------------------------------------------------------------
def chunk_all(
    sources: dict[str, Path | list[str]] | None = None,
    *,
    semantic: bool | None = None,
    boundary_cache: "_BoundaryCache | None" = None,
) -> list[Chunk]:
    """Chunk all knowledge base files across 3 buckets.

    Returns list of all chunks with metadata.
    Constitution Art. XIII: each chunk carries its bucket origin.

    Args:
        sources: Index source map (defaults to ``INDEX_SOURCES``).
        semantic: Chunking-mode override threaded to every text-file chunk call
            (FU-1 — network gate under skip_vectors):
              * ``None`` (default) → each file resolves its own mode from
                ``ingest_path_semantic_enabled()`` (env-var contract — unchanged).
              * ``False`` → FORCE the recursive size-based splitter for the WHOLE
                sweep, so NO network call is made. Callers pass this for a local
                graph+vault rebuild (``skip_vectors=True``): semantic chunking
                embeds sentences via OpenAI to place boundaries, so a "local"
                rebuild must not use it. YAML chunks are already offline and are
                unaffected.
              * ``True`` → force semantic for the whole sweep.
        boundary_cache: Optional :class:`_BoundaryCache` seeded from a prior
            index. When provided AND compatible, unchanged source files reuse
            their prior chunks verbatim (skipping the per-sentence boundary
            embeds — the RAG rebuild hang fix). ``None`` (default) =
            current full re-chunk behavior, bit-for-bit (the cache is the only
            thing that can change runtime, never output for an unchanged corpus).

    ``semantic`` and ``boundary_cache`` are ORTHOGONAL: ``semantic`` selects the
    chunking mode for files that ARE (re-)chunked; ``boundary_cache`` decides
    WHICH files skip chunking entirely (unchanged → reuse). A cached file is
    reused verbatim regardless of ``semantic``; a non-cached file is chunked
    under ``semantic``.
    """
    if sources is None:
        sources = INDEX_SOURCES

    # Activate the boundary cache for the duration of this call. _chunk_text_like_file
    # reads the module handle (threading it through every chunk helper call-site
    # would be far more invasive). Restored in `finally` so concurrent/repeat calls
    # without a cache see the default (None) behavior.
    global _ACTIVE_BOUNDARY_CACHE
    _prev_cache = _ACTIVE_BOUNDARY_CACHE
    _ACTIVE_BOUNDARY_CACHE = boundary_cache

    try:
        return _chunk_all_impl(sources, semantic=semantic)
    finally:
        _ACTIVE_BOUNDARY_CACHE = _prev_cache


def _chunk_all_impl(
    sources: dict[str, Path | list[str]], *, semantic: bool | None = None
) -> list[Chunk]:
    """Body of :func:`chunk_all` (boundary cache already activated by caller).

    ``semantic`` is threaded from ``chunk_all`` to every ``_chunk_text_like_file``
    call so the FU-1 network gate (main) survives the boundary-cache refactor
    (#71): a cache MISS still honors the caller's semantic-mode override, while a
    cache HIT reuses prior chunks verbatim before ``semantic`` is even consulted.
    """
    all_chunks: list[Chunk] = []

    # ----------------------------------------------------------------
    # BUCKET: external
    # ----------------------------------------------------------------

    # 1. DNA YAMLs (per person)
    dna_dir = sources.get("dna")
    if dna_dir and dna_dir.exists():
        for person_dir in sorted(dna_dir.iterdir()):
            if not person_dir.is_dir() or person_dir.name.startswith(("_", ".")):
                continue
            person = person_dir.name
            for yaml_file in person_dir.glob("*.yaml"):
                if yaml_file.name == "CONFIG.yaml":
                    continue
                chunks = chunk_yaml(yaml_file, person=person)
                for c in chunks:
                    c.bucket = "external"
                all_chunks.extend(chunks)

    # 1b. DNA YAMLs (per theme/program — STORY-EXTERNAL-CONSOLIDATION)
    # Same shape as persons, but these slugs are programs/orgs/systems, not people.
    # Tagged with layer="theme_dna" so retrieval can distinguish a program's DNA
    # from a real person's; still bucket=external (no cross-bucket contamination).
    dna_themes_dir = sources.get("dna_themes")
    if dna_themes_dir and dna_themes_dir.exists():
        for theme_dir in sorted(dna_themes_dir.iterdir()):
            if not theme_dir.is_dir() or theme_dir.name.startswith(("_", ".")):
                continue
            theme = theme_dir.name
            for yaml_file in theme_dir.glob("*.yaml"):
                if yaml_file.name == "CONFIG.yaml":
                    continue
                chunks = chunk_yaml(yaml_file, person=theme, layer="theme_dna")
                for c in chunks:
                    c.bucket = "external"
                all_chunks.extend(chunks)

    # 2. Person dossiers
    persons_dir = sources.get("dossiers_persons")
    if persons_dir and persons_dir.exists():
        for pattern in ("DOSSIER-*.md", "DOSSIER-*.txt"):
            for md_file in sorted(persons_dir.glob(pattern)):
                person = _person_from_filename(md_file.stem)
                chunks = _chunk_text_like_file(
                    md_file, person=person, layer="dossier", semantic=semantic
                )
                for c in chunks:
                    c.bucket = "external"
                all_chunks.extend(chunks)

    # 3. Theme dossiers
    themes_dir = sources.get("dossiers_themes")
    if themes_dir and themes_dir.exists():
        for pattern in ("DOSSIER-*.md", "DOSSIER-*.txt"):
            for md_file in sorted(themes_dir.glob(pattern)):
                domain = _domain_from_theme(md_file.stem)
                chunks = _chunk_text_like_file(
                    md_file, domain=domain, layer="theme", semantic=semantic
                )
                for c in chunks:
                    c.bucket = "external"
                all_chunks.extend(chunks)

    # 4. Playbooks
    playbooks_dir = sources.get("playbooks")
    if playbooks_dir and playbooks_dir.exists():
        for pattern in ("*.md", "*.txt"):
            for md_file in sorted(playbooks_dir.glob(pattern)):
                chunks = _chunk_text_like_file(
                    md_file, layer="playbook", semantic=semantic
                )
                for c in chunks:
                    c.bucket = "external"
                all_chunks.extend(chunks)

    # ----------------------------------------------------------------
    # BUCKET: business — data-driven, usa TODAS as entradas de INDEX_SOURCES
    # Adicionar/remover subdir em INDEX_SOURCES atualiza automaticamente.
    # ----------------------------------------------------------------

    _business_layer_map = {
        "business_inbox": "inbox",
        "business_insights": "insight",
        "business_dossiers": "business_dossier",
        "business_dossiers_persons": "business_dossier",
        "business_dossiers_themes": "business_dossier",
        "business_dossiers_operations": "business_dossier",
        "business_sops": "sop",
        "business_dna": "business_dna",
        "business_decisions": "decision",
        "business_narratives": "narrative",
        "business_people": "people",
        "business_sources": "source",
        "business_advisory": "advisory",
    }
    _business_text_patterns = ("*.md", "*.txt")

    # STORY-A2-FIX (2026-06-28): the STORY-A2 ``is_staging_path`` blanket-exclude
    # was DROPPING UNIQUE CONTENT. Disk measurement proved that 449 files under
    # ``knowledge/business/inbox/_unclassified/**`` have ZERO canonical copy
    # elsewhere — A2 was not removing duplicates, it was deleting real meetings
    # from the index (business MEETs 1316→732, MEET-1417 vanished). The original
    # ~45% duplication was an INTERNAL mirror (``_unclassified/X`` vs
    # ``_unclassified/misc/X``) already resolved by STORY-A1 (content_sha
    # keep-first dedup at write time in hybrid_index.py) + B2 (disk collapse).
    # A1 deduplicates LOSSLESSLY across ALL source paths, so the path-based
    # exclusion is both redundant for true duplicates and destructive for unique
    # staging content. Decision: index staging content (it gets person="" via the
    # A4 path attribution — orphan-but-searchable > permanently lost). The
    # ``is_staging_path`` function is RETAINED (imported by tests + the rebuild
    # script) but is no longer used to drop content here.
    _seen_business: set[str] = set()
    for workspace_file in _iter_glob_specs(sources.get("business", [])):
        _fp = str(workspace_file.resolve())
        if _fp in _seen_business:
            continue
        _seen_business.add(_fp)
        if workspace_file.suffix in (".yaml", ".yml"):
            chunks = chunk_yaml(workspace_file, layer="workspace")
            if not chunks:
                chunks = _chunk_text_like_file(
                    workspace_file, layer="workspace", semantic=semantic
                )
        else:
            chunks = _chunk_text_like_file(
                workspace_file, layer="workspace", semantic=semantic
            )
        for c in chunks:
            c.bucket = "business"
        all_chunks.extend(chunks)

    for _key, _layer in _business_layer_map.items():
        _biz_dir = sources.get(_key)
        if not _biz_dir or not _biz_dir.exists():
            continue
        for pattern in _business_text_patterns:
            for md_file in sorted(_biz_dir.rglob(pattern)):
                if md_file.name.startswith(("_", ".")):
                    continue
                # STORY-A2-FIX (2026-06-28): staging directory segments
                # (``_unclassified`` / ``misc``) are NO LONGER excluded here.
                # Unique staging content (449 files, 0 canonical copies) was being
                # dropped, costing 584 real meetings from the index. STORY-A1
                # content_sha keep-first dedup (hybrid_index.py) already removes any
                # true duplicate losslessly regardless of source path, so no
                # path-based skip is needed. Note: the per-file ``name.startswith
                # ("_", ".")`` guard above still skips dot/underscore FILES — but the
                # ``_unclassified`` DIRECTORY's real ``.md`` files now flow through.
                _fp = str(md_file.resolve())
                if _fp in _seen_business:
                    continue  # evitar duplicatas se dirs se sobrepõem
                _seen_business.add(_fp)
                # STORY-A4: durable inline person attribution. Deterministic,
                # No-Invention — only paths with a reliable person signal get a
                # slug; everything else stays "" (was the source of 33.5k orphans).
                #   * inbox/<SLUG>/...           → person = <SLUG> (path segment)
                #   * dossiers/persons/DOSSIER-X → person = X IFF X is a known
                #     person (matcher-validated; concepts stay "")
                #   * all other business dirs    → "" (sub-structure is not
                #     person-based: by-meeting/by-theme/cross-person/etc.)
                # Dossier check is PATH-based (not key-based): the recursive
                # ``business_dossiers`` rglob reaches persons/ too, and dedup
                # (``_seen_business``) means whichever loop sees a file FIRST
                # must attribute it.
                _person = ""
                if _key == "business_inbox":
                    _person = _business_person_from_path(md_file, _biz_dir)
                elif "/dossiers/persons/" in md_file.as_posix():
                    _person = _business_dossier_person(md_file)
                chunks = _chunk_text_like_file(
                    md_file, person=_person, layer=_layer, semantic=semantic
                )
                for c in chunks:
                    c.bucket = "business"
                all_chunks.extend(chunks)

    # ----------------------------------------------------------------
    # BUCKET: personal
    # ----------------------------------------------------------------

    # 8. Personal cognitive (reflections, mental models, journal)
    personal_cognitive_dir = sources.get("personal_cognitive")
    if personal_cognitive_dir and personal_cognitive_dir.exists():
        for pattern in ("*.md", "*.txt"):
            for md_file in sorted(personal_cognitive_dir.rglob(pattern)):
                if md_file.name.startswith(("_", ".")):
                    continue
                chunks = _chunk_text_like_file(
                    md_file, layer="cognitive", semantic=semantic
                )
                for c in chunks:
                    c.bucket = "personal"
                all_chunks.extend(chunks)

    # 9. Personal DNA YAMLs
    personal_dna_dir = sources.get("personal_dna")
    if personal_dna_dir and personal_dna_dir.exists():
        for yaml_file in sorted(personal_dna_dir.rglob("*.yaml")):
            if yaml_file.name == "CONFIG.yaml":
                continue
            chunks = chunk_yaml(yaml_file)
            for c in chunks:
                c.bucket = "personal"
            all_chunks.extend(chunks)

    # ----------------------------------------------------------------
    # RAW TRANSCRIPT ARTIFACTS (STORY-RAW-1 — EPIC-RAG-RAW-INDEXATION)
    # ----------------------------------------------------------------
    # Close the broken edge (ADR-RAG-006 §1): raw transcript chunks written by
    # the ingest pipeline to ``.data/artifacts/chunks/<slug>/BATCH-*-chunks.json``
    # become a FIRST-CLASS index source, joining the distilled DNA YAMLs in the
    # one canonical index. Because ``rebuild`` sources these chunks itself on
    # every pass, they are DURABLE — the PoC's out-of-band merge (wiped by the
    # next rebuild) is eliminated.
    #
    #   * bucket: resolved PER SLUG via the canonical ``resolve_bucket`` SOT
    #     (sidecar-first; defaults to external) — Art. XIII isolation. NOT the
    #     pipeline-stamped ``bucket`` field inside the artifact (often empty/stale).
    #   * person: the slug (= dir name) — enables ``person``-filtered retrieval.
    #   * layer: ``"transcript"`` (raw origin) via ``normalize_artifact_chunks``.
    #   * dedup: by ``chunk_id`` against everything already collected, so a
    #     re-read across consecutive rebuilds never duplicates (AC-7 idempotency;
    #     ``content_sha`` provides a second dedup layer downstream).
    artifacts_chunks_dir = sources.get("artifacts_chunks")
    if artifacts_chunks_dir and artifacts_chunks_dir.exists():
        # Lazy import: keeps ``chunker`` import cheap and dodges any circular
        # import with the pipeline.mce layer (resolve_bucket lazy-imports too).
        from engine.intelligence.pipeline.mce.person_paths import resolve_bucket

        _default_artifact_bucket = SOURCE_BUCKET.get("artifacts_chunks", "external")
        _seen_artifact_ids: set[str] = {c.chunk_id for c in all_chunks}
        for slug_dir in sorted(artifacts_chunks_dir.iterdir()):
            # Only per-slug subdirs are in scope (flat root files have no
            # reliable person slug). Skip files, dotfiles, and ``_`` helpers.
            if not slug_dir.is_dir() or slug_dir.name.startswith(("_", ".")):
                continue
            slug = slug_dir.name
            try:
                bucket = resolve_bucket(slug)
            except Exception:  # pragma: no cover - defensive: never block the index
                logger.warning(
                    "raw-1: resolve_bucket failed for slug=%s — defaulting to %s",
                    slug,
                    _default_artifact_bucket,
                )
                bucket = _default_artifact_bucket
            for artifact_file in sorted(slug_dir.glob("BATCH-*-chunks.json")):
                for chunk in normalize_artifact_chunks(
                    artifact_file, person=slug, bucket=bucket
                ):
                    if chunk.chunk_id in _seen_artifact_ids:
                        continue  # idempotent: no duplicate across rebuilds
                    _seen_artifact_ids.add(chunk.chunk_id)
                    all_chunks.append(chunk)

    return all_chunks


def _person_from_filename(stem: str) -> str:
    """Extract person name from dossier filename.

    Case-insensitive ``DOSSIER-`` strip: external dossiers are UPPERCASE
    (``DOSSIER-*.md``) but business dossiers appear in both cases
    (``DOSSIER-X.md`` and ``dossier-x.md`` — STORY-A4). The output is always
    lowercased, so a lowercase prefix must be stripped too.
    """
    name = re.sub(r"^DOSSIER-", "", stem, flags=re.IGNORECASE)
    return name.lower()


def _domain_from_theme(stem: str) -> str:
    """Extract domain hint from theme dossier filename."""
    name = re.sub(r"^DOSSIER-\d+-?", "", stem)
    return name.lower().replace("-", "_")


def _business_person_from_path(md_file: Path, biz_dir: Path) -> str:
    """Deterministic inline person attribution for a business inbox file.

    STORY-A4: ``knowledge/business/inbox/<SLUG>/...`` carries the person slug
    as the FIRST path segment under the inbox root. This derives ``<SLUG>`` so
    ``chunk_all`` can stamp ``person`` AT BUILD TIME (durable) instead of the
    non-durable B3 post-pass that ``cmd_rag_index`` wiped on every rebuild.

    Determinism + No-Invention contract:
      * the directory name on disk IS the canonical slug (same convention the
        artifacts loop relies on — ``slug = slug_dir.name``); no new
        normalization is invented here.
      * a file sitting directly at the inbox root (no ``<SLUG>/`` segment) has
        NO reliable person → returns ``""`` (No Invention).
      * staging segments (``_unclassified`` / ``unclassified`` / ``misc``) are NO
        LONGER excluded upstream (STORY-A2-FIX 2026-06-28 — they carry unique
        content that must be indexed). They are NOT person slugs, so this helper
        now treats them as non-slugs → ``""`` (No Invention). Previously
        ``unclassified`` / ``misc`` (no leading ``_``) would have been minted as a
        fake person once the A2 upstream exclusion was removed.

    Returns the slug, or ``""`` when no confident slug exists.
    """
    try:
        rel = md_file.resolve().relative_to(biz_dir.resolve())
    except ValueError:  # pragma: no cover - defensive: file outside biz_dir
        return ""
    parts = rel.parts
    # parts[-1] is the filename; a leading directory segment is required.
    if len(parts) < 2:
        return ""  # loose file at inbox root — No Invention
    slug = parts[0].strip()
    if not slug or slug.startswith(("_", ".")):
        return ""
    # STORY-A2-FIX: a staging directory name is never a person slug.
    if slug.lower() in _STAGING_SEGMENTS:
        return ""
    return slug


def _business_dossier_person(md_file: Path) -> str:
    """Deterministic person attribution for a business person-dossier.

    STORY-A4: ``knowledge/business/dossiers/persons/DOSSIER-<NAME>.md`` MIGHT
    name a real person — but the same dir also holds CONCEPT dossiers
    (``DOSSIER-AI-FIRST-APPROACH``, ``DOSSIER-AUTOMATION-STRATEGIES``).
    Stamping ``person`` from the filename alone would invent people out of
    concepts (No Invention violation).

    So the filename-derived name is VALIDATED against the canonical people
    matchers (the SAME ``external_people`` / ``internal_people`` registries the
    B3 backfill used): only a recognized person gets a slug; an unrecognized
    name (concept, or person absent from the registry) stays ``""`` — an honest
    gap, not a guess.

    Returns the canonical person slug, or ``""`` when not a known person.
    """
    if "/dossiers/persons/" not in md_file.as_posix():
        return ""
    if not md_file.stem.upper().startswith("DOSSIER-"):
        return ""
    raw = _person_from_filename(md_file.stem)  # lowercase-hyphen, prefix stripped
    if not raw:
        return ""
    try:
        # Lazy import: keeps chunker import cheap + dodges any circular import.
        from engine.intelligence.pipeline import external_people, internal_people

        name = raw.replace("-", " ")
        ext = external_people.classify(name)
        if ext:
            return ext
        intern = internal_people.classify(name)
        if intern:
            return intern[0]  # (slug, relationship)
    except Exception:  # pragma: no cover - defensive: never block the index
        return ""
    return ""  # not a known person → honest gap (No Invention)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    print(f"\n{'=' * 60}")
    print("CHUNKER - Knowledge Base")
    print(f"{'=' * 60}\n")

    chunks = chunk_all()

    # Stats
    by_layer: dict[str, int] = {}
    by_person: dict[str, int] = {}
    total_chars = 0

    for c in chunks:
        by_layer[c.layer or "unknown"] = by_layer.get(c.layer or "unknown", 0) + 1
        if c.person:
            by_person[c.person] = by_person.get(c.person, 0) + 1
        total_chars += len(c.text)

    print(f"Total chunks: {len(chunks)}")
    print(f"Total chars: {total_chars:,} ({total_chars // 4:,} est. tokens)")
    print("\nBy layer:")
    for layer, count in sorted(by_layer.items()):
        print(f"  {layer}: {count}")
    print("\nBy person:")
    for person, count in sorted(by_person.items()):
        print(f"  {person}: {count}")
    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
