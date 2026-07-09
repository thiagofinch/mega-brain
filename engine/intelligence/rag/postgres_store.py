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
      (``match_rag_chunks``), porém em SQL puro. Não porta código do refbrain.

Schema: rag_chunks table (see scripts/migrate_rag_chunks_pgvector.sql for the
        legacy ``embedding vector(1024)`` column, and
        scripts/migrate_rag_chunks_halfvec_m2.sql for the active
        ``embedding_halfvec halfvec(3072)`` column + HNSW index).

        The active embedding column is parameterised (``embedding_column``,
        default ``embedding_halfvec``) so the same store drives both the legacy
        ``vector`` space and the M2 ``halfvec(3072)`` space without forking the
        class. The similarity query inlines the body of the
        ``match_rag_chunks_halfvec`` SQL function so the backend is
        self-contained (no server-side function required for read paths) while
        remaining bit-for-bit compatible with the Supabase-resident function:

            1 - (embedding_halfvec <=> query) AS similarity
            WHERE bucket = :bucket AND embedding_halfvec IS NOT NULL
                  AND 1 - (embedding_halfvec <=> query) > :threshold
            ORDER BY embedding_halfvec <=> query
            LIMIT :count

STORY-RAG-VM-M2: the active column is ``embedding_halfvec halfvec(3072)`` cast
``::halfvec``, indexed with HNSW (``halfvec_cosine_ops``). ``halfvec`` indexes up
to 4000 dims (``vector`` caps HNSW at 2000), which is why the 3072-dim space is
stored as ``halfvec``. The dimension is NOT hardcoded — it is resolved from
``embedding_config`` so M1 (1536→3072) and the column stay in lock-step.

Constitution Art. XIII: bucket isolation is enforced at query time via the
``bucket`` column filter. Never widen the filter unless you are an explicitly
authorized cross-bucket agent (sua-organizacao-oracle).

