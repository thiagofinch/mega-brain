"""Postgres Store — generic Postgres-backed vector storage for Mega Brain RAG.

Implements the ``VectorStore`` ABC (``vector_store.py:22``) using **psycopg2 and
pure SQL** against ANY PostgreSQL server with the ``pgvector`` extension. Unlike
``PgVectorStore`` (which speaks to Supabase over PostgREST / RPC), this backend
needs only a ``DATABASE_URL`` — no Supabase account, no PostgREST, no service
key. That is what unlocks the OSS clone path (STORY-GBA-F1.1): a developer who
clones the repo can run a local ``pgvector/pgvector:pg16`` container and have a
fully working RAG store with zero hosted dependencies.

Story: STORY-GBA-F1.1 — Fase 1 (Portabilidade OSS)
Date: 2026-06-20
Tipo: CREATE INTERNO — espelha o contrato funcional de ``PgVectorStore`` sobre
      as MESMAS tabelas (``rag_chunks``) e a MESMA semântica de busca
      (``match_rag_chunks``), porém em SQL puro. Não porta código do gbrain.

Schema: rag_chunks table (see scripts/migrate_rag_chunks_pgvector.sql).
        The similarity query inlines the body of the ``match_rag_chunks`` SQL
        function so the backend is self-contained (no server-side function
        required for read paths) while remaining bit-for-bit compatible with the
        Supabase-resident function:

            1 - (embedding <=> query) AS similarity
            WHERE bucket = :bucket AND embedding IS NOT NULL
                  AND 1 - (embedding <=> query) > :threshold
            ORDER BY embedding <=> query
            LIMIT :count

Constitution Art. XIII: bucket isolation is enforced at query time via the
``bucket`` column filter. Never widen the filter unless you are an explicitly
authorized cross-bucket agent (the knowledge oracle).

Constitution Art. VI (no secrets in code): the DSN comes from ``DATABASE_URL``.
"""

from __future__ import annotations

import json
import os
import warnings
from typing import Any

from .vector_store import SearchResult, VectorStore

# pgvector dimension of the rag_chunks.embedding column (see migration SQL).
# Kept as a module constant so tests and DDL stay in sync.
EMBEDDING_DIM = 1024

# Default similarity floor — mirrors match_rag_chunks DEFAULT and PgVectorStore.
DEFAULT_MATCH_THRESHOLD = 0.40


def _to_pgvector_literal(embedding: list[float]) -> str:
    """Render a Python float list as a pgvector text literal: ``[1,2,3]``.

    pgvector accepts the bracketed, comma-separated form for both INSERT casts
    (``'[...]'::vector``) and distance operators. We build it explicitly instead
    of relying on psycopg2 adapters so this module has zero dependency on the
    optional ``pgvector`` Python package — pure psycopg2 + SQL, as the story
    requires.
    """
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


