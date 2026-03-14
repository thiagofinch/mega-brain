#!/usr/bin/env python3
"""
SOP DETECTOR — Auto-detect process descriptions in meeting insights.
====================================================================

Scans insight JSON files for process-like patterns (sequential steps,
imperative verbs, numbered lists) and generates draft SOP YAML files.

Draft SOPs are saved to knowledge/business/sops/{area}/{slug}.yaml
with status: draft — human review is ALWAYS required before promotion.

Version: 1.0.0
Date: 2026-03-09
Story: S09 — EPIC-REORG-001
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from core.paths import BUSINESS_INSIGHTS, BUSINESS_SOPS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DETECTION HEURISTICS
# ---------------------------------------------------------------------------

# Portuguese + English keywords that indicate process descriptions
PROCESS_KEYWORDS: list[str] = [
    "passo",
    "etapa",
    "fase",
    "primeiro",
    "depois",
    "então",
    "entao",
    "pipeline",
    "fluxo",
    "processo",
    "procedimento",
    "a gente faz",
    "o fluxo é",
    "o processo é",
    "step",
    "first",
    "then",
    "next",
    "finally",
    "workflow",
    "procedure",
]

# Imperative verb prefixes (Portuguese + English) common in process steps
IMPERATIVE_PREFIXES: list[str] = [
    "fazer",
    "criar",
    "abrir",
    "enviar",
    "verificar",
    "validar",
    "configurar",
    "executar",
    "rodar",
    "acessar",
    "clicar",
    "preencher",
    "selecionar",
    "confirmar",
    "revisar",
    "aprovar",
    "publicar",
    "agendar",
    "ligar",
    "mandar",
    "create",
    "open",
    "send",
    "check",
    "validate",
    "configure",
    "run",
    "click",
    "fill",
    "select",
    "confirm",
    "review",
    "approve",
    "publish",
    "schedule",
]

# Area classification keywords
AREA_KEYWORDS: dict[str, list[str]] = {
    "comercial": [
        "venda",
        "vendas",
        "sales",
        "closer",
        "closing",
        "lead",
        "prospect",
        "pipeline",
        "funil",
        "funnel",
        "follow-up",
        "follow up",
        "demo",
        "proposta",
        "proposal",
        "negociacao",
        "deal",
        "CRM",
    ],
    "producao": [
        "produção",
        "producao",
        "conteúdo",
        "conteudo",
        "content",
        "design",
        "página",
        "pagina",
        "page",
        "landing",
        "copy",
        "criativo",
        "creative",
        "edição",
        "edicao",
        "edit",
        "video",
        "thumbnail",
    ],
    "financeiro": [
        "financeiro",
        "finance",
        "pagamento",
        "payment",
        "nota fiscal",
        "invoice",
        "contabilidade",
        "accounting",
        "DRE",
        "fluxo de caixa",
        "cash flow",
        "imposto",
        "tax",
        "reembolso",
        "refund",
    ],
    "onboarding": [
        "onboarding",
        "integração",
        "integracao",
        "boas vindas",
        "welcome",
        "primeiro dia",
        "first day",
        "treinamento",
        "training",
        "ramp",
    ],
    "marketing": [
        "marketing",
        "tráfego",
        "trafego",
        "traffic",
        "ads",
        "campanha",
        "campaign",
        "mídia",
        "midia",
        "media",
        "email marketing",
        "SEO",
        "social media",
        "redes sociais",
    ],
    "suporte": [
        "suporte",
        "support",
        "CS",
        "customer success",
        "atendimento",
        "ticket",
        "chamado",
        "reclamação",
        "reclamacao",
        "complaint",
    ],
    "operacoes": [
        "operação",
        "operacao",
        "operations",
        "processo",
        "process",
        "automação",
        "automacao",
        "automation",
        "workflow",
        "sistema",
        "system",
        "ferramenta",
        "tool",
    ],
}

# Numbered-list patterns
_NUMBERED_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:\d+[\.\)\-]|\(?[a-z]\))\s+\S",
    re.MULTILINE,
)

# Sequence connectors pattern
_SEQUENCE_PATTERN = re.compile(
    r"(?:primeiro|segundo|terceiro|quarto|quinto|"
    r"first|second|third|fourth|fifth|"
    r"passo\s+\d|step\s+\d|etapa\s+\d|fase\s+\d)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------


def _score_process_likelihood(text: str) -> int:
    """Score how likely a text describes a process (0-100).

    Heuristics:
      - Each process keyword found: +10 (max 40)
      - Numbered list items: +8 per item (max 32)
      - Sequence connectors: +12 per match (max 36)
      - 3+ imperative verbs: +15
    """
    text_lower = text.lower()
    score = 0

    # Process keywords
    kw_hits = sum(1 for kw in PROCESS_KEYWORDS if kw in text_lower)
    score += min(kw_hits * 10, 40)

    # Numbered lists
    numbered = _NUMBERED_PATTERN.findall(text)
    score += min(len(numbered) * 8, 32)

    # Sequence connectors
    sequences = _SEQUENCE_PATTERN.findall(text)
    score += min(len(sequences) * 12, 36)

    # Imperative verbs
    imperative_count = sum(
        1 for pref in IMPERATIVE_PREFIXES if re.search(rf"\b{re.escape(pref)}\b", text_lower)
    )
    if imperative_count >= 3:
        score += 15

    return min(score, 100)


def _classify_area(text: str) -> str:
    """Classify a text into a business area based on keyword frequency.

    Returns the area with the most keyword hits, or 'operacoes' as default.
    """
    text_lower = text.lower()
    best_area = "operacoes"
    best_count = 0

    for area, keywords in AREA_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_area = area

    return best_area


# ---------------------------------------------------------------------------
# STEP EXTRACTION
# ---------------------------------------------------------------------------


def _extract_steps(text: str) -> list[dict[str, str]]:
    """Extract sequential steps from process text.

    Tries multiple patterns:
      1. Numbered items (1. ..., 2. ..., etc.)
      2. Sequence connectors (primeiro... depois... então...)
      3. Sentence-level split on imperative verbs
    """
    steps: list[dict[str, str]] = []

    # Pattern 1: numbered items
    numbered_re = re.compile(
        r"(?:^|\n)\s*(\d+)[\.\)\-]\s*(.+?)(?=\n\s*\d+[\.\)\-]|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = numbered_re.findall(text)
    if len(matches) >= 2:
        for _, content in matches:
            clean = content.strip().split("\n")[0].strip()
            if clean:
                steps.append({"action": clean, "detail": ""})
        return steps

    # Pattern 2: sequence connector splitting
    parts = re.split(
        r"(?:primeiro|passo\s*1|step\s*1|1[\.\)])\s*[,:]?\s*",
        text,
        flags=re.IGNORECASE,
        maxsplit=1,
    )
    if len(parts) > 1:
        # Split remainder on connectors
        remainder = parts[1]
        segments = re.split(
            r"(?:depois|então|entao|segundo|terceiro|quarto|quinto|"
            r"passo\s*\d|step\s*\d|etapa\s*\d|"
            r"em seguida|next|then|finally|por fim)\s*[,:]?\s*",
            remainder,
            flags=re.IGNORECASE,
        )
        for seg in segments:
            clean = seg.strip().rstrip(".,;")
            if clean and len(clean) > 5:
                steps.append({"action": clean[:200], "detail": ""})
        if steps:
            return steps

    # Pattern 3: sentence split with imperative detection
    sentences = re.split(r"[.!?]\s+", text)
    for sent in sentences:
        sent_lower = sent.lower().strip()
        for pref in IMPERATIVE_PREFIXES:
            if sent_lower.startswith(pref) or re.match(
                rf"^(voce|você|a gente|we|you)\s+{re.escape(pref)}",
                sent_lower,
            ):
                steps.append({"action": sent.strip()[:200], "detail": ""})
                break

    return steps


# ---------------------------------------------------------------------------
# INSIGHT NORMALIZATION
# ---------------------------------------------------------------------------


def _normalize_insight(raw: dict) -> dict:
    """Normalize different insight JSON formats into a common shape.

    Handles both TF001-style (summary/evidence/person) and
    CG-SM001-style (insight/source.speaker/id_chunk).
    """
    # Text content
    text = raw.get("summary") or raw.get("insight") or ""
    evidence = raw.get("evidence", "")
    combined = f"{text}\n{evidence}" if evidence else text

    # Speaker
    speaker = raw.get("person") or ""
    if not speaker:
        source = raw.get("source", {})
        if isinstance(source, dict):
            speaker = source.get("speaker", "")

    # Source ID
    source_id = raw.get("id", "")
    if not source_id:
        source = raw.get("source", {})
        if isinstance(source, dict):
            source_id = source.get("source_id", "")

    # Chunk IDs
    chunk_ids = raw.get("chunk_ids", [])
    if not chunk_ids:
        cid = raw.get("id_chunk", "")
        if cid:
            chunk_ids = [cid]

    # Title
    title = raw.get("title") or raw.get("insight", "")[:80] or "Untitled"

    return {
        "text": combined,
        "title": title,
        "speaker": speaker,
        "source_id": source_id,
        "chunk_ids": chunk_ids,
        "raw": raw,
    }


# ---------------------------------------------------------------------------
# SLUG GENERATION
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    # Remove accents (simplified)
    replacements = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ü": "u",
        "ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # Replace non-alphanumeric with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:60] or "untitled"


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

_SOP_THRESHOLD = 30  # Minimum score to consider something a process


def detect_sops(insights_path: Path) -> list[dict]:
    """Scan insights for process descriptions.

    Args:
        insights_path: Path to a JSON file (single insight list or
                       envelope with 'insights' key) or a directory
                       of JSON files.

    Returns:
        List of detected SOPs with metadata. Each dict contains:
          id, title, area, steps, detected_from, score.
    """
    insight_files: list[Path] = []

    if insights_path.is_dir():
        insight_files = sorted(insights_path.glob("**/*.json"))
    elif insights_path.is_file():
        insight_files = [insights_path]
    else:
        logger.warning("Path does not exist: %s", insights_path)
        return []

    detected: list[dict] = []
    sop_counter = 0

    for fpath in insight_files:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", fpath.name, e)
            continue

        # Handle both list-of-insights and envelope formats
        insights: list[dict] = []
        if isinstance(data, list):
            insights = data
        elif isinstance(data, dict) and "insights" in data:
            insights = data["insights"]
        else:
            logger.debug("Skipping %s: unrecognized format", fpath.name)
            continue

        for raw_insight in insights:
            norm = _normalize_insight(raw_insight)
            score = _score_process_likelihood(norm["text"])

            if score < _SOP_THRESHOLD:
                continue

            area = _classify_area(norm["text"])
            steps = _extract_steps(norm["text"])

            if len(steps) < 2:
                # Not enough steps to constitute a process
                continue

            sop_counter += 1
            sop_id = f"SOP-{area.upper()}-{sop_counter:03d}"

            sop = {
                "id": sop_id,
                "title": norm["title"],
                "area": area,
                "status": "draft",
                "version": "0.1.0",
                "score": score,
                "detected_from": [
                    {
                        "source": norm["source_id"],
                        "speaker": norm["speaker"],
                        "chunk_ids": norm["chunk_ids"],
                        "file": str(fpath.name),
                    },
                ],
                "steps": [
                    {"step": i + 1, "action": s["action"], "detail": s["detail"]}
                    for i, s in enumerate(steps)
                ],
                "validation_notes": (
                    "Auto-detected -- requires human review before "
                    "promotion to workspace/_templates/"
                ),
                "detected_at": datetime.now(tz=UTC).isoformat(),
            }
            detected.append(sop)
            logger.info(
                "Detected SOP: %s (%s) score=%d steps=%d",
                sop_id,
                norm["title"][:50],
                score,
                len(steps),
            )

    logger.info("Total SOPs detected: %d", len(detected))
    return detected


def save_sop_draft(sop: dict, area: str | None = None) -> Path:
    """Save a detected SOP as draft YAML.

    Args:
        sop: SOP dict as returned by detect_sops().
        area: Override area classification. If None, uses sop['area'].

    Returns:
        Path to the created YAML file.
    """
    target_area = area or sop.get("area", "operacoes")
    slug = _slugify(sop.get("title", "untitled"))
    sop_id = sop.get("id", "SOP-UNK-000")

    dest_dir = BUSINESS_SOPS / target_area
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slug}.yaml"
    dest = dest_dir / filename

    # Avoid overwriting
    if dest.exists():
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{slug}-{counter}.yaml"
            counter += 1

    # Build clean YAML-friendly dict (strip internal fields)
    yaml_data = {
        "id": sop_id,
        "title": sop["title"],
        "area": target_area,
        "status": "draft",
        "version": sop.get("version", "0.1.0"),
        "detected_from": sop.get("detected_from", []),
        "steps": sop.get("steps", []),
        "validation_notes": sop.get(
            "validation_notes",
            "Auto-detected -- requires human review before promotion.",
        ),
    }

    with open(dest, "w", encoding="utf-8") as f:
        f.write("# Auto-detected SOP\n")
        yaml.dump(
            yaml_data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    logger.info("Saved SOP draft: %s", dest)
    return dest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for SOP detection."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if len(sys.argv) < 2:
        default_path = BUSINESS_INSIGHTS / "by-meeting"
        print("\n=== SOP Detector ===\n")
        print("Scans insight JSON files for process descriptions")
        print("and generates draft SOP YAML files.\n")
        print("Usage:")
        print(f"  python {__file__} <insights_path>")
        print(f"  python {__file__} --default  (scans {default_path})")
        print(f"\nOutput: {BUSINESS_SOPS}/<area>/<slug>.yaml")
        return 0

    if sys.argv[1] == "--default":
        target = BUSINESS_INSIGHTS / "by-meeting"
    else:
        target = Path(sys.argv[1])

    if not target.exists():
        logger.error("Path does not exist: %s", target)
        return 1

    sops = detect_sops(target)

    if not sops:
        print("No process descriptions detected.")
        return 0

    print(f"\nDetected {len(sops)} SOP(s):\n")
    for sop in sops:
        area = sop["area"]
        saved = save_sop_draft(sop, area)
        print(f"  [{sop['id']}] {sop['title'][:60]}")
        print(f"    Area: {area} | Steps: {len(sop['steps'])} | Score: {sop['score']}")
        print(f"    Saved: {saved}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
