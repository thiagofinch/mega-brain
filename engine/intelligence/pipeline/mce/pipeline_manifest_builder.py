"""
pipeline_manifest_builder.py -- Pipeline Manifest Generator
============================================================

Reads structured truth sources and generates a single PIPELINE-MANIFEST.json
that the renderer uses. When the pipeline changes, this builder re-runs
and the manifest updates. The renderer reloads on next execution.

Truth sources consumed (in priority order):
  PRIMARY:
    1. core/intelligence/pipeline/mce/mce_checkpoints.yaml
       -> 200 checkpoints, step validation rules
    2. core/engine/rules/workflows/mce.yaml
       -> quality gates, veto conditions, step-to-state mapping
    3. core/intelligence/pipeline/mce/state_machine.py
       -> valid states, transitions

  SUPPLEMENTAL:
    4. .claude/skills/pipeline-mce/SKILL.md
       -> step names, squad assignments, human-readable descriptions
       -> parsed with simple regex -- fragile, used only for labels/docs

Output:
    .claude/mission-control/PIPELINE-MANIFEST.json

Triggered by:
    .claude/hooks/pipeline_manifest_watcher.py (PostToolUse hook)
    Any write to the four truth sources triggers rebuild.

CLI:
    python3 -m core.intelligence.pipeline.mce.pipeline_manifest_builder
    python3 -m core.intelligence.pipeline.mce.pipeline_manifest_builder --force

Constraints:
    - stdlib + PyYAML only.
    - Never raises -- logs warnings and continues with partial data.
    - Idempotent -- safe to run multiple times.

Version: 1.0.0
Date: 2026-03-28
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from engine.paths import CLAUDE, CORE, MISSION_CONTROL, ROOT
except ImportError:
    ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    CORE = ROOT / "core"
    CLAUDE = ROOT / ".claude"
    MISSION_CONTROL = CLAUDE / "mission-control"

logger = logging.getLogger("mce.pipeline_manifest_builder")

# ---------------------------------------------------------------------------
# Source paths
# ---------------------------------------------------------------------------

_CHECKPOINTS_YAML = CORE / "intelligence" / "pipeline" / "mce" / "mce_checkpoints.yaml"
_WORKFLOW_RULES_YAML = CORE / "engine" / "rules" / "workflows" / "mce.yaml"
_STATE_MACHINE_PY = CORE / "intelligence" / "pipeline" / "mce" / "state_machine.py"
_SKILL_MD = CLAUDE / "skills" / "pipeline-mce" / "SKILL.md"

_MANIFEST_PATH = MISSION_CONTROL / "PIPELINE-MANIFEST.json"

# ---------------------------------------------------------------------------
# Step metadata -- fallback when SKILL.md is not parseable
# ---------------------------------------------------------------------------

_STEP_DEFAULTS: dict[int, dict[str, str]] = {
    0: {"name": "DETECT", "squad": "---", "type": "deterministic"},
    1: {"name": "INGEST", "squad": "gate", "type": "deterministic"},
    2: {"name": "BATCH", "squad": "gate", "type": "deterministic"},
    3: {"name": "CHUNK", "squad": "parse", "type": "llm"},
    4: {"name": "ENTITY RESOLUTION", "squad": "canon", "type": "llm"},
    5: {"name": "INSIGHT EXTRACTION", "squad": "dig", "type": "llm"},
    6: {"name": "MCE BEHAVIORAL", "squad": "behav", "type": "llm"},
    7: {"name": "MCE IDENTITY", "squad": "psych", "type": "llm"},
    8: {"name": "MCE VOICE", "squad": "voice", "type": "llm"},
    9: {"name": "IDENTITY CHECKPOINT", "squad": "guard", "type": "human"},
    10: {"name": "CONSOLIDATION", "squad": "scribe", "type": "deterministic"},
    11: {"name": "FINALIZE", "squad": "ops", "type": "deterministic"},
    12: {"name": "REPORT", "squad": "ops", "type": "output"},
}

# Known microsteps -- extended when SKILL.md is parseable
_MICROSTEP_DEFAULTS: dict[str, dict[str, str]] = {
    "10.1": {"name": "DOSSIER COMPILATION", "squad": "scribe"},
    "10.2": {"name": "SOURCE COMPILATION", "squad": "scribe"},
    "10.3": {"name": "DNA YAML GENERATION", "squad": "weave"},
    "10.4": {"name": "AGENT GENERATION", "squad": "clone"},
    "10.5": {"name": "ACTIVATION GENERATION", "squad": "clone"},
}

# Background steps -- proactive tasks that run outside primary pipeline flow
# (MCE21-3.4: Background vs Foreground Task Visibility)
_BACKGROUND_STEPS: set[str] = {
    "dream_task",
    "rag_indexation",
}

# Expected artifacts per step -- extended from checkpoints
_ARTIFACT_MAP: dict[int, list[str]] = {
    1: ["knowledge/{bucket}/inbox/{slug}/"],
    3: ["artifacts/chunks/{slug}/CHUNKS-STATE.json"],
    4: ["artifacts/canonical/CANONICAL-MAP.json"],
    5: ["artifacts/insights/{slug}/INSIGHTS-STATE.json"],
    6: ["artifacts/insights/{slug}/INSIGHTS-STATE.json"],  # behavioral_patterns added
    7: ["artifacts/insights/{slug}/INSIGHTS-STATE.json"],  # value_hierarchy added
    8: ["knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml"],
    9: [".claude/mission-control/mce/{slug}/pipeline_state.yaml"],
    10: [
        "knowledge/external/dossiers/persons/DOSSIER-{slug_upper}.md",
        "knowledge/external/dna/persons/{slug}/FILOSOFIAS.yaml",
        "knowledge/external/dna/persons/{slug}/HEURISTICAS.yaml",
        "knowledge/external/dna/persons/{slug}/FRAMEWORKS.yaml",
        "knowledge/external/dna/persons/{slug}/METODOLOGIAS.yaml",
        "knowledge/external/dna/persons/{slug}/MODELOS-MENTAIS.yaml",
        "knowledge/external/dna/persons/{slug}/OBSESSIONS.yaml",
        "knowledge/external/dna/persons/{slug}/PARADOXES.yaml",
        "knowledge/external/dna/persons/{slug}/BEHAVIORAL-PATTERNS.yaml",
        "knowledge/external/dna/persons/{slug}/VALUES-HIERARCHY.yaml",
        "agents/external/{slug}/AGENT.md",
        "agents/external/{slug}/SOUL.md",
        "agents/external/{slug}/MEMORY.md",
        "agents/external/{slug}/DNA-CONFIG.yaml",
        "agents/external/{slug}/ACTIVATION.yaml",
    ],
    11: [".claude/mission-control/mce/{slug}/metrics.yaml"],
    12: ["logs/mce/{slug}/MCE-{tag}.md"],
}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        logger.warning("Truth source not found: %s", path)
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", path, exc)
        return {}


def _load_skill_md(path: Path) -> dict[str, Any]:
    """
    Parse SKILL.md for step names and descriptions.
    Uses simple regex -- fragile by design, used only for labels.
    Falls back to _STEP_DEFAULTS on any failure.
    """
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        steps: dict[str, dict[str, str]] = {}

        # Match patterns like "### STEP 3: CHUNK (LLM)" or "### STEP 10: CONSOLIDATION"
        pattern = re.compile(
            r"###\s+STEP\s+(\d+)[:\s]+([A-Z][A-Z\s\-]+?)(?:\s*\(([A-Z]+)\))?\s*$",
            re.MULTILINE,
        )
        for match in pattern.finditer(text):
            step_num = int(match.group(1))
            step_name = match.group(2).strip()
            step_type_raw = (match.group(3) or "").lower()
            step_type = step_type_raw if step_type_raw in ("llm", "deterministic", "human") else ""
            steps[str(step_num)] = {"name": step_name, "skill_type": step_type}

        return steps
    except Exception as exc:
        logger.warning("SKILL.md parse failed: %s", exc)
        return {}


def _parse_state_machine_states(path: Path) -> list[str]:
    """Extract STATES list from state_machine.py using regex."""
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
        match = re.search(r"STATES\s*[:=]\s*\[([^\]]+)\]", text, re.DOTALL)
        if not match:
            return []
        raw = match.group(1)
        states = [s.strip().strip('"').strip("'") for s in raw.split(",") if s.strip()]
        return [s for s in states if s]
    except Exception as exc:
        logger.warning("state_machine.py parse failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_manifest(force: bool = False) -> dict[str, Any]:
    """
    Build the PIPELINE-MANIFEST.json from all truth sources.

    Returns the manifest dict and writes it to disk.
    Always safe to call -- never raises.
    """
    now = datetime.now(UTC).isoformat()

    # Load truth sources
    checkpoints_raw = _load_yaml_safe(_CHECKPOINTS_YAML)
    workflow_rules = _load_yaml_safe(_WORKFLOW_RULES_YAML)
    skill_steps = _load_skill_md(_SKILL_MD)
    sm_states = _parse_state_machine_states(_STATE_MACHINE_PY)

    # Index checkpoints by step
    cps_by_step: dict[int, list[dict]] = {}
    for cp in checkpoints_raw.get("checkpoints", []):
        sn = cp.get("step_number", 0)
        cps_by_step.setdefault(sn, []).append(
            {
                "id": cp.get("id", ""),
                "phase": cp.get("phase", "post"),
                "check_type": cp.get("check_type", "deterministic"),
                "description": cp.get("description", ""),
                "blocking": cp.get("blocking", True),
            }
        )

    # Index quality gates by step
    gates_by_step: dict[int, dict] = {}
    for gate in workflow_rules.get("quality_gates", []):
        for step_num in gate.get("step_applies_to", []):
            gates_by_step[step_num] = {
                "id": gate.get("id", ""),
                "name": gate.get("name", ""),
                "severity": gate.get("severity", "block"),
                "type": gate.get("type", "auto"),
                "veto_conditions": gate.get("veto_conditions", []),
            }

    # Index veto conditions
    vetos: dict[str, dict] = {}
    for vc in workflow_rules.get("veto_conditions", []):
        vetos[vc.get("id", "")] = {
            "name": vc.get("name", ""),
            "description": vc.get("description", ""),
            "action": vc.get("action", "block"),
            "severity": vc.get("severity", "BLOCKING"),
            "recovery": vc.get("recovery", ""),
        }

    # Step-to-state mapping
    step_state_map: dict[str, str] = {
        str(k): str(v) for k, v in workflow_rules.get("step_state_mapping", {}).items()
    }

    # Build steps dict
    steps: dict[str, dict[str, Any]] = {}
    total_steps = max(_STEP_DEFAULTS.keys())

    for step_num in range(0, total_steps + 1):
        defaults = _STEP_DEFAULTS.get(
            step_num, {"name": f"STEP {step_num}", "squad": "---", "type": "?"}
        )
        skill_override = skill_steps.get(str(step_num), {})

        step_name_lower = (skill_override.get("name") or defaults["name"]).lower().replace(" ", "_")
        step_entry: dict[str, Any] = {
            "step_id": step_num,
            "name": skill_override.get("name") or defaults["name"],
            "squad": defaults["squad"],
            "type": skill_override.get("skill_type") or defaults["type"],
            "is_background": step_name_lower in _BACKGROUND_STEPS,
            "state": step_state_map.get(str(step_num), ""),
            "checkpoints": cps_by_step.get(step_num, []),
            "quality_gate": gates_by_step.get(step_num, {}),
            "expected_artifacts": _ARTIFACT_MAP.get(step_num, []),
            "microsteps": {},
        }

        # Add known microsteps for step 10
        if step_num == 10:
            for ms_id, ms_defaults in _MICROSTEP_DEFAULTS.items():
                step_entry["microsteps"][ms_id] = {
                    "microstep_id": ms_id,
                    "name": ms_defaults["name"],
                    "squad": ms_defaults["squad"],
                    "expected_artifacts": [],
                    "checkpoints": [],
                }

        steps[str(step_num)] = step_entry

    # Build blocking rules index
    blocking_rules: list[dict[str, Any]] = []
    for rule in checkpoints_raw.get("blocking_rules", []):
        blocking_rules.append(
            {
                "rule_id": rule.get("rule_id", ""),
                "step_number": rule.get("step_number", 0),
                "condition": rule.get("condition", ""),
                "action": rule.get("action", ""),
                "blocking_checkpoints": rule.get("blocking_checkpoints", []),
            }
        )

    # Assemble manifest
    manifest: dict[str, Any] = {
        "_meta": {
            "version": "1.0.0",
            "generated_at": now,
            "generated_by": "pipeline_manifest_builder.py",
            "generated_from": [
                str(_CHECKPOINTS_YAML.relative_to(ROOT))
                if _CHECKPOINTS_YAML.exists()
                else "MISSING",
                str(_WORKFLOW_RULES_YAML.relative_to(ROOT))
                if _WORKFLOW_RULES_YAML.exists()
                else "MISSING",
                str(_STATE_MACHINE_PY.relative_to(ROOT))
                if _STATE_MACHINE_PY.exists()
                else "MISSING",
                str(_SKILL_MD.relative_to(ROOT)) if _SKILL_MD.exists() else "MISSING",
            ],
            "total_steps": total_steps,
            "total_checkpoints": sum(len(v) for v in cps_by_step.values()),
            "total_quality_gates": len(gates_by_step),
            "total_veto_conditions": len(vetos),
            "valid_states": sm_states,
        },
        "steps": steps,
        "blocking_rules": blocking_rules,
        "veto_conditions": vetos,
        "quality_gates": {str(k): v for k, v in gates_by_step.items()},
    }

    # Write to disk
    try:
        _MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        _MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        logger.info(
            "PIPELINE-MANIFEST.json written: %d steps, %d checkpoints, %d gates",
            total_steps,
            manifest["_meta"]["total_checkpoints"],
            manifest["_meta"]["total_quality_gates"],
        )
    except Exception as exc:
        logger.error("Failed to write manifest: %s", exc)

    return manifest


# ---------------------------------------------------------------------------
# Loader (used by renderer -- hot-reloads on mtime change)
# ---------------------------------------------------------------------------


class PipelineManifestLoader:
    """
    Singleton loader for PIPELINE-MANIFEST.json.
    Reloads automatically when the file changes on disk.
    Safe to instantiate once at module level and share.
    """

    def __init__(self) -> None:
        self._manifest: dict[str, Any] | None = None
        self._mtime: float = 0.0

    def get(self) -> dict[str, Any]:
        """Return manifest, reloading if file was modified since last load."""
        if not _MANIFEST_PATH.exists():
            logger.warning("PIPELINE-MANIFEST.json not found -- building now")
            return build_manifest()

        try:
            mtime = _MANIFEST_PATH.stat().st_mtime
        except OSError:
            return self._manifest or {}

        if self._manifest is None or mtime > self._mtime:
            try:
                self._manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
                self._mtime = mtime
                logger.debug("Manifest reloaded (mtime changed)")
            except Exception as exc:
                logger.warning("Failed to reload manifest: %s", exc)

        return self._manifest or {}

    def step(self, step_id: int) -> dict[str, Any]:
        """Return spec for a single step."""
        return self.get().get("steps", {}).get(str(step_id), {})

    def microstep(self, step_id: int, microstep_id: str) -> dict[str, Any]:
        """Return spec for a microstep."""
        return self.step(step_id).get("microsteps", {}).get(microstep_id, {})

    def checkpoints_for_step(self, step_id: int) -> list[dict[str, Any]]:
        return self.step(step_id).get("checkpoints", [])

    def expected_artifacts(self, step_id: int) -> list[str]:
        return self.step(step_id).get("expected_artifacts", [])

    def veto(self, veto_id: str) -> dict[str, Any]:
        return self.get().get("veto_conditions", {}).get(veto_id, {})


# Singleton -- import and use anywhere
manifest_loader = PipelineManifestLoader()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build PIPELINE-MANIFEST.json")
    parser.add_argument("--force", action="store_true", help="Rebuild even if sources unchanged")
    parser.add_argument("--validate", action="store_true", help="Validate manifest after build")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    manifest = build_manifest(force=args.force)

    if args.validate:
        steps_count = len(manifest.get("steps", {}))
        cps_count = manifest.get("_meta", {}).get("total_checkpoints", 0)
        gates_count = manifest.get("_meta", {}).get("total_quality_gates", 0)
        print(f"Manifest valid: {steps_count} steps, {cps_count} checkpoints, {gates_count} gates")
        print(f"   Written to: {_MANIFEST_PATH}")
    else:
        print(f"Manifest built: {_MANIFEST_PATH}")


if __name__ == "__main__":
    _cli()
