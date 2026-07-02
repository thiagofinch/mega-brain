"""domain_aggregator.py — MAP-CONFLITOS cross-source per-domain (Story MCE-4.5).

Operates at the DOMAIN level, across multiple expert slugs that contribute to
the same AGG-{DOMAIN}.yaml.  This is intentionally NOT inside mce/ because
it does not process a single slug — it aggregates insights across all slugs
in a domain (roundtable 2026-05-17, Posicao #5).

Public API (exactly 3 functions):
    aggregate_domain_conflicts(domain, *, root=None) -> dict[str, Any]
    detect_cross_source_conflict(slug_a, slug_b, domain, *, root=None) -> list[dict[str, Any]]
    classify_conflict_type(conflict) -> str

Stack: stdlib + PyYAML only.  Zero LLM.  Zero imports of orchestrate.py.
Lazy import of contradiction_detector (avoids heavy import chain at module load).

Cross-source bridge decision (F1 from @po review):
    contradiction_detector.detect(person_slug, insights) processes contradictions
    WITHIN a single slug's insight list.  For cross-source comparison we need
    contradictions BETWEEN slug_a insights and slug_b insights.

    Option A (rejected): concatenate insights_a + insights_b and call detect()
    once — but this confuses the semantics: detect() uses person_slug for ID
    generation and the ID would embed the wrong slug for half the insights.
    Also, detect() skips self-comparison by ID, which could silently drop
    valid cross-slug pairs when IDs collide.

    Option B (chosen): load insights for slug_a and slug_b independently, then
    perform a direct cross-product comparison using the same internal keyword
    logic (_find_triggered_pair-equivalent) reimplemented here without importing
    private symbols.  This is more defensively isolated — domain_aggregator
    never touches orchestrate.py internals, and the cross-source comparison is
    semantically clean: we explicitly compare ONE insight from slug_a against
    ONE insight from slug_b, never same-slug pairs.

    Documented inline per @po F1 requirement.
"""

from __future__ import annotations

import hashlib
import itertools
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML
except ImportError as _err:  # pragma: no cover
    raise ImportError(
        "domain_aggregator requires PyYAML. Install via: pip install pyyaml"
    ) from _err

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0.0"

# 13 valid domains — matches AGG-*.yaml existing set (Story MCE-4.5 AC1).
# ai-systems added STORY-MCE-AI-SYSTEMS-DOMAIN: experts on AI agent
# orchestration / operating-systems fall outside the 12 business domains;
# without this entry their domain aggregation (gates 7A/7E) can never pass.
VALID_DOMAINS: frozenset[str] = frozenset(
    {
        "ads",
        "ai-systems",
        "content",
        "customer-success",
        "finance",
        "funnels",
        "hiring",
        "leadership",
        "marketing",
        "offers",
        "outbound",
        "pricing",
        "vendas",
    }
)

# Conservative antonym keywords for classify_conflict_type (AC5, F-08).
# Includes PT-BR and EN equivalents.
ANTONYM_KEYWORDS: frozenset[str] = frozenset(
    {
        # PT-BR
        "nunca",
        "sempre",
        "impossivel",
        "obrigatorio",
        "proibido",
        "ao contrario",
        "contradiz",
        "errado",
        "incorreto",
        # EN
        "never",
        "always",
        "impossible",
        "mandatory",
        "forbidden",
        "contrary",
        "contradicts",
        "wrong",
        "incorrect",
    }
)

# Keyword pairs that trigger cross-source conflict detection.
# Mirrors the antonym table in contradiction_detector without importing it.
_CROSS_ANTONYM_PAIRS: list[tuple[str, str]] = [
    ("NUNCA", "SEMPRE"),
    ("PROIBIDO", "OBRIGATORIO"),
    ("IMPOSSIVEL", "POSSIVEL"),
    ("NAO DEVE", "DEVE"),
    ("ELIMINAR", "PRESERVAR"),
    ("AUMENTAR", "REDUZIR"),
    ("ACELERAR", "DESACELERAR"),
    ("SIMPLIFICAR", "COMPLEXIFICAR"),
    ("JAMAIS", "SEMPRE"),
    ("NUNCA", "OBRIGATORIO"),
    ("PROIBIDO", "DEVE"),
    # EN equivalents
    ("NEVER", "ALWAYS"),
    ("FORBIDDEN", "MANDATORY"),
    ("IMPOSSIBLE", "POSSIBLE"),
    ("WRONG", "CORRECT"),
    ("INCORRECT", "CORRECT"),
]

