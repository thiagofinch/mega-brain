"""
audit_pipeline_contracts.py — MCE Contract Audit Tool (Story MCE-17.0, T3)

Performs AST-based static analysis of:
  - orchestrate.py  (PRODUCER)  — emits template_ids via emit_phase_payload(template_id="X", ...)
  - log_generator.py (CONSUMER) — reads template_ids via stream.get("X") or
                                  _with_disk_fallback(stream.get("X") or {}, ...)

Computes:
  phantom_reads = consumer reads template_ids that producer never emits
  dead_emits    = producer emits template_ids that consumer never reads
  schema_mismatch = same state file read with incompatible interfaces at different call sites

Output: Markdown audit report.

Usage:
  python3 -m engine.intelligence.pipeline.mce.audit_pipeline_contracts \\
    --producer engine/intelligence/pipeline/mce/orchestrate.py \\
    --consumer engine/intelligence/pipeline/mce/log_generator.py \\
    --output docs/audits/mce-contract-audit-2026-05-30.md
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class EmitSite:
    """One emit_phase_payload call in orchestrate.py."""

    template_id: str
    file: str
    line: int


@dataclass
class ReadSite:
    """One stream.get() or _with_disk_fallback(stream.get(...)) call in log_generator.py."""

    template_id: str
    file: str
    line: int
    read_method: str  # "stream.get" | "_with_disk_fallback"


@dataclass
class SchemaAccess:
    """How a JSON state file is accessed at a specific call site."""

    file_key: str      # logical file name, e.g. "ROLE-TRACKING.json"
    location: str      # "log_generator.py:L1409"
    accessor: str      # description of key path accessed
    schema_note: str   # what shape is expected


@dataclass
class SchemaMismatch:
    """Two or more accesses to the same state file with incompatible schemas."""

    state_file: str
    site_a: SchemaAccess
    site_b: SchemaAccess
    severity: str = "CRITICAL"


# ---------------------------------------------------------------------------
# AST walker: PRODUCER (orchestrate.py)
# ---------------------------------------------------------------------------


class EmitVisitor(ast.NodeVisitor):
    """Walks the producer AST and collects all emit_phase_payload(template_id=...) calls."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.sites: list[EmitSite] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = _resolve_call_name(node)
        if func_name in ("emit_phase_payload",):
            tid = _extract_kwarg_str(node, "template_id")
            if tid:
                self.sites.append(EmitSite(
                    template_id=tid,
                    file=self.filepath,
                    line=node.lineno,
                ))
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# AST walker: CONSUMER (log_generator.py)
# ---------------------------------------------------------------------------


class ReadVisitor(ast.NodeVisitor):
    """Walks the consumer AST and collects all stream.get(...) and
    _with_disk_fallback(stream.get(...), ...) call sites."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.sites: list[ReadSite] = []
        # Track stream.get() line numbers captured via _with_disk_fallback
        # so we can avoid double-counting them when we encounter them standalone
        self._disk_fallback_get_lines: set[int] = set()

    def visit_Call(self, node: ast.Call) -> None:
        func_name = _resolve_call_name(node)

        if func_name == "_with_disk_fallback":
            # First arg is stream.get("X") or (expr or stream.get("X") or {})
            # Walk first arg to find stream.get calls; record them only once
            if node.args:
                first_arg = node.args[0]
                inner_gets = _find_stream_gets_in_expr(first_arg)
                seen_in_this_call: set[tuple[str, int]] = set()
                for tid, get_line in inner_gets:
                    key = (tid, get_line)
                    if key not in seen_in_this_call:
                        seen_in_this_call.add(key)
                        self.sites.append(ReadSite(
                            template_id=tid,
                            file=self.filepath,
                            line=get_line,
                            read_method="_with_disk_fallback",
                        ))
                        self._disk_fallback_get_lines.add(get_line)
            self.generic_visit(node)
            return

        if _is_stream_get(node):
            tid = _get_stream_get_key(node)
            if tid and node.lineno not in self._disk_fallback_get_lines:
                self.sites.append(ReadSite(
                    template_id=tid,
                    file=self.filepath,
                    line=node.lineno,
                    read_method="stream.get",
                ))

        self.generic_visit(node)


# ---------------------------------------------------------------------------
# AST helper utilities
# ---------------------------------------------------------------------------


def _resolve_call_name(node: ast.Call) -> str:
    """Return a dotted name for the function being called."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts = []
        cur: ast.expr = node.func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def _extract_kwarg_str(node: ast.Call, kwarg: str) -> str | None:
    """Extract the string value of a keyword argument from a call node."""
    for kw in node.keywords:
        if kw.arg == kwarg:
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
    return None


