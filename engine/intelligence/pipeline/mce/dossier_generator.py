"""dossier_generator.py -- Synthesise a structured dossier for a person slug.
=============================================================================

Frente 8 (2026-05-13): reads INSIGHTS-STATE.json (L1-L5) + L6-L10 YAMLs +
agent files (AGENT.md / SOUL.md) and produces a single Markdown dossier at
``knowledge/{bucket}/dossiers/persons/dossier-{slug}.md``.

Contract:
    - Deterministic-first: all 7 sections can be generated without LLM.
    - Optional LLM refinement for Section 1 (bio narrative) via llm_router.
      Falls back to deterministic template if LLM is unavailable.
    - Idempotent: if dossier already exists with same source timestamp, skip
      (unless ``force=True``).
    - Non-fatal: caller (cmd_consolidate) must remain non-blocking.
    - Output target: >= 4 KB (Step 10 check is >= 2 KB; we aim higher).

Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.intelligence.utils.agent_files import find_agent_file  # MCE-13.6
from engine.paths import ARTIFACTS, PROCESSING, ROOT

logger = logging.getLogger("mce.dossier_generator")

_GENERATOR_VERSION = "dossier_generator v1.0.0"

# Regex that matches the baseline comment written into every generated dossier header.
# Format: <!-- insights_baseline: N -->
_BASELINE_RE = re.compile(r"<!--\s*insights_baseline:\s*(\d+)\s*-->")

_DEFAULT_REGENERATE_THRESHOLD_PCT = 20

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _slug_to_person_name(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.split("-"))


_PLACEHOLDER_CHUNKS = {"chunk_?", "?", "", "unknown", "none", "null"}


def _normalize_chunk_id(raw: str) -> str:
    """Strip duplicate 'chunk_' prefix so we don't emit [chunk_chunk_X]."""
    s = (raw or "").strip()
    if s.startswith("chunk_"):
        s = s[len("chunk_") :]
    return s


def _chunk_ref(ins: dict, fallback: str = "") -> str:
    """Return `[chunk_X]` inline citation for an insight (Story MCE-3.2).

    Resolution order:
        1. ins["chunks"][0] (most common — insight already cites first chunk)
        2. ins["chunk_id"]
        3. ins["id"] (insight id as last-resort surrogate)
        4. fallback param (caller-provided default)

    Skips placeholder values like `chunk_?` and normalizes duplicate prefixes.
    Returns empty string if nothing resolves.
    """
    if not isinstance(ins, dict):
        return f"[chunk_{fallback}]" if fallback else ""

    candidates: list[str] = []
    chunks = ins.get("chunks") or []
    if isinstance(chunks, list):
        for c in chunks:
            if isinstance(c, str):
                candidates.append(c)
            elif isinstance(c, dict) and c.get("id"):
                candidates.append(str(c["id"]))
    if ins.get("chunk_id"):
        candidates.append(str(ins["chunk_id"]))
    if ins.get("id"):
        candidates.append(str(ins["id"]))
    if fallback:
        candidates.append(fallback)

    for raw in candidates:
        if not raw or raw.strip().lower() in _PLACEHOLDER_CHUNKS:
            continue
        normalized = _normalize_chunk_id(raw)
        if normalized and normalized.lower() not in _PLACEHOLDER_CHUNKS:
            return f"[chunk_{normalized}]"
    return ""


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Load YAML, returning {} on missing/error."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("Failed to load %s: %s", path, exc)
        return {}