_NEGATION_ANCHORS: frozenset[str] = frozenset(kw for pair in _CROSS_ANTONYM_PAIRS for kw in pair)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    """Resolve repository root from this file's location."""
    # engine/intelligence/pipeline/domain_aggregator.py → 4 levels up = repo root
    return Path(__file__).resolve().parent.parent.parent.parent


def _agg_path(domain: str, root: Path) -> Path:
    domain_upper = domain.upper()
    return root / "knowledge" / "external" / "dna" / "domains" / domain / f"AGG-{domain_upper}.yaml"


def _map_conflitos_path(domain: str, root: Path) -> Path:
    domain_upper = domain.upper()
    return (
        root
        / "knowledge"
        / "external"
        / "dna"
        / "domains"
        / domain
        / f"MAP-CONFLITOS-{domain_upper}.yaml"
    )


def _insights_path_for_slug(slug: str, root: Path) -> Path:
    """Canonical INSIGHTS-STATE.json for an external slug."""
    return root / ".data" / "artifacts" / "insights" / slug / "INSIGHTS-STATE.json"


def _extract_text_from_entry(entry: dict[str, Any]) -> str:
    """Extract normalized uppercase text from an AGG entry or insight dict."""
    text = (
        entry.get("insight")
        or entry.get("quote")
        or entry.get("text")
        or entry.get("statement")
        or entry.get("content")
        or entry.get("description")
        or entry.get("name")
        or ""
    )
    return str(text).upper()


def _contains_keyword(text: str, keyword: str) -> bool:
    return keyword in text


def _find_cross_pair(text_a: str, text_b: str) -> tuple[str, str, str] | None:
    """Return (kw_a, kw_b, confidence) if the texts form a cross-source conflict.

    Returns None if no antonym match is found.
    This is the cross-source equivalent of contradiction_detector._find_triggered_pair.
    We reimplement it here (Option B decision) to avoid importing private symbols
    from contradiction_detector and to keep cross-source semantics clean.
    """
    for kw_a, kw_b in _CROSS_ANTONYM_PAIRS:
        a_has_a = _contains_keyword(text_a, kw_a)
        a_has_b = _contains_keyword(text_a, kw_b)
        b_has_a = _contains_keyword(text_b, kw_a)
        b_has_b = _contains_keyword(text_b, kw_b)

        if a_has_a and b_has_b:
            confidence = "HIGH"
            return (kw_a, kw_b, confidence)
        if a_has_b and b_has_a:
            confidence = "HIGH"
            return (kw_b, kw_a, confidence)

    return None


def _make_conflict_id(domain: str, slug_a: str, slug_b: str, idx: int) -> str:
    """Deterministic conflict ID: CONF-{domain}-{slug_a}-{slug_b}-{NNN}.

    Uses SHA-256 prefix for uniqueness when idx alone could collide.
    """
    pair = sorted([slug_a, slug_b])
    raw = f"{domain}::{pair[0]}::{pair[1]}::{idx}"
    short = hashlib.sha256(raw.encode()).hexdigest()[:6]
    return f"CONF-{domain}-{pair[0]}-{pair[1]}-{short}"


def _load_yaml_file(path: Path) -> dict[str, Any] | None:
    """Load a YAML file safely. Returns None on any error."""
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.debug("Failed to load YAML %s: %s", path, exc)
    return None