class PostgresStore(VectorStore):
    """Generic psycopg2 / pure-SQL implementation of ``VectorStore``.

    Functional parity with :class:`PgVectorStore`: same ``rag_chunks`` columns,
    same write semantics (UPSERT on ``chunk_id``), same search semantics
    (cosine similarity via ``<=>`` with a threshold floor, bucket-isolated),
    same ``SearchResult`` shape.

    Usage::

        store = PostgresStore(bucket="external")          # reads DATABASE_URL
        store.add(chunk_id, text, embedding, metadata)
        results = store.search(query_embedding, top_k=30)
    """

    def __init__(
        self,
        bucket: str = "external",
        match_threshold: float = DEFAULT_MATCH_THRESHOLD,
        dsn: str | None = None,
        table: str = "rag_chunks",
    ) -> None:
        """Initialise the Postgres store.

        Args:
            bucket: Knowledge bucket — ``"external"`` | ``"business"`` |
                ``"personal"``. Default filter for all search/count/clear calls.
            match_threshold: Minimum cosine similarity to return results.
                Default 0.40 (parity with ``PgVectorStore`` / ``match_rag_chunks``).
            dsn: Postgres connection string. If ``None``, read from the
                ``DATABASE_URL`` environment variable (resolved lazily at first
                connect so constructing the object never raises).
            table: Target table name. Defaults to ``rag_chunks``.
        """
        self.bucket = bucket
        self.match_threshold = match_threshold
        self._dsn = dsn
        self.table = table
        self._conn = None  # lazy init

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _resolve_dsn(self) -> str:
        dsn = self._dsn or os.environ.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError(
                "PostgresStore requires a DSN. Set DATABASE_URL or pass dsn=..."
            )
        return dsn

    def _get_conn(self):
        """Lazy-open a psycopg2 connection (autocommit) and reuse it."""
        if self._conn is None or getattr(self._conn, "closed", 1):
            import psycopg2

            self._conn = psycopg2.connect(self._resolve_dsn())
            self._conn.autocommit = True
        return self._conn

    def close(self) -> None:
        """Close the underlying connection if open."""
        if self._conn is not None and not getattr(self._conn, "closed", 1):
            self._conn.close()
        self._conn = None

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def _record_tuple(
        self, chunk_id: str, text: str, embedding: list[float], metadata: dict | None
    ) -> tuple:
        """Build the positional values tuple for an UPSERT row.

        Column order mirrors PgVectorStore.add()'s record dict exactly so the
        two backends persist identical rows for identical input.
        """
        meta = metadata or {}
        return (
            chunk_id,
            self.bucket,
            meta.get("source_file", ""),
            text,
            _to_pgvector_literal(embedding),
            meta.get("person", ""),
            meta.get("domain", ""),
            meta.get("layer", ""),
            meta.get("section", ""),
            json.dumps(meta),
        )

    _UPSERT_SQL_TMPL = (
        "INSERT INTO {table} "
        "(chunk_id, bucket, source_path, chunk_text, embedding, "
        " person, domain, layer, section, metadata) "
        "VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s::jsonb) "
        "ON CONFLICT (chunk_id) DO UPDATE SET "
        "  bucket = EXCLUDED.bucket, "
        "  source_path = EXCLUDED.source_path, "
        "  chunk_text = EXCLUDED.chunk_text, "
        "  embedding = EXCLUDED.embedding, "
        "  person = EXCLUDED.person, "
        "  domain = EXCLUDED.domain, "
        "  layer = EXCLUDED.layer, "
        "  section = EXCLUDED.section, "
        "  metadata = EXCLUDED.metadata"
    )

    def add(
        self,
        chunk_id: str,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Insert or update a single chunk with its embedding (UPSERT)."""
        sql = self._UPSERT_SQL_TMPL.format(table=self.table)
        with self._get_conn().cursor() as cur:
            cur.execute(sql, self._record_tuple(chunk_id, text, embedding, metadata))

    def add_batch(
        self,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Insert or update a batch of chunks in one round-trip (UPSERT).

        Uses ``execute_values`` so all rows ship in a single statement, the
        psycopg2 equivalent of PgVectorStore's single bulk upsert call.
        """
        if not chunk_ids:
            return
        if metadatas is None:
            metadatas = [{}] * len(chunk_ids)

        from psycopg2.extras import execute_values

        rows = [
            self._record_tuple(cid, text, emb, meta)
            for cid, text, emb, meta in zip(chunk_ids, texts, embeddings, metadatas)
        ]
        # The embedding (index 4) and metadata (index 9) need explicit casts;
        # execute_values applies the template per row.
        template = "(%s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s::jsonb)"
        insert_sql = (
            f"INSERT INTO {self.table} "
            "(chunk_id, bucket, source_path, chunk_text, embedding, "
            " person, domain, layer, section, metadata) VALUES %s "
            "ON CONFLICT (chunk_id) DO UPDATE SET "
            "  bucket = EXCLUDED.bucket, "
            "  source_path = EXCLUDED.source_path, "
            "  chunk_text = EXCLUDED.chunk_text, "
            "  embedding = EXCLUDED.embedding, "
            "  person = EXCLUDED.person, "
            "  domain = EXCLUDED.domain, "
            "  layer = EXCLUDED.layer, "
            "  section = EXCLUDED.section, "
            "  metadata = EXCLUDED.metadata"
        )
        with self._get_conn().cursor() as cur:
            execute_values(cur, insert_sql, rows, template=template)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 30,
        bucket_filter: str | None = "SELF",  # SELF = use self.bucket
    ) -> list[SearchResult]:
        """Cosine similarity search — inlines ``match_rag_chunks`` semantics.

        Mirrors ``PgVectorStore.search`` (and the server-side SQL function) to
        the letter: 1 - cosine_distance, threshold floor, bucket isolation,
        ordered by distance, capped at ``top_k``.

        Args:
            query_embedding: Query vector (same active space as stored vectors).
            top_k: Max results.
            bucket_filter: ``"SELF"`` (default) → ``self.bucket``; ``None`` →
                all buckets (cross-bucket, restricted); else explicit bucket.
        """
        if bucket_filter == "SELF":
            effective_bucket = self.bucket
        else:
            effective_bucket = bucket_filter

        vec = _to_pgvector_literal(query_embedding)
        # Build WHERE dynamically so the None (all-buckets) path is supported
        # without a magic sentinel, exactly like the SQL function's
        # (bucket_filter IS NULL OR bucket = bucket_filter).
        params: list[Any] = [vec]
        bucket_clause = ""
        if effective_bucket is not None:
            bucket_clause = "AND c.bucket = %s "
            params.append(effective_bucket)
        params.extend([vec, self.match_threshold, vec, top_k])

        sql = (
            "SELECT c.chunk_id, c.chunk_text, c.source_path, c.bucket, "
            "       c.person, c.layer, c.section, c.metadata, "
            "       1 - (c.embedding <=> %s::vector) AS similarity "
            f"FROM {self.table} c "
            "WHERE c.embedding IS NOT NULL "
            f"{bucket_clause}"
            "AND 1 - (c.embedding <=> %s::vector) > %s "
            "ORDER BY c.embedding <=> %s::vector "
            "LIMIT %s"
        )

        try:
            with self._get_conn().cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        except Exception as e:
            warnings.warn(f"[PostgresStore] search failed: {e}", stacklevel=2)
            return []

        return [
            SearchResult(
                chunk_id=row[0],
                text=row[1],
                metadata={
                    "source_path": row[2] or "",
                    "bucket": row[3] or self.bucket,
                    "person": row[4] or "",
                    "layer": row[5] or "",
                    "section": row[6] or "",
                    **(self._coerce_metadata(row[7])),
                },
                score=float(row[8]),
            )
            for row in rows
        ]

    @staticmethod
    def _coerce_metadata(raw: Any) -> dict:
        """Normalise a JSONB column value to a dict (psycopg2 may give dict or str)."""
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else {}
            except (ValueError, TypeError):
                return {}
        return {}

    def get_embeddings_by_chunk_ids(
        self,
        chunk_ids: list[str],
        column: str = "embedding",
    ) -> dict[str, list[float]]:
        """Hydrate stored embeddings for the given chunk_ids from the active column.

        Parity with ``PgVectorStore.get_embeddings_by_chunk_ids``: bucket-scoped,
        column-scoped, fail-open (returns ``{}`` on any DB error). Used by the
        F2.3 cosine re-score so the compare happens in the SAME persisted space.

        Note: ``column`` is whitelisted (only known embedding columns) to keep it
        safe from SQL injection while still allowing the active-column override.
        """
        if not chunk_ids:
            return {}
        if column not in {"embedding"}:
            warnings.warn(
                f"[PostgresStore] refusing unknown embedding column: {column!r}",
                stacklevel=2,
            )
            return {}

        placeholders = ",".join(["%s"] * len(chunk_ids))
        sql = (
            f"SELECT chunk_id, {column} FROM {self.table} "
            f"WHERE bucket = %s AND chunk_id IN ({placeholders})"
        )
        params: list[Any] = [self.bucket, *chunk_ids]
        try:
            with self._get_conn().cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        except Exception as e:
            warnings.warn(
                f"[PostgresStore] embedding hydration failed: {e}", stacklevel=2
            )
            return {}

        out: dict[str, list[float]] = {}
        for cid, vec in rows:
            parsed = self._parse_vector(vec)
            if parsed is not None:
                out[cid] = parsed
        return out

    @staticmethod
    def _parse_vector(vec: Any) -> list[float] | None:
        """Coerce a pgvector column value to ``list[float]`` (or None)."""
        if vec is None:
            return None
        # pgvector text representation: "[1,2,3]"
        if isinstance(vec, str):
            try:
                vec = json.loads(vec)
            except (ValueError, TypeError):
                return None
        if not isinstance(vec, (list, tuple)):
            return None
        try:
            return [float(x) for x in vec]
        except (ValueError, TypeError):
            return None

    def get(self, chunk_id: str) -> SearchResult | None:
        """Retrieve a chunk by ID (score fixed at 1.0, parity with PgVectorStore)."""
        sql = (
            "SELECT chunk_id, chunk_text, source_path, bucket, person, layer, "
            f"section, metadata FROM {self.table} WHERE chunk_id = %s"
        )
        try:
            with self._get_conn().cursor() as cur:
                cur.execute(sql, (chunk_id,))
                row = cur.fetchone()
        except Exception:
            return None
        if not row:
            return None
        return SearchResult(
            chunk_id=row[0],
            text=row[1],
            metadata={
                "source_path": row[2] or "",
                "bucket": row[3] or "",
                "person": row[4] or "",
                "layer": row[5] or "",
                "section": row[6] or "",
                **(self._coerce_metadata(row[7])),
            },
            score=1.0,
        )

    def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID. Returns True on success (parity with PgVectorStore)."""
        sql = f"DELETE FROM {self.table} WHERE chunk_id = %s"
        try:
            with self._get_conn().cursor() as cur:
                cur.execute(sql, (chunk_id,))
            return True
        except Exception:
            return False

    def count(self) -> int:
        """Count chunks for this bucket (parity with PgVectorStore)."""
        sql = f"SELECT COUNT(*) FROM {self.table} WHERE bucket = %s"
        try:
            with self._get_conn().cursor() as cur:
                cur.execute(sql, (self.bucket,))
                row = cur.fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0

    def clear(self) -> None:
        """Delete all chunks in this bucket (parity with PgVectorStore)."""
        sql = f"DELETE FROM {self.table} WHERE bucket = %s"
        with self._get_conn().cursor() as cur:
            cur.execute(sql, (self.bucket,))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def health_check(self) -> dict:
        """Verify Postgres connectivity and row count (parity with PgVectorStore)."""
        try:
            with self._get_conn().cursor() as cur:
                cur.execute(f"SELECT 1 FROM {self.table} LIMIT 1")
                cur.fetchall()
            total = self.count()
            return {
                "ok": True,
                "bucket": self.bucket,
                "chunk_count": total,
                "table": self.table,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
