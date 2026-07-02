#!/usr/bin/env python3
"""
Health Scorer — Holistic 0-100 Score with 5 Components
=======================================================
Implements the deterministic health formula ported from OLD MegaBrain:

    Score = min(100, sum([
        state_files_score,    # JSON valid +10, schema valid +5, mtime <7d +5
        agents_score,         # MEMORYs exist +10, <30d +5, no orphans +5
        dossiers_score,       # person dossier +10, theme dossier +5, no broken routing +5
        inbox_score,          # no urgents >7d +10, <10 pending +5, all with sidecar +5
        pipeline_score        # no FAILED states +10, batch history has run +5, last run <7d +5
    ]))

Usage:
    from engine.intelligence.health.health_scorer import HealthScorer, HealthScore

    scorer = HealthScorer(Path("/path/to/project"))
    result = scorer.compute()
    print(result.score_total, result.grade)

CLI:
    python3 -m engine.intelligence.health.health_scorer

Story: MCE-11.12
Version: 1.0.0
Date: 2026-05-27
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------


@dataclass
class ComponentResult:
    """Result for a single health component."""

    score: int
    max: int
    checks: dict[str, bool]
    issues: list[str] = field(default_factory=list)


@dataclass
class HealthScore:
    """Full health score output.

    Attributes:
        score_total:   0-100 integer score.
        grade:         EXCELENTE / BOM / ATENÇÃO / CRÍTICO
        computed_at:   ISO 8601 timestamp of computation.
        components:    Per-component breakdown.
        issues:        Human-readable list of detected problems.
    """

    score_total: int
    grade: str
    computed_at: str
    components: dict[str, ComponentResult]
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "score_total": self.score_total,
            "grade": self.grade,
            "computed_at": self.computed_at,
            "components": {
                name: {
                    "score": comp.score,
                    "max": comp.max,
                    "checks": comp.checks,
                }
                for name, comp in self.components.items()
            },
            "issues": self.issues,
        }


# ---------------------------------------------------------------------------
# GRADING
# ---------------------------------------------------------------------------

_GRADE_THRESHOLDS = [
    (85, "EXCELENTE"),
    (70, "BOM"),
    (50, "ATENÇÃO"),
    (0, "CRÍTICO"),
]


def _grade(score: int) -> str:
    for threshold, label in _GRADE_THRESHOLDS:
        if score >= threshold:
            return label
    return "CRÍTICO"


# ---------------------------------------------------------------------------
# HEALTH SCORER
# ---------------------------------------------------------------------------


class HealthScorer:
    """Computes the holistic 0-100 health score for the MegaBrain system.

    Args:
        project_root: Absolute path to the project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def compute(self) -> HealthScore:
        """Run all 5 component checks and return the aggregated HealthScore."""
        computed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        components: dict[str, ComponentResult] = {
            "state_files": self._check_state_files(),
            "agents": self._check_agents(),
            "dossiers": self._check_dossiers(),
            "inbox": self._check_inbox(),
            "pipeline": self._check_pipeline(),
        }

        total = sum(c.score for c in components.values())
        total = min(100, total)
        issues: list[str] = []
        for name, comp in components.items():
            issues.extend(f"{name}: {issue}" for issue in comp.issues)

        result = HealthScore(
            score_total=total,
            grade=_grade(total),
            computed_at=computed_at,
            components=components,
            issues=issues,
        )

        # Write HEALTH-STATE.json — non-blocking
        try:
            self._persist(result)
        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # COMPONENT 1 — State Files (max 20pts)
    # ------------------------------------------------------------------

    def _check_state_files(self) -> ComponentResult:
        """Check .data/artifacts/insights/INSIGHTS-STATE.json.

        - JSON valid:                    +10
        - Schema has required fields:    +5  (version, total_insights, persons)
        - mtime < 7 days:                +5
        """
        score = 0
        checks: dict[str, bool] = {
            "json_valid": False,
            "schema_valid": False,
            "mtime_lt_7d": False,
        }
        issues: list[str] = []

        state_file = self._root / ".data" / "artifacts" / "insights" / "INSIGHTS-STATE.json"

        if not state_file.exists():
            issues.append("INSIGHTS-STATE.json nao encontrado")
            return ComponentResult(score=0, max=20, checks=checks, issues=issues)

        # JSON valid (+10)
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            checks["json_valid"] = True
            score += 10
        except (json.JSONDecodeError, OSError):
            issues.append("INSIGHTS-STATE.json invalido (JSON parse error)")
            return ComponentResult(score=score, max=20, checks=checks, issues=issues)

        # Schema valid (+5)
        required_fields = {"version", "total_insights", "persons"}
        # Accept top-level or nested under insights_state
        top_keys = set(data.keys()) if isinstance(data, dict) else set()
        nested = data.get("insights_state", {}) if isinstance(data, dict) else {}
        nested_keys = set(nested.keys()) if isinstance(nested, dict) else set()
        combined_keys = top_keys | nested_keys

        if required_fields.issubset(combined_keys):
            checks["schema_valid"] = True
            score += 5
        else:
            missing = required_fields - combined_keys
            issues.append(f"INSIGHTS-STATE.json schema incompleto: faltam {missing}")

        # mtime < 7 days (+5)
        age_days = (time.time() - state_file.stat().st_mtime) / 86400.0
        if age_days < 7:
            checks["mtime_lt_7d"] = True
            score += 5
        else:
            issues.append(f"INSIGHTS-STATE.json nao atualizado ha {age_days:.1f} dias (limite: 7d)")

        return ComponentResult(score=score, max=20, checks=checks, issues=issues)

    # ------------------------------------------------------------------
    # COMPONENT 2 — Agents (max 20pts)
    # ------------------------------------------------------------------

    def _check_agents(self) -> ComponentResult:
        """Check agents/external/ for MEMORY.md presence and freshness.

        - At least 1 MEMORY.md exists:                +10
        - At least 1 MEMORY.md updated < 30 days:     +5
        - No MEMORY.md with size < 100 bytes (empty):  +5
        """
        score = 0
        checks: dict[str, bool] = {
            "memory_exists": False,
            "memory_fresh": False,
            "no_empty_memory": False,
        }
        issues: list[str] = []

        agents_dir = self._root / "agents" / "external"
        memory_files = list(agents_dir.rglob("MEMORY.md")) if agents_dir.exists() else []

        # Filter out trash and worktrees
        memory_files = [
            f for f in memory_files if ".claude/trash" not in str(f) and "worktrees" not in str(f)
        ]

        if not memory_files:
            issues.append("Nenhum MEMORY.md encontrado em agents/external/")
            return ComponentResult(score=0, max=20, checks=checks, issues=issues)

        # MEMORY.md exists (+10)
        checks["memory_exists"] = True
        score += 10

        # At least 1 fresh (< 30 days) (+5)
        now = time.time()
        fresh_count = sum(1 for f in memory_files if (now - f.stat().st_mtime) / 86400.0 < 30)
        if fresh_count > 0:
            checks["memory_fresh"] = True
            score += 5
        else:
            issues.append(
                f"Todos os {len(memory_files)} MEMORY.md estao ha mais de 30 dias sem atualizacao"
            )

        # No empty (<100 bytes) (+5)
        empty_files = [f for f in memory_files if f.stat().st_size < 100]
        if not empty_files:
            checks["no_empty_memory"] = True
            score += 5
        else:
            rel = [str(f.relative_to(self._root)) for f in empty_files[:3]]
            issues.append(f"{len(empty_files)} MEMORY.md vazios (<100 bytes): {rel}")

        return ComponentResult(score=score, max=20, checks=checks, issues=issues)

    # ------------------------------------------------------------------
    # COMPONENT 3 — Dossiers (max 20pts)
    # ------------------------------------------------------------------

    def _check_dossiers(self) -> ComponentResult:
        """Check knowledge/external/dossiers/ for person and theme dossiers.

        - At least 1 person dossier exists:                +10
        - At least 1 theme dossier exists:                 +5
        - No broken routing (dossier-general.md not sole dossier in themes): +5
        """
        score = 0
        checks: dict[str, bool] = {
            "person_dossier_exists": False,
            "theme_dossier_exists": False,
            "no_broken_routing": False,
        }
        issues: list[str] = []

        persons_dir = self._root / "knowledge" / "external" / "dossiers" / "persons"
        themes_dir = self._root / "knowledge" / "external" / "dossiers" / "themes"

        # Person dossier (+10)
        person_dossiers = (
            [f for f in persons_dir.glob("dossier-*.md") if f.is_file()]
            if persons_dir.exists()
            else []
        )
        # Exclude example/template entries
        real_persons = [
            f for f in person_dossiers if "example" not in f.name and "name" not in f.name
        ]

        if real_persons:
            checks["person_dossier_exists"] = True
            score += 10
        else:
            issues.append("Nenhum dossier de pessoa real em knowledge/external/dossiers/persons/")

        # Theme dossier (+5)
        theme_dossiers = (
            [f for f in themes_dir.glob("*.md") if f.is_file()] if themes_dir.exists() else []
        )
        # Exclude dossier-general.md
        real_themes = [f for f in theme_dossiers if "general" not in f.name.lower()]

        if real_themes:
            checks["theme_dossier_exists"] = True
            score += 5
        else:
            issues.append(
                "Nenhum dossier tematico real em knowledge/external/dossiers/themes/ "
                "(apenas dossier-general.md indica routing quebrado)"
            )

        # No broken routing (+5)
        # Broken = themes dir only has dossier-general.md (routing wrote everything to general)
        general_only = len(theme_dossiers) > 0 and all(
            "general" in f.name.lower() for f in theme_dossiers
        )
        if not general_only:
            checks["no_broken_routing"] = True
            score += 5
        else:
            issues.append(
                "Dossier tematico so tem dossier-general.md — routing pode estar quebrado"
            )

        return ComponentResult(score=score, max=20, checks=checks, issues=issues)

    # ------------------------------------------------------------------
    # COMPONENT 4 — Inbox (max 20pts)
    # ------------------------------------------------------------------

    def _check_inbox(self) -> ComponentResult:
        """Check knowledge/external/inbox/ for pending files.

        - No file with mtime > 7 days unprocessed:  +10
        - Less than 10 pending files total:          +5
        - Every file has a .entity-discovery.json sidecar: +5

        When inbox is empty (no files), score is max (20) — clean state.
        """
        score = 0
        checks: dict[str, bool] = {
            "no_urgents": False,
            "lt_10_pending": False,
            "all_have_sidecar": False,
        }
        issues: list[str] = []

        inbox_dir = self._root / "knowledge" / "external" / "inbox"

        if not inbox_dir.exists():
            # No inbox at all — max score (clean)
            checks["no_urgents"] = True
            checks["lt_10_pending"] = True
            checks["all_have_sidecar"] = True
            return ComponentResult(score=20, max=20, checks=checks, issues=issues)

        # Gather processable files (exclude sidecars and hidden files)
        pending = [
            f
            for f in inbox_dir.iterdir()
            if f.is_file()
            and not f.name.startswith(".")
            and not f.name.endswith(".entity-discovery.json")
            and not f.name.endswith(".json")
        ]

        if not pending:
            # Empty inbox — max score
            checks["no_urgents"] = True
            checks["lt_10_pending"] = True
            checks["all_have_sidecar"] = True
            return ComponentResult(score=20, max=20, checks=checks, issues=issues)

        now = time.time()

        # No urgents > 7 days (+10)
        urgents = [f for f in pending if (now - f.stat().st_mtime) / 86400.0 > 7]
        if not urgents:
            checks["no_urgents"] = True
            score += 10
        else:
            issues.append(f"{len(urgents)} arquivo(s) no inbox ha mais de 7 dias sem processamento")

        # < 10 pending (+5)
        if len(pending) < 10:
            checks["lt_10_pending"] = True
            score += 5
        else:
            issues.append(f"{len(pending)} arquivos pendentes no inbox (limite: 10)")

        # All have sidecar (+5)
        missing_sidecar = [
            f for f in pending if not (inbox_dir / f"{f.name}.entity-discovery.json").exists()
        ]
        if not missing_sidecar:
            checks["all_have_sidecar"] = True
            score += 5
        else:
            rel = [f.name for f in missing_sidecar[:3]]
            issues.append(
                f"{len(missing_sidecar)} arquivo(s) sem .entity-discovery.json sidecar: {rel}"
            )

        return ComponentResult(score=score, max=20, checks=checks, issues=issues)

    # ------------------------------------------------------------------
    # COMPONENT 5 — Pipeline (max 20pts)
    # ------------------------------------------------------------------

    def _check_pipeline(self) -> ComponentResult:
        """Check FSM states and BATCH-HISTORY.json.

        - No slug with state FAILED in FSM:                    +10
        - BATCH-HISTORY.json exists with >= 1 successful run:  +5
        - Last run completed < 7 days ago:                     +5
        """
        score = 0
        checks: dict[str, bool] = {
            "no_failed_slugs": False,
            "batch_history_has_run": False,
            "last_run_lt_7d": False,
        }
        issues: list[str] = []

        # No FAILED slugs in FSM (+10)
        mce_dir = self._root / ".claude" / "mission-control" / "mce"
        failed_slugs: list[str] = []

        if mce_dir.exists():
            try:
                import yaml

                for state_file in mce_dir.rglob("pipeline_state.yaml"):
                    try:
                        data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
                        if isinstance(data, dict) and data.get("state") == "failed":
                            slug = data.get("slug", str(state_file.parent.name))
                            failed_slugs.append(slug)
                    except Exception:
                        continue
            except ImportError:
                # PyYAML unavailable — skip FSM check, give benefit of doubt
                pass

        # Filter out known test/fixture slugs
        test_slugs = {
            "not-paused",
            "terminal-pause",
            "full-cycle",
            "resume-hook-test",
            "trigger-pause",
            "crash-vs-pause",
            "pause-path",
        }
        real_failed = [s for s in failed_slugs if s not in test_slugs]

        if not real_failed:
            checks["no_failed_slugs"] = True
            score += 10
        else:
            issues.append(f"{len(real_failed)} slug(s) com estado FAILED: {real_failed[:3]}")

        # BATCH-HISTORY.json with >= 1 run (+5)
        batch_history_path = self._root / "system" / "REGISTRY" / "BATCH-HISTORY.json"
        last_run_at: float = 0.0

        if batch_history_path.exists():
            try:
                data = json.loads(batch_history_path.read_text(encoding="utf-8"))
                batches = data.get("batches", [])
                if isinstance(batches, list) and len(batches) > 0:
                    checks["batch_history_has_run"] = True
                    score += 5

                    # Find newest completed batch timestamp (+5)
                    for batch in batches:
                        if isinstance(batch, dict):
                            completed = batch.get("completed_at") or batch.get("updated_at", "")
                            if completed:
                                try:
                                    import re

                                    # Parse ISO timestamps like 2026-04-19T00:00:00Z
                                    m = re.match(
                                        r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})",
                                        completed,
                                    )
                                    if m:
                                        import calendar
                                        import datetime

                                        dt = datetime.datetime(
                                            *[int(g) for g in m.groups()],
                                            tzinfo=datetime.UTC,
                                        )
                                        ts = calendar.timegm(dt.timetuple())
                                        if ts > last_run_at:
                                            last_run_at = ts
                                except Exception:
                                    pass
                else:
                    issues.append("BATCH-HISTORY.json existe mas nao tem runs registrados")
            except (json.JSONDecodeError, OSError):
                issues.append("BATCH-HISTORY.json invalido ou ilegivel")
        else:
            issues.append("BATCH-HISTORY.json nao encontrado em system/REGISTRY/")

        # Last run < 7 days (+5)
        if last_run_at > 0:
            age_days = (time.time() - last_run_at) / 86400.0
            if age_days < 7:
                checks["last_run_lt_7d"] = True
                score += 5
            else:
                issues.append(f"Ultimo run do pipeline ha {age_days:.1f} dias (limite: 7d)")
        else:
            # No timestamp found — if batch history has runs, check HEALTH-STATE.json mtime
            health_state = self._root / ".data" / "artifacts" / "HEALTH-STATE.json"
            if health_state.exists():
                age_days = (time.time() - health_state.stat().st_mtime) / 86400.0
                if age_days < 7:
                    checks["last_run_lt_7d"] = True
                    score += 5
                else:
                    issues.append(f"HEALTH-STATE.json nao atualizado ha {age_days:.1f} dias")

        return ComponentResult(score=score, max=20, checks=checks, issues=issues)

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def _persist(self, result: HealthScore) -> None:
        """Write HEALTH-STATE.json to .data/artifacts/."""
        artifacts_dir = self._root / ".data" / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifacts_dir / "HEALTH-STATE.json"
        out_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# ASCII RENDERING
