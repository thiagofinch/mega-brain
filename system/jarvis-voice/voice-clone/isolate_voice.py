#!/usr/bin/env python3
"""
VOICE ISOLATOR - Limpa áudio usando ElevenLabs API
===================================================
Remove ruído e isola apenas a voz nos segmentos.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEGMENTS_DIR = os.path.join(_SCRIPT_DIR, "segments_clean")
ISOLATED_DIR = os.path.join(_SCRIPT_DIR, "segments_isolated")


def isolate_voice(input_path: str, output_path: str) -> bool:
    """Usa ElevenLabs Audio Isolation para limpar áudio."""

    print(f"  Processando: {os.path.basename(input_path)}...")

    with open(input_path, "rb") as audio_file:
        response = requests.post(
            "https://api.elevenlabs.io/v1/audio-isolation",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            files={"audio": (os.path.basename(input_path), audio_file, "audio/mpeg")}
        )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"  ✓ Isolado: {os.path.basename(output_path)}")
        return True
    else:
        print(f"  ✗ Erro: {response.status_code} - {response.text[:100]}")
        return False


def main():
    print("=" * 60)
    print("ELEVENLABS VOICE ISOLATOR")
    print("=" * 60)

    # Cria diretório de saída
    os.makedirs(ISOLATED_DIR, exist_ok=True)

    # Lista arquivos
    segments = sorted([f for f in os.listdir(SEGMENTS_DIR) if f.endswith(".mp3")])
    print(f"\nSegmentos para processar: {len(segments)}")

    success = 0
    for seg in segments:
        input_path = os.path.join(SEGMENTS_DIR, seg)
        output_path = os.path.join(ISOLATED_DIR, seg.replace(".mp3", "_isolated.mp3"))

        if isolate_voice(input_path, output_path):
            success += 1

    print(f"\n✅ {success}/{len(segments)} segmentos isolados")
    print(f"📁 Salvos em: {ISOLATED_DIR}")

    return success == len(segments)


if __name__ == "__main__":
    main()
