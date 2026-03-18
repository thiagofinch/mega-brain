"""
batch_governor.py -- Batch Size Governor
========================================
Partitions large file sets into manageable batches for Pipeline Jarvis.

Rules:
  - Max 5 files per batch (configurable)
  - Files grouped by source person when possible
  - Each batch gets a sequential ID (BATCH-001, BATCH-002, ...)
  - Returns list of batches ready for sequential processing

Version: 1.0.0
Date: 2026-03-07
"""

from pathlib import Path

from core.paths import INBOX

MAX_BATCH_SIZE = 5


def _extract_source_hint(filepath: Path) -> str:
    """Extract a grouping hint from the file path."""
    try:
        rel = filepath.relative_to(INBOX)
        if len(rel.parts) > 1:
            return rel.parts[0]
    except ValueError:
        pass

    parent = filepath.parent.name
    if parent and parent.lower() not in {"inbox", "meetings", "calls", "documents"}:
        return parent

    return "ungrouped"


def partition_files(
    files: list[Path],
    max_size: int = MAX_BATCH_SIZE,
) -> list[dict]:
    """Partition a list of files into batches."""
    if not files:
        return []

    groups: dict[str, list[Path]] = {}
    for f in files:
        hint = _extract_source_hint(f)
        groups.setdefault(hint, []).append(f)

    batches = []
    batch_num = 1

    for source, group_files in sorted(groups.items()):
        for i in range(0, len(group_files), max_size):
            chunk = group_files[i : i + max_size]
            batch_id = f"BATCH-{batch_num:03d}"
            batches.append(
                {
                    "id": batch_id,
                    "source_hint": source,
                    "files": [str(f) for f in chunk],
                    "count": len(chunk),
                    "total_size": sum(f.stat().st_size for f in chunk if f.exists()),
                }
            )
            batch_num += 1

    return batches


def should_partition(file_count: int) -> bool:
    """Check if a file set needs partitioning."""
    return file_count > MAX_BATCH_SIZE


def format_plan(batches: list[dict]) -> str:
    """Format a batch plan for display in the pipeline."""
    if not batches:
        return "No files to process."

    total_files = sum(b["count"] for b in batches)
    lines = [
        f"GOVERNOR: {total_files} files -> {len(batches)} batches (max {MAX_BATCH_SIZE}/batch)",
        "",
    ]

    for b in batches:
        lines.append(f"  {b['id']} [{b['source_hint']}] - {b['count']} files")
        for f in b["files"]:
            lines.append(f"    - {Path(f).name}")

    return "\n".join(lines)
