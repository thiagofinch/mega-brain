"""
cli.py -- CLI Entry Point for MCE Pipeline Infrastructure
==========================================================

Run the MCE pipeline infrastructure from terminal without Claude Code.
Manages state tracking, metadata, metrics, and workflow detection.

.. note::
    This CLI orchestrates the **infrastructure** (state, metadata, metrics)
    but the actual extraction is done by the Claude Code MCE skill.
    The CLI is for monitoring and management, not for running prompts.

Usage::

    # Full pipeline (infrastructure setup)
    python -m core.intelligence.pipeline.mce.cli --persona alex-hormozi

    # Resume from last state
    python -m core.intelligence.pipeline.mce.cli --persona alex-hormozi --resume

    # Dry run (preview, no writes)
    python -m core.intelligence.pipeline.mce.cli --persona alex-hormozi --dry-run

    # Upgrade existing 5-layer agent to MCE
    python -m core.intelligence.pipeline.mce.cli --persona alex-hormozi --upgrade

    # Show help
    python -m core.intelligence.pipeline.mce.cli --help

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path for direct invocation
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Module imports (after path fix)
# ---------------------------------------------------------------------------

from core.intelligence.pipeline.mce.metadata_manager import MetadataManager
from core.intelligence.pipeline.mce.metrics import MetricsTracker
from core.intelligence.pipeline.mce.state_machine import PipelineStateMachine
from core.intelligence.pipeline.mce.workflow_detector import WorkflowMode, detect

logger = logging.getLogger("mce.cli")


# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------


def _header(text: str) -> None:
    """Print a section header."""
    width = 70
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def _info(label: str, value: str) -> None:
    """Print a labeled info line."""
    print(f"  {label:<24} {value}")


def _separator() -> None:
    print("-" * 70)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_status(slug: str, verbose: bool = False) -> int:
    """Show current pipeline status for a persona.

    Returns:
        0 if state exists, 1 if no state found.
    """
    _header(f"MCE Pipeline Status: {slug}")

    # State machine
    sm = PipelineStateMachine(slug)
    _info("Current State:", sm.state)
    _info("Is Terminal:", str(sm.is_terminal))
    _info("State File:", str(sm.state_path))

    # Metadata
    mgr = MetadataManager.load(slug)
    if mgr:
        _separator()
        _info("Pipeline Status:", mgr.pipeline_status)
        _info("Mode:", mgr.mode)
        _info("Source Code:", mgr.source_code or "(none)")
        _info("Phases Complete:", str(len(mgr.completed_phase_names)))
        _info("Sources Processed:", str(len(mgr.sources_processed)))
        _info("Next Phase:", mgr.next_incomplete_phase or "ALL DONE")

        if verbose and mgr.phases_completed:
            _separator()
            print("  Phase Details:")
            for name, data in mgr.phases_completed.items():
                status = "DONE" if data.get("completed") else "IN PROGRESS"
                print(f"    {name:<28} [{status}]")
    else:
        print("  (no metadata found)")

    # Metrics
    mt = MetricsTracker.load(slug)
    if mt:
        _separator()
        _info("Total Duration:", f"{mt.total_duration_seconds:.1f}s")
        _info("Phases Timed:", str(mt.phases_completed))

        if verbose:
            for name in mt.phase_names:
                dur = mt.phase_duration(name)
                print(f"    {name:<28} {dur:.1f}s")
    else:
        print("  (no metrics found)")

    print()
    return 0 if mgr else 1


def cmd_detect(slug: str, verbose: bool = False) -> int:
    """Detect workflow mode (greenfield/brownfield).

    Returns:
        0 always (detection is informational).
    """
    _header(f"Workflow Detection: {slug}")

    mode = detect(slug)

    _info("Mode:", mode.mode.upper())
    _info("Has Agent:", str(mode.has_agent))
    _info("Has DNA:", str(mode.has_dna))
    _info("Has MCE:", str(mode.has_mce))
    _info("New Sources:", str(len(mode.new_sources)))
    _info("Delta Sources:", str(len(mode.delta_sources)))

    if verbose and mode.new_sources:
        _separator()
        print("  New Sources:")
        for f in mode.new_sources[:20]:
            print(f"    + {f}")
        if len(mode.new_sources) > 20:
            print(f"    ... and {len(mode.new_sources) - 20} more")

    if verbose and mode.delta_sources:
        _separator()
        print("  Delta Sources (may need re-processing):")
        for f in mode.delta_sources[:20]:
            print(f"    ~ {f}")

    print()
    return 0


def cmd_init(
    slug: str,
    *,
    dry_run: bool = False,
    upgrade: bool = False,
    skip_checkpoint: bool = False,
    verbose: bool = False,
) -> int:
    """Initialize MCE pipeline infrastructure for a persona.

    Creates state machine, metadata, and metrics files.  Does NOT
    run extraction (that requires Claude Code).

    Args:
        slug: Persona slug.
        dry_run: If True, only preview what would happen.
        upgrade: If True, treats as brownfield upgrade from legacy 5-layer.
        skip_checkpoint: If True, notes that identity checkpoint will be
                         auto-approved.
        verbose: Extra output.

    Returns:
        0 on success, 1 on error.
    """
    _header(f"MCE Pipeline Init: {slug}")

    # Step 1: Workflow detection
    mode: WorkflowMode = detect(slug)
    effective_mode = mode.mode
    if upgrade and not mode.has_mce:
        effective_mode = "brownfield"

    _info("Detected Mode:", mode.mode.upper())
    if upgrade:
        _info("Upgrade Mode:", "YES (adding MCE layers to existing agent)")
    _info("Effective Mode:", effective_mode.upper())
    _info("New Sources:", str(len(mode.new_sources)))

    if not mode.new_sources and mode.is_greenfield:
        print()
        print("  WARNING: No sources found in inbox.")
        print(f"  Place source files in knowledge/external/inbox/{slug}/")
        print()
        return 1

    if dry_run:
        _separator()
        print("  DRY RUN -- no files will be written")
        _separator()
        print()
        print("  Would create:")
        print("    - State machine (init state)")
        print(f"    - Metadata ({effective_mode}, {len(mode.new_sources)} sources)")
        print("    - Metrics tracker")
        if skip_checkpoint:
            print("    - Identity checkpoint: AUTO-APPROVE")
        print()
        print("  Next step: Run MCE skill in Claude Code to start extraction.")
        print()
        return 0

    # Step 2: Initialize state machine
    sm = PipelineStateMachine(slug, auto_load=False)
    sm.save()
    _info("State Machine:", f"INIT -> {sm.state_path}")

    # Step 3: Initialize metadata
    source_code = slug[:2].upper().replace("-", "")
    mgr = MetadataManager(slug, mode=effective_mode, source_code=source_code)
    mgr.pipeline_status = "not_started"
    mgr.save()
    _info("Metadata:", f"CREATED -> {mgr.metadata_path}")

    # Step 4: Initialize metrics
    mt = MetricsTracker(slug)
    mt.save()
    _info("Metrics:", f"CREATED -> {mt.metrics_path}")

    _separator()

    if skip_checkpoint:
        print("  NOTE: Identity checkpoint will be auto-approved.")

    print()
    print("  Infrastructure ready. Next steps:")
    print("  1. Open Claude Code in this project")
    print(f"  2. Run: /mce --persona {slug}")
    print("  3. The skill will use this infrastructure for state tracking")
    print()

    if verbose:
        _separator()
        print("  Created files:")
        print(f"    {sm.state_path}")
        print(f"    {mgr.metadata_path}")
        print(f"    {mt.metrics_path}")
        print()

    return 0


def cmd_resume(slug: str, verbose: bool = False) -> int:
    """Resume pipeline from last saved state.

    Returns:
        0 if resumable state found, 1 if not.
    """
    _header(f"MCE Pipeline Resume: {slug}")

    sm = PipelineStateMachine(slug)

    if sm.state == "init":
        print("  No previous state found. Use --persona without --resume to start.")
        print()
        return 1

    if sm.is_terminal:
        print(f"  Pipeline is in terminal state: {sm.state}")
        print("  Use reset or start a new pipeline run.")
        print()
        return 1

    _info("Resuming from:", sm.state)

    mgr = MetadataManager.load(slug)
    if mgr:
        next_phase = mgr.next_incomplete_phase
        _info("Next Phase:", next_phase or "ALL DONE")
        _info("Pipeline Status:", mgr.pipeline_status)
    else:
        _info("Metadata:", "NOT FOUND (may need reinit)")

    mt = MetricsTracker.load(slug)
    if mt:
        _info("Time Spent:", f"{mt.total_duration_seconds:.1f}s so far")

    print()
    print("  Infrastructure is ready to resume.")
    print("  Open Claude Code and the MCE skill will pick up from this state.")
    print()
    return 0


def cmd_reset(slug: str, dry_run: bool = False) -> int:
    """Reset pipeline state to init.

    Returns:
        0 on success.
    """
    _header(f"MCE Pipeline Reset: {slug}")

    if dry_run:
        print("  DRY RUN -- would reset state to 'init'")
        print()
        return 0

    sm = PipelineStateMachine(slug)
    old_state = sm.state
    sm.reset()

    _info("Previous State:", old_state)
    _info("New State:", sm.state)
    print()
    return 0


# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m core.intelligence.pipeline.mce.cli",
        description=(
            "MCE Pipeline Infrastructure CLI -- manage state, metadata, "
            "and metrics for Mind Clone Extraction pipeline runs."
        ),
    )

    parser.add_argument(
        "--persona",
        required=True,
        help="Persona slug (e.g. alex-hormozi, cole-gordon)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume from last saved state",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview actions without writing files",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        default=False,
        help="Upgrade existing 5-layer agent to MCE (forces brownfield mode)",
    )
    parser.add_argument(
        "--skip-checkpoint",
        action="store_true",
        default=False,
        help="Auto-approve identity checkpoint (skip manual review)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=False,
        help="Reset pipeline state to init",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        default=False,
        help="Show current pipeline status (alias for default behavior)",
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        default=False,
        help="Only run workflow detection (greenfield/brownfield)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code (0 = success, 1 = error/no-state).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(name)s: %(message)s",
    )

    slug: str = args.persona

    # Route to appropriate command
    if args.detect:
        return cmd_detect(slug, verbose=args.verbose)

    if args.reset:
        return cmd_reset(slug, dry_run=args.dry_run)

    if args.resume:
        return cmd_resume(slug, verbose=args.verbose)

    if args.status:
        return cmd_status(slug, verbose=args.verbose)

    # Default: check if state exists already
    sm = PipelineStateMachine(slug)
    if sm.state != "init" and not args.dry_run:
        # State exists -- show status
        return cmd_status(slug, verbose=args.verbose)

    # No state or explicitly starting -- init
    return cmd_init(
        slug,
        dry_run=args.dry_run,
        upgrade=args.upgrade,
        skip_checkpoint=args.skip_checkpoint,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())
