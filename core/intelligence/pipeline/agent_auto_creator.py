"""
agent_auto_creator.py -- MCE Threshold Trigger for Agent Auto-Creation
======================================================================
When a person accumulates 3+ insights across ANY source in INSIGHTS-STATE.json,
this script auto-creates a skeleton AGENT.md using Template V3 structure.

This implements the "MCE threshold is cumulative" rule: it counts insights
across ALL sources (categories, persons, insights list, behavioral_patterns),
not just a single meeting.

Running on an already-created agent is a no-op (idempotent).

Integration model::

    INSIGHTS-STATE.json (cumulative data)
             |
             v
    agent_auto_creator.count_insights_for_person()
             |
             +-- < 3 insights -> skip (below threshold)
             |
             +-- >= 3 insights -> check if AGENT.md exists
                      |
                      +-- exists -> no-op ("agent already exists, skipping")
                      |
                      +-- not exists -> create AGENT.md skeleton
                                |
                                +-- log to agent_creations.jsonl

Bucket routing:
    - scope=course / corpus contains "external" / person in external DNA -> agents/external/{slug}/
    - scope=business / person in behavioral_patterns with bucket=business -> agents/business/collaborators/{slug}/
    - default (no scope info) -> agents/external/{slug}/ (expert default)

Version: 1.0.0
Date: 2026-03-16
Story: W2.2
"""

from __future__ import annotations

