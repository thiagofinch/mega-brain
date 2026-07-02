"""
001_legacy_states -- Migrate v1 pipeline state names to v2.
===========================================================

Extracts the legacy ``STATE_MIGRATION`` dict that was previously hardcoded
in ``state_machine.py`` into a proper versioned migration.

Renames:
    knowledge_extraction  ->  insight_extraction
    mce_extraction        ->  mce_behavioral
    validation            ->  reporting
    entities              ->  entity_resolution

Idempotent: if the state is already a v2 name, no change is made.

Version: 1.0.0
Date: 2026-04-01
Epic: MCE-V2 / Story MCE2-1.7
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("mce.migrations.001")

# ╔══ PATTERN: Strategy ═════════════════════════════════════╗
# ║ O QUE   -> cada migration e uma classe com up()          ║
# ║ COMO    -> runner descobre, ordena, executa em sequencia  ║
# ║ QUANDO  -> schema muda, estados renomeiam, campos novos  ║
# ╚══════════════════════════════════════════════════════════╝

# The exact mapping that was in state_machine.py STATE_MIGRATION dict.
LEGACY_STATE_MAP: dict[str, str] = {
    "knowledge_extraction": "insight_extraction",
    "mce_extraction": "mce_behavioral",
    "validation": "reporting",
    "entities": "entity_resolution",
}


class Migration:
    """Rename v1 legacy state names to their v2 equivalents.

    This migration operates on the state data dict (loaded from
    ``pipeline_state.yaml``).  It checks the ``state`` field and
    renames it if it matches a legacy name.

    Idempotent: running this on already-migrated data is a no-op.
    """

    version = "001"
    description = "Rename v1 legacy pipeline state names to v2 equivalents"

    def up(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Apply the migration to state data.

        Args:
            state_data: The full pipeline state dict (from YAML).

        Returns:
            The (possibly modified) state dict.
        """
        current_state = state_data.get("state", "init")
        new_state = LEGACY_STATE_MAP.get(current_state)

        if new_state is not None:
            logger.info(
                "Migration 001: renaming state %r -> %r",
                current_state,
                new_state,
            )
            state_data["state"] = new_state
        else:
            logger.debug(
                "Migration 001: state %r needs no rename (already v2 or unknown)",
                current_state,
            )

        # Also migrate any legacy state names in the history entries.
        history = state_data.get("history", [])
        for entry in history:
            for field in ("from", "to"):
                old_val = entry.get(field, "")
                mapped = LEGACY_STATE_MAP.get(old_val)
                if mapped is not None:
                    entry[field] = mapped

        return state_data
