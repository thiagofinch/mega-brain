"""Lazy upsert facade for per-batch embeddings.

This module is invoked by ``cmd_process_batch`` (Step 3 of the chunk → embed
→ upsert transaction).  The actual bucket-wide index materialization is
performed downstream by ``cmd_rag_index`` (Phase 4.5, Art. XV), which reads
all persisted artifacts under ``artifacts/embeddings/<slug>/*-embeddings.json``
and rebuilds the BM25 + vector + graph indexes atomically.

So this module's job during ``process_batch`` is:

* confirm that the embeddings list passed in is well-formed,
* return an honest count of embeddings *queued* for indexation,
* never lie about what was written.

This avoids the anti-pattern of pretending the index was updated when only the
on-disk artifacts were touched.  The honest return shape lets ``cmd_finalize``
report accurate progress in the EXECUTION REPORT and FULL PIPELINE REPORT.

Contract
--------
``upsert_to_index(embeddings, *, bucket, slug) -> dict``

* ``embeddings``  - list of embedding dicts each carrying ``embedding`` (vector)
  and optionally ``text``, ``chunk_id``, ``metadata``, ``embedding_model``.
* ``bucket``      - knowledge bucket: ``"external"``, ``"business"`` or
  ``"personal"`` (used for downstream routing - bucket isolation Art. XIII).
* ``slug``        - source/person slug (e.g. ``"alex-hormozi"``).

Returns a dict with ``upserted`` (int — number of valid embeddings ready),
``bucket``, ``slug`` and ``deferred_to`` (the downstream command that
actually materializes the index).
"""

from __future__ import annotations

from typing import Any


def upsert_to_index(
    embeddings: list[dict[str, Any]] | Any,
    *,
    bucket: str = "external",
    slug: str = "unknown",
) -> dict[str, Any]:
    """Acknowledge a batch of embeddings ready for Phase 4.5 indexation.

    See module docstring for full contract.
    """
    if not isinstance(embeddings, list):
        return {
            "upserted": 0,
            "bucket": bucket,
            "slug": slug,
            "reason": "embeddings_not_a_list",
        }

    valid = 0
    for emb in embeddings:
        if not isinstance(emb, dict):
            continue
        vec = emb.get("embedding")
        if isinstance(vec, list) and vec:
            valid += 1

    return {
        "upserted": valid,
        "bucket": bucket,
        "slug": slug,
        "deferred_to": "cmd_rag_index",
    }
