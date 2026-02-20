#!/usr/bin/env python3
"""
VOICE ISOLATOR - JARVIS Robótico dos Filmes
============================================
Remove música de fundo e efeitos, mantém voz processada.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(_SCRIPT_DIR, "jarvis_robotic")
OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "jarvis_robotic_isolated")


def isolate_voice(input_path: str, output_path: str) -> bool:
    """Usa ElevenLabs Audio Isolation."""
    filename = os.path.basename(input_path)
    print(f"  Processando: {filename}...", end=" ", flush=True)

    with open(input_path, "rb") as audio_file:
        response = requests.post(
            "https://api.elevenlabs.io/v1/audio-isolation",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            files={"audio": (filename, audio_file, "audio/mpeg")}
        )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print("✓")
        return True
    else:
        print(f"✗ ({response.status_code})")
        return False


def main():
    print("=" * 60)
    print("VOICE ISOLATOR - JARVIS ROBÓTICO")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    segments = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".mp3")])
    print(f"\nSegmentos: {len(segments)}")

    success = 0
    for seg in segments:
        input_path = os.path.join(INPUT_DIR, seg)
        output_path = os.path.join(OUTPUT_DIR, seg.replace(".mp3", "_isolated.mp3"))
        if isolate_voice(input_path, output_path):
            success += 1

    print(f"\n✅ {success}/{len(segments)} isolados")
    print(f"📁 {OUTPUT_DIR}")
    return success


if __name__ == "__main__":
    main()
