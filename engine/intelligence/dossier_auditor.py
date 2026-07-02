"""dossier_auditor.py — Audit inline chunk references in dossiers (Story MCE-3.2).

Validates that dossiers carry `[chunk_X-N]` inline citations on >=80% of
their statements (bullets, quotes, numbered items).

Usage:
    from engine.intelligence.dossier_auditor import audit_dossier_chunk_refs
    result = audit_dossier_chunk_refs(Path("knowledge/external/dossiers/persons/dossier-X.md"))
    # result = {total_statements, with_refs, missing_count, ratio, verdict, missing_lines}

Thresholds:
    PASS: ratio >= 0.80
    WARN: 0.50 <= ratio < 0.80
    FAIL: ratio < 0.50
"""

from __future__ import annotations

import re
from pathlib import Path

CHUNK_REF_PATTERN = re.compile(r"\[chunk_[A-Za-z0-9_\-/]+\]")
# Statement = bullet, numbered item, or blockquote
STATEMENT_PATTERN = re.compile(r"^\s*(?:[*-]|\d+\.|>)\s+\S")

PASS_THRESHOLD = 0.80
WARN_THRESHOLD = 0.50


def audit_dossier_chunk_refs(path: Path) -> dict:
    """Audit ratio of statements with inline `[chunk_X]` refs in a dossier.

    Args:
        path: Path to dossier markdown file.

    Returns:
        dict with: total_statements, with_refs, missing_count, ratio (float),
        verdict (PASS|WARN|FAIL), missing_lines (first 10 examples).
    """
    if not path.exists() or not path.is_file():
        return {
            "total_statements": 0,
            "with_refs": 0,
            "missing_count": 0,
            "ratio": 0.0,
            "verdict": "FAIL",
            "missing_lines": [],
            "error": f"file not found: {path}",
        }

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "total_statements": 0,
            "with_refs": 0,
            "missing_count": 0,
            "ratio": 0.0,
            "verdict": "FAIL",
            "missing_lines": [],
            "error": f"unreadable: {exc}",
        }

    lines = text.split("\n")
    total = 0
    with_refs = 0
    missing: list[tuple[int, str]] = []

    in_code_block = False
    in_header = True  # everything before first `## Section` is preamble
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip fenced code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        # Detect end of preamble: first `## ` heading
        if stripped.startswith("## ") and in_header:
            in_header = False
        # Skip ASCII art table separators
        if re.match(r"^\s*\|[-: |]+\|\s*$", line):
            continue
        # Skip table rows (column-based)
        if "|" in line and stripped.startswith("|"):
            continue
        # Skip frontmatter delimiters
        if stripped.startswith("---"):
            continue
        # Skip preamble blockquotes (metadata like "> Gerado por...", "> N insights")
        if in_header and stripped.startswith(">"):
            continue

        if STATEMENT_PATTERN.match(line):
            total += 1
            if CHUNK_REF_PATTERN.search(line):
                with_refs += 1
            else:
                missing.append((i, line[:100].strip()))

    ratio = with_refs / total if total > 0 else 0.0
    if ratio >= PASS_THRESHOLD:
        verdict = "PASS"
    elif ratio >= WARN_THRESHOLD:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    return {
        "total_statements": total,
        "with_refs": with_refs,
        "missing_count": len(missing),
        "ratio": round(ratio, 3),
        "verdict": verdict,
        "missing_lines": missing[:10],
    }


def audit_all_dossiers(bucket_root: Path | None = None) -> dict[str, dict]:
    """Audit all person dossiers under knowledge/{bucket}/dossiers/persons/.

    Args:
        bucket_root: Custom root for testing. Defaults to repo knowledge/.

    Returns:
        dict mapping dossier filename → audit result dict.
    """
    root = bucket_root or Path(__file__).resolve().parents[2] / "knowledge"
    results: dict[str, dict] = {}
    for bucket in ("external", "business", "personal"):
        persons_dir = root / bucket / "dossiers" / "persons"
        if not persons_dir.is_dir():
            continue
        for dossier in persons_dir.glob("dossier-*.md"):
            results[f"{bucket}/{dossier.name}"] = audit_dossier_chunk_refs(dossier)
    return results