def _load_insights(slug: str) -> dict[str, Any]:
    """Load INSIGHTS-STATE.json for slug."""
    insights_path = ROOT / ".data" / "artifacts" / "insights" / slug / "INSIGHTS-STATE.json"
    if not insights_path.exists():
        return {}
    try:
        with open(insights_path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("Failed to load INSIGHTS-STATE.json for %s: %s", slug, exc)
        return {}


def _count_current_insights(slug: str) -> int:
    """Return total insight count from INSIGHTS-STATE.json for *slug*.

    Counts all insights across every person entry (mirrors the summation in
    ``create_dossier``).  Returns 0 if data unavailable.
    """
    insights_data = _load_insights(slug)
    persons = insights_data.get("persons", {})
    total = 0
    for person_data in persons.values():
        if isinstance(person_data, dict):
            total += len(person_data.get("insights", []))
    return total


def _read_baseline_from_dossier(dossier_path: Path) -> int | None:
    """Extract the ``<!-- insights_baseline: N -->`` value from an existing dossier.

    Returns the integer N if found, or None when the comment is absent (legacy
    dossiers pre-dating this feature).
    """
    if not dossier_path.exists():
        return None
    try:
        text = dossier_path.read_text(encoding="utf-8", errors="ignore")
        m = _BASELINE_RE.search(text)
        if m:
            return int(m.group(1))
    except Exception as exc:
        logger.debug("Could not read baseline from %s: %s", dossier_path, exc)
    return None


def should_regenerate(
    slug: str,
    bucket: str = "external",
    threshold_pct: int = _DEFAULT_REGENERATE_THRESHOLD_PCT,
) -> bool:
    """Return True when the dossier should be regenerated due to insight growth.

    Decision rules (evaluated in order):
        1. Dossier does not exist → False (``create_dossier`` will create it
           normally; no need to force).
        2. Dossier has no ``<!-- insights_baseline: N -->`` header → True
           (legacy migration: regenerate unconditionally so baseline is written).
        3. Current insight count / baseline > 1 + (threshold_pct / 100) → True.
        4. Otherwise → False (growth is within threshold; idempotent skip wins).

    Args:
        slug: Person slug (kebab-case).
        bucket: Knowledge bucket (``external`` | ``business``).
        threshold_pct: Growth percentage that triggers regeneration (default 20).

    Returns:
        bool
    """
    dossier_path = ROOT / "knowledge" / bucket / "dossiers" / "persons" / f"dossier-{slug}.md"

    # Rule 1: dossier doesn't exist yet — no need to force
    if not dossier_path.exists():
        return False

    # Rule 2: legacy dossier with no baseline comment — migrate immediately
    baseline = _read_baseline_from_dossier(dossier_path)
    if baseline is None:
        logger.info(
            "should_regenerate(%s): no baseline found — legacy dossier, forcing regenerate",
            slug,
        )
        return True

    # Rule 3: growth check
    current = _count_current_insights(slug)
    if baseline == 0:
        # Pathological case: baseline=0 but dossier exists; regenerate if any insights now
        if current > 0:
            logger.info(
                "should_regenerate(%s): baseline=0 but current=%d — forcing regenerate",
                slug,
                current,
            )
            return True
        return False

    ratio = current / baseline
    threshold_ratio = 1.0 + (threshold_pct / 100.0)
    if ratio > threshold_ratio:
        logger.info(
            "should_regenerate(%s): current=%d baseline=%d ratio=%.2f > threshold=%.2f — forcing regenerate",
            slug,
            current,
            baseline,
            ratio,
            threshold_ratio,
        )
        return True

    logger.debug(
        "should_regenerate(%s): current=%d baseline=%d ratio=%.2f <= threshold=%.2f — skip",
        slug,
        current,
        baseline,
        ratio,
        threshold_ratio,
    )
    return False


def _extract_by_tag(insights_data: dict[str, Any], slug: str) -> dict[str, list[dict]]:
    """Group insights by tag from INSIGHTS-STATE.json persons block."""
    persons = insights_data.get("persons", {})
    person_name = _slug_to_person_name(slug)
    person_data = persons.get(person_name, {})
    if not person_data:
        for key, val in persons.items():
            if isinstance(val, dict):
                person_data = val
                break
    insights = person_data.get("insights", []) if isinstance(person_data, dict) else []
    by_tag: dict[str, list[dict]] = defaultdict(list)
    for ins in insights:
        if isinstance(ins, dict):
            by_tag[ins.get("tag", "?")].append(ins)
    return dict(by_tag)


def _read_agent_identity(slug: str, bucket: str) -> str:
    """Extract the Identidade section from agent.md (case-insensitive, MCE-13.6)."""
    agent_dir = ROOT / "agents" / bucket / slug
    agent_md = find_agent_file(agent_dir, "agent.md")
    if agent_md is None or not agent_md.exists():
        return ""
    try:
        text = agent_md.read_text(encoding="utf-8")
        # Strip frontmatter
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                text = text[end + 3 :]
        # Extract ## Identidade section
        match = re.search(r"##\s+Identidade\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    except Exception as exc:
        logger.debug("Could not read AGENT.md identity for %s: %s", slug, exc)
    return ""


def _read_soul_tone(slug: str, bucket: str) -> dict[str, Any]:
    """Extract tone table and sig phrases from soul.md (case-insensitive, MCE-13.6)."""
    agent_dir = ROOT / "agents" / bucket / slug
    soul_md = find_agent_file(agent_dir, "soul.md")
    if soul_md is None or not soul_md.exists():
        return {}
    try:
        text = soul_md.read_text(encoding="utf-8")
        result: dict[str, Any] = {}
        # Extract personality section
        match = re.search(
            r"##\s+Personalidade\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL | re.IGNORECASE
        )
        if match:
            result["personality"] = match.group(1).strip()
        return result
    except Exception as exc:
        logger.debug("Could not read SOUL.md for %s: %s", slug, exc)
        return {}


def _detect_sources(slug: str) -> list[str]:
    """Detect source files from inbox or chunks."""
    inbox = ROOT / "knowledge" / "external" / "inbox" / slug
    sources: list[str] = []
    if inbox.exists():
        for p in sorted(inbox.iterdir()):
            if p.suffix in (".txt", ".md", ".pdf", ".mp4", ".mp3"):
                sources.append(f"knowledge/external/inbox/{slug}/{p.name}")
    if not sources:
        chunks_dir = ROOT / ".data" / "artifacts" / "chunks" / slug
        if chunks_dir.exists():
            for p in sorted(chunks_dir.iterdir()):
                if p.suffix in (".json",):
                    name = p.stem.replace("chunks-", "")
                    if name:
                        sources.append(f"knowledge/external/inbox/{slug}/{name}.txt")
    return sources[:10]


def _cross_ref_agents(slug: str, frameworks: list[dict]) -> list[str]:
    """Scan agents for shared keywords and return cross-reference suggestions."""
    # Keywords from this person's frameworks/philosophies
    keywords: list[str] = []
    for ins in frameworks[:5]:
        text = ins.get("insight", "")
        # Extract significant words
        words = re.findall(r"\b[A-Z][a-z]{3,}\b", text)
        keywords.extend(words[:3])
    if not keywords:
        keywords = ["digital", "remote", "organic"]

    refs: list[str] = []
    agents_root = ROOT / "agents"
    if not agents_root.exists():
        return refs

    # MCE-13.6: scan both lowercase and UPPERCASE conventions; deduplicate paths
    _seen_paths: set = set()
    for _pattern in ("agent.md", "AGENT.md"):
        for agent_md in agents_root.rglob(_pattern):
            if agent_md in _seen_paths:
                continue
            _seen_paths.add(agent_md)
            if slug in str(agent_md):
                continue
            try:
                text = agent_md.read_text(encoding="utf-8", errors="ignore")
                for kw in keywords:
                    if kw.lower() in text.lower():
                        # Derive agent slug from path
                        rel = agent_md.relative_to(agents_root)
                        parts = list(rel.parts)
                        if len(parts) >= 2:
                            agent_slug = parts[-2]
                            ref_line = (
                                f"- `{agent_slug}` — compartilha domínio: {kw} "
                                f"[chunk_crossref-{slug}-{agent_slug}]"
                            )
                            if ref_line not in refs:
                                refs.append(ref_line)
                        break
            except Exception:
                pass
            if len(refs) >= 5:
                break

    return refs


# ---------------------------------------------------------------------------
# Attribution / Contributors (Story MCE-11.7)
# ---------------------------------------------------------------------------

# Delimiters used to identify and replace the Contributors section in-place
# when a theme dossier is updated multiple times.
_CONTRIB_START = "<!-- attribution-start -->"
_CONTRIB_END = "<!-- attribution-end -->"


def calculate_attribution(insights: list[dict]) -> list[dict]:
    """Calculate per-expert contribution percentages from a list of insights.

    Each insight dict is expected to carry a ``source_person`` or ``person``
    field (string slug or display name). If neither is present the insight is
    counted under the sentinel value ``"unknown"``.

    Args:
        insights: List of insight dicts (any schema — only the person field is
            read).

    Returns:
        Sorted list of ``{"expert": str, "count": int, "percentage": int}``
        dicts ordered by percentage descending, then expert name ascending.
        Returns an empty list when *insights* is empty.

    Examples::

        >>> calculate_attribution([{"source_person": "JH"} for _ in range(9)]
        ...     + [{"source_person": "CG"}])
        [{'expert': 'JH', 'count': 9, 'percentage': 90},
         {'expert': 'CG', 'count': 1, 'percentage': 10}]
    """
    counter: Counter[str] = Counter(
        ins.get("source_person") or ins.get("person") or "unknown"
        for ins in insights
        if isinstance(ins, dict)
    )
    total = sum(counter.values())
    if total == 0:
        return []
    return sorted(
        [
            {"expert": k, "count": v, "percentage": round(v / total * 100)}
            for k, v in counter.items()
        ],
        key=lambda x: (-x["percentage"], x["expert"]),
    )


def render_contributors_section(
    attribution: list[dict],
    total: int,
    updated_date: str,
) -> str:
    """Render the Contributors markdown section for injection into a theme dossier.

    The section is wrapped in HTML comment delimiters so it can be located and
    replaced by :func:`replace_contributors_section` on subsequent updates.

    Args:
        attribution: Output of :func:`calculate_attribution`.
        total: Total insight count (for the footer line).
        updated_date: ISO date string (``YYYY-MM-DD``) for the footer.

    Returns:
        Markdown string including delimiters, or empty string when *attribution*
        is empty (AC6 — zero insights → section omitted).
    """
    if not attribution:
        return ""

    lines = [
        _CONTRIB_START,
        "",
        "## Contributors",
        "",
        "| Expert | Insights | % |",
        "|--------|----------|---|",
    ]
    for entry in attribution:
        lines.append(f"| {entry['expert']} | {entry['count']} | {entry['percentage']}% |")

    lines.append("")
    lines.append(f"> Baseado em {total} insights. Atualizado em {updated_date}.")
    lines.append("")
    lines.append(_CONTRIB_END)

    return "\n".join(lines)


def replace_contributors_section(dossier_text: str, new_section: str) -> str:
    """Replace (or insert) the Contributors section in an existing dossier.

    Uses ``<!-- attribution-start -->`` / ``<!-- attribution-end -->`` delimiters
    to locate and replace the block safely without touching adjacent content.

    If no existing section is found, the new section is inserted immediately
    after the first H1 heading (before the first H2).

    Args:
        dossier_text: Full text of the existing dossier file.
        new_section: Output of :func:`render_contributors_section`.

    Returns:
        Updated dossier text with Contributors section replaced/inserted.
    """
    if not new_section:
        return dossier_text

    # Replace existing delimited block if present.
    pattern = re.compile(
        re.escape(_CONTRIB_START) + r".*?" + re.escape(_CONTRIB_END),
        re.DOTALL,
    )
    if pattern.search(dossier_text):
        return pattern.sub(new_section, dossier_text)

    # No existing block — insert after H1, before first H2.
    # Pattern: the H1 line + its trailing newlines, then we inject before "## ".
    h2_match = re.search(r"(?m)^## ", dossier_text)
    if h2_match:
        insert_pos = h2_match.start()
        return dossier_text[:insert_pos] + new_section + "\n\n" + dossier_text[insert_pos:]

    # Fallback: append at end.
    return dossier_text + "\n\n" + new_section


# ---------------------------------------------------------------------------
# Contradictions / Pontos de Tensão (Story MCE-11.2)
# ---------------------------------------------------------------------------

_QUALIFYING_PRIORITIES: frozenset[str] = frozenset({"HIGH", "MEDIUM"})


def _load_review_queue(slug: str) -> list[dict]:
    """Load contradiction entries for *slug* from REVIEW-QUEUE.json.

    Resolution order (AC1):
      1. Per-slug:  .data/artifacts/canonical/{slug}/REVIEW-QUEUE.json
      2. Global:    .data/processing/canonical/REVIEW-QUEUE.json  (filtered by person_slug)
      3. Not found: return []

    Only items with type==contradiction AND priority in {HIGH, MEDIUM} are returned (AC2).
    The real schema (v2.0.0) wraps items under a top-level "items" key; the global queue
    uses "review_queue". Both flat-list and wrapped formats are tolerated.
    """
    per_slug_path = ARTIFACTS / "canonical" / slug / "REVIEW-QUEUE.json"
    global_path = PROCESSING / "canonical" / "REVIEW-QUEUE.json"

    raw_items: list[dict] = []

    if per_slug_path.exists():
        try:
            data = json.loads(per_slug_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Schema v2.0.0 uses "items"; guard against other wrapper keys
                raw_items = data.get("items") or data.get("review_queue") or []
            elif isinstance(data, list):
                raw_items = data
        except Exception as exc:
            logger.debug("Failed to read per-slug REVIEW-QUEUE for %s: %s", slug, exc)
    elif global_path.exists():
        try:
            data = json.loads(global_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                raw_items = data.get("items") or data.get("review_queue") or []
            elif isinstance(data, list):
                raw_items = data
            # Filter to this slug's entries
            raw_items = [i for i in raw_items if i.get("person_slug") == slug]
        except Exception as exc:
            logger.debug("Failed to read global REVIEW-QUEUE filtering for %s: %s", slug, exc)

    return [
        item
        for item in raw_items
        if isinstance(item, dict)
        and item.get("type") == "contradiction"
        and str(item.get("priority", "")).upper() in _QUALIFYING_PRIORITIES
    ]


def _render_tensions_section(slug: str) -> str:
    """Return the '## ⚠ Pontos de Tensao' markdown section string, or '' if none.

    Each tension entry is rendered as:
        ### Tensao N: {short_label}
        - **Claim A:** {source_insight_ids[0]}
        - **Claim B:** {source_insight_ids[1]}
        - **Severidade:** {priority}

    AC4: Returns empty string when no qualifying contradictions exist — caller
    must omit the section entirely, leaving no empty header in the dossier.
    """
    items = _load_review_queue(slug)
    if not items:
        return ""

    lines: list[str] = ["## ⚠ Pontos de Tensao", ""]
    for n, item in enumerate(items, 1):
        source_ids = item.get("source_insight_ids") or []
        claim_a = source_ids[0] if len(source_ids) > 0 else "?"
        claim_b = source_ids[1] if len(source_ids) > 1 else "?"
        question = item.get("question") or f"Tensao entre {claim_a} e {claim_b}"
        priority = str(item.get("priority", "?")).capitalize()

        # Short label: strip the "Insight X vs Insight Y — keywords: ..." prefix
        # and keep only the keywords portion for brevity, or fall back to index label.
        short_label = question
        if " — keywords: " in question:
            short_label = question.split(" — keywords: ", 1)[1].strip()
        elif len(question) > 80:
            short_label = question[:77] + "..."

        lines.append(f"### Tensao {n}: {short_label}")
        lines.append(f"- **Claim A:** {claim_a}")
        lines.append(f"- **Claim B:** {claim_b}")
        lines.append(f"- **Severidade:** {priority}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Optional LLM bio
# ---------------------------------------------------------------------------


def _try_llm_bio(
    slug: str,
    by_tag: dict[str, list[dict]],
    values_data: dict,
    voice_data: dict,
    agent_identity: str,
) -> str | None:
    """Attempt LLM-generated 3-paragraph bio for Section 1.

    Returns None if LLM unavailable.  Cost target: < $0.02 (gpt-4o-mini).
    """
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter
    except ImportError:
        logger.debug("llm_router not available — using deterministic bio")
        return None

    person_name = _slug_to_person_name(slug)
    filosofias = [ins.get("insight", "") for ins in by_tag.get("[FILOSOFIA]", [])[:3]]
    frameworks = [ins.get("insight", "") for ins in by_tag.get("[FRAMEWORK]", [])[:3]]
    values = [v.get("value", "") for v in values_data.get("values", [])[:3] if isinstance(v, dict)]
    sig_phrases = [p.get("phrase", "") for p in voice_data.get("signature_phrases", [])[:3]]

    # Phase 2 MCE-6.0: load from .prompt.md, fall back to inline if file missing.
    _prompts_dir = Path(__file__).parent / "prompts"
    _consolidate_tmpl_path = _prompts_dir / "consolidate.prompt.md"
    _consolidate_tmpl = ""
    try:
        _consolidate_tmpl = _consolidate_tmpl_path.read_text(encoding="utf-8")
    except OSError:
        pass

    _filosofias_block = chr(10).join(f"- {f[:100]}" for f in filosofias)
    _frameworks_block = chr(10).join(f"- {f[:100]}" for f in frameworks)
    _values_str = ", ".join(values)
    _sig_phrases_block = chr(10).join(f'- "{p[:80]}"' for p in sig_phrases)
    _agent_identity_trunc = agent_identity[:400] if agent_identity else "(não disponível)"

    if _consolidate_tmpl:
        prompt = _consolidate_tmpl.format(
            person_name=person_name,
            slug=slug,
            agent_identity=_agent_identity_trunc,
            filosofias_block=_filosofias_block,
            frameworks_block=_frameworks_block,
            values_str=_values_str,
            sig_phrases_block=_sig_phrases_block,
        )
    else:
        prompt = f"""Você é um especialista em síntese de perfis para sistemas de IA.

PESSOA: {person_name}
SLUG: {slug}

IDENTIDADE (do AGENT.md):
{agent_identity[:400] if agent_identity else '(não disponível)'}

FILOSOFIAS (L1):
{chr(10).join(f'- {f[:100]}' for f in filosofias)}

FRAMEWORKS (L4):
{chr(10).join(f'- {f[:100]}' for f in frameworks)}

VALORES (L7): {', '.join(values)}

FRASES ASSINATURA (L8):
{chr(10).join(f'- "{p[:80]}"' for p in sig_phrases)}

TAREFA: Escreva uma narrativa biográfica de 2-3 parágrafos em português brasileiro
sobre {person_name}. O texto será a Seção 1 (Identidade Narrativa) de um dossiê
estruturado. Seja específico, use os dados acima, evite generalizações.

Responda APENAS o texto dos parágrafos, sem marcadores extras."""

    try:
        router = LLMRouter()
        raw = router.run_prompt(
            prompt,
            provider="openai",
            step="dossier_bio",
            max_output_tokens=400,
        )
        if raw and len(raw.strip()) > 100:
            return raw.strip()
    except Exception as exc:
        logger.debug("LLM bio failed for %s: %s — using deterministic", slug, exc)

    return None


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_section1_bio(
    slug: str,
    by_tag: dict[str, list[dict]],
    values_data: dict,
    voice_data: dict,
    agent_identity: str,
    llm_bio: str | None,
) -> str:
    if llm_bio:
        return llm_bio

    person_name = _slug_to_person_name(slug)
    values = [v.get("value", "") for v in values_data.get("values", [])[:3] if isinstance(v, dict)]
    values_str = ", ".join(values) or "(valores a extrair)"

    # Use agent identity if available
    if agent_identity and len(agent_identity) > 80:
        return agent_identity

    filosofias = by_tag.get("[FILOSOFIA]", [])
    first_filo = filosofias[0].get("insight", "") if filosofias else ""
    frameworks = by_tag.get("[FRAMEWORK]", [])
    first_fw = frameworks[0].get("insight", "") if frameworks else ""

    return f"""{person_name} é uma autoridade em sua área, com uma metodologia própria \
derivada dos insights extraídos de suas fontes. Esta biografia é um placeholder \
determinístico — gere a versão completa via LLM (llm_bio) ou edite manualmente com \
base nos 10 layers de DNA.

Valores principais: {values_str}. \
{first_filo[:120] if first_filo else '(Primeira filosofia central a ser extraída das fontes.)'}

{first_fw[:200] if first_fw else '(Primeiro framework principal a ser extraído das fontes.)'}"""


def _build_section2_filosofias(by_tag: dict[str, list[dict]]) -> str:
    items = by_tag.get("[FILOSOFIA]", [])[:5]
    if not items:
        return "(Nenhuma filosofia extraída)"
    lines = []
    for i, ins in enumerate(items, 1):
        content = ins.get("insight", "")[:200]
        ins_id = ins.get("id", f"F{i}")
        ref = _chunk_ref(ins, fallback=ins_id)
        lines.append(f"**{i}. [{ins_id}]** {content} {ref}")
    return "\n\n".join(lines)


def _build_section3_models_frameworks(by_tag: dict[str, list[dict]]) -> str:
    models = by_tag.get("[MODELO-MENTAL]", [])[:3]
    frameworks = by_tag.get("[FRAMEWORK]", [])[:5]

    lines = ["### Modelos Mentais (L2)\n"]
    if models:
        for ins in models:
            content = ins.get("insight", "")[:180]
            ref = _chunk_ref(ins, fallback=ins.get("id", ""))
            lines.append(f"- {content} {ref}")
    else:
        lines.append("- (Nenhum modelo mental extraído)")

    lines.append("\n### Frameworks Principais (L4)\n")
    if frameworks:
        for ins in frameworks:
            content = ins.get("insight", "")[:180]
            ins_id = ins.get("id", "?")
            ref = _chunk_ref(ins, fallback=ins_id)
            lines.append(f"- **[{ins_id}]** {content} {ref}")
    else:
        lines.append("- (Nenhum framework extraído)")

    return "\n".join(lines)


def _build_section4_heuristicas(by_tag: dict[str, list[dict]]) -> str:
    heuristicas = by_tag.get("[HEURISTICA]", [])[:5]
    metodologias = by_tag.get("[METODOLOGIA]", [])[:3]

    lines = ["### Heurísticas Operacionais (L3)\n"]
    if heuristicas:
        for ins in heuristicas:
            content = ins.get("insight", "")[:180]
            ref = _chunk_ref(ins, fallback=ins.get("id", ""))
            lines.append(f"- {content} {ref}")
    else:
        lines.append("- (Nenhuma heurística extraída)")

    lines.append("\n### Metodologias Acionáveis (L5 — top 3)\n")
    if metodologias:
        for ins in metodologias:
            content = ins.get("insight", "")[:200]
            ins_id = ins.get("id", "?")
            ref = _chunk_ref(ins, fallback=ins_id)
            lines.append(f"- **[{ins_id}]** {content} {ref}")
    else:
        lines.append("- (Nenhuma metodologia extraída)")

    return "\n".join(lines)


def _build_section5_voice_behavioral(
    voice_data: dict,
    behavioral_data: dict,
) -> str:
    tone = voice_data.get("tone_profile", {})
    certainty = tone.get("certainty", {}).get("score", "?")
    authority = tone.get("authority", {}).get("score", "?")
    warmth = tone.get("warmth", {}).get("score", "?")
    directness = tone.get("directness", {}).get("score", "?")
    teaching = tone.get("teaching_focus", {}).get("score", "?")

    sig_phrases = voice_data.get("signature_phrases", [])[:5]
    sig_lines = (
        "\n".join(
            f'- "{p.get("phrase", "")[:120]}" {_chunk_ref(p, fallback=p.get("id", ""))}'
            for p in sig_phrases
        )
        or "- (Nenhuma frase extraída)"
    )

    patterns = behavioral_data.get("patterns", behavioral_data.get("behavioral_patterns", []))[:3]
    bp_lines = (
        "\n".join(
            f"- **{p.get('pattern_name', '')[:60]}**: {p.get('action', '')[:100]} "
            f"{_chunk_ref(p, fallback=p.get('id', ''))}"
            for p in patterns
            if isinstance(p, dict)
        )
        or "- (Nenhum padrão extraído)"
    )

    comm = voice_data.get("communication_patterns", {})
    opening_dict = comm.get("opening_hooks", {}) if isinstance(comm, dict) else {}
    structure_dict = comm.get("story_structure", {}) if isinstance(comm, dict) else {}
    closing_dict = comm.get("closing_signatures", {}) if isinstance(comm, dict) else {}
    opening = opening_dict.get("padrao", "Dados impactantes")
    structure = structure_dict.get("padrao", "Problema → Solução → CTA")
    closing = closing_dict.get("padrao", "CTA direto")
    opening_ref = _chunk_ref(opening_dict, fallback="L8-opening")
    structure_ref = _chunk_ref(structure_dict, fallback="L8-structure")
    closing_ref = _chunk_ref(closing_dict, fallback="L8-closing")

    return f"""\
### Perfil de Tom (L8)

| Dimensão | Score (0-10) |
|----------|-------------|
| Certeza | {certainty} |
| Autoridade | {authority} |
| Calor | {warmth} |
| Diretividade | {directness} |
| Foco Pedagógico | {teaching} |

### Frases Assinatura (L8)

{sig_lines}

### Padrões Comportamentais (L6)

{bp_lines}

### Padrões de Comunicação

- **Abertura:** {opening} {opening_ref}
- **Estrutura narrativa:** {structure} {structure_ref}
- **Fechamento:** {closing} {closing_ref}"""


def _build_section6_obsessions_paradoxes(
    obsessions_data: dict,
    paradoxes_data: dict,
) -> str:
    obsessions = obsessions_data.get("obsessions", [])[:3]
    paradoxes = paradoxes_data.get("paradoxes", [])[:3]

    lines = ["### Obsessões (L9)\n"]
    if obsessions:
        for obs in obsessions:
            name = obs.get("obsession", "?")
            freq = obs.get("frequency", "?")
            quote = obs.get("quote", "")[:150]
            ref = _chunk_ref(obs, fallback=obs.get("id", ""))
            lines.append(f"**{name}** (frequência={freq}) {ref}")
            if quote:
                lines.append(f'> "{quote}" {ref}')
            lines.append("")
    else:
        lines.append("(Nenhuma obsessão extraída)")

    lines.append("\n### Paradoxos Produtivos (L10)\n")
    if paradoxes:
        for par in paradoxes:
            pid = par.get("id", "?")
            ta = par.get("tension_a", "")[:80]
            tb = par.get("tension_b", "")[:80]
            resolution = par.get("resolution", "")[:120]
            ref = _chunk_ref(par, fallback=pid)
            lines.append(f"**{pid}:** {ta} ↔ {tb} {ref}")
            if resolution:
                lines.append(f"*Resolução:* {resolution}")
            lines.append("")
    else:
        lines.append("(Nenhum paradoxo extraído)")

    return "\n".join(lines)


def _build_section7_crossrefs(slug: str, frameworks: list[dict]) -> str:
    refs = _cross_ref_agents(slug, frameworks)
    if not refs:
        return "(Nenhum agente com domínio compartilhado detectado automaticamente.)"
    return "\n".join(refs)


# ---------------------------------------------------------------------------
# Dossier assembler
# ---------------------------------------------------------------------------


def create_dossier(
    slug: str,
    bucket: str = "external",
    *,
    force: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Generate and write a structured dossier for the given slug.

    Args:
        slug: Person slug (kebab-case).
        bucket: Knowledge bucket (``external`` | ``business``).
        force: If True, overwrite even if dossier already exists.
        use_llm: If True, attempt LLM bio refinement (gpt-4o-mini).

    Returns:
        Dict with keys:
            - ``status`` (str): ``written`` | ``skipped`` | ``error``
            - ``dossier_path`` (str): Absolute path to dossier file.
            - ``sections_filled`` (int): Number of sections with content.
            - ``size_bytes`` (int): Final dossier size in bytes.
            - ``llm_used`` (bool): Whether LLM bio was used.
            - ``error`` (str, optional): Error message on failure.
    """
    person_name = _slug_to_person_name(slug)
    generated_at = _now_iso()

    dossier_dir = ROOT / "knowledge" / bucket / "dossiers" / "persons"
    dossier_path = dossier_dir / f"dossier-{slug}.md"

    # Idempotency check
    if dossier_path.exists() and not force:
        size = dossier_path.stat().st_size
        logger.info(
            "Dossier already exists for %s (%d bytes) — skipping (use force=True)", slug, size
        )
        return {
            "status": "skipped",
            "reason": "dossier already exists",
            "dossier_path": str(dossier_path),
            "sections_filled": 7,
            "size_bytes": size,
            "llm_used": False,
        }

    # Load all sources
    insights_data = _load_insights(slug)
    by_tag = _extract_by_tag(insights_data, slug)
    total_insights = sum(len(v) for v in by_tag.values())

    dna_base = ROOT / "knowledge" / bucket / "dna" / "persons" / slug
    voice_data = _load_yaml_safe(dna_base / "voice-dna.yaml")
    behavioral_data = _load_yaml_safe(dna_base / "behavioral-patterns.yaml")
    values_data = _load_yaml_safe(dna_base / "values-hierarchy.yaml")
    obsessions_data = _load_yaml_safe(dna_base / "obsessions.yaml")
    paradoxes_data = _load_yaml_safe(dna_base / "paradoxes.yaml")

    agent_identity = _read_agent_identity(slug, bucket)
    sources = _detect_sources(slug)

    # Count what we actually have
    chunks_dir = ROOT / ".data" / "artifacts" / "chunks" / slug
    chunks_count = 0
    if chunks_dir.exists():
        for p in chunks_dir.iterdir():
            if p.suffix == ".json":
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        chunks_count += len(data)
                    elif isinstance(data, dict):
                        chunks_count += len(data.get("chunks", [data]))
                except Exception:
                    chunks_count += 1

    checkpoint_path = (
        ROOT
        / ".claude"
        / "mission-control"
        / "mce"
        / slug
        / "checkpoints"
        / "identity-checkpoint.json"
    )
    checkpoint_verdict = "APPROVE"
    if checkpoint_path.exists():
        try:
            cp = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            checkpoint_verdict = cp.get("verdict", "APPROVE")
        except Exception:
            pass

    frameworks_list = by_tag.get("[FRAMEWORK]", [])

    # Optional LLM bio
    llm_bio: str | None = None
    llm_used = False
    if use_llm:
        llm_bio = _try_llm_bio(slug, by_tag, values_data, voice_data, agent_identity)
        llm_used = llm_bio is not None

    # Build all sections
    s1 = _build_section1_bio(slug, by_tag, values_data, voice_data, agent_identity, llm_bio)
    s2 = _build_section2_filosofias(by_tag)
    s3 = _build_section3_models_frameworks(by_tag)
    s4 = _build_section4_heuristicas(by_tag)
    s5 = _build_section5_voice_behavioral(voice_data, behavioral_data)
    s6 = _build_section6_obsessions_paradoxes(obsessions_data, paradoxes_data)
    s7 = _build_section7_crossrefs(slug, frameworks_list)
    # Story MCE-11.2: contradictions surfaced as Pontos de Tensao (empty string = no section)
    tensions_section = _render_tensions_section(slug)

    sections_filled = sum(
        1 for s in [s1, s2, s3, s4, s5, s6, s7] if s and "(Nenhum" not in s and len(s.strip()) > 20
    )

    sources_count = len(sources) or max(1, len(by_tag))
    sources_block = (
        "\n".join(f"- {s}" for s in sources)
        if sources
        else f"- knowledge/{bucket}/inbox/{slug}/ (via MCE pipeline)"
    )

    dna_layers_complete = (
        sum(
            1
            for p in [
                dna_base / "voice-dna.yaml",
                dna_base / "behavioral-patterns.yaml",
                dna_base / "values-hierarchy.yaml",
                dna_base / "obsessions.yaml",
                dna_base / "paradoxes.yaml",
            ]
            if p.exists()
        )
        + 5
    )  # L1-L5 from insights

    # Story MCE-3.16: compute density indicator for header
    try:
        from engine.intelligence.density import (
            compute_dossier_density,
            render_density_indicator,
        )

        density_info = compute_dossier_density(slug, bucket)
        density_score = int(density_info.get("density", 0))
        density_indicator = render_density_indicator(density_score)
    except Exception:
        density_score = 0
        density_indicator = "◯◯◯◯◯ (0)"

    # Story MCE-11.2: tensions_block is either a full section with trailing \n\n---\n
    # or empty string (AC4 — no section when no qualifying contradictions)
    tensions_block = f"\n{tensions_section}\n\n---\n\n" if tensions_section else "\n"

    dossier_md = f"""\
---
slug: {slug}
person: {person_name}
bucket: {bucket}
generated_at: {generated_at}
generator: {_GENERATOR_VERSION}
version: 1.0.0
status: complete
auto_generated: true
sources_count: {sources_count}
chunks_count: {chunks_count}
insights_count: {total_insights}
dna_layers_complete: {dna_layers_complete}
density: {density_score}
identity_checkpoint: {checkpoint_verdict}
---
<!-- insights_baseline: {total_insights} -->

# Dossier: {person_name}

> Gerado automaticamente por `{_GENERATOR_VERSION}`.
> {total_insights} insights extraídos | {dna_layers_complete}/10 layers DNA | checkpoint={checkpoint_verdict}
> Densidade: {density_indicator}

---

## 1. Identidade Narrativa

{s1}

---

## 2. Filosofias Centrais (L1)

{s2}

---

## 3. Modelos Mentais & Frameworks (L2 + L4)

{s3}

---

## 4. Heurísticas Operacionais (L3 + L5)

{s4}

---

## 5. Voice DNA & Behavioral (L6 + L8)

{s5}

---

## 6. Obsessions & Paradoxes (L9 + L10)

{s6}

---

## 7. Cross-References

{s7}

---

## Sources

{sources_block}

---
{tensions_block}
*Gerado por `engine/intelligence/pipeline/mce/dossier_generator.py` v1.0.0*
*Frente 8 — MCE Campaign 12/12 | Step 10 (Consolidation/Forge)*
"""

    # Write dossier
    try:
        dossier_dir.mkdir(parents=True, exist_ok=True)
        dossier_path.write_text(dossier_md, encoding="utf-8")
        size_bytes = len(dossier_md.encode("utf-8"))
        logger.info(
            "Dossier written for %s: %d bytes, %d sections, llm=%s",
            slug,
            size_bytes,
            sections_filled,
            llm_used,
        )
        return {
            "status": "written",
            "dossier_path": str(dossier_path),
            "sections_filled": sections_filled,
            "size_bytes": size_bytes,
            "llm_used": llm_used,
            "insights_count": total_insights,
            "dna_layers_complete": dna_layers_complete,
        }
    except Exception as exc:
        logger.error("Failed to write dossier for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "dossier_path": str(dossier_path),
            "sections_filled": 0,
            "size_bytes": 0,
            "llm_used": llm_used,
        }


def ensure_dossier_created(
    slug: str,
    bucket: str = "external",
    *,
    force: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Non-fatal wrapper around create_dossier. Designed for pipeline wiring.

    Never raises. Returns structured result with status='error' on failure.
    """
    try:
        return create_dossier(slug, bucket, force=force, use_llm=use_llm)
    except Exception as exc:
        logger.warning("ensure_dossier_created failed for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "dossier_path": "",
            "sections_filled": 0,
            "size_bytes": 0,
            "llm_used": False,
        }
