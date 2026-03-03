#!/usr/bin/env python3
"""
CREATE CLEAN VOICE CLONE - [VOICE_ACTOR_NAME]
============================================
Cria clone usando segmentos isolados (limpos).
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not set in environment")
ISOLATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "segments_isolated")

VOICE_NAME = "JARVIS-Voice-Clone-v2"
VOICE_DESCRIPTION = """Voz do dublador brasileiro [VOICE_ACTOR_NAME].
Dublador oficial do JARVIS nos filmes do Homem de Ferro em português brasileiro.
Tom sofisticado, elegante, articulado.
Ironia sutil, confiança, precisão.
Dicção impecável, voz de locutor profissional.
Extraído do Podcast Desfoque #102 com Voice Isolation."""


def create_voice():
    print("=" * 60)
    print("CRIANDO CLONE LIMPO - VOICE SAMPLE")
    print("=" * 60)

    # Lista arquivos isolados
    audio_files = sorted([
        os.path.join(ISOLATED_DIR, f)
        for f in os.listdir(ISOLATED_DIR)
        if f.endswith(".mp3")
    ])

    print(f"\nArquivos de áudio isolados: {len(audio_files)}")
    for f in audio_files:
        print(f"  ✓ {os.path.basename(f)}")

    # Prepara files para upload
    files = []
    for audio_path in audio_files:
        filename = os.path.basename(audio_path)
        files.append(
            ("files", (filename, open(audio_path, "rb"), "audio/mpeg"))
        )

    # Dados
    data = {
        "name": VOICE_NAME,
        "description": VOICE_DESCRIPTION,
        "labels": json.dumps({
            "accent": "brazilian-portuguese",
            "age": "middle-aged",
            "gender": "male",
            "use_case": "assistant"
        })
    }

    print(f"\n📤 Enviando para ElevenLabs...")

    response = requests.post(
        "https://api.elevenlabs.io/v1/voices/add",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        data=data,
        files=files
    )

    # Fecha arquivos
    for _, (_, file_obj, _) in files:
        file_obj.close()

    if response.status_code == 200:
        result = response.json()
        voice_id = result.get("voice_id")
        print(f"\n✅ VOZ CRIADA COM SUCESSO!")
        print(f"   Voice ID: {voice_id}")
        print(f"   Nome: {VOICE_NAME}")

        # Salva Voice ID
        with open(os.path.join(os.path.dirname(ISOLATED_DIR), "voice_id_clean.txt"), "w") as f:
            f.write(voice_id)

        return voice_id
    else:
        print(f"\n❌ Erro: {response.status_code}")
        print(response.text)
        return None


def configure_settings(voice_id: str):
    """Configura settings otimizados para JARVIS."""
    print(f"\n⚙️  Configurando voice settings...")

    # Settings para voz elegante e precisa do JARVIS
    settings = {
        "stability": 0.45,           # Ligeiramente mais estável
        "similarity_boost": 0.85,    # Alta fidelidade à voz original
        "style": 0.30,               # Moderado - elegante mas não exagerado
        "use_speaker_boost": True
    }

    response = requests.post(
        f"https://api.elevenlabs.io/v1/voices/{voice_id}/settings/edit",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json=settings
    )

    if response.status_code == 200:
        print("✅ Settings configurados!")
        for k, v in settings.items():
            print(f"   {k}: {v}")
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False


def test_voice(voice_id: str):
    """Testa a voz com frases típicas do JARVIS."""
    print(f"\n🔊 Testando voz...")

    test_phrases = [
        "Bem-vindo de volta, senhor. JARVIS online e operacional.",
        "Estamos na fase quatro, batch trinta e cinco de cinquenta e sete. Duzentos e nove arquivos processados.",
        "Senhor, detectei uma anomalia. Posso investigar se desejar."
    ]

    base_dir = os.path.dirname(ISOLATED_DIR)

    for i, phrase in enumerate(test_phrases, 1):
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "text": phrase,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.85,
                    "style": 0.30,
                    "use_speaker_boost": True
                }
            }
        )

        if response.status_code == 200:
            test_file = os.path.join(base_dir, f"test_clean_{i}.mp3")
            with open(test_file, "wb") as f:
                f.write(response.content)
            print(f"  ✓ Teste {i}: {test_file}")
        else:
            print(f"  ✗ Teste {i} falhou: {response.status_code}")


if __name__ == "__main__":
    voice_id = create_voice()

    if voice_id:
        configure_settings(voice_id)
        test_voice(voice_id)

        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)
        print(f"\n🎯 Voice ID: {voice_id}")
        print(f"📝 Nome: {VOICE_NAME}")
        print(f"\n📁 Arquivos de teste salvos em voice-clone/")
        print("=" * 60)