import json
import logging
import re
import sys
import unicodedata
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from core.paths import (
    AGENTS_BUSINESS,
    AGENTS_EXTERNAL,
    ARTIFACTS,
    DATA,
    ROOT,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

MCE_INSIGHT_THRESHOLD = 3
INSIGHTS_STATE_PATH = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
AGENT_CREATIONS_LOG = DATA / "agent_memory" / "system" / "agent_creations.jsonl"

# Template V3 version tag
TEMPLATE_VERSION = "AGENT-MD-ULTRA-ROBUSTO-V3"


# ---------------------------------------------------------------------------
# SLUG GENERATION
# ---------------------------------------------------------------------------


def slugify(name: str) -> str:
    """Convert a person name to a filesystem-safe slug.

    Examples:
        "Alex Hormozi" -> "alex-hormozi"
        "Liam Ottley"  -> "liam-ottley"
        "Pedro Valerio" -> "pedro-valerio"
    """
    # Normalize unicode (remove accents)
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


# ---------------------------------------------------------------------------
# INSIGHTS COUNTING
# ---------------------------------------------------------------------------


def load_insights_state() -> dict:
    """Load INSIGHTS-STATE.json. Returns empty dict if file not found."""
    if not INSIGHTS_STATE_PATH.exists():
        logger.warning("INSIGHTS-STATE.json not found at %s", INSIGHTS_STATE_PATH)
        return {}
    with open(INSIGHTS_STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def count_all_person_insights(state: dict) -> dict[str, int]:
    """Count cumulative insights per person across ALL sources in INSIGHTS-STATE.json.

    Searches four data sections:
    1. categories -> insights[] with source_person field
    2. persons -> {PersonName: [insights]}
    3. insights -> [{person: "Name", ...}]
    4. behavioral_patterns -> {slug: {person: "Name", patterns: [...]}}

    Returns dict mapping person name -> total insight count.
    """
    counts: Counter[str] = Counter()

    # 1. Categories (older format with source_person)
    categories = state.get("categories", {})
    for _cat_name, cat_data in categories.items():
        if not isinstance(cat_data, dict):
            continue
        for insight in cat_data.get("insights", []):
            source_person = insight.get("source_person", "")
            if source_person:
                # Normalize slug to title case for dedup
                counts[_normalize_person_name(source_person)] += 1

    # 2. Persons (newer format: name -> [insight objects])
    persons = state.get("persons", {})
    for person_name, insight_list in persons.items():
        if isinstance(insight_list, list) and len(insight_list) > 0:
            # Skip meeting-tagged keys (MEET-XXXX) -- they are source IDs, not persons
            if person_name.startswith("MEET-"):
                continue
            counts[person_name] += len(insight_list)

    # 3. Top-level insights array (e.g. person name entries)
    insights_list = state.get("insights", [])
    if isinstance(insights_list, list):
        for item in insights_list:
            person = item.get("person", "")
            if person:
                counts[person] += 1

    # 4. Behavioral patterns (count pattern entries as insight evidence)
    behavioral = state.get("behavioral_patterns", {})
    for _slug, bp_data in behavioral.items():
        if not isinstance(bp_data, dict):
            continue
        person_name = bp_data.get("person", "")
        patterns = bp_data.get("patterns", [])
        if person_name and isinstance(patterns, list):
            counts[person_name] += len(patterns)

    return dict(counts)


def _normalize_person_name(slug_or_name: str) -> str:
    """Convert a slug like 'alex-hormozi' to title case 'Alex Hormozi'.

    If the input already has spaces (is a name), returns as-is.
    """
    if " " in slug_or_name:
        return slug_or_name
    return slug_or_name.replace("-", " ").title()


# ---------------------------------------------------------------------------
# BUCKET ROUTING
# ---------------------------------------------------------------------------


def determine_bucket(person_name: str, state: dict) -> str:
    """Determine which agent bucket a person belongs to.

    Returns "external" or "business".

    Decision logic:
    1. Check behavioral_patterns for explicit bucket field
    2. Check persons insights for scope field (course -> external)
    3. Check if person already has agent dir in external/ or business/
    4. Default: external (expert assumption)
    """
    slug = slugify(person_name)

    # 1. Check behavioral_patterns for explicit bucket
    behavioral = state.get("behavioral_patterns", {})
    for bp_slug, bp_data in behavioral.items():
        if not isinstance(bp_data, dict):
            continue
        bp_person = bp_data.get("person", "")
        if slugify(bp_person) == slug or bp_slug == slug:
            bucket = bp_data.get("bucket", "")
            if bucket in ("business", "external"):
                return bucket

    # 2. Check persons insights for scope field
    persons = state.get("persons", {})
    person_insights = persons.get(person_name, [])
    if isinstance(person_insights, list):
        for insight in person_insights:
            scope = insight.get("scope", "")
            corpus = insight.get("corpus", "")
            if scope == "course" or "external" in corpus:
                return "external"
            if scope in ("business", "company"):
                return "business"

    # 3. Check if agent dir already exists in either location
    external_path = AGENTS_EXTERNAL / slug
    if external_path.exists():
        return "external"

    business_paths = [
        AGENTS_BUSINESS / "collaborators" / slug,
        AGENTS_BUSINESS / "partners" / slug,
        AGENTS_BUSINESS / "alumni" / slug,
    ]
    for bp in business_paths:
        if bp.exists():
            return "business"

    # 4. Default: external (expert content)
    return "external"


def get_agent_dir(person_name: str, bucket: str) -> Path:
    """Get the target directory for an agent based on bucket.

    External: agents/external/{slug}/
    Business: agents/business/collaborators/{slug}/
    """
    slug = slugify(person_name)
    if bucket == "business":
        return AGENTS_BUSINESS / "collaborators" / slug
    return AGENTS_EXTERNAL / slug


# ---------------------------------------------------------------------------
# AGENT.MD SKELETON GENERATOR
# ---------------------------------------------------------------------------


def generate_agent_skeleton(person_name: str, insight_count: int, bucket: str) -> str:
    """Generate a minimal but valid Template V3 AGENT.md skeleton.

    The skeleton includes:
    - Frontmatter with id, layer, role, version, updated
    - Header block with agent card
    - Dashboard with status indicators (all PENDING except index)
    - PARTE 1 (Composicao Atomica) with placeholder
    - DEPENDENCIES section
    - Placeholders for Parts 2-10

    All content is traceable -- no invented expertise or quotes.
    """
    slug = slugify(person_name)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    layer = "L3" if bucket == "external" else "L2"

    return f"""---
id: {slug}
layer: {layer}
role: "Auto-generated agent (pending enrichment)"
version: "0.1.0"
updated: "{today}"
template: "{TEMPLATE_VERSION}"
auto_created: true
---

# ===============================================================================
# {person_name.upper()} - PERSON AGENT
# ===============================================================================
# ID: @{slug}
# LAYER: {layer} ({"Mind Clone" if bucket == "external" else "Business Collaborator"})
# SOURCE: Auto-created by MCE pipeline ({insight_count} cumulative insights)
# STATUS: SKELETON -- requires enrichment via /process-jarvis Phase 5
# ===============================================================================

```
+==============================================================================+
|                    {person_name.upper()} - AGENT CARD{" " * max(0, 40 - len(person_name))}|
+==============================================================================+
|                                                                              |
|  Tipo:           {"SUPER AGENT - PESSOA (Espelho)" if bucket == "external" else "BUSINESS COLLABORATOR"}{" " * (max(0, 24 - len("SUPER AGENT - PESSOA (Espelho)" if bucket == "external" else "BUSINESS COLLABORATOR")))}|
|  Versao:         0.1.0 (skeleton)                                            |
|  Template:       {TEMPLATE_VERSION}                                   |
|  Maturidade:     10%                                                         |
|  Ultima Update:  {today}                                                  |
|                                                                              |
|  DNA Composition:                                                            |
|  +-- {person_name.upper()}:   100%{" " * max(0, 42 - len(person_name))}|
|  +-- Tipo:         Isolado/Espelho (single-source)                           |
|                                                                              |
|  Insights:       {insight_count} cumulative (threshold: {MCE_INSIGHT_THRESHOLD}+){" " * max(0, 30 - len(str(insight_count)))}|
|                                                                              |
+==============================================================================+
```

---

# ===============================================================================
# PARTE 0: INDICE E DASHBOARD
# ===============================================================================

```
+==============================================================================+
|                            DASHBOARD DE STATUS                               |
+==============================================================================+
|                                                                              |
|  PARTE 0  | Indice             | #################### | 100% | COMPLETE     |
|  PARTE 1  | Composicao Atomica | .................... |   0% | PENDING      |
|  PARTE 2  | Grafico Identidade | .................... |   0% | PENDING      |
|  PARTE 3  | Mapa Neural (DNA)  | .................... |   0% | PENDING      |
|  PARTE 4  | Nucleo Operacional | .................... |   0% | PENDING      |
|  PARTE 5  | Sistema de Voz     | .................... |   0% | PENDING      |
|  PARTE 6  | Motor de Decisao   | .................... |   0% | PENDING      |
|  PARTE 7  | Interfaces Conexao | .................... |   0% | PENDING      |
|  PARTE 8  | Protocolo Debate   | .................... | N/A  | ISOLADO      |
|  PARTE 9  | Memoria Experien.  | .................... |   0% | PENDING      |
|  PARTE 10 | Expansoes e Refs   | .................... |   0% | PENDING      |
|                                                                              |
|  MATURIDADE GERAL: ##.................. 10%                                  |
|                                                                              |
+==============================================================================+
```

> **STATUS:** This is a skeleton agent auto-created by the MCE pipeline.
> All PARTE sections (1-10) require enrichment via `/process-jarvis` Phase 5.
> Insight count at creation: {insight_count}
> Bucket: {bucket}
> Created: {today}

---

## DEPENDENCIES

| Type | Path |
|------|------|
| READS | `artifacts/insights/INSIGHTS-STATE.json` |
| READS | `knowledge/{bucket}/dna/` |
| DEPENDS_ON | Constitution: agent-integrity, agent-traceability |
| DEPENDS_ON | Template: {TEMPLATE_VERSION} |
"""


# ---------------------------------------------------------------------------
# CREATION LOGGER
# ---------------------------------------------------------------------------


def log_creation(person_name: str, slug: str, agent_dir: Path, bucket: str,
                 insight_count: int) -> None:
    """Append creation event to agent_creations.jsonl."""
    AGENT_CREATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": "agent_auto_created",
        "person": person_name,
        "slug": slug,
        "agent_dir": str(agent_dir.relative_to(ROOT)),
        "bucket": bucket,
        "insight_count": insight_count,
        "template": TEMPLATE_VERSION,
        "trigger": "mce_threshold",
        "threshold": MCE_INSIGHT_THRESHOLD,
    }

    with open(AGENT_CREATIONS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info("Logged creation: %s -> %s", person_name, agent_dir)


# ---------------------------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------------------------


def check_and_create_agent(person_name: str, state: dict | None = None,
                           dry_run: bool = False) -> dict:
    """Check if a person meets the MCE threshold and create agent if needed.

    Args:
        person_name: The person's display name (e.g. "Jordan Lee")
        state: Pre-loaded INSIGHTS-STATE dict (loaded if None)
        dry_run: If True, only report what would happen without writing files

    Returns:
        dict with keys: action, person, slug, insight_count, bucket, agent_dir, reason
    """
    if state is None:
        state = load_insights_state()

    slug = slugify(person_name)

    # Count cumulative insights for this person
    all_counts = count_all_person_insights(state)
    insight_count = all_counts.get(person_name, 0)

    result = {
        "person": person_name,
        "slug": slug,
        "insight_count": insight_count,
        "threshold": MCE_INSIGHT_THRESHOLD,
    }

    # Check threshold
    if insight_count < MCE_INSIGHT_THRESHOLD:
        result["action"] = "skip"
        result["reason"] = (
            f"Below threshold: {insight_count} insights "
            f"(need {MCE_INSIGHT_THRESHOLD}+)"
        )
        return result

    # Determine bucket and agent directory
    bucket = determine_bucket(person_name, state)
    agent_dir = get_agent_dir(person_name, bucket)
    agent_file = agent_dir / "AGENT.md"

    result["bucket"] = bucket
    result["agent_dir"] = str(agent_dir.relative_to(ROOT))

    # Idempotency check: agent already exists
    if agent_file.exists():
        result["action"] = "noop"
        result["reason"] = "Agent already exists, skipping"
        print(f"[NOOP] {person_name}: agent already exists at {agent_dir.relative_to(ROOT)}")
        return result

    if dry_run:
        result["action"] = "would_create"
        result["reason"] = f"Would create agent ({insight_count} insights, bucket={bucket})"
        print(f"[DRY-RUN] {person_name}: would create at {agent_dir.relative_to(ROOT)}")
        return result

    # Create agent directory and AGENT.md
    agent_dir.mkdir(parents=True, exist_ok=True)
    skeleton = generate_agent_skeleton(person_name, insight_count, bucket)
    agent_file.write_text(skeleton, encoding="utf-8")

    # Log creation
    log_creation(person_name, slug, agent_dir, bucket, insight_count)

    result["action"] = "created"
    result["reason"] = f"Created agent ({insight_count} insights, bucket={bucket})"
    print(f"[CREATED] {person_name}: {agent_dir.relative_to(ROOT)}/AGENT.md "
          f"({insight_count} insights, bucket={bucket})")
    return result


def scan_all_persons(state: dict | None = None,
                     dry_run: bool = False) -> list[dict]:
    """Scan all persons in INSIGHTS-STATE.json and create agents where needed.

    Args:
        state: Pre-loaded INSIGHTS-STATE dict (loaded if None)
        dry_run: If True, only report what would happen

    Returns:
        List of result dicts from check_and_create_agent
    """
    if state is None:
        state = load_insights_state()

    all_counts = count_all_person_insights(state)
    results = []

    # Sort by insight count descending for clear output
    sorted_persons = sorted(all_counts.items(), key=lambda x: x[1], reverse=True)

    for person_name, count in sorted_persons:
        # Skip meeting IDs (MEET-XXXX)
        if person_name.startswith("MEET-"):
            continue
        result = check_and_create_agent(person_name, state=state, dry_run=dry_run)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for agent_auto_creator.

    Usage:
        python3 -m core.intelligence.pipeline.agent_auto_creator --person "Name"
        python3 -m core.intelligence.pipeline.agent_auto_creator --scan
        python3 -m core.intelligence.pipeline.agent_auto_creator --scan --dry-run
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="MCE threshold trigger: auto-create AGENT.md when insights >= 3"
    )
    parser.add_argument(
        "--person",
        type=str,
        help="Person name to check (e.g. 'Jordan Lee')",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan all persons in INSIGHTS-STATE.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would happen without writing files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not args.person and not args.scan:
        parser.error("Specify --person 'Name' or --scan")

    state = load_insights_state()
    if not state:
        print("[ERROR] Could not load INSIGHTS-STATE.json")
        sys.exit(1)

    if args.person:
        result = check_and_create_agent(args.person, state=state, dry_run=args.dry_run)
        _print_result_summary([result])
    elif args.scan:
        results = scan_all_persons(state=state, dry_run=args.dry_run)
        _print_result_summary(results)


def _print_result_summary(results: list[dict]) -> None:
    """Print a summary table of results."""
    print("\n" + "=" * 72)
    print("AGENT AUTO-CREATOR SUMMARY")
    print("=" * 72)

    created = [r for r in results if r["action"] == "created"]
    noop = [r for r in results if r["action"] == "noop"]
    skipped = [r for r in results if r["action"] == "skip"]
    would_create = [r for r in results if r["action"] == "would_create"]

    print(f"  Created:      {len(created)}")
    print(f"  Already exist: {len(noop)}")
    print(f"  Below threshold: {len(skipped)}")
    if would_create:
        print(f"  Would create: {len(would_create)}")

    print("-" * 72)

    for r in results:
        icon = {
            "created": "+",
            "noop": "=",
            "skip": "-",
            "would_create": "?",
        }.get(r["action"], " ")

        insight_str = f"{r['insight_count']}/{r['threshold']}"
        bucket_str = r.get("bucket", "n/a")
        print(f"  [{icon}] {r['person']:<25} insights={insight_str:<6} "
              f"bucket={bucket_str:<10} {r['reason']}")

    print("=" * 72)


if __name__ == "__main__":
    main()
