"""QueryTrace — Observability for the RAG pipeline.

Captures every query with retrieval metadata and persists to JSONL.
Non-blocking write: trace failure never interrupts the query.

Story: STORY-RAG-6 (S6) — Phase 1 Wave 4
Date: 2026-04-12

Output: .data/query_traces/YYYY-MM-DD.jsonl  (one JSON object per line)
ROUTING key: "query_traces"

Schema is forward-compatible with:
  - S7: threshold_applied, chunks_filtered_count
  - S8: hhem_hallucination_probability, hallucination_warning
  - S9: ragas_context_precision
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# ROUTING (mirrors engine/paths.py — avoids circular import)
# ---------------------------------------------------------------------------
def _traces_dir() -> Path:
    """Resolve .data/query_traces/ relative to project root."""
    root = Path(__file__).resolve().parents[3]  # mega-brain/
    d = root / ".data" / "query_traces"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# QUERYTRACE DATACLASS
# ---------------------------------------------------------------------------
@dataclass
class QueryTrace:
    """Complete trace of a single RAG query execution.

    Required fields are populated by the pipeline.
    Optional fields are filled by downstream stages (S7, S8, S9).
    """

    # Core identity
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str = ""
    bucket: str = "external"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Retrieval metadata
    retrieval_scores: list[dict] = field(default_factory=list)
    # Format: [{"chunk_id": str, "score": float, "source": "dense"|"sparse"|"rrf"}, ...]

    # Pipeline metadata
    pipeline_selected: str = ""  # A/B/C/D/E or "pgvector_rrf"
    chunk_count: int = 0
    latency_ms: float = 0.0

    # Self-RAG faithfulness (set by self_rag.py / verify())
    faithfulness_score: float = -1.0  # -1 = not computed

    # S7: threshold monitoring
    threshold_applied: float = -1.0  # MATCH_THRESHOLD at query time
    chunks_filtered_count: int = 0  # Chunks dropped below threshold

    # S8: HHEM hallucination detection (populated if faithfulness < 0.60)
    hhem_hallucination_probability: float = -1.0  # -1 = not computed
    hallucination_warning: bool = False

    # S9: RAGAS evaluation (populated by nightly batch)
    ragas_context_precision: float = -1.0  # -1 = not computed

    # S10: TF-IDF+SVM query classifier (populated by bucket_query_router)
    classifier_confidence: float = -1.0  # -1 = not run
    classifier_source: str = ""  # "heuristic" | "classifier" | ""
    final_bucket: str = ""  # final bucket routing decision

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# PERSISTENCE (non-blocking)
# ---------------------------------------------------------------------------
def persist_trace(trace: QueryTrace) -> None:
    """Persist trace to daily JSONL file. Non-blocking (background thread).

    File: .data/query_traces/YYYY-MM-DD.jsonl
    Failure is silently logged — never raises.
    """

    def _write() -> None:
        try:
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            path = _traces_dir() / f"{today}.jsonl"
            line = json.dumps(trace.to_dict(), ensure_ascii=False) + "\n"
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass  # Non-blocking: trace failure never interrupts query

    t = threading.Thread(target=_write, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# READ HELPERS (for S9 RAGAS evaluation)
# ---------------------------------------------------------------------------
def load_traces(date: str | None = None) -> list[QueryTrace]:
    """Load traces from JSONL file.

    Args:
        date: "YYYY-MM-DD" string. Defaults to today.

    Returns: List of QueryTrace objects.
    """
    if date is None:
        date = datetime.now(UTC).strftime("%Y-%m-%d")
    path = _traces_dir() / f"{date}.jsonl"
    if not path.exists():
        return []
    traces = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                traces.append(
                    QueryTrace(
                        **{k: v for k, v in data.items() if k in QueryTrace.__dataclass_fields__}
                    )
                )
            except Exception:
                continue
    return traces


def load_traces_range(start: str, end: str) -> list[QueryTrace]:
    """Load traces for a date range (inclusive). Dates as 'YYYY-MM-DD'."""
    from datetime import date as _date
    from datetime import timedelta

    start_d = _date.fromisoformat(start)
    end_d = _date.fromisoformat(end)
    all_traces: list[QueryTrace] = []
    current = start_d
    while current <= end_d:
        all_traces.extend(load_traces(current.isoformat()))
        current += timedelta(days=1)
    return all_traces
