"""
workspace_sync.py -- Bridge descriptive knowledge to prescriptive workspace
=====================================================================
Syncs validated business intelligence from knowledge/business/ (descriptive --
what happened) into workspace/ (prescriptive -- how things should work).

Four sync rules:
  1. SOPs (status:approved) -> workspace/_templates/   (SOP promotion)
  2. Decisions              -> workspace/strategy/      (strategic decisions)
  3. Company dossiers       -> workspace/businesses/    (company intel refs)
  4. Person insights        -> workspace/team/          (team member summaries)

Each sync creates a lightweight .sync.yaml reference, NOT a full copy.
Human-edited workspace files are NEVER overwritten.

Design decisions:
  - .sync.yaml format mirrors .ref.yaml from smart_router (consistency)
  - Timestamp comparison: only syncs when source is newer than destination
  - Append-only JSONL logging for audit trail
  - ImportError-safe: can be called from batch_auto_creator or standalone

Constraints:
  - Python 3, stdlib + PyYAML only
  - Imports from core.paths

Version: 1.0.0
Date: 2026-03-10
Story: Phase 1.6 -- EPIC 1 (Workspace Sync)
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

from core.paths import (  # noqa: E402
    BUSINESS_DECISIONS,
    BUSINESS_DOSSIERS,
    BUSINESS_INSIGHTS,
    BUSINESS_SOPS,
    LOGS,
    ROUTING,
    WORKSPACE_BUSINESSES,
    WORKSPACE_STRATEGY,
    WORKSPACE_TEAM,
    WORKSPACE_TEMPLATES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

SYNC_LOG: Path = ROUTING.get("workspace_sync_log", LOGS / "workspace-sync.jsonl")

# Sentinel filename that marks a sync reference.
SYNC_SUFFIX = ".sync.yaml"

# Approved SOP statuses that qualify for promotion.
APPROVED_STATUSES: set[str] = {"approved", "validated", "promoted"}


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------


@dataclass
class SyncEntry:
    """Represents one synced item."""

    rule: str = ""
    source: str = ""
    destination: str = ""
    action: str = ""  # "created", "updated", "skipped"
    reason: str = ""


@dataclass
class SyncResult:
    """Aggregated result of a full sync run."""

    synced: list[SyncEntry] = field(default_factory=list)
    skipped: list[SyncEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def synced_count(self) -> int:
        return len(self.synced)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def to_dict(self) -> dict:
        return {
            "synced_count": self.synced_count,
            "skipped_count": self.skipped_count,
            "error_count": len(self.errors),
            "synced": [
                {"rule": e.rule, "source": e.source, "dest": e.destination, "action": e.action}
                for e in self.synced
            ],
            "skipped": [
                {"rule": e.rule, "source": e.source, "reason": e.reason} for e in self.skipped
            ],
            "errors": self.errors,
            "duration_ms": self.duration_ms,
        }


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    import re

    text = text.lower().strip()
    replacements = {
        "\u00e1": "a",
        "\u00e0": "a",
        "\u00e3": "a",
        "\u00e2": "a",
        "\u00e9": "e",
        "\u00ea": "e",
        "\u00ed": "i",
        "\u00f3": "o",
        "\u00f4": "o",
        "\u00f5": "o",
        "\u00fa": "u",
        "\u00fc": "u",
        "\u00e7": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:60] or "untitled"


def _is_newer(source: Path, dest: Path) -> bool:
    """Check if source file is newer than destination file.

    Returns True if source is newer (should sync) or dest does not exist.
    Returns False if dest is newer or same age (skip sync).
    """
    if not dest.exists():
        return True
    if not source.exists():
        return False

    source_mtime = source.stat().st_mtime
    dest_mtime = dest.stat().st_mtime
    return source_mtime > dest_mtime


def _is_human_edited(dest: Path) -> bool:
    """Check if a workspace file appears to be human-edited.

    A file is considered human-edited if:
      - It exists AND is NOT a .sync.yaml file
      - OR it's a .sync.yaml that was manually modified (has human_edited flag)
    """
    if not dest.exists():
        return False

    # .sync.yaml files are always safe to update
    if dest.name.endswith(SYNC_SUFFIX):
        try:
            data = yaml.safe_load(dest.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("human_edited"):
                return True
        except Exception:
            pass
        return False

    # Non-sync files in workspace are sacred
    return True


def _write_sync_ref(
    dest: Path,
    *,
    source_path: str,
    source_type: str,
    title: str,
    summary: str = "",
    metadata: dict | None = None,
) -> None:
    """Write a .sync.yaml reference file.

    This is the standard sync reference format. It contains a pointer back
    to the source file plus a lightweight summary, NOT a full copy.

    Args:
        dest: Absolute path to write the .sync.yaml file.
        source_path: Relative path to the source file (from project root).
        source_type: Type of source (sop, decision, dossier, insight).
        title: Human-readable title.
        summary: Brief summary of the content.
        metadata: Optional additional metadata dict.
    """
    ref_data: dict = {
        "sync_ref": True,
        "version": "1.0.0",
        "source_type": source_type,
        "source_path": source_path,
        "title": title,
        "summary": summary,
        "synced_at": _now_iso(),
        "auto_generated": True,
        "human_edited": False,
    }
    if metadata:
        ref_data["metadata"] = metadata

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write("# Auto-synced reference -- workspace_sync.py\n")
        f.write("# Source of truth: see source_path below\n")
        yaml.dump(
            ref_data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    logger.debug("Wrote sync ref: %s", dest)


def _relative_to_root(path: Path) -> str:
    """Get path relative to project root, as string."""
    try:
        return str(path.relative_to(_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# SYNC RULE 1: SOPs -> workspace/_templates/
# ---------------------------------------------------------------------------


def _sync_sops(result: SyncResult, *, dry_run: bool = False) -> None:
    """Promote validated SOPs from knowledge/business/sops/ to workspace/_templates/.

    Only SOPs with status in APPROVED_STATUSES are promoted.
    Creates a .sync.yaml reference in workspace/_templates/{area}/.
    """
    if not BUSINESS_SOPS.exists():
        logger.debug("No SOPs directory at %s", BUSINESS_SOPS)
        return

    sop_files = sorted(BUSINESS_SOPS.rglob("*.yaml"))

    for sop_path in sop_files:
        if sop_path.name.startswith("."):
            continue
        if sop_path.name.endswith(SYNC_SUFFIX):
            continue

        try:
            data = yaml.safe_load(sop_path.read_text(encoding="utf-8"))
        except Exception as exc:
            result.errors.append(f"Cannot parse SOP {sop_path.name}: {exc}")
            continue

        if not isinstance(data, dict):
            continue

        status = str(data.get("status", "")).lower()
        if status not in APPROVED_STATUSES:
            result.skipped.append(
                SyncEntry(
                    rule="sop_promotion",
                    source=_relative_to_root(sop_path),
                    reason=f"status={status} (need: {', '.join(sorted(APPROVED_STATUSES))})",
                )
            )
            continue

        # Determine destination: workspace/_templates/{area}/{slug}.sync.yaml
        area = data.get("area", "general")
        slug = _slugify(data.get("title", sop_path.stem))
        dest = WORKSPACE_TEMPLATES / area / f"{slug}{SYNC_SUFFIX}"

        # Check if newer
        if not _is_newer(sop_path, dest):
            result.skipped.append(
                SyncEntry(
                    rule="sop_promotion",
                    source=_relative_to_root(sop_path),
                    reason="destination is newer or same age",
                )
            )
            continue

        # Check if human-edited
        if _is_human_edited(dest):
            result.skipped.append(
                SyncEntry(
                    rule="sop_promotion",
                    source=_relative_to_root(sop_path),
                    reason="destination is human-edited (sacred)",
                )
            )
            continue

        action = "updated" if dest.exists() else "created"

        if not dry_run:
            _write_sync_ref(
                dest,
                source_path=_relative_to_root(sop_path),
                source_type="sop",
                title=data.get("title", slug),
                summary=f"SOP {data.get('id', 'unknown')} -- {len(data.get('steps', []))} steps",
                metadata={
                    "sop_id": data.get("id", ""),
                    "area": area,
                    "version": data.get("version", ""),
                    "step_count": len(data.get("steps", [])),
                },
            )

        result.synced.append(
            SyncEntry(
                rule="sop_promotion",
                source=_relative_to_root(sop_path),
                destination=_relative_to_root(dest),
                action=action,
            )
        )
        logger.info("SOP promoted: %s -> %s (%s)", sop_path.name, dest.name, action)


# ---------------------------------------------------------------------------
# SYNC RULE 2: Decisions -> workspace/strategy/
# ---------------------------------------------------------------------------


def _sync_decisions(result: SyncResult, *, dry_run: bool = False) -> None:
    """Sync strategic decisions from knowledge/business/decisions/ to workspace/strategy/.

    Scans for .md and .yaml decision files. Creates .sync.yaml references
    in workspace/strategy/decisions/.
    """
    if not BUSINESS_DECISIONS.exists():
        logger.debug("No decisions directory at %s", BUSINESS_DECISIONS)
        return

    decision_files = sorted(
        f
        for f in BUSINESS_DECISIONS.rglob("*")
        if f.is_file()
        and f.suffix in (".md", ".yaml", ".yml", ".json")
        and not f.name.startswith(".")
        and not f.name.endswith(SYNC_SUFFIX)
    )

    dest_dir = WORKSPACE_STRATEGY / "decisions"

    for dec_path in decision_files:
        slug = _slugify(dec_path.stem)
        dest = dest_dir / f"{slug}{SYNC_SUFFIX}"

        if not _is_newer(dec_path, dest):
            result.skipped.append(
                SyncEntry(
                    rule="decision_sync",
                    source=_relative_to_root(dec_path),
                    reason="destination is newer or same age",
                )
            )
            continue

        if _is_human_edited(dest):
            result.skipped.append(
                SyncEntry(
                    rule="decision_sync",
                    source=_relative_to_root(dec_path),
                    reason="destination is human-edited (sacred)",
                )
            )
            continue

        # Extract title from file
        title = dec_path.stem.replace("-", " ").replace("_", " ").title()
        summary = ""

        if dec_path.suffix in (".yaml", ".yml"):
            try:
                data = yaml.safe_load(dec_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    title = data.get("title", title)
                    summary = data.get("summary", data.get("description", ""))
            except Exception:
                pass
        elif dec_path.suffix == ".md":
            try:
                first_lines = dec_path.read_text(encoding="utf-8").split("\n", 5)
                for line in first_lines:
                    stripped = line.strip().lstrip("#").strip()
                    if stripped:
                        title = stripped
                        break
            except Exception:
                pass

        action = "updated" if dest.exists() else "created"

        if not dry_run:
            _write_sync_ref(
                dest,
                source_path=_relative_to_root(dec_path),
                source_type="decision",
                title=title,
                summary=str(summary)[:200] if summary else "",
                metadata={"original_filename": dec_path.name},
            )

        result.synced.append(
            SyncEntry(
                rule="decision_sync",
                source=_relative_to_root(dec_path),
                destination=_relative_to_root(dest),
                action=action,
            )
        )
        logger.info("Decision synced: %s -> %s (%s)", dec_path.name, dest.name, action)


# ---------------------------------------------------------------------------
# SYNC RULE 3: Company dossiers -> workspace/businesses/
# ---------------------------------------------------------------------------


def _sync_companies(result: SyncResult, *, dry_run: bool = False) -> None:
    """Sync company dossiers from knowledge/business/dossiers/companies/ to workspace/businesses/.

    Creates .sync.yaml references inside workspace/businesses/{company-slug}/.
    Respects existing human-edited files -- never overwrites them.
    """
    companies_dir = BUSINESS_DOSSIERS / "companies"
    if not companies_dir.exists():
        logger.debug("No company dossiers at %s", companies_dir)
        return

    dossier_files = sorted(
        f
        for f in companies_dir.rglob("*")
        if f.is_file()
        and f.suffix in (".md", ".yaml", ".yml", ".json")
        and not f.name.startswith(".")
        and not f.name.endswith(SYNC_SUFFIX)
    )

    for dos_path in dossier_files:
        # Derive company slug from filename (e.g., DOSSIER-ACME-CORP.md -> acme-corp)
        slug = _slugify(dos_path.stem.replace("DOSSIER-", "").replace("dossier-", ""))
        if not slug:
            slug = _slugify(dos_path.stem)

        dest_dir = WORKSPACE_BUSINESSES / slug
        dest = dest_dir / f"intel{SYNC_SUFFIX}"

        if not _is_newer(dos_path, dest):
            result.skipped.append(
                SyncEntry(
                    rule="company_sync",
                    source=_relative_to_root(dos_path),
                    reason="destination is newer or same age",
                )
            )
            continue

        if _is_human_edited(dest):
            result.skipped.append(
                SyncEntry(
                    rule="company_sync",
                    source=_relative_to_root(dos_path),
                    reason="destination is human-edited (sacred)",
                )
            )
            continue

        # Extract title
        title = slug.replace("-", " ").title()
        if dos_path.suffix == ".md":
            try:
                first_lines = dos_path.read_text(encoding="utf-8").split("\n", 5)
                for line in first_lines:
                    stripped = line.strip().lstrip("#").strip()
                    if stripped:
                        title = stripped
                        break
            except Exception:
                pass

        action = "updated" if dest.exists() else "created"

        if not dry_run:
            _write_sync_ref(
                dest,
                source_path=_relative_to_root(dos_path),
                source_type="company_dossier",
                title=title,
                summary=f"Intelligence dossier for {title}",
                metadata={
                    "company_slug": slug,
                    "original_filename": dos_path.name,
                },
            )

        result.synced.append(
            SyncEntry(
                rule="company_sync",
                source=_relative_to_root(dos_path),
                destination=_relative_to_root(dest),
                action=action,
            )
        )
        logger.info("Company dossier synced: %s -> %s (%s)", dos_path.name, dest.name, action)


# ---------------------------------------------------------------------------
# SYNC RULE 4: Person insights -> workspace/team/
# ---------------------------------------------------------------------------


def _sync_team_insights(result: SyncResult, *, dry_run: bool = False) -> None:
    """Sync person-level insights from knowledge/business/insights/by-person/ to workspace/team/.

    Creates .sync.yaml references inside workspace/team/{person-slug}/.
    These are lightweight pointers to the full insight data in the business bucket.
    """
    by_person_dir = BUSINESS_INSIGHTS / "by-person"
    if not by_person_dir.exists():
        logger.debug("No by-person insights at %s", by_person_dir)
        return

    # Scan for person subdirectories or individual files
    insight_items: list[Path] = []

    # Check for subdirectories (each person has a dir) or individual files
    for item in sorted(by_person_dir.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_dir() or (
            item.is_file()
            and item.suffix in (".md", ".yaml", ".yml", ".json")
            and not item.name.endswith(SYNC_SUFFIX)
        ):
            insight_items.append(item)

    for item in insight_items:
        if item.is_dir():
            person_slug = item.name
            source_path = item
            # Count files inside for summary
            file_count = sum(
                1 for f in item.rglob("*") if f.is_file() and not f.name.startswith(".")
            )
            summary = f"{file_count} insight file(s) for {person_slug}"
        else:
            person_slug = _slugify(item.stem)
            source_path = item
            summary = f"Insight summary for {person_slug}"
            file_count = 1

        dest_dir = WORKSPACE_TEAM / person_slug
        dest = dest_dir / f"insights{SYNC_SUFFIX}"

        if not _is_newer(source_path, dest):
            result.skipped.append(
                SyncEntry(
                    rule="team_insight_sync",
                    source=_relative_to_root(source_path),
                    reason="destination is newer or same age",
                )
            )
            continue

        if _is_human_edited(dest):
            result.skipped.append(
                SyncEntry(
                    rule="team_insight_sync",
                    source=_relative_to_root(source_path),
                    reason="destination is human-edited (sacred)",
                )
            )
            continue

        title = person_slug.replace("-", " ").title()
        action = "updated" if dest.exists() else "created"

        if not dry_run:
            _write_sync_ref(
                dest,
                source_path=_relative_to_root(source_path),
                source_type="team_insights",
                title=f"Insights: {title}",
                summary=summary,
                metadata={
                    "person_slug": person_slug,
                    "file_count": file_count,
                },
            )

        result.synced.append(
            SyncEntry(
                rule="team_insight_sync",
                source=_relative_to_root(source_path),
                destination=_relative_to_root(dest),
                action=action,
            )
        )
        logger.info("Team insights synced: %s -> %s (%s)", person_slug, dest.name, action)


# ---------------------------------------------------------------------------
# JSONL LOGGING
# ---------------------------------------------------------------------------


def _log_sync(result: SyncResult, *, dry_run: bool = False) -> None:
    """Append sync event to JSONL audit log."""
    try:
        SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": _now_iso(),
            "dry_run": dry_run,
            "synced_count": result.synced_count,
            "skipped_count": result.skipped_count,
            "error_count": len(result.errors),
            "duration_ms": result.duration_ms,
            "synced": [
                {"rule": e.rule, "source": e.source, "action": e.action} for e in result.synced
            ],
        }
        with open(SYNC_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write workspace sync log", exc_info=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------


def sync(*, dry_run: bool = False, verbose: bool = False) -> SyncResult:
    """Run all four sync rules.

    This is the main public API. It scans business knowledge sources and
    creates lightweight .sync.yaml references in workspace/ for any items
    that qualify for promotion.

    Args:
        dry_run: If True, report what would be synced but write nothing.
        verbose: If True, log at DEBUG level.

    Returns:
        SyncResult describing all actions taken.

    Example::

        from core.intelligence.pipeline.workspace_sync import sync

        result = sync(dry_run=True)
        print(f"Would sync {result.synced_count} items")
    """
    import time

    start = time.monotonic()

    if verbose:
        logger.setLevel(logging.DEBUG)

    result = SyncResult()

    # Rule 1: SOPs -> workspace/_templates/
    try:
        _sync_sops(result, dry_run=dry_run)
    except Exception as exc:
        result.errors.append(f"SOP sync failed: {exc}")
        logger.warning("SOP sync failed: %s", exc, exc_info=True)

    # Rule 2: Decisions -> workspace/strategy/
    try:
        _sync_decisions(result, dry_run=dry_run)
    except Exception as exc:
        result.errors.append(f"Decision sync failed: {exc}")
        logger.warning("Decision sync failed: %s", exc, exc_info=True)

    # Rule 3: Company dossiers -> workspace/businesses/
    try:
        _sync_companies(result, dry_run=dry_run)
    except Exception as exc:
        result.errors.append(f"Company sync failed: {exc}")
        logger.warning("Company sync failed: %s", exc, exc_info=True)

    # Rule 4: Person insights -> workspace/team/
    try:
        _sync_team_insights(result, dry_run=dry_run)
    except Exception as exc:
        result.errors.append(f"Team insight sync failed: {exc}")
        logger.warning("Team insight sync failed: %s", exc, exc_info=True)

    elapsed = int((time.monotonic() - start) * 1000)
    result.duration_ms = elapsed

    _log_sync(result, dry_run=dry_run)

    logger.info(
        "Workspace sync complete: %d synced, %d skipped, %d errors in %dms",
        result.synced_count,
        result.skipped_count,
        len(result.errors),
        elapsed,
    )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="workspace_sync",
        description=("Sync business knowledge to workspace (descriptive -> prescriptive)."),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced, write nothing.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging.",
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    prefix = "[DRY-RUN] " if args.dry_run else ""
    result = sync(dry_run=args.dry_run, verbose=args.verbose)

    print(f"\n{prefix}Workspace Sync Results ({result.duration_ms}ms)")
    print(f"  Synced:   {result.synced_count}")
    print(f"  Skipped:  {result.skipped_count}")
    print(f"  Errors:   {len(result.errors)}")

    if result.synced:
        print("\n  Synced items:")
        for entry in result.synced:
            src_name = Path(entry.source).name
            print(f"    [{entry.rule}] {src_name} -> {entry.destination} ({entry.action})")

    if result.skipped and args.verbose:
        print("\n  Skipped items:")
        for entry in result.skipped:
            src_name = Path(entry.source).name
            print(f"    [{entry.rule}] {src_name}: {entry.reason}")

    if result.errors:
        print("\n  Errors:")
        for err in result.errors:
            print(f"    [!] {err}")

    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
