"""Tests for core.intelligence.benchmark.framework.

Covers: Benchmark, BenchmarkSuite, BenchmarkResult, BenchmarkReport,
        load_benchmark_history, compare_benchmarks.
"""

import json
import time
from pathlib import Path

import pytest

from core.intelligence.benchmark.framework import (
    Benchmark,
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkSuite,
    compare_benchmarks,
    load_benchmark_history,
)


# ---------------------------------------------------------------------------
# BenchmarkResult
# ---------------------------------------------------------------------------


class TestBenchmarkResult:
    def test_fields_populated(self):
        r = BenchmarkResult(name="chunker", operation="chunk_500", duration_ms=12.5)
        assert r.name == "chunker"
        assert r.operation == "chunk_500"
        assert r.duration_ms == 12.5
        assert r.iterations == 1
        assert isinstance(r.metadata, dict)
        assert r.timestamp  # auto-populated

    def test_custom_timestamp_preserved(self):
        r = BenchmarkResult(
            name="x", operation="y", duration_ms=1.0, timestamp="2026-01-01T00:00:00Z"
        )
        assert r.timestamp == "2026-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------


class TestBenchmark:
    def test_measure_records_duration(self):
        bench = Benchmark("test")
        with bench.measure("sleep_op"):
            time.sleep(0.01)  # 10 ms
        assert len(bench.results) == 1
        assert bench.results[0].operation == "sleep_op"
        assert bench.results[0].duration_ms >= 5  # at least ~5ms

    def test_measure_records_on_exception(self):
        bench = Benchmark("test")
        with pytest.raises(ValueError):
            with bench.measure("failing_op"):
                raise ValueError("boom")
        # Duration should still be recorded despite the exception
        assert len(bench.results) == 1
        assert bench.results[0].operation == "failing_op"
        assert bench.results[0].duration_ms >= 0

    def test_measure_metadata(self):
        bench = Benchmark("test")
        with bench.measure("op", metadata={"tokens": 500}):
            pass
        assert bench.results[0].metadata == {"tokens": 500}

    def test_time_function_measures_execution(self):
        def slow_func():
            time.sleep(0.01)

        bench = Benchmark("test")
        result = bench.time_function(slow_func, operation="slow")
        assert result.operation == "slow"
        assert result.duration_ms >= 5
        assert result.iterations == 1

    def test_time_function_iterations_averages(self):
        call_count = 0

        def counter():
            nonlocal call_count
            call_count += 1

        bench = Benchmark("test")
        result = bench.time_function(counter, operation="count", iterations=5)
        assert call_count == 5
        assert result.iterations == 5
        assert "all_durations_ms" in result.metadata
        assert len(result.metadata["all_durations_ms"]) == 5

    def test_time_function_uses_func_name_as_default(self):
        def my_special_func():
            pass

        bench = Benchmark("test")
        result = bench.time_function(my_special_func)
        assert result.operation == "my_special_func"

    def test_save_writes_jsonl(self, tmp_path):
        bench = Benchmark("test", results_dir=tmp_path)
        with bench.measure("op1"):
            pass
        with bench.measure("op2"):
            pass
        out = bench.save()
        assert out.exists()
        lines = out.read_text().strip().splitlines()
        assert len(lines) == 2
        parsed = json.loads(lines[0])
        assert parsed["operation"] == "op1"

    def test_save_appends(self, tmp_path):
        bench = Benchmark("test", results_dir=tmp_path)
        with bench.measure("op1"):
            pass
        bench.save()
        with bench.measure("op2"):
            pass
        bench.save()
        out = tmp_path / "test.jsonl"
        lines = out.read_text().strip().splitlines()
        # op1 written first call, op1+op2 written second call (op2 only new)
        # Actually save() appends all current results each time.
        # After first save: 1 line (op1). After second save: 1 + 2 = 3 lines.
        assert len(lines) == 3

    def test_clear_empties_results(self):
        bench = Benchmark("test")
        with bench.measure("op"):
            pass
        assert len(bench.results) == 1
        bench.clear()
        assert len(bench.results) == 0


# ---------------------------------------------------------------------------
# BenchmarkReport
# ---------------------------------------------------------------------------


class TestBenchmarkReport:
    def test_summary_computes_stats(self):
        results = [
            BenchmarkResult(name="a", operation="op1", duration_ms=10.0),
            BenchmarkResult(name="a", operation="op2", duration_ms=20.0),
            BenchmarkResult(name="a", operation="op3", duration_ms=30.0),
        ]
        report = BenchmarkReport(
            suite_name="test_suite",
            results=results,
            total_duration_ms=60.0,
            timestamp="2026-01-01T00:00:00Z",
        )
        s = report.summary
        assert s["suite"] == "test_suite"
        assert s["total_benchmarks"] == 3
        assert s["total_duration_ms"] == 60.0
        assert s["mean_ms"] == 20.0
        assert s["median_ms"] == 20.0
        assert s["min_ms"] == 10.0
        assert s["max_ms"] == 30.0

    def test_summary_empty_results(self):
        report = BenchmarkReport(
            suite_name="empty",
            results=[],
            total_duration_ms=0,
            timestamp="2026-01-01T00:00:00Z",
        )
        s = report.summary
        assert s["total_benchmarks"] == 0
        assert s["mean_ms"] == 0


