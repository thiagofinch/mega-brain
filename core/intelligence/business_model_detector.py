#!/usr/bin/env python3
"""
BUSINESS MODEL DETECTOR - Intelligence Layer v1.0
===================================================
Detecta estrutura organizacional e modelo de negocio de entidades absorvidas.

Detecta:
1. Departamentos e divisoes
2. Team sizes e estrutura
3. Revenue signals e ticket medio
4. Role consolidation (1 pessoa, 2+ cargos)
5. Cadeia organizacional completa (role_chain)

Alimenta campo `business_model` no ENTITY-REGISTRY para cada pessoa.

Dependencias: Sprint 4 completo (roles com weighted_score)
Inspiracao: MMOS Layers 6-8, org_chain_detector existente

Versao: 1.0.0
Data: 2026-02-26
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
# DETECTION PATTERNS
# ---------------------------------------------------------------------------

DEPARTMENT_PATTERNS = [
    r"(?:our|my|the|nosso|meu)\s+(\w+(?:\s+\w+)?)\s+(?:team|department|division|equipe|setor|area)",
    r"(?:head|director|VP|gerente|chefe|lider)\s+(?:of|de|do|da)\s+(\w+(?:\s+\w+)?)",
    r"(?:the|o|a)\s+(\w+(?:\s+\w+)?)\s+(?:side|arm|wing|parte|braco)\s+of\s+(?:the\s+)?(?:business|company|empresa)",
    r"(?:we\s+have|temos)\s+(?:a|an|um|uma)\s+(\w+(?:\s+\w+)?)\s+(?:team|department|equipe)",
]

TEAM_SIZE_PATTERNS = [
    r"(\d+)\s*[-–]?\s*(?:person|people|member|pessoa|funcionario|employee)\s+(?:team|equipe|company|empresa)",
    r"(?:team|equipe)\s+(?:of|de|com)\s+(\d+)",
    r"(?:we\s+have|temos|there(?:'s| are))\s+(\d+)\s+(?:people|employees|team members|pessoas|funcionarios)",
    r"(\d+)\s+(?:full[- ]time|part[- ]time|contractors?|freelancers?)",
    r"(?:grow|grew|scale[d]?)\s+(?:to|from\s+\d+\s+to)\s+(\d+)\s+(?:people|employees|team|reps)",
]

REVENUE_PATTERNS = [
    r"(?:revenue|faturamento|receita|sales|vendas).*?(?:\$|R\$)\s*([\d,.]+)\s*([KMBkmb](?:illion|ilhao|ilhoes)?)?",
    r"(?:\$|R\$)\s*([\d,.]+)\s*([KMBkmb](?:illion|ilhao|ilhoes)?)?\s*(?:per|a|por)\s+(?:month|year|ano|mes)",
    r"(?:ticket|preco|price|aov|average order).*?(?:\$|R\$)\s*([\d,.]+)",
    r"(?:made|fez|gerou|generated)\s+(?:\$|R\$)\s*([\d,.]+)\s*([KMBkmb](?:illion|ilhao|ilhoes)?)?",
    r"(\d+)\s*(?:figure|digitos)\s+(?:business|empresa|negocio)",
]

ROLE_CONSOLIDATION_PATTERNS = [
    r"(\w+(?:\s+\w+)?)\s+(?:also|tambem|e\s+tambem)\s+(?:handles?|does|faz|cuida\s+de?|manages?)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
    r"(?:wears?\s+(?:many|multiple|varios|muitos)\s+hats?)",
    r"(?:one\s+person|uma\s+pessoa)\s+(?:doing|fazendo|handling)\s+(?:both|dois|ambos)\s+(\w+(?:\s+\w+)?)\s+(?:and|e)\s+(\w+(?:\s+\w+)?)",
    r"(\w+(?:\s+\w+)?)\s+(?:doubles?\s+as|serve[s]?\s+as|funciona\s+como)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
    r"(?:before\s+you\s+)?(?:split|separate|dividir|separar)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:and|e|from|de?)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
]

# Departments normalization map
DEPARTMENT_ALIASES = {
    "sales": "Sales", "vendas": "Sales", "comercial": "Sales",
    "marketing": "Marketing", "mkt": "Marketing",
    "ops": "Operations", "operations": "Operations", "operacoes": "Operations",
    "hr": "Human Resources", "people": "Human Resources", "rh": "Human Resources",
    "finance": "Finance", "financeiro": "Finance",
    "product": "Product", "produto": "Product",
    "engineering": "Engineering", "tech": "Engineering", "dev": "Engineering",
    "customer": "Customer Success", "cs": "Customer Success", "suporte": "Customer Success",
    "content": "Content", "conteudo": "Content",
    "acquisition": "Acquisition", "aquisicao": "Acquisition",
    "growth": "Growth", "crescimento": "Growth",
    "design": "Design", "creative": "Design",
    "legal": "Legal", "juridico": "Legal",
}


# ---------------------------------------------------------------------------
# CORE: DETECT BUSINESS MODEL
# ---------------------------------------------------------------------------
def detect_business_model(text, source_id=None):
    """
    Detect business model patterns in text.

    Returns:
        {
            "departments": [{name, context}],
            "team_sizes": [{size, context, role}],
            "revenue_signals": [{amount, context}],
            "role_consolidation": [{roles, evidence}],
        }
    """
    text_lower = text.lower()
    results = {
        "departments": [],
        "team_sizes": [],
        "revenue_signals": [],
        "role_consolidation": [],
    }

    # Detect departments
    for pattern in DEPARTMENT_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            dept_raw = match.group(1).strip()
            dept_norm = _normalize_department(dept_raw)
            if dept_norm:
                results["departments"].append({
                    "name": dept_norm,
                    "raw": dept_raw,
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect team sizes
    for pattern in TEAM_SIZE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            size_str = match.group(1)
            if size_str.isdigit():
                size = int(size_str)
                if 1 <= size <= 100000:  # sanity check
                    results["team_sizes"].append({
                        "size": size,
                        "context": _extract_ctx(text, match.start(), match.end()),
                        "source_id": source_id,
                    })

    # Detect revenue signals
    for pattern in REVENUE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            groups = match.groups()
            amount_str = groups[0]
            multiplier = groups[1] if len(groups) > 1 else None
            amount = _parse_amount(amount_str, multiplier)
            if amount:
                results["revenue_signals"].append({
                    "amount": amount,
                    "raw": match.group(0).strip(),
                    "context": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    # Detect role consolidation
    for pattern in ROLE_CONSOLIDATION_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            groups = match.groups()
            if len(groups) >= 2:
                role1 = groups[0].strip() if groups[0] else None
                role2 = groups[1].strip() if groups[1] else None
                if role1 and role2:
                    results["role_consolidation"].append({
                        "roles": [role1.upper(), role2.upper()],
                        "evidence": _extract_ctx(text, match.start(), match.end()),
                        "source_id": source_id,
                    })
            elif "hats" in match.group(0) or "chapeus" in match.group(0):
                results["role_consolidation"].append({
                    "roles": ["MULTIPLE"],
                    "evidence": _extract_ctx(text, match.start(), match.end()),
                    "source_id": source_id,
                })

    return results


def detect_in_file(filepath, registry=None):
    """Detect business model patterns across all chunks in a file."""
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_id = data.get("source_id", data.get("source_hash", filepath.stem))

    if "chunks" in data:
        chunks = data["chunks"]
    else:
        chunks = [data]

    all_results = {
        "departments": [],
        "team_sizes": [],
        "revenue_signals": [],
        "role_consolidation": [],
    }

    for chunk in chunks:
        text = chunk.get("content", "") or chunk.get("texto", "") or chunk.get("text", "")
        if not text:
            continue

        result = detect_business_model(text, source_id=source_id)
        for key in all_results:
            all_results[key].extend(result[key])

    return {
        "source_id": source_id,
        "chunk_count": len(chunks),
        **{k: len(v) for k, v in all_results.items()},
        "details": all_results,
    }


def scan_all_chunks(registry=None, save=True):
    """Scan ALL chunk files for business model patterns."""
    if registry is None:
        registry = load_registry()

    # Aggregate per person
    person_models = defaultdict(lambda: {
        "departments": [],
        "team_sizes": [],
        "revenue_signals": [],
        "role_consolidation": [],
        "sources": set(),
    })

    files_scanned = 0
    total_depts = 0
    total_sizes = 0
    total_revenue = 0
    total_consolidation = 0

    for fpath in sorted(CHUNKS_DIR.glob("*.json")):
        if fpath.name in ("CHUNKS-STATE.json", "_INDEX.json", "_rag_export.json"):
            continue

        result = detect_in_file(fpath, registry=registry)
        files_scanned += 1
        source_id = result["source_id"]

        total_depts += result["departments"]
        total_sizes += result["team_sizes"]
        total_revenue += result["revenue_signals"]
        total_consolidation += result["role_consolidation"]

        # Associate findings with persons from the same source
        persons = registry.get("persons", {})
        associated_person = _find_person_for_source(source_id, persons)

        if associated_person:
            pm = person_models[associated_person]
            pm["departments"].extend(result["details"]["departments"])
            pm["team_sizes"].extend(result["details"]["team_sizes"])
            pm["revenue_signals"].extend(result["details"]["revenue_signals"])
            pm["role_consolidation"].extend(result["details"]["role_consolidation"])
            pm["sources"].add(source_id)

    # Update registry with business models
    if save:
        _update_registry_business_models(person_models, registry)
        save_registry(registry)

    return {
        "files_scanned": files_scanned,
        "total_departments": total_depts,
        "total_team_sizes": total_sizes,
        "total_revenue_signals": total_revenue,
        "total_role_consolidation": total_consolidation,
        "persons_with_models": len(person_models),
        "person_details": {
            k: {
                "departments": len(v["departments"]),
                "team_sizes": len(v["team_sizes"]),
                "revenue_signals": len(v["revenue_signals"]),
                "role_consolidation": len(v["role_consolidation"]),
            }
            for k, v in person_models.items()
        },
    }


# ---------------------------------------------------------------------------
# REGISTRY INTEGRATION
# ---------------------------------------------------------------------------
def _update_registry_business_models(person_models, registry):
    """Update ENTITY-REGISTRY with business model data."""
    persons = registry.get("persons", {})
    roles = registry.get("roles", {})

    for person_name, model_data in person_models.items():
        if person_name not in persons:
            continue

        # Deduplicate departments
        dept_names = list(set(d["name"] for d in model_data["departments"]))

        # Aggregate team sizes (take max per mention)
        sizes = [t["size"] for t in model_data["team_sizes"]]
        size_estimate = _estimate_team_size(sizes)

        # Aggregate revenue signals
        revenue_sigs = list(set(r["amount"] for r in model_data["revenue_signals"]))

        # Build role chain from existing registry roles
        role_chain = _build_role_chain(roles)

        # Role consolidation
        consolidations = []
        seen = set()
        for rc in model_data["role_consolidation"]:
            key = tuple(sorted(rc["roles"]))
            if key not in seen:
                seen.add(key)
                consolidations.append({
                    "roles": rc["roles"],
                    "evidence": rc["evidence"],
                })

        has_data = (dept_names or sizes or revenue_sigs or consolidations)

        persons[person_name]["business_model"] = {
            "detected": has_data,
            "departments": dept_names[:20],
            "team_size_estimate": size_estimate,
            "revenue_signals": revenue_sigs[:10],
            "role_chain": role_chain,
            "role_consolidation": consolidations[:10],
            "sources_analyzed": len(model_data["sources"]),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


def _build_role_chain(roles):
    """Build role chain from registry role data (reports_to, direct_reports)."""
    chain = {}
    for role_name, role_data in roles.items():
        reports_to = role_data.get("reports_to")
        direct_reports = role_data.get("direct_reports", [])
        if reports_to or direct_reports:
            chain[role_name] = {
                "reports_to": reports_to,
                "manages": direct_reports,
            }
    return chain


def _find_person_for_source(source_id, persons):
    """Find which person is associated with a source_id."""
    if not source_id:
        return None

    source_lower = source_id.lower()

    # Try matching by source presence in person's sources
    for person_name, pdata in persons.items():
        sources = pdata.get("sources", [])
        for s in sources:
            if s.lower() == source_lower or source_lower in s.lower():
                return person_name

    # Heuristic: match by person name fragments in source_id
    for person_name in persons:
        name_parts = person_name.lower().split()
        for part in name_parts:
            if len(part) > 3 and part in source_lower:
                return person_name

    return None


def _estimate_team_size(sizes):
    """Estimate team size from multiple signals."""
    if not sizes:
        return "unknown"
    max_size = max(sizes)
    if max_size <= 10:
        return "1-10"
    elif max_size <= 50:
        return "10-50"
    elif max_size <= 200:
        return "50-200"
    elif max_size <= 1000:
        return "200-1000"
    else:
        return "1000+"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _normalize_department(raw):
    """Normalize department name from raw text."""
    raw_lower = raw.strip().lower()
    for alias, norm in DEPARTMENT_ALIASES.items():
        if alias in raw_lower:
            return norm
    # Return capitalized if reasonable length
    if 2 <= len(raw) <= 30:
        return raw.title()
    return None


def _parse_amount(amount_str, multiplier=None):
    """Parse monetary amount from string."""
    try:
        clean = amount_str.replace(",", "").replace(".", "")
        if not clean:
            return None
        num = float(clean)
        if multiplier:
            m = multiplier.lower()[0]
            if m == "k":
                num *= 1000
            elif m == "m":
                num *= 1000000
            elif m == "b":
                num *= 1000000000
        if num > 100:
            return f"${num:,.0f}"
        return None
    except (ValueError, IndexError):
        return None


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== BUSINESS MODEL DETECTOR v1.0: Full Scan ===\n")
        result = scan_all_chunks(save=True)
        print(f"Files scanned:          {result['files_scanned']}")
        print(f"Departments found:      {result['total_departments']}")
        print(f"Team sizes found:       {result['total_team_sizes']}")
        print(f"Revenue signals:        {result['total_revenue_signals']}")
        print(f"Role consolidation:     {result['total_role_consolidation']}")
        print(f"Persons with models:    {result['persons_with_models']}")

        if result["person_details"]:
            print(f"\n--- Person Business Models ---")
            for person, details in result["person_details"].items():
                print(f"  {person}:")
                print(f"    Departments: {details['departments']}")
                print(f"    Team sizes: {details['team_sizes']}")
                print(f"    Revenue signals: {details['revenue_signals']}")
                print(f"    Role consolidation: {details['role_consolidation']}")

    elif len(sys.argv) > 1:
        filepath = sys.argv[1]
        result = detect_in_file(filepath)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    else:
        print("Uso:")
        print("  python3 business_model_detector.py --all        # Scan all chunks")
        print("  python3 business_model_detector.py <filepath>   # Scan single file")
        sys.exit(1)


if __name__ == "__main__":
    main()
