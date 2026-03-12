#!/usr/bin/env python3
"""
CHUNKER - Hybrid RAG Phase 3.1
================================
Recursive character splitting with hierarchy preservation.
512 tokens (~2048 chars), 15% overlap.
Metadata per chunk: source_file, person, domain, layer, chunk_id.

Versao: 1.0.0
Data: 2026-03-01
"""

import hashlib
import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # mega-brain/
CHUNK_SIZE = 2048       # ~512 tokens (4 chars/token avg)
CHUNK_OVERLAP = 307     # ~15% of 2048
MIN_CHUNK_SIZE = 100    # Skip chunks smaller than this

# What to index
INDEX_SOURCES = {
    "dna": BASE_DIR / "knowledge" / "external" / "dna" / "persons",
    "dossiers_persons": BASE_DIR / "knowledge" / "external" / "dossiers" / "persons",
    "dossiers_themes": BASE_DIR / "knowledge" / "external" / "dossiers" / "themes",
    "playbooks": BASE_DIR / "knowledge" / "external" / "playbooks",
}


# ---------------------------------------------------------------------------
# CHUNK MODEL
# ---------------------------------------------------------------------------
class Chunk:
    """A text chunk with metadata."""

    __slots__ = (
        "chunk_id",
        "domain",
        "end_char",
        "layer",
        "metadata",
        "person",
        "section",
        "source_file",
        "start_char",
        "text",
    )

    def __init__(self, text: str, source_file: str, **kwargs):
        self.text = text
        self.source_file = source_file
        self.person = kwargs.get("person", "")
        self.domain = kwargs.get("domain", "")
        self.layer = kwargs.get("layer", "")
        self.section = kwargs.get("section", "")
        self.start_char = kwargs.get("start_char", 0)
        self.end_char = kwargs.get("end_char", 0)
        self.metadata = kwargs.get("metadata", {})
        # Generate deterministic chunk_id
        content_hash = hashlib.md5(
            f"{source_file}:{self.start_char}:{text[:100]}".encode()
        ).hexdigest()[:8]
        self.chunk_id = kwargs.get("chunk_id", f"ch_{content_hash}")

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_file": self.source_file,
            "person": self.person,
            "domain": self.domain,
            "layer": self.layer,
            "section": self.section,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "char_count": len(self.text),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# SPLITTING
# ---------------------------------------------------------------------------
def _split_by_sections(text: str) -> list[dict]:
    """Split markdown text by ## headers, preserving hierarchy."""
    sections = []
    lines = text.split("\n")
    current_section = ""
    current_lines: list[str] = []
    current_start = 0
    char_offset = 0

    for _i, line in enumerate(lines):
        line_len = len(line) + 1  # +1 for newline
        if line.startswith("## "):
            if current_lines:
                content = "\n".join(current_lines)
                sections.append({
                    "section": current_section,
                    "content": content,
                    "start_char": current_start,
                })
            current_section = line[3:].strip()
            current_lines = [line]
            current_start = char_offset
        else:
            current_lines.append(line)
        char_offset += line_len

    if current_lines:
        content = "\n".join(current_lines)
        sections.append({
            "section": current_section,
            "content": content,
            "start_char": current_start,
        })

    return sections


