"""
core/intelligence/pipeline/index_generator.py — Source Index Auto-Generator

For each expert dir in knowledge/external/sources/*, scans all files and
generates an _INDEX.md using the source-index.md template format.

Usage:
    from engine.intelligence.pipeline.index_generator import generate_all_indexes
    paths = generate_all_indexes()

    # Single expert:
    from engine.intelligence.pipeline.index_generator import generate_index
    path = generate_index("alex-hormozi")
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from engine.paths import EXTERNAL_DNA_PERSONS, EXTERNAL_SOURCES

logger = logging.getLogger(__name__)

# File extensions to count as source documents
SOURCE_EXTENSIONS = {".md", ".txt", ".docx", ".pdf", ".yaml", ".yml"}

# Files/dirs to skip
SKIP_NAMES = {"_INDEX.md", "index.md", ".DS_Store", "__pycache__", ".gitkeep"}


def _count_entries_in_yaml(yaml_path: Path) -> int:
    """Count entries in a DNA YAML file without importing yaml (lightweight)."""
    if not yaml_path.exists():
        return 0
    try:
        import yaml

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, dict):
            entries = data.get("entries", [])
            if isinstance(entries, list):
                return len(entries)
            return data.get("total_entries", 0)
    except Exception:
        pass
    return 0


def _scan_source_files(source_dir: Path) -> list[dict[str, str]]:
    """Scan a source directory for content files, returning file metadata."""
    files: list[dict[str, str]] = []
    if not source_dir.exists():
        return files

    for item in sorted(source_dir.iterdir()):
        if item.name in SKIP_NAMES:
            continue
        if item.is_dir():
            # Count files in subdirectories (compiled/, raw/)
            subfiles = list(item.rglob("*"))
            doc_count = sum(
                1 for f in subfiles if f.is_file() and f.suffix.lower() in SOURCE_EXTENSIONS
            )
            if doc_count > 0:
                files.append(
                    {
                        "name": item.name + "/",
                        "type": "directory",
                        "docs": str(doc_count),
                        "modified": datetime.fromtimestamp(item.stat().st_mtime, tz=UTC).strftime(
                            "%Y-%m-%d"
                        ),
                    }
                )
        elif item.is_file() and item.suffix.lower() in SOURCE_EXTENSIONS:
            files.append(
                {
                    "name": item.name,
                    "type": item.suffix.lstrip(".").upper(),
                    "docs": "1",
                    "modified": datetime.fromtimestamp(item.stat().st_mtime, tz=UTC).strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

    return files


def _get_dna_summary(expert_slug: str) -> list[dict[str, str | int]]:
    """Get DNA layer summary for an expert."""
    expert_dna_dir = EXTERNAL_DNA_PERSONS / expert_slug
    if not expert_dna_dir.exists():
        return []

    layers = [
        ("FILOSOFIAS", "filosofias.yaml"),
        ("MODELOS-MENTAIS", "modelos-mentais.yaml"),
        ("HEURISTICAS", "heuristicas.yaml"),
        ("FRAMEWORKS", "frameworks.yaml"),
        ("METODOLOGIAS", "metodologias.yaml"),
    ]

    summary = []
    for layer_name, filename in layers:
        # Try case-insensitive match
        layer_path = None
        for child in expert_dna_dir.iterdir():
            if child.name.lower() == filename.lower():
                layer_path = child
                break

        count = _count_entries_in_yaml(layer_path) if layer_path else 0
        rel_path = (
            f"../../dna/persons/{expert_slug}/{layer_path.name}"
            if layer_path
            else f"../../dna/persons/{expert_slug}/{filename}"
        )
        summary.append({"layer": layer_name, "count": count, "file": rel_path})

    return summary


def _format_expert_name(slug: str) -> str:
    """Convert slug to display name: 'alex-hormozi' -> 'Alex Hormozi'."""
    return " ".join(word.capitalize() for word in slug.split("-"))


def generate_index(expert_slug: str) -> Path:
    """Generate _INDEX.md for one expert's source directory.

    Args:
        expert_slug: Expert directory name (e.g. "alex-hormozi").

    Returns:
        Path to the generated _INDEX.md file.
    """
    source_dir = EXTERNAL_SOURCES / expert_slug
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    expert_name = _format_expert_name(expert_slug)
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    # Scan source files
    source_files = _scan_source_files(source_dir)
    total_docs = sum(int(f["docs"]) for f in source_files)

    # Get DNA summary
    dna_summary = _get_dna_summary(expert_slug)
    total_dna_entries = sum(layer["count"] for layer in dna_summary)

    # Build the index markdown
    lines: list[str] = []
    lines.append(f"# INDICE: {expert_name.upper()}")
    lines.append("")
    lines.append("> **version:** 1.0.0")
    lines.append("> **owner:** pipeline-mce")
    lines.append(f"> **date:** {today}")
    lines.append("> **canonical_scope:** external.sources.index")
    lines.append(
        f"> **total_temas:** {len([f for f in source_files if f['type'] != 'directory' and f['name'].endswith('.md')])}"
    )
    lines.append(f"> **total_documentos_fonte:** {total_docs}")
    lines.append(f"> **mce_pipeline:** auto-generated -- {total_dna_entries} DNA entries")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Themes section (MD files as themes)
    theme_files = [f for f in source_files if f["type"] == "MD"]
    if theme_files:
        lines.append("## TEMAS DISPONIVEIS")
        lines.append("")
        lines.append("| Tema | Arquivo | Docs | Ultima atualizacao |")
        lines.append("|------|---------|------|--------------------|")
        for f in theme_files:
            theme_name = f["name"].replace(".md", "").replace("-", " ").replace("_", " ").title()
            lines.append(
                f"| {theme_name} | [{f['name']}](./{f['name']}) | {f['docs']} | {f['modified']} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    # Source files section (all files and dirs)
    lines.append("## TODOS OS ARQUIVOS")
    lines.append("")
    lines.append("| Arquivo | Tipo | Docs | Ultima atualizacao |")
    lines.append("|---------|------|------|--------------------|")
    for f in source_files:
        lines.append(f"| {f['name']} | {f['type']} | {f['docs']} | {f['modified']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # DNA summary
    if dna_summary:
        lines.append("## MCE EXTRACTION SUMMARY")
        lines.append("")
        lines.append("| Layer | Count | Files |")
        lines.append("|-------|-------|-------|")
        for layer in dna_summary:
            count_str = str(layer["count"]) if layer["count"] > 0 else "-"
            file_link = f"[{layer['layer']}.yaml]({layer['file']})" if layer["count"] > 0 else "-"
            lines.append(f"| {layer['layer']} | {count_str} | {file_link} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Agent section
    agent_types = ["external", "business", "personal"]
    for agent_type in agent_types:
        agent_dir = source_dir.parent.parent.parent.parent / "agents" / agent_type / expert_slug
        if agent_dir.exists():
            lines.append("## AGENTE")
            lines.append("")
            lines.append("| Arquivo | Path |")
            lines.append("|---------|------|")
            # MCE-13.6: check both lowercase and UPPERCASE conventions
            for canonical_file in ["agent.md", "soul.md", "memory.md", "dna-config.yaml"]:
                try:
                    from engine.intelligence.utils.agent_files import find_agent_file as _faf
                    resolved = _faf(agent_dir, canonical_file)
                except Exception:
                    resolved = None
                if resolved is not None and resolved.exists():
                    agent_file = resolved.name  # preserves actual casing on disk
                    rel = f"agents/{agent_type}/{expert_slug}/{agent_file}"
                    lines.append(f"| {agent_file} | [{rel}](../../../../{rel}) |")
            lines.append("")
            lines.append("---")
            lines.append("")
            break

    # Version history
    lines.append("## HISTORICO DE VERSOES")
    lines.append("")
    lines.append("| Versao | Data | Mudanca |")
    lines.append("|--------|------|---------|")
    lines.append(f"| 1.0.0 | {today} | Auto-generated by index_generator.py |")
    lines.append("")

    # Write the file
    output_path = source_dir / "_INDEX.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")

    logger.info(
        "Generated _INDEX.md for %s: %d files, %d DNA entries",
        expert_slug,
        total_docs,
        total_dna_entries,
    )
    return output_path


def generate_all_indexes() -> list[Path]:
    """Generate _INDEX.md for all experts in knowledge/external/sources/.

    Returns:
        List of paths to generated _INDEX.md files.
    """
    if not EXTERNAL_SOURCES.exists():
        logger.error("Sources directory not found: %s", EXTERNAL_SOURCES)
        return []

    generated: list[Path] = []
    expert_dirs = sorted(
        d for d in EXTERNAL_SOURCES.iterdir() if d.is_dir() and not d.name.startswith(".")
    )

    for expert_dir in expert_dirs:
        try:
            path = generate_index(expert_dir.name)
            generated.append(path)
        except Exception as exc:
            logger.error("Failed to generate index for %s: %s", expert_dir.name, exc)

    return generated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    paths = generate_all_indexes()
    print(f"\nGenerated {len(paths)} _INDEX.md files:")
    for p in paths:
        print(f"  {p}")