def _is_stream_get(node: ast.Call) -> bool:
    """True if node is stream.get(...)."""
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "stream"
    )


def _get_stream_get_key(node: ast.Call) -> str | None:
    """Return the string key passed to stream.get(key)."""
    if node.args:
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def _find_stream_gets_in_expr(node: ast.expr) -> list[tuple[str, int]]:
    """Recursively find all stream.get("X") calls within an expression.
    Returns list of (template_id, lineno)."""
    results: list[tuple[str, int]] = []
    if isinstance(node, ast.Call) and _is_stream_get(node):
        key = _get_stream_get_key(node)
        if key:
            results.append((key, node.lineno))
        return results
    # BoolOp covers `stream.get("X") or stream.get("Y") or {}`
    if isinstance(node, ast.BoolOp):
        for value in node.values:
            results.extend(_find_stream_gets_in_expr(value))
        return results
    # Subscript, attribute, etc. — walk children
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.expr):
            results.extend(_find_stream_gets_in_expr(child))
    return results


# ---------------------------------------------------------------------------
# Schema mismatch detection
# ---------------------------------------------------------------------------
# Hand-crafted analysis of confirmed ROLE-TRACKING and INSIGHTS-STATE
# mismatches. Full inter-procedural schema inference via AST would require
# type inference far beyond a single-pass static tool.


def _detect_schema_mismatches(consumer_source: str, consumer_path: str) -> list[SchemaMismatch]:
    """
    Detect known schema mismatches in log_generator.py using line-level search.

    Two confirmed mismatches (roundtable strategic 2026-05-30):
    1. ROLE-TRACKING.json — _fpb_load_role_tracking returns a pre-extracted single-slug
       dict, while direct call sites read persons as a raw list and iterate themselves.
       Incompatible consumption interfaces for the same state file.
    2. INSIGHTS-STATE.json — dual-path: persons[person_name] (single-person key lookup)
       vs persons.values() iteration (multi-person aggregate view).
    """
    mismatches: list[SchemaMismatch] = []
    lines_list = consumer_source.splitlines()

    # ---- 1. ROLE-TRACKING.json -------------------------------------------
    # Extractor interface: _fpb_load_role_tracking (returns pre-extracted dict)
    # Direct reader interface: rt.get("persons", []) + iterate inline

    rt_extractor_fn_line: int | None = None
    rt_direct_reader_line: int | None = None

    for i, line in enumerate(lines_list, start=1):
        stripped = line.strip()
        if "def _fpb_load_role_tracking" in stripped:
            rt_extractor_fn_line = i
        # Direct reader: rt.get("persons", []) outside of the extractor function
        # These appear in _step_pre_00_bucket_selection and _load_role_tracking_for_cascade
        if re.search(r'(?:rt|data)\.get\("persons",\s*\[\]', stripped):
            # Exclude the line inside _fpb_load_role_tracking itself
            if rt_extractor_fn_line is None or i > rt_extractor_fn_line + 20:
                if rt_direct_reader_line is None:
                    rt_direct_reader_line = i

    if rt_extractor_fn_line and rt_direct_reader_line:
        mismatches.append(SchemaMismatch(
            state_file="ROLE-TRACKING.json",
            site_a=SchemaAccess(
                file_key="ROLE-TRACKING.json",
                location=f"log_generator.py:L{rt_extractor_fn_line} (_fpb_load_role_tracking)",
                accessor="persons as list -> filter by slug -> return single extracted dict",
                schema_note=(
                    "returns PRE-EXTRACTED single-slug dict; "
                    "callers receive {domains:[], themes:[], domain_count:int, ...}"
                ),
            ),
            site_b=SchemaAccess(
                file_key="ROLE-TRACKING.json",
                location=f"log_generator.py:L{rt_direct_reader_line} (direct reader)",
                accessor='rt.get("persons", []) -> iterate list -> access raw p dict inline',
                schema_note=(
                    "reads raw persons list, iterates it inline, accesses "
                    "p['slug'] / p['domains'] directly — incompatible interface with "
                    "_fpb_load_role_tracking consumers"
                ),
            ),
            severity="CRITICAL",
        ))

    # ---- 2. INSIGHTS-STATE.json ------------------------------------------
    # Path A: persons.get(person_name) — single-person key lookup
    # Path B: for pdata in persons.values() — multi-person aggregate view

    insights_path_a_line: int | None = None
    insights_path_b_line: int | None = None

    for i, line in enumerate(lines_list, start=1):
        stripped = line.strip()
        if insights_path_a_line is None and re.search(r'persons\.get\(person_name', stripped):
            insights_path_a_line = i
        if insights_path_b_line is None and "for pdata in persons.values()" in stripped:
            insights_path_b_line = i

    if insights_path_a_line and insights_path_b_line:
        mismatches.append(SchemaMismatch(
            state_file="INSIGHTS-STATE.json",
            site_a=SchemaAccess(
                file_key="INSIGHTS-STATE.json",
                location=f"log_generator.py:L{insights_path_a_line}",
                accessor="persons.get(person_name, {})",
                schema_note=(
                    "accesses by PERSON_NAME string key -> single-person view; "
                    "pdata may be dict{'insights':[...]} or list"
                ),
            ),
            site_b=SchemaAccess(
                file_key="INSIGHTS-STATE.json",
                location=f"log_generator.py:L{insights_path_b_line}",
                accessor="for pdata in persons.values()",
                schema_note=(
                    "iterates ALL persons in file -> multi-person aggregate view; "
                    "may include cross-slug contamination"
                ),
            ),
            severity="HIGH",
        ))

    return mismatches


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------


