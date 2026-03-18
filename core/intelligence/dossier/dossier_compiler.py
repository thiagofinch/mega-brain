#!/usr/bin/env python3
"""
DOSSIER COMPILER - Intelligence Layer v1.0
============================================
Auto-creates dossier markdown files from available knowledge (DNA + insights).

Called when dossier_trigger.py decides CREATE.  The trigger only EVALUATES;
this module does the actual file generation.

Behavior:
    1. Takes a theme/person slug and optional list of source insight IDs.
    2. Reads relevant insights from artifacts/insights/.
    3. Reads relevant DNA entries from knowledge/{bucket}/dna/persons/{slug}/.
    4. Compiles a markdown dossier with standard sections.
    5. Saves to knowledge/{bucket}/dossiers/{category}/{slug}.md

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - Dossier format uses ^[SOURCE:] traceability markers.
    - Incremental: if dossier exists, appends new sections (never overwrites).

Version: 1.0.0
Date: 2026-03-09
Story: S08 (EPIC-REORG-001)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

from core.paths import (  # noqa: E402
    ARTIFACTS,
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_EXTERNAL,
    LOGS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BUCKET RESOLUTION
# ---------------------------------------------------------------------------

_BUCKET_MAP: dict[str, Path] = {
    "external": KNOWLEDGE_EXTERNAL,
    "business": KNOWLEDGE_BUSINESS,
}


def _bucket_root(bucket: str) -> Path:
    """Resolve a bucket name to its knowledge directory."""
    if bucket not in _BUCKET_MAP:
        msg = f"Unknown bucket '{bucket}'. Valid: {list(_BUCKET_MAP)}"
        raise ValueError(msg)
    return _BUCKET_MAP[bucket]


# ---------------------------------------------------------------------------
# DNA READERS
# ---------------------------------------------------------------------------

_DNA_LAYERS = (
    ("FILOSOFIAS", "L1: Filosofias"),
    ("MODELOS-MENTAIS", "L2: Modelos Mentais"),
    ("HEURISTICAS", "L3: Heuristicas"),
    ("FRAMEWORKS", "L4: Frameworks"),
    ("METODOLOGIAS", "L5: Metodologias"),
)


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file, returning empty dict on failure."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        logger.warning("Failed to parse YAML: %s", path)
        return {}


def load_dna_config(slug: str, bucket: str = "external") -> dict[str, Any]:
    """Load the CONFIG.yaml for a person slug."""
    base = _bucket_root(bucket) / "dna" / "persons" / slug
    return _read_yaml(base / "CONFIG.yaml")


def load_dna_layers(slug: str, bucket: str = "external") -> dict[str, list[dict]]:
    """
    Load all 5 DNA layers for a slug.

    Returns a dict mapping layer key (e.g. 'FILOSOFIAS') to the list of items
    found in that YAML file.
    """
    base = _bucket_root(bucket) / "dna" / "persons" / slug
    layers: dict[str, list[dict]] = {}
    for filename, _label in _DNA_LAYERS:
        data = _read_yaml(base / f"{filename}.yaml")
        # Try the lowercase key matching the filename first,
        # then fall back to "itens" (newer DNA format).
        key = filename.lower().replace("-", "_")
        items = data.get(key) or data.get("itens", [])
        if isinstance(items, list):
            layers[filename] = items
        else:
            layers[filename] = []
    return layers


# ---------------------------------------------------------------------------
# INSIGHT READERS
# ---------------------------------------------------------------------------


def load_insights(insight_ids: list[str] | None = None) -> list[dict]:
    """
    Load insights from artifacts/insights/.

    If *insight_ids* is provided, only return matching entries.
    Otherwise return all insights found across JSON files.
    """
    insights_dir = ARTIFACTS / "insights"
    if not insights_dir.exists():
        return []

    all_insights: list[dict] = []
    for jf in sorted(insights_dir.glob("*.json")):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        # INSIGHTS-STATE.json has a nested structure: categories -> list
        if "categories" in data:
            for _cat_key, cat_val in data["categories"].items():
                for item in cat_val.get("insights", []):
                    all_insights.append(item)
        elif isinstance(data, list):
            all_insights.extend(data)

    if insight_ids is not None:
        id_set = set(insight_ids)
        return [i for i in all_insights if i.get("id") in id_set]
    return all_insights


# ---------------------------------------------------------------------------
# SECTION RENDERERS
# ---------------------------------------------------------------------------


def _render_header(
    slug: str,
    category: str,
    config: dict[str, Any],
    *,
    is_update: bool = False,
) -> str:
    """Render the dossier header block."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    person_name = config.get("pessoa", slug.replace("-", " ").title())
    version = "1.0.0" if not is_update else config.get("versao", "1.0.0")
    slug_upper = slug.upper()

    lines = [
        f"# Dossier: {person_name}",
        "",
        f"> **Slug:** {slug}",
        f"> **Category:** {category}",
        f"> **Version:** {version}",
        f"> **Generated:** {now}",
        "> **Source:** dossier_compiler.py v1.0.0 (S08)",
        "",
        "---",
        "",
    ]

    # TL;DR from config synthesis
    sintese = config.get("sintese", {})
    if sintese:
        lines.append("## TL;DR")
        lines.append("")
        em_uma_frase = sintese.get("em_uma_frase", "")
        if em_uma_frase:
            lines.append(f"> {em_uma_frase}")
            lines.append(f"> ^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:sintese]")
            lines.append("")
        paragrafo = sintese.get("paragrafo", "")
        if paragrafo:
            lines.append(paragrafo.strip())
            lines.append("")
        lines.append("---")
        lines.append("")

    # Identity table
    fontes = config.get("metadados", {}).get("fontes_utilizadas", [])
    n_fontes = len(fontes) if fontes else 0
    total_insights = config.get("metadados", {}).get("total_insights_processados", 0)

    lines.append("## Identidade")
    lines.append("")
    lines.append("| Campo | Valor |")
    lines.append("|-------|-------|")
    lines.append(f"| Nome | {person_name} |")
    if config.get("padroes_comportamentais", {}).get("tom_de_comunicacao", {}).get("estilo"):
        lines.append(
            f"| Estilo | {config['padroes_comportamentais']['tom_de_comunicacao']['estilo']} |"
        )
    lines.append(f"| Fontes Processadas | {n_fontes} |")
    lines.append(f"| Insights Totais | {total_insights} |")
    lines.append(f"| Slug | {slug_upper} |")
    lines.append(f"| Ultima Atualizacao | {now} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def _render_dna_section(layers: dict[str, list[dict]], slug: str) -> str:
    """Render the DNA Cognitivo section with all 5 layers."""
    lines = ["## DNA Cognitivo (5 Camadas)", ""]

    for filename, label in _DNA_LAYERS:
        items = layers.get(filename, [])
        lines.append(f"### {label}")
        lines.append("")
        if not items:
            lines.append("*Nenhum elemento encontrado nesta camada.*")
            lines.append("")
            continue

        # Render up to 15 items per layer for readability
        rendered = items[:15]
        for item in rendered:
            item_id = item.get("id", "?")
            nome = item.get("nome", item.get("name", ""))
            declaracao = item.get("declaracao", item.get("descricao", item.get("description", "")))

            if nome and declaracao:
                lines.append(f"- **{nome}:** {declaracao}")
            elif nome:
                lines.append(f"- **{nome}**")
            elif declaracao:
                lines.append(f"- {declaracao}")
            else:
                lines.append(f"- (Item {item_id})")
            lines.append(
                f"  ^[SOURCE:knowledge/external/dna/persons/{slug}/{filename}.yaml:{item_id}]"
            )

        remaining = len(items) - len(rendered)
        if remaining > 0:
            lines.append(f"- *... +{remaining} elementos adicionais*")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _render_insights_section(insights: list[dict]) -> str:
    """Render the key insights section."""
    lines = ["## Insights Principais", ""]
    if not insights:
        lines.append("*Nenhum insight disponivel para compilacao.*")
        lines.append("")
        return "\n".join(lines)

    # Group by priority (HIGH first)
    high = [i for i in insights if i.get("priority") == "HIGH"]
    medium = [i for i in insights if i.get("priority") == "MEDIUM"]
    rest = [i for i in insights if i.get("priority") not in {"HIGH", "MEDIUM"}]

    ordered = high + medium + rest

    for idx, item in enumerate(ordered[:20], 1):
        insight_id = item.get("id", f"INS-{idx:03d}")
        text = item.get("insight", item.get("text", ""))
        confidence = item.get("confidence", "")
        chunks = item.get("chunks", [])

        line = f"{idx}. {text}"
        if confidence:
            line += f" (confidence: {confidence})"
        lines.append(line)

        # Traceability marker
        chunk_ref = ", ".join(chunks[:3]) if chunks else insight_id
        lines.append(f"   ^[SOURCE:INSIGHTS-STATE.json:{chunk_ref}]")

    remaining = len(ordered) - 20
    if remaining > 0:
        lines.append(f"\n*... +{remaining} insights adicionais nao exibidos.*")

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _render_sources_section(config: dict[str, Any], slug: str) -> str:
    """Render the sources table."""
    lines = ["## Fontes", ""]
    fontes = config.get("metadados", {}).get("fontes_utilizadas", [])
    if not fontes:
        lines.append("*Nenhuma fonte registrada no CONFIG.yaml.*")
        lines.append("")
        return "\n".join(lines)

    lines.append("| ID | Titulo | Chunks |")
    lines.append("|----|--------|--------|")
    for f in fontes:
        sid = f.get("source_id", "?")
        title = f.get("source_title", "?")
        chunks = f.get("chunks_usados", 0)
        lines.append(f"| {sid} | {title} | {chunks} |")
        lines.append(
            f"^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:fontes_utilizadas:{sid}]"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _render_connections_section(config: dict[str, Any]) -> str:
    """Render the connections section if available."""
    conexoes = config.get("conexoes", {})
    if not conexoes:
        return ""

    lines = ["## Conexoes", ""]

    for kind, label in [
        ("complementa", "Complementa"),
        ("tensiona", "Tensiona"),
        ("alinha", "Alinha com"),
    ]:
        items = conexoes.get(kind, [])
        if items:
            lines.append(f"### {label}")
            lines.append("")
            for c in items:
                pessoa = c.get("pessoa", "?")
                em = c.get("em", "")
                nota = c.get("nota", "")
                lines.append(f"- **{pessoa}** em *{em}*: {nota}")
            lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _render_footer(slug: str) -> str:
    """Render the dossier footer."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"\n---\n\n"
        f"*Dossier compilado automaticamente por `dossier_compiler.py` v1.0.0*\n"
        f"*Story: S08 (EPIC-REORG-001)*\n"
        f"*Timestamp: {now}*\n"
    )


# ---------------------------------------------------------------------------
# INCREMENTAL APPEND
# ---------------------------------------------------------------------------


def _render_incremental_section(
    insight_ids: list[str],
    insights: list[dict],
    slug: str,
) -> str:
    """Render a section to append to an existing dossier."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "",
        "---",
        "",
        f"## Atualizacao Incremental ({now})",
        "",
        f"> Novos insights adicionados: {len(insights)}",
        f"> IDs: {', '.join(insight_ids[:10])}",
        "",
    ]

    if insights:
        lines.append("### Novos Insights")
        lines.append("")
        for idx, item in enumerate(insights, 1):
            insight_id = item.get("id", f"NEW-{idx:03d}")
            text = item.get("insight", item.get("text", ""))
            chunks = item.get("chunks", [])
            lines.append(f"{idx}. {text}")
            chunk_ref = ", ".join(chunks[:3]) if chunks else insight_id
            lines.append(f"   ^[SOURCE:INSIGHTS-STATE.json:{chunk_ref}]")
        lines.append("")

    lines.append(f"*Secao adicionada por `dossier_compiler.py` em {now}*")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CORE: compile_dossier
# ---------------------------------------------------------------------------


def compile_dossier(
    slug: str,
    category: str,
    bucket: str = "external",
    insight_ids: list[str] | None = None,
) -> Path:
    """
    Compile a dossier from available knowledge.

    Args:
        slug: Kebab-case identifier (e.g. 'alex-hormozi', 'call-funnels').
        category: Target subdirectory ('persons', 'themes', 'companies', 'operations').
        bucket: Knowledge bucket ('external' or 'business').
        insight_ids: Optional list of specific insight IDs to include.

    Returns:
        Path to the created/updated dossier file.

    Raises:
        ValueError: If bucket is unknown.
        FileNotFoundError: If no DNA data found for slug.
    """
    bucket_root = _bucket_root(bucket)
    dossier_dir = bucket_root / "dossiers" / category
    dossier_dir.mkdir(parents=True, exist_ok=True)

    slug_upper = slug.upper()
    dossier_path = dossier_dir / f"DOSSIER-{slug_upper}.md"

    # Load DNA
    config = load_dna_config(slug, bucket)
    layers = load_dna_layers(slug, bucket)

    # Check we have SOME data to work with
    total_dna = sum(len(v) for v in layers.values())
    if not config and total_dna == 0:
        msg = f"No DNA data found for slug '{slug}' in bucket '{bucket}'"
        raise FileNotFoundError(msg)

    # Load insights
    insights = load_insights(insight_ids)

    # If dossier already exists -> incremental append
    if dossier_path.exists():
        logger.info("Dossier exists at %s - appending incremental section", dossier_path)
        section = _render_incremental_section(
            insight_ids or [i.get("id", "") for i in insights],
            insights,
            slug,
        )
        with open(dossier_path, "a", encoding="utf-8") as f:
            f.write(section)

        _log_compilation(
            slug, category, bucket, dossier_path, mode="append", n_insights=len(insights)
        )
        return dossier_path

    # Fresh compilation
    logger.info("Compiling new dossier for '%s' -> %s", slug, dossier_path)

    sections = [
        _render_header(slug, category, config),
        _render_dna_section(layers, slug),
        _render_insights_section(insights),
        _render_sources_section(config, slug),
        _render_connections_section(config),
        _render_footer(slug),
    ]

    content = "".join(sections)
    dossier_path.write_text(content, encoding="utf-8")

    _log_compilation(slug, category, bucket, dossier_path, mode="create", n_insights=len(insights))
    return dossier_path


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------


def _log_compilation(
    slug: str,
    category: str,
    bucket: str,
    path: Path,
    *,
    mode: str,
    n_insights: int,
) -> None:
    """Append a compilation event to the dossier trigger log."""
    log_path = LOGS / "dossier-compilations.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": f"dossier_{mode}",
        "slug": slug,
        "category": category,
        "bucket": bucket,
        "path": str(path.relative_to(_ROOT)),
        "insights_included": n_insights,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info("[LOGGED] dossier_%s for %s -> %s", mode, slug, path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compile a dossier from DNA + insights.",
    )
    parser.add_argument("slug", help="Kebab-case slug (e.g. 'alex-hormozi')")
    parser.add_argument(
        "--category",
        default="persons",
        choices=["persons", "themes", "companies", "operations"],
        help="Dossier category (default: persons)",
    )
    parser.add_argument(
        "--bucket",
        default="external",
        choices=["external", "business"],
        help="Knowledge bucket (default: external)",
    )
    parser.add_argument(
        "--insight-ids",
        nargs="*",
        default=None,
        help="Specific insight IDs to include",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        result = compile_dossier(
            slug=args.slug,
            category=args.category,
            bucket=args.bucket,
            insight_ids=args.insight_ids,
        )
        print(f"\n[OK] Dossier compiled: {result}")
    except (ValueError, FileNotFoundError) as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
