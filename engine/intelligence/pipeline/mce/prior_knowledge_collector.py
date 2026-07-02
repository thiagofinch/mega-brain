"""prior_knowledge_collector.py — Collects ALL pre-existing data about a person."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from engine.paths import AGENTS_EXTERNAL, ARTIFACTS, KNOWLEDGE_BUSINESS, KNOWLEDGE_EXTERNAL, ROOT

logger = logging.getLogger("mce.prior_knowledge")


@dataclass
class PriorKnowledge:
    slug: str
    bucket: str = "unknown"
    insights_by_person: str = ""
    insights_by_person_path: str = ""
    insights_state_entries: list = field(default_factory=list)
    dossier_business: str = ""
    dossier_external: str = ""
    agent_memory: str = ""
    thinking_patterns: list = field(default_factory=list)
    profile_summary: str = ""
    total_prior_insights: int = 0
    sources_processed: list = field(default_factory=list)
    locations_found: list = field(default_factory=list)


def _parse_by_person_file(content: str) -> dict:
    """Parse by-person markdown file into structured data."""
    result = {"insights": 0, "patterns": [], "profile": "", "sources": []}
    # Extract meetings processed
    m = re.search(r"Meetings processados:\*\*\s*(.+)", content)
    if m:
        result["sources"] = [s.strip() for s in m.group(1).split(",")]
    # Count table rows (insights)
    result["insights"] = len(re.findall(r"^\|\s*\d+\s*\|", content, re.MULTILINE))
    # Extract patterns
    in_patterns = False
    for line in content.split("\n"):
        if "Padrões de Pensamento" in line or "Padroes de Pensamento" in line:
            in_patterns = True
            continue
        if in_patterns:
            if line.startswith("- "):
                result["patterns"].append(line.lstrip("- ").strip())
            elif line.startswith("#") or line.startswith("---"):
                in_patterns = False
    # Extract profile
    in_profile = False
    profile_lines = []
    for line in content.split("\n"):
        if "## Perfil" in line:
            in_profile = True
            continue
        if in_profile:
            if line.startswith("#") or line.startswith("---"):
                in_profile = False
            elif line.strip():
                profile_lines.append(line.lstrip("- ").strip())
    result["profile"] = "; ".join(profile_lines)
    return result


def _find_dossier(base_dir: Path, slug: str) -> Path | None:
    """Find dossier by slug with fuzzy matching."""
    if not base_dir.exists():
        return None
    slug_upper = slug.upper().replace("-", " ").replace("_", " ")
    slug_parts = slug.split("-")
    for f in base_dir.glob("DOSSIER-*.md"):
        fname = f.stem.upper().replace("-", " ")
        if all(p.upper() in fname for p in slug_parts):
            return f
    return None


def collect_prior_knowledge(slug: str) -> PriorKnowledge:
    """Scan all locations for pre-existing data about a person."""
    pk = PriorKnowledge(slug=slug)
    # 1. by-person insights
    try:
        for bucket_name, bucket_dir in [
            ("business", KNOWLEDGE_BUSINESS),
            ("external", KNOWLEDGE_EXTERNAL),
        ]:
            bp = bucket_dir / "insights" / "by-person" / f"{slug}.md"
            if bp.exists():
                content = bp.read_text(encoding="utf-8")
                pk.insights_by_person = content
                pk.insights_by_person_path = str(bp)
                pk.bucket = bucket_name
                pk.locations_found.append(str(bp))
                parsed = _parse_by_person_file(content)
                pk.total_prior_insights += parsed["insights"]
                pk.thinking_patterns = parsed["patterns"]
                pk.profile_summary = parsed["profile"]
                pk.sources_processed = parsed["sources"]
                break
    except Exception as e:
        logger.warning("by-person scan failed: %s", e)
    # 2. Dossiers
    try:
        for label, ddir in [
            ("business", KNOWLEDGE_BUSINESS / "dossiers" / "persons"),
            ("external", KNOWLEDGE_EXTERNAL / "dossiers" / "persons"),
        ]:
            d = _find_dossier(ddir, slug)
            if d:
                content = d.read_text(encoding="utf-8")
                if label == "business":
                    pk.dossier_business = content
                else:
                    pk.dossier_external = content
                pk.locations_found.append(str(d))
                if pk.bucket == "unknown":
                    pk.bucket = label
    except Exception as e:
        logger.warning("dossier scan failed: %s", e)
    # 3. INSIGHTS-STATE.json
    try:
        ipath = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
        if ipath.exists():
            data = json.loads(ipath.read_text(encoding="utf-8"))
            persons = data.get("persons", {})
            # Try exact match and title-case variants
            person_name = " ".join(w.capitalize() for w in slug.split("-"))
            for variant in [person_name, slug]:
                if variant in persons:
                    entry = persons[variant]
                    if isinstance(entry, dict):
                        pk.insights_state_entries = entry.get("insights", [])
                    elif isinstance(entry, list):
                        pk.insights_state_entries = entry
                    pk.locations_found.append(str(ipath))
                    break
            # Also count from flat insights
            flat = data.get("insights", [])
            flat_for_person = [
                i
                for i in flat
                if i.get("person", "").lower().replace("é", "e")
                == person_name.lower().replace("é", "e")
            ]
            if flat_for_person and not pk.insights_state_entries:
                pk.insights_state_entries = flat_for_person
            pk.total_prior_insights += len(pk.insights_state_entries)
    except Exception as e:
        logger.warning("INSIGHTS-STATE scan failed: %s", e)
    # 4. Agent MEMORY.md
    try:
        for agent_base in [AGENTS_EXTERNAL / slug, ROOT / "agents" / "business"]:
            if agent_base.is_dir():
                mem = agent_base / "MEMORY.md"
                if mem.exists():
                    pk.agent_memory = mem.read_text(encoding="utf-8")
                    pk.locations_found.append(str(mem))
                    break
            # Check subdirs for business
            if agent_base == ROOT / "agents" / "business" and agent_base.exists():
                for sub in agent_base.rglob(f"{slug}/MEMORY.md"):
                    pk.agent_memory = sub.read_text(encoding="utf-8")
                    pk.locations_found.append(str(sub))
                    break
    except Exception as e:
        logger.warning("agent memory scan failed: %s", e)
    logger.info(
        "Prior knowledge for %s: %d insights, %d locations",
        slug,
        pk.total_prior_insights,
        len(pk.locations_found),
    )
    return pk