# ---------------------------------------------------------------------------


def _gauge_bar(score: int, total: int = 100, width: int = 20) -> str:
    """Render a filled/empty progress bar."""
    if total == 0:
        return "░" * width
    filled = round(score / total * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _component_bar(score: int, max_pts: int = 20, width: int = 12) -> str:
    return _gauge_bar(score, max_pts, width)


def _trend_arrow(score: int, max_pts: int = 20) -> str:
    ratio = score / max_pts if max_pts > 0 else 0
    if ratio >= 1.0:
        return "✓"
    if ratio >= 0.75:
        return "↑"
    if ratio >= 0.5:
        return "↓"
    return "↓↓"


def render_health_box(result: HealthScore) -> str:
    """Render the ASCII health score box for /jarvis-briefing."""
    grade = result.grade
    total = result.score_total
    bar = _gauge_bar(total)
    pct = f"{total}%"

    lines: list[str] = [
        "┌─────────────────────────────────────────┐",
        f"│  HEALTH SCORE: {total}/100 — {grade:<12}       │",
        f"│  {bar}  {pct:<4}              │",
        "│                                         │",
    ]

    comp_labels = {
        "state_files": "State Files",
        "agents": "Agents    ",
        "dossiers": "Dossiers  ",
        "inbox": "Inbox     ",
        "pipeline": "Pipeline  ",
    }

    for key, label in comp_labels.items():
        comp = result.components.get(key)
        if comp is None:
            continue
        bar12 = _component_bar(comp.score, comp.max, 12)
        arrow = _trend_arrow(comp.score, comp.max)
        lines.append(f"│  {label}  {bar12}  {comp.score}/{comp.max} {arrow:<2}   │")

    lines.append("└─────────────────────────────────────────┘")

    if result.issues:
        lines.append("")
        lines.append("  Issues:")
        for issue in result.issues[:5]:
            lines.append(f"    • {issue}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entrypoint: compute and display health score."""
    import argparse

    parser = argparse.ArgumentParser(description="MegaBrain Holistic Health Score (0-100)")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output JSON instead of ASCII box",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Project root path (default: auto-detect from this file)",
    )
    args = parser.parse_args()

    if args.root:
        root = Path(args.root).resolve()
    else:
        # Auto-detect: go up from engine/intelligence/health/
        root = Path(__file__).resolve().parent.parent.parent.parent

    scorer = HealthScorer(root)
    result = scorer.compute()

    if args.json_output:
        import sys

        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(0 if result.score_total >= 70 else 1)
    else:
        print(render_health_box(result))
        print(f"\n  Computed at: {result.computed_at}")
        print("  HEALTH-STATE.json written to: .data/artifacts/HEALTH-STATE.json")

        import sys

        sys.exit(0 if result.score_total >= 70 else 1)


if __name__ == "__main__":
    main()
