"""
Base exporter -- Abstract base class for knowledge exporters.
==============================================================

Defines the interface that all exporters must implement.
Based on Strategy Pattern from Skill Seekers SkillAdaptor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class KnowledgeExporter(ABC):
    """Abstract base class for knowledge export formats.

    Subclasses implement format-specific logic for converting
    Mega Brain artifacts to external formats.

    Attributes:
        PLATFORM: Platform identifier (e.g., "markdown", "notion")
        VERSION: Exporter version for compatibility tracking
    """

    PLATFORM: str = "unknown"
    VERSION: str = "1.0.0"

    @abstractmethod
    def format_playbook(
        self,
        playbook_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format a playbook for export.

        Args:
            playbook_path: Path to playbook markdown file
            metadata: Optional additional metadata

        Returns:
            Formatted content ready for export
        """
        ...

    @abstractmethod
    def format_dna(
        self,
        dna_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format a DNA schema for export.

        Args:
            dna_path: Path to DNA YAML file or directory
            metadata: Optional additional metadata

        Returns:
            Formatted content ready for export
        """
        ...

    @abstractmethod
    def format_dossier(
        self,
        dossier_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format a dossier for export.

        Args:
            dossier_path: Path to dossier markdown file
            metadata: Optional additional metadata

        Returns:
            Formatted content ready for export
        """
        ...

    @abstractmethod
    def export(
        self,
        content: str,
        output_path: Path,
    ) -> Path:
        """Write formatted content to output destination.

        Args:
            content: Formatted content to export
            output_path: Destination path

        Returns:
            Path to created file
        """
        ...

    def export_playbook(
        self,
        playbook_path: Path,
        output_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Convenience method: format and export playbook.

        Args:
            playbook_path: Source playbook
            output_path: Destination
            metadata: Optional metadata

        Returns:
            Path to exported file
        """
        content = self.format_playbook(playbook_path, metadata)
        return self.export(content, output_path)

    def export_dna(
        self,
        dna_path: Path,
        output_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Convenience method: format and export DNA.

        Args:
            dna_path: Source DNA
            output_path: Destination
            metadata: Optional metadata

        Returns:
            Path to exported file
        """
        content = self.format_dna(dna_path, metadata)
        return self.export(content, output_path)

    def export_dossier(
        self,
        dossier_path: Path,
        output_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Convenience method: format and export dossier.

        Args:
            dossier_path: Source dossier
            output_path: Destination
            metadata: Optional metadata

        Returns:
            Path to exported file
        """
        content = self.format_dossier(dossier_path, metadata)
        return self.export(content, output_path)
