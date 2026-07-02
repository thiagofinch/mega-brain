"""atlas_classifier.py — Atlas Classification Block (Story MCE-13.23).

Performs formal domain classification for a pipeline slug using a combination
of heuristic path analysis and LLM-assisted classification. Produces a
classification block that feeds into AGG-*.yaml domain files, enabling
Phase 8 gate 7A to pass.

The "Atlas" name refers to the knowledge atlas: the cross-domain map of where
each expert's insights belong. Classification is the precondition for domain
aggregation (domain_aggregator.py).

Stack: stdlib + PyYAML. LLM via llm_router (optional — falls back to heuristic).
Zero imports of orchestrate.py.

Story: MCE-13.23
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Valid domains (mirrors domain_aggregator.VALID_DOMAINS)
VALID_DOMAINS: frozenset[str] = frozenset(
    {
        "ads",
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

#: Keyword → domain heuristic map.
#: Ordered from most specific to least specific.
_DOMAIN_KEYWORDS: list[tuple[frozenset[str], str]] = [
    (frozenset({"nepq", "objeção", "objection", "fechamento", "closing", "qualificação"}), "vendas"),
    (frozenset({"preço", "precificação", "price", "pricing", "âncora", "anchor"}), "pricing"),
    (frozenset({"funil", "funnel", "etapa", "stage", "conversão", "conversion"}), "funnels"),
    (frozenset({"anúncio", "ad", "tráfego", "traffic", "roas", "facebook ads", "meta ads"}), "ads"),
    (frozenset({"sdr", "outbound", "prospecção", "prospecting", "cold outreach"}), "outbound"),
    (frozenset({"conteúdo", "content", "copywriting", "copy", "email", "newsletter"}), "content"),
    (frozenset({"oferta", "offer", "produto", "product", "proposta", "value proposition"}), "offers"),
    (frozenset({"marketing", "brand", "marca", "posicionamento", "positioning"}), "marketing"),
    (frozenset({"contratar", "hiring", "recrutamento", "recruitment", "onboarding"}), "hiring"),
    (frozenset({"liderança", "leadership", "gestão", "management", "cultura", "culture"}), "leadership"),
    (frozenset({"retenção", "retention", "churn", "lTV", "customer success", "upsell"}), "customer-success"),
    (frozenset({"finanças", "finance", "receita", "revenue", "margem", "margin", "lucro"}), "finance"),
]

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    """Resolve repository root from this file's location."""
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def _agg_path(domain: str, root: Path) -> Path:
    domain_upper = domain.upper()
    return root / "knowledge" / "external" / "dna" / "domains" / domain / f"AGG-{domain_upper}.yaml"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Heuristic classification
# ---------------------------------------------------------------------------


def classify_by_heuristic(
    slug: str,
    insights: list[dict[str, Any]],
) -> list[str]:
    """Return list of domains inferred from insight content using keyword heuristics.

    Scans the combined text of all insights for domain signal keywords.
    Returns up to 3 best-matching domains (sorted by keyword hit count).

    Args:
        slug:     Pipeline slug.
        insights: List of insight dicts from INSIGHTS-STATE.

    Returns:
        List of domain strings (may be empty if no signals found).
    """
    combined_text = " ".join(
        (
            str(ins.get("insight") or "")
            + " "
            + str(ins.get("quote") or "")
            + " "
            + str(ins.get("category") or "")
        ).lower()
        for ins in insights
        if isinstance(ins, dict)
    )

    # Also use slug tokens as weak signal
    slug_tokens = set(slug.lower().replace("-", " ").split())
    combined_text += " " + " ".join(slug_tokens)

    domain_scores: dict[str, int] = {}
    for keywords, domain in _DOMAIN_KEYWORDS:
        hits = sum(1 for kw in keywords if kw in combined_text)
        if hits > 0:
            domain_scores[domain] = domain_scores.get(domain, 0) + hits

    # Return top-3 domains by hit count
    sorted_domains = sorted(domain_scores.items(), key=lambda x: -x[1])
    return [d for d, _ in sorted_domains[:3]]


# ---------------------------------------------------------------------------
# LLM-assisted classification (optional)
# ---------------------------------------------------------------------------

_CLASSIFICATION_PROMPT_PATH = (
    Path(__file__).resolve().parent / "prompts" / "atlas-classification.prompt.md"
)


def _build_classification_prompt(slug: str, insights_sample: list[dict[str, Any]]) -> str:
    """Build the LLM classification prompt."""
    domains_list = ", ".join(sorted(VALID_DOMAINS))
    sample_text = "\n".join(
        f"- {str(ins.get('insight') or ins.get('quote') or '')[:200]}"
        for ins in insights_sample[:30]
        if isinstance(ins, dict)
    )

    template = None
    if _CLASSIFICATION_PROMPT_PATH.exists():
        try:
            template = _CLASSIFICATION_PROMPT_PATH.read_text(encoding="utf-8")
        except Exception:
            pass

    if template:
        return template.format(
            slug=slug,
            domains=domains_list,
            insights_sample=sample_text,
        )

    # Inline fallback prompt
    return (
        f"You are a domain classification expert for a knowledge pipeline.\n"
        f"Analyze the insights below from expert '{slug}' and classify which domains\n"
        f"they belong to.\n\n"
        f"Valid domains: {domains_list}\n\n"
        f"Insights sample:\n{sample_text}\n\n"
        f"Return ONLY valid JSON: {{\"domains\": [\"domain1\", \"domain2\"], "
        f"\"confidence\": \"HIGH|MEDIUM|LOW\", \"reasoning\": \"brief explanation\"}}\n"
        f"Classify up to 3 domains maximum. Use only domains from the valid list.\n"
    )


