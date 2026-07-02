#!/usr/bin/env python3
"""
Startup Health Hook v2.0 — SessionStart
========================================
Validates critical directories and state files on session start.
Delegates holistic 0-100 scoring to HealthScorer (MCE-11.12).
Prints compact health summary. Never blocks (always exit 0).

Hook: SessionStart | Timeout: 5s
Epic 3.3 — Governance Engine
Story MCE-11.12 — v2.0: delegates to HealthScorer for ATENCAO/CRITICO display
"""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

# Critical directories that MUST exist
CRITICAL_DIRS = [
    "engine",
    "agents",
    "knowledge/external",
    ".claude/hooks",
    "docs/governance/rules",
    ".claude/skills",
]

# Critical state files that MUST exist
CRITICAL_FILES = [
    "engine/paths.py",
    "agents/_registry/ecosystem-registry.yaml",
    ".claude/settings.json",
]

# ROUTING keys to spot-check (sample — not all 131)
ROUTING_SPOT_CHECKS = [
    "logs",
    "artifacts/audit",
    ".data",
    ".claude/sessions",
    ".claude/mission-control",
]


def main():
    try:
        missing_dirs = []
        for d in CRITICAL_DIRS:
            if not (_ROOT / d).is_dir():
                missing_dirs.append(d)

        missing_files = []
        for f in CRITICAL_FILES:
            if not (_ROOT / f).is_file():
                missing_files.append(f)

        missing_routing = []
        try:
            from engine.paths import ROUTING

            for key in ROUTING_SPOT_CHECKS:
                path = _ROOT / key
                if not path.parent.exists():
                    missing_routing.append(key)
        except ImportError:
            missing_routing.append("engine.paths import failed")

        rag_checks = []
        for bucket_name, bucket_path in [
            ("business", ".data/rag_business"),
            ("external", ".data/rag_index"),
            ("personal", "knowledge/personal/index"),
        ]:
            full_path = _ROOT / bucket_path
            chunks_path = full_path / "chunks.json"
            if not full_path.exists() or not chunks_path.exists():
                continue

            try:
                with chunks_path.open(encoding="utf-8") as handle:
                    chunks = json.load(handle)
            except (OSError, json.JSONDecodeError):
                rag_checks.append(
                    {
                        "bucket": bucket_name,
                        "chunks": 0,
                        "vectors": 0,
                        "dim": None,
                        "aligned": False,
                    }
                )
                continue

            vec_path = full_path / "vectors.json"
            n_vec = 0
            actual_dim = None
            if vec_path.exists():
                try:
                    with vec_path.open(encoding="utf-8") as handle:
                        vector_data = json.load(handle)
                    vectors = vector_data.get("vectors", [])
                    if isinstance(vectors, list):
                        n_vec = len(vectors)
                        if n_vec > 0 and isinstance(vectors[0], list):
                            actual_dim = len(vectors[0])
                except (OSError, json.JSONDecodeError, AttributeError, IndexError, TypeError):
                    pass

            rag_checks.append(
                {
                    "bucket": bucket_name,
                    "chunks": len(chunks) if isinstance(chunks, list) else 0,
                    "vectors": n_vec,
                    "dim": actual_dim,
                    "aligned": len(chunks) == n_vec
                    if n_vec > 0 and isinstance(chunks, list)
                    else True,
                }
            )

        total_checks = (
            len(CRITICAL_DIRS) + len(CRITICAL_FILES) + len(ROUTING_SPOT_CHECKS) + len(rag_checks)
        )
        total_issues = (
            len(missing_dirs)
            + len(missing_files)
            + len(missing_routing)
            + sum(0 if check["aligned"] else 1 for check in rag_checks)
        )
        passed = total_checks - total_issues

        if rag_checks:
            print("[RAG]")
            for check in rag_checks:
                symbol = "✓" if check["aligned"] else "✗"
                print(
                    f"  {symbol} {check['bucket']}: {check['chunks']} chunks, "
                    f"{check['vectors']} vectors @ {check['dim']}d"
                )

        if total_issues == 0:
            print(f"[Health] {passed}/{total_checks} checks OK")
        else:
            issues = missing_dirs + missing_files + missing_routing
            print(f"[Health] {passed}/{total_checks} OK | Missing: {', '.join(issues[:5])}")

        # Story MCE-11.12 — Holistic 0-100 score via HealthScorer
        # Show full gauge when score < 70 (ATENCAO or CRITICO); show 1-liner otherwise
        try:
            from engine.intelligence.health.health_scorer import (
                HealthScorer,
                render_health_box,
            )

            scorer = HealthScorer(_ROOT)
            health = scorer.compute()
            if health.score_total < 70:
                print("")
                print(render_health_box(health))
            else:
                print(f"[Health Score] {health.score_total}/100 — {health.grade}")
        except Exception:
            # HealthScorer unavailable — silently skip (non-blocking)
            pass

    except Exception as e:
        print(f"[Health] error: {str(e)[:60]}")

    sys.exit(0)


if __name__ == "__main__":
    main()
