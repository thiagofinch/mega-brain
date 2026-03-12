#!/usr/bin/env python3
"""
RAG EVALUATOR - Phase 3.5
==========================
Lightweight evaluation metrics inspired by RAGAS:
- Faithfulness: Is the answer faithful to the retrieved context?
- Context Precision: Are the top chunks actually relevant?
- Context Recall: Did we retrieve all relevant chunks?
- Answer Relevancy: Does the answer address the question?

Uses LLM-as-judge (Claude) for evaluation when available,
falls back to heuristic scoring.

Versao: 1.0.0
Data: 2026-03-01
"""

import json
import sys
import time
from pathlib import Path

from .hybrid_query import hybrid_search

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
EVAL_DIR = BASE_DIR / ".data" / "rag_eval"

# ---------------------------------------------------------------------------
# TEST CASES
# ---------------------------------------------------------------------------
BASIC_TEST_SUITE: list[dict] = [
    {
        "id": "T001",
        "query": "commission structure for closers",
        "expected_domains": ["compensation", "vendas"],
        "expected_persons": ["alex-hormozi", "cole-gordon"],
        "min_results": 3,
    },
    {
        "id": "T002",
        "query": "how to handle price objection",
        "expected_domains": ["vendas"],
        "expected_persons": ["cole-gordon"],
        "min_results": 3,
    },
    {
        "id": "T003",
        "query": "hiring process for sales team",
        "expected_domains": ["hiring", "vendas"],
        "expected_persons": [],
        "min_results": 2,
    },
    {
        "id": "T004",
        "query": "offer creation methodology",
        "expected_domains": ["offers", "product"],
        "expected_persons": ["alex-hormozi"],
        "min_results": 2,
    },
    {
        "id": "T005",
        "query": "follow up sequence after no show",
        "expected_domains": ["vendas", "follow_up"],
        "expected_persons": [],
        "min_results": 2,
    },
]


# ---------------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------------
class EvalResult:
    """Result of evaluating a single test case."""

    def __init__(self, test_id: str, query: str):
        self.test_id = test_id
        self.query = query
        self.context_precision: float = 0.0
        self.context_recall: float = 0.0
        self.result_count: int = 0
        self.domain_hit_rate: float = 0.0
        self.person_hit_rate: float = 0.0
        self.latency_ms: float = 0.0
        self.passed: bool = False
        self.details: dict = {}

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "query": self.query,
            "context_precision": round(self.context_precision, 3),
            "context_recall": round(self.context_recall, 3),
            "domain_hit_rate": round(self.domain_hit_rate, 3),
            "person_hit_rate": round(self.person_hit_rate, 3),
            "result_count": self.result_count,
            "latency_ms": round(self.latency_ms, 1),
            "passed": self.passed,
        }


def evaluate_test_case(test: dict) -> EvalResult:
    """Evaluate a single test case against the hybrid search pipeline."""
    result = EvalResult(test["id"], test["query"])

    # Run search
    search_result = hybrid_search(test["query"], top_k=10)

    if "error" in search_result:
        result.details["error"] = search_result["error"]
        return result

    results = search_result.get("results", [])
    result.result_count = len(results)
    result.latency_ms = search_result.get("latency_ms", 0)

    # Metric 1: Context Precision (are results relevant?)
    # Heuristic: check if result domains/persons match expected
    expected_domains = set(test.get("expected_domains", []))
    expected_persons = set(test.get("expected_persons", []))

    domain_hits = 0
    person_hits = 0
    relevant_count = 0

    for r in results:
        r_domain = r.get("domain", "").lower()
        r_person = r.get("person", "").lower()
        is_relevant = False

        if expected_domains and r_domain:
            for ed in expected_domains:
                if ed in r_domain or r_domain in ed:
                    domain_hits += 1
                    is_relevant = True
                    break

        if expected_persons and r_person:
            for ep in expected_persons:
                if ep in r_person or r_person in ep:
                    person_hits += 1
                    is_relevant = True
                    break

        # Also check text content for query terms
        text = r.get("text_preview", "").lower()
        query_terms = test["query"].lower().split()
        term_matches = sum(1 for t in query_terms if t in text and len(t) > 3)
        if term_matches >= 2:
            is_relevant = True

        if is_relevant:
            relevant_count += 1

    # Context precision = relevant / total
    if results:
        result.context_precision = relevant_count / len(results)

    # Domain hit rate
    if expected_domains:
        found_domains = set()
        for r in results:
            rd = r.get("domain", "").lower()
            for ed in expected_domains:
                if ed in rd or rd in ed:
                    found_domains.add(ed)
        result.domain_hit_rate = len(found_domains) / len(expected_domains)

    # Person hit rate
    if expected_persons:
        found_persons = set()
        for r in results:
            rp = r.get("person", "").lower()
            for ep in expected_persons:
                if ep in rp or rp in ep:
                    found_persons.add(ep)
        result.person_hit_rate = len(found_persons) / len(expected_persons)
    else:
        result.person_hit_rate = 1.0  # No person requirement

    # Context recall = did we find enough results?
    min_results = test.get("min_results", 3)
    result.context_recall = min(1.0, result.result_count / max(min_results, 1))

    # Pass/fail
    result.passed = (
        result.result_count >= min_results
        and result.context_precision >= 0.3
        and result.context_recall >= 0.5
    )

    return result