def _load_insights_for_slug(slug: str, domain: str, root: Path) -> list[dict[str, Any]]:
    """Load insights for a slug.  Priority:

    1. INSIGHTS-STATE.json from .data/artifacts/insights/{slug}/
    2. Entries from AGG-{DOMAIN}.yaml filtered by person == slug

    Falls back gracefully to empty list if neither exists.
    """
    # Try INSIGHTS-STATE.json first
    ins_path = _insights_path_for_slug(slug, root)
    if ins_path.exists():
        try:
            import json as _json

            data = _json.loads(ins_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Flatten all layer lists into a single list
                insights: list[dict[str, Any]] = []
                for key, val in data.items():
                    if isinstance(val, list):
                        insights.extend(item for item in val if isinstance(item, dict))
                if insights:
                    return insights
        except Exception as exc:
            logger.debug("INSIGHTS-STATE.json unreadable for %s: %s", slug, exc)

    # Fall back to AGG entries filtered by origin == slug (MCE-4.5 R1 fix)
    # AGG entries carry an `origin` field (e.g. "alex-hormozi"). Without filtering,
    # the cross-product would compare entries from the same slug against themselves,
    # inflating false positives. Filter strictly by origin match.
    agg = _load_yaml_file(_agg_path(domain, root))
    if not agg:
        return []
    entries = agg.get("entries", [])
    slug_norm = slug.strip().lower()
    slug_insights = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        origin = str(entry.get("origin", "")).strip().lower()
        if origin and origin == slug_norm:
            slug_insights.append(entry)
    return slug_insights


def _atomic_write_yaml(content: str, target: Path) -> None:
    """Atomic write to target using tempfile + os.replace (AC6).

    Reuses the exact pattern from orchestrate.py:_save_insights_state.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _infer_layer_from_entry(entry: dict[str, Any]) -> str:
    """Infer a DNA layer string from an AGG entry's category or id field."""
    entry_id = str(entry.get("id") or "")
    category = str(entry.get("category") or entry.get("layer") or "")
    combined = (entry_id + " " + category).lower()
    for num in range(10, 0, -1):
        if f"l{num}" in combined or f"l{num}_" in combined:
            return f"L{num}"
    # Map common category names to layers
    if "filosof" in combined:
        return "L1"
    if "modelo" in combined or "mental" in combined:
        return "L2"
    if "heurist" in combined:
        return "L3"
    if "framework" in combined:
        return "L4"
    if "metodolog" in combined:
        return "L5"
    if "behavioral" in combined or "comporta" in combined:
        return "L6"
    if "valor" in combined or "value" in combined:
        return "L7"
    if "voice" in combined or "voz" in combined:
        return "L8"
    if "obsess" in combined:
        return "L9"
    if "paradox" in combined:
        return "L10"
    return "L3"  # default to heuristics


# ---------------------------------------------------------------------------
# Public API — exactly 3 functions (AC2)
# ---------------------------------------------------------------------------


def classify_conflict_type(conflict: dict[str, Any]) -> str:
    """Classify a conflict as 'complementar', 'divergente', or 'contraditorio'.

    Conservative default: returns 'complementar' when no explicit antonym
    keywords are detected in either excerpt (F-08, AC5).

    Logic:
      - If combined excerpts contain 0 antonym keywords -> 'complementar'
      - If combined excerpts contain 1-2 antonym keywords -> 'divergente'
      - If combined excerpts contain 3+ antonym keywords -> 'contraditorio'

    This prevents false positives (Veto V4): 'contraditorio' is NEVER returned
    without at least 3 explicit antonym keyword signals.
    """
    text_a = str(conflict.get("insight_a_excerpt") or "").lower()
    text_b = str(conflict.get("insight_b_excerpt") or "").lower()
    combined = text_a + " " + text_b

    antonym_count = sum(1 for kw in ANTONYM_KEYWORDS if kw in combined)

    if antonym_count == 0:
        return "complementar"  # default conservador (F-08)
    if antonym_count >= 3:
        return "contraditorio"
    return "divergente"


def detect_cross_source_conflict(
    slug_a: str,
    slug_b: str,
    domain: str,
    *,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    """Compare insights from slug_a and slug_b within the same domain.

    Cross-source bridge (Option B — see module docstring):
    - Load insights for slug_a independently
    - Load insights for slug_b independently
    - Perform explicit cross-product: each entry from slug_a vs each from slug_b
    - Never compares same-slug pairs
    - Uses _find_cross_pair() (local reimplementation, no private symbol import)

    Returns a list of raw conflict dicts (may be empty if no antonyms found).
    Each conflict dict has: slug_a, slug_b, text_a, text_b, keywords, confidence,
    entry_a (source entry), entry_b (source entry).
    """
    if root is None:
        root = _repo_root()

    insights_a = _load_insights_for_slug(slug_a, domain, root)
    insights_b = _load_insights_for_slug(slug_b, domain, root)

    if not insights_a or not insights_b:
        logger.debug(
            "detect_cross_source_conflict: no insights for %s or %s in domain %s",
            slug_a,
            slug_b,
            domain,
        )
        return []

    # Pre-filter slug_a insights: only those with at least one negation anchor
    anchor_a = [
        e
        for e in insights_a
        if any(_contains_keyword(_extract_text_from_entry(e), kw) for kw in _NEGATION_ANCHORS)
    ]

    conflicts: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, ...]] = set()

    for entry_a in anchor_a:
        text_a = _extract_text_from_entry(entry_a)
        id_a = str(entry_a.get("id") or id(entry_a))

        for entry_b in insights_b:
            id_b = str(entry_b.get("id") or id(entry_b))
            text_b = _extract_text_from_entry(entry_b)

            pair_key = tuple(sorted([id_a, id_b]))
            if pair_key in seen_pairs:
                continue

            result = _find_cross_pair(text_a, text_b)
            if result is None:
                continue

            kw_a, kw_b, confidence = result
            seen_pairs.add(pair_key)

            conflicts.append(
                {
                    "slug_a": slug_a,
                    "slug_b": slug_b,
                    "id_a": id_a,
                    "id_b": id_b,
                    "text_a": text_a,
                    "text_b": text_b,
                    "entry_a": entry_a,
                    "entry_b": entry_b,
                    "keywords": [kw_a, kw_b],
                    "confidence": "MEDIA" if confidence == "HIGH" else "BAIXA",
                    # Confidence mapped: HIGH keyword match -> MEDIA epistemic
                    # (cross-source confidence is structurally lower than within-slug)
                }
            )

    return conflicts


