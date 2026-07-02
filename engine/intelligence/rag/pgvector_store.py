"""pgvector Store — portable vector storage for Mega Brain RAG.

Implements the ``VectorStore`` ABC. Historically this backend spoke to Supabase
exclusively over **PostgREST / RPC** (``client.upsert``, ``client.rpc``,
``client.select``, ``client.delete``) — conveniences that only exist on a hosted
Supabase deployment and do NOT work against a generic PostgreSQL server.

Story: STORY-RAG-2 (S2) — Phase 1 Wave 2 (original Supabase backend)
       STORY-GBA-F1.3 — Fase 1 (Portabilidade OSS): the 7 PostgREST calls
                        (``.rpc`` x1, ``.select`` x4, ``.upsert`` x2) — plus the
                        two ``.delete`` PostgREST writes — were made portable.

What F1.3 changed (and what it deliberately did NOT)
----------------------------------------------------
The original REST code is preserved **bit-for-bit** as the Supabase fallback
path so RNF-2 (no regression on the Supabase route) holds. On top of it, every
operation now FIRST tries the portable SQL backend (:class:`PostgresStore`,
STORY-GBA-F1.1) when a direct DSN is available, and only falls back to PostgREST
when it is not. The net effect:

    DATABASE_URL set  → pure-SQL (psycopg2) path  → portable, OSS-clonable
    only SUPABASE_URL → PostgREST / RPC path      → unchanged legacy behavior

Why delegate to PostgresStore instead of inlining new SQL here?
The pure-SQL translation of EVERY one of these operations already exists,
tested for parity, in :class:`PostgresStore` (F1.1): same ``rag_chunks`` columns,
same UPSERT-on-``chunk_id`` write semantics, the same ``match_rag_chunks`` search
semantics (``1 - (embedding <=> query)`` with a threshold floor, bucket-isolated,
ordered by distance, capped at ``top_k``), and the same ``SearchResult`` shape.
Re-typing that SQL inline would duplicate a tested surface and violate REUSE >
CREATE. Delegation gives identical behavior with one source of SQL truth, while
``PgVectorStore`` stays the public face callers already construct.

Constitution Art. XIII: bucket isolation is enforced at query time via the
``bucket`` filter — on BOTH paths. Never pass a widening filter unless you are an
explicitly authorized cross-bucket agent (the knowledge oracle).

Constitution Art. VI (no secrets in code): the SQL path's DSN comes from
``DATABASE_URL``; the REST path's credentials come from ``SUPABASE_URL`` /
``SUPABASE_SERVICE_ROLE_KEY``. Both are read from the environment.
"""

from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING

from .vector_store import SearchResult, VectorStore

if TYPE_CHECKING:
    from .postgres_store import PostgresStore