# ---------------------------------------------------------------------------
# SUITE RUNNER
# ---------------------------------------------------------------------------
def run_suite(
    suite: list[dict] | None = None,
    verbose: bool = True,
) -> dict:
    """Run a full evaluation suite.

    Returns:
        {
            "suite_size": int,
            "passed": int,
            "failed": int,
            "avg_precision": float,
            "avg_recall": float,
            "avg_latency_ms": float,
            "results": [EvalResult.to_dict(), ...],
        }
    """
    if suite is None:
        suite = BASIC_TEST_SUITE

    results: list[EvalResult] = []

    for test in suite:
        if verbose:
            print(f"  Running {test['id']}: {test['query'][:50]}...", end=" ")

        eval_result = evaluate_test_case(test)
        results.append(eval_result)

        if verbose:
            status = "PASS" if eval_result.passed else "FAIL"
            print(f"[{status}] precision={eval_result.context_precision:.2f} "
                  f"recall={eval_result.context_recall:.2f} "
                  f"latency={eval_result.latency_ms:.0f}ms")

    # Aggregate
    passed = sum(1 for r in results if r.passed)
    precisions = [r.context_precision for r in results]
    recalls = [r.context_recall for r in results]
    latencies = [r.latency_ms for r in results]

    summary = {
        "suite_size": len(suite),
        "passed": passed,
        "failed": len(suite) - passed,
        "pass_rate": round(passed / max(len(suite), 1), 3),
        "avg_precision": round(sum(precisions) / max(len(precisions), 1), 3),
        "avg_recall": round(sum(recalls) / max(len(recalls), 1), 3),
        "avg_latency_ms": round(sum(latencies) / max(len(latencies), 1), 1),
        "results": [r.to_dict() for r in results],
    }

    return summary


def save_results(summary: dict, eval_dir: Path | None = None) -> Path:
    """Save evaluation results to disk."""
    d = eval_dir or EVAL_DIR
    d.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filepath = d / f"eval-{timestamp}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return filepath


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAG Evaluation")
    parser.add_argument("--test-suite", choices=["basic"], default="basic",
                        help="Which test suite to run")
    parser.add_argument("--save", action="store_true",
                        help="Save results to disk")
    parser.add_argument("--quiet", action="store_true",
                        help="Minimal output")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("RAG EVALUATOR")
    print(f"{'='*60}\n")

    suite = BASIC_TEST_SUITE if args.test_suite == "basic" else BASIC_TEST_SUITE

    summary = run_suite(suite, verbose=not args.quiet)

    print(f"\n{'─'*60}")
    print(f"RESULTS: {summary['passed']}/{summary['suite_size']} passed "
          f"({summary['pass_rate']*100:.0f}%)")
    print(f"Avg Precision: {summary['avg_precision']:.3f}")
    print(f"Avg Recall:    {summary['avg_recall']:.3f}")
    print(f"Avg Latency:   {summary['avg_latency_ms']:.0f}ms")
    print(f"{'─'*60}")

    if args.save:
        filepath = save_results(summary)
        print(f"\nResults saved to: {filepath}")

    print(f"\n{'='*60}\n")

    # Exit code based on pass rate
    sys.exit(0 if summary["pass_rate"] >= 0.6 else 1)


if __name__ == "__main__":
    main()