def aggregate_domain_conflicts(
    domain: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Orchestrate full MAP-CONFLITOS aggregation for a domain (AC2).

    Workflow:
      1. Validate domain against VALID_DOMAINS (raises ValueError if invalid).
      2. Load AGG-{DOMAIN}.yaml -> extract expert slugs from experts[].person.
      3. For each pair (slug_a, slug_b): call detect_cross_source_conflict().
      4. For each raw conflict: call classify_conflict_type() + build schema entry.
      5. Write MAP-CONFLITOS-{DOMAIN}.yaml via atomic write (AC6).
      6. Return status dict with keys: status, domain, conflicts_found,
         conflicts_written, experts_compared.

    Idempotency:
      If MAP-CONFLITOS-{D}.yaml already exists and AGG has the same `updated`
      field as recorded in the existing MAP file, returns status='skipped'.
      If AGG changed (or no `updated` field) -> regenerates (status='updated'
      or 'written' for first time).

    Returns:
        dict with keys: status, domain, conflicts_found, conflicts_written,
        experts_compared. On error, status='error' + error key.
    """
    if domain not in VALID_DOMAINS:
        valid_sorted = sorted(VALID_DOMAINS)
        raise ValueError(f"Domain '{domain}' is not valid. Must be one of: {valid_sorted}")

    if root is None:
        root = _repo_root()

    domain_upper = domain.upper()  # F2: direct .upper(), no no-op replace

    agg_path = _agg_path(domain, root)
    agg_data = _load_yaml_file(agg_path)
    if not agg_data:
        logger.warning("aggregate_domain_conflicts: AGG not found at %s", agg_path)
        return {
            "status": "error",
            "domain": domain,
            "error": f"AGG not found: {agg_path}",
            "conflicts_found": 0,
            "conflicts_written": 0,
            "experts_compared": 0,
        }

    experts_list = agg_data.get("experts", [])
    slugs = [e["person"] for e in experts_list if isinstance(e, dict) and "person" in e]
    experts_compared = len(slugs)

    # Idempotency check (AC — F4 note: if no `updated` field, always regenerate)
    agg_updated = agg_data.get("updated", "")
    target_path = _map_conflitos_path(domain, root)
    if target_path.exists() and agg_updated:
        existing = _load_yaml_file(target_path)
        if existing and existing.get("agg_updated_at") == agg_updated:
            logger.info("MAP-CONFLITOS-%s.yaml is current (AGG unchanged). Skipping.", domain_upper)
            return {
                "status": "skipped",
                "domain": domain,
                "conflicts_found": 0,
                "conflicts_written": existing.get("total_conflicts", 0),
                "experts_compared": experts_compared,
            }

    # Cross-source conflict detection: all pairs of slugs
    all_raw_conflicts: list[dict[str, Any]] = []
    for slug_a, slug_b in itertools.combinations(slugs, 2):
        raw = detect_cross_source_conflict(slug_a, slug_b, domain, root=root)
        all_raw_conflicts.extend(raw)

    # Build schema-conforming conflict entries
    conflict_entries: list[dict[str, Any]] = []
    for idx, raw in enumerate(all_raw_conflicts, start=1):
        entry_a = raw.get("entry_a") or {}
        entry_b = raw.get("entry_b") or {}

        excerpt_a = str(
            entry_a.get("quote")
            or entry_a.get("insight")
            or entry_a.get("description")
            or raw.get("text_a", "")
        )[:200]
        excerpt_b = str(
            entry_b.get("quote")
            or entry_b.get("insight")
            or entry_b.get("description")
            or raw.get("text_b", "")
        )[:200]

        # Capitalize excerpts for display (they were uppercased internally)
        # Use original entry text where possible
        excerpt_a_display = str(
            entry_a.get("quote")
            or entry_a.get("insight")
            or entry_a.get("description")
            or excerpt_a
        )[:200]
        excerpt_b_display = str(
            entry_b.get("quote")
            or entry_b.get("insight")
            or entry_b.get("description")
            or excerpt_b
        )[:200]

        conflict_dict = {
            "insight_a_excerpt": excerpt_a_display,
            "insight_b_excerpt": excerpt_b_display,
        }
        conflict_type = classify_conflict_type(conflict_dict)

        layer = _infer_layer_from_entry(entry_a)
        name_a = str(entry_a.get("name") or entry_a.get("id") or "")
        name_b = str(entry_b.get("name") or entry_b.get("id") or "")
        description = (
            f"Divergencia entre {raw['slug_a']} e {raw['slug_b']}: "
            f"{name_a[:60] or 'sem nome'} vs {name_b[:60] or 'sem nome'}"
        )

        conflict_entries.append(
            {
                "conflict_id": _make_conflict_id(domain, raw["slug_a"], raw["slug_b"], idx),
                "slug_a": raw["slug_a"],
                "slug_b": raw["slug_b"],
                "type": conflict_type,
                "layer": layer,
                "description": description,
                "insight_a_excerpt": excerpt_a_display,
                "insight_b_excerpt": excerpt_b_display,
                "confidence": raw.get("confidence", "BAIXA"),
            }
        )

    generated_at = _now_iso()
    map_doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": domain,
        "domain_upper": domain_upper,
        "generated_at": generated_at,
        "agg_updated_at": agg_updated,  # stored for idempotency check
        "experts_compared": experts_compared,
        "total_conflicts": len(conflict_entries),
        "conflicts": conflict_entries,
    }

    yaml_content = yaml.dump(
        map_doc,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
    )

    _atomic_write_yaml(yaml_content, target_path)

    status = "written" if not agg_updated else "updated"
    # Reaching here means write happened (idempotency guard returned early above).
    logger.info(
        "MAP-CONFLITOS-%s.yaml written: %d conflicts from %d experts",
        domain_upper,
        len(conflict_entries),
        experts_compared,
    )

    return {
        "status": status,
        "domain": domain,
        "conflicts_found": len(all_raw_conflicts),
        "conflicts_written": len(conflict_entries),
        "experts_compared": experts_compared,
    }


def _list_domains_for_slug(slug: str, root: Path) -> list[str]:
    """Return list of domains where the slug appears in AGG experts[].person.

    Scans knowledge/external/dna/domains/*/AGG-*.yaml.
    Used by orchestrate.py cmd_finalize hook to infer which domains to aggregate.
    """
    domains_dir = root / "knowledge" / "external" / "dna" / "domains"
    if not domains_dir.is_dir():
        return []

    found: list[str] = []
    for domain_dir in domains_dir.iterdir():
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name
        if domain not in VALID_DOMAINS:
            continue
        agg_data = _load_yaml_file(_agg_path(domain, root))
        if not agg_data:
            continue
        experts = agg_data.get("experts", [])
        if any(isinstance(e, dict) and e.get("person") == slug for e in experts):
            found.append(domain)

    return found
