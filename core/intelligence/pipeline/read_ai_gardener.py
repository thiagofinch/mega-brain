"""
Read.ai Pessoal Gardener — organizes personal meeting transcripts into subfolders.

Scans root of inbox/PESSOAL/MEETINGS/ for uncategorized files and moves them
into theme subfolders based on keyword matching in the filename and content.

Themes:
  COACHING, NETWORKING, LEARNING, SALES, INTERVIEWS, PERSONAL, MISC

Only runs on trigger (every N personal ingestions, configured via READ_AI_GARDENER_TRIGGER).

Usage:
    from core.intelligence.pipeline.read_ai_gardener import PessoalGardener
    gardener = PessoalGardener(config)
    result = gardener.run()
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.intelligence.pipeline.read_ai_config import ReadAIConfig

# Theme definitions: (folder_name, keywords_in_filename_or_content)
THEMES: list[tuple[str, list[str]]] = [
    ("COACHING", [
        "coaching", "mentoring", "mentor", "mentoria", "acompanhamento",
        "sessao", "session", "1on1", "1:1", "one-on-one", "check-in",
    ]),
    ("NETWORKING", [
        "networking", "connection", "intro", "introduction", "coffee chat",
        "catch up", "catchup", "meet and greet",
    ]),
    ("LEARNING", [
        "workshop", "training", "course", "aula", "class", "webinar",
        "masterclass", "tutorial", "study", "learning",
    ]),
    ("SALES", [
        "sales call", "demo", "discovery", "pitch", "proposal",
        "closing", "follow up", "follow-up", "prospect", "lead",
        "deal", "negociacao", "venda",
    ]),
    ("INTERVIEWS", [
        "interview", "entrevista", "hiring", "candidate", "candidato",
        "screening", "assessment",
    ]),
    ("PERSONAL", [
        "personal", "pessoal", "family", "familia", "health", "saude",
        "doctor", "medico", "therapy", "terapia",
    ]),
]


@dataclass
class GardenResult:
    """Result of a gardener run."""

    files_scanned: int
    files_moved: int
    files_skipped: int  # already in subfolder
    moves: dict[str, int]  # theme → count


class PessoalGardener:
    """Organizes personal meeting transcripts into themed subfolders."""

    def __init__(self, config: ReadAIConfig):
        self.config = config
        self.pessoal_dir = config.pessoal_dir
        self._log_path = config.log_dir / "gardener.jsonl"

    def run(self) -> GardenResult:
        """
        Scan root files in pessoal_dir and move into theme subfolders.

        Only considers .txt files directly in the root of pessoal_dir
        (files already in subfolders are skipped).
        """
        if not self.pessoal_dir.exists():
            return GardenResult(0, 0, 0, {})

        root_files = [
            f for f in self.pessoal_dir.iterdir()
            if f.is_file() and f.suffix == ".txt"
        ]

        moves: dict[str, int] = {}
        files_moved = 0

        for filepath in root_files:
            theme = self._classify(filepath)
            dest_dir = self.pessoal_dir / theme
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filepath.name

            # Avoid overwriting
            if dest.exists():
                stem = dest.stem
                suffix = dest.suffix
                counter = 1
                while dest.exists():
                    dest = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            shutil.move(str(filepath), str(dest))
            files_moved += 1
            moves[theme] = moves.get(theme, 0) + 1

            self._log_move(filepath.name, theme, dest)

        result = GardenResult(
            files_scanned=len(root_files),
            files_moved=files_moved,
            files_skipped=0,
            moves=moves,
        )

        self._log_run(result)
        return result

    def _classify(self, filepath: Path) -> str:
        """
        Classify a transcript file into a theme based on filename and
        first 50 lines of content.
        """
        name_lower = filepath.name.lower()

        # Read first 50 lines for content matching
        content_sample = ""
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= 50:
                        break
                    lines.append(line)
                content_sample = " ".join(lines).lower()
        except OSError:
            pass

        combined = f"{name_lower} {content_sample}"

        for theme_name, keywords in THEMES:
            for kw in keywords:
                if kw in combined:
                    return theme_name

        return "MISC"

    def _log_move(self, filename: str, theme: str, dest: Path) -> None:
        """Log individual file move."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "file_moved",
            "filename": filename,
            "theme": theme,
            "destination": str(dest),
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _log_run(self, result: GardenResult) -> None:
        """Log gardener run summary."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "gardener_run",
            "files_scanned": result.files_scanned,
            "files_moved": result.files_moved,
            "moves": result.moves,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
