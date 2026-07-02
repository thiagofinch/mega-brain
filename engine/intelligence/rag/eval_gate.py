"""Eval gate — fail CI on retrieval correctness drops (recall@K).

PORTED from gbrain `src/commands/eval-gate.ts` + `src/core/bench/{correctness-gate,qrels-file}.ts`
(SHA congelado 4ee530f, v0.42.42.0). Story: STORY-GBA-F0.1 (EPIC-GBRAIN-ABSORPTION).

This is the ARMOR layer of the absorption: a CI-blocking correctness gate that
replays a frozen qrels gabarito against the CURRENT retrieval and FAILS (exit
non-zero) if recall@K / first_relevant_hit_rate fall below a floor. It must
exist BEFORE any retrieval change (reranker, cosine, query expansion — Fases 2-3)
so no change can silently regress recall.

Adaptation to mega-brain (vs gbrain):
  - gbrain compare key `${source_id}::${slug}` → mega-brain `${bucket}::${chunk_id}`.
    The retrieval unit here is the chunk_id (matching `ragas_evaluator.py`'s
    IDBasedContextPrecision, which compares chunk_id sets). `bucket` is the
    isolation axis (Art. XIII), analogous to gbrain's `source_id`.
  - Retrieval is REUSED from `ragas_evaluator.retrieve_chunk_ids` (rrf_retrieve
    with BM25 fallback) — NOT duplicated. The default search fn wraps it; tests
    inject a stub for deterministic, index-free runs (gbrain `searchFn` pattern).

Scope: F0.1 ports the CORRECTNESS gate only (recall@K vs qrels). The regression
gate (jaccard/top-1/latency replay) from gbrain is out of scope for this story.

Fail-closed posture (gbrain D3): any per-query exception (timeout, retrieval
error) is recorded as `errored` and flips the verdict to `fail` via a
`queries_errored > 0` breach — the lenient alternative (drop the failing query)
would silently inflate scores by hiding hard queries.

Exit codes: 0 PASS, 1 FAIL (breach or in-process throw), 2 USAGE.

Usage:
    python3 -m engine.intelligence.rag.eval_gate --qrels engine/intelligence/rag/qrels-baseline.json
    python3 -m engine.intelligence.rag.eval_gate --qrels FILE -k 10 --threshold-recall-at-k 0.70 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# CONSTANTS (ported from gbrain qrels-file.ts DEFAULT_QRELS_THRESHOLDS)
# ---------------------------------------------------------------------------
QRELS_FILE_SCHEMA_VERSION = 1

DEFAULT_RECALL_AT_K = 0.70
DEFAULT_FIRST_RELEVANT_HIT = 0.60
# Lower default because exact top-1 is harder than any-relevant top-1.
DEFAULT_EXPECTED_TOP1 = 0.50
DEFAULT_K = 10
DEFAULT_BUCKET = "external"


# ---------------------------------------------------------------------------
# DATA TYPES
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SourceRef:
    """A `${bucket}::${chunk_id}` reference (mega-brain analog of gbrain's
    `{source_id, slug}`)."""

    bucket: str
    chunk_id: str


@dataclass
class QrelsEntry:
    query_id: str
    query: str
    # Normalized {bucket, chunk_id} refs. Plain chunk_id strings auto-promote
    # to bucket='external' (legacy slug-only shape).
    relevant: list[SourceRef]
    # If set, retrieved[0] MUST equal this exact ref (strict top-1 metric).
    expected_top1: SourceRef | None = None
    # Bucket to run the query against (default external — matches ragas).
    bucket: str = DEFAULT_BUCKET
    label: str | None = None


@dataclass
class QrelsFile:
    schema_version: int
    queries: list[QrelsEntry]
    description: str | None = None


@dataclass
class PerQueryResult:
    query_id: str
    query: str
    recall_at_k: float
    first_relevant_hit: int  # 0 | 1
    retrieved_count: int
    expected_top1_hit: int | None = None  # 0 | 1
    errored: bool = False
    error_message: str | None = None


@dataclass
class CorrectnessSummary:
    k: int
    queries_total: int
    queries_run: int  # total - errored
    queries_errored: int
    mean_recall_at_k: float
    first_relevant_hit_rate: float
    expected_top1_hit_rate: float
    # Denominator = queries with expected_top1 SET (not total queries).
    expected_top1_denominator: int


@dataclass
class Breach:
    metric: str
    observed: float | None = None
    threshold: float | None = None
    reason: str | None = None
    error_tail: str | None = None


@dataclass
class CorrectnessGateResult:
    ran: bool
    qrels_path: str | None = None
    summary: CorrectnessSummary | None = None
    thresholds: dict | None = None
    breaches: list[Breach] = field(default_factory=list)


# search_fn(query, bucket, k) -> ordered list of (bucket, chunk_id) tuples, best first.
SearchFn = Callable[[str, str, int], list[tuple[str, str]]]


class QrelsParseError(Exception):
    """Raised when a qrels file is malformed (usage error → exit 2)."""

    def __init__(self, message: str, entry_index: int | None = None) -> None:
        super().__init__(message)
        self.entry_index = entry_index


# ---------------------------------------------------------------------------
# COMPARE KEYS (ported from gbrain makeRef / refKey)
# ---------------------------------------------------------------------------
def make_ref(bucket: str, chunk_id: str) -> str:
    """Build the canonical `${bucket}::${chunk_id}` compare key."""
    return f"{bucket}::{chunk_id}"


def ref_key(ref: SourceRef) -> str:
    return make_ref(ref.bucket, ref.chunk_id)


# ---------------------------------------------------------------------------
# CORE METRICS (ported VERBATIM from gbrain qrels-file.ts)
# ---------------------------------------------------------------------------
def compute_recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """recall@k = |intersect(retrieved[:k], relevant)| / |relevant|.

    Both `retrieved` and `relevant` are arrays of `${bucket}::${chunk_id}` keys.
    Returns a number in [0, 1].
    """
    if not relevant:
        return 0.0
    relevant_set = set(relevant)
    top_k = retrieved[:k]
    hits = sum(1 for r in top_k if r in relevant_set)
    return hits / len(relevant)


def compute_first_relevant_hit(retrieved: list[str], relevant: list[str]) -> int:
    """1 if retrieved[0] in relevant else 0. Empty retrieved → 0."""
    if not retrieved:
        return 0
    return 1 if retrieved[0] in set(relevant) else 0


def compute_ndcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """nDCG@k over BINARY relevance (gain 1 if the ranked id is in `relevant`).

    Added for STORY-RBM-1 (multi-arm benchmark): nDCG is the primary metric the
    retrieval-stack research (`03-recommendations.md:25-27`) asks for to compare
    arms, because — unlike recall@K (a set count, position-blind) — nDCG REWARDS
    putting relevant chunks HIGHER. Two arms can have identical recall@10 yet
    different nDCG@10 if one ranks the relevant chunk at position 1 and the other
    at position 9; that ranking quality is exactly the reranker/dims dial RBM-2/3
    will move.

    Both `retrieved` and `relevant` are arrays of `${bucket}::${chunk_id}` keys
    (same compare-key contract as `compute_recall_at_k`).

    DCG  = Σ_{i=1..k} rel_i / log2(i + 1)      (rel_i ∈ {0, 1})
    IDCG = DCG of the ideal ranking (all relevant first), capped at k.
    nDCG = DCG / IDCG, in [0, 1].

    Edge cases (all unit-tested):
      * relevance at the TOP of the ranking  → nDCG == 1.0
      * relevance present but INVERTED/lower  → 0.0 < nDCG < 1.0
      * ZERO relevant ids recovered in top-k  → nDCG == 0.0
      * empty `relevant` set (IDCG would be 0) → 0.0 (mirrors recall convention,
        no division by zero).
    """
    import math

    if not relevant:
        return 0.0
    relevant_set = set(relevant)
    top_k = retrieved[:k]

    # DCG of the actual ranking (position i is 1-based → log2(i + 1)).
    dcg = sum(
        1.0 / math.log2(rank + 2)  # rank is 0-based ⇒ +2 gives log2(position+1)
        for rank, rid in enumerate(top_k)
        if rid in relevant_set
    )

    # IDCG: ideal ranking puts as many relevant ids as fit (min(|relevant|, k))
    # at the top, each contributing the maximal positional discount.
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def compute_expected_top1_hit(retrieved: list[str], expected_top1: str) -> int:
    """1 if retrieved[0] == expected_top1 else 0. Empty retrieved → 0."""
    if not retrieved:
        return 0
    return 1 if retrieved[0] == expected_top1 else 0


# ---------------------------------------------------------------------------
# QRELS PARSING (ported from gbrain parseQrelsFile)
# ---------------------------------------------------------------------------
def _parse_ref(raw: dict, ctx: str, idx: int) -> SourceRef:
    bucket = raw.get("bucket")
    chunk_id = raw.get("chunk_id")
    if not isinstance(bucket, str) or not isinstance(chunk_id, str):
        raise QrelsParseError(f"{ctx} missing bucket or chunk_id", idx)
    return SourceRef(bucket=bucket, chunk_id=chunk_id)


def parse_qrels_file(content: str) -> QrelsFile:
    """Parse a qrels JSON file.

    Accepts both the legacy chunk_id-only shape (`relevant_chunk_ids` +
    `first_relevant_chunk_id`, bucket auto-defaults to 'external') and the
    federated shape (`relevant` + `expected_top1` with explicit bucket).
    """
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as err:
        raise QrelsParseError(f"Malformed JSON: {err}") from err

    if not isinstance(parsed, dict):
        raise QrelsParseError(
            'Qrels file must be a JSON object. Expected: {"schema_version":1,"queries":[...]}'
        )

    if parsed.get("schema_version") != QRELS_FILE_SCHEMA_VERSION:
        raise QrelsParseError(
            f"Unsupported schema_version {parsed.get('schema_version')} "
            f"(this build expects {QRELS_FILE_SCHEMA_VERSION})"
        )

    raw_queries = parsed.get("queries")
    if not isinstance(raw_queries, list):
        raise QrelsParseError('Qrels file missing "queries" array')
    if len(raw_queries) == 0:
        raise QrelsParseError('Qrels file has empty "queries" array — at least one entry required')

    queries: list[QrelsEntry] = []
    for i, raw in enumerate(raw_queries):
        if not isinstance(raw, dict):
            raise QrelsParseError(f"Entry {i} is not a JSON object", i)

        query_id = raw["query_id"] if isinstance(raw.get("query_id"), str) else f"entry-{i}"
        query = raw.get("query")
        if not isinstance(query, str) or query.strip() == "":
            raise QrelsParseError(f"Entry {i} ({query_id}) missing or empty 'query'", i)

        entry_bucket = raw["bucket"] if isinstance(raw.get("bucket"), str) else DEFAULT_BUCKET

        # Normalize relevant: prefer federated `relevant`, fall back to legacy.
        relevant: list[SourceRef] = []
        if isinstance(raw.get("relevant"), list):
            for j, r in enumerate(raw["relevant"]):
                if not isinstance(r, dict):
                    raise QrelsParseError(
                        f"Entry {i} ({query_id}) relevant[{j}] is not an object", i
                    )
                relevant.append(_parse_ref(r, f"Entry {i} ({query_id}) relevant[{j}]", i))
        elif isinstance(raw.get("relevant_chunk_ids"), list):
            for j, cid in enumerate(raw["relevant_chunk_ids"]):
                if not isinstance(cid, str):
                    raise QrelsParseError(
                        f"Entry {i} ({query_id}) relevant_chunk_ids[{j}] is not a string", i
                    )
                relevant.append(SourceRef(bucket=DEFAULT_BUCKET, chunk_id=cid))
        else:
            raise QrelsParseError(
                f"Entry {i} ({query_id}) missing 'relevant' or 'relevant_chunk_ids'", i
            )
        if not relevant:
            raise QrelsParseError(f"Entry {i} ({query_id}) has empty relevant set", i)

        # Normalize expected_top1: prefer federated, fall back to legacy.
        expected_top1: SourceRef | None = None
        if raw.get("expected_top1") is not None:
            e = raw["expected_top1"]
            if not isinstance(e, dict):
                raise QrelsParseError(f"Entry {i} ({query_id}) expected_top1 is not an object", i)
            expected_top1 = _parse_ref(e, f"Entry {i} ({query_id}) expected_top1", i)
        elif isinstance(raw.get("first_relevant_chunk_id"), str):
            expected_top1 = SourceRef(bucket=DEFAULT_BUCKET, chunk_id=raw["first_relevant_chunk_id"])

        queries.append(
            QrelsEntry(
                query_id=query_id,
                query=query,
                relevant=relevant,
                expected_top1=expected_top1,
                bucket=entry_bucket,
                label=raw["label"] if isinstance(raw.get("label"), str) else None,
            )
        )

    return QrelsFile(
        schema_version=QRELS_FILE_SCHEMA_VERSION,
        queries=queries,
        description=parsed.get("_description") if isinstance(parsed.get("_description"), str) else None,
    )


# ---------------------------------------------------------------------------
# DEFAULT SEARCH FN (reuses ragas_evaluator retrieval — NOT duplicated)
# ---------------------------------------------------------------------------
def _default_search_fn(query: str, bucket: str, k: int) -> list[tuple[str, str]]:
    """Default retrieval: delegates to `ragas_evaluator.retrieve_chunk_ids`
    (rrf_retrieve + BM25 fallback). Returns ordered (bucket, chunk_id) tuples."""
    from .ragas_evaluator import retrieve_chunk_ids

    chunk_ids = retrieve_chunk_ids(query, bucket=bucket, top_k=k)
    return [(bucket, cid) for cid in chunk_ids]


# ---------------------------------------------------------------------------
# CORRECTNESS GATE ORCHESTRATOR (ported from gbrain correctness-gate.ts)
# ---------------------------------------------------------------------------
def _run_one_query(
    entry: QrelsEntry, k: int, search_fn: SearchFn
) -> PerQueryResult:
    try:
        raw = search_fn(entry.query, entry.bucket, k)
        retrieved = [make_ref(b, c) for (b, c) in raw]
    except Exception as err:
        return PerQueryResult(
            query_id=entry.query_id,
            query=entry.query,
            recall_at_k=0.0,
            first_relevant_hit=0,
            retrieved_count=0,
            errored=True,
            error_message=str(err),
        )

    relevant = [ref_key(r) for r in entry.relevant]
    out = PerQueryResult(
        query_id=entry.query_id,
        query=entry.query,
        recall_at_k=compute_recall_at_k(retrieved, relevant, k),
        first_relevant_hit=compute_first_relevant_hit(retrieved, relevant),
        retrieved_count=len(retrieved),
    )
    if entry.expected_top1 is not None:
        out.expected_top1_hit = compute_expected_top1_hit(retrieved, ref_key(entry.expected_top1))
    return out


def run_correctness_gate(
    qrels: QrelsFile,
    k: int = DEFAULT_K,
    search_fn: SearchFn | None = None,
) -> tuple[CorrectnessSummary, list[PerQueryResult]]:
    """Run every qrels query against retrieval; compute recall@K aggregates.

    Does NOT raise on per-query failures (recorded as errored). Raises if the
    qrels file is empty (caller bug; parse_qrels_file already rejects this).
    """
    if not qrels.queries:
        raise ValueError("run_correctness_gate: qrels file has no queries")

    fn = search_fn if search_fn is not None else _default_search_fn

    per_query = [_run_one_query(entry, k, fn) for entry in qrels.queries]

    errored = sum(1 for p in per_query if p.errored)
    non_errored = [p for p in per_query if not p.errored]

    mean_recall = (
        sum(p.recall_at_k for p in non_errored) / len(non_errored) if non_errored else 0.0
    )
    first_relevant_rate = (
        sum(p.first_relevant_hit for p in non_errored) / len(non_errored) if non_errored else 0.0
    )
    with_expected = [p for p in non_errored if p.expected_top1_hit is not None]
    expected_top1_rate = (
        sum(p.expected_top1_hit or 0 for p in with_expected) / len(with_expected)
        if with_expected
        else 0.0
    )

    summary = CorrectnessSummary(
        k=k,
        queries_total=len(per_query),
        queries_run=len(per_query) - errored,
        queries_errored=errored,
        mean_recall_at_k=mean_recall,
        first_relevant_hit_rate=first_relevant_rate,
        expected_top1_hit_rate=expected_top1_rate,
        expected_top1_denominator=len(with_expected),
    )
    return summary, per_query


def _correctness_breaches(
    summary: CorrectnessSummary,
    per_query: list[PerQueryResult],
    thresholds: dict,
) -> list[Breach]:
    breaches: list[Breach] = []

    # Per-query throws are gate failures (gbrain Finding 2D).
    if summary.queries_errored > 0:
        errored_q = [p for p in per_query if p.errored][:5]
        breaches.append(
            Breach(
                metric="queries_errored",
                observed=summary.queries_errored,
                threshold=0,
                reason="one_or_more_qrels_queries_threw",
                error_tail=" | ".join(f"{p.query_id}: {p.error_message}" for p in errored_q),
            )
        )
    if summary.mean_recall_at_k < thresholds["recall_at_k"]:
        breaches.append(
            Breach(
                metric="mean_recall_at_k",
                observed=summary.mean_recall_at_k,
                threshold=thresholds["recall_at_k"],
            )
        )
    if summary.first_relevant_hit_rate < thresholds["first_relevant_hit"]:
        breaches.append(
            Breach(
                metric="first_relevant_hit_rate",
                observed=summary.first_relevant_hit_rate,
                threshold=thresholds["first_relevant_hit"],
            )
        )
    # Only enforce expected_top1 floor when at least one query had it set.
    if (
        summary.expected_top1_denominator > 0
        and summary.expected_top1_hit_rate < thresholds["expected_top1"]
    ):
        breaches.append(
            Breach(
                metric="expected_top1_hit_rate",
                observed=summary.expected_top1_hit_rate,
                threshold=thresholds["expected_top1"],
            )
        )
    return breaches


def run_gate(
    qrels_path: str,
    k: int = DEFAULT_K,
    thresholds: dict | None = None,
    search_fn: SearchFn | None = None,
) -> CorrectnessGateResult:
    """High-level gate: parse qrels, run correctness, compute breaches.

    Fail-closed: a parse error or in-process throw surfaces as a breach (the
    gate ran in PASS posture and now cannot proceed) rather than a silent skip.
    """
    th = {
        "recall_at_k": DEFAULT_RECALL_AT_K,
        "first_relevant_hit": DEFAULT_FIRST_RELEVANT_HIT,
        "expected_top1": DEFAULT_EXPECTED_TOP1,
    }
    if thresholds:
        th.update({k2: v for k2, v in thresholds.items() if v is not None})

    try:
        content = Path(qrels_path).read_text(encoding="utf-8")
        qrels = parse_qrels_file(content)
    except (OSError, QrelsParseError) as err:
        return CorrectnessGateResult(
            ran=True,
            qrels_path=qrels_path,
            thresholds=th,
            breaches=[Breach(metric="qrels_parse", reason="qrels_unreadable", error_tail=str(err))],
        )

    try:
        summary, per_query = run_correctness_gate(qrels, k=k, search_fn=search_fn)
    except Exception as err:
        return CorrectnessGateResult(
            ran=True,
            qrels_path=qrels_path,
            thresholds=th,
            breaches=[
                Breach(metric="correctness_gate", reason="orchestrator_threw", error_tail=str(err))
            ],
        )

    breaches = _correctness_breaches(summary, per_query, th)
    return CorrectnessGateResult(
        ran=True,
        qrels_path=qrels_path,
        summary=summary,
        thresholds=th,
        breaches=breaches,
    )


# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------
def _result_to_dict(result: CorrectnessGateResult, verdict: str) -> dict:
    s = result.summary
    return {
        "schema_version": 1,
        "verdict": verdict,
        "correctness_gate": {
            "ran": result.ran,
            "qrels_path": result.qrels_path,
            "summary": (
                {
                    "k": s.k,
                    "queries_total": s.queries_total,
                    "queries_run": s.queries_run,
                    "queries_errored": s.queries_errored,
                    "mean_recall_at_k": round(s.mean_recall_at_k, 4),
                    "first_relevant_hit_rate": round(s.first_relevant_hit_rate, 4),
                    "expected_top1_hit_rate": round(s.expected_top1_hit_rate, 4),
                    "expected_top1_denominator": s.expected_top1_denominator,
                }
                if s
                else None
            ),
            "thresholds": result.thresholds,
            "breaches": [
                {
                    "metric": b.metric,
                    "observed": b.observed,
                    "threshold": b.threshold,
                    "reason": b.reason,
                    "error_tail": b.error_tail,
                }
                for b in result.breaches
            ],
        },
    }


def _print_human(result: CorrectnessGateResult, verdict: str) -> None:
    overall = "PASS" if verdict == "pass" else "FAIL"
    print(f"Verdict: {overall}\n")
    print("Correctness gate (--qrels)")
    s = result.summary
    if s:
        floor_r = result.thresholds["recall_at_k"] if result.thresholds else "?"
        floor_f = result.thresholds["first_relevant_hit"] if result.thresholds else 0
        print(f"  queries_run:        {s.queries_run}/{s.queries_total} ({s.queries_errored} errored)")
        print(f"  mean_recall@{s.k}:      {s.mean_recall_at_k:.3f} (floor {floor_r})")
        print(
            f"  first_relevant_hit: {s.first_relevant_hit_rate * 100:.1f}% "
            f"(floor {float(floor_f) * 100:.0f}%)"
        )
        if s.expected_top1_denominator > 0:
            floor_e = result.thresholds["expected_top1"] if result.thresholds else 0
            print(
                f"  expected_top1_hit:  {s.expected_top1_hit_rate * 100:.1f}% "
                f"over {s.expected_top1_denominator} queries (floor {float(floor_e) * 100:.0f}%)"
            )
    if result.breaches:
        print("  BREACHES:")
        for b in result.breaches:
            obs = f" observed={b.observed:.3f}" if isinstance(b.observed, float) else (
                f" observed={b.observed}" if b.observed is not None else ""
            )
            thr = f" threshold={b.threshold}" if b.threshold is not None else ""
            reason = f" reason={b.reason}" if b.reason else ""
            print(f"    - {b.metric}{obs}{thr}{reason}")
            if b.error_tail:
                print(f"      {b.error_tail[:200]}")


# ---------------------------------------------------------------------------
# CLI (ported from gbrain runEvalGate — exit 0/1/2)
# ---------------------------------------------------------------------------
def run_eval_gate(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Eval gate — fail CI on retrieval correctness drops (recall@K)",
    )
    parser.add_argument("--qrels", help="Qrels JSON file (frozen gabarito)")
    parser.add_argument("-k", "--k", type=int, default=DEFAULT_K, help=f"Top-K (default {DEFAULT_K})")
    parser.add_argument("--threshold-recall-at-k", type=float, default=None)
    parser.add_argument("--threshold-first-relevant-hit", type=float, default=None)
    parser.add_argument("--threshold-expected-top1", type=float, default=None)
    parser.add_argument("--json", action="store_true", help="Print JSON envelope")
    args = parser.parse_args(argv)

    if not args.qrels:
        print("Error: --qrels must be set", file=sys.stderr)
        return 2
    if not Path(args.qrels).exists():
        print(f"Error: qrels file not found: {args.qrels}", file=sys.stderr)
        return 2

    thresholds = {
        "recall_at_k": args.threshold_recall_at_k,
        "first_relevant_hit": args.threshold_first_relevant_hit,
        "expected_top1": args.threshold_expected_top1,
    }
    result = run_gate(args.qrels, k=args.k, thresholds=thresholds)
    verdict = "fail" if result.breaches else "pass"

    if args.json:
        print(json.dumps(_result_to_dict(result, verdict), indent=2, ensure_ascii=False))
    else:
        _print_human(result, verdict)

    return 1 if verdict == "fail" else 0


def main() -> None:
    sys.exit(run_eval_gate())


if __name__ == "__main__":
    main()
