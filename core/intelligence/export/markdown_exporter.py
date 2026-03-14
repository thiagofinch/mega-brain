"""
Markdown Exporter -- Export knowledge artifacts to clean markdown.
===================================================================

This is the default exporter and serves as a reference implementation.
It produces clean, portable markdown files.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .base import KnowledgeExporter


class MarkdownExporter(KnowledgeExporter):
    """Export knowledge artifacts to clean markdown format.

    This exporter:
    - Adds export metadata header
    - Cleans up internal references
    - Produces portable markdown
    """

    PLATFORM = "markdown"
    VERSION = "1.0.0"

    def format_playbook(
        self,
        playbook_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format playbook with export header."""
        playbook_path = Path(playbook_path)

        if not playbook_path.exists():
            raise FileNotFoundError(f"Playbook not found: {playbook_path}")

        content = playbook_path.read_text(encoding="utf-8")

        # Add export header
        header = self._create_header(
            artifact_type="Playbook",
            source_path=playbook_path,
            metadata=metadata,
        )

        return f"{header}\n{content}"

    def format_dna(
        self,
        dna_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format DNA schema as markdown.

        If path is a directory, combines all YAML files.
        If path is a file, formats that single file.
        """
        dna_path = Path(dna_path)

        if not dna_path.exists():
            raise FileNotFoundError(f"DNA not found: {dna_path}")

        if dna_path.is_dir():
            return self._format_dna_directory(dna_path, metadata)
        else:
            return self._format_dna_file(dna_path, metadata)

    def _format_dna_directory(
        self,
        dna_dir: Path,
        metadata: dict[str, Any] | None,
    ) -> str:
        """Format all YAML files in a DNA directory."""
        yaml_files = sorted(dna_dir.glob("*.yaml"))

        if not yaml_files:
            raise ValueError(f"No YAML files in: {dna_dir}")

        sections: list[str] = []

        header = self._create_header(
            artifact_type="DNA",
            source_path=dna_dir,
            metadata=metadata,
        )
        sections.append(header)

        for yaml_file in yaml_files:
            section_name = yaml_file.stem.replace("-", " ").title()
            sections.append(f"\n## {section_name}\n")

            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                sections.append(self._yaml_to_markdown(data))
            except yaml.YAMLError:
                # If not valid YAML, include raw content
                sections.append(f"```yaml\n{yaml_file.read_text()}\n```")

        return "\n".join(sections)

    def _format_dna_file(
        self,
        dna_file: Path,
        metadata: dict[str, Any] | None,
    ) -> str:
        """Format a single DNA YAML file."""
        header = self._create_header(
            artifact_type="DNA",
            source_path=dna_file,
            metadata=metadata,
        )

        try:
            with open(dna_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            content = self._yaml_to_markdown(data)
        except yaml.YAMLError:
            content = f"```yaml\n{dna_file.read_text()}\n```"

        return f"{header}\n{content}"

    def format_dossier(
        self,
        dossier_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format dossier with export header."""
        dossier_path = Path(dossier_path)

        if not dossier_path.exists():
            raise FileNotFoundError(f"Dossier not found: {dossier_path}")

        content = dossier_path.read_text(encoding="utf-8")

        header = self._create_header(
            artifact_type="Dossier",
            source_path=dossier_path,
            metadata=metadata,
        )

        return f"{header}\n{content}"

    def export(
        self,
        content: str,
        output_path: Path,
    ) -> Path:
        """Write content to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _create_header(
        self,
        artifact_type: str,
        source_path: Path,
        metadata: dict[str, Any] | None,
    ) -> str:
        """Create export metadata header."""
        now = datetime.now(UTC).isoformat(timespec="seconds")

        lines = [
            "---",
            f"exported_at: {now}",
            f"exporter: {self.PLATFORM}/{self.VERSION}",
            f"artifact_type: {artifact_type}",
            f"source: {source_path.name}",
        ]

        if metadata:
            for key, value in metadata.items():
                lines.append(f"{key}: {value}")

        lines.append("---\n")

        return "\n".join(lines)

    def _yaml_to_markdown(self, data: Any, indent: int = 0) -> str:
        """Convert YAML data to readable markdown list."""
        lines: list[str] = []
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}- **{key}**:")
                    lines.append(self._yaml_to_markdown(value, indent + 1))
                else:
                    lines.append(f"{prefix}- **{key}**: {value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(self._yaml_to_markdown(item, indent))
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{data}")

        return "\n".join(lines)
