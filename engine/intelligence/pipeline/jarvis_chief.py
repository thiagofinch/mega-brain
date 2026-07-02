"""jarvis-chief — Pipeline-Chief Orchestrator

Sequences the 23 cmds in orchestrate.py, enforces gates between phases,
invokes the Chronicler skill to render each phase live in chat.

Never runs cognitive work directly — pure orchestration.

Functions
---------
orchestrate(slug)  -- run full MCE pipeline for slug, rendering each phase
resume(slug)       -- continue from last completed phase
state(slug)        -- display current pipeline state (no execution)

EXPECTED_PHASES manifest
------------------------
Canonical order of 23 phases mapping template_id → cmd name.
Used by orchestrate() and the coverage gate.

STORY-MCE-6.0 Phase 5 (2026-05-22).
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# PATH SETUP — resolve project root regardless of cwd
# ---------------------------------------------------------------------------

_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parents[
    2
]  # engine/intelligence/pipeline → engine/intelligence → engine → root

# ---------------------------------------------------------------------------
# EXPECTED_PHASES manifest
# Canonical sequence — each entry maps phase_idx → template_id → cmd name
# ---------------------------------------------------------------------------

EXPECTED_PHASES: list[dict[str, Any]] = [
    {"phase_idx": 0, "template_id": "ingestion_guard", "cmd": "cmd_ingest", "gate": False},
    {"phase_idx": 1, "template_id": "ingest_report", "cmd": "cmd_ingest", "gate": False},
    {"phase_idx": 2, "template_id": "batch_log", "cmd": "cmd_batch", "gate": False},
    {"phase_idx": 3, "template_id": "execution_chunks", "cmd": "cmd_process_batch", "gate": False},
    {
        "phase_idx": 4,
        "template_id": "execution_embeddings",
        "cmd": "cmd_process_batch",
        "gate": False,
    },
    {
        "phase_idx": 5,
        "template_id": "rag_indexation",
        "cmd": "cmd_rag_index",
        "gate": True,
        "gate_rule": "chunks_delta_tolerance",
    },
    {
        "phase_idx": 5.5,
        "template_id": "graphrag_index",
        "cmd": "cmd_graphrag_index",
        "gate": False,
        "opt_in_env": "MCE_GRAPHRAG_ENABLED",
        # STORY-ENABLE-GBRAIN-FULL: default ON (mirrors orchestrate.cmd_graphrag_index
        # which now defaults MCE_GRAPHRAG_ENABLED to "1"). Unset → active; opt-out =0.
        "opt_in_default": "1",
    },
    {"phase_idx": 6, "template_id": "execution_insights", "cmd": "cmd_insights", "gate": False},
    {"phase_idx": 7, "template_id": "execution_behavioral", "cmd": "cmd_behavioral", "gate": False},
    {"phase_idx": 8, "template_id": "execution_voice", "cmd": "cmd_voice", "gate": False},
    {"phase_idx": 9, "template_id": "execution_identity", "cmd": "cmd_identity", "gate": False},
    {
        "phase_idx": 10,
        "template_id": "identity_checkpoint",
        "cmd": "cmd_identity_checkpoint",
        "gate": True,
        "gate_rule": "identity_checkpoint_approve",
    },
    {"phase_idx": 11, "template_id": "contradictions", "cmd": "cmd_consolidate", "gate": False},
    {"phase_idx": 12, "template_id": "narrative_metabolism", "cmd": "cmd_narrative", "gate": False},
    {"phase_idx": 13, "template_id": "sources_compilation", "cmd": "cmd_sources", "gate": False},
    {
        "phase_idx": 14,
        "template_id": "domain_aggregator",
        "cmd": "cmd_aggregate_domain",
        "gate": False,
    },
    {"phase_idx": 15, "template_id": "agent_state", "cmd": "cmd_promote_agent", "gate": False},
    {
        "phase_idx": 16,
        "template_id": "phase8_gate",
        "cmd": "cmd_phase8",
        "gate": True,
        "gate_rule": "phase8_all_checks_pass",
    },
    {"phase_idx": 17, "template_id": "workspace_sync", "cmd": "cmd_finalize", "gate": False},
    {"phase_idx": 18, "template_id": "full_pipeline_report", "cmd": "cmd_finalize", "gate": False},
    {"phase_idx": 19, "template_id": "llm_cost", "cmd": "cmd_finalize", "gate": False},
    {
        "phase_idx": 20,
        "template_id": "auto_advance_trigger",
        "cmd": "cmd_auto_advance",
        "gate": False,
    },
    {"phase_idx": 21, "template_id": "squad_activation", "cmd": "cmd_finalize", "gate": False},
    {
        "phase_idx": 22,
        "template_id": "chronicler_audit",
        "cmd": "run_chronicler_audit",
        "gate": False,
    },
]

# ---------------------------------------------------------------------------
# PHASE-STREAM.jsonl reader
# ---------------------------------------------------------------------------


def _default_artifacts_root(slug: str) -> Path:
    """Resolve the canonical PHASE-STREAM directory for *slug*.

    MUST agree with the writer (``phase_payload.emit_phase_payload`` →
    ``engine.paths.ARTIFACTS``). The artifacts root migrated to ``.data/artifacts``
    (engine/paths.py: ``ARTIFACTS = ROOT/.data/artifacts``, marker ``# S15``).
    The legacy default here was ``<root>/artifacts/pipeline/<slug>`` — an EMPTY
    directory under the new layout — which made the orchestrator read 0 payloads
    on a real ``/ingest --process`` run and synthesize every phase as SILENT
    (coverage_pct collapses to 0). Reader and writer must point at the same path.

    Falls back to the legacy location only if ``engine.paths`` cannot be imported
    (e.g. minimal test fixtures without the full project on sys.path).
    """
    try:
        from engine.paths import ARTIFACTS

        return ARTIFACTS / "pipeline" / slug
    except Exception:  # pragma: no cover — defensive fallback for stripped envs
        return _PROJECT_ROOT / ".data" / "artifacts" / "pipeline" / slug


def _phase_stream_path(slug: str, artifacts_root: Path | None = None) -> Path:
    root = artifacts_root or _default_artifacts_root(slug)
    return root / "PHASE-STREAM.jsonl"


def _read_phase_stream(slug: str, artifacts_root: Path | None = None) -> list[dict]:
    """Read all payloads from PHASE-STREAM.jsonl for slug."""
    path = _phase_stream_path(slug, artifacts_root)
    if not path.exists():
        return []
    payloads = []
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        payloads.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except OSError:
        pass
    return payloads


def _read_last_payload(slug: str, artifacts_root: Path | None = None) -> dict | None:
    """Read the tail (most recent) entry from PHASE-STREAM.jsonl."""
    payloads = _read_phase_stream(slug, artifacts_root)
    return payloads[-1] if payloads else None


# ---------------------------------------------------------------------------
# Chronicler render invocation
# ---------------------------------------------------------------------------


def _render_phase(payload: dict, history: list[dict]) -> str:
    """Invoke chronicler renderers.render() for a single payload.

    Falls back to a minimal text block if chronicler is unavailable
    (e.g. during test fixtures without full project path).
    """
    template_id = payload.get("template_id", "unknown")
    slug = payload.get("slug", "?")
    status = payload.get("status", "?")
    ts = payload.get("ts", 0)

    try:
        sys.path.insert(0, str(_PROJECT_ROOT))
        # Import via dotted path since .claude is not a Python package
        import importlib.util

        skill_path = _PROJECT_ROOT / ".claude" / "skills" / "chronicler" / "renderers.py"
        spec = importlib.util.spec_from_file_location("chronicler_renderers", skill_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod.render(template_id, payload, history, mode="canonical")
    except Exception:
        pass  # Fall through to minimal block

    # Minimal fallback (no chronicler available). If the payload carries a
    # self-contained ascii_block (e.g. a BYPASSED/opt-in-disabled box), render it
    # verbatim — ascii_block is the canonical body (mirrors chronicler _base_render).
    ascii_block = payload.get("ascii_block", "")
    if ascii_block:
        return ascii_block
    ts_str = datetime.fromtimestamp(ts, UTC).strftime("%H:%M:%S") if ts else "?"
    return (
        f"[PHASE {template_id}] slug={slug} status={status} ts={ts_str}\n"
        f"  metrics: {json.dumps(payload.get('metrics', {}), ensure_ascii=False)[:120]}"
    )


def _synthesize_silent_payload(expected: dict, slug: str) -> dict:
    """Create a synthetic SILENT-PHASE payload when expected template is missing."""
    return {
        "ts": time.time(),
        "slug": slug,
        "template_id": f"SILENT-PHASE:{expected['template_id']}",
        "status": "silent",
        "metrics": {
            "phase_idx": expected["phase_idx"],
            "expected_template": expected["template_id"],
            "expected_cmd": expected["cmd"],
        },
        "ascii_block": "",
        "schema_version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Opt-in phase awareness (e.g. GraphRAG behind MCE_GRAPHRAG_ENABLED)
# ---------------------------------------------------------------------------
#
# Some EXPECTED_PHASES are opt-in: they only run when an env flag is set
# (declared via "opt_in_env" on the phase). When the flag is OFF, the phase
# is intentionally NOT executed — it must NOT count against coverage and must
# NOT render as a SILENT-PHASE anomaly (a standard run would otherwise show
# sub-100% / "SILENT", which reads as breakage). When the flag is ON, the
# phase rejoins the coverage denominator and a missing payload IS a real
# silent (genuine coverage gap).


def _phase_is_active(expected: dict) -> bool:
    """Return True if this expected phase should be counted/required this run.

    A phase is INACTIVE only when it declares an ``opt_in_env`` flag that is
    currently OFF. All non-opt-in phases are always active. Treated as ON when
    the env var is set to a truthy value ("1", "true", "yes", "on").

    A phase MAY declare ``opt_in_default`` (the value used when the env var is
    UNSET). Default is "0" (off when unset — legacy opt-in). A phase that is ON
    by default (e.g. graphrag_index post STORY-ENABLE-GBRAIN-FULL) sets
    ``opt_in_default="1"`` so an unset env means ACTIVE and ``=0`` opts out —
    symmetric with the executor (orchestrate.cmd_graphrag_index).
    """
    flag = expected.get("opt_in_env")
    if not flag:
        return True
    import os

    default = str(expected.get("opt_in_default", "0"))
    return os.environ.get(flag, default).strip().lower() in {"1", "true", "yes", "on"}


def _active_expected_phases(expected_phases: list[dict]) -> list[dict]:
    """Filter EXPECTED_PHASES to those active for the current env."""
    return [p for p in expected_phases if _phase_is_active(p)]


def _synthesize_optin_disabled_payload(expected: dict, slug: str) -> dict:
    """Synthesize a clean 'opt-in disabled' (BYPASSED) payload for a phase whose
    env flag is OFF. Renders verbatim as a tidy box — NOT a SILENT-PHASE warning.

    Keeps the real template_id (status="skipped") so it is NOT counted as a
    free-form/SILENT box by the audit, and never pollutes coverage either way
    (the phase is excluded from the denominator when inactive).
    """
    flag = expected.get("opt_in_env", "?")
    tid = expected["template_id"]
    W = 77  # inner width between the ║ borders (minus the 2-space left pad)

    def _row(text: str) -> str:
        # Left-pad 2 spaces, right-pad to width. Uses str len (no wide chars here
        # except an em-dash which renders 1 cell in monospace terminals).
        return f"║  {text:<{W - 2}}║"

    ascii_block = "\n".join(
        [
            f"╔{'═' * W}╗",
            _row("PHASE BYPASSED (opt-in disabled)"),
            _row(f"template_id: {tid}"),
            _row(f"reason: {flag} not set -- phase skipped by design"),
            _row(f"enable with: export {flag}=1"),
            f"╚{'═' * W}╝",
        ]
    )
    return {
        "ts": time.time(),
        "slug": slug,
        "template_id": tid,
        "status": "skipped",
        "metrics": {
            "phase_idx": expected["phase_idx"],
            "opt_in_env": flag,
            "opt_in_enabled": False,
        },
        "ascii_block": ascii_block,
        "schema_version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------


def _evaluate_gate(phase_def: dict, payload: dict) -> tuple[bool, str]:
    """Evaluate a gate rule.

    Returns:
        (passed: bool, reason: str)
    """
    rule = phase_def.get("gate_rule", "")
    m = payload.get("metrics", {})

    if rule == "chunks_delta_tolerance":
        # Gate 5: RAG indexation regression gate (Constitution Art. XV).
        # This gate guards against INDEX SHRINKAGE (data loss) — it must block
        # ONLY when the chunk count drops beyond tolerance. Positive deltas are
        # normal, desired growth from ingesting new material and must ALWAYS pass.
        # Origin: live /ingest --process halted at phase 5 on a +102 growth delta
        # because the prior abs() comparison blocked growth as well as shrinkage.
        chunks_delta = m.get("chunks_delta", 0)
        tolerance = m.get("chunks_tolerance", 100)
        if chunks_delta < -tolerance:
            return False, (
                f"chunks_delta {chunks_delta} indicates index SHRINKAGE beyond "
                f"tolerance {tolerance} (possible data loss)"
            )
        return True, "chunks_delta within tolerance (growth allowed)"

    if rule == "identity_checkpoint_approve":
        # Gate 10: identity_checkpoint APPROVE/REVIEW/REJECT
        verdict = m.get("verdict", m.get("checkpoint_result", "")).upper()
        if verdict == "REJECT":
            return False, "identity_checkpoint REJECT — blocking pipeline"
        return True, f"identity_checkpoint: {verdict or 'APPROVE'}"

    if rule == "phase8_all_checks_pass":
        # Gate 16: phase8_gate all 7 checks pass
        checks = m.get("checks", {})
        failed = [k for k, v in checks.items() if not v] if isinstance(checks, dict) else []
        if failed:
            return False, f"phase8_gate FAIL: {', '.join(failed)}"
        total = m.get("total_checks", m.get("gates_total", 0))
        passed = m.get("passed_checks", m.get("gates_passed", total))
        if total and passed < total:
            return False, f"phase8_gate {passed}/{total} checks passed"
        return True, "phase8_gate: all checks passed"

    # Unknown rule — pass by default
    return True, f"unknown gate rule: {rule}"


# ---------------------------------------------------------------------------
# Core orchestrate loop
# ---------------------------------------------------------------------------


def _import_orchestrate_cmds() -> Any:
    """Lazy-import the orchestrate module so jarvis_chief has no circular dep."""
    import importlib

    return importlib.import_module("engine.intelligence.pipeline.mce.orchestrate")


def _invoke_cmd(name: str, fn: Any, slug: str) -> dict[str, Any]:
    """Invoke a pipeline cmd, returning result. Never raises — fail-open per Art. XII."""
    try:
        result = fn(slug)
        if not isinstance(result, dict):
            result = {"success": True, "cmd": name, "raw": result}
        return result
    except Exception as exc:
        return {"success": False, "cmd": name, "error": str(exc)}


def _read_new_payloads(slug: str, pointer: int, artifacts_root: Path | None) -> list[dict]:
    """Return payloads appended to PHASE-STREAM.jsonl since *pointer* (line count)."""
    all_payloads = _read_phase_stream(slug, artifacts_root)
    return all_payloads[pointer:]


def orchestrate(
    slug: str,
    *,
    artifacts_root: Path | None = None,
    user_override: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the full MCE pipeline for slug, actively invoking each cmd then rendering.

    Active orchestration loop (STORY-MCE-6.0 Phase 8a-fix):
      For each cmd in CMD_SEQUENCE:
        1. Record pointer (current PHASE-STREAM line count)
        2. Invoke the cmd (fail-open per Art. XII)
        3. Read new payloads emitted since pointer
        4. Render each new payload via chronicler and print
        5. Update pointer to end-of-file
        6. Evaluate gate if applicable — REJECT stops pipeline

    Phases 0-2 (ingestion_guard, ingest_report, batch_log) are emitted by
    /ingest BEFORE jarvis-chief takes over. They are read from the existing
    PHASE-STREAM and rendered without re-invocation.

    Args:
        slug: pipeline slug (e.g. "alex-hormozi")
        artifacts_root: optional override for artifacts root
        user_override: if True, do not stop on gate failures
        dry_run: if True, render existing PHASE-STREAM without invoking cmds
                 (used for testing and *state* display)

    Returns:
        Dict with 'phases_rendered', 'gates_failed', 'stopped_at', 'coverage_pct'
    """
    # ------------------------------------------------------------------
    # Pre-existing entries (phases already emitted by /ingest step)
    # ------------------------------------------------------------------
    initial_history = _read_phase_stream(slug, artifacts_root)
    pointer = len(initial_history)  # line position before we start invoking

    phases_rendered = 0
    gates_failed: list[dict] = []
    stopped_at = None

    # Phases 0-2 are already in PHASE-STREAM from /ingest — render them first
    PRE_INGESTED_TEMPLATES = {"ingestion_guard", "ingest_report", "batch_log"}

    for expected in EXPECTED_PHASES:
        tid = expected["template_id"]
        if tid not in PRE_INGESTED_TEMPLATES:
            break
        matching = [p for p in initial_history if p.get("template_id") == tid]
        payload = matching[-1] if matching else _synthesize_silent_payload(expected, slug)
        rendered = _render_phase(payload, initial_history)
        phases_rendered += 1
        if not dry_run:
            print(rendered)
            sys.stdout.flush()

    if dry_run:
        # dry_run: just render whatever is in PHASE-STREAM, no cmd invocations
        for expected in EXPECTED_PHASES:
            tid = expected["template_id"]
            if tid in PRE_INGESTED_TEMPLATES:
                continue  # already rendered above
            matching = [p for p in initial_history if p.get("template_id") == tid]
            if matching:
                payload = matching[-1]
            elif not _phase_is_active(expected):
                # opt-in phase whose flag is OFF — render clean BYPASSED, not SILENT
                payload = _synthesize_optin_disabled_payload(expected, slug)
            else:
                payload = _synthesize_silent_payload(expected, slug)
            payload["metrics"] = payload.get("metrics", {})
            payload["metrics"]["phase_idx"] = expected["phase_idx"]
            rendered = _render_phase(payload, initial_history)
            phases_rendered += 1
            print(rendered)
            sys.stdout.flush()
            if expected.get("gate") and payload.get("status") != "silent":
                gate_passed, gate_reason = _evaluate_gate(expected, payload)
                if not gate_passed and not user_override:
                    gates_failed.append(
                        {
                            "phase_idx": expected["phase_idx"],
                            "template_id": tid,
                            "reason": gate_reason,
                        }
                    )
                    stopped_at = expected["phase_idx"]
                    break
        audit_payload = _build_chronicler_audit_payload(
            slug, initial_history, EXPECTED_PHASES, initial_history
        )
        print(_render_phase(audit_payload, initial_history))
        # Dedupe coverage math (Story MCE-6.0.2). Opt-in phases whose env flag is
        # OFF are excluded from the denominator — a standard run must show 100%.
        expected_tids = {p["template_id"] for p in _active_expected_phases(EXPECTED_PHASES)}
        rendered_tids = {p.get("template_id") for p in initial_history if p.get("template_id")}
        covered_tids = expected_tids & rendered_tids
        total = len(expected_tids)
        return {
            "slug": slug,
            "phases_rendered": phases_rendered,
            "phases_unique": len(covered_tids),
            "gates_failed": gates_failed,
            "stopped_at": stopped_at,
            "coverage_pct": int(len(covered_tids) / total * 100) if total else 0,
            "total_phases": total,
        }

    # ------------------------------------------------------------------
    # Active invocation — import cmds lazily (avoid circular at module load)
    # ------------------------------------------------------------------
    try:
        orch = _import_orchestrate_cmds()
    except Exception as exc:
        print(f"[jarvis-chief] FATAL: cannot import orchestrate module: {exc}", file=sys.stderr)
        orch = None

    # Derive batch_ids from cmd_batch for cmd_process_batch phases
    _batch_ids: list[str] = []
    _batch_ids_resolved = False

    def _get_batch_ids() -> list[str]:
        nonlocal _batch_ids, _batch_ids_resolved
        if _batch_ids_resolved:
            return _batch_ids
        _batch_ids_resolved = True
        if not orch:
            return _batch_ids
        try:
            br = orch.cmd_batch(slug, single_file=True)
            ids = br.get("batch_ids") or []
            if not ids and isinstance(br.get("batches"), list):
                ids = [b.get("batch_id") for b in br["batches"] if b.get("batch_id")]
            if not ids and isinstance(br.get("batches_for_slug"), list):
                ids = [b.get("batch_id") for b in br["batches_for_slug"] if b.get("batch_id")]
            _batch_ids = [i for i in ids if i]
        except Exception as exc:
            print(f"[jarvis-chief] cmd_batch error (non-fatal): {exc}", file=sys.stderr)
        return _batch_ids

    # Derive domains for cmd_aggregate_domain
    def _get_domains() -> list[str]:
        if not orch:
            return []
        try:
            from engine.intelligence.pipeline.domain_aggregator import _list_domains_for_slug

            return _list_domains_for_slug(slug, root=_PROJECT_ROOT) or []
        except Exception:
            return []

    # ------------------------------------------------------------------
    # CMD_SEQUENCE: maps template_ids that need active invocation → lambda
    # Phases 0-2 are skipped (pre-ingested). chronicler_audit is handled
    # after the loop via run_chronicler_audit().
    # ------------------------------------------------------------------

    def _run_process_batch_phases() -> list[dict]:
        """Invoke cmd_process_batch for each batch_id; return per-batch results."""
        results = []
        batch_ids = _get_batch_ids()
        if not batch_ids:
            # No batches found — emit a single no-op invocation so PHASE-STREAM gets entries
            if orch:
                try:
                    r = orch.cmd_process_batch(batch_id="", slug=slug)
                    results.append(r)
                except Exception as exc:
                    results.append(
                        {"success": False, "cmd": "cmd_process_batch", "error": str(exc)}
                    )
        else:
            for bid in batch_ids:
                if orch:
                    try:
                        r = orch.cmd_process_batch(batch_id=bid, slug=slug)
                        results.append(r)
                    except Exception as exc:
                        results.append(
                            {"success": False, "cmd": "cmd_process_batch", "error": str(exc)}
                        )
        return results

    def _run_aggregate_domain() -> None:
        """Invoke cmd_aggregate_domain for each domain this slug belongs to."""
        if not orch:
            return
        for domain in _get_domains():
            try:
                orch.cmd_aggregate_domain(domain)
            except Exception as exc:
                print(
                    f"[jarvis-chief] cmd_aggregate_domain({domain}) error (non-fatal): {exc}",
                    file=sys.stderr,
                )

    # Template_ids that trigger a group cmd invocation before render
    # Maps template_id → callable(slug) that invokes the right cmd(s)
    CMD_DISPATCH: dict[str, Any] = {}
    if orch:
        CMD_DISPATCH = {
            "execution_chunks": _run_process_batch_phases,
            "execution_embeddings": lambda: None,  # same cmd as above, already ran
            "rag_indexation": lambda: _invoke_cmd("cmd_rag_index", orch.cmd_rag_index, slug),
            "execution_insights": lambda: _invoke_cmd("cmd_insights", orch.cmd_insights, slug),
            "execution_behavioral": lambda: _invoke_cmd(
                "cmd_behavioral", orch.cmd_behavioral, slug
            ),
            "execution_voice": lambda: _invoke_cmd("cmd_voice", orch.cmd_voice, slug),
            "execution_identity": lambda: _invoke_cmd("cmd_identity", orch.cmd_identity, slug),
            "identity_checkpoint": lambda: _invoke_cmd(
                "cmd_identity_checkpoint", orch.cmd_identity_checkpoint, slug
            ),
            "contradictions": lambda: _invoke_cmd("cmd_consolidate", orch.cmd_consolidate, slug),
            "narrative_metabolism": lambda: _invoke_cmd("cmd_narrative", orch.cmd_narrative, slug),
            "sources_compilation": lambda: _invoke_cmd("cmd_sources", orch.cmd_sources, slug),
            "domain_aggregator": _run_aggregate_domain,
            "agent_state": lambda: _invoke_cmd("cmd_promote_agent", orch.cmd_promote_agent, slug),
            "phase8_gate": lambda: _invoke_cmd("cmd_phase8", orch.cmd_phase8, slug),
            # cmd_finalize emits workspace_sync + full_pipeline_report + llm_cost + squad_activation
            "workspace_sync": lambda: _invoke_cmd("cmd_finalize", orch.cmd_finalize, slug),
            "full_pipeline_report": lambda: None,  # already emitted by cmd_finalize above
            "llm_cost": lambda: None,  # already emitted by cmd_finalize above
            "auto_advance_trigger": lambda: _invoke_cmd(
                "cmd_auto_advance", orch.cmd_auto_advance, slug
            ),
            "squad_activation": lambda: None,  # already emitted by cmd_finalize above
        }

    # ------------------------------------------------------------------
    # Main loop — iterate EXPECTED_PHASES, invoke cmds, render new payloads
    # ------------------------------------------------------------------
    all_history = list(initial_history)

    for expected in EXPECTED_PHASES:
        tid = expected["template_id"]
        phase_idx = expected["phase_idx"]

        if tid in PRE_INGESTED_TEMPLATES:
            continue  # already rendered in pre-ingested block above
        if tid == "chronicler_audit":
            continue  # handled after loop

        # 1) Record pointer before invocation
        pointer = len(all_history)

        # 2) Invoke the cmd for this phase (if dispatch registered)
        dispatch_fn = CMD_DISPATCH.get(tid)
        if dispatch_fn is not None:
            try:
                dispatch_fn()
            except Exception as exc:
                print(
                    f"[jarvis-chief] cmd dispatch error for {tid} (non-fatal): {exc}",
                    file=sys.stderr,
                )

        # 3) Read new payloads emitted since pointer
        fresh_history = _read_phase_stream(slug, artifacts_root)
        new_payloads = fresh_history[pointer:]
        all_history = fresh_history

        # 4) Render new payloads; if none emitted, synthesize SILENT-PHASE
        if new_payloads:
            for payload in new_payloads:
                payload["metrics"] = payload.get("metrics", {})
                payload["metrics"]["phase_idx"] = phase_idx
                rendered = _render_phase(payload, all_history)
                phases_rendered += 1
                print(rendered)
                sys.stdout.flush()
        else:
            # No payload emitted by THIS phase's dispatch — could be:
            #   (1) a no-op sibling of a multi-template emitter (cmd_finalize emits
            #       workspace_sync + full_pipeline_report + llm_cost + squad_activation
            #       all at the workspace_sync step; the later phases dispatch lambda:None),
            #   (2) a genuinely failed/absent cmd (real SILENT).
            # We must distinguish them by the RIGHT history window: everything emitted
            # SO FAR THIS RUN (all_history), NOT the pre-run snapshot (initial_history).
            # Looking at initial_history misses payloads a sibling cmd emitted moments
            # ago during this same run → false SILENT-PHASE + coverage collapse.
            # Genuine silents are preserved: if a cmd truly failed, its template_id is
            # absent from all_history too, so we still synthesize SILENT.
            already_emitted = any(p.get("template_id") == tid for p in all_history)
            if not already_emitted:
                if not _phase_is_active(expected):
                    # Opt-in phase with env flag OFF: render a clean BYPASSED box,
                    # NOT a SILENT-PHASE anomaly. It is also excluded from the
                    # coverage denominator below, so a standard run shows 100%.
                    payload = _synthesize_optin_disabled_payload(expected, slug)
                else:
                    payload = _synthesize_silent_payload(expected, slug)
                rendered = _render_phase(payload, all_history)
                phases_rendered += 1
                print(rendered)
                sys.stdout.flush()

        # 5) Gate evaluation — use the most recently rendered payload for this template
        if expected.get("gate"):
            gate_payloads = [p for p in all_history if p.get("template_id") == tid]
            gate_payload = gate_payloads[-1] if gate_payloads else None
            if gate_payload and gate_payload.get("status") != "silent":
                gate_passed, gate_reason = _evaluate_gate(expected, gate_payload)
                if not gate_passed and not user_override:
                    gates_failed.append(
                        {
                            "phase_idx": phase_idx,
                            "template_id": tid,
                            "reason": gate_reason,
                        }
                    )
                    stopped_at = phase_idx
                    print(
                        f"\n[jarvis-chief] GATE BLOCKED at phase {phase_idx} "
                        f"({tid}): {gate_reason}\n"
                        f"Re-run with --override to skip gates."
                    )
                    break

    # ------------------------------------------------------------------
    # Post-loop: chronicler audit
    # ------------------------------------------------------------------
    final_history = _read_phase_stream(slug, artifacts_root)
    audit_payload = _build_chronicler_audit_payload(
        slug, final_history, EXPECTED_PHASES, final_history
    )
    rendered_audit = _render_phase(audit_payload, final_history)
    print(rendered_audit)
    sys.stdout.flush()

    # Dedupe coverage math — count unique template_ids that match EXPECTED_PHASES,
    # not raw emission count (cmd_finalize emits multiple template_ids and some
    # templates render twice during the loop). Coverage_pct must stay in [0, 100].
    # Opt-in phases whose env flag is OFF (e.g. graphrag_index when
    # MCE_GRAPHRAG_ENABLED is unset) are excluded from the denominator — a
    # standard run is "complete" at 100% without the opt-in phase.
    expected_tids = {p["template_id"] for p in _active_expected_phases(EXPECTED_PHASES)}
    rendered_tids = {p.get("template_id") for p in final_history if p.get("template_id")}
    covered_tids = expected_tids & rendered_tids
    total = len(expected_tids)
    coverage_pct = int(len(covered_tids) / total * 100) if total else 0

    # Informational: how many emissions per template (>=2 = duplicates)
    from collections import Counter

    emission_counts = Counter(p.get("template_id") for p in final_history if p.get("template_id"))
    duplicate_emissions = {tid: c for tid, c in emission_counts.items() if c > 1}

    return {
        "slug": slug,
        "phases_rendered": phases_rendered,
        "phases_unique": len(covered_tids),
        "gates_failed": gates_failed,
        "stopped_at": stopped_at,
        "coverage_pct": coverage_pct,
        "total_phases": total,
        "duplicate_emissions": duplicate_emissions,
    }


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------


def resume(slug: str, *, artifacts_root: Path | None = None) -> dict[str, Any]:
    """Continue from last completed phase.

    Reads the PHASE-STREAM.jsonl tail, finds the last rendered template_id,
    and returns the next expected phase so the agent can invoke the right cmd.

    Returns:
        Dict with 'last_phase', 'next_phase', 'next_cmd', 'remaining_phases'
    """
    history = _read_phase_stream(slug, artifacts_root)
    if not history:
        return {
            "last_phase": None,
            "next_phase": EXPECTED_PHASES[0]["template_id"] if EXPECTED_PHASES else None,
            "next_cmd": EXPECTED_PHASES[0]["cmd"] if EXPECTED_PHASES else None,
            "remaining_phases": len(EXPECTED_PHASES),
            "message": f"No PHASE-STREAM.jsonl found for {slug} — start from phase 0",
        }

    last = history[-1]
    last_tid = last.get("template_id", "")

    # Find the index of the last rendered template in EXPECTED_PHASES
    last_idx = -1
    for i, ph in enumerate(EXPECTED_PHASES):
        if ph["template_id"] == last_tid:
            last_idx = i

    next_idx = last_idx + 1
    if next_idx >= len(EXPECTED_PHASES):
        return {
            "last_phase": last_tid,
            "next_phase": None,
            "next_cmd": None,
            "remaining_phases": 0,
            "message": f"Pipeline complete for {slug} — all {len(EXPECTED_PHASES)} phases rendered",
        }

    next_phase = EXPECTED_PHASES[next_idx]
    remaining = len(EXPECTED_PHASES) - next_idx

    return {
        "last_phase": last_tid,
        "next_phase": next_phase["template_id"],
        "next_cmd": next_phase["cmd"],
        "remaining_phases": remaining,
        "resume_from_idx": next_idx,
        "message": (
            f"Resume {slug} from phase {next_idx}/{len(EXPECTED_PHASES)-1}: "
            f"{next_phase['template_id']} → {next_phase['cmd']}"
        ),
    }


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def state(slug: str, *, artifacts_root: Path | None = None) -> str:
    """Display current pipeline state without executing anything.

    Reads PHASE-STREAM.jsonl and renders a readable status block.

    Returns:
        Human-readable status string suitable for printing in chat.
    """
    history = _read_phase_stream(slug, artifacts_root)
    total = len(EXPECTED_PHASES)

    if not history:
        return (
            f"╔{'═' * 77}╗\n"
            f"║  jarvis-chief STATE: {slug:<55}║\n"
            f"╠{'═' * 77}╣\n"
            f"║  No PHASE-STREAM.jsonl found for this slug.{'':33}║\n"
            f"║  Pipeline has not started.{'':50}║\n"
            f"╚{'═' * 77}╝"
        )

    # Build rendered_map: template_id → payload
    rendered_map: dict[str, dict] = {}
    for p in history:
        tid = p.get("template_id", "")
        rendered_map[tid] = p

    # Compute stats
    rendered_tids = set(rendered_map.keys())
    expected_tids = {ph["template_id"] for ph in EXPECTED_PHASES}
    missing = expected_tids - rendered_tids

    last = history[-1]
    last_tid = last.get("template_id", "?")
    last_ts = last.get("ts", 0)
    last_ts_str = (
        datetime.fromtimestamp(last_ts, UTC).strftime("%Y-%m-%d %H:%M:%S UTC") if last_ts else "?"
    )

    rendered_count = len([t for t in EXPECTED_PHASES if t["template_id"] in rendered_tids])
    coverage_pct = int(rendered_count / total * 100) if total else 0

    bar_filled = int(coverage_pct / 100 * 30)
    bar = "▓" * bar_filled + "░" * (30 - bar_filled)

    # Resume info
    resume_info = resume(slug, artifacts_root=artifacts_root)

    lines = [
        f"╔{'═' * 77}╗",
        f"║  jarvis-chief STATE: {slug:<55}║",
        f"╠{'═' * 77}╣",
        f"║  PHASE-STREAM entries: {len(history):<53}║",
        f"║  Coverage: {rendered_count}/{total} phases [{bar}] {coverage_pct}%{'':18}║",
        f"║  Last rendered: {last_tid:<60}║",
        f"║  Last ts: {last_ts_str:<66}║",
        f"╠{'═' * 77}╣",
    ]

    # Phase table (compact)
    for ph in EXPECTED_PHASES:
        tid = ph["template_id"]
        if tid in rendered_tids:
            p = rendered_map[tid]
            status = p.get("status", "?")
            marker = "✓" if status in ("ok", "warning") else ("✗" if status == "fail" else "~")
        else:
            marker = "·"
        gate_mark = " [GATE]" if ph.get("gate") else ""
        line = f"║  {marker} [{ph['phase_idx']:2d}] {tid:<45}{gate_mark:<10}║"
        lines.append(line[:80].ljust(79) + "║" if len(line) > 80 else line)

    lines.append(f"╠{'═' * 77}╣")

    if resume_info.get("next_phase"):
        next_cmd = (resume_info.get("next_cmd") or "")[:55]
        lines.append(f"║  NEXT: {next_cmd:<69}║")
        msg = resume_info.get("message", "")[:73]
        lines.append(f"║  {msg:<75}║")
    else:
        lines.append(f"║  STATUS: Pipeline complete or blocked.{'':38}║")

    if missing:
        miss_preview = ", ".join(sorted(missing)[:3])[:55]
        ellipsis = "..." if len(missing) > 3 else ""
        lines.append(
            f"║  MISSING ({len(missing)}): {miss_preview}{ellipsis:<{18 - len(ellipsis)}}║"[:80]
            + "║"
            if len(f"║  MISSING ({len(missing)}): {miss_preview}{ellipsis}") > 78
            else f"║  MISSING ({len(missing)}): {miss_preview}{ellipsis:<{75 - len(f'MISSING ({len(missing)}): {miss_preview}{ellipsis}')}}║"
        )

    lines.append(f"╚{'═' * 77}╝")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chronicler audit builder
# ---------------------------------------------------------------------------


def _build_chronicler_audit_payload(
    slug: str,
    history: list[dict],
    expected_phases: list[dict],
    all_history: list[dict],
) -> dict:
    """Build the chronicler_audit payload from rendered history.

    Opt-in phases whose env flag is OFF (e.g. graphrag_index) are excluded from
    the expected set: they are not "missing" and do not count against
    templates_expected, so a standard run audits as complete (0 missing).
    """
    active_phases = _active_expected_phases(expected_phases)
    expected_tids = {ph["template_id"] for ph in active_phases}
    rendered_tids = {p.get("template_id") for p in history}

    missing = sorted(expected_tids - rendered_tids)
    schema_mismatches = sum(
        1
        for p in history
        if p.get("status") == "fail" and "schema" in str(p.get("metrics", {})).lower()
    )

    # Count free-form boxes
    free_form_count = sum(
        1
        for p in history
        if str(p.get("template_id", "")).startswith("SILENT-PHASE:")
        or str(p.get("template_id", "")).startswith("FREE-FORM:")
    )

    rendered_count = len([t for t in active_phases if t["template_id"] in rendered_tids])

    return {
        "ts": time.time(),
        "slug": slug,
        "template_id": "chronicler_audit",
        "status": "ok" if not missing else "warning",
        "metrics": {
            "phase_idx": 22,
            "templates_rendered": rendered_count,
            "templates_expected": len(active_phases),
            "missing_templates": missing,
            "schema_mismatches": schema_mismatches,
            "free_form_count": free_form_count,
        },
        "ascii_block": "",
        "schema_version": "1.0.0",
    }


def run_chronicler_audit(slug: str, *, artifacts_root: Path | None = None) -> str:
    """Run the post-finalize Chronicler audit and return the rendered box.

    Called by jarvis-chief after cmd_finalize completes.
    """
    from engine.intelligence.pipeline.phase_payload import emit_phase_payload

    history = _read_phase_stream(slug, artifacts_root)
    audit_payload = _build_chronicler_audit_payload(slug, history, EXPECTED_PHASES, history)

    # Emit to PHASE-STREAM so it's tracked
    try:
        emit_phase_payload(
            slug=slug,
            template_id="chronicler_audit",
            status=audit_payload["status"],
            metrics=audit_payload["metrics"],
            ascii_block="",
            artifacts_root=artifacts_root,
        )
    except Exception:
        pass  # Non-fatal — audit must not crash pipeline

    return _render_phase(audit_payload, history)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli_state(slug: str) -> None:
    print(state(slug))


def _cli_resume(slug: str) -> None:
    r = resume(slug)
    print(json.dumps(r, indent=2, ensure_ascii=False))


def _cli_orchestrate(slug: str, *, override: bool = False) -> None:
    result = orchestrate(slug, user_override=override)
    print(f"\n[jarvis-chief] Done: {result}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="jarvis-chief — Pipeline-Chief Orchestrator",
        prog="jarvis_chief.py",
    )
    subparsers = parser.add_subparsers(dest="command")

    state_p = subparsers.add_parser("state", help="Display current pipeline state")
    state_p.add_argument("slug")

    resume_p = subparsers.add_parser("resume", help="Show resume point")
    resume_p.add_argument("slug")

    orch_p = subparsers.add_parser("orchestrate", help="Render all phases from PHASE-STREAM")
    orch_p.add_argument("slug")
    orch_p.add_argument("--override", action="store_true", help="Skip gates")

    args = parser.parse_args()

    if args.command == "state":
        _cli_state(args.slug)
    elif args.command == "resume":
        _cli_resume(args.slug)
    elif args.command == "orchestrate":
        _cli_orchestrate(args.slug, override=getattr(args, "override", False))
    else:
        parser.print_help()
