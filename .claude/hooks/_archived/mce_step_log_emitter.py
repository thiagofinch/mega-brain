# ARCHIVED 2026-04-16 — W3-001.6
# Logic consolidated into .claude/hooks/mce_step_logger.py
# Not referenced in settings.json

"""
mce_step_log_emitter.py -- PostToolUse Hook for Real-time Step Logs
====================================================================

Fires after every tool use. Detects if an MCE pipeline step or microstep
just completed and renders the Chronicler ASCII block to stdout.

Detection priority:
  1. Step result file written:
     .claude/mission-control/mce/{slug}/step_results/step_NN_result.json
     → Load StepResult from JSON, render immediately.

  2. Bash command pattern (deterministic steps):
     "orchestrate ingest|batch|finalize" → detect step 1/2/11

  3. Artifact write pattern (LLM steps):
     Write to CHUNKS-STATE.json → step 3
     Write to CANONICAL-MAP.json → step 4
     Write to INSIGHTS-STATE.json → step 5/6/7 (distinguished by content)
     Write to VOICE-DNA.yaml → step 8
     Write to dossiers/ or agents/ → step 10

  4. Pipeline manifest watcher:
     Any write to mce_checkpoints.yaml, mce-workflow-rules.yaml,
     SKILL.md → trigger pipeline_manifest_builder.build_manifest()

This hook is NON-FATAL — any exception is silently logged.
Never blocks Claude Code execution.

Version: 1.0.0
Date: 2026-03-28
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("hooks.mce_step_log_emitter")

# ── Safe imports ─────────────────────────────────────────────────────────────
_IMPORTS_OK = False
try:
    from engine.intelligence.pipeline.mce.chronicler_data_collector import (
        resolve_person_name,
        resolve_slug_from_path,
    )
    from engine.intelligence.pipeline.mce.pipeline_manifest_builder import (
        build_manifest,
        manifest_loader,
    )
    from engine.intelligence.pipeline.mce.step_log_renderer import (
        render_briefing,
        render_step_block,
    )
    from engine.intelligence.pipeline.mce.step_result import (
        BucketMetrics,
        StepAlert,
        StepImpact,
        StepOutput,
        StepResult,
    )
    from engine.paths import ARTIFACTS, KNOWLEDGE_EXTERNAL, LOGS, MISSION_CONTROL, ROOT

    _IMPORTS_OK = True
except Exception as _ie:
    pass  # Hook silent-fails if imports broken

# ── Truth source paths (for manifest watcher) ────────────────────────────────
_TRUTH_SOURCES = [
    "mce_checkpoints.yaml",
    "mce-workflow-rules.yaml",
    "SKILL.md",
    "state_machine.py",
]


# ── Step result dir ──────────────────────────────────────────────────────────
def _step_result_dir(slug: str) -> Path:
    return MISSION_CONTROL / "mce" / slug / "step_results"


# ═══════════════════════════════════════════════════════════════════════════════
# MANIFEST WATCHER — rebuild when truth sources change
# ═══════════════════════════════════════════════════════════════════════════════


def _check_manifest_rebuild(path_str: str) -> bool:
    """Return True if the written file is a truth source and manifest was rebuilt."""
    if not _IMPORTS_OK:
        return False
    p = Path(path_str)
    if p.name in _TRUTH_SOURCES:
        try:
            build_manifest(force=True)
            logger.info("PIPELINE-MANIFEST.json rebuilt (truth source changed: %s)", p.name)
            return True
        except Exception as exc:
            logger.debug("Manifest rebuild failed: %s", exc)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# STEP RESULT LOADER — primary detection
# ═══════════════════════════════════════════════════════════════════════════════


def _try_load_step_result(path_str: str, slug: str) -> StepResult | None:
    """
    If the written file is a step_result JSON, load and return StepResult.
    Pattern: .claude/mission-control/mce/{slug}/step_results/step_NN_result.json
    """
    if not _IMPORTS_OK:
        return None
    try:
        p = Path(path_str)
        if "step_results" not in str(p):
            return None
        if not p.name.startswith("step_") or not p.name.endswith("_result.json"):
            return None

        data = json.loads(p.read_text(encoding="utf-8"))
        # Reconstruct StepResult from JSON
        result = StepResult(
            step_id=data.get("step_id", 0),
            slug=data.get("slug", slug),
            status=data.get("status", "COMPLETE"),
            step_name=data.get("step_name", ""),
            step_type=data.get("step_type", ""),
            squad=data.get("squad", ""),
            microstep_id=data.get("microstep_id"),
            microstep_name=data.get("microstep_name"),
            duration_seconds=data.get("duration_seconds", 0.0),
            timestamp=data.get("timestamp", ""),
            metrics=data.get("metrics", {}),
            bucket=data.get("bucket", "external"),
            quality_score=data.get("quality_score"),
            quality_roi=data.get("quality_roi", 0.0),
            chronicler_note=data.get("chronicler_note", ""),
            integrity_pct=data.get("integrity_pct", 100.0),
            digest_error=data.get("digest_error", False),
            digest_error_detail=data.get("digest_error_detail", ""),
        )

        # Reconstruct sub-objects
        for out_d in data.get("outputs", []):
            result.outputs.append(
                StepOutput(
                    label=out_d.get("label", ""),
                    value=out_d.get("value", ""),
                    output_type=out_d.get("output_type", "artifact"),
                    highlight=out_d.get("highlight", False),
                    chunk_ids=out_d.get("chunk_ids", []),
                )
            )
        for imp_d in data.get("impacts", []):
            result.impacts.append(
                StepImpact(
                    target=imp_d.get("target", ""),
                    count=imp_d.get("count", 0),
                    impact_type=imp_d.get("impact_type", ""),
                    bucket=imp_d.get("bucket", ""),
                    is_cross_bucket=imp_d.get("is_cross_bucket", False),
                )
            )
        for al_d in data.get("alerts", []):
            result.alerts.append(
                StepAlert(
                    level=al_d.get("level", "info"),
                    category=al_d.get("category", "info"),
                    message=al_d.get("message", ""),
                    action_required=al_d.get("action_required", False),
                    reversible=al_d.get("reversible", True),
                    detail=al_d.get("detail", ""),
                )
            )

        # Bucket metrics
        for bkt_key, bkt_attr in [
            ("bucket_external", "bucket_external"),
            ("bucket_business", "bucket_business"),
            ("bucket_personal", "bucket_personal"),
        ]:
            bm = data.get(bkt_key, {})
            if bm:
                setattr(
                    result,
                    bkt_attr,
                    BucketMetrics(
                        files=bm.get("files", 0),
                        chunks=bm.get("chunks", 0),
                        insights=bm.get("insights", 0),
                        entities=bm.get("entities", 0),
                        is_primary=bm.get("is_primary", False),
                        confidence=bm.get("confidence", 0.0),
                    ),
                )

        result.bucket_intersections = data.get("bucket_intersections", [])

        return result

    except Exception as exc:
        logger.debug("_try_load_step_result failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK DETECTION — infer from tool name + path
# ═══════════════════════════════════════════════════════════════════════════════


def _detect_step_from_tool(tool_name: str, tool_input: dict) -> tuple[int, str, str | None]:
    """
    Fallback: detect step from tool name + path patterns.
    Returns (step_id, slug, microstep_id | None).
    Returns (-1, "", None) if not an MCE step.
    """
    if not _IMPORTS_OK:
        return -1, "", None

    # Bash tool — orchestrate commands
    if tool_name == "bash":
        cmd = tool_input.get("command", "")
        if "orchestrate" in cmd:
            if "ingest" in cmd:
                return 1, _slug_from_cmd(cmd), None
            if "batch" in cmd:
                return 2, _slug_from_cmd(cmd), None
            if "finalize" in cmd:
                return 11, _slug_from_cmd(cmd), None

    # Write tools — artifact patterns
    path_str = tool_input.get("path", "") or tool_input.get("file_path", "") or ""
    content = tool_input.get("new_str", "") or tool_input.get("content", "") or ""

    if not path_str:
        return -1, "", None

    slug = _slug_from_path(path_str)

    if "CHUNKS-STATE.json" in path_str:
        return 3, slug, None
    if "CANONICAL-MAP.json" in path_str:
        return 4, slug, None
    if "INSIGHTS-STATE.json" in path_str:
        if "behavioral_patterns" in content:
            return 6, slug, None
        if "value_hierarchy" in content:
            return 7, slug, None
        return 5, slug, None
    if "VOICE-DNA.yaml" in path_str:
        return 8, slug, None
    if "pipeline_state.yaml" in path_str and "approve" in content.lower():
        return 9, slug, None
    if "/dossiers/persons/" in path_str:
        return 10, slug, "10.1"
    if "/dna/persons/" in path_str and any(
        x in path_str for x in ["FILOSOFIAS", "HEURISTICAS", "FRAMEWORKS", "METODOLOGIAS"]
    ):
        return 10, slug, "10.3"
    if "/agents/" in path_str and "AGENT.md" in path_str:
        return 10, slug, "10.4"
    if path_str.startswith("logs/mce/") and "MCE-" in path_str:
        return 12, slug, None

    return -1, "", None


def _slug_from_cmd(cmd: str) -> str:
    parts = cmd.split()
    for i, p in enumerate(parts):
        if p in ("ingest", "batch", "finalize", "status", "full"):
            if i + 1 < len(parts):
                cand = parts[i + 1].strip("'\"")
                if "/" in cand:
                    return Path(cand).stem
                return cand
    return "unknown"


def _slug_from_path(path_str: str) -> str:
    try:
        skip = {
            "dna",
            "dossiers",
            "sources",
            "inbox",
            "chunks",
            "canonical",
            "insights",
            "persons",
            "themes",
            "artifacts",
            "knowledge",
            "external",
            "business",
            "personal",
            "agents",
            "logs",
            "mce",
            "step_results",
            "mission-control",
            ".claude",
        }
        parts = Path(path_str).parts
        for seg in reversed(parts):
            clean = seg.lower()
            for ext in (".json", ".yaml", ".md", ".txt"):
                clean = clean.replace(ext, "")
            if clean not in skip and len(clean) > 2 and not clean.startswith("step_"):
                return clean
    except Exception:
        pass
    return "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK RESULT BUILDER — minimal StepResult from filesystem
# ═══════════════════════════════════════════════════════════════════════════════


def _build_fallback_result(step_id: int, slug: str, microstep_id: str | None) -> StepResult:
    """Build a minimal StepResult by reading available artifacts."""
    result = StepResult(
        step_id=step_id,
        slug=slug,
        status="COMPLETE",
        microstep_id=microstep_id,
        timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    try:
        # Read metadata for bucket info
        meta_path = MISSION_CONTROL / "mce" / slug / "metadata.yaml"
        if meta_path.exists():
            import yaml

            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            result.bucket = meta.get("primary_bucket", "external").lower()
            conf = meta.get("classification_confidence", 0)
            if result.bucket == "external":
                result.bucket_external = BucketMetrics(confidence=conf * 100, is_primary=True)
            elif result.bucket == "business":
                result.bucket_business = BucketMetrics(confidence=conf * 100, is_primary=True)
            else:
                result.bucket_personal = BucketMetrics(confidence=conf * 100, is_primary=True)

        # Step-specific artifact reads
        if step_id == 3:
            cp = ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
            if cp.exists():
                data = json.loads(cp.read_text(encoding="utf-8"))
                chunks = data.get("chunks", [])
                result.metrics["chunks_created"] = len(chunks)
                result.bucket_external = BucketMetrics(
                    chunks=len(chunks),
                    files=len({c.get("meta", {}).get("source_id") for c in chunks}),
                    is_primary=True,
                )

        elif step_id in (5, 6, 7):
            ip = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
            if ip.exists():
                data = json.loads(ip.read_text(encoding="utf-8"))
                total = data.get("total_insights", 0)
                result.metrics["total_insights"] = total
                result.bucket_external = BucketMetrics(insights=total, is_primary=True)

    except Exception as exc:
        logger.debug("_build_fallback_result partial failure: %s", exc)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN HOOK ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """
    PostToolUse hook entry point.
    Claude Code passes payload via stdin as JSON:
    {
        "tool_name": "str",
        "tool_input": {...},
        "tool_output": "str",
        "session_id": "str"
    }
    """
    if not _IMPORTS_OK:
        return

    try:
        raw = sys.stdin.read().strip()
        if not raw:
            return

        payload = json.loads(raw)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {})

        # 0. Check if a truth source was modified → rebuild manifest
        path_str = tool_input.get("path", "") or tool_input.get("file_path", "") or ""
        if path_str:
            _check_manifest_rebuild(path_str)

        # 1. Try to load from step_result JSON (primary path)
        result = None
        if path_str and "step_results" in path_str:
            result = _try_load_step_result(path_str, _slug_from_path(path_str))

        # 2. Fallback: detect from tool patterns
        if result is None:
            step_id, slug, microstep_id = _detect_step_from_tool(tool_name, tool_input)
            if step_id < 0 or slug in ("unknown", ""):
                return  # Not an MCE step — skip
            result = _build_fallback_result(step_id, slug, microstep_id)

        # 3. Render and print
        block = render_step_block(result)
        print(block, flush=True)

        # 4. Log to step logger JSONL
        _append_step_log(result)

    except Exception as exc:
        logger.debug("mce_step_log_emitter failed: %s", exc)


def _append_step_log(result) -> None:
    """Append a compact JSONL entry for validate_mce_logs.py consumption."""
    try:
        log_path = LOGS / "mce-step-logger.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": result.timestamp or datetime.now(UTC).isoformat(),
            "slug": result.slug,
            "step": result.step_id,
            "microstep": result.microstep_id,
            "step_name": result.step_name,
            "status": result.status,
            "bucket": result.bucket,
            "quality_score": result.quality_score,
            "metrics": {k: v for k, v in result.metrics.items() if not isinstance(v, dict | list)},
        }
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
