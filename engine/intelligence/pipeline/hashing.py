"""hashing.py — SOT canonical hash for MegaBrain pipeline.

Single source of truth (SOT) for content hashing across the entire system.
Used by:
    - engine/intelligence/pipeline/ingestion_guard.py (Phase 0 dedup registry)
    - services/obsidian-sync/* (vault frontmatter mb_content_hash)
    - engine/intelligence/pipeline/semantic_logger.py (event content_hash field)

Why SOT? The roundtable on 2026-05-06 (finding F3 / data-engineer + qa)
identified hash drift as a HIGH risk: if Phase 0 ingestion-registry hashes
"foo\\n" but obsidian-sync hashes "foo\\r\\n", the two systems disagree on
whether content has changed, leading to silent vault corruption (file gets
overwritten when it shouldn't, or vice versa).

This module is the ONLY place hash logic lives. All callers MUST use
`canonical_hash()` — never construct sha256() inline for content.

STORY-OS-001 AC10-AC11.
"""

from __future__ import annotations

import hashlib
import unicodedata


def canonical_hash(body: bytes | str) -> str:
    """Return canonical SHA-256 hex digest of body content.

    Normalization steps (applied in order):
        1. Decode UTF-8 if input is bytes
        2. Strip UTF-8 BOM (U+FEFF) if present
        3. Normalize line endings: CRLF (\\r\\n) → LF (\\n)
        4. Unicode NFC normalization (canonical composition)
        5. SHA-256, return hex digest

    Important non-normalizations (PRESERVED, by design):
        - Trailing whitespace (significant in some formats — caller must strip)
        - Leading whitespace
        - Tab vs space (callers may have different conventions)
        - Case (markdown is case-sensitive)

    Why these choices?
        - BOM strip: Windows text editors silently insert BOM; without strip,
          same logical content yields different hashes.
        - CRLF→LF: Git autocrlf converts on Windows; hash must be platform-
          independent.
        - NFC: macOS HFS+ historically stored in NFD (decomposed); NFC ensures
          é (single codepoint) and é (e + combining acute) hash identically.

    Args:
        body: Content as bytes (assumed UTF-8) or str.

    Returns:
        SHA-256 hex digest (64 chars, lowercase).

    Examples:
        >>> canonical_hash("hello\\n")
        '5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03'

        >>> canonical_hash("hello\\r\\n") == canonical_hash("hello\\n")
        True

        >>> canonical_hash("\\ufeffhello\\n") == canonical_hash("hello\\n")
        True

    Raises:
        UnicodeDecodeError: if bytes input is not valid UTF-8.
    """
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    # Strip BOM if present at start
    if body.startswith("﻿"):
        body = body[1:]
    # Normalize line endings
    body = body.replace("\r\n", "\n")
    # Unicode NFC (canonical composition) — important on macOS
    body = unicodedata.normalize("NFC", body)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def canonical_hash_file(path) -> str:
    """Convenience: read file and return canonical_hash of its content.

    Args:
        path: pathlib.Path or str pointing to a UTF-8 text file.

    Returns:
        canonical_hash of file content.
    """
    from pathlib import Path

    p = Path(path)
    return canonical_hash(p.read_bytes())


__all__ = ["canonical_hash", "canonical_hash_file"]
