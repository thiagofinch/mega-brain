#!/usr/bin/env python3
"""Pipeline Auto-Heal Detection Engine.

Detects missed pipeline steps for any source_id and reports gaps
with actionable heal instructions.

Usage:
    python3 core/intelligence/pipeline_heal.py --check TF001
    python3 core/intelligence/pipeline_heal.py --check-all
    python3 core/intelligence/pipeline_heal.py --list-sources
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    step_id: str
    name: str
    passed: bool
    detail: str
    heal_action: str = ""


@dataclass
class HealReport:
    source_id: str
    source_name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)

    @property
    def score_pct(self) -> int:
        if not self.checks:
            return 0
        return int(self.passed_count / self.total_count * 100)

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class PipelineHealDetector:
    """Detects missed pipeline steps for processed sources."""

    def __init__(self, project_root: Path | None = None):
        if project_root is None:
            # Walk up from this file to find the project root
            project_root = Path(__file__).resolve().parent.parent.parent
        self.root = Path(project_root)
        self._chunks_cache: dict | None = None
        self._insights_cache: dict | None = None
        self._narratives_cache: dict | None = None
        self._registry_cache: dict | None = None

    # -- Lazy loaders -------------------------------------------------------

    def _load_json(self, rel_path: str) -> dict | None:
        path = self.root / rel_path
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _load_yaml_file(self, rel_path: str) -> dict | None:
        if yaml is None:
            return None
        path = self.root / rel_path
        if not path.exists():
            return None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _file_contains(self, rel_path: str, needle: str) -> bool:
        path = self.root / rel_path
        if not path.exists():
            return False
        try:
            return needle in path.read_text(encoding="utf-8")
        except OSError:
            return False

    @property
    def chunks_state(self) -> dict:
        if self._chunks_cache is None:
            self._chunks_cache = (
                self._load_json("processing/chunks/CHUNKS-STATE.json") or {}
            )
        return self._chunks_cache

    @property
    def insights_state(self) -> dict:
        if self._insights_cache is None:
            self._insights_cache = (
                self._load_json("processing/insights/INSIGHTS-STATE.json") or {}
            )
        return self._insights_cache

    @property
    def narratives_state(self) -> dict:
        if self._narratives_cache is None:
            self._narratives_cache = (
                self._load_json("processing/narratives/NARRATIVES-STATE.json") or {}
            )
        return self._narratives_cache

    @property
    def file_registry(self) -> dict:
        if self._registry_cache is None:
            self._registry_cache = (
                self._load_json("system/REGISTRY/file-registry.json") or {}
            )
        return self._registry_cache

    # -- Source helpers ------------------------------------------------------

    def _find_source(self, source_id: str) -> dict | None:
        for src in self.chunks_state.get("sources", []):
            if src.get("source_id") == source_id:
                return src
        return None

    def _source_name(self, source_id: str) -> str:
        src = self._find_source(source_id)
        if src:
            for key in ("speaker", "guest", "host"):
                if src.get(key):
                    return src[key]
            return src.get("source_title", source_id)
        return source_id

    def _person_slug(self, source_id: str) -> str:
        """Derive kebab-case slug from source metadata."""
        name = self._source_name(source_id)
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    # -- Public API ---------------------------------------------------------

    def list_sources(self) -> list[str]:
        """Return all source_ids from CHUNKS-STATE."""
        return [s["source_id"] for s in self.chunks_state.get("sources", [])]

    def detect(self, source_id: str) -> HealReport:
        """Run all checks for a source_id and return a HealReport."""
        report = HealReport(
            source_id=source_id,
            source_name=self._source_name(source_id),
        )
        slug = self._person_slug(source_id)

        report.checks.append(self._check_chunks(source_id))
        report.checks.append(self._check_canonical(source_id))
        report.checks.append(self._check_insights(source_id))
        report.checks.append(self._check_narratives(source_id, slug))
        report.checks.append(self._check_person_dossier(source_id, slug))
        report.checks.append(self._check_theme_dossiers(source_id))
        report.checks.append(self._check_nav_map(source_id))
        report.checks.append(self._check_agent_memory(source_id, slug))
        report.checks.append(self._check_rag_index())
        report.checks.append(self._check_file_registry(source_id))
        report.checks.append(self._check_session_state(source_id))
        report.checks.append(self._check_dna(source_id, slug))
        report.checks.append(self._check_soul(source_id, slug))
        report.checks.append(self._check_inbox_registry(source_id))

        return report

    # -- Individual checks --------------------------------------------------

    def _check_chunks(self, sid: str) -> CheckResult:
        """P2: Verify CHUNKS-STATE has chunks for this source."""
        src = self._find_source(sid)
        if src and src.get("chunk_count", 0) > 0:
            return CheckResult(
                "P2", "Chunking", True, f"{src['chunk_count']} chunks"
            )
        return CheckResult(
            "P2", "Chunking", False, f"No chunks for {sid}",
            f"Run /process-jarvis Phase 2 for {sid}",
        )

    def _check_canonical(self, sid: str) -> CheckResult:
        """P3: Verify CANONICAL-MAP has entities from this source."""
        cmap = self._load_json("processing/canonical/CANONICAL-MAP.json")
        if cmap is None:
            return CheckResult(
                "P3", "Entity Resolution", False,
                "CANONICAL-MAP.json not found",
                f"Run /process-jarvis Phase 3 for {sid}",
            )
        # The canonical map stores entities under canonical_state.canonical_map
        inner = cmap.get("canonical_state", cmap)
        entity_map = inner.get("canonical_map", {})
        # Check if the person from this source appears
        name = self._source_name(sid)
        count = 0
        for entity_name in entity_map:
            if name.lower() in entity_name.lower():
                count += 1
        # Also search the full JSON for the source_id
        text = json.dumps(cmap)
        if sid in text or count > 0:
            return CheckResult(
                "P3", "Entity Resolution", True,
                f"{max(count, 1)} entities",
            )
        return CheckResult(
            "P3", "Entity Resolution", False,
            f"No entities for {sid}",
            f"Run /process-jarvis Phase 3 for {sid}",
        )

    def _check_insights(self, sid: str) -> CheckResult:
        """P4: Verify INSIGHTS-STATE has insights referencing this source."""
        categories = self.insights_state.get("categories", {})
        count = 0
        high_count = 0
        prefix = f"{sid}_"
        for cat_data in categories.values():
            for insight in cat_data.get("insights", []):
                chunks = insight.get("chunks", [])
                if any(str(c).startswith(prefix) for c in chunks):
                    count += 1
                    if insight.get("confidence") == "HIGH" or insight.get(
                        "priority"
                    ) == "HIGH":
                        high_count += 1
        if count > 0:
            return CheckResult(
                "P4", "Insights", True,
                f"{count} insights ({high_count} HIGH)",
            )
        return CheckResult(
            "P4", "Insights", False, f"No insights for {sid}",
            f"Run /process-jarvis Phase 4 for {sid}",
        )

    def _check_narratives(self, sid: str, slug: str) -> CheckResult:
        """P5: Verify NARRATIVES-STATE has a person narrative."""
        persons = self.narratives_state.get("persons", {})
        name = self._source_name(sid)
        for person_name, data in persons.items():
            pslug = re.sub(r"[^a-z0-9]+", "-", person_name.lower()).strip("-")
            if pslug == slug or name.lower() in person_name.lower():
                narrative = data.get("narrative", "")
                sections = narrative.count("##") if narrative else 0
                return CheckResult(
                    "P5", "Narratives", True,
                    f"1 person, ~{max(sections, 1)} sections",
                )
        # Fallback: check if source_id appears anywhere in narratives
        if sid in json.dumps(persons):
            return CheckResult(
                "P5", "Narratives", True,
                "Source referenced in narratives",
            )
        return CheckResult(
            "P5", "Narratives", False, f"No narrative for {name}",
            f"Run /process-jarvis Phase 5 for {sid}",
        )

    def _check_person_dossier(self, sid: str, slug: str) -> CheckResult:
        """P6.2: Verify DOSSIER-{PERSON}.md exists."""
        dossier_dir = self.root / "knowledge" / "external" / "dossiers" / "persons"
        if not dossier_dir.exists():
            return CheckResult(
                "P6.2", "Person Dossier", False,
                "Dossier directory not found",
                f"Run /process-jarvis Phase 6.2 for {sid}",
            )
        name = self._source_name(sid)
        dossier_name = f"DOSSIER-{name.upper().replace(' ', '-')}.md"
        if (dossier_dir / dossier_name).exists():
            return CheckResult(
                "P6.2", "Person Dossier", True, dossier_name
            )
        # Try slug-based match
        for f in dossier_dir.glob("DOSSIER-*.md"):
            if slug in f.name.lower().replace("-", " ").replace(" ", "-"):
                return CheckResult("P6.2", "Person Dossier", True, f.name)
        return CheckResult(
            "P6.2", "Person Dossier", False, f"No dossier for {name}",
            f"Run /process-jarvis Phase 6.2 for {sid}",
        )

    def _check_theme_dossiers(self, sid: str) -> CheckResult:
        """P6.3: Verify theme dossiers reference this source."""
        theme_dir = self.root / "knowledge" / "external" / "dossiers" / "themes"
        if not theme_dir.exists():
            return CheckResult(
                "P6.3", "Theme Dossiers", False,
                "Theme dossier directory not found",
                f"Run /process-jarvis Phase 6.3 for {sid}",
            )
        found = []
        for f in sorted(theme_dir.glob("DOSSIER-*.md")):
            rel = str(f.relative_to(self.root))
            if self._file_contains(rel, sid):
                found.append(f.stem.replace("DOSSIER-", ""))
        if found:
            return CheckResult(
                "P6.3", "Theme Dossiers", True, f"{len(found)} themes"
            )
        return CheckResult(
            "P6.3", "Theme Dossiers", False,
            f"No theme dossiers reference {sid}",
            f"Run /process-jarvis Phase 6.3 for {sid}",
        )

    def _check_nav_map(self, sid: str) -> CheckResult:
        """P6.6: Verify NAVIGATION-MAP.json is updated with this source."""
        nav = self._load_json("knowledge/NAVIGATION-MAP.json")
        if nav is None:
            return CheckResult(
                "P6.6", "Navigation Map", False,
                "NAVIGATION-MAP.json not found",
                "Run python3 core/intelligence/nav_map_builder.py",
            )
        text = json.dumps(nav)
        if sid in text:
            return CheckResult(
                "P6.6", "Navigation Map", True,
                "Source in NAVIGATION-MAP.json",
            )
        # Check if person dossier is in the nav map
        slug = self._person_slug(sid)
        name = self._source_name(sid)
        if slug in text.lower() or name.upper() in text.upper():
            return CheckResult(
                "P6.6", "Navigation Map", True,
                "Person referenced in NAVIGATION-MAP.json",
            )
        return CheckResult(
            "P6.6", "Navigation Map", False,
            f"No {sid} entry in NAVIGATION-MAP.json",
            "Run python3 core/intelligence/nav_map_builder.py",
        )

    def _check_agent_memory(self, sid: str, slug: str) -> CheckResult:
        """P7.4: Verify agent MEMORY.md has this source_id."""
        mem_path = f"agents/minds/{slug}/MEMORY.md"
        full = self.root / mem_path
        if not full.exists():
            return CheckResult(
                "P7.4", "Agent MEMORY", False,
                f"No MEMORY.md at {mem_path}",
                f"Create {mem_path} with {sid} insights",
            )
        if self._file_contains(mem_path, sid):
            return CheckResult("P7.4", "Agent MEMORY", True, mem_path)
        return CheckResult(
            "P7.4", "Agent MEMORY", False,
            f"MEMORY.md exists but no {sid} ref",
            f"Update {mem_path} with {sid} insights",
        )

    def _check_rag_index(self) -> CheckResult:
        """P8.1.1: Verify RAG BM25 index is current."""
        # Check cache locations
        for rel in [
            "core/intelligence/rag/.cache/bm25_index.json",
            "core/intelligence/rag/bm25_index.json",
            ".cache/rag/bm25_index.json",
        ]:
            idx_path = self.root / rel
            if idx_path.exists():
                chunks_path = (
                    self.root / "processing" / "chunks" / "CHUNKS-STATE.json"
                )
                if chunks_path.exists():
                    if idx_path.stat().st_mtime >= chunks_path.stat().st_mtime:
                        return CheckResult(
                            "P8.1.1", "RAG Index", True, "BM25 current"
                        )
                    return CheckResult(
                        "P8.1.1", "RAG Index", False, "BM25 index outdated",
                        "Run python3 core/intelligence/rag/hybrid_index.py --build",
                    )
                return CheckResult(
                    "P8.1.1", "RAG Index", True, "BM25 exists (no CHUNKS to compare)"
                )
        # No index file found — check if hybrid_index.py exists at all
        if (self.root / "core/intelligence/rag/hybrid_index.py").exists():
            return CheckResult(
                "P8.1.1", "RAG Index", False, "BM25 index not built",
                "Run python3 core/intelligence/rag/hybrid_index.py --build",
            )
        return CheckResult(
            "P8.1.1", "RAG Index", False, "RAG system not found",
            "Install RAG system first",
        )

    def _check_file_registry(self, sid: str) -> CheckResult:
        """P8.1.2: Verify file-registry.json has an entry for this source."""
        files = self.file_registry.get("files", {})
        name = self._source_name(sid)
        name_upper = name.upper()
        for fpath in files:
            if sid in fpath or name_upper in fpath.upper():
                return CheckResult(
                    "P8.1.2", "File Registry", True, "Entry found"
                )
        return CheckResult(
            "P8.1.2", "File Registry", False,
            f"No entry for {sid}",
            "Run python3 scripts/file_registry.py --scan",
        )

    def _check_session_state(self, sid: str) -> CheckResult:
        """P8.1.3: Verify session/mission state references this source."""
        for rel in [
            "system/SESSION-STATE.md",
            ".claude/mission-control/MISSION-STATE.json",
        ]:
            if (self.root / rel).exists():
                if self._file_contains(rel, sid):
                    return CheckResult(
                        "P8.1.3", "Session State", True,
                        f"Referenced in {rel}",
                    )
        # State file exists but no reference
        if (self.root / ".claude/mission-control/MISSION-STATE.json").exists():
            return CheckResult(
                "P8.1.3", "Session State", False,
                f"State exists but no {sid} ref",
                f"Update session state with {sid} completion",
            )
        return CheckResult(
            "P8.1.3", "Session State", False,
            "No session state file found",
            "Create session state tracking",
        )

    def _check_dna(self, sid: str, slug: str) -> CheckResult:
        """P8.1.8: Verify DNA exists if dossier density >= 3/5."""
        dna_dir = self.root / "knowledge" / "external" / "dna" / "persons" / slug
        if dna_dir.exists():
            yaml_files = list(dna_dir.glob("*.yaml"))
            return CheckResult(
                "P8.1.8", "DNA Auto-Create", True,
                f"{len(yaml_files)} files",
            )
        # DNA doesn't exist — check if it should
        density = self._dossier_density(sid, slug)
        if density >= 3:
            return CheckResult(
                "P8.1.8", "DNA Auto-Create", False,
                f"DNA missing: density {density}/5 >= threshold",
                f"Run /extract-dna {slug} to create DNA from dossier",
            )
        return CheckResult(
            "P8.1.8", "DNA Auto-Create", True,
            f"DNA not needed: density {density}/5 < 3 threshold",
        )

    def _check_soul(self, sid: str, slug: str) -> CheckResult:
        """P8.1.9: Verify SOUL.md is updated with this source_id."""
        soul_path = f"agents/minds/{slug}/SOUL.md"
        full = self.root / soul_path
        if not full.exists():
            return CheckResult(
                "P8.1.9", "SOUL Update", False,
                f"No SOUL.md at {soul_path}",
                f"Create SOUL.md for {slug} with {sid} insights",
            )
        if self._file_contains(soul_path, sid):
            return CheckResult(
                "P8.1.9", "SOUL Update", True, f"SOUL.md has {sid} ref"
            )
        return CheckResult(
            "P8.1.9", "SOUL Update", False,
            f"No {sid} ref in SOUL.md",
            f"Update {soul_path} with {sid} insights",
        )

    def _check_inbox_registry(self, sid: str) -> CheckResult:
        """P8.3.5: Verify INBOX-REGISTRY has an entry for this source."""
        for rel in [
            "system/registry/INBOX-REGISTRY.md",
            "system/REGISTRY/INBOX-REGISTRY.md",
        ]:
            if (self.root / rel).exists():
                if self._file_contains(rel, sid):
                    return CheckResult(
                        "P8.3.5", "INBOX Registry", True,
                        f"Entry in {rel}",
                    )
                return CheckResult(
                    "P8.3.5", "INBOX Registry", False,
                    f"Registry exists but no {sid} entry",
                    f"Add {sid} entry to {rel}",
                )
        return CheckResult(
            "P8.3.5", "INBOX Registry", False,
            "INBOX-REGISTRY not found",
            f"Create INBOX-REGISTRY with {sid} entry",
        )

    # -- Helpers ------------------------------------------------------------

    def _dossier_density(self, sid: str, slug: str) -> int:
        """Count non-empty major sections in person dossier (max 5).

        Sections checked: TL;DR / Philosophy / Modus Operandi / Arsenal / Traps
        """
        dossier_dir = self.root / "knowledge" / "external" / "dossiers" / "persons"
        if not dossier_dir.exists():
            return 0

        name = self._source_name(sid)
        dossier_name = f"DOSSIER-{name.upper().replace(' ', '-')}.md"
        dossier_path = dossier_dir / dossier_name
        if not dossier_path.exists():
            for f in dossier_dir.glob("DOSSIER-*.md"):
                if slug in f.name.lower():
                    dossier_path = f
                    break
            else:
                return 0

        try:
            content = dossier_path.read_text(encoding="utf-8").lower()
        except OSError:
            return 0

        markers = [
            "tl;dr", "philosoph", "filosof",
            "modus operandi", "operacion",
            "arsenal", "framework", "heuristic", "heuristica",
            "trap", "armadilha", "ponto cego",
        ]
        found = set()
        for m in markers:
            if m in content:
                # Map to one of 5 canonical sections
                if m in ("tl;dr",):
                    found.add("tldr")
                elif m in ("philosoph", "filosof"):
                    found.add("philosophy")
                elif m in ("modus operandi", "operacion"):
                    found.add("modus")
                elif m in ("arsenal", "framework", "heuristic", "heuristica"):
                    found.add("arsenal")
                elif m in ("trap", "armadilha", "ponto cego"):
                    found.add("traps")
        return len(found)

    # -- Report formatting --------------------------------------------------

    def format_report(self, report: HealReport) -> str:
        """Generate ASCII visual report."""
        lines: list[str] = []
        w = 65

        lines.append("=" * w)
        title = f"  PIPELINE HEALTH: {report.source_id} ({report.source_name})"
        lines.append(title)
        lines.append("=" * w)
        lines.append("")

        # Score bar
        pct = report.score_pct
        filled = int(pct / 100 * 15)
        bar = "\u2588" * filled + "\u2591" * (15 - filled)
        lines.append(
            f"  SCORE: {report.passed_count}/{report.total_count} "
            f"{bar} {pct}%"
        )
        lines.append("")

        # Individual checks
        for c in report.checks:
            icon = "\u2705" if c.passed else "\u274c"
            step = c.step_id.ljust(8)
            name = c.name.ljust(18)
            lines.append(f"  {icon} {step}{name}{c.detail}")

        # Heal actions
        failed = report.failed_checks
        if failed:
            lines.append("")
            lines.append(f"  HEAL ACTIONS NEEDED: {len(failed)}")
            for i, c in enumerate(failed, 1):
                lines.append(f"  {i}. [{c.step_id}] {c.heal_action}")
        else:
            lines.append("")
            lines.append("  ALL CHECKS PASSED \u2728")

        lines.append("=" * w)
        return "\n".join(lines)

    def format_report_json(self, report: HealReport) -> str:
        """Generate JSON report."""
        return json.dumps(
            {
                "source_id": report.source_id,
                "source_name": report.source_name,
                "score": f"{report.passed_count}/{report.total_count}",
                "pct": report.score_pct,
                "checks": [
                    {
                        "step": c.step_id,
                        "name": c.name,
                        "passed": c.passed,
                        "detail": c.detail,
                        "heal": c.heal_action,
                    }
                    for c in report.checks
                ],
            },
            indent=2,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline Auto-Heal Detection Engine"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check", metavar="SOURCE_ID",
        help="Check a specific source_id",
    )
    group.add_argument(
        "--check-all", action="store_true",
        help="Check all known sources",
    )
    group.add_argument(
        "--list-sources", action="store_true",
        help="List all source_ids from CHUNKS-STATE",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of ASCII",
    )
    parser.add_argument(
        "--root", type=Path, default=None,
        help="Project root (auto-detected if omitted)",
    )

    args = parser.parse_args()
    detector = PipelineHealDetector(args.root)

    if args.list_sources:
        sources = detector.list_sources()
        if args.json:
            print(json.dumps(sources, indent=2))
        else:
            print(f"Sources ({len(sources)}):")
            for s in sources:
                name = detector._source_name(s)
                print(f"  {s} \u2014 {name}")
        sys.exit(0)

    if args.check:
        src = detector._find_source(args.check)
        if src is None:
            print(f"Error: source_id '{args.check}' not found in CHUNKS-STATE.json")
            sys.exit(2)
        report = detector.detect(args.check)
        if args.json:
            print(detector.format_report_json(report))
        else:
            print(detector.format_report(report))
        sys.exit(0 if report.passed_count == report.total_count else 1)

    if args.check_all:
        sources = detector.list_sources()
        if not sources:
            print("No sources found in CHUNKS-STATE.json")
            sys.exit(1)
        any_failed = False
        for sid in sources:
            report = detector.detect(sid)
            if args.json:
                print(detector.format_report_json(report))
            else:
                print(detector.format_report(report))
                print()
            if report.failed_checks:
                any_failed = True
        sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
