"""
cascading.py -- Post-extraction cascade for MCE pipeline
=========================================================
Routes extracted insights from INSIGHTS-STATE.json to:
  1. Cargo agent MEMORY.md files (via DNA-CONFIG.yaml reverse lookup)
  2. Theme dossiers in knowledge/external/dossiers/themes/

Ported from .claude/hooks/post_batch_cascading.py but adapted to work
with the INSIGHTS-STATE.json format (person-keyed, not batch-keyed).

Called directly by orchestrate.cmd_finalize() as a Python import,
not as a PostToolUse hook -- so it fires reliably every time.

Reading strategy (Story MCE-11.14):
    Always reads per-slug INSIGHTS-STATE.json:
        .data/artifacts/insights/{slug}/INSIGHTS-STATE.json
    This file contains the full rich schema: insight, chunks[], priority,
    confidence, status, provenance.  The global aggregated file at
        .data/artifacts/insights/INSIGHTS-STATE.json
    has a degraded schema (id, tag, title only) and is NOT used for
    cascade routing decisions.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from engine.paths.
    - Append-only to MEMORY.md / dossier files.
    - JSONL logging to logs/cascading.jsonl.

Version: 1.1.0
Date: 2026-05-27
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.intelligence.pipeline.mce.dossier_generator import (
    calculate_attribution,
    render_contributors_section,
    replace_contributors_section,
)
from engine.intelligence.pipeline.mce.theme_agent_map import load_theme_agent_map
from engine.intelligence.pipeline.mce.theme_router import ThemeRouter
from engine.paths import (
    AGENTS_CARGO,
    ARTIFACTS,
    EXTERNAL_DOSSIERS_PERSONS_BY_THEME,
    KNOWLEDGE_EXTERNAL,
    LOGS,
    ROOT,
)

# ---------------------------------------------------------------------------
# Priority filter (Story MCE-11.14 — AC3)
# ---------------------------------------------------------------------------

# Minimum priority level for routing insights to agent MEMORY / dossiers.
# Insights below this threshold are logged as skipped.
# Override via env var: MCE_CASCADE_MIN_PRIORITY=HIGH|MEDIUM|LOW
CASCADE_MIN_PRIORITY: str = os.getenv("MCE_CASCADE_MIN_PRIORITY", "MEDIUM")
PRIORITY_RANK: dict[str, int] = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

logger = logging.getLogger("mce.cascading")

_CASCADING_LOG: Path = LOGS / "cascading.jsonl"
_DOSSIERS_DIR: Path = KNOWLEDGE_EXTERNAL / "dossiers" / "themes"
_SOLOS_DIR: Path = EXTERNAL_DOSSIERS_PERSONS_BY_THEME

# Solo dossier thresholds (Story MCE-13.2)
# CREATE: minimum insights required to create a new solo (person×theme intersection).
# UPDATE: minimum new insights required to append to an existing solo.
_SOLO_CREATE_THRESHOLD: int = 10
_SOLO_UPDATE_THRESHOLD: int = 5

# Lazy singleton: initialised on first call to _update_theme_dossiers.
# Keeps startup cost zero for callers that don't use the cascade path.
_theme_router: ThemeRouter | None = None


def _get_theme_router() -> ThemeRouter:
    """Return (or lazily create) the module-level ThemeRouter instance."""
    global _theme_router
    if _theme_router is None:
        _theme_router = ThemeRouter(dossiers_dir=_DOSSIERS_DIR)
    return _theme_router


# ---------------------------------------------------------------------------
# JSONL logging
# ---------------------------------------------------------------------------


def _log_action(entry: dict[str, Any]) -> None:
    """Append a JSON line to the cascading audit log (non-fatal)."""
    try:
        _CASCADING_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["timestamp"] = datetime.now(UTC).isoformat()
        with open(_CASCADING_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write cascading log", exc_info=True)


# ---------------------------------------------------------------------------
# Agent discovery
# ---------------------------------------------------------------------------


def _find_cargo_agents_for_person(person_slug: str) -> list[Path]:
    """Find all cargo agents that consume DNA from a given person.

    Scans agents/cargo/**/DNA-CONFIG.yaml for entries in
    dna_sources.primario[].pessoa matching the slug.

    Args:
        person_slug: Kebab-case person identifier.

    Returns:
        List of cargo agent directory Paths.
    """
    targets: list[Path] = []
    slug_lower = person_slug.lower().strip()

    if not AGENTS_CARGO.is_dir():
        return targets

    for config_path in AGENTS_CARGO.rglob("DNA-CONFIG.yaml"):
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        dna_sources = data.get("dna_sources", {})
        if not isinstance(dna_sources, dict):
            continue

        primario = dna_sources.get("primario", [])
        if not isinstance(primario, list):
            continue

        for entry in primario:
            if not isinstance(entry, dict):
                continue
            pessoa = entry.get("pessoa", "").lower().strip()
            if pessoa == slug_lower:
                targets.append(config_path.parent)
                break

    return targets


def _find_cargo_agents_by_slugs(slugs: list[str]) -> list[Path]:
    """Resolve cargo agent directory Paths from a list of slug names.

    Used by the THEME_TO_AGENTS second lookup (Story MCE-11.6 AC2) to convert
    deterministic slug names from theme-to-agents.yaml into filesystem Paths
    that _update_cargo_memory() can write to.

    Scans AGENTS_CARGO recursively for directories whose name matches a slug.
    Returns one Path per slug (first match wins).  Missing slugs are logged as
    warnings but do not cause errors (AC5 — fallback safe).

    Args:
        slugs: List of lowercase cargo agent slugs from THEME_TO_AGENTS.

    Returns:
        List of Path objects (agent directories).  May be shorter than slugs
        if some slugs have no matching directory.
    """
    if not slugs or not AGENTS_CARGO.is_dir():
        return []

    # Build a slug → Path index once (avoids O(n*m) rglob per slug).
    slug_index: dict[str, Path] = {}
    for dna_path in AGENTS_CARGO.rglob("DNA-CONFIG.yaml"):
        agent_dir = dna_path.parent
        slug_index[agent_dir.name.lower()] = agent_dir

    result: list[Path] = []
    for slug in slugs:
        slug_lower = slug.lower().strip()
        if slug_lower in slug_index:
            result.append(slug_index[slug_lower])
        else:
            logger.warning(
                "theme_to_agents: slug '%s' not found in %s — skipping",
                slug_lower,
                AGENTS_CARGO,
            )

    return result


# ---------------------------------------------------------------------------
# Cargo agent MEMORY.md update
# ---------------------------------------------------------------------------


def _update_cargo_memory(
    agent_dir: Path,
    insights: list[dict[str, Any]],
    person_slug: str,
) -> dict[str, Any]:
    """Append insights to a cargo agent's MEMORY.md.

    Args:
        agent_dir: Path to the cargo agent directory.
        insights: List of insight dicts to append.
        person_slug: Source person slug for attribution.

    Returns:
        Dict with update results.
    """
    memory_path = agent_dir / "MEMORY.md"
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    appended = 0

    # Create stub if MEMORY.md doesn't exist
    if not memory_path.exists():
        agent_name = " ".join(w.capitalize() for w in agent_dir.name.split("-"))
        memory_path.write_text(
            f"# MEMORY: {agent_name}\n\n"
            f"> **Atualizado:** {now}\n\n---\n\n"
            "## INSIGHTS EXTRAIDOS\n\n"
            "*Insights serao adicionados aqui automaticamente.*\n\n---\n\n"
            "## HISTORICO DE ATUALIZACOES\n\n"
            "| Data | Mudanca | Material Processado |\n"
            "|------|---------|---------------------|\n"
            f"| {now} | Criacao inicial (auto-gerado) | cascading.py v1.0 |\n",
            encoding="utf-8",
        )

    try:
        text = memory_path.read_text(encoding="utf-8")
    except Exception as exc:
        return {"error": str(exc), "appended": 0}

    for insight in insights:
        # Dedup: check if insight ID or chunk_id already present
        insight_id = insight.get("id", "") or insight.get("chunk_id", "")
        if insight_id and insight_id in text:
            continue

        title = insight.get("title", "") or insight.get("insight", "Insight")
        content = (
            insight.get("content") or insight.get("insight") or insight.get("summary") or title
        )
        tag = insight.get("tag", "")
        priority = insight.get("priority", "MEDIUM")

        entry = (
            f"\n### {now} - {title}\n\n"
            f"**Source:** {person_slug} | **Tag:** {tag} | **Priority:** {priority}\n\n"
        )
        if insight_id:
            entry += f"**ID:** {insight_id}\n\n"
        entry += f"{content}\n"

        # Insert before the HISTORICO section or at EOF
        hist_marker = "## HISTORICO DE ATUALIZACOES"
        hist_alt = "## HIST\u00d3RICO DE ATUALIZA\u00c7\u00d5ES"
        hist_pos = text.find(hist_marker)
        if hist_pos == -1:
            hist_pos = text.find(hist_alt)

        if hist_pos != -1:
            # Find the --- separator before HISTORICO
            sep_pos = text.rfind("---", 0, hist_pos)
            if sep_pos != -1:
                text = text[:sep_pos].rstrip() + "\n" + entry + "\n---\n\n" + text[hist_pos:]
            else:
                text = text[:hist_pos].rstrip() + "\n" + entry + "\n" + text[hist_pos:]
        else:
            text = text.rstrip() + "\n" + entry + "\n"

        appended += 1

    # Update the date header
    text = re.sub(
        r"(\*\*Atualizado:\*\*)\s*\d{4}-\d{2}-\d{2}",
        f"\\1 {now}",
        text,
        count=1,
    )

    try:
        memory_path.write_text(text, encoding="utf-8")
    except Exception as exc:
        return {"error": str(exc), "appended": appended}

    return {"appended": appended, "path": str(memory_path)}


# ---------------------------------------------------------------------------
# Attribution helpers (Story MCE-11.7)
# ---------------------------------------------------------------------------

# Matches section headers like: ## ALEX-HORMOZI — Atualizacao 2026-03-16
_PERSON_SECTION_RE = re.compile(
    r"^## ([A-Z][A-Z0-9\-]+?) — Atualizacao",
    re.MULTILINE,
)

# Matches insight bullet lines like: - **[HIGH]** Some insight text
_INSIGHT_BULLET_RE = re.compile(r"^\s*-\s+\*\*\[(?:HIGH|MEDIUM|LOW)\]\*\*", re.MULTILINE)


def _parse_dossier_contributors(dossier_text: str) -> list[dict]:
    """Parse contributor attribution from an existing theme dossier.

    Builds person slug → insight count by scanning each person section
    and counting ``- **[PRIORITY]**`` bullet lines within it.

    Args:
        dossier_text: Full text of the theme dossier.

    Returns:
        Output of :func:`calculate_attribution` — sorted list of
        ``{"expert": str, "count": int, "percentage": int}`` dicts.
        Returns ``[]`` when no person sections or no insight bullets found.
    """
    # Split into (person_slug_upper, section_body) pairs.
    sections: list[tuple[str, str]] = []
    matches = list(_PERSON_SECTION_RE.finditer(dossier_text))
    for i, m in enumerate(matches):
        slug_upper = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(dossier_text)
        sections.append((slug_upper, dossier_text[start:end]))

    if not sections:
        return []

    # Build synthetic insight list: one dict per bullet line, keyed by slug.
    synthetic_insights: list[dict] = []
    for slug_upper, body in sections:
        bullets = _INSIGHT_BULLET_RE.findall(body)
        for _ in bullets:
            synthetic_insights.append({"source_person": slug_upper})

    return calculate_attribution(synthetic_insights)


def _rebuild_contributors_section(dossier_path: Path, dossier_text: str) -> str:
    """Recalculate attribution from *dossier_text* and inject/replace section.

    Always recalculates from scratch (AC3 — not append-only).

    Args:
        dossier_path: Path to the dossier file (used only for logging).
        dossier_text: Current full text of the dossier.

    Returns:
        Updated dossier text with Contributors section in place.
        Returns original text unchanged if attribution yields 0 insights.
    """
    attribution = _parse_dossier_contributors(dossier_text)
    total = sum(e["count"] for e in attribution)
    if total == 0:
        logger.debug(
            "attribution: no insight bullets found in %s — section omitted",
            dossier_path.name,
        )
        return dossier_text

    updated_date = datetime.now(UTC).strftime("%Y-%m-%d")
    new_section = render_contributors_section(attribution, total, updated_date)
    return replace_contributors_section(dossier_text, new_section)


# ---------------------------------------------------------------------------
# Solo dossier helpers (Story MCE-13.2)
# ---------------------------------------------------------------------------


def _majority_layer(insights: list[dict]) -> str:
    """Return the DNA layer that appears most often in a list of insights.

    Used to populate the ``layer_dominante`` frontmatter field of a solo
    dossier.  Tags are stripped of ``[]`` brackets before counting.
    """
    from collections import Counter

    counts: Counter[str] = Counter()
    tag_to_layer: dict[str, str] = {
        "FILOSOFIA": "L1_FILOSOFIAS",
        "MODELO_MENTAL": "L2_MODELOS_MENTAIS",
        "HEURISTICA": "L3_HEURISTICAS",
        "FRAMEWORK": "L4_FRAMEWORKS",
        "METODOLOGIA": "L5_METODOLOGIAS",
        "PADRAO_COMPORTAMENTAL": "L6_PADROES_COMPORTAMENTAIS",
        "VALOR": "L7_VALORES",
        "VOZ": "L8_VOZ_DNA",
        "OBSSESSAO": "L9_OBSESSOES",
        "PARADOXO": "L10_PARADOXOS",
    }
    for ins in insights:
        raw = (ins.get("tag") or "").strip("[]").upper()
        layer = tag_to_layer.get(raw, "L3_HEURISTICAS")
        counts[layer] += 1
    if not counts:
        return "L3_HEURISTICAS"
    return counts.most_common(1)[0][0]


def _create_solo_dossier(
    solo_path: Path,
    person_slug: str,
    category: str,
    category_insights: list[dict],
    bucket: str = "external",
) -> None:
    """Create a new solo dossier (person×theme intersection) in hybrid format.

    Format: YAML frontmatter + Markdown body.  Pattern: ``{slug}--{category}.md``.

    Args:
        solo_path: Absolute path for the new file.
        person_slug: Slug identifying the person (e.g. "alex-hormozi").
        category: Canonical category string (e.g. "pricing").
        category_insights: All insights for this person×category pair.
        bucket: Knowledge bucket — templates the cross-ref paths so a
            business/personal solo never points back into external
            (STORY-MCE-BUCKET-AWARE-WRITES — Art. XIII).
    """
    now_iso = datetime.now(UTC).isoformat(timespec="seconds")
    layer_dom = _majority_layer(category_insights)
    count = len(category_insights)

    # Frontmatter
    person_display = person_slug.replace("-", " ").title()
    category_display = category.replace("-", " ").title()
    frontmatter = (
        "---\n"
        f"slug: {person_slug}--{category}\n"
        f"pessoa_id: {person_slug}\n"
        f"tema_id: {category}\n"
        f"layer_dominante: {layer_dom}\n"
        f"insights_count: {count}\n"
        f"boot_priority: HIGH\n"
        f"generated_at: {now_iso}\n"
        f"version: 1.0.0\n"
        "---\n\n"
    )

    # Header + argumento central (first non-empty insight as seed)
    seed_text = ""
    for ins in category_insights[:3]:
        candidate = ins.get("insight", "") or ins.get("title", "")
        if candidate:
            seed_text = candidate
            break

    body = (
        f"# {person_display} sobre {category_display}\n\n"
        "## Argumento Central\n\n"
        f"{seed_text}\n\n"
        "## Insights Chave\n\n"
    )

    # Insights section (up to 20)
    for ins in category_insights[:20]:
        ins_id = ins.get("id", "?")
        title = ins.get("title", "") or ins.get("insight", "")[:80]
        quote = ins.get("quote", "")
        source_raw = ins.get("source", {})
        source_str = (
            source_raw.get("title", source_raw.get("source_id", "?"))
            if isinstance(source_raw, dict)
            else str(source_raw)
        )
        confidence = ins.get("confidence", "MEDIUM")
        tag = (ins.get("tag") or "?").strip("[]")
        body += f"### {ins_id}: {title}\n"
        if quote:
            body += f'> "{quote}"\n'
        body += (
            f"- **Fonte:** {source_str}\n"
            f"- **Confiança:** {confidence}\n"
            f"- **Tag:** {tag}\n"
            f"- **Category:** {category}\n\n"
        )

    # Cross-refs (bucket-templated — Art. XIII isolation)
    body += (
        "## Cross-refs\n\n"
        f"- Tema: knowledge/{bucket}/dossiers/themes/\n"
        f"- Dossier pessoa: knowledge/{bucket}/dossiers/persons/dossier-{person_slug}.md\n"
        f"- DNA layers: knowledge/{bucket}/dna/persons/{person_slug}/\n"
    )

    solo_path.write_text(frontmatter + body, encoding="utf-8")
    logger.info(
        "solo: CREATED %s — %d insights",
        solo_path.name,
        count,
    )


def _append_to_solo_dossier(
    solo_path: Path,
    person_slug: str,
    category: str,
    new_insights: list[dict],
) -> None:
    """Append a new update section to an existing solo dossier.

    Args:
        solo_path: Path to the existing solo file.
        person_slug: Slug for the person.
        category: Category string for the solo.
        new_insights: Insights to append (already filtered >= _SOLO_UPDATE_THRESHOLD).
    """
    now_precise = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    marker = f"Atualização {now_precise}"

    text = solo_path.read_text(encoding="utf-8")
    if marker in text:
        # True duplicate within same pipeline run — skip.
        return

    section = (
        f"\n\n---\n\n"
        f"## Atualização {now_precise}\n\n"
        f"### Insights novos ({len(new_insights)} adicionados)\n\n"
    )
    for ins in new_insights[:20]:
        ins_id = ins.get("id", "?")
        title = ins.get("title", "") or ins.get("insight", "")[:80]
        tag = (ins.get("tag") or "?").strip("[]")
        confidence = ins.get("confidence", "MEDIUM")
        section += f"- **{ins_id}** [{tag}] [{confidence}] {title}\n"

    solo_path.write_text(text + section, encoding="utf-8")
    logger.info(
        "solo: UPDATED %s — %d new insights",
        solo_path.name,
        len(new_insights),
    )


# ---------------------------------------------------------------------------
# Theme dossier update
# ---------------------------------------------------------------------------


def _update_theme_dossiers(
    insights: list[dict[str, Any]],
    person_slug: str,
    bucket: str = "external",
) -> dict[str, Any]:
    """Update theme dossiers with new insights grouped by category.

    Args:
        insights: List of insight dicts.
        person_slug: Source person for attribution.
        bucket: Knowledge bucket — routes theme dossiers AND solos under
            ``knowledge/{bucket}/dossiers/...`` instead of the hardcoded
            external module constants (STORY-MCE-BUCKET-AWARE-WRITES — D4, Art. XIII).

    Returns:
        Dict with update results.
    """
    from engine.intelligence.pipeline.mce.person_paths import PersonArtifactPaths

    paths = PersonArtifactPaths(person_slug, bucket, root=ROOT)
    dossiers_dir = paths.dossier_theme_dir
    solos_dir = paths.solos_dir

    dossiers_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    # Include HH:MM:SS in the section header so multiple same-day pipeline
    # runs produce unique markers and the dedup check does not falsely skip
    # the second run.  The date-only value (``now``) is kept for display
    # in dossier metadata fields where day-level granularity is sufficient.
    now_precise = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    # Per-bucket router so dossier paths resolve under knowledge/{bucket}/dossiers/themes
    # (the cached module-level router is external-only and unsafe for business/personal).
    router = ThemeRouter(dossiers_dir=dossiers_dir)

    def _resolve_into_bucket(insight: dict[str, Any]) -> Path:
        """Resolve an insight's theme dossier, forcing it into the bucket dir.

        ThemeRouter resolves configured routes to ABSOLUTE paths declared in
        theme-routing.yaml (hardcoded under external). Theme dossiers are flat
        ``dossier-{theme}.md`` files, so re-rooting by filename guarantees bucket
        isolation regardless of the config (no-op for the external bucket).
        """
        return dossiers_dir / router.resolve(insight).name

    # Group insights by resolved dossier path (semantic routing via ThemeRouter).
    # Dual-routing (Story MCE-12.3): each insight can route to TWO dossiers:
    #   Primary:   resolved by tag (layer-based, e.g. [HEURISTICA] -> heuristicas)
    #              This path uses the full insight dict (tag takes priority in resolve()).
    #   Secondary: resolved by category field (domain-based, e.g. "vendas" -> sales-process)
    #              Only fires when category is populated and != "none".
    # If both paths resolve to the same dossier, only one update is made (dedup via set).
    by_path: dict[Path, list[dict]] = {}
    # Track paths that were added ONLY via the secondary (domain) route.
    secondary_only_paths: set[Path] = set()

    for ins in insights:
        # Primary route: tag-based (layer dossier).
        # Resolve using ONLY tag so layer dossiers always receive the insight
        # regardless of whether category is also present.  (ThemeRouter.resolve
        # prioritises category over tag when both are set, which would cause
        # layer dossiers to be skipped for categorised insights.)
        tag_raw = (ins.get("tag") or "").strip("[]")
        primary_path = _resolve_into_bucket(
            {"tag": ins.get("tag", ""), "dna_layer": ins.get("dna_layer", "")}
        )
        if primary_path not in by_path:
            by_path[primary_path] = []
        by_path[primary_path].append(ins)

        # Secondary route: category-based (domain dossier) — MCE-12.3
        cat = (ins.get("category") or "").strip().lower()
        if cat and cat != "none":
            secondary_path = _resolve_into_bucket({"category": cat})
            if secondary_path != primary_path:
                if secondary_path not in by_path:
                    by_path[secondary_path] = []
                    secondary_only_paths.add(secondary_path)
                by_path[secondary_path].append(ins)

    themes_updated = 0
    themes_created = 0
    themes_updated_secondary = 0

    for dossier_path, theme_insights in by_path.items():
        # Use the filename stem (minus "dossier-" prefix) as human-readable key
        # for logging and section headers.
        theme_key = dossier_path.stem.removeprefix("dossier-").upper()

        # Update threshold: 2+ insights required. Lower than the create
        # threshold (3) because an existing dossier already has foundational
        # content -- even 2 new insights add meaningful enrichment.
        if len(theme_insights) < 2:
            continue

        if dossier_path.exists():
            try:
                text = dossier_path.read_text(encoding="utf-8")
                # Append a new section for this person's insights.
                # Uses ``now_precise`` (date + time) so multiple same-day
                # runs produce distinct sections and the dedup marker below
                # does not falsely suppress the second run.
                section = (
                    f"\n\n---\n\n"
                    f"## {person_slug.upper()} — Atualizacao {now_precise}\n\n"
                    f"**Fonte:** MCE Pipeline cascading\n"
                    f"**Insights:** {len(theme_insights)}\n\n"
                )
                for ins in theme_insights[:10]:  # cap at 10 per update
                    title = ins.get("title", "") or ins.get("insight", "")
                    priority = ins.get("priority", "MEDIUM")
                    section += f"- **[{priority}]** {title}\n"

                # Dedup: skip only if a section with this exact person +
                # timestamp already exists (second-level precision avoids
                # same-day collisions while still preventing true duplicates
                # within the same pipeline run).
                marker = f"{person_slug.upper()} — Atualizacao {now_precise}"
                if marker not in text:
                    text += section
                    # Story MCE-11.7: recalculate attribution from full dossier text
                    text = _rebuild_contributors_section(dossier_path, text)
                    dossier_path.write_text(text, encoding="utf-8")
                    themes_updated += 1
                    # MCE-12.3: track secondary-only (domain) updates separately
                    if dossier_path in secondary_only_paths:
                        themes_updated_secondary += 1
            except Exception as exc:
                logger.warning("Failed to update dossier %s: %s", dossier_path.name, exc)
        else:
            # Create threshold: 3+ insights required. Higher bar than
            # updates (2) because a brand-new dossier must carry enough
            # substance to justify its existence as a standalone file.
            if len(theme_insights) < 3:
                continue
            try:
                # Use ThemeRouter.ensure_dossier_exists for auto-discovered paths
                # so the header format is consistent across all new dossiers.
                created = router.ensure_dossier_exists(dossier_path, theme_key, now)
                if not created:
                    # Race condition: file appeared between our exists() check
                    # and now.  Fall through to the update path on next cycle.
                    continue

                # Append first-person section on top of the minimal template.
                text = dossier_path.read_text(encoding="utf-8")
                section = (
                    f"## {person_slug.upper()} — Atualizacao {now_precise}\n\n"
                    f"**Insights:** {len(theme_insights)}\n\n"
                )
                for ins in theme_insights[:10]:
                    title = ins.get("title", "") or ins.get("insight", "")
                    priority = ins.get("priority", "MEDIUM")
                    section += f"- **[{priority}]** {title}\n"

                # Story MCE-11.7: inject attribution into new dossier
                new_text = _rebuild_contributors_section(dossier_path, text + section)
                dossier_path.write_text(new_text, encoding="utf-8")
                themes_created += 1
            except Exception as exc:
                logger.warning("Failed to create dossier %s: %s", dossier_path.name, exc)

    # --- Third output: solo dossiers (person×theme intersections) MCE-13.2 ---
    # Groups insights by canonical category (not by dossier path) and creates
    # or updates person×theme solo files in persons-by-theme/.
    # Pattern: {person_slug}--{category}.md  (double hyphen delimiter).
    # Thresholds: CREATE >= 10, UPDATE >= 5.  Avoids noisy stubs.
    solos_created = 0
    solos_updated = 0

    solos_dir.mkdir(parents=True, exist_ok=True)

    # Group insights by (category).  person_slug is fixed for this call.
    by_category: dict[str, list[dict]] = {}
    for ins in insights:
        cat = (ins.get("category") or "").strip().lower()
        if cat and cat != "none":
            by_category.setdefault(cat, []).append(ins)

    for category, category_insights in by_category.items():
        solo_key = f"{person_slug}--{category}"
        solo_path = solos_dir / f"{solo_key}.md"

        try:
            if not solo_path.exists():
                if len(category_insights) >= _SOLO_CREATE_THRESHOLD:
                    _create_solo_dossier(
                        solo_path, person_slug, category, category_insights, bucket
                    )
                    solos_created += 1
            else:
                if len(category_insights) >= _SOLO_UPDATE_THRESHOLD:
                    _append_to_solo_dossier(solo_path, person_slug, category, category_insights)
                    solos_updated += 1
        except Exception as exc:
            logger.warning("Failed to process solo dossier %s: %s", solo_key, exc)

    return {
        "themes_updated": themes_updated,
        "themes_created": themes_created,
        "themes_scanned": len(by_path),
        "themes_updated_secondary": themes_updated_secondary,
        "solos_created": solos_created,
        "solos_updated": solos_updated,
    }


# ---------------------------------------------------------------------------
# By-person insights file update
# ---------------------------------------------------------------------------


def _update_by_person_insights(
    slug: str, new_insights: list[dict], bucket: str = "business"
) -> dict:
    """Update the by-person insights file with new insights from pipeline."""
    from engine.intelligence.pipeline.mce.person_paths import PersonArtifactPaths

    bp_path = PersonArtifactPaths(slug, bucket, root=ROOT).insights_by_person

    result: dict[str, Any] = {"updated": False, "path": str(bp_path), "insights_added": 0}

    if not bp_path.exists():
        logger.info("No by-person file at %s, skipping", bp_path)
        return result

    try:
        content = bp_path.read_text(encoding="utf-8")

        # Find the last section before Padrões de Pensamento
        lines = content.split("\n")
        insert_idx = len(lines)
        for i, line in enumerate(lines):
            if "Padrões de Pensamento" in line or "Padroes de Pensamento" in line:
                insert_idx = i
                break

        # Build new insights section
        # Get source IDs from new insights to avoid duplicates
        existing_sources: set[str] = set()
        for line in lines:
            m = re.search(r"MEET-\d+", line)
            if m:
                existing_sources.add(m.group())

        new_section_lines: list[str] = []
        added = 0
        # Group by source
        by_source: dict[str, list[dict]] = {}
        for ins in new_insights:
            src = ins.get("source", {})
            sid = src.get("source_id", "") if isinstance(src, dict) else ""
            if sid and sid not in existing_sources:
                by_source.setdefault(sid, []).append(ins)

        for sid, insights in by_source.items():
            new_section_lines.append(f"\n## Insights de {sid}\n")
            new_section_lines.append("| # | Insight | Tema | Confiança |")
            new_section_lines.append("|---|---------|------|-----------|")
            for idx, ins in enumerate(insights, 1):
                tag = ins.get("tag", "").strip("[]")
                conf = ins.get("confidence", "MEDIUM")
                text = ins.get("insight", "")[:80]
                new_section_lines.append(f"| {idx} | {text} | {tag} | {conf} |")
            added += len(insights)

        if new_section_lines:
            # Insert before Padrões de Pensamento
            lines = lines[:insert_idx] + new_section_lines + [""] + lines[insert_idx:]

            # Update header with new sources
            for idx, line in enumerate(lines):
                if "Meetings processados:" in line:
                    new_sources = ", ".join(sorted(existing_sources | set(by_source.keys())))
                    lines[idx] = f"> **Meetings processados:** {new_sources}"
                    break

            bp_path.write_text("\n".join(lines), encoding="utf-8")
            result["updated"] = True
            result["insights_added"] = added
            logger.info("Updated by-person file: %s (+%d insights)", bp_path, added)

    except Exception as e:
        logger.warning("Failed to update by-person file: %s", e)
        result["error"] = str(e)

    return result


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def _dedup_key_agg(name: str) -> str:
    """Normalise a name string into a dedup key for AGG-DOMAIN entries."""
    return name.lower().strip()[:50]


def _build_agg_entry(
    ins: dict, slug: str, existing_ids: set[str], id_prefix: str, seq: int
) -> tuple[dict, int]:
    """Build a structured AGG-DOMAIN entry from an insight dict.

    Returns:
        Tuple of (entry_dict, next_seq).
    """
    insight_id = ins.get("id", "")
    name = ins.get("insight", "") or ins.get("name", "") or ins.get("title", insight_id)
    description = ins.get("insight", "") or ins.get("description", "") or name
    chunks = list(ins.get("chunks", []) or [])
    confidence = ins.get("confidence", 0.8)
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except ValueError:
            confidence = 0.8

    # Derive layer from tag
    tag = (ins.get("tag") or "").strip().upper().strip("[]")
    layer_map = {
        "FILOSOFIA": "L1_FILOSOFIAS",
        "MODELO-MENTAL": "L2_MODELOS_MENTAIS",
        "HEURISTICA": "L3_HEURISTICAS",
        "FRAMEWORK": "L4_FRAMEWORKS",
        "METODOLOGIA": "L5_METODOLOGIAS",
    }
    layer = layer_map.get(tag, "L0_UNKNOWN")

    new_id = f"{id_prefix}_{seq:03d}"
    while new_id in existing_ids:
        seq += 1
        new_id = f"{id_prefix}_{seq:03d}"

    entry = {
        "id": new_id,
        "name": name[:200],
        "description": description[:500],
        "source_insight_ids": [insight_id] if insight_id else [],
        "chunk_refs": chunks,
        "confidence": round(float(confidence), 2),
        "layer": layer,
        "origin": slug,
        "last_updated": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return entry, seq + 1


def _update_single_agg_yaml(
    agg_path: Path,
    slug: str,
    insights: list[dict],
    domain: str,
) -> dict[str, Any]:
    """Merge new insights into a single AGG-*.yaml file (append-only, idempotent).

    Only updates fields: entries[] — structured list with source_insight_ids.
    Never overwrites other fields (experts, version, etc.).

    Args:
        agg_path: Path to the AGG-DOMAIN.yaml file.
        slug: Person slug for attribution.
        insights: Filtered insights to merge.
        domain: Domain name for logging.

    Returns:
        Dict with keys: added, updated, total.
    """
    import yaml as _yaml

    if not agg_path.exists():
        logger.debug("_update_single_agg_yaml: %s does not exist, skipping", agg_path)
        return {"added": 0, "updated": 0, "total": 0, "skipped": "file not found"}

    try:
        data = _yaml.safe_load(agg_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        logger.warning("_update_single_agg_yaml: failed to parse %s: %s", agg_path, exc)
        return {"added": 0, "updated": 0, "total": 0, "error": str(exc)}

    if not isinstance(data, dict):
        data = {}

    entries: list[dict] = data.get("entries", []) or []

    # Build dedup index: key -> list index
    key_to_idx: dict[str, int] = {}
    existing_ids: set[str] = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        key_to_idx[_dedup_key_agg(entry.get("name", ""))] = idx
        existing_ids.add(entry.get("id", ""))

    # Determine ID prefix: first 3 chars of domain
    id_prefix = (domain[:3] + "agg").lower()
    seq = len(entries) + 1

    added = 0
    updated = 0

    for ins in insights:
        name = ins.get("insight", "") or ins.get("name", "") or ins.get("title", "")
        dk = _dedup_key_agg(name)
        insight_id = ins.get("id", "")
        chunks = list(ins.get("chunks", []) or [])

        if dk in key_to_idx:
            # Extend existing entry's source_insight_ids + chunk_refs (union)
            idx = key_to_idx[dk]
            entry = entries[idx]
            src_ids: list = entry.get("source_insight_ids", []) or []
            existing_chunks: list = entry.get("chunk_refs", []) or []

            changed = False
            if insight_id and insight_id not in src_ids:
                src_ids.append(insight_id)
                changed = True
            for ch in chunks:
                if ch not in existing_chunks:
                    existing_chunks.append(ch)
                    changed = True

            if changed:
                entry["source_insight_ids"] = src_ids
                entry["chunk_refs"] = existing_chunks
                entry["last_updated"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                entries[idx] = entry
                updated += 1
        else:
            # New entry
            new_entry, seq = _build_agg_entry(ins, slug, existing_ids, id_prefix, seq)
            entries.append(new_entry)
            key_to_idx[dk] = len(entries) - 1
            existing_ids.add(new_entry["id"])
            added += 1

    if added == 0 and updated == 0:
        return {"added": 0, "updated": 0, "total": len(entries), "skipped": "no new data"}

    # Write back: update only entries + metadata fields, preserve everything else
    data["entries"] = entries
    data["total_entries"] = len(entries)
    data["updated"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Update or add expert entry for this slug
    experts: list[dict] = data.get("experts", []) or []
    slug_expert = next(
        (e for e in experts if isinstance(e, dict) and e.get("person") == slug), None
    )
    if slug_expert is None:
        # Count how many entries belong to this slug
        slug_count = sum(1 for e in entries if isinstance(e, dict) and e.get("origin") == slug)
        experts.append(
            {
                "person": slug,
                "entry_count": slug_count,
                "source_dir": f"external/dna/persons/{slug}",
            }
        )
        data["experts"] = experts
        data["total_experts"] = len(experts)
    else:
        # Update entry_count
        slug_expert["entry_count"] = sum(
            1 for e in entries if isinstance(e, dict) and e.get("origin") == slug
        )

    try:
        agg_path.write_text(
            _yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("_update_single_agg_yaml: write failed for %s: %s", agg_path, exc)
        return {"added": added, "updated": updated, "total": len(entries), "error": str(exc)}

    return {"added": added, "updated": updated, "total": len(entries)}


def _update_aggregated_domain_yamls(
    slug: str,
    insights: list[dict],
    cargo_dirs: list[Path],
) -> dict[str, Any]:
    """Update AGG-*.yaml domain files with new structured insight entries.

    For each cargo agent in cargo_dirs, reads its DNA-CONFIG.yaml to find
    dna_sources.agregado[].path entries pointing to AGG-*.yaml files.
    Merges insights into each referenced AGG-*.yaml file.

    APPEND-ONLY: never deletes existing entries. Idempotent.
    Non-blocking: individual file failures are logged but do not abort.

    Args:
        slug: Person slug being cascaded.
        insights: Priority-filtered insights list.
        cargo_dirs: List of cargo agent directory Paths to scan.

    Returns:
        Dict with keys: domains_updated, entries_added, entries_updated, errors[].
    """
    result: dict[str, Any] = {
        "domains_updated": 0,
        "entries_added": 0,
        "entries_updated": 0,
        "errors": [],
    }

    if not insights or not cargo_dirs:
        return result

    # Collect unique AGG-*.yaml paths from all cargo DNA-CONFIGs
    # Map: agg_path -> domain name (for ID prefix)
    agg_targets: dict[Path, str] = {}

    for agent_dir in cargo_dirs:
        config_path = agent_dir / "DNA-CONFIG.yaml"
        if not config_path.exists():
            continue
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        dna_sources = data.get("dna_sources", {})
        if not isinstance(dna_sources, dict):
            dna_sources = {}

        agregado = dna_sources.get("agregado", []) or []
        # Fallback: some DNA-CONFIGs use top-level dna_agregado key instead of
        # dna_sources.agregado — accept both schemas transparently.
        if not agregado:
            agregado = data.get("dna_agregado", []) or []
        if not isinstance(agregado, list):
            continue

        for agg_entry in agregado:
            if not isinstance(agg_entry, dict):
                continue
            rel_path = agg_entry.get("path", "")
            domain = agg_entry.get("dominio", "")
            if not rel_path:
                continue

            # Resolve relative to project ROOT
            agg_path = ROOT / rel_path
            if agg_path not in agg_targets:
                agg_targets[agg_path] = domain or agg_path.stem.replace("AGG-", "").lower()

    if not agg_targets:
        logger.debug(
            "_update_aggregated_domain_yamls: no AGG targets found for %d cargo dirs",
            len(cargo_dirs),
        )
        return result

    # Filter: only insights with L1-L5 tags (those that belong in AGG domain YAMLs)
    l1_l5_tags = {"[FILOSOFIA]", "[MODELO-MENTAL]", "[HEURISTICA]", "[FRAMEWORK]", "[METODOLOGIA]"}
    domain_insights = [
        ins
        for ins in insights
        if (ins.get("tag") or "").strip().upper() in {t.upper() for t in l1_l5_tags}
    ]

    if not domain_insights:
        logger.debug(
            "_update_aggregated_domain_yamls: no L1-L5 insights for slug=%s, skipping AGG update",
            slug,
        )
        return result

    for agg_path, domain in agg_targets.items():
        try:
            update_result = _update_single_agg_yaml(agg_path, slug, domain_insights, domain)
            if update_result.get("added", 0) > 0 or update_result.get("updated", 0) > 0:
                result["domains_updated"] += 1
                result["entries_added"] += update_result.get("added", 0)
                result["entries_updated"] += update_result.get("updated", 0)
                _log_action(
                    {
                        "action": "agg_domain_updated",
                        "slug": slug,
                        "domain": domain,
                        "agg_path": str(
                            agg_path.relative_to(ROOT)
                            if agg_path.is_relative_to(ROOT)
                            else agg_path
                        ),
                        "added": update_result.get("added", 0),
                        "updated": update_result.get("updated", 0),
                        "total": update_result.get("total", 0),
                    }
                )
                logger.info(
                    "_update_aggregated_domain_yamls: domain=%s slug=%s added=%d updated=%d",
                    domain,
                    slug,
                    update_result.get("added", 0),
                    update_result.get("updated", 0),
                )
        except Exception as exc:
            err_msg = f"domain={domain} path={agg_path}: {exc}"
            logger.warning("_update_aggregated_domain_yamls: error for %s: %s", slug, err_msg)
            result["errors"].append(err_msg)

    return result


def _load_per_slug_insights(slug: str) -> tuple[list[dict], str | None]:
    """Load insights from the per-slug rich INSIGHTS-STATE.json.

    Per Story MCE-11.14: always reads from the per-slug file which carries
    the full schema (priority, confidence, chunks[], status, provenance).
    Never falls back to the global degraded aggregation file.

    Args:
        slug: Person slug (e.g. "alex-hormozi").

    Returns:
        Tuple of (insights_list, error_or_none).
        On missing file: returns ([], None) — caller logs warning and skips.
        On parse error: returns ([], error_message).
    """
    per_slug_path: Path = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"

    if not per_slug_path.exists():
        return [], None  # caller will warn + skip (AC4)

    try:
        data = json.loads(per_slug_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [], f"Failed to parse per-slug INSIGHTS-STATE: {exc}"

    collected: list[dict] = []

    # Primary shape: {"persons": {"<Name>": {"insights": [...], ...}}}
    persons = data.get("persons", {})
    if isinstance(persons, dict):
        for person_name, pdata in persons.items():
            if not isinstance(pdata, dict):
                continue
            collected.extend(ins for ins in pdata.get("insights", []) if isinstance(ins, dict))

    # Secondary shape: flat "insights" list
    flat = data.get("insights", [])
    if isinstance(flat, list):
        for ins in flat:
            if isinstance(ins, dict):
                collected.append(ins)

    return collected, None


def _filter_by_priority(
    insights: list[dict],
    min_priority: str = CASCADE_MIN_PRIORITY,
) -> tuple[list[dict], int]:
    """Filter insights by minimum priority rank.

    Args:
        insights: List of insight dicts; priority field may be absent.
        min_priority: Minimum inclusive priority string (HIGH/MEDIUM/LOW).

    Returns:
        Tuple of (accepted_insights, skipped_count).
        Insights with missing priority default to MEDIUM (graceful degradation
        per story risk table).
    """
    threshold = PRIORITY_RANK.get(min_priority.upper(), PRIORITY_RANK["MEDIUM"])
    accepted: list[dict] = []
    skipped = 0

    for ins in insights:
        raw_p = ins.get("priority") or "MEDIUM"
        rank = PRIORITY_RANK.get(str(raw_p).upper(), PRIORITY_RANK["MEDIUM"])
        if rank >= threshold:
            accepted.append(ins)
        else:
            skipped += 1
            logger.debug(
                "cascade: skipping insight id=%s priority=%s (below threshold=%s)",
                ins.get("id", "?"),
                raw_p,
                min_priority,
            )

    return accepted, skipped


def run_post_extraction_cascade(
    slug: str,
    insights_path: Path | None = None,
    bucket: str = "business",
) -> dict[str, Any]:
    """Run the full post-extraction cascade for a person.

    Reads per-slug INSIGHTS-STATE.json (Story MCE-11.14), applies priority
    filter, and cascades to cargo agents, theme dossiers, and by-person
    insights files.

    Args:
        slug: Person slug (e.g. "alex-hormozi").
        insights_path: Ignored — kept for backward-compatible call-sites.
            Reading strategy always uses the per-slug rich file at
            .data/artifacts/insights/{slug}/INSIGHTS-STATE.json (AC1).
        bucket: Knowledge bucket ("business" or "external").

    Returns:
        Dict with cascade results.
    """
    result: dict[str, Any] = {
        "slug": slug,
        "cargo_agents_updated": 0,
        "cargo_agents_found": 0,
        "themes_updated": 0,
        "themes_created": 0,
        "insights_processed": 0,
        "insights_skipped_priority": 0,
        "reading_strategy": "per_slug",  # AC1 — confirms reading strategy
        "solos_created": 0,  # MCE-13.2
        "solos_updated": 0,  # MCE-13.2
    }

    # AC1: always read from per-slug rich file
    per_slug_path: Path = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    all_insights, load_err = _load_per_slug_insights(slug)

    if load_err:
        result["error"] = load_err
        _log_action({"action": "cascade_error", **result})
        return result

    if not per_slug_path.exists():
        # AC4: no per-slug file → warn + skip (no fallback to global)
        result["skipped"] = f"cascade: no per-slug insights for {slug}, skipping"
        logger.warning("cascade: no per-slug insights for %s, skipping", slug)
        _log_action({"action": "cascade_skipped", **result})
        return result

    if not all_insights:
        result["skipped"] = f"No insights found in per-slug file for slug={slug}"
        _log_action({"action": "cascade_skipped", **result})
        return result

    # AC3: priority filter — only MEDIUM+ routed by default
    person_insights, skipped_count = _filter_by_priority(all_insights)
    result["insights_skipped_priority"] = skipped_count

    if not person_insights:
        result["skipped"] = (
            f"All {len(all_insights)} insights below priority threshold={CASCADE_MIN_PRIORITY}"
        )
        _log_action({"action": "cascade_skipped", **result})
        return result

    result["insights_processed"] = len(person_insights)

    # AC2 + AC5: log that rich fields are present so cascade log confirms priority
    if person_insights:
        sample = person_insights[0]
        logger.info(
            "cascade: slug=%s insights=%d sample priority=%s confidence=%s chunks=%d",
            slug,
            len(person_insights),
            sample.get("priority", "MEDIUM"),
            sample.get("confidence", "?"),
            len(sample.get("chunks", [])),
        )

    # --- Cascade to cargo agents ---
    # Mechanism 1: DNA-CONFIG reverse lookup — agents that explicitly list
    # this person in their dna_sources.primario[].pessoa field.
    cargo_dirs = _find_cargo_agents_for_person(slug)
    result["cargo_agents_found"] = len(cargo_dirs)

    # Mechanism 2 (Story MCE-11.6): THEME_TO_AGENTS + FRAMEWORK_TO_AGENTS
    # deterministic lookup — cargo agents that must receive cascade for
    # the themes/frameworks present in insights, regardless of DNA-CONFIG.
    # Union of both mechanisms (no duplicates) ensures full coverage.
    theme_map = load_theme_agent_map()
    dna_config_paths: set[Path] = set(cargo_dirs)
    theme_extra_dirs: list[Path] = []

    for ins in person_insights:
        extra_slugs, routing_log = theme_map.resolve_for_insight(ins)
        if extra_slugs:
            _log_action(
                {
                    "action": "theme_agent_map_resolved",
                    "slug": slug,
                    "insight_id": ins.get("id", "?"),
                    "routing": routing_log,
                    "extra_agents": extra_slugs,
                }
            )
            logger.debug("cascade: %s — %s", slug, routing_log)
            extra_dirs = _find_cargo_agents_by_slugs(extra_slugs)
            for d in extra_dirs:
                if d not in dna_config_paths:
                    dna_config_paths.add(d)
                    theme_extra_dirs.append(d)

    # Merge: all_cargo_dirs = mechanism-1 + mechanism-2 (deduplicated)
    all_cargo_dirs: list[Path] = cargo_dirs + theme_extra_dirs
    result["cargo_agents_theme_extra"] = len(theme_extra_dirs)
    result["cargo_agents_found_total"] = len(all_cargo_dirs)

    for agent_dir in all_cargo_dirs:
        # MCE-11.17 R5: verify DNA-CONFIG valid before MEMORY write (WARN-only V1).
        try:
            from engine.intelligence.pipeline.mce.enforcement import enforce_cargo_dna_config

            r5_result = enforce_cargo_dna_config(agent_dir)
            if not r5_result.passed:
                # V1: WARN only — continue cascade despite violation.
                _log_action(
                    {
                        "action": "r5_violation",
                        "agent": str(agent_dir.relative_to(ROOT)),
                        "code": r5_result.code,
                        "message": r5_result.message,
                        "slug": slug,
                    }
                )
        except Exception as _r5_exc:
            logger.debug("R5 enforcement check failed non-fatally: %s", _r5_exc)

        update_result = _update_cargo_memory(agent_dir, person_insights, slug)
        if update_result.get("appended", 0) > 0:
            result["cargo_agents_updated"] += 1
            _log_action(
                {
                    "action": "cargo_memory_updated",
                    "agent": str(agent_dir.relative_to(ROOT)),
                    "appended": update_result["appended"],
                    "slug": slug,
                    "mechanism": (
                        "theme_to_agents" if agent_dir in theme_extra_dirs else "dna_config"
                    ),
                }
            )

    # --- Cascade to theme dossiers + solo dossiers ---
    dossier_result = _update_theme_dossiers(person_insights, slug, bucket)
    result["themes_updated"] = dossier_result.get("themes_updated", 0)
    result["themes_created"] = dossier_result.get("themes_created", 0)
    result["themes_updated_secondary"] = dossier_result.get("themes_updated_secondary", 0)
    # MCE-13.2: solo dossier counts (person×theme intersections)
    result["solos_created"] = dossier_result.get("solos_created", 0)
    result["solos_updated"] = dossier_result.get("solos_updated", 0)

    # --- Cascade to by-person insights file ---
    by_person_result = _update_by_person_insights(slug, person_insights, bucket=bucket)
    result["by_person_updated"] = by_person_result.get("updated", False)
    result["by_person_insights_added"] = by_person_result.get("insights_added", 0)

    # --- Cascade to AGG-DOMAIN.yaml files ---
    # Updates structured YAML domain aggregates (not just MEMORY.md text).
    agg_result = _update_aggregated_domain_yamls(slug, person_insights, all_cargo_dirs)
    result["agg_domains_updated"] = agg_result.get("domains_updated", 0)
    result["agg_entries_added"] = agg_result.get("entries_added", 0)

    # MCE-13.4: ensure cross-refs between 3 dossier levels (fail-open)
    try:
        from scripts.mce_13_4_cross_refs import _ensure_cross_refs as _mcr

        _mcr(slug)
        result["cross_refs_updated"] = True
        logger.info("cascade: cross-refs reconciled for %s (MCE-13.4)", slug)
    except Exception as _xr_exc:
        result["cross_refs_updated"] = False
        logger.warning("cascade: cross-refs update failed non-fatally for %s: %s", slug, _xr_exc)

    _log_action({"action": "cascade_complete", **result})
    logger.info(
        "Cascade complete for %s: %d cargo agents updated, %d themes updated, %d themes created, %d agg domains updated",
        slug,
        result["cargo_agents_updated"],
        result["themes_updated"],
        result["themes_created"],
        result["agg_domains_updated"],
    )

    return result
