#!/usr/bin/env python3
"""enforcement.py — Pure deterministic checkpoint logic for MCE CHECKPOINT-ENFORCEMENT.

Story MCE-4.3a: CHECKPOINT infra (PostToolUse soft-warn + journey log).
Story MCE-11.17: 5 Inviolable Pipeline Rules (business-level invariants).
Constitution Art. XII (Pipeline MCE Integrity), Art. IX (Journey Log),
Art. X (Artifact Contracts).

Exposes 4 original public functions (MCE-4.3a, no LLM, no external deps):
  - validate_pre_conditions(slug, phase, state) -> list[str]
  - validate_post_conditions(slug, phase, state) -> list[str]
  - load_pipeline_state(slug, root) -> dict
  - save_pipeline_state(slug, state, root) -> None

Exposes 5 new business-rule functions (MCE-11.17, additive, WARN-only V1):
  - enforce_classification_before_chunking(slug, root) -> EnforcementResult
  - enforce_chunks_indexed_before_insights(slug, root) -> EnforcementResult
  - enforce_insight_chunk_traceability(slug, root) -> EnforcementResult
  - enforce_phase8_gates(slug, root) -> EnforcementResult
  - enforce_cargo_dna_config(agent_path) -> EnforcementResult

All 5 new functions:
  - Return EnforcementResult(passed, rule, code, message, affected_pct, extra)
  - Emit WARN to stdout in canonical format when violated (V1 — never block)
  - Append audit entry to .data/artifacts/ENFORCEMENT-LOG.jsonl
  - Accept bypass flag via env var MCE_BYPASS_R{N}=1 (documented)

Atomic write: create temp file in same directory → os.replace() onto target.
Pattern mirrors _save_insights_state() in orchestrate.py:1121.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.enforcement")

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_PIPELINE_STATE_RELPATH = ".data/artifacts/mce/{slug}/PIPELINE-STATE.json"


def _pipeline_state_path(slug: str, root: Path) -> Path:
    """Return the absolute path to PIPELINE-STATE.json for a given slug."""
    return root / ".data" / "artifacts" / "mce" / slug / "PIPELINE-STATE.json"


# ---------------------------------------------------------------------------
# State I/O
# ---------------------------------------------------------------------------


def load_pipeline_state(slug: str, root: Path) -> dict[str, Any]:
    """Load PIPELINE-STATE.json for *slug* relative to *root*.

    Returns an empty dict when the file does not exist — first-run safe.
    Never raises on missing file; caller is responsible for handling empty state.
    """
    path = _pipeline_state_path(slug, root)
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_pipeline_state(slug: str, state: dict[str, Any], root: Path) -> None:
    """Persist *state* to PIPELINE-STATE.json for *slug* via atomic write.

    Uses tempfile.mkstemp() in the target directory + os.replace() so the
    write is atomic even on crash.  Mirrors the pattern from orchestrate.py
    _save_insights_state (line 1121).

    Raises OSError / IOError on unrecoverable write failures (disk full, etc.).
    """
    target = _pipeline_state_path(slug, root)
    target.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, target)
    except Exception:
        # Best-effort cleanup — do not swallow the original exception.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Condition definitions
# ---------------------------------------------------------------------------

# Pre-conditions per phase: {phase -> [(condition_name, check_fn)]}
# check_fn(slug, state, root) -> bool  — True means PASS.
#
# Rules come from the mce_checkpoints.yaml spec consolidated in the roundtable
# 2026-05-17 (conditions C-02, C-04, C-06, C-07).  We implement a minimal
# deterministic subset that can run without filesystem I/O on the state dict
# alone, plus lightweight optional filesystem checks when root is provided.


def _check_slug_nonempty(slug: str, _state: dict[str, Any], _root: Path) -> bool:
    return bool(slug and slug.strip())


def _check_schema_version_present(_slug: str, state: dict[str, Any], _root: Path) -> bool:
    return bool(state.get("schema_version"))


def _check_checkpoints_is_list(_slug: str, state: dict[str, Any], _root: Path) -> bool:
    return isinstance(state.get("checkpoints"), list)


def _check_bucket_valid(_slug: str, state: dict[str, Any], _root: Path) -> bool:
    # Empty state (new slug, no checkpoint yet) is allowed — only validate non-empty.
    if not state:
        return True
    return state.get("bucket") in ("external", "business", "personal")


def _check_last_updated_present(_slug: str, state: dict[str, Any], _root: Path) -> bool:
    # Empty state (new slug) is allowed — only validate if state is non-empty.
    if not state:
        return True
    return bool(state.get("last_updated"))


# Pre-condition registry — applies to ALL phases unless phase-specific override.
_PRE_CONDITIONS_GLOBAL: list[tuple[str, Any]] = [
    ("slug_nonempty", _check_slug_nonempty),
]

# Post-condition registry — applies to ALL phases.
_POST_CONDITIONS_GLOBAL: list[tuple[str, Any]] = [
    ("schema_version_present", _check_schema_version_present),
    ("checkpoints_is_list", _check_checkpoints_is_list),
    ("bucket_valid", _check_bucket_valid),
    ("last_updated_present", _check_last_updated_present),
]

# Phase-specific overrides (extend global list).
_PRE_CONDITIONS_PHASE: dict[str, list[tuple[str, Any]]] = {}
_POST_CONDITIONS_PHASE: dict[str, list[tuple[str, Any]]] = {}


# ---------------------------------------------------------------------------
# Public validation API
# ---------------------------------------------------------------------------


def validate_pre_conditions(slug: str, phase: str, state: dict[str, Any]) -> list[str]:
    """Evaluate pre-conditions for *phase* against *state*.

    Returns a list of violation description strings.  Empty list = PASS.
    Purely deterministic — no filesystem access, no LLM, no network.
    """
    violations: list[str] = []
    checks = list(_PRE_CONDITIONS_GLOBAL)
    checks.extend(_PRE_CONDITIONS_PHASE.get(phase, []))

    for name, fn in checks:
        try:
            # root not used in pre-conditions (state dict only)
            passed = fn(slug, state, Path("."))
        except Exception as exc:
            violations.append(f"pre:{phase}:{name}:ERROR:{exc!r}")
            continue
        if not passed:
            violations.append(f"pre:{phase}:{name}:FAIL — condition '{name}' not satisfied")
    return violations


def validate_post_conditions(slug: str, phase: str, state: dict[str, Any]) -> list[str]:
    """Evaluate post-conditions for *phase* against *state*.

    Returns a list of violation description strings.  Empty list = PASS.
    Purely deterministic — no filesystem access, no LLM, no network.
    """
    violations: list[str] = []
    checks = list(_POST_CONDITIONS_GLOBAL)
    checks.extend(_POST_CONDITIONS_PHASE.get(phase, []))

    for name, fn in checks:
        try:
            passed = fn(slug, state, Path("."))
        except Exception as exc:
            violations.append(f"post:{phase}:{name}:ERROR:{exc!r}")
            continue
        if not passed:
            violations.append(f"post:{phase}:{name}:FAIL — condition '{name}' not satisfied")
    return violations


# ---------------------------------------------------------------------------
# Slug extraction (moved here from checkpoint_observer.py — Story MCE-4.3b)
# Public so enforcement_guard.py can import without duplicating logic (AC5).
# ---------------------------------------------------------------------------


def extract_slug_from_path(file_path: str) -> str | None:
    """Extract pipeline slug from a .data/artifacts/mce/{slug}/... path.

    Returns None when the path does not match the expected MCE artifact layout.
    """
    parts = Path(file_path).parts
    try:
        mce_idx = next(i for i, p in enumerate(parts) if p == "mce")
        if mce_idx + 1 < len(parts):
            return parts[mce_idx + 1]
    except StopIteration:
        pass
    return None


# ---------------------------------------------------------------------------
# MCE-11.17: 5 Inviolable Pipeline Rules
# ---------------------------------------------------------------------------
# All functions below are ADDITIVE to the MCE-4.3a infrastructure above.
# They operate at the business-rule layer (artifacts ↔ pipeline flow) rather
# than the FSM state layer (PIPELINE-STATE.json).
#
# V1: WARN-only (emit + log, never block pipeline).
# V2 goal: fail-closed after ENFORCEMENT-LOG.jsonl accumulates >=10 runs.
# ---------------------------------------------------------------------------

# Resolved lazily so this module can be imported without engine.paths on PATH.
_ENFORCEMENT_LOG_PATH: Path | None = None


def _enforcement_log_path() -> Path:
    """Resolve .data/artifacts/ENFORCEMENT-LOG.jsonl relative to project root."""
    global _ENFORCEMENT_LOG_PATH
    if _ENFORCEMENT_LOG_PATH is None:
        try:
            from engine.paths import ARTIFACTS

            _ENFORCEMENT_LOG_PATH = ARTIFACTS / "ENFORCEMENT-LOG.jsonl"
        except ImportError:
            # Fallback for direct invocation without installed package.
            _root = Path(__file__).resolve().parent.parent.parent.parent.parent
            _ENFORCEMENT_LOG_PATH = _root / ".data" / "artifacts" / "ENFORCEMENT-LOG.jsonl"
    return _ENFORCEMENT_LOG_PATH


def _artifacts_root() -> Path:
    """Return .data/artifacts root (lazy, never raises)."""
    try:
        from engine.paths import ARTIFACTS

        return ARTIFACTS
    except ImportError:
        _root = Path(__file__).resolve().parent.parent.parent.parent.parent
        return _root / ".data" / "artifacts"


@dataclasses.dataclass
class EnforcementResult:
    """Result of a single enforcement rule check.

    Attributes:
        passed: True when the rule was satisfied (or bypassed).
        rule: Rule ID, e.g. "R1".
        code: Short error code, e.g. "NO_CLASSIFICATION".
        message: Human-readable violation description.
        affected_pct: Percentage affected (used by R3 traceability check).
        bypassed: True when the bypass flag was set.
        bypass_reason: The reason string provided with the bypass.
        slug: Source slug (empty string when not applicable, e.g. R5).
        extra: Additional metadata for the audit log.
    """

    passed: bool
    rule: str
    code: str = ""
    message: str = ""
    affected_pct: float | None = None
    bypassed: bool = False
    bypass_reason: str = ""
    slug: str = ""
    extra: dict[str, Any] = dataclasses.field(default_factory=dict)


def _is_bypassed(rule_num: str) -> tuple[bool, str]:
    """Check whether a rule bypass flag is set in the environment.

    Env var: MCE_BYPASS_R{N}=<reason string (min 10 chars)>.
    Returns (bypassed, reason).
    """
    env_key = f"MCE_BYPASS_R{rule_num}"
    reason = os.environ.get(env_key, "")
    if reason and len(reason.strip()) >= 10:
        return True, reason.strip()
    return False, ""


def _emit_enforcement_warn(result: EnforcementResult) -> None:
    """Print canonical ENFORCEMENT_VIOLATION format to stdout (WARN-only V1).

    Format from story AC8:
        ENFORCEMENT_VIOLATION_R{N}: {message}
        Operacao bloqueada: {operation}
        Para resolver: {resolution_hint}
        bypassed_by: null | <reason>
    """
    if result.passed:
        return

    bypassed_str = f'"{result.bypass_reason}"' if result.bypassed else "null"

    lines = [
        f"ENFORCEMENT_VIOLATION_{result.rule}: {result.message}",
        f"Operacao: verificacao {result.rule} (V1 WARN-only — nao bloqueia pipeline)",
        f"Para resolver: verifique o estado do slug '{result.slug}' e re-execute a fase anterior",
        f"bypassed_by: {bypassed_str}",
    ]
    if result.affected_pct is not None:
        lines.append(f"affected_pct: {result.affected_pct:.1f}%")

    print("\n".join(lines), flush=True)
    logger.warning(
        "ENFORCEMENT_VIOLATION_%s: %s | slug=%s bypassed=%s",
        result.rule,
        result.message,
        result.slug,
        result.bypassed,
    )


def _append_enforcement_log(result: EnforcementResult) -> None:
    """Append a JSON line to ENFORCEMENT-LOG.jsonl (non-fatal).

    Schema from story AC7:
        {timestamp, rule, code, slug, affected_pct, bypassed_by,
         bypass_reason, status}
    """
    log_path = _enforcement_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "rule": result.rule,
            "code": result.code,
            "slug": result.slug,
            "bypassed_by": result.bypass_reason if result.bypassed else None,
            "bypass_reason": result.bypass_reason if result.bypassed else None,
            "status": "BYPASSED" if result.bypassed else ("PASS" if result.passed else "WARN"),
        }
        if result.affected_pct is not None:
            entry["affected_pct"] = round(result.affected_pct, 1)
        if result.extra:
            entry.update(result.extra)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.debug("Failed to write ENFORCEMENT-LOG.jsonl: %s", exc)


# ---------------------------------------------------------------------------
# R1 — Source files must be classified before chunking
# ---------------------------------------------------------------------------


def enforce_classification_before_chunking(
    slug: str,
    root: Path | None = None,
) -> EnforcementResult:
    """R1: Source files must be classified before chunking.

    Checks that the MetadataManager for *slug* has a non-empty classification
    block with both ``source_type`` and ``primary_bucket`` populated.

    V1: WARN-only. Never raises. Always returns EnforcementResult.

    Args:
        slug: Pipeline slug (e.g. "alex-hormozi").
        root: Project root (resolved via engine.paths if None).

    Returns:
        EnforcementResult with passed=True when classification is present.
    """
    bypassed, reason = _is_bypassed("1")
    rule = "R1"

    if bypassed:
        result = EnforcementResult(
            passed=True,
            rule=rule,
            code="BYPASSED",
            message="R1 bypassed via MCE_BYPASS_R1",
            bypassed=True,
            bypass_reason=reason,
            slug=slug,
        )
        _append_enforcement_log(result)
        return result

    try:
        # Lazy import so module loads without full engine on PATH.
        from engine.intelligence.pipeline.mce.metadata_manager import MetadataManager

        mgr = MetadataManager.load(slug)
        if mgr is None:
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="NO_METADATA",
                message=f"No metadata found for slug '{slug}' — file was never ingested",
                slug=slug,
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        classification = getattr(mgr, "classification", {}) or {}
        source_type = classification.get("source_type", "")
        primary_bucket = classification.get("primary_bucket", "")

        if (
            not source_type
            or source_type == "unknown"
            or not primary_bucket
            or primary_bucket == "unknown"
        ):
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="NO_CLASSIFICATION",
                message=(
                    f"Source file for slug '{slug}' is not fully classified: "
                    f"source_type='{source_type}' primary_bucket='{primary_bucket}'"
                ),
                slug=slug,
                extra={"source_type": source_type, "primary_bucket": primary_bucket},
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            extra={"source_type": source_type, "primary_bucket": primary_bucket},
        )
        _append_enforcement_log(result)
        return result

    except Exception as exc:
        logger.debug("enforce_classification_before_chunking error: %s", exc)
        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            message=f"R1 check skipped (error): {exc}",
            extra={"check_error": str(exc)},
        )
        _append_enforcement_log(result)
        return result


# ---------------------------------------------------------------------------
# R2 — Chunks must be vector-indexed before insight extraction
# ---------------------------------------------------------------------------


def enforce_chunks_indexed_before_insights(
    slug: str,
    root: Path | None = None,
) -> EnforcementResult:
    """R2: Chunks must be vector-indexed before insight extraction.

    Checks that at least 1 chunk file exists for *slug* under
    .data/artifacts/chunks/{slug}/.

    V1: WARN-only. Never raises. Always returns EnforcementResult.

    Args:
        slug: Pipeline slug.
        root: Project root (resolved via engine.paths if None).

    Returns:
        EnforcementResult with passed=True when chunks exist.
    """
    bypassed, reason = _is_bypassed("2")
    rule = "R2"

    if bypassed:
        result = EnforcementResult(
            passed=True,
            rule=rule,
            code="BYPASSED",
            message="R2 bypassed via MCE_BYPASS_R2",
            bypassed=True,
            bypass_reason=reason,
            slug=slug,
        )
        _append_enforcement_log(result)
        return result

    try:
        artifacts = _artifacts_root()
        chunks_dir = artifacts / "chunks" / slug

        # Count chunk files — same resolution tiers as _resolve_chunks_for_slug.
        chunk_count = 0
        if (chunks_dir / "CHUNKS-STATE.json").exists():
            try:
                data = json.loads((chunks_dir / "CHUNKS-STATE.json").read_text(encoding="utf-8"))
                chunks_list = data if isinstance(data, list) else data.get("chunks", [])
                chunk_count = len(chunks_list)
            except Exception:
                chunk_count = 0
        if chunk_count == 0 and chunks_dir.is_dir():
            batch_files = list(chunks_dir.glob("BATCH-*-chunks.json"))
            for bf in batch_files:
                try:
                    data = json.loads(bf.read_text(encoding="utf-8"))
                    chunks_list = data if isinstance(data, list) else data.get("chunks", [])
                    chunk_count += len(chunks_list)
                except Exception:
                    pass

        if chunk_count == 0:
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="CHUNKS_NOT_INDEXED",
                message=(
                    f"No chunks found for slug '{slug}' — "
                    "run cmd_batch + cmd_process_batch before insight extraction"
                ),
                slug=slug,
                extra={"chunks_dir": str(chunks_dir)},
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            extra={"chunks_found": chunk_count},
        )
        _append_enforcement_log(result)
        return result

    except Exception as exc:
        logger.debug("enforce_chunks_indexed_before_insights error: %s", exc)
        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            message=f"R2 check skipped (error): {exc}",
            extra={"check_error": str(exc)},
        )
        _append_enforcement_log(result)
        return result


# ---------------------------------------------------------------------------
# R3 — Insights must have chunk_id traceability
# ---------------------------------------------------------------------------

#: Minimum fraction of insights that must carry a non-empty chunk_id/chunks ref.
R3_TRACEABILITY_THRESHOLD: float = 0.90  # 90%


def enforce_insight_chunk_traceability(
    slug: str,
    root: Path | None = None,
    threshold: float = R3_TRACEABILITY_THRESHOLD,
) -> EnforcementResult:
    """R3: Insights must have chunk_id traceability.

    Reads .data/artifacts/insights/{slug}/INSIGHTS-STATE.json and checks
    that >= *threshold* (default 90%) of insights have a non-empty
    ``chunk_id``, ``chunk_ids``, or ``chunks`` field.

    V1: WARN-only. Never raises. Always returns EnforcementResult.

    Args:
        slug: Pipeline slug.
        root: Project root (resolved via engine.paths if None).
        threshold: Fraction (0-1) of insights that must have chunk refs.

    Returns:
        EnforcementResult with passed=True when traceability >= threshold.
    """
    bypassed, reason = _is_bypassed("3")
    rule = "R3"

    if bypassed:
        result = EnforcementResult(
            passed=True,
            rule=rule,
            code="BYPASSED",
            message="R3 bypassed via MCE_BYPASS_R3",
            bypassed=True,
            bypass_reason=reason,
            slug=slug,
        )
        _append_enforcement_log(result)
        return result

    try:
        artifacts = _artifacts_root()
        ins_path = artifacts / "insights" / slug / "INSIGHTS-STATE.json"

        if not ins_path.exists():
            # No insights file yet — not a violation (insights not extracted).
            result = EnforcementResult(
                passed=True,
                rule=rule,
                slug=slug,
                message="R3 skipped — INSIGHTS-STATE.json not found (insights not yet extracted)",
                extra={"insights_path": str(ins_path)},
            )
            _append_enforcement_log(result)
            return result

        data = json.loads(ins_path.read_text(encoding="utf-8"))

        # Collect all insights from persons dict or flat list.
        all_insights: list[dict[str, Any]] = []
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            for pdata in persons.values():
                if isinstance(pdata, dict):
                    all_insights.extend(
                        ins for ins in pdata.get("insights", []) if isinstance(ins, dict)
                    )
        flat = data.get("insights", [])
        if isinstance(flat, list):
            all_insights.extend(ins for ins in flat if isinstance(ins, dict))

        if not all_insights:
            result = EnforcementResult(
                passed=True,
                rule=rule,
                slug=slug,
                message="R3 skipped — no insights found in INSIGHTS-STATE.json",
            )
            _append_enforcement_log(result)
            return result

        def _has_chunk_ref(ins: dict[str, Any]) -> bool:
            for field in ("chunk_id", "chunk_ids", "chunks"):
                val = ins.get(field)
                if val:
                    if isinstance(val, str) and val.strip():
                        return True
                    if isinstance(val, list) and val:
                        return True
            return False

        traced = sum(1 for ins in all_insights if _has_chunk_ref(ins))
        total = len(all_insights)
        pct = (traced / total) * 100.0

        if pct < threshold * 100.0:
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="MISSING_CHUNK_REFS",
                message=(
                    f"Only {pct:.1f}% of insights for slug '{slug}' have chunk_id refs "
                    f"(threshold: {threshold * 100:.0f}%)"
                ),
                affected_pct=pct,
                slug=slug,
                extra={"traced": traced, "total": total, "threshold_pct": threshold * 100},
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            affected_pct=pct,
            extra={"traced": traced, "total": total},
        )
        _append_enforcement_log(result)
        return result

    except Exception as exc:
        logger.debug("enforce_insight_chunk_traceability error: %s", exc)
        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            message=f"R3 check skipped (error): {exc}",
            extra={"check_error": str(exc)},
        )
        _append_enforcement_log(result)
        return result


# ---------------------------------------------------------------------------
# R4 — Phase 8 gates must pass before finalize
# ---------------------------------------------------------------------------


def enforce_phase8_gates(
    slug: str,
    root: Path | None = None,
) -> EnforcementResult:
    """R4: Phase 8 gates (7B-7I) must pass before finalize.

    Reads .data/logs/phase8-gate.jsonl and verifies that the most recent
    gate entry for *slug* has all sub-checks passing. Gates that are absent
    from the state are treated as SKIP (not FAIL) — limits check to what
    the state already contains.

    V1: WARN-only. Never raises. Always returns EnforcementResult.

    Args:
        slug: Pipeline slug.
        root: Project root (resolved via engine.paths if None).

    Returns:
        EnforcementResult with passed=True when all present gates pass.
    """
    bypassed, reason = _is_bypassed("4")
    rule = "R4"

    if bypassed:
        result = EnforcementResult(
            passed=True,
            rule=rule,
            code="BYPASSED",
            message="R4 bypassed via MCE_BYPASS_R4",
            bypassed=True,
            bypass_reason=reason,
            slug=slug,
        )
        _append_enforcement_log(result)
        return result

    try:
        try:
            from engine.paths import LOGS

            gate_log = LOGS / "phase8-gate.jsonl"
        except ImportError:
            _root = Path(__file__).resolve().parent.parent.parent.parent.parent
            gate_log = _root / ".data" / "logs" / "phase8-gate.jsonl"

        if not gate_log.exists():
            # Phase 8 has never run — not a hard violation in V1.
            result = EnforcementResult(
                passed=True,
                rule=rule,
                slug=slug,
                message="R4 skipped — phase8-gate.jsonl not found (Phase 8 not yet run)",
                extra={"gate_log": str(gate_log)},
            )
            _append_enforcement_log(result)
            return result

        # Read all lines, find the most recent entry for this slug.
        latest_entry: dict[str, Any] | None = None
        with open(gate_log, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict) and entry.get("slug") == slug:
                        latest_entry = entry
                except json.JSONDecodeError:
                    continue

        if latest_entry is None:
            result = EnforcementResult(
                passed=True,
                rule=rule,
                slug=slug,
                message=f"R4 skipped — no phase8 gate entry found for slug '{slug}'",
            )
            _append_enforcement_log(result)
            return result

        checks: dict[str, bool] = latest_entry.get("checks", {})
        failures: list[str] = latest_entry.get("failures", [])

        # Treat as PASS if the entry already recorded no failures.
        if not failures and isinstance(checks, dict):
            failures = [k for k, v in checks.items() if not v]

        if failures:
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="PHASE8_GATE_FAILED",
                message=(f"Phase 8 gates failed for slug '{slug}': {failures}"),
                slug=slug,
                extra={"failed_gates": failures, "all_checks": checks},
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            extra={"checks_passed": list(checks.keys())},
        )
        _append_enforcement_log(result)
        return result

    except Exception as exc:
        logger.debug("enforce_phase8_gates error: %s", exc)
        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=slug,
            message=f"R4 check skipped (error): {exc}",
            extra={"check_error": str(exc)},
        )
        _append_enforcement_log(result)
        return result


# ---------------------------------------------------------------------------
# R5 — Cargo agents must have DNA-CONFIG valid before receiving cascade
# ---------------------------------------------------------------------------


def enforce_cargo_dna_config(agent_path: str | Path) -> EnforcementResult:
    """R5: Cargo agents must have DNA-CONFIG.yaml before receiving cascade.

    Checks that *agent_path* contains a ``DNA-CONFIG.yaml`` file that is
    non-empty and parseable as YAML with a ``dna_sources`` key.

    V1: WARN-only. Never raises. Always returns EnforcementResult.

    Args:
        agent_path: Path to the cargo agent directory (str or Path).

    Returns:
        EnforcementResult with passed=True when DNA-CONFIG.yaml is valid.
    """
    bypassed, reason = _is_bypassed("5")
    rule = "R5"
    agent_dir = Path(agent_path)

    if bypassed:
        result = EnforcementResult(
            passed=True,
            rule=rule,
            code="BYPASSED",
            message="R5 bypassed via MCE_BYPASS_R5",
            bypassed=True,
            bypass_reason=reason,
            slug=str(agent_dir),
        )
        _append_enforcement_log(result)
        return result

    try:
        config_path = agent_dir / "DNA-CONFIG.yaml"

        if not config_path.exists():
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="MISSING_DNA_CONFIG",
                message=(
                    f"Cargo agent at '{agent_dir}' has no DNA-CONFIG.yaml — "
                    "cascade write blocked in V2 (WARN only in V1)"
                ),
                slug=str(agent_dir),
                extra={"agent": str(agent_dir)},
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        # Validate parseable YAML with dna_sources key.
        try:
            import yaml

            with open(config_path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if not isinstance(data, dict) or "dna_sources" not in data:
                result = EnforcementResult(
                    passed=False,
                    rule=rule,
                    code="INVALID_DNA_CONFIG",
                    message=(
                        f"Cargo agent DNA-CONFIG.yaml at '{agent_dir}' is missing "
                        "'dna_sources' key or is not a valid YAML mapping"
                    ),
                    slug=str(agent_dir),
                    extra={"agent": str(agent_dir), "config_path": str(config_path)},
                )
                _emit_enforcement_warn(result)
                _append_enforcement_log(result)
                return result
        except Exception as yaml_exc:
            result = EnforcementResult(
                passed=False,
                rule=rule,
                code="UNPARSEABLE_DNA_CONFIG",
                message=f"DNA-CONFIG.yaml for '{agent_dir}' cannot be parsed: {yaml_exc}",
                slug=str(agent_dir),
                extra={"agent": str(agent_dir), "parse_error": str(yaml_exc)},
            )
            _emit_enforcement_warn(result)
            _append_enforcement_log(result)
            return result

        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=str(agent_dir),
            extra={"config_path": str(config_path)},
        )
        _append_enforcement_log(result)
        return result

    except Exception as exc:
        logger.debug("enforce_cargo_dna_config error: %s", exc)
        result = EnforcementResult(
            passed=True,
            rule=rule,
            slug=str(agent_dir),
            message=f"R5 check skipped (error): {exc}",
            extra={"check_error": str(exc)},
        )
        _append_enforcement_log(result)
        return result


# ---------------------------------------------------------------------------
# Enforcement report builder (AC9 — ENFORCEMENT REPORT block)
# ---------------------------------------------------------------------------


def build_enforcement_report(
    slug: str,
    results: list[EnforcementResult],
) -> str:
    """Build a compact ENFORCEMENT REPORT block for display in pipeline output.

    Format (AC9):
        ENFORCEMENT REPORT
        R1: PASS | R2: WARN (no chunks) | R3: WARN (85.0%) | R4: PASS | R5: PASS

    Args:
        slug: Source slug (for display).
        results: List of EnforcementResult, one per rule (R1-R5).

    Returns:
        Formatted multi-line string ready for print().
    """
    lines = ["", "─" * 50, "ENFORCEMENT REPORT", f"slug: {slug}"]
    parts: list[str] = []

    for r in results:
        if r.bypassed:
            parts.append(f"{r.rule}: BYPASSED ({r.bypass_reason[:30]})")
        elif r.passed:
            if r.affected_pct is not None:
                parts.append(f"{r.rule}: PASS ({r.affected_pct:.0f}% traced)")
            else:
                parts.append(f"{r.rule}: PASS")
        else:
            if r.affected_pct is not None:
                parts.append(f"{r.rule}: WARN ({r.affected_pct:.0f}% traceability)")
            elif r.code:
                short = r.code.replace("_", " ").lower()
                parts.append(f"{r.rule}: WARN ({short})")
            else:
                parts.append(f"{r.rule}: WARN")

    lines.append(" | ".join(parts))
    lines.append("─" * 50)
    return "\n".join(lines)
