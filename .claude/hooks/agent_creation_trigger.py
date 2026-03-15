#!/usr/bin/env python3
"""
Agent Discovery Engine v3.1

Two-axis automatic agent tracking:
  AXIS 1 — PERSON: detects persons with DNA+dossier ready for mind agents
  AXIS 2 — CARGO: counts role mentions from agents/cargo/ hierarchy in knowledge base

Auto-discovers everything from filesystem. Zero hardcoded registries.

Hook: PostToolUse | Timeout: 5s | Version: 3.1.0
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# ── PATHS ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent

try:
    sys.path.insert(0, str(ROOT))
    from core.paths import AGENTS, ARTIFACTS, KNOWLEDGE_EXTERNAL, LOGS, MISSION_CONTROL

    AGENT_DISCOVERY = AGENTS / "discovery"
except ImportError:
    KNOWLEDGE_EXTERNAL = ROOT / "knowledge" / "external"
    AGENTS = ROOT / "agents"
    ARTIFACTS = ROOT / "artifacts"
    LOGS = ROOT / "logs"
    MISSION_CONTROL = ROOT / ".claude" / "mission-control"
    AGENT_DISCOVERY = AGENTS / "discovery"

DNA_PERSONS = KNOWLEDGE_EXTERNAL / "dna" / "persons"
DOSSIER_DIR = KNOWLEDGE_EXTERNAL / "dossiers" / "persons"
INSIGHTS_DIR = ARTIFACTS / "insights"
MINDS_DIR = AGENTS / "external"
CARGO_DIR = AGENTS / "cargo"
ROLE_TRACKING = AGENT_DISCOVERY / "role-tracking.md"
DISCOVERY_STATE = MISSION_CONTROL / "DISCOVERY-STATE.json"
CREATION_LOG = LOGS / "agent-creation.jsonl"

# ── THRESHOLDS ─────────────────────────────────────────────────────
MIN_DNA_YAMLS = 1
MIN_DOSSIER_BYTES = 3072
CARGO_CRITICAL = 10
CARGO_IMPORTANT = 5

SKIP_FILES = {
    ".gitkeep",
    ".DS_Store",
    "DOSSIER-EXAMPLE.md",
    "HORMOZI-FULL-AGENT.md",
    "HORMOZI-RESUMO.md",
}

# Extra keyword expansions for common slugs (auto-discovery handles the rest)
KEYWORD_EXPAND = {
    "bdr": ["business development"],
    "sds": ["sales development specialist"],
    "lns": ["lead nurture"],
    "cro": ["chief revenue"],
    "cfo": ["chief financial"],
    "cmo": ["chief marketing"],
    "coo": ["chief operating"],
    "ceo": ["chief executive", "founder", "fundador"],
    "closer": ["closing", "fechamento"],
    "setter": ["setting", "appointment setter"],
    "sdr": ["sales development rep"],
    "nepq-specialist": ["nepq", "neuro-emotional"],
}


# ═══════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════


@dataclass
class PersonRecord:
    slug: str
    dna_yaml_count: int = 0
    dossier_exists: bool = False
    dossier_bytes: int = 0
    insight_count: int = 0
    agent_exists: bool = False
    status: str = "SKIP"
    priority: int = 0


@dataclass
class CargoRole:
    slug: str
    area: str
    has_agent: bool = False
    mentions: int = 0
    source_count: int = 0
    status: str = "TRACK"


# ═══════════════════════════════════════════════════════════════════
# AXIS 1: PERSON SCAN
# ═══════════════════════════════════════════════════════════════════


def scan_persons() -> list[PersonRecord]:
    persons: dict[str, PersonRecord] = {}

    if DNA_PERSONS.is_dir():
        for d in os.scandir(DNA_PERSONS):
            if not d.is_dir() or d.name.startswith(("_", ".")):
                continue
            rec = persons.setdefault(d.name, PersonRecord(slug=d.name))
            try:
                rec.dna_yaml_count = sum(
                    1
                    for f in os.scandir(d.path)
                    if f.is_file() and f.name.endswith((".yaml", ".yml"))
                )
            except OSError:
                pass

    if DOSSIER_DIR.is_dir():
        for f in os.scandir(DOSSIER_DIR):
            if not f.is_file() or f.name in SKIP_FILES:
                continue
            if f.name.startswith("DOSSIER-") and f.name.endswith(".md"):
                slug = f.name[8:-3].lower()
                rec = persons.setdefault(slug, PersonRecord(slug=slug))
                rec.dossier_exists = True
                try:
                    rec.dossier_bytes = f.stat().st_size
                except OSError:
                    pass

    if INSIGHTS_DIR.is_dir():
        for f in os.scandir(INSIGHTS_DIR):
            if not f.is_file() or not f.name.endswith(".json"):
                continue
            nl = f.name.lower()
            for slug in persons:
                parts = slug.split("-")
                code = "".join(p[0] for p in parts).lower() if len(parts) >= 2 else ""
                if slug in nl or slug.replace("-", "") in nl or (code and code in nl):
                    persons[slug].insight_count += 1
                    break

    if MINDS_DIR.is_dir():
        for d in os.scandir(MINDS_DIR):
            if d.is_dir() and not d.name.startswith(("_", ".")) and d.name in persons:
                if (Path(d.path) / "AGENT.md").exists():
                    persons[d.name].agent_exists = True

    for rec in persons.values():
        if rec.agent_exists:
            rec.status = "HAS_AGENT"
        elif (
            rec.dna_yaml_count >= MIN_DNA_YAMLS
            and rec.dossier_exists
            and rec.dossier_bytes >= MIN_DOSSIER_BYTES
        ):
            rec.status = "READY"
        elif rec.dna_yaml_count >= MIN_DNA_YAMLS:
            rec.status = "NEEDS_DOSSIER"
        elif rec.dna_yaml_count == 0 and rec.dossier_exists:
            rec.status = "NEEDS_DNA"
        rec.priority = rec.dna_yaml_count * 10 + (rec.dossier_bytes // 1024) + rec.insight_count * 5

    return sorted(persons.values(), key=lambda r: r.priority, reverse=True)


# ═══════════════════════════════════════════════════════════════════
# AXIS 2: CARGO SCAN (auto-discovered from agents/cargo/)
# ═══════════════════════════════════════════════════════════════════


def discover_cargo_roles() -> list[CargoRole]:
    """Auto-discover cargo roles from agents/cargo/{area}/{role}/ filesystem.

    Deduplicates by slug, preferring the entry that has AGENT.md.
    """
    by_slug: dict[str, CargoRole] = {}

    if not CARGO_DIR.is_dir():
        return []

    for area_entry in os.scandir(CARGO_DIR):
        if not area_entry.is_dir() or area_entry.name.startswith("."):
            continue
        area = area_entry.name
        try:
            for role_entry in os.scandir(area_entry.path):
                if not role_entry.is_dir() or role_entry.name.startswith("."):
                    continue
                slug = role_entry.name
                has_agent = (Path(role_entry.path) / "AGENT.md").exists()
                existing = by_slug.get(slug)
                # Keep the entry that has AGENT.md, or first seen
                if existing is None or (has_agent and not existing.has_agent):
                    by_slug[slug] = CargoRole(slug=slug, area=area, has_agent=has_agent)
        except OSError:
            pass

    return list(by_slug.values())


def count_cargo_mentions(roles: list[CargoRole]) -> None:
    """Count keyword mentions in knowledge base files. Mutates roles in place."""
    # Build keyword map: keyword -> role index
    kw_map: list[tuple[str, int]] = []
    for i, role in enumerate(roles):
        # Primary: slug itself and slug without hyphens
        kw_map.append((role.slug, i))
        if "-" in role.slug:
            kw_map.append((role.slug.replace("-", " "), i))
        # Expansions
        for extra in KEYWORD_EXPAND.get(role.slug, []):
            kw_map.append((extra, i))

    # Collect scannable files
    files: list[Path] = []
    if DNA_PERSONS.is_dir():
        for d in os.scandir(DNA_PERSONS):
            if d.is_dir() and not d.name.startswith(("_", ".")):
                try:
                    files.extend(
                        Path(f.path)
                        for f in os.scandir(d.path)
                        if f.is_file() and f.name.endswith((".yaml", ".yml"))
                    )
                except OSError:
                    pass
    if DOSSIER_DIR.is_dir():
        files.extend(
            Path(f.path)
            for f in os.scandir(DOSSIER_DIR)
            if f.is_file() and f.name.endswith(".md") and f.name not in SKIP_FILES
        )

    # Scan each file
    sources_per_role: list[set[str]] = [set() for _ in roles]
    for filepath in files:
        try:
            content = filepath.read_text(errors="ignore").lower()
        except OSError:
            continue
        src = filepath.stem
        for kw, idx in kw_map:
            c = content.count(kw)
            if c > 0:
                roles[idx].mentions += c
                sources_per_role[idx].add(src)

    for i, role in enumerate(roles):
        role.source_count = len(sources_per_role[i])
        if role.has_agent:
            role.status = "HAS_AGENT"
        elif role.mentions >= CARGO_CRITICAL:
            role.status = "CRITICAL"
        elif role.mentions >= CARGO_IMPORTANT:
            role.status = "IMPORTANT"


# ═══════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════


def generate_outputs(persons: list[PersonRecord], cargo: list[CargoRole]) -> tuple[str, dict]:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    p_ready = [p for p in persons if p.status == "READY"]
    c_critical = [r for r in cargo if r.status == "CRITICAL" and not r.has_agent]

    # ── Markdown ──
    lines = [
        "# Agent Discovery - Role Tracking",
        "",
        f"> Auto-generated: {now} | v3.1.0",
        "",
        "## Person Agents (external/)",
        "",
        "| Slug | DNA | Dossier KB | Insights | Agent | Status |",
        "|------|-----|------------|----------|-------|--------|",
    ]
    for p in persons:
        kb = str(p.dossier_bytes // 1024) if p.dossier_exists else "-"
        st = {
            "HAS_AGENT": "`●`",
            "READY": "**READY**",
            "NEEDS_DOSSIER": "~dossier",
            "NEEDS_DNA": "~dna",
        }.get(p.status, "-")
        ag = "Yes" if p.agent_exists else "**No**"
        lines.append(f"| {p.slug} | {p.dna_yaml_count} | {kb} | {p.insight_count} | {ag} | {st} |")

    if p_ready:
        lines.extend(["", "### Create"])
        for p in p_ready:
            lines.append(
                f"- **{p.slug}** — {p.dna_yaml_count} DNA, {p.dossier_bytes // 1024}KB dossier"
            )

    # Cargo by area
    areas: dict[str, list[CargoRole]] = {}
    for r in cargo:
        areas.setdefault(r.area, []).append(r)

    lines.extend(["", "## Cargo Roles", ""])
    for area in sorted(areas):
        lines.append(f"### {area}")
        lines.append("| Role | Mentions | Sources | Agent | Status |")
        lines.append("|------|----------|---------|-------|--------|")
        for r in sorted(areas[area], key=lambda x: x.mentions, reverse=True):
            ag = "Yes" if r.has_agent else "**No**"
            st = {"HAS_AGENT": "`●`", "CRITICAL": "**CRITICAL**", "IMPORTANT": "IMPORTANT"}.get(
                r.status, "Track"
            )
            lines.append(f"| {r.slug} | {r.mentions} | {r.source_count} | {ag} | {st} |")
        lines.append("")

    if c_critical:
        lines.extend(["### Create"])
        for r in c_critical:
            lines.append(f"- **{r.slug}** ({r.area}) — {r.mentions} mentions")
    lines.append("")

    md = "\n".join(lines)

    # ── JSON state ──
    state = {
        "version": "3.1.0",
        "scanned_at": now,
        "persons": [
            {
                "slug": p.slug,
                "status": p.status,
                "dna": p.dna_yaml_count,
                "dossier_kb": p.dossier_bytes // 1024,
                "insights": p.insight_count,
                "has_agent": p.agent_exists,
                "priority": p.priority,
            }
            for p in persons
        ],
        "cargo": [
            {
                "slug": r.slug,
                "area": r.area,
                "mentions": r.mentions,
                "sources": r.source_count,
                "has_agent": r.has_agent,
                "status": r.status,
            }
            for r in cargo
        ],
    }

    return md, state


def build_message(persons: list[PersonRecord], cargo: list[CargoRole]) -> str:
    parts = []
    for p in persons:
        if p.status == "READY":
            parts.append(f"[PERSON READY] {p.slug}")
    for r in cargo:
        if r.status == "CRITICAL" and not r.has_agent:
            parts.append(f"[CARGO CRITICAL] {r.slug} ({r.mentions} mentions)")
    return " | ".join(parts)


def log_events(persons: list[PersonRecord], cargo: list[CargoRole]):
    items = []
    for p in persons:
        if p.status == "READY":
            items.append({"type": "person", "id": p.slug, "status": "READY"})
    for r in cargo:
        if r.status == "CRITICAL" and not r.has_agent:
            items.append(
                {"type": "cargo", "id": r.slug, "status": "CRITICAL", "mentions": r.mentions}
            )
    if not items:
        return
    CREATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    with open(CREATION_LOG, "a") as f:
        for item in items:
            item["timestamp"] = now
            f.write(json.dumps(item) + "\n")


# ═══════════════════════════════════════════════════════════════════
# HOOK ENTRY
# ═══════════════════════════════════════════════════════════════════

WATCHED = ["knowledge/external/dna", "knowledge/external/dossiers", "artifacts/insights"]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:  # noqa: F841
        data = {}

    tool = data.get("tool_name", "")
    path = data.get("tool_input", {}).get("file_path", "")

    if tool not in ("Write", "Edit") or not any(w in path for w in WATCHED):
        print(json.dumps({"continue": True}))
        return

    try:
        persons = scan_persons()
        cargo = discover_cargo_roles()
        count_cargo_mentions(cargo)

        AGENT_DISCOVERY.mkdir(parents=True, exist_ok=True)
        MISSION_CONTROL.mkdir(parents=True, exist_ok=True)

        md, state = generate_outputs(persons, cargo)
        ROLE_TRACKING.write_text(md)
        DISCOVERY_STATE.write_text(json.dumps(state, indent=2))

        msg = build_message(persons, cargo)
        if msg:
            log_events(persons, cargo)
            print(json.dumps({"continue": True, "message": msg}))
        else:
            print(json.dumps({"continue": True}))

    except Exception as e:
        print(json.dumps({"continue": True, "warning": f"Discovery: {e!s}"}))


if __name__ == "__main__":
    main()
