"""engine.intelligence.health — Holistic system health scoring.

Exports:
    HealthScorer  — 5-component scorer (state_files, agents, dossiers, inbox, pipeline)
    HealthScore   — Dataclass returned by HealthScorer.compute()

Story: MCE-11.12
"""

from engine.intelligence.health.health_scorer import HealthScore, HealthScorer

__all__ = ["HealthScore", "HealthScorer"]
