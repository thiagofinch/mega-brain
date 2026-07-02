"""C-18 shim (2026-05-12): adapter for orchestrate.py process-batch.

orchestrate.py:_import_chunker imports ``chunk_document`` from
``engine.intelligence.pipeline.chunker`` — but the canonical chunker lives in
``engine.intelligence.rag.chunker`` with different function names. This shim
bridges the gap with zero behavior change to either side.

Canonical chunker contract (from rag/chunker.py):
  - chunk_markdown(filepath, person="", domain="", layer="") -> list[Chunk]
  - chunk_yaml(filepath, person="", layer="") -> list[Chunk]
  - _chunk_text_like_file(filepath, ...) -> list[Chunk]  (markdown path for .txt/.md)

This shim exposes ``chunk_document(file_path)`` which routes by extension.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from engine.intelligence.rag.chunker import (
    _chunk_text_like_file,
    chunk_yaml,
)

# Project root (mega-brain/). Mirror rag/chunker.py::BASE_DIR exactly so that
# chunk_markdown's ``filepath.relative_to(BASE_DIR)`` succeeds for our temp file.
# This file lives at engine/intelligence/pipeline/chunker.py → parents[3] == root.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Binary document formats that require a real extractor before chunking.
# Reading these as UTF-8 text yields garbage / zero usable chunks.
_BINARY_DOC_EXTENSIONS = {".pdf", ".docx"}


def _extract_binary_to_text(p: Path, ext: str) -> str:
    """Extract real text from a binary document (.pdf/.docx).

    Uses the existing orphaned extractors. Lazy-imported inside this function
    because they carry optional native deps (pymupdf/mammoth) — keeping the
    import here preserves import-time safety, consistent with the module's
    lazy pattern.

    Raises on missing dep / corrupt file; the caller fails open to an empty
    chunk list rather than reading binary as UTF-8.
    """
    from engine.intelligence.pipeline.extractors import extract_docx, extract_pdf

    if ext == ".pdf":
        return extract_pdf(str(p))
    # ext == ".docx"
    return extract_docx(str(p))


def chunk_document(file_path: str | Path) -> list[dict[str, Any]]:
    """Chunk a single document, returning serializable dicts.

    Routes by file extension to the canonical chunker function:
      .md / .txt  -> chunk_markdown (via _chunk_text_like_file)
      .yaml/.yml  -> chunk_yaml
      other       -> chunk_markdown (best-effort plain text path)

    Returns:
        List of dicts (not Chunk objects) so that orchestrate.py's transaction
        layer can JSON-serialize them without dataclass adapters.
    """
    p = Path(file_path)
    ext = p.suffix.lower()

    person = ""
    # Best-effort person inference from path
    for token in p.parts:
        if "knowledge" in token.lower() and len(p.parts) > 4:
            # e.g. knowledge/business/inbox/acme/misc/file.txt
            try:
                idx = list(p.parts).index("inbox")
                if idx + 1 < len(p.parts):
                    person = p.parts[idx + 1]
                    break
            except ValueError:
                pass

    if ext in {".yaml", ".yml"}:
        chunks = chunk_yaml(p, person=person)
    elif ext in _BINARY_DOC_EXTENSIONS:
        # Binary doc: extract real text first, then chunk the extracted text.
        # NEVER fall through to the UTF-8 text reader (it reads binary as
        # garbage → 0 usable chunks → empty DNA → Identity Checkpoint ABORT).
        chunks = []
        tmp_path: Path | None = None
        tmp_dir = _PROJECT_ROOT / ".data" / "tmp" / "pdf-extract"
        try:
            text = _extract_binary_to_text(p, ext)
            tmp_dir.mkdir(parents=True, exist_ok=True)
            # Temp file MUST live under _PROJECT_ROOT so chunk_markdown's
            # relative_to(BASE_DIR) does not raise. Keep the original stem for
            # traceable source_file metadata.
            fd, tmp_name = tempfile.mkstemp(
                prefix=f"{p.stem}.", suffix=".txt", dir=str(tmp_dir)
            )
            tmp_path = Path(tmp_name)
            with open(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
            chunks = _chunk_text_like_file(tmp_path, person=person)
        except Exception as exc:  # missing dep / corrupt file / extraction error
            print(
                f"[chunker] WARNING: failed to extract text from {ext} "
                f"'{p.name}': {type(exc).__name__}: {exc}. "
                f"Producing 0 chunks (fail-open, not reading binary as text).",
                flush=True,
            )
            chunks = []
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
    else:
        chunks = _chunk_text_like_file(p, person=person)

    # Serialize Chunk instances to dicts.
    # NOTE (2026-05-12): Chunk uses __slots__ so it has no __dict__. We must
    # extract via __slots__ explicitly. Falls back to __dict__ then str().
    result: list[dict[str, Any]] = []
    for c in chunks:
        if isinstance(c, dict):
            result.append(c)
        elif hasattr(c, "__slots__"):
            d = {}
            for slot in c.__slots__:
                if hasattr(c, slot):
                    val = getattr(c, slot)
                    # Skip non-serializable defaults
                    if val is not None:
                        d[slot] = val
            result.append(d)
        elif hasattr(c, "__dict__"):
            result.append({k: v for k, v in c.__dict__.items() if not k.startswith("_")})
        else:
            result.append({"text": str(c)})
    return result