_PHANTOM_HIGH_KEYWORDS = {
    "source_discovery", "download_extract", "speaker_visual_gate",
    "filename_sidecar", "classification", "organization", "routing",
    "batch_creation", "chunking", "embeddings", "entity_discovery",
    "lifecycle_move", "batch_history", "workspace_sync",
    "cascading_roles", "cascading_solos", "cascading_themes",
    "memory_enrichment",
}

_DEAD_HIGH_KEYWORDS = {
    "execution_chunks", "execution_embeddings", "execution_behavioral",
    "execution_identity", "execution_voice", "execution_entities",
    "atlas_classification", "ingest_report", "batch_log",
    "pipeline_report", "pipeline_recover", "pipeline_cleanup",
    "promote_agent", "consolidate_dossier", "phase8_tracking",
    "cross_bucket_cascade", "execution_report", "phase8_gate",
    "full_pipeline_report",
}


def _phantom_severity(tid: str) -> str:
    return "HIGH" if tid in _PHANTOM_HIGH_KEYWORDS else "MEDIUM"


def _dead_severity(tid: str) -> str:
    return "HIGH" if tid in _DEAD_HIGH_KEYWORDS else "MEDIUM"


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------


def analyze(producer_path: pathlib.Path, consumer_path: pathlib.Path) -> dict[str, Any]:
    """Parse both files and compute contract gaps."""

    # Parse producer
    producer_source = producer_path.read_text(encoding="utf-8")
    producer_tree = ast.parse(producer_source, filename=str(producer_path))
    emit_visitor = EmitVisitor(filepath=producer_path.name)
    emit_visitor.visit(producer_tree)

    # Parse consumer
    consumer_source = consumer_path.read_text(encoding="utf-8")
    consumer_tree = ast.parse(consumer_source, filename=str(consumer_path))
    read_visitor = ReadVisitor(filepath=consumer_path.name)
    read_visitor.visit(consumer_tree)

    emit_sites = emit_visitor.sites
    read_sites = read_visitor.sites

    # Build unique template_id sets
    emitted_ids: set[str] = {s.template_id for s in emit_sites}
    read_ids: set[str] = {s.template_id for s in read_sites}

    phantom_ids = read_ids - emitted_ids
    dead_ids = emitted_ids - read_ids
    healthy_ids = emitted_ids & read_ids

    # Build phantom read list — de-duplicate: one row per unique (template_id, line)
    seen_phantom: set[tuple[str, int]] = set()
    phantom_reads: list[dict[str, Any]] = []
    for site in sorted(read_sites, key=lambda s: (s.template_id, s.line)):
        if site.template_id in phantom_ids:
            key = (site.template_id, site.line)
            if key not in seen_phantom:
                seen_phantom.add(key)
                phantom_reads.append({
                    "template_id": site.template_id,
                    "location": f"{site.file}:{site.line}",
                    "method": site.read_method,
                    "severity": _phantom_severity(site.template_id),
                })

    # Build dead emit list — de-duplicate: one row per unique template_id (first occurrence)
    seen_dead: set[str] = set()
    dead_emits: list[dict[str, Any]] = []
    for site in sorted(emit_sites, key=lambda s: s.template_id):
        if site.template_id in dead_ids and site.template_id not in seen_dead:
            seen_dead.add(site.template_id)
            dead_emits.append({
                "template_id": site.template_id,
                "location": f"{site.file}:{site.line}",
                "severity": _dead_severity(site.template_id),
            })

    # Schema mismatches
    schema_mismatches = _detect_schema_mismatches(consumer_source, str(consumer_path))

    return {
        "producer_path": str(producer_path),
        "consumer_path": str(consumer_path),
        "producer_lines": producer_source.count("\n") + 1,
        "consumer_lines": consumer_source.count("\n") + 1,
        "emit_sites": emit_sites,
        "read_sites": read_sites,
        "emitted_ids": sorted(emitted_ids),
        "read_ids": sorted(read_ids),
        "phantom_reads": phantom_reads,
        "dead_emits": dead_emits,
        "healthy_ids": sorted(healthy_ids),
        "schema_mismatches": schema_mismatches,
    }