Constitution Art. VI (no secrets in code): the DSN comes from ``DATABASE_URL``.
"""

from __future__ import annotations

import json
import os
import warnings
from typing import Any

from .dynamic_security import FILTERABLE_IDENTITY_COLUMNS
from .vector_store import SearchResult, VectorStore

# pgvector dimension of the LEGACY rag_chunks.embedding column (vector(1024)).
# Kept as a module constant so legacy tests and the legacy DDL stay in sync.
# The ACTIVE column dimension (embedding_halfvec) is resolved at runtime from
# embedding_config.get_embedding_dimensions() — never hardcode it (M2 RNF).
EMBEDDING_DIM = 1024

# Active embedding column (STORY-RAG-VM-M2 expand-contract). The legacy
# ``embedding vector(1024)`` column survives until the M3 contract/cutover; new
# reads/writes target ``embedding_halfvec halfvec(3072)``.
ACTIVE_EMBEDDING_COLUMN = "embedding_halfvec"

# pgvector cast for the active column. halfvec stores float16 components and is
# the only type whose HNSW index supports > 2000 dims (up to 4000).
ACTIVE_VECTOR_CAST = "halfvec"

# Columns the store is allowed to read/write as embeddings. Whitelisted to keep
# the dynamically-interpolated column name injection-safe. ``embedding`` (legacy
# vector) stays here so M3 hydration/parity can still read the old space.
_ALLOWED_EMBEDDING_COLUMNS = {"embedding_halfvec", "embedding"}

# Columns ``search(filters=...)`` is allowed to build a WHERE predicate on
# (STORY-F1-15 / 12b). This is a CLOSED whitelist: only these fixed, real
# ``rag_chunks`` columns can be interpolated into the ``AND c.{col} = %s`` clause,
# so a hostile filter KEY can never inject SQL (values are always parameterised).
# ``bucket`` is deliberately EXCLUDED — bucket isolation (Art. XIII) is owned by
# the dedicated ``bucket_filter`` arg and must never be widened via ``filters``.
# ``bu`` (STORY-213.W3.1 / E1) IS filterable: it is the ORTHOGONAL business-unit
# axis (sua-organizacao vs empresa-b), NOT the knowledge-TYPE axis ``bucket``. A ``bu`` filter
# narrows by business; it never widens bucket isolation. An unknown filter KEY
# (e.g. a ``bu`` typo) is silently ignored — it is not in this closed set, so it
# never restricts and never reaches SQL (the AC2 negative proof).
# ``visibility`` + ``client_id`` (STORY-213.W3.2 / E2+E3) join the whitelist as the
# app-layer DEFENSE-IN-DEPTH twin of the DB RLS predicate (AC5): the store CAN
# pre-filter on the same real row-security columns the RLS policy enforces, so a
# chunk the RLS would block is never returned by the app path either. They come from
# the single DECLARED SOT ``dynamic_security.FILTERABLE_IDENTITY_COLUMNS`` so the enum
# lives in ONE place (AC7). NOTE the row-security axis is ``visibility``, NOT
# ``persona``: ``persona`` (internal|external) is the JWT-claim of the REQUESTER and
# has NO ``rag_chunks`` column — interpolating a phantom ``persona`` column would break
# every query, so it is deliberately absent from this closed set (No Invention).
_FILTERABLE_COLUMNS = frozenset(
    {
        "person",
        "domain",
        "layer",
        "section",
        "source_type",
        "quality_tier",
        "entity_type",
        "graph_id",
        "community_id",
        "bu",  # STORY-213.W3.1 — orthogonal business-unit axis
    }
    | FILTERABLE_IDENTITY_COLUMNS  # STORY-213.W3.2 — visibility + client_id (E2+E3)
)


def apply_metadata_filters(
    results: list[SearchResult], filters: dict | None
) -> list[SearchResult]:
    """In-memory post-filter over ``SearchResult.metadata`` (the non-SQL path).

    The canonical filter is the composite WHERE pushed down inside
    ``PostgresStore.search`` (SQL). This helper is the equivalent for callers that
    cannot push the predicate into SQL — e.g. the ``PgVectorStore`` PostgREST /
    RPC fallback whose server-side ``match_rag_chunks`` returns a fixed column set
    (STORY-F1-15 / 12b). Semantics mirror the SQL path AND the query-layer
    ``hybrid_query._matches_filters`` so the ONE filter behaves identically across
    every backend:

      * no filter (``None`` / empty)           → identity (backward-compat);
      * a falsy wanted value                    → inert key (never restricts);
      * an active key whose value is ``None``   → row EXCLUDED (an extraction_gap
        row cannot prove the requested tag — honest, "etiquetar + filtrar");
      * comparison is case-insensitive on strings.

    Only whitelisted keys (``_FILTERABLE_COLUMNS``) restrict; an unknown key is
    ignored (never a crash, never a raw interpolation).
    """
    if not filters:
        return results
    active = {
        k: v for k, v in filters.items() if v and k in _FILTERABLE_COLUMNS
    }
    if not active:
        return results
    kept: list[SearchResult] = []
    for sr in results:
        meta = sr.metadata or {}
        ok = True
        for key, wanted in active.items():
            actual = meta.get(key)
            if actual is None or str(actual).lower() != str(wanted).lower():
                ok = False
                break
        if ok:
            kept.append(sr)
    return kept

# Default similarity floor — mirrors match_rag_chunks DEFAULT and PgVectorStore.
DEFAULT_MATCH_THRESHOLD = 0.40

# HNSW query-time recall tuning (applied per connection — see migration §4).
#   ef_search: candidate list size at query time (40-200; higher = better recall)
#   iterative_scan: 'relaxed_order' keeps pulling candidates when the bucket
#     post-filter drops rows, preventing recall holes under Art. XIII isolation.
DEFAULT_HNSW_EF_SEARCH = 100
DEFAULT_HNSW_ITERATIVE_SCAN = "relaxed_order"


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
        embedding_column: str = ACTIVE_EMBEDDING_COLUMN,
        ef_search: int = DEFAULT_HNSW_EF_SEARCH,
        iterative_scan: str = DEFAULT_HNSW_ITERATIVE_SCAN,
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
            embedding_column: Active embedding column. Default
                ``"embedding_halfvec"`` (M2 halfvec(3072) space). Must be in the
                ``_ALLOWED_EMBEDDING_COLUMNS`` whitelist — the value is
                interpolated into SQL, so an unknown name raises immediately
                (injection guard). Pass ``"embedding"`` to drive the legacy
                ``vector`` space (M3 parity/hydration).
            ef_search: HNSW ``hnsw.ef_search`` GUC applied per connection
                (40-200; higher = better recall, slower).
            iterative_scan: HNSW ``hnsw.iterative_scan`` mode applied per
                connection (``"relaxed_order"`` preserves recall under the
                bucket post-filter — Art. XIII).
        """
        if embedding_column not in _ALLOWED_EMBEDDING_COLUMNS:
            raise ValueError(
                f"embedding_column={embedding_column!r} not allowed; "
                f"expected one of {sorted(_ALLOWED_EMBEDDING_COLUMNS)}"
            )
        self.bucket = bucket
        self.match_threshold = match_threshold
        self._dsn = dsn
        self.table = table
        self.embedding_column = embedding_column
        # halfvec for the active M2 column; vector for the legacy column.
        self.vector_cast = (
            ACTIVE_VECTOR_CAST if embedding_column == ACTIVE_EMBEDDING_COLUMN else "vector"
        )
        self.ef_search = ef_search
        self.iterative_scan = iterative_scan
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
        """Lazy-open a psycopg2 connection (autocommit), tune it, and reuse it."""
        if self._conn is None or getattr(self._conn, "closed", 1):
            import psycopg2

            self._conn = psycopg2.connect(self._resolve_dsn())
            self._conn.autocommit = True
            self._apply_session_tuning(self._conn)
        return self._conn

    def _apply_session_tuning(self, conn) -> None:
        """Apply HNSW recall GUCs to the session (best-effort, never fatal).

        ``hnsw.ef_search`` and ``hnsw.iterative_scan`` only exist on a pgvector
        build new enough (iterative_scan requires >= 0.8.0). If the server is
        older, the SET fails — we swallow it (warn) so the store still works
        with default recall rather than refusing to connect. Only the halfvec
        (HNSW) column path tunes; the legacy ``vector`` column has no HNSW index.
        """
        if self.embedding_column != ACTIVE_EMBEDDING_COLUMN:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("SET hnsw.ef_search = %s", (int(self.ef_search),))
        except Exception as e:  # pragma: no cover - server-version dependent
            warnings.warn(
                f"[PostgresStore] could not set hnsw.ef_search: {e}", stacklevel=2
            )
        try:
            with conn.cursor() as cur:
                # iterative_scan is an enum GUC; value is from a fixed internal
                # constant (not user input), so string-formatting is safe here.
                cur.execute(f"SET hnsw.iterative_scan = '{self.iterative_scan}'")
        except Exception as e:  # pragma: no cover - requires pgvector >= 0.8.0
            warnings.warn(
                f"[PostgresStore] could not set hnsw.iterative_scan "
                f"(requires pgvector >= 0.8.0): {e}",
                stacklevel=2,
            )

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

        Etiquetagem (completude-total.S1): ``source_type`` and ``quality_tier``
        come from the SAME metadata dict the caller already populates. The
        derivation lives in ``engine/intelligence/rag/tagging.py`` and is invoked
        by the CALLER (e.g. rebuild.py) — persistence stays dumb. When the caller
        supplied no tag (legacy caller, or an honest ``extraction_gap``) the value
        is ``None`` → the column is written NULL, never a fabricated default
        (No Invention — ``.claude/rules/extraction-no-fallbacks.md``).

        Ontology payload (STORY-F1-15 / 12a): the three trailing slots
        ``entity_type`` (the chunk's Object Type — F1-1), ``graph_id`` (its
        knowledge-graph node id) and ``community_id`` (its persisted community —
        F1-7A) are PROMOTED here from the JSONB ``metadata`` blob to dedicated
        columns so the query layer (12b) can pre-filter on them with a btree/GIN
        index instead of a JSONB scan. They come from the SAME ``metadata`` dict
        the caller already populates; ``None`` when the signal has not arrived yet
        (community_id/graph_id are honest-empty today — issue #141 — the FILTER
        exists and works; the DATA lands with the graph→chunk wiring later) →
        written NULL, never fabricated. These three MUST stay positionally in
        lock-step with ``_UPSERT_SQL_TMPL`` and ``add_batch`` (the two SQL sites).

        BU axis (STORY-213.W3.1 / E1): the trailing slot ``bu`` is the ORTHOGONAL
        business-unit tag (sua-organizacao vs empresa-b) — distinct from ``bucket`` (the
        knowledge-TYPE axis, Art. XIII). It is promoted from ``metadata.bu`` to a
        dedicated, indexed column so the query layer can pre-filter ``WHERE bu``.
        ``None`` when the caller supplied no BU (legacy caller, or a chunk whose
        BU has not been derived yet) → written NULL, never a fabricated default
        (No Invention — the path backfill fills it later). This slot MUST stay
        positionally in lock-step with ``_UPSERT_SQL_TMPL`` and ``add_batch``.
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
            meta.get("source_type"),  # NULL when absent (extraction_gap)
            meta.get("quality_tier"),  # NULL when absent (extraction_gap)
            meta.get("entity_type"),  # F1-15/F1-1 — NULL when untyped (honest)
            meta.get("graph_id"),  # F1-15 — NULL until graph wiring (honest, #141)
            meta.get("community_id"),  # F1-15/F1-7A — NULL when no community (honest)
            meta.get("bu"),  # 213.W3.1/E1 — NULL until path backfill (honest)
        )

    _UPSERT_SQL_TMPL = (
        "INSERT INTO {table} "
        "(chunk_id, bucket, source_path, chunk_text, {emb_col}, "
        " person, domain, layer, section, metadata, source_type, quality_tier, "
        " entity_type, graph_id, community_id, bu) "
        "VALUES (%s, %s, %s, %s, %s::{cast}, %s, %s, %s, %s, %s::jsonb, %s, %s, "
        "        %s, %s, %s, %s) "
        "ON CONFLICT (chunk_id) DO UPDATE SET "
        "  bucket = EXCLUDED.bucket, "
        "  source_path = EXCLUDED.source_path, "
        "  chunk_text = EXCLUDED.chunk_text, "
        "  {emb_col} = EXCLUDED.{emb_col}, "
        "  person = EXCLUDED.person, "
        "  domain = EXCLUDED.domain, "
        "  layer = EXCLUDED.layer, "
        "  section = EXCLUDED.section, "
        "  metadata = EXCLUDED.metadata, "
        "  source_type = EXCLUDED.source_type, "
        "  quality_tier = EXCLUDED.quality_tier, "
        "  entity_type = EXCLUDED.entity_type, "
        "  graph_id = EXCLUDED.graph_id, "
        "  community_id = EXCLUDED.community_id, "
        "  bu = EXCLUDED.bu"
    )

    def add(
        self,
        chunk_id: str,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Insert or update a single chunk with its embedding (UPSERT)."""
        sql = self._UPSERT_SQL_TMPL.format(
            table=self.table, emb_col=self.embedding_column, cast=self.vector_cast
        )
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
        # ON CONFLICT (chunk_id) cannot touch the same target row twice in one
        # statement (psycopg2.errors.CardinalityViolation). chunk_id is
        # content-stable, so duplicate corpus text yields duplicate chunk_ids
        # legitimately — a full-bucket add_batch can carry 2+ rows with the SAME
        # chunk_id. Collapse to the LAST occurrence (row[0] is chunk_id, see
        # _record_tuple): deterministic, and identical to what the UPSERT would
        # converge to if the dups were sent in separate statements (later write
        # wins). Without this, execute_values below aborts the whole batch and
        # kills the rebuild (rc=1) on the first bucket with a repeat.
        deduped: dict[str, tuple] = {}
        for row in rows:
            deduped[row[0]] = row
        rows = list(deduped.values())
        # The embedding (index 4) and metadata (index 9) need explicit casts;
        # execute_values applies the template per row. emb_col/cast track the
        # active column (halfvec(3072) by default — M2 expand-contract). The two
        # slots at index 10/11 are source_type/quality_tier (completude-total.S1);
        # the three slots at index 12/13/14 are the ontology payload
        # entity_type/graph_id/community_id (STORY-F1-15 / 12a); the trailing slot
        # at index 15 is ``bu`` (STORY-213.W3.1 / E1 — orthogonal business-unit
        # axis) — all plain TEXT, no cast. They MUST stay positionally in lock-step
        # with _record_tuple and _UPSERT_SQL_TMPL (this is the second — duplicated —
        # SQL write site).
        emb_col = self.embedding_column
        template = (
            f"(%s, %s, %s, %s, %s::{self.vector_cast}, %s, %s, %s, %s, %s::jsonb, "
            "%s, %s, %s, %s, %s, %s)"
        )
        insert_sql = (
            f"INSERT INTO {self.table} "
            f"(chunk_id, bucket, source_path, chunk_text, {emb_col}, "
            " person, domain, layer, section, metadata, source_type, quality_tier, "
            " entity_type, graph_id, community_id, bu) "
            "VALUES %s "
            "ON CONFLICT (chunk_id) DO UPDATE SET "
            "  bucket = EXCLUDED.bucket, "
            "  source_path = EXCLUDED.source_path, "
            "  chunk_text = EXCLUDED.chunk_text, "
            f"  {emb_col} = EXCLUDED.{emb_col}, "
            "  person = EXCLUDED.person, "
            "  domain = EXCLUDED.domain, "
            "  layer = EXCLUDED.layer, "
            "  section = EXCLUDED.section, "
            "  metadata = EXCLUDED.metadata, "
            "  source_type = EXCLUDED.source_type, "
            "  quality_tier = EXCLUDED.quality_tier, "
            "  entity_type = EXCLUDED.entity_type, "
            "  graph_id = EXCLUDED.graph_id, "
            "  community_id = EXCLUDED.community_id, "
            "  bu = EXCLUDED.bu"
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
        filters: dict | None = None,
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
            filters: Optional ontology / metadata pre-filter (STORY-F1-15 / 12b).
                A dict of ``{column: wanted_value}`` restricted to
                :data:`_FILTERABLE_COLUMNS` (``person``, ``domain``, ``layer``,
                ``section``, ``source_type``, ``quality_tier``, ``entity_type``,
                ``community_id``, ``graph_id``, ``bu``, ``visibility``,
                ``client_id``). ``bu`` (STORY-213.W3.1) is the orthogonal
                business-unit axis (sua-organizacao vs empresa-b) — a ``{"bu": "sua-organizacao"}``
                filter narrows by business without touching bucket isolation.
                ``visibility``/``client_id`` (STORY-213.W3.2) are the app-layer
                defense-in-depth twin of the DB RLS predicate (E3). Each active
                (truthy) key adds an
                ``AND c.{col} = %s`` predicate to the WHERE — a SQL PUSHDOWN
                (btree/GIN-indexed, 12a) that cuts the top-k candidate set BEFORE
                the distance sort, not a post-hoc python filter. The key is only
                ever a whitelisted column name (never interpolated raw); values are
                parameterised. Default (``None``/empty) is byte-identical to the
                pre-12b query. A row whose column is NULL (extraction_gap) never
                matches an active filter (SQL ``NULL = value`` is UNKNOWN) — honest
                "etiquetar + filtrar, NÃO excluir": the row stays in the brain, it
                is only invisible to a restrictive query. ``bucket`` is NOT
                filterable here (Art. XIII isolation is owned by ``bucket_filter``).
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
        # 12b composite filter pushdown: one AND per active, whitelisted key.
        filter_clause = ""
        if filters:
            for key, wanted in filters.items():
                if not wanted:
                    continue  # inert key — never restricts (default-includes-all)
                if key not in _FILTERABLE_COLUMNS:
                    continue  # unknown key ignored — never a raw interpolation
                filter_clause += f"AND c.{key} = %s "  # key ∈ closed whitelist
                params.append(wanted)
        params.extend([vec, self.match_threshold, vec, top_k])

        emb = self.embedding_column  # whitelisted in __init__ (injection-safe)
        cast = self.vector_cast
        sql = (
            "SELECT c.chunk_id, c.chunk_text, c.source_path, c.bucket, "
            "       c.person, c.layer, c.section, "
            "       c.entity_type, c.graph_id, c.community_id, c.metadata, "
            f"       1 - (c.{emb} <=> %s::{cast}) AS similarity "
            f"FROM {self.table} c "
            f"WHERE c.{emb} IS NOT NULL "
            f"{bucket_clause}"
            f"{filter_clause}"
            f"AND 1 - (c.{emb} <=> %s::{cast}) > %s "
            f"ORDER BY c.{emb} <=> %s::{cast} "
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
                    # Ontology payload columns (12a) — surfaced so downstream can
                    # read them; None stays None (honest, never a fabricated tag).
                    "entity_type": row[7],
                    "graph_id": row[8],
                    "community_id": row[9],
                    # JSONB spread LAST so a legacy row (column still NULL, tag only
                    # in the blob) still surfaces its entity_type from metadata.
                    **(self._coerce_metadata(row[10])),
                },
                score=float(row[11]),
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
        column: str | None = None,
    ) -> dict[str, list[float]]:
        """Hydrate stored embeddings for the given chunk_ids from the active column.

        Parity with ``PgVectorStore.get_embeddings_by_chunk_ids``: bucket-scoped,
        column-scoped, fail-open (returns ``{}`` on any DB error). Used by the
        F2.3 cosine re-score so the compare happens in the SAME persisted space.

        Args:
            chunk_ids: Chunk identifiers to hydrate.
            column: Embedding column to read. Defaults to ``self.embedding_column``
                (``embedding_halfvec`` — the M2 active space). The legacy
                ``embedding`` column is still readable for M3 parity/migration.

        Note: ``column`` is whitelisted (only known embedding columns) to keep it
        safe from SQL injection while still allowing the active-column override.
        """
        if not chunk_ids:
            return {}
        if column is None:
            column = self.embedding_column
        if column not in _ALLOWED_EMBEDDING_COLUMNS:
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
            "section, entity_type, graph_id, community_id, metadata "
            f"FROM {self.table} WHERE chunk_id = %s"
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
                # Ontology payload columns (STORY-F1-15 / 12a) — None stays None.
                "entity_type": row[7],
                "graph_id": row[8],
                "community_id": row[9],
                **(self._coerce_metadata(row[10])),
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
                "embedding_column": self.embedding_column,
                "vector_cast": self.vector_cast,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