# ---------------------------------------------------------------------------
# BenchmarkSuite
# ---------------------------------------------------------------------------


class TestBenchmarkSuite:
    def test_create_adds_benchmark(self):
        suite = BenchmarkSuite("pipeline")
        bench = suite.create("chunker")
        assert isinstance(bench, Benchmark)
        assert bench.name == "chunker"

    def test_add_external_benchmark(self):
        suite = BenchmarkSuite("pipeline")
        bench = Benchmark("external")
        suite.add(bench)
        with bench.measure("op"):
            pass
        report = suite.run_report()
        assert len(report.results) == 1

    def test_run_report_aggregates_results(self):
        suite = BenchmarkSuite("pipeline")
        b1 = suite.create("chunker")
        b2 = suite.create("router")
        with b1.measure("chunk"):
            pass
        with b2.measure("route"):
            pass
        report = suite.run_report()
        assert report.suite_name == "pipeline"
        assert len(report.results) == 2
        ops = {r.operation for r in report.results}
        assert ops == {"chunk", "route"}

    def test_save_report_writes_json(self, tmp_path):
        suite = BenchmarkSuite("pipeline", results_dir=tmp_path)
        bench = suite.create("chunker")
        with bench.measure("op"):
            pass
        report = suite.run_report()
        out = suite.save_report(report)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["suite_name"] == "pipeline"
        assert "summary" in data
        assert "results" in data


# ---------------------------------------------------------------------------
# load_benchmark_history
# ---------------------------------------------------------------------------


class TestLoadBenchmarkHistory:
    def test_loads_from_jsonl(self, tmp_path):
        bench = Benchmark("loader_test", results_dir=tmp_path)
        with bench.measure("op_a"):
            pass
        with bench.measure("op_b"):
            pass
        bench.save()

        history = load_benchmark_history("loader_test", results_dir=tmp_path)
        assert len(history) == 2
        assert history[0].operation == "op_a"
        assert history[1].operation == "op_b"

    def test_returns_empty_for_missing_file(self, tmp_path):
        history = load_benchmark_history("nonexistent", results_dir=tmp_path)
        assert history == []

    def test_skips_malformed_lines(self, tmp_path):
        f = tmp_path / "bad.jsonl"
        f.write_text('{"name":"a","operation":"op","duration_ms":1.0,"iterations":1,"metadata":{},"timestamp":"t"}\nNOT_JSON\n')
        history = load_benchmark_history("bad", results_dir=tmp_path)
        assert len(history) == 1


# ---------------------------------------------------------------------------
# compare_benchmarks
# ---------------------------------------------------------------------------


class TestCompareBenchmarks:
    def test_detects_faster(self):
        current = [BenchmarkResult(name="a", operation="op", duration_ms=80.0)]
        baseline = [BenchmarkResult(name="a", operation="op", duration_ms=100.0)]
        cmp = compare_benchmarks(current, baseline)
        assert cmp["op"]["status"] == "faster"
        assert cmp["op"]["change_pct"] == -20.0

    def test_detects_slower(self):
        current = [BenchmarkResult(name="a", operation="op", duration_ms=120.0)]
        baseline = [BenchmarkResult(name="a", operation="op", duration_ms=100.0)]
        cmp = compare_benchmarks(current, baseline)
        assert cmp["op"]["status"] == "slower"
        assert cmp["op"]["change_pct"] == 20.0

    def test_detects_stable(self):
        current = [BenchmarkResult(name="a", operation="op", duration_ms=102.0)]
        baseline = [BenchmarkResult(name="a", operation="op", duration_ms=100.0)]
        cmp = compare_benchmarks(current, baseline)
        assert cmp["op"]["status"] == "stable"

    def test_detects_new_operation(self):
        current = [BenchmarkResult(name="a", operation="new_op", duration_ms=50.0)]
        baseline = []
        cmp = compare_benchmarks(current, baseline)
        assert cmp["new_op"]["status"] == "new"

    def test_detects_removed_operation(self):
        current = []
        baseline = [BenchmarkResult(name="a", operation="old_op", duration_ms=50.0)]
        cmp = compare_benchmarks(current, baseline)
        assert cmp["old_op"]["status"] == "removed"
