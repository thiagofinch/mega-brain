"""
Voice Registry — Persistent store for voice fingerprints.
L3 Personal: VOICE-REGISTRY.yaml is gitignored.
"""

from datetime import datetime

import yaml

from core.paths import ROUTING

REGISTRY_PATH = ROUTING["speakers"] / "VOICE-REGISTRY.yaml"
EMBEDDINGS_DIR = ROUTING["voice_embeddings"]


def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"version": "1.0", "speakers": []}
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f) or {"version": "1.0", "speakers": []}


def _save_registry(data: dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def get_all_speakers() -> list:
    return _load_registry().get("speakers", [])


def get_speaker_by_id(speaker_id: str) -> dict | None:
    for s in get_all_speakers():
        if s["id"] == speaker_id:
            return s
    return None


def find_speaker_by_name(name: str) -> dict | None:
    for s in get_all_speakers():
        if s["name"].lower() == name.lower():
            return s
    return None


def register_speaker(name: str, embedding_file: str, phrases: list = None) -> dict:
    registry = _load_registry()
    speakers = registry.get("speakers", [])
    # Generate next ID
    max_id = max([int(s["id"].split("-")[1]) for s in speakers], default=0)
    new_id = f"SPK-{str(max_id + 1).zfill(3)}"
    entry = {
        "id": new_id,
        "name": name,
        "embedding_file": embedding_file,
        "phrases_sample": phrases or [],
        "registered_at": datetime.now().isoformat()[:10],
        "sessions_seen": 1,
    }
    speakers.append(entry)
    registry["speakers"] = speakers
    _save_registry(registry)
    return entry


def increment_sessions_seen(speaker_id: str):
    registry = _load_registry()
    for s in registry.get("speakers", []):
        if s["id"] == speaker_id:
            s["sessions_seen"] = s.get("sessions_seen", 0) + 1
            break
    _save_registry(registry)