# ---------------------------------------------------------------------------
# Markdown report renderer
# ---------------------------------------------------------------------------


def render_markdown(result: dict[str, Any]) -> str:
    now_str = datetime.now(UTC).strftime("%Y-%m-%d")
    phantom_reads = result["phantom_reads"]
    dead_emits = result["dead_emits"]
    schema_mismatches = result["schema_mismatches"]

    n_phantom = len(phantom_reads)
    n_dead = len(dead_emits)
    n_schema = len(schema_mismatches)
    n_total = n_phantom + n_dead + n_schema
    n_healthy = len(result["healthy_ids"])
    n_emits_total = len(result["emitted_ids"])
    n_reads_total = len(result["read_ids"])

    lines: list[str] = [
        f"# MCE Contract Audit — {now_str}",
        "",
        f"**Producer:** `{pathlib.Path(result['producer_path']).name}` ({result['producer_lines']} lines)",
        f"**Consumer:** `{pathlib.Path(result['consumer_path']).name}` ({result['consumer_lines']} lines)",
        f"**Total emits (unique):** {n_emits_total}",
        f"**Total reads (unique):** {n_reads_total}",
        f"**Healthy intersection:** {n_healthy}",
        "",
        "---",
        "",
    ]

    # Phantom Reads
    lines.append(
        f"## Phantom Reads (consumer reads template_id that producer never emits) — {n_phantom} items"
    )
    lines.append("")
    if phantom_reads:
        lines.append("| # | template_id | consumer location | method | severity |")
        lines.append("|---|-------------|-------------------|--------|----------|")
        for i, pr in enumerate(phantom_reads, start=1):
            lines.append(
                f"| {i} | `{pr['template_id']}` | {pr['location']} | {pr['method']} | {pr['severity']} |"
            )
    else:
        lines.append("_No phantom reads detected._")
    lines.append("")

    # Dead Emits
    lines.append(
        f"## Dead Emits (producer emits template_id that consumer never reads) — {n_dead} items"
    )
    lines.append("")
    if dead_emits:
        lines.append("| # | template_id | producer location | severity |")
        lines.append("|---|-------------|-------------------|----------|")
        for i, de in enumerate(dead_emits, start=1):
            lines.append(
                f"| {i} | `{de['template_id']}` | {de['location']} | {de['severity']} |"
            )
    else:
        lines.append("_No dead emits detected._")
    lines.append("")

    # Schema Mismatches
    lines.append(f"## Schema Mismatches — {n_schema} items")
    lines.append("")
    if schema_mismatches:
        lines.append("| # | state_file | site_a (location, schema) | site_b (location, schema) | severity |")
        lines.append("|---|------------|---------------------------|---------------------------|----------|")
        for i, sm in enumerate(schema_mismatches, start=1):
            a = sm.site_a
            b = sm.site_b
            a_desc = f"{a.location}: `{a.accessor}` — {a.schema_note}"
            b_desc = f"{b.location}: `{b.accessor}` — {b.schema_note}"
            lines.append(
                f"| {i} | `{sm.state_file}` | {a_desc} | {b_desc} | {sm.severity} |"
            )
    else:
        lines.append("_No schema mismatches detected._")
    lines.append("")

    # Healthy Intersection
    lines.append("## Healthy Intersection (emitted AND read)")
    lines.append("")
    if result["healthy_ids"]:
        lines.append("| # | template_id |")
        lines.append("|---|-------------|")
        for i, tid in enumerate(result["healthy_ids"], start=1):
            lines.append(f"| {i} | `{tid}` |")
    else:
        lines.append("_No healthy pairs found._")
    lines.append("")

    # Summary
    convergence = round(min(n_total, 38) / max(n_total, 38) * 100) if n_total > 0 else 0
    lines += [
        "## Summary",
        "",
        "| Category | Count | Roundtable Expectation |",
        "|----------|-------|------------------------|",
        f"| Phantom reads | **{n_phantom}** | 15 |",
        f"| Dead emits | **{n_dead}** | 21 |",
        f"| Schema mismatches | **{n_schema}** | 2 |",
        f"| **TOTAL** | **{n_total}** | **38** |",
        "",
        f"**Convergence vs roundtable expectation (38 gaps):** {convergence}%",
        "",
        "### Phantom Read IDs (unique)",
        "",
        ", ".join(sorted({f"`{pr['template_id']}`" for pr in phantom_reads})) if phantom_reads else "_none_",
        "",
        "### Dead Emit IDs",
        "",
        ", ".join(f"`{de['template_id']}`" for de in dead_emits) if dead_emits else "_none_",
        "",
        "---",
        (
            f"_Generated by `audit_pipeline_contracts.py` on "
            f"{datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%S UTC')}_"
        ),
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit MCE pipeline contracts via AST static analysis."
    )
    parser.add_argument(
        "--producer",
        required=True,
        help="Path to orchestrate.py (the producer)",
    )
    parser.add_argument(
        "--consumer",
        required=True,
        help="Path to log_generator.py (the consumer)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the markdown audit report",
    )
    args = parser.parse_args()

    producer_path = pathlib.Path(args.producer)
    consumer_path = pathlib.Path(args.consumer)
    output_path = pathlib.Path(args.output)

    if not producer_path.exists():
        print(f"ERROR: producer not found: {producer_path}", file=sys.stderr)
        sys.exit(1)
    if not consumer_path.exists():
        print(f"ERROR: consumer not found: {consumer_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing producer: {producer_path} ...")
    print(f"Parsing consumer: {consumer_path} ...")

    result = analyze(producer_path, consumer_path)

    n_phantom = len(result["phantom_reads"])
    n_dead = len(result["dead_emits"])
    n_schema = len(result["schema_mismatches"])
    n_total = n_phantom + n_dead + n_schema

    print("\nResults:")
    print(f"  Emitted (unique): {len(result['emitted_ids'])}")
    print(f"  Read    (unique): {len(result['read_ids'])}")
    print(f"  Healthy:          {len(result['healthy_ids'])}")
    print(f"  Phantom reads:    {n_phantom}  (expected ~15)")
    print(f"  Dead emits:       {n_dead}  (expected ~21)")
    print(f"  Schema mismatches:{n_schema}  (expected 2)")
    print(f"  TOTAL gaps:       {n_total}  (expected ~38)")

    report = render_markdown(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nReport written: {output_path} ({len(report.encode())} bytes)")


if __name__ == "__main__":
    main()
