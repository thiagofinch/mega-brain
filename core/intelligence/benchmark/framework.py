"""Benchmark framework for Mega Brain pipeline performance.

Measures execution time, throughput, and quality for pipeline operations.
Results stored in .data/benchmarks/ as JSONL for trend tracking.

Usage:
    from core.intelligence.benchmark.framework import Benchmark, BenchmarkSuite

    bench = Benchmark("chunker")
    with bench.measure("chunk_1000_tokens"):
        chunker.chunk(text)
    bench.save()
"""

import json
import statistics
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_RESULTS_DIR = Path(".data/benchmarks")


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str
    operation: str
    duration_ms: float
    iterations: int = 1
    metadata: dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class BenchmarkReport:
    """Aggregated results from a benchmark suite run."""

    suite_name: str
    results: list[BenchmarkResult]
    total_duration_ms: float
    timestamp: str
    system_info: dict = field(default_factory=dict)

    @property
    def summary(self) -> dict:
        durations = [r.duration_ms for r in self.results]
        return {
            "suite": self.suite_name,
            "total_benchmarks": len(self.results),
            "total_duration_ms": self.total_duration_ms,
            "mean_ms": statistics.mean(durations) if durations else 0,
            "median_ms": statistics.median(durations) if durations else 0,
            "min_ms": min(durations) if durations else 0,
            "max_ms": max(durations) if durations else 0,
            "timestamp": self.timestamp,
        }


class Benchmark:
    """Individual benchmark runner."""

    def __init__(self, name: str, results_dir: str | Path | None = None):
        self.name = name
        self._results_dir = Path(results_dir or DEFAULT_RESULTS_DIR)
        self._results: list[BenchmarkResult] = []

    @contextmanager
    def measure(self, operation: str, metadata: dict | None = None):
        """Context manager to measure execution time."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._results.append(
                BenchmarkResult(
                    name=self.name,
                    operation=operation,
                    duration_ms=round(elapsed_ms, 3),
                    metadata=metadata or {},
                )
            )

    def time_function(
        self,
        func,
        *args,
        operation: str = "",
        iterations: int = 1,
        **kwargs,
    ) -> BenchmarkResult:
        """Benchmark a function with optional repeated iterations."""
        op_name = operation or func.__name__
        durations = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            durations.append((time.perf_counter() - start) * 1000)

        avg_ms = statistics.mean(durations)
        result = BenchmarkResult(
            name=self.name,
            operation=op_name,
            duration_ms=round(avg_ms, 3),
            iterations=iterations,
            metadata={"all_durations_ms": [round(d, 3) for d in durations]},
        )
        self._results.append(result)
        return result

    @property
    def results(self) -> list[BenchmarkResult]:
        return self._results

    def save(self, results_file: str | Path | None = None) -> Path:
        """Save results to JSONL file."""
        if results_file is None:
            self._results_dir.mkdir(parents=True, exist_ok=True)
            results_file = self._results_dir / f"{self.name}.jsonl"
        results_file = Path(results_file)
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, "a", encoding="utf-8") as f:
            for result in self._results:
                f.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
        return results_file

    def clear(self):
        """Clear collected results."""
        self._results.clear()


class BenchmarkSuite:
    """Run multiple benchmarks as a suite."""

    def __init__(self, name: str, results_dir: str | Path | None = None):
        self.name = name
        self._results_dir = Path(results_dir or DEFAULT_RESULTS_DIR)
        self._benchmarks: list[Benchmark] = []

    def add(self, benchmark: Benchmark) -> None:
        self._benchmarks.append(benchmark)

    def create(self, name: str) -> Benchmark:
        bench = Benchmark(name, self._results_dir)
        self._benchmarks.append(bench)
        return bench

    def run_report(self) -> BenchmarkReport:
        """Generate aggregated report from all benchmarks."""
        all_results = []
        for bench in self._benchmarks:
            all_results.extend(bench.results)

        total_ms = sum(r.duration_ms for r in all_results)

        return BenchmarkReport(
            suite_name=self.name,
            results=all_results,
            total_duration_ms=round(total_ms, 3),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def save_report(self, report: BenchmarkReport | None = None) -> Path:
        """Save suite report to JSON file."""
        if report is None:
            report = self.run_report()

        self._results_dir.mkdir(parents=True, exist_ok=True)
        report_file = (
            self._results_dir
            / f"suite-{self.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )

        report_dict = {
            "suite_name": report.suite_name,
            "summary": report.summary,
            "results": [asdict(r) for r in report.results],
            "timestamp": report.timestamp,
        }
        report_file.write_text(
            json.dumps(report_dict, indent=2, ensure_ascii=False)
        )
        return report_file


def load_benchmark_history(
    name: str, results_dir: str | Path | None = None
) -> list[BenchmarkResult]:
    """Load historical benchmark results from JSONL."""
    results_dir = Path(results_dir or DEFAULT_RESULTS_DIR)
    results_file = results_dir / f"{name}.jsonl"

    if not results_file.exists():
        return []

    results = []
    for line in results_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                data = json.loads(line)
                results.append(BenchmarkResult(**data))
            except (json.JSONDecodeError, TypeError):
                continue
    return results


def compare_benchmarks(
    current: list[BenchmarkResult], baseline: list[BenchmarkResult]
) -> dict:
    """Compare current benchmark results against a baseline."""
    current_by_op = {r.operation: r.duration_ms for r in current}
    baseline_by_op = {r.operation: r.duration_ms for r in baseline}

    comparisons = {}
    for op in set(current_by_op) | set(baseline_by_op):
        curr = current_by_op.get(op)
        base = baseline_by_op.get(op)
        if curr is not None and base is not None:
            change_pct = ((curr - base) / base) * 100 if base > 0 else 0
            comparisons[op] = {
                "current_ms": curr,
                "baseline_ms": base,
                "change_pct": round(change_pct, 1),
                "status": (
                    "faster"
                    if change_pct < -5
                    else "slower" if change_pct > 5 else "stable"
                ),
            }
        elif curr is not None:
            comparisons[op] = {
                "current_ms": curr,
                "baseline_ms": None,
                "status": "new",
            }
        else:
            comparisons[op] = {
                "current_ms": None,
                "baseline_ms": base,
                "status": "removed",
            }

    return comparisons
