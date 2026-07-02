"""
product_detector.py -- Stub module
==================================

Placeholder for the product-detection logic referenced by
``cmd_finalize`` in ``engine.intelligence.pipeline.mce.orchestrate``.

The real detector parses INSIGHTS-STATE.json categories, routes
product-related insights to per-product YAML files under
``workspace/businesses/{bu}/L3-product/`` and returns ``detected /
routed / staged`` counters that ``cmd_finalize`` aggregates into its
``product_detection`` block.

This stub keeps the import callable so the legacy ``cmd_finalize``
fallback branch does not crash. It returns a no-op result (zero
detections) so the rest of the pipeline can proceed without polluting
logs with ``ModuleNotFoundError``.

Status: TODO -- replace with a real implementation when product YAML
routing comes online (post G13). Tracked under the same auto-orchestration
hardening initiative as G13-G16 (2026-05-13).

Public surface (kept stable for cmd_finalize):
    - ``SourceMeta`` dataclass
    - ``detect_and_route(insight_text, field_path, value, source,
        source_count=1, dry_run=False)`` -> dict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceMeta:
    """Source metadata accepted by ``detect_and_route``.

    Mirrors the contract expected by ``cmd_finalize`` so the call site
    keeps compiling. Fields are intentionally permissive (typed loosely)
    to absorb whatever shape the metadata manager produces.
    """

    source_id: str = ""
    source_type: str = ""
    source_platform: str = ""
    participants: list[Any] = field(default_factory=list)
    has_summary: bool = False
    has_transcript: bool = False
    word_count: int = 0


def detect_and_route(
    *,
    insight_text: str,
    field_path: str,
    value: Any,
    source: SourceMeta,
    source_count: int = 1,
    dry_run: bool = False,
) -> dict[str, Any]:
    """No-op product detector.

    Returns a dict with ``detected=False`` so ``cmd_finalize`` records
    "0 routed / 0 staged" without raising. The real implementation will
    classify the insight, decide on a product YAML target, and either
    apply the change or stage it as a proposal.
    """
    return {
        "detected": False,
        "routed": False,
        "staged": False,
        "reason": "product_detector stub -- real router not yet implemented",
        "source_id": source.source_id,
        "field_path": field_path,
        "dry_run": dry_run,
    }
