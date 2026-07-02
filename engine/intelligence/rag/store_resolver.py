"""Store Resolver — env-driven selection of the RAG VectorStore backend.

Single point of truth that decides WHICH :class:`VectorStore` implementation to
instantiate based on the environment, so the exact same calling code runs on a
local Postgres, on a hosted Supabase, or on any managed Postgres — with **zero
config** for whoever clones the OSS repo.

Story: STORY-GBA-F1.2 — Fase 1 (Portabilidade OSS)
Date: 2026-06-20
Tipo: CREATE INTERNO — DATABASE_URL é convenção universal de Postgres, não
      código portado do gbrain. Esta camada apenas orquestra os dois backends
      internos (``PostgresStore`` de F1.1 e ``PgVectorStore`` legado).

Resolution rules (precedence is DEFINED and documented):

    1. ``DATABASE_URL`` present  → :class:`PostgresStore`  (psycopg2 / pure SQL)
    2. ``SUPABASE_URL`` present  → :class:`PgVectorStore`  (PostgREST / RPC)
    3. both present             → ``DATABASE_URL`` WINS    (see rationale below)
    4. neither present          → ``StoreResolutionError`` with setup guidance

Why ``DATABASE_URL`` wins when both are set
-------------------------------------------
``DATABASE_URL`` is the more explicit, more portable contract: a direct DSN
that works against ANY Postgres (local container, RDS, Supabase's own direct
connection, etc.) without a hosted REST layer. ``SUPABASE_URL`` implies the
PostgREST/RPC stack, which is a superset of dependencies (service key, network,
function deploy). When an operator has *both* configured, they almost always
want the direct, dependency-light path. Choosing the more explicit transport on
conflict is the least-surprising, most-portable default. An operator who truly
wants the Supabase REST path with ``DATABASE_URL`` also set can force it via
``prefer="supabase"`` (or unset ``DATABASE_URL``).

Constitution Art. VI (no secrets in code): both URLs come from the environment.
Constitution Art. XIII (bucket isolation): ``bucket`` is forwarded unchanged to
the chosen backend, which enforces isolation at query time.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid import cost / circulars at module load
    from .vector_store import VectorStore

# Env var names — kept as module constants so tests and docs stay in sync.
ENV_DATABASE_URL = "DATABASE_URL"
ENV_SUPABASE_URL = "SUPABASE_URL"

# Accepted values for the explicit ``prefer`` override.
_PREFER_DATABASE = "database"
_PREFER_SUPABASE = "supabase"


class StoreResolutionError(RuntimeError):
    """Raised when no vector-store backend can be resolved from the environment.

    Distinct from a generic ``RuntimeError`` so callers (e.g. the hybrid index,
    which wants graceful degradation to ``None``) can catch the *specific*
    "nothing is configured" condition without swallowing real DB errors.
    """


# Human-actionable setup instruction surfaced on the "neither configured" path.
_SETUP_HINT = (
    "No vector-store backend configured. Set ONE of the following in your .env:\n"
    "  • DATABASE_URL=postgresql://user:pass@host:5432/db   "
    "(any Postgres with the pgvector extension — recommended for local/OSS)\n"
    "  • SUPABASE_URL=https://<ref>.supabase.co  +  "
    "SUPABASE_SERVICE_ROLE_KEY=<service-key>   (hosted Supabase)\n"
    "Quick local start: "
    "docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pg pgvector/pgvector:pg16 "
    "then export DATABASE_URL=postgresql://postgres:pg@localhost:5432/postgres"
)


def _env(name: str) -> str:
    """Read an env var, treating whitespace-only as unset (parity with clients)."""
    return (os.environ.get(name) or "").strip()


def resolve_backend(prefer: str | None = None) -> str:
    """Return the backend identifier (``"database"`` | ``"supabase"``) for the env.

    Pure decision function — does not import or construct anything, so it is cheap
    and trivially testable. ``get_vector_store`` builds on top of it.

    Args:
        prefer: Optional explicit override. ``"database"`` forces the
            ``DATABASE_URL`` path; ``"supabase"`` forces the ``SUPABASE_URL``
            path. The forced backend must actually be configured, else
            ``StoreResolutionError`` is raised. ``None`` (default) applies the
            documented precedence (DATABASE_URL wins on conflict).

    Raises:
        StoreResolutionError: when the requested/derived backend is not
            configured in the environment.
    """
    has_db = bool(_env(ENV_DATABASE_URL))
    has_supabase = bool(_env(ENV_SUPABASE_URL))

    if prefer is not None:
        choice = prefer.strip().lower()
        if choice == _PREFER_DATABASE:
            if not has_db:
                raise StoreResolutionError(
                    f"prefer='database' but {ENV_DATABASE_URL} is not set.\n{_SETUP_HINT}"
                )
            return _PREFER_DATABASE
        if choice == _PREFER_SUPABASE:
            if not has_supabase:
                raise StoreResolutionError(
                    f"prefer='supabase' but {ENV_SUPABASE_URL} is not set.\n{_SETUP_HINT}"
                )
            return _PREFER_SUPABASE
        raise StoreResolutionError(
            f"Unknown prefer={prefer!r}; expected 'database' or 'supabase'."
        )

    # Documented precedence: DATABASE_URL is the more explicit/portable contract.
    if has_db:
        return _PREFER_DATABASE
    if has_supabase:
        return _PREFER_SUPABASE

    raise StoreResolutionError(_SETUP_HINT)


def get_vector_store(
    bucket: str = "external",
    match_threshold: float = 0.40,
    prefer: str | None = None,
) -> VectorStore:
    """Resolve and instantiate the correct :class:`VectorStore` for the env.

    This is the function call-sites use instead of constructing a concrete store
    directly. The two backends share the same constructor surface
    (``bucket`` + ``match_threshold``), so the chosen one is built uniformly.

    Args:
        bucket: Knowledge bucket — ``"external"`` | ``"business"`` | ``"personal"``.
            Forwarded unchanged; the backend enforces isolation at query time.
        match_threshold: Minimum cosine similarity to return (default 0.40,
            parity with both backends / ``match_rag_chunks``).
        prefer: Optional explicit backend override (see :func:`resolve_backend`).

    Returns:
        A constructed ``PostgresStore`` or ``PgVectorStore``. Imports are local
        so resolving the Postgres path never imports the Supabase client and
        vice-versa.

    Raises:
        StoreResolutionError: when no backend is configured (or the forced
            ``prefer`` backend is missing).
    """
    backend = resolve_backend(prefer=prefer)

    if backend == _PREFER_DATABASE:
        from .postgres_store import PostgresStore

        return PostgresStore(bucket=bucket, match_threshold=match_threshold)

    # backend == "supabase"
    from .pgvector_store import PgVectorStore

    return PgVectorStore(bucket=bucket, match_threshold=match_threshold)


def is_any_backend_configured() -> bool:
    """True if at least one vector-store backend is configured in the env.

    Convenience for graceful-degradation call-sites (e.g. the hybrid index)
    that want to check availability without catching an exception.
    """
    return bool(_env(ENV_DATABASE_URL)) or bool(_env(ENV_SUPABASE_URL))
