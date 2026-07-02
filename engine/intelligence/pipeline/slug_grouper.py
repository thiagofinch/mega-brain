"""
Slug Grouper — Groups files by their parent directory (slug).

Files arrive from patterns like:
    knowledge/business/inbox/{slug}/{filename}
    .claude/mission-control/mce/{slug}/{filename}

The slug is extracted as the immediate parent directory name of each file.

Usage:
    from engine.intelligence.pipeline.slug_grouper import group_files_by_slug

    groups = group_files_by_slug(file_list)
    # Returns: {"alex-hormozi": [Path(...), Path(...)], "cole-gordon": [Path(...)]}
"""

from pathlib import Path


def group_files_by_slug(file_list: list[Path]) -> dict[str, list[Path]]:
    """
    Group files by their slug (immediate parent directory name).

    Args:
        file_list: List of file paths to group.

    Returns:
        Dict mapping each unique slug to its ordered list of files.
        Order within each group preserves the original order from file_list.
    """
    groups: dict[str, list[Path]] = {}

    for file_path in file_list:
        path = Path(file_path) if not isinstance(file_path, Path) else file_path
        slug = path.parent.name

        if not slug:
            # Skip files with no parent directory (e.g., bare filenames)
            continue

        if slug not in groups:
            groups[slug] = []
        groups[slug].append(path)

    return groups