class PgVectorStore(VectorStore):
    """Portable pgvector implementation of VectorStore.

    Prefers the pure-SQL :class:`PostgresStore` backend (psycopg2, works on any
    Postgres) when ``DATABASE_URL`` is configured, and transparently falls back
    to the legacy Supabase PostgREST / RPC client otherwise. Both paths share the
    same ``rag_chunks`` schema and the same semantics.

    Usage::

        store = PgVectorStore(bucket="external")
        store.add(chunk_id, text, embedding, metadata)
        results = store.search(query_embedding, top_k=30)
    """

    def __init__(
        self,
        bucket: str = "external",
        match_threshold: float = 0.40,
    ) -> None:
        """Initialise pgvector store.

        Args:
            bucket: Knowledge bucket — ``"external"`` | ``"business"`` | ``"personal"``.
                    Used as default filter for all search calls.
            match_threshold: Minimum similarity score to return results.
                             Default 0.40 per S7 (MATCH_THRESHOLD update).
        """
        self.bucket = bucket
        self.match_threshold = match_threshold
        self._client = None  # lazy init (Supabase PostgREST client)
        self._sql_store: PostgresStore | None = None  # lazy init (psycopg2 path)
        self._sql_resolved = False  # have we tried to resolve the SQL backend?

    # ------------------------------------------------------------------
    # Backend resolution
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazy-initialise the legacy Supabase PostgREST client."""
        if self._client is None:
            from engine.providers import supabase_client

            self._client = supabase_client
        return self._client

    def _get_sql_store(self) -> PostgresStore | None:
        """Return the portable :class:`PostgresStore` if a DSN is available.

        Resolution is attempted once and memoised. When ``DATABASE_URL`` is set,
        every operation runs through pure SQL (psycopg2) for full portability;
        when it is absent, this returns ``None`` and callers transparently use
        the Supabase PostgREST path — preserving legacy behavior with no
        regression (RNF-2).
        """
        if not self._sql_resolved:
            self._sql_resolved = True
            dsn = (os.environ.get("DATABASE_URL") or "").strip()
            if dsn:
                from .postgres_store import PostgresStore

                self._sql_store = PostgresStore(
                    bucket=self.bucket,
                    match_threshold=self.match_threshold,
                    dsn=dsn,
                )
        return self._sql_store

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add(
        self,
        chunk_id: str,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Insert or update a single chunk with its embedding."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: INSERT ... ON CONFLICT (chunk_id) DO UPDATE (F1.1).
            sql_store.add(chunk_id, text, embedding, metadata)
            return

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        record = {
            "chunk_id": chunk_id,
            "bucket": self.bucket,
            "source_path": (metadata or {}).get("source_file", ""),
            "chunk_text": text,
            "embedding": embedding,
            "person": (metadata or {}).get("person", ""),
            "domain": (metadata or {}).get("domain", ""),
            "layer": (metadata or {}).get("layer", ""),
            "section": (metadata or {}).get("section", ""),
            "metadata": metadata or {},
        }
        client.upsert("rag_chunks", record, on_conflict="chunk_id")

    def add_batch(
        self,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Insert or update a batch of chunks in a single round-trip."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: execute_values INSERT ... ON CONFLICT (F1.1).
            sql_store.add_batch(chunk_ids, texts, embeddings, metadatas)
            return

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        if metadatas is None:
            metadatas = [{}] * len(chunk_ids)

        records = [
            {
                "chunk_id": cid,
                "bucket": self.bucket,
                "source_path": meta.get("source_file", ""),
                "chunk_text": text,
                "embedding": emb,
                "person": meta.get("person", ""),
                "domain": meta.get("domain", ""),
                "layer": meta.get("layer", ""),
                "section": meta.get("section", ""),
                "metadata": meta,
            }
            for cid, text, emb, meta in zip(chunk_ids, texts, embeddings, metadatas)
        ]
        client.upsert("rag_chunks", records, on_conflict="chunk_id")

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 30,
        bucket_filter: str | None = "SELF",  # SELF = use self.bucket
    ) -> list[SearchResult]:
        """Similarity search.

        Portable path inlines ``match_rag_chunks`` semantics in pure SQL (F1.1);
        legacy path calls the server-side RPC over PostgREST. Both honour the
        same bucket filter, threshold floor, ordering, and limit.

        Args:
            query_embedding: Query embedding (dimensions per embedding_config.py).
            top_k: Number of results to return.
            bucket_filter: Override bucket filter.
                          ``"SELF"`` (default) = use ``self.bucket``.
                          ``None`` = all buckets (cross-bucket, restricted).
        """
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: SELECT ... ORDER BY embedding <=> query LIMIT (F1.1).
            return sql_store.search(
                query_embedding, top_k=top_k, bucket_filter=bucket_filter
            )

        # Legacy Supabase PostgREST / RPC path (unchanged).
        client = self._get_client()

        # Resolve bucket filter
        if bucket_filter == "SELF":
            effective_bucket = self.bucket
        else:
            effective_bucket = bucket_filter

        try:
            rows = client.rpc(
                "match_rag_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": self.match_threshold,
                    "match_count": top_k,
                    "bucket_filter": effective_bucket,
                },
            )
        except Exception as e:
            warnings.warn(f"[PgVectorStore] search failed: {e}", stacklevel=2)
            return []

        if not rows:
            return []

        return [
            SearchResult(
                chunk_id=row["chunk_id"],
                text=row["chunk_text"],
                metadata={
                    "source_path": row.get("source_path", ""),
                    "bucket": row.get("bucket", self.bucket),
                    "person": row.get("person", ""),
                    "layer": row.get("layer", ""),
                    "section": row.get("section", ""),
                    **(row.get("metadata") or {}),
                },
                score=float(row["similarity"]),
            )
            for row in rows
        ]

    def get_embeddings_by_chunk_ids(
        self,
        chunk_ids: list[str],
        column: str = "embedding",
    ) -> dict[str, list[float]]:
        """Hydrate stored embeddings for the given chunk_ids from the ACTIVE column.

        Ported from gbrain ``BrainEngine.getEmbeddingsByChunkIds`` (hybrid.ts,
        SHA 4ee530f, hydration at :1932). The cosine re-score (F2.3) must compare
        the query embedding against the SAME vector space the dense retrieval
        ranked in. We therefore READ the already-stored vector from the active
        column — we never recompute it. Recomputing could (pre-F0.2) place the
        chunk in a divergent space and corrupt cosine; reading the persisted
        column guarantees space parity with the HNSW/pgvector ranking.

        Args:
            chunk_ids: Chunk identifiers to hydrate.
            column: Embedding column to read. Defaults to ``"embedding"`` — the
                single active column established by STORY-GBA-F0.2 (one space).

        Returns:
            Mapping ``{chunk_id: embedding}``. Chunks with no stored vector are
            omitted. Returns ``{}`` on any DB error (fail-open: caller degrades
            to plain RRF order, exactly like gbrain's ``catch → return results``).
        """
        if not chunk_ids:
            return {}

        # M1 (CodeRabbit PR34): whitelist ``column`` BEFORE either path. The SQL
        # store (PostgresStore) already validates internally (F1.1), but the
        # legacy PostgREST path below interpolates ``column`` straight into the
        # query string with no guard — an arbitrary column would allow injection.
        # Mirror PostgresStore's fail-open behavior (warn + empty mapping → caller
        # degrades to plain RRF order) for both paths so the contract is uniform.
        if column not in {"embedding"}:
            warnings.warn(
                f"[PgVectorStore] refusing unknown embedding column: {column!r}",
                stacklevel=2,
            )
            return {}

        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: SELECT chunk_id, embedding WHERE bucket AND
            # chunk_id IN (...) — column whitelisted against injection (F1.1).
            return sql_store.get_embeddings_by_chunk_ids(chunk_ids, column=column)

        # Legacy Supabase PostgREST path (column whitelisted above).
        client = self._get_client()
        # PostgREST in.(...) filter — bucket-scoped (Art. XIII) and column-scoped.
        id_list = ",".join(str(cid) for cid in chunk_ids)
        query = (
            f"bucket=eq.{self.bucket}"
            f"&chunk_id=in.({id_list})"
            f"&select=chunk_id,{column}"
        )
        try:
            rows = client.select("rag_chunks", query)
        except Exception as e:
            warnings.warn(
                f"[PgVectorStore] embedding hydration failed: {e}",
                stacklevel=2,
            )
            return {}

        out: dict[str, list[float]] = {}
        for row in rows or []:
            vec = row.get(column)
            if vec is None:
                continue
            # pgvector may serialize as a JSON string "[...]" depending on the
            # PostgREST representation; normalize to list[float].
            if isinstance(vec, str):
                try:
                    import json

                    vec = json.loads(vec)
                except (ValueError, TypeError):
                    continue
            if not isinstance(vec, (list, tuple)):
                continue
            out[row["chunk_id"]] = [float(x) for x in vec]
        return out

    def get(self, chunk_id: str) -> SearchResult | None:
        """Retrieve a chunk by ID."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: SELECT ... WHERE chunk_id = %s (F1.1).
            return sql_store.get(chunk_id)

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        try:
            rows = client.select(
                "rag_chunks",
                f"chunk_id=eq.{chunk_id}&select=chunk_id,chunk_text,source_path,bucket,person,layer,section,metadata",
            )
        except Exception:
            return None
        if not rows:
            return None
        row = rows[0]
        return SearchResult(
            chunk_id=row["chunk_id"],
            text=row["chunk_text"],
            metadata={
                "source_path": row.get("source_path", ""),
                "bucket": row.get("bucket", ""),
                "person": row.get("person", ""),
                "layer": row.get("layer", ""),
                "section": row.get("section", ""),
                **(row.get("metadata") or {}),
            },
            score=1.0,
        )

    def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: DELETE FROM rag_chunks WHERE chunk_id = %s (F1.1).
            return sql_store.delete(chunk_id)

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        try:
            client.delete("rag_chunks", f"chunk_id=eq.{chunk_id}")
            return True
        except Exception:
            return False

    def count(self) -> int:
        """Count chunks for this bucket."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: SELECT COUNT(*) WHERE bucket = %s (F1.1).
            return sql_store.count()

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        try:
            rows = client.select(
                "rag_chunks",
                f"bucket=eq.{self.bucket}&select=id",
            )
            return len(rows)
        except Exception:
            return 0

    def clear(self) -> None:
        """Delete all chunks in this bucket."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: DELETE FROM rag_chunks WHERE bucket = %s (F1.1).
            sql_store.clear()
            return

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        client.delete("rag_chunks", f"bucket=eq.{self.bucket}")

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def health_check(self) -> dict:
        """Verify connectivity and row count."""
        sql_store = self._get_sql_store()
        if sql_store is not None:
            # Portable path: SELECT 1 FROM rag_chunks LIMIT 1 + count (F1.1).
            return sql_store.health_check()

        # Legacy Supabase PostgREST path (unchanged).
        client = self._get_client()
        try:
            client.select("rag_chunks", "select=id&limit=1")
            total = self.count()
            return {
                "ok": True,
                "bucket": self.bucket,
                "chunk_count": total,
                "table": "rag_chunks",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
