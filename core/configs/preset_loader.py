"""Load and validate pipeline presets.

Presets are YAML configurations that define how different content types
should be processed through the Mega Brain pipeline.
"""

from pathlib import Path

import yaml


PRESETS_DIR = Path(__file__).parent / "presets"

VALID_PRESETS = ["course", "meeting", "podcast", "book"]


def load_preset(name: str) -> dict:
    """Load a preset by name.

    Args:
        name: Preset name (course, meeting, podcast, book).

    Returns:
        Preset configuration as a dictionary.

    Raises:
        ValueError: If preset name is not valid.
        FileNotFoundError: If preset file doesn't exist.
    """
    if name not in VALID_PRESETS:
        raise ValueError(f"Unknown preset '{name}'. Valid presets: {VALID_PRESETS}")

    preset_path = PRESETS_DIR / f"{name}.yaml"
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset file not found: {preset_path}")

    with open(preset_path) as f:
        return yaml.safe_load(f)


def list_presets() -> list[dict]:
    """List all available presets with metadata.

    Returns:
        List of dicts with name, description, scope for each preset.
    """
    presets = []
    for name in VALID_PRESETS:
        try:
            config = load_preset(name)
            presets.append(
                {
                    "name": config.get("name", name),
                    "description": config.get("description", ""),
                    "scope": config.get("ingestion", {}).get("scope", "unknown"),
                }
            )
        except (FileNotFoundError, yaml.YAMLError):
            presets.append({"name": name, "description": "ERROR", "scope": "unknown"})
    return presets


if __name__ == "__main__":
    for p in list_presets():
        print(f"  {p['name']:12} | {p['scope']:10} | {p['description']}")
