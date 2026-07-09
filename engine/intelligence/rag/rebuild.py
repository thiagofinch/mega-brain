#!/usr/bin/env python3
"""
REBUILD - RAG Index + Knowledge Graph Full Rebuild
====================================================
Rebuilds all RAG indexes (BM25 per bucket) and the knowledge graph
in a single deterministic pass.  No LLM calls.

Called automatically by the MCE pipeline ``cmd_finalize`` step, or
manually via CLI for maintenance / recovery.

Usage::

    python3 -m core.intelligence.rag.rebuild [--bucket BUCKET] [--full]

Options:
    --bucket external|business|personal|all   (default: all)
    --full   Include vector embeddings (requires OPENAI_API_KEY)

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import time
from typing import Any


def _dual_write_pgvector(
    bucket: str,
    idx: Any,
    reflect_entity_type: bool = False,
    entity_type_extractor: Any = None,
) -> dict[str, Any]:
    """Mirror a freshly-built index's vectors into pgvector halfvec(3072).

    Closes Gap A (completude-total.S1): the indexation used to write embeddings
    ONLY to ``vectors.json`` while the query path reads EXCLUSIVELY from pgvector,
    so new material was invisible to search. After ``idx.save()`` persists the
    JSON, this writes the SAME embeddings to pgvector with the etiquetagem tags.

    Pairing invariant (from HybridIndex.build): ``idx.chunks[i]`` is positionally
    aligned with ``idx.vector.vectors[i]`` — both are filtered from the SAME single
    pass (hybrid_index.py content_sha write-gate). We zip them; a length mismatch
    is a hard error (never silently truncate).

    Idempotency (AC2): ``add_batch`` UPSERTs on ``chunk_id`` (a content-stable id).
    Re-running with byte-identical input re-writes identical rows — row count does
    not grow. Bucket isolation (AC4): one ``PgVectorStore(bucket=b)`` per bucket;
    the bucket column is set per row, never widened.

    Fail-loud (AC5): any pgvector write error PROPAGATES. We do NOT fall back to
    JSON-only — a resolved-but-failing backend must BLOCK the indexation (Art. XV),
    not silently degrade.

    No-op when ``idx.vector.vectors`` is empty (a BM25-only / ``skip_vectors``
    build): there is nothing to mirror, and the save guard already preserved any
    existing ``vectors.json``. Returns a small stats dict for the caller's report.

    Typed ingestion (STORY-F1-1): each chunk is also stamped with an
    ``entity_type`` (the Object Type of its knowledge — the F1-15 typed filter's
    vocabulary) and a ``source_content_sha`` (SHA-256 of its source file, R3
    provenance), both landing in the JSONB ``metadata`` column (no DDL — the
    ``entity_type``/``graph_id`` promotion to first-class columns is F1-15's job).
    DNA chunks get ``entity_type`` deterministically (zero LLM). Non-DNA chunks
    get it via the 2-pass reflection ONLY when ``reflect_entity_type=True`` — the
    default (``False``) keeps the standard rebuild deterministic / no-LLM, so this
    change never fires a per-chunk LLM call in the automatic pipeline path (the
    corpus-wide typed backfill is F1-15, not this function).
    """
    vectors = getattr(idx.vector, "vectors", None) or []
    chunks = idx.chunks or []
    if not vectors:
        return {"dual_write": "skipped", "reason": "no vectors (BM25-only build)"}

    if len(vectors) != len(chunks):
        # The positional pairing is a build invariant; a mismatch means the index
        # is internally inconsistent. Fail loud rather than mis-pair embeddings.
        raise RuntimeError(
            f"[dual_write_pgvector] bucket={bucket}: chunks({len(chunks)}) != "
            f"vectors({len(vectors)}); refusing to mis-pair (Art. XV fail-loud)."
        )

    from .pgvector_store import PgVectorStore
    from .tagging import derive_entity_type, derive_tags, source_content_sha

    chunk_ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []
    # Per-source cache: read + hash each source file ONCE per rebuild (many chunks
    # share a source), not once per chunk. None stays None (honest gap).
    source_sha_cache: dict[str, str | None] = {}
    entity_tagged = 0
    entity_llm_calls = 0
    for chunk in chunks:
        # Inject the bucket being rebuilt (the authoritative signal) before
        # deriving the tag. The chunk dict's own ``bucket`` field is the chunker's
        # construction-time DEFAULT ("external" — chunk_markdown/chunk_yaml never
        # pass bucket=), NOT the real bucket. Without this, ``derive_tags`` could
        # not route a personal/business chunk to its source_type and fell into the
        # extraction-gap (None, None) for 100% of rows. We spread into a NEW dict so
        # the original chunk is never mutated.
        chunk_with_bucket = {**chunk, "bucket": bucket}
        source_type, quality_tier = derive_tags(chunk_with_bucket)
        # entity_type (STORY-F1-1): DNA → deterministic (zero LLM); non-DNA →
        # 2-pass reflection ONLY when reflect_entity_type is on (else honest None).
        entity_type, et_telemetry = derive_entity_type(
            chunk_with_bucket,
            reflect=reflect_entity_type,
            extractor=entity_type_extractor,
        )
        entity_llm_calls += et_telemetry.get("llm_calls", 0)
        if entity_type is not None:
            entity_tagged += 1
        # source_content_sha (STORY-F1-1 / R3 provenance): hash the SOURCE file,
        # cached per source_file. Uses the chunk's real ``source_file`` path.
        sf = chunk.get("source_file", "") or ""
        if sf not in source_sha_cache:
            source_sha_cache[sf] = source_content_sha(sf)
        meta = dict(chunk.get("metadata") or {})
        # Carry the fields the writer persists as first-class columns, sourced
        # from the chunk's real signals (No Invention — None where unprovable).
        meta.setdefault("source_file", chunk.get("source_file", ""))
        meta.setdefault("person", chunk.get("person", ""))
        meta.setdefault("domain", chunk.get("domain", ""))
        meta.setdefault("layer", chunk.get("layer", ""))
        meta.setdefault("section", chunk.get("section", ""))
        meta["source_type"] = source_type
        meta["quality_tier"] = quality_tier
        # New JSONB metadata fields (F1-15 promotes entity_type to a column later).
        meta["entity_type"] = entity_type
        meta["source_content_sha"] = source_sha_cache[sf]
        chunk_ids.append(chunk.get("chunk_id", ""))
        texts.append(chunk.get("text", ""))
        metadatas.append(meta)

    store = PgVectorStore(bucket=bucket)
    store.add_batch(chunk_ids, texts, vectors, metadatas)
    tagged = sum(1 for m in metadatas if m.get("source_type") is not None)
    provenance = sum(1 for m in metadatas if m.get("source_content_sha") is not None)
    return {
        "dual_write": "ok",
        "rows": len(chunk_ids),
        "source_type_tagged": tagged,
        "source_type_gap": len(chunk_ids) - tagged,
        "entity_type_tagged": entity_tagged,
        "entity_type_gap": len(chunk_ids) - entity_tagged,
        "entity_type_llm_calls": entity_llm_calls,
        "entity_type_reflect": reflect_entity_type,
        "source_content_sha_present": provenance,
    }


def rebuild(
    bucket: str = "all",
    skip_vectors: bool = True,
    incremental: bool = False,
    dual_write_pgvector: bool = True,
    reflect_entity_type: bool = False,
    entity_type_extractor: Any = None,
) -> dict[str, Any]:
    """Rebuild RAG indexes for specified bucket(s) and knowledge graph.

    Args:
        bucket: Which bucket to rebuild --
            ``"external"``, ``"business"``, ``"personal"``, or ``"all"``.
        skip_vectors: If ``True`` (default), only build BM25 indexes.
            Set to ``False`` for full vector rebuild (needs OPENAI_API_KEY).
        incremental: If ``True`` (STORY-MCE-INCREMENTAL-RAG-INDEX) and
            ``skip_vectors=False``, reuse prior vectors keyed by content_sha and
            embed only new/changed chunks. The per-bucket ``target_dir`` is passed
            down as ``index_dir`` so prior state is loaded from the SAME bucket dir
            (Art. XIII isolation preserved). Default ``False`` = full rebuild,
            behavior bit-for-bit unchanged (AC9).
        dual_write_pgvector: If ``True`` (default — completude-total.S1, Gap A),
            mirror each freshly-built embedding into pgvector halfvec(3072) with
            its source_type/quality_tier tag right after ``idx.save()``. No-op on a
            BM25-only build (no vectors to mirror). Set ``False`` for a pure-BM25
            maintenance rebuild that must not touch pgvector.
        reflect_entity_type: If ``True`` (STORY-F1-1), run the non-DNA 2-pass
            reflection to populate ``entity_type`` for non-DNA chunks (≤1 LLM call
            per non-DNA chunk). Default ``False`` keeps the rebuild deterministic /
            zero-LLM — DNA chunks are ALWAYS typed deterministically regardless.
            The corpus-wide typed backfill (turning this on for a full rebuild) is
            F1-15's job, not the automatic pipeline path.
        entity_type_extractor: Optional pass-1 extractor override (dependency
            injection for the 2-pass reflection). ``None`` uses the default OpenAI
            schema-guided extractor. Only consulted when ``reflect_entity_type``.

    Returns:
        Stats dict with per-bucket chunk counts, graph stats, and the S4 fan-out
        parity report::

            {
                "external": {"chunks": 3012, "dir": ".data/rag_index", "pgvector": {...}},
                "business": {"chunks": 48, "dir": ".data/rag_business", "pgvector": {...}},
                "personal": {"chunks": 12, "dir": "knowledge/personal/index"},
                "graph": {"total_entities": 1302, "total_edges": 2508, ...},
                "graph_by_bucket": {...},
                "vault": {...},
                "fanout": {"parity_ok": True, "by_bucket": {...}, "gaps": []},
                "duration_s": 4.2,
            }
    """
    from engine.paths import KNOWLEDGE_PERSONAL, RAG_BUSINESS, RAG_INDEX

    from .graph_builder import build_graph, graph_file_for_bucket
    from .hybrid_index import HybridIndex

    t0 = time.monotonic()
    results: dict[str, Any] = {}

    # -- Per-bucket BM25 indexes ------------------------------------------

    buckets_to_build = ["external", "business", "personal"] if bucket == "all" else [bucket]

    bucket_dirs = {
        "external": RAG_INDEX,
        "business": RAG_BUSINESS,
        "personal": KNOWLEDGE_PERSONAL / "index",
    }

    for b in buckets_to_build:
        target_dir = bucket_dirs.get(b)
        if target_dir is None:
            results[b] = {"error": f"Unknown bucket: {b}"}
            continue

        idx = HybridIndex.build_for_bucket(
            b,
            skip_vectors=skip_vectors,
            incremental=incremental,
            index_dir=target_dir,
        )
        idx.save(target_dir)
        results[b] = {
            "chunks": len(idx.chunks),
            "dir": str(target_dir),
        }

        # -- Dual-write to pgvector (Gap A — completude-total.S1) ----------
        # After the JSON is persisted, mirror the embeddings into pgvector with
        # their etiquetagem tags so the read path (which queries pgvector only)
        # sees newly-indexed material. No-op on a BM25-only build. Fail-loud: a
        # write error propagates and BLOCKS the rebuild (AC5 / Art. XV).
        if dual_write_pgvector:
            results[b]["pgvector"] = _dual_write_pgvector(
                b,
                idx,
                reflect_entity_type=reflect_entity_type,
                entity_type_extractor=entity_type_extractor,
            )

    # -- Knowledge graph: ONE graph per bucket (STORY-RAG-VM-G2) -----------
    #
    # Determinism (AC9): build buckets in a FIXED order and save each to its own
    # ``graph-{bucket}.json`` (Art. XIII — files never merge). The external graph
    # additionally mirrors to the legacy ``graph.json`` alias inside ``save()`` for
    # one release. A bucket with no DNA dir (e.g. personal today) is a graceful
    # no-op (empty graph saved). Mirrors the BM25 ``buckets_to_build`` loop above so
    # the graph and the index always cover the same buckets.
    graph_results: dict[str, Any] = {}
    for b in buckets_to_build:
        g = build_graph(bucket=b)
        g.save(graph_file_for_bucket(b))
        graph_results[b] = g.stats
    # Back-compat: ``results["graph"]`` historically meant the external graph stats
    # (sole graph). Keep that key pointing at external; add per-bucket detail beside it.
    results["graph"] = graph_results.get("external", {})
    results["graph_by_bucket"] = graph_results

    # -- Vault Cortex regen (STORY-S6, Fase B) ----------------------------
    #
    # CONTINUOUS REGEN (founder NON-NEGOTIABLE): the moment the graph is
    # reconstructed + saved above, the Obsidian vault at ``vault/`` regenerates so
    # it tracks the graph on every rebuild (new ingestion → new node → new leaf,
    # no manual command). The vault reads the just-saved ``graph-{bucket}.json``
    # read-only — it never rebuilds/re-embeds/re-chunks (AC7).
    #
    # NON-FATAL (Art. XII): a failure here is a secondary-output error — it WARNs
    # and records the reason, but NEVER fails the graph/vector rebuild (mirrors the
    # ``log_generator`` treatment in ``cmd_finalize``). Idempotent: same graph →
    # byte-identical vault (no git/Obsidian churn).
    try:
        from .vault_generator import regenerate_vault

        results["vault"] = regenerate_vault()
    except Exception as exc:  # secondary output, must not break rebuild (Art. XII)
        results["vault"] = {"error": f"{type(exc).__name__}: {exc}"}

    # -- Fan-out parity (completude-total.S4) ------------------------------
    # S4 formalizes the three write-paths above (vector via S1, graph via S3/G2,
    # vault via S6) as ONE coherent fan-out and PROVES coverage: every bucket in
    # ``buckets_to_build`` was routed through ALL THREE outputs — no bucket is
    # silently skipped in one index but present in another (the lateral-door drift
    # this story closes). See ``_compute_fanout_parity``.
    results["fanout"] = _compute_fanout_parity(buckets_to_build, results)

    results["duration_s"] = round(time.monotonic() - t0, 2)
    return results


def _compute_fanout_parity(
    buckets: list[str],
    results: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate real per-bucket coverage across the three fan-out outputs.

    S4 anti-failure invariant: every bucket in ``buckets`` must have been ROUTED
    through all three outputs — vector (S1 dual-write / BM25 chunks), graph (S3/G2
    per-bucket graph), and vault (S6 regen). This does NOT re-run any write-path;
    it reads the counts the three subsystems already recorded in ``results`` and
    reports them so a gap is visible, never masked.

    No Invention (Art. IV): the counts are the REAL numbers each subsystem
    produced. A bucket that legitimately has zero content (e.g. ``personal`` with
    no DNA) shows ``vector=0 / graph_entities=0`` — that is CONSISTENT coverage
    (all three outputs saw the same empty bucket), not a gap. A gap is when a
    bucket was skipped in one output but not another, or a write-path errored.

    Returns::

        {
          "by_bucket": {
             "external": {"vector_rows": N, "bm25_chunks": M, "graph_entities": E,
                          "graph_edges": D, "vault_leaves": L, "covered": True,
                          "outputs_present": ["vector","graph","vault"],
                          "outputs_missing": []},
             ...
          },
          "buckets_expected": [...],
          "buckets_covered": [...],
          "gaps": [ {"bucket": ..., "missing": [...], "reason": ...}, ... ],
          "parity_ok": True,
        }
    """
    vault = results.get("vault") or {}
    vault_buckets = vault.get("buckets") if isinstance(vault, dict) else None
    vault_errored = isinstance(vault, dict) and "error" in vault
    graph_by_bucket = results.get("graph_by_bucket") or {}

    by_bucket: dict[str, Any] = {}
    gaps: list[dict[str, Any]] = []
    covered_buckets: list[str] = []

    for b in buckets:
        bucket_res = results.get(b) or {}
        # A per-bucket error in the BM25/vector loop means the whole bucket was not
        # built — that IS a fan-out gap for every output.
        bucket_build_error = "error" in bucket_res

        # -- Vector output (S1): the BM25 index always runs; the pgvector mirror is
        #    a no-op on a BM25-only build (skipped) but still "present" (routed).
        pgv = bucket_res.get("pgvector") or {}
        vector_present = (not bucket_build_error) and ("chunks" in bucket_res)
        vector_rows = pgv.get("rows", 0)
        bm25_chunks = bucket_res.get("chunks", 0)
        # A pgvector write that ERRORED (not "ok"/"skipped") is a vector gap.
        pgv_state = pgv.get("dual_write")
        vector_errored = pgv_state not in (None, "ok", "skipped")

        # -- Graph output (S3/G2): present when this bucket has a stats entry.
        graph_stats = graph_by_bucket.get(b)
        graph_present = isinstance(graph_stats, dict) and "error" not in graph_stats
        graph_entities = (graph_stats or {}).get("total_entities", 0) if graph_present else 0
        graph_edges = (graph_stats or {}).get("total_edges", 0) if graph_present else 0

        # -- Vault output (S6): present when the vault regen produced a per-bucket
        #    entry. A vault-level error is NON-FATAL (Art. XII) but IS recorded as a
        #    vault gap so the operator sees the secondary output did not cover it.
        if vault_errored or not isinstance(vault_buckets, dict):
            vault_present = False
            vault_leaves = 0
        else:
            vb = vault_buckets.get(b)
            vault_present = isinstance(vb, dict)
            vault_leaves = (vb or {}).get("leaves", 0) if vault_present else 0

        outputs_present: list[str] = []
        outputs_missing: list[str] = []
        (outputs_present if (vector_present and not vector_errored) else outputs_missing).append(
            "vector"
        )
        (outputs_present if graph_present else outputs_missing).append("graph")
        (outputs_present if vault_present else outputs_missing).append("vault")

        covered = not outputs_missing
        by_bucket[b] = {
            "vector_rows": vector_rows,
            "bm25_chunks": bm25_chunks,
            "graph_entities": graph_entities,
            "graph_edges": graph_edges,
            "vault_leaves": vault_leaves,
            "outputs_present": outputs_present,
            "outputs_missing": outputs_missing,
            "covered": covered,
        }
        if covered:
            covered_buckets.append(b)
        else:
            reason_bits = []
            if bucket_build_error:
                reason_bits.append(f"bm25/vector build error: {bucket_res.get('error')}")
            if vector_errored:
                reason_bits.append(f"pgvector dual_write={pgv_state}")
            if not graph_present:
                reason_bits.append("graph missing for bucket")
            if not vault_present:
                reason_bits.append("vault error" if vault_errored else "vault missing for bucket")
            gaps.append(
                {
                    "bucket": b,
                    "missing": outputs_missing,
                    "reason": "; ".join(reason_bits) or "output not routed",
                }
            )

    return {
        "by_bucket": by_bucket,
        "buckets_expected": list(buckets),
        "buckets_covered": covered_buckets,
        "gaps": gaps,
        "parity_ok": not gaps,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Rebuild RAG indexes and knowledge graph")
    parser.add_argument(
        "--bucket",
        default="all",
        choices=["external", "business", "personal", "all"],
        help="Which bucket to rebuild (default: all)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include vector embeddings (requires OPENAI_API_KEY)",
    )
    args = parser.parse_args()

    skip_vectors = not args.full

    print(f"\n{'=' * 60}")
    print("RAG INDEX REBUILD")
    print(f"{'=' * 60}")
    print(f"  Bucket: {args.bucket}")
    print(f"  Mode:   {'full (BM25 + vectors)' if args.full else 'BM25-only'}")
    print(f"{'─' * 60}\n")

    results = rebuild(bucket=args.bucket, skip_vectors=skip_vectors)

    # Pretty-print results
    for key in ("external", "business", "personal"):
        if key in results:
            info = results[key]
            if "error" in info:
                print(f"  {key}: ERROR - {info['error']}")
            else:
                print(f"  {key}: {info['chunks']} chunks -> {info['dir']}")

    if "graph" in results:
        g = results["graph"]
        print(
            f"\n  graph: {g.get('total_entities', 0)} entities, " f"{g.get('total_edges', 0)} edges"
        )

    # -- S4 fan-out parity report --
    fanout = results.get("fanout")
    if fanout:
        print("\n  fan-out parity (vector | graph | vault):")
        for b, info in fanout.get("by_bucket", {}).items():
            mark = "OK" if info.get("covered") else "GAP"
            print(
                f"    [{mark}] {b}: vector={info.get('vector_rows', 0)} rows "
                f"(bm25={info.get('bm25_chunks', 0)}) | "
                f"graph={info.get('graph_entities', 0)} entities | "
                f"vault={info.get('vault_leaves', 0)} leaves"
            )
        gaps = fanout.get("gaps", [])
        if gaps:
            print("\n  ⚠ fan-out GAPS (a bucket missing from an output):")
            for gap in gaps:
                print(f"    - {gap['bucket']}: missing {gap['missing']} — {gap['reason']}")
        else:
            print("  parity_ok: all buckets covered by all three outputs")

    duration = results.get("duration_s", 0)
    print(f"\n  Total time: {duration}s")
    print(f"\n{'=' * 60}")

    # Also dump machine-readable JSON to stdout
    print("\n--- JSON ---")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