def classify_by_llm(
    slug: str,
    insights: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Optional LLM-assisted classification.

    Returns dict with domains[], confidence, reasoning OR None if LLM unavailable.
    Never raises — exceptions are caught and None returned.
    """
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter

        prompt = _build_classification_prompt(slug, insights)
        router = LLMRouter()
        raw = router.run_prompt(prompt, step="classification", max_output_tokens=256)
        if not raw:
            return None

        # Parse JSON from response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        parsed = json.loads(match.group(0))
        domains = parsed.get("domains", [])
        # Validate against known domains
        valid = [d for d in domains if d in VALID_DOMAINS]
        if not valid:
            return None
        return {
            "domains": valid,
            "confidence": parsed.get("confidence", "MEDIUM"),
            "reasoning": parsed.get("reasoning", ""),
            "method": "llm",
        }
    except Exception as exc:
        logger.debug("atlas_classifier: LLM classification failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# AGG file management
# ---------------------------------------------------------------------------


def _load_agg(domain: str, root: Path) -> dict[str, Any]:
    """Load AGG-{domain}.yaml or return empty skeleton."""
    path = _agg_path(domain, root)
    if path.exists():
        try:
            import yaml

            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.debug("atlas_classifier: failed to load AGG for %s: %s", domain, exc)
    return {
        "schema_version": "1.0.0",
        "domain": domain,
        "experts": [],
        "entries": [],
        "created_at": _now_iso(),
        "updated": _now_iso(),
    }


def _save_agg(domain: str, root: Path, data: dict[str, Any]) -> None:
    """Atomically write AGG-{domain}.yaml."""
    import yaml

    path = _agg_path(domain, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
    )
    tmp_fd, tmp_str = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    tmp_path = Path(tmp_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _upsert_expert_in_agg(
    agg_data: dict[str, Any],
    slug: str,
    person_name: str,
) -> bool:
    """Add slug to AGG experts[] if not already present. Returns True if added."""
    experts = agg_data.setdefault("experts", [])
    existing = [e for e in experts if isinstance(e, dict) and e.get("person") == slug]
    if existing:
        return False
    experts.append(
        {
            "person": slug,
            "display_name": person_name,
            "added_at": _now_iso(),
        }
    )
    agg_data["updated"] = _now_iso()
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_and_register(
    slug: str,
    *,
    root: Path | None = None,
    insights: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Classify a slug into domains and register it in AGG-*.yaml files.

    Pipeline:
      1. Load insights (from INSIGHTS-STATE.json if not provided).
      2. Try LLM classification first (optional, fails gracefully).
      3. Fall back to heuristic keyword classification.
      4. For each domain detected: upsert slug into AGG-{domain}.yaml.

    This enables Phase 8 gate 7A to pass on the next run.

    Args:
        slug:     Pipeline slug (e.g. "jordan-lee").
        root:     Repo root (resolved automatically if None).
        insights: Optional pre-loaded insights (loaded from disk if None).

    Returns:
        Dict with: status, slug, domains_classified, domains_registered,
        classification_method, domains.
    """
    if root is None:
        root = _repo_root()

    # Load insights if not provided
    if insights is None:
        ins_path = root / ".data" / "artifacts" / "insights" / slug / "INSIGHTS-STATE.json"
        insights = []
        if ins_path.exists():
            try:
                state = json.loads(ins_path.read_text(encoding="utf-8"))
                persons = state.get("persons", {})
                for entry in persons.values():
                    if isinstance(entry, dict):
                        insights.extend(entry.get("insights", []))
                    elif isinstance(entry, list):
                        insights.extend(i for i in entry if isinstance(i, dict))
            except Exception as exc:
                logger.debug("atlas_classifier: failed to load insights for %s: %s", slug, exc)

    if not insights:
        logger.debug("atlas_classifier: no insights for %s — classification empty", slug)
        return {
            "status": "no_insights",
            "slug": slug,
            "domains_classified": 0,
            "domains_registered": 0,
            "classification_method": "none",
            "domains": [],
        }

    # 1. Try LLM classification
    llm_result = classify_by_llm(slug, insights)
    if llm_result:
        domains = llm_result["domains"]
        method = "llm"
        confidence = llm_result.get("confidence", "MEDIUM")
    else:
        # 2. Heuristic fallback
        domains = classify_by_heuristic(slug, insights)
        method = "heuristic"
        confidence = "MEDIUM" if domains else "LOW"

    if not domains:
        return {
            "status": "unclassified",
            "slug": slug,
            "domains_classified": 0,
            "domains_registered": 0,
            "classification_method": method,
            "domains": [],
        }

    # Derive person display name from slug
    person_name = " ".join(part.capitalize() for part in slug.replace("_", "-").split("-"))

    # Register in AGG files
    registered: list[str] = []
    for domain in domains:
        if domain not in VALID_DOMAINS:
            continue
        try:
            agg_data = _load_agg(domain, root)
            added = _upsert_expert_in_agg(agg_data, slug, person_name)
            if added:
                _save_agg(domain, root, agg_data)
                registered.append(domain)
                logger.info(
                    "atlas_classifier: registered %s in AGG-%s.yaml",
                    slug,
                    domain.upper(),
                )
            else:
                logger.debug(
                    "atlas_classifier: %s already in AGG-%s.yaml — skipping",
                    slug,
                    domain.upper(),
                )
        except Exception as exc:
            logger.warning(
                "atlas_classifier: failed to register %s in domain %s: %s", slug, domain, exc
            )

    return {
        "status": "classified",
        "slug": slug,
        "domains_classified": len(domains),
        "domains_registered": len(registered),
        "domains_skipped": len(domains) - len(registered),
        "classification_method": method,
        "confidence": confidence,
        "domains": domains,
        "domains_newly_registered": registered,
    }
