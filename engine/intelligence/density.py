"""density.py — Compute dossier density score 0-5 (Story MCE-3.16).

Density is the trigger signal for Phase 8.1.8 DNA consolidation in JARVIS v2.1.
A dossier reaching density >= 3/5 is "saudavel" — enough material to merit
auto-running `cmd_consolidate`.

Five binary criteria, each worth 1 point (cap at 5):

    1. chunks_cited           >= 30   (via NAVIGATION-MAP)
    2. signature_phrases      >= 5    (via voice-dna.yaml)
    3. dna_layers_populated   >= 7/10 (via agent AGENT.md frontmatter)
    4. behavioral_patterns    >= 5    (via behavioral-patterns.yaml)
    5. insights_total         >= 50   (via INSIGHTS-STATE.json or agent frontmatter)

Indicator scale:

    ◯◯◯◯◯ (0) Vazio       ◐◐◐◯◯ (3) Saudavel ← TRIGGER POINT
    ◐◯◯◯◯ (1) Esboco      ◐◐◐◐◯ (4) Robusto
    ◐◐◯◯◯ (2) Esqueleto   ◐◐◐◐◐ (5) Completo
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]

CHUNKS_THRESHOLD = 30
SIGNATURE_PHRASES_THRESHOLD = 5
DNA_LAYERS_THRESHOLD = 7
BEHAVIORAL_PATTERNS_THRESHOLD = 5
INSIGHTS_THRESHOLD = 50

# Story MCE-11.19: read from thresholds.yaml; fallback to hardcoded values above.
try:
    from engine.intelligence.pipeline.config.threshold_loader import get_threshold as _get_th

    TRIGGER_DENSITY: int = _get_th("dna_auto_create.min_density", default=3)
    MAX_DENSITY: int = _get_th("dna_auto_create.max_density", default=5)
except Exception:
    TRIGGER_DENSITY = 3
    MAX_DENSITY = 5


def _safe_yaml_load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        logger.warning("density: cannot read yaml %s: %s", path, exc)
        return {}
    return data if isinstance(data, dict) else {}


def _safe_json_load(path: Path) -> dict | list:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("density: cannot read json %s: %s", path, exc)
        return {}


def _count_chunks_cited(slug: str, root: Path) -> int:
    """Pull from NAVIGATION-MAP.json."""
    nav_path = root / ".data" / "navigation-map.json"
    nav = _safe_json_load(nav_path)
    if not isinstance(nav, dict):
        return 0
    key = f"dossier-{slug}.md"
    for dtype_entries in nav.get("dossiers", {}).values():
        entry = dtype_entries.get(key)
        if entry:
            return int(entry.get("total_chunks_cited", 0) or 0)
    return 0


def _count_signature_phrases(slug: str, bucket: str, root: Path) -> int:
    voice = _safe_yaml_load(
        root / "knowledge" / bucket / "dna" / "persons" / slug / "voice-dna.yaml"
    )
    explicit = voice.get("total_signature_phrases")
    if isinstance(explicit, int) and explicit > 0:
        return explicit
    phrases = voice.get("signature_phrases") or []
    return len(phrases) if isinstance(phrases, list) else 0


def _read_agent_frontmatter(slug: str, bucket: str, root: Path) -> dict:
    """Pull YAML frontmatter from agents/{bucket}/{slug}/AGENT.md."""
    agent_md = root / "agents" / bucket / slug / "AGENT.md"
    if not agent_md.is_file():
        return {}
    try:
        text = agent_md.read_text(encoding="utf-8")
    except OSError:
        return {}
    # Accept either `---\n...\n---` frontmatter or `key: value` lines at top.
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        try:
            data = yaml.safe_load(fm_match.group(1))
            return data if isinstance(data, dict) else {}
        except yaml.YAMLError:
            return {}
    # Fallback: grep first 40 lines for known keys
    out: dict[str, Any] = {}
    for line in text.splitlines()[:40]:
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.+?)\s*$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        try:
            out[key] = int(val)
        except ValueError:
            out[key] = val.strip("'\"")
    return out


def _count_dna_layers(slug: str, bucket: str, root: Path) -> int:
    fm = _read_agent_frontmatter(slug, bucket, root)
    raw = fm.get("dna_layers_populated") or fm.get("dna_layers_complete")
    try:
        return int(raw) if raw is not None else 0
    except (TypeError, ValueError):
        return 0


def _count_behavioral_patterns(slug: str, bucket: str, root: Path) -> int:
    bp = _safe_yaml_load(
        root / "knowledge" / bucket / "dna" / "persons" / slug / "behavioral-patterns.yaml"
    )
    explicit = bp.get("total_patterns")
    if isinstance(explicit, int) and explicit > 0:
        return explicit
    patterns = bp.get("patterns") or bp.get("behavioral_patterns") or []
    return len(patterns) if isinstance(patterns, list) else 0


def _count_insights(slug: str, bucket: str, root: Path) -> int:
    # Prefer agent frontmatter (already aggregated)
    fm = _read_agent_frontmatter(slug, bucket, root)
    raw = fm.get("insights_count") or fm.get("total_insights")
    try:
        if raw is not None:
            return int(raw)
    except (TypeError, ValueError):
        pass
    # Fallback: INSIGHTS-STATE in .data/artifacts/mce
    insights_state = root / ".data" / "artifacts" / "mce" / slug / "INSIGHTS-STATE.json"
    data = _safe_json_load(insights_state)
    if isinstance(data, dict):
        explicit = data.get("total_insights") or data.get("insights_count")
        if isinstance(explicit, int):
            return explicit
        insights = data.get("insights") or []
        return len(insights) if isinstance(insights, list) else 0
    return 0


def compute_dossier_density(
    slug: str,
    bucket: str = "external",
    root: Path | None = None,
) -> dict:
    """Compute density 0-5 for a dossier and return breakdown.

    Returns:
        {
            "slug": str,
            "bucket": str,
            "density": int (0-5),
            "criteria": {
                "chunks_cited":           {value, threshold, met},
                "signature_phrases":      {...},
                "dna_layers_populated":   {...},
                "behavioral_patterns":    {...},
                "insights_total":         {...},
            }
        }
    """
    base = root or ROOT
    metrics = {
        "chunks_cited": (_count_chunks_cited(slug, base), CHUNKS_THRESHOLD),
        "signature_phrases": (
            _count_signature_phrases(slug, bucket, base),
            SIGNATURE_PHRASES_THRESHOLD,
        ),
        "dna_layers_populated": (
            _count_dna_layers(slug, bucket, base),
            DNA_LAYERS_THRESHOLD,
        ),
        "behavioral_patterns": (
            _count_behavioral_patterns(slug, bucket, base),
            BEHAVIORAL_PATTERNS_THRESHOLD,
        ),
        "insights_total": (_count_insights(slug, bucket, base), INSIGHTS_THRESHOLD),
    }
    score = 0
    breakdown: dict[str, dict] = {}
    for key, (value, threshold) in metrics.items():
        met = value >= threshold
        if met:
            score += 1
        breakdown[key] = {"value": value, "threshold": threshold, "met": met}

    return {
        "slug": slug,
        "bucket": bucket,
        "density": min(score, MAX_DENSITY),
        "criteria": breakdown,
    }


def render_density_indicator(density: int) -> str:
    """`4` -> `◐◐◐◐◯ (4)` (5-cell scale)."""
    d = max(0, min(int(density), MAX_DENSITY))
    filled = "◐" * d
    empty = "◯" * (MAX_DENSITY - d)
    return f"{filled}{empty} ({d})"


def density_label(density: int) -> str:
    """Human-readable status."""
    labels = {0: "Vazio", 1: "Esboco", 2: "Esqueleto", 3: "Saudavel", 4: "Robusto", 5: "Completo"}
    return labels.get(int(density), "Indefinido")
