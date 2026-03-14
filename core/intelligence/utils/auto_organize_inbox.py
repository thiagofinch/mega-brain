#!/usr/bin/env python3
"""
Auto-organize INBOX files based on content type.
Watches the 00-INBOX folder and suggests actions for new files.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Paths
MEGA_BRAIN_ROOT = Path(__file__).parent.parent
INBOX_PATH = MEGA_BRAIN_ROOT / "00-INBOX"
KNOWLEDGE_PATH = MEGA_BRAIN_ROOT / "KNOWLEDGE"

# File type mappings
FILE_ACTIONS = {
    ".txt": "transcript",
    ".md": "document",
    ".mp4": "video",
    ".mp3": "audio",
    ".m4a": "audio",
    ".wav": "audio",
    ".pdf": "document",
    ".docx": "document",
    ".xlsx": "spreadsheet",
}

# Knowledge themes for classification
THEMES = {
    "01-estrutura-time": [
        "team",
        "structure",
        "org",
        "bdr",
        "sds",
        "bc",
        "hierarchy",
        "christmas tree",
    ],
    "02-processo-vendas": ["sales", "process", "closing", "closer", "call", "pitch", "objection"],
    "03-contratacao": ["hiring", "recruit", "interview", "onboard", "candidate", "farm system"],
    "04-comissionamento": ["compensation", "commission", "ote", "salary", "bonus", "incentive"],
    "05-metricas": ["metric", "kpi", "conversion", "rate", "benchmark", "cac", "ltv"],
    "06-funil-aplicacao": ["funnel", "application", "qualify", "lead", "pipeline"],
    "07-pricing": ["price", "pricing", "ticket", "high-ticket", "discount"],
    "08-ferramentas": ["tool", "crm", "software", "phone burner", "tech stack"],
    "09-gestao": ["management", "leadership", "coaching", "1:1", "training"],
}


def detect_themes(content: str) -> list:
    """Detect which knowledge themes match the content."""
    content_lower = content.lower()
    matches = []

    for theme, keywords in THEMES.items():
        for keyword in keywords:
            if keyword in content_lower:
                matches.append(theme)
                break

    return matches if matches else ["99-secundario"]


def get_file_info(file_path: Path) -> dict:
    """Get information about a file."""
    suffix = file_path.suffix.lower()

    return {
        "name": file_path.name,
        "type": FILE_ACTIONS.get(suffix, "unknown"),
        "size": file_path.stat().st_size,
        "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
    }


def scan_inbox() -> list:
    """Scan INBOX for files that need processing."""
    files = []

    for item in INBOX_PATH.iterdir():
        if item.is_file() and not item.name.startswith("."):
            info = get_file_info(item)

            # For transcripts, detect themes
            if info["type"] == "transcript":
                with open(item, "r", encoding="utf-8") as f:
                    content = f.read()
                info["themes"] = detect_themes(content)
                info["word_count"] = len(content.split())

            files.append({"path": item, **info})

    return files


def suggest_actions(files: list) -> None:
    """Print suggested actions for each file."""
    print("\n" + "=" * 60)
    print("MEGA BRAIN - INBOX SCANNER")
    print("=" * 60 + "\n")

    if not files:
        print("INBOX is empty. Nothing to process.")
        return

    for file in files:
        print(f"File: {file['name']}")
        print(f"  Type: {file['type']}")
        print(f"  Size: {file['size']:,} bytes")

        if file["type"] == "transcript":
            print(f"  Words: {file['word_count']:,}")
            print(f"  Detected themes: {', '.join(file['themes'])}")
            print(f"  Action: Run /extract-knowledge {file['path']}")

        elif file["type"] in ["video", "audio"]:
            print(f"  Action: Run /process-video {file['path']}")

        elif file["type"] == "document":
            print(f"  Action: Read and extract knowledge manually")

        print()

    print("=" * 60)
    print(f"Total files in INBOX: {len(files)}")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    if not INBOX_PATH.exists():
        print(f"Error: INBOX path does not exist: {INBOX_PATH}")
        sys.exit(1)

    files = scan_inbox()
    suggest_actions(files)


if __name__ == "__main__":
    main()
