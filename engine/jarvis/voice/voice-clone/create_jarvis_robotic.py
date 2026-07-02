#!/usr/bin/env python3
"""
CREATE JARVIS ROBOTIC CLONE - v3
================================
Clone da voz do JARVIS dos filmes Homem de Ferro.
Tom robótico/processado original dos filmes.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_robotic_isolated")

VOICE_NAME = "JARVIS-Robotic-v3"
VOICE_DESCRIPTION = """Voz do JARVIS dos filmes Homem de Ferro 1, 2, 3 e Vingadores.
Dublagem brasileira por [VOICE_ACTOR_NAME] com processamento robótico original dos filmes.
Tom metálico, preciso, elegante.
Características: processamento digital, leve reverb, clareza artificial.
Extraído diretamente das cenas dos filmes da Marvel."""


def create_voice():
    print("=" * 60)
    print("CRIANDO JARVIS ROBÓTICO v3")
    print("=" * 60)

    audio_files = sorted(
        [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.endswith(".mp3")]
    )

    print(f"\nArquivos isolados: {len(audio_files)}")

    files = []
    for audio_path in audio_files:
        filename = os.path.basename(audio_path)
        files.append(("files", (filename, open(audio_path, "rb"), "audio/mpeg")))
        print(f"  ✓ {filename}")

    data = {
        "name": VOICE_NAME,
        "description": VOICE_DESCRIPTION,
        "labels": json.dumps(
            {
                "accent": "brazilian-portuguese",
                "age": "synthetic",
                "gender": "male",
                "use_case": "assistant",
            }
        ),
    }

    print("\n📤 Enviando para ElevenLabs...")

    response = requests.post(
        "https://api.elevenlabs.io/v1/voices/add",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        data=data,
        files=files,
    )

    for _, (_, file_obj, _) in files:
        file_obj.close()

    if response.status_code == 200:
        result = response.json()
        voice_id = result.get("voice_id")
        print("\n✅ JARVIS ROBÓTICO CRIADO!")
        print(f"   Voice ID: {voice_id}")

        with open(os.path.dirname(INPUT_DIR) + "/voice_id_robotic.txt", "w") as f:
            f.write(voice_id)

        return voice_id
    else:
        print(f"\n❌ Erro: {response.status_code}")
        print(response.text)
        return None


def configure_settings(voice_id: str):
    """Settings para voz robótica do JARVIS."""
    print("\n⚙️  Configurando settings robóticos...")

    # Settings para manter o tom robótico/processado
    settings = {
        "stability": 0.60,  # Mais estável = mais robótico
        "similarity_boost": 0.90,  # Alta fidelidade ao som do filme
        "style": 0.15,  # Baixo = menos emocional, mais máquina
        "use_speaker_boost": True,
    }

    response = requests.post(
        f"https://api.elevenlabs.io/v1/voices/{voice_id}/settings/edit",
        headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        json=settings,
    )

    if response.status_code == 200:
        print("✅ Settings configurados!")
        for k, v in settings.items():
            print(f"   {k}: {v}")
        return True
    return False


def test_voice(voice_id: str):
    """Testa com frases do JARVIS."""
    print("\n🔊 Testando voz robótica...")

    phrases = [
        "Bem-vindo de volta, senhor. JARVIS online.",
        "Sistemas operacionais. Todas as funções dentro dos parâmetros normais.",
        "Senhor, detectei uma anomalia nos dados. Recomendo investigação imediata.",
        "Estamos na fase quatro, batch trinta e cinco de cinquenta e sete.",
    ]

    base_dir = os.path.dirname(INPUT_DIR)

    for i, phrase in enumerate(phrases, 1):
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={
                "text": phrase,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.60,
                    "similarity_boost": 0.90,
                    "style": 0.15,
                    "use_speaker_boost": True,
                },
            },
        )

        if response.status_code == 200:
            test_file = f"{base_dir}/test_robotic_{i}.mp3"
            with open(test_file, "wb") as f:
                f.write(response.content)
            print(f"  ✓ Teste {i}: {os.path.basename(test_file)}")


if __name__ == "__main__":
    voice_id = create_voice()

    if voice_id:
        configure_settings(voice_id)
        test_voice(voice_id)

        print("\n" + "=" * 60)
        print("JARVIS ROBÓTICO v3 PRONTO")
        print("=" * 60)
        print(f"\n🎯 Voice ID: {voice_id}")
        print("🎬 Fonte: Filmes Homem de Ferro + Vingadores")
        print("🤖 Tom: Robótico/Processado original")
        print("=" * 60)
