#!/usr/bin/env python3
"""
ORG CHAIN DETECTOR - Intelligence Layer v1.0
==============================================
Detecta padroes hierarquicos e cadeia organizacional no texto dos chunks.

Detecta:
1. Hierarquia explicita: "[ROLE] reporta ao [ROLE]", "manages [N] [ROLES]"
2. Job descriptions implicitas: responsabilidades, KPIs, metricas
3. Relacoes de equipe: "team of [N]", "[N] reps", "my team"
4. Progression paths: "promote from [ROLE] to [ROLE]"

Registra relacoes no ENTITY-REGISTRY.
Gera SOW skeleton para roles novos.

Versao: 1.0.0
Data: 2026-02-24
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, save_registry, normalize_text

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
CHUNKS_DIR = BASE_DIR / "processing" / "chunks"

# ---------------------------------------------------------------------------
# HIERARCHY PATTERNS
# ---------------------------------------------------------------------------

# Pattern: [ROLE] reports to / reporta ao [ROLE]
REPORTS_TO_PATTERNS = [
    r"(\w[\w\s-]{2,30})\s+(?:reports?\s+to|reporta\s+(?:ao?|para))\s+(?:the\s+)?(\w[\w\s-]{2,30})",
    r"(\w[\w\s-]{2,30})\s+(?:under|underneath|below)\s+(?:the\s+)?(\w[\w\s-]{2,30})",
    r"(?:the\s+)?(\w[\w\s-]{2,30})\s+(?:is\s+)?(?:managed|supervised)\s+by\s+(?:the\s+)?(\w[\w\s-]{2,30})",
]

# Pattern: [ROLE] manages / gerencia [N] [ROLES]
MANAGES_PATTERNS = [
    r"(\w[\w\s-]{2,30})\s+(?:manages?|gerencia|lidera|leads?)\s+(?:a\s+team\s+of\s+)?(\d+)\s+(\w[\w\s-]{2,30})",
    r"(\w[\w\s-]{2,30})\s+(?:manages?|gerencia|supervises?)\s+(?:the\s+)?(\w[\w\s-]{2,30})\s+team",
    r"(?:the\s+)?(\w[\w\s-]{2,30})\s+(?:has|have)\s+(\d+)\s+(\w[\w\s-]{2,30})\s+(?:on\s+(?:their|the)\s+team|reporting)",
]

# Pattern: team structure and sizes
TEAM_SIZE_PATTERNS = [
    r"(?:team\s+of|equipe\s+de)\s+(\d+)\s+(\w[\w\s-]{2,30})",
    r"(\d+)\s+(\w[\w\s-]{2,30})\s+(?:on\s+(?:the|my|our)\s+team|reps?|vendedores|closers?|setters?|bdrs?)",
    r"(?:hire|contratar)\s+(\d+)\s+(\w[\w\s-]{2,30})",
]

# Pattern: progression / promotion
PROGRESSION_PATTERNS = [
    r"(?:promote|promover)\s+(?:from\s+)?(\w[\w\s-]{2,30})\s+(?:to|para)\s+(\w[\w\s-]{2,30})",
    r"(\w[\w\s-]{2,30})\s+(?:evolves?|progresses?|advances?)\s+(?:to|into)\s+(\w[\w\s-]{2,30})",
    r"(?:path|caminho|carreira)\s+(?:from\s+)?(\w[\w\s-]{2,30})\s+(?:to|para|->|→)\s+(\w[\w\s-]{2,30})",
]

# Pattern: responsibilities / KPIs
RESPONSIBILITY_PATTERNS = [
    r"(?:the\s+)?(\w[\w\s-]{2,30})\s+(?:is\s+)?responsible\s+for\s+(.{10,100}?)(?:\.|,|;|\n)",
    r"(?:the\s+)?(\w[\w\s-]{2,30})\s+(?:must|should|needs?\s+to|precisa|deve)\s+(.{10,100}?)(?:\.|,|;|\n)",
    r"(?:the\s+)?(\w[\w\s-]{2,30})(?:'s|s)\s+(?:job|role|responsibilit(?:y|ies))\s+(?:is|are|includes?)\s+(.{10,100}?)(?:\.|,|;|\n)",
]

# Pattern: KPIs and metrics
KPI_PATTERNS = [
    r"(\w[\w\s-]{2,30})\s+(?:should\s+)?(?:hit|reach|achieve|make|do)\s+(\d+[\+]?)\s+(.{5,50}?)(?:\s+(?:per|a|cada)\s+(?:day|week|month|dia|semana|mes))",
    r"(\d+[\+]?)\s+(.{5,50}?)\s+(?:per|a|cada)\s+(?:day|week|month|dia|semana|mes)\s+(?:for|para)\s+(?:the\s+)?(\w[\w\s-]{2,30})",
]

# Known role keywords for matching
KNOWN_ROLES = {
    "closer", "closers", "bdr", "bdrs", "sdr", "sdrs", "sds",
    "setter", "setters", "sales manager", "sales lead",
    "sales coordinator", "lns", "customer success",
    "cro", "cfo", "cmo", "coo", "hr director",
    "rep", "reps", "sales rep", "sales reps",
    "manager", "managers", "lead", "leads",
    "vendedor", "vendedores", "gerente", "coordenador",
}


# ---------------------------------------------------------------------------
# CORE: DETECT ORG CHAINS
# ---------------------------------------------------------------------------
def detect_org_patterns(text, source_id=None):
    """
    Detect organizational chain patterns in text.

    Returns:
        {
            "hierarchy": [{superior, subordinate, type, context}],
            "team_sizes": [{role, size, context}],
            "progressions": [{from_role, to_role, context}],
            "responsibilities": [{role, responsibility, context}],
            "kpis": [{role, metric, value, period, context}],
        }
    """
    text_lower = text.lower()
    results = {
        "hierarchy": [],
        "team_sizes": [],
        "progressions": [],
        "responsibilities": [],
        "kpis": [],
    }

    # Detect hierarchy (reports to)
    for pattern in REPORTS_TO_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            subordinate = _clean_role(match.group(1))
            superior = _clean_role(match.group(2))
            if _is_likely_role(subordinate) or _is_likely_role(superior):
                results["hierarchy"].append({
                    "subordinate": subordinate,
                    "superior": superior,
                    "relation": "reports_to",
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect manages patterns
    for pattern in MANAGES_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            groups = match.groups()
            if len(groups) == 3:
                superior = _clean_role(groups[0])
                count = groups[1]
                subordinate = _clean_role(groups[2])
            else:
                superior = _clean_role(groups[0])
                subordinate = _clean_role(groups[1])
                count = "?"
            if _is_likely_role(superior) or _is_likely_role(subordinate):
                results["hierarchy"].append({
                    "superior": superior,
                    "subordinate": subordinate,
                    "relation": "manages",
                    "count": count,
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect team sizes
    for pattern in TEAM_SIZE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            groups = match.groups()
            size = groups[0]
            role = _clean_role(groups[1])
            if _is_likely_role(role):
                results["team_sizes"].append({
                    "role": role,
                    "size": int(size) if size.isdigit() else size,
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect progressions
    for pattern in PROGRESSION_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            from_role = _clean_role(match.group(1))
            to_role = _clean_role(match.group(2))
            if _is_likely_role(from_role) or _is_likely_role(to_role):
                results["progressions"].append({
                    "from_role": from_role,
                    "to_role": to_role,
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect responsibilities
    for pattern in RESPONSIBILITY_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            role = _clean_role(match.group(1))
            responsibility = match.group(2).strip()
            if _is_likely_role(role):
                results["responsibilities"].append({
                    "role": role,
                    "responsibility": responsibility,
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect KPIs
    for pattern in KPI_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            groups = match.groups()
            if len(groups) == 3:
                if groups[0].isdigit() or "+" in groups[0]:
                    # Pattern: 100 calls per day for BDR
                    value = groups[0]
                    metric = groups[1].strip()
                    role = _clean_role(groups[2])
                else:
                    # Pattern: BDR should hit 100 calls per day
                    role = _clean_role(groups[0])
                    value = groups[1]
                    metric = groups[2].strip()
                if _is_likely_role(role):
                    results["kpis"].append({
                        "role": role,
                        "metric": metric,
                        "value": value,
                        "context": _extract_ctx(text, match.start(), match.end()),
                        "source_id": source_id,
                    })

    return results


def detect_org_in_file(filepath, registry=None):
    """Detect org patterns across all chunks in a file."""
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_id = data.get("source_id", data.get("source_hash", filepath.stem))

    if "chunks" in data:
        chunks = data["chunks"]
    else:
        chunks = [data]

    all_results = {
        "hierarchy": [],
        "team_sizes": [],
        "progressions": [],
        "responsibilities": [],
        "kpis": [],
    }

    for chunk in chunks:
        text = chunk.get("content", "") or chunk.get("texto", "") or chunk.get("text", "")
        if not text:
            continue

        result = detect_org_patterns(text, source_id=source_id)
        for key in all_results:
            all_results[key].extend(result[key])

    # Update registry with discovered responsibilities
    if registry:
        _update_registry_with_org_data(all_results, registry)

    return {
        "source_id": source_id,
        "chunk_count": len(chunks),
        **{k: len(v) for k, v in all_results.items()},
        "details": all_results,
    }


def scan_all_chunks(registry=None, save=True):
    """Scan ALL chunk files for org patterns."""
    if registry is None:
        registry = load_registry()

    all_hierarchy = []
    all_team_sizes = []
    all_progressions = []
    all_responsibilities = []
    all_kpis = []
    files_scanned = 0

    for fpath in sorted(CHUNKS_DIR.glob("*.json")):
        if fpath.name in ("CHUNKS-STATE.json", "_INDEX.json", "_rag_export.json"):
            continue

        result = detect_org_in_file(fpath, registry=registry)
        files_scanned += 1

        all_hierarchy.extend(result["details"]["hierarchy"])
        all_team_sizes.extend(result["details"]["team_sizes"])
        all_progressions.extend(result["details"]["progressions"])
        all_responsibilities.extend(result["details"]["responsibilities"])
        all_kpis.extend(result["details"]["kpis"])

    if save:
        save_registry(registry)

    return {
        "files_scanned": files_scanned,
        "hierarchy_relations": len(all_hierarchy),
        "team_sizes_found": len(all_team_sizes),
        "progressions_found": len(all_progressions),
        "responsibilities_found": len(all_responsibilities),
        "kpis_found": len(all_kpis),
        "hierarchy": all_hierarchy,
        "team_sizes": all_team_sizes,
        "progressions": all_progressions,
        "responsibilities": all_responsibilities,
        "kpis": all_kpis,
    }


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _clean_role(text):
    """Clean and normalize a role name extracted from regex."""
    text = text.strip()
    # Remove common leading articles
    text = re.sub(r"^(?:the|a|an|o|a|um|uma|cada)\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def _is_likely_role(text):
    """Check if extracted text is likely a role/position."""
    norm = normalize_text(text)
    if norm in KNOWN_ROLES:
        return True
    # Check partial matches
    for role in KNOWN_ROLES:
        if role in norm or norm in role:
            return True
    return False


def _extract_ctx(text, start, end, window=60):
    """Extract context around match."""
    s = max(0, start - window)
    e = min(len(text), end + window)
    ctx = text[s:e].strip()
    if s > 0:
        ctx = "..." + ctx
    if e < len(text):
        ctx = ctx + "..."
    return ctx


def _update_registry_with_org_data(org_results, registry):
    """Update ENTITY-REGISTRY with org chain data."""
    roles = registry.get("roles", {})

    for resp in org_results["responsibilities"]:
        role_name = resp["role"].upper().replace(" ", "-")
        if role_name in roles:
            existing = roles[role_name].get("responsibilities", [])
            if resp["responsibility"] not in existing:
                existing.append(resp["responsibility"])
                roles[role_name]["responsibilities"] = existing[:20]  # cap at 20

    for rel in org_results["hierarchy"]:
        sup = rel.get("superior", "").upper().replace(" ", "-")
        sub = rel.get("subordinate", "").upper().replace(" ", "-")
        if sup in roles:
            reports = roles[sup].setdefault("direct_reports", [])
            if sub not in reports:
                reports.append(sub)
        if sub in roles:
            roles[sub]["reports_to"] = sup


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== ORG CHAIN DETECTOR: Full Scan ===\n")
        result = scan_all_chunks(save=True)
        print(f"Files scanned:       {result['files_scanned']}")
        print(f"Hierarchy relations: {result['hierarchy_relations']}")
        print(f"Team sizes found:    {result['team_sizes_found']}")
        print(f"Progressions:        {result['progressions_found']}")
        print(f"Responsibilities:    {result['responsibilities_found']}")
        print(f"KPIs found:          {result['kpis_found']}")

        if result["hierarchy"]:
            print(f"\n--- Hierarchy ---")
            for h in result["hierarchy"][:15]:
                print(f"  {h['superior']} -> {h['subordinate']} ({h['relation']})")

        if result["team_sizes"]:
            print(f"\n--- Team Sizes ---")
            for t in result["team_sizes"][:10]:
                print(f"  {t['size']}x {t['role']}")

        if result["kpis"]:
            print(f"\n--- KPIs ---")
            for k in result["kpis"][:10]:
                print(f"  {k['role']}: {k['value']} {k['metric']}")

        if result["responsibilities"]:
            print(f"\n--- Top Responsibilities ---")
            for r in result["responsibilities"][:10]:
                print(f"  {r['role']}: {r['responsibility'][:80]}")

    elif len(sys.argv) > 1:
        filepath = sys.argv[1]
        result = detect_org_in_file(filepath)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    else:
        print("Uso:")
        print("  python3 org_chain_detector.py --all        # Scan all chunks")
        print("  python3 org_chain_detector.py <filepath>   # Scan single file")
        sys.exit(1)


if __name__ == "__main__":
    main()