def _recursive_split(text: str, max_size: int = CHUNK_SIZE,
                     overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Recursively split text into chunks with overlap."""
    if len(text) <= max_size:
        return [text] if len(text) >= MIN_CHUNK_SIZE else []

    # Try splitting by paragraphs first
    separators = ["\n\n", "\n", ". ", " "]
    for sep in separators:
        parts = text.split(sep)
        if len(parts) > 1:
            chunks = []
            current = ""
            for part in parts:
                candidate = current + sep + part if current else part
                if len(candidate) > max_size and current:
                    chunks.append(current)
                    # Overlap: keep tail of previous chunk
                    tail = current[-overlap:] if overlap else ""
                    current = tail + sep + part if tail else part
                else:
                    current = candidate
            if current and len(current) >= MIN_CHUNK_SIZE:
                chunks.append(current)
            if chunks:
                return chunks

    # Fallback: hard split
    chunks = []
    for i in range(0, len(text), max_size - overlap):
        chunk = text[i:i + max_size]
        if len(chunk) >= MIN_CHUNK_SIZE:
            chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# FILE CHUNKERS
# ---------------------------------------------------------------------------
def chunk_markdown(filepath: Path, person: str = "", domain: str = "",
                   layer: str = "") -> list[Chunk]:
    """Chunk a markdown file preserving ## section hierarchy."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    rel_path = str(filepath.relative_to(BASE_DIR))
    sections = _split_by_sections(text)
    chunks = []

    for sec_info in sections:
        sec_name = sec_info["section"]
        sec_content = sec_info["content"]
        sec_start = sec_info["start_char"]

        sub_chunks = _recursive_split(sec_content)
        offset = 0
        for i, sub_text in enumerate(sub_chunks):
            start = sec_start + offset
            chunks.append(Chunk(
                text=sub_text,
                source_file=rel_path,
                person=person,
                domain=domain,
                layer=layer,
                section=sec_name,
                start_char=start,
                end_char=start + len(sub_text),
                metadata={"section_index": i},
            ))
            offset += len(sub_text)

    return chunks


def chunk_yaml(filepath: Path, person: str = "", layer: str = "") -> list[Chunk]:
    """Chunk a DNA YAML file — one chunk per entry."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return []

    rel_path = str(filepath.relative_to(BASE_DIR))
    chunks = []

    if not isinstance(data, dict):
        return []

    # Find the list of entries (e.g. heuristicas, frameworks, etc.)
    entries_list = None
    for v in data.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            entries_list = v
            break

    if not entries_list:
        return []

    layer_name = filepath.stem.lower()
    for i, entry in enumerate(entries_list):
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id", f"{layer_name}_{i}")
        # Serialize entry to text for embedding
        text_parts = [f"ID: {entry_id}"]
        for k, v in entry.items():
            if k == "id":
                continue
            if isinstance(v, str):
                text_parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                text_parts.append(f"{k}: {', '.join(str(x) for x in v)}")
            elif isinstance(v, dict):
                text_parts.append(f"{k}: {v}")

        text = "\n".join(text_parts)
        domains = entry.get("dominios", [])
        domain = domains[0] if domains else ""

        chunks.append(Chunk(
            text=text,
            source_file=rel_path,
            person=person,
            domain=domain,
            layer=layer_name,
            section=entry_id,
            chunk_id=entry_id,
            metadata={"entry_index": i, "domains": domains},
        ))

    return chunks


# ---------------------------------------------------------------------------
# FULL INDEX
# ---------------------------------------------------------------------------
def chunk_all(sources: dict[str, Path] | None = None) -> list[Chunk]:
    """Chunk all knowledge base files.

    Returns list of all chunks with metadata.
    """
    if sources is None:
        sources = INDEX_SOURCES

    all_chunks: list[Chunk] = []

    # 1. DNA YAMLs (per person)
    dna_dir = sources.get("dna")
    if dna_dir and dna_dir.exists():
        for person_dir in sorted(dna_dir.iterdir()):
            if not person_dir.is_dir() or person_dir.name.startswith(("_", ".")):
                continue
            person = person_dir.name
            for yaml_file in person_dir.glob("*.yaml"):
                if yaml_file.name == "CONFIG.yaml":
                    continue  # Skip config, it's not content
                all_chunks.extend(chunk_yaml(yaml_file, person=person))

    # 2. Person dossiers
    persons_dir = sources.get("dossiers_persons")
    if persons_dir and persons_dir.exists():
        for md_file in sorted(persons_dir.glob("DOSSIER-*.md")):
            person = _person_from_filename(md_file.stem)
            all_chunks.extend(chunk_markdown(md_file, person=person, layer="dossier"))

    # 3. Theme dossiers
    themes_dir = sources.get("dossiers_themes")
    if themes_dir and themes_dir.exists():
        for md_file in sorted(themes_dir.glob("DOSSIER-*.md")):
            domain = _domain_from_theme(md_file.stem)
            all_chunks.extend(chunk_markdown(md_file, domain=domain, layer="theme"))

    # 4. Playbooks
    playbooks_dir = sources.get("playbooks")
    if playbooks_dir and playbooks_dir.exists():
        for md_file in sorted(playbooks_dir.glob("*.md")):
            all_chunks.extend(chunk_markdown(md_file, layer="playbook"))

    return all_chunks


def _person_from_filename(stem: str) -> str:
    """Extract person name from dossier filename."""
    name = re.sub(r"^DOSSIER-", "", stem)
    return name.lower()


def _domain_from_theme(stem: str) -> str:
    """Extract domain hint from theme dossier filename."""
    name = re.sub(r"^DOSSIER-\d+-?", "", stem)
    return name.lower().replace("-", "_")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    print(f"\n{'='*60}")
    print("CHUNKER - Knowledge Base")
    print(f"{'='*60}\n")

    chunks = chunk_all()

    # Stats
    by_layer: dict[str, int] = {}
    by_person: dict[str, int] = {}
    total_chars = 0

    for c in chunks:
        by_layer[c.layer or "unknown"] = by_layer.get(c.layer or "unknown", 0) + 1
        if c.person:
            by_person[c.person] = by_person.get(c.person, 0) + 1
        total_chars += len(c.text)

    print(f"Total chunks: {len(chunks)}")
    print(f"Total chars: {total_chars:,} ({total_chars // 4:,} est. tokens)")
    print("\nBy layer:")
    for layer, count in sorted(by_layer.items()):
        print(f"  {layer}: {count}")
    print("\nBy person:")
    for person, count in sorted(by_person.items()):
        print(f"  {person}: {count}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
